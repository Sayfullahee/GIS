# CHER-CDSS Google Earth Engine & Remote Sensing Processing Guide
## Standard Operating Procedure for Earth Observation Operations
**Standard:** Master Implementation Scaffold v4.1 (Stage 9 & Stage 13)  
**Location:** `05_Analysis/02_SCRIPTS/earth_engine/`  
**Sensors:** Sentinel-1 C-Band SAR, Sentinel-2 MSI Optical, Copernicus 30m DEM, ESA WorldCover 10m  

---

## 1. Overview & Institutional Mandate

Remote sensing within CHER-CDSS provides continuous, repeatable, and spatially comprehensive evidence of environmental dynamics across the 10 N-HYPPADEC member states. It supplements ground-truth field data with macro-level verification of:
1. **Land Cover Changes (`G15`):** Riparian buffer deforestation, wetland degradation, urbanization.
2. **Vegetation Condition:** NDVI seasonal trends and localized dry-spell/siltation stress.
3. **Surface Water & Flood Inundation (`G24`/`G25`):** Post-event SAR flood boundary delineation.
4. **Riverbank Erosion Retreat (`G26`/`G27`):** Multi-temporal waterline shifting at monitored gully sites.
5. **Agricultural Shock Exposure (`G29`):** Direct acreage of croplands submerged during dam spillage or peak river discharge.

---

## 2. GEE Script Directory & Usage

| Script File | Purpose | Earth Engine Datasets | Output Layer |
|---|---|---|---|
| [`01_gee_landcover_worldcover.js`](01_gee_landcover_worldcover.js) | 10m Land Cover baseline | `ESA/WorldCover/v200` | `G15_LandCover` |
| [`02_gee_sentinel2_ndvi.js`](02_gee_sentinel2_ndvi.js) | Seasonal NDVI anomaly | `COPERNICUS/S2_SR_HARMONIZED` | Vegetation Stress Indicator |
| [`03_gee_sentinel1_flood_sar.js`](03_gee_sentinel1_flood_sar.js) | Radar flood extent mapping | `COPERNICUS/S1_GRD` | `G25_ObservedFloods` |
| [`04_gee_riverbank_erosion.js`](04_gee_riverbank_erosion.js) | Waterline erosion tracking | `COPERNICUS/S2_SR_HARMONIZED` | `G26_ErosionSites` / `G27` |
| [`05_gee_agricultural_exposure.js`](05_gee_agricultural_exposure.js) | Inundated cropland overlay | `ESA/WorldCover/v200` + `S1_GRD` | `G29_FloodExposure` |

---

## 3. Operational Workflow (GEE -> CHER-CDSS Ingestion)

```
Google Earth Engine (Cloud)
         │  Run GEE Script (JS / Python)
         ▼
Export GeoTIFF to Google Drive / Cloud Bucket
         │  Download to 04_GIS/01_RAW/
         ▼
01_ingest.py (Source Registration & SHA-256 Hashing)
         │  02_validate.py (CRS EPSG:4326, Bounds, Range QC)
         ▼
21_remote_sensing.py (Zonal Statistics by LGA & State)
         │  Promote to 04_GIS/02_CLEAN & 04_GIS/03_DERIVED
         ▼
Update G31 (Hazard), G32 (Exposure) & Web GIS API (/api/remote_sensing)
```

---

## 4. Ground-Truthing and Scientific Accuracy Rules

In strict compliance with **Section 41 (Non-Negotiable Scientific Rules)**:
1. **Never Treat Satellite Estimates as Ground Truth without Validation:** All remote sensing products must achieve $> 85.0\%$ overall classification agreement against field survey coordinates (`DB01_Community_Master`, `DB03_Erosion_Sites`).
2. **Explicit Labeling:** Every map or figure derived from satellite classification must state:
   - Satellite Platform and Sensor (e.g. *Copernicus Sentinel-1 C-Band SAR*)
   - Acquisition Dates and Processing Window
   - Spatial Resolution (e.g. *10m resampled to 30m*)
   - Pre-processing corrections (Atmospheric BOA Level-2A, Speckle Lee Filtering)
3. **Traceability:** Zonal summaries are permanently catalogued in `05_Analysis/03_OUTPUTS/RS_Earth_Observation_Summary.csv` and served live via the Executive Management Dashboard.

---
*Maintained by N-HYPPADEC Remote Sensing & GIS Directorate — October 2026*
