# Row 19 sharded route — bounded Codex launch opinion

Date: 3 October 2026, Phoenix. Reviewer: exact `GPT: R052 Entropy paper`,
native `01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Incoming handoff `09d441bf-7a4a-5c40-a2fe-2f45c03f072e` was read end-to-end,
ownership committed at Unimog `bc25422d`, then manager ACK accepted before
review edits or read-only delegation. Brief: Unimog
`69c179df7ce1d68a8fe339d67d49c89044d4fa80`,
`prompts/2026-10-03_codex_r052_row19_sharded_route.txt`, SHA256
`0a072fbee0ed54dd3bff624eb810e1e412843330bef4ac4baf2803306c46758f`.

**NOT ON BOARD with the nine-job wave 1 as built at RSC
`8552e6b62f3e10793990a1e9aa1e0cdd3a1efc12`.** The exact objection is to
recovery, resource and admission evidence being reported as qualified when
the current controls can miss failures. The copied scientific procedure is
acceptable. Correct the bounded controls below, then propose one full
24-worker pilot before the other eight jobs. This opinion approves no shard
submission, including a pilot, and requests no new owner go merely to retain
the already recorded 3 October instruction and 2 October cap ruling.

The route computes independent records for the same three B200 tasks. It
does not replace C1/C2/C3, merge checkpoints, compute original fits, aggregate
an interval, read coverage or authorize stage 2. Four source-owned sequential
jobs `7516927`–`7516930` remain untouched and provide the reference/control.

The required corrections and qualification are:

1. **Make the live view fail closed on job and worker failures.**
   `row19_shard.py:278` folds a missing status into runner exit 4 correctly.
   However, `row19_shard_status.py:136` only alarms on existing worker statuses
   with exit 4; it merely prints the ledger runner exit and PBS state. A fit,
   I/O or hard-link exception can leave no worker status, job-end records 4,
   and the watcher can still return 0 with fresh/no alarms. Admission failure
   exits the PBS script before job-end and can leave no binding/status at all;
   absent bindings are silently skipped at status line93. Reconcile each
   admitted job's plan, expected slots, bindings, runner exit and fresh PBS
   state. A terminal job with missing, malformed, foreign or undeclared exits,
   or runner exit 4, must alarm. Missing statuses are expected only while their
   job is genuinely pending/running. No binding before first admission is
   different from lost binding beside admitted evidence. Retain failure
   receipts; do not release a reservation merely because status is absent.

2. **Bind resumed evidence to the requested index and hold damaged plans.**
   `read_record` at shard line113 validates the record's internal index, but
   does not require it to equal the index in the requested path. Valid index 0
   copied into `rec_001.json` is treated as index 1 resumed at lines244–245.
   The watcher detects this later, but the worker's claimed HOLD contract
   fails locally. Require internal index == requested index before reuse and
   publication. The planner at submit line25 calls any existing filename DONE
   without validation; malformed/misplaced evidence must HOLD rather than
   disappear from the missing set. A live reservation whose required plan is
   absent at submit line35 must also HOLD rather than free its indices for
   duplicate work. Keep one serialized submission owner, or serialize the
   complete planning/reservation operation; the ledger lock alone protects
   budget mutation, not a separately read task plan. Add bounded fixtures for
   these actual refusal paths, without changing canonical scientific code.

3. **Enforce the terminal memory rule and qualify the packed node.**
   Shard lines250–251 check 6 GiB only before each new resample. The last
   resample can exceed it, publish and return 0 at lines271–275; fully resumed
   workers also bypass the check. Check after durable records and at terminal
   publication, preserve evidence and report HELD on a breached peak. The
   watcher must recognize the breach. Separately, 24 individual 6 GiB limits
   permit 144 GiB, above the packed job's `mem=56gb` request. The reported
   1.3–1.5 GB peaks are unfinished sequential originals, not measured peaks
   of 24 concurrent production refits. This is an unqualified resource
   envelope, not evidence that the node will actually run out of memory.
   After the controls are corrected, the first job should run all 24 intended
   workers. Retain job/node peak memory with headroom under its filled request,
   actual packed runtimes and all 24 terminal statuses before scaling.

4. **Retain timing completeness across recovery without re-buying fits.**
   Shard lines259–265 publish/fsync a record before writing its separate timing
   row. A death between them leaves a valid record whose timing is permanently
   absent because resume skips it. Status lines113–127 summarize available rows
   without matching their indices to accepted records or checking missing,
   duplicate, malformed or nonfinite observations. Detect these gaps and make
   incomplete timing explicit; it must block an unqualified all 600 timing
   distribution or stage-2 costing. Do not recompute a valid record to invent
   its missing wall/peak observation. Atomic paired evidence is one remedy;
   conservative detection and retained incomplete-measurement diagnosis are
   sufficient for this bounded collection route.

5. **Make production parity and stop-on-alarm an actual admission condition.**
   `fresh_snapshot` at status line30 pulls only the shard root and campaign.
   `sequential_records` at line45 reads the last separate slice cache without
   refreshing it or checking its age. A fresh shard pull with stale/missing
   sequential evidence is not fresh production parity. Refresh both sources,
   validate both records against the frozen task, and label zero overlap
   PENDING. Before scaling from the corrected pilot, require current successful
   same-index overlap for all three dataset identities, using the oracle for
   rep 2 where required. A validated discrepancy remains an alarm. Submit main
   at line105 performs no watch/parity/STOP preflight: enforce a retained fresh
   zero-alarm operator admission gate or an equivalent checked gate before
   every subsequent submission. A watcher exit1 must prevent the next dispatch;
   diagnosis and any STOP clearing are recorded before resuming. STOP currently
   means `<root>/STOP`, checked at resample boundaries; it may wait many hours
   for an in-flight fit. A two-hour poll is not a two-hour execution stop.

6. **Retain the claimed admission receipt and state the actual contract.**
   Evidence commit `d06a83c048ae3c82b42a3f606c2b8f7dd121276d` contains
   `lengau_admission_and_dry_run.txt`, but its 22 lines are the nine-job planning
   output and a queue footer. It has no reps 0/1/2 environment/code/seed/identity
   admission or past-deadline exit 75 receipt. The brief reports those successes;
   this retained file does not independently substantiate them. Save the
   actual existing no-fit smoke transcript and clone/pin/identity receipts.
   The manifest's inherited `stops`, `measurements` and `not_in_this_slice`
   still describe the sequential 8GB request, checkpoint lock, original/cache,
   aggregation and request-ID acknowledgments, and exclude route B. Replace
   these with the shard's actual 56gb request, hard-link publication, timing,
   root STOP and failure boundaries. Source owns that prospective amendment.

The first packed job also serializes initial binding creation: shard
lines200–208 check-then-create shared `task_<rep>.json` through ledger
`write_atomic`, whose temp path is always `<path>.tmp`. Simultaneous first
admissions can race on it. Establish and validate all three immutable bindings
before concurrent jobs, or use a serialized/no-replace creation primitive.
Lost bindings beside prior evidence must hold. A pilot is an additional
qualification after these corrections, not a substitute for them.

Positive findings remain material. `task` and `resample_record` use the same
Config, resolved seed, data metadata, original outer folds, full stratified
draw matrix, copy grouping and fit seed `seed + 1 + index` as canonical
`analyze.refit_bootstrap.one`. The scientific/failure fields and JSON-roundtrip
checksum form match `_save`. The canonical analyze/models/simulate SHA256 pins
are unchanged. Existing correct records are skipped; the hard-link publication
fsyncs the record and containing directory and refuses replacement. None of
the objections requires changing the canonical numerical procedure.

The eight stub fixtures support all 10 mapped indices in different orders,
strict restore with 10 resumed/0 new and equal aggregate predictors. The two
worker calls in that fixture run sequentially, so they do not prove concurrent
publication/admission. The retained real-fit script/output support exact
parsed scientific-value equality on three tiny Mac resamples, indices 2,1,0,
without tolerance. They exclude timing and SHA; Python equality is not literal
IEEE bit comparison (`+0.0 == -0.0`). Qualify “bitwise” accordingly or implement
the stronger comparator if that is intended. This wording distinction does
not invalidate the copied science or demand another scientific run here.

Reservation arithmetic is sound: each full request reserves 1,152 core-hours;
nine reserve 10,368 within the separate 24,000 shard envelope. With 576 live slice
reservations, combined reservation exposure is 10,944 before settled/historical
or other allocation charges. The ledger conservatively retains killed/vanished
job reservations until scheduler settlement, checks cap equality, and prevents
repeat reservation of a shard job number. Maintain aggregate allocation usage
and the owner's recorded cap-raise procedure without resetting either ledger;
this review has not verified remaining allocation or changed the 100,000 limit.

The dry run assigns 600 indices through 201 worker slots: eight jobs have 24,
the ninth 9, while PBS reserves 216 cores. Adding the four sequential cores
gives 220 queued/running cores, not proof that 216 shard workers run concurrently.
The four sequential jobs use seriallong; the proposed shards use serial. The
brief's serial max-run 10 limit alone does not prove a global 10-job limit.
Have the operator retain fresh all-queue/global limits before launch and report
actual concurrency. If a global 10-running-jobs limit applies while all four
sequential jobs run, only six packed jobs can run at once; nine may be queued
within the applicable queue policy. No live qmgr/account check was made here.

The 46,800-second/1.25×longest dispatch rule is a disclosed planning heuristic,
not an upper bound on the next resample or a guarantee of three records/worker,
clean job-end or completion inside 48 hours. A PBS kill leaves committed records
and a full live reservation. The corrected pilot should resolve this packed
runtime uncertainty and current production parity before the other eight.

Read end-to-end: the brief, all three shard modules, ledger and eight-test source;
all manifest fields (4000 exclusion seeds checked as unchanged metadata with
no declared-seed overlap); the specified canonical resample/validation/restore
functions; the three authorized public evidence files; and relevant environment,
comparator and prior endpoint contracts. Standard-library git/blob/JSON/hash
checks showed reviewed files/evidence byte-equal to the live tree. Three read-only
peer lanes challenged science, worker recovery/resources and plan/budget/watch.
No submitted module/test/fixture, fit, simulation, remote command, PBS/account
operation or submission was executed. No private reader/plant/key/audit output
was opened. Only this review and the reviewer's R052 log/lifecycle are owned;
source retains implementation, manifest, ledger, oracle, summaries and dispatch.
Prior verdicts, exposure disclosures and one-time completion reports stay closed.
