# v15 REVISION 14: crashed-worker slot disposition

Codex review, local 11 October / UTC 12 October 2026. Exact
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Whole incoming brief `prompts/2026-10-12_codex_r052_v15_crashed_slot_r14.txt`
at Unimog `3da3aba59576160fe4f6fcbbb0d7fd186ed91974`, SHA256
`5b08be2fb243b6f650a5afbfc6b9aaafbfdea55cb98a37ef6fa5a533979b957d`,
read; ownership committed at Unimog `08b3e39d5167614997ac54a891983d3263b58417`,
then incoming `3db11320-038f-5586-9740-fd9f518da122` ACK
`1791781354.2998981`, before review edits/delegation.

## Verdict

**NOT FAVOURABLE to adopt exact RSC `651c0c5` v15/REVISION14 yet.**
One required repair, V15-1 below, prevents the shared crash proof from satisfying
its own timing-attribution contract. No controls ADOPT literal is issued for
controls SHA256 `54e013da12862661069c69e0fdec4cb4459f47e9de117d4a7ba11174b8963da0`.
The adopted v14 disposition hold is not removed by this review. Repair the narrow
proof and return new committed bytes/controls for re-review before promotion,
deployment or progressing on v15 receipts. No fit or simulation is required.

## V15-1 — require every same-job timing to match a surviving planned coordinate

`candidate_v15/row19_screen_admit.py:1073–1081` visits `timing_scan(root, jid)`
but rejects a readable dictionary only if its slot or coordinate belongs to a
**crashed** worker. It does not require the timing to belong to any **surviving
planned** worker. Missing coordinate/slot fields, unplanned coordinates, wrong
surviving slots or a noncanonical pathname with different embedded attribution
can pass this part of the proof.

A concrete static counterexample, not an alleged incident or executed test:

1. Keep the otherwise eligible job-13 evidence: F/4, settled runner-4 certificate,
   matching plan, 23 valid surviving statuses and the matching slot-16 signal
   line. The crashed `83/2` artifacts remain absent.
2. Also retain a readable timing-only file
   `<root>/timing/rep999/t_777.json` naming `7531397.sched01`, with embedded
   `rep=999`, `index=777`, `slot=0`, and no corresponding record.
3. `timing_scan:801–816` returns that same-job file. Slot 0 is not crashed and
   `999/777` is not a crashed coordinate, so the new loop accepts it. The later
   coordinate-file checks inspect only crashed coordinates and do not find it.
4. `row19_screen_verify.py:175–199` enumerates **record** files and their paired
   timings. With no record, this orphan creates no verifier unit. Status's
   unit checks (`status:826–830`) and admission's unit attribution checks
   (`admit:1258–1263`) therefore do not catch it. Admission recomputes the same
   incomplete proof, so exact equality of the disposition does not repair this
   omission.

The result can withhold the scheduler-exit-4, runner-exit-4 and missing-status
alarms despite unexplained same-job timing evidence outside the plan. This
contradicts the declared requirement that every timing naming this job be at
a surviving coordinate. The example does not credit a fabricated completed
record; the blocker is the unsupported clean crash classification/receipt that
allows the subsequent gate to progress.

Repair the shared implementation: construct the exact surviving planned
coordinate→slot map and require every same-job timing hit to have strict,
non-boolean integer coordinate/slot fields, exact membership and slot agreement,
and the canonical timing pathname corresponding to its embedded coordinate.
Keep unreadable, temporary and unknown-attribution timings as refusals. Keep
the existing no-crashed-artifact and later-bound-completion protections.

Add focused negatives for an orphan same-job out-of-plan timing, missing/wrong
coordinate or slot fields, a wrong surviving slot, and pathname/content aliasing.
Check the shared proof and status/admission consumers: the crash disposition
must refuse and the original failure hold must remain. These are controller
metadata checks, not new scientific runs. Return updated test provenance and
exact candidate/controls hashes.

## Safeguards credited

The rest of the design has useful protections:

- `admit:1009–1068` requires refit F/4, settled runner-4 evidence, matching
  entry/plan, exactly scoped surviving statuses, one matching job-end code list
  and one eligible signal line for each missing planned worker, with no extra
  detected worker-death line. Killed/Terminated are excluded.
- The actual committed `.out.txt` shows job 13, 24 worker codes with `None` at
  slot 16 and zeros elsewhere. The `.err.txt` names that PBS ID, rep 83/index 2/
  slot 16 and Segmentation fault. These selected fixture bytes support the
  intended matching example; the live statuses/record absence were not inspected.
- `status:280–297,509–533` retrieves both files for eligible settled refit
  runner-4 jobs and checks this observation's retrieval hashes. Failure leaves
  the hold; `:729–824` retains actual 4/4 exits, charges and surviving-worker
  checks while accounting crashed coordinates as uncompleted. Other alarms,
  including memory, walltime, task binding and survivor failures, remain.
- `admit:1111–1162` reloads the current unique ledger entry, exact certificate,
  current bound plan and both current PBS-file hashes, recomputes the proof and
  requires exact disposition equality. `:1480–1489` validates this before the
  exceptional 4/4 summary; `:1359–1363` rechecks the settled certificate on
  transition.
- `admit:1253–1273` subtracts only the validated crashed coordinates, then applies
  normal survivor counts/partition/producer checks. `later_completion:873–882`
  retains current canonical artifact verification. A later legitimate completion
  is credited to its later bound producer, not to the crashed job.
- The crashed job cannot qualify a pilot (`admit:1175–1178`, `status:944–953`).
  With its artifacts absent, `83/2` is neither done nor in flight; the unchanged
  planner can re-plan it with a new job/reservation under normal caps. The old
  attempt's charge is not refunded or rewritten. No retry is launched here.

## Identity and validation limits

Working candidate bytes match committed `651c0c5`:

- status `0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b`;
- admission `67516f9ea1517fbbee9168ae4158f7f43bd01a69ab1e3de4e5f4691bc2e63ff9`;
- test `4a8399b537a03d87fcb292b6078f0d2400fda7d2541041209e0c7ab3c51abbde`;
- `.out.txt` fixture `6acfed16a3430556b2c49b6cd1f432ed689a84fcd3827daf9b8a7d564e41f9bf`;
- `.err.txt` fixture `8a222e8d4c9600a174e1cf4aa67d495655ee9b71e021d52c1832ee20d298626d`.

Controls append v15 with preserved versions 1–14; only admission/status pins
change from adopted v14. The other 12 pins, programme, partition `8d1de408…`,
resources/sub-envelope/S are unchanged. Packaging identity is favourable and
does not override V15-1.

Static test source has 51 checks: 32 shared-rule checks (four positives and
28 negatives), six status checks, twelve admission checks and one conditional
real replay. The orphan-timing counterexample is not covered. The “unattributable
timing anywhere” negative concerns unreadability rather than a readable orphan
outside the survivor plan.

The conditional real replay (`test_crashed_slot_r14.py:227–252`) uses cached
local evidence and a retained receipt/verifier; it does not pull fresh evidence.
EC2 reconciliation remains stubbed (`:162`), so this is not validation of a fresh
whole-role production watch. The individual admission checks do not execute the
full receipt/qualification/submission chain. Reported 51/51, live replay and
14/23 versus 16/23 regressions were **not run here**. The older tests' return-value
and unadopted-lineage assumptions explain limitations, not a passed full regression.
`test_pbs_settled_r13.py` still names candidate_v14; identify any temporary
repointing used for a claimed v15 regression run.

## Nonblocking precision

`crash_line_re:999–1001` matches arbitrary single-token manifest and log-root
paths. Thus “exact planned worker command” overstates path matching: rep, indices,
slot and the command form are matched, but those paths are not tied to the planned
script. Tighten or qualify that description. No independent completed-output
bypass was established from it in this review.

The memory-map diagnosis remains an operator hypothesis, not an observed cause
for the dead process. The cause note's categorical exclusion of job/node memory
exhaustion is stronger than the available observations; low aggregate RSS and
other workers surviving do not establish why this allocation failed. Keep the
inference and its limits explicit. The earlier committed scheduler extract gives
46,155,404 kB / `(120 × 1024²)` kB = 36.68%, rather than 38%; no new raw-source
verification was performed. This cause interpretation is not needed to repair
or review the disposition contract, and no mitigation/retry decision is issued.

## Ownership and retained gates

Three bounded peers and root read static source/diff/tests/contracts and selected
committed PBS fixtures; no project import/execution/runtime tests, fits/simulations,
raw scientific/private/live snapshots, SSH/AWS, source implementation edits,
adoption/deployment/activation/qualification/refill, job intervention, worktrees
or push. Foreign staged `.err` and new untracked `AGENTS.md` remain untouched.
Author owns the proof repair/tests/current docs/frontmatter/generated INDEX,
cutover/dispatch/jobs. Root owns this record, own R052 appends, sole findings and
lifecycle. The prior R13 review `1de6dc0`/accepted `dcf4e4f4` and SI
`3916eb79`/`e633edc3`/accepted `2e3f1b29` stay closed.

After a repaired exact package receives favourable review, author must preserve
adopted v14 history, promote/deploy both reviewed controller files, obtain actual
fresh whole-role evidence, and follow step 8's one existing-pilot metadata
qualification, new hash, actual-source review and matching max100 adoption.
No repeat fit, old archive/activation/benchmark replay or automatic release.
All standing USD45 Q1+Q2/actual-result production go, USD2300/3000/retries-owner,
programme100000/refit+S60000/max100/S2304/bank17/HEAL hold/STOP192/k40 and
qualification/migration/adoption/release/exposure limits carry.
