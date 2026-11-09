"""
07_erosion.py
=============
Erosion indicator computation, hotspot analysis, and
erosion severity aggregation to community level.

Depends on: DB03 (CLEAN), G26 (CLEAN)
Outputs:
  - IND03 — Erosion Severity per community (max and mean)
  - IND04 — River Proximity per community (from G05 distances in DB03)
  - Erosion site summary per community
  - G27 hotspot density (kernel density estimation where sample sufficient)
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS, GIS_DERIVED,
    EROSION_HOTSPOT_MIN_SITES_KDE_SIMPLE,
    EROSION_HOTSPOT_MIN_SITES_KDE_WEIGHTED,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("07_erosion")


# ---------------------------------------------------------------------------
# Load DB03
# ---------------------------------------------------------------------------

def load_db03(path: Optional[Path] = None) -> pd.DataFrame:
    p = path or DATA_CLEAN / "DB03_Erosion_Sites_CLEAN.csv"
    if not p.exists():
        log.warning(f"DB03 CLEAN not found at {p}")
        return pd.DataFrame()
    df = pd.read_csv(p)
    log.info(f"DB03 loaded: {len(df)} erosion sites")
    return df


# ---------------------------------------------------------------------------
# IND03 — Erosion Severity
# ---------------------------------------------------------------------------

def compute_ind03(erosion_df: pd.DataFrame) -> pd.DataFrame:
    """
    IND03 per community:
      - Max Severity_0_4 among all sites in community
      - Mean Severity_0_4 (active sites only)
      - Count of active high-severity sites (>= 3)
    Normalised to 0-100: score = (value / 4) * 100
    """
    if erosion_df.empty:
        return pd.DataFrame(columns=["Community_ID",
                                      "IND03_Max_Severity",
                                      "IND03_Mean_Severity_Active",
                                      "IND03_Max_Severity_Norm",
                                      "IND03_High_Severity_Count"])

    active = erosion_df[erosion_df["Activity_Status"] == "Active"]

    # Aggregation by community
    all_agg = (
        erosion_df.groupby("Community_ID")
        .agg(
            IND03_Max_Severity   = ("Severity_0_4", "max"),
            IND03_Site_Count     = ("Erosion_ID",   "count"),
        )
        .reset_index()
    )

    if not active.empty:
        active_agg = (
            active.groupby("Community_ID")
            .agg(
                IND03_Mean_Severity_Active  = ("Severity_0_4", "mean"),
                IND03_High_Severity_Count   = ("Severity_0_4",
                                               lambda x: (x >= 3).sum()),
                IND03_Active_Site_Count     = ("Erosion_ID", "count"),
            )
            .reset_index()
        )
        result = all_agg.merge(active_agg, on="Community_ID", how="left")
    else:
        result = all_agg.copy()
        result["IND03_Mean_Severity_Active"] = np.nan
        result["IND03_High_Severity_Count"]  = 0
        result["IND03_Active_Site_Count"]    = 0

    # Normalise max severity 0-4 → 0-100
    result["IND03_Max_Severity_Norm"] = (
        pd.to_numeric(result["IND03_Max_Severity"], errors="coerce") / 4 * 100
    ).clip(0, 100)

    log.info(f"IND03 computed for {len(result)} communities "
             f"(from {len(erosion_df)} erosion sites)")
    return result


# ---------------------------------------------------------------------------
# IND04 — River Proximity
# ---------------------------------------------------------------------------

def compute_ind04(erosion_df: pd.DataFrame,
                  community_df: pd.DataFrame) -> pd.DataFrame:
    """
    IND04 = distance from community centroid to nearest river.
    Populated from DB03 River_Distance_m (set by 04_integrate.py SJ04).
    If not available uses community's Hydropower_Distance as proxy.
    Direction: INVERTED — closer = higher hazard score.
    """
    result = community_df[["Community_ID"]].copy()

    # Use mean river distance of sites associated with each community
    if not erosion_df.empty and "River_Distance_m" in erosion_df.columns:
        dist_by_comm = (
            erosion_df.groupby("Community_ID")["River_Distance_m"]
            .min()    # minimum distance = closest site to river
            .reset_index(name="IND04_River_Distance_m")
        )
        result = result.merge(dist_by_comm, on="Community_ID", how="left")
    else:
        result["IND04_River_Distance_m"] = np.nan

    # Fallback: DB01 Hydropower_Distance (rough proxy)
    if "Hydropower_Distance" in community_df.columns:
        mask = result["IND04_River_Distance_m"].isna()
        result.loc[mask, "IND04_River_Distance_m"] = (
            community_df.loc[
                community_df["Community_ID"].isin(result.loc[mask, "Community_ID"]),
                ["Community_ID","Hydropower_Distance"]
            ]
            .set_index("Community_ID")["Hydropower_Distance"]
            * 1000   # km to m
        ).values

    # Inversion + normalisation (max capped at 500m per BUF001)
    max_dist = 500.0   # BUF001 — beyond this proximity score = 0
    d = pd.to_numeric(result["IND04_River_Distance_m"], errors="coerce")
    result["IND04_River_Proximity_Norm"] = (
        ((max_dist - d.clip(upper=max_dist)) / max_dist * 100).clip(0, 100)
    )
    result["IND04_River_Distance_m"] = d

    log.info("IND04 computed")
    return result


# ---------------------------------------------------------------------------
# Hotspot density (simple implementation)
# ---------------------------------------------------------------------------

def compute_hotspot_density_by_state(
    erosion_df: pd.DataFrame,
    community_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tiered hotspot method per HAZARD_MODEL_DECISIONS.csv HMD03.
    For each state: apply severity-weighted KDE if >= 20 sites,
    simple KDE if 10-19, point mapping only if < 10.

    Simplified implementation: produces a community-level
    'hotspot proximity score' (0-100) based on proximity to
    high-severity active erosion sites.
    Full raster KDE requires rasterio/scipy — noted in output.
    """
    if erosion_df.empty or community_df.empty:
        return pd.DataFrame(columns=["Community_ID","G27_Hotspot_Score","G27_Method"])

    active = erosion_df[erosion_df["Activity_Status"] == "Active"].copy()
    records = []

    for state in community_df["State_Code"].unique():
        state_sites = active[active["Community_ID"].isin(
            community_df.loc[community_df["State_Code"] == state, "Community_ID"]
        )]
        n_sites = len(state_sites)

        if n_sites < EROSION_HOTSPOT_MIN_SITES_KDE_SIMPLE:
            method = "PointMapping"
        elif n_sites < EROSION_HOTSPOT_MIN_SITES_KDE_WEIGHTED:
            method = "SimpleKDE"
        else:
            method = "SeverityWeightedKDE"

        log.info(f"State {state}: {n_sites} active sites → method: {method}")

        state_comms = community_df[community_df["State_Code"] == state]
        for _, comm in state_comms.iterrows():
            if state_sites.empty:
                score = 0.0
            else:
                # Distance-weighted severity score
                scores = []
                for _, site in state_sites.iterrows():
                    dlat = float(site["Latitude"]) - float(comm["Latitude"])
                    dlon = float(site["Longitude"]) - float(comm["Longitude"])
                    dist_km = ((dlat**2 + dlon**2)**0.5) * 111
                    sev = float(site.get("Severity_0_4", 1))
                    if method == "SeverityWeightedKDE":
                        w = sev * max(0, 1 - dist_km / 5.0)  # bandwidth = 5km
                    elif method == "SimpleKDE":
                        w = max(0, 1 - dist_km / 5.0)
                    else:
                        w = 1.0 if dist_km < 2.0 else 0.0
                    scores.append(w)
                score = min(sum(scores) / (len(state_sites) * 4) * 100, 100.0)

            records.append({
                "Community_ID":    comm["Community_ID"],
                "G27_Hotspot_Score": round(score, 2),
                "G27_Method":       method,
            })

    result = pd.DataFrame(records)
    log.info(f"G27 hotspot scores computed for {len(result)} communities")
    update_processing_status("G27", QCStatus.DERIVED)
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "07_EROSION — Erosion Indicator Computation")
    assert_upstream_clean(["DB03"])

    erosion_df = load_db03()
    comm_path  = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"

    if not comm_path.exists():
        log.warning("DB01 CLEAN not found — erosion module skipped")
        return None

    community_df = pd.read_csv(comm_path)

    ind03 = compute_ind03(erosion_df)
    ind04 = compute_ind04(erosion_df, community_df)
    hotspot = compute_hotspot_density_by_state(erosion_df, community_df)

    # Merge all erosion outputs
    result = community_df[["Community_ID","State_Code"]].copy()
    result = result.merge(ind03,   on="Community_ID", how="left")
    result = result.merge(ind04,   on="Community_ID", how="left")
    result = result.merge(hotspot, on="Community_ID", how="left")

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "Erosion_Indicators_IND03_IND04_G27.csv"
    result.to_csv(out, index=False)
    log.info(f"Erosion indicators saved: {out}")
    log.info("07_erosion complete")
    return result


if __name__ == "__main__":
    run_all()
