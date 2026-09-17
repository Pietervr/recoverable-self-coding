# `proceedings/figures/`: the figures of the proceedings paper

| file | figure | run |
| --- | --- | --- |
| `rsc_pipeline.tex` | Figure 1, the schematic of the certification pipeline (hand-placed TikZ) | `pdflatex rsc_pipeline.tex` |
| `make_cself_measured.py` | Figure 2, from the shipped `cself_measured_synthea.csv` | `python3 make_cself_measured.py` (run in this folder) |
| `rsc_simulation.py` | Figure 3, and every number of Section 7 and Supplementary S2 (printed to the terminal) | `python3 rsc_simulation.py` (about ten seconds) |

The simulation uses no external data and fixed seeds (`numpy.random.SeedSequence`), so its printed numbers
are identical on every run under the versions in `requirements-lock.txt`. The exact, simulation-free checks of
Proposition 1 are in `../checks/` (`python3 ../checks/proposition1_exact_checks.py`). The physiological
pipeline that produces `cself_measured_synthea.csv` and the MIMIC-IV demo estimates is in `../cself/`.

The Wilson intervals quoted in Section 3 are two-sided 95% Wilson score intervals computed from the printed
counts (1714 of 1898 and 35 of 78); the worked review-board example of the Introduction is arithmetic from
`P_c = 1 - exp(-M * Dt)`. Neither is printed by a script.
