with open('07_Decision_Support/02_Dashboards/app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'function loadSitRepDashboard' in l or 'function loadInterventionsData' in l or 'function loadFieldOpsDashboard' in l or 'function loadFloodDashboard' in l:
        print(f"Line {i+1}: {l.strip()}")

