/**
 * 03_gee_sentinel1_flood_sar.js
 * =============================
 * Google Earth Engine (GEE) Script for Sentinel-1 C-Band SAR Flood Extent Mapping
 * N-HYPPADEC / CHER-CDSS — 10 Member States of Nigeria
 * Standard: Scaffold v4.1 Stage 9.5 & Layer G25 (Observed Floods)
 */

var studyArea = ee.Geometry.Polygon([
  [[3.2, 6.5], [12.0, 6.5], [12.0, 13.5], [3.2, 13.5], [3.2, 6.5]]
]);

// 1. Load Sentinel-1 GRD SAR (IW Mode, VV & VH Polarizations)
var s1Collection = ee.ImageCollection('COPERNICUS/S1_GRD')
                     .filterBounds(studyArea)
                     .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                     .filter(ee.Filter.eq('instrumentMode', 'IW'));

// 2. Pre-flood dry season reference composite (January - March 2026)
var preFlood = s1Collection.filterDate('2026-01-01', '2026-03-31')
                           .select('VH')
                           .median()
                           .clip(studyArea);

// 3. Peak flood period composite (August - October 2026)
var postFlood = s1Collection.filterDate('2026-08-01', '2026-10-05')
                            .select('VH')
                            .median()
                            .clip(studyArea);

// 4. Thresholding difference for specular backscatter reflection on open water
// Water exhibits dramatic specular reduction in backscatter compared to land
var difference = postFlood.subtract(preFlood);
var floodThreshold = -3.2; // dB drop threshold
var flooded = difference.lt(floodThreshold);

// 5. Mask permanent water bodies using JRC Global Surface Water
var jrcWater = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence');
var permanentWater = jrcWater.gt(80);
var floodInundation = flooded.where(permanentWater, 0).selfMask();

// 6. Terrain slope masking: remove steep terrain shadows (> 5 degrees per DEC02)
var dem = ee.Image('USGS/SRTMGL1_003');
var slope = ee.Terrain.slope(dem);
var floodClean = floodInundation.updateMask(slope.lt(5));

Map.centerObject(studyArea, 7);
Map.addLayer(preFlood, {min: -25, max: -5}, 'Pre-Flood SAR Baseline', false);
Map.addLayer(postFlood, {min: -25, max: -5}, 'Peak-Flood SAR Scene', false);
Map.addLayer(floodClean, {palette: ['0000FF']}, 'Sentinel-1 Observed Flood Extent (G25)');

// 7. Export Inundation Polygon to Drive / Asset
Export.image.toDrive({
  image: floodClean,
  description: 'CHER_CDSS_G25_Sentinel1_SAR_Flood_Inundation_2026',
  scale: 30,
  region: studyArea,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});
