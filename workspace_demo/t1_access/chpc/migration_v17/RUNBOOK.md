# v16 -> v17 migration (controls v17: the EC2 provider epoch-2 adoption) - RUNBOOK and SCRIPTS, BUILT AND TESTED, NOT EXECUTED

Written 19 October 2026 (R052, Claude, bounded job). Nothing in this folder has been run against the live tree, Lengau or AWS.
The scripts need their own FAVOURABLE Codex scripts review before step 1 (Codex e2 adoption review, "Which missing work must
precede which action": "Before live migration: build and separately review `migration_v17` preflight, full v16 archives,
promotion/deployment, proof/retry paths, retirement/rollover/adoption and tests").

## What is authorised and what is not

Codex re-review `reviews/2026-10-19_e2_repair_codex_rereview.md` (RSC `1c948d8`, SHA-256 `48b9cf05…`) is FAVOURABLE for the exact
repaired candidate package at RSC `c26835f` + `806c44c`, with the literal

    ADOPT row19-screen-controls sha256=9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0 version=17

It covers the controls and the pinned controller implementation only. The review adds: "The controls literal alone does **not**
cryptographically bind the Mac-only authority files or promotion-map digest ... Preserve this exact reviewed package through
migration and verify the Mac/map/builder/promoter identities as well as the controls." Every step here therefore checks the
package identities (`v17_package.py` `PACKAGE`: candidate controls `9ea4e727`, map `6bc8bd39`, builder `f2a80f42`, promoter
`f0c320c2`, admission `c3960464`, record `48b9cf05`), and `promote_v17.py --check` checks every one of the 20 map rows' sources.

Not authorised by anything here: E2Q1 or any EC2 qualification instance, production, a release, the p80 release consumers,
rescue, a pilot fit, or any scale-up beyond the existing `scaleup_refit_v16.json`.

**AWS spend (wording fixed per the Codex re-review, "Staging, wording and remaining sequence").** The design text "no AWS spend
before the epoch-2 release" means **no AWS PRODUCTION spend** before the epoch-2 release (schema-3 RELEASE certificate, a
favourable exact-result review, `release-adopt`) and a fresh budget check. The separately permitted epoch-2 qualification
instance E2Q1 (its own prospective permission record, the USD 300 allowance, the reviewed bundle staging procedure) PRECEDES that
release; it is not part of this migration. This migration itself makes no AWS call: `prod_authority.py inventory` and
`ec2_sync.py cycle` seal the authority inventory from the Mac's run ledgers and move it to the root over ssh.

## The package and the scripts

The step scripts are in this folder; each follows its `migration_v16/` counterpart and keeps every rule Codex's migration_v16
reviews established (`reviews/2026-10-17_migration_v16_codex_review.md` R1-R4, `..._rereview.md` P2 containment and P2 deploy
retry, `2026-10-17_mig2_e2n_codex_review.md`, `mig_compat`, `mig_allowlist`):

| Step | Script | Where | Writes |
|---|---|---|---|
| 1 | `preflight_v17.sh` (Mac half: `v17_package.py preflight`) | Mac + Lengau | nothing |
| 2 | `archive_v16.sh` (`lengau_archive.py`, `mac_archive.py`) | Lengau, then Mac | the two archives, the Mac copy of the Lengau `SHA256SUMS` |
| 3 | `chpc/candidate_v17/promote_v17.py` (reviewed, unchanged) | Mac | the 20 promoted paths, the v17 adoption record |
| 4 | `deploy_v17.sh` | Mac -> Lengau | one controller-clone commit (17 files), the deploy proof |
| 5 | `ec2_cycle_v17.sh pre-activation` (+ `check_v17.sh`) | Mac (+ Lengau read-only) | a new authority generation on the root |
| 6 | `lengau.sh activate_e2.sh` | Lengau | `row19_screen/ec2/activation_e2.json` (by the reviewed command) |
| 7 | `ec2_cycle_v17.sh post-activation` (+ `receipt_check_v17.py`) | Mac (+ Lengau read-only) | a new generation, the refit and bank receipts |
| 8.1 | `lengau.sh rollover_pilot_v17.sh` | Lengau | moves the v16 review to `gate_retired/` |
| 8.3 | `package_qual_v17.py` | Mac | `chpc/qualification_v17_<qsha8>/` |
| 8.4 | `lengau.sh adopt_pilot17.sh --file reviews/<record>.md` | Lengau | the record commit in the controller clone, the new gate review (by the adopter) |

Shared parts: `lengau.sh` (the one Mac -> Lengau transport, `# @transport`), `remote_lib.sh` (the Lengau prelude: the fixed
toolchain root `# @root`, containment, drain, lock, git, evidence allowlist, science digest, the v17/deploy/activation checks),
`lengau_archive.py` (the Lengau archive inventory, build and certificate), `mac_archive.py` (the Mac archive's),
`v17_package.py` (the package identities and the Mac-side gates). Tests: `test_migration_v17.py`; results: `test_results.txt`.

Where commands run:

- On the Mac, every command runs from `workspace_demo/t1_access`.
- On Lengau, `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`; controller commands run from the controller clone
  `$T/rsc_screen_ctl/workspace_demo/t1_access` through `$T/t1py`. Every Lengau part goes through `lengau.sh`, which sends ONE
  script (`remote_lib.sh` + `lengau_archive.py` + any payload files + the body) over
  `ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s`. The Lengau-only bodies run as
  `bash chpc/migration_v17/lengau.sh activate_e2.sh`, `... rollover_pilot_v17.sh`, `... adopt_pilot17.sh --file reviews/<record>.md`;
  run alone they refuse.
- Every step refuses rather than overwrites and is safe to re-run: a completed step reports itself, an interrupted one resumes
  or refuses. Partial evidence (a staging directory, a dirty controller clone, a kept proof) is never overwritten or removed:
  report it and recover it explicitly.

**Never:**

- stop, restart or edit any running refit, bank or EC2 worker or reaper, or the job clone `rsc_screen` and its numerical tree;
- set any permission, qualification, activation or inventory by hand; edit a ledger, budget file, proof, claim or plan;
- change reviewed bytes (`chpc/candidate_v17/*`, `chpc/candidate_e2/*`, `chpc/candidate_e2q/*`, `chpc/e2_final/*`) after review;
- delete or relabel the e1 partition, its activation proof or any older archive (e1 stays as provenance);
- rerun a pilot fit, repeat `--qualify` to fish for a pass, or reuse an old ADOPT or pilot literal;
- revert the controls: undoing epoch 2 is a new reviewed epoch (DESIGN_v17 s.3 item 3), never a rollback.

## The coordinated hold, and the running refit jobs 47-56

**The hold.** From step 1 until the new pilot adoption (step 8.4) the operator keeps the coordinated hold: the refill scripts
are not invoked, the slot watcher is stopped, and no controller command is started by hand - no admission, status or receipt
command (other than the ones these steps run), no `row19_partition`/`row19_ec2_*` command, no settlement, no EC2 authority
command. A successful drain probe proves one instant only; every Lengau step re-probes (process inventory - which now also
matches `programme_gate` and `row19_ledger`, so a settlement in flight refuses - and both lock files) immediately before it
writes. No worker or reaper is ever stopped to obtain it.

**Running jobs keep running, untouched.** Refit jobs 47-56 (PBS 7551252-7551261) were admitted under v16 and are queued or
running. A refit job runs entirely from the scientific clone `rsc_screen` (its PBS script `cd`s there): `row19_shard.py
job-start` checks only the manifest's code pins and the ledger reservation, the workers write records and timings to the root,
and `job-end` writes the runner's end into the campaign ledger. None of that reads the controller clone, the controls, the
partition or the gate, and the migration changes none of what it reads (the job clone is proved by its complete eight-file
science manifest before and after the controller commit). So a queued job starts and a running job finishes exactly as under
v16, whether its event falls before, during or after the switch.

**How their results are settled and honoured after v17 adoption.**

1. *Records.* A job's records are bound to the manifest code pins and the task identities, not to a controls version, and no
   plan binds a controls version. The step-7 v17 receipt (generation 17) observes and verifies every record of jobs 47-56
   exactly as the v16 receipts did for jobs 37-45 at the v16 cutover; nothing is re-planned or re-run.
2. *Settlement.* A finished job's ledger entry is settled through the unchanged route
   `programme_gate.py settle --manifest chpc/row19_screen_manifest.json -- $T/t1py chpc/row19_ledger.py ... settle ...` in the
   controller clone. `programme_gate` first requires `lineage_problem() == ''`: it passes under v16 before step 4 and under v17
   from DEPLOY OK on; during the controller commit window it would refuse (and the drain refuses a settlement in flight). So
   settlements are deferred from step 1 to DEPLOY OK (step 4) and may then be run at a step boundary - never concurrently with a
   step script. Until settled, a finished job's reservation stays counted as live in the programme funding (the conservative
   side). Settlement does not depend on the activation or the pilot gate.
3. *Coordinates.* Jobs 47-56 were planned by v16, which plans only Lengau's 13 replicates and its existing claims and never an
   unclaimed coordinate of the 47 EC2-designated replicates (DESIGN_e2 s.6 item 1). They therefore hold no claim on an
   epoch-2-owned coordinate. The canonical activation (step 6) proves it: under the plan lock it refuses on ANY Lengau claim on
   an owned coordinate. If it ever does refuse on one, nothing is erased: re-snapshot, re-declare, re-review (DESIGN_v17 s.6
   step 6). The status view keeps their claims as history either way.
4. *Dispositions* (a crashed slot, a closed-no-record job) that one of these jobs needs are made after step 7 with the unchanged
   v17 status code, which is byte-identical to v16's (`a9f9180b`).

From step 4 (deploy) until step 6 (activation) every NEW Lengau refit admission HOLDS ("partition epoch 2 is pinned but not
activated", `activation_problem_v10`); from step 6 until step 8.4 it also needs current v17 receipts and the new pilot
adoption. Running and queued jobs are unaffected by both.

## 0. Preconditions

| Gate | Check | Abort if |
|---|---|---|
| Controls | the committed record `reviews/2026-10-19_e2_repair_codex_rereview.md` (`48b9cf05`) carries the literal for the exact `chpc/candidate_v17/row19_screen_controls.json` bytes (`9ea4e727`) - `preflight_v17.sh` checks it in HEAD | no literal, other bytes |
| Package | builder `f2a80f42`, promoter `f0c320c2`, map `6bc8bd39`, admission `c3960464`, every map source (`promote_v17.py --check`) | any byte differs |
| Scripts reviewed | a committed FAVOURABLE Codex record on THIS folder at its exact commit, and `python3 chpc/migration_v17/test_migration_v17.py` passing on the reviewed bytes | no record, or the scripts changed after it |
| Final e2 data | Codex FAVOURABLE on `chpc/e2_final/` (adoption review A, `785aa8c`; retained by the re-review) | - |
| Hold | the coordinated hold above is in force; no refill since the operator started it | any admission during the hold |
| EC2 | no live EC2 attempt (qual-Q1/4 dispositioned and fenced: ack_g48, inventory g52) and no EC2 reaper on the Mac | a live attempt |
| Running jobs | jobs 47-56 and whatever else is live keep running (see above) | - |

## 1. Full live read-only preflight (Mac and Lengau)

1. Do not invoke `refill_r1.sh` or `refill_b1.sh`. End the slot-watch task. Let any controller command already running
   finish. Then run the FULL preflight `bash chpc/migration_v17/preflight_v17.sh` (no option: Mac AND Lengau).
   `--local-only` runs the Mac half alone, prints `PREFLIGHT (Mac only) OK - the Lengau checks were NOT run`, and does not
   satisfy this step (Codex migration_v16 re-review: "run the full read-only preflight first ... `--local-only` is
   insufficient"). It is the first no-write observation of Lengau's actual tools and filesystem; a refusal is reported verbatim,
   never bypassed, and no authority is created by hand to clear it.
2. It refuses unless:
   - **Mac** (`v17_package.py preflight`): the live controls and adoption are the adopted v16 bytes (`01976b6a`, `523fe18a`),
     committed; each of the 19 promoted paths holds its v16 bytes (the five chpc files v17 replaces, the four Mac aws_ec2 files)
     or is absent (the nine new paths and `make_e2_funding.py`), committed; the package identities above, committed, and
     `promote_v17.py --check` exits 0; the record carries the literal in HEAD; the e1 partition is `8d1de408`; the Mac
     `qualified_refit_job1.json` is the v16 `2c7a7ef1`; the budget phases are committed; no Mac archive or staging directory; a
     successful Mac process inventory shows no refill, slot-watch, controller, EC2-authority (`ec2_sync`, `prod_authority`,
     `prod_launch`, `qual_permit`) or EC2-reaper process; a shared non-blocking probe of `aws_ec2/runs/.authority.lock`
     succeeds.
   - **Lengau**: the tool versions are printed (`git --version`, `flock --version`, the system `python3`, `$T/t1py`; t1py must be
     >= 3.6); a successful, non-empty `ps -u pvanrooyen` shows no controller command; both `$T/programme_admission.lock` and
     `$T/row19_screen/plans/.submit.lock` exist and a shared non-blocking probe succeeds on each; every fixed root and every
     path a later step reads or writes is its own physical path in its scope, the controller and scientific roots disjoint; the
     controller clone is clean (`ctl_clean`: only the three pinned untracked evidence files) at the v16 bytes (controls,
     adoption, e1 and the five replaced files), with none of the nine v17 paths and `aws_ec2/prod/` absent or a real directory;
     the gate holds `qualified_refit_job1.json` `2c7a7ef1` and an active `review_refit.json` bound to it; the v16 retirement
     target, `activation_e2.json`, the archive `v16_before_v17`, an archive staging directory and `v17_deploy_proof` do not
     exist; `activation_e1.json` exists; no budget phase is pending and the ledger cap equals the committed 81,000 phase; every
     archive source exists with its v16 identity (`lengau_archive.py inventory`); the job clone's complete eight-file science
     digest list is printed. It reports whether `scaleup_refit_v16.json` is present (it is not generation-bound and stays valid
     under v17).
3. Expected: `mac preflight OK`, `lengau tools: ...`, `drain observed`, `paths resolved`, `archive sources complete`,
   `lengau preflight OK`, `PREFLIGHT OK`.

**The controller clone's pinned untracked evidence** (unchanged from v16; `remote_lib.sh` `CTL_EVIDENCE` = `lengau_archive.py`
`UNTRACKED_CTL`): `aws_ec2/ec2_release_state.json` `80ba0ac5…`, `aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json`
`154511e6…`, `reviews/2026-10-11_d1d2_f3_codex_record.md` `636f1e77…`. They are retained historical administrative evidence and
are not authority for this migration's path; the legacy, terminal S route (`chpc/row19_ec2_shadow.py`) declares and reads the
release-state copy, and S stays terminal with its retry held (Codex allowlist review P3). `ctl_clean` is the v16 rule with the
directory inventory now NUL-delimited and any entry whose name holds a newline refused (the allowlist review's other P3).

## 2. Archive the adopted v16 state (Lengau, then Mac)

`bash chpc/migration_v17/archive_v16.sh --dry-run` (Mac checks and the plan, no ssh), then `bash chpc/migration_v17/archive_v16.sh`.

a. **Lengau** `$T/archive_screen/v16_before_v17/` (`lengau_archive.py`), every file read-only, with this mandatory inventory and
nothing else: `ctl/HEAD.txt`; `ctl/<path>` for every file the adopted v16 entry pins, its partition e1 (`8d1de408`), the v16
controls, adoption, admission, status, designated declaration, budget phases, screen manifest and the two row-22 helpers;
`ctl/untracked/<path>` for the three evidence files with their pinned hashes; the WHOLE gate (`qualified_refit_job1.json`
`2c7a7ef1`, the active review, `scaleup_refit_v16.json` when present, every receipt and PBS copy) with `INVENTORY.gate`;
`jobs/row19_screen_refit_*` with `INVENTORY.jobs`; `ledger/row19_screen_campaign_budget.json`; `ec2/activation_e1.json`;
`SHA256SUMS`; `COMPLETE` (schema, the `SHA256SUMS` digest, the HEAD, the qualification, the review, the budget digest). It is
staged in `.v16_before_v17.staging.<pid>`, verified in full and published by one rename. The ledger is a point-in-time reference
copy read once (running jobs replace it atomically at job end, so it is not re-read after the copy); every other source must be
unchanged across the build.

b. **Mac** `chpc/results/archive/row19_screen_v16_before_v17/` (`mac_archive.py`) holding EXACTLY the 13 members of
`build_v17.ARCHIVE` (the v16 admission `1b02f336`, partition module `ed6aa177`, ingestion `b697dc36`, qualifier `1fc6b61f`,
state module `bda200dc`, prod_authority `b8ca02b8`, prod_launch `21b7cf57`, make_prod_manifest `8da79911`, qual_permit
`c503e795`, controls `01976b6a`, adoption `523fe18a`, qualification `2c7a7ef1`, the committed budget), plus `SHA256SUMS` and the
JSON `COMPLETE` (`schema` `row19-screen-mac-archive-v16-before-v17-1`, `sha256sums`, `budget`, `lengau_sha256sums`), which is
what the reviewed `build_v17.archive_problems` reads. The Mac budget phases must be the bytes the Lengau archive certifies. Only
after the Mac archive names this Lengau archive is the Lengau `SHA256SUMS` text kept beside it as
`chpc/results/archive/row19_screen_v16_before_v17.lengau_SHA256SUMS.txt` (its digest checked against both certificates).

Expected: `archive built ...`, `sha256sums=<64 hex>`, `budget=<64 hex>`, `Mac archive ... verifies: 13 members ...
build_v17.archive_problems: []`, `ARCHIVE OK`. A re-run accepts an existing archive only if its complete certificate verifies
(and the Mac archive names that Lengau archive); a partial, substituted, writable or uncertified archive, or a leftover staging
directory, refuses and is left exactly as it is. If the Lengau half fails the Mac half is not written; if the Mac half fails
after the Lengau archive was published, nothing is written on the Mac and a re-run (after the cause is fixed) verifies the
Lengau archive and builds the Mac half.

## 3. Promote v17 on the Mac (the reviewed `promote_v17.py`, unchanged)

    python3 chpc/candidate_v17/promote_v17.py --dry-run --review reviews/2026-10-19_e2_repair_codex_rereview.md
    python3 chpc/candidate_v17/promote_v17.py --review reviews/2026-10-19_e2_repair_codex_rereview.md

It resolves the authenticated v16 base first (the live exact v16, else only the verified archive), checks the candidate, the
review literal in HEAD and the archive, then copies the e2 partition and data, the Mac aws_ec2 code, the helpers, the admission
and LAST the controls, then writes the version-17 adoption record (atomic replaces; an interrupted promotion resumes; a complete
one reports `already promoted, verified`). Then commit atomically, the paths printed by
`python3 chpc/migration_v17/v17_package.py commit-paths` (the 19 map paths, the controls, the adoption record, the Mac archive
directory and the Lengau `SHA256SUMS` copy):

    git -C ~/Recoverable-Self-Coding add <those paths, each prefixed workspace_demo/t1_access/> && git -C ~/Recoverable-Self-Coding commit -F <msg> -- <the same paths>

Then `python3 chpc/candidate_v17/promote_v17.py --check-promoted --review reviews/2026-10-19_e2_repair_codex_rereview.md` must
exit 0, and `python3 chpc/migration_v17/v17_package.py check-promoted` must print `mac v17 promotion OK`.

`aws_ec2/prod/` becomes tracked for the four e2 files only (DESIGN_v17 choice 5); the untracked e1 Q1/Q2 operational manifests
there are left as they are. From here to step 7 do not run the Mac status, receipt or EC2 authority commands (the Mac is v17,
Lengau still v16).

## 4. Deploy to the controller clone (Lengau)

`bash chpc/migration_v17/deploy_v17.sh --dry-run`, then `bash chpc/migration_v17/deploy_v17.sh`.

On the Mac it refuses unless `v17_package.py check-promoted` passes (the package identities, the strict Mac archive certificate
and the builder's view of it, `promote_v17.py --check-promoted`, every promoted path, the adoption, the record and the archive
committed), the Mac drain holds, and the Mac tree's own `authority`, `lineage`, `controls`, `designated` checks are empty and
`A.partition` is schema 2, epoch 2, 3,274 owned.

The payload is the 17 files of DESIGN_v17 s.6 step 4, in this order: the review record; `chpc/row19_partition_e2.json`
(`48cea639`); the data at their mapped tracked paths - `chpc/claims_snapshot_e2.json` (`31cc268f`), `aws_ec2/e2_funding.json`,
`aws_ec2/prod/manifest_production_e2.json`, `aws_ec2/prod/manifest_e2q1_e2.json`, `aws_ec2/prod/manifest_e2q2_e2.json`,
`aws_ec2/prod/panel_e2q_e2.json` (`f04a5e43`); the six helpers; the admission; the controls; LAST the adoption record. The Mac-only
`aws_ec2/*.py` are not deployed (DESIGN_v17 choice 4). They travel inside the one Lengau script, each checked against its Mac
SHA-256.

On Lengau, immediately before the controller change, it refuses unless: the drain is observed; the archive's complete
certificate verifies and is the one the Mac archive names; the controller clone is clean, at the v16 bytes with none of the
nine new paths, at the archived HEAD; the gate qualification and active review equal the archived ones; `activation_e1.json`
exists and `activation_e2.json` does not; every Python payload compiles and every JSON payload parses under `$T/t1py` (nothing
is executed); a complete eight-file science before-manifest is taken. Every destination, its `.v17tmp` sibling and parent
(including the new `aws_ec2/prod/`), the controller and gate authority and the proof directory pass containment up front and
again immediately before each copy. Before the first controller write it writes the deploy proof
`$T/archive_screen/v17_deploy_proof/` (`science_before.sha256`, `intent`). It makes ONE commit of exactly the payload paths
(checked; the three evidence files stay untracked), takes the complete after-manifest and refuses completion unless it is
identical; only then is `DONE` written, with `science_after` = the proven-equal `science_before` digest (no unchecked digest
pipeline - the mig2 review's P3), and read back before success is reported. A failed after-proof is kept as `after_failed.*`.

A re-run on a clone that already holds exactly these bytes makes no commit and reports `DEPLOY OK` only if `DONE` binds this
payload and the recorded HEADs, the deployed commit is in HEAD's history and the CURRENT eight science files equal the preserved
pre-mutation manifest; otherwise `DEPLOY HELD pending verified recovery`. An attempt that wrote its proof but changed nothing
resumes on that proof. An interrupted copy or commit leaves a dirty clone, which every re-run refuses: report it and recover it
explicitly. A hold is reported to the owner and Codex with the kept proof; it is never cleared by editing the proof, rewriting
the scientific clone or rerunning a fit.

Expected output: `payload: 17 files ... compile ... parse`; `deploy proof written before any controller change`; `science bytes
UNCHANGED (8 files, ...; deploy proof DONE at ctl ...)`; the remote digest list; `authority '' lineage '' controls ''`;
`designated ''`; `partition schema row19-provider-partition-2 epoch 2 owned 3274 (ee31504e4a04)`; `activation HOLD: ...`;
`IDENTICAL` (28 files: the 17 v17 pins, controls, adoption, the e2 partition, the six data files, the record and e1); `DEPLOY OK`.

From this commit on, every new Lengau refit admission HOLDS until step 6. Settlements may resume (see "The coordinated hold").

## 5. A fresh installed inventory (Mac, read-only Lengau checks)

    bash chpc/migration_v17/ec2_cycle_v17.sh pre-activation

It checks the Mac promotion and drain, then on Lengau (read-only) that v17 is deployed and adopted (deploy proof `DONE`, its
commit in HEAD's history, `ctl_clean`) and epoch 2 not yet activated; runs `python3 aws_ec2/prod_authority.py inventory` and
`python3 aws_ec2/ec2_sync.py cycle` (DESIGN_v17 s.6 step 5; the cycle seals and installs its own new generation, the first call
seals a local one); then checks on Lengau that the INSTALLED inventory is fresh, that no attempt owns a coordinate outside the
3,274 and that no live attempt of another epoch exists (the read-only mirror of `row19_partition.handover_problems`). It prints
the time left: step 6 must follow within 6 h of the seal (`INVENTORY_MAX_AGE_S`). A failure stops with the command's status; a
re-run seals a new generation (the root accepts only strictly newer ones).

## 6. Canonical epoch-2 activation (Lengau)

    bash chpc/migration_v17/lengau.sh activate_e2.sh

It refuses unless v17 is deployed and adopted (`DONE`, `ctl_clean`, the e2 partition at `48cea639`), `activation_e1.json`
exists, the drain is observed, the controller lineage is v17's, the installed inventory passes the same 6 h precheck, and the
destination `row19_screen/ec2/activation_e2.json` is contained and absent. It then runs the reviewed command

    $T/t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json

which takes the common plan lock itself and refuses (exit 3, nothing written) on a held lock, non-adopted controls, a latest
version not pinning `48cea639`, a missing or foreign e1 activation, a stale inventory, an outside owner, a live attempt of
another epoch, an EC2 history problem or any Lengau claim on an owned coordinate. After it, the body verifies the written proof
is THE canonical activation of e2 under the adopted v17 (`row19_partition.activation_problem`, mode canonical; controls version
17, `9ea4e727`, epoch 2) and that the printed sha256 is the file's. Expected: `activated epoch 2: ... sha256 ...`,
`activation proof ...: ... activation_problem ''`, `ACTIVATED epoch 2`.

A re-run on an existing proof verifies it and prints `ALREADY ACTIVATED (verified)` (the completed state, also after an
interruption between the proof's link and the command's report). A refused activation is reported verbatim: a held plan lock -
retry later; a stale inventory - a fresh step 5; a claim on an owned coordinate - re-snapshot, re-declare, re-review; never erase
a claim or edit a proof. The e1 proof stays on the root as provenance.

## 7. ACK and fresh whole-role v17 receipts (Mac)

    bash chpc/migration_v17/ec2_cycle_v17.sh post-activation

It verifies the canonical activation on the root (read-only), runs `python3 aws_ec2/ec2_sync.py cycle` (a generation binding
`activation_e2.json` installed and acknowledged), the refit receipt
`python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt` (it must exit 0:
fresh, production, zero alarms), `receipt_check_v17.py` on that receipt (generation 17 = latest 17 with controls `9ea4e727` in
its verifier document, the designated view, the EC2 binding naming exactly `activation_e1.json` and `activation_e2.json`, no
HOLD, STOP or EC2 problem), then the bank receipt `python3 chpc/row22_bank_status.py --manifest <abs>/chpc/row22_bank_manifest.json
--publish-receipt`. Expected: `RECEIPT OK ...`, `POST-ACTIVATION CYCLE AND RECEIPTS OK`. Any alarm or `designated set:` alarm
stops the migration for review; a re-run publishes new receipts.

## 8. Pilot qualification rollover - ONE regenerated qualification of the existing job 1, a NEW hash, no fit

Under v17 the verifier stamps generation 17 and `generation_problem` requires it, so the v16 qualification `2c7a7ef1` and its
adopted review stop satisfying the refit gate (DESIGN_v17 s.3 item 1).

1. `bash chpc/migration_v17/lengau.sh rollover_pilot_v17.sh`. It refuses unless v17 is deployed and adopted (`DONE`), the
   canonical e2 activation is on the root, the drain is observed, the v16 archive verifies and certifies byte-identical copies
   of the active `review_refit.json` and of `qualified_refit_job1.json` (`2c7a7ef1`), and the review is bound to `2c7a7ef1`; the
   source, target, directory and chmod target are containment-checked immediately before the move and the chmod. It moves the
   review to `gate_retired/review_refit.v16_qual2c7a7ef1_max100.json` (read-only). `scaleup_refit_v16.json` is not touched.
   Expected: `retired to ...`. A re-run reports `already retired (verified)` (and completes a chmod an interruption missed).
2. Make ONE call: `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1`.
   Expected: `QUALIFIED: refit job 1 (<qsha16>) copied to the gate`. A `NOT QUALIFIED` stops the migration; do not repeat it.
3. `python3 chpc/migration_v17/package_qual_v17.py --dry-run`, then without `--dry-run`: it writes
   `chpc/qualification_v17_<qsha8>/` (the qualification, its verifier document, the receipt the call published, every watch
   receipt the qualification names, both archives' `SHA256SUMS`, and `SHA256SUMS`), refusing a qualification that is still
   `2c7a7ef1` or whose verifier is not generation 17. Commit it with explicit paths and route it to Codex for
   `ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100`. Never reuse the `3c605514` or `2c7a7ef1` literal.
4. After Codex's committed record: `bash chpc/migration_v17/lengau.sh adopt_pilot17.sh --file reviews/<record>.md`. It refuses
   while a review is active, without the retired v16 review, while the gate still holds `2c7a7ef1`, without the canonical
   activation, without an observed drain, when the record does not carry the literal for EXACTLY the gate's qualification, or
   when the record destination or gate paths fail containment; it commits the record in the controller clone and runs the
   supported `--adopt-review <record> --max-job-number 100`, which creates the new `gate/review_refit.json` and never overwrites
   one. Expected: `adopt_pilot17 complete`.

## 9. Refills resume

With the new pilot adopted, the existing scale-up adoption (`gate/scaleup_refit_v16.json`, not generation-bound) in force and a
fresh receipt (at most 2,700 s old) each time, refills resume through the refill scripts, inside refit+S 81,000, programme
100,000, serial max_run 10 and job ceiling 100, exactly as under v16. The coordinated hold ends here. If no scale-up adoption is
present (preflight reports it), admission stays first-job-alone until one is adopted.

## Operator sequence (summary)

hold -> `preflight_v17.sh` -> `archive_v16.sh` -> `promote_v17.py` (+ Mac commit) -> `deploy_v17.sh` (settlements may resume) ->
`ec2_cycle_v17.sh pre-activation` -> within 6 h `lengau.sh activate_e2.sh` -> `ec2_cycle_v17.sh post-activation` ->
`lengau.sh rollover_pilot_v17.sh` -> ONE `--qualify 1` -> `package_qual_v17.py` (+ commit) -> Codex pilot literal ->
`lengau.sh adopt_pilot17.sh --file <record>` -> refills.

Still separate and later (not this migration): the reviewed E2Q1 bundle collection/verification/staging procedure and its
prospective permission (the qualifier command passes `--snapshot chpc/claims_snapshot_e2.json`, the deployed `31cc268f`), R6'
interleaving and capacity evidence, the schema-3 RELEASE certificate, the exact-result review, `release-adopt`, the p80 and
`row19_screen_release.py` re-pins, rescue.

## Tests (private copies only)

`python3 chpc/migration_v17/test_migration_v17.py` (from anywhere; `-k <substring>` selects, `--keep` keeps the temp world). It
builds throwaway worlds from an explicit ALLOWLIST of administrative files copied from the live tree (it never clones or hashes
the whole repository, so no protected plant/key/sample file or scientific source is read; the job clone holds synthetic
placeholders), a fake Lengau root and fake tools (`ps`, `sha256sum`; `ssh` and `scp` that always refuse; restricted git and
flock CLIs on the Lengau half's PATH), copies the production files and substitutes exactly the `# @root` and `# @transport`
lines. The fake `$T/t1py` is python3 for `-c` snippets, simulates the two positive controller commands that cannot run off
Lengau (`row19_partition.py activate`, `--adopt-review`) and refuses every other controller script. `ec2_sync.py`, the refit and
bank status are private stubs; `prod_authority.py inventory` runs for real in the private tree.

It covers the positive route end to end (with every re-run), the restricted-CLI route, and interruption/retry at every step:
preflight refusals (package bytes, record, Mac drain and authority lock, live state, Lengau state and leftovers); archive
(incomplete sources, failed checksum, unreadable source, staging left on either side, a Mac half that failed after the Lengau
half, self-consistent subsets, a substituted Mac member, the strict Mac verify); promotion interrupted after the controls copy;
deploy (archive corruption, an uncommitted promotion, changed data, every drain observation, every science failure, the
after-proof retries, a copy failure resuming on its proof, a mid-payload failure and a refused commit leaving a dirty clone,
proof tampering, payload compile failures, an early v17 path); containment (controller, gate, archive, ec2 directory, gate
members, committed nested `chpc`/`reviews`/`aws_ec2` redirects, a temporary-sibling symlink, a controller alias in the science
clone, gitfile/symlinked `.git`); the evidence allowlist (including the newline-named entry); the EC2 cycles (failed sync,
stale inventory, outside owner, receipts with an alarm, generation 16, no e2 binding, a failed bank receipt, and retries); the
activation (held lock, refused problems, crash after the link, a wrong proof never edited, drain failures, stale inventory,
ordering); rollover, package and adoption refusals and retries. Results: `test_results.txt`.

Untested on the Mac: real ssh transport and Lengau's real tools (git, flock, realpath, base64, sha256sum - emulated by restricted
CLIs only) and Lustre's flock(2)/rename/chmod behaviour; the real canonical activation, `ec2_sync` cycle, refit/bank receipts,
`--qualify` and `--adopt-review` (simulated or stubbed); the real controller-clone commit on Lengau.

## Known consequences of v17 (not migration steps)

- `row19_screen_release.py` (pinned, unchanged) and the `release_p80` adoption bind the v16 admission and controls: no numerical
  release under v17 until their own reviewed packages re-pin the v17 bytes (DESIGN_v17 s.3 item 2).
- `row19_ec2_shadow.py` still hard-codes 60,000; S stays terminal.
- Under v17 the e1 activation proof is historical (v17 no longer pins e1); it is kept, never erased.

## Abort and recovery

- Before step 4 a failure leaves Lengau on v16; a Mac promotion committed but not deployed leaves Lengau on v16 - keep the hold
  and do not run the Mac status or EC2 commands until step 7.
- After step 4 and before step 6, new refit admission holds and science continues; settlements may run. A failed activation is
  reported verbatim and repaired by the reviewed route (a fresh step 5; a re-snapshot); the controls are never reverted.
- A `DEPLOY HELD` keeps the controller clone and `$T/archive_screen/v17_deploy_proof/` for an explicit recovery decision by the
  owner and Codex.
- Report every refusal verbatim. The rescue route stays disabled throughout.

## Open choices for Codex (this scripts review)

1. **Activation freshness margin.** `activate_e2.sh` prechecks the installed inventory with the canonical 6 h rule and no extra
   margin; the activation re-checks it under the plan lock. A smaller precheck bound (for example 5 h) would refuse earlier.
2. **`prod_authority.py inventory` before the cycle** (DESIGN_v17 s.6 step 5 lists both). The cycle seals its own generation, so
   the first call only seals a local generation that is never installed; kept for fidelity to the reviewed text.
3. **The step-8 order.** `rollover_pilot_v17.sh` requires the canonical activation first (DESIGN s.6 order 6 -> 7 -> 8). Retiring
   the review before the activation is harmless but useless (the receipts need the activation).
4. **Drain pattern widened.** `CTLPAT` adds `programme_gate|row19_ledger` (settlements) to the v16 pattern; the Mac pattern adds
   the EC2 authority commands and `bench_reaper.py` (a live attempt makes the migration wait; nothing is stopped).
5. **The Lengau `SHA256SUMS` copy on the Mac** (`chpc/results/archive/row19_screen_v16_before_v17.lengau_SHA256SUMS.txt`) is a
   new committed path beside the Mac archive, written only after the Mac archive names that Lengau archive, used by
   `check-promoted` and the pilot package. The alternative is to fetch it over ssh at packaging time.
6. **Settlements after DEPLOY OK.** The runbook lets finished jobs be settled between steps from DEPLOY OK on (lineage clean
   under v17), rather than deferring them to step 9.
7. **Step-4 compile check.** Payload Python is compiled (not executed) and JSON parsed under `$T/t1py` before any controller
   write; a failure refuses with nothing changed.
8. **`receipt_check_v17.py` scope.** It requires exactly `activation_e1.json` and `activation_e2.json` in the receipt's EC2
   binding; a later epoch would need its own check.
