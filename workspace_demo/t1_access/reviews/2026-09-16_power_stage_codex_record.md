# Power-stage second opinion — Codex final record

Status: FINAL, 16 September 2026. Delivery/receipt are recorded separately in R052.
Request: `2026-09-16_power_stage_codex_brief.md`, RSC `26f34d8`, six questions.
Reviewed baseline: RSC `da6070d`; Unimog `22213342`. The companion
`2026-09-16_power_stage_mc.json` pins every reviewed source and records the
binomial calculations. Earlier source reading and gate checks were preserved
across the wrap, not restarted.
No fitting, response simulation, job interruption, launch, protocol edit or push.

**Recommendation:** add a bounded, explicitly labelled sensitivity study of the
historical fixed-score procedure: all four declared mixture alternatives at the
nominal 0.01-nat gain, 50 independent datasets each, if the owner's benchmarked
budget permits. It answers a real gap without waiting for a replacement interval.
It is not full §10 validation, does not restore interval coverage, and cannot
license a model-data hypothesis verdict. The narrower completed audit remains
reportable if the run is poor, incomplete or not undertaken. Do not present the
existing zero-false-call result as a calibrated discriminator.

This is scientific advice, not approval to launch, interrupt a probe, amend a
rule or undertake the separate AI pilot. Claude retains dispatch and disposition.

## Verified implementation and provenance

Read `simulate.py` (all 1,025 lines), `analyze.py` (all 668 lines),
`probe_refit.py` (all 73 lines), the entire request, and preregistration
sections 5, 7–10, budget and freeze-manifest text. Completed the simulation-design
document through its current ledger, strategy lines 1–100, and current manuscript
introduction, transfer, methods, results and discussion/conclusion in full.
Read the current owner/Claude exchange through 12:58 PDT in native Entropy SI
`9c0d76b5-e296-4739-bb14-ed95dfe64a09`. The owner has frozen text through §2.5;
the separate AI-side pilot is not an expansion of this review.

Source snapshot: RSC HEAD `26f34d8`; SHA256:

- `simulate.py`: `0832d490f6b2f10749f53f6f5ea69c2079acb240fbf0dce7f1dba7b2f89ab3fb`
- `analyze.py`: `c49c8f744c1dae0cca59fdebe0c6f7134027d6555bb11eb69dcb1ed8c455d219`
- `probe_refit.py`: `84db00f684cf7382bbc19a1d245b026f5e1055c85c7dada190f400b46654281c`

The brief's Q6 chronology is incorrect. `gain_gate` was introduced/enforced in
RSC `4677e41` (11 September 2026, 17:49 PDT). The named local artifact was
committed in `3ca9304` (13 September 2026, 08:04 PDT), produced under `9b277df`,
code/config hash `d77c3ecc161e`. The legacy ungated cloud file is a different
artifact. Preregistration §10 explicitly assigns the recomputed-check route to
the earlier d4v12b job output.

Named local file: `sim_results/gain_local_9b277df/gain_calibration_D4.json`;
3,477,642 bytes; SHA256
`38a67e1c8caa76c4bdefbc0e22a59b62678ef3d8e902e53b0b88ee6d3e0a8697`.
Metadata: D=4, seed 2026, calibration 32 concepts per family, independent check
64 per family at seed 3026; check relative-SE gate .20 and relative agreement .25.
The actual pure reader/gate functions extracted from current `simulate.py`
accept all twelve pairs with no problems. All entries carry calibration and
check convergence/reproduction flags; none has a failure note. No numerical
revalidation was executed. The companion script records exactly what ran:
AST-extracted functions with a scalar finite-check substitute, without importing
the numerical pipeline. This establishes the stored-entry gate result, not a
new independent reproduction of the numerical calibration.

`power_points(file)` returns twelve alternatives. `power_points(file,
targets=[.01])` returns exactly M3, M3H(tau=.5), M3V, M3L(pi0=.05), with scales
0.7048470316951376, 0.5359075609613234, 0.6267476817856267,
0.7187787541376713. `accepted_gain_artefact` accepts this raw D4 file under its
own stored hash. Run compatibility with a future numerical configuration still
requires an explicit provenance/reuse decision; no future dispatch is approved.

Implementation facts relevant to Q2–Q4:

- `expected_gain` measures the generating-density versus a best-found graded
  reference fitted at 256 concepts; the independent check uses 512. It is not
  the finite-design selected-X minus selected-G procedure's expectation. The
  preregistration says this explicitly. A nominal positive gain need not yield
  positive finite-design mean scores or high detection probability.
- `decide` is positive lower endpoint -> mixture, negative upper endpoint ->
  graded, otherwise inconclusive; unavailable intervals are separate failures.
  A simulation can measure this rule's actual operating characteristics without
  certifying the interval's nominal coverage. This distinction needs a complete
  final discussion, including the null boundary and finite generator scope.
- The local CLI defaults to five layers (25,33,41,49,57), eight inner starts,
  all twelve gain points and chunks of 32. d4v12b used one layer 41 and four
  inner starts. There is no target-only CLI argument: target selection exists
  in the Python API. The proposed 200-dataset run is not the default CLI task.
- The local CLI calls `power_points` without the stronger top-level
  `accepted_gain_artefact` D/hash checks. It also creates no refit checkpoint
  directory, unlike `probe_refit.py`. Any future runner must make these
  configuration/provenance choices concrete before a benchmark/launch.
- `fit_seconds` is the sum of elapsed fitter times, not a hardware-independent
  core-cost benchmark. The preregistration contrasts a historical 900 s Mac
  layer with roughly 83 min on a loaded cloud vCPU. The brief's 6,188-second
  cloud average cannot establish a 31-hour Mac schedule, especially on new
  mixture generators. Actual first-replicate benchmarking remains required.
- All three predictors are saved from the same fits: primary selection,
  ensemble and inherited pair. Their mixture-generator operating characteristics
  can be compared without another density-fitting run.
- With refit intervals, the companion cluster interval is retained on the same
  datasets. Refitting is substantial additional work: B full sequential
  pipelines per dataset with this runner, not a second cheap interval formula.
- The probe checkpoints completed resamples, while `run_points` writes complete
  datasets only after a worker chunk returns. Restart reruns the original
  dataset fit before loading bootstrap checkpoints; unfinished work may be
  lost. The claim that a kill/restart resumes without any loss is too strong.
  Suspension is a distinct operation. No pause/stop was performed.

## Q1 — What the zero-false-call result earns

The diagnosis of missing sensitivity is correct. The conclusion that the entire
audit is worthless, or necessarily unpublishable, without it is too strong.
The completed experiment measures the historical procedure's false two-state
frequency under twelve specific graded generators. Its contrast with the
inherited predictor pair is useful even if the expanded procedure proves weak
at detecting mixtures. That would expose a specificity–sensitivity tradeoff,
not erase the false calls of the inherited pair.

What is not earned is “the predictors are calibrated,” “the assay discriminates
the families,” or a guarantee that it returns an indicator only when the system
has the property. The measured object is the whole specified analysis, with its
fitting, family selection and interval-sign decision. Its components have not
been independently validated. A simulation's known generator label also differs
from the sign of this fitted procedure's expected score difference: the latter
can be positive between two misspecified predictors on a graded generator.

**Current-paper consequence.** The explicit limitation in transfer §2.4–2.5 is
helpful, but the Introduction's closing “predictors calibrated” and its
“calibrates the assay on human data” still overstate the evidence. Human
reproduction anchors an implementation; it supplies no known two-state ground
truth or human error-rate calibration. The Conclusion's “which components are
now calibrated” needs the same qualification. The owner's freeze through §2.5
is respected: flag the frozen claims for owner disposition, do not edit them.
Outside the freeze, state a partial operating-characteristic audit, with
sensitivity unmeasured or reported at the few new settings actually run.

The new sampling-unit discussion is subject to the same boundary. Independent
random effects can be identically distributed, hence exchangeable, despite
heterogeneity. A ratio between replicate spread and fixed-score bootstrap SE
does not independently validate or invalidate the concept as sampling unit;
shared training fits, selection and tails still intervene. The saved-row
comparison does not isolate a cost of each of five components. This is a
claim-scope observation, not a reopening of the numerical row audit.

My recommendation changes the proposed *addition*, not the status of the two
completed analyses: given the owner's explicit wish to close this gap, the
bounded matched sensitivity study is worthwhile. The manuscript can still
stand as a narrower audit if it cannot be completed. Publish its outcome
regardless of direction; do not make publication conditional on high power.

## Q2 — Power under the historical interval remains meaningful

For a fixed generator and the complete frozen historical algorithm, define

    p_g = Pr(the algorithm returns mixture support | generator g).

Generating independent datasets and counting that event estimates p_g directly.
It does not require accepting the algorithm's internal interval as a valid
95% confidence interval. The Monte Carlo interval around the counted frequency
is a different interval, obtained across independent datasets.

A too-narrow interval can increase detection when scores are positive, so a
high rate alone is not evidence of a valid test. But failure to include a
negative expectation is not the event of crossing zero: all historical primary
intervals were negative at the tested graded settings. A badly calibrated
interval around a strongly negative score can still make few false positive
calls there. The 0.216 is inclusion of an estimated, tail-sensitive reference,
not a demonstrated universal interval-width factor. It does not establish
inflated size at the zero boundary or quantify inflation under these mixtures.

Therefore report **detection probabilities of the historical fixed-score rule**
(power against the declared generative alternatives), beside the existing
per-setting graded false-call frequencies, failures and interval limitation.
Do not call this size-controlled power for all expected-score nulls. The grid
does not establish performance at every near-boundary or unmodelled graded law.

Run cluster only to answer that historical question. Running refit instead would
answer a different question; running both is not a prerequisite. If a separately
budgeted refit study is later chosen, use the same datasets and paired decisions;
the code retains the cluster companion from those fits. Each refit interval costs
B further full pipelines, and B=50 only weakly resolves percentile tails. This
is not a cheap second uncertainty calculation. A refit success on alternatives
would not validate its null coverage either.

The existing §8.2/§10 replacement requirement and independent validation gates
before CONF remain. This historical sensitivity screen must be a separate
ledger scope; it cannot be called completion of row 9, which follows validated
inference, or used to reinstate the cluster interval as the future primary.

This distinction follows the separation of estimation, testing and model
selection performance in Morris, White & Crowther (2019), §§3.3 and 5.2; they
also caution against reading power without type-I-error control. Their advice
supports interpreting several measures together, not discarding measurements
of a flawed method. [Primary paper](https://discovery.ucl.ac.uk/10066118/1/2019%20-%20Morris%20-%20simulation%20studies%20tutorial%20-%20stat%20med.pdf).
Generic CV interval failures are also established by Bates, Hastie & Tibshirani;
their results are context, not a proof of the particular cause or repair here.
[Primary paper](https://tibshirani.su.domains/ftp/NCV.pdf).

## Q3 — Four alternatives at 0.01, R=50: a useful screen, not a certified gate

Prefer the four alternatives at the already declared 0.01-nat target, 50 each,
over splitting the same 200 datasets into 25 at each of two gains. This estimates
one clearly specified operating point for each alternative. It supports a
sentence about sensitivity **at those four settings**, not a power curve,
monotonicity, the human 0.003-nat plateau, or sensitivity throughout a family.

The gain is a generator-versus-large-sample-graded-reference quantity. It is
not theta_g, the finite-design mean of selected X minus selected G, and is not
an observed human effect mapped onto an identical measurement. Low power at
this nominal gain could reflect finite-sample fitting/selection as well as
interval behaviour. Report the achieved calibration/check gains and the
finite-design score distribution; do not silently re-tune scales on power data.

Calculated uncertainty (hypothetical counts, not simulation results):

| Calls / attempted datasets | Estimate | MCSE | Exact two-sided 95% interval |
|---|---:|---:|---:|
| 20/25 | 0.80 | 0.0800 | [0.5930, 0.9317] |
| 40/50 | 0.80 | 0.0566 | [0.6628, 0.8997] |
| 0/50 | 0.00 | plug-in 0 | [0, 0.0711] |
| 50/50 | 1.00 | plug-in 0 | [0.9289, 1] |

Thus 40/50 is not evidence that true power is at least 0.8. For orientation,
an individual one-sided exact 95% lower bound first exceeds 0.8 at 45/50;
four Bonferroni simultaneous one-sided bounds require 47/50 each. These are
precision illustrations, **not new pass rules or an amendment**. Marginal
intervals and a claim about all four should be labelled according to the
inference actually used. Rough normal planning for a 95% half-width of 0.05
near p=0.8 needs 246 datasets per setting, not 50; this is not a recommendation
to spend that amount now.

The full draft names 1,000 per alternative, both D choices as needed, recovery
and later band validation. R=50 at D=4 is a prospectively specified reduced
sensitivity study inspired by §10, not execution of the complete predeclared
stage or a measured D=8 underpowered fallback.

If a gain-response curve becomes the scientific claim, declare multiple gains
before running it. The existing 0.003/0.01/0.03 points are appropriate labelled
points, with uncertainties; monotonicity is an expectation to examine, not an
assumption to enforce. A stronger 0.03 positive-control addition can help
interpret low detection at 0.01, but needs its own predeclared scope and budget,
and must not replace unfavourable 0.01 results. No such extension is approved
here. For the present bounded question the single target is enough.

The companion script inverts binomial tail probabilities and checks the
published NIST example and the zero-count formula; it imports no fitting code.
[NIST exact interval construction](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

## Q4 — Priority is reasonable; the proposed interruption and timing are not ready

For the new SI sensitivity question, ordinary historical-cluster power is more
directly relevant than finishing replacement-interval validation. That gives it
a reasonable claim on the **next available, budgeted** local compute. It does not
establish that stopping either live probe now is the best schedule. The PC's
JOB E is the current probe; JOB D is complete. The Mac probe, PID 8012/PPID 1/
PGID 8010 with caffeinate 8014, was checked live during this review and left alone.

Do not schedule a 31-hour takeover from the cloud timing average. Even accepting
6,188 fitter-seconds as quoted, 200 x 6,188 / 3,600 / 11 = 31.25 is only an ideal
division of a historical workload. It does not measure Mac mixture performance,
compilation, memory/contention or chunk stragglers. No new timing audit or
benchmark was run by Codex. The protocol's own Mac/cloud measurements demonstrate
why such rates cannot simply be transplanted.

Likewise, “checkpointed, resumes without loss” is false for kill/relaunch. The
probe saves completed refit resamples; original dataset fits are rerun, in-flight
work can be lost, and complete rows wait for a whole chunk. Suspending a live
process tree is a different operation with its own resource consequences. A
planned owner-authorized interruption should preserve the exact process tree,
paths, checkpoint identities and restart settings and account for lost work.
No signal, restart or duplication is part of this review.

Before requesting the owner's execution go, Claude can prepare a concrete run
manifest and ledger row with these choices:

1. Historical comparison: D=4, 64 concepts, layer 41 only, four inner and eight
   outer starts, fixed-score B=2,000, all four 0.01 alternatives, 50 fresh dataset
   seeds per alternative; preserve d4v12b and record source/runtime provenance.
   A modern runner must explicitly reconcile relevant source and failure-policy
   differences with the historical target; source hashes alone do not prove
   behavioural parity, and failed rows must retain the current explicit status.
2. Call `power_points(..., targets=[.01])` through an explicit scoped runner.
   The CLI defaults otherwise change layers, inner starts and number of points.
   Bind the gain file's D, checksum and source hash through the accepted-artifact
   contract; do not use its entry-only CLI check as cross-snapshot authorization.
3. Benchmark at least one complete dataset from each of the four alternatives
   on the intended machine, before committing the campaign. Retain valid benchmark
   rows in the fixed sample under a predeclared policy. Stop on technical or cost
   failure, save everything, and report an incomplete screen as incomplete.
   Low sensitivity is a result, not a reason to change the rule or stop reporting.
4. Write a measured wall/worker-hour cap, checkpoint cadence, independent seed
   schedule and interruption/resumption plan. Prefer available cores or a safe
   probe boundary when feasible. Any scheduling change remains the owner's call.

The separate pilot row 16 does not inherit an inference approval from this
recommendation. A 64-concept single-layer simulation cannot validate a
16-concept pilot's folds, a 35-layer band, decoders or the target bridge. Pilot
numbers remain descriptive under §5; no H1 verdict follows. The clue audit,
capture gates and prior route-A conditions are unchanged. I have not reviewed
or implemented the proposed scores-to-Dataset bridge.

## Q5 — Each alternative first; pooling only as a labelled secondary average

Report, for each generator, attempted/completed counts and all four outcomes:
mixture, graded, inconclusive, unavailable. Primary detection frequency is
mixture calls / attempted datasets, so technical failures are not quietly
excluded; also show availability and any conditional-on-usable frequency with
its denominator. A row never attempted because the campaign stopped is missing
work, not an observed assay failure. Keep seeds and paired primary/ensemble/
inherited-pair decisions so their differences can be read on the same datasets.

An equal-weight mean of the four rates is legitimate as a declared descriptive
average over **this four-setting design**. It cannot replace the four rows or
establish the protocol's “under every mixture alternative” criterion. For example,
rates 0.4, 1, 1, 1 average 0.85 while one alternative is poorly detected.

With independent replicates and fixed stratum weights w_g, its variance is
sum_g w_g^2 p_g(1-p_g)/R_g. At four equal R=50 and p_g=0.8 this gives MCSE 0.0283.
Heterogeneous strata are not generally one common-p binomial experiment, so do
not attach an ordinary exact Binomial(200,p) interval as if they were. If common
random numbers couple settings, include covariance or preserve the pairing in
the uncertainty calculation. Report the minimum per-setting estimate as a
descriptive worst observed setting, with the individual intervals visible.
Morris et al. §5.2 specifically caution against averages over mechanisms hiding
conditional performance; the four rows remain the scientific result.

## Q6 — The named gain artifact passes; the premise about its age is wrong

Gate enforcement `4677e41` is 11 September; the named local twelve-pair artifact
`3ca9304` is 13 September, generated under `9b277df`. Its independent checks
already exist and the current stored-entry gates accept all twelve. The legacy
cloud file that motivates the revalidation route is a different file. There
is no reason to recompute these fits merely because Q6 says this artifact
predates the gate. Do not choose repeated check seeds until one passes.

The brief also overstates agreement as “inside its standard error” for every
pair. For M3V at 0.01, calibration 0.01017444 versus check 0.00948088 differs
by about 1.38 check SE (0.00050268). The declared tolerance gate passes; a
one-SE agreement rule is not the gate. State the actual criterion.

This is acceptance of the **stored evidence under the checked contract**,
not a numerical reproduction of calibration or automatic compatibility with
future code. The dispatch manifest must preserve its checksum, generating code,
D, calibration/check seeds, counts, attained gains and reference-search policy,
and state any explicit mapping to a newer execution snapshot. If the generating
density or gain-reference definition changes, fresh declared calibration/checking
may be needed; if only the small-sample inference rule changes, old scales can
remain labelled generator-reference targets, but their meaning is still not
that rule's expected CV gain. A different D is not silently approved by this D4
artifact. Report any revalidation actually performed, with its reason and result;
none was performed by Codex.

## Disposition boundary and evidence

Final evidence: the preserved gate script/output at `da6070d`, the new
standard-library MC script/JSON, and this record. Source hashes match the
checkpoint; reviewed manuscript/docs were clean at `22213342`. There was no
reopening of the 12,000-row numerical audit or prior policy/PDF reviews.

The real wrap `01a0a8a3` -> `01a0abca` was independently verified from the latest
native attempt (suffix `01a0abbd`), common registry and committed prompt at
Unimog `0a046cb8`. Exact name/topic retained; the complete native user receipt
matches the unchanged prompt except for its terminal newline. Prior park records
and failed historical attempts remain intact. This review continued after wrap.

Ownership: Codex review/evidence/reply/receipt and R052 log append only; Claude
manuscript/protocol/dispatch/front matter; R084 instruments. The owner-go,
ledger, benchmark and spending rules remain: no AWS here, further cap USD3,000,
USD90,000 scale rejected, remaining roughly USD2,780 only a dated estimate.
B remains rejected as written; A retains its separate gates. No publication,
push, scientific launch, interruption or protocol amendment is authorized by
this record. Existing jobs and other-owner files remain untouched.
