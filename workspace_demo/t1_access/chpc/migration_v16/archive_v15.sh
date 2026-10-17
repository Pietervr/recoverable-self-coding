#!/bin/bash
# Migration v15 -> v16, step 2 (Mac -> Lengau, then Mac): immutable archives of the ACTUALLY ADOPTED v15 state BEFORE anything
# changes. Each refuses to overwrite: an existing archive whose SHA256SUMS verifies is reported and left as it is (a re-run after
# an interruption between the two halves); an existing archive without a verifying SHA256SUMS refuses.
#  a. Lengau $T/archive_screen/v15_before_v16/{gate,jobs,ctl,ledger} (v13 archive_v9.sh + v15 deploy pattern): the WHOLE gate
#     (qualified_refit_job1.json 3c605514, the active review_refit.json, every watch/verify receipt, every retained PBS out/err
#     copy), the refit job scripts, the v15 controller files of rsc_screen_ctl and its HEAD, the controller clone's budget phases
#     chpc/row19_screen_budget.json and the campaign ledger row19_screen_campaign/budget.json (reference copies only).
#     Refuses unless the controller clone is clean at the v15 bytes, the gate qualification is 3c605514, a review is active and
#     no controller command runs.
#  b. Mac chpc/results/archive/row19_screen_v15_before_v16/: the v15 controls, adoption, admission, status, the budget phases
#     and the Mac copy of qualified_refit_job1.json (3c605514), with SHA256SUMS, read-only. promote_v16.py requires it.
# Usage (from workspace_demo/t1_access): bash chpc/migration_v16/archive_v15.sh [--dry-run]
#   --dry-run   the Mac checks and the plan only: no ssh, nothing written.
# Test hook: V16_FAKE_LENGAU=<dir containing FAKE_LENGAU> runs the Lengau half locally against that fake toolchain.
set -u
DRY=${1:-}
fail() { echo "ARCHIVE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
MA=chpc/results/archive/row19_screen_v15_before_v16
QUAL=chpc/results/row19_screen/receipts/qualified_refit_job1.json
MACF="chpc/row19_screen_controls.json chpc/row19_screen_controls_adoption.json chpc/row19_screen_admit.py chpc/row19_screen_status.py chpc/row19_screen_budget.json $QUAL"
want() { [ -e "$1" ] || fail "$1 is missing"; [ "$(shasum -a 256 "$1" | cut -c1-64)" = "$2" ] || fail "$1 is not $2"; }
mac_ok() {   # the Mac half is complete and verifies
  [ -e $MA/SHA256SUMS ] && (cd $MA && shasum -a 256 -c -s SHA256SUMS) || return 1
  [ "$(grep -c . $MA/SHA256SUMS)" = 6 ] && grep -q '^828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5  row19_screen_controls.json$' $MA/SHA256SUMS \
    && grep -q '^3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c  qualified_refit_job1.json$' $MA/SHA256SUMS
}
if [ -e $MA ]; then
  mac_ok || fail "$MA exists but does not verify as the complete v15 archive; not overwriting (inspect by hand)"
  MAC_DONE=1
else
  want chpc/row19_screen_controls.json 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5
  want chpc/row19_screen_controls_adoption.json 970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d
  want chpc/row19_screen_admit.py ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac
  want chpc/row19_screen_status.py 0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b
  want $QUAL 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c
  [ -e chpc/row19_screen_budget.json ] || fail "chpc/row19_screen_budget.json is missing"
  MAC_DONE=0
fi
if [ "$DRY" = "--dry-run" ]; then
  echo "DRY RUN - Mac checks pass; would:"
  echo "  - Lengau: create \$T/archive_screen/v15_before_v16/{gate,jobs,ctl,ledger} + SHA256SUMS, read-only (or verify an existing one)"
  [ $MAC_DONE = 1 ] && echo "  - Mac: $MA exists and verifies; left as it is" || echo "  - Mac: create $MA ($(echo $MACF | wc -w | tr -d ' ') files + SHA256SUMS), read-only"
  exit 0
fi
if [ -n "${V16_FAKE_LENGAU:-}" ]; then
  [ -e "$V16_FAKE_LENGAU/FAKE_LENGAU" ] || fail "V16_FAKE_LENGAU has no FAKE_LENGAU marker"
  remote() { env V16_T="$V16_FAKE_LENGAU" bash -s; }
else
  remote() { ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s; }
fi
echo "== a. Lengau"
remote <<'REMOTE' || fail "the Lengau archive failed (above); the Mac archive was not written"
if [ -n "${V16_T:-}" ]; then [ -e "$V16_T/FAKE_LENGAU" ] || { echo "V16_T is a test hook and needs a FAKE_LENGAU marker"; exit 1; }; T=$V16_T; else T=/mnt/lustre/users/pvanrooyen/t1_toolchain; fi
A=$T/archive_screen/v15_before_v16; C=$T/rsc_screen_ctl/workspace_demo/t1_access; G=$T/row19_screen/gate
if [ -e "$A" ]; then
  [ -e $A/SHA256SUMS ] && (cd $A && sha256sum -c --quiet SHA256SUMS) && grep -q '^3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c  ./gate/qualified_refit_job1.json$' $A/SHA256SUMS \
    || { echo "archive exists and does not verify, not overwriting: $A"; exit 1; }
  echo "archive exists and verifies, left as it is: $A $(wc -l < $A/SHA256SUMS) files SHA256SUMS $(sha256sum $A/SHA256SUMS | cut -c1-16)"; exit 0
fi
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition" | grep -v grep)
[ -n "$p" ] && { echo "controller command running on the login node:"; echo "$p"; exit 1; }
cd $C || exit 1
[ -z "$(git status --short)" ] || { echo "controller clone not clean"; exit 1; }
[ "$(sha256sum chpc/row19_screen_controls.json | cut -c1-64)" = 828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5 ] || { echo "controller clone controls are not adopted v15"; exit 1; }
[ "$(sha256sum chpc/row19_screen_controls_adoption.json | cut -c1-64)" = 970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d ] || { echo "controller clone adoption is not the v15 record"; exit 1; }
[ "$(sha256sum $G/qualified_refit_job1.json | cut -c1-64)" = 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c ] || { echo "gate qualification is not 3c605514"; exit 1; }
[ -e $G/review_refit.json ] || { echo "no active gate review_refit.json"; exit 1; }
mkdir -p $A/gate $A/jobs $A/ctl $A/ledger || exit 1
cp -pR $G/. $A/gate/ || exit 1
for j in $T/jobs/row19_screen_refit_*; do [ -e "$j" ] && { cp -p "$j" $A/jobs/ || exit 1; }; done
for f in row19_screen_controls.json row19_screen_controls_adoption.json row19_screen_admit.py row19_screen_status.py row19_screen_verify.py programme_gate.py row19_screen_release.py row19_screen_resources.json row19_screen_budget.json row22_bank_status.py row22_bank_submit.py; do
  [ -e chpc/$f ] && { cp -p chpc/$f $A/ctl/ || exit 1; }
done
git log -1 --format='rsc_screen_ctl HEAD %H' > $A/ctl/HEAD.txt
cp -p $T/row19_screen_campaign/budget.json $A/ledger/row19_screen_campaign_budget.json || exit 1
(cd $A && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
find $A -type f -exec chmod a-w {} +
echo "archive $A $(wc -l < $A/SHA256SUMS) files SHA256SUMS $(sha256sum $A/SHA256SUMS | cut -c1-16)"
grep -E "gate/(qualified|review)_refit|ctl/row19_screen_(controls|status|admit)|ledger/" $A/SHA256SUMS | cut -c1-16,65-
REMOTE
echo "== b. Mac"
if [ $MAC_DONE = 1 ]; then
  echo "Mac archive exists and verifies, left as it is: $MA SHA256SUMS $(shasum -a 256 $MA/SHA256SUMS | cut -c1-16)"
else
  mkdir -p $MA || fail "cannot create $MA"
  for f in $MACF; do cp -p "$f" $MA/ || fail "copy $f"; done
  (cd $MA && shasum -a 256 $(ls | grep -v '^SHA256SUMS$' | sort) > SHA256SUMS)
  chmod a-w $MA/*
  mac_ok || fail "the new Mac archive does not verify"
  echo "Mac archive $MA $(grep -c . $MA/SHA256SUMS) files SHA256SUMS $(shasum -a 256 $MA/SHA256SUMS | cut -c1-16)"
  cut -c1-16,65- $MA/SHA256SUMS
fi
echo "ARCHIVE OK - commit the Mac archive with explicit paths together with the promotion (step 3)"
