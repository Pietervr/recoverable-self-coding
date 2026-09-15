"""The tail of the omega-2 reference bank: the rows with the most extreme point estimates, their shard, rep, decision,
interval and fit diagnostics; and the reference mean with the most extreme rows removed one by one (descriptive only)."""
import glob
import os

import numpy as np
import pandas as pd

D = "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/sim_results/ref_m2s_omega2_aac9f69/final_2026-09-15"
frames = []
for f in sorted(glob.glob(os.path.join(D, "calibration_D4.shard*of010.csv"))):
    x = pd.read_csv(f)
    x["shard"] = os.path.basename(f)[20:23]
    frames.append(x)
df = pd.concat(frames, ignore_index=True)
col = "selection_ws_point"
p = df[col].astype(float)
order = p.abs().sort_values(ascending=False).index
keep = [c for c in ("shard", "rep", col, "selection_decision", "selection_ws_lo", "selection_ws_hi", "convergence",
                    "inner_convergence", "recovery", "fit_seconds") if c in df.columns]
print(df.loc[order[:12], keep].to_string())
print("quantiles of the point estimate:", np.round(p.quantile([0, 0.001, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1]).values, 3))
for k in (0, 1, 2, 5, 10):
    y = p.drop(order[:k])
    print(f"without the {k} most extreme rows: n {len(y)}, mean {y.mean():.4f}, SD {y.std(ddof=1):.4f}, "
          f"SE {y.std(ddof=1) / np.sqrt(len(y)):.4f}")
