#!/usr/bin/env python3
"""Paper figure data for the Phase 2 fresh check of the Melcón v7 development plan (read-only over devcheck_v7.py's
report.json; no fit, no generated recording, no EEG).

Writes, beside the manuscript's figure scripts:
  melcon_v7_phase2_groups.csv  one row per group x configuration (baseline, C2): group outcome, eligible windows, runs,
                               the group PXP of null, graded and two-state in each of the ten main windows, and per family
                               the scored, severe and newly unavailable fold units and the severe transitions;
  melcon_v7_phase2_gates.csv   each declared gate and whether it holds, the pooled graded severe counts B and C, and the
                               lock decision.
Usage: ../../.venv/bin/python devcheck_figure_data.py
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(HERE, "results", "devcheck_v7", "run-061c01d763b9")
FIG = "/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/figures"
GROUPS = ("X1|strong|d0", "X1|strong|d1", "G1|strong|d0", "G1|strong|d1", "G3|weak|d0", "G3|weak|d1")
CONFIGS = ("baseline", "c2")

rep = json.load(open(os.path.join(RUN, "report.json")))
assert rep["n_present"] == rep["n_expected"] == 204, (rep["n_present"], rep["n_expected"])
rows = []
for g in GROUPS:
    for c in CONFIGS:
        d = rep["decisions"][f"{g}|{c}"]
        r = dict(group=g, config=c, outcome=d["outcome"], n_windows_eligible=d["n_windows_eligible"],
                 run_null=(d["runs"] or {}).get("null"), run_graded=(d["runs"] or {}).get("graded"),
                 run_twostate=(d["runs"] or {}).get("twostate"))
        for i, p in enumerate(d["pxp"]):
            for j, m in enumerate(("null", "graded", "twostate")):
                r[f"pxp_{m}_w{i}"] = "" if p is None else p[j]
        for fam in ("graded", "twostate"):
            cnt = rep["per_group_family"][f"{g}|{fam}"]["counts"]
            r[f"{fam}_scheduled"] = cnt.get("scheduled", 0)
            r[f"{fam}_scored"] = cnt.get("scored", 0)
            r[f"{fam}_severe"] = cnt.get(f"{c}_severe", 0)
            r[f"{fam}_unavailable"] = cnt.get(f"{c}_unavailable", 0)
            r[f"{fam}_newly_unavailable"] = cnt.get("newly_unavailable", 0) if c == "c2" else 0
            for tr in ("SS", "SN", "NS", "NN"):
                r[f"{fam}_transition_{tr}"] = cnt.get(f"transition_{tr}", 0)
        rows.append(r)
with open(os.path.join(FIG, "melcon_v7_phase2_groups.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

gate = rep["gates"]
with open(os.path.join(FIG, "melcon_v7_phase2_gates.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["gate", "holds"])
    for k, v in gate.get("gates", {}).items():
        w.writerow([k, v])
    w.writerow(["graded_severe_B", gate.get("graded_severe_B")])
    w.writerow(["graded_severe_C", gate.get("graded_severe_C")])
    w.writerow(["graded_scored", gate.get("graded_scored")])
    w.writerow(["lock_c2", gate.get("lock_c2")])
print(json.dumps(dict(decisions={k: v["outcome"] for k, v in rep["decisions"].items()}, gates=gate), indent=1))
