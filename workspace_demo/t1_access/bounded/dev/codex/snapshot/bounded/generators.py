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

Seeds: dataset_seed(namespace, setting, replicate) = default_rng([namespace, H(setting), H(replicate)]).integers(2^31),
H = first 32 bits of SHA-256 of "setting:<id>" / "replicate:<r>" (the two tags hashed separately), namespaces
development 271100, calibration 271200, validation 271300.

`python -m bounded.generators --write` regenerates catalogue.json from build_catalogue(); every dataset is built from
the catalogue file (the configuration hash covers it).
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

CATALOGUE_PATH = os.path.join(HERE, "catalogue.json")
NAMESPACES = {"development": 271100, "calibration": 271200, "validation": 271300}
GAIN_ARTEFACT = os.path.join(T1, "sim_results", "gain_sens600", "gain_calibration_D4.json")
D = 4
N_CARRIERS = 6
BOUNDARY_SMOKE_LAMBDA = 0.5          # development placeholder for the smoke run only; never a frozen value
COUNTS = dict(development_smoke=1, calibration=500, validation_graded=400, validation_alternative=1000)


def _tag(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


def dataset_seed(namespace: str, setting: str, replicate: int) -> int:
    ns = NAMESPACES[namespace]
    return int(np.random.default_rng([ns, _tag(f"setting:{setting}"), _tag(f"replicate:{int(replicate)}")]).integers(2**31))


# ----------------------------------------------------------------------------------------------
# the catalogue
# ----------------------------------------------------------------------------------------------
def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


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
    return dict(
        about="R052 bounded-comparison qualification catalogue - DRAFT, not adopted (bounded/DESIGN_bounded_v1.md)",
        design=dict(concepts=P.N_CONCEPTS, family_counts=list(P.FAMILY_COUNTS), family_weights=[f"{c}/64" for c in P.FAMILY_COUNTS],
                    D=D, carriers=N_CARRIERS, levels=list(M.LEVELS), trials_per_concept=N_CARRIERS * len(M.LEVELS) * D,
                    layer=P.LAYER, n_outer=P.N_OUTER, cap=P.CAP),
        members=dict(G=list(MB.MEMBERS_G), X=list(MB.MEMBERS_X), recipe=MB.recipe_table(), recovery="models.fit S9 chain"),
        namespaces=NAMESPACES, seed_rule="default_rng([namespace, sha256('setting:<id>')[:8], sha256('replicate:<r>')[:8]]).integers(2**31)",
        counts=COUNTS, gain_source=gsrc, settings=st)


def load_catalogue(path: str = CATALOGUE_PATH) -> dict:
    with open(path) as fh:
        return json.load(fh)


def setting(sid: str, cat: dict | None = None) -> dict:
    cat = load_catalogue() if cat is None else cat
    for s in cat["settings"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


# ----------------------------------------------------------------------------------------------
# datasets
# ----------------------------------------------------------------------------------------------
def _relabel(ds: "A.Dataset") -> "A.Dataset":
    ds.family = P.family_labels()
    return ds


def _dataset(y, design, meta) -> "A.Dataset":
    return A.Dataset(np.asarray(y, float)[:, None], design["k"], design["concept"], P.family_labels(),
                     np.array([P.LAYER]), meta=dict(meta, D=D, carrier=design["carrier"], draw=design["draw"]))


def _m2b_mu(theta, k, u=0.0):
    return M.components("M2H", np.append(theta[:6], 0.0), k, u=u)["mu"]


def make(s: dict, seed: int, lam: float | None = None) -> "A.Dataset":
    """The dataset of catalogue setting `s` at dataset seed `seed` (one layer, three strata). `lam` supplies the boundary
    lambda when the catalogue's is not frozen (development only)."""
    gen, p = s["generator"], s["params"]
    if gen.startswith("simulate:"):
        name = gen.split(":", 1)[1]
        ds = S.make_dataset(name, S.generator_theta(name, **p), n_per_family=8, D=D, layers=(P.LAYER,), seed=int(seed))
        return _relabel(ds)
    if gen == "lowamp_M2B":
        base = dict(S.BASE, mu_low=p["mu_low"], mu_top=p["mu_top"])
        th = S.generator_theta("M2B", base=base)
        ds = S.make_dataset("M2B", th, n_per_family=8, D=D, layers=(P.LAYER,), seed=int(seed))
        ds.meta["base"] = base
        return _relabel(ds)
    rng = np.random.default_rng(int(seed))
    d = S.make_design(8, N_CARRIERS, D)
    k = d["k"]
    th_b = S.generator_theta("M2B")
    if gen == "boundary":
        lam = p["lam"] if p["lam"] is not None else lam
        if lam is None:
            raise ValueError("boundary lambda is not frozen: pass a declared development value")
        mu = _m2b_mu(th_b, k)
        sigma = np.exp(p["log_sigma0"] + float(lam) * np.sin(np.pi * k / 8.0) ** 2)
        y = mu + sigma * rng.normal(size=k.size)
        return _dataset(y, d, dict(generator="boundary", lam=float(lam), seed=int(seed)))
    if gen == "t5_M2H":
        th = S.generator_theta("M2H", tau=p["tau"])
        u_c = rng.normal(0.0, p["tau"], size=d["C"])
        c = M.components("M2H", th, k, u=u_c[d["concept"]])
        df = float(p["df"])
        eps = rng.standard_t(df, size=k.size) * np.sqrt((df - 2.0) / df)
        y = c["mu"] + c["sigma"] * eps
        return _dataset(y, d, dict(generator="t5_M2H", tau=p["tau"], df=df, seed=int(seed), u_c=u_c))
    if gen == "nlvar_carrier":
        v_c = rng.normal(0.0, p["concept_log_scale"], size=d["C"])
        g_r = rng.normal(0.0, p["carrier_sd"], size=N_CARRIERS)
        b = rng.normal(0.0, p["background_sd"], size=(d["C"], N_CARRIERS, D))
        eps = rng.normal(size=k.size)
        mu = _m2b_mu(th_b, k)
        sigma = (p["sigma_base"] + p["sigma_bump"] * np.exp(-0.5 * ((k - p["bump_centre"]) / p["bump_width"]) ** 2)) \
            * np.exp(v_c[d["concept"]])
        y = mu + g_r[d["carrier"]] + b[d["concept"], d["carrier"], d["draw"]] * (8.0 - k) / 8.0 + sigma * eps
        return _dataset(y, d, dict(generator="nlvar_carrier", seed=int(seed), v_c=v_c, carrier_effects=g_r))
    if gen == "M3S":
        th = S.generator_theta("M3H", tau=1.0, sep=p["sep"], scale=p["scale"])
        v_c = rng.normal(0.0, p["omega"], size=d["C"])
        unif = rng.uniform(size=k.size)
        eps = rng.normal(size=k.size)
        c = M.components("M3H", th, k, u=0.0)
        high = unif < c["A"]                                  # A = 0 at the catch level
        mu = np.where(high, c["mu_high"], c["mu_low"])
        y = mu + c["sigma_low"] * np.exp(v_c[d["concept"]]) * eps
        return _dataset(y, d, dict(generator="M3S", omega=p["omega"], sep=p["sep"], scale=p["scale"], seed=int(seed),
                                   v_c=v_c, theta_m3s=MB.m3s_theta(th[0], np.exp(th[1]), np.exp(th[2]), th[3], th[4], th[5],
                                                                   np.exp(th[6]), p["omega"]).tolist()))
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
