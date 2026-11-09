"""
18_maps.py
==========
Map export module — generates standardised map metadata records and
export-ready CSV/GeoJSON files for each of the 27 map outputs.

Full cartographic rendering (PDF/PNG) requires QGIS Desktop or a GIS
rendering library. This module:
  1. Produces a MAP_REGISTER.csv recording all map outputs, their source
     layers, status, and standard cartographic element checklist.
  2. For maps that can be produced from CSV data, generates GeoJSON-ready
     output files for import into QGIS project templates.
  3. Applies the standard map element checklist (title, legend, north arrow,
     scale bar, CRS, sources, data date, map date, project name, version,
     author/unit) per MAP_PRODUCTION_STANDARD in the spec.

All final maps exported as PDFs are stored in 04_GIS/05_MAP_EXPORTS/.
Map files versioned: MAP_01_Study_Area_v1_0.pdf etc.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    ANALYSIS_OUTPUTS, REPORTS_FIGURES,
    GIS_MAPS, REPORTS_TABLES,
    DATA_DATE, RISK_MODEL_VERSION, BASELINE_VERSION,
)
from logger import get_logger, log_separator

log = get_logger("18_maps")

# Standard map element checklist — every final map must have all of these
MAP_ELEMENTS_REQUIRED = [
    "Title", "Legend", "North_Arrow", "Scale_Bar",
    "CRS", "Sources", "Data_Date", "Map_Date",
    "Project_Name", "Version", "Author_Unit",
]

# Map register: all planned map outputs
MAP_REGISTER_TEMPLATE = [
    {"Map_ID": "MAP_01", "Map_Name": "Study Area Overview",
     "Primary_Layer": "G01", "Supporting_Layers": "G02,G05,G16",
     "Category": "Base"},
    {"Map_ID": "MAP_02", "Map_Name": "Community Sampling",
     "Primary_Layer": "G03", "Supporting_Layers": "G01,G02",
     "Category": "Base"},
    {"Map_ID": "MAP_03", "Map_Name": "Community Risk Overview",
     "Primary_Layer": "G35", "Supporting_Layers": "G01,G02,G03",
     "Category": "Risk"},
    {"Map_ID": "MAP_04", "Map_Name": "Hydrology and River Network",
     "Primary_Layer": "G05", "Supporting_Layers": "G01,G06,G07,G08",
     "Category": "Hydrology"},
    {"Map_ID": "MAP_05", "Map_Name": "Flood Hazard",
     "Primary_Layer": "G24", "Supporting_Layers": "G01,G03,G05,G25",
     "Category": "Hazard"},
    {"Map_ID": "MAP_06", "Map_Name": "Hydropower Facilities",
     "Primary_Layer": "G07", "Supporting_Layers": "G01,G05,G08,G28",
     "Category": "Infrastructure"},
    {"Map_ID": "MAP_07", "Map_Name": "Terrain and Elevation",
     "Primary_Layer": "G09", "Supporting_Layers": "G10,G12",
     "Category": "Terrain"},
    {"Map_ID": "MAP_08", "Map_Name": "Hillshade",
     "Primary_Layer": "G12", "Supporting_Layers": "G01",
     "Category": "Terrain"},
    {"Map_ID": "MAP_09", "Map_Name": "Land Cover",
     "Primary_Layer": "G15", "Supporting_Layers": "G01,G03",
     "Category": "Environment"},
    {"Map_ID": "MAP_10", "Map_Name": "Infrastructure Inventory",
     "Primary_Layer": "G19", "Supporting_Layers": "G01,G16,G17,G18",
     "Category": "Infrastructure"},
    {"Map_ID": "MAP_11", "Map_Name": "Flood and Erosion Exposure",
     "Primary_Layer": "G29", "Supporting_Layers": "G01,G03,G30",
     "Category": "Exposure"},
    {"Map_ID": "MAP_12", "Map_Name": "Critical Facilities",
     "Primary_Layer": "G18", "Supporting_Layers": "G01,G19",
     "Category": "Infrastructure"},
    {"Map_ID": "MAP_13", "Map_Name": "Climate Stations",
     "Primary_Layer": "G20", "Supporting_Layers": "G01,G21",
     "Category": "Climate"},
    {"Map_ID": "MAP_14", "Map_Name": "Mean Annual Rainfall Surface",
     "Primary_Layer": "G22", "Supporting_Layers": "G01,G20",
     "Category": "Climate"},
    {"Map_ID": "MAP_15", "Map_Name": "Mean Annual Temperature Surface",
     "Primary_Layer": "G23", "Supporting_Layers": "G01,G20",
     "Category": "Climate"},
    {"Map_ID": "MAP_16", "Map_Name": "Observed Flood Events",
     "Primary_Layer": "G25", "Supporting_Layers": "G01,G03,G05",
     "Category": "Hazard"},
    {"Map_ID": "MAP_17", "Map_Name": "Erosion Sites Inventory",
     "Primary_Layer": "G26", "Supporting_Layers": "G01,G03",
     "Category": "Erosion"},
    {"Map_ID": "MAP_18", "Map_Name": "Erosion Severity",
     "Primary_Layer": "G26", "Supporting_Layers": "G01,G03",
     "Category": "Erosion"},
    {"Map_ID": "MAP_19", "Map_Name": "Erosion Hotspots",
     "Primary_Layer": "G27", "Supporting_Layers": "G01,G03,G26",
     "Category": "Erosion"},
    {"Map_ID": "MAP_20", "Map_Name": "Composite Risk Index",
     "Primary_Layer": "G35", "Supporting_Layers": "G01,G02,G03,G12",
     "Category": "Risk"},
    {"Map_ID": "MAP_21", "Map_Name": "Hazard Index",
     "Primary_Layer": "G31", "Supporting_Layers": "G01,G03",
     "Category": "Risk"},
    {"Map_ID": "MAP_22", "Map_Name": "Exposure Index",
     "Primary_Layer": "G32", "Supporting_Layers": "G01,G03",
     "Category": "Risk"},
    {"Map_ID": "MAP_23", "Map_Name": "Vulnerability Index",
     "Primary_Layer": "G33", "Supporting_Layers": "G01,G03",
     "Category": "Risk"},
    {"Map_ID": "MAP_24", "Map_Name": "Criticality Index",
     "Primary_Layer": "G34", "Supporting_Layers": "G01,G03",
     "Category": "Risk"},
    {"Map_ID": "MAP_25", "Map_Name": "Risk Classification",
     "Primary_Layer": "G35", "Supporting_Layers": "G01,G02,G03",
     "Category": "Risk"},
    {"Map_ID": "MAP_26", "Map_Name": "Adaptation Inventory",
     "Primary_Layer": "G36", "Supporting_Layers": "G01,G03",
     "Category": "Adaptation"},
    {"Map_ID": "MAP_27", "Map_Name": "Priority Areas",
     "Primary_Layer": "G37", "Supporting_Layers": "G01,G02,G03",
     "Category": "Priority"},
]


# ---------------------------------------------------------------------------
# Map register
# ---------------------------------------------------------------------------

def build_map_register() -> pd.DataFrame:
    """
    Build/update the MAP_REGISTER.csv recording all 27 map outputs,
    their source layers, cartographic element checklist, and export status.
    """
    today = date.today().isoformat()
    records = []

    for m in MAP_REGISTER_TEMPLATE:
        record = {
            **m,
            "File_Name":        f"{m['Map_ID']}_{m['Map_Name'].replace(' ','_')}_v1_0.pdf",
            "Version":          BASELINE_VERSION,
            "Data_Date":        DATA_DATE,
            "Map_Date":         today,
            "CRS":              "EPSG:4326",
            "Project_Name":     "N-HYPPADEC GIS Decision-Support System",
            "Risk_Model_Version": RISK_MODEL_VERSION,
            "Export_Status":    "Pending",
            "Export_Path":      str(GIS_MAPS / f"{m['Map_ID']}_{m['Map_Name'].replace(' ','_')}_v1_0.pdf"),
        }
        # Add cartographic element status fields
        for elem in MAP_ELEMENTS_REQUIRED:
            record[f"Has_{elem}"] = "Pending"

        records.append(record)

    df = pd.DataFrame(records)

    REPORTS_FIGURES.mkdir(parents=True, exist_ok=True)
    out = REPORTS_FIGURES / "MAP_REGISTER.csv"
    df.to_csv(out, index=False)
    log.info(f"Map register created: {out} ({len(df)} maps planned)")
    return df


# ---------------------------------------------------------------------------
# Export-ready community data (for QGIS import)
# ---------------------------------------------------------------------------

def export_community_map_data() -> None:
    """
    Write a consolidated community point file with all risk scores
    ready for QGIS import and map production.
    """
    g37_path = ANALYSIS_OUTPUTS / "G37_PriorityAreas.csv"
    if not g37_path.exists():
        log.warning("G37 not found — community map export skipped")
        return

    df = pd.read_csv(g37_path)

    # Add DB01 coordinates
    db01_path = Path(__file__).parent.parent.parent / "03_Data" / "CLEAN" / \
                "DB01_Community_Master_CLEAN.csv"
    if db01_path.exists():
        db01 = pd.read_csv(db01_path)[["Community_ID","Latitude","Longitude","Population"]]
        df = df.merge(db01, on="Community_ID", how="left")

    # Check required coordinate columns present
    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        log.warning("No coordinates available — community map export skipped")
        return

    # Select map-relevant columns only (no household data)
    map_cols = [
        "Community_ID","Community" if "Community" in df.columns else "Community_ID",
        "State_Code","LGA_Code","Latitude","Longitude","Population",
        "H_Score","E_Score","V_Score","C_Score","R_Score","R_Class",
        "Priority_Score","Priority_Tier","Priority_Rank","Data_Confidence",
    ]
    export_cols = [c for c in map_cols if c in df.columns]
    export_df = df[export_cols].copy()
    export_df["Map_Date"] = date.today().isoformat()

    GIS_MAPS.mkdir(parents=True, exist_ok=True)
    out_csv = GIS_MAPS / "Community_Risk_MapData_v1_0.csv"
    export_df.to_csv(out_csv, index=False)
    log.info(f"Community map data exported: {out_csv} ({len(export_df)} communities)")

    # GeoJSON export
    try:
        import json
        features = []
        for _, row in export_df.dropna(subset=["Latitude","Longitude"]).iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["Longitude"]), float(row["Latitude"])],
                },
                "properties": {
                    k: (None if pd.isna(v) else v)
                    for k, v in row.items()
                    if k not in ["Latitude","Longitude"]
                },
            }
            features.append(feature)

        geojson = {"type": "FeatureCollection", "features": features}
        out_json = GIS_MAPS / "Community_Risk_MapData_v1_0.geojson"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, default=str)
        log.info(f"GeoJSON exported: {out_json}")

    except Exception as exc:
        log.warning(f"GeoJSON export failed: {exc}")


# ---------------------------------------------------------------------------
# Map element checklist verification
# ---------------------------------------------------------------------------

def verify_map_elements(map_file_path: Path, map_id: str) -> dict:
    """
    Record which cartographic elements are present in a map file.
    Full verification requires manual review — this generates the checklist
    template that a cartographer confirms.
    Returns checklist dict.
    """
    checklist = {f"Has_{elem}": "Pending" for elem in MAP_ELEMENTS_REQUIRED}
    checklist["Map_ID"]      = map_id
    checklist["Map_File"]    = str(map_file_path)
    checklist["Check_Date"]  = date.today().isoformat()
    checklist["Verified_By"] = "Pending — cartographer review required"
    return checklist


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_all() -> None:
    log_separator(log, "18_MAPS — Map Register and Export Preparation")
    GIS_MAPS.mkdir(parents=True, exist_ok=True)
    REPORTS_FIGURES.mkdir(parents=True, exist_ok=True)

    build_map_register()
    export_community_map_data()

    log.info(
        "18_maps complete.\n"
        f"  MAP_REGISTER.csv: 27 maps registered in {REPORTS_FIGURES}\n"
        f"  Community map data ready for QGIS in {GIS_MAPS}\n"
        "  NOTE: Final PDF map production requires QGIS Desktop with project "
        "templates in 04_GIS/04_PROJECTS/. "
        "Every map must pass cartographic element checklist before publication."
    )


if __name__ == "__main__":
    run_all()
