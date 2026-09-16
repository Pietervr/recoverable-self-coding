"""M2B refit control — the refitting bootstrap against the concept-cluster bootstrap at the clean null (read-only).

Reads the pulled rows of run refit_control_aac9f69 (two shards, five datasets each; SEED 2027, reps 0-9) and the saved
d4v12b calibration rows. Every dataset carries BOTH intervals for the same fits: `selection_ws_lo/hi/se` from the interval
method the run used, and `selection_cluster_ws_lo/hi/se` from the fixed-score concept-cluster bootstrap, so the comparison
is exactly paired and needs no refitting here.

The reference target for coverage is theta_g for M2B, estimated as the replicate mean of the 1,000 saved d4v12b M2B
datasets, with its Monte-Carlo standard error; coverage is also reported against theta_g +- 2 SE as a sensitivity, since
the target is itself estimated. No fits, no simulation, no cloud call.

Writes refit_control_summary.json and refit_control_paired.csv beside the rows, and refit_control_intervals.pdf/.png.
Run: /Users/pietervanrooyen/Unimog-Projects/papers/ai_dissipative/presentation/.venv/bin/python 2026-09-16_refit_control_analysis.py
"""
import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

SIM = "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/sim_results"
RUN = os.path.join(SIM, "refit_control_aac9f69")
D4 = os.path.join(SIM, "d4v12b", "calibration_D4.csv")

rows = []
for shard in ("000", "001"):
    with open(os.path.join(RUN, f"calibration_D4.shard{shard}of002.csv"), newline="") as fh:
        rows += list(csv.DictReader(fh))
assert len(rows) == 10, len(rows)
assert {r["generator"] for r in rows} == {"M2B"} and {r["grid"] for r in rows} == {"{}"}

with open(D4, newline="") as fh:
    ref = [r for r in csv.DictReader(fh) if r["generator"] == "M2B"]
ref_points = np.array([float(r["selection_ws_point"]) for r in ref])
theta = float(ref_points.mean())
theta_se = float(ref_points.std(ddof=1) / np.sqrt(ref_points.size))

def num(r, k):
    v = r.get(k, "")
    return float(v) if v not in ("", "nan", None) else float("nan")

paired, out = [], []
for r in rows:
    point = num(r, "selection_ws_point")
    rl, rh = num(r, "selection_ws_lo"), num(r, "selection_ws_hi")
    cl, ch = num(r, "selection_cluster_ws_lo"), num(r, "selection_cluster_ws_hi")
    rec = dict(rep=int(r["rep"]), decision=r["selection_decision"], point=point,
               refit_lo=rl, refit_hi=rh, refit_se=num(r, "selection_ws_se"), refit_width=rh - rl,
               cluster_lo=cl, cluster_hi=ch, cluster_se=num(r, "selection_cluster_ws_se"), cluster_width=ch - cl,
               refit_covers=bool(rl <= theta <= rh), cluster_covers=bool(cl <= theta <= ch),
               interval_method=r.get("interval_method", ""), interval_n_rep=r.get("interval_n_rep", ""),
               interval_usable=r.get("interval_usable", ""), convergence=num(r, "convergence"),
               fit_hours=num(r, "fit_seconds") / 3600.0, wall_hours=num(r, "wall_seconds") / 3600.0)
    paired.append(rec)
    out.append(rec)

def frac(key):
    return sum(p[key] for p in paired) / len(paired)

points = np.array([p["point"] for p in paired])
summary = dict(
    run="refit_control_aac9f69", n_datasets=len(paired), generator="M2B", grid="{}",
    interval_method=sorted({p["interval_method"] for p in paired}),
    interval_n_rep=sorted({p["interval_n_rep"] for p in paired}),
    decisions={d: sum(1 for p in paired if p["decision"] == d) for d in sorted({p["decision"] for p in paired})},
    reference=dict(source="d4v12b M2B replicate mean", n=int(ref_points.size), theta=theta, theta_se=theta_se),
    point_mean=float(points.mean()), point_sd=float(points.std(ddof=1)),
    coverage=dict(refit=frac("refit_covers"), cluster=frac("cluster_covers")),
    coverage_vs_theta_plus_2se=dict(
        refit=sum(p["refit_lo"] <= theta + 2 * theta_se and p["refit_hi"] >= theta - 2 * theta_se for p in paired) / len(paired),
        cluster=sum(p["cluster_lo"] <= theta + 2 * theta_se and p["cluster_hi"] >= theta - 2 * theta_se for p in paired) / len(paired)),
    width=dict(refit_mean=float(np.mean([p["refit_width"] for p in paired])),
               cluster_mean=float(np.mean([p["cluster_width"] for p in paired])),
               ratio_median=float(np.median([p["refit_width"] / p["cluster_width"] for p in paired]))),
    claimed_se=dict(refit_mean=float(np.mean([p["refit_se"] for p in paired])),
                    cluster_mean=float(np.mean([p["cluster_se"] for p in paired])),
                    replicate_sd=float(points.std(ddof=1))),
    convergence=float(np.mean([p["convergence"] for p in paired])),
    cost=dict(fit_hours_mean=float(np.mean([p["fit_hours"] for p in paired])),
              wall_hours_total=float(np.sum([p["wall_hours"] for p in paired]))),
    note="Ten datasets at one clean null: a coverage estimate here has a Monte-Carlo SE of about 0.09, so it screens for "
         "gross failure and cannot establish 0.90. The target is itself estimated from the saved d4v12b rows.")

with open(os.path.join(RUN, "refit_control_summary.json"), "w") as fh:
    json.dump(summary, fh, indent=1)
with open(os.path.join(RUN, "refit_control_paired.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

INK, MUTED, DATA, ALT = "#222222", "#6b6b6b", "#4c72b0", "#dd8452"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
fig, ax = plt.subplots(figsize=(6.2, 3.0), constrained_layout=True)
order = sorted(range(len(paired)), key=lambda i: paired[i]["point"])
for y, i in enumerate(order):
    p = paired[i]
    ax.plot([p["cluster_lo"], p["cluster_hi"]], [y + 0.16, y + 0.16], color=MUTED, lw=2.2, solid_capstyle="butt")
    ax.plot([p["refit_lo"], p["refit_hi"]], [y - 0.16, y - 0.16], color=DATA, lw=2.2, solid_capstyle="butt")
    ax.plot(p["point"], y, "o", ms=3, color=INK)
ax.axvline(theta, color=ALT, lw=1.2)
ax.axvspan(theta - 2 * theta_se, theta + 2 * theta_se, color=ALT, alpha=0.18, lw=0)
ax.axvline(0.0, color=INK, lw=0.8, ls=":")
ax.set_yticks(range(len(order)), [f"rep {paired[i]['rep']}" for i in order])
ax.set_xlabel(r"band-mean $\bar\Delta$ (nat per trial)")
ax.set_title("M2B clean null: refitting (blue) vs concept-cluster (grey) intervals, paired on the same fits", loc="left")
ax.text(theta, len(order) - 0.4, "  reference $\\theta_g$ (d4v12b mean $\\pm$ 2 SE)", color=ALT, fontsize=6.4, va="top")
fig.savefig(os.path.join(RUN, "refit_control_intervals.pdf"))
fig.savefig(os.path.join(RUN, "refit_control_intervals.png"), dpi=200)
print(json.dumps(summary, indent=1))
