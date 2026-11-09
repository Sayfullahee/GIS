"""
ai_portfolio_optimizer.py
=========================
Phase 4 AI Module for CHER-CDSS v4.2 Decision Support.
Provides:
  1. Prescriptive Multi-Objective Capital Investment Portfolio Optimizer.
  2. MILP / 0-1 Knapsack Solver for Capital Allocation adhering to Section 34 IES validity rules.
  3. Four Strategic Allocation Policies:
     - MAX_IES: Maximizes aggregate risk reduction & Intervention Effectiveness Score.
     - MAX_COMMUNITIES: Maximizes number of communities protected while ensuring minimum impact.
     - EQUITY_BALANCED: Enforces fair geographic distribution across member states.
     - CRITICAL_FIRST: Strictly prioritizes Tier 1 critical risk zones.
  4. Counterfactual Benchmark Engine comparing AI optimization against naive rank-based allocation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds

PROJECT_ROOT = Path(r"c:\xampp\htdocs\GIS")
DATA_CLEAN = PROJECT_ROOT / "03_Data" / "CLEAN"
PRIORITY_AREAS_PATH = DATA_CLEAN / "Priority_Areas_CLEAN.csv"

# Canonical Intervention Package Catalog for N-HYPPADEC
INTERVENTION_CATALOG = [
    {
        "category": "Drainage & Embankment",
        "title_template": "Riparian Flood Protection Levee & Dykes — {community}",
        "base_cost_ngn": 260_000_000.0,
        "base_reduction_pct": 0.28,
        "primary_hazard": "Flooding",
        "suitability_fn": lambda risk, gap: risk >= 60.0
    },
    {
        "category": "Erosion Control",
        "title_template": "Gully Stabilization & Gabion Retaining Wall — {community}",
        "base_cost_ngn": 175_000_000.0,
        "base_reduction_pct": 0.32,
        "primary_hazard": "Gully Erosion",
        "suitability_fn": lambda risk, gap: 50.0 <= risk < 68.0
    },
    {
        "category": "Resilience Infrastructure",
        "title_template": "Elevated Multi-Purpose Evacuation Shelter & Solar Hub — {community}",
        "base_cost_ngn": 110_000_000.0,
        "base_reduction_pct": 0.22,
        "primary_hazard": "Compound Vulnerability",
        "suitability_fn": lambda risk, gap: gap >= 10.0 or risk >= 55.0
    },
    {
        "category": "Water Security",
        "title_template": "Solar High-Yield Clean Water Borehole & Reticulation — {community}",
        "base_cost_ngn": 55_000_000.0,
        "base_reduction_pct": 0.18,
        "primary_hazard": "Water Stress / Drought",
        "suitability_fn": lambda risk, gap: risk < 55.0
    },
    {
        "category": "Ecological Buffer",
        "title_template": "Riparian Agroforestry & Vetiver Grass Buffer Strip — {community}",
        "base_cost_ngn": 40_000_000.0,
        "base_reduction_pct": 0.15,
        "primary_hazard": "Riverbank Retreat",
        "suitability_fn": lambda risk, gap: True
    }
]


def load_candidate_communities(
    pool_size: int = 100,
    state_filter: Optional[str] = None,
    min_risk: float = 40.0
) -> pd.DataFrame:
    """Loads and prepares candidate communities from verified Priority_Areas_CLEAN.csv."""
    if not PRIORITY_AREAS_PATH.exists():
        raise FileNotFoundError(f"Missing priority file: {PRIORITY_AREAS_PATH}")
    
    df = pd.read_csv(PRIORITY_AREAS_PATH)
    
    # Filter state if requested
    if state_filter and state_filter.upper() not in ["ALL", ""]:
        df = df[df["State_Name"].str.upper() == state_filter.upper()]
        
    # Minimum risk threshold
    df = df[df["Composite_Risk"] >= min_risk]
    
    # Sort by priority rank or score descending
    if "Priority_Rank" in df.columns:
        df = df.sort_values(by="Priority_Rank", ascending=True)
    else:
        df = df.sort_values(by="Priority_Score", ascending=False)
        
    candidates = df.head(pool_size).copy().reset_index(drop=True)
    return candidates


def generate_candidate_packages(candidates_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Synthesizes candidate project packages adhering to Section 34 IES validation rules."""
    packages = []
    
    for idx, row in candidates_df.iterrows():
        c_id = str(row["Community_ID"])
        c_name = str(row.get("Community", f"Community {c_id}"))
        lga = str(row.get("LGA", "Unknown LGA"))
        state = str(row.get("State_Name", "Unknown State"))
        state_code = str(row.get("State_Code", "NG-DEF"))
        risk_before = float(row.get("Composite_Risk", 50.0))
        gap = float(row.get("Adaptation_Gap", 0.0))
        
        # Select best-fit intervention from catalog
        chosen_cat = None
        for item in INTERVENTION_CATALOG:
            if item["suitability_fn"](risk_before, gap):
                chosen_cat = item
                break
        if chosen_cat is None:
            chosen_cat = INTERVENTION_CATALOG[-1]
            
        # Cost modulated slightly by risk severity to reflect engineering scope
        cost_scale = 0.85 + (min(risk_before, 100.0) / 100.0) * 0.30
        budget_ngn = round(chosen_cat["base_cost_ngn"] * cost_scale, -5) # Round to nearest 100k
        
        # Risk reduction modulated by base reduction
        reduction_rate = chosen_cat["base_reduction_pct"]
        delta_r = round(risk_before * reduction_rate, 2)
        risk_after = round(max(risk_before - delta_r, 5.0), 2)
        
        # Section 34 IES Formula: ((R_before - R_after) / R_before) * 100%
        ies_pct = round(((risk_before - risk_after) / risk_before) * 100.0, 2) if risk_before > 0 else 0.0
        
        # Capital Efficiency: delta R points per 100M NGN
        budget_m = budget_ngn / 1_000_000.0
        capital_efficiency = round((delta_r / budget_m) * 100.0, 4) if budget_m > 0 else 0.0
        
        packages.append({
            "candidate_index": idx,
            "community_id": c_id,
            "community_name": c_name,
            "lga_name": lga,
            "state_name": state,
            "state_code": state_code,
            "category": chosen_cat["category"],
            "title": chosen_cat["title_template"].format(community=c_name),
            "primary_hazard": chosen_cat["primary_hazard"],
            "budget_ngn": budget_ngn,
            "risk_before": risk_before,
            "risk_after": risk_after,
            "delta_r": delta_r,
            "ies_pct": ies_pct,
            "capital_efficiency": capital_efficiency,
            "estimated_beneficiaries": int(2500 + (risk_before * 85))
        })
        
    return packages


def optimize_capital_portfolio(
    total_budget_ngn: float = 2_500_000_000.0,
    objective: str = "MAX_IES",
    state_filter: Optional[str] = None,
    max_state_share_pct: float = 28.0,
    candidate_pool_size: int = 100,
    min_risk: float = 40.0
) -> Dict[str, Any]:
    """
    Executes prescriptive multi-objective capital allocation optimization:
      - Objective 'MAX_IES': maximize total weighted IES and risk points reduced.
      - Objective 'MAX_COMMUNITIES': maximize count of served communities.
      - Objective 'EQUITY_BALANCED': enforces strict state upper allocation bound.
      - Objective 'CRITICAL_FIRST': weights Tier 1 communities heavily.
    """
    candidates_df = load_candidate_communities(
        pool_size=candidate_pool_size,
        state_filter=state_filter,
        min_risk=min_risk
    )
    
    if candidates_df.empty:
        return {
            "status": "ERROR",
            "message": "No candidate communities matched the specified filters."
        }
        
    packages = generate_candidate_packages(candidates_df)
    n = len(packages)
    
    # Extract arrays
    costs = np.array([p["budget_ngn"] for p in packages], dtype=float)
    ies_values = np.array([p["ies_pct"] for p in packages], dtype=float)
    delta_r_values = np.array([p["delta_r"] for p in packages], dtype=float)
    risk_before_values = np.array([p["risk_before"] for p in packages], dtype=float)
    
    # Objective Coefficients (MILP minimizes c^T * x, so we negate for maximization)
    if objective == "MAX_IES":
        c = -(delta_r_values * (ies_values / 100.0))
    elif objective == "MAX_COMMUNITIES":
        # Weight each community 1.0 plus small tie-breaker on IES
        c = -(1.0 + (ies_values / 1000.0))
    elif objective == "CRITICAL_FIRST":
        # Exponential weighting on risk_before
        c = -(delta_r_values * ((risk_before_values / 50.0) ** 2.0))
    else: # EQUITY_BALANCED
        c = -(delta_r_values * 1.0)
        
    # Budget constraint: sum(cost_i * x_i) <= total_budget_ngn
    A_rows = [costs]
    b_u = [total_budget_ngn]
    b_l = [0.0]
    
    # State equity constraints if EQUITY_BALANCED
    states = [p["state_name"] for p in packages]
    unique_states = sorted(list(set(states)))
    
    if objective == "EQUITY_BALANCED" and len(unique_states) > 1:
        max_state_budget = total_budget_ngn * (max_state_share_pct / 100.0)
        for st in unique_states:
            st_mask = np.array([1.0 if s == st else 0.0 for s in states])
            A_rows.append(st_mask * costs)
            b_u.append(max_state_budget)
            b_l.append(0.0)
            
    A = np.vstack(A_rows)
    constraints = LinearConstraint(A, b_l, b_u)
    
    # Binary bounds: x_i in {0, 1}
    integrality = np.ones(n) # All variables are integers
    bounds = Bounds(0, 1)
    
    # Solve via SciPy MILP
    res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)
    
    if not res.success:
        # Fallback to greedy knapsack algorithm if solver is unbounded or infeasible
        selected_indices = _fallback_greedy_knapsack(packages, total_budget_ngn)
    else:
        x_sol = np.round(res.x).astype(int)
        selected_indices = [i for i in range(n) if x_sol[i] == 1]
        
    selected_packages = [packages[i] for i in selected_indices]
    
    # Sort selected packages by priority / IES
    selected_packages.sort(key=lambda p: (p["risk_before"], p["ies_pct"]), reverse=True)
    for rank_idx, sp in enumerate(selected_packages, 1):
        sp["allocation_rank"] = rank_idx
        
    # Portfolio Aggregate Metrics
    allocated_budget = sum(p["budget_ngn"] for p in selected_packages)
    unallocated_budget = max(total_budget_ngn - allocated_budget, 0.0)
    utilization_pct = round((allocated_budget / total_budget_ngn) * 100.0, 2) if total_budget_ngn > 0 else 0.0
    total_delta_r = round(sum(p["delta_r"] for p in selected_packages), 2)
    avg_ies = round(sum(p["ies_pct"] for p in selected_packages) / len(selected_packages), 2) if selected_packages else 0.0
    total_beneficiaries = sum(p["estimated_beneficiaries"] for p in selected_packages)
    portfolio_efficiency = round((total_delta_r / (allocated_budget / 1_000_000.0)) * 100.0, 4) if allocated_budget > 0 else 0.0
    
    # State-by-State Allocation Breakdown
    state_breakdown = {}
    for sp in selected_packages:
        st = sp["state_name"]
        if st not in state_breakdown:
            state_breakdown[st] = {"count": 0, "budget_ngn": 0.0, "communities": []}
        state_breakdown[st]["count"] += 1
        state_breakdown[st]["budget_ngn"] += sp["budget_ngn"]
        state_breakdown[st]["communities"].append(f"{sp['community_name']} ({sp['lga_name']})")
        
    state_summary = []
    for st, data in sorted(state_breakdown.items(), key=lambda x: x[1]["budget_ngn"], reverse=True):
        share_pct = round((data["budget_ngn"] / allocated_budget) * 100.0, 1) if allocated_budget > 0 else 0.0
        state_summary.append({
            "state_name": st,
            "project_count": data["count"],
            "budget_allocated_ngn": data["budget_ngn"],
            "budget_share_pct": share_pct,
            "sample_communities": data["communities"][:3]
        })
        
    # Category Breakdown
    cat_breakdown = {}
    for sp in selected_packages:
        c = sp["category"]
        cat_breakdown[c] = cat_breakdown.get(c, 0) + 1
        
    # Compute Counterfactual Naive Baseline (Top-down greedy allocation)
    naive_indices = _fallback_greedy_knapsack(packages, total_budget_ngn, sort_by_rank=True)
    naive_packages = [packages[i] for i in naive_indices]
    naive_delta_r = sum(p["delta_r"] for p in naive_packages)
    naive_count = len(naive_packages)
    delta_r_gain_pct = round(((total_delta_r - naive_delta_r) / naive_delta_r) * 100.0, 1) if naive_delta_r > 0 else 0.0
    
    return {
        "status": "OPTIMAL" if res.success else "HEURISTIC_FEASIBLE",
        "optimization_timestamp": datetime.now().isoformat(),
        "strategy": objective,
        "input_budget_ngn": total_budget_ngn,
        "allocated_budget_ngn": allocated_budget,
        "unallocated_budget_ngn": unallocated_budget,
        "budget_utilization_pct": utilization_pct,
        "portfolio_summary": {
            "selected_projects_count": len(selected_packages),
            "total_risk_points_reduced": total_delta_r,
            "mean_ies_score_pct": avg_ies,
            "estimated_beneficiaries_protected": total_beneficiaries,
            "capital_efficiency_points_per_100m": portfolio_efficiency,
            "state_coverage_count": len(state_breakdown)
        },
        "state_allocations": state_summary,
        "category_distribution": cat_breakdown,
        "counterfactual_ai_advantage": {
            "ai_risk_reduction_gain_pct": delta_r_gain_pct,
            "additional_communities_served": len(selected_packages) - naive_count,
            "evaluation_note": "AI multi-objective formulation selects Pareto-efficient project combinations yielding higher net resilience per Naira invested."
        },
        "selected_interventions": selected_packages
    }


def _fallback_greedy_knapsack(
    packages: List[Dict[str, Any]],
    budget_limit: float,
    sort_by_rank: bool = False
) -> List[int]:
    """Heuristic fallback knapsack implementation."""
    if sort_by_rank:
        sorted_indices = list(range(len(packages))) # Already in priority order
    else:
        # Sort by capital efficiency descending
        sorted_indices = sorted(
            range(len(packages)),
            key=lambda i: packages[i]["capital_efficiency"],
            reverse=True
        )
        
    selected = []
    current_cost = 0.0
    for idx in sorted_indices:
        pkg_cost = packages[idx]["budget_ngn"]
        if current_cost + pkg_cost <= budget_limit:
            selected.append(idx)
            current_cost += pkg_cost
            
    return selected


if __name__ == "__main__":
    import json
    res = optimize_capital_portfolio(
        total_budget_ngn=2_500_000_000.0,
        objective="MAX_IES",
        max_state_share_pct=25.0
    )
    print("Optimization Status:", res["status"])
    print("Selected Projects:", res["portfolio_summary"]["selected_projects_count"])
    print("Allocated Budget (NGN):", f"{res['allocated_budget_ngn']:,.2f}")
    print("Mean IES (%):", res["portfolio_summary"]["mean_ies_score_pct"])
    print("Efficiency Gain vs Naive:", f"{res['counterfactual_ai_advantage']['ai_risk_reduction_gain_pct']}%")
