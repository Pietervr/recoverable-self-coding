#!/bin/bash
# EC2 user-data for one jitter worker (modes: s2closure | s4a | s4b). Placeholders filled by aws/launch_s4.py:
#   __BUCKET__ __CODE_PREFIX__ __RESULTS_PREFIX__ __BUNDLE__ __MODE__ __SHARD__ (i/K) __SHARD_TAG__ __WORKERS__ __KIND__
#   __LIFETIME_S__ __NUMPY__ __SCIPY__ __JAX__ __JOBLIB__ __PANDAS__
# The instance installs python3.12 + the pinned numerical stack, pulls the bundle from the CODE prefix (the instance role
# may only GetObject there), resumes any results already on the RESULTS prefix (the role may Put there), runs the job
# with a background S3 sync every 5 minutes, flushes on the spot two-minute notice, syncs once more at the end and SHUTS
# DOWN (the launcher sets terminate-on-shutdown). Two independent hard stops bound the spend even if the job hangs.
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[ud] start $(date -u +%FT%TZ) mode __MODE__ shard __SHARD__ workers __WORKERS__ kind __KIND__ lifetime __LIFETIME_S__ s"
export AWS_DEFAULT_REGION=us-west-2          # the bucket's region; EC2 metadata calls do not need it
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/userdata___MODE_____SHARD_TAG__.log"
# hard stops: shutdown at the lifetime whatever happens (two mechanisms, as the T1 user-data does)
( sleep __LIFETIME_S__; echo "[ud] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "jitter worker lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[ud] dnf python3.12 failed (falling back to uv)"
mkdir -p /opt/s4 && cd /opt/s4
if command -v python3.12 >/dev/null 2>&1; then
  python3.12 -m venv venv
else
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; export PATH="$HOME/.local/bin:$PATH"
  uv python install 3.12 >/dev/null 2>&1; uv venv --python 3.12 venv >/dev/null 2>&1
fi
. venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[ud] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || { echo "[ud] bundle download failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__.sha256" bundle.sha256 || { echo "[ud] checksum download failed"; shutdown -h now; }
awk '{print $1"  bundle.tar.gz"}' bundle.sha256 | sha256sum -c - || { echo "[ud] bundle checksum FAILED"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
python - <<'EOF'
import jax, numpy, scipy, joblib, pandas, models
print("[ud] jax", jax.__version__, "numpy", numpy.__version__, "scipy", scipy.__version__, "joblib", joblib.__version__, "pandas", pandas.__version__, "devices", jax.devices(), "code", models.code_hash())
EOF
mkdir -p results/s4 results/s2
# resume: results already on S3 (an earlier interrupted worker, or s4a.json for s4b)
aws s3 sync "s3://$BUCKET/$RES/results/s4" results/s4 --quiet || true
if [ "__MODE__" = "s2closure" ]; then aws s3 sync "s3://$BUCKET/$RES/results/s2" results/s2 --quiet || true; fi
sync_out() {
  aws s3 sync results/s4 "s3://$BUCKET/$RES/results/s4" --quiet --exclude "*.tmp.*"
  if [ "__MODE__" = "s2closure" ]; then aws s3 sync results/s2 "s3://$BUCKET/$RES/results/s2" --quiet --exclude "archive/*"; fi
  aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true
}
( while true; do sleep 300; sync_out; echo "[ud] synced $(date -u +%T)"; done ) &
SYNC_PID=$!
# spot two-minute notice: flush results, then let the interruption take the instance (resume is cheap: per-dataset files)
( TOKEN=""; while true; do
    TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300" 2>/dev/null)
    CODE_=$(curl -s -o /dev/null -w "%{http_code}" -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/spot/instance-action 2>/dev/null)
    if [ "$CODE_" = "200" ]; then echo "[ud] SPOT INTERRUPTION NOTICE $(date -u +%FT%TZ)"; sync_out; echo "[ud] flushed"; sleep 130; fi
    sleep 5
  done ) &
echo "[ud] run start $(date -u +%FT%TZ)"
case "__MODE__" in
  s2closure) bash aws/s2_closure.sh __WORKERS__ __PART__ > "results/s2/run_closure___PART__.log" 2>&1 ;;
  s4a)       export S4_S3_RESULTS="s3://$BUCKET/$RES/results/s4"
             python s4.py s4a --workers __WORKERS__ --shard __SHARD__ --wait-h 20 > "results/s4/run_s4a___SHARD_TAG__.log" 2>&1 ;;
  s4b)       python s4.py s4b --workers __WORKERS__ --shard __SHARD__ --kind __KIND__ > "results/s4/run_s4b___SHARD_TAG__.log" 2>&1 ;;
esac
echo "[ud] run rc=$? $(date -u +%FT%TZ)"
kill $SYNC_PID 2>/dev/null
sync_out
echo "[ud] done $(date -u +%FT%TZ); shutting down"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
