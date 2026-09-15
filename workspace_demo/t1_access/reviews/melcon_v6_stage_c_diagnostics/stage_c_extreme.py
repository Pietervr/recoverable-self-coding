"""Re-run the most extreme stage C window (X2 strong, no drift, replicate 2, subject 30, result position 15) from its manifest
seeds and show, per fold, where the graded model's held-out loss comes from: its fitted catch spread exp(s0) and spread
slope r against the training block's S, the training catch count, and the held-out per-trial log-likelihood of catch and
present trials under graded and two-state. Read-only; writes nothing into the namespace."""
import json
import os
import sys

sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/melcon_port")
import numpy as np  # noqa: E402

import battery as BT  # noqa: E402
import likelihood as LK  # noqa: E402
import recording as RC  # noqa: E402
import synthetic as SY  # noqa: E402

CASES = [("X2", "strong", 0, 2, 30, 15), ("G1", "strong", 1, 0, 30, 10), ("G3", "strong", 0, 0, 18, 11)]
run_dir = os.path.join(BT.OUT_DIR, "v6-ebaddf98807b")
cal = BT.load_calibration(run_dir)
man = json.load(open(os.path.join(run_dir, "manifest.json")))
ident = BT.digest(man)
for g, st, di, rep, subj, pos in CASES:
    si = BT.STRENGTHS.index(st)
    m = BT.recording_manifest(ident, g, si, di, rep, subj, cal[(g, st)])
    saved = BT.load_verified(BT.cell_path(run_dir, g, si, di, rep, subj), m)
    w = RC.WINDOWS[pos]
    rec = SY.generate(SY.template(subj, "nocue"), g, m["amplitude"], m["drift"], tags=tuple(m["tags"]))
    res = RC.recording_scores(rec, subj, "nocue", windows=(w,))
    print(f"\n=== {g} {st} d{di} r{rep} sub-{subj} window {w} (position {pos}): saved Delta {saved['delta'][pos]:+.3f}, "
          f"re-run Delta {res['delta'][0]:+.3f}; saved evidence {np.round(saved['evidence'][pos], 2).tolist()}")
    dec = res["decoder"]
    names = LK.PARAMS["graded"]
    for hi, (B, d) in enumerate(sorted(dec["halves"].items())):
        tr, W = d["trials"], d["W"]
        catch = tr["catch"].to_numpy(bool)
        right = (tr["side"].to_numpy() == "right") & ~catch
        logc = np.where(catch, np.nan, np.log(np.where(catch, 1.0, tr["contrast"].to_numpy(float))))
        blk = tr["block"].to_numpy()
        for fi, (b_tr, b_te) in enumerate(((B[0], B[1]), (B[1], B[0]))):
            s = res["folds"][(hi, fi, w)]
            mtr, mte = blk == b_tr, blk == b_te
            test = LK.Block(W[mte, w], logc[mte], catch[mte], right[mte])
            sc = s["graded"]["scaling"]
            dte = LK.design(test, sc)
            line = f"  half {B} fold train {b_tr} -> test {b_te}: n_train_catch {int(catch[mtr].sum())}, S {sc['S']:.3f}"
            for mod in ("null", "graded", "twostate"):
                r = s[mod]
                if not r["available"]:
                    line += f" | {mod} unavailable ({r['reason']})"
                    continue
                ll = LK.loglik(mod, r["theta"], dte)
                line += (f" | {mod} held {r['heldout']:.1f} (catch {ll[dte['c']].sum():.1f}, present {ll[~dte['c']].sum():.1f},"
                         f" worst trial {ll.min():.1f})")
            th = dict(zip(names, s["graded"]["theta"])) if s["graded"]["available"] else None
            if th:
                line += (f" | graded exp(s0)/S {np.exp(th['s0']) / sc['S']:.3f}, r {th['r']:+.2f}, a1/S {th['a1'] / sc['S']:.2f},"
                         f" twostate sigma/S {np.exp(s['twostate']['theta'][1]) / sc['S']:.3f}")
            print(line)
