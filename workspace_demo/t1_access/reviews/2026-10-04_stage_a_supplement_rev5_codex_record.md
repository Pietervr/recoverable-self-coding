# Row-20 OS-bridge supplement revision 5 — independent intent and lost-group recovery

Date: 3 October 2026 (Phoenix; 4 October UTC filename). Reviewer: Codex,
`GPT: R052 Entropy paper`.
Brief: Unimog `03b4458f4b5214efe3455fe661b826d33af0ebee`,
`prompts/2026-10-04_codex_r052_supplement_rev5_review.txt`,
SHA256 `67ec765f351ab55b46e70b9c2141fd8d63d9a3035de864a7a8ada5fea716b796`.
The whole R084 companion brief was also read.
Ownership: Unimog `66e07d74`; incoming handoff
`6214d0ec-0912-504f-9778-8ee8869accdb` accepted before review edits/delegation.
Candidate: `c2a21504041a5b2d7e5ba68fddb7ddd9bcd0f00c`.
Execution identity: `6e5fd49852ccb05720fea2be2b3012baae596ebabf50370352e7fde19b976896`.
Source lines below refer to this candidate under `stimuli/photo/`.
This is the bounded follow-up to [revision 4](2026-10-04_stage_a_supplement_rev4_codex_record.md),
not a fresh review of reader results, accepted science, base Stage A, row19 or
closed hostile/length work.

## Verdict

**NOT FAVOURABLE to this exact supplement package, P2.** The independent intent
closes the previous stale-controller-snapshot endpoint redispatch blocker.
However, the new fallback can leave the old released group or recorded escaped
descendants running, and can retire its watchdog without confirming extinction.
Its complete recovery identity publication is also not checked before GO.
These are narrow supplement recovery obligations explicitly claimed by criteria
§R5, not a demonstrated second endpoint dispatch or over-budget PASS.

The owner's standing conditional go on the bridge check remains in force across
revisions. Its favourable-review condition is unsatisfied here, so this record
does not bind ROW20S_GO.json or authorize either forward. A first favourable
review of the exact package verified by R052 can bind without another owner turn.
No forward, retry, archive, scoring, model/reader call or remote job is performed
by this review.

## Credited closure at the release boundary

`write_release_intent` creates `intent/<phase>.json` using O_CREAT|O_EXCL,
then file and directory fsync (`stage_a_controller.py:165–183`). The supplement
override publishes after watchdog arming (`1508–1518`), before base `_phase`
persists and sends GO (`1204–1208`). The succeeding mandatory base `_persist`
also fsyncs the output directory before GO (`enforce.py:79–92`), sealing the
new intent directory's parent entry. There is no separate parent-fsync blocker
in this production ordering. Exceptions from the publisher stop before GO and
enter inherited gated-worker cleanup.

Whole controller replacements cannot rewrite or delete that independent intent.
`_prior_start_evidence:1419–1420` consumes any intent, including an unreadable
entry, and `_supersede:1451–1471` refuses independently of terminal publication,
before another gates/endpoint phase. Admitted PASS remains final. Genuine
gates-only refusal with no endpoint intent remains resumable. Thus the previous
late gates snapshot no longer makes another endpoint session eligible.

`_missing_measurements:1495–1500` also requires a positive exit peak matching
each intent's endpoint and session in its loaded/in-memory record. Lost endpoint
records on restart now retain that measurement obligation. Existing same-session
endpoint commits, native-after-instrumented ordering, comparison receipts,
finite/bound checks and row21 compatibility remain credited. A still-live final
disk-record limitation is stated below; the blanket durable-peak claim is not
credited without that qualification.

## P2: old resources are not always ended and confirmed gone

Criteria §R5 (`STAGE_A_SUPPLEMENT_CRITERIA.md:180–187`) promises recovery of
the intended leader group and watchdog even when their controller record is
lost. `_reconcile_intents:1521–1542` does not meet that promise:

- At `1527–1528`, it skips the leader if `same_process(leader)` is false.
  A leader can exit while a child remains in the recorded PGID. The accepted
  `memprobe.end_group:195–233` deliberately supports a departed leader: it checks
  PGID reuse, enumerates surviving group members and requires extinction. The
  new caller prevents this helper from running. An old gates snapshot, controller
  death, leader exit and surviving child suffice. With the watchdog already gone
  (as the submitted fixtures permit), the child is never reconciled; with a live
  watchdog, the helper can kill that safeguard after skipping the group.
- At `1531`, `end_group(ident, [])` ignores separately persisted member identities.
  The sampler discovers and retains descendants (`1316`, `1327–1328`), and
  `_persist` writes `members_<session>_<phase>.json` (`574`, `579`, name `1157`).
  An already recorded descendant that moves outside the original PGID is killed
  by `end_group` only when its identity is supplied (`memprobe.py:221–225`).
  The watchdog receives and consumes that members file (`1163`,
  `stage_a_watchdog.py:242`), but the new helper discards it before retiring the
  watchdog. This gap can matter even with a live original leader.
- At `1537–1539`, Survivors is logged and the loop continues to watchdog cleanup.
  Extinction has failed, yet its safeguard can be killed. The accepted base
  reconciliation holds on this error before retiring the watchdog (`535–563`).
- The watchdog loop ends at its time limit (`1535–1536`), then records
  `ended: True` (`1540`) without checking whether that identity is actually gone.

These are static source-supported counterexamples, not executed reproductions,
observed production orphans, lost charged forwards or claims of regenerated PASS.
New dispatch still refuses. The issue is continuation of the old released work
and the accuracy of the declared cleanup result.

Reconcile every valid intended leader through the existing identity/PGID reuse
checks, even if that leader has exited; include validated identities from the
independently saved members file. Retire the watchdog only after group/member
extinction is confirmed. On Survivors, uncertain evidence or timeout, retain
the safeguard as applicable, refuse/hold, and record cleanup as unconfirmed.
Require actual watchdog extinction before `ended: True`. This can be repaired
in the supplement fallback without changing accepted base policy.

## Complete publication and durable-record qualification

`os.write:174` is called once and its byte count is ignored. A short successful
write can leave partial JSON, be fsynced and return normally before GO. Its
unreadable entry still prevents a later dispatch, but cannot supply trustworthy
leader/watchdog identities after controller rollback. Ensure all bytes are
written and a complete recovery record is established before GO; fail before GO
on incomplete publication or file/directory fsync failure. Keep partial evidence
as refusal evidence and explicitly state unconfirmed cleanup. Valid non-object
JSON currently raises TypeError at `release_intents:192` rather than the claimed
structured refusal; it aborts before dispatch, so it is not another-start proof.

The six-point self-audit overstates universal durable peak-loss closure.
`_missing_measurements` reads `self.rec` (`1492–1500`), while `_finalise` hashes
the separately written disk controller record (`1605`). A delayed old `_persist`
can land after `_close`, while memory still retains endpoint peaks. Finalisation
can report no missing measurements and bind a disk hash whose endpoint records
are absent. `final_admitted:233–256` and `stage_a.supplement_receipt_ok:2118–2202`
do not independently rederive those disk endpoint peaks. Current final aggregate
time/peaks still come from intact memory: no undercharged or over-cap run is
demonstrated. Qualify the claim, or ensure the final durable record itself meets
the measurement/identity obligations without allowing an older publication to
replace the accepted evidence. Do not label every such durable loss STOPPED on
the strength of an in-memory predicate fixture.

Other whole-record claims remain bounded: ordinary stale open-session beats are
conservatively recharged by the existing crash-tail path, and intent refusal
prevents another endpoint. These new fixtures do not roll back beat/session-time
fields or assert a charged-time lower bound. The intent helper introduces no new
ledger writer; existing starts/commit/session predicates remain unchanged.
Intents are create-once. Other phase/final files use logical lifecycle guards,
not universally O_EXCL; final storage mismatch can rewrite STOPPED as already
declared. Guardian records have session/phase names but are updated within that
identity. These qualifications neither reopen accepted clocks nor supply a new
concurrency proof.

## Exact package, carry and retained evidence

Root independently matches all six package fields below, the identity self-digest,
15 declared source bindings and 17 live bound files. Against revision 4 exactly
criteria and supplement identity fields move; both plans, manifest, budget,
input00 and carry remain unchanged. Base Controller body/policy is unchanged;
the helper/class move changes its whole file hash. Parent-at-HEAD builder refusal
is intended; the supplement has its own builder. Parent remains `cc1d2cb`,
internal identity `1d017dcefd1e810df77a2e643a03b9ffbdcf01e711cf47cd3ae5290d6fd2c727`.
Its eight metadata hashes, total bytes and reference outputs are not a whole-tree
digest. Accepted parent capture bytes were not reopened.

Carry starts/completions/failures/passes is 194/193/1/194, with
2,338.113973380568 seconds and 396,783,863 bytes. Two new unique starts yield
196/195/1/196 of 200; four spare starts are not retry permission. Row21 combines
196+1,856=2,052≤2,056, without adding the parent 194 twice. Remaining storage is
676,957,961 bytes. Four hours/1GiB, 48GiB cap/44GiB stop and charged 60-second
closure persist. Forecasts are implementer estimates, not new measurements.
This exposed input00 sentry does not isolate OS causality, qualify all images or
edits, reproduce 120 shams, admit PILOT or approve Stage B.

The [retained suite](2026-10-04_photo_suite_supplement_rev5_run.md), RSC `64cbd04`,
names exact HEAD `c2a2150` and clean photo status. All 14 inventory sizes/hashes
match. Main: 386 collected = 343 OK + 43 skips; build: 27 OK. Thus **370 passing
executions, 359 distinct executed cases, 11 repeats, zero failures/errors**.
All 47 supplement methods pass, including six new Rev5 methods. Forty-three
skips comprise 16 WordNet restored in build plus **27 unexecuted Stage A
transitions: five old and 22 moved**. The incoming 22 parenthetical is not the
total. The retained revision-4 first failure and test-only correction remain
closed; reader production/package and actual job(c) results are not re-reviewed.

The six new methods (`tests/test_stage_a_supplement.py:861–979`) support their
actual assertions. The two rollback cases drive a real synthetic endpoint through
GO, kill watchdog/controller, then manually strip endpoint workers from the
post-crash current record. Their teardown asserts leader extinction before file
cleanup, closing the earlier attribution weakness. They do not pause/interleave
a real old `_persist` writer, regress clock fields or check descendants/watchdog
extinction. The peak case is predicate-only. The 'both sides of GO' case constructs
one ambiguous intent state, not two driven crash windows. Publication failure
patches the whole publisher to throw before creating evidence. Gates-only
resumption is exercised. Passing assertions do not establish omitted classes.

Before reconsideration retain synthetic cases for dead-leader/live-child with
live and lost watchdog, recorded out-of-group descendants, Survivors retaining
the safeguard, watchdog timeout without false success, and short-write/file-fsync/
directory-fsync failure before GO. Cover an actual delayed snapshot publication
and durable-final measurement obligation or precisely narrow the latter claim.
Assert original group/member/watchdog extinction before teardown, no new worker,
no receipt/final regeneration and conservative charged recovery. These are
mechanism fixtures, not permission to run the scientific supplement.

## Review boundary and attestation

Three read-only peers supplied scoped source/evidence findings; root integrated
them and checked metadata. No submitted code/import/function, test/fake/fixture,
CLI/provider/model/reader/forward, archive, scoring or simulation was executed.
No actual capture/image/array/tensor, raw reader response/journal, private-key
semantics, human/plant/audit data was opened. No remote/account/job operation,
worktree or push. Source owns code, current summaries, captures/results/go/archive/
dispatch; root owns this record and its own R052 append/lifecycle only. Foreign
files and all closed reports are preserved. No arbitrary operator deletion is
needed for the negative findings.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A-supplement",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "c2a21504041a5b2d7e5ba68fddb7ddd9bcd0f00c",
  "package": {
    "supplement_criteria_sha256": "5b8f7a20c484d46e1284e87078887c85a3d4bacdefa4084df294a780205e4226",
    "supplement_identity_sha256": "8f08c2d0b6d78b8f8054f3894a30996721830f9774fc5b94ebac832b9531d796",
    "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"
  }
}
-->
