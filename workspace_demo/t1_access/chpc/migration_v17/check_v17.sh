# Migration v16 -> v17, the READ-ONLY Lengau checks around the EC2 cycles (steps 5 and 7; sourced through lengau.sh by
# ec2_cycle_v17.sh with --var STAGE=...). Writes nothing.
#   STAGE=pre-before   before the pre-activation cycle: v17 is the deployed, adopted controller (deploy proof DONE, its commit in
#                      HEAD's history, ctl_clean) and the epoch-2 activation does NOT exist yet
#   STAGE=pre-after    after that cycle: the root's INSTALLED authority inventory is valid, sealed and fresh (< 6 h,
#                      row19_ec2_state.INVENTORY_MAX_AGE_S), no EC2 attempt owns a coordinate outside the e2 owned set and no
#                      live attempt of another epoch exists (the read-only mirror of row19_partition.handover_problems; the
#                      canonical activation re-checks all of it under the plan lock)
#   STAGE=post         after the activation: the root's activation_e2.json is THE canonical epoch-2 activation under the adopted v17
[ "${V17_PRELUDE:-}" = 1 ] || { echo "sourced through lengau.sh by ec2_cycle_v17.sh only"; exit 1; }
[ "$NP" = 0 ] || die "check_v17.sh takes no payload"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
v17_adopted
deploy_done
src_file "$ACT1" "$GS" "epoch-1 activation proof"
case ${STAGE:-} in
  pre-before)
    [ ! -e "$ACT2" ] && [ ! -L "$ACT2" ] || die "the epoch-2 activation already exists: this is not the pre-activation stage (run activate_e2.sh to verify it)"
    echo "lengau check (pre-before) OK: v17 deployed and adopted, deploy proof DONE, epoch 1 active, epoch 2 not yet activated";;
  pre-after)
    [ ! -e "$ACT2" ] && [ ! -L "$ACT2" ] || die "the epoch-2 activation already exists"
    "$T/t1py" -c "$INV_PY" "$GS" chpc/row19_screen_manifest.json chpc/row19_partition_e2.json \
      || die "the installed inventory does not admit the epoch-2 activation (above): disposition and fence outside owners first, or run a fresh cycle"
    echo "lengau check (pre-after) OK: a fresh installed inventory admits the epoch-2 activation";;
  post)
    act2_valid
    echo "lengau check (post) OK: the canonical epoch-2 activation is on the root";;
  *) die "unknown STAGE ${STAGE:-}";;
esac
