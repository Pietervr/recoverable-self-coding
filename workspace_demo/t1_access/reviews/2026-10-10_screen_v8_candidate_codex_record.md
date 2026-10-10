# R052 — screen version-8 candidate implementation review

Date: 10 October 2026 UTC. Reviewer: Codex, `GPT: R052 Entropy paper`.
Candidate: RSC `c1956ef`; incoming brief Unimog `d84beb2f`,
`prompts/2026-10-10_codex_r052_screen_v8_candidate_review.txt`, SHA256
`7cefa2a13cb91adb37557f27c690b408ce1de723e47bbe23a8c56d6a01a062fd`.
Ownership committed at Unimog `04f97ff2`; handoff
`e5c6d70d-4423-538d-af02-c8184e68415a` accepted before review edits/delegation.

## Two requested verdicts

| Question | Verdict |
| --- | --- |
| (i) Version 8 candidate as built | **NOT FAVOURABLE.** Repair R1–R3 below and return exact committed bytes with the bounded negative checks. The disposition and prospective resource designs in `a86debe` remain favourable. |
| (ii) Promote this candidate and adopt it for job 10 | **NOT FAVOURABLE to promotion of these bytes.** The proposed generation migration is sound in principle, with the evidence-preservation and actual-qualification steps below. Job 10 remains held for repaired implementation review, adoption and a fresh zero-alarm whole-role receipt. |

This record contains **no controller or pilot ADOPT authority**. The owner's standing conditional go carries forward; no repeat go is requested. The owner’s 10 October 03:1x UTC instruction to continue Lengau operations is recorded in R052 and carries forward. This review does not reinstate the earlier operating stop. Existing independently gated bank scope through job 17 and source operations remain under that instruction. Codex performs no Lengau operation or dispatch.

## Evidence and exact package

Read the whole incoming brief and candidate design note, candidate/controller differences, relevant unchanged verifier/worker/ledger/adoption paths, prior `a86debe` disposition/resource record, R052 header/latest log, and retained local harness/output. Three read-only reviewers independently inspected disposition, resource binding and adoption. Static checks used file hashes, Python AST parsing without imports and deterministic resource arithmetic. No candidate execution, test rerun, scientific import, fit/simulation, new endpoint/target/coverage analysis, private plant/key/reader/PC output, account operation, worktree or push occurred.

All four candidate files match their committed `c1956ef` bytes and the brief:

| Path relative to `chpc/` | SHA256 |
| --- | --- |
| `candidate_v8/row19_screen_admit.py` | `e62f289bc9e0d970960347af7ad2fa5df079c2d18f17781fa9e93ca5e45a2242` |
| `candidate_v8/row19_screen_status.py` | `3457c9e8fb555c4f12747d6dcdaacf258781495b051da397357041ed289905bf` |
| `candidate_v8/row19_screen_controls.json` | `76aa22f9a960b2c0d1613ab9f4865cd50bb92453561fd8945249932b318af92f` |
| `row19_screen_resources.json` | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |

Canonical version-7 admit/status/controls remain `573e5b18…` / `dac142fb…` / `43a099ca…`. The scientific manifest `43b75f94…`, shard worker `828d5964…`, verifier `d8d3c73b…`, release `7a67fd1f…`, programme gate `10a53402…` and bank manifest/submit `d895c8a3…` / `88fd335e…` match the committed unchanged bytes. Review findings below use line numbers in the candidate files unless qualified otherwise.

Source output `tests_v8_output.txt` reports **12/12 new checks and 88/88 regression checks passing**; those results were read, not independently rerun. Its real-snapshot disposition demonstration uses synthetic PBS output, as disclosed (`tests_v8.py:556–571`). Claude's separate observation of the actual 2,589-byte job-3 output naming `7527352.sched01` with no admission-failure marker is source-reported evidence. A real fresh observer receipt must retrieve/bind those actual bytes; the fixture cannot supply it.

## R1 — current timing provenance is not recomputed for later completions

`admit:746–825` promises an independent current-root disposition check. It scans current timing files (`:705–720`) but only rejects unreadable/non-JSON/non-object files or a timing naming the killed job. For a disposed coordinate with files, `coordinate_files` checks filenames (`:723–734`), then `later_completion` checks the **retained verifier’s** timing/job/slot (`:737–743`), without comparing it to the current canonical timing file.

Concrete static counterexample: after a clean receipt showing a later bound job P4 completed rep51/index0 in slot0, change only its current canonical `timing/rep51/t_000.json` to a readable timing naming unbound P999, earlier P1, or P4 in wrong slot23. Keep its valid scientific record, retained verifier, plans, ledger, task bindings and PBS output unchanged. The direct scan ignores those non-P3 producers; `later_completion` still sees the old valid P4/0. `main/evidence` validates the current record, not timing (`:384–440,1359`); `units_problem` uses the same retained verifier (`:884–924`); transitions and bound checks bind no current timing digest (`:484–504,985–1009`). These predicates can remain clean despite current unsupported provenance. This trace was derived from source, not executed.

Version 7 already used retained unit evidence for ordinary jobs; this is not described as a new ordinary-job regression. **The new exceptional waiver does not establish its stated current-root safety predicate.** Validate the current timing's contract, coordinate, identity, producer and slot against the retained verified evidence, or bind the current artifact bytes and refuse any changed/absent evidence until recollected. Preserve a genuinely later bound planned completion and the disposed job's unchanged historical uncompleted partition.

Add a disk-only post-receipt mutation check for each unbound/earlier/wrong-slot producer, keeping the retained verifier/receipt fixed. The existing retry negatives change verifier units and rebuild the receipt (`tests_v8.py:324–329`); they do not test this case. Also require current absent/changed timing and changed record evidence to hold rather than borrowing the retained verdict.

## R2 — the observed settlement certificate is not bound

The brief requires unchanged token/job/plan/**note**/charge. Status returns the charge but not `settle_note` or `settled_at` in its disposition (`status:260–262`); receipt bindings likewise omit them. Admission checks only that the **current** note has at least eight characters and the current time is finite (`admit:767–771`), while transition checks compare state, job ID, charge and runner fields (`:998–1000`). A different valid note or another finite settlement time therefore need not trigger recollection. Admission even accepts a negative finite `settled_at`, although status requires it nonnegative (`status:211–213`).

Bind the observed settlement certificate, including nonnegative time, note and charge, with token/job/plan identity; compare it to the current entry at admission and transition, or bind the relevant entry digest. Preserve the actual charged loss; do not rewrite settlement to make a receipt pass. Add valid-note replacement, nonnegative-time replacement and negative-time mutations **after** a clean watch, with unchanged receipt. The existing missing-note check (`tests_v8.py:220`) demonstrates absence detection, not continuity.

## R3 — the current reservation's core count is truncated

`envelope_problem` accepts any finite numeric `entry['cores']` for which `int(cores) == 24` (`admit:647–650`). Thus 24.5 cores, walltime 172,800 s and reserved charge 1,152 pass this comparison although the entry's own product is 1,176. The programme counter checks declared charges, not cores (`programme_gate.py:97–109`); the ledger validator accepts positive fractional cores, and runner-start also truncates (`row19_ledger.py:102,173`). Integer validation in `reserve` protects newly generated entries, not changed current entries.

Require an exact non-boolean integer core count equal to the resolved envelope, without truncation, and consistent exact full-request charge. Add a current-ledger fractional-core mutation after a clean prospective receipt; ensure receipt/admission refuse it. The exact pinned 48-hour policy itself is integral; no hypothetical resource-policy expansion is requested.

## Checks that work and the remaining resource scope

The narrow F/integer-exit, settled-charge, token/job/plan, no-runner-end, scoped-status, killed-job/orphan/temp/unreadable-timing, canonical-coordinate and bound-readable-output paths are present. Failed output retrieval cannot prove absence of admission failure. Only the three intended scheduler-exit/runner-end/missing-status alarms are suppressed; memory, binding, foreign, record and anchor paths remain. The exit and zero worker counts remain visible; both status and admission reject a dispositioned pilot. Version-7 ordinary historical partitions remain. A removed disposition claim falls back to ordinary terminal validation.

The separately pinned walltime-only policy is the right approach. Every new refit job at or above 10 resolves to serial/24/48 h/120 GB/haswell_reg/reserve1,800/per_slot1. Plans, PBS request, deadline/start arguments, reservation and prospective receipt checks consistently carry 172,800 s and 1,152 full core-hours. The unchanged shard job-start compares supplied walltime with the reservation, so it can accept 48 h without editing the 30-hour scientific manifest. Jobs 1–9 and originals retain their manifest envelopes. Checking the policy pin for every refit, and applying the added scheduler-envelope reconciliation only to jobs from `first_job`, is appropriate for historical compatibility. Existing historical and fresh whole-role checks remain required.

**Budget correction:** the brief's “49 more requests fit” is the synthetic fixture's balance (spent plus live 3,312.55; room 56,687.45). R052's recorded actual refit balance is spent 1,892.81 plus live 4,320, leaving **53,787.19**, or **46** full 1,152-hour reservations. This dated arithmetic is not fresh scheduler accounting or a batch permission. Settlement may change available room; the locked current campaign/common funding gates decide each request. Cap60,000, highest job100, common100,000 and all existing losses remain; no guarantee of all B200 work or runtime tail is adopted.

The reported done48/in-flight144 and first retry reps51–74/index0 follow the unchanged planner at that retained snapshot. Recompute from actual valid missing/unreserved work before submission; do not force that plan if evidence has moved.

## Adoption path after repair — actual evidence, same scope

The source's generation migration is appropriate after a favourable review of the repaired exact package:

1. Preserve the old controls adoption, pilot review, qualification, named full verifier and supporting watch/PBS evidence with their digests. Archiving only `gate/review_refit.json` is insufficient: `status:519–527` overwrites the same local/remote qualification filename.
2. Promote the reviewed candidate files to canonical paths, with the exact resource policy, and commit/adopt their actual new controls digest and review SHA. Keep observer/controller-clone bytes coherent; admissions remain paused during the switch. Running jobs retain their original producer paths/manifests/bindings/requests.
3. Recollect real `--qualify 1` under the adopted generation against the retained job-1 evidence. This is validation, not a fit rerun. The unchanged verifier can report the latest lineage version containing its exact bytes (`row19_screen_verify.py:43–55`). Old generation-7 qualifications correctly refuse under version8 (`admit:867–881,1057–1093`).
4. Return the actual new qualification, retained full verifier and supporting production receipt/upload/accounting evidence for bounded Codex migration review. The new qualification digest is presently unknown. A fixture-generated qualification, an old digest or a wildcard cannot substitute for a literal pilot ADOPT on the real artifact (`admit:1133–1177`). Preserve scope **refit max_job100**; originals are complete, so no originals re-adoption is needed solely to admit refits. Their old qualification remains historical generation-7 authority.
5. After the actual pilot ADOPT is committed/adopted, require a fresh production zero-alarm whole-role receipt within2,700s, actual job-3 output/settlement evidence, unchanged bindings/pins and current funding/capacity/STOP gates before job10.

No adoptable literal line is issued for the rejected candidate. Repaired bytes need new exact pins; the later actual qualification needs its own literal digest-bound line. Future numerical-release adoption also needs updated consumer pins for **both admit and controls** (`row19_screen_release.py:64–66,184–194`), plus the separate actual-target review. This review grants no T/endpoint/coverage or numerical release.

## Ownership and next step

Claude owns candidate repairs, source-run bounded checks, promotion/adoption/qualification, ledgers, dispatch and current docs/tracker/frontmatter/generated INDEX. Route R1–R3, the fixture-versus-actual budget correction and adoption sequence into that lane; return a concrete committed repair package. Codex owns this record and its own R052/lifecycle entries only. No running job or watcher was changed. Fixed attempted100/B200, seeds/draws/pairing, scientific seals, raw-bank limits, HEAL hold, shard STOP192 and prior closed reports/exposure remain. The owner's operating ruling and standing conditional go continue; no new owner permission is needed to repair and return the bounded package.
