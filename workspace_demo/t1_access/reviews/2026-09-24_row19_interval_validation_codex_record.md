# Row 19: refitting-bootstrap interval screen — Codex second opinion

24 September 2026 UTC / 23 September local. Reviewer: GPT: R052 Entropy paper,
native session 01a0d17f-15ca-7691-85e0-3615eb5fe7af. Request: Unimog-Projects
`prompts/2026-09-24_row19_interval_validation_second_opinion.txt`, commit
`8c57291e`; proposed row 19 at `694b81c4`. Transport receipt
`cec5044a-f0e5-5222-92bb-f226bba97b6d` accepted after review ownership was
recorded in R052, Unimog commit `d1cc5a3d`. Claude retains the design, ledger,
implementation and dispatch. This is a second opinion, with no scientific ownership transfer.

**Verdict: NOT ON BOARD with row 19 as written.** Preserve the owner's go,
but the outstanding Codex gate is not satisfied. First commit row 4's procedure
and reference plan; then qualify and price the intended refit workload in a
short bounded slice. My preferred first coverage screen is omega 1, with omega 2
retained as a required stress condition whose reference may remain unresolved.
A positive screen does not authorize the next five settings automatically.

The proposed comparison is coverage of the complete procedure's expected
held-out score difference at 64 concepts, D=4 and layer 41. The cluster interval
uses the original out-of-fold scores; the replacement reruns the nested fits
on each concept resample. Each generated dataset can carry both intervals.
This is neither oracle-gain estimation nor validation of a future start policy.

## 1. First setting: omega 1, after the procedure is locked

Omega 2 is the worst historical failure but presently a poor first *coverage*
purchase: its reference error can change the conclusion more than the additional
100 interval datasets would resolve. I independently recomputed the saved bank:
n=1,000, mean -6.869911, MCSE 2.678379, median -2.065273; the minimum is
-2650.300023 and removing that one point moves the mean to -4.223835.
Removing it or substituting the median changes the estimand and is not a repair.

A deterministic re-reading of the completed B=50 probe makes the problem concrete:

| Setting | External reference mean ± 2 MCSE | Refit / cluster at the mean | Refit count over that entire target range |
|---|---|---|---|
| omega 1 | -0.869513 ± 0.022483 | 17/20 / 14/20 | 17/20 throughout |
| omega 2 | -6.869911 ± 5.356758 | 6/20 / 3/20 | 4/20 to 18/20 |

These ranges are **sensitivity ranges**, not established confidence sets for
the expectation, particularly in the heavy tail. The calculation visits every
interval endpoint and intervening segment, not just the range's two ends.
The omega-2 binomial interval conditional on one chosen bank mean omits this
reference uncertainty; buying more interval datasets alone does not remove it.

Omega 1 has a known cluster failure, a much tighter reference and an unresolved
B=50 result: the exact 95% interval on 17/20 is [0.6211, 0.9679]. It is a more
interpretable first test of the B=200 candidate. This is an order-of-testing
recommendation, not permission to omit omega 2 or change its target. Omega 2
could instead be a useful first *futility* test if undercoverage can be shown
even at the most favourable target in an independently justified reference set.
That condition is not supplied by the present ±2-MCSE statement. Row 7 already
says to stop spending there if its target cannot be pinned down.

Use the full reference: the top-level
`sim_results/ref_m2s_omega2_aac9f69/calibration_D4.csv` has only 128 rows.
The ten `final_2026-09-15/calibration_D4.shard*of010.csv` files have 1,000
distinct replicate IDs. Their mean agrees with the 1,000 bank rows in
`reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv`; matched point values
differ by at most 1.42e-14 after serialization. Pin the actual files and hashes.

## 2. Size: 100 × B=200 is a useful gross-failure screen, conditionally

Keep B=200 if that is the candidate interval being assessed. At B=200, each
2.5% tail has roughly five resamples; at B=50 it has roughly 1.25.
Larger B reduces bootstrap simulation noise. It does not add unseen extreme
concepts to a dataset, repair a start policy, or identify a tail-dominated target.
The B=50 evidence is development evidence, not a verdict on B=200.

At n=100, coverage MCSE is 0.030 **at coverage 0.90**; it is 0.0412 at 0.216
and at most 0.050. The blanket statement that n=100 cannot certify 0.90 is
mathematically too strong: for a fixed known target, 96/100 gives an exact
two-sided 95% interval [0.90074, 0.988996]. But the chance of at least 96/100
when true coverage is 0.91 is only 4.74%, and this does not account for target
uncertainty, multiple settings or repeated looks. The ledger also explicitly
makes the 100- and 200-dataset looks failure-only. Retain that distinction.

For the single-look failure screen in §4 below, power to stop is 80.8% at
coverage 0.80, 32.8% at 0.85, and 99.9% at 0.70. Thus n=100 can support a
useful spending decision about gross undercoverage, but is weak near the
boundary. It is worth considering after policy, reference and price are settled;
it is not worth USD 306 merely to compare an uncertain target with a historical
0.216. The saved probe has already shown a positive paired movement.

## 3. Cost: benchmark first; the present USD 306 is not a forecast

There are two distinct substitutions in that number:

1. The 51 Mac-core-hour basis was measured at **M2S omega 0.5**, not omega 2
   (`PREREGISTRATION_T1_model.md` §10 and `bench_refit.py`).
2. Eight vCPUs are treated as eight workers with Mac-core throughput and full
   utilization. Row 5 already records a 3.7× Mac advantage on a different,
   matched M3 workload. It is not a refit ratio, but it contradicts using
   parity of core-hours as an established fact.

The completed probe's per-row timing fields provide more relevant caution.
Mean summed bootstrap fit time for B=50 is 27.54 worker-hours at omega 1 and
45.30 at omega 2. Fourfold linear extrapolation plus the mean original fit is
110.66 and 182.02 hours respectively. These are **fit-wall-time extrapolations
under the probe's actual concurrent load**, not new B=200 measurements, exclusive
CPU time, cloud forecasts or complete costs. Resumed rows' `wall_seconds` do
not include all previously checkpointed work; they are not the total cost.
The extrapolations nevertheless show why the omega-0.5 benchmark cannot price
the stress setting.

Even retaining the original 51-hour basis and USD 0.48 per instance-hour:

| Cloud time per unit Mac work | First 100 | All six failing settings at 100 |
|---|---:|---:|
| 1× | USD 306 | USD 1,836 |
| 2× | USD 612 | USD 3,672 |
| 3.7×, illustrative only | USD 1,132 | USD 6,793 |

No row in this table is a measured Spot quote. The launcher itself labels its
c8i price an estimate and applies a region factor. AWS reports Managed Spot
savings through billable versus training seconds; a previous discount is not
a forward price commitment. Use the correct regional training tariff, instance
hours and measured billing ratio, with a conservative reserve.
[AWS billing fields](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeTrainingJob.html),
[Managed Spot](https://docs.aws.amazon.com/sagemaker/latest/dg/model-managed-spot-training.html).

The public EC2 c8i.2xlarge specification is 8 vCPUs on 4 cores with 2 threads
per core and 16 GiB RAM. Confirm the actual training host and measure aggregate
throughput at the intended concurrency; do not assume eight independent physical
cores. Row 1 already records two out-of-memory c8i.2xlarge control attempts.
Reducing worker count or changing instance shape changes the cost arithmetic.
[AWS instance specifications](https://docs.aws.amazon.com/ec2/latest/instancetypes/co.html).

The initial slice must precede the full 100: predetermined datasets and resample
indices, the actual nested refit path, compilation and original-fit cost,
per-resample time, peak memory, worker utilization, and persisted/resumed counts.
Measure the matched Mac slice as well if a Mac-to-cloud ratio is claimed.
`TASK=bench` uses an M3H fit/pipeline, so it is not this M2S refit benchmark.
Set a separate small dollar/runtime ceiling for this qualification, inside the
existing row/global caps; it is a proposal for the source to make concrete, not
a launch authorized by this review.

USD 450 can remain the maximum willingness to spend, but a 1.5× trigger is
not that cap: 306×1.5=459; 450/306=1.4706 before overhead. Enforce an aggregate
bound over qualification, every shard, restart and retry, with stopping reserve.
At the assumed USD 0.48 rate, USD 450 buys at most 937.5 instance-hours before
other charges. A fleet runtime budget at a verified conservative rate is
controllable; a projected throughput ratio is not a monetary hard stop.
The current launcher sets per-job runtime and wait clocks, not a dollar budget.
[AWS stopping clocks](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_StoppingCondition.html).

I used the supplied Cost Explorer balance, without accessing the account.
USD 2,207.56 minus USD 1,978.78 is USD 228.78, not 228.75; the three cents are
immaterial here. More substantively, the documented cap begins 12 September
21:50 UTC, and the ledger leaves that day's post-cutoff charges unseparated.
Reconcile them and attributable non-training costs; identify the USD 0.12/day
usage type rather than inferring it is a running job. This does not alter the
owner's go or lift the USD 3,000 ceiling.

## 4. Stop on inadequate absolute coverage; report the paired improvement

Do not invent a “material move from 0.216” threshold. A move to 0.50 can be
large, convincing and still useless for the required 0.90 coverage.
The 0.216 is also from historical rows/reference; the current cluster comparator
must use the same new datasets and same external target as the refit interval.

A concrete proposal for **one standalone, single-setting, single-look screen**:

- At 100 usable intervals, stop for futility if the one-sided 97.5% exact
  binomial upper bound is below 0.90: **83 or fewer covered out of 100**.
  At 83 the upper bound is 0.897735; at 84 it is 0.905690.
- Carry reference uncertainty. For an independently justified target set T,
  compute Kmax = max over theta in T of the number of intervals containing theta.
  Require the same upper-bound failure at Kmax. Even the most favourable target
  must fail. If reference uncertainty prevents that decision, report unresolved.
  The current heavy-tail ±2-MCSE range is not automatically a valid T.
- Anything not stopped is “not ruled out at this look”, not a row-8 pass.
  Do not automatically buy the other five settings. A further look or setting
  follows the committed prospective rule and an updated budget.

The 2.5% bound is conditional on a fixed target; adding a valid 99% independent
target set bounds the one-look erroneous-stop probability by at most 3.5%.
This is not a family-wide sequential guarantee. Row 4 must allocate error across
the actual settings and looks. For illustration, reserving 1% for simultaneous
target sets and dividing 4% over 12 settings × 4 looks would use alpha=0.04/48;
the n=100 failure threshold would then be **79**, not 83. This conservative
illustration is not an adopted replacement for row 8.

Report both marginal coverage counts and the paired discordant counts:
refit-only, cluster-only, both and neither; their difference divided by the
common paired denominator is the coverage gain. A paired test can quantify
improvement but cannot substitute for the absolute 0.90 requirement.
Report all attempted datasets, valid points, usable intervals and failures;
use the actual usable n in the bound, and do not silently replace failed rows.
The coverage target and denominators remain those of §10.
[Exact binomial intervals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).

A negative result would mean that this specified policy/B=200 interval fails
this setting, subject to its reference analysis. It would not establish that
every refitting bootstrap fails, or identify the source of the failure.

## 5. What otherwise wastes the money

**Wait for row 4 for validation.** Its gate says no validation run before the
prospective amendment is committed. The new start policy applies to the original
fit, bootstrap refits and reference expectation alike. An old-policy run now
would remain old-policy development evidence, with no automatic pooling into
new-policy validation. That can be worth buying for a separately stated method
question, but row 19 currently claims to advance row 8 and the confirmatory
programme. The reference calculation is cheaper than bootstrapping each
reference dataset, and must match the adopted procedure.

**Pairing is genuinely implemented.** `analyze_dataset` computes the original
pipeline once, saves its cluster interval beside the refit interval, and gets
selection, ensemble and historical scores from each shared refit.
`simulate._row` persists those companion endpoints. Raising the number of
datasets to 100 and B to 200 does not require a second fit campaign for the
cluster comparison. This is distinct from reusing an earlier B=50 campaign.

**A short B=5 or B=50 job does not automatically extend to B=200.**
`dataset_identity` binds B, configuration, code, data, runtime and folds;
`stratified_resample` also consumes random draws family by family in arrays
whose size depends on B. Changing B changes the identity and generally changes
even the early resamples. If a timed slice is intended to contribute later,
it must already use the locked B=200 configuration and a bounded subset of its
exact indices, with verified continuation. The reviewed runner has no dedicated
resample-slice interface. Do not claim reuse without implementing and checking it.

**Prove recovery, including its cost.** In `analyze.py:349`, the original
`run_dataset` executes before bootstrap checkpoint recovery; that original
analysis is still uncheckpointed. `t1_job.py:111` can log a restore error and
continue without restored work; its mirror upload happens at dataset-chunk
boundaries. SageMaker's managed synchronization is the intermediate protection,
not proof that this application resumed correctly. Demonstrate restoration in
the intended image, identity/checksum acceptance, increasing completed-resample
counts and final agreement with an uninterrupted qualification case. A failed
restore must hold for diagnosis, not silently buy the same fits again.
[AWS checkpoint behavior](https://docs.aws.amazon.com/sagemaker/latest/dg/model-checkpoints.html).

Fix sources and runtime before production, use a new namespace and a declared
seed/task/shard manifest, and set four inner starts explicitly if that remains
the adopted policy: the cloud launcher defaults to eight. Fresh seeds are
required; the default 2026 would reuse historical datasets. Refit resamples are
sequential within a dataset on the current `one_replicate` path; packing
datasets can improve utilization but does not shorten that chain. Chunk barriers,
startup, memory and restarts belong in the price.

If reference or validation rows cross machines/environments, the earlier
three-M3 cluster panel does not qualify this refit path. Preserve its result;
qualify the actual policy, M2S setting and refit path before pooling or asserting
matched numerical procedures. Full runtime versions matter even where the short
code/config hash agrees.

Finally, use an external-reference evaluator: `simulate.summarize` uses the
same evaluated run's mean as truth, and `t1_job.run_stage` uploads that summary.
It must not be presented as row 19's independent coverage result.

## Disposition and verification

What would change my decision: a committed policy/reference/decision amendment;
a defensible target set at the chosen setting; a concrete bounded qualification
with measured throughput, memory and interruption recovery; and a revised
manifest and enforceable aggregate budget. I would then review that narrower
launch specification. No further owner permission is invented by this record.

Read the request and `rsc_t1_simulation_design.md` end to end; read
pre-registration §§7–10, the completed 19 September probe record and analysis,
the row-17 record as the requested precedent, `analyze.py`, both cloud runner
files, the benchmark/probe scripts and the complete relevant generation,
serialization, queue and summary functions in `simulate.py`.
Review basis: RSC `1ab20cd465aff17ee3e22402244ca8571f39810d`.
No fit, simulation, cloud/account operation, source edit, protocol edit or push
was performed. The separate completed R2 reading remains closed.

Checks were deterministic saved-CSV arithmetic in SciPy 1.18.1: reproduced the
40-row counts and paired comparisons, the complete reference mean, matched the
1,000 final-shard points to the compact reference, swept coverage over every
endpoint/segment of the stated sensitivity ranges, summed per-row fit timings,
and evaluated binomial CDFs/beta quantiles and cost formulas. These calculations
do not validate a new interval or qualify a machine. The temporary calculator
is not a new scientific output. The core formulas are
`binom.cdf(k,100,.9)`, `beta.ppf(.975,k+1,100-k)`,
`mean(fit_seconds + 4*interval_fit_seconds)/3600`, and direct inclusive
endpoint comparisons to each external target.

Input SHA256 values (relative to `workspace_demo/t1_access/`):

| File | SHA256 |
|---|---|
| `sim_results/refit_probe_3ca9304/refit_probe_D4.csv` | `d3c38ac03ca5c8f9272e7e9d7af0bfbf2d9d43388521bfca04dfca1fd9b58cef` |
| `reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv` | `1622fad3cb50938f77a9627583fc93b59d4177242208633d5a9bf503840cf220` |
| `sim_results/d4v12b/calibration_D4.csv` | `7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb` |
| `sim_results/ref_m2s_omega2_aac9f69/calibration_D4.csv` (128 rows) | `e02ef698d2f86b6bd5d0b3fb56e7f0c46a24e7dee08b7bdd8225d2c88ad0e784` |
