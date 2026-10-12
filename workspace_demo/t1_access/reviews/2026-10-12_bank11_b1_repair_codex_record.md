# Bank B1 REPAIR R1: bounded reconsideration

12 October 2026. Codex, exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`. This reviews only the repair to the
completed bank B1 second opinion, RSC `4295ed6`; it does not reopen that review.

Whole incoming `prompts/2026-10-12_codex_r052_bank11_b1_repair.txt` read at
Unimog `2e0c48789c420989252dfa3dc1bc25ce376fc9e7`, SHA256
`49a382041125353404ea2e048efd53e4c0bcff728e95717b8e577d817bbd1ee0`, and
whole updated `DESIGN_B1.md` read. Ownership committed at Unimog
`01a0ad4fcc45c7c46deecf5592ef87626ab387e5`, then incoming
`7824ccbf-9ee5-5c2c-a46d-a88dc4926347` ACK `1791792435.196147`, before edits
or delegation. Exact candidate RSC `c7138df75ab2a71c823109f79595ee56d0166e21`.

## Four verdicts

1. **Disposition/status: NOT FAVOURABLE to these exact bytes.** The original
   `b0240.json` escape is repaired. One terminal-newline filename still passes
   the promised exact inventory while being ignored by the producer verifier.
2. **Admission upgrade: NOT FAVOURABLE to adoption yet.** B1-2, B1-3 and B1-4
   are closed. Prefer route (a), the hardened schema-2 upgrade, after the shared
   inventory repair. The same helper is used by status and admission.
3. **Job-18 retry authority now: NOT FAVOURABLE.** Its resource and scientific
   identity design remain acceptable, but the exact disposition prerequisite is
   unsatisfied. No max-job-18 authority or launch permission is issued here.
4. **Unchanged manifest with existing 48-hour override: FAVOURABLE.** Retain
   manifest `d895c8a3bdf4983ad5a08868ce7a718b82f638c498ad02ea8acd848af63c0a69`
   and the existing `--walltime-h 48` option; the override itself needs no new
   scientific binding or repeated fit.

No requested status, schema-2 deployment or retry **ADOPT** literal is issued
for this package. Prior authority through job 17 is unchanged. The owner's
standing conditional go persists and can bind when a repaired exact package
receives a favourable record, without another routine go.

## One remaining bounded repair: B1-1

`row22_bank_dispo.py:42–43,119–120` uses `^b(\d{3})\.json$` with `match`.
Python's `$` can match immediately before a final newline. Consequently an extra
file named `records/b024.json\n`, beside a valid canonical rep-24 record, passes
inventory as declared rep 24. Job 11's planned-rep scan covers 240–263, so its
`b240*` through `b263*` checks do not inspect that file. Producer verification
(`row22_bank_verify.py:62–63`) and submit evidence (`row22_bank_submit.py:81–86`)
use a glob ending literally in `.json`, which omits the newline-ended alias.
The extra noncanonical evidence can therefore survive both status and admission.
This contradicts the explicit every-entry-exact-canonical inventory contract.
It does not establish a completed failed-job rep, and no actual such file or
runtime incident is alleged.

Use `fullmatch`, `\Z`, or exact reconstructed canonical-basename equality in
the inventory predicate. Add the focused terminal-newline alias negative beside
valid canonical rep 24 with job 11's planned reps empty; cover records and timing
inventory and retain the valid-inventory positive. This is a metadata repair;
no scientific fit is needed for reconsideration.

## Repairs credited

- **B1-2:** admission locates the exact receipt-bound producer verification by
  SHA256 in the gate and refuses its absence. It checks the current record hash,
  current timing contract and pinned task seed, and the later bound job's planned
  slot. The status retains and transfers the exact verification line bytes.
- **B1-3:** typed summary, bound-job and current-ledger mappings must have equal
  job sets before per-job validation. Omitting summary 11 and its output binding
  while retaining bound job 11 now holds.
- **B1-4:** explicit empty-list alarms, literal true freshness/production and
  finite non-boolean time are required. Gate age/future limits remain; the
  qualification and its embedded receipt receive the strict field checks.

Loss, no-runner-end, scoped status/timing, retrieved unchanged PBS output,
admission-failure refusal, later-completion verification, memory alarms,
uncompleted-plan partition and pilot exclusion retain their earlier guards.
If verification SCP fails but receipt publication succeeds, admission refuses
the unavailable bound verification. Confirm both transfers before refill.

## Migration and retry conditions retained

Two procedural clarifications apply to route (a). At `c7138df`, canonical
`chpc/row22_bank_submit.py` still contains the old bytes and canonical
`row22_bank_dispo.py` is absent. First promote the exact reviewed candidate bytes
into the canonical paths and commit that promotion; deploy selectively from
that promotion commit. Confirm deployed hashes and every unchanged bank pin,
including ledger `7e8f83b85a9da14497da3535faa411e8fc12a9a5733d701fba5cce73ee9ff560`.
Preserve schema-1 history and the actual job-1 qualification, archive the old
gate, adopt schema 2 bound to that qualification, and publish fresh complete
zero-alarm evidence. Remote provenance and qualification claims in this brief
are source-reported, not independently certified here.

Also, submit `--dry-run` returns before writing plan, PBS script or reservation.
It prints the proposal; separately render/check the proposed plan and request
before qsub rather than treating that dry run as those files' creation.
After favourable exact adoption, the scope is ONE job 18, reps 240–263 only,
missing and unreserved, one rep per slot, serial 24 cores, 120 GB, 48 hours,
unchanged datasets, seeds and bindings. Max job number 18 is only a number
ceiling; inspect actual coordinates/resources and retain current funding,
capacity, STOP and the cooperative programme gate.

The source snapshot gives 9,141.21 settled + 1,728 live + 1,152 reservation =
12,021.21 of the 15,000 bank cap. Failed job 11 retains its 864.76 core-hours.
Request/plan/reservation/PBS/job-start remain 172,800 seconds; the worker deadline
is 171,000 minus startup. The 1.8071 ratio to the reported completed maximum is
slack, not a tail bound, completion guarantee or restart-recovery proof. All
common programme limits and raw-bank versus numerical-target/release gates stand;
no job 19, wider campaign or new seed/target authority is granted.

## Evidence and ownership

Source reports 59/59 tests and a 07:59Z zero-alarm status run, 336/408 valid and
saved verification `2818a5f6…`; these were not rerun or live-certified by Codex.
The 22 added cases include two positives, so they are not all new negatives.
Review was static source/diff/test-source inspection, authorized fixture/hash
and deterministic metadata/resource checks, with three bounded read-only peers.
No project execution, runtime tests, fits, simulations, private/raw scientific
outputs, live operations, dispatch or job intervention occurred.

Claude R052 owns the minimal repair, tests, current docs/row 22, promotion,
migration, ledgers, gates and operations. Codex owns only this record, its R052
log appends and the sole findings handoff/lifecycle. Prior completed reviews and
reports, foreign files, source jobs, owner operating ruling and approvals remain
preserved. Reconsider only the small exact-byte repair and required regression.
