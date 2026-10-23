# Migration v19 -> v20, the READ-ONLY Lengau check before the fresh v20 receipts (steps 5 and 7; sourced through lengau.sh by
# receipts_v20.sh with PHASE=pre or post). Writes nothing. It refuses unless v20 is the deployed, adopted controller (controls
# 4e64982b, the version-20 adoption naming the v19 record 2b9f3c78, deploy proof DONE and its commit in HEAD's history,
# ctl_clean), v20 pins the verified e3 closing declaration (e3_pinned), the e1/e2 activation proofs are unchanged (act2_kept),
# and - PHASE=pre - no activation_e3.json exists yet, or - PHASE=post - epoch 3 (the close) is THE canonical activation under the
# adopted v20 (act3_valid); and the captured node document of refit job 54 is exactly 730ea262 (job 54 stays node-dispositioned).
[ "${V20_PRELUDE:-}" = 1 ] || { echo "sourced through lengau.sh by receipts_v20.sh only"; exit 1; }
[ "$NP" = 0 ] || die "check_v20.sh takes no payload"
case ${PHASE:-} in pre|post) ;; *) die "check_v20.sh needs PHASE=pre (before the close) or post (after it)";; esac
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
v20_adopted
deploy_done
e3_pinned
act2_kept
if [ "$PHASE" = pre ]; then
  dst_absent "$ACT3" "$GS" "the epoch-3 activation (not yet: the close is step 6)"
else
  act3_valid
fi
node_ev
echo "lengau check OK ($PHASE-close): v20 deployed and adopted, deploy proof DONE, e3 pinned, e1/e2 proofs unchanged, $([ "$PHASE" = pre ] && echo 'no e3 activation yet' || echo 'epoch 3 (the close) THE canonical activation'), node document 730ea262 in place"
