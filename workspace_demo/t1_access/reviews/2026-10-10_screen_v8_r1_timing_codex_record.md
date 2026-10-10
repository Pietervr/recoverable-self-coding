# R052 — v8 current-timing closure and controller adoption review

Date: 10 October 2026 UTC. Reviewer: Codex, `GPT: R052 Entropy paper`.
Candidate: RSC `3648d9b`; bounded closure of `ce06828`'s remaining R1 timing check.
Incoming brief: Unimog `e2711267`, `prompts/2026-10-10_codex_r052_screen_v8_r1_timing_review.txt`, SHA256 `089a8628bc409ad3dacce7f1416042364cf864bca97f01771673d43cfdc1132f`.
Ownership committed at Unimog `4260c660`; handoff `48a78590-b965-5426-8430-8d8a21c2657e` accepted before review edits or delegation.

## Requested verdicts and exact authority

| Question | Verdict |
| --- | --- |
| (i) Candidate bytes at `3648d9b` as v8 | **FAVOURABLE.** Remaining R1 timing validity is closed; the R2/R3 closures in `ce06828` remain. |
| (ii) Exact promotion and controller adoption, with the established migration | **FAVOURABLE**, under the evidence-preservation and coherent promotion sequence below. This grants controller authority only. |

```text
ADOPT row19-screen-controls sha256=9f73622238034ed49cde86d0ee70c31a8bc8e2f1de9535f810eb4081dc49e9d7 version=8
```

**No pilot ADOPT line is issued here.** The actual new v8 qualification digest is not yet known. Refit job 10 remains held for actual qualification review, pilot adoption and a fresh whole-role production receipt. This controller review is not numerical-release authority. The owner's 10 October 03:1x UTC operating ruling, independently gated source operations/bank scope through job 17 and standing conditional go carry forward; no renewed stop or owner go is requested. Codex performs no dispatch or Lengau operation.

## Reviewed bytes and evidence

| Path relative to `chpc/` | SHA256 |
| --- | --- |
| `candidate_v8/row19_screen_admit.py` | `4fa993ee97d13d491b7afa5374c8ec49a330e64173872737942b0467bb0cb965` |
| `candidate_v8/row19_screen_status.py` | `ae91c8d035e53403b7d664fd1b8ed8e90995c0e88904b8f4915c6dcb13963948` |
| `candidate_v8/row19_screen_controls.json` | `9f73622238034ed49cde86d0ee70c31a8bc8e2f1de9535f810eb4081dc49e9d7` |
| `row19_screen_resources.json` | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |

Root verified these files against their committed `3648d9b` bytes, checked JSON and Python AST syntax without imports, and read the whole brief/design, prior record, repair/harness diffs, retained source-run output and relevant validity/adoption paths. Two read-only reviewers independently checked closure and promotion. Source reports **15/15 candidate checks and 88/88 regressions passing**; Codex read the output and executed no tests or candidate code.

Canonical v7 admit/status/controls remain `573e5b18…` / `dac142fb…` / `43a099ca…`; this candidate is not yet deployed or adopted. Resources, science manifest `43b75f94…`, shard worker `828d5964…`, verifier `d8d3c73b…`, release `7a67fd1f…`, programme gate `10a53402…`, and bank manifest/submit `d895c8a3…` / `88fd335e…` remain unchanged across the candidate repairs. Producer, ledger, task identity, seed, draw and scientific procedure changes are outside this approval.

## R1 closure

`TIMING_MEASURES` (`admit:747`) lists exactly `wall_s`, `fit_seconds`, `maxrss`, `t`. After the retained producer/coordinate/identity/integer-slot checks, `current_artifacts_problem:772–774` refuses unless each current value satisfies `_num` and is nonnegative. `_num:184–185` excludes booleans and nonnumeric values and requires finiteness. This is the same predicate as the unchanged verifier's `finite_nonneg:73–74`, used by `timing_ok:93–105`. Missing fields fail safely through `ct.get`; malformed/nonfinite JSON still refuses through the strict read. Both admission disposition (`:882`, via `later_completion:787`) and status (`status:244`) use this check before accepting a later completion at a disposed coordinate. The former negative-wall-time/missing-fit-seconds traces now refuse.

The 16 new post-watch mutations (`tests_v8.py:707–733`) change only the current timing, keeping retained verifier/receipt fixed: each required field missing, negative, a numeric string, or boolean. Assertions require refusal in admission and status, unchanged record-file text, and restored admission/disposition after restoring valid timing. These are isolated controller fixtures: `_retry_files:42–51` writes a synthetic `rep`/`ident`/`sha="s"` record matching retained synthetic units. Its byte-identity assertion establishes that the record was untouched; it does not establish a scientifically valid production record. This evidence limit does not undermine the independent current-timing predicate or its static closure. The production evidence steps below remain necessary.

R2's observed/current settlement certificate comparison, nonnegative time and plan binding, and R3's exact non-boolean integer cores/full-request product checks are unchanged from the accepted closures in `ce06828`. Attribution scanning remains distinct from measurement validity: killed-job naming, unreadable or temporary timing anywhere still withholds disposition; measurement validity is required wherever the exceptional rule relies on current timing. This review introduces no new scientific timing rule or arbitrary JSON formatting lock.

## Required migration before job 10

1. Preserve old controls adoption, pilot review, qualification, named full verifier and supporting watch/PBS bytes with their digests **before overwriting any filename**. `--qualify` reuses the qualification filename. Preserve the old generation's authority as historical evidence.
2. Pause admissions while promoting exactly the three reviewed candidate files to canonical paths, with the exact pinned resource policy. Commit/adopt the actual controls digest and this review's actual SHA coherently across observer/controller clones. Keep candidate controls metadata byte-identical during promotion; editing its pending/review text changes the approved digest. Current documentation and the adoption record carry the new status. Running producers keep their original paths, manifests, bindings and resource requests.
3. Run real v8 `--qualify 1` on retained job-1 evidence, without rerunning fits. Return the actual new qualification, retained full verifier and supporting production receipt/upload/accounting evidence for bounded Codex migration review and a literal digest-bound **refit max_job100** pilot line. The future digest is unknown: no old generation-7 digest, fixture or wildcard substitutes. Originals are complete and need no re-adoption solely for refit admission.
4. After that actual pilot review is committed/adopted, require a fresh zero-alarm whole-role v8 production receipt within **2,700 seconds**, binding actual job-3 PBS output/settlement, unchanged bindings/pins and current funding/capacity/STOP gates before job 10. The synthetic output used by the harness cannot supply this production evidence.

The walltime-only policy remains serial/24 cores/48 h/120 GB/haswell_reg/reserve1,800/per_slot1 from refit job10; jobs1–9 and originals retain their manifest requests. Full prospective reservation is1,152 core-hours. Highest refit job100, campaign cap60,000 and common100,000 remain. Dated actual budget arithmetic is46 full requests versus49 in the synthetic fixture; neither is batch permission or fresh accounting. Each admission uses the locked current funding/capacity gates; no runtime-tail guarantee is adopted.

Future numerical release must update both admit and controls consumer pins and obtain separate actual-target authority. No T, endpoint, coverage or numerical release is approved. Fixed attempted100/B200, seeds/draws/pairing, science seals, raw-bank limits, HEAL hold, shard STOP192, three slice attempts, prior closed reports/exposure and foreign files remain.

Claude owns promotion/adoption/actual qualification, ledgers, dispatch, current docs/tracker/frontmatter/generated INDEX and fixture wording alignment. Codex owns this record and its own R052/lifecycle entries only. No source edits, scientific imports/execution, fits/simulations, private outputs, account operations, worktree or push occurred. Next source action is the preserved-evidence controller migration, then return its actual evidence for the separate pilot review.
