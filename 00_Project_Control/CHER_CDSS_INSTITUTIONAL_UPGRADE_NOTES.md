# CHER-CDSS Institutional Upgrade Notes
## From Research Baseline to Permanent Institutional Infrastructure

**Version:** v1.0 | **Date:** 2026-10-02  
**Reference:** CHER-CDSS Master Institutional Implementation Guide (2026)

---

## 1. Purpose of This Document

The current system (Phases 1–10) is built as a file-based research baseline
using CSV data, GeoPackage GIS files, and Python scripts. It is a complete,
fully functional decision-support system for the 2026 baseline.

The CHER-CDSS Institutional Implementation Guide defines the path to convert
this into a **permanent institutional infrastructure** for N-HYPPADEC.

This document maps the current system to the institutional upgrade path,
identifies what exists, what needs to be added, and what the priorities are.

---

## 2. Geography Note (Resolved in v4.1)

The system is now fully aligned with **CHER-CDSS Advanced Master Implementation Scaffold v4.1**:
The ten confirmed N-HYPPADEC member states are:
**Niger (`NIG`), Kebbi (`KEB`), Plateau (`PLA`), Benue (`BEN`), Kogi (`KOG`), Kwara (`KWA`), Kaduna (`KAD`), Nasarawa (`NAS`), Taraba (`TAR`), Gombe (`GOM`)**.

- Internal state codes: `NIG`, `KEB`, `PLA`, `BEN`, `KOG`, `KWA`, `KAD`, `NAS`, `TAR`, `GOM`
- Entity ID prefix: `NG-` (e.g., `NG-NIG-...`, `NG-KEB-...`)
- `LKP_States.csv` and `LKP_LGAs.csv` have been updated with all 10 states and 186 LGAs.
- Permanent hierarchy: $\text{State} \longrightarrow \text{LGA} \longrightarrow \text{Ward (sub-layer G02W)} \longrightarrow \text{Community} \longrightarrow \text{Site / Facility / Household / Observation}$.
- Master specification: `00_Project_Control/CHER_CDSS_ADVANCED_MASTER_IMPLEMENTATION_SCAFFOLD_v4.1.md`.

---

## 3. Current State vs Institutional Target

| Component | Current Baseline (File-Based) | Institutional Target (CHER-CDSS) | Priority |
|---|---|---|---|
| Database | CSV files in 03_Data/ | PostgreSQL + PostGIS central database | High |
| Field collection | Manual CSV entry / templates | KoboToolbox / ODK Collect + API | High |
| GIS | GeoPackage files + QGIS | QGIS + PostGIS; GeoServer when ready | Medium |
| Version control | VERSION_LOG.csv + file naming | Git + PostgreSQL audit tables | Medium |
| Analysis | Python pipeline (run_pipeline.py) | Same Python pipeline + PostGIS queries | Low (already done) |
| Dashboards | CSV/GeoJSON exports for QGIS | Web dashboard (Grafana/Metabase/custom) | Medium |
| Web GIS | Not yet | GeoServer + Leaflet/MapLibre | Low (phase 2) |
| Intervention tracking | Not yet | Intervention module (Section 17 CHER-CDSS) | High |
| Remote sensing | Documented but not automated | Google Earth Engine workflows | Medium |
| Security | File-level access | Role-based PostgreSQL + VPN | High |
| Mobile field collection | Paper/CSV | KoboToolbox offline forms | High |

---

## 4. PostgreSQL / PostGIS Migration

### 4.1 Why migrate

The current CSV-based system is fully functional for the research baseline.
PostgreSQL/PostGIS becomes necessary when:
- Multiple users need simultaneous write access
- Mobile field data arrives continuously via API
- Spatial joins need to run at scale on large datasets
- Audit trails and row-level versioning are required
- Dashboard and web GIS tools need live data connections

### 4.2 Migration approach

The current CLEAN CSVs map directly to PostgreSQL tables.
No schema redesign is needed — the column definitions in `03_Data/CLEAN/DB0*_SCHEMA.csv`
are the PostgreSQL table definitions.

**Step-by-step migration:**

```sql
-- 1. Create database and enable PostGIS
CREATE DATABASE cher_cdss;
\c cher_cdss
CREATE EXTENSION postgis;

-- 2. Create schemas matching the current directory structure
CREATE SCHEMA raw;
CREATE SCHEMA clean;
CREATE SCHEMA derived;
CREATE SCHEMA lookups;

-- 3. Example: create DB01 community master table
CREATE TABLE clean.community_master (
    community_id       VARCHAR(12) PRIMARY KEY,
    community          VARCHAR(100) NOT NULL,
    state_code         VARCHAR(6) NOT NULL REFERENCES lookups.states(state_code),
    state_name         VARCHAR(50) NOT NULL,
    lga_code           VARCHAR(10) NOT NULL REFERENCES lookups.lgas(lga_code),
    lga                VARCHAR(60) NOT NULL,
    latitude           DOUBLE PRECISION NOT NULL,
    longitude          DOUBLE PRECISION NOT NULL,
    gps_accuracy_m     DOUBLE PRECISION NOT NULL,
    survey_date        DATE NOT NULL,
    population         INTEGER,
    livelihood         VARCHAR(5) REFERENCES lookups.livelihood(livelihood_code),
    electricity_access VARCHAR(7),
    water_source       VARCHAR(5),
    flood_experience   VARCHAR(7),
    erosion_presence   VARCHAR(7),
    hydropower_distance DOUBLE PRECISION,
    adaptation_status  VARCHAR(5),
    photo_id           VARCHAR(50),
    notes              TEXT,
    record_created     DATE NOT NULL DEFAULT CURRENT_DATE,
    record_modified    DATE,
    data_version       VARCHAR(10) NOT NULL DEFAULT 'v1.0',
    qc_status          VARCHAR(12) NOT NULL DEFAULT 'RAW',
    -- PostGIS geometry column
    geom               GEOMETRY(POINT, 4326)
);

-- 4. Load existing CLEAN CSV data
COPY clean.community_master
FROM '/path/to/03_Data/CLEAN/DB01_Community_Master_CLEAN.csv'
CSV HEADER;

-- 5. Populate geometry from lat/lon
UPDATE clean.community_master
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

-- 6. Create spatial index
CREATE INDEX idx_community_master_geom
ON clean.community_master USING GIST(geom);
```

### 4.3 Python pipeline adaptation

The pipeline scripts need one configuration change to switch from CSV to PostgreSQL.
In `config.py`, add:

```python
# PostgreSQL connection (loaded from environment variables — never hardcode)
import os
PG_CONNECTION = {
    "host":     os.environ.get("CHER_DB_HOST", "localhost"),
    "port":     int(os.environ.get("CHER_DB_PORT", 5432)),
    "database": os.environ.get("CHER_DB_NAME", "cher_cdss"),
    "user":     os.environ.get("CHER_DB_USER"),
    "password": os.environ.get("CHER_DB_PASSWORD"),
}
USE_POSTGRES = os.environ.get("CHER_USE_POSTGRES", "false").lower() == "true"
```

Each module then uses `pd.read_sql()` instead of `pd.read_csv()` when
`USE_POSTGRES = True`. The analytical logic is identical — only the data
source changes. This allows the system to run in file mode (current) or
PostgreSQL mode (institutional) with the same scripts.

---

## 5. KoboToolbox / ODK Field Data System

### 5.1 Forms to build

Based on CHER-CDSS Section 8.1, six forms are required:

| Form | Maps to | Priority |
|---|---|---|
| Community Monitoring | DB01 | High — deploy first |
| Erosion Site Monitoring | DB03 | High |
| Infrastructure Monitoring | DB06 | High |
| Hydropower/Water Observation | DB04 | High |
| Household Survey | DB02 (RESTRICTED) | Medium |
| Intervention Monitoring | New — see Section 6 below | Medium |

### 5.2 Field form design rules

Each form must:
- Use the **exact same field names** as the corresponding DB schema CSV
- Use **controlled choice lists** for all coded fields (loaded from LKP_ lookup tables)
- Capture GPS in WGS84 decimal degrees with accuracy recorded
- Capture a photograph with linked Photo_ID
- Work **offline** (no connectivity required in field)
- Be **versioned** — form changes documented before deployment; old submissions preserved

### 5.3 ETL pipeline (Kobo → CHER-CDSS)

```
Kobo/ODK submission
        ↓
KoboToolbox API (JSON) or ODK Central API
        ↓  [01_ingest.py — Kobo ingestion module]
RAW storage (03_Data/RAW/kobo_submissions/)
        ↓  [02_validate.py]
Structural + referential + coordinate QC
        ↓  [03_clean.py]
CLEAN storage → PostgreSQL clean schema
        ↓  [04_integrate.py]
Spatial joins + permanent ID assignment
        ↓
Domain processing (05–15)
```

Add to `01_ingest.py`:

```python
import requests, json

def ingest_from_kobo(form_id: str, kobo_token: str) -> pd.DataFrame:
    """Pull new submissions from KoboToolbox API."""
    url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_id}/data.json"
    headers = {"Authorization": f"Token {kobo_token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    submissions = resp.json()["results"]
    df = pd.json_normalize(submissions)
    log.info(f"Kobo: {len(df)} submissions pulled from form {form_id}")
    return df
```

---

## 6. Intervention Monitoring Module

This module does not yet exist in the current system. It is required for the
institutional CHER-CDSS (Section 17 of the guide).

### 6.1 Database table: DB07 — Interventions

**Primary key:** Intervention_ID (format: INT-YYYY-NNNN, e.g. INT-2026-0001)

| Field | Type | Description |
|---|---|---|
| Intervention_ID | Text | Permanent intervention identifier |
| Community_ID | Text | FK → DB01 |
| Erosion_ID | Text | FK → DB03 (if erosion intervention) |
| Infrastructure_ID | Text | FK → DB06 (if infrastructure intervention) |
| Intervention_Type | Text | Erosion control / Flood barrier / Drainage / Livelihood / Other |
| Description | Text | What was done |
| Problem_Addressed | Text | Specific problem targeted |
| Start_Date | Date | |
| End_Date | Date | |
| Status | Text | Planned / In progress / Completed / Cancelled |
| Implementing_Unit | Text | N-HYPPADEC unit responsible |
| Partners | Text | Co-implementing organisations |
| Before_Condition | Text | Condition before intervention (linked to DB03/DB06 record) |
| After_Condition | Text | Condition after intervention (new DB03/DB06 observation) |
| Before_Photo_ID | Text | Pre-intervention photograph |
| After_Photo_ID | Text | Post-intervention photograph |
| Beneficiaries_Count | Integer | People directly benefiting |
| Outcome_Measured | Text | Yes / No / Pending |
| Outcome_Summary | Text | What changed |
| Notes | Text | |

### 6.2 Intervention questions (per CHER-CDSS Section 17)

| Stage | Questions answered |
|---|---|
| Before | What was the condition? Who was exposed? What was the risk score? |
| Intervention | What was done, where, when, by whom? |
| Immediate | Was it completed and functional? |
| Outcome | Did exposure / severity / disruption / vulnerability change? |
| Long-term | Has the improvement been maintained? What remains unresolved? |

### 6.3 Script: 19_interventions.py (to be built)

```python
"""
19_interventions.py
===================
Future module: Intervention tracking and outcome measurement.
Links N-HYPPADEC interventions to pre/post DB03/DB06/G35 records.
Computes outcome indicators: ΔR_Score; ΔSeverity; ΔDisruption.
"""
# Placeholder — to be implemented in institutional deployment phase
```

---

## 7. Management Dashboard

### 7.1 What the dashboard must show

Based on CHER-CDSS Section 19.1:

| Panel | Data source | Update frequency |
|---|---|---|
| Ten-state risk overview map | G35 + G37 | At each pipeline run |
| Priority areas — Tier 1 communities | G37 | At each pipeline run |
| Current major flood/erosion events | G25 + G26 + FLAG_Register | Continuous |
| Risk distribution by state | 06_Reports/02_TABLES/ | At each pipeline run |
| Hydropower/water indicators | G28 + IND08 | Monthly |
| Intervention status | DB07 (when built) | At milestones |
| Data freshness indicator | PROCESSING_STATUS.csv | Daily |
| Data completeness by state | G35 completeness fields | At each pipeline run |

### 7.2 Current output files usable by any dashboard tool

These files produced by the current pipeline are immediately usable by
Grafana, Metabase, Power BI, or a custom web dashboard:

| File | Dashboard use |
|---|---|
| `G35_CompositeRisk.csv` | Risk score map + distribution charts |
| `G37_PriorityAreas.csv` | Priority ranking table + tier map |
| `G37_Top20_Priority_Communities.csv` | Management top-priorities table |
| `TABLE_State_Summaries.csv` | State comparison chart |
| `TABLE_Descriptive_Statistics.csv` | Summary statistics panel |
| `TABLE_Risk_Distribution_by_State.csv` | Risk distribution bar chart |
| `FLAG_Register_[date].csv` | Alert panel |
| `Community_Risk_MapData_v1_0.geojson` | Interactive web map (Leaflet/MapLibre) |

### 7.3 Recommended dashboard stack

| Component | Tool | Notes |
|---|---|---|
| Data storage | PostgreSQL + PostGIS | After migration |
| Charts/tables | Grafana or Metabase | Connect directly to PostgreSQL |
| Web map | GeoServer + Leaflet or MapLibre | Serve G35/G37 as WMS/WFS |
| API layer | FastAPI | Expose data to dashboard and mobile apps |
| Deployment | Docker | Reproducible; easy staff handover |

---

## 8. Remote Sensing Integration

Per CHER-CDSS Section 12, the following remote sensing workflows should be
added as the system matures:

| Product | Source | Frequency | Script to add |
|---|---|---|---|
| Land cover update | ESA WorldCover / Sentinel-2 | 1–3 years | 20_landcover.py |
| NDVI / vegetation condition | Sentinel-2 | Monthly/seasonal | 21_vegetation.py |
| Flood extent (event) | Sentinel-1 SAR | Post-event | 22_flood_extent.py |
| Riverbank change detection | Sentinel-2 / Landsat | Annual | 23_riverbank.py |
| Agricultural exposure | Sentinel-2 | Seasonal | 24_agriculture.py |

Processing via Google Earth Engine (GEE):
- GEE scripts export derived products as GeoTIFFs
- Products ingested into `04_GIS/01_RAW/` via `01_ingest.py`
- Same QC pipeline applied as for any new source layer
- `earth_engine/` subfolder in `05_Analysis/02_SCRIPTS/` for GEE scripts

---

## 9. Non-Negotiable Long-Term Principles

From CHER-CDSS Section 31 — these apply permanently:

| Principle | Rule |
|---|---|
| History | Never overwrite historical observations |
| Data separation | Never mix raw and derived data |
| Identifiers | Never use community names as primary keys |
| Privacy | Never publish confidential household coordinates |
| Model integrity | Never change risk methodology without versioning |
| Remote sensing | Never treat satellite estimates as field measurements without validation |
| Causation | Never treat correlation as proof of causation |
| Spreadsheets | Never let undocumented spreadsheets become parallel authoritative databases |
| Dependency | Never let the system depend on one staff member |
| Documentation | Always document enough for another trained team to operate the system |

---

## 10. Immediate Next Actions for Institutional Deployment

From CHER-CDSS Section 34, adapted to current state:

| # | Action | Who | When |
|---|---|---|---|
| 1 | Confirm authoritative N-HYPPADEC state list (geography reconciliation) | Executive management | Before production |
| 2 | Approve this system as the institutional reference and assign CHER-CDSS Coordinator | Executive Sponsor | Before production |
| 3 | Confirm institutional ownership; nominate technical roles (Section 5 of guide) | Management | Immediately |
| 4 | Set up PostgreSQL/PostGIS development environment | System Administrator | Month 1 |
| 5 | Finalize and test KoboToolbox/ODK forms (DB01/DB03/DB06/DB04 forms first) | Data Manager + Field Team | Month 1–2 |
| 6 | Build Kobo → ETL ingestion pipeline in 01_ingest.py | GIS Officer + Analyst | Month 2 |
| 7 | Load and quality-check the 2026 baseline research data into PostgreSQL | Data Manager | Month 2–3 |
| 8 | Run system acceptance tests (SYSTEM_ACCEPTANCE_TESTS.md) against PostgreSQL | All technical roles | Month 3 |
| 9 | Build intervention monitoring module (DB07 + 19_interventions.py) | Statistical Analyst | Month 3–4 |
| 10 | Build management dashboard prototype | GIS Officer + Analyst | Month 4–5 |
| 11 | Establish backup, security, and version control procedures | System Administrator | Month 1 (parallel) |
| 12 | Complete staff training on all system components | CHER-CDSS Coordinator | Month 4–6 |
| 13 | Run controlled pilot in 2–3 communities before full rollout | Field Team | Month 5 |
| 14 | Approve operational update schedule (MONITORING_LOGIC.md) | Management | Month 5 |
| 15 | Full institutional rollout to all confirmed member states | All roles | Month 6+ |
