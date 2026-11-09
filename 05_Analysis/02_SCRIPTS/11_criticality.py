"""
11_criticality.py
=================
Compute Criticality Index (G34) from infrastructure, electricity,
and hydropower disruption indicators.

Depends on: G19 (CLEAN), G18 (CLEAN), G28 (DERIVED), DB01 (CLEAN)
Outputs:
  - C_Score 0-100 per community → G34

Key rule: IND08 = NULL (not 0) for communities outside BUF004 (10km).
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS,
    BUFFER_HYDROPOWER_COMM_KM,
    RISK_MODEL_VERSION, QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("11_criticality")


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(np.where(series.notna(), 0.0, np.nan), index=series.index)
    return ((series - mn) / (mx - mn) * 100).clip(0, 100)


# ---------------------------------------------------------------------------
# Critical service count per community
# ---------------------------------------------------------------------------

def count_critical_services(
    community_df: pd.DataFrame,
    infra_df: Optional[pd.DataFrame],
    poi_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """Count critical infrastructure and POI items per community."""
    result = community_df[["Community_ID"]].copy()

    # Critical infrastructure (G19)
    if infra_df is not None and "Critical_Service" in infra_df.columns:
        crit_infra = (
            infra_df[infra_df["Critical_Service"] == "Yes"]
            .groupby("Community_ID").size()
            .reset_index(name="Critical_Infra_Count")
        )
        result = result.merge(crit_infra, on="Community_ID", how="left")
    else:
        result["Critical_Infra_Count"] = np.nan

    # Critical POI (G18)
    if poi_df is not None and "Critical_Service" in poi_df.columns:
        crit_poi = (
            poi_df[poi_df["Critical_Service"] == "Yes"]
            .groupby("Community_ID").size()
            .reset_index(name="Critical_POI_Count")
        )
        result = result.merge(crit_poi, on="Community_ID", how="left")
    else:
        result["Critical_POI_Count"] = np.nan

    result["Critical_Services_Count"] = (
        result["Critical_Infra_Count"].fillna(0) +
        result["Critical_POI_Count"].fillna(0)
    )
    return result


# ---------------------------------------------------------------------------
# IND06 critical infra exposure component
# ---------------------------------------------------------------------------

def compute_ind06_critical_exposure(
    community_df: pd.DataFrame,
    g29_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Load critical infrastructure exposure from G29 output."""
    result = community_df[["Community_ID"]].copy()

    if g29_path and g29_path.exists():
        g29 = pd.read_csv(g29_path)
        if "Critical_Infra_in_Moderate_Plus_Hazard" in g29.columns:
            result = result.merge(
                g29[["Community_ID","Critical_Infra_in_Moderate_Plus_Hazard"]],
                on="Community_ID", how="left"
            )
            result["IND06_Critical_Infra_Exposed_Norm"] = _minmax(
                pd.to_numeric(
                    result["Critical_Infra_in_Moderate_Plus_Hazard"],
                    errors="coerce"
                )
            )
        else:
            result["IND06_Critical_Infra_Exposed_Norm"] = np.nan
    else:
        result["IND06_Critical_Infra_Exposed_Norm"] = np.nan

    return result


# ---------------------------------------------------------------------------
# G34 — Criticality Index
# ---------------------------------------------------------------------------

def compute_g34_criticality(
    community_df: pd.DataFrame,
    crit_services_df: pd.DataFrame,
    ind06c_df: pd.DataFrame,
    ind07_df: Optional[pd.DataFrame] = None,
    ind08_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    C_Score = weighted sum:
      IND06 critical infra exposed = 35%
      IND07 electricity disruption = 30%
      IND08 hydropower disruption  = 35%  ← NULL for communities outside BUF004
    """
    result = community_df[["Community_ID","State_Code","LGA_Code"]].copy()

    result = result.merge(crit_services_df, on="Community_ID", how="left")
    result = result.merge(ind06c_df[["Community_ID","IND06_Critical_Infra_Exposed_Norm"]],
                          on="Community_ID", how="left")

    # IND07
    if ind07_df is not None and "IND07_Electricity_Disruption" in ind07_df.columns:
        result = result.merge(
            ind07_df[["Community_ID","IND07_Electricity_Disruption"]],
            on="Community_ID", how="left"
        )
        result["IND07_Electricity_Disruption_Norm"] = _minmax(
            pd.to_numeric(result["IND07_Electricity_Disruption"], errors="coerce")
        )
    else:
        result["IND07_Electricity_Disruption_Norm"] = np.nan

    # IND08 — hydropower disruption
    # Key rule: communities outside BUF004 get NULL not 0
    result["Hydropower_Within_10km"] = "No"
    result["IND08_Hydropower_Disruption_Norm"] = np.nan

    if ind08_df is not None and "IND08_Hydropower_Disruption" in ind08_df.columns:
        # Each facility has coordinates; find communities within BUF004
        hydro_path = DATA_CLEAN / "DB04_Hydropower_Water_CLEAN.csv"
        if hydro_path.exists():
            hydro = pd.read_csv(hydro_path)
            facility_locs = hydro[["Hydro_ID","Latitude","Longitude"]].drop_duplicates("Hydro_ID")

            for _, comm in community_df.iterrows():
                clat = float(comm["Latitude"])
                clon = float(comm["Longitude"])
                for _, fac in facility_locs.iterrows():
                    dist_km = (
                        (clat - float(fac["Latitude"]))**2 +
                        (clon - float(fac["Longitude"]))**2
                    )**0.5 * 111
                    if dist_km <= BUFFER_HYDROPOWER_COMM_KM:
                        idx = result.index[result["Community_ID"] == comm["Community_ID"]]
                        result.loc[idx, "Hydropower_Within_10km"] = "Yes"
                        # Get IND08 for nearest facility
                        fac_ind08 = ind08_df.loc[
                            ind08_df["Hydro_ID"] == fac["Hydro_ID"],
                            "IND08_Hydropower_Disruption"
                        ]
                        if not fac_ind08.empty:
                            result.loc[idx, "IND08_Hydropower_Disruption_Norm"] = float(
                                fac_ind08.values[0]
                            )
                        break

    # Weighted C_Score
    components = [
        ("IND06_Critical_Infra_Exposed_Norm",   0.35),
        ("IND07_Electricity_Disruption_Norm",    0.30),
        ("IND08_Hydropower_Disruption_Norm",     0.35),
    ]

    c_score    = pd.Series(0.0, index=result.index)
    weight_sum = pd.Series(0.0, index=result.index)

    for col, w in components:
        if col in result.columns:
            vals  = pd.to_numeric(result[col], errors="coerce")
            avail = vals.notna()
            c_score    += vals.fillna(0) * w * avail
            weight_sum += w * avail

    result["C_Score"] = np.where(
        weight_sum > 0,
        (c_score / weight_sum).clip(0, 100),
        np.nan,
    )

    result["C_Missing_Components"] = sum(
        result.get(col, pd.Series(dtype=float)).isna().astype(int)
        for col, _ in components
    )
    n_avail = len(components) - result["C_Missing_Components"]
    result["C_Data_Completeness"] = pd.cut(
        n_avail, bins=[-1, 0, 1, 3], labels=["Minimal","Partial","Full"]
    )
    result["Risk_Model_Version"] = RISK_MODEL_VERSION
    result["Computation_Date"]   = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G34_CriticalityIndex.csv"
    result.to_csv(out, index=False)
    log.info(f"G34 Criticality Index saved: {out} | "
             f"Mean C_Score: {result['C_Score'].mean():.1f}")
    update_processing_status("G34", QCStatus.DERIVED)
    append_version_log(BASELINE_VERSION, "G34", "GIS Layer", "DERIVE",
                       f"G34 Criticality Index computed: {len(result)} communities")
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "11_CRITICALITY — Criticality Index (G34)")
    assert_upstream_clean(["DB01","DB06"])

    comm_path  = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    infra_path = DATA_CLEAN / "DB06_Infrastructure_CLEAN.csv"

    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community_df = pd.read_csv(comm_path)
    infra_df     = pd.read_csv(infra_path) if infra_path.exists() else None

    # POI CSV (if exported from G18)
    poi_path = ANALYSIS_OUTPUTS / "G18_POI_CLEAN.csv"
    poi_df   = pd.read_csv(poi_path) if poi_path.exists() else None

    crit_services = count_critical_services(community_df, infra_df, poi_df)

    g29_path = ANALYSIS_OUTPUTS / "G29_FloodExposure_community.csv"
    ind06c   = compute_ind06_critical_exposure(community_df, g29_path)

    ind07_path = ANALYSIS_OUTPUTS / "Hydro_Indicators_IND07_IND08.csv"
    ind07_df   = pd.read_csv(ind07_path) if ind07_path.exists() else None

    ind08_path = ANALYSIS_OUTPUTS / "IND08_Hydropower_Disruption.csv"
    ind08_df   = pd.read_csv(ind08_path) if ind08_path.exists() else None

    g34 = compute_g34_criticality(
        community_df, crit_services, ind06c, ind07_df, ind08_df
    )
    log.info("11_criticality complete")
    return g34


if __name__ == "__main__":
    run_all()
