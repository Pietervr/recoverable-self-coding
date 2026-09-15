"""Stage C diagnosis 3 (read-only): prevalence of catastrophic held-out losses. Per cell, over recording x main-window
entries: the fraction where a model's held-out evidence per trial falls more than 1 nat (and more than 0.1 nat) below the
null model's; and how the per-window Delta changes if those entries are excluded (the median-of-recordings Delta is
already robust; this shows the tail's share)."""
import json
import os
import sys

sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/melcon_port")
import numpy as np  # noqa: E402

import battery as BT  # noqa: E402

run_dir = os.path.join(BT.OUT_DIR, "v6-ebaddf98807b")
subjects = BT.templates()
cal = BT.load_calibration(run_dir)
ident = BT.digest(json.load(open(os.path.join(run_dir, "manifest.json"))))
print("cell             entries | graded<null-1 | twostate<null-1 | graded<null-0.1 | twostate<null-0.1 | "
      "mean Delta all | mean Delta w/o catastrophes")
tot = dict(n=0, g1=0, t1=0)
for g in ("G1", "G2", "G3", "X1", "X2"):
    for si, st in enumerate(BT.STRENGTHS):
        for di in range(len(BT.DRIFTS)):
            gn, tn, dl = [], [], []
            for r in range(BT.N_REP):
                for s in subjects:
                    x = BT.load_verified(BT.cell_path(run_dir, g, si, di, r, s),
                                         BT.recording_manifest(ident, g, si, di, r, s, cal[(g, st)]))
                    if x["status"] != "ok":
                        continue
                    pos = BT.main_positions(x["windows"])
                    ev = np.asarray(x["evidence"], float)[pos]
                    n = np.asarray(x["n_trials"], float)[pos]
                    gn += list((ev[:, 1] - ev[:, 0]) * 4 / n)
                    tn += list((ev[:, 2] - ev[:, 0]) * 4 / n)
                    dl += list(np.asarray(x["delta"], float)[pos])
            gn, tn, dl = np.array(gn), np.array(tn), np.array(dl)
            ok = np.isfinite(gn) & np.isfinite(tn) & np.isfinite(dl)
            cat = ok & ((gn < -1) | (tn < -1))
            tot["n"] += int(ok.sum()); tot["g1"] += int((gn[ok] < -1).sum()); tot["t1"] += int((tn[ok] < -1).sum())
            print(f"{g} {st:<6} d{di}  {ok.sum():>5}  | {np.mean(gn[ok] < -1):.3f} | {np.mean(tn[ok] < -1):.3f} | "
                  f"{np.mean(gn[ok] < -0.1):.3f} | {np.mean(tn[ok] < -0.1):.3f} | {np.mean(dl[ok]):+.4f} | "
                  f"{np.mean(dl[ok & ~cat]):+.4f}", flush=True)
print(f"all cells: {tot['n']} recording-window entries; graded more than 1 nat/trial below null in {tot['g1']} "
      f"({tot['g1'] / tot['n']:.3%}), two-state in {tot['t1']} ({tot['t1'] / tot['n']:.3%})")
