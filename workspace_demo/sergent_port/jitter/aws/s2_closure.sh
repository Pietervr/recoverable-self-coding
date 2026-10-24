#!/bin/bash
# The S2 closure under the corrected code (Codex S3 review 24 Oct 2026, findings 9, 12, 14): the declared development
# scope W2/T1/O1 at R = 25, the §4 node/rank/small-spread checks, the corrected basin check, the corrected two-vs-four-
# start profile validation, and the recovery check rerun with its oracle-Sigma variant.
# Run from the jitter directory inside the bundle, with the venv active. Results land under results/s2 (synced to S3 by
# the user-data loop every 5 min; a relaunch resumes from the synced per-task and per-set files).
#   usage: bash aws/s2_closure.sh <workers> [all | W2 | T1 | O1 | checks]
# PARTS (24 Oct 2026, after the first instance ran the sets one at a time on 20 of 96 cores): one instance per part.
#   W2 / T1 / O1  the decision batch of that setting, all 25 sets in one queue (s2.run_decision), then its summary line
#   checks        waits for W2 set 0 on S3 (the node check refits it), then nodes, ranks, small-spread, basins, profiles,
#                 recovery rerun
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
  S=$1
  echo "[closure] decision $S 0-24 start $(date -u +%T)" | tee -a "$LOG"
  python s2.py decision --setting $S --R 25 --sets 0-24 --workers "$W" > "results/s2/closure_decision_$S.log" 2>&1
  echo "[closure] decision $S rc=$? $(date -u +%T)" | tee -a "$LOG"
}

checks() {
  # the node check refits W2 set 0 under three quadrature rules against the archived set 0: wait for it on S3
  if [ ! -f results/s2/decision/W2/set_0.json ]; then
    echo "[closure] waiting for W2 set 0 on S3 $(date -u +%T)" | tee -a "$LOG"
    until aws s3 cp "s3://${BUCKET:-xtenure-cself-pvr-usw2}/${RES:-results/t1_access/jitter_s4}/results/s2/decision/W2/set_0.json" results/s2/decision/W2/set_0.json --quiet 2>/dev/null; do sleep 120; done
    echo "[closure] W2 set 0 arrived $(date -u +%T)" | tee -a "$LOG"
  fi
  echo "[closure] checks nodes (W2 set 0) start $(date -u +%T)" | tee -a "$LOG"
  python s2.py checks --kind nodes --setting W2 --set 0 --workers "$W" > results/s2/closure_checks_nodes.log 2>&1
  echo "[closure] checks nodes rc=$? $(date -u +%T)" | tee -a "$LOG"
  python s2.py checks --kind ranks > results/s2/closure_checks_ranks.log 2>&1
  python s2.py checks --kind smallspread > results/s2/closure_checks_smallspread.log 2>&1
  echo "[closure] checks ranks/smallspread done $(date -u +%T)" | tee -a "$LOG"
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
  W2|T1|O1) decision "$PART" ;;
  checks)   checks ;;
  all)      for S in W2 T1 O1; do decision "$S"; done
            python s2.py summary > results/s2/closure_summary.log 2>&1
            echo "[closure] summary rc=$? $(date -u +%T)" | tee -a "$LOG"
            checks ;;
  *)        echo "[closure] unknown part $PART" | tee -a "$LOG"; exit 2 ;;
esac
echo "[closure] done $(date -u +%FT%TZ)" | tee -a "$LOG"
