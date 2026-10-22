"""Controls v19 CANDIDATE (NOT adopted): tests of the E2Q3 ON-DEMAND QUALIFIER (owner decision 21 Oct 2026, R052 "On-demand
E2Q3"; DESIGN_v19.md s.7). Mac, pure python, synthetic or read-only; no AWS, no ssh, no Lengau. Writes only temporary dirs.

  1. the candidate chpc modules (row19_ec2_state REVISION 5, row19_ec2_e2qual REVISION 2, row19_ec2_ingest REVISION 9) add
     E2Q3 and change nothing else: every earlier contract byte-stable, the panel regenerates byte-equal, the release constants
     and code set unchanged, the unchanged qualifier reads the grown contract set;
  2. the E2Q3 operational manifest is the maker's exact derivation; the E2Q1/E2Q2/production manifests still derive byte-equal;
  3. prod_authority REVISION 9 (live aws_ec2 bytes over the candidate chpc modules): E2Q3 admission refused without its own
     permit, before E2Q1 AND E2Q2 are both dispositioned, and as a second E2Q3; the USD 300 allowance arithmetic (15.74 + 8.30
     + 128.02); the counter 3; the funding declaration still byte-equal; the crash envelope; on-demand charging at 5.60 (the
     authority and the reaper agree);
  4. qual_permit REVISION 3 (--e2q3) on a temporary copy of the release state;
  5. prod_launch REVISION 8: the market arguments (spot contracts byte-unchanged, on-demand none), and a full E2Q3 admission
     (dry run and live, captured dispatch) next to an E2Q2 admission on the same synthetic state.

    python3 chpc/candidate_v19_oploss/test_v19_e2q3.py          (from workspace_demo/t1_access)"""
import argparse, ast, copy, difflib, hashlib, importlib.util, io, json, os, re, shutil, sys, tempfile, time, contextlib

CAND = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(CAND); T1 = os.path.dirname(CHPC)
AWS = os.path.join(T1, "aws_ec2")
for p in (T1, CHPC, AWS):
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


ES0 = load("row19_ec2_state_v18", os.path.join(CHPC, "row19_ec2_state.py"))          # the live v18 bytes (comparison only)
EQ0 = load("row19_ec2_e2qual_v18", os.path.join(CHPC, "row19_ec2_e2qual.py"))
ES = load("row19_ec2_state", os.path.join(CAND, "row19_ec2_state.py"))                # the candidate: what every import below sees
EQ = load("row19_ec2_e2qual", os.path.join(CAND, "row19_ec2_e2qual.py"))
import row19_partition as RP                                                         # unchanged v18 bytes
import prod_authority as PA, prod_launch as PL, qual_permit as QP, bench_launch as L, bench_reaper as BR  # live aws_ec2 bytes
assert PA.ES is ES and PA.EQ is EQ and PL.ES is ES and PL.EQ is EQ, "the aws_ec2 tools must see the candidate chpc modules"
fails, npass = [], [0]


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{str(extra)[:300]}]" if extra and not cond else ""), flush=True)
    if cond:
        npass[0] += 1
    else:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def removed_lines(old, new):
    """The lines of `old` that `new` drops or replaces (difflib), as a list."""
    a, b = open(old).read().splitlines(), open(new).read().splitlines()
    return [a[i] for tag, i1, i2, _j1, _j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag in ("replace", "delete")
            for i in range(i1, i2)]


PROD_P = os.path.join(CHPC, "row19_screen_manifest.json"); PROD = json.load(open(PROD_P)); PROD_SHA = PA.PROD_SHA
PART_P = os.path.join(CHPC, "row19_partition_e2.json"); PSHA = sha(PART_P); PART = RP.load(PART_P, PROD, PROD_SHA)
PANEL_P = os.path.join(AWS, "prod", "panel_e2q_e2.json"); PANEL = json.load(open(PANEL_P))
SNAP_P = os.path.join(T1, PANEL["claims_snapshot"]["path"])
MAN3 = os.path.join(CAND, "manifest_e2q3_e2.json")

# ---- 1. the candidate chpc modules ---------------------------------------------------------------------------------------
c2, c3 = ES.CONTRACTS["E2Q2"], ES.CONTRACTS["E2Q3"]
check("state: E2Q3 = E2Q2's geometry and roles (c7a.24xlarge, 76 workers, 60 GB, 52 / 20 / 4) with market on-demand and max_price 5.60",
      {k: v for k, v in c3.items() if k not in ("market", "max_price")} == {k: v for k, v in c2.items() if k != "max_price"}
      and c3["market"] == "on-demand" and c3["max_price"] == 5.60 and sorted(c3) == sorted(list(c2) + ["market"]))
check("state: every earlier contract is byte-stable (equal to v18's, no market key) and reads as spot",
      {k: v for k, v in ES.CONTRACTS.items() if k != "E2Q3"} == ES0.CONTRACTS and all("market" not in c for k, c in ES.CONTRACTS.items() if k != "E2Q3")
      and [ES.contract_market(k) for k in sorted(ES.CONTRACTS)] == ["spot", "spot", "on-demand", "spot", "spot", "spot"])
rm = removed_lines(os.path.join(CHPC, "row19_ec2_state.py"), os.path.join(CAND, "row19_ec2_state.py"))
check("state: the candidate only ADDS to the v18 bytes (REVISION 5 text, the E2Q3 contract, contract_market); nothing removed but the docstring close",
      rm == ["the live row19_ec2_state.py (bda200dc), because ingestion's operational_problem and plan_problem read CONTRACTS from it.\"\"\""], rm)
check("e2qual: CONTRACTS / RUNS grow by E2Q3 -> qual-E2Q3; the panel declaration's own fields stay E2Q1/E2Q2 (frozen)",
      EQ.CONTRACTS == ("E2Q1", "E2Q2", "E2Q3") and EQ.RUNS == {c: f"qual-{c}" for c in EQ.CONTRACTS}
      and EQ.PANEL_CONTRACTS == EQ0.CONTRACTS and EQ.PANEL_RUNS == EQ0.RUNS)
same = all(getattr(EQ, k) == getattr(EQ0, k) for k in ("CODE", "COVERAGE", "CERT_SCHEMA", "RELEASE_LITERAL", "REPLAY_SCOPE", "WORK_N", "DUP_N",
                                                        "SENTINELS", "WORKERS", "EXPECT_S", "LIFETIME_S", "MEM_HOST_LIMIT_GIB", "MEM_MIN_SAMPLES",
                                                        "QUAL_MAX_UNPRODUCED", "EPOCH", "PANEL_SCHEMA"))
check("e2qual: the release rule constants, the certificate code set and the panel schema are unchanged", same)
rm = removed_lines(os.path.join(CHPC, "row19_ec2_e2qual.py"), os.path.join(CAND, "row19_ec2_e2qual.py"))
check("e2qual: the only replaced lines are the docstring close, CONTRACTS, RUNS and the panel's contracts/runs fields", len(rm) == 4
      and rm[1].startswith("CONTRACTS = (\"E2Q1\", \"E2Q2\")") and rm[2].startswith("RUNS = {") and "list(CONTRACTS)" in rm[3], rm)
snap = json.load(open(SNAP_P))
want = EQ.derive_panel(PART, PSHA, snap, sha(SNAP_P), PANEL["claims_snapshot"]["path"])
check("panel: the committed declared panel (f04a5e43) regenerates BYTE-EQUAL under the candidate module and passes panel_problem",
      EQ.panel_bytes(want) == open(PANEL_P, "rb").read() and sha(PANEL_P).startswith("f04a5e43")
      and EQ.panel_problem(PANEL, PART, PSHA, snap, sha(SNAP_P)) == "" and EQ0.panel_problem(PANEL, PART, PSHA, snap, sha(SNAP_P)) == "")
srcs = {f: open(os.path.join(d, f)).read() for d, fs in ((AWS, ("prod_authority.py", "prod_launch.py", "e2q_stage.py", "make_prod_manifest.py")),
                                                        (CHPC, ("row19_ec2_qualify.py",)), (CAND, ("row19_ec2_ingest.py",))) for f in fs}
check("panel: no consumer gates on the panel's `contracts` / `runs` fields (they are declaration text)",
      not any(re.search(r"panel(\[|\.get\()\s*[\"'](contracts|runs)[\"']", s) for s in srcs.values()))
qs = srcs["row19_ec2_qualify.py"]
check("qualifier (unchanged v18 bytes 1d8eee78): it reads the contract set from row19_ec2_e2qual, so qual-E2Q3/<n> is accepted under v19",
      sha(os.path.join(CHPC, "row19_ec2_qualify.py")).startswith("1d8eee78")
      and 'contract not in EQ.CONTRACTS or a.key.split("/")[0] != EQ.RUNS[contract]' in qs and "E2Q2\"" not in qs.split("REVISION 6")[-1])
ig_contracts = ast.literal_eval(re.search(r"^E2Q_CONTRACTS = (\(.*?\))", srcs["row19_ec2_ingest.py"], re.M).group(1))   # static: ingestion imports the science stack
rm = removed_lines(os.path.join(CHPC, "row19_ec2_ingest.py"), os.path.join(CAND, "row19_ec2_ingest.py"))
check("ingest: E2Q_CONTRACTS = E2Q1, E2Q2, E2Q3 (the released per-slot route); only that line and the docstring close are replaced",
      ig_contracts == ("E2Q1", "E2Q2", "E2Q3") and len(rm) == 2 and rm[1].startswith("E2Q_CONTRACTS = (\"E2Q1\", \"E2Q2\")"), rm)

# ---- 2. operational manifests ----------------------------------------------------------------------------------------------
check("manifest: the candidate manifest_e2q3_e2.json is exactly the bytes make_prod_manifest writes for E2Q3 (and passes operational_problem)",
      open(MAN3, "rb").read() == EQ.opmanifest_bytes(ES, PROD, PROD_SHA, "E2Q3") and ES.operational_problem(json.load(open(MAN3)), PROD, PROD_SHA) == ""
      and json.load(open(MAN3))["ec2_production"]["instance"]["market"] == "on-demand" and json.load(open(MAN3))["ec2_production"]["lifetime_s"] == 79200)
check("manifest: the committed E2Q1 / E2Q2 / production manifests still derive byte-equal under the candidate state module",
      all(open(os.path.join(AWS, "prod", f"manifest_{c.lower()}_e2.json"), "rb").read() == EQ.opmanifest_bytes(ES, PROD, PROD_SHA, c)
          for c in ("E2Q1", "E2Q2", "production")))
check("manifest: the E2Q3 manifest is not yet at aws_ec2/prod/ (it is promoted with v19, the map's data row)",
      not os.path.exists(os.path.join(AWS, "prod", "manifest_e2q3_e2.json")))
slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in
         enumerate([("work", c) for c in PANEL["work"]] + [("qual_lengau", c) for c in PANEL["duplicates"]] + [("sentinel", c) for c in ([1, 0], [1, 1], [1, 2], [1, 3])])]
att = dict(attempt_id="ec2-qual-E2Q3-a1", sequence=9, coordinates=PANEL["work"], duplicates=PANEL["duplicates"], sentinels=[[1, 0], [1, 1], [1, 2], [1, 3]])
plan = dict(attempt_id=att["attempt_id"], contract="E2Q3", partition_sha256=PSHA, opmanifest_sha256="o" * 64, activation_sha256="a" * 64, sequence=9, slots=slots)
check("plan: the unchanged plan contract accepts the E2Q3 plan and refuses it under the E2Q2 name (the contract is plan identity)",
      ES.plan_problem(plan, "E2Q3", att, PSHA, "o" * 64, "a" * 64) == "" and ES.plan_problem(plan, "E2Q2", att, PSHA, "o" * 64, "a" * 64) != "")

# ---- 3. prod_authority REVISION 9 -------------------------------------------------------------------------------------------
REAL = PA.ledgers()
E1 = REAL["qual-E2Q1"]["attempts"]; E2 = REAL["qual-E2Q2"]["attempts"]
check("authority: the real ledgers hold E2Q1/1 (USD 15.74) and E2Q2/1 (USD 8.30), both reconciled and dispositioned",
      [(a["state"], a["ingestion"], round(PA.charged(a), 2)) for a in E1] == [("reconciled", "dispositioned", 15.74)]
      and [(a["state"], a["ingestion"], round(PA.charged(a), 2)) for a in E2] == [("reconciled", "dispositioned", 8.30)])
REL = {"qualification_e2": {"ok": True, "e2q2_ok": True, "e2q3_ok": True}}


def with_run(leds, run, attempts):
    d = copy.deepcopy(leds); d[run] = {"attempts": attempts}; return d


def e3(state="intent", **kw):
    a = dict(attempt=1, sequence=999, attempt_id="ec2-qual-E2Q3-a1", contract="E2Q3", state=state, lifetime_s=79200, max_price=5.60,
             anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD, type="c7a.24xlarge", coordinates=[], ingestion="pending", market="on-demand")
    a.update(kw); return a


check("admission: E2Q3 is admitted when E2Q1 and E2Q2 are both dispositioned and its own permit exists", PA.e2q_admission_problem("E2Q3", REL, REAL) == "")
r = PA.e2q_admission_problem("E2Q3", {"qualification_e2": {"ok": True, "e2q2_ok": True}}, REAL)
check("admission: refused without its own permission record (qualification_e2.e2q3)", "own permission record" in r, r)
pend = with_run(REAL, "qual-E2Q2", [dict(E2[0], ingestion="pending")])
r = PA.e2q_admission_problem("E2Q3", REL, pend)
check("admission: refused while the E2Q2 attempt is not yet dispositioned", "every non-rejected E2Q1 and E2Q2 attempt" in r, r)
r = PA.e2q_admission_problem("E2Q3", REL, {k: v for k, v in REAL.items() if k != "qual-E2Q2"})
check("admission: refused when no E2Q2 attempt exists (E2Q3 follows E2Q2, never replaces it)", "E2Q1 and E2Q2" in r, r)
r = PA.e2q_admission_problem("E2Q3", REL, with_run(REAL, "qual-E2Q1", [dict(E1[0], ingestion="pending")]))
check("admission: refused while the E2Q1 attempt is not dispositioned", "E2Q1 and E2Q2" in r, r)
r = PA.e2q_admission_problem("E2Q3", REL, with_run(REAL, "qual-E2Q3", [e3("launched")]))
check("admission: a second E2Q3 is refused (at most one instance; no fourth attempt)", "at most one" in r, r)
check("admission: a REJECTED E2Q3 (no instance ever existed) does not count", PA.e2q_admission_problem("E2Q3", REL, with_run(REAL, "qual-E2Q3", [e3("rejected")])) == "")
check("admission: E2Q1 and E2Q2 stay refused (one instance each)", "ONE instance" in PA.e2q_admission_problem("E2Q1", REL, REAL)
      and "at most one" in PA.e2q_admission_problem("E2Q2", REL, REAL))
fund = json.load(open(PA.E2_FUNDING))
worst = PA.worst_usd(PA.QUAL_LIFETIME_S, ES.CONTRACTS["E2Q3"]["max_price"])
check("money: the E2Q3 worst case is 22.75 h x (5.60 + 0.014) + 0.30 = USD 128.02", round(worst, 2) == 128.02, worst)
check("money: allowance 15.74 + 8.30 + 128.02 = 152.05 <= 300 (unrounded sum) - epoch2_problem admits E2Q3; budget_problem routes it to the epoch bound",
      PA.epoch2_problem(REAL, "qual-E2Q3", worst, fund) == "" and PA.budget_problem(REAL, "qual-E2Q3", worst) == "")
used = sum(PA.charged(a) for a in E1 + E2)
r = PA.epoch2_problem(REAL, "qual-E2Q3", 300.0 - used + 0.01, fund)
check("money: a worst case 1 cent above the USD 300 allowance remainder is refused; the exact remainder fits",
      "allowance" in r and PA.epoch2_problem(REAL, "qual-E2Q3", 300.0 - used, fund) == "", r)
three = with_run(REAL, "qual-E2Q3", [e3("reconciled", terminal=dict(compute_s=3600, ancillary_s=3600), ingestion="dispositioned")])
r = PA.epoch2_problem(three, "qual-E2Q3", worst, fund)
check("money: the counter is 3 - with three non-rejected epoch-2 qualification instances a further one is refused",
      PA.E2_MAX_QUAL_INSTANCES == 3 and "3 qualification instance(s) used" in r, r)
check("funding: the declaration aws_ec2/e2_funding.json (d6f414e8) still derives byte-equal (max_qualification_instances stays 2)",
      sha(PA.E2_FUNDING).startswith("d6f414e8") and PA.funding_problem(fund, PART, REAL) == "" and fund["max_qualification_instances"] == 2
      and PA.E2_FUNDED_QUAL_INSTANCES == 2)
check("crash rule: E2Q3 shares the production envelope label (same instance type, workers, volume)",
      "E2Q3" in PA.CRASH_EQUIVALENT_CONTRACTS and PA.crash_envelope("E2Q3", "c7a.24xlarge", 79200) == ["production", "c7a.24xlarge", 79200]
      and PA.is_e2_qual("qual-E2Q3") and PA.crash_counted_run("qual-E2Q3"))
rec = e3("reconciled", terminal=dict(compute_s=10 * 3600, ancillary_s=10.5 * 3600))
want_c = 10 * 5.60 + 10.5 * PA.ANC_H_PROD + PA.S3_FIXED_PROD
check("charging: an on-demand attempt is charged at its recorded 5.60 USD/h - worst case until reconciled, observed hours after; the reaper agrees",
      abs(PA.charged(rec) - want_c) < 1e-9 and abs(BR.report_charge(rec) - want_c) < 1e-9
      and abs(PA.charged(e3("launched")) - worst) < 1e-9 and abs(BR.report_charge(e3("launched")) - worst) < 1e-9)
src = srcs["prod_authority.py"]
check("release: an E2Q3 certificate releases only with every E2Q1 and E2Q2 attempt dispositioned (the branch exists beside E2Q2's)",
      'if run == E2Q_RUNS["E2Q3"]:' in src and "an E2Q3 release needs every E2Q1 and E2Q2 attempt dispositioned" in src
      and "len(_nonrejected(leds, is_e2_qual)) > E2_MAX_QUAL_INSTANCES" in src)

# ---- 4. qual_permit --e2q3 on a temporary copy of the release state --------------------------------------------------------
SAVE = dict(PA_HERE=PA.HERE, PA_REL=PA.RELEASE_STATE, L_HERE=L.HERE)
TQ = tempfile.mkdtemp(prefix="v19e2q3_permit_"); TH = os.path.join(TQ, "t1", "aws_ec2"); os.makedirs(TH)
r0 = json.load(open(os.path.join(AWS, "ec2_release_state.json")))
backing = [r0["row23"]["report_path"], r0["qualification"]["record_path"], r0["qualification_e2"]["record_path"],
           r0["qualification_e2"]["e2q2"]["record_path"], "runs/BENCH_FENCE.json", "prod/permit_e2q3.md", "ec2_release_state.json"]
for rel in backing:
    dst = os.path.normpath(os.path.join(TH, rel)); os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(os.path.normpath(os.path.join(AWS, rel)), dst)
PA.HERE, PA.RELEASE_STATE, L.HERE = TH, os.path.join(TH, "ec2_release_state.json"), TH
quiet = lambda *a, **k: None
check("permit: the temporary release state is the real one (qualification_e2 and e2q2 ok, no e2q3 yet)",
      PA.release_state()["qualification_e2"]["ok"] and PA.release_state()["qualification_e2"]["e2q2_ok"] and not PA.release_state()["qualification_e2"]["e2q3_ok"])
out = []
check("permit: --e2q3 together with --e2q2 is refused", QP.permit("prod/permit_e2q3.md", 1, out.append, epoch2=True, e2q2=True, e2q3=True) == 3
      and "E2Q3 is permitted only" in out[-1], out)
check("permit: --e2q3 without --epoch2 is refused", QP.permit("prod/permit_e2q3.md", 1, out.append, e2q3=True) == 3)
noq2 = json.load(open(PA.RELEASE_STATE)); del noq2["qualification_e2"]["e2q2"]; json.dump(noq2, open(PA.RELEASE_STATE, "w"), indent=1)
check("permit: --e2q3 is refused while E2Q2 is not permitted", QP.permit("prod/permit_e2q3.md", 1, out.append, epoch2=True, e2q3=True) == 3)
shutil.copy(os.path.join(AWS, "ec2_release_state.json"), PA.RELEASE_STATE)
check("permit: --epoch2 --e2q3 writes qualification_e2.e2q3 pinning the record; release_state reads e2q3_ok; the e2q2 block is untouched",
      QP.permit("prod/permit_e2q3.md", 5, quiet, epoch2=True, e2q3=True) == 0 and PA.release_state()["qualification_e2"]["e2q3_ok"]
      and json.load(open(PA.RELEASE_STATE))["qualification_e2"]["e2q3"]["record_sha256"] == sha(os.path.join(AWS, "prod", "permit_e2q3.md"))
      and json.load(open(PA.RELEASE_STATE))["qualification_e2"]["e2q2"] == r0["qualification_e2"]["e2q2"])
check("permit: with the permit in place and the real ledgers, the E2Q3 gate opens",
      PA.e2q_admission_problem("E2Q3", PA.release_state(REAL), REAL) == "")
open(os.path.join(TH, "prod", "permit_e2q3.md"), "a").write("edited after permission\n")
check("permit: a permit record edited after permission reads as NOT permitted", not PA.release_state()["qualification_e2"]["e2q3_ok"])
PA.HERE, PA.RELEASE_STATE, L.HERE = SAVE["PA_HERE"], SAVE["PA_REL"], SAVE["L_HERE"]
shutil.rmtree(TQ, ignore_errors=True)

# ---- 5. prod_launch REVISION 8 ----------------------------------------------------------------------------------------------
def old_spot(c):        # the pre-REVISION-8 literal of prod_launch.admit
    return ["--instance-market-options", json.dumps({"MarketType": "spot", "SpotOptions": {
        "MaxPrice": f"{c['max_price']:.2f}", "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}})]


check("launch: every spot contract's market arguments are byte-identical to the pre-REVISION-8 request",
      all(PL.market_args(ES.CONTRACTS[k]) == old_spot(ES.CONTRACTS[k]) for k in ES.CONTRACTS if k != "E2Q3"))
check("launch: the on-demand E2Q3 request carries NO market options (no spot request)", PL.market_args(ES.CONTRACTS["E2Q3"]) == [])
try:
    PL.market_args(dict(ES.CONTRACTS["E2Q3"], market="capacity-block")); bad = False
except ValueError:
    bad = True
check("launch: an unknown purchase market refuses", bad)

TA = tempfile.mkdtemp(prefix="v19e2q3_launch_")
SAVE = dict(L_HERE=L.HERE, PA_HERE=PA.HERE, LOCK=PA.LOCK, STATE=PA.STATE, INV=PA.INV_DIR, REL=PA.release_state, WI=PA.write_inventory,
            AWSF=L.aws, FIN=L.finish, PINS=L.PINS, ACT=RP.activation_problem,
            PL=dict(stop_problem=PL.stop_problem, controls_doc=PL.controls_doc, controls_pin=PL.controls_pin, snapshot_state=PL.snapshot_state,
                    inventory_bound_problem=PL.inventory_bound_problem))
L.HERE = PA.HERE = TA
PA.LOCK, PA.STATE, PA.INV_DIR = os.path.join(TA, "runs", ".authority.lock"), os.path.join(TA, "runs", ".authority_state.json"), os.path.join(TA, "runs", "inventory")
shutil.copy(os.path.join(AWS, "budget_baseline.json"), TA)
CALLS, DISPATCH, RELX = [], [], {"r": REL}
PA.release_state = lambda leds=None: RELX["r"]
PA.write_inventory = lambda now=None: None


def fake_aws(*args, timeout=120):
    CALLS.append(list(args))
    if args[0] == "ssm":
        return argparse.Namespace(stdout=json.dumps({"Parameters": [{"Value": "ami-test"}]}))
    if "run-instances" in args and "--dry-run" in args:
        raise L.AwsError("An error occurred (DryRunOperation) when calling the RunInstances operation", "DryRunOperation")
    return argparse.Namespace(stdout="{}")


L.aws = fake_aws
L.finish = lambda run, led, att, fresh, guard=None: DISPATCH.append((run, att, guard())) or 0
tgz = os.path.join(TA, "t.tgz"); open(tgz, "w").write("toolchain"); L.PINS = dict(L.PINS, **{"t1_toolchain_lengau.tgz": L.sha256(tgz)})
RP.activation_problem = lambda *a, **k: ""
PL.stop_problem = lambda run, snapshot: ""
PL.controls_doc = lambda: {"versions": [{"version": 19, "partition": {"path": "chpc/row19_partition_e2.json", "sha256": PSHA}}]}
PL.controls_pin = lambda: PSHA
PL.inventory_bound_problem = lambda w: ""
snapd = os.path.join(TA, "snap"); actp = os.path.join(snapd, "live", "refit", "root", "ec2", "activation_e2.json")
os.makedirs(os.path.dirname(actp)); open(actp, "w").write("{}")
dups = {tuple(c) for c in PANEL["duplicates"]}
extra = [(r, i) for r in range(1, 60) for i in range(200) if not RP.blocked(PART, r, i) and (r, i) not in dups][:12]
DONE = dups | set(extra)
PL.snapshot_state = lambda snapshot, part, now=None: (DONE, "watch_refit_synthetic.json", {"time": time.time()})


def seed(runs):
    shutil.rmtree(os.path.join(TA, "runs"), ignore_errors=True)
    for run in runs:
        d = os.path.join(TA, "runs", run); os.makedirs(d)
        shutil.copy(os.path.join(AWS, "runs", run, "attempts.json"), d)
    os.makedirs(os.path.join(TA, "runs", "inventory"), exist_ok=True)


def admit(contract, manifest, dry=False):
    a = argparse.Namespace(contract=contract, epoch=2, partition=PART_P, manifest=manifest, panel=PANEL_P, snapshot=snapd, tarball=tgz, dry_run=dry)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = PL.admit(a)
    except SystemExit as e:
        rc = f"EXIT {e.code}"
    return rc, buf.getvalue()


def run_args(calls):
    return [c for c in calls if "run-instances" in c]


seed(["qual-E2Q1", "qual-E2Q2", "qual-Q2"])
rc, out = admit("E2Q3", MAN3, dry=True)
dry = run_args(CALLS)
check("E2Q3 dry run: authorised (DryRunOperation) with no market options, nothing journaled",
      rc == 0 and "EC2 authorization OK" in out and len(dry) == 1 and "--instance-market-options" not in dry[0]
      and not os.path.exists(os.path.join(TA, "runs", "qual-E2Q3", "attempts.json")), (rc, out[-400:]))
CALLS.clear()
rc, out = admit("E2Q3", MAN3)
led3 = json.load(open(os.path.join(TA, "runs", "qual-E2Q3", "attempts.json")))
a3 = led3["attempts"][-1]; req3 = json.load(open(a3["request"])); plan3 = json.load(open(a3["plan"]))
check("E2Q3 live: admitted as qual-E2Q3/1, the declared panel (52 + 20 + 4), worst USD 128.02 printed, ON-DEMAND",
      rc == 0 and a3["attempt_id"] == "ec2-qual-E2Q3-a1" and len(a3["coordinates"]) == 52 and len(a3["duplicates"]) == 20 and len(a3["sentinels"]) == 4
      and "worst USD 128.02" in out and "ON-DEMAND, charged at 5.60/h" in out, (rc, out[-500:]))
check("E2Q3 live: the saved RunInstances request has no --instance-market-options; the attempt records max_price 5.60 and market on-demand; "
      "the plan's instance carries market on-demand",
      "--instance-market-options" not in req3["args"] and a3["max_price"] == 5.60 and a3["market"] == "on-demand" and a3["type"] == "c7a.24xlarge"
      and plan3["instance"]["market"] == "on-demand" and plan3["contract"] == "E2Q3" and plan3["lifetime_s"] == 79200
      and DISPATCH and DISPATCH[-1][0] == "qual-E2Q3" and DISPATCH[-1][2] == "")
qual_usd = sum(PA.charged(x) for r, l in PA.ledgers().items() if PA.is_e2_qual(r) for x in l["attempts"])
check("E2Q3 live: the authority charges the intent at its worst case USD 128.02; the qualification allowance then holds USD 152.05 of 300",
      abs(PA.charged(a3) - worst) < 1e-9 and abs(qual_usd - (used + worst)) < 1e-9 and round(qual_usd, 2) == 152.05, qual_usd)
led3["attempts"][-1]["state"] = "launched"; L.save("qual-E2Q3", led3)          # as the dispatch would leave it
rc2, out2 = admit("E2Q3", MAN3)
check("E2Q3: a second admission on the same state is refused (at most one instance)", rc2 != 0 and "at most one" in out2 + str(rc2), (rc2, out2[-300:]))
# E2Q2 on a state where it was never launched: its spot request is byte-unchanged
CALLS.clear(); seed(["qual-E2Q1", "qual-Q2"])
rc, out = admit("E2Q2", os.path.join(AWS, "prod", "manifest_e2q2_e2.json"))
a2 = json.load(open(os.path.join(TA, "runs", "qual-E2Q2", "attempts.json")))["attempts"][-1]; req2 = json.load(open(a2["request"]))
i = req2["args"].index("--instance-market-options")
check("E2Q2 (spot) on the same harness: the market options are exactly the pre-REVISION-8 spot request; no market key in its attempt",
      rc == 0 and req2["args"][i:i + 2] == old_spot(ES.CONTRACTS["E2Q2"]) and "market" not in a2 and a2["max_price"] == 1.20, (rc, out[-300:]))
norm = lambda args: [("X" if k > 0 and args[k - 1] in ("--client-token", "--tag-specifications", "--user-data") else x) for k, x in enumerate(args)]
check("E2Q3 vs E2Q2: the two requests differ ONLY by the two spot-market arguments (token, tags and user-data aside)",
      norm(req3["args"]) == norm(req2["args"][:i] + req2["args"][i + 2:]))

L.HERE, PA.HERE, PA.LOCK, PA.STATE, PA.INV_DIR = SAVE["L_HERE"], SAVE["PA_HERE"], SAVE["LOCK"], SAVE["STATE"], SAVE["INV"]
PA.release_state, PA.write_inventory, L.aws, L.finish, L.PINS, RP.activation_problem = SAVE["REL"], SAVE["WI"], SAVE["AWSF"], SAVE["FIN"], SAVE["PINS"], SAVE["ACT"]
for k, v in SAVE["PL"].items():
    setattr(PL, k, v)
shutil.rmtree(TA, ignore_errors=True)
check("the live tree is untouched: no E2Q3 ledger, the release state has no e2q3 block, the v18 chpc modules in place",
      not os.path.exists(os.path.join(AWS, "runs", "qual-E2Q3")) and "e2q3" not in json.load(open(os.path.join(AWS, "ec2_release_state.json")))["qualification_e2"]
      and sha(os.path.join(CHPC, "row19_ec2_state.py")).startswith("7bdedafc") and sha(os.path.join(CHPC, "row19_ec2_e2qual.py")).startswith("5ceba551"))

print(f"\n{npass[0]} passed, {len(fails)} failed")
print("ALL OK" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
