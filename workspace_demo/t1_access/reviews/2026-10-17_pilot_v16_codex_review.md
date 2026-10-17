# v16 regenerated refit-pilot qualification

17 October 2026. **FAVOURABLE for the regenerated qualification of existing refit job 1**, SHA256 `2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44`, in RSC `08f65f2d9854bd8349d8c285c90d77fc59703b93`. No blocking finding in the supplied pilot metadata, generation binding or retained operating contracts.

```text
ADOPT row19-screen-pilot role=refit qualification=2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44 max_job=100
```

This literal binds this qualification and an absolute campaign job-number ceiling. After its supported adoption and fresh operating checks, it supports **ONE first new-order job**. It does not adopt scale-up, certify concentrated packing, validate interval coverage, enable rescue or release EC2 production. Do not reuse the historical `3c605514` qualification literal.

## Scope

Read the complete brief `Unimog-Projects/prompts/2026-10-17_codex_r052_pilot_v16_review.txt`, commit `e2ab0d0324742f12f2c08d4700397b36a36482df`, SHA256 `29845b939a0109c64242d4ed730341bfa3181771b8910f2bb5b55131934a8def`. Ownership was committed at Unimog `6d6a9134ce4b0a48460d96d25b122af174733b89`, then handoff `d74b6135-88e5-5d89-813b-8d3780d1ad57` was accepted before review edits. Exact session remains `GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.

Reviewed the committed `chpc/qualification_v16_2c7a7ef1/` package, the preceding v15 qualification/review, relevant producer/consumer code and RUNBOOK steps 7–9. Three independent readers checked package/receipts, generation/adopter binding and resource applicability. Paths below are relative to `workspace_demo/t1_access/`.

## Existing pilot, no new fit

The actual qualification hash was independently recomputed; it is the exact new hash above. Its own job binding is still PBS `7523818.sched01`, token `2a25377fe9db`, plan SHA256 `39cbd2eeb7501a24961fdf72ff9c021bad211d492a5bc349df9a4724d1867e94`, with the same 24 task digests for reps 3–26. The manifest `43b75f94…`, root/campaign, all seven scientific source pins and wrapper pin are identical to the prior qualification. All seven current local source files also match those scientific pins.

The **entire pilot job summary is structurally identical** to the v15 artifact. All 24 pilot verifier-unit metadata records, `3/0` through `26/0`, are also structurally identical: valid records and timings naming that same PBS producer and slots 0–23. Scheduler/runner exits remain 0/0; all 24 workers ended 0; 24 new, zero resumed/left, no failed unit and no disposition. No new pilot producer, timing or task binding appears. This substantiates reuse of the completed pilot rather than a replacement fit.

The qualification itself is new metadata: its timestamp, current verifier/anchor certificate and whole-role observation have advanced. The full verifier now contains 856 unit metadata records rather than the previous 287, and the whole-role receipt covers 45 jobs rather than 13. All prior job and task bindings are retained. The old closed-no-record output pin and job-13 crash-output/error pins are unchanged; additional historical failures remain explicitly dispositioned. “No new pilot fit” does not mean that the intervening campaign history or the complete JSON stayed unchanged.

The source's `row19_screen_status.py:996–1033` qualification path reads the existing clean job, reduces its own binding to that job and its task scope, then writes/copies metadata. It does not launch a fit. This review did not rerun it or independently observe how many times the operator invoked it.

## Current v16 generation and named evidence

The package's 13 files match their committed bytes; its checksum manifest has the exact 12 non-self entries. The retained verifier is `verify_refit_20261017T204309Z.json`, actual SHA256 `ade2b1e432e0875c25908fde824dbc6ab15f212b6bd7db838f5417e445db5159`, matching both qualification digest fields and the embedded receipt. It reports empty code/environment differences and:

- `version=16`, `latest=16`, clean controller-lineage verdict;
- adopted controls `01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220`;
- verifier source `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec`, equal to the current source and latest v16 pin.

Current controls/adoption and the reviewed controller/designated/resource/partition pins agree. Adoption SHA256 is `523fe18adad603af23425cdd4cb41039b4a287254e36aa55ba34d933b0081411`. The anchor verdict agrees across qualification, embedded receipt and verifier; its canonical digest is `fda3c209…`. Required index 0 is equal for anchors 0, 1 and 2, with no conflict, difference, missing or invalid entry. The extra equal comparison at anchor0/index10 is later retained history, not a changed original anchor identity.

All eight directly named historical watch files are packaged and match their referenced hashes. They and the embedded receipt have explicit empty alarms and fresh/production flags. Both archive checksum manifests match the package pins: Lengau `448dc1629981323c6a944ad22ec8c5960dccca7398e9cc8580a45725b214d7ae`, Mac `a90afca3ddf64a9abe1fa01d45976def2c73da341ecea0897c361a25af31b78e`; their 294/6 listed identities retain the predecessor qualification and evidence. Actual archived payloads were not reopened or rehashed in this review.

## Resource applicability and the next gate

The original direct watch `watch_refit_20261010T224529Z.json`, SHA256 `c6fd4a730829d6b17c4d0855231f63507c92892b0e3e473bc39610c20b8400fa`, supplies the same pilot resource values: 47,179,688 KiB scheduler memory (44.994 GiB, 37.495% of 120 GiB), maximum worker RSS 2.3195 GiB, maximum worker runtime 24.3876 h within its historical 30 h request. The new summary correctly labels terminal state as ledger settlement and memory as retained prior-receipt qstat evidence; current qstat fields are null. No memory breach is recorded. Historical measurements are not presented as a new live PBS observation.

V16 retains 24 cores, 120 GiB, one index per single-thread worker and the existing worker memory stop. The prospective policy already gives jobs 10 onward 48 h: one new job reserves 1,152 core-hours. Job 1's old request remains 30 h. Its mixed-replicate success is supporting engineering evidence; it does **not** establish the peak behavior of 24 workers concentrated on one replicate. The saved next-coordinate view is rep3/indices11–34; fresh planning must choose the then-current lowest free coordinates.

The supported adopter requires this exact current gate hash, literal and tracked unchanged review, refuses an existing review and does not overwrite one. Later admission rechecks the qualification and a whole-role receipt no older than 2,700 s, with current bindings, transitions, dispositions, resource envelope, funding and provider constraints. A later stale receipt needs a fresh status receipt, not another `--qualify` call.

Keep the existing sequence: adopt this committed record with `adopt_pilot16.sh`; fresh current receipts and funding/identity/partition checks; `--jobs 1 --dry-run`; then the same ONE-job call if admitted. “Alone” limits new-order admission; existing jobs remain untouched. Every further new-order job remains held until that first job is terminal and settled and a separate actual packing/resource review and scale-up adoption succeed. `max_job=100` supplies none of that later authority. The committed 81,000 refit+S envelope, 100,000 programme stop, disabled rescue and separate E2/p80/EC2 release gates remain unchanged.

## Validation limits

Only source and administrative metadata were read. Deterministic stdlib checks authenticated package bytes, references, old/new pilot identity and current pins; no project imports, simulation, fit, qualifier, adopter, planner, dry run, full suite, SSH/cloud/scheduler operation or job intervention was performed.

The independent package audit passed 99 bounded integrity/consistency checks; the parent comparison and separate generation/resource checks agree on the unchanged pilot and requested scope. These are administrative checks, not a scientific runtime suite.

The package is complete for the qualification's directly named receipts and verifier, but is not a recursively complete forensic archive: five older snapshots referenced within historical watches are unbundled. The original direct job-1 memory receipt is present. Historical PBS output/error bodies are also represented by names and hashes, rather than bundled for a new content audit. They were not opened elsewhere, including foreign fixture files. These limits do not undermine the checked unchanged pilot; they prevent claiming that every historical memory chain or failure body was independently re-audited. Fresh live `receipt_problem` still validates current closed-no-record/crashed-slot bodies before admission and must hold on absent or changed evidence.

The role-wide observation was not atomic. Embedded job partitions list 855 completions; the later verifier contains one additional valid outside-set unit, `77/9`, from still-running job 42/PBS `7543885.sched01`, slot 23. No embedded completed coordinate is missing. The embedded designated scan already accounts for 856 as 515 designated plus 341 outside-set; the earlier packaged watch had 340 outside. The verifier time follows the watch start time by about 106 s. This is consistent with an outside-set worker finishing during collection, with no pilot-unit or designated-denominator change. It is not a reason to reuse a stale receipt or call the snapshots identical.

Private evidence: `/private/tmp/r052_pilot_v16_parent_checks_20261017.json` and its helper; `/private/tmp/r052_pilot_v16_binding_review_20261017.md`, `/private/tmp/r052_pilot_v16_package_review_20261017.md`, `/private/tmp/r052_pilot_v16_resource_review_20261017.md` and their linked metadata checks. No raw fit, protected plant/key/reader/audit/human/pull payload was opened. The previously disclosed protected-byte incident and exposure limitations remain; this pass does not create blind calibration.

Only this review is owned in RSC; Claude retains current summaries/frontmatter, source, ledger, adoption and dispatch. Foreign files are preserved; no worktree or push. All three readers and deterministic checks are complete; no task-owned job, listener or poller remains.
