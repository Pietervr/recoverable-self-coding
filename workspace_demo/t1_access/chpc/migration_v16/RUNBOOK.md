# v15 -> v16 migration (the resized row-19 screen controller) - RUNBOOK, DRAFT, NOT EXECUTED

This runbook is a draft written on 17 October 2026 for Codex's review of `chpc/candidate_v16/` (see `candidate_v16/DESIGN_v16.md`).
It follows the pattern of `chpc/migration_v13/RUNBOOK.md` and the v15 cutover (`migration_v15/promote_v15.py`, `deploy_v15.sh`).
The step scripts named below (`preflight_v16.sh`, `archive_v15.sh`, `promote_v16.py`, `deploy_v16.sh`) are **not written yet**.
They are written on the v15 pattern once Codex has committed a FAVOURABLE record with the literal
`ADOPT row19-screen-controls sha256=<the v16 controls SHA-256> version=16`. Nothing in this file has been run.

Where commands run:

- On the Mac, every command runs from `workspace_demo/t1_access` unless marked Lengau.
- On Lengau, `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`, and controller commands run from the controller clone
  `$T/rsc_screen_ctl/workspace_demo/t1_access` through `$T/t1py`, via `ssh -o ControlPath=none lengau ...`.
- Every step refuses rather than overwrites.

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
| Review | Codex's committed record carries `ADOPT row19-screen-controls sha256=<v16> version=16` for the exact `candidate_v16/row19_screen_controls.json` bytes | no literal, or other bytes |
| Old-plan hold | no refit admission since 17 Oct (owner); the refill scripts are not invoked; `slot_watch.sh` is stopped | any admission under v15 after 17 Oct |
| Running jobs | jobs 37-45 (and whatever is live) keep running; their settlements go through `programme_gate.py run ... settle` as usual | - |
| Prior packages | none is required for refit admission; the prefix release (s.6 item 3) and the EC2 epoch (item 5) are separate and may follow | - |

## 1. Drain controller commands (Lengau login and Mac)

1. Do not invoke `refill_r1.sh` or `refill_b1.sh`. End the slot-watch task, which only reads `qstat`.
2. Let any controller command already running finish. `preflight_v16.sh` (v13 `preflight.sh` pattern) must then find no
   `row19_screen_admit|status|verify`, `row22_bank_submit|status`, `row19_ec2_*` or `row19_partition` process on the login node.
3. Do not run the Mac's status or receipt commands during steps 2-6. A slot that frees stays empty until step 8.

## 2. Archive the adopted v15 state (Lengau)

`archive_v15.sh` creates `$T/archive_screen/v15_before_v16/{gate,ctl}` with `SHA256SUMS`, all read-only. It copies:

- the whole gate: `qualified_refit_job1.json`, `review_refit.json`, every watch and verify receipt, every retained PBS
  out/err copy;
- the v15 controller files and the controller clone HEAD;
- the campaign ledger `row19_screen_campaign/budget.json` and the budget phases `chpc/row19_screen_budget.json`, as a
  reference copy only.

Expected output: the archive path, its file count and the SHA256SUMS hash. Abort if the archive exists, or if the controls
are not `828d3b69`.

## 3. Promote v16 on the Mac

Run `python3 chpc/migration_v16/promote_v16.py --dry-run`, then run it again without `--dry-run`. It checks, in order:

- the candidate controls are the reviewed v16 SHA-256, and versions 1-15 are byte-identical to the adopted file;
- the latest entry is version 16, pinning partition e1 `8d1de408`;
- every v16 pin equals its file, taking admit, status and `row19_screen_designated.json` from `candidate_v16/`;
- every other pin equals v15's;
- the review record holds the literal.

It then archives the Mac v15 files and the Mac copy of `qualified_refit_job1.json` to
`chpc/results/archive/row19_screen_v15_before_v16/` (read-only). It copies the candidate controls, admit, status and
declaration into `chpc/` and writes `chpc/row19_screen_controls_adoption.json` for version 16. Commit atomically:
`git -C <RSC> add <the 4 chpc files + adoption + archive dir> && git -C <RSC> commit -F <msg> -- <same paths>`.

## 4. Deploy to the controller clone (Lengau)

Run `bash chpc/migration_v16/deploy_v16.sh --dry-run`, then run it without `--dry-run`. It makes one commit in
`rsc_screen_ctl` with the promoted controls, adoption, admit, status, the declaration and the review record. The job clone
`rsc_screen` is not touched.

Expected output:

- `science bytes UNCHANGED`;
- `authority '' lineage '' controls ''`;
- the local-vs-remote pin comparison `IDENTICAL`;
- this designated check, run as `$T/t1py` in the controller clone, printing an empty string:
  `python3 -c 'import sys; sys.path.insert(0,"chpc"); import json, row19_screen_admit as A; m=json.load(open("chpc/row19_screen_manifest.json")); print(repr(A.designated(m, "chpc/row19_screen_manifest.json")[1]))'`.

The e1 activation proof stays valid because v16 pins the same partition. Do NOT re-activate.

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
The command runs `cap_problem` (60,000 committed) first. It then writes the pending phase, raises the ledger
(`CampaignLedger.raise_cap`, which records old 60,000, new 81,000, the note and the time in `cap_history`), certifies cap and
history, and commits the phase.

If it is interrupted, repeat the same command to resume, or run `--retire-pending --note ...`. Never edit the ledger. Commit
the changed `chpc/row19_screen_budget.json` in the controller clone, copy it to the Mac and commit it there with explicit paths.
The sub-envelope in controls v16 is already 81,000, so from here the binding limits are the ledger's 81,000, the refit+S
81,000 and the programme's 100,000.

## 6. Fresh whole-role v16 evidence (Mac)

Run `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt`, then the
bank receipt as before.

Expected:

- fresh, production, zero alarms;
- the verifier stamps generation 16;
- the printout carries the `DESIGNATED S x 0..79` line;
- RESCUE-PENDING lists 43/4 and 83/2, with `attempt_running` while job 37 is live;
- the receipt carries `designated`.

Any `designated set:` alarm stops the migration.

## 7. Pilot qualification rollover - one regenerated qualification, a NEW hash, no fit

Under v16 the existing `qualified_refit_job1.json` names a v15 generation and is refused, as at the v13 and v15 cutovers.

1. Retire the active `review_refit.json` to `gate_retired/` (v13 `rollover_pilot.sh` pattern; the archive in step 2 holds
   byte-identical copies).
2. Make ONE call:
   `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1`.
   It regenerates the qualification from the EXISTING pilot job 1 under v16 with a new hash, `<qsha>`.
3. Route the qualification metadata to Codex for `ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100`.
4. After Codex's committed record, run `--adopt-review` (the `adopt_pilot13.sh` pattern).

## 8. ONE first new-order Lengau job, alone

1. Fresh receipt (step 6), at most 2,700 s old.
2. Run `t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --jobs 1 --dry-run`.
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
run:

    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-scaleup reviews/<record>.md

This writes `gate/scaleup_refit_v16.json`, which is never overwritten. Refills may then resume through the refill scripts
with a fresh receipt each time, inside 81,000, the scheduler's serial max_run 10 and max_job 100.

If the review is not favourable, stop and return to the owner with a revised packing or design. Do not consume the rescue
allowance on ordinary retries.

## Abort and recovery

Before step 4 a failed step leaves Lengau on v15. Refit refills stay held regardless, under the owner's 17 Oct hold. After
step 4, admissions need v16 receipts and the step-7 qualification. A raise interrupted in step 5 resumes or retires through
the CLI. Report every refusal verbatim. The rescue route (`--rescue`) stays disabled throughout; enabling it is a separate
reviewed amendment that chooses and qualifies its resources.
