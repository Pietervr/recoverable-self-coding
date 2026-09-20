"""Read the finished Mac refit probe (ledger row 2) against independent references. Read-only.

    .venv/bin/python reviews/2026-09-19_refit_probe_analysis.py

The probe ran 20 new-seed datasets at each of M2S omega = 1 and omega = 2 (seed 2027, D = 4, layer 41,
B = 50 refit resamples), with interval="refit": selection_ws_* is the pipeline-refitting interval and
selection_cluster_ws_* the fixed-score concept-cluster interval built from the same fits, so the two are
paired on every dataset. Development evidence only: 20 datasets give a Monte-Carlo SE near 0.11 on a
coverage figure, or 0.067 at coverage 0.90.

Coverage is read against the procedure's expectation estimated OUTSIDE this run, never against the probe's
own 20-row mean:
  omega = 1: the 1,000-row d4v12b mean;
  omega = 2: the independent 1,000-row bank ref_m2s_omega2_aac9f69 (its mean is tail-dominated, so the
             bank median and the mean without its most extreme dataset are reported beside it).
`simulate.summarize()` scores coverage against the same run's mean and is not used here.
"""
import csv
import json
import math
import statistics as st
from pathlib import Path

T1 = Path(__file__).resolve().parent.parent
PROBE = T1 / "sim_results/refit_probe_3ca9304/refit_probe_D4.csv"
D4V12B = T1 / "sim_results/d4v12b/calibration_D4.csv"
# The full 1,000-row bank lives with the 15 Sept analysis; sim_results/ref_m2s_omega2_aac9f69/ holds only
# the first 128 rows, pulled from S3 on 13 Sept before the run finished.
BANK = T1 / "reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv"
OMEGAS = [1.0, 2.0]


def rows(path, cols, keep):
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if keep(r):
                out.append({c: r[c] for c in cols})
    return out


def f(x):
    return float(x) if x not in ("", None) else float("nan")


def grid_omega(g):
    try:
        return json.loads(g).get("omega")
    except Exception:
        return None


def reference(path, omega, label, bank=False):
    if bank:                                   # source,rep,point,lo,hi with 1,000 bank and 1,000 d4v12b rows
        pts = [f(r["point"]) for r in rows(path, ["point"], lambda r: r["source"] == "bank")]
    else:
        pts = [f(r["selection_ws_point"]) for r in rows(
            path, ["selection_ws_point", "failed"],
            lambda r: r["generator"] == "M2S" and grid_omega(r["grid"]) == omega
            and r["failed"] in ("0", "0.0", "False"))]
    m, sd = st.mean(pts), st.stdev(pts)
    trimmed = sorted(pts)[1:] if omega == 2.0 else None      # without the single most extreme dataset
    return {"label": label, "n": len(pts), "mean": m, "sd": sd, "mcse": sd / math.sqrt(len(pts)),
            "median": st.median(pts),
            "mean_wo_extreme": st.mean(trimmed) if trimmed else None}


def clopper_pearson(k, n, alpha=0.05):
    """Exact two-sided 95% interval for a coverage count, by the beta quantiles (no SciPy here)."""
    def beta_q(q, a, b):
        lo_, hi_ = 0.0, 1.0
        for _ in range(200):
            mid = (lo_ + hi_) / 2
            if betainc(a, b, mid) < q:
                lo_ = mid
            else:
                hi_ = mid
        return (lo_ + hi_) / 2

    def betainc(a, b, x):                      # regularised incomplete beta by simple quadrature
        n_steps = 2000
        h = x / n_steps
        s = 0.0
        for i in range(n_steps + 1):
            u = min(max(i * h, 1e-12), 1 - 1e-12)
            w = 1 if i in (0, n_steps) else (4 if i % 2 else 2)
            s += w * u ** (a - 1) * (1 - u) ** (b - 1)
        s *= h / 3
        return s / math.exp(math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))

    lo_ = 0.0 if k == 0 else beta_q(alpha / 2, k, n - k + 1)
    hi_ = 1.0 if k == n else beta_q(1 - alpha / 2, k + 1, n - k)
    return lo_, hi_


def block(p, targets):
    lo, hi = [f(r["selection_ws_lo"]) for r in p], [f(r["selection_ws_hi"]) for r in p]
    clo, chi = [f(r["selection_cluster_ws_lo"]) for r in p], [f(r["selection_cluster_ws_hi"]) for r in p]
    pt = [f(r["selection_ws_point"]) for r in p]
    se, cse = [f(r["selection_ws_se"]) for r in p], [f(r["selection_cluster_ws_se"]) for r in p]
    w = [h - l for l, h in zip(lo, hi)]
    cw = [h - l for l, h in zip(clo, chi)]
    out = {"n": len(p), "point_mean": st.mean(pt), "point_sd": st.stdev(pt),
           "width_refit": st.mean(w), "width_cluster": st.mean(cw),
           "width_ratio_of_means": st.mean(w) / st.mean(cw),
           "width_ratio_median_paired": st.median([a / b for a, b in zip(w, cw)]),
           "se_refit": st.mean(se), "se_cluster": st.mean(cse),
           "decisions": {d: sum(1 for r in p if r["selection_decision"] == d) for d in
                         sorted({r["selection_decision"] for r in p})},
           "usable_refit": sum(1 for r in p if r["selection_interval_usable"] in ("1", "True", "1.0")),
           "resamples_used": sorted({int(float(r["interval_n_used"])) for r in p}),
           "failed": sum(1 for r in p if r["failed"] not in ("0", "0.0", "False")),
           "coverage": {}}
    for name, target in targets.items():
        cr = [l <= target <= h for l, h in zip(lo, hi)]
        cc = [l <= target <= h for l, h in zip(clo, chi)]
        out["coverage"][name] = {
            "target": target, "refit": sum(cr), "cluster": sum(cc),
            "ci_refit": clopper_pearson(sum(cr), len(cr)), "ci_cluster": clopper_pearson(sum(cc), len(cc)),
            "only_refit": sum(1 for a, b in zip(cr, cc) if a and not b),      # discordant pairs, same datasets
            "only_cluster": sum(1 for a, b in zip(cr, cc) if b and not a)}
    return out


def main():
    cols = ["generator", "grid", "rep", "failed", "convergence", "inner_convergence", "interval_n_used",
            "interval_n_failed", "interval_usable", "selection_decision", "selection_ws_point", "selection_ws_lo",
            "selection_ws_hi", "selection_ws_se", "selection_cluster_ws_lo", "selection_cluster_ws_hi",
            "selection_cluster_ws_se", "selection_interval_usable", "interval_method", "code_hash"]
    probe = rows(PROBE, cols, lambda r: True)
    print(f"probe rows {len(probe)}, interval {sorted({r['interval_method'] for r in probe})}, "
          f"code {sorted({r['code_hash'] for r in probe})}")
    print(f"convergence {sorted({r['convergence'] for r in probe})}, inner "
          f"{sorted({r['inner_convergence'] for r in probe})}, "
          f"resample failures {sorted({r['interval_n_failed'] for r in probe})}")

    figure_data(probe, T1 / "reviews/2026-09-19_refit_probe_figure_data.csv")
    for omega in OMEGAS:
        p = [r for r in probe if grid_omega(r["grid"]) == omega]
        refs = {"d4v12b 1,000-row mean": reference(D4V12B, omega, "d4v12b")}
        if omega == 2.0:
            b = reference(BANK, omega, "independent bank", bank=True)
            refs["independent bank mean"] = b
            refs["bank median"] = {"mean": b["median"]}
            refs["bank mean without its most extreme dataset"] = {"mean": b["mean_wo_extreme"]}
        targets = {k: v["mean"] for k, v in refs.items()}
        r = block(p, targets)
        print(f"\n=== M2S omega = {omega}: {r['n']} datasets, decisions {r['decisions']}, "
              f"failed {r['failed']}, usable {r['usable_refit']}, resamples used {r['resamples_used']}")
        for k, v in refs.items():
            extra = ""
            if "n" in v:
                extra = f" (n={v['n']}, sd {v['sd']:.4f}, MCSE {v['mcse']:.4f})"
            print(f"  reference {k}: {v['mean']:.5f}{extra}")
        print(f"  probe's own 20-row mean {r['point_mean']:.5f}, replicate SD {r['point_sd']:.5f}")
        for k, c in r["coverage"].items():
            print(f"  coverage vs {k} ({c['target']:.5f}): refitting {c['refit']}/{r['n']} "
                  f"[{c['ci_refit'][0]:.2f}, {c['ci_refit'][1]:.2f}], cluster {c['cluster']}/{r['n']} "
                  f"[{c['ci_cluster'][0]:.2f}, {c['ci_cluster'][1]:.2f}]; on the same datasets "
                  f"{c['only_refit']} covered only by refitting, {c['only_cluster']} only by the cluster interval")
        print(f"  mean width refitting {r['width_refit']:.5f} vs cluster {r['width_cluster']:.5f} "
              f"(ratio of means {r['width_ratio_of_means']:.3f}, median paired ratio "
              f"{r['width_ratio_median_paired']:.3f})")
        print(f"  claimed SE refitting {r['se_refit']:.5f} ({r['se_refit'] / r['point_sd']:.3f} of the probe's own "
              f"spread), cluster {r['se_cluster']:.5f} ({r['se_cluster'] / r['point_sd']:.3f})")
        ref_sd = refs["d4v12b 1,000-row mean"]["sd"]
        print(f"  the same against the 1,000-row spread {ref_sd:.5f}: refitting "
              f"{r['se_refit'] / ref_sd:.3f}, cluster {r['se_cluster'] / ref_sd:.3f}")


def figure_data(probe, out):
    """One row per dataset: both intervals, the point, and whether each covers each reference target."""
    refs = {1.0: {"d4v12b_mean": reference(D4V12B, 1.0, "d4v12b")["mean"]}, 2.0: {}}
    b = reference(BANK, 2.0, "bank", bank=True)
    refs[2.0] = {"d4v12b_mean": reference(D4V12B, 2.0, "d4v12b")["mean"], "bank_mean": b["mean"],
                 "bank_median": b["median"], "bank_mean_wo_extreme": b["mean_wo_extreme"]}
    import csv as _csv
    with open(out, "w", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(["omega", "rep", "point", "refit_lo", "refit_hi", "refit_se", "cluster_lo", "cluster_hi",
                    "cluster_se", "target", "target_value", "refit_covers", "cluster_covers"])
        for r in probe:
            om = grid_omega(r["grid"])
            for name, tv in refs[om].items():
                w.writerow([om, r["rep"], r["selection_ws_point"], r["selection_ws_lo"], r["selection_ws_hi"],
                            r["selection_ws_se"], r["selection_cluster_ws_lo"], r["selection_cluster_ws_hi"],
                            r["selection_cluster_ws_se"], name, f"{tv:.6f}",
                            int(f(r["selection_ws_lo"]) <= tv <= f(r["selection_ws_hi"])),
                            int(f(r["selection_cluster_ws_lo"]) <= tv <= f(r["selection_cluster_ws_hi"]))])
    print("wrote", out)


if __name__ == "__main__":
    main()
