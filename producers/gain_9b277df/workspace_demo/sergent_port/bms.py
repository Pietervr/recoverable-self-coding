#!/usr/bin/env python3
"""Random-effects Bayesian model selection — a port of SPM12's spm_BMS.m (Stephan et al. 2009,
NeuroImage 46:1004) with the protected exceedance probability and Bayes omnibus risk of
spm_BMS_bor.m (Rigoux et al. 2014, NeuroImage 84:971), as called by
SoundConsciousEEG_SingleTrialPredict_ModelComp_Twind_PlotFig.m:  spm_BMS(lme, [], 0, 0, 1).

Written from the SPM12 sources' algorithm (variational Dirichlet update, convergence
norm(alpha - prev) < 1e-3, uniform Dirichlet prior alpha0 = 1, exceedance probabilities by 1e6
Dirichlet samples for > 2 models, free energies F1 (RFX) and F0 (null: all models equally frequent)
for the BOR). SPM itself is not imported.
"""
from __future__ import annotations

import numpy as np
from scipy.special import gammaln, psi

EPS = np.finfo(float).eps  # MATLAB eps


def dirichlet_exceedance(alpha, nsamp=1_000_000, rng=None):
    rng = np.random.default_rng(0) if rng is None else rng
    alpha = np.asarray(alpha, dtype=float)
    r = rng.gamma(shape=alpha, scale=1.0, size=(int(nsamp), alpha.size))
    j = np.argmax(r, axis=1)  # normalisation does not change the argmax
    return np.bincount(j, minlength=alpha.size) / float(nsamp)


def _free_energy(L, post_a, post_r, prior_a):
    """FE(L, posterior, priors) of spm_BMS_bor: L is (K, n)."""
    K, n = L.shape
    a0 = np.sum(prior_a)
    Elogr = psi(post_a) - psi(np.sum(post_a))
    Sqf = np.sum(gammaln(post_a)) - gammaln(np.sum(post_a)) - np.sum((post_a - 1) * Elogr)
    Sqm = -np.sum(post_r * np.log(post_r + EPS))
    ELJ = gammaln(a0) - np.sum(gammaln(prior_a)) + np.sum((prior_a - 1) * Elogr)
    ELJ += np.sum(post_r * (Elogr[:, None] + L))
    return ELJ + Sqf + Sqm


def _free_energy_null(L):
    """FE_null(L): the null hypothesis that all models are equally frequent."""
    K, n = L.shape
    F0 = 0.0
    for i in range(n):
        tmp = L[:, i] - np.max(L[:, i])
        g = np.exp(tmp) / np.sum(np.exp(tmp))
        F0 += np.sum(g * (L[:, i] - np.log(K) - np.log(g + EPS)))
    return F0


def spm_bms(lme, nsamp=1_000_000, alpha0=None, rng=None):
    """lme: (n_subjects, n_models) log model evidences.

    Returns dict(alpha, exp_r, xp, pxp, bor, g) where g (n_subjects, n_models) are the posterior
    model-assignment probabilities.
    """
    lme = np.asarray(lme, dtype=float)
    Ni, Nk = lme.shape
    alpha0 = np.ones(Nk) if alpha0 is None else np.asarray(alpha0, dtype=float)
    alpha = alpha0.copy()
    c, cc = 1.0, 10e-4
    n_iter = 0
    while c > cc:
        log_u = lme + psi(alpha)[None, :] - psi(np.sum(alpha))
        log_u = log_u - log_u.max(axis=1, keepdims=True)
        u = np.exp(log_u)
        g = u / u.sum(axis=1, keepdims=True)
        beta = g.sum(axis=0)
        prev = alpha
        alpha = alpha0 + beta
        c = np.linalg.norm(alpha - prev)
        n_iter += 1
        if n_iter > 10000:
            raise RuntimeError("spm_bms did not converge")
    exp_r = alpha / np.sum(alpha)
    if Nk == 2:
        from scipy.stats import beta as beta_dist
        xp = np.array([beta_dist.cdf(0.5, alpha[1], alpha[0]), beta_dist.cdf(0.5, alpha[0], alpha[1])])
    else:
        xp = dirichlet_exceedance(alpha, nsamp, rng)
    L = lme.T  # (K, n)
    F1 = _free_energy(L, alpha, g.T, alpha0)
    F0 = _free_energy_null(L)
    bor = 1.0 / (1.0 + np.exp(F1 - F0))
    pxp = (1 - bor) * xp + bor / Nk
    return dict(alpha=alpha, exp_r=exp_r, xp=xp, pxp=pxp, bor=bor, g=g, F1=F1, F0=F0, n_iter=n_iter)


def simes_threshold(pvals, alpha=0.05):
    """MCP_fromPval_fn(p, alpha, 'Simes') equivalent: the Benjamini-Hochberg / Simes step-up rule.

    Returns (critical p-value, boolean mask of rejected tests). Rejected = p <= p_(k) where k is the
    largest index with p_(k) <= alpha * k / m; returns (nan, all False) when nothing is rejected.
    """
    p = np.asarray(pvals, dtype=float)
    m = p.size
    order = np.argsort(p)
    ps = p[order]
    crit = alpha * np.arange(1, m + 1) / m
    ok = np.where(ps <= crit)[0]
    if ok.size == 0:
        return np.nan, np.zeros(m, dtype=bool)
    k = ok.max()
    thr = ps[k]
    return thr, p <= thr


if __name__ == "__main__":
    # sanity checks: identical evidences -> uniform; one dominant model -> pxp ~ 1
    rng = np.random.default_rng(1)
    lme = np.zeros((20, 3))
    r = spm_bms(lme, nsamp=200_000, rng=rng)
    print("identical evidences: exp_r", np.round(r["exp_r"], 3), "xp", np.round(r["xp"], 3),
          "pxp", np.round(r["pxp"], 3), "bor %.3f" % r["bor"])
    lme = np.zeros((20, 3)); lme[:, 2] += 5.0
    r = spm_bms(lme, nsamp=200_000, rng=rng)
    print("model 3 +5 nats in every subject: exp_r", np.round(r["exp_r"], 3), "xp", np.round(r["xp"], 3),
          "pxp", np.round(r["pxp"], 3), "bor %.3g" % r["bor"])
    lme = rng.normal(size=(20, 3)) * 0.5; lme[:12, 1] += 3; lme[12:, 2] += 3
    r = spm_bms(lme, nsamp=200_000, rng=rng)
    print("mixed population (12 vs 8): exp_r", np.round(r["exp_r"], 3), "xp", np.round(r["xp"], 3),
          "pxp", np.round(r["pxp"], 3), "bor %.3g" % r["bor"])
