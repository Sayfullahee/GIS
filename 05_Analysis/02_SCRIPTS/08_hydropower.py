"""
08_hydropower.py
================
Hydropower indicator computation, time-series analysis,
disruption scoring, and G28 facility summary layer.

Depends on: DB04 (CLEAN), G07 (CLEAN)
Outputs:
  - IND07 — Electricity Disruption per community
  - IND08 — Hydropower Disruption per facility
  - G28 facility summary (aggregated from DB04)
  - Generation efficiency and sedimentation trend flags
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS,
    BUFFER_HYDROPOWER_COMM_KM,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("08_hydropower")

# Sedimentation severity encoding for trend analysis
SEDIMENTATION_ORDER = {"None": 0, "Low": 1, "Moderate": 2, "High": 3, "Critical": 4}


# ---------------------------------------------------------------------------
# Load DB04
# ---------------------------------------------------------------------------

def load_db04(path: Optional[Path] = None) -> pd.DataFrame:
    p = path or DATA_CLEAN / "DB04_Hydropower_Water_CLEAN.csv"
    if not p.exists():
        log.warning(f"DB04 CLEAN not found at {p}")
        return pd.DataFrame()
    df = pd.read_csv(p, parse_dates=["Observation_Date"])
    log.info(f"DB04 loaded: {len(df)} observations from {df['Hydro_ID'].nunique()} facilities")
    return df


# ---------------------------------------------------------------------------
# Time-series QC (Q15 for DB04)
# ---------------------------------------------------------------------------

def qc_generation_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Flag impossible year-on-year generation jumps > 200%."""
    if df.empty or "Generation_MWh" not in df.columns:
        return df
    df = df.copy().sort_values(["Hydro_ID", "Observation_Date"])
    df["_Year"] = df["Observation_Date"].dt.year

    annual = (
        df.groupby(["Hydro_ID","_Year"])["Generation_MWh"]
        .sum()
        .reset_index()
    )
    annual["_prev"] = annual.groupby("Hydro_ID")["Generation_MWh"].shift(1)
    annual["_pct_change"] = (
        (annual["Generation_MWh"] - annual["_prev"]) / annual["_prev"].replace(0, np.nan) * 100
    )
    suspicious = annual[annual["_pct_change"].abs() > 200]
    if len(suspicious) > 0:
        log.warning(
            f"DB04 time-series: {len(suspicious)} facility-years with "
            f">200% generation change — flag for operator verification"
        )
    return df.drop(columns=["_Year"])


# ---------------------------------------------------------------------------
# IND08 — Hydropower Disruption
# ---------------------------------------------------------------------------

def compute_ind08(df: pd.DataFrame) -> pd.DataFrame:
    """
    IND08 per facility:
      - Total disruption days
      - Generation loss rate (vs theoretical maximum)
      - Flood damage incidence
      - Sedimentation trend
    Normalised to 0-100 using study-area reference bounds.
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    if "Sedimentation" not in df.columns:
        df["Sedimentation"] = "Low"
    if "Disruption_Duration_Days" not in df.columns:
        df["Disruption_Duration_Days"] = 0
    if "Installed_MW" not in df.columns:
        df["Installed_MW"] = 500.0
    if "Flood_Damage" not in df.columns:
        df["Flood_Damage"] = "No"

    df["_sedimentation_num"] = df["Sedimentation"].map(SEDIMENTATION_ORDER).fillna(0)

    # Disruption days per year
    df["_Year"] = df["Observation_Date"].dt.year
    record_years = df.groupby("Hydro_ID")["_Year"].nunique().reset_index(name="Record_Years")

    facility_summary = (
        df.groupby("Hydro_ID")
        .agg(
            Total_Disruption_Days   = ("Disruption_Duration_Days",  "sum"),
            Total_Generation_MWh    = ("Generation_MWh",            "sum"),
            Installed_MW            = ("Installed_MW",              "first"),
            Flood_Damage_Events     = ("Flood_Damage",
                                       lambda x: (x == "Yes").sum()),
            Max_Sedimentation_Num   = ("_sedimentation_num",        "max"),
            Observation_Count       = ("Observation_ID",            "count"),
        )
        .reset_index()
    )

    facility_summary = facility_summary.merge(record_years, on="Hydro_ID", how="left")
    facility_summary["Record_Years"] = facility_summary["Record_Years"].fillna(1)

    # Annual disruption rate
    facility_summary["Annual_Disruption_Days"] = (
        facility_summary["Total_Disruption_Days"] / facility_summary["Record_Years"]
    )

    # Generation efficiency vs theoretical max
    facility_summary["Theoretical_Max_MWh"] = (
        facility_summary["Installed_MW"] * 8760 * facility_summary["Record_Years"]
    )
    facility_summary["Generation_Efficiency_Pct"] = np.where(
        facility_summary["Theoretical_Max_MWh"] > 0,
        (facility_summary["Total_Generation_MWh"] /
         facility_summary["Theoretical_Max_MWh"] * 100).clip(0, 100),
        np.nan,
    )

    # IND08 composite (generation loss + disruption + flood damage)
    # Normalise components to 0-100 before weighting
    for col in ["Annual_Disruption_Days", "Max_Sedimentation_Num", "Flood_Damage_Events"]:
        mn, mx = facility_summary[col].min(), facility_summary[col].max()
        if mx > mn:
            facility_summary[f"_{col}_norm"] = (
                (facility_summary[col] - mn) / (mx - mn) * 100
            ).clip(0, 100)
        else:
            facility_summary[f"_{col}_norm"] = 0.0

    # Generation loss = inverse of efficiency
    facility_summary["_gen_loss_norm"] = (
        (100 - facility_summary["Generation_Efficiency_Pct"].fillna(50)).clip(0, 100)
    )

    facility_summary["IND08_Hydropower_Disruption"] = (
        0.35 * facility_summary["_Annual_Disruption_Days_norm"] +
        0.35 * facility_summary["_gen_loss_norm"] +
        0.20 * facility_summary["_Flood_Damage_Events_norm"] +
        0.10 * facility_summary["_Max_Sedimentation_Num_norm"]
    ).clip(0, 100)

    # Drop helper columns
    helper_cols = [c for c in facility_summary.columns if c.startswith("_")]
    facility_summary = facility_summary.drop(columns=helper_cols)

    facility_summary["Computation_Date"] = date.today().isoformat()
    log.info(f"IND08 computed for {len(facility_summary)} facilities")
    return facility_summary


# ---------------------------------------------------------------------------
# IND07 — Electricity Disruption (community level)
# ---------------------------------------------------------------------------

def compute_ind07_from_db01(community_df: pd.DataFrame) -> pd.DataFrame:
    """
    IND07 from DB01 Electricity_Access field.
    Where DB04 provides outage data this should be supplemented.
    Encoding: No access = 100; Partial = 50; Yes (with outage data) = scaled.
    """
    result = community_df[["Community_ID"]].copy()

    if "Electricity_Access" in community_df.columns:
        mapping = {"No": 100.0, "Partial": 50.0, "Yes": 20.0, "Unknown": np.nan}
        result["IND07_Electricity_Disruption"] = (
            community_df["Electricity_Access"].map(mapping)
        )
    else:
        result["IND07_Electricity_Disruption"] = np.nan

    log.info("IND07 derived from DB01 Electricity_Access (proxy)")
    return result


# ---------------------------------------------------------------------------
# G28 summary layer
# ---------------------------------------------------------------------------

def build_g28_summary(ind08_df: pd.DataFrame,
                       g07_path: Optional[Path] = None) -> pd.DataFrame:
    """Join IND08 facility summary to G07 coordinates for G28."""
    if ind08_df.empty:
        return pd.DataFrame()

    g07_csv = g07_path or DATA_CLEAN / "G07_HydropowerFacilities_CLEAN.csv"
    if g07_csv.exists():
        g07 = pd.read_csv(g07_csv)
        merged = ind08_df.merge(
            g07[["Hydro_ID","Facility_Name","State_Code",
                 "Latitude","Longitude","Installed_MW"]],
            on="Hydro_ID", how="left", suffixes=("","_g07")
        )
    else:
        log.warning("G07 CLEAN CSV not found — G28 will lack coordinates")
        merged = ind08_df.copy()

    merged["Data_Version"] = BASELINE_VERSION
    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G28_HydroObservations_Summary.csv"
    merged.to_csv(out, index=False)
    log.info(f"G28 summary saved: {out}")
    update_processing_status("G28", QCStatus.DERIVED)
    return merged


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "08_HYDROPOWER — Hydropower Indicator Computation")
    assert_upstream_clean(["DB04"])

    df = load_db04()
    df = qc_generation_timeseries(df)

    ind08_df = compute_ind08(df)
    build_g28_summary(ind08_df)

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if comm_path.exists():
        community_df = pd.read_csv(comm_path)
        ind07_df = compute_ind07_from_db01(community_df)
        out = ANALYSIS_OUTPUTS / "Hydro_Indicators_IND07_IND08.csv"
        ind07_df.to_csv(out, index=False)
        log.info(f"IND07 saved: {out}")

    if not ind08_df.empty:
        out2 = ANALYSIS_OUTPUTS / "IND08_Hydropower_Disruption.csv"
        ind08_df.to_csv(out2, index=False)
        log.info(f"IND08 saved: {out2}")

    log.info("08_hydropower complete")
    return ind08_df


if __name__ == "__main__":
    run_all()
