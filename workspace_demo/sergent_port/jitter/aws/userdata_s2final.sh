#!/bin/bash
# EC2 user-data for the S2 FINAL EVIDENCE (25 Oct 2026; Codex S3 re-review findings 3, 4, 9 and closure order 14): the
# final-rule paired checks and the three R = 25 development blocks under ONE immutable bundle, chunk 64, on c7a.24xlarge.
#   ROLE checks (one host): s2.py repair --label F, G and H on W2 set 0 as three concurrent 20-worker pools, then
#     --label crosseval (F's endpoints at fixed parameters on the G and H grids) and --label final-summary; results/s2/checks
#     goes to <RES>/s2final/checks/.
#   ROLE dev (host i of K): s2.py decision --setting W2,T1,O1 --R 25 --sets 0-24 --out-dir results/s2/decision_final
#     --shard i/K; the shards are disjoint, so no host needs another's files; results/s2/decision_final goes to
#     <RES>/s2final/dev/ (a separate prefix: the bundle's archived W2 set_0.json is never overwritten). The assemble step
#     (s2.py assemble --setting W2,T1,O1 --all --R 25 --out-dir results/s2/decision_final) runs on the Mac after the pull.
# Placeholders as in userdata_s4.sh (__PART__ = checks | dev, __SHARD__ = i/K for dev).
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[s2final] start $(date -u +%FT%TZ) role __PART__ shard __SHARD__ workers __WORKERS__ lifetime __LIFETIME_S__ s bundle __BUNDLE__"
export AWS_DEFAULT_REGION=us-west-2
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/s2final___PART_____TAG__.log"
( sleep __LIFETIME_S__; echo "[s2final] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "s2final lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
# the frozen runtime contract (DESIGN 8): the 64-trial chunked training objective, exported before any Python import; no XLA_FLAGS
export JITTER_TRIAL_CHUNK=64
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[s2final] dnf python3.12 failed"
mkdir -p /opt/s4 && cd /opt/s4
python3.12 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[s2final] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || { echo "[s2final] bundle download failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__.sha256" bundle.sha256 || { echo "[s2final] checksum download failed"; shutdown -h now; }
awk '{print $1"  bundle.tar.gz"}' bundle.sha256 | sha256sum -c - || { echo "[s2final] bundle checksum FAILED"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
echo "[s2final] bundle RSC hash $(cat BUNDLE_RSC_HASH)"
python -c 'import jax, numpy, scipy, models; print("[s2final] jax", jax.__version__, "numpy", numpy.__version__, "scipy", scipy.__version__, "code", models.code_hash(), "TRIAL_CHUNK", models.TRIAL_CHUNK, "N_TAU", models.N_TAU_NODES)'
mkdir -p results/s2/checks results/s2/decision_final
if [ "__PART__" = "checks" ]; then SRC=results/s2/checks; DST="s3://$BUCKET/$RES/s2final/checks"; else SRC=results/s2/decision_final; DST="s3://$BUCKET/$RES/s2final/dev"; fi
# resume: this role's files already on S3 (a spot interruption and relaunch); dev shards are disjoint, so a resumed host sees only its own
# each dev host keeps its OWN run record (the AMIs differ in the Python patch level by region, 3.12.14 vs 3.12.15, so a
# resumed host must never inherit another host's run_config.json; 25 Oct 10:13Z a relaunched shard refused on it): the record
# is uploaded as run_config___SHARD_TAG__.json and the shared name is excluded both ways
aws s3 sync "$DST" "$SRC" --quiet --exclude "*run_config.json" --exclude "run_config_*.json" || true
aws s3 cp "$DST/run_config___SHARD_TAG__.json" "$SRC/run_config.json" --quiet 2>/dev/null || true
sync_out() {
  [ -f "$SRC/run_config.json" ] && [ "__PART__" = "dev" ] && cp "$SRC/run_config.json" "$SRC/run_config___SHARD_TAG__.json"
  aws s3 sync "$SRC" "$DST" --quiet --exclude "*.tmp.*" --exclude "run_config.json"
  # dev: the endpoint archive (the per-task start/endpoint npz, results/s2/archive/decision_final) is kept too
  if [ "__PART__" = "dev" ] && [ -d results/s2/archive/decision_final ]; then aws s3 sync results/s2/archive/decision_final "s3://$BUCKET/$RES/s2final/dev_archive" --quiet --exclude "*.tmp.*"; fi
  aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true
}
( while true; do sleep 240; sync_out; echo "[s2final] synced $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg) files $(find $SRC -name '*.json' | wc -l)"; done ) &
SYNC_PID=$!
( TOKEN=""; while true; do
    TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300" 2>/dev/null)
    CODE_=$(curl -s -o /dev/null -w "%{http_code}" -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/spot/instance-action 2>/dev/null)
    if [ "$CODE_" = "200" ]; then echo "[s2final] SPOT INTERRUPTION NOTICE $(date -u +%FT%TZ)"; sync_out; echo "[s2final] flushed"; sleep 130; fi
    sleep 5
  done ) &
echo "[s2final] run start $(date -u +%FT%TZ)"
if [ "__PART__" = "checks" ]; then
  # the data-identity reference must be generated on this platform: AWS x86 regenerates W2 set 0 bit-differently from the
  # Mac (data ids 2e5907f1... vs 015aef5a...; first attempt 25 Oct 09:33Z refused on all twenty). Use the AWS closure
  # fleet's archived record (results/s2_aws/decision/W2/set_0.json in RSC, sha256 checked) and set the bundled Mac record aside.
  mkdir -p results/s2_aws/decision/W2
  aws s3 cp "s3://$BUCKET/$RES/results/s2/decision/W2/set_0.json" results/s2_aws/decision/W2/set_0.json --quiet
  echo "a8c21ecad0f7955772e3aa64b86938a0e20f0e441850810114857967491d6fdf  results/s2_aws/decision/W2/set_0.json" | sha256sum -c - || { echo "[s2final] AWS W2 set 0 reference checksum FAILED"; sync_out; shutdown -h now; }
  mv results/s2/decision/W2/set_0.json results/s2/decision/W2/set_0.mac.json && cp results/s2_aws/decision/W2/set_0.json results/s2/decision/W2/set_0.json   # repair_run reads DEC_DIR directly
  PIDS=""
  for L in F G H; do
    ( python -u s2.py repair --label $L --setting W2 --set 0 --workers 20 > results/s2/checks/run_repair_$L.log 2>&1; echo "[s2final] repair $L rc=$? $(date -u +%FT%TZ)" ) &
    PIDS="$PIDS $!"
  done
  wait $PIDS
  # the three pools must all have written their run files before the cross-evaluation and the summary
  for L in F G H; do [ -f results/s2/checks/repair_W2_set0_$L.json ] || echo "[s2final] repair $L: NO RUN FILE"; done
  python -u s2.py repair --label crosseval --setting W2 --set 0 --workers 20 > results/s2/checks/run_crosseval.log 2>&1; echo "[s2final] crosseval rc=$? $(date -u +%FT%TZ)"
  python -u s2.py repair --label final-summary --setting W2 --set 0 > results/s2/checks/run_final_summary.log 2>&1; echo "[s2final] final-summary rc=$? $(date -u +%FT%TZ)"
  tail -n 30 results/s2/checks/repair_W2_set0_final_summary.md 2>/dev/null | sed 's/^/[s2final:summary] /'
else
  python -u s2.py decision --setting W2,T1,O1 --R 25 --sets 0-24 --out-dir results/s2/decision_final --shard __SHARD__ --workers __WORKERS__ > results/s2/decision_final/run_shard___SHARD_TAG__.log 2>&1
  echo "[s2final] decision rc=$? $(date -u +%FT%TZ) task files $(find results/s2/decision_final -name 'set_*_m*.json' | wc -l)"
fi
kill $SYNC_PID 2>/dev/null
sync_out
echo "[s2final] all done $(date -u +%FT%TZ)"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
