"""EC2 provider epoch 2 CANDIDATE (NOT adopted): ingestion REVISION 5 (chpc/candidate_e2/row19_ec2_ingest.py) under a
schema-2 partition, in a sandbox root with synthetic records (the frozen-task check stubbed exactly as the existing
test_row19_ec2_ingest.py STUB mode does). No fits, no Lengau, no AWS.

  1. a complete epoch-2 production bundle ingests; the work coordinates must be OWNED by epoch 2 (a Lengau coordinate as work
     HOLDS);
  2. per-slot outcomes: a worker that died (exit 139) without output is UNPRODUCED - the others are published, the register
     lists it with its exit, the fence is raised there too, and the Mac ack then releases it; nothing is invented as a
     failed-fit record;
  3. an unproduced slot that left any record/timing/status HOLDS (ambiguous); too many unproduced work slots or too few
     sentinels HOLD; an unknown outcome string HOLDS;
  4. a qualification attempt and every schema-1 epoch keep the all-or-nothing contract.

    python3 chpc/candidate_e2/test_e2_ingest.py               (from workspace_demo/t1_access)"""
import copy, glob, hashlib, importlib.util, json, os, shutil, sys, tempfile, time, types

CAND = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(CAND); T1 = os.path.dirname(CHPC)
for p in (T1, CHPC, CAND):
    sys.path.insert(0, p)
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# --- the STUB scientific checks of test_row19_ec2_ingest.py (records synthetic, everything else the real modules) ---
def _rsha(d):
    return hashlib.sha256(json.dumps({k: v for k, v in d.items() if k != "sha"}, sort_keys=True).encode()).hexdigest()


SHs = types.ModuleType("row19_shard")
SHs.task = lambda man, r: dict(ident=f"ident{int(r)}", seed=int(r), n_rep=200, bands=["ws"], code_hash="c")
SHs.record_path = lambda root, r, i: os.path.join(root, "records", f"rep{int(r)}", f"rec_{int(i):03d}.json")
SHs.timing_path = lambda root, r, i: os.path.join(root, "timing", f"rep{int(r)}", f"t_{int(i):03d}.json")


def _read(path, t, i):
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    if d.get("ident") != t["ident"] or d.get("sha") != _rsha(d) or d["rep"] != int(i):
        raise ValueError(f"{path}: a record this task cannot accept")
    return d


SHs.read_record = _read
SHs.binding_for = lambda man, msha, root, r, t: dict(manifest_sha=msha, rep=int(r), ident=t["ident"], ckpt=os.path.join(root, "records", f"rep{int(r)}"))
Vs = types.ModuleType("row19_screen_verify")
Vs.payload = lambda rec: json.dumps(dict(stats=rec.get("stats"), failed=rec.get("failed"), failed_reason=rec.get("failed_reason")), sort_keys=True)
Vs.timing_ok = lambda d, **want: next((f"{k} {d.get(k)!r} is not {v!r}" for k, v in want.items() if d.get(k) != v), "")
sys.modules["row19_shard"] = SHs; sys.modules["row19_screen_verify"] = Vs


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


RP = load_mod("row19_partition", os.path.join(CAND, "row19_partition.py"))
IG = load_mod("row19_ec2_ingest", os.path.join(CAND, "row19_ec2_ingest.py"))
import row19_ec2_state as ES
SH = SHs
IG.ACTIVATION_MODE = "sandbox"
PROD = json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))
DESIG = json.load(open(os.path.join(CHPC, "candidate_v16", "row19_screen_designated.json")))
W = [24, 25, 28, 29]                                           # EC2-designated replicates; index 0 Lengau's, index 1 EC2 work
AID, KEY, SEQ = "ec2-prod-e2-a1", "prod-e2/1", 9
STATUS0 = dict(exit=0, reason="", left=[], resumed=[], wall_s=70000.0, cpu_s=69000.0, started=1.0, ended=70001.0, maxrss=2_400_000_000, host="ip-10-0-0-1")
scratch = tempfile.mkdtemp()


def rec(r, i):
    return dict(d := dict(rep=i, ident=f"ident{r}", stats={"ws": {"point": 0.1 * r + i}}, failed=False, failed_reason=""), sha=_rsha(d))


def timing(r, i, job="7523818.sched01", slot=0):
    return dict(rep=r, index=i, ident=f"ident{r}", fit_seconds=60000.0, wall_s=70000.0, failed=False, maxrss=2_400_000_000, t=1.0, job=job, slot=slot, host="h")


def inventory(atts, gen):
    own = {f"{c[0]}/{c[1]}": [k, a["sequence"]] for k, a in atts.items() if ES.owns(a) for c in a["coordinates"]}
    fence = {f"{c[0]}/{c[1]}": a["sequence"] for a in atts.values() for c in a["coordinates"]}
    return ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=gen, at=time.time(), attempts=atts, owners=dict(sorted(own.items())), fence=fence,
                        release=dict(production_released=False, released_attempts=[]), usd={}))


def put(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, "w"))


def build(case, unprod=None, leave=False, work=None, cls="production", outcome_override=None, status_for=None):
    """A sandbox screen root under an ACTIVATED schema-2 epoch 2 (predecessor e1 activated there too) and one EC2 bundle."""
    unprod = unprod or {}
    d = os.path.join(scratch, case); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    root = os.path.join(d, "root"); camp = os.path.join(d, "camp"); os.makedirs(os.path.join(root, "plans")); os.makedirs(camp)
    for r in W:
        put(SH.record_path(root, r, 0), rec(r, 0)); put(SH.timing_path(root, r, 0), timing(r, 0))
    put(os.path.join(root, "plans", "job_1.json"), {"job": 1, "slots": [{"slot": k, "rep": r, "indices": [0]} for k, r in enumerate(W)]})
    put(os.path.join(camp, "budget.json"), {"entries": {"t": {"kind": "shard", "rep": 1, "state": "settled", "job_id": "1.s"}}})
    man = copy.deepcopy(PROD); man["storage"] = {"root": root, "campaign": camp}
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w")); msha = sha(mp)
    dp = os.path.join(d, "designated.json"); json.dump(dict(DESIG, manifest_sha256=msha), open(dp, "w")); RP.DESIGNATED_PATH = dp
    e1 = RP.declare(man, msha, 40, 1); e1p = os.path.join(d, "e1.json"); json.dump(e1, open(e1p, "w"))
    cp = os.path.join(d, "controls.json"); IG.CONTROLS = cp
    json.dump({"versions": [{"version": 13, "partition": {"path": "x", "sha256": sha(e1p)}}]}, open(cp, "w"))
    proof1, _ = RP.activate(man, mp, e1p, cp, mode="sandbox"); put(RP.activation_path(man, 1), proof1)
    snap = RP.claims_snapshot(man, msha, {"note": case}); sp = os.path.join(d, "snap.json"); json.dump(snap, open(sp, "w"))
    e2 = RP.declare2(man, msha, json.load(open(dp)), sha(dp), snap, sha(sp), e1, sha(e1p), 2); pp = os.path.join(d, "e2.json"); json.dump(e2, open(pp, "w"))
    json.dump({"versions": [{"version": 13, "partition": {"path": "x", "sha256": sha(e1p)}}, {"version": 17, "partition": {"path": "y", "sha256": sha(pp)}}]}, open(cp, "w"))
    ident = dict(root=os.path.abspath(root), manifest_sha256="5" * 64, mode="sandbox")
    ES.install_inventory(root, inventory({}, 2), ident)
    proof2, probs = RP.activate(man, mp, pp, cp, mode="sandbox"); assert probs == [], probs
    put(RP.activation_path(man, 2), proof2)
    opm = ES.derive_operational(man, msha, 2, 75300, "production"); opp = os.path.join(d, "op.json"); json.dump(opm, open(opp, "w")); opsha = sha(opp)
    b = os.path.join(d, "bundle"); broot = os.path.join(b, "root"); env = os.path.join(b, "env"); os.makedirs(env)
    work = work or [(r, 1) for r in W]
    slots = [dict(slot=k, rep=r, indices=[i], role="work") for k, (r, i) in enumerate(work)]
    slots += [dict(slot=len(work) + k, rep=r, indices=[0], role="sentinel") for k, r in enumerate(W)]
    for s in slots:
        r, i, sl = s["rep"], s["indices"][0], s["slot"]
        if sl in unprod and not leave:
            if sl in (status_for or {}):                                 # an orderly non-completion status of that slot
                put(os.path.join(broot, "status", f"job{AID}.slot{sl}.json"), dict(STATUS0, job=AID, slot=sl, rep=r, ident=f"ident{r}", indices=[i],
                                                                                   new=[], left=[i], **status_for[sl]))
            continue
        put(SH.record_path(broot, r, i), rec(r, i)); put(SH.timing_path(broot, r, i), timing(r, i, AID, sl))
        put(os.path.join(broot, "status", f"job{AID}.slot{sl}.json"), dict(STATUS0, job=AID, slot=sl, rep=r, ident=f"ident{r}", indices=[i], new=[i]))
    for r in sorted({s["rep"] for s in slots}):
        json.dump(dict(binding=SH.binding_for(opm, opsha, "/mnt/prod/root", r, SH.task(PROD, r))), open(os.path.join(broot, f"task_{r}.json"), "w"), default=str)
    plan = dict(job=1, attempt_id=AID, sequence=SEQ, epoch=2, contract="production", partition_sha256=sha(pp), opmanifest_sha256=opsha,
                activation_sha256=sha(RP.activation_path(man, 2)), slots=slots)
    put(os.path.join(env, "plan.json"), plan)
    put(os.path.join(env, "upload_verify.json"), dict(transfer_verified=True))
    put(os.path.join(env, "attest_B.json"), dict(profile="B_full", problems=[], XLA_FLAGS=ES.XLA_BASE + " --xla_cpu_max_isa=AVX2", OPENBLAS_CORETYPE="Haswell",
                                                 threads={k: "1" for k in ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
                                                 numpy_dispatch_active=["X86_V2", "X86_V3"], openblas_core={"libscipy_openblas.so": "Haswell"}))
    oc = {f"w_slot{s['slot']}": unprod.get(s["slot"], 0) for s in slots}
    if outcome_override:
        oc.update(outcome_override)
    put(os.path.join(env, "outcomes.json"), dict(declared=len(slots), outcomes=oc, unresolved_after_kill=[]))
    lines = [f"{sha(p)}  {os.path.relpath(p, b)}\n" for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True))
             if os.path.isfile(p) and os.path.relpath(p, b) != "env/upload_verify.json"]
    open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
    att = dict(key=KEY, run="prod-e2", attempt=1, attempt_id=AID, sequence=SEQ, state="reconciled", ingestion="pending", contract="production",
               plan_sha256=sha(os.path.join(env, "plan.json")), coordinates=[list(c) for c in work], sentinels=[[r, 0] for r in W],
               duplicates=[], charged_usd=20.0, **{"class": cls})
    inv = inventory({KEY: att}, 3); ip = os.path.join(d, "inventory.json"); json.dump(inv, open(ip, "w"))
    ES.install_inventory(root, inv, ident)
    return dict(root=root, mp=mp, pp=pp, opp=opp, ip=ip, b=b, e2=e2)


def ingest(c):
    return IG.main(["--manifest", c["mp"], "--partition", c["pp"], "--opmanifest", c["opp"], "--authority", c["ip"], "--attempt-key", KEY, "--bundle", c["b"]])


def entry(c):
    p = os.path.join(c["root"], "ec2", "register.json")
    return (json.load(open(p))["attempts"].get(AID) if os.path.exists(p) else None), (json.load(open(p)) if os.path.exists(p) else None)


def published(c, r, i):
    return os.path.exists(SH.record_path(c["root"], r, i))


# 1 complete
c = build("complete"); rc = ingest(c); e, R = entry(c)
check("complete epoch-2 bundle ingests: 4 work published, 4 sentinels compared, unproduced empty",
      rc == 0 and e["state"] == "ingested" and sorted(e["coordinates"]) == [f"{r}/1" for r in W] and e["unproduced"] == {}
      and len(e["compared_equal"]) == 4 and all(published(c, r, 1) for r in W))
check("the work coordinates are epoch-2-owned (not Lengau's index 0)", all(RP.blocked(c["e2"], r, 1) and not RP.blocked(c["e2"], r, 0) for r in W))
check("a replay of the ingested attempt re-validates", ingest(c) == 0)
c = build("lengau_work", work=[(3, 1), (25, 1), (28, 1), (29, 1)]); rc = ingest(c)
check("a work coordinate outside epoch 2 (rep 3, a Lengau replicate) HOLDS the attempt; nothing published", rc == 3 and entry(c)[0] is None and not published(c, 25, 1))

# 2 partial
c = build("partial", unprod={1: 139}); rc = ingest(c); e, R = entry(c)
check("one worker died (exit 139, no output): the other 3 work coordinates are published, the attempt is 'ingested'",
      rc == 0 and e["state"] == "ingested" and sorted(e["coordinates"]) == ["24/1", "28/1", "29/1"] and published(c, 24, 1) and not published(c, 25, 1))
check("the register lists the unproduced coordinate with its slot and exit; no record is invented for it",
      e["unproduced"] == {"25/1": {"slot": 1, "outcome": 139}} and "25/1" not in e["coordinates"] and not published(c, 25, 1))
check("the fence is raised at the unproduced coordinate too (this attempt can never publish it later)", R["fence"].get("25/1") == SEQ)
check("a replay keeps it unproduced and passes", ingest(c) == 0 and entry(c)[0]["unproduced"] == {"25/1": {"slot": 1, "outcome": 139}})
PA = load_mod("prod_authority", os.path.join(CAND, "aws_ec2", "prod_authority.py"))
import bench_launch as L
TMP = tempfile.mkdtemp(); L.HERE = PA.HERE = TMP
L.save("prod-e2", {"run": "prod-e2", "attempts": [dict(attempt=1, sequence=SEQ, attempt_id=AID, state="reconciled", ingestion="pending", contract="production",
                                                     plan_sha256=json.load(open(c["ip"]))["attempts"][KEY]["plan_sha256"], coordinates=[[r, 1] for r in W],
                                                     lifetime_s=79200, max_price=1.2, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD, type="c7a.24xlarge",
                                                     terminal=dict(compute_s=3600, ancillary_s=3600))]})
check("the Mac ack accepts the partial register entry and records the crash for the EC2 crash rule",
      PA.ack("prod-e2", 1, os.path.join(c["root"], "ec2", "register.json")) is True
      and PA.ec2_crash_history(PA.ledgers())[(25, 1)][0]["exit"] == 139 and PA.owned(PA.ledgers()) == {})
shutil.rmtree(TMP)
c = build("censored", unprod={2: "censored at the upload deadline"}); rc = ingest(c); e, _ = entry(c)
check("a deadline-censored worker without output is unproduced too", rc == 0 and e["unproduced"] == {"28/1": {"slot": 2, "outcome": "censored at the upload deadline"}})
c = build("sentinel1", unprod={5: 134}); rc = ingest(c); e, _ = entry(c)
check("one sentinel lost (3 of 4 compared equal) still publishes the 4 work coordinates", rc == 0 and len(e["compared_equal"]) == 3 and len(e["coordinates"]) == 4)

c = build("resume", unprod={3: 75}, status_for={3: dict(exit=75, reason="deadline: the next refit cannot finish")}); rc = ingest(c); e, _ = entry(c)
check("the worker's own RESUME exit 75 with a status leaving the coordinate is unproduced (deadline)", rc == 0 and e["unproduced"] == {"29/1": {"slot": 3, "outcome": 75}})

# 3 holds
c = build("held4", unprod={1: 4}, status_for={1: dict(exit=4, reason="memory: maxrss above the stop")}); rc = ingest(c)
check("exit 4 (the worker's HELD guard: memory/identity/admission) HOLDS the attempt for review", rc == 3 and entry(c)[0] is None)
c = build("sig_status", unprod={1: 139}, status_for={1: dict(exit=139)}); rc = ingest(c)
check("a signal exit WITH a status is not the crashed-worker signature: HOLDS", rc == 3 and entry(c)[0] is None)
c = build("exit1", unprod={1: 1}); rc = ingest(c)
check("any other exit (1) without output HOLDS", rc == 3 and entry(c)[0] is None)
c = build("resume_nostatus", unprod={1: 75}); rc = ingest(c)
check("RESUME 75 without its status HOLDS (an orderly exit always writes one)", rc == 3 and entry(c)[0] is None)
c = build("ambiguous", unprod={1: 139}, leave=True); rc = ingest(c)
check("an unproduced slot that left its record/timing/status HOLDS (ambiguous output); nothing published", rc == 3 and entry(c)[0] is None and not published(c, 24, 1))
c = build("sentinels2", unprod={4: 139, 5: 139}); rc = ingest(c)
check("only 2 sentinels produced (< 3) HOLDS", rc == 3 and entry(c)[0] is None)
IG.MAX_UNPRODUCED_WORK = 1
c = build("toomany", unprod={0: 139, 1: 137}); rc = ingest(c)
check("more unproduced work slots than the bound HOLDS for a resource review", rc == 3 and entry(c)[0] is None)
IG.MAX_UNPRODUCED_WORK = 7
c = build("badstring", outcome_override={"w_slot0": "killed somehow"}); rc = ingest(c)
check("an outcome that is neither an integer nor the censored marker HOLDS", rc == 3 and entry(c)[0] is None)

# 4 all-or-nothing where it was
c = build("qualification", unprod={1: 139}, cls="qualification")
inv = json.load(open(c["ip"])); rc = ingest(c)
check("a qualification attempt keeps all-or-nothing (and is refused before release anyway)", rc == 3 and entry(c)[0] is None)
check("schema-1 epochs keep all-or-nothing: the partial branch is gated on schema 2 + production (source)",
      'partial = schema2 and att["class"] == "production"' in open(IG.__file__).read())
shutil.rmtree(scratch)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
