#!/usr/bin/env bash
# Waits for the 2026-08-28 night chain (E7s2 -> E8 -> E9) to finish,
# then runs E10 (lens-free Llama loop) — never concurrent with the
# jlens rig (GPU contention). Detach with nohup.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
while pgrep -f run_night_20260828.sh >/dev/null 2>&1; do
  sleep 300
done
echo "=== night chain gone; starting E10 $(date) ==="
python3 -u e10_llama_loop.py --seed 0
echo "=== E10 done $(date) ==="
