"""
17_reports.py
=============
Generate analytical tables and community/state profile reports.

Outputs:
  - Community profile tables (one row per community — all indicators + risk)
  - State summary tables (aggregated by state)
  - Descriptive statistics tables (n, mean, SD, median, IQR, min, max)
  - Risk distribution tables
  - Change detection tables (when previous baseline available)
  - All outputs saved to 06_Reports/02_TABLES/

Does NOT produce maps (that is 18_maps.py).
Does NOT expose household-level data.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config import (
    ANALYSIS_OUTPUTS, REPORTS_TABLES, REPORTS_DRAFTS,
    DECISION_RISK, DECISION_PRIORITY,
    DATA_DATE,
)
from logger import get_logger, log_separator

log = get_logger("17_reports")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_read(path: Path) -> Optional[pd.DataFrame]:
    if path.exists():
        return pd.read_csv(path)
    log.warning(f"File not found (skipped): {path.name}")
    return None


def _desc_stats(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    """Descriptive statistics: n, missing, mean, SD, median, IQR, min, max."""
    records = []
    for col in numeric_cols:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        records.append({
            "Variable":    col,
            "N":           int(s.count()),
            "Missing_N":   int(s.isna().sum()),
            "Missing_Pct": round(s.isna().mean() * 100, 1),
            "Mean":        round(s.mean(), 2),
            "SD":          round(s.std(), 2),
            "Median":      round(s.median(), 2),
            "IQR":         round(s.quantile(0.75) - s.quantile(0.25), 2),
            "Min":         round(s.min(), 2),
            "Max":         round(s.max(), 2),
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Community profile table
# ---------------------------------------------------------------------------

def build_community_profile_table() -> Optional[pd.DataFrame]:
    """
    One row per community with: identifiers, indicators, H/E/V/C/R scores,
    priority rank and tier. Draws from G35 (all component scores included).
    """
    g35 = _safe_read(ANALYSIS_OUTPUTS / "G35_CompositeRisk.csv")
    if g35 is None:
        return None

    g36 = _safe_read(ANALYSIS_OUTPUTS / "G36_Adaptation.csv")
    g37 = _safe_read(ANALYSIS_OUTPUTS / "G37_PriorityAreas.csv")

    profile = g35.copy()

    if g36 is not None:
        merge_cols = ["Community_ID","IND09_Adaptation_Coverage","IND10_Adaptation_Gap",
                      "Total_Adaptation_Measures","Structural_Measures_Count",
                      "Nature_Based_Measures_Count"]
        profile = profile.merge(
            g36[[c for c in merge_cols if c in g36.columns]],
            on="Community_ID", how="left"
        )

    if g37 is not None:
        priority_cols = ["Community_ID","Priority_Score","Priority_Tier",
                         "Priority_Rank","Data_Confidence","Data_Confidence_Note"]
        profile = profile.merge(
            g37[[c for c in priority_cols if c in g37.columns]],
            on="Community_ID", how="left"
        )

    # Attach DB01 core attributes
    from config import DATA_CLEAN
    db01 = _safe_read(DATA_CLEAN / "DB01_Community_Master_CLEAN.csv")
    if db01 is not None:
        meta_cols = ["Community_ID", "Community", "State_Name", "LGA", "Population"]
        avail_meta = [c for c in meta_cols if c in db01.columns]
        for c in ["Community", "State_Name", "LGA", "Population"]:
            if c in profile.columns:
                profile = profile.drop(columns=[c])
        profile = profile.merge(db01[avail_meta], on="Community_ID", how="left")

    profile["Report_Date"] = date.today().isoformat()
    profile["Data_Date"]   = DATA_DATE

    REPORTS_TABLES.mkdir(parents=True, exist_ok=True)
    out = REPORTS_TABLES / "TABLE_Community_Profiles.csv"
    profile.to_csv(out, index=False)
    log.info(f"Community profile table: {out} ({len(profile)} communities)")
    return profile


# ---------------------------------------------------------------------------
# State summary table
# ---------------------------------------------------------------------------

def build_state_summary_table(profile: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
    """Population-weighted mean of community scores aggregated to state level."""
    if profile is None:
        profile = _safe_read(REPORTS_TABLES / "TABLE_Community_Profiles.csv")
    if profile is None:
        return None

    score_cols = ["H_Score","E_Score","V_Score","C_Score","R_Score","Priority_Score"]
    available  = [c for c in score_cols if c in profile.columns]

    # Population-weighted mean
    def weighted_mean(group: pd.DataFrame, col: str) -> float:
        if "Population" in group.columns:
            pop = pd.to_numeric(group["Population"], errors="coerce").fillna(1)
        else:
            pop = pd.Series(1.0, index=group.index)
        vals = pd.to_numeric(group[col], errors="coerce")
        valid = vals.notna()
        if valid.sum() == 0:
            return np.nan
        return (vals[valid] * pop[valid]).sum() / pop[valid].sum()

    records = []
    for state, grp in profile.groupby("State_Code"):
        row = {
            "State_Code":         state,
            "State_Name":         grp["State_Name"].iloc[0] if "State_Name" in grp.columns else "",
            "Community_Count":    len(grp),
            "Population_Total":   pd.to_numeric(grp.get("Population", pd.Series(dtype=float)),
                                                 errors="coerce").sum(),
        }
        for col in available:
            row[f"{col}_Wtd_Mean"] = round(weighted_mean(grp, col), 2)
            row[f"{col}_Max"]      = round(pd.to_numeric(grp[col], errors="coerce").max(), 2)

        if "R_Class" in grp.columns:
            for cls in ["Very Low","Low","Moderate","High","Very High"]:
                row[f"N_{cls.replace(' ','_')}"] = int((grp["R_Class"] == cls).sum())

        if "Priority_Tier" in grp.columns:
            for tier in [1,2,3,4]:
                row[f"Tier_{tier}_Count"] = int((grp["Priority_Tier"] == tier).sum())

        records.append(row)

    state_df = pd.DataFrame(records).sort_values("R_Score_Wtd_Mean", ascending=False)
    state_df["Report_Date"] = date.today().isoformat()

    out = REPORTS_TABLES / "TABLE_State_Summaries.csv"
    state_df.to_csv(out, index=False)
    log.info(f"State summary table: {out} ({len(state_df)} states)")
    return state_df


# ---------------------------------------------------------------------------
# Descriptive statistics table
# ---------------------------------------------------------------------------

def build_descriptive_stats_table(profile: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
    """Descriptive stats for all major indicator and risk variables."""
    if profile is None:
        profile = _safe_read(REPORTS_TABLES / "TABLE_Community_Profiles.csv")
    if profile is None:
        return None

    numeric_cols = [
        "H_Score","E_Score","V_Score","C_Score","R_Score",
        "IND01_Flood_Frequency","IND03_Max_Severity_Norm",
        "IND04_River_Proximity_Norm","IND05_Pop_Exposure",
        "IND06_Flood_Infra_Exposure","IND09_Adaptation_Coverage",
        "IND10_Adaptation_Gap","Priority_Score",
    ]

    stats = _desc_stats(profile, numeric_cols)
    stats["Report_Date"] = date.today().isoformat()

    out = REPORTS_TABLES / "TABLE_Descriptive_Statistics.csv"
    stats.to_csv(out, index=False)
    log.info(f"Descriptive statistics table: {out}")
    return stats


# ---------------------------------------------------------------------------
# Risk distribution table
# ---------------------------------------------------------------------------

def build_risk_distribution_table(profile: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
    """Count and % of communities per risk class by state."""
    if profile is None:
        profile = _safe_read(REPORTS_TABLES / "TABLE_Community_Profiles.csv")
    if profile is None or "R_Class" not in profile.columns:
        return None

    dist = (
        profile.groupby(["State_Code","R_Class"])
        .agg(Count=("Community_ID","count"))
        .reset_index()
    )
    totals = profile.groupby("State_Code").size().reset_index(name="Total")
    dist   = dist.merge(totals, on="State_Code")
    dist["Pct"] = (dist["Count"] / dist["Total"] * 100).round(1)

    out = REPORTS_TABLES / "TABLE_Risk_Distribution_by_State.csv"
    dist.to_csv(out, index=False)
    log.info(f"Risk distribution table: {out}")
    return dist


# ---------------------------------------------------------------------------
# Sensitivity analysis summary table
# ---------------------------------------------------------------------------

def build_sensitivity_summary(profile: Optional[pd.DataFrame] = None) -> None:
    """Summary of class changes between baseline and sensitivity models."""
    if profile is None:
        profile = _safe_read(REPORTS_TABLES / "TABLE_Community_Profiles.csv")
    if profile is None:
        return

    rows = []
    for s_col, s_class in [("R_Score_S1","R_Class_S1"),("R_Score_S2","R_Class_S2")]:
        if s_col not in profile.columns:
            continue
        changed = (profile["R_Class"] != profile.get(s_class, profile["R_Class"])).sum()
        rows.append({
            "Model":         s_col.replace("R_Score_",""),
            "Communities_Changing_Class": int(changed),
            "Pct_Changing":  round(changed / len(profile) * 100, 1),
        })

    if rows:
        sens_df = pd.DataFrame(rows)
        out = REPORTS_TABLES / "TABLE_Sensitivity_Analysis.csv"
        sens_df.to_csv(out, index=False)
        log.info(f"Sensitivity summary: {out}")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

def run_all() -> None:
    log_separator(log, "17_REPORTS — Analytical Tables and Profiles")
    REPORTS_TABLES.mkdir(parents=True, exist_ok=True)

    profile    = build_community_profile_table()
    state_df   = build_state_summary_table(profile)
    stats      = build_descriptive_stats_table(profile)
    risk_dist  = build_risk_distribution_table(profile)
    build_sensitivity_summary(profile)

    log.info(
        f"17_reports complete — tables saved to {REPORTS_TABLES}\n"
        f"  Community profiles: {len(profile) if profile is not None else 0} rows\n"
        f"  State summaries:    {len(state_df) if state_df is not None else 0} rows"
    )


if __name__ == "__main__":
    run_all()
