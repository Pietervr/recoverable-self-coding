"""Tests of chpc/row19_ec2_qualify.py (the predeclared Q1/Q2/S release rule; Codex 0483db4 V10-7), STUB mode on the Mac:
synthetic records with the frozen-task check stubbed, everything else the real ingestion/state code. Builds a Lengau root,
an isolated S shadow root, a Q1 bundle (48 block + 24 Lengau duplicates + 4 sentinels = 76) and a Q2 bundle (24 repeats)
and checks RELEASE, NO_RELEASE on each kind of difference, INCONCLUSIVE on short successful-fit coverage, the memory gate and
the sandbox replay (R5) on the actual bundle.    .venv/bin/python test_row19_ec2_qualify.py"""
import os, sys, json, glob, shutil, hashlib, copy, tempfile, time, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
def _rsha(d): return hashlib.sha256(json.dumps({k: v for k, v in d.items() if k != "sha"}, sort_keys=True).encode()).hexdigest()
SHs = types.ModuleType("row19_shard")
SHs.task = lambda man, r: dict(ident=f"ident{int(r)}", seed=int(r), n_rep=200, bands=["ws"], code_hash="c")
SHs.record_path = lambda root, r, i: os.path.join(root, "records", f"rep{int(r)}", f"rec_{int(i):03d}.json")
SHs.timing_path = lambda root, r, i: os.path.join(root, "timing", f"rep{int(r)}", f"t_{int(i):03d}.json")
def _read(path, t, i):
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    if d.get("ident") != t["ident"] or d.get("sha") != _rsha(d) or d["rep"] != int(i):
        raise ValueError(f"{path}: not acceptable")
    return d
SHs.read_record = _read
SHs.binding_for = lambda man, msha, root, r, t: dict(manifest_sha=msha, rep=int(r), ident=t["ident"])
Vs = types.ModuleType("row19_screen_verify")
Vs.payload = lambda rec: json.dumps(dict(stats=rec.get("stats"), failed=rec.get("failed"), failed_reason=rec.get("failed_reason")), sort_keys=True)
Vs.timing_ok = lambda d, **w: next((f"{k}" for k, v in w.items() if d.get(k) != v), "")
sys.modules["row19_shard"] = SHs; sys.modules["row19_screen_verify"] = Vs
import row19_partition as RP, row19_ec2_state as ES, row19_ec2_ingest as IG, row19_ec2_qualify as Q, row19_ec2_shadow as SHD
Q.PREDICTORS = ["ws"]; Q.MODE = "sandbox"                         # stub statistics are stats[predictor][band]
ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
prod = json.load(open(os.path.join(HERE, "chpc", "row19_screen_manifest.json")))
REC = lambda r, i, failed=False, v=0.0, nan=False: dict(rep=i, ident=f"ident{r}", stats={"ws": {"ws": float("nan") if nan else 0.01 * r + i + v}},
                                                      failed=failed, failed_reason="nc" if failed else "", sha=None)
def put(root, r, i, rec, job="L", slot=0):
    rec = dict(rec); rec["sha"] = _rsha(rec)
    for p, obj in ((SHs.record_path(root, r, i), rec), (SHs.timing_path(root, r, i), dict(rep=r, index=i, ident=f"ident{r}", fit_seconds=6e4, wall_s=7e4,
                                                                                             failed=rec["failed"], maxrss=2_400_000_000, t=1.0, job=job, slot=slot))):
        os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, "w"))


JID = {1: "7600001.sched01", 2: "7600002.sched01"}


def s_world(d, man, msha, failed, nan, shadow_missing, s_edit):
    """S's isolated root and campaign as the unchanged worker + the shadow admission leave them."""
    sroot, scamp = os.path.join(d, "s_root"), os.path.join(d, "s_camp")
    sman = ES.derive_isolated_S(man, msha, sroot, scamp); sp = os.path.join(d, "s_manifest.json"); json.dump(sman, open(sp, "w"))
    os.makedirs(os.path.join(sroot, "plans")); os.makedirs(os.path.join(sroot, "status")); os.makedirs(scamp)
    entries = {}
    for n in (1, 2):
        plan = SHD.s_job(n); tok = f"tok{n}"
        json.dump(dict(plan, queue="serial", walltime_s=172800, token=tok, created=1.0), open(os.path.join(sroot, "plans", f"job_{n}.json"), "w"))
        entries[tok] = dict(token=tok, kind="shard", rep=n, root=sroot, cores=24, walltime_s=172800, reserved_core_h=1152.0, attempt=1,
                            state="settled", job_id=JID[n], settled_core_h=600.0)
        for sl in plan["slots"]:
            r, i = sl["rep"], sl["indices"][0]
            if (r, i) != shadow_missing:
                put(sroot, r, i, REC(r, i, (r, i) in failed, nan=(r, i) in nan), job=JID[n], slot=sl["slot"])
            json.dump(dict(job=JID[n], slot=sl["slot"], rep=r, ident=f"ident{r}", indices=[i], new=[i], resumed=[], left=[], exit=0, reason="",
                           wall_s=7e4, cpu_s=7e4, started=1.0, ended=2.0, maxrss=2_400_000_000), open(os.path.join(sroot, "status", f"job{JID[n]}.slot{sl['slot']}.json"), "w"))
    json.dump(dict(cap_core_h=2304.0, entries=entries), open(os.path.join(scamp, "budget.json"), "w"))
    if s_edit:
        s_edit(sroot, scamp)
    return sp


def world(case, failed=frozenset(), q2_delta=None, lengau_delta=None, shadow_missing=None, mem_peak_kb=150 * 2 ** 20, nan=frozenset(),
          running=None, s_edit=None):
    d = os.path.join(tempfile.mkdtemp(), case); os.makedirs(d)
    root = os.path.join(d, "root"); os.makedirs(os.path.join(root, "plans"))
    for r in range(3, 27):
        for i in (0, 1, 2):
            put(root, r, i, REC(r, i, (r, i) in failed, nan=(r, i) in nan))
    man = copy.deepcopy(prod); man["storage"] = {"root": root, "campaign": os.path.join(d, "camp")}
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w")); msha = sha(mp)
    smp = s_world(d, man, msha, failed, nan, shadow_missing, s_edit)
    part = RP.declare(man, msha, 2, 1); pp = os.path.join(d, "partition.json"); json.dump(part, open(pp, "w"))
    cp = os.path.join(d, "ctl.json"); json.dump({"versions": [{"version": 10, "partition": {"sha256": sha(pp)}}]}, open(cp, "w"))
    Q.CONTROLS = cp
    os.makedirs(os.path.join(root, "ec2")); json.dump(RP.activate(man, mp, pp, cp, mode="sandbox")[0], open(RP.activation_path(man, 1), "w"))
    actsha = sha(RP.activation_path(man, 1))
    atts = {}
    def bundle(key, contract, seq, work, dup, sent, delta=None):
        opm = ES.derive_operational(man, msha, 1, 75300, contract); opp = os.path.join(d, f"op_{contract}.json"); json.dump(opm, open(opp, "w"))
        aid = f"ec2-{key.split('/')[0]}-a1"; b = os.path.join(d, f"b_{contract}"); env = os.path.join(b, "env"); os.makedirs(env)
        roles = [("work", c) for c in work] + [("qual_lengau" if contract == "Q1" else "qual_repeat", c) for c in dup] + [("sentinel", c) for c in sent]
        slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in enumerate(roles)]
        for s in slots:
            r, i = s["rep"], s["indices"][0]
            v = (delta or {}).get((r, i), 0.0)
            put(os.path.join(b, "root"), r, i, REC(r, i, (r, i) in failed, v, nan=(r, i) in nan), job=aid, slot=s["slot"])
            os.makedirs(os.path.join(b, "root", "status"), exist_ok=True)
            json.dump(dict(job=aid, slot=s["slot"], rep=r, ident=f"ident{r}", indices=[i], new=[i], resumed=[], left=[], exit=0, reason="",
                           wall_s=7e4, cpu_s=7e4, started=1.0, ended=2.0, maxrss=2_400_000_000), open(os.path.join(b, "root", "status", f"job{aid}.slot{s['slot']}.json"), "w"))
        for r in {s["rep"] for s in slots}:
            json.dump(dict(binding=SHs.binding_for(opm, sha(opp), "/mnt/prod/root", r, SHs.task(man, r))), open(os.path.join(b, "root", f"task_{r}.json"), "w"))
        plan = dict(job=1, attempt_id=aid, sequence=seq, epoch=1, contract=contract, partition_sha256=sha(pp), opmanifest_sha256=sha(opp),
                    activation_sha256=actsha, slots=slots)
        json.dump(plan, open(os.path.join(env, "plan.json"), "w"))
        json.dump(dict(transfer_verified=True), open(os.path.join(env, "upload_verify.json"), "w"))
        json.dump(dict(profile="B_full", problems=[], XLA_FLAGS=ES.XLA_BASE + " --xla_cpu_max_isa=AVX2", OPENBLAS_CORETYPE="Haswell",
                       threads={k: "1" for k in ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
                       numpy_dispatch_active=["X86_V3"], openblas_core={"lib": "Haswell"}), open(os.path.join(env, "attest_B.json"), "w"))
        json.dump(dict(declared=len(slots), outcomes={f"w_slot{s['slot']}": 0 for s in slots}, unresolved_after_kill=[]), open(os.path.join(env, "outcomes.json"), "w"))
        open(os.path.join(env, "memory.txt"), "w").write("".join(f"{60 * t} {192 * 2 ** 20} {192 * 2 ** 20 - mem_peak_kb} 1\n" for t in range(12)))
        nrun = len(slots) if running is None else running
        open(os.path.join(env, "occupancy.txt"), "w").write("".join(f"{60 * t} {nrun} 70.0 70.0 70.0\n" for t in range(12)))
        lines = [f"{sha(p)}  {os.path.relpath(p, b)}\n" for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True))
                 if os.path.isfile(p) and os.path.relpath(p, b) != "env/upload_verify.json"]
        open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
        atts[key] = dict(key=key, run=key.split("/")[0], attempt=1, attempt_id=aid, sequence=seq, state="reconciled", ingestion="pending",
                         contract=contract, plan_sha256=sha(os.path.join(env, "plan.json")), coordinates=[list(c) for c in work],
                         sentinels=[list(c) for c in sent], duplicates=[list(c) for c in dup], charged_usd=20.0, **{"class": "qualification"})
        return b, opp
    b1, op1 = bundle("qual-Q1/1", "Q1", 1, Q.Q1_BLOCK, Q.Q1_LENGAU, [(20, 0), (21, 0), (22, 0), (23, 0)], delta=lengau_delta)
    b2, op2 = bundle("qual-Q2/1", "Q2", 2, [], Q.Q2_REPEAT, [], delta=q2_delta)
    own = {f"{c[0]}/{c[1]}": [k, a["sequence"]] for k, a in atts.items() if ES.owns(a) for c in a["coordinates"]}
    fence = {f"{c[0]}/{c[1]}": a["sequence"] for a in atts.values() for c in a["coordinates"]}
    inv = ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=5, at=time.time(), attempts=atts, owners=dict(sorted(own.items())), fence=fence,
                       release=dict(production_released=False, released_attempts=[]), usd={}))
    ip = os.path.join(d, "inv.json"); json.dump(inv, open(ip, "w"))
    out = os.path.join(d, "cert.json")
    rc = Q.main(["--manifest", mp, "--partition", pp, "--authority", ip, "--q1-key", "qual-Q1/1", "--q1-bundle", b1, "--q1-opmanifest", op1,
                 "--q2-key", "qual-Q2/1", "--q2-bundle", b2, "--q2-opmanifest", op2, "--s-manifest", smp, "--sandbox", os.path.join(d, "sb"), "--out", out])
    cert = json.load(open(out))
    return rc, cert, root


rc, cert, root = world("clean")
check("clean panel: RELEASE, Q1 named released, replay R5 passes, memory reported", rc == 0 and cert["outcome"] == "RELEASE" and cert["released_attempts"] == ["qual-Q1/1"]
      and cert["replay"]["final_state"] == "ingested" and cert["replay"]["hashes_equal"] and cert["memory"]["samples_at_full_packing"] == 12, cert["problems"][:3])
check("R1-6 the replay states its exact scope (no producer/host or transfer recovery claimed)", "NOT producer" in cert["replay"]["scope"])
check("R1-4 S producer evidence is reported and bound (jobs, PBS ids, ledger, plans, statuses)", cert["s"]["1"]["job_id"] == JID[1]
      and cert["bound"]["s"]["ledger_sha256"] and len(cert["bound"]["s"]["plans"]) == 2 and cert["schema"].endswith("-2"))
check("the evaluation never writes the screen root (replay ran in the sandbox)", not os.path.exists(os.path.join(root, "ec2", "register.json")))
check("the certificate binds code, manifests, plans, bundles, inventory, S evidence", all(cert["bound"].get(k) for k in
      ("code", "manifest_sha256", "partition_sha256", "activation_sha256", "inventory_sha256", "opmanifests", "bundles", "plans", "s")))
rc, cert, _ = world("q2diff", q2_delta={(5, 199): 1e-12})
check("one Q2 payload difference: NO_RELEASE", rc == 3 and cert["outcome"] == "NO_RELEASE" and any("R3" in p for p in cert["problems"]), cert["problems"][:2])
rc, cert, _ = world("l1diff", lengau_delta={(4, 2): 1e-12})
check("one Q1-vs-Lengau duplicate difference: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("R1" in p for p in cert["problems"]), cert["problems"][:2])
rc, cert, _ = world("shadowmiss", shadow_missing=(10, 198))
check("a missing S shadow reference: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("(10, 198)" in p for p in cert["problems"]), cert["problems"][:2])
rc, cert, _ = world("mem", mem_peak_kb=186 * 2 ** 20)
check("host memory above 184 GiB at the 76-worker packing: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("memory" in p for p in cert["problems"]), cert["problems"][:2])
many = frozenset({(r, i) for r in range(3, 10) for i in (198, 199)})
rc, cert, _ = world("cov", failed=many)
check("failed fits agreeing everywhere but short successful coverage: INCONCLUSIVE (never RELEASE)",
      rc == 3 and cert["outcome"] == "INCONCLUSIVE" and "R2" in cert["coverage_short"] and cert["parts"]["R2"]["failed_both"] == 14, (cert["outcome"], cert["coverage_short"], cert["problems"][:2]))
rc, cert, _ = world("fewfail", failed=frozenset({(3, 199), (3, 198), (4, 1)}))
check("a few agreeing failed fits are reported apart and still RELEASE", cert["outcome"] == "RELEASE" and cert["parts"]["R2"]["failed_both"] == 2, cert["problems"][:2])
# R1-4: agreeing checksum-valid non-finite statistics never count as successful fits
nanset = frozenset({(r, i) for r in range(3, 12) for i in (198, 199)})
rc, cert, _ = world("nan", nan=nanset)
check("R1-4 agreeing non-finite paths are counted apart and short coverage is INCONCLUSIVE, never RELEASE",
      cert["outcome"] == "INCONCLUSIVE" and cert["parts"]["R2"]["nonfinite_both"] == 18 and cert["parts"]["R2"]["successful_both"] == 30,
      (cert["outcome"], cert["parts"].get("R2"), cert["problems"][:2]))
# R1-4: S provenance
rc, cert, _ = world("s_nostatus", s_edit=lambda r, c: os.remove(os.path.join(r, "status", f"job{JID[2]}.slot5.json")))
check("R1-4 an S slot without its terminal worker status: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("S job 2" in p for p in cert["problems"]), cert["problems"][:2])
def unsettle(r, c):
    L = json.load(open(os.path.join(c, "budget.json"))); L["entries"]["tok1"].update(state="live"); json.dump(L, open(os.path.join(c, "budget.json"), "w"))
rc, cert, _ = world("s_live", s_edit=unsettle)
check("R1-4 an S job whose producing entry is not settled: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("S job 1" in p for p in cert["problems"]), cert["problems"][:2])
def plan_edit(r, c):
    p_ = os.path.join(r, "plans", "job_2.json"); d_ = json.load(open(p_)); d_["slots"][0]["indices"] = [197]; json.dump(d_, open(p_, "w"))
rc, cert, _ = world("s_plan", s_edit=plan_edit)
check("R1-4 an S plan that is not the declared fixed plan: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("fixed plan" in p for p in cert["problems"]), cert["problems"][:2])
def foreign_timing(r, c):
    tp = SHs.timing_path(r, 3, 199); t = json.load(open(tp)); t["job"] = "999.sched01"; json.dump(t, open(tp, "w"))
rc, cert, _ = world("s_timing", s_edit=foreign_timing)
check("R1-4 an S record whose timing names another producer: NO_RELEASE", cert["outcome"] == "NO_RELEASE", cert["problems"][:2])
# R1-6: memory samples must cover the full planned packing
rc, cert, _ = world("packing", running=40)
check("R1-6 memory samples taken below the 76-worker packing: NO_RELEASE", cert["outcome"] == "NO_RELEASE" and any("full 76-worker packing" in p for p in cert["problems"]), cert["problems"][:2])
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
