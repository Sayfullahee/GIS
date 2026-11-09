with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
scripts = [m.start() for m in re.finditer(r'<script>', text)]
print("Script tags at positions:", scripts)

# Look at end of document
print("\nEnd of app.py (last 1000 chars):")
print(text[-1000:])
