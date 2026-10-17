#!/bin/bash
# Migration v15 -> v16, step 4 (Mac -> Lengau): deploy the promoted and COMMITTED v16 controls, admission, status, the designated
# declaration, the adoption record and the review record into the CONTROLLER clone rsc_screen_ctl (one commit), as deploy_v15.sh
# did. The six files travel inside the one Lengau script (lengau.sh payload, each checked against its Mac SHA-256); nothing is
# staged in patches/. The job clone rsc_screen is never written.
# Mac, before anything leaves: promote_v16.py --check (full authority + the complete Mac archive certificate + the exact
# version-16 adoption), the six files committed, the Mac tree's own authority/lineage/controls/designated checks empty.
# Lengau, IMMEDIATELY before the controller mutation: the drain observed (checked process inventory, both locks probed free),
# the Lengau archive's complete certificate (lengau_archive.py verify) and that it is the archive the Mac archive names, the
# controller clone clean at the v15 bytes AND at the archived HEAD, the gate qualification and active review equal to the
# archived ones, and a COMPLETE before-manifest of the job clone's fixed science inventory (every file read, every digest
# command checked). After the commit: a complete after-manifest identical to the before-manifest, a clean clone, the
# controls/lineage/authority and designated checks, and a local-vs-remote comparison of every pinned file. Any failed or
# incomplete observation refuses (exit 3).
# Re-run safe: a controller clone already at exactly these bytes is reported (after the archive check) and only the checks run.
# An interrupted copy/commit leaves a dirty clone, which every re-run refuses: report it and recover it explicitly.
# Usage (from workspace_demo/t1_access): bash chpc/migration_v16/deploy_v16.sh [--dry-run]
#   --dry-run   the Mac checks and the local file list only: no ssh, nothing copied.
# Production route only (lengau.sh); tests run private copies (test_migration_v16.py).
set -u -o pipefail
DRY=${1:-}
fail() { echo "DEPLOY REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
REC=reviews/2026-10-17_v16_p80_codex_review.md
python3 chpc/migration_v16/promote_v16.py --check || fail "the Mac promotion is not complete and verified (promote_v16.py --check, above)"
LSUMS=$(python3 chpc/migration_v16/mac_archive.py verify --get lengau_sha256sums) || fail "the Mac archive does not verify"
CHANGED="chpc/row19_screen_status.py chpc/row19_screen_admit.py chpc/row19_screen_designated.json chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json $REC"
for f in $CHANGED; do git ls-files --error-unmatch -- $f >/dev/null 2>&1 && git diff --quiet HEAD -- $f || fail "$f is not committed (commit the promotion first; only committed bytes are deployed)"; done
ALL=$(python3 -c 'import json; v = json.load(open("chpc/row19_screen_controls.json"))["versions"][-1]; print(" ".join(sorted(v["files"])))') || fail "cannot read the v16 pins"
ALL="$ALL chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_partition_e1.json $REC"
python3 -c 'import sys; sys.path.insert(0, "chpc"); import programme_gate as PG, row19_screen_admit as A; import json
m = json.load(open("chpc/row19_screen_manifest.json")); w = [PG.controls_authority_problem(), PG.lineage_problem(), A.controls_problem(), A.designated(m, "chpc/row19_screen_manifest.json")[1]]
print("mac authority", repr(w[0]), "lineage", repr(w[1]), "controls", repr(w[2]), "designated", repr(w[3])); sys.exit(1 if any(w) else 0)' || fail "the Mac promoted tree does not pass its own checks (above)"
LOCAL=$(mktemp -t v16_local) && REMOTE_OUT=$(mktemp -t v16_remote) || fail "mktemp failed"
shasum -a 256 $ALL | sort -k2 > $LOCAL || fail "cannot hash the local pinned files"
[ "$(wc -l < $LOCAL | tr -d ' ')" = "$(echo $ALL | wc -w | tr -d ' ')" ] || fail "the local digest list is incomplete"
echo "== local ($(wc -l < $LOCAL | tr -d ' ') files; copied: $CHANGED)"; cut -c1-12,65- $LOCAL
[ "$DRY" = "--dry-run" ] && { echo "DRY RUN: nothing copied"; exit 0; }
. chpc/migration_v16/lengau.sh || fail "cannot load chpc/migration_v16/lengau.sh"
FILES=(); for f in $CHANGED; do FILES+=(--file "$f"); done
to_lengau - "${FILES[@]}" --var "ALL=$ALL" --var "LSUMS=$LSUMS" > $REMOTE_OUT 2>&1 <<'REMOTE'
[ "$NP" = 6 ] || die "expected six payload files, got $NP"
cd "$C" || die "no controller clone $C"
drained
locks_free
archive_py verify "$T" || die "the v15 archive does not verify as complete (archive_v15.sh first; never deploy without it)"
lsums=$(archive_py verify "$T" --get sha256sums) || die "archive verify failed"
[ "$lsums" = "$LSUMS" ] || die "the Lengau archive (${lsums:0:16}) is not the one the Mac archive names (${LSUMS:0:16})"
git_clean "$C"
TMPD=$(mktemp -d) || die "mktemp failed"
same=1; i=1
while [ $i -le $NP ]; do
  eval "f=\$P${i}_PATH"
  payload $i "$TMPD/$i"
  cmp -s "$TMPD/$i" "$f" || same=0
  i=$((i + 1))
done
if [ $same = 1 ]; then
  echo "controller clone already holds exactly these v16 bytes; no commit"
else
  pin chpc/row19_screen_controls.json $V15_CONTROLS "controller clone controls (adopted v15)"
  pin chpc/row19_screen_controls_adoption.json $V15_ADOPTION "controller clone adoption (v15 record)"
  pin chpc/row19_screen_admit.py $V15_ADMIT "controller clone admission (v15)"
  pin chpc/row19_screen_status.py $V15_STATUS "controller clone status (v15)"
  [ ! -e chpc/row19_screen_designated.json ] || die "controller clone already has a designated declaration"
  head=$(git rev-parse --verify HEAD) || die "git rev-parse HEAD failed"
  ahead=$(archive_py verify "$T" --get ctl_head) || die "archive verify failed"
  [ "$head" = "$ahead" ] || die "controller clone HEAD ${head:0:12} is not the archived v15 HEAD ${ahead:0:12}"
  pin "$G/qualified_refit_job1.json" "$(archive_py verify "$T" --get qualification)" "gate qualification (archived)"
  pin "$G/review_refit.json" "$(archive_py verify "$T" --get review)" "active gate review (archived)"
  before=$(sci_manifest) || { printf '%s\n' "$before"; die "the job-clone science before-proof is incomplete; nothing was changed"; }
  i=1; LIST=""
  while [ $i -le $NP ]; do
    eval "f=\$P${i}_PATH"
    mkdir -p "$(dirname "$f")" || die "mkdir for $f failed"
    cp "$TMPD/$i" "$f.v16tmp" && mv "$f.v16tmp" "$f" || die "copy of $f failed (the clone is now dirty: recover explicitly)"
    [ "$(h "$f")" = "$(h "$TMPD/$i")" ] || die "$f did not land intact (the clone is now dirty: recover explicitly)"
    LIST="$LIST $f"; i=$((i + 1))
  done
  git add -- $LIST || die "git add failed (the clone is now dirty: recover explicitly)"
  git -c user.name=R052 -c user.email=r052@local commit -q -m 'screen controllers: lineage version 16 (admission + status REVISION 16 and the designated-coordinates declaration: the resized screen S x 0..79; RSC 3686a11, review f6896e1); every other controller byte and the epoch-1 partition unchanged' -- $LIST \
    || die "git commit failed (the clone is now dirty: recover explicitly)"
  after=$(sci_manifest) || { printf '%s\n' "$after"; die "the job-clone science after-proof is incomplete; completion refused"; }
  [ "$before" = "$after" ] || die "science bytes changed during the deployment; completion refused"
  echo "science bytes UNCHANGED ($(printf '%s\n' "$after" | wc -l | tr -d ' ') files, complete before and after manifests identical)"
fi
rm -rf "$TMPD"
git_clean "$C"
git log -1 --format='ctl %h' || die "git log failed"
echo "== remote"; sha256sum -- $ALL | sort -k2 || die "remote digest of the pinned files failed"
echo "== end remote"
"$T/t1py" -c 'import sys; sys.path.insert(0,"chpc"); import programme_gate as PG, row19_screen_admit as A; print("authority", repr(PG.controls_authority_problem()), "lineage", repr(PG.lineage_problem()), "controls", repr(A.controls_problem()))' || die "the authority check did not run"
"$T/t1py" -c 'import sys; sys.path.insert(0,"chpc"); import json, row19_screen_admit as A; m=json.load(open("chpc/row19_screen_manifest.json")); print("designated", repr(A.designated(m, "chpc/row19_screen_manifest.json")[1]))' || die "the designated check did not run"
echo "lengau deploy body complete"
REMOTE
rc=$?
cat $REMOTE_OUT
[ $rc = 0 ] || fail "the Lengau half exited $rc (above)"
grep -q "ABORT" $REMOTE_OUT && fail "the remote half printed an ABORT (above)"
grep -qx "lengau deploy body complete" $REMOTE_OUT || fail "the remote half did not complete"
echo "== local vs remote"; diff <(awk '{print $1, $2}' $LOCAL) <(sed -n '/^== remote/,/^== end remote/p' $REMOTE_OUT | grep -E '^[0-9a-f]{64} ' | awk '{print $1, $2}') && echo IDENTICAL || fail "the controller clone differs from the Mac (above)"
grep -q "^authority '' lineage '' controls ''$" $REMOTE_OUT && grep -q "^designated ''$" $REMOTE_OUT || fail "a remote authority/lineage/controls/designated problem is not empty (above)"
rm -f $LOCAL $REMOTE_OUT
echo "DEPLOY OK - v16 in rsc_screen_ctl; do NOT re-activate e1 (v16 pins the same partition)"
