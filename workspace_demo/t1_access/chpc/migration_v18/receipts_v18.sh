#!/bin/bash
# Migration v17 -> v18, step 5 (Mac, with a read-only Lengau check): FRESH GENERATION-18 ROLE RECEIPTS (the post-activation half
# of migration_v17's ec2_cycle_v17.sh, without any EC2 cycle or activation: v18 changes no partition, data or EC2 code, and
# epoch 2 stays active).
#   Mac: v18_package.py check-promoted; the Mac drain (no refill, slot-watch, controller, EC2-authority or reaper process; the
#   authority lock free). Lengau (check_v18.sh): v18 deployed and adopted (deploy proof DONE), epoch 2 still the canonical
#   activation, the captured node document 730ea262 in place. Then the refit receipt
#   `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt` (it must exit
#   0: fresh, production, zero alarms - the v18 status view fetches the node document and dispositions refit job 54),
#   receipt_check_v18.py on that receipt (generation 18 = latest 18 with controls 452b82df, the designated view, the EC2 binding
#   with exactly activation_e1 and activation_e2, no HOLD/STOP/problems, and job 54's node disposition bound to 730ea262), then
#   the bank receipt `python3 chpc/row22_bank_status.py --manifest <abs>/chpc/row22_bank_manifest.json --publish-receipt`.
# Re-run: always safe - every receipt is a new file; a failed command stops the script with its exit status and nothing is
# retried automatically. An alarm stops the migration for review (an alarm about the EC2 authority inventory's age with a live
# attempt is NOT cleared here: that is the separately reviewed EC2 cycle route). Usage (from workspace_demo/t1_access).
# Production route only; tests run private copies.
set -u -o pipefail
fail() { echo "RECEIPTS REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
[ $# = 0 ] || fail "usage: receipts_v18.sh (no arguments)"
python3 chpc/migration_v18/v18_package.py check-promoted || fail "the Mac promotion is not complete, committed and verified (above)"
python3 chpc/migration_v18/v18_package.py drain || fail "the Mac drain is not observed (above)"
. chpc/migration_v18/lengau.sh || fail "cannot load chpc/migration_v18/lengau.sh"
to_lengau check_v18.sh || fail "the Lengau check refused (above); no receipt was published"
START=$(date +%s) || fail "no clock"
python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt \
  || fail "the refit receipt is not fresh, production and alarm-free (exit $?, above); stop the migration and report"
python3 chpc/migration_v18/receipt_check_v18.py --since "$START" || fail "the refit receipt does not bind the v18 generation, epoch 2 and the job-54 node disposition (above)"
python3 chpc/row22_bank_status.py --manifest "$PWD/chpc/row22_bank_manifest.json" --publish-receipt \
  || fail "the bank receipt exited $? (above); stop and report"
echo "V18 RECEIPTS OK - next: bash chpc/migration_v18/lengau.sh rollover_pilot_v18.sh (step 6)"
