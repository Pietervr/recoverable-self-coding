"""Ledger row 19, STAGE 2 (the screen): the LOSSLESS producer of the screen datasets' original fits (Codex RSC 9202e8b, item 3).

Each worker runs, for each assigned screen rep, the literal canonical original call the slice runner makes -
`A.run_dataset(ds, cfg, seed, outer_folds=folds)` on the task `row19_shard.task(man, rep)` builds - and keeps the COMPLETE
run in the slice runner's original-cache contract (`row19_slice` schema row19-orig-v3: every RUN_KEYS field as typed raw
bytes at full precision, payload and metadata checksums, the identity and code hash), so the later sealed collector can hand
`analyze_dataset` the full original (deltas, folds, layers, members, selections, logq, n_c, flags, convergence, parameters)
and never buys one. The bank's reduced band-mean record is NOT used for the screen.

Publication: built exactly as `row19_slice.write_orig`, then published by temp + fsync + hard LINK (never replaces an existing
cache: two producers cannot overwrite each other); the timing file first; the cache READ BACK and validated with
`row19_slice.read_orig` against this task's identity, code hash, dataset, cfg and folds before the worker reports it. A failed
original is a cache like any other (its `failed` flag and reason kept) and is reported, never retried for a better outcome.

LAYOUT under the originals root:  orig/orig_<ident[:24]>.json  (the slice runner's name),  timing/o<rrr>.json,
status/job<J>.slot<S>.json (always written),  plans/job_<n>.json, logs/, gate/, STOP.
The screen's task bindings live in the REFIT root (row19_shard job-start); this producer checks the manifest's declared
identity per rep instead and never writes a binding.

SUBCOMMANDS (each through the pinned wrapper t1py):
  job-start --manifest M --plan P --job-id J --walltime-s W --reservation-token T
  worker    --manifest M --reps 3,7 --slot S --job-id J --deadline-epoch E
  job-end   --manifest M --plan P --job-id J --reservation-token T --started-epoch E
Exit codes: 0 done, 75 deadline or STOP with work left, 4 HELD. The ledger kind is "orig" (rep = the job number)."""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, time, argparse, resource, platform, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(os.path.join(HERE, "..")), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import analyze as A
import row19_slice as R19
import row19_shard as SH
from row19_ledger import CampaignLedger

DONE, RESUME, HELD = 0, 75, 4
KIND = "orig"


def held(msg):
    print(f"HELD: {msg}", flush=True)
    return HELD


def screen_reps(man):
    return [int(r) for r in man["datasets"]["reps"]]


def orig_path(root, ident):
    return os.path.join(root, "orig", f"orig_{ident[:24]}.json")


def timing_path(root, rep):
    return os.path.join(root, "timing", f"o{int(rep):03d}.json")


def task_checked(man, rep):
    """The rep's task, refused when its identity is not the manifest's declared one."""
    t = SH.task(man, rep)
    want = man["datasets"].get("identities", {}).get(str(rep))
    if want != t["ident"]:
        raise ValueError(f"rep {rep}: this runtime computes identity {t['ident'][:16]}, the manifest declares {str(want)[:16]}")
    return t


def build_cache(run, t, seconds):
    """The cache document exactly as row19_slice.write_orig builds it (to_wire, payload and metadata checksums)."""
    wire = R19.to_wire(run)
    rec = dict(schema=R19.ORIG_SCHEMA, ident=t["ident"], code_hash=t["code_hash"], seconds=float(seconds),
               payload_sha=R19.payload_sha(wire), written=time.time(), run=wire)
    rec["meta_sha"] = R19.meta_sha(rec)
    return rec


def publish_cache(path, rec):
    """temp + fsync + LINK (never replaces) + directory fsync; the same JSON form as row19_slice.write_atomic writes."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    try:
        with open(tmp, "w") as fh:
            json.dump(rec, fh, indent=1, sort_keys=True, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
        try:
            os.link(tmp, path)
        except FileExistsError:
            raise ValueError(f"{path}: already exists (two producers for one dataset, or a file that appeared meanwhile)")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    d = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


def read_cache(root, t):
    """(run, '') for a valid cache of this task, (None, 'absent') when there is none; raises ValueError otherwise (HOLDS)."""
    p = orig_path(root, t["ident"])
    if not os.path.exists(p):
        return None, "absent"
    got, why = R19.read_orig(p, t["ident"], t["code_hash"], t["ds"], t["cfg"], t["folds"])
    if got is None:
        raise ValueError(f"{p}: an original cache this task cannot accept ({why})")
    return got, ""


def cmd_job_start(a):
    man = json.load(open(a.manifest)); plan = json.load(open(a.plan)); root = man["storage"]["root"]
    why = SH.admission(man, a.skip_environment_check)
    if why:
        return held(why)
    slots = plan.get("slots", []); cores = int(man["pbs"]["cores"])
    if len(slots) > cores or len({s["slot"] for s in slots}) != len(slots):
        return held(f"the plan has {len(slots)} slots for {cores} cores, or a repeated slot")
    declared, seen = set(screen_reps(man)), set()
    for s in slots:
        for r in s["reps"]:
            if int(r) not in declared or int(r) in seen:
                return held(f"slot {s['slot']}: screen rep {r} is not declared or is repeated in the plan")
            seen.add(int(r))
    if not a.no_reservation:
        try:
            e = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).runner_start(
                a.reservation_token, a.job_id, KIND, int(plan["job"]), root, cores, float(a.walltime_s))
        except Exception as ex:
            return held(f"reservation: {ex}")
        print(f"reservation {e['token']}: original job {plan['job']}, {e['reserved_core_h']:.1f} core-h", flush=True)
    for sub in ("orig", "timing", "status", "logs", "plans", "gate"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    print(f"original job {plan['job']} admitted: {len(slots)} slots, {len(seen)} datasets", flush=True)
    return DONE


def cmd_worker(a):
    t0 = time.time()
    man = json.load(open(a.manifest)); root = a.root or man["storage"]["root"]
    status = os.path.join(root, "status", f"job{a.job_id}.slot{a.slot}.json")
    os.makedirs(os.path.dirname(status), exist_ok=True)
    st = dict(job=a.job_id, slot=int(a.slot), reps=[], new=[], resumed=[], left=[], failed_originals=[], exit=HELD, reason="",
              host=platform.node(), started=t0)

    def finish(code, reason):
        st.update(exit=code, reason=reason, left=[r for r in st["reps"] if r not in st["new"] and r not in st["resumed"]],
                  wall_s=time.time() - t0, maxrss=SH.maxrss_bytes(), cpu_s=sum(resource.getrusage(resource.RUSAGE_SELF)[:2]), ended=time.time())
        if code == DONE and st["left"]:
            st["exit"] = code = RESUME
        R19.write_atomic(status, st)
        print(f"original worker job {a.job_id} slot {a.slot}: exit {code} new {st['new']} resumed {st['resumed']} left {st['left']} {reason}", flush=True)
        return code
    try:
        why = SH.admission(man, a.skip_environment_check)
        if why:
            return finish(held(why), why)
        try:
            reps = [int(x) for x in a.reps.split(",") if x.strip() != ""]
        except ValueError:
            return finish(held("reps are not integers"), "reps are not integers")
        st["reps"] = reps
        if len(set(reps)) != len(reps) or any(r not in set(screen_reps(man)) for r in reps):
            why = f"reps {reps} repeat or are not declared"
            return finish(held(why), why)
        mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
        expect = float(man["originals"].get("expect_original_s", 0) or 0)
        margin = float(man["originals"].get("deadline_margin", 1.25))
        stop_file = os.path.join(root, "STOP")

        def memory_breach():
            return bool(mem_stop) and SH.maxrss_bytes() > mem_stop
        longest = 0.0
        for r in reps:
            try:
                t = task_checked(man, r)
                got, _ = read_cache(root, t)
            except ValueError as e:
                return finish(held(str(e)), str(e))
            if got is not None:
                st["resumed"].append(r); continue
            if os.path.exists(stop_file):
                return finish(RESUME, "stop requested (STOP file)")
            if memory_breach():
                why = f"memory: maxrss {SH.maxrss_bytes()/2**30:.2f} GiB above the stop, before rep {r}"
                return finish(held(why), why)
            need = max(expect, margin * longest)
            if a.deadline_epoch is not None and time.time() + need > float(a.deadline_epoch):
                return finish(RESUME, f"deadline: {float(a.deadline_epoch) - time.time():.0f} s left, {need:.0f} s needed")
            t1 = time.time()
            run = A.run_dataset(t["ds"], t["cfg"], t["seed"], outer_folds=t["folds"])
            wall = time.time() - t1; longest = max(longest, wall)
            bad = R19.run_problems(run, t["ds"], t["cfg"], t["folds"])
            if bad:
                why = f"rep {r}: the original's output does not meet the cache schema: {'; '.join(bad)}"
                return finish(held(why), why)
            rec = build_cache(run, t, wall)
            try:
                SH.publish(timing_path(root, r), dict(rep=int(r), seed=int(t["seed"]), ident=t["ident"], fit_seconds=float(run.get("fit_seconds", 0.0)),
                                                      wall_s=wall, failed=bool(run["failed"]), maxrss=SH.maxrss_bytes(), t=time.time(),
                                                      job=a.job_id, slot=int(a.slot), host=platform.node()), replace=True)
                publish_cache(orig_path(root, t["ident"]), rec)
                back, _ = read_cache(root, t)
            except ValueError as e:
                return finish(held(str(e)), str(e))
            if back is None:
                return finish(held(f"rep {r}: the cache did not read back"), "read-back failed")
            st["new"].append(r)
            if run["failed"]:
                st["failed_originals"].append(dict(rep=int(r), reason=str(run.get("failed_reason", ""))[:300]))
            print(f"  rep {r}: {wall:.0f} s wall, failed={bool(run['failed'])}, payload {rec['payload_sha'][:12]}, maxrss {SH.maxrss_bytes()/2**30:.2f} GiB", flush=True)
            if memory_breach():
                why = f"memory: maxrss {SH.maxrss_bytes()/2**30:.2f} GiB above the stop after rep {r} (its cache is published and kept)"
                return finish(held(why), why)
        if memory_breach():
            return finish(held("memory: above the stop at the terminal check"), "memory at the terminal check")
        return finish(DONE, "")
    except BaseException as e:
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
    print(f"original job {plan['job']} ended: exit {code}; worker exit codes {codes}; wall {wall:.0f} s", flush=True)
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
    a = ap.parse_args(argv)
    return {"job-start": cmd_job_start, "worker": cmd_worker, "job-end": cmd_job_end}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
