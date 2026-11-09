"""
13_risk.py
==========
Compute Composite Risk Index (G35): R = 0.35H + 0.25E + 0.25V + 0.15C
Plus sensitivity models S1 (equal weights) and S2 (hazard-dominant).

Depends on: G31 H_Score, G32 E_Score, G33 V_Score, G34 C_Score (all DERIVED)
Outputs:
  - G35 CompositeRisk with R_Score, R_Class, sensitivity S1/S2 scores
  - Rank within study area
  - Spearman rank correlation between baseline and sensitivity models

Key rules:
  - Formula verified per record: |R - (0.35H+0.25E+0.25V+0.15C)| < 0.01
  - Weights locked — cannot change after seeing output
  - G35 once PUBLISHED is immutable
  - R_Score is a decision-support index, not a disaster probability
"""

from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import numpy as np

from config import (
    ANALYSIS_OUTPUTS, DECISION_RISK,
    RISK_MODEL_VERSION,
    RISK_WEIGHTS_BASELINE,
    RISK_WEIGHTS_S1_EQUAL,
    RISK_WEIGHTS_S2_HAZARD_DOMINANT,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    update_processing_status,
    append_version_log,
)

log = get_logger("13_risk")


# ---------------------------------------------------------------------------
# Load component indices
# ---------------------------------------------------------------------------

def load_components() -> Optional[pd.DataFrame]:
    """Load G31-G34 outputs and merge on Community_ID."""
    paths = {
        "G31": ANALYSIS_OUTPUTS / "G31_HazardIndex.csv",
        "G32": ANALYSIS_OUTPUTS / "G32_ExposureIndex.csv",
        "G33": ANALYSIS_OUTPUTS / "G33_VulnerabilityIndex.csv",
        "G34": ANALYSIS_OUTPUTS / "G34_CriticalityIndex.csv",
    }

    dfs = {}
    for layer_id, path in paths.items():
        if not path.exists():
            log.error(f"{layer_id} output not found at {path}")
            return None
        df = pd.read_csv(path)
        dfs[layer_id] = df

    # Merge on Community_ID
    score_cols = {
        "G31": "H_Score",
        "G32": "E_Score",
        "G33": "V_Score",
        "G34": "C_Score",
    }
    completeness_cols = {
        "G31": "H_Data_Completeness",
        "G32": "E_Data_Completeness",
        "G33": "V_Data_Completeness",
        "G34": "C_Data_Completeness",
    }

    result = dfs["G31"][["Community_ID","State_Code","LGA_Code"]].copy()

    # Try to get Community name from G31 if present
    if "Community" in dfs["G31"].columns:
        result["Community"] = dfs["G31"]["Community"]

    for layer_id, score_col in score_cols.items():
        df = dfs[layer_id]
        cols_to_grab = ["Community_ID", score_col]
        comp_col = completeness_cols[layer_id]
        if comp_col in df.columns:
            cols_to_grab.append(comp_col)
        result = result.merge(df[cols_to_grab], on="Community_ID", how="left")

    return result


# ---------------------------------------------------------------------------
# Compute risk score for a given weight set
# ---------------------------------------------------------------------------

def _compute_r_score(
    df: pd.DataFrame,
    weights: Dict[str, float],
    suffix: str = "",
) -> pd.Series:
    """
    Weighted sum of H/E/V/C scores.
    Missing components reduce effective weight proportionally.
    """
    score      = pd.Series(0.0, index=df.index)
    weight_sum = pd.Series(0.0, index=df.index)

    component_map = {
        "H": "H_Score",
        "E": "E_Score",
        "V": "V_Score",
        "C": "C_Score",
    }

    for key, col in component_map.items():
        w = weights.get(key, 0.0)
        if col in df.columns:
            vals  = pd.to_numeric(df[col], errors="coerce")
            avail = vals.notna()
            score      += vals.fillna(0) * w * avail
            weight_sum += w * avail

    r = np.where(weight_sum > 0, (score / weight_sum).clip(0, 100), np.nan)
    return pd.Series(r, index=df.index, name=f"R_Score{suffix}")


# ---------------------------------------------------------------------------
# Classify risk
# ---------------------------------------------------------------------------

def classify_risk(r_score: pd.Series, thresholds: Optional[Dict] = None) -> pd.Series:
    """
    Classify R_Score into 5 classes.
    Thresholds use natural breaks (Jenks) computed on first run
    and FROZEN thereafter. If thresholds dict not provided, uses
    equal-interval as placeholder until Jenks computed.
    """
    if thresholds:
        t1, t2, t3, t4 = (thresholds["very_low_max"], thresholds["low_max"],
                          thresholds["moderate_max"], thresholds["high_max"])
    else:
        # Placeholder equal-interval thresholds — replace with Jenks after first run
        t1, t2, t3, t4 = 20.0, 40.0, 60.0, 80.0
        log.warning(
            "Using equal-interval thresholds as placeholder — "
            "run Jenks classification on baseline distribution and "
            "record thresholds in RISK_MODEL_SPEC.md Section 6 before publication."
        )

    classes = pd.cut(
        r_score,
        bins=[-np.inf, t1, t2, t3, t4, np.inf],
        labels=["Very Low", "Low", "Moderate", "High", "Very High"],
        right=True,
    )
    return classes.astype(str).replace("nan", pd.NA)


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------

def run_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Compute S1 and S2 sensitivity models and rank correlations."""
    df = df.copy()

    df["R_Score_S1"] = _compute_r_score(df, RISK_WEIGHTS_S1_EQUAL)
    df["R_Score_S2"] = _compute_r_score(df, RISK_WEIGHTS_S2_HAZARD_DOMINANT)
    df["R_Class_S1"] = classify_risk(df["R_Score_S1"])
    df["R_Class_S2"] = classify_risk(df["R_Score_S2"])

    # Ranks
    df["Rank_S1"] = df["R_Score_S1"].rank(ascending=False, method="min").astype("Int64")
    df["Rank_S2"] = df["R_Score_S2"].rank(ascending=False, method="min").astype("Int64")
    df["Rank_Change_S1"] = (df["Rank_S1"] - df["Rank_Baseline"]).astype("Int64")

    # Spearman rank correlations
    baseline_valid = df[["R_Score","R_Score_S1","R_Score_S2"]].dropna()
    if len(baseline_valid) > 2:
        corr_s1 = baseline_valid["R_Score"].corr(
            baseline_valid["R_Score_S1"], method="spearman"
        )
        corr_s2 = baseline_valid["R_Score"].corr(
            baseline_valid["R_Score_S2"], method="spearman"
        )
        log.info(f"Sensitivity rank correlations — S1: {corr_s1:.3f} | S2: {corr_s2:.3f}")

        if corr_s1 < 0.7:
            log.warning(
                f"S1 rank correlation ({corr_s1:.3f}) < 0.70 — "
                "model rankings are sensitive to weight specification. "
                "Review and document in RISK_MODEL_SPEC.md."
            )

        # Class change analysis
        class_change_s1 = (df["R_Class"] != df["R_Class_S1"]).sum()
        total = df["R_Class"].notna().sum()
        pct_change = class_change_s1 / total * 100 if total > 0 else 0
        log.info(
            f"Communities changing risk class (baseline vs S1): "
            f"{class_change_s1}/{total} ({pct_change:.1f}%)"
        )
        if pct_change > 30:
            log.warning(
                f"{pct_change:.1f}% of communities change class under S1 — "
                "high sensitivity. Document in sensitivity analysis report."
            )

    return df


# ---------------------------------------------------------------------------
# Formula verification
# ---------------------------------------------------------------------------

def verify_formula(df: pd.DataFrame) -> bool:
    """Q — |R - (0.35H + 0.25E + 0.25V + 0.15C)| < 0.01 for all records."""
    calculated = (
        0.35 * df["H_Score"].fillna(0) +
        0.25 * df["E_Score"].fillna(0) +
        0.25 * df["V_Score"].fillna(0) +
        0.15 * df["C_Score"].fillna(0)
    )
    # For records where all 4 components present, check formula
    all_present = (
        df["H_Score"].notna() & df["E_Score"].notna() &
        df["V_Score"].notna() & df["C_Score"].notna()
    )
    discrepancy = (df.loc[all_present, "R_Score"] - calculated[all_present]).abs()
    max_disc = discrepancy.max() if len(discrepancy) > 0 else 0.0
    passed = max_disc < 0.01
    if not passed:
        log.error(f"Formula verification failed — max discrepancy: {max_disc:.4f}")
    else:
        log.info(f"Formula verified — max discrepancy: {max_disc:.6f}")
    return passed


# ---------------------------------------------------------------------------
# G35 — Composite Risk
# ---------------------------------------------------------------------------

def compute_g35_composite_risk() -> Optional[pd.DataFrame]:
    """Main function: load components, compute R, classify, run sensitivity."""
    df = load_components()
    if df is None:
        return None

    # Baseline R_Score
    df["R_Score"] = _compute_r_score(df, RISK_WEIGHTS_BASELINE)

    # Verify formula
    verify_formula(df)

    # Classify
    df["R_Class"] = classify_risk(df["R_Score"])

    # Rank
    df["Rank_Baseline"] = (
        df["R_Score"].rank(ascending=False, method="min").astype("Int64")
    )

    # Sensitivity models
    df = run_sensitivity(df)

    # Required metadata (per G35 schema)
    df["Risk_Model_Version"]      = RISK_MODEL_VERSION
    df["Hazard_Weight"]           = RISK_WEIGHTS_BASELINE["H"]
    df["Exposure_Weight"]         = RISK_WEIGHTS_BASELINE["E"]
    df["Vulnerability_Weight"]    = RISK_WEIGHTS_BASELINE["V"]
    df["Criticality_Weight"]      = RISK_WEIGHTS_BASELINE["C"]
    df["Weight_Sum_Check"]        = (
        df["Hazard_Weight"] + df["Exposure_Weight"] +
        df["Vulnerability_Weight"] + df["Criticality_Weight"]
    )
    df["Normalization_Method"]    = "Min-max 0-100 study area"
    df["Reference_Bounds"]        = f"Baseline {DATA_DATE} study area"
    df["Data_Date"]               = DATA_DATE
    df["Input_Versions"]          = BASELINE_VERSION
    df["Computation_Date"]        = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out_csv = ANALYSIS_OUTPUTS / "G35_CompositeRisk.csv"
    df.to_csv(out_csv, index=False)

    # Also save to Decision Support folder
    DECISION_RISK.mkdir(parents=True, exist_ok=True)
    out_ds = DECISION_RISK / "G35_CompositeRisk_v1_0.csv"
    df.to_csv(out_ds, index=False)

    log.info(
        f"G35 Composite Risk saved: {out_csv} | "
        f"{len(df)} communities | "
        f"Mean R: {df['R_Score'].mean():.1f} | "
        f"High+VeryHigh: {(df['R_Class'].isin(['High','Very High'])).sum()}"
    )

    update_processing_status("G35", QCStatus.DERIVED)
    append_version_log(BASELINE_VERSION, "G35", "GIS Layer", "DERIVE",
                       f"G35 Composite Risk computed ({RISK_MODEL_VERSION}): "
                       f"{len(df)} communities")
    return df


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "13_RISK — Composite Risk Index (G35)")
    g35 = compute_g35_composite_risk()
    if g35 is not None:
        log.info("13_risk complete")
    return g35


# Expose DATA_DATE from config (needed in metadata)
from config import DATA_DATE

if __name__ == "__main__":
    run_all()
