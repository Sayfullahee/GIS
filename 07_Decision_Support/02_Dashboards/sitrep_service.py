"""
sitrep_service.py
=================
Executive Policy Brief & Situation Report (SitRep) Generator for CHER-CDSS v4.2.
Produces institutional, high-resolution, print-ready advisories and data dossiers
for the N-HYPPADEC Managing Director, Governing Board, and National Emergency Council.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import pandas as pd
import json
import logo_asset

PROJECT_ROOT = Path(r"c:\xampp\htdocs\GIS")
DATA_LOOKUPS = PROJECT_ROOT / "03_Data" / "LOOKUPS"
DATA_CLEAN = PROJECT_ROOT / "03_Data" / "CLEAN"

def generate_sitrep_data(state_code: Optional[str] = None) -> Dict[str, Any]:
    """Generates structured SitRep metrics for a specific state or national overview."""
    df_states = pd.read_csv(DATA_LOOKUPS / "LKP_States.csv")
    df_lgas = pd.read_csv(DATA_LOOKUPS / "LKP_LGAs.csv")
    df_sep = pd.read_csv(DATA_LOOKUPS / "LKP_State_EnvironmentalProblems.csv")
    df_comm = pd.read_csv(DATA_CLEAN / "DB01_Community_Master_CLEAN.csv") if (DATA_CLEAN / "DB01_Community_Master_CLEAN.csv").exists() else None

    # Filter by state if provided
    s_filter = state_code.upper() if state_code and state_code.upper() != "ALL" else None
    
    if s_filter:
        state_row = df_states[df_states["State_Code"] == s_filter]
        state_name = state_row.iloc[0]["State_Name"] if len(state_row) > 0 else s_filter
        scope_title = f"{state_name} State Focus"
        sep_subset = df_sep[df_sep["State_Code"] == s_filter]
        lgas_count = len(df_lgas[df_lgas["State_Code"] == s_filter])
    else:
        scope_title = "N-HYPPADEC Ten Member States Master Corridor"
        state_name = "All 10 Member States"
        sep_subset = df_sep
        lgas_count = len(df_lgas)

    # Calculate metrics
    sev_col = "Severity_Level" if "Severity_Level" in sep_subset.columns else ("Severity" if "Severity" in sep_subset.columns else None)
    total_incidents = len(sep_subset)
    critical_incidents = len(sep_subset[sep_subset[sev_col] == "Critical"]) if sev_col else 0
    high_incidents = len(sep_subset[sep_subset[sev_col] == "High"]) if sev_col else 0
    
    # Top Hazards
    hazard_counts = sep_subset["Problem_Name"].value_counts().to_dict()
    top_hazards = [{"hazard": k, "count": v} for k, v in list(hazard_counts.items())[:5]]
    
    # Budget Estimates (Rule-based: Critical = NGN 85M, High = NGN 40M per hotspot)
    est_budget_ngn = (critical_incidents * 85_000_000) + (high_incidents * 40_000_000)
    est_affected_pop = (critical_incidents * 45_000) + (high_incidents * 18_000)

    # Detailed Incident List
    incidents_list = []
    for _, r in sep_subset.iterrows():
        incidents_list.append({
            "record_id": r.get("Record_ID", "SEP-UNK"),
            "state_name": r.get("State_Name", "N/A"),
            "hazard_name": r.get("Problem_Name", "N/A"),
            "severity": r.get("Severity_Level", r.get("Severity", "Moderate")),
            "category": r.get("Category", "Environmental"),
            "notes": r.get("Notes", r.get("Field_Observation_Notes", "Standard field record")),
            "source": r.get("Observed_Source", r.get("Validation_Source", "N-HYPPADEC GIS"))
        })

    report_ref = f"NHYP/CHER-CDSS/SITREP/{date.today().strftime('%Y-%m')}/{s_filter.replace('NG-', '') if s_filter else 'NAT-01'}"

    return {
        "status": "SUCCESS",
        "report_ref": report_ref,
        "date_issued": datetime.now().strftime("%d %B %Y, %H:%M WAT"),
        "scope": scope_title,
        "state_name": state_name,
        "state_code": s_filter or "NATIONAL",
        "total_lgas_monitored": lgas_count,
        "total_incidents_recorded": total_incidents,
        "critical_incidents": critical_incidents,
        "high_incidents": high_incidents,
        "estimated_affected_population": est_affected_pop,
        "recommended_emergency_allocation_ngn": est_budget_ngn,
        "top_hazards": top_hazards,
        "incidents": incidents_list
    }

def generate_sitrep_html(state_code: Optional[str] = None) -> str:
    """Renders a print-ready, high-resolution official SitRep document."""
    data = generate_sitrep_data(state_code)
    
    hazards_rows = ""
    for h in data["top_hazards"]:
        hazards_rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E2E8F0; font-weight: 600;">{h['hazard']}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E2E8F0; text-align: center;">{h['count']} Verified Hotspots</td>
        </tr>
        """

    incidents_rows = ""
    for inc in data["incidents"][:12]:
        badge_color = "#DC2626" if inc["severity"] == "Critical" else ("#D97706" if inc["severity"] == "High" else "#2563EB")
        incidents_rows += f"""
        <tr>
            <td style="padding: 6px 10px; border-bottom: 1px solid #E2E8F0; font-family: monospace; font-size: 11px;">{inc['record_id']}</td>
            <td style="padding: 6px 10px; border-bottom: 1px solid #E2E8F0;">{inc['state_name']}</td>
            <td style="padding: 6px 10px; border-bottom: 1px solid #E2E8F0; font-weight: 600;">{inc['hazard_name']}</td>
            <td style="padding: 6px 10px; border-bottom: 1px solid #E2E8F0;"><span style="background:{badge_color}; color:#FFF; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">{inc['severity']}</span></td>
            <td style="padding: 6px 10px; border-bottom: 1px solid #E2E8F0; font-size: 11px; color: #475569;">{inc['notes']}</td>
        </tr>
        """

    logo_data_uri = logo_asset.get_logo_data_uri()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SITREP - {data['report_ref']}</title>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            color: #0F172A;
            background: #FFF;
            margin: 0;
            padding: 24px;
            font-size: 13px;
            line-height: 1.45;
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 3px double #0F172A;
            padding-bottom: 14px;
            margin-bottom: 20px;
        }}
        .crest-title {{
            text-align: center;
            flex: 1;
        }}
        .crest-title h2 {{ margin: 0; font-size: 16px; letter-spacing: 0.05em; color: #064E3B; font-weight: 800; }}
        .crest-title h3 {{ margin: 3px 0; font-size: 14px; color: #0F172A; }}
        .crest-title p {{ margin: 0; font-size: 11px; color: #64748B; }}
        .doc-badge {{
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            padding: 8px 12px;
            border-radius: 6px;
            text-align: right;
            font-size: 11px;
        }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 16px 0;
        }}
        .kpi-box {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #0284C7;
            padding: 10px 12px;
            border-radius: 4px;
        }}
        .kpi-box.red {{ border-left-color: #DC2626; }}
        .kpi-box.amber {{ border-left-color: #D97706; }}
        .kpi-box.green {{ border-left-color: #059669; }}
        .kpi-lbl {{ font-size: 10px; text-transform: uppercase; color: #64748B; font-weight: 600; letter-spacing: 0.04em; }}
        .kpi-val {{ font-size: 18px; font-weight: 800; color: #0F172A; margin: 4px 0 2px 0; }}
        .kpi-sub {{ font-size: 10px; color: #64748B; }}
        .section-title {{
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #1E293B;
            border-bottom: 1.5px solid #CBD5E1;
            padding-bottom: 4px;
            margin: 20px 0 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 16px;
        }}
        th {{
            background: #F1F5F9;
            color: #334155;
            text-align: left;
            padding: 8px 10px;
            border-bottom: 2px solid #CBD5E1;
            font-weight: 600;
        }}
        .sign-off {{
            display: flex;
            justify-content: space-between;
            margin-top: 36px;
            padding-top: 16px;
            border-top: 1px solid #E2E8F0;
        }}
        .sig-block {{
            width: 45%;
        }}
        .sig-line {{
            margin-top: 32px;
            border-top: 1px solid #0F172A;
            padding-top: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #0284C7;
            color: #FFF;
            padding: 10px 18px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>

    <div class="header">
        <img src="{logo_data_uri}" style="width: 72px; height: 72px; object-fit: contain; border-radius: 50%; margin-right: 14px; background: #FFF; padding: 2px; border: 2px solid #065F46; box-shadow: 0 2px 6px rgba(0,0,0,0.15);" alt="N-HYPPADEC Official Seal">
        <div class="crest-title">
            <h2>NATIONAL HYDROELECTRIC POWER PRODUCING AREAS DEVELOPMENT COMMISSION</h2>
            <h3>CENTRE FOR HYDROPOWER, EROSION & RESILIENCE (CHER-CDSS)</h3>
            <p>INSTITUTIONAL MULTI-HAZARD SITUATION REPORT & DECISION ADVISORY</p>
        </div>
        <div class="doc-badge">
            <strong>REF:</strong> {data['report_ref']}<br>
            <strong>DATE:</strong> {data['date_issued']}<br>
            <strong>SECURITY:</strong> RESTRICTED (OFFICIAL USE)
        </div>
    </div>

    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; padding: 12px 14px; border-radius: 4px; margin-bottom: 16px;">
        <strong style="color: #1E40AF; font-size: 13px;">EXECUTIVE SUMMARY — {data['scope']}</strong>
        <p style="margin: 4px 0 0 0; color: #1E293B; font-size: 12px;">
            This briefing document synthesizes active spatial intelligence across the 14 statutory environmental and security hazard domains for <strong>{data['state_name']}</strong>. 
            Ground observations confirm <strong>{data['critical_incidents']} Tier-1 Critical Hotspots</strong> requiring prioritized engineering stabilization, emergency relief pre-positioning, and flood barrier defense deployments under the N-HYPPADEC 2026 Resilience Mandate.
        </p>
    </div>

    <div class="kpi-row">
        <div class="kpi-box red">
            <div class="kpi-lbl">Critical Emergency Sites</div>
            <div class="kpi-val">{data['critical_incidents']}</div>
            <div class="kpi-sub">Tier 1 Severe Threat Level</div>
        </div>
        <div class="kpi-box amber">
            <div class="kpi-lbl">Total Verified Hotspots</div>
            <div class="kpi-val">{data['total_incidents_recorded']}</div>
            <div class="kpi-sub">G65 Multi-Hazard Layer</div>
        </div>
        <div class="kpi-box green">
            <div class="kpi-lbl">Estimated Population at Risk</div>
            <div class="kpi-val">{data['estimated_affected_population']:,}</div>
            <div class="kpi-sub">Riverine & Agro-pastoral</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-lbl">Recommended Allocation</div>
            <div class="kpi-val">₦{data['recommended_emergency_allocation_ngn'] / 1e6:,.1f}M</div>
            <div class="kpi-sub">Targeted Defense Interventions</div>
        </div>
    </div>

    <div class="section-title">1. Primary Hazard Drivers & Risk Distribution</div>
    <table>
        <thead>
            <tr>
                <th>Hazard Threat Domain</th>
                <th style="text-align: center;">Verified Footprint Count</th>
            </tr>
        </thead>
        <tbody>
            {hazards_rows}
        </tbody>
    </table>

    <div class="section-title">2. Ground-Truthed Field Incidents & Threat Locations</div>
    <table>
        <thead>
            <tr>
                <th>Incident ID</th>
                <th>State</th>
                <th>Hazard Domain</th>
                <th>Severity</th>
                <th>Field Intelligence & Notes</th>
            </tr>
        </thead>
        <tbody>
            {incidents_rows}
        </tbody>
    </table>

    <div class="section-title">3. Institutional Action Protocols & Recommended Directives</div>
    <ol style="padding-left: 20px; font-size: 12px; line-height: 1.6; margin-top: 6px;">
        <li><strong>River Basin Defenses:</strong> Immediate deployment of riprap revetments and dyke reinforcements across downstream floodplains (Shiroro, Kainji, Jebba, Dadin Kowa corridors).</li>
        <li><strong>Banditry Farm Denial Buffer:</strong> Coordinate joint security patrols with state commands to protect farmers during planting and harvesting in vulnerable riverine LGAs.</li>
        <li><strong>FEW-CAM Early Warning Activation:</strong> Escalate community warning sirens and SMS broadcast alerts to Level 2 (Warning) in active confluence zones.</li>
    </ol>

    <div class="sign-off">
        <div class="sig-block">
            <div style="font-size: 11px; color: #64748B;">Prepared by:</div>
            <div class="sig-line">Director of Community Resilience & GIS Operations<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">CHER-CDSS Platform Technical Secretariat</span></div>
        </div>
        <div class="sig-block">
            <div style="font-size: 11px; color: #64748B;">Approved for Transmittal:</div>
            <div class="sig-line">Managing Director / Chief Executive Officer<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">National Hydroelectric Power Producing Areas Development Commission</span></div>
        </div>
    </div>
</body>
</html>
    """
    return html
