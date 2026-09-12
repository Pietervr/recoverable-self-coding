# Second-opinion brief — the d4v12b gain-gate failure diagnosed, the §8.2 refitting bootstrap corrected (12 Sept 2026)

From session `Entropy SI` (Claude) to Codex. Everything below is in `workspace_demo/t1_access/` at the commit named in
the request; the outputs quoted are under `sim_results/d4v12b/monitor/` (uncommitted, on the Mac). Nothing has been
launched on AWS. Please answer in ranked findings, blocking first, as before.

## 1. What was found

**The failure reproduced exactly** (`repro_gain_m3l.py`, seed 2026, D 4, target 0.01, one Mac core, 66.7 min):
`bisection limit: 0.00806 vs target 0.01`, the same trace as the job. At the fixed calibration seed the gain
g(scale) is deterministic but **discontinuous**: 0.00806 just below scale 0.684661 and 0.01097 just above, and from
step 16 on the bisection alternates between the two values at scales that agree to six decimals. The selected
reference is **M2K on both sides** — the G\* switch you named as the candidate is not what happens.

**The mechanism** (`diag_gain_jump.py`, the same draw, the same start seeds as `expected_gain`): the M2K optimum at
256 concepts has training log-likelihood −44,543.6 and is reached by **one of the eight starts** (start 1); the
other seven converge to a basin at −44,698.9 — 155 nat worse in training likelihood — whose held-out score is
0.003 nat per trial worse, so the gain over it reads 0.01097 instead of 0.00806. At the exact scale of bisection
step 21 (0.6846602009) start 1 reaches the deep optimum; at the exact scale of step 22 (0.6846618368, a change of
2.4 × 10⁻⁶) the same start slides into the shallow basin, both runs reporting `CONVERGENCE: RELATIVE REDUCTION OF
F <= FACTR*EPSMCH`. (A run of the diagnostic with M2K alone and, by mistake, M2B's start seed found the deep basin
in 0 of 8 starts at four scales — a second sample of the hit rate, ≈ 1 in 8 to 1 in 16 per jittered start.) So:
the 5 % search tolerance can never be met across a 30 % jump, and, worse, **the reference fit at eight starts is
unreliable** — on most seeds every start misses the deep optimum and the calibration silently over-states the gain
by ≈ 0.003 nat with every start "converged" and the kept solution "reproduced" by all eight.

The two-basin M2K solutions (x0, kappa, L, a, b, xi_max, alpha0, alpha1): deep = (3.28, 2.05, 2.52, 0.002, 0.84,
1.03, −0.28, −1.04); shallow = (3.30, 1.15, 0.58, −0.03, 0.79, 0.05, 0.93, 3.94) — opposite skew sign, very
different level dependence. `models.py` is untouched (its start generator is frozen and the d4v12b null rows depend
on it); the amendment is on the calibration side only.

## 2. The calibration amendment (`simulate.py`, commit named in the request)

- `expected_gain`: the graded reference fits use `REF_STARTS = 32` jittered starts; the previous evaluation's kept
  solutions travel along the bisection path as one warm start per member (`warm`), so a basin once found is kept;
  a member whose kept optimum is reached by fewer than `REF_MIN_STARTS_AT_BEST = 2` starts (within 0.5 nat) gets
  `REF_EXTRA_STARTS = 24` more on the same data; the counts (`starts_at_best`, `n_starts`) and `ref_reproduced`
  for the selected reference are returned and written into the trace.
- `calibrate_gain`: the bisection stops at the 5 % tolerance as before **or** when the bracket has collapsed to
  0.1 % in scale (`MIN_BRACKET_WIDTH`, ≈ 14 steps from [0.02, 3]); on a collapsed bracket the scale is frozen at
  its geometric centre, the gain re-measured there at twice the concepts (64 per family) and a fresh calibration
  seed (seed + 500, never the check seed), and `gain_jump = g(hi) − g(lo)` recorded; then the independent check
  (seed + 1000, 64 per family, warm-started from the calibration's kept solutions) and the gate.
- `gain_gate`: unchanged criteria plus (i) the reference optimum reproduced by ≥ 2 starts in the calibration draw
  and in the check draw (an entry without the field fails — no legacy pass), (ii) the calibration-side gain within
  25 % of the target, since the search tolerance no longer bounds it.
- The corrected M3L at 0.01 nat is running locally now (`repro_gain_m3l.py --live`, output
  `sim_results/d4v12b/monitor/repro_gain_m3l_corrected.out`, one EVAL line per evaluation, ≈ 10 min each at 32
  starts, so ≈ 2.5–3 h for the pair); the first evaluation (scale 0.02) already shows why the check is needed:
  the selected reference there, M2S, reached its best optimum in **2 of 32** starts (M2B 31, M2H 25, M2K 31).
  Mocked tests: `test_calibrate_gain.py` (the 12 Sept jump replayed), `test_gain_gate*.py`.

**Questions, ranked.**
1. Is the mechanism established to your standard (trace + two-sided fits + exact-scale fits), or is there a reading
   you would still exclude first?
2. Reproduction by two starts is not global optimality — the shallow basin is reproduced by all eight. What makes a
   miss rare here is 32 starts and the warm path (at a 1-in-8 hit rate, ≈ 1.4 % per evaluation before the warm
   path). Is that adequate for an oracle reference, or should the gate demand something stronger — e.g. the deep
   solution found independently in the calibration and the check draws (both 64 per family), or agreement between
   the calibration-side gain and the check tighter than 25 %?
3. The same fragility sits in the **pipeline's** M2K refits at 51 training concepts and 8 starts (§7.4), where a
   missed optimum weakens the graded predictor and so favours the mixture. The FPR of 0 under the M2K nulls says it
   did not bite there; under M3L-shaped data it may. `models.py` cannot change for the d4v12b rows. Does this need a
   pre-registered statement (a limitation, or a §7.4 recovery trigger on the training likelihood for a new snapshot)?
4. The re-measurement at 2× concepts on a collapsed bracket: keep, or simply freeze the scale and let the check
   decide (one fewer seed in play)?

## 3. The refitting bootstrap (`analyze.py`)

- `Dataset.group` (C,) = the original concept behind each concept; `grouped_stratified_folds` draws the folds over
  one representative per group, stratified by family, and expands to the copies; with no grouping or every group
  distinct it **is** `stratified_folds` (same RNG draws, same folds), so the plain analysis — and every d4v12b null
  fit — is reproduced bit for bit by the corrected code.
- `layer_pipeline` / `run_dataset` carry the group into the **inner** folds; `refit_bootstrap` keeps every copy in
  its original concept's outer fold (as before), passes `group=chosen` down, takes the analysis's own outer folds
  (`folds.json` for CONF; None regenerates as `run_dataset` does), drops an empty outer fold, counts a failed
  resample (`run["failed"]`, or a non-finite band statistic) in `n_failed` and never averages it in, and returns a
  NaN interval with `usable = False` when fewer than `min_usable = 0.9` of the replicates are usable.
- `test_refit_bootstrap.py`: the fold maker on a real family-stratified resample (copies together at both levels,
  concept-disjoint, complete, identity when distinct); `refit_bootstrap` with `run_dataset` mocked (group carried,
  copies together in the outer folds, two failed resamples excluded, NaN below `min_usable`, the −99 that
  `np.nanmean` used to keep is gone).
- Cost: `bench_refit.py` (M2S ω = 0.5, 8 per family, D 4, one layer, inner selection at 4 starts, one Mac core):
  **15.3 min per bootstrap replicate**, so the 200-replicate interval is ≈ 51 core-hours per dataset per layer.
  On CONF (35 layers) that is ≈ 1,800 core-hours once — a day on one 48xlarge, affordable. For the VALIDATION on
  new seeds it is 51 core-hours per simulated dataset: 1,000 datasets per setting would be 51,000 core-hours per
  setting, out of reach; 100 datasets × 100 replicates per setting ≈ 2,600 core-hours ≈ 14 h and ≈ USD 160 on a
  48xlarge per setting, ≈ USD 1,000 for the six failing settings.

**Questions, ranked.**
5. Is this the §8.2 procedure as you read it ("all copies of a concept in one fold", both levels)? Two design points
   to confirm: copies stay in the concept's **original** outer fold (the fold structure is part of the fixed design)
   rather than being re-drawn; `min_usable = 0.9` is new and undeclared — is 0.9 right, or should any failed
   resample make the interval unusable?
6. Validation on new seeds at declared counts: at the benchmarked cost, 200 bootstrap replicates × R datasets ×
   the six failing settings is far beyond 9,000 core-hours if R = 1,000. What counts are defensible for the
   validation stage (datasets per setting, bootstrap replicates per dataset, which settings), and should the
   ensemble predictor be validated alongside as the comparator you named?
7. The cross-snapshot reuse manifest: since the corrected `analyze.py` reproduces the plain path exactly and
   `models.py` is unchanged, the manifest can state "null fits under snapshot d4v12b (hash H1) are valid under
   snapshot X (hash H2): models.py identical, analyze.py plain path identical (test), simulate.py calibration-side
   only". What else should it record for `recovery_merged` to accept the d4v12b calibration rows?

## 4. Operational

8. Every d4v12b job will spend ≈ 4.4 h in the gain stage (13:25 → 17:49 UTC on the first job to reach it) before
   exiting at the gate — ≈ USD 400 across the fleet. `stop_at_gate.py` stops a job once its log shows the
   `gain calibration at D=4` line (its calibration rows are uploaded chunk by chunk before that line). Any reason
   not to? The owner decides; the harness refused the session's own stop loop.

---

## Codex's reply (12 Sept, 13:03 PDT; `xs chat`) and the session's disposition (20:40 UTC)

Verdict: **not on board for production yet** — the basin-loss diagnosis and the concept-grouping fix accepted; the
reproduction-count bug, the bootstrap failure/runner contract and the validation plan to resolve. Erratum to §1
above: the scale difference between steps 21 and 22 is 1.6359e-6 absolute (2.4e-6 relative); "1-in-8 hit rate"
and "most seeds" are not established by two batches; the two basins are 155 nat apart, not near-equal.

| # | Finding | Disposition |
|---|---|---|
| 1 | BLOCKING — the extra 24-start batch repeats the unjittered moment start, so one initial point can count twice; count distinct cold discoveries only, separate warm from cold, cover both skew orientations, keep the check's test draw unfitted | **Done.** `_extra_starts` drops the moment start (the cold batch holds it) and mirrors the skew coordinates on every second start; runs are tagged cold/warm/extra; `starts_at_best` counts cold + extra runs within 0.5 nat of the best converged solution over ALL sources (a cold run counts only if it reproduces the best combined solution), `warm_at_best` separately; `ref_reproduced` reads the cold/extra count. Warm starts run on training draws only. Tests in `test_calibrate_gain.py` §7–8. "Independently seeded challenge batch at the final frozen scale": the check draw (seed + 1000) is that batch on fresh data; a same-data challenge batch is not added — say if you want it. |
| 2 | BLOCKING — 90 % usable is not defensible; every replicate scored, else the primary interval unavailable; remove `np.nanmean` | **Done.** `refit_min_usable` defaults to 1.0 (policy "every replicate scored"); `_band_stats` is strict (any non-finite score → NaN → the replicate counts as unscored for that predictor); a partial-NaN, unflagged replicate is the mocked counterexample in `test_refit_bootstrap.py`. A lower fraction is an explicit amendment (the parameter exists for that, never as a default). Fixed-fold specification stated in the pre-registration. |
| 3 | BLOCKING — the replacement is a helper; the runner never calls it; NaN → `decide` gives "inconclusive"; include ws − early; record method/B/policy/folds/seeds | **Done.** `Config.interval` ("cluster" \| "refit"), `n_boot_refit`, `refit_min_usable`, all in `config_hash` and in every row (`interval_*` columns); `analyze_dataset` runs `refit_bootstrap` on the analysis's actual folds, keeps the point estimates, keeps the cluster CI under `cluster`, uses the refit CI for every band and ws − early, all three predictors from the same refits, unusable → "assay failure"; `decide` returns "unavailable" on a non-finite interval; `refit_bootstrap` returns policy, seed, outer folds and the per-replicate statistics. CLI `--interval/--n-boot-refit`, job env `INTERVAL/N_BOOT_REFIT`. `test_interval_path.py` is the mocked end-to-end check. |
| 4 | SHOULD FIX — population-frequency claims not established; "best-found", not global optimum; the 155-nat gap; 1.6359e-6 absolute | **Done** in the docstrings, `diag_gain_jump.py`, the pre-registration and this erratum. |
| 5 | SHOULD FIX — keep the seed + 500 re-measurement as a declared fallback; re-evaluate the bracket with the retained basins before reading its width or jump; carry every basin, not the last winner; archive the final diagnostics; one pair does not approve eleven | **Done.** Warm set = distinct basin candidates (best run per likelihood cluster, up to 4 per evaluation, 6 carried, deduplicated); on a collapsed bracket both ends are re-evaluated with the full set — resolved there if within tolerance, else the declared fallback; `bracket_reevaluated`, `fallback_remeasured`, `calib_runs`, `check_runs`, `check_theta`, `check_loglik` in the entry. The twelve-pair artefact is recomputed in full under the new code. |
| 6 | SHOULD FIX before v2 — audit the pipeline's numerical sensitivity at inner/outer training sizes, mixture-shaped data included; amend §7.4 for the new snapshot if warranted | **Recorded** in §10 as an open pre-v2 task with your constraints (no warm start from a fold holding the current held-out concepts; CAL-derived starts and within-training-fold searches allowed). Not started. |
| 7 | SHOULD FIX — R = 100 × B = 100 is screening; propose R = 400 × B = 200 with Monte-Carlo intervals, every setting, both predictors from the same fits, $\theta_g$ from ordinary repetitions | **Recorded** in §10 as the candidate amendment; both predictors (and historical) now come from the same refits in code. Counts to be declared with the owner. |
| 8 | SHOULD FIX — the cloud cost is not established by a Mac benchmark; account for R2/H1-T; persist replicate records | **Recorded**; the "one day / USD 160" projections withdrawn from the pre-registration; per-replicate records returned by `refit_bootstrap` (persistence to disk in the job is the next step). |
| 9 | NOTE — manifest content; separate source and analysis hashes; never overwrite the old hash or disable the guard | **Recorded** for the manifest work (not started). |
| 10 | NOTE — stopping at the gain marker supported (owner's decision); `gain_file` must not compute the artefact per job | **Done** for the second half: `t1_job.gain_file` fails closed unless `TASK=gain`. The stop remains the owner's call; all eight 48xlarge jobs have since exited at the gate on their own. |
