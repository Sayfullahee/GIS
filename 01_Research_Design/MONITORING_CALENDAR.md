# RESEARCH DESIGN: INSTITUTIONAL MONITORING CALENDAR
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System (CHER-CDSS)
### N-HYPPADEC / Ten Member States of Nigeria
**Document ID:** `RD-MC-2026-v4.1` | **Stage:** 2.5 | **Status:** Approved Baseline  
**Governing Specification:** CHER-CDSS Master Implementation Scaffold v4.1 (October 2026)

---

## 1. Operating Cycle Structure

CHER-CDSS operates on an integrated **multi-tiered monitoring rhythm** designed to balance rapid disaster alert capabilities with rigorous statutory reporting:

```
[ Monthly ]   Automated Data Ingest · Station Precipitation · Dam Telemetry Logs · QC Review
     │
     ▼
[ Quarterly ] Indicator Engine Execution · Hotspot Updates · Infrastructure Condition Logs
     │
     ▼
[ Seasonal ]  Pre-Wet Season Flood Preparedness (May) · Post-Flood Damage Assessment (Nov)
     │
     ▼
[ Annual ]    State of Climate Resilience Report · Baseline Refresh · Conference Evidence Pack
```

---

## 2. Tiered Operating Schedules

### Tier 1: Monthly Operational Ingestion (Every 1st–5th of the Month)
- **Target Data:**
  - Automated download of NiMet synoptic station observations (precipitation, max/min temperature).
  - Hydropower generation, reservoir pool elevation, and outflow discharge logs from dam operators.
  - Verification of new field survey submissions uploaded to KoboToolbox / ODK central servers.
- **Actions:**
  - Execute automated QC scripts (`01_ingest.py` and `02_validate.py`).
  - Flag any anomalies, coordinate drift, or missing submissions to State Focal Persons.
  - Publish monthly system health status to IT Director and GIS Lead.

### Tier 2: Quarterly Indicator Refresh (End of Q1, Q2, Q3, Q4)
- **Schedule:** March 31, June 30, September 30, December 31.
- **Actions:**
  - Run the full 18-step analytical pipeline (`run_pipeline.py`).
  - Update `G21_Climate_Observations`, `G28_Hydro_Water`, and `G35_Composite_Risk`.
  - Refresh the Executive Management Dashboard (`http://localhost:8000/`) with new quarterly metrics.
  - Review Top-20 Priority Communities list for emerging shifts in risk ranking.

### Tier 3: Seasonal Hydrological Windows (Tailored to Nigerian Hydro-Climatic Zones)
- **Pre-Wet Season Flood Preparedness Window (May 1 – May 31):**
  - Synthesize NiMet Seasonal Rainfall Prediction (SRP) and NIHSA Annual Flood Outlook (AFO).
  - Pre-position early warning telemetry in high-risk riverine corridors (Shiroro, Kainji downstream, Makurdi front).
  - Dispatch enumerators for pre-season dyke integrity and drainage clearing audits.
- **Post-Flood Damage & Loss Verification Window (October 15 – November 15):**
  - High-resolution satellite acquisition (Sentinel-2 / Planet Labs) of peak flood extents (`G25`).
  - Deploy field rapid response teams to record agricultural crop loss, livestock mortality, and culvert washouts.
  - Calculate post-disaster household Food Consumption Scores (FCS) and update `Loss_Damage_CLEAN.csv`.

### Tier 4: Annual Institutional Reporting & Conference Cycle (October–December)
- **October 1–15:** Data freeze for the annual cycle. No new observations accepted for the annual reporting snapshot.
- **October 16–25:** Execution of final analytical pipeline, sensitivity analyses (S1, S2), and $R_{\text{mult}}$ validation checks.
- **October 26–31:** Generation of the **Ten State Climate Resilience Profiles** (`06_Reports/04_FINAL/`).
- **November 1–15:** Compilation of the statutory **Annual State of Climate Resilience Report** and executive summary.
- **November 16–30:** Production of the **International Conference Evidence Pack** and high-resolution cartographic atlas.
- **December 1–15:** Executive Steering Committee sign-off, capital budget allocation review, and release archiving in `09_Archive/`.

---

## 3. Roles & Responsibilities Matrix by Cadence

| Cadence | Lead Responsible | Supporting Roles | Output Deliverable |
|:---|:---|:---|:---|
| **Monthly** | GIS & Data Manager | DEV, State Focal Persons | Monthly QC Log & Ingestion Summary |
| **Quarterly** | Risk Modeling Lead | Statistician, Hydrogeologist | Quarterly Indicator Update & Dashboard Sync |
| **Seasonal** | Field Coordinator | Remote Sensing Lead, Livelihoods | Pre-Season Alert & Post-Flood Loss Assessment |
| **Annual** | Programme Manager | All Thematic Leads, MD / Board | 10 State Profiles, Annual Report & Conference Pack |

---
*Operationalized by N-HYPPADEC Directorate of Monitoring & Evaluation — 2026*
