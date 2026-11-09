# Climate–Hydropower–Erosion–Community Resilience Decision-Support System
## N-HYPPADEC / CHER-CDSS | Ten States of Nigeria

**Baseline:** 2026 | **Specification:** Advanced Master Implementation Scaffold v4.1 (October 2026) | **Build Status:** ✅ ALL PHASES COMPLETE & v4.1 VALIDATED

**FEW-CAM addendum:** The flood early-warning, alarm and community-awareness scaffold is implemented in the schema, dashboard, field form and GIS register. It is not an operational warning service until feeds, thresholds, authorities, user roles and pilot acceptance are approved.

---

## 1. System Purpose

A version-controlled, spatially enabled, longitudinal evidence and decision-support system integrating climate, hydrology, hydropower, flood, erosion, infrastructure, household, community, vulnerability, resilience and adaptation data for the ten N-HYPPADEC states of Nigeria.

### Ten Confirmed N-HYPPADEC Member States (Section 2)
| Permanent State Code | Entity ID Prefix | State Name | Geopolitical Zone | Capital |
|---|---|---|---|---|
| **NIG** | `NG-NIG-` | Niger | North Central | Minna |
| **KEB** | `NG-KEB-` | Kebbi | North West | Birnin Kebbi |
| **PLA** | `NG-PLA-` | Plateau | North Central | Jos |
| **BEN** | `NG-BEN-` | Benue | North Central | Makurdi |
| **KOG** | `NG-KOG-` | Kogi | North Central | Lokoja |
| **KWA** | `NG-KWA-` | Kwara | North Central | Ilorin |
| **KAD** | `NG-KAD-` | Kaduna | North West | Kaduna |
| **NAS** | `NG-NAS-` | Nasarawa | North Central | Lafia |
| **TAR** | `NG-TAR-` | Taraba | North East | Jalingo |
| **GOM** | `NG-GOM-` | Gombe | North East | Gombe |

> **Note (v4.1):** State codes are internal permanent identifiers, not ISO codes. `NIG` denotes Niger State and must not be confused with the Niger Republic or Nigeria's country code; entity IDs therefore carry the recommended prefix `NG-` (for example `NG-NIG-...`).
> **Permanent Hierarchy:** $\text{State} \longrightarrow \text{LGA} \longrightarrow \text{Ward (sub-layer G02W)} \longrightarrow \text{Community} \longrightarrow \text{Site / Facility / Household / Observation}$.

---

## 2. Core Properties (in priority order)

1. **Traceability** — Every output traceable to its data, method, source, version and QC status (Data Provenance & Audit Trail)
2. **Updateability** — New observations enter as dated records; history is never overwritten (RAW Landing Immutability)
3. **Reproducibility** — Same approved data + processing version = same analytical result (Frozen 2026 Reference Bounds)
4. **Explainability** — Every indicator and risk result: Input + Formula + Parameters + Reference Bounds + Version = Output
5. **Privacy & Data Governance** — Household data protected (Level 3 Restricted); only approved aggregations published

---

## 3. Directory Structure

```
GIS/
├── 00_Project_Control/       ← Master Scaffold v4.1, Reference Bounds, Version log, registers, control files
├── 01_Research_Design/       ← Study design, sampling frame, protocols (Stage 6.1)
├── 02_Fieldwork/             ← Field forms, survey instruments, GPS logs, photos
├── 03_Data/
│   ├── RAW/                  ← Ingested source data (immutable)
│   ├── CLEAN/                ← QC-passed analytical data + DB schemas
│   ├── DERIVED/              ← Computed indicators, indices, risk models
│   ├── LOOKUPS/              ← Reference/lookup tables + relational model + LKP_States + LKP_LGAs
│   └── POSTGRESQL_DDL_v4.1.sql ← PostgreSQL/PostGIS DDL; 31 core tables including FEW-CAM
├── 04_GIS/
│   ├── 01_RAW/               ← Source GIS datasets (never modified)
│   ├── 02_CLEAN/             ← QC-validated GIS layers
│   ├── 03_DERIVED/           ← Analytical GIS products
│   ├── 04_PROJECTS/          ← QGIS project files (LTR version pinned at build)
│   ├── 05_MAP_EXPORTS/       ← Final map outputs (PDF/PNG) + MAP_PRODUCTION_STANDARD.md
│   └── 06_METADATA/          ← Layer metadata, schemas, QC checklists; FEW-CAM G38-G43 register
├── 05_Analysis/
│   ├── 01_INPUTS/            ← Analysis input datasets
│   ├── 02_SCRIPTS/           ← Python pipeline (22 scripts + run_pipeline.py + test_pipeline.py)
│   ├── 03_OUTPUTS/           ← Analysis results (G29–G37 CSV outputs)
│   └── 04_QC/                ← QC reports and logs
├── 06_Reports/
│   ├── 01_DRAFTS/            ← Profile templates (community + state)
│   ├── 02_TABLES/            ← Analytical tables from 17_reports.py
│   ├── 03_FIGURES/           ← Map register
│   └── 04_FINAL/             ← Published reports (immutable)
├── 07_Decision_Support/
│   ├── 01_Risk/              ← RISK_MODEL_SPEC.md (v4.1) + G35 outputs
│   ├── 02_Dashboards/        ← Dashboard data files (Grafana / MapLibre)
│   └── 03_Priority_Areas/    ← G37 priority area outputs + top-20 list
├── 08_Updates/               ← UPDATE_LOG.csv + monitoring + update procedure
└── 09_Archive/               ← Superseded versions (immutable)
```

---

## 4. Master Risk and Decision Formulas (Section 34)

### Composite Risk Formula
$$R = 0.35H + 0.25E + 0.25V + 0.15C$$

All components normalized to **0–100**. Model version: **Risk_Model_v4.1**

| Component | Provisional Weight | Layer | Concept |
|---|---|---|---|
| **H — Hazard** | 35% | G31 | Exposure to flood and erosion hazard |
| **E — Exposure** | 25% | G32 | Population and assets in hazard zone |
| **V — Vulnerability** | 25% | G33 | Socio-economic sensitivity and lack of adaptation |
| **C — Criticality** | 15% | G34 | Critical infrastructure & hydropower dependence |

> **Provisional Weights Note:** Weights are provisional until ratified by the Steering Committee (Stage 17.5).
> **Multiplicative Aggregation Check (Stage 17.9):** Every run evaluates $R_{\text{mult}} = H^{0.35} \times E^{0.25} \times V^{0.25} \times C^{0.15}$ to ensure that zero exposure ($E=0$) cannot yield high risk.
> $R$ is a **decision-support index** — explicitly **not a probability of disaster**.

### Normalization Reference Bounds (v4.1 Stage 17.8)
Reference bounds ($\min_{\text{ref}}, \max_{\text{ref}}$) are **frozen at the 2026 baseline** (`00_Project_Control/REFERENCE_BOUNDS_REGISTER.csv`) and are **never** re-computed dynamically per period:
- Positive: $x_{\text{norm}} = 100 \times \frac{x - \min_{\text{ref}}}{\max_{\text{ref}} - \min_{\text{ref}}}$ (clipped to $[0, 100]$)
- Inverse: $x_{\text{norm}} = 100 \times \frac{\max_{\text{ref}} - x}{\max_{\text{ref}} - \min_{\text{ref}}}$ (clipped to $[0, 100]$)

### Intervention Effectiveness Score (IES) & Residual Risk (v4.1)
$$\text{IES} = \left(\frac{\text{Risk}_{\text{before}} - \text{Risk}_{\text{after}}}{\text{Risk}_{\text{before}}}\right) \times 100\%$$
- **Validity rules:** Both terms must use identical model versions and frozen reference bounds.
- If $\text{Risk}_{\text{before}} = 0$, IES is mathematically undefined (`N/A`).
- Must report observation period and confidence rating; otherwise labelled `Observed Risk Change`.
- $\text{Residual Risk} = \text{Risk}_{\text{after}}$.

---

## 5. 43-Layer GIS Master Register (Section 31 + FEW-CAM)

| Range | Category | Key Layers |
|---|---|---|
| **G01–G04** | Administrative & Communities | State (G01); LGA with Ward sub-layer G02W (G02); Communities (G03); Households Restricted (G04) |
| **G05–G08** | Hydrology & Hydropower | River & Drainage Network explicitly including main rivers, tributaries, distributaries, streams (G05); HydroBasins (G06); HydroFacilities (G07); Reservoirs (G08) |
| **G09–G14** | Terrain | DEM (G09); Slope in degrees (G10); Aspect (G11); Hillshade (G12); Flow Direction (G13); Flow Accumulation (G14) |
| **G15–G19** | Environment & Infrastructure | Land cover (G15); Roads (G16); Buildings (G17); POI (G18); Field infrastructure (G19) |
| **G20–G23** | Climate | Stations (G20); Observations (G21); Rainfall surface (G22); Temperature surface (G23) |
| **G24–G28** | Hazard & Observed Events | Flood hazard model (G24); Observed floods (G25); Erosion sites (G26); Erosion hotspots (G27); Hydropower monitoring (G28) |
| **G29–G30** | Exposure | Flood exposure (G29); Erosion exposure (G30) |
| **G31–G37** | Decision Support | Hazard Index (G31); Exposure Index (G32); Vulnerability Index (G33); Criticality Index (G34); Composite Risk (G35); Adaptation (G36); Priority Areas (G37) |
| **G38–G43** | Flood Early Warning & Preparedness | Flood Alert Zones (G38); Flood Warning Points (G39); Community Awareness Locations (G40); Approved Evacuation or Assembly Areas (G41); Historical Flood Events (G42); Recent Flood Extent (G43) |

**G05 remains critical:** the river and drainage network explicitly includes main rivers, tributaries, distributaries, streams, and drainage channels. New-layer metadata and publication caveats are in [`04_GIS/06_METADATA/FEW_CAM_GIS_REGISTER.csv`](04_GIS/06_METADATA/FEW_CAM_GIS_REGISTER.csv).

---

## 6. Core Data Tables (Section 32 — 22 Tables)

| Domain | Table Name | Primary Key | Key Foreign Keys & Content |
|---|---|---|---|
| **Administrative** | `Ward_Master` *(v4.1)* | `Ward_ID` | `LGA_ID`, `State_Code`, boundary version, dates |
| **Administrative** | `Community_Master` | `Community_ID` | `Ward_ID`, `LGA_ID`, `State_Code`, coordinates, population, `Provenance_ID` |
| **Survey** | `Household_Survey` | `Household_ID` | `Community_ID`, consent, socioeconomics, losses (Level 3 Restricted) |
| **Hazard** | `Erosion_Sites` | `Erosion_ID` | `Community_ID`, type, severity 0–4, dimensions, threat, `Provenance_ID` |
| **Hazard** | `Flood_Events` | `Flood_Event_ID` | Date, depth, duration, source agency, confidence rating |
| **Flood Early Warning** | `Flood_Alerts` | `Alert_ID` | Graduated level, trigger/rule version, confidence, review/approval/release/cancellation |
| **Flood Early Warning** | `Flood_Alert_Triggers` | `Trigger_ID` | Evidence source, observation time, value/threshold, rule and confidence |
| **Flood Early Warning** | `Flood_Alert_Areas` | `Alert_Area_ID` | Affected geometry, community/LGA, exposed population/assets |
| **Flood Early Warning** | `Flood_Notifications` | `Notification_ID` | Approved channel, message version/language, delivery and reach |
| **Flood Early Warning** | `Flood_Acknowledgements` | `Acknowledgement_ID` | Notification acknowledgement outcome and time |
| **Community Awareness** | `Flood_Awareness` | `Awareness_ID` | Community activity, language, audience, reach, materials and feedback |
| **Community Awareness** | `Flood_Drills` | `Drill_ID` | Preparedness exercise, participants, outcome and lessons |
| **Flood Impact** | `Flood_Impacts` | `Impact_ID` | Verified event impacts, loss, disruption, confidence and provenance |
| **Performance** | `Flood_Warning_Performance` | `Performance_ID` | Lead time, reach, hit/miss/false-alarm, extent, coverage and audit completeness |
| **Hydropower** | `Facility_Master` *(v4.1)* | `Facility_ID` | Capacity, operator, status, linked basin, coordinates |
| **Hydropower** | `Hydropower_Water` | `Hydro_Record_ID` | `Facility_ID`, elevation, inflow, outflow, generation, disruption |
| **Climate** | `Climate_Station` *(v4.1)* | `Station_ID` | Operator, coordinates, elevation, operating period |
| **Climate** | `Climate_Observations`| `Climate_ID` | `Station_ID`, date, rainfall, temp min/max |
| **Infrastructure** | `Infrastructure` | `Infrastructure_ID` | `Community_ID`, type, condition 1–5, service disruption |
| **Food & Social** | `Food_Security` | `Food_Record_ID` | `Community_ID`, crop/livestock loss, food security index |
| **Food & Social** | `Security_Impact` | `Security_Event_ID` | Development impacts: displacement, farm/market/project access |
| **Interventions** | `Interventions` | `Intervention_ID` | Project, budget, baseline risk, outcome risk, IES score, residual risk |
| **Loss & Damage** | `Loss_Damage` *(v4.1)* | `Loss_ID` | Event link, asset/livelihood type, physical qty, financial value NGN |
| **Decision** | `Indicators` | `Indicator_Entry_ID`| `Indicator_ID`, `Community_ID`, raw & normalized value, period |
| **Decision** | `Risk_Assessments` | `Risk_ID` | `Community_ID`, H, E, V, C, Composite Risk, confidence rating, version |
| **Decision** | `Priority_Areas` *(v4.1)* | `Priority_ID` | `Community_ID`, composite risk, adaptation gap, priority tier 1–4 |
| **Decision** | `Scenarios` | `Scenario_ID` | Climate stress, land-use, adaptation scenario projections |
| **Governance** | `Data_Provenance` *(v4.1)*| `Provenance_ID` | Source, date, method, software version, analyst, limitations |
| **Governance** | `Audit_Trail` *(v4.1)* | `Audit_ID` | Table, PK, original value, corrected value, reason, user, timestamp |
| **Governance** | `Data_Confidence` *(v4.1)*| `Confidence_ID` | Completeness %, recency, source quality, rating (High/Mod/Low/Unk) |
| **Governance** | `Lookup_Code` *(v4.1)* | `Lookup_ID` | Controlled vocabularies, units, classes, dictionary versions |

---

## 7. PostgreSQL / PostGIS DDL

A complete PostgreSQL/PostGIS DDL script defining the 31-table core model (plus supporting lookup, audit and RAW tables), spatial geometries, foreign keys, workflow constraints, RBAC groups, audit triggers and immutable RAW triggers is available at:
👉 [`03_Data/POSTGRESQL_DDL_v4.1.sql`](file:///c:/xampp/htdocs/GIS/03_Data/POSTGRESQL_DDL_v4.1.sql)

---

## 8. Python Pipeline & Verification

```
05_Analysis/02_SCRIPTS/
├── config.py                       ← Central v4.1 config, reference bounds, IES & risk math
├── qc_utils.py                     ← Automated data quality & referential integrity checks
├── test_pipeline.py                ← 12-suite automated test (197/197 checks passing)
└── run_pipeline.py                 ← 18-step master pipeline controller
```

Run test suite: `python test_pipeline.py` (Full 197 checks)  
Run quick test: `python test_pipeline.py --quick`  
Run pipeline dry-run: `python run_pipeline.py --dry-run`

---

## 9. Responsibility, Inputs, and Acceptance Matrix (Section 44)

Stage-by-stage governance and delivery matrix across 30 implementation stages:
- **Phase 0:** Governance, Mandate & Framework (Stages 1–2) — Sponsor, Steering Committee, Programme Manager
- **Phase 1:** Master Geography, Database Infrastructure, Field System & ETL (Stages 3–7) — GIS Manager, Developer, Field Coordinator
- **Phase 2:** GIS, Earth Observation, Climate, Hydrology, Flood & Erosion (Stages 8–12) — Remote Sensing Analyst, Hydro-Climate Analyst, GIS Analyst
- **Phase 3:** Food Security, Security Impacts, Adaptation & MRV (Stages 13–15) — MRV Officer, Livelihoods Specialist, Privacy Focal Person
- **Phase 4:** Indicators, Composite Risk, Uncertainty, Prioritisation (Stages 16–20) — Statistician, Risk Modeller, GIS Manager
- **Phase 5:** Dashboard, Annual Report, Conference Pack, UAT & Go-Live (Stages 22–24, 28–29) — Sponsor, Programme Manager, Users
- **Phase 6:** Scenario Modelling & Early Warning Prototype (Stage 21) — Hydro-Climate Analyst, Risk Modeller
- **Phase 7:** Long-Term Continuous Operations (Stage 30) — System Owner, GIS Data Manager

Full specification: [`00_Project_Control/CHER_CDSS_ADVANCED_MASTER_IMPLEMENTATION_SCAFFOLD_v4.1.md`](file:///c:/xampp/htdocs/GIS/00_Project_Control/CHER_CDSS_ADVANCED_MASTER_IMPLEMENTATION_SCAFFOLD_v4.1.md)

---

## 10. Field Collection System (Stage 5 — KoboToolbox / ODK)

- **Master XLSForm Workbook:** [`02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.1.xlsx`](file:///c:/xampp/htdocs/GIS/02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.1.xlsx)
- **Specification & SOP:** [`02_Fieldwork/XLSFORM_SPECIFICATION.md`](file:///c:/xampp/htdocs/GIS/02_Fieldwork/XLSFORM_SPECIFICATION.md)
- **Features:** 74 survey questions, 10-state selection with 186 cascading LGAs (`choice_filter`), conditional skip logic, GPS accuracy constraints, and strict non-PII media protocols.

---

## 11. Web GIS & Executive Decision Dashboard (Stage 22)

- **FastAPI Backend Server:** [`07_Decision_Support/02_Dashboards/app.py`](file:///c:/xampp/htdocs/GIS/07_Decision_Support/02_Dashboards/app.py)
- **Launch Command:** `python run_dashboard.py`
- **Dashboard Interface:** [http://localhost:8000/](http://localhost:8000/) (Interactive Leaflet map, KPI tiles, live risk calculator, priority tiers)
- **REST API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs) (OpenAPI / Swagger UI)
- **Flood Early Warning & Community Awareness:** [`00_Project_Control/FEW_CAM_IMPLEMENTATION.md`](00_Project_Control/FEW_CAM_IMPLEMENTATION.md) documents the FEW-01–FEW-13 workflow, PostGIS access roles, six new GIS layers, performance indicators, and pilot safety gates. The dashboard is read-only; it does not issue official warnings.

---

## 12. Docker & Enterprise Container Deployment (Stage 27)

Single-command full stack deployment with PostgreSQL 16 + PostGIS 3.4, GeoServer, MinIO, and FastAPI:
- **Orchestration Config:** [`docker-compose.yml`](file:///c:/xampp/htdocs/GIS/docker-compose.yml)
- **Container Build:** [`Dockerfile`](file:///c:/xampp/htdocs/GIS/Dockerfile)
- **Environment Template:** [`.env.example`](file:///c:/xampp/htdocs/GIS/.env.example)
- **Operations Manual:** [`DOCKER_DEPLOYMENT_GUIDE.md`](file:///c:/xampp/htdocs/GIS/DOCKER_DEPLOYMENT_GUIDE.md)

Command: `docker compose up -d --build`


---

## v2.0 Environmental Domains Extension

Six new environmental domains integrated into the system (2026-10-14):

| Domain | Code | GIS Layers | Script | Key Indicators |
|---|---|---|---|---|
| Climate Change | CC | G38–G42 | `20_climate_change.py` | IND11 rainfall trend; IND12 temp trend; IND13 drought (SPI-12) |
| Flooding Upgraded | FL | G43–G46 | `21_flooding.py` | IND14 RP inundation; Gumbel + HAND model |
| Land Degradation | LD | G47–G50 | `22_land_degradation.py` | IND15 NDVI trend; IND16 RUSLE soil loss |
| Deforestation | DF | G51–G54 | `23_deforestation.py` | IND17 deforestation rate; Hansen GFC |
| Waste Pollution | WP | G55–G58 | `24_waste_pollution.py` | IND18 dump proximity; IND19 leachate risk |
| Biodiversity Loss | BL | G59–G63 | `25_biodiversity.py` | IND20 habitat integrity; IND21 PA coverage; IND22 ES loss |

**Environmental Risk Index v2.0 (G64):** `26_eri.py`
```
ERI = 0.25H + 0.15E + 0.15V + 0.10C + 0.10CC + 0.08LD + 0.07DF + 0.05WP + 0.05BL
```
Weights verified: 0.25+0.15+0.15+0.10+0.10+0.08+0.07+0.05+0.05 = **1.00** ✓

New databases: DB07 Interventions | DB08 Waste Sites | DB09 Biodiversity Observations  
New sources: SRC018–SRC030 (CHIRPS, CORDEX, Hansen GFC, JRC, Sentinel-2, WDPA, RUSLE)  
New buffers: BUF008–BUF012  
New indicators: IND11–IND22  
New model decisions: HMD07–HMD10

Full specification: `00_Project_Control/ENVIRONMENTAL_DOMAINS_EXTENSION.md`
