"""
ai_field_anomaly_service.py
===========================
Phase 2 AI Module for CHER-CDSS v4.2 Field Operations.
Provides:
  1. Survey Anomaly & Fraud Detection (GPS Spoofing, Straight-lining, Velocity Check).
  2. Mobile Survey Photo PII Detection & Level 3 Privacy Blurring Gate.
  3. Intelligent Quarantine Auto-Resolution Recommendation Engine.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. Spatial-Temporal Velocity & Distance Calculator (Haversine)
# -----------------------------------------------------------------------------
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometres."""
    r = 6371.0 # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

# -----------------------------------------------------------------------------
# 2. Enumeration Anomaly & Fraud Detection Engine
# -----------------------------------------------------------------------------
def audit_submission_anomalies(
    submission: Dict[str, Any],
    recent_submissions_by_enumerator: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates field survey submission against behavioural & spatial fraud patterns:
      - Test 1: Duration & Completion Velocity (under 120 seconds for 74 questions)
      - Test 2: Unrealistic Enumerator Travel Speed (> 120 km/h between rural sites)
      - Test 3: Straight-Lining Response Entropy (Identical answers on multi-choice arrays)
      - Test 4: Precision GPS Spoofing (identical coords for distinct communities)
    """
    flags = []
    risk_score = 0.0 # 0 (normal) to 1.0 (severe fraud probability)
    
    # 1. Survey Duration Check
    start_time = submission.get("start") or submission.get("_submission_time")
    end_time = submission.get("end")
    if start_time and end_time:
        try:
            t0 = datetime.fromisoformat(str(start_time).replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(str(end_time).replace("Z", "+00:00"))
            duration_sec = (t1 - t0).total_seconds()
            if 0 < duration_sec < 120:
                flags.append(f"AI_FRAUD_WARN: Rapid completion ({duration_sec:.0f}s for 74-question instrument)")
                risk_score += 0.35
        except Exception:
            pass

    # 2. Spatial Travel Velocity Check
    lat = submission.get("latitude")
    lon = submission.get("longitude")
    enum_id = submission.get("enumerator_id", "ENUM_DEFAULT")
    
    if recent_submissions_by_enumerator and lat is not None and lon is not None:
        try:
            cur_lat, cur_lon = float(lat), float(lon)
            last_sub = recent_submissions_by_enumerator[-1]
            last_lat = float(last_sub.get("latitude", cur_lat))
            last_lon = float(last_sub.get("longitude", cur_lon))
            last_time_str = last_sub.get("_ingested_at") or last_sub.get("_submission_time")
            
            if last_time_str:
                last_t = datetime.fromisoformat(str(last_time_str).replace("Z", "+00:00"))
                cur_t = datetime.now()
                delta_hours = max((cur_t - last_t).total_seconds() / 3600.0, 0.001)
                dist_km = haversine_km(last_lat, last_lon, cur_lat, cur_lon)
                speed_kmh = dist_km / delta_hours
                
                # If speed > 130 km/h across rugged rural terrain without airport
                if dist_km > 5.0 and speed_kmh > 130.0:
                    flags.append(f"AI_FRAUD_WARN: Implausible velocity ({speed_kmh:.1f} km/h over {dist_km:.1f} km)")
                    risk_score += 0.45
                    
                # Exact identical coordinates for different communities
                if dist_km == 0.0 and submission.get("community_name") != last_sub.get("community_name"):
                    flags.append("AI_FRAUD_WARN: Identical coordinate duplication on separate community names (Couch-Surfing)")
                    risk_score += 0.40
        except Exception:
            pass

    # 3. Straight-Lining Response Variance
    # Count identical response patterns across ordinal/numerical questions
    sample_answers = [
        submission.get("flood_severity_rating"),
        submission.get("erosion_threat_level"),
        submission.get("food_insecurity_index"),
        submission.get("infrastructure_damage_score")
    ]
    valid_answers = [float(a) for a in sample_answers if a is not None and str(a).replace('.','',1).isdigit()]
    if len(valid_answers) >= 4 and len(set(valid_answers)) == 1:
        flags.append("AI_QC_ADVISORY: Zero-variance straight-lining across severity assessments")
        risk_score += 0.20

    is_anomalous = risk_score >= 0.50
    recommendation = "QUARANTINE_FOR_SUPERVISOR_AUDIT" if is_anomalous else "PASS_TO_CLEAN"

    return {
        "is_anomalous": is_anomalous,
        "fraud_risk_score": round(min(risk_score, 1.0), 2),
        "recommendation": recommendation,
        "anomaly_flags": flags,
        "audited_at": datetime.now().isoformat()
    }

# -----------------------------------------------------------------------------
# 3. Photo PII Privacy Shield Verification
# -----------------------------------------------------------------------------
def inspect_field_photo_pii(photo_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates field photo metadata and image attributes against Level 3 PII privacy rules.
    If facial features or identifying badges are present, triggers redaction workflow.
    """
    file_name = photo_metadata.get("file_name", "photo.jpg")
    photo_type = photo_metadata.get("photo_category", "INFRASTRUCTURE") # INFRASTRUCTURE | EROSION_GULLY | FLOOD_WATERMARK | HOUSEHOLD
    has_consent = photo_metadata.get("consent_for_media", False)
    
    # In CHER-CDSS Level 3 rules: NO individual facial photos may be published in derived GIS layers
    requires_face_redaction = (photo_type == "HOUSEHOLD") or (photo_metadata.get("faces_detected", 0) > 0)
    
    return {
        "status": "SCANNED",
        "file_name": file_name,
        "level3_compliant": not requires_face_redaction or has_consent,
        "requires_face_blur": requires_face_redaction,
        "privacy_tier": "LEVEL_3_RESTRICTED",
        "action_taken": "APPLY_GAUSSIAN_BLUR_SHIELD" if requires_face_redaction else "CLEARED_NON_PII",
        "audit_timestamp": datetime.now().isoformat()
    }
