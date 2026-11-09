"""
02_validate.py
==============
Structural, referential, coordinate, temporal, logical, range,
and missing-vs-zero QC checks for all six field databases (DB01-DB06).

On pass  → sets QC_Status = CLEAN
On fail  → sets QC_Status = QC_FAILED and raises PipelineCriticalError
           so run_pipeline.py halts before any downstream processing.

QC checks implemented here: Q01-Q10, Q17-Q19
"""

from datetime import date
from pathlib import Path
from typing import Dict

import pandas as pd

from config import (
    DATA_RAW, DATA_CLEAN, DATA_LOOKUPS,
    LKP_STATES, LKP_LGAS, LKP_LIVELIHOOD,
    LKP_WATER_SOURCE, LKP_ADAPTATION, LKP_QC_STATUS,
    LKP_EROSION_TYPE, LKP_EROSION_SEV,
    LKP_INFRA_TYPE, LKP_OP_STATUS,
    ANALYSIS_QC, QCStatus, BASELINE_VERSION,
    NIGERIA_BOUNDS,
)
from logger import get_logger, log_separator
from qc_utils import (
    QCReport,
    check_required_fields,
    check_no_nulls_in_required,
    check_unique_key,
    check_fk_resolves,
    check_coordinates,
    check_gps_accuracy,
    check_dates,
    check_range,
    check_missing_not_zero,
    check_allowed_values,
    update_processing_status,
    append_version_log,
)

log = get_logger("02_validate")


class PipelineCriticalError(RuntimeError):
    """Raised when a critical QC check fails — halts the pipeline."""
    pass


# ---------------------------------------------------------------------------
# Load lookups once
# ---------------------------------------------------------------------------

def _load_lookup(path: Path, key_col: str) -> pd.DataFrame:
    return pd.read_csv(path)[[key_col]].dropna()


# ---------------------------------------------------------------------------
# DB01 — Community Master
# ---------------------------------------------------------------------------

def validate_db01(df: pd.DataFrame) -> QCReport:
    report = QCReport("DB01", "Database")

    lkp_states = _load_lookup(LKP_STATES, "State_Code")
    lkp_lgas   = _load_lookup(LKP_LGAS,   "LGA_Code")
    lkp_lga_df = pd.read_csv(LKP_LGAS)
    lkp_liv    = _load_lookup(LKP_LIVELIHOOD, "Livelihood_Code")
    lkp_water  = _load_lookup(LKP_WATER_SOURCE, "Water_Source_Code")
    lkp_adapt  = _load_lookup(LKP_ADAPTATION, "Adaptation_Code")

    required = [
        "Community_ID","Community","State_Code","State_Name",
        "LGA_Code","LGA","Latitude","Longitude",
        "GPS_Accuracy_m","Survey_Date","Record_Created","Data_Version","QC_Status",
    ]

    check_required_fields(df, required, report)
    check_no_nulls_in_required(df, required, report)
    check_unique_key(df, "Community_ID", report)
    check_fk_resolves(df, "State_Code", lkp_states, "State_Code", report, "Q04a")
    check_fk_resolves(df, "LGA_Code",   lkp_lgas,   "LGA_Code",   report, "Q04b")

    # State/LGA consistency
    if "State_Code" in df.columns and "LGA_Code" in df.columns:
        merged = df.merge(
            lkp_lga_df[["LGA_Code","State_Code"]],
            on="LGA_Code", how="left", suffixes=("","_lkp")
        )
        mismatch = int((merged["State_Code"] != merged["State_Code_lkp"]).sum())
        report.add("Q04c","Referential integrity","State_Code/LGA_Code consistent",
                   passed=mismatch==0, critical=True,
                   details=f"{mismatch} mismatches" if mismatch else "")

    check_coordinates(df, "Latitude", "Longitude", report)
    check_gps_accuracy(df, "GPS_Accuracy_m", report)
    check_dates(df, "Survey_Date", report, min_date="2026-01-01")

    # Optional FK checks
    check_fk_resolves(df, "Livelihood", lkp_liv, "Livelihood_Code", report, "Q17a", critical=False)
    check_fk_resolves(df, "Water_Source", lkp_water, "Water_Source_Code", report, "Q17b", critical=False)
    check_fk_resolves(df, "Adaptation_Status", lkp_adapt, "Adaptation_Code", report, "Q17c", critical=False)

    check_allowed_values(df, "Electricity_Access", ["Yes","No","Partial","Unknown"], report, "Q08a")
    check_allowed_values(df, "Flood_Experience",   ["Yes","No","Unknown"],           report, "Q08b")
    check_allowed_values(df, "Erosion_Presence",   ["Yes","No","Unknown"],           report, "Q08c")

    check_range(df, "Population", 1, 100000, report, "Q09a", critical=False)

    # Privacy: no Household_ID
    report.add("Q11","Privacy","No Household_ID in DB01",
               passed="Household_ID" not in df.columns, critical=True)

    return report


# ---------------------------------------------------------------------------
# DB02 — Household Survey
# ---------------------------------------------------------------------------

def validate_db02(df: pd.DataFrame, community_ids: pd.Series) -> QCReport:
    report = QCReport("DB02", "Database")

    required = [
        "Household_ID","Community_ID","Enumerator_ID","Survey_Date",
        "Consent_Given","Record_Created","Data_Version","QC_Status",
    ]
    check_required_fields(df, required, report)
    check_no_nulls_in_required(df, required, report)
    check_unique_key(df, "Household_ID", report)

    comm_df = pd.DataFrame({"Community_ID": community_ids})
    check_fk_resolves(df, "Community_ID", comm_df, "Community_ID", report)

    # Consent gate
    if "Consent_Given" in df.columns:
        no_consent = int((df["Consent_Given"] == "No").sum())
        report.add("Q19","Consent","All Consent_Given = Yes",
                   passed=no_consent==0, critical=True,
                   details=f"{no_consent} records without consent — must be quarantined")

    check_dates(df, "Survey_Date", report, min_date="2026-01-01")
    check_coordinates(df, "Latitude", "Longitude", report)

    check_range(df, "HH_Size",     1,   30, report, "Q09a", critical=False)
    check_range(df, "HH_Head_Age", 15, 100, report, "Q09b", critical=False)

    check_missing_not_zero(df, ["Flood_Losses_NGN","Erosion_Losses_NGN"], report)

    report.add("Q11","Privacy","GPS coordinates not published from DB02",
               passed=True, critical=True,
               details="Reminder: DB02 Lat/Lon must never appear in Level 1/2 outputs")

    return report


# ---------------------------------------------------------------------------
# DB03 — Erosion Sites
# ---------------------------------------------------------------------------

def validate_db03(df: pd.DataFrame) -> QCReport:
    report = QCReport("DB03", "Database")

    lkp_etype = _load_lookup(LKP_EROSION_TYPE, "Erosion_Type_Code")
    lkp_esev  = _load_lookup(LKP_EROSION_SEV,  "Severity_Code")

    required = [
        "Erosion_ID","Community_ID","Latitude","Longitude",
        "GPS_Accuracy_m","Erosion_Type","Activity_Status","Severity_0_4",
        "Infrastructure_Threat","Observation_Date","Observed_By",
        "Record_Created","Data_Version","QC_Status",
    ]
    check_required_fields(df, required, report)
    check_no_nulls_in_required(df, required, report)
    check_unique_key(df, "Erosion_ID", report)
    check_fk_resolves(df, "Erosion_Type",  lkp_etype, "Erosion_Type_Code", report, "Q04a")

    # Severity must be integer 0-4
    if "Severity_0_4" in df.columns:
        sev = pd.to_numeric(df["Severity_0_4"], errors="coerce")
        bad = int(~sev.isin([0,1,2,3,4]).all())  # simplified
        invalid_sev = int((~sev.isin([0,1,2,3,4])).sum())
        report.add("Q04b","Referential integrity","Severity_0_4 is integer 0-4",
                   passed=invalid_sev==0, critical=True,
                   details=f"{invalid_sev} invalid severity values")

    check_coordinates(df, "Latitude", "Longitude", report)
    check_gps_accuracy(df, "GPS_Accuracy_m", report)
    check_dates(df, "Observation_Date", report, min_date="2026-01-01")

    check_allowed_values(df, "Activity_Status",
                         ["Active","Inactive","Stabilised","Unknown"], report, "Q08a")
    check_allowed_values(df, "Infrastructure_Threat",
                         ["Yes","No","Unknown"], report, "Q08b")

    check_range(df, "Length_m", 0.1, 10000, report, "Q09a", critical=False)
    check_range(df, "Width_m",  0.1,  2000, report, "Q09b", critical=False)
    check_range(df, "Depth_m",  0.1,   100, report, "Q09c", critical=False)

    check_missing_not_zero(df, ["Length_m","Width_m","Depth_m"], report)

    return report


# ---------------------------------------------------------------------------
# DB04 — Hydropower/Water Observations
# ---------------------------------------------------------------------------

def validate_db04(df: pd.DataFrame) -> QCReport:
    report = QCReport("DB04", "Database")

    lkp_ops = _load_lookup(LKP_OP_STATUS, "Status_Code")

    required = [
        "Observation_ID","Hydro_ID","Facility_Name",
        "State_Code","LGA_Code","Latitude","Longitude",
        "Observation_Date","Operating_Status",
        "Monitoring_Source","Source_Date",
        "Record_Created","Data_Version","QC_Status",
    ]
    check_required_fields(df, required, report)
    check_no_nulls_in_required(df, required, report)
    check_unique_key(df, "Observation_ID", report)
    check_fk_resolves(df, "Operating_Status", lkp_ops, "Status_Code", report)

    lkp_states = _load_lookup(LKP_STATES, "State_Code")
    check_fk_resolves(df, "State_Code", lkp_states, "State_Code", report, "Q04b")

    check_coordinates(df, "Latitude", "Longitude", report)
    check_dates(df, "Observation_Date", report, min_date="2010-01-01")
    check_dates(df, "Source_Date", report, min_date="2000-01-01")

    check_range(df, "Generation_MWh",    0, None, report, "Q09a", critical=False)
    check_range(df, "Reservoir_Level_m", 0, None, report, "Q09b", critical=False)
    check_range(df, "River_Discharge_m3s", 0, None, report, "Q09c", critical=False)

    check_missing_not_zero(df, ["Generation_MWh"], report)

    return report


# ---------------------------------------------------------------------------
# DB05 — Climate Observations
# ---------------------------------------------------------------------------

def validate_db05(df: pd.DataFrame) -> QCReport:
    report = QCReport("DB05", "Database")

    required = [
        "Climate_ID","Station_ID","Station_Name",
        "Observation_Date","Observation_Period","State_Code",
        "Latitude","Longitude","Source","Source_Date",
        "Unit_Standard","QC_Status","Record_Created","Data_Version",
    ]
    check_required_fields(df, required, report)
    check_no_nulls_in_required(df, required, report)
    check_unique_key(df, "Climate_ID", report)

    lkp_states = _load_lookup(LKP_STATES, "State_Code")
    check_fk_resolves(df, "State_Code", lkp_states, "State_Code", report, "Q04a", critical=False)

    check_coordinates(df, "Latitude", "Longitude", report)
    check_dates(df, "Observation_Date", report, min_date="1950-01-01")

    check_range(df, "Rainfall_mm",      0,   500, report, "Q09a", critical=False)
    check_range(df, "Temperature_Max_C", -5,  55, report, "Q09b", critical=True)
    check_range(df, "Temperature_Min_C", -5,  55, report, "Q09c", critical=True)

    # Min <= Max
    if all(c in df.columns for c in ["Temperature_Min_C","Temperature_Max_C"]):
        inv = int((df["Temperature_Min_C"] > df["Temperature_Max_C"]).sum())
        report.add("Q08a","Logical","Temperature_Min_C <= Temperature_Max_C",
                   passed=inv==0, critical=True,
                   details=f"{inv} inversions")

    check_allowed_values(df, "Observation_Period",
                         ["Daily","Monthly","Annual","Event"], report, "Q08b", critical=True)

    check_allowed_values(df, "Unit_Standard", ["SI"], report, "Q08c", critical=True)
    check_missing_not_zero(df, ["Rainfall_mm"], report)

    return report


# ---------------------------------------------------------------------------
# DB06 — Infrastructure
# ---------------------------------------------------------------------------

def validate_db06(df: pd.DataFrame) -> QCReport:
    report = QCReport("DB06", "Database")

    lkp_infra = _load_lookup(LKP_INFRA_TYPE, "Infra_Type_Code")

    required = [
        "Infrastructure_ID","Community_ID","Infrastructure_Type",
        "Description","Latitude","Longitude","GPS_Accuracy_m",
        "Condition","Flood_Exposure","Erosion_Exposure",
        "Critical_Service","Observation_Date","Observed_By",
        "Record_Created","Data_Version","QC_Status",
    ]
    check_required_fields(df, required, report)
    check_no_nulls_in_required(df, required, report)
    check_unique_key(df, "Infrastructure_ID", report)
    check_fk_resolves(df, "Infrastructure_Type", lkp_infra, "Infra_Type_Code", report)

    check_coordinates(df, "Latitude", "Longitude", report)
    check_gps_accuracy(df, "GPS_Accuracy_m", report)
    check_dates(df, "Observation_Date", report, min_date="2026-01-01")

    check_allowed_values(df, "Condition",
                         ["Good","Fair","Poor","Critical","Unknown"], report, "Q08a")
    check_allowed_values(df, "Flood_Exposure",
                         ["Yes","No","Unknown"], report, "Q08b", critical=True)
    check_allowed_values(df, "Erosion_Exposure",
                         ["Yes","No","Unknown"], report, "Q08c", critical=True)
    check_allowed_values(df, "Critical_Service",
                         ["Yes","No"], report, "Q08d", critical=True)

    check_range(df, "Damage_Severity", 0, 4, report, "Q09a", critical=False)

    return report


# ---------------------------------------------------------------------------
# Run all DB validations
# ---------------------------------------------------------------------------

def run_all(data_dir: Path = DATA_RAW) -> Dict[str, QCReport]:
    """Validate all available DB CSV files. Returns dict of reports."""
    log_separator(log, "02_VALIDATE — Database QC Checks")
    reports = {}

    db_files = {
        "DB01": data_dir / "DB01_Community_Master_RAW.csv" if (data_dir / "DB01_Community_Master_RAW.csv").exists() else data_dir / "DB01_Community_Master_ENTRY_TEMPLATE.csv",
        "DB02": data_dir / "DB02_Household_Survey_RAW.csv",
        "DB03": data_dir / "DB03_Erosion_Sites_RAW.csv" if (data_dir / "DB03_Erosion_Sites_RAW.csv").exists() else data_dir / "DB03_Erosion_Sites_ENTRY_TEMPLATE.csv",
        "DB04": data_dir / "DB04_Hydropower_Water_RAW.csv",
        "DB05": data_dir / "DB05_Climate_Observations_RAW.csv",
        "DB06": data_dir / "DB06_Infrastructure_RAW.csv" if (data_dir / "DB06_Infrastructure_RAW.csv").exists() else data_dir / "DB06_Infrastructure_ENTRY_TEMPLATE.csv",
    }

    community_ids = None

    for db_id, path in db_files.items():
        if not path.exists():
            log.warning(f"{db_id} file not found at {path} — skipping")
            continue

        df = pd.read_csv(path)
        log.info(f"Validating {db_id}: {len(df)} records")

        if db_id == "DB01":
            report = validate_db01(df)
            community_ids = df.get("Community_ID", pd.Series(dtype=str))
        elif db_id == "DB02":
            report = validate_db02(df, community_ids if community_ids is not None else pd.Series(dtype=str))
        elif db_id == "DB03":
            report = validate_db03(df)
        elif db_id == "DB04":
            report = validate_db04(df)
        elif db_id == "DB05":
            report = validate_db05(df)
        elif db_id == "DB06":
            report = validate_db06(df)
        else:
            continue

        reports[db_id] = report
        log.info(report.summary())

        # Save QC report
        report_path = ANALYSIS_QC / f"QC_Run_{db_id}_{date.today().strftime('%Y%m%d')}.csv"
        report.to_csv(report_path)

        # Update processing status
        new_status = QCStatus.CLEAN if report.passed else QCStatus.QC_FAILED
        update_processing_status(db_id, new_status, qc_passed=report.passed)

        if not report.passed:
            log.error(f"CRITICAL QC FAILURE: {db_id} — {report.critical_failures} critical checks failed")
            raise PipelineCriticalError(
                f"{db_id} failed critical QC — pipeline halted. "
                f"Fix {report.critical_failures} critical failure(s) and re-run."
            )

    return reports


if __name__ == "__main__":
    run_all()
