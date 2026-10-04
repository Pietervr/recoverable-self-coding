# Row-20 OS-bridge supplement revision 6 — favourable with declared limits

Date: 4 October 2026 (Phoenix). Reviewer: Codex, `GPT: R052 Entropy paper`.
Incoming brief: Unimog `4672813db632eac0b4e9ed516ca222b25767989d`,
`prompts/2026-10-04_codex_r052_supplement_rev6_review.txt`,
SHA256 `c269d683b5d2179971ce456fac410f5bcf351b3d811cf84ef38f890ee6b3688e`. The whole R084 companion brief was read.
Ownership: Unimog `cacfd2cf`; handoff
`601dce05-f120-5b51-b15d-d829a64446ca` accepted before review edits/delegation.
Exact candidate: `5f08728fcf77281627984e3f93b9f33621bee71a`.
Execution identity: `98bd31392b1d0277201e05a9320b9b163155549fded6edfd2e4936ae3829d859`.
Source references below name this candidate under `stimuli/photo/`.
This answers [revision 5](2026-10-04_stage_a_supplement_rev5_codex_record.md);
accepted science, base Stage A, reader/results, row19 and old reviews stay closed.

## Verdict and review standard

**FAVOURABLE to this exact supplement package, with the declared limits below.**
Revision 6 repairs the concrete revision-5 cleanup, publication and durable
endpoint-peak findings. No source-supported path was found to another endpoint
session after a start, a wrong comparison, or an admitted supplement PASS without
its required endpoint evidence.

R052 explicitly requested that a crash/recovery path whose consequence is only
unfinished/unconfirmed cleanup or STOPPED be recorded as a declared limit rather
than a further blocker. I apply that distinction here on its technical merits.
This does not establish an implicit new owner approval or waive wrong-result,
redispatch or false-admission defects. The remaining limits concern failure
completion and the extent of evidence, not a discovered successful-admission path.
They are **declared limits in this favourable record**, not required repairs before
the two-forward check.

The owner's existing standing bridge go remains in force: it can bind to this
first favourable record on the exact package R052 has verified, without another
owner turn. Source owns ROW20S_GO.json binding and dispatch. This record covers
only the original input00's one instrumented and one native bridge forward under
row20's carried envelope. It supplies no measured bridge result, retry authority,
new input/tolerance search, CAL/PILOT admission or Stage B go. The reviewer runs
no forward and binds no go file.

## Concrete revision-5 findings closed

**Lost-group recovery and safeguard retirement.** `_reconcile_intents`
(`stage_a_controller.py:1581–1627`) now calls the accepted `memprobe.end_group`
for every valid intent even when its leader has departed. That helper's PGID reuse
checks, surviving-group enumeration and supplied member identities remain the
accepted mechanism (`memprobe.py:195–233`). The new caller loads valid saved
member identities (`1595–1606`), covering recorded descendants outside the group.
Unreadable JSON members or Survivors produce unconfirmed cleanup and continue
before watchdog retirement (`1601–1611`). Only a confirmed group reaches watchdog
kill/poll, and liveness is checked again before `confirmed/ended: True`
(`1612–1627`). The refusal records UNCONFIRMED where that explicit branch occurs
(`1513–1524`). The former dead-leader skip, discarded available saved members,
retirement after Survivors and unchecked timeout success are closed.

**Complete publication before GO.** `create_once:168–189` exclusively creates
the file, loops until every encoded byte is written, rejects no progress, fsyncs
file and directory, and checks exact read-back bytes. `intent_problem:192–206`
requires the declared object fields, valid leader/watchdog identities, endpoint
phase and members-file name. `write_release_intent:209–224` checks before writing
and after reparsing. The supplement publishes after watchdog arming and before
the base persist/GO (`1568–1579`, `1262–1266`); exceptions stop before GO.
`release_intents:227–240` preserves partial/non-object evidence as structured
unreadable entries. A failed publication cannot imply fresh-start eligibility.
The mandatory following base persist seals the output directory before GO, so
there is no independent missing-parent-fsync blocker in that production order.

**Durable endpoint measurement evidence.** `_finalise:1666–1670` holds the same
write lock as `_persist` across finalisation. `_finalise_locked:1677–1680` reads
actual disk bytes, checks intended endpoint peaks by phase and session, and
creates an exclusive exact-byte `controller_at_final_<session>.json` copy. A
missing durable peak joins mandatory missing measurements and prevents PASS;
the final binds that copy's name/hash (`1687`, `1703–1704`, `1713–1717`). If an
old snapshot lands first, those bytes are checked and loss yields STOPPED. If it
lands after the lock is released, it can change live controller.json but cannot
replace the bound copy. Row21 rehashes and rederives intended peaks from the copy
(`stage_a.py:2140–2149`). The still-live memory-versus-disk endpoint loss from
revision5 is therefore closed.

The new copy is counted in final storage. Copy/read/create failure or blocked
finalisation can leave admission unfinished; a storage fixed-point mismatch
rewrites STOPPED without its admission marker. Generic `final_admitted:291–314`
checks the marker/final byte hash, final session and abort; it does **not** alone
validate the controller copy. Complete evidence admission is the production
finalisation plus row21 verifier, whose receipt/session/ledger/record/comparison/
compatibility checks remain in force. A marker-only helper call is not a complete
supplement validation.

## Declared operational and evidence limits

- Recovery confirms the enumerated group and available **valid recorded member
  identities**. A missing members file is treated as empty; a valid JSON container
  of the wrong shape or invalid entries can be filtered rather than explicitly
  labelled UNCONFIRMED (`1597–1602`). Member files are separately saved snapshots,
  not an append-only membership journal. An older same-phase writer can regress
  that evidence; an escaped descendant never recorded, omitted, lost or malformed
  is not proven recovered. The helper's confirmation must not be described as
  universal extinction of every possible descendant. The independent intent
  still forces restart refusal, with no new worker/comparison/final regenerated.
- Unexpected permission, process-observation, directory-iteration or durable-read
  errors can abort before a graceful refusal/UNCONFIRMED/STOPPED object is written.
  They do not fall through to a new worker or successful final in the inspected
  paths. A safeguard already absent cannot be kept; explicit unconfirmed-group
  recovery means the caller does not deliberately retire an existing safeguard.
  This is limited failure recovery, not a promise of completion after arbitrary
  storage/process failure or power loss.
- Partial/exclusive publication failure can conservatively consume the version
  and leave it unable to resume. A pre-GO intent is deliberately treated as a
  possible start. Whole-tree operator deletion remains the stated external
  residual; it is not a new submitted production path or a correctness guarantee.
- The durable-copy addition checks intended endpoint exit peaks. Other final
  resource figures still come from intact controller memory and are retained in
  the final; this is not an independent new rederivation of every resource/time
  field from that copy. Session-time rollback is **not newly fixtured**, as §R6
  now states. The unchanged accepted crash-tail accounting remains credited.
  Lifecycle-guarded outputs are not universally O_EXCL; a declared storage
  mismatch can rewrite the final STOPPED, and guardian records update within
  session/phase. No universal writer-order proof is claimed.

Under the expressly requested bar these limits can leave cleanup or the check
unfinished, or STOPPED; no concrete route through them to redispatch, wrong
comparison or successful evidence-free admission was found. They are retained
openly rather than asserted to be absent. Further hardening is a separate future
change, not an additional gate imposed by this record.

## Exact package, accounting and scope

Root independently matches all six fields below, the identity self-digest,
15 declared source bindings and 17 live bound files. Compared with revision5 only
criteria and supplement identity package fields move; supplement plan, base plan,
manifest, budget, input00 and carry remain fixed. Moved production files are the
supplement helpers/subclass in stage_a_controller.py and row21 verification in
stage_a.py; the base Controller body is byte-identical. Guard, watchdog, memprobe,
enforce, comparator and report policies are unchanged.

Parent remains bound to `cc1d2cb`, internal identity
`1d017dcefd1e810df77a2e643a03b9ffbdcf01e711cf47cd3ae5290d6fd2c727`.
Parent-at-HEAD builder refusal is intended; supplement uses its own builder.
Parent pins cover eight metadata hashes, total bytes and reference outputs,
not a whole-tree digest. Accepted parent capture bytes were not reopened here.
Reader revision17/package and its prior favourable record remain closed.

Carry starts/completions/failures/passes is194/193/1/194, time
2,338.113973380568 seconds, storage396,783,863bytes. Two new unique starts give
196/195/1/196 of200; four spare starts are not retry permission. Row21 combines
196+1,856=2,052≤2,056 without adding parent194 twice. Remaining storage is
676,957,961bytes; four hours/1GiB, 48GiB cap/44GiB stop and charged60-second
closure persist. Forecasts are implementer estimates, not new measurements.
This exposed one-input bridge does not isolate OS causality, qualify all images
or edits, reproduce120shams, or replace row21's own finite engineering gates.

## Retained suite and fixture assertions

The [retained suite](2026-10-04_photo_suite_supplement_rev6_run.md), RSC`98c8606`,
names exact HEAD`5f08728` and clean photo status. All14 inventory sizes/hashes
match. Main394=351OK+43skips, build27OK: **378 passing executions, 367 distinct
executed cases, 11 repeats, zero failures/errors**. All55 supplement methods,
including8new Rev6Cleanup methods, pass. The43skips comprise16WordNet restored
in build plus **27 unexecuted Stage A transitions:5old+22moved**; the incoming
22parenthetical is not their total or new complete transition coverage.

The new source assertions are meaningful and bounded (`tests/test_stage_a_supplement.py:995–1174`):
departed leader/live group child and a separately saved out-of-group identity are
checked gone before teardown. The latter uses separate sleepers, not a descendant
whose actual escape and identity capture are driven. Survivors drives a refused
restart with UNCONFIRMED and watchdog alive; simulated inability to confirm
watchdog death prevents an ended claim, rather than proving a sleeper survives
SIGKILL. Publication drives 7-byte short writes, initial-write no progress, wrong
read-back and non-object input; a garbled intent in a
synthetic controller run stops before release/ledger; a non-object disk intent
gives structured refusal. The post-close case deliberately replaces disk workers
after real close, then checks STOPPED, durable missing peaks, copy hash and no
admitted PASS. It does not naturally schedule a stalled `_persist` writer, call
the complete row21 verifier, or inject a late overwrite after successful final.
The lock/copy source argument covers the latter ordering; no reviewer execution
or exhaustive scheduler test is claimed.

The retained positive row21 Run fixture manually supplies a PASS and a controller
copy with no workers or release intents. Its new intended-peak check is therefore
vacuous; it still exercises existing receipt/comparison/runtime checks. The new
post-close fixture checks the peak predicate and final marker, not the full row21
verifier. These coverage limits do not establish a production bypass, where the
pre-GO intent is mandatory.

No new fixture injects file/directory fsync failures or publication stalls, rolls
back beat/session time with a charged-time lower-bound assertion, or exhausts all
missing/malformed member evidence. Source exceptions before GO and admission
checks supply their bounded fail-closed argument. Earlier retained failures,
test-only correction and assertion qualifications remain historical, not erased.
The companion brief's job(c) adjudication wording is a stale metadata pointer;
R052's current source ADMITTED/three-adjudication status is carried without this
review reopening actual reader outputs or adjudication.

## Review boundary and exact attestation

Three read-only peers provided scoped source/evidence findings; root integrated
them and checked Git/blob/AST metadata. No submitted module/import/function,
test/fake/fixture, CLI/provider/model/reader/forward, archive/scoring/simulation
was executed. No actual capture/image/array/tensor, raw reader journal/answer,
private-key semantics, human/plant/audit data was opened. No SSH/PBS/account/
remote job action, worktree or push. Source owns code/currentdocs/frontmatter/
generated INDEX/tracker/ledger/captures/results/go/archive/scoring/dispatch;
root owns this record and its own R052 append/lifecycle only. Foreign files,
source jobs, exposure disclosures, old reports and accepted handoffs remain intact.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A-supplement",
  "verdict": "favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-04",
  "reviewed_commit": "5f08728fcf77281627984e3f93b9f33621bee71a",
  "package": {
    "supplement_criteria_sha256": "83ffd69d8896b3b4f08d78b4fde3cf63fd91e7d36b191af29d3425e2212f5a92",
    "supplement_identity_sha256": "1acf556481928ceb6771c4d4140e0032b4b88e0bcd51ec67591169517df2c23c",
    "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"
  }
}
-->
