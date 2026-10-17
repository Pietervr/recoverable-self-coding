#!/bin/bash
# Migration v15 -> v16, step 7.4 (Lengau): adopt Codex's review of the REGENERATED v16 refit pilot qualification (new hash,
# max job 100) - the v13 adopt_pilot13.sh pattern. The record must carry
#   ADOPT row19-screen-pilot role=refit qualification=<the new qsha> max_job=100
# (the supported adopter checks it against the gate qualification; a reused 3c605514 literal is refused because the gate now
# holds the regenerated qualification). Usage: REC=reviews/<record>.md; commit the record on the Mac, scp it to
# $T/patches/ctl16.$(basename $REC) first, then
#   ssh -o ControlPath=none lengau "REC=$REC bash -s" < chpc/migration_v16/adopt_pilot16.sh
# The adopter creates the NEW gate review_refit.json and refuses when one exists (never overwrites).
# Test hook: V16_T=<dir containing FAKE_LENGAU> runs against that fake toolchain.
if [ -n "${V16_T:-}" ]; then [ -e "$V16_T/FAKE_LENGAU" ] || { echo "V16_T is a test hook and needs a FAKE_LENGAU marker"; exit 1; }; T=$V16_T; else T=/mnt/lustre/users/pvanrooyen/t1_toolchain; fi
C=$T/rsc_screen_ctl/workspace_demo/t1_access
[ -n "${REC:-}" ] || { echo "REC unset"; exit 1; }
cd $C || exit 1
grep -q '"version": 16' chpc/row19_screen_controls_adoption.json || { echo "v16 is not the adopted controls here"; exit 1; }
[ -e $T/row19_screen/gate/review_refit.json ] && { echo "an active review exists; retire it first (rollover_pilot_v16.sh)"; exit 1; }
[ "$(sha256sum $T/row19_screen/gate/qualified_refit_job1.json | cut -c1-64)" = 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c ] && { echo "the gate qualification is still the v15 3c605514; regenerate it under v16 first (--qualify 1)"; exit 1; }
[ -e $REC ] || { cp $T/patches/ctl16.$(basename $REC) $REC && git add $REC && git -c user.name=R052 -c user.email=r052@local commit -q -m "Codex record: v16 refit pilot ADOPT max 100 on the regenerated qualification" -- $REC; } || exit 1
git log -1 --format=%h; sha256sum $REC
$T/t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-review $REC --max-job-number 100 2>&1 | tail -4
sha256sum $T/row19_screen/gate/review_refit.json
