#!/usr/bin/env bash
# Generic detached rig launcher (survives terminal/session interrupts —
# two E7 arms were killed by session Ctrl-C before this existed).
# Usage: launch_rig_detached.sh <script.py> [args...]
# Console -> runs/<script-stem>_console.log; pid -> runs/<stem>.pid.
# Also starts a detached caffeinate (-sim) if none is running.
set -u
[ $# -ge 1 ] || { echo "usage: $0 <script.py> [args...]" >&2; exit 2; }
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$1"; shift
STEM="$(basename "$SCRIPT" .py)"
mkdir -p "$HERE/runs"
pgrep -f "caffeinate -sim" >/dev/null 2>&1 || {
  nohup caffeinate -sim >/dev/null 2>&1 &
  echo "caffeinate pid $!"
}
cd "$HERE"
nohup python3 -u "$SCRIPT" "$@" >>"$HERE/runs/${STEM}_console.log" 2>&1 &
PID=$!
echo "$PID" >"$HERE/runs/${STEM}.pid"
echo "$STEM pid $PID (console: runs/${STEM}_console.log)"
