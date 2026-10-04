# Row-20 OS-bridge supplement revision 3 — durable first-start evidence

Date: 3 October 2026 (Phoenix; 4 October UTC filename). Reviewer: Codex,
`GPT: R052 Entropy paper`.
Brief: Unimog `a4fe7ffbf4ac5460c309c9955af391ad1176594a`,
`prompts/2026-10-04_codex_r052_reader_rev17_and_supplement_rev3_review.txt`,
SHA256 `664c124f1e5ab9e24f22f8fbf1fcba3e0d18f657007a1f57d6c8427f28249254`; R084's whole accompanying adversarial brief read.
Ownership: Unimog `5db1d217`; handoff
`89460a5d-0d67-55f8-a1b0-06c20737e26c` accepted before review edits and delegation.
This is one of two independent class reviews answering RSC `1abb851`.
Accepted science, base Stage A, row19 and old matcher reviews remain closed.
All source line references are to the candidate under `stimuli/photo/`.
Candidate: `4baba91421ab19810fb4df84f3f8fd9cf5de63ce`.
Execution identity: `84c3210494805702ec7c11fbeb1dbd67d22fc68b3ff366473fa5e6226de67da4`.
Other answer: [reader revision 17](2026-10-04_reader_rev17_codex_record.md).

## Verdict

**NOT FAVOURABLE to this exact supplement revision-3 package as declared.** The
failed-terminal-write bypass is structurally closed for recognized prior starts,
and same-session endpoint binding is enforced by controller, receipt and row21.
One **P2** class gap remains: a durable `released=False` endpoint record can
describe a worker that already received GO. A crash before its first durable
post-release update can therefore permit a second endpoint session, contrary to
the declared release/interruption stop rule.

This is a static source interleaving, not an executed reproduction, observed
forward, lost charged counter or replay of a committed endpoint. The accepted
base Stage A policy/accounting and comparator remain closed. The supplement
requires its separate scoped owner go after a favourable exact record; the
standing reader go and the earlier four-native go do not cover it. No forward
or Stage B work is approved here.

## P2: an ambiguous durable endpoint release is treated as no start

Criteria §R2/§R3 and controller `1332–1334/1360–1363` explicitly treat a released
endpoint worker as prior-start evidence, separately from a ledger attempt. The
source's new before-start fixture was changed because released endpoint workers
are themselves start evidence. `released=False` is nevertheless only a pre-GO
snapshot, not durable proof that GO was never delivered:

1. Inherited `_phase` creates an endpoint record with `released=False` at
   `1152–1153`, then persists its leader/watchdog identities at `1166–1168`.
2. It sends GO and closes the pipe at `1170–1171`. Only afterward does it set
   `released=True` **in memory** (`1172`). No immediate persist intervenes.
   `_sample` starts the asynchronous I/O thread at `1249–1251`; that thread
   persists later at `1215`. Completion/error writes are later still.
3. A SIGKILL after GO delivery but before the first durable true update can
   leave only the open session and an endpoint record with `released=False`.
   Choose that interval before the worker's first Budget attempt: no ledger
   attempt, DONE, pass output, comparison or terminal exists. This requires
   no operator deletion, forged record or special scientific output.
4. On restart `_load:303–316` reconciles the recorded group and charges the
   crash tail. `_reconcile:499–527` visits that unreaped worker regardless of
   the boolean, but does not change `released` or mark release ambiguity.
5. `_prior_start_evidence:1371–1373` ignores the endpoint record unless
   `released` is truthy. With the other evidence absent it returns empty;
   `_supersede:1411` takes the inherited path, then new gates and endpoint
   workers may run (`616–631`). Both later endpoints can commit in that new
   session; all three new same-session PASS checks can consequently pass.
   `_missing_measurements:1442–1444` also excludes the ambiguous old worker.

`enforce.Budget.attempt:425–431` persists the charged attempt BEFORE yielding
to a forward (`434`). A real model forward therefore leaves ledger evidence
and would be refused. Earlier time remains charged and the group is reconciled.
The defect is the broader declared one-session-from-first-ENDPOINT-START rule
and its measurement coverage, not missing or duplicated charged model work.
The final-session check cannot restore the lost distinction before that first
attempt.

**Required structural closure:** in the supplement, conservatively treat any
durable endpoint worker record as a possible prior start unless stronger durable
evidence proves it never crossed release. Counting any recorded worker in
SUPPLEMENT_PHASES, independent of its `released` boolean, is the narrow simple
repair. Alternatively persist supplement-specific release intent BEFORE GO and
use it for restart and measurement decisions. Another write-after-GO cannot
remove the ambiguous crash window. Keep the accepted base Controller unchanged
and make refusal independent of terminal persistence.

Retain an adversarial no-forward crash-boundary fixture with the durable endpoint
record `released=False`, valid worker/watchdog and open-session accounting,
no attempt/DONE/pass/comparison/terminal, representing delivery before its first
heartbeat. Restart must reconcile, retain/charge time, refuse before ANY new
phase worker and preserve result/receipt/final bytes. If using release intent,
also cover its failed write and interruption before/after GO. Review the entire
release-evidence class, including armed-but-unreleased uncertainty; do not patch
only a convenient heartbeat instance. No new scientific review is requested.

## Closures credited

`_supersede:1394–1411` sets `_refusal` before best-effort `_terminalise` and
returns without superseding. A pre-rename terminal failure changes the reason,
not the decision. `_gates`, `_phase`, `_finalise` refuse independently. Normal
production refusal closes a charged refused session before any phase worker;
prior crash accounting is reconciled first. Ledger attempts/unreadable ledger,
recognized released endpoint workers, DONEs, pass files, comparisons and terminal
records each supply prior evidence. An admitted PASS raises before superseding;
missing marker or matching abort makes it unadmitted and recognized starts refuse.

Both endpoint commits must name the current session in controller `1423–1431/
1494–1495`, receipt `stage_a.py:2052–2055` and row21 verifier `2170–2171`.
Native admission still requires this session's instrumented commit before load;
an already attempted endpoint cannot resume. Full direct comparison receipts and
three record validators remain re-derived by row21; tolerance agreement through
an old reference never substitutes for direct new/new comparison.

The accepted parent stays bound to `cc1d2cb`, internal identity
`1d017dcefd1e810df77a2e643a03b9ffbdcf01e711cf47cd3ae5290d6fd2c727`, distinct
from the identity-file package hash. Parent package_at_commit(HEAD) intentionally
refuses after supplement code moves; the supplement uses its own builder.
Parent pins cover eight metadata hashes, total bytes and reference outputs,
not a whole-tree digest. Row21 retains its independent accepted-parent gate.

## Evidence, identity and carried bounds

All 34 supplement methods pass, including eight Rev3Adversarial and five Restart.
The new completed-endpoint crashes and deletion cases begin after durable released
histories; none exercises GO before the first true snapshot. Endpoint defaults
now use the real carried Budget ledger/current session; receipt and arrays remain
synthetic, not actual model/env/comparison evidence.

The brief overstates “each” of 15 adversarial groups asserting unchanged bytes,
no worker and a closed charged refusal. Deletion/unreadable cases assert fewer
properties; the without-gates case expects SystemExit and leaves an open session
for later crash charging, with a weak worker filter; the foreign-session case
tests only the predicate, not final/receipt/verifier end-to-end. Admitted-PASS
refusal uses SystemExit/pending-start accounting. Pass-only, comparison-only and
terminal-only histories are not isolated fixtures. These coverage descriptions
need qualification; they are not additional production blockers.

Root reproduces all **six package fields**, identity self-digest and 15 declared
source bindings, and checks 17 live bound files. Only criteria/identity package
hashes change from revision 2; supplement plan/base plan/manifest/budget unchanged.
The base Controller and guard/enforce/watchdog policy remain unchanged in the
revision 3 diff. Whole supplement-tree deletion is explicitly an operator act
outside the controller's reach; this counterexample needs no deletion.

Carry 194/193/1/194 starts/completions/failures/passes, 2,338.113973380568 seconds
and 396,783,863 bytes stays charged. Two new starts yield 196/195/1/196 of 200;
row21 aggregate is 196+1,856=2,052≤2,056, without adding parent 194 twice.
Remaining storage 676,957,961 bytes; four-hour/1GiB/48GiB envelope, 44GiB stop
and charged 60-second closure carry. Four spare starts are not retry permission.
Forecasts are implementer estimates, not measurements by this reviewer.

This exposed fixed-input 00 bridge does not isolate OS causality, qualify all
images/edits, reproduce 120 shams on the new OS, admit PILOT or approve Stage B.
Earlier finite Stage A/build/metadata/tolerance qualifications carry.

## Retained evidence and review boundary

Shared retained run: RSC `b532f08`, HEAD `977655f` after supplement `4baba91`;
[suite record](2026-10-04_photo_suite_supplement_rev3_reader_rev17_run.md).
All 14 inventory files independently match their sizes and SHA256 values.
Main: 373 collected, 330 OK, 43 skipped, exit 0. Build: 27 collected/OK,
exit 0. Combined: **357 passing executions, 346 distinct executed cases,
11 repeats, zero failures/errors**. Sixteen WordNet skips are restored by the
build row; five Rev12Transition and 22 moved Rev13/14/15 Stage A transition
cases remain unexecuted. This is not fresh complete Stage A transition coverage.

Eight new Rev17Reader methods and eight Rev3Adversarial methods account for the
16 added collections. The crash method remains one collected method, now with
four subtests (ordinary/structural at the 2,049-byte and 1 MiB boundaries).
All 34 supplement methods pass. A passing fixture is evidence for its assertions,
not proof of every possible crash interleaving or actual provider behavior.
The Rev6 timing controls pass; their 0.6-second success sleeps under a two-second
timer leave 1.4 seconds before other scheduling/I/O, not immunity to arbitrary
scheduling delays. The old failed run remains historical evidence.

Three read-only peers reviewed source and named public synthetic evidence.
Root independently used standard-library Git/blob hashing, literal AST
reconstruction and metadata/count checks. No submitted module/import/function,
test/fake/fixture, CLI/model/provider/reader/forward, archive or scoring ran.
No actual capture/image/array/tensor, raw reader response/journal, private-key
semantics, human output or prohibited audit material was opened. Owned CLI and
qualification-key bytes were opaque hashes only. No remote/account/job action,
worktree or push. Code, current summaries, captures, results, go, archive and
dispatch belong to the source; these records and root's R052 log/lifecycle are
the only owned repository edits.

## Exact attestation

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A-supplement",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "4baba91421ab19810fb4df84f3f8fd9cf5de63ce",
  "package": {
    "supplement_criteria_sha256": "7c0ce9da7755ad721a1790385674a0fd655bf3e8430876b86eee0bfb870fdad5",
    "supplement_identity_sha256": "1823e427baa49021485e99da0983bb815dac41b8c680146f9c3f5a9f19025a51",
    "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"
  }
}
-->
