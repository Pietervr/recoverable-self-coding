"""Ledger row 19 stage 2: validate the screen's evidence IN THE PRODUCER RUNTIME (login node, t1py) and print ONE JSON document for
the Mac's view (row19_screen_status.py), which binds its SHA-256. Reads only; writes nothing.

--role refit: every record under <root>/records/rep<R>/rec_<iii>.json validated by row19_shard.read_record against the SCREEN
              task; its timing <root>/timing/rep<R>/t_<iii>.json (parsed, this rep/index/identity, finite non-negative
              measurements, job and slot); every task binding <root>/task_<R>.json equal to what this runtime recomputes
              (row19_shard.binding_problem) and its SHA-256.
--role orig:  every lossless cache <root>/orig/orig_<ident24>.json read back with row19_slice.read_orig against the declared
              task, its timing <root>/timing/o<rrr>.json, and the failed flag.
ANCHORS (both roles; Codex RSC 9202e8b item 2): for each declared development anchor rep (0, 1, 2) under ITS OWN contract - the
development shard manifest named and hashed in the screen manifest, `row19_shard.task(shard_manifest, rep)` - the shard root's
record at every REQUIRED overlap index and every other index the shard root and the slice's sequential checkpoint both hold
are validated (row19_shard.read_record; analyze._record_ok on the sequential line) and compared on the canonical scientific
payload, float bits included. Missing required evidence, an invalid record or any difference is reported; nothing is relabelled.

    t1py chpc/row19_screen_verify.py --manifest chpc/row19_screen_manifest.json --role refit
"""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, math, glob, hashlib, argparse, time

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import analyze as A
import row19_slice as R19
import row19_shard as SH

VERIFY_SCHEMA = "row19-screen-verify-1"
SCI = ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep")


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def finite_nonneg(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def canon(v):
    if isinstance(v, bool) or v is None or isinstance(v, (int, str)):
        return v
    if isinstance(v, float):
        return "f:" + v.hex()
    if isinstance(v, (list, tuple)):
        return [canon(x) for x in v]
    if isinstance(v, dict):
        return {k: canon(v[k]) for k in sorted(v)}
    return repr(v)


def payload(rec):
    return json.dumps({k: canon(rec.get(k)) for k in SCI}, sort_keys=True)


def timing_ok(d, **want):
    if not isinstance(d, dict):
        return "not an object"
    for k, v in want.items():
        if d.get(k) != v:
            return f"{k} {d.get(k)!r} is not {v!r}"
    for k in ("wall_s", "fit_seconds", "maxrss", "t"):
        if not finite_nonneg(d.get(k)):
            return f"{k} is not finite and non-negative"
    if not isinstance(d.get("job"), str) or not isinstance(d.get("slot"), int) or isinstance(d.get("slot"), bool):
        return "job or slot missing"
    return ""


def anchors(man):
    an = man["anchors"]
    sp = os.path.join(T1, an["shard_manifest"])
    if not os.path.exists(sp) or sha_file(sp) != an["shard_manifest_sha256"]:
        return dict(problem="the anchors' shard manifest is absent or not the declared bytes", reps={})
    sman = json.load(open(sp)); sroot = sman["storage"]["root"]; seq_root = an["sequential_root"]
    out = {}
    for r in an["reps"]:
        e = dict(required=list(an["required_overlap"][str(r)]), compared=[], equal=[], differ=[], missing=[], invalid=[])
        try:
            t = SH.task(sman, int(r))
        except Exception as ex:
            out[str(r)] = dict(e, problem=f"task: {ex}"); continue
        seq = {}
        ck = os.path.join(seq_root, "ckpt", f"refit_{t['ident'][:24]}.jsonl")
        if os.path.exists(ck):
            for line in open(ck).read().splitlines():
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    e["invalid"].append("sequential line not JSON"); continue
                if not A._record_ok(d, t["ident"], t["seed"], t["n_rep"], t["idx"], t["bands"]):
                    e["invalid"].append(f"sequential record {d.get('rep')}"); continue
                seq[int(d["rep"])] = d
        shard = {}
        for p in glob.glob(os.path.join(sroot, "records", f"rep{int(r)}", "rec_*.json")):
            i = int(os.path.basename(p)[4:7])
            try:
                shard[i] = SH.read_record(p, t, i)
            except ValueError as ex:
                e["invalid"].append(str(ex)[:160])
        both = sorted(set(seq) & set(shard))
        for i in e["required"]:
            if i not in both:
                e["missing"].append(i)
        for i in both:
            e["compared"].append(i)
            (e["equal"] if payload(seq[i]) == payload(shard[i]) else e["differ"]).append(i)
        e["ident"] = t["ident"]
        out[str(r)] = e
    return dict(problem="", reps=out, shard_manifest_sha256=an["shard_manifest_sha256"])


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True); ap.add_argument("--role", required=True, choices=("refit", "orig"))
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); root = man["storage"]["root"]
    env, bad_env = R19.check_environment(man); _, bad_code = R19.check_code(man)
    reps = [int(r) for r in man["datasets"]["reps"]]; msha = R19.sha_file(a.manifest)
    units, bindings, tasks = {}, {}, {}

    def task(r):
        if r not in tasks:
            tasks[r] = SH.task(man, r)
        return tasks[r]
    if a.role == "refit":
        for d in sorted(glob.glob(os.path.join(root, "records", "rep*"))):
            rs = os.path.basename(d)[3:]
            if not rs.isdigit() or int(rs) not in reps:
                units[f"{rs}/?"] = dict(record=dict(ok=False, reason="undeclared rep")); continue
            r = int(rs); t = task(r)
            for p in sorted(glob.glob(os.path.join(d, "rec_*.json"))):
                i = int(os.path.basename(p)[4:7]); u = {}
                try:
                    rec = SH.read_record(p, t, i); u["record"] = dict(ok=True, sha=rec["sha"], failed=rec["failed"])
                except ValueError as ex:
                    u["record"] = dict(ok=False, reason=str(ex)[:200])
                tp = SH.timing_path(root, r, i)
                if os.path.exists(tp):
                    try:
                        td = json.load(open(tp)); why = timing_ok(td, rep=r, index=i, ident=t["ident"])
                        u["timing"] = dict(ok=not why, reason=why, job=td.get("job"), slot=td.get("slot"))
                    except Exception as ex:
                        u["timing"] = dict(ok=False, reason=str(ex)[:120])
                else:
                    u["timing"] = None
                units[f"{r}/{i}"] = u
        for p in sorted(glob.glob(os.path.join(root, "task_*.json"))):
            rs = os.path.basename(p)[5:-5]
            if not rs.isdigit() or int(rs) not in reps:
                bindings[rs] = dict(ok=False, reason="undeclared rep"); continue
            r = int(rs); t = task(r)
            why = SH.binding_problem(root, r, SH.binding_for(man, msha, root, r, t), create=False)
            bindings[rs] = dict(ok=not why, reason=why, sha256=sha_file(p), ident=t["ident"], declared_ident_equal=t["ident"] == man["datasets"]["identities"].get(rs))
    else:
        import row19_screen_orig as O
        prefix = {man["datasets"]["identities"][str(r)][:24]: r for r in reps}
        for p in sorted(glob.glob(os.path.join(root, "orig", "orig_*.json"))):
            pre = os.path.basename(p)[5:-5]
            if pre not in prefix:
                units[f"?{pre}"] = dict(record=dict(ok=False, reason="no declared identity")); continue
            r = prefix[pre]; u = {}
            try:
                t = O.task_checked(man, r); got, _ = O.read_cache(root, t)
                u["record"] = dict(ok=True, failed=bool(got["run"]["failed"]), payload_sha=got["payload_sha"])
            except ValueError as ex:
                u["record"] = dict(ok=False, reason=str(ex)[:200]); t = task(r)
            tp = O.timing_path(root, r)
            if os.path.exists(tp):
                try:
                    td = json.load(open(tp)); why = timing_ok(td, rep=r, ident=t["ident"])
                    u["timing"] = dict(ok=not why, reason=why, job=td.get("job"), slot=td.get("slot"))
                except Exception as ex:
                    u["timing"] = dict(ok=False, reason=str(ex)[:120])
            else:
                u["timing"] = None
            units[str(r)] = u
    doc = dict(schema=VERIFY_SCHEMA, role=a.role, time=time.time(), manifest_sha256=msha, environment_bad=bad_env, code_bad=bad_code,
               units=units, bindings=bindings, anchors=anchors(man))
    print(json.dumps(doc, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
