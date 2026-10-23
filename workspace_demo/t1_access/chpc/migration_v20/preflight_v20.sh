#!/bin/bash
# Migration v19 -> v20, step 1 (Mac + Lengau; READ-ONLY): the FULL live read-only preflight (the preflight_v19.sh pattern).
# Refuses unless:
#  Mac (v20_package.py preflight): the pinned package is exact and committed (candidate controls 4e64982b, map 79c78ea7, the
#          builder, the promoter, the two promoted controllers, the e3 closing declaration ca87fb1d, the Mac authority e1381d68, the
#          retained node evidence 730ea262) AND the operator adoption record is pinned (the v20_package.py record pin), committed and
#          carries the v20 literal IN HEAD; the live chpc/ controls and adoption are the ADOPTED v19 bytes (111c3107 / 2b9f3c78),
#          committed; the two promoted pins and the Mac authority hold their v19 bytes and the new e3 path is absent;
#          `promote_v20.py --check` exits 0; the e2 partition is the committed 48cea639; `prod_authority.py close-check` reports the
#          EC2 close preconditions MET (RUNBOOK step 0b done);
#          the Mac qualified_refit_job1.json is the v19 pilot qualification e123d6e5 and its pilot record 26aa4f8d is committed;
#          the budget phases are committed; no Mac archive, Lengau-SHA256SUMS copy or staging directory exists; a successful Mac
#          process inventory shows no refill, slot-watch, controller, EC2-authority or EC2-reaper process; a shared non-blocking
#          probe of the Mac EC2 authority lock succeeds.
#  Lengau: the toolchain versions are printed (git, flock, system python3, $T/t1py; t1py must be >= 3.6); no controller command
#          runs on the login node (checked process inventory); both lock files exist and a shared non-blocking probe succeeds on
#          each; every fixed root and every authority/destination path a later step uses is its own physical path in its scope,
#          the controller and scientific clone roots disjoint (remote_lib.sh); the controller clone is clean (ctl_clean: only
#          the three pinned untracked evidence files) at the adopted v19 (controls 111c3107, adoption 2b9f3c78, the two files v20
#          replaces at their v19 bytes, the v19 controls record and the v19 pilot record);
#          the gate holds qualified_refit_job1.json e123d6e5 and an active review_refit.json bound to it, the v19 review is not yet
#          retired and the v18 review is (left by migration_v19); epoch 2 is THE canonical activation under the adopted v19
#          (activation_e2.json; e1 kept) and no activation_e3.json exists; the root's installed authority inventory shows no live or
#          owning EC2 attempt (the Lengau view of step 0b); the
#          captured node document $T/jobs/row19_screen_refit_54.nodefail.json is exactly 730ea262; no archive v19_before_v20,
#          staging directory or v20 deploy proof exists; no budget phase is pending and the ledger cap equals the committed
#          81,000 phase; every archive source exists with its v19 identity (lengau_archive.py inventory); the job clone's
#          COMPLETE eight-file science digest list is printed.
#  Every observation is checked: a failed or empty process inventory, a lock that cannot be probed, a failed git status or a
#  failed digest REFUSES; none is read as "drained" or "clean". Workers and reapers are never stopped.
#  --local-only is NOT the step-1 preflight: the full run (with ssh) is the first live read-only observation.
# Usage (from workspace_demo/t1_access):  bash chpc/migration_v20/preflight_v20.sh [--local-only]
# Production route only (lengau.sh); tests run private copies (test_migration_v20.py).
set -u -o pipefail
fail() { echo "PREFLIGHT REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
case ${1:-} in ""|--local-only) ;; *) fail "unknown argument $1";; esac
python3 chpc/migration_v20/v20_package.py preflight || fail "the Mac half refused (above)"
[ "${1:-}" = "--local-only" ] && { echo "PREFLIGHT (Mac only) OK - the Lengau checks were NOT run; run without --local-only before step 2"; exit 0; }
. chpc/migration_v20/lengau.sh || fail "cannot load chpc/migration_v20/lengau.sh"
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
while read -r f s; do src_file "$C/$f" "$CR" "controller file v20 replaces: $f"; pin "$f" "$s" "controller clone $f (v19)"; done <<<"$V19_REPLACED"
for f in $V20_NEW; do dst_absent "$C/$f" "$CR" "new v20 data path $f"; done
for rs in "$V19_REC" "$V19_PILOT_REC"; do
  f=${rs%% *}; s=${rs##* }; src_file "$C/$f" "$CR" "controller record $f"; pin "$f" "$s" "controller clone $f"
  (git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 && git diff --quiet HEAD -- "$f") || die "$f is not committed in the controller clone"
done
dst_dir "$C/chpc" "$CR" "controller chpc directory"; dst_dir "$C/reviews" "$CR" "controller reviews directory"
src_file "$G/qualified_refit_job1.json" "$GS" "gate qualification"; src_file "$G/review_refit.json" "$GS" "active gate review"
[ -e "$G/scaleup_refit_v16.json" ] || [ -L "$G/scaleup_refit_v16.json" ] && src_file "$G/scaleup_refit_v16.json" "$GS" "gate scale-up adoption"
dst_dir "$R" "$GS" "retired-review directory"; dst_absent "$RETIRED_V19" "$GS" "v19 review retirement target"
src_file "$RETIRED_V18" "$GS" "the retired v18 review (left by migration_v19)"
dst_absent "$ACT3" "$GS" "the epoch-3 activation (the close happens after the deploy)"
dst_dir "$PS" "$T" "archive parent"; dst_absent "$A" "$PS" "archive v19_before_v20"; dst_absent "$PROOF" "$PS" "v20 deploy proof"
! ls -d "$PS"/.v19_before_v20.staging* >/dev/null 2>&1 || die "an interrupted archive build left $PS/.v19_before_v20.staging*; inspect it by hand"
echo "paths resolved: controller, gate, ec2, archive and proof paths are their own physical paths; controller and science roots disjoint"
v19_current
pin "$G/qualified_refit_job1.json" $V19_QUAL "gate qualification (adopted v19 e123d6e5)"
grep -q -- "$V19_QUAL" "$G/review_refit.json" || die "the active review is not bound to qualification e123d6e5"
[ -e "$G/scaleup_refit_v16.json" ] && echo "gate: scaleup_refit_v16.json present (not generation-bound; it stays valid under v20)" \
  || echo "gate: no scaleup_refit_v16.json (admission stays first-job-alone until a scale-up adoption)"
act2_valid
node_ev
echo "epoch 2 active (canonical under the adopted v19); captured node document 730ea262 in place"
"$T/t1py" -c 'import sys; sys.path.insert(0, "chpc"); import row19_ec2_state as ES
inv, why = ES.installed_inventory(sys.argv[1], max_age=float("inf"))
live = ES.live_attempts(inv) if inv else ["(no inventory: %s)" % why]
print("installed authority inventory: generation %s, owners %d, live or owning %s" % ((inv or {}).get("generation"), len((inv or {}).get("owners") or {}), live))
sys.exit(1 if (why or live or (inv or {}).get("owners")) else 0)' "$GS" \
  || die "the root's installed inventory still shows a live or owning EC2 attempt: finish RUNBOOK step 0b (dispositions, ec2_sync) first"
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
