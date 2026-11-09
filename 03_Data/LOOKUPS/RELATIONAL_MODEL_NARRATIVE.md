# Master Relational Model
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Core Hierarchy

The system's primary organising hierarchy flows from administrative units down to field observations:

```
NIGERIA
  └── STATE  (10 target states — LKP_States.csv)
        └── LGA  (LKP_LGAs.csv → G02)
              └── COMMUNITY  (DB01 → G03)
                    ├── HOUSEHOLDS  (DB02 → G04 RESTRICTED)
                    ├── EROSION SITES  (DB03 → G26)
                    ├── INFRASTRUCTURE  (DB06 → G19)
                    └── ADAPTATION RECORDS  (DB01 + DB06)
```

---

## 2. Asset Relationships (Separate Hierarchy)

Hydropower and climate assets have their own hierarchies that link to the community hierarchy spatially:

```
HYDROPOWER FACILITY  (G07)
  ├── RESERVOIR  (G08 — one per facility)
  ├── WATER/GENERATION OBSERVATIONS  (DB04 → G28 — many per facility over time)
  └── COMMUNITY RELATIONSHIPS  (via BUF004 10km buffer — SJ06)

CLIMATE STATION  (G20)
  └── CLIMATE OBSERVATIONS  (DB05 — many per station over time)
```

---

## 3. Key Foreign Key Rules

| Child | Foreign Key | Parent | Rule |
|---|---|---|---|
| DB01 | State_Code | LKP_States | Must resolve |
| DB01 | LGA_Code | LKP_LGAs | Must resolve + consistent with State_Code |
| DB02 | Community_ID | DB01 | Must resolve — no orphan households |
| DB03 | Community_ID | DB01 | Must resolve — assigned via SJ12 |
| DB04 | Hydro_ID | G07 | Must resolve — G07 must exist first |
| DB05 | Station_ID | G20 | Must resolve — G20 must exist first |
| DB06 | Community_ID | DB01 | Must resolve — assigned via SJ11 |
| G08 | Hydro_ID | G07 | Must resolve — no orphan reservoirs |

---

## 4. DB-to-GIS Synchronisation Rules

Every field database has a direct GIS counterpart. These must stay in sync:

| Database | GIS Layer | Sync Key | Sync Direction |
|---|---|---|---|
| DB01 Community Master | G03 Communities | Community_ID | DB01 → G03 (GIS derived from DB01 GPS) |
| DB02 Household Survey | G04 Households (RESTRICTED) | Household_ID | DB01 → G04 (RESTRICTED) |
| DB03 Erosion Sites | G26 Erosion Sites | Erosion_ID | DB03 → G26 |
| DB04 Hydro/Water Obs | G28 Hydro Observations | Hydro_ID + Observation_Date | DB04 → G28 |
| DB06 Infrastructure | G19 Field Infrastructure | Infrastructure_ID | DB06 → G19 |

**Rule:** When a new record is added to a database, its corresponding GIS layer must be updated in the same processing cycle. Do not publish GIS layers that are out of sync with their source database.

---

## 5. Derived Field Rules

Some fields in databases are calculated by GIS scripts — not entered in the field:

| Field | Database | Source | Script |
|---|---|---|---|
| Hydropower_Distance | DB01 | G07 via BUF004 buffer | 04_integrate.py |
| River_Distance_m | DB03, DB06 | G05 via nearest-feature | 04_integrate.py |
| Community_ID | DB03 | G03 via SJ12 spatial join | 04_integrate.py |
| Community_ID | DB06 | G03 via SJ11 spatial join | 04_integrate.py |
| HYBAS_ID | DB01 | G06 via SJ03 | 04_integrate.py |
| Flood_Exposure (GIS-validated) | DB06 | G29 | 09_exposure.py |
| Erosion_Exposure (GIS-validated) | DB06 | G30 | 09_exposure.py |

**Rule:** Derived fields must never be manually edited after calculation. If the source GIS layer changes, the derived field must be recalculated by rerunning the relevant script.

---

## 6. Lookup Table Relationships

All coded fields across all six databases must resolve to a lookup table:

| Lookup Table | Used By |
|---|---|
| LKP_States.csv | DB01, DB02 (via Community_ID), DB03 (via Community_ID), DB04, DB05, DB06 |
| LKP_LGAs.csv | DB01, DB04, DB06 |
| LKP_Livelihood.csv | DB01, DB02 |
| LKP_ErosionType.csv | DB03 |
| LKP_ErosionSeverity.csv | DB03, DB04, DB06 |
| LKP_InfrastructureType.csv | DB06 |
| LKP_WaterSource.csv | DB01, DB02 |
| LKP_AdaptationStatus.csv | DB01, DB02 |
| LKP_OperatingStatus.csv | DB04, G07 |
| LKP_QC_Status.csv | DB01, DB02, DB03, DB04, DB05, DB06 |

---

## 7. Privacy Boundaries

```
LEVEL 3 RESTRICTED
  └── DB02 Household Survey  (all fields)
  └── G04 Household GIS layer  (all fields)
        │
        ▼ Aggregation gate (PRIV07 checklist)
        │
LEVEL 2 TEAM
  └── All other databases and GIS layers
        │
        ▼ Publication approval gate
        │
LEVEL 1 PUBLIC
  └── Approved outputs only (community-level aggregations, generalised maps)
```

No Level 3 data may cross the aggregation gate without PI approval and PRIV07 sign-off.

---

## 8. Update Rule

When a new observation is added to any database:

1. Insert as a **new dated record** — do not overwrite existing records
2. Assign a new unique primary key
3. Set QC_Status = RAW
4. Run the QC pipeline for that database
5. On QC pass: set QC_Status = CLEAN
6. Recalculate only the **dependent derived products** (see build dependency order)
7. Run QC on derived products
8. Publish new version; archive previous version
9. Update VERSION_LOG.csv and PROCESSING_STATUS.csv

**Never overwrite a previously published record. New observation = new record.**

---

## 9. Build Dependency Order (Database Phase)

```
LKP_States + LKP_LGAs (must exist first)
        ↓
DB01 Community Master (CLEAN)
        ↓
DB02 Household Survey (CLEAN) ─── parallel ─── DB03 Erosion Sites (CLEAN)
                                                         │
                                               DB06 Infrastructure (CLEAN)
        ↓
G07 Hydropower Facilities (CLEAN) ─── then ─── DB04 Hydropower/Water (CLEAN)
        ↓
G20 Climate Stations (CLEAN) ─── then ─── DB05 Climate Observations (CLEAN)
```

---

*Version controlled: see VERSION_LOG.csv for change history.*
