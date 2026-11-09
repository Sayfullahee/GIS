"""
================================================================================
CHER-CDSS: AI Dam Water Level Monitoring & Agro-Drought Harvest Loss Engine
================================================================================
Module: ai_drought_harvest_service.py
Directory: 07_Decision_Support/02_Dashboards/
Author: N-HYPPADEC CDSS Engineering Team
Standard: CHER-CDSS Master Implementation Scaffold v4.2
Purpose:
  Provides dual prescriptive AI capabilities:
    1. Hydro-AI Dam Water Level & Hydrostatic Monitor:
       Tracks live reservoir head elevations (m), usable capacity (%),
       freeboard safety margins, and dead storage vs. spillway flood risks
       across all major hydroelectric and multipurpose dams in member states.
    2. Agro-Drought AI & State Harvest Loss Predictor:
       Computes agro-meteorological precipitation deficits across all 10 member
       states, uses FAO-33 water production functions to calculate predicted
       yield reductions across 5 regional staple crops (Maize, Sorghum, Millet,
       Rice, Yam), and ranks states by drought harvest vulnerability to guide
       emergency food reserves and dam irrigation releases.
================================================================================
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("cher_cdss.drought_harvest_service")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_CLEAN = BASE_DIR / "03_Data" / "CLEAN"

# ---------------------------------------------------------------------------
# 1. Authoritative Dam Catalogue & Hydrostatic Baselines
# ---------------------------------------------------------------------------
TARGET_DAMS_CATALOGUE = {
    "DAM-NIG-01": {
        "dam_name": "Kainji Hydroelectric Dam",
        "state_code": "NG-NIG",
        "state_name": "Niger",
        "river": "Niger River",
        "installed_capacity_mw": 760.0,
        "purpose": "Hydropower Generation, Irrigation, Flood Control",
        "full_reservoir_level_m": 141.83,
        "min_operating_level_m": 135.00,
        "crest_elevation_m": 143.50,
        "storage_capacity_mcm": 15000.0,  # Million Cubic Meters
        "current_water_level_m": 139.40,
        "inflow_m3s": 1280.0,
        "outflow_m3s": 1150.0,
        "irrigation_scheme": "Kainji-Jebba Floodplain Agricultural Basin"
    },
    "DAM-NIG-02": {
        "dam_name": "Jebba Hydroelectric Dam",
        "state_code": "NG-NIG",
        "state_name": "Niger / Kwara Border",
        "river": "Niger River",
        "installed_capacity_mw": 578.0,
        "purpose": "Run-of-River Hydropower, River Navigation",
        "full_reservoir_level_m": 103.00,
        "min_operating_level_m": 99.00,
        "crest_elevation_m": 104.50,
        "storage_capacity_mcm": 3880.0,
        "current_water_level_m": 101.80,
        "inflow_m3s": 1420.0,
        "outflow_m3s": 1380.0,
        "irrigation_scheme": "Bacita & Patigi Sugar Cane & Rice Schemes"
    },
    "DAM-NIG-03": {
        "dam_name": "Shiroro Hydroelectric Dam",
        "state_code": "NG-NIG",
        "state_name": "Niger",
        "river": "Kaduna River",
        "installed_capacity_mw": 600.0,
        "purpose": "Hydropower, Irrigation, Fisheries",
        "full_reservoir_level_m": 382.00,
        "min_operating_level_m": 360.00,
        "crest_elevation_m": 384.50,
        "storage_capacity_mcm": 7000.0,
        "current_water_level_m": 376.50,
        "inflow_m3s": 980.0,
        "outflow_m3s": 850.0,
        "irrigation_scheme": "Kaduna River Downstream Alluvial Plains"
    },
    "DAM-NIG-04": {
        "dam_name": "Zungeru Hydroelectric Dam",
        "state_code": "NG-NIG",
        "state_name": "Niger",
        "river": "Kaduna River",
        "installed_capacity_mw": 700.0,
        "purpose": "Hydropower Generation, Agricultural Water Management",
        "full_reservoir_level_m": 230.00,
        "min_operating_level_m": 215.00,
        "crest_elevation_m": 233.00,
        "storage_capacity_mcm": 10400.0,
        "current_water_level_m": 226.30,
        "inflow_m3s": 1100.0,
        "outflow_m3s": 920.0,
        "irrigation_scheme": "Wushishi & Tegina Irrigation Corridor"
    },
    "DAM-GOM-01": {
        "dam_name": "Dadin Kowa Multipurpose Dam",
        "state_code": "NG-GOM",
        "state_name": "Gombe",
        "river": "Gongola River (Upper Benue Basin)",
        "installed_capacity_mw": 40.0,
        "purpose": "Large-Scale Agrarian Irrigation, Water Supply, Hydropower",
        "full_reservoir_level_m": 332.00,
        "min_operating_level_m": 310.00,
        "crest_elevation_m": 335.00,
        "storage_capacity_mcm": 2800.0,
        "current_water_level_m": 321.40,
        "inflow_m3s": 410.0,
        "outflow_m3s": 390.0,
        "irrigation_scheme": "Yamaltu-Deba 30,000 Ha Irrigation Project"
    },
    "DAM-TAR-01": {
        "dam_name": "Kashimbila Multipurpose Dam",
        "state_code": "NG-TAR",
        "state_name": "Taraba",
        "river": "Katsina-Ala River (Benue Basin)",
        "installed_capacity_mw": 40.0,
        "purpose": "Disaster Buffering (Lake Nyos), Hydropower, Irrigation",
        "full_reservoir_level_m": 240.00,
        "min_operating_level_m": 220.00,
        "crest_elevation_m": 243.00,
        "storage_capacity_mcm": 500.0,
        "current_water_level_m": 234.80,
        "inflow_m3s": 650.0,
        "outflow_m3s": 610.0,
        "irrigation_scheme": "Takum & Donga Agro-Industrial Farmlands"
    },
    "DAM-ADA-01": {
        "dam_name": "Kiri Multipurpose Dam",
        "state_code": "NG-ADA",
        "state_name": "Adamawa",
        "river": "Banjiram River / Gongola Basin",
        "installed_capacity_mw": 20.0,
        "purpose": "Savannah Sugar Irrigation & Downstream Flood Buffering",
        "full_reservoir_level_m": 170.50,
        "min_operating_level_m": 160.00,
        "crest_elevation_m": 173.00,
        "storage_capacity_mcm": 615.0,
        "current_water_level_m": 165.20,
        "inflow_m3s": 280.0,
        "outflow_m3s": 250.0,
        "irrigation_scheme": "Savannah Sugar Company Estate (6,000 Ha)"
    },
    "DAM-KEB-01": {
        "dam_name": "Bakolori Irrigation Reservoir (Basin Influence)",
        "state_code": "NG-KEB",
        "state_name": "Kebbi / Sokoto Basin",
        "river": "Sokoto River / Rima Basin",
        "installed_capacity_mw": 3.0,
        "purpose": "Large-Scale Rice & Wheat Irrigation Supply",
        "full_reservoir_level_m": 310.00,
        "min_operating_level_m": 295.00,
        "crest_elevation_m": 312.50,
        "storage_capacity_mcm": 450.0,
        "current_water_level_m": 301.60,
        "inflow_m3s": 190.0,
        "outflow_m3s": 180.0,
        "irrigation_scheme": "Argungu & Yauri Riverine Rice Polders"
    },
    "DAM-NAS-01": {
        "dam_name": "Doma Irrigation Dam",
        "state_code": "NG-NAS",
        "state_name": "Nasarawa",
        "river": "Mada River Tributary",
        "installed_capacity_mw": 5.0,
        "purpose": "Municipal Water Supply, Irrigation",
        "full_reservoir_level_m": 185.00,
        "min_operating_level_m": 170.00,
        "crest_elevation_m": 188.00,
        "storage_capacity_mcm": 120.0,
        "current_water_level_m": 178.40,
        "inflow_m3s": 85.0,
        "outflow_m3s": 75.0,
        "irrigation_scheme": "Doma Basin Vegetable & Rice Scheme"
    }
}

# ---------------------------------------------------------------------------
# 2. Agro-Ecological State Profiles & Crop Yield Sensitivities
# ---------------------------------------------------------------------------
# FAO-33 Water Production Function Crop Yield Response Factors (Ky)
# Ky > 1: highly sensitive to water deficit (heavy yield penalty)
# Ky < 1: drought tolerant
CROP_YIELD_SENSITIVITIES = {
    "Maize": {
        "ky": 1.25,
        "optimal_water_mm": 550.0,
        "critical_growth_stage": "Tasseling and Grain Filling",
        "staple_tier": "Major Cereal Food Security Grain"
    },
    "Rice": {
        "ky": 1.20,
        "optimal_water_mm": 650.0,
        "critical_growth_stage": "Panicle Initiation and Heading",
        "staple_tier": "National Commercial and Household Staple"
    },
    "Yam": {
        "ky": 1.00,
        "optimal_water_mm": 500.0,
        "critical_growth_stage": "Tuber Bulking",
        "staple_tier": "Riverine Guinea Savanna Tuber"
    },
    "Sorghum": {
        "ky": 0.90,
        "optimal_water_mm": 450.0,
        "critical_growth_stage": "Flowering",
        "staple_tier": "Drought-Hardy Dryland Grain"
    },
    "Millet": {
        "ky": 0.85,
        "optimal_water_mm": 350.0,
        "critical_growth_stage": "Booting and Anthesis",
        "staple_tier": "Semi-Arid Arid Frontier Staple"
    }
}

# Member state agro-meteorological baselines (grounded in DB05 & Food Security data)
STATE_AGRO_PROFILES = {
    "NG-GOM": {
        "name": "Gombe",
        "zone": "Sudan / Sahel Savanna",
        "seasonal_normal_rain_mm": 120.0,
        "current_observed_rain_mm": 68.5,   # Drought stress scenario
        "farming_population": 1850000,
        "cultivated_hectares": 340000,
        "dominant_crops": ["Millet", "Sorghum", "Maize", "Rice"],
        "dams_linked": ["DAM-GOM-01"]
    },
    "NG-KEB": {
        "name": "Kebbi",
        "zone": "Sudan Savanna (Rima Valley)",
        "seasonal_normal_rain_mm": 145.0,
        "current_observed_rain_mm": 92.0,
        "farming_population": 2900000,
        "cultivated_hectares": 580000,
        "dominant_crops": ["Rice", "Millet", "Sorghum", "Maize"],
        "dams_linked": ["DAM-KEB-01", "DAM-NIG-01"]
    },
    "NG-KAD": {
        "name": "Kaduna",
        "zone": "Northern Guinea Savanna",
        "seasonal_normal_rain_mm": 125.0,
        "current_observed_rain_mm": 86.4,
        "farming_population": 3400000,
        "cultivated_hectares": 620000,
        "dominant_crops": ["Maize", "Sorghum", "Rice", "Yam"],
        "dams_linked": ["DAM-NIG-03"]
    },
    "NG-NIG": {
        "name": "Niger",
        "zone": "Southern Guinea Savanna",
        "seasonal_normal_rain_mm": 144.0,
        "current_observed_rain_mm": 115.2,
        "farming_population": 3600000,
        "cultivated_hectares": 750000,
        "dominant_crops": ["Rice", "Yam", "Maize", "Sorghum"],
        "dams_linked": ["DAM-NIG-01", "DAM-NIG-02", "DAM-NIG-03", "DAM-NIG-04"]
    },
    "NG-KWA": {
        "name": "Kwara",
        "zone": "Guinea Savanna Transition",
        "seasonal_normal_rain_mm": 118.0,
        "current_observed_rain_mm": 96.0,
        "farming_population": 1950000,
        "cultivated_hectares": 320000,
        "dominant_crops": ["Cassava", "Yam", "Rice", "Maize"],
        "dams_linked": ["DAM-NIG-02"]
    },
    "NG-PLA": {
        "name": "Plateau",
        "zone": "Montane / Northern Guinea Savanna",
        "seasonal_normal_rain_mm": 128.0,
        "current_observed_rain_mm": 105.0,
        "farming_population": 2100000,
        "cultivated_hectares": 290000,
        "dominant_crops": ["Maize", "Irish Potato", "Sorghum", "Vegetables"],
        "dams_linked": []
    },
    "NG-NAS": {
        "name": "Nasarawa",
        "zone": "Southern Guinea Savanna",
        "seasonal_normal_rain_mm": 130.0,
        "current_observed_rain_mm": 110.5,
        "farming_population": 1650000,
        "cultivated_hectares": 310000,
        "dominant_crops": ["Yam", "Rice", "Maize", "Cassava"],
        "dams_linked": ["DAM-NAS-01"]
    },
    "NG-KOG": {
        "name": "Kogi",
        "zone": "Riverine Confluence Guinea Savanna",
        "seasonal_normal_rain_mm": 128.0,
        "current_observed_rain_mm": 112.0,
        "farming_population": 2400000,
        "cultivated_hectares": 390000,
        "dominant_crops": ["Yam", "Cassava", "Rice", "Maize"],
        "dams_linked": ["DAM-NIG-02"]
    },
    "NG-TAR": {
        "name": "Taraba",
        "zone": "Benue Valley & Mambilla Highlands",
        "seasonal_normal_rain_mm": 122.0,
        "current_observed_rain_mm": 108.0,
        "farming_population": 1900000,
        "cultivated_hectares": 440000,
        "dominant_crops": ["Rice", "Yam", "Maize", "Sorghum"],
        "dams_linked": ["DAM-TAR-01"]
    },
    "NG-BEN": {
        "name": "Benue",
        "zone": "Southern Guinea Savanna (Food Basket)",
        "seasonal_normal_rain_mm": 132.0,
        "current_observed_rain_mm": 122.0,
        "farming_population": 3800000,
        "cultivated_hectares": 680000,
        "dominant_crops": ["Yam", "Rice", "Soybeans", "Maize"],
        "dams_linked": ["DAM-TAR-01"]
    },
    "NG-ADA": {
        "name": "Adamawa",
        "zone": "Upper Benue Valley",
        "seasonal_normal_rain_mm": 120.0,
        "current_observed_rain_mm": 88.0,
        "farming_population": 2200000,
        "cultivated_hectares": 420000,
        "dominant_crops": ["Sorghum", "Maize", "Rice", "Groundnut"],
        "dams_linked": ["DAM-ADA-01"]
    }
}


# ---------------------------------------------------------------------------
# 3. Core AI Functions: Water Level & Hydrostatic Monitoring
# ---------------------------------------------------------------------------
def get_dam_water_levels_overview(
    dam_id_filter: Optional[str] = None,
    water_level_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates real-time water levels, usable capacity (%), freeboard safety,
    and classifies both Flood Spillway Exceedance and Dead Storage Drought Risks
    across all strategic hydroelectric & irrigation dams.
    """
    dams_list = []
    
    for d_id, meta in TARGET_DAMS_CATALOGUE.items():
        if dam_id_filter and d_id != dam_id_filter:
            continue

        curr_lvl = water_level_override if (dam_id_filter and d_id == dam_id_filter and water_level_override is not None) else meta["current_water_level_m"]
        frl = meta["full_reservoir_level_m"]
        mol = meta["min_operating_level_m"]
        crest = meta["crest_elevation_m"]

        # 1. Usable Active Storage Percentage
        usable_span = max(0.1, frl - mol)
        storage_pct = round(max(0.0, min(100.0, ((curr_lvl - mol) / usable_span) * 100.0)), 1)

        # 2. Freeboard Headroom (m)
        freeboard_m = round(max(0.0, crest - curr_lvl), 2)

        # 3. Hydrostatic Risk Tier
        if curr_lvl >= frl - 0.4:
            status = "CRITICAL_SPILLWAY_FLOOD_RISK"
            status_desc = "Reservoir near maximum retention capacity. Imminent spillway discharge."
            risk_color = "#DC2626"
            action_code = "SPILL_WARNING"
        elif curr_lvl >= frl - 1.2:
            status = "HIGH_WATER_SURCHARGE"
            status_desc = "Water level high; buffer capacity narrowing."
            risk_color = "#F59E0B"
            action_code = "WATCH_DISCHARGE"
        elif curr_lvl <= mol + 0.8:
            status = "DEAD_STORAGE_DROUGHT_RISK"
            status_desc = "Reservoir depleted near dead storage threshold. Irrigation & power intake threatened."
            risk_color = "#991B1B"
            action_code = "DROUGHT_WATER_RESTRICTION"
        elif curr_lvl <= mol + 2.5:
            status = "LOW_STORAGE_DROUGHT_STRESS"
            status_desc = "Sub-optimal reservoir level. Agrarian irrigation rationing recommended."
            risk_color = "#D97706"
            action_code = "IRRIGATION_RATIONING"
        else:
            status = "OPTIMAL_CONSERVATION_POOL"
            status_desc = "Balanced hydrostatic head. Safe for full power generation & controlled irrigation."
            risk_color = "#10B981"
            action_code = "NORMAL_OPERATIONS"

        # 4. Usable Active Storage (MCM)
        usable_mcm = round(meta["storage_capacity_mcm"] * (storage_pct / 100.0), 1)

        dams_list.append({
            "dam_id": d_id,
            "dam_name": meta["dam_name"],
            "state_code": meta["state_code"],
            "state_name": meta["state_name"],
            "river": meta["river"],
            "installed_capacity_mw": meta["installed_capacity_mw"],
            "purpose": meta["purpose"],
            "elevation_metrics": {
                "current_water_level_m": curr_lvl,
                "full_reservoir_level_m": frl,
                "min_operating_level_m": mol,
                "crest_elevation_m": crest,
                "freeboard_headroom_m": freeboard_m
            },
            "storage_metrics": {
                "active_storage_pct": storage_pct,
                "usable_storage_mcm": usable_mcm,
                "total_storage_capacity_mcm": meta["storage_capacity_mcm"]
            },
            "flow_rates": {
                "inflow_m3s": meta["inflow_m3s"],
                "outflow_m3s": meta["outflow_m3s"],
                "net_accumulation_m3s": round(meta["inflow_m3s"] - meta["outflow_m3s"], 1)
            },
            "irrigation_scheme": meta["irrigation_scheme"],
            "hydrostatic_status": status,
            "status_description": status_desc,
            "risk_color": risk_color,
            "action_code": action_code
        })

    return {
        "status": "OPERATIONAL",
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "total_dams_monitored": len(dams_list),
        "dams": dams_list
    }


# ---------------------------------------------------------------------------
# 4. Core AI Functions: State Rainfall & Drought Harvest Loss Prediction
# ---------------------------------------------------------------------------
def compute_state_drought_and_harvest_loss(
    simulated_state_deficits: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Computes precipitation deficits, agricultural drought severity classifications,
    and predicts crop yield losses across Maize, Sorghum, Millet, Rice, and Yam
    using FAO-33 water production functions. Ranks states from most to least vulnerable.
    """
    results = []

    for s_code, prof in STATE_AGRO_PROFILES.items():
        norm_rain = prof["seasonal_normal_rain_mm"]
        
        # Allow interactive stress simulation override if provided
        if simulated_state_deficits and s_code in simulated_state_deficits:
            obs_rain = max(0.0, norm_rain * (1.0 - (simulated_state_deficits[s_code] / 100.0)))
        else:
            obs_rain = prof["current_observed_rain_mm"]

        # Rainfall Deficit Percentage
        rain_deficit_pct = round(max(0.0, ((norm_rain - obs_rain) / norm_rain) * 100.0), 1)

        # Agricultural Drought Classification
        if rain_deficit_pct >= 55.0:
            drought_class = "EXTREME_AGRICULTURAL_DROUGHT"
            ipc_phase = "IPC Phase 3 (Crisis)"
            risk_color = "#DC2626"
        elif rain_deficit_pct >= 40.0:
            drought_class = "SEVERE_AGRICULTURAL_DROUGHT"
            ipc_phase = "IPC Phase 3 (Crisis)"
            risk_color = "#EA580C"
        elif rain_deficit_pct >= 25.0:
            drought_class = "MODERATE_AGRICULTURAL_DROUGHT"
            ipc_phase = "IPC Phase 2 (Stressed)"
            risk_color = "#D97706"
        elif rain_deficit_pct >= 12.0:
            drought_class = "MILD_AGRICULTURAL_DROUGHT"
            ipc_phase = "IPC Phase 2 (Stressed)"
            risk_color = "#EAB308"
        else:
            drought_class = "ADEQUATE_MOISTURE_BALANCE"
            ipc_phase = "IPC Phase 1 (Minimal)"
            risk_color = "#10B981"

        # FAO-33 Crop Yield Response Modeling
        crop_impacts = {}
        weighted_loss_sum = 0.0
        crop_count = len(CROP_YIELD_SENSITIVITIES)

        for crop_name, sens in CROP_YIELD_SENSITIVITIES.items():
            ky = sens["ky"]
            # Predicted yield reduction percentage:
            # Yield Loss % = min(95.0, Ky * Rainfall Deficit %)
            loss_pct = round(min(95.0, ky * rain_deficit_pct), 1)
            crop_impacts[crop_name] = {
                "crop": crop_name,
                "yield_loss_pct": loss_pct,
                "ky_response_factor": ky,
                "staple_tier": sens["staple_tier"],
                "critical_growth_stage": sens["critical_growth_stage"],
                "is_dominant_in_state": crop_name in prof["dominant_crops"]
            }
            weighted_loss_sum += loss_pct

        mean_harvest_loss_pct = round(weighted_loss_sum / crop_count, 1)

        # Estimated stressed cropland and vulnerable farming population
        stressed_hectares = int(prof["cultivated_hectares"] * (rain_deficit_pct / 100.0) * 0.85)
        vulnerable_pop = int(prof["farming_population"] * (mean_harvest_loss_pct / 100.0) * 0.75)

        results.append({
            "state_code": s_code,
            "state_name": prof["name"],
            "agro_zone": prof["zone"],
            "rainfall_metrics": {
                "seasonal_normal_rain_mm": norm_rain,
                "current_observed_rain_mm": round(obs_rain, 1),
                "rainfall_deficit_pct": rain_deficit_pct
            },
            "drought_classification": {
                "severity_label": drought_class,
                "food_security_phase": ipc_phase,
                "risk_color": risk_color
            },
            "harvest_impact": {
                "mean_harvest_reduction_pct": mean_harvest_loss_pct,
                "stressed_cropland_hectares": stressed_hectares,
                "vulnerable_farming_population": vulnerable_pop,
                "total_cultivated_hectares": prof["cultivated_hectares"],
                "total_farming_population": prof["farming_population"]
            },
            "crop_breakdown": crop_impacts,
            "dominant_crops": prof["dominant_crops"],
            "dams_linked": prof["dams_linked"]
        })

    # Sort states descending by Mean Harvest Reduction (hardest-hit states first)
    results_sorted = sorted(results, key=lambda x: x["harvest_impact"]["mean_harvest_reduction_pct"], reverse=True)

    for rank, item in enumerate(results_sorted, 1):
        item["vulnerability_rank"] = rank

    # Compute national/regional summary statistics
    total_stressed_ha = sum(r["harvest_impact"]["stressed_cropland_hectares"] for r in results_sorted)
    total_vulnerable_people = sum(r["harvest_impact"]["vulnerable_farming_population"] for r in results_sorted)
    avg_harvest_loss = round(float(np.mean([r["harvest_impact"]["mean_harvest_reduction_pct"] for r in results_sorted])), 1)

    top_crisis_states = [r["state_name"] for r in results_sorted if "Crisis" in r["drought_classification"]["food_security_phase"]]
    if not top_crisis_states:
        top_crisis_states = [results_sorted[0]["state_name"], results_sorted[1]["state_name"]]

    return {
        "status": "OPERATIONAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_states_evaluated": len(results_sorted),
            "highest_deficit_state": results_sorted[0]["state_name"],
            "highest_deficit_loss_pct": results_sorted[0]["harvest_impact"]["mean_harvest_reduction_pct"],
            "regional_average_harvest_loss_pct": avg_harvest_loss,
            "total_cropland_under_drought_stress_ha": total_stressed_ha,
            "total_farming_population_at_risk": total_vulnerable_people,
            "priority_intervention_states": top_crisis_states
        },
        "state_rankings": results_sorted
    }


# ---------------------------------------------------------------------------
# 5. Prescriptive Agrarian Irrigation & Emergency Food Directives
# ---------------------------------------------------------------------------
def generate_drought_irrigation_advisory() -> Dict[str, Any]:
    """
    Synthesizes prescriptive engineering & food security directives, linking
    available dam water storage to the hardest-hit agricultural drought states.
    """
    harvest_data = compute_state_drought_and_harvest_loss()
    dams_data = get_dam_water_levels_overview()

    rankings = harvest_data["state_rankings"]
    top_3 = rankings[:3]

    directives = []

    # 1. Irrigation releases from upstream reservoirs
    for st in top_3:
        linked_dams = st["dams_linked"]
        if linked_dams:
            dam_names = [TARGET_DAMS_CATALOGUE[d]["dam_name"] for d in linked_dams if d in TARGET_DAMS_CATALOGUE]
            directives.append({
                "category": "DAM_IRRIGATION_RELEASE",
                "priority": "HIGH",
                "target_state": st["state_name"],
                "deficit_pct": st["harvest_impact"]["mean_harvest_reduction_pct"],
                "directive": (
                    f"Authorize controlled irrigation water release from {', '.join(dam_names)} "
                    f"into the downstream canal network to mitigate {st['harvest_impact']['mean_harvest_reduction_pct']}% "
                    f"projected yield deficit for {', '.join(st['dominant_crops'][:3])}."
                )
            })
        else:
            directives.append({
                "category": "SOLAR_IRRIGATION_PUMPING",
                "priority": "HIGH",
                "target_state": st["state_name"],
                "deficit_pct": st["harvest_impact"]["mean_harvest_reduction_pct"],
                "directive": (
                    f"Deploy mobile solar-powered water pumping units to riverine clusters in {st['state_name']} "
                    f"to pump alluvial groundwater across {st['harvest_impact']['stressed_cropland_hectares']:,} Ha of stressed cropland."
                )
            })

    # 2. Grain Reserve Allocation Directive
    directives.append({
        "category": "STRATEGIC_GRAIN_RESERVE",
        "priority": "CRITICAL",
        "target_state": f"{top_3[0]['state_name']} & {top_3[1]['state_name']}",
        "directive": (
            f"Pre-position 15,000 Metric Tonnes of strategic grain buffers (Sorghum & Maize) in {top_3[0]['state_name']} "
            f"and {top_3[1]['state_name']} ahead of the dry season to prevent speculative food price escalation."
        )
    })

    # 3. Seed subsidy recommendation
    directives.append({
        "category": "DROUGHT_TOLERANT_SEEDS",
        "priority": "MEDIUM",
        "target_state": "All Sahel/Sudan Margin States",
        "directive": (
            "Subsidize distribution of short-duration, drought-tolerant seed varieties "
            "(SAMMAZ-16 Maize, SOSAT-C88 Pearl Millet) for the upcoming secondary planting cycle."
        )
    })

    return {
        "status": "OPERATIONAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hardest_hit_states": [s["state_name"] for s in top_3],
        "directives": directives
    }

