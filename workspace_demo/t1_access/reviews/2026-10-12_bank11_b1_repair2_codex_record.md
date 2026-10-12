# Bank B1 REPAIR R2: final bounded reconsideration

12 October 2026. Codex, exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`. This reviews the narrow repair to
RSC `82b7253`; previously completed reviews remain closed.

Whole incoming `prompts/2026-10-12_codex_r052_bank11_b1_repair2.txt` read at
Unimog `86845ae98e238c53369a56936c48c179db0766d2`, SHA256
`7711127526202e5791db159dafd0fc9e7f16cf51b94add4e84365dcdca3f23fa`, and
whole updated `DESIGN_B1.md` read. Ownership committed at Unimog
`bfb666ac7a8ef9d572dda9aed3b0b02b8ee2d001`, then incoming
`300c3a2d-c129-53b8-b321-6096febe9ffb` ACK `1791793788.5319118`, before
review edits or delegation. Exact candidate RSC
`8d6339d5a1d7ee180ba0726c798cae486a60d7cc`.

## Four verdicts

1. **Disposition/status: FAVOURABLE** to the exact R2 status/helper bytes.
   B1-1 is closed; charged failed job 11 retains its loss and uncompleted plan,
   without completion, qualification or restart-recovery credit.
2. **Admission upgrade: FAVOURABLE to route (a)** with the exact submit/helper
   bytes, preserved bank pins and reviewed schema-2 migration below. B1-2/3/4
   remain closed. The procedural legacy route is not the adopted route for this
   new disposition/retry scope.
3. **One job-18 retry: FAVOURABLE**, conditional on the migration, matching
   adoption and fresh actual admission checks below. Scope is only reps 240–263,
   one per slot, serial 24 cores, 120 GB, 48 hours, unchanged scientific identities.
4. **Unchanged manifest with existing 48-hour override: FAVOURABLE.** Retain
   manifest `d895c8a3bdf4983ad5a08868ce7a718b82f638c498ad02ea8acd848af63c0a69`
   and use existing `--walltime-h 48`. No manifest amendment, new binding or
   repeated fit is required for this resource override itself.

The owner's standing conditional go binds within these scopes once their stated
operating gates hold; another routine go is unnecessary. This is prospective
authority, not a claim that promotion, migration, adoption or dispatch occurred.

## Exact operating adoption lines

```text
ADOPT row22-bank-promote revision=B1-R2 source_commit=8d6339d5a1d7ee180ba0726c798cae486a60d7cc status_sha256=1ac4b5036ca9550cdd68c711144b9673dcba626765dc58187c56b9857bb4903a submit_sha256=9665c3292cd01263be315020aac43bcc893c50574d5e69e4211cdbe931d3b8fe dispo_sha256=94f4585b4975fa95a35e1483003d1c9cfa905cfab2c81fab6a3e4d10a9fd6f1a
ADOPT row22-bank-deploy clone=rsc_bank review_schema=row22-bank-review-2 submit_sha256=9665c3292cd01263be315020aac43bcc893c50574d5e69e4211cdbe931d3b8fe dispo_sha256=94f4585b4975fa95a35e1483003d1c9cfa905cfab2c81fab6a3e4d10a9fd6f1a qualification=3c35f08608cef95c5ebe7a99134bb47ee42d1978f2383a7db4f7ca003ccbea17 max_job_number=18
ADOPT row22-bank-retry qualification=3c35f08608cef95c5ebe7a99134bb47ee42d1978f2383a7db4f7ca003ccbea17 max_job_number=18 jobs=1 job=18 reps=240-263 per_slot=1 queue=serial cores=24 mem_gb=120 walltime_s=172800 deadline_reserve_s=1800 manifest_sha256=d895c8a3bdf4983ad5a08868ce7a718b82f638c498ad02ea8acd848af63c0a69
```

These are literal operating scopes. The existing bank `adopt_review` does not
parse an ADOPT line: it binds the tracked unmodified review path/hash, actual
qualification hash and numeric ceiling. Therefore retain this committed record
and enforce the full scope procedurally as well as through the code's gates.
Max job number 18 alone does not encode one job, its coordinates or resources.
The qualification hash is the actual job-1 hash established in
`2026-10-08_actual_evidence_codex_record.md`; confirm the unchanged current gate
bytes and binding at cutover. No new pilot fit is required for migration.

## Why the remaining repair passes

`row22_bank_dispo.py:44–46,117–123` now fullmatches ASCII evidence patterns and
requires an exact reconstructed `b<rep:03d>.json` basename. Terminal-newline,
non-ASCII digit and extra-character aliases fail before attribution. Inventory
`:131–132` tests `r is None`, so rep 0 remains valid. Timing scan `:106` uses the
same canonical check; unreadable-status classification `:91` also fullmatches.
No new acceptance path or regression was found in these deltas.

The focused test source covers newline aliases in both directories, including
appearance after a clean receipt, non-ASCII rejection and a valid inventory
positive; existing clean synthetic worlds include `b000.json`. Test-source
inspection supports the intended branches. Source reports **66/66 passes** and
an **08:25Z zero-alarm view**, job 11 dispositioned, 336/408 valid, verifier
`5ee3c8e4…`; Codex did not rerun those tests or certify live evidence.

The status and submit bytes are unchanged from the reviewed R1 package. Current
record hash/timing/seed/later-slot verification, receipt-bound verifier, exact
typed job-set equality and strict clean/qualification fields retain their
credited fixes. Only helper name handling, tests and design text changed.
Charged loss, no runner end, scoped evidence, unchanged retrieved PBS output,
admission-failure refusal, memory alarms, uncompleted partition and pilot
exclusion remain. Earlier exact-byte judgments remain dated history.

## Migration and dispatch requirements

The rewritten `DESIGN_B1.md` sequence addresses both earlier clarifications:

- Promote all three reviewed files into canonical Mac paths, check each hash,
  and commit. Deploy submit/helper selectively **from that promotion commit**.
  The candidate commit's canonical paths are not a deployment substitute.
- Drain controller commands while preserving running science jobs; archive the
  schema-1 review, temporary twin and submitter history. Preserve the actual
  job-1 qualification and all plans, evidence, ledgers and numbering. Confirm
  every unchanged bank science pin, especially ledger
  `7e8f83b85a9da14497da3535faa411e8fc12a9a5733d701fba5cce73ee9ff560`;
  do not replace it with the current canonical ledger.
- Adopt this tracked record under schema 2 with max 18, bound to the exact
  qualification above. Publish a fresh complete zero-alarm whole-bank receipt
  and its exact verifier. Confirm both transfers, verifier first. A failed
  verifier copy causes admission to hold even if receipt publication succeeds.
- `--dry-run` writes no plan, PBS script or reservation. Separately render/read
  the proposed plan and PBS text using the deployed planner/request functions;
  check job 18, only reps 240–263, one per slot and the exact resources. Recheck
  missing/unreserved coordinates, funding, capacity and STOP in the cooperative
  programme window before the one real `--jobs 1 --walltime-h 48` submission.
  Retain the actual invocation/plan/PBS and execution host.

Manifest, worker, verifier and authorized PBS fixture hashes remain unchanged.
The source snapshot arithmetic is 9,141.21 settled + 1,728 live + 1,152 new =
12,021.21 of the 15,000 bank cap, with 2,978.79 headroom; failed job 11's 864.76
core-hours stay charged. Use current ledgers at admission, not this snapshot.
Request/plan/reservation/PBS/job-start remain 172,800 seconds; worker deadline is
171,000 minus startup. The 1.8071 ratio to the reported completed maximum is
slack, not a tail bound, guaranteed completion or restart-recovery evidence.

All five ledgers, common allocation/campaign limits, declared other use,
capacity, STOP, cooperative one-job/24-core/48-hour window and prior owner
qualification/release/exposure rules remain. No job 19, cap increase, wider
campaign, seed/target amendment or numerical-T authority is granted. Raw bank
permission does not release numerical inference. The owner's current CHPC
operating ruling is retained without reopening it.

## Method and responsibility

Codex and two bounded read-only peers inspected the exact helper/test/design
deltas and retained contracts. Deterministic committed-blob/SHA checks and
static AST parsing confirmed identities and unchanged functions/pins; no
project import/execution, runtime test, fit, simulation, private/raw scientific
output, live operation, deployment, adoption, dispatch or job intervention was
performed. Current remote provenance/qualification claims remain source-reported
unless established by the dated actual-pilot record; recheck them at migration.

Claude R052 owns current docs/row 22, promotion, migration, adoption, ledgers,
gates and operations. Codex owns only this record, its log appends and the sole
findings handoff/lifecycle. Foreign files, source jobs, earlier completed reports
and standing approvals/limits are preserved.
