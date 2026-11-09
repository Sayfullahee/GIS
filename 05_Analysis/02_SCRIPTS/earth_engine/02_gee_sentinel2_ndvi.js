/**
 * 02_gee_sentinel2_ndvi.js
 * ========================
 * Google Earth Engine (GEE) Script for Sentinel-2 MSI NDVI & Vegetation Anomaly
 * N-HYPPADEC / CHER-CDSS — 10 Member States of Nigeria
 * Standard: Scaffold v4.1 Stage 9.4 (Vegetation Products & Anomalies)
 */

var studyArea = ee.Geometry.Polygon([
  [[3.2, 6.5], [12.0, 6.5], [12.0, 13.5], [3.2, 13.5], [3.2, 6.5]]
]);

// 1. Cloud masking using S2 Scene Classification Layer (SCL)
function maskS2clouds(image) {
  var scl = image.select('SCL');
  // Keep vegetation (4), bare soil (5), water (6)
  var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
  return image.updateMask(mask).divide(10000);
}

// 2. Load Sentinel-2 Level-2A BOA Surface Reflectance (2026 Peak Wet Season)
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterBounds(studyArea)
           .filterDate('2026-07-01', '2026-09-30')
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
           .map(maskS2clouds)
           .median()
           .clip(studyArea);

// 3. Compute Normalized Difference Vegetation Index (NDVI)
// NDVI = (NIR - RED) / (NIR + RED) -> (B8 - B4) / (B8 + B4)
var ndvi_2026 = s2.normalizedDifference(['B8', 'B4']).rename('NDVI_2026');

// 4. Long-term Historical Baseline (2019-2025 median)
var s2_hist = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(studyArea)
                .filterDate('2019-07-01', '2025-09-30')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .map(maskS2clouds)
                .median()
                .clip(studyArea);

var ndvi_hist = s2_hist.normalizedDifference(['B8', 'B4']).rename('NDVI_HIST');

// 5. Vegetation Anomaly (Current minus Historical Baseline)
var ndvi_anomaly = ndvi_2026.subtract(ndvi_hist).rename('NDVI_ANOMALY');

var ndviVis = {min: 0.0, max: 0.8, palette: ['d73027', 'f46d43', 'fdae61', 'fee08b', 'd9ef8b', 'a6d96a', '66bd63', '1a9850']};
var anomVis = {min: -0.2, max: 0.2, palette: ['ca0020', 'f4a582', 'f7f7f7', '92c5de', '0571b0']};

Map.centerObject(studyArea, 7);
Map.addLayer(ndvi_2026, ndviVis, 'Sentinel-2 NDVI 2026 Baseline');
Map.addLayer(ndvi_anomaly, anomVis, 'NDVI Anomaly (Negative = Drought / Silt Stress)');

// Export GeoTIFF for CHER-CDSS Ingestion
Export.image.toDrive({
  image: ndvi_anomaly,
  description: 'CHER_CDSS_Sentinel2_NDVI_Anomaly_2026',
  scale: 30,
  region: studyArea,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});
