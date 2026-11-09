# Update Operation Procedure
## How New Observations Enter the CHER-CDSS System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Core Principle

> **A new observation enters as a new dated record linked to the permanent asset/community identifier.
> It never overwrites a previous observation. History is preserved permanently.**

This principle applies to every data domain:
field surveys, climate records, hydropower observations,
erosion site measurements, infrastructure assessments, and remote-sensing products.

---

## 2. Update Workflow (All Data Types)

```
NEW DATA ARRIVES
        ↓
[STEP 1] SOURCE REGISTRATION
Register in SOURCE_REGISTER.csv (if new external source)
Record: provider, URL, version, acquisition date, CRS, licence

        ↓
[STEP 2] RAW INGESTION (01_ingest.py)
Copy/load raw file into 03_Data/RAW/ or 04_GIS/01_RAW/
Do NOT modify source data
Set QC_Status = INGESTED

        ↓
[STEP 3] STRUCTURAL AND QC VALIDATION (02_validate.py)
Run Q01–Q10 checks
CRITICAL FAILURE → halt; fix errors; re-submit
PASS → proceed

        ↓
[STEP 4] CLEAN AND PROMOTE (03_clean.py)
Apply field standardisation
Consent gate (DB02)
Set QC_Status = CLEAN
Write to 03_Data/CLEAN/

        ↓
[STEP 5] INTEGRATION (04_integrate.py)
Assign / verify permanent ID
Run spatial joins (community → LGA → basin → river)
Populate derived fields (River_Distance_m, Hydropower_Distance)
Sync DB-to-GIS layers (G03, G19, G26)

        ↓
[STEP 6] DOMAIN PROCESSING (05–15 scripts)
Run only the modules whose upstream inputs changed
(Do NOT re-run the full pipeline if only one domain changed)

        ↓
[STEP 7] QC AND CROSS-CHECKS (16_qc.py)
Privacy check
Provenance check
Cross-database consistency
Geometry sync

        ↓
[STEP 8] RECALCULATE DEPENDENT DERIVED PRODUCTS
Recalculate only the downstream outputs that depend on the changed input
Archive previous versions of changed outputs

        ↓
[STEP 9] PUBLISH NEW VERSION
Increment version number
Update VERSION_LOG.csv
Update PROCESSING_STATUS.csv
Archive superseded outputs to 09_Archive/

        ↓
[STEP 10] GENERATE OUTPUTS
Re-run 17_reports.py and 18_maps.py for affected outputs
Update FLAG_Register
Notify management of new flags (if any critical flags raised)
```

---

## 3. Permanent ID Assignment Rules

| Object | When ID is assigned | Who assigns it | Can it change? |
|---|---|---|---|
| Community | On first survey | Data Manager | Never |
| Erosion site | On first field observation | Data Manager | Never |
| Infrastructure item | On first field survey | Data Manager | Never |
| Hydropower facility | On registration in G07 | GIS Officer / Data Manager | Never |
| Climate station | On registration in G20 | Data Manager | Never |
| Household | On first survey (RESTRICTED) | Data Manager | Never |
| Observation record | Auto-generated on insert | Pipeline | Never |
| Intervention | On registration | CHER-CDSS Coordinator | Never |

**If an administrative name or boundary changes** (e.g. LGA renamed):
- Update the Name field
- Add a `Previous_Name` or `Name_History` field
- Do NOT change the permanent ID
- Record the name change in VERSION_LOG.csv

---

## 4. Update Rules by Data Domain

### 4.1 Erosion Sites (6–12 month cycle; post-event)

1. Field team revisits **existing site** using its permanent **Erosion_ID**
2. Records new observations as a **new dated row** in DB03 — same Erosion_ID, new Observation_Date
3. Old row is never deleted or modified
4. Re-run `07_erosion.py` for the affected community
5. If change thresholds exceeded → flags generated automatically
6. If new site discovered → assign new Erosion_ID; run `04_integrate.py` SJ12

### 4.2 Climate Observations (monthly / continuous)

1. New monthly data received from NiMet or approved source
2. Appended to DB05 CLEAN as new Climate_ID records
3. Re-run `05_climate.py` → updated G21 station summary
4. If new extreme events → update G25 (observed floods) as needed
5. G22/G23 surfaces re-interpolated annually (not monthly)

### 4.3 Hydropower/Water Observations (monthly / operational interval)

1. New observations appended to DB04 as new Observation_ID records
2. Re-run `08_hydropower.py` → updated IND07, IND08, G28
3. If disruption flag triggered → alert generated

### 4.4 Infrastructure (annual + post-event)

1. Field team visits infrastructure items using their permanent **Infrastructure_ID**
2. New condition/damage assessment entered as a new row in DB06 — same Infrastructure_ID, new Observation_Date
3. Re-run `04_integrate.py` → G19 updated
4. Re-run `09_exposure.py` → G29/G30/G32 updated

### 4.5 Community Survey (2–3 year cycle)

1. New survey round uses same Community_IDs
2. New survey records entered in DB01 with new Survey_Date
3. Previous community record retained (do not overwrite)
4. Full pipeline re-run for affected communities
5. New baseline risk scores published as a new version (v2.0)

### 4.6 GIS Layer Updates (when source data updated)

1. New source file acquired and registered in SOURCE_REGISTER.csv
2. Saved to `04_GIS/01_RAW/` with version date in filename
3. Previous CLEAN layer moved to `09_Archive/`
4. New CLEAN layer processed; QC run
5. All DERIVED layers that depend on this layer re-flagged as needing recomputation
6. Downstream processing re-run in dependency order

### 4.7 Risk Score Updates (when any upstream input changes)

1. Identify which upstream inputs changed
2. Re-run only the affected pipeline steps in dependency order
3. New R_Score computed; old R_Score archived with its version
4. If community's risk class changes → `TIER_CHANGE` flag generated
5. New version published; management notified if any `NEW_HIGH_RISK` flags

---

## 5. What NOT to Do

| Prohibited action | Correct action |
|---|---|
| Overwrite a previous observation record | Append a new dated record |
| Delete a community or erosion site record | Set Active_Status = Inactive; retain record |
| Change a permanent ID | Update Name/alias field; keep ID |
| Modify a published output | Publish a new version; archive the old |
| Re-run the full pipeline when only one domain changed | Run only the affected modules |
| Publish outputs from QC_FAILED data | Fix QC failure first |
| Add 0 for a missing measurement | Use NULL; flag as DATA_GAP |
| Recalculate risk with new weights mid-cycle | Create a new model version; run sensitivity |
| Edit raw data files | Work only in CLEAN copies |
| Let spreadsheets become authoritative parallel databases | All updates go through the pipeline |

---

## 6. Update Log Entry (required for every update cycle)

After each update, append to `08_Updates/UPDATE_LOG.csv`:

| Field | Example |
|---|---|
| Update_ID | UPD-2027-001 |
| Update_Date | 2027-04-01 |
| Update_Type | Erosion field survey |
| Data_Domains_Affected | DB03, G26, G27, G31, G35, G37 |
| New_Records_Added | 47 |
| Records_Modified | 0 (none — new rows only) |
| Previous_Version_Archived | Yes |
| New_Version | v1.1 |
| Flags_Generated | EROSION_WORSENING (3), DATA_GAP (2) |
| Flags_Resolved | EROSION_WORSENING (1) |
| Outputs_Regenerated | G26, G27, G31, G35, G37, community profiles |
| Updated_By | [Name] |
| Notes | Post-wet-season survey round; 5 new sites identified |

Create the log file template at: `08_Updates/UPDATE_LOG.csv`
