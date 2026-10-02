# R052: Stage A and AI-reader revision-8 exact-package review

2 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.

**Verdict: NOT ON BOARD with Stage A execution or AI-reader qualification calls
at RSC `9f696c653f55df3409437d77836e5b7f74efdba1`.** This is the combined negative
record allowed by the brief; it contains no favourable attestation. Stage A A2/A3
close their previous counterexamples; A1 remains partly open. The reader's
repeated-start, same-ID and ordinary marker-timeout repairs are credited; reader
C closes its observation-cutoff paths. Reader B retains specific startup and
compatible-session admission gaps. Reader A's late-return/revocation window
exceeds the stated residual. Declaration corrections remain below. The owner's
Stage A gate question remains open; no alternate exception or go is adopted.
Reader calls still need a favourable exact-package review and dated owner go.

## Scope and evidence

Read the full revision-8 Unimog brief at
`4550c6ff84844c061175a0f39235dc33ccfee9cd`, SHA256
`627cddbd42d37f926a8c80b44a9ccd763661a118a4b1428b040d2275661c1ff6`.
Own review/log ownership was committed at Unimog `95ea9b6a`, then handoff
`82f31a4c-f2bc-5fd0-a7d3-68ec2276fc34` was acknowledged and registry-accepted
before review edits. Compare the completed revision-7 record
`12a7f20febe0bbac9661cd5b7904097b1a0b7cbe`; previous reviews are not restarted.

Stage A remains a native fidelity/resource screen: 160 mandatory forwards,
18 planned diagnostics and 16 carried engineering attempts, 194 of 200;
1,808.73 seconds carried. The reader retains 300 paired items, 600 responses,
at most 660 attempts and six hours. Its grayscale admission panel remains
63 easy items requiring at least 61 correct. Neither package grants Stage B
authority or scientific interval adoption.

Read the pinned criteria/readiness, controller/watchdog/guard/enforcement,
reader design/job/executor/runtime and affected fixtures, prior review and owning
framework §§8.2/8.4 and ledger row 20. Three independent static helpers examined
startup, reader and integration paths. Citations below are exact-package lines
relative to `workspace_demo/t1_access/stimuli/photo/`. No submitted module,
program, test, fixture or CLI was imported or executed. Only static git/blob/AST,
JSON, hash and deterministic metadata arithmetic were used. No image was opened
or named, model called, capture/forward/fit/simulation launched, account operated,
worktree created or push performed. Source R052 owns framework/ledger/protocol/
dispatch; R084 implementation; Codex this review and its own work-item log.

All five Stage A hashes, inner identity and identity-to-source/map/receipt/packet
relations, plus all 24 reader fields, were independently reproduced from the
committed blobs and existing binary/manifest/sandbox bytes. The CLI version is
the saved value; its binary was hashed, not executed. Plan, manifest, budget,
reader set/key/delivery/template/instructions are unchanged from revision 7;
no scientific population, alias, model, draw or cap change is requested.

The retained suite record and all ten output files at RSC `d26cb8e6e61a4e8520175ace00b72f4a83d4ad30` were inspected;
every listed byte count and SHA256 matches, including empty stdout and status.
HEAD is exactly `9f696c653f55df3409437d77836e5b7f74efdba1`, photo status clean,
17:49:03–18:20:42 UTC. The main log shows **247 tests in 1897.130 s, OK with five
WordNet skips, exit 0**; the separate build run shows **five WordNet tests in
0.672 s, OK, exit 0**. Those five are full-form S1, inflections, key rebuild,
specificity and synonym residue. The new Rev8 tests total eight (two runtime,
six crash); controller classes total 47 (31 Controller, 12 Finalisation,
four Startup). This is implementer evidence, not a new Codex test run. Passing
these fixtures does not cover the additional transitions identified below.

## Question 1: six submitted conditions

| Condition | Disposition |
|---|---|
| Stage A A1: pre-pending failed start | Timeout plus already-committed guardian death is repaired; healthy-guardian external controller death and unresolved receipt publication remain. |
| Stage A A2: deadline extension | Closed for the prior long-first-persist trace: pending deadline durable before extension; recorded-death and missing-death recovery checked. |
| Stage A A3: interrupted reconciliation | Closed for the prior repeated-failure trace: earlier pending entries retained until first successful clock persist, then deduplicated. |
| Reader A: marker timeout | Ordinary stalls with effective revocation repaired; late-return publication after early unlink can escape the currently stated two-blocked-steps residual. |
| Reader B: startup and session relation | Repeated starts, elapsed setup, same-ID dedup and missing/duplicate session refusals credited; initial pending publication, recovered remaining-time bound and undeclared session statuses remain. |
| Reader C: observation cutoff | Closed for the exit probe and in-loop/fallback evidence timestamps; correct the fixture's equivalence-positive description. |

### Stage A A1: healthy guardian can leave an uncharged start

The process-start origin now reaches the guardian (`stage_a_controller.py:443–445,
531–534`). Its timeout record includes that origin (`stage_a_watchdog.py:142–146`),
and recovery charges every unaccounted guardian JSON start exactly once
(`controller:325–353`). The new pre-pending directory/lock fixture
(`tests/test_controller.py:525–552`) genuinely checks full recorded start-to-death
charge, 2.021/2.014 seconds, and no double charge on a further restart.

However, the guardian's ordinary controller-death branch **returns silently**
(`watchdog:127–129`). Kill the controller while directory creation/lock is stalled,
before pending publication and before the guardian deadline. A healthy guardian
observes the death and exits without a record. No pending/open session identifies
that protected start. Recovery permits a carry-only base or the existing closed
clock (`controller:222–236`), and its pending/guardian scan has nothing to charge.
Renewed work can therefore omit that machine-up startup interval. This does not
require the disclosed case of a guardian that also died before recording.

The timeout path has a related publication window: it kills the controller before
writing its receipt (`watchdog:145–146`). Recovery can run while that guardian is
still writing/fsyncing; only committed `guardian_*.json` is scanned
(`controller:340`), and `_load:223–224` excludes all guardian-prefixed material,
including a temporary receipt, from the lost-accounting hold. The new fixture
reads the completed receipt before starting recovery, so it does not test this
transition. A later receipt may be charged at a later restart; it does not make
the intervening run's current budget complete.

Preserve charge or a conservative hold for a known protected start across an
external controller death and unresolved guardian publication. Retain targeted
recovery evidence for those transitions. This is A1's existing bounded engineering
condition, not an infallible storage, scheduling or kernel guarantee.

### Stage A A2/A3: previous paths closed

`controller:479–484` commits the extended deadline in the accumulated pending
entry before sending it to the guardian. `_failed_start_charge:294–319` uses the
matching recorded death, otherwise the durable same-boot deadline plus grace.
The existing-closed-clock/first-persist-before-rename test (`tests:554–589`) checks
both death-present and death-deleted branches, 11.016/11.727 seconds. A2 closes.

Pending writes now retain earlier entries (`controller:277–292,468–491`); removal
occurs only after the controller persist containing their charges. Known session
IDs prevent a second charge (`:325–337`). The real S2 exit after load but before
persist leaves supplied honest S1 pending evidence intact; S3 charges both
(`tests:591–615`). This is meaningful evidence of the interrupted transition,
though S1's initial state is supplied rather than produced by another crash.
A3 closes. The corrected open-tail ≥60 seconds versus same-boot failed-start
actual interval, possibly below 60, is accurate.

### Reader A: credit the commit-point repair, finish its late-return scope

The marker is file-fsynced under a temporary name; its rename is the last operation
and runs through the final deadline lock (`ai_reader_exec.py:193–207,528–550`).
A fully returned commit wins; a deadline that wins or waits beyond the 0.5-second
grace latches `fired`, starts bounded tombstone/unlink revocation, then exits.
The 59-second timer leaves the stated grace/revocation inside the charged 60.
Admission refuses a matching tombstone (`:1043–1055`). Infinite pre-/post-rename
stalls, normal close, matching tombstone and other-session control are genuinely
covered (`tests/test_ai_reader_crash.py:497–530`). The old ordinary marker
post-rename directory-fsync stall no longer exists.

One narrower-than-declared residual remains. A commit stalls **before** rename;
the timer cannot acquire its lock, sets `fired=True`, and starts revocation.
The tombstone write blocks, while unlink succeeds because no marker exists yet.
The commit then resumes and renames the marker **after that successful unlink**.
`Deadline.commit:545–550` does not recheck the fired latch after `fn()`; it marks
the commit successful. `_run:752–757` calls `Timer.cancel()`, which does not stop
a callback already running, and can return. A matching marker with no tombstone can qualify, either before
the daemon callback exits 75 or after normal main-thread exit terminates it.
This needs one blocked tombstone writer and a late rename, **not both revocation
steps blocked**. The infinite-stall fixture never releases the commit into this
window.

Finish the fired-deadline/late-return refusal and cleanup, with a finite-release
control, or explicitly correct and qualify this broader ineffective-revocation
residual. The previously accepted candid filesystem limits remain; a universal
crash-proof transaction is not requested. Credit the repaired healthy-revocation
paths without claiming the stated two-blocked-steps scope is exhaustive.

### Reader B: three bounded gaps after the credited repairs

Each successfully published start now owns its pending file and shares its ID
with the clock session (`exec:622–668`). Earlier files are absorbed at first clock
persist before deletion (`Clock:249–279`); repeated failures preserve both starts,
and a crash after first persist charges once. Elapsed old-clock read is subtracted
from the setup allowance. Missing/duplicated journal-session mutations are refused
(`:1080–1095`). The six real-process Rev8 cases (`crash:497–618`, four B cases at `:532–618`) substantiate
these repairs.

1. **The initial pending write itself.** `Job.run:632` calls the atomic writer
   before the lock, but that writer creates `.json.tmp`, writes and file-fsyncs
   before rename (`enforce.py:79–95`). A setup-timer kill or ordinary SIGKILL while
   a readable pending temporary file waits at fsync/rename leaves startup evidence
   that `exec:654–665` never reads: its glob accepts only completed `.json` names.
   Later `check_accounting` does not hold on this temporary evidence. Repeated
   starts can omit those intervals despite a readable earlier clock. This exceeds
   the disclosed directory-creation/no-trace case. Recover or conservatively hold
   on incomplete publication evidence and state any genuinely unobservable
   publication residual accurately; do not reset known startup time.
2. **The shortened timer omits recovered charges.** `exec:639–652` computes the
   setup balance from only `clock.json.seconds_total`, before `Clock:229–267`
   absorbs an open crashed session and prior pending starts. Its guard is started
   only **after** first persist returns (`:275–279`). Example under the 21,600 s
   cap: saved base 21,250 s, open live 300 s plus the 30 s tail; recovery leaves
   about 20 s. The earlier calculation sees about 350 s and keeps the 300 s setup
   timer. First persist can block under that timer with the full recovered balance
   already known in RAM but no cap guard running. This is a bounded cap overrun,
   not a new naming call with a wrong balance: successful Clock return uses the
   reconciled total and subsequently holds/stops. Bound the first persist by the
   full recovered remaining allowance, including pending/crash charges, rather
   than only the earlier closed base. Retain a near-cap recovery/blocked-first-
   persist case; no scientific request is needed.
3. **"Ran" accepts undeclared closed states.** `clock_problems:168–188` does not
   validate the historical session's `closed` domain. `_admit_clock:1074` uses
   `charged_s` only for literal `crashed`/`failed_start`; `:1091` calls every other
   state a session that ran. In a valid multi-session COMPLETE, change an earlier
   `crashed` status to an undeclared string, reduce the total by its removed tail
   and rehash the marker. Its ID still covers the journal open session, its live
   value is well typed, totals sum and the last COMPLETE remains unchanged; the
   altered clock can pass when the remaining total still exceeds attempt time.
   Require declared compatible status domains and their corresponding charge
   semantics. This finishes the requested bounded session relation; it does not
   authenticate otherwise self-consistent historical wall times.

The lock-contender race can conservatively add an extra failed-start charge and
cause a hold; it does not authorize an extra request and is not another admission
gate here. Unknown/unavailable storage can remain a stated residual; the concrete
readable-evidence and known-balance paths above need charge/hold coverage.

### Reader C: observation cutoff closed, fixture claim narrowed

`LocalCommand.poll` timestamps exit after the probe (`runtime:268–270`). Both
in-loop and fallback reads must complete their read/search before the deadline,
and only that saved observation text is parsed for the receipt (`:398–430`). A
late observation sets timeout. The post-cleanup `run_local` output read remains
valid in scope: the group is extinct and reaped, so its evidence is a timely exit
and stable bounded bytes, not a new live evidence observation.

The new tests genuinely exercise a late exit probe and an already-exited command's
late fallback (`tests/test_ai_reader.py:1413–1430,1432–1475`). The fallback control
passes the timing/readability check, but **does not establish an equivalent=true
receipt**: its `LOGS:1400–1405` uses content `[x]`, model `m`, empty feature tags;
the call uses the actual configured reader and image/prompt. The test discards
the returned receipt and asserts only that the error does not name deadline or
unreadable content. Correct the "equivalence-positive" comment/brief description;
a full matching positive control would strengthen that fixture. Static code and
the separate retained Boundary invocation/equivalence check support closure of
C's actual cutoff repair. This is evidence-description precision, not another
scientific run or reopened boundary mechanism.

## Question 2: declaration alignment and negative list

The requested main corrections are present: the interval table separates ordinary
preceding-reading, deciding-reading, blocked-I/O deciding-iteration and first-hang
pre-GO baselines; current pinned rates/delivery match; older ~22/0.1 memory
paragraph is historical; A4 and final `time_scope` distinguish finalisation 50
from whole charge 60; suite pointer names revision 8; D distinguishes both-route
authority tests from shared-checker membership tests and admits stale counters in
two variants; the failed-start floor is accurate. The shared guard and reader's
supplementary negative lists actually include `b569f8a`, `c036c00`, `12a7f20`
(`stage_a_guard.py:61–62`, `exec:128`); absence of a positive matching attestation
remains the general refusal. No new schema/attestation objection is raised.

The about-21 GiB/s local qualification remains accepted under the prior stated
scheduling/current-ledger/kill-delivery assumptions. Revision-8 pinned endpoints:
ordinary preceding reading → kill/leader/extinction 0.0224/0.0288/0.062 s;
deciding reading → leader 0.0064; blocked I/O deciding iteration → worker 0.0088;
first-hang pre-GO → consumption/observation/group/controller
0.0104/0.1586/0.1838/0.1948; third-hang preceding reading → same
0.0054/0.1528/0.1779/0.1905. Delivery 0.0273 gives `4/(0.16+0.0273) ≈ 21.4`;
latest endpoint gives `4/0.1948 ≈ 20.5`. Synthetic averages are
13.63/32.29/53.68/75.22 GiB/s: one thread fits, others do not. These are local
observations and finite averages, not burst bounds or frozen-model measurements.
The stated revision-7 working-file/pinned-file attribution correction is accepted.

Alignment is still incomplete in summaries and residual descriptions:

- Readiness `:24–25` labels all four timing paths from a previous successful
  reading; first-hang and blocked-I/O baselines must use the owning table's labels.
- Criteria `:34–35` says every quoted value comes from the revision-8 file, but
  older §00 A/B examples retain 2.7/10.8/9.7 s and 57.9 MiB against current
  2.778/11.173/10.283 and 58.4. Explicit historical attribution suffices; this
  incidental bookkeeping does not undo memory closure or require a rerun.
- Controller observation prose `:31` and criteria A3 `:161–162` still state 0.1 s
  tick staleness; current constant is 0.15. Update or mark the old statement
  historical. Criteria current limits `:342` and readiness `:47` still conflate
  60-second whole closure with 50-second finalisation allowance.
- Stage A's no-trace residual omits a healthy guardian's silent death branch;
  reader startup residual omits readable incomplete pending publication; reader
  marker residual omits late rename after a successful early unlink. Correct
  those claims alongside the scoped control dispositions above.
- The reader fallback fixture is timely-parse-positive, not equivalence-positive.

## Question 3: disclosed pre-commit STOPPED observation

**Acceptable as an unresolved disclosed observation; it is not proof of resolution
or a new independent admission failure.** The known unretained run saw STOPPED
where this fixture expected COMPLETE, with its reason absent. The other truncated
run has an unidentified crash-module failure: the retained material cannot prove
it was the same failure a second time. Describe one identified observation plus
one unidentified failure, rather than assert their identity.

A STOPPED receipt is non-qualifying; a resumed job dispatches no further reader
calls once a receipt exists (`exec:717–718`), while clock completion bookkeeping
continues after its write. Scientific admission requires a valid COMPLETE. Thus the observation could
be a conservative early stop or an underlying error; it does not show promotion
of invalid evidence, reset, or permissible retry of an answer. It can affect
availability and must remain visible. The later repetitions are source-reported,
not retained original-failure evidence; the exact retained 247-test run passes
this fixture, its closed-clock failure/stall branches and controls. Do not claim
the cause is known or the intermittent observation is resolved from those passes.

Evidence to settle it: retain any recurrence at the exact commit with full command,
test/subtest identity, exit status and stderr, receipt reason, bounded journal,
clock/marker/tombstone state and the relevant cleanup/watchdog records, excluding
credentials and images. The new assertion (`crash:428–429`) prints reason plus
driver stderr and is useful. A retained causal diagnosis with a targeted regression
would settle a code defect; an identified environmental/fixture cause must likewise
be supported by the actual receipt/evidence. No blanket repeat of the unchanged
green suite or scientific call is required merely to erase this disclosure.
This reader-only observation supplies no Stage A failure by itself.

## Question 4: exact remaining list and scope

Stage A: finish A1 charge/hold across healthy-guardian pre-pending death and
unresolved guardian receipt publication; align the specified timing/allowance/
attribution summaries. A2/A3, prior B/D, the 60-second closure and conditional
about-21 GiB/s qualification remain credited.

Reader: finish B's incomplete pending publication, full recovered balance before
blocking first persist and declared compatible session states; repair or explicitly
qualify A's finite late-return/ineffective-revocation window; correct those residual
and fixture descriptions. C and D remain closed in their stated scopes. Keep the
pre-commit observation honestly unresolved unless causal evidence settles it.

No favourable block or launch/call authority is issued. A changed exact package
may be resubmitted; no draw, alias, model, CLI, scientific rule or budget expansion
is requested. Source ownership and owner's unresolved gate decision remain.
Construction exposure persists: this chat/helpers cannot be blind naming readers.
Earlier full-bank R2 at `1ab20cd` retains the `f2d1328` target-visible,
concept-batched limitation and prior exposure, not later blind calibration.
Row 19 and old hostile/length assignments/reports stay closed. No prohibited
plant/key, private audit/human outputs or old job was opened/restarted. Foreign
changes were preserved. One authorised completion report follows this record's
commit; its actual receipt belongs in the work-item log.

## Reproduced identities (identification only)

| Stage A field | Reproduced value |
|---|---|
| `criteria_sha256` | `a17bdbbfc5a42d0ee7e52518029a79440f7594734867435a42a87bafc4b6077f` |
| `identity_sha256` | `86320c18ee5e5ea27bfba4016ecea0d46a372ee7bc7bcce507eb4798dc2d2807` |
| `plan_sha256` | `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc` |
| `manifest_sha256` | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| `budget_sha256` | `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f` |

Inner execution identity: `1c7beaa2c5c396ac9001fd40e85ed3cf912fbf3dd94a3b4884739d489926bdd3`.

| Reader field | Reproduced value |
|---|---|
| `ai_reader_qual_set.json_sha256` | `27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302` |
| `ai_reader_qual_key.json_sha256` | `d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea` |
| `ai_reader_delivery.json_sha256` | `f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8` |
| `ai_reader_exec.py_sha256` | `d7f0d28ad92cf5dcfbf066a3c63e20c89aed5440cec71dd16f82e56bf86c7b46` |
| `ai_reader_score.py_sha256` | `c66e6183f41a48dd9ac6aa2d15d5d952a5a0f0b5c15d842f594c11bf91f0aeaf` |
| `ai_reader_runtime.py_sha256` | `96235ea8e276b49ee671437776ee45d49a0249db70ce69b17849881fd4cac89e` |
| `ai_reader_journal.py_sha256` | `e067889c4210b91ec220fbd4f63421fb93fc4fd64f14c398f288fcaa3bcf2907` |
| `ai_reader_key.py_sha256` | `e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f` |
| `ai_reader_frame.py_sha256` | `cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8` |
| `ai_reader_qual.py_sha256` | `6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc` |
| `AI_READER_JOB.md_sha256` | `cb9a4176410bb32a27e2ab2c35efeb4efbd02f1288cfde4d455af85d5df43e1d` |
| `AI_READER_DESIGN.md_sha256` | `2d2b8869a67f8edd4dc81d6474d57c641b637da814e12e86952913528ec9c8eb` |
| `stage_a_guard.py_sha256` | `519a6cd5b6da6f2281a5ca6c13df793c7f3f20efe41e9af283329909d7458e5e` |
| `enforce.py_sha256` | `5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42` |
| `memprobe.py_sha256` | `83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465` |
| `stage_a_watchdog.py_sha256` | `5e663afc8ba7c548cb67955b4573c5d8751980f19fec3467479f34cc5b096728` |
| `codex_realpath` | `/opt/homebrew/Caskroom/codex/0.159.3/bin/codex` |
| `codex_sha256` | `4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878` |
| `codex_package_json_sha256` | `8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121` |
| `cli_version` | `codex-cli 0.159.3` |
| `sandbox_exec_sha256` | `58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8` |
| `command_template_sha256` | `031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba` |
| `instructions_sha256` | `e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790` |
| `package_digest` | `9b7aecf96464b6f87689db4e77bb83521cfa9fb04d3174ddcb96f8cd2f493097` |
