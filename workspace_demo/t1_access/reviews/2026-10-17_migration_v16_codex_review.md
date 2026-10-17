# Migration v16 scripts — Codex review

17 October 2026. **CHANGE 4 before the switch-over.** The reviewed v16 controls remain favourable at `01976b6a…`; this migration package is not yet ready to execute. Its archive, drain observation, job-clone digest and fake-toolchain boundaries need the repairs below. The owner's go remains conditional on the scripts passing review; no new owner-permission question is raised.

Reviewed package: RSC `1d3c873c1b49b1dfbfdda49ffa71c5625c036948`, `workspace_demo/t1_access/chpc/migration_v16/`. Paths below are relative to `workspace_demo/t1_access/`. Exact brief: Unimog `prompts/2026-10-17_codex_r052_migration_v16_review.txt`, commit `13cf2932987eef6e9ae9885f68c4c30c10da38cc`, SHA256 `cd7e3a4ace6662371b5937e3c52bf2900f044b9b286cc5d46c495f4ee6b7c8e8`. Ownership was committed at Unimog `630309675605e379c39a39c823470417b119c5aa`, then handoff `16d147df-4dd7-500d-89ce-47b8e8d31e50` was accepted by **GPT: R052 Entropy paper**, native `01a0d19e-2127-7051-9a61-6db771088559`.

This review read the runbook and all six scripts, their relevant authority/qualification dependencies, and used bounded private shell/metadata probes. Three readers checked archive/preflight, promotion/deployment and pilot rollover/test claims. No script, live tree, ledger, worker or scientific output was changed; no real ssh/scp, scheduler/AWS operation, fit, model draw or migration was run. Concurrent p80 repairs are outside this assignment.

## R1 — P1: a checksum file does not establish a complete recovery archive

`archive_v15.sh:57–60` accepts an existing Lengau archive if its listed files verify and it contains the pinned qualification line. It never requires the promised controller files, active review, budget phases, ledger or job inventory. A private archive containing **only** `gate/qualified_refit_job1.json` plus its one-line `SHA256SUMS` passes that exact branch and prints “archive exists and verifies”. A digest manifest can verify an incomplete set perfectly.

New construction also skips missing controller inputs (`:73–75`), leaves the checksum pipeline unchecked (`:78`), and does not verify a mandatory complete inventory before reporting success. `deploy_v16.sh:43` only checks that `SHA256SUMS` exists; it does not validate the archive before changing and committing the controller clone. A private extracted-deploy probe with a malformed checksum file still copied the new files and returned zero. This defeats the explicit archive-before-promotion/deployment prerequisite.

The Mac checks have a related hole: `archive_v15.sh:24–27` requires six lines and only two named pins. `promote_v16.py:92–110` requires the four pinned v15 files plus the qualification, but not the budget-phase filename. Those five required files plus an arbitrary sixth checksummed file can omit the promised `row19_screen_budget.json` while satisfying both checks.

**Fix:** define and verify the mandatory inventory for each archive, with a captured manifest for variable gate/job contents. Require every expected source and copy/hash operation to succeed; capture the controller HEAD, all required controller bytes, old active review/qualification, budget phases and ledger explicitly. Stage construction, verify every digest and exact required inventory, then publish a completion marker/manifest atomically. On reuse and immediately before controller mutation, verify that same complete certificate and the expected v15 identities. Mere existence, line count or a self-consistent subset is insufficient. Reject malformed, missing, extra/substituted required entries and interrupted archives. Do not overwrite partial evidence; report or explicitly recover it.

Add negative fixtures for the one-file remote archive, a missing ledger/budget/controller file, failed checksum command, substituted Mac sixth file and archive corruption between creation and deploy.

## R2 — P2: failed drain/lock observations can be treated as “drained”

Process scans at `preflight_v16.sh:52–53,65–66`, `archive_v15.sh:62–63`, `deploy_v16.sh:46–47` and `rollover_pilot_v16.sh:17–18` filter `ps` output without checking whether the inventory command succeeded. An empty result from a failed `ps` is accepted as no controller process. A private exact-branch probe with `ps` exiting 23 passed the drain check.

The warn-only fallback at `preflight_v16.sh:67–71` is **not acceptable as proof that the locks are free**. A private process held an exclusive programme lock; with `flock` unavailable, the exact branch printed WARN and returned zero. A successful process-name scan cannot replace observing the lock, whose holder need not match those names.

**Fix:** capture and check the process inventory first, then distinguish a valid no-match from observation failure. Probe both locks through checked `flock` or a Python `fcntl.flock(LOCK_SH|LOCK_NB)` fallback using the same lock files; refuse if no reliable probe is available. Check git/status observations similarly rather than treating failed output as clean. Keep the operator's coordinated admission hold throughout the migration: a successful instantaneous probe is not a lock held over the whole cutover. Do not stop workers or reapers to obtain it.

Add process-inventory failure, unavailable probe and actually held-lock tests. Existing “busy process” refusal tests alone do not cover these failure paths.

## R3 — P2: an incomplete job-clone digest can be reported unchanged

`deploy_v16.sh:55,58` does not check the exit status of either job-clone science hash command. When the same file is missing/unreadable before and after deployment, both commands can produce identical **partial** lists. Their comparison then prints “science bytes UNCHANGED”. The later controller-clone pin/authority checks do not validate the job clone's complete file set. `preflight_v16.sh:92–93` likewise prints its success after an unchecked hash pipeline.

A private extracted-remote deployment with the job-clone `analyze.py` absent produced two hash-command failures, matching partial lists, “science bytes UNCHANGED”, no ABORT and a zero remote exit. This is a false verification result even though the script did not itself delete that file.

**Fix:** require every expected science input to exist/read and every digest command to succeed. Compare an exact fixed inventory and complete before/after manifests; fail before controller mutation if the initial proof is incomplete, and refuse completion on any after-check failure. Apply checked pipeline/error handling throughout; `set -u` alone does not do this, and adding `set -e` alone does not validate every pipeline. Preserve the job clone as read-only.

Test missing/unreadable science input, digest-command failure, partial output and changed digest. A success-path hash comparison does not establish these refusals.

## R4 — P2: a marker alone does not confine the production test hook

The fake-toolchain guards check only for `FAKE_LENGAU`: `preflight_v16.sh:56–63`, `archive_v15.sh:47–55`, `deploy_v16.sh:31–41`, and the first hook branches of both pilot scripts. They do not resolve the selected root or reject a real-toolchain alias, nor require controller/gate/archive/patch destinations to remain inside the marked fake root after symlink resolution.

Thus the guard establishes deliberate opt-in, not the brief's stronger requirement that the test route cannot operate on the real Lengau tree. A marked private root with `rsc_screen_ctl` pointing outside it passes the guard. In an independent two-private-directory test, `adopt_pilot16.sh` copied its review into the sibling clone outside the marked root and returned zero under its mocked adopter. This proves an actual write can escape the test boundary; it does not prove a real qualification would pass. No unmarked production root is claimed to pass, and no real root was tested or changed.

**Fix:** remove the test hook from production scripts and inject fakes only into private copies, or enforce a shared strict test-root policy: canonicalize paths, reject the production toolchain and aliases, constrain test roots to an explicitly private location, and require every mutated controller/gate/archive/patch destination to resolve beneath that test root. A marker is additional evidence, not the containment check. Keep ordinary production invocations on the fixed production route.

Add negative alias/symlink escape fixtures using private directories only and a valid isolated fake-root fixture. Never create a marker in the real toolchain to test this.

## Accepted mechanics and remaining gates

The Mac promotion's exact candidate/review pins, committed literal, preserved v15 entries, controls-last ordering and per-file atomic replacements are appropriate. Its mixed v15/v16-state recognition provides a useful interrupted-promotion path. The remote target is the controller clone, not the scientific job clone. The new controls' first-job-alone/scale-up gates remain unchanged by these scripts.

Remote deployment interrupted during copying or before its commit leaves a dirty controller clone; rerun refuses that state. This is a safe hold, consistent with the runbook's “resumes or refuses” language. Preserve/report that dirty state and use an explicit verified recovery before continuing. The completed-promotion fast path (`promote_v16.py:124–146`) recognizes only three adoption fields and skips archive verification; tighten it to full authority/archive validation or label it only a no-write state report. Later deploy authority checks still refuse a malformed adoption, so this is a P3 recovery/reporting qualification rather than an additional demonstrated release escape.

The raise-cap command is the supported two-phase `--raise-cap 81000`; the controller takes the programme lock internally, retains pending-phase/history checks, and does not raise the 100,000 programme limit. Fresh lock-held accounting immediately before it remains mandatory; the old cost illustration is not a reservation.

The pilot sequence should remain: verify archived old review/qualification, retire the old review, make **one** qualification-metadata call on existing job 1, stop on NOT QUALIFIED, package/commit the exact new evidence, obtain the new qualification-specific pilot literal, then use the supported adopter. The scripts contain no pilot fit or worker/reaper stop. The supported adopter checks the actual qualification and tracked literal and refuses overwrite; the historical `3c605514` literal cannot authorize the new hash. A rerun that safely refuses an already retired/adopted state is acceptable when the runbook describes it honestly. Actual qualification/adoption success is not proved by mock guards.

After repaired scripts pass review, the owner's existing conditional go permits Claude to execute the documented cutover. Fresh receipts, new pilot adoption and the **one** intended new-order job precede its separate actual-resource/scale-up review. This migration review supplies none of those later literals and does not release p80, rescue or a new EC2 epoch. No favourable migration literal is issued for the current script bytes; A's earlier controls literal is not a substitute.

## Verification and limits

All findings have bounded private evidence:

- `/private/tmp/r052_migration_preflight_archive_probe_20261017.py`: exact existing-archive branch accepts the qualification-only archive; failed process observation passes; an exclusively held private programme lock passes when `flock` is absent; marker guard accepts a symlink escape.
- `/private/tmp/r052_migration_deploy_proof_20261017.py` and `.json`: extracted remote deployment body accepts a malformed archive, and returns zero with “science bytes UNCHANGED” after both job-science hash reads fail on a missing file. Private git/ps/t1py mocks isolate these shell guards; no real commit, transport or authority validation was performed.
- `/private/tmp/r052_migration_rollover_audit.py`: **12/12 ordinary bounded expectations**, plus the separately reproduced failed-ps retirement. `/private/tmp/r052_migration_rollover_extra_20261017.py` demonstrates the private symlink write escape. Both pilot shell scripts pass `bash -n`; their source and runbook still match `1d3c873`. Positive adoption is a strict literal-only mock, not real qualification, git authority or provenance validation.

The builder's setup/four scratch harnesses were read but not rerun against their fixed mutable test roots. Their “~35 refusals” is not independently certified here. In particular, a wrapper filters a “No user named” diagnostic from the simulated process scan, and manual case output is not proof that the original command failed closed. Prior r13/r14 controller regressions are not migration-shell tests: the preceding audit found 51/51 for r13 and the same 70/71 stale replay for r14 in live and candidate. They were not repeated here.

Real ssh/scp, GNU `flock`/`sha256sum` transport behavior, real positive `--raise-cap`, `--qualify`, `--adopt-review`, and the actual remote clone commit remain untested. Those limitations do not excuse the reproduced guard failures; repair and retest their negative paths before executing the cutover. The qualifying status workflow and supported adopter were inspected statically rather than invoked. Successful private-path tests cannot establish production resource/qualification evidence.

No repository file other than this review is owned for mutation. Foreign p80 work and the other existing files are preserved. All private probes are synthetic administrative tests, not scientific results, and all readers finished without task-owned listeners or scientific jobs.
