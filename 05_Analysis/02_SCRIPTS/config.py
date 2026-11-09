"""
config.py
=========
Central configuration for the N-HYPPADEC CHER-CDSS Decision-Support Pipeline.
Updated for CHER-CDSS Master Implementation Scaffold v4.1 (October 2026).
All paths, constants, model parameters, and reference bounds are defined here.
Do NOT hardcode paths or reference bounds in individual processing modules.
"""

import sys
import os
from pathlib import Path

# Fix Windows console UTF-8 encoding if needed
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Root directories
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(os.environ.get("GIS_PROJECT_ROOT", Path(__file__).resolve().parent.parent.parent))

FIELDWORK_DIR   = PROJECT_ROOT / "02_Fieldwork"
KOBO_STAGING_DIR = FIELDWORK_DIR / "staging"
KOBO_SUBMISSIONS_LANDING = KOBO_STAGING_DIR / "kobo_submissions_landing.csv"
KOBO_QUARANTINE_LOG      = KOBO_STAGING_DIR / "kobo_quarantine_log.csv"
KOBO_SYNC_LOG            = KOBO_STAGING_DIR / "kobo_sync_history.json"

DATA_RAW        = PROJECT_ROOT / "03_Data" / "RAW"
DATA_CLEAN      = PROJECT_ROOT / "03_Data" / "CLEAN"
DATA_DERIVED    = PROJECT_ROOT / "03_Data" / "DERIVED"
DATA_LOOKUPS    = PROJECT_ROOT / "03_Data" / "LOOKUPS"


GIS_RAW         = PROJECT_ROOT / "04_GIS" / "01_RAW"
GIS_CLEAN       = PROJECT_ROOT / "04_GIS" / "02_CLEAN"
GIS_DERIVED     = PROJECT_ROOT / "04_GIS" / "03_DERIVED"
GIS_PROJECTS    = PROJECT_ROOT / "04_GIS" / "04_PROJECTS"
GIS_MAPS        = PROJECT_ROOT / "04_GIS" / "05_MAP_EXPORTS"
GIS_METADATA    = PROJECT_ROOT / "04_GIS" / "06_METADATA"

ANALYSIS_INPUTS  = PROJECT_ROOT / "05_Analysis" / "01_INPUTS"
ANALYSIS_SCRIPTS = PROJECT_ROOT / "05_Analysis" / "02_SCRIPTS"
ANALYSIS_OUTPUTS = PROJECT_ROOT / "05_Analysis" / "03_OUTPUTS"
ANALYSIS_QC      = PROJECT_ROOT / "05_Analysis" / "04_QC"

REPORTS_DRAFTS  = PROJECT_ROOT / "06_Reports" / "01_DRAFTS"
REPORTS_TABLES  = PROJECT_ROOT / "06_Reports" / "02_TABLES"
REPORTS_FIGURES = PROJECT_ROOT / "06_Reports" / "03_FIGURES"
REPORTS_FINAL   = PROJECT_ROOT / "06_Reports" / "04_FINAL"

DECISION_RISK     = PROJECT_ROOT / "07_Decision_Support" / "01_Risk"
DECISION_DASH     = PROJECT_ROOT / "07_Decision_Support" / "02_Dashboards"
DECISION_PRIORITY = PROJECT_ROOT / "07_Decision_Support" / "03_Priority_Areas"

UPDATES_DIR = PROJECT_ROOT / "08_Updates"
ARCHIVE_DIR = PROJECT_ROOT / "09_Archive"

PROJECT_CONTROL = PROJECT_ROOT / "00_Project_Control"

# ---------------------------------------------------------------------------
# Control files
# ---------------------------------------------------------------------------
SCAFFOLD_V41        = PROJECT_CONTROL / "CHER_CDSS_ADVANCED_MASTER_IMPLEMENTATION_SCAFFOLD_v4.1.md"
SOURCE_REGISTER     = PROJECT_CONTROL / "SOURCE_REGISTER.csv"
PROCESSING_STATUS   = PROJECT_CONTROL / "PROCESSING_STATUS.csv"
VERSION_LOG         = PROJECT_CONTROL / "VERSION_LOG.csv"
INDICATOR_REGISTER  = PROJECT_CONTROL / "INDICATOR_REGISTER.csv"
REFERENCE_BOUNDS    = PROJECT_CONTROL / "REFERENCE_BOUNDS_REGISTER.csv"
BUFFER_RULES        = PROJECT_CONTROL / "BUFFER_RULES.csv"
SPATIAL_JOIN_RULES  = PROJECT_CONTROL / "SPATIAL_JOIN_RULES.csv"
TERRAIN_DECISIONS   = PROJECT_CONTROL / "TERRAIN_PROCESSING_DECISIONS.csv"
HAZARD_DECISIONS    = PROJECT_CONTROL / "HAZARD_MODEL_DECISIONS.csv"
EXPOSURE_DECISIONS  = PROJECT_CONTROL / "EXPOSURE_MODEL_DECISIONS.csv"
CLIMATE_DECISIONS   = PROJECT_CONTROL / "CLIMATE_INTERPOLATION_DECISIONS.csv"
RISK_MODEL_SPEC     = DECISION_RISK / "RISK_MODEL_SPEC.md"

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------
LKP_STATES          = DATA_LOOKUPS / "LKP_States.csv"
LKP_LGAS            = DATA_LOOKUPS / "LKP_LGAs.csv"
LKP_DATA_CONFIDENCE = DATA_LOOKUPS / "LKP_DataConfidence.csv"
LKP_LOOKUP_CODE     = DATA_LOOKUPS / "LKP_LookupCode.csv"
LKP_LIVELIHOOD      = DATA_LOOKUPS / "LKP_Livelihood.csv"
LKP_EROSION_TYPE    = DATA_LOOKUPS / "LKP_ErosionType.csv"
LKP_EROSION_SEV     = DATA_LOOKUPS / "LKP_ErosionSeverity.csv"
LKP_INFRA_TYPE      = DATA_LOOKUPS / "LKP_InfrastructureType.csv"
LKP_WATER_SOURCE    = DATA_LOOKUPS / "LKP_WaterSource.csv"
LKP_ADAPTATION      = DATA_LOOKUPS / "LKP_AdaptationStatus.csv"
LKP_QC_STATUS       = DATA_LOOKUPS / "LKP_QC_Status.csv"
LKP_OP_STATUS       = DATA_LOOKUPS / "LKP_OperatingStatus.csv"
LKP_LAND_COVER      = DATA_LOOKUPS / "LKP_LandCoverClasses.csv"
LKP_ROAD_HIERARCHY  = DATA_LOOKUPS / "LKP_RoadHierarchy.csv"
LKP_POI_CLASSES     = DATA_LOOKUPS / "LKP_POIClasses.csv"
LKP_ENV_PROBLEMS    = DATA_LOOKUPS / "LKP_EnvironmentalProblems.csv"
LKP_STATE_ENV_PROBLEMS = DATA_LOOKUPS / "LKP_State_EnvironmentalProblems.csv"
GEOJSON_G65_ENV_PROBLEMS = GIS_DERIVED / "G65_EnvironmentalProblems.geojson"
RELATIONAL_MODEL    = DATA_LOOKUPS / "RELATIONAL_MODEL.csv"

# ---------------------------------------------------------------------------
# CRS standard
# ---------------------------------------------------------------------------
CRS_PROJECT = "EPSG:4326"

# ---------------------------------------------------------------------------
# Study states (Ten N-HYPPADEC states from CHER-CDSS v4.1 Section 2)
# ---------------------------------------------------------------------------
INTERNAL_STATE_CODES = [
    "NIG",  # Niger
    "KEB",  # Kebbi
    "PLA",  # Plateau
    "BEN",  # Benue
    "KOG",  # Kogi
    "KWA",  # Kwara
    "KAD",  # Kaduna
    "NAS",  # Nasarawa
    "TAR",  # Taraba
    "GOM",  # Gombe
]

STUDY_STATES = [f"NG-{code}" for code in INTERNAL_STATE_CODES]

# Extended regional states disabled - system operates strictly on 10 N-HYPPADEC member states
EXTENDED_BASIN_STATE_CODES = []
EXTENDED_BASIN_STATES = []

STATE_NAMES = {
    "NG-NIG": "Niger",
    "NG-KEB": "Kebbi",
    "NG-PLA": "Plateau",
    "NG-BEN": "Benue",
    "NG-KOG": "Kogi",
    "NG-KWA": "Kwara",
    "NG-KAD": "Kaduna",
    "NG-NAS": "Nasarawa",
    "NG-TAR": "Taraba",
    "NG-GOM": "Gombe",
}

ALL_STATE_NAMES = {
    **STATE_NAMES,
    "NG-ADA": "Adamawa",
}

# Nigeria bounding box (extended for buffer stations/features)
NIGERIA_BOUNDS = {
    "lat_min": 4.0,
    "lat_max": 14.5,
    "lon_min": 2.0,
    "lon_max": 15.5,
}

# Extended bounds for climate stations (100km buffer)
EXTENDED_BOUNDS = {
    "lat_min": 3.5,
    "lat_max": 15.0,
    "lon_min": 1.5,
    "lon_max": 16.0,
}

# ---------------------------------------------------------------------------
# QC status codes (must match LKP_QC_Status.csv)
# ---------------------------------------------------------------------------
class QCStatus:
    RAW          = "RAW"
    INGESTED     = "INGESTED"
    VALIDATING   = "VALIDATING"
    QC_FAILED    = "QC_FAILED"
    CLEAN        = "CLEAN"
    DERIVED      = "DERIVED"
    VALIDATED    = "VALIDATED"
    PUBLISHED    = "PUBLISHED"
    ARCHIVED     = "ARCHIVED"

# ---------------------------------------------------------------------------
# Risk model parameters (CHER-CDSS v4.1 — provisional base formula)
# ---------------------------------------------------------------------------
RISK_MODEL_VERSION = "Risk_Model_v4.1"
SCAFFOLD_VERSION   = "v4.1"
BASELINE_VERSION   = "Baseline_2026"
DATA_DATE          = "2026-10"

RISK_WEIGHTS_BASELINE = {
    "H": 0.35,
    "E": 0.25,
    "V": 0.25,
    "C": 0.15,
}

RISK_WEIGHTS_S1_EQUAL = {
    "H": 0.25,
    "E": 0.25,
    "V": 0.25,
    "C": 0.25,
}

RISK_WEIGHTS_S2_HAZARD_DOMINANT = {
    "H": 0.45,
    "E": 0.20,
    "V": 0.20,
    "C": 0.15,
}

PRIORITY_WEIGHTS = {
    "R_Score": 0.70,
    "Adaptation_Gap": 0.30,
}

# ---------------------------------------------------------------------------
# Normalization Reference Bounds (v4.1 Stage 17.8)
# Fixed min/max bounds frozen at 2026 baseline. Never dynamically recomputed.
# ---------------------------------------------------------------------------
REFERENCE_BOUNDS_2026 = {
    "IND01": {"min": 0.0, "max": 10.0, "dir": "positive"},
    "IND02": {"min": 0.0, "max": 5.0, "dir": "positive"},
    "IND03": {"min": 0.0, "max": 4.0, "dir": "positive"},
    "IND04": {"min": 0.0, "max": 5000.0, "dir": "inverse"},
    "IND05": {"min": 0.0, "max": 10000.0, "dir": "positive"},
    "IND06a": {"min": 0.0, "max": 50.0, "dir": "positive"},
    "IND06b": {"min": 0.0, "max": 25.0, "dir": "positive"},
    "IND06c": {"min": 0.0, "max": 30.0, "dir": "positive"},
    "IND07": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "IND08": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "IND09": {"min": 0.0, "max": 100.0, "dir": "inverse"},
    "IND10": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "H": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "E": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "V": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "C": {"min": 0.0, "max": 100.0, "dir": "positive"},
    "R": {"min": 0.0, "max": 100.0, "dir": "positive"},
}

def normalize_value(x, min_ref, max_ref, direction="positive"):
    """
    Normalizes value against fixed baseline reference bounds with out-of-bounds clipping.
    Direction: 'positive' or 'inverse'
    """
    if max_ref == min_ref:
        return 50.0
    
    # Clip value within bounds to prevent extrapolation distortion
    clipped_x = max(min_ref, min(x, max_ref))
    
    if direction == "positive":
        return 100.0 * (clipped_x - min_ref) / (max_ref - min_ref)
    elif direction == "inverse":
        return 100.0 * (max_ref - clipped_x) / (max_ref - min_ref)
    else:
        raise ValueError(f"Invalid direction: {direction}")

def compute_composite_risk(h, e, v, c, weights=None, method="additive"):
    """
    Computes Composite Risk R on [0, 100].
    Methods:
      - 'additive': R = 0.35H + 0.25E + 0.25V + 0.15C (Section 34)
      - 'multiplicative': R_mult = H^0.35 * E^0.25 * V^0.25 * C^0.15 (Stage 17.9)
    """
    w = weights or RISK_WEIGHTS_BASELINE
    h = max(0.0, min(float(h), 100.0))
    e = max(0.0, min(float(e), 100.0))
    v = max(0.0, min(float(v), 100.0))
    c = max(0.0, min(float(c), 100.0))
    
    if method == "additive":
        return round(w["H"] * h + w["E"] * e + w["V"] * v + w["C"] * c, 2)
    elif method == "multiplicative":
        # Multiplicative aggregation check (Stage 17.9)
        # Avoid zero-log issues by epsilon if needed, but if E=0, geometric risk = 0
        r_mult = (h ** w["H"]) * (e ** w["E"]) * (v ** w["V"]) * (c ** w["C"])
        return round(r_mult, 2)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

def compute_ies(risk_before, risk_after, method_before="v4.1", method_after="v4.1", ref_bounds_same=True):
    """
    Computes Intervention Effectiveness Score (IES) with Section 34 validity rules:
    IES = ((Risk_before - Risk_after) / Risk_before) * 100
    Returns None if Risk_before == 0 or methodology/reference bounds differ.
    """
    if not ref_bounds_same or method_before != method_after:
        return None  # Invalid comparison across different methodologies/bounds
    if risk_before is None or risk_after is None:
        return None
    if float(risk_before) <= 0.0:
        return None  # Undefined when Risk_before = 0 (Reported as N/A)
    
    ies = ((float(risk_before) - float(risk_after)) / float(risk_before)) * 100.0
    return round(ies, 2)

# ---------------------------------------------------------------------------
# Buffer distances (must match BUFFER_RULES.csv)
# ---------------------------------------------------------------------------
BUFFER_RIVER_COMMUNITY_M    = 500    # BUF001
BUFFER_RIVER_INFRA_M        = 200    # BUF002
BUFFER_EROSION_THREAT_M     = 100    # BUF003
BUFFER_HYDROPOWER_COMM_KM   = 10     # BUF004
BUFFER_COMMUNITY_SERVICE_KM = 2      # BUF005
BUFFER_CLIMATE_STATION_KM   = 50     # BUF006
BUFFER_EROSION_RIVER_M      = 300    # BUF007

# ---------------------------------------------------------------------------
# GPS accuracy thresholds
# ---------------------------------------------------------------------------
GPS_ACCURACY_FLAG_M   = 30    # Flag for review
GPS_ACCURACY_REJECT_M = 100   # Reject — require re-survey

# ---------------------------------------------------------------------------
# Minimum sample thresholds (from HAZARD_MODEL_DECISIONS.csv HMD03)
# ---------------------------------------------------------------------------
EROSION_HOTSPOT_MIN_SITES_KDE_SIMPLE    = 10
EROSION_HOTSPOT_MIN_SITES_KDE_WEIGHTED  = 20
EROSION_HOTSPOT_MIN_SITES_CLUSTERING    = 30

# ---------------------------------------------------------------------------
# Flood hazard validation threshold (HMD04)
# ---------------------------------------------------------------------------
FLOOD_HAZARD_VALIDATION_PCT = 0.70  # 70% of High-confidence G25 events in Moderate+ zones

# ---------------------------------------------------------------------------
# Slope unit (DEC02 — FIXED)
# ---------------------------------------------------------------------------
SLOPE_UNIT = "degrees"  # Do NOT change without updating TERRAIN_PROCESSING_DECISIONS.csv
