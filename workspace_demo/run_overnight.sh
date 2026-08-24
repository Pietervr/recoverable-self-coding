#!/usr/bin/env bash
# run_overnight.sh — the unattended P0->P1->E1 chain, launched once the model
# and lens downloads have both landed. Each stage gates the next; everything
# logs to runs/overnight.log. Safe to re-run: stages skip work already done.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT_DIR="$HERE/upstream/jlens-qwen36"
NPZ="$PORT_DIR/data/lens/qwen36_27b_neuronpedia_n1000.npz"
LOG="$HERE/runs/overnight.log"
mkdir -p "$HERE/runs"
exec >>"$LOG" 2>&1
echo "===== run_overnight $(date) ====="

# 1. Convert the lens (skipped if the npz already exists)
if [ ! -f "$NPZ" ]; then
  echo "-- converting lens"
  HF_HUB_DISABLE_XET=1 uv run --directory "$PORT_DIR" --with torch python "$HERE/convert_lens.py" || { echo "FAIL convert"; exit 1; }
fi
echo "-- lens npz: $(ls -la "$NPZ" | awk '{print $5}') bytes"

# 2. Model smoke test
echo "-- smoke test"
uv run --directory "$PORT_DIR" python scripts/smoke_model.py || { echo "FAIL smoke"; exit 2; }

# 3. Start the server with the n=1000 lens (if not already up)
if ! curl -s --max-time 5 http://127.0.0.1:8765/api/lens >/dev/null; then
  echo "-- starting server"
  ( cd "$PORT_DIR" && JLENS_PATH="$NPZ" nohup uv run python -m uvicorn jlens_qwen.serve:app \
      --host 127.0.0.1 --port 8765 >"$HERE/runs/server.log" 2>&1 & )
  # wait up to 10 min for the model to load into the server
  n=0
  until curl -s --max-time 5 http://127.0.0.1:8765/api/lens | grep -q n_prompts; do
    sleep 10; n=$((n+1)); [ "$n" -ge 60 ] && { echo "FAIL server start"; exit 3; }
  done
fi
curl -s http://127.0.0.1:8765/api/lens | head -c 300; echo

# 4. P0 first light
echo "-- p0 first light"
python3 "$HERE/p0_first_light.py" || { echo "FAIL p0"; exit 4; }

# 5. P1 calibration (with a 10-item causal spot-check)
echo "-- p1 calibrate"
python3 "$HERE/p1_calibrate.py" --validate 10 || { echo "FAIL p1"; exit 5; }

# 6. E1 statics
echo "-- e1 statics"
python3 "$HERE/e1_statics.py" --levels 0,2,4,8,16 --items 60 || { echo "FAIL e1"; exit 6; }

echo "===== OVERNIGHT CHAIN COMPLETE $(date) ====="
