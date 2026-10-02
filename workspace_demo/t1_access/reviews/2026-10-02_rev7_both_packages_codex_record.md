# R052: Stage A and AI-reader revision-7 exact-package review

2 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.

**Verdict: NOT ON BOARD with Stage A execution or AI-reader qualification calls at
RSC `068fe300c1972b89a25967914c848a00513d1d23`.** This is the single negative
record permitted by the brief; it contains no favourable attestation. Stage A
has one remaining control condition, A, plus declaration alignment. Reader A–C
remain partly open; D is closed. The conditional approximately 21 GiB/s memory
qualification and the test-only assertion fix/module rerun are accepted in the
scope below. The owner's Stage A gate question remains open, with no adopted
exception or go. The reader's pre-call review and dated owner-go requirements
remain in force.

## Scope and retained evidence

Read the full Unimog brief
`prompts/2026-10-02_codex_r052_rev7_both_packages_review.txt` at
`bea961674aca1047bb88b4c97579ee631b6b93ea`, SHA256
`bc577b259dab920776398230f1d94954768b482589fbddd223e7b7d2acf1ee08`.
Own review/log ownership was committed at Unimog `66825963`, then handoff
`62c4e44f-903d-59fa-9d77-85ba742f07a4` was acknowledged and registry-accepted
before review edits. Compare the completed revision-6 record RSC
`c036c00dcb1ccbc4dbb0364e07065926ad93ff5f`; earlier assignments are not restarted.

Stage A tests 20 frozen inputs against the same-weight native reference: 160
mandatory forwards, 18 planned diagnostics and 16 carried engineering attempts,
194 of 200, with 1,808.73 seconds carried. It produces fidelity/resource evidence.
The reader retains 300 items in two views, 600 planned responses, at most 660
attempts and six hours; the grayscale admission panel is still 63 easy items,
requiring at least 61 correct. Neither package supplies Stage B authority.

Read the pinned criteria/readiness, controller/watchdog, memory and ledger/guard,
worker/report; reader design/job, executor/runtime/journal/scorer; affected tests,
fake drivers and frozen metadata; owning framework §§8.2/8.4 and ledger row 20.
Three independent static helpers checked control, validation and reader paths.
References below are exact-package line numbers relative to
`workspace_demo/t1_access/stimuli/photo/`. No submitted module, program, test,
fixture or CLI was imported or executed. Git blobs, AST literals, byte hashes and
deterministic metadata arithmetic were used. No image was opened or named, model
called, forward/capture/fit/simulation launched, account operated, worktree created
or push performed. R052 owns framework/ledger/protocol/dispatch; R084 owns
implementation; Codex owns this review and its own work-item log.

All five Stage A hashes, inner execution identity, source/import-map/receipt
relations and the reader's 24-field identity were independently reproduced from
the committed blobs and retained binary/manifest/sandbox bytes, using the saved
CLI version without executing it. From revision 6 to 7, the plan changes only
revision, envelope/controller constants and budget hash; its inputs, cases,
attempts, tolerances and source pins are unchanged. Manifest, reader set/key/
delivery, delivery order and all 600 user-text hashes are byte-identical. The
earlier accepted scientific population, key/specificity, provenance, isolation,
smoke, native admission and report conditions remain closed.

The retained suite record `reviews/2026-10-02_photo_suite_rev7_run.md` and all 17
main/supplement files were read from RSC `ed7f2ff`; main-record sizes and hashes
match the blobs, including empty stdout/status files. Main HEAD is exactly
`068fe300…`, photo status clean, 15:15:29–15:41:01 UTC. Its output shows **236 tests
in 1529.797 s, one failure, five WordNet skips, exit 1**. The separate build run
shows **five WordNet tests in 0.656 s, OK, exit 0**. The five are full-form S1,
inflections, key rebuild, specificity and synonym residue.

The one failure is the revision-6 slow-receipt/slow-close assertion expecting
`not closed on this receipt`; the process still exits 75 with a durable COMPLETE
that is refused, now first by `no closure marker`. The full diff from the exact
package to `f3ae67848a97c2ff47a960cb014ee7b5c007c569` changes only that assertion and
its explanatory comment in `tests/test_ai_reader_crash.py:385`; it accepts either
refusal message. All other files are byte-identical, and tests are outside both
package identities. The retained supplement names `f3ae678…`, clean photo status,
15:42:16–15:51:01 UTC, **26 crash-module tests in 524.783 s, OK, exit 0**. This is
implementer evidence, not a Codex test run.

## Question 1: disposition of the eight conditions

| Package/condition | Disposition at the exact package |
|---|---|
| Stage A A: coverage and cumulative charge | Guardian coverage and 50+5+5 closure repair credited; failed-start recovery still loses charge in the paths below. |
| Stage A B: guardian memory | Closed: sampled and final contribution counted; unreadable final observation refuses PASS. |
| Stage A C: timing | Conditional approximately 21 GiB/s qualification accepted; use the correct endpoint labels and pinned fixture values. |
| Stage A D: authority/recovery sets | Closed: strict domains, actual retained-file binding and exact consumed/outstanding sets reach real admission. Fixture descriptions need precision. |
| Reader A: failed closure admission | Clock-file failure and marker-exception repairs credited; marker's own timeout after rename still qualifies mechanically. |
| Reader B: clock binding/startup charge | Scientific clock override, total sum and attempt-duration floor repaired; repeated/pre-pending failed starts still lose time. Finish the bounded journal-session relation. |
| Reader C: observation deadline | In-loop read/parse crossing repaired; fallback final read and exit-probe timestamps still bypass the cutoff. |
| Reader D: overlength/declarations | Closed for the requested complete-ok excerpt/count invariant and current timing/descendant declarations. |

### Stage A A: preserve the whole failed-start charge through recovery

The guardian now starts before directory creation/lock and survives `run(emit=)`
through result output (`stage_a_controller.py:379–401`). `_close:583–600` charges
the full 60 seconds (50 finalisation + 5 revocation + 5 exit/output) and moves the
guardian deadline to that charged closure. Diagnostics no longer block the abort
path. The retained directory/output/post-close fixtures demonstrate these repairs.
Missing-death evidence for a durable open session now takes the conservative
same-boot/deadline branch (`:250–271`). These are substantial closures.

The new pending-start record does not yet preserve cumulative charge on all
ordinary failed startup/restart paths:

1. **Before pending-start publication.** Directory creation and lock acquisition
   (`:387–388`) precede `controller.starting.json` (`:411–413`). A stall here is
   killed by the guardian, but has no pending/open session. On restart `_load`
   excludes `guardian_*` files from lost-accounting refusal (`:219–228`) and does
   not reconcile their startup deaths. The directory-stall fixture leaves a
   guardian death file but checks only the kill (`tests/test_controller.py:315–330`),
   not recovery charge. The next start can therefore admit a fresh base without
   this machine-up startup interval. Preserve a conservative charge or hold for
   that protected start; a kill alone is not continuous accounting.
2. **Deadline extension before the first durable session.** `_run:418–425`
   extends the guardian to the remaining row cap before the open session and its
   new deadline are persisted. With an existing valid closed `controller.json`,
   block the first persist before rename: the old clock stays valid, the pending
   start still names only the 300-second setup deadline, and the controller can
   survive nearly the remaining row cap. `_charge_failed_start:273–292` does not
   read the guardian death and charges at most that pending setup interval. This
   trace uses an existing clock, so it does not rely on bypassing the separate
   missing-controller/temporary-output refusal. Bind the protected deadline and
   charge durably before extending it, or recover the actual longer tail.
3. **A crash during recovery of a failed start.** `_run:408` reads old pending S1
   into RAM, replaces the sole file with S2 at `:411–413`, computes S1's charge in
   memory at `:415`, then supersedes old finals before first persist at `:416–425`.
   If S2 dies there, S1's pending evidence and uncommitted charge are lost. S3 can
   charge only S2. Preserve prior pending charges durably until absorbed into the
   controller clock; repeated failed starts must not erase earlier startup time.

Target recovery after the pre-pending stall, a long first persist before rename
with an existing clock, and two consecutive failures during pending reconciliation.
These are bounded engineering failures within the existing four-hour cap, not a
request for infallible storage or universal scheduler/kernel guarantees. The
declared reboot/power-loss rule and accepted cap-plus-five guardian grace stand.
The brief's blanket “never less than 60 s” also exceeds the same-boot failed-start
formula's `max(0, …)`; state any intended conservative floor accurately.

### Stage A B–D: credit the closures, describe their evidence accurately

The guardian's lifetime maximum is included in each aggregate and its final
maximum is mandatory (`controller:602–619,641–667,1059–1063`). The memory fixture
counts 57.9 MiB; an unreadable guardian refuses PASS
(`tests/test_controller.py:367–387`). B is closed. C is assessed under Question 2.

`enforce.py:124–162,222–264` now applies strict authority types/date/lowercase hash,
checks the retained owner file's actual bytes/hash/strict contents, and enforces
the exact recovery sets. Controller (`:719–731`), full final validator
(`stage_a_report.py:245–250,301`) and pre-native admission (`stage_a.py:892–895`)
use `witness_dir=out`. The legal consume-before-next-try crash remains supported:
`interrupted, recovery consumed` requires 1…tries consumed entries and no outstanding
entry; other statuses require 1…tries−1, an interrupted last try exactly one
outstanding entry, no overlap. No unconditional next-session equality is added.
D is closed; no signature service or permission infrastructure is needed.

Authority mutations exercise both final/pre-native routes
(`tests/test_stage_a_runner.py:480–521`). The missing-file case at `:522–525` and
exact-set cases at `:527–549` exercise the shared checker directly; call sites
establish both-route refusal statically. The overlap/duplicate variants retain
stale counters after deleting a completed entry, despite the “legal counters”
description. They do assert the particular recovery diagnostic, so this does not
undo D. Correct the evidence description rather than claim all variants ran
through both complete admission routes with otherwise legal counters.

### Reader A: marker publication still admits an ordinary timeout

`Clock.close` now fully writes the closed clock before publishing
`clock.closed.json` (`ai_reader_exec.py:313–322`). Clock-file post-rename failure/
stall leaves no marker; an ordinary marker exception removes it at `:323–327`.
Admission binds the marker to the raw hash, clock hash and last session
(`:940–971`). Credit those fixes.

However, the marker's own writer renames it before opening/fsyncing its directory
(`enforce.py:79–92`). If that directory step stalls, the common final timer calls
`os._exit(75)` (`exec:489–492`), bypassing the exception/unlink. A durable COMPLETE,
readable closed clock and matching readable marker survive. `admit_clock:944–988`
can admit them despite the unfinished bounded closure; scientific scoring uses
that admission (`ai_reader_score.py:180–186`). This needs only the marker write's
ordinary stall, not the previously accepted Stage A case of two failed revocations.

The new fixture at `tests/test_ai_reader_crash.py:419–431` tests the clock-file
error/stall; `:433–438` tests a marker exception. Neither tests the marker's
post-rename stall/exit-75 path. Distinguish bounded successful closure from this
failed process exit, with targeted admission evidence after a marker timeout.
Preserve the candid filesystem/power-loss residual rather than claim crash-proof
publication.

### Reader B: retain startup charge before replacing its pending evidence

Scientific scoring/admission now refuses a supplied clock path
(`ai_reader_score.py:155–156,198–208`); the admitted total must equal closed live
plus crash/failed-start charges and cover the journal's charged attempt seconds
(`exec:972–987`). The zero-clock and inconsistent-sum examples are refused. A
single failed start is charged by the next successful Clock persist (`:217–239`),
and its fixture is meaningful.

Repeated failures still erase charge. S1 durably writes `clock.starting.json`,
then dies before Clock's first persist. S2 reads S1 at `Job.run:569` and replaces
the sole file with S2 at `:573–574` before `check_accounting:575` and Clock's
reconciliation/persist. If S2 also dies there, S1's authority exists only in lost
RAM; S3 charges S2 alone. These pre-clock paths have no attempt durations to make
the journal floor detect the missing setup. Durably accumulate or reconcile
pending charges before replacement; test two failures followed by recovery.

Coverage before pending publication also matters near the cumulative cap.
`mkdir`, lock and old-clock read (`:554–561`) precede the pending record; the
shortened replacement timer (`:565–567`) starts afresh without subtracting elapsed
setup, and pending `start_wall` is the later `now` (`:572`). With three seconds
left, a five-second old-clock read can return under the initial 300-second timer,
then obtain a fresh three seconds. A subsequent failed start charges only that
later interval. Include elapsed setup in the remaining deadline/charge or hold
when it cannot be recovered. No model call is needed for these checks.

Finish the bounded journal/clock-session consistency requested by B as well:
the marker binds only the last session. The admitted clock does not require each
journal `open.session` to have a unique compatible clock entry. In a valid
multi-session COMPLETE, dropping an earlier clock session, reducing the total to
the last live time and updating the marker hash still passes the present checks
if that last time exceeds summed `end.seconds`; the committed journal/package
need not change. Check membership/uniqueness while allowing extra failed/pre-open
clock sessions. This is a specific altered-accounting relation, not a requirement
to authenticate self-consistent historical wall times or build tamper-proof archives.

`Rev7.test_failed_start_is_charged_at_the_next_start` (`crash:440–452`) tests one
failure then success. The undercharge fixtures (`:454–477`) test the repaired
zero-total and inconsistent-sum cases; they do not cover the above paths. The
different pending/open UUIDs can also conservatively double-charge a crash between
first persist and pending unlink; align them or disclose that early-stop case.

### Reader C: check the observation that actually supplies accepted evidence

The in-loop read/parse branch now checks its completed observation time
(`ai_reader_runtime.py:401–406`), closing the prior in-loop crossing. Cleanup,
bounded reads and final overflow checks remain credited.

The fallback remains: a command writes correct logs and exits before deadline;
`LocalCommand.poll:267–272` returns False with `timed_out=False`; the first complete
log read at `:408` and search at `:415` finish after deadline. Cleanup does not
update the flag, and `:413–414` checks only that old flag. Correct equivalent input/
configuration logs can still be accepted. Timestamp every read/parse that can
supply accepted evidence, including the fallback. A genuinely recorded timely
observation may remain valid; a new late observation must not create a receipt.

Likewise `poll` measures `late` before the exit probe, so a scheduling pause across
`:267–268` can accept an exit actually observed late. Check the resulting exit
observation's timestamp. `test_complete_logs_observed_after_the_deadline`
(`tests/test_ai_reader.py:1299–1321`) tests the repaired in-loop branch while the
fake leader sleeps; the timeout-zero fixture (`:1295–1297`) does not establish an
already-exited leader at its probe. Add targeted already-exited/fallback controls
with complete equivalence-positive logs, without any scientific request.

### Reader D: closed within its requested scope

Complete-ok event text now binds the exact answer or first 2,000 characters and
actual character count (`ai_reader_journal.py:304–321`); lifecycle/full digest/
answer-file checks remain. Excerpt and length mutations refuse on complete and
resume validation. Overlength is still an error, with no gate credit. The new
fixture at `tests/test_ai_reader.py:1323–1336` covers both requested mutations.
The design marks older 30-second allowances historical; current job says 60;
descendant declarations distinguish recorded escapes from unobserved transient
children. The current reader suite pointer is revision 7. D is closed; the
previously accepted transient-child and source/isolation limits stand.

## Question 2: conditional memory qualification

**Yes, approximately 21 GiB/s is now acceptable as the declared measured local
qualification under the stated assumptions.** It is not an enforced universal
allocation, scheduling or kill-latency guarantee, and it measures synthetic
control paths, not the frozen model's actual growth.

Ticks carry source observation time; the watchdog no longer resets age to
consumption (`controller:958–960,1062–1088`; `watchdog:187–207`). The saved ordinary
path runs from its preceding successful reading through kill, leader death and
verified extinction: 0.0316 / 0.0361 / 0.041 s. The later hung sample's source
reading through watchdog observation/group extinction/controller death is
0.1559 / 0.1831 / 0.1936 s. The first hung sample uses the pre-GO arming tick as
baseline, not an actual successful memory reading; its corresponding endpoints
are 0.1501 / 0.1770 / 0.1896 s. The blocked-I/O 0.0084 s observation-to-worker-death
figure starts at the deciding iteration, so do not label it a preceding-reading
interval. These distinctions do not require a new scientific run.

Stipulating 0.16 s observation allowance and the pinned fixture's separate
0.0267 s SIGKILL delivery gives `4/(0.16+0.0267) ≈ 21.42 GiB/s`; using the latest
observed controller endpoint gives `4/0.1936 ≈ 20.66 GiB/s`. About 21 is reasonable
for this scoped declaration. Current fixture averages are **11.12 GiB/s** for
one thread and **33.41 / 53.04 / 74.06** for two/four/eight: one fits, the others
do not. The brief/criteria instead quote another set (11.66 / 34.0 / 55.2 / 70.5
and 0.0259 s). Correct their attribution to the exact retained fixture; the
engineering conclusion is unchanged. Finite averages do not bound bursts.

Keep the stated assumptions: ordinary scheduling without multi-second starvation/
suspension, a current footprint ledger within a reading, and SIGKILL delivered as
measured. Faster allocation, overshoot, pressure or cap failure stops and
invalidates the qualified fit claim; no Stage B authority follows. Guardian
memory is now included. Remove or clearly mark historical the criteria's older
“enforced” 0.1-second/~22 GiB/s paragraph under “still in force” (`:68–85`), old
50-versus-60 allowance description (`:168–170`) and “this package” revision-5
suite pointer (`:307–308`). State full 60-second charge in the final `time_scope`
(`controller:751–752`). This is declaration alignment, not another memory-code
gate or a demand for a privileged kernel cap.

## Question 3: assertion repair and rerun

**The retained test-only fix plus complete crash-module rerun is acceptable. No
full suite rerun on `f3ae678…` is required solely for that assertion change.**
The main run remains honestly recorded as one failure, not silently converted to
an all-green run. Its failure is the changed refusal message, and the supplement
finishes both refusal and successful-close controls. All other submitted code/
tests are byte-identical. The remaining paths above were not exercised by either
run; evidence for their repairs should target those paths with earlier controls
retained. No unchanged repetition or scientific qualification call is needed to
settle these engineering gaps.

## Question 4: exact remaining list and carried scope

Before favourable reconsideration, Stage A needs A's continuous, durable
failed-start/restart accounting and its targeted recovery evidence, with the
timing/fixture/current-declaration alignment above. B and D are closed; C's scoped
approximately 21 GiB/s qualification is accepted. Reader needs A's marker-timeout
admission refusal, B's repeated/pre-pending startup accounting and bounded
journal-session relation, and C's final-read/exit observation cutoff, with targeted
retained controls. D is closed. Submit the exact changed package(s); no draw,
alias, CLI, model, scientific rule or budget expansion is requested.

Neither package receives a favourable block or launch/call permission here.
The owner's possible Stage A gate change is a separate unresolved decision;
the reader gate remains unchanged. Later passes do not approve Stage B, CONF,
interval adoption or paid compute.

Construction exposure remains disclosed: this chat and helpers cannot be blind
naming readers. Full-bank R2 at RSC `1ab20cd` retains its `f2d1328` target-visible,
concept-batched limitation and prior exposure; it is not later blind calibration.
Row 19, older hostile/length reviews and prior assignments/reports stay closed.
No prohibited plant/key, private audit results or human outputs were opened;
no old capture/refit/simulation/PC job restarted. Foreign changes were preserved.
One authorised completion report goes to Claude R052 after this record is committed;
its receipt/log belongs in the work item.

## Reproduced identities (identification only)

| Stage A field | Reproduced value |
|---|---|
| `criteria_sha256` | `ede8f10f0565acf788378f804e9ce2df3c41fc41529fd2d3b64dd361a57cc1e0` |
| `identity_sha256` | `3dcda1b3381bef74809e4d98895555d59fb0c1bcc9b9f229cb55f14f469af320` |
| `plan_sha256` | `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc` |
| `manifest_sha256` | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| `budget_sha256` | `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f` |

Inner execution identity: `6da552d7a9e4a6f74767be2a2b8dcceb8f43d3f1edf5a74906e9f7881f3101c6`.

| Reader field | Reproduced value |
|---|---|
| `ai_reader_qual_set.json_sha256` | `27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302` |
| `ai_reader_qual_key.json_sha256` | `d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea` |
| `ai_reader_delivery.json_sha256` | `f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8` |
| `ai_reader_exec.py_sha256` | `8a0b3831266f71177a4c12db4fdc2f702f944ac326efd29b8d0871e6e88d2f62` |
| `ai_reader_score.py_sha256` | `c66e6183f41a48dd9ac6aa2d15d5d952a5a0f0b5c15d842f594c11bf91f0aeaf` |
| `ai_reader_runtime.py_sha256` | `b4ce96ecdf0252a445eecd95701cca27efc41b8a5119853ea913188bf2a153f9` |
| `ai_reader_journal.py_sha256` | `e067889c4210b91ec220fbd4f63421fb93fc4fd64f14c398f288fcaa3bcf2907` |
| `ai_reader_key.py_sha256` | `e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f` |
| `ai_reader_frame.py_sha256` | `cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8` |
| `ai_reader_qual.py_sha256` | `6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc` |
| `AI_READER_JOB.md_sha256` | `34c82851bd0d6b871e650ace4dad25ae33bfec7da3fa4d103f2bbdfcb7dbc6cd` |
| `AI_READER_DESIGN.md_sha256` | `2ce732d33686043142d929fed185692bb626321f1418de8523ae6662965c86c3` |
| `stage_a_guard.py_sha256` | `6788e8acdb8f660bf03805c84a8502e1d412adc160f5708eaf6854defc4c3136` |
| `enforce.py_sha256` | `5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42` |
| `memprobe.py_sha256` | `83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465` |
| `stage_a_watchdog.py_sha256` | `bdb2c5e916aa57a946b9145f7dbcbeda9cfadde9b95b76121b2536240b55c8a5` |
| `codex_realpath` | `/opt/homebrew/Caskroom/codex/0.159.3/bin/codex` |
| `codex_sha256` | `4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878` |
| `codex_package_json_sha256` | `8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121` |
| `cli_version` | `codex-cli 0.159.3` |
| `sandbox_exec_sha256` | `58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8` |
| `command_template_sha256` | `031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba` |
| `instructions_sha256` | `e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790` |
| `package_digest` | `f4b7c665a2add27cd75c9aec065c23f3b416f8b14ceb41160b427ca5504321aa` |
