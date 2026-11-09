"""
generate_qgis_project.py
========================
Generates the authoritative QGIS Project file (QGIS 3.34 LTR)
CHER_CDSS_Master_Project_v4.1.qgs and user guide in 04_GIS/04_PROJECTS/
"""

from pathlib import Path

PROJECT_ROOT = Path(r"c:\xampp\htdocs\GIS")
PROJECTS_DIR = PROJECT_ROOT / "04_GIS" / "04_PROJECTS"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

qgs_content = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="CHER-CDSS N-HYPPADEC Master Spatial Decision Platform v4.1" version="3.34.0-Prizren">
  <homePath path=""/>
  <title>CHER-CDSS | National Hydroelectric Power Producing Areas Development Commission (N-HYPPADEC)</title>
  <autotransaction active="0"/>
  <evaluateDefaultValues active="0"/>
  <trust active="0"/>
  <projectCrs>
    <spatialrefsys>
      <wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]</wkt>
      <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
      <srsid>3452</srsid>
      <srid>4326</srid>
      <authid>EPSG:4326</authid>
      <description>WGS 84</description>
      <projectionacronym>longlat</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>true</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <layer-tree-group>
    <customproperties>
      <Option/>
    </customproperties>
    <!-- Group 07: Decision Support & Risk -->
    <layer-tree-group name="07_Decision_Support_and_Risk" expanded="1" checked="Qt::Checked">
      <layer-tree-layer name="G37_Priority_Areas" id="g37_priority_areas" checked="Qt::Checked" source="../../07_Decision_Support/03_Priority_Areas/G37_PriorityAreas_v1_0.csv"/>
      <layer-tree-layer name="G35_Composite_Risk" id="g35_composite_risk" checked="Qt::Checked" source="../../07_Decision_Support/01_Risk/G35_CompositeRisk_v1_0.csv"/>
      <layer-tree-layer name="G36_Adaptation" id="g36_adaptation" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G36_Adaptation.csv"/>
      <layer-tree-layer name="G34_Criticality_Index" id="g34_criticality" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G34_CriticalityIndex.csv"/>
      <layer-tree-layer name="G33_Vulnerability_Index" id="g33_vulnerability" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G33_VulnerabilityIndex.csv"/>
      <layer-tree-layer name="G32_Exposure_Index" id="g32_exposure" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G32_ExposureIndex.csv"/>
      <layer-tree-layer name="G31_Hazard_Index" id="g31_hazard" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G31_HazardIndex.csv"/>
    </layer-tree-group>
    <!-- Group 06: Hazards & Observed Events -->
    <layer-tree-group name="06_Hazards_and_Observed_Events" expanded="1" checked="Qt::Checked">
      <layer-tree-layer name="G27_Erosion_Hotspots" id="g27_erosion_hotspots" checked="Qt::Checked" source="../../03_Data/CLEAN/DB03_Erosion_Sites_CLEAN.csv"/>
      <layer-tree-layer name="G26_Erosion_Sites" id="g26_erosion_sites" checked="Qt::Checked" source="../../03_Data/CLEAN/DB03_Erosion_Sites_CLEAN.csv"/>
      <layer-tree-layer name="G25_Flood_Observed" id="g25_flood_observed" checked="Qt::Checked" source="../../03_Data/CLEAN/G25_ObservedFloods_CLEAN.csv"/>
      <layer-tree-layer name="G24_Flood_Hazard" id="g24_flood_hazard" checked="Qt::Checked" source="../../05_Analysis/03_OUTPUTS/G31_HazardIndex.csv"/>
    </layer-tree-group>
    <!-- Group 05: Climate & Meteorology -->
    <layer-tree-group name="05_Climate_and_Meteorology" expanded="0" checked="Qt::Unchecked">
      <layer-tree-layer name="G20_Climate_Stations" id="g20_climate_stations" checked="Qt::Unchecked" source="../../03_Data/CLEAN/Climate_Station_CLEAN.csv"/>
      <layer-tree-layer name="G21_Climate_Observations" id="g21_climate_obs" checked="Qt::Unchecked" source="../../03_Data/CLEAN/DB05_Climate_Observations_CLEAN.csv"/>
      <layer-tree-layer name="G22_Rainfall_Surface" id="g22_rainfall_surface" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G23_Temperature_Surface" id="g23_temp_surface" checked="Qt::Unchecked" source=""/>
    </layer-tree-group>
    <!-- Group 04: Infrastructure & Exposure -->
    <layer-tree-group name="04_Infrastructure_and_Exposure" expanded="0" checked="Qt::Unchecked">
      <layer-tree-layer name="G19_Field_Infrastructure" id="g19_field_infra" checked="Qt::Unchecked" source="../../03_Data/CLEAN/DB06_Infrastructure_CLEAN.csv"/>
      <layer-tree-layer name="G29_Flood_Exposure" id="g29_flood_exposure" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G29_FloodExposure_community.csv"/>
      <layer-tree-layer name="G30_Erosion_Exposure" id="g30_erosion_exposure" checked="Qt::Unchecked" source="../../05_Analysis/03_OUTPUTS/G30_ErosionExposure_community.csv"/>
      <layer-tree-layer name="G16_OSM_Roads" id="g16_osm_roads" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G17_OSM_Buildings" id="g17_osm_buildings" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G18_OSM_POI" id="g18_osm_poi" checked="Qt::Unchecked" source=""/>
    </layer-tree-group>
    <!-- Group 03: Terrain & Geomorphology -->
    <layer-tree-group name="03_Terrain_and_Geomorphology" expanded="0" checked="Qt::Unchecked">
      <layer-tree-layer name="G09_DEM" id="g09_dem" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G10_Slope" id="g10_slope" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G11_Aspect" id="g11_aspect" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G12_Hillshade" id="g12_hillshade" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G13_FlowDirection" id="g13_flowdir" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G14_FlowAccumulation" id="g14_flowaccum" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G15_LandCover" id="g15_landcover" checked="Qt::Unchecked" source=""/>
    </layer-tree-group>
    <!-- Group 02: Hydrology & Hydropower -->
    <layer-tree-group name="02_Hydrology_and_Hydropower" expanded="1" checked="Qt::Checked">
      <layer-tree-layer name="G07_HydroFacilities" id="g07_hydro_facilities" checked="Qt::Checked" source="../../03_Data/CLEAN/Facility_Master_CLEAN.csv"/>
      <layer-tree-layer name="G08_Reservoirs" id="g08_reservoirs" checked="Qt::Checked" source=""/>
      <layer-tree-layer name="G05_River_and_Drainage_Network" id="g05_river_network" checked="Qt::Checked" source=""/>
      <layer-tree-layer name="G06_HydroBasins" id="g06_hydrobasins" checked="Qt::Unchecked" source=""/>
      <layer-tree-layer name="G28_Hydro_Water" id="g28_hydro_water" checked="Qt::Unchecked" source="../../03_Data/CLEAN/DB04_Hydropower_Water_CLEAN.csv"/>
    </layer-tree-group>
    <!-- Group 01: Administrative & Demographic -->
    <layer-tree-group name="01_Administrative_and_Demographic" expanded="1" checked="Qt::Checked">
      <layer-tree-layer name="G03_Communities" id="g03_communities" checked="Qt::Checked" source="../../04_GIS/05_MAP_EXPORTS/Community_Risk_MapData_v1_0.geojson"/>
      <layer-tree-layer name="G02W_Wards" id="g02w_wards" checked="Qt::Unchecked" source="../../03_Data/CLEAN/Ward_Master_CLEAN.csv"/>
      <layer-tree-layer name="G02_Nigeria_LGA" id="g02_lga" checked="Qt::Checked" source="../../03_Data/LOOKUPS/LKP_LGAs.csv"/>
      <layer-tree-layer name="G01_Nigeria_State" id="g01_state" checked="Qt::Checked" source="../../03_Data/LOOKUPS/LKP_States.csv"/>
      <layer-tree-layer name="G04_Households_Restricted" id="g04_households" checked="Qt::Unchecked" source="../../03_Data/CLEAN/DB02_Household_Survey_CLEAN_RESTRICTED.csv"/>
    </layer-tree-group>
  </layer-tree-group>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>degrees</units>
    <extent>
      <xmin>3.200000</xmin>
      <ymin>6.500000</ymin>
      <xmax>12.800000</xmax>
      <ymax>13.200000</ymax>
    </extent>
    <rotation>0</rotation>
    <destationsrs>
      <spatialrefsys>
        <wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]</wkt>
        <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
        <srsid>3452</srsid>
        <srid>4326</srid>
        <authid>EPSG:4326</authid>
        <description>WGS 84</description>
      </spatialrefsys>
    </destationsrs>
  </mapcanvas>
</qgis>
"""

qgs_path = PROJECTS_DIR / "CHER_CDSS_Master_Project_v4.1.qgs"
with open(qgs_path, "w", encoding="utf-8") as f:
    f.write(qgs_content.strip())

readme_content = """# QGIS MASTER SPATIAL DECISION PROJECT
## CHER-CDSS / N-HYPPADEC Ten Member States
**Project File:** `CHER_CDSS_Master_Project_v4.1.qgs` | **Software Pin:** QGIS 3.34 LTR (Prizren)  
**Spatial Reference System:** `EPSG:4326` (WGS 84) | Alternative Projected: `EPSG:32632` (UTM Zone 32N)

---

## 1. How to Open the Master Project

1. Launch **QGIS 3.34 LTR**.
2. Open Project: File -> Open -> navigate to `c:/xampp/htdocs/GIS/04_GIS/04_PROJECTS/CHER_CDSS_Master_Project_v4.1.qgs`.
3. The project pre-configures the canvas extent to the ten N-HYPPADEC states ($3.2^\\circ\\text{E}$ to $12.8^\\circ\\text{E}$, $6.5^\\circ\\text{N}$ to $13.2^\\circ\\text{N}$).

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
"""

readme_path = PROJECTS_DIR / "README_QGIS_PROJECT.md"
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(readme_content.strip())

print(f"SUCCESS: Created {qgs_path} and {readme_path}")
