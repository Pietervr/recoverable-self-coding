"""EC2 provider epoch 2 CANDIDATE (NOT adopted): the RELEASED E2Q1/E2Q2 per-slot ingestion route (chpc/candidate_e2/
row19_ec2_ingest.py REVISION 8) and the choice-3 crash ruling (chpc/candidate_e2q/aws_ec2/prod_authority.py REVISION 8), for
Codex's review reviews/2026-10-19_e2_adoption_codex_review.md B1. STUB mode on the Mac exactly as candidate_e2/test_e2_ingest.py
and test_e2q_qualify.py: synthetic records with the frozen-task check stubbed, everything else the real candidate modules
(partition, ingestion, shared rules, the state module carrying the E2Q contracts, the Mac authority). No fits, no Lengau, no AWS;
every root, bundle and ledger is in a temporary directory.

The world: a sandbox screen root under an ACTIVATED schema-2 epoch 2 (predecessor e1 activated first) declared from a claims
snapshot whose Lengau-completed coordinates are rep 24: 0-8, rep 25: 0-5, 7, 8, rep 28: 0-2 and rep 3: 0-11 (rep 24 indices
9-10 planned), so an E2Q1 plan is 52 owned work (rep 24 indices 11..62) + 20 duplicates + 4 sentinels (rep 3).

  1. publication: a RELEASED E2Q1 (and E2Q2) with qualifying non-completions publishes the produced work, lists the unproduced
     work, raises the fence there, journals the failure evidence and keeps its real class (cls "qualification"); the REAL Mac
     `ack` releases exactly published + unproduced = the 52 owned coordinates;
  2. holding: the UNRELEASED cases; schema 1 and another qualification contract (epoch-1 Q1) stay all-or-nothing; the
     qualifying-kind rules (exit 4, present-null status, leftover output, missing work output, a duplicate of no qualifying
     kind, deficient sentinels, a sentinel or duplicate difference with ec2/HOLD); R4' - at most 3 non-completions of ALL
     roles - holds a 4th even where production's 7-work-slot bound would not;
  3. interruption and replay: a forced stop leaves 'ingesting', the replay completes, a second replay re-validates; changed
     failure evidence on completion or on replay HOLDS and writes ec2/HOLD;
  4. choice 3: an acknowledged fatal UNPRODUCED E2Q work slot and an acknowledged production crash of the same coordinate in the
     same physical envelope exclude it (mixed qualification-ACK / production-ACK allocation test, both real ingestions and real
     ACKs); different-envelope controls (lifetime, instance type, producer geometry, an epoch-1 Q1 contract) and the
     non-counting outcomes (duplicates/sentinels, censored, dispositioned) do not.

    python3 chpc/candidate_e2q/test_e2q_ingest.py              (from workspace_demo/t1_access)"""
import copy, glob, hashlib, importlib.util, json, os, shutil, sys, tempfile, time, types

Q = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(Q); T1 = os.path.dirname(CHPC); E2 = os.path.join(CHPC, "candidate_e2")
for p in (T1, os.path.join(T1, "aws_ec2"), CHPC, E2, Q):
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


ES = load_mod("row19_ec2_state", os.path.join(Q, "row19_ec2_state.py"))                 # the E2Q contracts
E2R = load_mod("row19_ec2_e2rules", os.path.join(E2, "row19_ec2_e2rules.py"))
RP = load_mod("row19_partition", os.path.join(E2, "row19_partition.py"))
IG = load_mod("row19_ec2_ingest", os.path.join(E2, "row19_ec2_ingest.py"))               # REVISION 8
EQ = load_mod("row19_ec2_e2qual", os.path.join(Q, "row19_ec2_e2qual.py"))
PA = load_mod("prod_authority", os.path.join(Q, "aws_ec2", "prod_authority.py"))          # REVISION 8
import bench_launch as L
IG.ACTIVATION_MODE = "sandbox"
PROD = json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))
DESIG = json.load(open(os.path.join(CHPC, "row19_screen_designated.json")))
CENS = E2R.CENSORED
LENGAU_DONE = [(24, i) for i in range(9)] + [(25, i) for i in (0, 1, 2, 3, 4, 5, 7, 8)] + [(28, i) for i in (0, 1, 2)] + [(3, i) for i in range(12)]
EC2_DUPS = [(24, i) for i in range(9)] + [(25, i) for i in (0, 1, 2, 3, 4, 5, 7, 8)] + [(28, i) for i in (0, 1, 2)]
SENT = [(3, 0), (3, 1), (3, 2), (3, 3)]
STATUS0 = dict(exit=0, reason="", left=[], resumed=[], wall_s=70000.0, cpu_s=69000.0, started=1.0, ended=70001.0, maxrss=2_400_000_000, host="ip-10-0-0-1")
DEADLINE = "deadline: 120 s left, 900 s needed for the next resample"
scratch = tempfile.mkdtemp()


def rec(r, i, delta=0.0):
    d = dict(rep=i, ident=f"ident{r}", stats={"ws": {"ws": 0.01 * r + i + delta}}, failed=False, failed_reason="")
    return dict(d, sha=_rsha(d))


def timing(r, i, job, slot):
    return dict(rep=r, index=i, ident=f"ident{r}", fit_seconds=60000.0, wall_s=70000.0, failed=False, maxrss=2_400_000_000, t=1.0, job=job, slot=slot, host="h")


def put(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, "w"))


def roles_for(contract):
    """(work, duplicates, sentinels) of a plan of `contract` in this world."""
    if contract in ("E2Q1", "E2Q2"):
        return [(24, i) for i in range(11, 63)], list(EC2_DUPS), list(SENT)
    if contract == "Q1":                                            # epoch-1 qualification geometry: 48 work + 24 duplicates + 4
        return [(24, i) for i in range(11, 59)], list(EC2_DUPS) + [(3, i) for i in range(4, 8)], list(SENT)
    if contract == "production":                                    # 72 owned work: rep 24 11..62, rep 25 6 and 9..27
        return [(24, i) for i in range(11, 63)] + [(25, 6)] + [(25, i) for i in range(9, 28)], [], list(SENT)
    raise ValueError(contract)


def build(case, contract="E2Q1", cls="qualification", released=True, unprod=None, status_for=None, raw_status=None, leave=(),
          use_e1=False, aid=None, key=None, seq=11, run=None, dup_delta=None, sent_delta=None, censored_names=None):
    """A sandbox root under an activated schema-2 epoch 2 (or, use_e1, the schema-1 epoch 1 pinned last) and one bundle of
    `contract`. `unprod` {slot: outcome}; `leave` the unproduced slots that nevertheless left their record/timing/status."""
    unprod = unprod or {}
    run = run or ("prod-e2" if contract == "production" else EQ.RUNS.get(contract, f"qual-{contract}"))
    aid = aid or f"ec2-{run}-a1"; key = key or f"{run}/1"
    d = os.path.join(scratch, case); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    root, camp = os.path.join(d, "root"), os.path.join(d, "camp"); os.makedirs(os.path.join(root, "plans")); os.makedirs(camp)
    for r, i in LENGAU_DONE:
        put(SHs.record_path(root, r, i), rec(r, i)); put(SHs.timing_path(root, r, i), timing(r, i, "7523818.sched01", 0))
    put(os.path.join(root, "plans", "job_1.json"), {"job": 1, "slots": [{"slot": 0, "rep": 24, "indices": [9]}, {"slot": 1, "rep": 24, "indices": [10]}]})
    put(os.path.join(camp, "budget.json"), {"entries": {"t": {"kind": "shard", "rep": 1, "state": "settled", "job_id": "1.s"}}})
    man = copy.deepcopy(PROD); man["storage"] = {"root": root, "campaign": camp}
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w")); msha = sha(mp)
    dp = os.path.join(d, "designated.json"); json.dump(dict(DESIG, manifest_sha256=msha), open(dp, "w")); RP.DESIGNATED_PATH = dp
    e1 = RP.declare(man, msha, 40, 1); e1p = os.path.join(d, "e1.json"); json.dump(e1, open(e1p, "w"))
    cp = os.path.join(d, "controls.json"); IG.CONTROLS = cp
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
    epoch = 1 if use_e1 else 2
    psel = e1p if use_e1 else pp
    opm = ES.derive_operational(man, msha, epoch, 75300, contract); opp = os.path.join(d, "op.json"); json.dump(opm, open(opp, "w")); opsha = sha(opp)
    work, dups, sent = roles_for(contract)
    b = os.path.join(d, "bundle"); broot = os.path.join(b, "root"); env = os.path.join(b, "env"); os.makedirs(env)
    roles = [("work", c) for c in work] + [("qual_lengau", c) for c in dups] + [("sentinel", c) for c in sent]
    slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in enumerate(roles)]
    for s in slots:
        r, i, sl = s["rep"], s["indices"][0], s["slot"]
        stp = os.path.join(broot, "status", f"job{aid}.slot{sl}.json")
        if sl in unprod and sl not in leave:
            if sl in (status_for or {}):
                st = dict(STATUS0, job=aid, slot=sl, rep=r, ident=f"ident{r}", indices=[i], new=[], left=[i]); st.update(status_for[sl]); put(stp, st)
            elif sl in (raw_status or {}):
                os.makedirs(os.path.dirname(stp), exist_ok=True); open(stp, "w").write(raw_status[sl])
            continue
        delta = (dup_delta or {}).get((r, i), 0.0) + (sent_delta or {}).get((r, i), 0.0)
        put(SHs.record_path(broot, r, i), rec(r, i, delta)); put(SHs.timing_path(broot, r, i), timing(r, i, aid, sl))
        put(stp, dict(STATUS0, job=aid, slot=sl, rep=r, ident=f"ident{r}", indices=[i], new=[i]))
    for r in sorted({s["rep"] for s in slots}):
        json.dump(dict(binding=SHs.binding_for(opm, opsha, "/mnt/prod/root", r, SHs.task(PROD, r))), open(os.path.join(broot, f"task_{r}.json"), "w"), default=str)
    plan = dict(job=1, attempt_id=aid, sequence=seq, epoch=epoch, contract=contract, partition_sha256=sha(psel), opmanifest_sha256=opsha,
                activation_sha256=sha(RP.activation_path(man, epoch)), slots=slots)
    put(os.path.join(env, "plan.json"), plan)
    put(os.path.join(env, "upload_verify.json"), dict(transfer_verified=True))
    put(os.path.join(env, "attest_B.json"), dict(profile="B_full", problems=[], XLA_FLAGS=ES.XLA_BASE + " --xla_cpu_max_isa=AVX2", OPENBLAS_CORETYPE="Haswell",
                                                 threads={k: "1" for k in ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
                                                 numpy_dispatch_active=["X86_V2", "X86_V3"], openblas_core={"libscipy_openblas.so": "Haswell"}))
    oc = {f"w_slot{s['slot']}": unprod.get(s["slot"], 0) for s in slots}
    put(os.path.join(env, "outcomes.json"), dict(declared=len(slots), outcomes=oc, unresolved_after_kill=[]))
    names = sorted(k for k, v in oc.items() if v == CENS) if censored_names is None else censored_names
    open(os.path.join(env, "censored.txt"), "w").write("".join(f"{n}\n" for n in names))
    resum(b)
    att = dict(key=key, run=run, attempt=1, attempt_id=aid, sequence=seq, state="reconciled", ingestion="pending", contract=contract,
               disposition_requested=False, plan_sha256=sha(os.path.join(env, "plan.json")), coordinates=[list(c) for c in work],
               sentinels=[list(c) for c in sent], duplicates=[list(c) for c in dups], charged_usd=26.0, **{"class": cls})
    owners = {f"{c[0]}/{c[1]}": [key, seq] for c in sorted(work)}
    inv = ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=3, at=time.time(), attempts={key: att}, owners=owners,
                       fence={k: seq for k in owners}, release=dict(production_released=bool(released), released_attempts=[key] if released else []), usd={}))
    ip = os.path.join(d, "inventory.json"); json.dump(inv, open(ip, "w"))
    ES.install_inventory(root, inv, ident)
    return dict(d=d, root=root, mp=mp, pp=psel, opp=opp, ip=ip, b=b, e2=e2, key=key, aid=aid, seq=seq, run=run, contract=contract,
                plan_sha256=att["plan_sha256"], work=work, dups=dups, sent=sent, slots=slots, cp=cp, dp=dp)


def resum(b):
    lines = [f"{sha(p)}  {os.path.relpath(p, b)}\n" for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True))
             if os.path.isfile(p) and os.path.relpath(p, b) not in ("env/upload_verify.json", "BUNDLE_SHA256SUMS")]
    open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))


def ingest(c):
    IG.CONTROLS = c["cp"]; RP.DESIGNATED_PATH = c["dp"]
    return IG.main(["--manifest", c["mp"], "--partition", c["pp"], "--opmanifest", c["opp"], "--authority", c["ip"], "--attempt-key", c["key"], "--bundle", c["b"]])


def entry(c):
    p = os.path.join(c["root"], "ec2", "register.json")
    reg = json.load(open(p)) if os.path.exists(p) else None
    return ((reg or {}).get("attempts") or {}).get(c["aid"]), reg


def held_file(c):
    return os.path.exists(ES.paths(c["root"])["hold"])


def published(c, r, i):
    return os.path.exists(SHs.record_path(c["root"], r, i))


def held(c, rc):
    return rc == 3 and entry(c)[0] is None and not any(published(c, *w) for w in c["work"])


W0 = 0                                       # slot 0 = work (24, 11); slot 20 = work (24, 31); slots 52..71 duplicates; 72..75 sentinels
DUP0, SENT0 = 52, 72

# ---- 1. publication of a released E2Q1 / E2Q2, real class kept, exact ACK ---------------------------------------------------------
c = build("e2q1_complete"); rc = ingest(c); e, R = entry(c)
check("released E2Q1, complete: 52 work coordinates published, 20 duplicates + 4 sentinels compared equal, unproduced {}, class kept",
      rc == 0 and e["state"] == "ingested" and len(e["coordinates"]) == 52 and e["unproduced"] == {} and len(e["compared_equal"]) == 24
      and e["cls"] == "qualification" and e["contract"] == "E2Q1", (rc, e and e.get("cls")))
c = build("e2q1_crash", unprod={20: 139}); rc = ingest(c); e, R = entry(c)
check("released E2Q1 with one crashed WORK slot (139, no status, no output): 51 published, the coordinate listed unproduced with its exit",
      rc == 0 and e["state"] == "ingested" and len(e["coordinates"]) == 51 and e["unproduced"] == {"24/31": {"slot": 20, "outcome": 139}}
      and not published(c, 24, 31) and published(c, 24, 32))
check("... its real class 'qualification' is kept in the register; the failure evidence is journaled; the fence is raised at the unproduced coordinate",
      e["cls"] == "qualification" and set(e["failure_evidence"]) == {"bundle_sums_sha256", "outcomes_sha256", "censored_sha256", "unproduced_status", "unproduced"}
      and e["failure_evidence"]["unproduced_status"] == {"20": None} and R["fence"].get("24/31") == c["seq"])
check("... a replay of the ingested entry re-validates", ingest(c) == 0)
TMP = tempfile.mkdtemp(); L.HERE = PA.HERE = TMP


def ledger_att(cx, **kw):
    a = dict(attempt=1, sequence=cx["seq"], attempt_id=cx["aid"], state="reconciled", ingestion="pending", contract=cx["contract"],
             plan_sha256=cx["plan_sha256"], coordinates=[list(w) for w in cx["work"]], sentinels=[list(s) for s in cx["sent"]],
             duplicates=[list(x) for x in cx["dups"]], lifetime_s=79200, max_price=1.2, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD,
             type="c7a.24xlarge", terminal=dict(compute_s=3600, ancillary_s=3600))
    a.update(kw); return a


L.save("qual-E2Q1", {"run": "qual-E2Q1", "attempts": [ledger_att(c)]})
regp = os.path.join(c["root"], "ec2", "register.json")
bad = json.load(open(regp)); bad["attempts"][c["aid"]]["unproduced"] = {}; bp = os.path.join(TMP, "bad_register.json"); json.dump(bad, open(bp, "w"))
try:
    PA.ack("qual-E2Q1", 1, bp); ok_ = False
except ValueError:
    ok_ = True
check("Mac ack refuses the E2Q1 register entry when published + unproduced miss one owned coordinate (exact accounting)", ok_)
check("Mac ack (REAL prod_authority.ack) releases the released E2Q1 attempt: published 51 + unproduced 1 = the 52 owned coordinates; the exit is recorded",
      PA.ack("qual-E2Q1", 1, regp) is True and L.load("qual-E2Q1")["attempts"][0]["ingest_ack"]["unproduced"] == {"24/31": {"slot": 20, "outcome": 139}}
      and PA.owned(PA.ledgers()) == {} and PA.ack("qual-E2Q1", 1, regp) is False)
check("... the acknowledged E2Q1 crash enters the crash history under the normalised production envelope",
      PA.ec2_crash_history(PA.ledgers())[(24, 31)] == [dict(attempt="qual-E2Q1/1", exit=139, contract="E2Q1", envelope=["production", "c7a.24xlarge", 79200])])
shutil.rmtree(TMP)
c = build("e2q2_censored_dup", contract="E2Q2", unprod={DUP0 + 3: CENS}); rc = ingest(c); e, _ = entry(c)
check("released E2Q2 with a censored DUPLICATE (status absent, named in env/censored.txt): all 52 work published, the duplicate not compared, unproduced work {}",
      rc == 0 and len(e["coordinates"]) == 52 and e["unproduced"] == {} and len(e["compared_equal"]) == 23 and e["cls"] == "qualification" and e["contract"] == "E2Q2")
c = build("e2q1_resume", unprod={5: 75}, status_for={5: dict(exit=75, reason=DEADLINE)}); rc = ingest(c); e, _ = entry(c)
check("released E2Q1 with the worker's own RESUME 75 and an orderly deadline LEFT status: unproduced, the rest published",
      rc == 0 and e["unproduced"] == {"24/16": {"slot": 5, "outcome": 75}} and len(e["coordinates"]) == 51)
c = build("e2q1_three", unprod={0: 139, DUP0: 137, SENT0: CENS}); rc = ingest(c); e, _ = entry(c)
check("R4': exactly 3 non-completions of all roles (work 139, duplicate 137, sentinel censored) still publish (51 work, 3 sentinels compared)",
      rc == 0 and len(e["coordinates"]) == 51 and e["unproduced"] == {"24/11": {"slot": 0, "outcome": 139}} and len(e["compared_equal"]) == 22)

# ---- 2. holding --------------------------------------------------------------------------------------------------------------------
c = build("e2q1_four", unprod={0: 139, 1: 139, 2: 139, 3: 139}); rc = ingest(c)
check("R4': a 4th non-completion HOLDS the released E2Q1 (4 work slots, inside production's 7-work bound: the qualification-wide 3 applies)",
      held(c, rc) and IG.MAX_UNPRODUCED_WORK == 7)
c = build("e2q1_four_mixed", unprod={0: 139, DUP0: 139, DUP0 + 1: 139, SENT0: 139}); rc = ingest(c)
check("R4': 4 non-completions across roles (1 work, 2 duplicates, 1 sentinel) HOLD", held(c, rc))
c = build("unreleased_partial", released=False, unprod={20: 139}); rc = ingest(c)
check("an UNRELEASED E2Q1 with a qualifying non-completion HOLDS (qualification output never enters the root before release)", held(c, rc))
c = build("unreleased_complete", released=False); rc = ingest(c)
check("an UNRELEASED complete E2Q1 HOLDS too", held(c, rc))
c = build("q1_released_partial", contract="Q1", unprod={20: 139}); rc = ingest(c)
check("another qualification contract (epoch-1 Q1 geometry), RELEASED, under schema 2: all-or-nothing - one crashed slot HOLDS", held(c, rc))
c = build("q1_released_complete", contract="Q1"); rc = ingest(c); e, _ = entry(c)
check("... positive control: the same released Q1-contract attempt, complete, ingests (the hold above is the all-or-nothing gate)",
      rc == 0 and e["state"] == "ingested" and "unproduced" not in e)
c = build("schema1_partial", use_e1=True, unprod={20: 139}); rc = ingest(c)
check("schema 1: a released E2Q1 under an epoch-1 (schema-1) partition stays all-or-nothing - one crashed slot HOLDS", held(c, rc))
c = build("schema1_complete", use_e1=True); rc = ingest(c); e, _ = entry(c)
check("... positive control: complete under schema 1 it ingests all-or-nothing (no unproduced map)", rc == 0 and e["state"] == "ingested" and "unproduced" not in e)
c = build("held4", unprod={20: 4}, status_for={20: dict(exit=4, reason="memory: maxrss above the stop")}); rc = ingest(c)
check("exit 4 (the worker's HELD guard) HOLDS the released E2Q1", held(c, rc))
c = build("null_status", unprod={20: 139}, raw_status={20: "null\n"}); rc = ingest(c)
check("a present-null status of a crashed slot HOLDS (never 'no status')", held(c, rc))
c = build("leftover", unprod={20: 139}, leave={20}); rc = ingest(c)
check("leftover output (record/timing/status) beside a nonzero outcome HOLDS (ambiguous)", held(c, rc))
c = build("missing_work", unprod={}); os.remove(SHs.record_path(os.path.join(c["b"], "root"), 24, 31)); resum(c["b"]); rc = ingest(c)
check("missing work output under outcome 0 HOLDS (a produced slot must be a complete unit)", held(c, rc))
c = build("dup_exit1", unprod={DUP0 + 2: 1}); rc = ingest(c)
check("a duplicate of no qualifying kind (exit 1) HOLDS", held(c, rc))
c = build("sentinels_two", unprod={SENT0: 139, SENT0 + 1: 139}); rc = ingest(c)
check("deficient sentinels (2 produced < 3) HOLD", held(c, rc))
c = build("sentinel_diff", sent_delta={SENT[1]: 1e-12}); rc = ingest(c)
check("a produced sentinel differing from Lengau HOLDS and writes ec2/HOLD", rc == 3 and entry(c)[0] is None and held_file(c))
c = build("dup_diff", dup_delta={(25, 3): 1e-12}); rc = ingest(c)
check("a produced duplicate differing from Lengau HOLDS and writes ec2/HOLD", rc == 3 and entry(c)[0] is None and held_file(c))
c = build("cens_unbound", unprod={20: CENS}, censored_names=[]); rc = ingest(c)
check("a censored outcome that env/censored.txt does not name HOLDS", held(c, rc))

# ---- 3. interruption, replay, changed failure evidence ------------------------------------------------------------------------------
real_pub, calls = IG.publish_copy, [0]


def stop_after_first(src, dst, want):
    calls[0] += 1
    if calls[0] > 1:
        raise ValueError("forced stop")
    return real_pub(src, dst, want)


c = build("int_ok", unprod={20: 139}); calls[0] = 0
IG.publish_copy = stop_after_first; rc1 = ingest(c); IG.publish_copy = real_pub
st1 = entry(c)[0]["state"]; rc2 = ingest(c); rc3 = ingest(c)
check("interruption: a forced stop leaves 'ingesting'; the replay completes 'ingested'; a second replay re-validates (released E2Q1)",
      rc1 == 3 and st1 == "ingesting" and rc2 == 0 and rc3 == 0 and entry(c)[0]["state"] == "ingested" and entry(c)[0]["cls"] == "qualification")
c = build("int_changed", unprod={20: 139}); calls[0] = 0
IG.publish_copy = stop_after_first; ingest(c); IG.publish_copy = real_pub
op = os.path.join(c["b"], "env", "outcomes.json"); o = json.load(open(op)); o["outcomes"]["w_slot20"] = 137; json.dump(o, open(op, "w")); resum(c["b"])
rc = ingest(c)
check("changed failure evidence on completion (139 -> 137, checksums regenerated) HOLDS, ec2/HOLD written, the entry stays 'ingesting'",
      rc == 3 and held_file(c) and entry(c)[0]["state"] == "ingesting")
c = build("replay_changed", unprod={20: 139}); ingest(c)
op = os.path.join(c["b"], "env", "outcomes.json"); o = json.load(open(op)); o["outcomes"]["w_slot20"] = CENS; json.dump(o, open(op, "w"))
open(os.path.join(c["b"], "env", "censored.txt"), "w").write("w_slot20\n"); resum(c["b"])
check("changed failure evidence on replay of an ingested E2Q1 (139 rewritten to the censor marker) HOLDS and writes ec2/HOLD", ingest(c) == 3 and held_file(c))

# ---- 4. choice 3: one physical envelope for production and released E2Q owned work -------------------------------------------------
TMP = tempfile.mkdtemp(); L.HERE = PA.HERE = TMP
cq = build("mix_e2q1", unprod={20: 139}, seq=21); rq = ingest(cq)
cp_ = build("mix_prod", contract="production", cls="production", released=False, unprod={20: 137}, seq=22); rp = ingest(cp_)
check("mixed: the released E2Q1 (24/31 exit 139) and a production attempt (24/31 exit 137) both ingest with the coordinate unproduced",
      rq == 0 and rp == 0 and entry(cq)[0]["unproduced"] == {"24/31": {"slot": 20, "outcome": 139}}
      and entry(cp_)[0]["unproduced"] == {"24/31": {"slot": 20, "outcome": 137}}, (rq, rp))
L.save("qual-E2Q1", {"run": "qual-E2Q1", "attempts": [ledger_att(cq)]})
PA.ack("qual-E2Q1", 1, os.path.join(cq["root"], "ec2", "register.json"))
leds1 = PA.ledgers()
check("one acknowledged E2Q1 crash alone does not exclude: (24, 31) is allocated again to production",
      PA.ec2_crash_excluded(leds1) == set() and (24, 31) in PA.allocate(cq["e2"], leds1, set(), 72, PA.ec2_crash_excluded(leds1)))
L.save("prod-e2", {"run": "prod-e2", "attempts": [ledger_att(cp_)]})
PA.ack("prod-e2", 1, os.path.join(cp_["root"], "ec2", "register.json"))
leds = PA.ledgers(); ex = PA.ec2_crash_excluded(leds)
check("mixed qualification-ACK + production-ACK in the same physical envelope (c7a.24xlarge, 76 workers, 60 GB, 79,200 s) exclude (24, 31)",
      ex == {(24, 31)} and [x["envelope"] for x in PA.ec2_crash_history(leds)[(24, 31)]] == [["production", "c7a.24xlarge", 79200]] * 2, ex)
alloc = PA.allocate(cq["e2"], leds, set(), 72, ex)
check("... the allocator never issues a third physically equivalent attempt at (24, 31); its neighbours stay allocatable",
      (24, 31) not in alloc and (24, 30) in alloc and (24, 32) in alloc)
check("... and the E2Q launcher's free-work check sees the same exclusion (build refuses a panel that includes it)",
      (24, 31) in PA.ec2_crash_excluded(leds, "E2Q1"))
old_hist = {}                                                   # REVISION 7's rule on the same ledgers: production runs only, contract label
for run_, l_ in leds.items():
    if PA.run_class(run_) != "production":
        continue
    for a_ in l_["attempts"]:
        for k_, u_ in ((a_.get("ingest_ack") or {}).get("unproduced") or {}).items():
            old_hist.setdefault(k_, []).append((u_["outcome"], [a_["contract"], a_["type"], a_["lifetime_s"]]))
check("counter-reference: REVISION 7's rule (production runs only, envelope keyed by contract name) on the SAME ledgers excludes nothing - "
      "the third physically equivalent attempt the review describes",
      [k_ for k_, xs in old_hist.items() if sum(1 for o_, e_ in xs if E2R.counts_toward_crash_rule(o_) and e_ == ["production", "c7a.24xlarge", 79200]) >= 2] == []
      and PA.crash_envelope("E2Q1", "c7a.24xlarge", 79200) == ["production", "c7a.24xlarge", 79200])


def excluded_with(edit_q=None, edit_p=None, q_run="qual-E2Q1"):
    lt = copy.deepcopy(leds)
    if edit_q:
        edit_q(lt["qual-E2Q1"]["attempts"][0])
    if edit_p:
        edit_p(lt["prod-e2"]["attempts"][0])
    if q_run != "qual-E2Q1":
        lt[q_run] = lt.pop("qual-E2Q1")
    return PA.ec2_crash_excluded(lt)


check("control: a different lifetime (E2Q1 at 75,300 s vs production 79,200 s) is another envelope - not excluded",
      excluded_with(edit_q=lambda a: a.update(lifetime_s=75300)) == set())
check("control: a different recorded instance type (production on c7a.48xlarge) is another envelope - not excluded",
      excluded_with(edit_p=lambda a: a.update(type="c7a.48xlarge")) == set())
real_contract = dict(ES.CONTRACTS["E2Q1"]); ES.CONTRACTS["E2Q1"] = dict(real_contract, workers=72)
check("control: a different producer geometry (E2Q1 with 72 workers per instance) keeps its own label - not excluded", excluded_with() == set())
ES.CONTRACTS["E2Q1"] = real_contract
check("control: an epoch-1 Q1 contract (run qual-Q1, the same geometry) is never normalised nor counted - not excluded",
      excluded_with(edit_q=lambda a: a.update(contract="Q1"), q_run="qual-Q1") == set())
check("control: a censored (deadline) E2Q1 work outcome does not count - not excluded",
      excluded_with(edit_q=lambda a: a["ingest_ack"]["unproduced"]["24/31"].update(outcome=CENS)) == set())
check("control: a dispositioned E2Q1 attempt (no acknowledged ingestion) does not count - not excluded",
      excluded_with(edit_q=lambda a: a.update(ingestion="dispositioned")) == set())
cd = build("dup_sent_crash", unprod={DUP0: 139, SENT0: 139}, seq=23); rd = ingest(cd)
check("duplicates and sentinels never enter the crash history: a released E2Q1 whose crashed slots are a duplicate and a sentinel acknowledges no unproduced work",
      rd == 0 and entry(cd)[0]["unproduced"] == {})
check("the shared fatal set is unchanged (129..159) and the counter still counts it alone",
      PA.FATAL_EXITS is E2R.FATAL_SIGNAL_EXITS and not E2R.counts_toward_crash_rule(75) and not E2R.counts_toward_crash_rule(CENS))
shutil.rmtree(TMP)

shutil.rmtree(scratch, ignore_errors=True)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
