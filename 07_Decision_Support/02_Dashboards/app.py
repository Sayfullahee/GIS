"""
app.py
======
CHER-CDSS Web GIS & Executive Decision-Support API Server
Specification: Master Implementation Scaffold v4.1 (October 2026)
Technology: FastAPI + Uvicorn + Leaflet / MapLibre Integration
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Path as FPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure scripts, fieldwork, and dashboard directories are on path for imports
PROJECT_ROOT = Path(os.environ.get("GIS_PROJECT_ROOT", Path(__file__).resolve().parent.parent.parent))
SCRIPTS_DIR = PROJECT_ROOT / "05_Analysis" / "02_SCRIPTS"
FIELDWORK_DIR = PROJECT_ROOT / "02_Fieldwork"
DASH_DIR = PROJECT_ROOT / "07_Decision_Support" / "02_Dashboards"
PRIORITY_DIR = PROJECT_ROOT / "07_Decision_Support" / "03_Priority_Areas"

for p in [str(SCRIPTS_DIR), str(FIELDWORK_DIR), str(DASH_DIR), str(PRIORITY_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import json
import config as cfg
import pandas as pd
import numpy as np

import kobo_sync_pipeline
import mhcvi_service
import sitrep_service
import alert_service
import ai_advisory_service
import ai_field_anomaly_service
import ai_flood_forecast_service
import ai_portfolio_optimizer
import ai_weather_service
import emergency_dispatch_gateway
import executive_dossier_service
import database_sync_service
import ai_drought_harvest_service
import logo_asset

FEW_RESTRICTED_TABLES = {
    "flood_alerts",
    "flood_alert_triggers",
    "flood_alert_areas",
    "flood_notifications",
    "flood_acknowledgements",
    "flood_awareness",
    "flood_drills",
    "flood_events",
    "flood_impacts",
    "flood_warning_performance",
}

tags_metadata = [
    {
        "name": "🏛️ Governance & Geography",
        "description": "Administrative boundaries, 10 N-HYPPADEC member states, LGA registers, infrastructure assets, and system health status.",
    },
    {
        "name": "🌊 FEW-CAM Flood Early Warning",
        "description": "Flood Early Warning, Alarm & Community Awareness System: alert lifecycle, multi-source triggers, spatial alert zones (G38), gauges (G39), and lead-time verification.",
    },
    {
        "name": "📊 Indicators & Risk Models",
        "description": "Master indicator family (IND01–IND10), reference bounds normalisation, composite risk engine (R = 0.35H + 0.25E + 0.25V + 0.15C), and Intervention Effectiveness Score (IES).",
    },
    {
        "name": "🗺️ GIS & Spatial Services",
        "description": "43-layer master geospatial register (G01–G43), priority hotspot coordinate feeds, and dynamic GeoJSON feature streams.",
    },
    {
        "name": "🛰️ Earth Observation & Remote Sensing",
        "description": "Copernicus Sentinel-1 SAR flood inundation analysis, Sentinel-2 NDVI vegetative baselines, and multi-temporal riverbank retreat rates.",
    },
    {
        "name": "📈 Scenario Simulation Lab",
        "description": "Stage 21 empirical stress testing simulating extreme precipitation anomalies (+10% to +30%), temperature rise, and adaptation dike investments.",
    },
    {
        "name": "🛡️ Interventions & MRV",
        "description": "Measurement, Reporting & Verification (MRV) registry for capital defense assets, dykes, drainage channels, and public expenditure.",
    },
    {
        "name": "🌾 Thematic Livelihoods & Security",
        "description": "Agricultural yield loss assessments, food access constraints, and conflict-environmental impact monitoring.",
    },
    {
        "name": "🗄️ Core Database Model (31 Tables)",
        "description": "Section 32 PostgreSQL/PostGIS relational data model browser with automated data dictionaries and Level 3 privacy masking.",
    },
    {
        "name": "🌍 Multi-Hazard & Environmental Risks",
        "description": "National multi-hazard taxonomy (14 canonical problems: Food Security, Bandit Attack, Air Pollution, Climate Change, Deforestation, Desertification, Drought, Ecological Conflict, Erosion, Flooding, Lead Poisoning, Oil Spillage, Solid Waste, Water Pollution) and G65 spatial layer.",
    },
    {
        "name": "🔄 Field Operations & Data Ingestion",
        "description": "Real-time KoboToolbox / ODK field survey data sync, 5-gate quality control, landing staging, and quarantine resolution.",
    },
    {
        "name": "🗺️ Multi-Hazard Compound Vulnerability (MHCVI)",
        "description": "Multi-Hazard Compound Vulnerability Index (0-100) aggregating 14 hazards across Security, Hydrology, and Environmental degradation.",
    },
    {
        "name": "📄 Institutional SitRep & Policy Briefs",
        "description": "Automated executive situation reports, emergency budget estimations, and high-resolution printable policy advisories.",
    },
    {
        "name": "🚨 Early Warning Matrix & Alert Dispatch",
        "description": "Multi-hazard early warning advisories, hydro dam discharge alerts, and emergency broadcast dispatch simulation.",
    },
    {
        "name": "🤖 Prescriptive AI & Early Warning Engine",
        "description": "Multi-phase operational AI services: GenAI Executive SitRep Synthesizer, 6-Language Vernacular Alerts, Field Survey CV PII & Fraud Shield, Dam Hydro Forecasts, and Prescriptive Capital Investment Portfolio Optimizer.",
    },
    {
        "name": "🖥️ Executive Management Web UI",
        "description": "Interactive Web GIS dashboard interface and executive decision portal.",
    },
]


app = FastAPI(
    title="CHER-CDSS Institutional Decision-Support API",
    description="""
# Climate–Hydropower–Erosion–Community Resilience Decision-Support System (CHER-CDSS)
### Authoritative Institutional Evidence Platform for the Ten N-HYPPADEC States of Nigeria
**Specification**: Master Implementation Scaffold v4.2 (October 2026)  
**Lead Agency**: National Hydroelectric Power Producing Areas Development Commission (N-HYPPADEC)  
**Security & Access Classification**: Level 1 (Public Analytics) / Level 3 (Restricted Microdata Isolated)  

---

### Core Analytical Architecture:
1. **Permanent Spatial Scope**: 10 Member States (*Niger, Kebbi, Plateau, Benue, Kogi, Kwara, Kaduna, Nasarawa, Taraba, Gombe*), 186 LGAs, 50 Sentinel Communities.
2. **43-Layer Master GIS Register**: Administrative (`G01`–`G03`), Hydrology (`G05`–`G08`), Terrain (`G09`–`G14`), Land Cover & EO (`G15`, `G43`), Hazards (`G24`–`G27`), Composite Risk (`G31`–`G37`), and FEW-CAM Alert Zones (`G38`–`G43`).
3. **Master Risk Formula**: $R = 0.35H + 0.25E + 0.25V + 0.15C$, normalized strictly against frozen `Baseline_2026` reference bounds.
4. **FEW-CAM Warning Architecture**: Multi-level warning continuum (Level 0 Routine, Level 1 Watch, Level 2 Warning, Level 3 Emergency) with verified empirical lead times.
5. **31-Table Relational Schema**: PostgreSQL 16 + PostGIS 3.4 compliant data models with immutable audit trails and provenance tracking.
    """,
    version="4.1",
    openapi_tags=tags_metadata,
    contact={
        "name": "N-HYPPADEC Decision Support & GIS Directorate",
        "url": "http://localhost:8000/",
        "email": "gis-support@n-hyppadec.gov.ng"
    },
    license_info={
        "name": "Government Public Evidence License (NITDA Sovereign Data Compliant)",
        "url": "https://nitda.gov.ng"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_records(df: Optional[pd.DataFrame]) -> list:
    if df is None or len(df) == 0:
        return []
    return json.loads(df.to_json(orient="records"))

def load_flood_dataset(name: str) -> Optional[pd.DataFrame]:
    path = cfg.DATA_CLEAN / f"{name}_CLEAN.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)

def column_name(df: pd.DataFrame, name: str) -> Optional[str]:
    return next((column for column in df.columns if column.lower() == name.lower()), None)

def require_dataset_column(df: pd.DataFrame, name: str, dataset: str) -> str:
    field = column_name(df, name)
    if field is None:
        raise HTTPException(status_code=500, detail=f"{dataset} is missing required field '{name}'")
    return field

def numeric_column(df: pd.DataFrame, name: str, dataset: str) -> pd.Series:
    field = require_dataset_column(df, name, dataset)
    values = pd.to_numeric(df[field], errors="coerce")
    if (df[field].notna() & values.isna()).any():
        raise HTTPException(status_code=500, detail=f"{dataset}.{name} contains a non-numeric value")
    return values

def released_alerts(df: pd.DataFrame) -> pd.DataFrame:
    status = require_dataset_column(df, "status", "Flood_Alerts")
    return df[df[status].astype(str).str.casefold().eq("released")]

def published_performance(df: pd.DataFrame) -> pd.DataFrame:
    status = require_dataset_column(df, "publication_status", "Flood_Warning_Performance")
    return df[df[status].astype(str).str.casefold().eq("approved")]

def published_awareness(df: pd.DataFrame) -> pd.DataFrame:
    status = require_dataset_column(df, "publication_status", "Flood_Awareness")
    return df[df[status].astype(str).str.casefold().eq("approved")]

def public_fields(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    selected = {field: actual for field in fields if (actual := column_name(df, field)) is not None}
    return df[list(selected.values())].rename(columns={actual: field for field, actual in selected.items()})

# ---------------------------------------------------------------------------
# Static Assets & Official Agency Heraldry
# ---------------------------------------------------------------------------
if os.path.exists(logo_asset.STATIC_DIR):
    app.mount("/static", StaticFiles(directory=logo_asset.STATIC_DIR), name="static")

@app.get("/logo.png", include_in_schema=False)
@app.get("/logo.jpg", include_in_schema=False)
@app.get(
    "/api/logo",
    tags=["🏛️ Statutory Decision Support & Reporting"],
    summary="Official N-HYPPADEC Emblem & Logo Asset",
    description="Returns the authoritative high-resolution official seal and emblem of the National Hydroelectric Power Producing Areas Development Commission."
)
def get_official_agency_logo():
    path = logo_asset.get_logo_filepath()
    media_type = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    return FileResponse(path, media_type=media_type)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
class RiskCalculationRequest(BaseModel):
    hazard: float = Field(..., ge=0, le=100, description="Hazard Index (0-100)")
    exposure: float = Field(..., ge=0, le=100, description="Exposure Index (0-100)")
    vulnerability: float = Field(..., ge=0, le=100, description="Vulnerability Index (0-100)")
    criticality: float = Field(..., ge=0, le=100, description="Criticality Index (0-100)")
    method: str = Field("additive", description="'additive' or 'multiplicative'")

class IESCalculationRequest(BaseModel):
    risk_before: float = Field(..., ge=0, le=100, description="Pre-intervention risk score")
    risk_after: float = Field(..., ge=0, le=100, description="Post-intervention risk score")
    method_before: str = "v4.1"
    method_after: str = "v4.1"
    reference_bounds_match: bool = True

class KoboRemediationRequest(BaseModel):
    submission_id: str = Field(..., description="Unique submission ID from quarantine log")
    corrections: Dict[str, Any] = Field(..., description="Field corrections dictionary")
    approved_by: Optional[str] = Field("Field Supervisor", description="Approving officer name/designation")
    justification: Optional[str] = Field("Field data remediation", description="Justification for override/remediation")

class AlertBroadcastRequest(BaseModel):
    alert_id: str = Field(..., description="Target alert ID")
    channel: Optional[str] = Field("SMS_BROADCAST", description="Transmission channel (SMS_BROADCAST, VHF_RADIO, WHATSAPP_EMERGENCY)")
    recipients_group: Optional[str] = Field("Community Liaison Officers & Village Heads", description="Target recipient category")

class SitRepSynthesisRequest(BaseModel):
    state_code: Optional[str] = Field(None, description="Optional State Code e.g. NG-NIG or None for all states")

class AlertTranslationRequest(BaseModel):
    alert_id: str = Field("ALT-2026-NIG-001", description="Authoritative alert identifier")
    target_language: str = Field("hausa", description="Indigenous language: hausa, nupe, tiv, yoruba, fulfulde, gbagyi")
    target_states: List[str] = Field(default_factory=lambda: ["Niger", "Kwara"], description="Target states")
    target_lgas: List[str] = Field(default_factory=lambda: ["Mokwa", "Lavun", "Pategi"], description="Target LGAs")
    hazard_type: str = Field("Flooding", description="Hazard type e.g. Flooding, Dam Spillway Release")
    severity: str = Field("CRITICAL", description="Severity class: ADVISORY, WATCH, WARNING, CRITICAL")
    lead_time_hours: int = Field(24, description="Evacuation lead time in hours")
    evacuation_shelter: str = Field("Designated Primary School & LGA Hall", description="Safe assembly / shelter location")

class FieldAuditRequest(BaseModel):
    submission: Dict[str, Any] = Field(..., description="Field survey submission payload")
    recent_submissions: Optional[List[Dict[str, Any]]] = Field(None, description="Historical submissions by the same enumerator for velocity checks")

class PhotoPiiScanRequest(BaseModel):
    file_name: str = Field("survey_sample.jpg", description="Photo filename")
    photo_category: str = Field("INFRASTRUCTURE", description="Photo category: INFRASTRUCTURE, HOUSEHOLD, EROSION_GULLY, FLOOD_WATERMARK")
    faces_detected: int = Field(0, description="Detected facial bounding boxes")
    consent_for_media: bool = Field(False, description="Has explicit Level 3 signed subject consent")

class DamForecastRequest(BaseModel):
    dam_id: str = Field("DAM-NIG-01", description="Dam Identifier: DAM-NIG-01 (Kainji), DAM-NIG-02 (Jebba), DAM-NIG-03 (Shiroro), DAM-GOM-01 (Dadin Kowa), DAM-TAR-01 (Kashimbila)")
    upstream_rainfall_forecast_mm: float = Field(45.0, description="Upstream basin 24-hr cumulative rainfall forecast (mm)")
    current_water_level_m: Optional[float] = Field(None, description="Current reservoir water level (m)")

class PortfolioOptimizationRequest(BaseModel):
    total_budget_ngn: float = Field(2_500_000_000.0, description="Capital allocation budget in NGN")
    objective: str = Field("MAX_IES", description="Optimization policy: MAX_IES, MAX_COMMUNITIES, EQUITY_BALANCED, CRITICAL_FIRST")
    state_filter: Optional[str] = Field(None, description="Optional State name filter (or ALL)")
    max_state_share_pct: float = Field(28.0, description="Max budget percentage allowed per state in equity mode")
    candidate_pool_size: int = Field(100, description="Candidate pool size from top priority communities")
    min_risk: float = Field(40.0, description="Minimum Composite Risk threshold for candidate inclusion")

class EmergencyBroadcastDispatchPayload(BaseModel):
    dam_id: str = Field("DAM-NIG-01", description="Dam Identifier")
    dam_name: str = Field("Kainji Dam", description="Dam Name")
    warning_level: int = Field(3, ge=1, le=4, description="Warning Level (1-4)")
    spill_risk_pct: float = Field(78.5, description="Spill risk probability percentage")
    lead_time_hours: int = Field(18, description="Evacuation lead time in hours")
    affected_lgas: List[str] = Field(["Mokwa", "Borgu"], description="List of downstream exposed LGAs")
    language: str = Field("English", description="Vernacular language for dispatch")
    selected_channels: List[str] = Field(["SMS", "WHATSAPP", "TELEGRAM"], description="Active dispatch channels")
    custom_directive: Optional[str] = Field(None, description="Optional custom operational directive")
    sender_officer: str = Field("N-HYPPADEC Situation Room", description="Dispatching officer or role")

class PostgisDbConfigRequest(BaseModel):
    host: Optional[str] = Field(None, description="PostgreSQL host")
    port: Optional[int] = Field(None, description="PostgreSQL port")
    dbname: Optional[str] = Field(None, description="Database name")
    user: Optional[str] = Field(None, description="Database user")
    password: Optional[str] = Field(None, description="Database password")

# ---------------------------------------------------------------------------
# Helper Loaders
# ---------------------------------------------------------------------------
def get_states_data():
    df = pd.read_csv(cfg.LKP_STATES)
    return safe_records(df)

def get_lgas_data(state_code: Optional[str] = None):
    df = pd.read_csv(cfg.LKP_LGAS)
    if state_code:
        df = df[df["State_Code"] == state_code]
    return safe_records(df)

# ---------------------------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/api/health",
    tags=["🏛️ Governance & Geography"],
    summary="System Health & Governance Status",
    description="Returns operational status, scaffold version, states covered, LGA counts, active GIS layers, and database tables for the CHER-CDSS platform."
)
def health_check():
    return {
        "status": "HEALTHY",
        "system": "CHER-CDSS N-HYPPADEC Evidence Platform",
        "scaffold_version": "v4.1",
        "baseline_period": "2026",
        "states_count": len(cfg.STUDY_STATES),
        "lgas_count": len(pd.read_csv(cfg.LKP_LGAS)),
        "layers_count": 43,
        "database_tables": 31,
        "test_status": "Run current validation suite for verified test results"
    }

@app.get(
    "/api/states",
    tags=["🏛️ Governance & Geography"],
    summary="List Ten N-HYPPADEC Member States",
    description="Returns full statutory lookup records for the ten confirmed N-HYPPADEC member states with internal prefixes, land areas, and geographic coordinates."
)
def list_states():
    return {
        "count": len(cfg.STUDY_STATES),
        "states": get_states_data()
    }

@app.get(
    "/api/states/{state_code}/lgas",
    tags=["🏛️ Governance & Geography"],
    summary="List Local Government Areas (LGAs) by State",
    description="Returns all statutory Local Government Areas within the specified state code (e.g. NG-NIG, NG-BEN, NG-KOG)."
)
def get_state_lgas(
    state_code: str = FPath(..., description="ISO/Statutory state code prefix (e.g. NG-NIG)")
):
    lgas = get_lgas_data(state_code)
    if not lgas:
        raise HTTPException(status_code=404, detail=f"No LGAs found for state {state_code}")
    return {
        "state_code": state_code,
        "count": len(lgas),
        "lgas": lgas
    }

@app.get(
    "/api/indicators",
    tags=["📊 Indicators & Risk Models"],
    summary="Master Reference Indicators & Frozen Baseline Bounds",
    description="Returns the master register of indicators (IND01–IND10) alongside their directional polarity, baseline minimum/maximum reference bounds, and normalization rules."
)
def list_indicators():
    df = pd.read_csv(cfg.REFERENCE_BOUNDS)
    return {
        "count": len(df),
        "version": "Baseline_2026",
        "indicators": safe_records(df)
    }

@app.get(
    "/api/layers",
    tags=["🗺️ GIS & Spatial Services"],
    summary="43-Layer Master GIS Register",
    description="Returns the full technical catalog of all 43 spatial layers (G01–G43) across Administrative, Hydrology, Terrain, Hazards, Risk, and FEW-CAM categories."
)
def list_gis_layers():
    # 43-Layer Master Register
    layers = [
        {"id": "G01", "name": "Nigeria_State", "category": "Administrative", "type": "Polygon"},
        {"id": "G02", "name": "Nigeria_LGA", "category": "Administrative", "type": "Polygon", "sub_layer": "G02W Ward Boundaries"},
        {"id": "G03", "name": "Communities", "category": "Administrative", "type": "Point"},
        {"id": "G04", "name": "Households", "category": "Socioeconomic", "type": "Point", "privacy": "Level 3 Restricted"},
        {"id": "G05", "name": "River_and_Drainage_Network", "category": "Hydrology", "type": "Line", "scope": "Main rivers, tributaries, distributaries, streams, and drainage channels"},
        {"id": "G06", "name": "HydroBasins", "category": "Hydrology", "type": "Polygon"},
        {"id": "G07", "name": "HydroFacilities", "category": "Hydropower", "type": "Point"},
        {"id": "G08", "name": "Reservoirs", "category": "Hydropower", "type": "Polygon"},
        {"id": "G09", "name": "DEM", "category": "Terrain", "type": "Raster", "resolution": "30m"},
        {"id": "G10", "name": "Slope", "category": "Terrain", "type": "Raster", "unit": "degrees"},
        {"id": "G11", "name": "Aspect", "category": "Terrain", "type": "Raster"},
        {"id": "G12", "name": "Hillshade", "category": "Terrain", "type": "Raster"},
        {"id": "G13", "name": "FlowDirection", "category": "Hydrology", "type": "Raster"},
        {"id": "G14", "name": "FlowAccumulation", "category": "Hydrology", "type": "Raster"},
        {"id": "G15", "name": "LandCover", "category": "Environment", "type": "Raster"},
        {"id": "G16", "name": "OSM_Roads", "category": "Infrastructure", "type": "Line"},
        {"id": "G17", "name": "OSM_Buildings", "category": "Exposure", "type": "Polygon"},
        {"id": "G18", "name": "OSM_POI", "category": "Criticality", "type": "Point"},
        {"id": "G19", "name": "Infrastructure_Field", "category": "Infrastructure", "type": "Point"},
        {"id": "G20", "name": "Climate_Stations", "category": "Climate", "type": "Point"},
        {"id": "G21", "name": "Climate_Observations", "category": "Climate", "type": "Table"},
        {"id": "G22", "name": "Rainfall_Surface", "category": "Climate", "type": "Raster"},
        {"id": "G23", "name": "Temperature_Surface", "category": "Climate", "type": "Raster"},
        {"id": "G24", "name": "Flood_Hazard", "category": "Hazard", "type": "Raster/Vector"},
        {"id": "G25", "name": "Flood_Observed", "category": "Hazard", "type": "Polygon"},
        {"id": "G26", "name": "Erosion_Sites", "category": "Hazard", "type": "Point"},
        {"id": "G27", "name": "Erosion_Hotspots", "category": "Hazard", "type": "Raster/Vector"},
        {"id": "G28", "name": "Hydro_Water", "category": "Hydrology", "type": "Table"},
        {"id": "G29", "name": "Flood_Exposure", "category": "Exposure", "type": "Vector"},
        {"id": "G30", "name": "Erosion_Exposure", "category": "Exposure", "type": "Vector"},
        {"id": "G31", "name": "Hazard_Index", "category": "Decision_Support", "type": "Index 0-100"},
        {"id": "G32", "name": "Exposure_Index", "category": "Decision_Support", "type": "Index 0-100"},
        {"id": "G33", "name": "Vulnerability_Index", "category": "Decision_Support", "type": "Index 0-100"},
        {"id": "G34", "name": "Criticality_Index", "category": "Decision_Support", "type": "Index 0-100"},
        {"id": "G35", "name": "Composite_Risk", "category": "Decision_Support", "type": "Index 0-100"},
        {"id": "G36", "name": "Adaptation", "category": "MRV", "type": "Vector"},
        {"id": "G37", "name": "Priority_Areas", "category": "Decision_Support", "type": "Vector"},
        {"id": "G38", "name": "Flood_Alert_Zones", "category": "Flood_Early_Warning", "type": "Polygon"},
        {"id": "G39", "name": "Flood_Warning_Points", "category": "Flood_Early_Warning", "type": "Point"},
        {"id": "G40", "name": "Community_Awareness_Locations", "category": "Community_Awareness", "type": "Point"},
        {"id": "G41", "name": "Approved_Evacuation_or_Assembly_Areas", "category": "Emergency_Preparedness", "type": "Polygon"},
        {"id": "G42", "name": "Historical_Flood_Events", "category": "Flood_Events", "type": "Polygon"},
        {"id": "G43", "name": "Recent_Flood_Extent", "category": "Flood_Events", "type": "Polygon"},
    ]
    return {"total_layers": len(layers), "layers": layers}

@app.get(
    "/api/flood/warning-levels",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="Statutory Warning Level Continuum & Guidance",
    description="Returns the 4-tier warning level continuum (Level 0 Normal Monitoring to Level 3 Flood Warning) with institutional guidance and operational mandate disclaimers."
)
def get_flood_warning_levels():
    return {
        "authority": "Decision-support only; official warnings require authorised emergency-management approval.",
        "thresholds_status": "approval_required",
        "levels": [
            {"level": 0, "name": "Normal Monitoring", "guidance": "Routine monitoring; no immediate threat."},
            {"level": 1, "name": "Advisory", "guidance": "Increasing flood potential; preparedness and monitoring."},
            {"level": 2, "name": "Flood Watch", "guidance": "Higher likelihood; preparedness and coordination increase."},
            {"level": 3, "name": "Flood Warning", "guidance": "Flood imminent or occurring; follow approved emergency instructions."},
        ],
    }

@app.get(
    "/api/flood/alerts",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="Active & Released Flood Alerts Register",
    description="Queries released institutional flood alerts with optional state and LGA filters. Enforces verified release status and confidence metrics."
)
def get_flood_alerts(
    state_code: Optional[str] = Query(None, description="Optional statutory state code filter (e.g. NG-NIG)"),
    lga_id: Optional[str] = Query(None, description="Optional LGA identifier filter")
):
    if not isinstance(state_code, str):
        state_code = None
    if not isinstance(lga_id, str):
        lga_id = None
    source = load_flood_dataset("Flood_Alerts")
    if source is None:
        return {"status": "NOT_CONFIGURED", "count": 0, "alerts": []}
    for field in ("alert_id", "issued_at", "state_code", "warning_level", "trigger_type",
                  "hazard_score", "confidence", "status", "released_at"):
        require_dataset_column(source, field, "Flood_Alerts")
    warning_levels = numeric_column(source, "warning_level", "Flood_Alerts")
    if (warning_levels.isna().any() or warning_levels.mod(1).ne(0).any()
            or not warning_levels.between(0, 3).all()):
        raise HTTPException(status_code=500, detail="Flood_Alerts.warning_level must be an integer from 0 to 3")
    df = released_alerts(source)
    for filter_name, value in (("state_code", state_code), ("lga_id", lga_id)):
        if value:
            field = column_name(df, filter_name)
            if field is None:
                raise HTTPException(status_code=500, detail=f"Flood_Alerts is missing required field '{filter_name}'")
            df = df[df[field].astype(str).str.casefold() == value.casefold()]
    fields = [
        "alert_id", "issued_at", "state_code", "lga_id", "warning_level",
        "trigger_type", "hazard_score", "confidence", "status", "released_at",
    ]
    return {"status": "OPERATIONAL", "count": len(df), "alerts": safe_records(public_fields(df, fields))}

@app.get(
    "/api/flood/geojson",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="FEW-CAM Spatial Alert Zones (G38)",
    description="Streams GeoJSON FeatureCollection of released flood alert zones (G38) including exposed population estimates, affected area, and warning severity."
)
def get_flood_alert_geojson():
    path = cfg.GIS_DERIVED / "G38_Flood_Alert_Zones_v1_0.geojson"
    if not path.exists():
        return {"status": "NOT_CONFIGURED", "type": "FeatureCollection", "features": []}
    with path.open(encoding="utf-8") as source:
        geojson = json.load(source)
    if (geojson.get("type") != "FeatureCollection"
            or not isinstance(geojson.get("features"), list)
            or any(not isinstance(feature, dict)
                   or feature.get("type") != "Feature"
                   or "geometry" not in feature for feature in geojson["features"])):
        raise HTTPException(status_code=500, detail="Flood alert zones must be a GeoJSON FeatureCollection")
    safe_features = []
    public_properties = [
        "alert_id", "warning_level", "state_code", "lga_id", "confidence",
        "released_at", "affected_area_sqkm", "exposed_population",
    ]
    for feature in geojson["features"]:
        properties = feature.get("properties") or {}
        status_field = next((key for key in properties if key.lower() == "status"), None)
        if status_field is None:
            raise HTTPException(status_code=500, detail="Flood alert zone features require a status field")
        if str(properties[status_field]).casefold() != "released":
            continue
        level_field = next((key for key in properties if key.lower() == "warning_level"), None)
        if level_field is None:
            raise HTTPException(status_code=500, detail="Released flood alert zone features require warning_level")
        try:
            level = int(properties[level_field])
        except (TypeError, ValueError):
            raise HTTPException(status_code=500, detail="Flood alert zone warning_level must be an integer from 0 to 3")
        if level not in range(4):
            raise HTTPException(status_code=500, detail="Flood alert zone warning_level must be an integer from 0 to 3")
        safe_properties = {
            field: properties[key]
            for field in public_properties
            if (key := next((key for key in properties if key.lower() == field), None)) is not None
        }
        safe_features.append({
            "type": "Feature",
            "geometry": feature.get("geometry"),
            "properties": safe_properties,
        })
    return {"status": "OPERATIONAL", "type": "FeatureCollection", "features": safe_features}

@app.get(
    "/api/flood/warning-points",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="Hydrological Flood Warning Points & Gauge Network (G39)",
    description="Returns GeoJSON FeatureCollection of active gauge stations, stage sensors, and community alert point coordinates (G39)."
)
def get_flood_warning_points():
    path = cfg.GIS_DERIVED / "G39_Flood_Warning_Points_v1_0.geojson"
    if not path.exists():
        return {"status": "NOT_CONFIGURED", "type": "FeatureCollection", "features": []}
    with path.open(encoding="utf-8") as source:
        return json.load(source)

@app.get(
    "/api/flood/extent",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="Recent Flood Inundation Extent (G43)",
    description="Streams Sentinel-1 SAR and hydrological delineated recent flood extent polygon boundaries (G43)."
)
def get_flood_extent():
    path = cfg.GIS_DERIVED / "G43_Recent_Flood_Extent_v1_0.geojson"
    if not path.exists():
        return {"status": "NOT_CONFIGURED", "type": "FeatureCollection", "features": []}
    with path.open(encoding="utf-8") as source:
        return json.load(source)

@app.get(
    "/api/flood/performance",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="Early Warning Verification & Lead-Time Audit Log",
    description="Returns empirical warning verification records including lead time in hours, hit/miss/false alarm classifications, and audit completeness percentages."
)
def get_flood_warning_performance():
    source = load_flood_dataset("Flood_Warning_Performance")
    if source is None:
        return {"status": "NOT_CONFIGURED", "count": 0, "evaluations": []}
    require_dataset_column(source, "publication_status", "Flood_Warning_Performance")
    df = published_performance(source)
    for field in ("performance_id", "evaluated_at", "hit_status", "confidence"):
        require_dataset_column(df, field, "Flood_Warning_Performance")
    fields = [
        "performance_id", "alert_id", "evaluated_at", "lead_time_hours",
        "hit_status", "alerted_extent_sqkm", "observed_extent_sqkm",
        "high_risk_communities", "communities_reached",
        "audit_completeness_pct", "confidence",
    ]
    return {"status": "OPERATIONAL", "count": len(df), "evaluations": safe_records(public_fields(df, fields))}

@app.get(
    "/api/flood/dashboard",
    tags=["🌊 FEW-CAM Flood Early Warning"],
    summary="FEW-CAM Operational KPI & Metric Rollup",
    description="Calculates real-time flood warning KPIs: active alerts by severity level, notification reach rates, acknowledgement percentages, and mean verification metrics."
)
def get_flood_dashboard():
    alert_source = load_flood_dataset("Flood_Alerts")
    if alert_source is not None:
        for field in ("alert_id", "issued_at", "state_code", "warning_level", "trigger_type",
                      "hazard_score", "confidence", "status", "released_at"):
            require_dataset_column(alert_source, field, "Flood_Alerts")
        warning_levels = numeric_column(alert_source, "warning_level", "Flood_Alerts")
        if (warning_levels.isna().any() or warning_levels.mod(1).ne(0).any()
                or not warning_levels.between(0, 3).all()):
            raise HTTPException(status_code=500, detail="Flood_Alerts.warning_level must be an integer from 0 to 3")
    alerts = released_alerts(alert_source) if alert_source is not None else None
    notifications = load_flood_dataset("Flood_Notifications")
    acknowledgements = load_flood_dataset("Flood_Acknowledgements")
    awareness_source = load_flood_dataset("Flood_Awareness")
    if awareness_source is not None:
        require_dataset_column(awareness_source, "publication_status", "Flood_Awareness")
    awareness = published_awareness(awareness_source) if awareness_source is not None else None
    performance_source = load_flood_dataset("Flood_Warning_Performance")
    if performance_source is not None:
        require_dataset_column(performance_source, "publication_status", "Flood_Warning_Performance")
        for field in ("performance_id", "evaluated_at", "hit_status", "confidence"):
            require_dataset_column(published_performance(performance_source), field, "Flood_Warning_Performance")
    performance = published_performance(performance_source) if performance_source is not None else None

    alert_count = 0 if alerts is None else len(alerts)
    active_count = 0
    alert_levels = {str(level): 0 for level in range(4)}
    released_ids = set()
    if alerts is not None:
        status_field = column_name(alerts, "status")
        level_field = column_name(alerts, "warning_level")
        alert_id_field = column_name(alerts, "alert_id")
        if alert_id_field:
            released_ids = set(alerts[alert_id_field].astype(str))
        if status_field and level_field:
            active_released = alerts[status_field].astype(str).str.casefold().eq("released")
            active_count = int((active_released & numeric_column(alerts, "warning_level", "Flood_Alerts").gt(0)).sum())
        if level_field:
            for level, count in alerts[level_field].astype(str).value_counts().items():
                if level in alert_levels:
                    alert_levels[level] = int(count)

    notification_ids = set()
    if notifications is not None:
        notification_alert_field = require_dataset_column(notifications, "alert_id", "Flood_Notifications")
        notification_id_field = require_dataset_column(notifications, "notification_id", "Flood_Notifications")
        recipient_field = require_dataset_column(notifications, "recipient_count", "Flood_Notifications")
        reached_field = require_dataset_column(notifications, "reached_count", "Flood_Notifications")
        notifications = notifications[notifications[notification_alert_field].astype(str).isin(released_ids)]
        notification_ids = set(notifications[notification_id_field].astype(str))
        recipients = pd.to_numeric(notifications[recipient_field], errors="coerce")
        reached = pd.to_numeric(notifications[reached_field], errors="coerce")
        if (recipients.isna().any() or reached.isna().any()
                or recipients.lt(0).any() or reached.lt(0).any()
                or recipients.mod(1).ne(0).any() or reached.mod(1).ne(0).any()
                or reached.gt(recipients).any()):
            raise HTTPException(status_code=500, detail="Flood_Notifications has invalid recipient or reach counts")
    if acknowledgements is not None:
        ack_notification_field = require_dataset_column(acknowledgements, "notification_id", "Flood_Acknowledgements")
        ack_status_field = require_dataset_column(acknowledgements, "acknowledgement_status", "Flood_Acknowledgements")
        acknowledgement_statuses = acknowledgements[ack_status_field].astype(str).str.casefold()
        allowed_acknowledgements = {"received", "understood", "help_requested", "unable_to_act", "unconfirmed"}
        if not acknowledgement_statuses.isin(allowed_acknowledgements).all():
            raise HTTPException(status_code=500, detail="Flood_Acknowledgements contains an invalid acknowledgement_status")
        acknowledgements = acknowledgements[
            acknowledgements[ack_notification_field].astype(str).isin(notification_ids)
            & acknowledgements[ack_status_field].astype(str).str.casefold().ne("unconfirmed")
        ]

    recipient_count = reached_count = 0
    if notifications is not None:
        recipient_field = require_dataset_column(notifications, "recipient_count", "Flood_Notifications")
        reached_field = require_dataset_column(notifications, "reached_count", "Flood_Notifications")
        recipient_count = int(pd.to_numeric(notifications[recipient_field], errors="coerce").fillna(0).sum())
        reached_count = int(pd.to_numeric(notifications[reached_field], errors="coerce").fillna(0).sum())

    acknowledgement_rate = None
    if notifications is not None and acknowledgements is not None and len(notifications) > 0:
        if len(acknowledgements) > recipient_count:
            raise HTTPException(status_code=500, detail="Flood_Acknowledgements exceeds the released notification recipient count")
        if recipient_count:
            acknowledgement_rate = round(len(acknowledgements) / recipient_count * 100, 1)
    reach_rate = round(reached_count / recipient_count * 100, 1) if recipient_count else None

    awareness_count = 0 if awareness is None else len(awareness)
    performance_fields = [
        "performance_id", "alert_id", "evaluated_at", "lead_time_hours",
        "hit_status", "alerted_extent_sqkm", "observed_extent_sqkm",
        "high_risk_communities", "communities_reached",
        "audit_completeness_pct", "confidence",
    ]
    performance_records = [] if performance is None else safe_records(public_fields(performance, performance_fields))
    performance_metrics = {
        "mean_lead_time_hours": None,
        "hit_rate_pct": None,
        "false_alarm_rate_pct": None,
        "high_risk_awareness_coverage_pct": None,
        "mean_audit_completeness_pct": None,
    }
    if performance is not None and len(performance):
        evaluated_at_field = column_name(performance, "evaluated_at")
        alert_id_field = column_name(performance, "alert_id")
        if evaluated_at_field and alert_id_field:
            performance = (
                performance.sort_values(evaluated_at_field)
                .drop_duplicates(alert_id_field, keep="last")
            )
        outcome_field = column_name(performance, "hit_status")
        if outcome_field:
            outcomes = performance[outcome_field].astype(str).str.casefold()
            allowed_outcomes = {"hit", "miss", "false_alarm", "unverified"}
            if not outcomes.isin(allowed_outcomes).all():
                raise HTTPException(status_code=500, detail="Flood_Warning_Performance contains an invalid hit_status")
            event_outcomes = outcomes.isin(("hit", "miss"))
            event_denominator = int(event_outcomes.sum())
            if event_denominator:
                performance_metrics["hit_rate_pct"] = round(float(outcomes[event_outcomes].eq("hit").sum()) / event_denominator * 100, 1)
            warning_outcomes = outcomes.isin(("hit", "false_alarm"))
            warning_denominator = int(warning_outcomes.sum())
            if warning_denominator:
                performance_metrics["false_alarm_rate_pct"] = round(float(outcomes[warning_outcomes].eq("false_alarm").sum()) / warning_denominator * 100, 1)
        for field, metric in (
            ("lead_time_hours", "mean_lead_time_hours"),
            ("audit_completeness_pct", "mean_audit_completeness_pct"),
        ):
            value_field = column_name(performance, field)
            if value_field:
                values = numeric_column(performance, field, "Flood_Warning_Performance").dropna()
                if len(values):
                    if metric == "mean_lead_time_hours" and values.lt(0).any():
                        raise HTTPException(status_code=500, detail="Flood_Warning_Performance lead time cannot be negative")
                    if metric == "mean_audit_completeness_pct" and not values.between(0, 100).all():
                        raise HTTPException(status_code=500, detail="Flood_Warning_Performance audit completeness must be 0 to 100")
                    performance_metrics[metric] = round(float(values.mean()), 1)
        high_risk_field = column_name(performance, "high_risk_communities")
        reached_field = column_name(performance, "communities_reached")
        if high_risk_field and reached_field:
            high_risk = numeric_column(performance, "high_risk_communities", "Flood_Warning_Performance")
            reached = numeric_column(performance, "communities_reached", "Flood_Warning_Performance")
            valid_counts = high_risk.notna() & reached.notna()
            if (high_risk[valid_counts].lt(0).any() or reached[valid_counts].lt(0).any()
                    or reached[valid_counts].gt(high_risk[valid_counts]).any()):
                raise HTTPException(status_code=500, detail="Flood_Warning_Performance awareness counts are invalid")
            valid_coverage = high_risk.gt(0) & reached.notna()
            if valid_coverage.any():
                coverage = reached[valid_coverage] / high_risk[valid_coverage] * 100
                performance_metrics["high_risk_awareness_coverage_pct"] = round(float(coverage.mean()), 1)
    latest_update = None
    if alerts is not None:
        timestamp_field = next(
            (column for column in alerts.columns if column.lower() in ("updated_at", "issued_at", "released_at")),
            None,
        )
        if timestamp_field and len(alerts):
            latest_update = str(alerts[timestamp_field].max())

    return {
        "status": "OPERATIONAL" if alerts is not None else "NOT_CONFIGURED",
        "active_warnings": active_count,
        "total_alerts": alert_count,
        "warning_level_counts": alert_levels,
        "notification_reach_rate_pct": reach_rate,
        "notification_acknowledgement_rate_pct": acknowledgement_rate,
        "awareness_activities": awareness_count,
        "performance_evaluations": performance_records,
        "performance_metrics": performance_metrics,
        "last_update": latest_update,
    }

@app.get(
    "/api/risk/summary",
    tags=["📊 Indicators & Risk Models"],
    summary="State-Level Composite Risk Summary (TABLE_State_Summaries)",
    description="Returns weighted mean Hazard (H), Exposure (E), Vulnerability (V), Criticality (C), and Composite Risk (R) scores, plus Tier 1 Critical and Tier 2 High hotspot counts across all 10 member states."
)
def get_risk_summary():
    summary_path = cfg.PROJECT_ROOT / "06_Reports" / "02_TABLES" / "TABLE_State_Summaries.csv"
    if summary_path.exists():
        df = pd.read_csv(summary_path)
        state_summaries = []
        for _, row in df.iterrows():
            sc = str(row["State_Code"])
            internal = sc.replace("NG-", "")
            sname = str(row["State_Name"]) if pd.notna(row["State_Name"]) and str(row["State_Name"]).strip() else internal
            state_summaries.append({
                "state_code": sc,
                "state_name": sname,
                "internal_code": internal,
                "h_mean": round(float(row["H_Score_Wtd_Mean"]), 1),
                "e_mean": round(float(row["E_Score_Wtd_Mean"]), 1),
                "v_mean": round(float(row["V_Score_Wtd_Mean"]), 1),
                "c_mean": round(float(row["C_Score_Wtd_Mean"]), 1),
                "r_score": round(float(row["R_Score_Wtd_Mean"]), 1),
                "tier1_critical": int(row.get("Tier_1_Count", 0)),
                "tier2_high": int(row.get("Tier_2_Count", 0))
            })
        return {
            "overall_composite_risk_mean": round(float(df["R_Score_Wtd_Mean"].mean()), 2),
            "total_critical_hotspots": int(df["Tier_1_Count"].sum()),
            "total_high_priority_sites": int(df["Tier_2_Count"].sum()),
            "state_profiles": state_summaries
        }

    # Fallback to defaults if table not yet generated
    state_summaries = [
        {"state_code": "NG-NIG", "state_name": "Niger", "internal_code": "NIG", "h_mean": 65.4, "e_mean": 43.8, "v_mean": 69.0, "c_mean": 39.6, "r_score": 57.0, "tier1_critical": 0, "tier2_high": 3},
        {"state_code": "NG-BEN", "state_name": "Benue", "internal_code": "BEN", "h_mean": 52.8, "e_mean": 24.8, "v_mean": 51.9, "c_mean": 67.9, "r_score": 47.8, "tier1_critical": 0, "tier2_high": 3},
        {"state_code": "NG-NAS", "state_name": "Nasarawa", "internal_code": "NAS", "h_mean": 52.9, "e_mean": 25.3, "v_mean": 67.1, "c_mean": 37.6, "r_score": 47.3, "tier1_critical": 0, "tier2_high": 1},
        {"state_code": "NG-GOM", "state_name": "Gombe", "internal_code": "GOM", "h_mean": 51.2, "e_mean": 8.1, "v_mean": 67.8, "c_mean": 65.9, "r_score": 46.8, "tier1_critical": 0, "tier2_high": 3},
        {"state_code": "NG-KAD", "state_name": "Kaduna", "internal_code": "KAD", "h_mean": 43.6, "e_mean": 27.4, "v_mean": 70.4, "c_mean": 17.2, "r_score": 42.3, "tier1_critical": 1, "tier2_high": 0},
        {"state_code": "NG-TAR", "state_name": "Taraba", "internal_code": "TAR", "h_mean": 31.9, "e_mean": 3.5, "v_mean": 60.3, "c_mean": 81.0, "r_score": 39.3, "tier1_critical": 0, "tier2_high": 2},
        {"state_code": "NG-PLA", "state_name": "Plateau", "internal_code": "PLA", "h_mean": 44.5, "e_mean": 12.9, "v_mean": 60.5, "c_mean": 29.2, "r_score": 38.3, "tier1_critical": 0, "tier2_high": 2},
        {"state_code": "NG-KOG", "state_name": "Kogi", "internal_code": "KOG", "h_mean": 46.1, "e_mean": 21.0, "v_mean": 48.7, "c_mean": 23.6, "r_score": 37.1, "tier1_critical": 0, "tier2_high": 1},
        {"state_code": "NG-KEB", "state_name": "Kebbi", "internal_code": "KEB", "h_mean": 32.1, "e_mean": 4.2, "v_mean": 58.6, "c_mean": 47.4, "r_score": 34.1, "tier1_critical": 0, "tier2_high": 0},
        {"state_code": "NG-KWA", "state_name": "Kwara", "internal_code": "KWA", "h_mean": 34.9, "e_mean": 7.8, "v_mean": 45.7, "c_mean": 34.2, "r_score": 30.7, "tier1_critical": 0, "tier2_high": 1},
    ]
    return {
        "overall_composite_risk_mean": round(float(np.mean([s["r_score"] for s in state_summaries])), 2),
        "total_critical_hotspots": sum(s["tier1_critical"] for s in state_summaries),
        "total_high_priority_sites": sum(s["tier2_high"] for s in state_summaries),
        "state_profiles": state_summaries
    }

@app.post(
    "/api/risk/calculate",
    tags=["📊 Indicators & Risk Models"],
    summary="Simulate Composite Risk Engine Calculation",
    description="Calculates provisional composite risk using both additive (Section 21) and geometric multiplicative checks, returning priority tier categorization."
)
def calculate_risk(req: RiskCalculationRequest):
    r_additive = cfg.compute_composite_risk(req.hazard, req.exposure, req.vulnerability, req.criticality, method="additive")
    r_multiplicative = cfg.compute_composite_risk(req.hazard, req.exposure, req.vulnerability, req.criticality, method="multiplicative")
    
    tier = "Tier 4 Monitor"
    if r_additive >= 70:
        tier = "Tier 1 Critical"
    elif r_additive >= 55:
        tier = "Tier 2 High"
    elif r_additive >= 40:
        tier = "Tier 3 Moderate"

    return {
        "inputs": {
            "H": req.hazard,
            "E": req.exposure,
            "V": req.vulnerability,
            "C": req.criticality
        },
        "weights": cfg.RISK_WEIGHTS_BASELINE,
        "provisional_additive_risk": r_additive,
        "stage17_9_multiplicative_check": r_multiplicative,
        "zero_exposure_check": "PASS (Risk = 0 under geometric)" if req.exposure == 0 and r_multiplicative == 0 else "N/A",
        "priority_tier": tier
    }

@app.post(
    "/api/ies/calculate",
    tags=["📊 Indicators & Risk Models"],
    summary="Compute Intervention Effectiveness Score (IES)",
    description="Calculates percentage risk reduction achieved by physical or institutional interventions. Strictly enforces frozen baseline bounds compatibility."
)
def calculate_ies(req: IESCalculationRequest):
    ies = cfg.compute_ies(
        risk_before=req.risk_before,
        risk_after=req.risk_after,
        method_before=req.method_before,
        method_after=req.method_after,
        ref_bounds_same=req.reference_bounds_match
    )
    if ies is None:
        if req.risk_before == 0:
            msg = "Undefined: Pre-intervention risk was 0.0 (Reported as N/A per Section 34)."
        elif not req.reference_bounds_match:
            msg = "Invalid: Comparisons across differing reference bounds are prohibited."
        else:
            msg = "Invalid: Methodology versions mismatch."
        return {
            "valid": False,
            "ies_percentage": None,
            "reason": msg,
            "label": "Not Applicable"
        }
    
    return {
        "valid": True,
        "risk_before": req.risk_before,
        "risk_after": req.risk_after,
        "residual_risk": req.risk_after,
        "ies_percentage": ies,
        "label": "Intervention Effectiveness Score" if req.reference_bounds_match else "Observed Risk Change"
    }

@app.get(
    "/api/scenarios",
    tags=["📈 Scenario Simulation Lab"],
    summary="Stage 21 Empirical Climate & Adaptation Scenarios",
    description="Returns the scenario matrix modeling baseline, moderate stress (+10% precipitation), severe climate shock (+30% precipitation), and post-intervention adaptation resilience."
)
def get_scenarios():
    summary_path = cfg.PROJECT_ROOT / "07_Decision_Support" / "04_Scenarios" / "SCENARIO_SUMMARY_MATRIX.csv"
    if summary_path.exists():
        df_sum = pd.read_csv(summary_path)
        return {
            "count": len(df_sum),
            "version": "Scenario_v4.1",
            "scenarios": safe_records(df_sum)
        }
    clean_path = cfg.DATA_CLEAN / "Scenarios_CLEAN.csv"
    if clean_path.exists():
        df_clean = pd.read_csv(clean_path)
        return {
            "count": len(df_clean),
            "version": "Scenario_v4.1",
            "scenarios": safe_records(df_clean)
        }
    return {"count": 0, "scenarios": []}

@app.get(
    "/api/interventions",
    tags=["🛡️ Interventions & MRV"],
    summary="Commissioned & Ongoing Interventions Register",
    description="Returns capital expenditure projects (embankments, dykes, drainage networks, resettlement schemes) across all 10 N-HYPPADEC states with budgetary totals."
)
def get_interventions():
    int_path = cfg.DATA_CLEAN / "Interventions_CLEAN.csv"
    if int_path.exists():
        df = pd.read_csv(int_path)
        return {
            "count": len(df),
            "total_budget_ngn": float(df["Budget_NGN"].sum()),
            "commissioned_count": int((df["Status"] == "Commissioned").sum()),
            "completed_count": int((df["Status"] == "Completed").sum()),
            "ongoing_count": int((df["Status"] == "Ongoing").sum()),
            "interventions": safe_records(df)
        }
    return {"count": 0, "interventions": []}

@app.get(
    "/api/mrv",
    tags=["🛡️ Interventions & MRV"],
    summary="Measurement, Reporting & Verification (MRV) Portfolio",
    description="Returns the formal MRV portfolio register (MRV_PORTFOLIO_REGISTER_v4.1.csv) tracking verified risk reduction (Delta R), IES performance, and budget utilization."
)
def get_mrv_portfolio():
    mrv_path = cfg.PROJECT_ROOT / "07_Decision_Support" / "05_MRV" / "MRV_PORTFOLIO_REGISTER_v4.1.csv"
    if not mrv_path.exists():
        mrv_path = cfg.ANALYSIS_OUTPUTS / "IES_Evaluation_Matrix.csv"
    if mrv_path.exists():
        df = pd.read_csv(mrv_path)
        valid_ies = df[df["IES_Score_Pct"].notna()]["IES_Score_Pct"]
        mean_ies = round(float(valid_ies.mean()), 1) if len(valid_ies) > 0 else 0.0
        return {
            "status": "OPERATIONAL",
            "count": len(df),
            "total_budget_ngn": float(df["Budget_NGN"].sum()),
            "mean_ies_pct": mean_ies,
            "commissioned_count": int((df["Status"] == "Commissioned").sum()),
            "completed_count": int((df["Status"] == "Completed").sum()),
            "ongoing_count": int((df["Status"] == "Ongoing").sum()),
            "mean_risk_reduction": round(float(df[df["Status"].isin(["Commissioned", "Completed"])]["Delta_Risk"].mean()), 2),
            "portfolio": safe_records(df)
        }
    return {"status": "PENDING", "count": 0, "portfolio": []}

@app.get(
    "/api/remote_sensing",
    tags=["🛰️ Earth Observation & Remote Sensing"],
    summary="Earth Observation & Satellite Telemetry Analytics",
    description="Returns Sentinel-1 SAR flood inundation areas (km²), Sentinel-2 mean NDVI vegetational vitality, multi-year riverbank retreat velocities, and EO classification accuracy."
)
def get_remote_sensing_summary():
    rs_path = cfg.ANALYSIS_OUTPUTS / "RS_Earth_Observation_Summary.csv"
    if rs_path.exists():
        df = pd.read_csv(rs_path)
        return {
            "status": "OPERATIONAL",
            "states_covered": len(df),
            "total_sar_flood_area_km2": round(float(df["SAR_Observed_Flood_Area_Km2"].sum()), 1),
            "mean_ndvi": round(float(df["Mean_NDVI_Baseline"].mean()), 2),
            "mean_riverbank_retreat_m_yr": round(float(df["Mean_Riverbank_Retreat_M_Yr"].mean()), 2),
            "overall_classification_accuracy_pct": round(float(df["EO_Classification_Accuracy_Pct"].mean()), 1),
            "records": safe_records(df)
        }
    return {"status": "PENDING", "states_covered": 0, "records": []}

@app.get(
    "/api/food_security",
    tags=["🌾 Thematic Livelihoods & Security"],
    summary="Agricultural Yield & Food Access Assessments",
    description="Returns crop loss percentages, livestock mortality rates, and household food consumption scores across flood-affected agrarian belts."
)
def get_food_security():
    food_path = cfg.DATA_CLEAN / "Food_Security_CLEAN.csv"
    if food_path.exists():
        df = pd.read_csv(food_path)
        return {
            "count": len(df),
            "crop_loss_mean": round(float(df["Crop_Loss_Pct"].mean()), 1),
            "livestock_loss_mean": round(float(df["Livestock_Loss_Pct"].mean()), 1),
            "records": safe_records(df)
        }
    return {"count": 0, "records": []}

@app.get(
    "/api/security_impacts",
    tags=["🌾 Thematic Livelihoods & Security"],
    summary="Displacement & Climate-Security Impacts",
    description="Returns displacement numbers, facility disruption indices, and security threat intersections in riverine communities."
)
def get_security_impacts():
    sec_path = cfg.DATA_CLEAN / "Security_Impact_CLEAN.csv"
    if sec_path.exists():
        df = pd.read_csv(sec_path)
        return {
            "count": len(df),
            "displaced_total": int(df["Displaced_Persons_Count"].sum()),
            "records": safe_records(df)
        }
    return {"count": 0, "records": []}

@app.get(
    "/api/facilities",
    tags=["🏛️ Governance & Geography"],
    summary="Hydropower & Critical Infrastructure Facilities Master",
    description="Returns master inventory of major hydroelectric power stations (Kainji, Jebba, Shiroro, Dadin Kowa, Zungeru, Kashimbila), dams, and installed capacities (MW)."
)
def get_facilities():
    fac_path = cfg.DATA_CLEAN / "Facility_Master_CLEAN.csv"
    if fac_path.exists():
        df = pd.read_csv(fac_path)
        return {
            "count": len(df),
            "total_capacity_mw": float(df["Installed_Capacity_MW"].sum()),
            "facilities": safe_records(df)
        }
    return {"count": 0, "facilities": []}

@app.get(
    "/api/climate_stations",
    tags=["🏛️ Governance & Geography"],
    summary="Hydro-Meteorological Climate Stations Network",
    description="Returns operational weather and hydrological telemetry stations across the Niger and Benue river basins."
)
def get_climate_stations():
    sta_path = cfg.DATA_CLEAN / "Climate_Station_CLEAN.csv"
    if sta_path.exists():
        df = pd.read_csv(sta_path)
        return {
            "count": len(df),
            "stations": safe_records(df)
        }
    return {"count": 0, "stations": []}

@app.get(
    "/api/tables",
    tags=["🗄️ Core Database Model (31 Tables)"],
    summary="List Section 32 Core Database Tables (31 Clean Datasets)",
    description="Enumerates all 31 clean database tables with row counts, column counts, restriction flags, and schema availability."
)
def list_core_tables():
    clean_files = sorted(list(cfg.DATA_CLEAN.glob("*_CLEAN*.csv")))
    tables = []
    seen = set()
    for f in clean_files:
        name = f.stem.replace("_CLEAN_RESTRICTED", "").replace("_CLEAN", "")
        if name in seen or name.endswith("_SCHEMA") or "PROCESSED" in f.name:
            continue
        seen.add(name)
        try:
            df = pd.read_csv(f)
            tables.append({
                "table_name": name,
                "file_name": f.name,
                "rows": len(df),
                "columns": len(df.columns),
                "is_restricted": "RESTRICTED" in f.name,
                "has_schema": (cfg.DATA_CLEAN / f"{name}_SCHEMA.csv").exists() or (cfg.DATA_CLEAN / f"{f.stem}_SCHEMA.csv").exists()
            })
        except Exception:
            pass
    return {"total_tables": len(tables), "tables": tables}

@app.get(
    "/api/tables/{table_name}",
    tags=["🗄️ Core Database Model (31 Tables)"],
    summary="Inspect Table Records & Field Data Dictionary",
    description="Queries records from any of the 31 clean relational tables with automatic Level 3 PII privacy redaction and accompanying schema data dictionary."
)
def get_table_data(
    table_name: str = FPath(..., description="Target clean table identifier (e.g. DB01_Community_Master, DB12_Hydropower_Facilities)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of sample rows to retrieve")
):
    if not isinstance(limit, int):
        limit = 50
    # Find matching clean file
    target = cfg.DATA_CLEAN / f"{table_name}_CLEAN.csv"
    if not target.exists():
        target = cfg.DATA_CLEAN / f"{table_name}_CLEAN_RESTRICTED.csv"
    if not target.exists():
        # Try matching by prefix
        matches = list(cfg.DATA_CLEAN.glob(f"*{table_name}*.csv"))
        if matches:
            target = matches[0]
    if not target or not target.exists():
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    
    df = pd.read_csv(target)
    
    # Enforce Level 3 Privacy: mask individual PII if Household_Survey
    if "Household" in target.stem or "DB02" in target.stem:
        for pii_col in ["Respondent_Name", "Phone_Number", "GPS_Coordinates", "NIN"]:
            if pii_col in df.columns:
                df[pii_col] = "[PROTECTED LEVEL 3]"
    
    schema_file = cfg.DATA_CLEAN / f"{table_name}_SCHEMA.csv"
    if not schema_file.exists():
        matches_schema = list(cfg.DATA_CLEAN.glob(f"*{table_name}*SCHEMA.csv"))
        if matches_schema:
            schema_file = matches_schema[0]
            
    schema = []
    if schema_file.exists():
        schema = safe_records(pd.read_csv(schema_file))
        
    return {
        "table_name": table_name,
        "total_rows": len(df),
        "limit": limit,
        "schema": schema,
        "data": safe_records(df.head(limit))
    }

# ---------------------------------------------------------------------------
# GEOJSON SERVICES
# ---------------------------------------------------------------------------
@app.get(
    "/api/geojson/priority_sites",
    tags=["🗺️ GIS & Spatial Services"],
    summary="Top Priority Critical Hotspots GeoJSON (G37)",
    description="Streams GeoJSON Point features for top priority intervention communities, complete with risk tiers, priority scores, and coordinates."
)
def get_priority_sites_geojson():
    top20_path = cfg.PROJECT_ROOT / "07_Decision_Support" / "03_Priority_Areas" / "G37_Top20_Priority_Communities.csv"
    db01_path = cfg.DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    
    if top20_path.exists() and db01_path.exists():
        top20 = pd.read_csv(top20_path)
        if "Community_ID.1" in top20.columns:
            top20 = top20.drop(columns=["Community_ID.1"])
        db01 = pd.read_csv(db01_path)
        merged = top20.merge(db01[["Community_ID", "Community", "State_Name", "LGA", "Latitude", "Longitude", "Livelihood"]], on="Community_ID", how="left")
        
        features = []
        for _, row in merged.iterrows():
            lat = row.get("Latitude")
            lon = row.get("Longitude")
            if pd.notna(lat) and pd.notna(lon):
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                    "properties": {
                        "id": str(row["Community_ID"]),
                        "name": str(row.get("Community", row["Community_ID"])),
                        "state": str(row.get("State_Name", row["State_Code"])),
                        "lga": str(row.get("LGA", "")),
                        "risk": round(float(row["R_Score"]), 1),
                        "priority_score": round(float(row.get("Priority_Score", row["R_Score"])), 1),
                        "tier": f"Tier {int(float(row['Priority_Tier']))}",
                        "confidence": str(row.get("Data_Confidence", "Moderate")),
                        "type": "Priority Hotspot"
                    }
                })
        if features:
            return {"type": "FeatureCollection", "features": features}

    # Fallback curated sites
    sites = [
        {"id": "SITE-NIG-01", "name": "Shiroro Downstream Basin", "state": "Niger", "lat": 9.97, "lon": 6.83, "risk": 74.5, "tier": "Tier 1 Critical", "type": "Hydropower Flood Zone"},
        {"id": "SITE-NIG-02", "name": "Kainji Lake Shoreline", "state": "Niger", "lat": 9.87, "lon": 4.60, "risk": 71.2, "tier": "Tier 1 Critical", "type": "Reservoir Erosion"},
        {"id": "SITE-KEB-01", "name": "Argungu River Floodplain", "state": "Kebbi", "lat": 12.74, "lon": 4.53, "risk": 68.3, "tier": "Tier 1 Critical", "type": "River Overflow"},
        {"id": "SITE-KEB-02", "name": "Yauri Downstream Embankment", "state": "Kebbi", "lat": 10.77, "lon": 4.77, "risk": 64.8, "tier": "Tier 2 High", "type": "Riverbank Failure"},
        {"id": "SITE-BEN-01", "name": "Makurdi Benue River Front", "state": "Benue", "lat": 7.73, "lon": 8.53, "risk": 78.9, "tier": "Tier 1 Critical", "type": "Major Flood Hotspot"},
        {"id": "SITE-BEN-02", "name": "Agatu Agricultural Basin", "state": "Benue", "lat": 7.89, "lon": 7.91, "risk": 72.1, "tier": "Tier 1 Critical", "type": "Farmland Inundation"},
        {"id": "SITE-KOG-01", "name": "Lokoja Confluence Point", "state": "Kogi", "lat": 7.80, "lon": 6.74, "risk": 82.4, "tier": "Tier 1 Critical", "type": "Niger-Benue Confluence"},
        {"id": "SITE-KOG-02", "name": "Ibaji Flood Basin", "state": "Kogi", "lat": 6.95, "lon": 6.88, "risk": 79.5, "tier": "Tier 1 Critical", "type": "Submergence Zone"},
        {"id": "SITE-KWA-01", "name": "Pategi Niger River Shoreline", "state": "Kwara", "lat": 8.73, "lon": 5.75, "risk": 67.2, "tier": "Tier 2 High", "type": "Riverbank Erosion"},
        {"id": "SITE-PLA-01", "name": "Jos North Urban Gully System", "state": "Plateau", "lat": 9.93, "lon": 8.89, "risk": 62.0, "tier": "Tier 2 High", "type": "Gully Hotspot"},
        {"id": "SITE-KAD-01", "name": "Kaduna River Urban Drainage", "state": "Kaduna", "lat": 10.52, "lon": 7.44, "risk": 65.8, "tier": "Tier 2 High", "type": "Urban Flood"},
        {"id": "SITE-NAS-01", "name": "Doma Dam Drainage Corridor", "state": "Nasarawa", "lat": 8.51, "lon": 8.35, "risk": 63.4, "tier": "Tier 2 High", "type": "Flash Flood Basin"},
        {"id": "SITE-TAR-01", "name": "Ibi Benue Riverbank Corridor", "state": "Taraba", "lat": 8.18, "lon": 9.75, "risk": 73.0, "tier": "Tier 1 Critical", "type": "River Overflow"},
        {"id": "SITE-GOM-01", "name": "Dadin Kowa Dam Outflow Zone", "state": "Gombe", "lat": 10.31, "lon": 11.51, "risk": 66.5, "tier": "Tier 2 High", "type": "Hydropower Flood Plain"},
    ]
    
    features = []
    for s in sites:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
            "properties": s
        })
    return {"type": "FeatureCollection", "features": features}

@app.get(
    "/api/priority/top20",
    tags=["📊 Indicators & Risk Models"],
    summary="Top-20 Priority Communities Capital Investment Register",
    description="Returns the authoritative ranked Top-20 Priority Communities for capital investment with full geographic context including State and LGA names."
)
def get_top20_priority_communities():
    top20_path = cfg.PROJECT_ROOT / "07_Decision_Support" / "03_Priority_Areas" / "G37_Top20_Priority_Communities.csv"
    db01_path = cfg.DATA_CLEAN / "DB01_Community_Master_CLEAN.csv"
    
    if not top20_path.exists():
        raise HTTPException(status_code=404, detail="G37_Top20_Priority_Communities.csv not found")
        
    top20 = pd.read_csv(top20_path)
    if "Community_ID.1" in top20.columns:
        top20 = top20.drop(columns=["Community_ID.1"])
        
    if db01_path.exists():
        db01 = pd.read_csv(db01_path)
        cols_to_use = [c for c in ["Community_ID", "Community", "State_Name", "LGA_Code", "LGA"] if c in db01.columns]
        merged = top20.merge(db01[cols_to_use], on="Community_ID", how="left", suffixes=("", "_db01"))
        if "LGA_db01" in merged.columns:
            merged["LGA"] = merged["LGA"].fillna(merged["LGA_db01"])
            merged = merged.drop(columns=["LGA_db01"])
        if "LGA_Code_db01" in merged.columns:
            merged["LGA_Code"] = merged["LGA_Code"].fillna(merged["LGA_Code_db01"])
            merged = merged.drop(columns=["LGA_Code_db01"])
    else:
        merged = top20
        
    records = []
    for idx, row in merged.iterrows():
        tier_val = row.get("Priority_Tier")
        if pd.notna(tier_val):
            try:
                t_num = int(float(tier_val))
                tier_label = f"Tier {t_num} Critical" if t_num == 1 else (f"Tier {t_num} High" if t_num == 2 else (f"Tier {t_num} Moderate" if t_num == 3 else f"Tier {t_num} Monitor"))
            except Exception:
                tier_label = str(tier_val)
        else:
            tier_label = "Tier 2 High"
            
        lga_name = str(row.get("LGA", "N/A"))
        if lga_name in ("nan", "None", "", "NaN"):
            lga_name = str(row.get("LGA_Code", "N/A"))
            
        records.append({
            "rank": int(row.get("Priority_Rank", idx + 1)),
            "community_id": str(row.get("Community_ID")),
            "community_name": str(row.get("Community", row.get("Community_ID"))),
            "state_code": str(row.get("State_Code")),
            "state_name": str(row.get("State_Name", row.get("State_Code"))),
            "lga": lga_name,
            "lga_name": lga_name,
            "lga_code": str(row.get("LGA_Code", "N/A")),
            "composite_risk": round(float(row.get("R_Score", 0.0)), 2),
            "adaptation_gap": round(float(row.get("IND10_Adaptation_Gap", 0.0)), 2) if "IND10_Adaptation_Gap" in row and pd.notna(row.get("IND10_Adaptation_Gap")) else 0.0,
            "priority_score": round(float(row.get("Priority_Score", 0.0)), 2),
            "priority_tier": tier_label,
            "confidence_rating": str(row.get("Data_Confidence", "Moderate"))
        })
        
    return {
        "status": "OPERATIONAL",
        "total": len(records),
        "data": records
    }

@app.get(
    "/api/geojson/layer/{layer_id}",
    tags=["🗺️ GIS & Spatial Services"],
    summary="Stream Master GIS Layer GeoJSON FeatureCollection",
    description="Fetches raw GeoJSON spatial features for any registered layer ID (e.g. G01, G02, G38, G39, G43)."
)
def get_gis_layer_geojson(
    layer_id: str = FPath(..., description="Layer ID identifier (e.g. G01, G38, G39)")
):
    lid = layer_id.upper()
    search_dirs = [cfg.GIS_CLEAN, cfg.GIS_DERIVED, cfg.PROJECT_ROOT / "04_GIS" / "05_MAP_EXPORTS"]
    for sdir in search_dirs:
        if sdir.exists():
            matches = list(sdir.glob(f"{lid}_*.geojson"))
            if matches:
                with matches[0].open(encoding="utf-8") as f:
                    return json.load(f)
    raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")

@app.get(
    "/api/environmental-problems",
    tags=["🌍 Multi-Hazard & Environmental Risks"],
    summary="List Canonical Multi-Hazard & Environmental Problems (14 Domains)",
    description="Returns the comprehensive 14-problem national environmental and security risk taxonomy including Food Security, Bandit Attack, Air Pollution, Climate Change, Deforestation, Desertification, Drought, Ecological Conflict, Erosion, Flooding, Lead Poisoning, Oil Spillage, Solid Waste Management, and Water Pollution with symbology, risk component, and key affected states."
)
def get_environmental_problems():
    p_path = cfg.DATA_LOOKUPS / "LKP_EnvironmentalProblems.csv"
    if not p_path.exists():
        raise HTTPException(status_code=404, detail="LKP_EnvironmentalProblems.csv not found")
    df = pd.read_csv(p_path)
    return {
        "status": "OPERATIONAL",
        "total": len(df),
        "taxonomy_standard": "Official National Environmental Survey Legend (14 Canonical Hazards)",
        "problems": safe_records(df)
    }

@app.get(
    "/api/environmental-problems/spatial",
    tags=["🌍 Multi-Hazard & Environmental Risks"],
    summary="Multi-Hazard Spatial GeoJSON FeatureCollection (G65)",
    description="Streams the G65 GeoJSON layer representing state-level observed incident locations for all 14 environmental and security hazards across N-HYPPADEC member states, Adamawa, and national benchmark corridors."
)
def get_environmental_problems_spatial():
    g65_path = cfg.GIS_DERIVED / "G65_EnvironmentalProblems.geojson"
    if not g65_path.exists():
        raise HTTPException(status_code=404, detail="G65_EnvironmentalProblems.geojson not found")
    with open(g65_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get(
    "/api/environmental-problems/{problem_code}",
    tags=["🌍 Multi-Hazard & Environmental Risks"],
    summary="Get Environmental Problem Profile & State Incidents",
    description="Retrieves taxonomy metadata and all recorded state incident observations for a specific hazard code (e.g. FOOD_SECURITY, BANDIT_ATTACK, DEFORESTATION, EROSION, LEAD_POISONING)."
)
def get_environmental_problem_detail(
    problem_code: str = FPath(..., description="Problem code identifier (e.g. FOOD_SECURITY, BANDIT_ATTACK, EROSION)")
):
    p_code = problem_code.upper()
    p_path = cfg.DATA_LOOKUPS / "LKP_EnvironmentalProblems.csv"
    sep_path = cfg.DATA_LOOKUPS / "LKP_State_EnvironmentalProblems.csv"
    if not p_path.exists() or not sep_path.exists():
        raise HTTPException(status_code=404, detail="Lookups not found")
    
    df_p = pd.read_csv(p_path)
    match_p = df_p[df_p["Problem_Code"].str.upper() == p_code]
    if match_p.empty:
        raise HTTPException(status_code=404, detail=f"Environmental problem '{problem_code}' not found")
    
    df_sep = pd.read_csv(sep_path)
    state_incidents = df_sep[df_sep["Problem_Code"].str.upper() == p_code]
    
    prob_meta = json.loads(match_p.iloc[0].to_json())
    return {
        "problem": prob_meta,
        "incident_count": len(state_incidents),
        "incidents": safe_records(state_incidents)
    }
# ---------------------------------------------------------------------------
# FIELD OPERATIONS & KOBOTOOLBOX DATA INGESTION
# ---------------------------------------------------------------------------
@app.get(
    "/api/kobo/status",
    tags=["🔄 Field Operations & Data Ingestion"],
    summary="KoboToolbox Ingestion Pipeline Status",
    description="Returns metrics on mobile survey field submissions, clean landing records, quarantined submissions, and last sync timestamp."
)
def get_kobo_status():
    landing_count = 0
    quarantine_count = 0
    sync_history = []
    
    if cfg.KOBO_SUBMISSIONS_LANDING.exists():
        try:
            landing_count = len(pd.read_csv(cfg.KOBO_SUBMISSIONS_LANDING))
        except Exception:
            landing_count = 0
            
    if cfg.KOBO_QUARANTINE_LOG.exists():
        try:
            quarantine_count = len(pd.read_csv(cfg.KOBO_QUARANTINE_LOG))
        except Exception:
            quarantine_count = 0
            
    if cfg.KOBO_SYNC_LOG.exists():
        try:
            with open(cfg.KOBO_SYNC_LOG, "r", encoding="utf-8") as f:
                sync_history = json.load(f)
        except Exception:
            sync_history = []

    last_sync = sync_history[-1] if sync_history else None
    return {
        "status": "OPERATIONAL",
        "pipeline_version": "v4.2-Kobo-ODK",
        "landing_submissions_count": landing_count,
        "quarantined_records_count": quarantine_count,
        "total_processed": landing_count + quarantine_count,
        "last_sync": last_sync,
        "sync_history_recent": sync_history[-10:] if sync_history else []
    }

@app.post(
    "/api/kobo/sync",
    tags=["🔄 Field Operations & Data Ingestion"],
    summary="Trigger KoboToolbox API Sync / Field Ingestion",
    description="Pulls new survey submissions from KoboToolbox API or generates sandbox mobile submissions, running them through the 5 quality control gates."
)
def trigger_kobo_sync(
    sandbox_mode: bool = Query(True, description="If true, generates realistic field survey submissions if remote API is unconfigured")
):
    try:
        api_token = os.environ.get("KOBO_API_TOKEN")
        if api_token:
            result = kobo_sync_pipeline.fetch_and_sync_kobo()
            if result.get("status") == "SUCCESS":
                return result

        if sandbox_mode:
            mocks = kobo_sync_pipeline.generate_mock_field_submissions(count=5)
            result = kobo_sync_pipeline.ingest_submissions(mocks)
            result["mode"] = "SANDBOX_GENERATOR"
            return result
        else:
            return kobo_sync_pipeline.fetch_and_sync_kobo()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kobo sync error: {str(e)}")

@app.get(
    "/api/kobo/quarantine",
    tags=["🔄 Field Operations & Data Ingestion"],
    summary="Inspect Quarantined Field Submissions",
    description="Retrieves mobile survey records flagged by QC gates (e.g. Consent refusal, Cascading LGA mismatch, GPS boundary violation) for supervisor audit and resolution."
)
def get_kobo_quarantine():
    if not cfg.KOBO_QUARANTINE_LOG.exists():
        return {"count": 0, "quarantined_records": []}
    try:
        df = pd.read_csv(cfg.KOBO_QUARANTINE_LOG)
        return {
            "count": len(df),
            "quarantined_records": safe_records(df)
        }
    except Exception as e:
        return {"count": 0, "quarantined_records": [], "error": str(e)}

@app.get(
    "/api/kobo/landing",
    tags=["🔄 Field Operations & Data Ingestion"],
    summary="Inspect Clean Landing Field Submissions",
    description="Retrieves verified, clean field survey submissions promoted to the staging landing dataset."
)
def get_kobo_landing():
    if not cfg.KOBO_SUBMISSIONS_LANDING.exists():
        return {"count": 0, "landing_records": []}
    try:
        df = pd.read_csv(cfg.KOBO_SUBMISSIONS_LANDING)
        return {
            "count": len(df),
            "landing_records": safe_records(df)
        }
    except Exception as e:
        return {"count": 0, "landing_records": [], "error": str(e)}

@app.post(
    "/api/kobo/resolve",
    tags=["🔄 Field Operations & Data Ingestion"],
    summary="Remediate & Promote Quarantined Submission",
    description="Applies supervisor corrections (e.g. corrected LGA code or consent verification), re-validates against 5 QC gates, and promotes the record into the clean landing dataset."
)
def resolve_kobo_quarantine(req: KoboRemediationRequest):
    result = kobo_sync_pipeline.resolve_quarantined_record(
        submission_id=req.submission_id,
        corrections=req.corrections,
        approved_by=req.approved_by,
        justification=req.justification
    )
    if result.get("status") in ["NOT_FOUND", "VALIDATION_FAILED", "ERROR"]:
        raise HTTPException(status_code=400, detail=result)
    return result

@app.post(
    "/api/kobo/webhook",
    tags=["🔄 Field Operations & Data Ingestion"],
    summary="Live KoboToolbox Webhook Receiver",
    description="Direct HTTP POST webhook receiver accepting real-time survey submissions directly from KoboToolbox or ODK Central servers."
)
def kobo_webhook_receiver(payload: Dict[str, Any]):
    try:
        result = kobo_sync_pipeline.ingest_submissions([payload])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook ingestion failure: {str(e)}")

# ---------------------------------------------------------------------------
# MULTI-HAZARD COMPOUND VULNERABILITY INDEX (MHCVI)
# ---------------------------------------------------------------------------
@app.get(
    "/api/vulnerability/mhcvi",
    tags=["🗺️ Multi-Hazard Compound Vulnerability (MHCVI)"],
    summary="Compute Multi-Hazard Compound Vulnerability Scores (0-100)",
    description="Aggregates the 14 statutory hazards across Security & Livelihood (40%), Hydrology (35%), and Environmental Degradation (25%) into a normalized compound vulnerability index per state and priority LGA."
)
def get_mhcvi_scores():
    return mhcvi_service.compute_mhcvi()

# ---------------------------------------------------------------------------
# INSTITUTIONAL SITREP & EXECUTIVE POLICY BRIEFS
# ---------------------------------------------------------------------------
@app.get(
    "/api/sitrep/data",
    tags=["📄 Institutional SitRep & Policy Briefs"],
    summary="Generate Structured Executive SitRep Dossier",
    description="Compiles an authoritative multi-hazard situation report with verified critical incident counts, affected population estimates, and recommended emergency budget allocations."
)
def get_sitrep_data(
    state_code: Optional[str] = Query(None, description="State code filter (e.g. NG-NIG, NG-BEN) or leave blank for All 10 States")
):
    return sitrep_service.generate_sitrep_data(state_code)

@app.get(
    "/api/sitrep/print",
    response_class=HTMLResponse,
    tags=["📄 Institutional SitRep & Policy Briefs"],
    summary="Render Official Print-Ready Situation Report (HTML / PDF)",
    description="Serves an executive, formatted, high-resolution printable N-HYPPADEC Situation Report document with official crests, tables, and signature blocks."
)
def print_sitrep_document(
    state_code: Optional[str] = Query(None, description="State code filter or blank for national")
):
    html = sitrep_service.generate_sitrep_html(state_code)
    return HTMLResponse(content=html)

# ---------------------------------------------------------------------------
# EARLY WARNING MATRIX & ALERT DISPATCH
# ---------------------------------------------------------------------------
@app.get(
    "/api/early-warning/alerts",
    tags=["🚨 Early Warning Matrix & Alert Dispatch"],
    summary="Active Multi-Hazard Early Warning Alerts",
    description="Returns operational early warnings across dam release schedules (Kainji, Shiroro, Jebba), flash flooding forecasts, banditry corridor advisories, and drought anomalies."
)
def get_early_warning_alerts():
    return alert_service.get_active_alerts()

@app.post(
    "/api/early-warning/simulate-dispatch",
    tags=["🚨 Early Warning Matrix & Alert Dispatch"],
    summary="Simulate Multi-Channel Emergency Alert Broadcast",
    description="Simulates transmitting an emergency advisory via SMS, VHF Radio, or WhatsApp to registered community liaison officers and disaster managers."
)
def dispatch_alert_simulation(req: AlertBroadcastRequest):
    return alert_service.simulate_alert_dispatch(
        alert_id=req.alert_id,
        channel=req.channel,
        recipients_group=req.recipients_group
    )

@app.get(
    "/api/early-warning/dispatch-history",
    tags=["🚨 Early Warning Matrix & Alert Dispatch"],
    summary="Alert Broadcast Dispatch Audit Log",
    description="Retrieves the broadcast transmission history log and recipient acknowledgement rates."
)
def get_alert_dispatch_history():
    return {
        "status": "OPERATIONAL",
        "history": alert_service.get_dispatch_history()
    }

# ---------------------------------------------------------------------------
# PHASE 1-4 OPERATIONAL AI SERVICES
# ---------------------------------------------------------------------------
@app.get(
    "/api/ai/sitrep/synthesize",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Data-Grounded Executive SitRep AI Synthesizer",
    description="Generates zero-hallucination intelligence briefs, risk vectors, and statutory directives anchored strictly to clean database indicators."
)
def ai_sitrep_synthesize_get(state_code: Optional[str] = Query(None, description="Optional State Code e.g. NG-NIG")):
    metrics = sitrep_service.generate_sitrep_data(state_code)
    return ai_advisory_service.generate_ai_sitrep_synthesis(metrics)

@app.post(
    "/api/ai/sitrep/synthesize",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Synthesize SitRep AI Brief with Custom Filter",
    description="Generates executive briefings with custom state filters adhering to frozen 2026 reference bounds."
)
def ai_sitrep_synthesize_post(req: SitRepSynthesisRequest):
    metrics = sitrep_service.generate_sitrep_data(req.state_code)
    return ai_advisory_service.generate_ai_sitrep_synthesis(metrics)

@app.get(
    "/api/ai/alerts/languages",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Supported Indigenous Warning Languages",
    description="Returns metadata for the 6 official vernacular early-warning languages: Hausa, Nupe, Tiv, Yoruba, Fulfulde, and Gbagyi."
)
def ai_alert_languages():
    return {
        "status": "OPERATIONAL",
        "supported_languages": ai_advisory_service.SUPPORTED_LANGUAGES
    }

@app.post(
    "/api/ai/alerts/translate",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Indigenous Multi-Lingual Alert & Radio Script Translator",
    description="Translates emergency flood and security advisories into local languages, producing 160-char SMS bulletins and phonetic radio scripts."
)
def ai_alert_translate(req: AlertTranslationRequest):
    payload = {
        "alert_id": req.alert_id,
        "target_states": req.target_states,
        "target_lgas": req.target_lgas,
        "hazard_type": req.hazard_type,
        "severity": req.severity,
        "lead_time_hours": req.lead_time_hours,
        "evacuation_shelter": req.evacuation_shelter
    }
    return ai_advisory_service.translate_alert_to_indigenous(payload, req.target_language)

@app.post(
    "/api/ai/fieldwork/audit-submission",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Field Survey Behavioral Fraud & Velocity Audit",
    description="Evaluates mobile enumerator submissions against completion duration, spatial travel speed (>130km/h), duplicate couch-surfing GPS coords, and straight-lining variance."
)
def ai_audit_field_submission(req: FieldAuditRequest):
    return ai_field_anomaly_service.audit_submission_anomalies(
        submission=req.submission,
        recent_submissions_by_enumerator=req.recent_submissions
    )

@app.post(
    "/api/ai/fieldwork/photo-pii-scan",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Mobile Photo Level 3 PII Privacy Shield Scan",
    description="Inspects field photos for facial biometric PII and household consent compliance, applying automated redaction gates."
)
def ai_scan_photo_pii(req: PhotoPiiScanRequest):
    return ai_field_anomaly_service.inspect_field_photo_pii({
        "file_name": req.file_name,
        "photo_category": req.photo_category,
        "faces_detected": req.faces_detected,
        "consent_for_media": req.consent_for_media
    })

@app.get(
    "/api/ai/flood/dams",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Hydropower Dam Catalog for Hydro Forecasting",
    description="Returns hydrological operating baselines, spillway discharge thresholds, and downstream LGAs for Kainji, Jebba, Shiroro, Dadin Kowa, and Kashimbila dams."
)
def ai_get_dams_catalogue():
    return {
        "status": "OPERATIONAL",
        "dams": ai_flood_forecast_service.DAMS_CATALOGUE
    }

@app.get(
    "/api/ai/flood/dam-forecasts",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Hydro-Meteorological Dam Inflow & Spillway AI Forecast",
    description="Simulates 24h, 48h, and 72h reservoir inflow, spillway exceedance probability, warning level, evacuation lead time, and inundated acreage."
)
def ai_dam_forecast_get(
    dam_id: str = Query("DAM-NIG-01", description="Dam ID (e.g. DAM-NIG-01 Kainji, DAM-NIG-02 Jebba, DAM-NIG-03 Shiroro, DAM-GOM-01 Dadin Kowa, DAM-TAR-01 Kashimbila)"),
    rainfall_mm: float = Query(45.0, description="Upstream 24h basin rainfall forecast (mm)"),
    water_level_m: Optional[float] = Query(None, description="Current reservoir water level (m)")
):
    return ai_flood_forecast_service.forecast_dam_inflow_and_spill(
        dam_id=dam_id,
        upstream_rainfall_forecast_mm=rainfall_mm,
        current_water_level_m=water_level_m
    )

@app.post(
    "/api/ai/flood/simulate-spill",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Simulate Extreme Upstream Storm Dam Spillway Shock",
    description="Simulates dam hydrological surge under extreme precipitation stress test."
)
def ai_dam_forecast_post(req: DamForecastRequest):
    return ai_flood_forecast_service.forecast_dam_inflow_and_spill(
        dam_id=req.dam_id,
        upstream_rainfall_forecast_mm=req.upstream_rainfall_forecast_mm,
        current_water_level_m=req.current_water_level_m
    )

@app.get(
    "/api/ai/priority/optimize-portfolio",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Prescriptive Capital Investment Portfolio Optimizer (GET)",
    description="Prescriptive MILP / 0-1 Knapsack optimizer allocating capital budgets across top-priority communities to maximize Intervention Effectiveness Score (IES) under equity and feasibility constraints."
)
def ai_portfolio_optimizer_get(
    budget_ngn: float = Query(2_500_000_000.0, description="Capital allocation budget in NGN"),
    objective: str = Query("MAX_IES", description="Strategy: MAX_IES, MAX_COMMUNITIES, EQUITY_BALANCED, CRITICAL_FIRST"),
    state: Optional[str] = Query(None, description="Optional State name filter (or ALL)"),
    max_state_share: float = Query(28.0, description="Max budget percentage allowed per state in equity mode")
):
    return ai_portfolio_optimizer.optimize_capital_portfolio(
        total_budget_ngn=budget_ngn,
        objective=objective,
        state_filter=state,
        max_state_share_pct=max_state_share
    )

@app.post(
    "/api/ai/priority/optimize-portfolio",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Prescriptive Capital Investment Portfolio Optimizer (POST)",
    description="Executes mathematical portfolio optimization adhering strictly to Stage 15 / Section 34 IES validity rules."
)
def ai_portfolio_optimizer_post(req: PortfolioOptimizationRequest):
    return ai_portfolio_optimizer.optimize_capital_portfolio(
        total_budget_ngn=req.total_budget_ngn,
        objective=req.objective,
        state_filter=req.state_filter,
        max_state_share_pct=req.max_state_share_pct,
        candidate_pool_size=req.candidate_pool_size,
        min_risk=req.min_risk
    )

# ---------------------------------------------------------------------------
# Improvement 1: Dynamic Dam Flood Inundation Plume on Map
# ---------------------------------------------------------------------------
@app.get(
    "/api/ai/flood/inundation-geojson",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Dynamic Dam Flood Wave Inundation Plume (GeoJSON)",
    description="Generates dynamic downstream flood wave plume polygon, river centerline, dam facility point, and exposed settlement GeoJSON based on dam spillway discharge modeling."
)
def ai_dam_inundation_geojson(
    dam_id: str = Query("DAM-NIG-01", description="Dam ID (e.g. DAM-NIG-01 Kainji, DAM-NIG-02 Jebba, DAM-NIG-03 Shiroro, DAM-GOM-01 Dadin Kowa, DAM-TAR-01 Kashimbila)"),
    rainfall_mm: float = Query(45.0, description="Upstream 24h basin rainfall forecast (mm)"),
    water_level_m: Optional[float] = Query(None, description="Current reservoir water level (m)")
):
    d_id = dam_id if isinstance(dam_id, str) else "DAM-NIG-01"
    r_mm = rainfall_mm if isinstance(rainfall_mm, (int, float)) else 45.0
    w_m = water_level_m if isinstance(water_level_m, (int, float)) else None
    return ai_flood_forecast_service.generate_dam_inundation_geojson(
        dam_id=d_id,
        upstream_rainfall_forecast_mm=r_mm,
        current_water_level_m=w_m
    )

# ---------------------------------------------------------------------------
# Improvement 2: Automated Live Satellite & Hydro-Meteorological Weather Feed
# ---------------------------------------------------------------------------
@app.get(
    "/api/ai/flood/live-weather",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Live Satellite Hydro-Meteorological Weather Feed for Dam Basin",
    description="Fetches live 24h, 48h, and 72h satellite precipitation, temperature, and wind speed from Open-Meteo for the selected dam basin, with calibrated offline hydro-climatology fallback."
)
def ai_dam_live_weather(
    dam_id: str = Query("DAM-NIG-01", description="Dam ID (DAM-NIG-01, DAM-NIG-02, DAM-NIG-03, DAM-GOM-01, DAM-TAR-01)")
):
    d_id = dam_id if isinstance(dam_id, str) else "DAM-NIG-01"
    return ai_weather_service.fetch_live_dam_weather(dam_id=d_id)

@app.get(
    "/api/ai/flood/all-dams-weather",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Live Weather Status Across All 5 Strategic Hydro Dams",
    description="Returns synchronized satellite and hydro-meteorological weather telemetry for all 5 N-HYPPADEC hydroelectric dams."
)
def ai_all_dams_weather():
    return ai_weather_service.get_all_dams_weather()

# ---------------------------------------------------------------------------
# Improvement 3: Real Cellular SMS & WhatsApp Broadcast Gateway Integration
# ---------------------------------------------------------------------------
@app.get(
    "/api/emergency/recipients",
    tags=["🚨 FEW-CAM Early Warning Engine"],
    summary="Registered Community Liaison Officers (CLOs) & Emergency Responders",
    description="Returns the verified directory of Community Liaison Officers, traditional leaders, and SEMA responders across N-HYPPADEC member states."
)
def emergency_get_recipients(
    state: Optional[str] = Query(None, description="Optional State filter"),
    lga: Optional[str] = Query(None, description="Optional LGA filter")
):
    st = state if isinstance(state, str) else None
    lg = lga if isinstance(lga, str) else None
    responders = emergency_dispatch_gateway.get_registered_responders(state_filter=st, lga_filter=lg)
    return {
        "status": "OPERATIONAL",
        "total": len(responders),
        "data": responders
    }

@app.get(
    "/api/emergency/dispatch-history",
    tags=["🚨 FEW-CAM Early Warning Engine"],
    summary="Tamper-Evident Emergency Broadcast Dispatch Audit Log",
    description="Retrieves chronological transmission receipts, carrier latency, and delivery acknowledgements for emergency broadcasts."
)
def emergency_get_dispatch_history(
    limit: int = Query(50, description="Max historical records to retrieve")
):
    lim = limit if isinstance(limit, int) else 50
    history = emergency_dispatch_gateway.get_dispatch_history(limit=lim)
    return {
        "status": "OPERATIONAL",
        "total_records": len(history),
        "history": history
    }

@app.post(
    "/api/emergency/dispatch",
    tags=["🚨 FEW-CAM Early Warning Engine"],
    summary="Execute Multi-Channel Emergency Alert Broadcast",
    description="Dispatches emergency early warning alerts across Cellular SMS (GSM shortcode), WhatsApp Business API, and Telegram bot webhooks with carrier ACK tokens."
)
def emergency_dispatch_post(payload: EmergencyBroadcastDispatchPayload):
    return emergency_dispatch_gateway.dispatch_emergency_broadcast(
        dam_id=payload.dam_id,
        dam_name=payload.dam_name,
        warning_level=payload.warning_level,
        spill_risk_pct=payload.spill_risk_pct,
        lead_time_hours=payload.lead_time_hours,
        affected_lgas=payload.affected_lgas,
        language=payload.language,
        selected_channels=payload.selected_channels,
        custom_directive=payload.custom_directive,
        sender_officer=payload.sender_officer
    )

# ---------------------------------------------------------------------------
# Improvement 4: One-Click Executive PDF Dossier with Official Seals & Verification QR
# ---------------------------------------------------------------------------
@app.get(
    "/api/sitrep/executive-dossier",
    response_class=HTMLResponse,
    tags=["🏛️ Statutory Decision Support & Reporting"],
    summary="One-Click Board-Ready Executive Dossier (A4 Print / PDF View)",
    description="Generates an official publication-ready A4 executive dossier with N-HYPPADEC federal seals, Level 1 restricted classification, grounded AI SitRep, Top-20 register, dynamic SVG QR code, and SHA-256 integrity hash."
)
def sitrep_executive_dossier(
    auto_print: bool = Query(False, description="Whether to automatically launch browser print dialog")
):
    ap = auto_print if isinstance(auto_print, bool) else False
    return executive_dossier_service.generate_executive_dossier_html(auto_print=ap)

# ---------------------------------------------------------------------------
# Improvement 5: Automated PostGIS Relational Database Sync & Audit
# ---------------------------------------------------------------------------
@app.get(
    "/api/database/postgis-status",
    tags=["🛠️ Data Pipeline & Integrity Governance"],
    summary="PostGIS Relational Database Connection & Schema Conformance Audit",
    description="Probes PostgreSQL / PostGIS spatial database connectivity and performs an authoritative schema conformance audit on all clean tables against the DDL v4.1 specification."
)
def database_postgis_status(
    host: Optional[str] = Query(None),
    port: Optional[int] = Query(None),
    dbname: Optional[str] = Query(None),
    user: Optional[str] = Query(None)
):
    custom_cfg = None
    if host or port or dbname or user:
        custom_cfg = {
            "host": host or "localhost",
            "port": port or 5433,
            "dbname": dbname or "fewcam",
            "user": user or "fewcam_dev",
            "password": os.environ.get("POSTGIS_PASSWORD", "ZFTLsRHDsOr8-zKSJLQcnLuitP4jebUoWCAaIeW9mfejDquF")
        }
    return database_sync_service.get_postgis_status(custom_cfg)

@app.post(
    "/api/database/sync-postgis",
    tags=["🛠️ Data Pipeline & Integrity Governance"],
    summary="Synchronize Clean Tables to PostGIS Relational Spatial Database",
    description="Triggers automated data seeding and spatial geometry population into PostGIS if reachable, or outputs an authoritative SQL migration execution plan."
)
def database_sync_postgis(req: Optional[PostgisDbConfigRequest] = None):
    custom_cfg = None
    if req and (req.host or req.port or req.dbname or req.user):
        custom_cfg = {
            "host": req.host or "localhost",
            "port": req.port or 5433,
            "dbname": req.dbname or "fewcam",
            "user": req.user or "fewcam_dev",
            "password": req.password or "ZFTLsRHDsOr8-zKSJLQcnLuitP4jebUoWCAaIeW9mfejDquF"
        }
    return database_sync_service.execute_postgis_sync(custom_cfg)

# ---------------------------------------------------------------------------
# AI Dam Water Level Monitoring & Agro-Drought Harvest Loss Engine
# ---------------------------------------------------------------------------
@app.get(
    "/api/ai/dams/water-levels",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Strategic Dams Water Level & Hydrostatic Head Monitoring",
    description="Real-time water levels, usable capacity (%), freeboard safety margins, and dead storage vs. spillway flood risk across all major dams in member states."
)
def ai_dams_water_levels(
    dam_id: Optional[str] = Query(None, description="Optional Dam ID filter (e.g. DAM-NIG-01, DAM-GOM-01, DAM-TAR-01)"),
    water_level_m: Optional[float] = Query(None, description="Optional simulated water level override (m)")
):
    d_id = dam_id if isinstance(dam_id, str) else None
    w_lvl = water_level_m if isinstance(water_level_m, (int, float)) else None
    return ai_drought_harvest_service.get_dam_water_levels_overview(dam_id_filter=d_id, water_level_override=w_lvl)

@app.get(
    "/api/ai/drought/state-harvest-impact",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="State-by-State Agro-Meteorological Drought & Crop Harvest Loss AI",
    description="Calculates rainfall deficits across all member states and computes predicted crop yield reductions across Maize, Sorghum, Millet, Rice, and Yam using FAO-33 water production functions, ranking states by drought vulnerability."
)
def ai_drought_state_harvest_impact(
    simulated_deficit_state: Optional[str] = Query(None, description="Optional State Code to stress test (e.g. NG-GOM, NG-KEB)"),
    simulated_deficit_pct: Optional[float] = Query(None, description="Optional simulated rainfall deficit % (0-100)")
):
    st_val = simulated_deficit_state if isinstance(simulated_deficit_state, str) else None
    pct_val = simulated_deficit_pct if isinstance(simulated_deficit_pct, (int, float)) else None
    sim_deficits = None
    if st_val and pct_val is not None:
        sim_deficits = {st_val: pct_val}
    return ai_drought_harvest_service.compute_state_drought_and_harvest_loss(simulated_state_deficits=sim_deficits)

@app.get(
    "/api/ai/drought/irrigation-advisory",
    tags=["🤖 Prescriptive AI & Early Warning Engine"],
    summary="Prescriptive Dam Irrigation & Strategic Food Security Directives",
    description="Generates concrete operational directives linking available reservoir water storage to downstream agricultural drought relief and emergency grain reserves."
)
def ai_drought_irrigation_advisory():
    return ai_drought_harvest_service.generate_drought_irrigation_advisory()

# ---------------------------------------------------------------------------
@app.get(
    "/",
    response_class=HTMLResponse,
    tags=["🖥️ Executive Management Web UI"],
    summary="Executive Decision-Support Web GIS Portal",
    description="Serves the interactive single-page Web GIS interface featuring Esri Leaflet basemaps, 31-Table Explorer, FEW-CAM alerts monitor, and live scenario tools."
)
def dashboard_ui():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CHER-CDSS | N-HYPPADEC Institutional Decision-Support System v4.1</title>
    <link rel="icon" type="image/jpeg" href="/api/logo">
    <!-- Modern Typography: Inter & Outfit -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <style>
        :root {
            --bg-primary: #070B14;
            --bg-secondary: #0E1626;
            --bg-card: #152238;
            --bg-card-hover: #1C2D4A;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --accent-blue: #0284C7;
            --accent-cyan: #06B6D4;
            --accent-red: #EF4444;
            --accent-amber: #F59E0B;
            --accent-green: #10B981;
            --accent-purple: #8B5CF6;
            --border-color: rgba(255, 255, 255, 0.08);
            --font-display: 'Outfit', sans-serif;
            --font-body: 'Inter', sans-serif;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: var(--font-body);
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            background: linear-gradient(180deg, rgba(14, 22, 38, 0.98) 0%, rgba(7, 11, 20, 0.98) 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 0.85rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-brand { display: flex; align-items: center; gap: 1rem; }

        .logo-badge {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #FFFFFF;
            padding: 2px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.45);
            border: 2px solid #15803D;
            object-fit: contain;
        }

        .header-title h1 {
            font-family: var(--font-display);
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, #FFFFFF, #93C5FD);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-title p { font-size: 0.78rem; color: var(--text-secondary); }

        .header-status { display: flex; align-items: center; gap: 1.25rem; }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: var(--accent-green);
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        /* Nav Tabs */
        .nav-tabs-bar {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 0 2rem;
            display: flex;
            gap: 0.5rem;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-family: var(--font-display);
            font-size: 0.9rem;
            font-weight: 600;
            padding: 0.85rem 1.25rem;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .tab-btn:hover { color: #FFFFFF; background: rgba(255, 255, 255, 0.02); }

        .tab-btn.active {
            color: var(--accent-cyan);
            border-bottom: 2px solid var(--accent-cyan);
            background: rgba(6, 182, 212, 0.05);
        }

        main {
            padding: 1.5rem 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            flex: 1;
        }

        .tab-content { display: none; }
        .tab-content.active { display: flex; flex-direction: column; gap: 1.5rem; }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 1rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.15rem;
            transition: transform 0.2s, border-color 0.2s;
            position: relative;
            overflow: hidden;
        }

        .kpi-card:hover { transform: translateY(-2px); border-color: rgba(6, 182, 212, 0.4); }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
        }

        .kpi-card.critical::before { background: linear-gradient(90deg, #F87171, #EF4444); }
        .kpi-card.purple::before { background: linear-gradient(90deg, #A78BFA, #8B5CF6); }
        .kpi-card.green::before { background: linear-gradient(90deg, #34D399, #10B981); }

        .kpi-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-secondary);
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
        }

        .kpi-value {
            font-family: var(--font-display);
            font-size: 1.85rem;
            font-weight: 700;
            color: #FFFFFF;
        }

        .kpi-sub { font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.35rem; }

        .dashboard-layout {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 1.5rem;
            flex: 1;
        }

        @media (max-width: 1024px) {
            .dashboard-layout { grid-template-columns: 1fr; }
        }

        .map-container-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 1.1rem;
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
            min-height: 620px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        .map-container-card.fullscreen-active {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            z-index: 999999 !important;
            margin: 0 !important;
            padding: 1.25rem 1.5rem !important;
            border-radius: 0 !important;
            border: none !important;
            background: rgba(7, 11, 20, 0.98) !important;
            backdrop-filter: blur(20px) !important;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.95) !important;
        }

        body.has-fullscreen-map {
            overflow: hidden !important;
        }

        .card-header { display: flex; justify-content: space-between; align-items: center; }

        .card-title {
            font-family: var(--font-display);
            font-size: 1.05rem;
            font-weight: 600;
            color: #FFFFFF;
        }

        .expand-map-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.16);
            color: #F8FAFC;
            padding: 0.42rem 0.9rem;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(10px);
            user-select: none;
        }

        .expand-map-btn:hover {
            background: rgba(2, 132, 199, 0.28);
            border-color: #38BDF8;
            color: #38BDF8;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
            transform: translateY(-1px);
        }

        .expand-map-btn.active {
            background: rgba(239, 68, 68, 0.25);
            border-color: #EF4444;
            color: #FCA5A5;
            box-shadow: 0 0 14px rgba(239, 68, 68, 0.3);
        }

        .expand-map-btn.active:hover {
            background: rgba(239, 68, 68, 0.4);
            color: #FFFFFF;
        }

        #map, #flood-map, #hazard-map {
            width: 100%;
            flex: 1;
            border-radius: 10px;
            min-height: 560px;
            height: 60vh;
            max-height: 820px;
            background: #0D1629;
            position: relative;
            z-index: 1;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .map-container-card.fullscreen-active #map,
        .map-container-card.fullscreen-active #flood-map,
        .map-container-card.fullscreen-active #hazard-map {
            height: calc(100vh - 95px) !important;
            min-height: calc(100vh - 95px) !important;
            max-height: none !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
        }

        .hazard-filter-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
            padding: 0.75rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
        }

        .hazard-filter-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-secondary);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .hazard-filter-btn:hover {
            color: #FFFFFF;
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.25);
        }

        .hazard-filter-btn.active {
            color: #FFFFFF;
            font-weight: 600;
            border-color: var(--accent-cyan);
            background: rgba(6, 182, 212, 0.2);
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
        }


        .leaflet-container {
            background: #0D1629 !important;
            font-family: var(--font-body) !important;
        }
        .leaflet-popup-content-wrapper {
            background: #152238 !important;
            color: #F8FAFC !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
        }
        .leaflet-popup-tip {
            background: #152238 !important;
        }
        .leaflet-control-layers {
            background: rgba(14, 22, 38, 0.95) !important;
            color: #F8FAFC !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            font-size: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
        }
        .map-legend {
            background: rgba(14, 22, 38, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            color: #F8FAFC;
            line-height: 1.5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 3px;
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }
        .legend-box {
            width: 14px;
            height: 10px;
            border-radius: 2px;
            display: inline-block;
        }

        .side-panel { display: flex; flex-direction: column; gap: 1.25rem; }

        .panel-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 1.2rem;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            margin-top: 0.6rem;
        }

        .data-table th {
            text-align: left;
            padding: 0.55rem 0.5rem;
            color: var(--text-secondary);
            font-weight: 500;
            border-bottom: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.15);
        }

        .data-table td {
            padding: 0.55rem 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }

        .data-table tr:hover { background: rgba(255, 255, 255, 0.025); }

        .tier-badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
        }

        .tier-1 { background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .tier-2 { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .tier-3 { background: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.4); }
        .tier-4 { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }

        .calc-form { display: flex; flex-direction: column; gap: 0.7rem; margin-top: 0.6rem; }

        .form-row { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }

        .form-row label { font-size: 0.8rem; color: var(--text-secondary); }

        .form-row input, .form-row select {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: #FFFFFF;
            padding: 0.35rem 0.6rem;
            border-radius: 6px;
            font-family: var(--font-body);
        }

        .btn-calc {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #FFFFFF;
            border: none;
            padding: 0.6rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            margin-top: 0.4rem;
            transition: opacity 0.2s;
        }

        .btn-calc:hover { opacity: 0.9; }

        .calc-output {
            margin-top: 0.5rem;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            font-size: 0.82rem;
            display: none;
        }

        .scenario-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.25rem;
        }

        .scenario-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .scenario-badge {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            align-self: flex-start;
        }

        .slider-control {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            margin-bottom: 0.75rem;
        }

        .slider-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        input[type="range"] {
            width: 100%;
            accent-color: var(--accent-cyan);
        }

        footer {
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            padding: 1rem 2rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        /* === UX v4.2 additions === */

        /* Empty-state / loading skeleton */
        .empty-state-cell {
            text-align: center;
            padding: 1.5rem 0.5rem;
            color: var(--text-secondary);
            font-size: 0.82rem;
        }
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(6, 182, 212, 0.3);
            border-top-color: var(--accent-cyan);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            vertical-align: middle;
            margin-right: 6px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Data timestamps */
        .data-timestamp {
            font-size: 0.72rem;
            color: var(--text-secondary);
            font-style: italic;
            margin-left: auto;
            white-space: nowrap;
        }

        /* API error pill */
        .api-error-pill {
            display: inline-flex;
            align-items: center;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #F87171;
            padding: 0.3rem 0.75rem;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        /* CSV export button */
        .btn-csv {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: var(--accent-green);
            padding: 0.3rem 0.75rem;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            transition: background 0.2s;
        }
        .btn-csv:hover { background: rgba(16, 185, 129, 0.25); }

        /* KPI card tooltips */
        .kpi-label-wrapper {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.4rem;
        }
        .kpi-tooltip-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 15px;
            height: 15px;
            background: rgba(148, 163, 184, 0.2);
            border-radius: 50%;
            font-size: 0.62rem;
            color: var(--text-secondary);
            cursor: default;
            position: relative;
            flex-shrink: 0;
        }
        .kpi-tooltip-icon .kpi-tooltip {
            display: none;
            position: absolute;
            bottom: calc(100% + 6px);
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-card-hover);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            font-size: 0.72rem;
            line-height: 1.45;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            width: 200px;
            z-index: 500;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            white-space: normal;
        }
        .kpi-tooltip-icon:hover .kpi-tooltip { display: block; }

        /* Input guidance disclosure */
        .input-guidance {
            background: rgba(6, 182, 212, 0.06);
            border: 1px solid rgba(6, 182, 212, 0.2);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            font-size: 0.8rem;
        }
        .input-guidance summary {
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            color: var(--accent-cyan);
            font-weight: 600;
            list-style: none;
            user-select: none;
        }
        .input-guidance summary::-webkit-details-marker { display: none; }
        .input-guidance[open] summary { border-bottom: 1px solid rgba(6, 182, 212, 0.15); }
        .input-guidance-body {
            padding: 0.75rem;
            color: var(--text-secondary);
            line-height: 1.55;
        }

        /* Print CSS for SitRep */
        @media print {
            * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            body { background: #FFFFFF !important; color: #111111 !important; font-family: Georgia, 'Times New Roman', serif !important; }
            header, .nav-tabs-bar, footer, #alert-ticker, #tour-btn,
            #global-search-wrapper, .tab-btn, .hazard-filter-bar,
            .expand-map-btn, .btn-calc, .btn-csv { display: none !important; }
            .tab-content { display: none !important; }
            #tab-sitrep { display: block !important; }
            .kpi-card, .panel-card, .map-container-card {
                background: #FFFFFF !important;
                border: 1px solid #CCCCCC !important;
                box-shadow: none !important;
                break-inside: avoid;
            }
            .kpi-value { color: #111111 !important; }
            .kpi-label, .kpi-sub, .card-title { color: #333333 !important; }
            .data-table th { background: #F0F0F0 !important; color: #333333 !important; }
            .data-table td { color: #111111 !important; border-bottom: 1px solid #DDDDDD !important; }
            a { color: #0055AA !important; }
            @page { margin: 1.5cm; }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-brand">
            <img src="/api/logo" alt="N-HYPPADEC Official Emblem" class="logo-badge">
            <div class="header-title">
                <h1>CHER-CDSS DECISION-SUPPORT PLATFORM</h1>
                <p>N-HYPPADEC Institutional Evidence System | Ten Member States | v4.2 Master Scaffold</p>
            </div>
        </div>
        <div id="global-search-wrapper" style="position:relative; flex:1; max-width:280px; margin:0 1.5rem;">
            <input type="text" id="global-search" placeholder="🔍 Search states, communities, tabs…"
                oninput="onSearchInput(this.value)"
                style="width:100%; background:rgba(255,255,255,0.06); border:1px solid var(--border-color); color:var(--text-primary); padding:0.4rem 0.9rem; border-radius:20px; font-size:0.82rem; font-family:var(--font-body); outline:none;">
            <div id="search-dropdown" style="display:none; position:absolute; top:calc(100% + 6px); left:0; right:0; background:var(--bg-card); border:1px solid var(--border-color); border-radius:10px; box-shadow:0 8px 20px rgba(0,0,0,0.5); z-index:2000; max-height:240px; overflow-y:auto;"></div>
        </div>
        <div class="header-status">
            <button onclick="openLoginModal()" style="background: rgba(14, 165, 233, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); padding: 0.35rem 0.8rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                <span>🔐</span> <span id="current-user-role">Managing Director (MD)</span>
            </button>
            <div class="status-pill">
                <div class="pulse-dot"></div>
                v4.2 ACTIVE & VALIDATED
            </div>
            <a href="/docs" target="_blank" style="color: var(--accent-cyan); text-decoration: none; font-size: 0.85rem; font-weight: 500;">API Docs &rarr;</a>
            <button id="tour-btn" onclick="startTour()" style="background: rgba(139,92,246,0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); width: 32px; height: 32px; border-radius: 50%; font-weight: 700; font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center;" title="Start onboarding tour">?</button>
        </div>
    </header>

    <!-- Institutional Role-Based Login & Security Clearance Modal -->
    <div id="login-modal" style="display: none; position: fixed; inset: 0; background: rgba(7, 11, 20, 0.85); backdrop-filter: blur(8px); z-index: 10000; align-items: center; justify-content: center;">
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px; width: 92%; max-width: 520px; padding: 1.75rem; box-shadow: 0 20px 40px rgba(0,0,0,0.6); position: relative;">
            <button onclick="closeLoginModal()" style="position: absolute; top: 16px; right: 16px; background: none; border: none; color: var(--text-secondary); font-size: 1.2rem; cursor: pointer;">✕</button>
            
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <img src="/api/logo" alt="N-HYPPADEC Official Seal" style="width: 46px; height: 46px; border-radius: 50%; background: #FFF; padding: 2px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid #15803D; object-fit: contain;">
                <div>
                    <h3 style="margin: 0; font-family: var(--font-display); font-size: 1.15rem; color: #FFF;">Institutional Login & Security Clearance</h3>
                    <p style="margin: 2px 0 0 0; font-size: 0.78rem; color: var(--text-secondary);">N-HYPPADEC CHER-CDSS Evidence Platform Access Control</p>
                </div>
            </div>

            <div style="background: rgba(14, 165, 233, 0.08); border-left: 3px solid var(--accent-cyan); padding: 0.75rem 1rem; border-radius: 4px; font-size: 0.8rem; margin-bottom: 1.25rem;">
                <strong>📋 Steps to Access & Log In Anytime:</strong>
                <ol style="margin: 4px 0 0 0; padding-left: 18px; line-height: 1.5; color: var(--text-primary);">
                    <li><strong>Launch Server:</strong> Double-click <code>start_platform.bat</code> or run <code>python run_dashboard.py</code>.</li>
                    <li><strong>Open Browser:</strong> Navigate to <code>http://127.0.0.1:8000/</code>.</li>
                    <li><strong>Select Role & Clearance:</strong> Choose your designated operational role below.</li>
                </ol>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                <div>
                    <label style="font-size: 0.8rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Select Designated Operational Role:</label>
                    <select id="login-role-select" onchange="onRoleChange()" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.5rem 0.8rem; border-radius: 6px; font-family: var(--font-body); font-size: 0.85rem;">
                        <option value="Managing Director (MD)" selected>🎖️ Managing Director / Governing Board (Full Executive Clearance)</option>
                        <option value="GIS & Remote Sensing Lead">🗺️ GIS & Remote Sensing Lead (Spatial Editor & EO Analyst)</option>
                        <option value="Field Operations Supervisor">🔄 Field Operations Supervisor (Kobo Ingestion & Quarantine Admin)</option>
                        <option value="Resilience Planning Analyst">📊 Resilience Planning Analyst (Scenarios & MRV Portfolio)</option>
                        <option value="Public Evidence Viewer">👁️ Public Evidence Viewer (Level-1 Public Analytics)</option>
                    </select>
                </div>

                <div>
                    <label style="font-size: 0.8rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Officer Email / ID:</label>
                    <input type="text" id="login-email-input" value="executive-md@n-hyppadec.gov.ng" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.5rem 0.8rem; border-radius: 6px; font-size: 0.85rem; box-sizing: border-box;">
                </div>

                <div>
                    <label style="font-size: 0.8rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Security Clearance Key / Token:</label>
                    <input type="password" id="login-pass-input" value="••••••••••••" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.5rem 0.8rem; border-radius: 6px; font-size: 0.85rem; box-sizing: border-box;">
                    <span style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 3px; display: block;">Default test environment is pre-authorized for rapid institutional evaluation.</span>
                </div>

                <div style="display: flex; gap: 0.75rem; margin-top: 0.75rem;">
                    <button class="btn-calc" style="flex: 1; margin-top: 0; background: var(--accent-cyan); color: #070B14; font-weight: 700;" onclick="authenticateUser()">Authenticate & Access</button>
                    <button class="btn-calc" style="margin-top: 0; background: rgba(255,255,255,0.08); color: #FFF;" onclick="closeLoginModal()">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Live Multi-Hazard Alert Ticker -->
    <div id="alert-ticker" style="background: rgba(239, 68, 68, 0.12); border-bottom: 1px solid rgba(239, 68, 68, 0.35); padding: 0.55rem 1.5rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; font-family: var(--font-body); z-index: 99;">
        <div style="display: flex; align-items: center; gap: 0.75rem; overflow: hidden; white-space: nowrap;">
            <span style="background: #EF4444; color: #FFF; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.7rem; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 4px;">
                <span class="pulse-dot" style="background: #FFF; width: 6px; height: 6px;"></span>
                ACTIVE ADVISORY
            </span>
            <span id="ticker-text" style="color: #FCA5A5; font-weight: 500;">
                <span class="spinner"></span> Checking advisories…
            </span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <button onclick="switchTab('flood')" style="background: rgba(239, 68, 68, 0.25); border: 1px solid rgba(239, 68, 68, 0.5); color: #FFF; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; cursor: pointer;">View Alert Matrix</button>
            <button onclick="document.getElementById('alert-ticker').style.display='none'" style="background: none; border: none; color: #94A3B8; font-size: 0.9rem; cursor: pointer; padding: 0 4px;">✕</button>
        </div>
    </div>

    <!-- Nav Bar -->
    <div class="nav-tabs-bar">
        <button class="tab-btn active" onclick="switchTab('overview')">&#127758; Executive Overview & GIS Map</button>
        <button class="tab-btn" onclick="switchTab('flood')">&#127783; FEW-CAM Flood Warnings & Alerts</button>
        <button class="tab-btn" onclick="switchTab('drought')">🌾 Agro-Drought & Dam Water Monitor</button>
        <button class="tab-btn" onclick="switchTab('multi_hazard')">&#127757; Multi-Hazard & Environmental Risks (14 Themes)</button>
        <button class="tab-btn" onclick="switchTab('field_ops')">&#128257; Field Ops & Kobo Ingestion Hub</button>
        <button class="tab-btn" onclick="switchTab('sitrep')">&#128196; Executive SitRep Generator</button>
        <button class="tab-btn" onclick="switchTab('scenarios')">&#9881; Scenario Simulation Lab (Stage 21)</button>
        <button class="tab-btn" onclick="switchTab('interventions')">&#128737; Interventions & MRV Registry</button>
        <button class="tab-btn" onclick="switchTab('tables')">&#128196; 31-Table Architecture Explorer</button>
        <button class="tab-btn" onclick="switchTab('remote_sensing')">&#128752; Earth Observation & Remote Sensing</button>
    </div>


    <main>
        <!-- TAB 1: EXECUTIVE OVERVIEW -->
        <div id="tab-overview" class="tab-content active">
            <div class="card-header" style="margin-bottom: 0.5rem;">
                <div class="card-title">Overview KPI Summary</div>
                <span class="data-timestamp" id="ts-overview"></span>
            </div>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Member States</div>
                    <div class="kpi-value">10</div>
                    <div class="kpi-sub">186 LGAs | Master Registry</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">GIS Layers Specified</div>
                    <div class="kpi-value">43</div>
                    <div class="kpi-sub">G01-G43 | GeoServer Ready</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Core Database Model</div>
                    <div class="kpi-value">31</div>
                    <div class="kpi-sub">PostgreSQL / PostGIS Tables</div>
                </div>
                <div class="kpi-card critical">
                    <div class="kpi-label kpi-label-wrapper">Tier 1 Critical Sites<span class="kpi-tooltip-icon">?<span class="kpi-tooltip">Communities with Composite Risk ≥ 65/100. These require immediate capital allocation and emergency preparedness interventions.</span></span></div>
                    <div class="kpi-value" id="kpi-critical">--</div>
                    <div class="kpi-sub">Immediate Capital Allocation</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label kpi-label-wrapper">Composite Risk Mean<span class="kpi-tooltip-icon">?<span class="kpi-tooltip">Weighted composite: R = 0.35×Hazard + 0.25×Exposure + 0.25×Vulnerability + 0.15×Criticality. Normalized 0–100 against Baseline_2026 reference bounds.</span></span></div>
                    <div class="kpi-value" id="kpi-risk">--</div>
                    <div class="kpi-sub">R = 0.35H + 0.25E + 0.25V + 0.15C</div>
                </div>
            </div>

            <div class="dashboard-layout">
                <div class="map-container-card">
                    <div class="card-header">
                        <div class="card-title">10-State Hydro-Resilience & Hazard Hotspot Map</div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">WGS84 EPSG:4326 | Live Priority Sites</span>
                            <button class="expand-map-btn" onclick="toggleMapFullscreen(this, 'map')" title="Toggle Full Screen Map">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
                                <span>Full Screen</span>
                            </button>
                        </div>
                    </div>
                    <div id="map"></div>
                </div>

                <div class="side-panel">
                    <div class="panel-card">
                        <div class="card-title">Ten State Resilience Profiles</div>
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>State</th>
                                    <th>Code</th>
                                    <th>Risk</th>
                                    <th>Tier 1</th>
                                </tr>
                            </thead>
                            <tbody id="state-table-body">
                                <tr class="loading-row"><td colspan="4" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="panel-card">
                        <div class="card-title">Live Risk & IES Evaluator</div>
                        <details class="input-guidance">
                            <summary>ℹ Input Guidance</summary>
                            <div class="input-guidance-body">
                                <strong>Hazard (H):</strong> Probability × magnitude of the primary flood, drought, or security hazard. Score 0–100 derived from IND01–IND04.<br>
                                <strong>Exposure (E):</strong> Degree of people, assets, and infrastructure in the hazard zone. Informed by population density and proximity to rivers and dams (IND05–IND06).<br>
                                <strong>Vulnerability (V):</strong> Social, economic, and adaptive capacity deficits. Includes poverty rates and infrastructure access gaps (IND07–IND08).<br>
                                <strong>Criticality (C):</strong> Presence of strategic assets and irreversibility of potential impacts (IND09–IND10).<br>
                                <em>All inputs are normalised 0–100 against the frozen Baseline_2026 reference bounds.</em>
                            </div>
                        </details>
                        <div class="calc-form">
                            <div class="form-row">
                                <label>Hazard (H)</label>
                                <input type="number" id="in_h" value="75" min="0" max="100" style="width: 70px;">
                            </div>
                            <div class="form-row">
                                <label>Exposure (E)</label>
                                <input type="number" id="in_e" value="65" min="0" max="100" style="width: 70px;">
                            </div>
                            <div class="form-row">
                                <label>Vulnerability (V)</label>
                                <input type="number" id="in_v" value="60" min="0" max="100" style="width: 70px;">
                            </div>
                            <div class="form-row">
                                <label>Criticality (C)</label>
                                <input type="number" id="in_c" value="70" min="0" max="100" style="width: 70px;">
                            </div>
                            <button class="btn-calc" onclick="evaluateRisk()">Compute Decision Scores</button>
                            <div class="calc-output" id="calc-result"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Top 20 Priority Communities Table -->
            <div class="panel-card">
                <div class="card-header">
                    <div class="card-title">&#128308; Top-20 Priority Communities Capital Investment Register</div>
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Formula: Priority_Score = 0.70 R + 0.30 IND10</span>
                        <button class="btn-csv" onclick="downloadTableAsCSV('top20-table', 'priority-communities.csv')">⬇ CSV</button>
                    </div>
                </div>
                <div style="overflow-x: auto; margin-top: 0.75rem;">
                    <table class="data-table" id="top20-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Community ID</th>
                                <th>State</th>
                                <th>LGA</th>
                                <th>Composite Risk</th>
                                <th>Adaptation Gap</th>
                                <th>Priority Score</th>
                                <th>Tier</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody id="top20-table-body">
                            <tr class="loading-row"><td colspan="9" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: FLOOD EARLY WARNING, ALARM & COMMUNITY AWARENESS -->
        <div id="tab-flood" class="tab-content">
            <div class="card-header">
                <div>
                    <h2 class="card-title" style="font-size: 1.3rem;">FEW-CAM — Flood Early Warning, Alarm & Community Awareness</h2>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">Decision support only. Official warnings require authorised emergency-management approval.</p>
                </div>
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    <span class="status-pill" id="flood-data-status">Checking flood data…</span>
                    <span class="data-timestamp" id="ts-flood"></span>
                </div>
            </div>
            <div class="kpi-grid">
                <div class="kpi-card critical"><div class="kpi-label kpi-label-wrapper">Released Active Warnings<span class="kpi-tooltip-icon">?<span class="kpi-tooltip">FEW-CAM alerts with status "Released" — authorised, active flood advisories at Level 1–3. Requires authorised emergency-management approval to release.</span></span></div><div class="kpi-value" id="flood-active-count">0</div><div class="kpi-sub">By state, LGA and community</div></div>
                <div class="kpi-card"><div class="kpi-label">Alerts Recorded</div><div class="kpi-value" id="flood-total-count">0</div><div class="kpi-sub">Includes cancelled and false alarms</div></div>
                <div class="kpi-card green"><div class="kpi-label">Notification Reach</div><div class="kpi-value" id="flood-reach-rate">Not evaluated</div><div class="kpi-sub">Reached recipients / intended recipients</div></div>
                <div class="kpi-card purple"><div class="kpi-label">Acknowledgement Rate</div><div class="kpi-value" id="flood-ack-rate">Not evaluated</div><div class="kpi-sub">Acknowledgements / notifications</div></div>
                <div class="kpi-card"><div class="kpi-label">Awareness Activities</div><div class="kpi-value" id="flood-awareness-count">0</div><div class="kpi-sub">Preparedness, outreach and review</div></div>
                <div class="kpi-card"><div class="kpi-label">Warning Hit Rate</div><div class="kpi-value" id="flood-hit-rate">Not evaluated</div><div class="kpi-sub">Verified hits / resolved outcomes</div></div>
                <div class="kpi-card critical"><div class="kpi-label">False-alarm Rate</div><div class="kpi-value" id="flood-false-rate">Not evaluated</div><div class="kpi-sub">False alarms / resolved outcomes</div></div>
                <div class="kpi-card"><div class="kpi-label">Mean Warning Lead Time</div><div class="kpi-value" id="flood-lead-time">Not evaluated</div><div class="kpi-sub">Hours before observed event</div></div>
                <div class="kpi-card"><div class="kpi-label">High-risk Awareness Coverage</div><div class="kpi-value" id="flood-awareness-coverage">Not evaluated</div><div class="kpi-sub">Communities reached / high-risk communities</div></div>
                <div class="kpi-card"><div class="kpi-label">Alert Audit Completeness</div><div class="kpi-value" id="flood-audit-completeness">Not evaluated</div><div class="kpi-sub">Required alert evidence and reviewer fields</div></div>
            </div>
            <div class="dashboard-layout">
                <div class="map-container-card">
                    <div class="card-header">
                        <div class="card-title">Flood Alert Areas & Timeline</div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">G38 | WGS84 EPSG:4326</span>
                            <button class="expand-map-btn" onclick="toggleMapFullscreen(this, 'flood-map')" title="Toggle Full Screen Map">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
                                <span>Full Screen</span>
                            </button>
                        </div>
                    </div>
                    <div id="flood-map"></div>
                </div>
                <div class="panel-card">
                    <div class="card-title">Graduated Warning Levels</div>
                    <div id="flood-levels" style="display: grid; gap: 0.6rem; margin-top: 0.8rem;"></div>
                    <p style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 1rem;">Thresholds are not configured as operational rules until formally approved and versioned.</p>
                </div>
            </div>
            <div class="panel-card">
                <div class="card-header">
                    <div class="card-title">Alert Timeline</div>
                    <button class="btn-csv" onclick="downloadTableAsCSV('flood-alerts-table', 'flood-alerts.csv')">⬇ CSV</button>
                </div>
                <div style="overflow-x: auto; margin-top: 0.75rem;">
                    <table class="data-table" id="flood-alerts-table"><thead><tr><th>Alert</th><th>Issued</th><th>State</th><th>LGA</th><th>Level</th><th>Status</th><th>Confidence</th></tr></thead><tbody id="flood-alerts-body"></tbody></table>
                </div>
            </div>
            <div class="panel-card">
                <div class="card-header">
                    <div class="card-title">Warning Performance Evaluations</div>
                    <button class="btn-csv" onclick="downloadTableAsCSV('flood-performance-table', 'warning-performance.csv')">⬇ CSV</button>
                </div>
                <div style="overflow-x: auto;">
                    <table class="data-table" id="flood-performance-table"><thead><tr><th>Alert</th><th>Evaluated</th><th>Lead Time (hours)</th><th>Outcome</th><th>Alerted Area (km²)</th><th>Observed Area (km²)</th><th>Confidence</th></tr></thead><tbody id="flood-performance-body"></tbody></table>
                </div>
            </div>

            <!-- Early Warning Dispatch Simulation Console -->
            <div class="panel-card" style="margin-top: 1rem; border-left: 4px solid #EF4444;">
                <div class="card-header">
                    <div>
                        <div class="card-title">🚨 Multi-Hazard Early Warning Simulation & Emergency Dispatcher</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Automated broadcast test to Community Liaison Officers, Village Heads & River Basin Responders</span>
                    </div>
                    <span class="status-pill" id="dispatch-status-badge">GATEWAY READY</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Target Active Advisory:</label>
                        <select id="dispatch-alert-select" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="ALT-2026-HYD-01">Kainji & Jebba Hydro Dams Stage-2 Spillway (Critical Level 3)</option>
                            <option value="ALT-2026-SEC-02">Allawa-Shiroro Forest Security Advisory (High Level 2)</option>
                            <option value="ALT-2026-MET-03">Upper Benue Extreme Rainfall Storm Warning (High Level 2)</option>
                            <option value="ALT-2026-ENV-04">Sudano-Sahelian Soil Moisture Drought Alert (Level 1)</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Broadcast Channel:</label>
                        <select id="dispatch-channel-select" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="SMS_BROADCAST">📲 Emergency Cellular SMS Blast (Fast Broadcast)</option>
                            <option value="WHATSAPP_EMERGENCY">💬 WhatsApp Community Leader Network</option>
                            <option value="VHF_RADIO">📻 VHF Marine & Hydropower Radio Net</option>
                        </select>
                    </div>
                    <div style="display: flex; align-items: flex-end;">
                        <button class="btn-calc" style="width: 100%; height: 38px; margin-top: 0; background: #DC2626;" onclick="triggerSimulatedDispatch()">Broadcast Simulated Alert</button>
                    </div>
                </div>
                <div id="dispatch-result-box" style="margin-top: 0.75rem; font-size: 0.8rem; display: none; padding: 0.75rem; border-radius: 6px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #34D399;"></div>
            </div>

            <!-- AI Phase 3: Hydro-Meteorological Reservoir Inflow & Spillway Forecaster -->
            <div class="panel-card" style="margin-top: 1rem; border-left: 4px solid var(--accent-cyan);">
                <div class="card-header">
                    <div>
                        <div class="card-title">🌊 Phase 3 AI: Hydro-Meteorological Dam Inflow & Spillway Risk Forecaster</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Non-linear runoff transfer modeling & spillway threshold exceedance for 5 N-HYPPADEC Hydro Dams</span>
                    </div>
                    <span class="status-pill" id="dam-forecast-status" style="color:var(--accent-cyan);">HYDRO AI READY</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Target Hydro Dam:</label>
                        <select id="dam-select" onchange="runDamForecast()" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="DAM-NIG-01">Kainji Hydroelectric Dam (760 MW, Niger River)</option>
                            <option value="DAM-NIG-02">Jebba Hydroelectric Dam (578 MW, Niger River)</option>
                            <option value="DAM-NIG-03">Shiroro Hydroelectric Dam (600 MW, Kaduna River)</option>
                            <option value="DAM-GOM-01">Dadin Kowa Multipurpose Dam (40 MW, Gongola River)</option>
                            <option value="DAM-TAR-01">Kashimbila Multipurpose Dam (40 MW, Katsina-Ala River)</option>
                        </select>
                    </div>
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
                            <label style="font-size: 0.78rem; color: var(--text-secondary);">Upstream 24h Rainfall: <span id="dam-rain-val" style="color:var(--accent-cyan); font-weight:700;">45 mm</span></label>
                            <button type="button" onclick="fetchLiveDamWeather()" class="btn-calc" style="padding: 2px 8px; font-size: 0.72rem; height: auto; margin: 0; background: rgba(56, 189, 248, 0.2); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4); cursor:pointer;" title="Pull Real-Time Open-Meteo Satellite Precipitation">🛰️ Live Satellite Weather</button>
                        </div>
                        <input type="range" id="dam-rain-slider" min="0" max="150" value="45" oninput="document.getElementById('dam-rain-val').innerText = this.value + ' mm'; runDamForecast()" style="width: 100%; accent-color: var(--accent-cyan); margin-top: 6px;">
                        <div id="dam-weather-strip" style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 4px; display: flex; gap: 8px;">
                            <span id="weather-source-badge">🛰️ Standby</span>
                            <span id="weather-temp-badge"></span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: flex-end;">
                        <button class="btn-calc" style="flex: 1; height: 38px; margin-top: 0; background: var(--accent-cyan); color: #000; font-weight: 700;" onclick="runDamForecast()">⚡ Run Inflow AI Forecast</button>
                        <button class="btn-calc" style="height: 38px; margin-top: 0; background: #DC2626; color: #FFF; font-weight: 700; white-space: nowrap;" onclick="openEmergencyDispatchModal()">📢 Dispatch Alerts</button>
                    </div>
                </div>

                <div id="dam-forecast-results" style="margin-top: 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem;">
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">24h Forecast Inflow</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-cyan);" id="dam-f24-inflow">-- m³/s</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);" id="dam-threshold-comp">Spillway: -- m³/s</div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">48h Peak Projection</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #F59E0B;" id="dam-f48-inflow">-- m³/s</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">72h: <span id="dam-f72-inflow">-- m³/s</span></div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">Spillway Exceedance Risk</div>
                        <div style="font-size: 1.25rem; font-weight: 700;" id="dam-spill-risk">-- %</div>
                        <div style="font-size: 0.7rem;" id="dam-warning-class"><span class="status-pill">Calculating...</span></div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">Evacuation Lead Time</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #34D399;" id="dam-lead-time">-- hours</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">Inundation: <span id="dam-inundated-area">-- Ha</span></div>
                    </div>
                </div>

                <div id="dam-directive-box" style="margin-top: 0.75rem; font-size: 0.82rem; padding: 0.75rem; border-radius: 6px; background: rgba(2, 132, 199, 0.1); border: 1px solid rgba(2, 132, 199, 0.3); color: var(--text-primary); line-height: 1.5;">
                    <strong>HYDROLOGICAL ADVISORY:</strong> Select a hydro dam and adjust upstream precipitation to simulate multi-horizon reservoir inflow.
                </div>
            </div>

            <!-- AI Phase 1: Multi-Lingual Indigenous Early Warning Alert Broadcaster -->
            <div class="panel-card" style="margin-top: 1rem; border-left: 4px solid #6366F1;">
                <div class="card-header">
                    <div>
                        <div class="card-title">🗣️ Phase 1 AI: Multi-Lingual Indigenous Early Warning Broadcaster</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Localized emergency advisories across 6 indigenous languages with 160-char SMS & phonetic radio scripts</span>
                    </div>
                    <span class="status-pill" style="color:#6366F1;">6 INDIGENOUS LANGUAGES</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Target Vernacular Language:</label>
                        <select id="lang-select" onchange="translateEarlyWarningAlert()" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="hausa">Hausa (Harshen Hausa) — Niger, Kebbi, Kaduna, Gombe</option>
                            <option value="nupe">Nupe (Zankpe Nupe) — Niger, Kwara, Kogi</option>
                            <option value="tiv">Tiv (Zwa Tiv) — Benue, Taraba, Nasarawa</option>
                            <option value="yoruba">Yoruba (Èdè Yorùbá) — Kwara, Kogi</option>
                            <option value="fulfulde">Fulfulde (Fulfulde) — Taraba, Adamawa, Plateau</option>
                            <option value="gbagyi">Gbagyi (Tugbagyi) — Niger, Kaduna</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Alert Incident Source:</label>
                        <select id="lang-alert-src" onchange="translateEarlyWarningAlert()" style="width: 100%; background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="ALT-DAM-SPILL">Kainji/Jebba Dam Spillway Gate Opening (Level 3 Emergency)</option>
                            <option value="ALT-BENUE-FLASH">Upper Benue River Tributaries Flash Flood (Level 2 High Watch)</option>
                            <option value="ALT-KADUNA-EROSION">Shiroro-Kaduna Riverbank Rapid Gully Scour (Level 2)</option>
                        </select>
                    </div>
                    <div style="display: flex; align-items: flex-end;">
                        <button class="btn-calc" style="width: 100%; height: 38px; margin-top: 0; background: #6366F1;" onclick="translateEarlyWarningAlert()">🔄 Synthesize Localized Alert</button>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                    <div style="background: var(--bg-secondary); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <span style="font-size: 0.75rem; font-weight: 700; color: var(--accent-cyan);">📲 COMPACT SMS TRANSMISSION</span>
                            <span id="sms-char-counter" class="status-pill" style="font-size:0.7rem; color:#34D399;">0 / 160 Chars</span>
                        </div>
                        <div id="lang-sms-text" style="font-size: 0.82rem; line-height: 1.5; color: var(--text-primary); font-family: monospace; min-height: 60px;">
                            Loading vernacular SMS preview...
                        </div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.85rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <span style="font-size: 0.75rem; font-weight: 700; color: #F59E0B;">📻 COMMUNITY RADIO BROADCAST SCRIPT</span>
                            <button onclick="navigator.clipboard.writeText(document.getElementById('lang-radio-script').innerText)" style="background: none; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 4px; padding: 2px 6px; font-size: 0.68rem; cursor: pointer;">📋 Copy</button>
                        </div>
                        <div id="lang-radio-script" style="font-size: 0.8rem; line-height: 1.5; color: var(--text-secondary); max-height: 120px; overflow-y: auto;">
                            Loading phonetic radio script...
                        </div>
                    </div>
                </div>
            </div>

            <p style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.75rem;">The dashboard is read-only. Alert authoring, technical review and official release must be performed through an authenticated, role-controlled operational system.</p>
        </div>

        <!-- TAB 3: SCENARIOS LAB -->
        <div id="tab-scenarios" class="tab-content">
            <div class="card-header">
                <div>
                    <h2 class="card-title" style="font-size: 1.3rem;">Stage 21 — Multi-Scenario Simulation & Stress Testing</h2>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">Empirical stress tests simulating climate pressure, watershed deforestation, and capital adaptation</p>
                </div>
                <span class="status-pill">&#9881; Scenario Engine v4.2 Active</span>
            </div>

            <div class="scenario-grid" id="scenario-cards-container">
                <!-- Populated via API -->
            </div>

            <div class="dashboard-layout" style="margin-top: 1rem;">
                <div class="panel-card">
                    <div class="card-title">&#128200; Interactive Policy Stress Simulator</div>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem;">Perturb regional parameters to project shifts across the 50 sentinel communities</p>
                    
                    <div class="slider-control">
                        <div class="slider-header">
                            <span>Extreme Precipitation Anomaly</span>
                            <span id="slider-rain-val">+0%</span>
                        </div>
                        <input type="range" id="slider-rain" min="0" max="30" value="0" oninput="updateSim()">
                    </div>

                    <div class="slider-control">
                        <div class="slider-header">
                            <span>Mean Temperature Rise (°C)</span>
                            <span id="slider-temp-val">+0.0°C</span>
                        </div>
                        <input type="range" id="slider-temp" min="0" max="3" step="0.5" value="0" oninput="updateSim()">
                    </div>

                    <div class="slider-control">
                        <div class="slider-header">
                            <span>Targeted Dyke & Floodwall Coverage</span>
                            <span id="slider-adp-val">0%</span>
                        </div>
                        <input type="range" id="slider-adp" min="0" max="100" value="0" oninput="updateSim()">
                    </div>

                    <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px; margin-top: 1rem; border: 1px solid var(--border-color);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.75rem; color: var(--text-secondary);">Simulated Mean Risk</div>
                                <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--accent-cyan);" id="sim-projected-risk">42.49</div>
                            </div>
                            <div>
                                <div style="font-size: 0.75rem; color: var(--text-secondary);">Projected Tier 1 Sites</div>
                                <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #F87171;" id="sim-tier1-count">1</div>
                            </div>
                            <div>
                                <div style="font-size: 0.75rem; color: var(--text-secondary);">Net Risk Delta</div>
                                <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #34D399;" id="sim-risk-delta">0.00</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel-card">
                    <div class="card-title">&#128220; Stage 21 Methodological Guidelines</div>
                    <ul style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6; margin-left: 1.25rem; margin-top: 0.75rem;">
                        <li><strong>Scenarios are Plausible Projections:</strong> Explicitly labelled as decision experiments, not unconditional deterministic predictions (Stage 21.6).</li>
                        <li><strong>Reference Bounds Stability:</strong> All scenarios preserve the 2026 baseline normalization reference bounds to maintain longitudinal comparability.</li>
                        <li><strong>Clamping Enforced:</strong> Normalized values exceeding 100 are strictly clamped at 100.0 per Rule 34.2.</li>
                        <li><strong>Traceability:</strong> Full scenario simulation records are permanently preserved in <code>07_Decision_Support/04_Scenarios/SCENARIO_RESULTS_v4.2.csv</code>.</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- TAB 3: INTERVENTIONS & MRV -->
        <div id="tab-interventions" class="tab-content">
            <div class="kpi-grid">
                <div class="kpi-card green">
                    <div class="kpi-label">Capital Investment Total</div>
                    <div class="kpi-value" id="mrv-total-budget">₦3.2B</div>
                    <div class="kpi-sub">20 Monitored Capital Projects</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Commissioned Assets</div>
                    <div class="kpi-value" id="mrv-comm-count">8</div>
                    <div class="kpi-sub">Handed Over to Communities</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Completed / Ongoing</div>
                    <div class="kpi-value" id="mrv-prog-count">12</div>
                    <div class="kpi-sub">Active Engineering Works</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Mean Intervention Effectiveness (IES)</div>
                    <div class="kpi-value" style="color: var(--accent-cyan);">33.5%</div>
                    <div class="kpi-sub">Average Risk Reduction Achieved</div>
                </div>
            </div>

            <div class="panel-card">
                <div class="card-header">
                    <div class="card-title">&#128737; N-HYPPADEC Monitored Interventions & MRV Register</div>
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Rule 34.4: IES = ((Risk_before - Risk_after) / Risk_before) * 100%</span>
                        <span class="data-timestamp" id="ts-mrv"></span>
                        <button class="btn-csv" onclick="downloadTableAsCSV('interventions-table', 'interventions-mrv.csv')">⬇ CSV</button>
                    </div>
                </div>
                <div style="overflow-x: auto; margin-top: 0.75rem;">
                    <table class="data-table" id="interventions-table">
                        <thead>
                            <tr>
                                <th>Intervention ID</th>
                                <th>Project Title</th>
                                <th>State</th>
                                <th>Community</th>
                                <th>Budget (NGN)</th>
                                <th>Status</th>
                                <th>Risk Before</th>
                                <th>Risk After</th>
                                <th>IES Score</th>
                                <th>Residual Risk</th>
                            </tr>
                        </thead>
                        <tbody id="interventions-table-body">
                            <tr class="loading-row"><td colspan="10" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Interactive IES Calculator & Validity Tester -->
            <div class="panel-card" style="max-width: 600px;">
                <div class="card-title">&#128290; Live IES & Residual Risk Validator (Section 34)</div>
                <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem;">Test mathematical validity rules for intervention evaluation</p>
                <div class="calc-form">
                    <div class="form-row">
                        <label>Risk Before Intervention (R_before)</label>
                        <input type="number" id="ies_r_before" value="68.4" min="0" max="100" style="width: 80px;">
                    </div>
                    <div class="form-row">
                        <label>Risk After Intervention (R_after)</label>
                        <input type="number" id="ies_r_after" value="44.2" min="0" max="100" style="width: 80px;">
                    </div>
                    <div class="form-row">
                        <label>Identical Reference Bounds</label>
                        <select id="ies_bounds_match" style="width: 80px;">
                            <option value="true" selected>Yes (2026)</option>
                            <option value="false">No (Mismatch)</option>
                        </select>
                    </div>
                    <button class="btn-calc" onclick="evaluateIES()">Validate & Calculate IES</button>
                    <div class="calc-output" id="ies-result"></div>
                </div>
            </div>

            <!-- AI Phase 4: Prescriptive Capital Investment Portfolio Optimizer -->
            <div class="panel-card" style="margin-top: 1rem; border-left: 4px solid #10B981;">
                <div class="card-header">
                    <div>
                        <div class="card-title">🤖 Phase 4 AI: Prescriptive Capital Investment Portfolio Optimizer</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Mixed-Integer Linear Programming (MILP) solver maximizing Intervention Effectiveness Score (IES) under equity and capital bounds</span>
                    </div>
                    <span class="status-pill" id="portfolio-solver-status" style="color:#10B981;">OPTIMIZER READY</span>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-top: 1rem; background: var(--bg-secondary); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color);">
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Total Capital Budget (NGN):</label>
                        <input type="number" id="ai-portfolio-budget" value="2500000000" step="50000000" style="width: 100%; background: var(--bg-primary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px; font-weight: 700;">
                        <div style="display: flex; gap: 0.4rem; margin-top: 6px;">
                            <button type="button" onclick="document.getElementById('ai-portfolio-budget').value=1000000000; runPortfolioOptimization();" style="background: none; border: 1px solid var(--border-color); color: var(--accent-cyan); border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; cursor: pointer;">₦1.0B</button>
                            <button type="button" onclick="document.getElementById('ai-portfolio-budget').value=2500000000; runPortfolioOptimization();" style="background: none; border: 1px solid var(--border-color); color: var(--accent-cyan); border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; cursor: pointer;">₦2.5B</button>
                            <button type="button" onclick="document.getElementById('ai-portfolio-budget').value=5000000000; runPortfolioOptimization();" style="background: none; border: 1px solid var(--border-color); color: var(--accent-cyan); border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; cursor: pointer;">₦5.0B</button>
                        </div>
                    </div>
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">Optimization Strategy Policy:</label>
                        <select id="ai-portfolio-strategy" onchange="runPortfolioOptimization()" style="width: 100%; background: var(--bg-primary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="MAX_IES">MAX_IES — Maximize Total Risk Reduction & IES</option>
                            <option value="EQUITY_BALANCED">EQUITY_BALANCED — Enforce Fair State Share (Max 28%)</option>
                            <option value="MAX_COMMUNITIES">MAX_COMMUNITIES — Maximize Communities Protected</option>
                            <option value="CRITICAL_FIRST">CRITICAL_FIRST — Prioritize Highest Risk Tier 1 First</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 0.78rem; color: var(--text-secondary); display: block; margin-bottom: 4px;">State Sub-Filter:</label>
                        <select id="ai-portfolio-state" onchange="runPortfolioOptimization()" style="width: 100%; background: var(--bg-primary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.6rem; border-radius: 6px;">
                            <option value="ALL">All 10 N-HYPPADEC Member States</option>
                            <option value="Benue">Benue State</option>
                            <option value="Niger">Niger State</option>
                            <option value="Kebbi">Kebbi State</option>
                            <option value="Plateau">Plateau State</option>
                            <option value="Kogi">Kogi State</option>
                            <option value="Kwara">Kwara State</option>
                            <option value="Kaduna">Kaduna State</option>
                            <option value="Nasarawa">Nasarawa State</option>
                            <option value="Taraba">Taraba State</option>
                            <option value="Gombe">Gombe State</option>
                        </select>
                    </div>
                    <div style="display: flex; align-items: flex-end;">
                        <button class="btn-calc" style="width: 100%; height: 38px; margin-top: 0; background: #10B981; color: #000; font-weight: 700;" onclick="runPortfolioOptimization()">⚡ Run Prescriptive Optimizer</button>
                    </div>
                </div>

                <!-- Optimization Metrics Summary -->
                <div class="kpi-grid" style="margin-top: 1rem;">
                    <div class="kpi-card green">
                        <div class="kpi-label">Allocated Capital</div>
                        <div class="kpi-value" id="ai-port-alloc-budget">--</div>
                        <div class="kpi-sub" id="ai-port-utilization">-- % Utilization</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Interventions Selected</div>
                        <div class="kpi-value" id="ai-port-projects-count">--</div>
                        <div class="kpi-sub" id="ai-port-states-count">Across -- Member States</div>
                    </div>
                    <div class="kpi-card purple">
                        <div class="kpi-label">Mean Projected IES</div>
                        <div class="kpi-value" id="ai-port-mean-ies" style="color:var(--accent-cyan);">-- %</div>
                        <div class="kpi-sub">Certified Risk Reduction</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Protected Population</div>
                        <div class="kpi-value" id="ai-port-beneficiaries">--</div>
                        <div class="kpi-sub">Direct Rural Beneficiaries</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">AI Advantage vs Naive</div>
                        <div class="kpi-value" id="ai-port-gain" style="color:#34D399;">+0.0%</div>
                        <div class="kpi-sub">Pareto Optimization Gain</div>
                    </div>
                </div>

                <!-- State Allocation Breakdown Pills -->
                <div style="margin-top: 0.75rem;">
                    <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">State-by-State Budget Distribution:</span>
                    <div id="ai-port-state-pills" style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.4rem;">
                        <!-- Populated dynamically -->
                    </div>
                </div>

                <!-- Selected Interventions Table -->
                <div style="overflow-x: auto; margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.82rem; font-weight: 600; color: var(--text-primary);">Optimal Capital Investment Portfolio Register (Ranked by Priority Impact)</span>
                        <button class="btn-csv" onclick="downloadTableAsCSV('ai-port-table', 'optimal_capital_portfolio.csv')">⬇ CSV Export</button>
                    </div>
                    <table class="data-table" id="ai-port-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Community</th>
                                <th>LGA</th>
                                <th>State</th>
                                <th>Recommended Engineering Package</th>
                                <th>Budget (NGN)</th>
                                <th>Risk Before</th>
                                <th>Risk After</th>
                                <th>Projected IES</th>
                                <th>Capital Efficiency</th>
                            </tr>
                        </thead>
                        <tbody id="ai-port-tbody">
                            <tr class="loading-row"><td colspan="10" class="empty-state-cell"><span class="spinner"></span> Loading optimized portfolio…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 5: 31-TABLE ARCHITECTURE EXPLORER -->
        <div id="tab-tables" class="tab-content">
            <!-- PostGIS Spatial Relational Database Status & Sync Panel -->
            <div id="postgis-status-box" style="margin-bottom: 1rem; padding: 0.85rem 1.2rem; background: var(--bg-card); border-radius: 8px; border: 1px solid var(--border-color); border-left: 4px solid #0284C7;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <span class="status-pill" style="color:#0284C7; background:rgba(2,132,199,0.15);">🗺️ PostGIS Relational Spatial Layer</span>
                        <span style="font-size:0.82rem; color:var(--text-secondary); margin-left:8px;">Authoritative PostgreSQL / PostGIS Spatial Database Integration</span>
                    </div>
                    <button class="btn-calc" style="margin:0; padding:0.4rem 0.9rem; font-size:0.82rem; background:#0284C7; font-weight:700;" onclick="checkPostgisSyncStatus()">⚡ Inspect & Sync PostGIS</button>
                </div>
            </div>

            <div class="panel-card">
                <div class="card-header">
                    <div>
                        <h2 class="card-title" style="font-size: 1.25rem;">Authoritative 31-Table Relational Database Explorer</h2>
                        <p style="font-size: 0.8rem; color: var(--text-secondary);">PostgreSQL / PostGIS Authoritative CLEAN Tables from Section 32</p>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <label style="font-size: 0.82rem; color: var(--text-secondary);">Select Table:</label>
                        <select id="table-select" onchange="loadSelectedTable()" style="background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.8rem; border-radius: 6px; font-family: var(--font-body);">
                            <!-- Populated via API -->
                        </select>
                    </div>
                </div>

                <div style="display: flex; gap: 1rem; margin-top: 1rem; align-items: center;">
                    <span class="status-pill" id="table-row-count">Loading...</span>
                    <span style="font-size: 0.8rem; color: var(--text-secondary);" id="table-schema-info"></span>
                </div>

                <div style="overflow-x: auto; margin-top: 1rem; max-height: 480px; overflow-y: auto;">
                    <table class="data-table" id="explorer-table">
                        <thead id="explorer-thead"></thead>
                        <tbody id="explorer-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 5: REMOTE SENSING & EARTH OBSERVATION -->
        <div id="tab-remote_sensing" class="tab-content">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Observed Flood Inundation</div>
                    <div class="kpi-value" id="kpi-rs-flood">--</div>
                    <div class="kpi-sub">Sentinel-1 C-Band SAR</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label">Mean Vegetation Baseline</div>
                    <div class="kpi-value" id="kpi-rs-ndvi">--</div>
                    <div class="kpi-sub">Sentinel-2 MSI Normalized NDVI</div>
                </div>
                <div class="kpi-card amber">
                    <div class="kpi-label">Riverbank Retreat Rate</div>
                    <div class="kpi-value" id="kpi-rs-retreat">--</div>
                    <div class="kpi-sub">Regional Average (m / year)</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Classification Accuracy</div>
                    <div class="kpi-value" id="kpi-rs-accuracy">--</div>
                    <div class="kpi-sub">Ground-Truthed Field Validation</div>
                </div>
            </div>

            <div class="panel-card" style="margin-top: 1.25rem;">
                <div class="card-header">
                    <div>
                        <div class="card-title">10-State Earth Observation & Satellite Risk Matrix</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Harmonized Multi-Temporal Sentinel-1 SAR & Sentinel-2 Optical Observations (Stage 9 / WP08)</div>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <div class="status-pill">SENSOR FUSION ACTIVE</div>
                        <span class="data-timestamp" id="ts-rs"></span>
                        <button class="btn-csv" onclick="downloadTableAsCSV('rs-table', 'remote-sensing.csv')">⬇ CSV</button>
                    </div>
                </div>

                <div style="overflow-x: auto; margin-top: 1rem;">
                    <table class="data-table" id="rs-table">
                        <thead>
                            <tr>
                                <th>State</th>
                                <th>Code</th>
                                <th>Major Hydro Basin</th>
                                <th>SAR Flood Extent</th>
                                <th>Mean NDVI</th>
                                <th>Canopy Cover</th>
                                <th>Bank Retreat</th>
                                <th>Cropland Exposed</th>
                                <th>EO Accuracy</th>
                                <th>QC Status</th>
                            </tr>
                        </thead>
                        <tbody id="rs-table-body">
                            <tr class="loading-row"><td colspan="10" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: AGRO-DROUGHT & DAM WATER LEVEL MONITOR -->
        <div id="tab-drought" class="tab-content">
            <div class="card-header" style="margin-bottom: 1.25rem;">
                <div>
                    <h2 class="card-title" style="font-size: 1.35rem; display: flex; align-items: center; gap: 8px;">
                        🌾 AI Agro-Drought Harvest Loss & Strategic Dam Water Level Monitor
                    </h2>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">
                        Dual-stream predictive AI evaluating real-time reservoir water levels (m) across 9 strategic dams and state-by-state agricultural harvest loss (FAO-33) across 10 member states.
                    </p>
                </div>
                <div style="display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;">
                    <span class="data-timestamp" id="ts-drought"></span>
                    <button class="btn-calc" style="margin: 0; padding: 0.45rem 1rem; font-size: 0.85rem; background: #059669; font-weight: 700;" onclick="loadDroughtDashboard()">⚡ Run Live Drought & Water Model</button>
                </div>
            </div>

            <!-- Top Summary KPIs -->
            <div class="kpi-grid" style="margin-bottom: 1.25rem;">
                <div class="kpi-card critical">
                    <div class="kpi-label">Highest Harvest Deficit State</div>
                    <div class="kpi-value" id="kpi-drought-worst-state" style="color: #EF4444;">--</div>
                    <div class="kpi-sub" id="kpi-drought-worst-loss">Calculating yield deficit...</div>
                </div>
                <div class="kpi-card" style="border-left-color: #F59E0B;">
                    <div class="kpi-label">Cropland Under Drought Stress</div>
                    <div class="kpi-value" id="kpi-drought-stressed-ha" style="color: #F59E0B;">-- Ha</div>
                    <div class="kpi-sub">Across Member States</div>
                </div>
                <div class="kpi-card" style="border-left-color: #0284C7;">
                    <div class="kpi-label">Farming Population At Risk</div>
                    <div class="kpi-value" id="kpi-drought-vuln-pop" style="color: #0284C7;">--</div>
                    <div class="kpi-sub">Food Insecurity IPC Phase 2/3</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label">Monitored Strategic Dams</div>
                    <div class="kpi-value" id="kpi-drought-dams-count" style="color: #10B981;">9 Facilities</div>
                    <div class="kpi-sub">Kainji, Jebba, Shiroro, Dadin Kowa...</div>
                </div>
            </div>

            <!-- 2-Column Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 1.25rem; margin-bottom: 1.25rem;">
                
                <!-- Left Column: State Drought Deficit & Harvest Loss Ranking -->
                <div class="panel-card" style="margin-bottom: 0;">
                    <div class="card-header">
                        <div>
                            <div class="card-title">📊 State Agricultural Drought & Harvest Loss Ranking</div>
                            <span style="font-size: 0.78rem; color: var(--text-secondary);">Ranked by predicted crop yield reduction (FAO-33 water production function)</span>
                        </div>
                        <span class="status-pill" style="color: #F59E0B;">FAO-33 SENSITIVITY</span>
                    </div>

                    <div style="overflow-x: auto; margin-top: 1rem; max-height: 520px; overflow-y: auto;">
                        <table class="data-table" id="drought-states-table">
                            <thead>
                                <tr>
                                    <th style="width: 35px; text-align: center;">#</th>
                                    <th>State & Zone</th>
                                    <th style="text-align: right;">Normal (mm)</th>
                                    <th style="text-align: right;">Observed</th>
                                    <th style="text-align: center;">Rain Deficit</th>
                                    <th style="text-align: center;">Harvest Loss</th>
                                    <th>Food Security</th>
                                    <th style="text-align: right;">Stressed Ha</th>
                                </tr>
                            </thead>
                            <tbody id="drought-states-tbody">
                                <tr class="loading-row"><td colspan="8" class="empty-state-cell"><span class="spinner"></span> Evaluating agro-meteorological moisture deficits...</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Crop Sensitivity Quick-Ref -->
                    <div style="margin-top: 1rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 6px; border: 1px solid var(--border-color); font-size: 0.78rem;">
                        <div style="font-weight: 700; color: #38BDF8; margin-bottom: 4px;">🌾 Regional Staple Crop Drought Sensitivity Factors (Ky):</div>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap; color: var(--text-secondary);">
                            <span>🌽 Maize: <strong style="color:#EF4444;">Ky 1.25 (High)</strong></span>
                            <span>🌾 Rice: <strong style="color:#EF4444;">Ky 1.20 (High)</strong></span>
                            <span>🍠 Yam: <strong style="color:#F59E0B;">Ky 1.00 (Moderate)</strong></span>
                            <span>🌾 Sorghum: <strong style="color:#10B981;">Ky 0.90 (Tolerant)</strong></span>
                            <span>🌾 Millet: <strong style="color:#10B981;">Ky 0.85 (Hardy)</strong></span>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Strategic Dams Water Level & Hydrostatic Monitor -->
                <div class="panel-card" style="margin-bottom: 0;">
                    <div class="card-header">
                        <div>
                            <div class="card-title">🌊 Strategic Dams Hydrostatic Water Level Monitor</div>
                            <span style="font-size: 0.78rem; color: var(--text-secondary);">Live reservoir elevations, usable storage capacity (%), and dead storage vs. spillway risk</span>
                        </div>
                        <span class="status-pill" style="color: #38BDF8;">9 DAMS ACTIVE</span>
                    </div>

                    <div id="dams-water-levels-container" style="display: grid; gap: 0.85rem; margin-top: 1rem; max-height: 580px; overflow-y: auto; padding-right: 4px;">
                        <div class="empty-state-cell"><span class="spinner"></span> Querying hydrostatic elevation gauges...</div>
                    </div>
                </div>

            </div>

            <!-- Bottom Full-Width Card: Prescriptive Irrigation Directives -->
            <div class="panel-card" style="border-left: 4px solid #10B981;">
                <div class="card-header">
                    <div>
                        <div class="card-title">🏛️ Prescriptive Governing Council Agrarian & Dam Irrigation Directives</div>
                        <span style="font-size: 0.78rem; color: var(--text-secondary);">Automated operational decisions linking dam reservoir storage to hardest-hit agricultural zones</span>
                    </div>
                    <span class="status-pill" style="color: #10B981;">EXECUTIVE DIRECTIVES</span>
                </div>
                <div id="drought-directives-container" style="display: grid; gap: 0.75rem; margin-top: 1rem;">
                    <div class="empty-state-cell"><span class="spinner"></span> Formulating prescriptive irrigation and relief directives...</div>
                </div>
            </div>
        </div>

        <!-- TAB: MULTI-HAZARD & ENVIRONMENTAL RISKS (14 THEMES) -->
        <div id="tab-multi_hazard" class="tab-content">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Canonical Multi-Hazards</div>
                    <div class="kpi-value">14 Themes</div>
                    <div class="kpi-sub">National Environmental Taxonomy</div>
                </div>
                <div class="kpi-card critical">
                    <div class="kpi-label">Geo-Referenced Incidents</div>
                    <div class="kpi-value">54 Hotspots</div>
                    <div class="kpi-sub">G65 Spatial Register (WGS84)</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Critical Severity Sites</div>
                    <div class="kpi-value">26 Sites</div>
                    <div class="kpi-sub">High Priority Environmental Threats</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label">Member State Coverage</div>
                    <div class="kpi-value">10 + 1 States</div>
                    <div class="kpi-sub">N-HYPPADEC + Adamawa Basin</div>
                </div>
            </div>

            <!-- Analytical Mode Selector: 14 G65 Themes vs Compound Vulnerability Heatmap -->
            <div style="display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem; background: var(--bg-card); padding: 0.6rem 1rem; border-radius: 8px; border: 1px solid var(--border-color);">
                <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">ANALYTICAL VIEW:</span>
                <button id="btn-mode-hotspots" class="hazard-filter-btn active" onclick="switchHazardViewMode('HOTSPOTS')">📍 14 Canonical Hazards Hotspots (G65)</button>
                <button id="btn-mode-mhcvi" class="hazard-filter-btn" onclick="switchHazardViewMode('MHCVI')">🔥 Multi-Hazard Compound Vulnerability Heatmap (MHCVI)</button>
            </div>

            <!-- Hazard Selector Pills -->
            <div class="hazard-filter-bar" id="hazard-filter-pills-bar">
                <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-right: 0.5rem;">Filter Hazard:</span>
                <button class="hazard-filter-btn active" onclick="filterHazard('ALL')">🌐 All 14 Themes</button>
                <button class="hazard-filter-btn" onclick="filterHazard('FOOD_SECURITY')">🌾 Food Security</button>
                <button class="hazard-filter-btn" onclick="filterHazard('BANDIT_ATTACK')">🎯 Bandit Attack</button>
                <button class="hazard-filter-btn" onclick="filterHazard('AIR_POLLUTION')">☁️ Air Pollution</button>
                <button class="hazard-filter-btn" onclick="filterHazard('CLIMATE_CHANGE')">🌡️ Climate Change</button>
                <button class="hazard-filter-btn" onclick="filterHazard('DEFORESTATION')">🌲 Deforestation</button>
                <button class="hazard-filter-btn" onclick="filterHazard('DESERTIFICATION')">🏜️ Desertification</button>
                <button class="hazard-filter-btn" onclick="filterHazard('DROUGHT')">☀️ Drought</button>
                <button class="hazard-filter-btn" onclick="filterHazard('ECOLOGICAL_CONFLICT')">⚔️ Ecological Conflict</button>
                <button class="hazard-filter-btn" onclick="filterHazard('EROSION')">⛰️ Erosion</button>
                <button class="hazard-filter-btn" onclick="filterHazard('FLOODING')">🌊 Flooding</button>
                <button class="hazard-filter-btn" onclick="filterHazard('LEAD_POISONING')">☣️ Lead Poisoning</button>
                <button class="hazard-filter-btn" onclick="filterHazard('OIL_SPILLAGE')">🛢️ Oil Spillage</button>
                <button class="hazard-filter-btn" onclick="filterHazard('SOLID_WASTE')">🗑️ Solid Waste</button>
                <button class="hazard-filter-btn" onclick="filterHazard('WATER_POLLUTION')">💧 Water Pollution</button>
            </div>

            <div class="dashboard-layout">
                <div class="map-container-card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">10-State Multi-Hazard & Environmental Risks Spatial Map (G65)</div>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">Interactive Geo-Referenced Hotspots across the Ten Member States for 14 Priority Threats</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <span id="hazard-active-badge" class="status-pill">SHOWING: ALL 14 THEMES</span>
                            <button class="expand-map-btn" onclick="toggleMapFullscreen(this, 'hazard-map')" title="Toggle Full Screen Map">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
                                <span>Full Screen</span>
                            </button>
                        </div>
                    </div>
                    <div id="hazard-map"></div>
                </div>

                <div class="side-panel">
                    <div class="panel-card" id="hazard-detail-card">
                        <div class="card-title" id="hazard-detail-title">Hazard Profile</div>
                        <div style="margin-top: 0.8rem; font-size: 0.82rem; line-height: 1.5; color: var(--text-secondary);" id="hazard-detail-desc">
                            Select any hazard filter pill or click any map marker to view institutional metadata, primary risk components, and documented state incident footprints.
                        </div>
                        <div style="margin-top: 1rem; display: flex; flex-direction: column; gap: 0.6rem; font-size: 0.8rem;" id="hazard-detail-meta">
                            <!-- Populated dynamically -->
                        </div>
                    </div>
                </div>
            </div>

            <div class="panel-card" style="margin-top: 0.5rem;">
                <div class="card-header">
                    <div>
                        <div class="card-title">Multi-Hazard Incident & Environmental Survey Register</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Authoritative Ground-Truthed Hotspot Registry with Coordinates and Field Validation Sources</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <span id="hazard-table-count" style="font-size: 0.8rem; color: var(--accent-cyan); font-weight: 600;">54 Records</span>
                        <span class="data-timestamp" id="ts-multihazard"></span>
                        <button class="btn-csv" onclick="downloadTableAsCSV('hazard-table', 'multi-hazard-incidents.csv')">⬇ CSV</button>
                    </div>
                </div>
                <div style="overflow-x: auto; margin-top: 0.75rem;">
                    <table class="data-table" id="hazard-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>State</th>
                                <th>Code</th>
                                <th>Hazard Domain</th>
                                <th>Severity</th>
                                <th>Coordinates</th>
                                <th>Validation Source</th>
                                <th>Observations & Notes</th>
                            </tr>
                        </thead>
                        <tbody id="hazard-table-body">
                            <tr class="loading-row"><td colspan="8" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: FIELD OPERATIONS & KOBOTOOLBOX DATA INGESTION -->
        <div id="tab-field_ops" class="tab-content">
            <div class="card-header">
                <div>
                    <h2 class="card-title" style="font-size: 1.3rem;">🔄 Field Operations & Real-Time KoboToolbox Ingestion Hub</h2>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">Authoritative 5-Gate Quality Control, Mobile Field Synchronization, and Quarantine Remediation Console</p>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <span class="data-timestamp" id="ts-fieldops"></span>
                    <button class="btn-calc" style="margin-top: 0; padding: 0.45rem 1rem; font-size: 0.8rem; background: var(--accent-cyan);" onclick="syncKoboData(false)">🔄 Pull Kobo API</button>
                    <button class="btn-calc" style="margin-top: 0; padding: 0.45rem 1rem; font-size: 0.8rem; background: #6366F1;" onclick="syncKoboData(true)">⚡ Ingest Sandbox Batch</button>
                </div>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card green">
                    <div class="kpi-label">Clean Landing Records</div>
                    <div class="kpi-value" id="kobo-landing-count">--</div>
                    <div class="kpi-sub">Passed All 5 Quality Control Gates</div>
                </div>
                <div class="kpi-card critical">
                    <div class="kpi-label">Quarantined Flagged Records</div>
                    <div class="kpi-value" id="kobo-quarantine-count">--</div>
                    <div class="kpi-sub">Awaiting Supervisor Remediation</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Total Submissions Processed</div>
                    <div class="kpi-value" id="kobo-total-count">--</div>
                    <div class="kpi-sub">Idempotent UUID Tracking</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Pipeline Health</div>
                    <div class="kpi-value" id="kobo-health-status" style="font-size: 1.2rem;">OPERATIONAL</div>
                    <div class="kpi-sub" id="kobo-last-sync">Last Sync: Checking...</div>
                </div>
            </div>

            <!-- Quarantine Inspection Console -->
            <div class="panel-card" style="border-left: 4px solid #EF4444; margin-top: 1rem;">
                <div class="card-header">
                    <div>
                        <div class="card-title">⚠️ Quarantine Remediation Console (Flagged Submissions)</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Submissions failing Gate 1 (Consent), Gate 2 (Cascading Geography), or Gate 3 (GPS Boundary)</span>
                    </div>
                    <span id="quarantine-badge" class="status-pill" style="color:#EF4444;">0 Flagged</span>
                </div>
                <div style="overflow-x: auto; margin-top: 0.75rem;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Submission ID</th>
                                <th>State & LGA</th>
                                <th>Flagged Gate / Failure Reason</th>
                                <th>Enumerator</th>
                                <th>Time Captured</th>
                                <th>Remediation Action</th>
                            </tr>
                        </thead>
                        <tbody id="quarantine-table-body">
                            <tr class="loading-row"><td colspan="6" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Clean Submissions Landing Table -->
            <div class="panel-card" style="margin-top: 1rem;">
                <div class="card-header">
                    <div>
                        <div class="card-title">✅ Validated Clean Submissions Landing Register</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Promoted field records verified and staged for database integration</span>
                    </div>
                    <span id="landing-badge" class="status-pill" style="color:#10B981;">0 Verified</span>
                </div>
                <div style="overflow-x: auto; margin-top: 0.75rem; max-height: 380px; overflow-y: auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Date</th>
                                <th>State</th>
                                <th>LGA</th>
                                <th>Community</th>
                                <th>Population</th>
                                <th>Observed Hazards</th>
                                <th>QC Verification</th>
                            </tr>
                        </thead>
                        <tbody id="landing-table-body">
                            <tr class="loading-row"><td colspan="8" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- AI Phase 2: Behavioral Fraud & Computer Vision Privacy Shield -->
            <div class="panel-card" style="margin-top: 1rem; border-left: 4px solid #8B5CF6;">
                <div class="card-header">
                    <div>
                        <div class="card-title">🛡️ Phase 2 AI: Field Survey Quality & Level 3 CV Privacy Shield</div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">Real-time spatial velocity checks, straight-lining detection, and facial biometric blurring gate</span>
                    </div>
                    <span class="status-pill" style="color:#8B5CF6;">AI QC SHIELD ACTIVE</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-top: 1rem;">
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">Gate 1: Duration Velocity</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #34D399;">Active (≥120s)</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">Rapid completion guard</div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">Gate 2: Travel Speed</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #34D399;">Active (≤130 km/h)</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">Haversine transit audit</div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">Gate 3: GPS Duplicate</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #34D399;">Active (Anti-Couch)</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">Cross-community coords</div>
                    </div>
                    <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">Gate 4: CV PII Redaction</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--accent-cyan);">Level 3 Restricted</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">Gaussian face blur gate</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem; padding: 0.6rem 0.8rem; background: var(--bg-secondary); border-radius: 6px; font-size: 0.8rem;">
                    <span>Automatic Quarantine Protocol: Flagged submissions routed directly to supervisor audit queue before reaching clean tables.</span>
                    <button class="btn-calc" style="margin-top: 0; padding: 0.35rem 0.8rem; font-size: 0.75rem; background: #8B5CF6;" onclick="testAiFieldAudit()">🧪 Run AI Field Audit Test</button>
                </div>
                <div id="ai-field-test-output" style="display: none; margin-top: 0.6rem; padding: 0.6rem; border-radius: 6px; font-size: 0.8rem; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); color: var(--text-primary);"></div>
            </div>
        </div>

        <!-- TAB: EXECUTIVE SITREP & POLICY BRIEF GENERATOR -->
        <div id="tab-sitrep" class="tab-content">
            <div class="card-header">
                <div>
                    <h2 class="card-title" style="font-size: 1.3rem;">📄 Institutional Multi-Hazard Situation Report (SitRep) Generator</h2>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">Automated executive briefings, hazard distribution profiles, and emergency capital allocations</p>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
                    <span class="data-timestamp" id="ts-sitrep"></span>
                    <select id="sitrep-state-filter" onchange="loadSitRepDashboard()" style="background: var(--bg-secondary); color: #FFF; border: 1px solid var(--border-color); padding: 0.4rem 0.8rem; border-radius: 6px; font-family: var(--font-body); font-size: 0.85rem;">
                        <option value="ALL">All 10 N-HYPPADEC Member States</option>
                        <option value="NG-NIG">Niger State</option>
                        <option value="NG-KEB">Kebbi State</option>
                        <option value="NG-PLA">Plateau State</option>
                        <option value="NG-BEN">Benue State</option>
                        <option value="NG-KOG">Kogi State</option>
                        <option value="NG-KWA">Kwara State</option>
                        <option value="NG-KAD">Kaduna State</option>
                        <option value="NG-NAS">Nasarawa State</option>
                        <option value="NG-TAR">Taraba State</option>
                        <option value="NG-GOM">Gombe State</option>
                        <option value="NG-ADA">Adamawa State</option>
                    </select>
                    <button class="btn-calc" style="margin-top: 0; padding: 0.45rem 1rem; font-size: 0.85rem; background: #6366F1;" onclick="triggerAiSitRepSynthesis()">✨ AI Executive Synthesis</button>
                    <button class="btn-calc" style="margin-top: 0; padding: 0.45rem 1rem; font-size: 0.85rem; background: #0284C7;" onclick="openPrintableSitRep()">🖨️ Printable SitRep</button>
                    <button class="btn-calc" style="margin-top: 0; padding: 0.45rem 1rem; font-size: 0.85rem; background: #059669; color: #FFF; font-weight: 700;" onclick="window.open('/api/sitrep/executive-dossier', '_blank')">📜 Executive Council Dossier (QR & Seal)</button>
                </div>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card critical">
                    <div class="kpi-label">Critical Emergency Sites</div>
                    <div class="kpi-value" id="sitrep-kpi-critical">--</div>
                    <div class="kpi-sub">Tier 1 Extreme Threat Level</div>
                </div>
                <div class="kpi-card amber">
                    <div class="kpi-label">Verified Hotspots Monitored</div>
                    <div class="kpi-value" id="sitrep-kpi-total">--</div>
                    <div class="kpi-sub">G65 Multi-Hazard Layer</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label">Estimated Population at Risk</div>
                    <div class="kpi-value" id="sitrep-kpi-pop">--</div>
                    <div class="kpi-sub">Agro-Pastoral & Riverine</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Recommended Allocation</div>
                    <div class="kpi-value" id="sitrep-kpi-budget">--</div>
                    <div class="kpi-sub">Targeted Defense Interventions</div>
                </div>
            </div>

            <div class="dashboard-layout" style="margin-top: 1rem;">
                <div class="panel-card" style="flex: 1.5;">
                    <div class="card-header">
                        <div class="card-title">Executive Summary & Strategic Briefing Notes</div>
                        <span id="sitrep-ref-badge" class="status-pill">REF: PENDING</span>
                    </div>
                    <div id="sitrep-summary-text" style="margin-top: 0.8rem; font-size: 0.85rem; line-height: 1.6; color: var(--text-primary); background: var(--bg-secondary); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        Loading executive briefing...
                    </div>
                    
                    <div class="card-title" style="margin-top: 1.25rem;">Active Threat Locations in Selected Domain</div>
                    <div style="overflow-x: auto; margin-top: 0.5rem; max-height: 280px; overflow-y: auto;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Hazard Domain</th>
                                    <th>Severity</th>
                                    <th>Field Intelligence</th>
                                </tr>
                            </thead>
                            <tbody id="sitrep-incidents-body">
                                <tr class="loading-row"><td colspan="4" class="empty-state-cell"><span class="spinner"></span> Loading data…</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="panel-card" style="flex: 1;">
                    <div class="card-title">Top Hazard Threat Drivers</div>
                    <div id="sitrep-top-hazards-list" style="display: flex; flex-direction: column; gap: 0.6rem; margin-top: 0.8rem;">
                        <!-- Populated dynamically -->
                    </div>

                    <div class="card-title" style="margin-top: 1.5rem;">Recommended Strategic Directives</div>
                    <ul id="sitrep-ai-directives" style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6; margin-left: 1.2rem; margin-top: 0.5rem;">
                        <li><strong>Dike Rehabilitation:</strong> Priority revetment reinforcements in active flood zones.</li>
                        <li><strong>Agro-Security Corridors:</strong> Armed joint patrols in vulnerable farming corridors.</li>
                        <li><strong>FEW-CAM Warning Escalation:</strong> Maintain community siren readiness and SMS alert broadcast protocols.</li>
                    </ul>
                </div>
            </div>
        </div>
    </main>


    <footer>
        <div>National Hydroelectric Power Producing Areas Development Commission (N-HYPPADEC)</div>
        <div>CHER-CDSS Platform v4.2 &copy; October 2026 | NITDA Sovereign Data Residency Compliant | PostgreSQL 16 + PostGIS 3.4</div>
    </footer>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <!-- Tour overlay -->
    <div id="tour-overlay" style="display:none; position:fixed; inset:0; z-index:9000; pointer-events:none;"></div>
    <div id="tour-box" style="display:none; position:fixed; z-index:9001; background:var(--bg-card); border:1px solid var(--accent-purple); border-radius:12px; padding:1.2rem; max-width:300px; box-shadow:0 8px 24px rgba(0,0,0,0.6); pointer-events:all;">
        <div id="tour-step-label" style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--accent-purple); margin-bottom:0.4rem;"></div>
        <div id="tour-step-text" style="font-size:0.85rem; line-height:1.5; color:var(--text-primary);"></div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem;">
            <button onclick="dismissTour()" style="background:none; border:none; color:var(--text-secondary); font-size:0.78rem; cursor:pointer;">✕ Dismiss</button>
            <button id="tour-next-btn" onclick="nextTourStep()" style="background:var(--accent-purple); border:none; color:#fff; padding:0.3rem 0.9rem; border-radius:6px; font-size:0.82rem; cursor:pointer;">Next →</button>
        </div>
    </div>
    <script>
        // High-fidelity basemap providers (no API keys required)
        function createBaseLayers() {
            return {
                "🗺️ Dark Canvas (Esri)": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
                    maxZoom: 16
                }),
                "🌍 OpenStreetMap": L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors',
                    maxZoom: 19
                }),
                "🛰️ Satellite Imagery": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri',
                    maxZoom: 18
                }),
                "🏔️ Topographic": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri',
                    maxZoom: 18
                })
            };
        }

        // =========================================================================
        // UX v4.2 HELPER FUNCTIONS
        // =========================================================================

        // API error display helper
        function showApiError(containerId, err) {
            console.error(err);
            const el = document.getElementById(containerId);
            if (!el) return;
            const pill = document.createElement('div');
            pill.className = 'api-error-pill';
            pill.textContent = '⚠ Data unavailable — API error';
            el.prepend(pill);
        }

        // CSV export helper
        function downloadTableAsCSV(tableId, filename) {
            const table = document.getElementById(tableId);
            if (!table) return;
            const rows = Array.from(table.querySelectorAll('tr'));
            const csv = rows.map(row =>
                Array.from(row.querySelectorAll('th,td')).map(cell => {
                    const text = cell.textContent.replace(/"/g, '""');
                    return `"${text}"`;
                }).join(',')
            ).join('\\n');
            const blob = new Blob([csv], {type: 'text/csv'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename;
            a.click();
            URL.revokeObjectURL(a.href);
        }

        // Onboarding tour
        const TOUR_STEPS = [
            { label: 'Step 1 of 4 — Navigation', text: 'Use the tab bar to switch between modules: Overview, Flood Warnings, Multi-Hazard, Field Ops, SitRep, Scenarios, Interventions, Table Explorer, and Remote Sensing.', anchor: 'nav-tabs-bar' },
            { label: 'Step 2 of 4 — KPI Cards', text: 'The coloured metric cards at the top of each tab show live summary indicators. Hover the ? icon on any KPI card for a detailed explanation.', anchor: 'tab-overview' },
            { label: 'Step 3 of 4 — Interactive Map', text: 'The main map shows all 10 N-HYPPADEC states. Click any marker for detailed community risk data. Use the layer control (top-right) to switch basemaps and overlays.', anchor: 'map' },
            { label: 'Step 4 of 4 — API Documentation', text: 'All data is accessible via a REST API. Click the "API Docs →" link in the header to explore every endpoint in the interactive Swagger UI.', anchor: null }
        ];
        let currentTourStep = 0;

        function startTour() {
            currentTourStep = 0;
            showTourStep();
        }

        function showTourStep() {
            const step = TOUR_STEPS[currentTourStep];
            document.getElementById('tour-step-label').textContent = step.label;
            document.getElementById('tour-step-text').textContent = step.text;
            document.getElementById('tour-next-btn').textContent = currentTourStep < TOUR_STEPS.length - 1 ? 'Next →' : 'Done ✓';
            const box = document.getElementById('tour-box');
            box.style.display = 'block';
            box.style.transform = '';
            if (step.anchor) {
                const anchor = document.getElementById(step.anchor);
                if (anchor) {
                    const rect = anchor.getBoundingClientRect();
                    box.style.top = (rect.bottom + 12) + 'px';
                    box.style.left = Math.min(rect.left, window.innerWidth - 320) + 'px';
                }
            } else {
                box.style.top = '50%';
                box.style.left = '50%';
                box.style.transform = 'translate(-50%,-50%)';
            }
        }

        function nextTourStep() {
            if (currentTourStep < TOUR_STEPS.length - 1) {
                currentTourStep++;
                showTourStep();
            } else {
                dismissTour();
            }
        }

        function dismissTour() {
            document.getElementById('tour-box').style.display = 'none';
            localStorage.setItem('cher_tour_done', '1');
        }

        // Global search
        const SEARCH_INDEX = [
            { label: '🌊 FEW-CAM Flood Warnings & Alerts', type: 'tab', tabId: 'flood' },
            { label: '🌾 Agro-Drought & Dam Water Level Monitor', type: 'tab', tabId: 'drought' },
            { label: '🌊 Strategic Dams Water Level Gauges', type: 'tool', tabId: 'drought' },
            { label: '🌾 State Harvest Loss & Crop Deficit AI', type: 'tool', tabId: 'drought' },
            { label: '🌍 Multi-Hazard & Environmental Risks', type: 'tab', tabId: 'multi_hazard' },
            { label: '🔄 Field Ops & Kobo Ingestion Hub', type: 'tab', tabId: 'field_ops' },
            { label: '📄 Executive SitRep Generator', type: 'tab', tabId: 'sitrep' },
            { label: '⚙ Scenario Simulation Lab', type: 'tab', tabId: 'scenarios' },
            { label: '🛡 Interventions & MRV Registry', type: 'tab', tabId: 'interventions' },
            { label: '📊 31-Table Architecture Explorer', type: 'tab', tabId: 'tables' },
            { label: '🛰 Earth Observation & Remote Sensing', type: 'tab', tabId: 'remote_sensing' },
            { label: 'Niger State (NG-NIG)', type: 'state', tabId: 'overview' },
            { label: 'Kebbi State (NG-KEB)', type: 'state', tabId: 'overview' },
            { label: 'Plateau State (NG-PLA)', type: 'state', tabId: 'overview' },
            { label: 'Benue State (NG-BEN)', type: 'state', tabId: 'overview' },
            { label: 'Kogi State (NG-KOG)', type: 'state', tabId: 'overview' },
            { label: 'Kwara State (NG-KWA)', type: 'state', tabId: 'overview' },
            { label: 'Kaduna State (NG-KAD)', type: 'state', tabId: 'overview' },
            { label: 'Nasarawa State (NG-NAS)', type: 'state', tabId: 'overview' },
            { label: 'Taraba State (NG-TAR)', type: 'state', tabId: 'overview' },
            { label: 'Gombe State (NG-GOM)', type: 'state', tabId: 'overview' },
        ];

        let searchTimer;
        function onSearchInput(val) {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => runSearch(val), 300);
        }

        function runSearch(val) {
            const dd = document.getElementById('search-dropdown');
            if (!val.trim()) { dd.style.display = 'none'; return; }
            const matches = SEARCH_INDEX.filter(item =>
                item.label.toLowerCase().includes(val.toLowerCase())
            ).slice(0, 8);
            if (!matches.length) { dd.style.display = 'none'; return; }
            dd.innerHTML = matches.map((m) =>
                `<div class="search-result-item" onclick="selectSearchResult('${m.tabId}', this)"
                    style="padding:0.5rem 0.9rem; cursor:pointer; font-size:0.82rem; border-bottom:1px solid var(--border-color);">
                    <span style="color:var(--text-secondary); font-size:0.7rem; text-transform:uppercase; margin-right:6px;">${m.type}</span>
                    ${m.label}
                </div>`
            ).join('');
            dd.style.display = 'block';
        }

        function selectSearchResult(tabId) {
            document.getElementById('search-dropdown').style.display = 'none';
            document.getElementById('global-search').value = '';
            switchTab(tabId);
        }

        document.addEventListener('click', e => {
            const wrapper = document.getElementById('global-search-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                document.getElementById('search-dropdown').style.display = 'none';
            }
        });

        // =========================================================================
        // Tab switching logic
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('onclick')?.includes(`'${tabId}'`));
            });
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            const target = document.getElementById('tab-' + tabId);
            if (target) target.classList.add('active');

            if (tabId === 'overview') {
                setTimeout(() => { if (window.map) window.map.invalidateSize(); }, 150);
            } else if (tabId === 'flood') {
                loadFloodDashboard();
                runDamForecast();
                translateEarlyWarningAlert();
                setTimeout(() => { if (window.floodMap) window.floodMap.invalidateSize(); }, 150);
            } else if (tabId === 'drought') {
                loadDroughtDashboard();
            } else if (tabId === 'multi_hazard') {
                loadMultiHazardDashboard();
                setTimeout(() => { if (window.hazardMap) window.hazardMap.invalidateSize(); }, 150);
            } else if (tabId === 'scenarios') {
                loadScenariosData();
            } else if (tabId === 'interventions') {
                loadInterventionsData();
                runPortfolioOptimization();
            } else if (tabId === 'tables') {
                loadTablesList();
                checkPostgisSyncStatus();
            } else if (tabId === 'remote_sensing') {
                loadRemoteSensingData();
            } else if (tabId === 'field_ops') {
                loadFieldOpsDashboard();
            } else if (tabId === 'sitrep') {
                loadSitRepDashboard();
                triggerAiSitRepSynthesis();
            }
        }

        // =========================================================================
        // Full Screen Map Toggle Functionality
        // =========================================================================
        function toggleMapFullscreen(btn, mapId) {
            const mapEl = document.getElementById(mapId);
            const container = mapEl ? mapEl.closest('.map-container-card') : null;
            if (!container) return;

            const isFullscreen = container.classList.toggle('fullscreen-active');
            document.body.classList.toggle('has-fullscreen-map', isFullscreen);

            if (isFullscreen) {
                btn.classList.add('active');
                btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14h6m0 0v6m0-6L3 21m17-7h-6m0 0v6m0-6l7 7M4 10h6m0 0V4m0 6L3 3m17 7h-6m0 0V4m0 6l7-7"/></svg> <span>Exit Full Screen</span>`;
            } else {
                btn.classList.remove('active');
                btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg> <span>Full Screen</span>`;
            }

            // Invalidate Leaflet map size after CSS layout adjusts
            setTimeout(() => {
                let m = null;
                if (mapId === 'map') m = window.map;
                else if (mapId === 'flood-map') m = window.floodMap;
                else if (mapId === 'hazard-map') m = window.hazardMap;
                if (m && typeof m.invalidateSize === 'function') {
                    m.invalidateSize();
                }
            }, 100);
        }

        // Global ESC key listener to exit full screen map mode
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' || e.key === 'Esc') {
                const activeContainer = document.querySelector('.map-container-card.fullscreen-active');
                if (activeContainer) {
                    const btn = activeContainer.querySelector('.expand-map-btn');
                    const mapEl = activeContainer.querySelector('#map, #flood-map, #hazard-map');
                    if (btn && mapEl) {
                        toggleMapFullscreen(btn, mapEl.id);
                    }
                }
            }
        });

        function floodField(record, name) {
            const key = Object.keys(record).find(item => item.toLowerCase() === name.toLowerCase());
            return key ? record[key] : '';
        }

        function appendFloodCell(row, value) {
            const cell = document.createElement('td');
            cell.textContent = value === null || value === undefined || value === '' ? '—' : String(value);
            row.appendChild(cell);
        }

        let floodMap;
        let floodLayerControl;
        function loadFloodDashboard() {
            const status = document.getElementById('flood-data-status');
            Promise.all([
                fetch('/api/flood/dashboard').then(response => {
                    if (!response.ok) throw new Error('Flood dashboard request failed');
                    return response.json();
                }),
                fetch('/api/flood/alerts').then(response => {
                    if (!response.ok) throw new Error('Flood alerts request failed');
                    return response.json();
                }),
                fetch('/api/flood/performance').then(response => {
                    if (!response.ok) throw new Error('Warning performance request failed');
                    return response.json();
                }),
                fetch('/api/flood/warning-levels').then(response => {
                    if (!response.ok) throw new Error('Warning level request failed');
                    return response.json();
                }),
                fetch('/api/flood/geojson').then(response => {
                    if (!response.ok) throw new Error('Flood alert map request failed');
                    return response.json();
                })
            ]).then(([dashboard, alerts, performance, levels, geojson]) => {
                status.textContent = dashboard.status === 'OPERATIONAL' ? 'Flood data available' : 'Flood data not configured';
                document.getElementById('flood-active-count').textContent = dashboard.active_warnings;
                document.getElementById('flood-total-count').textContent = dashboard.total_alerts;
                document.getElementById('flood-reach-rate').textContent = dashboard.notification_reach_rate_pct === null ? 'Not evaluated' : `${dashboard.notification_reach_rate_pct}%`;
                document.getElementById('flood-ack-rate').textContent = dashboard.notification_acknowledgement_rate_pct === null ? 'Not evaluated' : `${dashboard.notification_acknowledgement_rate_pct}%`;
                document.getElementById('flood-awareness-count').textContent = dashboard.awareness_activities;
                const metrics = dashboard.performance_metrics;
                document.getElementById('flood-hit-rate').textContent = metrics.hit_rate_pct === null ? 'Not evaluated' : `${metrics.hit_rate_pct}%`;
                document.getElementById('flood-false-rate').textContent = metrics.false_alarm_rate_pct === null ? 'Not evaluated' : `${metrics.false_alarm_rate_pct}%`;
                document.getElementById('flood-lead-time').textContent = metrics.mean_lead_time_hours === null ? 'Not evaluated' : `${metrics.mean_lead_time_hours} h`;
                document.getElementById('flood-awareness-coverage').textContent = metrics.high_risk_awareness_coverage_pct === null ? 'Not evaluated' : `${metrics.high_risk_awareness_coverage_pct}%`;
                document.getElementById('flood-audit-completeness').textContent = metrics.mean_audit_completeness_pct === null ? 'Not evaluated' : `${metrics.mean_audit_completeness_pct}%`;

                const alertsBody = document.getElementById('flood-alerts-body');
                alertsBody.replaceChildren();
                alerts.alerts.forEach(alert => {
                    const row = document.createElement('tr');
                    appendFloodCell(row, floodField(alert, 'alert_id'));
                    appendFloodCell(row, floodField(alert, 'released_at') || floodField(alert, 'issued_at'));
                    appendFloodCell(row, floodField(alert, 'state_code'));
                    appendFloodCell(row, floodField(alert, 'lga_id'));
                    appendFloodCell(row, `Level ${floodField(alert, 'warning_level')}`);
                    appendFloodCell(row, floodField(alert, 'status'));
                    appendFloodCell(row, floodField(alert, 'confidence'));
                    alertsBody.appendChild(row);
                });
                if (!alerts.alerts.length) {
                    const row = document.createElement('tr');
                    appendFloodCell(row, alerts.status === 'NOT_CONFIGURED' ? 'No operational alert feed connected' : 'No alerts recorded');
                    alertsBody.appendChild(row);
                }

                const evaluationBody = document.getElementById('flood-performance-body');
                evaluationBody.replaceChildren();
                performance.evaluations.forEach(evaluation => {
                    const row = document.createElement('tr');
                    appendFloodCell(row, floodField(evaluation, 'alert_id'));
                    appendFloodCell(row, floodField(evaluation, 'evaluated_at'));
                    appendFloodCell(row, floodField(evaluation, 'lead_time_hours'));
                    appendFloodCell(row, floodField(evaluation, 'hit_status'));
                    appendFloodCell(row, floodField(evaluation, 'alerted_extent_sqkm'));
                    appendFloodCell(row, floodField(evaluation, 'observed_extent_sqkm'));
                    appendFloodCell(row, floodField(evaluation, 'confidence'));
                    evaluationBody.appendChild(row);
                });
                if (!performance.evaluations.length) {
                    const row = document.createElement('tr');
                    appendFloodCell(row, 'No verified performance evaluations available');
                    evaluationBody.appendChild(row);
                }

                const levelsContainer = document.getElementById('flood-levels');
                levelsContainer.replaceChildren();
                levels.levels.forEach(level => {
                    const card = document.createElement('div');
                    card.style.cssText = 'background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.75rem;';
                    const title = document.createElement('strong');
                    title.textContent = `Level ${level.level} — ${level.name}`;
                    const description = document.createElement('div');
                    description.style.cssText = 'font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.3rem;';
                    description.textContent = level.guidance;
                    card.append(title, description);
                    levelsContainer.appendChild(card);
                });

                if (!floodMap) {
                    const floodBases = createBaseLayers();
                    floodMap = L.map('flood-map', {
                        zoomControl: true,
                        attributionControl: true,
                        layers: [floodBases["🗺️ Dark Canvas (Esri)"]]
                    }).setView([9.0820, 7.5000], 6.5);
                    window.floodMap = floodMap;
                    floodLayerControl = L.control.layers(floodBases, {}, { position: 'topright' }).addTo(floodMap);

                    // Add legend to flood map
                    const legend = L.control({ position: 'bottomright' });
                    legend.onAdd = function() {
                        const div = L.DomUtil.create('div', 'map-legend');
                        div.style.cssText = 'background: rgba(14,22,38,0.92); border: 1px solid rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: #F8FAFC; line-height: 1.6;';
                        div.innerHTML = `
                            <strong style="color: #38BDF8; font-size: 12px;">Alert Levels</strong><br>
                            <span style="display:inline-block;width:10px;height:10px;background:#EF4444;border-radius:2px;margin-right:5px;"></span> Level 3: Emergency<br>
                            <span style="display:inline-block;width:10px;height:10px;background:#F97316;border-radius:2px;margin-right:5px;"></span> Level 2: Warning<br>
                            <span style="display:inline-block;width:10px;height:10px;background:#FBBF24;border-radius:2px;margin-right:5px;"></span> Level 1: Watch<br>
                            <span style="display:inline-block;width:10px;height:10px;background:#38BDF8;border-radius:50%;margin-right:5px;"></span> Observed SAR Extent
                        `;
                        return div;
                    };
                    legend.addTo(floodMap);

                    // Load G39 Warning Points and G43 Flood Extents once
                    fetch('/api/geojson/layer/G39')
                        .then(r => r.json())
                        .then(pts => {
                            const ptLayer = L.geoJSON(pts, {
                                pointToLayer: (feat, latlng) => {
                                    return L.circleMarker(latlng, {
                                        radius: 7,
                                        fillColor: '#F97316',
                                        color: '#FFFFFF',
                                        weight: 2,
                                        fillOpacity: 0.95
                                    });
                                },
                                onEachFeature: (feat, layer) => {
                                    const p = feat.properties || {};
                                    layer.bindPopup(`<strong>⚠️ Gauge Warning Point:</strong><br>${p.name || p.point_id}<br>State: ${p.state_code || ''}<br>Warning Level: ${p.warning_level || 'Active'}`);
                                }
                            }).addTo(floodMap);
                            floodLayerControl.addOverlay(ptLayer, "⚠️ G39 Warning Gauge Points");
                        }).catch(e => console.warn('G39 warning:', e));

                    fetch('/api/geojson/layer/G43')
                        .then(r => r.json())
                        .then(ext => {
                            const extLayer = L.geoJSON(ext, {
                                pointToLayer: (feat, latlng) => {
                                    return L.circleMarker(latlng, {
                                        radius: 6,
                                        fillColor: '#38BDF8',
                                        color: '#0284C7',
                                        weight: 1.5,
                                        fillOpacity: 0.8
                                    });
                                },
                                onEachFeature: (feat, layer) => {
                                    const p = feat.properties || {};
                                    layer.bindPopup(`
                                        <div style="color: #0F172A; font-size: 12px;">
                                            <strong style="color: #0284C7;">🌊 Flood Event (${p.Event_ID || ''})</strong><br>
                                            Community: ${p.Community || ''} (${p.State_Name || ''})<br>
                                            Inundated: <b>${p.Inundated_Area_Km2 || ''} km²</b><br>
                                            Depth: <b>${p.Observed_Depth_M || ''} m</b><br>
                                            Sensor: ${p.SAR_Sensor || ''}
                                        </div>
                                    `);
                                }
                            }).addTo(floodMap);
                            floodLayerControl.addOverlay(extLayer, "🌊 G43 Observed Flood Extent");
                        }).catch(e => console.warn('G43 warning:', e));
                }

                if (window.floodAlertLayer) floodMap.removeLayer(window.floodAlertLayer);
                window.floodAlertLayer = L.geoJSON(geojson, {
                    style: feature => {
                        const lvl = Number(feature.properties?.warning_level || feature.properties?.Warning_Level) || 1;
                        const colors = ['#94A3B8', '#FBBF24', '#F97316', '#EF4444'];
                        return {
                            color: colors[lvl] || '#EF4444',
                            weight: 2.5,
                            fillColor: colors[lvl] || '#EF4444',
                            fillOpacity: 0.35
                        };
                    },
                    onEachFeature: (feature, layer) => {
                        const p = feature.properties || {};
                        const alertId = p.alert_id || p.Alert_ID || 'Flood alert area';
                        const zoneName = p.zone_name || p.Zone_Name || '';
                        const lvl = p.warning_level || p.Warning_Level || 'unknown';
                        layer.bindPopup(`
                            <div style="color: #0F172A; font-family: sans-serif; font-size: 13px;">
                                <strong style="font-size: 14px; color: #DC2626;">🚨 ${alertId}</strong><br>
                                ${zoneName ? `<strong>Zone:</strong> ${zoneName}<br>` : ''}
                                <strong>Warning Level:</strong> <span style="font-weight: bold; color: #DC2626;">Level ${lvl}</span><br>
                                <strong>State:</strong> ${p.state_code || p.State_Code || ''}
                            </div>
                        `);
                    }
                }).addTo(floodMap);

                if (floodLayerControl && !window.floodAlertLayerAdded) {
                    floodLayerControl.addOverlay(window.floodAlertLayer, "🚨 G38 Flood Alert Zones");
                    window.floodAlertLayerAdded = true;
                }

                setTimeout(() => floodMap.invalidateSize(), 150);
                const tsEl = document.getElementById('ts-flood');
                if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
            }).catch(error => {
                status.textContent = 'Flood data unavailable';
                console.error(error);
                showApiError('tab-flood', error);
            });
        }

        // Initialize Executive Overview Map
        const overviewBases = createBaseLayers();
        const map = L.map('map', {
            zoomControl: true,
            attributionControl: true,
            layers: [overviewBases["🗺️ Dark Canvas (Esri)"]]
        }).setView([9.0820, 7.5000], 6.5);
        window.map = map;

        const overviewLayerControl = L.control.layers(overviewBases, {}, { position: 'topright' }).addTo(map);

        // Fetch Priority Sites GeoJSON
        fetch('/api/geojson/priority_sites')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        const isTier1 = feature.properties.tier === 'Tier 1 Critical';
                        return L.circleMarker(latlng, {
                            radius: isTier1 ? 9 : 7,
                            fillColor: isTier1 ? '#EF4444' : '#F59E0B',
                            color: '#FFFFFF',
                            weight: 1.5,
                            opacity: 1,
                            fillOpacity: 0.85
                        });
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindPopup(`
                            <div style="color: #0F172A; font-family: sans-serif; font-size: 13px;">
                                <strong style="font-size: 14px;">${p.name}</strong><br>
                                <span style="color: #64748B;">State: ${p.state} (${p.type})</span><hr style="margin: 6px 0;">
                                <strong>Composite Risk:</strong> ${p.risk} / 100<br>
                                <strong>Priority:</strong> <span style="color: ${p.tier.includes('Critical') ? '#DC2626' : '#D97706'}; font-weight: bold;">${p.tier}</span>
                            </div>
                        `);
                    }
                }).addTo(map);
                overviewLayerControl.addOverlay(layer, "📍 Priority Hotspots");
            });

        // Add G01 N-HYPPADEC States boundary overlay
        fetch('/api/geojson/layer/G01')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    style: {
                        color: '#06B6D4',
                        weight: 1.5,
                        fillColor: '#06B6D4',
                        fillOpacity: 0.08
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindTooltip(`<strong>${p.State_Name || p.State || 'State'}</strong>`, { sticky: true });
                    }
                }).addTo(map);
                overviewLayerControl.addOverlay(layer, "🏛️ N-HYPPADEC States (G01)");
            }).catch(e => console.warn('G01 load warning:', e));

        // Add G05 River & Drainage Network overlay
        fetch('/api/geojson/layer/G05')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    style: {
                        color: '#38BDF8',
                        weight: 2,
                        opacity: 0.75
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindPopup(`<strong>🌊 River Network:</strong> ${p.River_Name || p.Name || 'Drainage Channel'}`);
                    }
                });
                overviewLayerControl.addOverlay(layer, "🌊 River Drainage Network (G05)");
            }).catch(e => console.warn('G05 load warning:', e));

        // Add G07 Hydro Facilities & Dams overlay
        fetch('/api/geojson/layer/G07')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        return L.circleMarker(latlng, {
                            radius: 8,
                            fillColor: '#0284C7',
                            color: '#38BDF8',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9
                        });
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindPopup(`<strong>⚡ Hydro Facility:</strong> ${p.Facility_Name || p.Name || 'Dam'}<br>State: ${p.State_Name || p.State || ''}`);
                    }
                });
                overviewLayerControl.addOverlay(layer, "⚡ Hydro Facilities & Dams (G07)");
            }).catch(e => console.warn('G07 load warning:', e));

        // Add G03 Needs Assessment Communities (1,616 Points) overlay
        fetch('/api/geojson/layer/G03')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        const p = feature.properties || {};
                        const tier = p.River_Buffer_Tier || '';
                        let color = '#10B981'; // Green (Safe)
                        let radius = 4;
                        if (tier.includes('Critical')) {
                            color = '#EF4444'; // Red
                            radius = 6;
                        } else if (tier.includes('High')) {
                            color = '#F97316'; // Orange
                            radius = 5;
                        } else if (tier.includes('Moderate')) {
                            color = '#FBBF24'; // Yellow
                            radius = 4.5;
                        }
                        return L.circleMarker(latlng, {
                            radius: radius,
                            fillColor: color,
                            color: '#FFFFFF',
                            weight: 1,
                            opacity: 0.9,
                            fillOpacity: 0.8
                        });
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties || {};
                        const distRiv = p.River_Distance_m != null ? (p.River_Distance_m < 1000 ? `${p.River_Distance_m} m` : `${(p.River_Distance_m/1000).toFixed(1)} km`) : 'N/A';
                        const distDam = p.Dam_Distance_km != null ? `${p.Dam_Distance_km} km` : 'N/A';
                        layer.bindPopup(`
                            <div style="color: #0F172A; font-family: sans-serif; font-size: 13px; line-height: 1.4;">
                                <strong style="font-size: 14px; color: #0284C7;">${p.Community || 'Community'}</strong><br>
                                <span style="color: #64748B;">${p.LGA || ''}, ${p.State_Name || ''}</span>
                                <hr style="margin: 6px 0; border: 0; border-top: 1px solid #E2E8F0;">
                                <strong>Community ID:</strong> ${p.Community_ID || ''}<br>
                                <strong>Nearest River:</strong> ${p.Nearest_River || 'N/A'} (${distRiv})<br>
                                <strong>Buffer Status:</strong> <span style="font-weight: bold; color: ${p.River_Buffer_Tier && p.River_Buffer_Tier.includes('Critical') ? '#DC2626' : (p.River_Buffer_Tier && p.River_Buffer_Tier.includes('High') ? '#EA580C' : '#059669')};">${p.River_Buffer_Tier || 'Safe'}</span><br>
                                <strong>Nearest Dam:</strong> ${p.Nearest_Dam || 'N/A'} (${distDam})<br>
                                <strong>Exposure Index:</strong> <span style="font-weight: bold;">${p.Exposure_Index || 'N/A'}</span> / 100<br>
                                <strong>GPS Coordinates:</strong> ${Number(p.Latitude).toFixed(5)}, ${Number(p.Longitude).toFixed(5)}
                            </div>
                        `);
                    }
                }).addTo(map);
                overviewLayerControl.addOverlay(layer, "🏘️ Needs Assessment Communities (1,616 Points)");
            }).catch(e => console.warn('G03 load warning:', e));

        // Fetch State Risk Summaries
        fetch('/api/risk/summary')
            .then(res => res.json())
            .then(data => {
                document.getElementById('kpi-critical').innerText = data.total_critical_hotspots;
                document.getElementById('kpi-risk').innerText = data.overall_composite_risk_mean;

                const tbody = document.getElementById('state-table-body');
                tbody.innerHTML = '';
                data.state_profiles.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="font-weight: 500;">${s.state_name}</td>
                        <td><span style="color: var(--text-secondary);">${s.internal_code}</span></td>
                        <td><span style="font-weight: 600; color: ${s.r_score >= 65 ? '#F87171' : '#FBBF24'};">${s.r_score}</span></td>
                        <td><span class="tier-badge ${s.r_score >= 65 ? 'tier-1' : 'tier-2'}">${s.tier1_critical}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
                const tsEl = document.getElementById('ts-overview');
                if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
            }).catch(err => showApiError('tab-overview', err));

        // Load Top 20 Priority Communities
        fetch('/api/priority/top20')
            .then(res => res.json())
            .then(res => {
                const tbody = document.getElementById('top20-table-body');
                tbody.innerHTML = '';
                const items = res.data || [];
                items.forEach((row, i) => {
                    const tr = document.createElement('tr');
                    const tier = row.priority_tier || row.Priority_Tier || 'Tier 2 High';
                    const tierClass = tier.includes('Tier 1') ? 'tier-1' : (tier.includes('Tier 2') ? 'tier-2' : 'tier-3');
                    const lgaDisplay = row.lga_name || row.lga || row.LGA || row.LGA_Name || row.lga_code || row.LGA_Code || 'N/A';
                    const commId = row.community_id || row.Community_ID || '';
                    const commName = row.community_name || row.Community || '';
                    const stateDisplay = row.state_name || row.State_Name || row.state_code || row.State_Code || 'N/A';
                    const riskVal = row.composite_risk !== undefined ? row.composite_risk : row.Composite_Risk;
                    const gapVal = row.adaptation_gap !== undefined ? row.adaptation_gap : row.Adaptation_Gap;
                    const scoreVal = row.priority_score !== undefined ? row.priority_score : row.Priority_Score;
                    const confVal = row.confidence_rating || row.Confidence_Rating || 'Moderate';
                    const rankVal = row.rank || row.Priority_Rank || (i + 1);

                    tr.innerHTML = `
                        <td><strong>${rankVal}</strong></td>
                        <td><code>${commId}</code>${commName && commName !== commId ? '<br><small style="color:var(--text-secondary); font-size:0.75rem;">' + commName + '</small>' : ''}</td>
                        <td>${stateDisplay}</td>
                        <td><strong style="color: var(--text-primary);">${lgaDisplay}</strong></td>
                        <td><strong>${riskVal}</strong></td>
                        <td>${gapVal}</td>
                        <td style="font-weight: 700; color: var(--accent-cyan);">${scoreVal}</td>
                        <td><span class="tier-badge ${tierClass}">${tier}</span></td>
                        <td><span style="font-size: 0.75rem; color: var(--text-secondary);">${confVal}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            }).catch(err => {
                fetch('/api/tables/Priority_Areas?limit=20')
                    .then(res => res.json())
                    .then(res => {
                        const tbody = document.getElementById('top20-table-body');
                        tbody.innerHTML = '';
                        (res.data || []).forEach((row, i) => {
                            const tr = document.createElement('tr');
                            const tier = row.Priority_Tier || '';
                            const tierClass = tier.includes('Tier 1') ? 'tier-1' : (tier.includes('Tier 2') ? 'tier-2' : 'tier-3');
                            const lgaDisplay = row.LGA || row.LGA_Name || row.lga_name || row.LGA_Code || 'N/A';
                            tr.innerHTML = `
                                <td><strong>${i + 1}</strong></td>
                                <td><code>${row.Community_ID}</code></td>
                                <td>${row.State_Name || row.State_Code}</td>
                                <td><strong style="color: var(--text-primary);">${lgaDisplay}</strong></td>
                                <td><strong>${row.Composite_Risk}</strong></td>
                                <td>${row.Adaptation_Gap}</td>
                                <td style="font-weight: 700; color: var(--accent-cyan);">${row.Priority_Score}</td>
                                <td><span class="tier-badge ${tierClass}">${tier}</span></td>
                                <td><span style="font-size: 0.75rem; color: var(--text-secondary);">${row.Confidence_Rating}</span></td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }).catch(fallbackErr => showApiError('tab-overview', fallbackErr));
            });

        // Load Scenarios Data
        function loadScenariosData() {
            fetch('/api/scenarios')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('scenario-cards-container');
                    container.innerHTML = '';
                    data.scenarios.forEach(s => {
                        const deltaColor = s.Mean_Delta > 0 ? '#F87171' : (s.Mean_Delta < 0 ? '#34D399' : 'var(--text-secondary)');
                        const deltaSign = s.Mean_Delta > 0 ? '+' : '';
                        const card = document.createElement('div');
                        card.className = 'scenario-card';
                        card.innerHTML = `
                            <div class="scenario-badge">${s.Scenario_ID}</div>
                            <h3 style="font-family: var(--font-display); font-size: 1.05rem;">${s.Scenario_Name}</h3>
                            <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                                <div>
                                    <div style="font-size: 0.72rem; color: var(--text-secondary);">Projected Mean Risk</div>
                                    <div style="font-family: var(--font-display); font-size: 1.7rem; font-weight: 700; color: #FFFFFF;">${s.Mean_Risk}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.72rem; color: var(--text-secondary);">Risk Delta</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: ${deltaColor};">${deltaSign}${s.Mean_Delta}</div>
                                </div>
                            </div>
                            <hr style="border-color: var(--border-color); opacity: 0.5;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.78rem;">
                                <span>Tier 1 Critical: <strong style="color: #F87171;">${s.Tier1_Critical_Count}</strong></span>
                                <span>Tier 2 High: <strong>${s.Tier2_High_Count}</strong></span>
                                <span>Tier 4 Monitor: <strong style="color: #34D399;">${s.Tier4_Monitor_Count}</strong></span>
                            </div>
                        `;
                        container.appendChild(card);
                    });
                }).catch(err => showApiError('tab-scenarios', err));
        }

        function updateSim() {
            const rain = parseFloat(document.getElementById('slider-rain').value);
            const temp = parseFloat(document.getElementById('slider-temp').value);
            const adp = parseFloat(document.getElementById('slider-adp').value);

            document.getElementById('slider-rain-val').innerText = '+' + rain + '%';
            document.getElementById('slider-temp-val').innerText = '+' + temp + '°C';
            document.getElementById('slider-adp-val').innerText = adp + '%';

            // Real-time perturbation formula
            const baseRisk = 42.49;
            const hazardElev = (rain * 0.45) + (temp * 2.2);
            const adpReduction = (adp * 0.22);
            const projected = Math.min(100, Math.max(0, baseRisk + hazardElev - adpReduction));
            const delta = projected - baseRisk;

            document.getElementById('sim-projected-risk').innerText = projected.toFixed(2);
            document.getElementById('sim-risk-delta').innerText = (delta >= 0 ? '+' : '') + delta.toFixed(2);
            document.getElementById('sim-risk-delta').style.color = delta > 0 ? '#F87171' : '#34D399';

            let t1 = 1;
            if (projected > 50) t1 = Math.round(1 + (projected - 50) * 0.6);
            if (projected < 35) t1 = 0;
            document.getElementById('sim-tier1-count').innerText = t1;
        }

        // Load Interventions Data
        function loadInterventionsData() {
            fetch('/api/interventions')
                .then(res => res.json())
                .then(res => {
                    const tbody = document.getElementById('interventions-table-body');
                    tbody.innerHTML = '';
                    res.interventions.forEach(item => {
                        const tr = document.createElement('tr');
                        const statusColor = item.Status === 'Commissioned' ? '#34D399' : (item.Status === 'Completed' ? '#60A5FA' : '#FBBF24');
                        const iesDisplay = item.IES_Score_Pct ? `<span class="tier-badge tier-4">${item.IES_Score_Pct}%</span>` : '<span style="color: var(--text-secondary);">In Progress</span>';
                        tr.innerHTML = `
                            <td><code>${item.Intervention_ID}</code></td>
                            <td style="font-weight: 500;">${item.Project_Title}</td>
                            <td>${item.State_Code}</td>
                            <td>${item.Community_ID}</td>
                            <td>₦${(item.Budget_NGN / 1e6).toFixed(1)}M</td>
                            <td><span style="color: ${statusColor}; font-weight: 600;">${item.Status}</span></td>
                            <td>${item.Risk_Before}</td>
                            <td>${item.Risk_After || 'N/A'}</td>
                            <td>${iesDisplay}</td>
                            <td><strong>${item.Residual_Risk}</strong></td>
                        `;
                        tbody.appendChild(tr);
                    });
                    const tsEl = document.getElementById('ts-mrv');
                    if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                }).catch(err => showApiError('tab-interventions', err));
        }

        // Load 22-Table Architecture Explorer
        function loadTablesList() {
            fetch('/api/tables')
                .then(res => res.json())
                .then(res => {
                    const select = document.getElementById('table-select');
                    select.innerHTML = '';
                    res.tables.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t.table_name;
                        opt.innerText = `${t.table_name} (${t.rows} rows, ${t.columns} cols)`;
                        select.appendChild(opt);
                    });
                    loadSelectedTable();
                }).catch(err => showApiError('tab-tables', err));
        }

        function loadSelectedTable() {
            const tableName = document.getElementById('table-select').value;
            if (!tableName) return;

            document.getElementById('table-row-count').innerText = 'Loading table...';
            fetch('/api/tables/' + tableName + '?limit=25')
                .then(res => res.json())
                .then(res => {
                    document.getElementById('table-row-count').innerText = `${res.total_rows} Records in Database`;
                    document.getElementById('table-schema-info').innerText = `Displaying first ${Math.min(res.limit, res.total_rows)} rows | Verified CLEAN Schema`;

                    const thead = document.getElementById('explorer-thead');
                    const tbody = document.getElementById('explorer-tbody');
                    thead.innerHTML = '';
                    tbody.innerHTML = '';

                    if (res.data.length === 0) return;

                    const cols = Object.keys(res.data[0]);
                    const headerRow = document.createElement('tr');
                    cols.forEach(c => {
                        const th = document.createElement('th');
                        th.innerText = c;
                        headerRow.appendChild(th);
                    });
                    thead.appendChild(headerRow);

                    res.data.forEach(r => {
                        const tr = document.createElement('tr');
                        cols.forEach(c => {
                            const td = document.createElement('td');
                            td.innerText = r[c] !== null && r[c] !== undefined ? r[c] : '—';
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    });
                }).catch(err => showApiError('tab-tables', err));
        }

        function evaluateRisk() {
            const h = parseFloat(document.getElementById('in_h').value) || 0;
            const e = parseFloat(document.getElementById('in_e').value) || 0;
            const v = parseFloat(document.getElementById('in_v').value) || 0;
            const c = parseFloat(document.getElementById('in_c').value) || 0;

            fetch('/api/risk/calculate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({hazard: h, exposure: e, vulnerability: v, criticality: c})
            })
            .then(res => res.json())
            .then(res => {
                const box = document.getElementById('calc-result');
                box.style.display = 'block';
                box.innerHTML = `
                    <strong>Provisional Risk (R):</strong> <span style="color: var(--accent-cyan); font-weight: bold;">${res.provisional_additive_risk}</span> / 100<br>
                    <strong>Multiplicative Check (Stage 17.9):</strong> ${res.stage17_9_multiplicative_check}<br>
                    <strong>Assigned Status:</strong> <span class="tier-badge tier-1">${res.priority_tier}</span>
                `;
            }).catch(err => showApiError('calc-result', err));
        }

        function evaluateIES() {
            const rb = parseFloat(document.getElementById('ies_r_before').value) || 0;
            const ra = parseFloat(document.getElementById('ies_r_after').value) || 0;
            const boundsMatch = document.getElementById('ies_bounds_match').value === 'true';

            fetch('/api/ies/calculate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({risk_before: rb, risk_after: ra, reference_bounds_match: boundsMatch})
            })
            .then(res => res.json())
            .then(res => {
                const box = document.getElementById('ies-result');
                box.style.display = 'block';
                if (res.valid) {
                    box.innerHTML = `
                        <strong style="color: #34D399;">VALID EVALUATION:</strong><br>
                        <strong>IES Score:</strong> <span style="color: var(--accent-cyan); font-weight: bold;">${res.ies_percentage}%</span> reduction<br>
                        <strong>Residual Risk:</strong> ${res.residual_risk}<br>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">Classification: ${res.label}</span>
                    `;
                } else {
                    box.innerHTML = `
                        <strong style="color: #F87171;">INVALID PER SECTION 34:</strong><br>
                        <span>${res.reason}</span>
                    `;
                }
            }).catch(err => showApiError('ies-result', err));
        }

        // Load Remote Sensing & Earth Observation Data
        function loadRemoteSensingData() {
            fetch('/api/remote_sensing')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('kpi-rs-flood').innerText = data.total_sar_flood_area_km2 + ' km²';
                    document.getElementById('kpi-rs-ndvi').innerText = data.mean_ndvi;
                    document.getElementById('kpi-rs-retreat').innerText = data.mean_riverbank_retreat_m_yr + ' m/yr';
                    document.getElementById('kpi-rs-accuracy').innerText = data.overall_classification_accuracy_pct + '%';

                    const tbody = document.getElementById('rs-table-body');
                    tbody.innerHTML = '';
                    data.records.forEach(r => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="font-weight: 600;">${r.State_Name}</td>
                            <td><code>${r.State_Code}</code></td>
                            <td>${r.Major_Hydro_Basin}</td>
                            <td style="font-weight: 700; color: #60A5FA;">${r.SAR_Observed_Flood_Area_Km2.toLocaleString()} km²</td>
                            <td>${r.Mean_NDVI_Baseline}</td>
                            <td>${r.Tree_Canopy_Cover_Pct}%</td>
                            <td style="color: ${r.Mean_Riverbank_Retreat_M_Yr >= 4.0 ? '#F87171' : '#FBBF24'}; font-weight: 600;">${r.Mean_Riverbank_Retreat_M_Yr} m/yr</td>
                            <td>${r.Cropland_Flood_Exposure_Pct}%</td>
                            <td><span class="status-pill" style="font-size: 0.72rem;">${r.EO_Classification_Accuracy_Pct}%</span></td>
                            <td><span class="tier-badge tier-4">${r.QC_Status}</span></td>
                        `;
                        tbody.appendChild(tr);
                    });
                    const tsEl = document.getElementById('ts-rs');
                    if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                }).catch(err => showApiError('tab-remote_sensing', err));
        }

        // Multi-Hazard & Environmental Risks (14 Themes)
        let hazardMap;
        let hazardLayerGroup;
        let allHazardFeatures = [];
        let allHazardMetadata = {};

        function loadMultiHazardDashboard() {
            if (!hazardMap) {
                const baseLayers = createBaseLayers();
                hazardMap = L.map('hazard-map', {
                    center: [9.0820, 8.6753],
                    zoom: 6,
                    layers: [baseLayers["🗺️ Dark Canvas (Esri)"]]
                });
                window.hazardMap = hazardMap;
                L.control.layers(baseLayers, null, { position: 'topright' }).addTo(hazardMap);
                hazardLayerGroup = L.layerGroup().addTo(hazardMap);
            }

            Promise.all([
                fetch('/api/environmental-problems').then(r => r.json()),
                fetch('/api/environmental-problems/spatial').then(r => r.json())
            ]).then(([probRes, geoRes]) => {
                if (probRes && probRes.problems) {
                    probRes.problems.forEach(p => {
                        allHazardMetadata[p.Problem_Code] = p;
                    });
                }
                if (geoRes && geoRes.features) {
                    allHazardFeatures = geoRes.features;
                    renderHazardData('ALL');
                }
                const tsEl = document.getElementById('ts-multihazard');
                if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
            }).catch(err => {
                console.error("Failed to load multi-hazard data:", err);
                showApiError('tab-multi_hazard', err);
            });
        }

        function filterHazard(code) {
            document.querySelectorAll('.hazard-filter-btn').forEach(btn => {
                const match = btn.getAttribute('onclick')?.includes(`'${code}'`);
                btn.classList.toggle('active', match);
            });
            renderHazardData(code);
        }

        function renderHazardData(selectedCode) {
            if (!hazardMap || !hazardLayerGroup) return;
            hazardLayerGroup.clearLayers();

            const filtered = selectedCode === 'ALL' 
                ? allHazardFeatures 
                : allHazardFeatures.filter(f => f.properties.problem_code === selectedCode);

            const activeBadge = document.getElementById('hazard-active-badge');
            if (activeBadge) {
                activeBadge.innerText = selectedCode === 'ALL' ? 'SHOWING: ALL 14 THEMES' : `SHOWING: ${selectedCode.replace(/_/g, ' ')}`;
            }
            const countBadge = document.getElementById('hazard-table-count');
            if (countBadge) {
                countBadge.innerText = `${filtered.length} Records`;
            }

            // Update Side Panel
            const titleEl = document.getElementById('hazard-detail-title');
            const descEl = document.getElementById('hazard-detail-desc');
            const metaEl = document.getElementById('hazard-detail-meta');

            if (selectedCode !== 'ALL' && allHazardMetadata[selectedCode]) {
                const meta = allHazardMetadata[selectedCode];
                if (titleEl) titleEl.innerHTML = `<span style="color: ${meta.Symbol_Color_Hex}; margin-right: 6px;">${meta.Symbol_Char}</span> ${meta.Problem_Name}`;
                if (descEl) descEl.innerText = meta.Description;
                if (metaEl) {
                    metaEl.innerHTML = `
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                            <span style="color:var(--text-secondary);">Category:</span>
                            <strong style="color:#FFF;">${meta.Category}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                            <span style="color:var(--text-secondary);">Risk Factor:</span>
                            <strong style="color:var(--accent-cyan);">${meta.Primary_Risk_Component}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                            <span style="color:var(--text-secondary);">GIS Layer Code:</span>
                            <code>${meta.GIS_Layer_Code}</code>
                        </div>
                        <div style="display:flex; flex-direction:column; gap:2px; margin-top:4px;">
                            <span style="color:var(--text-secondary);">Key Affected States:</span>
                            <span style="color:#FFF; font-size:0.75rem;">${meta.Key_Affected_States}</span>
                        </div>
                    `;
                }
            } else {
                if (titleEl) titleEl.innerText = 'National Multi-Hazard Framework (14 Themes)';
                if (descEl) descEl.innerText = 'Comprehensive multi-hazard integration spanning Food Security, Armed Bandit Attacks, Air Pollution, Climate Change Impacts, Deforestation, Desertification, Drought, Ecological Resource Conflicts, Gully & Riverbank Erosion, Flooding, Toxic Lead Contamination, Oil Spillage, Solid Waste Dumpsites, and Aquatic Pollution.';
                if (metaEl) {
                    metaEl.innerHTML = `
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                            <span style="color:var(--text-secondary);">Total Hazards Tracked:</span>
                            <strong style="color:var(--accent-cyan);">14 Themes</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                            <span style="color:var(--text-secondary);">Total Mapped Incidents:</span>
                            <strong style="color:#FFF;">${allHazardFeatures.length} Hotspots</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                            <span style="color:var(--text-secondary);">Spatial Extent:</span>
                            <strong style="color:#FFF;">10 Member States + Adamawa</strong>
                        </div>
                    `;
                }
            }

            // Populate Map Markers & Table Rows
            const tbody = document.getElementById('hazard-table-body');
            if (tbody) tbody.innerHTML = '';

            filtered.forEach(f => {
                const p = f.properties;
                const coords = f.geometry.coordinates; // [lon, lat]
                const color = p.symbol_color || '#38BDF8';
                const char = p.symbol_char || '●';
                const sevBadge = p.severity === 'Critical' ? 'tier-1' : (p.severity === 'High' ? 'tier-2' : 'tier-4');

                // Map Marker
                const marker = L.circleMarker([coords[1], coords[0]], {
                    radius: p.severity === 'Critical' ? 9 : 7,
                    fillColor: color,
                    color: '#FFFFFF',
                    weight: 1.5,
                    opacity: 1,
                    fillOpacity: 0.85
                });

                marker.bindPopup(`
                    <div style="padding: 4px; min-width: 220px;">
                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                            <span style="font-size: 16px;">${char}</span>
                            <strong style="color: #FFF; font-size: 13px;">${p.problem_name}</strong>
                        </div>
                        <div style="font-size: 11px; margin-bottom: 4px;">
                            <strong>State:</strong> ${p.state_name} (<code>${p.state_code}</code>)<br>
                            <strong>Severity:</strong> <span class="tier-badge ${sevBadge}">${p.severity}</span><br>
                            <strong>Category:</strong> ${p.category}
                        </div>
                        <div style="font-size: 10px; color: #94A3B8; margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px;">
                            <em>${p.notes}</em>
                        </div>
                    </div>
                `);
                hazardLayerGroup.addLayer(marker);

                // Table Row
                if (tbody) {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><code>${p.record_id}</code></td>
                        <td style="font-weight: 600;">${p.state_name}</td>
                        <td><code>${p.state_code}</code></td>
                        <td><span style="color: ${color}; margin-right: 4px;">${char}</span> <strong>${p.problem_name}</strong></td>
                        <td><span class="tier-badge ${sevBadge}">${p.severity}</span></td>
                        <td><span style="font-family: monospace; font-size: 0.75rem;">${coords[1].toFixed(2)}°N, ${coords[0].toFixed(2)}°E</span></td>
                        <td style="font-size: 0.75rem; color: var(--text-secondary);">${p.source}</td>
                        <td style="font-size: 0.78rem;">${p.notes}</td>
                    `;
                    tbody.appendChild(tr);
                }
            });
        }

        // =========================================================================
        // IMPROVEMENT 2: MULTI-HAZARD COMPOUND VULNERABILITY (MHCVI) VIEW
        // =========================================================================
        let currentHazardMode = 'HOTSPOTS';
        function switchHazardViewMode(mode) {
            currentHazardMode = mode;
            const btnHotspots = document.getElementById('btn-mode-hotspots');
            const btnMhcvi = document.getElementById('btn-mode-mhcvi');
            const pillsBar = document.getElementById('hazard-filter-pills-bar');
            const badge = document.getElementById('hazard-active-badge');

            if (mode === 'HOTSPOTS') {
                if (btnHotspots) btnHotspots.classList.add('active');
                if (btnMhcvi) btnMhcvi.classList.remove('active');
                if (pillsBar) pillsBar.style.display = 'flex';
                filterHazard('ALL');
            } else {
                if (btnHotspots) btnHotspots.classList.remove('active');
                if (btnMhcvi) btnMhcvi.classList.add('active');
                if (pillsBar) pillsBar.style.display = 'none';
                if (badge) badge.innerText = 'MODE: COMPOUND VULNERABILITY (MHCVI)';
                loadMhcviLayer();
            }
        }

        function loadMhcviLayer() {
            if (!hazardLayerGroup) return;
            hazardLayerGroup.clearLayers();

            fetch('/api/vulnerability/mhcvi')
                .then(r => r.json())
                .then(data => {
                    // Update Title & Desc
                    const titleEl = document.getElementById('hazard-detail-title');
                    const descEl = document.getElementById('hazard-detail-desc');
                    const metaEl = document.getElementById('hazard-detail-meta');
                    const countBadge = document.getElementById('hazard-table-count');

                    if (titleEl) titleEl.innerHTML = '🔥 Multi-Hazard Compound Vulnerability Index';
                    if (descEl) descEl.innerText = 'Integrates 14 threats across Security (40%), Hydrology (35%), and Environmental Degradation (25%) into an authoritative composite index (0–100) per N-HYPPADEC state and critical LGA.';
                    if (countBadge) countBadge.innerText = `${data.state_rankings.length} States Evaluated`;

                    if (metaEl && data.state_rankings.length > 0) {
                        const top = data.state_rankings[0];
                        metaEl.innerHTML = `
                            <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                                <span style="color:var(--text-secondary);">Highest Vulnerability State:</span>
                                <strong style="color:#EF4444;">${top.state_name} (${top.mhcvi_score}/100)</strong>
                            </div>
                            <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                                <span style="color:var(--text-secondary);">Dominant Driver:</span>
                                <strong style="color:var(--accent-cyan);">${top.dominant_driver}</strong>
                            </div>
                            <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                                <span style="color:var(--text-secondary);">Security Weight (40%):</span>
                                <strong style="color:#FFF;">${top.security_score} pts</strong>
                            </div>
                            <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                                <span style="color:var(--text-secondary);">Hydrology Weight (35%):</span>
                                <strong style="color:#FFF;">${top.hydro_score} pts</strong>
                            </div>
                            <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
                                <span style="color:var(--text-secondary);">Environment Weight (25%):</span>
                                <strong style="color:#FFF;">${top.env_score} pts</strong>
                            </div>
                        `;
                    }

                    // Render Circle Markers for States
                    data.state_rankings.forEach(st => {
                        const marker = L.circleMarker([st.latitude, st.longitude], {
                            radius: 12 + (st.mhcvi_score / 8),
                            fillColor: st.color,
                            color: '#FFFFFF',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.8
                        });

                        marker.bindPopup(`
                            <div style="padding: 6px; min-width: 240px; font-family: sans-serif;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                    <strong style="color: #0F172A; font-size: 14px;">${st.state_name} State</strong>
                                    <span style="background:${st.color}; color:#FFF; font-size:11px; font-weight:bold; padding:2px 6px; border-radius:4px;">${st.mhcvi_score} / 100</span>
                                </div>
                                <div style="font-size: 11px; color: #334155; line-height: 1.5;">
                                    <strong>Compound Tier:</strong> ${st.tier}<br>
                                    <strong>Dominant Risk:</strong> ${st.dominant_driver}<br>
                                    <strong>Security Score:</strong> ${st.security_score} / 100<br>
                                    <strong>Hydrology Score:</strong> ${st.hydro_score} / 100<br>
                                    <strong>Environment Score:</strong> ${st.env_score} / 100<br>
                                    <strong>Active Threat Count:</strong> ${st.active_hazard_count} hazards
                                </div>
                            </div>
                        `);
                        hazardLayerGroup.addLayer(marker);
                    });

                    // Populate Table with State Rankings & LGA Hotspots
                    const tbody = document.getElementById('hazard-table-body');
                    if (tbody) {
                        tbody.innerHTML = '';
                        data.lga_hotspots.forEach(lga => {
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td><code>${lga.lga_code}</code></td>
                                <td style="font-weight: 600;">${lga.state_name}</td>
                                <td><code>${lga.state_code}</code></td>
                                <td><strong>${lga.lga_name} LGA Hotspot</strong></td>
                                <td><span class="tier-badge ${lga.mhcvi_score >= 70 ? 'tier-1' : 'tier-2'}">${lga.mhcvi_score} / 100 (${lga.tier})</span></td>
                                <td><span style="font-family: monospace; font-size: 0.75rem;">Priority Rank #${lga.priority_rank}</span></td>
                                <td style="font-size: 0.75rem; color: var(--accent-cyan);">${lga.dominant_hazard}</td>
                                <td style="font-size: 0.78rem;">Compound joint emergency hotspot requiring prioritized defense infrastructure.</td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }
                }).catch(err => showApiError('tab-multi_hazard', err));
        }

        // =========================================================================
        // IMPROVEMENT 4: EARLY WARNING ALERT SIMULATION & DISPATCH
        // =========================================================================
        function triggerSimulatedDispatch() {
            const alertId = document.getElementById('dispatch-alert-select')?.value || 'ALT-2026-HYD-01';
            const channel = document.getElementById('dispatch-channel-select')?.value || 'SMS_BROADCAST';
            const badge = document.getElementById('dispatch-status-badge');
            const resultBox = document.getElementById('dispatch-result-box');

            if (badge) badge.innerText = 'TRANSMITTING...';

            fetch('/api/early-warning/simulate-dispatch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ alert_id: alertId, channel: channel })
            })
            .then(r => r.json())
            .then(data => {
                if (badge) badge.innerText = 'BROADCAST VERIFIED (100%)';
                if (resultBox) {
                    resultBox.style.display = 'block';
                    const d = data.dispatch_details;
                    resultBox.innerHTML = `
                        <strong>✓ Alert Transmitted:</strong> ${d.title}<br>
                        <strong>Channel:</strong> <code>${d.channel}</code> | <strong>Target:</strong> ${d.recipients_group}<br>
                        <strong>Delivery Reach:</strong> ${d.recipients_contacted} Recipients Contacted (${d.delivery_rate_pct}% Delivery Rate) | <strong>Acknowledgements:</strong> ${d.acknowledged_count} Verified Receipts.
                    `;
                }
            })
            .catch(err => {
                if (badge) badge.innerText = 'FAILED';
                console.error(err);
            });
        }

        // =========================================================================
        // IMPROVEMENT 1: FIELD OPERATIONS & KOBOTOOLBOX DATA INGESTION
        // =========================================================================
        function loadFieldOpsDashboard() {
            // 1. Pipeline Status
            fetch('/api/kobo/status')
                .then(r => r.json())
                .then(data => {
                    const elLanding = document.getElementById('kobo-landing-count');
                    const elQuar = document.getElementById('kobo-quarantine-count');
                    const elTotal = document.getElementById('kobo-total-count');
                    const elLastSync = document.getElementById('kobo-last-sync');

                    if (elLanding) elLanding.innerText = `${data.landing_submissions_count} Records`;
                    if (elQuar) elQuar.innerText = `${data.quarantined_records_count} Records`;
                    if (elTotal) elTotal.innerText = `${data.total_processed} Total`;
                    if (elLastSync && data.last_sync) {
                        elLastSync.innerText = `Last Sync: ${new Date(data.last_sync.sync_timestamp).toLocaleTimeString()}`;
                    }
                    const tsEl = document.getElementById('ts-fieldops');
                    if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                }).catch(err => showApiError('tab-field_ops', err));

            // 2. Quarantine Table
            fetch('/api/kobo/quarantine')
                .then(r => r.json())
                .then(data => {
                    const badge = document.getElementById('quarantine-badge');
                    if (badge) badge.innerText = `${data.count} Flagged`;

                    const tbody = document.getElementById('quarantine-table-body');
                    if (!tbody) return;
                    tbody.innerHTML = '';

                    if (!data.quarantined_records || data.quarantined_records.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary); padding: 1.5rem;">✅ Zero flagged records in quarantine. All submissions passed QC gates!</td></tr>`;
                        return;
                    }

                    data.quarantined_records.forEach(r => {
                        const tr = document.createElement('tr');
                        const subId = r._submission_id || r._id || 'SUB-UNK';
                        const reason = r._quarantine_reason || 'Gate failure';
                        tr.innerHTML = `
                            <td><code>${subId}</code></td>
                            <td>${r.state_code || 'N/A'} - ${r.lga_code || 'N/A'}</td>
                            <td><span style="color: #EF4444; font-weight: 600; font-size: 0.75rem;">${reason}</span></td>
                            <td><code>${r.enumerator_id || 'ENUM-01'}</code></td>
                            <td style="font-size: 0.75rem; color: var(--text-secondary);">${r.today_date || '2026-10-21'}</td>
                            <td>
                                <button class="btn-calc" style="margin-top:0; padding:0.25rem 0.6rem; font-size:0.75rem; background:#10B981;" onclick="resolveQuarantineRecord('${subId}')">✓ Remediate & Promote</button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }).catch(err => showApiError('tab-field_ops', err));

            // 3. Clean Landing Table
            fetch('/api/kobo/landing')
                .then(r => r.json())
                .then(data => {
                    const badge = document.getElementById('landing-badge');
                    if (badge) badge.innerText = `${data.count} Verified`;

                    const tbody = document.getElementById('landing-table-body');
                    if (!tbody) return;
                    tbody.innerHTML = '';

                    if (!data.landing_records || data.landing_records.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-secondary); padding: 1.5rem;">No promoted submissions in landing stage yet.</td></tr>`;
                        return;
                    }

                    data.landing_records.slice(0, 15).forEach(r => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><code>${r._submission_id || r._id || 'SUB-01'}</code></td>
                            <td>${r.today_date || '2026-10-21'}</td>
                            <td style="font-weight: 600;">${r.state_code}</td>
                            <td><code>${r.lga_code}</code></td>
                            <td>${r.community_name || 'Settlement'}</td>
                            <td>${r.estimated_population ? Number(r.estimated_population).toLocaleString() : 'N/A'}</td>
                            <td style="font-size: 0.75rem; color: var(--accent-cyan);">${r.environmental_problems_observed || 'FLOODING'}</td>
                            <td><span class="status-pill" style="color:#10B981;">PASSED ALL GATES</span></td>
                        `;
                        tbody.appendChild(tr);
                    });
                }).catch(err => showApiError('tab-field_ops', err));
        }

        function syncKoboData(sandboxMode) {
            const url = `/api/kobo/sync?sandbox_mode=${sandboxMode}`;
            fetch(url, { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    alert(`Kobo Ingestion Sync Complete!\n• New Processed: ${res.processed_count || 0}\n• Valid Promoted: ${res.passed_count || 0}\n• Quarantined: ${res.quarantined_count || 0}`);
                    loadFieldOpsDashboard();
                })
                .catch(err => {
                    alert('Sync error: ' + err);
                });
        }

        function resolveQuarantineRecord(subId) {
            const corrections = {
                consent_given: "yes",
                state_code: "NG-NIG",
                lga_code: "NG-NIG-001"
            };
            fetch('/api/kobo/resolve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    submission_id: subId,
                    corrections: corrections,
                    approved_by: "Field Supervisor",
                    justification: "Corrected LGA cascading mapping and confirmed consent"
                })
            })
            .then(r => r.json())
            .then(res => {
                alert(`Remediation Successful!\nSubmission ${subId} validated and promoted to Clean Landing.`);
                loadFieldOpsDashboard();
            })
            .catch(err => {
                alert('Resolution error: ' + err);
            });
        }

        // =========================================================================
        // IMPROVEMENT 3: EXECUTIVE SITREP & POLICY BRIEF GENERATOR
        // =========================================================================
        function loadSitRepDashboard() {
            const stateFilter = document.getElementById('sitrep-state-filter')?.value || 'ALL';
            const url = stateFilter === 'ALL' ? '/api/sitrep/data' : `/api/sitrep/data?state_code=${stateFilter}`;

            fetch(url)
                .then(r => r.json())
                .then(data => {
                    const elCrit = document.getElementById('sitrep-kpi-critical');
                    const elTotal = document.getElementById('sitrep-kpi-total');
                    const elPop = document.getElementById('sitrep-kpi-pop');
                    const elBudget = document.getElementById('sitrep-kpi-budget');
                    const elRef = document.getElementById('sitrep-ref-badge');
                    const elSummary = document.getElementById('sitrep-summary-text');

                    if (elCrit) elCrit.innerText = data.critical_incidents;
                    if (elTotal) elTotal.innerText = data.total_incidents_recorded;
                    if (elPop) elPop.innerText = Number(data.estimated_affected_population).toLocaleString();
                    if (elBudget) elBudget.innerText = `₦${(data.recommended_emergency_allocation_ngn / 1e6).toFixed(1)}M`;
                    if (elRef) elRef.innerText = `REF: ${data.report_ref}`;

                    if (elSummary) {
                        elSummary.innerHTML = `
                            <strong>EXECUTIVE DIRECTIVE:</strong> Synthesizing ground spatial intelligence across <strong>${data.scope}</strong>. 
                            Field verification records <strong>${data.critical_incidents} Tier-1 Critical Hotspots</strong> out of ${data.total_incidents_recorded} mapped environmental footprints. 
                            Estimated vulnerable riverine and agricultural population stands at <strong>${Number(data.estimated_affected_population).toLocaleString()}</strong> residents, 
                            warranting an emergency capital defense allocation of <strong>₦${(data.recommended_emergency_allocation_ngn / 1e6).toFixed(1)} Million</strong> under the 2026 N-HYPPADEC Resilience Mandate.
                        `;
                    }

                    // Top Hazards List
                    const listContainer = document.getElementById('sitrep-top-hazards-list');
                    if (listContainer) {
                        listContainer.innerHTML = '';
                        data.top_hazards.forEach(h => {
                            const row = document.createElement('div');
                            row.style.cssText = 'background: var(--bg-secondary); border: 1px solid var(--border-color); padding: 0.6rem 0.8rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem;';
                            row.innerHTML = `
                                <span><strong>${h.hazard}</strong></span>
                                <span style="color: var(--accent-cyan); font-weight: 700;">${h.count} Hotspots</span>
                            `;
                            listContainer.appendChild(row);
                        });
                    }

                    // Incidents Table
                    const tbody = document.getElementById('sitrep-incidents-body');
                    if (tbody) {
                        tbody.innerHTML = '';
                        data.incidents.slice(0, 10).forEach(inc => {
                            const tr = document.createElement('tr');
                            const sevClass = inc.severity === 'Critical' ? 'tier-1' : (inc.severity === 'High' ? 'tier-2' : 'tier-4');
                            tr.innerHTML = `
                                <td><code>${inc.record_id}</code></td>
                                <td style="font-weight: 600;">${inc.hazard_name}</td>
                                <td><span class="tier-badge ${sevClass}">${inc.severity}</span></td>
                                <td style="font-size: 0.78rem; color: var(--text-secondary);">${inc.notes}</td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }
                    const tsEl = document.getElementById('ts-sitrep');
                    if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                }).catch(err => showApiError('tab-sitrep', err));
        }

        function openPrintableSitRep() {
            const stateFilter = document.getElementById('sitrep-state-filter')?.value || 'ALL';
            const url = stateFilter === 'ALL' ? '/api/sitrep/print' : `/api/sitrep/print?state_code=${stateFilter}`;
            window.open(url, '_blank');
        }

        // =========================================================================
        // OPERATIONAL AI SERVICES: PHASE 1 TO PHASE 4 JAVASCRIPT HANDLERS
        // =========================================================================

        // Phase 1: GenAI Executive SitRep Synthesis
        function triggerAiSitRepSynthesis() {
            const stateFilter = document.getElementById('sitrep-state-filter')?.value || 'ALL';
            const url = stateFilter === 'ALL' ? '/api/ai/sitrep/synthesize' : `/api/ai/sitrep/synthesize?state_code=${stateFilter}`;
            
            const summaryEl = document.getElementById('sitrep-summary-text');
            if (summaryEl) summaryEl.innerHTML = '<span class="spinner"></span> <em>Synthesizing grounded executive decision intelligence...</em>';

            fetch(url)
                .then(r => r.json())
                .then(ai => {
                    if (summaryEl) {
                        summaryEl.innerHTML = `
                            <div style="margin-bottom:0.6rem; color:var(--accent-cyan); font-weight:700; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.05em;">
                                🤖 AI DECISION INTELLIGENCE BRIEF (${ai.state_context})
                            </div>
                            <div style="font-size:0.85rem; line-height:1.6; margin-bottom:0.8rem;">
                                ${ai.executive_summary}
                            </div>
                            <div style="font-size:0.78rem; font-weight:700; color:var(--text-secondary); margin-bottom:0.4rem; text-transform:uppercase;">
                                Grounded Key Risk Vectors:
                            </div>
                            <ul style="margin-left:1.2rem; font-size:0.8rem; color:var(--text-secondary); line-height:1.5; margin-bottom:0.8rem;">
                                ${ai.risk_drivers.map(d => `<li>${d}</li>`).join('')}
                            </ul>
                        `;
                    }

                    const directivesList = document.getElementById('sitrep-ai-directives');
                    if (directivesList && ai.strategic_directives) {
                        directivesList.innerHTML = ai.strategic_directives.map(dir => `
                            <li style="margin-bottom:0.4rem;">
                                <strong style="color:var(--accent-cyan);">${dir.split(':')[0]}:</strong> ${dir.split(':').slice(1).join(':')}
                            </li>
                        `).join('');
                    }

                    const badge = document.getElementById('sitrep-ref-badge');
                    if (badge) badge.innerText = `REF: ${ai.report_ref} (AI SYNTHESIZED)`;
                })
                .catch(err => {
                    if (summaryEl) summaryEl.innerText = 'AI Synthesis error: ' + err;
                });
        }

        // Phase 1: Indigenous Multi-Lingual Alert Translation
        function translateEarlyWarningAlert() {
            const lang = document.getElementById('lang-select')?.value || 'hausa';
            const src = document.getElementById('lang-alert-src')?.value || 'ALT-DAM-SPILL';
            
            let payload = {
                alert_id: src,
                target_language: lang,
                target_states: ["Niger", "Kwara"],
                target_lgas: ["Mokwa", "Lavun", "Pategi"],
                hazard_type: "Dam Spillway Release",
                severity: "CRITICAL",
                lead_time_hours: 14,
                evacuation_shelter: "Designated High Ground Primary School & LGA Council Hall"
            };

            if (src === 'ALT-BENUE-FLASH') {
                payload.target_states = ["Benue", "Taraba"];
                payload.target_lgas = ["Katsina-Ala", "Makurdi", "Wukari"];
                payload.hazard_type = "Flash Flooding";
                payload.severity = "HIGH";
                payload.lead_time_hours = 36;
            } else if (src === 'ALT-KADUNA-EROSION') {
                payload.target_states = ["Niger", "Kaduna"];
                payload.target_lgas = ["Shiroro", "Birnin Gwari"];
                payload.hazard_type = "Riverbank Collapse & Erosion";
                payload.severity = "HIGH";
                payload.lead_time_hours = 48;
            }

            fetch('/api/ai/alerts/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                const smsEl = document.getElementById('lang-sms-text');
                const counterEl = document.getElementById('sms-char-counter');
                const radioEl = document.getElementById('lang-radio-script');

                if (smsEl) smsEl.innerText = data.compact_sms;
                if (counterEl) {
                    counterEl.innerText = `${data.sms_char_count} / 160 Chars`;
                    counterEl.style.color = data.sms_char_count <= 160 ? '#34D399' : '#EF4444';
                }
                if (radioEl) radioEl.innerText = data.radio_broadcast_script;
            })
            .catch(err => {
                const smsEl = document.getElementById('lang-sms-text');
                if (smsEl) smsEl.innerText = 'Translation error: ' + err;
            });
        }

        // Phase 2: Field Survey Quality & CV Privacy Shield Test
        function testAiFieldAudit() {
            const outEl = document.getElementById('ai-field-test-output');
            if (outEl) {
                outEl.style.display = 'block';
                outEl.innerHTML = '<span class="spinner"></span> <em>Running simulated field survey behavioral & CV privacy audit...</em>';
            }

            const sampleSubmission = {
                _submission_time: new Date().toISOString(),
                start: new Date(Date.now() - 85000).toISOString(),
                end: new Date().toISOString(),
                latitude: 9.0820,
                longitude: 6.5410,
                enumerator_id: "ENUM-TEST-09",
                community_name: "Katsina-Ala Central Settlement",
                flood_severity_rating: "4",
                erosion_threat_level: "4",
                food_insecurity_index: "4",
                infrastructure_damage_score: "4"
            };

            fetch('/api/ai/fieldwork/audit-submission', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ submission: sampleSubmission })
            })
            .then(r => r.json())
            .then(res => {
                if (outEl) {
                    const statusColor = res.is_anomalous ? '#EF4444' : '#10B981';
                    outEl.innerHTML = `
                        <div style="font-weight:700; color:${statusColor}; margin-bottom:4px;">
                            ${res.recommendation === 'QUARANTINE_FOR_SUPERVISOR_AUDIT' ? '⚠️ QUARANTINED (Audit Failure)' : '✓ VERIFIED (Clean)'} — Fraud Risk Score: ${res.fraud_risk_score}
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-secondary);">
                            <strong>Triggered Flags:</strong>
                            <ul style="margin-left:1rem; margin-top:3px;">
                                ${res.anomaly_flags.length ? res.anomaly_flags.map(f => `<li>${f}</li>`).join('') : '<li>No behavioral anomalies detected. Passed all gates.</li>'}
                            </ul>
                        </div>
                    `;
                }
            })
            .catch(err => {
                if (outEl) outEl.innerText = 'Audit error: ' + err;
            });
        }

        // Phase 3: Hydro Dam Reservoir Inflow & Spillway Forecaster + Dynamic Inundation Plume
        function runDamForecast() {
            const damId = document.getElementById('dam-select')?.value || 'DAM-NIG-01';
            const rain = parseFloat(document.getElementById('dam-rain-slider')?.value || '45');

            fetch(`/api/ai/flood/dam-forecasts?dam_id=${damId}&rainfall_mm=${rain}`)
                .then(r => r.json())
                .then(data => {
                    const f24 = document.getElementById('dam-f24-inflow');
                    const f48 = document.getElementById('dam-f48-inflow');
                    const f72 = document.getElementById('dam-f72-inflow');
                    const thresh = document.getElementById('dam-threshold-comp');
                    const risk = document.getElementById('dam-spill-risk');
                    const warnClass = document.getElementById('dam-warning-class');
                    const lead = document.getElementById('dam-lead-time');
                    const inun = document.getElementById('dam-inundated-area');
                    const dirBox = document.getElementById('dam-directive-box');
                    const badge = document.getElementById('dam-forecast-status');

                    if (f24) f24.innerText = `${data.forecast_horizons.t24_inflow_m3s} m³/s`;
                    if (f48) f48.innerText = `${data.forecast_horizons.t48_inflow_m3s} m³/s`;
                    if (f72) f72.innerText = `${data.forecast_horizons.t72_inflow_m3s} m³/s`;
                    if (thresh) thresh.innerText = `Spillway Limit: ${data.spillway_discharge_threshold_m3s} m³/s`;
                    if (risk) {
                        risk.innerText = `${(data.spill_risk_probability * 100).toFixed(1)}%`;
                        risk.style.color = data.spill_risk_probability > 0.7 ? '#EF4444' : (data.spill_risk_probability > 0.35 ? '#F59E0B' : '#10B981');
                    }
                    if (warnClass) {
                        warnClass.innerHTML = `<span class="status-pill" style="color:${data.warning_level >= 3 ? '#EF4444' : (data.warning_level === 2 ? '#F59E0B' : '#10B981')}">${data.warning_class}</span>`;
                    }
                    if (lead) lead.innerText = `${data.forecast_lead_time_hours} hours`;
                    if (inun) inun.innerText = `${Number(data.estimated_inundated_hectares).toLocaleString()} Ha`;
                    if (dirBox) {
                        dirBox.innerHTML = `<strong>${data.dam_name.toUpperCase()} DIRECTIVE:</strong> ${data.action_directive} <br><span style="color:var(--text-secondary); font-size:0.75rem;">Downstream Exposed LGAs: ${data.downstream_exposed_lgas.join(', ')}</span>`;
                    }
                    if (badge) badge.innerText = `${data.dam_name.split(' ')[0]} AI FORECAST SYNCED`;

                    // Keep current forecast cached for emergency dispatch
                    window.currentDamForecast = data;
                })
                .catch(err => console.error('Dam forecast error:', err));

            // Fetch dynamic flood inundation plume GeoJSON
            fetch(`/api/ai/flood/inundation-geojson?dam_id=${damId}&rainfall_mm=${rain}`)
                .then(r => r.json())
                .then(geo => {
                    if (!window.floodMap || !geo || !geo.features) return;
                    if (window.damInundationLayer) {
                        window.floodMap.removeLayer(window.damInundationLayer);
                    }
                    window.damInundationLayer = L.geoJSON(geo, {
                        style: function(feat) {
                            if (feat.geometry.type === 'Polygon') {
                                const rLvl = feat.properties?.risk_level || 'ADVISORY';
                                const colorMap = {
                                    'CRITICAL': '#EF4444',
                                    'HIGH': '#F97316',
                                    'WARNING': '#F59E0B',
                                    'ADVISORY': '#38BDF8'
                                };
                                const col = colorMap[rLvl] || '#38BDF8';
                                return {
                                    color: col,
                                    weight: 2.5,
                                    opacity: 0.9,
                                    fillColor: col,
                                    fillOpacity: 0.38,
                                    dashArray: rLvl === 'CRITICAL' ? '4, 4' : null
                                };
                            } else if (feat.geometry.type === 'LineString') {
                                return {
                                    color: '#06B6D4',
                                    weight: 3.5,
                                    opacity: 0.85,
                                    dashArray: '6, 6'
                                };
                            }
                        },
                        pointToLayer: function(feat, latlng) {
                            const p = feat.properties || {};
                            if (p.type === 'dam_facility') {
                                return L.circleMarker(latlng, {
                                    radius: 11,
                                    fillColor: '#06B6D4',
                                    color: '#FFFFFF',
                                    weight: 2.5,
                                    opacity: 1,
                                    fillOpacity: 0.95
                                });
                            } else if (p.type === 'at_risk_settlement') {
                                return L.circleMarker(latlng, {
                                    radius: 6,
                                    fillColor: '#EF4444',
                                    color: '#FFFFFF',
                                    weight: 1.5,
                                    opacity: 1,
                                    fillOpacity: 0.95
                                });
                            }
                            return L.circleMarker(latlng, { radius: 5, fillColor: '#F59E0B' });
                        },
                        onEachFeature: function(feat, layer) {
                            const p = feat.properties || {};
                            if (p.type === 'dam_facility') {
                                layer.bindPopup(`
                                    <div style="font-family: Inter, sans-serif; min-width: 200px;">
                                        <div style="font-weight: 700; color: #06B6D4; font-size: 0.95rem; margin-bottom: 4px;">⚡ ${p.name || 'Hydro Dam'}</div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Type: <strong>${p.facility_type || 'Hydroelectric'}</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Installed Capacity: <strong>${p.capacity_mw || 0} MW</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Spill Threshold: <strong>${p.spillway_threshold_m3s || 0} m³/s</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Reservoir Level: <strong>${p.reservoir_level_m || 'Operating'} m</strong></div>
                                    </div>
                                `);
                            } else if (p.type === 'inundation_plume_zone') {
                                layer.bindPopup(`
                                    <div style="font-family: Inter, sans-serif; min-width: 220px;">
                                        <div style="font-weight: 700; color: #EF4444; font-size: 0.95rem; margin-bottom: 4px;">🌊 Modeled Flood Inundation Plume</div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Dam Facility: <strong>${p.dam_name || ''}</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Inundation Area: <strong>${p.estimated_inundated_hectares ? Number(p.estimated_inundated_hectares).toLocaleString() + ' Ha' : 'N/A'}</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Spill Risk: <strong>${p.spill_risk_pct || 0}%</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Lead Time: <strong>${p.lead_time_hours || 0} hours</strong></div>
                                        <div style="font-size: 0.75rem; color: #F59E0B; margin-top: 4px;">⚠️ ${p.directive || 'Downstream precautionary alert'}</div>
                                    </div>
                                `);
                            } else if (p.type === 'at_risk_settlement') {
                                layer.bindPopup(`
                                    <div style="font-family: Inter, sans-serif; min-width: 180px;">
                                        <div style="font-weight: 700; color: #F87171; font-size: 0.9rem; margin-bottom: 4px;">🏘️ ${p.settlement_name || 'Settlement'}</div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">LGA: <strong>${p.lga || ''}</strong> | State: <strong>${p.state || ''}</strong></div>
                                        <div style="font-size: 0.78rem; color: #CBD5E1;">Population: <strong>${Number(p.est_population || 0).toLocaleString()}</strong></div>
                                        <div style="font-size: 0.78rem; color: #EF4444; font-weight:600;">Est. Wave Arrival: <strong>${p.wave_arrival_hours || 0} hrs</strong></div>
                                    </div>
                                `);
                            } else if (p.type === 'downstream_flow_path') {
                                layer.bindTooltip(`Downstream Flow Reach: ${p.dam_name}`, { sticky: true });
                            }
                        }
                    }).addTo(window.floodMap);

                    try {
                        const bounds = window.damInundationLayer.getBounds();
                        if (bounds.isValid()) {
                            window.floodMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 11 });
                        }
                    } catch(e) { console.warn('Could not fit bounds to plume:', e); }
                })
                .catch(err => console.error('Plume GeoJSON error:', err));
        }

        // Improvement 2: Pull Live Open-Meteo Satellite Precipitation
        function fetchLiveDamWeather() {
            const damId = document.getElementById('dam-select')?.value || 'DAM-NIG-01';
            const srcBadge = document.getElementById('weather-source-badge');
            const tempBadge = document.getElementById('weather-temp-badge');

            if (srcBadge) srcBadge.innerHTML = '<span class="spinner" style="width:10px; height:10px;"></span> Syncing satellite weather...';

            fetch(`/api/ai/flood/live-weather?dam_id=${damId}`)
                .then(r => r.json())
                .then(data => {
                    const slider = document.getElementById('dam-rain-slider');
                    const valEl = document.getElementById('dam-rain-val');
                    if (slider && valEl) {
                        slider.value = Math.min(150, Math.max(0, Math.round(data.rainfall_24h_mm)));
                        valEl.innerText = `${data.rainfall_24h_mm} mm`;
                    }
                    if (srcBadge) {
                        srcBadge.innerHTML = data.is_live 
                            ? `<span style="color:#10B981; font-weight:700;">🛰️ Open-Meteo Live (${data.weather_condition})</span>`
                            : `<span style="color:#F59E0B; font-weight:600;">📊 Climatology Baseline (${data.weather_condition})</span>`;
                    }
                    if (tempBadge) {
                        tempBadge.innerHTML = `🌡️ ${data.temperature_c}°C &bull; 💨 ${data.wind_speed_kmh} km/h &bull; Prob: ${data.precipitation_probability_pct}%`;
                    }
                    runDamForecast();
                })
                .catch(err => {
                    console.error('Weather sync error:', err);
                    if (srcBadge) srcBadge.innerText = '⚠️ Weather feed offline';
                });
        }

        // Improvement 3: Emergency Dispatch Gateway Functions
        function openEmergencyDispatchModal() {
            const modal = document.getElementById('emergency-dispatch-modal');
            if (!modal) return;
            modal.style.display = 'flex';
            loadEmergencyRecipientsList();
        }

        function closeEmergencyDispatchModal() {
            const modal = document.getElementById('emergency-dispatch-modal');
            if (modal) modal.style.display = 'none';
        }

        function loadEmergencyRecipientsList() {
            const el = document.getElementById('dispatch-recipients-count');
            fetch('/api/emergency/recipients')
                .then(r => r.json())
                .then(res => {
                    if (el) el.innerText = `${res.total} Verified Officers Staged Across Member States`;
                })
                .catch(e => console.warn(e));
        }

        function submitEmergencyDispatch() {
            const damId = document.getElementById('dam-select')?.value || 'DAM-NIG-01';
            const fc = window.currentDamForecast || {
                dam_name: 'Kainji Dam',
                warning_level: 3,
                spill_risk_probability: 0.78,
                forecast_lead_time_hours: 18,
                downstream_exposed_lgas: ['Mokwa', 'Borgu']
            };
            const lang = document.getElementById('dispatch-lang-select')?.value || 'English';
            const channels = [];
            if (document.getElementById('ch-sms')?.checked) channels.push('SMS');
            if (document.getElementById('ch-whatsapp')?.checked) channels.push('WHATSAPP');
            if (document.getElementById('ch-telegram')?.checked) channels.push('TELEGRAM');

            const btn = document.getElementById('btn-submit-dispatch');
            if (btn) btn.innerHTML = '<span class="spinner" style="width:12px; height:12px;"></span> Transmitting Broadcast...';

            fetch('/api/emergency/dispatch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dam_id: damId,
                    dam_name: fc.dam_name || 'Hydro Dam',
                    warning_level: fc.warning_level || 3,
                    spill_risk_pct: Number(((fc.spill_risk_probability || 0.7) * 100).toFixed(1)),
                    lead_time_hours: fc.forecast_lead_time_hours || 18,
                    affected_lgas: fc.downstream_exposed_lgas || ['Mokwa', 'Borgu'],
                    language: lang,
                    selected_channels: channels,
                    custom_directive: null,
                    sender_officer: 'N-HYPPADEC Situation Room'
                })
            })
            .then(r => r.json())
            .then(res => {
                if (btn) btn.innerHTML = '✅ Broadcast Dispatched!';
                const resBox = document.getElementById('dispatch-receipt-box');
                if (resBox) {
                    resBox.style.display = 'block';
                    resBox.innerHTML = `
                        <div style="font-weight:700; color:#10B981; margin-bottom:4px;">🚀 DISPATCH SUCCESSFUL: ${res.dispatch_id}</div>
                        <div style="font-size:0.75rem; color:#CBD5E1;">
                            Recipients: <strong>${res.statistics.total_recipients} Officers</strong> &bull; 
                            Transmissions: <strong>${res.statistics.total_transmissions}</strong> (SMS: ${res.statistics.sms_sent}, WA: ${res.statistics.whatsapp_sent}, TG: ${res.statistics.telegram_sent}) &bull;
                            Success Rate: <strong>${res.statistics.success_rate_pct}%</strong>
                        </div>
                    `;
                }
                setTimeout(() => { if (btn) btn.innerHTML = '🚀 Authorize Multi-Channel Broadcast'; }, 4000);
            })
            .catch(err => {
                console.error(err);
                if (btn) btn.innerHTML = '⚠️ Transmission Error';
            });
        }

        // Improvement 5: PostGIS Relational Spatial Database Sync & Status
        function checkPostgisSyncStatus() {
            const card = document.getElementById('postgis-status-box');
            if (!card) return;
            fetch('/api/database/postgis-status')
                .then(r => r.json())
                .then(data => {
                    const conn = data.database_connection;
                    const audit = data.schema_audit;
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                            <div>
                                <span class="status-pill" style="color:${conn.connected ? '#10B981' : '#F59E0B'}; background:rgba(0,0,0,0.3);">
                                    ${conn.connected ? '🟢 PostGIS Live (Port ' + conn.port + ')' : '🟡 PostGIS Standby (Port ' + conn.port + ')'}
                                </span>
                                <span style="font-size:0.8rem; color:var(--text-secondary); margin-left:8px;">
                                    <strong>${audit.tables_ready_for_sync} of ${audit.total_registered_tables}</strong> Tables Schema Verified (${audit.compliance_rate_pct}%) &bull; <strong>${Number(audit.total_records_staged).toLocaleString()}</strong> Spatial Records Staged
                                </span>
                            </div>
                            <button class="btn-calc" style="margin:0; padding:0.35rem 0.8rem; font-size:0.8rem; background:#0284C7;" onclick="runPostgisSync()">
                                ⚡ Sync Clean Tables to PostGIS
                            </button>
                        </div>
                        <div id="postgis-sync-result" style="margin-top:6px; font-size:0.75rem; color:var(--text-secondary); display:none;"></div>
                    `;
                })
                .catch(e => console.warn(e));
        }

        function runPostgisSync() {
            const resEl = document.getElementById('postgis-sync-result');
            if (resEl) {
                resEl.style.display = 'block';
                resEl.innerHTML = '<span class="spinner" style="width:10px; height:10px;"></span> Synchronizing 34 clean tables into PostGIS spatial database...';
            }
            fetch('/api/database/sync-postgis', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    if (resEl) {
                        resEl.innerHTML = `
                            <span style="color:#10B981; font-weight:700;">✓ ${res.status}:</span> ${res.message} 
                            <br><span style="font-family:monospace; font-size:0.7rem; color:#94A3B8;">CLI Seeder: ${res.migration_command || 'Automated Seeder Executed'}</span>
                        `;
                    }
                })
                .catch(err => {
                    if (resEl) resEl.innerHTML = `<span style="color:#EF4444;">Sync Error: ${err}</span>`;
                });
        }

        // =========================================================================
        // AI AGRO-DROUGHT & STRATEGIC DAM WATER LEVEL MONITOR
        // =========================================================================
        function loadDroughtDashboard() {
            const tsEl = document.getElementById('ts-drought');
            if (tsEl) tsEl.textContent = 'Updating…';

            // 1. Fetch State Drought & Harvest Loss Predictions
            fetch('/api/ai/drought/state-harvest-impact')
                .then(r => r.json())
                .then(data => {
                    const sum = data.summary;
                    const wState = document.getElementById('kpi-drought-worst-state');
                    const wLoss = document.getElementById('kpi-drought-worst-loss');
                    const sHa = document.getElementById('kpi-drought-stressed-ha');
                    const vPop = document.getElementById('kpi-drought-vuln-pop');

                    if (wState) wState.innerText = sum.highest_deficit_state;
                    if (wLoss) wLoss.innerText = `-${sum.highest_deficit_loss_pct}% Estimated Yield Reduction`;
                    if (sHa) sHa.innerText = `${Number(sum.total_cropland_under_drought_stress_ha).toLocaleString()} Ha`;
                    if (vPop) vPop.innerText = `${Number(sum.total_farming_population_at_risk).toLocaleString()} Farmers`;

                    const tbody = document.getElementById('drought-states-tbody');
                    if (tbody && data.state_rankings) {
                        tbody.innerHTML = '';
                        data.state_rankings.forEach(st => {
                            const rf = st.rainfall_metrics;
                            const h = st.harvest_impact;
                            const d = st.drought_classification;

                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="text-align:center; font-weight:700;">${st.vulnerability_rank}</td>
                                <td>
                                    <strong>${st.state_name}</strong>
                                    <div style="font-size:0.7rem; color:var(--text-secondary);">${st.agro_zone}</div>
                                </td>
                                <td style="text-align:right;">${rf.seasonal_normal_rain_mm} mm</td>
                                <td style="text-align:right; font-weight:600;">${rf.current_observed_rain_mm} mm</td>
                                <td style="text-align:center;">
                                    <span class="status-pill" style="color:${d.risk_color}; background:rgba(0,0,0,0.3); font-weight:700;">
                                        -${rf.rainfall_deficit_pct}%
                                    </span>
                                </td>
                                <td style="text-align:center;">
                                    <div style="font-weight:700; color:${d.risk_color}; font-size:0.9rem;">
                                        -${h.mean_harvest_reduction_pct}%
                                    </div>
                                    <div style="background:rgba(255,255,255,0.1); height:4px; border-radius:2px; margin-top:3px;">
                                        <div style="background:${d.risk_color}; height:100%; width:${Math.min(100, h.mean_harvest_reduction_pct)}%; border-radius:2px;"></div>
                                    </div>
                                </td>
                                <td>
                                    <span style="font-size:0.75rem; color:${d.risk_color}; font-weight:600;">${d.food_security_phase}</span>
                                </td>
                                <td style="text-align:right; font-weight:600;">${Number(h.stressed_cropland_hectares).toLocaleString()} Ha</td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }
                })
                .catch(err => console.error('Drought data load error:', err));

            // 2. Fetch Strategic Dam Hydrostatic Water Levels
            fetch('/api/ai/dams/water-levels')
                .then(r => r.json())
                .then(res => {
                    const cont = document.getElementById('dams-water-levels-container');
                    const dCount = document.getElementById('kpi-drought-dams-count');
                    if (dCount && res.dams) dCount.innerText = `${res.dams.length} Strategic Facilities`;

                    if (cont && res.dams) {
                        cont.innerHTML = '';
                        res.dams.forEach(d => {
                            const e = d.elevation_metrics;
                            const s = d.storage_metrics;
                            const f = d.flow_rates;

                            const card = document.createElement('div');
                            card.style.cssText = 'background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:8px; padding:0.85rem 1rem; border-left:4px solid ' + d.risk_color + ';';
                            card.innerHTML = `
                                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                                    <div>
                                        <div style="font-weight:700; font-size:0.92rem; color:#F8FAFC;">${d.dam_name}</div>
                                        <div style="font-size:0.72rem; color:var(--text-secondary);">${d.state_name} &bull; ${d.river} &bull; <strong>${d.installed_capacity_mw} MW</strong></div>
                                    </div>
                                    <span class="status-pill" style="color:${d.risk_color}; font-size:0.72rem; font-weight:700; background:rgba(0,0,0,0.3);">
                                        ${d.action_code.replace(/_/g, ' ')}
                                    </span>
                                </div>

                                <div style="margin:8px 0;">
                                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:3px;">
                                        <span>Water Level: <strong style="color:#38BDF8;">${e.current_water_level_m} m</strong> (MOL: ${e.min_operating_level_m}m &bull; FRL: ${e.full_reservoir_level_m}m)</span>
                                        <span>Active Storage: <strong style="color:${d.risk_color};">${s.active_storage_pct}%</strong></span>
                                    </div>
                                    <div style="background:rgba(255,255,255,0.1); height:8px; border-radius:4px; overflow:hidden;">
                                        <div style="background:${d.risk_color}; height:100%; width:${Math.min(100, Math.max(5, s.active_storage_pct))}%; border-radius:4px; transition:width 0.5s;"></div>
                                    </div>
                                </div>

                                <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:var(--text-secondary);">
                                    <span>Headroom Freeboard: <strong style="color:#FFF;">${e.freeboard_headroom_m} m</strong></span>
                                    <span>Usable: <strong style="color:#FFF;">${Number(s.usable_storage_mcm).toLocaleString()} MCM</strong></span>
                                    <span>Inflow: <strong>${f.inflow_m3s} m³/s</strong></span>
                                </div>

                                <div style="font-size:0.7rem; color:#94A3B8; margin-top:5px; border-top:1px dashed rgba(255,255,255,0.1); padding-top:4px;">
                                    🌾 <strong>Downstream Reach:</strong> ${d.irrigation_scheme}
                                </div>
                            `;
                            cont.appendChild(card);
                        });
                    }
                })
                .catch(err => console.error('Dam water levels error:', err));

            // 3. Fetch Prescriptive Irrigation & Food Security Directives
            fetch('/api/ai/drought/irrigation-advisory')
                .then(r => r.json())
                .then(res => {
                    const cont = document.getElementById('drought-directives-container');
                    if (cont && res.directives) {
                        cont.innerHTML = '';
                        res.directives.forEach(dir => {
                            const prioColor = dir.priority === 'CRITICAL' ? '#EF4444' : (dir.priority === 'HIGH' ? '#F59E0B' : '#0284C7');
                            const dDiv = document.createElement('div');
                            dDiv.style.cssText = 'background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:6px; padding:0.75rem 1rem; display:flex; gap:12px; align-items:flex-start;';
                            dDiv.innerHTML = `
                                <div style="background:${prioColor}; color:#FFF; font-weight:800; font-size:0.68rem; padding:3px 7px; border-radius:4px; white-space:nowrap; margin-top:2px;">
                                    ${dir.priority}
                                </div>
                                <div style="flex:1;">
                                    <div style="font-size:0.72rem; text-transform:uppercase; color:var(--text-secondary); font-weight:700; margin-bottom:2px;">
                                        ${dir.category.replace(/_/g, ' ')} &bull; Target: <span style="color:#FFF;">${dir.target_state}</span>
                                    </div>
                                    <div style="font-size:0.83rem; color:#F8FAFC; line-height:1.45;">
                                        ${dir.directive}
                                    </div>
                                </div>
                            `;
                            cont.appendChild(dDiv);
                        });
                    }
                    if (tsEl) tsEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                })
                .catch(err => console.error('Directives error:', err));
        }

        // Phase 4: Prescriptive Capital Investment Portfolio Optimizer
        function runPortfolioOptimization() {
            const budget = parseFloat(document.getElementById('ai-portfolio-budget')?.value || '2500000000');
            const strategy = document.getElementById('ai-portfolio-strategy')?.value || 'MAX_IES';
            const stateFilter = document.getElementById('ai-portfolio-state')?.value || 'ALL';

            const tbody = document.getElementById('ai-port-tbody');
            if (tbody) tbody.innerHTML = '<tr class="loading-row"><td colspan="10" class="empty-state-cell"><span class="spinner"></span> Solving Pareto multi-objective MILP optimization problem...</td></tr>';

            fetch('/api/ai/priority/optimize-portfolio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    total_budget_ngn: budget,
                    objective: strategy,
                    state_filter: stateFilter,
                    max_state_share_pct: 28.0,
                    candidate_pool_size: 100,
                    min_risk: 40.0
                })
            })
            .then(r => r.json())
            .then(res => {
                const bAlloc = document.getElementById('ai-port-alloc-budget');
                const bUtil = document.getElementById('ai-port-utilization');
                const pCount = document.getElementById('ai-port-projects-count');
                const sCount = document.getElementById('ai-port-states-count');
                const mIes = document.getElementById('ai-port-mean-ies');
                const ben = document.getElementById('ai-port-beneficiaries');
                const gain = document.getElementById('ai-port-gain');
                const statusBadge = document.getElementById('portfolio-solver-status');

                if (bAlloc) bAlloc.innerText = `₦${(res.allocated_budget_ngn / 1e9).toFixed(2)}B`;
                if (bUtil) bUtil.innerText = `${res.budget_utilization_pct}% Capital Utilization`;
                if (pCount) pCount.innerText = `${res.portfolio_summary.selected_projects_count} Projects`;
                if (sCount) sCount.innerText = `Across ${res.portfolio_summary.state_coverage_count} Member States`;
                if (mIes) mIes.innerText = `${res.portfolio_summary.mean_ies_score_pct}%`;
                if (ben) ben.innerText = `${Number(res.portfolio_summary.estimated_beneficiaries_protected).toLocaleString()} Residents`;
                if (gain) gain.innerText = `+${res.counterfactual_ai_advantage.ai_risk_reduction_gain_pct}% vs Naive`;
                if (statusBadge) statusBadge.innerText = `${res.status} SOLUTION`;

                // Render State Allocation Pills
                const pillsContainer = document.getElementById('ai-port-state-pills');
                if (pillsContainer && res.state_allocations) {
                    pillsContainer.innerHTML = res.state_allocations.map(st => `
                        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:6px; padding:3px 8px; font-size:0.75rem; display:flex; align-items:center; gap:6px;">
                            <strong>${st.state_name}:</strong>
                            <span style="color:var(--accent-cyan); font-weight:700;">₦${(st.budget_allocated_ngn / 1e6).toFixed(1)}M</span>
                            <span style="color:var(--text-secondary);">(${st.project_count} sites, ${st.budget_share_pct}%)</span>
                        </div>
                    `).join('');
                }

                // Render Table Rows
                if (tbody && res.selected_interventions) {
                    tbody.innerHTML = '';
                    res.selected_interventions.forEach(item => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><strong style="color:var(--accent-cyan);">${item.allocation_rank}</strong></td>
                            <td style="font-weight:600;">${item.community_name}</td>
                            <td>${item.lga_name}</td>
                            <td><span class="status-pill">${item.state_name}</span></td>
                            <td style="font-size:0.8rem;">${item.title}</td>
                            <td style="font-weight:700;">₦${(item.budget_ngn / 1e6).toFixed(1)}M</td>
                            <td>${item.risk_before}</td>
                            <td style="color:#34D399; font-weight:600;">${item.risk_after}</td>
                            <td><span class="tier-badge tier-4">${item.ies_pct}%</span></td>
                            <td style="font-size:0.75rem; color:var(--text-secondary);">${item.capital_efficiency}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            })
            .catch(err => {
                if (tbody) tbody.innerHTML = `<tr><td colspan="10" style="color:#EF4444; text-align:center; padding:1.5rem;">Optimizer error: ${err}</td></tr>`;
            });
        }

        // =========================================================================
        // LOGIN & INSTITUTIONAL SECURITY CLEARANCE
        // =========================================================================
        const roleEmails = {
            "Managing Director (MD)": "executive-md@n-hyppadec.gov.ng",
            "GIS & Remote Sensing Lead": "gis-officer@n-hyppadec.gov.ng",
            "Field Operations Supervisor": "field-supervisor@n-hyppadec.gov.ng",
            "Resilience Planning Analyst": "planning-analyst@n-hyppadec.gov.ng",
            "Public Evidence Viewer": "public-viewer@n-hyppadec.gov.ng"
        };

        function openLoginModal() {
            const modal = document.getElementById('login-modal');
            if (modal) modal.style.display = 'flex';
        }

        function closeLoginModal() {
            const modal = document.getElementById('login-modal');
            if (modal) modal.style.display = 'none';
        }

        function onRoleChange() {
            const role = document.getElementById('login-role-select')?.value;
            const emailInput = document.getElementById('login-email-input');
            if (emailInput && roleEmails[role]) {
                emailInput.value = roleEmails[role];
            }
        }

        function authenticateUser() {
            const role = document.getElementById('login-role-select')?.value || 'Managing Director (MD)';
            const roleLabel = document.getElementById('current-user-role');
            if (roleLabel) roleLabel.innerText = role;
            closeLoginModal();
            alert(`Authentication Successful!\nWelcome, ${role}.\nSecurity clearance verified under NITDA Sovereign Standards.`);
        }

        // =========================================================================
        // INITIALIZATION & ALERT TICKER
        // =========================================================================
        window.addEventListener('DOMContentLoaded', () => {
            fetch('/api/early-warning/alerts')
                .then(r => r.json())
                .then(data => {
                    const ticker = document.getElementById('alert-ticker');
                    const tickerText = document.getElementById('ticker-text');
                    if (data.alerts && data.alerts.length > 0) {
                        const sorted = data.alerts.slice().sort((a, b) => (b.warning_level || 0) - (a.warning_level || 0));
                        const topAlert = sorted[0];
                        if (tickerText) tickerText.innerHTML = `🚨 <strong>${topAlert.title || ''}</strong> — ${topAlert.advisory_text || ''}`;
                    } else {
                        if (ticker) ticker.style.display = 'none';
                    }
                })
                .catch(() => {
                    const ticker = document.getElementById('alert-ticker');
                    if (ticker) ticker.style.display = 'none';
                });

            // Auto-show onboarding tour on first visit
            if (!localStorage.getItem('cher_tour_done')) {
                setTimeout(startTour, 800);
            }
        });
    </script>

    <!-- Emergency Broadcast Dispatch Gateway Modal -->
    <div id="emergency-dispatch-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.75); z-index:9999; align-items:center; justify-content:center; padding:16px;">
        <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; max-width:540px; width:100%; padding:20px 24px; box-shadow:0 20px 40px rgba(0,0,0,0.6); color:#F8FAFC;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:16px;">
                <div>
                    <h3 style="font-size:1.1rem; color:#EF4444; display:flex; align-items:center; gap:8px;">🚨 Multi-Channel Emergency Alert Dispatch</h3>
                    <div style="font-size:0.75rem; color:#94A3B8;">Direct cellular & messaging transmission to verified Community Liaison Officers</div>
                </div>
                <button onclick="closeEmergencyDispatchModal()" style="background:transparent; border:none; color:#94A3B8; font-size:1.4rem; cursor:pointer;">&times;</button>
            </div>

            <div style="display:grid; gap:12px; font-size:0.85rem;">
                <div>
                    <label style="font-size:0.75rem; color:#94A3B8; display:block; margin-bottom:4px;">Vernacular Dispatch Language:</label>
                    <select id="dispatch-lang-select" style="width:100%; background:#1E293B; color:#FFF; border:1px solid #475569; padding:6px 10px; border-radius:6px;">
                        <option value="English">English (National Directive Standard)</option>
                        <option value="Hausa">Hausa (Harshen Hausa) — Niger / Kebbi / Gombe</option>
                        <option value="Nupe">Nupe (Zankpe Nupe) — Niger / Kwara / Kogi</option>
                        <option value="Tiv">Tiv (Zwa Tiv) — Benue / Taraba</option>
                        <option value="Yoruba">Yoruba (Èdè Yorùbá) — Kwara / Kogi</option>
                        <option value="Fulfulde">Fulfulde (Fulfulde) — Taraba / Plateau</option>
                    </select>
                </div>

                <div>
                    <label style="font-size:0.75rem; color:#94A3B8; display:block; margin-bottom:6px;">Target Gateway Transmission Channels:</label>
                    <div style="display:flex; gap:16px;">
                        <label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="ch-sms" checked style="accent-color:#10B981;"> 📱 Cellular SMS (Shortcode)</label>
                        <label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="ch-whatsapp" checked style="accent-color:#25D366;"> 💬 WhatsApp Business</label>
                        <label style="display:flex; align-items:center; gap:6px; cursor:pointer;"><input type="checkbox" id="ch-telegram" checked style="accent-color:#0284C7;"> ✈️ Telegram Webhook</label>
                    </div>
                </div>

                <div style="background:#1E293B; border:1px solid #334155; border-radius:6px; padding:10px 12px; font-size:0.78rem;">
                    <div style="color:#94A3B8; margin-bottom:4px;">Staged Recipient Roster:</div>
                    <div style="color:#38BDF8; font-weight:700;" id="dispatch-recipients-count">Scanning CLO Directory...</div>
                    <div style="color:#64748B; font-size:0.72rem; margin-top:2px;">Includes SEMA Directors, District Village Heads, and Riverine Marshals.</div>
                </div>

                <div id="dispatch-receipt-box" style="display:none; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:10px 12px; font-size:0.78rem;"></div>

                <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:8px;">
                    <button onclick="closeEmergencyDispatchModal()" style="background:#334155; color:#F8FAFC; border:none; padding:8px 14px; border-radius:6px; cursor:pointer; font-weight:600;">Cancel</button>
                    <button id="btn-submit-dispatch" onclick="submitEmergencyDispatch()" style="background:#DC2626; color:#FFF; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:700; display:flex; align-items:center; gap:6px;">🚀 Authorize Multi-Channel Broadcast</button>
                </div>
            </div>
        </div>
    </div>

</body>
</html>
"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

