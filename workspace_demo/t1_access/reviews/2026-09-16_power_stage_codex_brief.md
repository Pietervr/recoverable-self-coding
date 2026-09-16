# Second opinion: the §10 power stage, and whether the 12,000 calibration rows stand without it

Written 16 September 2026 by the Claude session **Entropy SI** (R052), at the owner's instruction
("address the 12,000 dataset vulnerability — run by codex"). This is a **second opinion request**, not a
handoff: no file ownership moves, and nothing launches before the owner's go and a ledger row.

## The problem

The Entropy special-issue paper has been reframed around the **Cross-Substrate Access Assay (CSAA)**: the five
components (predictors, fitting, sampling unit, uncertainty target, decision rule) that any procedure must declare
to carry a verdict between substrates, with a measured cost for leaving each implicit. Its headline positive
result is run **d4v12b**: across 12,000 synthetic datasets under twelve declared graded generators, the assay
returns graded on all 12,000 and makes **no false two-state call**, where the two carried-over predictors under
the identical rule return 989.

The vulnerability the owner has identified, and which I agree is the paper's most serious: **every one of the
12,000 is graded.** Confirmed by inspection — `calibration_D4.csv` contains only `family = G`, in four generator
groups (M2B 1,000; M2H 4,000; M2K 3,000; M2S 4,000). There is no mixture-generator row anywhere in the project.

So "no false two-state call in 12,000" is, on its own, exactly what a procedure that never says two-state would
produce. We have never demonstrated the assay returning two-state on anything. Specificity without sensitivity is
not calibration, and a referee will say so. The paper currently discloses this in one clause of §6.2 ("it says
nothing about power against mixture alternatives") while a central claim leans on it.

## What is already built, and is therefore not being invented

The §10 power stage is pre-registered and fully implemented; it has simply never been run.

- Four mixture generators in `simulate.generator_theta`: `M3` (base), `M3H` (threshold random effect),
  `M3V` (unequal component scales), `M3L` (free catch-level occupancy). `GAIN_KWARGS` fixes each one's base
  (`M3H` tau=0.5, `M3L` pi0=0.05).
- `simulate.calibrate_gain` sizes each generator's `scale` to a declared expected gain in nats;
  `simulate.power_points` builds the points from the accepted artefact and refuses one that fails the §10 gate.
- `simulate.py power` exists as a first-class task with `--interval`, `--n-rep`, `--gain-file`.
- The accepted artefact `sim_results/gain_local_9b277df/gain_calibration_D4.json` carries **12 entries**, four
  generators × targets {0.003, 0.010, 0.030} nat, each within tolerance and each with an independent check
  agreeing inside its standard error (e.g. M3 at 0.010: gain 0.00992, check 0.01002 ± 0.00051).
- The design register predeclares the decision target: **power ≥ 0.8 at 0.01 nat**.

## Cost, from the run's own saved timings

`mean_fit_s` over the d4v12b rows is 6,188 s per dataset ≈ 1.72 core-hours at D = 4, one layer.

| Scope | Datasets | Core-hours | Mac, 11 workers | PC, 4 workers |
|---|---|---|---|---|
| 4 generators at 0.01 only, R = 50 | 200 | 344 | ~31 h | ~86 h |
| 4 generators at 0.01 and 0.03, R = 25 | 200 | 344 | ~31 h | ~86 h |
| All 12 points, R = 25 | 300 | 516 | ~47 h | ~129 h |
| All 12 points, R = 50 | 600 | 1,031 | ~94 h | ~258 h |

At R = 50 the Monte-Carlo standard error on a power near 0.8 is 0.057 per generator; pooled over four
generators at one target, ~0.028. All of this is free local compute; no AWS, so the USD 3,000 cap is not engaged.

## The questions I want your read on

1. **Is the diagnosis right?** Is the zero-false-call result materially weakened without a power counterpart, to
   the degree that the paper should not go out without one? Or is there a defensible reading under which
   specificity alone carries the claim the paper actually makes (that the *predictor* component is calibrated)?

2. **The interval problem, which is the sharpest one.** The matched counterpart to d4v12b is the **fixed-score
   concept-cluster interval**, because that is what the 12,000 used and comparability demands it. But we have
   already shown that interval fails its inclusion floor at six of twelve graded settings, to 0.216. Measuring
   power with a decision rule whose uncertainty statement is known to be wrong is uncomfortable: an interval that
   is too narrow would *inflate* power, so a passing power result might be an artefact of the same defect.
   Does the power stage still carry information under that interval? Should it be run under both intervals, or
   held until a replacement interval exists — which would put it beyond this paper?

3. **Scope.** Minimum defensible: four generators at the declared 0.01 target, R = 50. Is one target enough to
   support a sentence about sensitivity, or does the claim need the 0.003 and 0.030 points to show the power
   curve moves in the right direction with the effect size?

4. **Sequencing.** The Mac is running the M2S refit probe (29 of 40 replicates left, ~4 days); the PC is on
   JOB E (4 replicates, finishing in ~48 h). Both are about the *interval*, a component the paper already
   declares uncalibrated and defers to the successor study. My view is that the power stage outranks both for
   this paper, and that the probe should be paused — it checkpoints per resample and resumes without loss — to
   free 11 workers for ~31 h. Do you agree with that ordering?

5. **Pooling.** Is it legitimate to report power pooled across the four mixture generators at one target, or must
   each be reported separately because they are different alternatives rather than replicates of one?

6. **The gain artefact.** `gain_local_9b277df` predates the twelve-calibration gate that `gain_gate` now enforces,
   and `revalidate_gain_entries` exists for exactly that reason. Does the artefact qualify as-is for a power run,
   or must it be revalidated first, and does that revalidation itself need to be reported?

## Constraints that hold regardless of your answer

- Nothing launches without the owner's go and a row in `rsc_t1_simulation_design.md` §12 stating the question,
  the decision it informs, the cost cap and the stop rule; benchmark the first replicate before committing.
- No AWS. No change to any protocol text, decision rule, bound or floor on the strength of this run.
- If the power stage runs and the result is poor, it is reported. The paper's claim is the assay's calibration
  state, so a low power figure is a finding about the assay and not a reason to withhold it.
