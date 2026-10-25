# Does the human two-state preference survive trial-level latency and scale variation?

Design, revision 7 — 24 October 2026, session R052 Entropy SI. Status: S2 COMPLETE ON W2, T1/O1 READINGS PENDING;
FOR THE CODEX S3 FREEZE REVIEW. Rev 5 (RSC 0ddac98) received FAVOURABLE WITH CONDITIONS
(`reviews/2026-10-24_design_v5_codex_review.md`); rev 6 closed its four conditions and was the specification S1–S2
implemented. Revs 1–4 (960e93b, 57c1280, 8d6c195, 78e348c) and their reviews are the record of how it got here.
Rev 7 records what S2 found and changed (`S2_REPORT.md` is the evidence): the rev 6 fitter read 6 of 19 graded (W2)
development sets POSITIVE — false two-state calls — and the diagnosis found four defects: D1 the SHARED Ledoit–Wolf
training-catch Σ (the §4 claim "no model-independent direction of bias" was false under shrinkage: the compressed
template-direction variance is absorbed by the occupancy law better than by the graded scale law); D2 the four §5 starts
missing optima by up to 22 nat; D3 template coordinates running off along flat directions, −∞ warm starts and a lossy
acceptance rule; D4 the EM chain stopping on a failed inner solve and leaving G under-found; D5 the generator fits
degenerating under a free 53 × 53 Σ (they stay on Ledoit–Wolf, §7.1). The repairs are in §4 (Σ
by maximum likelihood inside each model), §5 (starts, box, acceptance, the EM loop), §7.1 and §8 (re-cost); the limitation
they expose (strength-dependent latency recovery under a free Σ) is in §7.5 and §10. Under the rev 7 fitter the W2
development block reads 0 POSITIVE, 8 NEGATIVE, 2 UNRESOLVED (R = 10; 0/1000 nesting violations). What rev 7 does NOT
change: the algebraic estimand (§6: the mean over participants of S_B3 − S_G3), the manifest and pass conditions (§7.3),
ε and the λ path (§7.4), the recovery flags (§7.5). What it changes about the estimand's MEANING is declared in §6: each
fitted density now carries its own maximum-likelihood Σ, so the contrast compares complete predictive models with
separately fitted noise (Codex S3 review 24 Oct, finding 1).

## 0. Stages and what is frozen when

S1  Provisional implementation; per-participant GENERATOR fits (§7.1: G3, B3 and B0, full data, whole epoch).
    Parameter values may be inspected; no cross-validated contrast is computed on real data.
S2  Development on development seeds (W2, T1, O1 at R = 25); numerical repairs (rev 7 declares them: §4 Σ, §5 starts,
    box, acceptance, EM loop); the §4 quadrature, support, rank and small-spread checks; the start-basin report; the
    profile-start validation of §5.
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
- Residual covariance Σ (W × W): estimated by MAXIMUM LIKELIHOOD INSIDE EACH MODEL (rev 7, S2 repair R1), not shared.
  Each candidate fit (G2, G3+, B2, B3+ and every constrained or generator fit) runs a generalised EM outer loop around
  the L-BFGS-B solve: M-step Σ = (1/n) Σᵢ E_post[(yᵢ − μ0 − g m T̃_τ)(·)ᵀ] with the per-(trial, τ node)
  responsibilities and E[g], E[g²] on the adaptive quadrature nodes (two-state: the low branch contributes rᵢrᵢᵀ);
  μ0 stays the training-catch mean anchor; the loop starts from the scaled sample catch covariance S × n/(n−p−2) (the
  KL-optimal scalar multiple of the sample covariance; Ledoit–Wolf kept for the record only), runs at most 8 steps to a
  1e-6 relative gain, is strictly monotone (§5), and the fit carries its own Σ; HELD-OUT trials are scored under the
  model's own (μ0, Σ). The zero-boundary selection compares final log-likelihoods, each at its own Σ. Why (S2, W2 set 1
  oracle test, `S2_REPORT.md` D1): with one shared Σ from ~115 catch trials in 16 dimensions the whitening alone cost
  0.88 nat/trial against the true density, the estimated Σ under-stated the variance along the template direction by
  13%, and the two-state occupancy law A(k) absorbed that level-independent excess better than the graded scale law
  a(k)²(r − 1) did — a systematic advantage for B at the LOW levels on graded data (+0.0058 nat/trial, 16/20
  participants) that no part of §6 or §7.4 absorbs. Under the oracle Σ the same set read NEGATIVE. The rev 6 sentence
  "Σ has no model-independent direction of bias" is withdrawn. Declared consequence (§7.5, §10): with Σ free inside
  the model, latency recovery is strength-dependent — on the weakest responder (S4, strength 0.44) the free Σ absorbs
  the jitter-induced variance and the fitted spread collapses (median 15 ms vs 63 true) where the oracle Σ recovers it;
  the recovery battery measures this (R1–R5 carry the strength covariate), and three Σ-structure options for the
  recovery ESTIMAND are left to the S3 review, not decided here: (a) profiles and recovery with Σ held at the
  unrestricted fit's EM value; (b) a factor-structured Σ (diagonal + rank-k); (c) Σ estimated under the graded fit and
  shared by both families for the recovery estimand only. Reported before the contrast is read: held-out catch
  whitening diagnostics under each model's Σ (mean, covariance, excess kurtosis and a normality test of the whitened
  catch residuals projected on T̃), level-stratified training residual second moments under each fitted model, and the
  common-covariance sensitivity D·R(ρ)·D (D = per-window training catch residual SDs; R(ρ) AR(1), ρ ∈ [0, 0.999] by
  ML on the same residuals; one matrix for both families). Σ is challenged by O5 rather than argued. Residual of D1
  under the per-model Σ (S2, W2 block): participants built on the strongest responder (S19: strength 2.32, s_g 0.76)
  still give B3 a held-out edge of +0.003 to +0.006 nat/trial with small training gaps on every fold — the two-state
  family's declared flexibility (a point mass at zero plus a lognormal high branch approximating a wide lognormal
  amplitude law), which moves set means by at most +0.0005 and produced no POSITIVE set.
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
  change the parameter dimension, so no reduced model is needed); the scale integral uses an ADAPTIVE Gauss–Hermite
  rule with 17 nodes in log g, centred and scaled at the posterior mode of each (trial, τ node) by four Newton steps
  (rev 7, as implemented in `models.py`; the rev 6 text's prior-centred 7-node rule produced a false two-state call
  on graded data in S2 and is kept only as the comparison arm of the §4 node check). Measured envelope against a fine
  trapezoid, worst case per (trial, node): 8e-6 nat for s_g ≤ 0.6, 2e-4 at s_g = 1.0, 7e-3 at the s_g = 1.5 box edge
  (fitted real s_g 0.14–0.77); the node check of §7.7 compares 17 against 33 nodes (and the 7-node prior rule) on a
  development set under the declared contrast tolerance, and 33 is adopted if 17 fails it. TWO-PASS RULE (declared
  25 Oct, for the Codex S3 re-review; `models.QUAD_G_RULE = "17then33"`, default `"17"` = the rule above unchanged): every
  fit runs at 17 nodes; afterwards each fitted scale-free model whose fitted s_g exceeds 0.6 is refitted at 33 nodes by
  one EM chain warm-started from its 17-node optimum under its own Σ, and the refit replaces it everywhere downstream
  (selection, held-out scores at 33 nodes, archive); the threshold is the envelope's 8e-6 nat per trial-node bound for
  s_g ≤ 0.6, not a development result; `FitCache.key` carries the rule and every result json records it with the refit
  counts per model. Its check (`s2.py checks --kind twopass`; `results/s2/checks/twopass_g_W2_set0.json`, Mac, 25 Oct):
  W2 set 0 under the rule against the 33-node reference of the 24 Oct node check (`delta3_new` of
  `nodes_g33_W2_set0.json`, AWS checks host) FAILED — max |Δ₃(two-pass) − Δ₃(33)| 3.70e-3 against the tolerance
  8.83e-5, four participants over it (m12 +1.8e-4, m14 +6.2e-4, m15 −3.7e-3, m18 −5.1e-4); 193 of the 400 candidate
  fits (48%: fitted s_g median 0.59, maximum 0.91 on this graded set) were refitted, each moving its training
  log-likelihood by +0.002 to +0.11 nat; the set primary stayed NEGATIVE under 17, 33 and the two-pass rule. Cost: the
  warm refits added 1.5% to the fit seconds within the run (task seconds 12,635 against the archived 17-node 12,524 on
  the same Mac), against about 1.9 for blanket 33. The rule is NOT validated by this check. Two of the four exceedances
  (m14, m18) are participants with no fit above the threshold, and the reference's own 17-node Δ₃ differs from the Mac's
  archived 17-node Δ₃ by up to 4.1e-3 (m15; also m0, m7, m12, m14, m18 above the tolerance), so the comparison carries a
  fitter and host difference as well as the quadrature: Codex traced the m15 swing to the fitter (a near-optimal B warm
  chain ending NOT_CONVERGED after 12 iterations and discarded; `reviews/2026-10-25_latency_quadrature_fix_codex_review.md`,
  findings 1, 4, 11). A separate repair job owns the next step; the declared 0.4 retry was not run. Fits at the s_g bound are
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
  ms/100, amplitudes in decoder units, logits unit). The optimiser objective is the negative MEAN log-likelihood per
  training trial (S1 choice: on the summed objective the 1e-5 gradient threshold sits at the float64 floor); archived
  and reported log-likelihoods are totals in nat. The two-state log-weights log A / log(1 − A) are evaluated in
  softplus form (S1 choice: sigmoid saturation gave NaN gradients). Σ is Cholesky-whitened for each EM step (§4); for
  each τ node the whitened template v_τ = Σ^{-1/2} T̃_τ is recomputed when template parameters change; for whitened
  data u_i,
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
  a non-positive slope, κ = 1 per level unit and x0 = 2.5. Nuisance starts by model: G0/B0: {T_A, T_B} ×
  {amplitudes as computed, amplitudes × 0.5}; G1/B1 positive-spread: {T_A, T_B} × s_τ ∈ {20, 40 ms}; G2/B2: {T_A,
  T_B} × s_g ∈ {0, 0.4}; G3/B3 positive-spread: T_A × {(20, 0), (40, 0.4)}, T_B × {(40, 0), (20, 0.4)}. The REDUCED
  candidate of G3/B3 IS a G2/B2 fit (free scale) and uses the G2/B2 recipe; the reduced candidate of G1/B1 is G0/B0.
  A reduced fit is computed once per participant, fold and data identity and cached wherever it is needed (as a model
  in its own right, as a boundary candidate, as a profile point at s_τ = 0, as a c₀ component).
  THE REPAIRED START SET (rev 7, S2 repair R2; `S2_REPORT.md` D2 and §7). The four design starts miss optima: a
  template fitted to the level-5 mean — which is the jitter-BROADENED template — slides to s_τ = 0, and on the W2
  development block the design starts alone would have missed the positive-spread optimum on 31% (G3+) and 41% (B3+)
  of fits, by up to about 1,000 nat. The recipe is therefore the UNION, for every positive-spread fit: the four design
  starts + four SMEARED-kernel template starts (non-negative least squares of the basis smeared by the truncated-normal
  latency kernel at s ∈ {20, 40, 80, 120} ms, all J columns, to the raw (T_A) and smoothed (T_B) level-5 response
  alternating, s_g = 0.4 where the model has a scale term) + the cached reduced fit LIFTED at 20, 40 and 80 ms + for the
  B family the selected G fit COLLAPSED onto B (A → 1 at every level: κ = 50, x0 = −5). Reduced B fits add the G twin's
  collapse to their four design starts. Every B candidate ALSO runs a warm EM chain from its G twin's own (θ collapsed,
  Σ), so that l(B) ≥ l(G) holds by construction in the joint (θ, Σ) space; a B optimum more than 0.05 nat above its G
  twin re-seeds G (B's θ projected onto G, one EM chain under B's Σ; the better G kept) and B re-chains from the new G.
  S2 usage on W2: the smeared starts win the first stage most often (G3+ 61%, B3+ 53%), the lifts 7–8%, the collapse
  11–17% for B; the warm and re-seed chains supply the selected optimum in 30–43% of fits; G2 never needed more than
  its design starts. This union is the recipe FROZEN at S3 for all models alike; the rev 6 development starts (broad
  template, near-collapsed) are subsumed by the collapse and smeared families.
- Constrained (profile) fits, §7.5: s_τ fixed at a grid value; the parameters are the full positive-spread vector
  minus s_τ (or the reduced vector at s_τ = 0). Starts: TWO per constrained fit — the unrestricted MLE of the same
  model (warm start) and the T_B start with the grid value's nearest §5 nuisance start. Warm-start LIFT when the
  unrestricted solution is REDUCED (it has no shift-only coefficients): keep every fitted visible coordinate and
  supply the four shift-only coefficients from the floored T_B initialisation (deterministic). At the s_τ = 0 profile
  point, a positive-spread warm start is PROJECTED onto the reduced coordinates (shift-only coefficients dropped).
  Every lift clips to the target box and refuses a non-finite start (rev 7, repair R3: under rev 6 a coefficient that
  had run below the softplus floor was packed as −∞ and every profile warm start was discarded at iteration 0, so the
  rev 6 benchmark's profile timings and intervals were effectively one-start).
  This is a declared exception to the four-start rule, VALIDATED in S2 on a frozen subset: 100 development
  participant-datasets per family drawn from the W2 and T1 development sets, every grid point of every profile,
  2-start versus 4-start constrained optima agreeing to 1e-6 relative in objective AND to 0.05 on the
  likelihood-ratio scale q(s); if either tolerance fails at any point, profiles use 4 starts and §8 is re-costed
  before S3.
- Box on the template coordinates (rev 7, repair R3): γ_j ≥ −30 for every coefficient (c ≥ 1e-13). Without it L-BFGS-B
  ran coefficients that want to be zero off along the flat direction (archived W2 set 1: median per-fit minimum γ −75,
  43 of 194 fits below −700, worst −1.9e6) and softplus underflowed to exactly zero.
- Acceptance (rev 7, repair R3): a START's result is the best end point among its attempts that satisfy (i)
  projected-gradient infinity norm ≤ 1e-5 in scaled units and (iii) finite objective and parameters; it is CONVERGED
  when that end point also satisfies (ii) relative objective change over the last 5 iterations ≤ 1e-9, or when it was
  reached in fewer than 5 iterations (a warm start at an optimum) and the perturbed re-run and the retries found
  nothing better than it by 1e-8 relative. Fewer than 5 iterations = EARLY → one re-run from the start perturbed by
  N(0, 0.1²) in scaled coordinates; iteration cap 2,000; at most two retries from re-seeded perturbed starts while the
  start is not yet CONVERGED. A worse retry never replaces a better stationary end point (rev 6 let it, and discarded
  exact warm starts whose perturbed re-run landed in another basin). A model whose starts leave no CONVERGED fit is
  UNAVAILABLE for that participant and fold. The best CONVERGED objective is selected; every attempt's end point and
  status is archived.
- The EM loop (rev 7, repairs R1 and D4): from the multi-start optimum under the starting Σ, at most 8 steps of
  {Σ M-step, re-whitening, one warm-started inner L-BFGS-B solve from the current θ}, ending when the total
  log-likelihood gains less than 1e-6 relative or would decrease (the adaptive quadrature's nodes move with Σ, so the
  E-step and the likelihood are not exactly consistent near convergence; a decrease, however small, ends the chain at
  the previous point). An inner solve that ends NOT_CONVERGED does not end the chain: its best finite end point is
  accepted as a generalised-EM ascent step whenever it raises the total log-likelihood (the Σ M-step is exact; the
  θ-step need only not decrease the objective), and otherwise the solve is retried once from the chain point with four
  times the iteration budget before the chain stops. Under rev 6 + R1–R3 the chain broke at the first failed inner
  solve and left G at its starting-Σ optimum on 11 of 900 development folds (D4: one fold 388 nat below B with a
  +18.6 nat held-out excess); under rev 7 no development chain ended that way (35 ascent steps accepted, all
  improving; `S2_REPORT.md` §4.2). Every EM step is archived as a start of the fit.
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

Prediction target under rev 7 (Codex S3 review 24 Oct, finding 1). The field mean(S_B3 − S_G3) is unchanged in form,
but the densities it compares have changed substantively: each model carries its own maximum-likelihood Σ (§4), so
S_{s,B3} − S_{s,G3} compares two COMPLETE predictive models with separately fitted noise — including their different
predictions for held-out catch trials — and a gain is not isolated evidence about occupancy conditional on one fixed
noise model. The decomposition D, D_scale, D_τ below likewise includes the re-estimation of Σ after each nuisance term
is added. §9's wording carries this qualification.

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
    and B0 beside it; (iii) joint Δ_0 on the primary span on its own available roster: POSITIVE / NEGATIVE /
    UNRESOLVED / UNAVAILABLE (≥ 16); (iv) Δ_0 ON R6, the same roster as D, D_scale and D_τ: POSITIVE / NEGATIVE /
    UNRESOLVED / UNAVAILABLE. The ATTENUATION PREMISE of §9 uses (iv), never (iii), so that the initial advantage and
    its attenuation are measured on one cohort; the residual Δ_3 on R6 is reported beside it.
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
whole-epoch template support, μ0 and the 53 × 53 Ledoit–Wolf Σ from all catch trials: G3, B3 and B0 (the §5 start
set). The generator fits do NOT use the per-model EM Σ of §4 (rev 7, S2 finding D5): under a free 53 × 53 Σ
estimated from about 900 trials the S10 G3 generator fit returned s_τ 24.7 ms and s_g 0.00 against 82.2 ms and 0.56
under Ledoit–Wolf, with B3 collapsed onto G3 — in 53 dimensions the full covariance absorbs the trial variability the
generators exist to carry. The generator fit names the Ledoit–Wolf whitening explicitly (the fitter's default
whitening is the scaled sample covariance, which is only the EM start of §4), refuses an EM cache, and a benchmark
never replaces the stored generator files. The stored generators (`results/generators/`, S1) carry exactly this
Ledoit–Wolf Σ (S10: shrinkage 0.059 from 152 catch trials) and are the configurations every S2 and S4 batch draws from. These supply every synthetic configuration (a, T̃, κ, x0, s_τ, s_g, μ0, Σ) in 53 dimensions, so synthetic data
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

### 7.3 Final-validation manifest (S4b; per fold the FOUR candidate fits that define the selected G3 and B3 — the
reduced candidates G2 and B2 and the positive-spread G3 and B3 — under the §5 union start set and EM loop (rev 7:
about 165 first-stage starts and about 310 archived solves per participant-dataset in place of rev 6's 80 starts;
cost is measured per participant-dataset, §8). G0/B0 are NOT fitted in the decision batch, because every decision
setting needs Δ_3 only; Δ_0 is fitted where it is required: the ε benchmark (§7.4, G0/B0 only) and the real data (§6).)
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
Count: 9 × 100 + 3 × 50 + 100 = 1,150 sets, 23,000 participant-datasets (rev 6 counted 1.84 M starts at 80 per
participant-dataset; rev 7 costs the batch per participant-dataset from the measured rate, §8).
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
  exact hits: among several pilots whose MC interval contains the target, the one with the larger λ is selected
  (tie-break declared); a direct hit has no bracket, so if its certification fails there is NO secant correction and
  the setting is UNCERTIFIED;
  bracket (when there is no hit): the adjacent remaining pilot pair whose estimates straddle the target; among
  several, the pair with the larger λ; fewer than two remaining pilots or no bracket → declared SEARCH FAILURE (the
  setting is UNCERTIFIED; (e) or T3 absent; this is failure of the declared search, not proof that no λ attains the
  target);
  interpolate linearly in λ between the bracket's two (λ, r) points; certify at R_ref = 50 fresh calibration seeds:
  CERTIFIED if the certified MC interval lies within target ± 0.15 ε (for E1 this places it inside [1.10, 1.40] ε,
  above ε by construction). An UNAVAILABLE certification reference (§7.4 rule) is UNCERTIFIED with no correction. A
  certified estimate whose interval contains the target but is too wide to lie within ± 0.15 ε is a PRECISION
  FAILURE: UNCERTIFIED, no correction (the correction is for a missed target, not for MC width);
  otherwise ONE secant correction: the two points are (λ_cert, r_cert) and whichever bracket endpoint lies on the
  other side of the target from r_cert (if both are on the same side, the nearer endpoint); if the secant slope is
  zero or the proposed λ leaves (0, 1], SEARCH FAILURE; re-certify at R_ref = 50 fresh seeds under the same rule;
  failing that, UNCERTIFIED. Both certification attempts are reported. Because two attempts are allowed, each
  certification interval uses the 97.5% level (t_{0.9875}) so that the stated nominal 95% confidence covers the
  pair; the t interval is nominal for the set-score distribution, not exact.
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
  ℓ_prof(s) the constrained optimum at s_τ = s (reduced model at s = 0; §5 constrained starts). Reference rule: if
  any constrained optimum (grid point or bisection midpoint) exceeds ℓ̂, ℓ̂ is replaced by that value, the
  unrestricted fit is flagged, and EVERY previously computed q, including q(0), is recomputed against the new ℓ̂; no
  stale acceptance label is retained. If that recomputation changes the acceptance of a grid point whose endpoint
  bracket has already been refined, the profile is UNAVAILABLE (declared; this preserves the fixed 15-constrained-fit
  budget rather than restarting the search). Grid {0, 5, 10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150} ms. Accepted
  points: q(0) ≤ c₀ (family-specific boundary critical value) and, for s > 0, q(s) ≤ χ²₁(0.95) = 3.841. Interval:
  the CONSERVATIVE OUTER HULL of the accepted set — lower bound = the largest rejected grid point below the smallest
  accepted point (or 0 if 0 is accepted), refined by one bisection between them (midpoint rejected → the rejected
  endpoint moves to the midpoint; accepted → the rejected endpoint stays); upper bound symmetric (150 if 150 is
  accepted). Disconnected accepted sets are reported as such and hulled (an accepted zero is never discarded by a
  search near the MLE). Empty accepted set → UNAVAILABLE profile (flagged). A constrained fit UNAVAILABLE at any grid
  point or midpoint → UNAVAILABLE profile. "Lower bound > 20 ms" is evaluated on the hull's lower bound. The hull is
  conservative with respect to the sampled crossings; it is not an exact inversion over every real spread (unseen
  accepted islands between rejected nodes are not excluded), and the fresh-seed gates validate the frozen
  grid-and-hull procedure as such.
Boundary critical value c₀ (per family), S4a, its OWN batch: 500 datasets per family from the (0, fitted) zero-jitter
  generator on the fixed roster (25 per configuration), two fits each — the positive-spread candidate and the reduced
  fit — giving the non-negative statistic q(0) = 2[max(ℓ_reduced, ℓ_positive) − ℓ_reduced] (a positive candidate worse
  than the reduced fit contributes 0, never a negative value); c₀ = the empirical 95th percentile (type-7 quantile)
  over AVAILABLE q(0) values; if more than 5% of the 500 are UNAVAILABLE, c₀ is UNAVAILABLE and every profile is
  UNAVAILABLE. c₀,G and c₀,B are frozen by commit before S4b. The S4b recovery batch never re-estimates c₀.
Statistics per configuration, setting, family, over AVAILABLE replicates: median relative bias of ŝ_τ; RMSE =
  sqrt(mean(ŝ_τ − s_τ)²); boundary-hit frequency; interval coverage; completion fraction. A configuration × setting
  with more than 20% UNAVAILABLE point fits or profiles FAILS that setting.
Declared expectation (rev 7, from the S2 recovery check, `results/s2/diagnosis/recovery_check_em_oracle_scaled.txt`):
with Σ free inside the model (§4) the latency estimand competes with Σ for the jitter-induced variance along the
template, and recovery is strength-dependent — on the strongest four of five checked configurations the EM-Σ fit
matches the oracle-Σ fit (S10 78/82/82 true ms, S13 53/51/54, S20 39/38/42, S2 59/72/67), on the weakest (S4, strength
0.44) it collapses (15 vs 68 vs 63). R1 ("the SAME ≥ 15 of 20 configurations") therefore carries real risk at the weak
end of the roster; the battery measures it rather than the design assuming it away, and the three Σ-structure options
of §4 are the declared remedies if R1 fails, to be weighed at the S3 review.
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
     paper may report rejection of the tested zero-jitter explanations ONLY for participants whose real hull lower
     bound exceeds 20 ms — the same event R3 validated under all five zero-jitter challenges — and must describe
     the above-20 ms magnitude as a nominal profile inference, not a calibrated bound. A real hull that merely
     excludes zero (lower bound in (0, 20]) licenses nothing under any flag: zero exclusion by itself was not
     validated under O1/O2 (a procedure returning ŝ_τ ≈ 10 ms with hull [2.5, 15] on every zero-jitter O1 replicate
     passes R2 and R3), and c₀ was calibrated at (0, fitted) only. This case is a `decide.py` branch test.
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

MEASURED (rev 7). The rev 6 design priced everything at an unmeasured 30 s/start. Two benchmarks replaced that:
`results/bench/bench_20261024T044019Z.md` under the rev 6 fitter (1.69 s per decision-batch start; S4 = 1,536 core-h
base, 1,915 with re-certification and 4-start profiles; S2 66; real data 9) and the rev 7 benchmark run alone after the
W2 development block on 24 Oct (`results/bench/bench_20261024T171350Z.md`; counted per fit in
`results/bench/recost_rev7_20261024T171350Z.md`, because every rev 7 fit archives its EM steps and chains as starts
and a per-start costing understates it): decision participant-dataset 289 s sequential (rev 6: 135 s), recovery
full-data dataset 82 s, constrained profile fit 6.8 s (2-start) / 14.0 s (4-start), ε dataset 1.8 s, c₀ pair 38 s;
S4 = 3,307 core-h base, 4,160 with re-certification and 4-start profiles; S2 136; real data 20. On the Mac's 12
performance cores the development block ran 2.08× slower than sequential (600 s per decision dataset), so the Mac's
own S4 is about 5,300 core-hour-equivalents and about a month of wall time; a cluster with one real core per worker
sits between. Target instance: c7a.24xlarge = 96 REAL cores (AMD Zen 4, one core per vCPU; an earlier 48-core
conversion was wrong). Contingency: both E1 and T3 may need one secant correction (§7.4), so the worst case budgets
TWO 50-set corrections: S4 = 3,307 core-h base, 4,240 worst (`recost_rev7.py`, 24 Oct; the 4,160 figure budgeted
one). Ideal instance-hours 34.4 base / 44.2 worst; at the design's USD 1.7/h about USD 59 / 75, at the 24 Oct spot
quote (USD 0.73–1.04/h over seven days, cap 1.20, estimate 0.95) about USD 33 / 42, before barriers, start-up,
contention and interruptions. MEASURED ON AWS (24 Oct, the S2 closure fleet; S2_REPORT 9): the per-core arithmetic
does not apply to this host. One decision task alone on the c7a.24xlarge's AMD EPYC 9R14 core takes 1,513 s (3.5× the
M4 core alone); 96 single-threaded workers per host thrash (in 95 min only the lightest participant finished, at
500-5,000 s); at 48 workers per host the host delivers about 60-70 decision tasks per hour, about one Mac, bound by the
socket's shared memory bandwidth and not by its cores; the XLA single-thread code-generation flag costs a further 30%
and is not used. RULE for S4: 48 workers per c7a.24xlarge, no `XLA_FLAGS`, the fleet costed per host. S4 base ≈ 41,000
decision-task-equivalents ≈ 600-700 host-hours (30-35 h on 20 hosts) = about USD 600 on eu-north-1 spot alone (0.95/h;
needs the Spot quota raised 512 → 2,048 vCPU) or about USD 2,400 with 15 of the 20 hosts on-demand (4.93/h) under the
standing 512 Spot + 520 On-Demand vCPU quotas per region; us-west-2a spot was reclaimed wholesale on 24 Oct, eu-north-1b
held. Inherited Nelder–Mead runs measured at
22 ms/run, spm_BMS at 0.04 s/call. The start-count accounting below is the rev 6 record of WHAT is fitted; its unit
costs are superseded by the measured rates.
- Candidate accounting: "the eight models" on real or recovery data = G0, B0, G2, B2 (reduced, each one fit) plus
  positive-spread G1, B1, G3, B3, with G1/B1/G3/B3 selected against their cached reduced candidates: 8 fits × 4 starts =
  32 starts per dataset, reduced fits cached and never refitted. The decision batch (§7.3) = G2, B2, G3+, B3+ = 80
  starts per participant-dataset. The ε batch = G0, B0 = 40 starts. Generator fits (S1) = G2, G3+, B2, B3+, B0 = 5 fits
  = 20 starts per participant.
- Real data, Mac (free): CV fits 20 × 32 × 5 folds × 2 spans = 6,400 starts; generator fits 20 × 20 = 400;
  unrestricted real full-data fits 20 × 32 = 640; real profiles 20 × 2 families × 15 constrained × 2 starts = 1,200;
  sensitivities (±250 support, inherited mean laws, D·R(ρ)·D, floor, s_g bound, whole-epoch contrast) ≈ 4 × 6,400 =
  25,600 starts if all are run; total ≈ 34,200 starts ≈ 285 core-h (several days on 12 Mac cores; the sensitivities
  can also go to AWS at ≈ USD 4 each ideal).
- S2 development (Mac where possible, else AWS): three 80-start batches at R = 25 (W2, T1, O1) = 120,000 starts; the
  profile-start validation on the frozen subset of §5: 2 families × 100 datasets × 13 grid points × 4 starts = 10,400
  constrained starts (the 2-start subset reused within them); start-basin and numerical experiments ≈ 20,000 starts.
  ≈ 150,000 starts ≈ 1,250 core-h.
- AWS, S4a: ε 50 × 20 × 40 = 40,000; pilots 5 × 20 × 20 × 80 = 160,000; certification 2 × 50 × 20 × 80 = 160,000;
  re-certification contingency 160,000; c₀ batches 2 families × 500 × 2 fits × 4 = 8,000. Subtotal 368,000 starts
  (528,000 with the contingency).
- AWS, S4b: decision manifest 23,000 × 80 = 1,840,000; recovery 26 settings × 25 × 20 × 32 = 416,000; recovery
  profiles 26 × 25 × 20 × 2 families × 15 constrained × 2 starts = 780,000 (1,560,000 if the §5 profile-start
  validation fails and 4 starts are required); inherited pipeline 950 sets × 20 × 795 = 15.1 M Nelder–Mead runs ≈
  587 core-h plus 950 × 53 = 50,350 BMS calls ≈ 14 core-h. Subtotal 3,036,000 starts (3,816,000 at 4-start profiles).
- Totals (AWS, S4a + S4b): 3,404,000 starts ≈ 28,370 core-h + 600 inherited ≈ 29,000 core-h (2-start profiles, no
  contingency); ≈ 30,300 with the contingency; ≈ 36,800 with 4-start profiles and the contingency. S2 (≈ 1,250
  core-h) and the real-data work (≈ 285) are in addition and run on the Mac where its calendar allows.
- At c7a.24xlarge (96 vCPU) and the October spot rate ≈ USD 1.7/h: ≈ USD 510–650 at perfect utilisation; ≈ USD
  920–1,170 at 70% utilisation with a 25% retry reserve; on-demand (≈ USD 5.3/h) ≈ USD 1,600–3,600.
- Before launch: benchmark one participant's full §4 set, a profile (both start rules), a generator fit, a c₀ pair
  and the inherited pipeline including BMS on the Mac and on the target instance (steady-state value + gradient to
  convergence from all starts; completed-dataset throughput at 96-way concurrency; compile time separately); cost
  the frozen manifest from measured rates in starts and runs; set the ledger row cap (Unimog
  `rsc_t1_simulation_design.md` §12 row 24) from that number; confirm headroom under the USD 3,000 AWS cap from the
  R052 spend trail; put the number to the owner. DONE 24 Oct: the Mac benchmark (`results/bench/`), the AWS probe and
  the closure fleet's throughput (the MEASURED ON AWS paragraph above); row 24 caps S4a + S4b at USD 1,300; the owner
  was given the measured rate and the fleet options on 24 Oct (20:20Z and 21:14Z).
- Declared reduction order if the measured cost exceeds the approved cap: (1) starts 4 → 3 in validation replicates
  only if S2 shows the fourth start never changed the selected optimum; (2) merge O3 and O4; (3) T2 to
  development-only; (4) recovery R 25 → 15 with thresholds unchanged and reduced precision stated; (5) profile grid
  13 → 9 points with the hull rule unchanged. Never: R below 100 at graded settings or E1, removal of O1/O2/O5,
  coarser quadrature than §4 licensed, skipping certification or the c₀ batch, or dropping R5. Any reduction
  re-validates on fresh seeds. If the cap still cannot be met, the licence narrows (ADEQUATE-ZERO-ONLY is the
  declared narrower identification claim) or the study stops.
- TIME-PRIORITY AMENDMENT (24 Oct 2026, recorded before any S4 draw; Codex S3 review finding 13). The numbered order
  above is for a cap breach. If the owner's submission window, not the cap, forces a reduction, the order is: FIRST T2
  to development-only (reduction (3): report-only, about 80 core-h, no gate or flag weakened); SECOND T3's S4b
  report-only reading deferred to a declared follow-up after first submission, with its S4a search and certification
  of λ_T3 retained as specified and its S4b power and coverage labelled pending in the paper. Everything else stays:
  W1–W4, O1–O5, T1, the instantiated E1, the own c₀ calibration and R1–R5 before the corresponding predictive and
  identification claims, and the W1/W3/W4 mechanism comparison before any attenuation attribution. Start removal has
  no measurement licensing it and the O3/O4 merger needs a specified combined generator, so neither is a time
  reduction. A reduced manifest is a predeclared narrower first-submission manifest, validated on fresh seeds, and the
  paper states what was validated. The lever is `s4.py s4b --defer T2[,T3]`, which records the deferral in
  `results/s4/manifest_amendment.json`; `s4.py evaluate` then reports the deferred settings as DEFERRED (declared),
  never as silently absent. At the S4 launch of 24 Oct the amendment was NOT invoked: the full manifest runs.
- Checkpoint per completed dataset for spot retries; one BLAS/XLA thread per worker; JIT with cached shapes.

## 9. What each outcome licenses in the paper

The study replaces the "untested jitter" limitation with a bounded answer; it is the SI's one central empirical
addition. Conditional on the primary licence:
- PRIMARY POSITIVE: "In this auditory dataset, over 255–705 ms, the two-state family retained a positive held-out
  advantage over the matched graded family after both represented trial-level latency and scale variation
  (interval; recovery status; misspecifications tested)." Not: that the published result rests on no artefact, nor
  that every graded account fails. The sentence names what is compared: two complete predictive models, each with its
  own fitted noise covariance (§6); the advantage is not isolated evidence about occupancy under one fixed noise model.
  If RECOVERY is NOT ADEQUATE or JITTER not DETECTED in G, robustness is to a scale
  term and to a latency term the data did not pin down, and the text says so.
- ATTENUATION PREMISE: any sentence about attenuation OF THE INHERITED ADVANTAGE requires Δ_0 ON R6 POSITIVE
  (BRIDGE (iv), the same cohort as D) and D POSITIVE; the residual reported with it is Δ_3 on R6. BRIDGE (iii) on the
  wider roster is continuity information, not the premise. Without the premise, a POSITIVE D_τ is reported only as
  "adding latency after scale reduced the scale-only contrast Δ_2", never as attenuation of the inherited advantage.
- "Not robust to representing trial variability": the premise, with the residual advantage then reported as
  NEGATIVE, UNRESOLVED or BOUNDED (an UNRESOLVED residual is called unresolved even when D is POSITIVE). A NEGATIVE
  primary with BRIDGE (iii) not POSITIVE is "the joint framing favours the graded family", a framing result.
- "Latency variation carries part of the attenuation": the premise, D_τ POSITIVE, RECOVERY ADEQUATE (full, not
  ZERO-ONLY) and JITTER DETECTED in the reference family G, and the W1→W3 RISE. "Latency carries most of the
  attenuation": additionally D_τ − D_scale POSITIVE. The scale analogue: the premise, D_scale POSITIVE, the W1→W4
  RISE. Short of these, attribution is to trial variability of unidentified form. The decomposition is scale-first
  and declared as such. Even then the supported wording is a decoder-readout latency term, not a physiological
  latency.
- Under ADEQUATE-ZERO-ONLY, the paper may say the tested zero-jitter explanations are rejected for the participants
  whose real hull lower bound exceeds 20 ms (the R3-validated event), and reports the above-20 ms magnitude as a
  nominal profile inference. A hull that excludes zero without clearing 20 ms licenses no statement.
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
none about experience. Rev 7 adds: the noise covariance is estimated by maximum likelihood inside each model (§4),
which repairs the systematic two-state advantage of a shared shrinkage Σ but makes latency recovery strength-dependent
(§7.5); the two-state family retains a small declared flexibility on strong responders with wide amplitude spread
(point mass at zero plus a lognormal) that the development block shows at +0.003 to +0.006 nat/trial on single
participants and never as a POSITIVE set. Neither is argued away; both are measured by S4b.

## 11. Files and literature

- This design: `workspace_demo/sergent_port/jitter/DESIGN_jitter.md` (rev 7; rev 1 960e93b, rev 2 57c1280, rev 3
  8d6c195, rev 4 78e348c, rev 5 0ddac98, rev 6 the commit before the S1 build). Codex reviews under `jitter/reviews/`
  (rev 5: FAVOURABLE WITH CONDITIONS). S2 evidence: `jitter/S2_REPORT.md`; records `results/s2/decision_rev6/` (rev 6
  fitter), `results/s2/decision_pre_d4/` (R1–R3 without D4), `results/s2/decision/` (rev 7 fitter),
  `results/s2/diagnosis/` (oracle test, Σ refits, recovery check), `results/s2/checks/` (§4 ranks, small spread).
- Code: `jitter/{data.py, models.py, fit.py, simulate.py, decide.py, bench.py, s2.py, diagnose.py}` with tests under
  `jitter/tests/` (81 tests over four files at rev 7); results under `jitter/results/`.
- Inherited code: `sergent_port/fit_models.py` (likelihoods 60–100, Nelder–Mead 102–110, `window_means` 138–143,
  `block_folds` 118, score 254), `model_comparison.py`, `bms.py`, `README.md`, `RESULTS_sergent.md`.
- Literature (verified in the rev 1 review unless marked): Woody 1967 (Med Biol Eng 5:539); Truccolo et al. 2002
  (Clin Neurophysiol 113:206); Sekar, Findley & Llinás 2012 (Neuroscience 206:167); Navajas, Ahmadi & Quian Quiroga
  2013 (J Neurosci 33:1337); Rutiku, Aru & Bachmann 2016 (Front Hum Neurosci 10:23); Ouyang et al. 2011, 2015
  (RIDE). Sergent et al. 2021's article and supplement have no single-trial latency estimation, realignment or
  simulated jitter control. Bauer & Curran 2003 (Psychol Methods 8:338): statistical precedent for the SI's
  contribution 1 (unverified; to be read before citation). No prior matched held-out comparison of this kind was
  found; no first-ever claim will be made.
