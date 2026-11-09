# RUSLE Methodology Specification
## Revised Universal Soil Loss Equation — CHER-CDSS v2.0

**Version:** v1.0 | **Date:** 2026-10-14

---

## 1. Formula

```
A = R × K × LS × C × P
```

| Symbol | Factor | Unit | Source | Notes |
|---|---|---|---|---|
| A | Annual soil loss | t/ha/yr | Computed | Output of RUSLE |
| R | Rainfall erosivity | MJ·mm/(ha·hr·yr) | G22 + CHIRPS | EI30 index |
| K | Soil erodibility | t·ha·hr/(ha·MJ·mm) | ISRIC SoilGrids | Clip to study area |
| LS | Slope-length factor | Dimensionless | G09 + G10 | McCool et al. 1987 |
| C | Cover-management factor | Dimensionless | G15 | See Table 1 below |
| P | Support practice factor | Dimensionless | Field data / default | Default = 1.0 where unknown |

---

## 2. R-Factor Computation

The rainfall erosivity R-factor is computed from CHIRPS daily rainfall (SRC018)
using the Modified Fournier Index (MFI) → EI30 conversion:

```
EI30 ≈ 0.04 × (MFI)^1.56    (Brown and Foster 1987; calibrated for West Africa)
```

Where MFI = Σ (monthly_rainfall² / annual_rainfall) across all months.

**Alternative:** Use ISRIC GloREDa global rainfall erosivity dataset where
local computation is not feasible. Document which was used.

---

## 3. K-Factor Source

Download from ISRIC SoilGrids:
- URL: https://soilgrids.org/
- Variable: Soil erodibility (K-factor) at 250m resolution
- Clip to study area + 10km buffer
- Register as SRC_ISRIC_K (add to SOURCE_REGISTER.csv)

---

## 4. LS-Factor Computation

```python
# Computed from G09 DEM and G10 slope using:
# McCool et al. (1987) — standard RUSLE LS factor
# LS = (flow_acc * cell_size / 22.13)^m * (sin(slope_rad) / 0.0896)^n
# where m=0.5 for slope > 5%; n=1.3 for slope > 5% (simplified)
```

Input layers: G09 DEM + G14 flow accumulation + G10 slope (degrees)

---

## 5. C-Factor Lookup Table (Table 1)

Approved C-factors by ESA WorldCover class:

| Class Code | Class Name | C-Factor | Reference |
|---|---|---|---|
| 10 | Tree cover | 0.001 | Wischmeier & Smith 1978 |
| 20 | Shrubland | 0.010 | Morgan 2005 |
| 30 | Grassland | 0.050 | Morgan 2005 |
| 40 | Cropland | 0.200 | Literature range 0.1–0.4; use 0.2 pending crop-type data |
| 50 | Built-up | 0.001 | Sealed surface; RUSLE output = 0 (P=0 for impervious) |
| 60 | Bare/sparse vegetation | 0.600 | Highly erodible |
| 70 | Snow/ice | 0.000 | N/A |
| 80 | Water | 0.000 | N/A |
| 90 | Wetland | 0.010 | Vegetated; low erosion |
| 95 | Mangroves | 0.001 | Root protection |
| 100 | Moss/lichen | 0.020 | Limited protection |

**Rule:** These C-factors must be reviewed by a soil scientist before production use.
Store approved values in `LKP_RUSLE_C_Factors.csv`.

---

## 6. P-Factor

Default P = 1.0 (no conservation practice) where field data unavailable.

Where DB06 or DB03 records show erosion control works (Control_Present = Yes;
Control_Condition = Good or Fair): apply P = 0.6 for that site.

Document all P-factor assumptions in processing log.

---

## 7. Output Classification

| RUSLE Value (t/ha/yr) | Class | Action |
|---|---|---|
| 0–5 | Slight | Monitor |
| 5–10 | Moderate | Preventive measures |
| 10–50 | High | Priority intervention |
| 50–200 | Very High | Urgent rehabilitation |
| > 200 | Extreme | Emergency; field verify before reporting |

Map to `LKP_LandDegradationClasses.csv` using IND16 thresholds.

---

## 8. Limitations and Uncertainty

- RUSLE estimates **sheet and rill erosion only** — gully erosion (major in SE Nigeria) requires separate assessment (DB03 + G26/G27)
- C-factors from literature; local calibration improves accuracy
- P-factor = 1.0 assumption overestimates erosion where conservation works exist
- RUSLE valid at field scale (< 1 ha); community-level aggregation introduces uncertainty
- All RUSLE outputs must carry a data confidence rating (Moderate at baseline)

---

*Reference: Wischmeier, W.H. and Smith, D.D. (1978). Predicting Rainfall Erosion Losses. USDA Agricultural Handbook No. 537.*
