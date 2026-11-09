with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '<script>' in l:
        print(f"<script> starts at line {i+1}")
    if '</script>' in l:
        print(f"</script> ends at line {i+1}")
