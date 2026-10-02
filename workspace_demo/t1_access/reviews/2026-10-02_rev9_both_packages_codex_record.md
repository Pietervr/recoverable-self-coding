# R052: Stage A and AI-reader revision-9 exact-package review

2 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.

**Verdict: NOT ON BOARD with Stage A execution or AI-reader qualification calls
at RSC `ba4fc75dfa9f2621789c6129f71dc27638b2e760`.** Both sets of submitted
counterexamples are repaired, with startup recovery credited for already-dead
starts. One related
condition remains per package: a still-live foreign start before TaskLock can
be charged only through recovery-now, permanently closed and deduplicated, and
its later interval never reconciled. The reader can additionally delete that
start's pending evidence. The final peer cross-check confirmed both traces.
This combined negative record contains
zero favourable blocks. The owner's Stage A gate question stays open; no
exception or go is adopted. Reader calls still require a favourable exact-package
review and dated owner go.

## Scope and retained evidence


Read the full revision-9 Unimog brief at
`c6058cc82bddb1bfa7ead8ed0e0d2f3c9e1189b7`, SHA256
`bfdd432e38e76ad4e8aa7a46aa5e50270f65bb3c3b169802271cd2af9819cc29`.
Ownership was committed at Unimog `039d7f07`, then handoff
`91a1db9f-7e27-55de-a683-b15d137d9d7e` was registry-accepted before review edits.
Compare the completed `7fdb937` review; earlier reviews/reports are not restarted.

Stage A remains a native fidelity/resource screen: 160 mandatory forwards,
18 planned diagnostics and 16 carried engineering attempts, **194 of 200**;
**1,808.73 s carried**, four cumulative hours, 1 GiB output and temporary storage,
48 GiB task memory with a 44 GiB stop. No Stage B or scientific interval authority.

Read the pinned criteria/readiness, controller/watchdog/guard and affected fixture
sources, exact identity metadata, previous review, owning framework §§8.2/8.4 and
ledger row 20. Three independent static helpers examined the Stage A, reader and
integration paths; the live-start trace was independently challenged and confirmed.
Code citations below are exact-package lines under
`workspace_demo/t1_access/stimuli/photo/`. No submitted program, module, test,
fixture or CLI was imported or executed. Only static git/blob/AST, JSON, hashes
and deterministic metadata arithmetic were used. No image was opened or named,
model called, capture/forward/fit/simulation launched, cloud/HPC/account operated,
worktree created or push performed. Construction exposure persists; these reviewers
cannot act as later blind naming readers. Source R052 owns framework/ledger/
protocol/dispatch and author frontmatter, R084 implementation, Codex this review
and its own work-item log.

All five Stage A hashes, inner identity and source/map/receipt/packet relations
reproduce independently from committed blobs. Plan, manifest and budget are
byte-identical to revision 8. The retained suite at
`f4a2cf7f4600fc4ca22e8d9ac9f9bd81bb03667f` records exact HEAD `ba4fc75` and a
clean photo directory, 19:24:58–19:57:09 UTC. All ten retained files match their
listed sizes and SHA256. Main run: **253 tests in 1928.955 s, OK, five WordNet
skips, exit 0**. Separate build run: **five WordNet tests in 0.655 s, OK, exit 0**.
The main log includes 33 Controller, 12 Finalisation and four Startup tests,
including the two new A1 cases; four new reader Rev9 cases also pass. This is
implementer evidence, not a new Codex run. It does not exercise the live-start
transition below.

All **24 reader fields** also independently reproduce from committed blobs and
the existing binary/manifest/sandbox bytes. CLI version is the saved value; its
binary was hashed, not executed. Reader set/key/delivery/runtime/template/
instructions are unchanged from revision 8. The frozen population remains
**300 paired items, 600 responses, at most 660 attempts and six cumulative hours**;
63 easy grayscale items require at least 61 correct. No model, draw, alias, prompt,
scientific rule or budget expansion is adopted. The retained log's four new
reader Rev9 cases accompany eight Rev8 and eight Rev7 cases, not duplicated
inherited test collection.

## Stage A

## Question 1: A1 transitions and producing fixtures

**A1.1 closes for the submitted already-dead transition.** The guardian durably
writes an `armed` record before emitting ARMED (`watchdog:129–136`), observes an
external controller death and records its end (`:139–142`). Recovery scans final
and temporary guardian records (`controller:343–358`) and uses a recorded end
(`:370–372`). `tests/test_controller.py`'s
`test_external_death_before_pending_with_a_healthy_guardian` actually starts a
controller, stalls it before pending publication, externally SIGKILLs it before
its long guardian deadline, waits for `controller_exited`, then recovers and
checks the exact start-to-death charge (`tests/test_controller.py:554–595`). It supplies neither the death nor its
receipt as an invented end state.

**A1.2 closes for the submitted death-before-publication transition.** An unresolved
same-boot armed record charges start to `min(now, setup deadline + 5 s)`
(`controller:361–380`); unreadable evidence or a reboot uses the declared 60 s.
`test_recovery_during_guardian_receipt_publication` starts the real guardian via
`tests/slow_guardian.py`, kills at the shortened setup deadline and delays the
post-kill write eight seconds. Recovery genuinely runs while the final record
still says armed; its charge covers the already-observed death. The test then
waits for the final killed receipt and checks coverage and no double charge
(`tests/test_controller.py:617–633`). That is the previous publication counterexample,
not a supplied final clock.

**A1 remains open for a live foreign start before the lock.** The code does not
require an unnamed armed start to be dead before treating its partial charge as
final. A concrete static trace, without altered records:

1. S1 publishes its armed guardian record, then stalls in directory creation or
   lock-file setup before acquiring TaskLock (`controller:474–477`;
   `guard:107–113`). It owns neither the task lock nor a pending entry.
2. S2 can acquire that lock and load the clock. It reads S1's still-armed record,
   charges only start→now, appends a closed `failed_start_before_pending` session
   and makes S1 known (`controller:343–358,380`). No liveness or controller-identity
   check establishes S1's end; the guardian base stores its own PID, not the
   protected controller identity (`watchdog:129–130`).
3. S1 remains stalled until its later guardian kill, which writes the real end.
   At S3, S1 is already a known session, so `controller:347` skips that later
   receipt permanently. The interval between the provisional charge and S1's
   actual end is never added.

This concerns a still-live pre-lock start, not conservative overcharging of an
already-ended lock contender. The clock is cumulative per start (`controller:218–222`);
S2's own live time does not complete S1's recorded charge. Even a union-of-active-
time interpretation misses a tail when S1 continues beyond S2's charged closure
(for example, a quickly refused S2 plus its 60 s closure versus S1's 300 s deadline).
Both new fixtures terminate S1 before recovery and therefore do not cover this
case. The stated no-trace residual does not apply: S1 has a readable armed record
and a healthy guardian.

Finish the bounded charge/hold boundary: hold until the foreign protected start
has ended, reconcile it by retained identity, or conservatively charge its full
protected bound, including the declared grace/margin, before marking it final.
If recovery is restricted to dead
controllers, enforce that restriction rather than assume it from the operator.
Retain a targeted live-before-lock recovery case. No model run or universal
filesystem, kernel or scheduler guarantee is requested.

Prior A2/A3, B/D and the conditional memory qualification remain closed in their
reviewed scopes. The new durable armed record repairs the two original A1 paths;
the finding above does not retract those repairs.

## Question 2: declarations and retained revision-8 measurements

Alignments a–d are present: each timing path's own baseline; explicitly historical
revision-7 versus revision-8 values; current 0.15 s tick staleness; 50 s finalisation
inside the 60 s charged closure. The supplementary negative list includes `7fdb937`
(`guard:62`). No new schema or attestation objection.

**Keep `controller_fixtures.json` as pinned revision-8 measurement evidence.** No
sampling/tick/worker-kill path changed, so the accepted endpoints, delivery and
conditional about-21 GiB/s scope need no blanket re-record. The new arming and
release paths did change; "no timing path changed" (`criteria:35–36`) is broader
than justified. Attribute the new A1 transition evidence to the revision-9 tests
and retained suite, rather than imply its values are in the older JSON.

The no-armed-record residual is disclosed but its **at-most-10 s** bound is too
tight. After the 10 s ARM wait, `_start_guardian` invokes cleanup before refusing
(`controller:571–574`). Cleanup waits up to two seconds for E, then up to five
seconds after termination before kill/reap (`:590–605`). State the ARM wait
separately from cleanup: nominal waits can total 17 s, plus process startup and
signal/reap latency. That is a qualification of the accepted untraceable-start
residual, not a demand to prove arbitrary OS operations cannot stall.

Criteria §6 (`:341–342`) still points to the rev8 run as evidence for "this package";
the exact suite is the rev9 record above. Readiness's evidence paragraph should
separate the retained rev8 numeric measurements from the rev9 transition tests.
Correct these pointers and residual descriptions alongside the live-start scope;
no full unchanged-suite rerun is required merely for their wording.

## Question 3: the two unresolved pre-commit observations

The revised disclosure correctly distinguishes **one identified STOPPED where
COMPLETE was expected**, without its reason, from **one unidentified crash-module
failure in truncated output**. They are not proved to be the same event. Their
cause remains unresolved; later retained passes show no recurrence in that run,
not a causal resolution.

STOPPED does not qualify a reader; resumed work dispatches no further reader call
after a receipt, although clock-close bookkeeping still runs. The observation
does not demonstrate false promotion, reset or an allowed retry of an answer,
and supplies no Stage A failure by itself. It does not add a Stage A admission
gate. Keep the disclosure and retain full bounded reason/stderr/clock/journal/
marker/watchdog evidence on recurrence, excluding credentials and images. No
scientific call or blanket repeat of the unchanged green suite is required.

## Question 4: exact remaining list

Stage A needs charge or hold for an unnamed foreign guardian record whose
protected controller can still be alive before the task lock, without permanently
finalising its partial start→now charge. Retain the targeted transition. Align
the untraceable-start bound, sampling-path attribution and exact-suite pointers
described above. **No favourable Stage A block is issued.** The owner's unresolved
gate decision remains with the owner.

## AI-reader

## Question 1: A and B1–B3, including producing fixtures

**A: finite late return closes.** The marker's rename remains its final commit
operation; `write_marker` supplies a removal undo (`exec:225–239`).
`Deadline.commit` rechecks `fired` after the rename returns, undoes the late marker
and raises rather than setting committed (`:579–590`). Deadline revocation also
repeatedly removes the marker every 5 ms until exit (`:636–649`). This closes
revision 8's finite rename after a successful early unlink when removal works;
the main thread cannot turn that observed fired-latch late return into success.

The new real-process test forces a blocked commit to return only after the fired
latch, with the tombstone writer blocked and an unblocked control
(`tests/test_ai_reader_crash.py:624–642`; `tests/airq_fixture.py:132–154`). It checks
an existing COMPLETE receipt, non-success exit, no surviving marker, tombstone
presence only in the healthy control, and failed admission. It produces the
finite fired-deadline/late-return transition. **It does not independently witness
the first unlink's completion:** the driver waits for fired plus 50 ms, not an
unlink acknowledgment. Narrow the stated ordering evidence accordingly. Static
post-return undo and repeated-removal code support the repaired mechanism without
inventing a measured early-unlink timestamp.

**Accepted filesystem scope, stated precisely.** An effective undo or repeated
unlink removes an observed late publication; a matching tombstone refuses it
even if removal fails. If the tombstone cannot be published **and neither
effective removal path can complete**, a matching marker can survive; this can
also happen after rename returned and undo blocks/fails. A rename still in flight
in the kernel when the process exits is another instance of unavailable effective
revocation. The source's "any late return the process observes" wording is too
strong without that removal assumption. This review expressly qualifies it.
Power loss can lose the non-directory-fsynced marker entry and leave a COMPLETE
non-qualifying. Universal filesystem transaction guarantees are not proved or
required. The prior condition allowed an honest residual qualification as the
alternative to a universal repair; the concrete healthy-removal counterexample
is repaired. This residual clarification is part of the accepted bounded scope, not a
new scientific gate or a request to rerun the identical suite.

**B1: incomplete pending publication closes.** Startup scans completed pending
files plus readable `.json.tmp` files whose final names do not exist
(`exec:701–716`). Their start IDs are absorbed once at the first clock persist
(`:282–309`), before their files are removed (`:740–743`). Invalid/unreadable JSON
uses the stated 30 s charge. The new fixture actually writes and file-fsyncs the
pending temporary, stalls before rename, dies under the setup timer, then starts
normal recovery and verifies the same ID's failed-start charge and removal
(`crash:644–659`; `airq_fixture:155–167`). It does not fabricate a recovered clock.
The no-temporary-on-disk directory/creation residual remains explicitly disclosed.

**B2: recovered balance before first persist closes.** Clock absorbs the crashed
open session and all prior pending starts, then calls `before_persist` with that
recovered total before any first persist (`exec:261–309`). The callback subtracts
both recovered total and current elapsed setup from the six-hour cap; exhaustion
holds, otherwise a shorter timer is installed before its durable deadline update
(`:720–739`). The real-process fixture first creates a crashed open clock, then
sets a near-cap balance and blocks the first persist. It checks exit 75 under the
recovered-allowance timer, within 12 s rather than the 20 s setup timer
(`crash:661–677`; `airq_fixture:168–175`). The near-cap configuration is supplied,
but the crashed session and the blocked first persist are produced. The retained
test demonstrates the shorter bound; it does not claim a universal scheduling
latency bound. The reader does not consume the Stage A guardian receipt; its own
pending-start recovery has the analogous live-start boundary described below.

**B3: declared compatible states closes.** `session_state_problem`, called by
`clock_problems` at load and admission, permits COMPLETE/STOPPED/ended with live
seconds and no crash charge fields; crashed requires charge = live + tail, tail
at least 30 s; failed_start requires zero live and its charge; undeclared states
refuse (`exec:170–217`). Admission counts only declared ran states and crashed
(`:1161–1168`). The fixture creates a genuine crash then a legal resumed COMPLETE,
confirms admission and applies sum-consistent, rehashed undeclared-state and
zero-tail/reduced-charge mutations (`crash:679–706`). These are intentionally supplied
admission mutations of a produced honest baseline, not claimed crash outputs.
This closes the requested status/charge relation; it does not authenticate all
self-consistent historical wall-clock values.

**One related live pending-start boundary remains.** The pending final/temporary
may belong to a process still alive before TaskLock. The code does not establish
that process's end before treating its start→now charge as final:

1. S1 writes its own pending record before TaskLock (`exec:677–680`). Its main
   thread can stall before acquiring the lock, including after a readable
   temporary was written, while its independent setup timer remains healthy
   (`enforce.py:83–90` for write/fsync/rename stalls).
2. S2 acquires the task lock, reads S1's foreign final/temporary (`:701–716`),
   charges only `min(now, deadline_wall) - start_wall` and appends a CLOSED
   failed_start (`Clock:282–299`). No protected-process identity or end/liveness
   check is retained in the pending record (`:678`). After first persist, S2
   deletes that pending evidence (`:740–742`).
3. S1 continues until its later setup-timer exit. Its extra interval is never
   reconciled: a later Clock skips the already-known ID (`:283–286`), and the
   pending file can already be gone. Keeping S1 stalled until its timer exits
   avoids any subsequent S1 clock session; no altered archive is required.
   A concrete promptly ended S2 is a pre-journal package/go refusal
   (`exec:770–775,783`), followed by its `ended` close (`:753–757`); that close's
   60 s timer is a time limit, not an automatic 60 s cumulative charge. S1's
   setup timer (`:668–669,566–577`) exits75 without a terminal startup record.

The per-start clock is additive (`:296–300,341–342`). S2's own time does not
finalise S1's required charge, and S1 can continue beyond S2's charged closure.
Both starts have readable evidence; this exceeds the disclosed no-temporary
residual. The new B1 fixture waits for S1's exit 75 before S2 starts
(`crash:647–653`), so it does not test live-before-lock recovery. B2 correctly
uses the recovered total, but that total already treats the live S1 partial
interval as final; B3 validates the declared failed_start shape, not its end.

Hold/reconcile an unresolved foreign live start, retain provisional accounting
and complete its charge before work/admission, or conservatively charge its full
protected bound, including declared grace/margin, before closing it.
If recovery is allowed only after every
old start is dead, enforce that boundary. Retain a targeted recovery-while-S1-
alive case. This is the current startup accounting scope, not a request for a
new scientific draw, archive-signing system or universal filesystem guarantee.

## Question 2: declarations and retained measurements

The C fallback description is corrected to **timely-parse-positive**, not an
equivalent receipt: content `[x]`, model `m`, empty feature tags; the returned
receipt is not asserted equivalent. C's actual observation cutoff and previous
boundary evidence remain credited. Startup residual now acknowledges readable
incomplete publication; marker residual acknowledges the revision-8 late return
after early unlink. Broaden/narrow the residual and fixture claims exactly as
qualified above when maintaining source prose. A prose edit to a bound file moves
this package's identity and must follow its existing exact-package review/go
binding; this review does not automatically approve a modified package.

The five Stage A alignment questions are addressed above.
Retaining the pinned revision-8 numeric controller measurements is acceptable
for unchanged sampling/tick/worker-kill paths; new Stage A transition evidence
belongs to the rev9 fixtures/suite. No blanket re-record or identical full-suite
rerun is required merely to replace a stale pointer or qualify wording.

## Question 3: unresolved pre-commit observations

The disclosure now correctly identifies **one unretained STOPPED where COMPLETE
was expected**, reason absent, plus **one unidentified failure in a truncated
crash-module run**; their identity is not asserted. The cause remains unresolved.
The retained rev9 run and source-reported pre-checks show no recurrence in those
runs, not causal resolution of the original events.

A STOPPED receipt cannot qualify; scientific admission requires a valid COMPLETE
and its closed clock/marker. A resumed job dispatches no further reader calls
after a receipt (`exec:790–791`), while its clock-close bookkeeping can continue
(`:753–760`). The disclosure demonstrates neither invalid promotion nor reset nor
an authorized retry of a received answer. **It adds no independent admission
failure on the evidence now retained.** Keep it visible; on recurrence,
retain exact test/subtest/command/exit/stderr/receipt reason and bounded journal,
clock/marker/tombstone/watchdog evidence without credentials or images. Causal
diagnosis and a targeted regression, or evidenced environmental/fixture cause,
would settle it. No additional scientific call or blanket unchanged-suite rerun
is requested to erase an honest unresolved disclosure.

## Question 4: exact remaining condition and dispatch gate

Finish charge or hold for foreign pending final/temporary evidence whose start
may still be alive before TaskLock, without permanently closing and deleting
its partial charge; retain the targeted live-start transition. Correct the
residual/fixture descriptions proportionately as qualified above. **No reader
attestation is issued. A favourable exact-package review and the dated owner
go remain required before any qualification call.** The later audit remains
a separate frozen job and gate; the reader's empirical 61/63 qualification is
not presumed from this mechanism review. Stage A, Stage B, licence provenance,
human equivalence and training-data independence are not approved here.

## Retained ownership and prior limits

Source R052 adopts owning framework/ledger/work-item summaries and routes the
bounded repair conditions to R084. Codex owns this review and its own log only;
author frontmatter remains untouched. Earlier row19/full-bank/hostile/length
reviews and their one-report receipts remain closed; full-bank R2 at `1ab20cd`
retains its `f2d1328` target-visible, concept-batched limitation and prior exposure,
not later blind calibration. No prohibited private outputs or old jobs were
opened/restarted; foreign edits preserved. One authorized completion follows this
record's commit; its actual transport/native receipt belongs in the work-item log.

## Reproduced identities (identification only)

| Stage A field | Reproduced value |
|---|---|
| `criteria_sha256` | `6adb6d1d14311016930dc07f38e8ecd55d5399ac80324da3ff6c8c9e2178864d` |
| `identity_sha256` | `57f6e68a3733c9f82ffa171ba354681c2da572f1f47384981571576151ac6df9` |
| `plan_sha256` | `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc` |
| `manifest_sha256` | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| `budget_sha256` | `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f` |

Inner execution identity: `5b6bc5bf72b7d14d7228f21f7349a5816cde07ff97c8e96562833be024c7fc4e`.

| Reader field | Reproduced value |
|---|---|
| `ai_reader_qual_set.json_sha256` | `27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302` |
| `ai_reader_qual_key.json_sha256` | `d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea` |
| `ai_reader_delivery.json_sha256` | `f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8` |
| `ai_reader_exec.py_sha256` | `dfe654564558b7924d2709677f2c389a95a99fd03dd71c17053fea1a9388bbc9` |
| `ai_reader_score.py_sha256` | `c66e6183f41a48dd9ac6aa2d15d5d952a5a0f0b5c15d842f594c11bf91f0aeaf` |
| `ai_reader_runtime.py_sha256` | `96235ea8e276b49ee671437776ee45d49a0249db70ce69b17849881fd4cac89e` |
| `ai_reader_journal.py_sha256` | `e067889c4210b91ec220fbd4f63421fb93fc4fd64f14c398f288fcaa3bcf2907` |
| `ai_reader_key.py_sha256` | `e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f` |
| `ai_reader_frame.py_sha256` | `cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8` |
| `ai_reader_qual.py_sha256` | `6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc` |
| `AI_READER_JOB.md_sha256` | `25982ce190d9da3002b98e6d8c953f99c23194cb41debd1fc086cf503c4fa637` |
| `AI_READER_DESIGN.md_sha256` | `c63f0f02dfd472c0a5c07788da1e8e45d2ec753144a95d8f5c0e4ab2dca05300` |
| `stage_a_guard.py_sha256` | `58a2056af5b1999e998b5c127b67b8bf1eaad68e44c34407afdaaccae13a13d5` |
| `enforce.py_sha256` | `5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42` |
| `memprobe.py_sha256` | `83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465` |
| `stage_a_watchdog.py_sha256` | `bb02ab5d3add4ed1fcedc460c66faf8993a60358f9423079add81c8b47874f4e` |
| `codex_realpath` | `/opt/homebrew/Caskroom/codex/0.159.3/bin/codex` |
| `codex_sha256` | `4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878` |
| `codex_package_json_sha256` | `8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121` |
| `cli_version` | `codex-cli 0.159.3` |
| `sandbox_exec_sha256` | `58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8` |
| `command_template_sha256` | `031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba` |
| `instructions_sha256` | `e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790` |
| `package_digest` | `33eac04943cc004ecfba129c190c8c378b332f067971274d3b90be622f9de920` |
