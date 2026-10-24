#!/bin/bash
# The S2 closure under the corrected code, on one 96-core instance (Codex S3 review 24 Oct 2026, findings 9, 12, 14):
# the declared development scope W2/T1/O1 at R = 25, the §4 node/rank/small-spread checks, the corrected basin check,
# the corrected two-vs-four-start profile validation, and the recovery check rerun with its oracle-Sigma variant.
# Run from the jitter directory inside the bundle, with the venv active. Results land under results/s2 (synced to S3 by
# the user-data loop). usage: bash aws/s2_closure.sh <workers>
set -uo pipefail
W=${1:-96}
LOG=results/s2/closure_log.txt
mkdir -p results/s2
echo "[closure] start $(date -u +%FT%TZ) workers $W code $(python - <<'EOF'
import models; print(models.code_hash())
EOF
)" | tee -a "$LOG"
for S in W2 T1 O1; do
  echo "[closure] decision $S 0-24 start $(date -u +%T)" | tee -a "$LOG"
  python s2.py decision --setting $S --R 25 --sets 0-24 --workers "$W" > "results/s2/closure_decision_$S.log" 2>&1
  echo "[closure] decision $S rc=$? $(date -u +%T)" | tee -a "$LOG"
done
python s2.py summary > results/s2/closure_summary.log 2>&1
echo "[closure] summary rc=$? $(date -u +%T)" | tee -a "$LOG"
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
echo "[closure] done $(date -u +%FT%TZ)" | tee -a "$LOG"
