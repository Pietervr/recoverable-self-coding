# Row-20 OS-bridge supplement revision 1 — bounded implementation review

Date: 3 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`.
Brief: Unimog `97408f889456296bc0c761bf978e54bef37402e3`,
`prompts/2026-10-03_codex_r052_reader_rev15_and_supplement_review.txt`, SHA256
`ef75d83904851ea18a4399f612d289dd0771dc1768a7b8720da78f508cb7c7e6`.
Ownership: Unimog `b2e74539`; handoff `13e033f7-cbde-5fe3-927a-08d0b5eb1254`
accepted before review edits and delegation. This is one of the two requested
bounded reviews; the other is linked below.
Candidate: `b67a07392f37b8e5184ef7cf52c95ddbb3c00acf`.
Execution identity: `4fb0e547b8329c57d1c216a144e769e4c74b5d1082904e6b5a1cdd5ba97f497d`.
Other review: [reader revision 15](2026-10-03_reader_rev15_codex_record.md).

## Verdict and design choice

**NOT FAVOURABLE to this exact supplement package.** A separate output tree,
ledger and controller with explicit row20 carry is an acceptable design choice.
It preserves the accepted Stage A bundle and charges the two new starts to its
existing envelope. It needs neither a Stage A transition nor a new enforce row.
Its new mode inherits resumable failure paths which contradict its terminal-stop
contract and can produce PASS after STOPPED, including after a mandatory memory
measurement was missing. This is a supplement-specific admission blocker.

No supplement execution, first CAL, row21 or PILOT is approved. The accepted
Stage A mechanism `1a33e68` and report `b0db0f9` remain closed. Reader standing go
and the earlier four-native Stage A go do not cover the supplement. A later
favourable exact supplement review still needs its own scoped owner go.

## P1: same-version restart can erase STOPPED admission conditions

`STAGE_A_SUPPLEMENT_CRITERIA.md:101–104` and `stage_a.py:1480` declare failure,
interruption or refusal after a start terminal, no recovery/release/retry. The
following **static source trace**, not an executed reproduction, violates it.

After both endpoints are completed, a receipt worker fails or produces an
inadmissible receipt. Inherited `Controller._run:641–643` appends a stop but does
not call the supplement terminal callback. `SupplementController._finalise:
1407–1422` writes STOPPED and can write its admission marker, without creating
`SUPPLEMENT_TERMINAL.json`. On another invocation `_supersede:546–554` moves that
final/marker/receipt aside. Gates (`stage_a.py:1680,1700–1705`) see no terminal and
no open/interrupted ledger try. `_run:627–631` skips both DONE phases. A new
successful receipt/final may then produce PASS without any version release.

The concrete resource consequence is more serious than a receipt wording issue.
`_final_peak:1018–1022` records an unavailable native worker exit peak and returns;
it does not terminalize. The native forward/output may be complete. First final
is STOPPED because `_missing_measurements:867–874` requires that released worker's
exit peak. Yet this filter selects only workers of **the current session**.
After restart the completed endpoint phases are skipped and the new session has
only new gates/receipt workers. With those readings present and recorded sampled
peaks below the cap, the earlier missing mandatory native exit observation is
no longer an admission failure. PASS is therefore possible although that native
execution never supplied the required measurement. Prior observations, counters
and time are retained; the acceptance condition is what is lost.

The same incomplete terminal policy permits controller crash/hold after the
instrumented endpoint was durably committed: `_load:303–316` reconciles/charges a
crashed open session; `_hold:647–654` closes a held one without terminalizing;
gates stop only an interrupted **attempt**, not a completed endpoint followed by
an interrupted controller. A following session can reload/skip instrumented and
dispatch native. `test_resume_reloads_and_never_replays:348–358` explicitly
permits post-commit reload, while the declared supplement contract forbids that
continuation after interruption.

The 19 passing fixtures test work failure/open-attempt interruption, which do
terminalize. Receipt failure tests `424–433` assert immediate STOPPED only, not
restart prohibition. They do not close these paths.

**Required before reconsideration:** make post-start supplement failure/hold/
interruption durable and terminal before any later forward or PASS regeneration.
Cover receipt/closure/final resource-measurement failures and completed-endpoint
controller crashes/holds. Restart must recognize a prior failed/STOPPED post-start
session even if the first terminal write failed or was interrupted. Preserve
completed results, counters, time and missing-measurement evidence. Keep the
repair supplement-specific; do not alter the closed Stage A resumption policy.

Retain meaningful no-forward restart fixtures for receipt exit/non-PASS, completed
native with mandatory exit peak absent, and crash/hold after instrumented commit
before native. Each must preserve charges/results, dispatch no subsequent
endpoint, and never regenerate same-version PASS. No tolerance change, different
input or old Stage A mutation is needed.

## Accounting, exact pins and parent identity

The committed plan fixes input00 exactly to the base plan (all frozen input and
request-token/template hashes) and new IDs `00-plain-os2701` and
`00-native-os2701`. It declares macOS27.0.1/build26A434/arm64; gates check all
three. The separate tree is `captures/photo_stage_a_supplement`; the reviewer did
not open it or the accepted capture tree.

| Row20 budget | Carried/declaration |
|---|---|
| Counters | 194 starts/193 completed/1 failed/194 passes carried; two single new tries yield 196 starts/195 completed/1 failed/196 passes |
| Starts | 196 of 200; four in hand do not authorize retry |
| Time | Carry 2,338.113973380568 seconds against total 14,400; setup/comparison/receipt/closure included |
| Storage | Carry 396,783,863 bytes against 1,073,741,824; separate-tree remainder 676,957,961 |
| Memory | Same per-task guardian/identity/exit-peak/sampler mechanism; stop44GiB, cap48GiB |

The carried storage pin includes post-report accepted-tree metadata; it is not a
claim that the earlier report's final size 396,774,626 changed retroactively.
The reviewer checked plan arithmetic/source binding, not actual tree size.
`supplement_open:1731–1741` enforces exact carry and excludes foreign/interrupted
IDs. `Budget.attempt` durably spends the start/pass before each forward; outputs
reload without a new forward. The controller carries time across sessions and
uses the remaining storage cap. Memory is a maximum over live work, not cumulative
allocation across the old and new task; required measurements must still survive
restart as above. Prospective row21 carries **combined196**, not another194;
1,856 additional row21 starts would make aggregate2,052≤2,056. This candidate
does not build or authorize Stage B.

Standard-library Git/blob/JSON/AST hashing reproduces all six package fields
below and the supplement identity self-hash. Its four blob-map pins, ten exact
local-code pins and packet-source pin match the candidate. Seventeen bound live
source/metadata files match when checked; this is not a fresh runtime dependency,
weight/lens, OS or capture admission.

The R084 sentence that parent `package_at_commit(HEAD)` still succeeds is wrong,
as R052 already disclosed. The parent's committed identity describes the accepted
`cc1d2cb` code; supplement HEAD changes stage_a.py and controller, so parent
rederivation there necessarily refuses. The accepted bundle's reviewed-commit
binding remains intact. The supplement's own package uses its own identity/import
map; no new path incorrectly calls the parent's package-at-HEAD function. Fresh
Stage A gate refusal at the changed code is intended. Correct the brief sentence;
**that discrepancy alone does not require a supplement package repair or parent
identity relabel**. Package file identity hashes and embedded execution-identity
hashes are distinct.

## Direct comparison and prospective gate scope

The production bridge compares (a) new instrumented directly to old27.0 input00
and (b) new native directly to new instrumented, with the reference denominator,
unchanged finite residual/requested-logit/argmax comparator and bound-input
checks. Native is separately loaded, has one prefill/no jlens import, and must
match the new instrumented merged embeddings bitwise. This is the requested
two-path bridge; it neither isolates OS causality nor reproduces all images,
edits or 120 shams on the new environment.

Receipt wording needs precision. An (a) failure writes (a), terminalizes and
correctly prevents native/(b). Thus 'both receipts before any stop' is not literal:
retain each executed comparison before its stop and record (b) absent when never
run. Do not spend native after (a) failure merely to satisfy that sentence.

`supplement_receipt_ok:2117–2181` requires admitted PASS/current receipt, unchanged
bound outputs, exact two single tries/carry+2, frozen input, both rederived finite
comparisons passing, native merge identity and all COMPAT_KEYS. A rederived
logit/finite failure holds. Two current claims are broader than its exact checks:

- Equality to retained comparison receipts covers rel_l2_max/argmax_equal, not
  every comparator result or bound/schema field; `_validate_record` and
  `_bound_checks` are not rerun there. Earlier validated production outputs and
  receipt hashes protect the retained checks, so this is not a demonstrated
  comparator-failure bypass. Narrow the claim or rederive the complete receipts.
- Parent worker pins are eight metadata hashes, total bytes and input00 reference
  checksums, not a whole-tree digest. The later row21 helper rechecks the selected
  reference but does not call `check_stage_a_frozen`/parent accepted-report
  admission. It alone does not prove every Stage A record unchanged. Prospective
  Stage B must retain its separate parent-acceptance/frozen-pin gate before CAL;
  this review does not treat the helper as the whole gate.

## Retained fixtures and review limits

Shared suite `79a6621` on readerHEAD05bd60b includes **19/19 supplement fixtures**
and 8/8 new reader fixtures. All18 retained inventory files match hashes/sizes.
Main344=300pass+1fail+43skip; build27pass; combined327passing executions,
one failure, 317 distinct executed cases and 11 repeats. Sixteen WordNet skips
are restored; 27 moved/older Stage A transition cases remain unexecuted.
Synthetic supplement fixtures use minimal/constructed accepted finals and records;
they are not a real accepted-bundle run or a scientific parity observation.

The one retained Rev6 reader closure failure is independently discussed in the
linked reader record: the fixture races a two-second pre-receipt sleep against
a two-second abort timer inside its three-second **total** allowance. It does
not show false admission or independently block this supplement. Three retained
passes do not erase it; one unretained fail/two passes are testimony only. The
three-second-receipt description and failure-time load inference need correction.

Read/reason only, three delegated read-only source/evidence peers, standard-library
hash/AST/count/byte arithmetic. No submitted import/function/test/fake/CLI,
provider/model/reader/forward/archive/scoring/simulation was run by the reviewer;
no actual capture tree/image/array/tensor/raw reader/private-key semantics/human
or prohibited audit data was opened. Owned CLI/opaque qualification-key hashing
was confined to the paired reader pins. No remote/account/job action, worktree
or push. Prior accepted results/exposure limits/caps/source jobs are preserved.
Source retains design/code/current summaries/results/go/dispatch; root owns only
the two review records and own R052 log/lifecycle.

## Exact negative attestation

This block records refusal and exact identity; the gate requires `favourable`.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A-supplement",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "b67a07392f37b8e5184ef7cf52c95ddbb3c00acf",
  "package": {
    "supplement_criteria_sha256": "60f7f3661afba0b6f519f1e5154a62fab55c752a5f6fae129cd1eadf19be147e",
    "supplement_identity_sha256": "c28518ee2e5b26145c1367c8bb7d56c7b8af52ca62b8a25847b69ad1b92ab599",
    "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"
  }
}
-->
