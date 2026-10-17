# Migration v16 — narrow legacy-tool compatibility review

17 October 2026. **FAVOURABLE for the compatibility repair at RSC `93a4daf8593941cf7f8ebe897c8736266b7c4c68`, with a nonblocking P3 test-description correction below.** The Git-directory checks are not weaker, and no held or unprobeable lock is newly accepted as free. The operational next step remains a fresh full live read-only preflight under the existing owner go; this record does not claim that the preflight or migration has succeeded.

## Scope

Read the complete brief `Unimog-Projects/prompts/2026-10-17_codex_r052_mig_compat_review.txt`, commit `2bd738342aca5b6b6bb9dd0b6efaaae3655a3f00`, SHA256 `3ea77636beea8e6cd1b7445841b498cf1150cb9071d99c02ba413fce0ff2b8c4`, and the complete `e3018d8..93a4daf` diff in `chpc/migration_v16/`. Read the changed source/test context and the preceding favourable review `reviews/2026-10-17_mig2_e2n_codex_review.md` (`0b8a2e16`). Paths below are relative to `workspace_demo/t1_access/` at the reviewed commit.

Ownership was committed in Unimog at `c32d6083940d4854005a4d1e0bf1a4d10d4d8bb2`, then handoff `3e3f41c4-8bdc-51e8-a650-f90a6a5e9c7c` was accepted before review edits. Exact session remains `GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`. Three bounded readers independently checked Git semantics, lock/platform semantics and the sanitized administrative suite.

## Compatibility and preserved authority

The migration-folder diff is confined to `remote_lib.sh`, one HEAD query in `archive_v15.sh`, the harness and runbook. Production changes are the directory-subshell Git calls, legacy `--git-dir` normalization and default `flock` conflict mapping. Deployment/archive inventories, payload pins, science manifests, proof/recovery rules, admission controls and qualification gates are unchanged. The prior review's nonblocking `deploy_v16.sh:181` final-digest P3 remains; this patch does not fix it.

**Git: favourable.** `remote_lib.sh:88–99` checks both Git query statuses. Empty output refuses. An absolute Git-directory result must already name `$CR/.git`; a relative result is resolved from the exact controller directory. Physical resolution must still equal `$CR/.git`, which must be a real canonical directory; the worktree must still equal `$CR`. A gitfile or symlink redirect elsewhere therefore cannot become valid merely by resolving its target. Resolving legitimate relative output is necessary for the older interface and does not authorize another Git directory.

`git_clean:156–159` and `archive_v15.sh:74` use checked `cd` subshells, so a failed directory change cannot query some other working directory or alter the caller's directory. Failed Git status remains a refusal. The production root, path-containment checks and controller/science separation remain intact. Git1.8.3.1's upstream implementation supports `--git-dir` and `--show-toplevel`, while its global-option handler does not implement `-C`. [Git1.8.3.1 options](https://raw.githubusercontent.com/git/git/v1.8.3.1/git.c), [revision parser](https://raw.githubusercontent.com/git/git/v1.8.3.1/builtin/rev-parse.c).

**Locks: favourable.** `remote_lib.sh:144–153` accepts0 from the nonblocking shared `flock` probe, refuses1 directly and sends every other failure to the checked same-file Python `fcntl` probe. The fixed child command is `true`. A status1 caused by some other failure is conservatively held; it is not mistaken for free. An absent command or failed utility can proceed only if the fallback actually acquires the shared nonblocking lock. Fallback75 holds; every other nonzero status refuses. The existing-file check and both controller lock paths remain unchanged. A successful observation is still an instant, not a lock held across migration.

## P3 — describe restricted shims accurately

`remote_lib.sh:86–87,148`, `RUNBOOK.md:375–381` and `test_migration_v16.py:18–23,182–190,203–225,869–887` overstate version fidelity. **Upstream util-linux2.23.2 already supports `-E`/`--conflict-exit-code`**; its source lists and handles that option, and its default conflict exit remains1. The version number alone does not establish that Lengau's installed executable rejects it. [Upstream flock2.23.2 source](https://raw.githubusercontent.com/util-linux/util-linux/v2.23.2/sys-utils/flock.c).

Similarly, the Git shim rejects `--literal-pathspecs`, although upstream Git1.8.3.1 accepts it. That option is not used by the reviewed route. These deliberately stricter shims are useful fault models, but passing them on modern host binaries is not execution on the exact historical binaries. The new production no-`-E` path remains valid; no unsafe lock acceptance follows from this documentation/test-model defect.

**Fix:** correct the version assertions and label the shims as selected restricted-CLI tests, or implement the actual version's supported interface. If a particular installed wrapper/build lacks a flag, record that observed command failure separately rather than infer it from the upstream version. Keep the `-C` regression test and the independent held/error/fallback tests. This P3 does not block the production compatibility repair or require new spending authority.

The Python test at `test_migration_v16.py:811–866` is also a conservative syntax/API scan of seven selected sources, not a Python3.6 runtime or full-controller certification. It parses using3.7 grammar plus a finite API blacklist and rejects all f-strings. The brief reports that actual `$T/t1py` is3.12.10; the controller is not being switched to system Python3.6.8. No new unsafe Python call was introduced by this patch.

## Verification and follow-through

The independent sanitized suite passed **42/42 in238 seconds**, outer exit0, with pinned source and real migration sources unchanged. Every selected committed source blob and migration code/test byte used matched `93a4daf` before execution. Focused private Git checks passed **21/21**, including absolute/relative/empty/malformed output, query/directory failure, external Git environment and actual gitfile/symlink fixtures. Focused private lock checks passed **49/49**, covering direct0/free and1/hold, error exits with successful/held/failed fallback, command absence, a missing file and actual local `fcntl` free/held outcomes.

All suite execution used a sanitized private source snapshot with protected paths excluded before checkout/tree hashing, explicit read/import/process/network guards and no real transport. Its1,245-path inventory contained zero protected paths; no protected payload was opened in this pass. The sole extra source fixture was the already-known ignored administrative pilot-qualification receipt, checked against fixed `3c605514…` before copying; it was not generated or scientifically recomputed. The prior pass's protected-byte hashing incident remains disclosed at `0b8a2e16`; it is not erased or treated as blind calibration. This pass did not rerun that unsafe snapshot or the old final-digest counter. Administrative fixtures establish no scientific result, real Lustre semantics, live old-tool invocation or positive pilot/cap/scale-up outcome. The guards supplement inspected private destinations; they are not an OS sandbox.

Evidence: `/private/tmp/r052_mig_compat_git_review_20261017.md`, `/private/tmp/r052_mig_compat_git_checks_20261017.py/.json`; `/private/tmp/r052_mig_compat_lock_review_20261017.md`, `/private/tmp/r052_mig_compat_lock_matrix_20261017.py/.json`; `/private/tmp/r052_mig_compat_suite_review_20261017.md`, `/private/tmp/r052_mig_compat_suite_20261017.py/.log`. All are administrative review artifacts.

The bounded scripts-review approval is:

FAVOURABLE row19-screen-migration version=16 scripts_commit=93a4daf8593941cf7f8ebe897c8736266b7c4c68

Retry the **full live read-only preflight** before any write; `--local-only` remains insufficient. Report another compatibility/identity/path/lock refusal without bypassing it. The prior ordered archive/promotion/deploy procedure, fresh whole-programme budget and supported cap phase, fresh whole-role receipts, one existing-pilot qualification-metadata call/no fit, new exact pilot review/adoption, ONE first new-order job and separate scale-up review remain unchanged. E2, p80 and rescue authority remain separate. Existing owner conditional go carries forward; no new routine permission question is needed.

Only this review file is owned in RSC. No production/source/current-summary/manuscript/ledger edit, real AWS/Lengau/SSH/scheduler/worker operation, scientific fit/draw/numerical release, worktree or push was performed. Foreign files are preserved. All three readers and private runs are complete; no task-owned process, listener or poller remains.
