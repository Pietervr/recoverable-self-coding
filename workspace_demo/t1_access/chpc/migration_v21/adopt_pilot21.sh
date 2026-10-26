# Migration v20 -> v21, step 8 (Lengau body): adopt the OPERATOR record (owner rule 20 Oct 2026: operational steps are recorded by
# the operator, no Codex review) of the REGENERATED v21 refit pilot qualification (new hash, max job 200 - the scope the owner
# set on 26 Oct 2026) - the adopt_pilot20.sh pattern. The record must carry
#   ADOPT row19-screen-pilot role=refit qualification=<the new qsha> max_job=200
# for EXACTLY the qualification now in the gate; the historical 2c7a7ef1, 8fdbf48e, 530df9a2, e123d6e5 and 2e99d615 literals
# cannot authorize it. Commit the record on the Mac, then (from workspace_demo/t1_access):
#   bash chpc/migration_v21/lengau.sh adopt_pilot21.sh --file reviews/<record>.md
# Requires v21 deployed and adopted (deploy proof DONE), epoch 3 the canonical activation, the v20 review retired (no active
# review) and a gate qualification that is none of the historical ones. The record is committed in the controller clone unless
# that clone already holds exactly these bytes, committed. The adopter creates the NEW gate review_refit.json and refuses when one
# exists (never overwrites).
[ "${V21_PRELUDE:-}" = 1 ] || { echo "run through: bash chpc/migration_v21/lengau.sh adopt_pilot21.sh --file reviews/<record>.md"; exit 1; }
[ "$NP" = 1 ] || die "expected exactly one payload (the pilot record), got $NP"
REC=$P1_PATH
case $REC in reviews/*.md) ;; *) die "the record $REC is not reviews/<name>.md";; esac
case ${REC#reviews/} in */*|.*) die "the record $REC is not a plain reviews/<name>.md";; esac
clean_rel "$REC" || die "the record $REC is not a plain relative path"
not_evidence "$REC" "pilot record"
adopt_paths() {   # containment of the record destination (and its reviews/ parent), the controller and gate authority, the new gate review
  dst_dir "$C/reviews" "$CR" "controller reviews directory"
  dst_file "$C/$REC" "$CR" "record destination"
  src_file "$C/chpc/row19_screen_controls.json" "$CR" "deployed controls"; src_file "$C/chpc/row19_screen_controls_adoption.json" "$CR" "deployed adoption"
  src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"
  dst_absent "$G/review_refit.json" "$GS" "new gate review (the adopter's destination)"
}
[ ! -e "$G/review_refit.json" ] && [ ! -L "$G/review_refit.json" ] || die "an active review exists; retire it first (rollover_pilot_v21.sh)"
cd "$C" || die "no controller clone $C"
ctl_git
adopt_paths
v21_adopted
deploy_done
act3_valid
acts_kept
src_file "$RETIRED_V20_200" "$GS" "the retired v20 max-200 review"
q=$(h "$G/qualified_refit_job1.json") || die "no readable gate qualification"
[ "$q" != "$V20_QUAL" ] || die "the gate qualification is still the v20 2e99d615; regenerate it under v21 first (--qualify 1)"
[ "$q" != "$V19_QUAL" ] || die "the gate qualification is the historical v19 e123d6e5"
[ "$q" != "$V18_QUAL" ] || die "the gate qualification is the historical v18 530df9a2"
[ "$q" != "$V17_QUAL" ] || die "the gate qualification is the historical v17 8fdbf48e"
[ "$q" != "$V16_QUAL" ] || die "the gate qualification is the historical v16 2c7a7ef1"
drained
locks_free
TMPD=$(mktemp -d) || die "mktemp failed"
payload 1 "$TMPD/rec"
LIT="ADOPT row19-screen-pilot role=refit qualification=$q max_job=200"
literal_in "$TMPD/rec" "$LIT" || die "the record does not carry the literal for the gate qualification ${q:0:16}: $LIT"
adopt_paths                                  # immediately before the copy and the adopter
if [ -e "$REC" ] || [ -L "$REC" ]; then
  cmp -s "$TMPD/rec" "$REC" || die "$REC exists in the controller clone with other bytes"
  git ls-files --error-unmatch -- "$REC" >/dev/null 2>&1 && git diff --quiet HEAD -- "$REC" || die "$REC is not committed in the controller clone"
else
  ctl_clean
  cp "$TMPD/rec" "$REC" || die "copy failed"
  git add -- "$REC" && git -c user.name=R052 -c user.email=r052@local commit -q -m "operator record: v21 refit pilot ADOPT max 200 on the regenerated qualification" -- "$REC" \
    || die "git commit of $REC failed (the clone may be dirty: recover explicitly)"
fi
rm -rf "$TMPD"
ctl_clean
git log -1 --format=%h || die "git log failed"
src_file "$C/$REC" "$CR" "committed record"; adopt_paths
sha256sum -- "$REC" || die "cannot hash $REC"
AOUT=$(mktemp) || die "mktemp failed"
"$T/t1py" chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-review "$REC" --max-job-number 200 > "$AOUT" 2>&1; rc=$?
tail -4 "$AOUT"; rm -f "$AOUT"
[ $rc = 0 ] || die "the supported adopter refused or failed (exit $rc, above)"
src_file "$G/review_refit.json" "$GS" "new gate review"
sha256sum -- "$G/review_refit.json" || die "no gate review_refit.json after the adopter"
echo "adopt_pilot21 complete"
