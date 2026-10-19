"""Exact binomial intervals for the sens600 blinded table, computed from blinded_counts.csv alone.
Run before `blind_read.py reveal`. Prints per-setting Clopper-Pearson intervals and the one-sided
lower bounds the ledger's precision illustrations use. No generator label is read or printed."""
import csv, os
from scipy.stats import beta

CSV = os.path.join(os.path.dirname(__file__), "..", "sim_results", "sens600", "blinded_counts.csv")

def cp(x, n, conf=0.95):
    """Clopper-Pearson two-sided interval."""
    a = 1 - conf
    lo = 0.0 if x == 0 else beta.ppf(a / 2, x, n - x + 1)
    hi = 1.0 if x == n else beta.ppf(1 - a / 2, x + 1, n - x)
    return lo, hi

def cp_lower_one_sided(x, n, conf=0.95):
    return 0.0 if x == 0 else beta.ppf(1 - conf, x, n - x + 1)

rows = list(csv.DictReader(open(CSV)))
print(f"{'id':<4}{'mix/att':>9}{'rate':>8}   exact two-sided 95%      one-sided 95% lower")
worst_lo = 1.0
for r in rows:
    x, n = int(r["mixture"]), int(r["attempted"])
    lo, hi = cp(x, n)
    one = cp_lower_one_sided(x, n)
    worst_lo = min(worst_lo, one)
    print(f"{r['setting_id']:<4}{x:>5}/{n:<3}{x/n:>8.4f}   [{lo:.4f}, {hi:.4f}]        {one:.4f}")

tot_x = sum(int(r["mixture"]) for r in rows)
tot_n = sum(int(r["attempted"]) for r in rows)
print()
print(f"all outcomes, summed over the twelve settings: mixture {tot_x}, "
      f"graded {sum(int(r['graded']) for r in rows)}, "
      f"inconclusive {sum(int(r['inconclusive']) for r in rows)}, "
      f"unavailable {sum(int(r['unavailable']) for r in rows)}, attempted {tot_n}")
print(f"worst individual one-sided 95% lower bound: {worst_lo:.4f}")
print()
print("Precision illustrations from the ledger (NOT pass rules): an individual one-sided exact 95%")
print("lower bound first exceeds 0.8 at 45/50; four simultaneous Bonferroni one-sided bounds need")
print("47/50 each. Bonferroni lower bounds at the observed counts, twelve settings simultaneous:")
for r in rows:
    x, n = int(r["mixture"]), int(r["attempted"])
    print(f"  {r['setting_id']:<4}{x:>5}/{n:<3}  one-sided 95%/12 lower {beta.ppf(0.05/12, x, n-x+1):.4f}")
print()
print("The summed row is NOT a binomial experiment: the twelve settings are heterogeneous strata,")
print("so no Binomial(600, p) interval is attached to it. Per-setting rows are the result.")
