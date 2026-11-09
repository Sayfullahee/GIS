with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('function loadSitRepDashboard')
if pos != -1:
    print(text[pos:pos+1500])
