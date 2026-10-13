# `proceedings/checks/`: the exact and numerical checks of the proceedings paper

Every script here is self-contained (`numpy` only), carries fixed seeds and writes a JSON file, so
the published numbers are reproducible to the digit under the versions in `requirements-lock.txt`.
Run them from this folder.

| file | what it establishes | run |
| --- | --- | --- |
| `proposition1_exact_checks.py` | exact, simulation-free checks of Proposition 1: the H2/M/1 root from a closed-form quadratic, the boundary amplitudes, three worked examples | `python3 proposition1_exact_checks.py` |
| `estimator_calibration.py` | request 5(c): the Figure 1 estimator recovers λ, the backlog and *P*<sub>c</sub> from a genuine event log, with no generating rate fed back in | `python3 estimator_calibration.py --kind MM1 --out calibration_mm1.json`<br>`python3 estimator_calibration.py --kind MD1 --out calibration_md1.json` |
| `margin_precision.py` | requests 5(a) and 5(b): the delta method with the joint covariance kept, the moving-block bootstrap, the observation span for a stated criterion, and the no-clipping counterexample | `python3 margin_precision.py --reps 48 --boot 400 --out margin_precision.json` |
| `abandonment_variant.py` | request 4: the M/M/1+D closed form by level crossing, checked against an event-driven simulation and against the lossless limit, plus the LCFS discipline comparison | `python3 abandonment_variant.py --out abandonment.json` |
| `run_length_check.py` | request 2: the two run protocols against the exact values at 48 replications per cell, for the bounded deadline fraction and for the divergent backlog | `python3 run_length_check.py --reps 48 --out run_length.json` |

The flags above are the defaults and are written out because they are the values the paper reports;
`--boot 400` in particular is the bootstrap resample count behind the Supplementary S2.6 table.
`margin_precision.py` takes a few minutes, the others under a minute each.

## Symbols

The manuscript writes the mean number of uncertified commitments **𝒩** and calls it the uncertified
backlog. The code predates that choice and still names the variable `sr`, after the stability index
of the foundational preprint. They are the same quantity. `margin` is 𝓜 = *C*<sub>self</sub> −
*R*<sub>self</sub>, `cr` is the capacity ratio, `dt` is the certification horizon Δ*t* and `H` is the
option-loss window.

## Two things these checks do not establish

- `estimator_calibration.py` generates its logs from the model it then estimates, so it establishes
  **synthetic estimator validity only**. It says nothing about whether a real workflow satisfies the
  model.
- The bootstrap block length is capped at *n*/50 as a safeguard. That is a choice, not a proof that
  the block length is adequate or that the intervals attain nominal coverage on these series.
