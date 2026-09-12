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

import hashlib
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
N_BOOT_REFIT = 200                  # §8.2: the pipeline-refitting bootstrap's replicate count
PREDICTORS = ("selection", "ensemble", "historical")
INTERVALS = ("cluster", "refit")    # §8.2 primary (concept-cluster bootstrap of the fixed scores) / its declared replacement


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
    interval: str = "cluster"           # §8.2: "cluster" (primary) or "refit" (the pipeline-refitting replacement, 12 Sept 2026)
    n_boot_refit: int = N_BOOT_REFIT    # replicates of the refitting bootstrap when interval == "refit"
    refit_min_usable: float = 1.0       # the fraction of refit replicates that must be scored; 1.0 = every one (Codex, 12 Sept)
    refit_checkpoint_dir: str | None = None   # where completed refit resamples are checkpointed (JSON lines, resumable); not a numerical setting
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
    group: np.ndarray | None = None   # (C,) the original concept behind each concept: the copies of one original in
                                      # a §8.2 refitting-bootstrap resample share a group and stay in ONE fold at
                                      # both levels; None = every concept its own group (the plain analysis)

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


def grouped_stratified_folds(family: np.ndarray, group: np.ndarray | None, n_folds: int, seed: int) -> list:
    """stratified_folds with a grouping: every concept sharing a group id (the copies of one original concept in a
    refitting-bootstrap resample, §8.2) lands in the same fold. The folds are drawn over one representative per
    group, stratified by the group's family, and expanded to the copies. With no grouping, or with every group
    distinct, this IS stratified_folds — the same RNG draws, the same folds — so the plain analysis is untouched."""
    family = np.asarray(family)
    if group is None:
        return stratified_folds(family, n_folds, seed)
    group = np.asarray(group)
    if group.size != family.size:
        raise ValueError(f"group has {group.size} entries for {family.size} concepts")
    uniq, first = np.unique(group, return_index=True)
    if uniq.size == group.size:
        return stratified_folds(family, n_folds, seed)
    gi = np.searchsorted(uniq, group)                 # each concept's group, as an index into uniq
    if np.any(family != family[first][gi]):
        raise ValueError("the copies of one group do not share a family")
    rep_folds = stratified_folds(family[first], n_folds, seed)
    fold_of_group = np.full(uniq.size, -1, dtype=np.int64)
    for r, f in enumerate(rep_folds):
        fold_of_group[f] = r
    assign = fold_of_group[gi]
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
                   outer_folds: list, cfg: Config, seed: int, layer_tag: int = 0,
                   group: np.ndarray | None = None) -> dict:
    """§8.1 on one layer's response column. Returns per-concept held-out scores and the three Delta_c.
    `group` (C,) keeps the copies of one original concept in one INNER fold as well (refitting bootstrap, §8.2);
    the outer folds are the caller's."""
    C = family.size
    members = cfg.members
    mi = {m: i for i, m in enumerate(members)}
    logq = np.full((len(members), C), np.nan)
    n_c = np.bincount(concept, minlength=C).astype(float)
    selected = []
    inner_scores = np.full((len(outer_folds), len(members)), np.nan)
    inner_conv = np.zeros((len(outer_folds), len(members)), dtype=float)      # fraction of inner fits converged
    inner_nonfinite = np.zeros((len(outer_folds), len(members)), dtype=bool)   # an inner fit or score was not finite
    converged = np.zeros((len(outer_folds), len(members)), dtype=bool)
    recovery = np.zeros((len(outer_folds), len(members)), dtype=np.int8)
    params = {m: [] for m in members}
    seconds = 0.0
    failed_reason = ""
    for f, test_c in enumerate(outer_folds):
        train_c = np.setdiff1d(np.arange(C), test_c)
        floor_sd = float(np.std(y[np.isin(concept, train_c)], ddof=1))
        train = _subset(y, k, concept, train_c, floor_sd)
        test = _subset(y, k, concept, test_c, floor_sd)
        inner = grouped_stratified_folds(family[train_c], None if group is None else np.asarray(group)[train_c],
                                         cfg.n_inner, seed=int(_rng(seed, layer_tag, f, 1).integers(2**31)))
        for m in members:
            j = mi[m]
            # inner 4-fold selection score (training concepts only). §9: a member whose inner fit or score is
            # not finite after the §7.4 recovery cannot be selected (score -inf) and is recorded; if every
            # member of a family is unscorable the primary comparison is unavailable (failed).
            if m in cfg.members_G or m in cfg.members_X:
                s = 0.0
                conv = 0
                for g, held in enumerate(inner):
                    tr_local = np.setdiff1d(np.arange(train_c.size), held)
                    tr_i = _subset(y, k, concept, train_c[tr_local], floor_sd)
                    te_i = _subset(y, k, concept, train_c[held], floor_sd)
                    r = M.fit(m, tr_i, cfg.n_gh, cfg.n_starts_inner, _rng(seed, layer_tag, f, 2, j, g))
                    seconds += r.seconds
                    conv += int(r.converged)
                    sc = M.concept_scores(m, r.theta, te_i, cfg.n_gh) if np.all(np.isfinite(r.theta)) else np.array([np.nan])
                    if not np.all(np.isfinite(sc)):
                        inner_nonfinite[f, j] = True
                        s = -np.inf
                    elif np.isfinite(s):
                        s += float(np.sum(sc))
                inner_scores[f, j] = s
                inner_conv[f, j] = conv / len(inner)
            # refit on all training concepts, score the held-out concepts
            r = M.fit(m, train, cfg.n_gh, cfg.n_starts, _rng(seed, layer_tag, f, 3, j))
            seconds += r.seconds
            converged[f, j] = r.converged
            recovery[f, j] = r.recovery
            params[m].append(r.theta)
            logq[j, test_c] = (M.concept_scores(m, r.theta, test, cfg.n_gh) if np.all(np.isfinite(r.theta))
                               else np.nan)
        gsel = max(cfg.members_G, key=lambda m: inner_scores[f, mi[m]])
        xsel = max(cfg.members_X, key=lambda m: inner_scores[f, mi[m]])
        if not np.isfinite(inner_scores[f, mi[gsel]]) or not np.isfinite(inner_scores[f, mi[xsel]]):
            failed_reason = f"fold {f}: every member of a family unscorable in inner selection"
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
    if not np.all(np.isfinite(logq[[mi[m] for m in cfg.members_G + cfg.members_X]])):
        failed_reason = failed_reason or "a retained member could not be scored on held-out concepts"
    failed = bool(failed_reason)
    return dict(members=members, logq=logq, n_c=n_c, delta=delta, selected=selected,
                inner_scores=inner_scores, inner_conv=inner_conv, inner_nonfinite=inner_nonfinite,
                converged=converged, recovery=recovery, failed=failed, failed_reason=failed_reason,
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
        return layer_pipeline(ds.y[:, l], ds.k, ds.concept, ds.family, outer_folds, cfg, seed, layer_tag=int(ds.layers[l]),
                              group=ds.group)
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
               inner_conv=np.stack([r["inner_conv"] for r in res]),
               inner_nonfinite=np.stack([r["inner_nonfinite"] for r in res]),
               recovery=np.stack([r["recovery"] for r in res]),
               failed=any(r["failed"] for r in res),
               failed_reason="; ".join(r["failed_reason"] for r in res if r["failed_reason"]),
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
    """§8.3 on a 95 % interval. A non-finite interval is 'unavailable', never 'inconclusive' (Codex, 12 Sept 2026)."""
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "unavailable"
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
    out = dict(failed=run["failed"], failed_reason=run.get("failed_reason", ""), layers=run["layers"].tolist(),
               convergence_rate=float(np.mean(run["converged"])),
               inner_convergence_rate=float(np.mean(run["inner_conv"])),
               inner_nonfinite=int(np.sum(run["inner_nonfinite"])),
               recovery_rate=float(np.mean(run["recovery"] > 0)),
               fit_seconds=run["fit_seconds"], predictors={},
               delta=run["delta"], logq=run["logq"], members=run["members"], selected=run["selected"])
    # §8.2: the interval method is a declared choice of the Config — the concept-cluster bootstrap of the fixed
    # out-of-fold scores (primary), or the pipeline-refitting bootstrap (its replacement when the simulated
    # coverage falls below 0.90). The point estimates are the fixed scores' band means either way; with "refit"
    # the cluster interval is kept beside the refit interval under "cluster", and an unusable refit interval is an
    # assay failure, never an inconclusive reading (Codex, 12 Sept 2026, finding 3).
    if cfg.interval not in INTERVALS:
        raise ValueError(f"cfg.interval must be one of {INTERVALS}, not {cfg.interval!r}")
    rb = None
    if cfg.interval == "refit" and not run["failed"]:
        rb = refit_bootstrap(ds, cfg, seed, n_rep=cfg.n_boot_refit, n_jobs=n_jobs, outer_folds=run["folds"],
                             min_usable=cfg.refit_min_usable, checkpoint_dir=cfg.refit_checkpoint_dir)
        out["interval"] = dict(method="refit", n_rep=rb["n_rep"], n_used=rb["n_used"], n_failed=rb["n_failed"],
                               usable=rb["usable"], policy=rb["policy"], seed=rb["seed"], fit_seconds=rb["fit_seconds"],
                               failed_reasons=rb["failed_reasons"], replicates=rb["replicates"],
                               outer_folds=rb["outer_folds"], checkpoint=rb["checkpoint"], ident=rb["ident"],
                               n_resumed=rb["n_resumed"], n_damaged=rb["n_damaged"])
    elif cfg.interval == "refit":
        out["interval"] = dict(method="refit", n_rep=cfg.n_boot_refit, n_used=0, n_failed=0, usable=False,
                               policy="not run: the analysis itself failed", seed=seed, fit_seconds=0.0, failed_reasons=[], replicates=[])
    else:
        out["interval"] = dict(method="cluster", n_rep=cfg.n_boot, n_used=cfg.n_boot, n_failed=0, usable=True,
                               policy="concept-cluster bootstrap of the fixed out-of-fold scores", seed=seed, fit_seconds=0.0)
    for p in PREDICTORS:
        b = band_bootstrap(run["delta"][p], run["layers"], ds.family, cfg.bands, cfg.n_boot, seed)
        usable = True
        if cfg.interval == "refit":
            b["cluster"] = {k: dict(v) for k, v in b.items() if isinstance(v, dict) and "lo" in v}
            rp = (rb or {}).get("predictors", {}).get(p, {})
            usable = bool(rp.get("usable", False))
            for band, stat in b["cluster"].items():
                v = rp.get("bands", {}).get(band)
                b[band] = dict(point=stat["point"], lo=v["lo"], hi=v["hi"], se=v["se"]) if (usable and v is not None) \
                    else dict(point=stat["point"], lo=float("nan"), hi=float("nan"), se=float("nan"))
            b["usable"] = usable
            b["interval"] = dict(n_used=rp.get("n_used", 0), n_failed=rp.get("n_failed", cfg.n_boot_refit), usable=usable)
        if "ws" in b:
            b["decision"] = "assay failure" if (run["failed"] or not usable) else decide(b["ws"]["lo"], b["ws"]["hi"])
            b["ws_max"] = band_max(run["delta"][p], run["layers"], cfg.bands["ws"])
        out["predictors"][p] = b
    # three flags, kept apart (review 3, finding 3): `failed` = the original fits / points are invalid;
    # `primary_available` = the primary comparison can be read (valid points AND a usable primary interval);
    # each predictor's own `usable` = its interval exists
    out["primary_available"] = bool(not run["failed"] and out["predictors"]["selection"].get("usable", True))
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
def _band_stats(delta: np.ndarray, masks: dict) -> dict:
    """Band means of a (L, C) score array, strict: a band with any non-finite score is NaN (no nanmean — a partial
    score array must never produce a usable number; Codex, 12 Sept 2026). ws_minus_early is added when both exist."""
    out = {}
    for b, m in masks.items():
        block = delta[m]
        out[b] = float(np.mean(block)) if np.all(np.isfinite(block)) else float("nan")
    if "ws" in out and "early" in out:
        out["ws_minus_early"] = out["ws"] - out["early"]
    return out


def dataset_identity(ds: Dataset, cfg: Config, seed: int, n_rep: int, outer_folds: list) -> str:
    """The complete data-and-procedure identity of a refitting bootstrap (Codex, review 4 finding 1): a digest of
    the response array, levels, concept and family mappings, group, exact layer ids, the generator metadata, every
    numerical setting of the Config, the seed, B and the actual outer folds. Two datasets that share a seed (the
    five-layer stage; two recovery points with a colliding tag) never share an identity."""
    h = hashlib.sha256()
    for arr in (ds.y, ds.k, ds.concept, ds.family, ds.layers):
        a = np.ascontiguousarray(np.asarray(arr, dtype=np.float64))
        h.update(repr(a.shape).encode()); h.update(a.tobytes())
    if ds.group is not None:
        h.update(np.ascontiguousarray(np.asarray(ds.group, dtype=np.int64)).tobytes())
    meta = {k: ds.meta.get(k) for k in ("generator", "theta", "D", "rho", "seed")}
    settings = dict(n_starts=cfg.n_starts, n_starts_inner=cfg.n_starts_inner, n_gh=cfg.n_gh, n_outer=cfg.n_outer,
                    n_inner=cfg.n_inner, n_boot=cfg.n_boot, interval=cfg.interval, n_boot_refit=cfg.n_boot_refit,
                    refit_min_usable=cfg.refit_min_usable, members_G=list(cfg.members_G), members_X=list(cfg.members_X),
                    bands=cfg.bands, fit_M0=cfg.fit_M0, seed=int(seed), n_rep=int(n_rep),
                    folds=[[int(c) for c in f] for f in outer_folds])
    h.update(json.dumps(dict(meta=meta, settings=settings), sort_keys=True, default=str).encode())
    return h.hexdigest()


def refit_bootstrap(ds: Dataset, cfg: Config, seed: int, n_rep: int = N_BOOT_REFIT, predictor: str = "selection",
                    n_jobs: int = 1, outer_folds: list | None = None, min_usable: float = 1.0,
                    checkpoint_path: str | None = None, checkpoint_dir: str | None = None) -> dict:
    """Resample whole concepts with replacement within family strata and re-run the ENTIRE per-layer procedure
    (outer folds, inner selection, refit, joint scoring) on every resample; percentile intervals of the band means
    and of ws − early, for EVERY predictor from the same refits (selection, ensemble, historical).
    Every copy of an original concept stays in that concept's outer fold and — through Dataset.group — in one
    inner fold: §8.2's "all copies of a concept in one fold" at both levels (the v1.2 code kept copies together
    only in the outer folds and drew the inner folds over copy ids, so copies of one concept could sit on both
    sides of an inner split; Codex, 12 Sept 2026). Keeping each copy in its ORIGINAL outer fold is the declared
    fixed-fold specification. `outer_folds` are the analysis's own folds (folds.json for CONF); None regenerates
    them as run_dataset does. Failure policy: a resample whose procedure fails (§9), or whose band scores are not
    all finite for a predictor, yields no statistic for it — it is counted, never averaged in — and a predictor's
    interval is usable only when at least `min_usable` of the replicates are scored; the default 1.0 means EVERY
    replicate (Codex, 12 Sept: the missing ones can hold both tails); a lower value is an explicit amendment.
    The per-replicate statistics are returned (`replicates`) so they can be persisted and rescored, and with
    `checkpoint_dir` (a file named by the identity) or `checkpoint_path` every completed resample is appended as one
    JSON line as it finishes (per chunk of n_jobs when parallel). A restart reuses only records that carry THIS
    bootstrap's complete identity (`dataset_identity`: data digest, generator, layers, mappings, Config, seed, B,
    folds), whose resample indices lie in range and whose drawn concepts equal the ones this run would draw; a
    damaged line (truncated JSON, wrong identity, wrong resample) is counted in `n_damaged` and recomputed, never
    accepted (Codex, review 4 finding 1). Top-level band entries are those of `predictor` (compatibility);
    `predictors` holds all three."""
    rng = np.random.default_rng(seed)
    idx = stratified_resample(ds.family, n_rep, rng)
    base_folds = stratified_folds(ds.family, cfg.n_outer, seed) if outer_folds is None else outer_folds
    fold_of = np.full(ds.n_concepts, -1, dtype=np.int64)
    for r, f in enumerate(base_folds):
        fold_of[np.asarray(f)] = r
    if np.any(fold_of < 0):
        raise ValueError("outer_folds do not cover every concept")
    rows_by_concept = [np.where(ds.concept == c)[0] for c in range(ds.n_concepts)]
    masks = {b: m for b, m in band_masks(ds.layers, cfg.bands).items() if m.any()}

    def one(rep):
        chosen = idx[rep]
        rows = np.concatenate([rows_by_concept[c] for c in chosen])
        new_concept = np.concatenate([np.full(rows_by_concept[c].size, j) for j, c in enumerate(chosen)])
        family = ds.family[chosen]
        folds = [f for f in (np.where(fold_of[chosen] == r)[0] for r in range(len(base_folds))) if f.size]
        sub = Dataset(ds.y[rows], ds.k[rows], new_concept, family, ds.layers, group=chosen)
        run = run_dataset(sub, cfg, seed + 1 + rep, outer_folds=folds)
        stats = {p: _band_stats(np.asarray(run["delta"][p], dtype=float), masks) for p in PREDICTORS}
        return dict(rep=int(rep), stats=stats, failed=bool(run["failed"]), failed_reason=run.get("failed_reason", ""),
                    fit_seconds=float(run.get("fit_seconds", 0.0)), chosen=[int(c) for c in chosen])
    ident = dataset_identity(ds, cfg, seed, n_rep, base_folds)
    if checkpoint_path is None and checkpoint_dir:
        checkpoint_path = os.path.join(checkpoint_dir, f"refit_{ident[:24]}.jsonl")
    done, n_damaged = {}, 0
    if checkpoint_path and os.path.exists(checkpoint_path):
        with open(checkpoint_path) as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    ok = (isinstance(d, dict) and d.get("ident") == ident and d.get("seed") == int(seed)
                          and d.get("n_rep") == int(n_rep) and isinstance(d.get("rep"), int) and 0 <= d["rep"] < n_rep
                          and d.get("chosen") == [int(c) for c in idx[d["rep"]]] and isinstance(d.get("failed"), bool)
                          and isinstance(d.get("stats"), dict) and all(p in d["stats"] for p in PREDICTORS))
                except Exception:
                    ok = False
                if ok:
                    done[int(d["rep"])] = d
                else:
                    n_damaged += 1
    todo = [r for r in range(n_rep) if r not in done]
    def _save(batch):
        if checkpoint_path:
            os.makedirs(os.path.dirname(checkpoint_path) or ".", exist_ok=True)
            with open(checkpoint_path, "a") as fh:
                for s in batch:
                    fh.write(json.dumps(dict(s, ident=ident, seed=int(seed), n_rep=int(n_rep)), default=float) + "\n")
    new = []
    if n_jobs > 1:
        from joblib import Parallel, delayed
        for i in range(0, len(todo), n_jobs):
            batch = Parallel(n_jobs=n_jobs)(delayed(one)(r) for r in todo[i:i + n_jobs])
            _save(batch); new += batch
    else:
        for r in todo:
            s = one(r)
            _save([s]); new.append(s)
    reps = sorted(list(done.values()) + new, key=lambda s: s["rep"])
    out = dict(method="refit", n_rep=int(n_rep), seed=int(seed), min_usable=float(min_usable),
               policy=("every replicate scored" if min_usable >= 1.0 else f"at least {min_usable:.0%} of the replicates scored"),
               outer_folds=[[int(c) for c in f] for f in base_folds], checkpoint=checkpoint_path, n_resumed=len(done),
               n_damaged=int(n_damaged), ident=ident,
               failed_reasons=[s["failed_reason"] for s in reps if s["failed"]],
               fit_seconds=float(sum(s["fit_seconds"] for s in reps)), predictors={},
               replicates=[dict(rep=s["rep"], failed=s["failed"], failed_reason=s["failed_reason"], stats=s["stats"]) for s in reps])
    bands = list(masks) + (["ws_minus_early"] if "ws" in masks and "early" in masks else [])
    for p in PREDICTORS:
        ok = [s for s in reps if not s["failed"] and all(np.isfinite(s["stats"][p][b]) for b in bands)]
        usable = bool(ok) and len(ok) >= min_usable * n_rep
        pr = dict(n_used=len(ok), n_failed=int(n_rep - len(ok)), usable=usable, bands={})
        for b in bands:
            if usable:
                v = np.array([s["stats"][p][b] for s in ok])
                pr["bands"][b] = dict(lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)), se=float(np.std(v, ddof=1)))
            else:
                pr["bands"][b] = dict(lo=float("nan"), hi=float("nan"), se=float("nan"))
        out["predictors"][p] = pr
    prim = out["predictors"][predictor]
    out.update(n_used=prim["n_used"], n_failed=prim["n_failed"], usable=prim["usable"])
    for b in bands:
        out[b] = dict(prim["bands"][b])
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
