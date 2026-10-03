# Row 20 Stage A revision 13 — Codex record

Review date: 2 October 2026 Phoenix /3 October UTC. Exact reviewer
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Candidate: `22047ec71f8200ca7c12a9234269aa58f1306224`.
Brief: Unimog `dd59431820c407791b3f75b26bbd8b6fc0af65f5`,
`prompts/2026-10-03_codex_r052_stage_a_rev13_review.txt`, SHA256
`b362fff44c8278e9b0903ec9903dcf2449c21c11c81e7c9dcd538a8935a97acc`.
Ownership committed at Unimog `1b7276c7` before handoff
`7b552b79-0979-5c5c-b147-dd73022eb6b9` was acknowledged and review work began.

**NOT FAVOURABLE for this exact package.** The proposed numerical rule and its
common comparator are accepted as a prospective local engineering criterion.
The normal chained transition carries the old records and counters. One new
transition recovery regression remains, plus the declaration/report corrections
listed below. No positive Stage A attestation is issued.

The system keeps the 158 revision-10 instrumented records and 16 revision-12
native records, changes the criterion used to compare requested logits, and
would complete native16–19 after a new exactly bound owner release and go.
The known15-native stop remains TERMINAL. This review releases, rebinds and
dispatches nothing; it establishes neither Stage A PASS nor Stage B authority.
Reader REV12 `09bbe0e` remains favourable and separate; its package is unchanged.

References below are candidate sources under `stimuli/photo/`, or retained
review evidence under `workspace_demo/t1_access/reviews/`.

## Question 1 — criterion and common implementation

Yes to the explicitly defined rule:
`abs(native-instrumented) <= max(0.10, step(max(abs(native),abs(instrumented))))`,
where normal-binade step is `2**(floor(log2(m))-7)` and step(0)=0.
`stage_a.py:83–94` uses `frexp`/`ldexp` to implement that definition. The0.10
floor dominates below16; at16 the tolerance is0.125, at32 it is0.25.
Relative L2<=0.01 and requested-vector argmax equality remain required.

`compare:1211–1240` preserves finite/nonzero reference norms and adds explicit
logit finiteness. Its per-component `np.all(d<=tol)` is the acceptance predicate;
the largest absolute difference is not used as a global threshold test.
It also records the worst difference/tolerance component separately from the
largest absolute difference. Native StopCheck (`1311–1317`) and final PARITY
validation (`stage_a_report.py:398–408`) call this same comparator and pass field.
The final validator still independently checks records, membership and criteria.

The four retained `Rev13Parity` tests (`test_stage_a_runner.py:1070–1124`) passed.
They cover the stated spacing examples, eight synthetic vector cases around
the16 boundary, one-/two-step differences, unchanged relative-L2 and argmax
failures, and source assertions for shared call sites. Each vector case varies
one component under an unchanged top logit; it does not produce a case where
maximum absolute difference and worst normalized difference occur at different
components, or separate producing worker/report executions. Source establishes
the correct shared calculation; that evidence limit adds no rerun requirement.

This is a declared engineering tolerance, not a uniquely optimal fidelity
threshold or proof that rounding caused the observed differences. It never
tightens the earlier0.10 rule and deliberately relaxes it where m>=16.

## Question 2 — normal chain, counter carry and remaining recovery defect

The embedded predecessor bodies independently equal their immutable identities:
revision10 `e146ec63bc32973bb217de6066b57fe1c972bf8cf79a369b19d8efca617b2f38`
and revision12 `c0fb2ea0f6c5ef83cdabd414cb7d761ec3aabd9de13ed6022a852a7b590da001`.
Each hashes to its declared identity. Comparing complete bodies with this exact
candidate, only local-code hashes differ; snapshot, environment, frozen inputs,
dispatch and machine fields match. From revision12 only `stage_a.py` and
`stage_a_report.py` change in the local-code map. No model was loaded to check it.

`identity_transition:815–858` requires a declared predecessor, chain-end agreement,
a current matching terminal release not previously consumed, identical explicit
frozen fields and no open/interrupted attempt. It writes the next link before
changing only the ledger identity slot. The normal path retains the first link,
old phase record, completed entries, attempts, counters and carry. Pre-native
admission and the final validator retain the previously reviewed full predicates.
`admitted_phase_identity:797–812` allows the old instrumented producer through
two links and the native predecessor through one. The retained positive fixture
checks these, full pre-native admission and all16 saved native comparisons.
Its assertions show all16 pass the new rule; only15-native exceeded the old0.10.
These are implementer-retained assertions, not reviewer recomputation of arrays.

**R1 — recover the prepared-link write boundary before reconsideration.**
At856 the second link is durable; at858 the ledger slot is written separately.
If the worker dies, or the second write fails, between them, link2 ends at the
current identity while the ledger still holds revision12. The next native worker
enters this function before `Budget` and refuses at833–834 because the chain end
is not the old ledger identity. Neither desk-gate attempt reconciliation nor
controller process reconciliation finishes that prepared transition. No forward
is dispatched, so this is a conservative refusal, not a counter reset or false
PASS. It nonetheless loses the unchanged-old-slot recheck/retry credited in the
revision12 record and wedges the newly submitted resume mechanism at its own
durable commit boundary. The14 new fixtures do not cover that boundary.

Require idempotent reconciliation of an exact prepared tail against its recorded
from/to, current package, old ledger, completed entries/counters/carry and frozen
provenance, under the valid terminal-release authority then required. Preserve
the existing link; complete only the identity-slot commit. A repeat must neither
append another link nor reset/recompute records or counters. If the controller
recorded a new failure and changed TERMINAL bytes, its new release requirement
still applies; this repair cannot reuse an invalidated release. A targeted
no-forward fault/restart fixture must produce the post-link/pre-slot state and
its retry, retaining the existing stale-release/mismatch refusals. No new native
forward or blanket suite rerun is requested.

The five skipped `Rev12Transition` cases are acceptable historical replacement
for the old moved ledger: the ten new chain cases ran and cover normal carry,
no/stale release, changed frozen inputs, undeclared ledger producer and broken
chain. Keep the actual scope of the relabel control: `1231–1241` first asserts
that the identity-membership helper accepts the changed revision12 phase label,
then changes it to an undeclared f-hash and requires full admission refusal.
It does not prove every relabel is
refused. The earlier unchanged-transition-artifact trust and limited explicit
FROZEN_KEYS remain qualified as before; no generic coherent-forgery or universal
receipt-authentication gate is reopened here.

## R2 — align the rationale, evidence and report declarations

These corrections belong in the source-owned package/readiness and summaries
when R1 is resubmitted. They require no new model or diagnostic run.

- The permitted `native_diag.stdout.txt:2,9,12` reports01/08/11-native maxima
  of0.03125 at magnitudes3.109/3.531/2.266, spacing0.015625: **two steps**.
  The other13 reported maxima are one local step. Correct the universal
  “every record exactly one step” claim in criteria54–55, the resume summary
  and brief. Specifically15-native is0.125 at16.5, one step under this formula.
  The many-step small-logit differences remain admitted by the unchanged floor.
- Criteria66–67's claim that nothing previously refused becomes looser is false.
  State unchanged below16, never tighter, deliberately relaxed at/above16.
  Earlier TERMINAL outcomes remain records and require their own release.
- Describe a step of the **larger magnitude's binade**, with boundary precision.
  Adjacent BF16 values16.0 and15.9375 differ by0.0625, although step(16)=0.125.
  The fixture intentionally admits16 versus15.875, two lower-binade gaps. Do
  not claim all unequal roundings at magnitude>=16 must differ by at least this
  step, or infer a rounding cause from bit-identical marker residuals/equal
  argmax. The declared formula can stay unchanged.
- `stage_a_report.py:520–523` labels the SVG's sole0.10 guide “tolerance0.10”.
  It is now the absolute **floor**, not the acceptance bound for every logit.
  Relabel that guide/title or explain the actual varying criterion accurately.
  Markdown537–541 shows maximum-absolute fields; worst-component fields are in
  machine JSON and failure diagnostics. Qualify criteria62's table claim.
- Distinguish21 skips:16 WordNet cases, plus5 old transition cases not rerun.
  Report293 collected,288 distinct cases exercised and299 passing executions;
  the build's27 includes11 main-run repeats. Do not call all21 WordNet skips
  or293 fully exercised cases. “All mechanism evidence synthetic” also needs
  the already disclosed copied-development-record transition exception.

## Question 3 — exact package, retained evidence and disposition

Independent standard-library git/blob/hash/JSON/AST metadata reproduced:

| Field | SHA256 |
|---|---|
| criteria | `63be1b381c254de7d3e813496767d59e2ae630df32d725fb6c4377245b828cdd` |
| identity file | `96fbd94b88f9247b7705a32cd385fcc9b8df826e19acce4c73d65532b005a2da` |
| plan | `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc` |
| manifest | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| budget | `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f` |

Inner identity is
`2bac56e30e43ad62fe70ed01b8cf0562181029939e9778374de21c3bdce358f8`.
Every identity-referenced code/blob hash and checked live bound file matches.
Reader's16 bound blobs and24 fields remain the `09bbe0e` package, digest
`3e2bcdcc5356cbfaf31af61b473aa46751ec149006620c0d3a66a99466b9ec11`.
Byte-identical template/instruction sources retain the earlier independent
recipe; external executable/manifest/sandbox metadata was re-hashed without a CLI.
No reader re-review or admission/go change follows from this comparison.

Retained suite `85c92ea3ae6ee60151a07dd5820f14dc11b19525` pins candidate HEAD
and empty pre-run photo-directory status. All ten declared file sizes/hashes match.
Main293 collected in2134.134s, OK/skipped21; build27 OK in3.521s. Both exits
zero, no failure/error. Four parity and ten new transition cases are explicitly
OK; old five transition cases skipped. The count distinction above preserves
that evidence. Hash/size verification and peer checks are read-only, not reruns.
The transition fixture copies the machine-local real tree; reviewers did not
open its real/copy arrays, output payloads or photographs. The permitted aggregate
diagnostic supports reported differences/argmax/merge equality; residual-zero
claims are retained summary/fixture assertions, not new reviewer measurements.

All three questions are answered: accept the explicit criterion/common comparator;
credit normal chain and replacement fixtures but require R1 recovery and R2
alignment; issue **no positive attestation** at this candidate. Prior favourable
revision12 mechanism and reader12 judgment stay closed, with their limits intact.
The compound post-watchdog-loss/hung-sampler residual still bounds the controller
only, not whole-worker extinction or the earlier ~21-GiB/s margin in that branch.

Source owns implementation, captures, framework, ledger, protocol, release/go and
dispatch. Only this record was changed in RSC. Read/reason and three read-only
peers plus standard metadata only: no submitted module/function/import/test/
fixture/CLI, diagnostic, forward/model, new scoring/fit/science, remote/account/
job operation, raw tensor/key/private audit/human/pull output, image opening or
naming, worktree or push. Existing jobs/foreign files and prior one-time reports
are preserved. No terminal release, rebound go, scientific output or launch is
created by this record.
