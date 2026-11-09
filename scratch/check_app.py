import re

with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

routes = re.findall(r'@app\.(?:get|post)\(["\']([^"\']+)', text)
print('Routes in app.py:')
for r in routes:
    print(' ', r)

# check for map or alert in text
print("\nOccurrences of 'map':", len(re.findall(r'map', text, re.IGNORECASE)))
print("Occurrences of 'flood':", len(re.findall(r'flood', text, re.IGNORECASE)))
print("Occurrences of 'alert':", len(re.findall(r'alert', text, re.IGNORECASE)))
