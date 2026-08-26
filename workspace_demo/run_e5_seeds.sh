#!/usr/bin/env bash
# run_e5_seeds.sh — run E5 realizations (both arms per seed) sequentially.
# Usage: run_e5_seeds.sh [seed ...]   (default: 0 1)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEEDS=("${@:-}")
if [ ${#SEEDS[@]} -eq 0 ] || [ -z "${SEEDS[0]}" ]; then
  SEEDS=(0 1)
fi
mkdir -p "$HERE/runs"
cd "$HERE"
for s in "${SEEDS[@]}"; do
  echo "===== E5 seed $s start $(date) ====="
  python3 -u e5_emergent.py --seed "$s" || echo "SEED $s FAILED (continuing)"
done
echo "===== E5 ALL SEEDS DONE $(date) ====="
