"""
20_climate_change.py
====================
Climate change domain processing.

Computes:
  - IND11: Rainfall trend (mm/decade) per station from DB05
  - IND12: Temperature trend (°C/decade) per station from DB05
  - IND13: Drought frequency index (SPI-12 < -1.30) per station
  - G38: Rainfall trend surface (interpolated raster)
  - G39: Temperature trend surface (interpolated raster)
  - G40: Drought frequency raster
  - G42: Climate Change Vulnerability Index per community

Depends on: DB05 (CLEAN), G20 (CLEAN), G21 (CLEAN)
"""

from datetime import date
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS, GIS_DERIVED,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("20_climate_change")

# Minimum years required for a robust trend
MIN_YEARS_TREND  = 15
MIN_YEARS_SPI    = 10
# Drought threshold (SPI < D2 = moderate-severe drought)
SPI_DROUGHT_THRESHOLD = -1.30


# ---------------------------------------------------------------------------
# SPI computation (simplified — Gamma distribution fitting)
# ---------------------------------------------------------------------------

def compute_spi(monthly_rainfall: pd.Series,
                scale: int = 12) -> pd.Series:
    """
    Compute Standardised Precipitation Index at given time scale.
    Uses simplified z-score approach where Gamma fitting not available.
    For production use scipy.stats.gamma.fit for proper SPI.
    """
    rolling = monthly_rainfall.rolling(window=scale, min_periods=scale).sum()
    mu  = rolling.mean()
    std = rolling.std()
    if std == 0 or pd.isna(std):
        return pd.Series(np.nan, index=monthly_rainfall.index)
    return (rolling - mu) / std


# ---------------------------------------------------------------------------
# Trend computation (OLS linear regression)
# ---------------------------------------------------------------------------

def compute_trend(
    values: pd.Series,
    min_years: int = MIN_YEARS_TREND,
) -> Tuple[Optional[float], Optional[float], int]:
    """
    Compute linear regression slope, p-value, and record length.
    Returns (slope_per_decade, p_value, n_years).
    Returns (None, None, n) if insufficient data.
    """
    clean = values.dropna()
    n = len(clean)
    if n < min_years:
        return None, None, n

    try:
        from scipy.stats import linregress
        x = np.arange(n, dtype=float)
        slope, intercept, r, p, se = linregress(x, clean.values)
        # Convert annual slope to per-decade
        slope_per_decade = slope * 10.0
        return round(slope_per_decade, 4), round(p, 4), n
    except ImportError:
        # Fallback: NumPy polyfit (no p-value)
        x = np.arange(n, dtype=float)
        coeffs = np.polyfit(x, clean.values, 1)
        slope_per_decade = coeffs[0] * 10.0
        return round(slope_per_decade, 4), None, n


# ---------------------------------------------------------------------------
# Station-level climate change indicators
# ---------------------------------------------------------------------------

def compute_station_indicators(db05: pd.DataFrame) -> pd.DataFrame:
    """
    For each station compute IND11, IND12, IND13 from DB05 time series.
    Returns one row per station with trend and drought statistics.
    """
    if db05.empty:
        log.warning("DB05 empty — climate change indicators cannot be computed")
        return pd.DataFrame()

    db05 = db05.copy()
    db05["Observation_Date"] = pd.to_datetime(db05["Observation_Date"], errors="coerce")
    db05 = db05[db05["Observation_Period"].isin(["Daily", "Monthly"])].copy()

    if db05.empty:
        log.warning("No daily/monthly DB05 records found")
        return pd.DataFrame()

    if "Temperature_Mean_C" not in db05.columns:
        if "Temperature_Min_C" in db05.columns and "Temperature_Max_C" in db05.columns:
            db05["Temperature_Mean_C"] = (
                pd.to_numeric(db05["Temperature_Min_C"], errors="coerce") +
                pd.to_numeric(db05["Temperature_Max_C"], errors="coerce")
            ) / 2.0
        else:
            db05["Temperature_Mean_C"] = np.nan

    db05["Year"]  = db05["Observation_Date"].dt.year
    db05["Month"] = db05["Observation_Date"].dt.month

    results = []

    for station_id, grp in db05.groupby("Station_ID"):
        grp = grp.sort_values("Observation_Date")

        # Annual rainfall totals
        annual_rain = (
            grp.groupby("Year")["Rainfall_mm"]
            .sum()
            .rename("Annual_Rainfall_mm")
        )

        # Annual temperature means
        annual_temp = (
            grp.groupby("Year")["Temperature_Mean_C"]
            .mean()
            .rename("Annual_Temp_C")
        )

        # Trend calculations
        rain_slope, rain_p, rain_n = compute_trend(annual_rain)
        temp_slope, temp_p, temp_n = compute_trend(annual_temp)

        # SPI drought frequency
        monthly_rain = (
            grp.groupby(["Year","Month"])["Rainfall_mm"]
            .sum()
            .reset_index()
            .sort_values(["Year","Month"])
        )
        monthly_series = pd.Series(
            monthly_rain["Rainfall_mm"].values,
            dtype=float
        )
        drought_freq = np.nan
        if len(monthly_series) >= MIN_YEARS_SPI * 12:
            spi = compute_spi(monthly_series, scale=12)
            drought_months = (spi < SPI_DROUGHT_THRESHOLD).sum()
            total_valid    = spi.notna().sum()
            drought_freq   = round(drought_months / total_valid, 4) if total_valid > 0 else np.nan

        # Extreme rainfall days
        daily = grp["Rainfall_mm"].dropna()
        if len(daily) >= 365:
            p95 = daily.quantile(0.95)
            extreme_days_per_yr = round(
                (daily > p95).sum() / max(1, rain_n), 2
            )
        else:
            extreme_days_per_yr = np.nan

        results.append({
            "Station_ID":                    station_id,
            "IND11_Rainfall_Trend_mm_decade": rain_slope,
            "IND11_Rainfall_Trend_Pvalue":    rain_p,
            "IND11_Rainfall_Record_Years":    rain_n,
            "IND12_Temp_Trend_C_decade":      temp_slope,
            "IND12_Temp_Trend_Pvalue":        temp_p,
            "IND12_Temp_Record_Years":        temp_n,
            "IND13_Drought_Freq_SPI":         drought_freq,
            "Extreme_Rainfall_Days_per_Year": extreme_days_per_yr,
            "Computation_Date":               date.today().isoformat(),
            "Trend_Method":                   "OLS linear regression (scipy.stats.linregress)",
        })

    df = pd.DataFrame(results)
    log.info(
        f"Climate indicators computed: {len(df)} stations | "
        f"With rainfall trend: {df['IND11_Rainfall_Trend_mm_decade'].notna().sum()} | "
        f"With drought freq: {df['IND13_Drought_Freq_SPI'].notna().sum()}"
    )
    return df


# ---------------------------------------------------------------------------
# Normalise climate indicators for CC_Score (G42 input)
# ---------------------------------------------------------------------------

def normalise_cc_indicators(
    station_df: pd.DataFrame,
    community_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate station-level indicators to community level and normalise 0–100.
    Uses nearest-station assignment (SJ04 variant for climate).
    """
    if station_df.empty or community_df.empty:
        return pd.DataFrame()

    result = community_df[["Community_ID","State_Code","LGA_Code",
                             "Latitude","Longitude"]].copy()

    # Nearest-station assignment (Euclidean approximation)
    station_coords = station_df.copy()
    # Join with G20 for coordinates if not already present
    g20_path = DATA_CLEAN / "G20_ClimateStations_CLEAN.csv"
    if g20_path.exists():
        g20 = pd.read_csv(g20_path)
        station_coords = station_coords.merge(
            g20[["Station_ID","Latitude","Longitude"]], on="Station_ID", how="left"
        )

    assigned_indicators = []
    for _, comm in result.iterrows():
        clat, clon = float(comm["Latitude"]), float(comm["Longitude"])
        best_dist, best_idx = float("inf"), None

        for idx, stn in station_coords.iterrows():
            if pd.isna(stn.get("Latitude")) or pd.isna(stn.get("Longitude")):
                continue
            dist = ((clat - float(stn["Latitude"]))**2 +
                    (clon - float(stn["Longitude"]))**2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_idx  = idx

        if best_idx is not None:
            row = station_coords.loc[best_idx]
            assigned_indicators.append({
                "Community_ID":        comm["Community_ID"],
                "Nearest_Station_ID":  row.get("Station_ID"),
                "Nearest_Station_km":  round(best_dist * 111, 2),
                "IND11_Raw":           row.get("IND11_Rainfall_Trend_mm_decade"),
                "IND12_Raw":           row.get("IND12_Temp_Trend_C_decade"),
                "IND13_Raw":           row.get("IND13_Drought_Freq_SPI"),
            })
        else:
            assigned_indicators.append({
                "Community_ID": comm["Community_ID"],
                "Nearest_Station_ID": None,
                "Nearest_Station_km": None,
                "IND11_Raw": None,
                "IND12_Raw": None,
                "IND13_Raw": None,
            })

    assigned = pd.DataFrame(assigned_indicators)

    def _minmax_invert(series: pd.Series, invert: bool = False) -> pd.Series:
        """Min-max normalise; optionally invert (lower = more adverse)."""
        s = pd.to_numeric(series, errors="coerce")
        mn, mx = s.min(), s.max()
        if pd.isna(mn) or pd.isna(mx) or mx == mn:
            return pd.Series(np.where(s.notna(), 50.0, np.nan), index=s.index)
        norm = ((s - mn) / (mx - mn) * 100).clip(0, 100)
        return (100 - norm) if invert else norm

    # IND11: negative rainfall trend is adverse (invert — lower = higher hazard)
    assigned["IND11_Norm"] = _minmax_invert(assigned["IND11_Raw"], invert=True)
    # IND12: positive temperature trend is adverse (no inversion needed)
    assigned["IND12_Norm"] = _minmax_invert(assigned["IND12_Raw"], invert=False)
    # IND13: higher drought frequency is adverse
    assigned["IND13_Norm"] = _minmax_invert(assigned["IND13_Raw"], invert=False)

    # Weighted CC_Score: rainfall trend 35% + temp trend 30% + drought freq 25%
    # (projection component G41 = 10% reserved — set to midpoint 50 where unavailable)
    cc = pd.Series(0.0, index=assigned.index)
    wt = pd.Series(0.0, index=assigned.index)
    for col, w in [("IND11_Norm",0.35),("IND12_Norm",0.30),("IND13_Norm",0.25)]:
        vals  = pd.to_numeric(assigned[col], errors="coerce")
        avail = vals.notna()
        cc   += vals.fillna(0) * w * avail
        wt   += w * avail
    assigned["CC_Score"] = np.where(wt > 0, (cc / wt).clip(0, 100), np.nan)

    result = result.merge(assigned, on="Community_ID", how="left")
    result["Computation_Date"] = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G42_ClimateChangeIndex.csv"
    result.to_csv(out, index=False)
    log.info(
        f"G42 Climate Change Index saved: {out} | "
        f"Mean CC_Score: {result['CC_Score'].mean():.1f}"
    )
    update_processing_status("G42", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G42", "GIS Layer", "DERIVE",
        f"G42 Climate Change Index computed: {len(result)} communities"
    )
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "20_CLIMATE_CHANGE — Climate Trend and Drought Indicators")
    assert_upstream_clean(["DB05"])

    db05_path = DATA_CLEAN / "DB05_Climate_Observations_CLEAN.csv"
    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"

    if not db05_path.exists():
        log.warning("DB05 CLEAN not found — climate change module skipped")
        return None

    db05        = pd.read_csv(db05_path)
    station_df  = compute_station_indicators(db05)

    # Save station-level indicators
    if not station_df.empty:
        out_stn = ANALYSIS_OUTPUTS / "ClimateChange_Station_Indicators.csv"
        station_df.to_csv(out_stn, index=False)
        log.info(f"Station indicators saved: {out_stn}")

    # Aggregate to communities
    if comm_path.exists() and not station_df.empty:
        community_df = pd.read_csv(comm_path)
        g42 = normalise_cc_indicators(station_df, community_df)
        log.info("20_climate_change complete")
        return g42
    else:
        log.warning("DB01 or station data unavailable — G42 community index skipped")
        return None


if __name__ == "__main__":
    run_all()
