# Migration v15 -> v16, step 7.1 (Lengau body; run from workspace_demo/t1_access on the Mac as
#   bash chpc/migration_v16/lengau.sh rollover_pilot_v16.sh
# which prepends remote_lib.sh: the fixed toolchain root, containment, drain, lock and archive checks).
# The v13 rollover_pilot.sh pattern: retire the ACTIVE v15 refit review (qualification 3c605514, max 100; Codex RSC 66d1e99) to
# gate_retired/ ONLY after the v15_before_v16 archive's complete certificate verifies (lengau_archive.py verify: exact
# inventory, every digest, COMPLETE) and certifies byte-identical copies of the active review and of qualified_refit_job1.json,
# and v16 is the deployed, adopted controller in rsc_screen_ctl. Admissions must be held: the drain is observed (checked
# process inventory, both locks probed free). Nothing is deleted; the 3c605514 authority stays historical. A re-run after the
# retirement refuses ("retired file exists"), which is the completed state. The next step (Mac, ONE call) regenerates the
# qualification from the EXISTING completed pilot job 1 under v16 - a NEW hash, no fit:
#   python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
[ "${V16_PRELUDE:-}" = 1 ] || { echo "run through: bash chpc/migration_v16/lengau.sh rollover_pilot_v16.sh"; exit 1; }
OUT=$R/review_refit.v15_qual3c605514_max100.json
[ ! -e "$OUT" ] && [ ! -L "$OUT" ] || die "retired file exists: $OUT (already retired)"
[ -f "$G/review_refit.json" ] || die "no active review_refit.json (already retired?)"
pin "$C/chpc/row19_screen_controls.json" $V16_CONTROLS "deployed controls (v16)"
"$T/t1py" -c 'import json, sys
a = json.load(open(sys.argv[1]))
sys.exit(0 if a.get("version") == 16 and a.get("controls_sha256") == sys.argv[2] else 1)' "$C/chpc/row19_screen_controls_adoption.json" $V16_CONTROLS \
  || die "v16 is not the deployed, adopted controller in rsc_screen_ctl (deploy_v16.sh first)"
drained
locks_free
archive_py verify "$T" || die "the v15 archive does not verify as complete (above)"
ra=$(archive_py verify "$T" --get review) || die "the v15 archive does not verify as complete (above)"
qa=$(archive_py verify "$T" --get qualification) || die "the v15 archive does not verify as complete (above)"
hr=$(h "$G/review_refit.json") || die "cannot hash the active review"
q=$(h "$G/qualified_refit_job1.json") || die "cannot hash the gate qualification"
echo "active review ${hr:0:16} archived ${ra:0:16}; qualification ${q:0:16} archived ${qa:0:16}"
[ "$hr" = "$ra" ] || die "MISMATCH: the active review is not the archived bytes"
[ "$q" = "$V15_QUAL" ] && [ "$q" = "$qa" ] || die "the gate qualification is not the archived 3c605514"
grep -q -- "$V15_QUAL" "$G/review_refit.json" || die "the active review is not bound to qualification 3c605514"
mkdir -p "$R" || die "cannot create $R"
[ ! -e "$OUT" ] && [ ! -L "$OUT" ] || die "retired file appeared: $OUT"
mv -- "$G/review_refit.json" "$OUT" || die "the move failed"
[ -f "$OUT" ] && [ ! -e "$G/review_refit.json" ] && [ "$(h "$OUT")" = "$ra" ] || die "the retired review did not land intact"
chmod a-w "$OUT" || die "chmod failed"
echo "retired to $OUT"
