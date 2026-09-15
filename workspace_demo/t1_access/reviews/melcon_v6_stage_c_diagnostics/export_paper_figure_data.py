"""Paper figure data for the failed Melcón v6 development battery (read-only: no fit, no generated recording, no EEG).

Writes Unimog-Projects/papers/adaptive_agency_special_issue/figures/melcon_v6_battery_data.csv, one row per group
replicate (60), from the v6 namespace results/battery/v6-ebaddf98807b:
  - outcome and cell verdict (verdicts.json);
  - median main-window group PXP of null, graded and two-state, the longest run of each at PXP >= 0.95, and the
    replicate mean Delta (stage_c_diag.json beside this script; every entry reproduced by Codex's audit, RSC e490f3b);
  - replicate diagnostics (replicates.csv): median main-window AUC, fitted two-state gaps, readout-latent correlation;
  - per cell the calibration target, amplitude and check (calibration.json) and the strength-resolution flag
    (strengths.json);
  - per cell the fraction of recording x main-window entries whose graded (two-state) held-out evidence per trial is
    more than 1 nat below null, recomputed from the verified payloads; the totals must equal
    stage_c_catastrophe.output.txt (1,898 and 8 of 20,400).
Run: /Users/pietervanrooyen/Recoverable-Self-Coding/.venv/bin/python export_paper_figure_data.py
"""
import csv
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/melcon_port")
import numpy as np  # noqa: E402

import battery as BT  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(BT.OUT_DIR, "v6-ebaddf98807b")
OUT = "/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/figures/melcon_v6_battery_data.csv"

ident = BT.digest(json.load(open(os.path.join(RUN, "manifest.json"))))
assert ident == "ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021", ident
subjects = BT.templates()
cal = BT.load_calibration(RUN)
verdicts = json.load(open(os.path.join(RUN, "verdicts.json")))
strengths = json.load(open(os.path.join(RUN, "strengths.json")))
diag = {d["cell"]: d for d in json.load(open(os.path.join(HERE, "stage_c_diag.json")))}
reps = {(r["generator"], r["strength"], r["drift"], r["replicate"]): r
        for r in csv.DictReader(open(os.path.join(RUN, "replicates.csv"), newline=""))}

rows, tot = [], dict(n=0, graded=0, twostate=0)
for g in BT.SY.GENERATORS:
    for si, st in enumerate(BT.STRENGTHS):
        for di, drift in enumerate(BT.DRIFTS):
            gn, tn = [], []
            for r in range(BT.N_REP):
                for s in subjects:
                    x = BT.load_verified(BT.cell_path(RUN, g, si, di, r, s), BT.recording_manifest(ident, g, si, di, r, s, cal[(g, st)]))
                    if x["status"] != "ok":
                        continue
                    pos = BT.main_positions(x["windows"])
                    ev = np.asarray(x["evidence"], float)[pos]
                    n = np.asarray(x["n_trials"], float)[pos]
                    gn += list((ev[:, 1] - ev[:, 0]) * 4 / n)
                    tn += list((ev[:, 2] - ev[:, 0]) * 4 / n)
            gn, tn = np.array(gn), np.array(tn)
            ok = np.isfinite(gn) & np.isfinite(tn)
            tot["n"] += int(ok.sum())
            tot["graded"] += int((gn[ok] < -1).sum())
            tot["twostate"] += int((tn[ok] < -1).sum())
            v = verdicts[f"{g}|{st}|{drift}"]
            c = cal[(g, st)]
            for r in range(BT.N_REP):
                d = diag[f"{g} {st} d{di} r{r}"]
                rep = reps[(g, st, str(drift), str(r))]
                assert d["outcome"] == rep["outcome"] == v["outcomes"][r], (g, st, di, r)
                rows.append(dict(generator=g, strength=st, drift=di, replicate=r, outcome=d["outcome"], cell_verdict=v["verdict"],
                                 pxp_median_null=d["pxp_median"][0], pxp_median_graded=d["pxp_median"][1],
                                 pxp_median_twostate=d["pxp_median"][2], longest_run_null=d["longest_run_095"]["null"],
                                 longest_run_graded=d["longest_run_095"]["graded"],
                                 longest_run_twostate=d["longest_run_095"]["twostate"], windows_argmax_twostate=d["argmax_counts"][2],
                                 delta_mean=d["delta_mean"], median_auc_main=rep["median_auc_main"],
                                 twostate_min_gap=rep["twostate_min_gap"], twostate_full_gap=rep["twostate_full_gap"],
                                 readout_latent_corr=rep["readout_latent_corr"], cal_target=c["target"], cal_amplitude=c["amplitude"],
                                 cal_check=c["check"], strength_resolved=strengths[g]["resolved"], cell_entries=int(ok.sum()),
                                 cell_graded_below_null_1nat=float(np.mean(gn[ok] < -1)),
                                 cell_twostate_below_null_1nat=float(np.mean(tn[ok] < -1))))
assert (tot["n"], tot["graded"], tot["twostate"]) == (20400, 1898, 8), tot
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
outcomes = [r["outcome"] for r in rows]
print(dict(rows=len(rows), totals=tot, outcomes={o: outcomes.count(o) for o in sorted(set(outcomes))},
           verdicts={v: sum(1 for k in verdicts.values() if k["verdict"] == v) for v in ("pass", "fail", "reported")}, out=OUT))
