#!/usr/bin/env bash
# run_e4_seeds.sh — run E4 realizations for the given seeds, sequentially,
# appending to runs/e4_loop.jsonl (arm resume is (alpha, seed)-aware).
# Usage: run_e4_seeds.sh [seed ...]   (default: 1 2 3)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEEDS=("${@:-}")
if [ ${#SEEDS[@]} -eq 0 ] || [ -z "${SEEDS[0]}" ]; then
  SEEDS=(1 2 3)
fi
mkdir -p "$HERE/runs"
cd "$HERE"
for s in "${SEEDS[@]}"; do
  echo "===== E4 seed $s start $(date) ====="
  python3 -u e4_loop_collapse.py --seed "$s" || echo "SEED $s FAILED (continuing)"
done
echo "===== ALL SEEDS DONE $(date) ====="
