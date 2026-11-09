import re

with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Find buttons or links with switch, tab, or view
matches = re.findall(r'<button[^>]*onclick=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</button>', text)
for fn, label in matches[:25]:
    lbl = re.sub(r'\s+', ' ', label).strip()
    if any(k in fn.lower() or k in lbl.lower() for k in ['tab', 'view', 'nav', 'switch', 'show', 'page']):
        print(f"Action: {fn} -> {lbl}")

# Find section IDs
sections = re.findall(r'<div[^>]*id=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*view[^"\']*["\']', text)
print("Views:", sections)
sections2 = re.findall(r'<section[^>]*id=["\']([^"\']+)["\']', text)
print("Sections:", sections2)
