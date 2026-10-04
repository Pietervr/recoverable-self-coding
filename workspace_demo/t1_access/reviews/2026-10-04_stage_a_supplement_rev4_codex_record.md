# Row-20 OS-bridge supplement revision 4 — persistence of release evidence

Date: 3 October 2026 (Phoenix; 4 October UTC filename). Reviewer: Codex,
`GPT: R052 Entropy paper`.
Brief: Unimog `aa2c2c24d1cf6db580fdc931757fffa7cd6c9de8`,
`prompts/2026-10-04_codex_r052_supplement_rev4_review.txt`,
SHA256 `d030f7e0cb34ab4d875f6904f7682b2e81cf380cf2e0764602234e76429ae278`.
Ownership: Unimog `a385cc78`; incoming handoff
`53e25828-b90a-5c6f-943a-c525c516ba35` accepted before review edits and delegation.
R084's accompanying brief was read only in its requested supplement/suite part.
Candidate: `280604d28c301f3c13fac683370b5128080d79ce`.
Execution identity: `e2a4a09d8b118017903fd44866a49846f652d0dea45ff169944f289f0e96734d`.
Source lines below refer to this candidate under `stimuli/photo/`.
This answers the supplement half of [the prior record](2026-10-04_stage_a_supplement_rev3_codex_record.md).
Reader qualification/results, accepted science, base Stage A, row19 and old
matcher reviews remain closed.

## Verdict

**NOT FAVOURABLE to this exact supplement revision-4 package as declared.**
The direct `released=False` predicate and mandatory-peak repair are correct.
A remaining **P2** persistence path can erase that pre-GO endpoint record:
an older gates I/O snapshot can be written after the endpoint's persist and GO.
A crash before other start evidence lands can then permit a new endpoint
session, contrary to the declared no-post-start-dispatch rule.

This is a source-supported scheduling/crash interleaving, not an executed
reproduction, observed forward, lost charged attempt or replay of a completed
endpoint. The simple schedule need not yield an eventual PASS; renewed endpoint
dispatch is sufficient for the finding. Prior independent terminal refusal,
same-session endpoint binding, carried accounting and comparator remain credited.

The owner's standing bridge go — "go on the bridge check if Codex is favourable"
— is preserved. It can bind to the first favourable exact package R052 verifies
without another owner turn. This record is negative, so that condition is not
satisfied by revision 4. No bridge forward or Stage B action follows from it.

## P2: write serialization does not preserve snapshot order

Revision 4 relies on the endpoint worker record as release intent: `_phase`
appends it with `released=False` (`1152–1155`), registers leader/watchdog,
persists it (`1168`), then writes/closes GO (`1170–1171`). The flag is set true
only in memory afterward (`1172`). Counting any endpoint record in
`_prior_start_evidence:1373–1378` correctly closes the prior direct crash window
**while that record survives**. Including every endpoint record in mandatory
measurements (`1444–1455`) is likewise conservative and correct.

The existing persistence mechanism does not establish survival against an older
writer. `_persist:529–544` makes its JSON snapshot under `self.lock` at `535`,
releases that lock, and acquires `self.wlock` only at `539` before writing at
`540`. Snapshots can therefore be written in the opposite order from their
generation. The default atomic writer replaces the whole file, with file and
directory fsync (`enforce.py:79–96`); it neither merges worker records nor rejects
an older snapshot.

The gates sampler has a daemon I/O thread (`1249–1251`) calling `_persist`
(`1203–1215`). On phase exit `_sample` sets `io_run=False` and joins for only
`2 * HEARTBEAT_S` (`1314–1317`, two seconds), without checking that the thread
has ended or refusing phase progression if it remains alive. The main thread
can then finish gates and release the first endpoint.

One concrete permitted schedule is:

1. Gates I/O snapshots the open session with only the gates worker, then pauses
   after releasing the state lock and before acquiring the write lock.
2. Gates ends. Its timed join expires. Main completes the gates worker and
   persists its finished state (`1187–1191`); no live-I/O barrier prevents entry
   into the endpoint phase.
3. Main appends the endpoint worker, persists its identities and false record,
   then delivers GO/close (`1168–1172`). The intended durable release boundary
   has been crossed.
4. The old gates I/O thread resumes and replaces `controller.json` with its
   earlier gates-only snapshot (`539–540`). The endpoint record has disappeared
   through a normal controller write, without operator deletion or tampering.
5. The controller dies before a fresh endpoint heartbeat or first Budget attempt,
   DONE, pass output, comparison or terminal supplies another start trace.
6. Restart loads/reconciles/charges the surviving gates-only session
   (`287–317/499–527`). `_prior_start_evidence:1366–1385` has no endpoint trace;
   it does not discover endpoint intent by scanning standalone watchdog files.
   New gates and endpoint dispatch are eligible (`616–633`), although the prior
   endpoint may already have received GO.

An older snapshot taken during the gates sampler may lack the gates exit peak.
That measurement would later force STOPPED at finalisation (`1503`); it does
not prevent the new endpoint GO beforehand. Thus this simple path establishes
post-release redispatch, **not a guaranteed PASS**.

A measured-gates variant is also permitted: an old I/O iteration pauses in/after
its directory sum (`1208`) through the timed join; main finishes the gates
worker and its peak/reaped record (`1060/1072/1191`). Resume that already-entered
iteration before endpoint append, let it snapshot the now-complete gates state,
then pause before `wlock` while main persists/releases the endpoint. `_io`
checks `io_run` at loop entry (`1206`), not again before that snapshot (`1215`).
Its later replacement need not lose the gates peak. The constructed gates-only
control shows such a surviving history is eligible to run to PASS. An eventual
PASS still depends on the rest of the new run; it is not needed for this refusal.

`Budget.attempt:425–434` publishes an attempt before yielding to a forward.
A real forward with that durable evidence would be refused on restart. The
identified interval is before that attempt: this is the broader endpoint-release
rule and loss of the old endpoint's measurement history, not uncharged or
duplicated model work. Crash time charging remains credited. Recovery of the
lost endpoint group cannot be inferred from a gates-only worker list.

## Required closure before reconsideration

Make supplement release evidence monotonic across all its asynchronous writers.
For example, serialize snapshot generation and publication together so an older
record cannot overwrite a newer one; or prevent endpoint progression until every
old phase I/O writer is confirmed ended. A separate supplement-specific durable
release-intent record, published before GO and immune to these whole-record
replacements, is another option if restart and mandatory-measurement decisions
both consume it. A write after GO does not close the crash boundary.

Keep the accepted base Controller policy/package closed; implement a supplement
scoped repair or explicitly declare and review any wider package move. Do not
simply treat every gates-only history as endpoint evidence: genuine pre-endpoint
gate refusals remain a valid distinct case. Refusal must stay independent of
terminal-file publication.

Retain meaningful no-forward concurrency/crash fixtures with synchronization
barriers: an old gates writer delayed before write serialization, completed
gates, endpoint record persisted/GO crossed, then stale writer allowed to land
and a restart before other start evidence. Assert no new phase worker,
preserved/charged recovery time, mandatory measurement obligations and no new
receipt/final. Cover the measured-gates variant and genuine gates-only control;
if choosing separate intent, cover failed publication and both sides of GO.
Assert recovered leader/group/watchdog extinction before fixture teardown.
This is a persistence-class repair, not another scientific review.

## Closures, pins and bounds credited

The direct false-record histories now refuse even with a dead/live leader and
without a ledger or completed outputs. Terminal recreation remains best effort:
`_supersede` sets independent refusal before it, and gates/phase/final guards
prevent progress when a surviving start trace exists. Admitted PASS remains final.
Both endpoint commits must belong to the current session in controller, receipt
and row21; native requires its own session's instrumented commit. Direct old/new
and new/new comparison receipts, finite/bound checks and full compatibility
rederivation stay credited. These controls do not reconstruct erased intent.

Root reproduces all six package fields, the identity self-digest and 15 declared
source bindings, and checks 17 live bound files. Exactly criteria and supplement
identity package fields move from revision 3; the supplement plan, base plan,
manifest and budget are unchanged. The revision-4 production diff is confined to
SupplementController; inherited persistence/sampler code is unchanged.
Parent stays bound to `cc1d2cb`, internal identity
`1d017dcefd1e810df77a2e643a03b9ffbdcf01e711cf47cd3ae5290d6fd2c727`.
Parent-at-HEAD builder refusal is intended; supplement uses its own builder.
Parent pins cover eight metadata hashes, total bytes and reference outputs,
not a whole-tree digest. Accepted parent capture bytes were not reopened here.

Carry 194/193/1/194 starts/completions/failures/passes,
2,338.113973380568 seconds and 396,783,863 bytes remains charged. Two new starts
yield 196/195/1/196 of 200; row21 aggregate is 196+1,856=2,052≤2,056 without
adding parent 194 twice. Remaining storage 676,957,961 bytes; four hours/1GiB,
48GiB cap/44GiB stop and charged 60-second closure carry. Four spare starts are
not retry permission. Forecasts are implementer estimates, not new measurements.
This exposed input-00 sentry does not isolate OS causality, qualify all images or
edits, reproduce 120 shams, admit PILOT or approve Stage B.

## Retained suite and actual fixture coverage

Final [suite record](2026-10-04_photo_suite_supplement_rev4_run.md), RSC `f8876eb`,
HEAD `1ea0f7d1e698d9451d77af0eeb7207783e054a02`: 380 main collected = 337 OK
+ 43 skips; build 27 OK. Combined **364 passing executions, 353 distinct
executed cases, 11 repeats, zero failures/errors**. All 14 inventory sizes/hashes
match. The [first attempt](2026-10-04_photo_suite_supplement_rev4_run_first_attempt.md)
retains one reader-fixture failure, 363 passes, the same 353 distinct/11 repeats
and 43 skips; its 14 inventory sizes/hashes also match. Both runs pass all 41
supplement methods, including seven new Rev4 methods.

The first failure is `Rev13Reader.test_the_evidence_is_job_b_s`'s evidence SHA
assertion. Commit `1ea0f7d` selects only the archived job-(b) evidence, requires
its existence and keeps the expected digest, instead of also consulting the
live journal that the source says job (c) replaced. This is a verified test-only
source correction; bound reader production files/package are unchanged. Actual
live/archive journals and job-(c) results were not opened. The first record's
introductory retention-directory name points at the final directory; its actual
first-attempt inventory is present and matches. Preserve the failed receipt.

43 skips = 16 WordNet cases restored in build plus **27 Stage A transition
cases unexecuted** (five old and 22 moved). The brief's 22 parenthetical is not
the total. This suite is synthetic mechanism evidence, not fresh complete Stage
A transition coverage or actual supplement/environment qualification.

Seven Rev4 methods construct false endpoint histories, gates-only history,
missing-peak predicate and isolated pass/comparison/terminal traces. They do not
interrupt the real pre-GO sequence or order competing snapshot writers. Their
refusal/no-new-worker/crashed-session assertions for surviving endpoint records
are meaningful, but the following claims need qualification:

- The live-worker helper kills surviving sleepers in its `finally`
  (`tests/test_stage_a_supplement.py:782–783/773–777`) before the later PID-gone
  assertion (`801`). That assertion cannot independently attribute extinction
  to controller reconciliation; watchdog extinction is not separately asserted.
- Terminal-only history already has an active terminal; `_terminalise:1391–1393`
  skips its setter. A patched failing writer is not an exercised failure in that
  case. Pass/comparison-only histories do exercise the failure path.
- The exit-peak case is a direct predicate test; the gates-only case is a manually
  constructed state. Neither excludes the stale-snapshot schedule.
- Criteria §R4 still overstates no-worker assertions for every deletion/unreadable
  case: tests `672–679/690–696` assert refusal/reason only; the controller-record
  case additionally checks workers. Existing no-gates SystemExit/open session,
  foreign-session predicate and admitted-PASS pending-start limits remain stated.

Minor docstrings still say released workers where new code includes all endpoint
records. These are description qualifications, separate from the P2 blocker.
Passing fixtures prove their assertions, not every scheduler/crash interleaving.

## Review boundary and exact attestation

Three read-only peers reviewed source and named public synthetic evidence; root
integrated the competing-write path and independently checked Git/blob hashes,
literal AST metadata and package/identity/carry pins. No submitted module,
import/function, test/fake/fixture, CLI/provider/model/reader/forward, archive,
scoring or simulation ran. No actual capture/image/array/tensor, raw reader
response/journal, private-key semantics, human/plant/audit data was opened. No
remote/account/job action, worktree or push. Source owns code, current summaries,
captures/results/go/archive/dispatch; root owns this record and its own R052
append/lifecycle only. Foreign files and closed reports remain preserved.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A-supplement",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "280604d28c301f3c13fac683370b5128080d79ce",
  "package": {
    "supplement_criteria_sha256": "de85d58a0bbaf3c7c05374473a58a77cc705eb24aede0ed7f95b75774087ab45",
    "supplement_identity_sha256": "30aba1bae4166197f78e6120b3ef431874d0b840df09113071ab809bd00e6edc",
    "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"
  }
}
-->
