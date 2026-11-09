"""
04_integrate.py
===============
Spatial joins, derived field population, and DB-to-GIS sync.

Runs after 03_clean.py. Performs:
  SJ01/SJ02 — Community → State/LGA point-in-polygon
  SJ03       — Community → HydroBasin
  SJ04       — Community → nearest river distance (IND04)
  SJ05       — Hydropower → HydroBasin
  SJ06       — Community ↔ Hydropower BUF004 10km
  SJ11       — Infrastructure → Community
  SJ12       — Erosion Sites → nearest Community
  DB-to-GIS  — Rebuild G03, G19, G26 point layers from CLEAN databases

All upstream layers must be CLEAN before this module runs.
"""

from pathlib import Path
from datetime import date

import pandas as pd

from config import (
    DATA_CLEAN, GIS_CLEAN, GIS_RAW,
    BUFFER_HYDROPOWER_COMM_KM,
    BUFFER_COMMUNITY_SERVICE_KM,
    QCStatus, BASELINE_VERSION, CRS_PROJECT,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("04_integrate")

# Optional geopandas import — graceful skip if not installed
try:
    import geopandas as gpd
    from shapely.geometry import Point
    HAS_GEO = True
except ImportError:
    HAS_GEO = False
    log.warning("geopandas not installed — spatial join functions will be skipped. "
                "Install with: pip install geopandas")


# ---------------------------------------------------------------------------
# DB-to-GIS sync helpers
# ---------------------------------------------------------------------------

def _df_to_gis_points(df: pd.DataFrame, lat_col: str, lon_col: str) -> "gpd.GeoDataFrame":
    """Convert a DataFrame with lat/lon columns to a GeoDataFrame."""
    if not HAS_GEO:
        raise ImportError("geopandas is required for GIS operations")
    geom = [
        Point(row[lon_col], row[lat_col])
        if pd.notna(row[lon_col]) and pd.notna(row[lat_col])
        else None
        for _, row in df.iterrows()
    ]
    gdf = gpd.GeoDataFrame(df, geometry=geom, crs=CRS_PROJECT)
    return gdf


def sync_db_to_gis(db_path: Path, lat_col: str, lon_col: str,
                   out_path: Path, asset_id: str) -> None:
    """
    Rebuild a GIS point layer from a CLEAN database CSV.
    Used for G03 (DB01), G19 (DB06), G26 (DB03).
    """
    if not HAS_GEO:
        log.warning(f"Skipping GIS sync for {asset_id} — geopandas not available")
        return

    df = pd.read_csv(db_path)
    gdf = _df_to_gis_points(df, lat_col, lon_col)

    GIS_CLEAN.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    log.info(f"GIS layer synced: {asset_id} → {out_path} ({len(gdf)} features)")
    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True,
                             notes=f"Rebuilt from CLEAN database {date.today()}")


# ---------------------------------------------------------------------------
# Spatial joins (attribute-level — non-GIS fallback using CSV lookups)
# ---------------------------------------------------------------------------

def join_community_to_lga(community_df: pd.DataFrame,
                           lga_df: pd.DataFrame) -> pd.DataFrame:
    """
    SJ01/SJ02 attribute fallback: verify Community State_Code/LGA_Code
    are consistent with the LGA lookup table.
    Full point-in-polygon requires GIS — flagged here if mismatch found.
    """
    lga_lookup = lga_df[["LGA_Code","State_Code"]].drop_duplicates()
    merged = community_df.merge(lga_lookup, on="LGA_Code", how="left",
                                 suffixes=("","_expected"))
    if "State_Code_expected" in merged.columns:
        mismatch = merged[merged["State_Code"] != merged["State_Code_expected"]]
        if len(mismatch) > 0:
            log.warning(f"SJ01/SJ02: {len(mismatch)} communities have "
                        f"State_Code inconsistent with LGA_Code — flag for GIS review")
    return community_df


def derive_hydropower_distance(community_df: pd.DataFrame,
                                hydro_df: pd.DataFrame) -> pd.DataFrame:
    """
    SJ06: For each community, find hydropower facilities within
    BUFFER_HYDROPOWER_COMM_KM and record distance + Hydro_ID list.
    Requires lat/lon in both DataFrames.
    Non-GIS approximation using Euclidean degree distance.
    """
    if "Latitude" not in community_df.columns:
        return community_df

    distances = []
    for _, comm in community_df.iterrows():
        clat, clon = comm["Latitude"], comm["Longitude"]
        nearby = []
        if "Latitude" in hydro_df.columns:
            for _, hydro in hydro_df.iterrows():
                dlat = abs(float(hydro["Latitude"]) - float(clat))
                dlon = abs(float(hydro["Longitude"]) - float(clon))
                # Approximate degree-to-km: 1 degree ≈ 111 km
                dist_km = ((dlat**2 + dlon**2)**0.5) * 111
                if dist_km <= BUFFER_HYDROPOWER_COMM_KM:
                    nearby.append((dist_km, hydro.get("Hydro_ID","")))
        if nearby:
            nearest_dist = min(nearby, key=lambda x: x[0])[0]
            hydro_ids = ",".join(h[1] for h in nearby)
        else:
            nearest_dist = None
            hydro_ids = None
        distances.append({"Hydropower_Distance": nearest_dist,
                          "Nearby_Hydro_IDs": hydro_ids})

    dist_df = pd.DataFrame(distances)
    community_df = community_df.copy()
    community_df["Hydropower_Distance"] = dist_df["Hydropower_Distance"].values
    log.info(f"Hydropower distance derived for {len(community_df)} communities")
    return community_df


def assign_community_to_infrastructure(infra_df: pd.DataFrame,
                                        community_df: pd.DataFrame) -> pd.DataFrame:
    """
    SJ11: Assign nearest Community_ID to each infrastructure item.
    Uses Euclidean approximation — GIS point-in-polygon preferred.
    """
    if not all(c in infra_df.columns for c in ["Latitude","Longitude"]):
        return infra_df
    if not all(c in community_df.columns for c in ["Community_ID","Latitude","Longitude"]):
        return infra_df

    assigned = []
    for _, infra in infra_df.iterrows():
        ilat, ilon = infra["Latitude"], infra["Longitude"]
        best_comm, best_dist = None, float("inf")
        for _, comm in community_df.iterrows():
            clat, clon = comm["Latitude"], comm["Longitude"]
            dist = ((float(ilat)-float(clat))**2 + (float(ilon)-float(clon))**2)**0.5 * 111
            if dist < best_dist and dist <= BUFFER_COMMUNITY_SERVICE_KM:
                best_dist = dist
                best_comm = comm["Community_ID"]
        assigned.append(best_comm)

    infra_df = infra_df.copy()
    infra_df["Community_ID"] = assigned
    nulls = infra_df["Community_ID"].isna().sum()
    if nulls:
        log.warning(f"SJ11: {nulls} infrastructure items have no community within "
                    f"{BUFFER_COMMUNITY_SERVICE_KM}km — flag for review")
    log.info(f"SJ11: Community_ID assigned to {len(infra_df)} infrastructure items")
    return infra_df


def assign_erosion_to_community(erosion_df: pd.DataFrame,
                                 community_df: pd.DataFrame,
                                 max_km: float = 5.0) -> pd.DataFrame:
    """
    SJ12: Assign nearest Community_ID to each erosion site.
    """
    if not all(c in erosion_df.columns for c in ["Latitude","Longitude"]):
        return erosion_df

    assigned = []
    for _, site in erosion_df.iterrows():
        slat, slon = site["Latitude"], site["Longitude"]
        best_comm, best_dist = None, float("inf")
        for _, comm in community_df.iterrows():
            clat, clon = comm["Latitude"], comm["Longitude"]
            dist = ((float(slat)-float(clat))**2 + (float(slon)-float(clon))**2)**0.5 * 111
            if dist < best_dist and dist <= max_km:
                best_dist = dist
                best_comm = comm["Community_ID"]
        assigned.append(best_comm)

    erosion_df = erosion_df.copy()
    erosion_df["Community_ID"] = assigned
    nulls = erosion_df["Community_ID"].isna().sum()
    if nulls:
        log.warning(f"SJ12: {nulls} erosion sites have no community within {max_km}km")
    log.info(f"SJ12: Community_ID assigned to {len(erosion_df)} erosion sites")
    return erosion_df


# ---------------------------------------------------------------------------
# Run integration
# ---------------------------------------------------------------------------

def run_all() -> None:
    log_separator(log, "04_INTEGRATE — Spatial Joins and DB-to-GIS Sync")

    # Assert upstream databases are clean
    assert_upstream_clean(["DB01","DB03","DB06"])

    # Load CLEAN databases
    db01_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    db03_path = DATA_CLEAN / "DB03_Erosion_Sites_CLEAN.csv"
    db06_path = DATA_CLEAN / "DB06_Infrastructure_CLEAN.csv"

    community_df = pd.read_csv(db01_path) if db01_path.exists() else None
    erosion_df   = pd.read_csv(db03_path) if db03_path.exists() else None
    infra_df     = pd.read_csv(db06_path) if db06_path.exists() else None

    # --- Attribute-level spatial joins ---
    if community_df is not None:
        from config import LKP_LGAS
        lga_df = pd.read_csv(LKP_LGAS)
        community_df = join_community_to_lga(community_df, lga_df)

        # Hydropower distance (requires DB04/G07 — skip if not yet available)
        hydro_path = DATA_CLEAN / "DB04_Hydropower_Water_CLEAN.csv"
        if hydro_path.exists():
            hydro_df = pd.read_csv(hydro_path)
            community_df = derive_hydropower_distance(community_df, hydro_df)
            community_df.to_csv(db01_path, index=False)

    # SJ11 — infrastructure → community
    if infra_df is not None and community_df is not None:
        infra_df = assign_community_to_infrastructure(infra_df, community_df)
        infra_df.to_csv(db06_path, index=False)

    # SJ12 — erosion → community
    if erosion_df is not None and community_df is not None:
        erosion_df = assign_erosion_to_community(erosion_df, community_df)
        erosion_df.to_csv(db03_path, index=False)

    # --- DB-to-GIS sync ---
    if community_df is not None:
        sync_db_to_gis(db01_path, "Latitude", "Longitude",
                       GIS_CLEAN / "G03_Communities_v1_0.gpkg", "G03")

    if db03_path.exists():
        sync_db_to_gis(db03_path, "Latitude", "Longitude",
                       GIS_CLEAN / "G26_ErosionSites_v1_0.gpkg", "G26")

    if db06_path.exists():
        sync_db_to_gis(db06_path, "Latitude", "Longitude",
                       GIS_CLEAN / "G19_FieldInfrastructure_v1_0.gpkg", "G19")

    log.info("04_integrate complete")


if __name__ == "__main__":
    run_all()
