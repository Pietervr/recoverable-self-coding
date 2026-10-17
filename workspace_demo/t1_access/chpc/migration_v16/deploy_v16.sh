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
# command checked). Every payload destination, its temporary sibling and parent, the controller/gate authority and the
# proof directory must be its own physical path in its canonical scope and outside the scientific clone (remote_lib.sh
# containment), checked first and again immediately before each copy. Before the first controller write the DEPLOY PROOF
# $T/archive_screen/v16_deploy_proof/ is written (science_before.sha256 = the complete pre-mutation manifest; intent =
# schema, controller HEAD before, payload digest, manifest digest; read-only). After the commit: a complete after-manifest
# identical to the before-manifest, then DONE (both HEADs, payload, before = after) is written; a failed after-proof is kept
# as after_failed.* and DONE is not written. Then a clean clone, the controls/lineage/authority and designated checks, and a
# local-vs-remote comparison of every pinned file. Any failed or incomplete observation refuses (exit 3).
# Re-run: a controller clone already at exactly these bytes reports DEPLOY OK ONLY with the proof's DONE binding this payload,
# the deployed commit in HEAD's history and the CURRENT eight science files equal to the preserved pre-mutation manifest;
# otherwise it is an explicit DEPLOY HELD pending verified recovery (never a rewrite of the job clone, never a fit). An
# attempt that wrote its proof but changed nothing (clean clone at the recorded HEAD, same payload, same science) resumes on
# that proof. An interrupted copy/commit leaves a dirty clone, which every re-run refuses: report it and recover it explicitly.
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
ctl_git
PS=$T/archive_screen
PSCHEMA=row19-screen-v16-deploy-proof-1
hold() { die "DEPLOY HELD pending verified recovery (the scientific clone is never rewritten and no fit is rerun to resolve it): $*"; }
dests() {   # containment of every payload destination and its temporary sibling (repeated immediately before each copy)
  local i=1 f
  while [ $i -le $NP ]; do
    eval "f=\$P${i}_PATH"
    clean_rel "$f" || die "payload path $f is not a plain relative path"
    not_evidence "$f" "payload $i"
    dst_file "$C/$f" "$CR" "payload $i destination"
    dst_absent "$C/$f.v16tmp" "$CR" "payload $i temporary sibling"
    i=$((i + 1))
  done
  for f in $ALL; do clean_rel "$f" || die "pinned path $f is not a plain relative path"; done
  dst_dir "$PROOF" "$PS" "deploy proof"
}
pkey() { sed -n "s/^$2 \([0-9a-f]*\)\$/\1/p" "$1"; }
proof_intent() {   # the durable pre-mutation record: sets IB_HEAD IB_PAY IB_SCI, or holds
  [ -d "$PROOF" ] && [ ! -L "$PROOF" ] || hold "no deploy proof $PROOF (the science before/after proof of the deployment is missing)"
  scoped "$PROOF" "$PS" "deploy proof"
  [ -f "$PROOF/intent" ] && [ ! -L "$PROOF/intent" ] || hold "the deploy proof has no complete intent record (an interrupted proof write; evidence kept)"
  src_file "$PROOF/intent" "$PS" "deploy proof intent"; src_file "$PROOF/science_before.sha256" "$PS" "preserved pre-mutation manifest"
  grep -qx "schema $PSCHEMA" "$PROOF/intent" || hold "the deploy proof intent has another schema"
  IB_HEAD=$(pkey "$PROOF/intent" ctl_head_before); IB_PAY=$(pkey "$PROOF/intent" payload); IB_SCI=$(pkey "$PROOF/intent" science_before)
  [ ${#IB_HEAD} = 40 ] && [ ${#IB_PAY} = 64 ] && [ ${#IB_SCI} = 64 ] || hold "the deploy proof intent is malformed"
  [ "$(h "$PROOF/science_before.sha256")" = "$IB_SCI" ] || hold "the preserved pre-mutation manifest is not the one its intent record certifies"
}
put() {   # put <dir> <name> <text>: a new read-only file, written beside itself and renamed into place
  dst_absent "$1/$2" "$PS" "deploy proof $2"; dst_absent "$1/.$2.tmp" "$PS" "deploy proof $2 temporary"
  printf '%s\n' "$3" > "$1/.$2.tmp" && mv -- "$1/.$2.tmp" "$1/$2" && chmod a-w "$1/$2" || die "cannot write the deploy proof $1/$2"
}
record_fail() {   # keep the failed after-proof as evidence beside the pre-mutation record
  local n; n=after_failed.$(date -u +%Y%m%dT%H%M%SZ).$$
  put "$PROOF" "$n" "$(printf 'schema %s\nreason %s\n--- after ---\n%s' "$PSCHEMA" "$1" "$2")"
}
dests
drained
locks_free
archive_py verify "$T" || die "the v15 archive does not verify as complete (archive_v15.sh first; never deploy without it)"
lsums=$(archive_py verify "$T" --get sha256sums) || die "archive verify failed"
[ "$lsums" = "$LSUMS" ] || die "the Lengau archive (${lsums:0:16}) is not the one the Mac archive names (${LSUMS:0:16})"
ctl_clean
TMPD=$(mktemp -d) || die "mktemp failed"
same=1; i=1; : > "$TMPD/payload.sums" || die "mktemp failed"
while [ $i -le $NP ]; do
  eval "f=\$P${i}_PATH"
  payload $i "$TMPD/$i"
  printf '%s  ./%s\n' "$(h "$TMPD/$i")" "$f" >> "$TMPD/payload.sums" || die "cannot list the payload digests"
  cmp -s "$TMPD/$i" "$f" || same=0
  i=$((i + 1))
done
paysha=$(h "$TMPD/payload.sums") || die "cannot hash the payload digest list"
head=$(git rev-parse --verify HEAD) || die "git rev-parse HEAD failed"
if [ $same = 1 ]; then
  echo "controller clone already holds exactly these v16 bytes; no commit"
  # a re-run is complete ONLY with the durable, complete before/after proof of the deployment that put these bytes here, and
  # only if the science bytes NOW equal the preserved pre-mutation manifest; anything else is an explicit hold
  proof_intent
  [ "$IB_PAY" = "$paysha" ] || hold "the deploy proof records another payload (${IB_PAY:0:16}, not ${paysha:0:16})"
  if [ ! -e "$PROOF/DONE" ] && [ ! -L "$PROOF/DONE" ]; then
    if cur=$(sci_manifest) && [ "$cur" = "$(cat "$PROOF/science_before.sha256")" ]; then
      st="the current science bytes do equal the preserved pre-mutation manifest"
    else
      st="the current science bytes are NOT the preserved pre-mutation manifest (or cannot be read completely)"
    fi
    hold "the earlier deployment's science after-proof is unresolved (no DONE in $PROOF; $st)"
  fi
  src_file "$PROOF/DONE" "$PS" "deploy proof DONE"
  grep -qx "schema $PSCHEMA" "$PROOF/DONE" || hold "the deploy proof DONE has another schema"
  dh=$(pkey "$PROOF/DONE" ctl_head_after)
  [ "$(pkey "$PROOF/DONE" ctl_head_before)" = "$IB_HEAD" ] && [ "$(pkey "$PROOF/DONE" payload)" = "$paysha" ] \
    && [ "$(pkey "$PROOF/DONE" science_before)" = "$IB_SCI" ] && [ "$(pkey "$PROOF/DONE" science_after)" = "$IB_SCI" ] && [ ${#dh} = 40 ] \
    || hold "the deploy proof DONE does not bind this payload, the recorded HEADs and an identical before/after manifest"
  git merge-base --is-ancestor "$dh" HEAD || hold "the controller HEAD ${head:0:12} does not contain the proved deployment commit ${dh:0:12}"
  cur=$(sci_manifest) || { printf '%s\n' "$cur"; hold "the current science proof is incomplete"; }
  [ "$cur" = "$(cat "$PROOF/science_before.sha256")" ] || hold "the current science bytes differ from the preserved pre-mutation manifest"
  echo "science bytes UNCHANGED ($(printf '%s\n' "$cur" | wc -l | tr -d ' ') files, current manifest equals the preserved pre-mutation manifest; deploy proof DONE at ctl ${dh:0:12})"
else
  for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_admit.py chpc/row19_screen_status.py; do
    src_file "$C/$f" "$CR" "controller authority $f"
  done
  pin chpc/row19_screen_controls.json $V15_CONTROLS "controller clone controls (adopted v15)"
  pin chpc/row19_screen_controls_adoption.json $V15_ADOPTION "controller clone adoption (v15 record)"
  pin chpc/row19_screen_admit.py $V15_ADMIT "controller clone admission (v15)"
  pin chpc/row19_screen_status.py $V15_STATUS "controller clone status (v15)"
  [ ! -e chpc/row19_screen_designated.json ] && [ ! -L chpc/row19_screen_designated.json ] || die "controller clone already has a designated declaration"
  ahead=$(archive_py verify "$T" --get ctl_head) || die "archive verify failed"
  [ "$head" = "$ahead" ] || die "controller clone HEAD ${head:0:12} is not the archived v15 HEAD ${ahead:0:12}"
  src_file "$G/qualified_refit_job1.json" "$T/row19_screen" "gate qualification"; src_file "$G/review_refit.json" "$T/row19_screen" "active gate review"
  pin "$G/qualified_refit_job1.json" "$(archive_py verify "$T" --get qualification)" "gate qualification (archived)"
  pin "$G/review_refit.json" "$(archive_py verify "$T" --get review)" "active gate review (archived)"
  before=$(sci_manifest) || { printf '%s\n' "$before"; die "the job-clone science before-proof is incomplete; nothing was changed"; }
  if [ -e "$PROOF" ] || [ -L "$PROOF" ]; then
    proof_intent
    [ ! -e "$PROOF/DONE" ] && [ ! -L "$PROOF/DONE" ] || hold "a completed deploy proof exists but the controller clone does not hold its bytes"
    [ "$IB_HEAD" = "$head" ] && [ "$IB_PAY" = "$paysha" ] || hold "an earlier attempt's deploy proof records another HEAD or payload"
    [ "$before" = "$(cat "$PROOF/science_before.sha256")" ] || hold "the science bytes differ from an earlier attempt's preserved pre-mutation manifest"
    sb=$IB_SCI
    echo "reusing the pre-mutation proof of an earlier attempt that changed nothing in the controller clone (HEAD ${head:0:12}, clean)"
  else
    dst_absent "$PROOF" "$PS" "deploy proof"
    mkdir -- "$PROOF" || die "cannot create the deploy proof $PROOF"
    put "$PROOF" science_before.sha256 "$before"
    sb=$(h "$PROOF/science_before.sha256") || die "cannot hash the preserved pre-mutation manifest"
    put "$PROOF" intent "$(printf 'schema %s\nctl_head_before %s\npayload %s\nscience_before %s' "$PSCHEMA" "$head" "$paysha" "$sb")"
    proof_intent
    [ "$(cat "$PROOF/science_before.sha256")" = "$before" ] || die "the deploy proof did not land intact"
    echo "deploy proof written before any controller change: $PROOF (science_before ${sb:0:16}, payload ${paysha:0:16})"
  fi
  dests
  i=1; LIST=""
  while [ $i -le $NP ]; do
    eval "f=\$P${i}_PATH"
    case $f in */*) dst_dir "$C/${f%/*}" "$CR" "payload $i parent";; esac
    mkdir -p -- "$(dirname -- "$f")" || die "mkdir for $f failed"
    dst_file "$C/$f" "$CR" "payload $i destination"; dst_absent "$C/$f.v16tmp" "$CR" "payload $i temporary sibling"
    cp -- "$TMPD/$i" "$f.v16tmp" || die "copy of $f failed (the clone is now dirty: recover explicitly)"
    [ -f "$f.v16tmp" ] && [ ! -L "$f.v16tmp" ] && dst_file "$C/$f" "$CR" "payload $i destination" \
      && mv -- "$f.v16tmp" "$f" || die "copy of $f failed (the clone is now dirty: recover explicitly)"
    [ "$(h "$f")" = "$(h "$TMPD/$i")" ] || die "$f did not land intact (the clone is now dirty: recover explicitly)"
    LIST="$LIST $f"; i=$((i + 1))
  done
  ctl_git
  git add -- $LIST || die "git add failed (the clone is now dirty: recover explicitly)"
  git -c user.name=R052 -c user.email=r052@local commit -q -m 'screen controllers: lineage version 16 (admission + status REVISION 16 and the designated-coordinates declaration: the resized screen S x 0..79; RSC 3686a11, review f6896e1); every other controller byte and the epoch-1 partition unchanged' -- $LIST \
    || die "git commit failed (the clone is now dirty: recover explicitly)"
  nhead=$(git rev-parse --verify HEAD) || die "git rev-parse HEAD failed after the commit"
  # the commit holds payload paths only (an unchanged payload file is not in it): never a pinned untracked evidence file, which
  # stays untracked exactly as archived
  cpaths=$(git diff-tree --no-commit-id --name-only -r "$nhead") || die "git diff-tree failed after the commit"
  [ -n "$cpaths" ] || die "the deployment commit records no path"
  plist=$(for f in $LIST; do printf '%s/%s\n' "${C#"$CR"/}" "$f"; done)
  while IFS= read -r f; do
    in_lines "$f" "$plist" || { printf '%s\n' "$cpaths"; die "the deployment commit holds $f, which is not a payload path (above)"; }
  done <<<"$cpaths"
  for f in $(ctl_evidence_paths); do
    ! git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 || die "pinned untracked evidence $f became tracked"
  done
  after=$(sci_manifest) || { printf '%s\n' "$after"; record_fail incomplete "$after"; die "the job-clone science after-proof is incomplete; completion refused (failure kept in $PROOF)"; }
  [ "$before" = "$after" ] || { record_fail changed "$after"; die "science bytes changed during the deployment; completion refused (failure kept in $PROOF)"; }
  put "$PROOF" DONE "$(printf 'schema %s\nctl_head_before %s\nctl_head_after %s\npayload %s\nscience_before %s\nscience_after %s' "$PSCHEMA" "$head" "$nhead" "$paysha" "$sb" "$(printf '%s\n' "$after" | sha256sum | cut -c1-64)")"
  chmod a-w "$PROOF" || die "chmod of the deploy proof failed"
  echo "science bytes UNCHANGED ($(printf '%s\n' "$after" | wc -l | tr -d ' ') files, complete before and after manifests identical; deploy proof DONE at ctl ${nhead:0:12})"
fi
rm -rf "$TMPD"
ctl_clean
git log -1 --format='ctl %h' || die "git log failed"
for f in $ALL; do src_file "$C/$f" "$CR" "deployed pinned file $f"; done
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
