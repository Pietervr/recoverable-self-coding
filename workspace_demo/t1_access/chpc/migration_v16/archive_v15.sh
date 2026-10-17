#!/bin/bash
# Migration v15 -> v16, step 2 (Mac -> Lengau, then Mac): immutable archives of the ACTUALLY ADOPTED v15 state BEFORE anything
# changes. Each archive has a fixed mandatory inventory, is built in a staging directory, verified in full (every digest AND
# the exact inventory) and only then published by one atomic rename with a COMPLETE certificate. A digest list that verifies
# a subset is never enough.
#  a. Lengau $T/archive_screen/v15_before_v16 (lengau_archive.py): ctl/HEAD.txt (the controller clone's HEAD); ctl/<path> for
#     EVERY file the adopted v15 entry pins plus the v15 controls, adoption, budget phases chpc/row19_screen_budget.json, the
#     screen manifest and the two row-22 bank controllers; the WHOLE gate (qualified_refit_job1.json 3c605514, the active
#     review_refit.json, every receipt and PBS copy) with INVENTORY.gate captured from the source; the refit job scripts
#     jobs/row19_screen_refit_* (at least one) with INVENTORY.jobs; ledger/row19_screen_campaign_budget.json; SHA256SUMS;
#     COMPLETE. Every source must exist as a regular file (no symlink), every copy and digest must succeed. Refuses unless the
#     drain is observed (a checked process inventory and both locks probed free), the controller clone is clean at the v15
#     bytes, the gate qualification is 3c605514 and a review is active.
#  b. Mac chpc/results/archive/row19_screen_v15_before_v16/ (mac_archive.py): EXACTLY row19_screen_controls.json (828d3b69),
#     row19_screen_controls_adoption.json (970c29f5), row19_screen_admit.py (ac06e803), row19_screen_status.py (0effcba3),
#     row19_screen_budget.json (committed bytes) and qualified_refit_job1.json (3c605514), with SHA256SUMS and COMPLETE (which
#     also records the Lengau archive's SHA256SUMS digest). promote_v16.py and deploy_v16.sh require it by name.
# Re-run: an existing archive is accepted only if its complete certificate verifies; an existing one that does not, or a
# staging directory left by an interrupted build, REFUSES and is left exactly as it is (inspect and recover by hand).
# Usage (from workspace_demo/t1_access): bash chpc/migration_v16/archive_v15.sh [--dry-run]
#   --dry-run   the Mac checks and the plan only: no ssh, nothing written.
# Production route only (lengau.sh); tests run private copies (test_migration_v16.py).
set -u -o pipefail
DRY=${1:-}
fail() { echo "ARCHIVE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
MA=chpc/results/archive/row19_screen_v15_before_v16
QUAL=chpc/results/row19_screen/receipts/qualified_refit_job1.json
want() { [ -f "$1" ] && [ ! -L "$1" ] || fail "$1 is missing"; [ "$(shasum -a 256 "$1" | cut -c1-64)" = "$2" ] || fail "$1 is not $2"; }
ls -d chpc/results/archive/.row19_screen_v15_before_v16.staging* >/dev/null 2>&1 \
  && fail "an interrupted Mac archive build left chpc/results/archive/.row19_screen_v15_before_v16.staging*; partial evidence kept, inspect it by hand"
if [ -e $MA ] || [ -L $MA ]; then
  python3 chpc/migration_v16/mac_archive.py verify || fail "$MA exists but does not verify as the complete v15 archive; not overwriting (inspect by hand)"
  MAC_DONE=1
else
  want chpc/row19_screen_controls.json 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5
  want chpc/row19_screen_controls_adoption.json 970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d
  want chpc/row19_screen_admit.py ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac
  want chpc/row19_screen_status.py 0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b
  want $QUAL 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c
  [ -f chpc/row19_screen_budget.json ] || fail "chpc/row19_screen_budget.json is missing"
  git ls-files --error-unmatch -- chpc/row19_screen_budget.json >/dev/null 2>&1 && git diff --quiet HEAD -- chpc/row19_screen_budget.json \
    || fail "chpc/row19_screen_budget.json is not git-tracked and unmodified"
  MAC_DONE=0
fi
if [ "$DRY" = "--dry-run" ]; then
  echo "DRY RUN - Mac checks pass; would:"
  echo "  - Lengau: verify the sources (lengau_archive.py inventory), then stage, verify and publish \$T/archive_screen/v15_before_v16 with COMPLETE (or verify an existing one)"
  [ $MAC_DONE = 1 ] && echo "  - Mac: $MA exists and verifies; left as it is" || echo "  - Mac: stage, verify and publish $MA (6 named files + SHA256SUMS + COMPLETE), read-only"
  exit 0
fi
. chpc/migration_v16/lengau.sh || fail "cannot load chpc/migration_v16/lengau.sh"
echo "== a. Lengau"
OUTF=$(mktemp -t v16_archive) || fail "mktemp failed"
to_lengau - > "$OUTF" 2>&1 <<'REMOTE'
if [ -e "$A" ] || [ -L "$A" ]; then
  archive_py verify "$T" || die "archive exists and does not verify as complete, not overwriting: $A"
  echo "archive exists and verifies, left as it is"; exit 0
fi
! ls -d "$T"/archive_screen/.v15_before_v16.staging* >/dev/null 2>&1 \
  || die "an interrupted archive build left $T/archive_screen/.v15_before_v16.staging*; partial evidence kept, inspect and recover it by hand"
drained
locks_free
cd "$C" || die "no controller clone $C"
ctl_git
git_clean "$C"
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
src_file "$G/qualified_refit_job1.json" "$T/row19_screen" "gate qualification"; src_file "$G/review_refit.json" "$T/row19_screen" "active gate review"
dst_dir "$T/archive_screen" "$T" "archive parent"; dst_absent "$A" "$T/archive_screen" "archive"
pin chpc/row19_screen_controls.json $V15_CONTROLS "controller clone controls (adopted v15)"
pin chpc/row19_screen_controls_adoption.json $V15_ADOPTION "controller clone adoption (v15 record)"
pin "$G/qualified_refit_job1.json" $V15_QUAL "gate qualification"
[ -f "$G/review_refit.json" ] || die "no active gate review_refit.json"
head=$(cd -- "$C" && git rev-parse --verify HEAD) || die "git rev-parse HEAD failed in the controller clone"
archive_py build "$T" "$head" || die "the archive build refused or failed (above); nothing was published"
archive_py verify "$T" || die "the published archive does not verify (above)"
REMOTE
rc=$?
OUT=$(cat "$OUTF") || fail "cannot read the Lengau output"
rm -f "$OUTF"
printf '%s\n' "$OUT"
[ $rc = 0 ] || fail "the Lengau archive failed (exit $rc, above); the Mac archive was not written"
LSUMS=$(printf '%s\n' "$OUT" | sed -n 's/^sha256sums=\([0-9a-f]\{64\}\)$/\1/p' | tail -1)
[ ${#LSUMS} = 64 ] || fail "the Lengau half did not report its verified SHA256SUMS digest"
echo "== b. Mac"
if [ $MAC_DONE = 1 ]; then
  rec=$(python3 chpc/migration_v16/mac_archive.py verify --get lengau_sha256sums) || fail "the Mac archive no longer verifies"
  [ "$rec" = "$LSUMS" ] || fail "the Mac archive was made with another Lengau archive (${rec:0:16}), not this one (${LSUMS:0:16})"
  echo "Mac archive exists, verifies and names this Lengau archive; left as it is"
else
  python3 chpc/migration_v16/mac_archive.py build "$LSUMS" || fail "the Mac archive build refused or failed (above)"
fi
echo "ARCHIVE OK - commit the Mac archive with explicit paths together with the promotion (step 3)"
