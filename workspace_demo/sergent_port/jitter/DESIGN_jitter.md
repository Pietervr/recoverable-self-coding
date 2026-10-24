# Does the human two-state preference survive trial-level latency and scale variation?

Design, revision 5 — 24 October 2026, session R052 Entropy SI. Status: DRAFT for Codex re-review.
Revs 1–4 (RSC 960e93b, 57c1280, 8d6c195, 78e348c) received NOT FAVOURABLE (reviews under `jitter/reviews/`). The rev 4
review states that the central predictive comparison is substantially ready and that the template gauge, mean
matching, full-epoch generators, one-factor controls, conservative unavailable accounting, S4a/S4b split, E1 guard
band, common-roster attenuation contrasts, O1 continuation and O5 construction stand. Rev 5 closes the profile
confidence-set and threshold-calibration contract, the attribution antecedent and reference family, the remaining
implementation branches, and the cost units. Nothing has been run.

## 0. Stages and what is frozen when

S1  Provisional implementation; per-participant GENERATOR fits (§7.1: G3, B3 and B0, full data, whole epoch).
    Parameter values may be inspected; no cross-validated contrast is computed on real data.
S2  Development on development seeds (W2, T1, O1 at R = 25); numerical repairs; the §4 quadrature, support, rank and
    small-spread checks; the start-basin report; the profile-start validation of §5.
S3  FREEZE by commit: code, `decide.py` with branch tests, generator algorithms, the manifest, the ε algorithm, the λ
    search algorithm, the profile construction, the critical-value calibration procedure and counts.
S4a Reference calibration on calibration seeds: ε; λ pilots, certification, at most one correction (§7.4); the
    profile boundary critical values c₀ per family (§7.5, its own batch). Outputs frozen by commit: ε, λ_E1, λ_T3,
    their certified references, c₀,G and c₀,B.
S4b Independent final validation on fresh validation seeds at the frozen settings: gates (b), (c), (e), V2, the
    recovery battery and its flags R1–R5. Only S4b batches feed any gate or flag.
S5  Real-data cross-validated fits, real profiles and the final contrast. Never inspected before S5.
Using empirical generator fits before S3 is not circular validation of the final contrast; the licence is
conditional on the fitted configurations and is not confirmation on a new human sample.

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
The answer is a bounded statement about the published statistical comparison under this readout; §9 fixes what each
outcome licenses.

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
projected trace is not a shifted neural source. A fitted latency here is a property of the decoder-distance time
course. Timing information exists only where the template has structure: a constant template (equal coefficients,
allowed by the gauge) makes the likelihood exactly independent of s_τ, broad plateaus give the near-degeneracy, and
near-exponential shapes let a shift act as a scale. The recovery and profile programme of §7.5, not the
parameterisation, supports any statement about spread; each participant's timing-information proxy
I_τ|a = a²[T'ᵀΣ⁻¹T' − (T'ᵀΣ⁻¹T)²/(TᵀΣ⁻¹T)] at the fitted template is reported beside it.

## 3. Data, preprocessing and spans (inherited, unchanged)

- Participants S1–S20; active session primary; passive deferred.
- Decoder distance per trial and sample from `decode.py` (liblinear); 10 Hz zero-phase low-pass
  (`fit_models.lowpass_filtfilt`); the port's 53 window means (`window_means`: 16 samples each, centres −285 + 30 i
  ms, sample times −300 to 1290 ms). Levels shifted by −1 in all models; the catch level is **0**.
- Folds: the port's five block folds (`block_folds`); block 21 always in training, never scored.
- PRIMARY SPAN: the 16 windows with centres 255–705 ms (sample times 240–720 ms): the article's stated span, chosen
  after the published and reproduced curves were known and before this contrast; the source curve's first 0.95
  crossing is 315 ms and both curves return to graded-highest at 675 ms, so not every window is an established
  two-state window. The whole-epoch alternative would ask a catch-fixed low state to carry early sound processing
  present on every trial, a framing bias against B; the late restriction applies identically to both likelihoods,
  adds no B-only term, discards early timing information, and 240–270 ms is not a sharp stage boundary after the
  filter. The conclusion is about a catch-anchored late-response family.
- WHOLE-EPOCH SPAN (53 windows): the generator span (§7.1) and a sensitivity of the contrast.
- All real-data profiles (§7.5) and all recovery fits are on the PRIMARY span with full-data trial counts.

## 4. The model families

Notation: trial i, level k_i ∈ {0..5}, window w in the span, observed y_i ∈ R^W (W = 16 primary, 53 whole epoch).
Everything below is identical in both families unless the line says otherwise.

Shared construction, estimated per participant and fold on training trials only:
- Baseline μ0(w): mean of training catch trials. Both families predict exactly μ0 on a no-response trial.
- Residual covariance Σ (W × W): Ledoit–Wolf shrinkage on training catch deviations about μ0, fixed for all models in
  that participant and fold. Reported before the contrast is read: held-out catch whitening diagnostics (mean,
  covariance, excess kurtosis and a normality test of the whitened catch residuals projected on T̃ — a bimodal catch
  distribution would show here), level-stratified training residual second moments under each fitted model, and
  the common-covariance sensitivity D·R(ρ)·D (D = per-window training catch residual SDs; R(ρ) AR(1), ρ ∈ [0, 0.999]
  by ML on the same residuals; one matrix for both families). Σ has no model-independent direction of bias; it is
  challenged by O5 rather than argued.
- Level amplitudes: a(k) = softplus(α_k) > 0 for k = 1..5, a(0) = 0 fixed. Softplus attains no exact zero; the catch
  is anchored at zero by construction. Both families carry exactly these five parameters; the inherited
  logistic-in-level mean laws are a declared sensitivity.
- Template T. Basis: cubic B-spline, open-clamped (knot multiplicity 4 at both ends), interior knots every 60 ms,
  support = the span's sample-time range extended by the latency truncation: primary [90, 870] ms (16 basis
  functions; zero-based indices 0, 1, 14, 15 invisible at zero shift), whole epoch [−450, 1440] ms. Coefficients
  c_j = softplus(γ_j) > 0 with one gauge coefficient fixed, γ_ref = 0, for the visible basis function whose support
  is centred at 450 ms (tie-break between 450 and 510 ms: the earlier). The template entering the model is
  T̃(t) = T(t)/m_vis(T), m_vis = the mean of T over the span's window sample times at τ = 0, so a(k) is the mean
  response over the span at zero shift, in decoder units. Identifiability (verified in the rev 3 review): the fixed
  visible gauge removes the scale; the shift-only coefficients contribute nothing to m_vis or to zero-shift
  predictions, so they are REMOVED from the parameter vector in every model and every profile point with s_τ = 0
  (G0, G2, B0, B2, the s_τ = 0 point of any profile); in models with s_τ > 0 they are identified only through shifted
  nodes, with weights that vanish like exp(−c/s_τ²) as s_τ → 0. Checks before S3: Jacobian rank at a generic point;
  rank with the stacked 31-node basis; small-spread behaviour at parent spreads {1, 2, 5, 8} ms and at the smallest
  node spacing; the ±250 ms sensitivity support. Flat or unbounded profiles in the shift-only directions are reported
  as such. A window's value is the mean of T̃ over that window's 16 sample times (`fit_models.py:138`). T is the
  filtered response; no second filter. T is fitted separately inside each model with identical basis, support,
  constraints and training-only initialisation; fitted shapes are plotted per participant; a common independently
  estimated template is run as a diagnostic if the contrast depends on them.
- Trial latency τ_i ~ N(0, s_τ²) truncated to ±150 ms, marginalised on 31 equally spaced nodes (10 ms) with
  truncated-normal weights normalised to one; s_τ ∈ (0, 150] ms a box parameter in the positive-spread model; the
  exact s_τ = 0 model is the REDUCED model (one node, shift-only coefficients removed). Parent and realised SD both
  reported (parent 80 → truncated 68.1 ms, 31-node 69.3 ms). Node check before S3: 31 vs 61 nodes must change every
  development participant's score contrast by less than one tenth of the contrast's interval half-width, else 61 is
  adopted and re-checked against 121. The ±250 ms support is a different latent model, run as a declared sensitivity
  with its own template support.
- Trial scale g_i ~ LogNormal(−s_g²/2, s_g²), mean 1; s_g ∈ [0, 1.5] box, s_g = 0 exact (the scale parameter does not
  change the parameter dimension, so no reduced model is needed); Gauss–Hermite 7 nodes checked against 15 at
  s_g = 1.5 under the same tolerance (15 adopted and checked against 31 if it fails). Fits at the s_g bound are
  flagged; a wider-bound (s_g ≤ 2.5, re-checked quadrature) sensitivity is run if any flagged fit is in a participant
  whose Δ_s drives the result. g and τ independent, level-invariant, one shape shifted as a whole: shared
  restrictions, challenged by O3/O4.

Graded family: y_i | k_i, τ_i, g_i ~ N( μ0 + g_i · a(k_i) · T̃(· − τ_i), Σ ).   G0: s_τ = s_g = 0. G1: s_τ free. G2:
s_g free. G3: both.
Two-state family: z_i ~ Bernoulli(A(k_i)), A(k) = max(A_min, lg_{κ,x0}(k)) for k ≥ 1, κ > 0 (log-parameterised),
A(0) = 0, A_min = 0.02.   y | z = 0 ~ N(μ0, Σ);   y | z = 1, τ, g ~ N( μ0 + g · m_H(k) · T̃(· − τ), Σ ),
m_H(k) = a(k)/A(k).   B0–B3 as G0–G3, nuisance on the high branch.

Declared second-moment consequence. With b = E[T̃_τ], H = E[T̃_τ T̃_τᵀ], r = exp(s_g²): both families have mean a·b;
Cov_G = Σ + a²(rH − bbᵀ), Cov_B = Σ + a²(rH/A − bbᵀ). The occupancy parameters are also a level-dependent variance
law along the template (at A = 0.02 up to 49a² before scale; the graded bound at s_g = 1.5 is 8.49a²). This is the
two-state hypothesis' own flexibility: a B win may reflect variance/tail modelling without visibly resolved modes,
and with s_g > 0 B's amplitude law is a point mass at zero plus a lognormal high branch. The floor A_min bounds m_H/a
at 50, is a numerical restriction with zero occupancy derivative when clipped; clipped levels are archived per fit;
a floor sensitivity {0.01, 0.02, 0.05} is run on the real comparison and on the T2 development case. Occupancy and
high-amplitude values are REPORTED per participant from the full-data B3 fit (point estimates with the archived
clip status); no occupancy profile is promised.

Catch anchoring A(0) = a(0) = 0 is a common restriction of both families. The free-catch sensitivity is WITHDRAWN
(exact invariance μ0 → μ0 + d·T̃, a(k) → a(k) − d with no independent baseline anchor on the primary span); the
restriction is checked by the held-out catch whitening and normality diagnostics above, and declared in §10.

Parameter counts, non-template: G0 5, G3 7, B0 7, B3 9. Template: 15 free coefficients in positive-spread models, 11
in reduced (s_τ = 0) models. No information criterion is added to a cross-validated score.

## 5. Fitting

- Maximum marginal likelihood, float64, JAX gradients, L-BFGS-B on the box above with parameter scaling (times in
  ms/100, amplitudes in decoder units, logits unit). Σ is Cholesky-whitened once per fold; for each τ node the
  whitened template v_τ = Σ^{-1/2} T̃_τ is recomputed when template parameters change; for whitened data u_i,
    q(i, τ, g) = ‖u_i‖² − 2 g m(k_i) (u_i · v_τ) + (g m(k_i))² ‖v_τ‖²,  m = a (graded) or m_H = a/A (two-state high
  branch); all trial–template projections as one matrix product; the two-state low branch is the m = 0 term; the
  branches combine by log-sum-exp with the occupancy weights. No residual tensor over nodes is formed.
- Zero-boundary construction for models with s_τ free (G1, G3, B1, B3). A single box-constrained call cannot change
  the parameter dimension at s_τ = 0, so each such fit is the better of two candidates: (i) the REDUCED fit (the
  corresponding s_τ = 0 model: G0 for G1, G2 for G3, etc., 11 template coefficients, s_τ absent) and (ii) the
  POSITIVE-SPREAD fit with s_τ ∈ [2, 150] ms (15 coefficients), started at the §5 spread starts (never at zero).
  The selected objective is max of the two; the selected model is recorded as REDUCED or POSITIVE. With fixed-node
  weights the spread derivative vanishes near zero, so the positive-spread candidate is what searches for a positive
  optimum; the reduced candidate preserves the exact likelihood at zero. The lower box edge 2 ms is a declared
  numerical floor; a positive-spread fit at that edge is flagged and the reduced fit is the comparison.
- Starts: exactly 4 per fit, from the fold's training blocks only. Two template starts: T_A = non-negative least
  squares of the basis to the training level-5 mean time course over the support's visible part; T_B = the same fit
  to that time course smoothed by a 90 ms moving average. Each: floor coefficients at 1e-3, rescale so the reference
  coefficient equals softplus(0) = ln 2, then γ = softplus⁻¹(c) = log(exp(c) − 1). T_A and T_B are recipes, not
  guaranteed distinct vectors (they coincide on a constant trace); coincidence is logged. Level amplitudes from
  training level means over the span, clipped below at 0.05 decoder units. κ, x0 from a logistic regression of the
  per-trial indicator "mean over the span above the training catch 90th percentile" on level; if separated or with
  a non-positive slope, κ = 1 per level unit and x0 = 2.5. Nuisance starts by model: G0/B0 (and every reduced
  candidate): {T_A, T_B} × {amplitudes as computed, amplitudes × 0.5}; G1/B1 positive-spread: {T_A, T_B} × s_τ ∈ {20,
  40 ms}; G2/B2: {T_A, T_B} × s_g ∈ {0, 0.4}; G3/B3 positive-spread: T_A × {(20, 0), (40, 0.4)}, T_B × {(40, 0), (20,
  0.4)}. Development (S2) adds a near-collapsed two-state start (A → 1 at all levels) and a broad-template start,
  and reports whether any start beyond the first changed the selected optimum; starts found material are added to
  the frozen recipe at S3 for all models alike.
- Constrained (profile) fits, §7.5: s_τ fixed at a grid value; the parameters are the full positive-spread vector
  minus s_τ (or the reduced vector at s_τ = 0). Starts: TWO per constrained fit — the unrestricted MLE of the same
  model (warm start) and the T_B start with the grid value's nearest §5 nuisance start. This is a declared exception
  to the four-start rule, VALIDATED in S2: on the development sets, 2-start constrained optima must agree with
  4-start constrained optima to 1e-6 relative in objective at every grid point of every profile; if not, profiles
  use 4 starts and §8 is re-costed before S3.
- Acceptance: a fit is CONVERGED when all of (i) projected-gradient infinity norm ≤ 1e-5 in scaled units; (ii)
  relative objective change over the last 5 iterations ≤ 1e-9; (iii) finite objective and parameters. If fewer
  than 5 iterations ran, the fit is EARLY: it is re-run once from the same start perturbed by N(0, 0.1²) in scaled
  coordinates, and the pair is CONVERGED only if both satisfy (i) and (iii) and their objectives agree to 1e-8
  relative; the better objective is kept. Iteration cap 2,000; two retries from re-seeded perturbed starts
  (N(0, 0.1²) scaled) on failure. A model whose starts leave no CONVERGED fit is UNAVAILABLE for that participant and
  fold. The best CONVERGED objective is selected; every start's end point and status is archived.
- Score: every out-of-fold trial's log marginal density summed once over the five folds, divided once by the total
  number of scored trials (block 21 excluded): S_{s,m}, nat per trial. The inherited fold-mean convention
  (`fit_models.py:254`) is reported for continuity only.
- Correctness: whitened objective and gradient checked against a direct dense implementation to 1e-10 relative on
  small cases; the §4 checks archived before S3.
- Logging per fit: data identity, code hash, seeds, bounds hit, clipped levels, retries, EARLY flags, REDUCED/POSITIVE
  selection, start statuses, start coincidences.

## 6. The decision

Primary estimand: the mean over available participants of the paired per-trial held-out advantage on the primary
span, Δ_s = S_{s,B3} − S_{s,G3}, with its 95% t-interval (n_avail − 1 degrees of freedom; participant as unit). The
inherited BMS protected exceedance probability is reported beside it as a descriptive convention.

Define Δ_j,s = S_{s,Bj} − S_{s,Gj} for j ∈ {0, 2, 3}.

LICENCE of the primary sign (all required; recovery flags are NOT part of it):
  V1a gates (b) and (c) of §7.3 met in S4b;
  V2  completion: at every ATTEMPTED S4b decision setting of §7.3 (an uninstantiated E1 or T3 after failed
      certification is reported as absent, not counted), UNAVAILABLE set-level primaries ≤ 10% of attempted sets;
      on the real data ≥ 16 of 20 participants with CONVERGED B3 and G3;
  V3  nothing non-finite in the primary interval.
LICENCE of the upper-bound field (separately): ε AVAILABLE, λ_E1 CERTIFIED, gate (e) met in S4b. If this licence
fails, UPPER BOUND is UNAVAILABLE and the primary sign licence is unaffected.
If the primary licence fails the primary result is NOT LICENSED; descriptive summaries, recovery and mechanism
results are still reported.

`decide.py` computes ALL of the following fields (no field ends the evaluation of another):
  PRIMARY SIGN: POSITIVE (lower bound > 0), NEGATIVE (upper bound < 0), UNRESOLVED (otherwise; a bound exactly 0 is
    UNRESOLVED). UNRESOLVED is not evidence of absence.
  ATTENUATION, on the common roster R6 = participants with all six of G0, G2, G3, B0, B2, B3 CONVERGED (≥ 16, else
    UNAVAILABLE), each a paired participant mean with its 95% t-interval, each POSITIVE / NEGATIVE / UNRESOLVED:
      D       = Δ_0 − Δ_3            (total attenuation of the B advantage by both nuisance terms)
      D_scale = Δ_0 − Δ_2            (attenuation by scale alone)
      D_τ     = Δ_2 − Δ_3            (incremental attenuation by latency after scale)
      D_τ − D_scale                  (which component contributes more, in this scale-first decomposition)
    D = D_scale + D_τ exactly on R6. The decomposition is scale-first and, with interactions, not an
    order-independent partition of responsibility; it is declared as such.
  UPPER BOUND (not equivalence): BOUNDED if the upper endpoint of the two-sided 95% interval for Δ_3 < ε, else NOT
    BOUNDED; UNAVAILABLE under the conditions above. POSITIVE and BOUNDED may coexist and are both reported.
  BRIDGE: (i) the unchanged inherited per-window result stands; (ii) held-out per-window marginal predictions of G0
    and B0 beside it; (iii) joint Δ_0 on the primary span: POSITIVE / NEGATIVE / UNRESOLVED / UNAVAILABLE (≥ 16).
  RECOVERY ADEQUATE and JITTER DETECTED, each per family (§7.5). REFERENCE FAMILY for attribution = G (declared
  now, §9): the attribution claim is that a graded account with trial variation explains part of the inherited
  advantage, so the latency term whose identification matters is the graded family's. B's flags are reported.
  ATTRIBUTION (secondary, each ≥ 16 on its own roster else UNAVAILABLE): G3 − G2, B3 − B2, G2 − G0, B2 − B0, G3 − G0,
    B3 − B0; fitted s_τ per participant with its §7.5 profile interval (raw); fitted s_g per participant as a RAW
    point estimate with its L-BFGS-B box status (no scale profile or interval is promised).
Branch tests committed at S3 cover at least: failed recovery with valid prediction; B0/G0 missing with B3/G3
available; ε UNAVAILABLE; λ_E1 not certified (absent E1, V2 unaffected); a positive but sub-ε advantage; a failed
calibration setting; a setting over the UNAVAILABLE limit; non-finite fits; exactly-zero bounds; a roster of 15; the
rev 3 counterexample (D POSITIVE, G3 − G2 and B3 − B2 POSITIVE, D_τ NEGATIVE → no latency attribution); the rev 4
counterexample (D_τ POSITIVE, D_τ − D_scale POSITIVE, D NEGATIVE → no "most of the attenuation", wording limited to
"adding latency after scale reduced Δ_2"); successful initial λ targeting; failed and corrected targeting;
unavailable recovery and profile outcomes; an off-grid true spread; a disconnected profile set; an empty accepted set.

## 7. Generators, calibration, recovery

### 7.1 Generator fits (S1)
Per real participant, three GENERATOR fits on full data (all blocks, no cross-validation), whole-epoch span,
whole-epoch template support, μ0 and the 53 × 53 Ledoit–Wolf Σ from all catch trials: G3, B3 and B0 (each 4 starts,
§5). These supply every synthetic configuration (a, T̃, κ, x0, s_τ, s_g, μ0, Σ) in 53 dimensions, so synthetic data
are generated as 53-window vectors and scored on the primary 16 windows, the whole epoch, and by the inherited
per-window pipeline alike. Generator fits never substitute for S5 scoring fits; primary-span fits generate nothing.
Response strength per configuration, a continuous covariate reported with every recovery result (no strata):
strength = a_gen(5) × (mean of T̃_gen over the primary windows at τ = 0), the generator's level-5 mean response over
255–705 ms in decoder units.

### 7.2 Generation
A synthetic participant has one coherent generating distribution across all five folds, with its base participant's
level counts and block labels (labels preserve counts and fold membership only, not stochastic block dependence —
declared limitation). For decision calibration each replicate set draws 20 base configurations with replacement from
the 20 (population generator, conditional on that finite empirical distribution). Within each synthetic training fold
μ0, Σ, shrinkage, starts and templates are re-estimated by the fitter exactly as on real data. Synthetic 53-window
vectors enter the inherited likelihoods after `window_means`; nothing is filtered or averaged again. For O1 the
stretch is applied to the continuous filtered template before the 16-sample window averaging, in both batteries.
Mechanism settings W1, W3, W4 are INDEPENDENT draws of configuration sets from the same pool (not paired), each with
only (s_τ, s_g) set; W1-vs-W3 and W1-vs-W4 therefore use the independent-proportion Newcombe interval (§7.6).

### 7.3 Final-validation manifest (S4b; fits G0, B0, G3, B3; 5 folds × 4 starts = 80 starts per participant-dataset)
  Graded, well-specified: W1 (s_τ, s_g) = (0, 0); W2 fitted G3; W3 (80 ms, 0); W4 (0, 1.0).         R = 100 each.
  Graded, out of family (zero latency jitter unless stated; s_g at the fitted G3 value unless stated):
    O1 per-trial time stretch about 240 ms: t' = 240 + (t − 240)·exp(ζ_i), ζ_i ~ N(0, 0.25²) truncated to ±0.5; the
       template CONTINUED beyond its support by its endpoint values (clamped at −450 and 1440 ms), identical in the
       decision and recovery O1; amplitude a(k) applied without renormalisation.
    O2 two components: T̃ split at 450 ms by a logistic ramp of slope 1/30 ms into T_a (early) and T_b (late);
       per-trial w_i ~ Beta(2, 2); response a(k)[2 w_i T_a + 2(1 − w_i) T_b] (mean a(k) T̃).
    O3 level-dependent latency, s_τ by level k = 1..5 = {60, 60, 40, 20, 20} ms.
    O4 (log g, τ) bivariate normal, correlation −0.5 before truncation, s_τ = 60 ms, g rescaled to mean one.
    O5 covariance challenge: y = m_k + (y_j − ȳ_k), the empirical within-level distribution of the base participant's
       real trials recentred to the G3 generator's marginal level mean m_k (resampled with replacement); no fresh
       latent draw. Declared: a covariance and shape challenge that retains the real trial variability once, not a
       known-truth graded generator.                                                             R = 100 each.
  Two-state: T1 fitted B3; T2 B3 with s_τ = 80 ms and occupancy A(k)/2 at every level (m_H recomputed so level means
    are unchanged; values below 0.02 generated as is and recorded; halving leaves the logistic family, declared);
    T3 on the §7.4 path at certified reference 2ε.                                        T1, T2, T3: R = 50 each.
  E1 on the §7.4 path at certified reference in [1.10, 1.40] ε (target 1.25 ε).                        R = 100.
Count: 9 × 100 + 3 × 50 + 100 = 1,150 sets, 23,000 participant-datasets, 1.84 M starts.
Pass conditions (pointwise for the frozen settings; exact one-sided 95% Clopper–Pearson; all-pass is an intersection
requirement; no simultaneous coverage claimed; none certifies the nominal 2.5% tail of a calibrated interval; the
tolerated ceilings are stated as such):
  (b) false POSITIVE under every graded setting W1–W4, O1–O5: ≤ 1 of 100 attempted sets (upper bound 4.66%), an
      UNAVAILABLE set-level primary counted as POSITIVE;
  (c) power at T1: ≥ 45 of 50 sets POSITIVE (lower bound 80.1%), UNAVAILABLE counted as non-detection; T2 and T3
      reported (detection, false NEGATIVE, interval coverage of the certified reference);
  (e) upper-bound error at E1: BOUNDED in ≤ 4 of 100 sets (upper bound 8.92%), UNAVAILABLE counted as BOUNDED; the
      certified E1 reference and its MC interval reported with the gate; coverage of the procedure reference
      reported at E1, W2 and O1; the result is stated as conditional on reference certification;
  V2 completion: UNAVAILABLE set-level primaries ≤ 10% at every attempted setting; every attempted set in the
      denominator; uninstantiated E1/T3 reported as absent.
One E1 point and one T1 alternative establish error control at the frozen settings, not uniform coverage or
least-favourable control along the path; §9 claims no more.
Any reduction of the frozen manifest triggers fresh-seed re-validation of the retained settings.

### 7.4 The margin ε, the λ path, certification (S4a)
Procedure reference at a configuration: the expected group mean of Δ_3 (or Δ_0 for the ε benchmark) when 20
resampled synthetic participants are generated from it and scored by the finite-training cross-validated procedure
on the primary span; estimated as the mean over R_ref independent sets; MC interval = mean ± t_{0.975, n_avail − 1} ×
SD/√n_avail over the AVAILABLE sets (nominal; a set with fewer than 16 usable participants is UNAVAILABLE and
counted); if more than 10% of the sets are UNAVAILABLE the reference is UNAVAILABLE, otherwise it is the mean over
available sets with that conditioning declared.
ε: the reference of Δ_0 under the fitted B0 generators (§7.1), R_ε = 50; ε = benchmark/3. If the benchmark's MC lower
bound ≤ 0 or the reference is UNAVAILABLE, ε is UNAVAILABLE (the upper-bound field is UNAVAILABLE; the primary licence
is unaffected). ε's algorithm is frozen at S3, its value at the end of S4a.
λ path: from the fitted B3 configuration, scale a(k) by λ ∈ (0, 1] at every level (m_H follows; occupancy
unchanged). No monotone finite-training advantage is guaranteed, so the search is declared:
  pilot λ ∈ {1, 0.75, 0.5, 0.35, 0.25} at R = 20 each (calibration seeds, shared between the two targets);
  reference estimate r(λ) and MC interval at each; an UNAVAILABLE pilot reference removes that λ from the grid; an
  exact hit (target inside a pilot's MC interval) selects that λ directly for certification;
  bracket: the adjacent remaining pilot pair whose estimates straddle the target; among several, the pair with the
  larger λ; fewer than two remaining pilots or no bracket → declared SEARCH FAILURE (the setting is UNCERTIFIED; (e)
  or T3 absent; this is failure of the declared search, not proof that no λ attains the target);
  interpolate linearly in λ between the bracket's two (λ, r) points; certify at R_ref = 50 fresh calibration seeds:
  CERTIFIED if the certified MC interval lies within target ± 0.15 ε (for E1 this places it inside [1.10, 1.40] ε,
  above ε by construction);
  otherwise ONE secant correction: the two points are (λ_cert, r_cert) and whichever bracket endpoint lies on the
  other side of the target from r_cert (if both are on the same side, the nearer endpoint); if the secant slope is
  zero or the proposed λ leaves (0, 1], SEARCH FAILURE; re-certify at R_ref = 50 fresh seeds under the same rule;
  failing that, UNCERTIFIED. Both certification attempts are reported. Because two attempts are allowed, each
  certification interval uses the 97.5% level (t_{0.9875}) so that the stated 95% confidence covers the pair.
  Targets: E1 1.25 ε; T3 2 ε. λ_E1, λ_T3 and their certified references are frozen by commit before S4b; S4b draws
  fresh validation seeds; no S4a batch feeds a gate, and no S4b batch is used to re-target.

### 7.5 Recovery battery, profiles and the jitter flags
Fixed roster: the 20 real participants' G3 and B3 generator configurations (not resampled). Recovery settings per
family: (s_τ, s_g) ∈ {0, 20, 40, 80} ms × {0, fitted, 1.0} (12 each, 24); plus O1 and O2 at zero jitter, generated
once and fitted by both families (2 shared): 26 settings. R = 25 independent datasets per configuration × setting;
all eight models fitted on FULL synthetic data (all blocks; the same fit size as the real reported estimates),
PRIMARY span, 4 starts (§5).
Confidence-bound convention for recovery rates (R2–R5): these pool replicates over a FIXED heterogeneous roster of
20 configurations; rates are reported pooled over all attempted replicates with exact one-sided 95% Clopper–Pearson
bounds treating replicates as independent given the roster, and per configuration beside them; the target is the
rate for this roster, not a population rate.
Profile confidence set for s_τ (per participant or synthetic dataset, per family's full model):
  q(s) = 2[ℓ̂ − ℓ_prof(s)], where ℓ̂ is the selected unrestricted objective (§5 zero-boundary construction) and
  ℓ_prof(s) the constrained optimum at s_τ = s (reduced model at s = 0; §5 constrained starts). If any ℓ_prof(s) >
  ℓ̂, ℓ̂ is replaced by that value and the unrestricted fit flagged. Grid {0, 5, 10, 15, 20, 30, 40, 50, 60, 80, 100,
  120, 150} ms. Accepted points: q(0) ≤ c₀ (family-specific boundary critical value, §7.5 calibration) and, for
  s > 0, q(s) ≤ χ²₁(0.95) = 3.841. Interval: the CONSERVATIVE OUTER HULL of the accepted set — lower bound = the
  largest grid point below the smallest accepted point that is rejected (or 0 if 0 is accepted), refined by one
  bisection between it and the smallest accepted point; upper bound symmetric (150 if 150 accepted). Disconnected
  accepted sets are reported as such and the hull is used (an accepted zero is never discarded by a search near
  the MLE). Empty accepted set → UNAVAILABLE profile (flagged). A constrained fit UNAVAILABLE at any grid point →
  UNAVAILABLE profile. "Lower bound > 20 ms" is evaluated on the hull's lower bound.
Boundary critical value c₀ (per family), S4a, its OWN batch: 500 datasets per family from the (0, fitted) zero-jitter
  generator on the fixed roster (25 per configuration), two fits each — the unrestricted positive-spread fit and the
  reduced fit — giving q(0); c₀ = the empirical 95th percentile (type-7 quantile) over AVAILABLE q(0) values; if more
  than 5% of the 500 are UNAVAILABLE, c₀ is UNAVAILABLE and every profile is UNAVAILABLE. c₀,G and c₀,B are frozen by
  commit before S4b. The S4b recovery batch never re-estimates c₀.
Statistics per configuration, setting, family, over AVAILABLE replicates: median relative bias of ŝ_τ; RMSE =
  sqrt(mean(ŝ_τ − s_τ)²); boundary-hit frequency; interval coverage; completion fraction. A configuration × setting
  with more than 20% UNAVAILABLE point fits or profiles FAILS that setting.
RECOVERY ADEQUATE (per family F), all required, all on S4b data:
  R1 point recovery: at s_τ = 40 ms and at 80 ms with fitted s_g, the SAME ≥ 15 of 20 configurations have median
     relative bias within ±25%, RMSE ≤ 50% of the true s_τ, and pass completion, in family F's full model;
  R2 false jitter: over all attempted replicates (unavailable counted as false) of each zero-jitter setting
     {(0, 0), (0, fitted), (0, 1.0), O1, O2} for family F, the fraction with ŝ_τ > 20 ms is ≤ 10% with upper bound
     ≤ 15%;
  R3 false detection at zero: over the same zero-jitter replicates, the fraction whose hull lower bound > 20 ms is
     ≤ 5% with upper bound ≤ 10%;
  R4 coverage: at (40, fitted) and (80, fitted), the hull covers the true s_τ in ≥ 90% of attempted replicates
     (unavailable counted as non-coverage) with lower bound ≥ 87%;
  R5 the 20 ms boundary actually used by the magnitude claim: at (20, fitted), the fraction of attempted replicates
     whose hull lower bound > 20 ms is ≤ 10% with upper bound ≤ 15% (unavailable counted as detections), and the hull
     covers 20 ms in ≥ 90% with lower bound ≥ 87%. If R5 fails but R1–R4 pass, the flag is ADEQUATE-ZERO-ONLY: the
     paper may report rejection of the tested zero-jitter explanations and must describe the above-20 ms magnitude
     as a nominal profile inference, not a calibrated bound.
Otherwise NOT ADEQUATE; the paper reports measured non-identifiability or miscalibration.
JITTER DETECTED (real data, per family F): the real full-data primary-span hull lower bound exceeds 20 ms in ≥ 10 of
20 participants in family F's full model (an UNAVAILABLE profile is a non-detection), and the group G3 − G2 (F = G) or
B3 − B2 (F = B) interval is POSITIVE. Real estimates are reported RAW with their hulls; simulation bias and RMSE are
diagnostics and are never applied as corrections to real data.
These flags support identification of a nontrivial parent spread for the specified readout model under the tested
conditions; they do not establish global identifiability, exclude every shape or noise explanation, or choose the
real generating family. Both families' flags are reported.
Individual τ_i posterior means are checked against truth on high-level synthetic trials and reported as secondary.

### 7.6 Inherited-pipeline mechanism test (S4b)
On the 53-window synthetic sets of W1–W4, O1–O5, T1: the unchanged per-window likelihoods and `model_comparison.py`
after `window_means`. Reported: the paper's three summaries (first window with pxp₃ > 0.95; first run of ≥ 3
consecutive windows with M3 the highest pxp, ties counting as not highest, "no run" if none; the strict MATLAB
Simes set), the full pxp curve and the per-participant per-window score advantage. The binary "call" is the
≥ 3-window run with its first window inside the primary span. A RISE in call rate from W1 to W3 (latency) or W1 to
W4 (scale) is declared when the 95% Newcombe interval for the difference of two INDEPENDENT proportions (the sets
are independent draws, §7.2) has lower bound > 0. W1 vs W3 and W1 vs W4 establish a sufficient simulation mechanism,
not which component reduced the real contrast. The Simes-on-pxp convention has no established error control and is
reported as the inherited convention.

### 7.7 Numerical validity
Every attempted dataset and set counted. UNAVAILABLE per §5; a set with UNAVAILABLE primary fits in more than 4 of
its 20 participants has an UNAVAILABLE set-level primary (the same available-case rule as the real data; this
set-level rule applies to CV decision settings only, not to full-data recovery fits, which use §7.5's completion
rules). Optimisation and quadrature error shown small relative to the contrast on development data before S4 seeds
are drawn. Development, calibration and validation seeds are disjoint and never reused.

## 8. Compute, venue, cost

All in START-level optimisations at the UNMEASURED 30 s/start target; "fit" = 4 starts unless stated; projections at
assumed rates, not quotes. Inherited Nelder–Mead runs priced at the README-derived, unmeasured 0.14 s/run; BMS
(1 M Dirichlet draws per call in the unchanged code) priced at an assumed 1 s/call, to be measured.
- Real data, Mac (free): CV fits 20 × 8 models × 5 folds × 4 × 2 spans = 6,400 starts; generator fits 60 fits = 240
  starts; unrestricted real full-data fits 20 × 8 × 4 = 640; real profiles 20 × 2 families × 15 constrained × 2 starts
  = 1,200; sensitivities (±250 support, inherited mean laws, D·R(ρ)·D, floor, s_g bound, whole-epoch contrast) ≈
  4 × 6,400 = 25,600 starts if all are run; total ≈ 34,000 starts ≈ 285 core-h (several days on 12 Mac cores; the
  sensitivities can also go to AWS at ≈ USD 4 each ideal).
- AWS, S4a: ε 50 × 20 × 40 = 40,000; pilots 5 × 20 × 20 × 80 = 160,000; certification 2 × 50 × 20 × 80 = 160,000;
  re-certification contingency 160,000; c₀ batches 2 families × 500 × 2 fits × 4 = 8,000. Subtotal 368,000 starts
  (528,000 with the contingency).
- AWS, S4b: decision manifest 23,000 × 80 = 1,840,000; recovery 26 settings × 25 × 20 × 8 models × 4 = 416,000;
  recovery profiles 26 × 25 × 20 × 2 families × 15 constrained × 2 starts = 780,000 (1,560,000 if the §5 profile-start
  validation fails and 4 starts are required); inherited pipeline 950 sets × 20 × 795 = 15.1 M Nelder–Mead runs ≈
  587 core-h plus 950 × 53 = 50,350 BMS calls ≈ 14 core-h. Subtotal 3,036,000 starts (3,816,000 at 4-start profiles).
- Totals: 3,404,000 starts ≈ 28,370 core-h + 600 inherited ≈ 29,000 core-h (2-start profiles, no contingency);
  ≈ 30,300 with the contingency; ≈ 36,800 with 4-start profiles and the contingency. S2 development (R = 25 at three
  settings, ≈ 120,000 starts ≈ 1,000 core-h) is in addition and runs on the Mac where possible.
- At c7a.24xlarge (96 vCPU) and the October spot rate ≈ USD 1.7/h: ≈ USD 510–650 at perfect utilisation; ≈ USD
  920–1,170 at 70% utilisation with a 25% retry reserve; on-demand (≈ USD 5.3/h) ≈ USD 1,600–3,600.
- Before launch: benchmark one participant's full §4 set, a profile (both start rules), a generator fit, a c₀ pair
  and the inherited pipeline including BMS on the Mac and on the target instance (steady-state value + gradient to
  convergence from all starts; completed-dataset throughput at 96-way concurrency; compile time separately); cost
  the frozen manifest from measured rates in starts and runs; set the ledger row cap (Unimog
  `rsc_t1_simulation_design.md` §12 row 24) from that number; confirm headroom under the USD 3,000 AWS cap from the
  R052 spend trail; put the number to the owner. The USD 400 placeholder in the ledger row is not met by this
  manifest and is reset at the measured number.
- Declared reduction order if the measured cost exceeds the approved cap: (1) starts 4 → 3 in validation replicates
  only if S2 shows the fourth start never changed the selected optimum; (2) merge O3 and O4; (3) T2 to
  development-only; (4) recovery R 25 → 15 with thresholds unchanged and reduced precision stated; (5) profile grid
  13 → 9 points with the hull rule unchanged. Never: R below 100 at graded settings or E1, removal of O1/O2/O5,
  coarser quadrature than §4 licensed, skipping certification or the c₀ batch, or dropping R5. Any reduction
  re-validates on fresh seeds. If the cap still cannot be met, the licence narrows (ADEQUATE-ZERO-ONLY is the
  declared narrower identification claim) or the study stops.
- Checkpoint per completed dataset for spot retries; one BLAS/XLA thread per worker; JIT with cached shapes.

## 9. What each outcome licenses in the paper

The study replaces the "untested jitter" limitation with a bounded answer; it is the SI's one central empirical
addition. Conditional on the primary licence:
- PRIMARY POSITIVE: "In this auditory dataset, over 255–705 ms, the two-state family retained a positive held-out
  advantage over the matched graded family after both represented trial-level latency and scale variation
  (interval; recovery status; misspecifications tested)." Not: that the published result rests on no artefact, nor
  that every graded account fails. If RECOVERY is NOT ADEQUATE or JITTER not DETECTED in G, robustness is to a scale
  term and to a latency term the data did not pin down, and the text says so.
- ATTENUATION PREMISE: any sentence about attenuation OF THE INHERITED ADVANTAGE requires BRIDGE (iii) POSITIVE and
  D POSITIVE. Without the premise, a POSITIVE D_τ is reported only as "adding latency after scale reduced the
  scale-only contrast Δ_2", never as attenuation of the inherited advantage.
- "Not robust to representing trial variability": the premise, with the residual advantage then reported as
  NEGATIVE, UNRESOLVED or BOUNDED (an UNRESOLVED residual is called unresolved even when D is POSITIVE). A NEGATIVE
  primary with BRIDGE (iii) not POSITIVE is "the joint framing favours the graded family", a framing result.
- "Latency variation carries part of the attenuation": the premise, D_τ POSITIVE, RECOVERY ADEQUATE (full, not
  ZERO-ONLY) and JITTER DETECTED in the reference family G, and the W1→W3 RISE. "Latency carries most of the
  attenuation": additionally D_τ − D_scale POSITIVE. The scale analogue: the premise, D_scale POSITIVE, the W1→W4
  RISE. Short of these, attribution is to trial variability of unidentified form. The decomposition is scale-first
  and declared as such. Even then the supported wording is a decoder-readout latency term, not a physiological
  latency.
- Under ADEQUATE-ZERO-ONLY, the paper may say the tested zero-jitter explanations are rejected where the real hull
  excludes zero, and reports the above-20 ms magnitude as a nominal profile inference.
- Any statement that graded simulations reproduced features of the inherited preference is made only if §7.6 shows
  it, with the setting named. If the tested latency settings do not reproduce the late plateau, the paper says
  "these tested jitter distributions did not reproduce it", not that the plateau is not a rising-edge artefact.
- UNRESOLVED without BOUNDED: reported with the interval, D, D_scale, D_τ, the T3/E1 detection and error rates, and
  the flags; not evidence of absence, not a survival.
- NOT LICENSED: descriptive summaries, recovery and mechanism results; no primary claim.
Error control is claimed at the frozen settings conditional on the fitted generator population, not uniformly; the
upper-bound result is conditional on reference certification.

Hostile reading anticipated: a better mean law (shared level means); variance/tail flexibility read as modes (the
declared second-moment law); noise or shape variability mislabelled as latency (R2/R3/R5 under O1/O2 and at 20 ms,
JITTER DETECTED on calibrated hulls, the readout-level declaration); a whole-epoch question substituted (primary
span, rationale declared); absence from non-significance (the partition, D, ε as an upper-bound claim with a
certified boundary); attribution from the wrong contrast or without its premise (D_τ with D POSITIVE and BRIDGE); a
battery from the fitted families only (O1–O5); decoder leakage (declared, unchanged); novelty (cited; no "first"
claim).

## 10. What this study does not do

It changes none of the decoder, folds, windows or inherited per-window models; the SI's reproduction stands. It does
not quantify the inherited design's leakage, and the decoder and likelihood folds remain non-nested on the saved
preds. It tests one nuisance family (latency shift of one template, lognormal scale, independent, level-invariant)
and challenges it with O1–O5; multi-component latencies, non-Gaussian residuals and a fixed-spatial-decoder
re-analysis are follow-on work. Catch anchoring is a common restriction checked only by the held-out catch
diagnostics; the free-catch sensitivity is withdrawn as non-identifiable. No scale (s_g) interval and no occupancy
profile are promised. The passive session, the whole-epoch contrast, ±250 ms support, the inherited mean laws,
D·R(ρ)·D, the A_min floor and the wider s_g bound are declared sensitivities. No claim about the language model and
none about experience.

## 11. Files and literature

- This design: `workspace_demo/sergent_port/jitter/DESIGN_jitter.md` (rev 5; rev 1 960e93b, rev 2 57c1280, rev 3
  8d6c195, rev 4 78e348c). Codex reviews under `jitter/reviews/`.
- Code (after review): `jitter/{models.py, fit.py, simulate.py, decide.py, bench.py}` with tests; results under
  `jitter/results/`.
- Inherited code: `sergent_port/fit_models.py` (likelihoods 60–100, Nelder–Mead 102–110, `window_means` 138–143,
  `block_folds` 118, score 254), `model_comparison.py`, `bms.py`, `README.md`, `RESULTS_sergent.md`.
- Literature (verified in the rev 1 review unless marked): Woody 1967 (Med Biol Eng 5:539); Truccolo et al. 2002
  (Clin Neurophysiol 113:206); Sekar, Findley & Llinás 2012 (Neuroscience 206:167); Navajas, Ahmadi & Quian Quiroga
  2013 (J Neurosci 33:1337); Rutiku, Aru & Bachmann 2016 (Front Hum Neurosci 10:23); Ouyang et al. 2011, 2015
  (RIDE). Sergent et al. 2021's article and supplement have no single-trial latency estimation, realignment or
  simulated jitter control. Bauer & Curran 2003 (Psychol Methods 8:338): statistical precedent for the SI's
  contribution 1 (unverified; to be read before citation). No prior matched held-out comparison of this kind was
  found; no first-ever claim will be made.
