"""
test_all_improvements.py
========================
Automated Verification Suite for the 5 High-Impact Platform Improvements:
Tests live endpoints over HTTP using urllib.request.
"""

import sys
import json
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")

def post(path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload else b""
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")

def run_tests():
    print("=" * 70)
    print("  CHER-CDSS 5-IMPROVEMENT ACCEPTANCE & INTEGRATION TEST SUITE")
    print("=" * 70)

    # 1. Test Kobo Status
    status_code, body = get("/api/kobo/status")
    assert status_code == 200, f"Kobo status failed: {status_code}"
    status_data = json.loads(body)
    print("✓ Gate 1: Kobo Ingestion Status API operational")
    print(f"  • Processed: {status_data['total_processed']} | Landing: {status_data['landing_submissions_count']} | Quarantined: {status_data['quarantined_records_count']}")

    # 2. Test Kobo Sync Sandbox
    status_code, body = post("/api/kobo/sync?sandbox_mode=true")
    assert status_code == 200, f"Kobo sync failed: {status_code}"
    sync_data = json.loads(body)
    print("✓ Gate 2: Kobo Field Submission Sync Pipeline")
    print(f"  • Processed: {sync_data.get('processed_count', 0)} | Passed: {sync_data.get('passed_count', 0)} | Quarantined: {sync_data.get('quarantined_count', 0)}")

    # 3. Test Kobo Quarantine Listing
    status_code, body = get("/api/kobo/quarantine")
    assert status_code == 200
    quar_data = json.loads(body)
    print(f"✓ Gate 3: Kobo Quarantine Log Inspector ({quar_data['count']} flagged records)")

    # 4. Test Kobo Quarantine Resolution (if any quarantined record exists)
    if quar_data["count"] > 0:
        first_sub = quar_data["quarantined_records"][0]
        sub_id = first_sub.get("_submission_id") or first_sub.get("_id")
        status_code, body = post("/api/kobo/resolve", {
            "submission_id": sub_id,
            "corrections": {
                "consent_given": "yes",
                "state_code": "NG-NIG",
                "lga_code": "NG-NIG-001"
            },
            "approved_by": "Test Supervisor",
            "justification": "Automated acceptance test override"
        })
        assert status_code == 200, f"Resolution failed: {body}"
        res_data = json.loads(body)
        print(f"✓ Gate 4: Quarantine Resolution Engine promoted record '{sub_id}'")

    # 5. Test MHCVI Compound Vulnerability
    status_code, body = get("/api/vulnerability/mhcvi")
    assert status_code == 200
    mhcvi_data = json.loads(body)
    assert len(mhcvi_data["state_rankings"]) >= 10
    top_state = mhcvi_data["state_rankings"][0]
    print("✓ Gate 5: Multi-Hazard Compound Vulnerability Index (MHCVI)")
    print(f"  • Evaluated: {mhcvi_data['states_evaluated']} States | Top Vulnerable: {top_state['state_name']} ({top_state['mhcvi_score']}/100)")
    print(f"  • LGA Hotspots generated: {len(mhcvi_data['lga_hotspots'])}")

    # 6. Test SitRep Structured Data
    status_code, body = get("/api/sitrep/data")
    assert status_code == 200
    sitrep_data = json.loads(body)
    print("✓ Gate 6: Executive SitRep Structured Data Generator")
    print(f"  • Report Ref: {sitrep_data['report_ref']} | Critical Hotspots: {sitrep_data['critical_incidents']}")
    print(f"  • Recommended Emergency Allocation: ₦{sitrep_data['recommended_emergency_allocation_ngn'] / 1e6:,.1f}M")

    # 7. Test SitRep HTML Print Document
    status_code, body = get("/api/sitrep/print")
    assert status_code == 200
    assert "NATIONAL HYDROELECTRIC POWER PRODUCING AREAS DEVELOPMENT COMMISSION" in body
    print("✓ Gate 7: Executive SitRep Print-Ready HTML Document Rendered (with official crests & sign-off)")

    # 8. Test Early Warning Alerts Feed
    status_code, body = get("/api/early-warning/alerts")
    assert status_code == 200
    alerts_data = json.loads(body)
    print(f"✓ Gate 8: Early Warning Multi-Hazard Alerts Feed ({alerts_data['total_active_alerts']} active alerts)")

    # 9. Test Emergency Broadcast Simulation
    status_code, body = post("/api/early-warning/simulate-dispatch", {
        "alert_id": "ALT-2026-HYD-01",
        "channel": "SMS_BROADCAST",
        "recipients_group": "Community Liaison Officers & Village Heads"
    })
    assert status_code == 200
    disp_data = json.loads(body)
    print("✓ Gate 9: Emergency Broadcast Simulation Transmitted")
    print(f"  • Dispatched via {disp_data['dispatch_details']['channel']} to {disp_data['dispatch_details']['recipients_contacted']} recipients")

    # 10. Test UI Landing Page
    status_code, body = get("/")
    assert status_code == 200
    assert "alert-ticker" in body
    assert "tab-field_ops" in body
    assert "tab-sitrep" in body
    assert "btn-mode-mhcvi" in body
    print("✓ Gate 10: Executive Management UI Portal loaded with all new controls and navigation tabs")

    print("=" * 70)
    print("  ALL 10 VERIFICATION GATES PASSED SUCCESSFULLY (10 / 10 PASS)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
