# Migration v17 -> v18, step 6.1 (Lengau body; run from workspace_demo/t1_access on the Mac as
#   bash chpc/migration_v18/lengau.sh rollover_pilot_v18.sh
# which prepends remote_lib.sh: the fixed toolchain root, containment, drain, lock and archive checks).
# The rollover_pilot_v17.sh pattern: retire the ACTIVE v17 refit review (qualification 8fdbf48e, max 100; Codex record
# reviews/2026-10-20_pilot_v17_codex_review.md) to gate_retired/review_refit.v17_qual8fdbf48e_max100.json ONLY after the
# v17_before_v18 archive's complete certificate verifies and certifies byte-identical copies of the active review and of
# qualified_refit_job1.json, v18 is the deployed, adopted controller (deploy proof DONE) and epoch 2 is still the canonical
# activation under it (step 4 precedes this one; step 5's receipts must have passed). Admissions must be held: the drain is
# observed (checked process inventory, both locks probed free). The retirement source, its target and directory, the gate
# qualification and the chmod target are containment-checked immediately before the move and the chmod. Nothing is deleted;
# the 8fdbf48e authority stays historical (and the older retired v16 review beside it). The gate's scaleup_refit_v16.json is
# not touched (it is not generation-bound).
# Re-run: once retired (no active review; the retired file holds exactly the archived review bytes) the run reports "already
# retired" and exits 0 - also when an interruption fell between the move and the chmod, which the re-run completes (chmod of
# the contained, regular retired file only). A retired file with other bytes, or both files present, refuses.
# The next step (Mac, ONE call) regenerates the qualification from the EXISTING completed pilot job 1 under v18 - a NEW hash,
# metadata only, no fit:
#   python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
[ "${V18_PRELUDE:-}" = 1 ] || { echo "run through: bash chpc/migration_v18/lengau.sh rollover_pilot_v18.sh"; exit 1; }
[ "$NP" = 0 ] || die "rollover_pilot_v18.sh takes no payload"
OUT=$RETIRED_V17
gate_paths() {   # containment of the retirement source, its target, the gate authority (repeated before use)
  src_file "$G/review_refit.json" "$GS" "active gate review (retirement source)"
  src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"
  dst_dir "$R" "$GS" "retired-review directory"
  dst_absent "$OUT" "$GS" "retirement target"
}
cd "$C" || die "no controller clone $C"
ctl_git
v18_adopted
deploy_done
act2_valid
if [ -e "$OUT" ] || [ -L "$OUT" ]; then
  [ ! -e "$G/review_refit.json" ] && [ ! -L "$G/review_refit.json" ] || die "both the retired v17 review $OUT and an active review exist; inspect by hand"
  ra=$(archive_py verify "$T" --get review) || die "the v17 archive does not verify as complete (above)"
  dst_dir "$R" "$GS" "retired-review directory"; dst_file "$OUT" "$GS" "the retired v17 review"
  [ "$(h "$OUT")" = "$ra" ] || die "the retired file $OUT is not the archived review bytes"
  if [ -w "$OUT" ]; then
    dst_file "$OUT" "$GS" "chmod target"; chmod a-w "$OUT" || die "chmod failed"
    echo "completed the interrupted retirement: $OUT made read-only"
  fi
  echo "already retired (verified): $OUT holds the archived review ${ra:0:16}; no active review"
  exit 0
fi
[ -e "$G/review_refit.json" ] || [ -L "$G/review_refit.json" ] || die "no active review_refit.json and no retired v17 review; inspect by hand"
gate_paths
drained
locks_free
archive_py verify "$T" || die "the v17 archive does not verify as complete (above)"
ra=$(archive_py verify "$T" --get review) || die "the v17 archive does not verify as complete (above)"
qa=$(archive_py verify "$T" --get qualification) || die "the v17 archive does not verify as complete (above)"
gate_paths
hr=$(h "$G/review_refit.json") || die "cannot hash the active review"
q=$(h "$G/qualified_refit_job1.json") || die "cannot hash the gate qualification"
echo "active review ${hr:0:16} archived ${ra:0:16}; qualification ${q:0:16} archived ${qa:0:16}"
[ "$hr" = "$ra" ] || die "MISMATCH: the active review is not the archived bytes"
[ "$q" = "$V17_QUAL" ] && [ "$q" = "$qa" ] || die "the gate qualification is not the archived 8fdbf48e"
grep -q -- "$V17_QUAL" "$G/review_refit.json" || die "the active review is not bound to qualification 8fdbf48e"
dst_dir "$R" "$GS" "retired-review directory"
mkdir -p -- "$R" || die "cannot create $R"
gate_paths                                   # immediately before the move: a member changed to a symlink since the archive refuses
mv -- "$G/review_refit.json" "$OUT" || die "the move failed"
[ -f "$OUT" ] && [ ! -L "$OUT" ] && [ ! -e "$G/review_refit.json" ] && [ ! -L "$G/review_refit.json" ] && [ "$(h "$OUT")" = "$ra" ] \
  || die "the retired review did not land intact"
dst_file "$OUT" "$GS" "chmod target"           # immediately before the chmod: a regular, contained file, never a link
chmod a-w "$OUT" || die "chmod failed"
echo "retired to $OUT"
