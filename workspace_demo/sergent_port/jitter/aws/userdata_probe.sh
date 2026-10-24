#!/bin/bash
# EC2 user-data for a THROUGHPUT PROBE (24 Oct 2026): the first S2 closure instance (c7a.24xlarge, 96 workers) had not
# finished one 20-task set after 30 minutes, against 289 s per decision participant-dataset sequential on the Mac. This
# probe measures, on a small instance of the same family, (1) the thread count of one JAX process under the run's
# environment (oversubscription or not), (2) the wall and CPU time of ONE decision task alone, (3) two tasks in parallel.
# Placeholders as in userdata_s4.sh: __BUCKET__ __CODE_PREFIX__ __RESULTS_PREFIX__ __BUNDLE__ __LIFETIME_S__ __NUMPY__
# __SCIPY__ __JAX__ __JOBLIB__ __PANDAS__ __TAG__
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[probe] start $(date -u +%FT%TZ) lifetime __LIFETIME_S__ s"
export AWS_DEFAULT_REGION=us-west-2
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/probe___TAG__.log"
( sleep __LIFETIME_S__; echo "[probe] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "probe lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
lscpu | head -30; nproc; free -g
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[probe] dnf python3.12 failed"
mkdir -p /opt/s4 && cd /opt/s4
python3.12 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[probe] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || { echo "[probe] bundle download failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
( while true; do sleep 120; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true; done ) &
cat > /opt/s4/probe.py <<'EOF'
import os, sys, time
t_start = time.time()
def threads():
    return int([l for l in open("/proc/self/status") if l.startswith("Threads:")][0].split()[1])
print("[probe] cpu_count", os.cpu_count(), "affinity", len(os.sched_getaffinity(0)), "NPROC", os.environ.get("NPROC"),
      "XLA_FLAGS", os.environ.get("XLA_FLAGS"), "OPENBLAS", os.environ.get("OPENBLAS_NUM_THREADS"), flush=True)
import numpy as np
import jax, jax.numpy as jnp
print("[probe] threads after jax import", threads(), flush=True)
x = jnp.ones((3000, 3000)); y = (x @ x).block_until_ready()
print("[probe] threads after a 3000x3000 matmul", threads(), "jax", jax.__version__, flush=True)
t0 = time.time(); c0 = os.times()
for _ in range(3):
    y = (x @ x).block_until_ready()
c1 = os.times(); w = time.time() - t0
print(f"[probe] 3 matmuls: wall {w:.2f} s, cpu {c1.user - c0.user + c1.system - c0.system:.2f} s (ratio {(c1.user - c0.user + c1.system - c0.system) / w:.2f})", flush=True)
import s2, models as M
bases = s2.load_bases(); members = s2.set_members("W2", 0)
print("[probe] code", M.code_hash(), "members", members[:3], flush=True)
t0 = time.time(); c0 = os.times()
row = s2.decision_task("W2", 0, 0, members[0], bases)
c1 = os.times(); w = time.time() - t0
cpu = c1.user - c0.user + c1.system - c0.system
print(f"[probe] ONE decision task W2 set 0 m0 (S{members[0]}) alone: wall {w:.0f} s, cpu {cpu:.0f} s (ratio {cpu / w:.2f}), threads now {threads()}, scores {row['scores']}, task seconds {row['seconds']:.0f}", flush=True)
sys.stdout.flush()
from joblib import Parallel, delayed
t0 = time.time()
rows = Parallel(n_jobs=2, backend="loky")(delayed(s2.decision_task)("W2", 0, m, members[m], bases) for m in (1, 2))
w = time.time() - t0
print(f"[probe] TWO decision tasks in parallel (loky, n_jobs 2): wall {w:.0f} s, task seconds {[round(r['seconds']) for r in rows]}, scores {[r['scores'] for r in rows]}", flush=True)
print(f"[probe] done in {time.time() - t_start:.0f} s", flush=True)
EOF
python -u /opt/s4/probe.py
echo "[probe] rc=$? $(date -u +%FT%TZ)"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
