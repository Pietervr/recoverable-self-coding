#!/usr/bin/env python3
"""t1_job.py — SageMaker training-job entry for the T1 simulations (pre-registration §7.5 and §10).

Runs simulate.py stages on every vCPU of the instance, resumes from and uploads to RESULTS_URI after
every round, and writes a summary per stage. Launched by launch_t1.py; the code channel is mounted at
/opt/ml/input/data/code (models.py, analyze.py, simulate.py, this file).

Environment (set by the launcher):
  TASK          all | calibration | power | recovery | gain | bench
  N_REP (1000), N_REP_RECOVERY (200), N_REP_5LAYERS (200), D, LAYERS ("41" or "25,33,41,49,57"), SEED,
  GENERATORS (optional comma list), N_JOBS, N_STARTS_INNER, SHARD / N_SHARDS
  RESULTS_URI   s3://bucket/results/t1_access/<run>/   (CSVs, gain JSON, progress and summaries land here)
TASK=all runs, for this shard: calibration -> power (gain calibration first) -> recovery -> the five-layer
check (calibration on M2B,M2K and power on M3H,M3V at N_REP_5LAYERS). Every stage's CSV carries the
shard suffix; shards are disjoint by construction (every N_SHARDS-th task) and concatenate.
Every artefact is also copied to /opt/ml/output/data (SageMaker's output.tar.gz).
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
N_REP_RECOVERY = int(os.environ.get("N_REP_RECOVERY", "200"))
N_REP_5LAYERS = int(os.environ.get("N_REP_5LAYERS", "200"))
D = int(os.environ.get("D", "4"))
LAYERS = tuple(int(x) for x in os.environ.get("LAYERS", "41").split(","))
FIVE_LAYERS = (25, 33, 41, 49, 57)
SEED = int(os.environ.get("SEED", "2026"))
GENERATORS = os.environ.get("GENERATORS") or None
N_JOBS = int(os.environ.get("N_JOBS") or os.cpu_count())
SHARD = int(os.environ.get("SHARD", "0"))          # this job takes every N_SHARDS-th (point, replicate) task
N_SHARDS = int(os.environ.get("N_SHARDS", "1"))
N_STARTS_INNER = int(os.environ.get("N_STARTS_INNER", "8"))   # §14: 4 if the budget requires (recorded in the pre-registration)
RESULTS_URI = os.environ["RESULTS_URI"].rstrip("/") + "/"
WORK = "/opt/ml/checkpoints" if os.path.isdir("/opt/ml/checkpoints") else "/opt/ml/sim_results"   # spot: synced to S3 by SageMaker too
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


def shard_name(csv_name: str) -> str:
    return csv_name.replace(".csv", f".shard{SHARD:02d}of{N_SHARDS:02d}.csv") if N_SHARDS > 1 else csv_name


def gain_file(cfg, S) -> str:
    """The §10 gain calibration: reuse RESULTS_URI/gain_calibration.json or compute it (deterministic per seed)."""
    local = os.path.join(WORK, "gain_calibration.json")
    if os.path.exists(local) or s3_download("gain_calibration.json", local):
        log("gain_calibration.json found — reusing it")
        return local
    t0 = time.time()
    log(f"gain calibration on {min(N_JOBS, 12)} workers")
    entries = S.calibrate_all_gains(seed=SEED, cfg=cfg, n_jobs=min(N_JOBS, 12))
    with open(local, "w") as fh:
        json.dump(entries, fh, indent=1, default=float)
    if SHARD == 0:
        s3_upload(local, "gain_calibration.json")
    for e in entries:
        log(f"  {e['generator']} target {e['target']}: scale {e['scale']} gain {e['gain']} {e['note']}")
    log(f"gain calibration done in {(time.time() - t0) / 60:.1f} min")
    shutil.copy(local, OUT_DIR)
    return local


def run_stage(task: str, n_rep: int, layers: tuple, generators, cfg, A, S):
    if task == "power":
        points, extras = S.power_points(gain_file(cfg, S))
        csv_name = f"power_D{D}{'_5layers' if len(layers) > 1 else ''}.csv"
    elif task == "calibration":
        points, extras = S.null_points(), None
        csv_name = f"calibration_D{D}{'_5layers' if len(layers) > 1 else ''}.csv"
    elif task == "recovery":
        points, extras = S.recovery_points(), None
        csv_name = f"recovery_D{D}.csv"
    else:
        raise SystemExit(f"unknown stage {task}")
    if generators:
        keep = set(generators.split(","))
        points = [p for p in points if p[0] in keep]
    csv_name = shard_name(csv_name)
    out_csv = os.path.join(WORK, csv_name)
    if not os.path.exists(out_csv) and s3_download(csv_name, out_csv):
        log(f"resuming from {RESULTS_URI}{csv_name}")
    t0 = time.time()
    log(f"stage {task}: n_rep={n_rep} layers={layers} generators={generators} -> {csv_name}")

    def on_chunk(path, n_done, n_total, elapsed):
        s3_upload(path, csv_name)
        prog = dict(task=task, D=D, n_rep=n_rep, layers=list(layers), shard=SHARD, n_shards=N_SHARDS,
                    done=n_done, total=n_total, elapsed_min=round(elapsed / 60, 1),
                    rate_per_hour=round(3600 * n_done / max(elapsed, 1), 1),
                    eta_hours=round((n_total - n_done) * elapsed / max(n_done, 1) / 3600, 2), n_jobs=N_JOBS,
                    updated=time.strftime("%Y-%m-%d %H:%M:%S"))
        with open(os.path.join(WORK, csv_name + ".progress.json"), "w") as fh:
            json.dump(prog, fh, indent=1)
        s3_upload(os.path.join(WORK, csv_name + ".progress.json"), csv_name + ".progress.json")
        log(f"{task}: {n_done}/{n_total} rows, {prog['rate_per_hour']} per hour, eta {prog['eta_hours']} h")

    S.run_points(points, n_rep, D, layers, S.RHO_LAYERS, cfg, SEED, N_JOBS, out_csv, extras,
                 chunk=N_JOBS, on_chunk=on_chunk, shard=(SHARD, N_SHARDS))
    if os.path.exists(out_csv):
        summ = S.summarize(out_csv)
        summ_path = out_csv.replace(".csv", "_summary.csv")
        summ.to_csv(summ_path, index=False)
        s3_upload(out_csv, csv_name)
        s3_upload(summ_path, os.path.basename(summ_path))
        shutil.copy(out_csv, OUT_DIR)
        shutil.copy(summ_path, OUT_DIR)
    log(f"stage {task} done in {(time.time() - t0) / 3600:.2f} h")


def bench(cfg, A, M, S):
    """Instance benchmark: is one fit single-threaded (CPU == wall)? how does throughput scale with workers?"""
    import numpy as np
    from joblib import Parallel, delayed
    log(f"env NPROC={os.environ.get('NPROC')} OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS')} "
        f"OPENBLAS_NUM_THREADS={os.environ.get('OPENBLAS_NUM_THREADS')} MKL_NUM_THREADS={os.environ.get('MKL_NUM_THREADS')} cpu_count={os.cpu_count()}")
    ds = S.make_dataset("M3H", S.generator_theta("M3H", tau=0.5, sep=2.0), n_per_family=8, D=D, layers=(41,), rho=0.9, seed=1)
    folds = A.stratified_folds(ds.family, 5, seed=1)
    train_c = np.setdiff1d(np.arange(ds.n_concepts), folds[0])
    train = A._subset(ds.y[:, 0], ds.k, ds.concept, train_c)

    def one_fit(i, member="M3H"):
        M.fit(member, train, cfg.n_gh, 1, np.random.default_rng(i), recovery=False)      # warm-up (compile)
        c0 = os.times(); w0 = time.time()
        M.fit(member, train, cfg.n_gh, M.N_STARTS, np.random.default_rng(i), recovery=False)
        w = time.time() - w0; c1 = os.times()
        return w, (c1.user - c0.user) + (c1.system - c0.system)
    w, c = one_fit(0)
    log(f"single process M3H fit: wall {w:.1f} s, cpu {c:.1f} s, ratio {c / w:.2f}")
    for n in sorted({os.cpu_count() // 2, os.cpu_count(), N_JOBS}):
        w0 = time.time()
        res = Parallel(n_jobs=n)(delayed(one_fit)(i) for i in range(n))
        walls = np.array([r[0] for r in res]); cpus = np.array([r[1] for r in res])
        log(f"{n} concurrent M3H fits: mean wall {walls.mean():.1f} s (max {walls.max():.1f}), mean cpu {cpus.mean():.1f} s, "
            f"round wall {time.time() - w0:.1f} s, throughput {n / walls.mean():.3f} fits/s")
    w0 = time.time()
    r = A.layer_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, folds, cfg, seed=1, layer_tag=41)
    log(f"one layer of the full §8 procedure, single process: {time.time() - w0:.0f} s, convergence {r['converged'].mean():.3f}")


def main():
    import analyze as A
    import models as M
    import simulate as S
    log(f"task={TASK} n_rep={N_REP}/{N_REP_RECOVERY}/{N_REP_5LAYERS} D={D} layers={LAYERS} seed={SEED} "
        f"generators={GENERATORS} n_jobs={N_JOBS} shard={SHARD}/{N_SHARDS} inner starts={N_STARTS_INNER} "
        f"trapezoid points={M.TRAP_POINTS}")
    log(subprocess.run([sys.executable, "-c", "import jax, numpy, scipy, pandas, joblib, platform; "
                        "print('jax', jax.__version__, 'numpy', numpy.__version__, 'scipy', scipy.__version__, "
                        "'pandas', pandas.__version__, 'joblib', joblib.__version__, platform.platform(), platform.machine())"],
                       capture_output=True, text=True).stdout.strip())
    cfg = A.Config(n_starts_inner=N_STARTS_INNER)
    t0 = time.time()
    if TASK == "bench":
        bench(cfg, A, M, S)
    elif TASK == "gain":
        gain_file(cfg, S)
    elif TASK == "all":
        run_stage("calibration", N_REP, LAYERS, GENERATORS, cfg, A, S)
        run_stage("power", N_REP, LAYERS, GENERATORS, cfg, A, S)
        run_stage("recovery", N_REP_RECOVERY, LAYERS, GENERATORS, cfg, A, S)
        run_stage("calibration", N_REP_5LAYERS, FIVE_LAYERS, "M2B,M2K", cfg, A, S)
        run_stage("power", N_REP_5LAYERS, FIVE_LAYERS, "M3H,M3V", cfg, A, S)
    else:
        run_stage(TASK, N_REP if TASK != "recovery" else N_REP_RECOVERY, LAYERS, GENERATORS, cfg, A, S)
    for f in os.listdir(WORK):
        p = os.path.join(WORK, f)
        if os.path.isfile(p):
            shutil.copy(p, OUT_DIR)
    log(f"all done in {(time.time() - t0) / 3600:.2f} h")


if __name__ == "__main__":
    main()
