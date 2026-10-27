"""bounded/members.py — the M3S mixture member and the per-member start recipe of the bounded comparison (S1).

M3S (method-repair record S1): the ordered two-state mixture with zero occupancy at the catch level and ONE concept
random log-scale v_c ~ N(0, omega^2) multiplying both component scales,

    q_M3S,c = integral prod_i [(1-A(k_i)) N(y_i; mu_low, sigma^2 e^{2v}) + A(k_i) N(y_i; mu_high(k_i), sigma^2 e^{2v})]
              N(v; 0, omega^2) dv,

integrated jointly over every trial of the concept by models.py's two-scale trapezoid rule (re_index = 7, so the
integration variable is v and its prior SD is omega = e^w). Raw parameters (mu_low, d0, d1, kA, kh, x0, s, w), with
mu_high, A and the ordering exactly as models._ordered; sigma = e^s. The likelihood is the prototype's
(scratch repair_local.py / repair_primary_local.py: ll_m3s) byte for byte in its arithmetic.

Moments start: M3H's moment start (models.start_from_moments) with the last coordinate set to log(0.3), the M2S
convention for a log-scale effect - the prototype's start.

Start recipe (S1, S5.13): every member 8 cold starts from the caller's stream (start 0 unjittered, 1..7 jittered at
models.JITTER_SD); M2S additionally 64 keyed narrow starts at jitter SD 0.25 from models.added_start_stream (the
existing keyed streams), key (models.SIZE_OUTER, fold, (seed, layer)); the existing recovery rule (models.fit, S9:
16 further starts, then 16 at doubled jitter, when no start converged) is kept for every member.

Registration happens at import, in memory: models.MEMBERS gains 'M3S' and models.start_from_moments is wrapped so that
models.starts_from_moments returns the M3S start. models.py on disk is not touched. Idempotent.
"""
from __future__ import annotations

import numpy as np

from . import T1  # noqa: F401  (puts t1_access on sys.path)
import models as M
import jax.numpy as jnp

M3S_PARAMS = ("mu_low", "d0", "d1", "kA", "kh", "x0", "s", "w")
M3S_RE_INDEX = 7
M3S_START_W = float(np.log(0.3))


def _ll_M3S(theta, y, k, u, floor):
    """Per-trial log-likelihood of M3S at concept log-scale u (prototype ll_m3s)."""
    low, high, logA, log1mA = M._ordered(theta, k, 0.)
    sigma = jnp.exp(theta[6] + u)
    lnlo = M._log_norm(y, low, sigma)
    mix = jnp.logaddexp(log1mA + lnlo, logA + M._log_norm(y, high, sigma))
    return jnp.where(k == M.K_CATCH, lnlo, mix)


def _register():
    if "M3S" not in M.MEMBERS:
        M.MEMBERS["M3S"] = M.Member("M3S", "X", M3S_PARAMS, _ll_M3S, re_index=M3S_RE_INDEX, mixture=True)
    if not getattr(M.start_from_moments, "_bounded_m3s", False):
        original = M.start_from_moments

        def start_from_moments(name, mom):
            if name == "M3S":
                th = original("M3H", mom)
                th[M3S_RE_INDEX] = M3S_START_W
                return th
            return original(name, mom)
        start_from_moments._bounded_m3s = True
        start_from_moments._original = original
        M.start_from_moments = start_from_moments


_register()

MEMBERS_G = tuple(M.FAMILY_G)                     # M2B M2H M2S M2K
MEMBERS_X = tuple(M.FAMILY_X) + ("M3S",)          # M3 M3H M3V M3L M3S
ORDER = MEMBERS_G + MEMBERS_X                     # j in the cold-start stream key [seed, fold, j]

N_COLD = 8
RECIPE = {m: dict(n_cold=N_COLD, added=()) for m in ORDER}
RECIPE["M2S"] = dict(n_cold=N_COLD, added=((64, 0.25),))


def recipe_table() -> dict:
    """The start recipe as plain data (for the row, the catalogue and the configuration hash)."""
    return {m: dict(n_cold=r["n_cold"], added=[list(b) for b in r["added"]]) for m, r in RECIPE.items()}


def fit_member(name: str, train: "M.Trials", fold: int, seed: int, layer: int, j: int | None = None) -> "M.FitResult":
    """Fit one retained member on one outer training set under the frozen recipe.

    Cold stream: np.random.default_rng([seed, fold, j]) with j the member's index in ORDER (prototype keying).
    Added starts (M2S only): models.fit's keyed streams under policy_key (SIZE_OUTER, fold, (seed, layer))."""
    j = ORDER.index(name) if j is None else int(j)
    r = RECIPE[name]
    rng = np.random.default_rng([int(seed), int(fold), j])
    if r["added"]:
        return M.fit(name, train, n_starts=r["n_cold"], rng=rng,
                     policy_key=(M.SIZE_OUTER, int(fold), (int(seed), int(layer))),
                     policy={name: tuple(tuple(b) for b in r["added"])})
    return M.fit(name, train, n_starts=r["n_cold"], rng=rng)


def m3s_theta(mu_low: float, sep0: float, sep1: float, kA: float, kh: float, x0: float, sigma: float,
              omega: float) -> np.ndarray:
    """Raw M3S vector from natural values: sep0 = e^{d0}, sep1 = e^{d1}, sigma = e^s, omega = e^w."""
    return np.array([mu_low, np.log(sep0), np.log(sep1), kA, kh, x0, np.log(sigma), np.log(max(omega, 1e-8))])
