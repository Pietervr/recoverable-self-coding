# Codex review record — Entropy T1, 12 September 2026

This file owns the Codex review findings and restart context for the four completed
12 September reviews. It records advice sent to `claude:Entropy SI`, not an owner
decision or authorization to launch work. The publication strategy and current
operational state remain with Unimog-Projects work item R052 and its owning docs.

## Current review position

Latest re-check: Recoverable-Self-Coding code `8972ba4` and documentation
`d1ab54f`; Unimog-Projects `84aaa653`. Claude requested the re-check through
`xs` after recording its disposition of Full review 3. All four reviews are
preserved below in chronological order; **Full review 4** is the current
disposition. The reviewed production files were clean at `d1ab54f`.

**Latest verdict: not on board with production yet.** The chosen-scale gate,
launcher interval/B options, failure/coverage bookkeeping, saved refit/H2
statistics and same-training challenge are accepted. Two integration blockers
remain: checkpoints can silently supply another dataset's intervals, and jobs
reject the revalidation writer's schema and fall back to the raw gain file.
Recovery-start provenance and output durability also need completion. The
numerical audit, validation design, benchmark and reuse manifest remain open.

The earlier approval of d4v12b was limited to continuing per-layer calibration and
recovery, with power held behind the revalidated gain gate. It did not approve a
new production wave or the still-pending 35-layer band validation. The latest
review supports bounded diagnostics and an owner decision to stop verified jobs
after their final calibration upload at the known-failing gain stage. Codex has
performed no AWS operation.

The latest re-check passed six existing test scripts, with an offline AWS SDK
substitute for the launcher's actual dry-run, and four new mocked fixtures. It
ran no numerical fit, simulated response dataset or AWS operation. Codex's
changes are this review record, its diagnostic script and the R052 review state.
The owning session's local calibration processes are outside the review. Its
reported M3L diagnostic at `a508601` supports the basin-loss diagnosis; no final
twelve-pair gain artefact or repaired coverage was established here. The owner's
further AWS spend cap is USD 3,000; every proposed stage must be costed within it
and any launch still requires the owner's go and Codex's explicit disposition.

## Resume procedure

1. Read this section and the latest review below. Run `git log` and inspect
   status in both repos; Claude may have landed fixes since `8972ba4`/`d1ab54f`.
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
5. Do not infer acceptance of the latest review from silence. Read R052 for
   the owner's current disposition and remaining execution budget.

Exact prompt to resume:
“Read ~/Recoverable-Self-Coding/workspace_demo/t1_access/reviews/2026-09-12_codex_review_record.md
and Unimog-Projects work item R052, check both repos' latest commits, then continue
the T1 second-opinion review from the outstanding findings.”

## Next re-check targets

- Gate the selected calibration evaluation, including when the lower endpoint
  wins; retain its full diagnostics and refresh endpoints after new discoveries.
- Carry interval and B through the real cloud launch request, with a mock
  launch-to-job-to-row check; record the frozen analysis configuration.
- Separate valid point estimates, primary assay failures and per-predictor
  interval availability; fix summaries and monitors without conditioning the
  reference target on successful bootstrap intervals.
- Save all bands, H2, companion cluster intervals, actual folds/seeds, and
  per-resample statistics/failure reasons; checkpoint resamples during fitting.
- Finish the fixed-scale training-only challenge and initial-vector/batch
  provenance; a new training dataset is a different objective, not that challenge.
- Use one accepted gain artefact in jobs and monitors; link it to its source
  checksum and update all diagnostics when revalidating it.
- Freeze and validate the procedure/counts/borderline rule on new seeds across
  all retained nulls and alternatives; complete the ordinary-fit sensitivity
  audit, cloud benchmark and explicit cross-snapshot reuse manifest.

## Evidence retained

The first review read **11,923 unique calibration rows**, not the later count in
R052. Its code hash was `b29215469af9`; its input CSV SHA-256 was
`ec5584ab1e3cc5def7bd9c5e1b907e4f6f16d4a2481599beaa37fff25a435315`.
The CSV can receive more rows; do not attribute that snapshot's counts or checksum
to a later file. Six null settings failed the per-layer .90 coverage rule,
despite zero primary mixture calls. The full numbers and interpretation are
in the first review below.

The second review ran the existing mocked
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

The third review adds
[six mocked re-check fixtures](2026-09-12_codex_recheck_counterexamples.py),
which exercise the actual calibration control flow, analysis-to-row-to-summary
path and launcher/job functions while replacing numerical fits, response-data
generation and cloud clients. Their assertions describe defects at `44b6d74`;
repairs should change those outcomes. The original two scripts retain the Mac
paths used in their review. Local outputs
of the production diagnostics were read from
`../sim_results/d4v12b/monitor/`; neither those outputs nor raw CSVs are
included with this record. The mocked tests and these
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

## Full review 3 — re-check of 44b6d74

Reviewed 12 September 2026, after the user requested continuation. Read R052 and
this record end-to-end, the complete updated brief and preregistration, the new
commit and full affected code paths, the launcher, monitor and tests. Latest
relevant Unimog commit: `7535ed57`; code commit: `44b6d74`. No production code,
preregistration, manuscript or running process was changed by this review.

**VERDICT: not on board with production yet.** The earlier specific fixes are
real, but the claim that all three blocking findings are closed is premature.
Five existing mocked scripts pass. The six fixtures in
`2026-09-12_codex_recheck_counterexamples.py` reproduce the gaps below; they run
no optimizer, generated response data or cloud operation. Their small artificial
values demonstrate control flow, not measured scientific outcomes.

1. **BLOCKING — the calibration gate can certify the wrong endpoint.**
   `simulate.py:500` selects the lower or upper re-evaluated endpoint when either
   meets tolerance. If the lower endpoint wins, `last = trace[-1]` at line 554
   and `full` still describe the upper endpoint. The returned scale and gain
   therefore use the lower fit while convergence, reproduction and archived
   runs use the upper fit. Fixture: selected scale 2 has one cold discovery
   (`ref_reproduced=False`); the last evaluated scale 4 has two; the entry passes
   with `calib_ref_reproduced=True`. Save each evaluation as a complete object
   and gate/archive the selected one. Add the lower-endpoint case to the tests;
   the existing healed-endpoint test exercises the upper endpoint. Also, the
   second endpoint evaluation can discover a basin absent from the first:
   refresh affected evaluations before declaring a surviving jump or freezing
   their reference diagnostics.

2. **BLOCKING FOR A REFIT CLOUD RUN — the launcher still selects cluster.**
   `t1_job.py:59` can read `INTERVAL` and `N_BOOT_REFIT`, but `launch_t1.py` has
   neither CLI option and its request `Environment` at line 121 sends neither.
   Setting these variables in the Mac shell does not transmit them to the
   container. A fully mocked launcher's real dry-run branch, with host
   `INTERVAL=refit` and `N_BOOT_REFIT=7`, emits neither field; the job defaults
   to cluster. Carry the declared method and B through the actual launcher and
   verify the request, job Config, row and hash together. The local
   `simulate.py --interval refit` path does work; that does not close the cloud
   path. This also affects the Config hash of a precomputed gain artefact.

3. **BLOCKING FOR VALIDATION — interval failures remain successes in the
   failure/coverage bookkeeping.** `analyze.py:351` keeps the original
   `run['failed']`; it is never updated when refitting makes the primary
   interval unavailable. `_row` copies it at `simulate.py:183`, while
   `summarize` at line 287 calls every `failed == 0` row usable and `spotcheck`
   line 167 uses that flag for its failure rate. Fixture: one failed bootstrap
   resample produces `selection_decision='assay failure'`, `interval_usable=0`,
   but `failed=0` and an empty reason; the monitor prints zero failures and the
   summary reports one usable interval with coverage zero. That interval
   should be absent from the conditional-coverage denominator. Keep separate
   flags for valid original fits/points, primary assay availability and each
   predictor's interval availability. Count all assay failures in monitors;
   compute coverage among that predictor's finite usable intervals. Retain
   valid original points for the unconditional procedure target even when
   their bootstrap fails: simply excluding them would create a different
   conditioning error. Missingness and its relation to the simulated data are
   performance results in their own right ([Morris, White & Crowther,
   §5.1](https://arxiv.org/html/1712.03198v3#S5.SS1)).

4. **BLOCKING FOR THE DECLARED POWER WORKFLOW — jobs and the monitor can
   disagree about the accepted gain artefact.** The missing-file refusal in
   `t1_job.gain_file:108` is fixed. But it reads only the raw JSON at line 98;
   `spotcheck.gain_file_for:95` prefers the revalidated JSON. The updated
   preregistration explicitly calls for precompute → revalidate → power.
   Fixture: a same-hash raw file passes all twelve pairs, the revalidated file
   fails, and the job's path still accepts all twelve while the monitor holds
   them. Use one explicitly accepted, immutable artefact in both readers, linked
   to the source checksum, scales, D and reference/analysis configuration; a
   later failed required check must hold dispatch as well as reporting. The
   raw file's own gate is still enforced by `power_points`; the defect is
   disagreement about which validation is authoritative. Also,
   `revalidate_gain_entries:620` updates check scalars but leaves the newly added
   `check_runs`, `check_theta` and `check_loglik` from the previous check. A
   fixture records fresh gain 0.011 alongside old theta 1 although the new
   check used theta 2. Update all check provenance together, and distinguish
   this legacy revalidation route from an extra opportunity to find a passing
   validation seed.

5. **REQUIRED BEFORE A COSTLY REFIT RUN — H2 and audit records are lost at the
   row boundary.** The helper now computes all three predictors and paired
   workspace-minus-early correctly in memory. However, `simulate._row:195`
   writes only workspace point/lo/hi/SE; early, late, H2 and companion cluster
   intervals disappear. `analyze_dataset:369` drops the helper's actual outer
   folds; `_row` drops bootstrap seed, policy, failure reasons, per-predictor
   usable counts and all replicate statistics. `one_replicate` returns only
   this reduced row. The mock reaches this actual path and confirms the loss.
   Persist the complete analysis record, with row/sidecar identity and
   checksums, and checkpoint completed resamples as they finish. Returning
   them after all B fits is insufficient for resuming a multi-hour dataset.
   This persistence gap is acknowledged in the brief; it remains open.

6. **REQUIRED BEFORE THE GAIN ARTEFACT — the final training-only challenge
   is still missing.** The deterministic repeated moment start is removed,
   and warm runs no longer count as cold discoveries: those defects are fixed.
   However, extra starts run only when the existing reproduction count is
   below two (`simulate.py:348`). A batch that repeatedly reaches the same
   inferior basin gets no challenge. Fixture: 32 distinct cold initial vectors,
   all mocked into one basin, return `ref_reproduced=True` with zero extra
   starts. The fresh seed+1000 check changes the training dataset and hence
   its likelihood objective; it does not challenge the final fit on the same
   training data. Add a declared independently seeded, stronger search on each
   final training draw, including starts spanning the observed opposite-skew
   basins, before evaluating its test scores. Define what happens if it improves
   the best likelihood; keep all recovery training-only and do not choose among
   check-test seeds. The run archive currently contains only source, rounded
   likelihood, convergence and iteration count (`simulate.py:379`), with no
   initial vectors, batch/seed IDs or final vectors per start. `_starts_at_best`
   counts rows rather than checking vector identity. Preserve that provenance
   so distinct discoveries can be audited. No new duplicate under the default
   Gaussian start generator was demonstrated here. Further, mirroring a
   zero-centred symmetric Gaussian skew jitter preserves its distribution;
   it does not guarantee the deliberately separated starting basins sought by
   the review. This is a reference-quality requirement, not a claim that a
   finite search proves global optimality.

7. **OPEN BEFORE PRODUCTION/V2 — the numerical audit, validation design and
   reuse manifest are recorded, not completed.** The proposed R=400/B=200
   amendment is reasonable to cost, but the count, seed blocks, borderline
   disposition and target-precision rule still need to be declared. Validate
   the chosen procedure at its actual B across every retained null and the
   declared alternatives; keep screening separate. R=400 gives a binomial
   Monte Carlo SE of 1.5 percentage points at coverage .90, before uncertainty
   in the estimated target; reporting that uncertainty and choosing repetitions
   for a stated precision follow [Morris, White & Crowther,
   §§5.2–5.3](https://arxiv.org/html/1712.03198v3#S5.SS3).
   The ordinary inner/outer training-only numerical audit, a measured cloud
   concurrency benchmark and the source-to-analysis reuse manifest remain
   required. The five-layer computational pilot still cannot validate the
   eventual 35-layer band. No successful final twelve-pair artefact or evidence
   that refitting repairs coverage was established by this re-check.

8. **SHOULD FIX — the coverage mechanism is overstated in both owning docs.**
   Preregistration §10 says the failure is tail sampling/interval shape,
   "not missing fitting variance"; `rsc_publication_strategy.md:15` attributes
   that categorical exclusion to Codex. The prior review rejected the claimed
   factor-of-seven SE deficit and identified extreme held-out losses. It did
   not establish that fitting/selection variability contributes nothing.
   Replace the exclusion with: extreme tail losses and interval shape require
   investigation alongside fitting/selection variability; RMS SE agreement
   alone does not separate these mechanisms. The within-M2K gain-jump
   diagnosis is a separate, accepted result.

Disposition against the preceding review:

| Previous finding | Current disposition |
|---|---|
| 1: duplicate moment start/reference quality | Duplicate removed and cold/warm separated; final challenge and auditable start identity remain open (3.6). |
| 2: grouping, partial NaN, missing resamples | Fixed in the helper; default requires every B resample. |
| 3: runner, failure, H2, provenance | In-memory method/H2 integration fixed; cloud launcher, failure summaries and saved records remain open (3.2, 3.3, 3.5). |
| 4: gain mechanism and frequency claims | Accepted; best-found/frequency wording repaired in the current preregistration and diagnostic. |
| 5: bracket history/archive | Re-evaluation and bounded candidate cache added; wrong endpoint can pass the gate (3.1). The capped cache is not a guarantee to retain every earlier basin. |
| 6: ordinary pipeline sensitivity | Recorded, not performed. |
| 7: final validation | Candidate amendment recorded, not frozen or validated. |
| 8: cost/persistence | Unsupported cloud projections withdrawn; benchmark and persistence remain open. |
| 9: reuse | Manifest still pending; old intervals do not validate refitting. |
| 10: gain precomputation/stop | Missing raw artefact now fails closed; accepted-file readers disagree (3.4). Stop disposition remains with the owner; no AWS action by this review. |

Next bounded step: repair the evidenced gate/launcher/bookkeeping paths, finish
the saved-output contract and reference challenge, and re-check those paths
before committing to the validation run. The fixed-fold refitting candidate
remains worth a declared screening diagnostic; its statistical adequacy is
still unknown. R052 remains with `Entropy SI`.

## Full review 4 — re-check of 8972ba4

Reviewed 12 September 2026 after Claude's 14:23 PDT request. Reviewed code
`8972ba4`, the complete updated brief and preregistration changes through
`d1ab54f`, and Unimog state through `84aaa653`, including the owner's USD 3,000
further AWS spend cap. The affected production paths and their tests were read;
production code, preregistration, manuscript and running processes were untouched.

**VERDICT: not on board with production yet.** Most of Full review 3 is now
fixed. The remaining blockers are reproducible integration faults in checkpoint
identity and the revalidated gain-file contract. The same-training challenge is
implemented; its recovery-start archive still has a gap. Numerical validation
remains a separate open requirement.

Six existing scripts pass: `test_calibrate_gain.py`, `test_refit_bootstrap.py`,
`test_interval_path.py`, `test_gain_gate.py`, `test_gain_gate_integration.py`, and
`test_launcher_env.py`. The launcher test used its real CLI/dry-run branch with
an offline `boto3` substitute that raises on any AWS operation. Four new fixtures
in [2026-09-12_codex_checkpoint_recheck.py](2026-09-12_codex_checkpoint_recheck.py)
exercise the real row/checkpoint and file-writing boundaries with mocked fits,
response data and cloud calls. Their numbers are artificial control-flow
examples. `verify.py` and numerical simulations were not run by this reviewer.

1. **BLOCKING — checkpoint identity permits another dataset's intervals.**
   `analyze.py:368` names files only `refit_seed<seed>.jsonl`; the reader at
   lines 471–478 accepts records solely by seed and `n_rep`. `t1_job.py:220`
   gives every stage one shared `refit_ckpt` directory. `simulate.py:227–232`
   intentionally gives the same member/grid/rep/D the same seed across layer
   grids. Consequently, an `all` job can reuse its one-layer bootstrap in its
   five-layer stage. The fixture runs the actual `one_replicate` path twice:
   one-layer point 1 and CI [1, 1], then five-layer point 5 with the same CI
   [1, 1], **zero five-layer refits**, and `primary_available=1`. A fresh
   five-layer checkpoint produces [5, 5]. The two rows have different valid
   code/config hashes, which do not protect the intermediate checkpoint.

   This also occurs within one layer grid: two declared M3H recovery points,
   `(tau=.5, sep=1)` and `(tau=2, sep=.5)`, share the weighted `grid_tag` 3500
   and dataset seed 1618648715 at rep 0/seed 2026/D4. The second fixture row
   has point 2 and the first setting's CI [.5, .5], with no new refits. The
   existing seed rule therefore cannot serve as a dataset identifier even
   after adding the layer count. Concurrent colliding tasks can also write
   the same file; the demonstrated defect already occurs sequentially.

   Key and validate checkpoints against complete data/procedure identity:
   data or input-manifest digest, generator parameters/readout, exact layer
   IDs, family/concept mappings, numerical code/config, seeds, actual folds
   and B. Keep the intended common random numbers. Reject mismatched or
   inconsistent records before reuse; validate replicate IDs and chosen
   indices. Test one→five layers, the two real recovery-grid points, changed
   folds/config and an interrupted resume. A truncated final JSON line
   currently raises in `json.loads`; specify recovery without silently
   accepting damaged completed records.

2. **BLOCKING — the real revalidation writer still disagrees with the job.**
   `spotcheck.py:119–123` writes `source_code_hash` and
   `revalidated_with`, but neither top-level `code_hash` nor `D`.
   `t1_job.gain_file:103–110` requires both latter fields for *either* file,
   so every file produced by that writer is skipped and the raw file is tried.
   The fixture uses the real writer with mocked new checks: both recorded
   hashes equal the job's expected hash, the revalidation fails, and the job
   nevertheless accepts all twelve raw pairs while the monitor reports FAIL.
   Merely testing a hand-built revalidated file with the raw schema would
   miss this writer/reader incompatibility.

   Define one accepted artefact schema and identity shared by writer, job and
   monitor, with explicit source/reference/analysis hashes, D, scales and
   source digest. A present required revalidation that fails or cannot be
   authenticated must hold the job. Test the real writer feeding both readers
   for passing, failing and malformed/mismatched files. The separate stale
   `check_*` problem **is fixed**: the positive fixture confirms new gain,
   theta, likelihood and runs travel together and obsolete check fields go.

3. **REQUIRED — optimizer recovery discards reference-start provenance.**
   The new challenge uses the same training draw, independent seeded jitter,
   and the declared separated skew starts before test scoring: accepted.
   However, `expected_gain` at `simulate.py:372–374` reconstructs only the
   initial `n_starts` vectors after calling `M.fit`. When the real recovery
   chain adds 16 starts (`models.py:592–611`), `len(cold.runs) > len(cold_x0)`
   causes `_tag` to receive `None` for the entire batch. All 48 initial and
   recovery runs then have `x0=None` and the same `cold:<seed>:<member>` batch
   label. `_starts_at_best` at `simulate.py:478` counts unidentified rows as distinct starts.

   The fixture exercises the actual `M.fit` recovery chain with only its
   optimizer calls mocked: 32 failed initial starts, 16 converged recovery
   starts and the final challenge. The archive loses all 48 initial vectors
   while reporting 16 reproductions. This demonstrates lost audit evidence;
   it does not demonstrate that those 16 actual generated vectors duplicate
   one another. Record vectors and recovery batch/seed provenance where each
   start is generated, preserve it through `expected_gain`, and require
   auditable identities for the reproduction count. Add the recovery path to
   the provenance test before treating the final archive as complete.

4. **REQUIRED BEFORE A COSTLY REFIT RUN — finish output durability.**
   H2 and all refit bands, seeds, policy, outer folds, failure reasons and
   replicate statistics now survive the row boundary. Remaining gaps are
   the acknowledged on-demand checkpoint upload and identity/checksum
   contract. `launch_t1.py:165` supplies `CheckpointConfig` only on the spot
   branch; `run_stage.on_chunk` uploads CSV/progress, and the final copy at
   `t1_job.py:241–244` copies only files directly under WORK, omitting the
   nested `refit_ckpt` directory. A completed-row JSON contains replicate
   statistics, but cannot recover work lost before that row is finished.
   Finish and test interrupted upload/download/resume for the chosen
   execution route before relying on paid resample recovery.

   There is also a smaller saved-output gap: `simulate.py:208–209` retains
   only the workspace companion cluster interval, although `analyze_dataset`
   retains companions for early, late and ws−early too. Preserve the companion
   intervals needed for the declared comparison and verify a full saved-record
   round trip. The statement that nothing computed is lost is too broad.

Disposition against Full review 3:

| Finding | Re-check disposition |
|---|---|
| 3.1 chosen-scale gate and endpoint refresh | Fixed. The final challenged evaluation at the chosen scale is gated/archived. The new lower-wins test verifies refusal on its own failed reproduction. The old defect fixture's upper-endpoint assertion should fail after this repair. |
| 3.2 launcher | Fixed. CLI interval/B reach the actual request and Config/hash test; host environment does not override them. |
| 3.3 failure and coverage bookkeeping | Fixed for the reviewed paths. Valid original points remain in the target; each predictor's finite usable intervals define its coverage denominator; the monitor separates fit and assay failures. |
| 3.4 accepted gain file / check provenance | Check-field replacement fixed. Real file writer and job reader still disagree (4.2). |
| 3.5 saved output and checkpointing | Main row fields fixed; checkpoint identity is unsafe (4.1), durability and remaining companion output incomplete (4.4). |
| 3.6 same-training challenge / start identity | Challenge implemented and accepted; ordinary-start identity fixed; recovery archive incomplete (4.3). |
| 3.7 audit, validation, benchmark, reuse | Open as acknowledged. No approval inferred from passing mocked tests. |
| 3.8 coverage-mechanism wording | Fixed in the preregistration and publication-strategy current state: fitting/selection variability remains under investigation. |

The reported `a508601` M3L diagnostic (scale .7188, gain .00997, check
.01003 ± .00052) is consistent with the accepted within-M2K basin-loss
explanation. It remains a diagnostic from the earlier code. Its sampled local
trace supports the repaired search on that pair; it establishes neither a
general miss probability nor the final twelve-pair artefact or interval coverage.

Next bounded step: repair the two writer/reader contracts and recovery-start
provenance, then re-check those paths. A declared local screening diagnostic
remains supported after the relevant repairs; before spending, freeze its
settings, seeds, counts, decision rule and cost within the owner's cap. The
ordinary inner/outer numerical audit, independent final validation at the
chosen B with a borderline/precision rule, measured cloud concurrency cost,
source-to-analysis reuse manifest and eventual 35-layer band validation remain
open under 3.7. No new AWS launch is approved by this review. R052 remains with
`Entropy SI`; the owner/session retain the existing-job stop decision.
