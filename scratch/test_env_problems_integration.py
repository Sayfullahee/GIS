import sys
import json
from pathlib import Path

BASE_DIR = Path(r"c:\xampp\htdocs\GIS")
sys.path.insert(0, str(BASE_DIR / "05_Analysis" / "02_SCRIPTS"))
sys.path.insert(0, str(BASE_DIR / "07_Decision_Support" / "02_Dashboards"))

import config as cfg
import pandas as pd
from app import app, get_environmental_problems, get_environmental_problems_spatial, get_environmental_problem_detail, list_states

def run_tests():
    print("--- 1. Testing LKP_EnvironmentalProblems.csv ---")
    ep_file = cfg.DATA_LOOKUPS / "LKP_EnvironmentalProblems.csv"
    assert ep_file.exists(), "LKP_EnvironmentalProblems.csv missing!"
    df_ep = pd.read_csv(ep_file)
    print(f"Loaded {len(df_ep)} environmental problems.")
    assert len(df_ep) == 14, f"Expected 14 problems, got {len(df_ep)}"
    expected_problems = [
        "Air Pollution", "Climate Change Impacts", "Deforestation", "Desertification",
        "Drought", "Ecological Conflict", "Erosion", "Flooding",
        "Lead Poisoning", "Oil Spillage", "Solid Waste Management", "Water Pollution",
        "Food Security", "Bandit Attack"
    ]
    for p in expected_problems:
        assert p in df_ep["Problem_Name"].values, f"Missing {p} in lookup!"
    print("All 14 canonical environmental & security problems verified.")

    print("\n--- 2. Testing LKP_State_EnvironmentalProblems.csv (54 incidents) ---")
    sep_file = cfg.DATA_LOOKUPS / "LKP_State_EnvironmentalProblems.csv"
    assert sep_file.exists(), "LKP_State_EnvironmentalProblems.csv missing!"
    df_sep = pd.read_csv(sep_file)
    print(f"Loaded {len(df_sep)} state problem records.")
    assert len(df_sep) == 54, f"Expected 54 records, got {len(df_sep)}"
    
    # Check Bandit Attack & Food Security presence
    bandit_records = df_sep[df_sep["Problem_Code"] == "BANDIT_ATTACK"]
    food_records = df_sep[df_sep["Problem_Code"] == "FOOD_SECURITY"]
    print(f"Bandit Attack incidents: {len(bandit_records)}")
    print(f"Food Security incidents: {len(food_records)}")
    assert len(bandit_records) >= 5, "Expected at least 5 Bandit Attack records!"
    assert len(food_records) >= 5, "Expected at least 5 Food Security records!"

    ada_records = df_sep[df_sep["State_Code"] == "NG-ADA"]
    print(f"Adamawa records: {len(ada_records)}")
    assert len(ada_records) >= 2, "Adamawa must have at least Deforestation and Erosion!"
    ada_problems = ada_records["Problem_Name"].tolist()
    assert "Deforestation" in ada_problems, "Adamawa missing Deforestation!"
    assert "Erosion" in ada_problems, "Adamawa missing Erosion!"
    print("State multi-hazard incident distribution verified.")

    print("\n--- 3. Testing G65 GeoJSON Spatial Layer ---")
    g65_file = cfg.GIS_DERIVED / "G65_EnvironmentalProblems.geojson"
    assert g65_file.exists(), "G65 GeoJSON missing!"
    with open(g65_file, "r", encoding="utf-8") as f:
        g65_data = json.load(f)
    features = g65_data.get("features", [])
    print(f"G65 contains {len(features)} spatial features.")
    assert len(features) == len(df_sep), "GeoJSON feature count mismatch!"
    ada_feats = [f for f in features if f["properties"]["state_name"] == "Adamawa"]
    assert len(ada_feats) >= 2, "GeoJSON missing Adamawa features!"
    print("G65 Spatial layer validated.")

    print("\n--- 4. Testing API Endpoints ---")
    ep_resp = get_environmental_problems()
    assert ep_resp["total"] == 14
    print("GET /api/environmental-problems -> OK (14 items)")

    spatial_resp = get_environmental_problems_spatial()
    assert len(spatial_resp["features"]) == len(features)
    print(f"GET /api/environmental-problems/spatial -> OK ({len(features)} features)")

    bandit_resp = get_environmental_problem_detail("BANDIT_ATTACK")
    assert bandit_resp["incident_count"] == len(bandit_records)
    print(f"GET /api/environmental-problems/BANDIT_ATTACK -> OK ({bandit_resp['incident_count']} incidents)")

    food_resp = get_environmental_problem_detail("FOOD_SECURITY")
    assert food_resp["incident_count"] == len(food_records)
    print(f"GET /api/environmental-problems/FOOD_SECURITY -> OK ({food_resp['incident_count']} incidents)")

    states_resp = list_states()
    states = states_resp["states"]
    has_ada = any(s["State_Name"] == "Adamawa" for s in states)
    assert has_ada, "Adamawa not present in /api/states!"
    print(f"GET /api/states -> OK ({len(states)} states, Adamawa confirmed)")

    print("\nALL 14 MULTI-HAZARD VERIFICATION CHECKS PASSED SUCCESSFULLY! ✅")

if __name__ == "__main__":
    run_tests()

