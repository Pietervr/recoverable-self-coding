"""Unit tests of prod_authority (Codex 0483db4 V10-2/V10-6): global allocation/ownership/fencing across runs and epochs,
sentinels, every budget envelope (production across epochs, cumulative with the moving baseline, per-part qualification
ceilings with the owner's acceptance), ack/disposition, the sealed inventory. No AWS; a temporary authority directory.
    python3 tests/test_prod_authority.py"""
import copy, json, os, sys, shutil, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); sys.path[:0] = [PKG, os.path.join(PKG, "..", "chpc")]
import prod_authority as PA, bench_launch as L, row19_partition as RP, row19_ec2_state as ES
TMP = tempfile.mkdtemp()
for f in ("budget_baseline.json", "ec2_release_state.json"):
    shutil.copy(os.path.join(PKG, f), os.path.join(TMP, f))
L.HERE = PA.HERE = TMP
PA.LOCK, PA.STATE = os.path.join(TMP, "runs", ".authority.lock"), os.path.join(TMP, "runs", ".authority_state.json")
PA.INV_DIR, PA.RELEASE_STATE = os.path.join(TMP, "runs", "inventory"), os.path.join(TMP, "ec2_release_state.json")
man_path = os.path.join(PKG, "..", "chpc", "row19_screen_manifest.json"); man = json.load(open(man_path))
part = RP.declare(man, RP.sha_file(man_path), 2, 1)                    # block = indices 198, 199
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))
def att(n, seq, state="launched", coords=(), ingestion="pending", **kw):
    return dict(dict(attempt=n, sequence=seq, attempt_id=f"a{n}", state=state, ingestion=ingestion, contract="production", plan_sha256="p",
                     coordinates=[list(c) for c in coords], lifetime_s=79200, max_price=1.20, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD), **kw)
def save(run, atts):
    L.save(run, {"run": run, "attempts": atts})

leds = {}
a1 = PA.allocate(part, leds, set(), 72)
check("fixed order: index 199 first, reps ascending", a1[:2] == [(3, 199), (4, 199)])
check("allocation stays inside the block", all(RP.blocked(part, *c) for c in PA.allocate(part, leds, set(), 500)))
leds = {"prod-e1": {"attempts": [att(1, 1, coords=a1)]}}
check("a live attempt's coordinates are never re-allocated", not set(a1) & set(PA.allocate(part, leds, set(), 72)))
leds2 = {"prod-e1": {"attempts": [att(1, 1, coords=a1)]}, "prod-e2": {"attempts": []}}
check("ownership is global across epochs (another epoch's run cannot allocate them)", not set(a1) & set(PA.allocate(part, leds2, set(), 200)))
leds = {"qual-Q1": {"attempts": [att(1, 1, coords=a1)]}}
check("a qualification attempt owns its block coordinates against production", not set(a1) & set(PA.allocate(part, leds, set(), 200)))
leds = {"b2": {"attempts": [att(1, 1, coords=a1)]}}
check("a benchmark run never owns", set(a1) <= set(PA.allocate(part, leds, set(), 200)))
leds = {"prod-e1": {"attempts": [att(1, 1, state="rejected", coords=a1)]}}
check("a rejected attempt releases its coordinates", PA.allocate(part, leds, set(), 1)[0] == (3, 199))
leds = {"prod-e1": {"attempts": [att(1, 1, state="reconciled", coords=a1, terminal=dict(compute_s=3600, ancillary_s=3600))]}}
check("a reconciled but not-ingested attempt still owns (pending output)", (3, 199) not in PA.allocate(part, leds, set(), 200))
leds["prod-e1"]["attempts"][0]["ingestion"] = "dispositioned"
leds["prod-e1"]["attempts"].append(att(2, 5, coords=[(3, 199)]))
check("fence = highest sequence ever assigned (a dispositioned writer is below it)", PA.fence(leds)["3/199"] == 5 and PA.owner_of(leds, (3, 199)) == ("prod-e1/2", 5))
leds = {"prod-e1": {"attempts": [att(1, 1, coords=[(3, 199)])]}, "prod-e2": {"attempts": [att(1, 2, coords=[(3, 199)])]}}
try:
    PA.owned(leds); check("double ownership across runs raises", False)
except RuntimeError:
    check("double ownership across runs raises", True)
pool = {(r, i) for r in range(3, 30) for i in range(3)}
s1 = PA.sentinels(pool, "tokA")
check("sentinels deterministic per token, distinct, from the pool, never from the excluded set",
      s1 == PA.sentinels(pool, "tokA") and len(set(s1)) == 4 and set(s1) <= pool and PA.sentinels(pool, "tokB") != s1
      and not set(PA.sentinels(pool, "tokA", exclude=s1)) & set(s1))

# budget
check("Q1 and Q2 worst of one attempt each are inside the declared ceilings 28 / 17",
      PA.worst_usd(PA.QUAL_LIFETIME_S, 1.20) <= 28 and PA.worst_usd(PA.QUAL_LIFETIME_S, 0.70) <= 17,
      (PA.worst_usd(PA.QUAL_LIFETIME_S, 1.20), PA.worst_usd(PA.QUAL_LIFETIME_S, 0.70)))
check("... and the honest worst exceeds the USD 43 declared on 10 Oct (owner acceptance needed)",
      PA.worst_usd(PA.QUAL_LIFETIME_S, 1.20) + PA.worst_usd(PA.QUAL_LIFETIME_S, 0.70) > 43)
now = time.time(); b0 = PA.baseline(now)
check("the baseline is a moving bound (idle accrual per started day)", PA.baseline(now + 2 * 86400) - b0 >= 2 * 5.5 - 1e-9 and b0 >= 500)
rel = PA.release_state()
check("budget: a 27 USD production attempt passes", PA.budget_problem({}, "prod-e1", 27.0, rel, now) == "")
many = {f"prod-e{k}": {"attempts": [att(1, k)]} for k in range(1, 40)} | {"qual-Q1": {"attempts": [att(1, 99)]}}
check("budget: the production envelope sums every epoch and the qualification", "production envelope" in PA.budget_problem(many, "prod-e40", 1200.0, rel, now))
check("budget: the cumulative cap includes the baseline and every run (row 23 too)",
      "cumulative cap" in PA.budget_problem({"b2": {"attempts": [dict(attempt=1, state="launched", lifetime_s=77400, max_price=1.20)]}}, "b2", 3000.0 - b0 - 10, rel, now))
unaccepted = copy.deepcopy(rel); unaccepted["qualification"]["owner_accepted_ceilings"] = False
check("budget: qualification refused until the owner accepts the ceilings", "not accepted" in PA.budget_problem({}, "qual-Q1", 27.9, unaccepted, now))
rel2 = json.loads(json.dumps(rel)); rel2["qualification"]["owner_accepted_ceilings"] = True
check("budget: Q1 within its ceiling once accepted", PA.budget_problem({}, "qual-Q1", 27.9, rel2, now) == "")
check("budget: a Q1 retry beyond the ceiling is refused (retries count)",
      "Q1 ceiling" in PA.budget_problem({"qual-Q1": {"attempts": [att(1, 1, state="reconciled", terminal=dict(compute_s=36000, ancillary_s=36000))]}}, "qual-Q1", 27.9, rel2, now))
check("release state: nothing released while no backed evidence exists", not rel["row23"]["ok"] and not rel["qualification"]["ok"] and not rel["production"]["ok"])

# inventory, ack, disposition (on disk, under the authority lock)
seqs = []
with PA.authority_lock():
    st, s = PA.bump(PA.state(), sequences=1); seqs.append(s); st, s = PA.bump(st, sequences=1); seqs.append(s)
check("global sequences are unique and increasing; generation advances", seqs == [1, 2] and PA.state()["generation"] == 3)
save("prod-e1", [att(1, 1, state="reconciled", coords=[(3, 199), (4, 199)], terminal=dict(compute_s=3600, ancillary_s=3600))])
save("b2", [dict(attempt=1, state="reconciled", lifetime_s=1, max_price=1.2, terminal=dict(compute_s=3600, ancillary_s=3600))])
with PA.authority_lock():
    ip = PA.write_inventory()
inv = json.load(open(ip))
check("the sealed inventory passes its own contract and carries the production attempt, not the benchmark",
      ES.inventory_problem(inv) == "" and list(inv["attempts"]) == ["prod-e1/1"] and inv["owners"]["3/199"] == ["prod-e1/1", 1])
reg = dict(schema=ES.REGISTER_SCHEMA, attempts={"a1": dict(state="ingested", key="prod-e1/1", sequence=1, plan_sha256="p", coordinates={"3/199": {}, "4/199": {}})})
rp = os.path.join(TMP, "register.json"); json.dump(reg, open(rp, "w"))
bad = json.loads(json.dumps(reg)); bad["attempts"]["a1"]["coordinates"].pop("4/199"); bp = os.path.join(TMP, "bad.json"); json.dump(bad, open(bp, "w"))
try:
    PA.ack("prod-e1", 1, bp); check("ack refuses a register entry with other coordinates", False)
except ValueError:
    check("ack refuses a register entry with other coordinates", True)
check("ack releases the attempt on the register's ingested entry", PA.ack("prod-e1", 1, rp) is True and L.load("prod-e1")["attempts"][0]["ingestion"] == "ingested")
check("ack is idempotent on the same entry", PA.ack("prod-e1", 1, rp) is False)
reg["attempts"]["a1"]["coordinates"]["3/199"] = {"x": 1}; json.dump(reg, open(rp, "w"))
try:
    PA.ack("prod-e1", 1, rp); check("ack refuses a different entry after acknowledgement", False)
except ValueError:
    check("ack refuses a different entry after acknowledgement", True)
check("an ingested attempt no longer owns", PA.owned(PA.ledgers()) == {})
save("prod-e1", L.load("prod-e1")["attempts"] + [att(2, 3, state="launched", coords=[(5, 199)])])
try:
    PA.disposition("prod-e1", 2, "x"); check("disposition refuses an unreconciled attempt", False)
except ValueError:
    check("disposition refuses an unreconciled attempt", True)
print("ALL PASS" if ok else "SOME FAILED"); shutil.rmtree(TMP); sys.exit(0 if ok else 1)
