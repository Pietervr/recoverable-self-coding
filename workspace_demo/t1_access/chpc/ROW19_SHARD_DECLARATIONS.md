# Row 19, the sharded route: declarations that correct the bound files' prose (R052, 3 October 2026)

Codex's record RSC `13a2fea` (`reviews/2026-10-03_row19_sharded_route_rev2_codex_record.md`) asked for three declaration
corrections "for the next source update" and noted that a changed bound manifest gets its own hash and bindings. This
file is that update. It exists because the two files that carry the stale sentences cannot be edited inside this campaign:

- every task binding in the root (`<root>/task_<R>.json`) carries the SHA-256 of `chpc/row19_shard_manifest.json`
  (`0eae2e6f…`), and job-start and every worker HOLD on a binding that differs, so editing the manifest would stop every
  later job of this campaign at admission;
- the manifest pins `chpc/row19_shard.py` (`828d5964…`), so editing a comment in the worker changes its pin, hence the
  manifest, hence the bindings.

Both files therefore stay byte-identical for the whole campaign (pilot job `7517913.sched01` and every later job in
`/mnt/lustre/users/pvanrooyen/t1_toolchain/row19_shard`). What they say is corrected HERE; the code is what runs.

## 1. Sentences in the bound files that are not what the code does

| Where | It says | What the code does |
|---|---|---|
| manifest `storage.timing` | `<root>/timing/rep<R>.job<J>.slot<S>.jsonl` | one file per record, `<root>/timing/rep<R>/t_<iii>.json` (rep, index, identity, wall, fit seconds, peak, job, slot, host), published and fsynced BEFORE the record (`row19_shard.py` `timing_path`, `cmd_worker`) |
| manifest `shard.plan_rule` | "DONE = the record file exists" | DONE = the file is this task's VALID record of that index (`row19_shard_submit.py` `evidence`, through `row19_shard.read_record`); any other file at a record path HOLDS the planner |
| manifest `shard.gate` | the revision-2 gate (qualification file exists; a fresh zero-alarm receipt younger than 2,700 s) | the revision-3 gate, stricter: §2 |
| worker `cmd_worker`, comment "ALWAYS a status, never silence" | every worker ends with a status | every Python exception inside the guarded body ends HELD with a status. A SIGKILL (scheduler kill, node loss, the OOM killer), an import or interpreter start-up failure before the guarded body, and a failed write of the status file itself leave NO status. The protection is not the worker: a terminal job with a missing status is an alarm in `row19_shard_status.py`, and `job-end` folds a missing or unreadable status to HELD |

## 2. The gate as it is enforced from revision 3 (`row19_shard_submit.py`, `row19_shard_status.py`)

A submission after the pilot needs all of the following, each verified on the cluster at submission time:

1. `<root>/gate/qualified_job1.json`, parsed strictly (a JSON object, no NaN or Infinity), with this schema, job 1,
   production evidence, a finite time that is neither in the future nor before the pilot's recorded end, and a `bound`
   block equal to what the submitter recomputes: the manifest file's SHA-256, the root, the campaign, the manifest's code
   pins and wrapper hash, the task identities read from the root's bindings (each binding naming this manifest), and the
   pilot's PBS id, reservation token and plan-file SHA-256 from the campaign ledger and the root. Its embedded receipt
   must be the view it was written from: fresh, production, zero alarms, the same `bound`, the pilot finished in the
   scheduler (state F, exit 0 or 75), every planned worker ended 0 or 75, scheduler-accounted memory observed and under
   90% of the request, and for every dataset parity observed and equal with no rejected record and no missing timing.
2. `<root>/gate/pilot_review.json`: the operator's record (`--adopt-review <record> --max-job-number N`) that the
   reviewer's verdict on the actual pilot evidence is the review record committed in the clone, named by relative path
   and SHA-256 (verified), for exactly the qualification now in the gate (its SHA-256), up to job number N. It is never
   overwritten and is refused while the qualification does not verify. A qualification alone admits nothing.
   LIMIT: the reviewer's wording is not machine-checked. The hash binds the operator's claim to one committed record, so
   the claim can be audited; it does not prove the record says yes.
3. `<root>/gate/watch_receipt.json`: strict JSON, this schema, fresh, production, zero alarms, a finite time not in the
   future and at most 2,700 s old (`--receipt-max-age-s` can only lower the ceiling), bound to the same manifest, root,
   campaign, pins and identities and to EVERY shard job in the ledger at that moment.
4. No `STOP` file; the manifest's code pins verified in the clone the jobs run from; the wrapper's hash verified.

Receipts produced with `--no-pull`, `--pbs-file` or `--no-upload` are marked non-production, are never uploaded as a
qualification, and are refused by the gate.

The status view reconciles each worker's terminal status with its plan slot exactly: the assigned list equal to the
plan's (not a subset), new / resumed / left a partition of it, exit 0 with nothing left and exit 75 with something left,
every `new` index an accepted record whose timing names that job and slot, no `left` index carrying that job's timing;
and every accepted record's timing is traced to a ledger job whose plan assigns that index to that slot and whose status
lists it as new. A deadline exit 75 is reported per slot with the indices left.

## 3. What the retained evidence does and does not show (from the same record)

- The Lengau smoke (`chpc/results/row19_shard_parity_2026-10-03/lengau_admission_smoke_rev2.txt`) ran on the login node
  with `--no-binding-check` and another root: it shows the wrapper, the code pins, the three dataset identities and the
  deadline exit. It does not show production job-start, reservation and binding publication, packing on a compute node
  or any refit. The pilot is the first evidence of those.
- `real_parity_output_rev2.txt` is three indices of a tiny Mac dataset (32 concepts, 2,688 trials, B = 8). "Bit-equal"
  there and in the status view means the serialised scientific payload with floats by their bits; timing and checksum
  fields are excluded, and a NaN payload cannot survive JSON.
- The job output's `MemTotal` at the start and `MemAvailable` / `MemFree` at the end are two readings, not a peak or a
  time series. The memory evidence is the scheduler-accounted `resources_used.mem` and each worker's own peak. The
  4.5 GiB per-worker stop acts before a resample, after a published record and at the end, not during a fit.
- The queue limits retained on 3 October (serial: 10 running jobs, 240 cores, 40 queued, 48 h) are the scheduler's
  configuration, not a promise of concurrency; a 24-core, 120 GB request is a whole `haswell_reg` node and waits for one.
- A deadline exit (75) may leave planned indices undone; three indices per worker is a plan, not a result.
- The dry-run artifact's final "exit 0" footer is the shell's, not the refused command's; the refusal is its explicit
  REFUSED line and the absence of a campaign ledger at that time.

## 4. Wave 2, the observer repairs and the adoption scope (Codex RSC `6d8c30a`, 8 October 2026)

Record: `reviews/2026-10-08_actual_evidence_codex_record.md` (SHA-256 `465ae691…`), on exact candidate `d979365`.

- **Where the campaign stands.** 192 accepted records with 192 timings, 64 per development dataset, every one traced to
  its producing plan, job, slot and new-status. Jobs 2-4 and 6-9 each ended with 24 workers exiting 75 (one new index and
  two left per worker). Every shard job is settled; nothing is live. 408 indices remain.
- **Repair (a), FAVOURABLE.** `row19_shard_status.py` (SHA-256 `682f3c16…`) pulls each evidence directory as an ssh
  tar stream, checks both exit codes, kills both processes on timeout, refuses a failed pull and promotes the staging copy
  only after every directory succeeds. The pulls are sequential per directory, not one atomic remote snapshot.
- **Repair (b), FAVOURABLE WITH CONDITIONS.** A job is DISPOSITIONED, not alarmed, only when it is terminal AND settled,
  has no parsed or unreadable worker status, no accepted record attributed to it, no recorded runner end and no ADMISSION
  FAILED. Only the missing-status, runner-end and scheduler-exit alarms are suppressed, and only in that closed case; a
  malformed, partial, status-bearing or unsettled job alarms as before.
- **Job 5 (`7523711.sched01`).** Its workers DID start: all 24 logs carry their assignment and identity headers. The
  scheduler's SIGKILL (Exit_status 265) came before any worker terminal status or committed record. Its 0.5067 core-hour
  charge, its plan and its cause are kept; it earns no completion or recovery credit, and its indices return to the planner.
  (The commit message of `d979365` calls it a "pre-start kill"; that wording is wrong and is not repeated.)
- **Adoption scope, FAVOURABLE WITH CONDITIONS, not yet acted on.** The existing `gate/pilot_review.json` (max 9, SHA-256
  `d4edfc7f…`) is archived with its authority and the reason, recorded in row 19 and R052; a new adoption of the committed
  record against the UNCHANGED job-1 qualification (`232dd924…`) allows job numbers up to 30 (jobs 10-30: 24 cores,
  serial, 48 h, 120 GB, 1,800 s reserve; cap 24,000). The max is never edited in place; ledgers and job numbering are
  never reset. Before any dispatch a fresh zero-alarm production receipt for the whole job set (1-9, then growing) is
  published AND uploaded within 2,700 s from a successful scheduler observation. The live ledger's bound science pin
  `8cfc7b0d…` is preserved, whatever the clone's current HEAD.
- **What max 30 does and does not buy.** 17 more full 1,152 core-hour requests plus the spent total is 24,375.76, above
  the 24,000 cap; at most 16 unrefunded requests fit. The unchanged planner groups the missing indices in threes, so max 30
  may leave missing work; it is a ceiling, not a promise to finish the 600.
- **Closed at 192 of 600 (owner, 8 October 2026, ~23:5x UTC: "yes, stop the shard at 192").** The development timing
  and parity collection ends at 192 records, 64 per dataset; Codex's second opinion in `6d8c30a` and Claude's both favoured
  it, because the screen's anchors need index 0 on each development dataset, not all 600 records. A `STOP` file in the root
  (`/mnt/lustre/users/pvanrooyen/t1_toolchain/row19_shard/STOP`, written 9 Oct 00:14 UTC with the ruling) refuses every
  further submission; no shard job was queued or running. The max-9 adoption stays in the gate as it is; the max-30 scope
  above is not used, so `pilot_review.json` is not archived. The ledger (settled 4,791.76, live 0), plans, bindings and
  records are kept unchanged. What is reported from it is a partial, grouped, deadline-selected development panel: the
  per-resample timing and memory at 24 per node, and the nine overlap comparisons (indices 0, 1 and 3 per dataset) with the
  sequential slice. No complete B = 200 endpoint, tail, coverage or restart claim is made from it.
- **Queues.** 24-core jobs stay on `serial`. CHPC's Accounts Policy v2.7 sets a global per-user ceiling (240 cores,
  20 jobs, queued jobs included), so `smp` adds no capacity on present evidence; any `smp` use is a separately reviewed
  per-submission design and nothing goes to `smp` before it.
