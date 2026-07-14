# `cself/` — measuring C_self and R_self from physiological data

The pipeline behind the proceedings' claim that the induced flux `R_self`, the
integrative capacity `C_self`, and their margin `M = C_self − R_self` are
**measured** quantities, not only formal ones. Homeostasis is the self-decoder:
an analyte leaving its reference band is a candidate commitment, its return
in-range is a certification, and the restoration rate is `C_self`.

The same **unchanged** estimator is run on two cohorts — one synthetic and
ambulatory, one real and critically ill.

| file | what it does |
| --- | --- |
| `csself_estimator.py` | the estimator (v2). `CR = λ/μ` from **rates**; `SR` = mean number in system from **occupancy**. Their agreement with `SR = CR/(1−CR)` is therefore a test, not an identity. |
| `synthea_to_cself.py` | Synthea → per-unit `(C_self, R_self, CR, SR)` → `../figures/cself_measured_synthea.csv`, the input to **Figure 1**. |
| `mimic_demo_cself.py` | MIMIC-IV **demo** → the real-physiology estimates reported in **Section 3**. |

## Reproducing Figure 1 (Synthea)

Openly downloadable, no registration:

```
curl -O https://synthetichealth.github.io/synthea-sample-data/downloads/10k_synthea_covid19_csv.zip
unzip 10k_synthea_covid19_csv.zip
python3 synthea_to_cself.py --data 10k_synthea_covid19_csv
cd ../figures && python3 make_cself_measured.py     # -> cself_measured.pdf
```

Expected: 313,127 lab rows over 5,319 units, **1,898 units** placed on the regime
map, **90.3%** below the feasibility boundary (`R_self < C_self`).

## Reproducing the Section 3 estimates (MIMIC-IV demo)

The **MIMIC-IV Clinical Database Demo** is openly licensed (Open Data Commons
ODbL) and needs **no credentialing and no data use agreement**:

```
python3 mimic_demo_cself.py --download
```

It fetches three tables (`labevents`, `diagnoses_icd`, `patients`) from
PhysioNet and prints aggregates only. Expected:

```
units on the regime map: 78 / 100
degenerate in either rate: 0
below the feasibility boundary: 44.9%   (vs 90.3% for ambulatory Synthea)
median CR: 1.023                        (the boundary itself)
```

Same 13-analyte panel as the Synthea figure, but read against **MIMIC's own
per-assay reference bands** (`labevents.ref_range_lower/upper`, median per
`itemid`) rather than textbook ranges.

**How to read this.** Absolute rates are *not* comparable across the two cohorts
— ICU series run over days, ambulatory ones over years — so the dimensionless
`CR` is the compared quantity. The cohorts separate in the direction the
construct requires: the ambulatory population sits below the feasibility
boundary, the critically ill sit *at and above* it. At this cohort size that is
a **face-validity check on measurability, not a validation**: no ROC, no lead
time, no detection claim is made from it. Large longitudinal cohorts, the
estimator's sample complexity, and its detection ROC are future work.

The full MIMIC-IV database is credentialed and carries a DUA. Nothing here
touches it — only the openly licensed demo.

## Data citations

- Walonoski, J. et al. *Synthea*. JAMIA **25**, 230–238 (2018). doi:10.1093/jamia/ocx079
- Johnson, A. et al. *MIMIC-IV Clinical Database Demo* (v2.2). PhysioNet (2023). doi:10.13026/dp1f-ex47
- Goldberger, A. et al. *PhysioBank, PhysioToolkit, and PhysioNet*. Circulation **101**, e215–e220 (2000).
