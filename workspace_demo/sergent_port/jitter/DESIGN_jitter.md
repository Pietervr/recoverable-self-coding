# Does the human two-state preference survive trial-level latency and scale variation?

Design, revision 3 — 24 October 2026, session R052 Entropy SI. Status: DRAFT for Codex re-review.
Rev 1 (RSC 960e93b) and rev 2 (57c1280) received NOT FAVOURABLE (`reviews/2026-10-23_design_codex_review.md`,
`reviews/2026-10-23_design_v2_codex_review.md`). Rev 2's shared mean construction, late-span target and sign
partition stand; rev 3 repairs the template identifiability on the restricted span, defines the full-span generator,
calibrates the upper-bound decision, accounts for unavailable fits, replaces the mechanism controls, and completes
the recovery, attribution and implementation contracts. Nothing has been run.

## 0. Stages and what is frozen when (answers review §6, freeze sequence)

S1 Provisional implementation; per-participant GENERATOR fits (§7.1) on full data, whole epoch. Their parameter
   values may be inspected; no cross-validated contrast is computed on real data at this stage.
S2 Development on development seeds (W2, T1, O1 at R = 25) and numerical repairs; the §4 quadrature/support checks.
S3 FREEZE by commit: code, `decide.py` with branch tests, generator algorithms, the manifest, the ε algorithm.
S4 Independent final validation on fresh seeds; the ε value estimated and committed.
S5 Real-data cross-validated fits and the final contrast. The real contrast is never inspected before S5.

## 1. The gap this closes

The SI's one strong completed result: the published two-model comparison of Sergent et al. 2021, carried over
unchanged to synthetic data, called two states in 989 of 12,000 one-state datasets, all at settings whose generator
carried item heterogeneity (SI §r-audit). The paper also reproduces the human result that motivates the programme
(§r-human): the two-state model preferred from 315 ms on 20 participants, with the same per-window models, which
have no term for trial-to-trial variation. `background.tex` and `discussion.tex` name the human-side form of the
confound (latency jitter of a graded response, Truccolo et al. 2002) and say it is not tested. The 989 false calls
concern a different sampling unit, fitting scheme and decision rule from the human analysis; this study is the
bridge from that caution to the human reference. It refits the 20 participants with a graded and a two-state family
matched in attainable level means and in every nuisance term, and asks whether the two-state preference survives.
The answer is a bounded statement about the published statistical comparison under this readout; §9 fixes what
each outcome licenses.

## 2. Why per-window models cannot see jitter, and what can

Each of the 53 windows is fitted separately (`sergent_port/fit_models.py`), so every model describes the marginal
distribution of the decoder distance at one window given the level. A graded response of fixed shape at a
trial-specific latency splits the trials at a rising-edge window into "arrived" and "not yet": a bimodal marginal
from one state. The information separating that from a true mixture is the same trial's values at the neighbouring
windows, outside every per-window likelihood. A trial-level latent latency shared across windows is needed. The
derived files carry the time course: `brain_data/sergent2021/derived/S{n}_{session}_preds.npz`, `preds` n_trials ×
1250 samples at 2 ms (S10 active: 930 × 1250; levels 1–6 with 152/158/157/156/155/152 trials; blocks 1–20 in
`trialinfo[:,0]`; the stored `fold` is the decoder fold, not the likelihood block fold). No re-decoding.

Readout-level interpretation, declared. The decoder is a different linear map at every sample, so a shift of the
projected trace, `beta(t)·x(t−τ)`, is not a shifted neural source, `beta(t−τ)·x(t−τ)`. A fitted latency here is a
property of the decoder-distance time course. The adversarial generators of §7 include shape variation for that
reason; a fixed-spatial-decoder re-analysis is follow-on work (§10).

## 3. Data, preprocessing and spans (inherited, unchanged)

- Participants S1–S20; active session primary; passive deferred.
- Decoder distance per trial and sample from `decode.py` (liblinear); 10 Hz zero-phase low-pass
  (`fit_models.lowpass_filtfilt`); the port's 53 window means (`window_means`: 16 samples each, centres −285 + 30 i
  ms, sample times from −300 to 1290 ms). Levels shifted by −1 in all models; the catch level is **0**.
- Folds: the port's five block folds (`block_folds`); block 21 always in training, never scored.
- PRIMARY SPAN: the 16 windows with centres 255–705 ms (sample times 240–720 ms). Rationale, declared: it is the
  article's stated span ("most of the period between 250 and 700 ms"), chosen after the published and reproduced
  curves were known and before this new contrast; the source curve's first 0.95 crossing is 315 ms and both curves
  return to graded-highest at 675 ms, so not every window in the span is an established two-state window. The
  whole-epoch alternative would ask a two-state low state fixed at catch to carry early sound processing present on
  every trial, a framing bias against B rather than a state-count test; the late restriction applies identically to
  both likelihoods and adds no B-only term, discards early timing information, and the first window (240–270 ms)
  is not a sharp stage boundary after the filter. The conclusion is about a catch-anchored late-response family.
- WHOLE-EPOCH SPAN (53 windows): the generator span (§7.1) and a sensitivity of the contrast.

## 4. The model families (answers review §§1–2, 6)

Notation: trial i, level k_i ∈ {0..5}, window w in the span, observed y_i ∈ R^W (W = 16 primary, 53 whole epoch).
Everything below is identical in both families unless the line says otherwise.

Shared construction, estimated per participant and fold on training trials only:
- Baseline μ0(w): mean of training catch trials. Both families predict exactly μ0 on a no-response trial.
- Residual covariance Σ (W × W): Ledoit–Wolf shrinkage on training catch deviations about μ0, fixed for all models
  in that participant and fold. Reported before the contrast is read: held-out catch whitening diagnostics,
  level-stratified training residual second moments under each fitted model, and the common-covariance sensitivity
  D·R(ρ)·D (D = per-window training catch residual SDs; R(ρ) AR(1) with ρ ∈ [0, 0.999] fitted by ML on the same
  training catch residuals; one matrix for both families). Σ has no model-independent direction of bias; it is
  challenged by O5 (§7) rather than argued.
- Level amplitudes: a(k) = softplus(α_k) > 0 for k = 1..5, a(0) = 0 fixed. Closure declared: softplus attains no
  exact zero; the catch is anchored at zero by construction, not by estimation. Both families carry exactly these
  five parameters; the inherited logistic-in-level mean laws are a declared sensitivity.
- Template T. Basis: cubic B-spline, open-clamped (knots of multiplicity 4 at both ends), interior knots every 60 ms
  over the template support. Support = the span's sample-time range extended by the latency truncation: primary
  [90, 870] ms (13 intervals, 16 basis functions), whole epoch [−450, 1440] ms. Coefficients c_j = softplus(γ_j) > 0,
  with one gauge coefficient fixed, γ_ref = 0, for the basis function whose support is centred nearest 480 ms (the
  middle of the primary span). The template entering the model is the normalised
    T̃(t) = T(t) / m_vis(T),   m_vis(T) = mean of T over the span's window sample times at τ = 0,
  so that a(k) is the mean response over the span at zero shift, in decoder units. Identifiability: scaling every
  coefficient leaves T̃ unchanged and is removed by the fixed gauge; moving mass from basis functions visible at
  τ = 0 to those visible only under shift (the first two and last two of the primary basis, supports [90,150],
  [90,210], [750,870], [810,870]) changes m_vis and therefore every prediction, so the rev 2 degeneracy is gone.
  The four shift-only coefficients enter the likelihood only through τ ≠ 0 nodes: in models with s_τ = 0 (G0, G2,
  B0, B2) they are not parameters at all (dropped from the vector, T̃ evaluated only on the visible support); in
  models with s_τ free they are identified only to the extent the latency distribution makes them visible, their
  profiles are reported, and the Hessian condition is checked on the parameters that enter. Rank is checked
  numerically at s_τ = 0, at the smallest nonzero node spacing and at the ±250 ms support sensitivity before S3.
  A window's value is the mean of T̃ over that window's 16 sample times (`fit_models.py:138`), not a centre value.
  T is the filtered response; no second filter. T is fitted separately inside each model with identical basis,
  support, constraints and training-only initialisation; fitted shapes are plotted per participant, and a common
  independently estimated template is run as a diagnostic if the contrast depends on them.
- Trial latency τ_i ~ N(0, s_τ²) truncated to ±150 ms, marginalised on 31 equally spaced nodes (10 ms) with
  truncated-normal weights normalised to one; s_τ ∈ [0, 150] ms a box parameter; s_τ = 0 is exact (one node). Parent
  and realised SD both reported (parent 80 → truncated 68.1 ms, 31-node 69.3 ms). Node check before S3: 31 vs 61
  nodes must change every development participant's score contrast by less than one tenth of the contrast's
  interval half-width, else 61 is adopted and re-checked against 121. The ±250 ms support is a different latent
  model, run as a declared sensitivity with its own template support, not as an integration check.
- Trial scale g_i ~ LogNormal(−s_g²/2, s_g²), mean 1; s_g ∈ [0, 1.5] box, s_g = 0 exact; Gauss–Hermite with 7 nodes
  checked against 15 at s_g = 1.5 under the same tolerance (15 adopted and checked against 31 if it fails). Fits
  at the s_g bound are flagged; a wider-bound (s_g ≤ 2.5, re-checked quadrature) sensitivity is run if any flagged
  fit is in a participant whose Δ_s drives the result. g and τ independent, level-invariant, one shape shifted as a
  whole: shared restrictions, challenged by O3/O4.

Graded family: y_i | k_i, τ_i, g_i ~ N( μ0 + g_i · a(k_i) · T̃(· − τ_i), Σ ).   G0: s_τ = s_g = 0. G1: s_τ free. G2:
s_g free. G3: both.
Two-state family: z_i ~ Bernoulli(A(k_i)), A(k) = max(A_min, lg_{κ,x0}(k)) for k ≥ 1, κ > 0 (log-parameterised),
A(0) = 0, A_min = 0.02.   y | z = 0 ~ N(μ0, Σ);   y | z = 1, τ, g ~ N( μ0 + g · m_H(k) · T̃(· − τ), Σ ),
m_H(k) = a(k)/A(k).   B0–B3 as G0–G3, nuisance on the high branch.

Declared second-moment consequence (review §1). With b = E[T̃_τ], H = E[T̃_τ T̃_τᵀ], r = exp(s_g²): both families
have mean a·b; Cov_G = Σ + a²(rH − bbᵀ), Cov_B = Σ + a²(rH/A − bbᵀ). The occupancy parameters are therefore also a
level-dependent variance law along the template (at A = 0.02 up to 49a² before scale; at s_g = 1.5 the graded
bound is 8.49a²). This is the two-state hypothesis' own flexibility, declared: a B win may reflect variance/tail
modelling without visibly resolved modes, and with s_g > 0 B's amplitude law is a point mass at zero plus a
lognormal high branch, not a two-point law. The floor A_min bounds m_H/a at 50 and is a numerical restriction with
zero occupancy derivative in clipped regions; per fit the clipped levels are archived, occupancy/high-amplitude
profiles are reported, and a floor sensitivity {0.01, 0.02, 0.05} is run on the real comparison and on the T2
development case. Catch anchoring A(0) = a(0) = 0 is a common restriction; the free-catch sensitivity frees a(0) in
G and A(0) in B with m_H(0) = a(0)/A(0), and makes μ0 a free W-vector parameter common to both families (the catch
mean would otherwise absorb the freed signal).

Parameter counts, non-template: G0 5, G3 7, B0 7, B3 9. Template: 15 free coefficients on the primary support in
models with s_τ free, 11 in models with s_τ = 0. No information criterion is added to a cross-validated score.

## 5. Fitting (answers review §6, `fit.py`)

- Maximum marginal likelihood, float64, JAX gradients, L-BFGS-B on the box above with parameter scaling (times in
  ms/100, amplitudes in decoder units, logits unit). Σ is Cholesky-whitened once per fold; for each τ node the
  whitened template v_τ = Σ^{-1/2} T̃_τ is recomputed when template parameters change; for whitened data u_i,
    q(i, τ, g) = ‖u_i‖² − 2 g m(k_i) (u_i · v_τ) + (g m(k_i))² ‖v_τ‖²,   m = a (graded) or m_H = a/A (two-state high
  branch), all trial–template projections as one matrix product; the two-state low branch is the m = 0 term and the
  two branches combine by log-sum-exp with the occupancy weights. No residual tensor over nodes is formed.
- Starts (4), from the fold's training blocks only: level amplitudes from training level means over the span
  (clipped below at 0.05 decoder units); template coefficients from a non-negative least-squares fit of the basis to
  the training level-5 mean time course, floored at 1e-3 before the log; κ, x0 from a logistic regression of the
  per-trial indicator "mean over the span above the training catch 90th percentile" on level; nuisance starts
  (s_τ, s_g) ∈ {(0, 0), (40, 0), (0, 0.4), (40, 0.4)} ms, components fixed at zero in models that lack them.
  Development adds a near-collapsed two-state start (A → 1 at all levels) and reports whether any start beyond the
  first changed the selected optimum.
- Acceptance: a fit is CONVERGED when all of (i) projected-gradient infinity norm ≤ 1e-5 in scaled units, (ii)
  relative objective change over the last 5 iterations ≤ 1e-9, (iii) finite objective and parameters. Iteration
  cap 2,000; two retries from re-seeded perturbed starts on failure. A model whose four starts leave no CONVERGED
  fit is UNAVAILABLE for that participant and fold. The best CONVERGED objective is selected; every start's end
  point and status is archived.
- Score: every out-of-fold trial's log marginal density summed once over the five folds, divided once by the total
  number of scored trials (block 21 excluded): S_{s,m}, nat per trial. The inherited fold-mean convention
  (`fit_models.py:254`) is reported for continuity only.
- Correctness: the whitened objective and gradient are checked against a direct dense implementation to 1e-10
  relative on small cases; quadrature, node, support and rank checks of §4 archived before S3.
- Logging: data identity, code hash, seeds, bounds hit, clipped levels, retries, start statuses, per fit.

## 6. The decision (answers review §3)

Primary estimand: the mean over available participants of the paired per-trial held-out advantage on the primary
span, Δ_s = S_{s,B3} − S_{s,G3}, with its 95% t-interval (n_avail − 1 degrees of freedom; participant as unit).
The inherited BMS protected exceedance probability is reported beside it as a descriptive convention.

VALIDITY (all three required for a licensed primary result; the RECOVERY flag is explicitly NOT part of it):
  V1 calibration: the final-validation pass conditions (b), (c) and (e) of §7 met;
  V2 numerical completion: at every final-validation setting, UNAVAILABLE primary (set-level) outcomes ≤ 10% of
     attempted sets, and on the real data ≥ 16 of 20 participants with CONVERGED B3 and G3;
  V3 nothing non-finite in the primary interval.
If VALIDITY fails the primary result is NOT LICENSED; descriptive summaries, recovery and mechanism results are
still reported.
Given VALIDITY, `decide.py` computes ALL of the following fields (none ends the evaluation of the others):
  PRIMARY SIGN: POSITIVE (lower bound > 0), NEGATIVE (upper bound < 0), UNRESOLVED (otherwise; a bound exactly 0 is
    UNRESOLVED). UNRESOLVED is not evidence of absence.
  ATTENUATION: D_s = Δ_s(B0 − G0) − Δ_s(B3 − G3) over the participants with all four of G0, B0, G3, B3 available
    (the intersection roster, never a difference of means over different rosters; needs ≥ 16); POSITIVE / NEGATIVE
    / UNRESOLVED / UNAVAILABLE.
  UPPER BOUND (not equivalence): with ε from §7.4, BOUNDED (upper endpoint of the two-sided 95% interval < ε) or
    NOT BOUNDED; UNAVAILABLE if ε is unavailable. POSITIVE and BOUNDED may coexist and are both reported.
  BRIDGE: (i) the unchanged inherited per-window result stands; (ii) held-out per-window marginal predictions of G0
    and B0 beside it; (iii) joint B0 − G0 on the primary span: POSITIVE / NEGATIVE / UNRESOLVED / UNAVAILABLE.
  RECOVERY ADEQUATE (simulation; §7.5) and JITTER DETECTED (real data; §7.5), each per family.
  ATTRIBUTION (secondary): G3 − G2 and B3 − B2 (incremental latency after scale), G2 − G0, B2 − B0, G3 − G0, B3 − B0;
    fitted s_τ, s_g per participant with the §7.5 intervals.
Branch tests committed at S3 cover at least: failed recovery with valid prediction; B0/G0 missing with B3/G3
available; ε nonpositive or unavailable; a positive but sub-ε advantage; a failed calibration setting; a setting
over the UNAVAILABLE limit; non-finite fits; exactly-zero bounds; a roster of 15.

## 7. Generators, calibration, recovery (answers review §§4–6)

### 7.1 Generator fits (stage S1)
Per real participant, two GENERATOR fits on full data (all blocks, no cross-validation), whole-epoch span, with the
whole-epoch template support, μ0 and the 53 × 53 Ledoit–Wolf Σ from all catch trials: a G3 fit and a B3 fit. These
supply every synthetic participant's configuration (a, T̃, κ, x0, s_τ, s_g, μ0, Σ) in 53 dimensions, so synthetic
data are generated as 53-window vectors and can be scored on the primary 16 windows, the whole epoch, and by the
inherited per-window pipeline alike. Generator fits are separate from, and never substitute for, the S5
cross-validated scoring fits. The primary-span fits supply no generator quantity.

### 7.2 Generation
A synthetic participant has one coherent generating distribution across all five folds, with its base participant's
level counts and block labels (labels preserve counts and fold membership only, not stochastic block dependence —
declared limitation). For decision calibration each replicate set draws 20 base configurations with replacement
from the 20 (population generator, conditional on that finite empirical distribution). Within each synthetic
training fold μ0, Σ, shrinkage, starts and templates are re-estimated by the fitter exactly as on real data.
Mechanism settings (W1, W3, W4) use the base configuration's a, T̃, μ0, Σ unchanged and set only (s_τ, s_g).

### 7.3 Final-validation manifest (fits G0, B0, G3, B3; 5 folds × 4 starts = 80 fits per participant-dataset)
  Graded, well-specified: W1 (s_τ, s_g) = (0, 0); W2 fitted G3; W3 (80 ms, 0); W4 (0, 1.0).      R = 100 each.
  Graded, out of family (zero latency jitter unless stated; s_g at the fitted G3 value unless stated):
    O1 per-trial time stretch about 240 ms, t' = 240 + (t − 240)·exp(ζ_i), ζ ~ N(0, 0.25²), amplitude unchanged;
    O2 two components: T̃ split at 450 ms by a logistic ramp of slope 1/30 ms into T_a (early) and T_b (late),
       per-trial weight w_i ~ Beta(2, 2), response a(k)[2 w_i T_a + 2(1 − w_i) T_b] (mean a(k) T̃);
    O3 level-dependent latency, s_τ by level k = 1..5 = {60, 60, 40, 20, 20} ms;
    O4 (log g, τ) bivariate normal, correlation −0.5 before truncation, s_τ = 60 ms, g rescaled to mean one;
    O5 covariance challenge: G3 generator means plus whole-trial residual vectors resampled with replacement within
       level from the base participant's real residuals about the G3 generator fit. Declared: these residuals may
       retain unknown structure, so O5 is a covariance challenge, not a known-truth noise generator.    R = 100 each.
  Two-state: T1 fitted B3; T2 B3 with s_τ = 80 ms and occupancy A(k)/2 at every level (m_H recomputed so level
    means are unchanged; values below 0.02 are generated as is and recorded — halving leaves the logistic family,
    declared); T3 weak alternative on the §7.4 path at expected advantage 2ε.          T1, T2: R = 50; T3: R = 50.
  E1 ε-boundary alternative on the §7.4 path at expected advantage ε.                                   R = 100.
Count: 9 × 100 + 3 × 50 + 100 = 1,150 sets, 23,000 participant-datasets, 1.84 M start-level optimisations.
Pass conditions (pointwise for the frozen settings; exact one-sided 95% Clopper–Pearson; all-pass is an
intersection requirement, no multiplicity adjustment claimed):
  (b) false POSITIVE under every graded setting W1–W4, O1–O5: ≤ 1 of 100 attempted sets (upper bound 4.66%),
      counting an UNAVAILABLE set-level primary as POSITIVE;
  (c) power at T1: ≥ 45 of 50 sets POSITIVE (lower bound 80.1%), counting UNAVAILABLE as non-detection; T2 and T3
      reported (detection, false NEGATIVE, interval coverage of the procedure reference);
  (e) upper-bound error at E1: BOUNDED in ≤ 5 of 100 sets (nominal 2.5%; upper bound 9.9%), counting UNAVAILABLE
      as BOUNDED; coverage of the procedure-level reference reported at E1, W2 and O1 with the MC uncertainty of
      the reference stated;
  completion (V2): UNAVAILABLE set-level primaries ≤ 10% at every setting, every attempted set in the denominator.
Any reduction of the frozen manifest triggers fresh-seed re-validation of the retained settings.

### 7.4 The margin ε and the alternative path
ε estimand: the procedure-level expected per-trial advantage of B0 over G0 on the primary span when data are
generated from each participant's fitted B0 generator (a B0 fit on full data, whole epoch, as in §7.1) and scored by
the finite-training cross-validated procedure. Estimate: R_ε = 50 independent sets of 20 resampled configurations,
G0 and B0 scoring fits only; the benchmark is the mean over sets of the group mean Δ(B0 − G0), with its MC standard
error; ε = benchmark / 3. If the benchmark's 95% lower MC bound ≤ 0, ε is UNAVAILABLE and no upper-bound claim is
made. The ε algorithm is frozen at S3, its value at S4.
Alternative path for T3 and E1: from the fitted B3 configuration, scale a(k) by λ ∈ (0, 1] at every level
(m_H follows; occupancy unchanged). Pilot at λ ∈ {1, 0.75, 0.5, 0.35, 0.25}, R = 20, procedure-level expected
advantage with MC SE; the target λ is interpolated and validated at R = 100 (E1) or 50 (T3); if the attained
advantage differs from the target by more than its MC SE the setting is re-run once at the corrected λ, else the
target is declared UNREACHABLE and the (e) gate is reported as not evaluable (VALIDITY then fails on V1).

### 7.5 Recovery battery and the jitter flags
Fixed roster: the 20 real participants' G3 and B3 generator configurations (not resampled). Settings per family:
(s_τ, s_g) ∈ {0, 40, 80} ms × {0, fitted, 1.0}; plus O1 and O2 at zero jitter. R = 25 independent datasets per
configuration × setting; fits of all eight models on FULL synthetic data (all blocks; the same fit size as the real
reported estimates), one fit per model per dataset.
Statistics per configuration, setting, family: median relative bias of ŝ_τ over the 25 replicates; RMSE =
sqrt(mean(ŝ_τ − s_τ)²); boundary-hit frequency; profile-interval coverage. Strata: high-response if the
configuration's a(5) is at or above the median of the 20, else weak-response.
RECOVERY ADEQUATE (per family F ∈ {G, B}), all required: at s_τ = 40 ms and at 80 ms with fitted s_g, the SAME ≥ 15
of 20 configurations have median relative bias within ±25% and RMSE ≤ 50% of the true s_τ, in the model of family F
with both nuisance terms; replicate-level false-jitter frequency (ŝ_τ > 20 ms) ≤ 10% with its 95% upper bound ≤ 15%
over the 500 estimates of each zero-jitter setting {(0, 0), (0, fitted), (0, 1.0), O1, O2} for that family.
Otherwise NOT ADEQUATE; the paper reports measured non-identifiability.
Intervals: profile marginal likelihood over s_τ (re-optimising all other parameters) on the full-data fit; the
critical value for the boundary s_τ = 0 is the 95th percentile of the profile likelihood-ratio statistic simulated
under the matching zero-jitter generator (not χ²); away from the boundary χ²₁(0.95) is used and its coverage is
checked in the battery. "Recovery-corrected" estimate = ŝ_τ minus the setting's median bias, with the replicate
RMSE as its uncertainty.
JITTER DETECTED (real data, per family): the real full-data profile interval's lower bound exceeds 20 ms in ≥ 10 of
20 participants in that family's full model, and the group G3 − G2 (or B3 − B2) advantage interval is POSITIVE.
Neither flag alone unlocks the attribution sentence of §9.
Individual τ_i posterior means are checked against truth on high-level synthetic trials and reported as secondary.

### 7.6 Inherited-pipeline mechanism test (b)(i)
On the 53-window synthetic sets of W1–W4, O1–O5, T1: the unchanged per-window likelihoods and `model_comparison.py`
applied after `window_means`. Reported: the paper's three summaries (first window with pxp₃ > 0.95; first run of ≥ 3
consecutive windows with M3 the highest pxp, ties counting as not highest, "no run" if none; the strict MATLAB
Simes set), the full pxp curve and the per-participant per-window score advantage. The binary "call" is the ≥ 3-window
run with its first window inside the primary span. W1 vs W3 isolates latency, W1 vs W4 scale, W2 joint variation,
from a common configuration. The Simes-on-pxp convention has no established error control and is reported as the
inherited convention.

### 7.7 Numerical validity
Every attempted dataset and set counted. UNAVAILABLE per §5; a set with any UNAVAILABLE primary fit in more than 4
of its 20 participants has an UNAVAILABLE set-level primary (the same available-case rule as the real data).
Optimisation and quadrature error shown small relative to the contrast on development data before S4 seeds are
drawn. Development seeds never reused.

## 8. Compute, venue, cost (answers review §4)

- Real data, Mac (free): primary and whole-epoch CV fits, 20 × 8 models × 5 folds × 4 starts × 2 spans = 6,400
  fits; generator and full-data fits ≈ 400; ≈ 60 core-h at the 30 s target.
- Final validation, AWS (owner 23 Oct: "we can run in aws"), all at the UNMEASURED 30 s/start target:
  decision manifest 23,000 datasets × 80 = 1.84 M starts ≈ 15,300 core-h; ε benchmark 1,000 datasets × 40 ≈ 330;
  alternative-path pilots ≈ 5 × 20 × 20 × 80 × 30 s ≈ 1,330; recovery (18 + 2) settings × 25 × 20 × 8 models × 4
  starts = 320,000 starts ≈ 2,670; inherited pipeline on 19,000 datasets: 53 × 3 × 5 = 795 Nelder–Mead runs each,
  15.1 M runs; the port README's measured rate (≈ 0.3 core-min per participant for these 795 fits, ≈ 0.14 s per
  run) gives ≈ 600 core-h, to be re-measured. Total ≈ 20,200 core-h. On c7a.24xlarge (96 vCPU, one per physical
  core) at the October spot rate ≈ USD 1.7/h: ≈ USD 360 at perfect utilisation, ≈ USD 640 at 70% utilisation with a
  25% retry reserve; on-demand (≈ USD 5.3/h) ≈ USD 1,100–2,000. Projections at assumed rates, not quotes.
- Before launch: benchmark one participant's full §4 set, the inherited pipeline, a generator fit, a profile and
  an interval construction on the Mac and on the target instance (steady-state value + gradient to convergence from
  all starts; completed-dataset throughput at 96-way concurrency; compile time separately), cost the frozen
  manifest from measured rates, set the ledger row cap (Unimog `rsc_t1_simulation_design.md` §12 row 24), confirm
  headroom under the USD 3,000 AWS cap from the R052 spend trail, and put the number to the owner. The owner's
  decision on the cap is taken at the measured number; the ledger row currently carries USD 400 as a placeholder
  that this manifest will not meet at 70% utilisation.
- Declared reduction order if the measured cost exceeds the approved cap: (1) starts 4 → 3 in validation replicates
  only if development shows the fourth start never changed the selected optimum; (2) merge O3 and O4 into one
  coupled generator; (3) drop T2 to development-only; (4) recovery R 25 → 15 with the pass thresholds unchanged and
  their reduced precision stated. Never: R below 100 at graded settings or at E1, removal of O1/O2/O5, coarser
  quadrature than the §4 checks licensed. Any reduction re-validates on fresh seeds. If the cap still cannot be
  met, the licence narrows or the study stops.
- Checkpoint per completed dataset for spot retries; one BLAS/XLA thread per worker; JIT with cached shapes.

## 9. What each outcome licenses in the paper (answers review §3)

The study replaces the "untested jitter" limitation with a bounded answer; it is the SI's one central empirical
addition. Conditional on VALIDITY:
- PRIMARY POSITIVE: "In this auditory dataset, over 255–705 ms, the two-state family retained a positive held-out
  advantage over the matched graded family after both represented trial-level latency and scale variation
  (interval; recovery status; misspecifications tested)." Not: that the published result rests on no artefact, nor
  that every graded account fails. If RECOVERY is NOT ADEQUATE or JITTER not DETECTED, robustness is to a scale term
  and to a latency term the data did not pin down, and the text says so.
- "Not robust to representing trial variability" requires BRIDGE (iii) POSITIVE and ATTENUATION POSITIVE, with the
  residual advantage reported as NEGATIVE, UNRESOLVED or BOUNDED. A NEGATIVE primary with BRIDGE (iii) not POSITIVE
  is reported as "the joint framing favours the graded family", a framing result, not attenuation.
- Attribution to latency ("the attenuation is carried by latency variation") requires all of: RECOVERY ADEQUATE in
  the generating family, JITTER DETECTED, ATTRIBUTION G3 − G2 (and B3 − B2 where B is the reference) POSITIVE, and
  the W3-vs-W1 mechanism result showing the inherited call rate rises with latency alone. Short of that, attribution
  is to trial variability of unidentified form, or to the scale term if G2 − G0 carries it.
- Any statement that graded simulations reproduced features of the inherited preference is made only if §7.6 shows
  it, with the setting named.
- If the tested latency settings do not reproduce the late plateau in §7.6, the paper says "these tested jitter
  distributions did not reproduce it", not that the plateau is not a rising-edge artefact.
- UNRESOLVED without BOUNDED: reported with the interval, D, the T3/E1 detection and error rates, and the flags; not
  evidence of absence, not a survival.
- NOT LICENSED: descriptive summaries, recovery and mechanism results; no primary claim.

Hostile reading anticipated: a better mean law (shared level means); variance/tail flexibility read as modes (the
declared second-moment law and the profiles); noise or shape variability mislabelled as latency (zero-jitter O1/O2
false-jitter gate, JITTER DETECTED on real profiles, the readout-level declaration); a whole-epoch question
substituted (primary span, with its rationale declared as post-publication, pre-contrast); absence from
non-significance (the partition, D, ε as an upper-bound claim); a battery from the fitted families only (O1–O5);
decoder leakage (declared, unchanged); novelty (cited; no "first" claim).

## 10. What this study does not do

It changes none of the decoder, folds, windows or inherited per-window models; the SI's reproduction stands. It does
not quantify the inherited design's leakage, and the decoder and likelihood folds remain non-nested on the saved
preds. It tests one nuisance family (latency shift of one template, lognormal scale, independent, level-invariant)
and challenges it with O1–O5; multi-component latencies, non-Gaussian residuals and a fixed-spatial-decoder
re-analysis are follow-on work. The passive session, the whole-epoch contrast, ±250 ms support, the inherited mean
laws, the free catch, the D·R(ρ)·D covariance, the A_min floor and the wider s_g bound are sensitivities, each
declared above. No claim about the language model and none about experience.

## 11. Files and literature

- This design: `workspace_demo/sergent_port/jitter/DESIGN_jitter.md` (rev 3; rev 1 960e93b, rev 2 57c1280).
- Codex reviews: `jitter/reviews/2026-10-23_design_codex_review.md`, `2026-10-23_design_v2_codex_review.md`.
- Code (after review): `jitter/{models.py, fit.py, simulate.py, decide.py, bench.py}` with tests; results under
  `jitter/results/`.
- Inherited code: `sergent_port/fit_models.py` (likelihoods 60–100, Nelder–Mead 102–110, `window_means` 138–143,
  `block_folds` 118, score 254), `model_comparison.py`, `bms.py`, `README.md`, `RESULTS_sergent.md`.
- Literature (verified in the rev 1 review unless marked): Woody 1967 (Med Biol Eng 5:539); Truccolo et al. 2002
  (Clin Neurophysiol 113:206); Sekar, Findley & Llinás 2012 (Neuroscience 206:167); Navajas, Ahmadi & Quian Quiroga
  2013 (J Neurosci 33:1337); Rutiku, Aru & Bachmann 2016 (Front Hum Neurosci 10:23); Ouyang et al. 2011, 2015
  (RIDE). Sergent et al. 2021's article and supplement have no single-trial latency estimation, realignment or
  simulated jitter control; report conditioning can select on timing or amplitude. Bauer & Curran 2003 (Psychol
  Methods 8:338): statistical precedent for the SI's contribution 1 (unverified; to be read before citation). No
  prior matched held-out comparison of this kind was found; no first-ever claim will be made.
