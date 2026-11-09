# Environmental Domains Extension
## CHER-CDSS v2.0 — Climate Change, Flooding, Land Degradation,
## Deforestation, Waste Pollution, Biodiversity Loss

**Version:** v2.0 | **Date:** 2026-10-14 | **Status:** Implementation specification

---

## 1. Extension Rationale

The baseline CHER-CDSS (v1.0) addressed flood and erosion hazard, infrastructure
exposure, and community vulnerability with a four-component risk model
(H × E × V × C). That framework is extended here to six additional environmental
domains that interact directly with hydropower generation, community resilience,
and N-HYPPADEC's mandate.

Each new domain is integrated into the existing architecture — it does not
replace any existing component. The composite risk model is upgraded to a
**twelve-component Environmental Risk Index (ERI)** that preserves full
backward compatibility with all v1.0 outputs.

---

## 2. New Domains and Their System Roles

| Domain | Code | Primary hazard/pressure | Feeds into |
|---|---|---|---|
| Climate Change | CC | Long-term forcing; trend amplifier | H_score; V_score; all projections |
| Flooding (upgraded) | FL | Multi-return-period flood model | H_score (replaces basic G24) |
| Land Degradation | LD | Soil loss; productivity decline | H_score; V_score; exposure |
| Deforestation | DF | Canopy loss; runoff amplifier; carbon | H_score; biodiversity |
| Waste Pollution | WP | Dump-site leachate; water contamination | V_score; health exposure |
| Biodiversity Loss | BL | Habitat fragmentation; ecosystem services | V_score; adaptation capacity |

---

## 3. New GIS Layers (G38–G63)

### Climate Change (G38–G42)
| ID | Name | Type | Derivation |
|---|---|---|---|
| G38 | Climate Trend Surface — Rainfall | Raster | DB05 time-series regression; CHIRPS trends |
| G39 | Climate Trend Surface — Temperature | Raster | DB05 time-series; ERA5 trends |
| G40 | Drought Frequency Index | Raster | DB05 SPI/SPEI; CHIRPS |
| G41 | Climate Projection — Rainfall 2030–2060 | Raster | CORDEX-Africa / CMIP6 bias-corrected |
| G42 | Climate Change Vulnerability Index | Vector-Polygon | Composite: G38 + G39 + G40 + G41 |

### Flooding — Upgraded Multi-Return-Period Model (G43–G46)
| ID | Name | Type | Derivation |
|---|---|---|---|
| G43 | Flood Inundation — 2-Year Return Period | Raster | HEC-RAS / HAND / JRC Global Surface Water |
| G44 | Flood Inundation — 10-Year Return Period | Raster | As G43 |
| G45 | Flood Inundation — 100-Year Return Period | Raster | As G43; authoritative where available |
| G46 | Flood Frequency Surface (multi-period composite) | Raster | G43 + G44 + G45 + G25 events |

### Land Degradation (G47–G50)
| ID | Name | Type | Derivation |
|---|---|---|---|
| G47 | NDVI Time Series (Annual Mean) | Raster | Sentinel-2 / Landsat 8-9 annual composite |
| G48 | NDVI Trend (Slope 2015–2026) | Raster | Linear regression on G47 annual values |
| G49 | Soil Erosion Risk (RUSLE-based) | Raster | R × K × LS × C × P factors |
| G50 | Land Degradation Index | Raster/Polygon | G48 + G49 + G15 change + G10 |

### Deforestation (G51–G54)
| ID | Name | Type | Derivation |
|---|---|---|---|
| G51 | Forest Cover Baseline (2015) | Raster | Hansen Global Forest Change / ESA |
| G52 | Forest Cover Current (latest epoch) | Raster | Hansen GFC / ESA WorldCover |
| G53 | Forest Cover Change (loss/gain) | Raster | G52 – G51; annual loss per pixel |
| G54 | Deforestation Pressure Index | Raster/Polygon | G53 + proximity to communities + roads |

### Waste Pollution (G55–G58)
| ID | Name | Type | Derivation |
|---|---|---|---|
| G55 | Waste Dump Sites | Vector-Point | Field survey (DB08) + remote sensing |
| G56 | Leachate Risk Zone | Raster/Polygon | G55 buffer + topography + G05 proximity |
| G57 | Open Burning Locations | Vector-Point | Field survey + Sentinel-5P TROPOMI |
| G58 | Waste Pollution Exposure Index | Vector-Polygon | G55 + G56 + G57 + G03 communities |

### Biodiversity (G59–G63)
| ID | Name | Type | Derivation |
|---|---|---|---|
| G59 | Protected Areas | Vector-Polygon | WDPA (World Database of Protected Areas) |
| G60 | Habitat Integrity Index | Raster | G15 land cover + G53 forest loss + fragmentation |
| G61 | Riparian Corridor Condition | Vector-Line | G05 rivers + G51/G52 forest cover buffer |
| G62 | Ecosystem Services Value | Raster/Polygon | G60 × ecosystem service weights |
| G63 | Biodiversity Loss Index | Vector-Polygon | G59 + G60 + G61 + G53 |

---

## 4. New Databases (DB07–DB09)

| ID | Name | Primary Key | Domain |
|---|---|---|---|
| DB07 | Intervention Tracking | Intervention_ID | All domains |
| DB08 | Waste / Pollution Sites | Waste_ID | Waste Pollution |
| DB09 | Biodiversity Field Observations | BioObs_ID | Biodiversity |

---

## 5. New Indicators (IND11–IND22)

| ID | Name | Direction | Domain | Index |
|---|---|---|---|---|
| IND11 | Rainfall Trend (mm/decade) | Negative trend = higher hazard | Climate Change | H; CC |
| IND12 | Temperature Trend (°C/decade) | Positive trend = higher stress | Climate Change | V; CC |
| IND13 | Drought Frequency Index (SPI < −1.5) | Higher = more hazard | Climate Change | H |
| IND14 | Flood Inundation Depth (10-yr RP) | Higher = more hazard | Flooding | H |
| IND15 | NDVI Trend (% change/year) | Negative = degradation | Land Degradation | H; LD |
| IND16 | RUSLE Soil Loss (t/ha/yr) | Higher = more hazard | Land Degradation | H |
| IND17 | Deforestation Rate (%/year) | Higher = amplified hazard | Deforestation | H |
| IND18 | Proximity to Waste Dump (m) | Closer = higher exposure | Waste Pollution | E; V |
| IND19 | Leachate Risk Score (0–100) | Higher = higher pollution risk | Waste Pollution | E |
| IND20 | Habitat Integrity Score (0–100) | Lower = more degraded | Biodiversity | V |
| IND21 | Protected Area Coverage (%) | Higher = more protected | Biodiversity | V (protective) |
| IND22 | Ecosystem Services Loss (% decline) | Higher = greater vulnerability | Biodiversity | V |

---

## 6. Updated Risk Model (ERI v2.0)

The Environmental Risk Index v2.0 retains the four-component HEVC baseline
and adds three environmental modifier indices:

```
ERI = w₁×H + w₂×E + w₃×V + w₄×C + w₅×CC + w₆×LD + w₇×DF + w₈×WP + w₉×BL

where all components are normalised 0–100 and weights sum to 1.0
```

### Baseline weight structure (ERI_Model_v2.0)

| Component | Symbol | Baseline Weight | Rationale |
|---|---|---|---|
| Hazard (flood+erosion) | H | 0.25 | Reduced from 0.35 — shared with CC/LD/DF |
| Exposure | E | 0.15 | Reduced from 0.25 — shared with WP |
| Vulnerability | V | 0.15 | Reduced from 0.25 — shared with BL |
| Criticality | C | 0.10 | Maintained proportionally |
| Climate Change | CC | 0.10 | Long-term forcing multiplier |
| Land Degradation | LD | 0.08 | Soil/productivity loss |
| Deforestation | DF | 0.07 | Runoff amplification; carbon loss |
| Waste Pollution | WP | 0.05 | Health and water contamination |
| Biodiversity Loss | BL | 0.05 | Ecosystem services; resilience erosion |

**Weight sum:** 0.25+0.15+0.15+0.10+0.10+0.08+0.07+0.05+0.05 = **1.00** ✓

**Backward compatibility:** The original HEVC composite risk (G35, v1.0) remains
published and unchanged. ERI v2.0 is a new output layer (G64) — it extends,
not replaces, the baseline.

---

## 7. New Output Layer

| ID | Name | Formula | Output |
|---|---|---|---|
| G64 | Environmental Risk Index (ERI v2.0) | See Section 6 | Community-level 0–100 |

---

## 8. Build Order for New Domains

All new layers must be built AFTER all existing G01–G37 layers pass QC.

```
G38–G40 (climate trends)    ← requires DB05 CLEAN + G22/G23
G41     (projections)       ← requires external CORDEX/CMIP6 data
G43–G46 (flood RP model)    ← requires G09 G10 G13 G14 G22 G25
G47–G48 (NDVI/vegetation)   ← requires remote sensing pipeline
G49     (RUSLE)             ← requires G09 G10 G15 G22
G50     (land degradation)  ← requires G47 G48 G49
G51–G53 (forest cover)      ← requires Hansen GFC / ESA
G54     (deforestation)     ← requires G51 G52 G53
G55–G57 (waste sites)       ← requires DB08 CLEAN
G58     (waste exposure)    ← requires G55 G56 G57 G03
G59     (protected areas)   ← requires WDPA download
G60–G62 (habitat/ecosystem) ← requires G59 G15 G53
G63     (biodiversity loss) ← requires G59 G60 G61 G53
G64     (ERI v2.0)          ← requires G31 G32 G33 G34 G42 G50 G54 G58 G63
```
