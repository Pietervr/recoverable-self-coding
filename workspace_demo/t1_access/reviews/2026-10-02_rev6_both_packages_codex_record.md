# R052: Stage A and AI-reader revision-6 exact-package review

2 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.

**Verdict: NOT ON BOARD with Stage A execution or AI-reader qualification calls at
RSC `bb4f07675bbc941bbb2dd9cb4c4762b82b42f9a8`.** Neither package receives a
favourable attestation. This is one negative record, as the brief permits. The
owner's question about changing the Stage A gate remains unanswered; it is not an
adopted exception or a go. The reader gate remains in force.

## Scope and evidence

Read the entire Unimog brief
`prompts/2026-10-02_codex_r052_rev6_both_packages_review.txt` at
`361d0bc396599d76c96e042e89de360088d1d5d8`, SHA256
`8fcc01d9bae482d5e635bd925c1e079430cefa50917000b4e2db2186c4316f42`.
Own review/log ownership was committed at Unimog `8611a4da`, then handoff
`a2c38501-9a3c-5736-88b2-f7b69edc869d` was acknowledged and registry-accepted
before review edits. The comparison is the completed revision-5 record RSC
`b569f8ac724e4469f041a9785815d86b66465898`.

Stage A has 20 frozen inputs, 160 mandatory forwards, 18 planned diagnostics and
16 carried engineering attempts: 194 of 200, with 1,808.73 seconds carried. It
compares the instrumented path to its same-weight native reference and produces
fidelity/resource evidence. The reader has 300 fixed items in two views, 600 planned
responses, at most 660 attempts and six hours. Its admission panel remains the 63
easy grayscale items, requiring at least 61 correct. Neither is an assumed pass or
Stage B authority.

Read the submitted criteria/readiness, controller/watchdog, ledger/guard,
worker/report and memory code; reader design/job, executor/runtime/journal/scorer;
changed tests and frozen metadata; owning framework §§8.2/8.4 and ledger row 20.
Three static helpers read the control, validation and reader paths independently.
References below are line numbers at the exact reviewed commit, relative to
`workspace_demo/t1_access/stimuli/photo/`. No submitted module, program, test,
fixture or Codex CLI was imported or executed by this review. Git blobs, AST
literals, hashes and deterministic metadata arithmetic were used. No image was
opened or named, model called, forward/capture/fit/simulation launched, account
operated, worktree created or push performed. Source owns framework/ledger/protocol/
dispatch; R084 owns implementation; this review owns only its record and own log.

All five Stage A package hashes and its inner identity were independently
reproduced. The reader's 24-field digest was reconstructed from exact source and
binary/manifest/sandbox bytes, using its saved CLI version without execution.
The plan, manifest, import map, reader set/key/delivery and all 600 delivery
user-text hashes are byte-identical from revision 5 to 6. No draw, alias, CLI or
budget expansion is requested. Previously accepted key/specificity, provenance,
request isolation, smoke, native admission and report checks remain in scope.

The retained suite record `reviews/2026-10-02_photo_suite_rev6_run.md` and all ten
output files were read at RSC `40c2758`. Every listed file size and SHA256 matches
its immutable blob, including the two empty files. Recorded HEAD is the reviewed
`bb4f076…`, with a clean photo directory before the run; start/end are
2026-10-02T13:40:22Z / 14:02:43Z. The main output shows **221 tests in 1338.445 s,
OK with five WordNet skips, exit 0**. The separate WordNet output shows **five
tests in 0.644 s, OK, exit 0**. No failure or error appears. The main raw output
contains five skips although the prose skip list names only four; the separate
run covers all five. This is retained implementer evidence, not a new run by
Codex. Another identical unchanged-suite run is not a remaining condition.

## Question 1: the eight conditions and their fixtures

| Prior Stage A condition | Revision-6 assessment |
|---|---|
| 1. Kill before blocking I/O; guard the first sample; qualify the full interval | Kill-first and tick-before-GO are real repairs. Ordinary stop, blocked I/O, and never-returning first/third sample fixtures exercise them. The timestamps do not yet establish the claimed previous-successful-reading through extinction interval; see Question 2. |
| 2. Independent controller deadline and continuous restart charge | The guardian and stalled-sampler controller kill are real. The post-gates persistence fixture proves the guarded path with a committed death receipt. Setup before guardian, output after retirement, missing death receipt and closed-session tail gaps remain. The new guardian is omitted from memory aggregation. |
| 3. Bounded abort/revocation | Parallel tombstone and marker unlink, five-second shared deadline and exit 75 repair the blocked-unlink path. Post-marker and blocked-unlink fixtures genuinely exercise it. Correct the fsync declaration; include revocation time and remove blocking diagnostics before reaching this abort. No universal crash-proof storage guarantee is demanded. |
| 4. Authorised retry history | The original 195-count extra-try/no-history counterexample is refused in final and pre-native validation; honest two-recovery history is exercised. Authority scalar/file consistency and exact status/history admission remain incomplete. |

| Prior reader condition | Revision-6 assessment |
|---|---|
| 1. Watchdog protects recorded escaped members | Closed for the original counterexample. Retirement checks both group and recorded identities; the controller-crash fixture with an escaped persistent child exercises the path before cleanup. The accepted transient/unobserved-child scope stands. |
| 2. Bind the retained answer dictionary | Dictionary/None and ordinary full-answer repairs are real and exercised on COMPLETE and incomplete resume with no dispatch. Overlength excerpt/original-length metadata remains unchecked against the available full event text. It remains an error, never naming credit. |
| 3. Setup, whole-job deadline, bounded receipt/close and admission | The setup timer, continuing cap guard, common 60-second receipt/close timer and scorer clock check are real improvements. Fixtures exercise a pre-write slow close and one setup stall. Post-rename failed-close admission, coherent undercharge/alternate clock and failed-start charge across retries remain. |
| 4. Own local-command cleanup; refuse late observations | Exit-watch/identity setup is now inside the cleanup owner; its one-shot failure fixture closes the orphan path. The new sleep-past-deadline fixtures ordinarily kill a still-running command before its late output. They do not exercise the late-observation acceptance branch described below. |

The remaining list is bounded by the concrete paths below. New evidence should
target the changed fault, observation and admission branches, with earlier
positive cases retained. No scientific execution is needed to repair them.

## Stage A: remaining conditions

### A. Complete controller coverage and charge its actual bounded closure

`stage_a_controller.py:331–336` performs `self.out.mkdir` before starting the
guardian. An ordinary blocked directory operation is outside its advertised
300-second setup deadline. At the opposite end, `run:384–386` releases the lock
and stops the guardian before `main:1007` prints the returned record. A blocked
stdout then has no live guardian or finalisation timer. This does not satisfy
the watchdog's stated coverage to controller exit. Move potentially blocking
setup inside active protection and retain independent protection through final
output/cleanup or make that output explicitly bounded. Target pre-guardian
directory and final-output stalls, rather than demanding universal import/kernel
latency bounds.

Restart also undercharges natural failed paths. The guardian kills first and only
then writes `guardian_<session>.json` (`stage_a_watchdog.py:136–139`). In `_load`
(`controller:212–242`), charge-until-restart is conditional on that file already
existing. If a controller blocked between phases is killed at the session cap
and its death file is missing or late, the fallback can charge only 60 seconds
after its last beat, despite a much longer machine-up tail. The new fixture
(`tests/test_controller.py:301–325`) waits for the committed receipt before
restart and thus avoids this case. Durably distinguish an armed/unfinished
controller session and conservatively charge or hold without relying on the
post-kill write having finished. Preserve the separately declared power-loss rule.

`_close:507–519` charges 60 future seconds and clears `open_session` before final
publication. `_load` reconciles death only inside `if open_session`, so a
post-close guardian death or stalled finalisation is not reconciled. The whole
60-second finalisation wait can be followed by five seconds of revocation
(`:436–468`), not charged in that closed total. Moreover `_bounded:451–452`
writes/flushes stderr before entering the bounded abort; that diagnostic can
itself block until the later guardian deadline. Preserve a pending bounded
closure/process-death relation for failed completion, account finalisation plus
revocation, and make diagnostics unable to delay abort. Add post-close and
missing/late-death-evidence restart checks with the known tail charged. The
declared cap-plus-five grace is acceptable if all of it is retained and charged;
it does not increase the admitted four-hour budget.

### B. Include the guardian in whole-task memory

The new guardian is a separate process/session, a controller child
(`controller:401–402`). The sampler enumerates worker descendants and adds the
controller and phase watchdog (`:960–962`), but never `self.guard.pid`.
`_task_aggregate:559–572` likewise lacks its footprint and final maximum. Thus the
aggregate omits a known owned process. Include the guardian's identity, footprint
and lifetime/final contribution, with a focused fixture asserting that
contribution. This is not evidence the expected 31 GiB workload fails the 48 GiB
cap; the guardian may be small. It is a concrete gap in the whole-task claim.

### C. Qualify and state the full observation interval accurately

The conditional engineering qualification remains acceptable in principle. The
exact enforced 0.16-second claim is not established by the current timestamps;
the evidence and targeted closure are given under Question 2. Do not change the
draw or demand a privileged kernel cap to settle this.

### D. Admit strict owner authority and an exact legal recovery history

`enforce.check_ledger:179–200` validates exact keys and a strict top-level recovery
try, but compares `authority.try` only by tuple equality. `true` or `1.0` equals
try 1. The authority date need only be nonempty and its file digest any
64-character string. Starting with otherwise legal retained recovery history,
changing only those authority fields to `true`, `not-a-date` and 64 `x`
characters leaves the predicates passing; each mutation also passes separately.
This is altered-archive admission, not honest intake output. Intake
(`stage_a_guard.py:154–170,318–326`) already requires exact positive integers,
nonblank text, a real date and a hash computed from the actual owner file.
Controller, pre-native and final validation share the weaker retained check
(`controller:623–635`, `stage_a.py:890–893`, `stage_a_report.py:245–250`).

Use those strict domains for retained admission and check the authority fields
and digest against the retained owner file, or checked original raw authority
bytes. No signature service or new permission infrastructure is requested. The
new bool fixture mutates the top-level try, not `authority.try`
(`tests/test_stage_a_runner.py:480`); its otherwise accepted synthetic authority
uses `'a'*64` without binding an owner file. Add authority-only bool/float/date/
digest mutations and a well-typed mismatch against that witness through both
pre-native and final admission.

The required recovery set is also not exact: `enforce:198–207` permits a consumed
recovery at any try up to the last, but only checks for missing required earlier
tries. A clean completed attempt with `tries=1` can acquire a consumed recovery
for try 1 without changing counters or output hashes and still pass. After
consumption, the honest state is `interrupted, recovery consumed`; a
later completion requires opening try 2 (`enforce:344–376`). Outstanding and
consumed entries can also overlap for an interrupted last try. Require precisely
1…tries−1 consumed tries for completed/open/failed/interrupted states and
1…tries for `interrupted, recovery consumed`, exactly one outstanding record per
interrupted attempt's last try, and no consumed/outstanding overlap. Test those
mutations with legal counters and unchanged outputs. Do not unconditionally require `consumed_by` to
equal the next attempt's session: a valid crash can intervene after durable
consumption and before the next try opens.

## Reader: remaining conditions

### A. A failed post-rename clock close must not qualify as completed

`Clock.close` appends a closed session with the raw-journal hash and clears
`open_session` before writing (`ai_reader_exec.py:277–291`). The common writer
renames that snapshot then opens/fsyncs its directory (`enforce.py:85–90`). A
one-shot directory error after rename leaves a readable closed clock beside a
durable COMPLETE journal. `_run:608` raises; `run:530–543` cancels the final timer
and skips further clock closure because `open_session` is already None. The
scorer's `admit_clock:894–905` accepts that matching hash/outcome and within-cap
total. A directory stall after rename can similarly exit 75 under the timer
while leaving mechanically admissible records. This is an ordinary I/O failure,
not an edited archive.

Distinguish successful bounded completion from a merely renamed snapshot, so
the documented unfinished closure does not qualify. Keep a candid filesystem/
power-loss residual instead of claiming infallible persistence. Add a post-rename
directory error and stall, checking scorer admission after the failed process
exit. The current slow-close fixture (`tests/airq_fixture.py:109–112`,
`tests/test_ai_reader_crash.py:377–402`) delays before the real write and proves
only that earlier failure window.

### B. Bind independent scientific clock admission and failed-start accounting

`ai_reader_score.py:195–207` exposes `clock_path` but omits it from scientific
injected-object refusal; `admit:185–186` accepts the supplied path. Even at the
default path, `admit_clock` checks no lower bound against the journal's charged
attempt seconds and no coherent session identities/totals. The lower-bound
check in `check_accounting:297–314` runs before execution, not scorer admission.

For an otherwise valid committed scientific COMPLETE journal with positive
attempt durations, an alternate/replacement clock with `seconds_total=0`,
`open_session=null` and one session containing `live_s=0`, `closed='COMPLETE'`
and the exact raw hash passes the shown schema and upper-bound predicates
(`exec:149–169,888–905`). Its journal/package need not change. This is coherent
altered-accounting admission, not a claim the honest writer generates it.
Refuse a scientific caller-selected clock; bind the intended execution clock's
session/accounting relations to the journal, including the charged-duration
lower bound and legal cumulative totals. Preserve labelled synthetic injection.
Test scientific-path refusal and coherent undercharge, rather than only NaN.

The setup timer also bounds each start without ensuring continuous charge across
failed starts. It allows a fresh 300 seconds before the old counter is loaded;
the cumulative guard starts only after Clock's initial persist
(`exec:222–226,519–527`). Death before that persist records no new session, so a
restart can lose this setup time and repeat it even near the cumulative cap.
Preserve a conservative failed-start charge/hold and enforce the relation to
remaining cumulative allowance. The shortened setup fixture kills once; add
restart accounting of that failed start. No reader call is made on this path.

### C. Check the actual final observation time for local receipts

In `ai_reader_runtime.py:398–401`, a poll may return True just before its deadline
and the bounded log read/regex search may complete after it with valid submission
and feedback logs. The branch breaks immediately, without another poll.
`timed_out` stays false; the final read/cleanup does not update it, and `:408–409`
can admit the receipt. A delayed read or scheduling interval suffices. This
contradicts the rule that complete logs observed only after the deadline refuse.

Check the observation timestamp after reading/parsing and before acceptance.
Target already-exited leaders observed late and complete valid logs whose
observation is deliberately delayed past deadline; assert those logs/exits
exist at refusal. Current fixtures (`tests/test_ai_reader.py:1258–1273`) sleep
1.1/1.3 seconds with timeout 1 and normally kill the still-running command
before the late exit/logs. Retain the repaired cleanup owner and cap handling.

### D. Validate the declared overlength representation; align current declarations

For an overlength `ok` outcome with a complete retained event stream, the full
event text/digest is retained, but the validator relaxes excerpt/length consistency
(`ai_reader_journal.py:314–320,336–341,516–520`).
An edited excerpt or another declared length above 2,000 can survive while full
digests remain unchanged. It is still `ERR_OVERLENGTH` (`ai_reader_score.py:105–106`)
and cannot become a correct name or improve the gate. Bind the available complete
event text's first 2,000 characters and actual character count to the retained
representation; test those metadata mutations. This completes the declared
unedited referral evidence, not a new scientific scoring rule.

Align current documentation: the older design table still describes 30 seconds
where the new transaction uses 60; mark genuinely historical descriptions as
such. `AI_READER_JOB.md:62` and the runtime opening say every fork stays in-group,
which exceeds the recorded-escape mechanism and fixture; qualify that claim
within the already accepted transient-child scope. Update stale suite pointers
to the retained revision-6 evidence when the next package is made.

## Question 2: memory qualification

**The conditional approximately 22 GiB/s margin remains acceptable in principle,
but is not established as the exact enforced interval claimed at this commit.**
Kill-first (`controller:988–994`) and tick-before-GO (`:859–865`) repair the
previous ordering. The saved figures are meaningful for the paths timed:
0.0093 seconds from deciding iteration start to leader death, 0.0616 to verified
extinction, 0.0082 with blocked I/O, and about 0.0334 to group death / 0.0464–
0.0484 to controller death from the watchdog's deciding observation
(`controller_fixtures.json:29–43`). Leader death and whole-group extinction are
different endpoints.

`_kill_now:920–922,947,989` timestamps the current deciding iteration's start,
not the previous successful below-stop reading. The hung-sample fixture times
from the later watchdog condition observation (`tests/test_controller.py:261–263`),
excluding the age of the preceding tick. The watchdog resets that tick's time
at consumption (`stage_a_watchdog.py:180–195`), not at the source observation.
Iteration work, tick delivery/consumption, polling and scan latency thus enter
the complete gap. The 50 ms + 100 ms + 10 ms arithmetic is a configured allowance,
not evidence every term is enforced from the preceding successful reading.

If 0.16 seconds and measured 0.0254-second kill latency are stipulated,
`4/(0.16+0.0254)` is about 21.6 GiB/s, reasonably rounded to 22. The kill figure
is evidence, not a universal bound. Synthetic one-thread averages 11.1–14.7
GiB/s fit that arithmetic; 2–8-thread averages 32–75 do not. Finite averages do
not bound allocation bursts or measure the frozen model. Rate times a stipulated
interval is illustrative growth, not observed controller overshoot.

Timestamp the preceding successful observation and the source/consumed tick,
kill and verified extinction; report the complete interval for ordinary stops
and first/later stalled sampling and recompute the conditional margin. State
ordinary scheduling/observation assumptions honestly. Include the guardian in
the whole-task aggregate. No universal allocator guarantee or privileged kernel
limit is required. Faster growth, pressure/cap failure or overshoot still stops
and invalidates the qualified fit claim; no Stage B authority follows.

## Question 3: revocation and guardian limits

The bounded parallel revocation and disclosed incomplete-write/power-loss
limitation are acceptable scoped engineering limits. Correct the statement
that neither operation is directory-fsynced: a successfully returned tombstone
write goes through `controller:470–474,191–192` to the file-fsync, rename and
directory-fsync writer (`enforce:77–90`); marker unlink lacks a following
directory fsync. A failed/blocked write has the disclosed residual. The
finalisation thread can publish late; successful tombstoning rejects its marker,
while unlink alone need not prevent that late publication. If both revocations
fail/block, exit 75 needs explicit review and must not be described as a
successful transaction. This is not a new demand for crash-proof persistence.

The guardian's 300-second setup and cap-plus-five deadline, including its minimum
finalisation floor on exhausted resume, can be declared local operational limits.
It need not heartbeat-kill immediately in every inter-phase interval. They are
acceptable only with full tail accounting, retained failure and no unsuccessful
completion treated as PASS; they do not reset any cap or permit new forwards.
The natural uncovered/missing-evidence/closed-session paths in Stage A condition A
are implementation gaps, not explained by those declarations. The conditional
memory limit also needs the accurate timing statement in Question 2.

## Question 4 and scope carried forward

Both verdicts are negative, so this record supplies neither matching favourable
block nor execution/call approval. Address each package's list above and submit
its exact changed identity with targeted retained evidence. The owner's Stage A
gate decision remains separate; the reader still requires its existing approved
package and dated owner go. Passing either stage later does not approve Stage B,
CONF, interval adoption or cloud spending.

Prior construction exposure remains disclosed: this chat and helpers cannot be
blind naming readers. The full-bank R2 review at RSC `1ab20cd` retains its
`f2d1328` target-visible, concept-batched limitation and prior exposure; it is
not later blind calibration. Row 19 and the older hostile/length/review tasks
remain closed with their single reports. No prohibited plant/key, private audit
results or human outputs were opened; no old capture/refit/simulation/PC job was
restarted. Foreign changes in both repositories were preserved. One authorised
completion report is to be sent to Claude R052 after this record is committed;
receipt/logging belongs in the work item, not a second scientific verdict.

## Reproduced package identities (identification only; no attestation)

| Stage A field | Reproduced value |
|---|---|
| `criteria_sha256` | `677bfff3aa31041a2871bc73553578936d86e9022afd7ab638df2a35ddde2007` |
| `identity_sha256` | `c15a60f62334549adc93e4dfc953095937ae287f6354d17d8eec0ebd347093a2` |
| `plan_sha256` | `40aba7ecf4a4cc6cdb5b0a5d536e87f31b4945f6c98a94c0458808050342c74c` |
| `manifest_sha256` | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| `budget_sha256` | `914fa4156368a2278357bb870786dd568a09823c202b9bd9ea880f1fada80a5d` |

Inner execution identity: `ec14571c74b19cb9fabab731a02136c70d1167b94bdf332e301ecbeacf6c7ead`.

| Reader field | Reproduced value |
|---|---|
| `ai_reader_qual_set.json_sha256` | `27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302` |
| `ai_reader_qual_key.json_sha256` | `d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea` |
| `ai_reader_delivery.json_sha256` | `f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8` |
| `ai_reader_exec.py_sha256` | `6f24563f2f0101b37c5ffcd105a7009ee2fb7e940ddf8fefc9065f1c16bee62c` |
| `ai_reader_score.py_sha256` | `e22ff107e9cac6f7a8b67f7ac777bed9b600ca6f369b112170f7698c32c1bfe6` |
| `ai_reader_runtime.py_sha256` | `d71bc4843e91a2ff61b7e7e1395c3a381225a47c0eaa8aaa281a6479b634cb1f` |
| `ai_reader_journal.py_sha256` | `39a4c9eadd7acbc6ff50ad00e55f0f040d6124dc9be538348d1c23ab05674c2b` |
| `ai_reader_key.py_sha256` | `e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f` |
| `ai_reader_frame.py_sha256` | `cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8` |
| `ai_reader_qual.py_sha256` | `6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc` |
| `AI_READER_JOB.md_sha256` | `d2838ca8bbc21a0054765c4b11989760ccbe8c754c24a9988f7b25dc94d24da3` |
| `AI_READER_DESIGN.md_sha256` | `0431b2c4514f09053a3e0c7344048064b7a9ca5cfc62f488a950b186d33b8d0e` |
| `stage_a_guard.py_sha256` | `6788e8acdb8f660bf03805c84a8502e1d412adc160f5708eaf6854defc4c3136` |
| `enforce.py_sha256` | `2df67706564d9603949ba94350de719db453b64d54bb27b8cb0939d450366fce` |
| `memprobe.py_sha256` | `9ea4fa5ba37509377178097f00a8eb46718a2d5c971d6a06dbea61ddbb5d3641` |
| `stage_a_watchdog.py_sha256` | `1ce89be37693d303ae0b727521906f3f194c91122d6c5f5fde306205477f159a` |
| `codex_realpath` | `/opt/homebrew/Caskroom/codex/0.159.3/bin/codex` |
| `codex_sha256` | `4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878` |
| `codex_package_json_sha256` | `8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121` |
| `cli_version` | `codex-cli 0.159.3` |
| `sandbox_exec_sha256` | `58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8` |
| `command_template_sha256` | `031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba` |
| `instructions_sha256` | `e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790` |
| `package_digest` | `68012501998ae14dd9cd24ce1edc593b8ccb725ac6d4fb7b4a204820ba5fbc05` |
