#!/usr/bin/env python3
"""Phase 1 of the Melcón v7 development plan — DEVPLAN_v7.md rev 1 §2.2 (logging-only re-runs of the 40 panel recordings
with exact v6 parity), §2.3 (the idealized readout, 272 recordings) and §2.5 (benchmark first, pause past 4 wall-hours).
Development only: no EEG, no group rule, no candidate, nothing frozen. No v6 file is edited and nothing is added to the
fitting.

Instrumentation, inside this process and its joblib workers only (install()):
  likelihood._run         a wrapper that calls the UNMODIFIED v6 _run and logs its result per start;
  likelihood.minimize     a pass-through that records nfev, status and message of the L-BFGS-B call it forwards;
  likelihood.fit          a wrapper that logs the seed tuple, the starts in order, the kept start and n_at_best;
  likelihood.fold_scores  a wrapper that logs scaling, dose support and per-trial predictions after the fold is scored.
Every fit therefore runs v6's objective, bounds, starts and L-BFGS-B options unchanged (the plan's "instrumented copy" is
met by calling the original rather than copying it); the wrappers read results after the fact and draw no random number.

Logged per start: order, retry flag, x0, theta, training log-likelihood (full precision), success, convergence, projected
gradient, nit, nfev, message, elapsed seconds, and per parameter the bounds, the absolute distance to the nearer bound and
the normalized position (x - lo) / (hi - lo). Per fit: seed tuples, availability and reason, kept start (first in order
among exact ties), n_at_best. Per fold and model, at every training and test trial: the conditional mean and SD (null:
mu0 + beta h and sigma0; graded: a0 + a1 L + beta h and exp(s0 + r L); two-state: mixing weight A, both component means,
component SD and the marginal mean and SD, with A = 0 and the high mean equal to the low one on catch trials, as in the
density) and the per-trial log-likelihood; per fold the training present-dose range and each test present trial labelled
below, within or above it.

Parity (panel): each re-run's battery.summary must equal the stored v6 result exactly in status, windows, models, evidence,
available, delta, n_trials, auc and the summary medians. The first selected recording is checked alone (--first) and any
difference stops Phase 1; all 40 are checked by --run and reported.

Idealized readout: the stochastic latent z_true that synthetic.generate stores for the same template, generator, drift and
tags (intrinsic noise, hemifield shift and drift; no decoder, no sensors; amplitude-independent), computed by
latent_only() and checked equal to generate on one recording per generator. G1, G2, G3, X1 x both drifts x 34 templates;
data tags (9, generator index, 0, drift index, 0, subject); the four block folds of recording.recording_scores on the
§2-retained trials, optimizer tags (subject, task index, half, fold, 99). True occupancy and component labels are stored as
diagnostic outputs only. Per recording only; no group rule.

Archive: results/devpanel_v7/run-<digest>/ with identity.json (SHA-256 of every loaded melcon_port module including this
wrapper, runtime, parent identity, panel manifest SHA-256, schema); each output has a sidecar (payload SHA-256, identity,
schema, key); reload verifies all of them and a mismatch is refused.

Usage (repo-root venv):  ../../.venv/bin/python devpanel_v7.py --self-test | --first | --run [--n-jobs 2] | --report
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ[_v] = "1"                                                   # before numpy; inherited by the joblib workers

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402

import numpy as np  # noqa: E402
from scipy.special import expit  # noqa: E402
from scipy.stats import norm  # noqa: E402

import battery as BT  # noqa: E402
import decoder as DEC  # noqa: E402
import inclusion as INC  # noqa: E402
import likelihood as LK  # noqa: E402
import recording as RC  # noqa: E402
import synthetic as SY  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "melcon-devpanel-v7-phase1-r1"
PLAN = "DEVPLAN_v7.md rev 1 §2.2-§2.5 (RSC 9cbcc0a)"
BASE = os.path.join(HERE, "results", "devpanel_v7")
PANEL_MANIFEST = os.path.join(BASE, "panel_manifest.json")
IDEAL_GENERATORS = ("G1", "G2", "G3", "X1")
IDEAL_PHASE = 9
IDEAL_WINDOW_TAG = 99
PAUSE_WALL_HOURS = 4.0
PARITY_KEYS = ("status", "windows", "models", "evidence", "available", "delta", "n_trials", "auc", "twostate_min_gap_median",
               "twostate_full_gap_median", "occupancy_abs_error_median", "readout_highlow_contrast_unadjusted_median",
               "readout_latent_corr_median")


def _sha_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _loaded_modules() -> dict:
    out = {}
    for mod in list(sys.modules.values()):
        f = getattr(mod, "__file__", None)
        if f and f.endswith(".py") and os.path.dirname(os.path.abspath(f)) == HERE:
            out[os.path.basename(f)] = _sha_file(os.path.abspath(f))
    return dict(sorted(out.items()))


LOADED = _loaded_modules()                                                  # read at import, re-verified before every output


# ------------------------------------------------------------------------------------------------------------ identity
def load_panel() -> dict:
    with open(PANEL_MANIFEST) as fh:
        return json.load(fh)


def identity() -> dict:
    pm = load_panel()
    return dict(schema=SCHEMA, plan=PLAN, modules=LOADED, runtime=BT.runtime(), parent_namespace=pm["parent_namespace"],
                parent_identity=pm["parent_identity"], panel_manifest_sha256=_sha_file(PANEL_MANIFEST), likelihood=LK.SPEC,
                ideal=dict(generators=IDEAL_GENERATORS, data_tags=f"({IDEAL_PHASE}, generator index, 0, drift index, 0, subject)",
                           optimizer_tags=f"(subject, task index, half, fold, {IDEAL_WINDOW_TAG})"),
                pause_wall_hours=PAUSE_WALL_HOURS)


def run_directory(ident: dict) -> str:
    ident = BT._jsonable(ident)
    d = os.path.join(BASE, f"run-{BT.digest(ident)[:12]}")
    for sub in ("panel", "ideal"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    path = os.path.join(d, "identity.json")
    if os.path.exists(path):
        with open(path) as fh:
            if json.load(fh) != ident:
                raise RuntimeError(f"{path}: identity differs from the running configuration")
    else:
        with open(path, "w") as fh:
            json.dump(ident, fh, indent=2)
    return d


def verify(d: str) -> str:
    """Refuse a loaded module changed on disk since import, or a process whose identity differs from the archive's."""
    changed = [f for f, h in LOADED.items() if _sha_file(os.path.join(HERE, f)) != h]
    if changed:
        raise RuntimeError(f"changed on disk since this process imported them: {changed}")
    ident = BT._jsonable(identity())
    with open(os.path.join(d, "identity.json")) as fh:
        saved = json.load(fh)
    if saved != ident:
        raise RuntimeError(f"identity differs from {d} in {sorted(k for k in set(saved) | set(ident) if saved.get(k) != ident.get(k))}")
    return BT.digest(ident)


def write_output(path: str, out: dict, key: str, ident: str) -> None:
    buf = io.BytesIO()
    np.save(buf, np.array([out], dtype=object), allow_pickle=True)
    data = buf.getvalue()
    side = dict(sha256=hashlib.sha256(data).hexdigest(), identity=ident, schema=SCHEMA, key=key)
    for p, payload in ((path, data), (path + ".sha256", json.dumps(side).encode())):
        with open(p + ".tmp", "wb") as fh:
            fh.write(payload)
        os.replace(p + ".tmp", p)


def load_output(path: str, key: str, ident: str) -> dict:
    with open(path, "rb") as fh:
        data = fh.read()
    with open(path + ".sha256") as fh:
        side = json.load(fh)
    if hashlib.sha256(data).hexdigest() != side.get("sha256"):
        raise RuntimeError(f"{path}: payload SHA-256 differs from its sidecar")
    if side.get("identity") != ident or side.get("schema") != SCHEMA or side.get("key") != key:
        raise RuntimeError(f"{path}: sidecar names another identity, schema or key; refused")
    out = np.load(io.BytesIO(data), allow_pickle=True)[0]
    if out.get("identity") != ident or out.get("key") != key:
        raise RuntimeError(f"{path}: payload names another identity or key; refused")
    return out


# ------------------------------------------------------------------------------------------------------ instrumentation
_ORIG = dict(run=LK._run, fit=LK.fit, fold_scores=LK.fold_scores, minimize=LK.minimize)
_STATE: dict = dict(min=None, starts=None, fits=[], folds={})


def _reset_state() -> None:
    _STATE.update(min=None, starts=None, fits=[], folds={})


def _minimize_logged(fun, x0, *args, **kwargs):
    t0 = time.perf_counter()
    res = _ORIG["minimize"](fun, x0, *args, **kwargs)
    _STATE["min"] = dict(nfev=int(res.nfev), status=int(res.status), message=str(res.message), minimize_s=time.perf_counter() - t0)
    return res


def _run_logged(model, d, b, x0):
    _STATE["min"] = None
    t0 = time.perf_counter()
    out = _ORIG["run"](model, d, b, x0)
    elapsed = time.perf_counter() - t0
    starts = _STATE["starts"]
    if starts is not None:
        m = _STATE["min"] or {}
        lo, hi = b[:, 0].copy(), b[:, 1].copy()
        th = np.array(out["theta"], dtype=float)
        k = len(starts)
        starts.append(dict(order=k, retry=bool(k >= 1 + LK.N_JITTER), x0=np.array(x0, dtype=float), theta=th,
                           loglik=float(out["loglik"]), success=bool(out["success"]), converged=bool(out["converged"]),
                           pg=float(out["pg"]), nit=int(out["nit"]), nfev=m.get("nfev"), lbfgsb_status=m.get("status"),
                           message=m.get("message"), elapsed_s=elapsed, lo=lo, hi=hi, dist_to_bound=np.minimum(th - lo, hi - th),
                           normalized=(th - lo) / (hi - lo)))
    return out


def _fit_logged(model, d, sc, tags=()):
    _STATE["starts"] = []
    try:
        r = _ORIG["fit"](model, d, sc, tags)
    finally:
        starts, _STATE["starts"] = _STATE["starts"], None
    tg = [int(t) for t in tags]
    if len(starts) != r["n_starts"]:
        raise RuntimeError(f"logged {len(starts)} starts for a fit of {r['n_starts']}")
    rec = dict(model=model, tags=tg, seed=[LK.SEED, *tg, LK.MODEL_INDEX[model]], retry_seed=[LK.SEED, *tg, LK.MODEL_INDEX[model], 1],
               available=bool(r["available"]), reason=r["reason"], n_starts=int(r["n_starts"]), n_converged=int(r["n_converged"]),
               retry=bool(r["retry"]), n_at_best=r.get("n_at_best"), kept_start=None, n_exact_ties_at_best=0, starts=starts)
    if r["available"]:
        kept = [s["order"] for s in starts if s["converged"] and s["loglik"] == r["loglik"]]
        if not kept or not np.array_equal(starts[kept[0]]["theta"], np.asarray(r["theta"], dtype=float)):
            raise RuntimeError("the logged starts do not reproduce the kept solution")
        rec.update(kept_start=kept[0], n_exact_ties_at_best=len(kept))
    _STATE["fits"].append(rec)
    return r


def predict(model: str, theta, d: dict) -> dict:
    """Per-trial conditional moments of a fitted density on a design (see the module docstring)."""
    th = np.asarray(theta, dtype=float)
    x, c, h = d["x"], d["c"], d["h"]
    if model == "null":
        mu0, ls, beta = th
        return dict(mean=mu0 + beta * h, sd=np.full(x.size, math.exp(ls)))
    if model == "graded":
        a0, a1, x0, lk, s0, r, beta = th
        L = np.where(c, 0.0, expit(math.exp(lk) * (x - x0)))
        return dict(mean=a0 + a1 * L + beta * h, sd=np.exp(s0 + r * L), L=L)
    if model == "twostate":
        mu_l, ls, d0, d1, x0, lka, lkh, beta = th[:8]
        A = np.where(c, 0.0, expit(math.exp(lka) * (x - x0)))
        H = np.where(c, 0.0, expit(math.exp(lkh) * (x - x0)))
        low = mu_l + beta * h
        high = np.where(c, low, mu_l + math.exp(d0) + math.exp(d1) * H + beta * h)
        sig = math.exp(ls)
        return dict(mean=(1.0 - A) * low + A * high, sd=np.sqrt(sig * sig + A * (1.0 - A) * (high - low) ** 2), A=A, H=H,
                    mean_low=low, mean_high=high, component_sd=np.full(x.size, sig))
    raise ValueError(f"no prediction for {model!r}")


def _design_arrays(d: dict) -> dict:
    return dict(y=np.asarray(d["y"], float), x=np.asarray(d["x"], float), catch=np.asarray(d["c"], bool), h=np.asarray(d["h"], float))


def _fold_logged(train, test, tags=(), models=LK.PRIMARY):
    n0 = len(_STATE["fits"])
    out = _ORIG["fold_scores"](train, test, tags=tags, models=models)
    fits = _STATE["fits"][n0:]
    key = tuple(int(t) for t in tags)
    sc = LK.scaling(train)
    rec = dict(tags=list(key), n_train=len(train), n_test=len(test), models={})
    if isinstance(sc, str):
        rec.update(scaling=None, unavailable_reason=sc)
    else:
        dtr, dte = LK.design(train, sc), LK.design(test, sc)
        xp = dtr["x"][~dtr["c"]]
        lo, hi = float(xp.min()), float(xp.max())
        pres = ~dte["c"]
        label = np.full(len(test), "catch", dtype=object)
        label[pres & (dte["x"] < lo)] = "below"
        label[pres & (dte["x"] >= lo) & (dte["x"] <= hi)] = "within"
        label[pres & (dte["x"] > hi)] = "above"
        rec.update(scaling=dict(sc), unavailable_reason=None, train=_design_arrays(dtr), test=_design_arrays(dte),
                   dose_support=dict(train_present_min=lo, train_present_max=hi, test_label=label,
                                     n_below=int((label == "below").sum()), n_within=int((label == "within").sum()),
                                     n_above=int((label == "above").sum())))
        for m in models:
            s = out[m]
            mr = dict(available=bool(s["available"]), reason=s["reason"], fit_logged=any(f["model"] == m for f in fits))
            if "theta" in s:
                th = np.asarray(s["theta"], dtype=float)
                mr.update(theta=th, loglik_train=float(s["loglik"]), heldout=s.get("heldout"),
                          train=predict(m, th, dtr), test=predict(m, th, dte),
                          train_ll=LK.loglik(m, th, dtr), test_ll=LK.loglik(m, th, dte))
            rec["models"][m] = mr
    for m in models:
        rec["models"].setdefault(m, dict(available=bool(out[m]["available"]), reason=out[m]["reason"], fit_logged=False))
    _STATE["folds"][key] = rec
    return out


def install() -> None:
    if LK._run is not _run_logged:
        LK._run, LK.fit, LK.fold_scores, LK.minimize = _run_logged, _fit_logged, _fold_logged, _minimize_logged


# ---------------------------------------------------------------------------------------------------------------- panel
def _same(a, b) -> bool:
    if isinstance(a, (list, tuple, np.ndarray)) or isinstance(b, (list, tuple, np.ndarray)):
        A, B = np.asarray(a), np.asarray(b)
        if A.shape != B.shape:
            return False
        if A.dtype.kind in "fc" and B.dtype.kind in "fc":
            return bool(np.array_equal(A, B, equal_nan=True))
        return bool(np.array_equal(A, B))
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return bool(a == b)


def parity(summary: dict, parent: dict) -> dict:
    diff = [k for k in PARITY_KEYS if (k in summary) != (k in parent) or (k in summary and not _same(summary[k], parent[k]))]
    return dict(equal=not diff, differing=diff, keys=list(PARITY_KEYS))


def panel_key(e: dict) -> str:
    return f"{e['generator']}_{e['strength']}_d{e['drift_index']}_r{e['replicate']}_sub-{e['subject']:02d}"


def run_panel(index: int, d: str) -> dict:
    install()
    ident = verify(d)
    e = load_panel()["panel"][index]
    key = panel_key(e)
    path = os.path.join(d, "panel", key + ".npy")
    if os.path.exists(path) or os.path.exists(path + ".sha256"):
        out = load_output(path, key, ident)
        return dict(index=index, key=key, role=e["role"], parity=out["parity"], timing=out["timing"], reused=True)
    parent_path = os.path.join(HERE, e["path"])
    man = e["parent_recording_manifest"]
    parent = BT.load_verified(parent_path, man)
    if _sha_file(parent_path + ".sha256") != e["parent_sidecar_file_sha256"]:
        raise RuntimeError(f"{parent_path}: sidecar differs from the panel manifest")
    _reset_state()
    t0 = time.perf_counter()
    rec = SY.generate(SY.template(man["subject"], "nocue"), man["generator"], man["amplitude"], man["drift"], tags=tuple(man["tags"]))
    t1 = time.perf_counter()
    res = RC.recording_scores(rec, man["subject"], "nocue")
    t2 = time.perf_counter()
    summ = BT.summary(res) if res["status"] == "ok" else {k: res[k] for k in ("status", "subject", "task")}
    par = parity(summ, parent)
    dec = None
    if res["status"] == "ok":
        dec = {str(B): dict(decoder_half=h["decoder_half"], W=h["W"], auc=h["auc"], trials=h["trials"])
               for B, h in res["decoder"]["halves"].items()}
    out = dict(kind="panel", schema=SCHEMA, identity=ident, key=key, index=index, entry=e, status=res["status"],
               traceback=res.get("traceback"), summary=summ, parity=par, reasons=res.get("reasons"), fits=_STATE["fits"],
               folds=_STATE["folds"], decoder=dec, timing=dict(generate_s=t1 - t0, scores_s=t2 - t1, total_s=t2 - t0),
               n_fits=len(_STATE["fits"]), n_starts=sum(f["n_starts"] for f in _STATE["fits"]), pid=os.getpid(),
               peak_rss_mb=BT._peak_rss_mb(), created_utc=_now())
    write_output(path, out, key, ident)
    _reset_state()
    return dict(index=index, key=key, role=e["role"], parity=par, timing=out["timing"], reused=False)


# ------------------------------------------------------------------------------------------------------- idealized readout
def ideal_tags(generator: str, drift_index: int, subject: int) -> tuple:
    return (IDEAL_PHASE, SY.GENERATORS.index(generator), 0, int(drift_index), 0, int(subject))


def latent_only(tmpl, generator: str, drift: bool, tags=()) -> dict:
    """The first part of synthetic.generate, statement for statement (the same random stream up to z): the trial table with
    z_true, occupancy_true and high_true, and the flags generate sets. No sensor sample, no amplitude."""
    rng = np.random.default_rng(np.random.SeedSequence([SY.SEED, *[int(t) for t in tags]]))
    trials = tmpl.reset_index(drop=True).copy()
    catch = trials["catch"].to_numpy(bool)
    right = (trials["side"].to_numpy() == "right") & ~catch
    lc = np.log(np.where(catch, 1.0, trials["contrast"].to_numpy(float)))
    x = np.where(catch, 0.0, (lc - lc[~catch].mean()) / lc[~catch].std(ddof=1))
    z, L, high = SY.latent(generator, x, catch, rng)
    z = z + SY.HEMI_SHIFT * right
    if drift:
        z = z + SY.DRIFT_PER_BLOCK * (trials["block"].to_numpy(float) - 1.0)
    trials["has_epoch"] = True
    trials["epoch_index"] = np.arange(len(trials))
    trials["retained"] = True
    trials["reject_reason"] = ""
    trials["edge_trial"] = False
    trials["z_true"] = z
    trials["occupancy_true"] = L
    trials["high_true"] = high
    return dict(trials=trials, generator=generator, drift=bool(drift), tags=tuple(tags))


def check_latent_path(generator: str, subject: int) -> dict:
    """latent_only against generate on one recording (drift on, amplitude 1): z_true, occupancy_true, high_true equal."""
    tags = ideal_tags(generator, 1, subject)
    tmpl = SY.template(subject, "nocue")
    light = latent_only(tmpl, generator, True, tags)["trials"]
    full = SY.generate(tmpl, generator, 1.0, True, tags=tags)["trials"]
    eq = {c: bool(np.array_equal(light[c].to_numpy(), full[c].to_numpy())) for c in ("z_true", "occupancy_true", "high_true")}
    return dict(generator=generator, subject=int(subject), tags=list(tags), equal=all(eq.values()), columns=eq)


def ideal_scores(light: dict, subject: int, task: str = "nocue") -> dict:
    """recording.recording_scores' four block folds with y = z_true on the §2-retained trials (one pseudo-window)."""
    gate = INC.section2(light)
    if not gate["passed"]:
        return dict(status="excluded: " + "; ".join(gate["reasons"]), section2=INC.report(gate))
    tr = INC.apply(light, gate)["trials"]
    rows = tr[tr["retained"].to_numpy(bool) & tr["has_epoch"].to_numpy(bool)]
    models = LK.PRIMARY
    held, avail, n_trials = np.zeros(len(models)), np.ones(len(models), dtype=bool), 0
    reasons = [set() for _ in models]
    for hi, B in enumerate(sorted(DEC.HALVES)):
        t = rows[rows.block.isin(B)].reset_index(drop=True)
        catch = t["catch"].to_numpy(bool)
        right = (t["side"].to_numpy() == "right") & ~catch
        logc = np.where(catch, np.nan, np.log(np.where(catch, 1.0, t["contrast"].to_numpy(float))))
        blk, y = t["block"].to_numpy(), t["z_true"].to_numpy(float)
        for fi, (b_tr, b_te) in enumerate(((B[0], B[1]), (B[1], B[0]))):
            mtr, mte = blk == b_tr, blk == b_te
            s = LK.fold_scores(LK.Block(y[mtr], logc[mtr], catch[mtr], right[mtr]), LK.Block(y[mte], logc[mte], catch[mte], right[mte]),
                               tags=(subject, RC.TASK_INDEX[task], hi, fi, IDEAL_WINDOW_TAG), models=models)
            n_trials += int(mte.sum())
            for mi, m in enumerate(models):
                if s[m]["available"]:
                    held[mi] += s[m]["heldout"]
                else:
                    avail[mi] = False
                    reasons[mi].add(s[m]["reason"])
    i2, i3 = models.index("graded"), models.index("twostate")
    return dict(status="ok", section2=INC.report(gate), models=list(models), evidence=np.where(avail, held / 4.0, np.nan),
                available=avail, n_trials=n_trials, reasons=[sorted(r) for r in reasons],
                delta=float((held[i3] - held[i2]) / max(n_trials, 1)) if avail[i2] and avail[i3] else float("nan"),
                truth=rows[["block", "catch", "side", "contrast", "z_true", "occupancy_true", "high_true"]].reset_index(drop=True))


def ideal_key(generator: str, drift_index: int, subject: int) -> str:
    return f"{generator}_d{drift_index}_sub-{subject:02d}"


def run_ideal(generator: str, drift_index: int, subject: int, d: str) -> dict:
    install()
    ident = verify(d)
    key = ideal_key(generator, drift_index, subject)
    path = os.path.join(d, "ideal", key + ".npy")
    if os.path.exists(path) or os.path.exists(path + ".sha256"):
        out = load_output(path, key, ident)
        return dict(key=key, status=out["status"], timing=out["timing"], reused=True)
    _reset_state()
    tags = ideal_tags(generator, drift_index, subject)
    t0 = time.perf_counter()
    try:
        light = latent_only(SY.template(subject, "nocue"), generator, bool(BT.DRIFTS[drift_index]), tags)
        res = ideal_scores(light, subject)
    except Exception as ex:                                               # recorded, never dropped
        res = dict(status=f"technical failure: {type(ex).__name__}: {ex}", traceback=traceback.format_exc())
    t1 = time.perf_counter()
    out = dict(kind="ideal", schema=SCHEMA, identity=ident, key=key, generator=generator, drift_index=int(drift_index),
               subject=int(subject), data_tags=list(tags), **res, fits=_STATE["fits"], folds=_STATE["folds"],
               timing=dict(total_s=t1 - t0), n_fits=len(_STATE["fits"]), n_starts=sum(f["n_starts"] for f in _STATE["fits"]),
               pid=os.getpid(), created_utc=_now())
    write_output(path, out, key, ident)
    _reset_state()
    return dict(key=key, status=out["status"], timing=out["timing"], reused=False)


# ------------------------------------------------------------------------------------------------------------ self-test
def self_test() -> None:
    """predict() against likelihood.loglik on random designs: the moments must reproduce the density per trial."""
    rng = np.random.default_rng(7)
    n = 400
    c = rng.random(n) < 0.15
    x = np.where(c, 0.0, rng.normal(size=n))
    h = ((rng.random(n) < 0.5) & ~c).astype(float)
    y = rng.normal(size=n)
    d = dict(y=y, x=x, c=c, h=h)
    for m, th in (("null", [0.1, -0.3, 0.2]), ("graded", [0.2, 1.3, 0.4, 0.7, -0.5, -1.9, 0.1]),
                  ("twostate", [-0.2, -0.4, 0.3, -0.1, 0.2, 1.1, 0.4, 0.15])):
        p = predict(m, th, d)
        ll = LK.loglik(m, th, d)
        if m == "twostate":
            s = p["component_sd"]
            mix = np.logaddexp(np.log1p(-p["A"]) + norm.logpdf(y, p["mean_low"], s),
                               np.log(np.maximum(p["A"], 1e-300)) + norm.logpdf(y, p["mean_high"], s))
            ref = np.where(c, norm.logpdf(y, p["mean_low"], s), mix)
        else:
            ref = norm.logpdf(y, p["mean"], p["sd"])
        err = float(np.max(np.abs(ref - ll)))
        assert err < 1e-9, (m, err)
    three = dict(y=np.zeros(3), x=np.array([-1.0, 0.0, 2.0]), c=np.array([False, True, False]), h=np.zeros(3))
    p = predict("twostate", [0, 0, 0, 0, 0, 0, 0, 0], three)
    assert p["A"][1] == 0.0 and p["mean_high"][1] == p["mean_low"][1]
    assert _same([1.0, float("nan")], np.array([1.0, np.nan])) and not _same([1.0], [np.nextafter(1.0, 2.0)])
    assert _same(np.array([True, False]), [True, False]) and _same(float("nan"), float("nan")) and not _same([1, 2], [1, 2, 3])
    print("self-test PASS")


# ----------------------------------------------------------------------------------------------------------------- main
def ideal_jobs(subjects: list) -> list:
    return [(g, di, s) for g in IDEAL_GENERATORS for di in range(len(BT.DRIFTS)) for s in subjects]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("--self-test", "--first", "--run", "--report"):
        ap.add_argument(flag, action="store_true")
    ap.add_argument("--n-jobs", type=int, default=2)
    a = ap.parse_args()
    self_test()
    if a.self_test:
        return
    install()
    d = run_directory(identity())
    ident = verify(d)
    print(f"archive {d} identity {ident[:12]}", flush=True)
    subjects = BT.templates()
    bench_path = os.path.join(d, "benchmark.json")
    if a.first:
        checks = [check_latent_path(g, subjects[0]) for g in IDEAL_GENERATORS]
        print(json.dumps(checks), flush=True)
        if not all(c["equal"] for c in checks):
            sys.exit("the latent-only path differs from synthetic.generate; Phase 1 stops")
        first = run_panel(0, d)
        print(json.dumps(first, default=str), flush=True)
        ideal = [run_ideal(g, 0, subjects[0], d) for g in IDEAL_GENERATORS]
        print(json.dumps(ideal, default=str), flush=True)
        t_panel = first["timing"]["total_s"]
        t_ideal = float(np.mean([r["timing"]["total_s"] for r in ideal]))
        worker_s = 39 * t_panel + (len(ideal_jobs(subjects)) - len(ideal)) * t_ideal
        wall_h = worker_s / max(a.n_jobs, 1) / 3600
        with open(os.path.join(BT.OUT_DIR, load_panel()["parent_namespace"], "manifest.json")) as fh:
            v6_runtime = json.load(fh)["runtime"]
        now_runtime = BT._jsonable(BT.runtime())
        runtime_diff = sorted(k for k in set(v6_runtime) | set(now_runtime) if v6_runtime.get(k) != now_runtime.get(k))
        bench = dict(created_utc=_now(), identity=ident, runtime_differs_from_v6_in=runtime_diff, latent_path_checks=checks,
                     first_panel=first,
                     ideal_first=ideal, panel_s_first=t_panel, ideal_s_mean=t_ideal, remaining_panel=39,
                     remaining_ideal=len(ideal_jobs(subjects)) - len(ideal), projected_worker_hours=worker_s / 3600,
                     n_jobs=a.n_jobs, projected_wall_hours=wall_h, pause_wall_hours=PAUSE_WALL_HOURS,
                     parity_first=first["parity"], proceed=bool(first["parity"]["equal"] and wall_h <= PAUSE_WALL_HOURS),
                     note="projection from one panel recording (all 20 windows) and one idealized recording per generator, "
                          "under the concurrent Mac load; extreme panel recordings may fit slower")
        with open(bench_path, "w") as fh:
            json.dump(BT._jsonable(bench), fh, indent=2)
        if not first["parity"]["equal"]:
            sys.exit(f"PARITY FAILED on the first recording ({first['parity']['differing']}); Phase 1 stops")
        print(f"first recording parity PASS; projected {worker_s / 3600:.2f} worker-h, {wall_h:.2f} wall-h at {a.n_jobs} "
              f"workers; proceed {bench['proceed']}", flush=True)
        if wall_h > PAUSE_WALL_HOURS:
            sys.exit(f"projection past {PAUSE_WALL_HOURS} wall-hours: pause and report before the main work")
    if a.run:
        with open(bench_path) as fh:
            bench = json.load(fh)
        if bench["identity"] != ident or not bench["proceed"]:
            sys.exit("no passing benchmark for this identity (run --first); nothing launched")
        from joblib import Parallel, delayed
        mod = importlib.import_module("devpanel_v7")
        n_panel = len(load_panel()["panel"])
        t0 = time.time()
        for r in Parallel(n_jobs=a.n_jobs, return_as="generator_unordered")(delayed(mod.run_panel)(i, d) for i in range(n_panel)):
            print(f"[{_now()}] panel {r['index']:>2} {r['key']} {r['role']}: parity {r['parity']['equal']} "
                  f"{r['parity']['differing']} {r['timing']['total_s']:.1f} s{' (reused)' if r['reused'] else ''}", flush=True)
        print(f"[{_now()}] panel done in {(time.time() - t0) / 3600:.2f} h", flush=True)
        for r in Parallel(n_jobs=a.n_jobs, return_as="generator_unordered")(delayed(mod.run_ideal)(g, di, s, d)
                                                                             for g, di, s in ideal_jobs(subjects)):
            print(f"[{_now()}] ideal {r['key']}: {r['status']} {r['timing']['total_s']:.1f} s{' (reused)' if r['reused'] else ''}",
                  flush=True)
        print(f"[{_now()}] Phase 1 runs finished in {(time.time() - t0) / 3600:.2f} h", flush=True)
    if a.run or a.report:
        pm = load_panel()
        rows = []
        for i, e in enumerate(pm["panel"]):
            p = os.path.join(d, "panel", panel_key(e) + ".npy")
            if not os.path.exists(p):
                rows.append(dict(index=i, key=panel_key(e), role=e["role"], present=False))
                continue
            o = load_output(p, panel_key(e), ident)
            rows.append(dict(index=i, key=panel_key(e), role=e["role"], present=True, parity=o["parity"]["equal"],
                             differing=o["parity"]["differing"], total_s=o["timing"]["total_s"], n_starts=o["n_starts"]))
        n_ideal = sum(os.path.exists(os.path.join(d, "ideal", ideal_key(*j) + ".npy")) for j in ideal_jobs(subjects))
        rep = dict(created_utc=_now(), identity=ident, panel=rows, panel_present=sum(r["present"] for r in rows),
                   panel_parity_equal=sum(bool(r.get("parity")) for r in rows), ideal_present=n_ideal,
                   ideal_expected=len(ideal_jobs(subjects)))
        with open(os.path.join(d, "parity_report.json"), "w") as fh:
            json.dump(rep, fh, indent=2)
        print(json.dumps({k: v for k, v in rep.items() if k != "panel"}), flush=True)


if __name__ == "__main__":
    main()
