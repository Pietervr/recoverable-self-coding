#!/bin/zsh
# Refitting-bootstrap coverage probe on the Mac (13 Sept 2026): M2S omega 2 and 1, 20 new-seed datasets each,
# 50 resamples per dataset, one layer (41), inner starts 4, 11 workers, detached with nohup so the harness's
# low-memory heuristic cannot kill it (the same way the twelve-pair gain run was launched). ~2 days.
T1=/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access
OUT=$T1/sim_results/refit_probe_3ca9304
mkdir -p "$OUT"
export NPROC=1
nohup "$T1/.venv/bin/python" "$T1/probe_refit.py" --points "M2S:omega=2.0,M2S:omega=1.0" --n-rep 20 --n-boot-refit 50 \
  --seed 2027 --layers 41 --n-starts-inner 4 --n-jobs 11 --out "$OUT" > "$OUT/probe.log" 2>&1 &
echo "launched pid $! -> $OUT/probe.log"
