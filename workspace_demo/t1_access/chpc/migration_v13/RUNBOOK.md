# Direct v9 -> v13 migration and the EC2 qualification cutover — RUNBOOK

Codex RSC `64034c5` (`reviews/2026-10-11_partition_e1_v13_codex_record.md`, SHA256 `99f059ff…`): FAVOURABLE to adopt exact
controls v13 `d933862e…` (historical); the identity in use is `840840f5…` (Codex RSC `5bab1a9`,
`reviews/2026-10-11_pbs_settled_observation_codex_record.md`, SHA256 `1d71afac…`: v13 with the status REVISION 11 that observes
settled jobs from their settlement after PBS history expiry; literal ADOPT there), pinning the epoch-1 partition `8d1de408…` (k = 40, indices 160–199 of reps 3–102, 4,000
coordinates, a bounded ownership allocation, not a whole-block funding reservation); PREFER direct v9 -> v13, no v12 step.
Prepared, NOT executed. Every command runs from `workspace_demo/t1_access` on the Mac unless marked Lengau; Lengau scripts
run as `ssh -o ControlPath=none lengau bash -s < chpc/migration_v13/<script>`. Every step refuses rather than overwrites.

Never: stop or restart attempt 5, its reaper or any running scientific worker (refit, bank, slice); set
`qualification.permitted` by hand; change the reviewed v13 controls or partition bytes; rerun a pilot fit.

## 0. Preconditions

| Gate | Check | Abort if |
|---|---|---|
| Row 23 declared | fresh `python3 aws_ec2/bench_finish.py --run b2 --attempt 5 --declare` printed ROW 23 SUCCESS; `ec2_release_state.json` row23 backed; committed | no success, or a declare not from a fresh invocation |
| Comparison tree fixed | nothing below touched `rsc_screen_ctl` while the comparator ran (bench_finish re-hashes it) | bench_finish reported a tree change |
| Reviewed bytes | `bash chpc/migration_v13/preflight.sh` | any REFUSED line |

## 1. Hold and drain the old controller commands

The v9 admission's planner has no partition guard and lives in memory in any waiting Python process; replacing files does
not change it (Codex 64034c5). The only admission paths are the refill scripts `refill_r1.sh` / `refill_b1.sh` and the slot
watcher `slot_watch.sh` in the R052 scratchpad (`…/fdb5f471-…/scratchpad/`):

1. Stop invoking the refill scripts; stop the slot-watch background task (it only reads `qstat`; ending it starts nothing).
2. Let any refill already running finish (watch its output), then `bash chpc/migration_v13/preflight.sh`: it refuses while
   any `row19_screen_admit|status|verify`, `row22_bank_submit|status`, `row19_ec2_*` or `row19_partition` process runs on the
   login node. The Mac's own status/receipt commands are not run during the migration.
3. Running PBS jobs (refit, bank, slice) and the attempt-5 reaper continue untouched. A slot that frees during the migration
   stays empty until step 9.

## 2. Archive the actually adopted v9 state (Lengau)

`ssh … bash -s < chpc/migration_v13/archive_v9.sh` -> `archive_screen/v9_before_v13/{gate,jobs,ctl}` with `SHA256SUMS`,
read-only. It copies the WHOLE gate (`qualified_refit_job1.json` 3820ac0e, `review_refit.json` 0324ff53, every watch/verify
receipt), the job scripts and the v9 controller files. Expected: the archive path, its line count, the SHA256SUMS hash and
the three gate/controls lines. Abort if the gate qualification is not 3820ac0e or the archive exists.

## 3. Promote v13 on the Mac

`python3 chpc/migration_v13/promote_v13.py --dry-run`, then without `--dry-run`. It checks every v13 pin, the record's
literal `ADOPT row19-screen-controls sha256=840840f5… version=13` (record 1d71afac), archives the Mac v9 files and the Mac copy of
`qualified_refit_job1.json` to `chpc/results/archive/row19_screen_v9_before_v13/`, copies the candidate controls/admit/status
into `chpc/` and writes the version-13 adoption record. Commit atomically:
`git -C <RSC> add <the 3 chpc files + adoption + archive dir> && git -C <RSC> commit -F <msg> -- <same paths>`.

## 4. Deploy (controller clone + S manifest in the job clone)

`bash chpc/migration_v13/deploy_v13.sh --dry-run`, then without. One commit in `rsc_screen_ctl` with the 14 pinned files,
controls, adoption, partition e1 and the review record; one commit in `rsc_screen` adding only
`chpc/row19_qual_S_manifest.json` (eabbda2a). Expected: `science bytes UNCHANGED`, `authority '' lineage '' controls ''`
(empty problem strings), `IDENTICAL`. Abort on any non-empty problem or a diff.

## 5. Canonical activation (Lengau)

`ssh … bash -s < chpc/migration_v13/activate_e1.sh` -> `row19_partition.py activate` under the plan lock with the adopted
v13 controls: the actual all-state claim scan (completed records, every historical/planned/reserved Lengau claim; a malformed
plan is an unknown claim). Expected `activated epoch 1: <root>/ec2/activation_e1.json sha256 …`. A HELD with problems means a
Lengau claim sits in the block: stop and report; never edit e1 (a new reviewed epoch is the only change).

## 6. Initial inventory

`python3 aws_ec2/ec2_sync.py cycle` - seals a new generation, installs it on the root with the deployed `row19_ec2_root.py`
(canonical: manifest 43b75f94 at its own root), pulls the acknowledgement and register. Expected exit 0. This is the first
run of the deployed handshake (an operational check Codex left open): any HELD stops the migration.

## 7. Fresh whole-role v13 evidence

`python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt`, then the bank:
`python3 chpc/row22_bank_status.py --manifest <abs>/chpc/row22_bank_manifest.json --publish-receipt`. Expected: fresh,
production, zero alarms; the refit receipt now carries the EC2 state (activation, installed inventory).

## 8. Pilot rollover — one regenerated qualification, a NEW hash, no fit

a. `ssh … bash -s < chpc/migration_v13/rollover_pilot.sh`: verifies the archive holds byte-identical copies of the active
   `review_refit.json` and `qualified_refit_job1.json` (3820ac0e), then retires the review to
   `gate_retired/review_refit.v9_qual3820ac0e_max100.json` (read-only). The old d64600f8/3820ac0e authority stays historical.
b. ONE call: `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1`
   - regenerates `qualified_refit_job1.json` from the EXISTING completed pilot job 1 under v13 (new controller/binding/time
   evidence -> a new hash) and copies it to the gate. Record the new hash `<qsha>`. PBS no longer knows 7523818: its state F /
   exit 0 come from the settlement note and its scheduler memory/walltime request from `watch_refit_20261010T224529Z.json`
   (the job summary's `prior_receipt`); Codex 5bab1a9 (c) accepts that, to be verified in the step-8c review (receipt bytes and
   hash, direct-qstat provenance, same PBS id/F/exit, settlement provenance, carried values).
c. Route a brief to Codex with the new qualification metadata (hash, bound jobs, receipt, archive SHA256SUMS) for the
   matching literal `ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100`. Never reuse the 3820ac0e literal.
d. After Codex's committed record: `REC=reviews/<record>.md`, copy it to `$T/patches/ctl13.<basename>`, then
   `ssh -o ControlPath=none lengau "REC=$REC bash -s" < chpc/migration_v13/adopt_pilot13.sh` (creates the NEW gate review;
   refuses if one exists).

Later inventory changes need fresh current receipts (step 7), not another `--qualify`.

## 9. Resume Lengau refills

Fresh receipt per refill (as before), then `refill_r1.sh` / `refill_b1.sh`; re-arm `slot_watch.sh`. The v13 admission now
refuses any coordinate in indices 160–199.

## 10. Qualification cutover and Q1 / Q2 / S

1. `python3 aws_ec2/qual_permit.py --record <the correct FAVOURABLE qualification-permission record, path relative to aws_ec2/>`:
   drains in-flight benchmark commands (exclusive lock), writes `runs/BENCH_FENCE.json`, sets `qualification.permitted`.
   The record must be THIS package's favourable permission review (the code pins the file, it does not parse its verdict).
2. Operational manifests: `python3 aws_ec2/make_prod_manifest.py --epoch 1 --contract Q1 --expect-s 75300 --out aws_ec2/prod/manifest_q1_e1.json`
   (and Q2 likewise).
3. Before each launch: `python3 aws_ec2/ec2_sync.py cycle`, then a fresh refit receipt (step 7) - the launcher requires a
   receipt <= 2,700 s old bound to the current inventory generation.
4. Q1: `python3 aws_ec2/prod_launch.py --contract Q1 --epoch 1 --partition chpc/row19_partition_e1.json --manifest aws_ec2/prod/manifest_q1_e1.json --snapshot chpc/results/row19_screen --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --dry-run`, then without `--dry-run`. Worst USD 27.92 (ceiling 28).
5. S (Lengau, both jobs): `t1py chpc/row19_ec2_shadow.py --manifest chpc/row19_screen_manifest.json --s-manifest chpc/row19_qual_S_manifest.json --job 1 --dry-run`, then without; same for `--job 2`. 2,304 core-h reserved under the programme 100,000 and the refit+S 60,000 sub-envelope.
6. Q2 after Q1 is reconciled: as 4 with `--contract Q2` and its manifest. Worst USD 16.54 (ceiling 17).
7. Reconcile, ingest (`row19_ec2_ingest.py`), run `row19_ec2_qualify.py`; route the certificate for the actual-result
   review. A favourable review -> `prod_authority.py release-adopt` -> production directly (owner's standing go), inside
   USD 2,300 / 3,000. A retry of Q1 or Q2 needs the owner.

## Abort and recovery

Every script refuses on re-run and nothing is overwritten. Before step 5 a failed step leaves Lengau on v9 (refills may
resume on v9 only if the controller clone is still at the v9 commit). After step 5 the activation is permanent; refills
need v13 receipts. Report every refusal verbatim.
