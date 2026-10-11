#!/bin/bash
# Migration step 2 (Lengau; run as: ssh -o ControlPath=none lengau bash -s < chpc/migration_v13/archive_v9.sh).
# Immutable archive of the ACTUALLY ADOPTED v9 controller state and the whole gate (incl. the pilot qualification 3820ac0e,
# review_refit.json 0324ff53, every watch/verify receipt) BEFORE anything changes. Refuses to overwrite.
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; A=$T/archive_screen/v9_before_v13
[ -e "$A" ] && { echo "archive exists, not overwriting: $A"; exit 1; }
C=$T/rsc_screen_ctl/workspace_demo/t1_access
[ "$(sha256sum $T/row19_screen/gate/qualified_refit_job1.json | cut -c1-64)" = 3820ac0e0c28a9cf484f02be3a9c377891aa81595413978d74e7de1eddee4678 ] || { echo "gate qualification is not 3820ac0e"; exit 1; }
mkdir -p $A/gate $A/jobs $A/ctl || exit 1
cp -p $T/row19_screen/gate/* $A/gate/ || exit 1
cp -p $T/jobs/row19_screen_refit_* $T/jobs/row19_screen_orig_* $A/jobs/ || exit 1
for f in row19_screen_controls.json row19_screen_controls_adoption.json row19_screen_admit.py row19_screen_status.py row19_screen_verify.py programme_gate.py row19_screen_release.py row19_screen_resources.json row22_bank_status.py row22_bank_submit.py; do
  [ -e $C/chpc/$f ] && { cp -p $C/chpc/$f $A/ctl/ || exit 1; }
done
(cd $C && git log -1 --format='rsc_screen_ctl HEAD %H' > $A/ctl/HEAD.txt)
(cd $A && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
find $A -type f -exec chmod a-w {} +
echo "archive $A"; wc -l < $A/SHA256SUMS; sha256sum $A/SHA256SUMS
grep -E "gate/(qualified|review)_refit|ctl/row19_screen_controls" $A/SHA256SUMS | cut -c1-16,65-
