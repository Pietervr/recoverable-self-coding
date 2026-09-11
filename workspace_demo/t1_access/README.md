# T1, model side — analysis code for the pre-registration

The pre-registration is **`PREREGISTRATION_T1_model.md`** (draft until its v2 freeze). This folder holds
the code its §15 manifest names; the pieces that exist are listed below, the rest (`capture.py`,
`decode_cal.py`, `h3.py`, `stimuli/`) follow the stimulus bank and the server addition.

| file | pre-registration section | what it is |
|---|---|---|
| `models.py` | §7, §7.4, §9 | the nine members (M0; G: M2B M2H M2S M2K; X: M3 M3H M3V M3L) as JAX log-likelihoods, the joint concept likelihood by adaptive Gauss–Hermite, the declared start generator, L-BFGS-B multi-start with analytic gradients, the recovery chain, samplers and state posteriors |
| `analyze.py` | §8 | stratified concept folds, the per-layer pipeline (inner selection, refit, held-out joint scores, the three predictors), the concept-cluster bootstrap, band means and the §8.3 rule, the refitting bootstrap fallback, SPM curves |
| `simulate.py` | §7.5, §10 | synthetic CONF-sized datasets from every member at declared base and grid parameters, the recovery grid, calibration nulls, the gain calibration and power alternatives, summaries |
| `verify.py` | — | V1 ports vs the numpy originals, V2 gradients, V3 quadrature vs dense integration, V4 densities and samplers, V5 self-refits |
| `bench.py` | §14 | timing of one fit per member and one full layer at confirmation size |
| `run_sims.sh` | §7.5, §10 | the first simulation pass, detached, resumable |
| `sim_results/` | — | CSV rows per replicate, `gain_calibration.json`, logs |

## Environment

```sh
uv venv --python 3.12 workspace_demo/t1_access/.venv
uv pip install --python workspace_demo/t1_access/.venv/bin/python -r workspace_demo/t1_access/requirements.txt
cd workspace_demo/t1_access
./.venv/bin/python verify.py            # ~3 min; must print ALL OK
./.venv/bin/python bench.py --layer     # the §14 numbers
nohup sh run_sims.sh > sim_results/logs/run_sims.log 2>&1 &      # 11 workers + the gain job
./.venv/bin/python simulate.py summary --out sim_results/calibration_D4.csv
```

Pinned versions are in `requirements.txt` (jax 0.11.1 CPU, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5,
joblib 1.6.0; Python 3.12.14, macOS Apple silicon). Each process is pinned to one XLA thread
(`models.py` sets `NPROC=1` before importing jax — the XLA CPU client sizes its Eigen pool from
that variable; the `XLA_FLAGS` thread flags do nothing in this jaxlib); parallelism is per dataset
through joblib, `NJOBS` workers of one core each — no more than the performance cores (12 on
this M4 Max): with 16 single-threaded workers one fit took 2.6x longer than alone.

## What the code decides that the text left open (all recorded as v1.2 amendments)

- **Optimiser.** Nelder–Mead is gone: every start is L-BFGS-B on the exact JAX gradient. The §14
  start count (100,800 per condition) is not computable with derivative-free fits.
- **Quadrature.** Plain prior-centred Gauss–Hermite does not converge at the CONF cluster size
  (168 trials per concept): 80 nodes still miss by 0.06–0.3 nat per concept (`verify.py` V3). The
  joint concept likelihood uses adaptive Gauss–Hermite (nodes centred on each concept's posterior mode
  with the Laplace scale, the mode found by eight unrolled damped Newton steps so that the gradient is
  exact); 10 nodes are accurate to 1e-8, 20 to 1e-12. The node rule keeps its form (< 1e-3 change).
- **Start generator.** Data moments of the training fold only; start 0 unjittered, starts 1–7 jittered
  by N(0, 0.25²) per coordinate in the optimiser's own parameter units (the raw vectors listed at the
  top of `models.py`); inherited members keep the inherited moment initialisation.
- **M3V floor.** sigma = floor + e^{s}, floor = 0.05 SD of the outer training fold (a smooth form of
  "floored at").
- **Synthetic generators.** Base parameters, the cross-layer AR(1) stand-in (rho 0.9) and the one-layer
  datasets of the first pass are declared in `simulate.py`'s docstring.
