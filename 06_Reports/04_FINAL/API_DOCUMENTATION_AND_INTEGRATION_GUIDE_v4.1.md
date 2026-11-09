# CHER-CDSS API DOCUMENTATION & TECHNICAL INTEGRATION GUIDE
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System
### For the Ten N-HYPPADEC Member States of Nigeria
**Version:** 4.1 (Authoritative Baseline Release) | **Publication Date:** October 2026  
**Commissioning Agency:** National Hydroelectric Power Producing Areas Development Commission (N-HYPPADEC)  
**Standard:** International Institutional OpenAPI 3.1.0 Standard  
**Document Code:** `NHYPPADEC-CHER-CDSS-API-v4.1`  
**Base URL:** `http://localhost:8000` (Production Intranet / Cloud Gateway)

---

## 1. EXECUTIVE SUMMARY & ARCHITECTURAL MANDATE

The **CHER-CDSS Application Programming Interface (API)** serves as the high-throughput, machine-readable analytical backbone of the N-HYPPADEC Institutional Evidence System. Designed to eliminate data silos and manual reporting delays, the API exposes authoritative spatial models, live flood warning telemetry, composite risk simulations, and relational database records to:
1. Executive Decision Dashboards and Operation Centers.
2. Inter-agency emergency managers (NiMet, NIHSA, NEMA, SEMA).
3. International development partners (World Bank, African Development Bank, UNDP).
4. State GIS Desks across the ten member states (*Niger, Kebbi, Plateau, Benue, Kogi, Kwara, Kaduna, Nasarawa, Taraba, Gombe*).

The API conforms to **OpenAPI 3.1.0**, implements strict **Level 1–3 data governance controls**, and operates at **sub-second latency (<150ms)** on high-concurrency analytical queries.

---

## 2. API ARCHITECTURE & SECURITY PROTOCOLS

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                       CONSUMER APPLICATIONS                            │
   │  Web GIS Dashboard · Mobile Field Apps · Partner APIs · Python SDKs    │
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │ HTTPS / JSON / GeoJSON
   ┌───────────────────────────────────▼────────────────────────────────────┐
   │                    FASTAPI APPLICATION GATEWAY                         │
   │  CORS Middleware · Request Validation · Route Routing · Rate Limiting  │
   └──────────┬────────────────────────┬────────────────────────┬───────────┘
              │                        │                        │
   ┌──────────▼────────────┐┌──────────▼───────────┐┌───────────▼───────────┐
   │  ANALYTICAL ENGINES   ││  FEW-CAM FLOOD CORE  ││  31-TABLE EXPLORER    │
   │ - Risk Index Calc     ││ - Real-Time Alerts   ││ - SQLite / PostgreSQL│
   │ - IES Intervention    ││ - Gauge Telemetry    ││ - Level 3 PII Masking │
   │ - Scenario Simulator  ││ - SAR Flood Extent   ││ - Immutable Audit Log │
   └───────────────────────┘└──────────────────────┘└───────────────────────┘
```

### Security & Privacy Classification (Sections 8 & 34)
- **Level 1 (Public Analytics):** Fully open endpoints (`/api/health`, `/api/states`, `/api/indicators`, `/api/flood/alerts`, `/api/risk/summary`, `/api/geojson/*`).
- **Level 2 (Institutional Operational):** Restricted operational records requiring valid agency headers.
- **Level 3 (Confidential Microdata):** Household-level microdata (`DB02_Household_Survey`, GPS household coordinates) is automatically stripped and replaced with `[PROTECTED LEVEL 3]` masking. Surveyor biometric IDs and personal phone numbers are inaccessible via public API calls.

---

## 3. MASTER ENDPOINT DIRECTORY (28 ENDPOINTS ACROSS 10 TAGS)

| Method | Endpoint | Domain Tag | Description |
|:---|:---|:---|:---|
| `GET` | `/api/health` | 🏛️ Governance & Geography | System Health, Uptime & Governance Status |
| `GET` | `/api/states` | 🏛️ Governance & Geography | List Ten Statutory N-HYPPADEC Member States |
| `GET` | `/api/states/{state_code}/lgas` | 🏛️ Governance & Geography | Filter LGAs by Statutory State Code |
| `GET` | `/api/facilities` | 🏛️ Governance & Geography | Hydropower, Dams & Critical Infrastructure Assets |
| `GET` | `/api/climate_stations` | 🏛️ Governance & Geography | Hydro-Meteorological Climate Gauges & Stations |
| `GET` | `/api/indicators` | 📊 Indicators & Risk Models | Master Reference Indicators & Baseline Normalization Bounds |
| `GET` | `/api/risk/summary` | 📊 Indicators & Risk Models | State-Level Composite Risk Summary (`TABLE_State_Summaries`) |
| `POST` | `/api/risk/calculate` | 📊 Indicators & Risk Models | Execute Multi-Pillar Risk Formula ($R$ and $R_{mult}$) |
| `POST` | `/api/ies/calculate` | 📊 Indicators & Risk Models | Compute Intervention Effectiveness Score ($IES$) |
| `GET` | `/api/layers` | 🗺️ GIS & Spatial Services | Master 43-Layer GIS Spatial Layer Register |
| `GET` | `/api/geojson/priority_sites` | 🗺️ GIS & Spatial Services | Top Critical Hotspot Priority Sites GeoJSON (`G37`) |
| `GET` | `/api/geojson/layer/{layer_id}` | 🗺️ GIS & Spatial Services | Stream Master GIS Layer GeoJSON FeatureCollection |
| `GET` | `/api/flood/warning-levels` | 🌊 FEW-CAM Flood Early Warning | Statutory 4-Tier Warning Level Continuum & Thresholds |
| `GET` | `/api/flood/alerts` | 🌊 FEW-CAM Flood Early Warning | Active & Released Flood Bulletins Register |
| `GET` | `/api/flood/geojson` | 🌊 FEW-CAM Flood Early Warning | Spatial FEW-CAM Alert Zones GeoJSON (`G38`) |
| `GET` | `/api/flood/warning-points` | 🌊 FEW-CAM Flood Early Warning | Hydrological Warning Points & Gauge Sensors (`G39`) |
| `GET` | `/api/flood/extent` | 🌊 FEW-CAM Flood Early Warning | Recent Satellite Flood Inundation Footprints (`G43`) |
| `GET` | `/api/flood/performance` | 🌊 FEW-CAM Flood Early Warning | Early Warning Lead-Time & Accuracy Audit Log |
| `GET` | `/api/flood/dashboard` | 🌊 FEW-CAM Flood Early Warning | Operational KPI Rollup & Active Warning Counts |
| `GET` | `/api/scenarios` | ⚙️ Scenario Simulation Lab | Empirical Stage-21 Climate & Adaptation Scenarios |
| `GET` | `/api/interventions` | 🛡️ Interventions & MRV | Commissioned Engineering & Community Interventions |
| `GET` | `/api/mrv` | 🛡️ Interventions & MRV | Measurement, Reporting & Verification (MRV) Portfolio |
| `GET` | `/api/remote_sensing` | 🛰️ Earth Observation & RS | Sentinel-1 SAR Floods, NDVI & Riverbank Retreat |
| `GET` | `/api/food_security` | 🌾 Thematic Security | Agricultural Yield, Farmland Loss & Nutrition Fragility |
| `GET` | `/api/security_impacts` | 🌾 Thematic Security | Climate Displacement & Resource-Conflict Dynamics |
| `GET` | `/api/tables` | 🗄️ Core Database Model | List Section-32 Relational Tables (31 Datasets) |
| `GET` | `/api/tables/{table_name}` | 🗄️ Core Database Model | Inspect Table Schema & Data Dictionary Records |
| `GET` | `/` | 🖥️ Executive Management Web UI | Interactive Single-Page Web GIS Decision Portal |

---

## 4. DETAILED SPECIFICATION BY FUNCTIONAL DOMAIN

### 4.1 🏛️ Governance & Geography
Provides statutory administrative hierarchies, geographical classifications, and monitored infrastructure networks.

#### `GET /api/health`
- **Purpose:** Verifies operational readiness, database connectivity, and data version status.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "4.1",
  "framework": "CHER-CDSS",
  "data_status": "VALIDATED_AND_CORRECTED",
  "agency": "N-HYPPADEC",
  "governance_classification": "LEVEL 1 / LEVEL 3 ISOLATED"
}
```

#### `GET /api/states`
- **Purpose:** Returns the authoritative list of 10 N-HYPPADEC member states with capital cities and geopolitical zones.
- **Query Parameters:** None.
- **Response `200 OK`:**
```json
[
  {
    "state_code": "NG-NIG",
    "state_name": "Niger",
    "capital": "Minna",
    "zone": "North Central",
    "hydropower_corridor": true
  },
  ...
]
```

#### `GET /api/states/{state_code}/lgas`
- **Purpose:** Lists the Local Government Areas for a designated member state.
- **Path Parameters:**
  - `state_code` (*string, required*): ISO statutory code (e.g., `NG-NIG`, `NG-BEN`).
- **Response `200 OK`:** Array of LGA strings (e.g., `["Shiroro", "Mokwa", "Borgu", "Lavun", ...]`).

---

### 4.2 📊 Indicators & Risk Models
Implements the core four-pillar institutional mathematical formulation specified in the CHER-CDSS Master Scaffold.

#### Master Risk Formulas:
1. **Additive Multi-Criteria Index ($R$):**
   $$R = 0.35H + 0.25E + 0.25V + 0.15C$$
   Where $H$ = Hazard, $E$ = Exposure, $V$ = Vulnerability, $C$ = Criticality (all scaled strictly $0.0 \le \text{Score} \le 100.0$).
2. **Multiplicative Integrity Check ($R_{\text{mult}}$):**
   $$R_{\text{mult}} = H^{0.35} \times E^{0.25} \times V^{0.25} \times C^{0.15}$$
   *Exposure Axiom:* If $E = 0$, then $R_{\text{mult}} \equiv 0.0$.
3. **Intervention Effectiveness Score ($IES$):**
   $$IES = \frac{R_{\text{before}} - R_{\text{after}}}{R_{\text{before}}} \times 100\%$$

#### `POST /api/risk/calculate`
- **Request Body:**
```json
{
  "hazard": 75.4,
  "exposure": 62.1,
  "vulnerability": 58.9,
  "criticality": 80.0
}
```
- **Response `200 OK`:**
```json
{
  "composite_risk": 68.64,
  "multiplicative_risk": 68.12,
  "risk_tier": "Tier 1 Critical",
  "action_guidance": "Immediate capital intervention and structural emergency response required.",
  "weights": {
    "hazard": 0.35,
    "exposure": 0.25,
    "vulnerability": 0.25,
    "criticality": 0.15
  }
}
```

#### `POST /api/ies/calculate`
- **Request Body:**
```json
{
  "risk_before": 72.5,
  "risk_after": 45.2,
  "reference_bounds_match": true
}
```
- **Response `200 OK`:**
```json
{
  "valid": true,
  "ies_percentage": 37.66,
  "residual_risk": 45.2,
  "label": "High Impact (>25% risk reduction)",
  "formula": "IES = (R_before - R_after) / R_before * 100"
}
```

---

### 4.3 🌊 FEW-CAM Flood Early Warning Architecture
Automates the Flood Early Warning Community Action Mechanism across 4 operational warning tiers.

| Warning Level | Color Code | Statutory Threshold | Required Operational Action |
|:---|:---|:---|:---|
| **Level 0: Routine** | `#10B981` (Green) | Gauge < 60% bankfull | Routine hydrological logging |
| **Level 1: Watch** | `#F59E0B` (Amber) | Gauge 60%–75% bankfull | Community focal points alerted |
| **Level 2: Warning** | `#F97316` (Orange) | Gauge 75%–90% bankfull | Evacuation corridors staged; asset protection |
| **Level 3: Emergency** | `#EF4444` (Red) | Gauge > 90% or spillway open | Immediate mandatory evacuation |

#### `GET /api/flood/alerts`
- **Query Parameters:**
  - `state_code` (*string, optional*): e.g. `NG-NIG`.
  - `lga_id` (*string, optional*): Filter by LGA.
- **Response `200 OK`:**
```json
{
  "total_alerts": 12,
  "alerts": [
    {
      "Alert_ID": "ALT-2026-NIG-001",
      "State_Code": "NG-NIG",
      "LGA_Name": "Mokwa",
      "Warning_Level": "Level 2 Warning",
      "Trigger_Condition": "Jebba pulse release + 48hr heavy convective precipitation",
      "Lead_Time_Hours": 36,
      "Status": "Released",
      "Issued_Timestamp": "2026-10-10T08:00:00Z"
    }
  ]
}
```

#### `GET /api/flood/geojson`
- **Purpose:** Serves spatial Polygon GeoJSON features representing FEW-CAM active risk corridors (`G38`).
- **Response `200 OK`:** Valid GeoJSON `FeatureCollection` (RFC 7946).

---

### 4.4 🗺️ GIS & Spatial Services
Provides streaming access to all 43 registered GIS layers in standard WGS84 coordinates.

#### `GET /api/layers`
- **Response `200 OK`:** Array of layer metadata objects containing `layer_id`, `layer_name`, `geometry`, `category`, and `clean_file`.

#### `GET /api/geojson/layer/{layer_id}`
- **Path Parameters:**
  - `layer_id` (*string, required*): Registered GIS layer identifier (e.g., `G01`, `G02`, `G03`, `G38`, `G39`, `G43`).
- **Response `200 OK`:** Raw GeoJSON FeatureCollection stream.
- **Error `404 Not Found`:** Returned when the layer ID does not match any registered asset.

---

### 4.5 🗄️ Core Database Model (31 Relational Tables)
Enables structural introspection and record querying across all Section-32 clean relational datasets.

#### `GET /api/tables`
- **Response `200 OK`:**
```json
{
  "total_tables": 31,
  "tables": [
    {"table_name": "DB01_Community_Master", "display_name": "Community Master", "row_count": 50, "category": "Administrative"},
    {"table_name": "DB02_Household_Survey", "display_name": "Household Socioeconomic Survey", "row_count": 1200, "category": "Socioeconomic"},
    ...
  ]
}
```

#### `GET /api/tables/{table_name}`
- **Path Parameters:**
  - `table_name` (*string, required*): Table identifier (e.g. `DB01_Community_Master`, `DB12_Hydropower_Facilities`).
- **Query Parameters:**
  - `limit` (*integer, optional, default=50, max=500*): Number of records.
- **Privacy Protections:**
  - If `table_name` matches household survey datasets, Level 3 PII columns (`respondent_name`, `phone`, `exact_gps`) are masked automatically.

---

## 5. CLIENT INTEGRATION EXAMPLES

### Python 3 Integration Example
```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Health check
health = requests.get(f"{BASE_URL}/api/health").json()
print("System Status:", health["status"], "| Version:", health["version"])

# 2. Compute Composite Risk Score
payload = {
    "hazard": 65.5,
    "exposure": 45.0,
    "vulnerability": 70.0,
    "criticality": 55.0
}
res = requests.post(f"{BASE_URL}/api/risk/calculate", json=payload).json()
print(f"Risk Score: {res['composite_risk']} ({res['risk_tier']})")
print("Guidance:", res["action_guidance"])

# 3. Stream FEW-CAM Alert Corridors GeoJSON
geojson = requests.get(f"{BASE_URL}/api/flood/geojson").json()
print("Loaded GeoJSON features:", len(geojson.get("features", [])))
```

### JavaScript / Leaflet Integration Example
```javascript
// Fetch active FEW-CAM warning corridors and add to Leaflet map
async function loadFloodCorridors(map) {
    try {
        const response = await fetch('http://localhost:8000/api/flood/geojson');
        const data = await response.json();
        
        L.geoJSON(data, {
            style: function(feature) {
                return {
                    color: '#EF4444',
                    weight: 2,
                    fillColor: '#F87171',
                    fillOpacity: 0.35
                };
            },
            onEachFeature: function(feature, layer) {
                layer.bindPopup(`
                    <strong>${feature.properties.Zone_Name || 'Flood Zone'}</strong><br>
                    State: ${feature.properties.State || 'N/A'}<br>
                    Risk Level: ${feature.properties.Warning_Level || 'Critical'}
                `);
            }
        }).addTo(map);
    } catch (err) {
        console.error('Failed to load FEW-CAM GeoJSON:', err);
    }
}
```

### cURL Quick Verification
```bash
# Verify system status
curl -X GET "http://localhost:8000/api/health" -H "Accept: application/json"

# Evaluate Intervention Effectiveness Score (IES)
curl -X POST "http://localhost:8000/api/ies/calculate" \
     -H "Content-Type: application/json" \
     -d '{"risk_before": 68.4, "risk_after": 42.1, "reference_bounds_match": true}'
```

---

## 6. HTTP STATUS CODES & ERROR RESPONSES

| Code | Status | Meaning & Resolution |
|:---|:---|:---|
| `200` | `OK` | Request succeeded. Response body contains requested JSON/GeoJSON. |
| `400` | `Bad Request` | Validation failure. Check numeric ranges ($0.0 \le x \le 100.0$) and required fields. |
| `404` | `Not Found` | Specified state code, layer ID, or table name does not exist. |
| `422` | `Unprocessable Entity` | Pydantic JSON schema mismatch. Verify parameter naming and types. |
| `500` | `Internal Server Error` | Backend file read failure. Contact N-HYPPADEC Data Support Desk. |

---

## 7. MAINTENANCE, AUDITABILITY & SERVICE LEVEL OBJECTIVES (SLOs)

- **Availability SLO:** $99.9\%$ operational uptime.
- **Latency SLO:** 95th percentile response time $< 150\text{ ms}$ for analytical calls; $< 300\text{ ms}$ for GIS GeoJSON streams.
- **Auditability:** Every schema table contains `created_at`, `updated_at`, `created_by`, and `qc_flag` fields conforming to Section 34 audit standards.
- **Interactive Documentation:**
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc Portal: `http://localhost:8000/redoc`
  - Raw OpenAPI JSON: `http://localhost:8000/openapi.json`

---
*Authoritative API Specification — Certified for Institutional Integration.*  
*National Hydroelectric Power Producing Areas Development Commission (N-HYPPADEC) © 2026*
