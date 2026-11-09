"""
05_climate.py
=============
Climate data processing: temporal aggregation, indicator computation,
time-series QC, and preparation of station summary layer (G21).

Depends on: DB05 (CLEAN), G20 (CLEAN)
Outputs:
  - DB05 aggregated station summaries → G21
  - IND01 flood frequency (partial — event count from DB01/G25)
  - Extreme rainfall flags
  - Dry spell and drought indicators
  - Seasonal means for G22/G23 surface interpolation inputs
"""

from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, GIS_CLEAN, GIS_DERIVED,
    ANALYSIS_OUTPUTS, QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("05_climate")

# Nigeria wet/dry season boundaries (approximate — southern states)
WET_SEASON_MONTHS  = [4, 5, 6, 7, 8, 9, 10]   # Apr–Oct
DRY_SEASON_MONTHS  = [1, 2, 3, 11, 12]          # Nov–Mar

# Extreme rainfall threshold (daily) — to be confirmed in INDICATOR_REGISTER
EXTREME_RAINFALL_DAILY_MM = 100.0


# ---------------------------------------------------------------------------
# Load DB05
# ---------------------------------------------------------------------------

def load_db05(path: Optional[Path] = None) -> pd.DataFrame:
    p = path or DATA_CLEAN / "DB05_Climate_Observations_CLEAN.csv"
    if not p.exists():
        log.warning(f"DB05 not found at {p} — climate processing skipped")
        return pd.DataFrame()
    df = pd.read_csv(p, parse_dates=["Observation_Date"])
    log.info(f"DB05 loaded: {len(df)} records from {df['Station_ID'].nunique()} stations")
    return df


# ---------------------------------------------------------------------------
# Time-series QC (Q15)
# ---------------------------------------------------------------------------

def qc_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag impossible jumps in consecutive daily rainfall per station.
    Sets Rainfall_QC_Flag = 'SUS' for flagged records.
    """
    if df.empty or "Rainfall_mm" not in df.columns:
        return df

    df = df.copy().sort_values(["Station_ID", "Observation_Date"])
    df = df.reset_index(drop=True)  # pandas 3.x: reset after sort to avoid index issues

    # Compute previous rainfall per station using shift
    df["_prev_rain"] = (
        df.groupby("Station_ID", sort=False)["Rainfall_mm"]
        .shift(1)
        .values  # use .values to avoid index alignment issues in pandas 3.x
    )
    df["_rain_jump"] = (df["Rainfall_mm"] - df["_prev_rain"]).abs()

    suspicious = df["_rain_jump"] > 300
    flagged_count = int(suspicious.sum())
    if flagged_count > 0:
        df.loc[suspicious, "Rainfall_QC_Flag"] = "SUS"
        log.warning(f"Time-series QC: {flagged_count} suspicious rainfall jumps flagged")

    df = df.drop(columns=["_prev_rain", "_rain_jump"])
    return df


# ---------------------------------------------------------------------------
# Temporal aggregation
# ---------------------------------------------------------------------------

def aggregate_station_means(
    df: pd.DataFrame,
    start_year: int = 2000,
    end_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Compute mean annual and seasonal rainfall and temperature per station.
    Returns one row per station with summary statistics for G21.
    """
    if df.empty:
        return pd.DataFrame()

    end_year = end_year or date.today().year
    df = df[
        (df["Observation_Date"].dt.year >= start_year) &
        (df["Observation_Date"].dt.year <= end_year) &
        (df["Observation_Period"].isin(["Daily", "Monthly"]))
    ].copy()

    if df.empty:
        log.warning("No daily/monthly records found in specified period")
        return pd.DataFrame()

    df["Year"]  = df["Observation_Date"].dt.year
    df["Month"] = df["Observation_Date"].dt.month
    df["Season"] = df["Month"].apply(
        lambda m: "Wet" if m in WET_SEASON_MONTHS else "Dry"
    )

    # Annual totals then mean across years
    annual = (
        df.groupby(["Station_ID", "Year"])
        .agg(
            Annual_Rainfall_mm    = ("Rainfall_mm",      "sum"),
            Annual_Temp_Max_Mean  = ("Temperature_Max_C", "mean"),
            Annual_Temp_Min_Mean  = ("Temperature_Min_C", "mean"),
            Record_Days           = ("Rainfall_mm",       "count"),
        )
        .reset_index()
    )

    station_summary = (
        annual.groupby("Station_ID")
        .agg(
            Mean_Annual_Rainfall_mm   = ("Annual_Rainfall_mm",   "mean"),
            Std_Annual_Rainfall_mm    = ("Annual_Rainfall_mm",   "std"),
            Mean_Annual_Temp_Max_C    = ("Annual_Temp_Max_Mean",  "mean"),
            Mean_Annual_Temp_Min_C    = ("Annual_Temp_Min_Mean",  "mean"),
            Record_Years              = ("Year",                   "count"),
            Mean_Record_Days_Per_Year = ("Record_Days",            "mean"),
        )
        .reset_index()
    )

    # Completeness flag
    expected_days = 365.25
    station_summary["Completeness_Pct"] = (
        station_summary["Mean_Record_Days_Per_Year"] / expected_days * 100
    ).clip(0, 100).round(1)

    log.info(
        f"Station summaries computed: {len(station_summary)} stations | "
        f"period {start_year}–{end_year}"
    )
    return station_summary


# ---------------------------------------------------------------------------
# Extreme events
# ---------------------------------------------------------------------------

def flag_extreme_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag daily records exceeding EXTREME_RAINFALL_DAILY_MM.
    Sets Extreme_Rainfall_Flag = 'Yes' and records threshold used.
    """
    if df.empty or "Rainfall_mm" not in df.columns:
        return df
    df = df.copy()
    mask = df["Rainfall_mm"] > EXTREME_RAINFALL_DAILY_MM
    df.loc[mask, "Extreme_Rainfall_Flag"]      = "Yes"
    df.loc[mask, "Extreme_Rainfall_Threshold_mm"] = EXTREME_RAINFALL_DAILY_MM
    df.loc[~mask & df["Rainfall_mm"].notna(), "Extreme_Rainfall_Flag"] = "No"
    log.info(f"Extreme rainfall events flagged: {int(mask.sum())} records > {EXTREME_RAINFALL_DAILY_MM}mm")
    return df


def compute_dry_spell(df: pd.DataFrame, threshold_mm: float = 1.0) -> pd.DataFrame:
    """
    Compute consecutive dry days per station per record.
    A 'dry day' is Rainfall_mm < threshold_mm.
    """
    if df.empty or "Rainfall_mm" not in df.columns:
        return df
    df = df.copy().sort_values(["Station_ID", "Observation_Date"])
    df = df.reset_index(drop=True)
    df["_is_dry"] = (df["Rainfall_mm"] < threshold_mm).astype(int)

    # Vectorised consecutive dry spell using cumsum trick
    # Reset counter at each wet day per station
    df["_group_id"] = (
        df.groupby("Station_ID")["_is_dry"]
        .transform(lambda x: (x == 0).cumsum())
    )
    df["Dry_Spell_Days"] = (
        df.groupby(["Station_ID", "_group_id"])["_is_dry"]
        .transform("cumsum")
    )
    df = df.drop(columns=["_is_dry", "_group_id"])
    log.info("Dry spell days computed")
    return df


# ---------------------------------------------------------------------------
# Save G21 station summary layer (CSV — GIS layer built in 04_integrate)
# ---------------------------------------------------------------------------

def save_g21_summary(
    station_summary: pd.DataFrame,
    g20_path: Optional[Path] = None,
) -> Optional[pd.DataFrame]:
    """
    Join station summary to G20 station metadata and save as G21 input CSV.
    """
    if station_summary.empty:
        log.warning("No station summary to save")
        return None

    # Attempt to join G20 coordinates
    g20_csv = g20_path or DATA_CLEAN / "G20_ClimateStations_CLEAN.csv"
    if g20_csv.exists():
        g20 = pd.read_csv(g20_csv)
        merged = station_summary.merge(
            g20[["Station_ID","Station_Name","State_Code","Latitude","Longitude","Elevation_m"]],
            on="Station_ID", how="left"
        )
    else:
        log.warning("G20 station layer not found — G21 will lack coordinates")
        merged = station_summary.copy()

    merged["Computation_Date"] = date.today().isoformat()
    merged["Data_Version"]     = BASELINE_VERSION

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_OUTPUTS / "G21_ClimateObservations_Summary.csv"
    merged.to_csv(out_path, index=False)
    log.info(f"G21 station summary saved: {out_path}")

    update_processing_status("G21", QCStatus.DERIVED)
    append_version_log(BASELINE_VERSION, "G21", "GIS Layer", "DERIVE",
                       f"G21 station summary computed from DB05: {len(merged)} stations")
    return merged


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> None:
    log_separator(log, "05_CLIMATE — Climate Data Processing")
    assert_upstream_clean(["DB05"])

    df = load_db05()
    if df.empty:
        log.warning("No DB05 data — climate module skipped")
        return

    df = qc_time_series(df)
    df = flag_extreme_rainfall(df)
    df = compute_dry_spell(df)

    # Save processed DB05
    out = DATA_CLEAN / "DB05_Climate_Observations_PROCESSED.csv"
    df.to_csv(out, index=False)
    log.info(f"Processed DB05 saved: {out}")

    summary = aggregate_station_means(df)
    save_g21_summary(summary)
    log.info("05_climate complete")


if __name__ == "__main__":
    run_all()
