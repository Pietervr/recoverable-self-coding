"""EC2 provider epoch 2 CANDIDATE (NOT adopted): tests of the Mac authority and launcher changes
(chpc/candidate_e2/aws_ec2/prod_authority.py REVISION 5, prod_launch.py REVISION 5) - pure python, no AWS, no Lengau; every
ledger write goes to a temporary authority directory. Design reviews/2026-10-17_row19_resize_codex.md s.3, s.4, s.6 item 5;
owner 17 Oct 2026 (five concurrent instances; ~USD 1,779 + USD 300 bounded allowance).

  1. REAL replay (read-only) on the saved ledgers and inventory: the epoch-2 forecast + allowance fits the remaining envelope;
  2. the replicate-complete allocator over the explicit owned set: 46 batches of 72 cover the 3,274 owned coordinates
     exactly once, earliest replicates first; completed, owned and crash-excluded coordinates are skipped;
  3. the fleet ceiling of five live instances, and the cumulative worst-case reservation of concurrent attempts;
  4. the epoch-2 bounds: base + 4 production attempts, 2 qualification instances, USD 300 allowance money, forecast +
     allowance; the funding declaration is the exact derivation (tampering refuses);
  5. the EC2 crash rule from acknowledged unproduced slots, and `ack` with unproduced coordinates;
  6. the launcher's production plan for a schema-2 epoch (72 work replicate-complete + 4 Lengau sentinels, plan contract)
     and its epoch gate.

    python3 chpc/candidate_e2/test_e2_authority.py            (from workspace_demo/t1_access)"""
import copy, hashlib, importlib.util, json, math, os, shutil, sys, tempfile, time

CAND = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(CAND); T1 = os.path.dirname(CHPC)
AWS = os.path.join(T1, "aws_ec2")
for p in (T1, AWS, CHPC, CAND, os.path.join(CAND, "aws_ec2")):
    sys.path.insert(0, p)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


RP = load_mod("row19_partition", os.path.join(CAND, "row19_partition.py"))
PA = load_mod("prod_authority", os.path.join(CAND, "aws_ec2", "prod_authority.py"))
PL = load_mod("prod_launch", os.path.join(CAND, "aws_ec2", "prod_launch.py"))
import bench_launch as L
import row19_ec2_state as ES
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json"); MAN = json.load(open(MAN_PATH)); MAN_SHA = sha(MAN_PATH)
RP.DESIGNATED_PATH = os.path.join(CHPC, "candidate_v16", "row19_screen_designated.json")
E2 = RP.load(os.path.join(CAND, "row19_partition_e2.json"), MAN, MAN_SHA)
E1 = RP.load(os.path.join(CHPC, "row19_partition_e1.json"), MAN, MAN_SHA)
FUND_PATH = os.path.join(CAND, "aws_ec2", "e2_funding.json"); FUND = json.load(open(FUND_PATH))
OWN = sorted(RP.owned_set(E2))
WORST = PA.worst_usd(PA.QUAL_LIFETIME_S, 1.20)

# ---- 1. REAL replay (read-only: the saved ledgers, baseline and newest sealed inventory) ------------------------------------
check("the authority's data directory is aws_ec2/ (the candidate never writes beside itself)", PA.HERE == AWS and PL.HERE == AWS)
leds_real = PA.ledgers(); now = time.time()
b = PA.budget(leds_real, now)
inv = json.load(open(os.path.join(AWS, "runs", "inventory", "latest.json")))
print(f"   real ledgers: production+qualification USD {b['production_usd']:.5f}, all runs {b['all_runs_usd']:.5f}, baseline now {b['baseline_usd']:.2f}; "
      f"inventory generation {inv['generation']}")
remaining_env = PA.PROD_ENVELOPE_USD - b["production_usd"]
remaining_cap = PA.CUMULATIVE_CAP_USD - b["baseline_usd"] - b["all_runs_usd"]
check("REAL: Q1 + Q2 charged USD 44.96 against the 2,300 envelope (design s.3: 44.96495)", abs(b["production_usd"] - 44.96495) < 0.001, b["production_usd"])
check("REAL: forecast 1,778.52 + allowance 300 = 2,078.52 fits the remaining production envelope (2,255.04)",
      FUND["epoch_cap_usd"] == 2078.52 and FUND["epoch_cap_usd"] <= remaining_env, remaining_env)
print(f"   REAL: remaining production envelope USD {remaining_env:.2f}; remaining under the 3,000 cap now USD {remaining_cap:.2f} "
      f"(epoch cap 2,078.52 leaves {remaining_cap - FUND['epoch_cap_usd']:.2f} for idle accrual at 5.50/day)")
check("REAL: the funding declaration is the exact derivation from the e2 partition and the Q2 ledger (46 batches, 3,496 slots)",
      PA.funding_problem(FUND, E2) == "" and FUND["base_batches"] == 46 and FUND["paid_slots"] == 3496 and FUND["owned_coordinates"] == 3274)
check("REAL: Q2-derived forecasts 1,704.42 (planned slot) / 1,778.52 (successful slot); funding maxima 1,284.251 (design s.3)",
      FUND["forecast"]["planned_slot_usd"] == 1704.42 and FUND["forecast"]["successful_slot_usd"] == 1778.52
      and FUND["funding_maxima_all_base_usd"] == 1284.251 and abs(FUND["forecast"]["basis"]["q2_charged_usd"] - 11.700804) < 1e-6)
check("REAL: five-instance calendar ceil(46/5) x 21.2811 h = 8.87 days (design s.3)", FUND["calendar_days_at_fleet"] == 8.87)
check("REAL: no attempt is live; the reconciled Q1 attempt 4 still OWNS its 48 retired e1 coordinates (to be fenced before e2)",
      PA.live_fleet(leds_real) == [] and sorted(c for c, (k, _) in PA.owned(leds_real).items() if k == "qual-Q1/4") == sorted(
          (r, i) for i in (198, 199) for r in range(3, 27)) and not any(RP.blocked(E2, *c) for c in PA.owned(leds_real)))

# ---- from here every write goes to a temporary authority directory ------------------------------------------------------------
TMP = tempfile.mkdtemp()
for f in ("budget_baseline.json", "ec2_release_state.json"):
    shutil.copy(os.path.join(AWS, f), os.path.join(TMP, f))
L.HERE = PA.HERE = TMP
PA.LOCK, PA.STATE = os.path.join(TMP, "runs", ".authority.lock"), os.path.join(TMP, "runs", ".authority_state.json")
PA.INV_DIR, PA.RELEASE_STATE = os.path.join(TMP, "runs", "inventory"), os.path.join(TMP, "ec2_release_state.json")
PA.E2_FUNDING = FUND_PATH


def att(n, seq, state="launched", coords=(), ingestion="pending", contract="production", **kw):
    return dict(dict(attempt=n, sequence=seq, attempt_id=f"ec2-x-a{n}", state=state, ingestion=ingestion, contract=contract, plan_sha256="p",
                     coordinates=[list(c) for c in coords], lifetime_s=79200, max_price=1.20, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD,
                     type="c7a.24xlarge"), **kw)


def rec(n, seq, coords=(), usd_h=1.0, **kw):          # a reconciled attempt charged about usd_h hours
    return att(n, seq, state="reconciled", coords=coords, terminal=dict(compute_s=3600 * usd_h, ancillary_s=3600 * usd_h), **kw)


# ---- 2. allocator ----------------------------------------------------------------------------------------------------------
a1 = PA.allocate(E2, {}, set(), 72)
reps1 = [r for r, _ in a1]
check("schema 2: the first batch is the earliest EC2 replicate's open coordinates in index order (rep 24 first)",
      a1 == OWN[:72] and a1[0][0] == 24 and reps1 == sorted(reps1) and all(a1[k] < a1[k + 1] for k in range(71)))
check("replicate-complete: rep 24's remaining coordinates all come before any of rep 25's",
      all(c[0] == 24 for c in a1[:sum(1 for c in OWN if c[0] == 24)]))
check("schema 1 keeps its order (index 199 downward, reps ascending)", PA.allocate(E1, {}, set(), 2) == [(3, 199), (4, 199)])
leds, got, seq = {"prod-e2": {"attempts": []}}, [], 1
for n in range(1, 60):
    w = PA.allocate(E2, leds, set(), 72)
    if not w:
        break
    got += w; leds["prod-e2"]["attempts"].append(att(n, seq, coords=w)); seq += 1
check("REPLAY: 46 batches of <= 72 cover all 3,274 owned coordinates exactly once (last batch 34)",
      len(leds["prod-e2"]["attempts"]) == 46 and sorted(got) == OWN and len(set(got)) == 3274
      and len(leds["prod-e2"]["attempts"][-1]["coordinates"]) == 3274 - 45 * 72)
check("every allocated coordinate is owned by epoch 2 (never a Lengau claim, never index >= 80)", all(RP.blocked(E2, *c) for c in got))
done = set(OWN[:10]); excl = {OWN[10]}
w = PA.allocate(E2, {}, done, 72, excl)
check("completed and crash-excluded coordinates are skipped", not (set(w) & (done | excl)) and w[0] == OWN[11])
check("a live attempt's coordinates are never re-allocated", not (set(PA.allocate(E2, {"prod-e2": {"attempts": [att(1, 1, coords=a1)]}}, set(), 72)) & set(a1)))

# ---- 3. fleet ceiling and cumulative reservation ---------------------------------------------------------------------------
five = {"prod-e2": {"attempts": [att(n, n, coords=[OWN[n]]) for n in range(1, 5)]}, "qual-E2Q1": {"attempts": [att(1, 9, contract="E2Q1")]}}
check("five live instances (production + qualification) refuse a sixth", "fleet ceiling" in PA.fleet_problem(five))
four = copy.deepcopy(five); four["qual-E2Q1"]["attempts"][0]["state"] = "reconciled"
four["qual-E2Q1"]["attempts"][0]["terminal"] = dict(compute_s=60, ancillary_s=60)
check("four live + one reconciled admit a fifth", PA.fleet_problem(four) == "")
amb = copy.deepcopy(four); amb["qual-E2Q1"]["attempts"][0].update(state="ambiguous")
check("an ambiguous attempt counts as live (it may hold an instance)", PA.fleet_problem(amb) != "")
rej = copy.deepcopy(four); rej["prod-e2"]["attempts"].append(att(9, 20, state="rejected"))
check("a rejected attempt (no instance ever) does not count", PA.fleet_problem(rej) == "")
bench = copy.deepcopy(four); bench["b2"] = {"attempts": [dict(attempt=1, state="launched", lifetime_s=1, max_price=1.2)]}
check("benchmark runs are outside the production fleet (exclusion_problem refuses them separately)",
      PA.fleet_problem(bench) == "" and PA.exclusion_problem(bench, L.REGION) != "")
bb = PA.budget(five)
check("five live attempts reserve 5 x worst case (USD 27.92) cumulatively against the envelope", abs(bb["production_usd"] - 5 * WORST) < 1e-6, bb)
rel = PA.release_state()
heavy = {"prod-e2": {"attempts": [rec(n, n, usd_h=2200 / 4 / 1.214) for n in range(1, 5)]}}
heavy["prod-e2"]["attempts"] += [att(n, n) for n in range(5, 9)]
check("the 2,300 envelope sees live worst cases and settled charges together",
      "production envelope" in PA.budget_problem(heavy, "prod-e2", WORST, rel, time.time()), PA.budget(heavy)["production_usd"])

# ---- 4. epoch-2 bounds -----------------------------------------------------------------------------------------------------
cheap = lambda k: {"prod-e2": {"attempts": [rec(n, n, usd_h=1.0) for n in range(1, k + 1)]}}
check("within the base: attempt 46 admits", PA.epoch2_problem(cheap(45), "prod-e2", WORST, FUND) == "")
check("extra batches 47..50 admit inside the allowance", PA.epoch2_problem(cheap(49), "prod-e2", WORST, FUND) == "")
check("a 51st production attempt (base 46 + 4 extra) refuses", "base 46 + 4 extra" in PA.epoch2_problem(cheap(50), "prod-e2", WORST, FUND))
r50 = cheap(49); r50["prod-e2"]["attempts"] += [att(k, 100 + k, state="rejected") for k in range(3)]
check("rejected attempts do not use the count", PA.epoch2_problem(r50, "prod-e2", WORST, FUND) == "")
q = {"qual-E2Q1": {"attempts": [rec(1, 1, contract="E2Q1")]}, "qual-E2Q2": {"attempts": [rec(1, 2, contract="E2Q2")]}}
check("two qualification instances fit; a third refuses", PA.epoch2_problem({"qual-E2Q1": q["qual-E2Q1"]}, "qual-E2Q2", WORST, FUND) == ""
      and "qualification instance" in PA.epoch2_problem(q, "qual-E2Q3", WORST, FUND))
check("worst case of 2 qualification + 4 extra batches = 6 x 27.92 = 167.51 <= 300 (the counters bind before the money at worst case)",
      6 * WORST <= PA.E2_ALLOWANCE_USD)
pricey = {"qual-E2Q1": {"attempts": [rec(1, 1, contract="E2Q1", usd_h=140 / 1.214)]}, "qual-E2Q2": {"attempts": [rec(1, 2, contract="E2Q2", usd_h=140 / 1.214)]}}
pricey.update(cheap(46))
check("allowance money: 2 qualification attempts charged ~281 refuse an extra batch whose worst would pass 300",
      "allowance" in PA.epoch2_problem(pricey, "prod-e2", WORST, FUND))
check("... while the base batches themselves are not allowance spend", PA.epoch2_problem({k: v for k, v in pricey.items()} | cheap(30), "prod-e2", WORST, FUND) == "")
big = {"prod-e2": {"attempts": [rec(n, n, usd_h=46.0 / 1.214) for n in range(1, 46)]}}
check("epoch cap: base batches charged far above the forecast refuse when the epoch would pass forecast + allowance",
      "epoch 2 cap" in PA.epoch2_problem(big, "prod-e2", WORST, FUND), PA.epoch2_problem(big, "prod-e2", WORST, FUND))
check("budget_problem: an epoch-2 qualification run has no per-part ceiling (bounded by epoch2_problem); an undeclared part refuses",
      PA.budget_problem({}, "qual-E2Q1", WORST, rel, time.time()) == "" and "no declared" in PA.budget_problem({}, "qual-X", WORST, rel, time.time()))
for name, edit in (("fleet ceiling 6", lambda f: f.update(fleet_ceiling=6)), ("allowance 400", lambda f: f.update(allowance_usd=400.0)),
                   ("base batches 47", lambda f: f.update(base_batches=47)), ("epoch cap 2,300", lambda f: f.update(epoch_cap_usd=2300.0)),
                   ("a cheaper Q2 basis", lambda f: f["forecast"]["basis"].update(q2_charged_usd=1.0))):
    t = copy.deepcopy(FUND); edit(t)
    check(f"funding tamper refuses: {name}", PA.funding_problem(t, E2) != "")

# ---- 5. crash rule and ack with unproduced ---------------------------------------------------------------------------------
c1, c2 = OWN[0], OWN[1]
k1, k2 = f"{c1[0]}/{c1[1]}", f"{c2[0]}/{c2[1]}"
def acked(n, seq, unprod):
    return rec(n, seq, coords=[c1, c2], ingestion="ingested", ingest_ack=dict(entry_sha256="x", unproduced=unprod))
h = {"prod-e2": {"attempts": [acked(1, 1, {k1: dict(slot=0, outcome=139)})]}}
check("one fatal crash does not exclude (the coordinate is re-allocated)", PA.ec2_crash_excluded(h) == set() and c1 in PA.allocate(E2, h, set(), 72))
CENS = "censored at the upload deadline"
h["prod-e2"]["attempts"].append(acked(2, 2, {k1: dict(slot=3, outcome=137), k2: dict(slot=4, outcome=CENS)}))
check("two same-envelope fatal crashes (SIGSEGV, OOM SIGKILL) exclude it: never a third identical attempt", PA.ec2_crash_excluded(h) == {c1})
check("a deadline-censored slot does not count as a crash", c2 not in PA.ec2_crash_excluded(h))
h2 = copy.deepcopy(h); h2["prod-e2"]["attempts"][1]["lifetime_s"] = 50000
check("crashes in another envelope (lifetime) do not add up", PA.ec2_crash_excluded(h2) == set())
h3 = copy.deepcopy(h); h3["prod-e2"]["attempts"][1]["ingest_ack"]["unproduced"][k1]["outcome"] = 1
check("a non-signal exit (1) is not a fatal allocation/signal crash", PA.ec2_crash_excluded(h3) == set())
check("the allocator skips the crash-excluded coordinate when the launcher passes it", c1 not in PA.allocate(E2, h, set(), 72, PA.ec2_crash_excluded(h)))
L.save("prod-e2", {"run": "prod-e2", "attempts": [rec(1, 1, coords=[c1, c2])]})
reg = dict(schema=ES.REGISTER_SCHEMA, attempts={"ec2-x-a1": dict(state="ingested", key="prod-e2/1", sequence=1, plan_sha256="p",
                                                               coordinates={k1: {}}, unproduced={k2: dict(slot=1, outcome=139)})})
rp = os.path.join(TMP, "register.json"); json.dump(reg, open(rp, "w"))
bad = copy.deepcopy(reg); bad["attempts"]["ec2-x-a1"]["unproduced"] = {}; bp = os.path.join(TMP, "bad.json"); json.dump(bad, open(bp, "w"))
try:
    PA.ack("prod-e2", 1, bp); check("ack refuses when published + unproduced miss an owned coordinate", False)
except ValueError:
    check("ack refuses when published + unproduced miss an owned coordinate", True)
both = copy.deepcopy(reg); both["attempts"]["ec2-x-a1"]["unproduced"] = {k1: dict(slot=0, outcome=139), k2: dict(slot=1, outcome=139)}
bp2 = os.path.join(TMP, "both.json"); json.dump(both, open(bp2, "w"))
try:
    PA.ack("prod-e2", 1, bp2); check("ack refuses a coordinate listed both published and unproduced", False)
except ValueError:
    check("ack refuses a coordinate listed both published and unproduced", True)
check("ack releases published + unproduced and records the unproduced exits", PA.ack("prod-e2", 1, rp) is True
      and L.load("prod-e2")["attempts"][0]["ingest_ack"]["unproduced"] == {k2: dict(slot=1, outcome=139)}
      and PA.owned(PA.ledgers()) == {})
check("after the ack the unproduced coordinate is allocatable again (one crash), the published one is not (completed)",
      c2 in PA.allocate(E2, PA.ledgers(), {c1}, 72) and c1 not in PA.allocate(E2, PA.ledgers(), {c1}, 72))
check("the crash history now carries the acknowledged exit", PA.ec2_crash_history(PA.ledgers())[c2][0]["exit"] == 139)

# ---- 6. the launcher's plan and epoch gate ---------------------------------------------------------------------------------
lengau_done = {tuple(c) for c in json.load(open(os.path.join(CAND, "claims_snapshot_e2.json")))["lengau_done"]}
work, dup, sent = PL.build("production", E2, {}, lengau_done, "tok-1")
check("production plan under e2: 72 work coordinates replicate-complete from the owned set, 4 Lengau sentinels, no duplicates",
      work == OWN[:72] and dup == [] and len(sent) == 4 and all(s in lengau_done and not RP.blocked(E2, *s) for s in sent))
plan = dict(attempt_id="ec2-prod-e2-a1", sequence=1, contract="production", partition_sha256="p" * 64, opmanifest_sha256="o" * 64,
            activation_sha256="a" * 64, slots=[dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in
                                               enumerate([("work", x) for x in work] + [("sentinel", x) for x in sent])])
view = dict(attempt_id="ec2-prod-e2-a1", sequence=1, coordinates=[list(x) for x in work], sentinels=[list(x) for x in sent], duplicates=[])
check("the 76-slot plan passes the unchanged plan contract (row19_ec2_state.plan_problem)",
      len(plan["slots"]) == 76 and ES.plan_problem(plan, "production", view, "p" * 64, "o" * 64, "a" * 64) == "")
lw, _, _ = PL.build("production", E2, {"prod-e2": {"attempts": [att(n, n, coords=OWN[(n - 1) * 72:n * 72]) for n in range(1, 46)]}}, lengau_done, "tok-2")
check("the 46th batch is the partial final batch of 34 work coordinates (+4 sentinels = 38 slots)", lw == OWN[45 * 72:] and len(lw) == 34)
check("the launcher's epoch gate reads and validates the funding declaration", PL.epoch_problem(E2, {}, "prod-e2", WORST) == "")
PA.E2_FUNDING = os.path.join(TMP, "nofund.json")
check("... and refuses an epoch-2 admission without it", "funding declaration" in PL.epoch_problem(E2, {}, "prod-e2", WORST))
PA.E2_FUNDING = FUND_PATH
check("a schema-1 epoch is not subject to the epoch-2 gate", PL.epoch_problem(E1, cheap(60), "prod-e1", WORST) == "")
check("the launcher admission calls the fleet and epoch gates after the existing envelopes (source wiring)",
      "PA.budget_problem(leds, run, worst, rel, now) or PA.fleet_problem(leds) or epoch_problem(part, leds, run, worst)" in open(PL.__file__).read())
shutil.rmtree(TMP)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
