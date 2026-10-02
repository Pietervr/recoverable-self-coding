"""Ledger row 19, stage 1: the refit qualification slice on CHPC Lengau, route A (sequential, checkpointed), one
dataset per process. Everything it does is declared in `row19_slice_manifest.json`; it runs only after Codex's review
of that specification and the owner's go, and it reads NO coverage.

    t1py chpc/row19_slice.py --manifest chpc/row19_slice_manifest.json --rep 0 --reservation-token T
                             [--until 20] [--segment 20] [--walltime-s 518400] [--pbs-kill-control]
                             [--root .../row19_slice] [--campaign .../row19_campaign] [--job-id 1234.sched01]
                             [--authorize-original-recompute "reason"]

Exit codes: 0 the dataset's chain is complete (aggregated without buying a fit); 75 stopped at the deadline, the
segment, the control target or an operator stop request (resume with the same arguments); 4 HELD (identity,
environment, reservation, task binding, second owner, checkpoint or cache damage, memory stop) - nothing more ran.

Order, each step fail-closed and BEFORE any fit (Codex 523249d, launch conditions A-H): manifest and environment
identity; the code pins; the campaign reservation bound to this PBS job; exclusive task ownership for this rep; the
dataset by its declared seed, its resolved seed checked against the declared exclusions; the task binding
(manifest, rep, seed, identity, B, target) persisted and re-verified; the checkpoint inspected without fitting; the
original-run cache validated (lossless nested serialisation, payload checksum, schema and shapes) or, with no
committed records, computed; then the chain under strict, durable, deadline-bounded, target-bounded hooks with a
checked stop boundary; status and timing ledgers; on completion the aggregation from the cached original and the
validated completed chain - no second chain, no fit.
"""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
import sys, json, time, argparse, hashlib, resource, platform, base64, fcntl
HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.getcwd() if os.path.exists(os.path.join(os.getcwd(), "analyze.py")) else os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, T1); sys.path.insert(0, HERE)
os.chdir(T1)
import numpy as np
import analyze as A, simulate as S, models as M
from row19_ledger import CampaignLedger, write_atomic

HELD, RESUME, DONE = 4, 75, 0
ORIG_SCHEMA = "row19-orig-v2"
RUN_KEYS = ("layers", "folds", "members", "delta", "logq", "n_c", "selected", "converged", "inner_conv", "inner_nonfinite",
            "recovery", "failed", "failed_reason", "params", "fit_seconds")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def held(msg):
    print(f"HELD: {msg}", flush=True)
    return HELD


# ---------------------------------------------------------------------------------------------------------------
# A: lossless nested serialisation of run_dataset's output (arrays as typed raw bytes, full precision)
# ---------------------------------------------------------------------------------------------------------------
def to_wire(o):
    if isinstance(o, np.ndarray):
        c = np.ascontiguousarray(o)
        return {"__nd__": str(c.dtype), "shape": list(c.shape), "b64": base64.b64encode(c.tobytes()).decode()}
    if isinstance(o, np.generic):
        c = np.ascontiguousarray(np.asarray(o))
        return {"__np__": str(c.dtype), "b64": base64.b64encode(c.tobytes()).decode()}
    if isinstance(o, dict):
        return {str(k): to_wire(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_wire(v) for v in o]
    if isinstance(o, (bool, int, float, str)) or o is None:
        return o
    raise TypeError(f"cannot serialise {type(o).__name__}")


def from_wire(o):
    if isinstance(o, dict) and "__nd__" in o:
        return np.frombuffer(base64.b64decode(o["b64"]), dtype=np.dtype(o["__nd__"])).reshape(o["shape"]).copy()
    if isinstance(o, dict) and "__np__" in o:
        return np.frombuffer(base64.b64decode(o["b64"]), dtype=np.dtype(o["__np__"]))[0]
    if isinstance(o, dict):
        return {k: from_wire(v) for k, v in o.items()}
    if isinstance(o, list):
        return [from_wire(v) for v in o]
    return o


def payload_sha(wire):
    return hashlib.sha256(json.dumps(wire, sort_keys=True).encode()).hexdigest()


def run_problems(run, n_layers, n_concepts):
    """Strict schema and shape checks on a (restored) run_dataset output; a list of problems, empty when clean."""
    p = []
    for k in RUN_KEYS:
        if k not in run:
            p.append(f"missing {k}")
    if p:
        return p
    if not isinstance(run["failed"], (bool, np.bool_)):
        p.append("failed is not a bool")
    if not isinstance(run["delta"], dict) or sorted(run["delta"]) != sorted(A.PREDICTORS):
        p.append("delta does not hold exactly the predictors")
    else:
        for q, v in run["delta"].items():
            if not (isinstance(v, np.ndarray) and v.shape == (n_layers, n_concepts) and v.dtype.kind == "f"):
                p.append(f"delta[{q}] is not a float array of shape ({n_layers}, {n_concepts})")
    if not (isinstance(run["folds"], list) and all(isinstance(f, np.ndarray) and f.ndim == 1 for f in run["folds"])):
        p.append("folds is not a list of 1-D arrays")
    else:
        cover = np.sort(np.concatenate([np.asarray(f, dtype=np.int64) for f in run["folds"]])) if run["folds"] else np.array([])
        if cover.size != n_concepts or not np.array_equal(cover, np.arange(n_concepts)):
            p.append("folds do not cover every concept exactly once")
    if not isinstance(run["params"], dict) or not all(isinstance(v, np.ndarray) for v in run["params"].values()):
        p.append("params is not a dict of arrays")
    for k in ("converged", "inner_conv", "inner_nonfinite", "recovery", "logq", "layers"):
        if not isinstance(run[k], np.ndarray):
            p.append(f"{k} is not an array")
    if isinstance(run["layers"], np.ndarray) and run["layers"].shape != (n_layers,):
        p.append("layers has the wrong shape")
    if not isinstance(run["fit_seconds"], (int, float)) or not np.isfinite(run["fit_seconds"]):
        p.append("fit_seconds is not finite")
    return p


def write_orig(path, run, ident, code_hash, seconds):
    wire = to_wire(run)
    rec = dict(schema=ORIG_SCHEMA, ident=ident, code_hash=code_hash, seconds=float(seconds), payload_sha=payload_sha(wire),
               written=time.time(), run=wire)
    write_atomic(path, rec)
    return rec["payload_sha"]


def read_orig(path, ident, code_hash, n_layers, n_concepts):
    """The validated original run, or (None, reason)."""
    try:
        rec = json.load(open(path))
    except Exception as e:
        return None, f"unreadable: {e}"
    if rec.get("schema") != ORIG_SCHEMA:
        return None, f"schema {rec.get('schema')!r} is not {ORIG_SCHEMA}"
    if rec.get("ident") != ident:
        return None, "another dataset identity"
    if rec.get("code_hash") != code_hash:
        return None, "another code/config hash"
    if payload_sha(rec.get("run")) != rec.get("payload_sha"):
        return None, "payload checksum mismatch"
    run = from_wire(rec["run"])
    bad = run_problems(run, n_layers, n_concepts)
    if bad:
        return None, "schema/shape: " + "; ".join(bad)
    return dict(run=run, seconds=float(rec["seconds"]), payload_sha=rec["payload_sha"]), ""


# ---------------------------------------------------------------------------------------------------------------
def environment(man):
    import jax, jaxlib, scipy, joblib
    env = dict(python=platform.python_version(), jax=jax.__version__, jaxlib=jaxlib.__version__, numpy=np.__version__,
               scipy=scipy.__version__, joblib=joblib.__version__, machine=platform.machine(), node=platform.node(),
               backend=str(jax.default_backend()), nproc=os.environ.get("NPROC"), omp=os.environ.get("OMP_NUM_THREADS"),
               cpu=_cpu_model())
    w = man.get("environment", {}).get("wrapper")
    if w and os.path.exists(w):
        env["wrapper"] = w; env["wrapper_sha256"] = sha_file(w)
    return env


def _cpu_model():
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def check_environment(man):
    env = environment(man)
    want = man["environment"]
    bad = [k for k in ("python", "jax", "jaxlib", "numpy", "scipy", "joblib", "machine") if str(want.get(k)) != str(env[k])]
    return env, bad


def check_code(man):
    got = {f: sha_file(os.path.join(T1, f)) for f in man["code"]["files"]}
    bad = [f for f, want in man["code"]["files"].items() if want and want != got[f]]
    return got, bad


def maxrss_bytes():
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return int(ru.ru_maxrss) * (1024 if platform.system() == "Linux" else 1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--until", type=int, default=None, help="cumulative target: only indices below this are ever dispatched (the control's 0..19)")
    ap.add_argument("--segment", type=int, default=None, help="at most this many NEW resamples this call")
    ap.add_argument("--walltime-s", type=float, default=None, help="the PBS walltime; the deadline is start + walltime - reserve")
    ap.add_argument("--pbs-kill-control", action="store_true", help="C2: no cooperative deadline - the interruption must come from PBS")
    ap.add_argument("--root", default=None)
    ap.add_argument("--campaign", default=None)
    ap.add_argument("--job-id", default=os.environ.get("PBS_JOBID", f"local-{int(time.time())}"))
    ap.add_argument("--reservation-token", default=None)
    ap.add_argument("--kind", default=None, help="main|c1|c2|c3 (the reservation's kind; defaults by until/segment)")
    ap.add_argument("--authorize-original-recompute", default=None, metavar="REASON",
                    help="recompute a lost ORIGINAL beside a committed checkpoint; recorded in the task binding")
    ap.add_argument("--skip-environment-check", action="store_true", help="tests only: the fixture environment is not Lengau's")
    ap.add_argument("--no-reservation", action="store_true", help="tests only")
    a = ap.parse_args(argv)
    t_start = time.time()
    man = json.load(open(a.manifest))
    manifest_sha = sha_file(a.manifest)
    root = a.root or man["storage"]["root"]
    campaign = a.campaign or man["storage"]["campaign"]
    kind = a.kind or ("main" if a.until is None else "c1")
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
    deadline = None if a.pbs_kill_control else t_start + walltime_s - reserve_s
    # C: the campaign reservation, bound to this job, before anything else
    ledger = CampaignLedger(campaign, man["budget"]["core_hours_cap"])
    if not a.no_reservation:
        if not a.reservation_token:
            return held("no --reservation-token: reserve before qsub (chpc/row19_ledger.py reserve)")
        try:
            entry = ledger.runner_start(a.reservation_token, a.job_id, kind, int(a.rep), root)
        except Exception as e:
            return held(f"reservation: {e}")
        print(f"reservation {entry['token']}: {entry['kind']} rep {entry['rep']} attempt {entry['attempt']}, {entry['reserved_core_h']:.1f} core-h", flush=True)
    # D: exclusive task ownership for this rep, held for the whole run, before any load or fit
    task_lock = open(os.path.join(root, f"task_{a.rep}.lock"), "a+")
    try:
        fcntl.flock(task_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return held(f"another process owns task rep {a.rep} in {root}")
    status_path = os.path.join(root, f"status_{a.rep}.json")
    timing_path = os.path.join(root, f"timing_{a.rep}.jsonl")
    task_path = os.path.join(root, f"task_{a.rep}.json")
    code_exit = HELD
    stop_reason = {}
    try:
        st = man["setting"]; c = man["cfg"]
        cfg = A.Config(start_policy=c["start_policy"], interval=c["interval"], n_boot_refit=int(c["n_boot_refit"]),
                       n_starts=int(c["n_starts"]), n_starts_inner=int(c["n_starts_inner"]),
                       refit_min_usable=float(c["refit_min_usable"]), n_outer=int(c["n_outer"]), n_inner=int(c["n_inner"]))
        kw = dict(st["grid"])
        theta = S.generator_theta(st["generator"], **kw)
        ds_seed = S.dataset_seed(st["generator"], kw, int(a.rep), int(st["D"]), int(man["datasets"]["seed_base"]))
        excluded = set(int(x) for x in man["datasets"].get("excluded_resolved_seeds", []))
        if ds_seed in excluded:
            return held(f"resolved dataset seed {ds_seed} is in the declared exclusion set")
        ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]),
                            layers=np.array(st["layers"]), rho=float(st["rho"]), seed=ds_seed)
        ds.meta.update(generator=st["generator"], theta=[float(x) for x in theta], D=int(st["D"]), rho=float(st["rho"]), seed=int(ds_seed))
        code_hash = S.config_hash(cfg, int(st["D"]), st["layers"], ds_seed, float(st["rho"]))
        folds = A.stratified_folds(ds.family, cfg.n_outer, ds_seed)
        ident = A.dataset_identity(ds, cfg, ds_seed, cfg.n_boot_refit, folds)
        ckpt_path = os.path.join(root, "ckpt", f"refit_{ident[:24]}.jsonl")
        orig_path = os.path.join(root, "orig", f"orig_{ident[:24]}.json")
        print(f"rep {a.rep}: dataset seed {ds_seed}, code/config {code_hash}, identity {ident[:16]}, policy {cfg.start_policy}, "
              f"target {'all ' + str(cfg.n_boot_refit) if a.until is None else '0..' + str(int(a.until) - 1)}", flush=True)
        # D: the task binding - persisted on the first start, re-verified on every later one
        binding = dict(manifest_sha=manifest_sha, rep=int(a.rep), ds_seed=int(ds_seed), ident=ident, code_hash=code_hash,
                       n_rep=int(cfg.n_boot_refit), until=a.until, ckpt=ckpt_path, orig=orig_path)   # the kind (c2 then c3) is per run
        if os.path.exists(task_path):
            task = json.load(open(task_path))
            diff = [k for k in binding if task.get("binding", {}).get(k) != binding[k]]
            if diff:
                return held(f"task binding differs on {diff}: this is not the task that was started in {root}")
        else:
            task = dict(binding=binding, created=time.time(), runs=[], expected_accepted=0, recompute_authorizations=[])
            write_atomic(task_path, task)
        # D: inspect the checkpoint without fitting
        cs = A.checkpoint_state(ds, cfg, ds_seed, cfg.n_boot_refit, folds, ckpt_path)
        if cs["rejected"] or cs["duplicates_conflicting"]:
            return held(f"checkpoint {ckpt_path}: {cs['rejected']} record(s) this run cannot accept, {cs['duplicates_conflicting']} conflicting duplicates; holding for diagnosis")
        if len(cs["accepted"]) < int(task.get("expected_accepted", 0)):
            return held(f"checkpoint holds {len(cs['accepted'])} accepted records but {task['expected_accepted']} were committed by earlier runs")
        print(f"checkpoint: {len(cs['accepted'])} accepted record(s), tail fragment {cs['tail_fragment']}", flush=True)
        # A/D: the original run - validated cache, or computed only when no committed record depends on it
        t0 = time.time()
        orig, why = (read_orig(orig_path, ident, code_hash, ds.n_layers, ds.n_concepts) if os.path.exists(orig_path) else (None, "absent"))
        if orig is None:
            if cs["accepted"]:
                if not a.authorize_original_recompute:
                    return held(f"original-run cache {why} while the checkpoint holds {len(cs['accepted'])} committed record(s): "
                                f"recompute only under --authorize-original-recompute (recorded)")
                task["recompute_authorizations"].append(dict(job=a.job_id, reason=a.authorize_original_recompute, why=why, t=time.time()))
                write_atomic(task_path, task)
                print(f"original-run recompute AUTHORIZED: {a.authorize_original_recompute} (cache {why})", flush=True)
            elif why != "absent":
                return held(f"original-run cache {why} and no committed record: remove it deliberately before a fresh start")
            run = A.run_dataset(ds, cfg, ds_seed, outer_folds=folds)
            orig_seconds, orig_cached = time.time() - t0, False
            bad = run_problems(run, ds.n_layers, ds.n_concepts)
            if bad:
                return held("the original run's output does not meet the schema: " + "; ".join(bad))
            psha = write_orig(orig_path, run, ident, code_hash, orig_seconds)
            back, why2 = read_orig(orig_path, ident, code_hash, ds.n_layers, ds.n_concepts)
            if back is None:
                return held(f"the original-run cache does not read back: {why2}")
        else:
            run, orig_seconds, orig_cached, psha = orig["run"], orig["seconds"], True, orig["payload_sha"]
        print(f"original run: {orig_seconds:.1f} s ({'cached' if orig_cached else 'computed'}), failed={run.get('failed')}, payload {psha[:12]}", flush=True)
        if run.get("failed"):
            return held(f"the original run failed: {run.get('failed_reason')}")
        # G/H: the stop boundary and the memory stop
        mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2**30
        def should_stop():
            if ledger.stop_requested(int(a.rep)):
                stop_reason.setdefault("request", ledger.stop_path(int(a.rep)) if os.path.exists(ledger.stop_path(int(a.rep))) else ledger.stop_path())
                return True
            if mem_stop and maxrss_bytes() > mem_stop:
                stop_reason.setdefault("memory", maxrss_bytes())
                return True
            return False
        n_before = len(open(timing_path).read().splitlines()) if os.path.exists(timing_path) else 0
        def on_record(rec):
            with open(timing_path, "a") as fh:
                fh.write(json.dumps(dict(rep=rec["rep"], fit_seconds=rec["fit_seconds"], failed=rec["failed"], t=time.time(),
                                         job=a.job_id, maxrss_bytes=maxrss_bytes())) + "\n"); fh.flush(); os.fsync(fh.fileno())
        try:
            rb = A.refit_bootstrap(ds, cfg, ds_seed, n_rep=cfg.n_boot_refit, outer_folds=folds, min_usable=cfg.refit_min_usable,
                                   checkpoint_path=ckpt_path, segment=a.segment, deadline=deadline, strict_restore=True,
                                   durable=True, on_record=on_record, until=a.until, should_stop=should_stop)
        except A.CheckpointDamaged as e:
            return held(str(e))
        t_chain_end = time.time()
        new_fits = ([float(l.get("fit_seconds", 0)) for l in (json.loads(x) for x in open(timing_path).read().splitlines()[n_before:] if x.strip())]
                    if os.path.exists(timing_path) else [])
        status = dict(phase="chain_done", rep=int(a.rep), job=a.job_id, kind=kind, ident=ident, code_hash=code_hash, policy=cfg.start_policy,
                      n_rep=int(cfg.n_boot_refit), until=a.until, segment=rb["segment"], n_done=rb["n_done"], n_new=rb["n_new"],
                      n_resumed=rb["n_resumed"], n_damaged=rb["n_damaged"], n_tail_repaired=rb["n_tail_repaired"], partial=rb["partial"],
                      target_complete=rb["target_complete"], stopped_at_deadline=rb["stopped_at_deadline"],
                      stopped_by_request=rb["stopped_by_request"], stop_reason=stop_reason,
                      original_seconds=orig_seconds, original_cached=orig_cached, original_payload_sha=psha,
                      original_note="wall seconds of run_dataset in this process; includes jit compilation when computed fresh",
                      refit_fit_seconds_total=rb["fit_seconds"], first_new_fit_s=(new_fits[0] if new_fits else None),
                      median_new_fit_s=(float(np.median(new_fits)) if new_fits else None),
                      compilation_note="jit compilation is NOT separated; the first new resample's excess over the median is the proxy",
                      chain_wall_seconds=t_chain_end - t_start, environment=env, code=code, checkpoint=rb["checkpoint"],
                      manifest_sha=manifest_sha, reservation=a.reservation_token)
        write_atomic(status_path, status)
        # B: aggregate from the cached original and the validated completed chain - no fit is bought
        if not rb["partial"]:
            t_f = time.time()
            res = A.analyze_dataset(ds, cfg, ds_seed, outer_folds=folds, run=run, interval_result=rb)
            status["result"] = {p: dict(decision=res["predictors"][p]["decision"], ws=res["predictors"][p]["ws"]) for p in A.PREDICTORS}
            status["interval"] = {k: v for k, v in res.get("interval", {}).items() if k != "replicates"}
            status["finalisation_seconds"] = time.time() - t_f
        if stop_reason.get("memory"):
            code_exit = HELD
        else:
            code_exit = DONE if not rb["partial"] else RESUME
        wall = time.time() - t_start
        ru = resource.getrusage(resource.RUSAGE_SELF)
        status.update(phase="final", wall_seconds=wall, cpu_seconds=ru.ru_utime + ru.ru_stime,
                      utilisation=(ru.ru_utime + ru.ru_stime) / max(wall, 1e-9), maxrss_bytes=maxrss_bytes(), exit=code_exit,
                      resource_note="ru_maxrss/cpu/wall of this one process after aggregation and status publication; "
                                    "no workers exist in this route; scheduler accounting is settled in the campaign ledger",
                      finished=time.time())
        write_atomic(status_path, status)
        if rb["stopped_by_request"]:
            write_atomic(os.path.join(root, f"STOP_ACK_rep{a.rep}.json"), dict(job=a.job_id, rep=int(a.rep), n_done=rb["n_done"], t=time.time(), reason=stop_reason))
        task["runs"].append(dict(job=a.job_id, kind=kind, started=t_start, ended=time.time(), exit=code_exit, n_done=rb["n_done"], n_new=rb["n_new"]))
        task["expected_accepted"] = int(rb["n_done"])
        write_atomic(task_path, task)
        if code_exit == HELD:
            return held(f"memory stop: maxrss {stop_reason['memory']/2**30:.2f} GiB exceeds {mem_stop/2**30:.2f} GiB; chain flushed at a record boundary")
        print(f"rep {a.rep}: {'COMPLETE' if code_exit == DONE else 'PARTIAL (resume)'}: done {rb['n_done']}/{cfg.n_boot_refit}, "
              f"new {rb['n_new']}, resumed {rb['n_resumed']}, wall {wall/60:.1f} min, maxrss {status['maxrss_bytes']/2**30:.2f} GiB"
              + (f", target 0..{int(a.until)-1} complete" if rb["target_complete"] else "")
              + (", stopped by request" if rb["stopped_by_request"] else ""), flush=True)
        return code_exit
    finally:
        if not a.no_reservation and a.reservation_token:
            try:
                ledger.runner_end(a.reservation_token, time.time() - t_start, code_exit)
            except Exception as e:
                print(f"ledger: runner_end failed: {e}", flush=True)
        try:
            fcntl.flock(task_lock.fileno(), fcntl.LOCK_UN); task_lock.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
