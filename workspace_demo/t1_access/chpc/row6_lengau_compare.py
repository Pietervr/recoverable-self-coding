"""Ledger row 6 on Lengau: compare the Lengau re-run rows against the stored AWS sens600 rows of the same three
datasets. Prints only the maximum |delta| per quantity and a decision-agreement boolean - never which decision a
setting returned - so sens600 stays blinded. Tolerance 1e-6 nat/trial, declared 17 September."""
import csv, json, sys, os
T1 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
AWS = os.path.join(T1, "sim_results/sens600/power_D4.csv")
LENGAU = sys.argv[1] if len(sys.argv) > 1 else os.path.join(T1, "chpc/results/row6_lengau_rows.csv")
NUM = ("selection_ws_point", "selection_ws_lo", "selection_ws_hi", "selection_ws_se")
TOL = 1e-6
SCALE = 0.5465000938917843

aws = [r for r in csv.DictReader(open(AWS))
       if r["generator"] == "M3" and abs(json.loads(r["grid"]).get("scale", 0) - SCALE) < 1e-12 and int(r["rep"]) in (0, 20, 40)]
aws = {int(r["rep"]): r for r in aws}
len_rows = {int(r["rep"]): r for r in csv.DictReader(open(LENGAU))}
assert sorted(aws) == [0, 20, 40] == sorted(len_rows), (sorted(aws), sorted(len_rows))
for rp in (0, 20, 40):
    assert aws[rp]["code_hash"] == len_rows[rp]["code_hash"] == "625798e9e7f4", "code hash mismatch"

worst = {q: 0.0 for q in NUM}
decisions_identical = True
failures = []
for rp in (0, 20, 40):
    a, m = aws[rp], len_rows[rp]
    for q in NUM:
        if a.get(q, "") == "" or m.get(q, "") in ("", "None"):
            failures.append(f"{q} missing on rep {rp}"); continue
        worst[q] = max(worst[q], abs(float(a[q]) - float(m[q])))
    if str(a["selection_decision"]) != str(m["selection_decision"]):
        decisions_identical = False
    if str(m.get("failed", "0")) not in ("0", "False", "false"):
        failures.append(f"lengau rep {rp} failed={m['failed']} reason={m.get('failed_reason')}")

print("ROW 6 PARITY PANEL - x86_64 Haswell (Lengau, the pinned cloud library set) against x86_64 Xeon 6 (AWS), one code hash")
print(f"  datasets compared:      3")
for q in NUM:
    print(f"  max |delta| {q:<22} {worst[q]:.3e} nat/trial")
print(f"  decisions identical:    {decisions_identical}")
print(f"  technical failures:     {failures if failures else 'none'}")
print(f"  lengau environment:     {next(iter(len_rows.values()))['env']}")
ok = all(worst[q] <= TOL for q in NUM) and decisions_identical and not failures
print(f"\n  tolerance 1e-6 nat/trial on every quantity, decisions identical")
print(f"  VERDICT: {'PASS - Lengau and AWS rows agree within tolerance on this cluster-mode panel' if ok else 'FAIL - Lengau rows may NOT be pooled with the published ones'}")
print("\n  (Which decision each setting returned is deliberately not printed: sens600 stays blinded. This cluster-mode panel")
print("   does not license refit pooling - Codex, RSC 052f156 - which needs its own refit-specific panel.)")
