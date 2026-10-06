"""Ledger row 22: the omega = 1 POLICY-MATCHED REFERENCE BANK for the stage-2 refitting-bootstrap screen (row 19).

WHAT IT COMPUTES. The coverage estimand (design record section 5) is the expectation of the complete procedure's band-mean
difference under the generator, over stimulus draws, folds and optimiser randomness - estimated by the mean of many
INDEPENDENT datasets run through the SAME procedure the screen runs. The bank therefore runs, for each of its own datasets,
exactly the original fit the slice and the screen run (`analyze.run_dataset(ds, cfg, seed, outer_folds=folds)` with the
dataset, Config, seed and folds built by `row19_shard.task`, i.e. the slice manifest's setting, cfg, start policy and code
pins) and keeps its band statistics. It computes NO bootstrap and reads no coverage; `row22_target.py` turns the records
into the target set T and the evaluator that refuses incompatible references.

WHY A NEW BANK. The historical omega = 1 reference (the 1,000-row d4v12b mean, -0.8695) is old-policy evidence: the start-policy
audit moved the M2S omega = 1 mean by about +0.23 nat per trial under a stronger search, about half the refit interval's
half-width at omega = 1 (0.48). A target computed under another fitter policy is not the screen's estimand.

SEEDS. Dataset seeds are `simulate.dataset_seed(generator, grid, rep, D, seed_base)` with the bank's OWN seed base; job-start
recomputes every declared bank seed and refuses when two coincide, when any meets the manifest's excluded set (every
historical M2S omega 1/2 identity the slice manifest excludes, plus the slice's and the screen's resolved seeds) or when the
list's SHA-256 differs from the manifest's.

LAYOUT under the bank root:
  records/b<rrr>.json          ONE record per bank dataset; published by temp + fsync + hard LINK (never replaces)
  timing/b<rrr>.json           its measurement, published first (replace allowed: a timing without its record is redone)
  status/job<J>.slot<S>.json   one per worker, ALWAYS written (also on an exception)
  bank_binding.json            manifest SHA-256, policy, code pins, numerical snapshot, seed list SHA-256; published once
  plans/job_<n>.json, logs/, gate/, STOP
A record that exists, names THIS bank rep and passes `record_ok` is never recomputed; any other file at a record path HOLDS.

STOPS: the STOP file and the deadline rule before each dataset (a fit in flight is never interrupted); memory (ru_maxrss
against the per-worker stop) before each dataset, after each published record and at the terminal check; a breach HOLDS.

SUBCOMMANDS (each a separate process; on Lengau each through the pinned wrapper t1py):
  job-start --manifest M --plan P --job-id J --walltime-s W --reservation-token T
  worker    --manifest M --reps 3,7 --slot S --job-id J --deadline-epoch E
  job-end   --manifest M --plan P --job-id J --reservation-token T --started-epoch E
Exit codes: 0 done, 75 stopped at the deadline or by request with work left (resume), 4 HELD."""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, time, math, argparse, resource, platform, fcntl, glob, hashlib, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
import analyze as A, simulate as S
import row19_slice as R19
import row19_shard as SH
from row19_ledger import CampaignLedger

DONE, RESUME, HELD = 0, 75, 4
RECORD_SCHEMA = "row22-bank-record-1"
BINDING_SCHEMA = "row22-bank-binding-1"
KIND = "bank"


def held(msg):
    print(f"HELD: {msg}", flush=True)
    return HELD


def bank_reps(man):
    return [int(r) for r in man["datasets"]["reps"]]


def resolved_seeds(man):
    """{bank rep: resolved dataset seed}, recomputed from the manifest's setting and seed base."""
    st = man["setting"]; kw = dict(st["grid"])
    return {r: int(S.dataset_seed(st["generator"], kw, int(r), int(st["D"]), int(man["datasets"]["seed_base"]))) for r in bank_reps(man)}


def seeds_sha256(seeds):
    return hashlib.sha256(json.dumps([[int(r), int(s)] for r, s in sorted(seeds.items())]).encode()).hexdigest()


def seed_problems(man):
    """Why the bank's seeds cannot be used ('' when they can): duplicates, a member of the excluded set, or a list that is not
    the one the manifest declares."""
    seeds = resolved_seeds(man)
    vals = list(seeds.values())
    if len(set(vals)) != len(vals):
        return "two bank datasets resolve to the same seed"
    excl = {int(x) for x in man["datasets"].get("excluded_resolved_seeds", [])}
    hit = sorted(set(vals) & excl)
    if hit:
        return f"{len(hit)} bank seed(s) are in the excluded set, e.g. {hit[:3]}"
    want = man["datasets"].get("resolved_seeds_sha256")
    if want and want != seeds_sha256(seeds):
        return "the recomputed bank seed list is not the manifest's (resolved_seeds_sha256)"
    return ""


def record_path(root, rep):
    return os.path.join(root, "records", f"b{int(rep):03d}.json")


def timing_path(root, rep):
    return os.path.join(root, "timing", f"b{int(rep):03d}.json")


def original_record(t, rep):
    """ONE bank record: the original fit exactly as the slice runner computes it (row19_slice.py: `A.run_dataset(ds, cfg,
    ds_seed, outer_folds=folds)`), reduced to its band statistics per predictor (`A._band_stats`, strict: a band with any
    non-finite score is NaN)."""
    run = A.run_dataset(t["ds"], t["cfg"], t["seed"], outer_folds=t["folds"])
    stats = {p: A._band_stats(np.asarray(run["delta"][p], dtype=float), t["masks"]) for p in A.PREDICTORS}
    rec = dict(schema=RECORD_SCHEMA, bank_rep=int(rep), seed=int(t["seed"]), ident=t["ident"], code_hash=t["code_hash"],
               policy=t["cfg"].start_policy, failed=bool(run["failed"]), failed_reason=run.get("failed_reason", "") or "",
               fit_seconds=float(run.get("fit_seconds", 0.0)), stats=stats)
    rec = json.loads(json.dumps(rec, default=float))          # the checksum is over the on-file representation
    rec["sha"] = A._record_sha(rec)
    return rec


def record_ok(d, t, rep):
    """A bank record is reused only if its schema, rep, seed, identity, code hash, policy, flags, complete statistics payload
    (every predictor, every band, numeric; NaN allowed and counted as unusable later) and checksum all check."""
    try:
        if not isinstance(d, dict) or d.get("schema") != RECORD_SCHEMA:
            return False
        if d.get("bank_rep") != int(rep) or d.get("seed") != int(t["seed"]) or d.get("ident") != t["ident"]:
            return False
        if d.get("code_hash") != t["code_hash"] or d.get("policy") != t["cfg"].start_policy:
            return False
        if not (isinstance(d.get("failed"), bool) and isinstance(d.get("failed_reason"), str)
                and isinstance(d.get("fit_seconds"), (int, float)) and not isinstance(d.get("fit_seconds"), bool)):
            return False
        st = d.get("stats")
        if not (isinstance(st, dict) and all(isinstance(st.get(p), dict) for p in A.PREDICTORS)):
            return False
        for p in A.PREDICTORS:
            for b in t["bands"]:
                v = st[p].get(b)
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    return False
        return d.get("sha") == A._record_sha(d)
    except Exception:
        return False


def read_record(path, t, rep):
    """The valid record at `path`, None when absent; raises ValueError for anything else (which HOLDS)."""
    if not os.path.exists(path):
        return None
    try:
        d = json.loads(open(path).read())
    except Exception as e:
        raise ValueError(f"{path}: not JSON ({e})")
    if not record_ok(d, t, rep):
        raise ValueError(f"{path}: a record this bank cannot accept (schema, rep, seed, identity, code hash, policy, payload or checksum)")
    return d


def binding(man, manifest_sha):
    seeds = resolved_seeds(man)
    t0 = SH.task(man, bank_reps(man)[0])
    return dict(schema=BINDING_SCHEMA, manifest_sha=manifest_sha, policy=t0["cfg"].start_policy, code=dict(man["code"]["files"]),
                setting=man["setting"], cfg={k: v for k, v in man["cfg"].items() if k != "note"},
                seed_base=int(man["datasets"]["seed_base"]), n=len(seeds), seeds_sha256=seeds_sha256(seeds),
                numerical=json.loads(json.dumps(A.numerical_snapshot(), default=str)))


def binding_problem(root, b, create):
    """'' when <root>/bank_binding.json holds exactly this binding; with `create`, a missing binding is published once, unless
    bank evidence already exists without it (HOLDS)."""
    bp = os.path.join(root, "bank_binding.json")
    os.makedirs(root, exist_ok=True)
    with open(bp + ".lock", "a+") as lk:
        fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        if os.path.exists(bp):
            try:
                old = json.load(open(bp))
            except Exception as e:
                return f"the bank binding in {root} is unreadable ({e})"
            diff = [k for k in b if old.get(k) != b[k]] + [k for k in old if k not in b]
            return f"the bank binding in {root} differs on {diff}" if diff else ""
        if not create:
            return f"no bank binding in {root} (job-start publishes it; a worker never does)"
        evid = glob.glob(os.path.join(root, "records", "b*.json")) + glob.glob(os.path.join(root, "timing", "b*.json"))
        if evid:
            return f"{len(evid)} record/timing file(s) exist in {root} without a bank binding; holding, not creating new provenance"
        SH.publish(bp, b)
        return ""


def cmd_job_start(a):
    man = json.load(open(a.manifest)); manifest_sha = R19.sha_file(a.manifest)
    plan = json.load(open(a.plan)); root = man["storage"]["root"]
    why = SH.admission(man, a.skip_environment_check)
    if why:
        return held(why)
    why = seed_problems(man)
    if why:
        return held(why)
    slots = plan.get("slots", []); cores = int(man["pbs"]["cores"])
    if len(slots) > cores or len({s["slot"] for s in slots}) != len(slots):
        return held(f"the plan has {len(slots)} slots for {cores} cores, or a repeated slot")
    declared, seen = set(bank_reps(man)), set()
    for s in slots:
        for r in s["reps"]:
            if int(r) not in declared or int(r) in seen:
                return held(f"slot {s['slot']}: bank rep {r} is not declared or is repeated in the plan")
            seen.add(int(r))
    if not a.no_reservation:
        try:
            e = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).runner_start(
                a.reservation_token, a.job_id, KIND, int(plan["job"]), root, cores, float(a.walltime_s))
        except Exception as ex:
            return held(f"reservation: {ex}")
        print(f"reservation {e['token']}: bank job {plan['job']}, {e['reserved_core_h']:.1f} core-h", flush=True)
    for sub in ("records", "timing", "status", "logs", "plans", "gate"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    why = binding_problem(root, binding(man, manifest_sha), create=True)
    if why:
        return held(why)
    env, _ = R19.check_environment(man)
    print(f"environment: python {env['python']} jax {env['jax']} numpy {env['numpy']} {env['machine']} backend {env['backend']}; "
          f"code pins verified for {sorted(man['code']['files'])}; bank binding published or equal", flush=True)
    print(f"bank job {plan['job']} admitted: {len(slots)} slots, {len(seen)} datasets, start {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}", flush=True)
    return DONE


def cmd_worker(a):
    t0 = time.time()
    man = json.load(open(a.manifest)); root = a.root or man["storage"]["root"]
    status = os.path.join(root, "status", f"job{a.job_id}.slot{a.slot}.json")
    os.makedirs(os.path.dirname(status), exist_ok=True)
    st = dict(job=a.job_id, slot=int(a.slot), reps=[], new=[], resumed=[], left=[], exit=HELD, reason="", host=platform.node(), started=t0)

    def finish(code, reason):
        st.update(exit=code, reason=reason, left=[r for r in st["reps"] if r not in st["new"] and r not in st["resumed"]],
                  wall_s=time.time() - t0, maxrss=SH.maxrss_bytes(), cpu_s=sum(resource.getrusage(resource.RUSAGE_SELF)[:2]), ended=time.time())
        if code == DONE and st["left"]:
            st["exit"] = code = RESUME
        R19.write_atomic(status, st)
        print(f"bank worker job {a.job_id} slot {a.slot}: exit {code} new {st['new']} resumed {st['resumed']} left {st['left']} {reason}", flush=True)
        return code
    try:
        why = SH.admission(man, a.skip_environment_check)
        if why:
            return finish(held(why), why)
        try:
            reps = [int(x) for x in a.reps.split(",") if x.strip() != ""]
        except ValueError:
            return finish(held("bank reps are not integers"), "bank reps are not integers")
        st["reps"] = reps
        declared = set(bank_reps(man))
        if len(set(reps)) != len(reps) or any(r not in declared for r in reps):
            why = f"bank reps {reps} repeat or are not declared"
            return finish(held(why), why)
        if not a.no_binding_check:
            why = binding_problem(root, binding(man, R19.sha_file(a.manifest)), create=False)
            if why:
                return finish(held(why), why)
        mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
        expect = float(man["pbs"].get("expect_original_s", 0) or 0)
        margin = float(man["pbs"].get("deadline_margin", 1.25))
        stop_file = os.path.join(root, "STOP")

        def memory_breach():
            return bool(mem_stop) and SH.maxrss_bytes() > mem_stop
        longest = 0.0
        print(f"bank worker job {a.job_id} slot {a.slot}: reps {reps}", flush=True)
        for r in reps:
            try:
                t = SH.task(man, r)
            except Exception as e:
                return finish(held(f"task of bank rep {r}: {e}"), f"task of bank rep {r}: {e}")
            path = record_path(root, r)
            try:
                if read_record(path, t, r) is not None:
                    st["resumed"].append(r); continue
            except ValueError as e:
                return finish(held(str(e)), str(e))
            if os.path.exists(stop_file):
                return finish(RESUME, "stop requested (STOP file)")
            if memory_breach():
                why = f"memory: maxrss {SH.maxrss_bytes()/2**30:.2f} GiB above the {mem_stop/2**30:.2f} GiB stop, before bank rep {r}"
                return finish(held(why), why)
            need = max(expect, margin * longest)
            if a.deadline_epoch is not None and time.time() + need > float(a.deadline_epoch):
                return finish(RESUME, f"deadline: {float(a.deadline_epoch) - time.time():.0f} s left, {need:.0f} s needed for the next dataset")
            t1 = time.time()
            rec = original_record(t, r)
            wall = time.time() - t1; longest = max(longest, wall)
            try:
                SH.publish(timing_path(root, r), dict(bank_rep=int(r), seed=int(t["seed"]), fit_seconds=rec["fit_seconds"], wall_s=wall,
                                                      failed=rec["failed"], maxrss=SH.maxrss_bytes(), t=time.time(), job=a.job_id,
                                                      slot=int(a.slot), host=platform.node()), replace=True)
                SH.publish(path, rec)
            except ValueError as e:
                return finish(held(str(e)), str(e))
            st["new"].append(r)
            print(f"  bank rep {r}: {wall:.0f} s wall, fit {rec['fit_seconds']:.0f} s, failed={rec['failed']}, maxrss {SH.maxrss_bytes()/2**30:.2f} GiB", flush=True)
            if memory_breach():
                why = f"memory: maxrss {SH.maxrss_bytes()/2**30:.2f} GiB above the {mem_stop/2**30:.2f} GiB stop, after bank rep {r} (its record is published and kept)"
                return finish(held(why), why)
        if memory_breach():
            why = f"memory: maxrss {SH.maxrss_bytes()/2**30:.2f} GiB above the {mem_stop/2**30:.2f} GiB stop at the terminal check"
            return finish(held(why), why)
        return finish(DONE, "")
    except BaseException as e:                                  # ALWAYS a status, never silence
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
    print(f"bank job {plan['job']} ended: exit {code}; worker exit codes {codes}; wall {wall:.0f} s", flush=True)
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
            p.add_argument("--root", default=None); p.add_argument("--reps", required=True)
            p.add_argument("--slot", type=int, required=True); p.add_argument("--deadline-epoch", type=float, default=None)
            p.add_argument("--no-binding-check", action="store_true", help="tests only")
    a = ap.parse_args(argv)
    return {"job-start": cmd_job_start, "worker": cmd_worker, "job-end": cmd_job_end}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
