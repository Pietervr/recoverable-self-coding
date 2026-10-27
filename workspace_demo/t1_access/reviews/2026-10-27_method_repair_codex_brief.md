# Method repair: Codex solution brief (round 2)

27 October 2026. R052 (Entropy SI, submission 31 Oct). Owner's instruction: "run this whole analysis by codex with the
explicit aim that we find a solution to the issues." Paths relative to `workspace_demo/t1_access/` unless absolute.

Round 1 (`reviews/2026-10-27_interval_diagnosis_codex_brief.md`, your record
`reviews/2026-10-27_interval_diagnosis_codex_record.md`) diagnosed. **This round must solve.** The deliverable is a repaired
method that we can (i) show working on development evidence now, (ii) validate on new seeds under a pre-declared floor,
and (iii) afford. A list of further caveats is not an acceptable answer; where something cannot be fixed, say what the
smallest honest redesign is and what it costs.

Same limits as round 1: no ssh, AWS, Lengau, launches or live actions; no edits outside
`sim_results/interval_diag_2026-10-27/codex/` (scratch, may run local CPU work: the Mac has the RSC venv
`.venv/bin/python`, jax 0.11.1, `NPROC=1` before importing jax) and the record named at the end. Do not commit.

## Inputs

- Paper: `/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/si_submission.tex` + `sections/`
  (+ `si_supplementary.tex`, `sections/appendix.tex` for the model design: 3 concept families, 91-concept bank).
- Code: `models.py` (members), `analyze.py` (folds :99, inner selection ~:204, `stratified_resample` :312,
  `band_bootstrap` :321, `refit_bootstrap` :613), `simulate.py` (generators, gain calibration), the pre-registration
  `PREREGISTRATION_T1_model.md`.
- Saved rows: `sim_results/d4v12b/calibration_D4.csv` (12,000 graded), the sens600 rows (find them via the paper's
  availability section / `sim_results/`), the omega=2 bank (S4).
- Diagnosis: `sim_results/interval_diag_2026-10-27/` (RSC 38e62fb) and your round-1 record.

## The issues to solve (Claude's inventory, check and complete it)

Measured failures:
1. Fixed-score interval below the 0.90 floor at 6/12 graded settings. Claimed causes: (1) stratified bootstrap with 8 per
   stratum is ~sqrt(7/8) narrow; (2) fitting variance not represented (tau=0.5, omega=0.5); (3) graded/mixture family
   asymmetry (M2S has a concept random scale, no mixture member does) -> heavy one-sided per-concept tail at omega>=1;
   the replicate-mean target is dominated by rare extreme concepts (omega=2 mean -6.87, median -2.07, min -2650).
2. `refit_bootstrap` inherits cause (1) and cannot see cause (3): the running Lane A screen at omega=1 is at risk.
3. Matched human comparison: O5 12/100 two-state calls (allowed <=1), W4 4 unavailable, T2 50/50 unavailable, T3 absent
   (no reference bracket), latency hull coverage 0.73-0.85 in both families.
4. Human fits: Nelder-Mead cap binds for most fits, ~30% still capped after restart; 555-645 ms not restarted.
5. Human verdict depends on rule (315 / run from 315 / Simes 375) and solver (onset 285).
Untested where relied on:
6. Error control near zero expected score difference (largest upper endpoint -0.0067; no near-boundary null).
7. Graded generators outside the fitted family.
8. Detection of two-state data whose concepts differ in scale.
9. Calibration design (8 families x 8 concepts) differs from the confirmatory design (3 families, 91-concept bank):
   strata bias, effective sample and any family-grouped jackknife change.
10. Band rule over the workspace layers; model-recovery stage; power stage at 1,000 per alternative: not run.
11. Readout projection (decoder trained at the extremes, applied near threshold) could create or destroy two states.
12. Inherited human-design leakage unquantified; passive session has no recovery simulations.
13. Start-recipe paired comparison for the scale member outstanding.

## What to deliver

S1. **The repaired interval/decision procedure**, concretely: estimand, statistic, resampling scheme (incl. the strata
    correction and how fitting variance enters), critical value, decision rule. Consider at least: strata-corrected
    bootstrap; refit bootstrap; grouped/concept jackknife with refit (and its validity with 3 families); a calibrated
    critical value on the point statistic (simulation-calibrated null, the paper's option 3); a bounded or robust proper
    score (e.g. Student-t residual members, a censored log score, per-concept score winsorisation declared in advance);
    a changed estimand (median-type or concept-trimmed target, and what it means for the scientific question); adding a
    mixture member with a concept random scale (M3S) to remove the asymmetry. Pick one primary design and justify it.
S2. **Development evidence now.** Whatever can be checked on saved rows, check (e.g. strata correction, estimand changes,
    robust scores recomputable from saved per-concept logq/delta; say exactly which are recomputable). If a small local
    simulation would discriminate between candidates (e.g. a handful of datasets at tau=0.5, omega=1 with an M3S member,
    or a near-boundary null), specify it precisely, estimate its Mac CPU time, and run it if it fits in ~2 hours of local CPU.
S3. **Validation plan** for the repaired procedure on new seeds at the confirmatory design (3 families): settings
    (including a near-boundary null and an out-of-family graded generator), R per setting, the pre-declared floor, and a
    core-hour estimate against what is left on Lengau (CSCI1913 ~7,600 core-h, HEAL1922 100,000 core-h, refit ledger cap
    181,000; one refit resample ~23.6 core-h at 24 concurrent workers).
S4. **Lane A**: continue, amend before coverage is computed, or stop and redirect to S3 - one recommendation, with the
    exact amendment text if amend.
S5. **The other issues (3-13)**: for each, a fix or the smallest redesign, its cost, and whether it is needed before the
    SI submission, before the model study, or never.
S6. **The paper**: the sentences that change if S1-S2 hold, written out, sourced to files/commits, framed as development
    evidence, consistent with the owner's directions (positive reading consistent with the abstract; calibration leads;
    unmet conditions stated as what a decision still requires; no licensed decision implied).

## Output

`reviews/2026-10-27_method_repair_codex_record.md`: S1-S6 in order, a one-line verdict at the top, every number with its
source (file:line, script + output path, or commit). Final message: the verdict line and S1's chosen design in five lines.
