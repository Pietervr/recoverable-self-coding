"""Merge the ten final shards of the omega-2 reference bank (ref_m2s_omega2_aac9f69) and report the 1,000-row reference
for the refit probe: mean of the per-dataset point estimate, SD, SE and the mean +- 2 SE range, beside the shard
summaries. The point column is chosen by matching shard 0's summary mean_point."""
import glob
import os

import numpy as np
import pandas as pd

D = "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/sim_results/ref_m2s_omega2_aac9f69/final_2026-09-15"
shards = sorted(glob.glob(os.path.join(D, "calibration_D4.shard*of010.csv")))
frames = [pd.read_csv(f) for f in shards]
s0 = pd.read_csv(os.path.join(D, "calibration_D4.shard000of010_summary.csv")).iloc[-1]
cands = [c for c in frames[0].columns if c.endswith("_point")]
match = [c for c in cands if np.isclose(frames[0][c].astype(float).mean(), float(s0["mean_point"]), atol=1e-9)]
print("point columns:", cands, "-> matching shard-0 mean_point:", match)
col = match[0]
df = pd.concat(frames, ignore_index=True)
print("rows", len(df), "unique reps", df["rep"].nunique(), "grid", df["grid"].unique(), "failed", int(df["failed"].astype(bool).sum()),
      "code_hash", df["code_hash"].unique())
x = df[col].astype(float)
x = x[np.isfinite(x)]
n = len(x)
mean, sd = float(x.mean()), float(x.std(ddof=1))
se = sd / np.sqrt(n)
print(f"{col}: n {n}, mean {mean:.4f}, SD {sd:.4f}, SE {se:.4f}, mean +- 2 SE [{mean - 2 * se:.4f}, {mean + 2 * se:.4f}]; "
      f"median {float(x.median()):.4f}")
for f in sorted(glob.glob(os.path.join(D, "*_summary.csv"))):
    s = pd.read_csv(f).iloc[-1]
    print(os.path.basename(f), f"n {int(s['n'])} mean_point {float(s['mean_point']):.4f} sd {float(s['sd_point']):.3f} "
          f"coverage {float(s['coverage']):.3f}")
