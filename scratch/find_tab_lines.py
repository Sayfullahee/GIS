with open('07_Decision_Support/02_Dashboards/app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'id="tab-flood"' in l or 'id="tab-multi_hazard"' in l or 'id="tab-interventions"' in l or 'id="tab-field_ops"' in l:
        print(f"Line {i+1}: {l.strip()}")

