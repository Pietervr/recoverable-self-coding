#!/bin/bash
# EC2 user-data for the TRIAL-CHUNK PAIRED CHECK (25 Oct 2026): W2 development set 0 (20 decision tasks) fitted twice on
# ONE c7a.24xlarge under the same code, once with the one-block training objective (JITTER_TRIAL_CHUNK=0, the
# behaviour of the code under review) and once with 64-trial chunks, as two concurrent 20-worker pools; each task's
# full row goes to results/checks/chunkpair/<chunk>/m<m>.json on S3. The comparison (per-participant Delta3, selections,
# numerical failures) is made on the Mac. Placeholders as in userdata_probe.sh.
set -uo pipefail
exec > /var/log/s4_userdata.log 2>&1
echo "[cpair] start $(date -u +%FT%TZ) lifetime __LIFETIME_S__ s"
export AWS_DEFAULT_REGION=us-west-2
BUCKET=__BUCKET__; CODE=__CODE_PREFIX__; RES=__RESULTS_PREFIX__
LOGKEY="s3://$BUCKET/$RES/logs/cpair___TAG__.log"
( sleep __LIFETIME_S__; echo "[cpair] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "probe lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
dnf -y install python3.12 python3.12-pip >/dev/null 2>&1 || echo "[cpair] dnf python3.12 failed"
mkdir -p /opt/s4 && cd /opt/s4
python3.12 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q "numpy==__NUMPY__" "scipy==__SCIPY__" "jax==__JAX__" "jaxlib==__JAX__" "joblib==__JOBLIB__" "pandas==__PANDAS__" || { echo "[cpair] pip install failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
aws s3 cp "s3://$BUCKET/$CODE/bundle/__BUNDLE__" bundle.tar.gz || { echo "[cpair] bundle download failed"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; shutdown -h now; }
tar -xzf bundle.tar.gz
cd sergent_port/jitter
( while true; do sleep 120; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" --quiet || true; aws s3 sync results/checks/chunkpair "s3://$BUCKET/$RES/results/checks/chunkpair" --quiet || true; done ) &
cat > /opt/s4/cpair.py <<'EOF'
import json, os, sys, time
sys.path.insert(0, os.getcwd())
import numpy as np
from joblib import Parallel, delayed
import s2, models as M
chunk = os.environ["JITTER_TRIAL_CHUNK"]
out = f"results/checks/chunkpair/{chunk}"
os.makedirs(out, exist_ok=True)

def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    return o

def task(m, base):
    import time as _t
    t0 = _t.time()
    row = s2.decision_task("W2", 0, m, base, s2.load_bases())
    row = clean(row)
    row.update(m=m, base=base, wall=_t.time() - t0, chunk=chunk, code=M.code_hash())
    with open(f"{out}/m{m}.json", "w") as f:
        json.dump(row, f)
    return m, row["wall"], row["scores"]

members = s2.set_members("W2", 0)
print(f"[cpair:{chunk}] code {M.code_hash()} TRIAL_CHUNK {M.TRIAL_CHUNK}", flush=True)
for m, w, sc in Parallel(n_jobs=20, backend="loky", return_as="generator_unordered")(delayed(task)(m, b) for m, b in enumerate(members)):
    print(f"[cpair:{chunk}] m{m}: wall {w:.0f} s, scores {sc}", flush=True)
print(f"[cpair:{chunk}] all done", flush=True)
EOF
( JITTER_TRIAL_CHUNK=0 python -u /opt/s4/cpair.py; echo "[cpair:0] rc=$?" ) &
P0=$!
( JITTER_TRIAL_CHUNK=64 python -u /opt/s4/cpair.py; echo "[cpair:64] rc=$?" ) &
P1=$!
wait $P0 $P1
aws s3 sync results/checks/chunkpair "s3://$BUCKET/$RES/results/checks/chunkpair" || true
echo "[cpair] all done $(date -u +%FT%TZ)"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
