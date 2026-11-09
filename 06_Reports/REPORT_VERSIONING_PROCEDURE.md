# Report Versioning Structure and Publication Procedure
## N-HYPPADEC / CHER-CDSS Decision-Support System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Report Status Stages

Every report passes through five stages in order.
No stage may be skipped. The stage is appended to the filename.

```
DRAFT → TECHNICAL_REVIEW → VALIDATED → FINAL → ARCHIVED
```

| Stage | Meaning | Who Approves | File Suffix |
|---|---|---|---|
| Draft | Working document; not for distribution | Author | `_Draft` |
| Technical Review | Under review by technical team | Technical lead | `_Reviewed` |
| Validated | Data and analysis verified; ready for management | Data Manager + GIS Officer | `_Validated` |
| Final | Approved and published | CHER-CDSS Coordinator / PI | `_Final` |
| Archived | Superseded by a newer version | System | `_Archived` |

---

## 2. File Naming Convention

```
[ReportType]_[Scope]_[Period]_v[X].[Y]_[Stage].[ext]
```

### Examples

| Report | Filename |
|---|---|
| Community profile draft | `Community_Profile_Abia_Isiala_Ngwa_v1.0_Draft.pdf` |
| State profile final | `State_Profile_Kogi_2026_v1.0_Final.pdf` |
| Annual report validated | `Annual_Report_2026_v2.1_Validated.pdf` |
| Risk maps final | `Risk_Map_TenStates_2026_v1.0_Final.pdf` |
| Superseded report | `State_Profile_Niger_2026_v1.0_Archived.pdf` |

### Version numbering

- `v1.0` → first production release
- `v1.1` → minor correction or annotation (same data, same analysis)
- `v2.0` → new data version or significant analytical change
- A new version **never overwrites** the previous — the previous moves to `06_Reports/04_FINAL/Archive/`

---

## 3. Report Types and Storage Locations

| Report Type | Storage | Update Frequency |
|---|---|---|
| Community profiles | `06_Reports/04_FINAL/Community_Profiles/` | Survey cycle / update |
| State profiles | `06_Reports/04_FINAL/State_Profiles/` | Annual |
| Annual report | `06_Reports/04_FINAL/Annual_Reports/` | Annual |
| Risk / hazard maps | `04_GIS/05_MAP_EXPORTS/` | At each data update |
| Analytical tables | `06_Reports/02_TABLES/` | At each data update |
| Figures | `06_Reports/03_FIGURES/` | At each data update |
| Climate evidence briefs | `06_Reports/04_FINAL/Climate_Evidence/` | Before major engagements |
| Intervention reports | `06_Reports/04_FINAL/Interventions/` | At milestones / completion |
| Data quality reports | `05_Analysis/04_QC/` | At each pipeline run |
| Management dashboard data | `07_Decision_Support/02_Dashboards/` | Continuous |

---

## 4. Publication Checklist

Before any report is moved to `_Final` status, the following must be confirmed:

```
REPORT: __________________________ VERSION: _______ DATE: _________
CHECKED BY: ______________________

DATA CHECKS
[ ] All data sourced from CLEAN or VALIDATED datasets (not RAW)
[ ] Data version recorded in report
[ ] No household-level data exposed (if community/household data used)
[ ] Privacy check signed off (if DB02 data used — PRIV07)
[ ] Risk language standard applied (no probability-of-disaster language)

ANALYTICAL CHECKS
[ ] Risk model version recorded: ______________________
[ ] Sensitivity analysis results included (S1 and S2)
[ ] Data confidence / completeness flags shown
[ ] All indicator weights and normalisation method documented

CARTOGRAPHIC CHECKS (if maps included)
[ ] All maps pass MAP_PRODUCTION_STANDARD.md checklist
[ ] All mandatory map elements present (title, legend, north arrow, etc.)
[ ] Attribution statements present for HydroSHEDS / ESA WorldCover / OSM

VERSION CONTROL
[ ] Report filename follows naming convention
[ ] Previous version moved to Archive if this is a replacement
[ ] VERSION_LOG.csv updated with this report version
[ ] Report registered in output catalogue

APPROVAL
[ ] Technical review completed
[ ] Data Manager sign-off
[ ] CHER-CDSS Coordinator / PI approval

Approved by: ________________________ Date: _____________
```

---

## 5. Annual Report Structure

The annual institutional report is the primary recurring publication.
It must be generated from the VALIDATED database — never from spreadsheets or ad hoc extracts.

### Mandatory sections

1. **Executive summary** — key findings; top-priority communities; major events; interventions completed
2. **Climate conditions and trends** — rainfall anomaly; temperature; extreme events; dry spells
3. **Flood status** — observed events; affected communities; comparison with previous year
4. **Erosion status** — active sites; severity changes; new sites detected
5. **Hydrological and hydropower conditions** — reservoir levels; generation; disruptions; sedimentation
6. **Community and infrastructure impacts** — exposed population; damaged/at-risk infrastructure
7. **Vulnerability and resilience** — indicators; changes since baseline
8. **Composite risk** — current scores; changes from previous period; sensitivity analysis
9. **Adaptation actions** — measures in place; gaps; IND10 Adaptation Gap
10. **N-HYPPADEC interventions** — what was done; where; outcomes measured (Section 17 of CHER-CDSS guide)
11. **Priority areas** — Tier 1/2 communities; data confidence flags
12. **Data quality** — completeness; update status; known gaps
13. **Annex A** — community-level data tables
14. **Annex B** — state profile summaries
15. **Annex C** — methodology notes and model version

---

## 6. Climate Evidence Brief

For international engagements (COP, regional forums, national climate dialogues),
a focused 4–8 page evidence brief is produced from the current validated database.

### Mandatory content per CHER-CDSS Section 20

- Current climate conditions and trends (numbers, not narratives)
- Flood and erosion impact statistics (verified field data)
- Affected communities and population (with data confidence rating)
- Hydropower and electricity disruption evidence
- Documented interventions and measured outcomes
- Remaining gaps and priority investment areas
- Data traceability statement ("Data sourced from CHER-CDSS v[X], [date]")

**Rule:** Climate evidence briefs must state the data version and date.
Claims must be traceable to the underlying database. No unverified assertions.

---

## 7. Archiving Policy

- Published reports are **immutable** — never edited after Final status
- A new version creates a new file; the old file moves to Archive
- Archives are retained permanently for audit and reproducibility
- Archive location: `06_Reports/04_FINAL/Archive/`
- Archive path recorded in VERSION_LOG.csv
