#!/bin/bash
# EC2 user-data for a PER-CORE THROUGHPUT PROBE (25 Oct 2026). The S2 closure achieved 30.8 decision tasks per
# c7a.24xlarge host-hour, and ONE decision task alone on one AMD core took 1,513 s against 435 s on the Mac's M4 core
# (same jax/jaxlib 0.11.1, numpy 2.5.3, scipy 1.18.1). This probe asks where the 3.5x goes, on one instance type per
# launch, running each variant of __PART__ (comma list) as its own process IN PARALLEL on the same task (W2 set 0 m0):
#   base     the closure environment (NPROC=1, one BLAS thread)
#   nothunk  XLA_FLAGS=--xla_cpu_use_thunk_runtime=false (XLA's legacy CPU runtime, if this jaxlib still has it)
#   prof     base under cProfile: the top functions by own and cumulative time
# Placeholders as in userdata_probe.sh.
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[xprobe] start $(date -u +%FT%TZ) lifetime __LIFETIME_S__ s variants __PART__"
export AWS_DEFAULT_REGION=us-west-2
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/xprobe___TAG__.log"
( sleep __LIFETIME_S__; echo "[xprobe] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "probe lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
lscpu | head -30; nproc; free -g; uname -m
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[xprobe] dnf python3.12 failed"
mkdir -p /opt/s4 && cd /opt/s4
python3.12 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[xprobe] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
python -c "import numpy; numpy.show_config()" 2>&1 | grep -iA3 "blas" | head -12
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || { echo "[xprobe] bundle download failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
( while true; do sleep 120; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true; done ) &
cat > /opt/s4/xprobe.py <<'EOF'
import os, sys, time
sys.path.insert(0, os.getcwd())
variant = sys.argv[1]
import numpy as np
import jax
import s2, models as M
bases = s2.load_bases(); members = s2.set_members("W2", 0)
print(f"[xprobe:{variant}] code {M.code_hash()} jax {jax.__version__} XLA_FLAGS {os.environ.get('XLA_FLAGS')}", flush=True)
t0 = time.time(); c0 = os.times()
if variant == "prof":
    import cProfile, pstats, io
    pr = cProfile.Profile(); pr.enable()
    row = s2.decision_task("W2", 0, 0, members[0], bases)
    pr.disable()
else:
    row = s2.decision_task("W2", 0, 0, members[0], bases)
c1 = os.times(); w = time.time() - t0
cpu = c1.user - c0.user + c1.system - c0.system
print(f"[xprobe:{variant}] ONE decision task W2 set 0 m0 (S{members[0]}): wall {w:.0f} s, cpu {cpu:.0f} s, task seconds {row['seconds']:.0f}, scores {row['scores']}", flush=True)
if variant == "prof":
    for key in ("tottime", "cumulative"):
        s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats(key).print_stats(30)
        print(f"[xprobe:prof] top 30 by {key}\n" + s.getvalue(), flush=True)
EOF
pids=""
for v in $(echo "__PART__" | tr ',' ' '); do
  if [ "$v" = "nothunk" ]; then
    ( XLA_FLAGS=--xla_cpu_use_thunk_runtime=false python -u /opt/s4/xprobe.py $v; echo "[xprobe:$v] rc=$?" ) &
  else
    ( python -u /opt/s4/xprobe.py $v; echo "[xprobe:$v] rc=$?" ) &
  fi
  pids="$pids $!"
done
wait $pids
echo "[xprobe] all done $(date -u +%FT%TZ)"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
