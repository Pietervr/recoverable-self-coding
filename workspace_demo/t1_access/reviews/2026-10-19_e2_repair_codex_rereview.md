# EC2 epoch-2 adoption repairs — Codex re-review

19 October 2026 — **FAVOURABLE for the exact repaired candidate package at `c26835f631c83a3e101a83673905a05443982196` plus `806c44c`. B1, B2 and C1 are closed.**

```text
ADOPT row19-screen-controls sha256=9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0 version=17
```

This is the static candidate-controls/package verdict requested by the brief. It does not execute adoption, approve unreviewed migration scripts, supply E2Q1 run permission or release qualification/production/scientific results. All previously identified operational prerequisites remain. No live authority was changed; adopted controls remain v16.

## Scope and exact package

Read the exact brief `Unimog-Projects/prompts/2026-10-19_codex_r052_e2_repair_rereview.txt`, Unimog `02780666400cbd4df4e676a9e2c5fa795556ee79`, SHA-256 `fdfb8b5faaeda1bc3790f2e7ed27f36ffe789b1b30cc3ce5a9e0859817f2d1cf`. Ownership was recorded at Unimog `db1885df`, then handoff `9c8471a4-392e-5e2a-9734-200b44ad69d9` was accepted before review edits. Exact session: `GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`. As required, the SI v2 snapshot gate was completed first, at Unimog `673f9621`, with its separate CHANGE 3 verdict and single completion pointer.

This re-review addresses the three repairs to `reviews/2026-10-19_e2_adoption_codex_review.md` (`785aa8cd`), their rebuilt bindings, shared-e1 effect and staging/wording corrections. A's final data are unchanged; their previous favourable judgment is retained, not replaced by a fresh scientific review. Paths below are relative to `workspace_demo/t1_access/`.

Independently authenticated controls SHA-256 is the literal above. Promotion-map SHA-256 is **`6bc8bd3947c398c0200c241725ad5dbb70555a3ee0290012a274a4cf6563df74`**. Exact changed integration sources are:

- Ingestion: `277c51b0a24fee6b151180e99584a831c091ca4b30b6bd999a1221ff364bf54f`.
- Qualifier: `1d8eee78fc9427cd9e4cebe09deac37cf4284f0b8a86714dcc9d80cde63cbb29`.
- E2 qualification helper: `5ceba55189dd351b2cc5a997b115cdbfd0d84f17397402fa7deb2b3e937025fa` — execution AST unchanged; docstring correction only.
- Mac authority: `e4897991aaeaf1dc019c9b73361d288e71464e6f89e416b66d9e3d7601df146d`.
- Builder: `f2a80f42962435fc3a6787d26d838c8b67b5e0c9fe231779890a5868cae72abb`.
- Promoter: `f0c320c28ef3273b1b62137606372fcab13a9fd4d68765ab826fdae22bb7b5fb`.

Parent checks authenticated all 20 map rows against their explicit committed sources and old-or-absent destinations, the 17 latest file pins, unchanged historical versions/non-version sections and unchanged final-data path set. Relative to the previously reviewed v17, only three latest file pins and its explanatory text change; the map additionally changes the Mac authority and controls rows. The live base is still controls `01976b6a` and adoption `523fe18a`.

## B1 — released-E2Q ingestion and crash accounting repaired

`candidate_e2/row19_ec2_ingest.py:483–497` now admits the partial route only for schema-2, released, class-qualification E2Q1/E2Q2, alongside the existing production branch. The real qualification class is retained. Unreleased qualification still holds; schema-1 and other qualification contracts remain all-or-nothing. The applied branch keeps bundle/plan/outcome/status/owned-work, lineage, inventory, fence, sentinel/duplicate, journal/publication and replay checks. It additionally enforces **at most three qualifying non-completions across all roles**; production's seven-work-slot rule cannot replace that requirement. Unproduced work is fenced/accounted for without fabricating a scientific record.

`candidate_e2q/aws_ec2/prod_authority.py:484–532` now includes acknowledged qual-E2 history and normalizes E2Q1/E2Q2/production labels only for matching production instance type, workers and volume and the recorded production instance type. Lifetime remains part of the envelope. Only acknowledged owned-work unproduced outcomes feed the fatal129–159 two-crash rule. Dispositioned attempts, comparison-only slots and censor/deadline outcomes do not acquire crash authority.

Independent guarded execution passed the new **44/44** behavioral checks plus **14** targeted checks. Actual synthetic ingestion/ACK chains show one E2Q crash followed by one production crash excluding the same physically equivalent coordinate before another allocation. Different lifetime/type/geometry remain distinct; E2Q2 is covered. Publication interruption/replay, real qualification class, exact ACK accounting, three-versus-four failures, invalid/present-null status, leftovers and comparison failures were exercised.

Coverage limit: one test description claims launcher refusal, but its assertion checks the shared excluded set rather than calling the launcher. This review does not call that a new executable launcher/cloud test. Synthetic fixture geometry is not a new validation of A's final 63-worker panel. Future changes to contract geometry/profile/history meaning require their own reviewed interpretation; this verdict covers the present pinned definitions.

## B2 — resource-evidence acceptance repaired; shared e1 change accepted

`candidate_e2q/row19_ec2_qualify.py:236–313` now validates ordinary field kinds and physical domains before computing memory evidence. Both timelines must be strictly increasing. Total memory is positive, available memory lies within total, RSS/load/count domains are checked, and a single occupancy row cannot amplify into multiple full-packing observations. Peak usage still includes **all** valid observations, including nonfull periods. Ten distinct qualifying samples, the 184GiB ceiling and terminal-worker limits remain.

Independent **56/56** qualifier checks passed. The original complete schema-3 counter — 12 observations with total192GiB and available193GiB — now yields return3, **NO_RELEASE**, no released attempt and invalid-memory evidence. Duplicated timestamps and one-occupancy-line amplification refuse; a valid150GiB positive control still releases synthetically. Twenty further bounded function cases checked ordinary malformed fields, unique joins, the exact184GiB boundary and a185GiB nonfull observation, which correctly fails.

**Accept the stricter shared method prospectively for e1 and e2.** It enforces the meaning of existing resource evidence without changing its numeric thresholds or scientific procedure. Historical records/certificates retain their original code pins and scope. No old host evidence is alleged invalid, no old certificate is silently reissued, and no e1 replay, release or extra paid/scientific rerun is required here. Future evaluations with the new qualifier bind its new bytes and pass its checks.

Nonblocking robustness limit: “never an exception” is not literal for arbitrary-length unsigned strings. A400-digit RSS can raise OverflowError and a5000-digit total ValueError outside the parser's exception boundary. Neither emits RELEASE or a new certificate; these are beyond ordinary producer counters. Bounded magnitude/conversion handling would make the stated guarantee exact. An exception can leave an old `--out` pathname, so a pre-existing file is not successful new evaluation: honor the nonzero command result and exact fresh certificate/review bindings. No stale-output acceptance route was demonstrated. This is fail-closed cleanup, not the original false-RELEASE blocker.

## C1 — authenticated-base promotion recovery repaired

`candidate_v17/build_v17.py:156–172` resolves the immutable base before building: live only when **both** fixed v16 controls/adoption hashes match, otherwise the completely verified archive. The shared archive verifier requires its exact13-member inventory, checksum manifest and COMPLETE, matching member digests and the fixed v16 authority digests. `build(base)` derives expected v17 from that authenticated base; `promote_v17.py` resolves it before candidate/state/review/write handling.

Independent execution passed **30/30** inspected synthetic private-Git-tree tests. The actual private promoter was interrupted after copying controls and before replacing adoption. Candidate/build checks then succeed from archived v16, complete-state checking correctly reports incomplete adoption, and retry changes only adoption. Complete checking/retry succeeds without changing payload bytes or mtimes. Six missing/partial/corrupt archive variants refuse across four commands, and changed adoption is refused. Twelve further named integration checks passed. Live source/authority remained unchanged.

The fixture's dummy Lengau archive checksum is not a real remote proof. Source containment, locks/drain, remote archives, transport/deploy and recovery evidence remain in the separate migration review. No local unit test establishes those operations.

The controls literal alone does **not** cryptographically bind the Mac-only authority files or promotion-map digest. Their exact bytes are authenticated by this committed-package review and the reviewed builder/map checks above. Mechanically, changing Mac source plus its builder/map constants could preserve the controls hash. That would be outside this verdict even if the literal text still matched. Preserve this exact reviewed package through migration and verify the Mac/map/builder/promoter identities as well as the controls; any changed package needs review. No such unreviewed change was found here.

## Staging, wording and remaining sequence

The documented remote qualification command now explicitly supplies `--snapshot chpc/claims_snapshot_e2.json`, the deployed `31cc268f` bytes. It preserves the reviewed `f04a5e43` panel. The 56-check suite demonstrates refusal without the override in a relocated layout, synthetic success with the correct copy, and refusal of a tampered copy. This settles the path argument; it does not supply the still-missing collection/verification/staging procedure.

Choice8 now correctly describes code-content binding rather than installation-location binding; the actual certificate still follows deployment and activation. Choice13 names the actual13-member archive. Other previously accepted design choices and A's exact final partition/funding/panel ruling stand within the prior review's scope.

Before live change, separately review `migration_v17`, its preflight/archive/deploy/recovery route and exact package identities. Preserve running workers/reapers, old claims/proofs and the coordinated authority transition. After adoption, refit admission holds until canonical e2 activation; obtain current installed inventory/lock-held overlap checks, current-v17 receipts and the **one existing-job1 metadata rollover**, new pilot hash/review/literal, with no fit.

Before one paid E2Q1, require the reviewed concrete bundle collection/verification/staging procedure, prospective E2Q1 permission, deployed/activated exact contracts and data, and current funding/fleet/inventory/receipt gates. Before five-way production, require reviewed R6 interleaving and capacity evidence. Actual76-worker R1'–R5' evidence, post-deployment schema-3 RELEASE certificate, exact-result favourable review, release-adopt, canonical qualification ingestion/ACK and current admission checks remain mandatory. The old runbook phrase “no AWS spend before the epoch-2 release” must mean **production** spend; separately permitted qualification precedes that release. Resolve this in the separately reviewed runbook, not by bypassing permission.

Standing owner approvals and limits persist: USD300 allowance, two qualification/four extra production bounds, five-instance ceiling, USD2300 production/USD3000 total, full reservation and current budget checks; refit+S81,000/programme100,000, serialmax_run10/job ceiling100, crash/rescue and freshness/ownership gates. Numerical release, p80/RESOLVED-target and positive scientific validation remain separate. No routine confirmation is requested.

## Verification record and limits

Parent: **98** stdlib source/admin binding checks, no runtime imports; A unchanged established by Git path metadata, with its already-reviewed source identities retained. Readers:44 behavioral +14 targeted B1 checks;56 qualifier checks +20 bounded B2 edge cases;30 private promotion +12 integration checks. The two absurd overflow cases are the disclosed exceptions, not successful failed-verdict tests. Broader regression counts and real-tree `promote_v17 --check` at806c44c remain source-recorded evidence; they were not independently rerun. Pre-existing regression FAIL lines were not relabelled as all passing.

Proofs: `/private/tmp/r052_e2_repair_binding_checks_20261019.json` and helper; `/private/tmp/r052_e2_repair_b1_review_20261019.md`, `b1_run_20261019.log`, `b1_safety_20261019.json`; `/private/tmp/r052_e2_repair_b2_review_20261019.md`, `b2_56_20261019.log`, `b2_edges_20261019.log`, `b2_safety_20261019.json`; `/private/tmp/r052_e2_repair_c1_review_20261019.md`, `c1_test30_20261019.log`, `c1_pins_20261019.json`. All shortened proof prefixes are `r052_e2_repair_`.

The private tests use allowlisted administrative source/metadata, synthetic records and guarded numerical stubs. They establish no actual host memory behavior, capacity, canonical transfer/ACK, remote restart or scientific parity. All processes finished. No actual promotion/deployment/activation/qualification/adoption, cloud/SSH/PBS/worker action, fit/simulation/decoding, source/ledger edit, worktree or push occurred. Protected/scientific/human/norm/plant/key/audit/reader/pull/sample payloads and foreign fixture.err were not opened. Prior exposure/protected-byte disclosures and foreign work remain preserved.
