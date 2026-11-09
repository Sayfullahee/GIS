"""
22_land_degradation.py
======================
Land degradation domain processing.

Computes:
  - IND15: NDVI trend (% change/year) per community from G47/G48
  - IND16: RUSLE soil loss (t/ha/yr) per community from G49
  - G50: Land Degradation Index per community (LD_Score 0-100)

Full raster outputs (G47, G48, G49) require remote sensing pipeline
(Google Earth Engine exports or Sentinel-2 processing).
This module processes the tabular/CSV derivatives for community-level scoring.

Depends on: G47 outputs (CSV from GEE), G48 outputs, G49 outputs, DB01 (CLEAN)
"""

from datetime import date
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS, ANALYSIS_INPUTS,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("22_land_degradation")

# LD_Score weights (must match HAZARD_MODEL_DECISIONS.csv HMD07)
LD_WEIGHTS = {
    "IND15_NDVI_Trend_Norm":  0.40,
    "IND16_RUSLE_Norm":       0.40,
    "LC_Change_Norm":         0.20,
}

# RUSLE C-factors by ESA WorldCover class
# (simplified literature values; replace with LKP_RUSLE_C_Factors.csv at production)
RUSLE_C_FACTORS = {
    10: 0.001,   # Tree cover — very high protection
    20: 0.01,    # Shrubland
    30: 0.05,    # Grassland
    40: 0.20,    # Cropland — moderate exposure
    50: 0.00,    # Built-up — sealed surface; RUSLE not applicable
    60: 0.60,    # Bare/sparse vegetation — high erosion risk
    70: 0.00,    # Snow/ice — not applicable
    80: 0.001,   # Water — not applicable
    90: 0.01,    # Wetland
    95: 0.001,   # Mangroves
    100: 0.02,   # Moss/lichen
}


# ---------------------------------------------------------------------------
# Load remote sensing outputs (expected as GEE exports or raster stats CSVs)
# ---------------------------------------------------------------------------

def load_ndvi_community_stats(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load pre-computed NDVI statistics per community.
    Expected columns: Community_ID; NDVI_Mean_2015; NDVI_Mean_Current;
                      NDVI_Trend_pct_per_yr; NDVI_Trend_Pvalue; NDVI_N_Years
    File produced by GEE export or rasterstats zonal statistics on G47/G48.
    """
    p = path or ANALYSIS_INPUTS / "NDVI_Community_Stats.csv"
    if not p.exists():
        log.warning(
            f"NDVI community stats not found at {p}. "
            "Run remote sensing pipeline (GEE) to produce this file. "
            "IND15 will be NULL until available."
        )
        return pd.DataFrame()
    df = pd.read_csv(p)
    log.info(f"NDVI stats loaded: {len(df)} communities from {p}")
    return df


def load_rusle_community_stats(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load pre-computed RUSLE mean soil loss per community.
    Expected columns: Community_ID; RUSLE_Mean_t_ha_yr; RUSLE_Max_t_ha_yr
    File produced by raster zonal statistics on G49.
    """
    p = path or ANALYSIS_INPUTS / "RUSLE_Community_Stats.csv"
    if not p.exists():
        log.warning(
            f"RUSLE stats not found at {p}. "
            "Run RUSLE raster computation (G49) to produce this file. "
            "IND16 will be NULL until available."
        )
        return pd.DataFrame()
    df = pd.read_csv(p)
    log.info(f"RUSLE stats loaded: {len(df)} communities from {p}")
    return df


# ---------------------------------------------------------------------------
# Compute LD_Score
# ---------------------------------------------------------------------------

def compute_ld_score(
    community_df: pd.DataFrame,
    ndvi_df: pd.DataFrame,
    rusle_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge indicators and compute community-level LD_Score."""
    result = community_df[["Community_ID","State_Code","LGA_Code"]].copy()

    # Merge NDVI stats
    if not ndvi_df.empty and "Community_ID" in ndvi_df.columns:
        result = result.merge(
            ndvi_df[["Community_ID"] +
                    [c for c in ["NDVI_Trend_pct_per_yr","NDVI_Trend_Pvalue",
                                  "NDVI_N_Years","NDVI_Mean_2015"]
                     if c in ndvi_df.columns]],
            on="Community_ID", how="left"
        )
    else:
        result["NDVI_Trend_pct_per_yr"] = np.nan

    # Merge RUSLE stats
    if not rusle_df.empty and "Community_ID" in rusle_df.columns:
        result = result.merge(
            rusle_df[["Community_ID"] +
                     [c for c in ["RUSLE_Mean_t_ha_yr","RUSLE_Max_t_ha_yr"]
                      if c in rusle_df.columns]],
            on="Community_ID", how="left"
        )
    else:
        result["RUSLE_Mean_t_ha_yr"] = np.nan

    def _minmax(s: pd.Series) -> pd.Series:
        s = pd.to_numeric(s, errors="coerce")
        mn, mx = s.min(), s.max()
        if pd.isna(mn) or mx == mn:
            return pd.Series(np.where(s.notna(), 50.0, np.nan), index=s.index)
        return ((s - mn) / (mx - mn) * 100).clip(0, 100)

    # IND15: negative NDVI trend = adverse — invert (more negative = higher LD score)
    if "NDVI_Trend_pct_per_yr" in result.columns:
        inverted_trend = -pd.to_numeric(result["NDVI_Trend_pct_per_yr"], errors="coerce")
        result["IND15_NDVI_Trend_Norm"] = _minmax(inverted_trend)
    else:
        result["IND15_NDVI_Trend_Norm"] = np.nan

    # IND16: higher RUSLE soil loss = higher LD
    if "RUSLE_Mean_t_ha_yr" in result.columns:
        rusle_vals = pd.to_numeric(result["RUSLE_Mean_t_ha_yr"], errors="coerce")
        # Log-transform before normalising (skewed distribution)
        log_rusle = np.log1p(rusle_vals)
        result["IND16_RUSLE_Norm"] = _minmax(log_rusle)
    else:
        result["IND16_RUSLE_Norm"] = np.nan

    # LC_Change: placeholder — will be populated when two WorldCover epochs available
    result["LC_Change_Norm"] = np.nan
    result["LC_Change_Note"] = "Requires two WorldCover epochs — set to NULL at baseline"

    # LD_Score weighted sum
    ld_score   = pd.Series(0.0, index=result.index)
    weight_sum = pd.Series(0.0, index=result.index)

    for col, w in LD_WEIGHTS.items():
        if col in result.columns:
            vals  = pd.to_numeric(result[col], errors="coerce")
            avail = vals.notna()
            ld_score   += vals.fillna(0) * w * avail
            weight_sum += w * avail

    result["LD_Score"] = np.where(
        weight_sum > 0,
        (ld_score / weight_sum).clip(0, 100),
        np.nan,
    )

    missing = sum(
        result.get(c, pd.Series(dtype=float)).isna().all()
        for c in ["IND15_NDVI_Trend_Norm","IND16_RUSLE_Norm","LC_Change_Norm"]
    )
    completeness = "Minimal" if missing == 3 else ("Partial" if missing > 0 else "Full")
    result["LD_Data_Completeness"] = completeness
    result["Computation_Date"]     = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G50_LandDegradationIndex.csv"
    result.to_csv(out, index=False)
    log.info(
        f"G50 Land Degradation Index saved: {out} | "
        f"Mean LD_Score: {result['LD_Score'].mean():.1f} | "
        f"Completeness: {completeness}"
    )
    update_processing_status("G50", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G50", "GIS Layer", "DERIVE",
        f"G50 Land Degradation Index computed: {len(result)} communities; "
        f"completeness: {completeness}"
    )
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "22_LAND_DEGRADATION — NDVI Trend + RUSLE + LD Index (G50)")
    assert_upstream_clean(["DB01"])

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community  = pd.read_csv(comm_path)
    ndvi_df    = load_ndvi_community_stats()
    rusle_df   = load_rusle_community_stats()

    result = compute_ld_score(community, ndvi_df, rusle_df)
    log.info("22_land_degradation complete")
    return result


if __name__ == "__main__":
    run_all()
