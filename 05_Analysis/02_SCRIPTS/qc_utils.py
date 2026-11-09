"""
qc_utils.py
===========
Shared QC utility functions used across all pipeline modules.
Covers structural, completeness, uniqueness, referential integrity,
coordinate, temporal, range, and missing-vs-zero checks.
"""

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config import (
    NIGERIA_BOUNDS,
    GPS_ACCURACY_FLAG_M,
    GPS_ACCURACY_REJECT_M,
    QCStatus,
    PROCESSING_STATUS,
    VERSION_LOG,
    BASELINE_VERSION,
    DATA_DATE,
)
from logger import get_logger

log = get_logger("qc_utils")


# ---------------------------------------------------------------------------
# QC result accumulation
# ---------------------------------------------------------------------------

class QCReport:
    """Accumulate QC check results for a single asset."""

    def __init__(self, asset_id: str, asset_type: str):
        self.asset_id   = asset_id
        self.asset_type = asset_type
        self.checks: List[Dict] = []
        self.critical_failures = 0
        self.advisory_flags    = 0

    def add(
        self,
        check_id: str,
        category: str,
        description: str,
        passed: bool,
        critical: bool,
        details: str = "",
    ) -> None:
        status = "PASS" if passed else ("CRITICAL_FAIL" if critical else "ADVISORY_FLAG")
        self.checks.append({
            "check_id":    check_id,
            "category":    category,
            "description": description,
            "status":      status,
            "critical":    critical,
            "details":     details,
        })
        if not passed:
            if critical:
                self.critical_failures += 1
            else:
                self.advisory_flags += 1

    @property
    def passed(self) -> bool:
        return self.critical_failures == 0

    @property
    def qc_status(self) -> str:
        return QCStatus.CLEAN if self.passed else QCStatus.QC_FAILED

    def summary(self) -> str:
        total   = len(self.checks)
        passed  = sum(1 for c in self.checks if c["status"] == "PASS")
        return (
            f"{self.asset_id} | {total} checks | "
            f"{passed} pass | "
            f"{self.critical_failures} critical fail | "
            f"{self.advisory_flags} advisory flag | "
            f"STATUS: {self.qc_status}"
        )

    def to_csv(self, output_path: Path) -> None:
        """Save QC report to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "check_id", "category", "description", "status", "critical", "details"
            ])
            writer.writeheader()
            writer.writerows(self.checks)
        log.info(f"QC report saved: {output_path}")


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

def check_required_fields(df: pd.DataFrame, required_fields: List[str], report: QCReport) -> None:
    """Q01 — All required fields present."""
    missing = [f for f in required_fields if f not in df.columns]
    report.add(
        "Q01", "Structure", "All required fields present",
        passed=len(missing) == 0,
        critical=True,
        details=f"Missing fields: {missing}" if missing else "",
    )


def check_no_nulls_in_required(df: pd.DataFrame, required_fields: List[str], report: QCReport) -> None:
    """Q02 — No nulls in required fields."""
    fields_present = [f for f in required_fields if f in df.columns]
    null_counts = {f: int(df[f].isna().sum()) for f in fields_present if df[f].isna().sum() > 0}
    report.add(
        "Q02", "Completeness", "No nulls in required fields",
        passed=len(null_counts) == 0,
        critical=True,
        details=f"Null counts: {null_counts}" if null_counts else "",
    )


def check_unique_key(df: pd.DataFrame, key_field: str, report: QCReport) -> None:
    """Q03 — No duplicate primary keys."""
    if key_field not in df.columns:
        return
    duplicates = int(df[key_field].duplicated().sum())
    report.add(
        "Q03", "Uniqueness", f"No duplicate {key_field}",
        passed=duplicates == 0,
        critical=True,
        details=f"{duplicates} duplicates found" if duplicates else "",
    )


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------

def check_fk_resolves(
    df: pd.DataFrame,
    fk_field: str,
    lookup_df: pd.DataFrame,
    lookup_key: str,
    report: QCReport,
    check_id: str = "Q04",
    critical: bool = True,
) -> None:
    """Q04/Q17 — Foreign key resolves to parent/lookup table."""
    if fk_field not in df.columns:
        return
    non_null = df[fk_field].dropna()
    unresolved = non_null[~non_null.isin(lookup_df[lookup_key])].unique().tolist()
    report.add(
        check_id, "Referential integrity", f"{fk_field} resolves to {lookup_key}",
        passed=len(unresolved) == 0,
        critical=critical,
        details=f"Unresolved values: {unresolved[:10]}" if unresolved else "",
    )


# ---------------------------------------------------------------------------
# Coordinate checks
# ---------------------------------------------------------------------------

def check_coordinates(
    df: pd.DataFrame,
    lat_field: str,
    lon_field: str,
    report: QCReport,
    bounds: Optional[Dict] = None,
) -> None:
    """Q05 — Coordinates within bounds and not swapped."""
    b = bounds or NIGERIA_BOUNDS
    if lat_field not in df.columns or lon_field not in df.columns:
        return

    lat_ok = df[lat_field].dropna().between(b["lat_min"], b["lat_max"])
    lon_ok = df[lon_field].dropna().between(b["lon_min"], b["lon_max"])

    lat_fail = int((~lat_ok).sum())
    lon_fail = int((~lon_ok).sum())

    # Swap detection: Lat looks like Lon or vice versa
    lat_as_lon = df[lat_field].dropna().between(b["lon_min"], b["lon_max"])
    lon_as_lat = df[lon_field].dropna().between(b["lat_min"], b["lat_max"])
    swaps = int((lat_as_lon & lon_as_lat & ~lat_ok).sum())

    passed = (lat_fail == 0) and (lon_fail == 0)
    report.add(
        "Q05", "Coordinate", "Coordinates within bounds and not swapped",
        passed=passed,
        critical=True,
        details=(
            f"Lat out-of-range: {lat_fail}; Lon out-of-range: {lon_fail}; "
            f"Possible swaps: {swaps}"
        ) if not passed else "",
    )


def check_gps_accuracy(df: pd.DataFrame, acc_field: str, report: QCReport) -> None:
    """GPS accuracy flag and reject thresholds."""
    if acc_field not in df.columns:
        return
    acc = df[acc_field].dropna()
    flagged = int((acc > GPS_ACCURACY_FLAG_M).sum())
    rejected = int((acc > GPS_ACCURACY_REJECT_M).sum())
    report.add(
        "GPS", "GPS", f"{acc_field} acceptable",
        passed=rejected == 0,
        critical=(rejected > 0),
        details=f"Flag (>{GPS_ACCURACY_FLAG_M}m): {flagged}; Reject (>{GPS_ACCURACY_REJECT_M}m): {rejected}",
    )


# ---------------------------------------------------------------------------
# Temporal checks
# ---------------------------------------------------------------------------

def check_dates(
    df: pd.DataFrame,
    date_field: str,
    report: QCReport,
    min_date: Optional[str] = None,
    allow_future: bool = False,
) -> None:
    """Q07 — Dates are valid, not future, and meet minimum date."""
    if date_field not in df.columns:
        return

    today = pd.Timestamp.now().normalize()
    parsed = pd.to_datetime(df[date_field], errors="coerce")
    invalid = int(parsed.isna().sum()) - int(df[date_field].isna().sum())
    future  = int((parsed > today).sum()) if not allow_future else 0

    too_old = 0
    if min_date:
        min_dt = pd.Timestamp(min_date)
        too_old = int((parsed < min_dt).sum())

    passed = (invalid == 0) and (future == 0) and (too_old == 0)
    report.add(
        "Q07", "Temporal", f"{date_field} valid dates",
        passed=passed,
        critical=True,
        details=f"Invalid: {invalid}; Future: {future}; Before {min_date}: {too_old}",
    )


# ---------------------------------------------------------------------------
# Range checks
# ---------------------------------------------------------------------------

def check_range(
    df: pd.DataFrame,
    field: str,
    min_val: Optional[float],
    max_val: Optional[float],
    report: QCReport,
    check_id: str = "Q09",
    critical: bool = False,
    allow_null: bool = True,
) -> None:
    """Q09 — Numeric field within plausible bounds."""
    if field not in df.columns:
        return
    series = df[field].dropna() if allow_null else df[field]
    out_low  = 0 if min_val is None else int((series < min_val).sum())
    out_high = 0 if max_val is None else int((series > max_val).sum())
    passed = (out_low == 0) and (out_high == 0)
    report.add(
        check_id, "Range", f"{field} in [{min_val}, {max_val}]",
        passed=passed,
        critical=critical,
        details=f"Below {min_val}: {out_low}; Above {max_val}: {out_high}",
    )


# ---------------------------------------------------------------------------
# Missing vs zero
# ---------------------------------------------------------------------------

def check_missing_not_zero(
    df: pd.DataFrame,
    fields: List[str],
    report: QCReport,
) -> None:
    """Q10 — Zero values that should be NULL (not-recorded sentinel)."""
    zero_counts = {}
    for field in fields:
        if field in df.columns:
            zeros = int((df[field] == 0).sum())
            if zeros > 0:
                zero_counts[field] = zeros

    report.add(
        "Q10", "Missing vs zero",
        "NULL used for not-recorded values — not 0",
        passed=len(zero_counts) == 0,
        critical=True,
        details=(
            f"Possible false-zero fields (verify each): {zero_counts}"
        ) if zero_counts else "",
    )


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

def check_allowed_values(
    df: pd.DataFrame,
    field: str,
    allowed: List[Any],
    report: QCReport,
    check_id: str = "Q08",
    critical: bool = False,
) -> None:
    """Q08 — Field contains only allowed values."""
    if field not in df.columns:
        return
    non_null = df[field].dropna()
    invalid = non_null[~non_null.isin(allowed)].unique().tolist()
    report.add(
        check_id, "Logical", f"{field} allowed values",
        passed=len(invalid) == 0,
        critical=critical,
        details=f"Invalid values: {invalid[:10]}" if invalid else "",
    )


# ---------------------------------------------------------------------------
# PROCESSING_STATUS update
# ---------------------------------------------------------------------------

def update_processing_status(
    asset_id: str,
    new_status: str,
    version: str = BASELINE_VERSION,
    updated_by: str = "pipeline",
    qc_passed: Optional[bool] = None,
    qc_by: str = "pipeline",
    notes: str = "",
) -> None:
    """Update a row in PROCESSING_STATUS.csv for the given asset."""
    today = date.today().isoformat()
    df = pd.read_csv(PROCESSING_STATUS)
    mask = df["Asset_ID"] == asset_id
    if mask.any():
        df.loc[mask, "Current_Status"] = new_status
        df.loc[mask, "Version"]        = version
        df.loc[mask, "Last_Updated"]   = today
        df.loc[mask, "Updated_By"]     = updated_by
        if qc_passed is not None:
            df.loc[mask, "QC_Passed"] = "Yes" if qc_passed else "No"
            df.loc[mask, "QC_Date"]   = today
            df.loc[mask, "QC_By"]     = qc_by
        if notes:
            df.loc[mask, "Notes"] = notes
        df.to_csv(PROCESSING_STATUS, index=False)
        log.info(f"PROCESSING_STATUS updated: {asset_id} → {new_status}")
    else:
        log.warning(f"Asset not found in PROCESSING_STATUS: {asset_id}")


def get_asset_status(asset_id: str) -> Optional[str]:
    """Return the current QC_Status for an asset."""
    df = pd.read_csv(PROCESSING_STATUS)
    row = df[df["Asset_ID"] == asset_id]
    if row.empty:
        return None
    return row.iloc[0]["Current_Status"]


def assert_upstream_clean(asset_ids: List[str]) -> None:
    """
    Raise RuntimeError if any upstream dependency is not CLEAN.
    Called at the start of every downstream processing module.
    """
    for asset_id in asset_ids:
        status = get_asset_status(asset_id)
        if status != QCStatus.CLEAN:
            raise RuntimeError(
                f"Upstream dependency {asset_id} has status '{status}' — "
                f"must be '{QCStatus.CLEAN}' before this module can run. "
                f"Pipeline halted."
            )
    log.info(f"Upstream dependencies confirmed CLEAN: {asset_ids}")


# ---------------------------------------------------------------------------
# Version log
# ---------------------------------------------------------------------------

def append_version_log(
    version: str,
    asset_id: str,
    asset_type: str,
    change_type: str,
    description: str,
    previous_version: str = "",
    status: str = "Active",
    notes: str = "",
) -> None:
    """Append a row to VERSION_LOG.csv."""
    today = date.today().isoformat()
    row = {
        "Version":          version,
        "Date":             today,
        "Author":           "pipeline",
        "Asset_ID":         asset_id,
        "Asset_Type":       asset_type,
        "Change_Type":      change_type,
        "Description":      description,
        "Previous_Version": previous_version,
        "Status":           status,
        "Notes":            notes,
    }
    with open(VERSION_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writerow(row)
    log.debug(f"VERSION_LOG updated: {asset_id} {version}")
