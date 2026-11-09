# RESEARCH DESIGN: MASTER INDICATOR DICTIONARY
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System (CHER-CDSS)
### N-HYPPADEC / Ten Member States of Nigeria
**Document ID:** `RD-IND-2026-v4.1` | **Stage:** 2.3 | **Status:** Approved Baseline  
**Governing Specification:** CHER-CDSS Master Implementation Scaffold v4.1 (October 2026)

---

## 1. Indicator Governance Principles

In compliance with Stage 2.3 and Section 34 of the Scaffold v4.1:
1. **Mathematical Directionality:**
   - **Positive ($+$):** Higher raw value indicates higher hazard, higher exposure, higher vulnerability, or higher overall risk.
   - **Inverse ($-$, Adaptive Capacity):** Higher raw value indicates stronger resilience, better infrastructure, or higher adaptive capacity (inverted during normalization: $100 - x_{\text{norm}}$).
2. **Fixed Reference Bounds:** All indicators normalize against locked 2026 baseline bounds ($\min_{\text{ref}}, \max_{\text{ref}}$) recorded in `00_Project_Control/REFERENCE_BOUNDS_REGISTER.csv`.
3. **No Silent Zeroes:** Missing values are never silently converted to zero. Explicit imputation or missingness flags are applied.
4. **Spatial Aggregation:** Bottom-up aggregation follows the hierarchy: $\text{Household / Site} \longrightarrow \text{Community} \longrightarrow \text{Ward} \longrightarrow \text{LGA} \longrightarrow \text{State}$.

---

## 2. Core Indicator Dictionary (IND01 to IND10)

### IND01: Flood Frequency
- **Full Title:** Annual Flood Event Recurrence Rate
- **Pillar:** Hazard ($H$) | Layer: G24 / G25 / DB01
- **Numerator:** Total verified flood events recorded over the monitoring period ($N_{\text{events}}$)
- **Denominator:** Number of monitored years ($T_{\text{years}}$)
- **Unit:** Events per year (float)
- **Mathematical Direction:** Positive ($+$)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 5.0$ events/year
- **Data Source:** `G25_ObservedFloods_CLEAN.csv` + `DB01_Community_Master_CLEAN.csv` (Flood_Frequency)
- **Frequency:** Annual / Post-wet-season
- **Spatial Resolution:** Community (`Community_ID`)
- **Missing Data Rule:** If unmonitored for $<1$ year, inherit LGA modal frequency and assign Low Data Confidence.
- **Interpretation:** Reflects chronic hydrodynamic exposure; values $> 2.0$ denote chronic flood corridors.

---

### IND02: Flood Severity
- **Full Title:** Compound Flood Impact Severity Score
- **Pillar:** Hazard ($H$) | Layer: G24 / G25 / DB01
- **Formula:** Weighted composite of maximum water depth, event duration, and reported infrastructure disruption:
  $$\text{IND02}_{\text{raw}} = 0.35 \times \text{Depth (m)} + 0.35 \times \min(14, \text{Duration (days)}) / 2.8 + 0.30 \times \text{Damage Scale (1-5)}$$
- **Unit:** Severity index points (0.0 to 10.0 scale)
- **Mathematical Direction:** Positive ($+$)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 10.0$
- **Data Source:** `DB01_Community_Master_CLEAN.csv` (Flood_Severity_Avg)
- **Frequency:** Seasonal (post-event)
- **Spatial Resolution:** Community (`Community_ID`)
- **Missing Data Rule:** Default to 0.0 only if community confirmed flood-free by local focal person.
- **Interpretation:** Captures the destructive physical energy of floodwaters beyond simple inundation.

---

### IND03: Erosion Severity
- **Full Title:** Monitored Gully & Riverbank Erosion Severity
- **Pillar:** Hazard ($H$) | Layer: G26 / G27 / DB03
- **Numerator:** Sum of field severity ratings ($S_i \in [1, 4]$) of active erosion sites within community boundary
- **Denominator:** Maximum theoretical severity for monitored sites
- **Formula:** $\text{IND03}_{\text{raw}} = \max(S_i) \times 2.5$ (or weighted site score)
- **Unit:** Severity scale (0.0 to 10.0)
- **Mathematical Direction:** Positive ($+$)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 10.0$
- **Data Source:** `DB03_Erosion_Sites_CLEAN.csv` (Severity field, 1=Minor, 2=Moderate, 3=Severe, 4=Catastrophic)
- **Frequency:** Quarterly
- **Spatial Resolution:** Community / Site (`Erosion_ID`)
- **Missing Data Rule:** Where no erosion survey exists, assign 0.0 with Data Confidence = "Unknown".
- **Interpretation:** Reflects geomorphic land degradation and impending structural undermining.

---

### IND04: River Proximity
- **Full Title:** Proximity to Mainstream Rivers & Major Drainage Channels
- **Pillar:** Hazard ($H$) | Layer: G05 / G03
- **Definition:** Euclidean distance from community centroid to nearest HydroRIVERS stream line.
- **Formula:** Inverted proximity score within the critical 500m buffer (BUF001):
  $$\text{IND04}_{\text{raw}} = \max\left(0, 100 \times \frac{500 - \min(500, \text{Distance (m)})}{500}\right)$$
- **Unit:** Score (0 to 100) or Distance in meters
- **Mathematical Direction:** Positive ($+$) (Closer to river = higher raw score)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 5000.0$ meters (distance) or $[0, 100]$ (score)
- **Data Source:** `G05_River_and_Drainage_Network` spatial join with `G03_Communities`
- **Frequency:** Static baseline (updated upon drainage channel construction)
- **Spatial Resolution:** Community centroid
- **Missing Data Rule:** Impute from GIS nearest neighbor vector query.
- **Interpretation:** Communities $< 200\text{m}$ from major channels face primary wave, scouring, and flood surge impacts.

---

### IND05: Population Exposure
- **Full Title:** Total Population Residing in Flood & Erosion Hazard Zones
- **Pillar:** Exposure ($E$) | Layer: G29 / G03 / DB01
- **Numerator:** Estimated community population residing within modelled Moderate, High, or Very High hazard zones
- **Denominator:** Total community population
- **Unit:** Percentage ($0$ to $100\%$) or Absolute Headcount
- **Mathematical Direction:** Positive ($+$)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 5000.0$ (headcount) or $100.0\%$
- **Data Source:** `DB01_Community_Master_CLEAN.csv` (Population) intersecting `G24_Flood_Hazard`
- **Frequency:** Annual
- **Spatial Resolution:** Community (`Community_ID`)
- **Missing Data Rule:** Apply 2006 Census projection adjusted by regional growth rate ($2.8\%/\text{year}$).
- **Interpretation:** Establishes the human scale of potential disaster casualties and relief requirements.

---

### IND06: Infrastructure Exposure
- **Full Title:** Critical Facilities & Public Assets in Hazard Corridors
- **Pillar:** Exposure ($E$) / Criticality ($C$) | Layer: G19 / G29 / DB06
- **Formula:** Count of critical facilities located within hazard buffers weighted by facility criticality weight (EMD02: Water=1.0, Health=1.5, Transport=1.2, School=0.8)
- **Unit:** Weighted facility count (float)
- **Mathematical Direction:** Positive ($+$)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 10.0$
- **Data Source:** `DB06_Infrastructure_CLEAN.csv` + `G19_FieldInfrastructure`
- **Frequency:** Semi-annual
- **Spatial Resolution:** Community / Facility
- **Missing Data Rule:** Retain 0 only if satellite verification confirms absence of built structures.
- **Interpretation:** Quantifies the structural vulnerability of basic service delivery systems.

---

### IND07: Electricity Disruption
- **Full Title:** Annual Grid Electricity Outage & Disruption Index
- **Pillar:** Vulnerability ($V$) / Criticality ($C$) | Layer: DB01 / DB04 / G28
- **Numerator:** Total days per year without functional electricity supply in riparian settlements
- **Denominator:** 365 days
- **Unit:** Percentage ($0$ to $100\%$) or Days/Year
- **Mathematical Direction:** Positive ($+$) (More outage = higher vulnerability)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 365.0$ days
- **Data Source:** `DB01_Community_Master_CLEAN.csv` (`Electricity_Access` inverted) & `DB04_Hydropower_Water`
- **Frequency:** Annual
- **Spatial Resolution:** Community
- **Missing Data Rule:** Assume $90\%$ outage for non-electrified rural riverine settlements.
- **Interpretation:** Measures local energy poverty paradox within the national hydropower producing corridor.

---

### IND08: Hydropower Disruption
- **Full Title:** Direct Dam Pulse / Operational Disruption Factor
- **Pillar:** Criticality ($C$) | Layer: DB04 / G28
- **Definition:** Compound score of downstream economic losses, unannounced turbine discharge events, and reservoir draw-down effects.
- **Unit:** Disruption Score (0.0 to 100.0)
- **Mathematical Direction:** Positive ($+$)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 100.0$
- **Special Rule:** Strictly set to `NULL` (or N/A) for communities situated outside the 10km Hydropower Buffer (BUF004). Never assign 0.0 where unapplicable.
- **Data Source:** `DB04_Hydropower_Water_CLEAN.csv`
- **Frequency:** Monthly
- **Spatial Resolution:** 10km Hydropower Zone
- **Interpretation:** Reflects specific externalities generated by large hydroelectric dams on contiguous riparian hosts.

---

### IND09: Adaptation Coverage
- **Full Title:** Community Disaster Adaptation & Protection Coverage
- **Pillar:** Vulnerability ($V$) / Adaptation ($G36$) | Layer: DB01 / DB06 / G36
- **Definition:** Proportion of required adaptation mechanisms actively installed and operational (flood dykes, check dams, drainage channels, solar boreholes, early warning radio).
- **Unit:** Proportion ($0.0$ to $1.0$) or Percentage ($0$ to $100\%$)
- **Mathematical Direction:** Inverse ($-$) in Vulnerability ($V_{\text{score}} = 100 \times (1 - \text{IND09})$); Positive in Adaptation ($G36$).
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 1.0$ (or $100.0\%$)
- **Data Source:** `DB01_Community_Master_CLEAN.csv` (`Adaptation_Measures`) & `G36_Adaptation`
- **Frequency:** Semi-annual
- **Spatial Resolution:** Community
- **Missing Data Rule:** Treat as 0.0 (no adaptation measures) only after field confirmation.
- **Interpretation:** Indicates protective capacity; communities near 0.0 lack any collective defense against shocks.

---

### IND10: Adaptation Gap
- **Full Title:** Unmet Disaster Risk Reduction Deficit
- **Pillar:** Decision Support ($G37$ Priority Areas)
- **Formula:** Formula approval gate:
  $$\text{IND10} = \max(0, R_{\text{score}} - 100 \times \text{IND09})$$
- **Unit:** Gap index points ($0.0$ to $100.0$)
- **Mathematical Direction:** Positive ($+$) (Larger gap = higher intervention urgency)
- **2026 Reference Bounds:** $\min_{\text{ref}} = 0.0$, $\max_{\text{ref}} = 100.0$
- **Data Source:** Computed in `14_adaptation.py` and `15_priority.py`
- **Frequency:** Baseline / Annual update
- **Spatial Resolution:** Community
- **Interpretation:** Combines high composite hazard/exposure risk with the complete absence of mitigating infrastructure.

---

## 3. Supporting Thematic Indicator Families (11 to 20)

| ID | Indicator Family | Indicator Name | Unit | Direction | Source Table | Key Utility |
|:---|:---|:---|:---:|:---:|:---|:---|
| **IND11** | Climate | Rain Anomaly | mm/yr | $+$ | `DB05_Climate_Observations` | Tracks deviations from 30-year normal |
| **IND12** | Climate | Extreme Rain Days | Days | $+$ | `DB05_Climate_Observations` | Rain events > 50mm in 24 hours |
| **IND13** | Food Security | Crop Washout Area | Hectares | $+$ | `Food_Security_CLEAN` | Direct loss of agricultural harvest |
| **IND14** | Food Security | Food Consumption Score | FCS (0-112) | $-$ | `Food_Security_CLEAN` | Standard WFP dietary diversity metric |
| **IND15** | Livelihood | Asset Damage Value | NGN | $+$ | `Loss_Damage_CLEAN` | Quantified economic disaster loss |
| **IND16** | Security | Farmland Access Denial | $\%$ | $+$ | `Security_Impact_CLEAN` | Safe metric of conflict-driven isolation |
| **IND17** | Infrastructure| Water Point Inundation | $\%$ | $+$ | `Infrastructure_CLEAN` | Contamination risk of drinking supply |
| **IND18** | MRV | Intervention Effectiveness | $\%$ | $-$ | `Interventions_CLEAN` | Validated $IES = (R_b - R_a)/R_b \times 100$ |
| **IND19** | MRV | Residual Risk Score | $0-100$ | $+$ | `Interventions_CLEAN` | Post-intervention risk remaining |
| **IND20** | Data Quality | Data Confidence Rating | Category | $-$ | `Data_Confidence_CLEAN` | High / Moderate / Low / Unknown |

---
*Maintained under N-HYPPADEC Version Control — Baseline 2026*
