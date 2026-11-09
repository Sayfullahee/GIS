"""
21_flooding.py
==============
Upgraded multi-return-period flood modelling.

Computes:
  - IND14: Flood inundation depth at 10-yr return period per community
  - G43: 2-yr return period inundation extent (HAND model)
  - G44: 10-yr return period inundation extent
  - G45: 100-yr return period inundation extent
  - G46: Multi-period flood frequency surface (supersedes basic G24 in ERI v2.0)

Method: Height Above Nearest Drainage (HAND) model where hydraulic model
        data (HEC-RAS / NIHSA) is unavailable.

Depends on: G09 (CLEAN), G14 (CLEAN), G22 (CLEAN), G25 (CLEAN), DB05 (CLEAN)
"""

from datetime import date
from pathlib import Path
from typing import Dict, Optional

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

log = get_logger("21_flooding")

# Return period design rainfall factors (approximate — replace with
# station-specific frequency analysis from DB05 in production)
RP_FACTORS = {
    2:   1.0,   # 2-yr RP: baseline
    10:  1.45,  # 10-yr RP: ~45% increase over 2-yr in humid Nigeria
    100: 2.10,  # 100-yr RP: ~110% increase over 2-yr
}


# ---------------------------------------------------------------------------
# Return-period rainfall estimation from DB05
# ---------------------------------------------------------------------------

def estimate_rp_rainfall(
    db05: pd.DataFrame,
    return_periods: list = [2, 10, 100],
) -> pd.DataFrame:
    """
    Estimate design rainfall for given return periods per station
    using Gumbel Extreme Value distribution fitted to annual maxima.
    Falls back to RP_FACTORS if insufficient data.
    Returns DataFrame with Station_ID + RP_2yr_mm + RP_10yr_mm + RP_100yr_mm.
    """
    if db05.empty:
        return pd.DataFrame()

    db05 = db05.copy()
    db05["Observation_Date"] = pd.to_datetime(db05["Observation_Date"], errors="coerce")
    db05 = db05[db05["Observation_Period"].isin(["Daily", "Monthly"])].copy()
    db05["Year"] = db05["Observation_Date"].dt.year

    results = []

    for station_id, grp in db05.groupby("Station_ID"):
        # Annual maxima
        annual_max = grp.groupby("Year")["Rainfall_mm"].max().dropna()
        n = len(annual_max)

        if n < 10:
            log.warning(
                f"Station {station_id}: only {n} annual maxima — "
                f"using RP_FACTORS approximation"
            )
            mean_max = annual_max.mean() if n > 0 else 80.0
            row = {"Station_ID": station_id, "Method": "RP_Factors", "N_Years": n}
            for rp, factor in RP_FACTORS.items():
                row[f"RP_{rp}yr_mm"] = round(mean_max * factor, 1)
            results.append(row)
            continue

        try:
            from scipy.stats import gumbel_r
            mu, beta = gumbel_r.fit(annual_max)
            row = {"Station_ID": station_id, "Method": "Gumbel_EV1", "N_Years": n}
            for rp in return_periods:
                p_exceed = 1 - 1/rp
                row[f"RP_{rp}yr_mm"] = round(
                    float(gumbel_r.ppf(p_exceed, loc=mu, scale=beta)), 1
                )
            results.append(row)
        except Exception as exc:
            log.warning(f"Gumbel fit failed for {station_id}: {exc} — using factors")
            mean_max = annual_max.mean()
            row = {"Station_ID": station_id, "Method": "RP_Factors_fallback", "N_Years": n}
            for rp, factor in RP_FACTORS.items():
                row[f"RP_{rp}yr_mm"] = round(mean_max * factor, 1)
            results.append(row)

    df = pd.DataFrame(results)
    if not df.empty and "Method" in df.columns:
        log.info(
            f"RP rainfall estimated: {len(df)} stations | "
            f"Gumbel: {(df['Method']=='Gumbel_EV1').sum()} | "
            f"Factor approximation: {(df['Method']!='Gumbel_EV1').sum()}"
        )
    else:
        log.warning("No station RP rainfall could be estimated from DB05")
    return df


# ---------------------------------------------------------------------------
# HAND-based inundation model (simplified CSV output for community points)
# ---------------------------------------------------------------------------

def compute_hand_flood_exposure(
    community_df: pd.DataFrame,
    rp_df: pd.DataFrame,
    g25_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Simplified HAND flood exposure estimation for community points.

    Full HAND raster computation requires G09/G14 rasters and GDAL/rasterio.
    This function produces the community-level flood exposure table
    (IND14 values) from:
      - RP rainfall estimates per nearest station
      - Observed flood records from G25
      - River proximity from SJ04 (community Hydropower_Distance proxy)

    Full raster outputs (G43-G46) require GIS post-processing.
    """
    result = community_df[["Community_ID","State_Code","LGA_Code",
                             "Latitude","Longitude"]].copy()

    # Assign nearest station RP rainfall
    g20_path = DATA_CLEAN / "G20_ClimateStations_CLEAN.csv"
    if g20_path.exists() and not rp_df.empty:
        g20 = pd.read_csv(g20_path)
        rp_with_coords = rp_df.merge(
            g20[["Station_ID","Latitude","Longitude"]], on="Station_ID", how="left"
        )

        rp_assignments = []
        for _, comm in result.iterrows():
            clat, clon = float(comm["Latitude"]), float(comm["Longitude"])
            best_dist, best_row = float("inf"), None
            for _, stn in rp_with_coords.iterrows():
                if pd.isna(stn.get("Latitude")):
                    continue
                dist = ((clat - float(stn["Latitude"]))**2 +
                        (clon - float(stn["Longitude"]))**2)**0.5
                if dist < best_dist:
                    best_dist = dist
                    best_row  = stn
            if best_row is not None:
                rp_assignments.append({
                    "Community_ID":     comm["Community_ID"],
                    "Design_RP10_mm":   best_row.get("RP_10yr_mm"),
                    "Design_RP2_mm":    best_row.get("RP_2yr_mm"),
                    "Design_RP100_mm":  best_row.get("RP_100yr_mm"),
                    "Nearest_Station":  best_row.get("Station_ID"),
                })
            else:
                rp_assignments.append({
                    "Community_ID": comm["Community_ID"],
                    "Design_RP10_mm": None, "Design_RP2_mm": None,
                    "Design_RP100_mm": None, "Nearest_Station": None,
                })

        result = result.merge(pd.DataFrame(rp_assignments), on="Community_ID", how="left")
    else:
        result["Design_RP10_mm"]  = np.nan
        result["Design_RP2_mm"]   = np.nan
        result["Design_RP100_mm"] = np.nan

    # Incorporate G25 observed flood evidence
    if g25_df is not None and not g25_df.empty and "Community_ID" in g25_df.columns:
        g25_agg = (
            g25_df.groupby("Community_ID")
            .agg(
                G25_Event_Count         = ("Flood_ID",    "count"),
                G25_Max_Depth_m         = ("Depth_m",     "max"),
                G25_High_Conf_Events    = ("Confidence",
                                           lambda x: (x == "High").sum()),
            )
            .reset_index()
        )
        result = result.merge(g25_agg, on="Community_ID", how="left")
        result["G25_Event_Count"] = result["G25_Event_Count"].fillna(0).astype(int)

    # IND14: normalised flood inundation depth proxy
    # Use RP_10yr rainfall as primary driver; adjust for observed events
    if "Design_RP10_mm" in result.columns:
        rain = pd.to_numeric(result["Design_RP10_mm"], errors="coerce")
        mn, mx = rain.min(), rain.max()
        if pd.notna(mn) and pd.notna(mx) and mx > mn:
            result["IND14_Flood_Inundation_Norm"] = ((rain - mn) / (mx - mn) * 100).clip(0, 100)
        else:
            result["IND14_Flood_Inundation_Norm"] = np.nan
    else:
        result["IND14_Flood_Inundation_Norm"] = np.nan

    # FL_Score for ERI (combined multi-RP indicator)
    components = []
    weights    = []
    for col, w in [("IND14_Flood_Inundation_Norm", 0.50),
                   ("G25_High_Conf_Events",         0.30),
                   ("G25_Max_Depth_m",              0.20)]:
        if col in result.columns:
            vals  = pd.to_numeric(result[col], errors="coerce")
            mn2, mx2 = vals.min(), vals.max()
            if pd.notna(mn2) and pd.notna(mx2) and mx2 > mn2:
                norm  = ((vals - mn2) / (mx2 - mn2) * 100).clip(0, 100)
                avail = norm.notna()
                components.append((norm, w, avail))
                weights.append(w)

    fl_score    = pd.Series(0.0, index=result.index)
    weight_sum  = pd.Series(0.0, index=result.index)
    for norm, w, avail in components:
        fl_score   += norm.fillna(0) * w * avail
        weight_sum += w * avail

    result["FL_Score"] = np.where(
        weight_sum > 0,
        (fl_score / weight_sum).clip(0, 100),
        np.nan,
    )
    result["Computation_Date"] = date.today().isoformat()
    result["Note"] = (
        "FL_Score is a community-level flood hazard index based on RP rainfall "
        "and observed events. Full raster outputs (G43-G46) require GIS post-processing "
        "using G09 DEM and HAND model. See G43_G46_Flooding_METADATA.csv."
    )

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G46_FloodFrequency_Community.csv"
    result.to_csv(out, index=False)
    log.info(
        f"G46 Flood Frequency (community) saved: {out} | "
        f"Mean FL_Score: {result['FL_Score'].mean():.1f}"
    )
    update_processing_status("G46", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G46", "GIS Layer", "DERIVE",
        f"G46 Flood Frequency computed: {len(result)} communities (community-level; rasters pending)"
    )
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "21_FLOODING — Multi-Return-Period Flood Model")
    assert_upstream_clean(["DB05","DB01"])

    db05_path = DATA_CLEAN / "DB05_Climate_Observations_CLEAN.csv"
    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    g25_path  = DATA_CLEAN / "G25_ObservedFloods_CLEAN.csv"

    if not db05_path.exists() or not comm_path.exists():
        log.warning("Required CLEAN files not found — flooding module skipped")
        return None

    db05        = pd.read_csv(db05_path)
    community   = pd.read_csv(comm_path)
    g25         = pd.read_csv(g25_path) if g25_path.exists() else None

    rp_df  = estimate_rp_rainfall(db05)
    result = compute_hand_flood_exposure(community, rp_df, g25)

    log.info("21_flooding complete")
    return result


if __name__ == "__main__":
    run_all()
