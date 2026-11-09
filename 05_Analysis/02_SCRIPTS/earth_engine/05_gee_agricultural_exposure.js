/**
 * 05_gee_agricultural_exposure.js
 * ===============================
 * Google Earth Engine (GEE) Script for Cropland Inundation & Agricultural Exposure
 * N-HYPPADEC / CHER-CDSS — 10 Member States of Nigeria
 * Standard: Scaffold v4.1 Stage 13 & Layer G29 (Flood Exposure - Agriculture)
 */

var studyArea = ee.Geometry.Polygon([
  [[3.2, 6.5], [12.0, 6.5], [12.0, 13.5], [3.2, 13.5], [3.2, 6.5]]
]);

// 1. Load ESA WorldCover Cropland Class (Value 40)
var worldcover = ee.ImageCollection('ESA/WorldCover/v200')
                   .filterBounds(studyArea)
                   .first()
                   .select('Map');
var croplands = worldcover.eq(40).selfMask();

// 2. Load Sentinel-1 Flood Inundation Layer
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
           .filterBounds(studyArea)
           .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
           .filter(ee.Filter.eq('instrumentMode', 'IW'));

var dryVH = s1.filterDate('2026-01-01', '2026-03-31').select('VH').median();
var wetVH = s1.filterDate('2026-08-01', '2026-10-05').select('VH').median();
var floodMask = wetVH.subtract(dryVH).lt(-3.2);

// 3. Intersect Croplands with Inundation to isolate inundated agricultural acreage
var inundatedCropland = croplands.updateMask(floodMask);

// Visualise
Map.centerObject(studyArea, 7);
Map.addLayer(croplands, {palette: ['f096ff']}, 'Active Cropland (ESA WorldCover)', false);
Map.addLayer(inundatedCropland, {palette: ['ff0055']}, 'Inundated Farmland / Crop Loss Zone (G29)');

// Export Agricultural Loss Extent GeoTIFF
Export.image.toDrive({
  image: inundatedCropland,
  description: 'CHER_CDSS_G29_Agricultural_Exposure_2026',
  scale: 30,
  region: studyArea,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});
