# DATA AND METHODOLOGY CATALOGUE
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System (CHER-CDSS)
### For the Ten N-HYPPADEC Member States of Nigeria
**Version:** 4.1 (Validated & Corrected Baseline) | **Publication Date:** October 2026  
**Commissioning Agency:** National Hydroelectric Power Producing Areas Development Commission (N-HYPPADEC)  
**Standard:** International Institutional Evidence Platform Standard  
**Document Code:** `NHYPPADEC-CHER-CDSS-DMC-v4.1`  

---

## 1. SYSTEM OVERVIEW & MANDATE

The **CHER-CDSS Data and Methodology Catalogue** provides the exhaustive technical reference manual for all datasets, spatial layers, relational tables, mathematical algorithms, and governance protocols comprising the N-HYPPADEC Institutional Evidence System.

The platform monitors **ten member states** across Nigeria:
- **North Central:** Niger (`NG-NIG`), Benue (`NG-BEN`), Plateau (`NG-PLA`), Kogi (`NG-KOG`), Kwara (`NG-KWA`), Nasarawa (`NG-NAS`).
- **North West:** Kebbi (`NG-KEB`), Kaduna (`NG-KAD`).
- **North East:** Taraba (`NG-TAR`), Gombe (`NG-GOM`).

---

## 2. THIRTY-SEVEN LAYER GIS MASTER REGISTER (G01–G37)

All spatial entities are projected in **WGS84 (EPSG:4326)**, standardized for GeoServer WMS/WFS publication and QGIS LTS integration.

| Layer ID | Layer Name | Geometry | Category | Description / Source |
|:---|:---|:---|:---|:---|
| **G01** | `Nigeria_State` | Polygon | Administrative | 10 State administrative boundaries (`NG-` prefix) |
| **G02** | `Nigeria_LGA` | Polygon | Administrative | 186 LGA administrative boundaries |
| **G02W** | `Ward_Boundaries` | Polygon | Administrative | Sub-layer of G02: Ward boundaries where formally delineated |
| **G03** | `Communities` | Point | Administrative | 50 Monitored sentinel communities with verified field GPS |
| **G04** | `Households` | Point | Socioeconomic | Level 3 Restricted household sample points (anonymized in public view) |
| **G05** | `River_and_Drainage_Network` | Line | Hydrology | Mainstream rivers, tributaries, distributaries, and drainage channels |
| **G06** | `HydroBasins` | Polygon | Hydrology | Level 6–8 watershed catchment boundaries (HydroSHEDS) |
| **G07** | `HydroFacilities` | Point | Hydropower | Dams, hydro stations, spillways, barrages (Kainji, Jebba, Shiroro, etc.) |
| **G08** | `Reservoirs` | Polygon | Hydropower | Reservoir water surface polygons at full supply capacity |
| **G09** | `DEM` | Raster | Terrain | SRTM 30m digital elevation model surface |
| **G10** | `Slope` | Raster | Terrain | Surface slope derived from G09, fixed in degrees |
| **G11** | `Aspect` | Raster | Terrain | Terrain aspect orientation (0–360 degrees) |
| **G12** | `Hillshade` | Raster | Terrain | Shaded relief surface (visual context only; non-analytical) |
| **G13** | `FlowDirection` | Raster | Hydrology | D8 flow direction surface derived from depression-filled DEM |
| **G14** | `FlowAccumulation` | Raster | Hydrology | Upslope contributing flow accumulation grid |
| **G15** | `LandCover` | Raster | Environment | 10m ESA WorldCover classification (cropland, wetland, water, urban) |
| **G16** | `OSM_Roads` | Line | Infrastructure | Primary, secondary, tertiary, and residential transportation network |
| **G17** | `OSM_Buildings` | Polygon | Exposure | Delineated building footprints from satellite / OSM extracts |
| **G18** | `OSM_POI` | Point | Criticality | Points of interest: hospitals, schools, markets, government centres |
| **G19** | `Infrastructure_Field` | Point | Infrastructure | Field-validated infrastructure (culverts, bridges, boreholes, dykes) |
| **G20** | `Climate_Stations` | Point | Climate | Active NiMet / NIHSA hydro-meteorological stations |
| **G21** | `Climate_Observations` | Table | Climate | Daily and monthly temperature and precipitation time series |
| **G22** | `Rainfall_Surface` | Raster | Climate | CHIRPS / NiMet interpolated mean annual & seasonal precipitation |
| **G23** | `Temperature_Surface` | Raster | Climate | Lapse-rate adjusted mean annual surface temperature grid |
| **G24** | `Flood_Hazard` | Raster/Vector | Hazard | Modelled flood hazard zones (Return periods: 5-yr, 20-yr, 50-yr) |
| **G25** | `Flood_Observed` | Polygon | Hazard | Historical and observed flood inundation polygons with confidence tags |
| **G26** | `Erosion_Sites` | Point | Hazard | Registered gully and riverbank erosion sites |
| **G27** | `Erosion_Hotspots` | Raster/Vector | Hazard | Kernel density estimation (KDE) surface of erosion severity |
| **G28** | `Hydro_Water` | Table | Hydrology | Reservoir inflow, storage volume, turbine discharge, and pulse spills |
| **G29** | `Flood_Exposure` | Vector | Exposure | Spatial intersection of flood extent with population and infrastructure |
| **G30** | `Erosion_Exposure` | Vector | Exposure | Proximity buffer (BUF003: 250m) intersection with vulnerable assets |
| **G31** | `Hazard_Index` | Index (0–100) | Decision Support | Normalised composite hazard score ($H$) |
| **G32** | `Exposure_Index` | Index (0–100) | Decision Support | Normalised composite exposure score ($E$) |
| **G33** | `Vulnerability_Index` | Index (0–100) | Decision Support | Normalised socioeconomic vulnerability score ($V$) |
| **G34** | `Criticality_Index` | Index (0–100) | Decision Support | Normalised grid and infrastructure criticality score ($C$) |
| **G35** | `Composite_Risk` | Index (0–100) | Decision Support | Authoritative composite risk index ($R = 0.35H + 0.25E + 0.25V + 0.15C$) |
| **G36** | `Adaptation` | Vector | MRV | Completed and active adaptation projects ($IND09$) |
| **G37** | `Priority_Areas` | Vector | Decision Support | Ranked priority interventions ($Score = 0.70R + 0.30IND10$) |

---

## 3. TWENTY-TWO CORE RELATIONAL DATABASE TABLES

Operated under PostgreSQL 16 with PostGIS 3.4 extensions, organized across structured schemas:

1. `DB01_Community_Master` — Sentinel community registry with GPS, demographics, livelihood.
2. `DB02_Household_Survey` — Socioeconomic household survey (Level 3 Restricted).
3. `DB03_Erosion_Sites` — Gully and bank erosion registry with geometry, dimensions, severity.
4. `DB04_Hydropower_Water` — Reservoir water levels, spillway operations, turbine discharge.
5. `DB05_Climate_Observations` — Station precipitation, temperature, extreme events.
6. `DB06_Infrastructure` — Public assets, bridges, culverts, schools, boreholes, clinics.
7. `G25_ObservedFloods` — Historical flood events, inundation area, displacement impact.
8. `Interventions` — Capital project registry, contractor, budget, progress, IES scores.
9. `Food_Security` — Crop losses, livestock impact, food price volatility, dietary stress.
10. `Security_Impact` — Safe development impacts, displacement figures, farm access loss.
11. `Ward_Master` — Administrative ward boundaries, codes, and linkage keys.
12. `Facility_Master` — Power plants, substations, water treatment, intake structures.
13. `Climate_Station` — Met stations metadata, elevation, sensor status, operator.
14. `Priority_Areas` — Ranked communities with priority scores, tiers, and interventions.
15. `Loss_Damage` — Economic and non-economic loss accounting records.
16. `Data_Provenance` — Source tracking, capture methodology, license, certifying officer.
17. `Audit_Trail` — Immutable change log, transaction timestamps, user IDs.
18. `Data_Confidence` — Quality ratings, ground-truthing percentages, error bounds.
19. `Lookup_Code` — Master codebook for classifications, hazard types, statuses.
20. `Scenarios` — Simulated perturbations, climate stress delta, adapted risk scores.
21. `LKP_LGAs` — 186 verified LGAs mapped to the 10 member states.
22. `LKP_States` — 10 official N-HYPPADEC states with internal codes and capitals.

---

## 4. INDICATOR DICTIONARY & NORMALIZATION ALGORITHM

### 4.1 Master Indicators ($IND01–IND10$)

| ID | Indicator Name | Unit | Direction | $min_{ref}$ | $max_{ref}$ | Component |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **IND01** | Flood Frequency | events / yr | Direct | 0.0 | 5.0 | Hazard ($H$) |
| **IND02** | Flood Severity | index (0–100) | Direct | 0.0 | 100.0 | Hazard ($H$) |
| **IND03** | Erosion Severity | index (0–100) | Direct | 0.0 | 100.0 | Hazard ($H$) |
| **IND04** | River Proximity | metres | Inverted | 0.0 | 5,000.0 | Hazard ($H$) |
| **IND05** | Population Exposure | persons in zone | Direct | 0.0 | 10,000.0 | Exposure ($E$) |
| **IND06** | Infrastructure Exposure | weighted asset count | Direct | 0.0 | 25.0 | Exposure ($E$) |
| **IND07** | Electricity Disruption | days / yr | Direct | 0.0 | 180.0 | Vulnerability ($V$) |
| **IND08** | Hydropower Disruption | generation loss % | Direct | 0.0 | 100.0 | Criticality ($C$) |
| **IND09** | Adaptation Coverage | ratio (0–1) | Inverted | 0.0 | 1.0 | Vulnerability ($V$) |
| **IND10** | Adaptation Gap | index (0–100) | Direct | 0.0 | 100.0 | Priority ($G37$) |

### 4.2 Locked 2026 Normalization Formulation
For a direct indicator $X$:
$$I_{\text{direct}} = \min\left(100, \max\left(0, \frac{X - min_{ref}}{max_{ref} - min_{ref}} \times 100\right)\right)$$

For an inverted indicator $X$ (where higher raw values reduce vulnerability/hazard):
$$I_{\text{inverted}} = \min\left(100, \max\left(0, \frac{max_{ref} - X}{max_{ref} - min_{ref}} \times 100\right)\right)$$

---

## 5. RISK MODELLING & SCIENTIFIC INTEGRITY CHECKS

### 5.1 Primary Additive Model
$$R = 0.35 \times H + 0.25 \times E + 0.25 \times V + 0.15 \times C$$
- **Tier 1 Critical:** $R \ge 70.0$ (Emergency Capital Intervention)
- **Tier 2 High:** $55.0 \le R < 70.0$ (Prioritized Resilience Works)
- **Tier 3 Moderate:** $40.0 \le R < 55.0$ (Structural Monitoring)
- **Tier 4 Low / Monitor:** $R < 40.0$ (Baseline Maintenance)

### 5.2 Multiplicative Structural Check ($R_{\text{mult}}$)
$$R_{\text{mult}} = H^{0.35} \times E^{0.25} \times V^{0.25} \times C^{0.15}$$
*Axiom of Exposure:* If physical Exposure $E = 0$, then $R_{\text{mult}} = 0.0$. This prevents capital allocation to unpopulated areas regardless of environmental hazard severity.

---

## 6. MRV & INTERVENTION EFFECTIVENESS SCORE ($IES$)

$$IES = \frac{R_{\text{before}} - R_{\text{after}}}{R_{\text{before}}} \times 100\%$$
- **Residual Risk:** $R_{\text{residual}} = R_{\text{after}}$.
- **Validity Constraints:**
  1. Identical reference bounds ($min_{ref}, max_{ref}$) must be used for before and after calculations.
  2. $R_{\text{before}} > 0$; if $R_{\text{before}} = 0$, $IES$ is strictly undefined (`null`).
  3. Minimum 6 months of operational observation required before certifying post-intervention score.

---

## 7. SCENARIO SIMULATION ENGINE

| Scenario ID | Name | Perturbation Parameters | Mean Risk Delta |
|:---|:---|:---|:---:|
| `SCN-2026-BASE` | 2026 Baseline Reference | Unperturbed baseline | $\pm 0.00$ |
| `SCN-2026-CLIM-STRESS` | Climate Stress | $+15\%$ Precipitation, $+1.5^\circ\text{C}$ Temp | $+4.84$ |
| `SCN-2026-LAND-DEGRADE` | Land Degradation | $-20\%$ Riparian Buffer, $+10\%$ Gully Activity | $+2.69$ |
| `SCN-2026-ADAPT-INVEST` | Adaptation Investment | $+50\%$ Dyke Coverage, Gabion Reinforcement | $-6.58$ |

---

## 8. DATA PRIVACY & ACCESS CONTROL ARCHITECTURE

- **Level 1 (Public Executive):** Aggregate indicators, state summaries, conference evidence packs, interactive public dashboard.
- **Level 2 (Operational / Agency):** Community-level coordinates, infrastructure registries, intervention financial specifics.
- **Level 3 (Restricted / Confidential):** Raw household survey microdata (`DB02`), personally identifiable information, surveyor device IDs. Strictly isolated and protected by column-level encryption.

---
*Authoritative Specification — N-HYPPADEC CHER-CDSS System Architecture v4.1*
