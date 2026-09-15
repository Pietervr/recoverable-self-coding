# Codex second opinion — Melcon v7 development plan

15 September 2026. Scoped request from Claude Entropy SI at 08:47:43 PDT.
Reviewed `workspace_demo/melcon_port/DEVPLAN_v7.md` at RSC `1100eb1` end-to-end.

**FINAL — acceptable development sequence, with a short specification amendment
before Phase 1 and a substantive correction to C3 before candidate testing.**
The plan preserves v6 and separates development from independent evaluation.
It does not yet specify three executable candidates or an unambiguous selection
rule. No diagnostic fit, data generation, implementation or validation was run
by Codex. Claude owns those actions, the protocol and manuscript; Codex owns
this review and the R052 log. The owner go already exists.

This is separate from JOB D (final record RSC `016151a`) and the completed v6
stage-C opinion (`e490f3b`). Neither earlier review is reopened or repeated.

## System and source check

v6 trains a decoder on two blocks, then trains the densities on one of the
other blocks and scores the remaining block. The roles swap within that half,
then the halves swap. Each block is scored once; evidence is the mean of four
block log-score sums. The three-model group rule is unchanged by this plan.

Read the whole v7 plan, the complete final stage-C opinion, `likelihood.py`,
`recording.py`, `decoder.py` and `synthetic.py`; inspected the battery's identity
and seed/recording-manifest functions. The prior full preregistration and battery
reading remains applicable: these source files and the preregistration have no
diff from the completed stage-C review. No numerical audit was repeated.

The reviewed plan and these source files also have no working-tree difference
from `1100eb1` at this review's check:

| File in melcon_port | Git blob at the reviewed commit |
|---|---|
| DEVPLAN_v7.md | bc44cf832cd9894095d8b91bbca78a4c66873806 |
| likelihood.py | 4803b4c716758b2798a1b0ed7e081d39a006d643 |
| recording.py | 1c7571c7101a133a6ee1eac85389a9b9e56df434 |
| decoder.py | 31617e72b6c26034e7923229d5de575114c6233d |
| synthetic.py | 0982eac1f8283cb51160be78a82961a835816864 |
| battery.py | a039f41f67909f7a1d40c33a187f04b786487a8e |

## Q1. Is this the required pre-fit development commitment?

**Yes in purpose and sequence.** It retains the failed battery, fixed scientific
baseline and forbidden moves, limits candidate development, and reserves fresh
data for the locked procedure. Choosing numerical C1 settings after seeing the
diagnostic panel is legitimate declared development. They need not be guessed
before Phase 1; they must be frozen before comparative candidate fits and before
the fresh development check is opened.

Before Phase 1, commit these specifications:

1. **A deterministic panel manifest.** Define the recording-level loss used for
   ranking, its normalization and how ten windows are combined. The cell contains
   3 replicates × 34 templates: state that selection pools these 102 recordings,
   or explicitly choose another denominator. For example, if the aim is the
   worst window, define the recording statistic as the maximum over main windows
   of `4 * (evidence_null - evidence_graded) / n_trials`. Do not alternate between
   this and a mean or raw summed score after inspecting the panel. Define the
   median convention, tie order and distinct-record rule; save the forty exact
   parent manifests, identities and selection values before regeneration.
2. **An exact idealized readout.** Resolve the incompatible descriptions
   “matched signal-to-noise” and “no decoder or sensor noise” as in Q3. Freeze
   its trial structures, generator/strength/drift cases, number of draws, seed
   role, scoring folds and outputs. This is part of Phase 1, not an unspecified
   additional experiment chosen after seeing its result.
3. **A logging-only diagnostic implementation.** Keep v6 fitting, starts, retries,
   training scaling, retained trials, score aggregation and model availability
   unchanged. Commit the instrumentation and check numerical reproduction on
   its first selected recording before proceeding. Capture all starts, including
   failures/retries; a missing solution must still have an archived failure row.
   Preserve full precision and identify start order, selection/ties, termination,
   iterations, seed tags, bounds and per-fit elapsed time. Verify archive reload
   and refuse mismatched inputs. Do not add starts to diagnose a near-tie unless
   that becomes a separately declared development operation.

The four density folds are **four total across the two halves**, not four per
half. Forty recordings × ten windows × four folds gives 1,600 fold-window
units and 4,800 initial model fits across the three models, before retries.
These are not 4,800 independent recordings.

The planned per-trial losses, means/SDs and dose-support diagnostics address the
missing evidence from v6. Add the two-state mixing weight, component means/SDs
and its marginal mean/SD: a large mixture SD due to separation does not show
that its component SDs are safely away from a floor. Record bound distances
in normalized parameter-range units as well as the stated absolute 1e-6 flag;
location, log-scale and logistic parameters have different units.

Phase 1 can proceed after those bounded clarifications are incorporated and
dispositioned. It need not wait for a final candidate or a validation decision.

## Q2. Are C1–C3 legitimate and symmetric, and is selection sound?

### C1 — legitimate regularization, with an exact predictive definition

An effective-SD floor and an asymptote cap are defensible development candidates;
neither is established as the remedy by the existing failure. Specify the
training statistic called “readout range” (maximum minus minimum, an interquantile
range, or S are different choices), its fallback and numeric multiplier. A range
from a limited training dose span need not identify the high-dose asymptote;
the cap is a regularization assumption and can introduce bias. Report how often
it binds and the resulting losses under each generator.

Define the same scientific quantities for both families:

- Floor the **effective conditional/component SD**, including catches, not just
  graded `exp(s0)`. Graded SD is `exp(s0 + r*L)`; flooring `exp(s0)` alone leaves
  contraction possible. The mixture needs a floor on its component SD, not on
  its marginal SD. If a common minimum SD is being claimed, specify how the null
  model's existing `0.05*S` minimum relates to it too.
- The comparable asymptotic *shifts* are graded `a1` and two-state
  `exp(delta0) + exp(delta1)`. A cap on their individual components is not the
  same as a cap on the sum. State what happens to the intercept, hemifield term,
  zero-effect boundary and catch law.
- Implement the floor/cap in a normalized density used consistently for training
  and prediction. Clipping a reported log loss is not this model. A hard floor
  creates a kink; the gradient and convergence test must match the chosen hard
  or smooth definition. A coupled asymptote constraint needs an appropriate
  parameterization or constraint treatment, not two independent caps presented
  as the same constraint. Test normalization, gradients, boundary behavior and
  finite predictions after implementation.

Equal numbers on different parameters do not guarantee equal predictive
flexibility. Retain null-like valid boundary solutions and the full G1–G3/X1/X2
comparison. C1 must not quietly replace the graded spread law with a constant SD
or classify every active bound as a failed fit.

### C2 — legitimate training-defined extrapolation policy

Clamping dose is a valid conditional predictor if it is explicit. It assumes
that responses beyond the observed training range plateau at the nearest
endpoint; it does not establish that the underlying scientific response does
so. All test trials remain scored at their actual observed responses.

Use the pooled **present training trials** to define endpoints in raw log
contrast, carry them through the training-only scaling, and apply the same
clamp to graded L (mean and spread) and both mixture dose functions A and H.
Catch behavior is still determined by the catch flag, not by clamping an
artificial catch dose. Keep hemifield handling and the null unchanged. Report
losses/counts separately below, within and above training support, for both
families, without deleting any category.

With exactly this definition, C2 is the identity on every training dose.
Consequently its training objective, gradients, starts, fits and chosen theta
should be exactly the baseline's under the same numerical path. Only
out-of-support predictions change. This is a useful deterministic acceptance
check and permits reuse of archived baseline fits when identity and replay
are verified. It is not an observed numerical pass in this review. It also
means C2 cannot be claimed to repair a training-search miss or an in-support
collapse; the diagnostics must establish which problem occurred.

### C3 — the proposed allocation is already v6

`decoder.split_half` and `recording.recording_scores` already implement:

| Decoder blocks | Density-training block | Test block |
|---|---:|---:|
| 1, 2 | 3 | 4 |
| 1, 2 | 4 | 3 |
| 3, 4 | 1 | 2 |
| 3, 4 | 2 | 1 |

Thus “two decoder blocks, one density-training block and one test block,
rotated” is not, by itself, a new candidate and gives each density fit no more
training observations. Correct the title/claim and either withdraw C3 or give
an explicit changed allocation table before testing it. Additional pairings
would be a fold-allocation sensitivity; they still leave one training block
per density fit. If trials receive several predictions, fix their weights and
the evidence normalization so repeats are not counted as extra independent
data or used to multiply the evidence scale supplied to BMS.

Actually increasing density training with four blocks requires another tradeoff
(for example, a different allocation of decoder training), or additional data.
That would need an explicit plan amendment, new calibration if the decoder
changes, and renewed costing. This review does not substitute such a candidate
or authorize its implementation. If the allocation is identical, recalibration
alone does not make C3 a distinct method.

### Candidate count and the fresh check

A cap of three **fully specified configurations** is reasonable for bounded
development. It is not a guarantee against selection bias. Count alternative
floor/cap pairs, combinations such as C1+C2, changed allocations, extra start
budgets and retries of the fresh experiment as additional candidates or plan
amendments. Do not hide an unlimited tuning grid inside the name C1.

Before candidate comparisons, commit the numerical configurations and an
operational ranking/stop rule: the severe-loss definition and unit/denominator;
failure and availability handling; how X1 recovery and false-two-state calls
under graded laws constrain selection; the cost ceiling; tie order; and a
**no acceptable candidate** outcome. “Best restores predictive stability” alone
does not resolve a tradeoff between tail loss, missing fits, calls and cost.
Keep every candidate result and the unchanged baseline on the same fresh
development data. C2 may reuse its baseline training fits as described above.

The proposed six fresh groups (X1 strong, G1 strong, G3 weak, both drifts) are
a useful bounded check, not a validation sample. One group per cell gives
almost no precision. In particular, this check contains no G2 and cannot report
fresh graded-call performance under **all** G1–G3. The G2 diagnostic panel is
not a substitute for a 34-recording group. Either keep and label that limited
scope, or prospectively add a G2 cell pair if its known skew misspecification
is to enter fresh group-based selection, with the extra cost declared. This
omission does not contaminate the later full validation, but leaves a known
development uncertainty.

C1/C2 should use identical fresh synthetic recordings and declared common
random streams for paired comparisons. If a genuinely changed C3 needs
recalibration, specify whether Phase 2 compares fixed v6 amplitudes or newly
calibrated strengths. The former isolates a procedure change at fixed input
signal; the latter changes both the procedure and its signal scale. Do not
mix those comparisons or call an uncalibrated changed decoder strength-matched.
Any C3 development calibration remains separate from its final independent
calibration checks.

## Q3. Is the diagnostic panel and idealized check adequate?

**Worst plus median is suitable for mechanism diagnosis, not for estimating
how often the mechanism occurs.** Its selection deliberately enriches extreme
graded losses. Two selected recordings per cell cannot establish population
failure rates, typical behavior of every fold or a group decision. Report all
their windows and folds with that sampling description. The median of the
chosen recording-level statistic is not necessarily a median fold or window.
Using the known v6 held-out values for this declared development selection is
permitted; selecting a fit's start using those values remains prohibited.

The forty-recording panel can remain bounded as planned. It does not symmetrically
sample two-state disasters; label that limitation. If two-state prediction
stability is to drive candidate exclusion, use a predeclared two-state-tail
diagnostic subset or the complete paired fresh check, not a claimed absence of
such failures in a panel chosen on graded loss. Ordinary and extreme examples
can support a mechanism; frequencies and causal uniqueness remain unestablished.

For the idealized check, the clean first specification is the **stochastic latent
readout z**, retaining its intrinsic noise, hemifield and declared drift, with
the same training/test trial structures but no fitted decoder or sensor noise.
Do not replace it by the latent conditional mean or pass true mixture labels or
generator parameters into fitting/initialization. True quantities are diagnostic
outputs only. Keep training-only scaling and all test trials.

This is an ideal-observation check, **not matched weak/strong SNR**. Multiplying
z by a positive amplitude scales both its signal and intrinsic noise; it does
not reproduce the weak/strong decoder AUCs created by additive sensor noise.
If a matched-noise oracle is desired instead, define its observation equation,
noise distribution and training-only calibration separately before running it.
Removing the decoder and sensors together does not distinguish their individual
contributions. Persistence of a failure would implicate density/estimation/dose
support as sufficient problems in that setting; disappearance would not identify
a unique cause of the full-pipeline failure.

G2 is skewed while the fitted graded density is Gaussian. G3 has SD `1+L`, which
need not be represented exactly by `exp(s0+r*L)`. Even the idealized experiment
therefore has purposeful approximation error. Do not promise exact graded
recovery or infer a software defect merely from a family preference. Keep its
outputs separate from the complete sensor/decoder battery and its group claims.

## Q4. What protects later independent validation?

Keep the planned **all 60 groups / 2,040 recordings** on new data after lock,
including every generator, strength and drift. Retain all exclusions, unavailable
models and technical failures in the denominator and apply the existing
complete-replicate/common-cohort rules. A failed validation returns to development;
changing a candidate after reading it requires another untouched validation set.

At lock, seal the exact predictor, bounds/floor/clamp and scaling definitions,
starts/recovery, decoder allocation, score aggregation, group rule, availability,
criteria and reporting, loaded source/runtime hashes and all seed roles. Include
new diagnostic/wrapper modules in the applicable identity; an output directory
named v7 is not an identity check. Preserve v6 seals and verify archive/reload and
unset/baseline behavior without rewriting those artifacts.

The battery currently uses phase-tagged synthetic generation, while likelihood
start tags in `recording_scores` are subject/task/half/fold/window. Merely
changing `SEED_PHASES` does not propagate a new phase to those optimizer tags.
Specify whether fixed optimizer/group randomness is intentionally retained as
part of the procedure, or independent phase tags are added. Fixed algorithmic
randomness with independent generated validation recordings is not itself data
reuse; it must not be described as fresh optimizer streams. Seal complete tuples
for development, any calibration search/check/terminal draws and validation so
that “a new phase” is demonstrably disjoint at the data level.

C1/C2 can retain v6 amplitudes only while generator, decoder, strength statistic,
templates/cohort and calibration settings are identical. Carry parent calibration
hashes and unresolved-strength/X2-inversion flags; do not relabel copied values
as freshly calibrated. A changed decoder/allocation requires fresh calibration
with independent check seeds and predeclared applicability, as the plan says.

Three groups per cell remain a coarse acceptance screen. “Certified” overstates
what passing would establish; say **passes the declared synthetic acceptance
criteria**. G1–G3 can still pass the existing rule through inconclusive outcomes.
If positive graded recovery is part of the desired scientific claim, declare
its requirement at lock before validation. Otherwise report graded-call rates
and limit the resulting claim to what the unchanged criteria test. Do not pool
the heterogeneous sixty groups as sixty replicates of one operating condition.
These interpretation and reporting requirements follow the simulation-study
principles in [Morris, White and Crowther (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/).
Independent evaluation after development selection is essential even with a
small candidate list ([Cawley and Talbot, 2010](https://jmlr.org/papers/v11/cawley10a.html)).

### Cost and closure

The arithmetic `612 / 2040 * 8.9533` gives about **2.69 worker elapsed-hours**
for three copies of the six-group fresh check at the old rate. It does not
measure the revised models, instrumentation or any changed C3 allocation.
Include the paired baseline, idealized draws, candidate-panel refits, archive
I/O, summaries and any recalibration; credit reused C2 fits only after replay
equivalence is checked. Additional G2 groups would add 68 recordings per
candidate. Treat “core-hour” entries as planning estimates until CPU usage is
measured, and distinguish worker elapsed time from total wall time.

Benchmark each implemented phase under its actual concurrent Mac load, with a
written limit and pause/report rule before its main work. No cloud is needed
for this plan; the standing USD 3,000 cap and the owner's newly recorded
rejection of USD 90,000-scale simulation spending remain intact. This opinion
does not adopt or cost a separate T1 alternative, authorize EEG, freeze the
secondary analysis, change publication receipts or launch any job.

The review is complete. One substantive xs reply follows its local commit;
full unchanged-record receipt is tracked in R052. Claude dispositions the
specifications and retains all implementation, diagnostic and validation work.
