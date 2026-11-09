"""
24_waste_pollution.py
=====================
Waste pollution domain processing.

Computes:
  - IND18: Proximity to nearest active waste dump site per community
  - IND19: Leachate risk score per community
  - G55: Waste dump sites GIS layer (derived from DB08)
  - G58: Waste Pollution Exposure Index per community (WP_Score 0–100)

Depends on: DB08 (CLEAN), DB01 (CLEAN), G05 (CLEAN for water contamination check)
"""

from datetime import date
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

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

log = get_logger("24_waste_pollution")

# Exposure zone distances (must be added to BUFFER_RULES.csv)
WASTE_PRIMARY_BUFFER_M    = 500    # BUF008 — direct exposure zone
WASTE_SECONDARY_BUFFER_M  = 1500   # BUF009 — secondary leachate zone
WATER_SOURCE_RISK_M       = 300    # Same as BUF007 river buffer

# Leachate risk weights by waste type (from LKP_WasteSiteTypes.csv)
LEACHATE_RISK_WEIGHTS = {
    "WST01": 0.70,   # Open municipal dump
    "WST02": 0.15,   # Controlled landfill
    "WST03": 1.00,   # Medical waste — maximum risk
    "WST04": 0.95,   # Industrial/chemical
    "WST05": 0.85,   # E-waste
    "WST06": 0.40,   # Agricultural
    "WST07": 0.10,   # Construction debris
    "WST08": 0.30,   # Open burning
    "WST09": 0.90,   # River disposal
    "WST10": 0.50,   # Roadside dump
    "WST99": 0.60,   # Unknown
}

# Burning risk multiplier
BURNING_RISK_MULTIPLIER = 1.30


# ---------------------------------------------------------------------------
# Sync DB08 to G55 GIS layer
# ---------------------------------------------------------------------------

def sync_db08_to_g55(db08_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    Generate G55 waste site GIS table from DB08 CLEAN.
    Full GIS layer (GeoPackage) requires geopandas.
    """
    p = db08_path or DATA_CLEAN / "DB08_WastePollutionSites_CLEAN.csv"
    if not p.exists():
        log.warning(f"DB08 CLEAN not found at {p}")
        return None

    df = pd.read_csv(p)
    log.info(f"DB08 loaded: {len(df)} waste sites")

    GIS_CLEAN.mkdir(parents=True, exist_ok=True)
    out = GIS_CLEAN / "G55_WasteDumpSites_v1_0.csv"
    df.to_csv(out, index=False)
    log.info(f"G55 saved: {out}")
    update_processing_status("G55", QCStatus.CLEAN,
                              notes=f"G55 synced from DB08: {len(df)} sites")
    return df


# ---------------------------------------------------------------------------
# Compute IND18 and IND19 per community
# ---------------------------------------------------------------------------

def compute_waste_exposure(
    community_df: pd.DataFrame,
    waste_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    For each community compute:
      IND18: distance to nearest active waste dump (m) — inverted 0-100
      IND19: leachate risk score — weighted by waste type and proximity
      WP_Score: weighted combination 0-100
    """
    result = community_df[["Community_ID","State_Code","LGA_Code",
                             "Latitude","Longitude"]].copy()

    # Filter to active sites only
    active = waste_df[waste_df["Activity_Status"] == "Active"].copy() \
        if "Activity_Status" in waste_df.columns else waste_df.copy()

    records = []
    for _, comm in community_df.iterrows():
        clat, clon = float(comm["Latitude"]), float(comm["Longitude"])

        site_distances     = []
        leachate_scores    = []
        burning_sites      = 0
        sites_in_500m      = 0
        medical_sites_500m = 0

        for _, site in active.iterrows():
            if pd.isna(site.get("Latitude")) or pd.isna(site.get("Longitude")):
                continue
            slat = float(site["Latitude"])
            slon = float(site["Longitude"])
            dist_km = ((clat-slat)**2 + (clon-slon)**2)**0.5 * 111
            dist_m  = dist_km * 1000

            site_distances.append(dist_m)
            wtype = str(site.get("Waste_Type_Code","WST99"))
            base_risk = LEACHATE_RISK_WEIGHTS.get(wtype, 0.60)

            # Distance decay (inverse square)
            decay = 1.0 / max(1.0, (dist_m / 100) ** 2)
            leachate_scores.append(base_risk * decay * 100)

            if dist_m <= WASTE_PRIMARY_BUFFER_M:
                sites_in_500m += 1
                if wtype == "WST03":
                    medical_sites_500m += 1

            if str(site.get("Open_Burning","No")) == "Yes" and dist_m <= WASTE_SECONDARY_BUFFER_M:
                burning_sites += 1

        # IND18: proximity (inverted — closer = higher score)
        if site_distances:
            nearest_m = min(site_distances)
            # Normalise: 0m → 100; >= 2000m → 0
            ind18 = max(0, (1 - nearest_m / 2000) * 100)
        else:
            nearest_m = np.nan
            ind18     = 0.0  # No waste sites nearby = no exposure

        # IND19: leachate risk (sum of decay-weighted site risks capped at 100)
        ind19 = min(100.0, sum(leachate_scores)) if leachate_scores else 0.0

        # Burning exposure indicator
        burning_exposure = min(100.0, burning_sites * 25.0)

        records.append({
            "Community_ID":            comm["Community_ID"],
            "Nearest_Waste_Site_m":    round(nearest_m, 0) if pd.notna(nearest_m) else np.nan,
            "Active_Sites_500m":       sites_in_500m,
            "Medical_Sites_500m":      medical_sites_500m,
            "IND18_Proximity_Norm":    round(ind18, 2),
            "IND19_Leachate_Risk_Norm":round(ind19, 2),
            "Burning_Exposure_Norm":   round(burning_exposure, 2),
        })

    exp_df = pd.DataFrame(records)
    result = result.merge(exp_df, on="Community_ID", how="left")

    # WP_Score: weighted combination
    # Proximity 40% + Leachate 35% + Burning 25%
    wp = (
        0.40 * result["IND18_Proximity_Norm"].fillna(0) +
        0.35 * result["IND19_Leachate_Risk_Norm"].fillna(0) +
        0.25 * result["Burning_Exposure_Norm"].fillna(0)
    )
    result["WP_Score"] = wp.clip(0, 100)

    # Critical flag: medical waste site within 500m
    result["MEDICAL_WASTE_ALERT"] = (result["Medical_Sites_500m"] > 0)

    # Data completeness: Full if DB08 has records; None if no DB08
    has_data = len(waste_df) > 0
    result["WP_Data_Completeness"] = "Full" if has_data else "None"
    result["Computation_Date"]     = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G58_WastePollutionExposure.csv"
    result.to_csv(out, index=False)

    medical_alerts = int(result["MEDICAL_WASTE_ALERT"].sum())
    log.info(
        f"G58 Waste Pollution Exposure saved: {out} | "
        f"Mean WP_Score: {result['WP_Score'].mean():.1f} | "
        f"Medical waste alerts: {medical_alerts}"
    )
    if medical_alerts > 0:
        log.warning(
            f"CRITICAL: {medical_alerts} communities have medical/clinical waste "
            f"sites within {WASTE_PRIMARY_BUFFER_M}m — HIGH_WASTE_HAZARD flag generated"
        )

    update_processing_status("G58", QCStatus.DERIVED)
    append_version_log(
        BASELINE_VERSION, "G58", "GIS Layer", "DERIVE",
        f"G58 Waste Pollution Exposure computed: {len(result)} communities; "
        f"medical alerts: {medical_alerts}"
    )
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "24_WASTE_POLLUTION — Waste Sites + Leachate + Exposure (G55, G58)")
    assert_upstream_clean(["DB01"])

    comm_path  = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    waste_path = DATA_CLEAN / "DB08_WastePollutionSites_CLEAN.csv"

    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community  = pd.read_csv(comm_path)
    waste_df   = sync_db08_to_g55(waste_path) if waste_path.exists() else pd.DataFrame()

    if waste_df is None or waste_df.empty:
        log.warning(
            "No waste site data available. "
            "WP_Score will be 0 for all communities (no exposure without data). "
            "Collect DB08 field data and re-run."
        )
        waste_df = pd.DataFrame()

    result = compute_waste_exposure(community, waste_df)
    log.info("24_waste_pollution complete")
    return result


if __name__ == "__main__":
    run_all()
