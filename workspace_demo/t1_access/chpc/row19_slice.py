"""Ledger row 19, stage 1: the refit qualification slice on CHPC Lengau, route A (sequential, checkpointed), one
dataset per process. Everything it does is declared in `row19_slice_manifest.json`; it runs only after Codex's review
of that specification and the owner's go, and it reads NO coverage.

    t1py chpc/row19_slice.py --manifest chpc/row19_slice_manifest.json --rep 0 [--segment 20] [--walltime-s 518400]
                             [--root /mnt/lustre/users/pvanrooyen/t1_toolchain/row19_slice] [--job-id 1234.sched01]

Exit codes: 0 the dataset's chain is complete (its intervals written); 75 stopped at the deadline or the segment
(resume with the same arguments); 4 HELD (identity, environment, budget, second writer or checkpoint damage) - nothing
ran. Steps, each fail-closed: the manifest and environment identity; the budget ledger; the dataset by its declared
seed; the original run (cached by dataset identity, so a resume never redoes it); the refitting bootstrap with the
strict, durable, deadline-bounded, segment-limited checkpoint; the status and timing ledgers; on completion, the
companion cluster interval and the refit interval through analyze_dataset on the cached run.
"""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
import sys, json, time, argparse, hashlib, resource, platform
HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.getcwd() if os.path.exists(os.path.join(os.getcwd(), "analyze.py")) else os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, T1)
os.chdir(T1)
import numpy as np
import analyze as A, simulate as S, models as M

HELD, RESUME, DONE = 4, 75, 0


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def write_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, default=float); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    d = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


def held(msg):
    print(f"HELD: {msg}", flush=True)
    return HELD


def environment():
    import jax, jaxlib, scipy, joblib
    return dict(python=platform.python_version(), jax=jax.__version__, jaxlib=jaxlib.__version__, numpy=np.__version__,
                scipy=scipy.__version__, joblib=joblib.__version__, machine=platform.machine(), node=platform.node())


def check_environment(man):
    env = environment()
    want = man["environment"]
    bad = [k for k in ("python", "jax", "jaxlib", "numpy", "scipy", "joblib", "machine") if str(want.get(k)) != str(env[k])]
    return env, bad


def check_code(man):
    """The manifest's code hashes, when pinned, must equal the files as loaded; null entries are recorded, not enforced."""
    got = {f: sha_file(os.path.join(T1, f)) for f in man["code"]["files"]}
    bad = [f for f, want in man["code"]["files"].items() if want and want != got[f]]
    return got, bad


class Budget:
    """Core-hours reserved and spent per job, in one JSON ledger; a job that would breach the cap never starts."""
    def __init__(self, path, cap, cores, walltime_s):
        self.path, self.cap, self.cores, self.walltime_s = path, float(cap), int(cores), float(walltime_s)
        self.state = json.load(open(path)) if os.path.exists(path) else dict(cap=self.cap, jobs={})

    def totals(self):
        spent = sum(j.get("spent_core_h", 0.0) for j in self.state["jobs"].values() if j.get("state") == "ended")
        live = sum(j.get("reserved_core_h", 0.0) for j in self.state["jobs"].values() if j.get("state") == "live")
        return spent, live

    def start(self, job_id):
        spent, live = self.totals()
        mine = self.cores * self.walltime_s / 3600.0
        if spent + live + mine > self.cap + 1e-9:
            return False, f"budget: spent {spent:.1f} + live {live:.1f} + this job {mine:.1f} > cap {self.cap:.0f} core-hours"
        self.state["jobs"][job_id] = dict(state="live", reserved_core_h=mine, started=time.time(), cores=self.cores)
        write_atomic(self.path, self.state)
        return True, f"budget: spent {spent:.1f}, live {live:.1f}, reserved {mine:.1f} of {self.cap:.0f}"

    def end(self, job_id, wall_s):
        j = self.state["jobs"][job_id]
        j.update(state="ended", spent_core_h=self.cores * wall_s / 3600.0, ended=time.time())
        write_atomic(self.path, self.state)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--segment", type=int, default=None, help="run at most this many NEW resamples (the control)")
    ap.add_argument("--walltime-s", type=float, default=None, help="the PBS walltime; the deadline is start + walltime - reserve")
    ap.add_argument("--root", default=None)
    ap.add_argument("--job-id", default=os.environ.get("PBS_JOBID", f"local-{int(time.time())}"))
    ap.add_argument("--skip-environment-check", action="store_true", help="tests only: the fixture environment is not Lengau's")
    a = ap.parse_args(argv)
    t_start = time.time()
    man = json.load(open(a.manifest))
    root = a.root or man["storage"]["root"]
    os.makedirs(root, exist_ok=True)
    for sub in ("ckpt", "orig"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    env, bad_env = check_environment(man)
    if bad_env and not a.skip_environment_check:
        return held(f"environment differs from the manifest on {bad_env}: {env}")
    code, bad_code = check_code(man)
    if bad_code:
        return held(f"code hashes differ from the manifest's pins on {bad_code}")
    walltime_s = a.walltime_s if a.walltime_s is not None else man["pbs"]["walltime_h"] * 3600.0
    reserve_s = float(man["pbs"]["deadline_reserve_s"])
    deadline = t_start + walltime_s - reserve_s
    budget = Budget(os.path.join(root, "budget.json"), man["budget"]["core_hours_cap"], man["pbs"]["cores"], walltime_s)
    ok, msg = budget.start(a.job_id)
    print(msg, flush=True)
    if not ok:
        return held(msg)
    status_path = os.path.join(root, f"status_{a.rep}.json")
    timing_path = os.path.join(root, f"timing_{a.rep}.jsonl")
    code_exit = HELD
    try:
        st = man["setting"]; c = man["cfg"]
        cfg = A.Config(start_policy=c["start_policy"], interval=c["interval"], n_boot_refit=int(c["n_boot_refit"]),
                       n_starts=int(c["n_starts"]), n_starts_inner=int(c["n_starts_inner"]),
                       refit_min_usable=float(c["refit_min_usable"]), n_outer=int(c["n_outer"]), n_inner=int(c["n_inner"]))
        kw = dict(st["grid"])
        theta = S.generator_theta(st["generator"], **kw)
        ds_seed = S.dataset_seed(st["generator"], kw, int(a.rep), int(st["D"]), int(man["datasets"]["seed_base"]))
        ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]),
                            layers=np.array(st["layers"]), rho=float(st["rho"]), seed=ds_seed)
        ds.meta.update(generator=st["generator"], theta=[float(x) for x in theta], D=int(st["D"]), rho=float(st["rho"]), seed=int(ds_seed))
        code_hash = S.config_hash(cfg, int(st["D"]), st["layers"], ds_seed, float(st["rho"]))
        folds = A.stratified_folds(ds.family, cfg.n_outer, ds_seed)
        ident = A.dataset_identity(ds, cfg, ds_seed, cfg.n_boot_refit, folds)
        print(f"rep {a.rep}: dataset seed {ds_seed}, code/config {code_hash}, identity {ident[:16]}, policy {cfg.start_policy}", flush=True)
        # the original run, cached by identity: a resume never redoes the original fit
        orig_path = os.path.join(root, "orig", f"orig_{ident[:24]}.json")
        t0 = time.time()
        if os.path.exists(orig_path):
            cached = json.load(open(orig_path))
            if cached.get("ident") != ident:
                return held(f"original-run cache {orig_path} carries another identity")
            run = cached["run"]
            for k in ("delta",):
                run[k] = {p: np.asarray(v, dtype=float) for p, v in run[k].items()}
            for k in ("converged", "inner_conv", "inner_nonfinite", "recovery", "logq", "layers"):
                if k in run:
                    run[k] = np.asarray(run[k])
            orig_seconds, orig_cached = float(cached["seconds"]), True
        else:
            run = A.run_dataset(ds, cfg, ds_seed, outer_folds=folds)
            orig_seconds, orig_cached = time.time() - t0, False
            ser = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in run.items() if k != "delta"}
            ser["delta"] = {p: np.asarray(v).tolist() for p, v in run["delta"].items()}
            write_atomic(orig_path, dict(ident=ident, seconds=orig_seconds, run=ser, code_hash=code_hash))
        print(f"original run: {orig_seconds:.1f} s ({'cached' if orig_cached else 'computed'}), failed={run.get('failed')}", flush=True)
        if run.get("failed"):
            return held(f"the original run failed: {run.get('failed_reason')}")
        # the refitting bootstrap under the declared hooks
        n_before = len(open(timing_path).read().splitlines()) if os.path.exists(timing_path) else 0
        def on_record(rec):
            with open(timing_path, "a") as fh:
                fh.write(json.dumps(dict(rep=rec["rep"], fit_seconds=rec["fit_seconds"], failed=rec["failed"], t=time.time(),
                                         job=a.job_id)) + "\n"); fh.flush(); os.fsync(fh.fileno())
        try:
            rb = A.refit_bootstrap(ds, cfg, ds_seed, n_rep=cfg.n_boot_refit, outer_folds=folds, min_usable=cfg.refit_min_usable,
                                   checkpoint_dir=os.path.join(root, "ckpt"), segment=a.segment, deadline=deadline,
                                   strict_restore=True, durable=True, on_record=on_record)
        except A.CheckpointDamaged as e:
            return held(str(e))
        wall = time.time() - t_start
        ru = resource.getrusage(resource.RUSAGE_SELF)
        status = dict(rep=int(a.rep), job=a.job_id, ident=ident, code_hash=code_hash, policy=cfg.start_policy,
                      n_rep=int(cfg.n_boot_refit), n_done=rb["n_done"], n_new=rb["n_new"], n_resumed=rb["n_resumed"],
                      n_damaged=rb["n_damaged"], n_tail_repaired=rb["n_tail_repaired"], partial=rb["partial"],
                      stopped_at_deadline=rb["stopped_at_deadline"], segment=rb["segment"], original_seconds=orig_seconds,
                      original_cached=orig_cached, refit_fit_seconds_total=rb["fit_seconds"], wall_seconds=wall,
                      cpu_seconds=ru.ru_utime + ru.ru_stime, utilisation=(ru.ru_utime + ru.ru_stime) / max(wall, 1e-9),
                      maxrss_bytes=int(ru.ru_maxrss) * (1024 if platform.system() == "Linux" else 1),
                      environment=env, code=code, checkpoint=rb["checkpoint"], finished=time.time())
        if not rb["partial"]:
            res = A.analyze_dataset(ds, cfg, ds_seed, outer_folds=folds, run=dict(run, **{}))
            status["result"] = {p: dict(decision=res["predictors"][p]["decision"], ws=res["predictors"][p]["ws"]) for p in A.PREDICTORS}
            status["interval"] = {k: v for k, v in res.get("interval", {}).items() if k != "replicates"}
        write_atomic(status_path, status)
        code_exit = DONE if not rb["partial"] else RESUME
        print(f"rep {a.rep}: {'COMPLETE' if code_exit == DONE else 'PARTIAL (resume)'}: done {rb['n_done']}/{cfg.n_boot_refit}, "
              f"new {rb['n_new']}, resumed {rb['n_resumed']}, wall {wall/60:.1f} min, maxrss {status['maxrss_bytes']/2**30:.2f} GiB", flush=True)
        return code_exit
    finally:
        budget.end(a.job_id, time.time() - t_start)


if __name__ == "__main__":
    sys.exit(main())
