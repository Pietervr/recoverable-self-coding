#!/bin/bash
# Migration v18 -> v19, step 1 (Mac + Lengau; READ-ONLY): the FULL live read-only preflight (the preflight_v18.sh pattern).
# Refuses unless:
#  Mac (v19_package.py preflight): the pinned package is exact and committed (candidate controls 4d868856, map b3a1778c, the
#          builder, the promoter, the two promoted sources, the retained node evidence 730ea262) AND the operator adoption record
#          is pinned (the v19_package.py record pin), committed and carries the v19 literal IN HEAD; the live chpc/ controls and adoption
#          are the ADOPTED v18 bytes (452b82df / 3e1fe9a1), committed; each of the two promoted paths holds its v18 bytes,
#          committed; `promote_v19.py --check` exits 0; the e2 partition is the committed 48cea639;
#          the Mac qualified_refit_job1.json is the v18 pilot qualification 530df9a2 and its pilot record 67f2b438 is committed;
#          the budget phases are committed; no Mac archive, Lengau-SHA256SUMS copy or staging directory exists; a successful Mac
#          process inventory shows no refill, slot-watch, controller, EC2-authority or EC2-reaper process; a shared non-blocking
#          probe of the Mac EC2 authority lock succeeds.
#  Lengau: the toolchain versions are printed (git, flock, system python3, $T/t1py; t1py must be >= 3.6); no controller command
#          runs on the login node (checked process inventory); both lock files exist and a shared non-blocking probe succeeds on
#          each; every fixed root and every authority/destination path a later step uses is its own physical path in its scope,
#          the controller and scientific clone roots disjoint (remote_lib.sh); the controller clone is clean (ctl_clean: only
#          the three pinned untracked evidence files) at the adopted v18 (controls 452b82df, adoption 3e1fe9a1, the two files v19
#          replaces at their v18 bytes, the v18 controls record and the v18 pilot record);
#          the gate holds qualified_refit_job1.json 530df9a2 and an active review_refit.json bound to it, and the v18 review is
#          not yet retired; epoch 2 is THE canonical activation under the adopted v18 (activation_e2.json; e1 kept); the
#          captured node document $T/jobs/row19_screen_refit_54.nodefail.json is exactly 730ea262; no archive v18_before_v19,
#          staging directory or v19 deploy proof exists; no budget phase is pending and the ledger cap equals the committed
#          81,000 phase; every archive source exists with its v18 identity (lengau_archive.py inventory); the job clone's
#          COMPLETE eight-file science digest list is printed.
#  Every observation is checked: a failed or empty process inventory, a lock that cannot be probed, a failed git status or a
#  failed digest REFUSES; none is read as "drained" or "clean". Workers and reapers are never stopped.
#  --local-only is NOT the step-1 preflight: the full run (with ssh) is the first live read-only observation.
# Usage (from workspace_demo/t1_access):  bash chpc/migration_v19/preflight_v19.sh [--local-only]
# Production route only (lengau.sh); tests run private copies (test_migration_v19.py).
set -u -o pipefail
fail() { echo "PREFLIGHT REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
case ${1:-} in ""|--local-only) ;; *) fail "unknown argument $1";; esac
python3 chpc/migration_v19/v19_package.py preflight || fail "the Mac half refused (above)"
[ "${1:-}" = "--local-only" ] && { echo "PREFLIGHT (Mac only) OK - the Lengau checks were NOT run; run without --local-only before step 2"; exit 0; }
. chpc/migration_v19/lengau.sh || fail "cannot load chpc/migration_v19/lengau.sh"
to_lengau - <<'REMOTE' || fail "Lengau checks failed (above)"
echo "lengau tools: $(git --version 2>&1 | head -1); $(flock --version 2>&1 | head -1); system $(python3 --version 2>&1 | head -1); t1py $("$T/t1py" -c 'import sys; print(sys.version.split()[0])' 2>&1 | head -1)"
"$T/t1py" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 6) else 1)' || die "\$T/t1py is not a Python >= 3.6 (the Lengau-side code needs it)"
drained
locks_free
echo "drain observed: no controller command; both locks free (shared non-blocking probe)"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
# path resolution: every controller, gate, ec2 and archive path a later step reads as authority or writes is its own physical path
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_designated.json \
         chpc/row19_screen_manifest.json chpc/row19_screen_budget.json chpc/row19_partition_e2.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
while read -r f s; do src_file "$C/$f" "$CR" "controller file v19 replaces: $f"; pin "$f" "$s" "controller clone $f (v18)"; done <<<"$V18_REPLACED"
for rs in "$V18_REC" "$V18_PILOT_REC"; do
  f=${rs%% *}; s=${rs##* }; src_file "$C/$f" "$CR" "controller record $f"; pin "$f" "$s" "controller clone $f"
  (git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 && git diff --quiet HEAD -- "$f") || die "$f is not committed in the controller clone"
done
dst_dir "$C/chpc" "$CR" "controller chpc directory"; dst_dir "$C/reviews" "$CR" "controller reviews directory"
src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"; src_file "$G/review_refit.json" "$GS" "active gate review"
[ -e "$G/scaleup_refit_v16.json" ] || [ -L "$G/scaleup_refit_v16.json" ] && src_file "$G/scaleup_refit_v16.json" "$GS" "gate scale-up adoption"
dst_dir "$R" "$GS" "retired-review directory"; dst_absent "$RETIRED_V18" "$GS" "v18 review retirement target"
src_file "$RETIRED_V17" "$GS" "the retired v17 review (left by migration_v18)"
dst_dir "$PS" "$T" "archive parent"; dst_absent "$A" "$PS" "archive v18_before_v19"; dst_absent "$PROOF" "$PS" "v19 deploy proof"
! ls -d "$PS"/.v18_before_v19.staging* >/dev/null 2>&1 || die "an interrupted archive build left $PS/.v18_before_v19.staging*; inspect it by hand"
echo "paths resolved: controller, gate, ec2, archive and proof paths are their own physical paths; controller and science roots disjoint"
v18_current
pin "$G/qualified_refit_job1.json" $V18_QUAL "gate qualification (adopted v18 530df9a2)"
grep -q -- "$V18_QUAL" "$G/review_refit.json" || die "the active review is not bound to qualification 530df9a2"
[ -e "$G/scaleup_refit_v16.json" ] && echo "gate: scaleup_refit_v16.json present (not generation-bound; it stays valid under v19)" \
  || echo "gate: no scaleup_refit_v16.json (admission stays first-job-alone until a scale-up adoption)"
act2_valid
node_ev
echo "epoch 2 active (canonical under the adopted v18); captured node document 730ea262 in place"
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
echo "PREFLIGHT OK: drain confirmed for this instant only - keep the coordinated hold (refill scripts and slot watcher stopped, no controller, settlement, status or EC2 authority command) through step 6 (RUNBOOK); refills resume only after the new pilot adoption"
