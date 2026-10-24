#!/usr/bin/env python3
"""jitter/simulate.py — the generators of DESIGN_jitter.md rev 6 §7.1–§7.3 and the inherited-pipeline mechanism
test of §7.6. Stage S1 (provisional; generator algorithms FROZEN at S3).

A synthetic participant has one coherent generating distribution across all five folds, with its base
participant's level counts and block labels (§7.2). Synthetic data are 53-window vectors generated from a
whole-epoch GeneratorConfig (a, T̃, κ, x0, s_τ, s_g, μ0, Σ): y_i = μ0 + g_i m(k_i) T̃(· − τ_i) + ε_i, ε ~ N(0, Σ),
τ continuous truncated normal (±150 ms, NOT the fitting nodes), g lognormal with mean one; two-state draws
z_i ~ Bernoulli(A(k_i)) and uses m_H = a/A on the high branch. The window value of a shifted template is the
mean of T̃(t − τ) over the window's 16 sample times (the continuous B-spline, `scipy.interpolate.BSpline`).

Settings (§7.3): W1 (0, 0); W2 fitted G3; W3 (80 ms, 0); W4 (0, 1.0);
  O1 per-trial time stretch about 240 ms, template continued beyond its support by its endpoint values;
  O2 two components split at 450 ms by a logistic ramp of slope 1/30 ms, w ~ Beta(2, 2);
  O3 level-dependent s_τ {60, 60, 40, 20, 20} ms; O4 (log g, τ) bivariate normal, ρ = −0.5, s_τ = 60, g rescaled
  to mean one under the truncation; O5 covariance challenge (real within-level distribution recentred to the G3
  generator's marginal level mean); T1 fitted B3; T2 B3 with s_τ = 80 and occupancy A/2 (m_H recomputed);
  λ path: a(k) × λ (m_H follows, occupancy unchanged) for T3 and E1.
Seeds: disjoint keyed streams per (stage, setting, replicate, member); development, calibration and validation
seeds never overlap (§7.7).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import quad
from scipy.interpolate import BSpline
from scipy.stats import truncnorm

import data as D
import models as M
from fit import GeneratorConfig

STAGE_OFFSET = {"development": 1, "calibration": 2, "validation": 3}
O3_S_TAU_BY_LEVEL = {1: 60.0, 2: 60.0, 3: 40.0, 4: 20.0, 5: 20.0}
O4_RHO, O4_S_TAU = -0.5, 60.0
O1_CENTRE_MS, O1_SD, O1_TRUNC = 240.0, 0.25, 0.5
O2_SPLIT_MS, O2_SLOPE_MS = 450.0, 30.0
T2_S_TAU = 80.0
MECHANISM = {"W1": (0.0, 0.0), "W3": (80.0, 0.0), "W4": (0.0, 1.0)}
RECOVERY_S_TAU = (0.0, 20.0, 40.0, 80.0)
RECOVERY_S_G = (0.0, "fitted", 1.0)


def seed_for(stage: str, setting: str, replicate: int, member: int = 0, extra: str = "") -> int:
    if stage not in STAGE_OFFSET:
        raise KeyError(stage)
    h = hashlib.sha256(f"{STAGE_OFFSET[stage]}|{setting}|{replicate}|{member}|{extra}".encode()).hexdigest()
    return int(h[:12], 16)


# ----------------------------------------------------------------------------------------------
# the continuous template and the latent draws
# ----------------------------------------------------------------------------------------------
def spline(cfg: GeneratorConfig) -> BSpline:
    b = M.basis("whole")
    return BSpline(b.knots, cfg.c_tilde, 3, extrapolate=False)


def template_windows(cfg: GeneratorConfig, tau_ms: np.ndarray, times_ms: np.ndarray | None = None,
                     clamp: bool = False) -> np.ndarray:
    """(n, 53) window means of T̃(t − τ_i). `times_ms` (n, 53, 16) overrides the sample times (O1 stretch)."""
    b = M.basis("whole")
    st = b.span.sample_times_ms if times_ms is None else times_ms
    t = st[None, :, :] - np.asarray(tau_ms)[:, None, None] if times_ms is None else st - np.asarray(tau_ms)[:, None, None]
    lo, hi = b.knots[0], b.knots[-1]
    t = np.clip(t, lo, np.nextafter(hi, lo)) if clamp else np.where(t >= hi, np.nextafter(hi, lo), t)
    vals = spline(cfg)(t)
    return vals.mean(axis=2)


def draw_latency(rng: np.random.Generator, n: int, s_tau_ms) -> np.ndarray:
    """τ ~ N(0, s²) truncated to ±150 ms (continuous); vector `s_tau_ms` allowed (O3)."""
    s = np.broadcast_to(np.asarray(s_tau_ms, dtype=np.float64), (n,))
    out = np.zeros(n)
    pos = s > 0
    if np.any(pos):
        a = D.TAU_TRUNC_MS / s[pos]
        out[pos] = truncnorm.rvs(-a, a, loc=0.0, scale=s[pos], random_state=rng)
    return out


def draw_scale(rng: np.random.Generator, n: int, s_g: float) -> np.ndarray:
    if s_g <= 0:
        return np.ones(n)
    return np.exp(rng.normal(-0.5 * s_g ** 2, s_g, size=n))


def level_means(cfg: GeneratorConfig) -> np.ndarray:
    """(6, 53) marginal level means μ0 + a(k) E[T̃_τ] under the config's (nodal) latency law."""
    b = M.basis("whole")
    if cfg.s_tau_ms > 0:
        w = M.truncnorm_node_weights(b.nodes_ms, cfg.s_tau_ms)
        ET = np.einsum("n,nw->w", w, np.einsum("nwj,j->nw", b.Bmat, cfg.c_tilde))
    else:
        ET = b.Bmat[b.node0] @ cfg.c_tilde
    return cfg.mu0[None, :] + cfg.a[:, None] * ET[None, :]


# ----------------------------------------------------------------------------------------------
# settings as configuration transforms
# ----------------------------------------------------------------------------------------------
def with_nuisance(cfg: GeneratorConfig, s_tau_ms: float, s_g: float) -> GeneratorConfig:
    return replace(cfg, s_tau_ms=float(s_tau_ms), s_g=float(s_g))


def scaled(cfg: GeneratorConfig, lam: float) -> GeneratorConfig:
    """λ path: a(k) × λ at every level (m_H follows, occupancy unchanged)."""
    return replace(cfg, a=cfg.a * lam)


def halved_occupancy(cfg: GeneratorConfig) -> GeneratorConfig:
    """T2: B3 with s_τ = 80 ms and occupancy A(k)/2 at every level; m_H recomputed so level means are
    unchanged; values below 0.02 are generated as is and recorded (`flags`)."""
    A = cfg.A.copy()
    A[1:] = A[1:] / 2.0
    flags = list(cfg.flags) + [f"T2 occupancy below A_MIN at levels {np.where(A[1:] < M.A_MIN)[0] + 1}"]
    return replace(cfg, A=A, s_tau_ms=T2_S_TAU, flags=flags)


def recovery_setting(cfg: GeneratorConfig, s_tau, s_g) -> GeneratorConfig:
    return with_nuisance(cfg, s_tau, cfg.s_g if s_g == "fitted" else s_g)


# ----------------------------------------------------------------------------------------------
# generation
# ----------------------------------------------------------------------------------------------
@dataclass
class Synthetic:
    W53: np.ndarray
    levels: np.ndarray
    blocks: np.ndarray
    tau: np.ndarray
    g: np.ndarray
    z: np.ndarray | None
    setting: str
    seed: int
    base: str

    def participant(self, subject: int = 0) -> D.Participant:
        return D.participant_from_windows(self.W53, self.levels, self.blocks, subject, f"syn-{self.setting}",
                                          f"-{self.seed}")


def _two_state_draw(rng, cfg, k):
    if cfg.family != "B":
        return None, cfg.a[k]
    z = rng.random(k.size) < cfg.A[k]
    mH = np.where(cfg.A > 0, cfg.a / np.where(cfg.A > 0, cfg.A, 1.0), 0.0)
    return z, np.where(z, mH[k], 0.0)


def generate(cfg: GeneratorConfig, levels: np.ndarray, blocks: np.ndarray, seed: int, setting: str = "W",
             base_W53: np.ndarray | None = None) -> Synthetic:
    """One synthetic participant from `cfg` at `setting` with the base's level counts and block labels.
    Settings: 'W' (the config's own nuisance), 'O1'..'O5', 'T2' (config already transformed), λ handled by
    `scaled`. O5 needs the base participant's real window means."""
    rng = np.random.default_rng(seed)
    k = np.asarray(levels, dtype=np.int64)
    n = k.size
    W = 53
    noise = rng.multivariate_normal(np.zeros(W), cfg.Sigma, size=n, method="cholesky")
    b = M.basis("whole")
    st = b.span.sample_times_ms
    tau = draw_latency(rng, n, cfg.s_tau_ms)
    g = draw_scale(rng, n, cfg.s_g)
    z, m = _two_state_draw(rng, cfg, k)
    if setting in ("W", "T2"):
        T = template_windows(cfg, tau)
        Y = cfg.mu0 + (g * m)[:, None] * T + noise
    elif setting == "O1":
        zeta = truncnorm.rvs(-O1_TRUNC / O1_SD, O1_TRUNC / O1_SD, loc=0.0, scale=O1_SD, size=n, random_state=rng)
        times = O1_CENTRE_MS + (st[None, :, :] - O1_CENTRE_MS) * np.exp(zeta)[:, None, None]
        T = template_windows(cfg, np.zeros(n), times, clamp=True)
        tau = np.zeros(n)
        Y = cfg.mu0 + (g * m)[:, None] * T + noise
    elif setting == "O2":
        tau = np.zeros(n)
        r = 1.0 / (1.0 + np.exp(-(st - O2_SPLIT_MS) / O2_SLOPE_MS))          # (53, 16) ramp
        vals = spline(cfg)(np.where(st >= b.knots[-1], np.nextafter(b.knots[-1], 0), st))  # (53, 16)
        Ta = (vals * (1.0 - r)).mean(axis=1)
        Tb = (vals * r).mean(axis=1)
        w = rng.beta(2.0, 2.0, size=n)
        T = 2.0 * w[:, None] * Ta[None, :] + 2.0 * (1.0 - w)[:, None] * Tb[None, :]
        Y = cfg.mu0 + (g * m)[:, None] * T + noise
    elif setting == "O3":
        s = np.array([0.0] + [O3_S_TAU_BY_LEVEL[i] for i in range(1, 6)])[k]
        tau = draw_latency(rng, n, s)
        T = template_windows(cfg, tau)
        Y = cfg.mu0 + (g * m)[:, None] * T + noise
    elif setting == "O4":
        s_g = cfg.s_g
        cov = np.array([[s_g ** 2, O4_RHO * s_g * O4_S_TAU], [O4_RHO * s_g * O4_S_TAU, O4_S_TAU ** 2]])
        draws = rng.multivariate_normal([-0.5 * s_g ** 2, 0.0], cov, size=4 * n)
        keep = np.abs(draws[:, 1]) <= D.TAU_TRUNC_MS
        draws = draws[keep][:n]
        while draws.shape[0] < n:
            more = rng.multivariate_normal([-0.5 * s_g ** 2, 0.0], cov, size=4 * n)
            draws = np.vstack([draws, more[np.abs(more[:, 1]) <= D.TAU_TRUNC_MS]])[:n]
        tau = draws[:, 1]
        g = np.exp(draws[:, 0]) / _o4_mean_g(s_g)
        T = template_windows(cfg, tau)
        Y = cfg.mu0 + (g * m)[:, None] * T + noise
    elif setting == "O5":
        if base_W53 is None:
            raise ValueError("O5 needs the base participant's real window means")
        tau = np.zeros(n); g = np.ones(n)
        mk = level_means(cfg)
        Y = np.empty((n, W))
        for lev in range(6):
            idx = np.where(k == lev)[0]
            real = base_W53[np.asarray(levels) == lev]
            pick = rng.integers(0, real.shape[0], size=idx.size)
            Y[idx] = mk[lev] + (real[pick] - real.mean(axis=0))
    else:
        raise KeyError(setting)
    return Synthetic(Y, k, np.asarray(blocks, dtype=np.int64), tau, g, z, setting, seed, cfg.base)


def _o4_mean_g(s_g: float) -> float:
    """E[g | |τ| ≤ 150] for (log g, τ) bivariate normal with ρ = −0.5, so that O4's g has mean one after the
    truncation (deterministic rescaling, not a sample mean)."""
    if s_g <= 0:
        return 1.0
    mu_x = -0.5 * s_g ** 2
    T = D.TAU_TRUNC_MS

    def integrand(tau):
        cond_mean = mu_x + O4_RHO * s_g * tau / O4_S_TAU
        cond_var = s_g ** 2 * (1.0 - O4_RHO ** 2)
        return np.exp(cond_mean + 0.5 * cond_var) * np.exp(-0.5 * (tau / O4_S_TAU) ** 2)

    num = quad(integrand, -T, T)[0]
    den = quad(lambda tau: np.exp(-0.5 * (tau / O4_S_TAU) ** 2), -T, T)[0]
    return float(num / den)


def replicate_set(configs: list, rng: np.random.Generator, n: int = 20) -> list:
    """Decision calibration: 20 base configurations drawn with replacement from the 20 (§7.2)."""
    return [configs[i] for i in rng.integers(0, len(configs), size=n)]


# ----------------------------------------------------------------------------------------------
# the inherited per-window pipeline on 53-window vectors (§7.6)
# ----------------------------------------------------------------------------------------------
def inherited_fits(W53: np.ndarray, levels: np.ndarray, blocks: np.ndarray, ncv: int = 5) -> np.ndarray:
    """The unchanged per-window likelihoods and starting values of `sergent_port/fit_models.py` on a 53-window
    matrix (nothing filtered or averaged again). Returns the (53, 3) matrix of mean-over-folds held-out
    log-likelihood for model0, model2B, model3 (the 'lme' handed to spm_BMS)."""
    import fit_models as FM
    snr0 = np.asarray(levels, dtype=np.int64)
    SNR_list = np.unique(snr0).astype(float)
    train_sets, test_sets = FM.block_folds(np.asarray(blocks), ncv)
    out = np.empty((W53.shape[1], 3))

    def sel(level):
        return snr0 == level

    for it in range(W53.shape[1]):
        tw = W53[:, it]
        acc = np.zeros(3)
        init0 = np.array([1.0, 0.0])
        m_max = tw[sel(SNR_list[-1])].mean(); m_min = tw[sel(SNR_list[1])].mean()
        s_max = tw[sel(SNR_list[-1])].std(ddof=1); s_min = tw[sel(SNR_list[1])].std(ddof=1)
        m_noise = tw[sel(SNR_list[0])].mean()
        initx0 = (SNR_list[-1] + SNR_list[1]) / 2.0
        initk = (m_max - m_min) / (SNR_list[-1] - SNR_list[1])
        init2B = np.array([initx0, initk, 2.0 * m_max, (s_max - s_min) / (m_max - m_min),
                           s_max - (s_max - s_min) / (m_max - m_min) * m_max, m_max])
        init3 = np.array([initx0, initk, m_noise, m_min - m_noise, m_max - m_min, initk, tw[sel(SNR_list[0])].std(ddof=1)])
        for icv in range(ncv):
            tr, te = train_sets[icv], test_sets[icv]
            bp, _, _, _ = FM.fminsearch(lambda p: -FM.llh_null(p, tw[tr]), init0)
            acc[0] += FM.llh_null(bp, tw[te])
            bp, _, _, _ = FM.fminsearch(lambda p: -FM.llh_logisticB(p, tw[tr], snr0[tr].astype(float)), init2B)
            acc[1] += FM.llh_logisticB(bp, tw[te], snr0[te].astype(float))
            f_tr = snr0[tr] == np.min(snr0[tr]); f_te = snr0[te] == np.min(snr0[te])
            bp, _, _, _ = FM.fminsearch(lambda p: -FM.llh_logisbimodalfixedsigma(p, tw[tr], snr0[tr].astype(float), f_tr), init3)
            acc[2] += FM.llh_logisbimodalfixedsigma(bp, tw[te], snr0[te].astype(float), f_te)
        out[it] = acc / ncv
    return out


def inherited_group_summary(lme_by_participant: list, nsamp: int = 1_000_000, seed: int = 0,
                            primary_windows=D.PRIMARY_WINDOWS) -> dict:
    """spm_BMS per window on (participants × 3) evidences; the paper's three summaries and the binary 'call'
    (a run of ≥ 3 consecutive windows with M3 the highest pxp whose first window lies inside the primary span)."""
    from bms import simes_threshold, spm_bms
    L = np.stack(lme_by_participant)              # (P, 53, 3)
    rng = np.random.default_rng(seed)
    pxp = np.empty((53, 3))
    for w in range(53):
        pxp[w] = spm_bms(L[:, w, :], nsamp=nsamp, rng=rng)["pxp"]
    centres = D.window_centres_ms()
    above = np.where(pxp[:, 2] > 0.95)[0]
    first_above = float(centres[above[0]]) if above.size else None
    highest = (pxp[:, 2] > pxp[:, 0]) & (pxp[:, 2] > pxp[:, 1])     # ties count as not highest
    run_start = None
    for w in range(53 - 2):
        if highest[w] and highest[w + 1] and highest[w + 2]:
            run_start = w
            break
    thr, _ = simes_threshold(1.0 - pxp[:, 2], 0.05)
    simes_strict = [] if np.isnan(thr) else [float(c) for c in centres[(1.0 - pxp[:, 2]) < thr]]
    call = run_start is not None and run_start in set(int(i) for i in primary_windows)
    return dict(pxp=pxp, first_window_pxp_above_095_ms=first_above,
                first_run_start_ms=None if run_start is None else float(centres[run_start]),
                simes_strict_ms=simes_strict, call=bool(call))
