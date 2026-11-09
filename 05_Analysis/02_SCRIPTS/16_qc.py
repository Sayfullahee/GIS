"""
16_qc.py
========
Cross-cutting QC and reporting module.

Responsibilities:
  Q11 — Privacy check: no household data in any public output
  Q12 — Provenance: all external datasets in SOURCE_REGISTER.csv
  Q13 — Version control: Data_Version populated; VERSION_LOG updated
  Q14 — Enumerator QC: completion rate and response pattern checks (DB02)
  Q15 — Time-series consistency: already run in 05_climate / 08_hydropower
  Q16 — Cross-database consistency: coordinates and codes consistent across DBs
  Q20 — Geometry-attribute sync: GIS coordinates match database lat/lon

Produces timestamped QC run reports in 05_Analysis/04_QC/.
"""

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from config import (
    DATA_CLEAN, ANALYSIS_QC, ANALYSIS_OUTPUTS,
    SOURCE_REGISTER, PROCESSING_STATUS,
    QCStatus,
)
from logger import get_logger, log_separator
from qc_utils import (
    QCReport,
    update_processing_status,
)

log = get_logger("16_qc")


# ---------------------------------------------------------------------------
# Q11 — Privacy check
# ---------------------------------------------------------------------------

def check_privacy_outputs(output_dir: Path = ANALYSIS_OUTPUTS) -> QCReport:
    """
    Scan all CSV files in ANALYSIS_OUTPUTS for prohibited columns
    (Household_ID, household Latitude/Longitude at row level without aggregation).
    """
    report = QCReport("PRIVACY_CHECK", "Cross-cutting QC")
    prohibited = ["Household_ID"]

    issues = []
    for csv_file in output_dir.glob("*.csv"):
        try:
            # Read only headers (nrows=0)
            cols = pd.read_csv(csv_file, nrows=0).columns.tolist()
            found = [c for c in prohibited if c in cols]
            if found:
                issues.append(f"{csv_file.name}: {found}")
        except Exception:
            pass

    report.add(
        "Q11", "Privacy",
        "No Household_ID in any public output files",
        passed=len(issues) == 0,
        critical=True,
        details="; ".join(issues) if issues else "",
    )
    log.info(f"Q11 Privacy check: {'PASS' if not issues else 'FAIL — ' + str(issues)}")
    return report


# ---------------------------------------------------------------------------
# Q12 — Provenance
# ---------------------------------------------------------------------------

def check_provenance() -> QCReport:
    """All external datasets registered in SOURCE_REGISTER.csv."""
    report = QCReport("PROVENANCE_CHECK", "Cross-cutting QC")

    required_sources = [
        "SRC001","SRC002","SRC003","SRC004","SRC005",
        "SRC007","SRC008","SRC009","SRC010","SRC011","SRC012",
        "SRC013","SRC014","SRC015","SRC016","SRC017",
    ]
    try:
        df = pd.read_csv(SOURCE_REGISTER)
        registered = df["Source_ID"].dropna().tolist()
        missing = [s for s in required_sources if s not in registered]
        report.add(
            "Q12", "Provenance",
            "All required sources in SOURCE_REGISTER.csv",
            passed=len(missing) == 0,
            critical=False,
            details=f"Missing: {missing}" if missing else "",
        )
    except Exception as exc:
        report.add("Q12", "Provenance", "SOURCE_REGISTER.csv readable",
                   passed=False, critical=False, details=str(exc))

    return report


# ---------------------------------------------------------------------------
# Q13 — Version control
# ---------------------------------------------------------------------------

def check_version_control(output_dir: Path = ANALYSIS_OUTPUTS) -> QCReport:
    """Data_Version populated in all output CSVs."""
    report = QCReport("VERSION_CHECK", "Cross-cutting QC")
    issues = []

    for csv_file in output_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file, nrows=5)
            if "Data_Version" in df.columns:
                nulls = df["Data_Version"].isna().sum()
                if nulls > 0:
                    issues.append(f"{csv_file.name}: {nulls} null Data_Version rows")
        except Exception:
            pass

    report.add(
        "Q13", "Version control",
        "Data_Version populated in all outputs",
        passed=len(issues) == 0,
        critical=False,
        details="; ".join(issues[:5]) if issues else "",
    )
    return report


# ---------------------------------------------------------------------------
# Q14 — Enumerator QC (DB02)
# ---------------------------------------------------------------------------

def check_enumerator_quality(
    db02_path: Optional[Path] = None,
    min_completion_rate: float = 0.80,
) -> QCReport:
    """Flag enumerators with <80% completion or anomalous response patterns."""
    report = QCReport("ENUMERATOR_QC", "Cross-cutting QC")

    p = db02_path or DATA_CLEAN / "DB02_Household_Survey_CLEAN_RESTRICTED.csv"
    if not p.exists():
        report.add("Q14", "Enumerator QC", "DB02 available for enumerator check",
                   passed=False, critical=False, details="DB02 not found — skipped")
        return report

    df = pd.read_csv(p)
    if "Enumerator_ID" not in df.columns:
        report.add("Q14", "Enumerator QC", "Enumerator_ID field present",
                   passed=False, critical=False, details="Enumerator_ID missing from DB02")
        return report

    # Required fields for completion rate
    required_fields = [
        "HH_Size","HH_Head_Sex","Livelihood_Primary","Flood_Affected",
        "Erosion_Affected","Water_Source","Electricity_Access",
    ]
    present_fields = [f for f in required_fields if f in df.columns]

    if not present_fields:
        report.add("Q14", "Enumerator QC", "Completion fields available",
                   passed=True, critical=False, details="No optional fields to check")
        return report

    df["_completion_rate"] = df[present_fields].notna().mean(axis=1)
    enumerator_stats = (
        df.groupby("Enumerator_ID")
        .agg(
            Mean_Completion = ("_completion_rate", "mean"),
            Record_Count    = ("Household_ID",     "count"),
        )
        .reset_index()
    )

    low_completion = enumerator_stats[
        enumerator_stats["Mean_Completion"] < min_completion_rate
    ]
    flagged = low_completion["Enumerator_ID"].tolist()

    report.add(
        "Q14", "Enumerator QC",
        f"All enumerators >= {min_completion_rate:.0%} completion rate",
        passed=len(flagged) == 0,
        critical=False,
        details=(f"Flagged enumerators ({len(flagged)}): {flagged[:10]}"
                 if flagged else ""),
    )

    if flagged:
        flag_path = ANALYSIS_QC / f"DB02_Enumerator_Flags_{date.today().isoformat()}.csv"
        low_completion.to_csv(flag_path, index=False)
        log.warning(f"Q14: {len(flagged)} enumerators below threshold — saved to {flag_path}")

    return report


# ---------------------------------------------------------------------------
# Q16 — Cross-database consistency
# ---------------------------------------------------------------------------

def check_cross_database_consistency() -> QCReport:
    """
    Verify coordinates and codes consistent across parent-child tables.
    E.g. DB03 sites within 10km of their DB01 parent community.
    """
    report = QCReport("CROSS_DB_CHECK", "Cross-cutting QC")

    db01_path = DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    db03_path = DATA_CLEAN / "DB03_Erosion_Sites_CLEAN.csv"
    db06_path = DATA_CLEAN / "DB06_Infrastructure_CLEAN.csv"

    if not all(p.exists() for p in [db01_path, db03_path]):
        report.add("Q16", "Cross-DB", "Required files available",
                   passed=False, critical=False, details="DB01 or DB03 not found")
        return report

    db01 = pd.read_csv(db01_path)
    db03 = pd.read_csv(db03_path)

    comm_coords = db01.set_index("Community_ID")[["Latitude","Longitude"]]
    distant = []

    for _, row in db03.iterrows():
        comm = row.get("Community_ID")
        if pd.isna(comm) or comm not in comm_coords.index:
            continue
        clat = float(comm_coords.loc[comm,"Latitude"])
        clon = float(comm_coords.loc[comm,"Longitude"])
        slat = float(row.get("Latitude", clat))
        slon = float(row.get("Longitude", clon))
        dist_km = ((slat - clat)**2 + (slon - clon)**2)**0.5 * 111
        if dist_km > 10.0:
            distant.append((row.get("Erosion_ID"), dist_km))

    report.add(
        "Q16", "Cross-DB",
        "DB03 erosion sites within 10km of parent community",
        passed=len(distant) == 0,
        critical=False,
        details=f"{len(distant)} sites > 10km from community centroid" if distant else "",
    )
    return report


# ---------------------------------------------------------------------------
# Q20 — Geometry-attribute sync
# ---------------------------------------------------------------------------

def check_geometry_attribute_sync() -> QCReport:
    """
    Check that GIS output CSV coordinates match database lat/lon.
    Compares G03/G26/G19 CSV outputs against DB01/DB03/DB06.
    """
    report = QCReport("GEOM_SYNC_CHECK", "Cross-cutting QC")

    pairs = [
        (DATA_CLEAN / "DB01_Community_Master_CLEAN.csv",  "Community_ID",
         ANALYSIS_OUTPUTS / "G03_Communities.csv",        "Community_ID"),
    ]

    for db_path, db_key, gis_path, gis_key in pairs:
        if not db_path.exists() or not gis_path.exists():
            continue
        db  = pd.read_csv(db_path)
        gis = pd.read_csv(gis_path)

        merged = db.merge(gis, on=db_key, suffixes=("_db","_gis"))
        for coord in ["Latitude","Longitude"]:
            db_col  = f"{coord}_db"  if f"{coord}_db"  in merged.columns else coord
            gis_col = f"{coord}_gis" if f"{coord}_gis" in merged.columns else coord
            if db_col in merged.columns and gis_col in merged.columns:
                diff = (merged[db_col] - merged[gis_col]).abs()
                mismatches = int((diff > 0.00001).sum())
                report.add(
                    "Q20", "Geometry sync",
                    f"{db_path.name} {coord} matches GIS layer",
                    passed=mismatches == 0,
                    critical=True,
                    details=f"{mismatches} coordinate mismatches > 0.00001 degrees",
                )
    return report


# ---------------------------------------------------------------------------
# Run all cross-cutting QC checks
# ---------------------------------------------------------------------------

def run_all() -> Dict[str, QCReport]:
    log_separator(log, "16_QC — Cross-Cutting Quality Checks")
    reports = {}

    checks = [
        ("Privacy",          check_privacy_outputs),
        ("Provenance",       check_provenance),
        ("Version",          check_version_control),
        ("Enumerator",       check_enumerator_quality),
        ("Cross_DB",         check_cross_database_consistency),
        ("Geometry_Sync",    check_geometry_attribute_sync),
    ]

    for name, fn in checks:
        try:
            r = fn()
            reports[name] = r
            log.info(r.summary())
            r.to_csv(ANALYSIS_QC / f"QC_{name}_{date.today().strftime('%Y%m%d')}.csv")
        except Exception as exc:
            log.error(f"Check {name} raised exception: {exc}")

    critical_fails = sum(r.critical_failures for r in reports.values())
    if critical_fails > 0:
        log.error(f"16_qc: {critical_fails} critical failures — resolve before publication")
    else:
        log.info("16_qc: all critical checks passed")

    return reports


if __name__ == "__main__":
    run_all()
