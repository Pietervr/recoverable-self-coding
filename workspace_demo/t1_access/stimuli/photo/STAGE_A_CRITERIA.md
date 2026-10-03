# Stage A (ledger row 20): declared criteria and code, revision 15 (R084, 3 October 2026)

**Specification:** framework `rsc_t1_two_channel_framework.md` §8.2, §8.4 and §8.6 (Unimog; R052's text).

**History.**

| Revision | Commit | Codex's review | Verdict |
|---|---|---|---|
| 1 | RSC `79343d9` | RSC `f9d2ef3` | NOT ON BOARD |
| 2 | RSC `e598f96` | RSC `69539bb` | NOT ON BOARD |
| 3 | RSC `a59fc2d` | RSC `081f17b` | NOT ON BOARD |
| 4 | RSC `d7a486a` | RSC `1bf9890` (combined with the AI reader) | NOT ON BOARD |
| 5 | RSC `2610d8a` | RSC `b569f8a` (combined) | NOT ON BOARD; A1, A7, A8 closed; the memory qualification accepted in principle |
| 6 | RSC `bb4f076` | RSC `c036c00` (combined) | NOT ON BOARD; kill-first, the guardian, bounded revocation and the 195-count refusal credited |
| 7 | RSC `068fe30` | RSC `12a7f20` (combined) | NOT ON BOARD; B and D closed; the ~21 GiB/s qualification (C) accepted; coverage, the 60 s closure and the missing-death branch credited |
| 8 | RSC `9f696c6` | RSC `7fdb937` (combined) | NOT ON BOARD; A2 and A3 closed; A1's timeout path credited; two A1 transitions and five summary alignments left |
| 9 | RSC `ba4fc75` | RSC `dda950b` (combined) | NOT ON BOARD; A1.1 and A1.2 closed as submitted; alignments a–d accepted; a live foreign start before the lock left |
| 10 | RSC `fbfb7db` | RSC `3390183` | FAVOURABLE; the owner's go (2 October) ran it: STOPPED by the controller race (`reviews/2026-10-02_stage_a_run.md`) |
| 11 | RSC `308901c` | RSC `5eb51a8` | NOT ON BOARD (Stage A; the reader favourable): A1 old-package admission, A2 gates hold, A3 live controls in the wait |
| 12 | RSC `620f768` | RSC `e7b31f0` | FAVOURABLE; the owner's release and go (bound at RSC `cef5e0b`) resumed it on 3 October: STOPPED at 15-native by the frozen logit criterion (`reviews/2026-10-03_stage_a_resume_run.md`) |
| 13 | RSC `22047ec` | RSC `c4bbcb5` | NOT FAVOURABLE: the criterion and the one compare accepted; the chain, carry and fixture replacement credited; R1 the prepared-link boundary, R2 declarations |
| 14 | RSC `c22cd32` | RSC `ac60eb8` | FAVOURABLE; the owner's release and go (bound at `28f1fc5`): the resume REFUSED at the gates - the machine's macOS had moved 27.0 -> 27.0.1 (`reviews/2026-10-03_stage_a_rev14_gates_refusal.md`) |
| 15 | this commit | — | answers R052's handoff `6dc8029e`: macOS 27.0 -> 27.0.1 as one declared transition difference (§R15) |

No review record of a not-favourable verdict can be named by a go: the guard's supplementary negative list holds
`f9d2ef3`, `69539bb`, `081f17b`, `1bf9890`, `b569f8a`, `c036c00`, `12a7f20`, `7fdb937`, `dda950b` (row 20; the last six combined; the list is in the reader-bound `stage_a_guard.py` and is not extended for `5eb51a8`, so the reader's favourable package stays byte-identical - the general refusal remains the absence of a positive, exactly matching attestation) and `cf3e49e`, `7048bb8`, `5a8d7ac` (AI reader). The general
rejection is the absence of a positive, exactly matching attestation.

**Not reopened** (accepted by Codex at `1bf9890`): the hashes and their relations, the shared strict guard (no schema
objection), the attestation v1 format, the inputs, cases, positional rule, transaction, statistic, engineering carry
and envelope; the sum-of-lifetime over-count as an early-stop convention; live-bound full logits and features; the two
tiny unreserved writes; the power-loss tail as an accounting rule; at `b569f8a` also A1, A7, A8, the startup and
immediate-restart repairs, the final aggregate and pre-native admission, and the memory qualification in principle.
Inputs, cases and the 178 planned attempts are byte-identical to revision 6; the plan moved to revision 7 only in its
envelope's controller constants (finalisation allowance 50 s, revocation 5 s, exit margin 5 s, close charge 60 s,
guardian setup deadline 300 s) and therefore its budget hash. Revision 8 changes no plan constant: plan, manifest
and budget are byte-identical to revision 7.

**Exposure.** Two actual runs have happened. Under the owner's go, on 2 October 2026, the revision-10 package ran the
gates and the whole instrumented phase - 158 forwards on the 20 development images - and stopped terminally before
native (`reviews/2026-10-02_stage_a_run.md`). Under the owner's release and go, on 3 October 2026, the revision-12
package resumed it: the gates, the transition, 16 native forwards (00- to 15-native), then a terminal stop at
15-native by the frozen logit criterion (`reviews/2026-10-03_stage_a_resume_run.md`); the 158 instrumented records are
unchanged. Every MECHANISM measurement below is from declared, non-development
fixtures: synthetic worker processes, the real watchdog, synthetic arrays; no model and no image
(`controller_fixtures.json`, recorded 2 October 2026 at 10:01 MST on the revision-8 code and kept as the PINNED
SAMPLING/TICK/KILL MEASUREMENTS: revisions 9 and 10 change no sampling, tick or worker-kill path; they DO change the
guardian's arming and release paths and add the foreign-start reconcile, whose evidence is the revision-9/10 tests
and the retained suite run, not that file; the §000/§00 interval, margin and A1–A3 values are from that file;
values inside the older sections are their own revision's and are marked so).

## R15. Revision 15: the machine's macOS moved 27.0 -> 27.0.1 (R052 handoff `6dc8029e`)

**What happened.** The Mac restarted unplanned on the morning of 3 October and took the macOS point update 27.0 ->
27.0.1 (build 26A434) - not the project's doing. At 16:27 UTC the revision-14 resume (owner's release and go, bound at
`28f1fc5`) was REFUSED at the gates before any forward: the execution identity's ONLY differing field was `macos`
(`reviews/2026-10-03_stage_a_rev14_gates_refusal.md`). The refused start was charged 71.5 s (2,169.5 -> 2,240.9 s of
14,400 s). TERMINAL.json and the owner's release were left unchanged and remain valid.

| # | Item | Where it lives | Fixture |
|---|---|---|---|
| 1 | The execution identity regenerated on macOS 27.0.1 | `stage_a_identity.json` (`stage_a.py identity` on this machine) | the gates worker at the resume (the real check) |
| 2 | `macos` leaves FROZEN_KEYS and becomes ONE DECLARED ENVIRONMENT DIFFERENCE, as narrowly as A1 declared its predecessors: only revision 12 declares `{"macos": ["27.0", "27.0.1"]}`; the revision-12 -> current link is admitted when every remaining frozen field is identical AND the pair is exactly 27.0 -> 27.0.1; any other value on either side refuses (revision 10 declares none). The link records `environment_differences` (field, from, to, the build string from `sw_vers`) beside the differing code files, the release, the completed ids, counters and carry. The first link (revision 10 -> 12, both 27.0) is untouched. The prepared-tail reconciliation compares the recorded difference too. `attempt_environment` derives each record's macOS from the links (completed before the declaring link: its `from`; later: the current). | `stage_a.ENVIRONMENT_KEYS`, `environment_differences`, `os_build`, `identity_transition`, `attempt_environment` | `test_stage_a_runner.Rev15Environment` (7), on a COPY of the real records, no forward: the declared pair admitted and recorded (build = `sw_vers`), link 1 byte-unchanged, counters carried, pre-native admission passes, provenance 00/15-native and the instrumented records 27.0, 16/19-native 27.0.1; refused: current macOS 27.1; a predecessor pair other than the declared one; another frozen field (machine) changed with it; revision 10's body (no declared difference); a prepared tail recorded for another OS pair (slot unchanged). Revision 13/14 classes unchanged and passing; their copies now start with no release (the live directory holds the owner's), and the stale-release case uses the kept 2 October release. |
| 3 | NO forward is added; the plan stays frozen. Natives 16-19 run on 27.0.1 and are compared with their instrumented references made on 27.0 under the unchanged rule (rel L2 <= 0.01; max(0.10, one bf16 step); identical argmax). A PASS shows parity across the path AND the OS point release; a FAIL in 16-19 is declared, prospectively, AMBIGUOUS between the OS change and the native path, settles nothing, stops Stage A, and only a reviewed control can resolve it. 15-native is re-evaluated from its committed 27.0 outputs (no forward). | the unchanged `compare`; this text | — |
| 4 | The mixed provenance wherever the result is stated | `stage_a_report`: a provenance note under the header (derived from the links: what was produced on which macOS, the refused start and its charge, the OS change not the project's doing) and a "native macOS" column in the parity table; this section; `READINESS_ROW20.md` | `Rev15Environment.test_report_states_the_mixed_provenance` (source-string scope, as revision 14's label test) |

**The question for Codex.** Is the cross-OS comparison of native 16-19 (references on 27.0, natives on 27.0.1)
acceptable as declared - a PASS read as parity across both, a FAIL as ambiguous - or must a control forward precede
them? **What a control would take** (built only if required): one NEW planned attempt, e.g. `00-native-control`,
re-running committed input 00 natively on 27.0.1 and requiring its residuals and requested logits to equal its own
27.0 native record (00-native) within the parity rule - bit-identity reported separately; it changes the frozen plan
(a declared plan difference: one attempt, one forward, inside the 200-forward cap at 191), adds a plan-revision note
and its own fixture, runs before 16-native, and a FAIL there stops Stage A as an OS-attributable difference.

## R14. Revision 14: the prepared-link boundary and the declarations of Codex `c4bbcb5`

Codex's record RSC `c4bbcb5` (NOT FAVOURABLE to revision 13 at `22047ec`) accepted the criterion and the one `compare`,
credited the chain, the counter carry and the replacement of the five old fixtures, and left R1 (one mechanism item)
and R2 (declarations), answered here through R052's handoff `ee9852d7`.

| # | Item | Where it lives | Fixture |
|---|---|---|---|
| R1 | The prepared-link write boundary | `stage_a.identity_transition` makes TWO writes in this order: (1) the next link, durable; (2) the ledger's identity slot. A death or failed write between them leaves a PREPARED TAIL (last link from the ledger's identity to the current one; ledger still on the predecessor). A later start reconciles it idempotently, completing ONLY write (2), when: the tail's from/to equal the ledger's identity and the current identity; the chain before it is unbroken and ends at the ledger's identity; the CURRENT `TERMINAL_RELEASE.json` is valid for the current TERMINAL bytes and was consumed by no earlier link (a release invalidated by a later controller failure cannot be reused - that failure needs its own release); the frozen inputs equal the predecessor's; no open or interrupted attempt; and the tail's predecessor, frozen list, differing code files, completed attempt ids, counters and carry equal the ledger's and the package's now. Otherwise it refuses. A repeat writes nothing; no third link, no reset, no recomputation. The docstring states the same. | `test_stage_a_runner.Rev14PreparedLink` (5), on a COPY of the real 3 October records, no forward: write (2) failed by injection after link 2 is durable, then the retry reconciles - slot moved, no third link, link 1, link 2 and `INSTRUMENTED_DONE.json` byte-unchanged, counters and completed ids unchanged, pre-native admission passes; a repeat of the reconciled state writes nothing (every file byte-identical); a prepared tail under a release the TERMINAL change invalidated refuses (the terminal gate, and the reconciliation's own release check) and reconciles under a NEW release; a tail whose `to` or `from` differs refuses; a tail whose counters, completed ids or frozen list differ refuses with the slot unchanged |
| R2 | Declarations | §R13 corrected in place: the two-step records 01/08/11, no rounding cause inferred, the step as the larger magnitude's binade with the 16.0 / 15.9375 boundary, "unchanged below 16, never tighter, deliberately relaxed at and above 16", the report's 0.10 guide labelled the floor and the table's columns qualified, the relabel control's actual scope; `READINESS_ROW20.md` (the copied-development-record exception to "synthetic"); the resume record's summary; the suite counts in §6 and the run record (collected / distinct / passing executions / skips by cause). | this text; `reviews/2026-10-03_stage_a_resume_run.md` (correction note) |

## R13. Revision 13: the native logit criterion and the chained transition (R052 handoff `8508993b`)

**What the 3 October records show** (`reviews/2026-10-03_stage_a_resume_run/native_diag.stdout.txt`). In all 16 native
records the marker-row residuals are bit-identical to the instrumented ones (relative L2 = 0), the merged inputs are
equal and the argmax is equal. The largest requested-logit difference is one local bfloat16 step in 13 records and
TWO steps in three: 01-, 08- and 11-native, 0.03125 at magnitudes 3.109, 3.531 and 2.266, where the step is 0.015625
(corrected in revision 14, Codex `c4bbcb5` R2). 15-native's is 0.125 at 16.5 - one step under the formula below. The
many-step differences at small logits are admitted by the unchanged 0.10 floor. The frozen absolute 0.10 is finer than
one step of the binade [16, 32); the records do not establish a rounding CAUSE (bit-identical marker residuals and an
equal argmax are what was observed, not why the logits differ).

**The step, precisely.** step(m) = 2^(floor(log2 m) − 7) is the bfloat16 spacing of the binade holding m = max(\|native\|,
\|instrumented\|) - the LARGER magnitude's binade. At a binade boundary it is coarser than the gap below: adjacent bf16
values 16.0 and 15.9375 differ by 0.0625 although step(16) = 0.125, and the fixture deliberately admits 16 vs 15.875
(two gaps of the lower binade). Nothing here claims that two unequal roundings at magnitude >= 16 must differ by at
least one step. The formula is unchanged from revision 13.

| # | Item | Where it lives | Fixture |
|---|---|---|---|
| A | The native logit criterion, per requested logit: \|native − instrumented\| ≤ max(0.10, one bfloat16 step at m), m = max(\|native\|, \|instrumented\|), step = 2^(floor(log2 m) − 7) (0 at m = 0, where 0.10 applies). The frozen 0.10 for every \|logit\| < 16; one step at and above 16 (0.125 for 16-32, 0.25 for 32-64). Relative L2 ≤ 0.01 and identical argmax unchanged. | `stage_a.bf16_step`, `logit_tolerance`, `compare` - the ONE implementation called by the native worker (`run_native`, its StopCheck via `parity_failure`) and by the final validator (`stage_a_report`, the PARITY row). The row adds the magnitude, tolerance and bf16 steps at the largest difference and at the worst logit (largest difference / tolerance), and `logit_within_tolerance`. The report's markdown table shows the largest-absolute-difference component's fields and,
from revision 14, the worst component's ratio and magnitude; the worst component's full fields are in
`stage_a_report.json` and in any failure message. The report's SVG guide line is labelled as the 0.10 FLOOR. | `test_stage_a_runner.Rev13Parity`: steps at 16.5, 16.0, just below 16, 32, 3.0, 0.3, 0, −16.5; one step at 16.5 passes; two steps fail; 0.11 at 12.0 fails; 0.0625 at 3.0 passes; 0.13 at 16.0 fails; m = 16 exactly with 0.125 passes; m just below 16 with 0.12 fails; 0.10 below 16 passes; argmax inequality and rel L2 > 0.01 fail whatever the logits; the source check that both sites call `compare` and no absolute-only test remains |
| D | The chained transition | `stage_a.PREDECESSORS`: revision 10 (`e146ec63…`, the instrumented phase) and revision 12 (`c0fb2ea0…`, RSC `620f768`, favourable at `e7b31f0`; the native records 00-15), each identity body embedded verbatim and checked to hash to it. `identity_transition` moves the ledger from whichever declared predecessor it holds, only where the recorded transitions end, under a terminal release not consumed by an earlier transition, with every frozen component identical and no open or interrupted attempt; it writes the next record (`IDENTITY_TRANSITION.2.json`; the first stays as written) before the slot moves. `admitted_phase_identity` admits a phase record whose identity reaches the current one through an unbroken chain of declared predecessors (rev 10 → rev 12 → rev 13); a broken chain admits nothing. Nothing is relabelled or recomputed; the resume re-evaluates 15-native's committed logits under A and runs 16- to 19-native and the report. | `test_stage_a_runner.Rev13Transition`, on a COPY of the REAL 3 October records (no forward): the copied state is the 3 October one; with a release, the second transition is written, counters (190 started, 189 completed, 1 failed) and completed records carried, the first transition and `INSTRUMENTED_DONE.json` byte-unchanged, the instrumented phase admitted through two links, pre-native admission passes, all 16 committed native records pass A (15-native at exactly one step, 0.125 at 16.5; under revision 12's rule only 15-native fails); without a release, and with the 2 October release (stale), no transition; changed frozen inputs, a ledger not where the chain ends, an undeclared predecessor and a broken chain refuse. The relabel control's scope,
as it is: it first asserts that the membership helper ACCEPTS the phase record relabelled to the revision-12 identity
(a declared link), then relabels it to an undeclared hash and requires full refusal - it does not prove that every
relabel is refused. `Rev12Transition` now skips: the 2 October ledger it copied was moved by the 3 October transition. |

**Rationale.** The native path emits bfloat16 logits; a tolerance below one representable step is not a fidelity test
but a demand that two roundings coincide. The rule is unchanged below 16, never tighter anywhere, and DELIBERATELY
RELAXED at and above 16 (corrected in revision 14: revision 13's "nothing refused becomes looser" was false - 15-native
was refused under revision 12 and passes here). Earlier TERMINAL outcomes remain records and need their own release.
It is a declared engineering tolerance, not a uniquely optimal fidelity threshold. Not adopted: one step at every logit
(fails most records at small logits and tests rounding, not fidelity); a relative tolerance (admits two steps at the
top of a binade and changes the rule everywhere).

**The 3 October attempt.** It stays TERMINAL in the record until the owner's `TERMINAL_RELEASE.json` names its
TERMINAL.json (which now carries the native StopCheck); then the native worker's `worker_open` performs the second
transition; 190 of 200 forwards, 2,169.5 s of 14,400 s and the storage are carried; native 16-19 (4 forwards) and the
report remain.

## R12. Revision 12: the three items of RSC `5eb51a8`

| # | Item | Where it lives | Fixture |
|---|---|---|---|
| A1 | The predecessor's completed phase admitted under a REVIEWED COMPATIBILITY TRANSITION | `stage_a.identity_transition` (called by `worker_open` before the ledger opens). The one declared predecessor is revision 10 (RSC `fbfb7db`, favourable at `3390183`), inner identity `e146ec63…`, its identity body embedded in `stage_a.py` and checked to hash to it. A transition needs the owner's `TERMINAL_RELEASE.json` naming the run's terminal record, every FROZEN component identical (plan, manifest, positions receipt, packet, package file maps, jlens, lens, dispatch, machine, macOS) and no open or interrupted attempt. It writes `IDENTITY_TRANSITION.json` (from, to, the predecessor's review, the release's sha256, every differing local code file with both hashes, the completed attempt ids, the counters and carry at the transition) BEFORE the ledger's current-identity slot moves. Nothing else changes: `INSTRUMENTED_DONE.json` keeps `e146ec63…` as its producer, no counter is reset, no output relabelled, no attempt recomputed. `admitted_phase_identity` lets pre-native admission and the final validator accept a phase record whose identity is the recorded transition's predecessor; every other predicate is unchanged. Between revision 10 and this package the forward and lens code (`image_adapter.py`, `dose.py`, `dose_report.py`, `memprobe.py`, `enforce.py`) and every frozen input are byte-identical; the differing files are named in the transition record. | `test_stage_a_runner.Rev12Transition` - on a COPY of the REAL 2 October records (158 attempts bound to `e146ec63…`, its terminal record; the originals untouched), NO forward: the transition and the full pre-native admission (all 20 plain inputs re-verified, the instrumented validator) pass with every counter and completed record carried and the producer's phase record byte-unchanged; without a release no transition and the ledger unchanged; changed frozen inputs refuse; a relabelled phase record refuses; an undeclared predecessor is refused by the ledger. (Skipped where that machine-local run is absent.) |
| A2 | A gates-phase hold is durable | `_run`: `ControllerHold` from `_gates` goes through `_hold` (reason in stops, session closed and charged, no terminal record, no report), as for work and report phases. | `test_controller.test_gates_phase_hold_is_closed_and_charged` (a blocking gates worker, an early-retiring watchdog: HELD returned, no open session, last session closed `held`, seconds charged, no terminal, worker gone) |
| A3 | The controls stay live during the watchdog-gone wait | `_sample`: the wait for a confirmed exit is no longer a sleep loop - the ordinary loop continues (memory, swap and pressure readings, phase deadline, I/O stop, iteration limit, each breach the ordinary kill-first stop); only the retired watchdog's own checks are absent; past GROUP_GONE_S without a confirmed exit the group is killed and the run HOLDS. The retired watchdog's pid leaves the sampled set. | `test_controller.test_controls_stay_live_during_the_watchdog_gone_wait` (the watchdog retires at 1 s; the worker touches 1 GiB over the lowered stop at 2.5 s, inside the 10 s wait: the ordinary memory stop fires, the worker is killed) |

**What changed, and which pinned numbers stand.** Revision 11 changed the watchdog's RETIREMENT rule (the leader's
own NOTE_EXIT, registered at arming, with the group and members gone; at arming a leader whose identity no longer
matches or is unreadable, or whose watch registration raises OSError, counts as already exited - those fallbacks
qualify "NOTE_EXIT only") and added a NEW CONTROLLER BRANCH: the bounded wait when the watchdog is gone before a
confirmed exit. That branch lies outside the revision-8 qualified envelope, so "no sampling, tick or kill path
changed" (revision 11) is withdrawn. In that branch the sampler's own readings continue (revision 12), so the
ordinary-stop interval (§00: preceding reading → kill 0.0224 s, leader 0.0288 s, extinction 0.062 s) applies to
memory stops there; the stalled-sampler interval (§00: first and third hung samples, through the watchdog's tick
check) does NOT apply, because the retired watchdog checks no tick - a sampler that stalls inside that wait is bounded
only by the guardian's deadline (disclosed residual). The pinned revision-8 `controller_fixtures.json` stands for the
ordinary stop, the blocked-I/O stop and the hung-sample paths with a live watchdog; it was not re-recorded. The
revision-10 replay of the teardown fixture (revision 11's brief) is implementer evidence, not a retained reviewer run.

**The 2 October attempt (unchanged rule, now admissible).** It stays TERMINAL in the record; it resumes only under the
owner's `TERMINAL_RELEASE.json` for that record (TERMINAL.json sha256 `7b2b8462…`) in the same output directory; the
native worker's `worker_open` performs the transition above; 174 of 200 forwards, 2,057.9 s of 14,400 and 317.5 MB
are carried; native runs on the remaining 26 forwards.

## R11. Revision 11: the 2 October execution race and the owner's terminal release

**The race (diagnosed in `reviews/2026-10-02_stage_a_run.md`).** The instrumented worker (31.0 GiB) committed
`INSTRUMENTED_DONE.json` and began its teardown; `proc_info` stopped answering for it before kqueue posted NOTE_EXIT;
the phase watchdog's retirement rule ("group and members no longer answer") retired it (exit 0); the controller saw a
retired watchdog without a confirmed leader exit and stopped terminally.

| Change | Where it lives | Fixture (`tests/test_controller.py`) |
|---|---|---|
| The watchdog retires only on the leader's CONFIRMED exit | `stage_a_watchdog.main` registers its own NOTE_EXIT watch on the leader at arming (a leader already gone, or not the recorded process, is exited); retirement needs that confirmed exit AND the group and every recorded member gone. An unanswered `proc_info` alone is a wait under the watchdog's other checks (controller death, deadline, stale beat, stale sampler), never a retirement. (Revision 11's claim that no sampling, tick or kill path changed is withdrawn in §R12.) | `test_slow_teardown_after_the_phase_record_does_not_stop` - PRODUCED: the worker commits its record, then lingers 1.5 s while the fixture watchdog's `proc_info` no longer answers for it (`tests/fixture_watchdogs.py teardown`, the real kqueue): PASS, native run, no terminal. The same fixture against the revision-10 code (`fbfb7db`) reproduces the 2 October stop exactly: STOPPED, "instrumented: watchdog exited (0)". |
| A watchdog gone before a confirmed exit HOLDS | `_sample`: the controller waits up to GROUP_GONE_S for the confirmed exit (kqueue); confirmed -> the phase ended and goes on to its independent predicates (exit code, durable record, exit peak); not confirmed -> the group is SIGKILLed and the run HOLDS (`ControllerHold` -> `_hold`: the reason in `stops`, the session closed and charged, no TERMINAL record, no report). | `test_watchdog_gone_before_a_confirmed_exit_holds` (a watchdog that exits 1 s after arming, a worker that never exits: HELD, worker gone, no terminal). Control: `test_worker_crash_and_missing_record` - a worker that dies without its record still STOPS. |
| The owner's release of a terminal record | `stage_a_guard.terminal_release`: `TERMINAL_RELEASE.json` under an exact schema (`terminal_sha256` = the sha256 of TERMINAL.json's exact bytes, owner, date YYYY-MM-DD, words, reason). With a matching release the terminal record is not active: work phases resume; TERMINAL.json stays unchanged as the record; any later failure appends to it, changes its bytes and voids the release. A malformed release refuses. The final record names the release. | `test_owner_release_of_a_terminal_record` (a native failure after the instrumented phase; a later run without a release still holds; with the release the next run resumes - the committed instrumented phase not rerun, native run, seconds carried - to PASS; a later failure voids it; a malformed date refuses) |

**The rule for the 2 October attempt (the owner's ruling, applied after Codex's record).** The attempt stays TERMINAL
in the record. Work resumes only under the owner's `TERMINAL_RELEASE.json` naming that exact record, in the same
output directory, with every counter carried and none reset: 174 of 200 row-20 forwards used, 2,057.9 s of the
14,400 s cumulative, 317.5 MB of 1 GiB. The committed instrumented records (158 attempts) are not rerun; they pass
through the native phase's pre-native admission and the final validator's full independent predicates, and the native
phase runs on the remaining 26 forwards (20 planned).

## 00000. Revision 10: a live foreign start before the lock (RSC `dda950b`)

| Path | Where it lives | Fixture (`tests/test_controller.py`) |
|---|---|---|
| A foreign start S1 published its `armed` record (or a pending entry) and is still ALIVE before the task lock when S2 recovers | The guardian's record retains the protected controller's identity (pid and start time). Holding the lock, S2 checks every unnamed start whose record names no end: if that identity is alive, S2 ends it (SIGKILL by identity), confirms the death and charges start -> confirmed end (`_end_foreign`, in `_guardian_charge` and `_failed_start_charge`); not confirmed dead within 10 s, the run HOLDS before anything is charged or removed. A dead one keeps the stated bound. The charge is therefore final only once S1 has ended; S1's later guardian record names an already-charged session and is not charged again. | `test_live_foreign_start_before_the_lock` (directory and lock stalls; S1 alive, its guardian healthy with a 300 s deadline; S2 recovers in this process: S1 ended by identity (exit −9), charged ≥ its guardian's recorded death − start; S3 adds nothing) |

## 0000. Revision 9: the two A1 transitions of RSC `7fdb937`

| Transition | Where it lives | Fixture (`tests/test_controller.py`) |
|---|---|---|
| A1.1 A healthy guardian sees an external controller death before the pending entry | The guardian now writes a durable `armed` record (session, the protected start's wall time, its setup deadline) BEFORE it reports ARMED - the controller loads nothing until then - and rewrites it at every ending of a start controller.json does not yet name: `controller_exited` (the death it observes), `released` (the controller ending before its session is durable - a refusal) or `killed` (its deadline); a normal stop of a session controller.json names writes nothing more (so no write follows the final record and its storage figure stays exact). Recovery charges every record whose session controller.json does not name, start → recorded end, as `failed_start_before_pending`, once. | `test_external_death_before_pending_with_a_healthy_guardian` (directory and lock stalls; the controller SIGKILLed from outside about 1 s after arming, long before its 300 s deadline; the guardian records `controller_exited`; the next start charges exactly death − start; no pending file existed) |
| A1.2 Recovery while the guardian is still publishing its receipt | A record that names no end - still `armed` because the post-kill write is in flight, or a readable `guardian_*.json.tmp` - is charged on the same boot until min(now, its setup deadline + 5 s), which is at least the interval to the actual death; the later receipt names an already-charged session and is not charged again. | `test_recovery_during_guardian_receipt_publication` (a fixture guardian, `tests/slow_guardian.py`, kills at the 2 s setup deadline and publishes 8 s later; recovery in that window finds `armed`, charges ≥ the measured interval to the death; after the receipt lands, ≥ death − start; a further start does not charge it again) |

Residual, stated as it is (qualified at revision 10): a start is untraceable only if its guardian never published the
`armed` record (its own write failed or stalled). The controller then waits ARM_TIMEOUT_S = 10 s, and its cleanup
before refusing waits up to 2 s for the guardian after the release message and up to 5 s after terminating it
before kill and reap: nominally 10 + 2 + 5 = 17 s, plus process start-up and signal/reap latency - none of it
charged, and done before any file operation of its own. This qualifies the residual; it is not a proof about
arbitrary OS stalls. A healthy guardian's observed death,
its release and its kill are all recorded; a death while the record is unpublished is charged to the setup deadline.

## 000. Revision 8: condition A of RSC `12a7f20` (continuous, durable failed-start/restart accounting)

| Path | Where it lives | Fixture (`tests/test_controller.py`) |
|---|---|---|
| A1. A stall before the pending entry exists (directory creation, the lock) | The guardian - started before any file operation - receives the protected start's wall time (`started_wall`, the controller process's own start) and writes it into its death record. At the next start `_charge_failed_start` charges every guardian record whose session controller.json does not name, from `started_wall` to its recorded controller death (60 s if unreadable), as `failed_start_before_pending`, once. | `test_pre_pending_stall_is_charged_at_restart` (directory and lock stalls, setup deadline 2 s: killed, no pending file; the next start charges exactly death − start, 2.021 s and 2.014 s; a further start does not charge it again) |
| A2. The deadline extension before the first durable session | The start's pending entry carries its guardian deadline; after the load, the longer deadline (the remaining row cap + 5 s) is written into that entry durably BEFORE the guardian is moved to it. A failed start is charged to its guardian's recorded death; without one, on the same boot, until min(now, that durable deadline + 5 s). | `test_long_first_persist_with_an_existing_clock` (a closed controller.json exists; the first persist blocks before its rename after the guardian moved past the 1 s setup deadline: the restart charges ≥ death − start, 11.016 s; with the death record deleted, until the durable deadline + 5 s, 11.727 s) |
| A3. A crash while reconciling an earlier failed start | `controller.starting.json` ACCUMULATES: each start reads every pending entry and writes them back with its own (only ever replaced by a superset); it is removed only after the first persist that charges all of them; entries already named in controller.json are skipped, so nothing is charged twice. | `test_two_failures_during_pending_reconciliation` (S1 pending; S2 publishes S1 + S2 and dies after its load, before its persist; S1 survives; S3 charges both, S1 40 ± 5 s) |

The floor, stated exactly: a dead OPEN session's tail is never less than 60 s; a FAILED START on the same boot is
charged its actual interval (start to recorded death, or to min(now, deadline + 5 s)), which can be less than 60 s;
after a reboot, or for an unreadable entry, 60 s. Residual: as stated in §0000 (revision 8's statement - "a start
whose guardian also died before writing its record" - omitted the healthy guardian's silent-death branch and the
receipt-publication window; both are charged since revision 9).

## 00. Revision 7: the four conditions of RSC `c036c00` (B and D closed, C accepted by `12a7f20`; A completed in §000)

| # | Condition | Where it lives | Fixtures (`tests/test_controller.py` unless named) |
|---|---|---|---|
| A | Complete controller coverage and tail charge | The guardian starts before ANY file operation (the output directory's creation included) and lives through the result's output (`run(emit=)`; `main` prints through it). A pending-start record (`controller.starting.json`) is durable before any load; the open session carries the guardian's wall-clock deadline. A dead session or failed start is charged from durable evidence only: a recorded controller death ends the tail; without one, on the same boot (`kern.boottime` earlier than the beat) the tail runs until min(now, the guardian deadline + 5 s); after a reboot the declared 60 s rule. The close charges the WHOLE bounded closure (`CLOSE_CHARGE_S` = finalisation 50 + revocation 5 + exit/output 5 = 60 s = the tail reserve) and moves the guardian's deadline to its end, so a post-close death lies inside the charged total. Diagnostics before an abort or after a kill are written by daemon threads. | `test_directory_stall_before_load_is_guarded` (killed at the shortened setup deadline; revision-7 record 2.7 s, revision-8 record 2.778 s); `test_final_output_stall_is_guarded_and_charged` (PASS admitted, output blocks, killed within the charged closure; revision-7 record 10.8 s, revision-8 11.173 s); `test_post_close_death_is_inside_the_charged_closure` (finalisation and both revocations blocked: death before the charged closure's end, not admitted; revision-7 record 9.7 s, revision-8 10.283 s); `test_crash_tail_charge` (blocked and no-evidence same-boot tails); `test_failed_start_is_charged`; `test_persistence_after_the_watchdog_retired_is_bounded` |
| B | Guardian in whole-task memory | The guardian's pid is sampled every iteration (`guardian_lifetime_max`), its final maximum read at finalisation (`guardian_final`; unreadable -> a missing mandatory measurement), both added to the phase and task aggregates. | `test_guardian_in_the_task_aggregate` (lifetime: revision-7 record 57.9 MiB, revision-8 58.4 MiB; unreadable -> STOPPED) |
| C | The timing statement | Each reading's observation instant is kept; the tick sent after a successful reading carries that reading's time (the watchdog measures staleness from it, not from consumption); the stop records the previous successful below-stop reading, the deciding reading, the kill, the leader's death and verified extinction; the watchdog records the tick's source and consumption times, its observation, group extinction and the controller's death. | `test_memory_stop_is_whole_task`, `test_never_returning_first_and_later_sample`, `test_memory_stop_with_blocked_io_kills_first` (values below) |
| D | Strict authority admission and exact recovery set | `enforce.check_ledger(..., witness_dir=out)` (controller, pre-native and final admission): authority with the intake's domains (non-blank text, try an exact positive int, never bool or float, a real calendar date, 64 lowercase hex), bound to the retained owner file (present, hashing to file_sha256, strict content equal to the authority); consumed tries exactly 1..tries-1 (1..tries for 'interrupted, recovery consumed'); exactly one outstanding entry, for the last try, on an interrupted attempt and none otherwise; no overlap. consumed_by is not required to equal the next session. | `test_stage_a_runner.ValidatorMutations.test_authority_domains_and_witness` (bool / float try, impossible dates, non-hex and wrong digests, an owner differing from the witness - each through the final and the pre-native admission route; the missing witness on the shared checker directly); `test_exact_consumed_and_outstanding_sets` (on the shared checker; the overlap and duplicate variants delete a completed entry and keep its counters - not otherwise-legal counters - and assert the particular recovery diagnostic; both admission routes call the same checker with `witness_dir`); `test_codex_unauthorised_extra_try` |

**The complete observation interval (measured; `controller_fixtures.json`, revision 8).** Endpoints and baselines are
separate:

| Path | Baseline → endpoints | Value |
|---|---|---|
| Ordinary memory stop | its preceding successful reading → kill / leader dead / verified extinction | 0.0224 / 0.0288 / 0.062 s |
| Ordinary memory stop | the deciding reading → leader dead | 0.0064 s |
| Memory stop, I/O thread blocked | the deciding iteration's observation → worker gone (timed by the test) | 0.0088 s |
| First sample never returns | the pre-GO arming tick (no successful reading precedes it) → tick consumed / watchdog observation / group extinct / controller gone | 0.0104 / 0.1586 / 0.1838 / 0.1948 s |
| Third sample never returns | its preceding successful reading → the same | 0.0054 / 0.1528 / 0.1779 / 0.1905 s |

**The conditional margin.** Stipulating the configured observation interval 0.16 s (ordinary: two readings' work
2 × 50 ms + one 20 ms sleep = 0.12 s; stalled: 150 ms tick staleness measured from the reading's own time + the
watchdog's 10 ms poll) and the pinned fixture's SIGKILL delivery 0.0273 s: 4 GiB / (0.16 + 0.0273) ≈ 21.4 GiB/s.
Measured against it: the ordinary stop's whole interval to verified extinction (0.062 s) lies inside 0.12 s; on a
stalled sample the watchdog's observation (0.1528–0.1586 s) lies inside 0.16 s and the group's extinction
(0.1779–0.1838 s) inside 0.16 + 0.0273 = 0.1873 s; the controller, killed after the group, is gone at 0.1905–0.1948 s,
up to 7.5 ms past it. On that latest endpoint, 4 GiB / 0.1948 s ≈ 20.5 GiB/s. The qualified limit is stated as about
21 GiB/s (accepted by Codex at `12a7f20` as the declared, measured local qualification). ASSUMPTIONS (stated, not
enforced): ordinary scheduling of the controller's threads and the watchdog process (no multi-second CPU starvation or
suspension); the kernel's footprint ledger current to within one reading; SIGKILL delivered within tens of
milliseconds as measured. The pinned fixture's synthetic growth rates (one thread 13.63 GiB/s fits; 2, 4 and 8
threads 32.29, 53.68 and 75.22 GiB/s do not) are finite averages that do not bound bursts or measure the frozen
model; Stage A reports the model's growth and peak, and a faster episode, an overshoot, pressure or a cap failure stops
and invalidates the qualified claim.

## 0. Revision 6: the four conditions of RSC `b569f8a` (rows 1–4 in force with §00's revocation and timing wording; the memory paragraph below is historical)

| # | Condition | Where it lives | Fixtures (`tests/test_controller.py` unless named) |
|---|---|---|---|
| 1 | Kill before any I/O wait; guard the first sample | `_sample` catches every stop and SIGKILLs the group itself (`_kill_now`) before the `finally` that disarms the tick check and joins the I/O thread, and before `_phase` persists; it records the last admissible observation (`stop_observed_mono`, the start of the deciding iteration), the kill and the leader's death (kqueue, no file I/O). The watchdog's tick check is armed by a tick written immediately BEFORE `GO`, so the first sample is guarded; after the kill the watchdog stays active (controller death, beat, deadline, group-and-member retirement) until extinction. | `test_memory_stop_with_blocked_io_kills_first` (I/O thread blocked forever; the worker gone 0.008 s after the last admissible observation, timed by the test, independent of the controller); `test_never_returning_first_and_later_sample` (sample 1 and sample 3 never return: group gone, controller killed); `test_sampler_unavailable_and_slow` (killed by the sampler itself, leader dead < 0.5 s) |
| 2 | An independent whole-controller deadline | A GUARDIAN (`stage_a_watchdog.py` in guardian mode) is started before the lock and any load, with a setup deadline (300 s), then moved to the session's cap + 5 s (at least the finalisation allowance + 5 s); on it, it SIGKILLs the controller by identity and records the death. Its path depends on no observation or persistence. The per-phase watchdog now kills the (alive) controller also on a stalled sampler. Crash charge: the guardian's and the watchdog's controller-death times; a blocked controller never seen to die is charged until the restart; the power-loss rule unchanged. | `test_persistence_after_the_watchdog_retired_is_bounded` (a controller-only persist blocks forever after the gates' watchdog retired: killed by the guardian at the shortened cap, run 18.7 s; the restart charges to that death); `test_never_returning_first_and_later_sample` |
| 3 | Bound the abort path | `_abort_exit`: revocation - an abort tombstone `STAGE_A_FINAL.ABORTED.json` naming the session, and the removal of the session's marker - runs in two threads for at most 5 s, then exit 75 whatever they did; `final_admitted` refuses a session with a tombstone. The tombstone write, when it returns, is file-, rename- and directory-fsynced; the marker's unlink is not followed by a directory fsync, so its removal's durability across a power loss is limited; if both block or fail, a marker can survive an exit 75 - reviewed as an abort, never a completed transaction. | `Finalisation.test_post_marker_stall_and_blocked_revocation_are_bounded` (the marker's write stalls after its rename: exit 75 in 10.6 s (allowance 4 s + the stall; 15.6 s with the unlink blocked), tombstone present, not admitted; the same with the unlink blocking forever: the marker survives, the tombstone refuses it) |
| 4 | The consumed recovery history | `enforce.check_ledger`: every consumed recovery an exact, typed, unique (attempt, try) entry whose authority (the owner's recovery file: attempt, session, try, owner, date, reason, file hash) names exactly it and a try the attempt has; every try of an attempt before its last must have such a recovery; outstanding interrupted entries name the last try; the open attempt's kind and session coherent. Used by pre-native admission, the final validator and the controller's final algebra. | `test_stage_a_runner.ValidatorMutations.test_codex_unauthorised_extra_try` (Codex's 195-of-200 counterexample refused in final and pre-native admission; an authority naming another try, a bool try, a missing field, a duplicate; legal with its authorised recovery); `StageA.test_crash_recovery_is_per_try_and_consumed` (the honest two-recovery history is legal) |

**HISTORICAL - the revision-6 memory statement, superseded by §00 (its 0.1 s tick check and ~22 GiB/s no longer hold;
the current statement is §00's ~21 GiB/s).** The enforced bound between two readings of a process is
0.12 s (0.16 s if the sampler stalls, through the watchdog's 0.1 s tick check and 10 ms poll); the kill is now sent by
the sampler at the decision, with no wait in between. The measured SIGKILL delivery (0.025 s kill → exit in the overshoot fixture) is evidence,
not a bound. Measured end to end with the I/O thread blocked: 0.008 s from the last admissible
observation to the worker's death. The 4 GiB headroom therefore covers growth up to about 4 GiB / (0.16 s + delivery)
≈ 22 GiB/s; one synthetic thread (11.1–14.7 GiB/s in two runs) fits, 2–8 threads (32–75 GiB/s) do not. This is the declared,
measured qualification Codex accepted in principle (RSC `b569f8a` Question 2) for this local Stage A: Stage A
reports the model's actual growth and peak; any cap, pressure or fidelity failure stops and is preserved; a faster
allocation episode or an overshoot invalidates the qualified claim and grants no Stage B authority.

## 1. The conditions A1–A8 of revision 5 (RSC `1bf9890`): where each lives

### A1 — every worker consumes and checks its own map; identity rechecked before completion

- **Gates** (`stage_a.desk_gates`): after the fresh identity equals the frozen one, the gates' own import map
  (`identity_files.gates.json`) is consumed by `check_imported_origins(map, identity.package_file_maps_sha256)`; the
  identity is rechecked (`recheck_identity`: local code, packet, plan, manifest, receipt) before GATES.json is
  committed.
- **Report** (`stage_a.run_report`): the map `worker_identity` returns is consumed and checked the same way; the
  report's `build` calls the recheck immediately before it writes `REPORT_RECEIPT.json` — a source change during
  report construction leaves no receipt, so no current report and no PASS.
- Instrumented and native: unchanged (map consumed after load, recheck before the phase record).

Fixtures (`tests/test_stage_a_runner.py`): `StageA.test_gates_consume_their_map_and_recheck` (an origins refusal and a
recheck failure each leave no GATES.json), `test_report_consumes_its_map_and_rechecks_before_the_receipt` (the map
check is called; a recheck failure leaves the report and both figures but no receipt).

### A2 — guarded startup, armed safeguard, whole-group restart

- **One cleanup owner from before the first spawn** (`stage_a_controller._phase`): the worker is spawned behind a start
  gate (a shell that execs the worker only after reading `GO` on stdin; EOF → exit 97, nothing ran); then the exit
  watch, the worker's identity (pid + start), the watchdog — given the controller's and the leader's identities — which
  must print `ARMED` within 10 s and whose identity is read, and the durable record holding both identities; only then
  is `GO` written. A failure at any step ends and reaps the gated worker, which has run nothing.
- **No phase starts while an earlier handle exists:** a leftover worker or watchdog is ended (whole group, reaped)
  first.
- **The watchdog checks its controller by identity** (pid AND start time) at arming and on every poll, and on firing
  kills, at once, every live member of the worker's group (enumerated by `memprobe.end_group`, anchored to the recorded
  leader identity) and every identity in the members file the controller keeps (escaped descendants); a stale beat or
  the hard deadline also kills the blocked controller, by identity, after the group.
- **Restart** (`_reconcile`): for each recorded worker of the crashed session, every live member of its process group
  is enumerated — not only the recorded ones — anchored to the leader's identity (XNU never reuses a pid that is still
  a process-group id; a live process holding the leader's pid with another start time means the group is extinct),
  killed with every recorded member, and confirmed gone; **only then** is the watchdog killed and confirmed gone.
  A crash between spawn and the first persist leaves an unreleased gated worker whose stdin closes with the controller
  (exit 97) and, if armed, a watchdog that kills its group on the controller's death.

Fixtures (`tests/test_controller.py`): `Startup` — exit-watch failure, watchdog spawn failure (no ARMED), first-persist
failure (each: the instrumented worker never released, ran nothing, is dead and reaped; the run STOPS), a leftover
handle ended before the report phase; `Controller.test_immediate_restart_kills_unrecorded_group_members` — a recorded
live leader with a child no record names, and a live watchdog: the child is killed, the watchdog last; the same with
the leader already exited and only the unrecorded child holding the group;
`test_stale_worker_reconciled_by_identity_only` (a recorded pid whose start differs is never signalled).

### A3 — one task aggregate, mandatory final measurements, the margin

- **By identity:** every sampled process's lifetime maximum is kept under its identity (`member_max`, pid:start); the
  leader's exit maximum, read from the exited, **unreaped** process, is folded in. The phase aggregate = Σ member maxima
  + the controller's lifetime maximum; `task_lifetime_sum` is the maximum over phases and live samples; at
  finalisation the controller samples itself again and the **task aggregate** = max over this session's workers of
  (Σ member maxima) + the controller's final lifetime maximum. A phase whose aggregate reaches the stop at the worker's
  exit stops.
- **Mandatory:** PASS requires every released worker's exit peak and the controller's final self sample; a missing
  one is listed in `missing_measurements` and the outcome is STOPPED.
- **Prompt stops:** every controller stop SIGKILLs the worker's group at once (no SIGTERM grace); the watchdog too.
- **The sampler does no file I/O:** the main thread samples (sleep 0.02 s; an iteration whose work exceeds 0.05 s
  stops) and ticks a pipe to the watchdog; a separate I/O thread persists and sums the storage. A hung sampler makes
  the watchdog kill the group (revision 5 stated no tick for 0.1 s; current: 0.15 s from the reading's own time,
  §00).

**The observation-to-death interval** — superseded in revision 6 by §0 (the sampler now kills at the decision, before
any join or persist; the first sample is guarded). Measured (`controller_fixtures.json`, revision 6):

| Measurement | Value |
|---|---|
| Largest sampling iteration's work over a full run | 5.2 ms (gates 3.2, instrumented 3.9, native 4.6, report 5.2 ms) against the 50 ms limit |
| Memory stop (whole task): last admissible observation → leader dead | 0.009 s (0.062 s to verified extinction) |
| Memory stop with the I/O thread blocked: last admissible observation → worker gone (timed by the test) | 0.008 s |
| Never-returning sample 1 / 3: watchdog observation → group gone; → controller gone | 0.033 s / 0.033 s; 0.048 s / 0.046 s |
| SIGKILL overshoot of a writer growing as fast as one thread can (killed at a 4 GiB reading) | 0.001 GiB (observed 4.122, exit peak 4.122 GiB; kill → exit 0.025 s) |
| Growth rate, one thread / 2 / 4 / 8 threads (numpy touch) | 11.1 / 32.0 / 53.1 / 66.8 GiB/s (revision 5's run: 14.7 / 36.2 / 58.1 / 75.0) |

Fixtures: `test_exit_peak_enters_the_task_aggregate` (the 1 GiB exit spike is in `member_max`, `task_lifetime_sum`
and the final aggregate, not only a side field), `test_exit_spike_over_the_stop_stops`,
`test_missing_mandatory_measurements_refuse_pass` (exit peak unreadable; controller self sample unreadable),
`test_memory_stop_is_whole_task`, `test_hung_sampler_watchdog_kills_on_stale_ticks`,
`test_sampler_unavailable_slow_and_blocked`.

### A4 — the whole-controller clock

- **From the process's start:** the session's live seconds count from the controller process's own start (libproc
  start time), before configuration, recovery and superseding.
- **Close and finalisation are charged and bounded (current, revision 7):** the close charges, at once, the whole
  bounded closure `CLOSE_CHARGE_S` = 60 s (finalisation `FINAL_ALLOWANCE_S` 50 s: receipt and ledger reads, hashing,
  scans, the final record and its marker; revocation 5 s; exit/output 5 s) and moves the guardian's deadline to its
  end; finalisation runs under a 50 s timer — past it the process ends with exit 75 after the bounded revocation. The
  storage scan precedes the close's time sample. (Revision 5 charged a single 60 s finalisation allowance.)
- **Crash charge (current: §000 and §00 A):** a dead open session's live time + a tail of at least 60 s ending at a
  recorded controller death, or on the same boot at min(now, the guardian's deadline + 5 s); failed starts as stated
  in §000. A power loss stays the declared 60 s accounting rule.
- **Lost or invalid accounting refuses:** an absent controller.json beside any existing task output; non-finite,
  negative or mistyped carry, totals, session times or beat; a total below the carry; a carry other than the declared
  one.

Fixtures: `test_crash_tail_charge` (declared, measured-longer, and blocked-never-seen-to-die tails),
`test_blocked_writer_watchdog_bounds_worker_and_controller` (group and controller killed),
`Finalisation.test_lost_and_invalid_accounting_refused` (absent record beside output; NaN, negative, wrong carry,
mistyped session), `test_post_rename_block_is_bounded_and_not_admitted`, the allowance charged in the PASS fixture.

### A5 — durable completion

`STAGE_A_FINAL.json` is written first; then, only if the output tree's size equals the declared figure (which includes
the record and its marker), `STAGE_A_FINAL.ADMITTED.json` names the final record's sha256 and session.
**`stage_a_controller.final_admitted(out)`** admits a final record only with that marker. A failure or block after the
final record's rename leaves no marker; a failure after the marker's own rename removes the marker before exit 75; a
size mismatch rewrites the record STOPPED, with no marker. Earlier finals and markers are superseded at every session
start.

Fixtures (`Finalisation`): failure before the final write; **post-rename exception** (the bytes say PASS, not
admitted, exit 75); **post-rename block** (bounded by the allowance, exit 75, not admitted); **marker failure after its
rename** (marker removed); **size mismatch** (STOPPED on disk, not admitted); `test_stale_pass_superseded`.

### A6 — legal ledger domains and full instrumented admission before native work

- **`enforce.check_ledger`** (used by the validator and the controller's final algebra): exactly four non-negative
  integer counters per row and aggregate (never bool or float); completed + failed ≤ started; passes ≥ started × the
  declared passes per try; aggregate = row 20 + row 21; every attempt with exactly kind, passes (= the declared 1),
  status (open, completed, interrupted, interrupted with recovery consumed, failed…) and tries ≥ 1; the completed map
  equal to the completed statuses; the open attempt coherent with its entry; interrupted entries and consumed
  recoveries coherent with the statuses; the row recount from tries and carry; row 21 zero in a row-20 ledger.
- **Pre-native admission:** before any native model is constructed, `admit_native` runs the complete instrumented
  validator (`stage_a_report.validate(..., phases=("instrumented",))`: ledger domains, every instrumented record and
  array under the full predicates, cross-case, 120 bitwise, suffix and encoder criteria, INSTRUMENTED_DONE).
- **Resumed records:** a committed record reloaded on resumption passes its phase's full predicates before use.
- **Predicates added:** requested ranks integers in [1, vocabulary], never bool, agreeing with the top-k and with the
  order of their logits (ties by ascending id, the capture's rule); top-k ids distinct integers in [0, vocabulary) with
  finite non-increasing logits; the final-logit dtype one of the capture's names (bfloat16, float16, float32) and the
  same on every record.

Fixtures: `ValidatorMutations.test_codex_ledger_counterexample` (all tries 0, per-try passes 1, started 16, passes 16,
completed 193, failed −177, row 21 zero, aggregate = row 20: refused), `test_coherent_zero_negative_and_typed_states`
(ten coherent or typed mutations), `test_ranks_top_k_and_logit_dtype`;
`StageA.test_consistent_nonplain_change_refused_before_native` (a non-plain `input_ids_sha256` changed with record,
ledger and phase-record hashes updated: refused, the native factory never called),
`test_resumed_record_admitted_by_the_full_predicates` (a bool rank in a reloaded record refused).

### A7 — exact report membership

The receipt must have exactly `session, package, identity, date, outputs, admissible, validator_pass`; its outputs
exactly the two SVG figures, the Markdown and the machine JSON, each matching on disk; the machine JSON's session and
flags equal to the receipt's; the session and the gates' package and identity current. The report always writes both
figures (an empty plot after a stop).

Fixtures: `Finalisation.test_report_failure_modes_prevent_pass` — machine JSON then failure, a wrong output hash,
another session, worker failure, **figures and Markdown removed with the receipt consistently trimmed**, an extra
receipt field, a receipt flag that differs from the machine report.

### A8 — declarations: provenance, source records, the audit scorer

- **Provenance snapshot vs current pin.** `manifest_dev.json`'s `execution_identity` is the **construction snapshot**
  taken when the manifest was last built (RSC `a59fc2d`): its `provenance_checks_sha256` `84abf361…` names the
  provenance record as it was then. The plan's `provenance_checks_sha256` `0085d38e…` pins the **current** record,
  revised at RSC `859262f` (revision 4) only in its `stock_matches_note` wording (a first crawl "does not establish the
  upload date or a later upload"); no check entry changed. The moved field is the plan's provenance pin (it moved the
  plan hash at revision 4); the manifest and its records for the eight Stage A inputs are unchanged and
  pinned record by record in the plan.
- **Admission policy (enforced, `stage_a.load_frozen`):** the frozen plan and manifest are the reviewed immutable
  records (both hashed in the package), and the **current** `dev_pool.json` and `provenance_checks.json` must be
  byte-identical to the plan's pins; a later change to either refuses until a new plan is reviewed.
- **Audit scorer code (a before-audit condition, not a Stage A gate):** `audit_package.py` binds the live classifier
  and normalisation source — `ai_reader_score.py`, `ai_reader_key.py`, `audit_alias_map.py` — and the map's pinned hash;
  the audit package records `audit_package.identity()` when reviewed, and `audit_package.score(..., pins=)` refuses on
  any difference. The frozen map and its construction record are unchanged.

Fixtures: `StageA.test_source_records_pinned`; `test_ai_reader.AuditMap.test_scorer_code_bound_in_the_audit_package`.

## 2. Revision 4 mechanisms still in force

The strict shared guard (`stage_a_guard.require_go`: exact key sets, typed values, commit objects, one closed block,
mandatory reviewed-commit re-derivation, descent and date order); the reviewed-package builder proving the identity–blob
relation (`stage_a.package_at_commit`); the positions receipt's three refusals; every writer's storage reservation
(work under cap − 64 MiB, finalisation under the full cap); the validator's per-record, ledger, membership, phase-record
and recomputed-criterion checks (`ValidatorMutations`, `GoAttestation`, `ReviewedPackageBuilder`, `Units`); crash
reconciliation into interrupted tries and the authorisation hold (HELD ≠ REFUSED ≠ STOPPED); the report reading the
ledger without authority; the MLX cache counted (2.0 GiB cache in a 4.222 GiB ledger; 2.222 current against 4.222
lifetime after a fall); the B prediction recomputed at finalisation; the interpretation item validated.

**Other mechanism measurements** (`controller_fixtures.json`, revision 6):

| Fixture | Result |
|---|---|
| Deadline, worker ignoring SIGTERM with a grandchild | SIGKILL at once; kill → reap 0.002 s; grandchild dead |
| Deadline, worker busy in 4096² MLX matmuls | kill → reap 0.002 s |
| Controller SIGKILLed during active work | worker and grandchild gone 0.030 s after the kill; restart reconciles, charges ≥ 60 s, PASSes |
| Controller writer blocked forever | stale beat: group gone 0.035 s and the controller 0.050 s after the observation |
| Immediate restart with an unrecorded live member (leader alive / leader exited) | every member killed, the watchdog retired last |
| Persistence failure | exit 75 in 6.1 s, first reason durable, no final record |
| Post-rename block of the final record | exit 75, not admitted, run 10.6 s (allowance set to 4 s in the fixture) |
| Whole PASS run (four synthetic workers, guardian included) | 6.0 s |

## 3. Inputs, cases, tolerances and stops

Unchanged from revision 4 (and 3, 2): relative L2 ≤ 0.01 per marker layer (FP32 in FP64, instrumented norm as
denominator), E1 logit difference ≤ 0.10 per requested logit - from revision 13 ≤ max(0.10, one bfloat16 step at
the logit's magnitude) (§R13) - identical argmax, the within-path cases bitwise equal to plain. The
envelope: 16 carried + 140 + 16 + 2 + 20 = **194 of 200**, 1,808.73 s carried; caps A 200 / 4 h / 1 GiB, task
memory 48 GiB (stop 44 GiB).

## 4. Running it (after the go only)

```
.venv-image/bin/python stimuli/photo/stage_a_controller.py run     # exit 0 PASS/STOPPED, 2 REFUSED, 4 HELD, 75 no final
```

A PASS is read only through `stage_a_controller.final_admitted(captures/photo_stage_a)`.

## 5. The attestation block (agreed by Codex at `081f17b`; unchanged)

```
<!-- STAGE-ATTESTATION v1
{"row": "20", "stage": "A", "verdict": "favourable", "reviewer": "<reviewer name and session>",
 "date": "YYYY-MM-DD", "reviewed_commit": "<40-hex RSC commit of the reviewed package>",
 "package": {"criteria_sha256": "...", "identity_sha256": "...", "plan_sha256": "...",
             "manifest_sha256": "...", "budget_sha256": "..."}}
-->
```

The go file holds exactly `review` {commit, path, record_sha256}, `owner_go` {by, date, words} and `package` (the
same five hashes). If one review approves both Stage A and the AI reader, each gets its own record with one block.

## 6. Tests (no model)

The retained-output evidence for this package is `reviews/2026-10-03_photo_suite_stage_a_rev15_run.md` (command, exit
status, counts, skips, identity, stdout/stderr); earlier records (`..._rev5_run.md` to `..._rev13_run.md`) are
historical (`..._rev14_run.md` included). Counts are stated as Codex `c4bbcb5` R2 asks: tests collected, distinct cases exercised (the main run's
collected minus cases skipped in BOTH runs), passing executions (both runs), each skip by its cause, and the build
run's repeats of main-run cases. For revision 13's record those were 293 collected, 288 distinct, 299 passing
executions, 21 skips = 16 WordNet (run in the build row) + 5 old transition cases not rerun, the build's 27 including
11 repeats; it is not "21 WordNet skips" nor "293 fully exercised".

## 7. Stated limits (not narrowed silently)

- **The memory margin** holds for growth below the rate stated in §00 (about 21 GiB/s, under its assumptions); it is
  not a guarantee against an allocator faster than that. The model's own peak and growth are Stage A measurements.
- **Descendants that leave the process group and exit between two samples** (20 ms apart in the controller) are not
  seen; one that persists after a sample is killed by its recorded identity, by the controller and by the watchdog,
  which retires only when the group AND every recorded member are gone. No Stage A worker forks a process that leaves
  its group.
- **The Σ-lifetime memory measure** over-counts processes whose peaks did not coincide; that can stop early, never
  late, for the processes it measures.
- **The 60 s charge for a power loss** is a declared accounting rule; with the machine up the unseen interval is
  measured by the watchdog and charged when longer.
- **The controller between phases** (no worker watchdog: setup, reconciliation, inter-phase persistence, the report
  checks) is bounded by the guardian (setup 300 s, then the cap + 5 s) and by its own timeouts (reconciliation 10 s per
  group, finalisation 50 s inside the 60 s charged closure: 50 + revocation 5 + exit/output 5).
- **The completion marker's commit point** is its rename; a failure of the marker's directory fsync that is followed
  by a failure (or block) of BOTH revocation steps would leave an admissible marker after exit 75 — the residual window,
  which needs filesystem failures on both; the tombstone write is directory-fsynced when it returns, the marker's unlink
  is not, so that removal's durability across a power loss is limited. Exit 75 and its stderr diagnostic are preserved and reviewed as an abort.
- **The guardian's bound is the session cap + 5 s:** a controller blocked between phases (no worker watchdog) is
  killed then, not sooner; the interval is charged until its recorded death.
- **Full logits and features** are live-bound digests, not archive-recomputed.
- **Small writes outside the reservation:** the task LOCK (under 100 bytes, before storage is configured) and a
  watchdog's record (under 1 KiB, a separate process); both fit the 64 MiB finalisation reserve.
