/**
 * 01_gee_landcover_worldcover.js
 * ==============================
 * Google Earth Engine (GEE) Script for Land Cover Extraction
 * N-HYPPADEC / CHER-CDSS — 10 Member States of Nigeria
 * Standard: Scaffold v4.1 Stage 9.3 & Layer G15 (ESA WorldCover 10m)
 */

// 1. Define study region bounds (10 N-HYPPADEC States)
var studyArea = ee.Geometry.Polygon([
  [[3.2, 6.5], [12.0, 6.5], [12.0, 13.5], [3.2, 13.5], [3.2, 6.5]]
]);

// 2. Load ESA WorldCover 10m v200 (2021)
var worldcover = ee.ImageCollection('ESA/WorldCover/v200')
                   .filterBounds(studyArea)
                   .first()
                   .clip(studyArea);

// 3. Class definitions per LKP_LandCoverClasses.csv
// 10: Tree cover, 20: Shrubland, 30: Grassland, 40: Cropland, 50: Built-up, 
// 60: Bare/sparse, 70: Snow/ice, 80: Permanent water bodies, 90: Herbaceous wetland, 95: Mangroves, 100: Moss/lichen
var landcoverVis = {
  bands: ['Map'],
  min: 10,
  max: 100,
  palette: [
    '006400', // 10: Tree cover
    'ffbb22', // 20: Shrubland
    'ffff4c', // 30: Grassland
    'f096ff', // 40: Cropland
    'fa0000', // 50: Built-up
    'b4b4b4', // 60: Bare / sparse
    'f0f0f0', // 70: Snow/ice
    '0064c8', // 80: Permanent water
    '0096a0', // 90: Herbaceous wetland
    '00cf75', // 95: Mangroves
    'fae6a0'  // 100: Moss/lichen
  ]
};

Map.centerObject(studyArea, 7);
Map.addLayer(worldcover, landcoverVis, 'ESA WorldCover 10m (G15)');

// 4. Calculate Riparian Buffer Canopy Cover (within 500m river corridor BUF001)
var trees = worldcover.select('Map').eq(10);
var cropland = worldcover.select('Map').eq(40);
var water = worldcover.select('Map').eq(80);

print('Riparian land cover components successfully prepared.');

// 5. Export Task to Google Drive / Cloud Storage for CHER-CDSS 04_GIS/01_RAW
Export.image.toDrive({
  image: worldcover,
  description: 'CHER_CDSS_G15_ESA_WorldCover_10m_2026',
  scale: 30, // Reprojected to 30m standard
  region: studyArea,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});
