import sys
sys.path.append('07_Decision_Support/02_Dashboards')
import app

for ep, fn in [
    ('dashboard', app.get_flood_dashboard),
    ('alerts', app.get_flood_alerts),
    ('performance', app.get_flood_warning_performance),
    ('levels', app.get_flood_warning_levels),
    ('geojson', app.get_flood_alert_geojson),
]:
    try:
        res = fn()
        print(f"{ep}: OK - {type(res)}")
        if ep == 'geojson':
            print("  features count:", len(res.get('features', [])))
            if res.get('features'):
                print("  feature 0 props:", res['features'][0].get('properties'))
        elif ep == 'alerts':
            print("  status:", res.get('status'), "count:", res.get('count'))
        elif ep == 'dashboard':
            print("  status:", res.get('status'), "active_warnings:", res.get('active_warnings'))
    except Exception as e:
        print(f"{ep}: FAILED: {e}")
