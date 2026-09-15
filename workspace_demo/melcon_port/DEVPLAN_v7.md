# Melcón battery — development plan for the revision after the failed v6 battery (v7, DRAFT rev 2, 15 Sept 2026)

**Status.** The owner gave the go on 15 Sept 2026. The plan was committed before any new diagnostic fit (RSC 1100eb1;
Codex, post-outcome record `t1_access/reviews/2026-09-15_melcon_v6_stage_c_codex_record.md`, RSC e490f3b, Q3 step 1).
**Rev 1** takes in Codex's second opinion on that commit (`t1_access/reviews/2026-09-15_melcon_v7_devplan_codex_record.md`,
RSC e42846e). Its dispositions are in §8, and Phase 1 proceeds from this revision.
**Rev 2** records Phase 1 (§2.6) and takes in Codex's record on the Phase 2 fixings
(`t1_access/reviews/2026-09-15_melcon_v7_phase2_fixings_codex_record.md`, RSC eaea99b): C1 and C1+C2 are withdrawn by
recorded amendment, the fixings are final (§3.1), and the dispositions are in §9.

The v6 battery is retained unchanged as the failed development record (namespace `results/battery/v6-ebaddf98807b/`:
calibration, stage C, verdicts). X1 strong recovered no two-state outcome in either drift condition, and no graded
generator was ever called graded. Everything learned from v6 is **development** evidence.

A locked procedure can at most **pass the declared synthetic acceptance criteria** in a fresh, independent validation
battery; nothing here "certifies" it. Nothing here reads EEG, and nothing is frozen.

## 1. What stays fixed (the comparison baseline)

These stay fixed:
- the secondary analysis's estimand
- the generator laws G1–G3, X1 and X2
- the dose definition and the 34 templates
- the decoder, its halves ((1,2), (3,4)), its windows, and the density folds within each half (one block trains, the
  other is scored, rotated; four folds per recording across the two halves)
- the calibration statistic and the ten calibrated v6 amplitudes
- the group rule: three models, spm_BMS, a run of 3 adjacent windows at PXP ≥ 0.95, precedence order
- the §9 pass criteria: G1–G3 need at least 2 substantive and at most 1 two-state outcome per cell; X1 strong needs
  two-state in at least 2 of 3 replicates in each drift condition
- the v6 fitting procedure: starts, retry, convergence rule, training-only scaling, bounds and selection

The v6 unresolved-strength flags and the X2 amplitude inversion stay reported.

**Not permitted:**
- rejecting every boundary fit, or classifying every active bound as a failed fit
- trimming losses or removing held-out trials
- choosing a start by held-out score
- lowering the PXP or run thresholds
- removing the null model
- boosting X1's amplitude to obtain a pass
- running only the cells that failed
- adding starts to settle a near-tie, unless declared separately as a development operation

## 2. Phase 1 — diagnostic panel and idealized readout (development; bounded; Mac)

### 2.1 Panel manifest (committed before any regeneration)

- **Recording statistic.** G_rec is the worst main-window graded loss relative to null, in nat per trial:
  G_rec = max over the 10 main windows of (4 · (evidence_null − evidence_graded) / n_trials). It uses the stored v6
  `evidence` (held-out sum / 4) and `n_trials`. This is the unit of the v6 stage C catastrophe diagnosis. Windows where
  null or graded is unavailable are skipped. A recording with no usable window, or whose status is not `ok`, is listed
  as unrankable and not selected.
- **Denominator.** Each of the 20 cells (generator × strength × drift) pools its 3 replicates × 34 templates, up to 102
  recordings.
- **Selection.** Two recordings per cell:
  - **worst:** the largest G_rec;
  - **median:** the rankable recording whose G_rec is closest to the cell's median (numpy median; with an even count,
    the mean of the two middle values), distinct from the worst.
  - Ties in either rule go to the lower replicate, then the lower subject.
  - This gives 40 distinct recordings. Using the v6 held-out values here is declared development selection; no fit's
    start is ever chosen by them.
- **Saved first.** `results/devpanel_v7/panel_manifest.json`, committed before any fit. It holds the selection script's
  hash and, for each of the 40 recordings:
  - the exact v6 parent `recording_manifest` (identity ebaddf98807b)
  - the parent result's SHA-256 sidecar
  - G_rec, its rank and the cell median
- **What it can show.** It enriches extreme graded losses, so it diagnoses mechanism. It cannot estimate how often a
  mechanism occurs, typical fold behaviour or a group decision. It does not sample two-state failures. Two-state
  prediction stability is judged only on the complete paired fresh check (§3), never from this panel.

### 2.2 Logging-only instrumentation

- **Wrapper.** A new module, `devpanel_v7.py`, re-runs each panel recording through the unmodified path:
  `SY.generate` from the parent manifest, then `RC.recording_scores` over all 20 windows. Inside its own process only,
  `LK._run` is replaced by an instrumented copy that calls the same objective, bounds and L-BFGS-B options. No file of
  the v6 code is edited, and nothing is added to the fitting.
  *As implemented (rev 2; Codex eaea99b Q6):* the wrapper installs functions that call the original `_run`, `fit` and
  `fold_scores` and a pass-through `minimize`, rather than a copy; logging reads their results and draws no random number.
- **Per start** (the moment start, 7 jitters and any 8 retries; failures included):
  - the seed tuple (SEED, recording tags, model index, retry flag) and start order
  - x0, theta and log-likelihood at full precision
  - success, the convergence decision and projected gradient
  - nit, nfev, the optimizer message and elapsed seconds
  - per parameter: the bounds, the absolute distance to the nearer bound, and the normalized position
    (x − lo)/(hi − lo)
- **Per fit:** the kept start (first in order among exact ties), `n_at_best` and availability. An unavailable fit still
  gets its reason row.
- **Per fold and model, at every training and test trial:**
  - the scaling (m, s, S, ybar)
  - the conditional mean and SD. Null: mean and SD. Graded: a0 + a1·L + β·h and exp(s0 + r·L). Two-state: the mixing
    weight A, both component means, the component SD exp(ls), and the marginal mean and SD.
  - the per-trial held-out log-likelihood
- **Per fold, dose support:** the training present-dose range (min and max of scaled x). Each test present trial is
  labelled below, within or above it.
- **Parity.** Each re-run must equal its stored v6 result exactly in `evidence`, `available`, `delta`, `n_trials`,
  `auc` and the two-state summary medians. Check the first selected recording before proceeding; any difference stops
  Phase 1. Check all 40 afterwards.
- **Archive.** The `results/devpanel_v7/` namespace carries its own identity: the SHA-256 of every loaded melcon_port
  module and the wrapper, the runtime, the parent identity and the panel manifest digest. Reload is verified, and
  mismatched inputs are refused.

### 2.3 Idealized readout (part of Phase 1)

- **The readout.** The **stochastic latent readout** `z_true` replaces the decoder projections. It is exactly what
  `SY.generate` stores for the same template, generator, drift and tags: intrinsic noise, hemifield shift and drift
  included, with no decoder and no sensor noise. `z_true` is drawn before any sensor sample and does not depend on the
  amplitude. The light path computes only that first part of `generate`, and is checked equal to `generate` on one
  recording per generator.
- **What it is not.** It is an ideal-observation check, not a matched weak/strong signal-to-noise condition, and it has
  no strength factor. Removing the decoder and the sensors together does not separate their contributions. G2 (skewed)
  and G3 (SD 1 + L) are deliberately approximated by the Gaussian graded density, so exact graded recovery is not
  expected, and a family preference is not a software-defect finding.
- **Cases.** G1, G2, G3 and X1 × both drift conditions × 34 templates = 272 recordings. Data tags are
  (phase 9, generator index, 0, drift index, 0, subject).
- **Scoring.**
  - Folds are the same four block folds as `recording_scores`, on all retained trials.
  - Availability follows `LK.fold_scores` (MIN_CATCH and MIN_SIDE on the training block).
  - Optimizer tags are (subject, task index, half, fold, 99). Window tag 99 is a declared pseudo-window, outside the
    real window indices 0–39.
  - Training-only scaling applies, and every test trial is scored.
- **Inputs and outputs.** True occupancy, component labels and generator parameters never enter fitting or starts.
  They are diagnostic outputs only. The logging is that of §2.2. The output is per recording only, with no group rule,
  and it is kept apart from the battery and its group claims.

### 2.4 Questions Phase 1 answers (mechanism, not frequency)

1. Per family, do severe held-out losses coincide with boundary solutions (in both absolute and normalized distance) and
   with test doses outside training support?
2. Do near-tie starts (converged, within 0.5 nat) give materially different predictions?
3. Does the graded fit's conditional SD collapse at extrapolated doses?
4. **How often does graded's effective SD fall below 0.05·S, and does that coincide with severe losses?** This is the
   floor that already bounds the null SD and the two-state component SD. In v6, `bounds()` gives both a log-SD in
   [log 0.05S, log 5S]. Graded's SD is exp(s0 + r·L) with r ∈ [−log 10, log 10], so at L = 1 it can reach 0.005·S (and
   50·S). The families' SD floors are therefore not symmetric.
5. How often do the asymptotic shifts sit at their bounds? Graded a1 ∈ [0, 10S]; two-state e^d0 + e^d1 ∈ [0.02S, 20S].

Every window and fold of the 40 recordings is reported, with this sampling description. The idealized check answers
whether each failure persists without the decoder and sensors. Persistence would implicate density, estimation or dose
support as sufficient in that setting. Disappearance would not identify a unique cause.

### 2.5 Load limit

- **Size:** 40 recordings (1,600 main fold-window units; 4,800 initial main-window model fits, before retries), plus
  272 idealized recordings (3,264 fits).
- **Workers:** 2, beside the running refit probe.
- **Rule:** benchmark the first recording, including parity, and write the projection. If Phase 1 projects past 4 wall
  hours, pause and report before its main work.

### 2.6 Phase 1 results (15 Sept 2026; no plan change)

Run `results/devpanel_v7/run-5d74bc1d6a11/` (wrapper `devpanel_v7.py`, RSC ad7e747; panel manifest RSC a856116; analysis
`devpanel_analyze.py` and its `analysis/summary.json`, RSC c2068f1). Development evidence; the panel shows mechanism, not
frequency.

- **Execution.** The latent-only path equals `SY.generate` for G1, G2, G3 and X1. The first recording matched v6 exactly, then
  all 40 panel re-runs matched in status, windows, models, evidence, available, delta, n_trials, auc and the summary medians;
  evidence rebuilt from the logged folds equals v6 for all 40. 272 idealized recordings, all `ok`. 0.10 wall-hours on 2
  workers beside the refit probe (projection 0.09).
- **Q1 (panel, main windows).** Graded: 111 of 1,600 fold units more than 1 nat per trial below null. 98.4 % of their summed
  loss lies on test trials outside the training dose range (33 % of their test trials), and the worst trial is extrapolated in
  100 of 111. A bound is active in 108 of 111 severe and 72 % of other units, so "at a bound" does not discriminate; `r` at its
  lower bound (−ln 10) does: 86 of 111 severe against 48 of 1,489 others. `log_k` is at a bound in most units of both kinds.
  Two-state: 22 severe, 96 % of their loss on extrapolated trials, `delta0` and both slopes at bounds.
- **Q2.** 410 graded fits have a distinct converged start within 0.5 nat; 46 differ in held-out score by more than 0.1 nat per
  trial and 15 by more than 1 nat (9 of them severe). Near-ties are a minor contributor.
- **Q3.** In severe graded units with extrapolated trials, the smallest SD at extrapolated doses is a median 0.58 of the
  smallest SD at within-support test doses (1.0 in other units); median 0.098 S against 0.27 S.
- **Q4.** No graded unit, in the panel's main or early windows or in the idealized readout, has an effective SD below 0.05 S
  at any dose; the smallest is 0.083 S. The SD contraction comes from `r` at its bound applied at extrapolated doses, not from
  crossing the floor. The 5 S ceiling of the same range does bind: effective SD above 5 S at some dose in 24 of 1,600
  main-window, 15 of 1,600 early-window and 27 of 1,088 idealized graded fits (maximum 9.7 S), every one with `r` > 0 and
  none severe.
- **Q5.** Graded `a1` at 10 S in 9 of 111 severe units (8 per mille of others); two-state `delta0` or `delta1` at a bound in
  73 % of all units, severe or not.
- **Idealized readout.** Graded severe in 12 of 1,088 fold units, all with extrapolated trials (97 % of the loss there);
  two-state 1. The readout has higher signal-to-noise than the battery, so rates are not comparable with the panel's. Family
  with the highest evidence per recording (two-state / graded / null of 34): G1 no drift 14/18/2, drift 19/14/1; G2 15/13/6,
  18/12/4; G3 8/23/3, 14/18/2; X1 27/5/2, 24/8/2. These are recording winners, not group decisions. The graded family
  contains G1 only within its parameter bounds: the true x0 lies outside the box in 1 of 136 no-drift folds (sub-26,
  block 4 → 3, x0 = −4.93; Codex eaea99b Q5). The bounds are not changed on these data.

**Reading for Phase 2 (development; the §3 fixings are still to be written and committed before any candidate fit).**
- C1's floor (0.05 S) binds in no kept fit, and its ceiling (5 S) only in fits with rising spread and no severe loss: the C1
  constraints exclude none of the observed severe kept solutions; their effect after constrained refitting has not been
  measured (Codex eaea99b Q1). (The first version of this section, and the RSC c2068f1 commit message, called C1 inert;
  that checked only the floor.) Its range stays the existing bounds, not values tuned on Phase 1;
  changing them or adding an `r` restriction would be a recorded plan amendment. Because C1 changes the feasible set, its
  starts and search paths differ from the baseline's, so its fits are not assumed identical.
- C2 acts on the located loss (extrapolated doses, both families).
- Neither candidate addresses the weak single-recording separation under G1 on the latent readout (one training block per
  fold). That bears on whether positive graded recovery can be declared a pass criterion at lock (§4).

## 3. Phase 2 — candidates (development; three configurations at most, one locked)

**The candidate set (rev 1).** Candidates are applied to both families, with training-only definitions and a written
rationale. There are exactly three configurations; anything else is a recorded plan amendment. That includes a changed
allocation, an asymptote cap, other floor values, extra start budgets and a retried fresh check.

- **C1 — symmetric effective-SD floor.**
  - Rule: every family's effective conditional or component SD is kept within the range the null SD and the two-state
    component SD already have, [0.05·S, 5·S], at every dose. Catch trials are included.
  - What changes: only the graded spread law's range. The two-state and null bounds already satisfy it.
  - Rationale: the §2.4 Q4 asymmetry. The value is the existing bound, not a constant tuned on Phase 1.
  - Constraint treatment: graded log-SD is linear in L, so bounding both endpoints (s0 at L = 0, s0 + r at L = 1) bounds
    every dose.
  - Fixed before any candidate fit: the exact parameterization, and whether |r| ≤ log 10 is kept as a linear
    constraint.
  - Tests: normalization, gradient, boundary and finite-prediction.
  - The graded spread law is never replaced by a constant SD.
- **C2 — no extrapolation in dose.**
  - Rule: each family's logistic dose terms are evaluated with scaled x clamped to [min, max] of the training block's
    present trials. This covers graded L in both mean and spread, and both two-state functions A and H.
  - Unchanged: catch trials stay governed by the catch flag; hemifield and the null are unchanged.
  - Every test trial is still scored at its observed response.
  - The clamp is the identity on every training dose. Training objectives, gradients, starts, fits and chosen theta
    therefore equal the baseline's, and only out-of-support predictions change.
  - C2 is scored from archived baseline fits once replay equivalence is verified. It cannot repair a training-search
    miss or an in-support collapse.
- **C1+C2** — both, scored from C1's fits for the same reason.
- **Withdrawn.**
  - Former C3 ("two decoder blocks, one density-training block and one test block, rotated") is exactly v6's allocation
    (`decoder.split_half`, `recording.recording_scores`). It gives no density fit more training data. Truly more density
    training would need a different decoder allocation or more data, and so an amendment, recalibration and new costing.
  - The asymptote cap of rev 0 is also withdrawn: it needs a tuned multiplier and imposes an unidentified plateau. The
    shift bounds are diagnosed in §2.4 Q5 only.
  - **C1 and C1+C2 (rev 2, after Phase 1; Codex eaea99b Q1)** are withdrawn by recorded amendment. The candidate set is
    C2 alone (§3.1 F1).

**Fixed after Phase 1, committed before any candidate fit:**
- C1's exact constraint treatment
- the severe-loss definition, its unit and denominator
- failure and availability handling
- how X1 recovery and false two-state calls under graded laws constrain selection
- the cost ceiling and the tie order
- a **no acceptable candidate** outcome, which returns the plan to amendment

**The fresh development check.**
- **Design:** X1 strong, G1 strong and G3 weak, both drift conditions, one replicate each: 6 groups × 34 recordings.
- **Streams:** new data phase 8, common random streams for all configurations.
- **Fits:** the unchanged baseline is fitted; C2 is scored from its logged fits under the replay contract (§3.1 F7).
- **Scope:** a bounded development check, not validation. It contains no G2, so it reports no fresh graded-call
  performance under all of G1–G3.
- **Retention:** every configuration and the baseline are retained and reported.
- **Amplitudes:** all configurations use the fixed v6 amplitudes, so the comparison is a procedure change at fixed input
  signal.

### 3.1 The fixings (rev 2; final, committed before any candidate fit; Codex record RSC eaea99b, dispositions §9)

**F1. Candidate set: C2 alone, by recorded amendment.** C1 and C1+C2 are withdrawn. The C1 constraints exclude none of the
observed severe kept solutions (§2.6); their effect after constrained refitting has not been measured. A faithful C1 needs
one of two things. The endpoint box in (s0, s1 = s0 + r) is not nested in v6: it removes some v6 predictions and admits
others, permits |r| up to log 100, and its jittered starts differ physically even with the same seeds and jitter algorithm.
The nested version keeps v6's box plus the endpoint constraints, and needs a constrained optimizer with a full-constraint
convergence rule. Developing and validating that optimizer is a poor use of this bounded check. This is a priority decision
from development evidence, not a demonstration that C1 could not help. Any return of C1 is a new amendment using the nested
definition, with primal feasibility and stationarity checked for all constraints (Codex eaea99b Q1).

**F2. Units and the paired comparison set.**
1. Every scheduled recording × half × fold × main-window key is enumerated first: 1,360 per family per group, 8,160 over
   the six groups, of which 5,440 are in the four graded groups. The shared §2 inclusion gate applies, and its exclusions
   and all failures stay in the accounting.
2. A family's paired comparison set is fixed from the saved baseline training state before any C2 held-out score is read.
   It holds the keys with inclusion passed, valid scoring inputs, a retained converged training fit for both the family and
   null, and finite null test densities. C2 has the same training fits and status at every key.
3. On that set a unit is severe if and only if the sum of all family-minus-null trial log densities, divided by all test
   trials, is strictly below −1 nat. A non-finite family trial density counts as severe and makes that family-fold
   unavailable; it stays in the denominator. A finite training fit whose baseline test score was non-finite is rescored
   under C2.
4. No converged training fit, invalid input, technical failure or non-finite null score is its own failure, unavailability
   or reference-failure category, never a fabricated loss or an automatic non-severe unit. Scheduled, included, fitted,
   reference-valid and scored counts are reported with their reasons. An empty comparison set cannot pass.

**F3. Failure and availability.** v6's rules, and §8's denominator and precedence, are unchanged when recording and group
decisions are assembled. Technical failures and exclusions of the shared baseline stage remain shared; a C2 replay exception
is a recorded failure, not a missing row.

**F4. Development gates.** The gates are decided only when all six groups and all 34 recording results per group are
present; an archived failure is a result, a missing job is incomplete. C2 is locked only if every gate holds; otherwise
Phase 2 stops for amendment.
1. X1 strong ends two-state in both drift groups under the unchanged `group.decide`. This is a conservative one-replicate
   development screen, not statistically equivalent to §9's two of three. Recording winners, positive Delta, a two-state
   run beside a graded run and a non-substantive outcome do not count.
2. Each of the four G1 strong and G3 weak groups ends graded or inconclusive/mixed. Graded-call counts are reported;
   passing through inconclusive outcomes demonstrates no positive graded recovery.
3. Pooled over the four graded groups, with B and C the baseline's and C2's graded severe counts on the same paired units:
   2·C ≤ B (B = 0 or 1 requires C = 0). This is an effect-size screen, not a significance test.
4. Tail guards: no increase in the two-state severe count in any of the six groups, and no increase in the graded severe
   count in any of the four graded groups.
5. No held-out family-fold newly unavailable where the baseline was available, compared per group and family with paired
   identities; repairs elsewhere do not offset new failures.

Reported beside the gates: the paired severe, repaired and new-severe transitions and the untrimmed loss magnitudes by group
and family, and the below-, within- and above-support counts and losses for both families.

**F5. Decision.** With C2 the only candidate there is no ranking contest: C2 is locked only if it passes F4. The baseline is
the comparator and cannot be locked. No unlisted variant, alternative solver or retry is added.

**F6. Cost ceiling.** The planning projection from the first Phase 1 recording (15.54 s) is about 0.88 worker-hours for the
baseline's 204 recordings, before logging, replay, summaries, group BMS and the common-cohort sensitivity. Benchmark the
first recording under the actual concurrent Mac load. The ceiling, 3 worker-hours and 4 wall-hours at two workers, counts
all of that work; stop and report if the projection exceeds either.

**F7. C2 replay contract, completed before any C2 held-out score is read.**
- Verify archive payload hashes, model and parameter order, complete fold keys, trial order, training scaling, source and
  runtime identity, parent input and calibration lineage, and the saved bounds, start, convergence and selection metadata.
- Reuse the exact retained theta and the training-fit availability flag, not the baseline fold's final held-out
  availability. Preserve retries, first-in-order exact ties and failure reasons. Never refit a missing result or choose
  another start by C2's score.
- Show that the clamped training design equals the original arrays; check per-trial likelihoods, analytic gradients and the
  summed likelihood; validate start selection from the logged starts.
- Reconstruct, with the same replay machinery, the unclamped baseline test likelihood arrays, finite masks, availability and
  reasons, fold sums, trial counts, recording evidence (sum/4) and Delta. Group assembly keeps the original cohorts, AUCs,
  window grid, seeds, precedence and common-cohort sensitivity.
- Then score C2. Each present test trial outside the training present-dose range is evaluated at the nearest endpoint, in
  graded L (mean and SD) and in both two-state A and H, at its observed y. Catch laws, hemifield terms and null are
  unchanged and verified unchanged, as are in-support predictions. Availability is re-evaluated from all C2 trial densities.

Equality is exact on the same numerical path; a mismatch stops for investigation and is never relaxed to a tolerance after it
is seen. C2 is an endpoint-plateau prediction assumption: it cannot repair a training-search miss, and it can bias
predictions outside support. Before it runs, the implementation is tested on unavailable training fits, non-finite held-out
scores, retry and tie selection, and replay failures.

**F8. No acceptable candidate.** If C2 fails any gate, Phase 2 stops. Every output is retained and reported, the phase-8
data become development data, and the plan returns to prospective amendment. No candidate is retried or added on these data.

**F9. Identity and seeds.** The new namespace seals the C2 and replay code, the F2–F5 definitions, the complete phase-8 data
tuples (8, generator index, strength index, drift index, 0, subject), the unchanged optimizer tags, the runtime, the actual
events and templates, and the calibration ancestry. v6 and Phase 1 are preserved. Later validation uses the complete locked
phase-10 battery and its declared criteria, without pooling heterogeneous groups as replicates.

### 3.2 Phase 2 result (15 Sept 2026): C2 not locked; Phase 2 stops (F8)

Run `results/devcheck_v7/run-061c01d763b9` (code and tests RSC 58770a1; benchmark 19.1 s per recording; recordings
0.50 wall-hours on two workers; report 28 s). All 204 recordings are `ok`, and every recording replayed exactly (F7): the
baseline evidence, availability, delta and n_trials were rebuilt equal to the stored summaries. Every scheduled unit is
scored (1,360 of 1,360 per family per group).

Gates (F4):
1. **X1 strong two-state in both drift groups — fails.** Both groups end inconclusive/mixed under the baseline and under
   C2. The two-state group PXP peaks at 0.82 without drift; with drift it reaches 0.999 in one window only (C2: 0.999,
   0.919 and 0.824 in windows starting 420, 510 and 540 ms), never three adjacent windows at 0.95.
2. **Graded groups graded or inconclusive — fails.** G1 strong with drift ends two-state under both configurations (two-state
   PXP at least 0.99 in the three adjacent windows starting 390, 420 and 450 ms).
3. **2·C ≤ B — fails.** Graded severe units over the four graded groups (5,440 scored) fall from 186 to 142, a 24 %
   reduction.
4. Tail guards — hold: no group's severe count rises for either family.
5. Newly unavailable family-folds — none.

Reported beside the gates: C2 repairs severe units and creates none (graded S→N 44 in the graded groups and 9 in the X1
groups, two-state S→N 13, N→S 0 everywhere), and it shrinks the most extreme graded losses about tenfold (worst unit
−2,006 → −134 nat per trial in G1 strong with drift). No group decision changes.

**Reading (development evidence).** The clamp removes the magnitude of the extrapolated tail, not the decisions. Both
decision failures are unchanged by C2: X1 strong lacks persistence at the calibrated readout strength, and a graded law with
drift across blocks is called two-state. Drift is a transport shift between the training and test blocks that no fitted
density models (Codex eaea99b Q5). Under F8, Phase 2 stops. Every output is retained, the phase-8 data are development
data, and the plan returns to prospective amendment; no candidate is retried or added on these data. No amendment is
proposed here: it waits on the owner's SI scope decision (15 Sept, `rsc_publication_strategy.md`) and a Codex read.

## 4. Phase 3 — lock

Implement the locked configuration with tests:
- density and gradient checks
- null-like special cases and finite predictions
- training-only scaling and selection
- decoder/density/test disjointness
- v6 preservation: archive reload, and unset/baseline behaviour, without rewriting v6 artefacts

Then write PREREG DRAFT v7 §6 and §9, and build a new identity and namespace (v7). The identity includes every new or
wrapper module; a directory name is not an identity check.

**Seal the seed roles.** Data phases:
- v6: 1 and 3–7
- the development fresh check: 8
- the idealized readout: 9
- validation: 10

Complete tuples are sealed for each.

**Optimizer tags.** They are (subject, task, half, fold, window), independent of the data phase. This fixed algorithmic
randomness is intentionally retained as part of the procedure. With new recordings it is not data reuse, and it is never
described as a fresh optimizer stream.

Whether positive graded recovery is a pass criterion is declared here, before validation. Otherwise graded-call rates are
reported, and the claim is limited to what the unchanged criteria test.
*Rev 2 (Codex eaea99b Q5).* For the C2 amendment the lock retains §9 and states its limit: passing tests strong-X1 recovery
and limited false two-state behaviour under the declared graded laws. It does not establish reliable positive identification
of graded generators or a general bidirectional classifier, and graded outcomes are reported in every validation cell. If
the scientific claim needs positive graded identification, a prospective recovery requirement and a new development plan
must precede the untouched validation. Codex reads the locked configuration and its tests
before any validation outcome is opened.

## 5. Phase 4 — independent validation

The whole battery runs on fresh data (phase 10): 5 generators × 2 strengths × 2 drift conditions × 3 replicates × 34
templates = 2,040 recordings (60 group replicates), all main windows, followed by the full-set summary.

- **Calibration lineage.** The candidates keep the generator, decoder, strength statistic, templates and calibration
  settings. The v6 amplitudes are therefore reused, with the parent calibration hashes and the unresolved-strength and
  X2-inversion flags carried in the manifest, never presented as recalibrated. No configuration in the set changes the
  decoder.
- **Criteria.** The §9 criteria are unchanged. All exclusions, unavailable models and technical failures stay in the
  denominator under the existing complete-replicate and common-cohort rules. The sixty heterogeneous groups are never
  pooled as replicates of one condition.
- **Stopping.** A failed validation returns the procedure to development. Any further selection needs another untouched
  validation sample.

## 6. Cost (Mac; planning values until benchmarked)

The v6 stage C rate is 8.9533 worker elapsed-hours for 2,040 recordings, about 0.0044 per recording.

| Phase | Planning value |
|---|---|
| Phase 1 panel | 40 recordings ≈ 0.2 worker-hours, plus logging I/O |
| Phase 1 idealized | 272 recordings, 3,264 fits ≈ 0.1 worker-hours (no sensor or decoder cost) |
| Phase 2 fresh check (rev 2) | baseline on 204 recordings ≈ 0.88 worker-hours (planning, from the first Phase 1 recording), plus logging, replay, C2 scoring, group BMS and summaries; ceiling 3 worker-hours / 4 wall-hours (§3.1 F6) |
| Phase 4 | ≈ 9–11 worker-hours |

These are worker elapsed-hours, not CPU hours and not wall time. Each phase is benchmarked under the actual concurrent
Mac load, with a written limit and a pause-and-report rule before its main work. No cloud, and no recalibration.

## 7. Revision trail

| Rev | Date | Change |
|---|---|---|
| 0 | 15 Sept 2026 | RSC 1100eb1: the plan committed before any fit (owner go; Codex e490f3b Q3). |
| 1 | 15 Sept 2026 | Codex e42846e taken in (§8). Panel manifest, statistic and selection defined; logging-only instrumentation with v6 parity; idealized readout = stochastic latent z; fold count corrected; C3 withdrawn as already v6; asymptote cap withdrawn; C1 = symmetric effective-SD floor at the existing 0.05·S; C1+C2 added; ranking/stop rule before candidate fits; seed phases 8/9/10 and fixed optimizer tags declared; "certified" replaced. |
| 1 | 15 Sept 2026 | Phase 1 run and results added as §2.6 (RSC a856116 manifest, ad7e747 wrapper, c2068f1 analysis); no change to the plan. |
| 2 | 15 Sept 2026 | Codex's Phase 2 fixings record (RSC eaea99b) taken in (§9): C1 and C1+C2 withdrawn by recorded amendment; final fixings F1–F9 (paired comparison set, development gates with tail guards, C2-only decision, cost ceiling counting all downstream work, full replay contract, identity); C1 wording corrected; G1 bound limitation and graded-recovery limit at lock recorded; wrapper implementation recorded in §2.2. |
| 2 | 15 Sept 2026 | Phase 2 result added as §3.2 (run-061c01d763b9): C2 fails three gates and is not locked; Phase 2 stopped under F8; no plan change. |

## 8. Dispositions — Codex's v7 plan record (RSC e42846e), read in full

| Codex | Disposition |
|---|---|
| Q1: panel manifest (statistic, normalization, window combination, denominator, median, ties, distinct rule, saved manifests) | Accepted: §2.1. |
| Q1: exact idealized readout | Accepted: §2.3, the stochastic latent z with no strength factor. |
| Q1: logging-only implementation, v6 parity on the first recording, all starts and failures, full precision, reload and refusal | Accepted: §2.2. |
| Q1: four density folds in total; 1,600 fold-window units and 4,800 initial fits | Accepted: §1, §2.5. |
| Q1: two-state mixing weight, component and marginal moments; normalized bound distances | Accepted: §2.2. |
| Q2 C1: exact predictive definition; effective component SD; comparable asymptote; normalized density; constraint treatment | Accepted. C1 is narrowed to the symmetric effective-SD floor at the existing bound (§3), prompted by the asymmetry found reading `bounds()` (§2.4 Q4). The cap is withdrawn rather than specified. |
| Q2 C2: pooled present training trials, same clamp on L, A and H; identity on training doses; reuse of baseline fits after replay | Accepted: §3. |
| Q2 C3: already v6 | Accepted, verified in `decoder.split_half` and `recording.recording_scores`; withdrawn. |
| Q2: candidate count; ranking/stop rule; no-acceptable outcome; G2 absent from the fresh check; common random streams | Accepted: §3. The fresh check keeps its limited, labelled scope. |
| Q3: panel for mechanism only; no two-state tail sampling; ideal ≠ matched SNR; G2/G3 approximation | Accepted: §2.1, §2.3, §2.4. |
| Q4: full 60-group validation; identity including wrappers; seed phases vs optimizer tags; lineage flags; "passes the declared synthetic acceptance criteria"; graded recovery declared at lock | Accepted: §4, §5. |
| Cost: planning values; worker elapsed time vs wall time; benchmark under load with a pause rule | Accepted: §2.5, §6. |

## 9. Dispositions — Codex's Phase 2 fixings record (RSC eaea99b, SHA-256 e8270b89…), read in full

| Codex | Disposition |
|---|---|
| Audit: 40/40 parity over 13 fields, 272 ideal records, 12,864 fits and 102,912 start selections replayed, ceiling counts reproduced | Noted; independent confirmation of §2.6. |
| Q1: withdraw C1 and C1+C2 by prospective amendment; corrected rationale ("exclude none of the observed severe kept solutions; effect after constrained refitting unmeasured"); endpoint box non-nested and its physical starts change; if retained, nested with full-constraint feasibility and stationarity | Accepted: §3 withdrawn list, §3.1 F1; wording corrected in §2.6 and the owning summaries. |
| Q2: X1 both drift groups and 2·C ≤ B as development gates with zero-count conventions; complete scheduled/paired denominators; strict −1; non-finite family density severe and unavailable; failure categories; per group and family; no newly unavailable units; tail guards for both families; transitions and untrimmed magnitudes | Accepted: §3.1 F2–F4. |
| Q3: tie order total; after withdrawal C2 passes every gate or stops for amendment | Accepted: §3.1 F5, F8. |
| Q4: replay contract beyond training-sum equality (lineage, theta and training-fit status, arrays and gradients, start selection, baseline test reconstruction and aggregation, rescoring non-finite baseline scores, unchanged null/catch/in-support checks, exact equality) | Accepted: §3.1 F7. |
| Q5: keep the fresh-check design; G1 truth outside the x0 box in 1/136 no-drift folds; recording winners are not group recovery; state the graded-recovery limit at lock | Accepted: §2.6 note, §4 rev 2 statement; bounds unchanged. |
| Q6: original-function wrappers acceptable; record the deviation | Accepted: §2.2 note, revision trail. |
| F6/F8/F9: ceiling counts all downstream work; no-acceptable exit; sealing list | Accepted: §3.1 F6, F8, F9; §6. |
