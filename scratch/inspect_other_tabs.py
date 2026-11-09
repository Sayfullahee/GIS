with open('07_Decision_Support/02_Dashboards/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('id="tab-flood"')
if pos != -1:
    print("FLOOD TAB:")
    print(text[pos:pos+1500])

pos2 = text.find('id="tab-interventions"')
if pos2 != -1:
    print("\nINTERVENTIONS TAB:")
    print(text[pos2:pos2+1500])
