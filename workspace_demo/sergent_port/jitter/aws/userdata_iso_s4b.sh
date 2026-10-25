#!/bin/bash
# EC2 user-data for one jitter worker, S4b with ONE PROCESS PER TASK (aws/run_s4b_isolated.py, embedded below;
# 25 Oct 2026: the loky workers' compile caches exhausted memory on the first rec hosts) and kind-specific log names.
# Generated from userdata_s4.sh (modes: s2closure | s4a | s4b). Placeholders filled by aws/launch_s4.py:
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
LOGKEY="s3://$BUCKET/$RES/logs/userdata___MODE_____KIND_____TAG__.log"     # TAG = the part for s2closure, else the shard tag
# hard stops: shutdown at the lifetime whatever happens (two mechanisms, as the T1 user-data does)
( sleep __LIFETIME_S__; echo "[ud] LIFETIME reached $(date -u +%FT%TZ)"; aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true; sync; shutdown -h now ) &
shutdown -h +$(( __LIFETIME_S__ / 60 + 10 )) "jitter worker lifetime" >/dev/null 2>&1 || true
export NPROC=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
# the 64-trial chunked training objective (models.TRIAL_CHUNK; 25 Oct 2026: 13x the host rate at 96 workers, equal to the
# one-block objective to rounding; S2_REPORT 9) - part of the S4 rule named in the Codex FREEZE line
export JITTER_TRIAL_CHUNK=64
# NO XLA_FLAGS (measured 24 Oct 2026 on the S2 closure hosts at 48 workers): with
# "--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1" medium participants took 2,846-3,335 s and
# S11 2,064-2,116 s; without it 2,323-2,595 s and 1,293-1,602 s - the single-threaded compile costs about 30%. The real
# ceiling is the host (memory bandwidth): 96 workers thrash (only the lightest participants finished in 95 min), 48 give
# about 60-70 decision tasks per host-hour, about one Mac. Launch with --workers 48.
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
( while true; do sleep 300; sync_out; echo "[ud] synced $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg) mem_used_GB $(free -g | awk '/Mem:/{print $3"/"$2}') tasks $(find results -name '*.json' -newer /opt/s4/bundle.tar.gz 2>/dev/null | wc -l)"; done ) &
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
  s4b)       export S4_S3_RESULTS="s3://$BUCKET/$RES/results/s4"
             # --kind rec needs only c0 (results/s4/c0.json, written by the S4a hosts as soon as their stage 1 has landed and
             # synced here within 5 min): a rec host launched beside the S4a hosts polls the prefix for it up to its lifetime
             cat > /opt/s4/run_s4b_isolated.py <<'PYEOF'
"""Execution harness for S4b on an AWS host (25 Oct 2026): the same task list and the same frozen task function as
`s4.py s4b` (s4.ensure_run_record, s4.pending(s4.s4b_tasks(kind), shard), s4.run_task), but each task runs in a FRESH
process (concurrent.futures ProcessPoolExecutor, spawn, max_tasks_per_child=1).

Why: the first S4b recovery hosts (rec shards 2-4, 13:07-14:13Z) died with rc 1 after about an hour. Their memory rose by
about 7 GB every 5 min while tasks completed (142 of 184 GB at the last sample): each long-lived loky worker keeps every
compiled function it has seen, and full-data datasets differ in trial count, so the cache grows with every task. One
process per task bounds the memory to one task's footprint; JAX start-up and compilation cost tens of seconds against tasks
of an hour. A task that raises is logged and the queue continues (its result file stays absent, so the manifest shows it
PENDING), where joblib's Parallel stopped the whole host. Not part of the scientific code: s2/s4/s5 and the five hashed
modules are untouched, so the run record (fingerprint, runner hash) is unchanged.

    python run_s4b_isolated.py --workers 96 --shard i/K --kind rec|cv [--wait-h H]      (from the jitter directory)
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.getcwd())
import s4  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=96)
    ap.add_argument("--shard", default=None)
    ap.add_argument("--kind", required=True, choices=["cv", "rec", "all"])
    ap.add_argument("--wait-h", type=float, default=0.0)
    a = ap.parse_args()
    s4.ensure_run_record(f"S4b {a.kind}")
    bases = s4.load_bases()
    c0 = s4.load_c0(a.wait_h * 3600.0) if a.kind == "rec" else s4.load_s4a()["c0"]
    todo = s4.pending(s4.s4b_tasks(a.kind), a.shard)
    label = f"S4b {a.kind} shard {a.shard or '1/1'} (isolated)"
    print(f"[s4] {label}: {len(todo)} tasks on {a.workers} workers, one process per task, start "
          f"{time.strftime('%H:%M:%SZ', time.gmtime())}", flush=True)
    t0, done, failed = time.time(), 0, []
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        futs = {ex.submit(s4.run_task, t, bases, c0): t for t in todo}
        for f in as_completed(futs):
            t = futs[f]
            try:
                f.result()
                done += 1
            except Exception:  # noqa: BLE001 - logged, the queue continues
                failed.append(t["path"])
                print(f"[s4] TASK FAILED {t['path']}:\n{traceback.format_exc()}", flush=True)
            if (done + len(failed)) % 50 == 0:
                print(f"[s4] {label}: {done} done, {len(failed)} failed of {len(todo)} at {time.time() - t0:.0f} s", flush=True)
    print(f"[s4] {label}: done {done} tasks, {len(failed)} failed, in {time.time() - t0:.0f} s", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
PYEOF
             python /opt/s4/run_s4b_isolated.py --workers __WORKERS__ --shard __SHARD__ --kind __KIND__ --wait-h $(( __LIFETIME_S__ / 3600 )) > "results/s4/run_s4b___KIND_____SHARD_TAG__.log" 2>&1 ;;
esac
echo "[ud] run rc=$? $(date -u +%FT%TZ)"
kill $SYNC_PID 2>/dev/null
sync_out
echo "[ud] done $(date -u +%FT%TZ); shutting down"
aws s3 cp /var/log/s4_userdata.log "$LOGKEY" || true
sync; shutdown -h now
