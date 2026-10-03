"""Row 19, the SHARDED route (owner, 3 October 2026: "yes - spin up as many cores as possible"): the refit chain's resamples
computed by many single-core workers, one resample index per record file, instead of one core walking the chain in order.

WHY IT IS THE SAME COMPUTATION. In `analyze.refit_bootstrap` every resample is a pure function of the dataset, the Config,
the seed, B and its own index: the draw `idx[rep]` comes from `stratified_resample(family, B, default_rng(seed))`, the
resampled dataset keeps each copy in its original outer fold, and the fit seed is `seed + 1 + rep`. Nothing carries from
one resample to the next. `resample_record` below is that function's body (`one(rep)` plus the on-file form `_save`
gives a record), unchanged; the canonical sources (analyze.py, models.py, simulate.py) are NOT edited, so the numerical
snapshot, and with it the dataset identity, is exactly the sequential chain's. A shard record therefore carries the same
identity, seed, B, index, draw, statistics and checksum form as a sequential record and is accepted by the same
`analyze._record_ok`; a file of shard records in index order is a valid sequential checkpoint. EVIDENCE that the body is
the same: the fixtures compare shard records with the sequential path's records field by field, the test pins the
source text of `one` it was copied from, and in production the shard records for the indices the sequential jobs also
compute (C1's 0..7, the mains' first records) are compared on their canonical scientific payload, float bits included
(`row19_shard_status.py`). The pin holds for THIS analyze.py only: a changed canonical source needs the copy re-verified.

WHAT IT IS NOT. It reads no coverage and aggregates nothing: it produces validated per-index records and timings. The
interval, the original fit, pooling with sequential records and any coverage reading stay with their own steps and gates.

LAYOUT under the shard root:
  records/rep<R>/rec_<iii>.json   ONE record; published by temp + fsync + hard LINK (never replaces an existing file)
  timing/rep<R>/t_<iii>.json      the measurement of that record (wall, fit seconds, peak memory, job, slot, host), published
                                  the same way BEFORE the record, so every published record has its timing; a timing file
                                  without a record (a death between the two) is replaced when the index is computed again
  status/job<J>.slot<S>.json      one per worker, ALWAYS written (also on an exception): indices, new, resumed, left, exit
  task_<R>.json                   the binding in the runner's shape, published once under a lock, never rewritten
  plans/job_<n>.json, logs/, gate/ (the operator's watch receipts and the pilot's qualification), STOP
A record that exists, names THIS index and passes `_record_ok` is never recomputed; any other file at a record path HOLDS.

STOPS (what this implementation enforces, no more): the STOP file and the deadline rule are checked BEFORE each resample
(a fit in flight is never interrupted, so a stop takes effect at the next resample boundary, possibly many hours later;
the deadline rule is a heuristic from this worker's own timings, not a bound on a fit); memory (ru_maxrss against the
per-worker stop) is checked before each resample, after each published record and before the terminal status, and a
breach HOLDS the worker (exit 4) with the evidence kept - an operational stop, not an invalid record.

SUBCOMMANDS (each a separate process; on Lengau each is run through the pinned wrapper t1py):
  job-start --manifest M --plan P --job-id J --walltime-s W --reservation-token T     admission of the packed job
  worker    --manifest M --rep R --indices 3,7 --slot S --job-id J --deadline-epoch E  one single-core worker
  job-end   --manifest M --plan P --job-id J --reservation-token T --started-epoch E   the runner's wall and exit in the ledger
Exit codes as the runner's: 0 done, 75 stopped at the deadline or by request with work left (resume), 4 HELD."""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, time, argparse, resource, platform, fcntl, glob, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
import analyze as A, simulate as S
import row19_slice as R19
from row19_ledger import CampaignLedger

DONE, RESUME, HELD = 0, 75, 4
# The source of analyze.refit_bootstrap's `one` that resample_record reproduces (sha256 of its text at the pinned
# analyze.py 97558aa9...); the test fails if the pinned source's `one` changes without this file being re-verified.
ONE_SOURCE_SHA256 = "7dd4f596ae99cc08b254f65466ff85af2fae9233116ba4e9fa27c2e42703515f"


def held(msg):
    print(f"HELD: {msg}", flush=True)
    return HELD


def config(man):
    c = man["cfg"]
    return A.Config(start_policy=c["start_policy"], interval=c["interval"], n_boot_refit=int(c["n_boot_refit"]),
                    n_starts=int(c["n_starts"]), n_starts_inner=int(c["n_starts_inner"]), refit_min_usable=float(c["refit_min_usable"]),
                    n_outer=int(c["n_outer"]), n_inner=int(c["n_inner"]))


def task(man, rep):
    """The frozen task of a dataset rep: dataset, Config, seed, B, folds, identity, the full draw matrix, the band names."""
    st = man["setting"]; cfg = config(man)
    if int(rep) not in [int(r) for r in man["datasets"]["reps"]]:
        raise ValueError(f"rep {rep} is not a declared dataset")
    kw = dict(st["grid"]); theta = S.generator_theta(st["generator"], **kw)
    seed = S.dataset_seed(st["generator"], kw, int(rep), int(st["D"]), int(man["datasets"]["seed_base"]))
    declared = man["datasets"].get("resolved_seeds", {})
    if str(rep) in declared and int(declared[str(rep)]) != int(seed):
        raise ValueError(f"resolved seed {seed} differs from the declared {declared[str(rep)]} for rep {rep}")
    ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]), layers=np.array(st["layers"]),
                        rho=float(st["rho"]), seed=seed)
    ds.meta.update(generator=st["generator"], theta=[float(x) for x in theta], D=int(st["D"]), rho=float(st["rho"]), seed=int(seed))
    folds = A.stratified_folds(ds.family, cfg.n_outer, seed)
    n_rep = int(cfg.n_boot_refit)
    ident = A.dataset_identity(ds, cfg, seed, n_rep, folds)
    idx = A.stratified_resample(ds.family, n_rep, np.random.default_rng(seed))
    masks = {b: m for b, m in A.band_masks(ds.layers, cfg.bands).items() if m.any()}
    bands = list(masks) + (["ws_minus_early"] if "ws" in masks and "early" in masks else [])
    code_hash = S.config_hash(cfg, int(st["D"]), st["layers"], seed, float(st["rho"]))
    return dict(ds=ds, cfg=cfg, seed=int(seed), n_rep=n_rep, folds=folds, ident=ident, idx=idx, masks=masks, bands=bands, code_hash=code_hash)


def resample_record(t, rep):
    """ONE resample's checkpoint record, exactly as analyze.refit_bootstrap computes and writes it (`one(rep)`, then the
    on-file form of `_save`): same draw, same resampled dataset and folds, same fit seed, same statistics, same checksum."""
    ds, cfg, seed, n_rep, base_folds, idx, masks = t["ds"], t["cfg"], t["seed"], t["n_rep"], t["folds"], t["idx"], t["masks"]
    fold_of = np.full(ds.n_concepts, -1, dtype=np.int64)
    for r, f in enumerate(base_folds):
        fold_of[np.asarray(f)] = r
    if np.any(fold_of < 0):
        raise ValueError("outer_folds do not cover every concept")
    rows_by_concept = [np.where(ds.concept == c)[0] for c in range(ds.n_concepts)]
    chosen = idx[rep]
    rows = np.concatenate([rows_by_concept[c] for c in chosen])
    new_concept = np.concatenate([np.full(rows_by_concept[c].size, j) for j, c in enumerate(chosen)])
    family = ds.family[chosen]
    folds = [f for f in (np.where(fold_of[chosen] == r)[0] for r in range(len(base_folds))) if f.size]
    sub = A.Dataset(ds.y[rows], ds.k[rows], new_concept, family, ds.layers, group=chosen)
    run = A.run_dataset(sub, cfg, seed + 1 + rep, outer_folds=folds)
    stats = {p: A._band_stats(np.asarray(run["delta"][p], dtype=float), masks) for p in A.PREDICTORS}
    s = dict(rep=int(rep), stats=stats, failed=bool(run["failed"]), failed_reason=run.get("failed_reason", ""),
             fit_seconds=float(run.get("fit_seconds", 0.0)), chosen=[int(c) for c in chosen])
    rec = dict(s, ident=t["ident"], seed=int(seed), n_rep=int(n_rep))
    rec = json.loads(json.dumps(rec, default=float))          # the checksum is over the on-file representation
    rec["sha"] = A._record_sha(rec)
    return rec


def record_path(root, rep, index):
    return os.path.join(root, "records", f"rep{int(rep)}", f"rec_{int(index):03d}.json")


def timing_path(root, rep, index):
    return os.path.join(root, "timing", f"rep{int(rep)}", f"t_{int(index):03d}.json")


def read_record(path, t, index):
    """The record in a file when it exists, names THIS index and passes analyze._record_ok for this task; None when absent;
    raises when a file is present and unacceptable (a record is never silently recomputed over evidence, and a valid
    record of another index under this index's name is not this index's record)."""
    if not os.path.exists(path):
        return None
    try:
        d = json.load(open(path))
    except Exception as e:
        raise ValueError(f"{path}: not JSON ({e})")
    if not A._record_ok(d, t["ident"], t["seed"], t["n_rep"], t["idx"], t["bands"]):
        raise ValueError(f"{path}: a record this task cannot accept (identity, index, draw, payload or checksum)")
    if d["rep"] != int(index):
        raise ValueError(f"{path}: holds the record of index {d['rep']}, not of index {int(index)}")
    return d


def publish(path, obj, replace=False):
    """temp + fsync + hard link (never replaces) + directory fsync. `replace` is for a timing file without its record."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(obj) + "\n"); fh.flush(); os.fsync(fh.fileno())
    try:
        if replace:
            os.replace(tmp, path)
        else:
            try:
                os.link(tmp, path)                             # fails if the target exists: an atomic no-replace publish
            except FileExistsError:
                raise ValueError(f"{path}: already exists (two writers for one index, or a file that appeared meanwhile)")
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    dfd = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def write_record(path, rec, index=None):
    if index is not None and rec.get("rep") != int(index):
        raise ValueError(f"{path}: refusing to publish the record of index {rec.get('rep')} under index {int(index)}")
    publish(path, rec)


def maxrss_bytes():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(r) if platform.system() == "Darwin" else int(r) * 1024


def binding_for(man, manifest_sha, root, rep, t):
    """The task binding in the runner's shape (so the identity oracle, the comparator's contract and the watch read it)."""
    return dict(manifest_sha=manifest_sha, rep=int(rep), ds_seed=int(t["seed"]), ident=t["ident"], code_hash=t["code_hash"],
                policy=t["cfg"].start_policy, n_rep=int(t["n_rep"]), until=None,
                ckpt=os.path.join(root, "records", f"rep{int(rep)}"), orig=os.path.join(root, "orig"),
                numerical=json.loads(json.dumps(A.numerical_snapshot(), default=str)))


def binding_problem(root, rep, b, create):
    """'' when <root>/task_<rep>.json holds exactly this binding. With `create`, a missing binding is published once (under
    a lock, by link, never rewritten) - unless shard evidence for that rep already exists without it, which HOLDS."""
    tp = os.path.join(root, f"task_{rep}.json")
    os.makedirs(root, exist_ok=True)
    with open(tp + ".lock", "a+") as lk:
        fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        if os.path.exists(tp):
            try:
                old = json.load(open(tp)).get("binding", {})
            except Exception as e:
                return f"rep {rep}: the task binding in {root} is unreadable ({e})"
            diff = [k for k in b if old.get(k) != b[k]] + [k for k in old if k not in b]
            return f"rep {rep}: the task binding in {root} differs on {diff}" if diff else ""
        if not create:
            return f"rep {rep}: no task binding in {root} (job-start publishes it; a worker never does)"
        evid = glob.glob(os.path.join(root, "records", f"rep{rep}", "rec_*.json")) + glob.glob(os.path.join(root, "timing", f"rep{rep}", "t_*.json"))
        if evid:
            return f"rep {rep}: {len(evid)} record/timing file(s) exist in {root} without a task binding; holding, not creating new provenance"
        publish(tp, dict(binding=b))
        return ""


def admission(man, skip_env):
    env, bad_env = R19.check_environment(man)
    if bad_env and not skip_env:
        return f"environment differs from the manifest on {bad_env}: {env}"
    code, bad_code = R19.check_code(man)
    if bad_code:
        return f"code hashes differ from the manifest's pins on {bad_code}"
    return ""


def cmd_job_start(a):
    man = json.load(open(a.manifest)); manifest_sha = R19.sha_file(a.manifest)
    plan = json.load(open(a.plan)); root = man["storage"]["root"]
    why = admission(man, a.skip_environment_check)
    if why:
        return held(why)
    slots = plan.get("slots", [])
    cores = int(man["pbs"]["cores"])
    if len(slots) > cores or len({s["slot"] for s in slots}) != len(slots):
        return held(f"the plan has {len(slots)} slots for {cores} cores, or a repeated slot")
    seen = set()
    for s in slots:
        if int(s["rep"]) not in [int(r) for r in man["datasets"]["reps"]]:
            return held(f"slot {s['slot']}: rep {s['rep']} is not a declared dataset")
        for i in s["indices"]:
            key = (int(s["rep"]), int(i))
            if key in seen or not (0 <= int(i) < int(man["cfg"]["n_boot_refit"])):
                return held(f"slot {s['slot']}: index {i} of rep {s['rep']} is repeated in the plan or out of range")
            seen.add(key)
    if not a.no_reservation:
        try:
            e = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).runner_start(
                a.reservation_token, a.job_id, "shard", int(plan["job"]), root, cores, float(a.walltime_s))
        except Exception as ex:
            return held(f"reservation: {ex}")
        print(f"reservation {e['token']}: shard job {plan['job']}, {e['reserved_core_h']:.1f} core-h", flush=True)
    for sub in ("records", "timing", "status", "logs", "plans", "gate"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    env, _ = R19.check_environment(man)
    print(f"environment: python {env['python']} jax {env['jax']} numpy {env['numpy']} scipy {env['scipy']} {env['machine']} "
          f"backend {env['backend']} wrapper {str(env.get('wrapper_sha256'))[:12]}; code pins verified for {sorted(man['code']['files'])}", flush=True)
    idents = man.get("shard", {}).get("identities", {})
    for rep in sorted({int(s["rep"]) for s in slots}):
        t = task(man, rep)
        if str(rep) in idents and idents[str(rep)] != t["ident"]:
            return held(f"rep {rep}: this process computes identity {t['ident'][:16]}, the manifest declares {idents[str(rep)][:16]}")
        why = binding_problem(root, rep, binding_for(man, manifest_sha, root, rep, t), create=True)
        if why:
            return held(why)
        print(f"rep {rep}: seed {t['seed']}, identity {t['ident'][:16]}, B {t['n_rep']}, binding published or equal", flush=True)
    print(f"job {plan['job']} admitted: {len(slots)} slots, {len(seen)} indices, start {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}", flush=True)
    return DONE


def cmd_worker(a):
    t0 = time.time()
    man = json.load(open(a.manifest)); root = a.root or man["storage"]["root"]
    sh = man.get("shard", {})
    status = os.path.join(root, "status", f"job{a.job_id}.slot{a.slot}.json")
    os.makedirs(os.path.dirname(status), exist_ok=True)
    st = dict(job=a.job_id, slot=int(a.slot), rep=int(a.rep), ident=None, indices=[], new=[], resumed=[], left=[], exit=HELD, reason="",
              host=platform.node(), started=t0)
    def finish(code, reason):
        st.update(exit=code, reason=reason, left=[i for i in st["indices"] if i not in st["new"] and i not in st["resumed"]],
                  wall_s=time.time() - t0, maxrss=maxrss_bytes(), cpu_s=sum(resource.getrusage(resource.RUSAGE_SELF)[:2]), ended=time.time())
        if code == DONE and st["left"]:
            st["exit"] = code = RESUME
        R19.write_atomic(status, st)
        print(f"worker job {a.job_id} slot {a.slot}: exit {code} new {st['new']} resumed {st['resumed']} left {st['left']} {reason}", flush=True)
        return code
    try:
        why = admission(man, a.skip_environment_check)
        if why:
            return finish(held(why), why)
        try:
            t = task(man, a.rep)
        except Exception as e:
            return finish(held(f"task: {e}"), f"task: {e}")
        st["ident"] = t["ident"]
        idents = sh.get("identities", {})
        if str(a.rep) in idents and idents[str(a.rep)] != t["ident"]:
            why = f"rep {a.rep}: identity {t['ident'][:16]} is not the manifest's {idents[str(a.rep)][:16]}"
            return finish(held(why), why)
        try:
            indices = [int(x) for x in a.indices.split(",") if x.strip() != ""]
        except ValueError:
            return finish(held("indices are not integers"), "indices are not integers")
        st["indices"] = indices
        if len(set(indices)) != len(indices) or any(not (0 <= i < t["n_rep"]) for i in indices):
            why = f"indices {indices} repeat or lie outside 0..{t['n_rep']-1}"
            return finish(held(why), why)
        if not a.no_binding_check:
            why = binding_problem(root, a.rep, binding_for(man, R19.sha_file(a.manifest), root, a.rep, t), create=False)
            if why:
                return finish(held(why), why)
        mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
        expect = float(sh.get("expect_layer_s", 0) or 0)
        margin = float(sh.get("deadline_margin", 1.25))
        stop_file = os.path.join(root, "STOP")
        def memory_breach():
            return bool(mem_stop) and maxrss_bytes() > mem_stop
        longest = 0.0
        print(f"worker job {a.job_id} slot {a.slot}: rep {a.rep} identity {t['ident'][:16]} indices {indices}", flush=True)
        for i in indices:
            path = record_path(root, a.rep, i)
            try:
                if read_record(path, t, i) is not None:
                    st["resumed"].append(i); continue
            except ValueError as e:
                return finish(held(str(e)), str(e))
            if os.path.exists(stop_file):
                return finish(RESUME, "stop requested (STOP file)")
            if memory_breach():
                why = f"memory: maxrss {maxrss_bytes()/2**30:.2f} GiB above the {mem_stop/2**30:.2f} GiB stop, before index {i}"
                return finish(held(why), why)
            need = max(expect, margin * longest)
            if a.deadline_epoch is not None and time.time() + need > float(a.deadline_epoch):
                return finish(RESUME, f"deadline: {float(a.deadline_epoch) - time.time():.0f} s left, {need:.0f} s needed for the next resample")
            t1 = time.time()
            rec = resample_record(t, i)
            wall = time.time() - t1; longest = max(longest, wall)
            try:
                publish(timing_path(root, a.rep, i), dict(rep=int(a.rep), index=int(i), ident=t["ident"], fit_seconds=rec["fit_seconds"], wall_s=wall,
                                                          failed=rec["failed"], maxrss=maxrss_bytes(), t=time.time(), job=a.job_id,
                                                          slot=int(a.slot), host=platform.node()), replace=True)
                write_record(path, rec, i)
            except ValueError as e:
                return finish(held(str(e)), str(e))
            st["new"].append(i)
            print(f"  index {i}: {wall:.0f} s wall, fit {rec['fit_seconds']:.0f} s, failed={rec['failed']}, maxrss {maxrss_bytes()/2**30:.2f} GiB", flush=True)
            if memory_breach():
                why = f"memory: maxrss {maxrss_bytes()/2**30:.2f} GiB above the {mem_stop/2**30:.2f} GiB stop, after index {i} (its record is published and kept)"
                return finish(held(why), why)
        if memory_breach():
            why = f"memory: maxrss {maxrss_bytes()/2**30:.2f} GiB above the {mem_stop/2**30:.2f} GiB stop at the terminal check"
            return finish(held(why), why)
        return finish(DONE, "")
    except BaseException as e:                                  # a fit, I/O or any other error: ALWAYS a status, never silence
        why = f"exception: {type(e).__name__}: {e}"
        traceback.print_exc()
        return finish(held(why), why)


def cmd_job_end(a):
    man = json.load(open(a.manifest)); plan = json.load(open(a.plan)); root = man["storage"]["root"]
    codes = []
    for s in plan.get("slots", []):
        p = os.path.join(root, "status", f"job{a.job_id}.slot{s['slot']}.json")
        try:
            codes.append(json.load(open(p)).get("exit") if os.path.exists(p) else None)
        except Exception:
            codes.append(None)
    code = HELD if (not codes or any(c not in (DONE, RESUME) for c in codes)) else (RESUME if any(c == RESUME for c in codes) else DONE)
    wall = max(0.0, time.time() - float(a.started_epoch))
    if not a.no_reservation:
        try:
            CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).runner_end(a.reservation_token, wall, code)
        except Exception as ex:
            print(f"job-end: the ledger entry could not be updated ({ex})", flush=True)
    print(f"job {plan['job']} ended: exit {code}; workers exit codes {codes}; wall {wall:.0f} s", flush=True)
    return code


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("job-start", "worker", "job-end"):
        p = sub.add_parser(name)
        p.add_argument("--manifest", required=True)
        p.add_argument("--job-id", default=os.environ.get("PBS_JOBID", f"local-{int(time.time())}"))
        p.add_argument("--skip-environment-check", action="store_true", help="tests only")
        p.add_argument("--no-reservation", action="store_true", help="tests only")
        if name != "worker":
            p.add_argument("--plan", required=True); p.add_argument("--reservation-token", default=None)
        if name == "job-start":
            p.add_argument("--walltime-s", type=float, required=True)
        if name == "job-end":
            p.add_argument("--started-epoch", type=float, required=True)
        if name == "worker":
            p.add_argument("--root", default=None); p.add_argument("--rep", type=int, required=True)
            p.add_argument("--indices", required=True); p.add_argument("--slot", type=int, required=True)
            p.add_argument("--deadline-epoch", type=float, default=None)
            p.add_argument("--no-binding-check", action="store_true", help="the admission smoke only: no task binding is required")
    a = ap.parse_args(argv)
    return {"job-start": cmd_job_start, "worker": cmd_worker, "job-end": cmd_job_end}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
