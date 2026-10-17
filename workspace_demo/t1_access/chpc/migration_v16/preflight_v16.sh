#!/bin/bash
# Migration v15 -> v16, step 1.2 (Mac + Lengau; READ-ONLY). Refuses unless:
#  Mac:    the live chpc/ controls/adoption/admission/status are the ADOPTED v15 bytes (828d3b69 / 970c29f5 / ac06e803 / 0effcba3)
#          and no designated declaration is live yet; candidate_v16/ holds the reviewed bytes (controls 01976b6a, admit 1b02f336,
#          status a9f9180b, declaration a96eb598), committed and unmodified, with versions 1-15 equal to the adopted file;
#          the Codex review record reviews/2026-10-17_v16_p80_codex_review.md (a315d7d2, RSC f6896e1) is git-tracked,
#          unmodified and carries the exact literal ADOPT line IN HEAD; the e1 partition is 8d1de408; the Mac copy of
#          qualified_refit_job1.json is the adopted v15 pilot qualification 3c605514; the Mac archive does not exist; no
#          refill/slot-watch/controller process runs on the Mac.
#  Lengau: no controller command runs on the login node (the v13/v15 process list); neither the programme admission lock nor
#          the screen plan lock is held; the controller clone rsc_screen_ctl is clean at the v15 bytes; the gate holds the
#          v15 qualification 3c605514 and an active review_refit.json; no cap phase is pending and the ledger cap equals the
#          last committed phase; epoch 1 is activated; the archive v15_before_v16 and the v16 retired review do not exist;
#          every archive source exists with its v15 identity (lengau_archive.py inventory); the job clone's complete science
#          digest list (fixed inventory, every file read and hashed) is printed.
#  Every observation is checked: a failed or empty process inventory, a lock that cannot be probed (flock(1) or a python
#  fcntl.flock(LOCK_SH|LOCK_NB) on the same file), a failed git status or a failed digest REFUSES; none is read as "drained" or
#  "clean". Every Lengau path must be its own physical path in its canonical scope, the controller and science roots disjoint
#  (remote_lib.sh); the controller chpc/ and reviews/ directories, its git directory, the authority files and the gate files are
#  resolved, and no v16 deploy proof exists. Workers and reapers are never stopped.
#  --local-only is NOT the step-1 preflight: the full run (with ssh) is the first live read-only observation.
# Usage (from workspace_demo/t1_access):  bash chpc/migration_v16/preflight_v16.sh [--local-only]
#   --local-only   the Mac checks only (no ssh); the migration still needs a full run.
# Production route only (lengau.sh); tests run private copies (test_migration_v16.py).
set -u -o pipefail
fail() { echo "PREFLIGHT REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
want() { [ -e "$1" ] || fail "$1 is missing"; [ "$(shasum -a 256 "$1" | cut -c1-64)" = "$2" ] || fail "$1 is not $2"; }
committed() { git ls-files --error-unmatch -- "$1" >/dev/null 2>&1 && git diff --quiet HEAD -- "$1" || fail "$1 is not git-tracked and unmodified (commit state differs from HEAD)"; }
LIT='ADOPT row19-screen-controls sha256=01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220 version=16'
REC=reviews/2026-10-17_v16_p80_codex_review.md
# -- adopted v15 (live) --
want chpc/row19_screen_controls.json 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5
want chpc/row19_screen_controls_adoption.json 970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d
want chpc/row19_screen_admit.py ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac
want chpc/row19_screen_status.py 0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_admit.py chpc/row19_screen_status.py; do committed $f; done
[ ! -e chpc/row19_screen_designated.json ] || fail "chpc/row19_screen_designated.json already exists (promotion started?)"
# -- reviewed v16 candidate --
want chpc/candidate_v16/row19_screen_controls.json 01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220
want chpc/candidate_v16/row19_screen_admit.py 1b02f336f174147db975142f62e3dae947deb14f673345cc99120074deb747a0
want chpc/candidate_v16/row19_screen_status.py a9f9180b73438221788d745567603fd267befca8fbc60528e3e7de47421ff64a
want chpc/candidate_v16/row19_screen_designated.json a96eb59833ff794d3f9ce0ca09ada03d045a29cb9f8a676dad86f8aba85d5584
for f in row19_screen_controls.json row19_screen_admit.py row19_screen_status.py row19_screen_designated.json; do committed chpc/candidate_v16/$f; done
python3 -c 'import json, sys
c = json.load(open("chpc/candidate_v16/row19_screen_controls.json")); a = json.load(open("chpc/row19_screen_controls.json"))
v = c["versions"][-1]
ok = c["versions"][:-1] == a["versions"] and v.get("version") == 16 and (v.get("partition") or {}).get("sha256") == "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608"
sys.exit(0 if ok else 1)' || fail "candidate versions 1-15 are not the adopted entries, or its latest entry is not version 16 pinning partition e1"
want chpc/row19_partition_e1.json 8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608
# -- the review record and its literal, in HEAD --
want $REC a315d7d2f7b91baec3b668e4dcec4c2530ab44d8c07aef597b77e28fdd3d447c
committed $REC
rec_head=$(git show "HEAD:./$REC") || fail "git show HEAD:./$REC failed"
grep -qxF -- "$LIT" <<<"$rec_head" || fail "the committed review record does not carry the exact line: $LIT"
# -- Mac pilot qualification and archive --
want chpc/results/row19_screen/receipts/qualified_refit_job1.json 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c
[ ! -e chpc/results/archive/row19_screen_v15_before_v16 ] || fail "the Mac archive row19_screen_v15_before_v16 already exists (migration started before?)"
ls -d chpc/results/archive/.row19_screen_v15_before_v16.staging* >/dev/null 2>&1 && fail "an interrupted Mac archive build left chpc/results/archive/.row19_screen_v15_before_v16.staging*; inspect it by hand"
committed chpc/row19_screen_budget.json
# -- Mac drain: no refill, slot watcher or controller command of this user --
ps_out=$(ps -x -o args=); rc=$?
[ $rc = 0 ] || fail "the Mac process inventory failed (ps exited $rc); the drain is not observed"
[ -n "$ps_out" ] || fail "the Mac process inventory is empty; the drain is not observed"
p=$(printf '%s\n' "$ps_out" | grep -E "refill_(r1|b1)\.sh|slot_watch\.sh|row19_screen_(admit|status|verify)\.py|row22_bank_(submit|status)\.py|row19_ec2_|row19_partition\.py"); rc=$?
case $rc in 0) echo "$p"; fail "a refill, slot-watch or controller command runs on the Mac (above)";; 1) ;; *) fail "the Mac process filter failed (grep exited $rc)";; esac
echo "mac preflight OK"
[ "${1:-}" = "--local-only" ] && { echo "PREFLIGHT (Mac only) OK - the Lengau checks were NOT run; run without --local-only before step 2"; exit 0; }
. chpc/migration_v16/lengau.sh || fail "cannot load chpc/migration_v16/lengau.sh"
to_lengau - <<'REMOTE' || fail "Lengau checks failed (above)"
drained
locks_free
echo "drain observed: no controller command; both locks free (shared non-blocking probe)"
cd "$C" || die "no controller clone $C"
ctl_git
git_clean "$C"
# path resolution: every controller, gate and archive path a later step reads as authority or writes is its own physical path
for f in chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_admit.py chpc/row19_screen_status.py \
         chpc/row19_screen_manifest.json chpc/row19_screen_budget.json chpc/row19_partition_e1.json; do src_file "$C/$f" "$CR" "controller authority $f"; done
dst_dir "$C/chpc" "$CR" "controller chpc directory"; dst_dir "$C/reviews" "$CR" "controller reviews directory"
dst_file "$C/chpc/row19_screen_designated.json" "$CR" "deploy destination"
src_file "$G/qualified_refit_job1.json" "$T/row19_screen" "gate qualification"; src_file "$G/review_refit.json" "$T/row19_screen" "active gate review"
dst_dir "$R" "$T/row19_screen" "retired-review directory"; dst_dir "$T/archive_screen" "$T" "archive parent"
[ ! -e "$PROOF" ] && [ ! -L "$PROOF" ] || die "a v16 deploy proof $PROOF already exists (migration started before?)"
echo "paths resolved: controller, gate, archive and proof paths are their own physical paths; controller and science roots disjoint"
pin chpc/row19_screen_controls.json $V15_CONTROLS "controller clone controls (adopted v15)"
pin chpc/row19_screen_controls_adoption.json $V15_ADOPTION "controller clone adoption (v15 record)"
pin chpc/row19_screen_admit.py $V15_ADMIT "controller clone admission (v15)"
pin chpc/row19_screen_status.py $V15_STATUS "controller clone status (v15)"
[ ! -e chpc/row19_screen_designated.json ] || die "controller clone already has the designated declaration"
pin "$G/qualified_refit_job1.json" $V15_QUAL "gate qualification (adopted v15 3c605514)"
[ -f "$G/review_refit.json" ] || die "no active gate review_refit.json"
[ ! -e "$G/scaleup_refit_v16.json" ] || die "a v16 scale-up adoption already exists"
[ ! -e "$R/review_refit.v15_qual3c605514_max100.json" ] || die "the v15 review is already retired"
[ ! -e "$A" ] && [ ! -L "$A" ] || die "archive v15_before_v16 already exists (migration started before?)"
! ls -d "$T"/archive_screen/.v15_before_v16.staging* >/dev/null 2>&1 || die "an interrupted archive build left $T/archive_screen/.v15_before_v16.staging*; inspect it by hand"
[ -e "$T/row19_screen/ec2/activation_e1.json" ] || die "epoch 1 is not activated (v16 relies on the existing e1 proof)"
"$T/t1py" -c 'import json, sys
ph = [x for x in json.load(open("chpc/row19_screen_budget.json"))["phases"] if not x.get("retired")]
led = json.load(open(sys.argv[1]))
print("budget phases: last", ph[-1]["cap_core_h"], "pending", bool(ph[-1].get("pending")), "; ledger cap", led.get("cap_core_h"))
sys.exit(0 if not ph[-1].get("pending") and led.get("cap_core_h") == ph[-1]["cap_core_h"] == 60000.0 else 1)' "$T/row19_screen_campaign/budget.json" \
  || die "a cap phase is pending, or the ledger cap is not the committed 60,000 phase (the raise belongs to step 5, after deploy), or the budget files do not read"
archive_py inventory "$T" || die "the archive sources are incomplete (above)"
sci=$(sci_manifest) || { printf '%s\n' "$sci"; die "the job-clone science proof is incomplete"; }
printf '%s\n' "$sci" | cut -c1-12,65-
echo "lengau preflight OK"
REMOTE
echo "PREFLIGHT OK: drain confirmed for this instant only - keep the coordinated admission hold (refill scripts and slot watcher stopped, no controller command) through step 8; refills resume only after the step-9 scale-up adoption"
