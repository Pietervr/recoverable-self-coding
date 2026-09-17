# Row 17: AWS completion of the M2S refit probe — Codex second opinion

17 September 2026. Reviewer: `GPT: R052 Entropy paper`, native session
`01a0adb6-5e09-7340-8470-22f1e9b75834`. Claude retains dispatch and ledger ownership.

**Verdict: not on board with launching the eighteen-replicate campaign as declared.**
The schedule purchase is scientifically reasonable, and keeping completed and
in-flight work on the Mac is the right default. Three matters need resolution:
the parity panel does not exercise the procedure being pooled; the running Mac
still owns all forty tasks; and the proposed timing/budget control is incomplete.
This is a bounded execution review, not a reopening of sens600 or prior reviews.
The owner's spending authorization stands; the outstanding gate is this review.

## Evidence and scope

Read the complete brief at RSC `c900d04`, 114 lines / 7,476 bytes, SHA256
`351439ccb947dbeac62e3d3683ef6d4ddd4a020cb82c493ac9860dffc42c2b82`;
working bytes equal that commit. Read `rsc_t1_simulation_design.md` end to end,
including rows 2, 5, 6, 14, 15 and 17; the complete prior saved power-stage reply;
`probe_refit.py`, its launcher, `launch_t1.py`, `t1_job.py`; and the relevant full
generation, queue, pipeline, interval and checkpoint functions in `simulate.py`
and `analyze.py`. Source hashes and reproducible checks are in
`2026-09-17_refit_aws_codex_checks.{py,json}` beside this record.

At 12:40 PDT the local CSV contains eleven emitted rows, all M2S omega 2;
twenty-two checkpoint files exist, seventeen with fifty recorded resamples and
five with 46–48. These are progress/identity observations, not a numerical
checkpoint audit or outcome interpretation. The brief's earlier 13 complete / 9
in flight is a dated snapshot. Chunked output explains why completed resamples
outnumber emitted rows. The eighteen unstarted datasets remain in the live
process's precomputed task list. PID 8012 / PPID 1 / PGID 8010 and caffeinate 8014
were read back with their command and start time; no signal was sent.

No fit, simulation, AWS account lookup, cloud operation, source edit, migration,
probe interruption, manuscript/protocol edit, or push was performed. No sens600
outcome was inspected. Its supplied status is context, not a new validation here.

## Q1 — the three M3 cluster datasets do not license refit pooling

**No.** Retain and report the declared positional panel, including its limitation;
do not discard it or replace its points after seeing its comparison. A pass is
useful evidence for those three M3 datasets under the historical cluster pipeline.
It is not evidence that every numerical path is hardware independent.

The target is M2S omega 1 and 2, seed 2027, `interval="refit"`, B=50,
code/config `fab869c34eb6`. The panel is M3 at one scale, seed 2026,
`interval="cluster"`, B=2000, hash `625798e9e7f4`. Although every generator is fitted
by the same candidate members, the input changes the optimiser paths, active
bounds, recovered fits, selections and tail scores. Cluster mode never calls
`refit_bootstrap` (`analyze.py:366`); it misses its duplicated-concept grouping,
resampled fits, checkpoint identities and percentile tails. Determinism on one
input is not a proof of equivalent behaviour on all inputs.

Matching the short code/config hash is also insufficient: `simulate.py:45` hashes
three sources and settings but not the numerical library versions. The actual
Mac rows record NumPy 2.5.3, SciPy 1.18.1, joblib 1.6.0; `launch_t1.py:37` installs
NumPy 2.4.6, SciPy 1.18.0, joblib 1.5.3. Both name JAX 0.11.1. Thus the proposed
comparison is not architecture alone. Pin and record the actual Python, JAX,
jaxlib, NumPy, SciPy, backend/precision and source settings; either align the
environments or explicitly qualify the tested pair. NumPy itself limits stream
compatibility guarantees to much stricter build/environment/machine conditions:
[NumPy compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html).

**A proportionate replacement gate for this bounded probe:** prospectively add a
matched end-to-end refit panel containing at least one fixed dataset from each
M2S setting (for example rep 0 at omega 1 and rep 0 at omega 2, fixed before
comparison), using their existing Mac results when complete and the intended
cloud environment. Run all fifty resamples, with identical source/settings,
data-generation and fit seeds, folds and resampling indices. Compare all three
predictors' points, refit endpoints/SE and companion cluster endpoints at the
declared 1e-6 nat/trial tolerance, plus identical decisions, availability/failure
flags, and selected-member records; preserve per-resample scores for diagnosing
a mismatch. Confirm input arrays and random-index identities before interpreting
output discrepancies. These duplicate panel runs are qualification work, not
additional independent replicates in the forty-dataset denominator.

Two settings are a minimum coverage of the actual procedure, not a theorem of
universal reproducibility. Report that limited basis. A few original fits and
predeclared resamples can be an earlier inexpensive failure screen and timing
benchmark, but cannot establish matching B=50 interval endpoints. If even that
qualification makes the acceleration unattractive, keeping the existing Mac
run is a legitimate outcome. A failed comparison does not mandate migrating or
rerunning the entire study: first diagnose it and retain separate provenance.

## Q2 — schedule purchase, with the original scientific limits

**Yes, provided the same forty unique datasets and procedure are retained.**
Machine allocation changes the delivery time, not the estimand, design or
evidential scope. Neither paying nor obtaining a parity pass promotes this into
coverage validation, CONF approval or a procedure amendment.

There are twenty independent datasets per omega, not ten per setting. Binomial
MCSE is at most 0.112 at n=20, or about 0.067 if coverage is 0.90; exact intervals
and per-setting counts still belong in the eventual reading. The brief's
“MC SE about 0.15 at n=10” is not this probe's planned per-setting denominator.
B=50 leaves its own percentile tails poorly resolved. Keep the paired cluster
comparison, independent reference uncertainty (especially omega 2's heavy tail),
failures and incomplete work visible. Do not pool the two omega settings into a
single coverage claim. This remains a screen for a large change, not proof of
0.90 coverage or proof that a negative screen rules out refitting.

## Q3 — adding capacity is compatible in principle; the claimed split is absent

My prior Q4 supported a separate sensitivity run while both refit probes stayed
untouched. It was not a blanket approval to repartition a running refit queue.
The new scope appropriately came back for this review.

`probe_refit.py:68` calls `run_points` for all forty tasks. `simulate.py:271–286`
constructs the task list and subtracts completed CSV rows once, at startup; it
does not re-read an exclusion manifest or completed rows between chunks. The
isolated fixture executes that actual function with fake workers: a row supplied
after the first batch is still computed in the second batch. Editing the source
file or adding cloud rows now cannot change the already-loaded task list.

Consequently, “the Mac continues untouched but owns only 22” is not implemented.
When the current chunk finishes, it starts its remaining eighteen. Cloud work
would duplicate that future work unless a concrete queue handoff is arranged.
Do not kill or pause it in response to this finding, insert placeholder rows,
or choose between duplicates according to which result is favourable.

Before dispatch, declare the exact (generator, grid, rep, D, seed) manifest,
confirm it against current completed/in-flight identities, and specify how the
Mac relinquishes only unstarted work at a safe boundary under the owner's
preserved constraints. The current runner has no drain/exclusion interface;
do not describe one as already available. Alternatively leave it wholly
untouched and explicitly propose duplicate cloud acceleration, with its extra
cost and a predetermined retained-copy rule disclosed. That is a different
execution proposal. Either route needs concrete disposition; this record does
not authorize signals or an improvised scheduler change. PC JOB E stays outside
scope. Final pooling must have one independent row per declared dataset identity.

## Q4 — no migration is sound; timing, restart and spend need concrete controls

**I favour no migration.** It preserves accrued work and avoids a difficult
checkpoint transfer for little schedule benefit. It does not remove the need
to match the future rows' procedure and runtime or resolve their ownership.
One instance per replicate is acceptable for isolation if the intended shape,
worker count, memory use and rate pass a measured benchmark. The current call
path gives each refit replicate one worker; unused vCPUs are still paid for.
Sequential resamples describe this call path, not a mathematical requirement.

The brief's arithmetic does not follow from its stated proxy:

- 4,730 seconds = 1.314 hours per pipeline; one original plus fifty resamples
  would be **67.01 hours**, not 55. Across eighteen: **1,206.15 instance-hours**.
- At the launcher's estimated USD 0.467/hour and the assumed fourfold discount,
  that is **USD 140.82**, versus **USD 563.27** at that full rate. These are
  conditional arithmetic, not a freshly verified tariff or spot-price promise.
- Eighteen full 72-hour jobs imply USD 151.31 at that discount or USD 605.23 at
  the full rate. A 72-hour timeout alone does not enforce a USD 250 fleet cap.

More fundamentally, a mixture dataset's cluster-analysis median is not a
benchmark of a duplicated-concept M2S refit at either stress setting. Measure
the original analysis, initial compilation, and several refit resamples at
both omega values on the intended instance/environment before widening. Use
elapsed time including outliers and restart overhead, not just a favourable
median. Budget the parity work and pilot explicitly as well as the production
rows, against their existing row caps and the USD 3,000 further-spend ceiling.
The dated USD 2,780 remainder is not a current balance.

Checkpointing is useful but not a guarantee of a free resume. `analyze.py:352`
repeats the original nested analysis before reading bootstrap checkpoints.
`t1_job.py:111` continues without restored checkpoints on a download failure;
its explicit mirror upload is after a completed dataset chunk, while the
SageMaker-managed `/opt/ml/checkpoints` sync is what protects intermediate
resamples. Confirm actual S3 persistence and resumed identity/counts on the
qualification work; freeze the namespace, task-to-shard mapping, sources and
runtime. No launch is licensed on an assumption that restore must have worked.
[AWS documents automatic checkpoint synchronization and restoration](https://docs.aws.amazon.com/sagemaker/latest/dg/model-checkpoints.html),
but the application must consume those checkpoints correctly.

`launch_t1.py:164` also turns `--max-hours 72 --spot` into 72 hours of runtime
and **144 hours including waiting**, rather than a 72-hour calendar deadline.
Record both clocks and the aggregate campaign stop rule, including retries;
do not silently reset the agreed clock with manual relaunches.
[AWS distinguishes those limits](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_StoppingCondition.html).
Managed Spot savings are measured from billable versus training seconds;
past savings do not lock future price or capacity
([AWS Managed Spot guide](https://docs.aws.amazon.com/sagemaker/latest/dg/model-managed-spot-training.html)).
Use an explicit fleet-spend watch and conservative stopping reserve inside
USD 250, with no automatic on-demand fallback or cap extension.

## Disposition

Keep row 17 unlaunched as declared. Return a bounded revision addressing the
refit-specific qualification, actual task ownership, measured two-setting
timing and enforceable aggregate cap. Preserve the original positional parity
result and all job evidence. No extra owner spending permission is being
invented here: the existing authorization and its paid-run gate remain in
force. A recheck can address only those execution points. Claude owns any
revised pilot/dispatch and ledger; Codex has implemented none of them.
