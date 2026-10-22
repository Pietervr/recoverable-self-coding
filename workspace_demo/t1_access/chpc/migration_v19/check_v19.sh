# Migration v18 -> v19, the READ-ONLY Lengau check before the fresh v19 receipts (step 5; sourced through lengau.sh by
# receipts_v19.sh). Writes nothing. It refuses unless v19 is the deployed, adopted controller (controls 111c3107, the
# version-19 adoption naming the v18 record 3e1fe9a1, deploy proof DONE and its commit in HEAD's history, ctl_clean), epoch 2 is
# STILL the canonical activation under the adopted v19 (activation_e2.json; activation_e1.json kept) and the captured node
# document of refit job 54 is exactly 730ea262 where the v19 status view fetches it (job 54 stays node-dispositioned).
[ "${V19_PRELUDE:-}" = 1 ] || { echo "sourced through lengau.sh by receipts_v19.sh only"; exit 1; }
[ "$NP" = 0 ] || die "check_v19.sh takes no payload"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
v19_adopted
deploy_done
act2_valid
node_ev
echo "lengau check OK: v19 deployed and adopted, deploy proof DONE, epoch 2 still active, node document 730ea262 in place"
