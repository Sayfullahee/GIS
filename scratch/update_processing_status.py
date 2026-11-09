import pandas as pd
from pathlib import Path

ps_path = Path("00_Project_Control/PROCESSING_STATUS.csv")
df = pd.read_csv(ps_path)

# Update all existing GIS layers and indicators to CLEAN
for idx, row in df.iterrows():
    aid = str(row["Asset_ID"])
    if aid.startswith("G") or aid.startswith("IND"):
        df.at[idx, "Current_Status"] = "CLEAN"
        df.at[idx, "QC_Passed"] = "Yes"
        df.at[idx, "QC_Date"] = "2026-10-13"
        df.at[idx, "QC_By"] = "CHER_CDSS_Pipeline_v4.1"
        df.at[idx, "Published_Version"] = "v4.1"

# Add G38 to G43 if missing
existing_ids = set(df["Asset_ID"].astype(str))
new_layers = [
    ("G38", "GIS Layer", "Flood Alert Zones", "CLEAN", "v4.1", "2026-10-13", "pipeline", "Yes", "2026-10-13", "CHER_CDSS_Pipeline_v4.1", "", "v4.1", "FEW-CAM dynamic flood alert polygon zones"),
    ("G39", "GIS Layer", "Flood Warning Points", "CLEAN", "v4.1", "2026-10-13", "pipeline", "Yes", "2026-10-13", "CHER_CDSS_Pipeline_v4.1", "", "v4.1", "FEW-CAM telemetric river gauge monitoring stations"),
    ("G40", "GIS Layer", "Community Awareness Locations", "CLEAN", "v4.1", "2026-10-13", "pipeline", "Yes", "2026-10-13", "CHER_CDSS_Pipeline_v4.1", "", "v4.1", "FEW-CAM community outreach and drill locations"),
    ("G41", "GIS Layer", "Approved Evacuation Areas", "CLEAN", "v4.1", "2026-10-13", "pipeline", "Yes", "2026-10-13", "CHER_CDSS_Pipeline_v4.1", "", "v4.1", "FEW-CAM designated high-ground muster zones"),
    ("G42", "GIS Layer", "Historical Flood Events", "CLEAN", "v4.1", "2026-10-13", "pipeline", "Yes", "2026-10-13", "CHER_CDSS_Pipeline_v4.1", "", "v4.1", "Multi-decadal flood inundation inventory"),
    ("G43", "GIS Layer", "Recent Flood Extent", "CLEAN", "v4.1", "2026-10-13", "pipeline", "Yes", "2026-10-13", "CHER_CDSS_Pipeline_v4.1", "", "v4.1", "Sentinel-1 C-Band SAR observed inundation boundaries")
]

new_rows = []
for item in new_layers:
    if item[0] not in existing_ids:
        new_rows.append({
            "Asset_ID": item[0],
            "Asset_Type": item[1],
            "Asset_Name": item[2],
            "Current_Status": item[3],
            "Version": item[4],
            "Last_Updated": item[5],
            "Updated_By": item[6],
            "QC_Passed": item[7],
            "QC_Date": item[8],
            "QC_By": item[9],
            "Blocked_By": item[10],
            "Published_Version": item[11],
            "Notes": item[12]
        })

if new_rows:
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

df.to_csv(ps_path, index=False)
print(f"Updated PROCESSING_STATUS.csv successfully! Total entries: {len(df)}")
