# Row 20 Stage A revision 11 — Codex review

Date: 2 October 2026. Reviewer: Codex, **GPT: R052 Entropy paper**,
native `01a0d19e-2127-7051-9a61-6db771088559`.
Candidate: **`308901c825ca2fcc28c716e22ff83973e68cb2b1`**.
Prior favourable revision-10 records: `339018303643d44bbeab087cf2d891553af7dd56`,
candidate `fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030`.
Assignment: Unimog `prompts/2026-10-02_codex_r052_rev11_both_packages_review.txt`
at `5b50c45445236e7864f035815c41479e476d1700`, SHA256
`4945baf5af8bd838e6063ed66c96088f77d90baf3f4955aac91cd4f269359ad0`.
Handoff `6ff60a4a-b4e0-5f06-945a-3631b5211189` was accepted after committed ownership.

## Verdict and scope

**NOT FAVOURABLE for the submitted Stage A resume package.** Three bounded
implementation conditions remain below. No favourable Stage A attestation is issued.
The owner's 2 October go and terminal-release intent are preserved; this review
does not release the terminal, rebind a go, resume a worker or authorize new work.
The separate reader judgment is in `2026-10-02_rev11_ai_reader_codex_record.md`.

Stage A is the local fidelity/resource screen, now proposed to reuse the completed
instrumented phase of the stopped revision-10 run and spend 20 native forwards
within the remaining 26. Source-reported totals remain 174/200 forwards,
2,057.9/14,400 seconds and 317.5 MB/1 GiB. The reported instrumented-phase task
peak of 31 GiB and whole-session charged duration of 249.2 seconds (including
the 60-second closure charge) are execution metadata, not a fidelity result. No actual
capture, saved scientific array or reader answer was inspected here.

Read/reason only: immutable source, full relevant declarations, prior reviews,
public execution summary, fixture source and retained textual suite evidence;
standard-library git/JSON/AST/hash arithmetic and independent read-only peers.
No submitted module, function, import, test, fixture or CLI was executed; no
forward, image opening or naming, model, scientific/remote/job/account operation,
worktree or push occurred. Source retains implementation, stimuli, captures,
framework, ledger, protocol, go files and dispatch.

## Question 1 — repair, producing evidence and exact remaining list

The normally armed watchdog now registers the leader's own kqueue exit watch,
latches NOTE_EXIT, and retires only with that exit plus group/member extinction
(`stimuli/photo/stage_a_watchdog.py:183–217`). A later unanswered process probe
alone no longer retires that ordinary path; deadline, stale beat/tick and
controller-death checks remain. Initial nonmatching/unavailable identity and
watch-registration OSError are explicit arming fallbacks (`188–191`), so the
literal phrase “NOTE_EXIT only” must be read with those qualifications.

The teardown fixture (`tests/test_controller.py:630–641`;
`tests/fixture_watchdogs.py:23–44`) produces the intended race: the fake worker
commits its phase marker and lingers 1.5 seconds; watchdog process probes are
suppressed for that leader while kqueue stays real. The retained suite reports
PASS, native executed and no terminal. The separate revision-10 replay reported
in the brief is implementer evidence, not an independently retained/replayed
old-code run by this reviewer. Its causal explanation agrees with the source.

The release helper (`stage_a_guard.py:137–164`) correctly binds an exact terminal
byte hash and owner/date/words/reason, keeps the terminal record and makes a later
append void the release. The report names the release. Its fixture (`controller
tests:598–628`) produces a native failure, unreleased refusal, released same-package
resume without rerunning instrumented work, carried seconds, later voiding and
malformed-date refusal. This is useful evidence of **terminal authority**, but
does not establish the proposed old-package data transition in A1.

| ID | Concrete surviving path | Required bounded repair/evidence |
|---|---|---|
| A1 | A valid terminal release does not admit the completed revision-10 instrumented phase under revision 11's changed identity. | Declare and implement a reviewed compatibility transition that preserves the old producer identity, every counter and all existing pre-native/final predicates; produce a no-forward old-package-to-new-package resume fixture. |
| A2 | A watchdog retirement during the gates phase raises `ControllerHold` outside the handlers that close and charge HELD sessions. | Handle this gates path through the same durable hold/close/charge operation; produce a blocking-gates early-retirement fixture that checks the returned HELD result and closed clock. |
| A3 | The new watchdog-gone wait suspends ordinary live memory/system sampling and ignores phase deadline/I/O-stop changes for up to 10 seconds while the worker can remain live. | Keep the declared controls active during the bounded wait, or end the live worker when those controls cannot be maintained; produce a no-model fixture that exercises the wait with a breached control. |

**A1 detail.** Revision 10's inner identity was
`e146ec63bc32973bb217de6066b57fe1c972bf8cf79a369b19d8efca617b2f38`;
revision 11's is
`fb4abaa10d5a34d7648df7f59e0b58676c2a695addd8af9a4de8fcb98ea8ad16`.
The public `2026-10-02_stage_a_run.md` at `66c64ca` identifies the completed
158-attempt phase as bound to the revision-10 package. `worker_open` reads the
current identity before opening the existing state (`stage_a.py:564–578`), and
`Budget` refuses a different saved row-20 identity (`enforce.py:350–373`). Even
bypassing that refusal would not suffice: `admit_native` requires the completed
phase's identity to equal the current budget identity (`stage_a.py:865–895`),
and the final validator enforces state and phase identities (`stage_a_report.py:
254,349–362`). Neither the release helper nor desk reconciliation migrates them.
The controller skipping an existing done marker is not scientific admission.
The release fixture uses one candidate throughout with fake workers/report; it
does not bind and carry revision-10 real-producer metadata into revision 11.
Do not silently relabel the old outputs, reset their counters or recompute 158
forwards within the remaining 26. This is a provenance/admission repair, not a
request for a new fidelity or calibration campaign.

**A2 detail.** `_run` calls `_gates` at `stage_a_controller.py:560–564`, before
the work/report `ControllerHold` handlers at `574–581`; `_gates:708–729` catches
only `ControllerStop`. A blocking gated worker plus the supplied early-retiring
watchdog reaches the same `ControllerHold` at `1216–1217`. `_sample` kills the
worker and `_phase` ends/persists it before rethrowing (`1115–1127,1250–1256`),
but `run` then only releases the lock/stops the guardian (`514–521`). It does
not call `_hold`/`_close`; the durable session remains open and the CLI raises
instead of returning HELD with its session closed and charged. A future recovery
can reconcile it; that does not meet the declared immediate HELD transition.
The retained hold fixture blocks only instrumented work (`tests:644–663`).

**A3 detail.** `controller:1206–1217` adds an inner sleep/exit-only loop for
`GROUP_GONE_S`, presently 10 seconds. During it the controller does not execute
its normal memory/pressure/swap readings, phase-deadline or `io_stop` checks
(`1199–1205,1218–1249`); the retired phase watchdog supplies no backup tick
control. The whole-run guardian still bounds total duration, and I/O may still
set a stop flag, but neither maintains these omitted live controls. This is a
concrete new branch outside the previously qualified sampled-memory envelope,
not an arbitrary OS-stall objection. The hold fixture shortens the wait to three
seconds and checks killing/closure, without breaching a control during that wait.
Thus the declaration “no sampling, tick or kill path changed” needs correction;
the pinned revision-8 numeric fixture cannot alone cover this new branch.

The existing crash-without-record control still reports STOPPED. Its continued
coverage and the successful teardown/release fixtures are credited; they do not
cover A1–A3. No other Stage A gate is imposed by this record.

## Questions 2–4 — separate reader, identity and authority

Questions 2 and 3 are answered in the separate favourable reader record: the
vanished-entry repair is sound, and an owner-authorized fresh job under its own
envelope uses the existing mechanism with fresh state and retained old evidence.
It does not authorize continuation past the closed first receipt.

For question 4, the Stage A package fields are reproduced as metadata, **not a
favourable attestation**:

| Field | SHA256 |
|---|---|
| criteria_sha256 | `4279dc848c07fb24ad4e022ed99d2414b89f00c561545aa4b6f06e8ed37dcdac` |
| identity_sha256 | `7abf9ee88cf5634524cd3ded9f3799eca98c576bbedb6c8efc19a02cc28f1827` |
| plan_sha256 | `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc` |
| manifest_sha256 | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| budget_sha256 | `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f` |

Retained suite `7d7cbd4`: exact candidate HEAD, clean photo status, main exit 0,
262 tests in 2,080.421 seconds, five WordNet skips with those five passed
separately in 0.660 seconds. That means 257 non-skipped main checks plus the five
separate checks, not 267 distinct tests. Controller has 37 collected tests.
This is retained implementer evidence, not a reviewer test run or proof of every
transition. The earlier disclosure remains one identified STOPPED observation
and one unidentified failure, cause unresolved; passing later runs does not
resolve that cause, and the two diagnosed 2 October races are separate events.

Correct the stale absolute “No forward has run on any development image” in
criteria line 35/readiness line 3 to distinguish synthetic mechanism checks from
the reported actual run. This is truthful exposure wording, not a new scientific
gate. Any bound-file edit moves the package and needs its new exact identity.
The three implementation conditions above, owner release/go and full admission
remain separate from any empirical Stage A success or Stage B authorization.
