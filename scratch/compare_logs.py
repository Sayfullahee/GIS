import csv

with open('00_Project_Control/PROCESSING_STATUS.csv', 'r', encoding='utf-8') as f:
    ps = list(csv.DictReader(f))
with open('00_Project_Control/VERSION_LOG.csv', 'r', encoding='utf-8') as f:
    vl = list(csv.DictReader(f))

vl_assets = set(r['Asset_ID'] for r in vl)
for r in ps:
    aid = r['Asset_ID']
    in_vl = aid in vl_assets
    print(f"{aid:20} Current_Status: {r['Current_Status']:10} QC_Passed: {r['QC_Passed']:5} in_vl: {in_vl}")
