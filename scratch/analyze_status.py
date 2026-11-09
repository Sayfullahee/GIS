import csv

with open('00_Project_Control/PROCESSING_STATUS.csv', 'r', encoding='utf-8') as f:
    reader = list(csv.DictReader(f))
    print(f'Total rows in PROCESSING_STATUS: {len(reader)}')
    by_status = {}
    for r in reader:
        s = r.get('Current_Status', 'Unknown')
        by_status.setdefault(s, []).append(r)
    for s, rows in by_status.items():
        print(f'Status: {s} ({len(rows)} items)')
        for r in rows:
            print(f"   [{r.get('Asset_ID')}] {r.get('Asset_Type')}: {r.get('Asset_Name')} | QC_Passed: {r.get('QC_Passed')}")
