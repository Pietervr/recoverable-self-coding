#!/usr/bin/env python3
"""t1_access/simulate.py — §7.5 recovery of the family distinction and §10 calibration / power, on
synthetic CONF-sized data through the full §8 procedure (analyze.analyze_dataset).

Synthetic design: 8 families x n_per_family concepts (CONF: 8 -> 64), 6 carriers, the level set
models.LEVELS, D draws per (concept, carrier) -> n_c = 6 x 7 x D trials per concept. Layers: a declared
grid inside the workspace band (SIM_LAYERS); per trial the standard noise is AR(1)-correlated across
layers with coefficient RHO_LAYERS, the mixture state is drawn once per trial and shared across the
layers, and a concept's random effect is shared across layers. PILOT will replace RHO_LAYERS by the
measured residual correlation (§10); until then it is a declared stand-in.

Generator base (declared here; CAL/PILOT-fitted parameters are added when they exist):
  graded   mu(0) = -1, mu(8) = +1 (L set from kappa, x0), x0 = 3, kappa = 1.5, sigma = |0.15 mu + 0.75|
           (0.60 at mu = -1, 0.90 at mu = +1); M2H tau / M2S omega / M2K alpha0 = alpha, alpha1 = 0 from the grid
  mixture  mu_low = -1, sigma = 0.6 (M3V: sigma_low 0.6, sigma_high 0.9), A(k) = sigmoid(1.5 (k - 3)),
           mu_high(k) = mu_low + sep*sigma + 1.0*lg_h(k) with lg_h the same logistic; M3H tau, M3L pi0 from
           the grid; `scale` multiplies both high-state offsets (used by the §10 gain calibration).

§7.5 grid: tau, omega in {0, .5, 1, 2}; sep = e^{d0}/sigma in {.5, 1, 2, 4}; pi0 in {0, .05, .2};
alpha in {0, 1, 3} -> 48 generator points (`recovery_points`). §10 nulls: the four graded members at
the grid; alternatives: the four mixture members at per-trial gains 0.003, 0.01, 0.03 nat, the gain
being the expected out-of-sample joint log-score advantage per trial of the generator over the best
graded member fitted at large sample (`expected_gain`, `calibrate_gain`).

Replicate counts and the layer grid are set by bench.py (§14) and recorded in the pre-registration v1.2;
the CLI takes them as arguments, so the committed outputs carry their own counts.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time as _time

import numpy as np

import analyze as A
import models as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "sim_results")
SIM_LAYERS = (25, 33, 41, 49, 57)     # declared reduced grid inside the workspace band 23–57
RHO_LAYERS = 0.9                      # stand-in for the PILOT-measured residual correlation across layers
N_CARRIERS = 6
GRID = dict(tau=(0.0, 0.5, 1.0, 2.0), omega=(0.0, 0.5, 1.0, 2.0), sep=(0.5, 1.0, 2.0, 4.0),
            pi0=(0.0, 0.05, 0.2), alpha=(0.0, 1.0, 3.0))
GAINS = (0.003, 0.01, 0.03)
BASE = dict(mu_low=-1.0, mu_top=1.0, x0=3.0, kappa=1.5, sigma=0.6, a=0.15, b=0.75, sigma_high=0.9, sep1=1.0)


# ----------------------------------------------------------------------------------------------
# design and generators
# ----------------------------------------------------------------------------------------------
def make_design(n_per_family: int = 8, n_carriers: int = N_CARRIERS, D: int = 4, levels=M.LEVELS) -> dict:
    C = A.N_FAMILIES * n_per_family
    per = n_carriers * len(levels) * D
    concept = np.repeat(np.arange(C), per)
    family = np.repeat(np.arange(A.N_FAMILIES), n_per_family)
    k = np.tile(np.repeat(np.array(levels, float), D), C * n_carriers)
    carrier = np.tile(np.repeat(np.arange(n_carriers), len(levels) * D), C)
    draw = np.tile(np.arange(D), C * n_carriers * len(levels))
    return dict(k=k, concept=concept, family=family, carrier=carrier, draw=draw, C=C)


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def generator_theta(name: str, tau: float = 0.0, omega: float = 0.0, sep: float = 2.0, pi0: float = 0.0,
                    alpha: float = 0.0, scale: float = 1.0, base: dict = BASE) -> np.ndarray:
    """The raw parameter vector of member `name` at the declared base and the given grid values."""
    b = base
    if name in ("M2B", "M2H", "M2S", "M2K"):
        L = (b["mu_top"] - b["mu_low"]) / (_sig(b["kappa"] * (M.K_MAX - b["x0"])) - _sig(b["kappa"] * (0.0 - b["x0"])))
        core = [b["x0"], b["kappa"], L, b["a"], b["b"], b["mu_top"]]
        if name == "M2B":
            return np.array(core)
        if name == "M2H":
            return np.array(core + [np.log(max(tau, 1e-8))])
        if name == "M2S":
            return np.array(core + [np.log(max(omega, 1e-8))])
        return np.array(core + [alpha, 0.0])
    s = b["sigma"]
    if name == "M3":
        # inherited parameterisation: the high mean is ABSOLUTE (L_high lg_h + step), so the offset from
        # mu_low goes into step: mu_high(k) = mu_low + sep*sigma*scale + sep1*scale*lg_h(k), as for the ordered members
        return np.array([b["x0"], b["kappa"], b["mu_low"], b["mu_low"] + sep * s * scale, b["sep1"] * scale, b["kappa"], s])
    core = [b["mu_low"], np.log(sep * s * scale), np.log(b["sep1"] * scale), b["kappa"], b["kappa"], b["x0"]]
    if name == "M3H":
        return np.array(core + [np.log(s), np.log(max(tau, 1e-8))])
    if name == "M3V":
        return np.array(core + [np.log(s), np.log(b["sigma_high"])])
    if name == "M3L":
        return np.array(core + [np.log(s), np.log(max(pi0, 1e-8) / (1.0 - max(pi0, 1e-8)))])
    raise KeyError(name)


def _ar1(rng, n, L, rho):
    e = np.empty((n, L))
    e[:, 0] = rng.normal(size=n)
    for l in range(1, L):
        e[:, l] = rho * e[:, l - 1] + np.sqrt(1.0 - rho ** 2) * rng.normal(size=n)
    return e


def make_dataset(name: str, theta: np.ndarray, n_per_family: int = 8, D: int = 4, layers=SIM_LAYERS,
                 rho: float = RHO_LAYERS, seed: int = 0, n_carriers: int = N_CARRIERS) -> A.Dataset:
    rng = np.random.default_rng(seed)
    d = make_design(n_per_family, n_carriers, D)
    layers = np.asarray(layers)
    L = layers.size
    n = d["k"].size
    m = M.MEMBERS[name]
    u_c = np.zeros(d["C"])
    if m.hierarchical:
        u_c = rng.normal(0.0, float(np.exp(theta[m.re_index])), size=d["C"])
    eps = _ar1(rng, n, L, rho)
    eps2 = _ar1(rng, n, L, rho)
    unif = rng.uniform(size=n)
    y = np.empty((n, L))
    for l in range(L):
        y[:, l] = M.sample(name, theta, d["k"], u=u_c[d["concept"]],
                           noise=dict(eps=eps[:, l], eps2=eps2[:, l], unif=unif))
    return A.Dataset(y, d["k"], d["concept"], d["family"], layers,
                     meta=dict(generator=name, theta=theta.tolist(), D=D, rho=rho, seed=seed,
                               carrier=d["carrier"], draw=d["draw"], u_c=u_c))


def recovery_points() -> list:
    pts = [("M2B", {})]
    pts += [("M2H", dict(tau=t)) for t in GRID["tau"]]
    pts += [("M2S", dict(omega=w)) for w in GRID["omega"]]
    pts += [("M2K", dict(alpha=a)) for a in GRID["alpha"]]
    pts += [("M3", dict(sep=s)) for s in GRID["sep"]]
    pts += [("M3H", dict(sep=s, tau=t)) for s in GRID["sep"] for t in GRID["tau"]]
    pts += [("M3V", dict(sep=s)) for s in GRID["sep"]]
    pts += [("M3L", dict(sep=s, pi0=p)) for s in GRID["sep"] for p in GRID["pi0"]]
    return pts


def null_points() -> list:
    return [p for p in recovery_points() if M.MEMBERS[p[0]].family == "G"]


# ----------------------------------------------------------------------------------------------
# one replicate through the full §8 procedure -> one CSV row
# ----------------------------------------------------------------------------------------------
def _row(name, kwargs, rep, D, layers, res, seconds, extra=None):
    row = dict(generator=name, family=M.MEMBERS[name].family, grid=json.dumps(kwargs, sort_keys=True), rep=rep, D=D,
               n_layers=len(layers), failed=int(res["failed"]), convergence=round(res["convergence_rate"], 4),
               recovery=round(res["recovery_rate"], 4), fit_seconds=round(res["fit_seconds"], 1),
               wall_seconds=round(seconds, 1))
    for p in A.PREDICTORS:
        b = res["predictors"][p]
        row[f"{p}_decision"] = b.get("decision", "")
        for key in ("point", "lo", "hi", "se"):
            row[f"{p}_ws_{key}"] = b["ws"][key] if "ws" in b else np.nan
        row[f"{p}_families_pooled_sign"] = b.get("ws_families_with_pooled_sign", np.nan)
    row["selected"] = json.dumps(res["selected_counts"], sort_keys=True)
    row["heldout"] = json.dumps({m: round(v, 5) for m, v in res["heldout_logscore_per_trial"].items()}, sort_keys=True)
    if extra:
        row.update(extra)
    return row


def one_replicate(name: str, kwargs: dict, rep: int, D: int, layers, rho: float, cfg: A.Config, seed: int,
                  extra: dict | None = None) -> dict:
    t0 = _time.time()
    theta = generator_theta(name, **kwargs)
    # deterministic dataset seed: (seed, member index, grid values, rep, D) — never Python's per-process str hash
    grid_tag = sum((i + 1) * int(round(1000 * float(v))) for i, v in enumerate(kwargs.get(x, 0.0) for x in ("tau", "omega", "sep", "pi0", "alpha", "scale")))
    ds_seed = int(np.random.default_rng([seed, M.ALL_MEMBERS.index(name), grid_tag % (2**31 - 1), rep, D]).integers(2**31))
    ds = make_dataset(name, theta, n_per_family=8, D=D, layers=layers, rho=rho, seed=ds_seed)
    res = A.analyze_dataset(ds, cfg, seed=ds_seed)
    return _row(name, kwargs, rep, D, layers, res, _time.time() - t0, extra)


def run_points(points: list, n_rep: int, D: int, layers, rho: float, cfg: A.Config, seed: int, n_jobs: int,
               out_csv: str, extras: dict | None = None, chunk: int = 32):
    """Runs every (point, rep) through one_replicate, appending rows to out_csv as chunks complete."""
    from joblib import Parallel, delayed
    tasks = [(name, kw, r) for (name, kw) in points for r in range(n_rep)]
    done = set()
    if os.path.exists(out_csv):
        with open(out_csv) as fh:
            for row in csv.DictReader(fh):
                done.add((row["generator"], row["grid"], int(row["rep"]), int(row["D"])))
    tasks = [t for t in tasks if (t[0], json.dumps(t[1], sort_keys=True), t[2], D) not in done]
    print(f"{len(tasks)} replicates to run ({len(done)} already in {out_csv}), n_jobs={n_jobs}", flush=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    t0 = _time.time()
    for i in range(0, len(tasks), chunk):
        batch = tasks[i:i + chunk]
        rows = Parallel(n_jobs=n_jobs)(delayed(one_replicate)(name, kw, r, D, layers, rho, cfg, seed,
                                                              (extras or {}).get((name, json.dumps(kw, sort_keys=True))))
                                       for (name, kw, r) in batch)
        new = not os.path.exists(out_csv)
        with open(out_csv, "a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"  {i + len(batch)}/{len(tasks)} done, {(_time.time() - t0) / 60:.1f} min", flush=True)


# ----------------------------------------------------------------------------------------------
# summaries
# ----------------------------------------------------------------------------------------------
def summarize(out_csv: str, predictor: str = "selection") -> "pd.DataFrame":
    import pandas as pd
    df = pd.read_csv(out_csv)
    dec = f"{predictor}_decision"
    rows = []
    for (g, grid, D), sub in df.groupby(["generator", "grid", "D"]):
        n = len(sub)
        counts = sub[dec].value_counts()
        point = sub[f"{predictor}_ws_point"]
        truth = point.mean()                       # the estimand proxy: the replicate mean of the point estimate
        cover = np.mean((sub[f"{predictor}_ws_lo"] <= truth) & (truth <= sub[f"{predictor}_ws_hi"]))
        rows.append(dict(generator=g, family=M.MEMBERS[g].family, grid=grid, D=D, n=n,
                         mixture=counts.get("mixture", 0) / n, graded=counts.get("graded", 0) / n,
                         inconclusive=counts.get("inconclusive", 0) / n, failure=counts.get("assay failure", 0) / n,
                         mean_point=truth, sd_point=point.std(ddof=1) if n > 1 else np.nan, coverage=cover,
                         mean_se=sub[f"{predictor}_ws_se"].mean(), convergence=sub["convergence"].mean(),
                         mean_fit_s=sub["fit_seconds"].mean()))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# §10: the per-trial gain of a mixture generator over the best graded member, and its calibration
# ----------------------------------------------------------------------------------------------
def expected_gain(name: str, theta: np.ndarray, seed: int = 0, n_per_family: int = 32, D: int = 4,
                  cfg: A.Config | None = None, graded=M.FAMILY_G) -> dict:
    """E[log q_true - log q_G*] per trial on fresh data, G* = the graded member with the best training
    joint log-likelihood at large sample (8 x n_per_family concepts)."""
    cfg = A.Config() if cfg is None else cfg
    tr = make_dataset(name, theta, n_per_family, D, layers=(41,), rho=0.0, seed=seed)
    te = make_dataset(name, theta, n_per_family, D, layers=(41,), rho=0.0, seed=seed + 1)
    train = M.Trials.build(tr.y[:, 0], tr.k, tr.concept, tr.n_concepts)
    test = M.Trials.build(te.y[:, 0], te.k, te.concept, te.n_concepts, floor_sd=train.floor_sd)
    fits = {g: M.fit(g, train, cfg.n_gh, cfg.n_starts, np.random.default_rng([seed, 7, i])) for i, g in enumerate(graded)}
    best = max(graded, key=lambda g: fits[g].loglik)
    lq_true = M.concept_scores(name, theta, test, cfg.n_gh)
    lq_best = M.concept_scores(best, fits[best].theta, test, cfg.n_gh)
    n = test.n
    return dict(gain=float((lq_true.sum() - lq_best.sum()) / n), best=best,
                gains={g: float((lq_true.sum() - M.concept_scores(g, fits[g].theta, test, cfg.n_gh).sum()) / n) for g in graded},
                converged={g: fits[g].converged for g in graded})


def calibrate_gain(name: str, target: float, kwargs: dict, lo: float = 0.02, hi: float = 3.0, tol: float = 0.05,
                   seed: int = 0, **gain_kw) -> dict:
    """Bisection on `scale` (multiplying both high-state offsets) until expected_gain is within tol
    (relative) of target. Returns the scale, the achieved gain and the trace."""
    trace = []
    def g(scale):
        r = expected_gain(name, generator_theta(name, scale=scale, **kwargs), seed=seed, **gain_kw)
        trace.append(dict(scale=scale, **{k: v for k, v in r.items() if k != "gains"}))
        return r["gain"]
    glo, ghi = g(lo), g(hi)
    if not (glo <= target <= ghi):
        return dict(scale=np.nan, gain=np.nan, trace=trace, note="target outside the bracket")
    for _ in range(20):
        mid = np.sqrt(lo * hi)
        gm = g(mid)
        if abs(gm - target) <= tol * target:
            return dict(scale=mid, gain=gm, trace=trace)
        if gm < target:
            lo, glo = mid, gm
        else:
            hi, ghi = mid, gm
    return dict(scale=mid, gain=gm, trace=trace, note="bisection limit")


def power_points(gain_file: str) -> tuple:
    """Alternatives for §10 from a calibrated-gain JSON: [(name, kwargs-with-scale)], extras per point."""
    with open(gain_file) as fh:
        cal = json.load(fh)
    pts, extras = [], {}
    for entry in cal:
        if not np.isfinite(entry.get("scale", np.nan)):
            continue
        kw = dict(entry["kwargs"]); kw["scale"] = entry["scale"]
        pts.append((entry["generator"], kw))
        extras[(entry["generator"], json.dumps(kw, sort_keys=True))] = dict(target_gain=entry["target"], gain=entry["gain"])
    return pts, extras


# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", choices=["recovery", "calibration", "gain", "power", "summary"])
    ap.add_argument("--n-rep", type=int, default=50)
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--layers", default=",".join(str(l) for l in SIM_LAYERS))
    ap.add_argument("--rho", type=float, default=RHO_LAYERS)
    ap.add_argument("--n-jobs", type=int, default=14)
    ap.add_argument("--n-starts-inner", type=int, default=M.N_STARTS)
    ap.add_argument("--n-gh", type=int, default=M.GH_NODES_DEFAULT)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=None)
    ap.add_argument("--gain-file", default=os.path.join(OUT_DIR, "gain_calibration.json"))
    ap.add_argument("--generators", default=None, help="comma list to restrict the generator set")
    a = ap.parse_args()
    layers = tuple(int(x) for x in a.layers.split(","))
    cfg = A.Config(n_starts_inner=a.n_starts_inner, n_gh=a.n_gh)
    os.makedirs(OUT_DIR, exist_ok=True)
    if a.task == "summary":
        for p in A.PREDICTORS:
            print(f"--- predictor: {p}")
            print(summarize(a.out, p).to_string())
        return
    if a.task == "gain":
        out = []
        names = M.FAMILY_X if a.generators is None else tuple(a.generators.split(","))
        for name in names:
            kw = dict(tau=0.5) if name == "M3H" else (dict(pi0=0.05) if name == "M3L" else {})
            for target in GAINS:
                t0 = _time.time()
                r = calibrate_gain(name, target, kw, seed=a.seed, cfg=cfg)
                out.append(dict(generator=name, kwargs=kw, target=target, scale=r["scale"], gain=r["gain"],
                                note=r.get("note", ""), trace=r["trace"]))
                print(f"{name} target {target}: scale {r['scale']:.4f} gain {r['gain']:.5f} ({(_time.time()-t0)/60:.1f} min) {r.get('note','')}", flush=True)
                with open(a.gain_file, "w") as fh:
                    json.dump(out, fh, indent=1, default=float)
        return
    if a.task == "recovery":
        points = recovery_points()
        out = a.out or os.path.join(OUT_DIR, f"recovery_D{a.D}.csv")
        extras = None
    elif a.task == "calibration":
        points = null_points()
        out = a.out or os.path.join(OUT_DIR, f"calibration_D{a.D}.csv")
        extras = None
    else:
        points, extras = power_points(a.gain_file)
        out = a.out or os.path.join(OUT_DIR, f"power_D{a.D}.csv")
    if a.generators:
        keep = set(a.generators.split(","))
        points = [p for p in points if p[0] in keep]
    run_points(points, a.n_rep, a.D, layers, a.rho, cfg, a.seed, a.n_jobs, out, extras)
    print(summarize(out).to_string())


if __name__ == "__main__":
    main()
