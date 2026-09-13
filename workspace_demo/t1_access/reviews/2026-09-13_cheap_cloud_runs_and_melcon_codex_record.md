# Codex second opinion — cheap cloud runs and Melcón, 13 September 2026

Reply to `2026-09-13_cheap_cloud_runs_and_melcon_codex_brief.md`, reviewed at RSC `5afb014`.
**Current disposition (13 September, continuation at `df81308`):** the owner gave the
cloud go at 10:18 PDT; both specified development runs are launched. The runner recheck
passes. Melcón v2 remains a draft with the concrete freeze requirements recorded under
“Continuation review 2” below. Launch-approval requests in the first review are its
pre-launch history, not outstanding requests.

Read the complete brief, Melcón draft, README, inventory and loader; the cloud launcher,
job, simulation and analysis paths; the inherited human decoder, likelihood fitting and
BMS code; and the previous simulation review. Checked the landed simulation rows,
existing behavioural inventory, five BDF **headers only**, and an artificial filter input.
No model fits, EEG outcome analyses, cloud jobs or changes to running jobs were made.
The public AWS price catalogue was read without accessing the AWS account.

**Verdict: support the owner's change of order and two small development runs, with a
different allocation.** Pack the ten M2B control datasets into two jobs; concentrate the
additional reference bank on M2S omega 2. Start the Melcón method work now, independently
of T1, but **do not freeze or decode under the current draft**. It has several repairable
problems that could change the family comparison, including a verified anti-aliasing
gap. The proposed cloud dollar figures are planning estimates, not launch-ready quotes.
The owner's separate go remains required by the brief; this record launches nothing.

The two branches answer different questions. The old-fitter runs help interpret the
running bootstrap probe. Melcón asks whether a conditional distributional comparison
extends to a second human sample and a visual detection task. Neither branch validates
the amended model-side fitter or establishes a neural mechanism in an LLM.

## A1. Keep the control; reject ten mostly idle instances

**Yes:** M2B, ten new datasets, B=50, seed 2027, D=4, layer 41, four inner/eight outer
starts and the same point fitter as the probe. Read its paired cluster/refit intervals
against the independent d4v12b M2B mean, **−0.014800122**, with MCSE **0.000048391**.
Carry the reference uncertainty, even though it is small here. Do not use the control's
own ten-row mean as truth. The checked control, probe, old bank and proposed seed-2028
reference bank have no dataset-seed overlap or within-bank duplicates.

**The proposed allocation is inefficient, and its runtime is unsupported.** The code path is:

1. `t1_job.run_stage` parallelizes datasets through `simulate.run_points`.
2. `one_replicate` calls `analyze_dataset` without `n_jobs`, hence `n_jobs=1`.
3. `refit_bootstrap` consequently executes its 50 resamples serially.

With ten datasets and ten shards, each eight-vCPU instance receives only one dataset.
Setting the outer `N_JOBS` to eight does not parallelize those resamples. All ten datasets
can still run simultaneously with **two shards and five dataset workers per job**:

```text
--task calibration --generators M2B --n-rep 10 --seed 2027
--n-starts-inner 4 --interval refit --n-boot-refit 50 --layers 41
--shards 2 --n-jobs 5 --spot
```

These are the proposed job-shape arguments, not a launch command: use a new immutable
run namespace and set the instance and runtime limit after costing. The current
calibration-only path correctly avoids the gain artefact. Checkpoint paths are separated
by shard, and the numerical bootstrap identity does not depend on worker count.

At equal per-worker speed, two jobs of five datasets take the same elapsed time as ten
jobs of one, with one fifth of the instance-hours. Contention can change per-worker
speed; measure rather than promise equal timing. One job with eight workers is another
reasonable packing, but completes in two dataset waves and provides less parallel
checkpoint isolation. Do not introduce nested bootstrap parallelism just for this run.

The **13 hours is a Mac-core estimate**, not a measured AWS duration. The old cloud M2B
ordinary rows average 6,205 seconds each. Multiplying that by 51 gives about 88 hours
per dataset; this too is only a warning-scale extrapolation, because bootstrap samples
and concurrency differ. It is sufficient to reject the claim of an established 13-hour
AWS runtime and to question the launcher's **default 48-hour limit**.

The recorded $0.48/Mac-core-hour conversion came from a loaded 48xlarge. Applying it to
130.05 Mac-core-hours gives $62.42 at its original utilization assumptions. If the same
per-vCPU throughput and price efficiency held, the ten one-worker eight-vCPU jobs would
instead cost about **$499**, and the two five-worker jobs about **$100**. These are
utilization scenarios, **not new AWS quotes**; a lightly loaded core can run faster.

Price verification: the public Stockholm SageMaker catalogue published
2026-09-13T03:17:25Z lists **ml.c7i.2xlarge Training at $0.45864/hour** and
ml.c7i.48xlarge at $11.00736/hour. The queried catalogue returned no matching c8i.2xlarge
training SKU. That does not establish that the account cannot run it; it means the
launcher's c8i **$0.50/hour remains its stated estimate**. Establish the actual selected
instance rate, matching-job throughput, maximum runtime and retry allowance before go.
[AWS regional price catalogue](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonSageMaker/current/eu-north-1/index.json).

Managed Spot adds interruption and capacity-wait uncertainty; use the existing checkpoint
contract and report actual training and billable seconds afterward. Do not equate an EC2
spot quote with SageMaker's billed training rate.
[AWS Managed Spot documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/model-managed-spot-training.html).

## A2. Prefer the POINTS filter, principally for omega 2

**A separate reference bank at seed 2028 is the right design.** Preserve original hashes
and seed identities, report each bank separately and then pool compatible valid point
estimates by dataset count. Reference reuse requires the same numerical point procedure;
interval choice and provenance-only code changes can be documented explicitly rather
than pretending hashes are equal. An amended fitter requires a different reference.

The benefit of 1,000 extra rows at each point is asymmetric:

| Setting | Existing mean | Existing MCSE | Projected MCSE after 1,000 more |
|---|---:|---:|---:|
| M2S omega 1 | −0.869513 | 0.011242 | 0.007949 |
| M2S omega 2 | −5.334354 | 0.733956 | 0.518985 |

Projections assume the observed variance remains representative. At omega 2, the most
negative 1% of rows contribute **35.5% of the absolute sum**; dropping just the minimum
moves the mean from −5.334 to −4.921. The projected normal 95% half-width only falls from
1.439 to 1.017. Reaching MCSE 0.25 would require about **8,620 total rows** under that
variance estimate. None of these normal approximations certifies tail accuracy.

**My allocation:** the M2B control plus **1,000 new omega-2 reference rows**, with no
omega-0/0.5 expansion. Omega 1 is already adequately precise for a twenty-dataset screen;
an optional 250-row omega-1 bank would mainly check cross-bank agreement. Do not spend
$720 to avoid a small runner change. The brief's $440 two-point estimate, apportioned by
the old fit times, implies roughly **$235 for omega 2 alone**, or about $286 with the
optional 250 omega-1 rows. These inherit the brief's price/throughput assumptions.

For planning, aim for **about $335 combined, with a $400 envelope** for the packed
control and omega-2 reference. This is a proposed limit for the owner's decision, not
an assertion that the current launch specification enforces it. If a credible runtime,
instance-hour and retry budget does not fit, reduce/defer the reference allocation;
retain the budget needed for the amended procedure. No claim that the old fitter needs
an indefinitely precise reference to decide a large bootstrap improvement.

The POINTS change should be limited to runner/launcher code. Validate named points
against the declared calibration grid, reject typos and empty selections, record the
resolved points, preserve dataset IDs under filtering/sharding, and test resumption.
If the parser is moved into a helper, include that helper in `CODE_FILES`; importing
`probe_refit.py` without uploading it would break the cloud entry. Use distinct run
names and an explicit **development reference/control** purpose even though the runner
calls the stage `calibration`. No power/gain stage should be entered.

**Keep the mean as the reference target.** Median and trimmed means are valuable tail
descriptions, but they estimate different quantities. They cannot replace the procedure
expectation when judging coverage of an interval for that expectation. A robust estimate
of the *mean* is a separate possibility with its own assumptions and uncertainty; it
is not accomplished by substituting the median. Report probe coverage as a function of
the reference value, along with paired refit-minus-cluster coverage and interval widths.
Freeze the additional bank size or a budget-based stopping rule in advance; do not keep
adding rows until a preferred coverage verdict appears.

**Later gain contract:** retain a complete run hash including the dataset seed. Add an
explicit compatibility layer separating the gain artefact's generator/reference-method
identity and calibration/check seeds from the evaluated pipeline and its dataset seed
bank. The accepted artefact keeps its original digest and provenance; the new run names
that artefact through a checked reuse manifest. Do not strip SEED from all hashes or
relabel the artefact as newly computed. Changing only the pipeline fitter need not
invalidate unchanged alternative-generator calibration, but changing the reference
method or generator specification does. Keep power fail-closed under this contract.

## B. Melcón: worth doing now, with six substantive revisions

### 1. Decoder: all-present training is reasonable; both stages need held-out blocks

Catch versus all Gabor-present trials with training-fold balanced weights is a defensible
primary presence decoder. It uses five times as many positives as the top quintile
(360 versus 72), **not nine times**. The ratio 9:1 describes present versus catch counts.
The top-quintile variant has fewer examples and no strong perceptual anchor, but calling
it “under-powered by construction” claims a power result that has not been measured.
Keep it as a declared sensitivity, with decoder performance and uncertainty reported.

The more important change is **end-to-end block separation**. Ten-fold trial-wise
out-of-fold decoding followed by four-fold block-wise likelihood CV does not hold each
likelihood-test block out of decoder training. A training trial's projection can depend
on EEG/labels from that outer test block; even an outer test trial's decoder can see
other trials in its block. “Every trial was unseen by its own decoder” is insufficient.

Use four outer blocks for the complete pipeline. Within each outer training set, form
cross-fitted training projections using only those blocks; fit scaling, class weights,
any readout normalization and likelihood parameters there. Generate the held-out
block's projections with training-only decoders. Predeclare how inner-decoder projections
and test projections share a scale, and examine that choice on synthetic recovery cases:
pooling projections with differing offsets/scales can itself create apparent mixtures.
An independent fixed decoder-calibration split is simpler but spends scarce catch trials.
Do not hide that tradeoff by returning to overlapping folds.

Freeze CV splits and all random seeds. A pooled-across-tasks decoder is a separate
sensitivity, not an automatic “replication”: it shares training information between the
task estimates. Report AUC from held-out predictions; exclude EOG from classifier features.

### 2. Dose: five quantiles change the model, not just its input format

The current inventory supports retaining nocue and informative and withholding the
noninformative intensity analysis. My metadata check found at least 324 distinct positive
contrasts per retained-task recording and six distinct quintile edges in every recording.
Thus tied-bin collapse is **not an observed problem** here. The problem is geometry:
five equally spaced ranks replace unequally spaced physical log contrasts. Logging
before rank-based binning does not preserve that spacing. A logistic
in contrast is generally not a logistic in contrast rank. Binning also mixes a range of
doses within each conditional distribution and can manufacture extra spread or components.

**Prefer continuous log contrast as the main covariate; use five quantiles for plots and
the legacy sensitivity.** Center/scale using training data only. Catch is a distinct
stimulus-absence indicator: it has no finite log contrast and must not be encoded as
zero beside z-scored positive contrasts, many of which are negative. Write the catch
density explicitly for both models. If a finite physical-zero dose is essential, a
predeclared raw-contrast parameterization is another coherent model, not an unchanged
log-contrast port.

Two inherited implementation traps need explicit repair in the new port:

- `llh_logisticB` computes its upper anchor from `max(snrs)` in **each call**. With a
  continuous covariate, training and test maxima differ. The same parameters then define
  different predictions; in the arithmetic check, the mean at x=1 changes from −0.3673
  to −0.2237 merely by changing another row's maximum from 5 to 4. Use a fixed
  training-derived anchor, or an intercept-plus-logistic parameterization.
- The inherited mixture identifies catch using the minimum level of the current subset.
  Use the actual catch flag, including when a fold has few/no catch trials. Define an
  unavailable-fold policy instead of silently treating a present dose as catch.

The authors calibrated **separate hemifield thresholds**, with subsequent contrast based
on response history plus random variation. That prevents treating dose as a wholly
randomized intervention. The existing metadata show a median left/right median-contrast
ratio of 1.094 and a maximum of 1.562. Pooling hemifield, orientation, block drift or
staircase histories can create heterogeneity that the simple graded comparator misses.
Specify shared nuisance treatment for both candidate models and a block/hemifield
sensitivity; keep the question conditional and predictive. Avoid claiming that a fitted
occupancy sigmoid recovers a unique sensory threshold over an unobserved wide dose range.
[Melcón et al., methods §§2.2–2.3](https://onlinelibrary.wiley.com/doi/10.1111/psyp.14525).

### 3. Report design: correct the human reference before revising the paper

The brief and current conversation repeatedly call the reproduced Sergent comparison
“no-report.” **That is incorrect.** `sergent_port/RESULTS_sergent.md` C6 reproduces the
published three-model comparison in the **active, report-required** session. C7 is our
additional comparison on passive data; the paper did not publish that three-model result.
This was already settled in the earlier theory review and must not re-enter Methods
or Results through the new dataset description.

Melcón adds an independent human sample and a visual task. Both its tasks require
reports. Omitting report labels from decoder/model fitting makes the analysis
**report-unconditioned**, not the experiment report-free. The report prompt changes
the task, and expected reporting can affect activity before it appears. The randomized
left/right response mapping limits specific thumb preparation before the question;
it does not remove perceptual decisions, expected reporting or later display effects.

A positive result supports **mixture-model preference in a presence readout under this
report-required visual task**. It establishes neither report-independent ignition nor
consciousness, bistable dynamics or a global broadcast. A two-component density need
not even have two modes. Report fitted conditional densities and component separation;
keep a graded-support or null outcome equally bounded. A direct report-effect claim
would need a suitable report manipulation and a direct contrast, not one positive and
one nonsignificant result from unlike datasets.

### 4. Preprocessing and exclusions: fix the actual loader, not only the wording

**Verified blocker: anti-aliasing at 2048 Hz.** Reading only the BDF headers shows:

| Recordings checked | Header low-pass | Raw sample rate |
|---|---:|---:|
| sub-01 nocue, ordinary reference | 208 Hz | 1024 Hz |
| sub-35 informative/noninformative; sub-36 informative/nocue | **417 Hz** | **2048 Hz** |

`load.py` applies no digital anti-alias low-pass, then uses `Epochs(decim=4)` on the
2048-Hz files. The output Nyquist frequency is 256 Hz; the 417-Hz acquisition corner
does not justify that operation. Its explanatory comment assumes a 208-Hz corner and
suppresses RuntimeWarnings. This establishes a missing protection, not that a particular
amount of aliasing has already been observed in EEG.

Specify an appropriate anti-alias filter for **all** recordings before decimation, or
a resampling method that supplies one. Preserve the native-sample photodiode timing;
document transition bandwidth, phase and edge handling. MNE distinguishes decimation
from filtered resampling and recommends filtering continuous data before epoch
decimation. Re-run loader verification after the repair and remove blanket warning
suppression.
[MNE filtering/resampling documentation](https://mne.tools/stable/auto_tutorials/preprocessing/30_filtering_resampling.html).

The fixed 150/100-µV rejection proposal can be developed without manual outcome-driven
choices, but is not yet a complete preprocessing specification:

- Keep the EOG channels for rejection: `load_subject` currently defaults to
  `keep_eog=False`. Define bipolar vertical and horizontal EOG traces and their
  filtering/reference, rather than “either vertical channel” without specifying the
  electrical reference. The current filters pick EEG only.
- Define flat/disconnected channels, the interpolation montage/method, a maximum bad
  channel count, and termination of the detect/interpolate/reapply sequence. Mark bad
  channels before their signal contaminates the common average; use fixed coordinates
  or an established montage, not an unspecified neighbour search.
- A −200 to +600 ms artefact screen includes the question period. Later ocular
  behaviour can therefore select trials used in the early analysis. Specify this
  selection explicitly, and report retention by contrast, side, block, task and report.
  The claim that later activity is constant across dose is not supported merely because
  the same question is asked.
- Restrict the non-positive-contrast exclusion to **present** trials. For missing
  reports, my preference is to retain otherwise valid trials in the report-unconditioned
  neural comparison and omit them only from report-conditioned summaries; otherwise
  justify an engagement-conditioned estimand and report a sensitivity. Missing reports
  occur after the signal being tested.
- Retaining at least 250 present/25 catch trials is a transparent provisional rule,
  not an established power guarantee. Require adequate classes in every training/test
  split too. Report all exclusion counts; do not relax thresholds after looking at
  model preferences to recover twenty participants.

“No ICA” is a defensible fixed choice, but not because ICA inherently requires manual
per-person decisions. It trades simpler processing for more residual ocular signal and
trial loss. The port currently has **no implemented artefact rejection**, so §3 must not
describe the full proposal as implemented. Freeze the implemented pipeline after
blind QC and synthetic checks, before decoding or looking at neural contrasts.

### 5. Windows and inference: the current early-window rule does not replicate the late result

**0–300 ms is a legitimate early-response question, but a poor sole primary test of the
late Sergent signature.** Its published and reproduced first pxp>0.95 window is centred
at **315 ms**, with a stable plateau at 435–495 ms (`RESULTS_sergent.md` C6/C8). The
visual task may differ in timing; this does not justify excluding the known reference
interval and interpreting an early null as a failure to generalize it.

My preference for the stated replication purpose is a predeclared **300–600 ms main
interval**, explicitly testing report-associated visual processing, with **0–300 ms as
a separate early analysis**. This contains the reference's stable late interval while
acknowledging the question-display confound. If the owner instead wants 0–300 ms primary,
name it an early visual extension and bound a negative result to that interval. There
is no timing choice in these data that independently removes the reporting task.

Two more fixes are necessary whichever interval is chosen:

**Filtering crosses the proposed boundary.** The inherited projected-activity filter is
a 12th-order 10-Hz Butterworth applied forward/backward. The read-only artificial-step
check at 512 Hz puts a step at 300.78 ms: after filtering, its mean in 270–300 ms is
**0.232 of the step height**, and there is ringing farther back. This is an illustration,
not an estimate of contamination in this dataset. The loader also uses noncausal
high-pass/notch filtering. Therefore a nominally pre-300-ms output is not guaranteed to
use only pre-question input. Specify the full temporal transfer/edge handling, show
impulse or step checks, and use a causal-processing sensitivity if making a claim about
activity preceding the question. Simply removing the 10-Hz smoother is insufficient.
[MNE filter design and temporal effects](https://mne.tools/stable/auto_tutorials/preprocessing/25_background_filtering.html).

**Sixteen samples at 512 Hz is 31.25 ms.** Ten nonoverlapping such windows occupy
312.5 ms. Use explicit half-open 30-ms time edges and 15/16 samples as needed, or declare
31.25-ms bins and select them by their complete support. The inherited Sergent code has
16-sample windows stepping by 15 samples at 500 Hz, sharing endpoints; “everything else
unchanged” is inaccurate here too. Adjacent smoothed windows are strongly dependent;
three in a row is a persistence convention, not three independent confirmations.

**Do not call 1−pxp a calibrated p-value.** SPM expects log model evidences and outputs
posterior model-frequency/exceedance summaries. The inherited code supplies mean-fold
held-out summed log scores, a predictive-evidence convention. Its “Simes” routine is a
BH-style step-up calculation on 1−pxp; neither that transformation nor three consecutive
windows establishes frequentist error control. Freeze either an explicitly descriptive
inherited convention, or a rule calibrated by model-recovery simulations at the actual
design. Do not report corrected significance as already established.
[SPM's own BMS implementation](https://raw.githubusercontent.com/spm/spm12/main/spm_BMS.m).

Report the direct **held-out log-score difference per trial** between the two families,
its participant-level variation and uncertainty, alongside three-way and two-way BMS.
Mean fold-summed evidence changes scale with retained trial count and fold count; equal
pxp thresholds in Sergent and Melcón do not represent matched evidence or power. The
existing Sergent three-versus-two-model sensitivity already demonstrates model-set
dependence. A shared four-outcome vocabulary likewise does not make human BMS and the
model-side interval/point test the same inferential procedure.

Do not carry over capped single-start Nelder–Mead as an unquestioned primary fitter.
The existing human diagnostics show substantial nonconvergence and boundary sensitivity.
Specify a finite training-only multistart recipe, numerical bounds/floors, convergence
and unavailable-fit policy; use the literal old recipe as a reproduction sensitivity.
Before outcome analysis, run small synthetic recovery checks using this dataset's dose,
block and side structure: graded heterogeneity/skew, overlapping and separated mixtures,
weak decoder signal and temporal dependence. The T1 synthetic calibration does not
validate this different human pipeline. Catch false alarms also motivate a declared
free-catch-occupancy sensitivity; physical absence does not by itself establish absence
of every possible internal high state.

Finally make the outcome table exclusive. Both families can meet their criteria in
different time intervals; put that pattern in **inconclusive/mixed**, with the time
courses shown, or predeclare a single aggregate comparison. The AUC≤0.55 rule has not
been calibrated as an assay-sensitivity gate. Weak presence decoding can make the
comparison uninformative without being an implementation failure, and good presence
decoding need not resolve two latent states. Report technical failures and insufficient
measurement sensitivity separately; do not silently select only high-AUC participants.

### 6. Replication label, work location and paper wording

Call this a **preregistered secondary cross-modal extension of the distributional assay**,
or a conceptual replication with the changed estimand/readout stated. It is not an exact
replication of the timing, dose manipulation or decoder calibration. The informative
task is a within-participant cue-context robustness analysis: **34 participants occur
in both its 35-recording sample and the nocue sample**, not two independent cohorts.
Do not treat task recordings as independent people or call cue invariance a report test.

I support starting this work now. Rewrite the obsolete freeze condition to say that
metadata/behaviour and loader QC have already been inspected, then freeze the implemented
secondary protocol before any EEG decoding, neural condition contrasts or model results
are examined. T1 simulations contain no neural observations. Register later changes
openly, and do not use either dataset's desired result to select the other's method.

**Where:** do the protocol, loader repairs and synthetic method checks locally now.
For the full EEG processing, prefer the **PC after its current audit** if a verified
copy and matching CPU environment can be prepared; moving the control to AWS frees that
slot. Retain the Mac raw-data master under the owner's existing storage preference.
Start with one recording worker, measure peak RAM and runtime, then choose concurrency.
If copying/setup would outlast the Mac probe, run on the Mac after the probe instead.
There is no measured basis yet for promising “days”; loading, nested decoding, fitting
and sensitivity runs should each be timed. No GPU or AWS EEG run is needed for the
proposed logistic/scalar-likelihood pipeline. Do not compete with the eleven-worker
Mac probe or disturb the ongoing PC audit.

Suggested manuscript status text, **until an actual secondary result exists**:

> The human reference analysis reproduces the published distributional model comparison
> in the active session of the Sergent auditory dataset. A separate analysis of its
> passive session examines the same candidate models. A secondary visual analysis is
> planned using Melcón et al.'s report-required detection dataset, with its protocol
> finalized before neural outcome analysis. It tests the assay's generalization across
> modality and task; it does not isolate the effect of reporting.

Use “preregistered” only after the freeze is recorded. Results §6.1 should not announce
a completed second human analysis, two replications, or a report-independent bridge
before the corresponding evidence exists. When it lands, give each dataset/task its
own outcome and qualification; the model-side empirical result is distinct from its
simulation validation. The physical-organization framing added earlier remains compatible
with any of these outcomes and does not depend on obtaining a mixture preference.

## Reproducibility and disposition

The accompanying `2026-09-13_cheap_cloud_runs_and_melcon_codex_checks.py` and JSON reproduce
the reference/tail arithmetic, seed checks, shard counts, illustrative cost arithmetic,
behavioural counts, BDF-header findings, filter example, window geometry and graded-anchor
example. Calibration source SHA-256 is
`7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb`; it was unchanged
while read. The check imports no project fitting code and reads no EEG samples.
The filtered public price-catalogue extract is retained in
`2026-09-13_cheap_cloud_runs_and_melcon_aws_prices.json`; its timestamp and URL identify
the source used for the quoted c7i rates, not a c8i or managed-spot quote.

**Next handoff:** Claude can prepare the packed control and filtered reference job
specifications with a real cost/runtime ceiling, and revise the Melcón draft around
these findings. The recommendation is to proceed with that preparation now; the existing
owner launch/freeze decision follows a concrete specification. No request here to
restart the probe, stop the audit, run new neural analyses, or fund the earlier cloud ladder.

## Continuation review 2 — launched runner and Melcón draft v2

13 September 2026, RSC `df81308` (runner `aac9f69`, Melcón `ab2c860`), Unimog
`b6804cea` plus the wrap acceptance commit `378ed4f0`. Read R052 including its wrap
entry, the current brief and this record, the revised code and full secondary draft,
and Claude Entropy SI's turns from 09:36 through the 10:50 monitor report, by session
ID `a5e468e7`. Its 10:18:33 PDT owner go and the subsequent launches are settled.
No additional launch, change to a running job, EEG outcome analysis or freeze is
authorized by this continuation. RSC has no `CLAUDE.md` or per-repo memory index at
the requested locations; the shared rules and relevant Unimog memory were used.

**Verdict:** on board with the implemented allocation and point filter for the two
already authorized development runs. Continue their existing monitoring. Melcón v2
incorporates the main conceptual revisions, but is **not ready to freeze**: its
likelihood, decoder-scale and outcome contracts still need the following concrete
completion. This recheck does not reopen the numerical T1 repairs closed by review 8.

### Cloud readback and exercised dispatch

Read-only AWS evidence, **17:51:39 UTC / 10:51:39 PDT**, is saved in
`2026-09-13_cheap_cloud_live_readback.json`; the same-named Python script reproduces
the readback with `--out <file>` using the existing `xtenure-read` profile. It only
lists/describes these runs, reads their logs and S3 objects, and writes its local
report. It has no launch, stop, upload or retry operation.

| Run | Actual job settings and log | Observed state |
|---|---|---|
| `refit_control_aac9f69` | Two on-demand `ml.c8i.2xlarge`; five dataset workers each; M2B, ten datasets total, seed 2027, D4, layer 41, four inner starts, `refit`, B50; 110 h maximum runtime | Both Training; logs say five datasets per shard; numerical hash `fab869c34eb6` |
| `ref_m2s_omega2_aac9f69` | Ten Spot `ml.c8i.2xlarge`; eight workers each; 100 datasets per shard; POINTS resolves only M2S omega 2; seed 2028, D4, layer 41, four inner starts, `cluster`; 60 h runtime / 120 h wait limits | All ten Training; numerical hash `3575ae74b0fb` |

The five uploaded files in **each** namespace match the working files byte for byte,
including `points_filter.py`. Runtime logs show JAX 0.11.1, NumPy 2.4.6, SciPy 1.18.0,
pandas 3.0.5 and joblib 1.5.3. No result objects or refit checkpoints had landed at
this early check. The service reports about 31–32 minutes of training per job;
`BillableTimeInSeconds` is absent. The launcher's printed `0.00 h billed` is its
missing-value fallback, **not evidence of zero spend**. Read actual billable time when
available; the Managed Spot saving uses its ratio to training time.
[AWS Managed Spot accounting](https://docs.aws.amazon.com/sagemaker/latest/dg/model-managed-spot-training.html),
[DescribeTrainingJob fields](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeTrainingJob.html).

`test_points_filter.py` passes. New
`2026-09-13_cheap_cloud_v2_runner_checks.py` exercises the real launcher dry-run,
`t1_job.run_stage` and `simulate.run_points`, substituting deterministic rows for fits
and in-memory stubs for S3. It verifies 2×5 control rows and 10×100 omega-2 rows,
exact dataset seeds, no duplicate work after a chunk interruption or complete-shard
resume, the resolved point in progress records, both runtime configurations, and no
gain-file call. Results are in its JSON companion. It measures dispatch correctness,
not numerical performance; no simulation fit is executed.

At the launcher's **estimated** USD 0.50 per instance-hour, the existing runtime caps
imply USD 110 + 300 = **410** for these jobs, before ancillary charges or separately
launched retries. That is the two-run specification the owner approved, not a hard
USD 400 cap. Their central estimates sum to **260**, not 300 (the latter includes
the optional omega-1 bank, which is held). Neither estimate is a verified c8i price.
No new allocation or retry allowance is added here; the USD 3,000 further-spend cap
continues to apply.

The **88 h** number remains an extrapolation from ordinary-row timings at a different
packing. There is still no measured AWS refitting time at this readback. A completed
resample's `fit_seconds` in the existing checkpoint files will supply the first
matching timing; examine several workers/resamples and later completed dataset wall
times before projecting completion and cost. The current serial bootstrap saves
each completed resample, and SageMaker syncs its checkpoint directory: an interruption
does not inherently discard all fifty refits. On-demand is the chosen allocation;
there is no new empirical finding here that Spot is unsuitable.

### M1. Specify actual densities and an identifiable catch sensitivity before freeze

Draft §6 still names `mu_high(x)` without giving its function, says the graded mean
is both intercept-plus-logistic and fixed-anchor, and gives no explicit graded catch
density. The sign/positivity constraints for SD linear in the mean, the numerical
parameter bounds, moment starts/jitter and optimization tolerances are not listed.
“Declared parameter bounds” cannot stand in for those values. §5 promises staircase
history nuisance treatment without defining its covariates; block as a sensitivity
also needs a prediction rule for a held-out, previously unseen block. Freeze formulas,
parameters and executable configuration together, with the same nuisance structure
for each compared density and no test-derived anchor.

One specific defect is algebraic: the catch sensitivity frees the mixture proportion
but retains `mu_high = mu_low` and the common sigma. Then

`(1 - pi_catch) N(mu_low, sigma) + pi_catch N(mu_low, sigma) = N(mu_low, sigma)`.

Its catch likelihood is identical for every `pi_catch`. The synthetic contract check
demonstrates it for 0, 0.2, 0.8 and 1. Define a distinguishable high-component catch
distribution for that sensitivity, including how its parameters are constrained by
training data, or remove the free-occupancy claim. A free parameter alone cannot test
catch false alarms under the equal-component definition. This is a specification
problem; no completed Melcón fit is alleged to be wrong.

### M2. The proposed pooled z score does not settle decoder-scale compatibility

The revised outer/inner block separation is accepted as the **intended** split. A
common affine transform of the pooled inner predictions does not align the three
two-block decoder score distributions with one another or with the outer three-block
decoder. For an illustrative case, three unit-SD normal score distributions with
decoder offsets −2, 0, +2 retain means −1.044, 0, +1.044 and SD 0.522 after that pooled
z score. The test decoder can meanwhile have one centred normal score distribution.
This is a counterexample to the proposed normalization being an alignment guarantee,
not evidence that the EEG has that artifact.

Specify whether normalization is per sample or window, and its order relative to the
10-Hz smoother. Demonstrate compatibility with the **actual nested decoder** on
synthetic signal, drift and weak-signal cases at two- versus three-block training sizes.
The implementation should also pass an isolation check: changing only outer-test
EEG/labels cannot change its trained decoder, normalization or likelihood parameters.
If a common scale fails those checks, adopt and declare a calibration design that
uses matching readouts for likelihood training and test scoring; do not assert that
pooling alone repaired it.

For the pooled-across-tasks sensitivity, specify held-out blocks across both tasks
and training-only top-quintile thresholds. A list of sensitivity names is not yet an
implementable CV protocol.

### M3. Make the outcome rule a total decision function, then test it

§7 says each family meets its rule with three consecutive windows, but the two-state
outcome also requires that the graded model does not meet the rule “in any window.”
Consider three mixture windows above 0.95 and one isolated graded window above 0.95.
If that isolated window blocks the mixture outcome, the text gives no mixed outcome
because the graded family has no three-window run. If only a full opposing run
blocks it, say so. Define one Boolean per family's complete persistence rule, then
classify the four Boolean combinations explicitly. Also state whether a null-model
run elsewhere overrides a family run; the current “or a null-model win” can overlap.

Define precedence for technical failure versus insufficient sensitivity, the exact
recording/window denominator after exclusions, and a minimum eligible sample for each
three-window run. “Median ... in every window” needs a specified axis and aggregation
over folds. Missing fits can otherwise make neighboring windows compare different
participant sets. Apply availability rules to the early analysis too.

For the participant bootstrap specify the estimator (mean of participant per-trial
scores versus a trial-weighted pooled mean), B, seed and interval construction; carry
each sampled participant's full time course and paired tasks together. A confidence
interval for an unspecified average cannot be reproduced.

The descriptive BMS interpretation is correctly bounded now. The promised synthetic
recovery checks still lack generator parameters, replicate counts, seeds and pass/
revise criteria. Set a bounded **development** battery before running it, retain the
results and revisions, and do not call a few successful synthetic cases calibrated
family-error control. The artificial checks accompanying this review do not replace
that full-pipeline recovery work.

### M4. Keep the filter repair; correct its verification and finish the data contract

The actual loader applies the default 200-Hz FIR to EEG **and** EOG before decimation,
keeps native-rate onset snapping, and removes the blanket warning suppression around
epoch creation. The filter has a 50-Hz transition band under the installed MNE; the
synthetic check finds about **53 dB attenuation at 256 Hz** and **59 dB at 300 Hz** for
both native sample rates. This supports the default repair.

However, the real `load_subject` path on artificial 1024- and 2048-Hz RawArrays emits
the decimation RuntimeWarning at **both** rates in MNE 1.13.0. MNE's guard warns when
the output rate is less than three times `info['lowpass']`: 512 < 600. Its own
documentation explains that this is a conservative cutoff-only heuristic and a
steeper transition can make it over-sensitive. Thus neither “no aliasing warning”
nor the code comment “an aliasing RuntimeWarning ... would be a real defect” describes
this implementation correctly. Retain the visible warning and document the response
check; do not suppress it or change a working filter just to silence the message.
[MNE resampling guidance and warning limitations](https://mne.tools/stable/auto_tutorials/preprocessing/30_filtering_resampling.html#best-practices).

The general `lowpass <= target Nyquist` guard does not check the stopband/transition;
freeze the actual default filter settings and test any exposed alternative. Likewise,
“v1 ... aliased the 256–417 Hz band” overstates the original finding: missing protection
was established, but the amount of aliasing in real EEG was not measured.

The returned channels are **128 EEG plus four individual EOG**, not two already bipolar
traces. `params['ch_types']` identifies them in memory, but `--cache` does not preserve
that type list or filter configuration. The new decoder/cache contract must explicitly
select 128 scalp features, construct VEOG1−VEOG2 and HEOG1−HEOG2 for rejection, and
authenticate preprocessing so that a pre-repair cache cannot silently return. The
existing verification CSV mixes two revised 132-channel rows with the earlier
128-channel rows; it is not an all-recording verification of the revised loader.
That pre-existing working-file change is preserved for Claude.

The fixed bad-channel rule is a useful specification, not implemented preprocessing.
Freeze the detect/interpolate/reference order, original sensor-to-montage mapping,
the denominator for the 20% rule and the final exclusion after the bounded iteration.
State whether recording-wide QC is intentionally allowed to see outer-test data;
otherwise learn adaptive channel decisions inside training splits. Continuous
noncausal filters likewise need a declared block-boundary policy for a strict
end-to-end holdout claim. Synthetic flat/bad-channel, EOG-only and block-boundary
checks can establish the intended behavior without opening neural outcomes.

### Small current-state corrections and handoff

- The brief's disposition still says the parser is in `t1_job.py` and `CODE_FILES` is
  unchanged. The actual, correctly uploaded implementation is `points_filter.py`.
- The Melcón README still makes the first T1 result a prerequisite for method work;
  the 13 September owner instruction changes that order. It also describes a
  128-channel output despite the default now retaining four EOG channels. Preserve
  the distinction between completed historical loader QC and the pending new pipeline.
- The draft opening already calls the extension “pre-registered,” while its own §10
  reserves that label until freeze. Use “planned secondary cross-modal extension”
  until the freeze is recorded. The final deviation paragraph cannot say likelihood
  forms are unchanged after declaring new parameterization and catch behavior.
- Keep the corrected active/report-required Sergent reference and the additional
  passive analysis, the 300–600 ms main / 0–300 ms early split, continuous log dose,
  report-unconditioned wording, and within-participant informative-task interpretation.

Evidence: `2026-09-13_melcon_v2_contract_checks.py` and its JSON contain the real-loader
synthetic filter/warning check and the catch, pooled-scale and outcome counterexamples.
They read no EEG and fit no decoder or density. The runner fixtures likewise substitute
rows for fits. Production source and Claude's draft remain unchanged by this review.
Next: Claude can complete the executable protocol and its declared synthetic battery,
then return that concrete version for the owner/freeze decision already in the plan.
R052 retains Entropy SI as holder; no request to relaunch either cloud run or disturb
the Mac probe or PC audit.
