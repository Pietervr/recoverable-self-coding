#!/usr/bin/env python3
"""Phase 2 fresh development check — DEVPLAN_v7.md rev 2 §3 and §3.1 F1–F9: the dose clamp C2 against the unchanged
baseline (C1 and C1+C2 withdrawn by recorded amendment). Development only: no EEG, nothing frozen, no v6 file edited and
nothing added to the fitting.

Design (§3). X1 strong, G1 strong and G3 weak, without and with drift, one replicate each: six groups x 34 recordings = 204,
generated with data tags (8, generator index, strength index, drift index, 0, subject) at the v6 calibrated amplitudes
(parent calibration hashes recorded; never recalibrated). The baseline is fitted once, through recording.recording_scores,
with in-process wrappers around the original likelihood functions (as in devpanel_v7.py) that log, per fit, the starts in
order (x0, theta, training log-likelihood, convergence, success, projected gradient, nit, nfev, status, message), the bounds
and the fit's result, and per fold the raw training and test blocks and each model's output. The wrappers draw no random
number.

Replay contract (F7), per recording, before any C2 score is used. Every comparison is exact, and a mismatch raises
ReplayMismatch:
  - payload sidecar, identity, manifest (recomputed from the identity and parent calibration) and complete fold keys;
  - per fold: the scaling and the non-finite-input rule recomputed from the raw blocks, and each model's fold output;
  - per fit: bounds; starts recomputed from the moment start and the seeded jitters (retries included); the retry rule;
    the start selection (first converged maximum in order, n_at_best, kept theta and training log-likelihood); the clamped
    training design equal to the original; per-trial training log-likelihoods and analytic gradients equal under the clamp;
  - the baseline held-out log-likelihood arrays, finite masks, availability and reasons equal to the logged fold output;
  - the recording's evidence (held-out sums / 4), availability, delta and n_trials rebuilt and equal to the stored summary.
C2 then evaluates each present test trial outside the training block's present-dose range at the nearest endpoint (graded L
in mean and SD, two-state A and H), at its observed y; catch trials, in-support trials and null are checked unchanged.
Every retained training fit is rescored, also where its baseline held-out score was non-finite, and availability is
re-evaluated from all C2 densities. Group decisions use group.decide unchanged, with the stored decoder AUCs.

Units and gates (F2–F5). Scheduled main-window keys: 34 recordings x 2 halves x 2 folds x 10 windows = 1,360 per family per
group. Categories: excluded, technical failure, no fit (fold unavailable, invalid test input, or no converged training fit
for the family or null), reference failure (non-finite null test density) and scored. On a scored unit a configuration is
severe iff any family trial density is non-finite (then also unavailable) or (sum of family - null trial log densities) /
n_test < -1 nat. C2 is locked only if all hold: all 204 results present; X1 strong two-state in both drift groups; each
graded group graded or inconclusive/mixed; 2 C <= B for the graded severe counts over the four graded groups (a non-empty
scored set); no increase in the two-state severe count in any group or the graded severe count in any graded group; no scored
family-fold newly unavailable in any group.

Usage (repo-root venv):  ../../.venv/bin/python devcheck_v7.py --first | --run [--n-jobs 2] | --report
Tests: test_devcheck_v7.py.
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ[_v] = "1"                                                   # before numpy; inherited by the joblib workers

import argparse  # noqa: E402
import collections  # noqa: E402
import csv  # noqa: E402
import hashlib  # noqa: E402
import importlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

import battery as BT  # noqa: E402
import decoder as DEC  # noqa: E402
import group as G  # noqa: E402
import likelihood as LK  # noqa: E402
import recording as RC  # noqa: E402
import synthetic as SY  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "melcon-devcheck-v7-phase2-r1"
PLAN = "DEVPLAN_v7.md rev 2 §3.1 F1-F9 (RSC f280138; Codex record eaea99b)"
BASE = os.path.join(HERE, "results", "devcheck_v7")
PARENT_NAMESPACE = "v6-ebaddf98807b"
PARENT_IDENTITY = "ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021"
GROUPS = (("X1", "strong", 0), ("X1", "strong", 1), ("G1", "strong", 0), ("G1", "strong", 1), ("G3", "weak", 0), ("G3", "weak", 1))
X1_GROUPS = GROUPS[:2]
GRADED_GROUPS = GROUPS[2:]
DATA_PHASE = 8
SEVERE = -1.0
FAMILIES = ("graded", "twostate")
MODELS = LK.PRIMARY
CONFIGS = ("baseline", "c2")
CEILING_WORKER_H, CEILING_WALL_H = 3.0, 4.0
DECIDE_ALLOWANCE_S = 180.0
SPEC = dict(groups=GROUPS, data_phase=DATA_PHASE, severe=SEVERE, families=FAMILIES, configs=CONFIGS,
            ceiling_worker_h=CEILING_WORKER_H, ceiling_wall_h=CEILING_WALL_H,
            clamp="present test x clipped to [min, max] of the training block's present x; catch, hemifield and null unchanged",
            gates=("all 204 results present", "X1 strong two-state in both drift groups (C2)",
                   "graded groups graded or inconclusive/mixed (C2)", "2 C <= B graded severe over graded groups, non-empty",
                   "no two-state severe increase in any group; no graded severe increase in any graded group",
                   "no scored family-fold newly unavailable in any group"))


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


LOADED = _loaded_modules()


def group_id(g: tuple) -> str:
    return f"{g[0]}|{g[1]}|d{g[2]}"


# ------------------------------------------------------------------------------------------------------------ identity
def parent_calibration() -> dict:
    run = os.path.join(BT.OUT_DIR, PARENT_NAMESPACE)
    with open(os.path.join(run, "manifest.json")) as fh:
        if BT.digest(json.load(fh)) != PARENT_IDENTITY:
            raise RuntimeError("parent namespace identity differs")
    cal = BT.load_calibration(run)
    return {f"{g}|{st}": dict(amplitude=float(cal[(g, st)]["amplitude"]), sha256=cal[(g, st)]["sha256"],
                              accepted=bool(cal[(g, st)]["accepted"])) for g, st, _ in GROUPS}


def identity() -> dict:
    subjects = BT.templates()
    return dict(schema=SCHEMA, plan=PLAN, modules=LOADED, runtime=BT.runtime(), parent_namespace=PARENT_NAMESPACE,
                parent_identity=PARENT_IDENTITY,
                parent_calibration_file=_sha_file(os.path.join(BT.OUT_DIR, PARENT_NAMESPACE, "calibration.json")),
                calibration=parent_calibration(), templates=subjects, template_digests=BT.template_digests(subjects),
                events_table=_sha_file(SY.TRIALS_CSV), likelihood=LK.SPEC, group=G.SPEC, decoder=DEC.SPEC,
                synthetic=SY.SPEC, spec=SPEC)


def run_directory(ident: dict) -> str:
    ident = BT._jsonable(ident)
    d = os.path.join(BASE, f"run-{BT.digest(ident)[:12]}")
    os.makedirs(os.path.join(d, "recordings"), exist_ok=True)
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
_STATE: dict = dict(min=None, starts=None, fits={}, folds={})


def _reset() -> None:
    _STATE.update(min=None, starts=None, fits={}, folds={})


def _minimize_logged(fun, x0, *args, **kwargs):
    res = _ORIG["minimize"](fun, x0, *args, **kwargs)
    _STATE["min"] = (int(res.nfev), int(res.status), str(res.message))
    return res


def _run_logged(model, d, b, x0):
    _STATE["min"] = None
    out = _ORIG["run"](model, d, b, x0)
    if _STATE["starts"] is not None:
        nfev, status, message = _STATE["min"] or (-1, -1, "")
        _STATE["starts"].append((np.array(x0, dtype=float), np.array(out["theta"], dtype=float), float(out["loglik"]),
                                 bool(out["converged"]), bool(out["success"]), float(out["pg"]), int(out["nit"]), nfev, status,
                                 message))
    return out


def _fit_logged(model, d, sc, tags=()):
    _STATE["starts"] = []
    try:
        r = _ORIG["fit"](model, d, sc, tags)
    finally:
        rows, _STATE["starts"] = _STATE["starts"], None
    cols = list(zip(*rows))
    starts = dict(x0=np.stack(cols[0]), theta=np.stack(cols[1]), loglik=np.array(cols[2], dtype=float),
                  converged=np.array(cols[3], dtype=bool), success=np.array(cols[4], dtype=bool), pg=np.array(cols[5], dtype=float),
                  nit=np.array(cols[6], dtype=int), nfev=np.array(cols[7], dtype=int), status=np.array(cols[8], dtype=int),
                  message=list(cols[9]))
    _STATE["fits"][(tuple(int(t) for t in tags), model)] = dict(
        available=bool(r["available"]), reason=r["reason"], n_starts=int(r["n_starts"]), n_converged=int(r["n_converged"]),
        retry=bool(r["retry"]), n_at_best=r.get("n_at_best"), theta=np.array(r["theta"], dtype=float) if r["available"] else None,
        loglik=float(r["loglik"]) if r["available"] else None, bounds=LK.bounds(model, sc), starts=starts)
    return r


def _fold_logged(train, test, tags=(), models=LK.PRIMARY):
    out = _ORIG["fold_scores"](train, test, tags=tags, models=models)
    blk = lambda b: dict(y=b.y.copy(), logc=b.logc.copy(), catch=b.catch.copy(), right=b.right.copy())  # noqa: E731
    _STATE["folds"][tuple(int(t) for t in tags)] = dict(
        train=blk(train), test=blk(test), models=list(models),
        output={m: dict(available=bool(out[m]["available"]), reason=out[m]["reason"], heldout=out[m].get("heldout"),
                        theta=np.array(out[m]["theta"], dtype=float) if "theta" in out[m] else None,
                        scaling=out[m].get("scaling")) for m in models})
    return out


def install() -> None:
    if LK._run is not _run_logged:
        LK._run, LK.fit, LK.fold_scores, LK.minimize = _run_logged, _fit_logged, _fold_logged, _minimize_logged


# ---------------------------------------------------------------------------------------------------------- recordings
def schedule(subjects: list) -> list:
    return [(g, st, di, int(s)) for g, st, di in GROUPS for s in subjects]


def recording_key(g: str, st: str, di: int, s: int) -> str:
    return f"{g}_{st}_d{di}_sub-{s:02d}"


def recording_manifest(ident: str, g: str, st: str, di: int, s: int, cal: dict) -> dict:
    return dict(config=ident, generator=g, strength=st, drift=bool(BT.DRIFTS[di]), drift_index=int(di), subject=int(s),
                tags=[DATA_PHASE, SY.GENERATORS.index(g), BT.STRENGTHS.index(st), int(di), 0, int(s)],
                amplitude=float(cal["amplitude"]), calibration=cal["sha256"], calibration_accepted=bool(cal["accepted"]),
                template=BT.template_digest(s), parent_identity=PARENT_IDENTITY)


def run_recording(g: str, st: str, di: int, s: int, d: str) -> dict:
    install()
    ident = verify(d)
    key = recording_key(g, st, di, s)
    path = os.path.join(d, "recordings", key + ".npy")
    man = recording_manifest(ident, g, st, di, s, parent_calibration()[f"{g}|{st}"])
    if os.path.exists(path) or os.path.exists(path + ".sha256"):
        out = load_output(path, key, ident)
        if out["manifest"] != man:
            raise RuntimeError(f"{path}: stored manifest differs")
        return dict(key=key, status=out["status"], timing=out["timing"], reused=True)
    _reset()
    t0 = time.perf_counter()
    rec = SY.generate(SY.template(s, "nocue"), g, man["amplitude"], man["drift"], tags=tuple(man["tags"]))
    t1 = time.perf_counter()
    res = RC.recording_scores(rec, s, "nocue")
    t2 = time.perf_counter()
    summ = BT.summary(res) if res["status"] == "ok" else {k: res[k] for k in ("status", "subject", "task")}
    out = dict(kind="recording", schema=SCHEMA, identity=ident, key=key, manifest=man, status=res["status"],
               traceback=res.get("traceback"), summary=summ, reasons=res.get("reasons"), fits=_STATE["fits"],
               folds=_STATE["folds"], timing=dict(generate_s=t1 - t0, scores_s=t2 - t1, total_s=t2 - t0), pid=os.getpid(),
               created_utc=_now())
    write_output(path, out, key, ident)
    _reset()
    return dict(key=key, status=out["status"], timing=out["timing"], reused=False)


# ------------------------------------------------------------------------------------------------------------- replay
class ReplayMismatch(RuntimeError):
    pass


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise ReplayMismatch(message)


def _eq(a, b) -> bool:
    A, B = np.asarray(a), np.asarray(b)
    if A.shape != B.shape:
        return False
    if A.dtype.kind in "fc" and B.dtype.kind in "fc":
        return bool(np.array_equal(A, B, equal_nan=True))
    return bool(np.array_equal(A, B))


def clamp(d: dict, lo: float, hi: float) -> dict:
    """C2's design: present trials' scaled dose clipped to [lo, hi]; catch rows, y and h unchanged."""
    return dict(d, x=np.where(d["c"], d["x"], np.clip(d["x"], lo, hi)))


def select_start(starts: dict):
    """likelihood.fit's selection: the first converged start with the highest training log-likelihood; n_at_best."""
    idx = [i for i in range(starts["loglik"].size) if starts["converged"][i]]
    if not idx:
        return None, 0
    best = max(idx, key=lambda i: starts["loglik"][i])
    return best, sum(starts["loglik"][i] >= starts["loglik"][best] - LK.BASIN_NAT for i in idx)


def replay_fit(m: str, f: dict, sc: dict, dtr: dict, tags: tuple, lo: float, hi: float, where: str):
    """The fit's logged path, recomputed; returns the kept theta, or None for a fit with no converged start."""
    b = LK.bounds(m, sc)
    _require(_eq(f["bounds"], b), f"{where}: bounds")
    st = f["starts"]
    n = st["loglik"].size
    n_initial = 1 + LK.N_JITTER
    retry = not bool(st["converged"][:n_initial].any())
    _require(n == f["n_starts"] and n == n_initial + (LK.RETRY_STARTS if retry else 0) and retry == f["retry"],
             f"{where}: start count or retry rule")
    _require(int(st["converged"].sum()) == f["n_converged"], f"{where}: converged count")
    p0 = LK.interior(LK.moment_start(m, dtr, sc), b)
    rng = np.random.default_rng(np.random.SeedSequence([LK.SEED, *tags, LK.MODEL_INDEX[m]]))
    x0 = [p0] + [LK.jitter(p0, b, rng, LK.JITTER_SD) for _ in range(LK.N_JITTER)]
    if retry:
        rng2 = np.random.default_rng(np.random.SeedSequence([LK.SEED, *tags, LK.MODEL_INDEX[m], 1]))
        x0 += [LK.jitter(p0, b, rng2, LK.RETRY_JITTER_SD) for _ in range(LK.RETRY_STARTS)]
    _require(_eq(np.stack(x0), st["x0"]), f"{where}: starts")
    best, n_at = select_start(st)
    if best is None:
        _require(not f["available"] and f["reason"] == "no converged start", f"{where}: fit without a converged start")
        return None
    _require(f["available"] and f["n_at_best"] == n_at, f"{where}: availability or n_at_best")
    th = st["theta"][best]
    _require(_eq(th, f["theta"]) and st["loglik"][best] == f["loglik"], f"{where}: kept start")
    dtc = clamp(dtr, lo, hi)
    _require(_eq(dtc["x"], dtr["x"]), f"{where}: the clamp is not the identity on training doses")
    ll1, g1 = LK.loglik(m, th, dtr, grad=True)
    ll2, g2 = LK.loglik(m, th, dtc, grad=True)
    _require(_eq(ll1, ll2) and _eq(g1, g2), f"{where}: training densities or gradient under the clamp")
    _require(float(ll1.sum()) == f["loglik"], f"{where}: training log-likelihood")
    return th


def replay_fold(fkey: tuple, fr: dict, fits: dict, where: str) -> dict:
    """One fold replayed: per model a category and, for a retained fit, the baseline and C2 held-out log densities."""
    train, test = LK.Block(**fr["train"]), LK.Block(**fr["test"])
    out = fr["output"]
    rec = dict(n_test=len(test), models={}, fold_reason=None)
    sc = LK.scaling(train)
    bad_input = not isinstance(sc, str) and (not np.all(np.isfinite(test.logc[~test.catch])) or not np.all(np.isfinite(test.y)))
    if isinstance(sc, str) or bad_input:
        reason = sc if isinstance(sc, str) else "non-finite test input"
        for m in MODELS:
            _require(not out[m]["available"] and out[m]["reason"] == reason and (fkey, m) not in fits,
                     f"{where}: fold unavailability ({reason})")
            rec["models"][m] = dict(category="no fit", reason=reason)
        rec["fold_reason"] = reason
        return rec
    dtr, dte = LK.design(train, sc), LK.design(test, sc)
    xp = dtr["x"][~dtr["c"]]
    lo, hi = float(xp.min()), float(xp.max())
    dtc = clamp(dte, lo, hi)
    pres = ~dte["c"]
    label = np.full(len(test), "catch", dtype=object)
    label[pres & (dte["x"] < lo)] = "below"
    label[pres & (dte["x"] >= lo) & (dte["x"] <= hi)] = "within"
    label[pres & (dte["x"] > hi)] = "above"
    unchanged = (label == "catch") | (label == "within")
    rec["label"] = label
    for m in MODELS:
        _require(out[m].get("scaling") == sc, f"{where} {m}: scaling")
        f = fits.get((fkey, m))
        _require(f is not None, f"{where} {m}: fit record missing")
        th = replay_fit(m, f, sc, dtr, fkey, lo, hi, f"{where} {m}")
        if th is None:
            _require(not out[m]["available"] and out[m]["reason"] == "no converged start", f"{where} {m}: fold output")
            rec["models"][m] = dict(category="no fit", reason="no converged start")
            continue
        _require(_eq(out[m]["theta"], th), f"{where} {m}: fold theta")
        llb = LK.loglik(m, th, dte)
        fin_b = bool(np.all(np.isfinite(llb)))
        _require(out[m]["available"] == fin_b and out[m]["reason"] == ("" if fin_b else "non-finite held-out density"),
                 f"{where} {m}: baseline availability")
        if fin_b:
            _require(out[m]["heldout"] == float(llb.sum()), f"{where} {m}: baseline held-out")
        llc = LK.loglik(m, th, dtc)
        _require(_eq(llc[unchanged], llb[unchanged]), f"{where} {m}: C2 changed a catch or in-support trial")
        if m == "null":
            _require(_eq(llc, llb), f"{where}: C2 changed null")
        rec["models"][m] = dict(category="fit", ll_baseline=llb, ll_c2=llc, finite_baseline=fin_b,
                                finite_c2=bool(np.all(np.isfinite(llc))))
    return rec


def _status_category(status: str) -> str:
    return "excluded" if status.startswith("excluded") else "technical failure"


def expected_blocks(subject: int) -> dict:
    """The scoring inputs recording.recording_scores builds for a synthetic recording, from its template alone (every
    template trial passes §2): per (half index, fold index) the training and test blocks' log contrast, catch flag and
    hemifield in trial order. Only the decoder projections y are not recomputable without the decoder."""
    t = SY.template(subject, "nocue")
    catch = t["catch"].to_numpy(bool)
    right = (t["side"].to_numpy() == "right") & ~catch
    logc = np.where(catch, np.nan, np.log(np.where(catch, 1.0, t["contrast"].to_numpy(float))))
    blk = t["block"].to_numpy()
    out = {}
    for hi, B in enumerate(sorted(DEC.HALVES)):
        half = np.isin(blk, B)
        for fi, pair in enumerate(((B[0], B[1]), (B[1], B[0]))):
            out[(hi, fi)] = tuple(dict(logc=logc[half][blk[half] == b], catch=catch[half][blk[half] == b],
                                       right=right[half][blk[half] == b]) for b in pair)
    return out


def replay_recording(out: dict, group: tuple, expected_manifest: dict | None = None) -> dict:
    """Replay one stored recording (F7); rebuild the baseline summary exactly and score C2; main-window units."""
    key, man = out["key"], out["manifest"]
    if expected_manifest is not None:
        _require(man == expected_manifest, f"{key}: manifest")
    subject = int(man["subject"])
    windows = list(RC.WINDOWS)
    main = set(DEC.MAIN)
    if out["status"] != "ok":
        cat = _status_category(out["status"])
        units = [dict(key=key, group=group_id(group), subject=subject, half=hi, fold=fi, window=w, family=fam, category=cat,
                      reason=out["status"]) for hi in range(2) for fi in range(2) for w in DEC.MAIN for fam in FAMILIES]
        return dict(key=key, group=group_id(group), subject=subject, status=out["status"], baseline=None, c2=None, units=units)
    summ = out["summary"]
    _require(list(summ["windows"]) == windows and list(summ["models"]) == list(MODELS), f"{key}: windows or models")
    task = RC.TASK_INDEX["nocue"]
    expected = {(subject, task, hi, fi, w) for hi in range(2) for fi in range(2) for w in windows}
    _require(set(out["folds"]) == expected, f"{key}: fold keys")
    _require({k for k, _ in out["fits"]} <= expected, f"{key}: fit keys")
    blocks = expected_blocks(subject)
    for (s_, t_, hi, fi, w), fr in out["folds"].items():
        for part, name in ((0, "train"), (1, "test")):
            for k in ("logc", "catch", "right"):
                _require(_eq(fr[name][k], blocks[(hi, fi)][part][k]), f"{key} {(s_, t_, hi, fi, w)}: {name} {k} (trial order)")
            _require(fr[name]["y"].size == blocks[(hi, fi)][part]["logc"].size, f"{key} {(s_, t_, hi, fi, w)}: {name} length")
    nW, nM = len(windows), len(MODELS)
    held = {c: np.zeros((nW, nM)) for c in CONFIGS}
    avail = {c: np.ones((nW, nM), dtype=bool) for c in CONFIGS}
    n_trials = np.zeros(nW, dtype=int)
    units = []
    for hi in range(2):
        for wi, w in enumerate(windows):
            for fi in range(2):
                fkey = (subject, task, hi, fi, w)
                rec = replay_fold(fkey, out["folds"][fkey], out["fits"], f"{key} {fkey}")
                n_trials[wi] += rec["n_test"]
                for mi, m in enumerate(MODELS):
                    r = rec["models"][m]
                    for c in CONFIGS:
                        if r["category"] == "fit" and r[f"finite_{c}"]:
                            held[c][wi, mi] += float(r[f"ll_{c}"].sum())
                        else:
                            avail[c][wi, mi] = False
                if w in main:
                    units += fold_units(key, group, subject, hi, fi, w, rec)
    results = {}
    i2, i3 = MODELS.index("graded"), MODELS.index("twostate")
    for c in CONFIGS:
        results[c] = dict(status="ok", subject=summ["subject"], task=summ["task"], windows=windows, models=list(MODELS),
                          evidence=np.where(avail[c], held[c] / 4.0, np.nan), available=avail[c].copy(),
                          delta=np.where(avail[c][:, i2] & avail[c][:, i3], (held[c][:, i3] - held[c][:, i2]) / np.maximum(n_trials, 1),
                                         np.nan),
                          n_trials=n_trials.copy(), auc=summ["auc"])
    for k in ("evidence", "available", "delta", "n_trials"):
        _require(_eq(results["baseline"][k], summ[k]), f"{key}: baseline {k} rebuilt from the replay")
    return dict(key=key, group=group_id(group), subject=subject, status="ok", baseline=results["baseline"], c2=results["c2"],
                units=units)


def fold_units(key: str, group: tuple, subject: int, hi: int, fi: int, w: int, rec: dict) -> list:
    units = []
    null = rec["models"]["null"]
    for fam in FAMILIES:
        r = rec["models"][fam]
        u = dict(key=key, group=group_id(group), subject=subject, half=hi, fold=fi, window=w, family=fam)
        if r["category"] != "fit" or null["category"] != "fit":
            units.append(dict(u, category="no fit", reason=rec["fold_reason"] or r.get("reason") or null.get("reason")))
            continue
        if not null["finite_baseline"]:
            units.append(dict(u, category="reference failure", reason="non-finite null test density"))
            continue
        u.update(category="scored", n_test=rec["n_test"], **{f"n_{lab}": int((rec["label"] == lab).sum())
                                                              for lab in ("below", "within", "above", "catch")})
        for c in CONFIGS:
            dll = r[f"ll_{c}"] - null["ll_baseline"]
            fin = r[f"finite_{c}"]
            loss = float(dll.sum() / rec["n_test"]) if fin else float("-inf")
            u.update({f"{c}_loss": loss, f"{c}_severe": bool((not fin) or loss < SEVERE), f"{c}_unavailable": bool(not fin),
                      **{f"{c}_dll_{lab}": float(np.sum(dll[rec["label"] == lab])) for lab in ("below", "within", "above", "catch")}})
        units.append(u)
    return units


# -------------------------------------------------------------------------------------------------------------- gates
def decide_groups(replays: list) -> dict:
    out = {}
    for g in GROUPS:
        reps = [r for r in replays if r["group"] == group_id(g)]
        for c in CONFIGS:
            results = [r[c] if r["status"] == "ok" else dict(status=r["status"], subject=r["subject"], task="nocue") for r in reps]
            ok = [x for x in results if x["status"] == "ok"]
            pos = BT.main_positions(ok[0]["windows"]) if ok else []
            n_pass = sum(not x["status"].startswith("excluded") for x in results)
            d = G.decide(results, pos, n_pass)
            out[(group_id(g), c)] = dict(outcome=d["outcome"], runs=d.get("runs"), n_windows_eligible=d.get("n_windows_eligible"),
                                         common_cohort_runs=d.get("common_cohort_runs"), n_recordings=len(results),
                                         pxp=[None if not row.get("eligible") else [float(v) for v in row["pxp"]]
                                              for row in d.get("windows", [])])
    return out


def tallies(units: list) -> dict:
    t = collections.defaultdict(int)
    for u in units:
        gk = (u["group"], u["family"])
        t[gk + ("scheduled",)] += 1
        t[gk + (u["category"],)] += 1
        if u["category"] == "scored":
            for c in CONFIGS:
                t[gk + (f"{c}_severe",)] += int(u[f"{c}_severe"])
                t[gk + (f"{c}_unavailable",)] += int(u[f"{c}_unavailable"])
            t[gk + ("newly_unavailable",)] += int(u["c2_unavailable"] and not u["baseline_unavailable"])
            t[gk + (f"transition_{'S' if u['baseline_severe'] else 'N'}{'S' if u['c2_severe'] else 'N'}",)] += 1
    return t


def gates(decisions: dict, units: list, n_present: int, n_expected: int) -> dict:
    if n_present != n_expected:
        return dict(decided=False, reason=f"incomplete: {n_present} of {n_expected} recording results present", lock_c2=False)
    t = tallies(units)
    cnt = lambda g, fam, k: t[(group_id(g), fam, k)]  # noqa: E731
    B = sum(cnt(g, "graded", "baseline_severe") for g in GRADED_GROUPS)
    C = sum(cnt(g, "graded", "c2_severe") for g in GRADED_GROUPS)
    scored_graded = sum(cnt(g, "graded", "scored") for g in GRADED_GROUPS)
    g = dict(
        x1_two_state_both_drifts=all(decisions[(group_id(x), "c2")]["outcome"] == "two-state" for x in X1_GROUPS),
        graded_groups_graded_or_inconclusive=all(decisions[(group_id(x), "c2")]["outcome"] in ("graded", "inconclusive/mixed")
                                                 for x in GRADED_GROUPS),
        graded_severe_halved=bool(scored_graded > 0 and 2 * C <= B),
        no_twostate_severe_increase=all(cnt(x, "twostate", "scored") > 0 and cnt(x, "twostate", "c2_severe") <= cnt(x, "twostate", "baseline_severe")
                                        for x in GROUPS),
        no_graded_severe_increase=all(cnt(x, "graded", "scored") > 0 and cnt(x, "graded", "c2_severe") <= cnt(x, "graded", "baseline_severe")
                                      for x in GRADED_GROUPS),
        no_newly_unavailable=all(cnt(x, fam, "newly_unavailable") == 0 for x in GROUPS for fam in FAMILIES))
    return dict(decided=True, gates=g, lock_c2=all(g.values()), graded_severe_B=B, graded_severe_C=C, graded_scored=scored_graded)


# ------------------------------------------------------------------------------------------------------------ reports
def build_report(d: str, ident: str) -> dict:
    subjects = BT.templates()
    cal = parent_calibration()
    replays, missing = [], []
    for g, st, di, s in schedule(subjects):
        key = recording_key(g, st, di, s)
        path = os.path.join(d, "recordings", key + ".npy")
        if not os.path.exists(path):
            missing.append(key)
            continue
        out = load_output(path, key, ident)
        replays.append(replay_recording(out, (g, st, di), recording_manifest(ident, g, st, di, s, cal[f"{g}|{st}"])))
    units = [u for r in replays for u in r["units"]]
    n_expected = len(schedule(subjects))
    decisions = decide_groups(replays) if not missing else {}
    gate = gates(decisions, units, len(replays), n_expected)
    t = tallies(units)
    per = {}
    for g in GROUPS:
        for fam in FAMILIES:
            gk = (group_id(g), fam)
            sev = {c: [u for u in units if (u["group"], u["family"]) == gk and u["category"] == "scored" and u[f"{c}_severe"]]
                   for c in CONFIGS}
            per[f"{gk[0]}|{fam}"] = dict(
                counts={k[2]: v for k, v in t.items() if k[:2] == gk},
                severe_loss_sum={c: float(np.sum([u[f"{c}_loss"] for u in sev[c]])) for c in CONFIGS},
                severe_loss_min={c: (float(min(u[f"{c}_loss"] for u in sev[c])) if sev[c] else None) for c in CONFIGS},
                dll_by_support={c: {lab: float(np.sum([u[f"{c}_dll_{lab}"] for u in units if (u["group"], u["family"]) == gk
                                                        and u["category"] == "scored"])) for lab in ("below", "within", "above", "catch")}
                                for c in CONFIGS})
    return dict(created_utc=_now(), identity=ident, plan=PLAN, n_expected=n_expected, n_present=len(replays), missing=missing,
                replay="every stored recording replayed exactly (F7); baseline evidence, availability, delta and n_trials rebuilt",
                decisions={f"{k[0]}|{k[1]}": v for k, v in decisions.items()}, gates=gate, per_group_family=per,
                recording_status=dict(collections.Counter(r["status"] if r["status"] == "ok" else _status_category(r["status"])
                                                          for r in replays))), units


def write_units(path: str, units: list) -> None:
    keys = []
    for u in units:
        keys += [k for k in u if k not in keys]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(units)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("--first", "--run", "--report"):
        ap.add_argument(flag, action="store_true")
    ap.add_argument("--n-jobs", type=int, default=2)
    a = ap.parse_args()
    install()
    d = run_directory(identity())
    ident = verify(d)
    print(f"archive {d} identity {ident[:12]}", flush=True)
    subjects = BT.templates()
    jobs = schedule(subjects)
    bench_path = os.path.join(d, "benchmark.json")
    if a.first:
        g, st, di, s = jobs[0]
        first = run_recording(g, st, di, s, d)
        t0 = time.perf_counter()
        out = load_output(os.path.join(d, "recordings", recording_key(g, st, di, s) + ".npy"), recording_key(g, st, di, s), ident)
        rep = replay_recording(out, (g, st, di), recording_manifest(ident, g, st, di, s, parent_calibration()[f"{g}|{st}"]))
        t_replay = time.perf_counter() - t0
        t_rec = first["timing"]["total_s"]
        worker_s = (len(jobs) - 1) * t_rec + len(jobs) * t_replay + DECIDE_ALLOWANCE_S
        wall_s = (len(jobs) - 1) * t_rec / max(a.n_jobs, 1) + len(jobs) * t_replay + DECIDE_ALLOWANCE_S
        bench = dict(created_utc=_now(), identity=ident, first=first, first_status=rep["status"], replay_s=t_replay,
                     replay="exact: baseline rebuilt from the logged folds; C2 scored", recording_s=t_rec,
                     projected_worker_hours=worker_s / 3600, projected_wall_hours=wall_s / 3600, n_jobs=a.n_jobs,
                     ceilings=dict(worker_h=CEILING_WORKER_H, wall_h=CEILING_WALL_H),
                     proceed=bool(worker_s / 3600 <= CEILING_WORKER_H and wall_s / 3600 <= CEILING_WALL_H),
                     note="one recording under the concurrent Mac load; decide allowance fixed; planning evidence")
        with open(bench_path, "w") as fh:
            json.dump(BT._jsonable(bench), fh, indent=2)
        print(json.dumps(BT._jsonable(bench), indent=1), flush=True)
        if not bench["proceed"]:
            sys.exit("projection past a ceiling: stop and report before the main work")
    if a.run:
        with open(bench_path) as fh:
            bench = json.load(fh)
        if bench["identity"] != ident or not bench["proceed"]:
            sys.exit("no passing benchmark for this identity (run --first); nothing launched")
        from joblib import Parallel, delayed
        mod = importlib.import_module("devcheck_v7")
        t0 = time.time()
        for r in Parallel(n_jobs=a.n_jobs, return_as="generator_unordered")(delayed(mod.run_recording)(*j, d) for j in jobs):
            print(f"[{_now()}] {r['key']}: {r['status']} {r['timing']['total_s']:.1f} s{' (reused)' if r['reused'] else ''}",
                  flush=True)
        print(f"[{_now()}] recordings finished in {(time.time() - t0) / 3600:.2f} h", flush=True)
    if a.run or a.report:
        t0 = time.time()
        report, units = build_report(d, ident)
        report["report_s"] = time.time() - t0
        write_units(os.path.join(d, "units.csv"), units)
        with open(os.path.join(d, "report.json"), "w") as fh:
            json.dump(BT._jsonable(report), fh, indent=1)
        print(json.dumps(BT._jsonable({k: report[k] for k in ("n_present", "n_expected", "recording_status", "decisions", "gates")}),
                         indent=1), flush=True)


if __name__ == "__main__":
    main()
