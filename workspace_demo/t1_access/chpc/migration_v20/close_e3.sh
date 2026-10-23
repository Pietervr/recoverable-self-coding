# Migration v19 -> v20, step 6 (Lengau body; sent by close_v20.sh through lengau.sh): THE EC2 CLOSE - the hand-back of the
# epoch-2 block to Lengau (owner decision 23 Oct 2026, route A; chpc/candidate_v20_handback/DESIGN_v20.md s.4).
# Refuses unless v20 is the deployed, ADOPTED controller (deploy proof DONE), the controller clone is clean, the adopted v20
# pins exactly the verified e3 closing declaration ca87fb1d (e3_pinned), the e1/e2 proofs are unchanged (act2_kept), the node
# document is in place, the drain is observed (checked process inventory, both locks probed free), the root's INSTALLED
# authority inventory is fresh (six hours) with no owner and no live or owning attempt, and e3 regenerates byte-equal from e2,
# the designated declaration and the root's OWN register (`row19_partition.py verify3`). Then ONE call:
#     $T/t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e3.json
# which takes the screen's plan lock itself (non-blocking: a held lock refuses with exit 3, nothing written), re-checks every
# close precondition under that lock (row19_partition.close_problems) and writes the immutable proof $EC2/activation_e3.json.
# Afterwards act3_valid (epoch 3 THE canonical activation under the adopted v20) and act2_kept again.
# Re-run: once activation_e3.json exists and verifies, the run reports "already closed" and exits 0; a proof that does not
# verify refuses (never overwritten or removed). Nothing else is written; no worker, reaper, plan, record or ledger is touched.
[ "${V20_PRELUDE:-}" = 1 ] || { echo "run through: bash chpc/migration_v20/close_v20.sh"; exit 1; }
[ "$NP" = 0 ] || die "close_e3.sh takes no payload"
cd "$C" || die "no controller clone $C"
ctl_git
ctl_clean
v20_adopted
deploy_done
e3_pinned
act2_kept
node_ev
if [ -e "$ACT3" ] || [ -L "$ACT3" ]; then
  act3_valid
  echo "already closed (verified): $ACT3 is THE canonical epoch-3 activation under the adopted v20; nothing written"
  echo "lengau close body complete"
  exit 0
fi
dst_absent "$ACT3" "$GS" "the epoch-3 activation proof"
drained
locks_free
"$T/t1py" -c 'import sys, time; sys.path.insert(0, "chpc"); import row19_ec2_state as ES
inv, why = ES.installed_inventory(sys.argv[1])
live = ES.live_attempts(inv) if inv else []
print("installed authority inventory: %s; generation %s, %.0f s old, owners %d, live or owning %s" % (
    why or "fresh", (inv or {}).get("generation"), time.time() - (inv or {}).get("at", 0), len((inv or {}).get("owners") or {}), live))
sys.exit(1 if (why or live or (inv or {}).get("owners")) else 0)' "$GS" \
  || die "the installed inventory is stale (over six hours) or still shows an owner or a live/owning attempt: run prod_authority.py inventory and ec2_sync.py cycle on the Mac (RUNBOOK step 0b/6), then re-run"
src_file "$EC2/register.json" "$GS" "the root's EC2 register"
"$T/t1py" chpc/row19_partition.py verify3 --manifest chpc/row19_screen_manifest.json --designated chpc/row19_screen_designated.json \
  --predecessor chpc/row19_partition_e2.json --register "$EC2/register.json" --partition chpc/row19_partition_e3.json \
  || die "e3 does not regenerate from e2, the designated declaration and the root's register (an EC2-completed coordinate?): re-declare, never edit"
"$T/t1py" chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e3.json; rc=$?
[ $rc = 0 ] || die "the close activation refused or failed (exit $rc, above); nothing was written unless it printed 'activated'"
act3_valid
act2_kept
node_ev
echo "CLOSED: epoch 3 activated - EC2 owns nothing, the 3,274 handed-back coordinates are Lengau-plannable; refit admission needs a fresh v20 receipt and the regenerated pilot adoption"
echo "lengau close body complete"
