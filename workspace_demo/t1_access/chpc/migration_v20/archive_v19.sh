#!/bin/bash
# Migration v19 -> v20, step 2 (Mac -> Lengau, then Mac): immutable archives of the ACTUALLY ADOPTED v19 state BEFORE anything
# changes (the archive_v16.sh pattern). Each archive has a fixed mandatory inventory, is built in a staging directory, verified in
# full (every digest AND the exact inventory) and only then published by one atomic rename with a COMPLETE certificate.
#  a. Lengau $T/archive_screen/v19_before_v20 (lengau_archive.py): ctl/HEAD.txt; ctl/<path> for EVERY file the adopted v19 entry
#     pins plus its partition e2 (48cea639), the e1 declaration (provenance), the v19 controls, adoption, admission, status,
#     designated declaration, budget phases, screen manifest, the two row-22 bank controllers, the v19 controls record and the
#     v19 pilot record; ctl/untracked/<path> for the three pinned untracked evidence files; the WHOLE gate
#     (qualified_refit_job1.json e123d6e5, the active review_refit.json, scaleup_refit_v16.json when present, every receipt and
#     PBS copy) with INVENTORY.gate; jobs/row19_screen_refit_* with INVENTORY.jobs, which MUST retain the captured node
#     document row19_screen_refit_54.nodefail.json at 730ea262; the ledger reference copy; both activation proofs
#     ec2/activation_e1.json and ec2/activation_e2.json; SHA256SUMS; COMPLETE (with the budget and node-evidence digests).
#     Refuses unless the drain is observed (checked process inventory, both locks probed free), the controller clone is clean
#     (ctl_clean) at the v19 controls and adoption, the gate qualification is e123d6e5, a review is active, epoch 2 is the
#     canonical activation and the node document is in place.
#  b. Mac chpc/results/archive/row19_screen_v19_before_v20/ (mac_archive.py): EXACTLY the 9 members of build_v20.ARCHIVE with
#     SHA256SUMS and the JSON COMPLETE (which records the Lengau archive's SHA256SUMS digest). The Mac budget phases must be the
#     bytes the Lengau archive certifies. promote_v20.py (build_v20.archive_problems) and deploy_v20.sh require it by name.
# Re-run: an existing archive is accepted only if its complete certificate verifies; an existing one that does not, or a staging
# directory left by an interrupted build, REFUSES and is left exactly as it is (inspect and recover by hand). If the Lengau half
# fails, the Mac half is not written; if the Mac half fails after the Lengau archive was published, a re-run verifies the Lengau
# archive and builds the Mac half.
# Usage (from workspace_demo/t1_access): bash chpc/migration_v20/archive_v19.sh [--dry-run]
#   --dry-run   the Mac checks and the plan only: no ssh, nothing written.
# Production route only (lengau.sh); tests run private copies (test_migration_v20.py).
set -u -o pipefail
DRY=${1:-}
case $DRY in ""|--dry-run) ;; *) echo "ARCHIVE REFUSED: unknown argument $DRY"; exit 3;; esac
fail() { echo "ARCHIVE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
MA=chpc/results/archive/row19_screen_v19_before_v20
ls -d chpc/results/archive/.row19_screen_v19_before_v20.staging* >/dev/null 2>&1 \
  && fail "an interrupted Mac archive build left chpc/results/archive/.row19_screen_v19_before_v20.staging*; partial evidence kept, inspect it by hand"
python3 chpc/migration_v20/v20_package.py drain || fail "the Mac drain is not observed (above)"
if [ -e $MA ] || [ -L $MA ]; then
  python3 chpc/migration_v20/mac_archive.py verify || fail "$MA exists but does not verify as the complete v19 archive; not overwriting (inspect by hand)"
  MAC_DONE=1
else
  python3 chpc/migration_v20/v20_package.py preflight || fail "the Mac tree is not the adopted v19 state of step 1 (above)"
  MAC_DONE=0
fi
if [ "$DRY" = "--dry-run" ]; then
  echo "DRY RUN - Mac checks pass; would:"
  echo "  - Lengau: verify the sources (lengau_archive.py inventory), then stage, verify and publish \$T/archive_screen/v19_before_v20 with COMPLETE (or verify an existing one)"
  [ $MAC_DONE = 1 ] && echo "  - Mac: $MA exists and verifies; left as it is" || echo "  - Mac: stage, verify and publish $MA (9 members + SHA256SUMS + COMPLETE), read-only"
  exit 0
fi
. chpc/migration_v20/lengau.sh || fail "cannot load chpc/migration_v20/lengau.sh"
echo "== a. Lengau"
OUTF=$(mktemp -t v20_archive) || fail "mktemp failed"
to_lengau - > "$OUTF" 2>&1 <<'REMOTE'
if [ -e "$A" ] || [ -L "$A" ]; then
  archive_py verify "$T" || die "archive exists and does not verify as complete, not overwriting: $A"
  echo "archive exists and verifies, left as it is"
  echo "== SHA256SUMS"; cat "$A/SHA256SUMS" || die "cannot read the archive's SHA256SUMS"; echo "== end SHA256SUMS"; exit 0
fi
! ls -d "$PS"/.v19_before_v20.staging* >/dev/null 2>&1 \
  || die "an interrupted archive build left $PS/.v19_before_v20.staging*; partial evidence kept, inspect and recover it by hand"
drained
locks_free
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"; src_file "$G/review_refit.json" "$GS" "active gate review"
dst_dir "$PS" "$T" "archive parent"; dst_absent "$A" "$PS" "archive"
v19_current
pin "$G/qualified_refit_job1.json" $V19_QUAL "gate qualification"
act2_valid
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
# the Lengau archive's complete SHA256SUMS, kept on the Mac beside the Mac archive (committed with it in step 3; packaged with the
# new pilot qualification in step 8.3): exactly the bytes whose digest the Lengau certificate and the Mac COMPLETE name
LS_FILE=chpc/results/archive/row19_screen_v19_before_v20.lengau_SHA256SUMS.txt
LS_TMP=$(mktemp -t v20_lsums) || fail "mktemp failed"
printf '%s\n' "$OUT" | sed -n '/^== SHA256SUMS$/,/^== end SHA256SUMS$/p' | sed '1d;$d' > "$LS_TMP" || fail "cannot extract the Lengau SHA256SUMS"
[ "$(shasum -a 256 "$LS_TMP" | cut -c1-64)" = "$LSUMS" ] || { rm -f "$LS_TMP"; fail "the Lengau SHA256SUMS text received is not the certified ${LSUMS:0:16}"; }
echo "== b. Mac"
if [ $MAC_DONE = 1 ]; then
  rec=$(python3 chpc/migration_v20/mac_archive.py verify --get lengau_sha256sums) || { rm -f "$LS_TMP"; fail "the Mac archive no longer verifies"; }
  [ "$rec" = "$LSUMS" ] || { rm -f "$LS_TMP"; fail "the Mac archive was made with another Lengau archive (${rec:0:16}), not this one (${LSUMS:0:16})"; }
  echo "Mac archive exists, verifies and names this Lengau archive; left as it is"
else
  python3 chpc/migration_v20/mac_archive.py build "$LSUMS" "$LBUDGET" || { rm -f "$LS_TMP"; fail "the Mac archive build refused or failed (above)"; }
fi
# only after the Mac archive names this Lengau archive is its SHA256SUMS kept on the Mac (a failed Mac half leaves nothing there)
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
