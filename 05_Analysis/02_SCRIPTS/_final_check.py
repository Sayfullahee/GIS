"""Final v2.0 project verification."""
from pathlib import Path

BASE = Path("c:/xampp/htdocs/GIS")

new_files = [
    "05_Analysis/02_SCRIPTS/20_climate_change.py",
    "05_Analysis/02_SCRIPTS/21_flooding.py",
    "05_Analysis/02_SCRIPTS/22_land_degradation.py",
    "05_Analysis/02_SCRIPTS/23_deforestation.py",
    "05_Analysis/02_SCRIPTS/24_waste_pollution.py",
    "05_Analysis/02_SCRIPTS/25_biodiversity.py",
    "05_Analysis/02_SCRIPTS/26_eri.py",
    "03_Data/CLEAN/DB07_Interventions_SCHEMA.csv",
    "03_Data/CLEAN/DB08_WastePollutionSites_SCHEMA.csv",
    "03_Data/CLEAN/DB09_BiodiversityObservations_SCHEMA.csv",
    "04_GIS/06_METADATA/G38_G42_ClimateChange_METADATA.csv",
    "04_GIS/06_METADATA/G43_G46_Flooding_METADATA.csv",
    "04_GIS/06_METADATA/G47_G50_LandDegradation_METADATA.csv",
    "04_GIS/06_METADATA/G51_G54_Deforestation_METADATA.csv",
    "04_GIS/06_METADATA/G55_G58_WastePollution_METADATA.csv",
    "04_GIS/06_METADATA/G59_G63_Biodiversity_METADATA.csv",
    "04_GIS/06_METADATA/G64_EnvironmentalRiskIndex_METADATA.csv",
    "03_Data/LOOKUPS/LKP_EnvironmentalDomains.csv",
    "03_Data/LOOKUPS/LKP_DroughtClasses.csv",
    "03_Data/LOOKUPS/LKP_LandDegradationClasses.csv",
    "03_Data/LOOKUPS/LKP_WasteSiteTypes.csv",
    "03_Data/LOOKUPS/LKP_HabitatTypes.csv",
    "00_Project_Control/ENVIRONMENTAL_DOMAINS_EXTENSION.md",
    "05_Analysis/01_INPUTS/RUSLE_METHODOLOGY.md",
]

ok = missing = 0
for f in new_files:
    exists = (BASE / f).exists()
    status = "OK  " if exists else "MISS"
    if exists: ok += 1
    else: missing += 1
    print(f"  {status}  {f}")

total_files  = sum(1 for _ in BASE.rglob("*") if _.is_file())
py_scripts   = sum(1 for _ in (BASE/"05_Analysis"/"02_SCRIPTS").glob("*.py"))
gis_meta     = sum(1 for _ in (BASE/"04_GIS"/"06_METADATA").glob("*.csv"))
lookups      = sum(1 for _ in (BASE/"03_Data"/"LOOKUPS").glob("*.csv"))

print(f"\n{'='*55}")
print(f"  CHER-CDSS v2.0 — Project Statistics")
print(f"{'='*55}")
print(f"  Total project files:     {total_files}")
print(f"  Python scripts:          {py_scripts}")
print(f"  GIS metadata files:      {gis_meta}")
print(f"  Lookup tables:           {lookups}")
print(f"  v2.0 new files: {ok} OK; {missing} missing")
print(f"{'='*55}")
