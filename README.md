# Recoverable Self-Coding (RSC) — figure-generation and analysis code

Code that reproduces all figures and the empirical pipeline for the **Recoverable
Self-Coding** papers by Pieter van Rooyen:

- **Special Issue article** — *Entropy, Capacity, and the Continuity of Agency in
  Human–AI Systems: A Recoverable Self-Coding Account* (Entropy, "Complexity"
  section).
- **Proceedings** — *Recoverable Self-Coding: A Measurable Rate–Capacity Law for Systems
  That Couple Inference to Irreversible Action* (*Physical Sciences Forum*, Entropy 2026
  proceedings, manuscript psf-3705961).
- **Poster** — Entropy 2026.
- Foundational paper (separate repo): *First-Order Recoverability Collapse in
  Self-Referential Information Decoders* — code at
  <https://github.com/Pietervr/cascade-collapse>; preprint
  [10.20944/preprints202601.0688](https://doi.org/10.20944/preprints202601.0688).

RSC casts the recoverability of irreversible action as a Shannon-style
rate–capacity law: a self-decoder holds an induced flux `R_self` below an
integrative capacity `C_self`, with capacity ratio `CR = R_self/C_self`; the
uncertified-commitment backlog is modelled as a single-server certification
queue, and the stability index `SR` (in the proceedings paper, the mean number of
uncertified commitments) grows as `(1−CR)^−1` near the boundary `CR = 1`.

## Layout

```
special_issue/
  figures/      figure scripts for the SI (rsc_*.py, fig_*.py) + per-figure README
  empirical/    the two operational substrates: GitHub review queues, Wikipedia edits
  derivation/   the effective-capacity derivation note + the invertibility-axis model
proceedings/
  figures/    proceedings figure scripts (rsc_pipeline.tex = Figure 1, the schematic;
              make_cself_measured.py = Figure 2; rsc_simulation.py = Figure 3)
  checks/     proposition1_exact_checks.py: exact, simulation-free checks of Proposition 1
              (the H2/M/1 root from a closed-form quadratic, the boundary amplitudes,
              and three worked examples); reads two functions from figures/rsc_simulation.py
  cself/      the physiological pipeline: the C_self/R_self estimator + both cohort
              drivers (Synthea -> Figure 2; MIMIC-IV demo -> the Section 3 estimates)
poster/figures/        poster figure scripts
```

`special_issue/figures/README.md` maps each script to its figure and result;
`proceedings/figures/README.md` gives the run command for each proceedings figure;
`proceedings/cself/README.md` documents the physiological pipeline and how to
reproduce its published numbers.

## Running

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python special_issue/figures/rsc_engine.py      # writes the figure PDF into the working dir
```

The simulation figures (`rsc_engine`, `rsc_estimators`, `rsc_instrument`,
`rsc_coupled`, `fig_invertibility`, the proceedings/poster scripts) are
self-contained — they need only `numpy`/`matplotlib`.

## Empirical data

The two field datasets are **not redistributed** (size); they are re-pullable
from public sources, then the figure scripts read pinned snapshots from `/tmp`
(override with `GH_DATA` / `MWH_DATA`):

- **GitHub** PR lifecycles via the authenticated `gh` GraphQL API —
  `special_issue/empirical/gh_fetch.py`, `gh_fetch_floods.py` (write to `/tmp/gh`).
- **Wikipedia** `mediawiki_history` dumps — `special_issue/empirical/dl_mwh.py`
  (writes to `/tmp/mwh`).

Then `fig_github.py`, `fig_wikipedia.py`, `fig_earlywarning.py`, and the
`analyze_*.py` probes read those snapshots.

## Physiological data (proceedings Section 3 / Figure 2)

Both cohorts are **openly available** and neither is redistributed here:

- **Synthea** 10k COVID-19 synthetic cohort — no registration.
  `proceedings/cself/synthea_to_cself.py --data <unzipped dir>` regenerates
  `proceedings/figures/cself_measured_synthea.csv` (the Figure 2 input): 1,898
  units with non-degenerate rates, 90.3% below the reference line `R_self = C_self`.
- **MIMIC-IV Clinical Database Demo** (100 ICU patients) — Open Data Commons
  ODbL, **no credentialing and no DUA**. `proceedings/cself/mimic_demo_cself.py
  --download` fetches it and prints the Section 3 aggregates: 78/100 units with
  non-degenerate rates, 44.9% below the reference line, median CR 1.023. The restoration
  process is parallel (infinite-server), so the line is a reference marker and not a
  stability boundary; the contrast between the cohorts is descriptive only.

The same computational procedure is applied to both cohorts, with cohort-specific
reference bands (textbook ranges for Synthea, MIMIC's own per-assay bands for MIMIC). The full,
credentialed MIMIC-IV database is not used. See `proceedings/cself/README.md`.

## Honest-scoping notes (recorded with the code)

- `special_issue/figures/fig_effcapacity.py` records a **negative result**: a
  count-based (SR) controller lags the regime it tracks, so the "alarm = capacity
  gain" is not cleanly computable — the paper makes that point qualitatively.
- `fig_earlywarning.py` detrends on **log-backlog**: the raw-backlog variance
  rises mechanically with the level, so only the level-invariant autocorrelation
  is reported as the critical-slowing-down signature (a modest, sign-contrast
  result).
- `derivation/invertibility_axis_*` is an **illustrative** model (a queue coupled
  to a drifting environment) used only to show the capacity and invertibility
  axes are independent.

## License

MIT (see `LICENSE`). If you use this code, please cite the papers above.
