"""
26_eri.py
=========
Environmental Risk Index v2.0 (ERI) — the nine-component composite.

Formula:
  ERI = 0.25H + 0.15E + 0.15V + 0.10C + 0.10CC + 0.08LD + 0.07DF + 0.05WP + 0.05BL

Where all components are normalised 0–100 and weights sum to 1.0.

Outputs:
  - G64: ERI score per community + classification + rank
  - Sensitivity models:
      S1: equal weights (0.111 each for 9 components)
      S2: hazard-dominant (H=0.40 + FL=0.10; others proportionally reduced)
      S3: environment-dominant (CC+LD+DF+WP+BL get 0.60 total)
  - Spearman rank correlations between baseline and sensitivity models
  - Communities where ERI > HEVC composite risk (G35) by >=10 points — new risks revealed

Backward compatibility:
  G35 (HEVC composite v1.0) is NOT changed or overwritten.
  G64 (ERI v2.0) is a new, additional output.

Depends on: G31 G32 G33 G34 (all CLEAN) + G42 G50 G54 G58 G63 (all DERIVED)
"""

from datetime import date
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from config import (
    ANALYSIS_OUTPUTS, DECISION_RISK, DECISION_PRIORITY,
    RISK_MODEL_VERSION, QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    update_processing_status,
    append_version_log,
)

log = get_logger("26_eri")

# ── ERI Model version ────────────────────────────────────────────────────────
ERI_MODEL_VERSION = "ERI_Model_v2.0"

# ── Baseline weights (sum = 1.0) ─────────────────────────────────────────────
ERI_WEIGHTS_BASELINE: Dict[str, float] = {
    "H_Score":  0.25,
    "E_Score":  0.15,
    "V_Score":  0.15,
    "C_Score":  0.10,
    "CC_Score": 0.10,
    "LD_Score": 0.08,
    "DF_Score": 0.07,
    "WP_Score": 0.05,
    "BL_Score": 0.05,
}

# ── Sensitivity model S1: equal weights ──────────────────────────────────────
_n = len(ERI_WEIGHTS_BASELINE)
ERI_WEIGHTS_S1_EQUAL: Dict[str, float] = {k: round(1.0/_n, 4)
                                           for k in ERI_WEIGHTS_BASELINE}

# ── Sensitivity model S2: hazard-dominant ────────────────────────────────────
ERI_WEIGHTS_S2_HAZARD: Dict[str, float] = {
    "H_Score":  0.35,
    "E_Score":  0.12,
    "V_Score":  0.12,
    "C_Score":  0.08,
    "CC_Score": 0.13,  # climate change amplifies hazard
    "LD_Score": 0.08,
    "DF_Score": 0.06,
    "WP_Score": 0.03,
    "BL_Score": 0.03,
}

# ── Sensitivity model S3: environment-dominant ───────────────────────────────
ERI_WEIGHTS_S3_ENV: Dict[str, float] = {
    "H_Score":  0.15,
    "E_Score":  0.10,
    "V_Score":  0.10,
    "C_Score":  0.05,
    "CC_Score": 0.17,
    "LD_Score": 0.15,
    "DF_Score": 0.13,
    "WP_Score": 0.08,
    "BL_Score": 0.07,
}


# ---------------------------------------------------------------------------
# Load all nine component indices
# ---------------------------------------------------------------------------

def load_components() -> Optional[pd.DataFrame]:
    """Load G31–G34 (v1.0 HEVC) and G42/G50/G54/G58/G63 (v2.0 env) outputs."""

    sources = {
        "G31": (ANALYSIS_OUTPUTS / "G31_HazardIndex.csv",      "H_Score"),
        "G32": (ANALYSIS_OUTPUTS / "G32_ExposureIndex.csv",     "E_Score"),
        "G33": (ANALYSIS_OUTPUTS / "G33_VulnerabilityIndex.csv","V_Score"),
        "G34": (ANALYSIS_OUTPUTS / "G34_CriticalityIndex.csv",  "C_Score"),
        "G42": (ANALYSIS_OUTPUTS / "G42_ClimateChangeIndex.csv","CC_Score"),
        "G50": (ANALYSIS_OUTPUTS / "G50_LandDegradationIndex.csv","LD_Score"),
        "G54": (ANALYSIS_OUTPUTS / "G54_DeforestationPressureIndex.csv","DF_Score"),
        "G58": (ANALYSIS_OUTPUTS / "G58_WastePollutionExposure.csv","WP_Score"),
        "G63": (ANALYSIS_OUTPUTS / "G63_BiodiversityLossIndex.csv","BL_Score"),
    }

    base = None
    missing_critical = []

    for layer_id, (path, score_col) in sources.items():
        if not path.exists():
            log.warning(f"{layer_id} output not found at {path} — {score_col} = NULL")
            if layer_id in ("G31","G32","G33","G34"):
                missing_critical.append(layer_id)
            continue

        df = pd.read_csv(path)
        if "Community_ID" not in df.columns or score_col not in df.columns:
            log.warning(f"{layer_id}: missing Community_ID or {score_col}")
            continue

        cols = ["Community_ID", score_col]
        # Include completeness flag if present
        comp_col = f"{score_col[0]}_Data_Completeness"
        if comp_col in df.columns:
            cols.append(comp_col)

        if base is None:
            # Start with State/LGA from first HEVC layer
            extra = ["State_Code","LGA_Code","Community"]
            base_cols = ["Community_ID"] + [c for c in extra if c in df.columns]
            base = df[base_cols + [score_col]].copy()
        else:
            base = base.merge(df[cols], on="Community_ID", how="outer")

    if missing_critical:
        log.error(
            f"Critical HEVC components missing: {missing_critical}. "
            "ERI cannot be computed without H, E, V, C scores."
        )
        return None

    log.info(
        f"ERI components loaded: {len(base)} communities | "
        f"Components available: {[k for k,(_,s) in sources.items() if s in base.columns]}"
    )
    return base


# ---------------------------------------------------------------------------
# Weighted ERI formula
# ---------------------------------------------------------------------------

def _compute_eri(df: pd.DataFrame, weights: Dict[str,float], suffix: str = "") -> pd.Series:
    """Apply weighted sum; missing components reduce effective weight proportionally."""
    score      = pd.Series(0.0, index=df.index)
    weight_sum = pd.Series(0.0, index=df.index)

    for col, w in weights.items():
        if col in df.columns:
            vals  = pd.to_numeric(df[col], errors="coerce")
            avail = vals.notna()
            score      += vals.fillna(0) * w * avail
            weight_sum += w * avail

    return pd.Series(
        np.where(weight_sum > 0, (score / weight_sum).clip(0, 100), np.nan),
        index=df.index,
        name=f"ERI_Score{suffix}",
    )


# ---------------------------------------------------------------------------
# Verify weight sums
# ---------------------------------------------------------------------------

def _verify_weights() -> None:
    for name, wts in [
        ("Baseline",         ERI_WEIGHTS_BASELINE),
        ("S1_Equal",         ERI_WEIGHTS_S1_EQUAL),
        ("S2_Hazard",        ERI_WEIGHTS_S2_HAZARD),
        ("S3_Environment",   ERI_WEIGHTS_S3_ENV),
    ]:
        total = sum(wts.values())
        assert abs(total - 1.0) < 0.005, f"{name} weights sum to {total:.4f} not 1.0"
    log.info("All ERI weight sets verified: sum = 1.0 ✓")


# ---------------------------------------------------------------------------
# Classify ERI score
# ---------------------------------------------------------------------------

def _classify_eri(r_score: pd.Series, thresholds: Optional[Dict] = None) -> pd.Series:
    """5-class classification using equal-interval placeholder until Jenks computed."""
    t1, t2, t3, t4 = (thresholds or {}).get(
        "breaks", [20.0, 40.0, 60.0, 80.0]
    )
    return pd.cut(
        r_score,
        bins=[-np.inf, t1, t2, t3, t4, np.inf],
        labels=["Very Low","Low","Moderate","High","Very High"],
        right=True,
    ).astype(str).replace("nan", pd.NA)


# ---------------------------------------------------------------------------
# Sensitivity analysis and rank correlation
# ---------------------------------------------------------------------------

def run_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ERI_Score_S1"] = _compute_eri(df, ERI_WEIGHTS_S1_EQUAL)
    df["ERI_Score_S2"] = _compute_eri(df, ERI_WEIGHTS_S2_HAZARD)
    df["ERI_Score_S3"] = _compute_eri(df, ERI_WEIGHTS_S3_ENV)
    df["ERI_Class_S1"] = _classify_eri(df["ERI_Score_S1"])
    df["ERI_Class_S2"] = _classify_eri(df["ERI_Score_S2"])
    df["ERI_Class_S3"] = _classify_eri(df["ERI_Score_S3"])

    try:
        for s_col, label in [("ERI_Score_S1","S1"),
                              ("ERI_Score_S2","S2"),
                              ("ERI_Score_S3","S3")]:
            valid = df[["ERI_Score", s_col]].dropna()
            if len(valid) > 2:
                corr = valid["ERI_Score"].corr(valid[s_col], method="spearman")
                log.info(f"Spearman rank correlation baseline vs {label}: {corr:.3f}")
                if corr < 0.70:
                    log.warning(
                        f"Low rank correlation ({corr:.3f}) vs {label} — "
                        "ERI rankings sensitive to weight choice. Document in sensitivity report."
                    )
    except Exception as exc:
        log.warning(f"Sensitivity correlation failed: {exc}")

    return df


# ---------------------------------------------------------------------------
# Compare ERI v2.0 with HEVC v1.0 (G35)
# ---------------------------------------------------------------------------

def compare_with_g35(eri_df: pd.DataFrame) -> pd.DataFrame:
    """Flag communities where ERI > G35 by >= 10 points — new risks revealed."""
    g35_path = ANALYSIS_OUTPUTS / "G35_CompositeRisk.csv"
    if not g35_path.exists():
        log.info("G35 not found — ERI vs HEVC comparison skipped")
        return eri_df

    g35 = pd.read_csv(g35_path)[["Community_ID","R_Score","R_Class"]]
    df  = eri_df.merge(
        g35.rename(columns={"R_Score":"HEVC_R_Score","R_Class":"HEVC_R_Class"}),
        on="Community_ID", how="left"
    )
    df["ERI_vs_HEVC_Delta"] = (
        pd.to_numeric(df["ERI_Score"], errors="coerce") -
        pd.to_numeric(df["HEVC_R_Score"], errors="coerce")
    ).round(2)

    newly_elevated = df[
        (df["ERI_vs_HEVC_Delta"] >= 10) &
        (df["ERI_Class"].isin(["High","Very High"])) &
        (~df["HEVC_R_Class"].isin(["High","Very High"]))
    ]
    log.info(
        f"ERI vs HEVC comparison: {len(newly_elevated)} communities newly elevated "
        f"to High/Very High by environmental domains (ERI > HEVC by >=10 pts)"
    )
    if len(newly_elevated) > 0:
        elevated_path = ANALYSIS_OUTPUTS / "ERI_Newly_Elevated_Communities.csv"
        newly_elevated.to_csv(elevated_path, index=False)
        log.info(f"Newly elevated communities saved: {elevated_path}")

    return df


# ---------------------------------------------------------------------------
# Build G64
# ---------------------------------------------------------------------------

def compute_g64_eri() -> Optional[pd.DataFrame]:
    """Main ERI computation."""
    _verify_weights()

    df = load_components()
    if df is None:
        return None

    # Baseline ERI
    df["ERI_Score"] = _compute_eri(df, ERI_WEIGHTS_BASELINE)
    df["ERI_Class"] = _classify_eri(df["ERI_Score"])
    df["ERI_Rank"]  = (
        df["ERI_Score"].rank(ascending=False, method="min")
        .astype("Int64")
    )

    # Sensitivity models
    df = run_sensitivity(df)

    # Rank change S1 vs baseline
    df["ERI_Rank_S1"] = (
        df["ERI_Score_S1"].rank(ascending=False, method="min")
        .astype("Int64")
    )
    df["ERI_Rank_Change_S1"] = (df["ERI_Rank_S1"] - df["ERI_Rank"]).astype("Int64")

    # Compare with HEVC G35
    df = compare_with_g35(df)

    # Count missing components
    df["ERI_Missing_Components"] = sum(
        df.get(col, pd.Series(dtype=float)).isna().astype(int)
        for col in ERI_WEIGHTS_BASELINE
    )
    df["ERI_Data_Completeness"] = pd.cut(
        9 - df["ERI_Missing_Components"],
        bins=[-1, 3, 6, 9],
        labels=["Minimal","Partial","Full"],
    ).astype(str)

    # Metadata
    df["ERI_Model_Version"]       = ERI_MODEL_VERSION
    df["HEVC_Model_Version"]      = RISK_MODEL_VERSION  # backward reference
    df["ERI_Hazard_Weight"]       = ERI_WEIGHTS_BASELINE["H_Score"]
    df["ERI_Exposure_Weight"]     = ERI_WEIGHTS_BASELINE["E_Score"]
    df["ERI_Vulnerability_Weight"]= ERI_WEIGHTS_BASELINE["V_Score"]
    df["ERI_Criticality_Weight"]  = ERI_WEIGHTS_BASELINE["C_Score"]
    df["ERI_ClimateChange_Weight"]= ERI_WEIGHTS_BASELINE["CC_Score"]
    df["ERI_LandDeg_Weight"]      = ERI_WEIGHTS_BASELINE["LD_Score"]
    df["ERI_Deforest_Weight"]     = ERI_WEIGHTS_BASELINE["DF_Score"]
    df["ERI_WastePollut_Weight"]  = ERI_WEIGHTS_BASELINE["WP_Score"]
    df["ERI_Biodiv_Weight"]       = ERI_WEIGHTS_BASELINE["BL_Score"]
    df["Weight_Sum_Check"]        = sum(ERI_WEIGHTS_BASELINE.values())
    df["Normalization_Method"]    = "Min-max 0-100 study area"
    df["Data_Date"]               = "2026"
    df["Computation_Date"]        = date.today().isoformat()

    # Save
    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    DECISION_RISK.mkdir(parents=True, exist_ok=True)

    out_csv = ANALYSIS_OUTPUTS  / "G64_EnvironmentalRiskIndex_ERI_v2.csv"
    out_ds  = DECISION_RISK     / "G64_ERI_v2.0_Community.csv"
    df.to_csv(out_csv, index=False)
    df.to_csv(out_ds,  index=False)

    tier1 = (df["ERI_Class"].isin(["High","Very High"])).sum()
    log.info(
        f"\n{'='*55}\n"
        f"  ERI v2.0 COMPLETE\n"
        f"{'='*55}\n"
        f"  Communities assessed:  {len(df)}\n"
        f"  Mean ERI Score:        {df['ERI_Score'].mean():.1f}\n"
        f"  High/Very High (ERI):  {tier1}\n"
        f"  Missing >= 5 components: {(df['ERI_Missing_Components'] >= 5).sum()}\n"
        f"  Saved: {out_csv}\n"
        f"  Model version: {ERI_MODEL_VERSION}\n"
    )

    update_processing_status("G64", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G64", "GIS Layer", "DERIVE",
        f"G64 ERI v2.0 computed ({ERI_MODEL_VERSION}): {len(df)} communities; "
        f"Mean ERI={df['ERI_Score'].mean():.1f}; High+VH={tier1}"
    )
    return df


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "26_ERI — Environmental Risk Index v2.0 (G64)")
    result = compute_g64_eri()
    if result is not None:
        log.info("26_eri complete")
    return result


if __name__ == "__main__":
    run_all()
