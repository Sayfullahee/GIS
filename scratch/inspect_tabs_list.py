import re

with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

tabs = re.findall(r"switchTab\(['\"]([^'\"]+)['\"]\)", text)
print("Unique switchTab targets:", sorted(list(set(tabs))))
