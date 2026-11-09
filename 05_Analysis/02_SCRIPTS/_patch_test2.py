"""Remove TABLE entries from required_outputs (they're in ANALYSIS_OUTPUTS loop)."""
from pathlib import Path
import re

f = Path(__file__).parent / "run_integration_test.py"
src = f.read_text(encoding="utf-8")

# Remove the TABLE entries from required_outputs dict
lines_to_remove = [
    '        "TABLE_Community_Profiles.csv":     ["Community_ID"],\n',
    '        "TABLE_State_Summaries.csv":        ["State_Code"],\n',
    '        "TABLE_Descriptive_Statistics.csv": ["Variable"],\n',
    '        "TABLE_Risk_Distribution_by_State.csv": ["State_Code"],\n',
]
for line in lines_to_remove:
    if line in src:
        src = src.replace(line, '', 1)
        print(f"Removed: {line.strip()}")
    else:
        print(f"NOT FOUND: {line.strip()}")

# Also fix ERI_Rank if still missing astype(int)
if 'eri["ERI_Rank"].dropna().is_unique' in src:
    src = src.replace(
        'eri["ERI_Rank"].dropna().is_unique',
        'eri["ERI_Rank"].dropna().astype(int).is_unique'
    )
    print("ERI_Rank fix applied")

# Fix Priority_Rank if still missing astype(int)  
old_pr = 'pd.read_csv(ANALYSIS_OUTPUTS / "G37_PriorityAreas.csv")[\n'                     '                  "Priority_Rank"\n'                     '              ].dropna().astype(int).is_unique'
if 'Priority_Rank"\n              ].dropna().is_unique' in src:
    src = src.replace(
        'Priority_Rank"\n              ].dropna().is_unique',
        'Priority_Rank"\n              ].dropna().astype(int).is_unique'
    )
    print("Priority_Rank fix applied")

f.write_text(src, encoding="utf-8")

# Verify
src2 = f.read_text(encoding="utf-8")
# Count how many times TABLE_Community_Profiles appears (should be exactly 1, in report_outputs)
count = src2.count('TABLE_Community_Profiles')
print(f"\nTABLE_Community_Profiles occurrences: {count} (expected: 1)")
print("ERI astype present:", 'ERI_Rank"].dropna().astype(int).is_unique' in src2)

# Show the report_outputs section
idx = src2.find('report_outputs')
if idx >= 0:
    print("\nreport_outputs section:")
    print(src2[idx:idx+400])
