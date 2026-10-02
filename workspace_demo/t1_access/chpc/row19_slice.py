"""Ledger row 19, stage 1: the refit qualification slice on CHPC Lengau, route A (sequential, checkpointed), one
dataset per process. Everything it does is declared in `row19_slice_manifest.json`; it runs only after Codex's review
of that specification and the owner's go, and it reads NO coverage.

    t1py chpc/row19_slice.py --manifest chpc/row19_slice_manifest.json --rep 0 --reservation-token T --kind main
                             [--until 20] [--segment 20] [--walltime-s 518400] [--pbs-kill-control]
                             [--root .../row19_slice] [--campaign .../row19_campaign] [--job-id 1234.sched01]
                             [--authorize-original-recompute "reason"]

Exit codes: 0 the dataset's chain is complete (aggregated without buying a fit); 75 stopped at the deadline, the
segment, the control target or an operator stop request (resume with the same arguments); 4 HELD (identity,
environment, reservation, task domain, binding, second owner, checkpoint or cache damage, lost progress, memory) -
nothing more ran.

Order, each step fail-closed and BEFORE any fit (Codex 523249d A-H; e44f804 R1-R7): manifest and environment identity
(versions, backend, thread caps, the wrapper's hash when pinned); the code pins; the declared task domain (rep, resolved
seed, kind, target, kill mode); the campaign reservation bound to this PBS job with this job's cores and walltime;
exclusive task ownership for this rep; the shared task index under task_index.json.lock; fresh-versus-recovering decided from the root's task index and prior
evidence before any binding is created; the task binding persisted and re-verified; the checkpoint inspected without
fitting against the per-record progress watermark; the current stop request and memory diagnosed before any original
work; the original-run cache validated (lossless nested serialisation, payload and metadata checksums, the complete
schema against cfg, dataset and folds) or, with no committed record, computed; then the chain under strict, durable,
deadline-bounded, target-bounded hooks with the stop checked before every dispatch and the watermark advanced after
every durable record; stop and memory re-checked after the last record and on no-work restores; on completion the
aggregation from the cached original and the validated completed chain - no second chain, no fit - with the
companion cluster interval retained; the measurement scopes stated as they are.
"""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, time, argparse, hashlib, resource, platform, base64, fcntl, math
HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.getcwd() if os.path.exists(os.path.join(os.getcwd(), "analyze.py")) else os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, T1); sys.path.insert(0, HERE)
os.chdir(T1)
import numpy as np
import analyze as A, simulate as S, models as M
from row19_ledger import CampaignLedger, write_atomic

HELD, RESUME, DONE = 4, 75, 0
ORIG_SCHEMA = "row19-orig-v3"
RUN_KEYS = ("layers", "folds", "members", "delta", "logq", "n_c", "selected", "converged", "inner_conv", "inner_nonfinite",
            "recovery", "failed", "failed_reason", "params", "fit_seconds")
THREAD_VARS = ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def held(msg):
    print(f"HELD: {msg}", flush=True)
    return HELD


# ---------------------------------------------------------------------------------------------------------------
# A/R6: lossless nested serialisation of run_dataset's output (arrays as typed raw bytes, full precision)
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


def meta_sha(rec):
    return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k not in ("run", "meta_sha")}, sort_keys=True).encode()).hexdigest()


def run_problems(run, ds, cfg, folds):
    """The complete contract of a (restored) run_dataset output against THIS cfg, dataset and folds - what the
    aggregation consumes; a list of problems, empty when clean."""
    p = []
    for k in RUN_KEYS:
        if k not in run:
            p.append(f"missing {k}")
    if p:
        return p
    L, C = ds.n_layers, ds.n_concepts
    members = run["members"]
    if not (isinstance(members, (list, tuple)) and members and all(isinstance(m, str) for m in members)):
        return ["members is not a non-empty sequence of names"]
    members = list(members)                                         # Config.members is a tuple; the cache decodes a list
    Mn = len(members)
    if not (isinstance(run["layers"], np.ndarray) and run["layers"].shape == (L,) and np.array_equal(run["layers"], np.asarray(ds.layers))):
        p.append("layers differ from the dataset's")
    fl = run["folds"]
    if not (isinstance(fl, list) and len(fl) == len(folds) and all(isinstance(f, np.ndarray) and f.ndim == 1 for f in fl)
            and all(np.array_equal(np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64)) for a, b in zip(fl, folds))):
        p.append("folds differ from the declared outer folds")
    if not isinstance(run["failed"], (bool, np.bool_)):
        p.append("failed is not a bool")
    if not isinstance(run["failed_reason"], str):
        p.append("failed_reason is not a string")
    if not isinstance(run["delta"], dict) or sorted(run["delta"]) != sorted(A.PREDICTORS):
        p.append("delta does not hold exactly the predictors")
    else:
        for q, v in run["delta"].items():
            if not (isinstance(v, np.ndarray) and v.shape == (L, C) and v.dtype.kind == "f"):
                p.append(f"delta[{q}] is not a float array of shape ({L}, {C})")
            elif not run["failed"] and not np.all(np.isfinite(v)):
                p.append(f"delta[{q}] has non-finite entries on a run not marked failed")
    if not (isinstance(run["logq"], np.ndarray) and run["logq"].shape == (L, Mn, C)):
        p.append(f"logq is not an array of shape ({L}, {Mn}, {C})")
    elif run["logq"].dtype.kind not in "fiu":
        p.append("logq is not a numeric array")
    if not (isinstance(run["n_c"], np.ndarray) and run["n_c"].shape == (C,)):
        p.append(f"n_c is not an array of shape ({C},)")
    sel = run["selected"]
    if not (isinstance(sel, (list, tuple)) and len(sel) == L):
        p.append(f"selected is not a sequence of length {L}")
    else:
        for li, layer_sel in enumerate(sel):
            if not (isinstance(layer_sel, (list, tuple)) and len(layer_sel) == len(folds)):
                p.append(f"selected[{li}] is not one (G, X) pair per fold"); continue
            for pair in layer_sel:
                if not (isinstance(pair, (list, tuple)) and len(pair) == 2 and all(isinstance(m, str) and m in members for m in pair)):
                    p.append(f"selected[{li}] holds a pair that is not two member names"); break
    nc = run["n_c"]
    if isinstance(nc, np.ndarray) and nc.shape == (C,):
        if nc.dtype.kind not in "iuf" or not np.all(np.isfinite(nc.astype(float))) or not np.all(nc > 0) \
                or not np.all(np.asarray(nc, dtype=float) == np.floor(np.asarray(nc, dtype=float))):
            p.append("n_c is not positive integral counts")       # the real pipeline returns bincount(...).astype(float)
    for k in ("converged", "inner_conv", "inner_nonfinite", "recovery"):
        v = run[k]
        if not (isinstance(v, np.ndarray) and v.ndim >= 2 and v.shape[0] == L and v.shape[1] == len(folds)):
            p.append(f"{k} is not an array with leading shape ({L}, {len(folds)})")
    if not (isinstance(run["params"], dict) and sorted(run["params"]) == sorted(members)):
        p.append("params keys are not exactly the members")
    else:
        for m, v in run["params"].items():
            if not (isinstance(v, np.ndarray) and v.ndim >= 1 and v.shape[0] == L):
                p.append(f"params[{m}] is not an array with leading dimension {L}")
    fs = run["fit_seconds"]
    if isinstance(fs, bool) or not isinstance(fs, (int, float)) or not math.isfinite(float(fs)) or float(fs) < 0:
        p.append("fit_seconds is not finite and non-negative")
    return p


def write_orig(path, run, ident, code_hash, seconds):
    wire = to_wire(run)
    rec = dict(schema=ORIG_SCHEMA, ident=ident, code_hash=code_hash, seconds=float(seconds), payload_sha=payload_sha(wire),
               written=time.time(), run=wire)
    rec["meta_sha"] = meta_sha(rec)
    write_atomic(path, rec)
    return rec["payload_sha"]


def read_orig(path, ident, code_hash, ds, cfg, folds):
    """The validated original run, or (None, reason). Every failure - parse, decode, schema, checksum - is a reason, never
    an exception (the runner HOLDS on a reason)."""
    try:
        rec = json.load(open(path))
        if rec.get("schema") != ORIG_SCHEMA:
            return None, f"schema {rec.get('schema')!r} is not {ORIG_SCHEMA}"
        if rec.get("ident") != ident:
            return None, "another dataset identity"
        if rec.get("code_hash") != code_hash:
            return None, "another code/config hash"
        if meta_sha(rec) != rec.get("meta_sha"):
            return None, "metadata checksum mismatch"
        sec = rec.get("seconds")
        if isinstance(sec, bool) or not isinstance(sec, (int, float)) or not math.isfinite(float(sec)) or float(sec) < 0:
            return None, "seconds is not finite and non-negative"
        if payload_sha(rec.get("run")) != rec.get("payload_sha"):
            return None, "payload checksum mismatch"
        run = from_wire(rec["run"])
        bad = run_problems(run, ds, cfg, folds)
        if bad:
            return None, "schema/shape: " + "; ".join(bad)
        return dict(run=run, seconds=float(sec), payload_sha=rec["payload_sha"]), ""
    except Exception as e:
        return None, f"unreadable or undecodable: {type(e).__name__}: {str(e)[:120]}"


# ---------------------------------------------------------------------------------------------------------------
def _cpu_model():
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def environment(man):
    import jax, jaxlib, scipy, joblib
    env = dict(python=platform.python_version(), jax=jax.__version__, jaxlib=jaxlib.__version__, numpy=np.__version__,
               scipy=scipy.__version__, joblib=joblib.__version__, machine=platform.machine(), node=platform.node(),
               backend=str(jax.default_backend()), jax_platforms=os.environ.get("JAX_PLATFORMS"), cpu=_cpu_model(),
               threads={k: os.environ.get(k) for k in THREAD_VARS})
    w = man.get("environment", {}).get("wrapper")
    env["wrapper"] = w
    env["wrapper_sha256"] = sha_file(w) if (w and os.path.exists(w)) else None
    return env


def check_environment(man):
    env = environment(man)
    want = man["environment"]
    bad = [k for k in ("python", "jax", "jaxlib", "numpy", "scipy", "joblib", "machine") if str(want.get(k)) != str(env[k])]
    if want.get("backend") and env["backend"] != want["backend"]:
        bad.append("backend")
    if any(env["threads"].get(k) != "1" for k in THREAD_VARS):
        bad.append("threads")
    if want.get("wrapper_sha256"):
        if env["wrapper_sha256"] != want["wrapper_sha256"]:
            bad.append("wrapper_sha256")
    return env, bad


def check_code(man):
    got = {f: sha_file(os.path.join(T1, f)) for f in man["code"]["files"]}
    bad = [f for f, want in man["code"]["files"].items() if want and want != got[f]]
    return got, bad


def _index_read(index_path):
    lk = open(index_path + ".lock", "a+")
    try:
        fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        return json.load(open(index_path)) if os.path.exists(index_path) else {}
    finally:
        fcntl.flock(lk.fileno(), fcntl.LOCK_UN); lk.close()


def _index_merge(index_path, key, value):
    """Read-merge-write of the shared task index under its lock: concurrent reps never lose one another's entries."""
    lk = open(index_path + ".lock", "a+")
    try:
        fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        idx = json.load(open(index_path)) if os.path.exists(index_path) else {}
        idx[key] = value
        write_atomic(index_path, idx)
    finally:
        fcntl.flock(lk.fileno(), fcntl.LOCK_UN); lk.close()


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
    ap.add_argument("--kind", default="main", help="main|c1|c2|c3 (the reservation's kind and the declared role)")
    ap.add_argument("--authorize-original-recompute", default=None, metavar="REASON",
                    help="recompute a lost ORIGINAL beside a committed checkpoint; recorded in the task binding")
    ap.add_argument("--skip-environment-check", action="store_true", help="tests only: the fixture environment is not Lengau's")
    ap.add_argument("--no-reservation", action="store_true", help="tests only")
    a = ap.parse_args(argv)
    t_main = time.time()
    man = json.load(open(a.manifest))
    manifest_sha = sha_file(a.manifest)
    root = a.root or man["storage"]["root"]
    campaign = a.campaign or man["storage"]["campaign"]
    kind = a.kind
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
    deadline = None if a.pbs_kill_control else t_main + walltime_s - reserve_s
    cores = int(man["pbs"]["cores"])
    # R2: the declared task domain - rep, resolved seed, kind, target and kill mode - before anything is reserved or owned
    ctl = man.get("control", {})
    if kind not in ("main", "c1", "c2", "c3"):
        return held(f"kind {kind!r} is not a declared role")
    if kind == "main":
        if int(a.rep) not in [int(r) for r in man["datasets"]["reps"]]:
            return held(f"rep {a.rep} is not in the declared datasets.reps {man['datasets']['reps']}")
        if a.until is not None or a.pbs_kill_control:
            return held("a main run carries no target and no kill mode")
    else:
        if int(a.rep) != int(ctl.get("rep", -1)) or a.until is None or int(a.until) != int(ctl.get("target", -1)):
            return held(f"control role {kind}: rep must be {ctl.get('rep')} and --until must be {ctl.get('target')}")
        if (kind == "c2") != bool(a.pbs_kill_control):
            return held(f"control role {kind}: --pbs-kill-control is {'required' if kind == 'c2' else 'not allowed'}")
    # R2: the resolved seed and its declared value, before any reservation (they need only the manifest and the rep)
    st = man["setting"]; c = man["cfg"]
    kw = dict(st["grid"])
    ds_seed = S.dataset_seed(st["generator"], kw, int(a.rep), int(st["D"]), int(man["datasets"]["seed_base"]))
    excluded = set(int(x) for x in man["datasets"].get("excluded_resolved_seeds", []))
    if ds_seed in excluded:
        return held(f"resolved dataset seed {ds_seed} is in the declared exclusion set")
    declared = man["datasets"].get("resolved_seeds", {})
    if str(a.rep) in declared and int(declared[str(a.rep)]) != int(ds_seed):
        return held(f"resolved seed {ds_seed} differs from the declared {declared[str(a.rep)]} for rep {a.rep}")
    # R1: the campaign reservation, bound to this job with this job's filled request, before anything else
    ledger = CampaignLedger(campaign, man["budget"]["core_hours_cap"])
    if not a.no_reservation:
        if not a.reservation_token:
            return held("no --reservation-token: reserve before qsub (chpc/row19_ledger.py reserve)")
        try:
            entry = ledger.runner_start(a.reservation_token, a.job_id, kind, int(a.rep), root, cores, walltime_s)
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
    index_path = os.path.join(root, "task_index.json")
    code_exit = HELD
    stop_reason = {}
    try:
        cfg = A.Config(start_policy=c["start_policy"], interval=c["interval"], n_boot_refit=int(c["n_boot_refit"]),
                       n_starts=int(c["n_starts"]), n_starts_inner=int(c["n_starts_inner"]),
                       refit_min_usable=float(c["refit_min_usable"]), n_outer=int(c["n_outer"]), n_inner=int(c["n_inner"]))
        theta = S.generator_theta(st["generator"], **kw)
        ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]),
                            layers=np.array(st["layers"]), rho=float(st["rho"]), seed=ds_seed)
        ds.meta.update(generator=st["generator"], theta=[float(x) for x in theta], D=int(st["D"]), rho=float(st["rho"]), seed=int(ds_seed))
        code_hash = S.config_hash(cfg, int(st["D"]), st["layers"], ds_seed, float(st["rho"]))
        folds = A.stratified_folds(ds.family, cfg.n_outer, ds_seed)
        ident = A.dataset_identity(ds, cfg, ds_seed, cfg.n_boot_refit, folds)
        ckpt_path = os.path.join(root, "ckpt", f"refit_{ident[:24]}.jsonl")
        orig_path = os.path.join(root, "orig", f"orig_{ident[:24]}.json")
        print(f"rep {a.rep} ({kind}): dataset seed {ds_seed}, code/config {code_hash}, identity {ident[:16]}, policy {cfg.start_policy}, "
              f"target {'all ' + str(cfg.n_boot_refit) if a.until is None else '0..' + str(int(a.until) - 1)}", flush=True)
        # R2/D: fresh versus recovering, decided from the root's task index and prior evidence BEFORE any binding is created
        binding = dict(manifest_sha=manifest_sha, rep=int(a.rep), ds_seed=int(ds_seed), ident=ident, code_hash=code_hash,
                       policy=cfg.start_policy, n_rep=int(cfg.n_boot_refit), until=a.until, ckpt=ckpt_path, orig=orig_path,
                       numerical=json.loads(json.dumps(A.numerical_snapshot(), default=str)))   # the producer's snapshot, for consumers elsewhere
        index = _index_read(index_path)
        if os.path.exists(task_path):
            task = json.load(open(task_path))
            diff = [k for k in binding if task.get("binding", {}).get(k) != binding[k]]
            if diff:
                return held(f"task binding differs on {diff}: this is not the task that was started in {root}")
        else:
            prior = [p for p in (status_path, timing_path, os.path.join(root, f"STOP_ACK_rep{a.rep}.json")) if os.path.exists(p)]
            if str(a.rep) in index or prior or os.path.exists(ckpt_path) or os.path.exists(orig_path):
                return held(f"no task binding for rep {a.rep} but prior evidence exists ({'index' if str(a.rep) in index else ''} "
                            f"{[os.path.basename(p) for p in prior]} ckpt={os.path.exists(ckpt_path)} orig={os.path.exists(orig_path)}): "
                            f"unexplained binding loss; holding")
            task = dict(binding=binding, created=time.time(), runs=[], expected_accepted=0, recompute_authorizations=[],
                        watermark_rule="expected_accepted is advanced after every durable record (record fsynced first, then this "
                                       "file); a crash between the two leaves it at most one record behind, which the next start "
                                       "tolerates; it never decreases")
            write_atomic(task_path, task)
            _index_merge(index_path, str(a.rep), dict(ident=ident, created=time.time()))
        # D: inspect the checkpoint without fitting, against the per-record watermark
        cs = A.checkpoint_state(ds, cfg, ds_seed, cfg.n_boot_refit, folds, ckpt_path)
        if cs["rejected"] or cs["duplicates_conflicting"]:
            return held(f"checkpoint {ckpt_path}: {cs['rejected']} record(s) this run cannot accept, {cs['duplicates_conflicting']} conflicting duplicates; holding for diagnosis")
        if len(cs["accepted"]) < int(task.get("expected_accepted", 0)):
            return held(f"checkpoint holds {len(cs['accepted'])} accepted records but {task['expected_accepted']} were committed by earlier runs: lost or rolled-back progress")
        print(f"checkpoint: {len(cs['accepted'])} accepted record(s), watermark {task.get('expected_accepted', 0)}, tail fragment {cs['tail_fragment']}", flush=True)
        # R5: the current stop request and the memory diagnosis BEFORE any original work
        mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2**30
        def ack(boundary, n_done):
            req = ledger.current_stop(int(a.rep))
            if req is not None:
                write_atomic(os.path.join(root, f"STOP_ACK_rep{a.rep}.json"),
                             dict(request_id=req.get("id"), scope=req.get("scope"), requested=req.get("requested"), job=a.job_id,
                                  rep=int(a.rep), boundary=boundary, n_done=int(n_done), t=time.time()))
        if ledger.stop_requested(int(a.rep)):
            ack("before the original", len(cs["accepted"]))
            print(f"rep {a.rep}: stop requested before any work; acknowledged; exit 75", flush=True)
            code_exit = RESUME
            return code_exit
        if mem_stop and maxrss_bytes() > mem_stop:
            return held(f"memory at admission {maxrss_bytes()/2**30:.2f} GiB already exceeds the {mem_stop/2**30:.2f} GiB stop")
        # A/D/R6: the original run - the validated cache, or computed only when no committed record depends on it
        t0 = time.time()
        orig, why = (read_orig(orig_path, ident, code_hash, ds, cfg, folds) if os.path.exists(orig_path) else (None, "absent"))
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
            bad = run_problems(run, ds, cfg, folds)
            if bad:
                return held("the original run's output does not meet the schema: " + "; ".join(bad))
            psha = write_orig(orig_path, run, ident, code_hash, orig_seconds)
            back, why2 = read_orig(orig_path, ident, code_hash, ds, cfg, folds)
            if back is None:
                return held(f"the original-run cache does not read back: {why2}")
        else:
            run, orig_seconds, orig_cached, psha = orig["run"], orig["seconds"], True, orig["payload_sha"]
        print(f"original run: {orig_seconds:.1f} s ({'cached' if orig_cached else 'computed'}), failed={run.get('failed')}, payload {psha[:12]}", flush=True)
        if run.get("failed"):
            return held(f"the original run failed: {run.get('failed_reason')}")
        # G/R5: the stop boundary and the memory stop, checked before every dispatch and after the last record
        def over_memory():
            return bool(mem_stop) and maxrss_bytes() > mem_stop
        def should_stop():
            if ledger.stop_requested(int(a.rep)):
                stop_reason.setdefault("request", ledger.current_stop(int(a.rep)))
                return True
            if over_memory():
                stop_reason.setdefault("memory", maxrss_bytes())
                return True
            return False
        n_before = len(open(timing_path).read().splitlines()) if os.path.exists(timing_path) else 0
        progress = {"n": len(cs["accepted"])}
        def on_record(rec):
            with open(timing_path, "a") as fh:
                fh.write(json.dumps(dict(rep=rec["rep"], fit_seconds=rec["fit_seconds"], failed=rec["failed"], t=time.time(),
                                         job=a.job_id, maxrss_bytes=maxrss_bytes())) + "\n"); fh.flush(); os.fsync(fh.fileno())
            progress["n"] += 1                                           # R2: the watermark advances per durable record
            task["expected_accepted"] = max(int(task.get("expected_accepted", 0)), progress["n"])
            write_atomic(task_path, task)
        try:
            rb = A.refit_bootstrap(ds, cfg, ds_seed, n_rep=cfg.n_boot_refit, outer_folds=folds, min_usable=cfg.refit_min_usable,
                                   checkpoint_path=ckpt_path, segment=a.segment, deadline=deadline, strict_restore=True,
                                   durable=True, on_record=on_record, until=a.until, should_stop=should_stop)
        except A.CheckpointDamaged as e:
            return held(str(e))
        t_chain_end = time.time()
        # R5: after the last record (and on a no-work restore): the current stop and memory state
        stopped_by_request = bool(rb["stopped_by_request"]) or ledger.stop_requested(int(a.rep))
        memory_breach = bool(stop_reason.get("memory")) or over_memory()
        new_fits = ([float(l.get("fit_seconds", 0)) for l in (json.loads(x) for x in open(timing_path).read().splitlines()[n_before:] if x.strip())]
                    if os.path.exists(timing_path) else [])
        status = dict(phase="chain_done", rep=int(a.rep), job=a.job_id, kind=kind, ident=ident, code_hash=code_hash, policy=cfg.start_policy,
                      seed=int(ds_seed), n_rep=int(cfg.n_boot_refit), until=a.until, segment=rb["segment"], n_done=rb["n_done"], n_new=rb["n_new"],
                      n_resumed=rb["n_resumed"], n_damaged=rb["n_damaged"], n_tail_repaired=rb["n_tail_repaired"], partial=rb["partial"],
                      target_complete=rb["target_complete"], stopped_at_deadline=rb["stopped_at_deadline"],
                      stopped_by_request=stopped_by_request, memory_breach=memory_breach, stop_reason=stop_reason,
                      original_seconds=orig_seconds, original_cached=orig_cached, original_payload_sha=psha,
                      original_note="wall seconds of run_dataset in this process when computed fresh (jit compilation INCLUDED, not separated); "
                                    "the cached value when restored",
                      refit_fit_seconds_total=rb["fit_seconds"], first_new_fit_s=(new_fits[0] if new_fits else None),
                      median_new_fit_s=(float(np.median(new_fits)) if new_fits else None),
                      compilation_note="jit compilation is NOT measured; the first new resample's excess over the median new resample of this job is a proxy only",
                      chain_wall_seconds=t_chain_end - t_main, environment=env, code=code, checkpoint=rb["checkpoint"],
                      manifest_sha=manifest_sha, reservation=a.reservation_token)
        write_atomic(status_path, status)
        # B: aggregate from the cached original and the validated completed chain - no fit is bought; the companion kept
        if not rb["partial"]:
            t_f = time.time()
            res = A.analyze_dataset(ds, cfg, ds_seed, outer_folds=folds, run=run, interval_result=rb)
            status["result"] = {p: dict(decision=res["predictors"][p]["decision"], ws=res["predictors"][p]["ws"],
                                        cluster_ws=res["predictors"][p].get("cluster", {}).get("ws")) for p in A.PREDICTORS}
            status["interval"] = {k: v for k, v in res.get("interval", {}).items() if k != "replicates"}
            status["aggregation_seconds"] = time.time() - t_f
        # R5: the current request and the sampled peak are refreshed AFTER aggregation (a crossing inside it counts)
        t_pub = time.time()
        stopped_by_request = stopped_by_request or ledger.stop_requested(int(a.rep))
        memory_breach = memory_breach or over_memory()
        if memory_breach:
            stop_reason.setdefault("memory", maxrss_bytes())
        if memory_breach:
            code_exit = HELD
        elif rb["partial"]:
            code_exit = RESUME
        else:
            code_exit = DONE
        status.update(phase="final", stopped_by_request=stopped_by_request, memory_breach=memory_breach, stop_reason=stop_reason,
                      exit=code_exit,
                      measurement_scope="wall_seconds_main runs from main() start (imports before main excluded) to the terminal boundary "
                                        "after the status, acknowledgment and task writes and BEFORE the final status rewrite and the ledger's "
                                        "runner_end write (those two are excluded); cpu_seconds_lifetime and maxrss_bytes are RUSAGE_SELF for "
                                        "the whole process (imports included), SAMPLED AT THAT SAME TERMINAL BOUNDARY, so utilisation mixes "
                                        "the two scopes; the stop request and the peak are re-read at that boundary too; aggregation_seconds is the "
                                        "aggregation only; publication_seconds is the status, acknowledgment and task writes after aggregation, "
                                        "excluding the final status rewrite and the ledger write; wrapper and PBS start-up are not measured; "
                                        "compilation is not measured; scheduler-accounted allocated time is settled in the campaign ledger",
                      finished=t_pub)
        write_atomic(status_path, status)
        if stopped_by_request:
            ack("after aggregation" if (not rb["partial"] and rb["n_new"]) else "after the last durable record" if rb["n_new"]
                else ("no work remaining" if not rb["partial"] else "no work bought"), rb["n_done"])
        task["runs"].append(dict(job=a.job_id, kind=kind, started=t_main, ended=time.time(), exit=code_exit, n_done=rb["n_done"], n_new=rb["n_new"]))
        task["expected_accepted"] = max(int(task.get("expected_accepted", 0)), int(rb["n_done"]))
        write_atomic(task_path, task)
        # R5/R7: the declared terminal-publication boundary - the request and the peak re-read, CPU/RSS sampled HERE
        t_term = time.time()
        late_stop = ledger.current_stop(int(a.rep))
        if late_stop is not None and not stopped_by_request:
            stopped_by_request = True
            ack("at publication", rb["n_done"])
        if over_memory() and not memory_breach:
            memory_breach = True; stop_reason.setdefault("memory", maxrss_bytes()); code_exit = HELD
        ru = resource.getrusage(resource.RUSAGE_SELF)
        status.update(stopped_by_request=stopped_by_request, memory_breach=memory_breach, stop_reason=stop_reason, exit=code_exit,
                      cpu_seconds_lifetime=ru.ru_utime + ru.ru_stime, maxrss_bytes=maxrss_bytes(),
                      publication_seconds=t_term - t_pub, wall_seconds_main=t_term - t_main,
                      utilisation=(ru.ru_utime + ru.ru_stime) / max(t_term - t_main, 1e-9), sampled_at="terminal boundary")
        write_atomic(status_path, status)
        if code_exit == HELD and task["runs"] and task["runs"][-1].get("job") == a.job_id:
            task["runs"][-1]["exit"] = code_exit; write_atomic(task_path, task)
        if code_exit == HELD:
            return held(f"memory stop: maxrss {maxrss_bytes()/2**30:.2f} GiB exceeds {mem_stop/2**30:.2f} GiB; chain flushed at a record boundary")
        print(f"rep {a.rep}: {'COMPLETE' if code_exit == DONE else 'PARTIAL (resume)'}: done {rb['n_done']}/{cfg.n_boot_refit}, "
              f"new {rb['n_new']}, resumed {rb['n_resumed']}, wall {status['wall_seconds_main']/60:.1f} min, maxrss {status['maxrss_bytes']/2**30:.2f} GiB"
              + (f", target 0..{int(a.until)-1} complete" if rb["target_complete"] else "")
              + (", stopped by request" if stopped_by_request else ""), flush=True)
        return code_exit
    finally:
        if not a.no_reservation and a.reservation_token:
            try:
                ledger.runner_end(a.reservation_token, time.time() - t_main, code_exit)
            except Exception as e:
                print(f"ledger: runner_end failed: {e}", flush=True)
        try:
            fcntl.flock(task_lock.fileno(), fcntl.LOCK_UN); task_lock.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
