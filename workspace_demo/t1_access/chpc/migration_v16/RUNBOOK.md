# v15 -> v16 migration (the resized row-19 screen controller) - RUNBOOK, SCRIPTS WRITTEN, NOT EXECUTED

Codex record `reviews/2026-10-17_v16_p80_codex_review.md` (RSC `f6896e1`, SHA-256 `a315d7d2…`), section A: FAVOURABLE for the
exact controls `candidate_v16/row19_screen_controls.json` with the literal

    ADOPT row19-screen-controls sha256=01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220 version=16

(candidate RSC `3686a11`, design `candidate_v16/DESIGN_v16.md`). The literal covers the controls and the pinned controller
implementation only. Codex: "Before operations, finish and review the actual preflight/archive/promote/deploy scripts, archive the
real adopted state, refresh whole-role v16 receipts, regenerate the existing pilot qualification without a fit, obtain its new
pilot literal, and admit the intended first job alone."

The step scripts are in this folder: `preflight_v16.sh`, `archive_v15.sh`, `promote_v16.py`, `deploy_v16.sh`,
`rollover_pilot_v16.sh`, `adopt_pilot16.sh`. They follow `migration_v13/` (preflight, archive, rollover and adopt) and
`migration_v15/` (promote, deploy). They were written and tested on the Mac on 17 October 2026 against a throwaway clone and a
fake Lengau toolchain (the `V16_FAKE_LENGAU` / `V16_T` test hook, which refuses any directory without a `FAKE_LENGAU` marker).
**None of them has been run against the live tree or Lengau.** Nothing in this file has been run.

Where commands run:

- On the Mac, every command runs from `workspace_demo/t1_access` unless marked Lengau.
- On Lengau, `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`, and controller commands run from the controller clone
  `$T/rsc_screen_ctl/workspace_demo/t1_access` through `$T/t1py`, via `ssh -o ControlPath=none lengau ...`.
- Lengau-only scripts run as `ssh -o ControlPath=none lengau bash -s < chpc/migration_v16/<script>`.
- Every step refuses rather than overwrites. Every script is safe to re-run: a completed step reports itself, an interrupted one
  resumes or refuses.

**Never:**

- stop, restart or edit any running refit, bank or EC2 worker or reaper, or the job clone `rsc_screen` and its numerical tree;
- set any permission or qualification by hand;
- edit any campaign ledger or budget file except through `--raise-cap` (step 5);
- change reviewed v16 bytes (the controls, declaration or partition) after review;
- rerun a pilot fit;
- reuse an old ADOPT literal;
- plan more than ONE new-order job before the scale-up review (step 9).

## 0. Preconditions

| Gate | Check | Abort if |
|---|---|---|
| Review | Codex's committed record carries `ADOPT row19-screen-controls sha256=01976b6a… version=16` for the exact `candidate_v16/row19_screen_controls.json` bytes (`preflight_v16.sh` checks it in HEAD) | no literal, or other bytes |
| Scripts reviewed | a committed Codex record on THIS folder's scripts (review section A: "finish and review the actual preflight/archive/promote/deploy scripts") | no record, or the scripts changed after it |
| Old-plan hold | no refit admission since 17 Oct (owner); the refill scripts are not invoked; `slot_watch.sh` is stopped | any admission under v15 after 17 Oct |
| Running jobs | jobs 37-45 (and whatever is live) keep running; their settlements go through `programme_gate.py run ... settle` as usual | - |
| Prior packages | none is required for refit admission; the prefix release (s.6 item 3) and the EC2 epoch (item 5) are separate and may follow | - |

## 1. Drain controller commands, then preflight (Lengau login and Mac)

1. Do not invoke `refill_r1.sh` or `refill_b1.sh`. End the slot-watch task, which only reads `qstat`.
2. Let any controller command already running finish. Then run `bash chpc/migration_v16/preflight_v16.sh`. It is read-only and
   refuses unless:
   - Mac: the live `chpc/` controls, adoption, admission and status are the adopted v15 bytes (`828d3b69`, `970c29f5`,
     `ac06e803`, `0effcba3`), committed, and no `chpc/row19_screen_designated.json` exists; the four candidate files are the
     reviewed bytes (`01976b6a`, `1b02f336`, `a9f9180b`, `a96eb598`), committed, with versions 1-15 equal to the adopted file and
     version 16 pinning partition e1 `8d1de408`; the review record is `a315d7d2`, committed, and HEAD carries the exact literal;
     the Mac `qualified_refit_job1.json` is `3c605514`; the Mac archive does not exist; no refill, slot-watch or controller
     process of this user runs on the Mac.
   - Lengau: no `row19_screen_admit|status|verify`, `row22_bank_submit|status`, `row19_ec2_*` or `row19_partition` process on the
     login node; neither `$T/programme_admission.lock` nor `$T/row19_screen/plans/.submit.lock` is held (a non-blocking shared
     `flock` probe; a WARN if `flock(1)` is missing); `rsc_screen_ctl` is clean at the v15 bytes with no declaration; the gate
     holds `qualified_refit_job1.json` `3c605514` and an active `review_refit.json`, and no `scaleup_refit_v16.json`; no budget
     phase is pending and the ledger cap equals the committed 60,000 phase; `$T/row19_screen/ec2/activation_e1.json` exists;
     neither `archive_screen/v15_before_v16` nor the retired v15 review exists. It prints the job clone's science hashes.

   Expected: `PREFLIGHT OK`. `--local-only` runs the Mac half alone (no ssh); it does not replace the full run.
3. Do not run the Mac's status or receipt commands during steps 2-5. A slot that frees stays empty until step 8.

## 2. Archive the adopted v15 state (Lengau, then Mac)

`bash chpc/migration_v16/archive_v15.sh --dry-run` (Mac checks and the plan, no ssh), then `bash chpc/migration_v16/archive_v15.sh`.

a. Lengau (over ssh): `$T/archive_screen/v15_before_v16/{gate,jobs,ctl,ledger}` with `SHA256SUMS`, all read-only. It copies:

- the whole gate: `qualified_refit_job1.json` (`3c605514`), the active `review_refit.json`, every watch and verify receipt, every
  retained PBS out/err copy;
- the refit job scripts `jobs/row19_screen_refit_*`;
- the v15 controller files of `rsc_screen_ctl` and its HEAD;
- the budget phases `chpc/row19_screen_budget.json` and the campaign ledger `row19_screen_campaign/budget.json`, as reference
  copies only.

It refuses unless the controller clone is clean at the v15 controls and adoption, the gate qualification is `3c605514`, a
review is active and no controller command runs.

b. Mac: `chpc/results/archive/row19_screen_v15_before_v16/` - the v15 controls, adoption, admission, status, the budget phases and
the Mac `qualified_refit_job1.json` (`3c605514`), with `SHA256SUMS`, read-only. `promote_v16.py` requires it.

Expected output: the Lengau archive path, its file count and SHA256SUMS hash and the gate/controls lines; then the Mac archive
and its six lines; `ARCHIVE OK`. An existing archive whose SHA256SUMS verifies is reported and kept (a re-run after an
interruption); one that does not verify refuses. If the Lengau half fails, the Mac half is not written.

## 3. Promote v16 on the Mac

Run `python3 chpc/migration_v16/promote_v16.py --dry-run`, then run it again without `--dry-run`. It refuses unless, in order:

- the candidate controls are the reviewed v16 SHA-256 `01976b6a`, and versions 1-15 are byte-identical to the adopted file;
- the latest entry is version 16, pinning partition e1 `8d1de408`;
- the review record is `a315d7d2`, git-tracked, unmodified, with the literal in HEAD; the candidate files are committed;
- every v16 pin equals its file, taking admit, status and `row19_screen_designated.json` from `candidate_v16/`;
- every other pin equals v15's, and the file set is v15's plus the declaration;
- the Mac archive from step 2 exists and verifies with the adopted v15 bytes;
- each of the four live paths is its v15 or its v16 bytes, and the adoption is the v15 record or the version-16 record.

It then copies the declaration, admission, status and LAST the controls into `chpc/` and writes
`chpc/row19_screen_controls_adoption.json` for version 16 (atomic writes). A re-run of a finished promotion prints `already
promoted`; an interrupted one resumes. Commit atomically (one command):

    git -C ~/Recoverable-Self-Coding add workspace_demo/t1_access/chpc/row19_screen_controls.json workspace_demo/t1_access/chpc/row19_screen_controls_adoption.json workspace_demo/t1_access/chpc/row19_screen_admit.py workspace_demo/t1_access/chpc/row19_screen_status.py workspace_demo/t1_access/chpc/row19_screen_designated.json workspace_demo/t1_access/chpc/results/archive/row19_screen_v15_before_v16 && git -C ~/Recoverable-Self-Coding commit -F <msg> -- <the same six paths>

## 4. Deploy to the controller clone (Lengau)

Run `bash chpc/migration_v16/deploy_v16.sh --dry-run`, then run it without `--dry-run`. On the Mac it refuses unless the
promotion is in place AND committed, and the Mac tree's own authority/lineage/controls/designated checks are empty. It copies
the six changed files to `$T/patches/ctl16.*` and makes one commit in `rsc_screen_ctl` with the promoted controls, adoption,
admit, status, the declaration and the review record (refuses unless `archive_screen/v15_before_v16/SHA256SUMS` exists, the
clone is clean at the v15 controls and no controller command runs). The job clone `rsc_screen` is not touched. A re-run on a
clone that already holds exactly these bytes makes no commit and repeats the checks.

Expected output:

- `science bytes UNCHANGED`;
- `authority '' lineage '' controls ''`;
- `designated ''` (the `A.designated(m, "chpc/row19_screen_manifest.json")[1]` check, run as `$T/t1py` in the controller clone);
- the local-vs-remote pin comparison `IDENTICAL` (19 files);
- `DEPLOY OK`.

The script refuses (exit 3) on any non-empty problem string, a diff or an ABORT line. The e1 activation proof stays valid
because v16 pins the same partition. Do NOT re-activate.

## 5. Raise the refit campaign cap to 81,000 through the two-phase protocol (Lengau, under the programme lock)

Fresh budget check first (design s.6 item 7). Read all programme ledgers under the lock, using the wrapper's own count or the
receipt's funding view. Record the following:

- the programme total, settled plus live;
- the refit+S total;
- that a further 38 ordinary + 2 rescue full reservations (46,080 core-h) fit under CSCI1913 100,000 with the live maxima
  carried.

The design's 03:06Z figures were 52,785.06 committed and 98,865.06 projected. If the projection exceeds 100,000, stop and
return to the owner with a revised costed design. Then run exactly:

    ssh -o ControlPath=none lengau 'cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access && /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --raise-cap 81000 --note "owner 17 Oct 2026: resized row-19 screen adopted (Codex design RSC 08ce9e3 s.3): refit+S sub-envelope 81,000 core-h; CSCI1913 100,000 stays the hard stop"'

Expected output: `cap raised to 81000 (ledger cap_history and chpc/row19_screen_budget.json committed; commit the budget file)`.
The command acquires the programme lock itself (Codex A item 5; no outer wrapper) and runs `cap_problem` (60,000 committed)
first. It then writes the pending phase, raises the ledger (`CampaignLedger.raise_cap`, which records old 60,000, new 81,000,
the note and the time in `cap_history`), certifies cap and history, and commits the phase.

If it is interrupted, repeat the same command to resume, or run `--retire-pending --note ...`. Never edit the ledger. Then
commit the changed budget file in the controller clone, copy it to the Mac and commit it there with explicit paths:

    ssh -o ControlPath=none lengau 'cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access && git add chpc/row19_screen_budget.json && git -c user.name=R052 -c user.email=r052@local commit -q -m "screen budget: refit cap phase 81,000 (two-phase --raise-cap, owner 17 Oct 2026)" -- chpc/row19_screen_budget.json && git log -1 --format=%h'
    scp -o ControlPath=none lengau:/mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access/chpc/row19_screen_budget.json chpc/row19_screen_budget.json
    git -C ~/Recoverable-Self-Coding add workspace_demo/t1_access/chpc/row19_screen_budget.json && git -C ~/Recoverable-Self-Coding commit -F <msg> -- workspace_demo/t1_access/chpc/row19_screen_budget.json

The sub-envelope in controls v16 is already 81,000, so from here the binding limits are the ledger's 81,000, the refit+S
81,000 and the programme's 100,000.

## 6. Fresh whole-role v16 evidence (Mac)

Run `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt`, then the
bank receipt as before: `python3 chpc/row22_bank_status.py --manifest <abs>/chpc/row22_bank_manifest.json --publish-receipt`.

Expected:

- fresh, production, zero alarms;
- the verifier stamps generation 16;
- the printout carries the `DESIGNATED S x 0..79` line;
- RESCUE-PENDING lists 43/4 and 83/2, with `attempt_running` while job 37 is live;
- the receipt carries `designated`.

Any `designated set:` alarm stops the migration.

## 7. Pilot qualification rollover - one regenerated qualification, a NEW hash, no fit

Under v16 the existing `qualified_refit_job1.json` (`3c605514`) names a v15 generation and is refused, as at the v13 and v15
cutovers.

1. `ssh -o ControlPath=none lengau bash -s < chpc/migration_v16/rollover_pilot_v16.sh`. It refuses unless v16 is the deployed,
   adopted controller in `rsc_screen_ctl`, no controller command runs, the archive from step 2 verifies and holds byte-identical
   copies of the active `review_refit.json` and of `qualified_refit_job1.json` (`3c605514`), and the review is bound to
   `3c605514`. It then moves the review to `gate_retired/review_refit.v15_qual3c605514_max100.json` (read-only). The
   `3c605514` authority (Codex RSC `66d1e99`) stays historical. Expected: `retired to …`.
2. Make ONE call:
   `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1`.
   It regenerates the qualification from the EXISTING pilot job 1 under v16 with a new hash, `<qsha>`, and copies it to the
   gate. Expected: `QUALIFIED: refit job 1 (<qsha16>) copied to the gate`. A `NOT QUALIFIED` stops the migration; do not repeat
   `--qualify` to fish for a pass.
3. Package the evidence as `chpc/qualification_v16_<qsha8>/` with its `SHA256SUMS` (the `qualification_v15_3c605514/` pattern:
   the qualification, the bound receipts and verify document, the retained PBS copies, both archives' SHA256SUMS), commit it with
   explicit paths and route the qualification metadata to Codex for
   `ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100`. Never reuse the `3c605514` literal.
4. After Codex's committed record: `REC=reviews/<record>.md`, then
   `scp -o ControlPath=none $REC lengau:/mnt/lustre/users/pvanrooyen/t1_toolchain/patches/ctl16.$(basename $REC)` and
   `ssh -o ControlPath=none lengau "REC=$REC bash -s" < chpc/migration_v16/adopt_pilot16.sh` (the `adopt_pilot13.sh` pattern).
   It refuses while a review is active or while the gate still holds `3c605514`, commits the record in the controller clone and
   runs `--adopt-review $REC --max-job-number 100`, which creates the NEW `gate/review_refit.json` and never overwrites one.
   Expected: `adopted: reviews/<record>.md (…) for refit, qualification <qsha16>, job numbers up to 100`.

Later inventory changes need fresh current receipts (step 6), not another `--qualify`.

## 8. ONE first new-order Lengau job, alone

1. Fresh receipt (step 6), at most 2,700 s old.
2. Run (Lengau):
   `ssh -o ControlPath=none lengau 'cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access && /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --jobs 1 --dry-run'`.
   Expected:
   - `designated S x 0..79 (a96eb598…)`;
   - Lengau plannable about 897 less what has settled since;
   - EC2-designated unclaimed about 3,274;
   - the RESCUE-PENDING lines;
   - job <n>: 24 slots at rep 3's lowest free indices, then rep 4's (replicate-complete), envelope serial 24 x 48 h (1,152 core-h);
   - `the gate would admit`.
3. Run the same command without `--dry-run`. The plan records `order: designated-replicate-complete-1`. Every later call
   refuses ("scale-up is held") until step 9.

All other jobs keep running.

## 9. Review before scale-up

When the new-order job is terminal and settled, collect a fresh receipt. Route the following for the packing/resource review
(design s.4: "the mixed-replicate pilot does not establish peak behavior when workers concentrate on one replicate"):

- its statuses, records and timings;
- scheduler and worker memory;
- any slot disposition;
- the receipt hash.

After a FAVOURABLE committed record that carries `ADOPT row19-screen-v16-scaleup first_job=<n> job_id=<pbs id> plan=<sha256>`,
copy the record to `$T/patches/` and commit it in the controller clone as `adopt_pilot16.sh` does (the adopter requires it git-tracked and unmodified there), then run (Lengau, in the controller clone):

    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-scaleup reviews/<record>.md

This writes `gate/scaleup_refit_v16.json`, which is never overwritten. Refills may then resume through the refill scripts
with a fresh receipt each time, inside 81,000, the scheduler's serial max_run 10 and max_job 100.

If the review is not favourable, stop and return to the owner with a revised packing or design. Do not consume the rescue
allowance on ordinary retries.

## Operator sequence (summary)

drain -> `preflight_v16.sh` -> `archive_v15.sh` -> `promote_v16.py` (+ Mac commit) -> `deploy_v16.sh` -> `--raise-cap 81000`
(+ budget commits) -> fresh refit and bank receipts -> `rollover_pilot_v16.sh` -> ONE `--qualify 1` -> Codex
`ADOPT row19-screen-pilot` literal -> `adopt_pilot16.sh` -> ONE `--jobs 1` -> settled -> Codex `ADOPT row19-screen-v16-scaleup`
literal -> `--adopt-scaleup` -> refills.

## Known consequences of v16 (not migration steps)

- `row19_screen_release.py` pins the v15 admission and controls in `CONSUMER_FILES`; after promotion it refuses until the
  separately reviewed p80 release package re-pins the v16 bytes (review section B: CHANGE 4).
- `row19_ec2_shadow.decl_problem` hard-codes the 60,000 sub-envelope, so a future S retry refuses under v16; S is terminal and a
  retry needs its own reviewed repair.

## Abort and recovery

Before step 4 a failed step leaves Lengau on v15. Refit refills stay held regardless, under the owner's 17 Oct hold. A
promotion committed on the Mac but not deployed leaves Lengau on v15; do not run the Mac status commands until step 6. After
step 4, admissions need v16 receipts and the step-7 qualification. A raise interrupted in step 5 resumes or retires through
the CLI. Report every refusal verbatim. The rescue route (`--rescue`) stays disabled throughout; enabling it is a separate
reviewed amendment that chooses and qualifies its resources.
