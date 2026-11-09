# CHER-CDSS Field Survey XLSForm Specification
## Master Mobile Data Collection Instrument v4.2.2 (Multi-Hazard, Security & AI CV Privacy Shield Addendum)
### KoboToolbox / ODK Collect Integration | November 2026

---

## 1. Instrument Overview

- **Form Title:** CHER-CDSS Community Resilience, Multi-Hazard & FEW-CAM Field Survey v4.2.2  
- **Form ID:** `cher_cdss_field_survey_v4_2`  
- **Version:** `2026110601`  
- **Primary Target Devices:** Android smartphones / tablets with KoboCollect or ODK Collect v2024+  
- **Storage Target:** Offline local encrypted storage $\longrightarrow$ HTTPS Sync $\longrightarrow$ `raw.submissions_landing` (PostgreSQL)  
- **Files:**
  - Standard Excel Workbook: [`02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.2.xlsx`](file:///c:/xampp/htdocs/GIS/02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.2.xlsx) (and [`v4.1.xlsx`](file:///c:/xampp/htdocs/GIS/02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.1.xlsx))
  - Survey Schema: [`02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.2_survey.csv`](file:///c:/xampp/htdocs/GIS/02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.2_survey.csv)
  - Choices Schema: [`02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.2_choices.csv`](file:///c:/xampp/htdocs/GIS/02_Fieldwork/CHER_CDSS_Master_XLSForm_v4.2_choices.csv)

---

## 2. Questionnaire Architecture & Modular Flow

```
[Start Survey]
      │
      ▼
Section 1: Enumerator & Informed Consent Gate
      │
      ├── (Consent = NO) ──▶ [Form Terminates / No Data Recorded]
      │
      └── (Consent = YES)
            │
            ▼
Section 2: Master Geography (10 States -> 186 Cascading LGAs -> Community -> GPS)
            │
            ▼
Section 3: Population, Lifeline Services & Livelihoods
            │
            ▼
Section 4: Climate Observations & Hydro-Meteorology
            │
            ▼
Section 5: Flood Intelligence & Historical Losses (Conditional on Flood Experience)
            │
            ▼
Section 6: Erosion Intelligence & Monitored Sites (Conditional on Erosion Presence)
            │
            ▼
Section 7: Food Security & Agricultural Losses
            │
            ▼
Section 8: Community Security & Banditry Impacts (Armed Raids, Cattle Rustling, Farm Denial)
            │
            ▼
Section 9: Adaptation, Interventions & MRV Tracking
            │
            ▼
Section 10: Photographic Media Protocol (Strict Non-PII Safeguards)
            │
            ▼
Section 11: Flood Early Warning Field Observations & Community Awareness
            │
            ▼
Section 12: Community Multi-Hazard & Environmental Problems (14 Canonical Themes)
            │
            ▼
[End Survey & Local Encrypted Save]
```

Section 12 incorporates the official 14-Theme National Multi-Hazard & Environmental Risk
taxonomy (Food Security, Bandit Attack, Air Pollution, Climate Change Impacts, Deforestation,
Desertification, Drought, Ecological Conflict, Erosion, Flooding, Lead Poisoning, Oil Spillage,
Solid Waste Management, Water Pollution) with ranking of primary community threat, severity,
and multi-year degradation trends.

---

## 3. Cascading Geography & Controlled Vocabulary (Stage 5.2)

The form enforces a 2-tier administrative cascade select:
1. **State:** User selects one of the 10 confirmed N-HYPPADEC states:
   - `NG-NIG` (Niger), `NG-KEB` (Kebbi), `NG-PLA` (Plateau), `NG-BEN` (Benue), `NG-KOG` (Kogi), `NG-KWA` (Kwara), `NG-KAD` (Kaduna), `NG-NAS` (Nasarawa), `NG-TAR` (Taraba), `NG-GOM` (Gombe).
2. **LGA:** Choice list is dynamically filtered using `choice_filter: state=${state_code}`.
   - Restricts choices to the exact official LGAs of that state (186 LGAs total).
   - Eliminates spelling variations, typos, and referential integrity violations before data leaves the field.

---

## 4. Key Skip Logic & Validation Constraints (Stages 5.3 & 5.4)

| Field Name | Trigger Condition / Relevance | Validation Constraint | Error / Warning Message |
|---|---|---|---|
| `grp_geo` through `grp_media` | `${consent_given} = 'yes'` | Mandatory consent | Survey terminates if consent is not granted. |
| `community_gps` | Always when consent granted | Accuracy $\le 30\text{m}$ flag; $< 100\text{m}$ hard gate | "GPS accuracy exceeds threshold. Move to open sky." |
| `estimated_population` | Population group | `. > 0 and . <= 100000` | "Population must be between 1 and 100,000." |
| `flood_frequency_5yrs` | `${flood_experience_past_year} = 'yes'` | `. >= 0 and . <= 20` | "Events must be between 0 and 20." |
| `flood_severity_rank` | `${flood_experience_past_year} = 'yes'` | Scale 1 to 5 | Rank 1 (Minor) to 5 (Catastrophic). |
| `erosion_type` | `${erosion_presence} = 'yes'` | Select one | Gully, Sheet, Rill, Riverbank. |
| `erosion_severity_rank`| `${erosion_presence} = 'yes'` | Scale 0 to 4 | Rank 0 (None) to 4 (Very Severe). |
| `crop_loss_pct` | Food security module | `. >= 0 and . <= 100` | "Percentage must be between 0 and 100." |
| `displaced_households` | `${displacement_observed} = 'yes'`| `. >= 0` | "Must be non-negative integer." |
| `bandit_attack_frequency` | `${bandit_attack_experienced} = 'yes'` | `. >= 0` | "Must be non-negative integer." |
| `environmental_problems_observed` | Section 12 Multi-Hazard | Select multiple (14 items) | Required selection of observed community hazards. |
| `primary_environmental_problem` | Observed hazards $> 0$ | Select one from observed | Single most severe threat to community. |
| `primary_problem_severity` | Primary problem selected | Scale 1 to 5 | Rank 1 (Minor) to 5 (Catastrophic). |
| `photo_category_1` / `_2` | `string-length(${site_photo_1}) > 0` | Select one (Infrastructure, Erosion, Flood, Household) | Category required for Level 3 CV Privacy Gating. |
| `consent_for_media_1` / `_2`| `string-length(${site_photo_1}) > 0` | Select one (Yes/No) | Required if human subjects appear in captured media. |
| `site_photo_1_desc` | `string-length(${site_photo_1}) > 0` | Text caption | Required if photo 1 is captured. |


---

## 5. Offline GPS and Media Protocol (Stage 5.5 & 5.6)

1. **Offline Mode:** The form does not require active cellular connectivity. Submissions are queued in ODK/KoboCollect memory.
2. **GPS Fix Procedure:** Wait for device GPS receiver to lock on at least 4 satellites until horizontal accuracy is within 15 metres.
3. **Media Safeguards (Privacy Level 2/3 & AI Computer Vision Shield):**
   - Photographic evidence must capture physical infrastructure, terrain erosion gullies, flood marks, or drainage channels.
   - **Level 3 Restricted Protocol:** If photos contain household compounds or accidental facial portraits, the Phase 2 AI Privacy Shield (`ai_field_anomaly_service.py`) automatically routes the media through a Gaussian face-blurring filter before any public or derived GIS layer export.
