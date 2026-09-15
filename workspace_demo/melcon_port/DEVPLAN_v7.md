# Melcón battery — development plan for the revision after the failed v6 battery (v7, DRAFT rev 1, 15 Sept 2026)

**Status.** The owner gave the go on 15 Sept 2026. The plan was committed before any new diagnostic fit (RSC 1100eb1;
Codex, post-outcome record `t1_access/reviews/2026-09-15_melcon_v6_stage_c_codex_record.md`, RSC e490f3b, Q3 step 1).
**Rev 1** takes in Codex's second opinion on that commit (`t1_access/reviews/2026-09-15_melcon_v7_devplan_codex_record.md`,
RSC e42846e). Its dispositions are in §8, and Phase 1 proceeds from this revision.

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
- **Fits:** the unchanged baseline and C1 are fitted; C2 and C1+C2 are scored from those fits.
- **Scope:** a bounded development check, not validation. It contains no G2, so it reports no fresh graded-call
  performance under all of G1–G3.
- **Retention:** every configuration and the baseline are retained and reported.
- **Amplitudes:** all configurations use the fixed v6 amplitudes, so the comparison is a procedure change at fixed input
  signal.

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
reported, and the claim is limited to what the unchanged criteria test. Codex reads the locked configuration and its tests
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
| Phase 2 fresh check | baseline + C1 on 204 recordings ≈ 1.8 worker-hours; C2 and C1+C2 by scoring, credited only after replay equivalence |
| Phase 4 | ≈ 9–11 worker-hours |

These are worker elapsed-hours, not CPU hours and not wall time. Each phase is benchmarked under the actual concurrent
Mac load, with a written limit and a pause-and-report rule before its main work. No cloud, and no recalibration.

## 7. Revision trail

| Rev | Date | Change |
|---|---|---|
| 0 | 15 Sept 2026 | RSC 1100eb1: the plan committed before any fit (owner go; Codex e490f3b Q3). |
| 1 | 15 Sept 2026 | Codex e42846e taken in (§8). Panel manifest, statistic and selection defined; logging-only instrumentation with v6 parity; idealized readout = stochastic latent z; fold count corrected; C3 withdrawn as already v6; asymptote cap withdrawn; C1 = symmetric effective-SD floor at the existing 0.05·S; C1+C2 added; ranking/stop rule before candidate fits; seed phases 8/9/10 and fixed optimizer tags declared; "certified" replaced. |

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
