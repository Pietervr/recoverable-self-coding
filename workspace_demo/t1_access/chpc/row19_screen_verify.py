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

REVISION 2 (Codex RSC a1ce224): only CANONICAL file names count (rec_<iii>.json exactly; any other name in a records
directory - rec_000_extra.json beside rec_000.json - is reported, never parsed into an index); two valid sequential records
for one index that differ are a CONFLICT (reported; identical duplicates are harmless); every index the shard root and the
sequential chain both hold is compared, and index 0 is required for all three anchors.

REVISION 3 (Codex RSC ee99ee1, R3 and R7): file names are ASCII only - `rec_[0-9]{3}.json` and `rep[1-9][0-9]*|rep0` - and must
equal the formatted name of the coordinate they parse to; two files for one logical (rep, index) are a conflict; the document
carries its CONTROLLER GENERATION (the lineage version this verifier's bytes belong to, its own SHA-256, the controls file's
SHA-256 and the lineage check's verdict), so a consumer can refuse evidence produced by another generation.
"""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, math, glob, hashlib, argparse, time, re

CANON = re.compile(r"^rec_([0-9]{3})\.json$", re.ASCII)
REPDIR = re.compile(r"^rep(0|[1-9][0-9]*)$", re.ASCII)


def canonical_index(name):
    """The index of an exactly formatted ASCII record name, else None."""
    m = CANON.match(name)
    return int(m.group(1)) if m and name == f"rec_{int(m.group(1)):03d}.json" else None


def generation():
    """The controller generation of THIS verifier: the lineage version whose files include these bytes."""
    cp = os.path.join(HERE, "row19_screen_controls.json")
    me = sha_file(os.path.abspath(__file__))
    try:
        ctl = json.load(open(cp)); latest = ctl["versions"][-1]
        mine = [v["version"] for v in ctl["versions"] if v["files"].get("chpc/row19_screen_verify.py") == me]
        bad = [f for f, h in latest["files"].items() if not os.path.exists(os.path.join(T1, f)) or sha_file(os.path.join(T1, f)) != h]
        return dict(verify_sha256=me, controls_sha256=sha_file(cp), version=(mine[-1] if mine else None), latest=latest["version"],
                    controls_problem=(f"controllers {bad} are not version {latest['version']}" if bad else ""))
    except Exception as e:
        return dict(verify_sha256=me, controls_sha256=None, version=None, latest=None, controls_problem=f"lineage unreadable: {e}")

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
        e = dict(required=list(an["required_overlap"][str(r)]), compared=[], equal=[], differ=[], missing=[], invalid=[], conflict=[])
        if 0 not in e["required"]:
            e["invalid"].append("index 0 is not among the required overlaps")
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
                i = int(d["rep"])
                if i in seq and payload(seq[i]) != payload(d):
                    e["conflict"].append(i); continue
                seq[i] = d
        shard = {}
        for p in glob.glob(os.path.join(sroot, "records", f"rep{int(r)}", "*")):
            i = canonical_index(os.path.basename(p))
            if i is None:
                e["invalid"].append(f"non-canonical file {os.path.basename(p)!r}"); continue
            if i in shard:
                e["conflict"].append(i); continue
            try:
                shard[i] = SH.read_record(p, t, i)
            except ValueError as ex:
                e["invalid"].append(str(ex)[:160])
        both = sorted((set(seq) & set(shard)) - set(e["conflict"]))
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
        seen_reps = set()
        for d in sorted(glob.glob(os.path.join(root, "records", "*"))):
            mrep = REPDIR.match(os.path.basename(d))
            rs = mrep.group(1) if mrep else None
            if rs is None or int(rs) not in reps or int(rs) in seen_reps:
                units[f"?{os.path.basename(d)!r}"] = dict(record=dict(ok=False, reason="undeclared, aliased or duplicated rep directory")); continue
            r = int(rs); seen_reps.add(r); t = task(r)
            for p in sorted(glob.glob(os.path.join(d, "*"))):
                i = canonical_index(os.path.basename(p))
                if i is None or f"{r}/{i}" in units:
                    units[f"{r}/?{os.path.basename(p)!r}"] = dict(record=dict(ok=False, reason="non-canonical or duplicated file name")); continue
                u = {}
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
               generation=generation(),
               units=units, bindings=bindings, anchors=anchors(man))
    print(json.dumps(doc, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
