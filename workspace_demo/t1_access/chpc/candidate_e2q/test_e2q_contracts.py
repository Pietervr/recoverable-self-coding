"""EC2 provider epoch 2 QUALIFICATION CANDIDATE (NOT adopted): the E2Q1 / E2Q2 contracts - the instance contracts
(chpc/candidate_e2q/row19_ec2_state.py REVISION 4), their operational manifests and the declared fixed panel produced by the
manifest builder (chpc/candidate_e2q/aws_ec2/make_prod_manifest.py REVISION 3, row19_ec2_e2qual.derive_panel), and the
launcher's E2Q plan (prod_launch.py REVISION 7, build). Pure python, no AWS, no Lengau; reads the candidate epoch-2
partition (87edfb9e), its claims snapshot and the production manifest; writes only to a temporary directory.

  1. the contracts regenerate BYTE-EQUAL from their inputs: both operational manifests and the panel fixture;
  2. the panel is the declaration of QUALIFICATION_E2.md s.2 on the 17 Oct candidate partition (52 work = rep 24 indices
     11..62 = the production allocator's first 52; 20 duplicates; 61 workers on rep 24) and binds its inputs;
  3. the maker and panel_problem refuse: a missing partition, another lifetime/contract/epoch, a different existing panel,
     every tampered field, a snapshot that is not the bound one, a partition whose panel cannot carry 61 on one replicate;
  4. the instance contracts and the unchanged plan contract accept exactly the E2Q plan shape;
  5. the launcher builds the E2Q plan only from the declared panel (free work, Lengau-completed duplicates, 4 token
     sentinels outside the duplicates, >= 61 on one replicate) and gates E2Q to epoch 2.

    python3 chpc/candidate_e2q/test_e2q_contracts.py          (from workspace_demo/t1_access)"""
import copy, hashlib, importlib.util, io, json, os, shutil, sys, tempfile, contextlib

Q = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(Q); T1 = os.path.dirname(CHPC); E2 = os.path.join(CHPC, "candidate_e2")
AWS = os.path.join(T1, "aws_ec2")
for p in (T1, AWS, CHPC, E2, Q, os.path.join(Q, "aws_ec2")):
    sys.path.insert(0, p)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


ES = load_mod("row19_ec2_state", os.path.join(Q, "row19_ec2_state.py"))
RP = load_mod("row19_partition", os.path.join(E2, "row19_partition.py"))
E2R = load_mod("row19_ec2_e2rules", os.path.join(E2, "row19_ec2_e2rules.py"))
EQ = load_mod("row19_ec2_e2qual", os.path.join(Q, "row19_ec2_e2qual.py"))
PA = load_mod("prod_authority", os.path.join(Q, "aws_ec2", "prod_authority.py"))
PL = load_mod("prod_launch", os.path.join(Q, "aws_ec2", "prod_launch.py"))
MK = load_mod("make_prod_manifest", os.path.join(Q, "aws_ec2", "make_prod_manifest.py"))
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json"); MAN = json.load(open(MAN_PATH))
PART_PATH = os.path.join(E2, "row19_partition_e2.json"); PSHA = sha(PART_PATH); PART = RP.load(PART_PATH, MAN, PA.PROD_SHA)
SNAP_PATH = os.path.join(E2, "claims_snapshot_e2.json"); SNAP = json.load(open(SNAP_PATH)); SSHA = sha(SNAP_PATH)
FIX = os.path.join(Q, "fixture", "panel_e2q_e2_candidate87ed.json"); PANEL = json.load(open(FIX))
OP1, OP2 = os.path.join(Q, "aws_ec2", "prod", "manifest_e2q1_e2.json"), os.path.join(Q, "aws_ec2", "prod", "manifest_e2q2_e2.json")
TMP = tempfile.mkdtemp()


def maker(*args):
    """Run the maker's main; returns ('OK', stdout) or ('REFUSED', message)."""
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            MK.main(list(args))
        return "OK", out.getvalue()
    except SystemExit as e:
        return "REFUSED", str(e)


# ---- 1. byte-equal regeneration ----------------------------------------------------------------------------------------------
r1 = maker("--epoch", "2", "--contract", "E2Q1", "--expect-s", "75300", "--out", os.path.join(TMP, "m1.json"), "--partition", PART_PATH,
           "--snapshot", SNAP_PATH, "--panel-out", os.path.join(TMP, "panel.json"))
r2 = maker("--epoch", "2", "--contract", "E2Q2", "--expect-s", "75300", "--out", os.path.join(TMP, "m2.json"), "--partition", PART_PATH,
           "--snapshot", SNAP_PATH, "--panel-out", os.path.join(TMP, "panel.json"))
check("the maker writes both E2Q operational manifests and the panel (the E2Q2 run re-derives and accepts the same panel)", r1[0] == "OK" and r2[0] == "OK", (r1, r2))
check("E2Q1 operational manifest regenerates BYTE-EQUAL to the committed prod/manifest_e2q1_e2.json", open(os.path.join(TMP, "m1.json"), "rb").read() == open(OP1, "rb").read())
check("E2Q2 operational manifest regenerates BYTE-EQUAL to the committed prod/manifest_e2q2_e2.json", open(os.path.join(TMP, "m2.json"), "rb").read() == open(OP2, "rb").read())
check("the panel regenerates BYTE-EQUAL to the committed candidate fixture (partition 87edfb9e)", open(os.path.join(TMP, "panel.json"), "rb").read() == open(FIX, "rb").read())
check("the operational manifests are the exact derivation (row19_ec2_state.operational_problem) at the funded 79,200 s lifetime",
      all(ES.operational_problem(json.load(open(p)), MAN, PA.PROD_SHA) == "" and json.load(open(p))["ec2_production"]["lifetime_s"] == 79200
          and json.load(open(p))["ec2_production"]["contract"] == c for p, c in ((OP1, "E2Q1"), (OP2, "E2Q2"))))
check("the operational manifests are the bytes row19_ec2_e2qual.opmanifest_bytes gives (what the release branch rederives)",
      open(OP1, "rb").read() == EQ.opmanifest_bytes(ES, MAN, PA.PROD_SHA, "E2Q1") and open(OP2, "rb").read() == EQ.opmanifest_bytes(ES, MAN, PA.PROD_SHA, "E2Q2"))
check("the operational manifests differ only in the contract name and its note (same geometry and roles)",
      {k: v for k, v in json.load(open(OP1)).items() if k not in ("ec2_production", "shard")} == {k: v for k, v in json.load(open(OP2)).items() if k not in ("ec2_production", "shard")}
      and json.load(open(OP1))["ec2_production"]["instance"] == json.load(open(OP2))["ec2_production"]["instance"])
check("NO final panel bytes are written at the production path (aws_ec2/prod/panel_e2q_e2.json): the final panel binds the final partition",
      not os.path.exists(os.path.join(AWS, "prod", "panel_e2q_e2.json")) and not os.path.exists(os.path.join(Q, "aws_ec2", "prod", "panel_e2q_e2.json")))

# ---- 2. the panel is the declaration ------------------------------------------------------------------------------------------
work = [tuple(c) for c in PANEL["work"]]; dups = [tuple(c) for c in PANEL["duplicates"]]
check("work = the first 52 owned coordinates in the production allocation order: rep 24 indices 11..62", work == [(24, i) for i in range(11, 63)])
check("... exactly what prod_authority.allocate gives the schema-2 partition with no ledger history (one rule, two consumers)",
      work == PA.allocate(PART, {}, set(), 52))
check("duplicates = the 20 lowest Lengau-completed designated coordinates of the EC2 replicates: rep 24 (0-8), 25 (0-5, 7, 8), 28 (0-2)",
      dups == [(24, i) for i in range(9)] + [(25, i) for i in (0, 1, 2, 3, 4, 5, 7, 8)] + [(28, i) for i in (0, 1, 2)])
check("the duplicates are Lengau-completed in the bound snapshot and never owned", set(dups) <= {tuple(c) for c in SNAP["lengau_done"]} and not any(RP.blocked(PART, *c) for c in dups))
check("61 workers on rep 24 (52 work + 9 duplicates) = QUALIFIED_REP_SLOTS", PANEL["concentration"]["max"] == 61 == E2R.QUALIFIED_REP_SLOTS and PANEL["concentration"]["max_reps"] == [24])
check("the panel binds the partition (sha256, owned digest) and the claims snapshot (path, sha256, claims digest)",
      PANEL["partition_sha256"] == PSHA and PANEL["owned_sha256"] == PART["owned_sha256"] and PANEL["claims_snapshot"] ==
      {"path": "chpc/candidate_e2/claims_snapshot_e2.json", "sha256": SSHA, "claims_sha256": SNAP["claims_sha256"]})
check("panel_problem accepts the fixture against its inputs", EQ.panel_problem(PANEL, PART, PSHA, SNAP, SSHA) == "")

# ---- 3. refusals --------------------------------------------------------------------------------------------------------------
r = maker("--epoch", "2", "--contract", "E2Q1", "--expect-s", "75300", "--out", os.path.join(TMP, "x1.json"))
check("the maker refuses an E2Q contract without --partition/--snapshot/--panel-out", r[0] == "REFUSED" and "--partition" in r[1] and not os.path.exists(os.path.join(TMP, "x1.json")))
r = maker("--epoch", "2", "--contract", "E2Q1", "--expect-s", "70000", "--out", os.path.join(TMP, "x2.json"), "--partition", PART_PATH,
          "--snapshot", SNAP_PATH, "--panel-out", os.path.join(TMP, "p2.json"))
check("the maker refuses another lifetime for an E2Q contract", r[0] == "REFUSED" and "75300" in r[1])
r = maker("--epoch", "3", "--contract", "E2Q1", "--expect-s", "75300", "--out", os.path.join(TMP, "x3.json"), "--partition", PART_PATH,
          "--snapshot", SNAP_PATH, "--panel-out", os.path.join(TMP, "p3.json"))
check("the maker refuses the E2Q contracts for any epoch but 2", r[0] == "REFUSED" and "epoch 2 only" in r[1])
r = maker("--epoch", "2", "--contract", "Q1", "--expect-s", "75300", "--out", os.path.join(TMP, "x4.json"))
check("the maker refuses the epoch-1 Q1 contract at epoch 2", r[0] == "REFUSED")
bad = os.path.join(TMP, "panel_other.json"); d_ = copy.deepcopy(PANEL); d_["work"][0] = [24, 70]; open(bad, "wb").write(EQ.panel_bytes(d_))
r = maker("--epoch", "2", "--contract", "E2Q1", "--expect-s", "75300", "--out", os.path.join(TMP, "x5.json"), "--partition", PART_PATH,
          "--snapshot", SNAP_PATH, "--panel-out", bad)
check("the maker never overwrites an existing different panel (immutable; regenerate with its partition)", r[0] == "REFUSED" and "immutable" in r[1]
      and not os.path.exists(os.path.join(TMP, "x5.json")))
r = maker("--epoch", "2", "--contract", "E2Q1", "--expect-s", "75300", "--out", os.path.join(TMP, "x6.json"), "--partition", PART_PATH,
          "--snapshot", os.path.join(CHPC, "row19_screen_manifest.json"), "--panel-out", os.path.join(TMP, "p6.json"))
check("the maker refuses a snapshot that is not the partition's bound claims snapshot", r[0] == "REFUSED")
for fld, mut in (("work", lambda p: p["work"].__setitem__(0, [24, 70])), ("duplicates", lambda p: p["duplicates"].__setitem__(0, [25, 6])),
                 ("partition_sha256", lambda p: p.update(partition_sha256="0" * 64)), ("concentration", lambda p: p["concentration"].update(max=62)),
                 ("roles", lambda p: p["roles"].update(work=51)), ("lifetime_s", lambda p: p.update(lifetime_s=75300)),
                 ("claims_snapshot.sha256", lambda p: p["claims_snapshot"].update(sha256="0" * 64)), ("extra field", lambda p: p.update(chosen="by outcome"))):
    d_ = copy.deepcopy(PANEL); mut(d_)
    check(f"panel_problem refuses a tampered panel ({fld})", EQ.panel_problem(d_, PART, PSHA, SNAP, SSHA) != "")
moved = os.path.join(TMP, "panel_moved.json"); d_ = copy.deepcopy(PANEL); d_["claims_snapshot"]["path"] = "chpc/no_such_snapshot.json"
open(moved, "wb").write(EQ.panel_bytes(d_))
try:
    PL.panel_for(PART, PSHA, moved); mv = ""
except (OSError, ValueError) as e:
    mv = type(e).__name__
check("the recorded snapshot path is where every consumer READS the snapshot (its bytes are checked against the partition's bound sha256): "
      "a panel pointing elsewhere refuses at the launcher", mv != "")
snap2 = copy.deepcopy(SNAP); snap2["lengau_done"] = [c for c in snap2["lengau_done"] if c != [24, 5]]
check("panel_problem refuses a claims snapshot that is not the one the partition binds", EQ.panel_problem(PANEL, PART, PSHA, snap2, "0" * 64) != "")
part2 = copy.deepcopy(PART); part2["claims_snapshot"] = dict(part2["claims_snapshot"], sha256="1" * 64, claims_sha256=snap2["claims_sha256"])
try:
    EQ.derive_panel(part2, "2" * 64, snap2, "1" * 64, "x"); low = ""
except ValueError as e:
    low = str(e)
check("a partition/snapshot on which the panel would carry only 60 on one replicate is REFUSED (re-declare before any outcome)",
      "below the qualified 61" in low, low)
try:
    EQ.derive_panel(json.load(open(os.path.join(CHPC, "row19_partition_e1.json"))), "3" * 64, SNAP, SSHA, "x"); e1 = ""
except ValueError as e:
    e1 = str(e)
check("the panel is never declared on the epoch-1 (schema-1) partition", "schema-2" in e1)

# ---- 4. instance contracts and the plan contract ------------------------------------------------------------------------------
check("E2Q1 and E2Q2: the production geometry (c7a.24xlarge, 76 workers, cap 1.20, 60 GB) with roles 52 work + 20 duplicates + 4 sentinels",
      all(ES.CONTRACTS[c] == dict(itype="c7a.24xlarge", workers=76, max_price=1.20, volume_gb=60, roles={"work": 52, "qual_lengau": 20, "sentinel": 4})
          for c in ("E2Q1", "E2Q2")) and {k: ES.CONTRACTS["production"][k] for k in ("itype", "workers", "max_price")} == dict(itype="c7a.24xlarge", workers=76, max_price=1.20))
check("the existing contracts are unchanged (production, Q1, Q2)", ES.CONTRACTS["Q1"]["roles"] == {"work": 48, "qual_lengau": 24, "sentinel": 4}
      and ES.CONTRACTS["Q2"] == dict(itype="c7a.12xlarge", workers=24, max_price=0.70, volume_gb=60, roles={"qual_repeat": 24})
      and ES.CONTRACTS["production"]["roles"] == {"work": None, "sentinel": 4})
SENT = [[3, 0], [3, 1], [4, 0], [5, 0]]
slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in enumerate([("work", c) for c in work] + [("qual_lengau", c) for c in dups]
                                                                                       + [("sentinel", tuple(c)) for c in SENT])]
att = dict(attempt_id="ec2-qual-E2Q1-a1", sequence=60, coordinates=[list(c) for c in work], duplicates=[list(c) for c in dups], sentinels=SENT)
plan = dict(attempt_id="ec2-qual-E2Q1-a1", contract="E2Q1", partition_sha256=PSHA, opmanifest_sha256="o" * 64, activation_sha256="a" * 64, sequence=60, slots=slots)
check("the unchanged plan_problem accepts the 76-slot E2Q1 plan", ES.plan_problem(plan, "E2Q1", att, PSHA, "o" * 64, "a" * 64) == "")
p2 = copy.deepcopy(plan); p2["slots"] = p2["slots"][1:]; [s.update(slot=k) for k, s in enumerate(p2["slots"])]
check("... and refuses 75 slots (one work slot short)", ES.plan_problem(p2, "E2Q1", dict(att, coordinates=att["coordinates"][1:]), PSHA, "o" * 64, "a" * 64) != "")
p3 = copy.deepcopy(plan); p3["slots"][60]["role"] = "qual_repeat"
check("... and refuses a role outside the contract", ES.plan_problem(p3, "E2Q1", att, PSHA, "o" * 64, "a" * 64) != "")
check("... and refuses the plan under the E2Q2 contract name (the contract is plan identity)", ES.plan_problem(plan, "E2Q2", att, PSHA, "o" * 64, "a" * 64) != "")

# ---- 5. the launcher's E2Q plan -------------------------------------------------------------------------------------------------
done = {tuple(c) for c in SNAP["lengau_done"]}
w_, d_, s_ = PL.build("E2Q1", PART, {}, done, "t1-qual-E2Q1-1-abc", PANEL)
check("build: the declared work and duplicates, 4 token sentinels (Lengau-completed, not owned, never among the duplicates)",
      w_ == work and d_ == dups and len(s_) == 4 and not set(s_) & set(dups) and all(c in done and not RP.blocked(PART, *c) for c in s_))
check("build: the built plan carries >= 61 on one replicate (sentinels can only raise it)",
      max(E2R.rep_concentration([dict(rep=r) for r, _ in w_ + d_ + s_]).values()) >= 61)
check("build: the sentinels are the token rule's (prod_authority.sentinels, exclude = duplicates)",
      s_ == PA.sentinels({c for c in done if not RP.blocked(PART, *c)}, "t1-qual-E2Q1-1-abc", exclude=dups))
def refuse(fn):
    try:
        fn(); return ""
    except ValueError as e:
        return str(e)
check("build refuses when a panel work coordinate is already completed", "not all free" in refuse(lambda: PL.build("E2Q1", PART, {}, done | {(24, 11)}, "t", PANEL)))
leds = {"prod-e2": {"attempts": [dict(attempt=1, sequence=5, attempt_id="x", state="launched", ingestion="pending", contract="production",
                                      plan_sha256="p", coordinates=[[24, 30]])]}}
check("build refuses when a panel work coordinate is owned by another attempt", "not all free" in refuse(lambda: PL.build("E2Q1", PART, leds, done, "t", PANEL)))
check("build refuses when a duplicate is not Lengau-completed in the receipt", "Lengau-completed" in refuse(lambda: PL.build("E2Q1", PART, {}, done - {(28, 2)}, "t", PANEL)))
check("build refuses without the declared panel", "declared panel" in refuse(lambda: PL.build("E2Q1", PART, {}, done, "t", None)))
check("build refuses the E2Q contracts on the epoch-1 partition", "epoch-2" in refuse(lambda: PL.build("E2Q1", json.load(open(os.path.join(CHPC, "row19_partition_e1.json"))), {}, done, "t", PANEL)))
check("panel_for validates the panel against the partition before any build (a tampered panel refuses)",
      "E2Q panel" in refuse(lambda: PL.panel_for(PART, PSHA, bad)) and PL.panel_for(PART, PSHA, FIX) == PANEL)
check("run names: E2Q1 -> qual-E2Q1, E2Q2 -> qual-E2Q2 (both counted by prod_authority.is_e2_qual), production -> prod-e2",
      PL.run_of("E2Q1", 2) == "qual-E2Q1" and PL.run_of("E2Q2", 2) == "qual-E2Q2" and PL.run_of("production", 2) == "prod-e2"
      and PA.is_e2_qual("qual-E2Q1") and PA.is_e2_qual("qual-E2Q2"))
rel = dict(qualification=dict(ok=True), qualification_e2=dict(ok=True, e2q2_ok=False), production=dict(ok=False))
check("gate: E2Q1 is refused at epoch 1 even when permitted", "epoch 2 only" in PL.gate_problem("E2Q1", 1, rel, {}, None))
check("gate: E2Q1 at epoch 2 with the permission and no earlier instance passes", PL.gate_problem("E2Q1", 2, rel, {}, None) == "")
check("gate: the epoch-1 Q1 permission never stands in for the epoch-2 one", "does not permit" in PL.gate_problem("E2Q1", 2, dict(rel, qualification_e2=dict(ok=False)), {}, None))
check("budget: a qual-E2 run is bounded by epoch2_problem, not the epoch-1 per-part ceilings", PA.budget_problem({}, "qual-E2Q1", 27.92) == "")
check("code_path: before promotion the candidate copies, after promotion the promoted files",
      EQ.code_path(T1, "chpc/row19_ec2_state.py", True) == os.path.join(Q, "row19_ec2_state.py")
      and EQ.code_path(T1, "chpc/row19_ec2_ingest.py", True) == os.path.join(E2, "row19_ec2_ingest.py")
      and EQ.code_path(T1, "chpc/row19_ec2_state.py", False) == os.path.join(T1, "chpc", "row19_ec2_state.py")
      and EQ.code_path(T1, "analyze.py", True) == os.path.join(T1, "analyze.py"))
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
