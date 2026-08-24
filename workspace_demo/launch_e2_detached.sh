#!/usr/bin/env bash
# Launch the E2 pilot + caffeinate fully detached (survives terminal/session
# interruptions). Console -> runs/e2_console.log; data -> runs/e2_hysteresis.jsonl.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HERE/runs"
nohup caffeinate -sim >/dev/null 2>&1 &
echo "caffeinate pid $!"
cd "$HERE"
nohup python3 e2_hysteresis.py --sessions 3 --kmax 48 --kstep 8 --probe-k 16 \
  >>"$HERE/runs/e2_console.log" 2>&1 &
echo "e2 pid $!"
