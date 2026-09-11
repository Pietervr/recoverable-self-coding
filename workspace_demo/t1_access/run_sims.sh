#!/bin/sh
# t1_access/run_sims.sh — the first simulation pass (§7.5 recovery grid, §10 calibration and power), sized
# by bench.py (2026-09-11, single-threaded: one dataset-layer of the full §8 procedure ≈ 7 min on one
# core at D = 4, 8 starts everywhere; ~1.7x at D = 8). Two chains: A on NJOBS workers, B (the gain
# calibration) on one. At 14 workers the whole script is ≈ 20 h.
#
#   NJOBS=14 nohup sh run_sims.sh > sim_results/logs/run_sims.log 2>&1 &
#
# Every task appends to its CSV as chunks complete and skips replicates already present, so a killed
# chain is resumed by running the same command again.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PY="$HERE/.venv/bin/python"
OUT="$HERE/sim_results"
LOG="$OUT/logs"
NJOBS="${NJOBS:-14}"
mkdir -p "$LOG"
cd "$HERE"

echo "start $(date)"

# chain B: the §10 gain calibration (four mixture members x three gains), one worker, in the background
( "$PY" simulate.py gain --seed 2026 > "$LOG/gain.log" 2>&1 && touch "$OUT/gain_calibration.done" ) &

# chain A
echo "calibration D4 $(date)"
"$PY" simulate.py calibration --n-rep 40 --D 4 --layers 41 --n-jobs "$NJOBS" --seed 2026 > "$LOG/calibration_D4.log" 2>&1

echo "waiting for the gain calibration $(date)"
while [ ! -f "$OUT/gain_calibration.done" ]; do sleep 60; done

echo "power D4 $(date)"
"$PY" simulate.py power --n-rep 40 --D 4 --layers 41 --n-jobs "$NJOBS" --seed 2026 > "$LOG/power_D4.log" 2>&1

echo "recovery D4 $(date)"
"$PY" simulate.py recovery --n-rep 10 --D 4 --layers 41 --n-jobs "$NJOBS" --seed 2026 > "$LOG/recovery_D4.log" 2>&1

echo "power D8 $(date)"
"$PY" simulate.py power --n-rep 20 --D 8 --layers 41 --n-jobs "$NJOBS" --seed 2026 > "$LOG/power_D8.log" 2>&1

echo "calibration D8 $(date)"
"$PY" simulate.py calibration --n-rep 20 --D 8 --layers 41 --n-jobs "$NJOBS" --seed 2026 > "$LOG/calibration_D8.log" 2>&1

# the layer-averaging check: two nulls and two alternatives on the five-layer grid
echo "five-layer check $(date)"
"$PY" simulate.py calibration --n-rep 20 --D 4 --n-jobs "$NJOBS" --seed 2026 --generators M2B,M2K \
      --out "$OUT/calibration_D4_5layers.csv" > "$LOG/calibration_D4_5layers.log" 2>&1
"$PY" simulate.py power --n-rep 20 --D 4 --n-jobs "$NJOBS" --seed 2026 --generators M3H,M3V \
      --out "$OUT/power_D4_5layers.csv" > "$LOG/power_D4_5layers.log" 2>&1

echo "done $(date)"
