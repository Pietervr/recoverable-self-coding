#!/bin/bash
# Migration v20 -> v21, step 5 (Mac -> Lengau, then Mac): the refit ledger cap 81,000 -> 181,000 by the EXISTING two-phase
# protocol (row19_screen_admit.py --raise-cap, owner ruling as --note; the migration_v16 step-5 pattern), so the ledger cap
# never stops a HEAL1922 admission (DESIGN_v21.md s.4: the cap choice). The admission's raise path appends the pending phase to
# chpc/row19_screen_budget.json, raises the ledger cap (row19_ledger.raise_cap: old, new, note, time in cap_history), certifies
# it and commits the phase - under the programme lock, for the length of that one call. Then the phase file is committed in the
# controller clone, copied back to the Mac (checked by SHA-256) for the operator's explicit-path commit.
# Lengau, before the raise: the drain observed, both locks free, ctl_clean, v21 deployed and adopted (deploy proof DONE), the
# committed last phase 81,000 not pending and the ledger cap 81,000 - or, on a re-run, the committed last phase 181,000 and the
# ledger cap 181,000 with its cap_history entry (reported "already raised", nothing written).
# Usage (from workspace_demo/t1_access): bash chpc/migration_v21/raise_cap_v21.sh [--dry-run]
set -u -o pipefail
DRY=${1:-}
case $DRY in ""|--dry-run) ;; *) echo "RAISE REFUSED: unknown argument $DRY"; exit 3;; esac
fail() { echo "RAISE REFUSED: $*"; exit 3; }
[ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || fail "run from workspace_demo/t1_access"
python3 chpc/migration_v21/v21_package.py check-promoted || fail "the Mac promotion is not complete, committed and verified (above)"
NOTE="owner ruling 26 Oct 2026 (R052): once we are out of our own limit we go to HEAL1922; controls v21 funding route CSCI1913 100,000 then HEAL1922 100,000, refit+S sub-envelope 181,000 = 81,000 + HEAL1922 100,000 (chpc/candidate_v21_heal/DESIGN_v21.md s.4)"
[ "$DRY" = "--dry-run" ] && { echo "DRY RUN: would run on Lengau: row19_screen_admit.py --role refit --raise-cap 181000 --note \"$NOTE\", commit chpc/row19_screen_budget.json in the controller clone, copy it back"; exit 0; }
python3 chpc/migration_v21/v21_package.py drain || fail "the Mac drain is not observed (above)"
. chpc/migration_v21/lengau.sh || fail "cannot load chpc/migration_v21/lengau.sh"
OUTF=$(mktemp -t v21_raise) || fail "mktemp failed"
to_lengau - --var "NOTE=$NOTE" > "$OUTF" 2>&1 <<'REMOTE'
cd "$C" || die "no controller clone $C"
ctl_git
drained
locks_free
ctl_clean
v21_adopted
deploy_done
src_file "$C/chpc/row19_screen_budget.json" "$CR" "budget phases"; src_file "$T/row19_screen_campaign/budget.json" "$T/row19_screen_campaign" "refit ledger"
state=$("$T/t1py" -c 'import json, sys
ph = [x for x in json.load(open("chpc/row19_screen_budget.json"))["phases"] if not x.get("retired")]
led = json.load(open(sys.argv[1])); h = led.get("cap_history") or []
last, cap = ph[-1], led.get("cap_core_h")
if not last.get("pending") and last["cap_core_h"] == cap == float(sys.argv[2]):
    print("before")
elif not last.get("pending") and last["cap_core_h"] == cap == float(sys.argv[3]) and h and h[-1].get("new") == cap:
    print("done")
else:
    print("other phase %s pending %s ledger %s" % (last["cap_core_h"], last.get("pending"), cap))' "$T/row19_screen_campaign/budget.json" "$LEDGER_CAP" "$LEDGER_CAP_V21") \
  || die "the budget phases or the ledger do not read"
echo "cap state: $state"
case $state in
  before)
    dst_file "$C/chpc/row19_screen_budget.json" "$CR" "budget phases (the raise writes them)"
    "$T/t1py" chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --raise-cap "$LEDGER_CAP_V21" --note "$NOTE" \
      || die "the two-phase raise refused or failed (above); resume with the same command or retire the pending phase (--retire-pending)"
    git add -- chpc/row19_screen_budget.json && git -c user.name=R052 -c user.email=r052@local commit -q -m "screen budget: refit cap phase 181,000 (two-phase --raise-cap, owner ruling 26 Oct 2026: CSCI1913 first, then HEAL1922; controls v21)" -- chpc/row19_screen_budget.json \
      || die "git commit of the budget phases failed (the clone may be dirty: recover explicitly)"
    ;;
  done) echo "already raised: the committed last phase and the ledger cap are 181,000 with its cap_history entry";;
  *) die "unexpected cap state ($state); inspect by hand";;
esac
ctl_clean
git log -1 --format='ctl %h' -- chpc/row19_screen_budget.json || die "git log failed"
echo "budget=$(h chpc/row19_screen_budget.json)"
"$T/t1py" -c 'import json, sys; led = json.load(open(sys.argv[1])); print("ledger cap %s; latest cap_history %s" % (led["cap_core_h"], (led.get("cap_history") or [None])[-1]))' "$T/row19_screen_campaign/budget.json"
route_live
echo "lengau raise body complete"
REMOTE
rc=$?
OUT=$(cat "$OUTF"); rm -f "$OUTF"; printf '%s\n' "$OUT"
[ $rc = 0 ] || fail "the Lengau half exited $rc (above)"
printf '%s\n' "$OUT" | grep -qx "lengau raise body complete" || fail "the remote half did not complete"
B=$(printf '%s\n' "$OUT" | sed -n 's/^budget=\([0-9a-f]\{64\}\)$/\1/p' | tail -1); [ ${#B} = 64 ] || fail "no budget digest reported"
TMPB=$(mktemp -t v21_budget) || fail "mktemp failed"
scp -q -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau:/mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access/chpc/row19_screen_budget.json "$TMPB" \
  || fail "cannot copy the committed budget phases back"
[ "$(shasum -a 256 "$TMPB" | cut -c1-64)" = "$B" ] || { rm -f "$TMPB"; fail "the copied budget phases are not the committed ${B:0:16}"; }
cp "$TMPB" chpc/row19_screen_budget.json && rm -f "$TMPB" || fail "cannot write chpc/row19_screen_budget.json"
echo "RAISE OK - chpc/row19_screen_budget.json is the controller clone's committed phase file (${B:0:16}); commit it on the Mac with an explicit path"
