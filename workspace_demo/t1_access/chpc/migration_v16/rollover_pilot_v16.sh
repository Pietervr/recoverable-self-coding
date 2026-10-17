#!/bin/bash
# Migration v15 -> v16, step 7.1 (Lengau; ssh -o ControlPath=none lengau bash -s < chpc/migration_v16/rollover_pilot_v16.sh).
# The v13 rollover_pilot.sh pattern: retire the ACTIVE v15 refit review (qualification 3c605514, max 100; Codex RSC 66d1e99) to
# gate_retired/ ONLY after verifying that the v15_before_v16 archive verifies and holds byte-identical copies of it and of
# qualified_refit_job1.json, and that v16 is the deployed, adopted controller in rsc_screen_ctl. Admissions must be held (no
# controller command runs). Nothing is deleted; the 3c605514 authority stays historical. The next step (Mac, ONE call)
# regenerates the qualification from the EXISTING completed pilot job 1 under v16 - a NEW hash, no fit:
#   python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
# Test hook: V16_T=<dir containing FAKE_LENGAU> runs against that fake toolchain.
if [ -n "${V16_T:-}" ]; then [ -e "$V16_T/FAKE_LENGAU" ] || { echo "V16_T is a test hook and needs a FAKE_LENGAU marker"; exit 1; }; T=$V16_T; else T=/mnt/lustre/users/pvanrooyen/t1_toolchain; fi
G=$T/row19_screen/gate; R=$T/row19_screen/gate_retired; A=$T/archive_screen/v15_before_v16; C=$T/rsc_screen_ctl/workspace_demo/t1_access
OUT=$R/review_refit.v15_qual3c605514_max100.json
[ -e $OUT ] && { echo "retired file exists: $OUT"; exit 1; }
[ -e $G/review_refit.json ] || { echo "no active review_refit.json (already retired?)"; exit 1; }
[ "$(sha256sum $C/chpc/row19_screen_controls.json | cut -c1-64)" = 01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220 ] \
  && grep -q '"version": 16' $C/chpc/row19_screen_controls_adoption.json || { echo "v16 is not the deployed, adopted controller in rsc_screen_ctl (deploy_v16.sh first)"; exit 1; }
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition" | grep -v grep)
[ -n "$p" ] && { echo "controller command running:"; echo "$p"; exit 1; }
h=$(sha256sum $G/review_refit.json | cut -c1-64); a=$(grep ' ./gate/review_refit.json$' $A/SHA256SUMS | cut -c1-64)
q=$(sha256sum $G/qualified_refit_job1.json | cut -c1-64); qa=$(grep ' ./gate/qualified_refit_job1.json$' $A/SHA256SUMS | cut -c1-64)
echo "active review $h archived $a; qualification $q archived $qa"
[ -n "$a" ] && [ "$h" = "$a" ] || { echo "MISMATCH: active review is not the archived bytes"; exit 1; }
[ "$q" = 3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c ] && [ "$q" = "$qa" ] || { echo "qualification is not the archived 3c605514"; exit 1; }
grep -q '3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c' $G/review_refit.json || { echo "the active review is not bound to qualification 3c605514"; exit 1; }
(cd $A && sha256sum -c --quiet SHA256SUMS) || { echo "archive does not verify"; exit 1; }
mkdir -p $R && mv $G/review_refit.json $OUT && chmod a-w $OUT && echo "retired to $OUT"
