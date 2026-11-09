import re

with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

tabs = re.findall(r'data-tab=["\']([^"\']+)["\']', text)
print('Data tabs found:', set(tabs))

nav_items = re.findall(r'<button[^>]*class=["\'][^"\']*nav-btn[^"\']*["\'][^>]*>([\s\S]*?)</button>', text)
for b in nav_items:
    print('Nav item:', re.sub(r'\s+', ' ', b).strip())
