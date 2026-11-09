with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines mentioning #map or id=\"map\":")
for i, l in enumerate(lines):
    if '#map' in l or 'id="map"' in l:
        print(f"{i+1}: {l.strip()}")
