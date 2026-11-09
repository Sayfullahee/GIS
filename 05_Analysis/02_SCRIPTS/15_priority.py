"""
15_priority.py
==============
Compute Priority Areas (G37): rank communities by risk + adaptation gap.

Priority_Score = 0.70 × R_Score + 0.30 × IND10_Adaptation_Gap
Tier 1-4 via natural breaks on Priority_Score.

Depends on: G35 (DERIVED), G36 (DERIVED)
Outputs:
  - G37 Priority Areas with rank, tier, data confidence
  - Top-20 priority list (CSV)
  - Sensitivity tier comparison report

Key rules:
  - All component scores retained (explainability)
  - Priority is DECISION SUPPORT — never described as automatic intervention mandate
  - Data confidence shown alongside rank
  - No household-level data in G37
"""

from datetime import date
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS, DECISION_PRIORITY,
    PRIORITY_WEIGHTS, RISK_MODEL_VERSION,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    update_processing_status,
    append_version_log,
)

log = get_logger("15_priority")


# ---------------------------------------------------------------------------
# Load G35 and G36
# ---------------------------------------------------------------------------

def load_inputs() -> Optional[pd.DataFrame]:
    g35_path = ANALYSIS_OUTPUTS / "G35_CompositeRisk.csv"
    g36_path = ANALYSIS_OUTPUTS / "G36_Adaptation.csv"

    if not g35_path.exists():
        log.error(f"G35 not found: {g35_path}")
        return None

    g35 = pd.read_csv(g35_path)

    if g36_path.exists():
        g36 = pd.read_csv(g36_path)
        cols = ["Community_ID","IND09_Adaptation_Coverage","IND10_Adaptation_Gap"]
        avail = [c for c in cols if c in g36.columns]
        g35 = g35.merge(g36[avail], on="Community_ID", how="left")
    else:
        log.warning("G36 not found — IND10 will be NULL in G37")
        g35["IND09_Adaptation_Coverage"] = np.nan
        g35["IND10_Adaptation_Gap"]      = np.nan

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if comm_path.exists():
        comm = pd.read_csv(comm_path)
        comm_cols = [c for c in ["Community_ID", "Community", "State_Name", "LGA_Code", "LGA"] if c in comm.columns]
        g35 = g35.merge(comm[comm_cols], on="Community_ID", how="left", suffixes=("", "_comm"))
        if "LGA_Code_comm" in g35.columns:
            g35["LGA_Code"] = g35["LGA_Code"].fillna(g35["LGA_Code_comm"])
            g35 = g35.drop(columns=["LGA_Code_comm"])

    return g35


# ---------------------------------------------------------------------------
# Priority score
# ---------------------------------------------------------------------------

def compute_priority_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Priority_Score = 0.70 × R_Score + 0.30 × IND10_Adaptation_Gap
    If IND10 missing, use R_Score only (100% weight on R).
    """
    df = df.copy()
    r   = pd.to_numeric(df["R_Score"],            errors="coerce")
    gap = pd.to_numeric(df.get("IND10_Adaptation_Gap",
                                pd.Series(dtype=float)), errors="coerce")

    has_gap = gap.notna()

    df["Priority_Score"] = np.where(
        has_gap,
        (PRIORITY_WEIGHTS["R_Score"] * r +
         PRIORITY_WEIGHTS["Adaptation_Gap"] * gap).clip(0, 100),
        r.clip(0, 100),
    )
    df["Priority_Score_Method"] = np.where(
        has_gap, "R+AdaptGap", "R_only"
    )
    return df


# ---------------------------------------------------------------------------
# Tier classification (natural breaks placeholder)
# ---------------------------------------------------------------------------

def classify_priority_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify Priority_Score into 4 tiers using natural breaks.
    Placeholder: equal-interval until Jenks computed on baseline.
    """
    df = df.copy()
    p  = pd.to_numeric(df["Priority_Score"], errors="coerce")

    # Natural breaks approximation (equal-interval placeholder)
    t1, t2, t3 = 75.0, 50.0, 25.0
    log.warning(
        "Priority tier thresholds use equal-interval placeholder — "
        "compute Jenks on baseline Priority_Score distribution and "
        "update thresholds in RISK_MODEL_SPEC.md Section 8 before publication."
    )

    df["Priority_Tier"] = np.select(
        [p >= t1, p >= t2, p >= t3],
        [1, 2, 3],
        default=4
    )
    df.loc[p.isna(), "Priority_Tier"] = pd.NA
    return df


# ---------------------------------------------------------------------------
# Data confidence rating
# ---------------------------------------------------------------------------

def assign_data_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive overall data confidence from component completeness flags.
    High = all 4 components Full
    Medium = at least 2 components Full
    Low = fewer than 2 Full
    """
    df = df.copy()

    comp_cols = ["H_Data_Completeness","E_Data_Completeness",
                 "V_Data_Completeness","C_Data_Completeness"]
    available = [c for c in comp_cols if c in df.columns]

    full_count = pd.Series(0, index=df.index)
    for col in available:
        full_count += (df[col].astype(str) == "Full").astype(int)

    df["Data_Confidence"] = pd.cut(
        full_count,
        bins=[-1, 1, 3, 4],
        labels=["Low","Medium","High"],
    ).astype(str)

    # Data confidence note for Low
    df["Data_Confidence_Note"] = np.where(
        df["Data_Confidence"] == "Low",
        "One or more risk index components have Minimal data completeness — "
        "field verification required before prioritising this community for intervention.",
        pd.NA,
    )
    return df


# ---------------------------------------------------------------------------
# G37 — Priority Areas
# ---------------------------------------------------------------------------

def compute_g37_priority() -> Optional[pd.DataFrame]:
    """Assemble and rank all communities; produce G37 output."""
    df = load_inputs()
    if df is None:
        return None

    df = compute_priority_score(df)
    df = classify_priority_tiers(df)
    df = assign_data_confidence(df)

    # Global rank (1 = highest priority)
    df["Priority_Rank"] = (
        df["Priority_Score"].rank(ascending=False, method="min")
        .astype("Int64")
    )

    # Ensure all component scores present for explainability
    for col in ["H_Score","E_Score","V_Score","C_Score","R_Score"]:
        if col not in df.columns:
            df[col] = np.nan

    df["Risk_Model_Version"] = RISK_MODEL_VERSION
    df["Computation_Date"]   = date.today().isoformat()

    # Sensitivity tier comparison (top-20)
    top_cols = [c for c in [
        "Community_ID", "Community", "State_Code", "State_Name", "LGA_Code", "LGA",
        "Priority_Rank", "Priority_Tier", "Priority_Score",
        "R_Score", "R_Class", "Data_Confidence"
    ] if c in df.columns]
    top20 = df.nsmallest(20, "Priority_Rank")[top_cols].copy()

    # Check top-20 stability across sensitivity models
    if "R_Score_S1" in df.columns:
        df["Rank_S1"] = df["R_Score_S1"].rank(ascending=False, method="min").astype("Int64")
        tier_change_s1 = (df["Priority_Tier"] != df.get("Priority_Tier_S1", df["Priority_Tier"])).sum()
        log.info(f"Tier changes baseline vs S1: {tier_change_s1}")

    # Save
    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    DECISION_PRIORITY.mkdir(parents=True, exist_ok=True)

    out_csv     = ANALYSIS_OUTPUTS / "G37_PriorityAreas.csv"
    out_ds      = DECISION_PRIORITY / "G37_PriorityAreas_v1_0.csv"
    out_top20   = DECISION_PRIORITY / "G37_Top20_Priority_Communities.csv"

    df.to_csv(out_csv, index=False)
    df.to_csv(out_ds,  index=False)
    top20.to_csv(out_top20, index=False)

    tier_counts = df["Priority_Tier"].value_counts().sort_index()
    log.info(
        f"G37 Priority Areas saved | {len(df)} communities\n"
        f"  Tier 1 (Highest): {tier_counts.get(1, 0)}\n"
        f"  Tier 2 (High):    {tier_counts.get(2, 0)}\n"
        f"  Tier 3 (Moderate):{tier_counts.get(3, 0)}\n"
        f"  Tier 4 (Lower):   {tier_counts.get(4, 0)}"
    )
    log.info(f"Top-20 priority list saved: {out_top20}")

    update_processing_status("G37", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G37", "GIS Layer", "DERIVE",
        f"G37 Priority Areas computed: {len(df)} communities; "
        f"Tier 1: {tier_counts.get(1, 0)}"
    )
    return df


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "15_PRIORITY — Priority Areas (G37)")
    g37 = compute_g37_priority()
    if g37 is not None:
        log.info("15_priority complete")
    return g37


if __name__ == "__main__":
    run_all()
