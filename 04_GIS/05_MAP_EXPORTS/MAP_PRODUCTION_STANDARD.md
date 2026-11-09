# Map Production Standard
## N-HYPPADEC GIS Decision-Support System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Mandatory Elements — Every Final Map

Every map published from this system must carry all eleven elements below.
A map missing any mandatory element must not be published or distributed.

| Element | Requirement |
|---|---|
| **Title** | Full descriptive title — no abbreviations; include state/LGA scope if sub-national |
| **Legend** | All symbolised classes shown; no orphan symbols |
| **North Arrow** | Pointing to true north; placed consistently (top-right preferred) |
| **Scale Bar** | Metric; two to three divisions; appropriate to map extent |
| **CRS** | Coordinate reference system stated (WGS84 / EPSG:4326) |
| **Sources** | All data sources listed with provider and date; HydroSHEDS and ESA WorldCover attribution mandatory where used |
| **Data Date** | Date of the underlying data (e.g. "Data: 2026 baseline") |
| **Map Date** | Date the map was produced (e.g. "Produced: 2026-10-02") |
| **Project Name** | "N-HYPPADEC Climate–Hydropower–Erosion–Community Resilience DSS" |
| **Version** | Map version (e.g. v1.0); must match file name version |
| **Author/Unit** | Producing unit or author name |

---

## 2. File Naming Convention

```
MAP_[NN]_[Descriptive_Name]_v[X]_[Y].pdf
```

Examples:
- `MAP_01_Study_Area_v1_0.pdf`
- `MAP_20_Composite_Risk_v1_0.pdf`
- `MAP_27_Priority_Areas_v2_0.pdf`

Version increments:
- Minor revision (same data, layout change): v1.0 → v1.1
- New data version: v1.x → v2.0

---

## 3. Colour Standards

### Risk and Index Maps

| Class | Colour | Hex | Use |
|---|---|---|---|
| Very Low | Light green | #1A9641 | Lowest risk/hazard/exposure |
| Low | Yellow-green | #A6D96A | |
| Moderate | Yellow | #FFFFC0 | |
| High | Orange | #FDAE61 | |
| Very High | Red | #D7191C | Highest risk |
| No Data | Light grey | #CCCCCC | Missing or insufficient data |

### Priority Tier Maps

| Tier | Colour | Hex |
|---|---|---|
| Tier 1 (Highest) | Dark red | #B2182B |
| Tier 2 (High) | Orange-red | #EF8A62 |
| Tier 3 (Moderate) | Light orange | #FDDBC7 |
| Tier 4 (Lower) | White | #FFFFFF |
| Data Confidence Low (flag) | Hatching over tier colour | — |

### Erosion Severity

| Severity | Colour | Hex |
|---|---|---|
| 0 — None | White | #FFFFFF |
| 1 — Low | Yellow | #FFFF00 |
| 2 — Moderate | Orange | #FFA500 |
| 3 — High | Red-orange | #FF4500 |
| 4 — Very High/Critical | Dark red | #8B0000 |

---

## 4. Typography Standards

| Element | Font | Size | Style |
|---|---|---|---|
| Map title | Sans-serif (e.g. Arial) | 14–16pt | Bold |
| Subtitle / scope | Sans-serif | 11–12pt | Regular |
| Legend title | Sans-serif | 10pt | Bold |
| Legend classes | Sans-serif | 9pt | Regular |
| Labels (community names) | Sans-serif | 7–9pt | Regular |
| Scale bar text | Sans-serif | 8pt | Regular |
| Sources / metadata text | Sans-serif | 7–8pt | Italic |

---

## 5. Map Sizes and Formats

| Use | Size | Format |
|---|---|---|
| Published report maps | A4 portrait or landscape | PDF |
| Large-format display maps | A1 or A0 | PDF |
| Digital/web maps | 1920×1080px | PNG |
| Working draft maps | Any | PDF or PNG |

Resolution: minimum 300 DPI for print; 96 DPI for web.

---

## 6. Projection Note

All maps use **WGS84 geographic coordinates (EPSG:4326)** as the project CRS.
For large-scale maps where distortion is significant, a projected CRS appropriate
for Nigeria (e.g. UTM Zone 32N — EPSG:32632) may be used for display
**provided the CRS is stated on the map** and the underlying data remains in EPSG:4326.

---

## 7. Attribution Requirements

The following attribution statements must appear on every map that uses the
corresponding dataset:

| Dataset | Required Attribution |
|---|---|
| HydroSHEDS (rivers, basins, DEM) | © HydroSHEDS / WWF / USGS |
| ESA WorldCover | © ESA WorldCover 2021 (CC BY 4.0) |
| OpenStreetMap | © OpenStreetMap contributors (ODbL) |
| OCHA boundaries | © OCHA / NBS Nigeria |

---

## 8. Risk Map Language Standard

Maps showing the composite risk index (G35) or hazard index (G31) must use
the following language conventions:

| Prohibited | Required instead |
|---|---|
| "probability of flooding" | "relative flood hazard" or "flood hazard index" |
| "will be flooded" | "in high flood hazard zone" |
| "disaster risk" (implying certainty) | "composite risk index score" |
| "danger zone" | "High / Very High risk class" |

The map legend must include a note:
> *"Risk scores are relative indices for decision support — not probabilities of disaster."*

---

## 9. Cartographic Checklist (sign-off before publication)

Complete this checklist for every map before release.
File the completed checklist in `04_GIS/06_METADATA/` alongside the map metadata.

```
MAP ID:        _________________
MAP TITLE:     _________________
VERSION:       _________________
DATE:          _________________
CHECKED BY:    _________________

MANDATORY ELEMENTS
[ ] Title present and correct
[ ] Legend present; all classes shown; no orphan symbols
[ ] North arrow present
[ ] Scale bar present (metric)
[ ] CRS stated
[ ] All sources listed with provider and date
[ ] Data date stated
[ ] Map date stated
[ ] Project name present
[ ] Version matches filename
[ ] Author/unit present

CONTENT CHECKS
[ ] Risk language standard applied (if risk/hazard map)
[ ] Attribution present for all required datasets
[ ] No household-level data visible (if community data shown)
[ ] Priority tier data confidence flag shown (if priority map)
[ ] Colour standards applied

TECHNICAL CHECKS
[ ] File resolution >= 300 DPI (print) or 96 DPI (web)
[ ] File naming convention followed
[ ] File saved to 04_GIS/05_MAP_EXPORTS/
[ ] Map registered in MAP_REGISTER.csv (18_maps.py)

SIGN-OFF
Cartographer: _________________  Date: _________________
Data Manager: _________________  Date: _________________
```
