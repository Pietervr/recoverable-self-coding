# Migration v16 -> v17, step 8.4 (Lengau body): adopt Codex's review of the REGENERATED v17 refit pilot qualification (new hash,
# max job 100) - the adopt_pilot16.sh pattern. The record must carry
#   ADOPT row19-screen-pilot role=refit qualification=<the new qsha> max_job=100
# for EXACTLY the qualification now in the gate (checked here before the record is committed in the controller clone, and again
# by the supported adopter); the historical 3c605514 and 2c7a7ef1 literals cannot authorize it. Commit the record on the Mac,
# then (from workspace_demo/t1_access):
#   bash chpc/migration_v17/lengau.sh adopt_pilot17.sh --file reviews/<record>.md
# lengau.sh carries the record inside the script (checked against its Mac SHA-256) and prepends remote_lib.sh. Requires v17
# deployed and adopted (deploy proof DONE), the canonical e2 activation on the root, the v16 review retired (no active review)
# and a gate qualification that is no longer 2c7a7ef1. The record destination and its reviews/ parent, the controller authority
# and the gate paths are containment-checked before the copy. The record is committed in the controller clone unless that clone
# already holds exactly these bytes, committed. The adopter creates the NEW gate review_refit.json and refuses when one exists
# (never overwrites); an adopter refusal is reported as a refusal and changes no gate file.
[ "${V17_PRELUDE:-}" = 1 ] || { echo "run through: bash chpc/migration_v17/lengau.sh adopt_pilot17.sh --file reviews/<record>.md"; exit 1; }
[ "$NP" = 1 ] || die "expected exactly one payload (the review record), got $NP"
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
[ ! -e "$G/review_refit.json" ] && [ ! -L "$G/review_refit.json" ] || die "an active review exists; retire it first (rollover_pilot_v17.sh)"
cd "$C" || die "no controller clone $C"
ctl_git
adopt_paths
v17_adopted
deploy_done
act2_valid
src_file "$RETIRED_V16" "$GS" "the retired v16 review"
q=$(h "$G/qualified_refit_job1.json") || die "no readable gate qualification"
[ "$q" != "$V16_QUAL" ] || die "the gate qualification is still the v16 2c7a7ef1; regenerate it under v17 first (--qualify 1)"
drained
locks_free
TMPD=$(mktemp -d) || die "mktemp failed"
payload 1 "$TMPD/rec"
LIT="ADOPT row19-screen-pilot role=refit qualification=$q max_job=100"
sed 's/^[[:space:]]*//; s/[[:space:]]*$//' "$TMPD/rec" | grep -xF -- "$LIT" >/dev/null || die "the record does not carry the literal for the gate qualification ${q:0:16}: $LIT"
adopt_paths                                  # immediately before the copy and the adopter
if [ -e "$REC" ] || [ -L "$REC" ]; then
  cmp -s "$TMPD/rec" "$REC" || die "$REC exists in the controller clone with other bytes"
  git ls-files --error-unmatch -- "$REC" >/dev/null 2>&1 && git diff --quiet HEAD -- "$REC" || die "$REC is not committed in the controller clone"
else
  ctl_clean
  cp "$TMPD/rec" "$REC" || die "copy failed"
  git add -- "$REC" && git -c user.name=R052 -c user.email=r052@local commit -q -m "Codex record: v17 refit pilot ADOPT max 100 on the regenerated qualification" -- "$REC" \
    || die "git commit of $REC failed (the clone may be dirty: recover explicitly)"
fi
rm -rf "$TMPD"
ctl_clean
git log -1 --format=%h || die "git log failed"
src_file "$C/$REC" "$CR" "committed record"; adopt_paths
sha256sum -- "$REC" || die "cannot hash $REC"
AOUT=$(mktemp) || die "mktemp failed"
"$T/t1py" chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --adopt-review "$REC" --max-job-number 100 > "$AOUT" 2>&1; rc=$?
tail -4 "$AOUT"; rm -f "$AOUT"
[ $rc = 0 ] || die "the supported adopter refused or failed (exit $rc, above)"
src_file "$G/review_refit.json" "$GS" "new gate review"
sha256sum -- "$G/review_refit.json" || die "no gate review_refit.json after the adopter"
echo "adopt_pilot17 complete"
