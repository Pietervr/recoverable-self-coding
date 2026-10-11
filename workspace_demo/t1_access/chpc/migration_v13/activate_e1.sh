#!/bin/bash
# Migration step 5 (Lengau; ssh -o ControlPath=none lengau bash -s < chpc/migration_v13/activate_e1.sh).
# Canonical epoch-1 activation under the screen's plan lock (row19_partition.py activate: the actual all-state claim scan
# over completed records and every historical/planned/reserved Lengau claim, malformed plans = unknown claims), with the
# ADOPTED v13 controls. Immutable: refuses when the proof exists. Prints counts only.
T=/mnt/lustre/users/pvanrooyen/t1_toolchain; C=$T/rsc_screen_ctl/workspace_demo/t1_access
cd $C || exit 1
grep -q '"version": 13' chpc/row19_screen_controls_adoption.json || { echo "v13 is not the adopted controls here"; exit 1; }
[ "$(sha256sum chpc/row19_screen_controls.json | cut -c1-64)" = 840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c ] || { echo "controls are not 840840f5"; exit 1; }
[ "$(sha256sum chpc/row19_partition_e1.json | cut -c1-64)" = 8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608 ] || { echo "partition is not 8d1de408"; exit 1; }
p=$(ps -u pvanrooyen -o args | grep -E "row19_screen_(admit|status|verify)|row19_ec2_" | grep -v grep)
[ -n "$p" ] && { echo "controller command running:"; echo "$p"; exit 1; }
$T/t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json
