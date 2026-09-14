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
import hashlib
import json
import os
import time as _time

import numpy as np

import analyze as A
import models as M

A.register_loaded_source("simulate.py", __file__)      # the snapshot carries THIS loaded code's digest (review 6 finding 1)


def config_hash(cfg: "A.Config", D: int, layers, seed: int, rho: float = None) -> str:
    """12 hex digits over the three code files and the run settings: written into every row and into the gain
    file, and checked on resume, so rows from two numerical methods can never be blended (Codex, 2026-09-11)."""
    h = hashlib.sha256()
    # the three code files AS LOADED (digests bound at each module's import — review 7): a row or gain file names the
    # implementation that produced it, never the file that happens to be on disk when the hash is computed
    for f in ("models.py", "analyze.py", "simulate.py"):
        if f not in A.LOADED_SOURCES:
            raise RuntimeError(f"no loaded-source digest for {f}: the module must register itself at import")
        h.update(f"{f}:{A.LOADED_SOURCES[f]}".encode())
    settings = dict(n_starts=cfg.n_starts, n_starts_inner=cfg.n_starts_inner, n_gh=cfg.n_gh, n_outer=cfg.n_outer,
                    n_inner=cfg.n_inner, n_boot=cfg.n_boot, members_G=list(cfg.members_G), members_X=list(cfg.members_X),
                    interval=cfg.interval, n_boot_refit=cfg.n_boot_refit, refit_min_usable=cfg.refit_min_usable,
                    D=int(D), layers=[int(l) for l in layers], seed=int(seed), rho=RHO_LAYERS if rho is None else rho,
                    trap=(M.TRAP_POINTS, M.OUTER_POINTS, M.TRAP_HALFWIDTH, M.PRIOR_HALFWIDTH),
                    newton=(M.NEWTON_STEPS, M.NEWTON_CANDIDATES, M.GRID_POINTS, M.GRID_HALFWIDTH), jitter=M.JITTER_SD,
                    lbfgsb=M.LBFGSB_OPTIONS)
    h.update(json.dumps(settings, sort_keys=True, default=str).encode())
    return h.hexdigest()[:12]

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "sim_results")
SIM_LAYERS = (25, 33, 41, 49, 57)     # declared reduced grid inside the workspace band 23–57
RHO_LAYERS = 0.9                      # stand-in residual correlation between ADJACENT PHYSICAL layers (PILOT measures it);
                                      # between sampled layers l1 < l2 the correlation is RHO_LAYERS ** (l2 - l1)
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


def _ar1(rng, n, layers, rho):
    """Standard-normal noise for n trials at the listed physical layers, AR(1) with coefficient rho per physical
    layer step: corr(e_l1, e_l2) = rho ** |l2 - l1|."""
    layers = np.asarray(layers)
    L = layers.size
    e = np.empty((n, L))
    e[:, 0] = rng.normal(size=n)
    for l in range(1, L):
        r = rho ** abs(int(layers[l]) - int(layers[l - 1]))
        e[:, l] = r * e[:, l - 1] + np.sqrt(1.0 - r ** 2) * rng.normal(size=n)
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
    eps = _ar1(rng, n, layers, rho)
    eps2 = _ar1(rng, n, layers, rho)
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


def base_null_points() -> list:
    """One grid value per graded member (the five-layer check): M2B; M2H tau 0.5; M2S omega 0.5; M2K alpha 1."""
    return [("M2B", {}), ("M2H", dict(tau=0.5)), ("M2S", dict(omega=0.5)), ("M2K", dict(alpha=1.0))]


# ----------------------------------------------------------------------------------------------
# one replicate through the full §8 procedure -> one CSV row
# ----------------------------------------------------------------------------------------------
def _row(name, kwargs, rep, D, layers, res, seconds, extra=None, code_hash=""):
    row = dict(generator=name, family=M.MEMBERS[name].family, grid=json.dumps(kwargs, sort_keys=True), rep=rep, D=D,
               n_layers=len(layers), code_hash=code_hash, runtime=runtime_versions(),
               failed=int(res["failed"]), failed_reason=res.get("failed_reason", ""),
               convergence=round(res["convergence_rate"], 4), inner_convergence=round(res.get("inner_convergence_rate", np.nan), 4),
               inner_nonfinite=int(res.get("inner_nonfinite", 0)), recovery=round(res["recovery_rate"], 4),
               fit_seconds=round(res["fit_seconds"], 1), wall_seconds=round(seconds, 1),
               interval_method=res.get("interval", {}).get("method", "cluster"),
               interval_n_rep=res.get("interval", {}).get("n_rep", np.nan),
               interval_n_used=res.get("interval", {}).get("n_used", np.nan),
               interval_n_failed=res.get("interval", {}).get("n_failed", np.nan),
               interval_usable=int(bool(res.get("interval", {}).get("usable", True))),
               interval_fit_seconds=round(float(res.get("interval", {}).get("fit_seconds", 0.0)), 1),
               interval_seed=res.get("interval", {}).get("seed", np.nan),
               interval_policy=res.get("interval", {}).get("policy", ""),
               interval_failed_reasons=json.dumps(res.get("interval", {}).get("failed_reasons", [])),
               interval_outer_folds=json.dumps(res.get("interval", {}).get("outer_folds", [])),
               interval_replicates=json.dumps(res.get("interval", {}).get("replicates", []), default=float),
               interval_ident=res.get("interval", {}).get("ident", ""),
               interval_n_damaged=res.get("interval", {}).get("n_damaged", 0),
               primary_available=int(bool(res.get("primary_available", not res["failed"]))))
    # per predictor: the decision and, for EVERY band and the paired ws - early statistic, point / lo / hi / se; with
    # the refitting interval also the companion cluster interval and the predictor's own interval availability
    # (review 3, finding 5: nothing computed in memory is lost at the row boundary)
    for p in A.PREDICTORS:
        b = res["predictors"][p]
        row[f"{p}_decision"] = b.get("decision", "")
        for band in ("ws", "early", "late", "ws_minus_early"):
            for key in ("point", "lo", "hi", "se"):
                row[f"{p}_{band}_{key}"] = b[band][key] if band in b else np.nan
        for band in ("ws", "early", "late", "ws_minus_early"):        # the companion cluster interval of EVERY band
            for key in ("lo", "hi", "se"):
                row[f"{p}_cluster_{band}_{key}"] = b["cluster"][band][key] if "cluster" in b and band in b["cluster"] else np.nan
        row[f"{p}_interval_usable"] = int(bool(b.get("usable", True)))
        row[f"{p}_interval_n_used"] = b.get("interval", {}).get("n_used", np.nan)
        row[f"{p}_families_pooled_sign"] = b.get("ws_families_with_pooled_sign", np.nan)
    row["selected"] = json.dumps(res["selected_counts"], sort_keys=True)
    row["heldout"] = json.dumps({m: round(v, 5) for m, v in res["heldout_logscore_per_trial"].items()}, sort_keys=True)
    # per-concept audit detail (Codex, 2026-09-11): the out-of-fold Delta_c of each predictor and every member's
    # held-out joint log score per concept, per layer — enough to rescore alternative interval rules offline
    row["delta_per_concept"] = json.dumps({p: np.round(res["delta"][p], 5).tolist() for p in A.PREDICTORS})
    row["logq_per_concept"] = json.dumps({m: np.round(res["logq"][:, i, :], 4).tolist() for i, m in enumerate(res["members"])})
    row["selected_per_layer_fold"] = json.dumps(res["selected"])
    if extra:
        row.update(extra)
    return row


def dataset_seed(name: str, kwargs: dict, rep: int, D: int, seed: int) -> int:
    """The deterministic dataset seed of a (member, grid point, replicate, D) — never Python's per-process str hash.
    Grid points with at most one grid value keep the v1.2 weighted tag (the d4v12b null rows depend on it); points
    with two or more values (M3H, M3L recovery points, every power point) use a digest of the sorted grid, because
    the weighted tag collided — (tau 0.5, sep 1) and (tau 2, sep 0.5) both gave 3500 (Codex, review 4 finding 1).
    No row of such a point has landed under the old tag."""
    if len(kwargs) <= 1:
        grid_tag = sum((i + 1) * int(round(1000 * float(v))) for i, v in enumerate(kwargs.get(x, 0.0) for x in ("tau", "omega", "sep", "pi0", "alpha", "scale")))
    else:
        grid_tag = int(hashlib.sha256(json.dumps({k: float(v) for k, v in kwargs.items()}, sort_keys=True).encode()).hexdigest()[:8], 16)
    return int(np.random.default_rng([seed, M.ALL_MEMBERS.index(name), grid_tag % (2**31 - 1), rep, D]).integers(2**31))


def one_replicate(name: str, kwargs: dict, rep: int, D: int, layers, rho: float, cfg: A.Config, seed: int,
                  extra: dict | None = None, code_hash: str = "") -> dict:
    t0 = _time.time()
    theta = generator_theta(name, **kwargs)
    ds_seed = dataset_seed(name, kwargs, rep, D, seed)
    ds = make_dataset(name, theta, n_per_family=8, D=D, layers=layers, rho=rho, seed=ds_seed)
    res = A.analyze_dataset(ds, cfg, seed=ds_seed)
    return _row(name, kwargs, rep, D, layers, res, _time.time() - t0, extra, code_hash)


def run_points(points: list, n_rep: int, D: int, layers, rho: float, cfg: A.Config, seed: int, n_jobs: int,
               out_csv: str, extras: dict | None = None, chunk: int = 32, on_chunk=None, shard=(0, 1)):
    """Runs every (point, rep) through one_replicate, appending rows to out_csv as chunks complete.
    on_chunk(out_csv, n_done, n_total, elapsed_seconds) is called after every chunk is written.
    shard=(i, N) or (ids, N): the tasks whose index modulo N is i / is in ids (the seeds are per
    (point, rep), so shards are disjoint and their CSVs concatenate)."""
    from joblib import Parallel, delayed
    code_hash = config_hash(cfg, D, layers, seed, rho)
    tasks = [(name, kw, r) for (name, kw) in points for r in range(n_rep)]
    ids = set(shard[0]) if isinstance(shard[0], (list, tuple, set)) else {int(shard[0])}
    tasks = [t for i, t in enumerate(tasks) if i % int(shard[1]) in ids]
    done = set()
    if os.path.exists(out_csv):
        with open(out_csv) as fh:
            for row in csv.DictReader(fh):
                if row.get("code_hash", "") != code_hash:
                    raise SystemExit(f"{out_csv} holds rows from code/config {row.get('code_hash')!r}, this run is {code_hash!r}: "
                                     f"never blend numerical methods — use a new run namespace")
                done.add((row["generator"], row["grid"], int(row["rep"]), int(row["D"])))
    tasks = [t for t in tasks if (t[0], json.dumps(t[1], sort_keys=True), t[2], D) not in done]
    print(f"{len(tasks)} replicates to run ({len(done)} already in {out_csv}), n_jobs={n_jobs}, code/config {code_hash}", flush=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    t0 = _time.time()
    for i in range(0, len(tasks), chunk):
        batch = tasks[i:i + chunk]
        rows = Parallel(n_jobs=n_jobs)(delayed(one_replicate)(name, kw, r, D, layers, rho, cfg, seed,
                                                              (extras or {}).get((name, json.dumps(kw, sort_keys=True))), code_hash)
                                       for (name, kw, r) in batch)
        new = not os.path.exists(out_csv)
        with open(out_csv, "a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"  {i + len(batch)}/{len(tasks)} done, {(_time.time() - t0) / 60:.1f} min", flush=True)
        if on_chunk is not None:
            on_chunk(out_csv, len(done) + i + len(batch), len(done) + len(tasks), _time.time() - t0)


# ----------------------------------------------------------------------------------------------
# summaries
# ----------------------------------------------------------------------------------------------
def recovery_merged(recovery_csv: str, calibration_csv: str, n_rep: int = 200) -> "pd.DataFrame":
    """The §7.5 recovery table: the mixture generators from the recovery stage plus the graded grid points'
    replicates 0..n_rep-1 from the calibration stage (identical seeds and configuration; not refitted)."""
    import pandas as pd
    rec = pd.read_csv(recovery_csv)
    cal = pd.read_csv(calibration_csv)
    cal = cal[cal["rep"] < n_rep]
    if rec["code_hash"].nunique() > 1 or cal["code_hash"].nunique() > 1 or set(rec["code_hash"]) != set(cal["code_hash"]):
        raise SystemExit("recovery_merged: the two stages carry different code/config hashes")
    return pd.concat([rec, cal], ignore_index=True)


def summarize(out_csv: str, predictor: str = "selection") -> "pd.DataFrame":
    import pandas as pd
    df = pd.read_csv(out_csv)
    dec = f"{predictor}_decision"
    rows = []
    for (g, grid, D), sub in df.groupby(["generator", "grid", "D"]):
        n = len(sub)
        counts = sub[dec].value_counts()
        # three separate things (review 3, finding 3): a valid original fit / point (failed == 0) — every one of them
        # estimates the unconditional procedure target theta_g, whether or not its interval could be built; the
        # predictor's own interval availability ({p}_interval_usable, finite lo/hi) — the coverage denominator; and
        # the assay's availability (the decision), counted as a failure rate of its own
        points = sub[sub["failed"] == 0]
        point = points[f"{predictor}_ws_point"]
        # the coverage estimand theta_g(D, L) = E[band-mean Delta] over draws, folds and optimiser randomness at the
        # design sizes, estimated by the replicate mean; its Monte-Carlo SE is reported beside it (pre-reg §10)
        truth = point.mean()
        truth_se = point.std(ddof=1) / np.sqrt(len(point)) if len(point) > 1 else np.nan
        lo, hi = f"{predictor}_ws_lo", f"{predictor}_ws_hi"
        iv = points
        if f"{predictor}_interval_usable" in sub.columns:
            iv = iv[iv[f"{predictor}_interval_usable"] == 1]
        iv = iv[np.isfinite(iv[lo].astype(float)) & np.isfinite(iv[hi].astype(float))]
        cover = np.mean((iv[lo] <= truth) & (truth <= iv[hi])) if len(iv) else np.nan
        rows.append(dict(generator=g, family=M.MEMBERS[g].family, grid=grid, D=D, n=n,
                         mixture=counts.get("mixture", 0) / n, graded=counts.get("graded", 0) / n,
                         inconclusive=counts.get("inconclusive", 0) / n, failure=counts.get("assay failure", 0) / n,
                         n_points=len(points), n_usable=len(iv), n_interval_missing=len(points) - len(iv),
                         mean_point=truth, ref_se=truth_se,
                         sd_point=point.std(ddof=1) if len(point) > 1 else np.nan, coverage=cover,
                         mean_se=iv[f"{predictor}_ws_se"].mean() if len(iv) else np.nan, convergence=sub["convergence"].mean(),
                         inner_convergence=sub["inner_convergence"].mean() if "inner_convergence" in sub else np.nan,
                         mean_fit_s=sub["fit_seconds"].mean()))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# §10: the per-trial gain of a mixture generator over the best graded member, and its calibration
# ----------------------------------------------------------------------------------------------
def expected_gain(name: str, theta: np.ndarray, seed: int = 0, n_per_family: int = 32, D: int = 4,
                  cfg: A.Config | None = None, graded=M.FAMILY_G, n_starts: int | None = None,
                  warm: dict | None = None, challenge: bool = False) -> dict:
    """E[log q_true - log q_G*] per trial on fresh data, G* = the graded member with the best training
    joint log-likelihood at large sample (8 x n_per_family concepts). The truth term is scored under the
    GENERATING density (floor 0 for M3V: the fitting floor belongs to fitted predictors only — Codex 2026-09-11);
    `se` is the concept-cluster standard error of the per-trial gain.

    The reference fit is an ORACLE at large sample, not the pipeline's fit, and it must find the best solution
    there is. Run d4v12b (12 Sept 2026, M3L at 0.01 nat): with the pipeline's 8 starts the best-found M2K
    solution at 256 concepts was reached by one start of that batch — the other seven ended in a basin 155 nat
    worse in training likelihood and 0.003 nat per trial worse held out — and whether that one start landed
    flipped with the data at a relative change of 2.4e-6 in the scale, so the gain alternated between 0.00806
    and 0.01097 and the bisection could not close. Hence (calibration side only; models.py and the pipeline
    untouched): REF_STARTS jittered starts per graded member ("cold"); `warm` = {member: [theta, ...]}, the
    distinct basin candidates found earlier on the bisection path, each run as one further start ("warm"), so
    a basin once found travels along the path; a member whose best-found solution is reached by fewer than
    REF_MIN_STARTS_AT_BEST DISTINCT cold starts gets REF_EXTRA_STARTS more ("extra": jittered from a further
    seed, never the unjittered moment start that the cold batch already holds — Codex, 12 Sept, finding 1 —
    and mirrored in the skew coordinates on every second start, so both skew orientations are covered). The
    counts are returned: `starts_at_best` = distinct cold + extra starts within REF_BASIN_TOL of the best
    converged solution over ALL sources (a cold discovery counts only if it reproduces the best combined
    solution), `warm_at_best` separately; `ref_reproduced` (read by the gate) uses the cold/extra/challenge
    count of the selected reference — distinct by INITIAL VECTOR, every run carrying its start (`x0`), batch and
    final vector so the discoveries can be audited. Reproduction is not proof of global optimality: it says the
    best-found solution was reached independently at least twice. `challenge=True` (the FINAL evaluation at a
    frozen scale, and the check): a declared, independently seeded, stronger training-only search on the same
    training draw — deliberately separated skew starts (alpha coordinates at ±ALPHA_SEP, both orientations) plus
    jittered starts at twice the jitter — before the test scores are read; if it improves the best likelihood by
    more than REF_BASIN_TOL the reference IS the improved solution (the gain is scored against it, the
    improvement recorded in `challenge_improved`, and the reproduction count then refers to that solution). It
    never touches the test draw. `candidates` = the distinct basins found (best run per likelihood cluster), the
    warm set for the next evaluation; `runs` = one record per start for the archive."""
    cfg = A.Config() if cfg is None else cfg
    n_starts = REF_STARTS if n_starts is None else int(n_starts)
    tr = make_dataset(name, theta, n_per_family, D, layers=(41,), rho=0.0, seed=seed)
    te = make_dataset(name, theta, n_per_family, D, layers=(41,), rho=0.0, seed=seed + 1)
    train = M.Trials.build(tr.y[:, 0], tr.k, tr.concept, tr.n_concepts)
    test = M.Trials.build(te.y[:, 0], te.k, te.concept, te.n_concepts, floor_sd=train.floor_sd)
    truth = M.Trials.build(te.y[:, 0], te.k, te.concept, te.n_concepts, floor_sd=0.0)
    fits, runs_by, extra, improved = {}, {}, {g: 0 for g in graded}, {g: 0.0 for g in graded}
    for i, g in enumerate(graded):
        # the cold fit with full provenance: every start (the §9 recovery batches included) carries its initial vector
        # and batch id from where it was generated — nothing is reconstructed afterwards (Codex, review 4 finding 3)
        runs, level, secs = _fit_reference(g, train, n_starts, np.random.default_rng([seed, 7, i]), cfg.n_gh, tag=f"{seed}:{i}")
        size = M.MEMBERS[g].n_params
        for k, w in enumerate(_warm_list(warm, g, size)):
            t0 = _time.time()
            runs += _tag(M._run_starts(g, train, w[None, :], cfg.n_gh, dict(M.LBFGSB_OPTIONS)), "warm", w[None, :], batch=f"warm:{k}")
            secs += _time.time() - t0
        if _starts_at_best(runs) < REF_MIN_STARTS_AT_BEST:
            t0 = _time.time()
            starts = _extra_starts(g, train, REF_EXTRA_STARTS, np.random.default_rng([seed, 7, i, 1]))
            runs += _tag(M._run_starts(g, train, starts, cfg.n_gh, dict(M.LBFGSB_OPTIONS)), "extra", starts, batch=f"extra:{seed}:{i}:1")
            secs += _time.time() - t0
            extra[g] = REF_EXTRA_STARTS
        if challenge:
            starts = _challenge_starts(g, train, REF_CHALLENGE_STARTS, np.random.default_rng([seed, 7, i, 2]))
            t0 = _time.time()
            ch = _tag(M._run_starts(g, train, starts, cfg.n_gh, dict(M.LBFGSB_OPTIONS)), "challenge", starts, batch=f"challenge:{seed}:{i}:2")
            secs += _time.time() - t0
            before = max((r["loglik"] for r in runs if r["converged"] and np.isfinite(r["loglik"])), default=-np.inf)
            after = max((r["loglik"] for r in ch if r["converged"] and np.isfinite(r["loglik"])), default=-np.inf)
            improved[g] = float(after - before) if after > before + REF_BASIN_TOL else 0.0
            runs += ch
        kept, n_conv = M._pick(runs)
        if kept is None or not np.isfinite(kept["loglik"]):
            raise RuntimeError(f"expected_gain({name}): the {g} reference fit did not produce a finite likelihood")
        fits[g] = M.FitResult(g, kept["theta"], kept["loglik"], bool(kept["converged"]), n_conv, len(runs), level,
                              sum(int(r["nfev"]) for r in runs), sum(int(r["nit"]) for r in runs), secs, runs)
        runs_by[g] = runs
    starts_at_best = {g: _starts_at_best(runs_by[g]) for g in graded}
    warm_at_best = {g: _starts_at_best(runs_by[g], sources=("warm",)) for g in graded}
    best = max(graded, key=lambda g: fits[g].loglik)
    lq_true = M.concept_scores(name, theta, truth, cfg.n_gh)
    lq_by = {g: M.concept_scores(g, fits[g].theta, test, cfg.n_gh) for g in graded}
    n_c = test.n_per_concept()
    per_concept = (lq_true - lq_by[best]) / n_c                     # per-trial gain per concept
    gain = float((lq_true.sum() - lq_by[best].sum()) / test.n)
    se = float(np.std(per_concept, ddof=1) / np.sqrt(per_concept.size))
    return dict(gain=gain, se=se, best=best,
                gains={g: float((lq_true.sum() - lq_by[g].sum()) / test.n) for g in graded},
                converged={g: fits[g].converged for g in graded},
                loglik={g: float(fits[g].loglik) for g in graded},
                theta={g: [float(v) for v in fits[g].theta] for g in graded},
                n_starts={g: int(fits[g].n_starts) for g in graded},
                starts_at_best=starts_at_best, warm_at_best=warm_at_best, extra_starts=extra,
                challenge=bool(challenge), challenge_improved=improved,
                ref_reproduced=bool(starts_at_best[best] >= REF_MIN_STARTS_AT_BEST),
                candidates={g: _basin_candidates(runs_by[g]) for g in graded},
                runs={g: [dict(source=r["source"], batch=r.get("batch", ""),
                               loglik=round(float(r["loglik"]), 3) if np.isfinite(r["loglik"]) else None,
                               converged=bool(r["converged"]), nit=int(r["nit"]), x0=r.get("x0"),
                               theta=[round(float(v), 5) for v in r["theta"]] if np.all(np.isfinite(r["theta"])) else None)
                          for r in runs_by[g]] for g in graded})


REF_STARTS = 32                  # jittered "cold" starts per graded reference fit (the pipeline's 8 found the best M2K solution once)
REF_MIN_STARTS_AT_BEST = 2       # the best-found reference solution must be reached by at least two distinct cold/extra/challenge starts
REF_EXTRA_STARTS = 24            # else this many more jittered starts (no repeated moment start; skew-mirrored on every second)
REF_CHALLENGE_STARTS = 32        # the final training-only challenge: separated skew starts + jittered starts at twice the jitter
REF_BASIN_TOL = 0.5              # a start "reaches" a solution when its loglik is within this (nat, total)
REF_MAX_CANDIDATES = 4           # distinct basins carried forward as warm starts per member
ALPHA_SEP = 2.0                  # the challenge's deliberately separated skew starts sit at alpha = ±ALPHA_SEP
COUNTED_SOURCES = ("cold", "recovery1", "recovery2", "extra", "challenge")   # sources whose distinct discoveries count


def _fit_reference(name: str, data: "M.Trials", n_starts: int, rng: np.random.Generator, n_gh: int,
                   jitter_sd: float = M.JITTER_SD, tag: str = "") -> tuple:
    """The cold reference fit with full start provenance: models.fit's multi-start and its §9 recovery chain (16 more
    starts at the jitter when no start converged, then 16 at twice the jitter), drawn from `rng` in the same order
    as models.fit, every run tagged with its initial vector and batch id where it is generated (Codex, review 4
    finding 3). Returns (runs, recovery level, seconds)."""
    opts = dict(M.LBFGSB_OPTIONS)
    t0 = _time.time()
    starts = M.starts_from_moments(name, data, n_starts, rng, jitter_sd)
    runs = _tag(M._run_starts(name, data, starts, n_gh, opts), "cold", starts, batch=f"cold:{tag}")
    level = 0
    kept, n_conv = M._pick(runs)
    if kept is None or n_conv == 0:
        level = 1
        more = M.starts_from_moments(name, data, M.N_STARTS_RECOVERY + 1, rng, jitter_sd)[1:]
        runs += _tag(M._run_starts(name, data, more, n_gh, opts), "recovery1", more, batch=f"recovery1:{tag}")
        kept, n_conv = M._pick(runs)
        if kept is None or n_conv == 0:
            level = 2
            more = M.starts_from_moments(name, data, M.N_STARTS_RECOVERY + 1, rng, 2.0 * jitter_sd)[1:]
            runs += _tag(M._run_starts(name, data, more, n_gh, opts), "recovery2", more, batch=f"recovery2:{tag}")
    return runs, level, _time.time() - t0


def _tag(runs: list, source: str, x0=None, batch: str = "") -> list:
    """Tag runs with their source and batch, and with their initial vector when the starts array is given."""
    out = []
    for j, r in enumerate(runs):
        d = dict(r, source=source, batch=batch)
        if x0 is not None and j < len(x0):
            d["x0"] = [round(float(v), 5) for v in np.asarray(x0)[j]]
        out.append(d)
    return out


def _warm_list(warm: dict | None, member: str, size: int) -> list:
    """The warm starts for `member` as a list of finite arrays of the right length (a single theta or a list)."""
    if not warm or warm.get(member) is None:
        return []
    arr = np.asarray(warm[member], dtype=float)
    rows = [arr] if arr.ndim == 1 else list(arr) if arr.ndim == 2 else []
    return [r for r in rows if r.size == size and np.all(np.isfinite(r))]


def _extra_starts(name: str, data: "M.Trials", n: int, rng: np.random.Generator, jitter_sd: float = M.JITTER_SD) -> np.ndarray:
    """n jittered starts for the extra batch: the unjittered moment start is dropped (the cold batch holds it, and a
    repeat would count one initial point twice — Codex, 12 Sept 2026), and every second start is mirrored in the
    member's skew coordinates (parameters named alpha*) so both orientations are tried."""
    starts = M.starts_from_moments(name, data, n + 1, rng, jitter_sd)[1:]
    for j, p in enumerate(M.MEMBERS[name].params):
        if p.startswith("alpha"):
            starts[1::2, j] *= -1.0
    return starts


def _starts_at_best(runs: list, tol: float = REF_BASIN_TOL, sources: tuple = COUNTED_SOURCES) -> int:
    """How many DISTINCT initial vectors among the converged runs from `sources` ended within tol nat (total
    training log-likelihood) of the best converged solution over ALL runs (every source, warm included). Runs
    without a recorded initial vector count one each."""
    conv = [r for r in runs if r["converged"] and np.isfinite(r["loglik"])]
    if not conv:
        return 0
    top = max(r["loglik"] for r in conv)
    hits = [r for r in conv if top - r["loglik"] <= tol and r.get("source", "cold") in sources]
    return len({tuple(r["x0"]) if r.get("x0") is not None else ("row", j) for j, r in enumerate(hits)})


def _challenge_starts(name: str, data: "M.Trials", n: int, rng: np.random.Generator,
                      jitter_sd: float = 2.0 * M.JITTER_SD) -> np.ndarray:
    """The final training-only challenge batch (Codex, 12 Sept 2026, review 3 finding 6): for a member with skew
    parameters (alpha*), four starts at the moment start with the skew coordinates set to every sign combination of
    ±ALPHA_SEP — deliberately separated basins, not a mirrored jitter — then jittered starts at twice the jitter
    from an independent seed, never the unjittered moment start."""
    base = M.start_from_moments(name, M.moments(data))
    idx = [j for j, p in enumerate(M.MEMBERS[name].params) if p.startswith("alpha")]
    fixed = []
    if idx:
        import itertools
        for signs in itertools.product((1.0, -1.0), repeat=len(idx)):
            s = np.array(base, dtype=float)
            for j, sg in zip(idx, signs):
                s[j] = sg * ALPHA_SEP
            fixed.append(s)
    k = max(0, int(n) - len(fixed))
    jit = M.starts_from_moments(name, data, k + 1, rng, jitter_sd)[1:] if k else np.empty((0, base.size))
    return np.vstack(fixed + [jit]) if fixed else jit


def _basin_candidates(runs: list, tol: float = REF_BASIN_TOL, k: int = REF_MAX_CANDIDATES) -> list:
    """The distinct basins among the converged runs — the best run of each likelihood cluster (clusters tol nat
    apart), best first, at most k — as parameter lists: the warm starts for the next evaluation."""
    conv = sorted([r for r in runs if r["converged"] and np.isfinite(r["loglik"])], key=lambda r: -r["loglik"])
    out = []
    for r in conv:
        if all(abs(r["loglik"] - c["loglik"]) > tol for c in out):
            out.append(r)
        if len(out) >= k:
            break
    return [[float(v) for v in r["theta"]] for r in out]


MIN_BRACKET_WIDTH = 1e-3         # the bisection stops when hi/lo - 1 is below this (0.1 % in scale)


def calibrate_gain(name: str, target: float, kwargs: dict, lo: float = 0.02, hi: float = 3.0, tol: float = 0.05,
                   seed: int = 0, max_iter: int = 30, min_width: float = MIN_BRACKET_WIDTH, **gain_kw) -> dict:
    """Geometric bisection on `scale` (multiplying both high-state offsets) until expected_gain at the FIXED
    calibration seed is within tol (relative) of target — or until the bracket has collapsed (hi/lo - 1 <
    min_width). At a fixed seed g(scale) is deterministic but not continuous: the kept reference fit can jump
    between the best-found solution and a basin far worse in training likelihood (155 nat in run d4v12b,
    12 Sept 2026, M3L at 0.01 nat: 0.00806 below and 0.01097 above scale 0.684661, M2K kept on both sides), and a
    tolerance tighter than that jump can never be met. The distinct basins found along the path travel as warm
    starts (`warm`, per member), which makes the evaluated function depend on the search history: on a collapsed
    bracket both ends are therefore RE-EVALUATED with the full warm set before the width or the jump is read
    (Codex, 12 Sept, finding 5) — if an end is then within tolerance the scale is resolved there; if the target
    has escaped the re-evaluated bracket (a healed jump moves both ends to one side) the bracket is widened on
    that side from the evaluations already made, nearest first, each re-evaluated, and the bisection continues;
    only a jump that survives the re-evaluation freezes the scale at the bracket's geometric centre, where, as
    the declared fallback (not a further chance to pick a seed), the calibration gain is re-measured at twice
    the concepts and a fresh calibration seed (seed + 500, never the check seed), the jump recorded as
    `gain_jump`. Then the independent check at seed + 1000 and
    CHECK_N_PER_FAMILY concepts (warm-started from the calibration's basins on the check's TRAINING draw only;
    the check's test draw is never fitted), and the gate. The final calibration and check evaluations keep every
    start's record (`calib_runs`, `check_runs`) and the check's parameters. Every failure is explicit in `note`
    (bracket, bisection limit, non-finite) and the caller must refuse such an entry."""
    trace = []
    warm = {}
    full = {}                       # the last evaluation in full (its per-start records are archived, not traced)
    def g(scale, s, **kw):
        npf = int(kw.get("n_per_family", gain_kw.get("n_per_family", 32)))
        r = expected_gain(name, generator_theta(name, scale=scale, **kwargs), seed=s, warm=warm or None, **{**gain_kw, **kw})
        for m, cands in r.get("candidates", {}).items():
            _merge_warm(warm, m, cands)
        trace.append(dict(scale=scale, seed=int(s), n_per_family=npf, **{k: v for k, v in r.items() if k not in ("gains", "runs")}))
        full.clear(); full.update(r); full.update(_scale=float(scale), _seed=int(s), _n_per_family=npf)
        if s == seed and "n_per_family" not in kw and not kw.get("challenge"):
            hist.append((float(scale), float(r["gain"])))
        return r["gain"]
    hist = []                       # every (scale, gain) at the calibration seed — the bracket can be rebuilt from it
    within = lambda v: abs(v - target) <= tol * target
    lo0, hi0 = lo, hi
    glo, ghi = g(lo, seed), g(hi, seed)
    if not (np.isfinite(glo) and np.isfinite(ghi)):
        return dict(scale=np.nan, gain=np.nan, trace=trace, note="non-finite gain at a bracket end")
    if not (glo <= target <= ghi):
        return dict(scale=np.nan, gain=np.nan, trace=trace, note=f"target outside the bracket [{glo:.5f}, {ghi:.5f}]")
    mid, gm, resolved, gain_jump, reevaluated, fallback = np.nan, np.nan, False, 0.0, False, False
    budget = max_iter + 12          # calibration-seed evaluations after the two ends, re-evaluations included
    while len(hist) - 2 < budget and not resolved:
        mid = np.sqrt(lo * hi)
        gm = g(mid, seed)
        if not np.isfinite(gm):
            return dict(scale=np.nan, gain=np.nan, trace=trace, note=f"non-finite gain at scale {mid:.6f}")
        if within(gm):
            resolved = True
            break
        if gm < target:
            lo, glo = mid, gm
        else:
            hi, ghi = mid, gm
        if hi / lo - 1.0 >= min_width:
            continue
        # the bracket has collapsed: re-evaluate both ends with every basin found on the path, then read them;
        # if the second end finds a basin the first had not seen, the first is refreshed before the pair is read
        reevaluated = True
        glo = g(lo, seed)
        snap = json.dumps(warm, sort_keys=True)
        ghi = g(hi, seed)
        if json.dumps(warm, sort_keys=True) != snap:
            glo = g(lo, seed)
        if not (np.isfinite(glo) and np.isfinite(ghi)):
            return dict(scale=np.nan, gain=np.nan, trace=trace, note="non-finite gain at a re-evaluated bracket end")
        if within(glo) or within(ghi):
            mid, gm = (lo, glo) if abs(glo - target) <= abs(ghi - target) else (hi, ghi)
            resolved = True
            break
        if glo <= target <= ghi:
            # a discontinuity that survives the re-evaluation: freeze the scale; the declared fallback re-measurement
            # is the final evaluation there (twice the concepts, seed + 500), with the training-only challenge
            fallback = True
            mid = float(np.sqrt(lo * hi))
            gain_jump = float(ghi - glo)
            gm = g(mid, seed + 500, n_per_family=2 * int(gain_kw.get("n_per_family", 32)), challenge=True)
            if not np.isfinite(gm):
                return dict(scale=np.nan, gain=np.nan, trace=trace, note=f"non-finite gain at the frozen scale {mid:.6f}")
            break
        # the target escaped the re-evaluated bracket (a healed jump moved both ends to one side): widen on that
        # side from the scales already visited, nearest first, re-evaluating each, and carry on bisecting
        up = ghi < target
        outer = (sorted({s for s, v in hist if s > hi and v > target}) or [hi0]) if up else \
                (sorted({s for s, v in hist if s < lo and v < target}, reverse=True) or [lo0])
        if up:
            lo, glo = hi, ghi
        else:
            hi, ghi = lo, glo
        found = False
        for s in outer:
            v = g(s, seed)
            if not np.isfinite(v):
                return dict(scale=np.nan, gain=np.nan, trace=trace, note=f"non-finite gain at scale {s:.6f}")
            if within(v):
                mid, gm, resolved, found = s, v, True, True
                break
            if (v > target) == up:
                found = True
                if up:
                    hi, ghi = s, v
                else:
                    lo, glo = s, v
                break
            if up:
                lo, glo = s, v
            else:
                hi, ghi = s, v
        if not found:
            return dict(scale=np.nan, gain=float(gm), trace=trace,
                        note=f"target escaped the bracket {'upward' if up else 'downward'} after re-evaluation")
    if not resolved and not fallback:
        return dict(scale=np.nan, gain=float(gm), trace=trace, note=f"bisection limit: {gm:.5f} vs target {target}")
    # the FINAL calibration evaluation is at the chosen scale, on the calibration training draw, with the declared
    # training-only challenge; it — never an endpoint evaluated for another purpose — is gated and archived
    # (Codex, 12 Sept, review 3 finding 1). The fallback evaluation above already is that final evaluation.
    gain_search = float(gm)
    if not fallback:
        gm = g(mid, seed, challenge=True)
        if not np.isfinite(gm):
            return dict(scale=np.nan, gain=np.nan, trace=trace, note=f"non-finite gain at the final evaluation, scale {mid:.6f}")
    chosen = dict(full)
    # the independent check: a fresh seed and twice the concepts (CHECK_N_PER_FAMILY), its SE being the
    # test-concept variation conditional on the check's own fitted graded reference; the same challenge on its
    # own training draw; its test draw is never fitted
    chk_kw = dict(gain_kw); chk_kw["n_per_family"] = CHECK_N_PER_FAMILY
    chk = expected_gain(name, generator_theta(name, scale=mid, **kwargs), seed=seed + 1000, warm=warm or None, challenge=True, **chk_kw)
    entry = dict(scale=float(mid), gain=float(gm), gain_search=gain_search, gain_jump=gain_jump,
                 bracket_reevaluated=reevaluated, fallback_remeasured=fallback,
                 calib_seed=chosen.get("_seed"), calib_n_per_family=chosen.get("_n_per_family"),
                 gain_check=chk["gain"], gain_check_se=chk["se"], check_seed=seed + 1000, check_n_per_family=CHECK_N_PER_FAMILY,
                 check_best=chk["best"], check_converged=all(chk["converged"].values()),
                 calib_converged=all(chosen["converged"].values()),
                 calib_ref_reproduced=bool(chosen.get("ref_reproduced", False)),
                 check_ref_reproduced=bool(chk.get("ref_reproduced", False)),
                 calib_starts_at_best=chosen.get("starts_at_best"), check_starts_at_best=chk.get("starts_at_best"),
                 calib_warm_at_best=chosen.get("warm_at_best"), check_warm_at_best=chk.get("warm_at_best"),
                 calib_challenge_improved=chosen.get("challenge_improved"), check_challenge_improved=chk.get("challenge_improved"),
                 calib_runs=chosen.get("runs"), calib_theta=chosen.get("theta"), calib_loglik=chosen.get("loglik"),
                 check_runs=chk.get("runs"), check_theta=chk.get("theta"), check_loglik=chk.get("loglik"),
                 trace=trace, note="")
    entry["note"] = gain_gate(entry, target)
    return entry


def _merge_warm(warm: dict, member: str, cands: list, k: int = REF_MAX_CANDIDATES + 2):
    """Add basin candidates to the warm set of `member`, newest first, deduplicated to 4 decimals, at most k kept."""
    have = [list(c) for c in warm.get(member, [])]
    for c in cands:
        key = [round(float(v), 4) for v in c]
        if all([round(float(v), 4) for v in h] != key for h in have):
            have.insert(0, [float(v) for v in c])
    warm[member] = have[:k]


CHECK_N_PER_FAMILY = 64         # the independent check draws 8 x 64 concepts (the calibration draws 8 x 32)
GATE_REL_SE = 0.20               # the check's SE must be <= 20 % of the target (else more reference simulation)
GATE_REL_AGREE = 0.25            # and |check - target| <= 25 % of the target — and |gain - target| likewise


def gain_gate(entry: dict, target: float) -> str:
    """The §10 acceptance gate for one (member, target) calibration: '' if it passes, else the reason.
    Declared rule: finite scale/gain/check/SE; every graded reference fit converged in the calibration draw
    and in the check draw; the selected reference's optimum reached by at least REF_MIN_STARTS_AT_BEST starts
    in both draws (12 Sept 2026); check SE <= GATE_REL_SE * target; |check - target| <= GATE_REL_AGREE * target;
    and (12 Sept 2026, with the bracket-width stop) |gain - target| <= GATE_REL_AGREE * target for the
    calibration side too, since the search tolerance no longer bounds it by itself."""
    for key in ("scale", "gain", "gain_check", "gain_check_se"):
        v = entry.get(key, np.nan)
        if v is None or not np.isfinite(v):
            return f"{key} not finite"
    if not entry.get("calib_converged", False):
        return "a graded reference fit did not converge in the calibration draw"
    if not entry.get("check_converged", False):
        return "a graded reference fit did not converge in the check draw"
    if not entry.get("calib_ref_reproduced", False):
        return f"the reference optimum was reached by fewer than {REF_MIN_STARTS_AT_BEST} starts in the calibration draw"
    if not entry.get("check_ref_reproduced", False):
        return f"the reference optimum was reached by fewer than {REF_MIN_STARTS_AT_BEST} starts in the check draw"
    if entry["gain_check_se"] > GATE_REL_SE * target:
        return f"check SE {entry['gain_check_se']:.5f} exceeds {GATE_REL_SE:.0%} of the target {target}"
    if abs(entry["gain_check"] - target) > GATE_REL_AGREE * target:
        return f"check {entry['gain_check']:.5f} disagrees with the target {target} by more than {GATE_REL_AGREE:.0%}"
    if abs(entry["gain"] - target) > GATE_REL_AGREE * target:
        return f"calibration gain {entry['gain']:.5f} disagrees with the target {target} by more than {GATE_REL_AGREE:.0%}"
    return ""


def revalidate_gain_entries(entries: list, seed: int, cfg: "A.Config", D: int = 4, n_jobs: int = 1) -> list:
    """Recompute every entry's independent check at CHECK_N_PER_FAMILY concepts (fresh seed) without touching
    its scale, then apply the gate — for a gain file produced by code that recorded the check without
    enforcing it (run d4v12b). Returns the updated entries; `note` carries any failure."""
    def one(e):
        e = dict(e)
        if not np.isfinite(e.get("scale", np.nan)):
            return e
        warm = (e.get("calib_theta") or (e["trace"][-1].get("theta") if e.get("trace") else None)) or None
        chk = expected_gain(e["generator"], generator_theta(e["generator"], scale=e["scale"], **e["kwargs"]),
                            seed=seed + 2000, n_per_family=CHECK_N_PER_FAMILY, D=D, cfg=cfg, warm=warm, challenge=True)
        # every check field is replaced together (a stale theta beside a fresh gain is a false record — Codex, review 3)
        for k in [k for k in e if k.startswith("check_")]:
            del e[k]
        e.update(gain_check=chk["gain"], gain_check_se=chk["se"], check_best=chk["best"],
                 check_seed=seed + 2000, check_n_per_family=CHECK_N_PER_FAMILY,
                 check_converged=all(chk["converged"].values()),
                 check_ref_reproduced=bool(chk.get("ref_reproduced", False)), check_starts_at_best=chk.get("starts_at_best"),
                 check_warm_at_best=chk.get("warm_at_best"), check_challenge_improved=chk.get("challenge_improved"),
                 check_runs=chk.get("runs"), check_theta=chk.get("theta"), check_loglik=chk.get("loglik"),
                 calib_converged=e.get("calib_converged", all(e["trace"][-1]["converged"].values()) if e.get("trace") else False),
                 calib_ref_reproduced=bool(e.get("calib_ref_reproduced",
                                                 e["trace"][-1].get("ref_reproduced", False) if e.get("trace") else False)))
        e["note"] = gain_gate(e, float(e["target"]))
        e["revalidated"] = (f"legacy route: the recorded scale kept, ONE declared check recomputed at {CHECK_N_PER_FAMILY} concepts "
                            f"per family, seed {seed + 2000} — not a search over check seeds")
        return e
    if n_jobs > 1:
        from joblib import Parallel, delayed
        return Parallel(n_jobs=n_jobs)(delayed(one)(e) for e in entries)
    return [one(e) for e in entries]


def validate_gain_entries(entries: list, targets=None, names=M.FAMILY_X) -> list:
    """Every declared (member, target) exactly once, every entry passing gain_gate. Returns the problems."""
    targets = GAINS if targets is None else tuple(targets)
    want = {(n, float(t)) for n in names for t in targets}
    have = [(e["generator"], float(e["target"])) for e in entries if float(e["target"]) in {float(t) for t in targets}]
    problems = []
    if sorted(have) != sorted(want):
        problems.append(f"pairs present {sorted(have)} != declared {sorted(want)}")
    for e in entries:
        if float(e["target"]) not in {float(t) for t in targets}:
            continue
        why = e.get("note") or gain_gate(e, float(e["target"]))
        if why:
            problems.append(f"{e['generator']} at {e['target']}: {why}")
    return problems


GAIN_KWARGS = {"M3": {}, "M3H": dict(tau=0.5), "M3V": {}, "M3L": dict(pi0=0.05)}   # the §10 alternatives' base


def _one_gain(name, target, seed, cfg, D):
    """One (member, target) entry: everything calibrate_gain returns (the gate reads calib_converged,
    check_converged, gain_check, gain_check_se) plus the identifying fields."""
    kw = GAIN_KWARGS[name]
    r = calibrate_gain(name, target, kw, seed=seed, cfg=cfg, D=D)
    entry = dict(generator=name, kwargs=kw, target=target, D=D, scale=np.nan, gain=np.nan,
                 gain_check=np.nan, gain_check_se=np.nan, calib_converged=False, check_converged=False, note="", trace=[])
    entry.update(r)
    return entry


def calibrate_all_gains(seed: int, cfg: A.Config, n_jobs: int = 1, names=M.FAMILY_X, D: int = 4, layers=(41,)) -> dict:
    """The twelve §10 gain calibrations (four mixture members x three gains) at the design's D, optionally in
    parallel. Refuses to return a set with a missing or unconverged target: power is claimed 'under every
    mixture alternative' only when all twelve exist. Returns {code_hash, D, entries}."""
    jobs = [(n, t) for n in names for t in GAINS]
    if n_jobs > 1:
        from joblib import Parallel, delayed
        entries = Parallel(n_jobs=n_jobs)(delayed(_one_gain)(n, t, seed, cfg, D) for n, t in jobs)
    else:
        entries = [_one_gain(n, t, seed, cfg, D) for n, t in jobs]
    problems = validate_gain_entries(entries, names=names)
    if problems:
        raise RuntimeError("gain calibration did not pass the §10 gate — " + "; ".join(problems))
    return dict(code_hash=config_hash(cfg, D, layers, seed), D=D, seed=seed, runtime=runtime_versions(),
                gate=dict(check_n_per_family=CHECK_N_PER_FAMILY, rel_se=GATE_REL_SE, rel_agree=GATE_REL_AGREE),
                entries=entries)


def runtime_versions() -> str:
    import platform
    import jax, scipy, pandas, joblib
    return (f"python {platform.python_version()} jax {jax.__version__} numpy {np.__version__} scipy {scipy.__version__} "
            f"pandas {pandas.__version__} joblib {joblib.__version__} {platform.machine()}")


def file_digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def accepted_gain_artefact(raw_path: str | None, revalidated_path: str | None, D: int, want: str | None) -> tuple:
    """ONE contract for the job and the monitor (Codex, review 4 finding 2): which gain artefact is accepted.
    The revalidated file is authoritative when it exists — it must carry this run's code/config hash (`code_hash`,
    or `source_code_hash`), this D, a `revalidated_with` identity and, when the job-written file is beside it, a
    `source_digest` equal to that file's digest; a revalidated file that fails any of these RAISES (the job holds,
    the monitor reports it), and one whose own gate failed is still the accepted artefact, so that `power_points`
    refuses it and the monitor prints the same FAIL. Otherwise the job-written file with this hash and D.
    `want=None` accepts the file's own hash (the monitor, which learns the run's hash from the file).
    Returns (path or None, info)."""
    raw = raw_path if raw_path and os.path.exists(raw_path) else None
    rev = revalidated_path if revalidated_path and os.path.exists(revalidated_path) else None
    info = dict(raw=raw, revalidated=rev, accepted=None, reason="", source_verified=False)
    raw_cal = None
    if raw:
        try:
            with open(raw) as fh:
                raw_cal = json.load(fh)
        except Exception as e:
            raise ValueError(f"gain artefact {os.path.basename(raw)} is malformed: {e}")
    if rev:
        try:
            with open(rev) as fh:
                cal = json.load(fh)
        except Exception as e:
            raise ValueError(f"revalidated artefact {os.path.basename(rev)} is malformed: {e}")
        if not isinstance(cal, dict):
            raise ValueError(f"revalidated artefact {os.path.basename(rev)} is not a record")
        # every identity field is REQUIRED (review 5 finding 2): a revalidation without its provenance is not one
        for key in ("code_hash", "source_code_hash", "source_digest", "revalidated_with", "D", "entries"):
            if key not in cal or cal[key] in (None, ""):
                raise ValueError(f"revalidated artefact lacks the required field {key!r}")
        h = cal["code_hash"]
        if cal["source_code_hash"] != h:
            raise ValueError("revalidated artefact's code_hash and source_code_hash disagree")
        if want is not None and h != want:
            raise ValueError(f"revalidated artefact is for code/config {h!r}, not this run's {want!r}")
        if int(cal.get("D", -1)) != int(D):
            raise ValueError(f"revalidated artefact is for D={cal.get('D')}, not D={D}")
        # the source is REQUIRED in every reader (review 6 finding 2): a revalidation is a check OF a job-written file,
        # and without that file beside it there is nothing it can be verified against — the job and the monitor hold alike
        if not raw:
            raise ValueError("no job-written file to verify the revalidation against: the gain artefact is HELD (both files must be present)")
        if not isinstance(raw_cal, dict) or raw_cal.get("code_hash") != h:
            raise ValueError("revalidated artefact's hash differs from the job-written file beside it")
        if cal["source_digest"] != file_digest(raw):
            raise ValueError("revalidated artefact does not match the job-written file beside it (source digest)")
        return rev, dict(info, accepted="revalidated", code_hash=h, revalidated_with=cal["revalidated_with"],
                         problems=cal.get("problems", []), source_verified=True)
    if raw:
        cal = raw_cal
        if isinstance(cal, dict) and int(cal.get("D", -1)) == int(D) and cal.get("code_hash") and (want is None or cal.get("code_hash") == want):
            return raw, dict(info, accepted="raw", code_hash=cal.get("code_hash"), source_verified=True)
        info["reason"] = (f"job-written artefact is for code/config {cal.get('code_hash') if isinstance(cal, dict) else 'old format'!r}, "
                          f"D {cal.get('D') if isinstance(cal, dict) else '?'}")
    return None, info


def resolve_gain_artefact(fetch, work_dir: str, D: int, want: str | None) -> tuple:
    """The job's side of the contract (review 5 finding 2): retrieve both artefacts through `fetch(name, local) ->
    'ok' | 'absent' | 'error'` and decide. A retrieval ERROR of either file is never a verified absence: it holds
    (raises); only a verified absence of the revalidated file permits the job-written fallback. Files already in
    `work_dir` are used as they are. Returns (accepted path or None, info with the fetch outcomes)."""
    name, rev_name = f"gain_calibration_D{D}.json", f"gain_calibration_D{D}.revalidated.json"
    local, rev_local = os.path.join(work_dir, name), os.path.join(work_dir, rev_name)
    status = {}
    for cand, path in ((rev_name, rev_local), (name, local)):
        if os.path.exists(path):
            status[cand] = "local"
            continue
        status[cand] = fetch(cand, path)
        if status[cand] not in ("ok", "absent"):
            raise ValueError(f"could not retrieve {cand} ({status[cand]}) — not a verified absence: the gain artefact is HELD")
    accepted, info = accepted_gain_artefact(local, rev_local, D, want)
    info["fetch"] = status
    return accepted, info


def changed_files(directory: str, seen: dict) -> list:
    """The files under `directory` whose (mtime, size) differ from the last upload recorded in `seen` (updated in
    place): a job uploads only what it wrote or changed itself, never a foreign download (review 5 finding 4)."""
    out = []
    if not os.path.isdir(directory):
        return out
    for fname in sorted(os.listdir(directory)):
        p = os.path.join(directory, fname)
        if not os.path.isfile(p):
            continue
        st = os.stat(p)
        key = (st.st_mtime_ns, st.st_size)
        if seen.get(fname) != key:
            out.append(p)
            seen[fname] = key
    return out


def power_points(gain_file: str, targets=None) -> tuple:
    """Alternatives for §10 from a calibrated-gain JSON: [(name, kwargs-with-scale)], extras per point.
    Every declared (member, target) must be present and finite; `targets` restricts to a subset."""
    with open(gain_file) as fh:
        cal = json.load(fh)
    entries = cal["entries"] if isinstance(cal, dict) else cal
    problems = validate_gain_entries(entries, targets=targets)
    if problems:
        raise SystemExit(f"gain file {gain_file} does not pass the §10 gate: " + "; ".join(problems))
    pts, extras = [], {}
    for entry in entries:
        if targets is not None and float(entry["target"]) not in {float(t) for t in targets}:
            continue
        kw = dict(entry["kwargs"]); kw["scale"] = entry["scale"]
        pts.append((entry["generator"], kw))
        extras[(entry["generator"], json.dumps(kw, sort_keys=True))] = dict(
            target_gain=entry["target"], gain=entry["gain"], gain_check=entry.get("gain_check"), gain_check_se=entry.get("gain_check_se"))
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
    ap.add_argument("--interval", choices=["cluster", "refit"], default="cluster",
                    help="§8.2 interval: the concept-cluster bootstrap (primary) or the pipeline-refitting bootstrap (its declared replacement)")
    ap.add_argument("--n-boot-refit", type=int, default=A.N_BOOT_REFIT)
    ap.add_argument("--n-gh", type=int, default=M.GH_NODES_DEFAULT)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=None)
    ap.add_argument("--gain-file", default=os.path.join(OUT_DIR, "gain_calibration.json"))
    ap.add_argument("--generators", default=None, help="comma list to restrict the generator set")
    a = ap.parse_args()
    layers = tuple(int(x) for x in a.layers.split(","))
    cfg = A.Config(n_starts_inner=a.n_starts_inner, n_gh=a.n_gh, interval=a.interval, n_boot_refit=a.n_boot_refit)
    os.makedirs(OUT_DIR, exist_ok=True)
    if a.task == "summary":
        for p in A.PREDICTORS:
            print(f"--- predictor: {p}")
            print(summarize(a.out, p).to_string())
        return
    if a.task == "gain":
        names = M.FAMILY_X if a.generators is None else tuple(a.generators.split(","))
        t0 = _time.time()
        out = calibrate_all_gains(a.seed, cfg, n_jobs=min(a.n_jobs, 12), names=names, D=a.D, layers=layers)
        with open(a.gain_file, "w") as fh:
            json.dump(out, fh, indent=1, default=float)
        for e in out["entries"]:
            print(f"{e['generator']} target {e['target']}: scale {e['scale']:.4f} gain {e['gain']:.5f} "
                  f"check {e['gain_check']:.5f} ± {e['gain_check_se']:.5f}", flush=True)
        print(f"gain calibration: {(_time.time() - t0) / 60:.1f} min on {min(a.n_jobs, 12)} workers", flush=True)
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
