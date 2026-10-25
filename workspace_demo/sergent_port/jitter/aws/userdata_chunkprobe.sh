#!/bin/bash
# EC2 user-data for the TRIAL-CHUNK HOST PROBE (25 Oct 2026). The per-core probe (userdata_xprobe.sh) put 98% of a
# decision task inside the compiled likelihood (about 19 ms per value-and-gradient call; Intel 1,224 s, Graviton 1,351 s,
# AMD 1,513 s alone, against 435 s on the M4), whose (n, N_tau, N_g) intermediates (about 3.2 MB each at n = 768) spill
# the private caches and thrash the shared memory system at 48-96 workers. This probe runs W2 development sets 0-4
# (100 decision tasks) at __WORKERS__ workers with JITTER_TRIAL_CHUNK=__PART__ (the training objective summed over
# 64-trial chunks under a scan with recompute; equal to the one-block objective to 1e-14) and logs each task's wall
# time as it completes. Placeholders as in userdata_probe.sh.
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[cprobe] start $(date -u +%FT%TZ) lifetime __LIFETIME_S__ s workers __WORKERS__ chunk __PART__"
export AWS_DEFAULT_REGION=us-west-2
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/cprobe___TAG__.log"
( sleep __LIFETIME_S__; echo "[cprobe] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "probe lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 JITTER_TRIAL_CHUNK=__PART__
lscpu | grep -E "Model name|^CPU\(s\)|L2|L3"; free -g
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[cprobe] dnf python3.12 failed"
mkdir -p /opt/s4 && cd /opt/s4
python3.12 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[cprobe] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || { echo "[cprobe] bundle download failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
( while true; do sleep 120; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true; done ) &
cat > /opt/s4/cprobe.py <<'EOF'
import os, sys, time
sys.path.insert(0, os.getcwd())
from joblib import Parallel, delayed
import s2, models as M

def task(r, m, base):
    import time as _t
    t0 = _t.time()
    row = s2.decision_task("W2", r, m, base, s2.load_bases())
    return r, m, base, _t.time() - t0, row["scores"]

bases = s2.load_bases()
jobs = [(r, m, b) for r in range(5) for m, b in enumerate(s2.set_members("W2", r))]
print(f"[cprobe] code {M.code_hash()} TRIAL_CHUNK {M.TRIAL_CHUNK} tasks {len(jobs)} workers {int(sys.argv[1])}", flush=True)
t_start = time.time()
done = 0
for r, m, b, w, sc in Parallel(n_jobs=int(sys.argv[1]), backend="loky", return_as="generator_unordered")(delayed(task)(*j) for j in jobs):
    done += 1
    print(f"[cprobe] TASK {done} W2 set {r} m{m} S{b}: wall {w:.0f} s at +{time.time() - t_start:.0f} s, scores {sc}", flush=True)
print(f"[cprobe] all {done} done in {time.time() - t_start:.0f} s", flush=True)
EOF
python -u /opt/s4/cprobe.py __WORKERS__
echo "[cprobe] rc=$? $(date -u +%FT%TZ)"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
