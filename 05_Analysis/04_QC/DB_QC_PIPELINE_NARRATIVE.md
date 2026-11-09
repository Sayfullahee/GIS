# Database QC Pipeline
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Pipeline Overview

Every production dataset passes through a 20-step QC pipeline before it can be
published or used in derived analytical products. The pipeline maps directly to
the specification's Q01–Q10 framework and extends it with system-specific checks.

```
RAW DATA INGESTED
      ↓
[Q01] Structure check
      ↓
[Q02] Completeness check
      ↓
[Q03] Uniqueness check
      ↓
[Q04] Referential integrity — parent tables
      ↓
[Q17] Referential integrity — lookup tables
      ↓
[Q05] Coordinate validity
      ↓
[Q07] Temporal validity
      ↓
[Q08] Logical consistency
      ↓
[Q09] Range validity
      ↓
[Q10] Missing vs zero
      ↓
[Q19] Consent verification (DB02 only)
      ↓
STATUS = CLEAN (if no critical failures)
      ↓
[Q06] Spatial validation (requires G01/G02)
      ↓
[Q16] Cross-database consistency
      ↓
[Q18] Spatial join completeness
      ↓
[Q20] Geometry–attribute sync
      ↓
[Q12] Provenance
      ↓
[Q13] Version control
      ↓
[Q14] Enumerator QC (DB02 only)
      ↓
[Q15] Time-series consistency (DB04/DB05)
      ↓
[Q11] Privacy check (DB02/G04 outputs only)
      ↓
STATUS = VALIDATED
      ↓
PUBLISHED
```

---

## 2. Critical vs Advisory Checks

### Critical — block publication on failure

| Code | Check |
|---|---|
| Q01 | Structure |
| Q02 | Completeness (required fields) |
| Q03 | Uniqueness (primary keys) |
| Q04 | Referential integrity — parent tables |
| Q05 | Coordinate validity |
| Q07 | Temporal validity |
| Q10 | Missing vs zero |
| Q11 | Privacy (DB02 outputs) |
| Q17 | Referential integrity — lookup tables |
| Q19 | Consent verification (DB02) |
| Q20 | Geometry–attribute sync |

### Advisory — flag and resolve but do not auto-block

| Code | Check |
|---|---|
| Q08 | Logical consistency |
| Q09 | Range validity |
| Q12 | Provenance |
| Q13 | Version control |
| Q14 | Enumerator QC |
| Q15 | Time-series consistency |
| Q16 | Cross-database consistency |
| Q18 | Spatial join completeness |

Advisory failures must be documented in the QC report and resolved or
explicitly accepted by the data manager before VALIDATED status is assigned.

---

## 3. QC Status Transitions

```
RAW → INGESTED (source registered in SOURCE_REGISTER.csv)
    → VALIDATING (Q01–Q10 running)
    → QC_FAILED (any critical check fails — fix and resubmit)
    → CLEAN (all critical checks pass)
    → DERIVED (computed outputs from CLEAN inputs)
    → VALIDATED (all advisory checks resolved; approved)
    → PUBLISHED (released as official output — IMMUTABLE)
    → ARCHIVED (superseded version — retained for reproducibility)
```

A dataset may cycle between VALIDATING and QC_FAILED multiple times.
Each cycle must be logged in VERSION_LOG.csv.

---

## 4. Script Responsibility Matrix

| Script | QC Steps Executed |
|---|---|
| 01_ingest.py | Source registration; initial structure check |
| 02_validate.py | Q01 Q02 Q03 Q04 Q05 Q07 Q08 Q09 Q10 Q17 |
| 03_clean.py | Q19 (consent); apply fixes; set status to CLEAN |
| 04_integrate.py | Q06 Q16 Q18 Q20 (spatial checks — requires GIS) |
| 05_climate.py | Q15 (time series — DB05) |
| 08_hydropower.py | Q15 (time series — DB04) |
| 16_qc.py | Q11 Q12 Q13 Q14 (cross-cutting QC and reporting) |

The master controller `run_pipeline.py` executes scripts in dependency order
and halts on any critical QC failure.

---

## 5. QC Report Standard

Every QC run must produce a timestamped QC report saved to:
`05_Analysis/04_QC/QC_Report_[DB_ID]_[YYYYMMDD_HHMMSS].csv`

The report must record:

| Field | Description |
|---|---|
| Run_Timestamp | YYYY-MM-DD HH:MM:SS |
| Database_ID | e.g. DB01 |
| Data_Version | Version of data checked |
| Script_Version | Version of validation script |
| Total_Records | Count of records checked |
| Critical_Failures | Count of critical check failures |
| Advisory_Flags | Count of advisory flags |
| QC_Status_Outcome | CLEAN / QC_FAILED |
| Checks_Run | Comma-separated list of QC codes run |
| Checks_Failed | Comma-separated list of failed checks |
| Notes | Summary of failures and actions taken |

---

## 6. Build Dependency Rule

No derived product may be built from a dataset with QC_Status != CLEAN.

The pipeline enforces this through `run_pipeline.py` — if any upstream
dataset has QC_Status = QC_FAILED, the pipeline halts before executing
dependent scripts.

This is the technical implementation of the specification's rule:
> *"Do not proceed to a downstream layer when an upstream dependency has
> failed critical QC."*

---

## 7. QC Check Cross-Reference by Database

| Check | DB01 | DB02 | DB03 | DB04 | DB05 | DB06 |
|---|---|---|---|---|---|---|
| Q01 Structure | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q02 Completeness | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q03 Uniqueness | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q04 Ref Integrity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q05 Coordinates | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q06 Spatial (GIS) | ✓ | — | ✓ | — | — | ✓ |
| Q07 Temporal | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q08 Logical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q09 Range | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q10 Missing/Zero | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q11 Privacy | — | ✓ | — | — | — | — |
| Q12 Provenance | — | — | — | ✓ | ✓ | — |
| Q13 Version | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q14 Enumerator | — | ✓ | — | — | — | — |
| Q15 Time Series | — | — | — | ✓ | ✓ | — |
| Q16 Cross-DB | ✓ | — | ✓ | ✓ | — | ✓ |
| Q17 Lookups | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Q18 Spatial Joins | ✓ | — | ✓ | — | — | ✓ |
| Q19 Consent | — | ✓ | — | — | — | — |
| Q20 Geom Sync | ✓ | — | ✓ | — | — | ✓ |

---

*Version controlled: see VERSION_LOG.csv for change history.*
