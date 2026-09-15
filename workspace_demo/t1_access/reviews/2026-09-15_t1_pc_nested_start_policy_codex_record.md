# Codex second opinion — JOB D nested start-policy development check

15 September 2026. Requested by Claude Entropy SI at 08:39 PDT, against
Unimog `a9c9266e`, `prompts/2026-09-15_t1_pc_nested_start_policy_check.txt`.

**DRAFT — substantive reading complete; seed/cost checks and final disposition
remain. Do not use this checkpoint as launch clearance.**

Codex owns this review, bounded supporting evidence and the R052 log. Claude
owns the dispatch brief, protocol, production, execution, monitors, manuscript
and R052 front matter. The owner approved the PC run in the native Entropy SI
transcript at 08:36:39 PDT / 15:36:39Z. This review does not launch it. Previous
Melcon stage-C, calibration, publication and session-tooling reviews remain closed.

## Reading and the procedure

Read the complete JOB D brief; the previous fitter-start record at RSC
`563d52a` and its brief/dispositions; the JOB C report and provenance at PC
`c02e559`; `rsc_t1_simulation_design.md`; the T1 pre-registration, especially
§§7–10 and 14–15; `analyze.py`; the model start, selection, recovery and scoring
code; and `simulate.py`'s dataset seeds and added-start generators. Fresh logs
and status were checked in both repositories. RSC has no local CLAUDE.md or
AGENTS.md. No numerical audit, fit, synthetic recording, bootstrap fit or cloud
job has been run by this review.

The comparison uses the same synthetic dataset for every policy. Each policy
must independently select a training solution in every inner and outer fit;
the inner held-out concept scores then select each family's member, and the
outer held-out concept scores supply Delta. All eight members are already
refitted in every outer fold by `layer_pipeline`. Thus archived fits can support
all four policy variants without further optimization. They cannot supply fits
on a different training sample, including a bootstrap resample.

## 1. Proposed disposition and scope

Accept this as a bounded, paired development step toward §4 of the previous
record, once the launch requirements below are incorporated and verified.
It does not complete that section's adoption requirements.

The important scope correction is **interval="cluster", n_boot=2000, one
layer (41)**. JOB D measures changes in nested point estimates, member choices
and the fixed-score cluster interval and its decision. The primary interval's
replacement by the refitting bootstrap has already been invoked (§10 and the
design companion §6). JOB D does not measure that interval, its decisions or
its coverage. It does not validate the 35-layer band. State this in the brief,
CSV and report, rather than calling the resulting decision today's primary
decision without qualification. A full B=200 refitting interval is outside
this job; do not quietly add one.

Keep the four settings and six declared replicates as a focused development
screen. M2S omega 1/2 address the observed stress conditions, M2B is a control,
and M3H sep 2/tau 0.5 is a mixture anchor. Its raw separation does not establish
that it is near the nested decision boundary or at a calibrated gain. The later
independent validation must include near-boundary alternatives and all retained
nulls; these four settings cannot stand in for that grid.

## 2. Prefixes, recovery and exact reproduction

Specify the candidate pools as ordered lists of stable start IDs. A sound
definition is: the exact existing cold batch and every recovery batch it
actually invokes, followed by the prescribed independent added batches.
Preserve the cold generator's RNG state across both recovery stages. No added
batch consumes that RNG. No extra recovery after the policy union is implied.
This deliberate cold-first recovery remains part of every variant, even when
an added batch would have converged without it.

Use **all** of `models._pick`: best finite converged training likelihood;
otherwise best finite nonconverged run, flagged; otherwise no solution.
First in canonical order wins an exact tie. A newly converged run can displace
a higher-likelihood nonconverged run, so training-score monotonicity is not an
unconditional check across this transition. Recovering a finite flagged fit is
different from declaring an assay failure. Keep inner unscorability, an entire
unscorable family and outer retained-member failure exactly as `layer_pipeline`
handles them. Never pick a start using held-out scores, carry a winner between
training folds or use generator truth to initialize a fit.

`simulate._extra_starts` drops the repeated moment start and mirrors alternate
skew-coordinate jitter starts. `_challenge_starts` supplies M2K's four ordered
sign combinations of +/-2, followed by twelve wide starts, within the sixteen.
Keep these exact semantics. Freeze complete seed tuples with member index,
outer/inner fold, size and batch suffix; M3H's first sixteen wide vectors must
equal a separately constructed sixteen-vector batch at full precision.

Recompute each variant's inner scores, selected members, all outer logq,
per-concept Delta, interval and outcome. Reuse the same folds and cluster
resampling indices across variants. Save selection, ensemble and historical
predictors from these same fits: that adds scoring, not optimization.

Replace the literal byte-identical-row check with **exact numerical payload
equality on the same PC/runtime and baseline configuration**, with a declared
comparison field list. Timing fields necessarily vary; truthful source and
policy provenance must differ when code differs. Neither belongs in numerical
parity. Do not disguise new code under an old hash to make a row match.

The first real M2B dataset is a useful integration check, but cannot exercise
every recovery path. Before main fitting, add bounded mocked checks for recovery
levels 0/1/2, a finite flagged fallback, all-nonfinite failure, exact ties,
converged preference, inner family failure and outer retained-member failure,
at both cold counts. Archive/reload/replay every variant and compare against
direct variant execution with mocked fitting. Confirm unset-policy numerical
parity and M3H prefix equality. An implementation has not yet been provided to
Codex; these are implementation acceptance conditions, not reported test passes.

## 3. Archive and identity

The present `FitResult.runs` lacks x0 and per-start duration, and its local
start indices restart in recovery batches. Add capture where starts are
generated/executed, preserving ordering and numerical behavior. Store global
and batch-local IDs, x0/theta/loglik without rounding, convergence, optimizer
termination/message, iterations/evaluations, recovery provenance, and elapsed
time. Distinguish recovery attempted from the selected solution's convergence;
under the cold-first definition recovery effort is shared across variants.

Keep the exact dataset arrays or a reproducible generator manifest plus their
hashes; concept/family mappings; actual outer and inner folds; training/scoring
indices; the outer-training floor used at both sizes; inner scores and each
member's per-concept outer scores; winner IDs and full outcome payloads.
This permits later explanation of a selection change or a tail loss without
another fit. Record whether all required starts and fits finished; failed
datasets remain rows, never silently replaced or dropped from summaries.

Freeze an exact baseline and committed implementation **before even the first
real verification fit**. The PC JOB C provenance lists models/analyze blobs
`5f78693357611420005ffadef814ee4b56bb9b72` and
`5a6e9c1a16049b218595c3346347cbc505ef4cdb`, which match the current Mac tree.
Its simulate blob is `15f58cbd6c7583303be01948b41d05c5d778d16f`; the Mac's is
`9bd9d3c9467e68ae0b9b84ff88af02757b0dc347`. Resolve that difference before
claiming a shared baseline; "c02e559 or later" alone does not pin one.

Bind the ordered policy, variants, start counts/jitter/recovery, all seeds,
effective Config/model globals, loaded source hashes (including new wrapper or
archive modules), runtime, dataset and folds into a JOB D identity. Existing
`simulate.config_hash` and `analyze.dataset_identity` explicitly enumerate
settings: a new Config field is not automatically included. Use a separate
JOB D manifest/namespace if that preserves the default production path.
Checkpoint identities/checksums must reject partial or mismatched artifacts;
test interruption/reload without fitting. Prefer checkpointing each fit/start
as well as each dataset, given the PC interruption history.

## 4. Seeds, reporting, cost and adoption

The proposed member/grid/replicate seed inputs are appropriate, with variants
sharing a dataset and its cold streams. `dataset_seed` returns a random 31-bit
integer: different input tuples do not mathematically guarantee unique output
seeds. Enumerate reps 0–5, require 24 distinct seeds and data hashes, and check
disjointness against the previously used dataset identities. No opportunistic
replacement seed. Archive the manifest and RNG/runtime identity.

For paired summaries, form differences within each dataset and resample those
whole paired rows within a setting. Six datasets, not 1,200 member fits or
2,000 bootstrap draws, are the replication count per setting. Publish every
paired value and availability transition. The bootstrap interval is descriptive
with five/six datasets, particularly at omega 2; absence of a change does not
establish equivalence, a stable expectation or optimizer saturation. Report
the fraction of valid pairs and the full failure counts. Preserve extreme
observations; a leave-one-out summary may describe influence without changing
the primary mean. Freeze the reporting and what happens after JOB D; no automatic
production adoption from a favorable result.

Re-cost the **actual** policy (M3H now 32 wide, M2S 64 narrow), rather than
carrying forward the earlier ~8.3 multiplier (M3H 16, M2S 80). The job executes
160 inner and 40 outer member fits per dataset; added starts differ sharply
in runtime. Distinguish summed worker elapsed time, measured CPU time and total
wall time. A lone M2B dataset does not measure loaded throughput or the other
three generators' tails. Benchmark a predeclared balanced first wave within
the existing 24 datasets at the intended worker count; four physical workers
is a reasonable starting layout. Seven workers previously delivered about four
solo processes' throughput, not seven. Do not divide a solo timing by seven
or discount contention twice. Include baseline verification, compilation,
scoring, archive I/O, zip/checksums, interruptions and tail completion.

The runtime rule needs a stopping boundary: after the fixed preflight, keep six
or reduce to the predeclared reps 0–4 in every setting based only on runtime;
retain all completed data and declare the rule. If twenty datasets still project
past 60 hours, stop and report for a revised scoped decision. Never continue
past the cap merely because the count was reduced. Keep the brief's report
before continuation; the execution session owns that gate.

For adoption, a policy A changes theta(g,A), the expectation of the complete
procedure. Original estimates, refitting-bootstrap repetitions and independent
reference means must use A. JOB D's six-row mean is not an adequate reference
target, especially at omega 2. Later validation needs a frozen A; independent
development/validation/reference streams; all retained nulls and calibrated
near-boundary mixture alternatives; the selected interval and required layer
grid; Monte Carlo precision and a rule for unresolved acceptance thresholds.
Ordinary nested-layer timing is useful input to its budget, but resampled
datasets have repeated concepts and different fit shapes. A bounded benchmark
of actual refitting resamples and intended concurrency is needed before that
budget becomes measured. This review does not authorize those future fits,
cloud spending, a Melcon revision or production adoption.

## Remaining work before FINAL

- Check the actual 24 seeds using the isolated existing seed function, without
  importing model code or generating data; compare known prior seed sets.
- Recompute this policy's linear costing from the existing timing evidence;
  no audit, optimizer or bootstrap rerun.
- Inspect the PC/Mac simulate-blob difference; complete primary-method source
  reading (NumPy parallel RNG; Morris/White/Crowther simulation guidance).
- Finalize Q1–Q4, commit explicit owned paths, append/commit R052 log, send ONE
  substantive xs reply to Claude Entropy SI, and verify the exact full-record
  receipt. No reply has yet been sent for JOB D.
