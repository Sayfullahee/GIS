# Community Profile Template
## N-HYPPADEC Climate–Hydropower–Erosion–Community Resilience DSS

**Profile Version:** v1.0 | **Data Date:** [YYYY] | **Produced:** [YYYY-MM-DD]

---

## SECTION 1 — COMMUNITY IDENTIFICATION

| Field | Value |
|---|---|
| Community ID | [Community_ID] |
| Community Name | [Community] |
| State | [State_Name] |
| LGA | [LGA] |
| Latitude | [Latitude]° N |
| Longitude | [Longitude]° E |
| Survey Date | [Survey_Date] |
| Population (estimated) | [Population] |
| Primary Livelihood | [Livelihood] |
| Water Source | [Water_Source] |
| Electricity Access | [Electricity_Access] |
| HydroBasin (Level 6) | [HYBAS_ID] |
| Nearest River Distance | [IND04_River_Distance_m] m |
| Nearest Hydropower Facility | [Hydro_ID] ([Hydropower_Distance] km) |

---

## SECTION 2 — HAZARD PROFILE

| Indicator | Value | Normalised Score (0–100) |
|---|---|---|
| Flood Frequency (IND01) | [IND01_Flood_Frequency] events/yr | [IND01_Flood_Frequency_Norm] |
| Flood Severity (IND02) | [IND02_Max_Severity] (max) | [IND02_Flood_Severity_Norm] |
| Erosion Severity (IND03) | [IND03_Max_Severity] / 4 | [IND03_Max_Severity_Norm] |
| River Proximity (IND04) | [IND04_River_Distance_m] m | [IND04_River_Proximity_Norm] |
| **Hazard Index (H)** | — | **[H_Score]** |
| H Data Completeness | [H_Data_Completeness] | — |

### Flood History
- Flood Experience Reported: [Flood_Experience]
- High-Confidence Flood Events (G25): [High_Confidence_Events]
- Most Recent Event: [Flood_Last_Event_Date]
- Maximum Recorded Depth: [Max_Depth_m] m
- Maximum Affected Households: [Max_Households_Affected]

### Erosion
- Erosion Present: [Erosion_Presence]
- Active Erosion Sites (within 5 km): [Active_Erosion_Sites_Count]
- Maximum Severity: [Active_Erosion_Max_Severity] / 4
- G27 Hotspot Score: [G27_Hotspot_Score] | Method: [G27_Method]

---

## SECTION 3 — EXPOSURE PROFILE

| Asset Type | In Moderate+ Flood Hazard Zone | Erosion Threat Zone (100m) |
|---|---|---|
| Population | [Pop_in_Moderate_Plus_Hazard] persons | — |
| Buildings | [Buildings_in_Moderate_Plus_Hazard] | [Buildings_Exposed_Count] |
| Roads | [Roads_km_Moderate_Plus_Hazard] km | [Roads_km_Exposed] km |
| Critical Infrastructure | [Critical_Infra_in_Moderate_Plus_Hazard] | [Critical_Infra_Exposed_Count] |
| Critical POI | [POI_Critical_in_Moderate_Plus_Hazard] | — |

| Index | Score (0–100) | Completeness |
|---|---|---|
| Population Exposure (IND05) | [IND05_Pop_Exposure] | — |
| Infrastructure Exposure (IND06) | [IND06_Flood_Infra_Exposure] | — |
| **Exposure Index (E)** | **[E_Score]** | [E_Data_Completeness] |

---

## SECTION 4 — VULNERABILITY PROFILE

| Indicator | Value | Score (0–100) |
|---|---|---|
| Electricity Disruption (IND07) | [Electricity_Access] | [IND07_Electricity_Disruption] |
| Adaptation Coverage (IND09 inverted) | [IND09_Adaptation_Coverage_Raw] | [IND09_Inverted_Norm] |
| HH Flood Loss Rate (DB02 agg.) | [HH_Flood_Loss_Rate] | [HH_Flood_Loss_Rate_Norm] |
| Livelihood Sensitivity | [Livelihood] | [Livelihood_Sensitivity_Norm] |
| **Vulnerability Index (V)** | — | **[V_Score]** |
| V Data Completeness | [V_Data_Completeness] | — |

> *Vulnerability data sourced from community survey (DB01) and aggregated household
> survey (DB02). No household-level data is published in this profile.*

---

## SECTION 5 — CRITICALITY PROFILE

| Indicator | Value | Score (0–100) |
|---|---|---|
| Critical Infrastructure Exposed (IND06c) | [Critical_Infra_Exposed_Count] items | [IND06_Critical_Infra_Exposed_Norm] |
| Electricity Disruption (IND07) | — | [IND07_Electricity_Disruption_Norm] |
| Hydropower Disruption (IND08) | Within 10km: [Hydropower_Within_10km] | [IND08_Hydropower_Disruption_Norm] |
| Critical Services Count | [Critical_Services_Count] | — |
| **Criticality Index (C)** | — | **[C_Score]** |
| C Data Completeness | [C_Data_Completeness] | — |

---

## SECTION 6 — COMPOSITE RISK

```
R = 0.35 × H  +  0.25 × E  +  0.25 × V  +  0.15 × C

R = 0.35 × [H_Score]  +  0.25 × [E_Score]  +  0.25 × [V_Score]  +  0.15 × [C_Score]

R = [R_Score]
```

| Model | R Score | Risk Class |
|---|---|---|
| **Baseline** (0.35/0.25/0.25/0.15) | **[R_Score]** | **[R_Class]** |
| S1 — Equal weights (0.25 each) | [R_Score_S1] | [R_Class_S1] |
| S2 — Hazard dominant (0.45/0.20/0.20/0.15) | [R_Score_S2] | [R_Class_S2] |

**Risk Model Version:** [Risk_Model_Version]  
**Computation Date:** [Computation_Date]

---

## SECTION 7 — ADAPTATION

| Category | Measures in Place |
|---|---|
| Structural | [Structural_Measures_Count] |
| Nature-Based | [Nature_Based_Measures_Count] |
| Preparedness | [Preparedness_Measures_Count] |
| Economic | [Economic_Measures_Count] |
| Institutional | [Institutional_Measures_Count] |
| **Total** | **[Total_Adaptation_Measures]** |

- **IND09 Adaptation Coverage:** [IND09_Adaptation_Coverage] (proportion 0–1)
- **IND10 Adaptation Gap:** [IND10_Adaptation_Gap] / 100

---

## SECTION 8 — PRIORITY CLASSIFICATION

| Field | Value |
|---|---|
| Priority Score | [Priority_Score] |
| **Priority Tier** | **[Priority_Tier]** (1 = Highest) |
| Priority Rank (study area) | [Priority_Rank] of [Total_Communities] |
| Data Confidence | [Data_Confidence] |
| Data Confidence Note | [Data_Confidence_Note] |

> *Priority classification is for decision support. It indicates relative priority
> for investigation and planning — not an automatic intervention mandate.
> Communities with Low data confidence require field verification before action.*

---

## SECTION 9 — DATA CONFIDENCE AND COMPLETENESS

| Component | Completeness | Notes |
|---|---|---|
| Hazard (H) | [H_Data_Completeness] | [H_missing_note] |
| Exposure (E) | [E_Data_Completeness] | [E_missing_note] |
| Vulnerability (V) | [V_Data_Completeness] | [V_missing_note] |
| Criticality (C) | [C_Data_Completeness] | [C_missing_note] |

---

## SECTION 10 — TRACEABILITY

This profile is traceable to its source data through the following chain:

```
PRIORITY TIER [Priority_Tier]
    ↓ Priority_Score = 0.70 × R + 0.30 × IND10
COMPOSITE RISK R = [R_Score]  ([Risk_Model_Version])
    ↓ R = 0.35H + 0.25E + 0.25V + 0.15C
H=[H_Score] | E=[E_Score] | V=[V_Score] | C=[C_Score]
    ↓ Component indices from CLEAN databases
DB01 Community Master | DB02 (agg.) | DB03 Erosion | DB04 Hydro | DB05 Climate | DB06 Infra
    ↓ Field survey + external sources
SOURCE_REGISTER.csv
```

---

*Profile generated by 17_reports.py | [Risk_Model_Version] | Data: [Data_Date]*
*For system documentation see README.md and RISK_MODEL_SPEC.md*
