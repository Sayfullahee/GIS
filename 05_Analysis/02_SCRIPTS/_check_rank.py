"""Debug rank uniqueness checks."""
import pandas as pd
from pathlib import Path

BASE = Path("c:/xampp/htdocs/GIS")
OUT  = BASE / "05_Analysis" / "03_OUTPUTS"

for fname, col in [("G37_PriorityAreas.csv","Priority_Rank"),
                   ("G64_EnvironmentalRiskIndex_ERI_v2.csv","ERI_Rank")]:
    p = OUT / fname
    if not p.exists():
        print(f"{fname}: NOT FOUND")
        continue
    df = pd.read_csv(p)
    series = df[col]
    print(f"\n{fname}::{col}")
    print(f"  dtype:          {series.dtype}")
    print(f"  null count:     {series.isna().sum()}")
    print(f"  sample values:  {series.head(5).tolist()}")
    dropped = series.dropna()
    print(f"  after dropna:   {len(dropped)} values, dtype={dropped.dtype}")
    try:
        as_int = dropped.astype(int)
        print(f"  astype(int) OK: is_unique={as_int.is_unique}")
    except Exception as e:
        print(f"  astype(int) FAILED: {e}")
    try:
        print(f"  nunique={dropped.nunique()}, count={dropped.count()}, match={dropped.nunique()==dropped.count()}")
    except Exception as e:
        print(f"  nunique check failed: {e}")
