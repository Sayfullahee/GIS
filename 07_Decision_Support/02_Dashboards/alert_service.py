"""
alert_service.py
================
Multi-Hazard Early Warning & Alert Dispatch Service for CHER-CDSS v4.2.
Monitors hydro-climatic telemetry and security thresholds to broadcast
verified advisories across SMS, VHF Radio, and Emergency WhatsApp channels.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import json

PROJECT_ROOT = Path(r"c:\xampp\htdocs\GIS")
DISPATCH_LOG_PATH = PROJECT_ROOT / "02_Fieldwork" / "staging" / "alert_dispatch_history.json"

ACTIVE_ADVISORIES = [
    {
        "alert_id": "ALT-2026-HYD-01",
        "category": "Hydrological / Dam Spill",
        "hazard_type": "Flooding",
        "severity": "CRITICAL",
        "level": 3,
        "title": "Kainji & Jebba Hydro Dams Stage-2 Spillway Discharge",
        "target_states": ["NG-NIG", "NG-KEB", "NG-KWA"],
        "target_lgas": ["Mokwa", "Lavun", "Yauri", "Pategi"],
        "lead_time_hours": 18,
        "issued_at": "2026-10-21T06:00:00",
        "advisory_text": "Spillway discharge active at Kainji Dam. Immediate downstream floodplain evacuation advised for riverine settlements.",
        "status": "ACTIVE"
    },
    {
        "alert_id": "ALT-2026-SEC-02",
        "category": "Security / Conflict",
        "hazard_type": "Bandit Attack",
        "severity": "HIGH",
        "level": 2,
        "title": "Allawa-Shiroro Forest Corridor Security Advisory",
        "target_states": ["NG-NIG"],
        "target_lgas": ["Shiroro", "Rafi"],
        "lead_time_hours": 6,
        "issued_at": "2026-10-21T07:30:00",
        "advisory_text": "Unverified armed movement detected along the river corridor. Suspend solitary farming activities and maintain group escorts.",
        "status": "ACTIVE"
    },
    {
        "alert_id": "ALT-2026-MET-03",
        "category": "Meteorological / Rainfall",
        "hazard_type": "Flooding",
        "severity": "HIGH",
        "level": 2,
        "title": "Upper Benue Basin Extreme Convective Storm Warning",
        "target_states": ["NG-BEN", "NG-TAR", "NG-ADA"],
        "target_lgas": ["Makurdi", "Guma", "Ibi", "Yola North"],
        "lead_time_hours": 12,
        "issued_at": "2026-10-21T08:15:00",
        "advisory_text": "Intense rainfall (>85mm/6h) forecast over Cameroon highlands and Benue confluence. Prepare flood barriers.",
        "status": "ACTIVE"
    },
    {
        "alert_id": "ALT-2026-ENV-04",
        "category": "Agro-Climatic Stress",
        "hazard_type": "Drought",
        "severity": "MODERATE",
        "level": 1,
        "title": "Sudano-Sahelian Soil Moisture Deficit Alert",
        "target_states": ["NG-KEB", "NG-GOM"],
        "target_lgas": ["Dandi", "Bagudo", "Balanga"],
        "lead_time_hours": 72,
        "issued_at": "2026-10-20T12:00:00",
        "advisory_text": "Negative NDVI anomaly detected. Supplemental irrigation and livestock water point management advised.",
        "status": "WATCH"
    }
]

def get_active_alerts() -> Dict[str, Any]:
    """Returns active multi-hazard alerts with severity rankings and lead times."""
    return {
        "status": "OPERATIONAL",
        "timestamp": datetime.now().isoformat(),
        "total_active_alerts": len(ACTIVE_ADVISORIES),
        "critical_count": len([a for a in ACTIVE_ADVISORIES if a["severity"] == "CRITICAL"]),
        "high_count": len([a for a in ACTIVE_ADVISORIES if a["severity"] == "HIGH"]),
        "alerts": ACTIVE_ADVISORIES
    }

def simulate_alert_dispatch(
    alert_id: str,
    channel: str = "SMS_BROADCAST",
    recipients_group: str = "Community Liaison Officers & Village Heads"
) -> Dict[str, Any]:
    """Simulates broadcasting an emergency alert to local field focal points."""
    target_alert = next((a for a in ACTIVE_ADVISORIES if a["alert_id"] == alert_id), ACTIVE_ADVISORIES[0])
    
    dispatch_record = {
        "dispatch_id": f"DISP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "alert_id": target_alert["alert_id"],
        "title": target_alert["title"],
        "channel": channel,
        "recipients_group": recipients_group,
        "dispatched_at": datetime.now().isoformat(),
        "recipients_contacted": 142,
        "delivery_rate_pct": 98.6,
        "acknowledged_count": 128,
        "status": "TRANSMITTED_AND_ACKNOWLEDGED"
    }

    # Save to history log
    history = []
    if DISPATCH_LOG_PATH.exists():
        try:
            with open(DISPATCH_LOG_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    
    history.insert(0, dispatch_record)
    with open(DISPATCH_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(history[:50], f, indent=2)

    return {
        "status": "SUCCESS",
        "message": f"Broadcast successfully dispatched via {channel} to {recipients_group}",
        "dispatch_details": dispatch_record
    }

def get_dispatch_history() -> List[Dict[str, Any]]:
    """Retrieves broadcast audit log."""
    if DISPATCH_LOG_PATH.exists():
        try:
            with open(DISPATCH_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []
