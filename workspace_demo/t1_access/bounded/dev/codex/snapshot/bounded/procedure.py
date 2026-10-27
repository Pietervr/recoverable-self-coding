"""bounded/procedure.py — the point pipeline of the bounded comparison, exactly as method-repair record S1.

One layer (41). Concept-disjoint outer folds stratified by family, three of them (analyze.stratified_folds, seeded by
the dataset seed). No inner selection. Every retained member is fitted on every outer training set (bounded.members
recipe) and scores its held-out concepts by the joint concept likelihood (models.concept_scores). Within each family
the members' JOINT concept densities are averaged with equal weights:

    log q_F,c = log( (1/|F|) sum_{m in F} q_m,c ),      G = (M2B, M2H, M2S, M2K),  X = (M3, M3H, M3V, M3L, M3S)

    d_c = (log q_X,c - log q_G,c) / n_c,     z_c = clip(d_c, -a, a),  a = 0.03,
    T   = sum_h W_h mean_{c in h} z_c,       W_h = n_h / 64 fixed (27/64, 22/64, 15/64),

and the unbounded mean U = sum_h W_h mean_{c in h} d_c is kept as a descriptive field only. A fit without a finite
solution, a non-finite held-out score or a non-finite d_c makes the dataset UNAVAILABLE, with its reason; it is never
dropped and never replaced. A converged-flag failure alone is the existing recovery rule's business (models.fit, S9)
and is recorded per fit, not an unavailability (as in analyze.layer_pipeline).

Pure functions (`bounded_statistic`, `assemble`) carry the arithmetic so that it can be tested without fitting.
"""
from __future__ import annotations

import time

import numpy as np
from scipy.special import logsumexp

from . import members as MB
import analyze as A
import models as M

CAP = 0.03
N_OUTER = 3
LAYER = 41
FAMILY_COUNTS = (27, 22, 15)                       # CONF animals / foods / vehicles (PROPOSED role map)
N_CONCEPTS = sum(FAMILY_COUNTS)                    # 64
FAMILY_WEIGHTS = tuple(n / N_CONCEPTS for n in FAMILY_COUNTS)


def family_labels() -> np.ndarray:
    """(64,) stratum label per concept index: 0 x27, 1 x22, 2 x15 (the declared design profile)."""
    return np.repeat(np.arange(len(FAMILY_COUNTS)), FAMILY_COUNTS)


def bounded_statistic(delta, family, weights=FAMILY_WEIGHTS, cap: float = CAP) -> dict:
    """T (bounded) and U (unbounded) from per-concept d_c and fixed stratum weights; raises on a non-finite d_c."""
    delta = np.asarray(delta, dtype=float)
    family = np.asarray(family)
    strata = np.unique(family)
    if delta.ndim != 1 or delta.shape != family.shape or delta.size == 0:
        raise ValueError("bad concept map")
    if len(weights) != strata.size or not np.isclose(sum(weights), 1.0):
        raise ValueError("one fixed weight per stratum, summing to one")
    if not np.all(np.isfinite(delta)):
        raise ValueError("unavailable concept score")
    z = np.clip(delta, -cap, cap)
    zh = [float(np.mean(z[family == h])) for h in strata]
    dh = [float(np.mean(delta[family == h])) for h in strata]
    T = float(sum(w * m for w, m in zip(weights, zh)))
    U = float(sum(w * m for w, m in zip(weights, dh)))
    return dict(T=T, unbounded=U, z=z, family_bounded_means=zh, family_unbounded_means=dh,
                n_clipped_low=int(np.sum(delta < -cap)), n_clipped_high=int(np.sum(delta > cap)))


def assemble(logq: dict, n_c, family, members_G=MB.MEMBERS_G, members_X=MB.MEMBERS_X) -> dict:
    """From held-out joint log scores {member: (C,)} to the ensembles, d_c, z_c, T and U, or UNAVAILABLE."""
    n_c = np.asarray(n_c, dtype=float)
    bad = [m for m in tuple(members_G) + tuple(members_X)
           if m not in logq or not np.all(np.isfinite(np.asarray(logq[m], dtype=float)))]
    if bad:
        return dict(unavailable=True, reason=f"held-out score not finite for {','.join(bad)}")
    gG = logsumexp(np.stack([np.asarray(logq[m], float) for m in members_G]), axis=0) - np.log(len(members_G))
    gX = logsumexp(np.stack([np.asarray(logq[m], float) for m in members_X]), axis=0) - np.log(len(members_X))
    delta = (gX - gG) / n_c
    if not np.all(np.isfinite(delta)):
        return dict(unavailable=True, reason="non-finite concept contrast d_c")
    st = bounded_statistic(delta, family)
    return dict(unavailable=False, reason="", ens_G=gG, ens_X=gX, delta=delta, **st)


def point_pipeline(y, k, concept, family, seed: int, layer: int = LAYER, n_outer: int = N_OUTER,
                   members_G=MB.MEMBERS_G, members_X=MB.MEMBERS_X, fit_member=None, on_fit=None,
                   check_profile: bool = True) -> dict:
    """S1's point procedure on one layer's response column y (n,), levels k, concept index (n,) and family (C,).

    `seed` keys the outer folds (analyze.stratified_folds(family, n_outer, seed)) and every fit stream (members.fit_member).
    `members_G/X`, `fit_member` and `check_profile` exist for tests only; production calls use the defaults. Returns a dict with the
    folds, per-fit records, held-out joint log scores, n_c, d_c, z_c, T, U and the availability verdict."""
    fit_member = MB.fit_member if fit_member is None else fit_member
    y = np.asarray(y, dtype=float); k = np.asarray(k, dtype=float); concept = np.asarray(concept, dtype=np.int64)
    family = np.asarray(family)
    C = family.size
    if check_profile and tuple(np.bincount(family)) != FAMILY_COUNTS:
        raise ValueError(f"family profile {tuple(np.bincount(family))} != declared {FAMILY_COUNTS}")
    order = tuple(members_G) + tuple(members_X)
    folds = A.stratified_folds(family, n_outer, int(seed))
    n_c = np.bincount(concept, minlength=C).astype(float)
    logq = {m: np.full(C, np.nan) for m in order}
    fits, reasons = [], []
    for f, test_c in enumerate(folds):
        train_c = np.setdiff1d(np.arange(C), test_c)
        floor = float(np.std(y[np.isin(concept, train_c)], ddof=1))
        tr = A._subset(y, k, concept, train_c, floor)
        te = A._subset(y, k, concept, test_c, floor)
        for j, m in enumerate(order):
            c0, w0 = time.process_time(), time.monotonic()
            fit = fit_member(m, tr, f, int(seed), int(layer), MB.ORDER.index(m) if m in MB.ORDER else j)
            finite = bool(np.all(np.isfinite(fit.theta)))
            sc = M.concept_scores(m, fit.theta, te) if finite else np.full(test_c.size, np.nan)
            logq[m][test_c] = sc
            rec = dict(fold=f, member=m, converged=bool(fit.converged), n_converged=int(fit.n_converged),
                       n_starts=int(fit.n_starts), n_added=int(fit.n_added), recovery=int(fit.recovery),
                       loglik=(float(fit.loglik) if np.isfinite(fit.loglik) else None),
                       theta=[float(v) if np.isfinite(v) else None for v in np.asarray(fit.theta, float)],
                       nfev=int(fit.nfev), nit=int(fit.nit),
                       cpu_seconds=time.process_time() - c0, wall_seconds=time.monotonic() - w0)
            if not finite:
                reasons.append(f"fold {f} {m}: no finite fit")
            elif not np.all(np.isfinite(sc)):
                reasons.append(f"fold {f} {m}: non-finite held-out score")
            fits.append(rec)
            if on_fit is not None:
                on_fit(rec)
    out = assemble(logq, n_c, family, members_G, members_X)
    if reasons:
        out = dict(unavailable=True, reason="; ".join(reasons))
    out.update(folds=[[int(c) for c in f] for f in folds], fits=fits, logq=logq, n_c=n_c, layer=int(layer),
               n_outer=int(n_outer), members_G=list(members_G), members_X=list(members_X))
    return out
