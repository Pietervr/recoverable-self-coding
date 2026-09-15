"""A5: H3, causal use — layer selection, states, matching, edit lists, amplitudes and outcomes (PREREGISTRATION_T1_model.md §11).

Runs in the analysis environment (workspace_demo/t1_access/.venv: jax, numpy, scipy, joblib). models.py and
analyze.py (Entropy SI's) are imported as libraries and never edited here. Captures go through capture.Server.

  select_layers    §8 pipeline on CAL R1 z-scores, 4 concept-disjoint family-stratified folds (4 concepts each),
                   band layers 23-57; the three band layers with the largest CAL band-mean Delta (selection
                   predictor) are the intervention layers, the largest the reference layer. A CAL choice, not
                   cross-fitting.
  assign_states    per trial at the reference layer: P(high) under the training-selected mixture member, fitted on
                   the other folds (hierarchical random effect at its posterior mode; M3V floor from the training
                   fold); high if > 0.9, low if < 0.1; levels 2, 3, 4 only.
  match            up to 200 high and 200 low trials matched on level, carrier and family (seeded); all eligible
                   pairs if fewer; the number is reported.
  offtarget_pairs  pre-assigned unrelated BACKGROUND pairs (u1 -> u2) per (target family, foil family), from two
                   families other than both (seeded).
  edit_lists       per trial: baseline (empty list); joint at the three layers: swap (swap_delta target -> foil,
                   lambda 1), ablate (target, lambda 1), rescue (steer v_t written at the CAL amplitude A_l), sham
                   (swap_delta lambda 0), off-target (swap_delta u1 -> u2 norm-matched per layer and position to the
                   trial's own swap), positive control (patch the matched k = 8 packet's marker rows); single-layer
                   swap, ablate and rescue at each layer. 1 + 6 + 9 = 16 captures per trial (§14).
  amplitudes       A_l = median written ||Delta h_l|| of the joint swap on CAL high-state trials (levels 2-4).
  outcomes         effect = (l_t - l_f) before - after (rescue: after - before); the joint-swap state interaction
                   E_high - E_low with a concept-cluster 95 % CI, supported if the CI excludes 0 and the estimate
                   >= 0.5 nat, strong if the lower bound >= 0.5; sham and off-target equivalence (|effect| < 0.25,
                   90 % CI inside); positive control on low-state trials (increase, CI excluding 0, else "not
                   testable"); closed-set argmax flips; dose regression; binary vs smooth held-out log score.

Interpretations recorded for Entropy SI (not in §11's text): CAL amplitudes use high-state trials at levels 2-4,
like the CONF analysis; the patch rows come from the k = 8 packet of the same (concept, carrier, draw) at all three
marker positions; flips use the §6.3 closed-set correctness.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

BAND = (23, 57)
H3_LEVELS = (2, 3, 4)
N_MATCH = 200
HIGH, LOW = 0.9, 0.1
SEOI = 0.5
EQUIV = 0.25
N_BOOT = 2000
SEED = 20260915


def _seed(*parts) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in (SEED, *parts)).encode()).hexdigest()[:16], 16)


# -- 1. layer selection on CAL ---------------------------------------------------------------

def cal_dataset(z: np.ndarray, layers: list[int], k: np.ndarray, concepts: np.ndarray):
    """analyze.Dataset over the band layers from CAL R1 z-scores [n, len(layers)]; concept order sorted."""
    import analyze as A

    names = sorted(set(concepts.tolist()))
    cidx = np.array([names.index(c) for c in concepts])
    fams = sorted({c.split("/")[0] for c in names})
    family = np.array([fams.index(c.split("/")[0]) for c in names])
    band = [i for i, l in enumerate(layers) if BAND[0] <= l <= BAND[1]]
    ds = A.Dataset(y=z[:, band], k=np.asarray(k, float), concept=cidx, family=family,
                   layers=np.array([layers[i] for i in band]), meta={"concepts": names})
    return ds


def select_layers(ds, seed: int = SEED, n_jobs: int = 1, cfg=None) -> dict:
    import analyze as A

    cfg = A.Config(n_outer=4, n_inner=4, n_starts_inner=4) if cfg is None else cfg
    folds = A.stratified_folds(ds.family, 4, seed)
    run = A.run_dataset(ds, cfg, seed, outer_folds=folds, n_jobs=n_jobs)
    band_mean = run["delta"]["selection"].mean(axis=1)                # (L,)
    order = np.argsort(-band_mean, kind="stable")
    chosen = sorted(int(ds.layers[i]) for i in order[:3])
    return {"band_mean_delta": dict(zip(ds.layers.tolist(), band_mean.tolist())),
            "intervention_layers": chosen, "reference_layer": int(ds.layers[order[0]]),
            "folds": [f.tolist() for f in folds], "failed": run["failed"], "run": run}


# -- 2. states ---------------------------------------------------------------------------------

def assign_states(run: dict, ds, layer: int) -> np.ndarray:
    """P(high) per trial at `layer` from the fold-held-out training-selected mixture member (§11, §8.5(b))."""
    import models as M
    from analyze import _subset

    li = list(ds.layers).index(layer)
    y, k, concept = ds.y[:, li], ds.k, ds.concept
    p = np.full(y.size, np.nan)
    for f, test_c in enumerate(run["folds"]):
        test_c = np.asarray(test_c)
        train_c = np.setdiff1d(np.arange(ds.n_concepts), test_c)
        floor_sd = float(np.std(y[np.isin(concept, train_c)], ddof=1))
        xsel = run["selected"][li][f][1]
        theta = run["params"][xsel][li][f]
        test = _subset(y, k, concept, test_c, floor_sd)
        u_c = M.posterior_u(xsel, theta, test) if M.MEMBERS[xsel].hierarchical else np.zeros(test_c.size)
        for j, c in enumerate(test_c):
            m = concept == c
            p[m] = M.state_posterior(xsel, theta, y[m], k[m], u=float(u_c[j]),
                                     floor=M.M3V_FLOOR_FRACTION * floor_sd)
    return p


def state_labels(p: np.ndarray, k: np.ndarray) -> np.ndarray:
    lab = np.full(p.size, "", dtype=object)
    eligible = np.isin(k, H3_LEVELS)
    lab[eligible & (p > HIGH)] = "high"
    lab[eligible & (p < LOW)] = "low"
    return lab


# -- 3. matching ---------------------------------------------------------------------------------

def match(labels: np.ndarray, k: np.ndarray, carrier: np.ndarray, family: np.ndarray, seed: int = SEED,
          n_max: int = N_MATCH) -> dict:
    """High/low pairs within (level, carrier, family) cells; at most n_max pairs, seeded."""
    rng = random.Random(_seed("match", seed))
    pairs = []
    cells = sorted({(int(a), int(b), str(c)) for a, b, c in zip(k, carrier, family)})
    for cell in cells:
        in_cell = (k == cell[0]) & (carrier == cell[1]) & (family == cell[2])
        hi = sorted(np.flatnonzero(in_cell & (labels == "high")).tolist())
        lo = sorted(np.flatnonzero(in_cell & (labels == "low")).tolist())
        rng.shuffle(hi)
        rng.shuffle(lo)
        pairs += [(h, l, cell) for h, l in zip(hi, lo)]
    eligible = len(pairs)
    if eligible > n_max:
        pairs = sorted(rng.sample(pairs, n_max), key=lambda t: (t[2], t[0]))
    return {"high": [p[0] for p in pairs], "low": [p[1] for p in pairs], "cells": [p[2] for p in pairs],
            "n_pairs": len(pairs), "n_eligible_pairs": eligible,
            "n_high_eligible": int(np.sum(labels == "high")), "n_low_eligible": int(np.sum(labels == "low"))}


# -- 4. off-target pairs -------------------------------------------------------------------------

def offtarget_pairs(bank: dict) -> dict:
    """{"<target family>|<foil family>": [u1 concept, u2 concept]} from two other families' BACKGROUND concepts."""
    families = bank["families"]
    bg = {f: sorted(c["id"] for c in bank["concepts"] if c["role"] == "BACKGROUND" and c["family"] == f)
          for f in families}
    out = {}
    for ft in families:
        for ff in families:
            if ft == ff:
                continue
            rng = random.Random(_seed("offtarget", ft, ff))
            f1, f2 = rng.sample(sorted(set(families) - {ft, ff}), 2)
            out[f"{ft}|{ff}"] = [rng.choice(bg[f1]), rng.choice(bg[f2])]
    return out


# -- 5. edit lists ---------------------------------------------------------------------------------

def edit_lists(layers: list[int], marker_positions: list[int], target_id: int, foil_id: int,
               amplitudes: dict | None = None, off_ids: tuple[int, int] | None = None,
               swap_written: dict | None = None, patch_rows: dict | None = None) -> dict:
    """Named edit lists for POST /api/capture. swap_written: {layer: per-position written norms of the trial's own
    joint swap} (needed for off-target); patch_rows: {layer: base64 bfloat16 rows [positions, D]} (positive control)."""
    pos = list(marker_positions)

    def swap(l, a=1.0):
        return {"mode": "swap_delta", "layer": l, "positions": pos, "alpha": a, "token_id": target_id, "target_id": foil_id}

    def ablate(l):
        return {"mode": "ablate", "layer": l, "positions": pos, "alpha": 1.0, "ablate_token_ids": [target_id]}

    def rescue(l):
        return {"mode": "steer", "layer": l, "positions": pos, "token_id": target_id,
                "target_norms": [float(amplitudes[l])] * len(pos)}

    out = {"baseline": [], "swap": [swap(l) for l in layers], "ablate": [ablate(l) for l in layers],
           "sham": [swap(l, 0.0) for l in layers]}
    if amplitudes is not None:
        out["rescue"] = [rescue(l) for l in layers]
    if off_ids is not None and swap_written is not None:
        out["offtarget"] = [{"mode": "swap_delta", "layer": l, "positions": pos, "token_id": off_ids[0],
                             "target_id": off_ids[1], "target_norms": [float(x) for x in swap_written[l]]}
                            for l in layers]
    if patch_rows is not None:
        out["positive"] = [{"mode": "patch", "layer": l, "positions": pos, "vectors_b64": patch_rows[l],
                            "vectors_dtype": "bfloat16"} for l in layers]
    for l in layers:
        out[f"swap@{l}"] = [swap(l)]
        out[f"ablate@{l}"] = [ablate(l)]
        if amplitudes is not None:
            out[f"rescue@{l}"] = [rescue(l)]
    return out


# -- 6. amplitudes -------------------------------------------------------------------------------

def amplitudes(swap_edit_logs: list[list[dict]], layers: list[int]) -> dict:
    """A_l: median written ||Delta h_l|| over CAL high-state trials and marker positions of the joint swap."""
    out = {}
    for l in layers:
        vals = [x for log in swap_edit_logs for e in log if e["layer"] == l for x in e["written_delta_norm"]]
        out[l] = float(np.median(vals))
    return out


# -- 7. outcomes ---------------------------------------------------------------------------------

def contrast(logit_t: np.ndarray, logit_f: np.ndarray) -> np.ndarray:
    return np.asarray(logit_t, float) - np.asarray(logit_f, float)


def effect(base: np.ndarray, after: np.ndarray, rescue: bool = False) -> np.ndarray:
    """Reduction of the target-foil contrast (positive = reduction); rescue: the increase."""
    return (after - base) if rescue else (base - after)


def _cluster_boot(stat, concepts: np.ndarray, family_of: dict, n_boot: int, seed: int) -> np.ndarray:
    """Concept-cluster bootstrap within family strata: `stat(weights)` gets per-trial multiplicities."""
    rng = np.random.default_rng(_seed("boot", seed))
    names = sorted(set(concepts.tolist()))
    by_fam: dict[str, list[str]] = {}
    for c in names:
        by_fam.setdefault(family_of[c], []).append(c)
    idx = {c: np.flatnonzero(concepts == c) for c in names}
    out = np.empty(n_boot)
    for b in range(n_boot):
        w = np.zeros(concepts.size)
        for fam, cs in by_fam.items():
            for c in rng.choice(cs, size=len(cs), replace=True):
                w[idx[c]] += 1
        out[b] = stat(w)
    return out


def interaction(e: np.ndarray, labels: np.ndarray, concepts: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    fam = {c: c.split("/")[0] for c in set(concepts.tolist())}
    hi, lo = labels == "high", labels == "low"

    def stat(w):
        wh, wl = w * hi, w * lo
        if wh.sum() == 0 or wl.sum() == 0:
            return np.nan
        return float(np.sum(wh * e) / wh.sum() - np.sum(wl * e) / wl.sum())

    point = stat(np.ones(e.size))
    boots = _cluster_boot(stat, concepts, fam, n_boot, seed)
    lo95, hi95 = np.nanpercentile(boots, [2.5, 97.5])
    supported = bool((lo95 > 0 or hi95 < 0) and point >= SEOI)
    return {"estimate": point, "ci95": [float(lo95), float(hi95)], "n_boot_nonfinite": int(np.sum(~np.isfinite(boots))),
            "supported": supported, "strong": bool(lo95 >= SEOI), "n_high": int(hi.sum()), "n_low": int(lo.sum())}


def equivalence(e: np.ndarray, concepts: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    fam = {c: c.split("/")[0] for c in set(concepts.tolist())}
    point = float(np.mean(e))
    boots = _cluster_boot(lambda w: float(np.sum(w * e) / w.sum()), concepts, fam, n_boot, seed)
    lo90, hi90 = np.percentile(boots, [5, 95])
    return {"estimate": point, "ci90": [float(lo90), float(hi90)],
            "equivalent": bool(abs(point) < EQUIV and lo90 > -EQUIV and hi90 < EQUIV)}


def positive_control(e_increase_low: np.ndarray, concepts_low: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    fam = {c: c.split("/")[0] for c in set(concepts_low.tolist())}
    point = float(np.mean(e_increase_low))
    boots = _cluster_boot(lambda w: float(np.sum(w * e_increase_low) / w.sum()), concepts_low, fam, n_boot, seed)
    lo95, hi95 = np.percentile(boots, [2.5, 97.5])
    sensitive = bool(point > 0 and lo95 > 0)
    return {"estimate": point, "ci95": [float(lo95), float(hi95)], "sensitive": sensitive,
            "h3": "testable" if sensitive else "not testable"}


def closed_set_correct(answer_logits: np.ndarray, target_pos: np.ndarray) -> np.ndarray:
    return np.argmax(answer_logits, axis=1) == target_pos


def flips(correct_before: np.ndarray, correct_after: np.ndarray, rescue: bool = False) -> dict:
    if rescue:
        return {"denominator": int(correct_before.size), "flips": int(np.sum(~correct_before & correct_after))}
    d = correct_before
    return {"denominator": int(d.sum()), "flips": int(np.sum(d & ~correct_after))}


def dose_regression(e: np.ndarray, dh: np.ndarray, margin: np.ndarray, k: np.ndarray, carrier: np.ndarray,
                    family: np.ndarray) -> dict:
    """OLS of the effect on ||Delta h||, baseline margin, level, carrier and family (one-hot, first level dropped)."""
    cols, names = [np.ones(e.size), dh, margin, k.astype(float)], ["intercept", "delta_h", "baseline_margin", "level"]
    for name, v in (("carrier", carrier), ("family", family)):
        levels = sorted(set(v.tolist()))[1:]
        cols += [(v == x).astype(float) for x in levels]
        names += [f"{name}={x}" for x in levels]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, e, rcond=None)
    return dict(zip(names, beta.tolist()))


def binary_vs_smooth(e: np.ndarray, labels: np.ndarray, z_ref: np.ndarray, concepts: np.ndarray, n_folds: int = 5,
                     seed: int = SEED) -> dict:
    """Held-out Gaussian log score (concept-disjoint folds) of effect ~ state vs effect ~ z (the smooth account)."""
    names = sorted(set(concepts.tolist()))
    rng = random.Random(_seed("bvs", seed))
    rng.shuffle(names)
    fold_of = {c: i % n_folds for i, c in enumerate(names)}
    f = np.array([fold_of[c] for c in concepts])
    xb = (labels == "high").astype(float)
    score = {"binary": 0.0, "smooth": 0.0}
    for r in range(n_folds):
        tr, te = f != r, f == r
        if te.sum() == 0:
            continue
        for key, x in (("binary", xb), ("smooth", np.asarray(z_ref, float))):
            X = np.column_stack([np.ones(tr.sum()), x[tr]])
            beta, *_ = np.linalg.lstsq(X, e[tr], rcond=None)
            resid = e[tr] - X @ beta
            s2 = float(np.mean(resid ** 2))
            mu = beta[0] + beta[1] * x[te]
            score[key] += float(np.sum(-0.5 * np.log(2 * np.pi * s2) - 0.5 * (e[te] - mu) ** 2 / s2))
    n = e.size
    return {"heldout_logscore_per_trial": {k2: v / n for k2, v in score.items()},
            "two_state_may_be_written": bool(score["binary"] > score["smooth"])}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="H3 setup pieces that exist before CONF")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("offtarget", help="write stimuli/h3_offtarget.json")
    args = ap.parse_args()
    if args.cmd == "offtarget":
        bank = json.loads((HERE / "stimuli" / "concepts.json").read_text())
        out = {"seed": SEED, "rule": "per (target family, foil family): one BACKGROUND concept from each of two other "
               "families, seeded", "pairs": offtarget_pairs(bank)}
        (HERE / "stimuli" / "h3_offtarget.json").write_text(json.dumps(out, indent=1) + "\n")
        print(f"{len(out['pairs'])} family combinations -> stimuli/h3_offtarget.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
