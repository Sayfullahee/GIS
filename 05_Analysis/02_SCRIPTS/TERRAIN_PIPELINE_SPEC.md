# Terrain Processing Pipeline Specification
## G09–G15 | Phase 4

**Version:** v1.0 | **Date:** 2026-10-02 | **Status:** Specification (not yet executed)

---

## 1. Overview

This pipeline produces all terrain and environment layers (G09–G15) from
two external source datasets. Every derived layer inherits the quality and
decisions of its upstream inputs. The pipeline must be executed in strict
dependency order — no step may run until its upstream dependency has
QC_Status = CLEAN.

```
SOURCES
  SRC005 HydroSHEDS DEM  OR  SRC006 Copernicus GLO-30 DEM  →  G09 DEM
  SRC007 ESA WorldCover                                      →  G15 Land Cover

G09 DEM (CLEAN)
  ├── G10 Slope
  ├── G11 Aspect
  ├── G12 Hillshade  [visualisation only]
  ├── G13 Flow Direction
  │     └── G14 Flow Accumulation
  └── (feeds G24 Flood Hazard in Phase 6)

G15 Land Cover (CLEAN, independent of G09)
  └── (feeds G24, G27, G29, G32 in later phases)
```

---

## 2. Pre-Processing Decisions Required

**All decisions in TERRAIN_PROCESSING_DECISIONS.csv must be recorded BEFORE
any script is run.** The pipeline will not produce reproducible results if
decisions are changed after processing begins.

| Decision | File | Status |
|---|---|---|
| DEC01 — DEM source selection | TERRAIN_PROCESSING_DECISIONS.csv | TO BE DECIDED |
| DEC02 — Slope unit (fixed: degrees) | TERRAIN_PROCESSING_DECISIONS.csv | DECIDED |
| DEC03 — Flow direction algorithm | TERRAIN_PROCESSING_DECISIONS.csv | TO BE DECIDED |
| DEC04 — Hydrologic conditioning method | TERRAIN_PROCESSING_DECISIONS.csv | TO BE DECIDED |
| DEC05 — Land cover source (WorldCover v200) | TERRAIN_PROCESSING_DECISIONS.csv | DECIDED |
| DEC06 — Hillshade parameters (az315/alt45) | TERRAIN_PROCESSING_DECISIONS.csv | DECIDED |

---

## 3. Step-by-Step Pipeline

### STEP T01 — Acquire DEM Source Tiles

```
Script:  01_ingest.py  (terrain module)
Input:   SOURCE_REGISTER.csv SRC005 or SRC006
Action:  Download all DEM tiles covering study area + 50km buffer
Output:  04_GIS/01_RAW/DEM/[tiles].tif
Log:     Record tile filenames; acquisition date; source version
QC Gate: All tiles present; none corrupted (checksum if available)
```

**HydroSHEDS download:**
- URL: https://www.hydrosheds.org/hydrosheds-core-downloads
- Select: Africa 3 arc-second conditioned DEM (HydroSHEDS CON)
- Tiles needed: covers approximately 4°N–14°N / 2°E–15°E

**Copernicus GLO-30 download (if DEC01 = Copernicus):**
- URL: https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model
- Select: GLO-30 tiles covering study area

---

### STEP T02 — Mosaic DEM Tiles

```
Script:  01_ingest.py  (terrain module)
Input:   04_GIS/01_RAW/DEM/[all tiles]
Command: gdal_merge.py -of GTiff -co COMPRESS=LZW
         -o 04_GIS/01_RAW/DEM/G09_DEM_mosaic_raw.tif [tile list]
Output:  04_GIS/01_RAW/DEM/G09_DEM_mosaic_raw.tif
Log:     Record all input tile names; gdal version; command used
QC Gate: Output extent covers study area + 50km buffer; no holes
```

---

### STEP T03 — Clip DEM to Study Area + Buffer

```
Script:  03_clean.py  (terrain module)
Input:   G09_DEM_mosaic_raw.tif
         G01 state boundary (CLEAN) + 50km buffer polygon
Command: gdalwarp -cutline [buffer.gpkg] -crop_to_cutline
         -co COMPRESS=LZW -tr [pixel_size] [pixel_size]
Output:  04_GIS/01_RAW/DEM/G09_DEM_clipped_raw.tif
QC Gate: Extent check; no holes within buffer
```

---

### STEP T04 — Hydrologic Conditioning (if required)

```
Script:  03_clean.py  (terrain module)
Applies: Only if DEC01 = Copernicus GLO-30 (HydroSHEDS already conditioned)
Input:   G09_DEM_clipped_raw.tif + G05 rivers (CLEAN, for stream burning)
Methods (choose per DEC04):
  Option A — Sink fill only:
    whitebox_tools --run=FillDepressions
    OR: saga_cmd ta_preprocessor 4
  Option B — Breach depressions (preferred for high-res DEMs):
    whitebox_tools --run=BreachDepressions
  Option C — Sink fill + stream burn:
    Step 1: Rasterise G05 river lines at DEM resolution
    Step 2: Lower DEM values along river by 1-5m (document amount)
    Step 3: Fill remaining sinks
Output:  04_GIS/02_CLEAN/G09_DEM_conditioned.tif
Log:     Record method; parameters; software version
QC Gate: G09-Q08 (no holes); G09-Q11 (river elevation check)
```

---

### STEP T05 — Produce G09 CLEAN Layer

```
Script:  03_clean.py  (terrain module)
Input:   Conditioned DEM (or HydroSHEDS clipped — already conditioned)
Action:  Set nodata value; set CRS metadata; add compression; rename
Command: gdal_translate -a_nodata -9999 -a_srs EPSG:4326
         -co COMPRESS=LZW -co BIGTIFF=IF_SAFER
         -of GTiff [input] 04_GIS/02_CLEAN/G09_DEM_[source]_[res]_v1_0.tif
QC Gate: Run ALL G09 QC checks (G09-Q01 to G09-Q15)
Status:  Set G09 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
```

---

### STEP T06 — Compute Slope (G10)

```
Script:  04_integrate.py  (terrain derivatives module)
Input:   04_GIS/02_CLEAN/G09_DEM_*_v1_0.tif
Dependency: G09 QC_Status = CLEAN (pipeline halts if not)
Command: gdaldem slope -of GTiff -co COMPRESS=LZW
         -alg Horn -b 1
         [input_G09] 04_GIS/03_DERIVED/G10_Slope_degrees_v1_0.tif
         (add -p flag for percent slope if DEC02 overridden — NOT recommended)
Unit:    Degrees (DEC02 — fixed)
QC Gate: Run ALL G10 QC checks (G10-Q01 to G10-Q12)
Status:  Set G10 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
```

---

### STEP T07 — Compute Aspect (G11)

```
Script:  04_integrate.py  (terrain derivatives module)
Input:   04_GIS/02_CLEAN/G09_DEM_*_v1_0.tif
Dependency: G09 QC_Status = CLEAN
Command: gdaldem aspect -of GTiff -co COMPRESS=LZW
         -alg Horn -b 1 -zero_for_flat
         [input_G09] 04_GIS/03_DERIVED/G11_Aspect_v1_0.tif
Note:    -zero_for_flat assigns 0 to flat areas;
         alternatively omit for -1 convention — document choice
QC Gate: Run ALL G11 QC checks (G11-Q01 to G11-Q09)
Status:  Set G11 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
```

---

### STEP T08 — Compute Hillshade (G12)

```
Script:  04_integrate.py  (terrain derivatives module)
Input:   04_GIS/02_CLEAN/G09_DEM_*_v1_0.tif
Dependency: G09 QC_Status = CLEAN
Command: gdaldem hillshade -of GTiff -co COMPRESS=LZW
         -az 315 -alt 45 -b 1
         [input_G09] 04_GIS/03_DERIVED/G12_Hillshade_az315_alt45_v1_0.tif
QC Gate: Run ALL G12 QC checks (G12-Q01 to G12-Q09)
Status:  Set G12 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
Note:    VISUALISATION ONLY — not an analytical input
```

---

### STEP T09 — Compute Flow Direction (G13)

```
Script:  04_integrate.py  (terrain derivatives module)
Input:   04_GIS/02_CLEAN/G09_DEM_*_v1_0.tif  (conditioned)
Dependency: G09 QC_Status = CLEAN
Algorithm: D8 (DEC03 — recommended)

Option A — GDAL/Python (pysheds):
  from pysheds.grid import Grid
  grid = Grid.from_raster('G09_DEM_conditioned.tif')
  fdir = grid.flowdir(dem)
  grid.to_raster(fdir, '04_GIS/03_DERIVED/G13_FlowDirection_D8_v1_0.tif')

Option B — WhiteboxTools:
  whitebox_tools --run=D8Pointer
    --dem=G09_DEM_conditioned.tif
    --output=G13_FlowDirection_D8_v1_0.tif

Option C — TauDEM:
  mpiexec -n [cores] pitremove -z [G09] -fel [filled]
  mpiexec -n [cores] d8flowdir -fel [filled] -p [G13]

Encoding: Document D8 encoding convention of chosen tool in TERRAIN_PROCESSING_DECISIONS.csv
QC Gate: Run ALL G13 QC checks (G13-Q01 to G13-Q12)
Status:  Set G13 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
```

---

### STEP T10 — Compute Flow Accumulation (G14)

```
Script:  04_integrate.py  (terrain derivatives module)
Input:   04_GIS/03_DERIVED/G13_FlowDirection_D8_v1_0.tif
Dependency: G13 QC_Status = CLEAN

Option A — Python (pysheds):
  acc = grid.accumulation(fdir)
  grid.to_raster(acc, '04_GIS/03_DERIVED/G14_FlowAccumulation_v1_0.tif')

Option B — WhiteboxTools:
  whitebox_tools --run=D8FlowAccumulation
    --input=G13_FlowDirection_D8_v1_0.tif
    --output=G14_FlowAccumulation_v1_0.tif
    --out_type=cells

Option C — TauDEM:
  mpiexec -n [cores] aread8 -p [G13] -ad8 [G14]

Unit:    Cells (default) OR km² (if weighted — document in metadata)
QC Gate: Run ALL G14 QC checks (G14-Q01 to G14-Q12)
Status:  Set G14 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
```

---

### STEP T11 — Acquire and Process Land Cover (G15)

```
Script:  01_ingest.py + 03_clean.py  (land cover module)
Input:   SRC007 ESA WorldCover v200 tiles
URL:     https://worldcover2021.esa.int/downloader

Step 1 — Download tiles:
  Download all tiles covering study area + 10km buffer
  Record: tile IDs; acquisition date; version confirmation

Step 2 — Mosaic:
  gdal_merge.py -of GTiff -co COMPRESS=LZW -ot Byte
    -o 04_GIS/01_RAW/LandCover/G15_WorldCover_mosaic.tif [tiles]

Step 3 — Clip to study area + 10km buffer:
  gdalwarp -cutline [buffer_10km.gpkg] -crop_to_cutline
    -co COMPRESS=LZW -ot Byte
    G15_WorldCover_mosaic.tif
    04_GIS/02_CLEAN/G15_LandCover_ESAWorldCover_v200_2021_v1_0.tif

Step 4 — Set nodata:
  gdal_translate -a_nodata 0 [if WorldCover uses 0 as nodata — confirm]

Step 5 — Validate class codes vs LKP_LandCoverClasses.csv:
  python 02_validate.py --layer G15 --check class_codes

QC Gate: Run ALL G15 QC checks (G15-Q01 to G15-Q16)
Status:  Set G15 QC_Status = CLEAN in PROCESSING_STATUS.csv on pass
```

---

## 4. Pipeline Execution Order

```
[DECISIONS RECORDED IN TERRAIN_PROCESSING_DECISIONS.csv]
          ↓
T01 Acquire DEM tiles
          ↓
T02 Mosaic DEM tiles  →  T11 Acquire + mosaic Land Cover (parallel)
          ↓                        ↓
T03 Clip DEM                T11 Clip Land Cover
          ↓                        ↓
T04 Hydrologic conditioning (if needed)
          ↓
T05 G09 CLEAN ──────────────────────────────────────────────────────────┐
          ↓                                                              │
    ┌─────┼──────────────────┐                                          │
    ↓     ↓                  ↓                                          │
   T06   T07                T08 [visualisation]                         │
   G10   G11                G12                                         │
  Slope Aspect           Hillshade                                      │
    ↓                                                                   │
   T09                                                                  │
   G13 Flow Direction                                                   │
    ↓                                                                   │
   T10                                                                  │
   G14 Flow Accumulation                                                │
                                                                        │
T11 G15 Land Cover CLEAN ───────────────────────────────────────────────┘
          ↓
ALL G09–G15 QC_Status = CLEAN
          ↓
PHASE 4 COMPLETE — proceed to Phase 5 (Infrastructure & Climate G16–G23)
```

---

## 5. Output File Naming Convention

| Layer | Filename |
|---|---|
| G09 | G09_DEM_HydroSHEDS_90m_v1_0.tif OR G09_DEM_Copernicus_30m_v1_0.tif |
| G10 | G10_Slope_degrees_v1_0.tif |
| G11 | G11_Aspect_v1_0.tif |
| G12 | G12_Hillshade_az315_alt45_v1_0.tif |
| G13 | G13_FlowDirection_D8_v1_0.tif |
| G14 | G14_FlowAccumulation_v1_0.tif |
| G15 | G15_LandCover_ESAWorldCover_v200_2021_v1_0.tif |

---

## 6. Software Requirements

| Tool | Purpose | Installation |
|---|---|---|
| GDAL >= 3.4 | Core raster processing (gdaldem, gdalwarp, gdal_merge) | pip install gdal OR conda install -c conda-forge gdal |
| Python >= 3.9 | Pipeline scripting | System Python or conda |
| rasterio >= 1.3 | Python raster I/O | pip install rasterio |
| numpy >= 1.23 | Array operations | pip install numpy |
| pysheds >= 0.3 | Flow direction/accumulation | pip install pysheds |
| WhiteboxTools >= 2.3 | Alternative hydrological tools | https://www.whiteboxgeo.com/download-whiteboxtools/ |
| QGIS >= 3.28 | Visual QC and manual checks | https://qgis.org |

---

## 7. QC Summary — Phase 4 Critical Gates

A downstream phase (Phase 5) may not start until ALL of the following pass:

| Layer | Critical QC Gate |
|---|---|
| G09 | No nodata holes; elevation range valid; conditioning documented |
| G10 | Slope unit documented; values 0–90 degrees; matches G09 extent |
| G11 | Values 0–360; extent matches G09 |
| G12 | Values 0–255; not used as analytical input |
| G13 | No internal sinks; D8 encoding documented; extent matches G09 |
| G14 | Values >= 0; accumulation unit documented; extent matches G09 |
| G15 | Class codes valid; coverage complete; CC BY 4.0 attribution recorded |

---

*Version controlled: see VERSION_LOG.csv for change history.*
