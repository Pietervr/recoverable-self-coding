#!/bin/bash
# Migration v9 -> v13, step 0 (Mac; read-only). Refuses unless: row 23 is declared (backed) on the Mac, no controller command
# (admit/status/verify/shadow/partition/root) runs on the Lengau login node, the controller clone is clean at the adopted v9
# bytes, the job clone's science bytes are the manifest pins, and the v13 candidate/record/partition are the reviewed bytes.
# Usage: bash chpc/migration_v13/preflight.sh      (from workspace_demo/t1_access)
set -u
fail() { echo "PREFLIGHT REFUSED: $*"; exit 3; }
python3 -c 'import sys; sys.path.insert(0, "aws_ec2"); import prod_authority as PA; r = PA.release_state(); sys.exit(0 if r["row23"]["ok"] else 1)' \
  || fail "row 23 is not declared successful with a backed report (bench_finish.py --declare first)"
want() { [ "$(shasum -a 256 "$1" | cut -c1-64)" = "$2" ] || fail "$1 is not $2"; }
want chpc/candidate_v10r4/row19_screen_controls.json 840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c
want chpc/row19_partition_e1.json 8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608
want reviews/2026-10-11_pbs_settled_observation_codex_record.md 1d71afacaf1f8f722b808a9c9bba5f1cc479d5a1609985a5ffab86d8f92f4abd
want chpc/row19_screen_controls.json 45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07
grep -qx 'ADOPT row19-screen-controls sha256=840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c version=13' reviews/2026-10-11_pbs_settled_observation_codex_record.md \
  || fail "the v13 ADOPT literal is not in the review record"
ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s <<'REMOTE' || fail "Lengau checks failed (above)"
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; C=$T/rsc_screen_ctl/workspace_demo/t1_access; J=$T/rsc_screen/workspace_demo/t1_access
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition" | grep -v grep)
[ -n "$p" ] && { echo "controller command running on the login node:"; echo "$p"; exit 1; }
cd $C || exit 1
[ -z "$(git status --short)" ] || { echo "controller clone has uncommitted changes"; exit 1; }
[ "$(sha256sum chpc/row19_screen_controls.json | cut -c1-64)" = 45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07 ] || { echo "controller clone controls are not adopted v9"; exit 1; }
[ ! -e $T/archive_screen/v9_before_v13 ] || { echo "archive v9_before_v13 already exists (migration started before?)"; exit 1; }
[ ! -e $T/row19_screen/ec2/activation_e1.json ] || { echo "epoch 1 already activated"; exit 1; }
cd $J && sha256sum chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py | cut -c1-12,65-
echo "lengau preflight OK"
REMOTE
echo "PREFLIGHT OK: drain confirmed for this instant - keep refill scripts and the slot watcher stopped until step 9"
