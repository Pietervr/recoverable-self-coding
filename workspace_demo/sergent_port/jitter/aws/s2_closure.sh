#!/bin/bash
# The S2 closure under the corrected code (Codex S3 review 24 Oct 2026, findings 9, 12, 14): the declared development
# scope W2/T1/O1 at R = 25, the §4 node/rank/small-spread checks, the corrected basin check, the corrected two-vs-four-
# start profile validation, and the recovery check rerun with its oracle-Sigma variant.
# Run from the jitter directory inside the bundle, with the venv active. Results land under results/s2 (synced to S3 by
# the user-data loop every 5 min; a relaunch resumes from the synced per-task and per-set files).
#   usage: bash aws/s2_closure.sh <workers> [all | W2 | T1 | O1 | checks | nodes | validators]
# PARTS (24 Oct 2026, after the first instance ran the sets one at a time on 20 of 96 cores): one instance per part.
#   W2 / T1 / O1  the decision batch of that setting, all 25 sets in one queue (s2.run_decision), then its summary line
#   nodes         waits for W2 set 0 on S3 (the node check refits it), then nodes, ranks, small-spread
#   validators    basins, the profile-start validation, the recovery rerun (no W2 set needed)
#   checks        nodes then validators on one host
#   all           everything in sequence (the original single-instance form)
set -uo pipefail
W=${1:-96}
PART=${2:-all}
LOG=results/s2/closure_log_$PART.txt
mkdir -p results/s2
echo "[closure] start $(date -u +%FT%TZ) part $PART workers $W code $(python - <<'EOF'
import models; print(models.code_hash())
EOF
)" | tee -a "$LOG"

decision() {
  S=$1; REV=${2:-}
  echo "[closure] decision $S 0-24 ${REV:+(reverse) }start $(date -u +%T)" | tee -a "$LOG"
  python s2.py decision --setting $S --R 25 --sets 0-24 --workers "$W" ${REV:+--reverse} > "results/s2/closure_decision_$S${REV:+_rev}.log" 2>&1
  echo "[closure] decision $S rc=$? $(date -u +%T)" | tee -a "$LOG"
}

checks() {
  # the node check refits W2 set 0 under three quadrature rules against the archived set 0. The W2 host writes
  # set_0.json only after its whole queue, but set 0's 20 task files land after its first round (the queue runs in set
  # order): wait for those on S3 and assemble set 0 here.
  S3W2="s3://${BUCKET:-xtenure-cself-pvr-usw2}/${RES:-results/t1_access/jitter_s4}/results/s2/decision/W2"
  if [ ! -f results/s2/decision/W2/set_0.json ]; then
    echo "[closure] waiting for W2 set 0 (set_0.json or its 20 task files) on S3 $(date -u +%T)" | tee -a "$LOG"
    while true; do
      aws s3 cp "$S3W2/set_0.json" results/s2/decision/W2/set_0.json --quiet 2>/dev/null && break
      N=$(aws s3 ls "$S3W2/tasks/" 2>/dev/null | grep -c 'set_0_m[0-9]*\.json$')
      if [ "$N" -ge 20 ]; then
        aws s3 sync "$S3W2/tasks" results/s2/decision/W2/tasks --quiet --exclude "*" --include "set_0_m*.json"
        python s2.py assemble --setting W2 --set 0 >> results/s2/closure_assemble.log 2>&1 && break
      fi
      sleep 120
    done
    echo "[closure] W2 set 0 in hand $(date -u +%T)" | tee -a "$LOG"
  fi
  echo "[closure] checks nodes (W2 set 0) start $(date -u +%T)" | tee -a "$LOG"
  python s2.py checks --kind nodes --setting W2 --set 0 --workers "$W" > results/s2/closure_checks_nodes.log 2>&1
  echo "[closure] checks nodes rc=$? $(date -u +%T)" | tee -a "$LOG"
  python s2.py checks --kind ranks > results/s2/closure_checks_ranks.log 2>&1
  python s2.py checks --kind smallspread > results/s2/closure_checks_smallspread.log 2>&1
  echo "[closure] checks ranks/smallspread done $(date -u +%T)" | tee -a "$LOG"
  [ "${1:-}" = "nodes_only" ] && return
  validators
}

validators() {
  # basins, the profile-start validation and the recovery rerun need no W2 set: a fifth host runs them beside the node
  # check (24 Oct 2026: one decision task = 1,513 s alone on the AMD core, 3.6x the Mac's sequential rate, so the
  # serial checks host would have been the closure's critical path)
  echo "[closure] basins start $(date -u +%T)" | tee -a "$LOG"
  python s2.py basins --workers "$W" > results/s2/closure_basins.log 2>&1
  echo "[closure] basins rc=$? $(date -u +%T)" | tee -a "$LOG"
  echo "[closure] profiles start $(date -u +%T)" | tee -a "$LOG"
  python s2.py profiles --n 100 --workers "$W" > results/s2/closure_profiles.log 2>&1
  echo "[closure] profiles rc=$? $(date -u +%T)" | tee -a "$LOG"
  echo "[closure] recovery check start $(date -u +%T)" | tee -a "$LOG"
  RECOVERY_TAG=final python results/s2/diagnosis/recovery_check.py 5 "$W" > results/s2/closure_recovery.log 2>&1
  echo "[closure] recovery rc=$? $(date -u +%T)" | tee -a "$LOG"
}

case "$PART" in
  W2|T1|O1)   decision "$PART" ;;
  W2-rev|T1-rev|O1-rev) decision "${PART%-rev}" reverse ;;    # a second host on the setting, from the far end of the set list
  checks)     checks ;;
  nodes)      checks nodes_only ;;
  validators) validators ;;
  all)      for S in W2 T1 O1; do decision "$S"; done
            python s2.py summary > results/s2/closure_summary.log 2>&1
            echo "[closure] summary rc=$? $(date -u +%T)" | tee -a "$LOG"
            checks ;;
  *)        echo "[closure] unknown part $PART" | tee -a "$LOG"; exit 2 ;;
esac
echo "[closure] done $(date -u +%FT%TZ)" | tee -a "$LOG"
