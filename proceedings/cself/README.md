# `cself/` — measuring C_self and R_self from physiological data

The pipeline behind the proceedings' claim that the induced flux `R_self`, the
integrative capacity `C_self`, and their margin `M = C_self − R_self` are
**measured** quantities, not only formal ones. Homeostasis is the self-decoder:
an analyte leaving its reference band is a candidate commitment, its return
in-range is a certification, and the restoration rate is `C_self`.

The same computational procedure is run on two cohorts — one synthetic and
ambulatory, one real and critically ill — each read against cohort-specific
reference ranges.

**Scope (proceedings, revisions 1 and 2, Sep 2026).** The physiological restoration
process is parallel (many analytes can be out of range and restore at once), so
the paper uses these data **only for the rates** `R_self`, `C_self` and their
margin. The single-server stability law is **not** applied to them: `CR` here is
a descriptive load ratio and `R_self = C_self` is a reference line, not a
stability boundary (an infinite-server process is stationary at every load).

| file | what it does |
| --- | --- |
| `csself_estimator.py` | the estimator (v2). `CR = λ/μ` from **rates** (`R_self` = onsets / observation span; `C_self` = restorations / union-busy time); `SR` = mean number in system from **occupancy**. `CR` exceeds 1 only when counted excursions remain unresolved at series end, so its value depends on the observation and censoring scheme. |
| `synthea_to_cself.py` | Synthea → per-unit `(C_self, R_self, CR, SR)` → `../figures/cself_measured_synthea.csv`, the input to **Figure 2**. |
| `mimic_demo_cself.py` | MIMIC-IV **demo** → the real-physiology estimates reported in **Section 3**. |

The `SR` column of the estimator and of the shipped CSV is the quantity the proceedings
paper writes **𝒩** and calls the uncertified backlog; the column name predates that
choice and is kept so that the released data file is stable.

## Reproducing Figure 2 (Synthea)

Openly downloadable, no registration:

```
curl -O https://synthetichealth.github.io/synthea-sample-data/downloads/10k_synthea_covid19_csv.zip
unzip 10k_synthea_covid19_csv.zip
python3 synthea_to_cself.py --data 10k_synthea_covid19_csv
cd ../figures && python3 make_cself_measured.py     # -> cself_measured.pdf
```

Expected: 313,127 lab rows over 5,319 units, **1,898 units** placed on the rate
plot, **90.3%** below the `R_self = C_self` reference line.

## Reproducing the Section 3 estimates (MIMIC-IV demo)

The **MIMIC-IV Clinical Database Demo** is openly licensed (Open Data Commons
ODbL) and needs **no credentialing and no data use agreement**:

```
python3 mimic_demo_cself.py --download
```

It fetches three tables (`labevents`, `diagnoses_icd`, `patients`) from
PhysioNet and prints aggregates only. If Python cannot verify the PhysioNet
certificate (a python.org macOS install without its certificates), download the
three files with `curl -L -O` from `https://physionet.org/files/mimic-iv-demo/2.2/hosp/`
into `mimic_demo/hosp/` and run the script without `--download`. Expected:

```
units on the rate plot: 78 / 100
degenerate in either rate: 0
below the R_self = C_self line: 44.9%   (vs 90.3% for ambulatory Synthea)
median CR: 1.023                        (near the reference line)
```

The same 13-analyte panel is requested as for the Synthea figure, but read against
**MIMIC's own per-assay reference bands** (`labevents.ref_range_lower/upper`, median
per `itemid`) rather than textbook ranges. Only **9** of the 13 resolve a usable band
in Synthea against **13** in MIMIC-IV, so the two arms are not measured on the same
panel.

**How to read this: no contrast is drawn between the cohorts** (round 3, reviewer
comment 1; the five analyses he asked for were run and are in the paper). Absolute
rates are not comparable across the two cohorts — ICU series run over days, ambulatory
ones over years — and the dimensionless `CR` does not repair that, because the cohorts
differ in the observation scheme rather than in a capacity property:

- `CR` exceeds one only through excursions left open at the end of a record, and
  **97.4% of MIMIC-IV units and 76.3% of Synthea units end on one**;
- the median `CR` of 1.023 has a bootstrap interval **[0.904, 1.085]**, which contains
  one;
- excluding the censored terminal excursions forces onsets to equal restorations, so
  `CR` collapses to the busy fraction and cannot exceed one — both cohorts then read
  100% below the line, which is a **degeneracy, not a finding**;
- per-analyte `CR` varies by more than an order of magnitude within a cohort, so a
  single pooled value per unit averages over very different series;
- the panels differ, as above.

What the two cohorts do show is that the estimator runs on real event streams of two
kinds and returns finite rates. No clinical, causal or detection claim is drawn, and no
ROC or lead time is computed. A censoring-aware duration estimator (Kaplan–Meier on
excursion durations) is the method a future cohort study would need; at 97% censoring it
would rest almost entirely on extrapolation, and it is not attempted here. Matched-cadence
analysis, downsampling and a pre-specified detection plan remain future work.

The full MIMIC-IV database is credentialed and carries a DUA. Nothing here
touches it — only the openly licensed demo.

## Data citations

- Walonoski, J. et al. *Synthea*. JAMIA **25**, 230–238 (2018). doi:10.1093/jamia/ocx079
- Johnson, A. et al. *MIMIC-IV Clinical Database Demo* (v2.2). PhysioNet (2023). doi:10.13026/dp1f-ex47
- Goldberger, A. et al. *PhysioBank, PhysioToolkit, and PhysioNet*. Circulation **101**, e215–e220 (2000).
