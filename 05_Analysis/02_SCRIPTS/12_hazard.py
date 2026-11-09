"""
12_hazard.py
============
Compute Hazard Index (G31) from IND01-IND04 and G24 flood hazard scores.
Validates output against G25 observed flood events.

Depends on: G24 (DERIVED), G26 (CLEAN), IND01-IND04 outputs
Outputs:
  - H_Score 0-100 per community → G31
  - Validation report: % of G25 High-confidence events in Moderate+ zones
"""

from datetime import date
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS,
    FLOOD_HAZARD_VALIDATION_PCT,
    RISK_MODEL_VERSION, QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("12_hazard")

# Indicator weights for H (indicative — must be approved per RISK_MODEL_SPEC.md)
H_WEIGHTS = {
    "IND01_Flood_Frequency_Norm":   0.30,
    "IND02_Flood_Severity_Norm":    0.25,
    "IND03_Max_Severity_Norm":      0.25,
    "IND04_River_Proximity_Norm":   0.20,
}


def _minmax(series: pd.Series, ref_max: Optional[float] = None) -> pd.Series:
    mn = 0.0
    mx = ref_max if ref_max is not None else series.max()
    if mx == mn:
        return pd.Series(np.where(series.notna(), 0.0, np.nan), index=series.index)
    return ((series - mn) / (mx - mn) * 100).clip(0, 100)


# ---------------------------------------------------------------------------
# Merge indicator inputs
# ---------------------------------------------------------------------------

def load_indicator_inputs(community_df: pd.DataFrame) -> pd.DataFrame:
    """Load pre-computed indicators from domain modules and merge."""
    result = community_df[["Community_ID","State_Code","LGA_Code"]].copy()

    # IND01/IND02 from 06_flood
    flood_ind_path = ANALYSIS_OUTPUTS / "Flood_Indicators_IND01_IND02.csv"
    if flood_ind_path.exists():
        flood_ind = pd.read_csv(flood_ind_path)
        cols = ["Community_ID","IND01_Flood_Frequency",
                "IND02_Max_Severity","IND02_Mean_Severity"]
        avail = [c for c in cols if c in flood_ind.columns]
        result = result.merge(flood_ind[avail], on="Community_ID", how="left")

    # IND03/IND04 from 07_erosion
    erosion_ind_path = ANALYSIS_OUTPUTS / "Erosion_Indicators_IND03_IND04_G27.csv"
    if erosion_ind_path.exists():
        er_ind = pd.read_csv(erosion_ind_path)
        cols = ["Community_ID","IND03_Max_Severity_Norm","IND04_River_Proximity_Norm"]
        avail = [c for c in cols if c in er_ind.columns]
        result = result.merge(er_ind[avail], on="Community_ID", how="left")

    # G24 mean hazard score per community (from zonal stats if available)
    g24_path = ANALYSIS_OUTPUTS / "G24_HazardZone_Stats.csv"
    if g24_path.exists():
        g24 = pd.read_csv(g24_path)
        if "Mean_Hazard_Score" in g24.columns:
            result = result.merge(
                g24[["Community_ID","Mean_Hazard_Score","Max_Hazard_Score"]],
                on="Community_ID", how="left"
            )

    return result


# ---------------------------------------------------------------------------
# Normalise indicators
# ---------------------------------------------------------------------------

def normalise_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Apply min-max normalisation to all raw indicator columns."""
    df = df.copy()

    # IND01 — flood frequency (log transform first for skewed distribution)
    if "IND01_Flood_Frequency" in df.columns:
        vals = pd.to_numeric(df["IND01_Flood_Frequency"], errors="coerce")
        log_vals = np.log1p(vals)
        df["IND01_Flood_Frequency_Norm"] = _minmax(log_vals)

    # IND02 — flood severity (use max severity per community)
    if "IND02_Max_Severity" in df.columns:
        df["IND02_Flood_Severity_Norm"] = _minmax(
            pd.to_numeric(df["IND02_Max_Severity"], errors="coerce")
        )
    elif "Mean_Hazard_Score" in df.columns:
        # Fallback to G24 mean hazard score
        df["IND02_Flood_Severity_Norm"] = pd.to_numeric(
            df["Mean_Hazard_Score"], errors="coerce"
        ).clip(0, 100)

    # IND03 and IND04 should already be normalised by 07_erosion.py
    for col in ["IND03_Max_Severity_Norm", "IND04_River_Proximity_Norm"]:
        if col not in df.columns:
            df[col] = np.nan

    return df


# ---------------------------------------------------------------------------
# G31 — Hazard Index
# ---------------------------------------------------------------------------

def compute_g31_hazard(df: pd.DataFrame) -> pd.DataFrame:
    """Weighted sum of normalised hazard indicators → H_Score 0-100."""
    result = df.copy()

    h_score    = pd.Series(0.0, index=result.index)
    weight_sum = pd.Series(0.0, index=result.index)
    missing    = pd.Series(0, index=result.index)

    for col, w in H_WEIGHTS.items():
        if col in result.columns:
            vals  = pd.to_numeric(result[col], errors="coerce")
            avail = vals.notna()
            h_score    += vals.fillna(0) * w * avail
            weight_sum += w * avail
            missing    += (~avail).astype(int)
        else:
            missing += 1

    result["H_Score"] = np.where(
        weight_sum > 0,
        (h_score / weight_sum).clip(0, 100),
        np.nan,
    )

    result["H_Missing_Components"] = missing.astype(int)
    n_avail = len(H_WEIGHTS) - missing
    result["H_Data_Completeness"] = pd.cut(
        n_avail, bins=[-1, 0, 1, 4], labels=["Minimal","Partial","Full"]
    )
    result["Risk_Model_Version"] = RISK_MODEL_VERSION
    result["Computation_Date"]   = date.today().isoformat()

    return result


# ---------------------------------------------------------------------------
# Validation against G25 observed floods
# ---------------------------------------------------------------------------

def validate_against_g25(
    g31_df: pd.DataFrame,
    threshold: float = FLOOD_HAZARD_VALIDATION_PCT,
) -> Tuple[float, str]:
    """
    Check: % of High-confidence G25 events falling in Moderate+ hazard communities.
    Returns (validation_score, status).
    """
    g25_path = DATA_CLEAN / "G25_ObservedFloods_CLEAN.csv"
    if not g25_path.exists():
        log.warning("G25 not found — skipping G31 validation")
        return (np.nan, "SKIPPED")

    g25 = pd.read_csv(g25_path)
    high_conf = g25[g25["Confidence"] == "High"]

    if len(high_conf) == 0:
        log.warning("No High-confidence G25 events — validation skipped")
        return (np.nan, "SKIPPED")

    # Join G31 H_Score to G25 events by Community_ID
    merged = high_conf.merge(
        g31_df[["Community_ID","H_Score"]],
        on="Community_ID", how="left"
    )

    # Moderate+ threshold ≈ H_Score >= 40 (indicative — refined at model approval)
    in_moderate_plus = (merged["H_Score"] >= 40).sum()
    total            = merged["H_Score"].notna().sum()

    if total == 0:
        return (np.nan, "SKIPPED")

    score = in_moderate_plus / total
    status = "PASS" if score >= threshold else "FAIL"

    log.info(
        f"G31 validation vs G25: {in_moderate_plus}/{total} "
        f"({score:.1%}) High-confidence events in Moderate+ hazard zones | "
        f"Threshold: {threshold:.0%} | {status}"
    )

    if status == "FAIL":
        log.error(
            f"G31 validation FAILED ({score:.1%} < {threshold:.0%}). "
            f"Review input weights in RISK_MODEL_SPEC.md HMD01 before publishing."
        )

    return (score, status)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "12_HAZARD — Hazard Index (G31)")
    assert_upstream_clean(["DB01","DB03"])

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community_df = pd.read_csv(comm_path)
    df           = load_indicator_inputs(community_df)
    df           = normalise_indicators(df)
    g31          = compute_g31_hazard(df)

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G31_HazardIndex.csv"
    g31.to_csv(out, index=False)
    log.info(f"G31 Hazard Index saved: {out} | "
             f"Mean H_Score: {g31['H_Score'].mean():.1f}")

    # Validate
    val_score, val_status = validate_against_g25(g31)

    update_processing_status("G31", QCStatus.DERIVED)
    append_version_log(BASELINE_VERSION, "G31", "GIS Layer", "DERIVE",
                       f"G31 Hazard Index computed: {len(g31)} communities; "
                       f"G25 validation: {val_status}")

    if val_status == "FAIL":
        from run_pipeline import PipelineCriticalError  # lazy import
        raise PipelineCriticalError(
            "G31 failed G25 validation — review hazard model weights before proceeding."
        )

    log.info("12_hazard complete")
    return g31


if __name__ == "__main__":
    run_all()
