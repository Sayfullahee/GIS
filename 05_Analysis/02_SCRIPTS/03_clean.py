"""
03_clean.py
===========
Apply validated fixes, filter non-consenting household records,
standardise coded fields, and promote datasets from RAW → CLEAN.

Rules:
  - Only runs on datasets that passed 02_validate.py (QC_Status = CLEAN or
    explicitly promoted by the data manager after manual fixes).
  - DB02: removes / quarantines records where Consent_Given != 'Yes'.
  - Standardises text case in coded fields (State_Code, LGA_Code etc.).
  - Writes clean copies to DATA_CLEAN/.
  - Updates QC_Status = CLEAN and Record_Modified timestamp.
  - Does NOT impute missing values — NULL stays NULL.
  - Does NOT modify raw files in DATA_RAW/.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    DATA_RAW, DATA_CLEAN,
    QCStatus, BASELINE_VERSION, ANALYSIS_QC,
)
from logger import get_logger, log_separator
from qc_utils import (
    update_processing_status,
    append_version_log,
    get_asset_status,
)
from qc_utils import QCReport

log = get_logger("03_clean")


# ---------------------------------------------------------------------------
# Helper: assert source has passed validation
# ---------------------------------------------------------------------------

def _require_validated(asset_id: str) -> None:
    status = get_asset_status(asset_id)
    if status not in (QCStatus.CLEAN, QCStatus.VALIDATED):
        raise RuntimeError(
            f"{asset_id} has status '{status}' — "
            f"run 02_validate.py first and fix all critical failures."
        )


# ---------------------------------------------------------------------------
# Common cleaning operations
# ---------------------------------------------------------------------------

def _standardise_codes(df: pd.DataFrame, code_columns: list) -> pd.DataFrame:
    """Upper-case and strip all coded fields."""
    for col in code_columns:
        if col in df.columns:
            df[col] = df[col].str.strip().str.upper() if df[col].dtype == object else df[col]
    return df


def _set_clean_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Mark all records as CLEAN with today's modification date."""
    today = date.today().isoformat()
    df["QC_Status"]      = QCStatus.CLEAN
    df["Record_Modified"] = today
    return df


def _save_clean(df: pd.DataFrame, filename: str) -> Path:
    """Write clean DataFrame to DATA_CLEAN/."""
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    out_path = DATA_CLEAN / filename
    df.to_csv(out_path, index=False, encoding="utf-8")
    log.info(f"Clean file saved: {out_path} ({len(df)} records)")
    return out_path


# ---------------------------------------------------------------------------
# DB01 — Community Master
# ---------------------------------------------------------------------------

def clean_db01(source_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    asset_id = "DB01"
    _require_validated(asset_id)

    path = source_path or (DATA_RAW / "DB01_Community_Master_RAW.csv" if (DATA_RAW / "DB01_Community_Master_RAW.csv").exists() else DATA_RAW / "DB01_Community_Master_ENTRY_TEMPLATE.csv")
    if not path.exists():
        log.warning(f"DB01 file not found: {path}")
        return None

    df = pd.read_csv(path)
    original_count = len(df)

    # Standardise coded fields
    code_cols = ["State_Code","LGA_Code","Livelihood","Water_Source","Adaptation_Status"]
    df = _standardise_codes(df, code_cols)

    # Standardise allowed-value fields to title case
    for col in ["Electricity_Access","Flood_Experience","Erosion_Presence"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title()

    df = _set_clean_metadata(df)
    _save_clean(df, "DB01_Community_Master_CLEAN.csv")

    log.info(f"DB01 cleaned: {original_count} records → {len(df)} records")
    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True)
    append_version_log(BASELINE_VERSION, asset_id, "Database", "CLEAN",
                       f"DB01 promoted to CLEAN: {len(df)} records")
    return df


# ---------------------------------------------------------------------------
# DB02 — Household Survey (RESTRICTED)
# ---------------------------------------------------------------------------

def clean_db02(source_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    RESTRICTED. Filters out non-consenting records.
    Clean output stored in DATA_CLEAN/ — Level 3 access only.
    """
    asset_id = "DB02"
    _require_validated(asset_id)

    path = source_path or DATA_RAW / "DB02_Household_Survey_RAW.csv"
    if not path.exists():
        log.warning(f"DB02 file not found: {path} — skipping")
        return None

    df = pd.read_csv(path)
    original_count = len(df)

    # CONSENT GATE — quarantine non-consenting records
    if "Consent_Given" in df.columns:
        no_consent = df[df["Consent_Given"] != "Yes"]
        if len(no_consent) > 0:
            quarantine_path = ANALYSIS_QC / f"DB02_QUARANTINE_no_consent_{date.today().isoformat()}.csv"
            no_consent.to_csv(quarantine_path, index=False)
            log.warning(
                f"DB02: {len(no_consent)} records quarantined (Consent_Given != Yes). "
                f"Saved to {quarantine_path}. PI review required before deletion."
            )
        df = df[df["Consent_Given"] == "Yes"].copy()

    code_cols = ["Livelihood_Primary","Livelihood_Secondary","Water_Source","Adaptation_Measure"]
    df = _standardise_codes(df, code_cols)
    df = _set_clean_metadata(df)

    # RESTRICTED — save to clean but note access level
    _save_clean(df, "DB02_Household_Survey_CLEAN_RESTRICTED.csv")
    log.info(f"DB02 cleaned: {original_count} → {len(df)} consented records (RESTRICTED)")

    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True,
                             notes="RESTRICTED — Level 3 access only")
    append_version_log(BASELINE_VERSION, asset_id, "Database", "CLEAN",
                       f"DB02 promoted to CLEAN (RESTRICTED): {len(df)} consented records")
    return df


# ---------------------------------------------------------------------------
# DB03 — Erosion Sites
# ---------------------------------------------------------------------------

def clean_db03(source_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    asset_id = "DB03"
    _require_validated(asset_id)

    path = source_path or (DATA_RAW / "DB03_Erosion_Sites_RAW.csv" if (DATA_RAW / "DB03_Erosion_Sites_RAW.csv").exists() else DATA_RAW / "DB03_Erosion_Sites_ENTRY_TEMPLATE.csv")
    if not path.exists():
        log.warning(f"DB03 file not found: {path}")
        return None

    df = pd.read_csv(path)
    code_cols = ["Erosion_Type","Activity_Status"]
    df = _standardise_codes(df, code_cols)

    # Standardise slope classification
    for col in ["Slope","Control_Condition","Sediment_To_River","Control_Present","Infrastructure_Threat"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title() if df[col].dtype == object else df[col]

    df = _set_clean_metadata(df)
    _save_clean(df, "DB03_Erosion_Sites_CLEAN.csv")

    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True)
    append_version_log(BASELINE_VERSION, asset_id, "Database", "CLEAN",
                       f"DB03 promoted to CLEAN: {len(df)} records")
    return df


# ---------------------------------------------------------------------------
# DB04 — Hydropower/Water Observations
# ---------------------------------------------------------------------------

def clean_db04(source_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    asset_id = "DB04"
    _require_validated(asset_id)

    path = source_path or DATA_RAW / "DB04_Hydropower_Water_RAW.csv"
    if not path.exists():
        log.warning(f"DB04 file not found: {path}")
        return None

    df = pd.read_csv(path)
    code_cols = ["State_Code","LGA_Code","Operating_Status"]
    df = _standardise_codes(df, code_cols)

    for col in ["Flood_Damage","Operational_Disruption","Transmission_Impact","Community_Impact"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title() if df[col].dtype == object else df[col]

    df = _set_clean_metadata(df)
    _save_clean(df, "DB04_Hydropower_Water_CLEAN.csv")

    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True)
    append_version_log(BASELINE_VERSION, asset_id, "Database", "CLEAN",
                       f"DB04 promoted to CLEAN: {len(df)} records")
    return df


# ---------------------------------------------------------------------------
# DB05 — Climate Observations
# ---------------------------------------------------------------------------

def clean_db05(source_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    asset_id = "DB05"
    _require_validated(asset_id)

    path = source_path or DATA_RAW / "DB05_Climate_Observations_RAW.csv"
    if not path.exists():
        log.warning(f"DB05 file not found: {path}")
        return None

    df = pd.read_csv(path)
    code_cols = ["State_Code","Observation_Period","Unit_Standard"]
    df = _standardise_codes(df, code_cols)

    # Standardise QC flags to upper
    for col in ["Rainfall_QC_Flag","Temperature_QC_Flag"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.upper() if df[col].dtype == object else df[col]

    df = _set_clean_metadata(df)
    _save_clean(df, "DB05_Climate_Observations_CLEAN.csv")

    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True)
    append_version_log(BASELINE_VERSION, asset_id, "Database", "CLEAN",
                       f"DB05 promoted to CLEAN: {len(df)} records")
    return df


# ---------------------------------------------------------------------------
# DB06 — Infrastructure
# ---------------------------------------------------------------------------

def clean_db06(source_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    asset_id = "DB06"
    _require_validated(asset_id)

    path = source_path or (DATA_RAW / "DB06_Infrastructure_RAW.csv" if (DATA_RAW / "DB06_Infrastructure_RAW.csv").exists() else DATA_RAW / "DB06_Infrastructure_ENTRY_TEMPLATE.csv")
    if not path.exists():
        log.warning(f"DB06 file not found: {path}")
        return None

    df = pd.read_csv(path)
    code_cols = ["Infrastructure_Type","State_Code","LGA_Code"]
    df = _standardise_codes(df, code_cols)

    for col in ["Condition","Flood_Exposure","Erosion_Exposure","Critical_Service","Service_Disruption"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title() if df[col].dtype == object else df[col]

    df = _set_clean_metadata(df)
    _save_clean(df, "DB06_Infrastructure_CLEAN.csv")

    update_processing_status(asset_id, QCStatus.CLEAN, qc_passed=True)
    append_version_log(BASELINE_VERSION, asset_id, "Database", "CLEAN",
                       f"DB06 promoted to CLEAN: {len(df)} records")
    return df


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

def run_all() -> dict:
    log_separator(log, "03_CLEAN — Promote Validated Datasets to CLEAN")
    results = {}
    for name, fn in [
        ("DB01", clean_db01),
        ("DB02", clean_db02),
        ("DB03", clean_db03),
        ("DB04", clean_db04),
        ("DB05", clean_db05),
        ("DB06", clean_db06),
    ]:
        try:
            df = fn()
            results[name] = "CLEAN" if df is not None else "SKIPPED"
        except RuntimeError as exc:
            log.error(f"{name}: {exc}")
            results[name] = "FAILED"
    return results


if __name__ == "__main__":
    run_all()
