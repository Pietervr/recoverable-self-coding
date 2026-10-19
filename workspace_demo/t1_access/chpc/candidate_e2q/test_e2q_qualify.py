"""EC2 provider epoch 2 QUALIFICATION CANDIDATE (NOT adopted): the schema-3 certificate of chpc/candidate_e2q/row19_ec2_qualify.py
(`e2` command, REVISION 5), STUB mode on the Mac exactly as the existing test_row19_ec2_qualify.py / candidate_e2/test_e2_ingest.py:
synthetic records with the frozen-task check stubbed, everything else the real candidate modules (partition, ingestion,
shared rules, state with the E2Q contracts, panel). No fits, no Lengau, no AWS.

The world: a screen root under an ACTIVATED schema-2 epoch 2 (sandbox mode, predecessor e1 activated first), declared from a
claims snapshot whose Lengau-completed coordinates are those of 17 Oct on the first EC2 replicates (rep 24: 0-8, rep 25: 0-5,
7, 8, rep 28: 0-2; rep 24 indices 9-10 planned), so the DECLARED panel is the real one: 52 work = rep 24 indices 11..62, 20
duplicates, 61 workers on rep 24. One E2Q1 bundle of 76 slots (52 work + 20 duplicates + 4 sentinels).

  1. a complete clean bundle: RELEASE; the certificate binds code, manifest, partition, panel, funding, both operational
     manifests, bundle, plan; R5' replay ingested with the SYNTHETIC per-slot case labelled and the modified replay HELD;
  2. each single R1'-R5' violation gives NO_RELEASE: a parity bit-flip on a duplicate, a sentinel mismatch, a crashed slot of
     no qualifying kind (exit 1), a present null status, an absent status of a produced slot, 4 non-completions (R4' > 3),
     a memory/occupancy gap (too few full-packing samples), host memory above 184 GiB, a replay mismatch;
  3. qualifying non-completions are reported and never invented as failed-fit records: a crashed work slot (139, no
     status) RELEASES with the ACTUAL per-slot case; a censored duplicate is reported and not compared;
  4. coverage: agreeing failed duplicates leaving < 15 finite successful -> INCONCLUSIVE, never RELEASE;
  5. input refusals: an attempt that is not the declared panel, a tampered panel, an operational manifest at another
     lifetime, an epoch-1 (schema-1) partition, a wrong funding declaration.
  6. REVISION 6 of the qualifier (Codex review reviews/2026-10-19_e2_adoption_codex_review.md B2 and "Before one paid E2Q1"):
     the review's full schema-3 counter case (12 full-packing samples, MemTotal 192 GiB, MemAvailable 193 GiB) now refuses;
     parser negatives (zero/negative total, available outside [0, total], negative RSS, non-integer fields, a repeated or
     backward timestamp, 12 copies of one timestamp, occupancy outside 0..76, a bad load average, a wrong field count, one
     occupancy line amplified over 12 memory samples) each give a failed verdict, never an exception or a release; and the
     RELOCATED snapshot layout: a panel whose recorded snapshot path is absent in the deployed tree refuses without --snapshot,
     releases with the deployed hash-checked copy passed by --snapshot (the panel bytes untouched), and refuses a tampered copy.

    python3 chpc/candidate_e2q/test_e2q_qualify.py              (from workspace_demo/t1_access)"""
import copy, glob, hashlib, importlib.util, json, os, shutil, sys, tempfile, time, types

Q = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(Q); T1 = os.path.dirname(CHPC); E2 = os.path.join(CHPC, "candidate_e2")
for p in (T1, CHPC, E2, Q):
    sys.path.insert(0, p)
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


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


ES = load_mod("row19_ec2_state", os.path.join(Q, "row19_ec2_state.py"))
E2R = load_mod("row19_ec2_e2rules", os.path.join(E2, "row19_ec2_e2rules.py"))
RP = load_mod("row19_partition", os.path.join(E2, "row19_partition.py"))
IG = load_mod("row19_ec2_ingest", os.path.join(E2, "row19_ec2_ingest.py"))
EQ = load_mod("row19_ec2_e2qual", os.path.join(Q, "row19_ec2_e2qual.py"))
QU = load_mod("row19_ec2_qualify", os.path.join(Q, "row19_ec2_qualify.py"))
QU.PREDICTORS = ["ws"]; QU.MODE = "sandbox"; IG.ACTIVATION_MODE = "sandbox"
PROD = json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))
DESIG = json.load(open(os.path.join(CHPC, "row19_screen_designated.json")))
CENS = E2R.CENSORED
LENGAU_DONE = [(24, i) for i in range(9)] + [(25, i) for i in (0, 1, 2, 3, 4, 5, 7, 8)] + [(28, i) for i in (0, 1, 2)] + [(3, i) for i in range(6)]
SENT = [(3, 0), (3, 1), (3, 2), (3, 3)]
KEY, AID, SEQ = "qual-E2Q1/1", "ec2-qual-E2Q1-a1", 11
STATUS0 = dict(exit=0, reason="", left=[], resumed=[], wall_s=70000.0, cpu_s=69000.0, started=1.0, ended=70001.0, maxrss=2_400_000_000, host="ip-10-0-0-1")
scratch = tempfile.mkdtemp()


def rec(r, i, delta=0.0, failed=False):
    d = dict(rep=i, ident=f"ident{r}", stats={"ws": {"ws": 0.01 * r + i + delta}}, failed=failed, failed_reason="nc" if failed else "")
    return dict(d, sha=_rsha(d))


def timing(r, i, job, slot):
    return dict(rep=r, index=i, ident=f"ident{r}", fit_seconds=60000.0, wall_s=70000.0, failed=False, maxrss=2_400_000_000, t=1.0, job=job, slot=slot, host="h")


def put(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, "w"))


def world(case, unprod=None, status_for=None, raw_status=None, dup_delta=None, sent_delta=None, failed_dups=(), mem_peak_gib=150.0,
          full_samples=12, drop_status=None, att_edit=None, panel_edit=None, op_lifetime=None, use_e1=False, fund_edit=None,
          corrupt_replay=False, mem_text=None, occ_text=None, relocate=None):
    unprod = unprod or {}
    d = os.path.join(scratch, case); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    root, camp = os.path.join(d, "root"), os.path.join(d, "camp"); os.makedirs(os.path.join(root, "plans")); os.makedirs(camp)
    for r, i in LENGAU_DONE:
        put(SHs.record_path(root, r, i), rec(r, i, failed=(r, i) in failed_dups)); put(SHs.timing_path(root, r, i), timing(r, i, "7523818.sched01", 0))
    put(os.path.join(root, "plans", "job_1.json"), {"job": 1, "slots": [{"slot": 0, "rep": 24, "indices": [9]}, {"slot": 1, "rep": 24, "indices": [10]}]})
    put(os.path.join(camp, "budget.json"), {"entries": {"t": {"kind": "shard", "rep": 1, "state": "settled", "job_id": "1.s"}}})
    man = copy.deepcopy(PROD); man["storage"] = {"root": root, "campaign": camp}
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w")); msha = sha(mp)
    dp = os.path.join(d, "designated.json"); json.dump(dict(DESIG, manifest_sha256=msha), open(dp, "w")); RP.DESIGNATED_PATH = dp
    e1 = RP.declare(man, msha, 40, 1); e1p = os.path.join(d, "e1.json"); json.dump(e1, open(e1p, "w"))
    cp = os.path.join(d, "controls.json"); QU.CONTROLS = cp
    json.dump({"versions": [{"version": 13, "partition": {"path": "x", "sha256": sha(e1p)}}]}, open(cp, "w"))
    proof1, _ = RP.activate(man, mp, e1p, cp, mode="sandbox"); put(RP.activation_path(man, 1), proof1)
    ident = dict(root=os.path.abspath(root), manifest_sha256=msha, mode="sandbox")
    ES.install_inventory(root, ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=2, at=time.time(), attempts={}, owners={}, fence={},
                                            release=dict(production_released=False, released_attempts=[]), usd={})), ident)
    snap = RP.claims_snapshot(man, msha, {"note": case}); sp = os.path.join(d, "snap.json"); json.dump(snap, open(sp, "w"))
    e2 = RP.declare2(man, msha, json.load(open(dp)), sha(dp), snap, sha(sp), e1, sha(e1p), 2); pp = os.path.join(d, "e2.json"); json.dump(e2, open(pp, "w"))
    if not use_e1:
        json.dump({"versions": [{"version": 13, "partition": {"path": "x", "sha256": sha(e1p)}}, {"version": 17, "partition": {"path": "y", "sha256": sha(pp)}}]}, open(cp, "w"))
        proof2, probs = RP.activate(man, mp, pp, cp, mode="sandbox"); assert probs == [], probs
        put(RP.activation_path(man, 2), proof2)
    snap_arg = None
    if relocate:                                                    # REVISION 6: the deployed layout lacks the recorded source path
        recorded = os.path.join(d, "source_evidence", "e2_final", "claims_snapshot_e2.json")   # never created in this tree
        panel = EQ.derive_panel(e2, sha(pp), snap, sha(sp), recorded)
        dep = os.path.join(d, "deployed", "chpc", "claims_snapshot_e2.json"); os.makedirs(os.path.dirname(dep))
        shutil.copyfile(sp, dep)
        if relocate == "tampered":
            open(dep, "a").write("\n")                              # same JSON content, other bytes: the sha256 no longer binds
        snap_arg = None if relocate == "absent" else dep
    else:
        panel = EQ.derive_panel(e2, sha(pp), snap, sha(sp), sp)
    if panel_edit:
        panel_edit(panel)
    panp = os.path.join(d, "panel.json"); open(panp, "wb").write(EQ.panel_bytes(panel))
    ops = {}
    for c in ("E2Q1", "production"):
        ops[c] = os.path.join(d, f"op_{c}.json"); open(ops[c], "wb").write(EQ.opmanifest_bytes(ES, man, msha, c))
    if op_lifetime:
        open(ops["E2Q1"], "w").write(json.dumps(ES.derive_operational(man, msha, 2, op_lifetime, "E2Q1"), indent=1, sort_keys=True))
    fund = {"schema": "t1-ec2-epoch-funding-1", "epoch": 2, "partition_owned_sha256": e2["owned_sha256"], "lifetime_s": 79200}
    if fund_edit:
        fund.update(fund_edit)
    fp = os.path.join(d, "funding.json"); json.dump(fund, open(fp, "w"))
    work = [tuple(c) for c in panel["work"]]; dups = [tuple(c) for c in panel["duplicates"]]
    b = os.path.join(d, "bundle"); broot = os.path.join(b, "root"); env = os.path.join(b, "env"); os.makedirs(env)
    roles = [("work", c) for c in work] + [("qual_lengau", c) for c in dups] + [("sentinel", c) for c in SENT]
    slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in enumerate(roles)]
    for s in slots:
        r, i, sl = s["rep"], s["indices"][0], s["slot"]
        stp = os.path.join(broot, "status", f"job{AID}.slot{sl}.json")
        if sl in unprod:
            if sl in (status_for or {}):
                st = dict(STATUS0, job=AID, slot=sl, rep=r, ident=f"ident{r}", indices=[i], new=[], left=[i]); st.update(status_for[sl]); put(stp, st)
            elif sl in (raw_status or {}):
                os.makedirs(os.path.dirname(stp), exist_ok=True); open(stp, "w").write(raw_status[sl])
            continue
        delta = (dup_delta or {}).get((r, i), 0.0) + (sent_delta or {}).get((r, i), 0.0)
        put(SHs.record_path(broot, r, i), rec(r, i, delta, failed=(r, i) in failed_dups)); put(SHs.timing_path(broot, r, i), timing(r, i, AID, sl))
        if sl != drop_status:
            put(stp, dict(STATUS0, job=AID, slot=sl, rep=r, ident=f"ident{r}", indices=[i], new=[i]))
    opm = json.load(open(ops["E2Q1"])); opsha = sha(ops["E2Q1"])
    for r in sorted({s["rep"] for s in slots}):
        json.dump(dict(binding=SHs.binding_for(opm, opsha, "/mnt/prod/root", r, SHs.task(PROD, r))), open(os.path.join(broot, f"task_{r}.json"), "w"), default=str)
    psel = e1p if use_e1 else pp
    plan = dict(job=1, attempt_id=AID, sequence=SEQ, epoch=2, contract="E2Q1", partition_sha256=sha(psel), opmanifest_sha256=opsha,
                activation_sha256=sha(RP.activation_path(man, 1 if use_e1 else 2)), instance=dict(ES.CONTRACTS["E2Q1"]), lifetime_s=79200, slots=slots)
    put(os.path.join(env, "plan.json"), plan)
    put(os.path.join(env, "upload_verify.json"), dict(transfer_verified=True))
    put(os.path.join(env, "attest_B.json"), dict(profile="B_full", problems=[], XLA_FLAGS=ES.XLA_BASE + " --xla_cpu_max_isa=AVX2", OPENBLAS_CORETYPE="Haswell",
                                                 threads={k: "1" for k in ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
                                                 numpy_dispatch_active=["X86_V2", "X86_V3"], openblas_core={"libscipy_openblas.so": "Haswell"}))
    oc = {f"w_slot{s['slot']}": unprod.get(s["slot"], 0) for s in slots}
    put(os.path.join(env, "outcomes.json"), dict(declared=len(slots), outcomes=oc, unresolved_after_kill=[]))
    open(os.path.join(env, "censored.txt"), "w").write("".join(f"{n}\n" for n in sorted(k for k, v in oc.items() if v == CENS)))
    total = 192 * 2 ** 20
    open(os.path.join(env, "memory.txt"), "w").write("".join(f"{60 * t} {total} {total - int(mem_peak_gib * 2 ** 20)} {76 * 2_300_000}\n" for t in range(12)))
    open(os.path.join(env, "occupancy.txt"), "w").write("".join(f"{60 * t} {76 if t < full_samples else 70} 70.0 70.0 70.0\n" for t in range(12)))
    if mem_text is not None:
        open(os.path.join(env, "memory.txt"), "w").write(mem_text)
    if occ_text is not None:
        open(os.path.join(env, "occupancy.txt"), "w").write(occ_text)
    lines =[f"{sha(p)}  {os.path.relpath(p, b)}\n" for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True))
             if os.path.isfile(p) and os.path.relpath(p, b) != "env/upload_verify.json"]
    open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
    att = dict(key=KEY, run="qual-E2Q1", attempt=1, attempt_id=AID, sequence=SEQ, state="reconciled", ingestion="pending", contract="E2Q1",
               disposition_requested=False, plan_sha256=sha(os.path.join(env, "plan.json")), coordinates=[list(c) for c in work],
               sentinels=[list(c) for c in SENT], duplicates=[list(c) for c in dups], charged_usd=26.0, **{"class": "qualification"})
    if att_edit:
        att_edit(att)
    owners = {f"{c[0]}/{c[1]}": [KEY, SEQ] for c in sorted(map(tuple, att["coordinates"]))}
    inv = ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=3, at=time.time(), attempts={KEY: att}, owners=owners,
                       fence={k: SEQ for k in owners}, release=dict(production_released=False, released_attempts=[]), usd={}))
    ip = os.path.join(d, "inventory.json"); json.dump(inv, open(ip, "w"))
    out = os.path.join(d, "cert.json")
    real_main, calls = IG.main, [0]
    def corrupting(argv):                                           # a replay mismatch: a published sandbox file changes before the 2nd replay
        calls[0] += 1
        if calls[0] == 3:
            srt = argv[argv.index("--manifest") + 1]; sroot = json.load(open(srt))["storage"]["root"]
            rp = SHs.record_path(sroot, *work[0]); os.chmod(rp, 0o644); r_ = json.load(open(rp)); r_["stats"]["ws"]["ws"] += 1e-12; json.dump(r_, open(rp, "w"))
        return real_main(argv)
    if corrupt_replay:
        IG.main = corrupting
    try:
        rc = QU.main_e2(["--manifest", mp, "--partition", e1p if use_e1 else pp, "--authority", ip, "--key", KEY, "--bundle", b,
                         "--opmanifest", ops["E2Q1"], "--prod-opmanifest", ops["production"], "--panel", panp, "--funding", fp,
                         "--sandbox", os.path.join(d, "sb"), "--out", out] + (["--snapshot", snap_arg] if snap_arg else []))
    finally:
        IG.main = real_main
    return rc, json.load(open(out)), dict(d=d, root=root, b=b, work=work, dups=dups, panel=panel, sb=os.path.join(d, "sb"), panp=panp,
                                          snap_sha=sha(sp), snap_arg=snap_arg)


def no_release(case, cert, needle):
    return cert["outcome"] == "NO_RELEASE" and cert["released_attempts"] == [] and any(needle in p for p in cert["problems"])


# 1 clean
rc, cert, w = world("clean")
check("the world's declared panel is the real one: 52 work = rep 24 indices 11..62, 20 duplicates, 61 on rep 24",
      w["work"] == [(24, i) for i in range(11, 63)] and len(w["dups"]) == 20 and w["panel"]["concentration"]["max"] == 61)
check("clean E2Q1 bundle: RELEASE naming the attempt, no problems, R1' 20/20 finite successful", rc == 0 and cert["outcome"] == "RELEASE"
      and cert["released_attempts"] == [KEY] and cert["problems"] == [] and cert["parts"]["R1"]["successful_both"] == 20, cert["problems"][:3])
check("schema 3, epoch 2; R4' memory 12 samples at the full 76-worker packing; plan concentration 61 on rep 24 (sentinels on rep 3)",
      cert["schema"] == "row19-ec2-qualification-certificate-3" and cert["epoch"] == 2 and cert["memory"]["samples_at_full_packing"] == 12
      and cert["memory"]["workers"] == 76 and cert["concentration"]["max"] == 61 and cert["concentration"]["max_reps"] == [24] and cert["concentration"]["slots"] == 76)
check("R2' validity: 52 produced work records, none unproduced, stated as a limitation (no reference)",
      cert["parts"]["R2_validity"]["produced"] == 52 and cert["parts"]["R2_validity"]["unproduced"] == [] and "no reference" in cert["parts"]["R2_validity"]["limitation"])
check("R4' sentinels: 4 compared equal against Lengau", cert["parts"]["R4_sentinels"]["successful_both"] == 4)
rp_ = cert["replay"]
check("R5' replay: forced stop 'ingesting' then two replays -> 'ingested', hashes equal, attempt presented as class production, scope stated",
      rp_["forced_stop_rc"] == 3 and rp_["state_after_stop"] == "ingesting" and rp_["replay_rc"] == 0 and rp_["second_replay_rc"] == 0
      and rp_["final_state"] == "ingested" and rp_["hashes_equal"] and rp_["presented_class"] == "production" and "NOT producer" in rp_["scope"])
ps = rp_["per_slot"]
check("R5' per-slot (no actual unproduced work slot): SYNTHETIC fatal-signal case on the first work slot - listed, fenced, evidence journaled, ack rule releases",
      ps["mode"] == "synthetic" and ps["slot"] == 0 and ps["coordinate"] == "24/11" and ps["outcome"] == 139 and ps["listed"] and ps["fenced"]
      and ps["evidence_journaled"] and ps["ack_problem"] == "" and ps["ingest_rc"] == 0)
check("R5' the modified bundle replayed against the UNMODIFIED journal HOLDS (ec2/HOLD in the sandbox)", ps["modified_replay_held"] and ps["modified_replay_rc"] == 3)
syn = {s["file"]: s for s in ps["synthetic"]}
check("every synthetic modification is labelled SYNTHETIC with its original and modified sha256 (record, timing, status removed; outcomes; checksums)",
      len(syn) == 5 and all(s["label"].startswith("SYNTHETIC") for s in syn.values()) and syn["env/outcomes.json"]["modified_sha256"] != syn["env/outcomes.json"]["original_sha256"]
      and all(s["modified_sha256"] is None and s["original_sha256"] for f, s in syn.items() if s["label"].endswith("removed")))
bd = cert["bound"]
check("the certificate binds code (the exact epoch-2 set), manifest, partition + owned digest, activation, inventory, panel, snapshot, funding, both operational manifests, lifetime, bundle, plan",
      sorted(bd["code"]) == EQ.CODE and all(bd.get(k) for k in ("manifest_sha256", "partition_sha256", "owned_sha256", "activation_sha256", "inventory_sha256",
                                                                "panel_sha256", "claims_snapshot_sha256", "funding_sha256", "bundle_sha256", "plan_sha256"))
      and set(bd["opmanifests"]) == {"qualified", "production"} and bd["lifetime_s"] == 79200)
check("the bound code is the candidate files actually used (ingest from candidate_e2, state/qualifier/panel from candidate_e2q)",
      bd["code"]["chpc/row19_ec2_ingest.py"] == sha(os.path.join(E2, "row19_ec2_ingest.py")) and bd["code"]["chpc/row19_ec2_state.py"] == sha(os.path.join(Q, "row19_ec2_state.py"))
      and bd["code"]["chpc/row19_ec2_qualify.py"] == sha(os.path.join(Q, "row19_ec2_qualify.py")))
check("the evaluation never writes the world root (the replay ran in its sandbox)", not os.path.exists(os.path.join(w["root"], "ec2", "register.json")))

# 2 each single R1'-R5' violation -> NO_RELEASE
rc, cert, _ = world("r1_bitflip", dup_delta={(25, 3): 1e-12})
check("R1': ONE duplicate payload bit-flip (1e-12) -> NO_RELEASE", rc == 3 and no_release("", cert, "R1 (25, 3)"), cert["problems"][:2])
rc, cert, _ = world("r4_sentinel", sent_delta={(3, 2): 1e-12})
check("R4': a sentinel mismatch against Lengau -> NO_RELEASE", no_release("", cert, "R4_sentinels (3, 2)"), cert["problems"][:2])
rc, cert, _ = world("crash_exit1", unprod={5: 1})
check("a crashed slot of NO qualifying kind (exit 1, no output) -> NO_RELEASE", no_release("", cert, "not a qualifying non-completion"), cert["problems"][:2])
rc, cert, _ = world("null_status", unprod={5: 139}, raw_status={5: "null\n"})
check("a PRESENT null status of an unproduced slot -> NO_RELEASE (never 'no status')", no_release("", cert, "not a JSON object"), cert["problems"][:2])
rc, cert, _ = world("absent_status", drop_status=7)
check("an ABSENT status of a produced slot -> NO_RELEASE (a complete terminal status is required)", no_release("", cert, "status missing"), cert["problems"][:2])
rc, cert, _ = world("four_unproduced", unprod={0: 139, 1: 139, 60: 139, 61: 139})
check("R4': 4 non-completed slots of all roles (> 3) -> NO_RELEASE", no_release("", cert, "R4': 4 non-completed"), cert["problems"][:2])
rc, cert, _ = world("mem_gap", full_samples=9)
check("R4': a memory/occupancy gap - 9 samples with all 76 running (< 10) -> NO_RELEASE", no_release("", cert, "memory gate: 9 samples at the full 76-worker"), cert["problems"][:2])
rc, cert, _ = world("mem_peak", mem_peak_gib=185.0)
check("R4': peak host use 185 GiB (> 184) -> NO_RELEASE", no_release("", cert, "peak host use 185.0"), cert["problems"][:2])
rc, cert, _ = world("replay_mismatch", corrupt_replay=True)
check("R5': a replay mismatch (a published sandbox record changed before the second replay) -> NO_RELEASE", no_release("", cert, "R5' sandbox replay failed")
      and cert["replay"]["second_replay_rc"] == 3, cert["problems"][:2])

# 3 qualifying non-completions are reported, never invented
rc, cert, w = world("actual_139", unprod={20: 139})
check("a crashed WORK slot (139, status absent) is a qualifying non-completion: RELEASE, reported with slot/role/coordinate/exit/kind",
      cert["outcome"] == "RELEASE" and cert["unproduced"] == [dict(slot=20, role="work", coordinate=[24, 31], outcome=139, kind="fatal_signal", status_present=False)], cert["problems"][:2])
check("... R2' counts it unproduced (51 produced), and R5' exercises the ACTUAL per-slot case (listed, fenced, evidence, ack)",
      cert["parts"]["R2_validity"]["produced"] == 51 and cert["parts"]["R2_validity"]["unproduced"] == [[24, 31]]
      and cert["replay"]["per_slot"]["mode"] == "actual" and cert["replay"]["per_slot"]["coordinate"] == "24/31" and cert["replay"]["per_slot"]["ack_problem"] == "")
sbA = os.path.join(w["sb"], "A", "root")
check("... and no record is invented for the crashed coordinate (absent in the sandbox root after ingestion)",
      not os.path.exists(SHs.record_path(sbA, 24, 31)) and os.path.exists(SHs.record_path(sbA, 24, 32)))
rc, cert, _ = world("censored_dup", unprod={55: CENS})
check("a censored DUPLICATE (status absent, named in env/censored.txt) is reported and not compared: RELEASE with R1' 19 compared",
      cert["outcome"] == "RELEASE" and cert["parts"]["R1"]["compared"] == 19 and cert["parts"]["R1"]["unproduced"] == [[24, 3]]
      and cert["unproduced"][0]["kind"] == "censored" and cert["unproduced"][0]["role"] == "qual_lengau", cert["problems"][:2])
rc, cert, _ = world("resume_bad", unprod={30: 75}, status_for={30: dict(exit=4, reason="memory: maxrss above the stop")})
check("a RESUME outcome whose status is a HELD exit 4 / memory reason -> NO_RELEASE", no_release("", cert, "orderly LEFT"), cert["problems"][:2])

# 4 coverage
six = {(24, 0), (24, 1), (24, 2), (24, 3), (24, 4), (24, 5)}
rc, cert, _ = world("coverage", failed_dups=six)
check("6 agreeing failed duplicates leave 14 finite successful (< 15): INCONCLUSIVE, never RELEASE",
      rc == 3 and cert["outcome"] == "INCONCLUSIVE" and cert["coverage_short"] == {"R1": 14} and cert["parts"]["R1"]["failed_both"] == 6 and cert["released_attempts"] == [],
      (cert["outcome"], cert["coverage_short"], cert["problems"][:2]))

# 5 input refusals
rc, cert, _ = world("not_panel", att_edit=lambda a: a.update(coordinates=a["coordinates"][1:] + [[24, 63]]))
check("an attempt whose work is not exactly the declared panel -> NO_RELEASE", no_release("", cert, "not exactly the declared panel"), cert["problems"][:2])
rc, cert, _ = world("panel_tamper", panel_edit=lambda p: p["work"].__setitem__(0, [24, 70]))
check("a tampered panel file (one work coordinate changed) -> NO_RELEASE", no_release("", cert, "panel:"), cert["problems"][:2])
rc, cert, _ = world("op_lifetime", op_lifetime=70000)
check("an E2Q operational manifest at another lifetime -> NO_RELEASE", no_release("", cert, "qualified operational manifest"), cert["problems"][:2])
rc, cert, _ = world("e1_partition", use_e1=True)
check("an epoch-1 (schema-1) partition cannot be qualified by the epoch-2 command -> NO_RELEASE", no_release("", cert, "schema-2 epoch-2"), cert["problems"][:2])
rc, cert, _ = world("fund_wrong", fund_edit=dict(lifetime_s=75300))
check("a funding declaration not at the funded lifetime -> NO_RELEASE", no_release("", cert, "funding:"), cert["problems"][:2])
rc, cert, _ = world("sentinel_dup", att_edit=lambda a: a.update(sentinels=[[24, 0], [3, 1], [3, 2], [3, 3]]))
check("a sentinel among the duplicates -> NO_RELEASE", no_release("", cert, "sentinels outside the duplicates"), cert["problems"][:2])

# 6 REVISION 6 (B2): impossible or duplicated resource observations; the relocated snapshot layout
GIB_KB = 2 ** 20
TOT = 192 * GIB_KB
def mem_lines(rows):
    return "".join(" ".join(str(x) for x in r) + "\n" for r in rows)
OCC12 = "".join(f"{60 * t} 76 70.0 70.0 70.0\n" for t in range(12))
rc, cert, _ = world("b2_counter_193", mem_text=mem_lines([(60 * t, TOT, 193 * GIB_KB, 76 * 2_300_000) for t in range(12)]))
check("B2 counter (the review's case): 12 full-packing samples with MemTotal 192 GiB and MemAvailable 193 GiB -> NO_RELEASE, return 3, "
      "the impossible observation named (was RELEASE / peak 0.0)",
      rc == 3 and cert["outcome"] == "NO_RELEASE" and cert["released_attempts"] == [] and no_release("", cert, "physically impossible")
      and cert["memory"]["valid"] is False, (rc, cert["outcome"], cert["problems"][:2]))
rc, cert, _ = world("b2_dup_ts", mem_text=mem_lines([(0, TOT, TOT - 150 * GIB_KB, 1)] * 12), occ_text="0 76 70.0 70.0 70.0\n" * 12)
check("B2 counter: 12 copies of ONE timestamp (memory and occupancy) are not 12 producer samples -> NO_RELEASE",
      rc == 3 and no_release("", cert, "time repeats"), cert["problems"][:2])
rc, cert, _ = world("b2_amplified", occ_text="0 76 70.0 70.0 70.0\n")
check("B2 counter: ONE occupancy line cannot be joined to 12 memory samples (one sample counted, < 10) -> NO_RELEASE",
      rc == 3 and no_release("", cert, "memory gate: 1 samples at the full 76-worker"), cert["problems"][:2])
rc, cert, _ = world("b2_valid_control", mem_text=mem_lines([(60 * t, TOT, TOT - 150 * GIB_KB, 76 * 2_300_000) for t in range(12)]), occ_text=OCC12)
check("B2 positive control: 12 distinct valid samples at 150 GiB -> RELEASE (the gate is not merely closed)",
      rc == 0 and cert["outcome"] == "RELEASE" and cert["memory"]["samples_at_full_packing"] == 12 and abs(cert["memory"]["peak_host_used_gib"] - 150.0) < 1e-9,
      cert["problems"][:2])
pd = os.path.join(scratch, "b2_parser"); os.makedirs(os.path.join(pd, "env"))
def parse(mem_rows=None, occ=OCC12, mem_raw=None):
    open(os.path.join(pd, "env", "memory.txt"), "w").write(mem_raw if mem_raw is not None else mem_lines(mem_rows))
    open(os.path.join(pd, "env", "occupancy.txt"), "w").write(occ)
    probs = []
    try:
        m = QU.memory(pd, probs, 76, label="E2Q1")
    except Exception as e:                                          # must never happen: a failed verdict, not an exception
        return "raised", f"{type(e).__name__}: {e}", None
    return ("refused" if probs else "accepted"), probs, m
good = [(60 * t, TOT, TOT - 150 * GIB_KB, 76 * 2_300_000) for t in range(12)]
v, p, m = parse(good)
check("B2 parser: valid distinct samples are accepted (12 at full packing, peak 150 GiB)", v == "accepted" and m["samples_at_full_packing"] == 12, p)
NEG = [("zero MemTotal", [(r[0], 0, 0, r[3]) for r in good], None, OCC12),
       ("negative MemTotal", None, "".join(f"{60 * t} -5 0 1\n" for t in range(12)), OCC12),
       ("negative MemAvailable", None, "".join(f"{60 * t} {TOT} -1 1\n" for t in range(12)), OCC12),
       ("MemAvailable above MemTotal", [(r[0], TOT, TOT + 1, r[3]) for r in good], None, OCC12),
       ("negative worker RSS", None, "".join(f"{60 * t} {TOT} {TOT - 150 * GIB_KB} -7\n" for t in range(12)), OCC12),
       ("non-integer MemAvailable (decimal)", None, "".join(f"{60 * t} {TOT} 1.5 1\n" for t in range(12)), OCC12),
       ("non-integer MemAvailable (text)", None, "".join(f"{60 * t} {TOT} abc 1\n" for t in range(12)), OCC12),
       ("non-integer timestamp", None, "".join(f"{60 * t}.5 {TOT} {TOT - GIB_KB} 1\n" for t in range(12)), OCC12),
       ("12 copies of one timestamp", [(0, TOT, TOT - 150 * GIB_KB, 1)] * 12, None, OCC12),
       ("a backward timestamp", [(0, TOT, TOT - GIB_KB, 1), (120, TOT, TOT - GIB_KB, 1), (60, TOT, TOT - GIB_KB, 1)], None, OCC12),
       ("occupancy above the 76 planned workers", good, None, "".join(f"{60 * t} 77 70.0 70.0 70.0\n" for t in range(12))),
       ("negative occupancy", good, None, "".join(f"{60 * t} -1 70.0 70.0 70.0\n" for t in range(12))),
       ("a non-finite load average", good, None, "".join(f"{60 * t} 76 nan 70.0 70.0\n" for t in range(12))),
       ("a wrong memory field count", None, "".join(f"{60 * t} {TOT} {TOT}\n" for t in range(12)), OCC12),
       ("a duplicated occupancy timestamp", good, None, OCC12 + "660 76 70.0 70.0 70.0\n")]
for name, rows, raw, occ in NEG:
    v, p, m = parse(rows, occ, raw)
    check(f"B2 parser negative: {name} -> a failed evidence verdict (a problem), never an exception or a release", v == "refused", (v, p))
rc, cert, w = world("snap_relocated_absent", relocate="absent")
check("snapshot: the reviewed panel's recorded snapshot path is absent in the deployed tree; without --snapshot the qualifier refuses",
      rc == 3 and no_release("", cert, "panel:") and any("unreadable" in p_ for p_ in cert["problems"]), cert["problems"][:2])
rc, cert, w = world("snap_relocated", relocate="deployed")
check("snapshot: with the deployed copy passed by --snapshot (hash-checked against the partition) the same panel bytes RELEASE, "
      "binding the snapshot sha256; the panel still records its source path (not edited)",
      rc == 0 and cert["outcome"] == "RELEASE" and cert["bound"]["claims_snapshot_sha256"] == w["snap_sha"]
      and json.load(open(w["panp"]))["claims_snapshot"]["path"].endswith(os.path.join("source_evidence", "e2_final", "claims_snapshot_e2.json"))
      and not os.path.exists(json.load(open(w["panp"]))["claims_snapshot"]["path"]), cert["problems"][:2])
rc, cert, w = world("snap_relocated_tampered", relocate="tampered")
check("snapshot: a --snapshot copy whose bytes are not the partition-bound 31cc268f-style digest refuses",
      rc == 3 and no_release("", cert, "not the one the partition is bound to"), cert["problems"][:2])

shutil.rmtree(scratch, ignore_errors=True)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
