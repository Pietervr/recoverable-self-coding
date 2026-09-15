#!/bin/zsh
# Every 30 min: the status of the two running M2B refit-control shards (refit_control_aac9f69, job suffix 1789338122);
# prints only when the job names/statuses change (not the growing hour counts), and exits once neither is InProgress.
T1=/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access
PY=$T1/.venv/bin/python
prev="$1"
while true; do
  now=$($PY $T1/launch_t1.py --status 2>/dev/null | grep "refit-contro.*1789338122" | awk '{print $1, $2, $3}')
  if [[ -n "$now" && "$now" != "$prev" ]]; then
    echo "$now" | sed "s/^/[$(date -u +%H:%MZ)] /"
    prev="$now"
  fi
  if [[ -n "$now" ]] && ! echo "$now" | grep -q "InProgress"; then
    echo "[$(date -u +%H:%MZ)] refit control: no shard InProgress; monitor exits"
    exit 0
  fi
  sleep 1800
done
