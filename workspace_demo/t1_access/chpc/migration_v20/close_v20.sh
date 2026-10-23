#!/bin/bash
# Migration v19 -> v20, step 6 (Mac -> Lengau): THE EC2 CLOSE (owner decision 23 Oct 2026, route A).
#   Mac: v20_package.py check-promoted (the complete, committed, verified v20 promotion), the Mac drain, then the Mac half of the
#        close preconditions with the PROMOTED authority: `python3 aws_ec2/prod_authority.py close-check` must report MET (no
#        owned coordinate, every attempt reconciled and ingested/dispositioned, the latest sealed inventory current and at most six
#        hours old). It writes nothing.
#   Lengau (close_e3.sh): the checks listed there, `row19_partition.py verify3` against the root's register, then the ONE
#        activation call under the plan lock, then act3_valid.
# If the installed inventory is older than six hours, first (Mac) `python3 aws_ec2/prod_authority.py inventory` and
# `python3 aws_ec2/ec2_sync.py cycle`, then re-run this script.
# Usage (from workspace_demo/t1_access): bash chpc/migration_v20/close_v20.sh [--dry-run]
#   --dry-run   the Mac checks only: no ssh, nothing written anywhere.
set -u -o pipefail
DRY=${1:-}
case $DRY in ""|--dry-run) ;; *) echo "CLOSE REFUSED: unknown argument $DRY"; exit 3;; esac
fail() { echo "CLOSE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
python3 chpc/migration_v20/v20_package.py check-promoted || fail "the Mac promotion is not complete, committed and verified (above)"
python3 chpc/migration_v20/v20_package.py drain || fail "the Mac drain is not observed (above)"
OUT=$(python3 aws_ec2/prod_authority.py close-check); rc=$?
printf '%s\n' "$OUT"
[ $rc = 0 ] && printf '%s\n' "$OUT" | grep -q '"close_preconditions": "MET"' \
  || fail "the Mac half of the close preconditions is NOT MET (above): finish RUNBOOK step 0b"
[ "$DRY" = "--dry-run" ] && { echo "DRY RUN - the Mac checks pass; would run close_e3.sh on Lengau (verify3, then the e3 activation under the plan lock)"; exit 0; }
. chpc/migration_v20/lengau.sh || fail "cannot load chpc/migration_v20/lengau.sh"
OUTF=$(mktemp -t v20_close) || fail "mktemp failed"
to_lengau close_e3.sh > "$OUTF" 2>&1; rc=$?
cat "$OUTF"
grep -q "ABORT" "$OUTF" && { rm -f "$OUTF"; fail "the Lengau half printed an ABORT (above)"; }
grep -qx "lengau close body complete" "$OUTF" || { rm -f "$OUTF"; fail "the Lengau half did not complete (exit $rc, above)"; }
rm -f "$OUTF"
[ $rc = 0 ] || fail "the Lengau half exited $rc (above)"
echo "CLOSE OK - epoch 3 active; next: bash chpc/migration_v20/receipts_v20.sh --post-close (step 7)"
