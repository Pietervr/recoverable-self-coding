# Bank REVISION B1 candidate: closed-no-record disposition of bank job 11, and the retry of reps 240-263

R052, 12 October 2026. Status: CANDIDATE, not adopted, not deployed. Nothing here changes a running job, a ledger, a gate
file or the bank clone on Lengau.

## Trigger

Bank job 11, `7531003.sched01`, ran on `cnode0359` with reps 240-263, one per slot. On 12 Oct at 07:23Z PBS killed it at its
36 h wall: F, `Exit_status 271`, walltime 36:01:54, cput 857:07 (all 24 cores busy), mem 29.3 GB. None of the 24 workers wrote
a status, timing or record. Every slot log and the PBS output stop at the start/"admitted" lines; there is no crash line.
The bank receipt was published first, then the job was settled at 864.76 core-h through `programme_gate`, giving bank spent
9,141.21, live 1,728 (jobs 16 and 17) and cap 15,000. Since then every bank receipt carries 26 alarms on job 11: bad exit, no
runner end, and 24 slots without a status. Without a disposition the bank can never again produce a zero-alarm receipt.

This is the same class of failure as refit job 3 (`7527352`, `cnode0358`, 9 Oct), and the same mechanism.
`row22_bank.py:257-286` checks the deadline only before a fit (need = max(86,400, 1.25 x longest)). With one rep per slot,
`longest` is 0 at that check, so the fit always starts, and nothing can stop it before PBS does.

**Node evidence.** The 14 completed bank jobs ran from 23:42:51 to 26:17:09 (median about 24:40). On `cnode0359` all 24 fits
were still running at the 35.5 h worker deadline, so every one of them was at least 1.35x slower than the slowest fit on any
other node. The refit job 3 fits on `cnode0358` were all at least 1.21x slower than the others. Two adjacent nodes have each
slowed a whole job, which is consistent with a node effect. Reps 240-263 have never run anywhere else, so a dataset effect is
not excluded. The 9 Oct brief claimed that a 1.21x slowdown would leave a bank job inside 36 h. That claim was wrong for this
node.

## The disposition (port of the refit REVISION 8 design, Codex RSC a86debe verdict 1)

`row22_bank_dispo.closed_no_record` is one implementation, imported by both sides:

- **Status view** (`row22_bank_status.py`, Mac): the fresh observation also retrieves `<toolchain>/jobs/row22_bank_<n>.out`
  of every settled bank entry that has no runner end, and records its rc, ok flag and SHA-256 in `jobs/_fetch.json`. The
  disposition holds only when all of these are true:
  - the observation is state F with an integer exit, and the settlement note carries the same `Exit_status`;
  - the ledger entry is SETTLED with charge, time and note, and has no runner-end field;
  - the plan carries this entry's token and job number;
  - no status file is scoped to the PBS id (by name, in any planned or unplanned slot, or by a parsed `job`), and no
    unreadable status file is present without a job in its name;
  - no timing file names the PBS id, and none is unreadable or temporary; nor does any timing in the verify document;
  - no planned rep has a temporary record or timing file, and any record or timing at a planned rep is a LATER bound bank
    job's planned completion that the producer runtime verified (current record bytes = verified bytes);
  - the retrieved output is unchanged since retrieval, names `job <PBS id>` and contains no `ADMISSION FAILED`.

  When it holds, only the bad-exit, missing-runner-end and missing-worker-status alarms are suppressed. Memory alarms and
  every other check stand. The summary keeps exit 271 and zero ended/new/resumed/left, and carries `disposition` (the
  settlement certificate, the plan SHA-256, the output SHA-256, and the 24 reps uncompleted with origin "plan") and
  `partition`. The receipt binds the output in `bound.job_outputs`. A dispositioned job never qualifies.
- **Admission** (`row22_bank_submit.py`, login node): every receipt disposition is recomputed from the CURRENT ledger, the
  live root and the PBS output on disk, and must be exactly equal to the recomputation: settlement certificate, exit,
  token, PBS id, plan SHA-256, output SHA-256 and uncompleted reps. The output must be bound and the summary must show zero
  work with the plan's reps uncompleted. A terminal job with a bad exit and no disposition refuses, and so does a stray
  output binding.

**Actual evidence** (candidate status run, read-only, separate live and receipt directories, nothing published,
12 Oct 07:34Z):
fresh snapshot, valid records 336/408, verify `919c24d41921`. Bank job 11 reads "PBS F exit 271, workers ended 0/24,
DISPOSITIONED closed-no-record: exit 271, charged 864.76 core-h, 24 reps uncompleted (origin plan), output f5f1f988cf3d".
Jobs 1-10 and 12-15 are F exit 0 with 24/24; jobs 16 and 17 are running. **No alarms.** The output SHA-256
`f5f1f988cf3d0b4fe2e0c5d8d5f36a8c8f6550a938ee42f8dd9c478a4264fedb` is the fixture `fixture_bank11/row22_bank_11.out.txt`.

**Tests**: `python3 chpc/candidate_bank_r1/test_bank_closed_no_record.py` reports 37/37 ALL OK. The cases are listed in its
docstring. Among them:
- the unsettled kill holds;
- a runner end holds;
- each kind of scoped or unreadable status and timing holds;
- a record without a later bound completion holds;
- every way the output can fail (not retrieved, changed, ADMISSION FAILED, not naming the job) holds;
- a note exit that differs from the observed exit holds;
- a bound job-18 retry completes the reps without lifting the disposition, while an unbound or wrong-slot retry holds;
- the memory alarm survives a disposition;
- seven admission refusals;
- the planner puts 240-263 into job 18.

## A deployment fact the reviewer must weigh

The bank clone on Lengau (`rsc_bank`, HEAD `012f3f3`) runs the **c1ce93e** submitter (SHA-256 `31685d01…`,
`REVIEW_SCHEMA row22-bank-review-1`). Its gate checks only STOP, seeds, the adopted review's path/hash and max job number.
The hardened Mac submitter (`ac8209f`, `88fd335e…`: qualification, review-2 and the fresh zero-alarm receipt in code) was
never reviewed for the bank clone and never deployed there. Codex's 6 Oct note says it is "outside prior exact c1ce93e review".
Bank jobs 2-17 were admitted under c1ce93e, with the receipt condition kept as an operating rule (refill only from a fresh
zero-alarm receipt) rather than in code. The admission half of this candidate is built on the `ac8209f` bytes.

## Proposals for the reviewer

1. **Status B1** as above: adopt, then promote the bytes to `chpc/` on the Mac. The status view runs only on the Mac.
2. **Admission**: (a) preferred: deploy `ac8209f` + B1 (`row22_bank_submit.py` + `row22_bank_dispo.py`) to `rsc_bank` as a
   reviewed upgrade, so the receipt gate and the disposition recheck are enforced in code. This re-adopts the review under
   schema 2, bound to the existing `qualified_bank_job1.json`. Or (b): keep c1ce93e and the procedural receipt rule. Under
   (b) the disposition recheck exists only in the status view.
3. **Retry of reps 240-263**: once fresh evidence still shows them missing and unreserved, retry them first as bank job 18,
   with the same datasets, seeds and bindings (the planner does this unchanged, because a settled entry is never in flight).
   The requested resource is serial, 24 cores, **48 h** (the serial maximum in CHPC policy v2.8) and 120 GB through the
   existing `--walltime-h 48` option. The manifest is unchanged, and the plan, PBS request, reservation and job-start
   `--walltime-s` all carry 172,800 s. The worker deadline becomes 171,000 s, which is 1.81x the 94,629 s (26:17:09) of the slowest
   completed bank job. That reduces the exposure but does not guarantee completion.
   Reservation: 1,152 core-h, so 9,141.21 + 1,728 + 1,152 = 12,021.21 ≤ 15,000. Scope: the adopted review covers job numbers
   up to 17, so job 18 needs a reviewed scope of **max job number 18** for this retry. It would be adopted by retiring
   `gate/bank_review.json` by hand (the documented route, recorded in row 22) and adopting the new record.
   **Node**: no host exclusion is proposed (Codex 9 Oct: one excluded node does not address another), but the retry's
   exec_host is recorded. If it lands on cnode0358 or cnode0359, that is reported before the result is interpreted.
4. The loss stays: 864.76 core-h is charged, job 11 gets no completion or recovery credit, the job number is consumed, and
   the plan, the output and the settlement are kept.

## REPAIR R1 (Codex RSC 4295ed6: four bounded evidence-gate repairs)

- **B1-1, strict inventory** (`row22_bank_dispo.inventory_problem`). Every entry under `records/` and `timing/` must be
  exactly `b<rrr>.json` (three digits) of a declared rep. Anything else holds the disposition and is never mapped onto
  another rep: `b0240.json`, an undeclared rep, a directory, a dot-file, a temporary file.
- **B1-2, later completion checked on current bytes.** The status view now keeps the verify document's exact bytes
  (the line whose SHA-256 is `bound.verify_sha256`). With `--publish-receipt` it copies them to `gate/verify_<stamp>.json`
  before the receipt. The admission finds that document in the gate by SHA-256, and without it refuses. It then requires
  the verified record's `file_sha256` to equal the current record bytes. It also applies the producer's timing contract
  (`row22_bank_verify.timing_check`: rep, task seed via the pinned `row22_bank.SH.task`, finite non-negative
  wall_s/fit_seconds/maxrss/t, job string, integer slot) to the current timing bytes. A later completion is never
  accepted without a verify document; the status view holds as well.
- **B1-3, one job set** (`dispositions_problem`). The receipt's summaries, `bound.jobs`, `bound.job_outputs` and the
  current ledger's bank jobs must all be typed mappings, and the summaries, the bound jobs and the ledger's jobs must be
  equal sets, before any job is validated.
- **B1-4, strict clean fields** (`clean_receipt_fields`). Both the gate receipt and the qualification's embedded receipt
  need `alarms` to be an explicit empty list, `fresh` and `production` exactly true, and a finite non-boolean `time`. The
  gate receipt must also fall inside the past/future bounds. The qualification itself needs a finite time.

**Tests:** 59/59 ALL OK. The 22 new cases are each of Codex's traces as a negative: b0240 beside a valid canonical rep 24;
the timing changed to wall_s -1 or to another seed after a clean receipt; changed record bytes; a bound verification
missing from the gate; job 11's summary and output binding removed; malformed alarms and time. The unchanged verified
job-18 completion is the positive case.

**Actual run of the repaired bytes** (read-only, separate directories, nothing published, 12 Oct 07:59Z): fresh snapshot,
336/408 valid, verify `2818a5f6…` (the saved file hashes to exactly that value). Job 11 is DISPOSITIONED (exit 271,
864.76 core-h, 24 reps uncompleted, output `f5f1f988…`), with **no alarms**.

## Route (a): the migration, with the evidence collected so far

Read on Lengau, 12 Oct ~08:00Z:
- **Clone `rsc_bank`:** HEAD `012f3f3`. It runs the c1ce93e submitter `31685d01…` (`REVIEW_SCHEMA row22-bank-review-1`).
  Its pinned `row19_ledger.py` is `7e8f83b8…`, which is the manifest pin and not the current canonical `9a779702…`. That
  ledger provides `reserve(kind, rep, cores, walltime_s, root, note)` and `bind(token, job_id)`, the API the candidate
  submitter uses. The pinned `row22_bank.py` is `2f98db3e…`.
- **Gate:** `bank_review.json` (schema 1, record `reviews/2026-10-08_actual_evidence_codex_record.md` `465ae691…`, max 17),
  its stale `bank_review.json.tmp.31370` (identical 258 bytes, left over from the hard-link adoption), and
  `qualified_bank_job1.json` `3c35f086…`.
- **Qualification:** schema 1, job 1, production true, finite time. Its embedded receipt passes the strict B1-4 fields.
  It binds job 1 = `7523732.sched01`, token `d3cf375f72da`, plan `d62408a6…`.

Steps after a favourable record (no science job is touched):
1. Drain: no bank submitter or status run in flight; jobs 16 and 17 keep running.
2. Archive `gate/bank_review.json`, its `.tmp` twin and the schema-1 submitter bytes under `gate/archive_schema1_<date>/`,
   and record it in row 22. The old record and the job-1 qualification stay where they are, unchanged.
3. Selective copy into `rsc_bank` by `git checkout <reviewed commit> -- ` of exactly these files: `chpc/row22_bank_submit.py`
   and `chpc/row22_bank_dispo.py`, plus the Codex record(s). Then confirm that every pinned manifest file (ledger
   `7e8f83b8`, `row22_bank.py`, `row19_shard.py`, …) still hashes to its pin. No bulk copy of `chpc/`.
4. Promote the status bytes on the Mac (`chpc/row22_bank_status.py`, `chpc/row22_bank_dispo.py`).
5. Re-adopt under schema 2 with `--adopt-review <B1 record> --max-job-number 18`. This binds to the existing
   qualification SHA `3c35f086…`, which `adopt_review` re-checks.
6. Publish a fresh complete bank receipt with zero alarms. The verify document goes first, then the receipt.
7. Run the job-18 dry run and check the actual plan, PBS script and invocation: job 18, reps 240–263 only, one per slot,
   serial, 24 cores, 120 GB, `--walltime-h 48` (172,800 s in plan/reservation/PBS/job-start). Each rep must be missing and
   unreserved. Recheck funding, capacity and STOP inside the cooperative `programme_gate` window. Only then submit, as one
   job, and record its exec_host.
