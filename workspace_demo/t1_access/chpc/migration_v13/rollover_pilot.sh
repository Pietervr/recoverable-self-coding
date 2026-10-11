#!/bin/bash
# Migration step 8a (Lengau; ssh -o ControlPath=none lengau bash -s < chpc/migration_v13/rollover_pilot.sh).
# Retire the ACTIVE v9 refit review (0324ff53, qualification 3820ac0e, max 100) to gate_retired/ ONLY after verifying the
# v9_before_v13 archive holds byte-identical copies of it and of qualified_refit_job1.json. Admissions must be held. The
# next step (Mac, ONE call) regenerates the qualification from the EXISTING completed pilot job 1 under v13 - a NEW hash, no fit:
#   python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; G=$T/row19_screen/gate; R=$T/row19_screen/gate_retired; A=$T/archive_screen/v9_before_v13
OUT=$R/review_refit.v9_qual3820ac0e_max100.json
[ -e $OUT ] && { echo "retired file exists: $OUT"; exit 1; }
[ -e $G/review_refit.json ] || { echo "no active review_refit.json (already retired?)"; exit 1; }
h=$(sha256sum $G/review_refit.json | cut -c1-64); a=$(grep ' ./gate/review_refit.json$' $A/SHA256SUMS | cut -c1-64)
q=$(sha256sum $G/qualified_refit_job1.json | cut -c1-64); qa=$(grep ' ./gate/qualified_refit_job1.json$' $A/SHA256SUMS | cut -c1-64)
echo "active review $h archived $a; qualification $q archived $qa"
[ -n "$a" ] && [ "$h" = "$a" ] || { echo "MISMATCH: active review is not the archived bytes"; exit 1; }
[ "$q" = 3820ac0e0c28a9cf484f02be3a9c377891aa81595413978d74e7de1eddee4678 ] && [ "$q" = "$qa" ] || { echo "qualification is not the archived 3820ac0e"; exit 1; }
(cd $A && sha256sum -c --quiet SHA256SUMS) || { echo "archive does not verify"; exit 1; }
mkdir -p $R && mv $G/review_refit.json $OUT && chmod a-w $OUT && echo "retired to $OUT"
