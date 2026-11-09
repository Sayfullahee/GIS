import sys
sys.path.append('07_Decision_Support/02_Dashboards')
import app

sites = app.get_priority_sites_geojson()
features = sites.get('features', [])
print(f"Total priority site features: {len(features)}")
null_tiers = 0
null_names = 0
tiers = set()
for f in features:
    props = f.get('properties', {})
    t = props.get('tier')
    if t is None:
        null_tiers += 1
    else:
        tiers.add(str(t))

print(f"Null tiers: {null_tiers}")
print(f"Unique tiers: {tiers}")
