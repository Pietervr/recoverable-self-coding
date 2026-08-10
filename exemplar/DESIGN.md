# The RSC Exemplar: a complete worked example, end to end

**Goal.** One detailed, reproducible demonstration of how to use Recoverable
Self-Coding practically — from raw multi-source data all the way to gated
decisions — exercising *every* object the foundational paper defines, in the
order the paper defines them. This is the "how to actually use it" companion
to the definition (paper §2) and the verification (paper §3).

**The dataset is itself part of the method.** In the spirit of
assemble-your-own-training-corpus, the exemplar stitches a *journey corpus*
from openly available sources with disjoint strengths:

| Segment | Source | License | What it contributes |
|---|---|---|---|
| Ambulatory baseline + deterioration | Synthea 10k COVID-19 cohort (synthetic) | open | years of labs; encounters incl. inpatient/ICU; outcomes; unlimited regeneration |
| ICU episode | PhysioNet/CinC-2019 (real, hourly) | open (challenge) | dense real physiology at the boundary; sepsis labels |
| ICU robustness / treatment detail | eICU-CRD Demo v2.0.1 (real) | open, no credentialing | meds, treatment, severity scores, dispositions |
| Ambulatory recovery tail | Synthea (synthetic) | open | post-discharge consolidation window |

Raw downloads live under `exemplar/data/` (gitignored, re-pullable); only
aggregates, stitched-journey *indices* (which unit + which offsets, no raw
rows), and figures are committed.

## Pipeline stages (each maps to a paper concept)

1. **Harmonize** (`schema.py`) — every source → one event table:
   `(unit, t_days, var, value, lo, hi)`. Bands: per-assay where the source
   ships them, the standard adult panel otherwise (same policy as the paper).
2. **Microstates** (`microstate.py`) — paper §2.1 made concrete: at each
   observation time the microstate ω(t) is the panel state vector (which
   variables in/out of band + backlog composition); the macrostate is
   Σ(t) = (R_self, C_self, ℳ) by coarse-graining. This is the map nobody
   shows on data; the exemplar shows it explicitly.
3. **Estimate** (`estimate.py`) — the unchanged excursion/restore estimator
   per segment (paper §3.1) *plus* the dynamic layer: a Gamma–Poisson
   conjugate filter giving a posterior over CR(t) that updates per event —
   the instrument the static estimator cannot provide on short windows.
4. **Queue check** (`queue_check.py`) — observed backlog occupancy vs
   CR/(1−CR) on the stitched corpus (paper §2.3).
5. **Gates** (`gates.py`) — C_self as a gate (paper §4.1/§4.2 levers):
   - G1 *escalation*: posterior P(CR>θ₁) exceeds p₁ → workup/screening
     (certification-capacity injection).
   - G2 *admission*: sustained ℳ<0 (posterior) → splice ICU segment
     (exogenous capacity injection).
   - G3 *discharge*: P(CR<θ₃) exceeds p₃ with positive margin drift → back
     to ambulatory tail.
   Gate parameters are stated, not tuned to outcomes.
6. **Stitch** (`stitch.py`) — the journey builder: Synthea deteriorating
   record + acuity/sepsis-matched real ICU stay + recovery tail, all in
   events/day units on one clock. Match on (implied CR at admission, sepsis
   flag); record the stitch index for reproducibility.
7. **Personalize** — run the same shock against two capacity phenotypes
   (a thin-margin and a high-reserve unit — the paper's Marli/Nduku pair,
   selected from data by capacity quartile at matched load, not invented).
8. **Render** (`make_journey_figure.py`) — the money figure: one continuous
   ℳ(t) with its posterior band across care levels, gates marked, backlog
   underneath; plus the two-phenotype overlay.

## Honesty constraints (stated wherever the exemplar is shown)

- A stitched synthetic+real journey demonstrates the **instrument**, not
  clinical evidence. The paper's CinC/MIMIC/Synthea results remain the
  evidence base.
- Gate thresholds are illustrative policy parameters; no outcome fitting.
- Every segment's provenance is visible in the figure (segment shading).

## Paper landing

A worked-example section in the foundational paper (v2) before the
Discussion, ~4–6 pages incl. the journey figure and the
microstate→macrostate figure; the full runnable pipeline stays here.

## Status

- [x] Design (this file)
- [x] Synthea 10k cohort downloaded (`data/`)
- [x] `schema.py` (microstate builder pending)
- [x] `estimate.py` (static + Gamma–Poisson filter)
- [x] `gates.py` + `stitch.py` (+ `make_journey_figure.py`; stitch_index.json committed)
- [ ] eICU demo pulled; robustness pass
- [ ] Journey + phenotype figures
- [ ] Paper section
