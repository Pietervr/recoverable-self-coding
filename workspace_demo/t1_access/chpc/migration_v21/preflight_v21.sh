#!/bin/bash
# Migration v20 -> v21, step 1 (Mac + Lengau; READ-ONLY): the FULL live read-only preflight (the preflight_v20.sh pattern, the EC2
# close checks dropped: the close is done and stays done). Refuses unless:
#  Mac (v21_package.py preflight): the pinned package is exact and committed (candidate controls, map, builder, promoter, the
#          programme gate REVISION 5, the admission REVISION 21, the retained node evidence 730ea262) AND the operator adoption
#          record is pinned (the v21_package.py record pin), committed and carries the v21 literal IN HEAD; the live chpc/
#          controls and adoption are the ADOPTED v20 bytes (4e64982b / 1ef162de), committed; the two promoted pins hold their v20
#          bytes; `promote_v21.py --check` exits 0; e3 ca87fb1d committed; the Mac qualified_refit_job1.json is the v20 pilot
#          qualification 2e99d615 and its active pilot record 34c2b22b (max 200) is committed; the budget phases are committed;
#          no Mac archive, Lengau-SHA256SUMS copy or staging directory exists; a successful Mac process inventory shows no
#          refill, settle, slot-watch or controller process.
#  Lengau: the toolchain versions are printed; no controller command runs on the login node; both lock files exist and a shared
#          non-blocking probe succeeds on each; every fixed root and every authority/destination path a later step uses is its own
#          physical path in its scope (remote_lib.sh); the controller clone is clean (ctl_clean) at the adopted v20 (controls
#          4e64982b, adoption 1ef162de, the two files v21 replaces at their v20 bytes, the v20 controls record and the active v20
#          pilot record); the gate holds qualified_refit_job1.json 2e99d615 and an active review_refit.json bound to it, the v20
#          max-200 review is not yet retired; epoch 3 (the close) is THE canonical activation under the adopted v20 (act3_valid);
#          the captured node document is exactly 730ea262; no archive v20_before_v21, staging directory or v21 deploy proof
#          exists; no budget phase is pending and the ledger cap equals the committed 81,000 phase; every archive source exists
#          with its v20 identity (lengau_archive.py inventory); the job clone's COMPLETE eight-file science digest list is printed.
#  Every observation is checked: a failed or empty process inventory, a lock that cannot be probed, a failed git status or a
#  failed digest REFUSES. Running refit jobs are never touched.
# Usage (from workspace_demo/t1_access):  bash chpc/migration_v21/preflight_v21.sh [--local-only]
set -u -o pipefail
fail() { echo "PREFLIGHT REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
case ${1:-} in ""|--local-only) ;; *) fail "unknown argument $1";; esac
python3 chpc/migration_v21/v21_package.py preflight || fail "the Mac half refused (above)"
[ "${1:-}" = "--local-only" ] && { echo "PREFLIGHT (Mac only) OK - the Lengau checks were NOT run; run without --local-only before step 2"; exit 0; }
. chpc/migration_v21/lengau.sh || fail "cannot load chpc/migration_v21/lengau.sh"
to_lengau - <<'REMOTE' || fail "Lengau checks failed (above)"
echo "lengau tools: $(git --version 2>&1 | head -1); $(flock --version 2>&1 | head -1); system $(python3 --version 2>&1 | head -1); t1py $("$T/t1py" -c 'import sys; print(sys.version.split()[0])' 2>&1 | head -1)"
"$T/t1py" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 6) else 1)' || die "\$T/t1py is not a Python >= 3.6 (the Lengau-side code needs it)"
drained
locks_free
echo "drain observed: no controller command; both locks free (shared non-blocking probe)"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_designated.json \
         chpc/row19_screen_manifest.json chpc/row19_screen_budget.json chpc/row19_partition_e3.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
while read -r f s; do src_file "$C/$f" "$CR" "controller file v21 replaces: $f"; pin "$f" "$s" "controller clone $f (v20)"; done <<<"$V20_REPLACED"
for rs in "$V20_REC" "$V20_PILOT_REC"; do
  f=${rs%% *}; s=${rs##* }; src_file "$C/$f" "$CR" "controller record $f"; pin "$f" "$s" "controller clone $f"
  (git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 && git diff --quiet HEAD -- "$f") || die "$f is not committed in the controller clone"
done
dst_dir "$C/chpc" "$CR" "controller chpc directory"; dst_dir "$C/reviews" "$CR" "controller reviews directory"
src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"; src_file "$G/review_refit.json" "$GS" "active gate review"
[ -e "$G/scaleup_refit_v16.json" ] || [ -L "$G/scaleup_refit_v16.json" ] && src_file "$G/scaleup_refit_v16.json" "$GS" "gate scale-up adoption"
dst_dir "$R" "$GS" "retired-review directory"; dst_absent "$RETIRED_V20_200" "$GS" "v20 max-200 review retirement target"
src_file "$RETIRED_V20" "$GS" "the retired v20 max-100 review (left by the 26 Oct max-200 adoption)"
dst_dir "$PS" "$T" "archive parent"; dst_absent "$A" "$PS" "archive v20_before_v21"; dst_absent "$PROOF" "$PS" "v21 deploy proof"
! ls -d "$PS"/.v20_before_v21.staging* >/dev/null 2>&1 || die "an interrupted archive build left $PS/.v20_before_v21.staging*; inspect it by hand"
echo "paths resolved: controller, gate, ec2, archive and proof paths are their own physical paths; controller and science roots disjoint"
v20_current
pin "$G/qualified_refit_job1.json" $V20_QUAL "gate qualification (adopted v20 2e99d615)"
grep -q -- "$V20_QUAL" "$G/review_refit.json" || die "the active review is not bound to qualification 2e99d615"
grep -q -- '"max_job_number": 200' "$G/review_refit.json" || die "the active review is not the max-200 adoption of 26 Oct"
act3_valid
node_ev
echo "epoch 3 (the close) canonical under the adopted v20; captured node document 730ea262 in place"
"$T/t1py" -c 'import json, sys
ph = [x for x in json.load(open("chpc/row19_screen_budget.json"))["phases"] if not x.get("retired")]
led = json.load(open(sys.argv[1]))
print("budget phases: last %s pending %s; ledger cap %s" % (ph[-1]["cap_core_h"], bool(ph[-1].get("pending")), led.get("cap_core_h")))
sys.exit(0 if not ph[-1].get("pending") and led.get("cap_core_h") == ph[-1]["cap_core_h"] == float(sys.argv[2]) else 1)' \
  "$T/row19_screen_campaign/budget.json" "$LEDGER_CAP" \
  || die "a cap phase is pending, or the ledger cap is not the committed 81,000 phase, or the budget files do not read"
archive_py inventory "$T" || die "the archive sources are incomplete (above)"
sci=$(sci_manifest) || { printf '%s\n' "$sci"; die "the job-clone science proof is incomplete"; }
printf '%s\n' "$sci" | cut -c1-12,65-
echo "lengau preflight OK"
REMOTE
echo "PREFLIGHT OK: drain confirmed for this instant only - keep the hold (no refill, settlement, status or controller command) through step 8 (RUNBOOK); refills resume only after the new pilot adoption"
