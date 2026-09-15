"""Stage C diagnosis (after outcomes, read-only): per replicate, the per-window group PXPs of null/graded/two-state, the
longest run of each model at PXP >= 0.95, and the mean held-out log-score difference Delta (two-state minus graded,
per trial) over recordings, on the main interval. Recomputes group.decide on the verified saved results; writes
nothing into the namespace."""
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/melcon_port")
import numpy as np  # noqa: E402

import battery as BT  # noqa: E402
import group as G  # noqa: E402

run_dir = BT.namespace_path(BT.config_identity()).replace(os.path.basename(BT.namespace_path(BT.config_identity())),
                                                          "v6-ebaddf98807b")
subjects = BT.templates()
cal = BT.load_calibration(run_dir)
man = json.load(open(os.path.join(run_dir, "manifest.json")))
ident = BT.digest(man)
out = []
first = True
for g in ("G1", "G2", "G3", "X1", "X2"):
    for si, st in enumerate(BT.STRENGTHS):
        for di in range(len(BT.DRIFTS)):
            for r in range(BT.N_REP):
                res = [BT.load_verified(BT.cell_path(run_dir, g, si, di, r, s),
                                        BT.recording_manifest(ident, g, si, di, r, s, cal[(g, st)])) for s in subjects]
                ok = [x for x in res if x["status"] == "ok"]
                pos = BT.main_positions(ok[0]["windows"])
                d = G.decide(res, pos, sum(not x["status"].startswith("excluded") for x in res))
                rows = d.get("windows", [])
                if first:
                    print("window row keys:", sorted(rows[0].keys()))
                    first = False
                pxp = np.array([rw["pxp"] for rw in rows])                   # (10, 3): null, graded, twostate
                delta = np.array([np.nanmean([x["delta"][p] for x in ok]) for p in pos])
                best = np.bincount(np.argmax(pxp, axis=1), minlength=3)
                longest = {}
                for mi, m in enumerate(("null", "graded", "twostate")):
                    L = c = 0
                    for v in pxp[:, mi] >= G.PXP_THRESHOLD:
                        c = c + 1 if v else 0
                        L = max(L, c)
                    longest[m] = L
                out.append(dict(cell=f"{g} {st} d{di} r{r}", outcome=d["outcome"], runs=d.get("runs"),
                                pxp_median=[round(float(v), 3) for v in np.median(pxp, axis=0)],
                                pxp_max=[round(float(v), 3) for v in np.max(pxp, axis=0)], argmax_counts=best.tolist(),
                                longest_run_095=longest, delta_mean=round(float(np.nanmean(delta)), 5),
                                delta_min=round(float(np.nanmin(delta)), 5), delta_max=round(float(np.nanmax(delta)), 5)))
                o = out[-1]
                print(f"{o['cell']:<18} {o['outcome']:<19} pxp med n/g/t {o['pxp_median']} max {o['pxp_max']} "
                      f"argmax {o['argmax_counts']} run095 {longest} Delta mean {o['delta_mean']:+.5f} "
                      f"[{o['delta_min']:+.5f}, {o['delta_max']:+.5f}]", flush=True)
json.dump(out, open("/private/tmp/claude-501/-Users-pietervanrooyen-Unimog-Projects/3a362df4-a2d5-40b7-adaf-f29c648d1ec4/"
                    "scratchpad/stage_c_diag.json", "w"), indent=1)
