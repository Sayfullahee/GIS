"""
run_dashboard.py
================
Convenience launcher for the CHER-CDSS Web GIS & REST API Server.
Usage:
    python run_dashboard.py
Access:
    Web Dashboard: http://localhost:8000/
    Interactive API Docs: http://localhost:8000/docs
"""

import sys
from pathlib import Path
import uvicorn

DASHBOARD_DIR = Path(__file__).parent / "07_Decision_Support" / "02_Dashboards"
sys.path.insert(0, str(DASHBOARD_DIR))

if __name__ == "__main__":
    print("==================================================================")
    print("  CHER-CDSS DECISION-SUPPORT PLATFORM (v4.1)")
    print("  Serving on: http://localhost:8000")
    print("  API Docs:   http://localhost:8000/docs")
    print("==================================================================")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, app_dir=str(DASHBOARD_DIR), reload=True)
