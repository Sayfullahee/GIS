"""
25_biodiversity.py
==================
Biodiversity domain processing.

Computes:
  - IND20: Habitat Integrity Score per community from G60
  - IND21: Protected Area Coverage % per community from G59
  - IND22: Ecosystem Services Loss proxy per community from G62
  - G63: Biodiversity Loss Index per community (BL_Score 0–100)

Full raster outputs (G59–G62) require external data (WDPA, Hansen GFC,
remote sensing). This module processes community-level derivatives.

Depends on: DB01 (CLEAN), DB09 (CLEAN — optional), G59/G60/G62/G63 CSV stats
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

log = get_logger("25_biodiversity")

# BL_Score weights (must be formalised in HAZARD_MODEL_DECISIONS.csv HMD09)
BL_WEIGHTS = {
    "IND20_HabitatIntegrity_Deficit": 0.35,  # 100 - G60 score
    "IND17_DeforestRate_Norm":        0.30,   # from 23_deforestation
    "IND21_PA_Gap_Norm":              0.20,   # 100 - protected area coverage
    "IND22_Riparian_Deficit":         0.15,   # 100 - G61 riparian condition
}

# Habitat naturalness scores (from LKP_HabitatTypes.csv — add column at implementation)
HABITAT_NATURALNESS = {
    "HAB01": 100, "HAB02": 100, "HAB03": 70, "HAB04": 90, "HAB05": 100,
    "HAB06": 40,  "HAB07": 20,  "HAB08": 30, "HAB09": 0,  "HAB10": 0,
    "HAB99": 50,
}


# ---------------------------------------------------------------------------
# Load biodiversity community stats (from GIS zonal statistics)
# ---------------------------------------------------------------------------

def load_habitat_stats(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load pre-computed habitat integrity stats per community from G60 raster.
    Expected columns: Community_ID; Habitat_Integrity_Mean; Protected_Area_Pct;
                      Riparian_Condition_Mean; Forest_Cover_Pct
    """
    p = path or ANALYSIS_INPUTS / "Habitat_Community_Stats.csv"
    if not p.exists():
        log.warning(
            f"Habitat stats not found at {p}. "
            "Build G59/G60/G61 and run zonal statistics to populate. "
            "IND20-IND22 will be NULL until available."
        )
        return pd.DataFrame()
    df = pd.read_csv(p)
    log.info(f"Habitat stats loaded: {len(df)} communities from {p}")
    return df


def load_db09_community_summary(
    db09_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Aggregate DB09 biodiversity observations to community level.
    Produces: species richness proxy, mean habitat integrity, disturbance severity.
    """
    p = db09_path or DATA_CLEAN / "DB09_BiodiversityObservations_CLEAN.csv"
    if not p.exists():
        log.warning("DB09 CLEAN not found — field biodiversity data unavailable")
        return pd.DataFrame()

    db09 = pd.read_csv(p)

    species_cols = [c for c in ["Mammal_Species_Count","Bird_Species_Count",
                                  "Reptile_Amphibian_Count","Plant_Species_Count"]
                    if c in db09.columns]

    agg_dict = {
        "BioObs_ID":            ("BioObs_ID",         "count"),
        "Disturbance_Severity": ("Disturbance_Severity","mean"),
    }
    if "Tree_Cover_Pct" in db09.columns:
        agg_dict["Mean_Tree_Cover_Pct"] = ("Tree_Cover_Pct", "mean")
    if species_cols:
        db09["Total_Species_Count"] = db09[species_cols].sum(axis=1)
        agg_dict["Mean_Species_Count"] = ("Total_Species_Count", "mean")

    summary = (
        db09.groupby("Community_ID")
        .agg(**{k: pd.NamedAgg(*v) for k, v in agg_dict.items()})
        .reset_index()
    )
    log.info(f"DB09 aggregated: {len(summary)} communities with field observations")
    return summary


# ---------------------------------------------------------------------------
# Compute BL_Score
# ---------------------------------------------------------------------------

def compute_bl_score(
    community_df: pd.DataFrame,
    habitat_df: pd.DataFrame,
    db09_agg: pd.DataFrame,
    df_scores_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Merge biodiversity indicators and compute community-level BL_Score."""
    result = community_df[["Community_ID","State_Code","LGA_Code"]].copy()

    # Merge GIS-derived habitat stats
    if not habitat_df.empty:
        result = result.merge(habitat_df, on="Community_ID", how="left")

    # Merge field observations
    if not db09_agg.empty:
        result = result.merge(db09_agg, on="Community_ID", how="left")

    # Load deforestation scores for IND17 reuse
    df_path = df_scores_path or ANALYSIS_OUTPUTS / "G54_DeforestationPressureIndex.csv"
    if df_path.exists():
        df_scores = pd.read_csv(df_path)[
            ["Community_ID","IND17_DeforestRate_Norm"]
        ]
        result = result.merge(df_scores, on="Community_ID", how="left")
    else:
        result["IND17_DeforestRate_Norm"] = np.nan

    def _safe_norm(s: pd.Series) -> pd.Series:
        s = pd.to_numeric(s, errors="coerce")
        mn, mx = s.min(), s.max()
        if pd.isna(mn) or mx == mn:
            return pd.Series(np.where(s.notna(), 50.0, np.nan), index=s.index)
        return ((s - mn) / (mx - mn) * 100).clip(0, 100)

    # IND20: Habitat integrity deficit (100 - mean G60 score)
    if "Habitat_Integrity_Mean" in result.columns:
        hi = pd.to_numeric(result["Habitat_Integrity_Mean"], errors="coerce")
        result["IND20_HabitatIntegrity_Deficit"] = (100 - hi).clip(0, 100)
    else:
        result["IND20_HabitatIntegrity_Deficit"] = np.nan

    # IND21: Protected area gap (100 - % PA coverage)
    if "Protected_Area_Pct" in result.columns:
        pa = pd.to_numeric(result["Protected_Area_Pct"], errors="coerce")
        result["IND21_PA_Gap_Norm"] = (100 - pa).clip(0, 100)
    else:
        result["IND21_PA_Gap_Norm"] = np.nan

    # IND22: Ecosystem services loss proxy — riparian condition deficit
    if "Riparian_Condition_Mean" in result.columns:
        rip = pd.to_numeric(result["Riparian_Condition_Mean"], errors="coerce")
        result["IND22_Riparian_Deficit"] = (100 - rip).clip(0, 100)
    else:
        result["IND22_Riparian_Deficit"] = np.nan

    # BL_Score weighted sum
    bl_score   = pd.Series(0.0, index=result.index)
    weight_sum = pd.Series(0.0, index=result.index)

    for col, w in BL_WEIGHTS.items():
        if col in result.columns:
            vals  = pd.to_numeric(result[col], errors="coerce")
            avail = vals.notna()
            bl_score   += vals.fillna(0) * w * avail
            weight_sum += w * avail

    result["BL_Score"] = np.where(
        weight_sum > 0,
        (bl_score / weight_sum).clip(0, 100),
        np.nan,
    )

    # Validate against DB09 field observations (where available)
    if "Mean_Species_Count" in result.columns:
        species = pd.to_numeric(result["Mean_Species_Count"], errors="coerce")
        # Communities with higher species counts should have lower BL_Score
        corr = result["BL_Score"].corr(species)
        if pd.notna(corr):
            expected_sign = corr < 0  # expect negative correlation
            if not expected_sign:
                log.warning(
                    f"BL_Score vs species richness correlation = {corr:.3f} "
                    "(expected negative — high species = low BL_Score). "
                    "Review indicator direction or data quality."
                )
            else:
                log.info(f"BL_Score validation: correlation with species count = {corr:.3f} ✓")

    missing_components = sum(
        result.get(c, pd.Series(dtype=float)).isna().all()
        for c in BL_WEIGHTS.keys()
    )
    completeness = (
        "Full" if missing_components == 0 else
        "Minimal" if missing_components >= 3 else "Partial"
    )
    result["BL_Data_Completeness"] = completeness
    result["Computation_Date"]     = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G63_BiodiversityLossIndex.csv"
    result.to_csv(out, index=False)
    log.info(
        f"G63 Biodiversity Loss Index saved: {out} | "
        f"Mean BL_Score: {result['BL_Score'].mean():.1f} | "
        f"Completeness: {completeness}"
    )
    update_processing_status("G63", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G63", "GIS Layer", "DERIVE",
        f"G63 Biodiversity Loss Index computed: {len(result)} communities; "
        f"completeness: {completeness}"
    )
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "25_BIODIVERSITY — Habitat Integrity + PA Coverage + BL Index (G63)")
    assert_upstream_clean(["DB01"])

    comm_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community   = pd.read_csv(comm_path)
    habitat_df  = load_habitat_stats()
    db09_agg    = load_db09_community_summary()

    result = compute_bl_score(community, habitat_df, db09_agg)
    log.info("25_biodiversity complete")
    return result


if __name__ == "__main__":
    run_all()
