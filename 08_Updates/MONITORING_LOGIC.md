# Monitoring Logic — Change Detection, Trend, Status and Alert System
## N-HYPPADEC / CHER-CDSS Decision-Support System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Core Monitoring Principle

Every monitored object follows the same longitudinal structure:

```
OBJECT (permanent ID)
    ↓
BASELINE (2026 — first production observation)
    ↓
OBSERVATION 1 (dated record — never overwrites baseline)
    ↓
OBSERVATION 2
    ↓
CHANGE = Observation N − Baseline (or Observation N − Observation N−1)
    ↓
TREND = direction and rate of change across multiple observations
    ↓
STATUS = current condition label (improving / stable / worsening / unknown)
```

**Rule:** A status word (worsening, improving, stable) must only be generated
when the system has a defined rule that supports that interpretation.
Do not infer trend from a single observation pair.
Minimum two comparable observations required before trend language is used.

---

## 2. Monitored Objects and Their Primary Variables

| Object | Permanent ID | Primary Variable | Change Measure |
|---|---|---|---|
| Erosion site | Erosion_ID | Severity_0_4; Width_m; Depth_m | ΔSeverity; ΔWidth; ΔDepth |
| Community | Community_ID | R_Score; H_Score; E_Score; V_Score; C_Score | ΔR; ΔH; ΔE; ΔV; ΔC |
| Hydropower facility | Hydro_ID | Generation_MWh; Disruption_Days; Sedimentation | ΔGeneration; ΔDisruption |
| Climate station | Station_ID | Annual_Rainfall_mm; Temperature_Mean | ΔRainfall; ΔTemp |
| Infrastructure item | Infrastructure_ID | Condition; Damage_Severity; Service_Disruption | ΔCondition; ΔDamage |
| Flood event | Flood_ID | New event recorded | Event count; severity |
| Priority rank | Community_ID | Priority_Rank; Priority_Tier | ΔRank; tier change |

---

## 3. Change Detection Rules

### 3.1 Numeric change

```
Absolute change:   ΔX = X_t2 − X_t1
Percentage change: %ΔX = (X_t2 − X_t1) / X_t1 × 100
```

**Rule:** Percentage change must not be calculated when the baseline (X_t1) is zero.
Use absolute change and flag the case.

### 3.2 Erosion site change thresholds

| Variable | Significant Change Threshold | Label |
|---|---|---|
| Severity_0_4 | ±1 or more | Severity increase / decrease |
| Width_m | +20% or more | Expansion |
| Depth_m | +20% or more | Deepening |
| Activity_Status | Active → Stabilised | Stabilisation |
| Activity_Status | Inactive → Active | Reactivation |

### 3.3 Risk score change thresholds

| Change in R_Score | Label |
|---|---|
| +10 or more | Significant deterioration |
| +5 to +9.9 | Moderate deterioration |
| −5 to +4.9 | Stable |
| −10 to −5.1 | Moderate improvement |
| −10 or more | Significant improvement |
| Risk class change | Tier change (e.g. Moderate → High) |

### 3.4 Trend rules (minimum 3 observations required)

| Pattern | Trend Label |
|---|---|
| Consecutive increases across ≥3 observations | Worsening |
| Consecutive decreases across ≥3 observations | Improving |
| Oscillating without net direction | Variable |
| Net change < threshold over entire period | Stable |
| Fewer than 3 comparable observations | Insufficient data for trend |

---

## 4. Monitoring Schedule

| Object | Monitoring Cycle | Trigger |
|---|---|---|
| Climate observations | Monthly (continuous) | Scheduled |
| Hydropower/water | Monthly (or operational interval) | Scheduled |
| Flood events | Immediately after event | Event-triggered |
| Erosion sites (priority) | 6 months | Scheduled |
| Erosion sites (standard) | 12 months | Scheduled |
| Erosion sites (post-event) | Immediately after major rainfall or earthquake | Event-triggered |
| Infrastructure | 12 months + after significant events | Scheduled + event |
| Community survey | 2–3 years (approved programme cycle) | Programmatic |
| Risk scores | When any upstream input changes | Data-triggered |
| Priority areas | When risk scores recalculated | Data-triggered |
| Land cover | 1–3 years (new authoritative product) | Product release |

---

## 5. Alert and Flag System

The following flags are generated analytically — they are evidence signals,
not automatic intervention decisions.

### 5.1 Flag codes and definitions

| Flag Code | Trigger Condition | Severity | Action Required |
|---|---|---|---|
| `HIGH_HAZARD` | H_Score ≥ 70 | High | Include in next field verification cycle |
| `HIGH_EXPOSURE` | E_Score ≥ 70 | High | Review exposed assets; update G29/G30 |
| `HIGH_VULNERABILITY` | V_Score ≥ 70 | High | Target for adaptation support |
| `HIGH_CRITICALITY` | C_Score ≥ 70 | High | Priority for infrastructure protection |
| `HIGH_RISK` | R_Score ≥ 70 OR R_Class = Very High | Critical | Tier 1 priority; field verification |
| `RAPID_CHANGE` | ΔR_Score ≥ 10 in one update cycle | High | Investigate cause; verify data |
| `NEW_EROSION` | New Erosion_ID added with Severity ≥ 2 | Moderate | Field verification within 3 months |
| `EROSION_WORSENING` | ΔSeverity ≥ 1 at any erosion site | High | Urgent field re-survey |
| `EROSION_CRITICAL` | Severity_0_4 = 4 | Critical | Emergency response assessment |
| `FLOOD_EVENT` | New G25 flood event record added | Situational | Record event; verify field data |
| `HYDRO_DISRUPTION` | Operational_Disruption = Yes at any facility | Moderate | Notify hydropower analyst |
| `HYDRO_SEDIMENTATION` | Sedimentation = High or Critical | High | Flag for engineering assessment |
| `DATA_GAP` | Any required field NULL in CLEAN dataset | Advisory | Assign to next field survey cycle |
| `QC_REQUIRED` | QC_Status = QC_FAILED for any asset | Blocking | Fix before downstream use |
| `LOW_DATA_CONFIDENCE` | Data_Confidence = Low for Tier 1 community | High | Priority field verification |
| `TIER_CHANGE` | Priority_Tier changes between update cycles | Informational | Document cause; notify management |
| `NEW_HIGH_RISK` | Community enters Very High risk class for first time | Critical | Immediate management notification |

### 5.2 Flag generation in the pipeline

Flags are computed in `16_qc.py` and `15_priority.py` and stored in:
- `05_Analysis/03_OUTPUTS/FLAG_Register_[YYYYMMDD].csv`
- Each flag record contains: Flag_Code, Asset_ID, Asset_Type, Trigger_Value,
  Flag_Date, Resolved (Yes/No), Resolution_Notes

### 5.3 Flag resolution

| Rule | Detail |
|---|---|
| Flags are never silently deleted | Resolution must be documented in FLAG_Register |
| A blocking flag (QC_REQUIRED) prevents publication | Must be resolved before any derived product is published |
| A critical flag triggers management notification | CHER-CDSS Coordinator notified within 5 working days |
| Flags persist until resolved | Unresolved flags accumulate in FLAG_Register for audit |

---

## 6. Monitoring Status Labels

Applied to each monitored object's current status field:

| Status | Definition | Minimum Evidence Required |
|---|---|---|
| `STABLE` | No significant change across ≥3 observations | 3+ observations within threshold |
| `IMPROVING` | Consistent decrease in hazard/risk/severity | 3+ consecutive decreasing observations |
| `WORSENING` | Consistent increase in hazard/risk/severity | 3+ consecutive increasing observations |
| `VARIABLE` | Oscillating without clear direction | 3+ observations; no consistent trend |
| `NEW` | First observation; no baseline for comparison | 1 observation only |
| `RECOVERING` | Improving following a documented intervention | Pre/post intervention data + improvement |
| `UNKNOWN` | Insufficient observations or data quality too low | < 2 comparable observations |

**Rule:** `WORSENING` and `IMPROVING` must only be written in reports and dashboards
when the data meets the minimum evidence requirement above.
If only one or two observations exist, use `UNKNOWN` or `NEW`.

---

## 7. Longitudinal Monitoring Example

### Erosion Site NIG-COM-001-ERO-001

```
OBJECT: Erosion site NIG-COM-001-ERO-001
Community: [Community name], Kogi State

Observation Date | Severity | Width_m | Depth_m | Status
2026-10-01       |    3     |  12.0   |   4.0   | NEW (baseline)
2027-04-01       |    3     |  14.0   |   4.5   | STABLE (insufficient obs for trend)
2028-10-01       |    4     |  18.0   |   6.0   | WORSENING (3 obs; ΔSeverity=+1)

Change (2026–2028):
  ΔSeverity:  +1   → Alert: EROSION_WORSENING
  ΔWidth:     +6m  → +50% → Alert: RAPID_CHANGE
  ΔDepth:     +2m  → +50%

Flags generated: EROSION_WORSENING, EROSION_CRITICAL (Severity=4)
Action triggered: Emergency response assessment required
```

### Community Risk Trend

```
OBJECT: Community [X], Risk Score

Period     | H    | E    | V    | C    | R_Score | R_Class
2026 (BL)  | 55.2 | 62.1 | 71.3 | 44.0 |  62.1   | High
2027 upd.  | 58.4 | 63.0 | 74.1 | 45.2 |  64.5   | High
2028 upd.  | 61.0 | 65.2 | 76.0 | 48.1 |  67.0   | High

Trend: R_Score +4.9 over 2 years → VARIABLE (below 5.0 threshold)
       V_Score consistently high — flag HIGH_VULNERABILITY
Next action: Review adaptation measures; check IND09 coverage
```
