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

# R1-2: disposition is a REQUEST; ownership is released only on the root's acknowledgement of the fence
save("prod-e1", [x for x in L.load("prod-e1")["attempts"] if x["attempt"] != 2] +
       [att(2, 3, state="reconciled", coords=[(5, 199)], terminal=dict(compute_s=60, ancillary_s=60))])
check("R1-2 a disposition request is recorded", PA.disposition("prod-e1", 2, "no output") is True)
check("R1-2 ... and the attempt still owns its coordinate until the root acknowledges", PA.owner_of(PA.ledgers(), (5, 199)) == ("prod-e1/2", 3))
with PA.authority_lock():
    PA.bump(PA.state()); ip = PA.write_inventory()
inv = json.load(open(ip))
check("R1-2 the inventory carries the request and keeps the owner", inv["attempts"]["prod-e1/2"]["disposition_requested"] is True
      and inv["owners"]["5/199"] == ["prod-e1/2", 3] and ES.inventory_problem(inv) == "")
root = os.path.join(TMP, "lroot"); PA.CANONICAL_ROOT = root
CANON = dict(root=os.path.abspath(root), manifest_sha256=PA.PROD_SHA, mode="canonical")
ack, probs = ES.install_inventory(root, inv, CANON)
ackp = ES.ack_path(root, inv["generation"])
check("R1-2 the root fences the request at installation (register entry dispositioned) and acknowledges it",
      probs == [] and "prod-e1/2" in ack["dispositioned"] and json.load(open(ES.paths(root)["register"]))["attempts"]["a2"]["state"] == "dispositioned")
forged = dict(json.load(open(ackp)), inventory_sha256="0" * 64); fp = os.path.join(TMP, "forged.json"); json.dump(forged, open(fp, "w"))
try:
    PA.disposition_confirm("prod-e1", 2, fp); check("R1-2 confirm refuses an acknowledgement of an inventory this authority did not seal", False)
except ValueError:
    check("R1-2 confirm refuses an acknowledgement of an inventory this authority did not seal", True)
check("R1-2 confirm releases ownership on the genuine acknowledgement", PA.disposition_confirm("prod-e1", 2, ackp) is True
      and PA.owner_of(PA.ledgers(), (5, 199)) is None)
check("R1-2 confirm is idempotent on the same acknowledgement", PA.disposition_confirm("prod-e1", 2, ackp) is False)
save("prod-e1", L.load("prod-e1")["attempts"] + [att(3, 7, state="reconciled", coords=[(6, 199)], terminal=dict(compute_s=60, ancillary_s=60))])
PA.disposition("prod-e1", 3, "x")
with PA.authority_lock():
    PA.bump(PA.state()); inv3 = json.load(open(PA.write_inventory()))
reg = json.load(open(ES.paths(root)["register"])); reg["attempts"]["a3"] = dict(attempt_id="a3", key="prod-e1/3", sequence=7, state="ingesting", coordinates={})
json.dump(reg, open(ES.paths(root)["register"], "w"))
ack3, _ = ES.install_inventory(root, inv3, CANON)
try:
    PA.disposition_confirm("prod-e1", 3, ES.ack_path(root, inv3["generation"])); check("R1-2 a root refusal (output being ingested) keeps the attempt owning", False)
except ValueError as e:
    check("R1-2 a root refusal (output being ingested) keeps the attempt owning", "REFUSED" in str(e) and PA.owner_of(PA.ledgers(), (6, 199)) == ("prod-e1/3", 7))

# R2-1: every seal is a new generation, archives are write-once, refresh/state change/delayed acknowledgement install
with PA.authority_lock():
    g0 = PA.state()["generation"]; pa_ = PA.write_inventory(); pb_ = PA.write_inventory()
ga, gb = json.load(open(pa_))["generation"], json.load(open(pb_))["generation"]
check("R2-1 two seals are two generations, each archived separately", gb == ga + 1 and ga > g0 and pa_ != pb_ and os.path.exists(pa_))
before = open(pa_).read()
st_ = json.load(open(PA.STATE)); json.dump(dict(st_, generation=ga - 1), open(PA.STATE, "w"))    # an authority state behind its archives
try:
    with PA.authority_lock():
        PA.write_inventory()
    check("R2-1 an existing generation archive is never overwritten", False)
except RuntimeError as e:
    check("R2-1 an existing generation archive is never overwritten", "immutable" in str(e) and open(pa_).read() == before)
json.dump(st_, open(PA.STATE, "w"))
cur = json.load(open(ES.paths(root)["inventory"]))
_, probs = ES.install_inventory(root, json.load(open(pa_)), CANON); _, probs2 = ES.install_inventory(root, json.load(open(pb_)), CANON)
check("R2-1 a refresh after an earlier installation installs (new generations, not a reseal of an installed one)", probs == [] and probs2 == [])
_, probs3 = ES.install_inventory(root, json.load(open(pa_)), CANON)
check("R2-1 the root still refuses an older generation after a newer one", probs3 and "older" in probs3[0])
same = json.load(open(pb_)); same["at"] = same["at"] + 1; same = ES.seal(same)
_, probs4 = ES.install_inventory(root, same, CANON)
check("R2-1 the root still refuses different bytes at an installed generation", probs4 and "other bytes" in probs4[0])
# launch -> reconciled: the reconciled view is a new generation and installs
L.save("prod-e9", {"run": "prod-e9", "attempts": [att(1, 60, state="launched", coords=[(9, 199)])]})
with PA.authority_lock():
    pl_ = PA.write_inventory()
led9 = L.load("prod-e9"); led9["attempts"][0].update(state="reconciled", terminal=dict(compute_s=60, ancillary_s=60)); L.save("prod-e9", led9)
with PA.authority_lock():
    pr_ = PA.write_inventory()
_, p1 = ES.install_inventory(root, json.load(open(pl_)), CANON); _, p2 = ES.install_inventory(root, json.load(open(pr_)), CANON)
check("R2-1 launch view then reconciled view install as successive generations",
      p1 == [] and p2 == [] and json.load(open(ES.paths(root)["inventory"]))["attempts"]["prod-e9/1"]["state"] == "reconciled")
# delayed acknowledgement after a refresh: the request's generation archive stays checkable
PA.disposition("prod-e9", 1, "no output")
with PA.authority_lock():
    pd_ = PA.write_inventory()
ackd, pd = ES.install_inventory(root, json.load(open(pd_)), CANON)
with PA.authority_lock():
    pf_ = PA.write_inventory()                                             # a refresh before the Mac reads the acknowledgement
ES.install_inventory(root, json.load(open(pf_)), CANON)
check("R2-1 a delayed acknowledgement confirms after a refresh (its generation archive is immutable)",
      pd == [] and PA.disposition_confirm("prod-e9", 1, ES.ack_path(root, ackd["generation"])) is True)
# root identity: a sandbox or another root's acknowledgement never releases
L.save("prod-e8", {"run": "prod-e8", "attempts": [att(1, 70, state="reconciled", coords=[(8, 199)], terminal=dict(compute_s=60, ancillary_s=60))]})
PA.disposition("prod-e8", 1, "x")
with PA.authority_lock():
    ps_ = PA.write_inventory()
sroot = os.path.join(TMP, "s_root")
acks, _ = ES.install_inventory(sroot, json.load(open(ps_)), dict(root=os.path.abspath(sroot), manifest_sha256="e" * 64, mode="sandbox"))
try:
    PA.disposition_confirm("prod-e8", 1, ES.ack_path(sroot, acks["generation"])); check("R2-1 an isolated/sandbox root's acknowledgement never releases", False)
except ValueError as e:
    check("R2-1 an isolated/sandbox root's acknowledgement never releases", "canonical" in str(e) and PA.owner_of(PA.ledgers(), (8, 199)) == ("prod-e8/1", 70), str(e))
_, why_id = ES.install_inventory(sroot, json.load(open(ps_)), dict(root=os.path.abspath(root), manifest_sha256="e" * 64, mode="canonical"))
check("R2-1 an installation naming another root than its own is refused", why_id and "names root" in why_id[0])
shutil.rmtree(L.run_dir("prod-e8")); shutil.rmtree(L.run_dir("prod-e9"))

# R1-4: release adoption from a validated certificate and a pinned favourable review
import hashlib
PA.controls_partition_sha = lambda: "p" * 64
code = {f: L.sha256(os.path.join(PA.T1, f)) for f in PA.RELEASE_CODE}
L.save("qual-Q1", {"run": "qual-Q1", "attempts": [att(1, 50, state="reconciled", plan_sha256="q1plan", attempt_id="ec2-qual-Q1-a1",
                                                       terminal=dict(compute_s=60, ancillary_s=60))]})
def cert(**kw):
    c = dict(schema=PA.CERT_SCHEMA, outcome="RELEASE", problems=[], coverage_short={}, parts={"R1": dict(successful_both=20), "R2": dict(successful_both=40),
             "R3": dict(successful_both=20)}, memory=dict(samples_at_full_packing=30, peak_host_used_gib=170.0), replay=dict(final_state="ingested",
             hashes_equal=True, scope="x"), released_attempts=["qual-Q1/1"], q1=dict(key="qual-Q1/1", attempt_id="ec2-qual-Q1-a1", sequence=50, plan_sha256="q1plan"),
             bound=dict(code=code, manifest_sha256=PA.PROD_SHA, partition_sha256="p" * 64, plans={"Q1": "q1plan"}))
    for k, v in kw.items():
        c[k] = v
    cp = os.path.join(TMP, "cert.json"); json.dump(c, open(cp, "w")); return cp
def review(cp, verdict="FAVOURABLE", keys="qual-Q1/1"):
    rp = os.path.join(TMP, "review.md")
    open(rp, "w").write(f"# actual-result review\n{verdict}\nRELEASE row19-ec2-qualification certificate={L.sha256(cp)} attempts={keys}\n"); return rp
cp = cert(); check("R1-4 a valid certificate with its favourable review releases exactly Q1", PA.release_problem(cp, review(cp)) == (["qual-Q1/1"], ""))
cp = cert(); rp = review(cp, verdict="pending"); check("R1-4 a review without FAVOURABLE refuses", PA.release_problem(cp, rp)[1] != "")
cp = cert(); rp = review(cp); os.remove(rp); check("R1-4 a missing review refuses", PA.release_problem(cp, rp)[1] != "")
cp = cert(); rp = review(cp, keys="qual-Q1/2"); check("R1-4 a review naming other attempts refuses", PA.release_problem(cp, rp)[1] != "")
cp = cert(bound=dict(code=dict(code, **{"chpc/row19_ec2_state.py": "0" * 64}), manifest_sha256=PA.PROD_SHA, partition_sha256="p" * 64, plans={"Q1": "q1plan"}))
check("R1-4 a certificate bound to other code bytes refuses (stale)", "current bytes" in PA.release_problem(cp, review(cp))[1])
cp = cert(bound=dict(code={k: v for k, v in code.items() if k != "chpc/row19_shard.py"}, manifest_sha256=PA.PROD_SHA, partition_sha256="p" * 64, plans={"Q1": "q1plan"}))
check("R2 a certificate binding less than the declared qualification code set refuses", "code set" in PA.release_problem(cp, review(cp))[1])
cp = cert(bound=dict(code=code, manifest_sha256=PA.PROD_SHA, partition_sha256="e" * 64, plans={"Q1": "q1plan"}))
check("R1-4 a certificate of another partition refuses (a later epoch needs its own release)", "partition" in PA.release_problem(cp, review(cp))[1])
cp = cert(released_attempts=["qual-Q1/1", "prod-e1/1"]); check("R1-4 a certificate releasing more than its Q1 refuses", PA.release_problem(cp, review(cp, keys="qual-Q1/1,prod-e1/1"))[1] != "")
cp = cert(q1=dict(key="qual-Q1/1", attempt_id="ec2-qual-Q1-a1", sequence=50, plan_sha256="other")); check("R1-4 a certificate whose Q1 plan is not the ledger's refuses", PA.release_problem(cp, review(cp))[1] != "")
cp = cert(parts={"R1": dict(successful_both=20), "R2": dict(successful_both=35), "R3": dict(successful_both=20)})
check("R1-4 short finite coverage refuses", "coverage" in PA.release_problem(cp, review(cp))[1])
cp = cert(schema="row19-ec2-qualification-certificate-1"); check("R1-4 a schema-1 certificate refuses", PA.release_problem(cp, review(cp))[1] != "")
cp = cert(); rp = review(cp)
r = json.load(open(PA.RELEASE_STATE)); open(os.path.join(TMP, "r23.json"), "w").write("{}"); open(os.path.join(TMP, "qrec.md"), "w").write("q")
r["row23"] = dict(declared_success=True, report_path="r23.json", report_sha256=L.sha256(os.path.join(TMP, "r23.json")))
r["qualification"].update(permitted=True, record_path="qrec.md", record_sha256=L.sha256(os.path.join(TMP, "qrec.md")))
json.dump(r, open(PA.RELEASE_STATE, "w"))
check("D-2 qualification is not ok without the benchmark cutover fence", not PA.release_state()["qualification"]["ok"])
os.makedirs(os.path.join(TMP, "runs"), exist_ok=True); open(os.path.join(TMP, "runs", "BENCH_FENCE.json"), "w").write("{}")
check("D-2 ... and ok once the fence exists", PA.release_state()["qualification"]["ok"])
check("R1-4 release-adopt writes the production block from the validated certificate", PA.release_adopt("cert.json", "review.md") == ["qual-Q1/1"]
      and PA.release_state()["production"]["ok"] and PA.release_state()["production"]["derived_released_attempts"] == ["qual-Q1/1"])
r = json.load(open(PA.RELEASE_STATE)); r["production"]["released_attempts"] = ["qual-Q1/1", "qual-Q2/1"]; json.dump(r, open(PA.RELEASE_STATE, "w"))
check("R1-4 a release state listing other attempts than its certificate is NOT released", not PA.release_state()["production"]["ok"])
r["production"]["released_attempts"] = ["qual-Q1/1"]; json.dump(r, open(PA.RELEASE_STATE, "w"))
code["chpc/row19_ec2_state.py"] = "1" * 64; cp2 = cert(); r["production"]["certificate_sha256"] = L.sha256(cp2); json.dump(r, open(PA.RELEASE_STATE, "w"))
check("R1-4 an adopted release whose certificate no longer matches the current inputs reads NOT released", not PA.release_state()["production"]["ok"])

# R1-7: exclusion
check("R1-7 a live benchmark attempt excludes production/qualification admission", "benchmark" in PA.exclusion_problem({"b2": {"attempts": [dict(attempt=5, state="launched")]}}, "eu-north-1"))
check("R1-7 a reconciled benchmark attempt does not", PA.exclusion_problem({"b2": {"attempts": [dict(attempt=5, state="reconciled")]}}, "eu-north-1") == "")
check("R1-7 an unresolved attempt in another region excludes", "region" in PA.exclusion_problem({"prod-e1": {"attempts": [dict(attempt=1, state="ambiguous", region="us-west-2")]}}, "eu-north-1"))
import bench_reaper as BR
pa = att(1, 1, state="reconciled", terminal=dict(compute_s=36000, ancillary_s=37000)); pl = att(2, 2, state="launched")
ba = dict(attempt=1, state="reconciled", max_price=1.2, terminal=dict(compute_s=3600, ancillary_s=3600))
check("R1-7 the reaper REPORTS a production/qualification attempt at its own rates (= the authority's charge), a benchmark by the row-23 rule",
      abs(BR.report_charge(pa) - PA.charged(pa)) < 1e-9 and abs(BR.report_charge(pl) - PA.charged(pl)) < 1e-9 and abs(BR.report_charge(ba) - L.charged(ba)) < 1e-9)
print("ALL PASS" if ok else "SOME FAILED"); shutil.rmtree(TMP); sys.exit(0 if ok else 1)
