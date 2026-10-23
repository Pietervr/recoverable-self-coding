#!/bin/bash
# Migration v19 -> v20, steps 5 (--pre-close) and 7 (--post-close) (Mac, with a read-only Lengau check): FRESH GENERATION-20
# ROLE RECEIPTS (the receipts_v19.sh pattern; no EC2 cycle here - the close itself is step 6, close_v20.sh).
#   Mac: v20_package.py check-promoted; the Mac drain (no refill, slot-watch, controller, EC2-authority or reaper process; the
#   authority lock free). Lengau (check_v20.sh PHASE=pre|post): v20 deployed and adopted (deploy proof DONE), e3 pinned, e1/e2
#   proofs unchanged, no e3 activation yet (pre) or epoch 3 the canonical activation (post), the node document 730ea262 in
#   place. Then the refit receipt
#   `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt` (it must exit
#   0: fresh, production, zero alarms - the v20 status view fetches the node document and dispositions refit job 54),
#   receipt_check_v20.py --phase pre|post on that receipt (generation 20 = latest 20 with controls 4e64982b, the designated view,
#   the EC2 binding with exactly activation_e1 and activation_e2 (pre) or e1, e2 and e3 (post: EC2 waiting 0, the view adding
#   up), no HOLD/STOP/problems, and job 54's node disposition bound to 730ea262), then
#   the bank receipt `python3 chpc/row22_bank_status.py --manifest <abs>/chpc/row22_bank_manifest.json --publish-receipt`.
# Re-run: always safe - every receipt is a new file; a failed command stops the script with its exit status and nothing is
# retried automatically. An alarm stops the migration for review (an alarm about the EC2 authority inventory's age with a live
# attempt is NOT cleared here: that is the separately reviewed EC2 cycle route). Usage (from workspace_demo/t1_access).
# Production route only; tests run private copies.
set -u -o pipefail
fail() { echo "RECEIPTS REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
case "${1:-}" in --pre-close) PHASE=pre;; --post-close) PHASE=post;; *) fail "usage: receipts_v20.sh --pre-close (step 5) | --post-close (step 7)";; esac
[ $# = 1 ] || fail "usage: receipts_v20.sh --pre-close | --post-close"
python3 chpc/migration_v20/v20_package.py check-promoted || fail "the Mac promotion is not complete, committed and verified (above)"
python3 chpc/migration_v20/v20_package.py drain || fail "the Mac drain is not observed (above)"
. chpc/migration_v20/lengau.sh || fail "cannot load chpc/migration_v20/lengau.sh"
to_lengau check_v20.sh --var "PHASE=$PHASE" || fail "the Lengau check refused (above); no receipt was published"
START=$(date +%s) || fail "no clock"
python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt \
  || fail "the refit receipt is not fresh, production and alarm-free (exit $?, above); stop the migration and report"
python3 chpc/migration_v20/receipt_check_v20.py --since "$START" --phase "$PHASE" || fail "the refit receipt does not bind the v20 generation, the $PHASE-close EC2 activations and the job-54 node disposition (above)"
python3 chpc/row22_bank_status.py --manifest "$PWD/chpc/row22_bank_manifest.json" --publish-receipt \
  || fail "the bank receipt exited $? (above); stop and report"
[ "$PHASE" = pre ] && echo "V20 RECEIPTS OK (pre-close) - next: bash chpc/migration_v20/close_v20.sh (step 6)" \
  || echo "V20 RECEIPTS OK (post-close) - next: bash chpc/migration_v20/lengau.sh rollover_pilot_v20.sh (step 8)"
