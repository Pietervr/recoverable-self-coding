# Row 20 Stage A — revision 12 Codex record

Date: 2 October 2026, America/Phoenix. Reviewer: Codex, exact session
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Accepted handoff: `bbf061d9-370e-5383-ace4-20d5441cd092`; ownership committed
in Unimog `73d31d4a` before manager acknowledgment and review work.
Brief: Unimog `05c72fc868761c8fad8f3fba76e041f896f872f8`,
`prompts/2026-10-02_codex_r052_rev12_stage_a_review.txt`, SHA256
`3e4e5e41749959787089b9812352493bbaaede749c10f3c1513aa229f7e0e75e`.

**FAVOURABLE for the exact Stage A package at
`620f76823a7d875aaa15d71244a59670ae33199c`. A1–A3 in the revision-11 record
at `5eb51a8753882d3a470eea44f931a77a3ebfe530` are closed within the declared
local Stage A scope. No further implementation condition is imposed here.**

This qualifies the package and the declared compatibility transition. It does
not establish Stage A PASS, native parity, fidelity, reader qualification
outcome, or Stage B authority. The owner's dated, exactly bound go and terminal
release remain separate admission requirements. The existing terminal is not
released, the go is not rebound, and no run is dispatched by this review.
Prior owner go/release intent, attempts, counters and exposure remain intact.

All source references below are immutable candidate blobs under
`workspace_demo/t1_access/stimuli/photo/`, unless another commit is named.
The three questions are answered below; the attestation is at the end.

## 1. A1: the old producer and counters are preserved

The declared predecessor is revision 10 at
`fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030`, with producer identity
`e146ec63bc32973bb217de6066b57fe1c972bf8cf79a369b19d8efca617b2f38`.
The embedded identity body independently equals that committed predecessor
body and hashes to this value. Comparing the complete old/current identity
bodies, only the local-code map changes; frozen inputs, snapshot pins,
Python/package versions, lens, dispatch and machine metadata are identical
for this exact pair. Immutable diffs show `image_adapter.py`, `dose.py`,
`dose_report.py`, `memprobe.py` and `enforce.py` unchanged from revision 10.
No forward or external weight loading was used to establish these comparisons.

`stage_a.py:683–719` requires a matching terminal release, the declared frozen
fields and no open/interrupted attempt. It writes `IDENTITY_TRANSITION.json`
before changing only the row-20 ledger identity slot. The receipt names both
identities, predecessor review, release-file hash, code differences with old/new
hashes, completed IDs, counters and carry. Existing completed records, attempts,
counter values and producer phase record are neither reset nor relabelled.
The unchanged `Budget` still refuses an undeclared predecessor.

This works on the actual controller path: existing instrumented completion is
skipped (`stage_a_controller.py:572–577`), desk gates reconcile interrupted work
without opening a current-identity `Budget`, and native worker admission performs
the transition before opening the ledger (`stage_a.py:730–738`). It then verifies
current execution identity and runs complete pre-native admission before model
construction (`1093–1100`). The instrumented and final validators use the same
old/current producer-identity alternative (`stage_a_report.py:361–364`). All
other membership, legal-domain, counter/cap, output-map, archive/hash/shape/dtype,
bitwise, suffix and encoder predicates remain required. This is a narrowly
declared identity exception, not a general permission to reuse another package.

The producing `Rev12Transition` fixture (`tests/test_stage_a_runner.py:984–1058`)
copies the machine-local 2 October output tree to a temporary tree. Its positive
case calls `worker_open(..., "native")` and full `admit_native`, checks carried
counters/completed entries and receipt IDs, keeps the old producer phase bytes
identical, and admits all 20 planned plain inputs without a forward. The four
controls exercise absent release, a changed plan pin, an undeclared phase label
and an undeclared ledger predecessor. Retained stderr explicitly marks all five
cases OK, not skipped. This closes A1's required no-forward transition evidence.

The evidence is copied-record admission, not a new native run or final PASS.
The copied input tree is not among the ten retained suite files; I did not open
either the original or copied captures, arrays or scientific output. The phase
relabel control uses an undeclared hash, not every possible coherent forgery.
There is no retained receipt/state-write crash fixture or full real-controller
continuation through native and final validation. Receipt-before-slot atomic
ordering supports normal recovery: an unchanged old slot can recheck and retry;
loss of the receipt after the slot has moved refuses old-phase admission.

Two declaration limits apply without adding a gate to this exact package.
`FROZEN_KEYS` lists its explicit comparison fields; it omits snapshot and
environment fields, which are independently equal in this pair and covered by
current runtime/exact-package admission. Receipt consumption (`674–680`) checks
from/to and the declared predecessor; it does not independently reauthenticate
every receipt field. Acceptance therefore assumes the retained transition
artifact is unchanged. Do not describe either mechanism as a generic freeze of
every future package field or an independently authenticated receipt on every
read. These are provenance limits, not a demonstrated normal-path counter reset
or predicate bypass in the submitted transition.

## 2. A2/A3: closure and ordinary live controls are restored

**A2 is closed.** `_run` catches a gates `ControllerHold` (`controller:561–565`)
and calls `_hold`. The held reason is recorded, `_close("held")` durably charges
the live duration and existing 60-second closure allowance, closes the session
and clears `open_session`, and the result is HELD. Cleanup ends the worker before
that closure; this route dispatches no report and creates no terminal.
The existing CLI mapping remains exit 4.

The fresh-directory producing fixture (`tests/test_controller.py:665–683`)
starts a blocking gates worker with a watchdog that really retires early. It
requires HELD, a closed/charged held session, no open session, no terminal and a
dead worker. The retained suite records it OK. It does not separately assert
report-file absence or exercise the CLI mapping; those follow from source rather
than those fixture assertions. Existing process-observation, signal and storage
residuals remain as previously qualified.

**A3's ordinary blind-wait defect is closed.** The inner sleep loop is removed
(`controller:1192–1263`). While waiting after watchdog loss, ordinary iterations
still check leader exit, I/O stop and phase deadline, sample task memory, apply
scheduled swap/pressure checks and the iteration-work limit, and take the
ordinary kill-first stop on a breach. The gone watchdog leaves the sampled set;
its failed pipe does not prevent the other controls. With no breach or confirmed
exit by the wait limit, the group is ended before a held session closes.

The new producing fixture (`tests/test_controller.py:685–703`) uses a watchdog
retiring at one second and a worker touching/retaining one GiB at 2.5 seconds,
over a lowered 768-MiB stop inside the ten-second wait. It requires the memory
STOPPED reason and a dead worker, rather than HELD when the wait expires. The
retained log reports it OK and a 1,026,591,288-byte reading over 805,306,368 bytes.
The saved previous-reading-to-kill interval is 0.028602 seconds; the deciding
iteration-to-kill interval is 0.002276 seconds. These are implementer observations,
not new reviewer measurements. The fixture's loose wall-time assertion and
printed kill timing do not establish a new worker-extinction endpoint.

The revised declaration correctly withdraws the blanket claim that no sampling,
tick or kill path changed and describes the retirement rule with its arming
fallbacks. Read the unchanged revision-8 figures 0.0224/0.0288/0.062 seconds as
historical observations and a same-path engineering reference for ordinary stops,
not exact revision-12 post-watchdog maxima. Their live-watchdog stalled-sampler
qualification does not extend to a retired watchdog.

The compound residual needs precise wording: if the watchdog is already gone and
the sampler then never returns, ordinary checks and the wait timer cannot advance.
The guardian bounds and kills the **controller only** (`stage_a_watchdog.py:109–165`),
not the phase group. Surviving-worker termination can depend on finite worker
completion, restart reconciliation or separate action. Neither the earlier
approximately 21-GiB/s tick-assisted margin nor prompt whole-task extinction is
established in that branch. This accepted local compound-failure residual adds no
universal OS guarantee or new scientific/blanket rerun condition. Owning summaries
must carry this qualification when quoting the memory margin or guardian bound.

## 3. Exact package, retained evidence and disposition

Independent standard-library git/blob/hash/JSON/AST arithmetic reproduced all five
attested fields and the inner identity
`c0fb2ea0f6c5ef83cdabd414cb7d761ec3aabd9de13ed6022a852a7b590da001`.
No submitted package helper, module, function, import, test, fixture or CLI was
executed by this review. Read-only peers checked transition, control and metadata
lanes. References were read as documents/source, not just matching keywords.

Retained evidence is
`2ba76a94ef788452336f1580eccd31d6c9e587c5`,
`reviews/2026-10-02_photo_suite_rev12_run.md` and its ten-file directory.
All declared byte lengths/hashes match; `head.txt` pins the exact candidate and
photo status is empty. Main stderr reports 269 tests in 2075.122 seconds,
OK with five WordNet skips, both stored exits zero; those exact five tests
separately pass under the build environment in 0.659 seconds. Thus 269 distinct
cases are exercised overall, not 274. Controller has 39 cases and transition
five; the seven new producing cases are explicitly OK. This is retained
implementer evidence, not a reviewer rerun or proof of every failure combination.

The corrected development-exposure declaration preserves the actual 2 October
revision-10 run. Process-mechanism measurements are synthetic; the new transition
fixture uses copied previous development records, so do not call every fixture
synthetic/nondevelopment. No new forward is involved in that fixture. Old-code
teardown replay remains attributed implementer evidence. The pre-commit STOPPED
observation and unidentified failure remain disclosed with cause unresolved;
the later passing suite does not resolve their cause.

The reader is not re-reviewed. Its sixteen bound blobs and 24 fields remain equal
to the revision-11 favourable package, digest
`6be7d4c8fc6b113f4505af166386f8cf3df23446ccfe19df61114bb5d2e4b760`;
the existing record at `5eb51a8` stands within its scope. Reader owner-envelope,
archiving, go and dispatch actions belong to the owner/source. This record emits
one Stage A attestation only. The positive matching guard remains required even
though the reader-bound guard's supplementary negative list was not extended.

Source retains implementation, captures, framework, ledger, protocol, go files
and dispatch. I changed only this review. No image was opened or named; no key
contents, real captures/arrays/journals/answers, private audit/human/pull output,
model/forward, fit/simulation, remote/HPC/cloud/account operation, worktree or
push was used. Prior text/bank/row-19 reviews and exposure limitations remain
separate; earlier completion reports must not be resent.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A",
  "verdict": "favourable",
  "reviewer": "Codex (GPT: R052 Entropy paper; native 01a0d19e-2127-7051-9a61-6db771088559)",
  "date": "2026-10-02",
  "reviewed_commit": "620f76823a7d875aaa15d71244a59670ae33199c",
  "package": {
    "criteria_sha256": "4e80b9590461dccbada956e82a413dbd46832c885cbdf6dc33ad87b8439e0870",
    "identity_sha256": "1a01d070da0c18fa871a0e252c9a8c9d98df9df250be10300181fa8696569664",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f"
  }
}
-->
