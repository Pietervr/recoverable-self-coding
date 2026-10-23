# Does the human two-state preference survive trial-level latency and scale variation?

Design, revision 1 — 23 October 2026, session R052 Entropy SI. Status: DRAFT for Codex review. Nothing here has
been run. The decision rule in §6 is frozen by commit before any real-data contrast is computed.

## 1. The gap this closes

The Entropy SI paper (Unimog `papers/adaptive_agency_special_issue/`) has one strong completed result: the
published two-model comparison of Sergent et al. 2021, carried over unchanged to synthetic data, called two
states in 989 of 12,000 one-state datasets, every one at a setting where the generator carried item
heterogeneity (SI §r-audit). Variation across sampling units alone makes a single graded state look like two
to that test. The paper also reproduces the human result that motivates the whole programme (SI §r-human):
on 20 participants' EEG, the two-state model is preferred from 315 ms. That preference was obtained with the
same three fixed per-window models, which have no term for trial-to-trial variation. The paper names the
human-side form of this confound — latency jitter of a graded response (Truccolo et al. 2002) — in
`background.tex` and again in `discussion.tex`, and both times says it is not tested.

This study tests it. It refits the 20 participants with graded and two-state model families that both
permit trial-to-trial variation in latency and in scale, and asks whether the two-state preference survives
when the graded family is given the nuisance structure the audit showed it needs. Either answer is a
contribution; the reading of each is fixed in §6 before the data are touched.

## 2. Why the inherited per-window models cannot see jitter

Each of the 53 windows is fitted separately (`sergent_port/fit_models.py`), so each model describes the
marginal distribution of the decoder distance y at one window given the level k. If a graded response of
fixed shape arrives at a trial-specific latency, then at a window on its rising edge the trials split into
"arrived" and "not yet arrived": a bimodal marginal from one state. No per-window likelihood can
distinguish that from a two-state mixture, because the information that separates them — the same trial's
values at the neighbouring windows — is outside the per-window model. A trial-level latent latency shared
across windows is therefore required, and it can only be identified from the whole single-trial time course.

The derived data already carry that time course: `brain_data/sergent2021/derived/S{n}_{session}_preds.npz`
holds `preds` (n_trials × 1250 samples at 2 ms, −0.5 to 2.0 s), `snr` (level 1–6, 7 in ten passive sets),
`fold`, `trialinfo` (block in column 1). No re-decoding is needed; the port's decoder, 10 Hz low-pass and
block folds are reused unchanged so that the new comparison sits on the same readout as the inherited one.

## 3. Data and preprocessing (inherited, unchanged)

- Participants S1–S20, active session primary (the paper's human reference), passive session secondary.
- Decoder distance per trial and sample from `decode.py` (liblinear solver, the committed readout).
- 10 Hz zero-phase low-pass as in `fit_models.lowpass_filtfilt`.
- Time grid for the joint model: the port's 53 windows (`window_means`, centres −285 + 30 i ms) for the
  primary analysis, so that per-window and joint results are read on one grid. Sensitivity: the filtered
  preds subsampled every 10 ms over the same span (161 points), which resolves latency more finely.
- Folds: the port's five block folds (`block_folds`), training on blocks outside the fold (21st block
  always in training), scoring the held-out fold. Same trial exclusions as the port (passive S6 third trial).
- Fitting window: all 53 windows (primary). Sensitivity: windows with centres 255–705 ms, the span over which
  the inherited two-state preference is observed.

## 4. The model families

Notation: trial i with level k_i, window w ∈ {1..W}, observed vector y_i ∈ R^W. Levels are shifted by −1 as
in the port; level 1 is no sound. lg_{κ,x0}(k) is the logistic of the paper's §t-families.

Shared components, estimated per participant and fold on training trials only, identical across the models
compared within a participant:
- Baseline time course μ0(w): the mean of the level-1 (no-sound) training trials at each window.
- Response template T(t): a smooth non-negative function of post-stimulus time, free in shape, normalised
  to max 1, parameterised as a cubic B-spline with knots every 60 ms from 0 to 1300 ms (≈ 22 coefficients,
  softplus-positive). It is fitted inside each model (not shared across models), because a fixed template
  would favour whichever family it was estimated under. Evaluated at (t_w − τ_i) by the spline, so a
  continuous shift needs no resampling of the data.
- Residual covariance Σ (W × W): estimated from the training level-1 trials' deviations about μ0 with a
  Ledoit–Wolf shrinkage estimate, then held fixed for all models within that participant and fold. The
  low-pass filter alone makes neighbouring windows strongly correlated; an independent-windows likelihood
  would be wrong for every model and would reward whichever family happens to exploit the error. Σ is
  estimated where no signal is present, so it is a noise covariance; template misfit on signal trials
  enters the residual equally for both families.
- Trial-level nuisance distributions: latency τ_i ~ N(0, s_τ²) truncated to ±150 ms, marginalised on a
  grid of 31 equally spaced shifts with Gaussian weights; scale g_i ~ LogNormal(−s_g²/2, s_g²) (mean 1),
  marginalised by 7-point Gauss–Hermite quadrature. s_τ and s_g are free parameters of the model that
  carries them; a model without a nuisance term has it fixed at zero.

Graded family (one state; the response amplitude is a graded function of level):
    y_i | k_i, τ_i, g_i ~ N( μ0 + g_i · a(k_i) · T(· − τ_i),  Σ ),
    a(k) = L · [lg_{κ,x0}(k) − lg_{κ,x0}(1)],  so a(1) = 0.
  G0: τ ≡ 0, g ≡ 1 (no trial nuisance).  G1: τ free, g ≡ 1.  G2: τ ≡ 0, g free.  G3: both free.

Two-state family (each trial is in the low or the high state; the state probability is graded in level):
    z_i ~ Bernoulli(A(k_i)),  A(k) = lg_{κ,x0}(k), A(1) = 0 forced as in the inherited M3;
    y_i | z_i = 0 ~ N( μ0 + c,  Σ )                                  (low state: no response, free offset c)
    y_i | z_i = 1, τ_i, g_i ~ N( μ0 + g_i · m_H(k_i) · T(· − τ_i),  Σ ),
    m_H(k) = L_H · lg_{κ_H,x0}(k) + δ   (the inherited high-state mean, graded modestly in level).
  B0–B3 as for G0–G3, with τ and g applying to the high-state response.

The two families are nuisance-matched: B3 and G3 differ only in whether the response amplitude is one
graded quantity or a Bernoulli switch times a high-state amplitude. The graded family with g free can
produce heavy right tails (the audit's M2S mechanism); the two-state family must win on bimodality beyond
what a skewed scale distribution and a latency spread can imitate.

Why both families get τ and g. Ignition on the two-state account may also occur at a variable latency and
with a variable amplitude. A design that gave the nuisance terms only to the graded family would make the
two-state model lose for lack of flexibility, not for being wrong. Matching is what lets the contrast speak
to the question.

Parameter counts (excluding the spline): G0 3 (L, κ, x0), G3 5; B0 7 (κ, x0, c, L_H, κ_H, δ, plus the
spline), B3 9. Σ and μ0 are not counted; they are identical across models.

## 5. Fitting

- Maximum marginal likelihood with analytic gradients (JAX, CPU, `NPROC=1` per worker as in the T1 code),
  L-BFGS-B with the spline coefficients unconstrained through softplus, σ-type parameters through log.
- Starts: 4 per fit — one from the inherited per-window fits (amplitude/logistic parameters from the
  port's `fits_<session>.csv` at the 435–495 ms windows, template from the level-6 mean time course), three
  from perturbations of it at jitter 0.25 in parameter space with seeded streams. The best training
  likelihood is kept; the chain and every start's end point are archived. The port's lesson stands: most
  inherited Nelder–Mead fits stopped at their evaluation cap, so convergence is checked (gradient norm,
  Hessian condition on the free parameters) and recorded, never assumed.
- Score: the summed held-out log marginal likelihood of the fold's trials, averaged over the five folds as
  in equation (cvscore) of the paper, and divided by the number of scored trials to give nat per trial.
- Everything per fit is logged with the data identity, code hash and seeds (the T1 `dataset_identity`
  pattern), so a fit is never silently reused across a changed specification.

## 6. The decision, fixed before any real-data contrast

Primary contrast: B3 against G3 (nuisance-matched). Per participant s,
    Δ_s = [ S_{s,B3} − S_{s,G3} ] / n_scored,s     (nat per trial, held out).
Group statistic: the mean Δ̄ over the 20 participants with its 95% t-interval, the participant being the
sampling unit, as in the inherited group analysis and as the audit's "sampling unit" component requires.
The random-effects BMS protected exceedance probability of B3 over G3 is reported beside it as the
inherited descriptive convention, not as the decision.

Control contrast: B0 against G0 (joint time-course models with no trial nuisance). This checks that the
joint framing itself reproduces the inherited preference before any nuisance is added; if it does not, the
study cannot speak to the inherited result and the reading is "inconclusive — framing".

Readings (exactly one applies; the thresholds are those of the inherited result's own scale, 0.0025–0.003
nat per trial at the plateau windows):
- SURVIVES: lower bound of the B3−G3 interval > 0.
- DISAPPEARS: B0−G0 lower bound > 0 (the joint framing shows the inherited preference) and the B3−G3
  interval includes 0 or lies below it.
- INCONCLUSIVE — framing: B0−G0 interval includes 0 or lies below it.
- INCONCLUSIVE — power: B0−G0 lower bound > 0, B3−G3 lower bound ≤ 0, and the §7 power gate was not met
  at the observed effect size.
The reading is computed by a script committed before the real-data fits are run, and the four readings and
their consequences for the manuscript are written in §9 now.

Secondary (reported, not decided on): G1 vs G0 and G2 vs G0 (does each nuisance term earn its place on
held-out score?), B1/B2 vs B0, the fitted s_τ and s_g per participant with their recovery-corrected
uncertainty from §7, the passive session on the same rule, and the two sensitivity grids of §3.

## 7. Calibration and recovery before the real contrast

All on synthetic data generated from parameters fitted to each participant's training trials, with the
participant's own Σ and μ0, so that the synthetic sets have the real data's noise, correlation and trial
counts. R replicate sets per generator setting, each set 20 synthetic participants, the full §4–§6 pipeline
run on each set exactly as it will run on the real data.

(a) Recovery of the jitter and scale terms — the identifiability gate. Generator G3 at fitted values and at
    s_τ ∈ {0, 20, 40, 60, 80} ms with s_g at its fitted value. Gate: across synthetic participants, the
    Spearman correlation between true and estimated s_τ ≥ 0.7 and median relative bias within ±25% at
    s_τ ≥ 40 ms; estimated s_τ at the true 0 ms setting has a 90% quantile below 15 ms. If the gate fails,
    the jitter term is declared not identifiable at this readout's SNR, G2/B2 (scale only) become the
    primary matched pair, and the paper says so. This is the chance the owner has chosen to take.
(b) False two-state rate under graded generators — the mechanism and the calibration together. Generators
    G0 (no nuisance), G1 at s_τ ∈ {40, 80} ms, G2 at fitted s_g, G3 at fitted values. For each synthetic
    set, (i) the inherited per-window pipeline (`fit_models.py` + `model_comparison.py`, unchanged) and
    (ii) the §6 B3−G3 rule. Gate for (ii): at every graded generator, the SURVIVES reading in ≤ 5% of
    replicate sets. Result (i) is reported in the paper whatever it shows: it is the direct test of whether
    latency jitter alone makes the inherited analysis prefer two states on data of this form.
(c) Power under two-state generators. Generator B3 at fitted values and at half the fitted high-state
    amplitude. Gate: the SURVIVES reading in ≥ 80% of replicate sets at fitted values. The observed
    effect size at which power falls below 80% defines the "inconclusive — power" boundary of §6.
R = 50 replicate sets per setting (≈ 10 settings, ≈ 10,000 synthetic participant-datasets). The gates in
(a)–(c) are evaluated and committed before the real-data contrast is computed; a failed gate stops the
real-data step and is reported as such.

## 8. Compute, venue, cost

- Development and the real-data fits on the Mac (free): 20 participants × 2 sessions × 8 models × 5 folds
  × 4 starts = 6,400 fits. Target ≤ 30 s per fit with gradients → ≈ 53 core-hours, under 5 h on 12 cores.
- The §7 battery on AWS (owner, 23 Oct: "we can run in aws"): ≈ 10,000 synthetic participant-datasets ×
  160 fits × 30 s ≈ 13,000 core-hours ≈ 140 instance-hours on a 96-vCPU c7a.24xlarge; at the on-demand
  rate seen in October (≈ USD 5.3/h) ≈ USD 740, on spot (≈ USD 1.7/h, interruption-prone in eu-north-1)
  ≈ USD 240. These are projections from a target fit time, not measurements. Before any launch: benchmark
  one participant's full §4 fit set on the Mac and on the target instance, cost the battery from the
  measured rate, add the ledger row's cost cap and stop rule (Unimog `rsc_t1_simulation_design.md` §12,
  row 24), confirm the remaining headroom under the USD 3,000 AWS cap from the R052 spend trail, and get
  the owner's go on the number. If the measured cost exceeds USD 400, R drops to 25 and the s_τ grid in
  (a) to {0, 40, 80} ms before anything else is cut.
- Stop rules: the first replicate set whose pipeline fails for a non-numerical reason (missing file, hash
  mismatch, duplicate result) stops the battery; numerical non-convergence is recorded per fit and the set
  is kept with its convergence flags.

## 9. What each outcome does to the paper (written now)

- SURVIVES. The human two-state preference is robust to trial-level latency and scale variation of the
  kinds that make the transferred test fail on synthetic data. Contribution 1 (the inherited test's false
  calls) is then bounded: the published human result does not rest on that artefact. Enters the SI as a
  new results subsection and one sentence in the abstract; the Introduction's claims paragraph gains a
  fourth claim.
- DISAPPEARS. The published preference is attributable to unmodelled trial variability, and §7(b)(i) shows
  on realistic synthetic data whether jitter alone produces it in the inherited analysis. This is the
  larger claim; it is stated as a property of the published statistical comparison under this readout,
  not as a finding about the physiology, and the leakage limits of the inherited design (SI §d-limits)
  still apply to it. Enters the SI as the lead result; the title's "Partial EEG Reproduction" clause
  changes to name it.
- INCONCLUSIVE — framing. Reported in the supplement with the B0−G0 result; the joint-model approach is
  recorded as not reproducing the per-window preference and the reason examined (grid, Σ, template).
- INCONCLUSIVE — power, or the (a) gate fails. Reported as a limitation with the measured power curve or
  the measured non-identifiability of s_τ; G2/B2 reported as the matched contrast actually available.
In every case the paper reports §7(b)(i), the recovery result of §7(a), and the fitted s_τ and s_g.

## 10. What this study does not do

It does not change the decoder, the folds, the windows or the inherited per-window models, so the SI's
reproduction result stands as reported. It does not quantify the leakage of the inherited design. It tests
one family of trial-level variation (latency shift of a fixed-shape template, lognormal scale); shape
variation across trials, multiple components with independent latencies and non-Gaussian residuals are
outside it and are named as such. It makes no claim about the language model and none about experience.

## 11. Files

- This design: `workspace_demo/sergent_port/jitter/DESIGN_jitter.md`.
- Code (to be written after review): `workspace_demo/sergent_port/jitter/{models.py, fit.py, simulate.py,
  decide.py}`; results under `workspace_demo/sergent_port/jitter/results/`; Codex reviews under
  `workspace_demo/sergent_port/jitter/reviews/`.
- Inherited code read for this design: `sergent_port/fit_models.py` (likelihoods lines 60–100, Nelder–Mead
  102–110, `window_means` 138–143, `block_folds` 118), `model_comparison.py`, `bms.py`, `README.md`.
- Paper sections: Unimog `papers/adaptive_agency_special_issue/sections/{introduction,methods,results,
  background,discussion}.tex`; the relevant audit result `results.tex` §r-audit and §r-unit.
- Literature to settle before the methods text: Truccolo et al. 2002 (already cited); single-trial latency
  methods (Woody 1967; RIDE, Ouyang et al. 2011/2015); the growth-mixture precedent for spurious classes
  under non-normality (Bauer & Curran 2003, Psychological Methods 8:338); Sergent et al. 2021's own
  treatment of latency variability (local `brain_data/sergent2021/sergent2021_SI.pdf`, to be read).
