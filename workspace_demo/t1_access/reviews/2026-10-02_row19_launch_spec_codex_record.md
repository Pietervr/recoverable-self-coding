# R052: row 19 Lengau qualification-slice launch specification

2 October 2026, America/Phoenix (-07). Reviewer: **GPT: R052 Entropy paper**,
native `01a0d19e-2127-7051-9a61-6db771088559`.

**Verdict: NOT ON BOARD with launching stage 1 as presently implemented.**
I remain on board with the staged, sequential engineering route in `c3e1d2a`.
The committed code contains useful recovery mechanisms, but the benchmark
addendum and an owner go alone cannot repair the integration, accounting and
control gaps below. This review approves no submission, fit, coverage reading,
paid fallback, screen or further setting.

**Brief:** Unimog `236fcc1fdb53dd24a0e7fa734fbe5f82b9521c73`,
`prompts/2026-10-02_codex_r052_row19_launch_specification.txt`, SHA256
`2193bda7ac1687da1a010ee482424aadfcce15e78e0c4abf9184b68caab5135b`.
Handoff `546f1dda-c4fb-5b51-8962-497965d1b42c` was accepted after ownership
commit Unimog `3b380324`, before review edits.

**Exact source reading:** RSC `4e26d03658ef60acd918674c48afdedc17df8a18`,
including the `9a6fbcc` manifest/templates, `ad0eb9f` comparator,
`ff82dd0` hooks and `5f6333c` policy. Line references below are to these
immutable blobs, relative to `workspace_demo/t1_access/`. The four source pins
reproduce exactly from local git blobs. Source-reported Lustre cherry-pick
`712d0f6` is not in the local object store; this read does not independently
inspect the remote clone. Preserve its dedicated ownership and do not edit a
queued/running job's tree.

The proposed system is three fresh development datasets at M2S omega 1,
D=4, layer 41, rho 0.9, eight concepts per family, with eight cold outer and
four cold inner starts plus the per-member additions. Each uses B=200 from the
outset, sequential refits on one core, durable restart checkpoints, and a
separate normal/interrupted/resumed control on indices 0..19 of the same B200
draw. The collective ceiling is 1,500 Lengau core-hours, including controls,
stage 0, lost work and restarts. It measures execution and recovery, reads no
coverage, and qualifies no packed or parallel-resample configuration.

Read the full brief, completed `c3e1d2a` record, current owning ledger row19,
protocol sections7.4/8/9/10.1, submitted runner/manifest/templates/comparator/
watch and their fixtures. Three peers checked the independent paths. All
review work was static reading and git/blob/hash inspection. **No submitted
code, import, test, fixture or CLI was executed.** No fits, simulations, model
or image operations, job polling/submission, HPC/cloud/account operations,
worktrees or push. No private audit/plant/reader/human/pull material was opened.
Reported fixture counts are implementer evidence, not a Codex rerun.

## 1. What is credited

- The named start-policy implementation is real: per-member additions, keyed
  streams, cold counts at both training sizes, deterministic lowest-index ties,
  unchanged recovery chain, and padding64 (`models.py:112–176,643–704`;
  `analyze.py:167–176,218–232`). M2S remains expressly an interim candidate,
  not adopted. The source-bound identity includes the effective policy.
- The runner checks all four non-null source pins and the declared Python,
  JAX/jaxlib, NumPy, SciPy, joblib and machine versions before its original
  fit (`row19_slice.py:52–69,114–119`). One-core/thread configuration is
  established before imports, and the declared route uses sequential calls.
- B200 draws and per-index fit seeds are unchanged across resumes; duplicate
  concepts stay together in both selection levels. Strict restore validates
  existing record identity/index/draw/payload/checksum, refuses conflicting
  valid duplicates, and counts repaired trailing fragments
  (`analyze.py:483–531,600–655`). Missing indices run in order; accepted records
  are not refitted within that hook. Its checkpoint lock and per-record fsync
  are useful, and partial chains expose no usable interval (`:658–719`).
- The original cache's intended purpose and file+directory fsync/rename are
  appropriate. Its implementation needs A and D below. The hook-level lock
  evidence does not establish ownership of the preceding original-fit phase.
- The comparator's scientific field selection and exclusion of timing and
  run-specific payload checksums are appropriate. Excluding checksums from
  *equality* does not excuse validating each file's own checksum.
- Python's exit status is preserved through the PBS `tee` pipeline. The
  report-before-stage2 and owner-go-per-stage rules remain appropriate.
- Deferring the policy-matched reference is acceptable for this engineering
  slice. It must exist under its own row before coverage is interpreted; old
  references remain sensitivity evidence. No new reference is demanded merely
  to test execution. Real Lustre/PBS interruption evidence is an output of the
  slice/control, not something this desk review pretends has already passed.

## 2. Exact launch conditions

### A. The real original-run cache cannot be published

`analyze.run_dataset` returns `folds` as a list of NumPy arrays and `params`
as a dictionary of stacked arrays (`analyze.py:99–111,288–300`). The runner
converts only top-level arrays and `delta` (`row19_slice.py:163–165`).
`write_atomic` uses `json.dump(..., default=float)` (`:35–39`); `float` cannot
encode the multi-element fold arrays or nested parameter arrays.

Thus a fresh real original fit reaches a serialization error **before the
first bootstrap resample**. Its unfinished `.tmp` is not an admitted cache;
a restart can buy the original again. This is a static type/path finding,
not a run performed by this review. The runner fixture omits `folds` and
`params` (`test_row19_slice.py:20–27`), so its cache success does not test the
actual returned structure.

**Required:** a complete lossless nested serializer/restore contract for the
actual `run_dataset` output, with a shaped no-fit round-trip fixture including
folds, parameters and arrays at every nesting level. Restore the arrays needed
by aggregation, preserve full precision and explicit failed/nonfinite semantics.
Do not silently discard required scientific fields to make JSON succeed.

### B. Completion starts a second unprotected B200 chain

After its strict durable B200 call completes (`row19_slice.py:176–178`), the
runner invokes `A.analyze_dataset(..., run=...)` (`:191–194`). Passing `run`
avoids another original fit; it does **not** supply the completed bootstrap.
With `cfg.interval='refit'`, `analyze_dataset` calls `refit_bootstrap` again
(`analyze.py:384–386`). The runner never set `cfg.refit_checkpoint_dir`
(its default is `None`, `:66`), and this second call receives no checkpoint,
deadline, strict-restore, durable or progress hooks.

It refits the same 200 indices again, can exceed the remaining PBS time, and
does not publish status until afterward. Timing callbacks and the resource
snapshot taken at runner `:181–190` miss this second chain. The runner tests
replace `analyze_dataset` with a result-producing lambda (`test_row19_slice.py:
41–46`), hiding the integration failure.

**Required:** aggregate the cached original and already validated `rb`
without dispatching any fit; retain the paired cluster interval from that
same original. Add a full-completion shaped fixture using the actual
aggregation path that proves no new `run_dataset`/bootstrap work is bought.
Simply pointing final aggregation at a checkpoint with permissive defaults
does not preserve the stated strict recovery contract.

### C. The collective cap is not an aggregate submission guard

1. `Budget` is stored at `<root>/budget.json` (`row19_slice.py:110,123`).
   Main, C1-normal and C2/C3-interrupted use different roots, so each gets an
   independent 1,500-hour ceiling. Stage0's declared charge of up to24 hours
   is not debited by this ledger (`row19_policy_bench.pbs:15,23`).
2. Each process loads the ledger once (`:74–76`) and overwrites its retained
   snapshot on start/end (`:83–95`), without lock/reload. A concrete ordered
   trace needs no simultaneous writes: J0 starts; J1 reads J0 and adds itself;
   J0 ends from its older state and replaces the file with only J0, erasing
   live J1. Atomic fsync/rename does not make this read-modify-write atomic.
3. Reservation is made only after PBS has allocated and started the job
   (`:108–124`), not before submission. Spent time is runner wall time after
   imports, not scheduler-accounted allocated time (`:92–95,201`). A job
   refused then has already consumed allocation. The declared four-submission
   limit is not read/enforced; numbered template names are not a counter.

**Required:** one campaign counter shared across every root/control and
stage0, with locked fresh read-modify-write, persistent submission/attempt
ownership, and a reservation before each qsub/resubmission. Reconcile against
PBS allocated cores and elapsed time, or conservatively retain the full
reservation until that accounting is verified. A separate reservation tool
used by the named operator is sufficient; automatic job submission is not
required. Never release a killed job merely because no runner end was saved.
Leaving its full reservation live is presently conservative and is credited.

At maximum declared charges, the budget equation is
`24 + 48 + W_int(hours) + 48 + 144*N <= 1500`, where N counts full-length
main-job charges. Initial stage0+C1+C2+three-main reservations are
`504 + W_int(hours)`, not `480 + W_int`. The allowed N depends on W_int and
actual settled costs; “about seven” is not enforced arithmetic. Early returns
may free verified reservation headroom, so this equation is not an absolute
count of submissions. The separate four-per-dataset rule still needs a
tracked declared maximum. Report incomplete qualification on exhaustion.

### D. Task admission, original-cache integrity and ownership precede fits

Strict checkpoint validation and its exclusive lock occur **inside**
`refit_bootstrap` (`analyze.py:628–655`), after the runner's original-cache
load or original fit (`row19_slice.py:147–168`). Consequently:

- A second process can perform an original fit/cache write before being
  refused as a second checkpoint writer.
- A committed bootstrap checkpoint with a missing original cache causes
  another original fit before restore is inspected. This is not a failed
  restore that holds without re-buying fits.
- The original cache verifies only its input `ident` (`:149–159`), with no
  payload checksum/schema/shape or stored-code-hash admission. A parseable
  changed `delta` can retain that ident and be accepted.
- Identity-derived filenames (`runner:147`; `analyze.py:624–625`) do not bind
  a task/rep to its *previously expected* identity. A changed manifest/runtime
  identity can silently select a new namespace instead of holding a declared
  resume. The robust identity digest distinguishes procedures; it does not
  itself provide this task-admission check.

**Required:** persist the frozen manifest/task/rep-to-identity binding and
expected progress, acquire task ownership and validate existing cache and
checkpoint evidence **before** any original fit. Refuse incompatible or
unexplained missing/damaged committed evidence; explicitly declared lost
uncommitted originals may be recomputed only under recorded authorization and
the same collective cap. Protect the original cache with a complete payload
checksum and strict schema/shape/identity checks, and demonstrate two-writer
refusal from before the original phase. No signatures, new attestation format
or universal storage guarantee are requested.

### E. C3 does not stop at the declared fixed control endpoint

`segment` means **this many NEW missing resamples**, not a cumulative end
index (`analyze.py:590–592,658–661`; runner `:102`). With C2 having committed
k>=1, C3's declared `--segment 20` adds20, ending at k+20. C1 contains20.
The comparator therefore rejects the nominal successful resumed control.
`test_row19_control_compare.py:28–30` instead uses7+13=20; it does not exercise
the declared C3 template. Merely passing20-k changes status `segment`, which
the current comparator also requires equal (`row19_control_compare.py:44–46`).

**Required:** declare and enforce the target index set0..19 independently
of this invocation's new-work allowance, preserve B=200, and compare a common
control-target contract. Exercise the actual C1/C2/C3 wrapper arguments in
a producing bounded fixture. Do not change B or post-select a convenient
prefix after observing the recovery outcome.

`W_int = original + about three resamples` is a sensible **initial calibration
proposal**, not a guarantee of the intended interruption. Stage0 times a
same-shaped M3H layer (`bench.py:30,54–59`), not this M2S original and its
variable bootstrap resamples. The runner starts its deadline after imports
and subtracts1800 seconds (`:108,120–122`); if that deadline is hit between
resamples it exits75 normally. It can therefore finish C2 cooperatively
rather than be killed by PBS. The manifest's literal20-minute example is
also stale (`manifest:41`): with a30-minute reserve, the bootstrap deadline
is already past at start, while the original is not deadline-gated.

Fix the addendum, actual PBS walltime, runner reserve and C2 interruption
policy together. Cost C1's original plus20 refits, startup and flush against
its48-hour allocation, and keep W_int inside the declared serial queue limit;
otherwise declare a legal control route/endpoint prospectively. Stage0 is a
planning proxy, not a measured bound for M2S throughput. The control report
must prove a real scheduled interruption,
at least one and fewer than20 accepted records beforehand, original-cache
reuse, and the actual lost in-flight/tail boundary. If it was killed in the
original or completed normally, that is recorded **non-qualification**, not
a passing recovery control. No additional real-fit pre-launch campaign is
requested: this is the slice control's declared purpose.

### F. Comparison must validate records and the exercised control

The field list `rep/chosen/stats/failed/failed_reason/ident/seed/n_rep` is
appropriate, and `fit_seconds/sha` should remain excluded from equality.
However, comparator `:14–55` validates neither each record's own checksum
nor required schema, finite/failure semantics, expected identity/index set
or target size. It accepts two empty files and equal incomplete subsets.
Missing scientific fields can compare as `None == None`; status evidence is
optional. Even with status, C3's `original_cached` is merely printed, and
`n_resumed>=1` does not establish a PBS kill or the intended C2 boundary.

**Required:** independently validate each supplied file's checksum and strict
record contract, bind the compared files/statuses to the declared task,
dataset and B200 target, require exact expected unique indices0..19 and
appropriate C1-fresh/C3-resumed/cache/actual-interruption evidence. Failed or
nonfinite scientific outputs retain their declared failure semantics and do
not become a favourable qualification merely because both chains failed
identically. A comparison can truthfully report parity separately from
technical qualification. Include empty/incomplete/missing-field/stale-hash/
wrong-target and non-producing control negatives in bounded fixtures.

### G. Live monitoring has false-green paths and no acknowledged stop boundary

`row19_watch.py:55` ignores a failed pull. It enumerates reps only from
already-present timing/status files (`:58–59`) and silently skips a missing
budget (`:99–107`). Failed transfer with an empty or stale local cache can
therefore say `no alarms` and exit0. A started job can spend hours stuck in
its original/first resample with no timing row: the four-hour test only runs
when rows exist (`:85–89`). An initial empty root before launch may honestly
say “nothing started”; once jobs are admitted, absent evidence is not a
healthy running campaign. Distinguish queue waiting from active/stalled work.

Checkpoint damage/other HELD paths return before publishing a new status
(`runner:167–180,195`). The watch's `n_damaged` test thus cannot reliably see
the refusal, and log tails are printed without classifying its exit/reason.
A checkpoint is fsynced before its timing callback (`analyze.py:674–676`);
a failure there can leave an accepted record, including a failed resample,
absent from the metrics on restart. Do not use timing-row counts as the sole
authoritative count of accepted work.

**Required:** expected task/job/rep identities, start/phase/freshness and
terminal/HELD evidence, failed-transfer/missing/invalid-record alarms, and a
first-record/original-phase timeout tied to the declared expected workload.
Reconcile progress metrics from validated checkpoint state without exposing
scientific outcomes. Validate the expected-fit range as finite/ordered and
state poll cadence and who acts. Stop further submissions on an unresolved
alarm or missing/invalid observation; do not green-light from a stale cache.

The hook starts the next resample immediately after a save; there is no
persisted campaign-stop request consulted at that boundary. A remote
`qdel after the resample is committed` is therefore not guaranteed to land
between fits. Add a stop/hold request with a checked boundary and acknowledgment,
or explicitly declare immediate cancellation with its bounded lost in-flight
work charged and accounted. Gate replacement submissions on diagnosis.
Finite operational guarantees under the declared environment are sufficient.

The watch also `json.load`s the entire status before removing result/interval
(`:42–44`); it does not satisfy the literal “never loads those entries” claim.
Use separate operational metrics or accurately say they are not displayed or
interpreted. `tee` failures and the final exit line (outside the live-log pipe)
must not be treated as a successful complete live record.

### H. Finish the bounded resource and measurement declaration

The prior manifest requirement included PBS memory, wrapper/loaded execution
identity, index/fold provenance, integrity/resource stops and recovery
ownership. The submitted manifest specifies cores/time but **no memory
request/limit** (`:64–76`), and PBS templates specify none. State the effective
requested memory/default as an actual value with the intended stop/diagnosis
rule; bind the wrapper/environment/backend/CPU/thread identity and backup/
attempt/stop ownership to this launch. This needs a bounded engineering
declaration, not the photograph arm's physical-memory machinery.

A different seed_base alone does not establish disjoint **resolved31-bit**
dataset seeds (`simulate.py:244–254`). Save/check the three resolved dataset
seeds/identities against the declared historical/reference exclusions without
inspecting sealed scientific outcomes. Separately retain the per-index
bootstrap/fit-seed derivation, folds/groups and B200 index matrix/hash;
those structural arrays need not themselves be disjoint from historical runs.
Existing deterministic recipes
and data/fold identity hashing are credited; complete the task-level admission
record rather than merely asserting disjointness in prose.

The manifest promises compilation seconds, but the runner only records
original elapsed time and aggregate fit seconds. Neither separates JIT
compilation. Its RSS/CPU/wall snapshot occurs before final aggregation and
status publication (`runner:181–195`); do not call it a complete job peak/time
measurement. Record the actual promised compilation/serialization/finalization
and scheduler resource evidence, or precisely delimit the measurement and
its limitation before it is used for costing. Parent/native-cache/archive
scope is stated for this one-process route; no packed-memory qualification
is inferred. Archive interrupted/held evidence and off-cluster checkpoint/
cache backups as declared, not only live display files.

## 3. Answers to R052's four questions

| Question | Answer at the reviewed snapshot |
|---|---|
| 1. Prerequisites3/4 satisfied? | **Not yet.** The concrete policy, four source pins, deterministic B200 draws, strict durable hook and no-coverage purpose are credited. A–D, G/H remain necessary to make real original/cache/final publication, collective budget, early task admission and bounded operation match the declaration. |
| 2. Interruption and scientific comparator? | **The proposed estimate and scientific field selection are reasonable, but insufficient as wired.** E fixes the cumulative endpoint and actually exercised PBS interruption; F validates each checksum/record/target and qualification evidence while continuing to exclude timing/checksum equality. |
| 3. Live alarm rule? | **Agree with stopping waste and holding further submissions; not with this watch as evidence that it is enforced.** G closes false-green, first-record, HELD/metrics and stop-boundary paths. H states measurement/resource scope. |
| 4. Launch after the benchmark addendum and owner go? | **NOT ON BOARD as specified.** Land A–H in the exact candidate and aligned declaration, supply producing bounded integration/control/admission evidence, then submit the corrected launch specification plus cost/W_int/range/resource values. Owner go remains separate. Real Lustre recovery is measured in the slice and reviewed with its report before stage2. |

The requirements are proportional to the already-declared row19 contract.
They do not demand universal filesystem/kernel behavior, perfect scheduling,
an adopted M2S policy before candidate testing, an existing matched reference
before an execution-only slice, full-chain uninterrupted parity, a new
parallel algorithm, a larger sample, a new attestation protocol, a blanket
unchanged-suite rerun, or immediate further HPC/model work by this reviewer.
The control/qualification may stop incomplete inside the cap; that is a valid
reported outcome, never a coverage disposition or permission to extend it.

## 4. Immutable reading pins and ownership

| File at RSC4e26d03, relative to `workspace_demo/t1_access/` | SHA256 |
|---|---|
| `models.py` | `28765f82b3e718c48521cf775add6220898752c662c4cdd1c3ffcdb113c4feef` |
| `analyze.py` | `972d92f6b9e435ed18fbf6c1e88300cc543950b59c7ed8aa8f563b47af2ae5bb` |
| `simulate.py` | `f588b9121be48ec553ab95e4dda5736941865498922468b5868c96758d0afe57` |
| `chpc/row19_slice.py` | `b51039a8f9aae51b00dc95f2854aa0fd1ec6dd08c6f885e5ba71a8c9fe3a2df8` |
| `chpc/row19_slice_manifest.json` | `471eb5528d36570f080700e1a83d1ad8f0a63b5dfe204fa45656f31c3374e6c2` |
| `chpc/row19_slice_rep.pbs.template` | `697bc8603cf37f3d404f4a3f92dd8336eee8d805a6c99c39d55d24172562d739` |
| `chpc/row19_slice_control.pbs.template` | `1be22d85a91051e7d672fb52c4f55fbf349b4365cb5d4e6158c454ce81d1f554` |
| `chpc/row19_control_compare.py` | `74956aa7b8120ebb8201086d49a9cdd8568d51fff9c5571a3dafd58cc9775dc0` |
| `chpc/row19_watch.py` | `bf11e9b21b249e10890244935c1f32ddfde7994c22375a4a9a854d12502511b4` |

Only this review is owned/edited in RSC; only the reviewer's own R052 log is
owned in Unimog. R052 retains author frontmatter, design/ledger/protocol/
manifest/implementation/dispatch. Preserve its benchmark7516261 and every
foreign edit. Source must adopt/routinely route its owning-document changes;
this record and the one authorized completion report do not silently edit
those files. Earlier row19/photo/bank reviews and their single completion
reports remain closed; the target-visible concept-batched R2 exposure remains
disclosed and is not later blind calibration.
