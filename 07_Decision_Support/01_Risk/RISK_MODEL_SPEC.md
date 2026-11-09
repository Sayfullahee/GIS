# Risk Model Specification
## Climate–Hydropower–Erosion–Community Resilience Decision-Support System
### For the Ten N-HYPPADEC States of Nigeria

**Model ID:** Risk_Model_v4.1  
**Version:** v4.1 | **Date:** 2026-10-07 | **Status:** Operational Decision Specification (CHER-CDSS Scaffold v4.1)  
**Governance:** Provisional baseline model pending Steering Committee ratification (Stage 17.5)

---

## 1. Model Purpose and Core Scientific Principles

This specification defines the composite risk model used to produce community-level risk scores (G35) and priority rankings (G37) for the ten N-HYPPADEC states of Nigeria.

The model is a **decision-support tool** and a **decision-support index**. It produces relative risk rankings to guide prioritisation of interventions, field investigation, and resource allocation. It is explicitly **not a probability** model, not a probability of disaster, not a return period map, and not an unvalidated prediction of disaster outcomes.

---

## 2. Master Composite Risk Formula

$$R = 0.35H + 0.25E + 0.25V + 0.15C$$

Where all components are normalised to **0–100** (0 = lowest risk; 100 = highest risk):

| Component | Symbol | Provisional Weight | Layer | Concept |
|---|---|---|---|---|
| **Hazard** | $H$ | 0.35 (35%) | G31 | Exposure to flood and erosion hazard |
| **Exposure** | $E$ | 0.25 (25%) | G32 | Population and assets situated within hazard zones |
| **Vulnerability** | $V$ | 0.25 (25%) | G33 | Socio-economic sensitivity and lack of adaptive capacity |
| **Criticality** | $C$ | 0.15 (15%) | G34 | Dependence on critical services, hydropower, and infrastructure |

**Weight Rationale & Governance:**
- Hazard receives the highest weight (0.35) as the primary physical driver of threat.
- Exposure (0.25) and Vulnerability (0.25) are co-equal impact mediators.
- Criticality (0.15) accounts for cascading systemic disruption (hydropower generation, inter-state grid, lifeline services).
- **Provisional status:** In accordance with Scaffold v4.1 Stage 17.5, these baseline weights are provisional pending formal Steering Committee sign-off.
- **Weight sum check:** $0.35 + 0.25 + 0.25 + 0.15 = 1.00$ ✓

---

## 3. Alternative Aggregation Form Check (Stage 17.9)

To prevent the theoretical artifact where zero exposure ($E=0$) could mathematically yield a high risk score under purely additive combination, every calculation run must compute the multiplicative / geometric alternative:

$$R_{\text{mult}} = H^{0.35} \times E^{0.25} \times V^{0.25} \times C^{0.15}$$

- Under this formulation, if $E = 0$, then $R_{\text{mult}} = 0.0$.
- Spearman rank correlation ($\rho$) and rank order differences between additive and multiplicative formulations must be documented in the analytical report.

---

## 4. Sensitivity Models (S1 and S2)

To evaluate model stability under varying policy priorities:

| Model ID | Name | H Weight | E Weight | V Weight | C Weight | Rationale |
|---|---|---|---|---|---|---|
| **Base** | Provisional Baseline | 0.35 | 0.25 | 0.25 | 0.15 | Standard UNDRR / N-HYPPADEC mandate balance |
| **S1** | Equal Weights | 0.25 | 0.25 | 0.25 | 0.25 | Unbiased reference comparison |
| **S2** | Hazard-Dominant | 0.45 | 0.20 | 0.20 | 0.15 | Emphasizes physical hazard extremes |

---

## 5. Fixed Normalization Reference Bounds (v4.1 Stage 17.8)

Min and max reference bounds are **frozen at the 2026 baseline** (`REFERENCE_BOUNDS_REGISTER.csv`) and are **never** recalculated from each incoming operational dataset. Re-computing bounds dynamically would render longitudinal trends and before/after intervention comparisons invalid.

- **Positive normalization:** $x_{\text{norm}} = 100 \times \frac{x - \min_{\text{ref}}}{\max_{\text{ref}} - \min_{\text{ref}}}$
- **Inverse normalization:** $x_{\text{norm}} = 100 \times \frac{\max_{\text{ref}} - x}{\max_{\text{ref}} - \min_{\text{ref}}}$
- **Out-of-bounds clipping:** Observed values $x < \min_{\text{ref}}$ are clipped to $0.0$; values $x > \max_{\text{ref}}$ are clipped to $100.0$ and flagged for audit.

---

## 6. Intervention Effectiveness Score (IES) & Residual Risk (Section 34)

Where verified before/after evidence exists:

$$\text{IES} = \left(\frac{\text{Risk}_{\text{before}} - \text{Risk}_{\text{after}}}{\text{Risk}_{\text{before}}}\right) \times 100\%$$

**Validity Rules (v4.1):**
1. $\text{Risk}_{\text{before}}$ and $\text{Risk}_{\text{after}}$ must use identical model versions and identical frozen baseline reference bounds.
2. If $\text{Risk}_{\text{before}} = 0$, IES is mathematically undefined and reported as `N/A`.
3. Metric must be accompanied by observation dates, counterfactual method, and Data Confidence rating.
4. Without formal experimental design, the metric must be labelled as `Observed Risk Change`, not causal impact.
5. $\text{Residual Risk} = \text{Risk}_{\text{after}}$.

---

## 7. Approval and Audit Record

- **Drafted By:** Technical Team & Risk Modelling Group  
- **Methodology Version:** Risk_Model_v4.1  
- **Scaffold Alignment:** CHER-CDSS Master Scaffold v4.1 (Sections 17, 34, 44)  
- **Approval Status:** Recommended for Steering Committee Formal Approval (Phase 0/1)  
