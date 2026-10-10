"""Unit tests of prod_authority: allocation, ownership/fencing, sentinels, both budget envelopes. No AWS.
    python3 tests/test_prod_authority.py"""
import json, os, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); sys.path[:0] = [PKG, os.path.join(PKG, "..", "chpc")]
import prod_authority as PA, bench_launch as L, row19_partition as RP
man_path = os.path.join(PKG, "..", "chpc", "row19_screen_manifest.json"); man = json.load(open(man_path))
part = RP.declare(man, RP.sha_file(man_path), 2, 1)                    # block = indices 198, 199
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x else ""))
led = {"attempts": []}
a1 = PA.allocate(part, led, set(), 72)
check("fixed order: index 199 first, reps ascending", a1[0] == (3, 199) and a1[99] == (102, 199) if len(a1) > 99 else a1[:2] == [(3, 199), (4, 199)])
check("allocation stays inside the block", all(RP.blocked(part, *c) for c in PA.allocate(part, led, set(), 500)))
led["attempts"].append(dict(attempt=1, sequence=1, state="launched", coordinates=[list(c) for c in a1], ingestion="pending"))
a2 = PA.allocate(part, led, set(), 72)
check("a live attempt's coordinates are never re-allocated", not set(a1) & set(a2))
led["attempts"][0]["state"] = "rejected"
check("a rejected attempt releases its coordinates", PA.allocate(part, led, set(), 1)[0] == (3, 199))
led["attempts"][0].update(state="reconciled", ingestion="pending")
check("a reconciled but not-ingested attempt still owns (pending output)", (3, 199) not in PA.allocate(part, led, set(), 200))
led["attempts"][0]["ingestion"] = "ingested"
done = set(a1)
check("ingested coordinates are completed, never re-allocated", not set(PA.allocate(part, led, done, 200)) & done)
led["attempts"] = [dict(attempt=1, sequence=1, state="launched", coordinates=[[3, 199]]), dict(attempt=2, sequence=2, state="intent", coordinates=[[3, 199]])]
try:
    PA.owned(led); check("double ownership raises", False)
except RuntimeError:
    check("double ownership raises", True)
led["attempts"] = [dict(attempt=1, sequence=1, state="launched", coordinates=[[3, 199]])]
check("owner_of names the attempt and sequence (fencing for late writers)", PA.owner_of(led, (3, 199)) == (1, 1) and PA.owner_of(led, (4, 199)) is None)
pool = {(r, i) for r in range(3, 30) for i in range(3)}
s1, s2 = PA.sentinels(pool, "tokA"), PA.sentinels(pool, "tokA")
check("sentinels deterministic per token, distinct, from the pool", s1 == s2 and len(set(s1)) == 4 and set(s1) <= pool and PA.sentinels(pool, "tokB") != s1)
# budget envelopes
base = PA.baseline()["spent_usd"]
led = {"attempts": []}
check("budget: a 27 USD attempt passes both envelopes", PA.budget_problem(led, "prod-test", 27.0) == "")
check("budget: production envelope enforced", "production envelope" in PA.budget_problem(led, "prod-test", 2301.0))
led = {"attempts": [dict(attempt=k, state="launched", lifetime_s=77400, max_price=1.20) for k in range(1, 90)]}   # unresolved: worst case each
check("budget: unresolved attempts are charged their worst case", "production envelope" in PA.budget_problem(led, "prod-test", 27.0))
PA.PROD_ENVELOPE_USD = 1e9
check("budget: cumulative cap enforced including the baseline and other runs", "cumulative cap" in PA.budget_problem({"attempts": []}, "prod-test", 3000.0 - base + 1))
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
