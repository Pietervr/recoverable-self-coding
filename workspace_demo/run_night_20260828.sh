#!/usr/bin/env bash
# The 2026-08-28 overnight chain, one detached process:
#   E7 seed 2 (precursors, ~2.2 h) -> E8 separatrix seed 0 (~4.5 h)
#   -> E9 cusp spot-checks seed 0 (~3 h)
# Each script has arm/phase-level resume, so re-running this chain after
# any failure continues where it left off. Console: runs/night_console.log.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
pgrep -f "caffeinate -sim" >/dev/null 2>&1 || { nohup caffeinate -sim >/dev/null 2>&1 & }
echo "=== NIGHT CHAIN start $(date) ==="
python3 -u e7_precursors_dwell.py --seed 2
echo "=== E7 seed 2 done $(date) ==="
python3 -u e8_separatrix.py --seed 0
echo "=== E8 done $(date) ==="
python3 -u e9_rig_spots.py --seed 0
echo "=== E9 spots done $(date) ==="
echo "=== NIGHT CHAIN complete $(date) ==="
