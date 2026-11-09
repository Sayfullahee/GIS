"""
06_flood.py
===========
Flood-related indicator computation and observed flood processing.

Depends on: DB01 (CLEAN), G25 (CLEAN), DB05/G21 (CLEAN)
Outputs:
  - IND01 — Flood Frequency (events/year per community)
  - IND02 — Flood Severity (composite score per event)
  - G25 attribute enrichment (confidence-weighted statistics)
  - Flood event summary per community
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, GIS_CLEAN, ANALYSIS_OUTPUTS,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("06_flood")

# Confidence weights for IND02 severity composite
CONFIDENCE_WEIGHTS = {"High": 1.0, "Medium": 0.7, "Low": 0.4}

# IND02 component weights (indicative — must be approved in INDICATOR_REGISTER)
# Depth 30%; Duration 25%; Area 20%; Households 15%; Infrastructure 10%
IND02_WEIGHTS = {
    "Depth_m":               0.30,
    "Duration_days":         0.25,
    "Area_Affected_sqkm":    0.20,
    "Households_Affected":   0.15,
    "Infra_Affected_Binary": 0.10,
}


# ---------------------------------------------------------------------------
# Load G25 observed floods
# ---------------------------------------------------------------------------

def load_g25(path: Optional[Path] = None) -> pd.DataFrame:
    p = path or DATA_CLEAN / "G25_ObservedFloods_CLEAN.csv"
    if not p.exists():
        log.warning(f"G25 not found at {p} — flood indicators will use DB01 only")
        return pd.DataFrame()
    df = pd.read_csv(p, parse_dates=["Date"])
    log.info(f"G25 loaded: {len(df)} flood events")
    return df


# ---------------------------------------------------------------------------
# IND01 — Flood Frequency
# ---------------------------------------------------------------------------

def compute_ind01(
    community_df: pd.DataFrame,
    flood_df: pd.DataFrame,
    obs_start_year: int = 2000,
) -> pd.DataFrame:
    """
    IND01 = count of flood events per community / observation years.
    Source: G25 events + DB01 Flood_Experience flag.
    """
    obs_years = date.today().year - obs_start_year
    if obs_years < 1:
        obs_years = 1

    result = community_df[["Community_ID"]].copy()

    if not flood_df.empty and "Community_ID" in flood_df.columns:
        # Count events per community from G25
        event_counts = (
            flood_df[flood_df["Date"].dt.year >= obs_start_year]
            .groupby("Community_ID")
            .size()
            .reset_index(name="Flood_Event_Count")
        )
        result = result.merge(event_counts, on="Community_ID", how="left")
        result["Flood_Event_Count"] = result["Flood_Event_Count"].fillna(0).astype(int)
    else:
        # Fallback: use DB01 Flood_Experience binary flag
        if "Flood_Experience" in community_df.columns:
            result["Flood_Event_Count"] = (
                community_df["Flood_Experience"].eq("Yes").astype(int)
            )
        else:
            result["Flood_Event_Count"] = np.nan

    result["IND01_Flood_Frequency"] = result["Flood_Event_Count"] / obs_years
    result["IND01_Obs_Years"]       = obs_years
    log.info(f"IND01 computed: {result['IND01_Flood_Frequency'].notna().sum()} communities")
    return result


# ---------------------------------------------------------------------------
# IND02 — Flood Severity
# ---------------------------------------------------------------------------

def _normalise_component(series: pd.Series) -> pd.Series:
    """Min-max normalise a series to 0-100."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(np.where(series.notna(), 50.0, np.nan), index=series.index)
    return ((series - mn) / (mx - mn) * 100).clip(0, 100)


def compute_ind02(flood_df: pd.DataFrame) -> pd.DataFrame:
    """
    IND02 = weighted composite of flood severity components per event.
    Note: IND02 weighting scheme must be approved before use in production.
    """
    if flood_df.empty:
        return pd.DataFrame()

    df = flood_df.copy()

    # Binary infrastructure affected
    if "Infrastructure_Affected" in df.columns:
        df["Infra_Affected_Binary"] = df["Infrastructure_Affected"].notna().astype(float)
    else:
        df["Infra_Affected_Binary"] = np.nan

    score = pd.Series(0.0, index=df.index)
    weight_used = 0.0

    for col, w in IND02_WEIGHTS.items():
        if col in df.columns:
            norm = _normalise_component(pd.to_numeric(df[col], errors="coerce"))
            available = norm.notna()
            score = score + norm.fillna(0) * w * available
            weight_used += w * available.mean()

    # Apply confidence weight
    conf_w = df["Confidence"].map(CONFIDENCE_WEIGHTS).fillna(0.5)
    df["IND02_Flood_Severity_Raw"]        = score
    df["IND02_Flood_Severity_Conf_Wt"]    = score * conf_w
    df["IND02_Confidence_Weight_Applied"] = conf_w

    log.info(f"IND02 computed for {len(df)} flood events")
    return df


# ---------------------------------------------------------------------------
# Community-level flood summary
# ---------------------------------------------------------------------------

def summarise_floods_by_community(
    flood_df: pd.DataFrame,
    ind01_df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate flood events to community level for risk index inputs."""
    if flood_df.empty:
        return ind01_df

    summary = (
        flood_df.groupby("Community_ID")
        .agg(
            IND02_Max_Severity    = ("IND02_Flood_Severity_Raw",     "max"),
            IND02_Mean_Severity   = ("IND02_Flood_Severity_Raw",     "mean"),
            Max_Depth_m           = ("Depth_m",                      "max"),
            Max_Duration_days     = ("Duration_days",                 "max"),
            Max_Households_Affected = ("Households_Affected",        "max"),
            High_Confidence_Events  = ("Confidence",
                                        lambda x: (x == "High").sum()),
        )
        .reset_index()
    )

    result = ind01_df.merge(summary, on="Community_ID", how="left")
    return result


# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------

def save_flood_indicators(df: pd.DataFrame) -> None:
    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "Flood_Indicators_IND01_IND02.csv"
    df.to_csv(out, index=False)
    log.info(f"Flood indicators saved: {out}")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "06_FLOOD — Flood Indicator Computation")
    assert_upstream_clean(["DB01"])

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if not comm_path.exists():
        log.warning("DB01 CLEAN not found — flood module skipped")
        return None

    community_df = pd.read_csv(comm_path)
    flood_df     = load_g25()

    ind01_df = compute_ind01(community_df, flood_df)

    if not flood_df.empty:
        flood_df = compute_ind02(flood_df)
        combined = summarise_floods_by_community(flood_df, ind01_df)
    else:
        combined = ind01_df

    save_flood_indicators(combined)
    log.info("06_flood complete")
    return combined


if __name__ == "__main__":
    run_all()
