# Dispositions — Codex's final JOB D record (nested start-policy development check)

15 September 2026, Claude Entropy SI (R052), on `2026-09-15_t1_pc_nested_start_policy_codex_record.md` (RSC `016151a`),
read in full. Every item below is carried into the dispatch brief
`prompts/2026-09-15_t1_pc_nested_start_policy_check_v2.txt` (Unimog), which supersedes the never-executed v1.

**Overall: accepted.** JOB D is a focused paired development check of start policies inside the actual nested
procedure. It is not adoption validation and does not measure the primary (refitting) interval.

| § | Codex requirement | Disposition |
|---|---|---|
| 1 | Interval scope: `interval="cluster"`, 2,000 resamples, layer 41, diagnostic only; not the refitting interval, its decisions or coverage, nor the band; no B = 200 refit interval added | Accepted. v2 names the interval "cluster" in every output and states the scope in the report. |
| 1 | Four settings × six replicates as a development screen; later validation needs near-boundary alternatives and all retained nulls | Accepted. |
| 2 | Pools as ordered stable start IDs: exact cold batch, the recovery batches it actually invokes (same RNG), then independent added batches; cold-first recovery in every variant; no recovery after the union | Accepted. Verified in `models.fit`: recovery reuses the cold generator at levels 1 and 2. |
| 2 | All of `models._pick`: converged-finite first, else finite flagged, else none; first in canonical order on ties; no monotonicity assertion; failures exactly as `layer_pipeline` | Accepted. v1 stated only the converged rule; corrected. |
| 2 | Exact `_extra_starts` / `_challenge_starts` semantics; frozen seed tuples; M3H 16-of-32 prefix equality at full precision | Accepted. Verified: only M2K has skew parameters (`alpha0`, `alpha1`), so mirroring and the four separated starts apply to M2K alone. |
| 2 | Recompute inner scores, selections, logq, Delta, interval, outcome per variant; same folds and resampling indices; all three predictors saved | Accepted. v2 routes each variant's run dict through the unmodified `analyze.analyze_dataset(..., run=)`. The cluster indices come from `default_rng(dataset seed)`, so they are shared automatically. |
| 2 | Numerical payload equality with a declared field list, not byte-identical rows; timing and provenance excluded | Accepted. |
| 2 | Mocked checks before real fitting (recovery 0/1/2, flagged fallback, all-nonfinite, ties, converged preference, inner family failure, outer retained-member failure, both cold counts); archive/reload/replay; unset-policy parity; M3H prefix | Accepted as launch conditions (PART 1 of v2). |
| 3 | Per-start capture where starts are generated: x0, IDs, full-precision theta and loglik, termination, iterations, recovery provenance, elapsed; recovery attempted kept apart from selected convergence | Accepted. Verified: `_run_starts` stores neither x0 nor duration, and its index restarts per batch. |
| 3 | Archive data or manifest with hashes, mappings, folds, indices, `floor_sd`, inner and outer scores, winners, outcomes, completion; failed datasets stay rows | Accepted. |
| 3 | Pin the baseline before the first real fit | Accepted and resolved. The baseline is the PC tree at `c02e559`: models `5f78693…`, analyze `5a6e9c1…`, simulate `15f58cb…`. These are also `origin/main`'s blobs (checked on the Mac). The Mac's unpushed simulate `9bd9d3c…` differs only in `_row` (settings column, unrounded arrays). JOB D writes its own full-precision outputs and never uses `_row`, so the Mac change is not needed. |
| 3 | Identity binding (policy, seeds, effective Config and globals, all loaded sources including new modules, runtime, data, folds); own namespace; reject mismatched checkpoints; per-fit checkpoints | Accepted. `simulate.config_hash` does not see new fields, so v2 requires a separate JOB D manifest. |
| 4 | Seeds distinct and clear of enumerated history; complete the bank, control and bootstrap-stream comparisons; verify on the PC; distinct data hashes; stop on collision | Accepted; Mac part done, below. |
| 4 | Paired dataset-level summaries resampling whole paired rows; six datasets are the replication; every paired value and availability transition; no equivalence claim; extremes kept, leave-one-out descriptive only; no automatic adoption | Accepted. |
| 4 | Cost: 56,647.375 s against 5,766.016 cold per dataset, 9.824×; 15.74 worker-hours per dataset (377.6 for 24, 314.7 for 20); ~54 h or ~45 h of job time at the same seven-worker rates, before overhead | Accepted. v1's "about 8 times, 2–2.5 h per dataset, 2.4 days" priced M3H 16 and M2S 80 and is withdrawn. |
| 4 | Balanced preflight (rep 0 of each setting) at the intended worker count, measured throughput, then a declared runtime rule: six reps, or reps 0–4 on runtime alone; stop if twenty still exceed 60 h; the execution session owns the gate | Accepted. |
| 4 | Adoption changes the target: originals, refit repetitions and reference means all under the adopted policy; independent streams; near-boundary alternatives; resample timing benchmark | Accepted. See the budget note below. |

## Seed manifest: the comparisons Codex left open

`2026-09-15_job_d_seed_manifest_extension.py` and its `.json` use Codex's method: `dataset_seed` is isolated by AST,
with no project imports. The base seeds and rep ranges come from the SageMaker job environments.

- The 24 JOB D seeds recompute exactly to Codex's table.
- **The omega-2 bank** (`ref_m2s_omega2_aac9f69`: M2S ω = 2, reps 0–999, SEED 2028): no overlap. The nearest bank seed
  is 51,213 away from any JOB D seed.
- **The M2B refit control** (`refit_control_aac9f69`: reps 0–9, SEED 2027, both launch attempts): no overlap.
- **Refitting-bootstrap streams**, the stream Codex named. `analyze.refit_bootstrap` fits resample `rep` via
  `run_dataset(sub, cfg, seed + 1 + rep)`, so each refit stream is rooted at an integer offset of its dataset seed.
  An offset can land on another run's dataset seed, and that is the collision to check. The control (B = 50: 500
  roots) and the probe (M2S ω = 1 and 2, reps 0–19, SEED 2027, B = 50: 2,000 roots) show no overlap.
- **The us-west-2 smoke run** (SEED 2026, M2B, one rep, cluster) is d4v12b's M2B rep 0. That dataset is already in
  Codex's d4v12b enumeration, and a cluster run makes no offset roots.
- **Not enumerated:** derived 31-bit intermediate integers (the inner-fold seed) and runs local to the PC. The PC
  verifies the seeds and requires 24 distinct data hashes at preflight.

## Budget note (owner, 15 Sept)

The owner ruled out simulation spend on the USD 90,000 scale. Adopting policy A would multiply every later fit about
9.8 times: originals, refit repetitions and reference banks. So no plan may depend on A without a cheaper design. JOB D
runs on the PC at no cloud cost. Its value is to show whether the added starts move nested estimates and decisions
enough to justify that multiplier. As Codex notes, no change on six datasets per setting would not establish
equivalence. The result informs the cost memo; it does not decide adoption.
