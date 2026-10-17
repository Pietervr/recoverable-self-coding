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
#          the job clone's science bytes are printed.
# Usage (from workspace_demo/t1_access):  bash chpc/migration_v16/preflight_v16.sh [--local-only]
#   --local-only   the Mac checks only (no ssh); the migration still needs a full run.
# Test hook: V16_FAKE_LENGAU=<dir containing FAKE_LENGAU> runs the Lengau body locally against that fake toolchain.
set -u
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
git show "HEAD:./$REC" | grep -qxF "$LIT" || fail "the committed review record does not carry the exact line: $LIT"
# -- Mac pilot qualification and archive --
want chpc/results/row19_screen/receipts/qualified_refit_job1.json 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c
[ ! -e chpc/results/archive/row19_screen_v15_before_v16 ] || fail "the Mac archive row19_screen_v15_before_v16 already exists (migration started before?)"
# -- Mac drain: no refill, slot watcher or controller command of this user --
p=$(ps -x -o args= | grep -E "refill_(r1|b1)\.sh|slot_watch\.sh|row19_screen_(admit|status|verify)\.py|row22_bank_(submit|status)\.py|row19_ec2_|row19_partition\.py" | grep -v grep)
[ -z "$p" ] || { echo "$p"; fail "a refill, slot-watch or controller command runs on the Mac (above)"; }
echo "mac preflight OK"
[ "${1:-}" = "--local-only" ] && { echo "PREFLIGHT (Mac only) OK - the Lengau checks were NOT run; run without --local-only before step 2"; exit 0; }
if [ -n "${V16_FAKE_LENGAU:-}" ]; then
  [ -e "$V16_FAKE_LENGAU/FAKE_LENGAU" ] || fail "V16_FAKE_LENGAU has no FAKE_LENGAU marker"
  remote() { env V16_T="$V16_FAKE_LENGAU" bash -s; }
else
  remote() { ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s; }
fi
remote <<'REMOTE' || fail "Lengau checks failed (above)"
if [ -n "${V16_T:-}" ]; then [ -e "$V16_T/FAKE_LENGAU" ] || { echo "V16_T is a test hook and needs a FAKE_LENGAU marker"; exit 1; }; T=$V16_T; else T=/mnt/lustre/users/pvanrooyen/t1_toolchain; fi
C=$T/rsc_screen_ctl/workspace_demo/t1_access; J=$T/rsc_screen/workspace_demo/t1_access; G=$T/row19_screen/gate
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition" | grep -v grep)
[ -n "$p" ] && { echo "controller command running on the login node:"; echo "$p"; exit 1; }
for L in $T/programme_admission.lock $T/row19_screen/plans/.submit.lock; do
  [ -e $L ] || continue
  if command -v flock >/dev/null 2>&1; then flock -n -s $L true || { echo "lock held: $L"; exit 1; }
  else echo "WARN: flock(1) unavailable; $L not probed (the process check above stands)"; fi
done
cd $C || exit 1
[ -z "$(git status --short)" ] || { echo "controller clone has uncommitted changes"; exit 1; }
chk() { [ "$(sha256sum $1 | cut -c1-64)" = $2 ] || { echo "controller clone $1 is not adopted v15 ($2)"; exit 1; }; }
chk chpc/row19_screen_controls.json 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5
chk chpc/row19_screen_controls_adoption.json 970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d
chk chpc/row19_screen_admit.py ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac
chk chpc/row19_screen_status.py 0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b
[ ! -e chpc/row19_screen_designated.json ] || { echo "controller clone already has the designated declaration"; exit 1; }
[ "$(sha256sum $G/qualified_refit_job1.json | cut -c1-64)" = 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c ] || { echo "gate qualification is not the adopted v15 3c605514"; exit 1; }
[ -e $G/review_refit.json ] || { echo "no active gate review_refit.json"; exit 1; }
[ ! -e $G/scaleup_refit_v16.json ] || { echo "a v16 scale-up adoption already exists"; exit 1; }
[ ! -e $T/row19_screen/gate_retired/review_refit.v15_qual3c605514_max100.json ] || { echo "the v15 review is already retired"; exit 1; }
[ ! -e $T/archive_screen/v15_before_v16 ] || { echo "archive v15_before_v16 already exists (migration started before?)"; exit 1; }
[ -e $T/row19_screen/ec2/activation_e1.json ] || { echo "epoch 1 is not activated (v16 relies on the existing e1 proof)"; exit 1; }
$T/t1py -c 'import json, sys
ph = [x for x in json.load(open("chpc/row19_screen_budget.json"))["phases"] if not x.get("retired")]
led = json.load(open(sys.argv[1]))
print("budget phases: last", ph[-1]["cap_core_h"], "pending", bool(ph[-1].get("pending")), "; ledger cap", led.get("cap_core_h"))
sys.exit(0 if not ph[-1].get("pending") and led.get("cap_core_h") == ph[-1]["cap_core_h"] == 60000.0 else 1)' $T/row19_screen_campaign/budget.json \
  || { echo "a cap phase is pending, or the ledger cap is not the committed 60,000 phase (the raise belongs to step 5, after deploy)"; exit 1; }
cd $J && sha256sum chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py | cut -c1-12,65-
echo "lengau preflight OK"
REMOTE
echo "PREFLIGHT OK: drain confirmed for this instant - keep the refill scripts and the slot watcher stopped; refills resume only after the step-9 scale-up adoption"
