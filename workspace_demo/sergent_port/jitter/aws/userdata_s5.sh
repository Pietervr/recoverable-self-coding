#!/bin/bash
# EC2 user-data for STAGE S5 (DESIGN 8, Codex S3 re-review finding 6: S5 fitting on c7a.24xlarge with the S4 pins).
# One host: the frozen bundle, the 20 participants' derived decoder outputs (S<s>_active_preds.npz, from the public OSF
# recordings; uploaded once to the CODE prefix as s5_inputs/__S5_INPUTS__ with its sha256), results/s4/summary.json and
# s4a.json from the results prefix (written on the Mac by `s4.py evaluate` and uploaded), then `s5.py all`; results/s5
# goes to <RES>/results/s5. s5.py itself refuses unless the S4 manifest is complete. Placeholders as in userdata_s4.sh.
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[s5] start $(date -u +%FT%TZ) workers __WORKERS__ lifetime __LIFETIME_S__ s bundle __BUNDLE__"
export AWS_DEFAULT_REGION=us-west-2
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/s5___TAG__.log"
( sleep __LIFETIME_S__; echo "[s5] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "s5 lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export JITTER_TRIAL_CHUNK=64
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[s5] dnf python3.12 failed"
mkdir -p /opt/s4 && cd /opt/s4
python3.12 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[s5] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
fail() { echo "[s5] $1"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; exit 1; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || fail "bundle download failed"
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__.sha256" bundle.sha256 || fail "checksum download failed"
awk '{print $1"  bundle.tar.gz"}' bundle.sha256 | sha256sum -c - || fail "bundle checksum FAILED"
aws s3 cp "s3://$BUCKET/$CODE/s5_inputs/__S5_INPUTS__" s5_inputs.tar.gz || fail "S5 inputs download failed"
aws s3 cp "s3://$BUCKET/$CODE/s5_inputs/__S5_INPUTS__.sha256" s5_inputs.sha256 || fail "S5 inputs checksum download failed"
awk '{print $1"  s5_inputs.tar.gz"}' s5_inputs.sha256 | sha256sum -c - || fail "S5 inputs checksum FAILED"
tar -xzf bundle.tar.gz
mkdir -p brain_data/sergent2021/derived && tar -xzf s5_inputs.tar.gz -C brain_data/sergent2021/derived
echo "[s5] inputs: $(ls brain_data/sergent2021/derived | wc -l) files"
cd sergent_port/jitter
echo "[s5] bundle RSC hash $(cat BUNDLE_RSC_HASH)"
python -c 'import jax, numpy, scipy, platform, models; print("[s5] python", platform.python_version(), "jax", jax.__version__, "numpy", numpy.__version__, "scipy", scipy.__version__, "code", models.code_hash(), "TRIAL_CHUNK", models.TRIAL_CHUNK, "N_TAU", models.N_TAU_NODES)'
mkdir -p results/s4 results/s5
aws s3 cp "s3://$BUCKET/$RES/results/s4/summary.json" results/s4/summary.json || fail "results/s4/summary.json missing on S3"
aws s3 cp "s3://$BUCKET/$RES/results/s4/s4a.json" results/s4/s4a.json || fail "results/s4/s4a.json missing on S3"
aws s3 cp "s3://$BUCKET/$RES/results/s4/run_config.json" results/s4/run_config.json --quiet || true
aws s3 sync "s3://$BUCKET/$RES/results/s5" results/s5 --quiet || true
sync_out() {
  aws s3 sync results/s5 "s3://$BUCKET/$RES/results/s5" --quiet --exclude "*.tmp.*"
  aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true
}
( while true; do sleep 240; sync_out; echo "[s5] synced $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg) files $(find results/s5 -name '*.json' | wc -l)"; done ) &
SYNC_PID=$!
( TOKEN=""; while true; do
    TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300" 2>/dev/null)
    CODE_=$(curl -s -o /dev/null -w "%{http_code}" -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/spot/instance-action 2>/dev/null)
    if [ "$CODE_" = "200" ]; then echo "[s5] SPOT INTERRUPTION NOTICE $(date -u +%FT%TZ)"; sync_out; echo "[s5] flushed"; sleep 130; fi
    sleep 5
  done ) &
echo "[s5] run start $(date -u +%FT%TZ)"
python -u s5.py all --workers __WORKERS__ > results/s5/run_s5.log 2>&1
echo "[s5] s5 rc=$? $(date -u +%FT%TZ)"
tail -n 20 results/s5/decision.md 2>/dev/null | sed 's/^/[s5:decision] /'
kill $SYNC_PID 2>/dev/null
sync_out
echo "[s5] all done $(date -u +%FT%TZ)"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
