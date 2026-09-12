# Codex review record — Entropy T1, 12 September 2026

This file owns the Codex review findings and restart context for the two completed
12 September reviews. It records advice sent to `claude:Entropy SI`, not an owner
decision or authorization to launch work. The publication strategy and current
operational state remain with Unimog-Projects work item R052 and its owning docs.

## Position at wrap

Reviewed Recoverable-Self-Coding code commit `a508601` and preregistration/brief
commit `ea8042d`. The latest review was sent through `xs say` before this wrap.
The two complete messages are preserved below in chronological order. Earlier
hypotheses in the first message are historical; use the second message for the
latest disposition.

**Latest verdict: not on board with production yet.** The within-M2K basin-loss
diagnosis and grouping of bootstrap copies at both fold levels are accepted.
The remaining blockers concern counting duplicate optimizer starts as independent
reproduction, bootstrap failure handling, connecting the refitting interval to
the actual runner, and specifying/validating the resulting procedure.

The earlier approval of d4v12b was limited to continuing per-layer calibration and
recovery, with power held behind the revalidated gain gate. It did not approve a
new production wave or the still-pending 35-layer band validation. The latest
review supports bounded diagnostics and an owner decision to stop verified jobs
after their final calibration upload at the known-failing gain stage. Codex has
performed no AWS operation.

The read-only reviews are complete; no Codex edit, fit, simulation, or cloud job
is in flight. This wrap saves their record and diagnostics only. No manuscript,
preregistration, publication decision, or production code is changed by the wrap.

## Resume procedure

1. Read this section and the latest review below. Run `git log` and inspect
   status in both repos; Claude may have landed fixes since `ea8042d`.
2. Read the current R052 frontmatter and its latest log entries in
   `~/Unimog-Projects/project_knowledge/work/R052-entropy-si-paper-access-at-threshold-brain-vs-la.md`.
   That item belongs to session `Entropy SI`; the reviewer does not take over
   its operations or owner decisions.
3. Read the latest requested brief end-to-end, then the relevant diff and full
   code paths. The last brief was
   [gain jump and refitting bootstrap](2026-09-12_gain_jump_and_refit_bootstrap_codex_brief.md).
   Check [the preregistration](../PREREGISTRATION_T1_model.md) §§7.4, 8.2, 10 and 15
   against the implementation.
4. For a requested re-check, give a fixed/not-fixed disposition for the findings,
   identify any new blocker, and send one substantive reply with the requested
   VERDICT through `xs say 'claude:Entropy SI' '<review>'`. Reviews remain
   read-only unless the owner changes the scope. Do not launch simulations.
5. Do not infer acceptance of the latest review from silence. The owner's
   disposition and any next execution budget are not in this review record.

Exact prompt to resume:
“Read ~/Recoverable-Self-Coding/workspace_demo/t1_access/reviews/2026-09-12_codex_review_record.md
and Unimog-Projects work item R052, check both repos' latest commits, then continue
the T1 second-opinion review from the outstanding findings.”

## Next re-check targets

- Gain reference gate: unique initial vectors and source/batch provenance;
  distinct discoveries of the best-found solution on both training draws;
  independent challenge at the frozen scale; no check-test feedback.
- Calibration search: retained basin candidates, refreshed bracket endpoints,
  final frozen-scale checks, all twelve pairs, saved fitting diagnostics.
  `t1_job.gain_file` must fail closed on a missing approved artefact if
  orchestration claims that calibration is computed once.
- Refitting: every required raw score finite; explicit failure policy with no
  silent conditioning on successful resamples; all original-concept copies
  grouped at both CV levels; fixed-fold specification tested against the
  declared target.
- Production analysis path: explicit interval-method option through
  `analyze_dataset` and `simulate.one_replicate`; original point estimate
  retained; unavailable interval becomes assay failure; paired H2
  workspace-minus-early statistic; method, B, folds and seeds in provenance.
- Validation: audit ordinary inner/outer fits with training-only stronger
  searches; freeze the procedure, counts and borderline disposition; new seeds
  for every retained null and declared alternative; uncertainty in the
  reference target; benchmark actual cloud concurrency before budget claims.
- Reuse: immutable source rows and hashes, explicit source-to-analysis manifest,
  exact eligible fields/keys. Old plain fits can support diagnostics if their
  path is unchanged; old intervals cannot validate the replacement.

## Evidence retained

The first review read **11,923 unique calibration rows**, not the later count in
R052. Its code hash was `b29215469af9`; its input CSV SHA-256 was
`ec5584ab1e3cc5def7bd9c5e1b907e4f6f16d4a2481599beaa37fff25a435315`.
The CSV can receive more rows; do not attribute that snapshot's counts or checksum
to a later file. Six null settings failed the per-layer .90 coverage rule,
despite zero primary mixture calls. The full numbers and interpretation are
in the first review below.

The most recent check ran the existing mocked
`test_refit_bootstrap.py`, `test_calibrate_gain.py`,
`test_gain_gate.py` and `test_gain_gate_integration.py`: all passed.
Two additional mock counterexamples showed:

- One successful moment initial vector repeated in batches of 32 and 24
  counted as two reproductions, setting `ref_reproduced=True`.
- A partial-NaN score array with `failed=False` produced a usable [1, 1]
  interval and `n_failed=0`.

The review scripts are preserved beside this record:

- [Mock counterexamples](2026-09-12_codex_gain_bootstrap_counterexamples.py):
  fixed data, mocked numerical fits and scores, no simulations or optimization.
  It demonstrates the reviewed implementation at `a508601`; its assertions
  should change outcome after the bugs are fixed. It is a review artefact,
  not a production regression test asserting that these bugs should persist.
- [CSV audit](2026-09-12_codex_calibration_csv_audit.py):
  standard-library read of existing rows, no repository imports, fits or
  simulations. It reports the current input checksum/count and checks for
  writes during reading. Output must be interpreted as a dated input snapshot.

Both scripts retain the original Mac paths used in the review. Local outputs
of the production diagnostics were read from
`../sim_results/d4v12b/monitor/`; neither those outputs nor raw CSVs are
included in this wrap commit. The four existing mocked tests and these
counterexamples do not establish numerical convergence or statistical coverage.

## Scientific and publication boundaries

The SI question is whether a statistical comparison of graded and discontinuous
representational responses transfers from human EEG to a language model, while
distinguishing access from recoverable operation. It does not assert shared
first-order-transition physics or consciousness/experience.

The human reference is the Sergent active-session reproduction with modest
predictive margins; the exact published Source Data curve and the port both first
cross .95 at 315 ms. The passive three-model comparison is an additional analysis
with this readout, not a claimed priority result or an automatically failed
reproduction. Its limitations and open checks are recorded in
`../../sergent_port/RESULTS_sergent.md` and its README (review reconciled at
`e341319`).

The model inference concerns concepts for one fixed checkpoint; carriers are
fixed and realizations are repeated observations. Do not revive ten independent
“subjects” from the discarded bundle display. H1 coherence evidence, H1-T
target-specific evidence/bridge, and H3 causal use remain distinct conditions;
causal use alone does not establish a discontinuous access transition.

Earlier strategy and introduction reviews are already recorded in
`~/Unimog-Projects/project_knowledge/rsc_publication_strategy.md`,
the Rev C architecture note 7, and
`~/Unimog-Projects/papers/adaptive_agency_special_issue/reviews/2026-09-12_intro_codex_brief.md`.
The introduction was reviewed twice; a third review is not pending by default.
PRE owns the loop physics; the SI owns workspace/T1. No rushed v4 publication
was approved. Title, collaborator, pre-assessment and publication hold remain
owner decisions. RSC notation uses “stability index” and “information retention”;
no entropy-production identity or proxy is assumed.

A second human dataset was downloaded by Claude's job; its owning record is R052.
Do not start EEG analysis under this review. No durable context needs to remain
only in the Codex transcript.

## Full review 1 — d4v12b calibration-stage read

Source brief:
[2026-09-12_d4v12b_calibration_read_codex_brief.md](2026-09-12_d4v12b_calibration_read_codex_brief.md).
Message sent before the gain-jump diagnosis. Preserved verbatim:

Read-only review of the brief, the 11,923 CSV rows, preregistration §§8–10, and the generating/scoring/dispatch code. I verified 11,923 unique replicate keys, one hash (b29215469af9), no recorded failures or nonfinite inner scores. No simulations or fits run.

1. BLOCKING — D4 has failed the configured per-layer coverage requirement. PREREGISTRATION_T1_model.md:295–298 says coverage below .90 under ANY retained generator invokes the refitting-bootstrap replacement; §10's D8 clause is a final design constraint, not permission to call D4 calibrated. Six settings fail, not five: M2H τ=.5/2, M2K α=1, M2S ω=.5/1/2. The .894 result is borderline in Monte Carlo terms, but .819/.780/.216 are not. Record the trigger and disposition now. D8 can be investigated as an explicitly documented diagnostic; neither that nor eventual layer averaging retroactively validates this D4 procedure. Keep the distinction between this failed per-layer check and the still-outstanding actual-band validation.

2. BLOCKING — The proposed gain diagnosis is not yet established (simulate.expected_gain/calibrate_gain, lines 299–360). Every scale reuses the SAME train/test seeds and optimizer-start seeds. Finite-reference sampling affects the curve, but these are not fresh noisy evaluations. Non-monotonicity alone does not defeat a continuous, sign-bracketed bisection. There is a specific discontinuity candidate: G* is selected by maximum TRAINING likelihood, but its gain is evaluated on TEST data; changing the winning reference member can jump that test score. Optimizer/quadrature branch changes are another possibility. The local trace file was empty when I read it. Inspect adjacent-scale gains by member, the selected member, training likelihoods and fit diagnostics before naming the cause. A larger reference sample and an explicitly specified coarser SEARCH tolerance are reasonable amendments to test; they do not replace the independent ±25% agreement / ≤20% SE / convergence gate. Freeze a scale before its fresh validation draw; do not search validation seeds until one passes. This failed search did not reach an approved independent check.

3. BLOCKING FOR THE FALLBACK — Saved scores cannot implement pipeline refitting, and the existing fallback is not ready (analyze.py:338–369, especially its call into layer_pipeline:155). They permit new intervals of fixed scores and the already-scored ensemble, not changed fits/selections after concept resampling. refit_bootstrap keeps duplicate original concepts together in OUTER folds, then renumbers their copies; layer_pipeline creates INNER folds from those copy IDs, so copies of one original concept can enter both inner training and validation. Preserve original-concept grouping at both levels. Also propagate run['failed'] and specify treatment/denominators for failed bootstrap replicates: the current np.nanmean extraction ignores that flag and can silently retain a statistic from an unavailable comparison. These findings concern activating the fallback, not the completed non-bootstrap fitting run.

4. SHOULD FIX — The SE comparison changes your causal diagnosis (brief reading 2; CSV selection_ws_se). Compare sqrt(mean(SE²)) with replicate SD, not mean(SE). For M2S ω=1 these are .3444 versus .3555; for ω=2, 22.011 versus 23.210, rather than 3.373 versus 23.210. Missing fitting variability may matter, but that factor-of-seven claim is unsupported. At ω=2, median Δ is −2.066 versus mean −5.334; the ten most negative replicates contribute 35.5% of the summed magnitude. In replicate 294, concept 28 alone has Δc=−26,626.93, producing the replicate mean −418.54; the selected pair is M2S/M3V in all five folds. This is strong evidence of extreme held-out tail losses, not primarily changing selected identities. All 784 coverage misses are intervals lying ABOVE the estimated target. Tail sampling and percentile-interval shape need investigation alongside fitting variability. The variance-scale diagnostic follows Morris, White & Crowther §5.2 (DOI 10.1002/sim.8086; https://arxiv.org/html/1712.03198v3).

5. SHOULD FIX BEFORE CHOOSING THE REPAIR — My first candidate remains the correctly implemented §8.2 refitting bootstrap, with a small, costed diagnostic before a full validation commitment; it is not guaranteed to repair these tails. The existing ensemble is a useful comparator, not a demonstrated solution: its coverage is .943 for M2H τ=.5 and .950 for M2K α=1, but .890 at M2H τ=2 and .852/.816/.215 for M2S ω=.5/1/2. Choosing a revision using these simulations is legitimate method development before CONF, provided it is recorded as such. Calling performance on the SAME outcome-inspected rows independent validation is not legitimate. Keep all candidate results, freeze the selection rule, then assess the chosen procedure on new simulation seeds with declared counts and Monte Carlo precision. The remaining 77 rows are not a suitable validation set across the full grid.

6. SHOULD FIX — Retain M2S ω=2 as the declared stress condition unless CAL/PILOT evidence supports a separately justified applicability restriction (models.py:191, simulate.py:141). It means a concept's noise-SD multiplier has a central 95% range of approximately .02–50. That is extreme, but an extreme score SD does not itself establish implausibility. Removing it because coverage failed would select the null space on the desired outcome; any evidence-based restriction needs an explicit amendment and the failed stress result remains visible. A trimmed LAYER-band mean changes nothing at one layer and may retain the same extreme concept across all layers. Trimming concepts changes the score estimand and is a different amendment. More D still means 64 independent concepts. The coverage reference itself is imprecise at ω=2: moving the estimated target by ±2 reported MCSE changes coverage from .216 to .180/.304. Failure is clear; .216 is not a precision-known population coverage.

7. SHOULD FIX — Withdraw the “.015 bar” and predicted D8 conclusion (brief reading 6; preregistration §10's gain definition). The negative null Δ includes predictor misspecification and finite-training/selection effects under that particular G distribution. It is not a universal complexity penalty to subtract from a .01 oracle-to-reference-G gain under another, mixture-generating distribution. Power must be measured under the calibrated alternatives with the FINAL interval rule. Zero primary false positives here establishes useful performance at the tested null points, many far from Δ=0; it is not general calibration of every graded distribution or evidence about power. One important saved secondary result: historical M3-vs-M2B gives mixture support in 651/1000 M2H τ=2 replicates and 337/1000 M2S ω=2 replicates. Report this as a simulation demonstration of the inherited pair's vulnerability to omitted heterogeneity, not as a result about human EEG.

8. NOTE / DISPOSITION — The landing is 11,923/12,000, not complete: M2K α=1 lacks 35 rows and α=3 lacks 42. Zero-event one-sided 95% FPR upper limits are about .30–.31% PER tested setting; do not substitute a pooled bound for the per-null requirement. Preserve these rows and their original hash. A gain-only code change alters the current whole-file hash but does not scientifically invalidate unchanged null fits: retain their provenance and document exactly which functions/settings are unchanged. Current models.py and analyze.py are unchanged from 52267ec. However, recovery_merged currently rejects unequal hashes (simulate.py:265), so a cross-snapshot reuse manifest/reader must be explicit; never relabel the old rows as the new configuration. Future interval changes require new analysis provenance and validation, not necessarily wholesale regeneration of every old diagnostic. I am content for remaining calibration to finish and existing jobs to exit at the enforced failure. Hold the proposed broad relaunch. Resolve/benchmark the interval method and precompute one validated twelve-pair gain artefact before dispatching production power/recovery/five-layer work; larger quotas do not resolve either issue.

VERDICT: not on board — with the proposed full relaunch yet. Finish remaining calibration, preserve the results, and hold the next production wave pending the interval-method decision and validated gain artefact.

## Full review 2 — gain jump and refitting bootstrap

Source brief:
[2026-09-12_gain_jump_and_refit_bootstrap_codex_brief.md](2026-09-12_gain_jump_and_refit_bootstrap_codex_brief.md).
Reviewed code a508601 and preregistration record ea8042d. Preserved verbatim:

Reviewed a508601, the ea8042d preregistration record, both diagnostics and the live corrected output. The four mocked test scripts pass. I also ran two small mocked counterexamples; no numerical fits, simulations or AWS operations.

1. BLOCKING — The reproduction gate can count the SAME initial point twice (simulate.expected_gain:335–337; models.starts_from_moments; simulate._starts_at_best). The extra M.fit(...,24) repeats the original batch's unjittered moment start. My mock has one successful initial vector, repeated in the 32- and 24-start batches: starts_at_best=2 and ref_reproduced=True. Exclude duplicate initial vectors; retain start-source/batch identifiers and separate cold-start from warm-start discoveries. Require genuinely distinct discoveries of the best-found reference on each training draw, with an independently seeded challenge batch at the final frozen scale. Include starts spanning both observed skew orientations. A tighter agreement between the two estimated gains would not detect a shared optimization bias. Warm starts from calibration into check TRAINING data are acceptable; the check TEST data must remain unused in fitting/search. Do not call that independent cold discovery unless the cold runs actually reproduce the best combined solution.

2. BLOCKING BEFORE USING THE FALLBACK — The original inner-fold leak and exclusion of explicitly flagged failed resamples are fixed (analyze.py:183,399–409). Keeping each copy in its original outer fold is a defensible fixed-fold bootstrap specification; keep it explicit and validate against the already-declared unconditional procedure target. But 90% usable is not a defensible default just because it looks high: the missing 10% can contain everything determining both 2.5% tails. My default is all B resamples successfully scored after declared recovery, otherwise primary interval unavailable. A policy allowing missing statistics needs an explicit amendment and a conservative missing-tail analysis, not just percentiles conditional on successful fits. Also remove np.nanmean at line 401: a mocked partial-NaN score array with failed=False still returns a usable [1,1] interval and n_failed=0. Validate every required score before reducing it. This latter case is a defensive gap beyond the now-correct handling of run['failed'].

3. BLOCKING BEFORE VALIDATION/PRODUCTION — The replacement is a helper, not yet the analysis used by the runner. analyze_dataset:351 still always calls band_bootstrap; simulate.one_replicate still calls analyze_dataset. Add an explicit interval-method path, preserve the original point estimate, and propagate unusable bootstrap intervals to assay failure rather than decide(NaN,NaN), which currently returns inconclusive. Include the H2 paired ws-minus-early statistic, which refit_bootstrap does not currently return. Record method, B, failure policy, actual outer folds and bootstrap seeds in the output/hash. A mocked end-to-end runner check should prove that choosing refitting changes the interval/decision path without launching fits.

4. SHOULD FIX — The mechanism is established for these runs; the population-frequency claims are not (diag_gain_steps21_22.out; brief §1; preregistration §10). I accept optimizer basin loss within M2K, and withdraw G* switching as the explanation of this incident. The exact-scale fits and nearby scale 0.684662 finding the better basin support that diagnosis. Say “best-found solution”, not established global optimum; remove “near-equal training likelihood” from the diagnostic/calibration docstrings—the observed gap is 155 nat. The absolute scale difference is 1.6359e-6; 2.4e-6 is its relative size. One start batch and another batch reused over nearby scales do not establish “most seeds” or a 1-in-8 hit probability. Even assuming independent starts, a hypothetical 1-in-16 rate gives a 12.7% miss probability at 32, versus 1.4% for 1-in-8. The live corrected output already shows scale 3 selecting M2K with only 1/57 starts at best (ref_reproduced=False), and gain .45347 versus the old .62553. The amendment is useful, but rarity of misses is not yet demonstrated.

5. SHOULD FIX BEFORE THE GAIN ARTEFACT — Keep the fixed-scale, fresh seed+500 remeasurement as an explicitly declared fallback; it is not an extra opportunity to select a successful seed (simulate.calibrate_gain). The independent seed+1000 check and both gain bounds remain. However, warm updates make the evaluated function depend on the search history: cached endpoint scores can become stale when a better basin is discovered. Re-evaluate the bracket with the retained basin candidates before interpreting its width or ghi−glo as a discontinuity. Carrying just the previous winner does not guarantee that every previously found basin is preserved. The bracket-width stop is a numerical stopping rule; any unresolved reference-quality failure must still hold the artefact. Archive the final check's fitting diagnostics/parameters and cold/warm discoveries, not only its reproduction boolean and counts. Reaching the particular failed pair once does not approve the other eleven pairs.

6. SHOULD FIX BEFORE V2 — Audit the ordinary pipeline's numerical sensitivity on declared representative draws at BOTH inner and outer training sizes (approximately 38 and 51 concepts), including mixture-shaped data, with stronger training-only reference searches. Zero mixture calls under the tested M2K nulls does not show that every graded fit was accurate; their large negative margins could conceal misses. If material likelihood improvements change held-out family comparisons, amend §7.4 for the new snapshot and revalidate that algorithm. Never use another CONF fold's fitted solution as a warm start if it contains the current held-out concepts. CAL-derived starts and within-training-fold searches are available. Keeping d4v12b immutable is a provenance constraint, not a requirement that the eventual CONF pipeline keep a demonstrated numerical weakness.

7. SHOULD FIX — R=100 datasets with B=100 resamples is screening, not validation of a B=200 procedure (brief §3, Q6). At coverage .90, R=100 has Monte Carlo SE 3 percentage points; R=400 has 1.5 pp and R=1000 has .95 pp. At .95 these are 2.18/1.09/.69 pp. My lower-cost final-validation proposal is a declared R=400/B=200 amendment, with Monte Carlo intervals and a predeclared disposition for estimates too close to .90 to resolve; retain R=1000 if retaining its original precision. Validate every retained null setting and the declared mixture alternatives, not only the six settings that failed the old method. Cheap screening can eliminate a clearly inadequate candidate first. Selection and ensemble can be scored from the SAME bootstrap fits: return/save both instead of invoking refit_bootstrap twice. Estimate the reference theta_g precisely using ordinary-pipeline repetitions without bootstrapping each reference dataset; eligible old fits can contribute. Its uncertainty matters especially at omega=2. Monte Carlo bookkeeping: Morris, White & Crowther, DOI 10.1002/sim.8086, §§5.2–5.3: https://arxiv.org/html/1712.03198v3.

8. SHOULD FIX — The cloud cost projection is not established by this benchmark (bench_refit.py; brief §3). The 51-hour quantity is Mac-core-hours from a very small one-generator benchmark. Dividing it by 192 advertised vCPUs does not establish 48xlarge wall time or dollars; the existing run already showed much slower loaded-cloud fits than the Mac benchmark. Benchmark the corrected procedure at the intended cloud concurrency before committing to “one day” or “USD 160 per setting”. A 35-layer R1 interval is also not the full study's cost: R2/H1-T and the declared additional analyses need accounting. Persist bootstrap replicate statistics/failure records so they can be resumed and rescored.

9. NOTE — Cross-snapshot reuse is reasonable for the unchanged PLAIN fitting/scoring path, not approval of the old intervals under the replacement. The manifest should name old/new commits and file/config hashes; exactly which point estimates/log scores/replicate keys are reusable; D, levels, concept/carrier counts, layers/rho, RNG/fold construction and starts/quadrature/precision; runtime and row-file checksums; and evidence that the plain path preserves inputs and seeded calls. Validate disjoint/complete replicate keys and an explicit authorized source-hash mapping in recovery_merged/spotcheck. Keep source and analysis hashes separate; do not overwrite the old hash or merely disable the mismatch guard. Changes arising from the pipeline audit in finding 6 would require a narrower reuse claim.

10. NOTE — I support stopping verified d4v12b jobs once they reach that gain marker (stop_at_gate.py; t1_job.run_stage/gain_file). The final calibration CSV uploads occur synchronously before the marker, and this snapshot's next stage is known to fail. Use the exact run/job identities, verify the landed shard rows, and retain the stopped-job status and cost record; pagination should not omit jobs/log events. This is a technical disposition for the owner's decision, not a request to run the stop script from this review. Also, t1_job.gain_file still computes a missing artefact independently in each job: “computed once” requires the orchestration to precompute/validate it and make production jobs fail closed if it is absent.

VERDICT: not on board — for production yet. The basin-loss diagnosis and concept-grouping fix are accepted; the reproduction-count bug, bootstrap failure/runner contract, and validation plan remain to be resolved. Bounded diagnostics and stopping the verified failing gain stages are supported.

