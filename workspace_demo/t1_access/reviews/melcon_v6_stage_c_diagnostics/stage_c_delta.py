"""Stage C diagnosis 2 (read-only): per cell, the distribution over recordings of the per-recording held-out Delta (two-state
minus graded, nat per trial) on the main interval, and of the per-recording evidence differences (graded - null,
two-state - null, per trial); the most extreme recordings are listed for re-running with their folds."""
import json
import os
import sys

sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/melcon_port")
import numpy as np  # noqa: E402

import battery as BT  # noqa: E402

run_dir = os.path.join(BT.OUT_DIR, "v6-ebaddf98807b")
subjects = BT.templates()
cal = BT.load_calibration(run_dir)
man = json.load(open(os.path.join(run_dir, "manifest.json")))
ident = BT.digest(man)
extreme = []
print("cell               | Delta per recording (median over windows): median  IQR  frac>0  max | "
      "(G-N)/trial median | (T-N)/trial median")
for g in ("G1", "G2", "G3", "X1", "X2"):
    for si, st in enumerate(BT.STRENGTHS):
        for di in range(len(BT.DRIFTS)):
            per_rec, gn, tn = [], [], []
            for r in range(BT.N_REP):
                for s in subjects:
                    x = BT.load_verified(BT.cell_path(run_dir, g, si, di, r, s),
                                         BT.recording_manifest(ident, g, si, di, r, s, cal[(g, st)]))
                    if x["status"] != "ok":
                        continue
                    pos = BT.main_positions(x["windows"])
                    d = np.asarray(x["delta"], float)[pos]
                    ev = np.asarray(x["evidence"], float)[pos]                     # (10, 3) held/4: null, graded, twostate
                    n = np.asarray(x["n_trials"], float)[pos]
                    per_rec.append(float(np.nanmedian(d)))
                    gn.append(float(np.nanmedian((ev[:, 1] - ev[:, 0]) * 4 / n)))
                    tn.append(float(np.nanmedian((ev[:, 2] - ev[:, 0]) * 4 / n)))
                    w = int(np.nanargmax(d)) if np.any(np.isfinite(d)) else 0
                    extreme.append((float(np.nanmax(d)), g, st, di, r, s, pos[w]))
            a = np.array(per_rec)
            q1, q3 = np.nanpercentile(a, [25, 75])
            print(f"{g} {st:<6} d{di}        | {np.nanmedian(a):+.4f}  [{q1:+.4f}, {q3:+.4f}]  {np.mean(a > 0):.2f}  "
                  f"{np.nanmax(a):+.3f} | {np.nanmedian(gn):+.4f} | {np.nanmedian(tn):+.4f}", flush=True)
extreme.sort(reverse=True)
print("largest single-window Delta (nat/trial):")
for e in extreme[:8]:
    print("  ", e)
