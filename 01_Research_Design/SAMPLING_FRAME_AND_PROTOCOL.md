# RESEARCH DESIGN: FIELD SAMPLING FRAME & PROTOCOL
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System (CHER-CDSS)
### N-HYPPADEC / Ten Member States of Nigeria
**Document ID:** `RD-SFP-2026-v4.1` | **Stage:** 6.1 | **Status:** Approved Baseline  
**Governing Specification:** CHER-CDSS Master Implementation Scaffold v4.1 (October 2026)

---

## 1. Scope & Objectives

This Sampling Protocol formalizes the statistical architecture for field data collection across the ten N-HYPPADEC member states. It governs:
1. Sentinel community selection across ecological hazard strata.
2. Household sampling for livelihood, loss, food-security, and vulnerability assessments.
3. Geo-referenced site selection for erosion gullies and critical infrastructure audits.

---

## 2. Statistical Sampling Methodology

### 2.1 Multi-Stage Stratified Cluster Sampling
The sampling design follows a four-stage hierarchy:
- **Stage 1 (State Strata):** 10 Confirmed Member States (`NG-NIG`, `NG-KEB`, `NG-PLA`, `NG-BEN`, `NG-KOG`, `NG-KWA`, `NG-KAD`, `NG-NAS`, `NG-TAR`, `NG-GOM`).
- **Stage 2 (LGA / Basin Sub-strata):** 186 Local Government Areas stratified by ecological proximity to hydropower reservoirs and major river basins (Niger Basin, Benue Basin, Lake Chad / Komadugu Basin).
- **Stage 3 (Primary Sampling Units - PSUs):** Sentinel Communities (`Community_ID`) selected proportional to hazard exposure (Flood Plain, Reservoir Buffer, Gully Escarpment).
- **Stage 4 (Secondary Sampling Units - SSUs):** Households (`Household_ID`) selected via systematic random sampling along transect lines within each PSU.

### 2.2 Sample Size Determination Formula

#### Household Sample Size (Cochran's Formula with Design Effect Adjustment)
For estimating household vulnerability and disaster impact proportions with $95\%$ confidence level:

$$n_0 = \frac{Z^2 \cdot p \cdot (1 - p)}{e^2}$$

Where:
- $Z = 1.96$ ($95\%$ confidence level)
- $p = 0.50$ (maximum variability assumption for conservative sample size)
- $e = 0.05$ (desired margin of error: $\pm 5\%$)

Yielding base unadjusted sample size:
$$n_0 = \frac{1.96^2 \cdot 0.50 \cdot 0.50}{0.05^2} = \frac{3.8416 \cdot 0.25}{0.0025} = 384.16 \approx 385\text{ households}$$

#### Adjustment for Cluster Sampling Design Effect ($DEFF$)
To account for intra-cluster correlation within riverine communities:
$$n_{\text{adj}} = n_0 \times DEFF$$
Where $DEFF = 1.50$ (standard design effect for complex cluster survey):
$$n_{\text{adj}} = 385 \times 1.50 = 577.5 \approx 578\text{ households}$$

#### Adjustment for Non-Response & Inaccessibility
Anticipating a $10\%$ non-response or seasonal access barrier rate ($r = 0.10$):
$$N_{\text{target}} = \frac{n_{\text{adj}}}{1 - r} = \frac{578}{0.90} \approx 642\text{ households (Full 10-State Rollout)}$$

#### 2026 Baseline Phase 1 Sample (50 Sentinel Communities)
For the 2026 Baseline calibration cycle, a representative sample of **50 sentinel communities** was established across all 10 states (5 communities per state), with **5 consented households per community** ($250$ in-depth household surveys) and complete physical enumeration of contiguous erosion sites ($75$ sites) and infrastructure facilities ($100$ assets).

---

## 3. Stratification Matrix Across the Ten States

| State Code | State Name | LGAs Total | Dominant Hazard Strata | 2026 Sentinel PSUs | Monitored Household SSUs |
|:---|:---|:---:|:---|:---:|:---:|
| `NG-NIG` | Niger | 25 | Hydro Spillway / Kainji-Jebba-Shiroro Basin | 5 Communities | 25 Households |
| `NG-KEB` | Kebbi | 21 | River Niger Floodplain / Lowland Siltation | 5 Communities | 25 Households |
| `NG-PLA` | Plateau | 17 | High-Elevation Gully Incision / Mining Pits | 5 Communities | 25 Households |
| `NG-BEN` | Benue | 23 | River Benue Alluvial Flood Basin / Washouts | 5 Communities | 25 Households |
| `NG-KOG` | Kogi | 21 | Niger–Benue Confluence / Deep Submergence | 5 Communities | 25 Households |
| `NG-KWA` | Kwara | 16 | Lower Jebba Discharge / Riparian Bank Scour | 5 Communities | 25 Households |
| `NG-KAD` | Kaduna | 23 | River Kaduna Flash Floods / Urban Drainage | 5 Communities | 25 Households |
| `NG-NAS` | Nasarawa | 13 | Benue Tributary Surges / Agricultural Gullies| 5 Communities | 25 Households |
| `NG-TAR` | Taraba | 16 | Upper Benue / Kashimbila Dam Buffer Zone | 5 Communities | 25 Households |
| `NG-GOM` | Gombe | 11 | Dadin Kowa Basin / Semi-Arid Gully Scarp | 5 Communities | 25 Households |
| **TOTAL** | **10 States** | **186 LGAs** | **All 4 Major Hydro-Geomorphic Strata** | **50 Communities** | **250 Households** |

---

## 4. Household Selection & Transect Walk SOP

1. **Community Ingress & Authorization:** Obtain verbal and signed community leadership assent (District Head / Village Chief) before entering community boundaries.
2. **Transect Line Establishment:** From the community center / traditional palace, establish two perpendicular cardinal transect axes (North–South, East–West).
3. **Sampling Interval ($k$):** Count total residential compounds along each axis ($N_{\text{axis}}$); set sampling interval $k = N_{\text{axis}} / 3$. Select every $k$-th compound.
4. **Household Head Consent:** Administer the mandatory informed consent script (`XLSForm` Section 1).
   - If consent is refused, advance to the immediate next compound ($k+1$).
   - Never coerce, offer unapproved inducements, or record household data without explicit consent.

---

## 5. Community Replacement Protocol

In the event of unanticipated insecurity, impassable flood waters, or localized resistance:
1. **First Alternate:** Select the pre-identified replacement community within the **identical LGA and identical hazard strata** from the backup sampling list.
2. **Second Alternate:** If no safe community exists within the same LGA, select a contiguous LGA within the same state exhibiting equivalent distance to river/reservoir.
3. **Documentation:** Log the replacement reason, date, and approving supervisor in `Audit_Trail_CLEAN.csv` and the survey metadata header.
4. **Strict Prohibition:** Never replace a community with an accessible but non-exposed settlement (e.g. replacing an inaccessible flood basin community with a dry upland market center).

---
*Approved by N-HYPPADEC Scientific Advisory Board & Ethics Committee — October 2026*
