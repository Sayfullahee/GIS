"""
09_exposure.py
==============
Compute Exposure Index (G32) from flood exposure (G29) and
erosion exposure (G30) outputs. Implements IND05 and IND06.

Depends on: DB01 (CLEAN), DB06 (CLEAN), G24 outputs, G26 (CLEAN)
Outputs:
  - G29 community flood exposure table
  - G30 community erosion exposure table
  - G32 Exposure Index (E_Score 0-100 per community)

Key rule: Exposure must NOT incorporate vulnerability variables.
Reference bounds frozen at first computation (EMD01).
"""

from datetime import date
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS,
    BUFFER_EROSION_THREAT_M,
    BUFFER_COMMUNITY_SERVICE_KM,
    RISK_MODEL_VERSION,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("09_exposure")

# Infrastructure weights (EMD02 — must match EXPOSURE_MODEL_DECISIONS.csv)
INFRA_WEIGHTS = {
    "Critical_Infra_Exposed_Count":      3,
    "Critical_Roads_km_Exposed":         2,
    "Buildings_Exposed_Count":           1,
    "POI_Critical_in_Moderate_Plus":     3,
}


# ---------------------------------------------------------------------------
# Normalisation helpers — reference bounds FROZEN at first run
# ---------------------------------------------------------------------------

def minmax_norm(series: pd.Series,
                ref_min: float = 0.0,
                ref_max: Optional[float] = None) -> pd.Series:
    """
    Min-max normalise to 0-100 using fixed reference bounds.
    If ref_max is None, use series maximum (first-run baseline).
    """
    if ref_max is None:
        ref_max = series.max()
    if ref_max == ref_min:
        return pd.Series(np.where(series.notna(), 0.0, np.nan), index=series.index)
    return ((series - ref_min) / (ref_max - ref_min) * 100).clip(0, 100)


# ---------------------------------------------------------------------------
# G29 — Flood Exposure
# ---------------------------------------------------------------------------

def compute_g29_flood_exposure(
    community_df: pd.DataFrame,
    infra_df: Optional[pd.DataFrame] = None,
    hazard_summary_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Build G29 community flood exposure table.
    Hazard summary (mean/max hazard score per community) comes from
    raster zonal stats (G24) — loaded from CSV if available, otherwise
    uses available community-level data.
    """
    result = community_df[["Community_ID","State_Code","LGA_Code","Population"]].copy()

    # Load pre-computed hazard zone stats if available
    if hazard_summary_path and hazard_summary_path.exists():
        haz = pd.read_csv(hazard_summary_path)
        result = result.merge(haz, on="Community_ID", how="left")
        log.info("Hazard zone statistics loaded from G24 zonal stats file")
    else:
        log.warning("G24 zonal stats not found — flood exposure based on community data only")
        for col in ["Mean_Hazard_Score","Max_Hazard_Score",
                    "Pop_in_Moderate_Plus_Hazard","Buildings_in_Moderate_Plus_Hazard",
                    "Roads_km_Moderate_Plus_Hazard","Critical_Infra_in_Moderate_Plus_Hazard",
                    "POI_Critical_in_Moderate_Plus_Hazard","Pct_Area_High_Plus_Hazard"]:
            result[col] = np.nan

    # IND05 — Population Exposure
    if "Pop_in_Moderate_Plus_Hazard" in result.columns:
        result["IND05_Pop_Exposure"] = minmax_norm(
            pd.to_numeric(result["Pop_in_Moderate_Plus_Hazard"], errors="coerce")
        )
    else:
        result["IND05_Pop_Exposure"] = np.nan

    # IND06a — Infrastructure exposure (flood)
    # Weighted score from exposed infrastructure components
    weighted = pd.Series(0.0, index=result.index)
    total_weight = 0
    for col, w in INFRA_WEIGHTS.items():
        if col in result.columns:
            norm = minmax_norm(pd.to_numeric(result[col], errors="coerce"))
            weighted += norm.fillna(0) * w
            total_weight += w

    if total_weight > 0:
        result["IND06_Flood_Infra_Exposure"] = (weighted / total_weight).clip(0, 100)
    else:
        result["IND06_Flood_Infra_Exposure"] = np.nan

    # Completeness flag
    required_cols = ["IND05_Pop_Exposure","IND06_Flood_Infra_Exposure",
                     "Mean_Hazard_Score"]
    available = result[required_cols].notna().sum(axis=1)
    result["Exposure_Data_Completeness"] = pd.cut(
        available,
        bins=[-1, 0, 1, 3],
        labels=["Minimal", "Partial", "Full"]
    )

    result["Computation_Date"]     = date.today().isoformat()
    result["Input_Layers_Version"] = BASELINE_VERSION
    result["Risk_Model_Version"]   = RISK_MODEL_VERSION

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G29_FloodExposure_community.csv"
    result.to_csv(out, index=False)
    log.info(f"G29 flood exposure saved: {out} ({len(result)} communities)")
    update_processing_status("G29", QCStatus.DERIVED)
    return result


# ---------------------------------------------------------------------------
# G30 — Erosion Exposure
# ---------------------------------------------------------------------------

def compute_g30_erosion_exposure(
    community_df: pd.DataFrame,
    erosion_df: Optional[pd.DataFrame] = None,
    infra_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Build G30 community erosion exposure table.
    Uses BUF003 (100m) around active erosion sites to identify exposed assets.
    """
    result = community_df[["Community_ID","State_Code","LGA_Code"]].copy()
    threat_km = BUFFER_EROSION_THREAT_M / 1000.0

    # Initialise other exposure columns
    for col in ["Infra_Exposed_Count","Critical_Infra_Exposed_Count",
                "Roads_km_Exposed","Buildings_Exposed_Count"]:
        result[col] = 0

    if erosion_df is not None and not erosion_df.empty:
        active = erosion_df[erosion_df["Activity_Status"] == "Active"].copy()

        # Sites per community (within 5km)
        site_counts = (
            active.groupby("Community_ID")
            .agg(
                Active_Erosion_Sites_Count = ("Erosion_ID",   "count"),
                Active_Erosion_Max_Severity= ("Severity_0_4", "max"),
            )
            .reset_index()
        )
        result = result.merge(site_counts, on="Community_ID", how="left")
        result["Active_Erosion_Sites_Count"]  = result["Active_Erosion_Sites_Count"].fillna(0)
        result["Active_Erosion_Max_Severity"] = result["Active_Erosion_Max_Severity"].fillna(0)
    else:
        result["Active_Erosion_Sites_Count"] = 0
        result["Active_Erosion_Max_Severity"] = 0

        # Infrastructure within BUF003 (100m) of active erosion sites
        if infra_df is not None and not infra_df.empty:
            for _, site in active.iterrows():
                slat, slon = float(site["Latitude"]), float(site["Longitude"])
                for _, infra in infra_df.iterrows():
                    ilat = float(infra["Latitude"])
                    ilon = float(infra["Longitude"])
                    dist_km = ((slat-ilat)**2 + (slon-ilon)**2)**0.5 * 111
                    if dist_km <= threat_km:
                        comm = infra.get("Community_ID")
                        if comm and comm in result["Community_ID"].values:
                            idx = result.index[result["Community_ID"] == comm]
                            result.loc[idx, "Infra_Exposed_Count"] += 1
                            if str(infra.get("Critical_Service","No")) == "Yes":
                                result.loc[idx, "Critical_Infra_Exposed_Count"] += 1

    # Severity-weighted exposure score (EMD03)
    result["Severity_Weighted_Exposure"] = (
        result["Active_Erosion_Sites_Count"] *
        result["Active_Erosion_Max_Severity"].clip(1, 4)
    )

    result["IND06_Erosion_Exposure"] = minmax_norm(
        result["Severity_Weighted_Exposure"]
    )

    result["Threat_Buffer_m"]  = BUFFER_EROSION_THREAT_M
    result["Active_Sites_Used"]= "Yes"
    result["Exposure_Data_Completeness"] = np.where(
        result["Active_Erosion_Sites_Count"] == 0, "None",
        np.where(result["IND06_Erosion_Exposure"].notna(), "Full", "Partial")
    )

    result["Computation_Date"]     = date.today().isoformat()
    result["Input_Layers_Version"] = BASELINE_VERSION

    out = ANALYSIS_OUTPUTS / "G30_ErosionExposure_community.csv"
    result.to_csv(out, index=False)
    log.info(f"G30 erosion exposure saved: {out}")
    update_processing_status("G30", QCStatus.DERIVED)
    return result


# ---------------------------------------------------------------------------
# G32 — Exposure Index
# ---------------------------------------------------------------------------

def compute_g32_exposure_index(
    g29_df: pd.DataFrame,
    g30_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    E_Score = weighted combination of IND05, IND06a (flood), IND06b (erosion).
    Weights per RISK_MODEL_SPEC.md Section 3:
      IND05 = 50%, IND06a = 30%, IND06b = 20%
    """
    result = g29_df[["Community_ID","State_Code","LGA_Code"]].copy()

    # Merge exposure components
    result = result.merge(
        g29_df[["Community_ID","IND05_Pop_Exposure","IND06_Flood_Infra_Exposure",
                "Exposure_Data_Completeness"]].rename(
            columns={"Exposure_Data_Completeness": "E_Flood_Completeness"}),
        on="Community_ID", how="left"
    )
    result = result.merge(
        g30_df[["Community_ID","IND06_Erosion_Exposure"]].rename(
            columns={"IND06_Erosion_Exposure": "IND06_Erosion_Infra_Exposure_Norm"}),
        on="Community_ID", how="left"
    )

    # Weighted sum — skip missing components
    w_ind05  = 0.50
    w_ind06a = 0.30
    w_ind06b = 0.20

    e_score = pd.Series(0.0, index=result.index)
    weight_sum = pd.Series(0.0, index=result.index)

    for col, w in [("IND05_Pop_Exposure", w_ind05),
                   ("IND06_Flood_Infra_Exposure", w_ind06a),
                   ("IND06_Erosion_Infra_Exposure_Norm", w_ind06b)]:
        vals = pd.to_numeric(result.get(col, pd.Series(dtype=float)), errors="coerce")
        avail = vals.notna()
        e_score   += vals.fillna(0) * w * avail
        weight_sum += w * avail

    result["E_Score"] = np.where(
        weight_sum > 0,
        (e_score / weight_sum).clip(0, 100),
        np.nan
    )

    missing = result[["IND05_Pop_Exposure",
                       "IND06_Flood_Infra_Exposure",
                       "IND06_Erosion_Infra_Exposure_Norm"]].isna().sum(axis=1)
    result["E_Missing_Components"] = missing.astype(int)
    result["E_Data_Completeness"]  = pd.cut(
        3 - missing,
        bins=[-1, 0, 2, 3],
        labels=["Minimal","Partial","Full"]
    )
    result["Risk_Model_Version"] = RISK_MODEL_VERSION
    result["Computation_Date"]   = date.today().isoformat()

    out = ANALYSIS_OUTPUTS / "G32_ExposureIndex.csv"
    result.to_csv(out, index=False)
    log.info(f"G32 Exposure Index saved: {out} | "
             f"Mean E_Score: {result['E_Score'].mean():.1f}")
    update_processing_status("G32", QCStatus.DERIVED)
    append_version_log(BASELINE_VERSION, "G32", "GIS Layer", "DERIVE",
                       f"G32 Exposure Index computed: {len(result)} communities")
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "09_EXPOSURE — Exposure Index (G29, G30, G32)")
    assert_upstream_clean(["DB01","DB03","DB06"])

    comm_path  = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    infra_path = DATA_CLEAN / "DB06_Infrastructure_CLEAN.csv"
    erode_path = DATA_CLEAN / "DB03_Erosion_Sites_CLEAN.csv"

    community_df = pd.read_csv(comm_path) if comm_path.exists() else pd.DataFrame()
    infra_df     = pd.read_csv(infra_path) if infra_path.exists() else None
    erosion_df   = pd.read_csv(erode_path) if erode_path.exists() else None

    if community_df.empty:
        log.error("DB01 CLEAN not found — exposure module cannot run")
        return None

    g29 = compute_g29_flood_exposure(community_df, infra_df)
    g30 = compute_g30_erosion_exposure(community_df, erosion_df, infra_df)
    g32 = compute_g32_exposure_index(g29, g30)

    log.info("09_exposure complete")
    return g32


if __name__ == "__main__":
    run_all()
