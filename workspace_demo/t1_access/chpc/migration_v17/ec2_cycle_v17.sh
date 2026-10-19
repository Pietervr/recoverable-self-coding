#!/bin/bash
# Migration v16 -> v17, steps 5 and 7 (Mac, with read-only Lengau checks): the EC2 authority cycles around the epoch-2 activation
# (DESIGN_e2.md s.6 steps 6-7; DESIGN_v17.md s.6 steps 5 and 7). Neither cycle calls AWS: prod_authority.py and ec2_sync.py seal
# the authority inventory from the Mac's run ledgers and move it over ssh (and its copy tool) to the root, where the controller clone's
# chpc/row19_ec2_root.py install takes the plan lock and writes the acknowledgement.
#
#   bash chpc/migration_v17/ec2_cycle_v17.sh pre-activation      step 5
#     Mac: v17_package.py check-promoted; the Mac drain (no other EC2-authority, controller or reaper process; the authority lock
#     free). Lengau (check_v17.sh pre-before): v17 deployed and adopted (deploy proof DONE), epoch 2 NOT yet activated. Then
#     `python3 aws_ec2/prod_authority.py inventory` and `python3 aws_ec2/ec2_sync.py cycle` (each must exit 0), then Lengau
#     (check_v17.sh pre-after): the INSTALLED inventory is fresh, with no owner outside the e2 owned set and no live attempt of
#     another epoch. Prints the time left: activate_e2.sh must run within 6 h of the seal (INVENTORY_MAX_AGE_S).
#
#   bash chpc/migration_v17/ec2_cycle_v17.sh post-activation     step 7
#     Mac checks as above. Lengau (check_v17.sh post): the canonical activation_e2.json is on the root. Then
#     `python3 aws_ec2/ec2_sync.py cycle` (a new generation binding activation_e2.json installed and acknowledged), the refit
#     receipt `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt`
#     (exit 0: fresh, production, zero alarms), receipt_check_v17.py on that receipt (generation 17, controls 9ea4e727, the
#     designated view, the EC2 binding with activation_e1 AND activation_e2, no EC2 HOLD/STOP/problems), then the bank receipt
#     `python3 chpc/row22_bank_status.py --manifest <abs>/chpc/row22_bank_manifest.json --publish-receipt` (exit 0).
#
# Re-run: always safe - every cycle seals a NEW generation (the root accepts only strictly newer ones) and every receipt is a new
# file; a failed command stops the script with its exit status and nothing is retried automatically. A HOLD or alarm stops the
# migration for review. Usage (from workspace_demo/t1_access). Production route only; tests run private copies.
set -u -o pipefail
fail() { echo "EC2 CYCLE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
MODE=${1:-}
case $MODE in pre-activation|post-activation) [ $# = 1 ] || fail "usage: ec2_cycle_v17.sh pre-activation|post-activation";;
  *) fail "usage: ec2_cycle_v17.sh pre-activation|post-activation";; esac
python3 chpc/migration_v17/v17_package.py check-promoted || fail "the Mac promotion is not complete, committed and verified (above)"
python3 chpc/migration_v17/v17_package.py drain || fail "the Mac drain is not observed (above)"
. chpc/migration_v17/lengau.sh || fail "cannot load chpc/migration_v17/lengau.sh"
if [ $MODE = pre-activation ]; then
  to_lengau check_v17.sh --var STAGE=pre-before || fail "the Lengau pre-activation check refused (above); no cycle was run"
  python3 aws_ec2/prod_authority.py inventory || fail "prod_authority.py inventory exited $? (above); stop and report"
  python3 aws_ec2/ec2_sync.py cycle || fail "ec2_sync.py cycle exited $? (above); stop and report (a re-run seals a new generation)"
  to_lengau check_v17.sh --var STAGE=pre-after || fail "the installed inventory does not admit the activation (above)"
  echo "PRE-ACTIVATION CYCLE OK - run 'bash chpc/migration_v17/lengau.sh activate_e2.sh' within the time printed above"
  exit 0
fi
to_lengau check_v17.sh --var STAGE=post || fail "the canonical epoch-2 activation is not on the root (above); run activate_e2.sh first"
python3 aws_ec2/ec2_sync.py cycle || fail "ec2_sync.py cycle exited $? (above); stop and report (a re-run seals a new generation)"
START=$(date +%s) || fail "no clock"
python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt \
  || fail "the refit receipt is not fresh, production and alarm-free (exit $?, above); stop the migration and report"
python3 chpc/migration_v17/receipt_check_v17.py --since "$START" || fail "the refit receipt does not bind the v17 generation and the epoch-2 activation (above)"
python3 chpc/row22_bank_status.py --manifest "$PWD/chpc/row22_bank_manifest.json" --publish-receipt \
  || fail "the bank receipt exited $? (above); stop and report"
echo "POST-ACTIVATION CYCLE AND RECEIPTS OK - next: bash chpc/migration_v17/lengau.sh rollover_pilot_v17.sh (step 8)"
