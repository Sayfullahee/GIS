import urllib.request
import json
import sys

def test_api():
    base = 'http://127.0.0.1:8000'
    tests_passed = 0
    total_tests = 0

    def check(name, condition, detail=''):
        nonlocal tests_passed, total_tests
        total_tests += 1
        if condition:
            tests_passed += 1
            print(f'  [PASS] {name} {detail}')
        else:
            print(f'  [FAIL] {name} {detail}')

    print('============================================================')
    print('  CHER-CDSS DECISION PLATFORM REST API VERIFICATION')
    print('============================================================')

    # 1. Health
    with urllib.request.urlopen(base + '/api/health') as r:
        d = json.loads(r.read().decode())
        check('Health Status', d.get('status') == 'HEALTHY')
        check('Version Check', d.get('scaffold_version') == 'v4.1')
        check('States Count', d.get('states_count') == 10)
        check('Layers Count', d.get('layers_count') == 43)
        check('Core Database Tables', d.get('database_tables') == 31)

    # 1b. FEW-CAM Dashboard & GIS Register
    with urllib.request.urlopen(base + '/api/layers') as r:
        d = json.loads(r.read().decode())
        layer_ids = [layer['id'] for layer in d.get('layers', [])]
        check('FEW-CAM GIS Layers Registered', all(layer_id in layer_ids for layer_id in ('G38', 'G39', 'G40', 'G41', 'G42', 'G43')))
        g05 = next(layer for layer in d['layers'] if layer['id'] == 'G05')
        check('G05 Main Rivers and Drainage Scope', all(term in g05.get('scope', '').casefold() for term in ('main rivers', 'tributaries', 'distributaries', 'streams', 'drainage channels')))

    with urllib.request.urlopen(base + '/api/flood/warning-levels') as r:
        d = json.loads(r.read().decode())
        check('Four Graduated Flood Warning Levels', [level['level'] for level in d.get('levels', [])] == [0, 1, 2, 3])
        check('Flood Thresholds Require Approval', d.get('thresholds_status') == 'approval_required')

    with urllib.request.urlopen(base + '/api/flood/dashboard') as r:
        d = json.loads(r.read().decode())
        check('Flood Dashboard Status Reported', d.get('status') in ('OPERATIONAL', 'NOT_CONFIGURED'))
        check('No Synthetic Flood Warnings', isinstance(d.get('active_warnings'), int))

    # 2. Risk Calculation Post
    req_data = json.dumps({'hazard': 60.0, 'exposure': 40.0, 'vulnerability': 50.0, 'criticality': 30.0}).encode('utf-8')
    req = urllib.request.Request(base + '/api/risk/calculate', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read().decode())
        # 0.35*60 + 0.25*40 + 0.25*50 + 0.15*30 = 21 + 10 + 12.5 + 4.5 = 48.0
        check('Additive Risk Calculation', abs(d.get('provisional_additive_risk') - 48.0) < 0.01)
        check('Tier Assignment', d.get('priority_tier') == 'Tier 3 Moderate')

    # 2b. Zero exposure check
    req_data = json.dumps({'hazard': 80.0, 'exposure': 0.0, 'vulnerability': 90.0, 'criticality': 70.0}).encode('utf-8')
    req = urllib.request.Request(base + '/api/risk/calculate', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read().decode())
        check('Zero Exposure Geometric Check', d.get('stage17_9_multiplicative_check') == 0.0)

    # 3. IES Calculation Post (Valid)
    req_data = json.dumps({'risk_before': 60.0, 'risk_after': 42.0, 'reference_bounds_match': True}).encode('utf-8')
    req = urllib.request.Request(base + '/api/ies/calculate', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read().decode())
        check('Valid IES Evaluation', d.get('valid') is True)
        check('IES Score Percentage', abs(d.get('ies_percentage') - 30.0) < 0.01)

    # 3b. IES Calculation Post (Invalid Zero Risk Before)
    req_data = json.dumps({'risk_before': 0.0, 'risk_after': 0.0, 'reference_bounds_match': True}).encode('utf-8')
    req = urllib.request.Request(base + '/api/ies/calculate', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read().decode())
        check('Invalid IES Zero Base Rule', d.get('valid') is False and 'Undefined' in d.get('reason', ''))

    # 3c. IES Calculation Post (Invalid Bounds Mismatch)
    req_data = json.dumps({'risk_before': 50.0, 'risk_after': 30.0, 'reference_bounds_match': False}).encode('utf-8')
    req = urllib.request.Request(base + '/api/ies/calculate', data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read().decode())
        check('Invalid IES Bounds Mismatch Rule', d.get('valid') is False and 'differing reference bounds' in d.get('reason', ''))

    # 4. Scenarios
    with urllib.request.urlopen(base + '/api/scenarios') as r:
        d = json.loads(r.read().decode())
        check('Scenario Matrix Count', d.get('count') == 4)
        scenarios = [s['Scenario_ID'] for s in d.get('scenarios', [])]
        check('Baseline Scenario Present', 'SCN-2026-BASE' in scenarios)
        check('Climate Stress Scenario Present', 'SCN-2026-CLIM-STRESS' in scenarios)
        check('Adaptation Investment Present', 'SCN-2026-ADAPT-INVEST' in scenarios)

    # 5. Interventions
    with urllib.request.urlopen(base + '/api/interventions') as r:
        d = json.loads(r.read().decode())
        check('Interventions Count', d.get('count') == 20)
        check('Total Budget NGN', d.get('total_budget_ngn') == 2820000000.0)
        check('Commissioned Works Count', d.get('commissioned_count') == 8)
        check('Completed Works Count', d.get('completed_count') == 6)
        check('Ongoing Works Count', d.get('ongoing_count') == 6)

    # 6. GeoJSON Priority Sites
    with urllib.request.urlopen(base + '/api/geojson/priority_sites') as r:
        d = json.loads(r.read().decode())
        check('GeoJSON Type', d.get('type') == 'FeatureCollection')
        check('GeoJSON Features Present', len(d.get('features', [])) > 0)
        first_feat = d.get('features')[0]
        check('GeoJSON Point Coordinates', len(first_feat['geometry']['coordinates']) == 2)
        check('GeoJSON Point Properties', 'risk' in first_feat['properties'] and 'tier' in first_feat['properties'])

    # 7. Tables & Data Explorer
    with urllib.request.urlopen(base + '/api/tables') as r:
        d = json.loads(r.read().decode())
        check('Authoritative Tables Count', d.get('total_tables') >= 22)
        table_names = [t['table_name'] for t in d.get('tables', [])]
        check('DB01 in Table Explorer', 'DB01_Community_Master' in table_names)
        check('Interventions in Table Explorer', 'Interventions' in table_names)

    # 8. Table detail
    with urllib.request.urlopen(base + '/api/tables/Interventions?limit=5') as r:
        d = json.loads(r.read().decode())
        check('Table Detail Rows', len(d.get('data', [])) == 5)
        check('Table Detail Schema', len(d.get('schema', [])) > 0)

    print('============================================================')
    print(f'  RESULTS: {tests_passed}/{total_tests} API Tests Passed ({tests_passed/total_tests*100:.1f}%)')
    print('============================================================')
    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == '__main__':
    test_api()
