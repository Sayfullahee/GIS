import re

with open(r'07_Decision_Support\02_Dashboards\app.py', 'r', encoding='utf-8') as f:
    text = f.read()

print('=== SCRIPT TAGS (Leaflet/JS) ===')
for m in re.finditer(r'<script[^>]*src=[\'"][^\'"]*[\'"][^>]*>', text):
    print(m.group(0))

print('\n=== MAP CONTAINERS ===')
for m in re.finditer(r'<div[^>]*id=[\'"][^\'"]*map[^\'"]*[\'"][^>]*>', text, re.I):
    print(m.group(0))

print('\n=== L.map calls ===')
for m in re.finditer(r'L\.map\([^\)]*\)', text):
    print(m.group(0))

print('\n=== Leaflet tileLayer calls ===')
for m in re.finditer(r'L\.tileLayer\([^\)]*\)', text):
    print(m.group(0))
