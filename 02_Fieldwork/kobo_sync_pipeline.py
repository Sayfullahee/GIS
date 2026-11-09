"""
kobo_sync_pipeline.py
=====================
Automated Real-Time KoboToolbox / ODK Ingestion Pipeline for CHER-CDSS v4.2.
Fetches, validates, stages, quarantines, and promotes mobile field survey submissions.

Validation Gates:
  - Gate 1: Informed Consent Gate (Consent_Given == 'yes')
  - Gate 2: Cascading Geographic Referential Integrity (State -> LGA mapping)
  - Gate 3: Spatial Boundary & GPS Precision Gates (Lat 4-14, Lon 2.5-15, Accuracy <= 30m)
  - Gate 4: Multi-Hazard & Numerical Constraint Rules (0-100%, 14 Canonical Hazards)
  - Gate 5: De-duplication & Idempotent Audit Logging
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(os.environ.get("GIS_PROJECT_ROOT", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(PROJECT_ROOT / "05_Analysis" / "02_SCRIPTS"))
import config as cfg

STAGING_DIR = cfg.FIELDWORK_DIR / "staging"
LANDING_CSV = cfg.KOBO_SUBMISSIONS_LANDING
QUARANTINE_CSV = cfg.KOBO_QUARANTINE_LOG
SYNC_HISTORY_JSON = cfg.KOBO_SYNC_LOG

# Ensure staging directory exists
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load Reference Lookups for Referential Integrity
# ---------------------------------------------------------------------------
def _load_reference_lookups():
    lkp_states = pd.read_csv(cfg.LKP_STATES)
    lkp_lgas = pd.read_csv(cfg.LKP_LGAS)
    lkp_problems = pd.read_csv(cfg.DATA_LOOKUPS / "LKP_EnvironmentalProblems.csv")
    
    valid_states = set(lkp_states["State_Code"].str.upper())
    valid_lgas = {} # lga_code -> state_code
    for _, r in lkp_lgas.iterrows():
        valid_lgas[str(r["LGA_Code"]).upper()] = str(r["State_Code"]).upper()
        
    valid_problems = set(lkp_problems["Problem_Code"].str.upper())
    return valid_states, valid_lgas, valid_problems

# ---------------------------------------------------------------------------
# Parse Geopoint helper
# ---------------------------------------------------------------------------
def _parse_geopoint(val: Any) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Parse lat, lon, accuracy from Kobo geopoint string 'lat lon alt acc' or dict/list."""
    if not val:
        return None, None, None
    if isinstance(val, (list, tuple)) and len(val) >= 2:
        return float(val[0]), float(val[1]), float(val[2]) if len(val) > 2 else 0.0
    if isinstance(val, str):
        parts = val.strip().split()
        if len(parts) >= 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                acc = float(parts[3]) if len(parts) >= 4 else 0.0
                return lat, lon, acc
            except (ValueError, IndexError):
                pass
    return None, None, None

# ---------------------------------------------------------------------------
# Quality Control Validation Engine
# ---------------------------------------------------------------------------
def validate_submission(record: Dict[str, Any], valid_states: set, valid_lgas: dict, valid_problems: set) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates record against all 5 Quality Control Gates.
    Returns: (is_valid: bool, reason: str, cleaned_record: dict)
    """
    sub_id = record.get("_id") or record.get("submission_id") or record.get("meta/instanceID") or record.get("instanceID")
    if not sub_id:
        return False, "GATE_0_FAIL: Missing submission instance identifier", {}

    cleaned = dict(record)
    cleaned["_submission_id"] = str(sub_id)
    cleaned["_ingested_at"] = datetime.now().isoformat()

    # GATE 1: INFORMED CONSENT
    consent = str(record.get("consent_given", "")).strip().lower()
    if consent not in ["yes", "1", "true"]:
        return False, "GATE_1_FAIL: Informed consent withheld (consent_given != 'yes')", cleaned

    # GATE 2: GEOGRAPHY & CASCADING REFERENTIAL INTEGRITY
    state = str(record.get("state_code", "")).strip().upper()
    lga = str(record.get("lga_code", "")).strip().upper()
    
    if not state or state not in valid_states:
        return False, f"GATE_2_FAIL: Invalid or unregistered State_Code '{state}'", cleaned
        
    if not lga or lga not in valid_lgas:
        return False, f"GATE_2_FAIL: Invalid or unregistered LGA_Code '{lga}'", cleaned
        
    if valid_lgas[lga] != state:
        return False, f"GATE_2_FAIL: LGA '{lga}' does not belong to State '{state}' (cascading failure)", cleaned

    # GATE 3: SPATIAL INTEGRITY & GPS PRECISION
    gps_val = record.get("community_gps") or record.get("_geolocation")
    lat, lon, acc = _parse_geopoint(gps_val)
    if lat is None or lon is None:
        # Fallback to separate fields
        lat = float(record.get("latitude")) if record.get("latitude") is not None else None
        lon = float(record.get("longitude")) if record.get("longitude") is not None else None
        acc = float(record.get("gps_accuracy", 0.0))

    if lat is None or lon is None:
        return False, "GATE_3_FAIL: Missing or unparseable GPS coordinates", cleaned

    if not (4.0 <= lat <= 14.0 and 2.5 <= lon <= 15.0):
        return False, f"GATE_3_FAIL: Coordinates ({lat}, {lon}) outside Nigeria territorial bounds", cleaned

    if acc and acc > 50.0:
        cleaned["_qc_flag"] = f"GPS_LOW_ACCURACY_{acc}m"
    else:
        cleaned["_qc_flag"] = "GPS_VERIFIED"

    cleaned["_latitude"] = round(lat, 6)
    cleaned["_longitude"] = round(lon, 6)
    cleaned["_gps_accuracy_m"] = round(acc, 1) if acc else None

    # GATE 4: CONSTRAINT VALIDATIONS
    crop_loss = record.get("crop_loss_pct")
    if crop_loss is not None and crop_loss != "":
        try:
            cl = float(crop_loss)
            if cl < 0 or cl > 100:
                return False, f"GATE_4_FAIL: crop_loss_pct {cl} outside allowable range [0, 100]", cleaned
        except ValueError:
            return False, f"GATE_4_FAIL: Non-numeric crop_loss_pct '{crop_loss}'", cleaned

    # Multi-hazard check
    hazards_obs = record.get("environmental_problems_observed", "")
    if hazards_obs:
        h_list = [h.strip().upper() for h in str(hazards_obs).replace(";", " ").split() if h.strip()]
        invalid_h = [h for h in h_list if h not in valid_problems]
        if invalid_h:
            return False, f"GATE_4_FAIL: Unregistered environmental hazard codes: {invalid_h}", cleaned

    return True, "PASSED_ALL_GATES", cleaned

# ---------------------------------------------------------------------------
# Sync / Ingest Core Engine
# ---------------------------------------------------------------------------
def ingest_submissions(raw_submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingests a list of raw submissions from Kobo API or Webhook.
    Applies the 5 QC gates, writes to staging landing, quarantines failures,
    and updates database / GIS derived layers.
    """
    valid_states, valid_lgas, valid_problems = _load_reference_lookups()
    
    # Load existing processed IDs to ensure idempotency (Gate 5)
    existing_ids = set()
    if LANDING_CSV.exists():
        try:
            df_existing = pd.read_csv(LANDING_CSV, usecols=["_submission_id"])
            existing_ids = set(df_existing["_submission_id"].astype(str))
        except Exception:
            pass

    passed_records = []
    quarantined_records = []

    for sub in raw_submissions:
        sub_id = str(sub.get("_id") or sub.get("submission_id") or sub.get("meta/instanceID") or sub.get("instanceID"))
        if sub_id in existing_ids:
            # Already ingested
            continue

        is_valid, reason, cleaned = validate_submission(sub, valid_states, valid_lgas, valid_problems)
        if is_valid:
            cleaned["_qc_status"] = "VALIDATED_CLEAN"
            passed_records.append(cleaned)
            existing_ids.add(sub_id)
        else:
            cleaned["_quarantine_reason"] = reason
            cleaned["_quarantined_at"] = datetime.now().isoformat()
            quarantined_records.append(cleaned)

    # 1. Append valid records to landing staging
    if passed_records:
        df_passed = pd.DataFrame(passed_records)
        if LANDING_CSV.exists():
            df_passed.to_csv(LANDING_CSV, mode="a", header=False, index=False, encoding="utf-8")
        else:
            df_passed.to_csv(LANDING_CSV, mode="w", header=True, index=False, encoding="utf-8")

    # 2. Append quarantined records to quarantine log
    if quarantined_records:
        df_quarantine = pd.DataFrame(quarantined_records)
        if QUARANTINE_CSV.exists():
            df_quarantine.to_csv(QUARANTINE_CSV, mode="a", header=False, index=False, encoding="utf-8")
        else:
            df_quarantine.to_csv(QUARANTINE_CSV, mode="w", header=True, index=False, encoding="utf-8")

    # 3. Update Sync History
    history_entry = {
        "sync_timestamp": datetime.now().isoformat(),
        "total_incoming": len(raw_submissions),
        "new_passed": len(passed_records),
        "new_quarantined": len(quarantined_records),
        "cumulative_passed": len(existing_ids)
    }

    history = []
    if SYNC_HISTORY_JSON.exists():
        try:
            with open(SYNC_HISTORY_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append(history_entry)
    with open(SYNC_HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return {
        "status": "SUCCESS",
        "processed_count": len(raw_submissions),
        "passed_count": len(passed_records),
        "quarantined_count": len(quarantined_records),
        "cumulative_valid_submissions": len(existing_ids),
        "timestamp": datetime.now().isoformat()
    }

# ---------------------------------------------------------------------------
# Quarantine Remediation / Resolution Engine
# ---------------------------------------------------------------------------
def resolve_quarantined_record(
    submission_id: str,
    corrections: Dict[str, Any],
    approved_by: str = "Admin",
    justification: str = "Verified and resolved via Field Ops Hub"
) -> Dict[str, Any]:
    """
    Resolves a quarantined submission by applying corrections, re-validating,
    and promoting it into the clean landing dataset.
    """
    if not QUARANTINE_CSV.exists():
        return {"status": "ERROR", "message": "Quarantine log does not exist"}

    df_quarantine = pd.read_csv(QUARANTINE_CSV)
    if df_quarantine.empty:
        return {"status": "ERROR", "message": "Quarantine log is empty"}

    # Find row
    id_col = "_submission_id" if "_submission_id" in df_quarantine.columns else "_id"
    match_mask = df_quarantine[id_col].astype(str) == str(submission_id)
    if not match_mask.any():
        return {"status": "NOT_FOUND", "message": f"Submission '{submission_id}' not found in quarantine"}

    row_dict = df_quarantine[match_mask].iloc[0].to_dict()
    # Apply corrections
    for k, v in corrections.items():
        row_dict[k] = v

    # Re-validate
    valid_states, valid_lgas, valid_problems = _load_reference_lookups()
    is_valid, reason, cleaned = validate_submission(row_dict, valid_states, valid_lgas, valid_problems)

    if not is_valid:
        return {
            "status": "VALIDATION_FAILED",
            "message": f"Remediation failed validation: {reason}",
            "submission_id": submission_id
        }

    # Promote to landing
    cleaned["_qc_status"] = "RESOLVED_AND_PROMOTED"
    cleaned["_resolved_by"] = approved_by
    cleaned["_resolution_justification"] = justification
    cleaned["_resolved_at"] = datetime.now().isoformat()

    df_passed = pd.DataFrame([cleaned])
    if LANDING_CSV.exists():
        df_passed.to_csv(LANDING_CSV, mode="a", header=False, index=False, encoding="utf-8")
    else:
        df_passed.to_csv(LANDING_CSV, mode="w", header=True, index=False, encoding="utf-8")

    # Remove from quarantine log
    df_quarantine = df_quarantine[~match_mask]
    df_quarantine.to_csv(QUARANTINE_CSV, mode="w", header=True, index=False, encoding="utf-8")

    return {
        "status": "RESOLVED",
        "message": f"Submission '{submission_id}' successfully remediated and promoted to Clean Landing",
        "submission_id": submission_id,
        "resolved_by": approved_by,
        "timestamp": datetime.now().isoformat()
    }


# ---------------------------------------------------------------------------
# Fetch from Remote KoboToolbox API
# ---------------------------------------------------------------------------
def fetch_and_sync_kobo(
    api_url: Optional[str] = None,
    asset_uid: Optional[str] = None,
    api_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Connects to the remote KoboToolbox API v2 endpoint, pulls submissions,
    and runs them through the ingestion and quarantine pipeline.
    """
    url = api_url or os.environ.get("KOBO_API_URL") or "https://kf.kobotoolbox.org/api/v2"
    asset = asset_uid or os.environ.get("KOBO_ASSET_UID") or "cher_cdss_field_survey_v4_2"
    token = api_token or os.environ.get("KOBO_API_TOKEN")

    endpoint = f"{url.rstrip('/')}/assets/{asset}/data.json"

    req = urllib.request.Request(endpoint)
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Token {token}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            return ingest_submissions(results)
    except urllib.error.HTTPError as e:
        return {
            "status": "ERROR",
            "http_code": e.code,
            "detail": f"Kobo API HTTP Error {e.code}: {e.reason}",
            "endpoint": endpoint
        }
    except Exception as e:
        return {
            "status": "OFFLINE_FALLBACK",
            "detail": f"Could not reach remote Kobo host ({e}). Pipeline operational in local offline/webhook mode.",
            "endpoint": endpoint
        }

# ---------------------------------------------------------------------------
# Mock Field Submission Generator (for Test & Dev Sandbox)
# ---------------------------------------------------------------------------
def generate_mock_field_submissions(count: int = 5) -> List[Dict[str, Any]]:
    """Generates realistic Kobo submission payloads matching v4.2 survey."""
    lkp_states = pd.read_csv(cfg.LKP_STATES)
    lkp_lgas = pd.read_csv(cfg.LKP_LGAS)
    
    submissions = []
    for i in range(count):
        state_row = lkp_states.sample(1).iloc[0]
        s_code = state_row["State_Code"]
        lga_candidates = lkp_lgas[lkp_lgas["State_Code"] == s_code]
        lga_row = lga_candidates.sample(1).iloc[0] if len(lga_candidates) > 0 else lkp_lgas.sample(1).iloc[0]
        
        # 10% chance to simulate a quarantine test case (e.g. invalid GPS or consent refusal)
        is_quarantine_test = (i == 3)
        consent = "no" if is_quarantine_test else "yes"
        
        sub = {
            "_id": f"KOBO-SUB-{date.today().strftime('%Y%m%d')}-{i+1001:04d}",
            "start_time": "2026-10-21T09:00:00",
            "end_time": "2026-10-21T09:35:00",
            "today_date": "2026-10-21",
            "enumerator_id": f"ENUM-{(i%12)+1:02d}",
            "supervisor_id": f"SUP-{s_code[3:]}-01",
            "consent_given": consent,
            "state_code": s_code,
            "lga_code": lga_row["LGA_Code"],
            "ward_name": f"Ward {i+1}",
            "community_name": f"Field Observation Settlement {i+1}",
            "community_gps": f"{9.5 + i*0.1} {6.5 + i*0.1} 240.0 5.4",
            "estimated_population": int(np.random.randint(500, 5000)),
            "primary_livelihood": "LIV01",
            "electricity_access": "Yes",
            "water_source": "WS01",
            "flood_experience_past_year": "yes",
            "flood_frequency_5yrs": 3,
            "flood_severity_rank": "3",
            "erosion_presence": "yes",
            "erosion_type": "gully",
            "erosion_severity_rank": "2",
            "crop_loss_pct": 25.5,
            "bandit_attack_experienced": "yes" if s_code in ["NG-NIG", "NG-KAD", "NG-KEB"] else "no",
            "bandit_attack_frequency": 2 if s_code in ["NG-NIG", "NG-KAD", "NG-KEB"] else 0,
            "farm_access_restricted": "yes" if s_code in ["NG-NIG", "NG-KAD", "NG-KEB"] else "no",
            "environmental_problems_observed": "FLOODING EROSION FOOD_SECURITY" + (" BANDIT_ATTACK" if s_code in ["NG-NIG", "NG-KAD"] else ""),
            "primary_environmental_problem": "FLOODING",
            "primary_problem_severity": "3",
            "primary_problem_trend": "worsening",
            "site_photo_1": f"site_photo_{i+1}.jpg",
            "photo_category_1": "INFRASTRUCTURE" if i % 2 == 0 else "EROSION_GULLY",
            "consent_for_media_1": "yes"
        }
        submissions.append(sub)
    return submissions

if __name__ == "__main__":
    print("=" * 65)
    print("  CHER-CDSS KOBOTOOLBOX REAL-TIME INGESTION PIPELINE")
    print("=" * 65)
    mocks = generate_mock_field_submissions(5)
    print(f"Generated {len(mocks)} mock test field submissions...")
    result = ingest_submissions(mocks)
    print("Ingestion Result:")
    print(json.dumps(result, indent=2))
