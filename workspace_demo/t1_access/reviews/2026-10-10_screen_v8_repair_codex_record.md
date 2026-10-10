# R052 — repaired screen version-8 candidate re-review

Date: 10 October 2026 UTC. Reviewer: Codex, `GPT: R052 Entropy paper`.
Candidate: RSC `28861c4`; bounded repair of `5cb9a02` findings R1–R3.
Incoming brief: Unimog `2c61abfc`, `prompts/2026-10-10_codex_r052_screen_v8_repair_review.txt`, SHA256 `924e1aa917529c600743b8ae48d24c243dfc6a9484ca3f7ef7563c4845602d64`.
Ownership committed at Unimog `ef5be4a5`; handoff `ba82b786-50dd-5d98-9321-4bccfb20c74f` accepted before review edits or delegation.

## Requested verdicts

| Question | Verdict |
| --- | --- |
| (i) Repaired bytes as the v8 candidate | **NOT FAVOURABLE.** R2 and R3 are closed; R1's current timing validity remains incomplete, as described below. |
| (ii) Promote these exact bytes and adopt their controls | **NOT FAVOURABLE to these bytes.** The generation migration remains sound, but the remaining R1 check must be repaired and reviewed first. |

**No controller or pilot ADOPT authority is issued.** Refit job 10 remains held. The owner's 10 October 03:1x UTC operating instruction and standing conditional go carry forward; this record does not reinstate the earlier operating stop or request another owner go. Independently gated source operations and bank scope through job 17 continue under that instruction. Codex performs no Lengau operation or dispatch.

## Evidence and exact bytes

Read the whole repair brief and updated candidate design, prior `5cb9a02` record, candidate repair diff and relevant current-artifact, receipt, admission, verifier, envelope and certificate paths. Read the retained harness changes and source-run output. Three read-only reviewers checked R1, R2/R3 and the adoption path separately. Root checked committed file equality, SHA256s, JSON syntax and Python AST syntax without importing or executing candidate code. No test rerun, scientific import, fit, simulation, endpoint/target/coverage analysis, private output, account operation, worktree or push occurred.

| Path relative to `chpc/` | SHA256 |
| --- | --- |
| `candidate_v8/row19_screen_admit.py` | `054d6d685cfd02ef3a41fd43251807d4133227016695fc2c914e88cbfef60584` |
| `candidate_v8/row19_screen_status.py` | `ae91c8d035e53403b7d664fd1b8ed8e90995c0e88904b8f4915c6dcb13963948` |
| `candidate_v8/row19_screen_controls.json` | `1436d885ea5021664a0076007cb2e08f6f4d4253a77a0735c50f7fbf370d0c8a` |
| `row19_screen_resources.json` | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |

These bytes match `28861c4`. Canonical v7 admit/status/controls remain `573e5b18…` / `dac142fb…` / `43a099ca…`. Resources, scientific manifest `43b75f94…`, shard worker `828d5964…`, verifier `d8d3c73b…`, release `7a67fd1f…`, programme gate `10a53402…` and bank manifest/submit `d895c8a3…` / `88fd335e…` remain unchanged from `c1956ef`. The resource policy remains inert under canonical v7.

Source output reports **14/14 candidate checks and 88/88 regression checks passing**; Codex read those results and did not rerun them. The ten new R1 mutations test producer, slot, identity, coordinate, missing files and a changed stored checksum field. They do not test the current timing measurement validity contract. The fixture change from empty retry placeholders to files matching retained unit fields is appropriate; existing assertions were not relaxed. Fixtures do not supply actual production qualification or job-3 output authority.

## R1 — producer continuity repaired; current timing validity still incomplete

`admit:745–776` now reads the current canonical timing and record. It rejects missing/unreadable files, wrong coordinate or declared identity, changed producer, non-integer/wrong slot and a stored record checksum different from the retained verified checksum. `later_completion:779–788` checks the retained producer is a later bound job that planned the coordinate in that slot before invoking that current check. Status `:244–247` and admission `:874–876` use the same predicate. This closes the original unbound/earlier/wrong-slot disk-only examples.

One part of the original R1 request remains: **validate the current timing's contract**. The unchanged verifier's `timing_ok` (`row19_screen_verify.py:93–105`) requires `wall_s`, `fit_seconds`, `maxrss` and `t` to be finite, nonnegative, non-boolean numbers. The new current check validates coordinate/identity/job/slot (`admit:762–766`) but never checks these four fields. Its strict JSON read accepts a negative number and does not require absent measurement fields. `timing_scan:713–728` rejects unreadable/non-object/non-published/killed-job timing, not invalid measurements.

Concrete static trace: after a clean receipt for the valid later P4 retry at rep51/index0, change only its current canonical timing to the same rep/index/identity/P4/slot0 with `wall_s=-1`, or remove `fit_seconds`. Leave the genuine valid scientific record, retained verifier, watch, bindings, plans, ledger and PBS output unchanged. The current helper returns clean, while a newly run full verifier would reject that timing. `evidence:391–447` validates current records, not timing; receipt unit reconciliation uses retained verifier units, and transition/envelope checks add no current measurement validation. The exceptional disposition can therefore still borrow the retained `timing.ok` for an invalid current artifact in both status and admission. This trace was established from source, not executed.

**Required closure:** apply the same four-field timing validity contract to the current canonical file alongside the repaired producer/coordinate checks, or bind the actual verified timing bytes and refuse changed bytes until recollected. Add post-watch disk-only negative checks with retained verifier/receipt fixed and a genuine valid record untouched: missing, negative, nonnumeric and boolean values in each required measurement field. Both status and admission must hold; restoring the valid timing must preserve the legitimate bound retry. No requirement to reject every harmless JSON formatting change is introduced.

The helper compares the record's stored checksum field rather than recomputing its payload itself. Main admission separately validates the current scientific record via `read_record`/`read_cache`; this record does **not** claim a scientific-record corruption bypass at main admission. The remaining blocking trace is the timing validity omission above.

## R2 and R3 — closed

**R2:** status `:267–269` carries settlement note/time/token/PBS ID/plan digest beside the charge. `certificate_problem` (`admit:794–803`) validates finite nonnegative charge/time and a substantive note, then compares the observed charge/note/time/token/job exactly with the current entry. Disposition `:832–834` invokes it; `:845` also binds the disposition's plan digest to the bound and current plan. Transition `:1065` invokes the same certificate check. The retained tests mutate valid note, nonnegative time, zero versus observed time and negative time without changing charge, and check both admission and transition refusal; certificate-less and wrong-plan receipts also hold. Charged loss remains unchanged.

**R3:** `envelope_problem:654–657` now requires an exact non-boolean integer core count equal to the resolved envelope, without truncation. The full reservation matches both the envelope and the entry's own cores × walltime. Retained tests refuse `24.5`, `24.0`, `True`, `"24"` and self-consistent 24.5/1,176 entries at receipt and prospective envelope checks. This closes the original fractional-core trace.

## Migration and limits retained

After the narrow R1 repair and favourable exact-package review, preserve the old controls adoption, pilot review, qualification, named full verifier and supporting watch/PBS bytes and digests **before** replacement; qualifying overwrites the same qualification filename. Pause admissions during promotion, promote exact reviewed candidate bytes plus the pinned policy, and commit/adopt the actual controls digest and new review SHA coherently across observer/controller clones. Changing candidate controls metadata during promotion changes its digest and needs a matching review. Running producers keep their original paths/manifests/bindings/requests.

Then collect real v8 `--qualify 1` against retained job-1 evidence, without rerunning fits. Return the actual new qualification/full-verifier/production receipt/upload/accounting evidence for bounded migration review and a literal digest-bound pilot authority with **refit max_job100**. Its digest is unknown now; no old digest, fixture or wildcard substitutes. Originals are complete, so no originals re-adoption is required solely for refit admission. After actual pilot adoption, job 10 still requires a fresh whole-role zero-alarm v8 receipt within 2,700 seconds binding actual job-3 output/settlement, unchanged bindings/pins and current funding/capacity/STOP gates. This sequence remains favourable in principle, independently of the unresolved implementation check.

The corrected budget wording distinguishes **49** synthetic-fixture requests from dated actual arithmetic: spent1,892.81 + live4,320 leaves53,787.19, or **46** full1,152 reservations. Neither is current scheduler accounting or batch permission. Campaign cap60,000, highest job100, common100,000, prior losses and per-request locked funding remain. The 48-hour request/deadline design is not a runtime-tail guarantee.

Future numerical release still needs updated admit **and** controls consumer pins and separate actual-target authority. No T/endpoint/coverage/numerical release is granted. Fixed attempted100/B200, seeds/draws/pairing, science seals, raw-bank scope, HEAL hold, shard STOP192, prior closed reports/exposure disclosures and foreign files remain.

Claude owns the narrow remaining timing repair, source-run checks, promotion/adoption/qualification, ledgers, dispatch and current docs/tracker/frontmatter/generated INDEX. Codex owns this record and its own R052/lifecycle entries only. Return one committed repair package; no completed earlier review or report needs replaying.
