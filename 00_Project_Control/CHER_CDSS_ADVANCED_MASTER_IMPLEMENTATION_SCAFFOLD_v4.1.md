# CHER-CDSS ADVANCED MASTER IMPLEMENTATION SCAFFOLD
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System
### For the Ten N-HYPPADEC States of Nigeria
**International Conference / Institutional Evidence-Platform Version 4.1 (validated and corrected)**  
**October 2026**

---

### Revision Note v4.1
- **Section 44 added:** Detailed Responsibility, Inputs, Tools, Acceptance, and Phasing Matrix for all 30 implementation stages.
- **Nine supporting data tables added:** `Ward_Master`, `Facility_Master`, `Climate_Station`, `Priority_Areas`, `Loss_Damage`, `Data_Provenance`, `Audit_Trail`, `Data_Confidence`, and `Lookup_Code` (Section 32).
- **Entity identifiers established:** Permanent identifiers defined for Wards (`Ward_ID`), Stations (`Station_ID`), Facilities (`Facility_ID`), Erosion Sites (`Erosion_ID`), Interventions (`Intervention_ID`), and Households (`Household_ID`).
- **Normalization reference bounds fixed:** Min and max reference bounds frozen at the 2026 baseline to ensure longitudinal comparability (Stage 17.8 & Section 34).
- **IES validity rules codified:** Intervention Effectiveness Score validity conditions enforced (must use identical methodology and reference bounds; undefined when $Risk_{before} = 0$; must be reported with observation period and confidence).
- **Provisional weights clarified:** Baseline additive composite risk weights documented as provisional pending Steering Committee approval; comparison against multiplicative/geometric alternative required (Stage 17.9).
- **State codes disambiguated:** State code internal identifiers clarified (`NIG`, `KEB`, `PLA`, `BEN`, `KOG`, `KWA`, `KAD`, `NAS`, `TAR`, `GOM`) with entity ID prefix `NG-` (e.g., `NG-NIG-...`).
- **Heading structure standardisation:** Renamed non-stage headings to `SECTION n` to avoid confusion with `STAGE n`.
- **GIS environment specification:** Replaced unverified QGIS version with requirement to pin the long-term-release (LTR) version in build environment specification.
- **Sampling design requirements:** Formal stratification, sample size formulas, margin of error, design effect, and replacement protocols added (Stage 6.1).

---

## SECTION 0 — HOW TO USE THIS SCAFFOLD

This document is the developer-ready and management-ready implementation blueprint for CHER-CDSS. It expands the previous proposal into explicit stages, steps, and expected outputs. Section 44 adds, for every stage, the accountable and responsible roles, key inputs, tools, acceptance criterion, and delivery phase. Calendar dates, budget, and staffing levels are deliberately not fixed here; they are management decisions listed in Section 44.3. Each stage can become a work package, procurement item, implementation sprint, SOP, or chapter of the final institutional manual.

The system is designed as a permanent institutional monitoring and decision-support capability rather than a one-time research project. The 2026 implementation is the baseline; subsequent years update the same permanent identifiers, indicators, intervention records, risk models, and evidence chain.

| Layer | Purpose | Primary Result |
|---|---|---|
| **Observe** | Field, satellite, climate, hydrology, project, and administrative observations | Raw evidence |
| **Validate** | Quality control, provenance, geometry, logical, and scientific checks | Trusted clean data |
| **Integrate** | Link observations through permanent IDs and spatial relationships | Institutional evidence base |
| **Analyse** | Indicators, trends, hazard/exposure/vulnerability/criticality | Evidence and metrics |
| **Model** | Risk, scenarios, uncertainty, residual risk | Decision intelligence |
| **Act** | Interventions, adaptation, and project implementation | Documented response |
| **Measure** | MRV and before/after effectiveness | Measured outcomes |
| **Decide** | Priority areas, budget/programme choices | Management decisions |
| **Report** | Dashboards, maps, annual reports, conference evidence | Institutional communication |
| **Learn** | Update methods and feedback from outcomes | Continuous improvement |

---

## SECTION 1 — MASTER OUTCOME

CHER-CDSS should enable N-HYPPADEC to answer, with traceable evidence:
1. What is happening?
2. Where?
3. When?
4. Who and what is exposed?
5. How severe is the risk?
6. What has changed?
7. What has N-HYPPADEC done?
8. Did the intervention work?
9. What risk remains?
10. What is likely under plausible scenarios?
11. Where should the next intervention or monitoring effort be directed?

**International positioning:** CHER-CDSS is an integrated climate intelligence, resilience monitoring, MRV, and decision-support system combining field observations, remote sensing, climate/hydrological evidence, hydropower information, GIS, socioeconomic evidence, food-security indicators, community-security impacts, risk modelling, intervention effectiveness, and uncertainty.

---

## SECTION 2 — PERMANENT GEOGRAPHIC SCOPE

| Permanent State Code | State Name | Capital | Geopolitical Zone |
|---|---|---|---|
| **NIG** | Niger | Minna | North Central |
| **KEB** | Kebbi | Birnin Kebbi | North West |
| **PLA** | Plateau | Jos | North Central |
| **BEN** | Benue | Makurdi | North Central |
| **KOG** | Kogi | Lokoja | North Central |
| **KWA** | Kwara | Ilorin | North Central |
| **KAD** | Kaduna | Kaduna | North West |
| **NAS** | Nasarawa | Lafia | North Central |
| **TAR** | Taraba | Jalingo | North East |
| **GOM** | Gombe | Gombe | North East |

> **Note (v4.1):** State codes are internal permanent identifiers, not ISO codes. `NIG` denotes Niger State and must not be confused with the Niger Republic or the country code for Nigeria; entity IDs therefore carry the recommended prefix `NG-` (for example `NG-NIG-...`), subject to approval of the ID policy (Section 42, task 4). The list of ten states must be confirmed against the N-HYPPADEC establishment Act before baseline freeze (Section 44.4).

**Permanent Hierarchy:**  
$$\text{State} \longrightarrow \text{LGA} \longrightarrow \text{Ward (where available)} \longrightarrow \text{Community} \longrightarrow \text{Site / Facility / Household / Observation}$$

Every level has a permanent ID (`State_Code`, `LGA_ID`, `Ward_ID`, `Community_ID`, and Site/Facility/Household/Observation IDs). Never create duplicate names when a permanent identifier exists. Every repeat observation must link to the same entity ID.

---

## SECTION 3 — MASTER ARCHITECTURE

```
External / Field / Satellite / Climate / Hydrology / Project records
                          │
                          ▼
                 RAW Immutable Storage
                          │
                          ▼
                       QC / ETL
                          │
                          ▼
              CLEAN Authoritative Datasets
                          │
                          ▼
                 PostgreSQL / PostGIS
                          │
                          ▼
                   Indicator Engine
                          │
                          ▼
      Hazard / Exposure / Vulnerability / Criticality
                          │
                          ▼
                   Thematic Indices
                          │
                          ▼
                    Composite Risk
                          │
                          ▼
            Scenario / Uncertainty Analysis
                          │
                          ▼
                    Priority Areas
                          │
                          ▼
             Dashboard / QGIS / GeoServer
                          │
                          ▼
                 Management Decisions
                          │
                          ▼
                    Interventions
                          │
                          ▼
                         MRV
                          │
                          ▼
                 Updated Observations
                          │
                          └───▶ (Repeat Cycle)
```

| Core Component | Role | Recommended Technology |
|---|---|---|
| **Field collection** | Offline standardized observation | KoboToolbox / ODK Collect |
| **Central database** | Authoritative structured / spatial evidence | PostgreSQL + PostGIS |
| **GIS** | Spatial editing, QA, map production | QGIS (current LTR version pinned at build) |
| **Remote sensing** | Earth observation processing | Sentinel / Landsat / DEM + GEE / GDAL / Rasterio |
| **ETL / analytics** | Validation, indicators, statistics, automation | Python, Pandas, GeoPandas, SciPy, Statsmodels |
| **GIS publication** | Web map services | GeoServer |
| **API** | System integration | FastAPI |
| **Web GIS** | Management interface | Leaflet / MapLibre |
| **Dashboard** | KPIs and trends | Custom dashboard / Grafana / Metabase |
| **Storage** | Raw imagery, files, backups | MinIO / S3-compatible storage |
| **Version control** | Code and configuration | Git |
| **Deployment** | Reproducible services | Docker |

---

## STAGES 1 TO 30 — DETAILED IMPLEMENTATION STAGES

### STAGE 1 — INSTITUTIONAL GOVERNANCE AND MANDATE
- **1.1 Executive mandate:** Obtain written approval, designate sponsor, define institutional owner, approve scope and reporting authority. Output: Approved mandate; named sponsor and system owner.
- **1.2 Steering structure:** Create steering committee, technical team, state focal persons, GIS/data manager, field coordinator, and security/privacy focal person. Output: Governance chart; TOR; meeting schedule.
- **1.3 Data-sharing agreements:** Define access to N-HYPPADEC project records, operator/hydropower data, climate/hydrology sources, and partner datasets. Output: Data-sharing register and agreements.
- **1.4 Ethics and privacy:** Approve consent language, personal-data minimisation, access controls, and anonymisation/pseudonymisation rules. Output: Ethics/privacy SOP.
- **1.5 Change control:** Require documented approval for new indicators, weights, layers, definitions, and questionnaire changes. Output: Change-control register.

### STAGE 2 — RESEARCH AND MONITORING FRAMEWORK
- **2.1 Theory of change:** Map climate/environmental pressures → hazards → exposure → vulnerability → impacts → interventions → outcomes → resilience. Output: Approved theory-of-change diagram.
- **2.2 Monitoring questions:** Define questions by climate, flood, erosion, hydropower, food security, livelihoods, security impacts, infrastructure, and adaptation. Output: Question bank.
- **2.3 Indicator definitions:** For every indicator define numerator, denominator, unit, direction, source, frequency, spatial unit, missing-data rule, and interpretation. Output: Indicator dictionary.
- **2.4 Baseline protocol:** Freeze the 2026 baseline rules and data cut-off; record all methodological versions. Output: 2026 baseline protocol.
- **2.5 Monitoring calendar:** Define monthly, quarterly, seasonal, and annual updates. Output: Monitoring calendar.

### STAGE 3 — MASTER GEOGRAPHY AND IDENTIFIERS
- **3.1 Administrative base:** Load OCHA/HDX administrative boundaries (state, LGA, and, where available, ward) and document source/version/date. Output: G01 state and G02 LGA layers; ward boundaries held as sub-layer G02W.
- **3.2 Community gazetteer:** Create standard community registry with permanent Community_ID and aliases. Output: G03 community master.
- **3.3 Entity IDs:** Create permanent IDs for wards, households, erosion sites, facilities, interventions, climate stations, and hydropower assets (`Ward_ID`, `Household_ID`, `Erosion_ID`, `Facility_ID`, `Intervention_ID`, `Station_ID`). Output: ID registry.
- **3.4 Spatial QA:** Run point-in-polygon, duplicate, coordinate-range, CRS, and geometry-validity checks. Output: Spatial QA report.
- **3.5 Versioning:** Never silently replace historical boundaries; retain source version and validity dates. Output: Boundary version register.

### STAGE 4 — DATABASE AND DATA MODEL
- **4.1 Logical model:** Define entities and relationships before coding. Output: ERD.
- **4.2 Raw schemas:** Create immutable raw landing tables. Output: RAW schema.
- **4.3 Clean schemas:** Create validated operational tables with constraints. Output: CLEAN schema.
- **4.4 Derived schemas:** Create indicators, indices, risk, scenarios, and outputs. Output: DERIVED schema.
- **4.5 Provenance:** Store source, acquisition date, processing method, software/model version, and analyst, implemented through Data_Provenance, Audit_Trail, Data_Confidence, and Lookup_Code tables (Section 32). Output: Data lineage fields.
- **4.6 Performance:** Add indexes, spatial indexes, constraints, and controlled lookup tables. Output: Production-ready database.

### STAGE 5 — KOBOTOOLBOX/ODK FIELD SYSTEM
- **5.1 Questionnaire design:** Implement identification, consent, climate, flood, erosion, hydropower, livelihoods, food security, security impacts, adaptation, and intervention sections. Output: Master XLSForm.
- **5.2 Cascade selects:** State → LGA → Community; use controlled lists and IDs. Output: Validated cascade logic.
- **5.3 Skip logic:** Only show relevant modules based on responses. Output: Tested skip logic.
- **5.4 Validation:** Range, required fields, date, coordinate, logical consistency, and duplicate warnings. Output: Validation rules.
- **5.5 Media:** Capture photos with IDs, dates, and location where appropriate; do not expose sensitive personal information. Output: Media protocol.
- **5.6 Offline testing:** Test in airplane/offline mode, sync failures, and recovery. Output: Field acceptance test.

### STAGE 6 — FIELD SAMPLING AND DATA COLLECTION
- **6.1 Sampling frame:** Finalize communities and household sample from the approved frame using a documented design: stratify by state, LGA, and community type; set sample size from approved precision parameters (confidence level, margin of error, design effect, expected non-response); record selection method, replacement rules, and weights. Output: Sampling frame and sampling protocol.
- **6.2 Enumerator training:** Train on consent, GPS, questionnaire, photo standards, safety, neutrality, and data quality. Output: Training completion record.
- **6.3 Pilot:** Pilot in a small number of communities; document problems and revise before baseline. Output: Pilot report.
- **6.4 Community survey:** Collect structured community observations and key-informant evidence. Output: Community dataset.
- **6.5 Household survey:** Collect household-level livelihood, loss, food-security, and resilience data with consent. Output: Household dataset.
- **6.6 Site surveys:** Collect erosion, infrastructure, and intervention observations with GPS and repeatable measurements. Output: Site datasets.
- **6.7 Daily QC:** Supervisor checks completeness, GPS, duplicates, unusual values, and missing evidence daily. Output: Daily QC log.

### STAGE 7 — ETL, QC AND DATA GOVERNANCE
- **7.1 Ingest:** Land every submission in RAW without overwriting. Output: Immutable raw record.
- **7.2 Structural validation:** Check field names, data types, required fields, and IDs. Output: Structural QC report.
- **7.3 Logical validation:** Check contradictions such as zero households affected with severe event where not logically justified. Output: Logical QC report.
- **7.4 Spatial validation:** Check coordinates, CRS, point-in-polygon, and geometry. Output: Spatial QC report.
- **7.5 Source validation:** Record who supplied data, when, how, and under what limitations. Output: Provenance register.
- **7.6 Clean/promote:** Only validated records enter CLEAN. Output: Promotion log.
- **7.7 Audit trail:** Retain original value, corrected value, reason, date, and user for material corrections. Output: Audit trail.

### STAGE 8 — GIS IMPLEMENTATION
- **8.1 Core geography:** G01 State, G02 LGA, G03 Communities, G04 Households.
- **8.2 Hydrography:** G05 River_and_Drainage_Network explicitly includes main rivers, tributaries, distributaries, seasonal streams, and channels; G06 basins.
- **8.3 Hydropower:** G07 facilities and G08 reservoirs.
- **8.4 Terrain:** G09 DEM, G10 slope, G11 aspect, G12 hillshade, G13 flow direction, G14 flow accumulation.
- **8.5 Land/infrastructure:** G15 land cover, G16 roads, G17 buildings, G18 POI, G19 field infrastructure.
- **8.6 Climate:** G20 stations, G21 observations, G22 rainfall surface, G23 temperature surface.
- **8.7 Hazards:** G24 flood hazard, G25 observed flood, G26 erosion sites, G27 erosion hotspots.
- **8.8 Water/exposure:** G28 hydropower/water, G29 flood exposure, G30 erosion exposure.
- **8.9 Indices:** G31 hazard, G32 exposure, G33 vulnerability, G34 criticality, G35 composite risk.
- **8.10 Response:** G36 adaptation/interventions, G37 priority areas.

### STAGE 9 — REMOTE SENSING AND EARTH OBSERVATION
- **9.1 Acquisition:** Define sensor, date range, spatial resolution, and cloud/quality thresholds. Output: Acquisition register.
- **9.2 Preprocessing:** Apply required corrections, masking, and harmonisation; record software/version. Output: Processed scenes.
- **9.3 Land cover:** Generate land-cover baseline/change products using approved classification method. Output: Land-cover products.
- **9.4 Vegetation:** Generate NDVI/vegetation-condition indicators and anomalies. Output: Vegetation products.
- **9.5 Surface water/flood:** Use radar/optical evidence as appropriate to derive observed water/flood extent. Output: Flood extent products.
- **9.6 Riverbank change:** Measure repeatable bankline/shoreline change where resolution and validation support it. Output: Riverbank-change products.
- **9.7 Validation:** Compare satellite outputs with field observations and known events. Output: Accuracy report.

### STAGE 10 — CLIMATE, HYDROLOGY AND HYDROPOWER
- **10.1 Climate acquisition:** Acquire rainfall, temperature, and other permitted variables from approved sources. Output: Climate archive.
- **10.2 Hydrology:** Acquire river/water-level/discharge/inflow/outflow observations where available. Output: Hydrology archive.
- **10.3 Hydropower:** Record facility, capacity, operating status, water conditions, generation/disruption, and source. Output: Hydropower monitoring dataset.
- **10.4 Time alignment:** Standardise timestamps, time zones, units, and aggregation periods. Output: Harmonised time series.
- **10.5 Trend analysis:** Apply appropriate trend/anomaly methods only where data length/quality supports them. Output: Trend tables/charts.
- **10.6 Hydro-climate linkage:** Analyse relationships between rainfall/water conditions and hydropower/community impacts without claiming unsupported causality. Output: Evidence analysis.

### STAGE 11 — FLOOD INTELLIGENCE AND EARLY WARNING
- **11.1 Drainage network:** Include main rivers, tributaries, distributaries, streams, channels, floodplains, and wetlands. Output: Connected drainage model.
- **11.2 Terrain model:** Use DEM, slope, flow direction, and flow accumulation. Output: Drainage/flood susceptibility evidence.
- **11.3 Historical flood evidence:** Combine observed flood polygons, field reports, and official flood information. Output: Historical flood layer.
- **11.4 Exposure overlay:** Intersect flood evidence with communities, households, roads, buildings, farms, facilities, and hydropower assets. Output: Exposure tables.
- **11.5 Event catalogue:** Record date, duration, depth/extent where available, source, confidence, and impacts. Output: Flood event database.
- **11.6 Alert prototype:** Develop watch/warning logic from approved rainfall, water, and susceptibility thresholds; validate before operational use. Output: Prototype alert model.

### STAGE 12 — EROSION INTELLIGENCE
- **12.1 Site inventory:** Create permanent Erosion_ID for every monitored site. Output: Erosion registry.
- **12.2 Field severity:** Record type, dimensions, severity 0–4, activity, bank proximity, land cover, drainage, and infrastructure threat. Output: Standard erosion observations.
- **12.3 Remote evidence:** Use imagery/topography for contextual change detection where resolution permits. Output: Erosion evidence.
- **12.4 Hotspot analysis:** Identify clusters/hotspots using defensible spatial methods and minimum sample rules. Output: Hotspot layer.
- **12.5 Intervention linkage:** Link erosion sites to control measures and intervention IDs. Output: Before/after structure.

### STAGE 13 — FOOD SECURITY AND LIVELIHOODS
- **13.1 Food-security framework:** Define household/community food-security indicators and approved scales. Output: Food-security protocol.
- **13.2 Agriculture exposure:** Map farms/agricultural land where data and privacy rules permit. Output: Agricultural exposure layer.
- **13.3 Loss recording:** Capture crop, livestock, fishing, and livelihood disruption from climate/security events. Output: Loss dataset.
- **13.4 Access/markets:** Record water, market, and farm-access constraints. Output: Livelihood access indicators.
- **13.5 Index:** Develop Food Security Risk Index with documented normalization/weights after governance approval. Output: Food-security risk layer.
- **13.6 Trend:** Monitor seasonal and annual changes. Output: Food-security dashboard.

### STAGE 14 — COMMUNITY SECURITY AND CONFLICT-IMPACT MONITORING
- **14.1 Scope:** Measure development impacts of insecurity/conflict, not tactical intelligence. Output: Approved scope.
- **14.2 Indicators:** Displacement, farm access, market access, service disruption, project access constraints, livelihood disruption, and assistance. Output: Security-impact dataset.
- **14.3 Source/confidence:** Record source type, event period, and confidence; separate reported from verified information. Output: Confidence fields.
- **14.4 Spatial safeguards:** Avoid publishing sensitive operational locations or personally identifiable information. Output: Safe map products.
- **14.5 Link to resilience:** Assess how security constraints interact with climate vulnerability and livelihood resilience. Output: Integrated resilience analysis.

### STAGE 15 — ADAPTATION, PROJECTS AND MRV
- **15.1 Intervention registry:** Create Intervention_ID, location, type, budget where authorised, date, target risk, status, and responsible unit. Output: Intervention database.
- **15.2 Baseline:** Record pre-intervention hazard, exposure, vulnerability, affected population, and condition. Output: Baseline evidence.
- **15.3 Output monitoring:** Record construction/completion/service-delivery outputs. Output: Output monitoring.
- **15.4 Outcome monitoring:** Measure change in risk/impact indicators after implementation. Output: Outcome dataset.
- **15.5 Effectiveness:** Calculate documented risk reduction where before/after evidence supports it. Output: Intervention Effectiveness Score.
- **15.6 Residual risk:** Calculate and classify remaining risk after intervention. Output: Residual-risk layer.
- **15.7 MRV report:** Produce Monitoring, Reporting, and Verification record with evidence, assumptions, and limitations. Output: MRV package.

### STAGE 16 — INDICATOR ENGINE
- **16.1 Indicator register:** Maintain definition, unit, source, frequency, direction, formula, owner, and quality threshold. Output: Indicator register.
- **16.2 Compute:** Run reproducible scripts rather than manual spreadsheet edits. Output: Indicator tables.
- **16.3 Validation:** Compare computed results to known examples and prior periods. Output: Indicator QA.
- **16.4 Versioning:** Store indicator methodology version and calculation date. Output: Indicator lineage.

### STAGE 17 — RISK, VULNERABILITY AND CRITICALITY
- **17.1 Hazard:** Combine approved hazard indicators into H on 0–100 scale. Output: Hazard index.
- **17.2 Exposure:** Combine population/infrastructure/livelihood exposure into E. Output: Exposure index.
- **17.3 Vulnerability:** Combine sensitivity and adaptive-capacity measures into V. Output: Vulnerability index.
- **17.4 Criticality:** Measure importance of services/assets and consequences of disruption into C. Output: Criticality index.
- **17.5 Composite:** Provisional base formula: $R = 0.35H + 0.25E + 0.25V + 0.15C$. Weights are provisional until approved by the steering committee; the rationale is recorded in the change-control register. Output: Composite risk.
- **17.6 Sensitivity:** Run equal-weight and approved alternative scenarios. Output: Sensitivity report.
- **17.7 Missing data:** Do not silently substitute zero; document imputation/coverage rules. Output: Risk data-quality report.
- **17.8 Reference bounds (v4.1):** Fix the min/max used for normalization at the 2026 baseline (theoretical/policy bounds, or baseline distribution winsorised at documented percentiles) and reuse them in every later period so scores remain comparable over time. Change only through change control, with prior periods recalculated. Output: Reference-bounds register.
- **17.9 Aggregation check (v4.1):** Compare the additive composite with a multiplicative/geometric alternative (so that zero exposure cannot yield high risk) and record rank differences and the reason for the form adopted. Output: Aggregation-form comparison.

### STAGE 18 — UNCERTAINTY AND CONFIDENCE
- **18.1 Data confidence:** Score completeness, recency, source quality, and validation status using an approved rubric. Output: Confidence layer.
- **18.2 Model uncertainty:** Document sensitivity to weights, thresholds, classification, and missingness. Output: Uncertainty report.
- **18.3 Map confidence:** Publish risk and confidence together where useful. Output: Risk + confidence maps.
- **18.4 Decision rule:** Define when low-confidence outputs can be used for screening versus formal prioritisation. Output: Decision-use protocol.

### STAGE 19 — THEMATIC ANALYTICS
- **19.1 Climate trends:** Seasonal/annual anomalies, trends, and extremes.
- **19.2 Flood analytics:** Frequency, extent, depth where available, duration, exposure, and losses.
- **19.3 Erosion analytics:** Severity, change, hotspot patterns, and intervention response.
- **19.4 Hydropower analytics:** Water conditions, generation/disruption, and community effects.
- **19.5 Food security:** Production/loss/access/food-security patterns.
- **19.6 Security impacts:** Displacement/access/service/livelihood effects.
- **19.7 Resilience:** Adaptation coverage, gaps, intervention effectiveness, and residual risk.

### STAGE 20 — SPATIAL PRIORITISATION
- **20.1 Priority rules:** Define management-approved criteria for urgency, severity, exposure, vulnerability, criticality, feasibility, and evidence confidence. Output: Priority methodology.
- **20.2 Multi-criteria analysis:** Combine approved criteria; do not hide weights. Output: Priority score.
- **20.3 Priority tiers:** Classify areas as critical / high / moderate / monitor as approved. Output: Priority map.
- **20.4 Investment portfolio:** Link priority areas to candidate interventions and expected outcomes. Output: Decision portfolio.

### STAGE 21 — SCENARIO MODELLING
- **21.1 Baseline scenario:** Represent current/baseline conditions.
- **21.2 Climate stress:** Apply approved changes in rainfall/temperature/extreme-event assumptions.
- **21.3 Land-cover scenario:** Test plausible land-cover/drainage changes where data support it.
- **21.4 Adaptation scenario:** Model risk after specified interventions.
- **21.5 Compare:** Show change in hazard/exposure/risk and affected population/assets.
- **21.6 Caveat:** Label scenarios as projections/experiments, not predictions unless formally validated.

### STAGE 22 — WEB GIS AND MANAGEMENT DASHBOARD
- **22.1 API:** Expose approved indicators and spatial services through controlled API endpoints.
- **22.2 Map services:** Publish approved layers through GeoServer.
- **22.3 Dashboard KPIs:** Show states, communities, hazards, losses, interventions, effectiveness, residual risk, and confidence.
- **22.4 Drill-down:** State → LGA → Community → Site/Facility → Observation.
- **22.5 Time slider:** Allow historical comparison where data support it.
- **22.6 Export:** Generate evidence tables, maps, and conference-ready figures.

### STAGE 23 — ANNUAL STATE OF CLIMATE RESILIENCE REPORT
- **23.1 Evidence freeze:** Set annual data cut-off and freeze the reporting dataset.
- **23.2 State profiles:** Produce 10 state profiles using consistent structure.
- **23.3 National synthesis:** Compare trends, hotspots, interventions, and remaining gaps.
- **23.4 MRV chapter:** Report adaptation actions and measured outcomes.
- **23.5 Data-quality chapter:** Report coverage, limitations, and confidence.
- **23.6 Recommendations:** Translate evidence into programme/budget/policy recommendations.

### STAGE 24 — INTERNATIONAL CONFERENCE EVIDENCE PACKAGE
- **24.1 Core message:** Define one institutional problem, one evidence gap, one solution, key results, and institutional value.
- **24.2 Evidence board:** Prepare 10-state map, climate trends, hazard maps, food-security evidence, intervention results, and residual risk.
- **24.3 Methods transparency:** Present sources, methods, validation, and limitations.
- **24.4 Results:** Show measured findings only; label estimates and scenarios.
- **24.5 Replicability:** Document architecture so other institutions can adapt the approach.
- **24.6 Data provenance:** Attach metadata/source notes to major figures.

### STAGE 25 — SECURITY, PRIVACY AND RESPONSIBLE DATA
- **25.1 Roles:** Define least-privilege access by role (RBAC matrix).
- **25.2 Personal data:** Minimise PII; pseudonymise household records for analysis.
- **25.3 Sensitive security data:** Restrict sensitive community-security information; publish only safe aggregates.
- **25.4 Encryption:** Use encryption in transit and at rest where supported.
- **25.5 Audit:** Log access, changes, exports, and administrative actions.
- **25.6 Retention:** Define retention and archival rules for raw, clean, and derived data.

### STAGE 26 — BACKUP, BUSINESS CONTINUITY AND DISASTER RECOVERY
- **26.1 Backup policy:** Daily incremental and scheduled full backups.
- **26.2 Off-site copy:** Maintain separate physical/cloud/off-site copy with controlled access.
- **26.3 Restore tests:** Perform scheduled restore tests; a backup is not accepted until restoration works.
- **26.4 Continuity:** Define fallback field collection, offline operations, and manual emergency reporting.

### STAGE 27 — SOFTWARE ENGINEERING AND REPRODUCIBILITY
- **27.1 Repository:** Store Python, SQL, configuration templates, and documentation in Git.
- **27.2 Environments:** Pin dependencies and maintain environment specification.
- **27.3 Automated tests:** Test formulas, transformations, ID logic, and API endpoints.
- **27.4 Pipeline:** Run ETL and indicator calculations reproducibly.
- **27.5 Release tags:** Tag baseline and production releases.

### STAGE 28 — VALIDATION AND SCIENTIFIC REVIEW
- **28.1 Internal review:** Technical team checks data and methods.
- **28.2 Field validation:** Validate maps/observations against selected ground-truth sites.
- **28.3 Statistical review:** Check assumptions, sample design, and analytical methods.
- **28.4 External peer review:** Where feasible, invite universities/technical partners to review methods.
- **28.5 Method freeze:** Freeze conference/annual-report methodology and record version.

### STAGE 29 — ACCEPTANCE TESTING AND GO-LIVE
- **29.1 Functional test:** Test collection, ingestion, database, GIS, analysis, dashboard, and reporting end-to-end.
- **29.2 Performance test:** Test map services, database queries, and dashboard response.
- **29.3 Security test:** Test access roles, backups, and audit logs.
- **29.4 User acceptance:** Management and technical users verify required outputs.
- **29.5 Go-live:** Approve production baseline and operational SOPs.

### STAGE 30 — LONG-TERM OPERATIONS AND CONTINUOUS IMPROVEMENT
- **30.1 Monthly:** Review new field submissions, automated feeds, QC failures, and urgent events.
- **30.2 Quarterly:** Review indicators, risk changes, interventions, and dashboard health.
- **30.3 Seasonal:** Review flood/drought/food-security conditions and seasonal hazards.
- **30.4 Annual:** Refresh baseline comparisons, state profiles, MRV, and State of Climate Resilience Report.
- **30.5 Post-event:** After major events, conduct event review and update lessons learned.
- **30.6 Model review:** Periodically review weights, thresholds, indicators, and data sources through change control.

---

## SECTION 31 — 43-LAYER GIS MASTER REGISTER (FEW-CAM ADDENDUM)

| ID | Layer Name | Purpose | Geometry / Format |
|---|---|---|---|
| **G01** | Nigeria_State | Administrative state boundary (10 N-HYPPADEC states) | Polygon / GeoPackage / Vector |
| **G02** | Nigeria_LGA | Administrative LGA boundary (sub-layer G02W holds Wards where available) | Polygon / GeoPackage / Vector |
| **G03** | Communities | Permanent community points / polygons with permanent Community_ID | Point / Polygon |
| **G04** | Households | Privacy-controlled household locations (Level 3 Restricted) | Point (jittered / aggregated) |
| **G05** | River_and_Drainage_Network | Main rivers, tributaries, distributaries, seasonal streams, and drainage channels | Line / Vector |
| **G06** | HydroBasins | Catchment / sub-basin hierarchy (Levels 6–8) | Polygon |
| **G07** | HydroFacilities | Hydropower dams, plants, and related facilities | Point |
| **G08** | Reservoirs | Reservoir and waterbody polygons | Polygon |
| **G09** | DEM | Digital Elevation Model (SRTM / Copernicus 30m) | Raster |
| **G10** | Slope | Terrain slope in degrees (DEC02) | Raster |
| **G11** | Aspect | Terrain aspect (azimuth 0–360°) | Raster |
| **G12** | Hillshade | Analytical terrain visualization surface | Raster |
| **G13** | FlowDirection | D8 hydrological flow direction surface | Raster |
| **G14** | FlowAccumulation | Accumulated upstream drainage area | Raster |
| **G15** | LandCover | Multi-temporal land-cover classes (Copernicus / ESA) | Raster |
| **G16** | OSM_Roads | Primary, secondary, tertiary, and access roads | Line |
| **G17** | OSM_Buildings | Building footprints and settlement extents | Polygon |
| **G18** | OSM_POI | Points of interest (markets, health, schools) | Point |
| **G19** | Infrastructure_Field | Field-observed infrastructure with condition ratings | Point |
| **G20** | Climate_Stations | Monitored climate stations (NiMet, NIHSA, internal) | Point |
| **G21** | Climate_Observations | Station observations time series | Table / Point |
| **G22** | Rainfall_Surface | Interpolated/modelled rainfall surface where justified | Raster |
| **G23** | Temperature_Surface | Temperature surface where justified | Raster |
| **G24** | Flood_Hazard | Modelled flood hazard / susceptibility zones (HMD01–06) | Raster / Vector |
| **G25** | Flood_Observed | Observed flood extents and event polygons | Polygon |
| **G26** | Erosion_Sites | Field-observed erosion locations with Erosion_ID | Point |
| **G27** | Erosion_Hotspots | Derived erosion hotspot surface (KDE / clustering) | Raster / Vector |
| **G28** | Hydro_Water | Hydrological and hydropower operational monitoring | Table / Point |
| **G29** | Flood_Exposure | Flood-exposed population, buildings, roads, and agriculture | Vector / Table |
| **G30** | Erosion_Exposure | Erosion-threatened assets and population | Vector / Table |
| **G31** | Hazard_Index | 0–100 normalized Hazard Index ($H$) | Vector / Raster / Table |
| **G32** | Exposure_Index | 0–100 normalized Exposure Index ($E$) | Vector / Raster / Table |
| **G33** | Vulnerability_Index | 0–100 normalized Vulnerability Index ($V$) | Vector / Raster / Table |
| **G34** | Criticality_Index | 0–100 normalized Criticality Index ($C$) | Vector / Raster / Table |
| **G35** | Composite_Risk | 0–100 Composite Risk score ($R$) | Vector / Table |
| **G36** | Adaptation | Interventions and adaptation measures inventory | Point / Polygon / Table |
| **G37** | Priority_Areas | Management-approved priority tiers and portfolios | Polygon / Vector |
| **G38** | Flood_Alert_Zones | Proposed/released warning extent with release state and confidence | MultiPolygon |
| **G39** | Flood_Warning_Points | Warning observation or monitoring points; no personal contact data | Point |
| **G40** | Community_Awareness_Locations | Community preparedness and awareness activities | Point |
| **G41** | Approved_Evacuation_or_Assembly_Areas | Authority-approved assembly/evacuation polygons only | Polygon |
| **G42** | Historical_Flood_Events | Verified historical flood-event footprints with provenance | MultiPolygon |
| **G43** | Recent_Flood_Extent | Time-stamped observed flood extent, distinct from forecasts/scenarios | MultiPolygon |

> **Note:** The v4.1 base register G01–G37 is extended by FEW-CAM layers G38–G43. Ward boundaries, where available, remain sub-layer `G02W` of `G02_Nigeria_LGA` and are not counted as a separate layer. G05 explicitly includes main rivers, tributaries, distributaries, streams, and drainage channels.

---

## SECTION 32 — CORE DATA TABLES

| Table Name | Primary Key | Main Content & Key Attributes |
|---|---|---|
| **Community_Master** | `Community_ID` | Location, population, climate impacts, services, livelihoods, Ward_ID, LGA_ID, State_Code, Provenance_ID |
| **Household_Survey** | `Household_ID` | Household socioeconomic, losses, food security, adaptation (Level 3 Restricted) |
| **Erosion_Sites** | `Erosion_ID` | Type, severity 0–4, dimensions, exposure, control status, GPS, Provenance_ID |
| **Flood_Events** | `Flood_Event_ID` | Date, extent/depth/duration, source, impacts, confidence, Provenance_ID |
| **Flood_Alerts** | `Alert_ID` | Level 0–3, trigger/rule version, risk/confidence, review/approval/release/cancellation |
| **Flood_Alert_Triggers** | `Trigger_ID` | Source, observation time, measured/threshold value, rule, confidence and provenance |
| **Flood_Alert_Areas** | `Alert_Area_ID` | Affected geometry, State/LGA/community, exposed population/assets and confidence |
| **Flood_Notifications** | `Notification_ID` | Released alert, approved channel/message/language, delivery and reach |
| **Flood_Acknowledgements** | `Acknowledgement_ID` | Notification acknowledgement status, source, community and time |
| **Flood_Awareness** | `Awareness_ID` | Community activity, language, audience, reach, materials and feedback |
| **Flood_Drills** | `Drill_ID` | Preparedness scenario, date, participation, outcome and lessons |
| **Flood_Impacts** | `Impact_ID` | Verified event impacts, losses, service disruption, confidence and provenance |
| **Flood_Warning_Performance** | `Performance_ID` | Lead time, reach, hit/miss/false-alarm, area comparison, coverage and audit completeness |
| **Hydropower_Water** | `Hydro_Record_ID` | Facility_ID, water conditions, head, inflow, outflow, generation/disruption |
| **Climate_Observations**| `Climate_ID` | Station_ID, date, rainfall, temp min/max, source, Provenance_ID |
| **Infrastructure** | `Infrastructure_ID` | Type, condition, exposure, service disruption, Community_ID, Provenance_ID |
| **Food_Security** | `Food_Record_ID` | Production, crop/livestock loss, food access, agricultural exposure, market constraints |
| **Security_Impact** | `Security_Event_ID` | Development impacts: displacement, farm/market/project access, service disruption |
| **Interventions** | `Intervention_ID` | Project/action, target risk, status, budget, baseline condition, outcome metrics |
| **Indicators** | `Indicator_ID` | Definition, formula, computed value, period, source, methodology version |
| **Risk_Assessments** | `Risk_ID` | H, E, V, C, Composite Risk, confidence rating, model version, reference bounds ID |
| **Scenarios** | `Scenario_ID` | Assumptions, climate/land-cover stressors, projected outputs, uncertainty |
| **Ward_Master** *(v4.1)* | `Ward_ID` | Ward name, parent LGA_ID, State_Code, boundary version, validity dates |
| **Facility_Master** *(v4.1)*| `Facility_ID` | Hydropower & related assets: type, capacity, operator, status, linked basin/community |
| **Climate_Station** *(v4.1)*| `Station_ID` | Station metadata, operator/source, coordinates, elevation, operating period |
| **Priority_Areas** *(v4.1)* | `Priority_ID` | Area, component scores & weights, priority tier, confidence, approval status & date |
| **Loss_Damage** *(v4.1)* | `Loss_ID` | Linked event ID, asset/livelihood type, physical quantity, financial value, confidence |
| **Data_Provenance** *(v4.1)*| `Provenance_ID` | Source, acquisition date, processing method, software/model version, analyst |
| **Audit_Trail** *(v4.1)* | `Audit_ID` | Table name, record PK, original value, corrected value, reason, user, timestamp |
| **Data_Confidence** *(v4.1)*| `Confidence_ID` | Record/layer, completeness, recency, source quality, validation status, rating |
| **Lookup_Code** *(v4.1)* | `Lookup_ID` | Controlled vocabularies, units, classes, domains, and dictionary versions |

**Key Relational Links (v4.1):**
1. `Community_Master` carries `Ward_ID` (FK to `Ward_Master`), `LGA_ID`, and `State_Code`.
2. `Hydropower_Water` carries `Facility_ID` (FK to `Facility_Master`).
3. `Climate_Observations` carries `Station_ID` (FK to `Climate_Station`).
4. Every operational table carries `State_Code`, `Community_ID` where applicable, and a `Provenance_ID` (FK to `Data_Provenance`).
5. Material corrections write immutable change entries to `Audit_Trail`.
6. `Risk_Assessments` and `Priority_Areas` reference `Confidence_ID` (to `Data_Confidence`) and model version / reference bounds ID.

---

## SECTION 33 — MASTER INDICATOR FAMILIES

1. **Climate:** Rainfall anomaly, temperature anomaly, extreme rainfall intensity, dry spell frequency, drought / water stress.
2. **Flood:** Frequency, severity, duration, observed extent, exposed population / assets, economic loss.
3. **Erosion:** Severity (0–4), active sites count, hotspot density, infrastructure threat proximity, sedimentation rate.
4. **Hydropower:** Reservoir water levels, generation stability, supply disruption, facility exposure, downstream community effects.
5. **Food Security:** Crop / livestock / fishing losses, food expenditure share, agricultural exposure, market access constraints.
6. **Livelihood:** Income disruption, loss of assets, recovery time, adaptive coping mechanisms.
7. **Community Security:** Conflict-driven displacement, farm access denial, market/service disruption, project execution access constraints.
8. **Infrastructure:** Physical condition, hazard exposure, users affected, service disruption duration.
9. **Adaptation / MRV:** Project coverage, completion rate, Intervention Effectiveness Score (IES), residual risk.
10. **Data Quality:** Completeness, recency, spatial accuracy, source authority, confidence rating.

---

## SECTION 34 — MASTER RISK AND DECISION FORMULAS

### 1. Base Composite Risk
$$R = 0.35H + 0.25E + 0.25V + 0.15C$$

Where:
- $H \in [0, 100]$: Hazard Index (G31)
- $E \in [0, 100]$: Exposure Index (G32)
- $V \in [0, 100]$: Vulnerability Index (G33)
- $C \in [0, 100]$: Criticality Index (G34)
- $R \in [0, 100]$: Composite Risk Score (G35)

### 2. Normalization Rules & Reference Bounds (v4.1)
- **Positive normalization** (higher raw value = higher risk/index):
  $$x_{\text{norm}} = 100 \times \frac{x - \min_{\text{ref}}}{\max_{\text{ref}} - \min_{\text{ref}}}$$
- **Inverse normalization** (higher raw value = lower risk/vulnerability, e.g. adaptive capacity):
  $$x_{\text{norm}} = 100 \times \frac{\max_{\text{ref}} - x}{\max_{\text{ref}} - \min_{\text{ref}}}$$
- **Constant-variable rule:** If $\max_{\text{ref}} = \min_{\text{ref}}$, assign a documented baseline constant (typically 50.0 or 0.0 depending on indicator context) and flag.
- **Normalization Reference Bounds (v4.1):** $\min_{\text{ref}}$ and $\max_{\text{ref}}$ are **fixed reference bounds frozen at the 2026 baseline** (Stage 17.8), registered in `Reference_Bounds_Register`. They are **never** re-computed dynamically from each incoming dataset.
- **Out-of-bounds clipping:** Values where $x < \min_{\text{ref}}$ are clipped to $0.0$; values where $x > \max_{\text{ref}}$ are clipped to $100.0$, and flagged with an audit alert for review.

### 3. Alternative Aggregation Form Check (Stage 17.9)
To ensure that zero exposure does not mathematically produce a high risk score under purely additive combination, compute the geometric/multiplicative alternative:
$$R_{\text{mult}} = H^{0.35} \times E^{0.25} \times V^{0.25} \times C^{0.15}$$
Record rank order correlation ($\rho$) and rank differences between additive and multiplicative forms in the analytical report.

### 4. Intervention Effectiveness Score (IES) (v4.1)
Where verified before/after evidence exists:
$$\text{IES} = \left(\frac{\text{Risk}_{\text{before}} - \text{Risk}_{\text{after}}}{\text{Risk}_{\text{before}}}\right) \times 100\%$$

**IES Validity Rules (v4.1):**
1. $\text{Risk}_{\text{before}}$ and $\text{Risk}_{\text{after}}$ **must** use the identical methodology version and the identical baseline reference bounds.
2. If $\text{Risk}_{\text{before}} = 0$, IES is mathematically undefined and **must** be reported as `N/A` (not applicable).
3. IES can **only** be published with:
   - Documented observation periods (pre- and post-intervention dates)
   - Specified comparison methodology
   - Assigned Data Confidence rating
4. Where causal attribution cannot be formally proven by experimental/quasi-experimental design, the metric **must** be explicitly labelled as `Observed Risk Change`, not causal impact.

### 5. Residual Risk
$$\text{Residual Risk} = \text{Risk}_{\text{after}}$$
Every priority score must preserve the underlying component values ($H, E, V, C$) and weights so executive management can audit the exact driver of high ranking.

---

## SECTION 35 — DATA CONFIDENCE FRAMEWORK

| Confidence Rating | Definition and Minimum Interpretation | Permitted Decision Use |
|---|---|---|
| **High** | Recent, complete, verified, supported by multiple or authoritative primary sources. | Full capital allocation, formal prioritisation, statutory reporting. |
| **Moderate** | Useful for planning and screening, but has material limitations in coverage, recency, or spatial resolution. | Indicative planning, screening, targeted field verification. |
| **Low** | Indicative only; substantial data gaps, unverified third-party reports, or outdated observations. | Trigger for additional field monitoring; **not** for standalone capital allocation. |
| **Unknown** | Evidence insufficient to assign confidence. | Flagged for urgent data collection. |

> **Principle:** Confidence is independent of Risk. A community with High Risk and Low Confidence requires immediate investigative deployment, whereas High Risk with High Confidence warrants immediate engineering/programmatic intervention.

---

## SECTION 36 — MANAGEMENT DECISION PRODUCTS

1. Ten State Climate Resilience Profiles (one standard profile per state).
2. N-HYPPADEC Climate Resilience Atlas (43-layer map folio, including FEW-CAM).
3. Annual State of Climate Resilience Report.
4. Climate-related Loss and Damage Database.
5. Flood and Erosion Hotspot Atlas.
6. Food Security and Livelihood Resilience Dashboard.
7. Community Security and Conflict-Impact Evidence Dashboard (safe aggregates only).
8. Hydropower Climate Risk Profile (Kainji, Jebba, Shiroro, Dadin Kowa, Kashimbila, etc.).
9. Intervention MRV Register and Effectiveness Reports.
10. Residual Risk and Adaptation Gap Map.
11. Priority Intervention Portfolio (Tiers 1 to 4).
12. Climate Early-Warning / Decision-Support Prototype.
13. International Conference Evidence Pack.
14. Data and Methodology Catalogue.

---

## SECTION 37 — INTERNATIONAL-CONFERENCE MINIMUM EVIDENCE STANDARD

1. Every major number has a documented source and reporting period.
2. Every map has a title, legend, scale bar, north arrow, coordinate reference system (WGS84 EPSG:4326), source citation, and publication date.
3. Every modelled output has explicit methodology and declared assumptions.
4. Every scenario is prominently labelled as a *scenario / projection*, never as an unconditioned prediction.
5. Every intervention claim distinguishes outputs (assets built) from outcomes (vulnerability reduced).
6. Every outcome claim states the observation period, comparison baseline, and counterfactual method.
7. Every composite risk score is traceable back to its underlying $H, E, V, C$ indicator components.
8. Every major figure includes a data confidence statement.
9. Data and model limitations are displayed transparently in footnotes/legends.
10. Only approved and safely aggregated community-security information is presented publicly.

---

## SECTION 38 — IMPLEMENTATION WORK-BREAKDOWN STRUCTURE (WBS)

| WP | Work Package Name | Stages | Key Acceptance Output |
|---|---|---|---|
| **WP01** | Governance and Mandate | Stage 1 | Approved institutional mandate, steering charter, privacy SOP |
| **WP02** | Research Framework | Stage 2 | Theory of change, question bank, indicator dictionary, baseline protocol |
| **WP03** | Geography and Identifiers | Stage 3 | 10-state master spatial registry, gazetteer, permanent ID schemas |
| **WP04** | Database Infrastructure | Stage 4 | PostgreSQL/PostGIS schemas (RAW, CLEAN, DERIVED, LOOKUPS), DDL, indexes |
| **WP05** | Field Collection System | Stages 5–6 | KoboToolbox XLSForm master, cascade selects, sampling protocol |
| **WP06** | ETL and Data Quality | Stage 7 | Automated ingestion, validation rules (structural/logical/spatial), promotion logs |
| **WP07** | GIS Implementation | Stage 8 | Complete 43-layer GIS registered and validated in QGIS |
| **WP08** | Earth Observation & RS | Stage 9 | Preprocessed Sentinel/Landsat/DEM imagery, land cover, surface water |
| **WP09** | Hydro-Climate Evidence | Stage 10 | Climate archives, river hydrology time series, hydropower monitoring |
| **WP10** | Flood Intelligence | Stage 11 | Flood hazard model, event catalogue, exposure overlays, alert prototype |
| **WP11** | Erosion Intelligence | Stage 12 | Monitored erosion site registry, field severity, hotspot KDE surfaces |
| **WP12** | Food & Livelihoods | Stage 13 | Agricultural exposure, loss database, food security risk index |
| **WP13** | Community Security Impacts | Stage 14 | Safe development-impact records (displacement, farm access disruption) |
| **WP14** | Adaptation & MRV | Stage 15 | Interventions database, baseline pairs, IES scores, residual risk |
| **WP15** | Indicator & Risk Engine | Stages 16–18 | Reproducible Python calculation pipeline, H/E/V/C indices, composite risk |
| **WP16** | Analytics & Scenarios | Stages 19–21 | Thematic analytics, climate stress scenarios, adaptation scenario comparison |
| **WP17** | Web GIS & Dashboard | Stage 22 | FastAPI service, GeoServer maps, interactive management dashboard |
| **WP18** | Reporting & Conference | Stages 23–24 | 10 State Profiles, Annual Report, International Conference Evidence Pack |
| **WP19** | Security & Continuity | Stages 25–26 | Role-based access control, encryption, 4-tier backup, restore drills |
| **WP20** | Software Engineering & QA | Stages 27–29 | Git repository, Docker containers, automated test suite, UAT sign-off |
| **WP21** | Operations & Improvement | Stage 30 | Operational monitoring calendar (monthly, quarterly, seasonal, annual) |

---

## SECTION 39 — PHASED DELIVERY ROADMAP

| Phase | Scope | Exit Criterion |
|---|---|---|
| **Phase 0** | Governance, requirements, baseline protocol | Mandate, governance charter, and baseline protocol approved by Sponsor |
| **Phase 1** | Geography, IDs, database, Kobo baseline | 10-state baseline architecture operational; schemas deployed; Kobo validated |
| **Phase 2** | GIS, climate, hydrology, flood, erosion | Core evidence layers (G01–G28) populated, validated, and published |
| **Phase 3** | Food security, security impacts, interventions/MRV | Integrated resilience dataset; intervention tracking and loss registers active |
| **Phase 4** | Indicators, risk, confidence, priority | Decision models validated; H/E/V/C and G35/G37 computed reproducibly |
| **Phase 5** | Dashboard, reporting, annual evidence | Management dashboard, 10 state profiles, and conference package signed off |
| **Phase 6** | Scenarios, early-warning prototype, automation | Advanced intelligence capabilities and scenario models validated |
| **Phase 7** | Annual update cycle | Institutional continuous-monitoring service running on established calendar |

---

## SECTION 40 — FINAL END-TO-END ALGORITHM

1. Receive institutional executive mandate.
2. Define governance, roles, and institutional data permissions.
3. Freeze research questions, indicator dictionary, and monitoring framework.
4. Create permanent geography and entity identifiers (`State_Code`, `LGA_ID`, `Ward_ID`, `Community_ID`, `Erosion_ID`, `Facility_ID`, `Station_ID`, `Intervention_ID`).
5. Deploy RAW, CLEAN, DERIVED, and LOOKUPS database schemas in PostgreSQL/PostGIS.
6. Configure standardized KoboToolbox / ODK XLSForm with cascade and skip logic.
7. Conduct field instrument pilot, enumerator training, and tool calibration.
8. Execute stratified field sampling across communities, households, and erosion/infrastructure sites.
9. Ingest all field submissions into immutable RAW landing storage without overwriting.
10. Execute automated structural, logical, spatial, and provenance QC checks.
11. Promote only QC-passed records to CLEAN operational tables; log exclusions.
12. Acquire, preprocess, and register the 37 GIS layers.
13. Acquire and process satellite remote sensing evidence (land cover, NDVI, flood extent).
14. Acquire and homogenize station climate and hydrological time series.
15. Update hydropower facility operations and infrastructure condition records.
16. Update flood event and erosion site catalogues with GPS coordinates and severity scores.
17. Update food-security, livelihood loss, and community security development-impact records.
18. Register N-HYPPADEC interventions and capture pre-implementation baseline conditions.
19. Measure physical intervention outputs and post-implementation outcome metrics.
20. Run indicator calculation scripts against CLEAN data.
21. Normalize indicators using frozen 2026 baseline reference bounds; compute $H, E, V, C$.
22. Calculate composite risk $R = 0.35H + 0.25E + 0.25V + 0.15C$; evaluate multiplicative alternative.
23. Calculate data confidence ratings and model uncertainty bounds.
24. Execute thematic analytics, trend tests, and hotspot analyses.
25. Run plausible scenario simulations (climate stress, adaptation).
26. Generate spatial prioritisation scores and classify priority intervention tiers.
27. Expose approved layers and metrics via FastAPI and GeoServer.
28. Render interactive KPIs and drill-down hierarchy on the management dashboard.
29. Generate 10 State Resilience Profiles, maps, and conference evidence displays.
30. Record executive management decisions and resource allocations.
31. Track project delivery through the MRV module.
32. Calculate Intervention Effectiveness Score (IES) and residual risk.
33. Archive the reporting snapshot in immutable repository storage.
34. Advance monitoring calendar to the next operational cycle and repeat.

---

## SECTION 41 — NON-NEGOTIABLE SCIENTIFIC AND INSTITUTIONAL RULES

1. **No fabricated data, geometry, trends, or impacts.** Every figure must link to raw evidence.
2. **Raw data are never overwritten.** Submissions land immutably in RAW.
3. **Permanent IDs are strictly reused.** Repeat observations append new rows pointing to the identical entity identifier.
4. **Source and processing provenance are mandatory.** Every record links to `Provenance_ID`.
5. **Modelled outputs are explicitly labelled as modelled.**
6. **Correlation is never presented as causation.**
7. **Scenarios are never presented as guaranteed forecasts.**
8. **Risk scores are decision-support indices, not disaster probabilities**, unless separately validated by probabilistic engineering models.
9. **Community security monitoring focuses exclusively on development impacts**, never tactical or military intelligence.
10. **Personally identifiable household information (PII) is strictly restricted** and never published publicly.
11. **Every material methodological modification receives a formal version tag** through change control.
12. **Every published map and conference figure must be fully reproducible** from source data and versioned code.

---

## SECTION 42 — FIRST IMPLEMENTATION TASK LIST

1. Approve this advanced CHER-CDSS scope document.
2. Approve the institutional governance structure and TORs.
3. Approve the 2026 baseline as the formal initial reporting period.
4. Confirm the permanent `Community_ID` and entity-ID policy (`NG-` prefix).
5. Confirm the 43-layer GIS master register, including G05 `River_and_Drainage_Network`.
6. Finalize the master data dictionary and indicator register.
7. Finalize KoboToolbox / XLSForm and conduct field pilot.
8. Deploy PostgreSQL / PostGIS development database with full schema DDL.
9. Load and QA administrative boundaries (10 states, LGAs, wards) and hydrography.
10. Establish RAW, CLEAN, and DERIVED storage directories and backup pipelines.
11. Initiate baseline field survey collection.
12. Establish formal data-sharing agreements for climate, hydrology, and hydropower operational data.
13. Compile the initial flood event and erosion site spatial catalogues.
14. Build food-security and community-security impact analysis modules.
15. Deploy the intervention and MRV registry module.
16. Implement the automated Python indicator, risk, and confidence calculation pipeline.
17. Produce the first 10-state baseline cartographic atlas.
18. Deploy the prototype web GIS and executive management dashboard.
19. Conduct internal technical and scientific validation reviews.
20. Freeze the baseline International Conference Evidence Package following steering sign-off.

---

## SECTION 43 — DEFINITION OF SUCCESS

CHER-CDSS is successful when N-HYPPADEC transitions from fragmented, episodic claims to a **continuous, traceable, spatially explicit, and empirically validated evidence system**. 

The completed platform will enable the Commission to definitively demonstrate:
- Exactly where environmental and climate hazards concentrate across the 10 states.
- How climate variability impacts communities, agriculture, and hydropower facilities.
- How food security and livelihoods are impacted by environmental shocks.
- How community-security constraints interact with baseline resilience.
- What interventions N-HYPPADEC has delivered, where, and at what cost.
- What measurable risk reduction occurred after intervention (IES).
- What residual risk remains requiring sustained commitment.
- Where future capital investments should be prioritized for maximum community resilience.

The 2026 baseline represents the institutional foundation: an enduring capability updated continuously across seasonal, annual, and post-event cycles.

---

## SECTION 44 — RESPONSIBILITY, INPUTS AND ACCEPTANCE MATRIX

### 44.1 Roles Used in This Matrix
- **Sponsor:** Executive Sponsor (Managing Director / Board)
- **STC:** Steering Committee
- **PM\*:** Programme Manager *(proposed addition)*
- **DEV\*:** Software and Database Engineer *(proposed addition)*
- **STAT\*:** Statistician and Risk Modeller *(proposed addition)*
- **RS\*:** Remote Sensing Analyst *(proposed addition)*
- **HCA\*:** Hydro-Climate Analyst *(proposed addition)*
- **MRV\*:** Monitoring, Reporting, and Verification Officer *(proposed addition)*
- **PRIV:** Security and Privacy Focal Person
- **GDM:** GIS and Data Manager
- **FC:** Field Coordinator
- **SFP:** State Focal Persons (10 states)
- **GIS:** GIS Analyst
- **IR\*:** Independent Scientific Reviewers *(proposed addition)*

### 44.2 Responsibility, Tools, Inputs, and Acceptance Matrix

| Stage | Accountable / Responsible | Key Inputs | Tools | Acceptance Criterion | Delivery Phase |
|---|---|---|---|---|---|
| **1. Governance** | **A:** Sponsor<br>**R:** STC, PM | Institutional mandate, legal Act, partner lists | Governance charter, data-sharing register | Signed mandate; named sponsor and system owner; approved TORs, data-sharing register, privacy SOP, and change-control register. | Phase 0 |
| **2. Framework** | **A:** PM<br>**R:** Technical team, STAT | Mandate, past reports, international conventions | Indicator dictionary template | Approved theory of change, question bank, indicator dictionary, 2026 baseline protocol, and monitoring calendar. | Phase 0 |
| **3. Geography & IDs** | **A:** GDM<br>**R:** GDM, SFP | OCHA/HDX boundaries, community gazetteers | QGIS, PostGIS, Python | Zero duplicate `Community_ID`s; all features pass CRS (EPSG:4326), geometry, and point-in-polygon checks; ID registry issued. | Phase 1 |
| **4. Database** | **A:** GDM<br>**R:** DEV | Entity Relationship Diagram, data dictionary | PostgreSQL / PostGIS, SQL, Git, Docker | RAW, CLEAN, DERIVED, LOOKUPS schemas deployed from versioned DDL; constraints and spatial indexes verified; RAW immutability enforced. | Phase 1 |
| **5. Field System** | **A:** FC<br>**R:** GDM, DEV | Indicator dictionary, controlled lookup vocabularies | KoboToolbox / ODK, XLSForm | Master XLSForm validates on ODK validator; cascade logic and skip rules tested; offline and sync-recovery tests passed. | Phase 1 |
| **6. Field Collection** | **A:** FC<br>**R:** SFP, Field Supervisors | Approved XLSForm, sampling frame | Kobo Collect, GPS receivers, Android devices | Training completion records archived; pilot report approved; daily QC logs kept; completeness verified against sampling frame per state. | Phase 1 |
| **7. ETL & QC** | **A:** GDM<br>**R:** DEV | Raw field submissions, validation rule definitions | Python, SQL, GeoPandas | 100% of raw submissions land unchanged in RAW; only QC-validated records reach CLEAN; promotion log and audit trail complete. | Phase 1 |
| **8. GIS** | **A:** GDM<br>**R:** GIS Analyst | CLEAN tabular data, external geospatial layers | QGIS (LTR), GeoServer, GDAL | All 43 layers registered with metadata; every published layer passes spatial QC. G38–G43 remain pending operational sources and publication approval. | Phase 2 |
| **9. Remote Sensing** | **A:** GDM<br>**R:** RS Analyst | Sentinel-2, Landsat-8/9, Copernicus 30m DEM | Google Earth Engine, GDAL, Rasterio | Acquisition register complete; land-cover and water extent products validated against field data; accuracy report meets STC threshold. | Phase 2 |
| **10. Hydro-Climate** | **A:** PM<br>**R:** HCA | NiMet, NIHSA, and hydropower dam logs | Python, SciPy, Statsmodels | Harmonised time series with verified units and timestamps; trend tests executed only where record length meets statistical standards. | Phase 2 |
| **11. Flood** | **A:** PM<br>**R:** HCA, GIS Analyst | DEM, drainage network (G05), flood observations | QGIS, GDAL, Python | Flood event catalogue complete with source and confidence ratings; exposure overlays reproducible; early warning alert prototype validated. | Phase 2 |
| **12. Erosion** | **A:** PM<br>**R:** GIS Analyst, FC | Field erosion surveys, high-res satellite imagery | Kobo, QGIS, GeoPandas | Every monitored site assigned permanent `Erosion_ID`; severity (0–4) and GPS recorded; hotspot KDE method meets minimum sample rules. | Phase 2 |
| **13. Food Security** | **A:** PM<br>**R:** Livelihoods Specialist, STAT | Household surveys, agricultural loss records | Kobo, Python, Pandas | Approved food-security scale; PII pseudonymised; Food Security Risk Index weights formally approved through change control. | Phase 3 |
| **14. Security Impacts** | **A:** PRIV<br>**R:** SFP, Analyst | Verified development-impact event logs | Kobo, PostGIS, Python | Scope strictly verified as development impacts; reported and verified evidence separated; published maps aggregate safely without PII. | Phase 3 |
| **15. Adaptation & MRV** | **A:** MRV Officer<br>**R:** SFP, GIS Analyst | N-HYPPADEC project files, baseline surveys | PostGIS, Kobo, Python | Every project assigned `Intervention_ID` with pre-intervention baseline; outputs and outcomes separated; IES complies with Section 34 rules. | Phase 3 |
| **16. Indicator Engine** | **A:** GDM<br>**R:** STAT, DEV | Indicator register, CLEAN database tables | Python, SQL, Git | Indicators calculated via versioned scripts; unit tests pass against synthetic test cases; calculation methodology versions recorded. | Phase 4 |
| **17. Risk** | **A:** PM<br>**R:** STAT | Normalized indicator scores, reference bounds | Python, PostGIS, Pandas | $H, E, V, C$ normalized on [0, 100] using frozen 2026 reference bounds; composite risk computed; sensitivity and aggregation checks published. | Phase 4 |
| **18. Uncertainty** | **A:** PM<br>**R:** STAT | Risk model outputs, data confidence logs | Python, QGIS | Data confidence rated (High/Mod/Low/Unk) for every community and layer; bivariate risk + confidence maps generated; decision rule approved. | Phase 4 |
| **19. Thematic Analytics** | **A:** PM<br>**R:** HCA, STAT, Analysts | Indicator tables, event catalogues | Python, Matplotlib, Seaborn | Reproducible analytical tables and charts produced for all themes with period notes; no causal assertions unsupported by study design. | Phase 4 |
| **20. Prioritisation** | **A:** STC<br>**R:** PM, STAT | Risk scores, confidence ratings, feasibility data | Python, PostGIS | Prioritisation criteria and weights fully documented and visible; rank orders traceable; 4 priority tiers formally approved. | Phase 4 |
| **21. Scenarios** | **A:** PM<br>**R:** STAT, HCA | Approved scenario assumptions, baseline models | Python, GIS | Scenarios explicitly labelled as projections/experiments; assumptions documented; comparative risk outputs reproducible. | Phase 6 |
| **22. Web GIS & Dashboard**| **A:** PM<br>**R:** DEV, GDM | CLEAN data, approved indicator and risk tables | FastAPI, GeoServer, MapLibre | API, map services, and dashboard meet performance targets in test plan; multi-level drill-down functional; exports include metadata. | Phase 5 |
| **23. Annual Report** | **A:** PM<br>**R:** All Leads | Frozen annual reporting database snapshot | Report templates, QGIS | Ten state profiles and national synthesis published; MRV and data-quality chapters complete; management recommendations signed off. | Phase 5 |
| **24. Conference Pack** | **A:** Sponsor<br>**R:** PM | Frozen methodology and peer-reviewed results | Presentation deck, map boards | Every figure traces to raw source and code; limitations disclosed; 10-point Section 37 evidence standard fully satisfied. | Phase 5 |
| **25. Security & Privacy** | **A:** PRIV<br>**R:** DEV, GDM | RBAC specification, ethics and privacy SOP | PostgreSQL roles, TLS, audit logs | Role-based access control active; database encrypted; access and export audit logs functioning; zero PII in public outputs. | Phase 1 onward |
| **26. Backup & Continuity**| **A:** GDM<br>**R:** DEV | 4-tier backup policy, DR plan | Automated backup tooling, off-site storage | Automated daily backups operating; off-site replica verified; successful end-to-end restore drill documented before production freeze. | Phase 1 onward |
| **27. Software Engineering**| **A:** GDM<br>**R:** DEV | Source code, configuration files, environment specs | Git, Docker, Pytest | Entire analytical pipeline builds and executes reproducibly from clean git checkout; test suite passes; baseline release tagged. | Phase 1 onward |
| **28. Validation Review** | **A:** STC<br>**R:** IR, STAT | Draft outputs, ground-truth field data | Review checklists, audit forms | Internal technical, field ground-truth, and statistical review reports closed; final baseline methodology frozen. | Phases 4–5 |
| **29. Acceptance & Go-Live**| **A:** Sponsor<br>**R:** PM, User Representatives | Formal system test plans, acceptance criteria | Test scripts, sign-off forms | Functional, performance, and security acceptance tests passed; formal UAT signed by stakeholders; production go-live approved. | Phase 5 |
| **30. Long-Term Operations**| **A:** System Owner<br>**R:** GDM, PM | Monitoring calendar, update SOPs | Automated pipeline, dashboard | Monthly, quarterly, seasonal, and annual evidence deliverables generated on schedule; change-control log maintained. | Phase 7 |

### 44.3 Management Decisions Required (Not Fixed in This Scaffold)
1. Calendar dates and durations for Phases 0 through 7.
2. Programme budget, procurement mechanisms, and funding allocations.
3. Institutional staffing allocations and whether proposed roles (\*) are fulfilled by permanent staff, secondees, or technical partners.
4. Production hosting architecture (on-premises secure server vs sovereign cloud) and statutory data-residency compliance.
5. Statistical sample sizes and precision targets for field survey modules (Stage 6.1), and dashboard load/response performance thresholds (Stage 29.2).
6. Formal Steering Committee approval of risk weights ($0.35, 0.25, 0.25, 0.15$), priority weights, and confidence rubrics (Stages 17, 18, 20).

### 44.4 Open Verification Items
1. Confirm the 10 state names against the N-HYPPADEC establishment Act prior to baseline freeze.
2. Confirm the exact QGIS Long-Term-Release (LTR) version to be pinned in the build environment specification.
3. Formalize the entity ID prefix policy (`NG-` prefix, e.g. `NG-NIG-...`) and the authoritative source for Ward boundary codes (`Ward_ID`).

---
*CHER-CDSS Advanced Master Implementation Scaffold v4.1 — Authoritative Institutional Implementation Blueprint*
