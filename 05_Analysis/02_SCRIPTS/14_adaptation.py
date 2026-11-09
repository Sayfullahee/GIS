"""
14_adaptation.py
================
Compile adaptation inventory (G36) and compute IND10 Adaptation Gap.

Depends on: DB01 (CLEAN), DB02 (CLEAN — aggregated), DB06 (CLEAN)
Outputs:
  - G36 community adaptation inventory (one row per community)
  - IND09_Adaptation_Coverage (raw 0-1)
  - IND10_Adaptation_Gap (0-100) — only if formula approved in INDICATOR_REGISTER

Key rule: IND10 formula must be approved before use.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_OUTPUTS,
    LKP_ADAPTATION,
    RISK_MODEL_VERSION, QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import (
    assert_upstream_clean,
    update_processing_status,
    append_version_log,
)

log = get_logger("14_adaptation")

# Adaptation measure category mapping from LKP_AdaptationStatus.csv
ADAPTATION_CATEGORIES = {
    "AD01": None,           # No adaptation
    "AD02": "Relocation",
    "AD03": "Relocation",
    "AD04": "Structural",
    "AD05": "Structural",
    "AD06": "Structural",
    "AD07": "Structural",
    "AD08": "Nature_Based",
    "AD09": "Nature_Based",
    "AD10": "Preparedness",
    "AD11": "Economic",
    "AD12": "Economic",
    "AD13": "Preparedness",
    "AD14": "Institutional",
    "AD99": None,
}


# ---------------------------------------------------------------------------
# Build adaptation inventory from DB01 and DB06
# ---------------------------------------------------------------------------

def build_adaptation_inventory(
    community_df: pd.DataFrame,
    infra_df: Optional[pd.DataFrame] = None,
    db02_agg: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Compile adaptation measures per community from:
    - DB01 Adaptation_Status (community-level primary measure)
    - DB06 Control_Present / Control_Condition (infrastructure-level)
    - DB02 Adaptation_Measure (household aggregated — optional)
    """
    result = community_df[["Community_ID","State_Code","LGA_Code"]].copy()

    # Primary community-level adaptation from DB01
    if "Adaptation_Status" in community_df.columns:
        result["Primary_Adaptation_Code"] = community_df["Adaptation_Status"]
    else:
        result["Primary_Adaptation_Code"] = np.nan

    # Categorise and count
    for cat in ["Structural","Nature_Based","Preparedness","Economic","Institutional","Relocation"]:
        result[f"{cat}_Measures_Count"] = 0

    if "Adaptation_Status" in community_df.columns:
        for idx, row in community_df.iterrows():
            code = row.get("Adaptation_Status")
            cat  = ADAPTATION_CATEGORIES.get(str(code) if pd.notna(code) else "AD01")
            if cat and cat in [c.replace("_Measures_Count","") for c in result.columns
                               if "_Measures_Count" in c]:
                comm_mask = result["Community_ID"] == row["Community_ID"]
                result.loc[comm_mask, f"{cat}_Measures_Count"] += 1

    # Supplement from DB06 control works
    if infra_df is not None and "Control_Present" in infra_df.columns:
        functional_controls = infra_df[
            (infra_df["Control_Present"] == "Yes") &
            (infra_df["Control_Condition"].isin(["Good","Fair"]))
        ]
        ctrl_counts = (
            functional_controls.groupby("Community_ID").size()
            .reset_index(name="_structural_from_infra")
        )
        result = result.merge(ctrl_counts, on="Community_ID", how="left")
        result["Structural_Measures_Count"] += result["_structural_from_infra"].fillna(0).astype(int)
        result = result.drop(columns=["_structural_from_infra"])

    # Supplement from DB02 household adaptation (aggregated)
    if db02_agg is not None and not db02_agg.empty:
        if "Adaptation_Measure" in db02_agg.columns:
            hh_adapt = (
                db02_agg.groupby("Community_ID")["Adaptation_Measure"]
                .apply(lambda x: x.notna().sum())
                .reset_index(name="_hh_adapt_count")
            )
            result = result.merge(hh_adapt, on="Community_ID", how="left")
            # Add HH adaptation evidence to preparedness count
            result["Preparedness_Measures_Count"] += (
                result["_hh_adapt_count"].fillna(0).astype(int)
            )
            result = result.drop(columns=["_hh_adapt_count"])

    # Total
    count_cols = [c for c in result.columns if c.endswith("_Measures_Count")]
    result["Total_Adaptation_Measures"] = result[count_cols].sum(axis=1)

    return result


# ---------------------------------------------------------------------------
# IND09 — Adaptation Coverage (raw proportion 0-1)
# ---------------------------------------------------------------------------

def compute_ind09_coverage(
    inventory_df: pd.DataFrame,
    max_applicable_measures: int = 6,
) -> pd.DataFrame:
    """
    IND09 = Total_Adaptation_Measures / max_applicable_measures.
    Capped at 1.0. Raw proportion — NOT 0-100 in G36.
    Inversion to vulnerability score is done in 10_vulnerability.py.
    """
    result = inventory_df.copy()
    result["IND09_Adaptation_Coverage"] = (
        result["Total_Adaptation_Measures"] / max_applicable_measures
    ).clip(0, 1)
    log.info(
        f"IND09 computed: mean coverage = "
        f"{result['IND09_Adaptation_Coverage'].mean():.2f}"
    )
    return result


# ---------------------------------------------------------------------------
# IND10 — Adaptation Gap (requires formula approval)
# ---------------------------------------------------------------------------

def compute_ind10_gap(
    inventory_df: pd.DataFrame,
    g31_path: Optional[Path] = None,
    g32_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    IND10 = Adaptation Gap — residual risk after existing adaptation.

    FORMULA (indicative — must be approved in INDICATOR_REGISTER.csv):
    IND10 = clip(R_combined - (IND09 * 50), 0, 100)
    where R_combined = mean of H_Score and E_Score (hazard-exposure pressure)
    and IND09 * 50 = adaptation reduction (50 = maximum reduction possible)

    If formula not yet approved, returns NULL for IND10.
    """
    result = inventory_df.copy()

    # Check formula approval status
    try:
        ind_reg = pd.read_csv(
            Path(__file__).parent.parent.parent / "00_Project_Control" / "INDICATOR_REGISTER.csv"
        )
        ind10_row = ind_reg[ind_reg["Indicator_ID"] == "IND10"]
        formula_approved = (
            not ind10_row.empty and
            str(ind10_row.iloc[0].get("Status","")).strip() == "Active"
        )
    except Exception:
        formula_approved = False

    if not formula_approved:
        result["IND10_Adaptation_Gap"] = np.nan
        log.warning(
            "IND10 formula not yet approved in INDICATOR_REGISTER.csv — "
            "IND10 set to NULL. Approve formula before G37 Priority computation."
        )
        return result

    # Load H and E scores
    h_scores, e_scores = pd.Series(dtype=float), pd.Series(dtype=float)

    if g31_path and g31_path.exists():
        g31 = pd.read_csv(g31_path)
        if "H_Score" in g31.columns:
            h_scores = g31.set_index("Community_ID")["H_Score"]

    if g32_path and g32_path.exists():
        g32 = pd.read_csv(g32_path)
        if "E_Score" in g32.columns:
            e_scores = g32.set_index("Community_ID")["E_Score"]

    result = result.set_index("Community_ID")
    r_combined = pd.concat([h_scores, e_scores], axis=1).mean(axis=1)
    result["_R_combined"] = r_combined

    result["IND10_Adaptation_Gap"] = (
        result["_R_combined"] - (result["IND09_Adaptation_Coverage"] * 50)
    ).clip(0, 100)

    result = result.drop(columns=["_R_combined"]).reset_index()
    log.info(
        f"IND10 computed: mean gap = {result['IND10_Adaptation_Gap'].mean():.1f}"
    )
    return result


# ---------------------------------------------------------------------------
# G36 — Adaptation layer
# ---------------------------------------------------------------------------

def build_g36(
    inventory_df: pd.DataFrame,
    ind09_df: pd.DataFrame,
    ind10_df: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble G36 from inventory, IND09, IND10."""
    result = inventory_df.copy()

    # Merge IND09
    if "IND09_Adaptation_Coverage" in ind09_df.columns:
        result = result.merge(
            ind09_df[["Community_ID","IND09_Adaptation_Coverage"]],
            on="Community_ID", how="left"
        )

    # Merge IND10
    if "IND10_Adaptation_Gap" in ind10_df.columns:
        result = result.merge(
            ind10_df[["Community_ID","IND10_Adaptation_Gap"]],
            on="Community_ID", how="left"
        )

    # Data source flag
    sources = []
    sources.append("Community_Survey")
    if ind10_df["IND10_Adaptation_Gap"].notna().any():
        sources.append("Household_Survey")
    result["Adaptation_Data_Source"] = ",".join(sources)
    result["Computation_Date"]       = date.today().isoformat()

    ANALYSIS_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = ANALYSIS_OUTPUTS / "G36_Adaptation.csv"
    result.to_csv(out, index=False)
    log.info(
        f"G36 Adaptation saved: {out} | "
        f"{len(result)} communities | "
        f"Mean IND09: {result['IND09_Adaptation_Coverage'].mean():.2f}"
    )
    update_processing_status("G36", QCStatus.DERIVED)
    append_version_log(BASELINE_VERSION, "G36", "GIS Layer", "DERIVE",
                       f"G36 Adaptation computed: {len(result)} communities")
    return result


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> Optional[pd.DataFrame]:
    log_separator(log, "14_ADAPTATION — Adaptation Inventory and Gap (G36)")
    assert_upstream_clean(["DB01","DB06"])

    comm_path  = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    infra_path = DATA_CLEAN / "DB06_Infrastructure_CLEAN.csv"

    if not comm_path.exists():
        log.error("DB01 CLEAN not found")
        return None

    community_df = pd.read_csv(comm_path)
    infra_df     = pd.read_csv(infra_path) if infra_path.exists() else None

    # DB02 aggregated (optional)
    db02_path = DATA_CLEAN / "DB02_Household_Survey_CLEAN_RESTRICTED.csv"
    db02_agg  = None
    if db02_path.exists():
        db02_raw = pd.read_csv(db02_path)
        db02_agg = db02_raw.groupby("Community_ID").first().reset_index()

    inventory = build_adaptation_inventory(community_df, infra_df, db02_agg)
    ind09_df  = compute_ind09_coverage(inventory)
    ind10_df  = compute_ind10_gap(
        ind09_df,
        g31_path=ANALYSIS_OUTPUTS / "G31_HazardIndex.csv",
        g32_path=ANALYSIS_OUTPUTS / "G32_ExposureIndex.csv",
    )
    g36 = build_g36(inventory, ind09_df, ind10_df)

    log.info("14_adaptation complete")
    return g36


if __name__ == "__main__":
    run_all()
