# QGIS MASTER SPATIAL DECISION PROJECT
## CHER-CDSS / N-HYPPADEC Ten Member States
**Project File:** `CHER_CDSS_Master_Project_v4.1.qgs` | **Software Pin:** QGIS 3.34 LTR (Prizren)  
**Spatial Reference System:** `EPSG:4326` (WGS 84) | Alternative Projected: `EPSG:32632` (UTM Zone 32N)

---

## 1. How to Open the Master Project

1. Launch **QGIS 3.34 LTR**.
2. Open Project: File -> Open -> navigate to `c:/xampp/htdocs/GIS/04_GIS/04_PROJECTS/CHER_CDSS_Master_Project_v4.1.qgs`.
3. The project pre-configures the canvas extent to the ten N-HYPPADEC states ($3.2^\circ\text{E}$ to $12.8^\circ\text{E}$, $6.5^\circ\text{N}$ to $13.2^\circ\text{N}$).

---

## 2. Layer Tree Organization (37 Layers Across 7 Thematic Groups)

The layer tree is organized into seven hierarchical groups matching Section 31 of Scaffold v4.1:

1. **`01_Administrative_and_Demographic`**:
   - `G01_Nigeria_State` (10 N-HYPPADEC member states)
   - `G02_Nigeria_LGA` (186 Local Government Areas)
   - `G02W_Wards` (Administrative Ward sub-layer)
   - `G03_Communities` (50 Sentinel communities with GPS, population, and composite risk)
   - `G04_Households_Restricted` (Restricted Level 3 layer, jittered/pseudonymised)

2. **`02_Hydrology_and_Hydropower`**:
   - `G05_River_and_Drainage_Network` (Main rivers, tributaries, distributaries, and streams)
   - `G06_HydroBasins` (Hydrological sub-basins Levels 6–8)
   - `G07_HydroFacilities` (Kainji, Jebba, Shiroro, Dadin Kowa, Kashimbila, etc.)
   - `G08_Reservoirs` (Reservoir waterbody boundaries)
   - `G28_Hydro_Water` (Operational dam water levels and inflow/outflow logs)

3. **`03_Terrain_and_Geomorphology`**:
   - `G09_DEM` (SRTM / Copernicus 30m)
   - `G10_Slope` (Terrain slope in degrees DEC02)
   - `G11_Aspect` (Terrain aspect azimuth)
   - `G12_Hillshade` (Cartographic relief visualisation)
   - `G13_FlowDirection` (D8 hydrological flow directions)
   - `G14_FlowAccumulation` (Accumulated catchment drainage area)
   - `G15_LandCover` (ESA WorldCover 2021 11-class surface)

4. **`04_Infrastructure_and_Exposure`**:
   - `G16_OSM_Roads` (Primary, secondary, and rural transit corridors)
   - `G17_OSM_Buildings` (Building footprints in riparian settlements)
   - `G18_OSM_POI` (Critical health, education, and market assets)
   - `G19_Field_Infrastructure` (Field-audited public boreholes, bridges, clinics)
   - `G29_Flood_Exposure` (Population & assets in modeled flood hazard zones)
   - `G30_Erosion_Exposure` (Assets within active gully 50m buffer BUF003)

5. **`05_Climate_and_Meteorology`**:
   - `G20_Climate_Stations` (NiMet synoptic and partner weather stations)
   - `G21_Climate_Observations` (Station monthly rainfall and temperature series)
   - `G22_Rainfall_Surface` (CHIRPS interpolated precipitation surface)
   - `G23_Temperature_Surface` (Lapse-rate corrected ambient temperature surface)

6. **`06_Hazards_and_Observed_Events`**:
   - `G24_Flood_Hazard` (Multi-criteria flood susceptibility surface)
   - `G25_Flood_Observed` (Observed flood polygons and inundation extents)
   - `G26_Erosion_Sites` (Field-observed gully and bank erosion locations)
   - `G27_Erosion_Hotspots` (Kernel density hotspot clusters)

7. **`07_Decision_Support_and_Risk`**:
   - `G31_Hazard_Index` ($H \in [0, 100]$)
   - `G32_Exposure_Index` ($E \in [0, 100]$)
   - `G33_Vulnerability_Index` ($V \in [0, 100]$)
   - `G34_Criticality_Index` ($C \in [0, 100]$)
   - `G35_Composite_Risk` ($R = 0.35H + 0.25E + 0.25V + 0.15C$)
   - `G36_Adaptation` (Adaptation inventory and gap analysis)
   - `G37_Priority_Areas` (Priority Tiers 1 to 4 with Top-20 register)

---

## 3. Cartographic Export Standards

When printing maps or generating conference figures from this project:
1. Comply strictly with [`04_GIS/05_MAP_EXPORTS/MAP_PRODUCTION_STANDARD.md`](../05_MAP_EXPORTS/MAP_PRODUCTION_STANDARD.md).
2. All 11 mandatory elements must be visible (Title, Subtitle, Legend, Scale Bar, North Arrow, Projection EPSG:4326, Data Date October 2026, Source Statement, Confidence Rating, N-HYPPADEC Logo/Disclaimer, Disclaimers).
3. Risk Color Palette:
   - Tier 1 Critical: Crimson Red (`#dc2626`)
   - Tier 2 High: Amber Orange (`#ea580c`)
   - Tier 3 Moderate: Golden Yellow (`#eab308`)
   - Tier 4 Monitor: Emerald Green (`#16a34a`)

---
*Maintained by N-HYPPADEC GIS & Data Management Directorate — 2026*