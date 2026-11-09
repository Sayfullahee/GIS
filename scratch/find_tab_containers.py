import re

with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

for t in ['overview', 'flood', 'multi_hazard', 'field_ops', 'sitrep', 'scenarios', 'interventions', 'tables', 'remote_sensing']:
    matches = re.findall(rf'id=["\'](?:tab-)?{t}["\']', text, re.IGNORECASE)
    print(f"Tab '{t}':", matches)
