# Migration v17 -> v18, the READ-ONLY Lengau check before the fresh v18 receipts (step 5; sourced through lengau.sh by
# receipts_v18.sh). Writes nothing. It refuses unless v18 is the deployed, adopted controller (controls 452b82df, the
# version-18 adoption naming the v17 record 61ca680e, deploy proof DONE and its commit in HEAD's history, ctl_clean), epoch 2 is
# STILL the canonical activation under the adopted v18 (activation_e2.json; activation_e1.json kept) and the captured node
# document of refit job 54 is exactly 730ea262 where the v18 status view fetches it.
[ "${V18_PRELUDE:-}" = 1 ] || { echo "sourced through lengau.sh by receipts_v18.sh only"; exit 1; }
[ "$NP" = 0 ] || die "check_v18.sh takes no payload"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
v18_adopted
deploy_done
act2_valid
node_ev
echo "lengau check OK: v18 deployed and adopted, deploy proof DONE, epoch 2 still active, node document 730ea262 in place"
