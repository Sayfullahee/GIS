"""
generate_xlsform.py
===================
Generates the authoritative Master KoboToolbox / ODK XLSForm for the
N-HYPPADEC CHER-CDSS Field Survey System v4.1.1 (October 2026).
Implements Stage 5 & 6 requirements:
- 10 confirmed N-HYPPADEC States
- 186 cascading LGAs with choice_filter: state=${state_code}
- Full skip logic and validation constraints
- Offline GPS collection rules
- Media capture protocols
"""

import sys
from pathlib import Path
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

PROJECT_ROOT = Path(r"c:\xampp\htdocs\GIS")
LOOKUPS_DIR = PROJECT_ROOT / "03_Data" / "LOOKUPS"
OUTPUT_DIR = PROJECT_ROOT / "02_Fieldwork"

# Load lookups
states_df = pd.read_csv(LOOKUPS_DIR / "LKP_States.csv")
lgas_df = pd.read_csv(LOOKUPS_DIR / "LKP_LGAs.csv")

# ---------------------------------------------------------------------------
# 1. SURVEY SHEET DEFINITION
# ---------------------------------------------------------------------------
survey_rows = [
    # Metadata
    {"type": "start", "name": "start_time", "label": "Start Time"},
    {"type": "end", "name": "end_time", "label": "End Time"},
    {"type": "today", "name": "today_date", "label": "Survey Date"},
    {"type": "deviceid", "name": "device_id", "label": "Device ID"},
    
    # Section: Enumerator & Consent
    {"type": "begin_group", "name": "grp_admin", "label": "SECTION 1: ENUMERATOR & INFORMED CONSENT", "appearance": "field-list"},
    {"type": "text", "name": "enumerator_id", "label": "Enumerator ID", "hint": "Assigned N-HYPPADEC Enumerator Code e.g. ENUM-01", "required": "yes"},
    {"type": "text", "name": "supervisor_id", "label": "Supervisor ID", "hint": "Field Supervisor Code e.g. SUP-NIG-01", "required": "yes"},
    {"type": "note", "name": "consent_note", "label": "Informed Consent Statement: This observation survey is conducted on behalf of N-HYPPADEC for community resilience planning and decision support. Participation is voluntary and personal identifiers will remain strictly confidential."},
    {"type": "select_one yes_no", "name": "consent_given", "label": "Does the community focal person/respondent provide informed consent to proceed?", "required": "yes"},
    {"type": "end_group", "name": "grp_admin"},

    # Section: Geography & Identification (Cascading State -> LGA)
    {"type": "begin_group", "name": "grp_geo", "label": "SECTION 2: MASTER GEOGRAPHY & LOCATION", "relevant": "${consent_given} = 'yes'"},
    {"type": "select_one state_list", "name": "state_code", "label": "State", "hint": "Select State from the 10 N-HYPPADEC member states", "required": "yes"},
    {"type": "select_one lga_list", "name": "lga_code", "label": "Local Government Area (LGA)", "hint": "Filtered by selected State", "choice_filter": "state=${state_code}", "required": "yes"},
    {"type": "text", "name": "ward_name", "label": "Ward Name", "hint": "Administrative Ward (sub-layer G02W)", "required": "no"},
    {"type": "text", "name": "community_name", "label": "Community / Settlement Name", "hint": "Official local community name", "required": "yes"},
    {"type": "text", "name": "community_id", "label": "Permanent Community ID", "hint": "e.g. NG-NIG-001-0001 (Leave blank if assigning in central database)", "required": "no"},
    {"type": "geopoint", "name": "community_gps", "label": "Community Center GPS Point", "hint": "Stand in an open area at community meeting center. Wait for accuracy < 30m.", "required": "yes"},
    {"type": "end_group", "name": "grp_geo"},

    # Section: Demographics & Lifeline Services
    {"type": "begin_group", "name": "grp_demo", "label": "SECTION 3: POPULATION & LIVELINE SERVICES", "relevant": "${consent_given} = 'yes'"},
    {"type": "integer", "name": "estimated_population", "label": "Estimated Resident Population", "hint": "Total estimated community inhabitants", "constraint": ". > 0 and . <= 100000", "constraint_message": "Population must be between 1 and 100,000", "required": "no"},
    {"type": "select_one livelihood_list", "name": "primary_livelihood", "label": "Primary Community Livelihood", "required": "yes"},
    {"type": "select_one electricity_list", "name": "electricity_access", "label": "Electricity Access Status", "required": "yes"},
    {"type": "select_one water_list", "name": "water_source", "label": "Primary Potable Water Source", "required": "yes"},
    {"type": "end_group", "name": "grp_demo"},

    # Section: Climate & Hydro-Meteorological Observations
    {"type": "begin_group", "name": "grp_climate", "label": "SECTION 4: CLIMATE & HYDROLOGICAL OBSERVATIONS", "relevant": "${consent_given} = 'yes'"},
    {"type": "select_one rainfall_trend", "name": "rainfall_pattern_change", "label": "Perceived Rainfall Pattern Changes in Past 5 Years", "required": "yes"},
    {"type": "select_one temp_trend", "name": "temperature_trend", "label": "Perceived Temperature Trends", "required": "yes"},
    {"type": "select_one yes_no", "name": "drought_stress_experienced", "label": "Did the community experience severe agricultural water stress / drought this year?", "required": "yes"},
    {"type": "decimal", "name": "hydropower_distance_km", "label": "Estimated Distance to Nearest Hydropower Facility / Dam (km)", "hint": "Approximate distance in kilometres", "constraint": ". >= 0", "required": "no"},
    {"type": "end_group", "name": "grp_climate"},

    # Section: Flood Intelligence (Skip Logic: only if flood experienced)
    {"type": "begin_group", "name": "grp_flood", "label": "SECTION 5: FLOOD INTELLIGENCE & LOSSES", "relevant": "${consent_given} = 'yes'"},
    {"type": "select_one yes_no", "name": "flood_experience_past_year", "label": "Has this community experienced flooding in the past 12 months?", "required": "yes"},
    {"type": "integer", "name": "flood_frequency_5yrs", "label": "Number of Flood Events in the Past 5 Years", "relevant": "${flood_experience_past_year} = 'yes'", "constraint": ". >= 0 and . <= 20", "required": "yes"},
    {"type": "select_one severity_1_5", "name": "flood_severity_rank", "label": "Maximum Flood Severity Rank", "hint": "1=Minor nuisance to 5=Catastrophic settlement submergence", "relevant": "${flood_experience_past_year} = 'yes'", "required": "yes"},
    {"type": "integer", "name": "flood_duration_days", "label": "Typical Flood Duration (Days water remained standing)", "relevant": "${flood_experience_past_year} = 'yes'", "constraint": ". >= 0 and . <= 120", "required": "no"},
    {"type": "select_multiple flood_cause", "name": "flood_primary_cause", "label": "Primary Causes of Flooding", "relevant": "${flood_experience_past_year} = 'yes'", "required": "yes"},
    {"type": "select_multiple exposed_assets", "name": "flood_assets_damaged", "label": "Community Assets Damaged by Flooding", "relevant": "${flood_experience_past_year} = 'yes'", "required": "yes"},
    {"type": "end_group", "name": "grp_flood"},

    # Section: Erosion Intelligence (Skip Logic: only if erosion present)
    {"type": "begin_group", "name": "grp_erosion", "label": "SECTION 6: EROSION INTELLIGENCE & SITE MONITORING", "relevant": "${consent_given} = 'yes'"},
    {"type": "select_one yes_no", "name": "erosion_presence", "label": "Is active or historical erosion present in or adjacent to the community?", "required": "yes"},
    {"type": "select_one erosion_type_list", "name": "erosion_type", "label": "Primary Erosion Type", "relevant": "${erosion_presence} = 'yes'", "required": "yes"},
    {"type": "select_one severity_0_4", "name": "erosion_severity_rank", "label": "Erosion Severity Rank (0–4)", "hint": "0=None, 1=Slight, 2=Moderate, 3=Severe, 4=Very Severe (Gully/Catastrophic)", "relevant": "${erosion_presence} = 'yes'", "required": "yes"},
    {"type": "select_one activity_list", "name": "erosion_activity", "label": "Erosion Activity Status", "relevant": "${erosion_presence} = 'yes'", "required": "yes"},
    {"type": "decimal", "name": "erosion_depth_m", "label": "Estimated Gully/Bank Depth (metres)", "relevant": "${erosion_presence} = 'yes'", "constraint": ". >= 0 and . <= 100", "required": "no"},
    {"type": "decimal", "name": "erosion_river_dist_m", "label": "Distance from Erosion Site to Nearest River / Drainage (metres)", "relevant": "${erosion_presence} = 'yes'", "constraint": ". >= 0", "required": "no"},
    {"type": "select_one yes_no", "name": "erosion_infra_threat", "label": "Does the erosion directly threaten buildings, roads, or critical infrastructure?", "relevant": "${erosion_presence} = 'yes'", "required": "yes"},
    {"type": "select_one yes_no", "name": "erosion_control_present", "label": "Are erosion control structures present at this site?", "relevant": "${erosion_presence} = 'yes'", "required": "yes"},
    {"type": "end_group", "name": "grp_erosion"},

    # Section: Food Security & Agriculture Loss
    {"type": "begin_group", "name": "grp_food", "label": "SECTION 7: FOOD SECURITY & AGRICULTURAL LOSSES", "relevant": "${consent_given} = 'yes'"},
    {"type": "decimal", "name": "crop_loss_pct", "label": "Estimated Crop Loss Rate (% of harvest lost to climate/flood/erosion)", "constraint": ". >= 0 and . <= 100", "required": "no"},
    {"type": "decimal", "name": "livestock_loss_pct", "label": "Estimated Livestock Loss Rate (%)", "constraint": ". >= 0 and . <= 100", "required": "no"},
    {"type": "select_one yes_no", "name": "food_shortage_experienced", "label": "Did the community experience acute food shortages in the past 12 months?", "required": "yes"},
    {"type": "select_one yes_no", "name": "market_access_disrupted", "label": "Has physical market access been cut off due to floods or damaged culverts/roads?", "required": "yes"},
    {"type": "end_group", "name": "grp_food"},

    # Section: Community Security & Banditry Development Impacts (Section 14)
    {"type": "begin_group", "name": "grp_sec", "label": "SECTION 8: COMMUNITY SECURITY & BANDITRY IMPACTS (DEVELOPMENT EFFECTS ONLY)", "relevant": "${consent_given} = 'yes'"},
    {"type": "select_one yes_no", "name": "bandit_attack_experienced", "label": "Has this community experienced armed bandit attacks, raids, or kidnapping in the past 12 months?", "required": "yes"},
    {"type": "integer", "name": "bandit_attack_frequency", "label": "Estimated Number of Bandit Incidents / Attacks in Past 12 Months", "relevant": "${bandit_attack_experienced} = 'yes'", "constraint": ". >= 0", "required": "no"},
    {"type": "select_multiple bandit_impact_list", "name": "bandit_impacts", "label": "Key Impacts of Bandit Insecurity on the Community", "relevant": "${bandit_attack_experienced} = 'yes'", "required": "yes"},
    {"type": "select_one yes_no", "name": "displacement_observed", "label": "Has the community hosted IDPs or experienced displacement in the past 12 months?", "required": "yes"},
    {"type": "integer", "name": "displaced_households_count", "label": "Estimated Number of Displaced Households Affected", "relevant": "${displacement_observed} = 'yes'", "constraint": ". >= 0", "required": "no"},
    {"type": "select_one yes_no", "name": "farm_access_restricted", "label": "Are farmers unable to safely access their agricultural lands due to banditry / security threats?", "required": "yes"},
    {"type": "select_one yes_no", "name": "development_project_delay", "label": "Have development or resilience projects experienced access delays?", "required": "yes"},
    {"type": "end_group", "name": "grp_sec"},

    # Section: Adaptation, Interventions & MRV (Section 15)
    {"type": "begin_group", "name": "grp_mrv", "label": "SECTION 9: ADAPTATION, INTERVENTIONS & MRV", "relevant": "${consent_given} = 'yes'"},
    {"type": "select_one yes_no", "name": "intervention_present", "label": "Are N-HYPPADEC or public adaptation / resilience projects implemented here?", "required": "yes"},
    {"type": "text", "name": "intervention_id", "label": "Intervention ID (if known)", "hint": "e.g. INT-NIG-001-0001", "relevant": "${intervention_present} = 'yes'", "required": "no"},
    {"type": "select_multiple project_types", "name": "intervention_types", "label": "Types of Interventions Present", "relevant": "${intervention_present} = 'yes'", "required": "yes"},
    {"type": "select_one project_status", "name": "intervention_status", "label": "Current Operational Status of Intervention", "relevant": "${intervention_present} = 'yes'", "required": "yes"},
    {"type": "select_one effectiveness_scale", "name": "perceived_effectiveness", "label": "Community Perceived Effectiveness of the Measure", "relevant": "${intervention_present} = 'yes'", "required": "yes"},
    {"type": "end_group", "name": "grp_mrv"},

    # Section: Photographic Media Protocol (Level 3 CV Privacy Shield Compliant)
    {"type": "begin_group", "name": "grp_media", "label": "SECTION 10: PHOTOGRAPHIC EVIDENCE PROTOCOL (NON-PII / CV SHIELD)", "relevant": "${consent_given} = 'yes'"},
    {"type": "note", "name": "media_note", "label": "Media Privacy Rule (Level 3): Capture physical infrastructure, erosion sites, and landscape only. Recognized faces or private household interiors require explicit consent and will be automatically blurred by AI before GIS publishing."},
    {"type": "image", "name": "site_photo_1", "label": "Primary Site / Landscape / Hazard Photograph", "required": "no"},
    {"type": "select_one photo_category_list", "name": "photo_category_1", "label": "Photograph 1 Category", "hint": "Subject category for automated CV privacy gating", "relevant": "string-length(${site_photo_1}) > 0", "required": "yes"},
    {"type": "select_one yes_no", "name": "consent_for_media_1", "label": "Has explicit Level 3 signed subject consent been obtained if human subjects are in frame?", "relevant": "string-length(${site_photo_1}) > 0", "required": "yes"},
    {"type": "text", "name": "site_photo_1_desc", "label": "Photograph 1 Caption / Description", "relevant": "string-length(${site_photo_1}) > 0", "required": "no"},
    {"type": "image", "name": "site_photo_2", "label": "Secondary Photograph (Erosion/Infrastructure/Intervention)", "required": "no"},
    {"type": "select_one photo_category_list", "name": "photo_category_2", "label": "Photograph 2 Category", "relevant": "string-length(${site_photo_2}) > 0", "required": "no"},
    {"type": "select_one yes_no", "name": "consent_for_media_2", "label": "Has explicit Level 3 signed subject consent been obtained for Photograph 2?", "relevant": "string-length(${site_photo_2}) > 0", "required": "no"},
    {"type": "text", "name": "site_photo_2_desc", "label": "Photograph 2 Caption / Description", "relevant": "string-length(${site_photo_2}) > 0", "required": "no"},
    {"type": "end_group", "name": "grp_media"},

    # Section: Flood Early Warning Field Observations & Community Awareness
    {"type": "begin_group", "name": "grp_few", "label": "SECTION 11: FLOOD EARLY WARNING FIELD OBSERVATIONS & COMMUNITY AWARENESS", "relevant": "${consent_given} = 'yes'"},
    {"type": "note", "name": "few_safety_note", "label": "Field observations support decision-making only and do not issue official warnings. Do not collect tactical security information or personal phone numbers."},
    {"type": "select_one yes_no", "name": "few_observation_available", "label": "Were flood or water-condition observations available during this activity?", "required": "yes"},
    {"type": "begin_group", "name": "grp_few_observation", "label": "Flood / water-condition evidence observation", "appearance": "field-list", "relevant": "${few_observation_available} = 'yes'"},
    {"type": "dateTime", "name": "few_observed_at", "label": "Date and time of flood or water-condition observation", "required": "yes"},
    {"type": "select_multiple few_evidence_type", "name": "few_evidence_sources", "label": "Evidence observed or received", "required": "yes"},
    {"type": "select_one few_drainage_feature", "name": "few_drainage_type", "label": "Main affected river or drainage feature type", "required": "no"},
    {"type": "text", "name": "few_watercourse_name", "label": "Local or published watercourse name", "required": "no"},
    {"type": "decimal", "name": "few_river_level_m", "label": "Observed river or water level (metres; if measured)", "constraint": ". >= 0", "required": "no"},
    {"type": "decimal", "name": "few_rate_of_rise_cm_hr", "label": "Observed rate of rise (centimetres per hour; if measured)", "constraint": ". >= 0", "required": "no"},
    {"type": "select_one few_confidence", "name": "few_observation_confidence", "label": "Observer assessment of evidence confidence", "required": "yes"},
    {"type": "select_one yes_no", "name": "few_flood_confirmed", "label": "Has flooding been directly observed at this location?", "required": "yes"},
    {"type": "end_group", "name": "grp_few_observation"},
    {"type": "select_one yes_no", "name": "few_awareness_delivered", "label": "Was a community preparedness or awareness activity delivered?", "required": "yes"},
    {"type": "select_multiple few_awareness_method", "name": "few_awareness_methods", "label": "Methods used", "relevant": "${few_awareness_delivered} = 'yes'", "required": "yes"},
    {"type": "text", "name": "few_awareness_language", "label": "Language(s) used", "relevant": "${few_awareness_delivered} = 'yes'", "required": "no"},
    {"type": "integer", "name": "few_awareness_audience", "label": "Estimated target audience", "relevant": "${few_awareness_delivered} = 'yes'", "constraint": ". >= 0", "required": "no"},
    {"type": "integer", "name": "few_awareness_reached", "label": "Estimated people reached", "relevant": "${few_awareness_delivered} = 'yes'", "constraint": ". >= 0", "required": "no"},
    {"type": "text", "name": "few_awareness_materials", "label": "Approved materials or message version used", "relevant": "${few_awareness_delivered} = 'yes'", "required": "no"},
    {"type": "text", "name": "few_community_feedback", "label": "Non-identifying community feedback or preparedness needs", "relevant": "${few_awareness_delivered} = 'yes'", "required": "no"},
    {"type": "end_group", "name": "grp_few"},

    # Section: Canonical Multi-Hazard & Environmental Risks Assessment (14 Themes)
    {"type": "begin_group", "name": "grp_env_problems", "label": "SECTION 12: COMMUNITY MULTI-HAZARD & ENVIRONMENTAL PROBLEMS (14 THEMES)", "relevant": "${consent_given} = 'yes'"},
    {"type": "note", "name": "env_problems_note", "label": "Official 14-Theme Multi-Hazard & Environmental Survey: Identify all severe environmental, climate, and human-induced hazards actively affecting this community."},
    {"type": "select_multiple env_problems_list", "name": "environmental_problems_observed", "label": "Select ALL Environmental & Security Problems Observed in this Community", "required": "yes"},
    {"type": "select_one env_problems_list", "name": "primary_environmental_problem", "label": "Which of the observed problems is the SINGLE HIGHEST PRIORITY / MOST SEVERE threat?", "relevant": "count-selected(${environmental_problems_observed}) > 0", "required": "yes"},
    {"type": "select_one severity_1_5", "name": "primary_problem_severity", "label": "Severity Rank of Primary Problem (1=Minor to 5=Catastrophic)", "relevant": "count-selected(${environmental_problems_observed}) > 0", "required": "yes"},
    {"type": "select_one problem_trend_list", "name": "primary_problem_trend", "label": "Trend of this problem over the past 3 years", "relevant": "count-selected(${environmental_problems_observed}) > 0", "required": "yes"},
    {"type": "select_one yes_no", "name": "lead_poisoning_risk", "label": "Is informal / artisanal gold mining or lead exposure present nearby?", "required": "yes"},
    {"type": "select_one yes_no", "name": "oil_pollution_risk", "label": "Are petroleum pipeline spills, bunkering, or fuel leaks observed in local soils/waters?", "required": "yes"},
    {"type": "select_one yes_no", "name": "solid_waste_blockage", "label": "Is open refuse dumping or plastic waste actively blocking community drains and watercourses?", "required": "yes"},
    {"type": "select_one yes_no", "name": "water_contamination_observed", "label": "Is local drinking water visibly contaminated by upstream runoff, mine tailings, or sewage?", "required": "yes"},
    {"type": "select_one yes_no", "name": "deforestation_observed", "label": "Is severe tree felling, commercial charcoal burning, or forest canopy loss ongoing?", "required": "yes"},
    {"type": "select_one yes_no", "name": "desertification_observed", "label": "Are sand dunes advancing or fertile topsoil converting to desert wasteland?", "required": "yes"},
    {"type": "select_one yes_no", "name": "ecological_conflict_present", "label": "Have violent clashes occurred over grazing routes, arable land, or water points?", "required": "yes"},
    {"type": "text", "name": "env_problem_mitigation_notes", "label": "Community actions taken or urgent interventions requested by community leaders", "required": "no"},
    {"type": "end_group", "name": "grp_env_problems"},
]


# ---------------------------------------------------------------------------
# 2. CHOICES SHEET DEFINITION
# ---------------------------------------------------------------------------
choices_rows = [
    # Yes / No
    {"list_name": "yes_no", "name": "yes", "label": "Yes"},
    {"list_name": "yes_no", "name": "no", "label": "No"},
]

# 10 States
for _, row in states_df.iterrows():
    choices_rows.append({
        "list_name": "state_list",
        "name": row["State_Code"],
        "label": f"{row['State_Name']} ({row['Internal_Code']})"
    })

# 186 LGAs with state filter attribute
for _, row in lgas_df.iterrows():
    choices_rows.append({
        "list_name": "lga_list",
        "name": row["LGA_Code"],
        "label": row["LGA_Name"],
        "state": row["State_Code"]
    })

# Livelihoods
livelihoods = [
    ("LIV01", "Rainfed Farming"),
    ("LIV02", "Irrigated Farming"),
    ("LIV03", "Artisanal Fishing"),
    ("LIV04", "Pastoralism / Livestock"),
    ("LIV05", "Trading & Commerce"),
    ("LIV06", "Artisan / Small Business"),
    ("LIV07", "Public Service / Salary"),
]
for c, l in livelihoods:
    choices_rows.append({"list_name": "livelihood_list", "name": c, "label": l})

# Electricity
electricity = [("Yes", "Grid Connected (Stable)"), ("Partial", "Grid Connected (Frequent Outages)"), ("OffGrid", "Solar / Generator / Off-grid"), ("No", "No Electricity Access")]
for c, l in electricity:
    choices_rows.append({"list_name": "electricity_list", "name": c, "label": l})

# Water sources
water_sources = [
    ("WS01", "Solar / Motorized Borehole"),
    ("WS02", "Handpump Borehole"),
    ("WS03", "Protected Dug Well"),
    ("WS04", "Unprotected Dug Well"),
    ("WS05", "River / Stream / Pond"),
    ("WS06", "Water Tanker / Commercial"),
]
for c, l in water_sources:
    choices_rows.append({"list_name": "water_list", "name": c, "label": l})

# Climate trends
choices_rows.extend([
    {"list_name": "rainfall_trend", "name": "earlier", "label": "Onset Earlier than Usual"},
    {"list_name": "rainfall_trend", "name": "delayed", "label": "Onset Significantly Delayed"},
    {"list_name": "rainfall_trend", "name": "erratic", "label": "Erratic / Short High-Intensity Storms"},
    {"list_name": "rainfall_trend", "name": "normal", "label": "No Noticeable Change"},
    {"list_name": "temp_trend", "name": "much_hotter", "label": "Noticeably Hotter Extremes"},
    {"list_name": "temp_trend", "name": "slightly_hotter", "label": "Slightly Warmer"},
    {"list_name": "temp_trend", "name": "normal", "label": "Normal / No Change"},
])

# Severity 1-5
for s in range(1, 6):
    labels = {1: "1 — Minor Nuisance", 2: "2 — Moderate Disruption", 3: "3 — Severe Farmland Damage", 4: "4 — Critical Structural Flooding", 5: "5 — Catastrophic Submergence"}
    choices_rows.append({"list_name": "severity_1_5", "name": str(s), "label": labels[s]})

# Severity 0-4
for s in range(0, 5):
    labels = {0: "0 — None", 1: "1 — Slight (Sheet/Rill)", 2: "2 — Moderate", 3: "3 — Severe (Gully)", 4: "4 — Very Severe (Canyon Gully)"}
    choices_rows.append({"list_name": "severity_0_4", "name": str(s), "label": labels[s]})

# Flood causes
choices_rows.extend([
    {"list_name": "flood_cause", "name": "river_overflow", "label": "Main River Overflow"},
    {"list_name": "flood_cause", "name": "intense_rain", "label": "Severe Localized Rainfall"},
    {"list_name": "flood_cause", "name": "dam_release", "label": "Upstream Reservoir / Dam Release"},
    {"list_name": "flood_cause", "name": "drainage_blocked", "label": "Blocked / Inadequate Drainage Channels"},
])

# Exposed assets
choices_rows.extend([
    {"list_name": "exposed_assets", "name": "crops_farmland", "label": "Farmlands & Food Crops"},
    {"list_name": "exposed_assets", "name": "residential_homes", "label": "Residential Buildings"},
    {"list_name": "exposed_assets", "name": "schools_clinics", "label": "Schools & Health Facilities"},
    {"list_name": "exposed_assets", "name": "roads_bridges", "label": "Roads, Culverts & Bridges"},
    {"list_name": "exposed_assets", "name": "water_boreholes", "label": "Water Infrastructure / Boreholes"},
])

# Erosion types
choices_rows.extend([
    {"list_name": "erosion_type_list", "name": "gully", "label": "Gully Erosion"},
    {"list_name": "erosion_type_list", "name": "riverbank", "label": "Riverbank / Shoreline Collapse"},
    {"list_name": "erosion_type_list", "name": "rill", "label": "Rill Erosion"},
    {"list_name": "erosion_type_list", "name": "sheet", "label": "Sheet Erosion"},
    {"list_name": "activity_list", "name": "active", "label": "Active (Rapidly expanding)"},
    {"list_name": "activity_list", "name": "stabilizing", "label": "Stabilizing (Slowing down)"},
    {"list_name": "activity_list", "name": "dormant", "label": "Dormant (Vegetated / No recent change)"},
])

# Project types
choices_rows.extend([
    {"list_name": "project_types", "name": "drainage", "label": "Concrete Drainage / Flood Channel"},
    {"list_name": "project_types", "name": "gully_control", "label": "Gully Reclamation / Gabions"},
    {"list_name": "project_types", "name": "solar_borehole", "label": "Solar-Powered Potable Water"},
    {"list_name": "project_types", "name": "school_health", "label": "School / Clinic Rehabilitation"},
    {"list_name": "project_types", "name": "embankment", "label": "River Embankment / Dyke"},
    {"list_name": "project_types", "name": "tree_planting", "label": "Agroforestry / Vegetative Barrier"},
    {"list_name": "project_status", "name": "completed", "label": "Completed & Fully Functional"},
    {"list_name": "project_status", "name": "ongoing", "label": "Under Construction / Ongoing"},
    {"list_name": "project_status", "name": "impaired", "label": "Partially Damaged / Impaired"},
    {"list_name": "project_status", "name": "abandoned", "label": "Abandoned / Defunct"},
    {"list_name": "effectiveness_scale", "name": "very_effective", "label": "Very Effective — Substantial Risk Reduction"},
    {"list_name": "effectiveness_scale", "name": "moderate", "label": "Moderate — Partial Protection"},
    {"list_name": "effectiveness_scale", "name": "ineffective", "label": "Ineffective — No Noticeable Reduction"},
])

# FEW-CAM evidence, drainage feature, awareness and confidence vocabularies
choices_rows.extend([
    {"list_name": "few_evidence_type", "name": "rainfall", "label": "Rainfall observation or approved forecast"},
    {"list_name": "few_evidence_type", "name": "river_level", "label": "River level or rate of rise"},
    {"list_name": "few_evidence_type", "name": "reservoir", "label": "Reservoir or water-condition observation"},
    {"list_name": "few_evidence_type", "name": "satellite", "label": "Satellite observed surface water or flood extent"},
    {"list_name": "few_evidence_type", "name": "community_report", "label": "Community or field-team report"},
    {"list_name": "few_drainage_feature", "name": "main_river", "label": "Main river"},
    {"list_name": "few_drainage_feature", "name": "tributary", "label": "Tributary"},
    {"list_name": "few_drainage_feature", "name": "distributary", "label": "Distributary"},
    {"list_name": "few_drainage_feature", "name": "stream", "label": "Stream"},
    {"list_name": "few_drainage_feature", "name": "drainage_channel", "label": "Drainage channel"},
    {"list_name": "few_awareness_method", "name": "sms", "label": "SMS"},
    {"list_name": "few_awareness_method", "name": "radio", "label": "Radio"},
    {"list_name": "few_awareness_method", "name": "community_leader", "label": "Community leader"},
    {"list_name": "few_awareness_method", "name": "field_team", "label": "Field team"},
    {"list_name": "few_awareness_method", "name": "digital", "label": "Digital channel"},
    {"list_name": "few_awareness_method", "name": "drill", "label": "Preparedness drill"},
    {"list_name": "few_confidence", "name": "high", "label": "High"},
    {"list_name": "few_confidence", "name": "moderate", "label": "Moderate"},
    {"list_name": "few_confidence", "name": "low", "label": "Low"},
    {"list_name": "few_confidence", "name": "unknown", "label": "Unknown"},
])

# Bandit Impacts
choices_rows.extend([
    {"list_name": "bandit_impact_list", "name": "farm_abandonment", "label": "Farmland Abandonment / Inability to Cultivate"},
    {"list_name": "bandit_impact_list", "name": "cattle_rustling", "label": "Cattle Rustling / Livestock Looted"},
    {"list_name": "bandit_impact_list", "name": "kidnapping_ransom", "label": "Kidnapping for Ransom / Loss of Assets"},
    {"list_name": "bandit_impact_list", "name": "village_displacement", "label": "Village Submersion / Forced Displacement to IDP Sites"},
    {"list_name": "bandit_impact_list", "name": "market_closure", "label": "Weekly Rural Market Closures / Commercial Paralysis"},
])

# Canonical Multi-Hazard & Environmental Problems (14 Themes matching LKP_EnvironmentalProblems)
choices_rows.extend([
    {"list_name": "env_problems_list", "name": "AIR_POLLUTION", "label": "Air Pollution (Particulate/Diesel/Factory Smoke)"},
    {"list_name": "env_problems_list", "name": "CLIMATE_CHANGE", "label": "Climate Change Impacts (Erratic Rains/Heat Stress)"},
    {"list_name": "env_problems_list", "name": "DEFORESTATION", "label": "Deforestation & Unchecked Fuelwood Logging"},
    {"list_name": "env_problems_list", "name": "DESERTIFICATION", "label": "Desertification & Southern Sand Dune Encroachment"},
    {"list_name": "env_problems_list", "name": "DROUGHT", "label": "Drought & Agricultural Water Table Desiccation"},
    {"list_name": "env_problems_list", "name": "ECOLOGICAL_CONFLICT", "label": "Ecological Conflict (Farmer-Herder Grazing Route Disputes)"},
    {"list_name": "env_problems_list", "name": "EROSION", "label": "Erosion (Gully, Rill & Riverbank Collapse)"},
    {"list_name": "env_problems_list", "name": "FLOODING", "label": "Flooding (Riverine Inundation & Dam Release Overflows)"},
    {"list_name": "env_problems_list", "name": "LEAD_POISONING", "label": "Lead Poisoning & Artisanal Gold Mining Contamination"},
    {"list_name": "env_problems_list", "name": "OIL_SPILLAGE", "label": "Oil Spillage & Petroleum Hydrocarbon Contamination"},
    {"list_name": "env_problems_list", "name": "SOLID_WASTE", "label": "Solid Waste Dumps & Drainage Canal Plastic Blockage"},
    {"list_name": "env_problems_list", "name": "WATER_POLLUTION", "label": "Water Pollution (Industrial Runoff & Agrochemical Infiltration)"},
    {"list_name": "env_problems_list", "name": "FOOD_SECURITY", "label": "Food Security (Severe Staple Deficit & Hunger Stress)"},
    {"list_name": "env_problems_list", "name": "BANDIT_ATTACK", "label": "Bandit Attack & Violent Rural Insecurity"},
])

# Problem trends
choices_rows.extend([
    {"list_name": "problem_trend_list", "name": "worsening", "label": "Worsening / Rapidly Escalating"},
    {"list_name": "problem_trend_list", "name": "stable", "label": "Stable / Constant Level"},
    {"list_name": "problem_trend_list", "name": "improving", "label": "Improving / Under Effective Control"},
])

# Photo Categories for Level 3 CV Privacy Shield
choices_rows.extend([
    {"list_name": "photo_category_list", "name": "INFRASTRUCTURE", "label": "Infrastructure Asset (Dyke, Culvert, Well, Road)"},
    {"list_name": "photo_category_list", "name": "EROSION_GULLY", "label": "Erosion Gully / Riverbank Scour"},
    {"list_name": "photo_category_list", "name": "FLOOD_WATERMARK", "label": "Flood Watermark / Inundation Zone"},
    {"list_name": "photo_category_list", "name": "HOUSEHOLD", "label": "Household / Settlement Compound (Level 3 Restricted)"},
])

# ---------------------------------------------------------------------------
# 3. SETTINGS SHEET DEFINITION
# ---------------------------------------------------------------------------
settings_rows = [
    {
        "form_title": "CHER-CDSS Community Resilience, Multi-Hazard & FEW-CAM Field Survey v4.2.2",
        "form_id": "cher_cdss_field_survey_v4_2",
        "version": "2026110601",
        "default_language": "English",
        "style": "pages"
    }
]


# Build DataFrames
survey_df = pd.DataFrame(survey_rows)
choices_df = pd.DataFrame(choices_rows)
settings_df = pd.DataFrame(settings_rows)

# Fill NaN with empty string
survey_df = survey_df.fillna("")
choices_df = choices_df.fillna("")
settings_df = settings_df.fillna("")

# Save CSV exports for version control and automated ingestion
for prefix in ["CHER_CDSS_Master_XLSForm_v4.1", "CHER_CDSS_Master_XLSForm_v4.2"]:
    survey_df.to_csv(OUTPUT_DIR / f"{prefix}_survey.csv", index=False)
    choices_df.to_csv(OUTPUT_DIR / f"{prefix}_choices.csv", index=False)
    settings_df.to_csv(OUTPUT_DIR / f"{prefix}_settings.csv", index=False)

    # Write formatted Excel workbook using openpyxl
    excel_path = OUTPUT_DIR / f"{prefix}.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        survey_df.to_excel(writer, sheet_name="survey", index=False)
        choices_df.to_excel(writer, sheet_name="choices", index=False)
        settings_df.to_excel(writer, sheet_name="settings", index=False)

    # Apply executive styling to the workbook
    wb = openpyxl.load_workbook(excel_path)
    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    for sheet_name in ["survey", "choices", "settings"]:
        ws = wb[sheet_name]
        ws.freeze_panes = "A2"
        for col in ws.iter_cols(min_row=1, max_row=1):
            for cell in col:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    wb.save(excel_path)
    print(f"Master XLSForm {prefix} generated successfully ({excel_path.stat().st_size} bytes)")

print(f"  Survey rows:  {len(survey_df)}")
print(f"  Choices rows: {len(choices_df)} (including {len(lgas_df)} cascading LGAs)")

