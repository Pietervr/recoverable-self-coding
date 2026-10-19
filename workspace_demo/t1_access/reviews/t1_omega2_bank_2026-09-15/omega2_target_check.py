"""Sanity check for the paper: the d4v12b cluster intervals at M2S omega = 2 (1,000 datasets, old policy) against
candidate reference values for the procedure's expectation, taken from the independent omega-2 bank
(ref_m2s_omega2_aac9f69, 1,000 datasets, seed 2028, same policy). Read-only: saved rows only, no fits.
Writes omega2_target_check.json and omega2_figure_data.csv (for the paper figure) beside this script."""
import glob
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.dirname(os.path.dirname(HERE))
COLS = ["generator", "grid", "rep", "failed", "selection_ws_point", "selection_ws_lo", "selection_ws_hi"]


def load(pattern):
    files = sorted(glob.glob(pattern))
    df = pd.concat([pd.read_csv(f, usecols=COLS) for f in files], ignore_index=True)
    return df, files


bank, bank_files = load(os.path.join(T1, "sim_results/ref_m2s_omega2_aac9f69/final_2026-09-15/calibration_D4.shard*of010.csv"))
d4, d4_files = load(os.path.join(T1, "sim_results/d4v12b/calibration_D4.shard*.csv"))
d4 = d4[(d4.generator == "M2S") & (d4.grid.apply(lambda g: json.loads(g).get("omega") == 2.0))]
d4 = d4.drop_duplicates(subset=["rep"])
for name, df in (("bank", bank), ("d4v12b", d4)):
    assert len(df) == 1000 and df.rep.nunique() == 1000 and int(df.failed.astype(bool).sum()) == 0, name

b = bank.selection_ws_point.to_numpy()
srt = np.sort(b)
targets = {
    "bank_mean": float(b.mean()),
    "bank_mean_without_most_extreme": float(srt[1:].mean()),
    "bank_median": float(np.median(b)),
    "d4v12b_mean": float(d4.selection_ws_point.mean()),
}
lo, hi = d4.selection_ws_lo.to_numpy(), d4.selection_ws_hi.to_numpy()
blo, bhi = bank.selection_ws_lo.to_numpy(), bank.selection_ws_hi.to_numpy()
cover = {k: dict(d4v12b_intervals=float(np.mean((lo <= v) & (v <= hi))), bank_intervals=float(np.mean((blo <= v) & (v <= bhi))))
         for k, v in targets.items()}
leave_k = []
for k in (0, 1, 2, 5, 10, 20, 50):
    kept = srt[k:]                       # the k most negative (most extreme) rows removed
    leave_k.append(dict(k=k, n=int(kept.size), mean=float(kept.mean()), se=float(kept.std(ddof=1) / np.sqrt(kept.size))))
out = dict(
    bank_files=[os.path.relpath(f, T1) for f in bank_files], d4v12b_files=[os.path.relpath(f, T1) for f in d4_files],
    bank=dict(n=int(b.size), mean=float(b.mean()), sd=float(b.std(ddof=1)), se=float(b.std(ddof=1) / np.sqrt(b.size)),
              median=float(np.median(b)), min=float(b.min()), quantiles={str(q): float(np.quantile(b, q)) for q in (0.001, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)},
              n_below_minus_55=int((b < -55).sum())),
    d4v12b=dict(n=int(len(d4)), mean=targets["d4v12b_mean"], median=float(d4.selection_ws_point.median()),
                min=float(d4.selection_ws_point.min())),
    targets=targets, coverage_of_targets=cover, leave_k_most_extreme=leave_k,
    note="Development evidence under the old eight-start policy; not a validation of any interval.")
with open(os.path.join(HERE, "omega2_target_check.json"), "w") as fh:
    json.dump(out, fh, indent=2)
pd.DataFrame(dict(source=["bank"] * len(bank) + ["d4v12b"] * len(d4),
                  rep=list(bank.rep) + list(d4.rep),
                  point=list(bank.selection_ws_point) + list(d4.selection_ws_point),
                  lo=list(bank.selection_ws_lo) + list(d4.selection_ws_lo),
                  hi=list(bank.selection_ws_hi) + list(d4.selection_ws_hi))).to_csv(os.path.join(HERE, "omega2_figure_data.csv"), index=False)
print(json.dumps({k: out[k] for k in ("bank", "d4v12b", "targets", "coverage_of_targets", "leave_k_most_extreme")}, indent=1))
