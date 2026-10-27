"""bounded/generators.py — the S3 generator catalogue of the bounded-comparison qualification and its datasets.

Thirty settings (method-repair record S3): sixteen graded and fourteen mixture alternatives.

  graded, historical (12, via simulate.py exactly): M2B; M2H tau 0/.5/1/2; M2S omega 0/.5/1/2; M2K alpha 0/1/3
  graded, new (4):
    G13 low-amplitude M2B          simulate.generator_theta('M2B', base=BASE with mu(0) = -0.1, mu(8) = +0.1)
    G14 boundary                   mu(k) of the base M2B; log sigma(k) = log 0.75 + lambda sin(pi k / 8)^2; Gaussian.
                                   lambda is a parameter, NOT searched here: the catalogue holds lambda = null until the
                                   S3 development search certifies it; the smoke run uses the declared placeholder 0.5.
    G15 t5 graded                  M2H mean with threshold variation tau = 0.5; innovations t(5) scaled to unit variance,
                                   times the M2B affine scale |a mu + b|.
    G16 nonlinear-variance graded  mu(k) of the base M2B; sigma(k) = 0.6 + 0.4 exp(-(k - 3)^2 / 2) (not affine in mu);
                                   concept log-scale v_c ~ N(0, 1); carrier effect gamma_r ~ N(0, 0.2^2) shared by all
                                   concepts; background effect beta_{c,r,d} ~ N(0, 0.2^2) per (concept, carrier, draw),
                                   shared by that draw's seven nested levels and weighted (8 - k)/8, the share of the
                                   packet's eight slots still holding background clauses (PREREGISTRATION_T1_model.md §3,
                                   "Packet and nesting"). The 0.2 SDs are declared development stress values, not CAL.
  alternatives (14):
    A01-A12 M3, M3H (tau .5), M3V, M3L (pi0 .05) at the three historical gains 0.003 / 0.01 / 0.03; the scale constants
            of sim_results/gain_sens600/gain_calibration_D4.json are STARTING VALUES ONLY (S3: all fourteen gains are to
            be re-certified against the graded reference under the frozen implementation before qualification).
    A13-A14 M3S at concept log-scale SD omega = 1 and 2, middle gain; starting scale = M3H's 0.01-nat constant.

Design profile (every setting): 64 concepts in three strata 27/22/15, D = 4, six carriers, seven levels (0,1,2,3,4,6,8),
168 trials per concept, one layer (41). simulate.make_dataset/make_design supply the concept x carrier x level x draw
layout; the family labels are replaced by the three declared strata (generation never reads them).

Seeds (seed rule v2, Codex round 4 N4): dataset_seed(namespace, setting, replicate) is the 128-bit integer formed
from the first 32 hex digits of SHA-256("bounded-seed-v2|<namespace value>|<SHA-256 of 'setting:<id>'>|<SHA-256 of
'replicate:<r>'>") - the setting and replicate tags hashed separately, nothing reduced to 31 bits. Namespaces:
calibration 271200, validation 271300, and separate DEVELOPMENT blocks - smoke 271100, benchmark 271110, adaptive
boundary search 271120, untouched boundary certification 271130, gain reference/check work 271140. (The 30 smoke rows of
RSC 77789e1 were drawn under the superseded 31-bit rule v1; they stay development evidence under their own hash.)

The catalogue is read ONCE, at this module's import, as bytes: those bytes are digested (CATALOGUE.sha256) and parsed,
and every dataset of the process is built from that parsed object (B1). A changed file on disk changes nothing until
a new process loads it under a new identity. `python -m bounded.generators --write` regenerates catalogue.json from
build_catalogue().

M3S truth adapter (`m3s_components`, `m3s_sample_dataset`, `m3s_truth_logq`): the only route to M3S data and to its
true joint marginal concept density. models.components / models.sample / simulate.make_dataset /
simulate.expected_gain / simulate.generator_theta REFUSE "M3S" (guards installed by bounded.members): models.components
would silently fall through to its M3L branch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

import numpy as np

from . import HERE, T1
from . import members as MB
from . import procedure as P
import analyze as A
import models as M
import simulate as S

with open(__file__, "rb") as _fh:
    LOADED_SOURCE_DIGEST = hashlib.sha256(_fh.read()).hexdigest()          # bound at this module's own import (B1)

CATALOGUE_PATH = os.path.join(HERE, "catalogue.json")
NAMESPACES = {"calibration": 271200, "validation": 271300,
              "development": 271100,                      # the smoke block
              "dev_benchmark": 271110, "dev_boundary_search": 271120, "dev_boundary_certification": 271130,
              "dev_gain": 271140}
DEVELOPMENT_NAMESPACES = ("development", "dev_benchmark", "dev_boundary_search", "dev_boundary_certification", "dev_gain")
QUALIFICATION_NAMESPACES = ("calibration", "validation")
SEED_RULE = "bounded-seed-v2"
GAIN_ARTEFACT = os.path.join(T1, "sim_results", "gain_sens600", "gain_calibration_D4.json")
D = 4
N_CARRIERS = 6
BOUNDARY_SMOKE_LAMBDA = 0.5          # development placeholder for the smoke run only; never a frozen value
COUNTS = dict(development_smoke=1, calibration=500, validation_graded=400, validation_alternative=1000)


def _h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def dataset_seed(namespace: str, setting: str, replicate: int) -> int:
    """128-bit dataset seed (seed rule v2); the folds and every fit stream are keyed by it."""
    ns = NAMESPACES[namespace]
    return int(_h(f"{SEED_RULE}|{ns}|{_h('setting:' + str(setting))}|{_h('replicate:' + str(int(replicate)))}")[:32], 16)


def plan_identities(namespace: str, cat: dict | None = None) -> list:
    """The reserved (setting, replicate) identities of a qualification namespace, from the catalogue's attempts."""
    cat = CATALOGUE.data if cat is None else cat
    key = {"calibration": "calibration", "validation": "validation"}[namespace]
    return [(s["id"], r) for s in cat["settings"] for r in range(int(s["attempts"][key]))]


# ----------------------------------------------------------------------------------------------
# the catalogue
# ----------------------------------------------------------------------------------------------
def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def resolved_truth(x: dict) -> dict:
    """The fully resolved generating parameters of one catalogue setting (raw vectors and the base they come from)."""
    gen, p = x["generator"], x["params"]
    if gen.startswith("simulate:"):
        name = gen.split(":", 1)[1]
        return dict(member=name, theta=[float(v) for v in S.generator_theta(name, **p)], base=dict(S.BASE))
    if gen == "lowamp_M2B":
        base = dict(S.BASE, mu_low=p["mu_low"], mu_top=p["mu_top"])
        return dict(member="M2B", theta=[float(v) for v in S.generator_theta("M2B", base=base)], base=base)
    if gen in ("boundary", "nlvar_carrier"):
        return dict(mean_member="M2B", mean_theta=[float(v) for v in S.generator_theta("M2B")], base=dict(S.BASE))
    if gen == "t5_M2H":
        return dict(mean_member="M2H", theta=[float(v) for v in S.generator_theta("M2H", tau=p["tau"])], base=dict(S.BASE))
    if gen == "M3S":
        return dict(member="M3S", theta=[float(v) for v in m3s_theta_from(p["sep"], p["scale"], p["omega"])],
                    params=list(MB.M3S_PARAMS), base=dict(S.BASE))
    raise KeyError(gen)


def build_catalogue() -> dict:
    with open(GAIN_ARTEFACT) as fh:
        gains = json.load(fh)
    scale = {(e["generator"], float(e["target"])): float(e["scale"]) for e in gains["entries"]}
    gsrc = dict(path=os.path.relpath(GAIN_ARTEFACT, T1), sha256=_sha256(GAIN_ARTEFACT), code_hash=gains.get("code_hash"),
                role="starting values only; every gain is re-certified under the frozen implementation (S3)")
    st = []

    def graded(sid, gen, params, origin, note=""):
        st.append(dict(id=sid, kind="graded", generator=gen, params=params, origin=origin, note=note,
                       attempts=dict(development_smoke=COUNTS["development_smoke"], calibration=COUNTS["calibration"],
                                     validation=COUNTS["validation_graded"])))

    graded("G01", "simulate:M2B", {}, "historical")
    for i, t in enumerate(S.GRID["tau"]):
        graded(f"G{2 + i:02d}", "simulate:M2H", dict(tau=t), "historical")
    for i, w in enumerate(S.GRID["omega"]):
        graded(f"G{6 + i:02d}", "simulate:M2S", dict(omega=w), "historical")
    for i, a in enumerate(S.GRID["alpha"]):
        graded(f"G{10 + i:02d}", "simulate:M2K", dict(alpha=a), "historical")
    graded("G13", "lowamp_M2B", dict(mu_low=-0.1, mu_top=0.1), "new",
           "low-amplitude M2B: the historical mu range [-1, +1] shrunk tenfold toward a common constant response")
    graded("G14", "boundary", dict(lam=None, log_sigma0=float(np.log(0.75)), development_placeholder_lam=BOUNDARY_SMOKE_LAMBDA),
           "new", "lambda frozen only after the S3 development search and certification; null means NOT FROZEN")
    graded("G15", "t5_M2H", dict(tau=0.5, df=5), "new", "t(5) innovations standardized to unit variance")
    graded("G16", "nlvar_carrier", dict(sigma_base=0.6, sigma_bump=0.4, bump_centre=3.0, bump_width=1.0,
                                        concept_log_scale=1.0, carrier_sd=0.2, background_sd=0.2), "new",
           "carrier and background SDs are declared development stress values (S3: from CAL or a declared stress value)")
    targets = S.GAINS
    n = 1
    for name in ("M3", "M3H", "M3V", "M3L"):
        for g in targets:
            kw = dict(S.GAIN_KWARGS[name]); kw["scale"] = scale[(name, float(g))]
            st.append(dict(id=f"A{n:02d}", kind="alternative", generator=f"simulate:{name}", params=kw, origin="historical",
                           target_gain=g, gain_certified=False, power_gate=(g == 0.01), note="scale = starting value",
                           attempts=dict(development_smoke=1, calibration=COUNTS["calibration"],
                                         validation=COUNTS["validation_alternative"])))
            n += 1
    for omega in (1.0, 2.0):
        st.append(dict(id=f"A{n:02d}", kind="alternative", generator="M3S",
                       params=dict(omega=omega, sep=2.0, scale=scale[("M3H", 0.01)]), origin="new", target_gain=0.01,
                       gain_certified=False, power_gate=True,
                       note="scale starting value = M3H's 0.01-nat constant; M3S gain not yet certified",
                       attempts=dict(development_smoke=1, calibration=COUNTS["calibration"],
                                     validation=COUNTS["validation_alternative"])))
        n += 1
    for x in st:                                  # resolved truth (N3): every inherited base value materialised
        x["resolved"] = resolved_truth(x)
    return dict(
        about="R052 bounded-comparison qualification catalogue - DRAFT, DEVELOPMENT-ONLY, not adopted, not sealed "
              "(bounded/DESIGN_bounded_v1.md)",
        freeze=dict(development_only=True, boundary_lambda_certificate=None, gain_certificates=None,
                    design_numerical_policy=None, benchmark_admission_receipt=None,
                    note="every field must hold a sealed receipt (path + sha256) and development_only must be false before "
                         "any calibration or validation identity can run (bounded.campaign.require_sealed)"),
        design=dict(concepts=P.N_CONCEPTS, family_counts=list(P.FAMILY_COUNTS), family_weights=[f"{c}/64" for c in P.FAMILY_COUNTS],
                    D=D, carriers=N_CARRIERS, levels=list(M.LEVELS), trials_per_concept=N_CARRIERS * len(M.LEVELS) * D,
                    layer=P.LAYER, n_outer=P.N_OUTER, cap=P.CAP),
        members=dict(G=list(MB.MEMBERS_G), X=list(MB.MEMBERS_X), recipe=MB.recipe_table(), recovery="models.fit S9 chain"),
        namespaces=NAMESPACES, development_namespaces=list(DEVELOPMENT_NAMESPACES),
        seed_rule="int(sha256('bounded-seed-v2|<namespace>|' + sha256('setting:<id>') + '|' + sha256('replicate:<r>'))[:32 hex], 16): 128 bits",
        counts=COUNTS, gain_source=gsrc, settings=st)


class Catalogue:
    """A catalogue frozen from its bytes: the digest and the parsed content come from the same read (B1)."""

    def __init__(self, raw: bytes, path: str | None = None):
        self._raw = bytes(raw)
        self.path = path
        self.sha256 = hashlib.sha256(self._raw).hexdigest()

    @classmethod
    def read(cls, path: str) -> "Catalogue":
        with open(path, "rb") as fh:
            return cls(fh.read(), path)

    @property
    def data(self) -> dict:
        return json.loads(self._raw)                 # a fresh parse of the frozen bytes: callers cannot mutate it

    def setting(self, sid: str) -> dict:
        for s in self.data["settings"]:
            if s["id"] == sid:
                return s
        raise KeyError(sid)


CATALOGUE = Catalogue.read(CATALOGUE_PATH)            # bound at import, used for every point of this process


def load_catalogue() -> dict:
    """The parsed catalogue this process loaded at import (never a re-read of the file)."""
    return CATALOGUE.data


def setting(sid: str) -> dict:
    return CATALOGUE.setting(sid)


# ----------------------------------------------------------------------------------------------
# datasets
# ----------------------------------------------------------------------------------------------
def _labels(size: int = 1) -> np.ndarray:
    return np.repeat(np.arange(len(P.FAMILY_COUNTS)), [c * int(size) for c in P.FAMILY_COUNTS])


def _relabel(ds: "A.Dataset", size: int = 1) -> "A.Dataset":
    ds.family = _labels(size)
    return ds


def _dataset(y, design, meta, size: int = 1) -> "A.Dataset":
    return A.Dataset(np.asarray(y, float)[:, None], design["k"], design["concept"], _labels(size),
                     np.array([P.LAYER]), meta=dict(meta, D=D, carrier=design["carrier"], draw=design["draw"]))


# ----------------------------------------------------------------------------------------------
# the M3S truth adapter (never models.components / models.sample / simulate.*)
# ----------------------------------------------------------------------------------------------
def m3s_components(theta_m3s, k, v=0.0) -> dict:
    """numpy: occupancy A(k) (zero at the catch level), mu_low, mu_high(k) and the per-trial scale sigma e^{v}."""
    mu_low, d0, d1, kA, kh, x0, s, _w = (float(t) for t in np.asarray(theta_m3s, float))
    k = np.asarray(k, float)
    A_ = np.where(k == M.K_CATCH, 0.0, 1.0 / (1.0 + np.exp(-kA * (k - x0))))
    mu_high = mu_low + np.exp(d0) + np.exp(d1) / (1.0 + np.exp(-kh * (k - x0)))
    return dict(A=A_, mu_low=np.full_like(k, mu_low), mu_high=mu_high, sigma=np.exp(s + np.asarray(v, float)) * np.ones_like(k))


def m3s_theta_from(sep: float, scale: float, omega: float) -> np.ndarray:
    """The M3S truth vector at the simulate.BASE mixture base (M3H's ordered core, threshold effect replaced by scale)."""
    th = S.generator_theta("M3H", tau=1.0, sep=sep, scale=scale)
    return MB.m3s_theta(th[0], np.exp(th[1]), np.exp(th[2]), th[3], th[4], th[5], np.exp(th[6]), omega)


def m3s_sample_dataset(theta_m3s, seed: int, size: int = 1, meta: dict | None = None) -> "A.Dataset":
    """M3S data: v_c ~ N(0, omega^2) per concept, then occupancy, then trial noise, from ONE stream."""
    rng = np.random.default_rng(int(seed))
    d = S.make_design(8 * int(size), N_CARRIERS, D)
    k = d["k"]
    omega = float(np.exp(theta_m3s[7]))
    v_c = rng.normal(0.0, omega, size=d["C"])
    unif = rng.uniform(size=k.size)
    eps = rng.normal(size=k.size)
    c = m3s_components(theta_m3s, k, v_c[d["concept"]])
    mu = np.where(unif < c["A"], c["mu_high"], c["mu_low"])
    y = mu + c["sigma"] * eps
    return _dataset(y, d, dict(meta or {}, generator="M3S", seed=int(seed), v_c=v_c,
                               theta_m3s=[float(t) for t in theta_m3s]), size)


def m3s_truth_logq(theta_m3s, data: "M.Trials") -> np.ndarray:
    """The TRUE joint MARGINAL concept log density of M3S (integrated over v; never conditioned on the realised v_c)."""
    return M.concept_scores("M3S", np.asarray(theta_m3s, float), data)


def _m2b_mu(theta, k, u=0.0):
    return M.components("M2H", np.append(theta[:6], 0.0), k, u=u)["mu"]


def make(s: dict, seed: int, lam: float | None = None, size: int = 1) -> "A.Dataset":
    """The dataset of catalogue setting `s` at dataset seed `seed` (one layer, three strata). `lam` supplies the boundary
    lambda when the catalogue's is not frozen (development only). `size` multiplies the concept count (64 x size, strata
    27/22/15 x size) for development reference banks only; every point of the procedure uses size 1."""
    gen, p = s["generator"], s["params"]
    npf = 8 * int(size)
    if gen.startswith("simulate:"):
        name = gen.split(":", 1)[1]
        ds = S.make_dataset(name, S.generator_theta(name, **p), n_per_family=npf, D=D, layers=(P.LAYER,), seed=int(seed))
        return _relabel(ds, size)
    if gen == "lowamp_M2B":
        base = dict(S.BASE, mu_low=p["mu_low"], mu_top=p["mu_top"])
        th = S.generator_theta("M2B", base=base)
        ds = S.make_dataset("M2B", th, n_per_family=npf, D=D, layers=(P.LAYER,), seed=int(seed))
        ds.meta["base"] = base
        return _relabel(ds, size)
    if gen == "M3S":
        return m3s_sample_dataset(m3s_theta_from(p["sep"], p["scale"], p["omega"]), seed, size,
                                  dict(omega=p["omega"], sep=p["sep"], scale=p["scale"]))
    rng = np.random.default_rng(int(seed))
    d = S.make_design(npf, N_CARRIERS, D)
    k = d["k"]
    th_b = S.generator_theta("M2B")
    if gen == "boundary":
        lam = p["lam"] if p["lam"] is not None else lam
        if lam is None:
            raise ValueError("boundary lambda is not frozen: pass a declared development value")
        mu = _m2b_mu(th_b, k)
        sigma = np.exp(p["log_sigma0"] + float(lam) * np.sin(np.pi * k / 8.0) ** 2)
        y = mu + sigma * rng.normal(size=k.size)
        return _dataset(y, d, dict(generator="boundary", lam=float(lam), seed=int(seed)), size)
    if gen == "t5_M2H":
        th = S.generator_theta("M2H", tau=p["tau"])
        u_c = rng.normal(0.0, p["tau"], size=d["C"])
        c = M.components("M2H", th, k, u=u_c[d["concept"]])
        df = float(p["df"])
        eps = rng.standard_t(df, size=k.size) * np.sqrt((df - 2.0) / df)
        y = c["mu"] + c["sigma"] * eps
        return _dataset(y, d, dict(generator="t5_M2H", tau=p["tau"], df=df, seed=int(seed), u_c=u_c), size)
    if gen == "nlvar_carrier":
        v_c = rng.normal(0.0, p["concept_log_scale"], size=d["C"])
        g_r = rng.normal(0.0, p["carrier_sd"], size=N_CARRIERS)
        b = rng.normal(0.0, p["background_sd"], size=(d["C"], N_CARRIERS, D))
        eps = rng.normal(size=k.size)
        mu = _m2b_mu(th_b, k)
        sigma = (p["sigma_base"] + p["sigma_bump"] * np.exp(-0.5 * ((k - p["bump_centre"]) / p["bump_width"]) ** 2)) \
            * np.exp(v_c[d["concept"]])
        y = mu + g_r[d["carrier"]] + b[d["concept"], d["carrier"], d["draw"]] * (8.0 - k) / 8.0 + sigma * eps
        return _dataset(y, d, dict(generator="nlvar_carrier", seed=int(seed), v_c=v_c, carrier_effects=g_r), size)
    raise KeyError(gen)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="regenerate catalogue.json from build_catalogue()")
    a = ap.parse_args()
    cat = build_catalogue()
    text = json.dumps(cat, indent=1, sort_keys=True) + "\n"
    if a.write:
        with open(CATALOGUE_PATH, "w") as fh:
            fh.write(text)
        print(f"wrote {CATALOGUE_PATH}: {len(cat['settings'])} settings")
    else:
        print(text)


if __name__ == "__main__":
    main()
