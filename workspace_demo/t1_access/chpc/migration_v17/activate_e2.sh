# Migration v16 -> v17, step 6 (Lengau body; run from workspace_demo/t1_access on the Mac as
#   bash chpc/migration_v17/lengau.sh activate_e2.sh
# which prepends remote_lib.sh: the fixed toolchain root, containment, drain, lock and proof checks).
# The CANONICAL epoch-2 activation (DESIGN_e2.md s.6 step 6, DESIGN_v17.md s.6 step 6): the reviewed command
#   $T/t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json
# run in the controller clone. That command takes the common plan lock itself (non-blocking: a held lock is "HELD", exit 3) and
# refuses, writing nothing, unless the adopted canonical controls pin e2 48cea639, the e1 activation is on the root and names
# e1, the root's INSTALLED authority inventory is fresh (sealed within 6 h) with no owner outside the e2 owned set and no live
# attempt of another epoch, the EC2 history is clean and no Lengau claim lies on an owned coordinate. This body adds, before it:
# v17 is the deployed, adopted controller (deploy proof DONE and its commit in HEAD's history, ctl_clean, the e2 partition at
# 48cea639), the drain observed (checked process inventory, both locks probed free), the activation destination contained (its
# own physical path in $T/row19_screen/ec2, absent) and the read-only inventory precheck (the same 6 h rule, so a stale
# inventory refuses before the activation is attempted); and after it: the written proof is THE canonical activation of e2
# under the adopted v17 (row19_partition.activation_problem in mode canonical) and the printed sha256 is its sha256.
# Re-run: an existing activation_e2.json is verified and reported "already activated" (exit 0) - the completed state, also after
# an interruption between the proof's link and the command's report. An existing proof that does not verify refuses. A refused
# activation is reported verbatim and changes nothing; never erase a claim, never edit a proof, never re-snapshot by hand: a
# claim on an owned coordinate means re-snapshot, re-declare and re-review (DESIGN_v17 s.6 step 6). The e1 proof stays on the
# root as provenance. Nothing here touches a worker, reaper or the scientific clone.
[ "${V17_PRELUDE:-}" = 1 ] || { echo "run through: bash chpc/migration_v17/lengau.sh activate_e2.sh"; exit 1; }
[ "$NP" = 0 ] || die "activate_e2.sh takes no payload"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
v17_adopted
deploy_done
src_file "$C/chpc/row19_partition_e2.json" "$CR" "the e2 partition"; pin chpc/row19_partition_e2.json $E2_PART "the e2 partition (48cea639)"
src_file "$ACT1" "$GS" "epoch-1 activation proof"
if [ -e "$ACT2" ] || [ -L "$ACT2" ]; then
  act2_valid
  echo "ALREADY ACTIVATED (verified): $ACT2 sha256 $(h "$ACT2") - the completed state; nothing written"
  exit 0
fi
drained
locks_free
"$T/t1py" -c 'import sys; sys.path.insert(0, "chpc"); import programme_gate as PG
w = PG.lineage_problem(); print("controller lineage %r" % w); sys.exit(1 if w else 0)' || die "the controller lineage is not v17's (above)"
"$T/t1py" -c "$INV_PY" "$GS" chpc/row19_screen_manifest.json chpc/row19_partition_e2.json \
  || die "the installed inventory does not admit the activation (above): run 'bash chpc/migration_v17/ec2_cycle_v17.sh pre-activation' first; nothing was written"
dst_dir "$EC2" "$GS" "the ec2 directory"; dst_absent "$ACT2" "$GS" "the epoch-2 activation proof"
echo "running the canonical activation (the command takes the plan lock itself)"
OUTF=$(mktemp) || die "mktemp failed"
"$T/t1py" chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json > "$OUTF" 2>&1; rc=$?
cat "$OUTF"
if [ $rc != 0 ]; then
  rm -f "$OUTF"
  [ -e "$ACT2" ] || [ -L "$ACT2" ] && die "the activation command exited $rc but $ACT2 now exists: re-run activate_e2.sh to verify it (never edit or remove it)"
  die "the canonical activation refused or failed (exit $rc, above): no activation was written; report it verbatim (a held plan lock: retry later; a stale inventory: a fresh pre-activation cycle; a claim on an owned coordinate: re-snapshot, re-declare, re-review - never erase a claim)"
fi
line=$(grep -E '^activated epoch 2: ' "$OUTF" | tail -1); rm -f "$OUTF"
[ -n "$line" ] || die "the activation command printed no 'activated epoch 2' line (above)"
act2_valid
[ "${line##* sha256 }" = "$(h "$ACT2")" ] || die "the activation printed sha256 ${line##* sha256 }, but $ACT2 is $(h "$ACT2")"
echo "ACTIVATED epoch 2: $ACT2 sha256 $(h "$ACT2") - Lengau refit admission no longer holds on the activation; it still needs current v17 receipts (step 7) and the new pilot adoption (step 8)"
