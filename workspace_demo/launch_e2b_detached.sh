#!/usr/bin/env bash
# Launch the E2b collapse-boundary run + caffeinate fully detached.
# Console -> runs/e2b_console.log; data -> runs/e2b_collapse.jsonl.
# Usage: launch_e2b_detached.sh [n_sessions]   (default 10; atomic-session
# resume skips sessions already complete in the jsonl)
set -u
SESSIONS="${1:-10}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HERE/runs"
nohup caffeinate -sim >/dev/null 2>&1 &
echo "caffeinate pid $!"
cd "$HERE"
nohup python3 -u e2b_collapse.py --sessions "$SESSIONS" \
  >>"$HERE/runs/e2b_console.log" 2>&1 &
echo "e2b pid $!"
