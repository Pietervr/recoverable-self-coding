#!/bin/bash
# Cutover v14 -> v15, step 2 (Mac -> Lengau): FIRST an immutable Lengau archive of the actually adopted v14 controller state
# and the whole gate (archive_screen/v14_before_v15: gate/, ctl/, SHA256SUMS; refuses if it exists), THEN the promoted v15
# controls, status, admission, adoption record and the review record into the CONTROLLER clone rsc_screen_ctl (one commit). The job
# clone rsc_screen is not touched; its science bytes are verified unchanged. Then the controls/lineage/authority checks the
# admission uses, and a local-vs-remote comparison of every pinned file. Requires Mac chpc/ promoted (controls 828d3b69).
# Usage (from workspace_demo/t1_access): bash chpc/migration_v15/deploy_v15.sh [--dry-run]
set -u
DRY=${1:-}
REC=reviews/2026-10-12_v15_r14_alias_repair_codex_record.md
[ "$(shasum -a 256 chpc/row19_screen_controls.json | cut -c1-64)" = 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5 ] || { echo "Mac chpc/ is not promoted to v15 (promote_v15.py)"; exit 3; }
CHANGED="chpc/row19_screen_status.py chpc/row19_screen_admit.py chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json $REC"
ALL=$(python3 -c 'import json; v = json.load(open("chpc/row19_screen_controls.json"))["versions"][-1]; print(" ".join(sorted(v["files"])))')
ALL="$ALL chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_partition_e1.json $REC"
shasum -a 256 $ALL | sort -k2 > /tmp/v15_local.txt
echo "== local ($(wc -l < /tmp/v15_local.txt) files; copied: $CHANGED)"; cut -c1-12,65- /tmp/v15_local.txt
[ "$DRY" = "--dry-run" ] && { echo "DRY RUN: nothing copied"; exit 0; }
O="-o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes"
for f in $CHANGED; do scp $O -q "$f" "lengau:/mnt/lustre/users/pvanrooyen/t1_toolchain/patches/ctl15.$(echo $f | tr / _)" || { echo "FAIL scp $f"; exit 1; }; done
ssh $O lengau "CHANGED='$CHANGED' ALL='$ALL' bash -s" <<'REMOTE' > /tmp/v15_remote.txt 2>&1
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; C=$T/rsc_screen_ctl/workspace_demo/t1_access; J=$T/rsc_screen/workspace_demo/t1_access
A=$T/archive_screen/v14_before_v15
[ -e "$A" ] && { echo "ABORT: archive exists, not overwriting: $A"; exit 1; }
cd $C || exit 1
[ -z "$(git status --short)" ] || { echo "ABORT: controller clone not clean"; exit 1; }
[ "$(sha256sum chpc/row19_screen_controls.json | cut -c1-64)" = 95d9bdfe4e4883b3e04d458a606c34d8504584b65e41344185beb8980df65630 ] || { echo "ABORT: controller clone controls are not adopted v14"; exit 1; }
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition" | grep -v grep)
[ -n "$p" ] && { echo "ABORT: controller command running on the login node:"; echo "$p"; exit 1; }
mkdir -p $A/gate $A/ctl || exit 1
cp -p $T/row19_screen/gate/* $A/gate/ || exit 1
for f in row19_screen_controls.json row19_screen_controls_adoption.json row19_screen_status.py row19_screen_admit.py row19_screen_verify.py programme_gate.py; do
  cp -p $C/chpc/$f $A/ctl/ || exit 1
done
git log -1 --format='rsc_screen_ctl HEAD %H' > $A/ctl/HEAD.txt
(cd $A && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
find $A -type f -exec chmod a-w {} +
echo "archive $A $(wc -l < $A/SHA256SUMS) files SHA256SUMS $(sha256sum $A/SHA256SUMS | cut -c1-16)"
grep -E "gate/(qualified|review)_refit|ctl/row19_screen_(controls|status)" $A/SHA256SUMS | cut -c1-16,65-
SCI="chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py chpc/row19_ledger.py chpc/row19_slice.py chpc/row19_screen_orig.py"
(cd $J && sha256sum $SCI > /tmp/sci15_before.txt)
for f in $CHANGED; do mkdir -p $(dirname $f); cp $T/patches/ctl15.$(echo $f | tr / _) $f || exit 1; done
git add $CHANGED && git -c user.name=R052 -c user.email=r052@local commit -q -m 'screen controllers: lineage version 15 (status + admission REVISION 14 crashed-worker slot disposition; RSC b6ea998, review f1bede4); every other controller byte and the epoch-1 partition unchanged' -- $CHANGED
git log -1 --format='ctl %h'; git status --short | head -3
echo "== remote"; sha256sum $ALL | sort -k2
(cd $J && sha256sum $SCI > /tmp/sci15_after.txt); cmp -s /tmp/sci15_before.txt /tmp/sci15_after.txt && echo "science bytes UNCHANGED" || echo "ABORT: science bytes changed"
$T/t1py -c 'import sys; sys.path.insert(0,"chpc"); import programme_gate as PG, row19_screen_admit as A; print("authority", repr(PG.controls_authority_problem()), "lineage", repr(PG.lineage_problem()), "controls", repr(A.controls_problem()))'
REMOTE
cat /tmp/v15_remote.txt
echo "== local vs remote"; diff <(awk '{print $1, $2}' /tmp/v15_local.txt) <(sed -n '/^== remote/,/^science /p' /tmp/v15_remote.txt | grep -E '^[0-9a-f]{64} ' | awk '{print $1, $2}') && echo IDENTICAL
