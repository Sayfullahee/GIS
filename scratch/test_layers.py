import urllib.request, json

for lid in ['G01', 'G05', 'G07', 'G08', 'G24', 'G38', 'G39', 'G43']:
    try:
        res = urllib.request.urlopen(f'http://localhost:8000/api/geojson/layer/{lid}')
        d = json.loads(res.read())
        print(f'{lid}: {res.status} features={len(d.get("features", []))}')
    except Exception as e:
        print(f'{lid}: ERROR {e}')
