#!/usr/bin/env bash
# Launch the E2 run + caffeinate fully detached (survives terminal/session
# interruptions). Console -> runs/e2_console.log; data -> runs/e2_hysteresis.jsonl.
# Usage: launch_e2_detached.sh [n_sessions]   (default 3; resume skips
# sessions already complete in the jsonl)
set -u
SESSIONS="${1:-3}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HERE/runs"
nohup caffeinate -sim >/dev/null 2>&1 &
echo "caffeinate pid $!"
cd "$HERE"
nohup python3 -u e2_hysteresis.py --sessions "$SESSIONS" --kmax 48 --kstep 8 \
  --probe-k 16 >>"$HERE/runs/e2_console.log" 2>&1 &
echo "e2 pid $!"
