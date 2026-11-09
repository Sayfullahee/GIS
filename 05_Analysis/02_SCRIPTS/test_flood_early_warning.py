"""Focused checks for the FEW-CAM dashboard reporting contract."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "07_Decision_Support" / "02_Dashboards"))

import app as dashboard_app


class FloodEarlyWarningApiTests(unittest.TestCase):
    def test_warning_levels_and_gis_register(self):
        levels = dashboard_app.get_flood_warning_levels()
        self.assertEqual([level["level"] for level in levels["levels"]], [0, 1, 2, 3])
        self.assertEqual(levels["thresholds_status"], "approval_required")

        layers = dashboard_app.list_gis_layers()
        self.assertEqual(layers["total_layers"], 43)
        self.assertEqual([layer["id"] for layer in layers["layers"][-6:]],
                         ["G38", "G39", "G40", "G41", "G42", "G43"])
        river_network = next(layer for layer in layers["layers"] if layer["id"] == "G05")
        self.assertIn("main rivers", river_network["scope"].casefold())
        self.assertIn("tributaries", river_network["scope"])
        self.assertIn("distributaries", river_network["scope"])
        self.assertIn("streams", river_network["scope"])
        self.assertIn("drainage channels", river_network["scope"])

    def test_alert_feed_only_returns_released_public_fields(self):
        alerts = pd.DataFrame([
            {
                "Alert_ID": "A-1", "Issued_At": "2026-10-01", "State_Code": "NG-NIG", "LGA_ID": "NIG-01",
                "Warning_Level": 2, "Status": "released", "Confidence": "High",
                "Trigger_Type": "river_level", "Hazard_Score": 81, "Released_At": "2026-10-01",
                "Approved_By": "manager-login", "Notes": "restricted review detail",
            },
            {
                "Alert_ID": "A-2", "Issued_At": "2026-10-02", "State_Code": "NG-NIG", "LGA_ID": "NIG-02",
                "Warning_Level": 3, "Status": "proposed", "Confidence": "Moderate",
                "Trigger_Type": "rainfall", "Hazard_Score": 42, "Released_At": None,
                "Approved_By": "", "Notes": "draft",
            },
        ])
        with patch.object(dashboard_app, "load_flood_dataset", return_value=alerts):
            response = dashboard_app.get_flood_alerts()
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["alerts"][0]["alert_id"], "A-1")
        self.assertNotIn("approved_by", response["alerts"][0])
        self.assertNotIn("notes", response["alerts"][0])

    def test_dashboard_metrics_use_released_and_published_records(self):
        datasets = {
            "Flood_Alerts": pd.DataFrame([
                {
                    "alert_id": "A-1", "status": "released", "warning_level": 2,
                    "issued_at": "2026-10-01", "state_code": "NG-NIG", "trigger_type": "river_level",
                    "hazard_score": 81, "confidence": "High", "released_at": "2026-10-01",
                },
                {
                    "alert_id": "A-2", "status": "proposed", "warning_level": 3,
                    "issued_at": "2026-10-02", "state_code": "NG-NIG", "trigger_type": "rainfall",
                    "hazard_score": 42, "confidence": "Moderate", "released_at": None,
                },
            ]),
            "Flood_Notifications": pd.DataFrame([
                {"notification_id": "N-1", "alert_id": "A-1", "recipient_count": 10, "reached_count": 8},
                {"notification_id": "N-2", "alert_id": "A-2", "recipient_count": 5, "reached_count": 5},
            ]),
            "Flood_Acknowledgements": pd.DataFrame([
                {"notification_id": "N-1", "acknowledgement_status": "received"},
                {"notification_id": "N-2", "acknowledgement_status": "received"},
            ]),
            "Flood_Awareness": pd.DataFrame([
                {"publication_status": "approved", "community_id": "C-1"},
                {"publication_status": "restricted", "community_id": "C-2"},
            ]),
            "Flood_Warning_Performance": pd.DataFrame([
                {
                    "publication_status": "approved", "performance_id": "P-1", "alert_id": "A-1",
                    "evaluated_at": "2026-10-03", "lead_time_hours": 6, "hit_status": "hit",
                    "high_risk_communities": 4, "communities_reached": 2,
                    "audit_completeness_pct": 80, "confidence": "High", "evaluated_by": "reviewer",
                    "lessons_learned": "internal note",
                },
                {
                    "publication_status": "restricted", "performance_id": "P-2", "alert_id": "A-2",
                    "evaluated_at": "2026-10-04", "lead_time_hours": 0, "hit_status": "false_alarm",
                    "high_risk_communities": 1, "communities_reached": 0,
                    "audit_completeness_pct": 20, "confidence": "Moderate", "evaluated_by": "reviewer",
                    "lessons_learned": "unpublished",
                },
            ]),
        }
        with patch.object(dashboard_app, "load_flood_dataset", side_effect=datasets.get):
            response = dashboard_app.get_flood_dashboard()

        self.assertEqual(response["active_warnings"], 1)
        self.assertEqual(response["total_alerts"], 1)
        self.assertEqual(response["warning_level_counts"]["2"], 1)
        self.assertEqual(response["notification_reach_rate_pct"], 80.0)
        self.assertEqual(response["notification_acknowledgement_rate_pct"], 10.0)
        self.assertEqual(response["awareness_activities"], 1)
        self.assertEqual(response["performance_metrics"]["hit_rate_pct"], 100.0)
        self.assertEqual(response["performance_metrics"]["false_alarm_rate_pct"], 0.0)
        self.assertEqual(response["performance_metrics"]["mean_lead_time_hours"], 6.0)
        self.assertEqual(response["performance_metrics"]["high_risk_awareness_coverage_pct"], 50.0)
        self.assertEqual(response["performance_metrics"]["mean_audit_completeness_pct"], 80.0)
        self.assertNotIn("evaluated_by", response["performance_evaluations"][0])
        self.assertNotIn("lessons_learned", response["performance_evaluations"][0])

    def test_dashboard_rejects_invalid_alert_levels(self):
        alert = pd.DataFrame([{
            "alert_id": "A-1", "status": "released", "warning_level": 2.5,
            "issued_at": "2026-10-01", "state_code": "NG-NIG",
            "trigger_type": "river_level", "hazard_score": 81,
            "confidence": "High", "released_at": "2026-10-01",
        }])
        with patch.object(dashboard_app, "load_flood_dataset", side_effect=lambda name: alert if name == "Flood_Alerts" else None):
            with self.assertRaises(dashboard_app.HTTPException) as error:
                dashboard_app.get_flood_dashboard()
        self.assertEqual(error.exception.status_code, 500)
        self.assertIn("warning_level", error.exception.detail)

    def test_level_zero_is_not_counted_as_an_active_warning(self):
        alert = pd.DataFrame([{
            "alert_id": "A-0", "status": "released", "warning_level": 0,
            "issued_at": "2026-10-01", "state_code": "NG-NIG",
            "trigger_type": "routine_monitoring", "hazard_score": 0,
            "confidence": "High", "released_at": "2026-10-01",
        }])
        with patch.object(dashboard_app, "load_flood_dataset", side_effect=lambda name: alert if name == "Flood_Alerts" else None):
            response = dashboard_app.get_flood_dashboard()
        self.assertEqual(response["total_alerts"], 1)
        self.assertEqual(response["active_warnings"], 0)
        self.assertEqual(response["warning_level_counts"]["0"], 1)

    def test_unconfigured_feeds_are_not_fabricated(self):
        with patch.object(dashboard_app, "load_flood_dataset", return_value=None):
            response = dashboard_app.get_flood_dashboard()
            alerts = dashboard_app.get_flood_alerts()
            performance = dashboard_app.get_flood_warning_performance()
        self.assertEqual(response["status"], "NOT_CONFIGURED")
        self.assertEqual(response["active_warnings"], 0)
        self.assertIsNone(response["performance_metrics"]["hit_rate_pct"])
        self.assertEqual(alerts["status"], "NOT_CONFIGURED")
        self.assertEqual(performance["status"], "NOT_CONFIGURED")


if __name__ == "__main__":
    unittest.main()
