#!/bin/zsh
# Every 30 min: the status of the two 13 Sept cloud runs (the M2B refit control and the omega-2 reference bank),
# one line per job whose status changed or is not InProgress, plus a fleet count; exits never (persistent Monitor).
T1=/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access
PY=$T1/.venv/bin/python
prev=""
while true; do
  now=$($PY $T1/launch_t1.py --status 2>/dev/null | grep "refit-contro\|ref-m2s-omeg\|ref_m2s\|refit_control" | awk '{print $1, $2, $3, $5, $6, $7}')
  ts=$(date -u +%H:%MZ)
  echo "$now" | grep -v "InProgress" | grep -v '^$' | sed "s/^/[$ts] /"
  n_ip=$(echo "$now" | grep -c "InProgress")
  n_done=$(echo "$now" | grep -c "Completed")
  n_fail=$(echo "$now" | grep -c "Failed\|Stopped")
  if [[ "$now" != "$prev" ]]; then echo "[$ts] fleet: $n_ip InProgress, $n_done Completed, $n_fail Failed/Stopped"; fi
  prev="$now"
  sleep 1800
done
