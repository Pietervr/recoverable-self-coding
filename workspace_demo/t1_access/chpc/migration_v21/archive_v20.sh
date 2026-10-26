#!/bin/bash
# Migration v20 -> v21, step 2 (Mac -> Lengau, then Mac): immutable archives of the ACTUALLY ADOPTED v20 state BEFORE anything
# changes (the archive_v19.sh pattern, re-pointed).
#  a. Lengau $T/archive_screen/v20_before_v21 (lengau_archive.py): ctl/HEAD.txt; ctl/<path> for EVERY file the adopted v20 entry
#     pins plus its partition e3 (ca87fb1d), the e1/e2 declarations (provenance), the v20 controls, adoption, admission, programme
#     gate, status, designated declaration, budget phases, screen manifest, the two row-22 bank controllers, the v20 controls
#     record and both v20 pilot records; ctl/untracked/<path> for the three pinned untracked evidence files; the WHOLE gate
#     (qualified_refit_job1.json 2e99d615, the active max-200 review_refit.json, scaleup_refit_v16.json, every receipt) with
#     INVENTORY.gate; jobs/row19_screen_refit_* with INVENTORY.jobs (retaining the node document at 730ea262); the ledger
#     reference copy; the three activation proofs ec2/activation_e1/e2/e3.json; SHA256SUMS; COMPLETE.
#  b. Mac chpc/results/archive/row19_screen_v20_before_v21/ (mac_archive.py): EXACTLY the 8 members of build_v21.ARCHIVE with
#     SHA256SUMS and the JSON COMPLETE (which records the Lengau archive's SHA256SUMS digest).
# Re-run: an existing archive is accepted only if its complete certificate verifies; anything else REFUSES and is left as it is.
# Usage (from workspace_demo/t1_access): bash chpc/migration_v21/archive_v20.sh [--dry-run]
set -u -o pipefail
DRY=${1:-}
case $DRY in ""|--dry-run) ;; *) echo "ARCHIVE REFUSED: unknown argument $DRY"; exit 3;; esac
fail() { echo "ARCHIVE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
MA=chpc/results/archive/row19_screen_v20_before_v21
ls -d chpc/results/archive/.row19_screen_v20_before_v21.staging* >/dev/null 2>&1 \
  && fail "an interrupted Mac archive build left chpc/results/archive/.row19_screen_v20_before_v21.staging*; inspect it by hand"
python3 chpc/migration_v21/v21_package.py drain || fail "the Mac drain is not observed (above)"
if [ -e $MA ] || [ -L $MA ]; then
  python3 chpc/migration_v21/mac_archive.py verify || fail "$MA exists but does not verify as the complete v20 archive; not overwriting (inspect by hand)"
  MAC_DONE=1
else
  python3 chpc/migration_v21/v21_package.py preflight || fail "the Mac tree is not the adopted v20 state of step 1 (above)"
  MAC_DONE=0
fi
if [ "$DRY" = "--dry-run" ]; then
  echo "DRY RUN - Mac checks pass; would:"
  echo "  - Lengau: verify the sources (lengau_archive.py inventory), then stage, verify and publish \$T/archive_screen/v20_before_v21 with COMPLETE (or verify an existing one)"
  [ $MAC_DONE = 1 ] && echo "  - Mac: $MA exists and verifies; left as it is" || echo "  - Mac: stage, verify and publish $MA (8 members + SHA256SUMS + COMPLETE), read-only"
  exit 0
fi
. chpc/migration_v21/lengau.sh || fail "cannot load chpc/migration_v21/lengau.sh"
echo "== a. Lengau"
OUTF=$(mktemp -t v21_archive) || fail "mktemp failed"
to_lengau - > "$OUTF" 2>&1 <<'REMOTE'
if [ -e "$A" ] || [ -L "$A" ]; then
  archive_py verify "$T" || die "archive exists and does not verify as complete, not overwriting: $A"
  echo "archive exists and verifies, left as it is"
  echo "== SHA256SUMS"; cat "$A/SHA256SUMS" || die "cannot read the archive's SHA256SUMS"; echo "== end SHA256SUMS"; exit 0
fi
! ls -d "$PS"/.v20_before_v21.staging* >/dev/null 2>&1 \
  || die "an interrupted archive build left $PS/.v20_before_v21.staging*; partial evidence kept, inspect and recover it by hand"
drained
locks_free
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"; src_file "$G/review_refit.json" "$GS" "active gate review"
dst_dir "$PS" "$T" "archive parent"; dst_absent "$A" "$PS" "archive"
v20_current
pin "$G/qualified_refit_job1.json" $V20_QUAL "gate qualification"
act3_valid
node_ev
head=$(cd -- "$C" && git rev-parse --verify HEAD) || die "git rev-parse HEAD failed in the controller clone"
archive_py build "$T" "$head" || die "the archive build refused or failed (above); nothing was published"
archive_py verify "$T" || die "the published archive does not verify (above)"
echo "== SHA256SUMS"; cat "$A/SHA256SUMS" || die "cannot read the archive's SHA256SUMS"; echo "== end SHA256SUMS"
REMOTE
rc=$?
OUT=$(cat "$OUTF") || fail "cannot read the Lengau output"
rm -f "$OUTF"
printf '%s\n' "$OUT"
[ $rc = 0 ] || fail "the Lengau archive failed (exit $rc, above); the Mac archive was not written"
LSUMS=$(printf '%s\n' "$OUT" | sed -n 's/^sha256sums=\([0-9a-f]\{64\}\)$/\1/p' | tail -1)
LBUDGET=$(printf '%s\n' "$OUT" | sed -n 's/^budget=\([0-9a-f]\{64\}\)$/\1/p' | tail -1)
[ ${#LSUMS} = 64 ] && [ ${#LBUDGET} = 64 ] || fail "the Lengau half did not report its verified SHA256SUMS and budget digests"
LS_FILE=chpc/results/archive/row19_screen_v20_before_v21.lengau_SHA256SUMS.txt
LS_TMP=$(mktemp -t v21_lsums) || fail "mktemp failed"
printf '%s\n' "$OUT" | sed -n '/^== SHA256SUMS$/,/^== end SHA256SUMS$/p' | sed '1d;$d' > "$LS_TMP" || fail "cannot extract the Lengau SHA256SUMS"
[ "$(shasum -a 256 "$LS_TMP" | cut -c1-64)" = "$LSUMS" ] || { rm -f "$LS_TMP"; fail "the Lengau SHA256SUMS text received is not the certified ${LSUMS:0:16}"; }
echo "== b. Mac"
if [ $MAC_DONE = 1 ]; then
  rec=$(python3 chpc/migration_v21/mac_archive.py verify --get lengau_sha256sums) || { rm -f "$LS_TMP"; fail "the Mac archive no longer verifies"; }
  [ "$rec" = "$LSUMS" ] || { rm -f "$LS_TMP"; fail "the Mac archive was made with another Lengau archive (${rec:0:16}), not this one (${LSUMS:0:16})"; }
  echo "Mac archive exists, verifies and names this Lengau archive; left as it is"
else
  python3 chpc/migration_v21/mac_archive.py build "$LSUMS" "$LBUDGET" || { rm -f "$LS_TMP"; fail "the Mac archive build refused or failed (above)"; }
fi
if [ -e $LS_FILE ] || [ -L $LS_FILE ]; then
  [ -f $LS_FILE ] && [ ! -L $LS_FILE ] && cmp -s "$LS_TMP" $LS_FILE || { rm -f "$LS_TMP"; fail "$LS_FILE exists with other bytes; not overwriting (inspect by hand)"; }
  rm -f "$LS_TMP"
else
  mkdir -p chpc/results/archive && cp "$LS_TMP" $LS_FILE.tmp.$$ && chmod a-w $LS_FILE.tmp.$$ && mv $LS_FILE.tmp.$$ $LS_FILE \
    || { rm -f "$LS_TMP"; fail "cannot write $LS_FILE"; }
  rm -f "$LS_TMP"
  echo "kept the Lengau SHA256SUMS on the Mac: $LS_FILE (${LSUMS:0:16})"
fi
echo "ARCHIVE OK - commit the Mac archive and $LS_FILE with explicit paths together with the promotion (step 3)"
