"""
23_deforestation.py
===================
Deforestation domain processing.

Computes:
  - IND17: Deforestation rate (%/year) per community from G53
  - G54: Deforestation Pressure Index per community (DF_Score 0–100)

Full raster computation (G51–G53) requires Hansen GFC data download
and remote sensing pipeline. This module processes community-level
derivatives from those rasters.

Depends on: G51/G52/G53 raster stats CSVs (from GEE or rasterstats),
            DB01 (CLEAN), G03 (CLEAN), G16 (CLEAN)
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

log = get_logger("23_deforestation")

# Forest definition threshold (must match HMD08 when decided)
FOREST_CANOPY_THRESHOLD_PCT = 30

# DF_Score weights (must be formalised in HAZARD_MODEL_DECISIONS.csv HMD08)
DF_WEIGHTS = {
    "IND17_DeforestRate_Norm":   0.35,
    "ForestProximity_Norm":      0.35,
    "PatchSize_Norm":            0.30,
}


# ---------------------------------------------------------------------------
# Load forest stats CSVs (from remote sensing pipeline)
# ---------------------------------------------------------------------------

def load_forest_community_stats(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load Hansen GFC-derived forest statistics per community.
    Expected columns: Community_ID; Forest_2015_ha; Forest_Current_ha;
                      Annual_Loss_ha; Annual_Loss_Pct; Forest_Patch_Mean_ha
    File produced by GEE or raster zonal statistics on G51/G52/G53.
    """
    p = path or ANALYSIS_INPUTS / "Forest_Community_Stats.csv"
    if not p.exists():
        log.warning(
            f"Forest community stats not found at {p}. "
            "Download Hansen GFC data and run remote sensing pipeline. "
            "IND17 and DF_Score will be NULL until available."
        )
        return pd.DataFrame()
    df = pd.read_csv(p)
    log.info(f"Forest stats loaded: {len(df)} communities")
    return df


# ---------------------------------------------------------------------------
# Compute DF_Score
# ---------------------------------------------------------------------------

def compute_df_score(
    community_df: pd.DataFrame,
    forest_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge forest indicators and compute community-level DF_Score."""
    result = community_df[["Community_ID","State_Code","LGA_Code",
                             "Latitude","Longitude"]].copy()

    if not forest_df.empty and "Community_ID" in forest_df.columns:
        result = result.merge(forest_df, on="Community_ID", how="left")
    else:
        log.warning("No forest stats available — DF_Score will be NULL")
        result["Annual_Loss_Pct"]   = np.nan
        result["Forest_2015_ha"]    = np.nan
        result["Forest_Current_ha"] = np.nan

    def _minmax(s: pd.Series, log_transform: bool = False) -> pd.Series:
        s = pd.to_numeric(s, errors="coerce")
        if log_transform:
            s = np.log1p(s.clip(lower=0))
        mn, mx = s.min(), s.max()
        if pd.isna(mn) or mx == mn:
            return pd.Series(np.where(s.notna(), 50.0, np.nan), index=s.index)
        return ((s - mn) / (mx - mn) * 100).clip(0, 100)

    # IND17: annual deforestation rate (%) — higher = more adverse
    if "Annual_Loss_Pct" in result.columns:
        result["IND17_DeforestRate_Norm"] = _minmax(
            pd.to_numeric(result["Annual_Loss_Pct"], errors="coerce")
        )
    else:
        result["IND17_DeforestRate_Norm"] = np.nan

    # Forest proximity: distance to remaining forest (inverted — closer = better)
    # Proxy: proportion of original 2015 forest remaining
    if all(c in result.columns for c in ["Forest_2015_ha","Forest_Current_ha"]):
        baseline = pd.to_numeric(result["Forest_2015_ha"], errors="coerce")
        current  = pd.to_numeric(result["Forest_Current_ha"], errors="coerce")
        pct_remaining = np.where(baseline > 0, current / baseline * 100, np.nan)
        # Invert: lower remaining = higher deforestation pressure
        result["ForestProximity_Norm"] = (100 - pd.Series(
            pct_remaining, index=result.index
        ).clip(0, 100))
    else:
        result["ForestProximity_Norm"] = np.nan

    # Patch size: smaller patches = higher fragmentation pressure (inverted)
    if "Forest_Patch_Mean_ha" in result.columns:
        # Log-transform; invert (smaller patches = higher score)
        patch = pd.to_numeric(result["Forest_Patch_Mean_ha"], errors="coerce")
        log_patch = np.log1p(patch)
        normalized = _minmax(log_patch)
        result["PatchSize_Norm"] = 100 - normalized   # invert
    else:
        result["PatchSize_Norm"] = np.nan

    # DF_Score weighted sum
    df_score   = pd.Series(0.0, index=result.index)
    weight_sum = pd.Series(0.0, index=result.index)

    for col, w in DF_WEIGHTS.items():
        if col in result.columns:
            vals  = pd.to_numeric(result[col], errors="coerce")
            avail = vals.notna()
            df_score   += vals.fillna(0) * w * avail
            weight_sum += w * avail

    result["DF_Score"] = np.where(
        weight_sum > 0,
        (df_score / weight_sum).clip(0, 100),
        np.nan,
    )

    result["DF_Data_Completeness"] = np.where(
        result["IND17_DeforestRate_Norm"].notna(), "Available", "Pending_Remote_Sensing"
    )
    result["Computation_Date"] = date.today().isoformat()
    result["Forest_Threshold_Pct_Canopy"] = FOREST_CANOPY_THRESHOLD_PCT
    result["Note"] = (
        "DF_Score requires Hansen GFC data. Until G51-G53 rasters are built, "
        "scores are NULL. See G51_G54_Deforestation_METADATA.csv and SRC020."
    )

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G54_DeforestationPressureIndex.csv"
    result.to_csv(out, index=False)
    log.info(
        f"G54 Deforestation Pressure Index saved: {out} | "
        f"Communities with data: {result['IND17_DeforestRate_Norm'].notna().sum()}/{len(result)}"
    )
    update_processing_status("G54", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G54", "GIS Layer", "DERIVE",
        f"G54 Deforestation Index computed: {len(result)} communities"
    )
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "23_DEFORESTATION — Hansen GFC + Deforestation Pressure (G54)")
    assert_upstream_clean(["DB01"])

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community  = pd.read_csv(comm_path)
    forest_df  = load_forest_community_stats()

    result = compute_df_score(community, forest_df)
    log.info("23_deforestation complete")
    return result


if __name__ == "__main__":
    run_all()
