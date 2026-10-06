"""Ledger row 22: validate the bank's records IN THE PRODUCER RUNTIME (login node, through the pinned wrapper t1py) and print
one JSON document for the Mac's status view (row22_bank_status.py), which binds its SHA-256 into the watch receipt.

Why here and not on the Mac: a record is valid only against its task's identity, and a dataset rebuilt on another platform
can carry another identity (the shard route needed a producer-runtime oracle for rep 2). This script imports the PINNED
row22_bank (record_ok / read_record against row19_shard.task) and changes nothing on disk.

For every declared bank rep with a record or a timing file: the record's validity (and the reason when not), its checksum,
the failed flag, the timing file's validity (parsed, this rep and seed, finite non-negative wall/fit/maxrss, job and slot
present) and its job/slot. Also: the manifest's SHA-256, the bank binding's SHA-256 and whether it equals what this runtime
recomputes, the seed-gate verdict, the environment and code-pin verdicts.

    t1py chpc/row22_bank_verify.py --manifest chpc/row22_bank_manifest.json
"""
import os
os.environ["NPROC"] = "1"; os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["JAX_PLATFORMS"] = "cpu"
import sys, json, math, glob, hashlib, argparse, time

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(os.path.join(HERE, "..")), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import row22_bank as B
import row19_slice as R19

VERIFY_SCHEMA = "row22-bank-verify-1"


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def finite_nonneg(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def timing_check(path, rep, seed):
    try:
        d = json.load(open(path))
    except Exception as e:
        return dict(ok=False, reason=f"not JSON ({e})")
    if d.get("bank_rep") != rep or d.get("seed") != seed:
        return dict(ok=False, reason="another rep or seed")
    for k in ("wall_s", "fit_seconds", "maxrss", "t"):
        if not finite_nonneg(d.get(k)):
            return dict(ok=False, reason=f"{k} is not finite and non-negative")
    if not isinstance(d.get("job"), str) or not isinstance(d.get("slot"), int) or isinstance(d.get("slot"), bool):
        return dict(ok=False, reason="job or slot missing")
    return dict(ok=True, job=d["job"], slot=d["slot"], wall_s=d["wall_s"], maxrss=d["maxrss"], failed=d.get("failed"))


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); root = man["storage"]["root"]
    env, bad_env = R19.check_environment(man); _, bad_code = R19.check_code(man)
    bp = os.path.join(root, "bank_binding.json")
    binding_equal = None
    if os.path.exists(bp):
        binding_equal = B.binding_problem(root, B.binding(man, R19.sha_file(a.manifest)), create=False) == ""
    reps_with_files = sorted({int(os.path.basename(p)[1:4]) for p in glob.glob(os.path.join(root, "records", "b*.json")) + glob.glob(os.path.join(root, "timing", "b*.json"))
                              if os.path.basename(p)[1:4].isdigit()})
    declared = set(B.bank_reps(man)); out = {}
    for r in reps_with_files:
        e = dict(declared=r in declared)
        if r not in declared:
            out[str(r)] = dict(e, record=dict(ok=False, reason="undeclared rep")); continue
        t = B.SH.task(man, r)
        rp, tp = B.record_path(root, r), B.timing_path(root, r)
        if os.path.exists(rp):
            try:
                d = B.read_record(rp, t, r)
                e["record"] = dict(ok=True, sha=d["sha"], failed=d["failed"], file_sha256=sha_file(rp))
            except ValueError as ex:
                e["record"] = dict(ok=False, reason=str(ex)[:300])
        else:
            e["record"] = None
        e["timing"] = timing_check(tp, r, int(t["seed"])) if os.path.exists(tp) else None
        out[str(r)] = e
    doc = dict(schema=VERIFY_SCHEMA, time=time.time(), manifest_sha256=R19.sha_file(a.manifest),
               bank_binding_sha256=sha_file(bp) if os.path.exists(bp) else None, binding_equal=binding_equal,
               seed_problem=B.seed_problems(man), environment_bad=bad_env, code_bad=bad_code, reps=out)
    print(json.dumps(doc, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
