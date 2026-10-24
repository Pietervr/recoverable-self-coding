# Does the human two-state preference survive trial-level latency and scale variation?

Design, revision 2 — 23 October 2026, session R052 Entropy SI. Status: DRAFT for Codex re-review.
Revision 1 (RSC 960e93b) received the verdict NOT FAVOURABLE (`reviews/2026-10-23_design_codex_review.md`);
every finding there is answered below, by section. Nothing has been run. The rule in §6 and the manifest in §7
are frozen by commit before any real-data contrast is computed; "before" means that the generators are built from
fitted parameters without inspecting any held-out contrast, not that the real data are untouched.

## 1. The gap this closes

The SI's one strong completed result: the published two-model comparison of Sergent et al. 2021, carried over
unchanged to synthetic data, called two states in 989 of 12,000 one-state datasets, all at settings whose
generator carried item heterogeneity (SI §r-audit). The paper also reproduces the human result that motivates
the programme (§r-human): the two-state model preferred from 315 ms on 20 participants. That preference was
obtained with the same per-window models, which have no term for trial-to-trial variation. `background.tex` and
`discussion.tex` name the human-side form of the confound (latency jitter of a graded response, Truccolo et al.
2002) and say it is not tested. The 989 false calls concern a different sampling unit, fitting scheme and
decision rule from the human analysis, so they do not by themselves establish that trial variability caused a
published error; this study is the bridge from that caution to the human reference.

It refits the 20 participants with a graded family and a two-state family that are matched in every respect
except whether a trial's response amplitude is one continuous quantity or a Bernoulli switch, and asks whether
the two-state preference survives when both families represent trial-level latency and scale variation. The
answer is a bounded statement about the published statistical comparison under this readout, not about
physiology; §9 fixes what each outcome licenses.

## 2. Why per-window models cannot see jitter, and what can

Each of the 53 windows is fitted separately (`sergent_port/fit_models.py`), so every model describes the
marginal distribution of the decoder distance at one window given the level. A graded response of fixed shape
at a trial-specific latency splits the trials at a rising-edge window into "arrived" and "not yet": a bimodal
marginal from one state. The information separating that from a true mixture is the same trial's values at
the neighbouring windows, outside every per-window likelihood. A trial-level latent latency shared across
windows is needed, identified from the whole single-trial time course. The derived files carry it:
`brain_data/sergent2021/derived/S{n}_{session}_preds.npz`, `preds` n_trials × 1250 samples at 2 ms (S10
active: 930 × 1250, levels 1–6 with 152/158/157/156/155/152 trials, blocks 1–20 in `trialinfo[:,0]`; the
stored `fold` is the decoder fold, not the likelihood block fold). No re-decoding.

Readout-level interpretation, declared. The decoder is a different linear map at every sample (`beta(t)`),
so a shift of the projected trace, `beta(t)·x(t−τ)`, is not the same as a shifted neural source,
`beta(t−τ)·x(t−τ)`. A fitted latency here is a property of the decoder-distance time course, not the latency
of one source. The adversarial generators of §7 include shape variation for that reason, and a fixed-spatial-
decoder check is named in §10 as follow-on work, not part of this study.

## 3. Data and preprocessing (inherited, unchanged)

- Participants S1–S20; active session primary; passive secondary and deferred (§7 cuts).
- Decoder distance per trial and sample from `decode.py` (liblinear, the committed readout); 10 Hz zero-phase
  low-pass as in `fit_models.lowpass_filtfilt`; the port's 53 window means (`window_means`: 16 samples each,
  centres −285 + 30 i ms). Levels shifted by −1 inside all models, so the catch (no-sound) level is **0**.
- Folds: the port's five block folds (`block_folds`); block 21 always in training, never scored.
- **Primary fitting span: the 16 windows with centres 255–705 ms**, the span over which the article states the
  two-state model's pxp stays above 0.95 ("most of the period between 250 and 700 ms"). The two-state claim lives
  there; the whole epoch contains early graded processing on every trial, which a no-response low state cannot
  carry and which would hand the graded family a win unrelated to state count. Sensitivity: all 53 windows.
- The 10 ms sub-sampled grid of rev 1 is withdrawn from this study (it adds no independent information after the
  10 Hz filter and needs its own joint generator).

## 4. The model families (answers review §1)

Notation: trial i, level k_i ∈ {0..5} (0 = catch), window w ∈ span, observed y_i ∈ R^W, W = 16 (primary).
Everything in this section applies identically to both families unless the line says otherwise.

Shared construction, estimated per participant and fold on training trials only, identical across models:
- Baseline μ0(w): mean of training catch trials. Both families predict exactly μ0 on a no-response trial; the
  rev 1 low-state offset c is removed. A matched baseline-correction sensitivity (one scalar offset applied to
  every branch of both families) is declared, not primary.
- Residual covariance Σ (W × W): Ledoit–Wolf shrinkage on the training catch trials' deviations about μ0, held
  fixed for all models in that participant and fold. Rev 1's claim that template misfit "enters equally" is
  withdrawn: an identical Σ does not make unequal residuals cost the same. §7 therefore carries a covariance
  misspecification generator, and the following are reported before the contrast is read: held-out catch
  whitening diagnostics (mean and covariance of Σ^{-1/2}(y − μ0) on test catch trials), level-stratified
  second moments of the training residuals under each fitted model, and one prespecified common-covariance
  sensitivity (heteroscedastic D·R(ρ)·D fitted once on the same training catch trials, used by both families).
  Σ has no model-independent direction of bias on the contrast; that is why it is challenged rather than argued.
- Level means: a free non-negative response amplitude per sound level, a(k) = softplus(α_k) for k = 1..5,
  a(0) = 0 fixed. Both families carry exactly these five parameters and no other level-mean law. The inherited
  logistic-in-level mean laws (M2's centred logistic, M3's logistic occupancy times logistic high mean) are a
  declared sensitivity, so that the primary contrast cannot be won by a better mean law.
- Template T(t): a positive cubic B-spline on [−150, 1450] ms with knots every 60 ms, coefficients
  parameterised by softmax so that they are positive and sum to one (the scale gauge of rev 1 is removed; no
  max-normalisation and no non-smooth point). The first two and last two coefficients are fixed at zero so T
  vanishes smoothly at both ends; outside the support T = 0. T is the filtered response, so no second filter is
  applied; a window's value is the mean of T evaluated at that window's 16 sample times (`fit_models.py:138`),
  not a point value at the centre. T is fitted separately inside each model with the identical basis,
  support, constraints and training-only initialisation; it is not a shared fitted component. Fitted shapes are
  plotted for every participant; if the contrast depends on them, a common independently estimated template is
  run as a diagnostic.
- Trial latency τ_i ~ N(0, s_τ²) truncated to ±150 ms, marginalised on 31 equally spaced nodes with the
  truncated-normal density as weights (normalised). s_τ ∈ [0, 150] ms is a bounded box parameter, not a log
  parameter; s_τ = 0 is an exact point of the model (one node, weight one). Reported: the parent parameter and
  the realised SD of the discrete distribution (at parent 80 ms the truncated continuous SD is 68.1 ms; the
  31-node discrete SD 69.3 ms). Prespecified numerical checks on development data: 31 vs 61 nodes and ±150 vs
  ±250 ms support must change every participant's score contrast by less than one tenth of the contrast's
  participant-interval half-width, else the finer setting is adopted.
- Trial scale g_i ~ LogNormal(−s_g²/2, s_g²), mean 1, marginalised by Gauss–Hermite quadrature; s_g ∈ [0, 1.5]
  bounded, s_g = 0 exact. Check: 7 vs 15 nodes at s_g = 1.5 under the same tolerance; the larger order is
  adopted if the check fails. g and τ independent, identical across levels, one shape shifted as a whole: these
  are shared restrictions, declared, and challenged by the §7 adversarial generators (level-dependent latency,
  amplitude–latency coupling).

Graded family (one state): y_i | k_i, τ_i, g_i ~ N( μ0 + g_i · a(k_i) · T(· − τ_i), Σ ).
  G0: s_τ = s_g = 0.  G1: s_τ free, s_g = 0.  G2: s_τ = 0, s_g free.  G3: both free.

Two-state family: z_i ~ Bernoulli(A(k_i)), A(k) = lg_{κ,x0}(k) for k ≥ 1 with κ > 0 (log-parameterised, so
occupancy is non-decreasing in level), A(0) = 0 fixed; A(k) is clipped below at A_min = 0.02 for k ≥ 1 and the
clip's activation is recorded per fit.
  y_i | z_i = 0 ~ N( μ0, Σ )                                       (no response; no free offset)
  y_i | z_i = 1, τ_i, g_i ~ N( μ0 + g_i · m_H(k_i) · T(· − τ_i), Σ ),   m_H(k) = a(k) / A(k).
  With this parameterisation the two-state mixture has exactly the same mean response a(k)·E[T(·−τ)] at every
  level as the graded model, so the families differ only in the within-level distribution: a continuous
  (possibly heavy-tailed) amplitude about a(k) versus a two-point switch between 0 and a(k)/A(k). B0–B3 as for
  G0–G3, the nuisance terms applying to the high-state response (a latency is meaningless on a no-response
  trial; none is added).

Catch anchoring, A(0) = a(0) = 0, is a common restriction of both families: it excludes spontaneous
response-like events on catch trials by construction. A free-catch-occupancy sensitivity is declared.

Parameter counts, non-spline: G0 5 (α_1..α_5); G3 7. B0 7 (α_1..α_5, κ, x0); B3 9. Each softmax template has
(number of free coefficients − 1) identifiable degrees. The two extra occupancy parameters are the two-state
hypothesis itself; held-out scoring charges their estimation cost, and no information criterion is added to a
cross-validated score. "Same nuisance terms" is not "same flexibility": §7(b) shows what the extra flexibility
buys under graded generators.

## 5. Fitting

- Maximum marginal likelihood, float64, JAX gradients, L-BFGS-B with the box bounds above. Exact algebra: Σ is
  Cholesky-whitened once per fold; for each τ-node the whitened template v_τ = Σ^{-1/2} T_τ is recomputed when
  spline parameters change; for whitened data u_i the quadratic form is
  q(i, τ, g) = ‖u_i‖² − 2 g a(k_i) (u_i · v_τ) + (g a(k_i))² ‖v_τ‖², so all trial–template projections are one
  matrix product (≈ 1.5 × 10⁶ products per objective at W = 53, fewer at W = 16); the two-state low branch is
  the g = 0 term, combined by log-sum-exp. No residual tensor over quadrature nodes is formed.
- Starts: 4 per fit, computed from the fold's training blocks only (no inherited `fits_*.csv` values, which were
  initialised from all trials): the level means from training level averages over the span, the template from
  the training level-5 mean time course, κ and x0 from a logistic fit to the fraction of training trials above
  the catch 90th percentile, s_τ ∈ {0, 40 ms} and s_g ∈ {0, 0.4} across the four starts so that they differ
  materially in spread, not only by perturbation. Development adds a near-collapsed two-state start (A → 1).
- Convergence standard per fit: projected-gradient norm below tolerance and the best-of-starts objective not
  improved by a fifth start in development; the chain and every start's end point are archived. A fit that
  meets neither standard after two retries is UNAVAILABLE; a participant with an unavailable fit in either
  competitor of a contrast is excluded from that contrast and counted (§6).
- Score. Every out-of-fold trial's log marginal density is summed once over the five folds, then divided once
  by the total number of scored trials (block 21 excluded): S_{s,m} in nat per trial. This replaces rev 1's
  double normalisation; the inherited fold-mean convention (`fit_models.py:254`) is reported alongside for
  continuity only.
- Every fit is logged with data identity, code hash, seeds, bounds hit and retries, so a fit is never silently
  reused across a changed specification.
- Correctness: the whitened objective and its gradient are checked against a direct dense implementation on
  small cases to 1e-10 relative; the quadrature and node checks of §4 are run and archived before the real fits.

## 6. The decision, fixed before any real-data contrast (answers review §4)

Primary estimand: the mean over participants of the paired per-trial held-out advantage
  Δ_s = S_{s,B3} − S_{s,G3}   (nat per trial, primary span),
with its 95% t-interval over the 20 participants (participant as sampling unit; folds are not units). The
protected exceedance probability of B3 over G3 from the inherited BMS is reported beside it as a descriptive
convention only (`bms.py:51` takes model evidences; these are predictive scores).

Precedence (each step ends the evaluation for that level):
1. VALIDITY. If fewer than 16 of 20 participants have available B3 and G3 fits, or any §7 pass condition at the
   primary span is unmet, the primary result is NOT LICENSED and only descriptive summaries are reported.
2. PRIMARY SIGN, a partition: POSITIVE (lower bound > 0), NEGATIVE (upper bound < 0), UNRESOLVED (interval
   contains 0). An UNRESOLVED result is not evidence of absence.
3. ATTENUATION, its own paired estimand: D_s = Δ_s(B0 − G0) − Δ_s(B3 − G3), mean and 95% t-interval; reported as
   POSITIVE / NEGATIVE / UNRESOLVED. "Significant before, non-significant after" is not a test of D and is not
   used.
4. EQUIVALENCE (secondary): a declared margin ε on the joint-score scale. ε is one third of the expected
   B0 − G0 advantage under the fitted B0 generator at the primary span, estimated in the §7 battery by
   independent large test draws before the real contrast is computed and committed with the battery results.
   If the B3 − G3 upper bound < ε the residual advantage is BOUNDED BELOW ε; otherwise NOT BOUNDED.
Flags carried with the result, orthogonal to the partition:
- BRIDGE: (i) the unchanged inherited per-window result (`model_comparison.py`) is the first bridge and stands;
  (ii) held-out per-window marginal predictions of G0 and B0 shown beside it; (iii) the joint B0 − G0 interval at
  the primary span (POSITIVE / NEGATIVE / UNRESOLVED). A non-positive B0 − G0 is reported as informative about the
  joint framing, not as "the study cannot speak".
- RECOVERY: §7(a) outcome, IDENTIFIED / NOT IDENTIFIED. NOT IDENTIFIED forbids attributing any change to
  recovered latency variation; it does not stop the predictive comparison.
- ATTRIBUTION (secondary): G1 − G0, G2 − G0, B1 − B0, B2 − B0, G3 − G0, B3 − B0 intervals; fitted s_τ, s_g per
  participant with recovery-corrected uncertainty.
The script `decide.py` computes all of the above from the fit tables and is committed, with unit tests for every
branch of the precedence, before the real-data fits are launched. Development choices are frozen at that
commit; the battery's final validation runs on fresh seeds after it.

## 7. Calibration and recovery (answers review §§2, 5)

Generation. A synthetic participant has one coherent generating distribution across all five folds, with the
real participant's level and block counts; μ0, Σ, shrinkage, starts and templates are re-estimated within each
synthetic training fold exactly as on real data (nothing generator-side is given to the fitter). Base
configurations are the 20 real participants' G3 (or B3) fits on the primary span; each replicate set resamples
20 configurations with replacement from the 20 (population generator), so the participant interval's
properties are tested over new participants, not a fixed roster. Synthetic data are generated as processed
53-window vectors (the joint models' observation level); the inherited per-window likelihoods and BMS consume
the same vectors directly after `window_means` (no second filter); block structure is preserved by assigning
the real block labels.

Manifest, final validation (fits G0, B0, G3, B3 only; 5 folds × 4 starts = 80 fits per participant-dataset):
  Graded, well-specified (false-POSITIVE bound): W1 G0 fitted; W2 G3 fitted; W3 G3 with s_τ = 80 ms and fitted
    s_g; W4 G3 with s_τ = 40 ms and s_g = 1.0.                                               R = 100 each.
  Graded, out of family (shape/covariance challenge, all zero latency jitter unless stated): O1 template width
    varying per trial (lognormal SD 0.25 on a time-stretch factor); O2 smooth per-trial variation of early/late
    component weights (two fixed components, Beta-distributed mixing weight, no discrete classes); O3 level-
    dependent latency (s_τ = 60 ms at the two lowest sound levels, 20 ms at the highest); O4 amplitude–latency
    coupling (ρ = −0.5 between log g and τ, s_τ = 60 ms); O5 covariance misspecification: G3 fitted means with
    residuals resampled from the real participant's level-stratified training residuals.           R = 100 each.
  Two-state (power and boundary): T1 B3 fitted; T2 B3 with jittered ignition (s_τ = 80 ms) and occupancy halved
    at every level; T3 weak alternative at the setting whose expected B3 − G3 gain (independent large test
    draws) is 1.5 ε; T4 near-collapsed alternative at expected gain 0.5 ε.                      R = 50 each.
  Count: 9 × 100 + 4 × 50 = 1,100 replicate sets, 22,000 participant-datasets, 1.76 M fits.
Pass conditions (uncertainty-based, one-sided 95% binomial):
  (b) false POSITIVE under every graded generator W1–W4, O1–O5: at most 1 of 100 sets (upper bound ≤ 4.7%).
      This is a generating-family classification error, not a type-I error at zero expected advantage; the
      interval's coverage of the procedure-level reference (independent large draws) is reported at W2 and O1.
  (c) power: at T1 at least 45 of 50 sets POSITIVE (lower bound ≥ 80%); T2 reported; T3 and T4 define the
      detection curve near ε (reported, not gated).
  A failed (b) or (c) at the primary span leaves the primary result NOT LICENSED (§6 step 1).
Recovery battery (a), separate and cheaper: all eight models, one training-sized fold per replicate, R = 25,
  generators G3 and B3 at s_τ ∈ {0, 40, 80} ms × s_g ∈ {0, fitted, 1.0} (9 settings each family), plus O1 and
  O2 at zero jitter. Per setting and per participant stratum (high-response / weak-response by fitted a(5)):
  bias, RMSE, boundary-hit frequency and interval coverage of ŝ_τ and ŝ_g; profile marginal likelihood over
  s_τ including 0, re-optimising T, a(k) and s_g at each value, in both families, with ridges against s_g and
  template width plotted. Individual τ_i posterior means are checked against truth on high-level trials and
  reported as secondary; no claim about individual trials is made from population recovery.
  IDENTIFIED requires, at s_τ = 40 and 80 ms with fitted s_g: median relative bias within ±25% and RMSE ≤ 50%
  of the true value in at least 15 of 20 participant conditions, in the family that generated the data; and
  under the three zero-jitter generators (G3 at 0, O1, O2) fitted ŝ_τ > 20 ms in at most 10% of participant
  conditions. Otherwise NOT IDENTIFIED (the flag of §6), and the paper reports measured non-identifiability.
Inherited-pipeline mechanism test (b)(i), run on W1–W4, O1–O5 and T1 sets (the per-window `fit_models.py`
  likelihoods and `model_comparison.py` unchanged after `window_means`): the paper's three summaries — first
  window with pxp₃ > 0.95, first run of ≥ 3 consecutive windows with M3 highest, the Simes set — plus the full
  pxp curve and the per-participant per-window score advantage. The binary "call" for rates is the ≥ 3-window
  run within 255–705 ms; its rate under W1 (no nuisance) vs W3 (latency only) vs W4 (scale heavy) isolates each
  mechanism from matched base parameters. The Simes-on-pxp convention has no established error control and is
  reported as the inherited convention.
Numerical validity: every attempted dataset counted; UNAVAILABLE fits per §5; a set with any UNAVAILABLE
  primary fit is retained and reported with that flag, never silently dropped; optimisation and quadrature
  error must be shown small relative to the contrast on development data before validation seeds are drawn.
Development (Mac, R = 25, W2, T1, O1) precedes and is separate from validation; development seeds are never
reused.

## 8. Compute, venue, cost (answers review §8)

- Real-data fits, Mac (free): 20 participants × 8 models × 5 folds × 4 starts = 3,200 fits (active, primary
  span) + the 53-window sensitivity 3,200 → at a 30 s target ≈ 53 core-h. Passive deferred.
- Final validation, AWS (owner 23 Oct: "we can run in aws"): 22,000 participant-datasets × 80 fits × 30 s =
  14,700 core-h; recovery battery ≈ 1,200 core-h; inherited per-window pipeline on the same sets ≈ 600 core-h.
  At the October spot rate seen on c7a.24xlarge (≈ USD 1.7/h, 96 vCPU, one vCPU per physical core) and
  perfect utilisation ≈ USD 290; at 70% utilisation plus a 25% retry reserve ≈ USD 520; on-demand (≈ USD
  5.3/h) ≈ USD 900–1,600. None of this is measured. The 30 s target is plausible only with the whitened
  algebra of §5, JIT with cached shapes, one BLAS/XLA thread per worker and no per-start recompilation;
  compile time is recorded separately.
- Before launch: benchmark one participant's full §4 set on the Mac and on the target instance (steady-state
  value + gradient to convergence from all four starts, completed-dataset throughput under 96-way
  concurrency), cost the frozen manifest from the measured rate, set the ledger row's cap (Unimog
  `rsc_t1_simulation_design.md` §12 row 24), confirm the headroom under the USD 3,000 AWS cap from the R052
  spend trail, and put the number to the owner. Checkpoint per completed dataset for spot retries.
- Declared reduction order if the measured cost exceeds the cap: (1) starts 4 → 3 in validation replicates,
  only after development shows the fourth start never changed the selected optimum; (2) O3 and O4 merged into
  one coupled generator; (3) T2 dropped (reported from development only). Never: R below 100 at the graded
  settings, removal of the out-of-family controls O1/O2/O5, or coarser quadrature than the §4 checks
  licensed. If the cap still cannot be met, the claimed licence narrows or the study stops; an under-
  calibrated result is not a saving.

## 9. What each outcome licenses in the paper (answers review §6)

The study replaces the "untested jitter" limitation with a bounded answer; it is the SI's one central
empirical addition, not a fourth item. Statements, conditional on VALIDITY:
- POSITIVE primary sign: "In this auditory dataset, the two-state family retained a positive held-out
  advantage over the matched graded family after both represented trial-level latency and scale variation
  (interval; recovery status; misspecifications tested)." It does not establish that the published result
  rests on no artefact, nor that every graded account fails; if RECOVERY is NOT IDENTIFIED, robustness is to
  the scale term and to a latency term the data could not pin down, and the text says so.
- NEGATIVE primary sign, or UNRESOLVED with ATTENUATION POSITIVE and residual advantage BOUNDED BELOW ε: "The
  inherited preference was not robust to a comparison that represented trial variability; the residual
  advantage was [negative / bounded below the declared margin]; graded simulations with [the W3/W4/O
  variation that did so] reproduced [the named features] of the inherited per-window preference." This
  establishes a sufficient statistical alternative under this readout, not the absence of physiological
  ignition and not latency as the unique cause. Attribution to latency requires RECOVERY IDENTIFIED and the
  G1 − G0 / W3 evidence; otherwise the attribution is to trial variability of unidentified form.
- UNRESOLVED without the above: reported as such, with the interval, D, the detection curve from T3/T4 and the
  BRIDGE flags. Not evidence of absence; not a survival.
- NOT LICENSED: descriptive summaries, the recovery result and the mechanism test are reported; no primary
  claim.
In every case the paper reports (b)(i) in full, including the case where latency jitter alone does not
reproduce the late plateau — that is a result, and it would mean the plateau's preference is not a
rising-edge artefact of the kind §2 describes.

Hostile reading anticipated: a better mean law rather than a state test (answered by the shared free level
means); noise or shape variability mislabelled as latency (RECOVERY gate with O1/O2 zero-jitter controls, and
the readout-level declaration of §2); a whole-epoch question substituted for the late-window result (primary
span 255–705 ms); absence claims from non-significance (the partition and ε); a battery built only from the
fitted families (O1–O5); inherited decoder leakage (declared, SI §d-limits, unchanged by this study); novelty
(single-trial latency work is cited, §11; no "first" claim).

## 10. What this study does not do

It changes none of the decoder, folds, windows or inherited per-window models; the SI's reproduction stands as
reported. It does not quantify the inherited design's leakage, and the decoder and likelihood folds remain
non-nested on the saved preds. It tests one nuisance family (latency shift of one template, lognormal scale,
independent, level-invariant) and challenges it with O1–O5; multi-component latencies with independent timing,
non-Gaussian residuals and a fixed-spatial-decoder re-analysis are named follow-on work. The passive session and
the 53-window span are sensitivities. No claim about the language model and none about experience.

## 11. Files and literature

- This design: `workspace_demo/sergent_port/jitter/DESIGN_jitter.md` (rev 2; rev 1 at RSC 960e93b).
- Codex review of rev 1: `jitter/reviews/2026-10-23_design_codex_review.md`.
- Code (after review): `jitter/{models.py, fit.py, simulate.py, decide.py, bench.py}`, tests beside them;
  results under `jitter/results/`.
- Inherited code: `sergent_port/fit_models.py` (likelihoods 60–100, Nelder–Mead 102–110, `window_means`
  138–143, `block_folds` 118, score 254), `model_comparison.py`, `bms.py`, `README.md`, `RESULTS_sergent.md`.
- Literature for the methods text (verified in the review unless marked): Woody 1967 (Med Biol Eng 5:539);
  Truccolo et al. 2002 (Clin Neurophysiol 113:206, cited in the SI); Sekar, Findley & Llinás 2012 (Neuroscience
  206:167 — latency variance and Woody-corrected averages in an all-or-none visual test; the ambiguity also runs
  the other way, jitter can make an all-or-none event look graded in averages); Navajas, Ahmadi & Quian Quiroga
  2013 (J Neurosci 33:1337); Rutiku, Aru & Bachmann 2016 (Front Hum Neurosci 10:23); Ouyang et al. 2011 and
  2015 (RIDE). Sergent et al. 2021's article and supplement contain report-conditioned distribution checks and
  no single-trial latency estimation, realignment or simulated jitter control; report conditioning can itself
  select on timing or amplitude. Bauer & Curran 2003 (Psychol Methods 8:338) remains the statistical precedent
  for the SI's contribution 1 and is not needed for this study's EEG-specific gap (unverified in the review;
  to be read before citation). No prior paper performing this matched held-out comparison was found; the paper
  will not claim first-ever novelty.
