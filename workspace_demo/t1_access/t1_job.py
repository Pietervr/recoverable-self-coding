#!/usr/bin/env python3
"""t1_job.py — SageMaker training-job entry for the T1 simulations (pre-registration §7.5 and §10).

Runs one simulate.py task on every vCPU of the instance, resumes from and uploads to RESULTS_URI
after every chunk, and writes the summary at the end. Launched by launch_t1.py; the code channel is
mounted at /opt/ml/input/data/code (models.py, analyze.py, simulate.py, this file).

Environment (set by the launcher):
  TASK          calibration | power | recovery | gain
  N_REP, D, LAYERS ("41" or "25,33,41,49,57"), SEED, GENERATORS (optional comma list), N_JOBS
  RESULTS_URI   s3://bucket/results/t1_access/<run>/   (CSV, gain JSON, progress and summary land here)
The power task computes the §10 gain calibration first (in parallel) unless gain_calibration.json is
already at RESULTS_URI. Every artefact is also copied to /opt/ml/output/data (SageMaker's output.tar.gz).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time

CODE = "/opt/ml/input/data/code"
sys.path.insert(0, CODE)
os.environ.setdefault("NPROC", "1")

import boto3  # noqa: E402

TASK = os.environ["TASK"]
N_REP = int(os.environ.get("N_REP", "1000"))
D = int(os.environ.get("D", "4"))
LAYERS = tuple(int(x) for x in os.environ.get("LAYERS", "41").split(","))
SEED = int(os.environ.get("SEED", "2026"))
GENERATORS = os.environ.get("GENERATORS") or None
N_JOBS = int(os.environ.get("N_JOBS") or os.cpu_count())
RESULTS_URI = os.environ["RESULTS_URI"].rstrip("/") + "/"
WORK = "/opt/ml/sim_results"
OUT_DIR = "/opt/ml/output/data"
os.makedirs(WORK, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

_bucket, _prefix = RESULTS_URI[5:].split("/", 1)
s3 = boto3.client("s3")


def s3_download(name: str, local: str) -> bool:
    try:
        s3.download_file(_bucket, _prefix + name, local)
        return True
    except Exception:
        return False


def s3_upload(local: str, name: str):
    s3.upload_file(local, _bucket, _prefix + name)


def log(msg: str):
    print(f"[t1_job {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    import analyze as A
    import models as M
    import simulate as S
    log(f"task={TASK} n_rep={N_REP} D={D} layers={LAYERS} seed={SEED} generators={GENERATORS} n_jobs={N_JOBS}")
    log(subprocess.run([sys.executable, "-c", "import jax, numpy, scipy, pandas, joblib, platform; "
                        "print('jax', jax.__version__, 'numpy', numpy.__version__, 'scipy', scipy.__version__, "
                        "'pandas', pandas.__version__, 'joblib', joblib.__version__, platform.platform(), platform.machine())"],
                       capture_output=True, text=True).stdout.strip())
    cfg = A.Config()
    t0 = time.time()

    if TASK in ("gain", "power"):
        gain_local = os.path.join(WORK, "gain_calibration.json")
        if s3_download("gain_calibration.json", gain_local):
            log("gain_calibration.json found at RESULTS_URI — reusing it")
        else:
            log(f"gain calibration on {min(N_JOBS, 12)} workers")
            entries = S.calibrate_all_gains(seed=SEED, cfg=cfg, n_jobs=min(N_JOBS, 12))
            with open(gain_local, "w") as fh:
                json.dump(entries, fh, indent=1, default=float)
            s3_upload(gain_local, "gain_calibration.json")
            for e in entries:
                log(f"  {e['generator']} target {e['target']}: scale {e['scale']} gain {e['gain']} {e['note']}")
            log(f"gain calibration done in {(time.time() - t0) / 60:.1f} min")
        shutil.copy(gain_local, OUT_DIR)
        if TASK == "gain":
            return
        points, extras = S.power_points(gain_local)
        csv_name = f"power_D{D}{'_5layers' if len(LAYERS) > 1 else ''}.csv"
    elif TASK == "calibration":
        points, extras = S.null_points(), None
        csv_name = f"calibration_D{D}{'_5layers' if len(LAYERS) > 1 else ''}.csv"
    elif TASK == "recovery":
        points, extras = S.recovery_points(), None
        csv_name = f"recovery_D{D}.csv"
    else:
        raise SystemExit(f"unknown TASK {TASK}")
    if GENERATORS:
        keep = set(GENERATORS.split(","))
        points = [p for p in points if p[0] in keep]

    out_csv = os.path.join(WORK, csv_name)
    if s3_download(csv_name, out_csv):
        log(f"resuming from {RESULTS_URI}{csv_name}")

    def on_chunk(path, n_done, n_total, elapsed):
        s3_upload(path, csv_name)
        prog = dict(task=TASK, D=D, n_rep=N_REP, layers=list(LAYERS), done=n_done, total=n_total,
                    elapsed_min=round(elapsed / 60, 1), rate_per_hour=round(3600 * n_done / max(elapsed, 1), 1),
                    eta_hours=round((n_total - n_done) * elapsed / max(n_done, 1) / 3600, 2), n_jobs=N_JOBS,
                    updated=time.strftime("%Y-%m-%d %H:%M:%S"))
        with open(os.path.join(WORK, csv_name + ".progress.json"), "w") as fh:
            json.dump(prog, fh, indent=1)
        s3_upload(os.path.join(WORK, csv_name + ".progress.json"), csv_name + ".progress.json")
        log(f"{n_done}/{n_total} rows, {prog['rate_per_hour']} per hour, eta {prog['eta_hours']} h")

    S.run_points(points, N_REP, D, LAYERS, S.RHO_LAYERS, cfg, SEED, N_JOBS, out_csv, extras,
                 chunk=max(N_JOBS, 32), on_chunk=on_chunk)
    summ = S.summarize(out_csv)
    summ_path = os.path.join(WORK, csv_name.replace(".csv", "_summary.csv"))
    summ.to_csv(summ_path, index=False)
    s3_upload(out_csv, csv_name)
    s3_upload(summ_path, os.path.basename(summ_path))
    for f in os.listdir(WORK):
        shutil.copy(os.path.join(WORK, f), OUT_DIR)
    log(f"done in {(time.time() - t0) / 3600:.2f} h")
    print(summ.to_string(), flush=True)


if __name__ == "__main__":
    main()
