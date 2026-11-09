import re

with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("--- CSS for maps ---")
for m in re.finditer(r'(#[a-zA-Z0-9_-]*map[a-zA-Z0-9_-]*\s*\{[^}]*\})', text, re.IGNORECASE):
    print(m.group(1))

print("\n--- HTML containers with 'map' ---")
for line in text.splitlines():
    if 'id=' in line and 'map' in line.lower():
        print(line.strip())

print("\n--- JS map initialization & usage ---")
for i, line in enumerate(text.splitlines()):
    if 'L.map' in line or 'floodMap' in line or 'tileLayer' in line or 'map.' in line:
        print(f"{i+1}: {line.strip()[:100]}")
