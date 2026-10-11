#!/bin/bash
# Migration step 8c (Lengau): adopt Codex's review of the REGENERATED v13 qualification (new hash, max job 100).
# Usage: REC=reviews/<record>.md; scp the committed record to $T/patches/ctl13.$(basename $REC) first, then
#   ssh -o ControlPath=none lengau "REC=$REC bash -s" < chpc/migration_v13/adopt_pilot13.sh
# The supported adopter creates the NEW gate review_refit.json and refuses when one exists (never overwrites).
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; C=$T/rsc_screen_ctl/workspace_demo/t1_access
[ -n "${REC:-}" ] || { echo "REC unset"; exit 1; }
cd $C || exit 1
[ -e $T/row19_screen/gate/review_refit.json ] && { echo "an active review exists; retire it first (rollover_pilot.sh)"; exit 1; }
[ -e $REC ] || { cp $T/patches/ctl13.$(basename $REC) $REC && git add $REC && git -c user.name=R052 -c user.email=r052@local commit -q -m "Codex record: v13 refit pilot ADOPT max 100 on the regenerated qualification" -- $REC; } || exit 1
git log -1 --format=%h; sha256sum $REC
$T/t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-review $REC --max-job-number 100 2>&1 | tail -4
sha256sum $T/row19_screen/gate/review_refit.json
