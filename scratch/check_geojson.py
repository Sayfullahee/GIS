import json

for name in ['G38_Flood_Alert_Zones_v1_0', 'G39_Flood_Warning_Points_v1_0', 'G43_Recent_Flood_Extent_v1_0']:
    with open(f'04_GIS/03_DERIVED/{name}.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'{name}: {len(data["features"])} features')
    if data['features']:
        print('  properties sample:', data['features'][0]['properties'])
