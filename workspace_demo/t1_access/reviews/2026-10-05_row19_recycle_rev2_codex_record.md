# Row 19 recycling revision 2 — bounded Codex re-review

Date: 5 October 2026, local PDT and UTC; completed 2026-10-05T08:52:53-07:00.
Reviewer: exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Incoming `de052b0e-a833-5656-823a-c0164b7e28fe`: whole brief read;
ownership Unimog `92c4c08d` committed before ACK, review edits and delegation.
ACK accepted `1791215042.997688`; do not re-ACK.
Brief: `prompts/2026-10-05_codex_r052_row19_recycle_rev2.txt`,
Unimog `52fa7821c0f2a3284b5d55d6bd1af200f227f43f`, SHA256 `ccff9ae7b3841090c4741b6baee9251c4714296075a782736dd87ced4cd6385b`.
Predecessor record RSC `0be55479c33a18deba3aaf119a12841fce93ea54` remains closed.
Exact candidate: `5926cc3ef95c60fd41bbea87949f9e1c96637c43`;
comparison `18446d10b735126b46036f1879087744b784f8eb`. Current owning ledger read at
Unimog `52fa7821c0f2a3284b5d55d6bd1af200f227f43f`.

| Exact candidate source/evidence | SHA256 | Bytes |
|---|---|---:|
| `chpc/row19_slice_rep.pbs.template` | `e6953e46e3aac63601172cd0acc12d2945d5c7dcc1c96a73830b0e1f74542810` | 4430 |
| `chpc/row19_watch.py` | `0d1ae9dd8368822ea0212c519b52b2fcd66d418c5eb3b538b910f08ad52b1af7` | 26643 |
| `test_row19_recycle.py` | `05456ff3606fd69c1b53a7fc698d4ef67e0192c61fa26e2fc14a576631e18bc0` | 13339 |
| `reviews/2026-10-05_row19_recycle_rev2_tests.txt` | `fa119c78ea79284551706f73a64de8f8068d25f2eb6549345e2adb34041852d6` | 4128 |
| `chpc/row19_slice.py` | `c67c4c0c776d810480218f0111623481b38598b30a5c5cb68127dcc83c5dacca` | 36947 |
| `chpc/row19_slice_manifest.json` | `d1a7371ba955039a2aefbcf14fef81b79f4ecd2cbf5c86c4ed8a0be3ffbe056f` | 80306 |

**NOT FAVOURABLE to deploying exact `5926cc3` for later main attempts with
its watch as the mandatory observer.** The revision closes substantial parts of
both `0be5547` findings. Two narrow producing paths remain: an attributed final
native-crash witness can be ignored when the latest runner end is absent and PBS
is unobserved/still R; the new mandatory call-start logger can fail before
dispatch, with its failure discarded and a later clean final logger status.

These are fixes to the same process/job and logger interfaces. They need no new
fit, numerical/ledger/manifest amendment or replacement scientific control.
The owner's C2/C3 drop and the amended-report limits in `0be5547` stand unchanged.

## Reviewed system and evidence

The filled template invokes the unchanged runner with `--segment 1`: one new
resample at most per fresh foreground process, restoring the same original cache
and strict checkpoint under the same scientific task, PBS job and reservation.
It repeats only after exit 75 and positive progress. Runner exit, checkpoint/
watermark semantics, full request admission, one live reservation and actual PBS
settlement remain unchanged. No loop call creates a new submission or reservation.
Running attempt-2 jobs retain their old filled scripts; this review concerns
later attempts plus the repaired Mac watch, not a change to running jobs.

Whole incoming brief, exact template/watch/fixture, scoped diff and retained
synthetic log were read. Three reused read-only peers examined watch, logger and
retained-evidence paths. Metadata checks independently verified the six declared
hashes and unchanged runner/manifest/ledger/submit/analyze blobs. Exact candidate
commit changes four paths: template, watch, fixture and retained log. The full
range from `18446d1` also contains the intervening completed `0be5547` review and
source tracker updates; those are not new producing code changes.

This is static source and retained synthetic evidence review. No submitted
imports, functions, tests, shell harnesses, fakes, fits, simulations, providers,
actual result/key/image/human artifacts, SSH/PBS, account or remote/job operations
were executed or opened. Root's `/tmp` helpers used stdlib Git/hash/JSON only.
Source job outcomes/operations in the owning ledger are declarations, not remote
observations independently made here. References below are exact candidate lines
relative to `workspace_demo/t1_access/`.

## Repairs credited

1. **Terminal grammar is repaired.** The template's final witness returns to
   `exit <rc> tee <tee> job <id> end <ISO>`; call count is on a preceding separate
   line (`chpc/row19_slice_rep.pbs.template:53–54`). It matches the unchanged
   watch regex and job-attributed parser (`chpc/row19_watch.py:38`, `148–156`).
   The old deterministic appended-calls parsing failure is closed.
2. **Ordinary active-call/gap lifecycle is repaired.** Attributed call-start
   markers (`template:42`) feed `call_starts` (`watch:159–168`). End/start
   chronology prevents a previous exit 75 from making a newer active process
   done (`180–181`). Without a final witness, PBS R admits the inter-call gap;
   unobserved mode admits only a bounded gap (`187–190`), and an expired
   unobserved gap alarms (`287–290`). `running` again follows job lifecycle
   (`354`), preserving first-record/stall/stop-ack checks (`387–409`). The
   progress baseline uses the first call and this job's own validated timings
   rather than restarting the whole-job clock for each process (`390–391`).
3. **Observed PBS end/native failure is repaired.** Gone/F/E invokes job end
   and missing-latest-process diagnosis, with a stale prior exit identified as
   such (`watch:284–286`). Recycling end/logger obligations apply even when a
   runner exit is absent (`296–307`). A clean matching final process/witness
   can end cleanly; nonzero/unknown logger evidence and unknown/failed PBS
   observation still alarm. Old-template jobs keep their prior behavior.
4. **Runner-stream/capture failures are preserved.** The three pipeline
   statuses are captured together (`template:43–44`). The first failing live
   tee or capture tee is retained (`45–46`) and stops recycling before another
   call (`48–50`), even if progress remains parsable. Failed `mktemp` sets
   `tee_rc=1` before dispatch (`41`). No later runner call overwrites those
   statuses. The final parser reads the retained tee status; no broad logging
   redesign is required.

The candidate retains the pinned numerical identity and existing task bindings.
The older manifest-pinned `9e7edbc` ledger start/end behavior is the same relevant
behavior already examined in `0be5547`; the declared untouched `rsc_slice`
runtime is not a new local-versus-pinned mismatch blocker. Watch/template repairs
can remain outside those pinned sources. Remote runtime bytes were not checked.

## Remaining finding 1: final job witness is not authoritative when the process never ends

`lifecycle` reads the job-attributed final witness as `found` (`watch:184`) but
uses it only to prevent `between` (`187`). Its actual end predicate is:

`job_ended = pbs_ended or (process_done and not between)` (`190`).

When `process_done` is false and PBS is not gone/F/E, the job's own final witness
does not invoke end obligations. A concrete valid later-call trace is:

1. Call 1 ends 75. The unchanged ledger retains its end and exit. Call 2 records
   a newer start under the same job/token, retaining those previous end fields.
2. Call 2 dies natively before Python's `finally`, so no latest runner end is
   written. The foreground pipeline returns 139. The template stops on non-75
   and writes `exit 139 tee 0 job <same id> end <time>` (`43–44`, `49`, `53–56`).
3. A fresh snapshot now contains the newer start, stale exit 75 and attributed
   final 139 line. `--qstat` is optional (`watch:198`); default observation is
   `-` (`269`), or PBS may still be R while the wrapper/scheduler finishes.
4. Old end precedes the newer start, so `process_done=False` (`181`); neither
   `-` nor R is a PBS end (`185`). `job_ended=False` despite `found=True` (`190`).
5. The PBS-end native diagnosis (`284`) and final exit/logger checks (`296`)
   are skipped. The watch calls the ended job `running call 2` and keeps live
   checks (`277–279`, `354`). If previous validated progress is recent, no stop
   is pending and other evidence passes, it returns 0/no alarms (`418–421`).

A later stall alarm does not substitute for reading the explicit crash evidence
already present. The same class covers a first-call native failure with no
runner exit. The template announces the call before invocation; if native failure
occurs before runner start in imports, the bound reservation can still look
queued/not started, and live health checks need not run. This is one predicate
gap, not a separate blocker or an observed failure claimed for source jobs.

Make an attributed job-final witness invoke whole-job end and terminal/logger/
native obligations independently of latest process-end fields and scheduler
observation. Missing latest runner end plus a native final exit must alarm under
default unobserved mode and PBS R as well as F/E/gone. Check logger failure too;
do not treat a stale prior exit as the final process exit. Keep current gap/active
logic when no final witness exists. No need to make qstat mandatory or redesign
the ledger, clock or scientific runtime.

The new fixture's native-crash case explicitly supplies PBS F
(`test_row19_recycle.py:190–194`). Unobserved/active cases have no final witness,
and final/logger cases retain PBS F. It therefore does not test this remaining
final-witness route. Add retained offline cases with the same native final line
under `-` and R, both stale prior exit and no runner exit/start, and nonzero
terminal logger evidence; each must alarm while clean active/gap cases remain.

## Remaining finding 2: failure of the mandatory call-start logger is discarded

The new attributed marker supplies lifecycle evidence and the first-call clock.
Its publication is `echo ... | tee -a $LOG` (`template:42`). That pipeline's
status is not inspected, and line 43 always dispatches the runner.

Concrete producing path: `mktemp` succeeds; the marker tee cannot append the call
line and returns nonzero; its status is discarded. The runner's live/capture
tees then succeed, so both retained pipeline logger values are zero. A later
call's marker and output are logged normally; ordinary completion writes final
`tee 0`. The watch reads whichever markers survived (`watch:159–168`), without
requiring the first/contiguous markers or checking total-call count. Its final
parser/logger predicate can accept that final stream as complete despite the
known earlier failure to publish mandatory lifecycle evidence (`148–156`,
`296–307`). Before another marker survives, the gap can also be misclassified
as old-template behavior and alarm conservatively. No lost charge, scientific
wrong result or actual source-job logger failure is claimed.

Capture marker publication status immediately; preserve failure in the sticky
logger field, remove the unused capture tempfile and stop before dispatch, or
provide an equally enforceable fail-closed flow. The final evidence must retain
the failed marker write. Add a fixture that fails the marker publication itself,
asserts no runner dispatch and nonzero final logger evidence. This is confined
to the newly required lifecycle marker; it adds no broad preexisting auxiliary-
logging/self-reporting gate or scientific test.

The existing tee-failure fixture targets runner pipelines correctly: before the
call-2 marker, `FAKE_STATE` is still 1; the fake runner increments it to 2 before
the live tee checks after consuming input (`test_row19_recycle.py:90–110`). Thus
`FAIL_LIVE_AT=2` tests call-2 stream failure, not this earlier marker publication.

## Retained tests and their exact limits

The named log `reviews/2026-10-05_row19_recycle_rev2_tests.txt` is 4128 bytes,
66 lines, with run label `2026-10-05T15:36:37Z`. Six module totals are
17/5/11/5/11/4: **53 OK events, 53 distinct named source tests, no repeated,
failed, error or skip events in this log.** Names and totals match the inspected
definitions. It records all four recycling tests, including the two new methods;
the earlier 51-pass unretained claim is not another run to add. This review read
and counted the retained evidence; it did not independently reproduce execution.

The new logger method extracts the actual loop and connects its resulting log
to real watch `terminal_evidence`/`call_starts`. It asserts a clean three-call
final line/markers, live tee failure at calls 1 and 2, and capture failure at
call 1, with no later call and retained nonzero final tee. The wrapped tee passes
input before returning failure, so it directly tests parsable progress despite
failure. It does not inject marker or `mktemp` failure. Failure cases assert
call stop/logger evidence, not every native runner return code.

The new watch method invokes the real runner once with stub fits under one
reservation, copies its evidence into a private synthetic snapshot, then calls
real `W.main` while editing ledger clocks/exits and writing synthetic call/final
lines. It crosses ordinary gap/active/expired-gap/stall/stop and observed-F native/
final/logger predicates. It does not execute a real second runner process or
ask PBS. Its edited call-2 start predates the retained call-1 announcement, so
that chronology is a constructed predicate case, not a physically faithful
two-call trace. The `--stall-h 0` assertion shows the check runs, not a measured
threshold proof that a later process cannot reset the clock. Source reading
supports the first-call baseline change independently.

The earlier scientific equality fixture still compares eight selected fields
over six indices using deterministic stub fits and same-interpreter calls.
The shell fake still ignores argv; static flags remain correct. No actual
fresh-process JAX fit parity, long-runtime remedy, producer/compute-node memory
cause or measured recovery/output admission follows from these 53 synthetic
events. These limits do not require another fit merely to close the two producing
integration branches.

## Preserved conditions and disposition

The 24-hour outer threshold is dispatch headroom, not proof against a PBS cut;
per-process runner deadlines reset, and full requested walltime remains the
reservation's admission value. The crash mechanism remains a hypothesis. Both
qualifications from `0be5547` carry; neither is added as a new deployment blocker.

Owner 5 October drops C2/C3. No replacement is imposed for an honest amended
execution/recovery report; original control remains unqualified, declared actual
parity is pre-crash indices 0/1 only, and newly computed post-resume parity is
not established. Actual pilot evidence, the other eight held shard jobs, coverage,
Stage 2/reference/cost/go and paid/cloud gates remain separate closed/open scopes.
Source attempt-2 jobs `7520111`, `7520953`, `7521637` and their filled scripts
are preserved. Root performed no monitoring/restart/resubmit/settlement/account
operation; HEAL1922 test success is source metadata, not new authority.

For reconsideration, submit the narrow final-witness and call-start logger
repairs with retained offline cases for those exact missing branches, keeping
the credited active/gap/terminal/health and stream/capture behavior. Source owns
implementation/current summaries/ledger/dispatch; root owns only this record,
its R052 append, committed findings adoption and lifecycle. One completion report
and accepted adoption finish this assignment; await a concrete revised package
or new explicit assignment. Foreign files, running source jobs, old approvals,
exposure disclosures and completed review/report identities are preserved.
