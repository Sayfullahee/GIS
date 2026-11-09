"""
test_ai_integration.py
======================
Comprehensive End-to-End Test Suite for CHER-CDSS v4.2 AI Integration (Phases 1-4).
"""

import sys
import os
import unittest
from pathlib import Path
import json

PROJECT_ROOT = Path(r"c:\xampp\htdocs\GIS")
sys.path.insert(0, str(PROJECT_ROOT / "05_Analysis" / "02_SCRIPTS"))
sys.path.insert(0, str(PROJECT_ROOT / "02_Fieldwork"))
sys.path.insert(0, str(PROJECT_ROOT / "07_Decision_Support" / "02_Dashboards"))
sys.path.insert(0, str(PROJECT_ROOT / "07_Decision_Support" / "03_Priority_Areas"))

import ai_advisory_service
import ai_field_anomaly_service
import ai_flood_forecast_service
import ai_portfolio_optimizer
import app


class TestCherCdssAiIntegration(unittest.TestCase):

    # -------------------------------------------------------------------------
    # PHASE 1: GENAI EXECUTIVE SITREP & INDIGENOUS TRANSLATION
    # -------------------------------------------------------------------------
    def test_01_phase1_sitrep_synthesis(self):
        sample_metrics = {
            "state_name": "Niger State",
            "total_incidents_recorded": 24,
            "critical_incidents": 6,
            "high_incidents": 10,
            "recommended_emergency_allocation_ngn": 850_000_000,
            "estimated_affected_population": 42000,
            "total_lgas_monitored": 8,
            "top_hazards": [{"hazard": "Flooding", "count": 12}, {"hazard": "Riverbank Erosion", "count": 8}]
        }
        res = ai_advisory_service.generate_ai_sitrep_synthesis(sample_metrics)
        self.assertEqual(res["status"], "OPERATIONAL")
        self.assertIn("INTELLIGENCE BRIEFING", res["executive_summary"])
        self.assertIn("Niger State", res["executive_summary"])
        self.assertEqual(len(res["strategic_directives"]), 4)
        self.assertEqual(res["quantified_impact"]["critical_hotspots"], 6)

    def test_02_phase1_indigenous_languages(self):
        payload = {
            "alert_id": "ALT-TEST-001",
            "target_states": ["Niger", "Kwara"],
            "target_lgas": ["Mokwa", "Lavun", "Pategi"],
            "hazard_type": "Dam Spillway Discharge",
            "severity": "CRITICAL",
            "lead_time_hours": 14,
            "evacuation_shelter": "High Ground Primary School"
        }
        for lang in ["hausa", "nupe", "tiv", "yoruba", "fulfulde", "gbagyi"]:
            res = ai_advisory_service.translate_alert_to_indigenous(payload, lang)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertIn("compact_sms", res)
            self.assertLessEqual(res["sms_char_count"], 160, f"SMS exceeded 160 chars in {lang}: {res['sms_char_count']}")
            self.assertIn("radio_broadcast_script", res)

    # -------------------------------------------------------------------------
    # PHASE 2: FIELD SURVEY QUALITY & LEVEL 3 CV PRIVACY SHIELD
    # -------------------------------------------------------------------------
    def test_03_phase2_field_fraud_detection(self):
        # 1. Rapid submission (<120s)
        fast_sub = {
            "start": "2026-11-06T09:00:00Z",
            "end": "2026-11-06T09:01:10Z", # 70 seconds
            "latitude": 9.08,
            "longitude": 6.54,
            "enumerator_id": "ENUM-01",
            "community_name": "Test Comm"
        }
        res = ai_field_anomaly_service.audit_submission_anomalies(fast_sub)
        self.assertTrue(any("Rapid completion" in f for f in res["anomaly_flags"]))

        # 2. Straight-lining zero variance
        sl_sub = {
            "latitude": 9.08,
            "longitude": 6.54,
            "flood_severity_rating": 3,
            "erosion_threat_level": 3,
            "food_insecurity_index": 3,
            "infrastructure_damage_score": 3
        }
        res_sl = ai_field_anomaly_service.audit_submission_anomalies(sl_sub)
        self.assertTrue(any("straight-lining" in f.lower() for f in res_sl["anomaly_flags"]))

    def test_04_phase2_cv_photo_pii_shield(self):
        # Household photo with face and no consent -> blur required
        meta_face = {
            "file_name": "hh_survey_01.jpg",
            "photo_category": "HOUSEHOLD",
            "faces_detected": 2,
            "consent_for_media": False
        }
        res = ai_field_anomaly_service.inspect_field_photo_pii(meta_face)
        self.assertTrue(res["requires_face_blur"])
        self.assertEqual(res["action_taken"], "APPLY_GAUSSIAN_BLUR_SHIELD")

        # Infrastructure photo without faces -> cleared
        meta_infra = {
            "file_name": "culvert_damage.jpg",
            "photo_category": "INFRASTRUCTURE",
            "faces_detected": 0
        }
        res_infra = ai_field_anomaly_service.inspect_field_photo_pii(meta_infra)
        self.assertFalse(res_infra["requires_face_blur"])
        self.assertEqual(res_infra["action_taken"], "CLEARED_NON_PII")

    # -------------------------------------------------------------------------
    # PHASE 3: HYDRO DAM RESERVOIR INFLOW & SPILL FORECASTING
    # -------------------------------------------------------------------------
    def test_05_phase3_dam_forecasts(self):
        for dam_id in ["DAM-NIG-01", "DAM-NIG-02", "DAM-NIG-03", "DAM-GOM-01", "DAM-TAR-01"]:
            fc = ai_flood_forecast_service.forecast_dam_inflow_and_spill(dam_id, upstream_rainfall_forecast_mm=65.0)
            self.assertEqual(fc["status"], "OPERATIONAL")
            self.assertIn("forecast_horizons", fc)
            self.assertGreater(fc["forecast_horizons"]["t24_inflow_m3s"], 0)
            self.assertIn(fc["warning_level"], [1, 2, 3])
            self.assertGreater(len(fc["downstream_exposed_lgas"]), 0)

    # -------------------------------------------------------------------------
    # PHASE 4: PRESCRIPTIVE CAPITAL PORTFOLIO OPTIMIZER
    # -------------------------------------------------------------------------
    def test_06_phase4_portfolio_optimizer(self):
        # 1. MAX_IES
        res_ies = ai_portfolio_optimizer.optimize_capital_portfolio(
            total_budget_ngn=2_500_000_000.0,
            objective="MAX_IES"
        )
        self.assertIn(res_ies["status"], ["OPTIMAL", "HEURISTIC_FEASIBLE"])
        self.assertGreater(res_ies["portfolio_summary"]["selected_projects_count"], 5)
        self.assertLessEqual(res_ies["allocated_budget_ngn"], 2_500_000_000.0)
        self.assertGreater(res_ies["portfolio_summary"]["mean_ies_score_pct"], 15.0)

        # 2. EQUITY_BALANCED
        res_eq = ai_portfolio_optimizer.optimize_capital_portfolio(
            total_budget_ngn=2_500_000_000.0,
            objective="EQUITY_BALANCED",
            max_state_share_pct=25.0
        )
        self.assertIn(res_eq["status"], ["OPTIMAL", "HEURISTIC_FEASIBLE"])
        self.assertGreater(len(res_eq["state_allocations"]), 3)

    # -------------------------------------------------------------------------
    # FASTAPI ROUTE ENDPOINTS DIRECT CALL VERIFICATION
    # -------------------------------------------------------------------------
    def test_07_api_ai_sitrep_endpoint(self):
        data = app.ai_sitrep_synthesize_get(state_code=None)
        self.assertEqual(data["status"], "OPERATIONAL")
        self.assertIn("executive_summary", data)
        self.assertEqual(len(data["strategic_directives"]), 4)

    def test_08_api_ai_alerts_translate_endpoint(self):
        req = app.AlertTranslationRequest(
            alert_id="ALT-API-01",
            target_language="nupe",
            target_states=["Niger", "Kwara"],
            target_lgas=["Mokwa", "Pategi"],
            hazard_type="Flooding",
            severity="CRITICAL",
            lead_time_hours=14,
            evacuation_shelter="Mokwa Town Hall"
        )
        data = app.ai_alert_translate(req)
        self.assertEqual(data["target_language"], "Nupe")
        self.assertLessEqual(data["sms_char_count"], 160)

    def test_09_api_ai_fieldwork_endpoints(self):
        # Audit
        req_audit = app.FieldAuditRequest(
            submission={
                "start": "2026-11-06T09:00:00Z",
                "end": "2026-11-06T09:00:50Z",
                "latitude": 9.08,
                "longitude": 6.54
            }
        )
        res_audit = app.ai_audit_field_submission(req_audit)
        self.assertIn("fraud_risk_score", res_audit)

        # Photo scan
        req_photo = app.PhotoPiiScanRequest(
            file_name="erosion.jpg",
            photo_category="EROSION_GULLY",
            faces_detected=0
        )
        res_photo = app.ai_scan_photo_pii(req_photo)
        self.assertFalse(res_photo["requires_face_blur"])

    def test_10_api_ai_dam_forecast_endpoints(self):
        data = app.ai_dam_forecast_get(dam_id="DAM-NIG-01", rainfall_mm=55.0, water_level_m=None)
        self.assertEqual(data["dam_id"], "DAM-NIG-01")
        self.assertIn("forecast_horizons", data)

    def test_11_api_ai_portfolio_optimizer_endpoint(self):
        req_opt = app.PortfolioOptimizationRequest(
            total_budget_ngn=2_000_000_000.0,
            objective="MAX_IES",
            candidate_pool_size=50
        )
        data = app.ai_portfolio_optimizer_post(req_opt)
        self.assertIn(data["status"], ["OPTIMAL", "HEURISTIC_FEASIBLE"])
        self.assertIn("selected_interventions", data)

    def test_12_top20_register_lga_names_preserved(self):
        res = app.get_top20_priority_communities()
        self.assertEqual(res["status"], "OPERATIONAL")
        records = res["data"]
        self.assertEqual(len(records), 20)
        for r in records:
            lga = r.get("LGA") or r.get("lga") or r.get("lga_name")
            self.assertTrue(lga and lga != "N/A" and lga != "None", f"Missing LGA in record: {r}")

    # -------------------------------------------------------------------------
    # IMPROVEMENT 1: DYNAMIC DAM INUNDATION PLUME GEOJSON
    # -------------------------------------------------------------------------
    def test_13_improvement_1_dam_inundation_geojson(self):
        res = app.ai_dam_inundation_geojson("DAM-NIG-01", 55.0)
        self.assertEqual(res["type"], "FeatureCollection")
        self.assertGreaterEqual(len(res["features"]), 4)
        geom_types = [f["geometry"]["type"] for f in res["features"]]
        self.assertIn("Point", geom_types)
        self.assertIn("LineString", geom_types)
        self.assertIn("Polygon", geom_types)

    # -------------------------------------------------------------------------
    # IMPROVEMENT 2: LIVE METEOROLOGICAL & SATELLITE WEATHER FEED
    # -------------------------------------------------------------------------
    def test_14_improvement_2_live_weather_feed(self):
        res = app.ai_dam_live_weather("DAM-NIG-01")
        self.assertIn(res["status"], ["SUCCESS", "OPERATIONAL_OFFLINE_BASELINE"])
        self.assertEqual(res["dam_id"], "DAM-NIG-01")
        self.assertIn("rainfall_24h_mm", res)
        self.assertIn("temperature_c", res)
        self.assertIn("wind_speed_kmh", res)
        self.assertIn("telemetry_source", res)

        all_dams = app.ai_all_dams_weather()
        self.assertEqual(all_dams["status"], "SUCCESS")
        self.assertEqual(all_dams["total_dams"], 5)

    # -------------------------------------------------------------------------
    # IMPROVEMENT 3: MULTI-CHANNEL EMERGENCY DISPATCH GATEWAY
    # -------------------------------------------------------------------------
    def test_15_improvement_3_emergency_dispatch_gateway(self):
        recipients = app.emergency_get_recipients()
        self.assertEqual(recipients["status"], "OPERATIONAL")
        self.assertGreaterEqual(recipients["total"], 8)

        req_disp = app.EmergencyBroadcastDispatchPayload(
            dam_id="DAM-NIG-01",
            dam_name="Kainji Dam",
            warning_level=3,
            spill_risk_pct=85.0,
            lead_time_hours=18,
            affected_lgas=["Mokwa", "Borgu"],
            language="Hausa",
            selected_channels=["SMS", "WHATSAPP", "TELEGRAM"],
            sender_officer="Test Commander"
        )
        disp_res = app.emergency_dispatch_post(req_disp)
        self.assertTrue(disp_res["dispatch_id"].startswith("DISP-"))
        self.assertEqual(disp_res["statistics"]["success_rate_pct"], 100.0)
        self.assertIn("sms", disp_res["payloads"])
        self.assertIn("whatsapp", disp_res["payloads"])
        self.assertIn("telegram", disp_res["payloads"])

        history = app.emergency_get_dispatch_history(limit=5)
        self.assertEqual(history["status"], "OPERATIONAL")
        self.assertGreaterEqual(history["total_records"], 1)

    # -------------------------------------------------------------------------
    # IMPROVEMENT 4: ONE-CLICK EXECUTIVE PDF DOSSIER & VERIFICATION QR
    # -------------------------------------------------------------------------
    def test_16_improvement_4_executive_dossier_service(self):
        html = app.sitrep_executive_dossier(auto_print=False)
        self.assertIsInstance(html, str)
        self.assertIn("N-HYPPADEC", html)
        self.assertIn("svg", html)  # Vector Crest and QR Code
        self.assertIn("RESTRICTED", html)
        self.assertIn("SHA-256 Checksum", html)
        self.assertIn("Top-20 Priority Communities Capital Investment Register", html)

    # -------------------------------------------------------------------------
    # IMPROVEMENT 5: AUTOMATED POSTGIS DATABASE SYNC & AUDIT
    # -------------------------------------------------------------------------
    def test_17_improvement_5_postgis_sync_service(self):
        status = app.database_postgis_status()
        self.assertEqual(status["status"], "OPERATIONAL")
        schema = status["schema_audit"]
        self.assertTrue(schema["ddl_file_present"])
        self.assertEqual(schema["compliance_rate_pct"], 100.0)
        self.assertEqual(schema["tables_ready_for_sync"], 34)

        sync_res = app.database_sync_postgis(None)
        self.assertIn(sync_res["status"], ["SUCCESS", "STANDBY_OFFLINE_VERIFIED"])
        self.assertIn("database", sync_res)

    # -------------------------------------------------------------------------
    # AI CAPABILITY 1: STRATEGIC DAM WATER LEVEL & HYDROSTATIC MONITOR
    # -------------------------------------------------------------------------
    def test_18_dam_water_levels_monitoring(self):
        res = app.ai_dams_water_levels()
        self.assertEqual(res["status"], "OPERATIONAL")
        self.assertGreaterEqual(res["total_dams_monitored"], 7)
        self.assertIn("dams", res)

        for d in res["dams"]:
            self.assertIn("dam_id", d)
            self.assertIn("dam_name", d)
            self.assertIn("elevation_metrics", d)
            self.assertIn("storage_metrics", d)
            self.assertIn("hydrostatic_status", d)
            self.assertIn("action_code", d)
            em = d["elevation_metrics"]
            self.assertGreater(em["full_reservoir_level_m"], em["min_operating_level_m"])
            sm = d["storage_metrics"]
            self.assertTrue(0.0 <= sm["active_storage_pct"] <= 100.0)

    # -------------------------------------------------------------------------
    # AI CAPABILITY 2: STATE RAINFALL DEFICIT & HARVEST LOSS PREDICTION (FAO-33)
    # -------------------------------------------------------------------------
    def test_19_state_drought_harvest_loss_prediction(self):
        res = app.ai_drought_state_harvest_impact()
        self.assertEqual(res["status"], "OPERATIONAL")
        self.assertIn("summary", res)
        self.assertIn("state_rankings", res)
        self.assertGreaterEqual(len(res["state_rankings"]), 10)

        # Check vulnerability ranking ordering (highest deficit first)
        rankings = res["state_rankings"]
        for i in range(len(rankings) - 1):
            self.assertGreaterEqual(
                rankings[i]["harvest_impact"]["mean_harvest_reduction_pct"],
                rankings[i+1]["harvest_impact"]["mean_harvest_reduction_pct"]
            )

        # Check crop breakdown keys
        first_state = rankings[0]
        cb = first_state["crop_breakdown"]
        for crop in ["Maize", "Rice", "Yam", "Sorghum", "Millet"]:
            self.assertIn(crop, cb)
            self.assertGreater(cb[crop]["ky_response_factor"], 0)
            self.assertTrue(0.0 <= cb[crop]["yield_loss_pct"] <= 100.0)

    # -------------------------------------------------------------------------
    # AI CAPABILITY 3: PRESCRIPTIVE DAM IRRIGATION & GRAIN DIRECTIVES
    # -------------------------------------------------------------------------
    def test_20_drought_irrigation_advisory(self):
        res = app.ai_drought_irrigation_advisory()
        self.assertEqual(res["status"], "OPERATIONAL")
        self.assertIn("hardest_hit_states", res)
        self.assertIn("directives", res)
        self.assertGreaterEqual(len(res["directives"]), 3)

        categories = [d["category"] for d in res["directives"]]
        self.assertTrue(any("IRRIGATION" in c for c in categories))
        self.assertIn("STRATEGIC_GRAIN_RESERVE", categories)

    # -------------------------------------------------------------------------
    # OFFICIAL N-HYPPADEC LOGO & INSTITUTIONAL SEALS
    # -------------------------------------------------------------------------
    def test_21_official_agency_logo_and_seals(self):
        import logo_asset
        import executive_dossier_service
        import sitrep_service

        # 1. Test logo file and data URI availability
        path = logo_asset.get_logo_filepath()
        self.assertTrue(os.path.exists(path))
        data_uri = logo_asset.get_logo_data_uri()
        self.assertTrue(data_uri.startswith("data:image/jpeg;base64,"))
        self.assertGreater(len(data_uri), 1000)

        # 2. Test logo API endpoint
        logo_resp = app.get_official_agency_logo()
        self.assertEqual(logo_resp.media_type, "image/jpeg")
        self.assertTrue(os.path.exists(logo_resp.path))

        # 3. Test Executive Dossier HTML includes official emblem
        dossier_html = executive_dossier_service.generate_executive_dossier_html()
        self.assertIn("data:image/jpeg;base64,", dossier_html)
        self.assertIn('alt="N-HYPPADEC Official Seal"', dossier_html)

        # 4. Test Situation Report (SitRep) HTML includes official emblem
        sitrep_html = sitrep_service.generate_sitrep_html()
        self.assertIn("data:image/jpeg;base64,", sitrep_html)
        self.assertIn('alt="N-HYPPADEC Official Seal"', sitrep_html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
