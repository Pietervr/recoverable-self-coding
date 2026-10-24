#!/bin/bash
# EC2 user-data for one jitter S4 worker. Placeholders are filled by aws/launch_s4.py:
#   __BUCKET__ __PREFIX__ __BUNDLE__ __MODE__ (s4a | s4b) __SHARD__ (i/K) __WORKERS__ __KIND__ (cv|rec|all) __LIFETIME_S__
# The instance: installs python3.12 + the pinned numerical stack, pulls the bundle from S3, (s4b) pulls s4a.json,
# runs s4.py with a background S3 sync of results/s4 every 5 minutes, syncs once more at the end, and SHUTS DOWN
# (terminate-on-shutdown is set by the launcher). A hard stop timer bounds the spend even if the job hangs.
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[ud] start $(date -u +%FT%TZ) mode __MODE__ shard __SHARD__ workers __WORKERS__ kind __KIND__"
# hard stop: shutdown after the lifetime whatever happens
( sleep __LIFETIME_S__; echo "[ud] LIFETIME reached $(date -u +%FT%TZ)"; sync; shutdown -h now ) &
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 XLA_FLAGS=--xla_cpu_multi_thread_eigen=false
if command -v dnf >/dev/null 2>&1; then
  dnf -y install python3.12 python3.12-pip awscli >/dev/null 2>&1 || dnf -y install python3.12 python3.12-pip >/dev/null 2>&1
  PY=python3.12
else
  apt-get update -y >/dev/null 2>&1; apt-get install -y python3.12 python3.12-venv python3-pip awscli >/dev/null 2>&1
  PY=python3.12
fi
mkdir -p /opt/s4 && cd /opt/s4
$PY -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__"
aws s3 cp "s3://__BUCKET__/__PREFIX__/bundle/__BUNDLE__" bundle.tar.gz || { echo "[ud] bundle download failed"; shutdown -h now; }
aws s3 cp "s3://__BUCKET__/__PREFIX__/bundle/__BUNDLE__.sha256" bundle.sha256 && sed 's#  .*#  bundle.tar.gz#' bundle.sha256 | sha256sum -c - || { echo "[ud] bundle checksum failed"; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
python - <<'EOF'
import jax, numpy, scipy, joblib; print("[ud] jax", jax.__version__, "numpy", numpy.__version__, "scipy", scipy.__version__, "joblib", joblib.__version__, "devices", jax.devices())
EOF
# results already on S3 (resume after an interruption, or s4a.json for s4b)
aws s3 sync "s3://__BUCKET__/__PREFIX__/results/s4" results/s4 --quiet || true
# periodic sync of the working set
( while true; do sleep 300; aws s3 sync results/s4 "s3://__BUCKET__/__PREFIX__/results/s4" --quiet; echo "[ud] synced $(date -u +%T)"; done ) &
SYNC_PID=$!
echo "[ud] run start $(date -u +%FT%TZ)"
if [ "__MODE__" = "s4a" ]; then
  python s4.py s4a --workers __WORKERS__ > results/s4/run_s4a.log 2>&1
else
  python s4.py s4b --workers __WORKERS__ --shard __SHARD__ --kind __KIND__ > "results/s4/run_s4b___SHARD_TAG__.log" 2>&1
fi
echo "[ud] run rc=$? $(date -u +%FT%TZ)"
kill $SYNC_PID 2>/dev/null
aws s3 sync results/s4 "s3://__BUCKET__/__PREFIX__/results/s4" --quiet
aws s3 cp /var/log/s4_userdata.log "s3://__BUCKET__/__PREFIX__/logs/userdata___MODE_____SHARD_TAG___$(date -u +%Y%m%dT%H%M%SZ).log" || true
echo "[ud] done $(date -u +%FT%TZ); shutting down"
sync; shutdown -h now
