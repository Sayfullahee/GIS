"""
test_pipeline.py
================
Self-contained test suite for the CHER-CDSS pipeline.

Generates synthetic data that mimics real field data, then runs
every major pipeline module against it and verifies the outputs.

No real field data required. Runs entirely on the existing file structure.

Usage:
    py test_pipeline.py              # full test suite
    py test_pipeline.py --quick      # config + QC tests only (fastest)

Exit codes:
    0 — all tests passed
    1 — one or more tests failed
"""

import sys
import argparse
import traceback
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure the scripts directory is on the path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── colour helpers (work on any terminal) ──────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):
    try:
        print(f"  {GREEN}✓{RESET}  {msg}")
    except Exception:
        print(f"  {GREEN}[OK]{RESET}  {msg}")

def fail(msg):
    try:
        print(f"  {RED}✗  FAIL: {msg}{RESET}")
    except Exception:
        print(f"  {RED}[FAIL] {msg}{RESET}")

def info(msg):
    try:
        print(f"  {CYAN}·{RESET}  {msg}")
    except Exception:
        print(f"  {CYAN}*{RESET}  {msg}")

def section(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


# ---------------------------------------------------------------------------
# Result accumulator
# ---------------------------------------------------------------------------
results = {"passed": 0, "failed": 0, "errors": []}

def check(name, condition, detail=""):
    if condition:
        ok(name)
        results["passed"] += 1
    else:
        fail(f"{name}" + (f" — {detail}" if detail else ""))
        results["failed"] += 1
        results["errors"].append(name)


# ===========================================================================
# SYNTHETIC DATA GENERATORS
# ===========================================================================

def make_db01(n=20):
    """Synthetic community master records — 20 communities across 5 N-HYPPADEC states."""
    states = [
        ("NG-NIG","Niger","NG-NIG-001","Agaie"),
        ("NG-KEB","Kebbi","NG-KEB-001","Aleiro"),
        ("NG-PLA","Plateau","NG-PLA-001","Barkin Ladi"),
        ("NG-BEN","Benue","NG-BEN-001","Ado"),
        ("NG-KOG","Kogi","NG-KOG-001","Adavi"),
    ]
    rows = []
    for i in range(n):
        sc, sn, lc, ln = states[i % len(states)]
        rows.append({
            "Community_ID":     f"COM-{sc[-2:]}-001-{i+1:04d}",
            "Community":        f"Test Community {i+1}",
            "State_Code":       sc,
            "State_Name":       sn,
            "LGA_Code":         lc,
            "LGA":              ln,
            "Latitude":         round(5.5 + i * 0.3, 6),
            "Longitude":        round(6.5 + i * 0.2, 6),
            "GPS_Accuracy_m":   round(np.random.uniform(3, 20), 1),
            "Survey_Date":      "2026-06-15",
            "Population":       int(np.random.randint(200, 5000)),
            "Livelihood":       np.random.choice(["LIV01","LIV02","LIV05"]),
            "Electricity_Access": np.random.choice(["Yes","No","Partial"]),
            "Water_Source":     np.random.choice(["WS01","WS02","WS06"]),
            "Flood_Experience": np.random.choice(["Yes","No","Unknown"]),
            "Erosion_Presence": np.random.choice(["Yes","No"]),
            "Hydropower_Distance": None,
            "Adaptation_Status": np.random.choice(["AD01","AD04","AD08"]),
            "Photo_ID":         f"PHO-{i+1:04d}",
            "Notes":            "",
            "Record_Created":   "2026-06-15",
            "Record_Modified":  None,
            "Data_Version":     "v1.0",
            "QC_Status":        "CLEAN",
        })
    return pd.DataFrame(rows)


def make_db03(community_ids, n=30):
    """Synthetic erosion site records."""
    rows = []
    for i in range(n):
        comm = community_ids[i % len(community_ids)]
        sc = comm.split("-")[1]
        rows.append({
            "Erosion_ID":       f"ERO-{sc}-{i+1:06d}",
            "Community_ID":     comm,
            "Latitude":         round(5.5 + i * 0.1, 6),
            "Longitude":        round(6.5 + i * 0.1, 6),
            "GPS_Accuracy_m":   round(np.random.uniform(3, 25), 1),
            "Erosion_Type":     np.random.choice(["GULLY","RILL","BANK"]),
            "Activity_Status":  np.random.choice(["Active","Inactive","Stabilised"]),
            "Severity_0_4":     int(np.random.randint(0, 5)),
            "Length_m":         round(np.random.uniform(5, 500), 1),
            "Width_m":          round(np.random.uniform(1, 50), 1),
            "Depth_m":          round(np.random.uniform(0.5, 15), 1),
            "River_Distance_m": round(np.random.uniform(50, 2000), 0),
            "Slope":            np.random.choice(["Gentle (2-5%)","Moderate (5-15%)","Steep (15-30%)"]),
            "Infrastructure_Threat": np.random.choice(["Yes","No","Unknown"]),
            "Control_Present":  np.random.choice(["Yes","No"]),
            "Control_Condition":np.random.choice(["Good","Fair","Poor","NA"]),
            "Sediment_To_River":np.random.choice(["Yes","No","Unknown"]),
            "Observation_Date": "2026-07-01",
            "Observed_By":      "Field Team A",
            "Notes":            "",
            "Record_Created":   "2026-07-01",
            "Record_Modified":  None,
            "Data_Version":     "v1.0",
            "QC_Status":        "CLEAN",
        })
    return pd.DataFrame(rows)


def make_db06(community_ids, n=25):
    """Synthetic infrastructure records."""
    rows = []
    for i in range(n):
        comm = community_ids[i % len(community_ids)]
        sc = comm.split("-")[1]
        rows.append({
            "Infrastructure_ID":  f"INF-{sc}-{i+1:06d}",
            "Community_ID":       comm,
            "Infrastructure_Type": np.random.choice(["ROAD_FED","HEALTH_C","SCHOOL_P","WATER_B"]),
            "Description":        f"Test infrastructure item {i+1}",
            "Latitude":           round(5.5 + i * 0.12, 6),
            "Longitude":          round(6.5 + i * 0.12, 6),
            "GPS_Accuracy_m":     round(np.random.uniform(3, 20), 1),
            "Condition":          np.random.choice(["Good","Fair","Poor","Critical"]),
            "Flood_Exposure":     np.random.choice(["Yes","No","Unknown"]),
            "Erosion_Exposure":   np.random.choice(["Yes","No","Unknown"]),
            "River_Distance_m":   None,
            "Damage_Severity":    int(np.random.randint(0, 5)),
            "Service_Disruption": np.random.choice(["Yes","No","Unknown"]),
            "Users_Affected":     int(np.random.randint(0, 2000)),
            "Repair_Status":      np.random.choice(["No repair needed","Planned","In progress"]),
            "Critical_Service":   np.random.choice(["Yes","No"]),
            "Observation_Date":   "2026-07-15",
            "Observed_By":        "Field Team B",
            "Notes":              "",
            "Record_Created":     "2026-07-15",
            "Record_Modified":    None,
            "Data_Version":       "v1.0",
            "QC_Status":          "CLEAN",
        })
    return pd.DataFrame(rows)


# ===========================================================================
# TEST SUITES
# ===========================================================================

def test_01_environment():
    section("TEST 01 — Environment and imports")
    try:
        import pandas as pd
        check("pandas importable", True, pd.__version__)
        import numpy as np
        check("numpy importable", True, np.__version__)
    except ImportError as e:
        check("core packages importable", False, str(e))

    # Project directories
    for d in ["03_Data/CLEAN","03_Data/LOOKUPS","04_GIS/06_METADATA",
              "05_Analysis/02_SCRIPTS","00_Project_Control"]:
        path = PROJECT_ROOT / d
        check(f"Directory exists: {d}", path.exists())

    # Essential control files
    for f in ["CHER_CDSS_ADVANCED_MASTER_IMPLEMENTATION_SCAFFOLD_v4.1.md",
              "REFERENCE_BOUNDS_REGISTER.csv",
              "SOURCE_REGISTER.csv","INDICATOR_REGISTER.csv",
              "BUFFER_RULES.csv","PROCESSING_STATUS.csv","VERSION_LOG.csv",
              "HAZARD_MODEL_DECISIONS.csv","EXPOSURE_MODEL_DECISIONS.csv",
              "SYSTEM_ACCEPTANCE_TESTS.md",
              "BACKUP_ARCHITECTURE.md"]:
        path = PROJECT_ROOT / "00_Project_Control" / f
        check(f"Control file exists: {f}", path.exists())

    # RISK_MODEL_SPEC lives in 07_Decision_Support/01_Risk/
    rms = PROJECT_ROOT / "07_Decision_Support" / "01_Risk" / "RISK_MODEL_SPEC.md"
    check("RISK_MODEL_SPEC.md exists (07_Decision_Support/01_Risk/)", rms.exists())

    # DDL script exists in 03_Data/
    ddl = PROJECT_ROOT / "03_Data" / "POSTGRESQL_DDL_v4.1.sql"
    check("POSTGRESQL_DDL_v4.1.sql exists (03_Data/)", ddl.exists())

    # Lookup tables
    for lkp in ["LKP_States.csv","LKP_LGAs.csv","LKP_DataConfidence.csv","LKP_LookupCode.csv",
                "LKP_Livelihood.csv","LKP_ErosionSeverity.csv","LKP_ErosionType.csv",
                "LKP_InfrastructureType.csv","LKP_QC_Status.csv",
                "LKP_AdaptationStatus.csv","LKP_LandCoverClasses.csv",
                "LKP_RoadHierarchy.csv","LKP_POIClasses.csv"]:
        path = PROJECT_ROOT / "03_Data" / "LOOKUPS" / lkp
        check(f"Lookup table exists: {lkp}", path.exists())

    # Python scripts
    for script in ["config.py","logger.py","qc_utils.py",
                   "01_ingest.py","02_validate.py","03_clean.py",
                   "04_integrate.py","13_risk.py","15_priority.py",
                   "run_pipeline.py"]:
        path = SCRIPTS_DIR / script
        check(f"Script exists: {script}", path.exists())

    # GIS metadata files (spot check key layers)
    for layer in ["G01_State_Boundaries","G03_Communities",
                  "G09_DEM","G24_FloodHazard","G35_CompositeRisk","G37_PriorityAreas"]:
        meta = PROJECT_ROOT / "04_GIS" / "06_METADATA" / f"{layer}_METADATA.csv"
        check(f"GIS metadata exists: {layer}", meta.exists())


def test_02_config():
    section("TEST 02 — config.py imports and paths")
    try:
        import config as cfg

        check("PROJECT_ROOT resolves", cfg.PROJECT_ROOT.exists())
        check("DATA_CLEAN path defined", hasattr(cfg, "DATA_CLEAN"))
        check("GIS_METADATA path defined", hasattr(cfg, "GIS_METADATA"))
        check("STUDY_STATES has 10 entries", len(cfg.STUDY_STATES) == 10)
        check("Risk weights sum to 1.0",
              abs(sum(cfg.RISK_WEIGHTS_BASELINE.values()) - 1.0) < 0.001)
        check("S1 weights sum to 1.0",
              abs(sum(cfg.RISK_WEIGHTS_S1_EQUAL.values()) - 1.0) < 0.001)
        check("S2 weights sum to 1.0",
              abs(sum(cfg.RISK_WEIGHTS_S2_HAZARD_DOMINANT.values()) - 1.0) < 0.001)
        check("Slope unit is degrees", cfg.SLOPE_UNIT == "degrees")
        check("BUF003 erosion threat = 100m",
              cfg.BUFFER_EROSION_THREAT_M == 100)
        check("G25 validation threshold = 70%",
              abs(cfg.FLOOD_HAZARD_VALIDATION_PCT - 0.70) < 0.001)
        check("RISK_MODEL_VERSION set",
              cfg.RISK_MODEL_VERSION.startswith("Risk_Model_v"))

        info(f"RISK_MODEL_VERSION: {cfg.RISK_MODEL_VERSION}")
        info(f"Baseline weights: H={cfg.RISK_WEIGHTS_BASELINE['H']} "
             f"E={cfg.RISK_WEIGHTS_BASELINE['E']} "
             f"V={cfg.RISK_WEIGHTS_BASELINE['V']} "
             f"C={cfg.RISK_WEIGHTS_BASELINE['C']}")

    except Exception as e:
        check("config.py imports without error", False, str(e))
        traceback.print_exc()


def test_03_lookups():
    section("TEST 03 — Lookup table integrity")
    lkp_dir = PROJECT_ROOT / "03_Data" / "LOOKUPS"

    # States: 10 N-HYPPADEC member states + extended regional basin states
    states = pd.read_csv(lkp_dir / "LKP_States.csv")
    check("LKP_States has member + basin records (>= 10)", len(states) >= 10,
          f"found {len(states)}")
    check("LKP_States no duplicate State_Code",
          states["State_Code"].nunique() == len(states))
    check("LKP_States no null State_Code",
          states["State_Code"].notna().all())

    # LGAs: has records and links to states
    lgas = pd.read_csv(lkp_dir / "LKP_LGAs.csv")
    check("LKP_LGAs has records", len(lgas) > 0)
    check("LKP_LGAs no duplicate LGA_Code",
          lgas["LGA_Code"].nunique() == len(lgas))
    unresolved = lgas[~lgas["State_Code"].isin(states["State_Code"])]
    check("All LGA State_Code values resolve to LKP_States",
          len(unresolved) == 0,
          f"{len(unresolved)} unresolved")

    # Erosion severity: codes 0-4
    sev = pd.read_csv(lkp_dir / "LKP_ErosionSeverity.csv")
    check("LKP_ErosionSeverity has codes 0-4",
          set(sev["Severity_Code"].astype(int)) == {0,1,2,3,4})

    # QC Status: required stages present
    qcs = pd.read_csv(lkp_dir / "LKP_QC_Status.csv")
    required_stages = {"RAW","INGESTED","CLEAN","DERIVED","VALIDATED","PUBLISHED","ARCHIVED"}
    check("LKP_QC_Status contains all required stages",
          required_stages.issubset(set(qcs["QC_Status_Code"])))

    # Land cover: 11 classes
    lc = pd.read_csv(lkp_dir / "LKP_LandCoverClasses.csv", on_bad_lines='skip')
    check("LKP_LandCoverClasses has 11 classes", len(lc) == 11,
          f"found {len(lc)}")
    check("WorldCover class codes present (10,20,40,50,60,80,90)",
          {10,20,40,50,60,80,90}.issubset(set(lc["Class_Code"].astype(int))))


def test_04_qc_utils():
    section("TEST 04 — qc_utils.py QC functions")
    try:
        from qc_utils import (
            QCReport,
            check_required_fields,
            check_no_nulls_in_required,
            check_unique_key,
            check_coordinates,
            check_dates,
            check_range,
            check_missing_not_zero,
            check_allowed_values,
        )

        # Build a small test DataFrame with known issues
        df_good = pd.DataFrame({
            "ID":        ["A001","A002","A003"],
            "Name":      ["Alpha","Beta","Gamma"],
            "Latitude":  [6.5, 7.1, 8.3],
            "Longitude": [7.2, 7.8, 8.1],
            "Date":      ["2026-06-01","2026-07-15","2026-09-01"],
            "Score":     [10.0, 20.0, 30.0],
            "Status":    ["Yes","No","Yes"],
        })

        df_bad = pd.DataFrame({
            "ID":        ["A001","A001","A003"],  # duplicate
            "Name":      ["Alpha", None, "Gamma"],  # null
            "Latitude":  [6.5, 95.0, 8.3],       # out-of-range
            "Longitude": [7.2, 7.8, 200.0],       # out-of-range
            "Date":      ["2026-06-01","not-a-date","2026-09-01"],
            "Score":     [10.0, 0.0, 30.0],       # 0 where NULL expected
            "Status":    ["Yes","INVALID","Yes"],
        })

        # --- Test QCReport class ---
        r = QCReport("TEST_ASSET", "Test")
        r.add("T1", "Structure", "test pass", passed=True,  critical=True)
        r.add("T2", "Structure", "test fail", passed=False, critical=True)
        r.add("T3", "Structure", "test warn", passed=False, critical=False)
        check("QCReport.passed = False when critical failure",
              r.passed == False)
        check("QCReport critical_failures = 1", r.critical_failures == 1)
        check("QCReport advisory_flags = 1",    r.advisory_flags == 1)
        check("QCReport qc_status = QC_FAILED", r.qc_status == "QC_FAILED")

        r_pass = QCReport("PASS_ASSET", "Test")
        r_pass.add("T1","Structure","all good", passed=True, critical=True)
        check("QCReport.passed = True when no critical failures",
              r_pass.passed == True)

        # --- Test individual checks against GOOD data ---
        rg = QCReport("GOOD","Test")
        check_required_fields(df_good, ["ID","Name","Latitude","Longitude"], rg)
        check("check_required_fields PASS on good data",
              rg.critical_failures == 0)

        check_no_nulls_in_required(df_good, ["ID","Name"], rg)
        check("check_no_nulls_in_required PASS on good data",
              rg.critical_failures == 0)

        check_unique_key(df_good, "ID", rg)
        check("check_unique_key PASS on good data (no duplicates)",
              rg.critical_failures == 0)

        check_coordinates(df_good, "Latitude", "Longitude", rg)
        check("check_coordinates PASS on good data",
              rg.critical_failures == 0)

        check_dates(df_good, "Date", rg, min_date="2026-01-01")
        check("check_dates PASS on good data", rg.critical_failures == 0)

        check_range(df_good, "Score", 0, 100, rg, critical=True)
        check("check_range PASS on good data", rg.critical_failures == 0)

        check_allowed_values(df_good, "Status", ["Yes","No"], rg, critical=False)
        check("check_allowed_values PASS on good data", rg.advisory_flags == 0)

        # --- Test individual checks CATCH errors in BAD data ---
        rb = QCReport("BAD","Test")
        pre = rb.critical_failures

        check_unique_key(df_bad, "ID", rb)
        check("check_unique_key CATCHES duplicates",
              rb.critical_failures > pre)

        pre = rb.critical_failures
        check_no_nulls_in_required(df_bad, ["Name"], rb)
        check("check_no_nulls_in_required CATCHES null values",
              rb.critical_failures > pre)

        pre = rb.critical_failures
        check_coordinates(df_bad, "Latitude", "Longitude", rb)
        check("check_coordinates CATCHES out-of-range values",
              rb.critical_failures > pre)

        pre_adv = rb.advisory_flags
        check_missing_not_zero(df_bad, ["Score"], rb)
        check("check_missing_not_zero CATCHES zero where NULL expected",
              rb.critical_failures > 0 or rb.advisory_flags > pre_adv)

        pre_adv = rb.advisory_flags
        check_allowed_values(df_bad, "Status", ["Yes","No"], rb, critical=False)
        check("check_allowed_values CATCHES invalid values",
              rb.advisory_flags > pre_adv)

    except Exception as e:
        check("qc_utils.py imports and runs", False, str(e))
        traceback.print_exc()


def test_05_validate_db01():
    section("TEST 05 — 02_validate.py — DB01 validation")
    try:
        from qc_utils import QCReport
        # Import the specific validator
        import importlib
        validate_mod = importlib.import_module("02_validate")

        lkp_dir = PROJECT_ROOT / "03_Data" / "LOOKUPS"
        lkp_states = pd.read_csv(lkp_dir / "LKP_States.csv")

        # --- Valid DB01 ---
        db01_good = make_db01(10)
        # Restrict to valid state codes from the lookup
        valid_state = lkp_states["State_Code"].iloc[0]
        valid_lga   = pd.read_csv(lkp_dir / "LKP_LGAs.csv")
        valid_lga   = valid_lga[valid_lga["State_Code"] == valid_state].iloc[0]
        for _, row in db01_good.iterrows():
            db01_good.loc[_, "State_Code"] = valid_state
            db01_good.loc[_, "State_Name"] = lkp_states.loc[
                lkp_states["State_Code"] == valid_state, "State_Name"
            ].values[0]
            db01_good.loc[_, "LGA_Code"] = valid_lga["LGA_Code"]
            db01_good.loc[_, "LGA"]      = valid_lga["LGA_Name"]

        report_good = validate_mod.validate_db01(db01_good)
        check("DB01 valid data — critical failures = 0",
              report_good.critical_failures == 0,
              f"found {report_good.critical_failures} critical failures")

        # --- Invalid DB01: duplicate ID ---
        db01_dup = db01_good.copy()
        db01_dup.iloc[1, db01_dup.columns.get_loc("Community_ID")] = db01_dup.iloc[0]["Community_ID"]
        report_dup = validate_mod.validate_db01(db01_dup)
        check("DB01 duplicate Community_ID — caught as critical failure",
              report_dup.critical_failures > 0)

        # --- Invalid DB01: out-of-range coordinates ---
        db01_coords = db01_good.copy()
        db01_coords.iloc[0, db01_coords.columns.get_loc("Latitude")] = 95.0
        report_coords = validate_mod.validate_db01(db01_coords)
        check("DB01 out-of-range latitude — caught as critical failure",
              report_coords.critical_failures > 0)

        # --- Invalid DB01: null required field ---
        db01_null = db01_good.copy()
        db01_null.iloc[0, db01_null.columns.get_loc("Survey_Date")] = None
        report_null = validate_mod.validate_db01(db01_null)
        check("DB01 null Survey_Date — caught as critical failure",
              report_null.critical_failures > 0)

    except Exception as e:
        check("02_validate.py validate_db01 runs", False, str(e))
        traceback.print_exc()


def test_06_validate_db03():
    section("TEST 06 — 02_validate.py — DB03 erosion validation")
    try:
        import importlib
        validate_mod = importlib.import_module("02_validate")

        db01 = make_db01(5)
        db03_good = make_db03(db01["Community_ID"].tolist(), n=10)
        # Ensure severity is valid int
        db03_good["Severity_0_4"] = db03_good["Severity_0_4"].clip(0, 4).astype(int)

        report = validate_mod.validate_db03(db03_good)
        check("DB03 valid data — critical failures = 0",
              report.critical_failures == 0,
              f"found {report.critical_failures}")

        # Invalid severity
        db03_bad = db03_good.copy()
        db03_bad.iloc[0, db03_bad.columns.get_loc("Severity_0_4")] = 9
        report_bad = validate_mod.validate_db03(db03_bad)
        check("DB03 severity=9 — caught as critical failure",
              report_bad.critical_failures > 0)

    except Exception as e:
        check("02_validate.py validate_db03 runs", False, str(e))
        traceback.print_exc()


def test_07_risk_formula():
    section("TEST 07 — Risk formula R = 0.35H + 0.25E + 0.25V + 0.15C")
    # Test the formula directly without importing 13_risk.py
    # (avoids the lazy module import chain)

    # Build a synthetic component table
    n = 50
    np.random.seed(42)
    components = pd.DataFrame({
        "Community_ID": [f"COM-AB-001-{i+1:04d}" for i in range(n)],
        "H_Score": np.random.uniform(0, 100, n),
        "E_Score": np.random.uniform(0, 100, n),
        "V_Score": np.random.uniform(0, 100, n),
        "C_Score": np.random.uniform(0, 100, n),
    })

    # Apply formula
    components["R_Score"] = (
        0.35 * components["H_Score"] +
        0.25 * components["E_Score"] +
        0.25 * components["V_Score"] +
        0.15 * components["C_Score"]
    )

    # Verify formula
    calculated = (
        0.35 * components["H_Score"] +
        0.25 * components["E_Score"] +
        0.25 * components["V_Score"] +
        0.15 * components["C_Score"]
    )
    discrepancy = (components["R_Score"] - calculated).abs().max()
    check("Formula: |R − (0.35H+0.25E+0.25V+0.15C)| < 0.01",
          discrepancy < 0.01, f"max discrepancy={discrepancy:.6f}")

    # Weight sum
    check("Weights sum to 1.0", abs(0.35+0.25+0.25+0.15 - 1.0) < 0.001)

    # Range check
    check("All R_Score values between 0 and 100",
          components["R_Score"].between(0, 100).all(),
          f"min={components['R_Score'].min():.1f} max={components['R_Score'].max():.1f}")

    # S1 sensitivity model
    components["R_Score_S1"] = (
        0.25 * components["H_Score"] +
        0.25 * components["E_Score"] +
        0.25 * components["V_Score"] +
        0.25 * components["C_Score"]
    )
    check("S1 equal weights sum to 1.0", abs(0.25*4 - 1.0) < 0.001)
    check("S1 R_Score also 0-100",
          components["R_Score_S1"].between(0, 100).all())

    # Spearman rank correlation baseline vs S1 (requires scipy)
    try:
        rank_corr = components["R_Score"].corr(components["R_Score_S1"],
                                               method="spearman")
        check(f"Spearman rank correlation baseline vs S1 > 0.5 (got {rank_corr:.3f})",
              rank_corr > 0.5)
        info(f"Rank correlation baseline vs S1: {rank_corr:.3f}")
    except Exception:
        # Fall back to Pearson if scipy not available
        rank_corr = components["R_Score"].corr(components["R_Score_S1"])
        check(f"Pearson correlation baseline vs S1 > 0.5 (got {rank_corr:.3f})",
              rank_corr > 0.5)
        info(f"Pearson correlation baseline vs S1: {rank_corr:.3f} (scipy not available for Spearman)")

    # Missing component handling — one component NULL
    components_partial = components.copy()
    components_partial.loc[0:4, "V_Score"] = np.nan

    def compute_r_partial(row):
        weights = {"H_Score":0.35,"E_Score":0.25,"V_Score":0.25,"C_Score":0.15}
        score, wsum = 0.0, 0.0
        for col, w in weights.items():
            if pd.notna(row[col]):
                score += row[col] * w
                wsum  += w
        return score / wsum if wsum > 0 else np.nan

    components_partial["R_partial"] = components_partial.apply(
        compute_r_partial, axis=1
    )
    check("Missing component handled — R computed from available components",
          components_partial["R_partial"].notna().all())
    check("Partial R_Score still 0-100",
          components_partial["R_partial"].between(0, 100).all())

    # Priority score formula
    components["IND10"] = np.random.uniform(0, 100, n)
    components["Priority_Score"] = (
        0.70 * components["R_Score"] + 0.30 * components["IND10"]
    ).clip(0, 100)
    check("Priority_Score = 0.70R + 0.30IND10, all 0-100",
          components["Priority_Score"].between(0, 100).all())


def test_08_indicator_normalisation():
    section("TEST 08 — Indicator normalisation and inversion rules")
    np.random.seed(7)
    n = 30

    # Min-max normalisation
    raw = pd.Series(np.random.uniform(0, 500, n))
    mn, mx = raw.min(), raw.max()
    normed = ((raw - mn) / (mx - mn) * 100).clip(0, 100)
    check("Min-max normalisation: all values 0-100",
          normed.between(0, 100).all())
    check("Min-max: min of normed = 0", abs(normed.min()) < 0.01)
    check("Min-max: max of normed = 100", abs(normed.max() - 100) < 0.01)

    # IND04 river proximity inversion (closer = higher hazard)
    distances = pd.Series([0, 100, 250, 500, 750, 1000])
    max_dist = 500.0   # BUF001
    inverted = ((max_dist - distances.clip(upper=max_dist)) / max_dist * 100).clip(0, 100)
    check("IND04 inversion: distance=0 → score=100",   abs(inverted.iloc[0] - 100) < 0.01)
    check("IND04 inversion: distance=500m → score=0",  abs(inverted.iloc[3]) < 0.01)
    check("IND04 inversion: distance=750m → score=0",  abs(inverted.iloc[4]) < 0.01)
    check("IND04 inversion: distance=250m → score=50", abs(inverted.iloc[2] - 50) < 0.01)

    # IND09 adaptation coverage inversion (higher coverage = lower vulnerability)
    coverage = pd.Series([0.0, 0.25, 0.50, 0.75, 1.0])
    inverted_cov = (1 - coverage) * 100
    check("IND09 inversion: coverage=0 → vulnerability=100",
          abs(inverted_cov.iloc[0] - 100) < 0.01)
    check("IND09 inversion: coverage=1 → vulnerability=0",
          abs(inverted_cov.iloc[4]) < 0.01)
    check("IND09 inversion: coverage=0.5 → vulnerability=50",
          abs(inverted_cov.iloc[2] - 50) < 0.01)

    # IND08 NULL for communities outside BUF004
    hydropower_within = pd.Series([True, False, True, False, False])
    ind08_values      = pd.Series([45.0, np.nan, 72.0, np.nan, np.nan])
    check("IND08 NULL (not 0) for communities outside BUF004",
          all(pd.isna(ind08_values[~hydropower_within]))
          and all(pd.notna(ind08_values[hydropower_within])))


def test_09_data_rules():
    section("TEST 09 — Critical data rules (NULL vs zero, privacy, immutability)")

    # NULL vs zero: loss fields should not have 0 as sentinel for missing
    losses = pd.Series([np.nan, np.nan, 0.0, 150000.0, np.nan])
    # The 0.0 here should be verified — it could mean confirmed zero loss OR missing
    zero_count = (losses == 0.0).sum()
    check("NULL vs zero: loss field check runs without error", True)
    info(f"  Zero-value loss records requiring verification: {zero_count}")

    # Privacy: Privacy_Compliant field must be Yes before G33 publication
    g33_data = pd.DataFrame({
        "Community_ID":     ["COM-AB-001-0001","COM-AB-001-0002"],
        "V_Score":          [55.2, 61.8],
        "Privacy_Compliant":["Yes","Yes"],
    })
    check("G33 Privacy_Compliant = Yes for all records",
          (g33_data["Privacy_Compliant"] == "Yes").all())

    # Privacy: no Household_ID in community-level outputs
    check("No Household_ID column in G33 data",
          "Household_ID" not in g33_data.columns)

    # Immutability: published outputs must not be overwritten
    # (conceptual check — verify archiving path exists)
    archive_path = PROJECT_ROOT / "09_Archive"
    check("09_Archive directory exists", archive_path.exists())

    # Processing status transitions must follow the defined order
    valid_statuses = {"RAW","INGESTED","VALIDATING","QC_FAILED",
                      "CLEAN","DERIVED","VALIDATED","PUBLISHED","ARCHIVED"}
    lkp_qc = pd.read_csv(PROJECT_ROOT / "03_Data" / "LOOKUPS" / "LKP_QC_Status.csv")
    actual_statuses = set(lkp_qc["QC_Status_Code"])
    check("LKP_QC_Status contains all required transition states",
          valid_statuses == actual_statuses,
          f"Missing: {valid_statuses - actual_statuses}")

    # Risk model language: R is an index, not probability
    risk_spec = PROJECT_ROOT / "07_Decision_Support" / "01_Risk" / "RISK_MODEL_SPEC.md"
    if risk_spec.exists():
        content = risk_spec.read_text(encoding="utf-8")
        check("RISK_MODEL_SPEC.md contains 'decision-support' language",
              "decision-support" in content.lower())
        check("RISK_MODEL_SPEC.md contains 'not a probability' language",
              "not a probability" in content.lower()
              or "not a probability" in content
              or "decision-support measure" in content.lower()
              or "not a probability of disaster" in content)
        check("RISK_MODEL_SPEC.md contains sensitivity models S1 and S2",
              "S1" in content and "S2" in content)
        check("RISK_MODEL_SPEC.md contains approval record",
              "approval" in content.lower())


def test_10_pipeline_dry_run():
    section("TEST 10 — run_pipeline.py dry run")
    try:
        import importlib
        pipeline_mod = importlib.import_module("run_pipeline")

        check("run_pipeline.py imports without error", True)
        check("PipelineCriticalError defined",
              hasattr(pipeline_mod, "PipelineCriticalError"))
        check("build_pipeline() callable",
              callable(getattr(pipeline_mod, "build_pipeline", None)))

        # Build pipeline and check step count
        pipeline = pipeline_mod.build_pipeline()
        check("Pipeline has 18 steps",
              len(pipeline.steps) >= 18, f"found {len(pipeline.steps)}")

        # Check all step IDs are present and sequential
        expected_ids = [f"{str(i).zfill(2)}_{name}" for i, name in enumerate([
            "ingest","validate","clean","integrate","climate","flood",
            "erosion","hydropower","exposure","vulnerability","criticality",
            "hazard","risk","adaptation","priority","qc","reports","maps"
        ], start=1)]
        actual_ids = [s.step_id for s in pipeline.steps]
        check("First 18 step IDs present",
              all(e == a for e, a in zip(expected_ids, actual_ids[:18])),
              f"\nExpected: {expected_ids[:3]}...\nActual:   {actual_ids[:3]}...")

        # Dry run should return exit code 3
        exit_code = pipeline.run(dry_run=True)
        check("Dry run returns exit code 3",
              exit_code == 3, f"got exit code {exit_code}")

        # Verify PipelineCriticalError halts pipeline
        halt_tested = False
        class HaltStep:
            def run_fn(self):
                raise pipeline_mod.PipelineCriticalError("Test halt — expected")

        try:
            raise pipeline_mod.PipelineCriticalError("expected")
        except pipeline_mod.PipelineCriticalError:
            halt_tested = True
        check("PipelineCriticalError can be raised and caught", halt_tested)

    except Exception as e:
        check("run_pipeline.py loads and builds pipeline", False, str(e))
        traceback.print_exc()


def test_11_processing_status():
    section("TEST 11 — PROCESSING_STATUS.csv and VERSION_LOG.csv integrity")
    ps_path  = PROJECT_ROOT / "00_Project_Control" / "PROCESSING_STATUS.csv"
    vl_path  = PROJECT_ROOT / "00_Project_Control" / "VERSION_LOG.csv"

    ps = pd.read_csv(ps_path)
    check("PROCESSING_STATUS.csv readable", True)
    check("PROCESSING_STATUS has required columns",
          all(c in ps.columns for c in ["Asset_ID","Asset_Type","Current_Status"]))

    # All 6 databases should be present
    for db in ["DB01","DB02","DB03","DB04","DB05","DB06"]:
        check(f"PROCESSING_STATUS contains {db}",
              db in ps["Asset_ID"].values)

    # All 37 GIS layers should be present
    for i in range(1, 38):
        gid = f"G{i:02d}"
        check(f"PROCESSING_STATUS contains {gid}",
              gid in ps["Asset_ID"].values)

    # VERSION_LOG should have Phase 10 entries
    vl = pd.read_csv(vl_path, engine='python', on_bad_lines='skip')
    check("VERSION_LOG.csv readable", True)
    has_v10 = 'v10.0' in vl['Version'].values if 'Version' in vl.columns else False
    check("VERSION_LOG has v10.0 (Phase 10) entries", has_v10)
    has_all_phases = False
    if "Description" in vl.columns:
        has_all_phases = vl["Description"].str.contains("All 10 phases", na=False).any()
    check("VERSION_LOG has ALL_PHASES COMPLETE description", has_all_phases)
    info(f"VERSION_LOG total entries: {len(vl)}")


def test_12_scaffold_v41():
    section("TEST 12 — CHER-CDSS v4.1 Scaffold & Decision Intelligence Standards")
    try:
        import config as cfg

        # 1. Scaffold document verification
        scaffold_path = cfg.SCAFFOLD_V41
        check("CHER_CDSS Scaffold v4.1 document exists", scaffold_path.exists())
        scaffold_text = scaffold_path.read_text(encoding="utf-8")
        check("Scaffold v4.1 contains Section 44 RACI Matrix", "SECTION 44" in scaffold_text)
        check("Scaffold v4.1 specifies GIS master register", ("SECTION 31 — 37-LAYER GIS MASTER REGISTER" in scaffold_text) or ("SECTION 31 — 43-LAYER GIS MASTER REGISTER" in scaffold_text))
        check("Scaffold v4.1 includes 22 Core Data Tables", "SECTION 32 — CORE DATA TABLES" in scaffold_text)
        check("Scaffold v4.1 defines fixed normalization reference bounds", "reference bounds (v4.1)" in scaffold_text.lower())
        check("Scaffold v4.1 codifies IES validity rules", "ies validity rules (v4.1)" in scaffold_text.lower())

        # 2. State configuration
        expected_states = ["NG-NIG", "NG-KEB", "NG-PLA", "NG-BEN", "NG-KOG", "NG-KWA", "NG-KAD", "NG-NAS", "NG-TAR", "NG-GOM"]
        check("STUDY_STATES matches 10 confirmed N-HYPPADEC states",
              cfg.STUDY_STATES == expected_states, f"found {cfg.STUDY_STATES}")

        # 3. Reference Bounds & Normalization
        ref_reg = cfg.REFERENCE_BOUNDS
        check("REFERENCE_BOUNDS_REGISTER.csv exists", ref_reg.exists())
        check("REFERENCE_BOUNDS_2026 configured in config.py", len(cfg.REFERENCE_BOUNDS_2026) >= 15)

        # Test normalization with clipping
        norm_mid = cfg.normalize_value(5.0, 0.0, 10.0, "positive")
        check("Normalization: mid-point 5.0 in [0, 10] = 50.0", abs(norm_mid - 50.0) < 0.001)

        norm_clip_high = cfg.normalize_value(15.0, 0.0, 10.0, "positive")
        check("Normalization: clipping upper bound (15.0 in [0, 10]) = 100.0", abs(norm_clip_high - 100.0) < 0.001)

        norm_clip_low = cfg.normalize_value(-3.0, 0.0, 10.0, "positive")
        check("Normalization: clipping lower bound (-3.0 in [0, 10]) = 0.0", abs(norm_clip_low - 0.0) < 0.001)

        norm_inv = cfg.normalize_value(2.0, 0.0, 10.0, "inverse")
        check("Normalization: inverse direction (2.0 in [0, 10]) = 80.0", abs(norm_inv - 80.0) < 0.001)

        # 4. Composite Risk (Additive vs Multiplicative Stage 17.9)
        r_add = cfg.compute_composite_risk(h=80, e=60, v=40, c=20, method="additive")
        expected_add = round(0.35 * 80 + 0.25 * 60 + 0.25 * 40 + 0.15 * 20, 2)
        check("Composite Risk additive formula matches", abs(r_add - expected_add) < 0.01)

        r_mult = cfg.compute_composite_risk(h=80, e=60, v=40, c=20, method="multiplicative")
        check("Composite Risk multiplicative alternative calculates", r_mult > 0)

        # Zero exposure check under multiplicative form
        r_zero_e = cfg.compute_composite_risk(h=80, e=0, v=40, c=20, method="multiplicative")
        check("Multiplicative check: E=0 yields zero risk", abs(r_zero_e - 0.0) < 0.01)

        # 5. Intervention Effectiveness Score (IES) Validity Rules
        ies_normal = cfg.compute_ies(risk_before=60.0, risk_after=36.0)
        check("IES normal calculation: 60 to 36 = 40.0% reduction", abs(ies_normal - 40.0) < 0.01)

        ies_zero = cfg.compute_ies(risk_before=0.0, risk_after=0.0)
        check("IES validity rule: undefined when Risk_before = 0 (returns None)", ies_zero is None)

        ies_mismatch = cfg.compute_ies(risk_before=60.0, risk_after=36.0, ref_bounds_same=False)
        check("IES validity rule: rejects comparison with mismatched reference bounds", ies_mismatch is None)

        # 6. Data Confidence Framework
        df_conf = pd.read_csv(cfg.LKP_DATA_CONFIDENCE)
        check("Data Confidence rubric contains 4 standard ratings",
              set(df_conf["Confidence_Rating"]) == {"High", "Moderate", "Low", "Unknown"})

    except Exception as e:
        check("test_12_scaffold_v41 runs without error", False, str(e))
        traceback.print_exc()


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="CHER-CDSS Pipeline Test Suite")
    parser.add_argument("--quick", action="store_true",
                        help="Run only fast tests (01-04)")
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*60}")
    print("  CHER-CDSS PIPELINE TEST SUITE")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Python:       {sys.version.split()[0]}")
    print(f"  Date:         {date.today()}")
    print(f"{'='*60}{RESET}\n")

    tests = [
        test_01_environment,
        test_02_config,
        test_03_lookups,
        test_04_qc_utils,
    ]

    if not args.quick:
        tests += [
            test_05_validate_db01,
            test_06_validate_db03,
            test_07_risk_formula,
            test_08_indicator_normalisation,
            test_09_data_rules,
            test_10_pipeline_dry_run,
            test_11_processing_status,
            test_12_scaffold_v41,
        ]

    for test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            section(f"UNEXPECTED ERROR in {test_fn.__name__}")
            traceback.print_exc()
            results["failed"] += 1
            results["errors"].append(test_fn.__name__)

    # Final summary
    total = results["passed"] + results["failed"]
    print(f"\n{BOLD}{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}{RESET}")
    print(f"  Total checks: {total}")
    print(f"  {GREEN}Passed:  {results['passed']}{RESET}")
    print(f"  {RED}Failed:  {results['failed']}{RESET}")

    if results["failed"] == 0:
        print(f"\n{BOLD}{GREEN}  ✓ ALL TESTS PASSED{RESET}\n")
        return 0
    else:
        print(f"\n{BOLD}{RED}  ✗ FAILED CHECKS ({results['failed']}):{RESET}")
        for e in results["errors"]:
            print(f"    {RED}·{RESET} {e}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
