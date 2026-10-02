# R052: Stage A and AI-reader revision-5 exact-package review

2 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.

**Verdict: NOT ON BOARD with Stage A execution or AI-reader qualification calls at
RSC `2610d8a66d36d170c26691158f1dbfd1e280e9e9`.** This record contains no
favourable attestation. The remaining conditions are listed separately below.
Several substantial revision-4 defects are closed; neither a new draw nor a key
change is requested. The owner's proposed change to the Stage A gate remains a
question for the owner, not an adopted exception or a go.

## Scope and evidence

The brief is Unimog
`prompts/2026-10-02_codex_r052_rev5_both_packages_review.txt`, at
`d7ab33dcd3a88919810b707d40ab43008daac36d`, SHA256
`40ddc4664655ad25c609ad3ecea7f3246eb85e72016fd2fe5baadbc8efa24f6f`.
Ownership was recorded in R052 and committed at Unimog `ca336c86`, then handoff
`a684db17-3bcd-572c-a139-27120a1f484f` was acknowledged and accepted before review
edits. The baseline is the completed revision-4 record RSC `1bf9890`.

Read the revision-5 criteria, readiness, reader design/job, submitted controller,
watchdog, memory/ledger/guard, worker/report, reader executor/runtime/journal/scorer,
audit-package binding, relevant tests and frozen JSON metadata, and the owning
framework §§8.2/8.4/8.6 and ledger row 20. Source references below are line numbers
at the exact reviewed commit, relative to `workspace_demo/t1_access/stimuli/photo/`.
Three helpers independently read the control, validation and reader paths. No
submitted module, program, test, fixture or Codex CLI was executed by this review.
Git blob reads, AST literal extraction, hashing and deterministic JSON arithmetic
were used; none is a scientific run. No image was opened or named, model called,
forward/capture/fit/simulation launched, account operated, worktree created or push
performed. Source owns framework/ledger/protocol/dispatch; R084 owns implementation.

Independently reproduced all five Stage A hashes and the inner identity; the local
code, map, positions receipt and packet hashes describe their exact git blobs.
Reconstructed the reader's argv/profile/environment/gate template from text and
its 24-field digest; read the pinned binary, package manifest and sandbox bytes for
their hashes, using the saved CLI version without executing it. From revision 4
to 5, the set, key, delivery, import map and manifest are byte-identical. The plan
diff is confined to revision, envelope and its derived budget hash: all 178
planned attempts, inputs, cases and diagnostics remain unchanged. The carry is
16 attempts and 1,808.73 seconds, making 194 of 200; no allowance is reset.

Retained evidence at RSC `78334bd6e09768143b2412b7d0e9231860e92cfa`,
`reviews/2026-10-02_photo_suite_rev5_run.md` and its directory, was read byte by
byte. All ten retained-file lengths/hashes match the record. It identifies the
reviewed HEAD and a clean photo directory, 12:24:22–12:44:24 UTC: exit 0, 209 tests
in 1,200.167 seconds, OK with five WordNet skips, followed by exit 0, five WordNet
checks OK in 0.661 seconds in the build environment. No failure or error is in the
output. The controller's separate recorded mechanism measurements are read from
`controller_fixtures.json`; the fixture definitions show what they measure.
These results are evidence for those exercised paths, not for unexercised paths
identified here. The earlier retained-suite rerun request remains closed; no
identical rerun is requested by this record.

## Question 1: closure map and remaining gaps

| Stage A condition | Finding at revision 5 |
|---|---|
| A1 maps and completion identity | Closed. Gates consume/check their map and recheck before GATES; report consumes/checks its map and rechecks before its receipt. The dedicated refusal fixtures exercise the omitted call sites. |
| A2 guarded startup and recovery | The start gate, pre-release durable worker/watchdog identities, ARMED reply, single cleanup owner and immediate whole-group restart fix the prior ordinary startup and unrecorded in-group child paths. The shared watchdog still retires on group extinction without checking recorded escaped members; see reader condition 1 and the scoped residual discussion. |
| A3 aggregate and stop margin | Exit peaks now enter member maxima and the final task aggregate; missing exit/self measurements stop PASS. Those fixtures close the earlier final-cap omission. The claimed complete 0.18-second interval is not enforced: cleanup waits before killing, the first sample is unguarded, and measured kill delivery is not a universal upper bound. See Stage A condition 1. |
| A4 whole-controller clock | Process-start accounting, finite/lost-state refusal, group/controller death timestamps and a charged finalisation allowance are improvements. A stalled sampler can outlive its retired watchdog, and several controller-only intervals have no independent deadline. See Stage A condition 2. |
| A5 completion | Marker gating, the ordinary post-rename failure/block and size-mismatch repairs work for the fixtures. The timeout's synchronous marker cleanup itself is unbounded; see Stage A condition 3. The disclosed filesystem failure residual is assessed separately. |
| A6 ledger and pre-native admission | The old zero/negative counterexample is rejected and the full instrumented validator runs before native construction and on reused records. Recovery history is still insufficiently admitted; see Stage A condition 4. |
| A7 report membership | Closed. The exact receipt keys, exact four outputs, current session/package/identity, output hashes and machine-report flags replace self-selected membership; trimmed/extra/flag mutations are exercised. |
| A8 declarations and pins | Closed for this package. Construction-snapshot provenance and the current plan pin are distinguished; current pool/provenance bytes are required equal to the pins. `audit_package.py` binds classifier/normalisation/map code for a later audit package; it does not create that audit package or qualify an audit. |

| Reader condition | Finding at revision 5 |
|---|---|
| R1 retained evidence | The exact=false received-agent/tool counterexample, nonblank provider `-o` evidence, complete-stream parsing and head/tail final-error policy are repaired with dedicated COMPLETE/resume fixtures. An ok outcome still does not bind its retained `-o` evidence to the separate digest; see reader condition 2. |
| R2 structural restart | Closed. Durable holds precede preflight/open; first/later structural-after-end crash fixtures resume with only a valid STOPPED receipt and no dispatch. |
| R3 group recovery | Immediate identity-anchored enumeration with watchdog retirement last closes the prior restart hole. Watchdog retirement on an empty original group still ignores recorded escaped members; see reader condition 1. |
| R4 clock | Finite-domain admission, the live guard, exhausted-resume stop and rejection of a 6.5-hour COMPLETE are real repairs. The receipt/close sequence can exceed the cap after disabling its guard; startup enforcement also begins late. See reader condition 3. |
| R5 local receipts | Bounded reads, quick-exit overflow and normal whole-group cleanup are fixed and measured. Post-spawn setup failures lack a cleanup owner, and deadline acceptance has two gaps; see reader condition 4. |
| R6 journal and quarantine | Exact record key sets, image-size/detail comparison, top-level error handling, token domains, full-file/record bounds and quarantine dedup are substantially repaired with matching mutations/restart fixtures. The independent retained-answer contradiction is not covered by the schema checks; see reader condition 2. |
| R7 declarations and run | The retained run is accepted and the frozen key unchanged. Revise timing, cleanup and evidence claims to match the closures below, then submit fresh identities and relevant retained regression evidence. |

### Stage A: exact remaining conditions

1. **Kill before any I/O wait, and guard the first sample.**
   `stage_a_controller.py:855–857` raises on the memory stop, but `_sample`'s
   `finally` at 872–875 sends `E` (disarming the watchdog's sampler check) and joins
   the I/O thread for up to two seconds. Only after that does `_phase:770–772`
   enter `_end_worker` and send SIGKILL. A slow or blocked writer is an ordinary
   fault path; the worker may continue allocating during that wait. Even healthy
   I/O sleeps in 50 ms pieces (819–820), outside the advertised interval. The
   measured `kill_to_reap_s` starts inside `_end_worker:647`, after this wait, so
   the 0.0167-second fixture value does not measure threshold-observation-to-death.

   Separately, GO precedes `_sample` (766–769), whose first tick is at 870 after
   memory and system observation. The watchdog starts `ticking=False` and enforces
   staleness only after a first tick (`stage_a_watchdog.py:95,112–126`). A hang in
   the first observation therefore leaves the 0.1-second safeguard unarmed while
   the I/O thread can keep its durable beat fresh. The existing hung-sampler
   fixture stalls on its third reading, not the first (`test_controller.py:229–235`).

   Send the stop signal before joining/persisting; keep the safeguard active until
   extinction is verified; arm sample liveness before release or before the first
   potentially blocking observation. Exercise first-sample stall and memory-stop
   plus blocked I/O, measuring from the last admissible observation through group
   extinction. Recompute the conditional margin from that whole interval. A measured
   0.0219-second SIGKILL result is useful evidence, not an enforced universal bound.

2. **Keep an independent whole-controller deadline through every interval.**
   A sampler-stale watchdog kills the worker and exits, but kills the controller
   only for heartbeat/hard-deadline reasons (`stage_a_watchdog.py:137–148`). A
   permanently blocked sampler may therefore keep the controller alive beyond
   four hours with no watchdog left. The fixture expressly expects no controller
   kill for its finite 25-second stall (`test_controller.py:243`). Crash accounting
   also extends the tail to restart only for heartbeat/hard-deadline reasons
   (`stage_a_controller.py:215–217`), leaving this live-controller tail unbounded
   and potentially undercharged.

   The initial load/persist/system read (`run:316–335`) and controller-only
   persistence after a worker/watchdog has ended (`_phase:783–787`) also precede
   or lie outside `_bounded`. Taking a timestamp from process start counts a
   completed operation; it does not terminate an indefinitely blocked operation.
   Start and retain a guard whose kill/exit path does not depend on observation or
   persistence, through setup, inter-phase work, cleanup and finalisation. Charge
   until verified controller death when the machine remains up; preserve the
   separately declared power-loss accounting rule. Test a never-returning first
   and later sample and persistence after the watchdog has retired, with a
   shortened cap and a bounded process exit.

3. **Bound the abort path itself.**
   `_bounded:370–376` calls `_unadmit` before exit 75; `_unadmit:379–386` performs
   filesystem existence/read/unlink operations synchronously without a timeout.
   A blocked abort operation can defeat the finalisation deadline, including after
   a marker rename. The final-record block fixture at `test_controller.py:642–650`
   has no marker and does not stall the cleanup. Ensure the process deadline
   survives marker cleanup, and document/admit the outcome of failed or incomplete
   revocation consistently. Add a post-marker stall/abort-cleanup fixture. This is
   separate from the accepted two-filesystem-failure residual in Question 3.

4. **Validate the consumed recovery history, not only aggregate algebra.**
   `enforce.check_ledger:166–180` requires lists and, for the current
   `interrupted, recovery consumed` status, merely some entry naming the attempt.
   It does not validate each consumed receipt or require the completed attempt's
   prior retries to correspond to unique authorised interrupted tries. A static
   archive counterexample: in an otherwise complete valid archive, change one
   completed planned entry's `tries` from 1 to 2, leave recovery history empty,
   and increase row20/aggregate started, passes and failed by one. Its 195 total
   attempts still fit 200, all counters are legal, and the recount at 184–189 agrees;
   completed files and phase hashes are unaffected. Nothing in this check proves
   the extra try had authority. This is consistently changed-state admission,
   not a claim that the honest writer spontaneously invents a retry.

   Validate exact typed/session/try identities and uniqueness for every consumed
   recovery, correspondence to the attempt's preceding tries and authority, and
   the open/interrupted relations (including kind/session/try domains). Reject
   extra completed tries without that evidence in both pre-native and final
   admission. Preserve the runtime's named, durably consumed owner authorisation.

### AI reader: exact remaining conditions

1. **Do not retire the watchdog while a recorded escaped member lives.**
   `stage_a_watchdog.py:97–98` returns when the original group is gone, before the
   controller-death check and without reading the members file. A sampled
   persistent child that leaves the group can remain when the leader exits; if the
   orchestrator dies before its own cleanup, this watchdog can retire successfully
   while the recorded child survives. This exceeds the disclosed transient,
   unobserved-child limitation. Normal `_clean_group` and immediate restart are
   repaired, but neither replaces the autonomous safeguard in that death window.
   Make watchdog retirement depend on both group and recorded-member extinction
   and exercise leader exit plus a recorded escaped child plus orchestrator death.
   No universal instrumentation of children that appear and disappear between
   observations is demanded. Stage A's stated no-escaping-worker scope limits this
   case there; the shared reader interface permits forks and needs the repair.

2. **Bind retained `-o` evidence to the answer used for admission.**
   `ai_reader_journal._rederive:308–314` compares retained file evidence only on
   provider/structural outcomes. Its ok branch at 326–328 compares event answer,
   recorded answer digest and the separate `file_answer_sha256`; bookkeeping at
   521–523 allows `file_answer=None` or a separately consistent bounded dictionary.
   An otherwise valid ok end can replace `file_answer` with another complete exact
   string, length and matching hash, or None, leave `file_answer_sha256` and the
   event/recorded answer unchanged, and recompute the receipt's raw hash/size.
   This retained contradiction is not rejected before resume/scoring. Honest
   `classify` writes matching evidence; this is an independent archive-admission
   counterexample, not a claimed ordinary provider output.

   Require retained `-o` evidence on ok, bind its digest to the separate field and
   the event/recorded answer, and verify complete text/length or the declared
   overlength representation consistently. Add COMPLETE and incomplete-resume
   mutations of the retained dictionary itself. The existing mismatch fixture
   changes the separate digest, while the new nonblank-file fixture covers a
   provider label; neither exercises this ok branch.

3. **Use one deadline and one charge through receipt and clock closure.**
   `ai_reader_exec.stop:488–496` records elapsed + 30 seconds and bounds only its
   append/persist. `_run:589–590` separately permits up to 60 seconds for
   `clock.close`; `Clock.close:269–285` sets `stop_beat` first (270), which also stops
   the cap guard. Example natural slow-I/O trace: COMPLETE is chosen at cap − 50,
   the receipt work takes 29 seconds, then close takes 40 seconds. The process
   finishes at cap + 19 while the receipt reports cap − 20, within six hours;
   journal/scorer admission never compares it with a finished clock record. The
   seven-hour validator allowance is fixed, but this undercharge remains.

   Keep the cap guard alive until all closure finishes, bound the combined
   finalisation under its charged allowance, and write/admit a completion that
   accounts for that entire transaction. If it times out after the durable COMPLETE receipt append,
   a saved COMPLETE must not remain independently qualifying. Exercise a near-cap
   COMPLETE with slow receipt and slow close together. Also cover initial
   `check_accounting` and `Clock`'s initial `persist` before its guard starts
   (`run:511–514`, initial `Clock.persist:214`, guard start 217–218); the later 900-second admission timer does not
   cover them. Finite-domain, guard-kill, guard-exit and exhausted-resume fixtures
   remain accepted for their exercised paths.

4. **Own local commands before spawn; enforce their final deadline.**
   `ai_reader_runtime.LocalCommand:241–247` spawns, then registers the exit watch
   and reads identity before either caller's cleanup `try`. An exit-watch error
   leaves an ungated local command outside `Job.proc` and its watchdog. A caller
   can STOP/sweep while that process lives. Put post-spawn setup inside a cleanup
   owner and test a one-shot exit-watch/identity setup failure with a child.

   `poll:254–263` checks leader exit before its deadline, so an exit observed late
   need not be marked timed out. `invocation_receipt:394–399` rejects overflow but
   uses `timed_out` only when submission/feedback are missing; valid logs appearing
   in the final read after timeout can still produce an equivalent receipt at
   425. Require explicit deadline compliance before accepting either receipt,
   including quick/late exit and complete invocation logs at timeout. The retained
   timeout fixture emits no logs and covers only the missing-log branch. Keep the
   already repaired bounded reads, final overflow check and whole-group cleanup.

## Question 2: the memory qualification

**Acceptable in principle as a declared, measured limit for this local Stage A;
not established by the exact implementation yet.** I do not require a sampling
controller to guarantee 48 GiB against arbitrary multithreaded allocation, or a
new privileged kernel mechanism as a prerequisite. The source now says the
qualification explicitly, and an expected peak near 31 GiB gives substantial
room below the 44 GiB stop on this engineering screen. That forecast is not a
measurement of the frozen development workload, and the 22 GiB/s condition is
not enforced on the model's allocator.

The arithmetic is approximately 4 / 0.18 = 22.22 GiB/s. The synthetic growth rates
are finite average rates and do not bound shorter allocation bursts. At that stipulated
interval, the measured single-thread rate 14.66 implies 2.64 GiB of growth;
36.22, 58.14 and 74.99 imply 6.52, 10.47 and 13.50 GiB. Those are illustrative
rate × interval calculations, not observed overshoots of the complete controller.
The brief's rounded 6.6–13.7 figures express the same warning. The actual separate
SIGKILL experiment records 4.132 → 4.133 GiB, a 0.001 GiB overshoot, and 0.0219 s
kill-to-exit. It sends a direct kill immediately after its sample
(`memprobe.py:348–363`); it does not traverse the controller's join-before-kill
path. Nor does an observed delivery time impose an upper bound on every future
kernel scheduling interval.

The required alternative is the specific enforceable control ordering in Stage A
conditions 1–2, with end-to-end timing evidence and a candid conditional margin.
Observe and report actual model growth/peak within the existing counted Stage A;
stop and preserve any cap/pressure/fidelity failure, never infer a favourable
result from expected memory. A faster allocation episode or overshoot invalidates
the qualified fit claim and cannot grant Stage B authority. This accepts the
bounded engineering experiment, not a universal hard-memory guarantee or a new
budget. No forward is authorised by this review.

## Question 3: disclosed residuals

**The stated rename/fsync-then-failed-unlink residual is acceptable as a disclosed
filesystem-failure limit for this local qualification.** It takes no scientific
error out of a denominator and confers no automatic Stage B go. Preserve the
failed exit and diagnostic evidence; an abort or uncertainty must be reviewed as
such. Do not promise universally crash-proof persistence. Unlink revocation is
not directory-fsynced here, so power-loss durability of that revocation is also
limited and should be stated. The single blocked cleanup that defeats the timer
is a separate operational omission (Stage A condition 3), not proved away by
disclosing two exceptions.

**The short-lived unobserved descendant is acceptable as a measured-observation
scope limit**, with the existing disclosure: Stage A workers are stated not to
leave their group; the reader may fork, and a child escaping and exiting between
member samples is not covered. Sum-of-lifetime memory is conservative for the
processes actually measured, not all possible unseen processes. This acceptance
does not cover a known, recorded child that persists after its leader's group
ends; reader condition 1 repairs that distinct safeguard defect.

The previously accepted live-bound logits/features, tiny writes within the
reserve, conditional lifetime-maximum overcount and declared power-loss tail
remain scoped conventions. Their acceptance is not an empirical fidelity pass.

## Question 4: disposition and package identities

Both verdicts are negative, so one combined record is used and no machine-readable
favourable block is present. For reconsideration, close the four conditions per
package above; retain the positive closures, caps, carry, population and key;
update the changed declarations and identities, with retained evidence for the
newly exercised regression paths. This is not a demand for another identical run
of an unchanged package. The shared watchdog repair changes both identities.
If either future verdict is favourable it gets its own record with one matching
attestation, exactly as the shared guard requires. The owner decides the separate
Stage A gate question; no exception is inferred from submitting this review.

| Stage A field | Reproduced value |
|---|---|
| criteria_sha256 | `cf547d69a05f687f0e2b9060f60887c7fc864561ca062bf6bab197d7f6fde6ce` |
| identity_sha256 | `55f0384411bcb2162a9306a36bd977cd4d53e3acb3b6522b66b48f1e8bd72913` |
| plan_sha256 | `40aba7ecf4a4cc6cdb5b0a5d536e87f31b4945f6c98a94c0458808050342c74c` |
| manifest_sha256 | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| budget_sha256 | `914fa4156368a2278357bb870786dd568a09823c202b9bd9ea880f1fada80a5d` |

Inner identity: `691f8d21270bb34612671a929bb3b37ed0830d1952499d5dfceb7cd7fd476db1`.

| Reader field | Reproduced value |
|---|---|
| ai_reader_qual_set.json_sha256 | `27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302` |
| ai_reader_qual_key.json_sha256 | `d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea` |
| ai_reader_delivery.json_sha256 | `f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8` |
| ai_reader_exec.py_sha256 | `a7e532205aae5d4975a79efed667f60f76d82c9e80c291926bd5feff8313ae1f` |
| ai_reader_score.py_sha256 | `bc96dfbc791357fc7a838d8bf2bd0575bc75ca2ba91d66a5edd2693a6fcda242` |
| ai_reader_runtime.py_sha256 | `1a0ce787c2ec5e67b593fb373e57cce5a2ec022a53a6baa6d9163b4584faf38b` |
| ai_reader_journal.py_sha256 | `4d404743c04171c41989a4cf1fa47e88169766f3c44248b73c72ece40b52b71d` |
| ai_reader_key.py_sha256 | `e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f` |
| ai_reader_frame.py_sha256 | `cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8` |
| ai_reader_qual.py_sha256 | `6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc` |
| AI_READER_JOB.md_sha256 | `6284a90796a1ec77ffdfd5666723712bd40bd57be7c688a8bcfb61ff1d9b456d` |
| AI_READER_DESIGN.md_sha256 | `b94106103ef5b5d1835e82f69cb706eb1b3ec7113f1dee41160098c61d2d33f3` |
| stage_a_guard.py_sha256 | `6788e8acdb8f660bf03805c84a8502e1d412adc160f5708eaf6854defc4c3136` |
| enforce.py_sha256 | `1439e67b53ebfcf5ef8f03a42a379de46532db0d3a7604b3765d5d586c7d9f59` |
| memprobe.py_sha256 | `9ea4fa5ba37509377178097f00a8eb46718a2d5c971d6a06dbea61ddbb5d3641` |
| stage_a_watchdog.py_sha256 | `35152c963e7510665d759e2d87fc716e5f8bfcfaa9505244c7c11bab35e3724d` |
| codex_realpath | `/opt/homebrew/Caskroom/codex/0.159.3/bin/codex` |
| codex_sha256 | `4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878` |
| codex_package_json_sha256 | `8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121` |
| cli_version | `codex-cli 0.159.3` (saved version; no new CLI execution) |
| sandbox_exec_sha256 | `58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8` |
| command_template_sha256 | `031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba` |
| instructions_sha256 | `e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790` |
| package_digest | `65baf75f29b151c99276f16169e679007f90ed84aa73fe01716f9a55ba85b8b3` |

The reader's 300 items/63 easy and 61-of-63 grayscale gate, S4 prospective sense
filter, enumerated exceptions and disclosed regular-plural omission stand. Its
human menu-choice norms remain a difficulty reference, not human free-naming
equivalence. Different developers do not prove independent errors or absence of
training exposure. This design-review chat and its helpers have construction
exposure and cannot act as blind readers. Earlier full-bank R2 remains complete
at `1ab20cd`, with `f2d1328`'s target-visible concept-batched limitation and prior
exposure disclosure; it is not later blind calibration. All earlier assignments
and their single completion reports remain closed. No report is resent, prior
handoff re-acknowledged or old job restarted. This review authorises no model
request, development forward, Stage B, cloud run or purchased setting.
