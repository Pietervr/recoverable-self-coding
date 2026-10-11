#!/bin/bash
# Migration step 4 (Mac -> Lengau): deploy the promoted v13 controller bytes, the adoption record, the review record and the
# epoch-1 partition into the CONTROLLER clone rsc_screen_ctl (one commit), and the controls-declared isolated S manifest into
# the JOB clone rsc_screen (one commit; locked science bytes verified unchanged before and after). Then the controls/lineage/
# authority checks the admission uses. Requires: Lengau archive_screen/v9_before_v13 exists; Mac chpc/ promoted (controls 840840f5).
# Usage (from workspace_demo/t1_access): bash chpc/migration_v13/deploy_v13.sh [--dry-run]
set -u
DRY=${1:-}
REC=reviews/2026-10-11_pbs_settled_observation_codex_record.md
[ "$(shasum -a 256 chpc/row19_screen_controls.json | cut -c1-64)" = 840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c ] || { echo "Mac chpc/ is not promoted to v13 (promote_v13.py)"; exit 3; }
FILES=$(python3 -c 'import json; v = json.load(open("chpc/row19_screen_controls.json"))["versions"][-1]; print(" ".join(sorted(v["files"])))')
FILES="$FILES chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_partition_e1.json $REC"
shasum -a 256 $FILES | cut -c1-64,65- | sort -k2 > /tmp/v13_local.txt
echo "== local ($(wc -l < /tmp/v13_local.txt) files)"; cut -c1-12,65- /tmp/v13_local.txt
[ "$DRY" = "--dry-run" ] && { echo "DRY RUN: nothing copied"; exit 0; }
O="-o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes"
for f in $FILES; do scp $O -q "$f" "lengau:/mnt/lustre/users/pvanrooyen/t1_toolchain/patches/ctl13.$(echo $f | tr / _)" || { echo "FAIL scp $f"; exit 1; }; done
ssh $O lengau "FILES='$FILES' bash -s" <<'REMOTE' > /tmp/v13_remote.txt 2>&1
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; C=$T/rsc_screen_ctl/workspace_demo/t1_access; J=$T/rsc_screen/workspace_demo/t1_access
[ -e $T/archive_screen/v9_before_v13/SHA256SUMS ] || { echo "ABORT: v9 archive missing (archive_v9.sh first)"; exit 1; }
SCI="chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py chpc/row19_ledger.py chpc/row19_slice.py chpc/row19_screen_orig.py"
cd $J && sha256sum $SCI > /tmp/sci_before.txt
cd $C || exit 1
[ -z "$(git status --short)" ] || { echo "ABORT: controller clone not clean"; exit 1; }
for f in $FILES; do mkdir -p $(dirname $f); cp $T/patches/ctl13.$(echo $f | tr / _) $f || exit 1; done
git add $FILES && git -c user.name=R052 -c user.email=r052@local commit -q -m 'screen controllers: lineage version 13 adopted directly from v9 (RSC 43a58d1 candidate_v10r4; review 5bab1a9 superseding 64034c5); epoch-1 partition pinned; scientific files unchanged' -- $FILES
git log -1 --format='ctl %h'; git status --short | head -3
echo "== remote"; sha256sum $FILES | sort -k2
cd $J || exit 1
S=chpc/row19_qual_S_manifest.json
if [ ! -e $S ]; then cp $C/$S $S && git add $S && git -c user.name=R052 -c user.email=r052@local commit -q -m 'qualification S: the controls-declared isolated S manifest (eabbda2a) in the job clone; scientific files unchanged' -- $S; fi
git log -1 --format='job %h'; echo "S $(sha256sum $S | cut -c1-12)"
sha256sum $SCI > /tmp/sci_after.txt; cmp -s /tmp/sci_before.txt /tmp/sci_after.txt && echo "science bytes UNCHANGED" || echo "ABORT: science bytes changed"
cd $C && $T/t1py -c 'import sys; sys.path.insert(0,"chpc"); import programme_gate as PG, row19_screen_admit as A; print("authority", repr(PG.controls_authority_problem()), "lineage", repr(PG.lineage_problem()), "controls", repr(A.controls_problem()))'
REMOTE
cat /tmp/v13_remote.txt
echo "== local vs remote"; diff <(awk '{print $1, $2}' /tmp/v13_local.txt) <(sed -n '/^== remote/,/^job /p' /tmp/v13_remote.txt | grep -E '^[0-9a-f]{64} ' | awk '{print $1, $2}') && echo IDENTICAL
