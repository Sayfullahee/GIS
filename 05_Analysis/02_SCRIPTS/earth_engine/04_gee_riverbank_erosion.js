/**
 * 04_gee_riverbank_erosion.js
 * ===========================
 * Google Earth Engine (GEE) Script for Multi-Temporal Riverbank Retreat & Erosion
 * N-HYPPADEC / CHER-CDSS — 10 Member States of Nigeria
 * Standard: Scaffold v4.1 Stage 9.6 & Layer G26/G27 (Erosion Sites & Hotspots)
 */

// Focused river corridor: Niger and Benue active gully zones
var riverCorridors = ee.Geometry.MultiPoint([
  [6.85, 9.50], // Niger State gully corridor
  [4.53, 12.74], // Kebbi Argungu floodplain
  [8.53, 7.73],  // Benue Makurdi riverfront
  [6.74, 7.80]   // Kogi Lokoja confluence
]);

var studyCorridor = riverCorridors.buffer(50000); // 50km monitoring envelope

// 1. Modified Normalized Difference Water Index (MNDWI)
// MNDWI = (Green - SWIR) / (Green + SWIR) -> (B3 - B11) / (B3 + B11)
function getMNDWI(yearStart, yearEnd) {
  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(studyCorridor)
              .filterDate(yearStart, yearEnd)
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
              .median();
  return col.normalizedDifference(['B3', 'B11']).rename('MNDWI');
}

// 2. Multi-temporal waterlines (2018 vs 2026)
var mndwi_2018 = getMNDWI('2018-01-01', '2018-03-31');
var mndwi_2026 = getMNDWI('2026-01-01', '2026-03-31');

// Threshold water mask: MNDWI > 0
var water_2018 = mndwi_2018.gt(0.0).rename('WATER_2018');
var water_2026 = mndwi_2026.gt(0.0).rename('WATER_2026');

// 3. Bank erosion occurs where land in 2018 transitioned to water in 2026
var bankErosion = water_2026.and(water_2018.not()).selfMask().rename('BANK_EROSION');

Map.centerObject(riverCorridors, 8);
Map.addLayer(water_2018, {palette: ['lightblue']}, 'Water Extent 2018');
Map.addLayer(water_2026, {palette: ['darkblue']}, 'Water Extent 2026');
Map.addLayer(bankErosion, {palette: ['red']}, 'Riverbank Land Loss / Gully Incursion (2018-2026)');

// Export Riverbank Change GeoTIFF
Export.image.toDrive({
  image: bankErosion,
  description: 'CHER_CDSS_G26_Riverbank_Retreat_2018_2026',
  scale: 10,
  region: studyCorridor,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});
