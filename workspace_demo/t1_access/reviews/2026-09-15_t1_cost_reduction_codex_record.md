# T1 cost reduction — final Codex second opinion

Status: COMPLETE, 15 September 2026. Review of Claude Entropy SI's separate
09:35:58 PDT request and [memo](2026-09-15_t1_cost_reduction_memo.md), RSC `b38f0d2`.
This is a review disposition and a concrete proposed validation design; Claude
owns the prospective protocol amendment and execution. It authorizes no launch.

## Disposition

I am on board with a bounded development sequence: diagnose and specify the fitter,
lock one procedure, screen the hardest settings first, and validate it independently
before adoption. Returning to the cluster interval requires an explicit amendment
of the already-invoked replacement decision. Section 7.4 does not automatically
reset that decision, and changes to density floors or parameter bounds can change
the statistical models. The current evidence does not validate a repaired interval.

I would screen a reduced-B refitting interval before developing a new repeated-split
procedure if the cluster candidate fails. Nadeau–Bengio is a defensible development
candidate, with substantial assumptions to check. Nested CV is reasonably deferred
on present cost and adaptation grounds; the memo overstates both its mandatory
repetition count and the categorical objection from within-concept dependence.

The AWS cap remains USD 3,000 of further spend. The owner's rejection of
USD 90,000-scale simulation spending stands. Free academic compute is a promising
route, but neither allocation approval nor T1 throughput has been established.

## System and evidence read

T1 compares training-selected mixture and graded predictors with four-fold inner
selection inside five concept-disjoint outer folds. It scores a concept jointly,
divides the log-score difference by its trial count, then averages concepts/layers.
The coverage target is the **expectation of this complete procedure**, including
data, folds and optimizer randomness. An interval for the particular fitted
predictor's risk, a full-data fit, or the oracle gain answers a different question.
The family-stratified fixed-score bootstrap currently omits refitting variability.
Its replacement clause has already fired. [Pre-registration](../PREREGISTRATION_T1_model.md),
§§7–10, including its opening draft/freeze rule, is controlling.

Reading completed across the saved continuations: the full 681-line current
pre-registration; full 128-line Unimog companion `rsc_t1_simulation_design.md`;
the complete memo; relevant T1 density/fitter and reporting definitions. Both
methods papers were read in order through their appendices: Bates–Hastie–Tibshirani
v4, all 2,588 extracted lines, and the published 2003 Nadeau–Bengio article,
all 3,086 extracted lines (the final 1,486 in this continuation). Public PDFs/text
are in `/tmp/r052_bates_cv*` and `/tmp/r052_nadeau_published*`. No transcript was copied.
Official CHPC policy §§2.1/2.3/3.1/3.3 and the full SU wiki were read, with relevant
claims checked again on 15 September. The registration URL failed to load;
opening that page is not an allocation receipt.

Fresh logs/status in both repos and xs list/chat were checked. The latest wrap
from source `01a0a5fa-f8cb-75d1-ba54-21447d0f239b` to
`01a0a603-ae67-7193-b841-ed0f27c8e414` was independently verified: native/common
completion, exact `GPT: R052 Entropy paper` name and R052 topic, and the sole full
native user receipt at `2026-09-15T17:00:57.221Z`. Prompt SHA256
`5e37f7bc568a2be9eef1290285816f5054ff9c1ac5398f8e1946f6c73e481099`
matches HEAD and checkpoint `c5cf868b`. This receipt concerns this source's wrap.

## Q1. Protocol: a prospective route back exists

1. **Starts and numerical implementation.** Section 10 explicitly leaves a
   pre-v2 numerical-sensitivity audit of §7.4 open. Training-only searches can
   therefore motivate a dated numerical amendment. JOB D is useful paired
   development evidence about the complete nested procedure. It does not establish
   coverage, prove global optima, or identify the cause of undercoverage. A material
   Delta change establishes start-policy sensitivity; it does not show that the
   final start policy is adequate or that fit variability explains the tail.
2. **Model changes.** T1 declares inherited affine absolute-value scales and an
   M3V-specific `0.05 * SD_train` floor; M3H/M3L use exponential scales. The inspected
   implementation reflects these differences. This is not a demonstrated analogue
   of the Melcon implementation issue. Changing floors, feasible parameter ranges,
   asymptotes or predictive continuation changes the family of densities unless
   it restores a documented intended definition. State the scientific rationale,
   affected equations, training-only units and symmetry explicitly. Such changes
   extend the frozen list of permitted revisions and need explicit approval as
   model/procedure amendments. They cannot be labelled numerical housekeeping.
3. **Interval decision.** Sections 8.2/10 record cluster failure and invoke refitting.
   The document remains draft v1.2, so it does not bind the final study forever to
   that candidate. Reconsideration must nevertheless say explicitly that a revised
   procedure will be assessed for a return to the cluster interval, why, and under
   what prospective acceptance rule. Preserve d4v12b and its failure as development
   history. If no effective procedure change is justified, rerunning the same
   candidate until it happens to pass is not a defensible reset.
4. **Before fresh validation.** Freeze the member-specific start counts, batches,
   selection/recovery/tie handling, any changed densities, interval/B/quantile rule,
   primary family predictor, target, seed roles and complete code/runtime identity.
   Select a cheaper recipe by declared training-fit accuracy, stability and cost
   criteria on development data. Originals, resamples and reference repetitions
   must use that same policy. New numerical/model policies require new reference
   targets and appropriate gain/recovery checks; the gain-calibration procedure
   itself has its own declared reference policy and must retain explicit lineage.

This supports development followed by independent validation, with a final
pre-v2 decision. It does not reopen the completed JOB D or Melcon plan reviews.

## Q2. Concrete least-favourable-first validation

### A. Scope, counts and stopping

For **one locked primary procedure at one D on the single synthetic layer**, use
the memo's order: M2S omega 2, 1, 0.5; M2H tau 0.5, 2; M2K alpha 1; then the
remaining retained nulls in a committed order. Declare independent dataset/fold/
optimizer/bootstrap streams and fixed seed prefixes before running. Different
settings can share a deliberate paired design, but duplicate datasets are never
extra independent replications within a setting.

Use attempted-dataset looks at **100, 200, 400**, with **1,000 as the sole optional
terminal extension, declared and costed now**. The first two looks permit failure
only. At 400, pass a setting only when both criteria below pass. Otherwise stop on
failure or extend an indeterminate setting to 1,000 if the declared resource budget
allows it. At 1,000, anything neither passed nor failed is **indeterminate**. If the
extension cannot be afforded, indeterminate at 400 remains indeterminate. Do not
add looks or keep extending until passage. A failed setting rejects this candidate
for all-setting adoption, allowing the rest of its campaign to stop and save cost.
An administrative stop, including one for an unresolved reference tail, is not a
statistical failure or a pass.

The fixed thresholds are coverage **0.90** and FPR **0.064**. Do not recompute the
latter as 0.05 plus two SE at the smaller R. The precision/adjudication rule below
is a proposed strengthening of the raw empirical threshold rule and must appear
in the amendment. It can leave a procedure close to either threshold unresolved.

### B. Reference uncertainty precedes coverage certification

For each setting, obtain an independent, policy-matched uncertainty interval
`C_g = [a_g, b_g]` for the complete-procedure mean. Fix it before examining the
validation outcomes. It must be independent of both procedure selection and the
validation rows. A compatible old bank needs a justified reuse/independence
manifest; the old-policy omega-2 bank cannot stand in for a changed policy.
Never estimate truth from the same validation rows and apply a binomial interval
as though their inclusion indicators were independent observations of known truth.

For each usable primary interval `I_i`, count:

- `x_minus = number with C_g wholly contained in I_i`;
- `x_plus = number with I_i intersecting C_g`.

On the event that the true mean lies in C_g, the containment probability is a lower
bound on true coverage and the intersection probability is an upper bound. Use
`x_minus` for passage and `x_plus` for failure. This deliberately conservative
construction also handles reference uncertainty that straddles many endpoints;
evaluating only the bank's point mean would hide that uncertainty.

For the error accounting below, C_g must cover all twelve targets simultaneously
with probability at least 0.99, for example via per-bank error at most 0.01/12.
**This is a requirement for the stated error guarantee, not a claim that the
available banks meet it.** A conventional mean ± z SE from one tail-dominated bank
does not establish it. Document the finite-moment/tail assumptions, independent
bank precision and stability across independent blocks; report extreme rows and
their influence. Leave-largest diagnostics quantify instability and do not remove
those rows from the target. No finite bank size guaranteed sufficient follows from
the old SE or the single omega-2 extreme. If a defensible C_g cannot be obtained
within the budget, coverage remains unresolved. Merely increasing R cannot repair
uncertainty in the target. A change of the mean target needs its own amendment.

### C. Exact integer boundaries

Let `y` be the number of mixture calls among all attempted datasets at a null.
The following table assumes all attempted datasets have usable primary intervals,
so the coverage denominator and the FPR denominator both equal n.

| Look n | Coverage failure if x_plus ≤ | FPR failure if y ≥ | Coverage pass if x_minus ≥ | FPR pass if y ≤ |
|---:|---:|---:|---:|---:|
| 100 | 78 | 17 | no early pass | no early pass |
| 200 | 164 | 27 | no early pass | no early pass |
| 400 | 338 | 44 | 373 | 15 |
| 1,000 | 866 | 92 | 920 | 48 |

Either failure rejects; both pass conditions are needed at the same eligible
terminal look. For example, known-target coverage 360/400 is indeterminate, not
passed merely because its estimate equals 0.90. Even with known truth, a true
coverage of 0.91 has only about 6.44% probability of meeting the coverage pass
boundary at 400 and 14.65% at 1,000. At true coverage 0.95 these probabilities are
95.20% and 99.998%. These are marginal fixed-look probabilities, not sequential
power or a joint probability that all settings pass. A wide C_g reduces pass power.
At true FPR 0.05, the corresponding FPR pass probabilities are only 14.99% and
42.20%. Thus these counts are practical for the observed near-zero-FPR regime;
they do not guarantee a decision for a procedure operating near nominal 5% FPR.
Keep that limitation in the budget rather than loosening the rule after seeing it.

The arithmetic is in [the stdlib script](2026-09-15_t1_cost_reduction_arithmetic.py)
and [its output](2026-09-15_t1_cost_reduction_arithmetic.json). It sums integer
binomial masses for rational thresholds; boundary decisions have no floating-point
tail approximation. It verifies mass sums, recurrence divisibility, symmetry,
agreement with direct combinations, and the adjacent nonqualifying count.
The method is one-sided exact binomial inversion; see
[NIST's exact-binomial limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm).

For passage use a one-sided tail probability at most **0.02 per final look**:
`P_0.90(X >= x_minus)` and `P_0.064(Y <= y)`. The two final looks spend at most
0.04 for any violated constraint. Requiring **every** null and both endpoints to
pass is an intersection-union test: if any constraint is violated, passing all
requires that violated constraint to pass. No extra factor of twelve is needed
for this single all-pass assertion. Adding the simultaneous reference error of
0.01 bounds false all-pass probability by 0.05, conditional on the stated sampling
and reference assumptions. These are not simultaneous 98% intervals for every row.

For failure use a tail probability at most **1/2400** at each endpoint, setting
and look: `P_0.90(X <= x_plus)` or `P_0.064(Y >= y)`. Four looks × two endpoints ×
twelve settings spend 0.04 by a union bound. Adding reference error bounds an
incorrect failure assertion anywhere in this fixed family by 0.05. The deliberately
strict failure cutoffs still reject catastrophic coverage cheaply; milder shortfalls
can remain indeterminate. Do not reuse these budgets to select among several
candidates, predictors, D values or band rules. Allocate error across prospective
adoption attempts, or reserve untouched final validation until all candidate
selection is over. Fresh seeds alone do not justify resetting this error budget
after each failed adoption attempt.

### D. Denominators and remaining stages

Coverage remains conditional on usable intervals, as §10 specifies; theta is
estimated using all valid point estimates, including those without an interval.
FPR keeps `simulate.summarize`'s denominator of **all attempted datasets**. Count
unavailable outcomes separately; they are not graded or inconclusive calls. At
each fixed attempted look, compute coverage tails using the actual usable count m
(the script accepts `--n m`), while FPR uses n. The exact binomial assertion is
conditional on m under independent identically distributed row/availability pairs.
Do not use the table's n=400 cutoff for m=397. Require at least 400 usable intervals
for a pass under this design; missing intervals may therefore require the declared
1,000-attempt look. No extra seed replacement or unannounced extension is allowed.

A new original-fit failure with no defined point cannot silently disappear from
the unconditional target. Resolve its mathematical handling before claiming that
target is validated. Interval-only failures remain assay-performance results and
need the protocol's explicit disposition; lowering FPR by making the assay
unavailable is not evidence of an improved procedure.

Passing twelve single-layer nulls opens the remaining development/validation
stages. It does not validate the alternatives, power, recovery, another D, or the
full layer-band rule. Retain the declared alternative coverage and power work,
the five-layer pilot and post-PILOT band validation. Report the ensemble from shared
fits as sensitivity unless it was selected as primary before this validation.

## Q3. Fallbacks and which to screen first

### Reduced-B refitting

This is the closest fallback to the already-declared replacement. Reducing B
changes the randomized interval procedure and its failure probability; retain
full inner selection, fitting/recovery and all-concept grouping on every resample.
Every required resample must be usable under the present rule. Choose B, interval
type and quantile convention on development evidence, lock them, and validate
that exact procedure independently. More validation datasets do not make a
noisy within-dataset quantile equivalent to its infinite-B limit.

| B | Expected draws below a true 2.5% quantile | SD on the probability scale | Probability of no draw below it |
|---:|---:|---:|---:|
| 50 | 1.25 | 0.02208 | 28.20% |
| 100 | 2.50 | 0.01561 | 7.95% |
| 200 | 5.00 | 0.01104 | 0.632% |

These are deterministic binomial calculations for independent bootstrap draws
and a continuous conditional distribution. They concern tail ranks, not the SE
of an endpoint in nats and not coverage itself. The current B=50 probe is useful
development evidence; it cannot be assumed to deliver stable 95% endpoints.

My first new candidate would be **B=100 refitting**, subject to the probe and a
measured resource ceiling, with a predeclared independent second bootstrap stream
on a fixed development subset to assess endpoint/decision variation. Retain B=200
as the comparator where already available; any added work is separately costed.
Archive complete prefix-indexed draws so legitimate B comparisons can reuse fits.
Their identities still bind B and the executed procedure; never relabel a B=50
checkpoint as B=200. Selection/ensemble/bands should share eligible refits.

Warm starts that alter fitting behavior require explicit procedure development.
They are excluded from this proposed fallback. Implementation acceleration needs
numerical and failure-path checks of the executed procedure; a JAX batching idea
or equal package versions is not yet a speed or equivalence result.

### Nadeau–Bengio corrected repeated splits

The published method uses
`s_d^2 = sum((d_j - mean(d))^2)/(J-1)` and
`Var_hat(mean(d)) = (1/J + n_test/n_train) * s_d^2`, with a t_(J-1) reference.
The factor multiplies the **sample variance of split means**, not an already
divided variance-of-the-mean estimate. Its correlation approximation depends on
training stability and approximate distributional assumptions; it can be liberal.
J around 15 is the authors' empirical recommendation, with diminishing returns.
[Nadeau–Bengio 2003](https://link.springer.com/content/pdf/10.1023/A:1024068626366.pdf),
§§3.1, 4 item 6, 5.2, Appendix A and note 14.

For a T1 development candidate, I would specify J=15 independent concept-level
split draws, paired across the two families, with training-only inner selection.
All trials/layers stay with their concept; preserve the eight family strata and
explicit test weights. State the integer training/test counts and ratio for each
stratum. T1's uneven 64-concept five-fold sizes cannot be replaced silently by a
generic 80/20 split. The repeated-split mean needs its own complete-procedure
reference unless equivalence of its expectation to the existing target is shown.

Ordinary resampled train/test fits and a repeated entire five-fold pipeline are
different procedures. The latter does not acquire the former's correction by
substitution. Cost the selected learner, including inner fits, at actual sizes;
J need not mean J complete outer pipelines. The paper does not establish validity
for T1's strata, joint score, selection and tail. Screen, then use the same fresh
all-setting gate; a citation cannot replace it. I would not prefer this unadapted
candidate over reduced-B refitting on current evidence.

### Bates–Hastie–Tibshirani nested CV

The memo's 200 repetitions are an experimental setting, not an Algorithm 1
requirement. However, Appendix F.8 reports needing many repetitions for stable
SE estimates. K-squared fitting calls per repetition is the relevant count; each
call in T1 would fit the training-selected learner, not another entire outer-CV
pipeline. K=5, R=200 gives a naive 1,000-fold fit-count ratio to ordinary CV,
not a universal runtime lower bound. [Bates–Hastie–Tibshirani v4](https://arxiv.org/pdf/2104.00673v4),
Algorithm 1, §§4.2, 5, 7, Appendix F.8.

Its MSE/CI target is instance-specific ErrXY, unlike T1's unconditional theta;
the OLS point-estimand result about Err does not remove that mismatch. Independence
within concepts is unnecessary if a whole concept can be treated as one independent
observation. Fixed family strata, joint loss and paired algorithm differences
still need adaptation; paired comparison is future work in §7. Thus I agree to
defer it as an unpriced adaptation with no demonstrated cheap advantage. I do not
agree that 200 is compulsory or that within-concept dependence alone rules it out.
Small-R validity/stability for T1 remains unestablished.

## Q4. Machines, pooling and honest cost accounting

### Numerical and sampling contract

Bitwise cross-architecture equality is not generally necessary. Before pooling,
Claude should commit a parity plan and results for an identical serialized
development panel on Mac, PC and CHPC: every member/null family, omega-2 extremes,
near ties, mixture data, recovery/failure paths and actual bootstrap duplicates.
Reuse the existing small JOB D panel where suitable and add only missing cases;
this is a portability check, not a second adoption-grade simulation campaign.

Bind source/config/start-policy/wrapper digests, Python/JAX/jaxlib/numpy/scipy
versions, x64, BLAS/XLA/thread settings, OS/CPU, exact data/folds/start vectors and
every RNG role. Compare density/objective/gradient calculations at fixed parameters
first, then the fitted pipeline: per-start outcome, selected member, per-concept
and band score, interval endpoints, decision and availability. Compare actual
loaded implementation hashes; a changed wrapper needs its own truthful hash.

A reasonable **initial engineering tolerance** for score/endpoints is
`1e-6 nat/trial`, to be fixed before the comparisons and justified against the
smallest 0.003-nat effect and decision margins. This is a proposal, not measured
parity. Raw parameter equality is unnecessary when different parameters express
the same density. Different optimizer basins, unexplained member choices, recovery
status or availability require investigation even when a rounded final call agrees.
For near-zero or reference-endpoint cases, a tolerance must not hide a changed
decision/inclusion. A canonical-runtime replay rule must be fixed before validation
and applied in the reference bank too. Preserve both outputs and count the dataset
once; if differences can move aggregate
disposition, stratify or validate the runtimes separately before pooling.

The exact-binomial proposal assumes iid evaluation outcomes for a fixed procedure.
Passing a finite parity panel is evidence, not a proof of identical outcome laws.
If residual architecture effects are material, fixed heterogeneous machine blocks
cannot simply use iid binomial counts. One explicit alternative is independent
per-row machine randomization with predeclared fixed probabilities and a matching
reference bank; this defines a mixture-over-runtimes target and must be disclosed.
Another is separate runtime validation. Do not assign all hard cells to one
architecture, allow runtime assignment to depend on fit outcomes, or double-count
paired replay rows. Preserve architecture-specific failure and score summaries.

### Capacity is conditional on measurement and access

CHPC's published policy grants a new approved programme 100,000 CPU-hours for
six months; academic programme use is free. Its default limit is 240 cores across
running and queued work, with job-count limits; scheduling and additional access
remain conditional. Scratch can expire after 90 unused days. These are programme
rules, not evidence that this programme has been approved.
[CHPC Accounts Policy v2.6](https://wiki.chpc.ac.za/_media/chpc:chpc_accounts_policy_v2.6.pdf),
§§2.1, 2.3, 3.3 and 4. SU's wiki confirms 1,000 trial CPU-hours and a fee thereafter;
the 1,000-core week limit belongs to the queue, not each user.
[SU HPC wiki](https://www0.sun.ac.za/hpc/index.php?title=Main_Page).

Correct the memo's unconditional claim that the cluster stages fit that allocation.
Its approximately 19,800 hours are historical Mac-equivalent projections. If r is
actual CHPC charged CPU-hours per such equivalent and s is the actual revised-policy
work multiplier, even those listed stages alone fit 100,000 only if `r*s <= 5.05`.
The two-null refit figure of 41,000 fits only if `r*s <= 2.44`. Additional S1/S2 rows,
reference banks, optional 1,000-row extensions, failures, rework and overhead must
also be budgeted. These inequalities illustrate the missing conversion, not a
benchmark or a reservation of capacity.

JOB D's 56,647.375 / 5,766.015625 = **9.824353** is a historical loaded PC worker
elapsed-time ratio for the specified cost model. It is not measured CPU time or a
universal multiplier for every setting, changed member recipe, resample or machine.
Do not discount the seven-worker contention a second time by dividing loaded
worker costs by four physical cores. Measure completed balanced batches at intended
concurrency, JIT/initialization, tails, failures, peak memory and scheduler charging.
Preserve checkpoint/transfer time and an explicit safety margin in the ledger.

Likewise, 12 Mac cores × 24 hours × 30 days is theoretical availability, not promised
productive capacity. Claude's 09:50 PDT transcript reports the Mac probe straggler
holding ten workers idle; at 09:53 it reports PC test-harness repairs before real
fits. These are the latest job readings used here, not a new monitor check.
Calendar completion cannot yet be inferred by dividing old core-hours by installed
cores. Claude owns benchmarks, scheduling and any implementation changes.

## Q5. Conditions that prevent endorsement

- A silent reset of the replacement clause, or model changes described as mere
  numerical correction without their explicit prospective amendment.
- Selecting the fitter, predictor, interval or B using validation outcomes and
  retaining those same rows as validation of the selection; deleting a difficult
  null, tail row or failed resample; hidden warm starts or leakage across folds.
- Treating starts sensitivity, zero FPR, a dispersion ratio, the B=50 probe, or
  a single-layer pass as proof of complete coverage or band validity.
- Calling coverage passed with unresolved reference uncertainty, changing the
  0.90/0.064 thresholds, optional extension beyond the declared looks, or treating
  indeterminate/unfinished cells as passed. The omega-2 stress condition stays.
- Pooling unequal procedures/targets without a justified runtime contract, or
  representing worker elapsed time and unapproved academic allocation as measured
  CPU throughput and guaranteed completion.
- A plan exceeding the AWS cap, depending on USD 90,000-scale simulation spend,
  or proceeding to CONF/freeze before the required calibration and other gates.

The practical next decision is to read the already-running development evidence,
specify the cheapest scientifically adequate candidate and its reference plan,
cost it by stage, then commit the prospective amendment. If the reference tail or
the required validation cannot be resolved within the resource ceiling, report
the model-side assay as unvalidated and keep that limit in the paper. Expense
does not make an unresolved validation into a pass.

## Ownership and delivery

Codex owns this record and its deterministic arithmetic only. No fits, generated
datasets, bootstrap samples, BMS/EEG analysis, cloud jobs, deployment, protocol or
production-code edits, freeze or push were performed for this review. Claude owns disposition,
protocol/code/production/manuscript, execution, monitors, PC dispatch and R052 front
matter. Codex appends only the R052 log and retains final delivery responsibility
until this unchanged complete record appears in Claude's native tool_result.
Closure will be recorded in the R052 log without changing this delivered record.

JOB D (`016151a`, disposition `b1885a5`) and Melcon v7 (`e42846e`, disposition
`9cbcc0a`) and their complete native receipts remain closed. This is one separate
cost-review reply. Other-owner results, models/PIDs, load_verification.csv, audit
archives and manuscript/counsel artifacts remain with their owners.
