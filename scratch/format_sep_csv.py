import csv
from pathlib import Path

path = Path(r"c:\xampp\htdocs\GIS\03_Data\LOOKUPS\LKP_State_EnvironmentalProblems.csv")

records = [
    ["SEP001","NG-ADA","Adamawa","DEFORESTATION","Deforestation",9.3245,12.4512,"Critical","National Environmental Survey Wall Map","Verified from Photo","Green starburst symbol positioned directly over Adamawa in official national poster."],
    ["SEP002","NG-ADA","Adamawa","EROSION","Erosion",9.8512,12.8021,"High","National Environmental Survey Wall Map","Verified from Photo","Red triangle symbol plotted in northern Adamawa highlands/gully belt."],
    ["SEP003","NG-ADA","Adamawa","FLOODING","Flooding",9.2014,12.4831,"Critical","N-HYPPADEC / Upper Benue River Basin Authority","Active Basin Monitor","Lagdo Dam release corridor along Benue River floodplains."],
    ["SEP004","NG-ADA","Adamawa","DROUGHT","Drought",10.2514,13.2045,"High","NiMet / ACReSAL Northern Savanna Drought Register","Active Basin Monitor","Northern dry spell belt impacting pastoral and rainfed agrarian communities."],
    ["SEP005","NG-NIG","Niger","FLOODING","Flooding",9.6100,6.5500,"Critical","N-HYPPADEC Master Hydrological Register","Verified","Downstream flood risk zone along Kainji-Jebba-Shiroro axis."],
    ["SEP006","NG-NIG","Niger","LEAD_POISONING","Lead Poisoning",9.9500,6.8000,"Critical","Federal Ministry of Health / NESREA Lead Incident Log","Verified","Artisanal gold mining lead contamination corridor in Shiroro/Rafi."],
    ["SEP007","NG-NIG","Niger","EROSION","Erosion",9.3500,6.0000,"Medium","CHER-CDSS G26 Erosion Register","Verified","Gully erosion in Mokwa and Bida agricultural zones."],
    ["SEP008","NG-NIG","Niger","SOLID_WASTE","Solid Waste Management",9.6150,6.5400,"High","NESREA Urban Sanitation Audit","Verified","Minna urban open dumping and drainage blockage hotspot."],
    ["SEP009","NG-KEB","Kebbi","FLOODING","Flooding",12.4500,4.2000,"Critical","N-HYPPADEC Flood Disaster Log","Verified","Severe Rima and Niger river basin seasonal inundation."],
    ["SEP010","NG-KEB","Kebbi","DESERTIFICATION","Desertification",12.8000,4.5000,"High","Great Green Wall National Agency","Verified","Arid frontline belt experiencing active sand dune movement."],
    ["SEP011","NG-KEB","Kebbi","DROUGHT","Drought",12.6000,4.3000,"High","NiMet Drought Risk Monitor","Verified","Prolonged dry spells affecting fadama rice and sorghum production."],
    ["SEP012","NG-PLA","Plateau","EROSION","Erosion",9.9000,8.9000,"Critical","CHER-CDSS G26 / NEWMAP Legacy Hotspots","Verified","Severe tin-mining legacy gully erosion across Jos plateau."],
    ["SEP013","NG-PLA","Plateau","ECOLOGICAL_CONFLICT","Ecological Conflict",9.5000,8.8000,"Critical","Ecological Conflict Peace & Resilience Audit","Verified","Pastoral grazing route vs farmland ecological tension."],
    ["SEP014","NG-BEN","Benue","FLOODING","Flooding",7.7300,8.5200,"Critical","N-HYPPADEC / Benue SEMA Flood Register","Verified","River Benue high-volume overflows in Makurdi and surrounding lowlands."],
    ["SEP015","NG-BEN","Benue","ECOLOGICAL_CONFLICT","Ecological Conflict",7.4500,8.9000,"Critical","National Grazing Corridor Resource Assessment","Verified","Riverine basin arable land pressure."],
    ["SEP016","NG-BEN","Benue","EROSION","Erosion",7.2000,8.6000,"High","CHER-CDSS G26 Erosion Hotspots","Verified","Active gully network in Gboko and Otukpo corridors."],
    ["SEP017","NG-KOG","Kogi","FLOODING","Flooding",7.8000,6.7400,"Critical","N-HYPPADEC Confluence Early Warning","Verified","Niger-Benue confluence inundation epicentre at Lokoja."],
    ["SEP018","NG-KOG","Kogi","EROSION","Erosion",7.5000,6.6000,"High","CHER-CDSS G26 Hotspot Register","Verified","Erosion scars in Okene and Ankpa escarpments."],
    ["SEP019","NG-KOG","Kogi","WATER_POLLUTION","Water Pollution",7.7800,6.7200,"Medium","NIWA / Confluence Water Quality Study","Verified","Riverine sedimentation and industrial runoff."],
    ["SEP020","NG-KWA","Kwara","FLOODING","Flooding",8.9500,4.9000,"High","N-HYPPADEC Flood Risk Register","Verified","Edu and Patigi flood-prone riverbanks along River Niger."],
    ["SEP021","NG-KWA","Kwara","EROSION","Erosion",8.5000,4.5500,"Medium","CHER-CDSS G26 Erosion Register","Verified","Gully erosion around Ilorin metropolitan outskirts."],
    ["SEP022","NG-KAD","Kaduna","AIR_POLLUTION","Air Pollution",10.5200,7.4400,"High","NESREA Air Quality Monitoring Station","Verified","Industrial particulate concentrations and vehicle exhaust."],
    ["SEP023","NG-KAD","Kaduna","FLOODING","Flooding",10.5000,7.4200,"High","Kaduna SEMA Flood Vulnerability Log","Verified","Kaduna River flash flood overflows affecting central wards."],
    ["SEP024","NG-KAD","Kaduna","ECOLOGICAL_CONFLICT","Ecological Conflict",10.1000,7.8000,"Critical","Southern Kaduna Resource Dispute Log","Verified","Ecological resource stress and land degradation conflicts."],
    ["SEP025","NG-NAS","Nasarawa","FLOODING","Flooding",8.5000,8.5200,"High","Nasarawa SEMA Rapid Assessment","Verified","Benue tributary backflow in Toto, Doma and Awe LGAs."],
    ["SEP026","NG-NAS","Nasarawa","EROSION","Erosion",8.6000,8.2000,"High","CHER-CDSS G26 Erosion Hotspots","Verified","Gully sites in Keffi and Lafia municipal catchments."],
    ["SEP027","NG-TAR","Taraba","DEFORESTATION","Deforestation",7.8500,10.5000,"Critical","Global Forest Watch / TAR SEMA Survey","Verified","Intensive illegal rosewood (Madrid) logging and forest clearance."],
    ["SEP028","NG-TAR","Taraba","FLOODING","Flooding",8.9000,11.3600,"Critical","N-HYPPADEC Riverine Monitoring","Verified","Upper Benue and Donga river basin annual flash inundation."],
    ["SEP029","NG-TAR","Taraba","ECOLOGICAL_CONFLICT","Ecological Conflict",7.2000,10.8000,"Critical","Mambilla Plateau Resource Audit","Verified","Highland grazing land allocation and ecological disputes."],
    ["SEP030","NG-GOM","Gombe","EROSION","Erosion",10.2800,11.1700,"Critical","NEWMAP Gombe State Interventions","Verified","Severe deep gully complexes threatening Gombe town."],
    ["SEP031","NG-GOM","Gombe","DESERTIFICATION","Desertification",10.8000,11.4000,"High","Frontline Shelterbelt Monitoring","Verified","Dukku and Funakaye semi-arid vegetative decline."],
    ["SEP032","NG-ZAM","Zamfara","LEAD_POISONING","Lead Poisoning",12.1600,6.6600,"Critical","MSF / Federal Ministry of Health Report","Verified","Historic and active artisanal gold ore milling lead poisoning epicentre."],
    ["SEP033","NG-RIV","Rivers","OIL_SPILLAGE","Oil Spillage",4.8100,7.0400,"Critical","NOSDRA National Oil Spill Monitor","Verified","Major crude oil spillage, pipeline ruptures, and mangrove destruction."],
    ["SEP034","NG-RIV","Rivers","WATER_POLLUTION","Water Pollution",4.7500,7.0000,"Critical","Niger Delta Water Quality Assessment","Verified","Hydrocarbon pollution of creeks and drinking boreholes."],
    ["SEP035","NG-BAY","Bayelsa","OIL_SPILLAGE","Oil Spillage",4.7500,6.1000,"Critical","NOSDRA Pipeline Incident Registry","Verified","Severe oil spills across Nembe, Brass, and Southern Ijaw creeks."],
    ["SEP036","NG-LAG","Lagos","AIR_POLLUTION","Air Pollution",6.5244,3.3792,"Critical","Lagos LASEPA Clean Air Initiative","Verified","High PM2.5 concentrations from traffic congestion and industrial clusters."],
    ["SEP037","NG-LAG","Lagos","SOLID_WASTE","Solid Waste Management",6.6012,3.3514,"Critical","LAWMA Dumpsite Environmental Audit","Verified","Olusosun landfill capacity and uncollected urban plastic runoff."],
    ["SEP038","NG-KAN","Kano","SOLID_WASTE","Solid Waste Management",11.9800,8.5300,"Critical","Kano REMASAB Waste Register","Verified","Open urban disposal and market organic waste blockage of canals."],
    ["SEP039","NG-KAN","Kano","AIR_POLLUTION","Air Pollution",12.0000,8.5100,"High","Sharada / Bompai Industrial Emissions Log","Verified","Tannery and textile industrial smoke plus dust storms."],
    ["SEP040","NG-BOR","Borno","DESERTIFICATION","Desertification",11.8333,13.1500,"Critical","Lake Chad Basin Commission / GGW","Verified","Lake Chad recession and extreme Saharan encroachment."]
]

header = ["Record_ID","State_Code","State_Name","Problem_Code","Problem_Name","Latitude","Longitude","Severity_Level","Observed_Source","Validation_Status","Notes"]

with open(path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerows(records)

print("Saved clean LKP_State_EnvironmentalProblems.csv")
