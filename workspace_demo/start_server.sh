#!/usr/bin/env bash
# start_server.sh — start the jlens-qwen36 serve API detached with the n=1000
# lens, and wait until /api/lens answers. Idempotent: exits 0 immediately if
# the server is already up. Logs -> runs/server.log.
#
# NOTE: serve.py carries the local tail-readout patch
# (patches/serve_tail_readout.patch); after a fresh setup_upstream.sh,
# re-apply it with `git apply` before starting.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT_DIR="$HERE/upstream/jlens-qwen36"
NPZ="$PORT_DIR/data/lens/qwen36_27b_neuronpedia_n1000.npz"
mkdir -p "$HERE/runs"

if curl -s --max-time 5 http://127.0.0.1:8765/api/lens | grep -q n_prompts; then
  echo "server already up"
  exit 0
fi

[ -f "$NPZ" ] || { echo "FAIL: lens npz missing: $NPZ"; exit 1; }
grep -q "pos_offset" "$PORT_DIR/jlens_qwen/serve.py" || {
  echo "FAIL: serve.py is missing the tail-readout patch"; exit 1; }

echo "-- starting server (model load takes a few minutes)"
( cd "$PORT_DIR" && JLENS_PATH="$NPZ" nohup uv run python -m uvicorn \
    jlens_qwen.serve:app --host 127.0.0.1 --port 8765 \
    >>"$HERE/runs/server.log" 2>&1 & )

n=0
until curl -s --max-time 5 http://127.0.0.1:8765/api/lens | grep -q n_prompts; do
  sleep 10
  n=$((n + 1))
  [ "$n" -ge 60 ] && { echo "FAIL: server did not come up in 10 min"; exit 2; }
done
echo "server up:"
curl -s http://127.0.0.1:8765/api/lens | head -c 300
echo
