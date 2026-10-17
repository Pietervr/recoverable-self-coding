# v15 -> v16 migration (the resized row-19 screen controller) - RUNBOOK, SCRIPTS REPAIRED (Codex R1-R4), NOT EXECUTED

Codex record `reviews/2026-10-17_v16_p80_codex_review.md` (RSC `f6896e1`, SHA-256 `a315d7d2…`), section A: FAVOURABLE for the
exact controls `candidate_v16/row19_screen_controls.json` with the literal

    ADOPT row19-screen-controls sha256=01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220 version=16

(candidate RSC `3686a11`, design `candidate_v16/DESIGN_v16.md`). The literal covers the controls and the pinned controller
implementation only. Codex: "Before operations, finish and review the actual preflight/archive/promote/deploy scripts, archive the
real adopted state, refresh whole-role v16 receipts, regenerate the existing pilot qualification without a fit, obtain its new
pilot literal, and admit the intended first job alone."

The step scripts are in this folder: `preflight_v16.sh`, `archive_v15.sh`, `promote_v16.py`, `deploy_v16.sh`,
`rollover_pilot_v16.sh`, `adopt_pilot16.sh`, with their shared parts `lengau.sh` (the one Mac -> Lengau transport),
`remote_lib.sh` (the Lengau prelude: fixed toolchain root, containment, drain, lock, git and science-digest checks),
`lengau_archive.py` (the Lengau archive inventory, build and certificate) and `mac_archive.py` (the Mac archive's). They follow
`migration_v13/` (preflight, archive, rollover and adopt) and `migration_v15/` (promote, deploy). Codex's review of RSC
`1d3c873` (`reviews/2026-10-17_migration_v16_codex_review.md`: CHANGE 4) required four repairs, made on 17 October 2026:

- **R1** each archive has a fixed mandatory inventory, is staged, verified in full (every digest and the exact inventory) and
  published by one atomic rename with a `COMPLETE` certificate; the same certificate is re-verified on reuse, immediately
  before the controller mutation (step 4) and before the review retirement (step 7.1); `promote_v16.py` requires the six Mac
  files by name;
- **R2** every drain observation is checked: a failed or empty process inventory, a lock that cannot be probed (`flock(1)` or a
  python `fcntl.flock(LOCK_SH|LOCK_NB)` on the same lock files) and a failed `git status` refuse; nothing is read as drained;
- **R3** the job clone's fixed science inventory (eight files) must exist, read and hash completely before the controller
  change, and the complete after-manifest must equal it, or the deploy refuses;
- **R4** the production scripts carry no test hook: the toolchain root (`remote_lib.sh`, `# @root`) and the transport
  (`lengau.sh`, `# @transport`) are fixed, and every Lengau path any body reads as authority or writes must resolve beneath the
  physical toolchain root (no symlink or alias escape). Tests run PRIVATE COPIES (see "Tests" below);
- **P3** the completed-promotion fast path runs the full authority and archive validation; `--check` is that validation as a
  no-write gate.

The repaired scripts need Codex's re-review before execution (step 0). **None of them has been run against the live tree or
Lengau.** Nothing in this file has been run.

Where commands run:

- On the Mac, every command runs from `workspace_demo/t1_access` unless marked Lengau.
- On Lengau, `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`, and controller commands run from the controller clone
  `$T/rsc_screen_ctl/workspace_demo/t1_access` through `$T/t1py`, via `ssh -o ControlPath=none lengau ...`.
- Every Lengau part goes through `lengau.sh`, which sends ONE script (`remote_lib.sh` + `lengau_archive.py` + any payload
  files + the body) over `ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s`. The Lengau-only bodies
  run as `bash chpc/migration_v16/lengau.sh rollover_pilot_v16.sh` and
  `bash chpc/migration_v16/lengau.sh adopt_pilot16.sh --file reviews/<record>.md`; run alone they refuse.
- Every step refuses rather than overwrites. Every script is safe to re-run: a completed step reports itself, an interrupted one
  resumes or refuses. Partial evidence (a staging directory, a dirty controller clone) is never overwritten or removed: report
  it and recover it explicitly.
- A successful drain probe proves one instant only. The operator's coordinated admission hold (refill scripts and slot watcher
  stopped, no Mac status or controller command) stays in force from step 1 to step 8; no worker or reaper is ever stopped to
  obtain it.

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
| Scripts reviewed | a committed FAVOURABLE Codex record on THIS folder's repaired scripts (review section A: "finish and review the actual preflight/archive/promote/deploy scripts"; the 17 Oct review of `1d3c873` was CHANGE 4, repaired R1-R4 + P3) and `python3 chpc/migration_v16/test_migration_v16.py` passing on the reviewed bytes | no record, or the scripts changed after it |
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
   - Lengau: every path the migration touches resolves beneath the physical toolchain root; a SUCCESSFUL, non-empty
     `ps -u pvanrooyen` shows no `row19_screen_admit|status|verify`, `row22_bank_submit|status`, `row19_ec2_*` or
     `row19_partition` process (a failed or empty inventory refuses); both `$T/programme_admission.lock` and
     `$T/row19_screen/plans/.submit.lock` exist and a non-blocking SHARED probe succeeds on each (`flock(1)`, else python
     `fcntl.flock(LOCK_SH|LOCK_NB)`; held, missing or unprobeable refuses); `rsc_screen_ctl` is clean (a failed `git status`
     refuses) at the v15 bytes with no declaration; the gate holds `qualified_refit_job1.json` `3c605514` and an active
     `review_refit.json`, and no `scaleup_refit_v16.json`; no budget phase is pending and the ledger cap equals the committed
     60,000 phase; `$T/row19_screen/ec2/activation_e1.json` exists; neither `archive_screen/v15_before_v16`, an archive staging
     directory nor the retired v15 review exists; every archive source exists with its v15 identity (`lengau_archive.py
     inventory`). It prints the job clone's COMPLETE science digest list (eight files; any missing, unreadable or failed digest
     refuses).
   - Mac additionally: `chpc/row19_screen_budget.json` is committed; no Mac archive staging directory exists; the Mac process
     inventory succeeded.

   Expected: `PREFLIGHT OK`. `--local-only` runs the Mac half alone (no ssh); it does not replace the full run.
3. Do not run the Mac's status or receipt commands during steps 2-5. A slot that frees stays empty until step 8.

## 2. Archive the adopted v15 state (Lengau, then Mac)

`bash chpc/migration_v16/archive_v15.sh --dry-run` (Mac checks and the plan, no ssh), then `bash chpc/migration_v16/archive_v15.sh`.

a. Lengau (over ssh, `lengau_archive.py`): `$T/archive_screen/v15_before_v16/`, every file read-only, with this mandatory
inventory and nothing else:

- `ctl/HEAD.txt`: the controller clone's HEAD;
- `ctl/<repo path>` for every file the adopted v15 entry pins (14), plus the v15 controls (`828d3b69`), adoption (`970c29f5`),
  budget phases `chpc/row19_screen_budget.json`, the screen manifest and `chpc/row22_bank_status.py` / `row22_bank_submit.py`;
- `gate/...`: the whole gate (`qualified_refit_job1.json` `3c605514`, the active `review_refit.json`, every watch and verify
  receipt, every retained PBS out/err copy), regular files only, with `INVENTORY.gate` captured from the source;
- `jobs/row19_screen_refit_*` (at least one), with `INVENTORY.jobs`;
- `ledger/row19_screen_campaign_budget.json` (a reference copy);
- `SHA256SUMS` (every file but itself and `COMPLETE`), then `COMPLETE` (schema, the `SHA256SUMS` digest, the HEAD, the
  qualification and the review digest).

Every source must exist as a regular file and carry its identity before anything is staged; the build stages in
`.v15_before_v16.staging.<pid>`, verifies the whole certificate there, then renames it into place. It refuses unless the drain is
observed (step 1 checks), the controller clone is clean at the v15 controls and adoption, the gate qualification is `3c605514`
and a review is active.

b. Mac (`mac_archive.py`): `chpc/results/archive/row19_screen_v15_before_v16/` holding EXACTLY `row19_screen_controls.json`
(`828d3b69`), `row19_screen_controls_adoption.json` (`970c29f5`), `row19_screen_admit.py` (`ac06e803`),
`row19_screen_status.py` (`0effcba3`), `row19_screen_budget.json` (committed bytes) and `qualified_refit_job1.json`
(`3c605514`), plus `SHA256SUMS` and `COMPLETE`, which also records the digest of the Lengau `SHA256SUMS` it was made with.
Built the same staged way. `promote_v16.py` and `deploy_v16.sh` require it by name.

Expected output: `archive built …` (file count, `SHA256SUMS` and HEAD), `sha256sums=<64 hex>`, `Mac archive … verifies: 6
files …`, `ARCHIVE OK`. A re-run accepts an existing archive only if its complete certificate verifies (and the Mac archive
names that Lengau archive); a malformed, partial, extra, substituted or uncertified archive, or a leftover staging directory,
refuses and is left exactly as it is. If the Lengau half fails, the Mac half is not written.

## 3. Promote v16 on the Mac

Run `python3 chpc/migration_v16/promote_v16.py --dry-run`, then run it again without `--dry-run`. It refuses unless, in order:

- the candidate controls are the reviewed v16 SHA-256 `01976b6a`, and versions 1-15 are byte-identical to the adopted file;
- the latest entry is version 16, pinning partition e1 `8d1de408`;
- the review record is `a315d7d2`, git-tracked, unmodified, with the literal in HEAD; the candidate files are committed;
- every v16 pin equals its file, taking admit, status and `row19_screen_designated.json` from `candidate_v16/`;
- every other pin equals v15's, and the file set is v15's plus the declaration;
- the Mac archive from step 2 holds exactly its six named files plus `SHA256SUMS` and `COMPLETE`, every digest verifying, and
  the candidate's versions 1-15 equal the ARCHIVED v15 controls;
- each of the four live paths is its v15 or its v16 bytes, and the adoption is the v15 record or EXACTLY the version-16 record
  this script writes.

It then copies the declaration, admission, status and LAST the controls into `chpc/` and writes
`chpc/row19_screen_controls_adoption.json` for version 16 (atomic writes). A re-run of a finished promotion runs every check above first and then prints `already
promoted, verified …`; an interrupted one resumes. `python3 chpc/migration_v16/promote_v16.py --check` is the same validation
with no write: exit 0 only for a complete, verified promotion. Commit atomically (one command; the archive path includes its
`COMPLETE`):

    git -C ~/Recoverable-Self-Coding add workspace_demo/t1_access/chpc/row19_screen_controls.json workspace_demo/t1_access/chpc/row19_screen_controls_adoption.json workspace_demo/t1_access/chpc/row19_screen_admit.py workspace_demo/t1_access/chpc/row19_screen_status.py workspace_demo/t1_access/chpc/row19_screen_designated.json workspace_demo/t1_access/chpc/results/archive/row19_screen_v15_before_v16 && git -C ~/Recoverable-Self-Coding commit -F <msg> -- <the same six paths>

## 4. Deploy to the controller clone (Lengau)

Run `bash chpc/migration_v16/deploy_v16.sh --dry-run`, then run it without `--dry-run`.

On the Mac it refuses unless `promote_v16.py --check` passes (full authority, the Mac archive certificate, the exact version-16
adoption), the six changed files are committed, and the Mac tree's own authority/lineage/controls/designated checks are
empty. The six files (promoted controls, adoption, admit, status, the declaration and the review record) travel inside the one
Lengau script, each checked against its Mac SHA-256; nothing is staged in `patches/`.

On Lengau, immediately before the controller change, it refuses unless: the drain is observed (checked process inventory,
both locks probed free); the archive's complete certificate verifies and its `SHA256SUMS` is the one the Mac archive names;
`rsc_screen_ctl` is clean, at the v15 bytes, with no declaration, and at the archived HEAD; the gate qualification and active
review equal the archived ones; and a COMPLETE before-manifest of the job clone's eight science files is taken (every file
read, every digest command checked). It then makes one commit in `rsc_screen_ctl`, takes the complete after-manifest and
refuses completion unless it is identical. The job clone `rsc_screen` is never written. A re-run on a clone that already holds
exactly these bytes makes no commit and repeats the archive check and the checks below. An interrupted copy or commit leaves a
dirty clone, which every re-run refuses: report it and recover it explicitly before continuing.

Expected output:

- `science bytes UNCHANGED (8 files, complete before and after manifests identical)`;
- `authority '' lineage '' controls ''`;
- `designated ''` (the `A.designated(m, "chpc/row19_screen_manifest.json")[1]` check, run as `$T/t1py` in the controller clone);
- the local-vs-remote pin comparison `IDENTICAL` (19 files);
- `DEPLOY OK`.

The script refuses (exit 3) on any non-empty problem string, a diff, an ABORT line or an incomplete remote run. The e1
activation proof stays valid because v16 pins the same partition. Do NOT re-activate.

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

1. `bash chpc/migration_v16/lengau.sh rollover_pilot_v16.sh`. It refuses unless v16 is the deployed, adopted controller in
   `rsc_screen_ctl`, the drain is observed (checked process inventory, both locks probed free), the archive from step 2
   verifies with its complete certificate and certifies byte-identical copies of the active `review_refit.json` and of
   `qualified_refit_job1.json` (`3c605514`), and the review is bound to `3c605514`. A re-run after the retirement refuses
   (`retired file exists`), which is the completed state. It then moves the review to `gate_retired/review_refit.v15_qual3c605514_max100.json` (read-only). The
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
4. After Codex's committed record: `bash chpc/migration_v16/lengau.sh adopt_pilot16.sh --file reviews/<record>.md` (the
   `adopt_pilot13.sh` pattern; the record travels inside the script, checked against its Mac SHA-256). It refuses while a
   review is active, while the gate still holds `3c605514`, without an observed drain, or when the controller clone holds the
   record with other or uncommitted bytes; it commits the record in the controller clone and runs
   `--adopt-review <record> --max-job-number 100`, which creates the NEW `gate/review_refit.json` and never overwrites one; an
   adopter refusal is reported as a refusal.
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
copy the record to `$T/patches/` and commit it in the controller clone with its explicit path, as `adopt_pilot16.sh` does (the adopter requires it git-tracked and unmodified there), then run (Lengau, in the controller clone):

    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-scaleup reviews/<record>.md

This writes `gate/scaleup_refit_v16.json`, which is never overwritten. Refills may then resume through the refill scripts
with a fresh receipt each time, inside 81,000, the scheduler's serial max_run 10 and max_job 100.

If the review is not favourable, stop and return to the owner with a revised packing or design. Do not consume the rescue
allowance on ordinary retries.

## Operator sequence (summary)

drain (held to step 8) -> `preflight_v16.sh` -> `archive_v15.sh` -> `promote_v16.py` (+ Mac commit) -> `deploy_v16.sh` ->
`--raise-cap 81000` (+ budget commits) -> fresh refit and bank receipts -> `lengau.sh rollover_pilot_v16.sh` -> ONE
`--qualify 1` -> Codex `ADOPT row19-screen-pilot` literal -> `lengau.sh adopt_pilot16.sh --file <record>` -> ONE `--jobs 1` ->
settled -> Codex `ADOPT row19-screen-v16-scaleup` literal -> `--adopt-scaleup` -> refills.

## Tests (private copies only)

`python3 chpc/migration_v16/test_migration_v16.py` (from anywhere; `-k <substring>` selects, `--keep` keeps the temp world).
It builds a throwaway world in a fresh private temp directory: a local git clone as the Mac tree, a fake Lengau root (two more
clones as controller and job clones, gate, locks, ledger, job scripts) and fake `ps` / `sha256sum` / `flock`. It copies the
production files into the clone and substitutes exactly the `# @root` and `# @transport` lines, refusing a root outside its
temp directory or aliasing the production toolchain and checking that no other line differs. No ssh, no Lengau, no live-tree
write. It covers the positive route (preflight, archive, promote, deploy, re-runs, rollover) and the negative paths Codex
listed: one-file remote archive (archive and deploy), missing ledger / budget phases / controller file / review / job scripts,
failed checksum command and unreadable source, interrupted build, self-consistent subset and fully regenerated archives,
archive corruption between creation and deploy (byte flip, extra file, missing `COMPLETE`, writable file), substituted Mac
sixth file, incomplete Mac archive, the P3 fast path; failed, empty and busy process inventories, unavailable lock probes,
actually held locks (both files, both probes), a failed `git status`; missing, unreadable, digest-failed, partial and changed
science inputs (before and after the commit); symlink escapes of the controller clone, gate, archive directory, a gate member
and an adopt destination, a valid aliased fake root, and bodies run without the prelude.

Untested on the Mac: real ssh transport and Lengau's GNU tools (`flock(1)` exit codes, `realpath`, `base64 -d`, `sha256sum`)
and Lustre's flock(2) behaviour; a positive `--adopt-review`, `--qualify`, `--raise-cap` and `--adopt-scaleup`; the real
controller-clone commit on Lengau.

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
