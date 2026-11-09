# RESEARCH DESIGN: 2026 BASELINE PROTOCOL
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System (CHER-CDSS)
### N-HYPPADEC / Ten Member States of Nigeria
**Document ID:** `RD-BP-2026-v4.1` | **Stage:** 2.4 | **Status:** Approved Baseline  
**Governing Specification:** CHER-CDSS Master Implementation Scaffold v4.1 (October 2026)

---

## 1. Executive Protocol Freeze Notice

This document establishes the official **2026 Baseline Protocol** for the CHER-CDSS platform. The 2026 baseline serves as the **permanent reference benchmark** against which all future environmental changes, disaster occurrences, and N-HYPPADEC capital interventions will be measured across the ten member states.

- **Baseline Period:** 2026 Quarter 3 – Quarter 4 (Wet Season Peak to Post-Flood Recession)
- **Official Data Cut-off Date:** **October 31, 2026, 23:59:59 WAT**
- **Methodology Version:** `CHER-CDSS-Methodology-v4.1`
- **Model Signature:** `Risk_Model_v4.1`
- **Spatial Reference System:** `EPSG:4326` (WGS 84 geographic) / Projected: `EPSG:32632` (UTM Zone 32N)

---

## 2. Core Baseline Invariants & Locking Rules

To prevent data drift and guarantee longitudinal comparability over the 10-year institutional mandate:

### Rule 1: Normalization Reference Bounds Freeze
All indicator normalization minimums ($\min_{\text{ref}}$) and maximums ($\max_{\text{ref}}$) are permanently locked as defined in `00_Project_Control/REFERENCE_BOUNDS_REGISTER.csv`.
- Under no circumstances shall incoming annual datasets dynamically re-calculate min and max values.
- New observations exceeding bounds are clamped to $[0.0, 100.0]$ with an automated audit alert flag (`Audit_Trail`).

### Rule 2: Permanent Entity Identifiers
All entity identifiers created during the 2026 cycle are permanent and immutable:
- States: `NG-NIG`, `NG-KEB`, `NG-PLA`, `NG-BEN`, `NG-KOG`, `NG-KWA`, `NG-KAD`, `NG-NAS`, `NG-TAR`, `NG-GOM`
- Communities: `COM-SSS-LLL-NNNN` (e.g. `COM-NIG-001-0001`)
- Erosion Sites: `ERO-SSS-LLL-NNNN`
- Facilities: `FAC-SSS-NNNN`
- Climate Stations: `STA-SSS-NNNN`
- Interventions: `INT-SSS-YYYY-NNNN`

### Rule 3: Separation of Raw Ingestion & Analytical Promotion
1. **Raw Landing Immutability:** Raw field submissions, satellite GeoTIFFs, and station rainfall records land in `03_Data/RAW/` and PostgreSQL schema `raw` with append-only permissions.
2. **Promotion Gate:** Only records passing structural, referential, spatial, and logical QC (Q01–Q20) are promoted to `03_Data/CLEAN/` and schema `clean`.
3. **Audit Trail Logging:** Any post-ingestion clerical correction must write an entry to `Audit_Trail` detailing table, primary key, old value, new value, justification, authorized user, and timestamp.

---

## 3. Baseline Data Inventory (Frozen October 2026)

| Asset ID | Domain | Baseline Entity Count | Geographic Coverage | Quality Assurance Status |
|:---|:---|:---:|:---|:---:|
| `DB01` | Sentinel Communities | 50 Communities | All 10 States (5 per state) | 100% Passed (Clean) |
| `DB02` | Household Survey | 250 Households | Stratified sample (Level 3 Restricted) | 100% Passed (Consented) |
| `DB03` | Monitored Erosion Sites | 75 Active Sites | Riparian & escarpment gullies | 100% GPS Validated |
| `DB04` | Hydropower Facilities | 36 Operational Records| Kainji, Jebba, Shiroro, Dadin Kowa, etc. | Operator Cross-checked |
| `DB05` | Climate Station Time-Series | 240 Monthly Records | NiMet synoptic & internal stations | Homogenized & Validated |
| `DB06` | Critical Infrastructure Assets| 100 Field Facilities | Water points, bridges, schools, health | Condition Graded (1–5) |
| `G01–G37`| Master GIS Layers | 37 Authoritative Layers| Full coverage across 10 States | Standardized EPSG:4326 |

---

## 4. Change Control & Re-Baseline Protocols

Modifications to the baseline are governed by the Steering Committee Change Control Board:
1. **Minor Errata (Type 1):** Coordinate correction (<100m) or spelling fix — Logged in `Audit_Trail`, version updated (e.g. `v4.1.1`).
2. **Methodological Adjustment (Type 2):** Adding an indicator or recalibrating risk weights ($H, E, V, C$) — Requires formal Steering Committee approval. All prior annual cycles must be retroactively recalculated using the new weights to maintain longitudinal trend validity.
3. **Comprehensive Re-baselining (Type 3):** Scheduled every five years (2031 Horizon). Involves full re-census of reference bounds and universal field re-enumeration.

---
*Ratified by N-HYPPADEC Project Directorate & Steering Committee — October 2026*
