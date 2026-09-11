#!/usr/bin/env python3
"""t1_access/analyze.py — the primary analysis of PREREGISTRATION_T1_model.md §8 (and the §8.2 fallback).

Inputs: a Dataset — one response column per layer (R1 z-scores, or R2 for §8.5(a)), the level k, the
concept index and the concept's family. Every step is per layer:

  §8.1  Five concept-disjoint outer folds stratified by family (`stratified_folds`, `folds.json`).
        For each outer fold: every member of G and X is fitted on the training concepts and scores
        the held-out concepts by the joint concept likelihood q_{m,c} (models.concept_scores).
        Training-only selection: the member of each family with the best inner 4-fold concept-disjoint
        stratified joint log score on the training concepts is the family's predictor for that fold.
        Delta_c = (log q_{X*,c} - log q_{G*,c}) / n_c.
        Sensitivity predictors, reported alongside: the equal-weight ensemble of joint likelihoods
        (a mixture over members of the concept-level likelihood) and the historical pair M3 vs M2B.
  §8.2  Concept-cluster bootstrap of the fixed out-of-fold Delta_c: whole concepts resampled with
        replacement within each family stratum, 2,000 replicates, every layer of a concept carried
        together (`band_bootstrap`). The pipeline-refitting fallback is `refit_bootstrap`.
  §8.3  Band means over the layer grid (ws 23–57 primary, early 3–15, late 58–62); mixture support if
        the 95 % CI of the ws band mean excludes 0 and is positive, graded support if negative,
        inconclusive otherwise. H2 = ws - early.
  §8.4  SPM curves (spm_BMS on the held-out joint log scores, all members and the inherited three).
  §9    A retained member that cannot be scored after the §7.4 recovery marks the primary comparison
        unavailable (`failed`); flagged (non-converged) fits are counted, not failures.

`analyze_dataset` returns the outcome table for one dataset. simulate.py drives it on synthetic data;
the CONF run will drive it on the captured readouts with the frozen folds.json.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field

import numpy as np

import models as M

HERE = os.path.dirname(os.path.abspath(__file__))
BANDS = {"ws": (23, 57), "early": (3, 15), "late": (58, 62)}
N_FAMILIES = 8
N_OUTER = 5
N_INNER = 4
N_BOOT = 2000
PREDICTORS = ("selection", "ensemble", "historical")


@dataclass
class Config:
    members_G: tuple = M.FAMILY_G
    members_X: tuple = M.FAMILY_X
    n_starts: int = M.N_STARTS          # refits and CAL/PILOT fits
    n_starts_inner: int = M.N_STARTS    # inner-selection fits (§14 allows 4 if the benchmark requires)
    n_gh: int = M.GH_NODES_DEFAULT
    n_outer: int = N_OUTER
    n_inner: int = N_INNER
    n_boot: int = N_BOOT
    fit_M0: bool = False                # M0 held-out scores for the SPM curves (§8.4)
    bands: dict = field(default_factory=lambda: dict(BANDS))

    @property
    def members(self) -> tuple:
        return (("M0",) if self.fit_M0 else ()) + tuple(self.members_G) + tuple(self.members_X)


@dataclass
class Dataset:
    y: np.ndarray          # (n, n_layers)
    k: np.ndarray          # (n,)
    concept: np.ndarray    # (n,) 0..C-1
    family: np.ndarray     # (C,) 0..N_FAMILIES-1
    layers: np.ndarray     # (n_layers,) layer ids
    meta: dict = field(default_factory=dict)

    @property
    def n_concepts(self) -> int:
        return int(self.family.size)

    @property
    def n_layers(self) -> int:
        return int(self.y.shape[1])


# ----------------------------------------------------------------------------------------------
# folds
# ----------------------------------------------------------------------------------------------
def stratified_folds(family: np.ndarray, n_folds: int, seed: int) -> list:
    """Concept-disjoint folds stratified by family: per family a seeded shuffle, then round-robin with a
    per-family offset so that the fold sizes balance. Returns a list of arrays of held-out concepts."""
    rng = np.random.default_rng(seed)
    family = np.asarray(family)
    fams = np.unique(family)
    assign = np.empty(family.size, dtype=np.int64)
    for j, f in enumerate(fams):
        idx = np.where(family == f)[0]
        rng.shuffle(idx)
        for i, c in enumerate(idx):
            assign[c] = (i + j) % n_folds
    return [np.where(assign == r)[0] for r in range(n_folds)]


def save_folds(folds: list, path: str, family: np.ndarray, seed: int):
    with open(path, "w") as fh:
        json.dump(dict(seed=seed, n_folds=len(folds), family=[int(x) for x in family],
                       folds=[[int(c) for c in f] for f in folds]), fh, indent=1)


def load_folds(path: str) -> list:
    with open(path) as fh:
        d = json.load(fh)
    return [np.asarray(f, dtype=np.int64) for f in d["folds"]]


# ----------------------------------------------------------------------------------------------
# one layer
# ----------------------------------------------------------------------------------------------
def _subset(y, k, concept, concepts, floor_sd=None) -> M.Trials:
    """Trials of the listed concepts, reindexed to 0..len(concepts)-1 in that order."""
    concepts = np.asarray(concepts)
    remap = np.full(int(concept.max()) + 1, -1, dtype=np.int64)
    remap[concepts] = np.arange(concepts.size)
    m = remap[concept] >= 0
    return M.Trials.build(y[m], k[m], remap[concept[m]], concepts.size, floor_sd)


def _rng(seed, *tags):
    return np.random.default_rng([int(seed)] + [int(t) for t in tags])


def layer_pipeline(y: np.ndarray, k: np.ndarray, concept: np.ndarray, family: np.ndarray,
                   outer_folds: list, cfg: Config, seed: int, layer_tag: int = 0) -> dict:
    """§8.1 on one layer's response column. Returns per-concept held-out scores and the three Delta_c."""
    C = family.size
    members = cfg.members
    mi = {m: i for i, m in enumerate(members)}
    logq = np.full((len(members), C), np.nan)
    n_c = np.bincount(concept, minlength=C).astype(float)
    selected = []
    inner_scores = np.full((len(outer_folds), len(members)), np.nan)
    converged = np.zeros((len(outer_folds), len(members)), dtype=bool)
    recovery = np.zeros((len(outer_folds), len(members)), dtype=np.int8)
    params = {m: [] for m in members}
    seconds = 0.0
    for f, test_c in enumerate(outer_folds):
        train_c = np.setdiff1d(np.arange(C), test_c)
        floor_sd = float(np.std(y[np.isin(concept, train_c)], ddof=1))
        train = _subset(y, k, concept, train_c, floor_sd)
        test = _subset(y, k, concept, test_c, floor_sd)
        inner = stratified_folds(family[train_c], cfg.n_inner, seed=int(_rng(seed, layer_tag, f, 1).integers(2**31)))
        for m in members:
            j = mi[m]
            # inner 4-fold selection score (training concepts only)
            if m in cfg.members_G or m in cfg.members_X:
                s = 0.0
                for g, held in enumerate(inner):
                    tr_local = np.setdiff1d(np.arange(train_c.size), held)
                    tr_i = _subset(y, k, concept, train_c[tr_local], floor_sd)
                    te_i = _subset(y, k, concept, train_c[held], floor_sd)
                    r = M.fit(m, tr_i, cfg.n_gh, cfg.n_starts_inner, _rng(seed, layer_tag, f, 2, j, g))
                    seconds += r.seconds
                    s += float(np.sum(M.concept_scores(m, r.theta, te_i, cfg.n_gh)))
                inner_scores[f, j] = s
            # refit on all training concepts, score the held-out concepts
            r = M.fit(m, train, cfg.n_gh, cfg.n_starts, _rng(seed, layer_tag, f, 3, j))
            seconds += r.seconds
            converged[f, j] = r.converged
            recovery[f, j] = r.recovery
            params[m].append(r.theta)
            logq[j, test_c] = M.concept_scores(m, r.theta, test, cfg.n_gh)
        gsel = max(cfg.members_G, key=lambda m: inner_scores[f, mi[m]])
        xsel = max(cfg.members_X, key=lambda m: inner_scores[f, mi[m]])
        selected.append((gsel, xsel))
    # the three predictors (§8.1)
    delta = {}
    sel_X = np.empty(C); sel_G = np.empty(C)
    for f, test_c in enumerate(outer_folds):
        gsel, xsel = selected[f]
        sel_X[test_c] = logq[mi[xsel], test_c]
        sel_G[test_c] = logq[mi[gsel], test_c]
    delta["selection"] = (sel_X - sel_G) / n_c
    iG = [mi[m] for m in cfg.members_G]; iX = [mi[m] for m in cfg.members_X]
    ens_G = _logmeanexp(logq[iG], axis=0); ens_X = _logmeanexp(logq[iX], axis=0)
    delta["ensemble"] = (ens_X - ens_G) / n_c
    if "M3" in mi and "M2B" in mi:
        delta["historical"] = (logq[mi["M3"]] - logq[mi["M2B"]]) / n_c
    else:
        delta["historical"] = np.full(C, np.nan)
    failed = not np.all(np.isfinite(logq[[mi[m] for m in cfg.members_G + cfg.members_X]]))
    return dict(members=members, logq=logq, n_c=n_c, delta=delta, selected=selected,
                inner_scores=inner_scores, converged=converged, recovery=recovery, failed=failed,
                params={m: np.array(v) for m, v in params.items()}, fit_seconds=seconds)


def _logmeanexp(a, axis=0):
    a = np.asarray(a, dtype=float)
    mx = np.max(a, axis=axis, keepdims=True)
    return (mx + np.log(np.mean(np.exp(a - mx), axis=axis, keepdims=True))).squeeze(axis)


# ----------------------------------------------------------------------------------------------
# all layers of a dataset
# ----------------------------------------------------------------------------------------------
def run_dataset(ds: Dataset, cfg: Config, seed: int, outer_folds: list | None = None, n_jobs: int = 1) -> dict:
    outer_folds = stratified_folds(ds.family, cfg.n_outer, seed) if outer_folds is None else outer_folds
    def one(l):
        return layer_pipeline(ds.y[:, l], ds.k, ds.concept, ds.family, outer_folds, cfg, seed, layer_tag=int(ds.layers[l]))
    if n_jobs > 1 and ds.n_layers > 1:
        from joblib import Parallel, delayed
        res = Parallel(n_jobs=n_jobs)(delayed(one)(l) for l in range(ds.n_layers))
    else:
        res = [one(l) for l in range(ds.n_layers)]
    C, L = ds.n_concepts, ds.n_layers
    out = dict(layers=ds.layers, folds=outer_folds, members=res[0]["members"],
               delta={p: np.stack([r["delta"][p] for r in res]) for p in PREDICTORS},     # (L, C)
               logq=np.stack([r["logq"] for r in res]),                                     # (L, M, C)
               n_c=res[0]["n_c"],
               selected=[r["selected"] for r in res],
               converged=np.stack([r["converged"] for r in res]),
               recovery=np.stack([r["recovery"] for r in res]),
               failed=any(r["failed"] for r in res),
               params={m: np.stack([r["params"][m] for r in res]) for m in res[0]["params"]},
               fit_seconds=sum(r["fit_seconds"] for r in res))
    return out


# ----------------------------------------------------------------------------------------------
# §8.2 bootstrap, §8.3 bands and rule
# ----------------------------------------------------------------------------------------------
def band_masks(layers: np.ndarray, bands: dict) -> dict:
    layers = np.asarray(layers)
    return {b: (layers >= lo) & (layers <= hi) for b, (lo, hi) in bands.items()}


def stratified_resample(family: np.ndarray, n_rep: int, rng: np.random.Generator) -> np.ndarray:
    """(n_rep, C) concept indices: whole concepts with replacement within each family stratum."""
    cols = []
    for f in np.unique(family):
        idx = np.where(family == f)[0]
        cols.append(idx[rng.integers(0, idx.size, size=(n_rep, idx.size))])
    return np.concatenate(cols, axis=1)


def band_bootstrap(delta: np.ndarray, layers: np.ndarray, family: np.ndarray, bands: dict = BANDS,
                   n_rep: int = N_BOOT, seed: int = 0) -> dict:
    """Point estimates and percentile 95 % CIs of the band means (and ws - early) of Delta (L, C)."""
    masks = band_masks(layers, bands)
    per_concept = {b: np.nanmean(delta[m], axis=0) for b, m in masks.items() if m.any()}   # (C,) each
    if "ws" in per_concept and "early" in per_concept:
        per_concept["ws_minus_early"] = per_concept["ws"] - per_concept["early"]
    rng = np.random.default_rng(seed)
    idx = stratified_resample(family, n_rep, rng)
    out = {}
    for b, v in per_concept.items():
        boot = v[idx].mean(axis=1)
        out[b] = dict(point=float(np.mean(v)), lo=float(np.percentile(boot, 2.5)),
                      hi=float(np.percentile(boot, 97.5)), se=float(np.std(boot, ddof=1)))
    # per-family band means (ws), no CI beyond the pooled one is required for the count
    if "ws" in per_concept:
        fam_means = np.array([np.mean(per_concept["ws"][family == f]) for f in np.unique(family)])
        pooled_sign = np.sign(out["ws"]["point"])
        out["ws_family_means"] = fam_means.tolist()
        out["ws_families_with_pooled_sign"] = int(np.sum(np.sign(fam_means) == pooled_sign))
    return out


def decide(lo: float, hi: float) -> str:
    if lo > 0:
        return "mixture"
    if hi < 0:
        return "graded"
    return "inconclusive"


def band_max(delta: np.ndarray, layers: np.ndarray, band=(23, 57)) -> tuple:
    m = (layers >= band[0]) & (layers <= band[1])
    if not m.any():
        return (float("nan"), None)
    means = np.nanmean(delta, axis=1)
    means = np.where(m, means, -np.inf)
    j = int(np.argmax(means))
    return float(means[j]), int(layers[j])


def analyze_dataset(ds: Dataset, cfg: Config, seed: int, outer_folds: list | None = None,
                    n_jobs: int = 1, run: dict | None = None) -> dict:
    """The outcome table for one dataset: per predictor, the band statistics, CIs and the §8.3 decision."""
    run = run_dataset(ds, cfg, seed, outer_folds, n_jobs) if run is None else run
    out = dict(failed=run["failed"], layers=run["layers"].tolist(),
               convergence_rate=float(np.mean(run["converged"])),
               recovery_rate=float(np.mean(run["recovery"] > 0)),
               fit_seconds=run["fit_seconds"], predictors={})
    for p in PREDICTORS:
        b = band_bootstrap(run["delta"][p], run["layers"], ds.family, cfg.bands, cfg.n_boot, seed)
        if "ws" in b:
            b["decision"] = "assay failure" if run["failed"] else decide(b["ws"]["lo"], b["ws"]["hi"])
            b["ws_max"] = band_max(run["delta"][p], run["layers"], cfg.bands["ws"])
        out["predictors"][p] = b
    # selected-member counts over layers x folds
    sel = {}
    for layer_sel in run["selected"]:
        for g, x in layer_sel:
            sel[g] = sel.get(g, 0) + 1
            sel[x] = sel.get(x, 0) + 1
    out["selected_counts"] = sel
    out["heldout_logscore_per_trial"] = {m: float(np.nanmean(np.nansum(run["logq"][:, i, :], axis=1) / np.sum(run["n_c"])))
                                        for i, m in enumerate(run["members"])}
    return out


# ----------------------------------------------------------------------------------------------
# §8.2 fallback: pipeline-refitting bootstrap (all copies of a concept in one fold)
# ----------------------------------------------------------------------------------------------
def refit_bootstrap(ds: Dataset, cfg: Config, seed: int, n_rep: int = 200, predictor: str = "selection",
                    n_jobs: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    idx = stratified_resample(ds.family, n_rep, rng)
    base_folds = stratified_folds(ds.family, cfg.n_outer, seed)
    fold_of = np.empty(ds.n_concepts, dtype=np.int64)
    for r, f in enumerate(base_folds):
        fold_of[f] = r
    rows_by_concept = [np.where(ds.concept == c)[0] for c in range(ds.n_concepts)]
    def one(rep):
        chosen = idx[rep]
        rows = np.concatenate([rows_by_concept[c] for c in chosen])
        new_concept = np.concatenate([np.full(rows_by_concept[c].size, j) for j, c in enumerate(chosen)])
        family = ds.family[chosen]
        folds = [np.where(fold_of[chosen] == r)[0] for r in range(cfg.n_outer)]
        sub = Dataset(ds.y[rows], ds.k[rows], new_concept, family, ds.layers)
        run = run_dataset(sub, cfg, seed + 1 + rep, outer_folds=folds)
        masks = band_masks(ds.layers, cfg.bands)
        return {b: float(np.nanmean(run["delta"][predictor][m])) for b, m in masks.items() if m.any()}
    if n_jobs > 1:
        from joblib import Parallel, delayed
        stats = Parallel(n_jobs=n_jobs)(delayed(one)(r) for r in range(n_rep))
    else:
        stats = [one(r) for r in range(n_rep)]
    out = {}
    for b in stats[0]:
        v = np.array([s[b] for s in stats])
        out[b] = dict(lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)), se=float(np.std(v, ddof=1)))
    return out


# ----------------------------------------------------------------------------------------------
# §8.4 SPM curves — the inherited assay, on the held-out joint log scores
# ----------------------------------------------------------------------------------------------
def spm_curves(run: dict, members: tuple | None = None) -> np.ndarray:
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "sergent_port")))
    from bms import spm_bms
    names = run["members"] if members is None else members
    mi = {m: i for i, m in enumerate(run["members"])}
    cols = [mi[m] for m in names]
    pxp = []
    for l in range(run["logq"].shape[0]):
        lme = run["logq"][l][cols].T                      # (C, |names|)
        pxp.append(spm_bms(lme, nsamp=200_000)["pxp"])
    return np.array(pxp)                                   # (L, |names|)


if __name__ == "__main__":
    # smoke: a small synthetic dataset through the whole §8 pipeline at one layer
    import simulate as S
    ds = S.make_dataset("M3H", S.generator_theta("M3H", tau=0.5, sep=2.0), n_per_family=8, D=4,
                        layers=np.array([40]), rho=0.9, seed=1)
    cfg = Config()
    res = analyze_dataset(ds, cfg, seed=1)
    for p in PREDICTORS:
        b = res["predictors"][p]
        print(p, b["decision"], "ws %.4f [%.4f, %.4f]" % (b["ws"]["point"], b["ws"]["lo"], b["ws"]["hi"]))
    print("selected:", res["selected_counts"], "convergence", res["convergence_rate"], "fit s", round(res["fit_seconds"], 1))
