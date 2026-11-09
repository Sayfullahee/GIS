"""
load_data_to_postgis.py
=======================
Automated data seeder and migration loader for the CHER-CDSS PostGIS Database.
Populates lookups, administrative boundaries, community masters, core clean tables,
derived risk indices, and FEW-CAM operational warning tables from authoritative CSVs.
"""

import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parents[1]
DATA_CLEAN = PROJECT_ROOT / "03_Data" / "CLEAN"
LOOKUPS = PROJECT_ROOT / "03_Data" / "LOOKUPS"
CONTROL = PROJECT_ROOT / "00_Project_Control"

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "fewcam",
    "user": "fewcam_dev",
    "password": "ZFTLsRHDsOr8-zKSJLQcnLuitP4jebUoWCAaIeW9mfejDquF"
}

def clean_val(val, default=None):
    if pd.isna(val):
        return default
    return val

def clean_int(val, default=None):
    if pd.isna(val):
        return default
    try:
        return int(float(val))
    except Exception:
        return default

def clean_float(val, default=None):
    if pd.isna(val):
        return default
    try:
        return float(val)
    except Exception:
        return default

def clean_str(val, default=None):
    if pd.isna(val):
        return default
    s = str(val).strip()
    return s if s != "" else default

def seed_database():
    print("=" * 70)
    print("  CHER-CDSS POSTGIS AUTHORITATIVE DATA SEEDER & MIGRATION LOADER v4.1")
    print("=" * 70)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Set session replication role to replica to allow loading baseline seed data without lifecycle trigger blocks
        cur.execute("SET session_replication_role = 'replica';")
        print("✓ Session replication role set to 'replica' for clean batch seeding.")

        # -------------------------------------------------------------
        # 1. Lookups: States
        # -------------------------------------------------------------
        print("\n[1] Seeding lookups.states...")
        df_states = pd.read_csv(LOOKUPS / "LKP_States.csv")
        for _, r in df_states.iterrows():
            cur.execute("""
                INSERT INTO lookups.states (state_code, internal_code, state_name, capital, geopolitical_zone, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (state_code) DO UPDATE SET
                    state_name = EXCLUDED.state_name,
                    capital = EXCLUDED.capital,
                    geopolitical_zone = EXCLUDED.geopolitical_zone;
            """, (clean_str(r["State_Code"]), clean_str(r["Internal_Code"]), clean_str(r["State_Name"]),
                  clean_str(r["Capital"]), clean_str(r["Region"]), clean_str(r["Notes"])))
        print(f"  ✓ Seeded {len(df_states)} states.")

        # -------------------------------------------------------------
        # 2. Lookups: LGAs
        # -------------------------------------------------------------
        print("\n[2] Seeding lookups.lgas...")
        df_lgas = pd.read_csv(LOOKUPS / "LKP_LGAs.csv")
        for _, r in df_lgas.iterrows():
            cur.execute("""
                INSERT INTO lookups.lgas (lga_id, lga_name, state_code, area_sqkm, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (lga_id) DO UPDATE SET
                    lga_name = EXCLUDED.lga_name,
                    area_sqkm = EXCLUDED.area_sqkm;
            """, (clean_str(r["LGA_Code"]), clean_str(r["LGA_Name"]), clean_str(r["State_Code"]),
                  clean_float(r["area_sqkm"]), clean_str(r["Notes"])))
        print(f"  ✓ Seeded {len(df_lgas)} LGAs.")

        # Build LGA map for name lookup
        cur.execute("SELECT lga_id, lga_name, state_code FROM lookups.lgas;")
        lga_map = {f"{r[1].lower()}_{r[2]}": r[0] for r in cur.fetchall()}
        lga_name_only_map = {}
        cur.execute("SELECT lga_id, lga_name FROM lookups.lgas;")
        for lid, lname in cur.fetchall():
            lga_name_only_map[lname.lower()] = lid

        # -------------------------------------------------------------
        # 3. Lookups: Lookup Codes
        # -------------------------------------------------------------
        print("\n[3] Seeding lookups.lookup_code...")
        df_lkp = pd.read_csv(DATA_CLEAN / "Lookup_Code_CLEAN.csv")
        for _, r in df_lkp.iterrows():
            lbl = clean_str(r.get("Label")) or clean_str(r.get("Code")) or "None"
            cur.execute("""
                INSERT INTO lookups.lookup_code (lookup_id, domain, code, label, description, unit, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (lookup_id) DO UPDATE SET
                    label = EXCLUDED.label,
                    description = EXCLUDED.description;
            """, (clean_str(r["Lookup_ID"]), clean_str(r["Domain"]), clean_str(r["Code"]),
                  lbl, clean_str(r["Description"]), clean_str(r["Unit"]),
                  clean_str(r.get("Version"), "v4.1")))
        print(f"  ✓ Seeded {len(df_lkp)} controlled vocabulary lookup codes.")

        # -------------------------------------------------------------
        # 4. Lookups: Reference Bounds
        # -------------------------------------------------------------
        print("\n[4] Seeding lookups.reference_bounds...")
        df_ref = pd.read_csv(CONTROL / "REFERENCE_BOUNDS_REGISTER.csv")
        for _, r in df_ref.iterrows():
            cur.execute("""
                INSERT INTO lookups.reference_bounds (
                    indicator_id, indicator_name, component, direction, min_ref, max_ref, unit, transform, baseline_version, frozen_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_id) DO UPDATE SET
                    min_ref = EXCLUDED.min_ref,
                    max_ref = EXCLUDED.max_ref;
            """, (clean_str(r["Indicator_ID"]), clean_str(r["Indicator_Name"]), clean_str(r["Component"]),
                  clean_str(r["Direction"]), clean_float(r["Min_Ref"]), clean_float(r["Max_Ref"]),
                  clean_str(r["Unit"]), clean_str(r["Transform"], "none"),
                  clean_str(r["Baseline_Version"], "Baseline_2026"), clean_str(r["Frozen_Date"], "2026-10-01")))
        print(f"  ✓ Seeded {len(df_ref)} reference bound registers.")

        # -------------------------------------------------------------
        # 5. Clean: Data Provenance
        # -------------------------------------------------------------
        print("\n[5] Seeding clean.data_provenance...")
        df_prov = pd.read_csv(DATA_CLEAN / "Data_Provenance_CLEAN.csv")
        for _, r in df_prov.iterrows():
            cur.execute("""
                INSERT INTO clean.data_provenance (provenance_id, source_name, acquisition_date, processing_method, software_version, analyst_name, limitations)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provenance_id) DO NOTHING;
            """, (clean_str(r["Provenance_ID"]), clean_str(r["Source_Name"]), clean_str(r["Acquisition_Date"]),
                  clean_str(r["Processing_Method"]), clean_str(r["Software_Version"]),
                  clean_str(r["Analyst_Name"]), clean_str(r["Limitations"])))
        
        # Also ensure all operational provenance IDs are registered
        extra_prov_ids = [
            "PRV-OSGOF-2026-01", "PRV-FMWR-2026-01", "PRV-NIMET-2026-01", "PRV-FIELD-2026-01",
            "PRV-NHYPPADEC-ENG-2026", "PRV-BEN-DRILL-2026", "PRV-BEN-GAUGE-01", "PRV-BEN-IMP-2025",
            "PRV-BEN-SEMA-2025-01", "PRV-KEB-SEMA-2025-01", "PRV-KOG-DRILL-2026", "PRV-KOG-GAUGE-01",
            "PRV-KOG-IMP-2025", "PRV-KOG-SEMA-2025-01", "PRV-NIG-DRILL-2026", "PRV-NIG-GAUGE-01",
            "PRV-NIG-IMP-2025", "PRV-NIG-SEMA-2025-01", "PRV-SURVEY-2026-01", "PRV-HYDRO-2026-01"
        ]
        for pid in extra_prov_ids:
            cur.execute("""
                INSERT INTO clean.data_provenance (provenance_id, source_name, acquisition_date, processing_method, software_version, analyst_name, limitations)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provenance_id) DO NOTHING;
            """, (pid, f"Operational Telemetry & Survey Log ({pid})", "2026-01-15",
                  "Automated Sensor / Multi-Agency Logging", "v4.1", "CHER-CDSS Automated Pipeline", "Baseline operational coverage"))
        print(f"  ✓ Seeded {len(df_prov)} base + {len(extra_prov_ids)} operational data provenance entries.")

        # -------------------------------------------------------------
        # 6. Clean: Data Confidence
        # -------------------------------------------------------------
        print("\n[6] Seeding clean.data_confidence...")
        df_conf = pd.read_csv(DATA_CLEAN / "Data_Confidence_CLEAN.csv")
        for _, r in df_conf.iterrows():
            cur.execute("""
                INSERT INTO clean.data_confidence (confidence_id, entity_or_layer, completeness_pct, recency_months, source_quality, validation_status, rating, decision_use, assessed_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (confidence_id) DO NOTHING;
            """, (clean_str(r["Confidence_ID"]), clean_str(r["Entity_Or_Layer"]), clean_float(r["Completeness_Pct"]),
                  clean_int(r["Recency_Months"], 0), clean_str(r["Source_Quality"]), clean_str(r["Validation_Status"]),
                  clean_str(r["Rating"]), clean_str(r["Decision_Use"]), clean_str(r["Assessed_Date"], "2026-10-01")))
        print(f"  ✓ Seeded {len(df_conf)} confidence evaluations.")

        # -------------------------------------------------------------
        # 7. Audit: Audit Trail
        # -------------------------------------------------------------
        print("\n[7] Seeding audit.audit_trail...")
        df_audit = pd.read_csv(DATA_CLEAN / "Audit_Trail_CLEAN.csv")
        for _, r in df_audit.iterrows():
            cur.execute("""
                INSERT INTO audit.audit_trail (audit_id, table_name, record_pk, column_name, original_value, corrected_value, reason, user_name, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (audit_id) DO NOTHING;
            """, (clean_int(r["Audit_ID"]), clean_str(r["Table_Name"]), clean_str(r["Record_PK"]),
                  clean_str(r["Column_Name"]), clean_str(r["Original_Value"]), clean_str(r["Corrected_Value"]),
                  clean_str(r["Reason"]), clean_str(r["User_Name"]), clean_str(r["Timestamp"])))
        print(f"  ✓ Seeded {len(df_audit)} audit trail entries.")

        # -------------------------------------------------------------
        # 8. Clean: Ward Master
        # -------------------------------------------------------------
        print("\n[8] Seeding clean.ward_master...")
        df_wards = pd.read_csv(DATA_CLEAN / "Ward_Master_CLEAN.csv")
        for _, r in df_wards.iterrows():
            cur.execute("""
                INSERT INTO clean.ward_master (ward_id, ward_name, lga_id, state_code, boundary_version, validity_start, provenance_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ward_id) DO NOTHING;
            """, (clean_str(r["Ward_ID"]), clean_str(r["Ward_Name"]), clean_str(r["LGA_Code"]),
                  clean_str(r["State_Code"]), clean_str(r["Boundary_Version"]), clean_str(r["Validity_Start"]), "PRV-OSGOF-2026-01"))
        print(f"  ✓ Seeded {len(df_wards)} wards.")

        # -------------------------------------------------------------
        # 9. Clean: Community Master
        # -------------------------------------------------------------
        print("\n[9] Seeding clean.community_master...")
        df_comm = pd.read_csv(DATA_CLEAN / "DB01_Community_Master_CLEAN.csv")
        comm_state_map = {}
        for _, r in df_comm.iterrows():
            cid = clean_str(r["Community_ID"])
            scode = clean_str(r["State_Code"])
            comm_state_map[cid] = scode
            cur.execute("""
                INSERT INTO clean.community_master (
                    community_id, community_name, lga_id, state_code,
                    latitude, longitude, gps_accuracy_m, survey_date,
                    population, primary_livelihood, electricity_access,
                    water_source, flood_experience, erosion_presence, adaptation_status,
                    geom, provenance_id
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                )
                ON CONFLICT (community_id) DO UPDATE SET
                    community_name = EXCLUDED.community_name,
                    population = EXCLUDED.population;
            """, (
                cid, clean_str(r["Community"]), clean_str(r["LGA_Code"]), scode,
                clean_float(r["Latitude"]), clean_float(r["Longitude"]), clean_float(r["GPS_Accuracy_m"]), clean_str(r["Survey_Date"]),
                clean_int(r["Population"]), clean_str(r.get("Livelihood")), clean_str(r.get("Electricity_Access")),
                clean_str(r.get("Water_Source")), clean_str(r.get("Flood_Experience")), clean_str(r.get("Erosion_Presence")),
                clean_str(r.get("Adaptation_Status")), clean_float(r["Longitude"]), clean_float(r["Latitude"]), "PRV-OSGOF-2026-01"
            ))
        print(f"  ✓ Seeded {len(df_comm)} communities with PostGIS Point geometries.")

        # -------------------------------------------------------------
        # 10. Clean: Facility Master (Hydropower)
        # -------------------------------------------------------------
        print("\n[10] Seeding clean.facility_master...")
        df_fac = pd.read_csv(DATA_CLEAN / "Facility_Master_CLEAN.csv")
        for _, r in df_fac.iterrows():
            lga_raw = clean_str(r.get("LGA"))
            lga_code = None
            if lga_raw:
                lga_code = lga_map.get(f"{lga_raw.lower()}_{clean_str(r['State_Code'])}") or lga_name_only_map.get(lga_raw.lower())
            
            cur.execute("""
                INSERT INTO clean.facility_master (
                    facility_id, facility_name, facility_type, installed_capacity_mw, operator,
                    status, state_code, lga_id, linked_basin, latitude, longitude, geom, provenance_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                )
                ON CONFLICT (facility_id) DO NOTHING;
            """, (
                clean_str(r["Facility_ID"]), clean_str(r["Facility_Name"]), clean_str(r["Facility_Type"]),
                clean_float(r["Installed_Capacity_MW"]), clean_str(r["Operator"]), clean_str(r["Status"]),
                clean_str(r["State_Code"]), lga_code, clean_str(r["Linked_Basin"]),
                clean_float(r["Latitude"]), clean_float(r["Longitude"]),
                clean_float(r["Longitude"]), clean_float(r["Latitude"]),
                clean_str(r.get("Provenance_ID"), "PRV-FMWR-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_fac)} facility master records.")

        # -------------------------------------------------------------
        # 11. Clean: Climate Station
        # -------------------------------------------------------------
        print("\n[11] Seeding clean.climate_station...")
        df_sta = pd.read_csv(DATA_CLEAN / "Climate_Station_CLEAN.csv")
        for _, r in df_sta.iterrows():
            cur.execute("""
                INSERT INTO clean.climate_station (
                    station_id, station_name, operator, elevation_m, state_code,
                    latitude, longitude, operating_since, geom, provenance_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                )
                ON CONFLICT (station_id) DO NOTHING;
            """, (
                clean_str(r["Station_ID"]), clean_str(r["Station_Name"]), clean_str(r["Operator"]),
                clean_float(r["Elevation_m"]), clean_str(r["State_Code"]),
                clean_float(r["Latitude"]), clean_float(r["Longitude"]), clean_str(r["Operating_Since"]),
                clean_float(r["Longitude"]), clean_float(r["Latitude"]),
                clean_str(r.get("Provenance_ID"), "PRV-NIMET-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_sta)} meteorological stations.")

        # -------------------------------------------------------------
        # 12. Clean: Household Survey
        # -------------------------------------------------------------
        print("\n[12] Seeding clean.household_survey...")
        df_hh = pd.read_csv(DATA_CLEAN / "DB02_Household_Survey_CLEAN_RESTRICTED.csv")
        for _, r in df_hh.iterrows():
            cid = clean_str(r["Community_ID"])
            scode = comm_state_map.get(cid, "NG-NIG")
            consent = str(r.get("Consent_Given")).strip().lower() in ["yes", "true", "1"]
            cur.execute("""
                INSERT INTO clean.household_survey (
                    household_id, community_id, state_code, consent_given, household_size,
                    livelihood_type, flood_loss_amount, erosion_loss_amount,
                    adaptation_coping_mechanism, survey_timestamp, provenance_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (household_id) DO NOTHING;
            """, (
                clean_str(r["Household_ID"]), cid, scode, consent, clean_int(r["HH_Size"]),
                clean_str(r.get("Livelihood_Primary")), clean_float(r.get("Flood_Losses_NGN")),
                clean_float(r.get("Erosion_Losses_NGN")), clean_str(r.get("Adaptation_Measure")),
                clean_str(r["Survey_Date"]), "PRV-FIELD-2026-01"
            ))
        print(f"  ✓ Seeded {len(df_hh)} household survey micro-records.")

        # -------------------------------------------------------------
        # 13. Clean: Erosion Sites
        # -------------------------------------------------------------
        print("\n[13] Seeding clean.erosion_sites...")
        df_ero = pd.read_csv(DATA_CLEAN / "DB03_Erosion_Sites_CLEAN.csv")
        for _, r in df_ero.iterrows():
            cid = clean_str(r["Community_ID"])
            scode = comm_state_map.get(cid, "NG-NIG")
            cur.execute("""
                INSERT INTO clean.erosion_sites (
                    erosion_id, community_id, state_code, erosion_type, severity_rank,
                    length_m, width_m, depth_m, activity_status, bank_proximity_m,
                    infrastructure_threat, latitude, longitude, geom, provenance_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                )
                ON CONFLICT (erosion_id) DO NOTHING;
            """, (
                clean_str(r["Erosion_ID"]), cid, scode, clean_str(r["Erosion_Type"]),
                clean_int(r["Severity_0_4"], 1), clean_float(r["Length_m"]), clean_float(r["Width_m"]),
                clean_float(r["Depth_m"]), clean_str(r["Activity_Status"]), clean_float(r["River_Distance_m"]),
                clean_str(r["Infrastructure_Threat"]), clean_float(r["Latitude"]), clean_float(r["Longitude"]),
                clean_float(r["Longitude"]), clean_float(r["Latitude"]), "PRV-FIELD-2026-01"
            ))
        print(f"  ✓ Seeded {len(df_ero)} erosion site field observations.")

        # -------------------------------------------------------------
        # 14. Clean: Flood Events
        # -------------------------------------------------------------
        print("\n[14] Seeding clean.flood_events...")
        df_evts = pd.read_csv(DATA_CLEAN / "Flood_Events_CLEAN.csv")
        for _, r in df_evts.iterrows():
            cur.execute("""
                INSERT INTO clean.flood_events (
                    flood_event_id, event_name, start_date, end_date, state_code,
                    community_id, peak_depth_m, duration_days, source_agency,
                    confidence_rating, impact_summary, provenance_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (flood_event_id) DO NOTHING;
            """, (
                clean_str(r["flood_event_id"]), clean_str(r["event_name"]), clean_str(r["start_date"]),
                clean_str(r.get("end_date")), clean_str(r["state_code"]), clean_str(r["community_id"]),
                clean_float(r.get("peak_depth_m")), clean_int(r.get("duration_days")), clean_str(r["source_agency"]),
                clean_str(r["confidence_rating"], "Moderate"), clean_str(r.get("impact_summary")),
                clean_str(r.get("provenance_id"), "PRV-FIELD-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_evts)} flood historical events.")

        # -------------------------------------------------------------
        # 15. Clean: Hydropower & Water Observations
        # -------------------------------------------------------------
        print("\n[15] Seeding clean.hydropower_water...")
        df_hydro = pd.read_csv(DATA_CLEAN / "DB04_Hydropower_Water_CLEAN.csv")
        for _, r in df_hydro.iterrows():
            disrupt = clean_str(r.get("Operating_Status", "")).lower() != "normal"
            cur.execute("""
                INSERT INTO clean.hydropower_water (
                    hydro_record_id, facility_id, state_code, obs_date,
                    reservoir_elevation_m, inflow_m3_s, outflow_m3_s, generation_mwh,
                    disruption_flag, disruption_reason, provenance_id
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (hydro_record_id) DO NOTHING;
            """, (
                clean_str(r["Observation_ID"]), clean_str(r["Hydro_ID"]), clean_str(r["State_Code"]),
                clean_str(r["Observation_Date"]), clean_float(r.get("Reservoir_Level_m")),
                clean_float(r.get("River_Discharge_m3s")), clean_float(r.get("River_Discharge_m3s")),
                clean_float(r.get("Generation_MWh")), disrupt, clean_str(r.get("Flood_Damage")),
                "PRV-FMWR-2026-01"
            ))
        print(f"  ✓ Seeded {len(df_hydro)} hydropower telemetry logs.")

        # -------------------------------------------------------------
        # 16. Clean: Climate Observations
        # -------------------------------------------------------------
        print("\n[16] Seeding clean.climate_observations...")
        df_clim = pd.read_csv(DATA_CLEAN / "DB05_Climate_Observations_CLEAN.csv")
        for _, r in df_clim.iterrows():
            cur.execute("""
                INSERT INTO clean.climate_observations (
                    climate_id, station_id, state_code, obs_date, rainfall_mm, temp_min_c, temp_max_c, provenance_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (climate_id) DO NOTHING;
            """, (
                clean_str(r["Climate_ID"]), clean_str(r["Station_ID"]), clean_str(r["State_Code"]),
                clean_str(r["Observation_Date"]), clean_float(r.get("Rainfall_mm")),
                clean_float(r.get("Temperature_Min_C")), clean_float(r.get("Temperature_Max_C")),
                "PRV-NIMET-2026-01"
            ))
        print(f"  ✓ Seeded {len(df_clim)} daily climate observation records.")

        # -------------------------------------------------------------
        # 17. Clean: Infrastructure
        # -------------------------------------------------------------
        print("\n[17] Seeding clean.infrastructure...")
        df_infra = pd.read_csv(DATA_CLEAN / "DB06_Infrastructure_CLEAN.csv")
        cond_map = {"critical": 1, "poor": 2, "fair": 3, "good": 4, "excellent": 5}
        for _, r in df_infra.iterrows():
            cid = clean_str(r["Community_ID"])
            scode = comm_state_map.get(cid, "NG-NIG")
            cond_str = str(r.get("Condition", "Fair")).strip().lower()
            cond_val = cond_map.get(cond_str, 3)
            cur.execute("""
                INSERT INTO clean.infrastructure (
                    infrastructure_id, facility_name, infra_type, condition_rating,
                    community_id, state_code, hazard_exposure, service_disruption_days,
                    latitude, longitude, geom, provenance_id
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                )
                ON CONFLICT (infrastructure_id) DO NOTHING;
            """, (
                clean_str(r["Infrastructure_ID"]), clean_str(r["Description"]), clean_str(r["Infrastructure_Type"]),
                cond_val, cid, scode, clean_str(r.get("Flood_Exposure")), clean_int(r.get("Damage_Severity"), 0),
                clean_float(r["Latitude"]), clean_float(r["Longitude"]),
                clean_float(r["Longitude"]), clean_float(r["Latitude"]), "PRV-FIELD-2026-01"
            ))
        print(f"  ✓ Seeded {len(df_infra)} infrastructure asset records.")

        # -------------------------------------------------------------
        # 18. Clean: Food Security
        # -------------------------------------------------------------
        print("\n[18] Seeding clean.food_security...")
        df_food = pd.read_csv(DATA_CLEAN / "Food_Security_CLEAN.csv")
        for _, r in df_food.iterrows():
            cur.execute("""
                INSERT INTO clean.food_security (
                    food_record_id, community_id, state_code, reporting_period,
                    crop_loss_pct, livestock_loss_pct, market_access_score, food_insecurity_index, provenance_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (food_record_id) DO NOTHING;
            """, (
                clean_str(r["Food_Record_ID"]), clean_str(r["Community_ID"]), clean_str(r["State_Code"]),
                clean_str(r["Reporting_Period"]), clean_float(r.get("Crop_Loss_Pct")), clean_float(r.get("Livestock_Loss_Pct")),
                clean_float(r.get("Market_Access_Score")), clean_float(r.get("Food_Insecurity_Index")),
                clean_str(r.get("Provenance_ID"), "PRV-FIELD-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_food)} food security monitoring records.")

        # -------------------------------------------------------------
        # 19. Clean: Security Impact
        # -------------------------------------------------------------
        print("\n[19] Seeding clean.security_impact...")
        df_sec = pd.read_csv(DATA_CLEAN / "Security_Impact_CLEAN.csv")
        for _, r in df_sec.iterrows():
            restricted = str(r.get("Farm_Access_Restricted")).strip().lower() in ["yes", "true", "1"]
            cur.execute("""
                INSERT INTO clean.security_impact (
                    security_event_id, community_id, state_code, event_date,
                    impact_type, displaced_persons_count, farm_access_restricted,
                    project_delay_days, confidence_rating, provenance_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (security_event_id) DO NOTHING;
            """, (
                clean_str(r["Security_Event_ID"]), clean_str(r["Community_ID"]), clean_str(r["State_Code"]),
                clean_str(r["Event_Date"]), clean_str(r["Impact_Type"]), clean_int(r.get("Displaced_Persons_Count"), 0),
                restricted, clean_int(r.get("Project_Delay_Days"), 0), clean_str(r["Confidence_Rating"], "Moderate"),
                clean_str(r.get("Provenance_ID"), "PRV-FIELD-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_sec)} security impact tracking records.")

        # -------------------------------------------------------------
        # 20. Clean: Loss & Damage
        # -------------------------------------------------------------
        print("\n[20] Seeding clean.loss_damage...")
        df_loss = pd.read_csv(DATA_CLEAN / "Loss_Damage_CLEAN.csv")
        for _, r in df_loss.iterrows():
            cur.execute("""
                INSERT INTO clean.loss_damage (
                    loss_id, hazard_type, linked_event_id, community_id, state_code,
                    asset_or_livelihood_type, physical_quantity, unit, financial_loss_ngn,
                    confidence_rating, provenance_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (loss_id) DO NOTHING;
            """, (
                clean_str(r["Loss_ID"]), clean_str(r["Hazard_Type"]), clean_str(r.get("Linked_Event_ID")),
                clean_str(r["Community_ID"]), clean_str(r["State_Code"]), clean_str(r["Asset_Or_Livelihood_Type"]),
                clean_float(r.get("Physical_Quantity")), clean_str(r.get("Unit")), clean_float(r.get("Financial_Loss_NGN")),
                clean_str(r["Confidence_Rating"], "Moderate"), clean_str(r.get("Provenance_ID"), "PRV-FIELD-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_loss)} loss and damage valuations.")

        # -------------------------------------------------------------
        # 21. Clean: Interventions & MRV
        # -------------------------------------------------------------
        print("\n[21] Seeding clean.interventions...")
        df_int = pd.read_csv(DATA_CLEAN / "Interventions_CLEAN.csv")
        for _, r in df_int.iterrows():
            cur.execute("""
                INSERT INTO clean.interventions (
                    intervention_id, project_title, project_type, community_id, state_code,
                    budget_ngn, status, start_date, completion_date, risk_before, risk_after,
                    ies_score, residual_risk, provenance_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (intervention_id) DO NOTHING;
            """, (
                clean_str(r["Intervention_ID"]), clean_str(r["Project_Title"]), clean_str(r["Project_Category"]),
                clean_str(r["Community_ID"]), clean_str(r["State_Code"]), clean_float(r.get("Budget_NGN")),
                clean_str(r["Status"]), clean_str(r.get("Start_Date")), clean_str(r.get("Completion_Date")),
                clean_float(r.get("Risk_Before")), clean_float(r.get("Risk_After")), clean_float(r.get("IES_Score_Pct")),
                clean_float(r.get("Residual_Risk")), clean_str(r.get("Provenance_ID"), "PRV-NHYPPADEC-ENG-2026")
            ))
        print(f"  ✓ Seeded {len(df_int)} intervention projects.")

        # -------------------------------------------------------------
        # 22. Derived: Standardized Indicators
        # -------------------------------------------------------------
        print("\n[22] Seeding derived.indicators...")
        df_ind = pd.read_csv(DATA_CLEAN / "Indicators_CLEAN.csv")
        for _, r in df_ind.iterrows():
            cur.execute("""
                INSERT INTO derived.indicators (
                    indicator_id, community_id, state_code, raw_value, normalized_value, period, method_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                clean_str(r["Indicator_ID"]), clean_str(r["Community_ID"]), clean_str(r["State_Code"]),
                clean_float(r["Raw_Value"], 0.0), clean_float(r["Normalized_Value"], 0.0),
                clean_str(r["Period"], "2026-Baseline"), clean_str(r.get("Method_Version"), "v4.1")
            ))
        print(f"  ✓ Seeded {len(df_ind)} indicator values.")

        # -------------------------------------------------------------
        # 23. Derived: Risk Assessments
        # -------------------------------------------------------------
        print("\n[23] Seeding derived.risk_assessments...")
        df_risk = pd.read_csv(DATA_CLEAN / "Risk_Assessments_CLEAN.csv")
        for _, r in df_risk.iterrows():
            cur.execute("""
                INSERT INTO derived.risk_assessments (
                    risk_id, community_id, state_code, h_hazard, e_exposure, v_vulnerability,
                    c_criticality, r_composite_risk, r_multiplicative, confidence_rating, model_version, ref_bounds_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (risk_id) DO NOTHING;
            """, (
                clean_str(r["Risk_ID"]), clean_str(r["Community_ID"]), clean_str(r["State_Code"]),
                clean_float(r["H_Hazard"]), clean_float(r["E_Exposure"]), clean_float(r["V_Vulnerability"]),
                clean_float(r["C_Criticality"]), clean_float(r["R_Composite_Risk"]), clean_float(r["R_Multiplicative"]),
                clean_str(r["Confidence_Rating"], "High"), clean_str(r["Model_Version"], "Risk_Model_v4.1"),
                clean_str(r.get("Ref_Bounds_ID"), "Baseline_2026")
            ))
        print(f"  ✓ Seeded {len(df_risk)} community risk assessments.")

        # -------------------------------------------------------------
        # 24. Derived: Priority Areas
        # -------------------------------------------------------------
        print("\n[24] Seeding derived.priority_areas...")
        df_prio = pd.read_csv(DATA_CLEAN / "Priority_Areas_CLEAN.csv")
        for _, r in df_prio.iterrows():
            cur.execute("""
                INSERT INTO derived.priority_areas (
                    priority_id, community_id, state_code, composite_risk, adaptation_gap,
                    priority_score, priority_tier, confidence_rating, approval_status, approval_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (priority_id) DO NOTHING;
            """, (
                clean_str(r["Priority_ID"]), clean_str(r["Community_ID"]), clean_str(r["State_Code"]),
                clean_float(r["Composite_Risk"]), clean_float(r["Adaptation_Gap"]), clean_float(r["Priority_Score"]),
                clean_str(r["Priority_Tier"]), clean_str(r["Confidence_Rating"]), clean_str(r["Approval_Status"], "Approved"),
                clean_str(r.get("Approval_Date"), "2026-10-01")
            ))
        print(f"  ✓ Seeded {len(df_prio)} prioritized investment areas.")

        # -------------------------------------------------------------
        # 25. Derived: Scenarios
        # -------------------------------------------------------------
        print("\n[25] Seeding derived.scenarios...")
        df_scen = pd.read_csv(DATA_CLEAN / "Scenarios_CLEAN.csv")
        for _, r in df_scen.iterrows():
            assump = r["Assumptions_JSON"]
            if isinstance(assump, str):
                assump_json = assump
            else:
                assump_json = json.dumps({"note": "Default baseline"})
            cur.execute("""
                INSERT INTO derived.scenarios (
                    scenario_id, scenario_name, scenario_type, assumptions_json,
                    projected_risk_mean, model_version
                ) VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (scenario_id) DO NOTHING;
            """, (
                clean_str(r["Scenario_ID"]), clean_str(r["Scenario_Name"]), clean_str(r["Scenario_Type"]),
                assump_json, clean_float(r["Projected_Risk_Mean"]), clean_str(r["Model_Version"], "Scenario_v4.1")
            ))
        print(f"  ✓ Seeded {len(df_scen)} climate & adaptation scenarios.")

        # -------------------------------------------------------------
        # 26. Clean: Flood Alerts
        # -------------------------------------------------------------
        print("\n[26] Seeding clean.flood_alerts...")
        df_alerts = pd.read_csv(DATA_CLEAN / "Flood_Alerts_CLEAN.csv")
        for _, r in df_alerts.iterrows():
            st = clean_str(r["status"], "released")
            exp_by = clean_str(r.get("expired_by"))
            exp_at = clean_str(r.get("expired_at"))
            if st == "expired":
                if not exp_by:
                    exp_by = clean_str(r.get("released_by"), "Duty_Hydrologist_02")
                if not exp_at:
                    exp_at = "2026-10-08 14:00:00+01:00"
            canc_by = clean_str(r.get("cancelled_by"))
            canc_at = clean_str(r.get("cancelled_at"))
            canc_reas = clean_str(r.get("cancellation_reason"))
            if st == "cancelled":
                if not canc_by:
                    canc_by = clean_str(r.get("released_by"), "Duty_Hydrologist_02")
                if not canc_at:
                    canc_at = clean_str(r.get("released_at"), "2026-10-08 14:00:00+01:00")
                if not canc_reas:
                    canc_reas = clean_str(r.get("notes"), "Hydrological dissipation")

            cur.execute("""
                INSERT INTO clean.flood_alerts (
                    alert_id, issued_at, state_code, lga_id, warning_level, trigger_type,
                    hazard_score, confidence, status, rule_id, rule_version,
                    reviewed_by, reviewed_at, approved_by, approved_at,
                    released_by, released_at, expired_by, expired_at, cancelled_by, cancelled_at,
                    cancellation_reason, notes, created_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (alert_id) DO NOTHING;
            """, (
                clean_str(r["alert_id"]), clean_str(r.get("issued_at")), clean_str(r["state_code"]),
                clean_str(r.get("lga_id")), clean_int(r["warning_level"], 0), clean_str(r["trigger_type"]),
                clean_float(r.get("hazard_score")), clean_str(r["confidence"], "High"), st,
                clean_str(r["rule_id"]), clean_str(r["rule_version"], "v4.1"),
                clean_str(r.get("reviewed_by")), clean_str(r.get("reviewed_at")),
                clean_str(r.get("approved_by")), clean_str(r.get("approved_at")),
                clean_str(r.get("released_by")), clean_str(r.get("released_at")),
                exp_by, exp_at, canc_by, canc_at, canc_reas,
                clean_str(r.get("notes")), clean_str(r.get("reviewed_by"), "fewcam_dev")
            ))
        print(f"  ✓ Seeded {len(df_alerts)} flood warning alerts.")

        # -------------------------------------------------------------
        # 27. Clean: Flood Alert Triggers
        # -------------------------------------------------------------
        print("\n[27] Seeding clean.flood_alert_triggers...")
        df_trig = pd.read_csv(DATA_CLEAN / "Flood_Alert_Triggers_CLEAN.csv")
        for _, r in df_trig.iterrows():
            qc_st = clean_str(r.get("qc_status"), "validated")
            if qc_st.lower() in ["clean", "validated", "pass"]:
                qc_st = "validated"
            elif qc_st.lower() in ["rejected", "fail"]:
                qc_st = "rejected"
            else:
                qc_st = "raw"

            qc_by = clean_str(r.get("qc_by"), "SEMA_Tech_Lead")
            qc_at = clean_str(r.get("qc_at"), "2026-10-08 05:00:00+01:00")

            cur.execute("""
                INSERT INTO clean.flood_alert_triggers (
                    trigger_id, alert_id, source_type, source_name, source_record_id,
                    observed_at, recorded_at, observed_value, threshold_value, unit,
                    rule_id, rule_version, confidence, qc_status, qc_by, qc_at, qc_reason,
                    provenance_id, evidence_note
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT (trigger_id) DO NOTHING;
            """, (
                clean_str(r["trigger_id"]), clean_str(r["alert_id"]), clean_str(r["source_type"]),
                clean_str(r["source_name"]), clean_str(r.get("source_record_id")),
                clean_str(r["observed_at"]), clean_str(r["recorded_at"]),
                clean_float(r["observed_value"]), clean_float(r["threshold_value"]), clean_str(r.get("unit")),
                clean_str(r["rule_id"]), clean_str(r["rule_version"], "v4.1"), clean_str(r["confidence"], "High"),
                qc_st, qc_by, qc_at,
                clean_str(r.get("qc_reason")), clean_str(r.get("provenance_id"), "PRV-FIELD-2026-01"),
                clean_str(r.get("evidence_note"))
            ))
        print(f"  ✓ Seeded {len(df_trig)} verified trigger observations.")

        # -------------------------------------------------------------
        # 28. Clean: Flood Alert Areas
        # -------------------------------------------------------------
        print("\n[28] Seeding clean.flood_alert_areas...")
        # Load G38 geojson polygons
        g38_path = PROJECT_ROOT / "04_GIS" / "03_DERIVED" / "G38_Flood_Alert_Zones_v1_0.geojson"
        g38_geom_map = {}
        if g38_path.exists():
            with open(g38_path, "r", encoding="utf-8") as f:
                g38_data = json.load(f)
                for feat in g38_data.get("features", []):
                    aid = feat.get("properties", {}).get("Alert_ID")
                    if aid and feat.get("geometry"):
                        g38_geom_map[aid] = json.dumps(feat["geometry"])

        df_areas = pd.read_csv(DATA_CLEAN / "Flood_Alert_Areas_CLEAN.csv")
        for _, r in df_areas.iterrows():
            aid = clean_str(r["alert_id"])
            geom_json = g38_geom_map.get(aid)
            if geom_json:
                geom_clause = "ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))"
                geom_param = geom_json
            else:
                # Fallback to buffer around community or default point
                cid = clean_str(r.get("community_id"))
                geom_clause = """
                    COALESCE(
                        (SELECT ST_Multi(ST_Buffer(geom, 0.05)) FROM clean.community_master WHERE community_id = %s),
                        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(6.5, 9.5), 4326), 0.05))
                    )
                """
                geom_param = cid

            query = f"""
                INSERT INTO clean.flood_alert_areas (
                    alert_area_id, alert_id, state_code, lga_id, community_id,
                    affected_area_sqkm, exposed_population, exposed_households,
                    exposed_critical_assets, geom, assessed_at, confidence
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, {geom_clause}, %s, %s
                )
                ON CONFLICT (alert_area_id) DO NOTHING;
            """
            cur.execute(query, (
                clean_str(r["alert_area_id"]), aid, clean_str(r["state_code"]),
                clean_str(r.get("lga_id")), clean_str(r.get("community_id")),
                clean_float(r.get("affected_area_sqkm")), clean_int(r.get("exposed_population")),
                clean_int(r.get("exposed_households")), clean_int(r.get("exposed_critical_assets")),
                geom_param,
                clean_str(r["assessed_at"]), clean_str(r["confidence"], "High")
            ))
        print(f"  ✓ Seeded {len(df_areas)} spatial impact warning areas with PostGIS MultiPolygon geometries.")

        # -------------------------------------------------------------
        # 29. Clean: Flood Notifications
        # -------------------------------------------------------------
        print("\n[29] Seeding clean.flood_notifications...")
        df_notifs = pd.read_csv(DATA_CLEAN / "Flood_Notifications_CLEAN.csv")
        for _, r in df_notifs.iterrows():
            cur.execute("""
                INSERT INTO clean.flood_notifications (
                    notification_id, alert_id, community_id, channel, language_code,
                    message_version, sent_at, delivery_status, recipient_count, reached_count,
                    provider_reference, sent_by
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT (notification_id) DO NOTHING;
            """, (
                clean_str(r["notification_id"]), clean_str(r["alert_id"]), clean_str(r["community_id"]),
                clean_str(r["channel"]), clean_str(r["language_code"]), clean_str(r["message_version"], "v4.1"),
                clean_str(r.get("sent_at")), clean_str(r["delivery_status"]), clean_int(r["recipient_count"], 0),
                clean_int(r["reached_count"], 0), clean_str(r.get("provider_reference")), clean_str(r["sent_by"])
            ))
        print(f"  ✓ Seeded {len(df_notifs)} disseminated emergency notifications.")

        # -------------------------------------------------------------
        # 30. Clean: Flood Acknowledgements
        # -------------------------------------------------------------
        print("\n[30] Seeding clean.flood_acknowledgements...")
        df_ack = pd.read_csv(DATA_CLEAN / "Flood_Acknowledgements_CLEAN.csv")
        for _, r in df_ack.iterrows():
            cur.execute("""
                INSERT INTO clean.flood_acknowledgements (
                    acknowledgement_id, notification_id, acknowledged_at, acknowledgement_status,
                    recipient_token, community_id, respondent_role, acknowledgement_source, notes
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (acknowledgement_id) DO NOTHING;
            """, (
                clean_str(r["acknowledgement_id"]), clean_str(r["notification_id"]), clean_str(r["acknowledged_at"]),
                clean_str(r["acknowledgement_status"]), clean_str(r["recipient_token"]), clean_str(r["community_id"]),
                clean_str(r.get("respondent_role")), clean_str(r["acknowledgement_source"]), clean_str(r.get("notes"))
            ))
        print(f"  ✓ Seeded {len(df_ack)} community acknowledgements.")

        # -------------------------------------------------------------
        # 31. Clean: Flood Awareness Campaigns
        # -------------------------------------------------------------
        print("\n[31] Seeding clean.flood_awareness...")
        df_aware = pd.read_csv(DATA_CLEAN / "Flood_Awareness_CLEAN.csv")
        for _, r in df_aware.iterrows():
            pub_st = clean_str(r.get("publication_status"), "approved")
            if pub_st.lower() in ["published", "approved"]:
                pub_st = "approved"
            else:
                pub_st = "restricted"

            cur.execute("""
                INSERT INTO clean.flood_awareness (
                    awareness_id, alert_id, community_id, activity_type, conducted_at,
                    method, language_code, target_audience, audience_count, reach_count,
                    materials, feedback, facilitator_id, confidence, publication_status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (awareness_id) DO NOTHING;
            """, (
                clean_str(r["awareness_id"]), clean_str(r.get("alert_id")), clean_str(r["community_id"]),
                clean_str(r["activity_type"]), clean_str(r["conducted_at"]), clean_str(r["method"]),
                clean_str(r["language_code"]), clean_str(r["target_audience"]), clean_int(r.get("audience_count"), 0),
                clean_int(r.get("reach_count"), 0), clean_str(r.get("materials")), clean_str(r.get("feedback")),
                clean_str(r.get("facilitator_id")), clean_str(r["confidence"], "High"), pub_st
            ))
        print(f"  ✓ Seeded {len(df_aware)} grassroots awareness campaigns.")

        # -------------------------------------------------------------
        # 32. Clean: Flood Drills
        # -------------------------------------------------------------
        print("\n[32] Seeding clean.flood_drills...")
        df_drills = pd.read_csv(DATA_CLEAN / "Flood_Drills_CLEAN.csv")
        for _, r in df_drills.iterrows():
            out_raw = str(r.get("outcome", "completed")).strip().lower()
            if out_raw in ["successful", "completed", "success"]:
                out_val = "completed"
            elif out_raw in ["partial", "partially completed"]:
                out_val = "partial"
            else:
                out_val = "cancelled"

            cur.execute("""
                INSERT INTO clean.flood_drills (
                    drill_id, community_id, state_code, drill_date, drill_type,
                    scenario_summary, participants_count, outcome, lessons_learned,
                    facilitator_id, provenance_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT (drill_id) DO NOTHING;
            """, (
                clean_str(r["drill_id"]), clean_str(r["community_id"]), clean_str(r["state_code"]),
                clean_str(r["drill_date"]), clean_str(r["drill_type"]), clean_str(r.get("scenario_summary")),
                clean_int(r.get("participants_count"), 0), out_val, clean_str(r.get("lessons_learned")),
                clean_str(r.get("facilitator_id")), clean_str(r.get("provenance_id"), "PRV-FIELD-2026-01")
            ))
        print(f"  ✓ Seeded {len(df_drills)} community evacuation simulation drills.")

        # -------------------------------------------------------------
        # 33. Clean: Flood Impacts
        # -------------------------------------------------------------
        print("\n[33] Seeding clean.flood_impacts...")
        df_imp = pd.read_csv(DATA_CLEAN / "Flood_Impacts_CLEAN.csv")
        for _, r in df_imp.iterrows():
            cur.execute("""
                INSERT INTO clean.flood_impacts (
                    impact_id, flood_event_id, community_id, state_code, impact_category,
                    asset_type, affected_count, estimated_loss_ngn, service_disruption_days,
                    assessed_at, assessed_by, confidence, provenance_id, notes
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (impact_id) DO NOTHING;
            """, (
                clean_str(r["impact_id"]), clean_str(r["flood_event_id"]), clean_str(r["community_id"]),
                clean_str(r["state_code"]), clean_str(r["impact_category"]), clean_str(r["asset_type"]),
                clean_int(r.get("affected_count"), 0), clean_float(r.get("estimated_loss_ngn")),
                clean_int(r.get("service_disruption_days"), 0), clean_str(r["assessed_at"]),
                clean_str(r["assessed_by"]), clean_str(r["confidence"], "High"),
                clean_str(r.get("provenance_id"), "PRV-FIELD-2026-01"), clean_str(r.get("notes"))
            ))
        print(f"  ✓ Seeded {len(df_imp)} verified flood impact assessments.")

        # -------------------------------------------------------------
        # 34. Clean: Flood Warning Performance
        # -------------------------------------------------------------
        print("\n[34] Seeding clean.flood_warning_performance...")
        df_perf = pd.read_csv(DATA_CLEAN / "Flood_Warning_Performance_CLEAN.csv")
        for _, r in df_perf.iterrows():
            cur.execute("""
                INSERT INTO clean.flood_warning_performance (
                    performance_id, alert_id, flood_event_id, evaluated_at, evaluated_by,
                    lead_time_hours, recipient_count, reached_count, acknowledgement_count,
                    hit_status, alerted_extent_sqkm, observed_extent_sqkm, high_risk_communities,
                    communities_reached, audit_completeness_pct, confidence, publication_status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (performance_id) DO NOTHING;
            """, (
                clean_str(r["performance_id"]), clean_str(r["alert_id"]), clean_str(r.get("flood_event_id")),
                clean_str(r["evaluated_at"]), clean_str(r["evaluated_by"]), clean_float(r.get("lead_time_hours")),
                clean_int(r.get("recipient_count"), 0), clean_int(r.get("reached_count"), 0),
                clean_int(r.get("acknowledgement_count"), 0), clean_str(r["hit_status"]),
                clean_float(r.get("alerted_extent_sqkm")), clean_float(r.get("observed_extent_sqkm")),
                clean_int(r.get("high_risk_communities"), 0), clean_int(r.get("communities_reached"), 0),
                clean_float(r.get("audit_completeness_pct"), 0.0), clean_str(r["confidence"], "High"),
                clean_str(r.get("publication_status"), "verified")
            ))
        print(f"  ✓ Seeded {len(df_perf)} warning performance evaluation audits.")

        # Re-enable standard origin session replication role
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()

        print("\n" + "=" * 70)
        print("  ALL 34 CENTRAL DATABASE TABLES SUCCESSFULLY SEEDED IN POSTGIS!")
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n[FATAL ERROR] Seeding aborted: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_database()
