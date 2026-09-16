"""Independent check of the per-setting reference-inclusion rates, and of the bank-based rates.

Read-only over saved rows; no fits. Written to verify, not to trust, the figures in Codex's record
(`2026-09-16_si_approved_framing_codex_record.md`, RSC 226024e), because they are going into the manuscript.

Per graded setting it computes, from `sim_results/d4v12b/calibration_D4.csv`:
  reference   the setting's own replicate mean of the primary (selection) point estimate - a SAME-SAMPLE estimate;
  inclusion   the fraction of that setting's 95 % concept-cluster intervals that contain that reference.
These are candidate-reference inclusion rates, not known-population coverage probabilities.

For M2S omega = 2 it also reports the independent-seed bank references from the paper's figure data
(`figures/t1_omega2_bank_data.csv`, exported from ref_m2s_omega2_aac9f69): the bank mean, its median, and its mean
after removing the single most extreme dataset, with the inclusion rate of each.

Run: python3 reference_inclusion_check.py
"""
import collections
import csv
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.normpath(os.path.join(HERE, "..", "..", "sim_results", "d4v12b", "calibration_D4.csv"))
BANK = "/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/figures/t1_omega2_bank_data.csv"

rows = list(csv.DictReader(open(CAL, newline="")))
assert len(rows) == 12000, len(rows)
by_setting = collections.defaultdict(list)
for r in rows:
    by_setting[(r["generator"], r["grid"])].append(r)

print(f"{'setting':<34} {'n':>5} {'reference':>12} {'inclusion':>10}   below 0.90")
below = []
for key in sorted(by_setting):
    rs = by_setting[key]
    pts = [float(r["selection_ws_point"]) for r in rs]
    ref = sum(pts) / len(pts)
    inc = sum(1 for r in rs if float(r["selection_ws_lo"]) <= ref <= float(r["selection_ws_hi"])) / len(rs)
    flag = "  <-- below" if inc < 0.90 else ""
    if inc < 0.90:
        below.append((f"{key[0]} {key[1]}", inc))
    print(f"{key[0] + ' ' + key[1]:<34} {len(rs):>5} {ref:>12.6f} {inc:>10.3f}{flag}")

print(f"\n{len(below)} settings below the 0.90 floor: " + ", ".join(f"{n} {v:.3f}" for n, v in below))
print("range of the below-floor rates: "
      f"{min(v for _, v in below):.3f} to {max(v for _, v in below):.3f}")

# The hardest null against the independent-seed bank.
w2 = by_setting[("M2S", '{"omega": 2.0}')]
lo = [float(r["selection_ws_lo"]) for r in w2]
hi = [float(r["selection_ws_hi"]) for r in w2]
brows = [r for r in csv.DictReader(open(BANK, newline="")) if r["source"] == "bank"]
bank = sorted(float(r["point"]) for r in brows)
assert len(bank) == 1000, len(bank)
bank_mean = sum(bank) / len(bank)
bank_se = statistics.stdev(bank) / len(bank) ** 0.5
cands = [("bank mean", bank_mean), ("bank median", statistics.median(bank)),
         ("bank mean without the minimum", sum(bank[1:]) / len(bank[1:])),
         ("d4v12b own replicate mean", sum(float(r["selection_ws_point"]) for r in w2) / len(w2))]
print(f"\nM2S omega = 2: independent bank of {len(bank)} datasets, mean {bank_mean:.6f}, sample SE {bank_se:.6f}, "
      f"median {statistics.median(bank):.6f}, minimum {min(bank):,.3f}")
for name, val in cands:
    inc = sum(1 for a, b in zip(lo, hi) if a <= val <= b) / len(lo)
    print(f"  {name:<32} {val:>12.6f}   inclusion {inc:.3f}")
