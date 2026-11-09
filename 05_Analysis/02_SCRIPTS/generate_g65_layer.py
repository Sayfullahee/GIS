import csv
import json
from pathlib import Path

BASE_DIR = Path(r"c:\xampp\htdocs\GIS")
LOOKUP_PROBLEMS = BASE_DIR / "03_Data" / "LOOKUPS" / "LKP_EnvironmentalProblems.csv"
LOOKUP_STATE_PROBLEMS = BASE_DIR / "03_Data" / "LOOKUPS" / "LKP_State_EnvironmentalProblems.csv"
GEOJSON_OUT = BASE_DIR / "04_GIS" / "03_DERIVED" / "G65_EnvironmentalProblems.geojson"
METADATA_OUT = BASE_DIR / "04_GIS" / "06_METADATA" / "G65_EnvironmentalProblems_METADATA.csv"
SCHEMA_OUT = BASE_DIR / "04_GIS" / "06_METADATA" / "G65_EnvironmentalProblems_SCHEMA.csv"

# Load problems lookup
problems = {}
with open(LOOKUP_PROBLEMS, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        problems[row["Problem_Code"]] = row

features = []
with open(LOOKUP_STATE_PROBLEMS, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        p_code = row["Problem_Code"]
        p_info = problems.get(p_code, {})
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "record_id": row["Record_ID"],
                "state_code": row["State_Code"],
                "state_name": row["State_Name"],
                "problem_code": p_code,
                "problem_name": row["Problem_Name"],
                "category": p_info.get("Category", "Environmental"),
                "symbol_shape": p_info.get("Symbol_Shape", "circle"),
                "symbol_color": p_info.get("Symbol_Color_Hex", "#38BDF8"),
                "symbol_char": p_info.get("Symbol_Char", "●"),
                "photo_order": int(p_info.get("Photo_Legend_Order", 99)),
                "severity": row["Severity_Level"],
                "source": row["Observed_Source"],
                "status": row["Validation_Status"],
                "notes": row["Notes"]
            }
        }
        features.append(feat)

geojson_data = {
    "type": "FeatureCollection",
    "name": "G65_EnvironmentalProblems",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": features
}

with open(GEOJSON_OUT, mode="w", encoding="utf-8") as f:
    json.dump(geojson_data, f, indent=2)

print(f"Generated {len(features)} GeoJSON features at {GEOJSON_OUT}")

# Create METADATA CSV
meta_rows = [
    ["Metadata_Item", "Value"],
    ["Layer_ID", "G65"],
    ["Layer_Name", "G65_EnvironmentalProblems"],
    ["Specification_Source", "Official National Environmental Survey Legend (Photo Standard)"],
    ["Coordinate_System", "EPSG:4326 (WGS 84)"],
    ["Feature_Type", "Vector Point"],
    ["Total_Features", str(len(features))],
    ["Taxonomy_Items", "14 (Air Pollution, Climate Change, Deforestation, Desertification, Drought, Ecological Conflict, Erosion, Flooding, Lead Poisoning, Oil Spillage, Solid Waste Management, Water Pollution, Food Security, Bandit Attack)"],
    ["Adamawa_Observations", "Deforestation (green starburst) and Erosion (red triangle) documented from official national survey map"],
    ["Member_State_Coverage", "10 N-HYPPADEC States + Adamawa Extended Basin State + Selected National Benchmarks"],
    ["Version", "v1.0 (Integrated October 2026)"],
    ["Custodian", "Federal Ministry of Environment / NESREA / N-HYPPADEC CHER-CDSS"],
    ["Status", "Active QC Validated"]
]

with open(METADATA_OUT, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(meta_rows)

print(f"Generated Metadata at {METADATA_OUT}")

# Create SCHEMA CSV
schema_rows = [
    ["Field_Name", "Data_Type", "Description", "Example"],
    ["record_id", "String(10)", "Unique event identifier", "SEP001"],
    ["state_code", "String(10)", "State ISO/Internal Code", "NG-ADA"],
    ["state_name", "String(50)", "State Name", "Adamawa"],
    ["problem_code", "String(30)", "Standard problem code", "DEFORESTATION"],
    ["problem_name", "String(60)", "Human-readable name matching photo", "Deforestation"],
    ["category", "String(40)", "Environmental category", "Land & Biosphere"],
    ["symbol_shape", "String(30)", "Legend symbology shape", "starburst"],
    ["symbol_color", "String(10)", "Hexadecimal symbol color", "#16A34A"],
    ["symbol_char", "String(10)", "Unicode symbol representation", "✱"],
    ["photo_order", "Integer", "1-12 sort order matching photo", "3"],
    ["severity", "String(20)", "Severity ranking (Critical/High/Medium)", "Critical"],
    ["source", "String(100)", "Survey observation origin", "National Environmental Survey Wall Map"],
    ["status", "String(40)", "Validation status", "Verified from Photo"],
    ["notes", "String(255)", "Contextual description", "Green starburst symbol positioned directly over Adamawa"]
]

with open(SCHEMA_OUT, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(schema_rows)

print(f"Generated Schema at {SCHEMA_OUT}")
