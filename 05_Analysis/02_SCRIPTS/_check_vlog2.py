import pandas as pd

vl = pd.read_csv(
    'c:/xampp/htdocs/GIS/00_Project_Control/VERSION_LOG.csv',
    engine='python', on_bad_lines='skip'
)
print('Rows parsed:', len(vl))
print('Columns:', vl.columns.tolist())
versions = sorted(vl['Version'].dropna().unique().tolist())
print('Version values:', versions)
has_v10 = 'v10.0' in versions
has_baseline = 'Baseline_2026' in versions
print('has v10.0:', has_v10)
print('has Baseline_2026:', has_baseline)
if 'Description' in vl.columns:
    all_phases = vl['Description'].str.contains('All 10 phases', na=False).any()
    print('has All 10 phases:', all_phases)
