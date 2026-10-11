"""Tests of chpc/row19_ec2_ingest.py (repaired for Codex RSC 0483db4 V10-2/4/5/8). Two modes, the same cases:

    .venv/bin/python test_row19_ec2_ingest.py                          # STUB: synthetic records, the frozen-task check stubbed
    t1py test_row19_ec2_ingest.py <lengau screen root> <scratch dir>   # REAL records (Lengau login node; sandbox only)

Each case builds a sandbox screen root (a copy of reps 3..6, indices 0 and 1), declares a partition k=199 (block = indices
1..199), pins it in a sandbox controls file, ACTIVATES it (row19_partition.activate), derives the operational manifest,
moves index 1 into a synthetic EC2 bundle (work) and copies index 0 (sentinels), with complete worker statuses, typed
outcomes, an effective B_full attestation, the plan bound to partition/opmanifest/activation, and a sealed authority
inventory naming the attempt as owner. Nothing touches a production root."""
import os, sys, json, glob, shutil, hashlib, copy, tempfile, time, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
STUB = len(sys.argv) < 3
REPS = [3, 4, 5, 6]; ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""), flush=True)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

if STUB:                                                       # stub the scientific checks; everything else is the real module
    def _rsha(d): return hashlib.sha256(json.dumps({k: v for k, v in d.items() if k != "sha"}, sort_keys=True).encode()).hexdigest()
    SHs = types.ModuleType("row19_shard")
    SHs.task = lambda man, r: dict(ident=f"ident{int(r)}", seed=int(r), n_rep=200, bands=["ws"], code_hash="c")
    SHs.record_path = lambda root, r, i: os.path.join(root, "records", f"rep{int(r)}", f"rec_{int(i):03d}.json")
    SHs.timing_path = lambda root, r, i: os.path.join(root, "timing", f"rep{int(r)}", f"t_{int(i):03d}.json")
    def _read(path, t, i):
        if not os.path.exists(path):
            return None
        d = json.load(open(path))
        if d.get("ident") != t["ident"] or d.get("sha") != _rsha(d):
            raise ValueError(f"{path}: a record this task cannot accept (identity, index, draw, payload or checksum)")
        if d["rep"] != int(i):
            raise ValueError(f"{path}: holds the record of index {d['rep']}, not of index {int(i)}")
        return d
    SHs.read_record = _read
    SHs.binding_for = lambda man, msha, root, r, t: dict(manifest_sha=msha, rep=int(r), ident=t["ident"], ckpt=os.path.join(root, "records", f"rep{int(r)}"))
    Vs = types.ModuleType("row19_screen_verify")
    Vs.payload = lambda rec: json.dumps(dict(stats=rec.get("stats"), failed=rec.get("failed"), failed_reason=rec.get("failed_reason")), sort_keys=True)
    def _timing_ok(d, **want):
        for k, v in want.items():
            if d.get(k) != v:
                return f"{k} {d.get(k)!r} is not {v!r}"
        return ""
    Vs.timing_ok = _timing_ok
    sys.modules["row19_shard"] = SHs; sys.modules["row19_screen_verify"] = Vs
    reseal = lambda d: dict({k: v for k, v in d.items() if k != "sha"}, sha=_rsha(d))
    scratch = tempfile.mkdtemp(); src_root = None
else:
    import analyze as A
    reseal = lambda d: dict({k: v for k, v in d.items() if k != "sha"}, sha=A._record_sha({k: v for k, v in d.items() if k != "sha"}))
    src_root, scratch = sys.argv[1], sys.argv[2]

import row19_shard as SH, row19_partition as RP, row19_ec2_state as ES
import row19_ec2_ingest as IG
IG.ACTIVATION_MODE = "sandbox"                                   # every proof here is a sandbox proof (Codex 3dc0daf R1-1)
prod = json.load(open(os.path.join(HERE, "chpc", "row19_screen_manifest.json")))
AID, KEY, SEQ = "ec2-prod-e1-a1", "prod-e1/1", 7
STATUS0 = dict(exit=0, reason="", left=[], resumed=[], wall_s=70000.0, cpu_s=69000.0, started=1.0, ended=70001.0, maxrss=2_400_000_000, host="ip-10-0-0-1")


def fake_record(r, i):
    return reseal(dict(rep=i, ident=f"ident{r}", stats={"ws": {"point": 0.1 * r + i}}, failed=(r == 6), failed_reason="no-converge" if r == 6 else ""))


def perturb(d, v):
    """A contrary record that still passes the frozen task: STUB sets the synthetic point; REAL adds v to the first finite
    numeric leaf of the real statistics (same layout, resealed). No value is printed."""
    if STUB:
        return reseal(dict(d, stats={"ws": {"point": v}}))
    st = copy.deepcopy(d["stats"])
    def bump(x):
        if isinstance(x, dict):
            for k in sorted(x):
                if isinstance(x[k], (dict, list)):
                    if bump(x[k]):
                        return True
                elif isinstance(x[k], float) and x[k] == x[k] and abs(x[k]) != float("inf"):
                    x[k] = x[k] + v; return True
        elif isinstance(x, list):
            for i, y in enumerate(x):
                if isinstance(y, (dict, list)):
                    if bump(y):
                        return True
                elif isinstance(y, float) and y == y and abs(y) != float("inf"):
                    x[i] = y + v; return True
        return False
    assert bump(st), "no finite statistic to perturb"
    return reseal(dict(d, stats=st))


def build(case, contract="production", cls="production"):
    d = os.path.join(scratch, case); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    root = os.path.join(d, "root"); os.makedirs(os.path.join(root, "plans"))
    for r in REPS:
        for i in (0, 1):
            for sub, f in (("records", f"rec_{i:03d}.json"), ("timing", f"t_{i:03d}.json")):
                os.makedirs(os.path.join(root, sub, f"rep{r}"), exist_ok=True)
                dst = os.path.join(root, sub, f"rep{r}", f)
                if STUB:
                    obj = fake_record(r, i) if sub == "records" else dict(rep=r, index=i, ident=f"ident{r}", fit_seconds=60000.0, wall_s=70000.0,
                                                                          failed=False, maxrss=2_400_000_000, t=1.0, job="7523818.sched01", slot=0, host="cnode")
                    json.dump(obj, open(dst, "w"))
                else:
                    shutil.copy2(os.path.join(src_root, sub, f"rep{r}", f), dst)
    man = copy.deepcopy(prod); man["storage"] = {"root": root, "campaign": os.path.join(d, "camp")}
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w")); msha = sha(mp)
    part = RP.declare(man, msha, 199, 1); pp = os.path.join(d, "partition.json"); json.dump(part, open(pp, "w")); psha = sha(pp)
    cp = os.path.join(d, "controls.json"); json.dump({"versions": [{"version": 10, "partition": {"path": "x", "sha256": psha}}]}, open(cp, "w"))
    IG.CONTROLS = cp
    proof, probs = RP.activate(man, mp, pp, cp, mode="sandbox")
    ap_ = RP.activation_path(man, 1); os.makedirs(os.path.dirname(ap_), exist_ok=True); json.dump(proof, open(ap_, "w"))
    opm = ES.derive_operational(man, msha, 1, 75300, contract); opp = os.path.join(d, "op.json"); json.dump(opm, open(opp, "w")); opsha = sha(opp)
    b = os.path.join(d, "bundle"); broot = os.path.join(b, "root"); env = os.path.join(b, "env"); os.makedirs(env)
    slots = []
    for k, r in enumerate(REPS):
        for sub, f in (("records", "rec_001.json"), ("timing", "t_001.json")):
            os.makedirs(os.path.join(broot, sub, f"rep{r}"), exist_ok=True)
            shutil.move(os.path.join(root, sub, f"rep{r}", f), os.path.join(broot, sub, f"rep{r}", f))
        slots.append(dict(slot=k, rep=r, indices=[1], role="work"))
    for k, r in enumerate(REPS):
        for sub, f in (("records", "rec_000.json"), ("timing", "t_000.json")):
            shutil.copy2(os.path.join(root, sub, f"rep{r}", f), os.path.join(broot, sub, f"rep{r}", f))
        slots.append(dict(slot=len(REPS) + k, rep=r, indices=[0], role="sentinel"))
    os.makedirs(os.path.join(broot, "status"))
    for s in slots:
        r, i = s["rep"], s["indices"][0]
        tp = SH.timing_path(broot, r, i); t = json.load(open(tp)); t.update(job=AID, slot=s["slot"]); json.dump(t, open(tp, "w"))
        ident = SH.task(prod, r)["ident"] if not STUB else f"ident{r}"
        json.dump(dict(STATUS0, job=AID, slot=s["slot"], rep=r, ident=ident, indices=[i], new=[i]),
                  open(os.path.join(broot, "status", f"job{AID}.slot{s['slot']}.json"), "w"))
    for r in REPS:
        json.dump(dict(binding=SH.binding_for(opm, opsha, "/mnt/prod/root", r, SH.task(prod, r))), open(os.path.join(broot, f"task_{r}.json"), "w"), default=str)
    plan = dict(job=1, attempt_id=AID, sequence=SEQ, epoch=1, contract=contract, partition_sha256=psha, opmanifest_sha256=opsha,
                activation_sha256=sha(ap_), slots=slots)
    json.dump(plan, open(os.path.join(env, "plan.json"), "w"))
    json.dump(dict(transfer_verified=True), open(os.path.join(env, "upload_verify.json"), "w"))
    json.dump(dict(profile="B_full", problems=[], XLA_FLAGS=ES.XLA_BASE + " --xla_cpu_max_isa=AVX2", OPENBLAS_CORETYPE="Haswell",
                   threads={k: "1" for k in ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
                   numpy_dispatch_active=["X86_V2", "X86_V3"], openblas_core={"libscipy_openblas.so": "Haswell"}), open(os.path.join(env, "attest_B.json"), "w"))
    json.dump(dict(declared=len(slots), outcomes={f"w_slot{s['slot']}": 0 for s in slots}, unresolved_after_kill=[]), open(os.path.join(env, "outcomes.json"), "w"))
    open(os.path.join(env, "userdata.log"), "w").write("mutable\n")
    att = dict(key=KEY, run="prod-e1", attempt=1, attempt_id=AID, sequence=SEQ, state="reconciled", ingestion="pending", contract=contract,
               plan_sha256=sha(os.path.join(env, "plan.json")), coordinates=[[r, 1] for r in REPS], sentinels=[[r, 0] for r in REPS],
               duplicates=[], charged_usd=1.0, **{"class": cls})
    inv = inventory({KEY: att})
    ip = os.path.join(d, "inventory.json"); json.dump(inv, open(ip, "w"))
    ES.install_inventory(root, inv)                              # the root's installed current view (R1-2)
    return dict(d=d, root=root, mp=mp, pp=pp, opp=opp, ip=ip, b=b, att=att, gen=3)


def inventory(atts, gen=3, at=None, owners=None, release=None):
    own = owners if owners is not None else {f"{c[0]}/{c[1]}": [k, a["sequence"]] for k, a in atts.items() if ES.owns(a) for c in a["coordinates"]}
    fence = {f"{c[0]}/{c[1]}": a["sequence"] for a in atts.values() for c in a["coordinates"]}
    return ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=gen, at=time.time() if at is None else at, attempts=atts,
                        owners=dict(sorted(own.items())), fence=fence, release=release or dict(production_released=False, released_attempts=[]), usd={}))


def sums(b):
    lines = []
    for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True)):
        rel = os.path.relpath(p, b)
        if os.path.isfile(p) and rel.split(os.sep)[0] in ("root", "env") and rel not in ("env/upload_verify.json", "env/userdata.log"):
            lines.append(f"{sha(p)}  {rel}\n")
    open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))


def ingest(c, key=KEY):
    return IG.main(["--manifest", c["mp"], "--partition", c["pp"], "--opmanifest", c["opp"], "--authority", c["ip"], "--attempt-key", key, "--bundle", c["b"]])


def reg(c):
    p = os.path.join(c["root"], "ec2", "register.json")
    return json.load(open(p)) if os.path.exists(p) else None


def held(c):
    return os.path.exists(os.path.join(c["root"], "ec2", "HOLD"))


def resave_inv(c, install=True, atts=None, **kw):
    c["gen"] += 1
    inv = inventory(atts or {KEY: c["att"]}, gen=c["gen"], **kw); json.dump(inv, open(c["ip"], "w"))
    if install:
        ES.install_inventory(c["root"], inv)
    return inv


def edit_bundle(c, rel, fn):
    p = os.path.join(c["b"], rel); d = json.load(open(p)); d = fn(d) or d; json.dump(d, open(p, "w"))


# 1 success, replay re-validated, installed inventory, fence
c = build("ok"); sums(c["b"]); rc = ingest(c); R = reg(c); e = (R or {"attempts": {}})["attempts"].get(AID, {})
pub = all(os.path.exists(SH.record_path(c["root"], r, 1)) and sha(SH.record_path(c["root"], r, 1)) == e["coordinates"][f"{r}/1"]["record_sha256"] for r in REPS) if e else False
check("success: 4 work pairs + statuses published, 'ingested', 4 sentinels equal", rc == 0 and e.get("state") == "ingested" and pub and len(e["compared_equal"]) == 4)
fk = [k for k, v in (e.get("coordinates") or {}).items() if v.get("failed")] if e else []
if STUB or fk:
    k6 = "6/1" if STUB else fk[0]; r6 = int(k6.split("/")[0])
    check("failed fits are published and reported as failed, never dropped", e and e["coordinates"][k6]["failed"] is True and os.path.exists(SH.record_path(c["root"], r6, 1)))
else:
    print("SKIP failed-fit publication: no failed fit among the real index-1 records copied (covered in STUB mode)", flush=True)
check("fence raised to the attempt's sequence", R and all(R["fence"][f"{r}/1"] == SEQ for r in REPS))
check("the installed inventory stays the root's view (ingestion never writes it)", json.load(open(os.path.join(c["root"], "ec2", "authority", "inventory.json")))["sha256"] == json.load(open(c["ip"]))["sha256"])
check("canonical task bindings untouched (none written)", not glob.glob(os.path.join(c["root"], "task_*.json")))
check("replay of an ingested attempt is re-validated and passes", ingest(c) == 0 and not held(c))
tp = SH.timing_path(c["root"], 3, 1); t = json.load(open(tp)); t["wall_s"] += 1; json.dump(t, open(tp, "w"))
check("replay after a canonical timing changed HOLDS and writes ec2/HOLD", ingest(c) == 3 and held(c))
st = os.path.join(c["root"], "ec2", "status", f"{AID}.slot0.json"); os.remove(os.path.join(c["root"], "ec2", "HOLD")); json.dump(t, open(tp, "w"))
c2 = build("okstatus"); sums(c2["b"]); ingest(c2); os.remove(os.path.join(c2["root"], "ec2", "status", f"{AID}.slot1.json"))
check("replay with a copied status missing HOLDS", ingest(c2) == 3 and held(c2))

# 2 crash after the first pair, then replay; staged bytes swapped before the replay
c = build("crash"); sums(c["b"])
real = IG.publish_copy; calls = {"n": 0}
def flaky(src, dst, want):
    calls["n"] += 1
    if calls["n"] == 4:
        raise ValueError("simulated crash")
    return real(src, dst, want)
IG.publish_copy = flaky; rc1 = ingest(c); IG.publish_copy = real
st1 = reg(c)["attempts"][AID]["state"]; rc2 = ingest(c); st2 = reg(c)["attempts"][AID]["state"]
check("crash leaves 'ingesting'; replay completes to 'ingested'", rc1 == 3 and st1 == "ingesting" and rc2 == 0 and st2 == "ingested")
c = build("crashswap"); sums(c["b"]); calls["n"] = 0; IG.publish_copy = flaky; ingest(c); IG.publish_copy = real
edit_bundle(c, "root/records/rep5/rec_001.json", lambda d: perturb(d, 9.9)); sums(c["b"])
check("a staged unit changed after journaling HOLDS the replay", ingest(c) == 3 and reg(c)["attempts"][AID]["state"] == "ingesting")

# 3 comparisons
c = build("sentinel"); edit_bundle(c, "root/records/rep3/rec_000.json", lambda d: perturb(d, 7.0)); sums(c["b"])
check("sentinel mismatch HOLDS, writes ec2/HOLD, nothing published", ingest(c) == 3 and held(c) and reg(c) is None)
c = build("dup"); shutil.copy2(os.path.join(c["b"], "root/records/rep4/rec_001.json"), SH.record_path(c["root"], 4, 1))
edit_bundle(c, "root/records/rep4/rec_001.json", lambda d: perturb(d, 5.5)); sums(c["b"])
check("contrary duplicate HOLDS", ingest(c) == 3 and held(c))
c = build("same"); shutil.copy2(os.path.join(c["b"], "root/records/rep4/rec_001.json"), SH.record_path(c["root"], 4, 1)); sums(c["b"])
check("identical duplicate counts once (preexisting, no replacement)", ingest(c) == 0 and reg(c)["attempts"][AID]["coordinates"]["4/1"]["preexisting"])

# 4 bundle completeness
c = build("unlisted"); sums(c["b"]); open(os.path.join(c["b"], "root", "stray.json"), "w").write("{}")
check("unlisted bundle file HOLDS", ingest(c) == 3)
c = build("mutable"); sums(c["b"]); open(os.path.join(c["b"], "env", "userdata.log"), "a").write("appended after hashing\n")
check("V10-3: userdata.log appended after hashing does not fail a healthy bundle", ingest(c) == 0)
for name, fn in (("a bool outcome", lambda d: d["outcomes"].update(w_slot0=False)), ("a string outcome", lambda d: d["outcomes"].update(w_slot1="0")),
                 ("a missing worker outcome", lambda d: d["outcomes"].pop("w_slot2")), ("an extra worker outcome", lambda d: d["outcomes"].update(w_slot99=0))):
    c = build("oc"); edit_bundle(c, "env/outcomes.json", fn); sums(c["b"])
    check(f"outcomes with {name} HOLD", ingest(c) == 3)
for name, fn in (("left index", lambda d: d.update(left=[1], new=[])), ("resume exit", lambda d: d.update(exit=75)),
                 ("another job", lambda d: d.update(job="7523818.sched01")), ("memory above the stop", lambda d: d.update(maxrss=5 * 2 ** 30)),
                 ("non-finite wall", lambda d: d.update(wall_s=float("nan")))):
    c = build("st"); edit_bundle(c, f"root/status/job{AID}.slot0.json", fn); sums(c["b"])
    check(f"incomplete status ({name}) HOLDS", ingest(c) == 3)
c = build("nostatus"); os.remove(os.path.join(c["b"], "root", "status", f"job{AID}.slot1.json")); sums(c["b"])
check("missing worker status HOLDS", ingest(c) == 3)
c = build("attest"); edit_bundle(c, "env/attest_B.json", lambda d: d.update(profile="B_nomask")); sums(c["b"])
check("a B_nomask attestation HOLDS", ingest(c) == 3)
c = build("attest2"); edit_bundle(c, "env/attest_B.json", lambda d: d.update(numpy_dispatch_active=["X86_V3", "X86_V4"])); sums(c["b"])
check("an attestation with numpy dispatch above X86_V3 HOLDS", ingest(c) == 3)

# 5 plan contract
def plan_edit(case, fn):
    c = build(case); edit_bundle(c, "env/plan.json", fn); c["att"]["plan_sha256"] = sha(os.path.join(c["b"], "env", "plan.json")); resave_inv(c); sums(c["b"])
    return c
check("plan naming a coordinate twice HOLDS", ingest(plan_edit("p1", lambda d: d["slots"][1].update(rep=3))) == 3)
check("plan with three sentinels HOLDS", ingest(plan_edit("p2", lambda d: d["slots"][7].update(role="work"))) == 3)
check("plan bound to another partition HOLDS", ingest(plan_edit("p3", lambda d: d.update(partition_sha256="0" * 64))) == 3)
check("plan slot numbers not 0..n-1 HOLD", ingest(plan_edit("p4", lambda d: d["slots"][0].update(slot=40))) == 3)
c = build("planbytes"); edit_bundle(c, "env/plan.json", lambda d: d.update(job=2)); sums(c["b"])
check("a plan that is not the attempt's bytes HOLDS", ingest(c) == 3)

# 6 authority: ownership, fence, staleness, generation, release
c = build("owner"); sums(c["b"]); a2 = dict(c["att"], key="prod-e1/2", attempt=2, attempt_id="ec2-prod-e1-a2", sequence=SEQ + 1)
resave_inv(c, atts={KEY: dict(c["att"], ingestion="dispositioned"), "prod-e1/2": a2})
check("a dispositioned attempt whose coordinates were reassigned is refused (late writer)", ingest(c) == 3 and reg(c) is None)
# R1-2: a fresh, sealed but SUPERSEDED inventory never licenses a late writer; the disposition is fenced on the root
c = build("superseded"); sums(c["b"]); old = json.load(open(c["ip"]))
inv4 = resave_inv(c, atts={KEY: dict(c["att"], disposition_requested=True)})
ack = json.load(open(ES.ack_path(c["root"], c["gen"])))
check("R1-2 a disposition request is fenced on the root at installation and acknowledged", KEY in ack["dispositioned"]
      and reg(c)["attempts"][AID]["state"] == "dispositioned")
json.dump(old, open(c["ip"], "w"))
check("R1-2 the older fresh sealed inventory (still naming the owner) refuses: not the installed current view", ingest(c) == 3 and reg(c)["attempts"][AID]["state"] == "dispositioned")
json.dump(inv4, open(c["ip"], "w"))
check("R1-2 the current inventory refuses the attempt under a disposition request", ingest(c) == 3)
a_, why = ES.install_inventory(c["root"], old)
check("R1-2 an out-of-order (older) delivery is refused by the installer", a_ is None and "older" in why[0])
a_, why = ES.install_inventory(c["root"], inv4)
check("R1-2 re-installing the same generation and bytes is idempotent (same acknowledgement)", a_ is not None and KEY in a_["dispositioned"])
c = build("raceing"); sums(c["b"]); calls = {"n": 0}; real = IG.publish_copy
def flaky2(src, dst, want):
    calls["n"] += 1
    if calls["n"] == 2:
        raise ValueError("crash")
    return real(src, dst, want)
IG.publish_copy = flaky2; ingest(c); IG.publish_copy = real
resave_inv(c, atts={KEY: dict(c["att"], disposition_requested=True)})
ack = json.load(open(ES.ack_path(c["root"], c["gen"])))
check("R1-2 a disposition of an attempt already 'ingesting' is refused in the acknowledgement (no release on the Mac)", KEY in ack["refused"] and KEY not in ack["dispositioned"])
c = build("noinv"); sums(c["b"]); os.remove(ES.paths(c["root"])["inventory"])
check("R1-2 no installed inventory refuses ingestion", ingest(c) == 3)
c = build("fence"); sums(c["b"]); os.makedirs(os.path.join(c["root"], "ec2"), exist_ok=True)
json.dump(dict(schema=ES.REGISTER_SCHEMA, authority_generation=0, fence={"3/1": SEQ + 5}, attempts={}), open(os.path.join(c["root"], "ec2", "register.json"), "w"))
check("a register fence above the attempt's sequence refuses", ingest(c) == 3)
c = build("stale"); sums(c["b"]); resave_inv(c, at=time.time() - 7 * 3600)
check("an inventory older than 6 h refuses", ingest(c) == 3)
c = build("future"); sums(c["b"]); resave_inv(c, at=time.time() + 3600)
check("an inventory from the future refuses", ingest(c) == 3)
c = build("seal"); sums(c["b"]); inv = json.load(open(c["ip"])); inv["generation"] = 99; json.dump(inv, open(c["ip"], "w"))
check("an inventory whose seal does not match refuses", ingest(c) == 3)
c = build("gen"); sums(c["b"]); os.makedirs(os.path.join(c["root"], "ec2"), exist_ok=True)
json.dump(dict(schema=ES.REGISTER_SCHEMA, authority_generation=9, fence={}, attempts={}), open(os.path.join(c["root"], "ec2", "register.json"), "w"))
check("an inventory generation older than one already consumed refuses", ingest(c) == 3)
c = build("unrec"); sums(c["b"]); c["att"]["state"] = "launched"; resave_inv(c)
check("an attempt not reconciled refuses", ingest(c) == 3)
c = build("qual", contract="Q1" if False else "production", cls="qualification"); sums(c["b"])
check("a qualification attempt not released refuses", ingest(c) == 3)
resave_inv(c, release=dict(production_released=True, released_attempts=[KEY]))
check("the same attempt once listed as released ingests", ingest(c) == 0)

# 7 inputs and STOP/HOLD
c = build("ctl"); sums(c["b"]); json.dump({"versions": [{"version": 10, "partition": None}]}, open(IG.CONTROLS, "w"))
check("a partition the latest controls do not pin refuses", ingest(c) == 3)
c = build("act"); sums(c["b"]); os.remove(RP.activation_path(json.load(open(c["mp"])), 1))
check("a partition with no activation proof refuses", ingest(c) == 3)
c = build("opm"); sums(c["b"]); o = json.load(open(c["opp"])); o["cfg"]["n_boot_refit"] = 100; json.dump(o, open(c["opp"], "w"))
check("an operational manifest that changes science refuses", ingest(c) == 3)
c = build("stop"); sums(c["b"]); open(os.path.join(c["root"], "STOP"), "w").write("x")
check("the root STOP refuses canonical publication", ingest(c) == 3 and reg(c) is None)
c = build("hold"); sums(c["b"]); os.makedirs(os.path.join(c["root"], "ec2"), exist_ok=True); open(os.path.join(c["root"], "ec2", "HOLD"), "w").write("{}")
check("an ec2/HOLD refuses canonical publication", ingest(c) == 3 and reg(c) is None)

# 8 publish_copy verifies staged bytes before writing
c = build("pc"); dst = os.path.join(c["d"], "x", "dst.json")
try:
    IG.publish_copy(os.path.join(c["b"], "env", "plan.json"), dst, "0" * 64); check("publish_copy refuses staged bytes that are not the registered hash", False)
except ValueError:
    check("publish_copy refuses staged bytes that are not the registered hash", not os.path.exists(dst))

# 9 activation refuses while the controls do not pin the partition; refuses a reserved block coordinate
c = build("act2"); man = json.load(open(c["mp"]))
json.dump({"versions": [{"version": 10, "partition": None}]}, open(IG.CONTROLS, "w"))
_, probs = RP.activate(man, c["mp"], c["pp"], IG.CONTROLS, mode="sandbox")
check("activation refuses while the controls do not pin the partition (guard not live)", any("does not pin" in p for p in probs))
json.dump({"slots": [{"slot": 0, "rep": 3, "indices": [150]}]}, open(os.path.join(c["root"], "plans", "job_9.json"), "w"))
json.dump({"versions": [{"version": 10, "partition": {"sha256": sha(c["pp"])}}]}, open(IG.CONTROLS, "w"))
_, probs = RP.activate(man, c["mp"], c["pp"], IG.CONTROLS, mode="sandbox")
check("activation refuses a block coordinate planned by Lengau", any("planned or reserved" in p for p in probs))
# R1-1: a sandbox proof is never accepted by a canonical consumer; a later controls version that drops the pin invalidates it
c = build("mode"); sums(c["b"]); IG.ACTIVATION_MODE = "canonical"
check("R1-1 a canonical ingestion refuses a sandbox activation proof", ingest(c) == 3)
IG.ACTIVATION_MODE = "sandbox"
c = build("lineage"); sums(c["b"]); ctl = json.load(open(IG.CONTROLS))
ctl["versions"].append({"version": 11, "partition": {"path": "x", "sha256": "f" * 64}}); json.dump(ctl, open(IG.CONTROLS, "w"))
check("R1-1 a proof made under version 10 is historical once version 11 pins another partition", ingest(c) == 3)
ctl["versions"][-1]["partition"] = ctl["versions"][0]["partition"]; json.dump(ctl, open(IG.CONTROLS, "w"))
check("... and valid while every later version keeps pinning it", ingest(c) == 0)
ctl["versions"][0]["reviewed"] = "edited"; json.dump(ctl, open(IG.CONTROLS, "w"))
c = build("lineage2"); sums(c["b"]); ctl = json.load(open(IG.CONTROLS)); ctl["versions"][0]["reviewed"] = "edited later"; json.dump(ctl, open(IG.CONTROLS, "w"))
check("R1-1 a proof whose controls version entry changed afterwards refuses", ingest(c) == 3)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
