#!/bin/bash
# Migration v15 -> v16, step 4 (Mac -> Lengau): deploy the promoted and COMMITTED v16 controls, admission, status, the designated
# declaration, the adoption record and the review record into the CONTROLLER clone rsc_screen_ctl (one commit), as deploy_v15.sh
# did. The job clone rsc_screen is not touched; its science bytes are verified unchanged. Then the controls/lineage/authority
# checks the admission uses, the designated-declaration check, and a local-vs-remote comparison of every pinned file.
# Requires: Mac chpc/ promoted (controls 01976b6a, version-16 adoption) and committed; Lengau archive_screen/v15_before_v16
# (archive_v15.sh). Re-run safe: a controller clone already at exactly these bytes is reported and only the checks run.
# Usage (from workspace_demo/t1_access): bash chpc/migration_v16/deploy_v16.sh [--dry-run]
#   --dry-run   the Mac checks and the local file list only: no ssh, nothing copied.
# Test hook: V16_FAKE_LENGAU=<dir containing FAKE_LENGAU> runs the Lengau half locally against that fake toolchain.
set -u
DRY=${1:-}
fail() { echo "DEPLOY REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
REC=reviews/2026-10-17_v16_p80_codex_review.md
[ "$(shasum -a 256 chpc/row19_screen_controls.json | cut -c1-64)" = 01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220 ] || fail "Mac chpc/ is not promoted to v16 (promote_v16.py)"
python3 -c 'import json, sys; a = json.load(open("chpc/row19_screen_controls_adoption.json")); sys.exit(0 if a.get("version") == 16 and a.get("controls_sha256") == "01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220" else 1)' \
  || fail "the Mac adoption record is not the version-16 record (promote_v16.py)"
CHANGED="chpc/row19_screen_status.py chpc/row19_screen_admit.py chpc/row19_screen_designated.json chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json $REC"
for f in $CHANGED; do git ls-files --error-unmatch -- $f >/dev/null 2>&1 && git diff --quiet HEAD -- $f || fail "$f is not committed (commit the promotion first; only committed bytes are deployed)"; done
ALL=$(python3 -c 'import json; v = json.load(open("chpc/row19_screen_controls.json"))["versions"][-1]; print(" ".join(sorted(v["files"])))')
ALL="$ALL chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_partition_e1.json $REC"
python3 -c 'import sys; sys.path.insert(0, "chpc"); import programme_gate as PG, row19_screen_admit as A; import json
m = json.load(open("chpc/row19_screen_manifest.json")); w = [PG.controls_authority_problem(), PG.lineage_problem(), A.controls_problem(), A.designated(m, "chpc/row19_screen_manifest.json")[1]]
print("mac authority", repr(w[0]), "lineage", repr(w[1]), "controls", repr(w[2]), "designated", repr(w[3])); sys.exit(1 if any(w) else 0)' || fail "the Mac promoted tree does not pass its own checks (above)"
LOCAL=$(mktemp -t v16_local); REMOTE_OUT=$(mktemp -t v16_remote)
shasum -a 256 $ALL | sort -k2 > $LOCAL
echo "== local ($(wc -l < $LOCAL | tr -d ' ') files; copied: $CHANGED)"; cut -c1-12,65- $LOCAL
[ "$DRY" = "--dry-run" ] && { echo "DRY RUN: nothing copied"; exit 0; }
O="-o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes"
if [ -n "${V16_FAKE_LENGAU:-}" ]; then
  [ -e "$V16_FAKE_LENGAU/FAKE_LENGAU" ] || fail "V16_FAKE_LENGAU has no FAKE_LENGAU marker"
  put() { cp "$1" "$V16_FAKE_LENGAU/patches/$2"; }
  remote() { env V16_T="$V16_FAKE_LENGAU" CHANGED="$CHANGED" ALL="$ALL" bash -s; }
else
  put() { scp $O -q "$1" "lengau:/mnt/lustre/users/pvanrooyen/t1_toolchain/patches/$2"; }
  remote() { ssh $O lengau "CHANGED='$CHANGED' ALL='$ALL' bash -s"; }
fi
for f in $CHANGED; do put "$f" "ctl16.$(echo $f | tr / _)" || fail "copy $f to patches/"; done
remote <<'REMOTE' > $REMOTE_OUT 2>&1
if [ -n "${V16_T:-}" ]; then [ -e "$V16_T/FAKE_LENGAU" ] || { echo "V16_T is a test hook and needs a FAKE_LENGAU marker"; exit 1; }; T=$V16_T; else T=/mnt/lustre/users/pvanrooyen/t1_toolchain; fi
C=$T/rsc_screen_ctl/workspace_demo/t1_access; J=$T/rsc_screen/workspace_demo/t1_access
[ -e $T/archive_screen/v15_before_v16/SHA256SUMS ] || { echo "ABORT: v15 archive missing (archive_v15.sh first)"; exit 1; }
cd $C || exit 1
[ -z "$(git status --short)" ] || { echo "ABORT: controller clone not clean"; exit 1; }
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition" | grep -v grep)
[ -n "$p" ] && { echo "ABORT: controller command running on the login node:"; echo "$p"; exit 1; }
same=1; for f in $CHANGED; do cmp -s $T/patches/ctl16.$(echo $f | tr / _) $f || same=0; done
if [ $same = 1 ]; then
  echo "controller clone already holds exactly these v16 bytes; no commit"
else
  [ "$(sha256sum chpc/row19_screen_controls.json | cut -c1-64)" = 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5 ] || { echo "ABORT: controller clone controls are not adopted v15"; exit 1; }
  [ ! -e chpc/row19_screen_designated.json ] || { echo "ABORT: controller clone already has a designated declaration"; exit 1; }
  SCI="chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py chpc/row19_ledger.py chpc/row19_slice.py chpc/row19_screen_orig.py"
  (cd $J && sha256sum $SCI > $T/patches/sci16_before.txt)
  for f in $CHANGED; do mkdir -p $(dirname $f); cp $T/patches/ctl16.$(echo $f | tr / _) $f || exit 1; done
  git add $CHANGED && git -c user.name=R052 -c user.email=r052@local commit -q -m 'screen controllers: lineage version 16 (admission + status REVISION 16 and the designated-coordinates declaration: the resized screen S x 0..79; RSC 3686a11, review f6896e1); every other controller byte and the epoch-1 partition unchanged' -- $CHANGED || exit 1
  (cd $J && sha256sum $SCI > $T/patches/sci16_after.txt); cmp -s $T/patches/sci16_before.txt $T/patches/sci16_after.txt && echo "science bytes UNCHANGED" || echo "ABORT: science bytes changed"
fi
git log -1 --format='ctl %h'; git status --short | head -3
echo "== remote"; sha256sum $ALL | sort -k2
echo "== end remote"
$T/t1py -c 'import sys; sys.path.insert(0,"chpc"); import programme_gate as PG, row19_screen_admit as A; print("authority", repr(PG.controls_authority_problem()), "lineage", repr(PG.lineage_problem()), "controls", repr(A.controls_problem()))'
$T/t1py -c 'import sys; sys.path.insert(0,"chpc"); import json, row19_screen_admit as A; m=json.load(open("chpc/row19_screen_manifest.json")); print("designated", repr(A.designated(m, "chpc/row19_screen_manifest.json")[1]))'
REMOTE
rc=$?
cat $REMOTE_OUT
[ $rc = 0 ] || fail "the Lengau half exited $rc (above)"
echo "== local vs remote"; diff <(awk '{print $1, $2}' $LOCAL) <(sed -n '/^== remote/,/^== end remote/p' $REMOTE_OUT | grep -E '^[0-9a-f]{64} ' | awk '{print $1, $2}') && echo IDENTICAL || fail "the controller clone differs from the Mac (above)"
grep -q "^authority '' lineage '' controls ''$" $REMOTE_OUT && grep -q "^designated ''$" $REMOTE_OUT || fail "a remote authority/lineage/controls/designated problem is not empty (above)"
grep -q "ABORT" $REMOTE_OUT && fail "the remote half printed an ABORT (above)"
echo "DEPLOY OK - v16 in rsc_screen_ctl; do NOT re-activate e1 (v16 pins the same partition)"
