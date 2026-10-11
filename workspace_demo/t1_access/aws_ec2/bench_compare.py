"""Ledger row 23 (revision 2): validate and compare one benchmark attempt against Lengau. Runs on the Lengau login node
under t1py from the controller tree (rsc_screen_ctl/workspace_demo/t1_access), where the frozen task is computed with
the pinned libraries the screen verifier uses:

    $T/t1py bench_compare.py --tree $T/rsc_screen_ctl/workspace_demo/t1_access --ec2 <attempt dir> --lengau-root $T/row19_screen --row6-ref $T/jobs --out report.json

Prints counts and deviations only - never a statistic's value or a decision (sens600 and the screen stay sealed).
EVERY record (EC2 and Lengau) first passes row19_shard.read_record against the frozen task (identity, seed, B, index,
draw, complete payload, own checksum); payload equality is the verifier's canonical float.hex form
(row19_screen_verify.payload over SCI). Exactly reps 3..38 at index 0 per arm: a missing, extra, invalid, unbound or
unattributed coordinate makes the panel INVALID. Failed fits are counted apart from usable parity. Timings are paired by
coordinate, identity and producer and must be positive and finite. Exit 0 only for a complete, valid panel (whatever the
parity outcome); exit 3 otherwise, with the reasons. A typed arm-A job-start refusal (env/ARM_A_REFUSED, RSC a44f5aa) is arm
A's recorded outcome: its 36 stage-2 workers are not declared (declared.txt), and any arm-A record present is a problem."""
import argparse, csv, glob, hashlib, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# --tree <t1_access> selects the code tree (on Lengau: rsc_screen_ctl's); it must be read before the imports below
T1 = os.path.abspath(sys.argv[sys.argv.index("--tree") + 1]) if "--tree" in sys.argv else os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [T1, os.path.join(T1, "chpc")]
import row19_shard as SH
import row19_screen_verify as V

REPS = list(range(3, 39))
PROD = os.path.join(T1, "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
NUM = ("selection_ws_point", "selection_ws_lo", "selection_ws_hi", "selection_ws_se")
SCALE = 0.5465000938917843
PINS = {"A": "824837ee54af3f5fe43d67427cfdd335afc99e2f6d846333eb030b0e559053fa",
        "B": "08e498c447341dee9f462f10a5570eda4ef58e3c5ad9e418dfc7bc8a4b061955"}
PLAN_PIN = "a67e2e1ce9c9c98455ee7946ec8f141ab50a5a8a473178b89aeaa12957d456d5"
NAMES = [f"row6_{a}_rep{r}" for a in "AB" for r in (0, 20, 40)] + [f"w_{a}_slot{i}" for a in "AB" for i in range(36)]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def numeric_leaves(x, path=""):
    if isinstance(x, dict):
        for k in sorted(x):
            yield from numeric_leaves(x[k], f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from numeric_leaves(v, f"{path}[{i}]")
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield path, float(x)


def read_rows(files):
    rows, dup = {}, []
    for f in files:
        for r in csv.DictReader(open(f)):
            if r.get("rep") not in ("0", "20", "40"):
                dup.append(f"non-canonical rep {r.get('rep')!r}"); continue
            k = int(r["rep"])
            if k in rows:
                dup.append(k)
            rows[k] = r
    return rows, dup


def stage1(ec2, ref_dir, problems):
    ref, dup = read_rows(sorted(glob.glob(os.path.join(ref_dir, "row6_lengau_rows_rep*.csv"))))
    if dup or sorted(ref) != [0, 20, 40]:
        problems.append(f"stage 1: Lengau reference reps {sorted(ref)} duplicates {dup}")
        return {}
    out = {}
    for arm in ("A", "B"):
        rows, dup = read_rows(sorted(glob.glob(os.path.join(ec2, f"row6_{arm}", "row6_rows_rep*.csv"))))
        if dup or sorted(rows) != [0, 20, 40]:
            problems.append(f"stage 1 arm {arm}: reps {sorted(rows)} duplicates {dup} (need exactly 0, 20, 40)")
            continue
        worst = {q: 0.0 for q in NUM}; exact = 0; dec = True; failed_same = True
        for rp in (0, 20, 40):
            r, m = rows[rp], ref[rp]
            if r["code_hash"] != m["code_hash"] or r["code_hash"] != "625798e9e7f4":
                problems.append(f"stage 1 arm {arm} rep {rp}: code hash"); continue
            try:
                gridok = all(x["generator"] == "M3" and isinstance(json.loads(x["grid"]), dict)
                             and float(json.loads(x["grid"]).get("scale", "nan")) == SCALE for x in (r, m))
            except Exception:
                gridok = False
            if not gridok:
                problems.append(f"stage 1 arm {arm} rep {rp}: generator/grid malformed or not the declared M3 scale point"); continue
            failed_same &= (r["failed"] == m["failed"])
            for q in NUM:
                a, b = float(r[q]), float(m[q])
                if not (math.isfinite(a) and math.isfinite(b)):
                    problems.append(f"stage 1 arm {arm} rep {rp} {q}: non-finite"); continue
                exact += (a.hex() == b.hex()); worst[q] = max(worst[q], abs(a - b))
            dec &= (r["selection_decision"] == m["selection_decision"])
        out[arm] = dict(exact_quantities=f"{exact}/12", decisions_identical=dec, failed_flags_identical=failed_same,
                        max_abs_delta={q: worst[q] for q in NUM})
    return out


def usable(rec, p, bands):
    """The procedure's own predicate (analyze.refit_bootstrap): not failed and every band of predictor p finite."""
    return (not rec["failed"]) and all(math.isfinite(float(rec["stats"][p][b])) for b in bands)


def canonical_layout(root, problems, arm):
    want = {f"rep{r}" for r in REPS}
    for sub, fname in (("records", "rec_000.json"), ("timing", "t_000.json")):
        d = os.path.join(root, sub)
        names = set(os.listdir(d)) if os.path.isdir(d) else set()
        for x in sorted(names - want):
            problems.append(f"stage 2 arm {arm}: unexpected {sub}/{x} (aliases such as rep03 are refused)")
        for x in sorted(names & want):
            got = sorted(os.listdir(os.path.join(d, x)))
            if got != [fname]:
                problems.append(f"stage 2 arm {arm}: {sub}/{x} holds {got}, not exactly [{fname}]")
    tops = {f for f in os.listdir(root)} if os.path.isdir(root) else set()
    allowed = {f"task_{r}.json" for r in REPS} | {f"task_{r}.json.lock" for r in REPS} | {"records", "timing", "status", "logs", "plans", "gate"}
    for x in sorted(tops - allowed):
        problems.append(f"stage 2 arm {arm}: unexpected root entry {x}")


def arm_a_refusal(ec2, problems):
    """RSC a44f5aa: a typed arm-A job-start refusal (native identity differs from the manifest) is arm A's parity outcome;
    its stage-2 workers are then not declared. Returns the refusal line or None."""
    p = os.path.join(ec2, "env", "ARM_A_REFUSED")
    if not os.path.exists(p):
        return None
    held = [x for x in open(p).read().splitlines() if x.startswith("HELD:")]
    if not (held and "computes identity" in held[-1] and "manifest declares" in held[-1]):
        problems.append("ARM_A_REFUSED present but not a typed identity refusal")
        return None
    return held[-1]


def stage2(ec2, lengau_root, problems, refused_a=None):
    man = json.load(open(PROD))
    tasks = {rep: SH.task(man, rep) for rep in REPS}
    preds = list(__import__("analyze").PREDICTORS)
    out = {}
    for arm in ("A", "B"):
        if arm == "A" and refused_a:
            recs = glob.glob(os.path.join(ec2, "root_A", "records", "*", "*"))
            if recs:
                problems.append(f"stage 2 arm A: refused at job-start yet {len(recs)} record file(s) present")
            out["A"] = dict(refused_at_job_start=True, reason=refused_a)
            continue
        mpath = os.path.join(ec2, "env", f"manifest_{arm}.json")
        if not os.path.exists(mpath) or sha(mpath) != PINS[arm]:
            problems.append(f"stage 2 arm {arm}: manifest missing or not the reviewed pin {PINS[arm][:12]}"); continue
        man_x = json.load(open(mpath))
        root = os.path.join(ec2, f"root_{arm}")
        canonical_layout(root, problems, arm)
        clean = exact = failed_both = timed = 0; worst = 0.0; unavailable = 0; walls = []; ratios = []
        use = {p: dict(both=0, ec2_only=0, lengau_only=0, neither=0) for p in preds}
        for rep in REPS:
            t = tasks[rep]; bad = []
            try:
                e = SH.read_record(SH.record_path(root, rep, 0), t, 0)
                l = SH.read_record(SH.record_path(lengau_root, rep, 0), t, 0)
            except ValueError as ex:
                problems.append(f"stage 2 arm {arm} rep {rep}: {ex}"); continue
            if e is None or l is None:
                problems.append(f"stage 2 arm {arm} rep {rep}: {'EC2' if e is None else 'Lengau'} record missing"); continue
            want_b = json.loads(json.dumps(SH.binding_for(man_x, PINS[arm], f"/mnt/bench/root_{arm}", rep, t), default=str))
            try:
                got_b = json.load(open(os.path.join(root, f"task_{rep}.json")))["binding"]
                if got_b != want_b:
                    bad.append(f"binding differs on {[k for k in want_b if got_b.get(k) != want_b[k]] + [k for k in got_b if k not in want_b]}")
            except Exception as ex:
                bad.append(f"binding unreadable ({ex})")
            try:
                te = json.load(open(SH.timing_path(root, rep, 0))); tl = json.load(open(SH.timing_path(lengau_root, rep, 0)))
                why = (V.timing_ok(te, rep=rep, index=0, ident=t["ident"], job=f"ec2{arm}", slot=rep - 3)
                       or V.timing_ok(tl, rep=rep, index=0, ident=t["ident"]))
                if why:
                    bad.append(f"timing {why}")
            except Exception as ex:
                bad.append(f"timing unreadable ({ex})")
            if bad:
                problems.extend(f"stage 2 arm {arm} rep {rep}: {x}" for x in bad); continue
            clean += 1
            exact += (V.payload(e) == V.payload(l))
            failed_both += (e["failed"] and l["failed"])
            for p in preds:
                ue, ul = usable(e, p, t["bands"]), usable(l, p, t["bands"])
                use[p]["both" if ue and ul else "ec2_only" if ue else "lengau_only" if ul else "neither"] += 1
            le, ll = dict(numeric_leaves(e["stats"])), dict(numeric_leaves(l["stats"]))
            if le.keys() != ll.keys():
                problems.append(f"stage 2 arm {arm} rep {rep}: statistic layout differs"); continue
            for k in le:
                x, y = le[k], ll[k]
                if math.isfinite(x) and math.isfinite(y):
                    worst = max(worst, abs(x - y))
                elif V.canon(x) != V.canon(y):
                    unavailable += 1
            we, wl = float(te["wall_s"]), float(tl["wall_s"])
            if not (math.isfinite(we) and math.isfinite(wl) and we > 0 and wl > 0):
                problems.append(f"stage 2 arm {arm} rep {rep}: wall not positive and finite (EC2 {we}, Lengau {wl})"); continue
            walls.append(we); ratios.append(wl / we); timed += 1
        out[arm] = dict(declared=len(REPS), validated_records=clean, valid_timing_pairs=timed, payload_exact=exact, failed_both=failed_both,
                        usable_by_predictor=use, max_abs_delta_finite=worst, nonfinite_disagreements=unavailable,
                        ec2_wall_h=(dict(median=statistics.median(walls) / 3600, min=min(walls) / 3600, max=max(walls) / 3600) if walls else None),
                        lengau_over_ec2=(dict(median=statistics.median(ratios), min=min(ratios), max=max(ratios)) if ratios else None))
        if clean != len(REPS) or timed != len(REPS):
            problems.append(f"stage 2 arm {arm}: {clean} records validated and {timed} timing pairs valid of {len(REPS)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ec2", required=True); ap.add_argument("--lengau-root", required=True)
    ap.add_argument("--row6-ref", required=True); ap.add_argument("--out", required=True); ap.add_argument("--tree", default=None)
    a = ap.parse_args()
    problems = []
    if sha(PROD) != PROD_SHA:
        sys.exit("the production screen manifest here is not 43b75f94")
    env = os.path.join(a.ec2, "env")
    att = {}
    try:
        prof_b = open(os.path.join(env, "profile_B.txt")).read().strip()
    except Exception:
        prof_b = None; problems.append("profile_B.txt missing")
    for arm, allowed in (("A", {"A"}), ("B", {"B_full", "B_nomask"})):
        try:
            d = json.load(open(os.path.join(env, f"attest_{arm}.json")))
            att[arm] = d
            need = ("profile", "XLA_FLAGS", "threads", "numpy_avx512_active", "numpy_dispatch_active", "openblas_core", "problems")
            if not isinstance(d, dict) or any(k not in d for k in need):
                problems.append(f"attestation {arm}: missing fields")
            elif d["profile"] not in allowed or (arm == "B" and d["profile"] != prof_b):
                problems.append(f"attestation {arm}: profile {d['profile']!r} (profile_B.txt {prof_b!r})")
            elif not isinstance(d["problems"], list) or d["problems"]:
                problems.append(f"attestation {arm}: {d['problems']}")
            elif not isinstance(d["openblas_core"], dict) or not d["openblas_core"] or not all(isinstance(v, str) and v for v in d["openblas_core"].values()):
                problems.append(f"attestation {arm}: OpenBLAS core unavailable")
            else:
                base = "--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1"
                th = d["threads"]; xf = d["XLA_FLAGS"]; av = d["numpy_dispatch_active"]
                typed = (isinstance(xf, str) and xf.startswith(base) and isinstance(th, dict)
                         and sorted(th) == ["MKL_NUM_THREADS", "NPROC", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS"]
                         and all(v == "1" for v in th.values()) and isinstance(av, list) and all(isinstance(x, str) for x in av))
                if arm == "A":
                    typed = typed and xf == base and d.get("OPENBLAS_CORETYPE") is None
                else:
                    typed = (typed and "--xla_cpu_max_isa=AVX2" in xf.split() and d.get("OPENBLAS_CORETYPE") == "Haswell"
                             and all("haswell" in v.lower() for v in d["openblas_core"].values())
                             and (d["profile"] != "B_full" or all(x in ("X86_V2", "X86_V3") for x in av)))
                if not typed:
                    problems.append(f"attestation {arm}: effective values do not match profile {d['profile']}")
        except Exception as ex:
            problems.append(f"attestation {arm} missing ({ex})")
    for f in ("FAILED", "OUTCOMES_FAILED"):
        if os.path.exists(os.path.join(env, f)):
            problems.append(f"instance reported {f}: " + open(os.path.join(env, f)).read().strip())
    try:
        uv = json.load(open(os.path.join(env, "upload_verify.json")))
        if uv.get("transfer_verified") is not True:
            problems.append(f"transfer not verified: {uv}")
    except Exception as ex:
        problems.append(f"upload_verify.json missing ({ex})")
    if not os.path.exists(os.path.join(env, "plan.json")) or sha(os.path.join(env, "plan.json")) != PLAN_PIN:
        problems.append("plan.json missing or not the reviewed pin")
    refused_a = arm_a_refusal(a.ec2, problems)
    try:
        ocd = json.load(open(os.path.join(env, "outcomes.json")))
        oc = ocd["outcomes"]
        un = ocd.get("unresolved_after_kill")
        if not (isinstance(un, list) and un == []):
            problems.append(f"cleanup left unresolved process groups or no typed record of them: {un!r}")
        want = [n for n in NAMES if not (refused_a and n.startswith("w_A_"))]
        try:
            decl = open(os.path.join(env, "declared.txt")).read().split()
        except Exception:
            decl = None
        if sorted(oc) != sorted(want) or (decl is not None and sorted(decl) != sorted(want)):
            problems.append(f"outcomes name set differs from the {len(want)} declared processes")
        bad = {k: v for k, v in oc.items() if not (isinstance(v, int) and not isinstance(v, bool) and v == 0)}
        if bad:
            problems.append(f"{len(bad)} process(es) not exit 0: {bad}")
    except Exception as ex:
        problems.append(f"outcomes.json missing or unreadable ({ex})")
    running = []
    try:
        prev = -1.0
        for line in open(os.path.join(env, "occupancy.txt")):
            f = line.split()
            if len(f) != 5:
                raise ValueError(f"malformed line {line!r}")
            ts, n = float(f[0]), int(f[1]); loads = [float(x) for x in f[2:]]
            if not all(math.isfinite(x) and x >= 0 for x in [ts] + loads):
                raise ValueError(f"non-finite or negative value at {line!r}")
            if ts <= prev or not 0 <= n <= 78:
                raise ValueError(f"non-monotonic time or count out of range at {line!r}")
            prev = ts; running.append(n)
        if not running:
            raise ValueError("empty")
    except Exception as ex:
        problems.append(f"occupancy timeline invalid ({ex})")
    report = dict(profile_B=(att.get("B") or {}).get("profile"), stage1=stage1(a.ec2, a.row6_ref, problems),
                  stage2=stage2(a.ec2, a.lengau_root, problems, refused_a),
                  arm_A_refused=refused_a, occupancy=(dict(samples=len(running), max=max(running), mean=sum(running) / len(running), min=min(running)) if running else None),
                  problems=problems, valid=not problems)
    json.dump(report, open(a.out, "w"), indent=1)
    print(json.dumps({k: report[k] for k in ("profile_B", "arm_A_refused", "stage1", "stage2", "occupancy", "valid")}, indent=1))
    for p in problems:
        print("INVALID:", p)
    return 0 if not problems else 3


if __name__ == "__main__":
    sys.exit(main())
