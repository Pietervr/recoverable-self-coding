#!/bin/bash
# Migration v16 -> v17, step 1 (Mac + Lengau; READ-ONLY): the FULL live read-only preflight. Refuses unless:
#  Mac (v17_package.py preflight): the live chpc/ controls and adoption are the ADOPTED v16 bytes (01976b6a / 523fe18a), committed;
#          every one of the 19 promoted paths of the reviewed promotion map holds its v16 bytes (or is absent when new), committed;
#          the reviewed package is exact and committed (candidate controls 9ea4e727, map 6bc8bd39, builder f2a80f42, promoter
#          f0c320c2, admission c3960464) and `promote_v17.py --check` exits 0 (every map source at its reviewed bytes, versions
#          1-16 equal to the adopted file, the e2 partition loading and regenerating); the review record
#          reviews/2026-10-19_e2_repair_codex_rereview.md (48b9cf05) is committed with the exact literal IN HEAD; the e1
#          partition is 8d1de408; the Mac qualified_refit_job1.json is the v16 pilot qualification 2c7a7ef1; the budget phases
#          are committed; no Mac archive or staging directory exists; a successful Mac process inventory shows no refill,
#          slot-watch, controller, EC2-authority or EC2-reaper process; a shared non-blocking probe of the Mac EC2 authority lock
#          aws_ec2/runs/.authority.lock succeeds.
#  Lengau: the toolchain versions are printed (git, flock, system python3, $T/t1py; t1py must be >= 3.6); no controller command
#          runs on the login node (checked process inventory); both lock files exist and a shared non-blocking probe succeeds on
#          each; every fixed root and every authority/destination path a later step uses is its own physical path in its scope,
#          the controller and scientific clone roots disjoint (remote_lib.sh); the controller clone is clean (ctl_clean: only the
#          three pinned untracked evidence files) at the v16 bytes (controls, adoption, the five files v17 replaces, status and
#          designated, e1), with NONE of the nine paths v17 adds; the gate holds qualified_refit_job1.json 2c7a7ef1 and an active
#          review_refit.json bound to it, and the v16 review is not yet retired; epoch 1 is activated and activation_e2.json does
#          NOT exist; no archive v16_before_v17, staging directory or v17 deploy proof exists; no budget phase is pending and the
#          ledger cap equals the committed 81,000 phase; every archive source exists with its v16 identity (lengau_archive.py
#          inventory); the job clone's COMPLETE eight-file science digest list is printed.
#  Every observation is checked: a failed or empty process inventory, a lock that cannot be probed, a failed git status or a
#  failed digest REFUSES; none is read as "drained" or "clean". Workers and reapers are never stopped.
#  --local-only is NOT the step-1 preflight: the full run (with ssh) is the first live read-only observation.
# Usage (from workspace_demo/t1_access):  bash chpc/migration_v17/preflight_v17.sh [--local-only]
# Production route only (lengau.sh); tests run private copies (test_migration_v17.py).
set -u -o pipefail
fail() { echo "PREFLIGHT REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
case ${1:-} in ""|--local-only) ;; *) fail "unknown argument $1";; esac
python3 chpc/migration_v17/v17_package.py preflight || fail "the Mac half refused (above)"
[ "${1:-}" = "--local-only" ] && { echo "PREFLIGHT (Mac only) OK - the Lengau checks were NOT run; run without --local-only before step 2"; exit 0; }
. chpc/migration_v17/lengau.sh || fail "cannot load chpc/migration_v17/lengau.sh"
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
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_status.py chpc/row19_screen_designated.json \
         chpc/row19_screen_manifest.json chpc/row19_screen_budget.json chpc/row19_partition_e1.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
while read -r f s; do src_file "$C/$f" "$CR" "controller file v17 replaces: $f"; pin "$f" "$s" "controller clone $f (v16)"; done <<<"$V16_REPLACED"
dst_dir "$C/chpc" "$CR" "controller chpc directory"; dst_dir "$C/reviews" "$CR" "controller reviews directory"
dst_dir "$C/aws_ec2" "$CR" "controller aws_ec2 directory"; dst_dir "$C/aws_ec2/prod" "$CR" "controller aws_ec2/prod directory (new)"
for f in $V17_NEW; do
  dst_absent "$C/$f" "$CR" "v17 path $f (must not exist before the deploy)"
done
src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"; src_file "$G/review_refit.json" "$GS" "active gate review"
[ -e "$G/scaleup_refit_v16.json" ] || [ -L "$G/scaleup_refit_v16.json" ] && src_file "$G/scaleup_refit_v16.json" "$GS" "gate scale-up adoption"
dst_dir "$R" "$GS" "retired-review directory"; dst_absent "$RETIRED_V16" "$GS" "v16 review retirement target"
src_file "$ACT1" "$GS" "epoch-1 activation proof"; dst_absent "$ACT2" "$GS" "epoch-2 activation proof (must not exist before v17)"
dst_dir "$PS" "$T" "archive parent"; dst_absent "$A" "$PS" "archive v16_before_v17"; dst_absent "$PROOF" "$PS" "v17 deploy proof"
! ls -d "$PS"/.v16_before_v17.staging* >/dev/null 2>&1 || die "an interrupted archive build left $PS/.v16_before_v17.staging*; inspect it by hand"
echo "paths resolved: controller, gate, ec2, archive and proof paths are their own physical paths; controller and science roots disjoint"
pin chpc/row19_screen_controls.json $V16_CONTROLS "controller clone controls (adopted v16)"
pin chpc/row19_screen_controls_adoption.json $V16_ADOPTION "controller clone adoption (v16 record)"
pin chpc/row19_partition_e1.json $E1_PART "controller clone partition e1"
pin "$G/qualified_refit_job1.json" $V16_QUAL "gate qualification (adopted v16 2c7a7ef1)"
grep -q -- "$V16_QUAL" "$G/review_refit.json" || die "the active review is not bound to qualification 2c7a7ef1"
[ -e "$G/scaleup_refit_v16.json" ] && echo "gate: scaleup_refit_v16.json present (not generation-bound; it stays valid under v17)" \
  || echo "gate: no scaleup_refit_v16.json (admission stays first-job-alone until a scale-up adoption)"
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
echo "PREFLIGHT OK: drain confirmed for this instant only - keep the coordinated hold (refill scripts and slot watcher stopped, no controller, settlement, status or EC2 authority command) through step 8 (RUNBOOK); refills resume only after the new pilot adoption"
