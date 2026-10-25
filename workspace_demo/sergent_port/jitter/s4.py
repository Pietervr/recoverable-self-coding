#!/usr/bin/env python3
"""jitter/s4.py — stages S4a and S4b of DESIGN_jitter.md rev 7 (§7.3–§7.6): the calibration battery, the final
validation manifest, the recovery battery with profiles, the inherited-pipeline mechanism test, and the gates.
Built 24 Oct 2026 for the AWS run (owner: "we need to do it on aws - go"). Every unit of work is a seeded
PARTICIPANT-DATASET TASK that writes one small JSON and is skipped when its file exists, so an interrupted instance
loses at most one dataset and any number of instances can take disjoint shards of one queue.

    s4.py bases                      cache the 20 base participants' levels/blocks/W53 (needed by O5) -> results/generators/bases_W53_active.npz
    s4.py s4a --workers N            S4a on calibration seeds, synchronously: ε benchmark (50 sets, G0/B0), λ pilots
                                     (5 × 20 sets), ε, λ selection, certification (50 sets, ≤ 1 secant correction) for
                                     E1 (1.25 ε) and T3 (2 ε), c₀ batches (2 × 500 datasets); writes results/s4/s4a.json
    s4.py s4b-queue                  list the S4b tasks (decision manifest + recovery) given results/s4/s4a.json
    s4.py s4b --workers N [--shard i/K] [--kind cv|rec|all]   run the S4b tasks of this shard, skipping finished ones
    s4.py evaluate                   set primaries, gates (b) (c) (e), V2, recovery flags R1–R5, rise -> results/s4/summary.{json,md}

Seeds: simulate.seed_for(stage, setting, r, m, extra) with stage 'calibration' (S4a) or 'validation' (S4b); member
draws seed_for(stage, setting, r, 0, 'set'). Development seeds (S2) never recur (§7.7).
Results: results/s4/<stage>/<setting>/set_<r>/m<m>.json (per participant-dataset; fits summarised, no start archives),
results/s4/c0/<family>/d<i>.json, results/s4/rec/<setting>/<config>/r<i>.json; aggregates in results/s4/.
"""
from __future__ import annotations

import os

os.environ.setdefault("NPROC", "1")

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time as _time  # noqa: E402

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # fit_models.py, bms.py (the inherited pipeline, §7.6)
import data as D  # noqa: E402
import decide as X  # noqa: E402
import fit as F  # noqa: E402
import models as M  # noqa: E402
import simulate as S  # noqa: E402

GEN_DIR = os.path.join(HERE, "results", "generators")
S4_DIR = os.path.join(HERE, "results", "s4")
SUBJECTS = list(range(1, 21))
DECISION_MODELS = ("G3", "B3")              # -> candidates G2, G3+, B2, B3+
EPS_MODELS = ("G0", "B0")
PILOT_LAMBDAS = (1.0, 0.75, 0.5, 0.35, 0.25)
R_EPS, R_PILOT, R_CERT = 50, 20, 50
C0_PER_CONFIG = 25
R_RECOVERY = 25
RECOVERY_S_TAU = (0.0, 20.0, 40.0, 80.0)
RECOVERY_S_G = (0.0, "fitted", 1.0)
# §7.3 manifest: setting -> (R, family of the generator, inherited pipeline run?)
MANIFEST = {
    "W1": (100, "G", True), "W2": (100, "G", True), "W3": (100, "G", True), "W4": (100, "G", True),
    "O1": (100, "G", True), "O2": (100, "G", True), "O3": (100, "G", True), "O4": (100, "G", True), "O5": (100, "G", True),
    "T1": (50, "B", True), "T2": (50, "B", False), "T3": (50, "B", False), "E1": (100, "B", False),
}
GRADED = ("W1", "W2", "W3", "W4", "O1", "O2", "O3", "O4", "O5")
AMENDMENT_NAME = "manifest_amendment.json"     # the §8 time-priority amendment, when invoked (T2, then T3)


def amendment_path() -> str:
    return os.path.join(S4_DIR, AMENDMENT_NAME)


def deferred_settings() -> dict:
    """The declared time-priority deferrals (DESIGN rev 7 §8 amendment): {setting: reason}; empty when none was invoked."""
    p = amendment_path()
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return json.load(f).get("deferred", {})


def record_deferral(settings: list, reason: str) -> dict:
    """Record a time-priority deferral BEFORE the deferred settings' S4b batch would run. Only T2 (development-only) and
    T3 (its S4b report-only reading; the S4a certification of λ_T3 stays) may be deferred (§8); nothing else is a time
    reduction. The record carries the time and code hash; `evaluate` reports deferred settings as DEFERRED."""
    bad = [s for s in settings if s not in ("T2", "T3")]
    if bad:
        raise ValueError(f"only T2 and T3 may be deferred (DESIGN rev 7 §8 time-priority amendment); got {bad}")
    cur = deferred_settings()
    for s in settings:
        cur[s] = reason
    rec = dict(deferred=cur, utc=_time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime()), code_hash=M.code_hash())
    _write(amendment_path(), rec)
    return rec


# ----------------------------------------------------------------------------------------------
# bases and generator configurations
# ----------------------------------------------------------------------------------------------
def bases_path(session="active"):
    return os.path.join(GEN_DIR, f"bases_W53_{session}.npz")


def cache_bases(session="active") -> dict:
    """Levels, blocks and the real 53-window means of the 20 base participants (O5 recentres the real trials)."""
    out = {}
    for s in SUBJECTS:
        p = D.load_participant(s, session)
        out[f"levels_{s}"] = p.levels
        out[f"blocks_{s}"] = p.blocks
        out[f"W53_{s}"] = p.W53
    np.savez_compressed(bases_path(session), **out)
    return load_bases(session)


def load_bases(session="active") -> dict:
    if not os.path.exists(bases_path(session)):
        return cache_bases(session)
    z = np.load(bases_path(session), allow_pickle=False)
    return {s: dict(levels=z[f"levels_{s}"], blocks=z[f"blocks_{s}"], W53=z[f"W53_{s}"]) for s in SUBJECTS}


def load_config(subject: int, model: str, session="active") -> F.GeneratorConfig:
    return F.GeneratorConfig.from_npz(os.path.join(GEN_DIR, f"S{subject}_{session}_{model}.npz"))


def set_members(stage: str, setting: str, r: int) -> list:
    rng = np.random.default_rng(S.seed_for(stage, setting, r, 0, "set"))
    return [int(s) for s in rng.choice(SUBJECTS, size=20, replace=True)]


def config_for(setting: str, base: int, lam: dict | None = None) -> tuple:
    """(GeneratorConfig, generate-mode) of a decision setting for one base subject. `lam` = {'E1': λ, 'T3': λ}."""
    if setting in ("W1", "W2", "W3", "W4", "O1", "O2", "O3", "O4", "O5"):
        g3 = load_config(base, "G3")
        if setting == "W1":
            return S.with_nuisance(g3, 0.0, 0.0), "W"
        if setting == "W2":
            return g3, "W"
        if setting == "W3":
            return S.with_nuisance(g3, 80.0, 0.0), "W"
        if setting == "W4":
            return S.with_nuisance(g3, 0.0, 1.0), "W"
        if setting in ("O1", "O2"):
            return S.with_nuisance(g3, 0.0, g3.s_g), setting          # zero latency jitter, s_g at the fitted value
        if setting in ("O3", "O4"):
            return g3, setting                                       # O3 sets s_τ by level inside generate; O4 (log g, τ) jointly
        return g3, "O5"
    if setting == "T1":
        return load_config(base, "B3"), "W"
    if setting == "T2":
        return S.halved_occupancy(load_config(base, "B3")), "T2"
    if setting in ("T3", "E1"):
        if lam is None or lam.get(setting) is None:
            raise ValueError(f"{setting} needs its certified λ")
        return S.scaled(load_config(base, "B3"), lam[setting]), "W"
    if setting == "EPS":
        return load_config(base, "B0"), "W"                          # ε benchmark: the fitted B0 generators (§7.4)
    if setting.startswith("LAM") or setting.startswith("CERT"):
        lam_value = float(setting.split("@")[1])
        return S.scaled(load_config(base, "B3"), lam_value), "W"
    raise KeyError(setting)


def make_synthetic(stage: str, setting: str, r: int, m: int, base: int, bases: dict, lam: dict | None = None) -> D.Participant:
    cfg, mode = config_for(setting, base, lam)
    b = bases[base]
    seed = S.seed_for(stage, setting, r, m)
    syn = S.generate(cfg, b["levels"], b["blocks"], seed, mode, base_W53=b["W53"] if mode == "O5" else None)
    p = syn.participant(subject=1000 * r + m)
    p.tag = f"{stage}-{setting}-r{r}-m{m}-S{base}"
    return p


# ----------------------------------------------------------------------------------------------
# tasks
# ----------------------------------------------------------------------------------------------
def _fit_summary(fr: F.FitResult, sp: M.ModelSpec | None) -> dict:
    d = dict(status=fr.status, loglik=fr.loglik, n_converged=fr.n_converged, n_starts=len(fr.starts),
             em_iterations=fr.em_iterations, selection=fr.selection, flags=fr.flags, candidates=fr.candidates,
             notes=[n for n in fr.notes if "stopped" in n or "accepted" in n or "retried" in n or "refit" in n],
             seconds=fr.seconds, quad=fr.quad)
    if fr.available and sp is not None:
        P = M.unpack(sp, fr.theta)
        d.update(s_tau_ms=P.s_tau_ms, s_g=P.s_g, a=[float(v) for v in P.a[1:]])
        if P.A is not None:
            d.update(A=[float(v) for v in P.A[1:]], kappa=P.kappa, x0=P.x0)
    return d


def cv_task(stage: str, setting: str, r: int, m: int, base: int, bases: dict, models: tuple, inherited: bool,
            lam: dict | None, out_path: str) -> dict:
    """One participant-dataset of a decision setting: the §7.3 decision batch (G2, B2, G3+, B3+ → G3, B3) or the ε
    batch (G0, B0), five block folds, held-out score; optionally the inherited per-window pipeline (§7.6)."""
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    p = make_synthetic(stage, setting, r, m, base, bases, lam)
    sp_ = D.span("primary")
    cache = F.FitCache()
    sums = {k: [] for k in models}
    folds = []
    fits_seen = []
    for fold in range(5):
        train, test, _, _ = D.fold_datasets(p, sp_, fold)
        res = F.fit_all_models(train, cache, "primary", models)
        row = dict(fold=fold, n_train=train.n, n_test=test.n, fits={})
        for name, fr in res.items():
            fits_seen.append(fr)
            sp = F.selected_spec(name, fr, "primary") if fr.available else None
            row["fits"][name] = _fit_summary(fr, sp)
        for sel in models:
            fr = res[sel]
            if fr.available:
                ll = F.score_heldout(F.selected_spec(sel, fr, "primary"), fr, test)
                sums[sel].append(float(np.sum(ll)))
            else:
                sums[sel].append(float("nan"))
        folds.append(row)
    n = D.n_scored(p)
    scores = {k: (float(np.sum(v) / n) if not np.any(np.isnan(v)) else float("nan")) for k, v in sums.items()}
    rec = dict(stage=stage, setting=setting, r=r, m=m, base=base, data_id=p.data_id, n_trials=p.n, n_scored=n,
               scores=scores, fold_sums=sums, folds=folds, code_hash=M.code_hash(), quad_rule=F.quad_rule_record(fits_seen))
    if inherited:
        t1 = _time.time()
        lme = S.inherited_fits(p.W53, p.levels, p.blocks)
        rec["inherited_lme"] = lme.tolist()
        rec["inherited_seconds"] = _time.time() - t1
    rec["seconds"] = _time.time() - t0
    _write(out_path, rec)
    return rec


def c0_task(family: str, config: int, i: int, bases: dict, out_path: str) -> dict:
    """One c₀ dataset (§7.5): the (0, fitted) zero-jitter generator of `config` for `family`, full data, primary
    span, the reduced and the positive-spread candidate; q(0) = 2[max(ℓ_pos, ℓ_red) − ℓ_red]."""
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    cfg = S.recovery_setting(load_config(config, family + "3"), 0.0, "fitted")
    b = bases[config]
    seed = S.seed_for("calibration", f"C0{family}", config, i)
    p = S.generate(cfg, b["levels"], b["blocks"], seed, "W").participant(subject=config)
    ds = D.full_dataset(p, D.span("primary"))
    # the same cross-family candidate/chain procedure as every other fit (G's B-basin re-seed, B's G-twin chains):
    # both families are fitted and the statistic reads this family's reduced and positive candidates (Codex S3 review
    # 24 Oct, finding 10 — a stand-alone family pair is not the declared fitter)
    res = F.fit_all_models(ds, F.FitCache(), "primary", ("G3", "B3"))
    red, pos = res[family + "2"], res[family + "3+"]
    q0 = X.q0_statistic(red.loglik if red.available else None, pos.loglik if pos.available else None)
    other = "B" if family == "G" else "G"
    rec = dict(family=family, config=config, i=i, data_id=p.data_id, q0=q0,
               reduced=_fit_summary(red, M.spec(family + "2")), positive=_fit_summary(pos, M.spec(family + "3+")),
               other_family={n: _fit_summary(res[n], M.spec(n)) for n in (other + "2", other + "3+")},
               seconds=_time.time() - t0, code_hash=M.code_hash(), quad_rule=F.quad_rule_record(res.values()))
    _write(out_path, rec)
    return rec


def rec_task(setting_key: str, config: int, i: int, bases: dict, c0: dict, out_path: str) -> dict:
    """One recovery dataset (§7.5): the fixed-roster configuration at a recovery setting, FULL data, primary span,
    all eight models, and the s_τ profile (hull) of each family's full model."""
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    fam_g, fam_b = load_config(config, "G3"), load_config(config, "B3")
    if setting_key in ("O1", "O2"):
        truth = dict(s_tau=0.0, s_g="fitted")
        cfg_g = S.with_nuisance(fam_g, 0.0, fam_g.s_g)
        mode = setting_key
    else:
        s_tau, s_g = setting_key.split("|")
        s_tau = float(s_tau)
        s_g_val = "fitted" if s_g == "fitted" else float(s_g)
        truth = dict(s_tau=s_tau, s_g=s_g_val)
        cfg_g = S.recovery_setting(fam_g, s_tau, s_g_val)
        mode = "W"
    rows = {}
    fits_seen = []
    for family, cfg in (("G", cfg_g), ("B", (S.with_nuisance(fam_b, 0.0, fam_b.s_g) if mode != "W" else S.recovery_setting(fam_b, truth["s_tau"], truth["s_g"])))):
        b = bases[config]
        seed = S.seed_for("validation", f"REC{family}|{setting_key}", config, i)
        # O1/O2 at zero jitter are generated once from the G configuration and fitted by both families (§7.5)
        gen_cfg = cfg_g if mode != "W" else cfg
        p = S.generate(gen_cfg, b["levels"], b["blocks"], seed, mode).participant(subject=config)
        ds = D.full_dataset(p, D.span("primary"))
        cache = F.FitCache()
        res = F.fit_all_models(ds, cache, "primary", F.FULL_MODELS)
        fits_seen += list(res.values())
        fits = {name: _fit_summary(fr, F.selected_spec(name, fr, "primary") if fr.available else None) for name, fr in res.items()}
        full = res[family + "3"]
        prof = None
        if full.available and c0.get(family) is not None:
            ev, plog = F.profile_evaluator(family, ds, full, "primary", cache)
            pr = X.hull_search(ev, full.loglik, c0[family])
            prof = pr.as_dict()
            fits_seen += [v for s_ms, v in plog.items() if s_ms > 0.0]          # the s = 0 point is res[family + "2"], counted above
        rows[family] = dict(data_id=p.data_id, fits=fits, profile=prof,
                            s_tau_hat=fits[family + "3"].get("s_tau_ms"), s_g_hat=fits[family + "3"].get("s_g"),
                            selection=fits[family + "3"].get("selection"))
    rec = dict(setting=setting_key, config=config, i=i, truth=truth, families=rows, seconds=_time.time() - t0,
               code_hash=M.code_hash(), quad_rule=F.quad_rule_record(fits_seen))
    _write(out_path, rec)
    return rec


def _write(path: str, rec: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(rec, f)
    os.replace(tmp, path)


# ----------------------------------------------------------------------------------------------
# queues and sharding
# ----------------------------------------------------------------------------------------------
def cv_path(stage, setting, r, m):
    return os.path.join(S4_DIR, stage, setting, f"set_{r}", f"m{m}.json")


def cv_tasks(stage: str, setting: str, R: int, models: tuple, inherited: bool, lam: dict | None = None) -> list:
    tasks = []
    for r in range(R):
        members = set_members(stage, setting, r)
        for m, base in enumerate(members):
            tasks.append(dict(kind="cv", stage=stage, setting=setting, r=r, m=m, base=base, models=models,
                              inherited=inherited, lam=lam, path=cv_path(stage, setting, r, m)))
    return tasks


def c0_tasks() -> list:
    return [dict(kind="c0", family=fam, config=c, i=i, path=os.path.join(S4_DIR, "c0", fam, f"S{c}_d{i}.json"))
            for fam in ("G", "B") for c in SUBJECTS for i in range(C0_PER_CONFIG)]


def recovery_settings() -> list:
    keys = [f"{s_tau:g}|{s_g}" for s_tau in RECOVERY_S_TAU for s_g in RECOVERY_S_G]
    return keys + ["O1", "O2"]


def rec_tasks() -> list:
    return [dict(kind="rec", setting=k, config=c, i=i, path=os.path.join(S4_DIR, "rec", k.replace("|", "_"), f"S{c}_r{i}.json"))
            for k in recovery_settings() for c in SUBJECTS for i in range(R_RECOVERY)]


def pending(tasks: list, shard: str | None = None) -> list:
    out = [t for t in tasks if not os.path.exists(t["path"])]
    if shard:
        i, k = (int(v) for v in shard.split("/"))
        out = [t for t in out if int(hashlib.sha256(t["path"].encode()).hexdigest()[:8], 16) % k == i]
    rng = np.random.default_rng(0)
    rng.shuffle(out)
    return out


def run_task(t: dict, bases: dict, c0: dict | None = None) -> str:
    if t["kind"] == "cv":
        cv_task(t["stage"], t["setting"], t["r"], t["m"], t["base"], bases, tuple(t["models"]), t["inherited"], t["lam"], t["path"])
    elif t["kind"] == "c0":
        c0_task(t["family"], t["config"], t["i"], bases, t["path"])
    elif t["kind"] == "rec":
        rec_task(t["setting"], t["config"], t["i"], bases, c0 or {}, t["path"])
    return t["path"]


def run_queue(tasks: list, workers: int, bases: dict, c0: dict | None = None, label: str = "") -> int:
    from joblib import Parallel, delayed
    todo = tasks
    print(f"[s4] {label}: {len(todo)} tasks on {workers} workers, start {_time.strftime('%H:%M:%SZ', _time.gmtime())}", flush=True)
    t0 = _time.time()
    if todo:
        Parallel(n_jobs=workers, backend="loky", verbose=0)(delayed(run_task)(t, bases, c0) for t in todo)
    print(f"[s4] {label}: done {len(todo)} tasks in {_time.time() - t0:.0f} s", flush=True)
    return len(todo)


# ----------------------------------------------------------------------------------------------
# aggregation helpers
# ----------------------------------------------------------------------------------------------
def load_set(stage: str, setting: str, r: int) -> dict | None:
    rows = []
    for m in range(20):
        pth = cv_path(stage, setting, r, m)
        if not os.path.exists(pth):
            return None
        with open(pth) as f:
            rows.append(json.load(f))
    return dict(setting=setting, r=r, rows=rows)


def set_scores(sset: dict, models=("G3", "B3")) -> dict:
    return {f"m{row['m']}": {k: row["scores"].get(k, float("nan")) for k in models} for row in sset["rows"]}


def set_mean_delta(sset: dict, a: str, b: str):
    """Mean over available participants of S_a − S_b (None if fewer than 16 available)."""
    vals = [row["scores"][a] - row["scores"][b] for row in sset["rows"]
            if np.isfinite(row["scores"].get(a, np.nan)) and np.isfinite(row["scores"].get(b, np.nan))]
    return float(np.mean(vals)) if len(vals) >= X.MIN_ROSTER else None


def reference_over_sets(stage: str, setting: str, R: int, a: str, b: str, level: float = 0.95) -> X.Interval:
    means = []
    for r in range(R):
        s = load_set(stage, setting, r)
        means.append(None if s is None else set_mean_delta(s, a, b))
    return X.procedure_reference(means, level)


# ----------------------------------------------------------------------------------------------
# S4a: ε, λ path, c₀ (synchronous on one host, or the same deterministic path on K hosts that share the result
# prefix: every host runs its hash shard of each batch, then waits until the whole batch is present before the
# selection step, so all K compute the same ε, c₀ and λ and the last one to finish writes s4a.json; 24 Oct 2026, after
# the AMD core measured several times slower than the Mac's — one host would have needed more than a day)
# ----------------------------------------------------------------------------------------------
class Incomplete(RuntimeError):
    """A batch is not complete on this host and no waiting was allowed (other shards still running or lost)."""


def s3_pull():
    """Pull the shared result prefix (set by the user-data as S4_S3_RESULTS) into results/s4; no-op without it."""
    src = os.environ.get("S4_S3_RESULTS")
    if not src:
        return False
    import subprocess
    out = subprocess.run(["aws", "s3", "sync", src, S4_DIR, "--quiet", "--exclude", "*.tmp.*"], capture_output=True, text=True)
    if out.returncode != 0:
        print(f"[s4] s3 pull rc {out.returncode}: {out.stderr.strip()[:200]}", flush=True)
    return out.returncode == 0


def complete_or_wait(tasks: list, shard: str | None, wait_s: float, label: str):
    """After this host ran its shard: return when every task file of the batch exists; otherwise pull the shared
    prefix every 2 min for up to wait_s seconds, then raise Incomplete. A single host (shard None) never waits."""
    t0 = _time.time()
    while True:
        missing = [t for t in tasks if not os.path.exists(t["path"])]
        if not missing:
            return
        if shard is None or _time.time() - t0 > wait_s:
            raise Incomplete(f"{label}: {len(missing)} of {len(tasks)} task files missing after {_time.time() - t0:.0f} s")
        print(f"[s4] {label}: waiting for {len(missing)} tasks of other shards ({_time.strftime('%H:%M:%SZ', _time.gmtime())})", flush=True)
        _time.sleep(120)
        s3_pull()


def s4a_stage1_tasks() -> list:
    stage = "calibration"
    tasks = cv_tasks(stage, "EPS", R_EPS, EPS_MODELS, False)
    for lam in PILOT_LAMBDAS:
        tasks += cv_tasks(stage, f"LAM@{lam:g}", R_PILOT, DECISION_MODELS, False)
    tasks += c0_tasks()
    return tasks


def s4a(workers: int, shard: str | None = None, wait_s: float = 0.0) -> dict:
    bases = load_bases()
    out_path = os.path.join(S4_DIR, "s4a.json")
    stage = "calibration"
    shard = None if shard in (None, "1/1") else shard
    # 1. ε benchmark, λ pilots and the c₀ batches are independent: one queue (this host's shard of it)
    tasks = s4a_stage1_tasks()
    run_queue(pending(tasks, shard), workers, bases, label=f"S4a epsilon + pilots + c0 shard {shard or '1/1'}")
    complete_or_wait(tasks, shard, wait_s, "S4a stage 1")
    # 2. ε
    bench = reference_over_sets(stage, "EPS", R_EPS, "B0", "G0")
    eps = X.epsilon(bench)
    result = dict(epsilon_benchmark=bench.as_dict(), epsilon=eps, epsilon_available=eps is not None)
    print(f"[s4a] epsilon benchmark {bench.as_dict()} -> epsilon {eps}", flush=True)
    # 3. c₀ per family
    c0 = {}
    for fam in ("G", "B"):
        q0s, n = [], 0
        for t in c0_tasks():
            if t["family"] != fam:
                continue
            n += 1
            with open(t["path"]) as f:
                q0s.append(json.load(f)["q0"])
        val, info = X.critical_value(q0s, n)
        c0[fam] = val
        result[f"c0_{fam}"] = dict(value=val, **info)
        print(f"[s4a] c0 {fam}: {val} {info}", flush=True)
    result["c0"] = c0
    # 4. λ path for E1 (1.25 ε) and T3 (2 ε); the pilots are shared
    pilots = [(lam, reference_over_sets(stage, f"LAM@{lam:g}", R_PILOT, "B3", "G3")) for lam in PILOT_LAMBDAS]
    result["pilots"] = [dict(lam=lam, reference=iv.as_dict()) for lam, iv in pilots]
    result["lambda"] = {}
    if eps is None:
        result["lambda"] = {"E1": None, "T3": None, "reason": "epsilon UNAVAILABLE"}
    else:
        for target_name, mult in (("E1", 1.25), ("T3", 2.0)):
            target = mult * eps

            def certify(lam_value, _name=target_name):
                setting = f"CERT{_name}@{lam_value:.6g}"
                ct = cv_tasks(stage, setting, R_CERT, DECISION_MODELS, False)
                run_queue(pending(ct, shard), workers, bases, label=f"S4a certification {setting} shard {shard or '1/1'}")
                complete_or_wait(ct, shard, wait_s, f"S4a certification {setting}")
                return reference_over_sets(stage, setting, R_CERT, "B3", "G3", level=0.975)   # 97.5% per attempt

            rec = X.lambda_path(pilots, target, eps, certify)
            result["lambda"][target_name] = dict(target=target, **rec.as_dict())
            print(f"[s4a] lambda {target_name}: {rec.status} lam {rec.lam} ({rec.mode}; {rec.reason})", flush=True)
    result["code_hash"] = M.code_hash()
    result["utc"] = _time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime())
    _write(out_path, result)
    print(f"[s4a] written {out_path}", flush=True)
    return result


def load_s4a() -> dict:
    with open(os.path.join(S4_DIR, "s4a.json")) as f:
        return json.load(f)


# ----------------------------------------------------------------------------------------------
# S4b: the manifest and the recovery battery (shardable)
# ----------------------------------------------------------------------------------------------
def s4b_tasks(kind: str = "all") -> list:
    a = load_s4a()
    lam = {k: (a["lambda"].get(k) or {}).get("lam") if (a["lambda"].get(k) or {}).get("status") == "CERTIFIED" else None
           for k in ("E1", "T3")}
    deferred = deferred_settings()
    tasks = []
    if kind in ("cv", "all"):
        for setting, (R, _fam, inherited) in MANIFEST.items():
            if setting in ("E1", "T3") and lam.get(setting) is None:
                continue                                               # uninstantiated: reported as ABSENT (§7.3)
            if setting in deferred:
                continue                                               # deferred by the §8 amendment: reported as DEFERRED
            tasks += cv_tasks("validation", setting, R, DECISION_MODELS, inherited, lam)
    if kind in ("rec", "all"):
        tasks += rec_tasks()
    return tasks


def s4b(workers: int, shard: str | None, kind: str, defer: list | None = None, defer_reason: str = "") -> int:
    bases = load_bases()
    c0 = load_s4a()["c0"]
    if defer:
        print(f"[s4] deferral recorded: {record_deferral(defer, defer_reason)}", flush=True)
    todo = pending(s4b_tasks(kind), shard)
    return run_queue(todo, workers, bases, c0, label=f"S4b {kind} shard {shard or '1/1'}")


def manifest_status(a: dict, attempted: dict, rec_counts: dict, deferred: dict | None = None) -> dict:
    """§7.3/§7.5 completeness BEFORE any licence is read (Codex S3 review 24 Oct 2026, finding 11): every retained
    setting has its R attempted outcomes (an attempted set = all 20 participant files present), E1/T3 without a
    CERTIFIED λ are ABSENT by declaration, a setting deferred by the §8 amendment is DEFERRED (declared), and an
    unfinished required setting is PENDING and withholds the licence — never silently absent. The recovery battery
    needs all 20 × R_RECOVERY datasets at each of its 14 settings. `attempted` = {setting: n attempted sets};
    `rec_counts` = {setting key: n result rows}."""
    deferred = deferred or {}
    lam = a.get("lambda", {}) or {}
    settings = {}
    for setting, (R, _fam, _inh) in MANIFEST.items():
        if setting in deferred:
            settings[setting] = dict(state="DEFERRED", reason=deferred[setting], attempted=int(attempted.get(setting, 0)), R=R)
            continue
        if setting in ("E1", "T3"):
            rec = lam.get(setting) or {}
            if rec.get("status") != "CERTIFIED":
                settings[setting] = dict(state="ABSENT", reason=f"lambda_{setting} {rec.get('status', 'not run')}: uninstantiated (§7.3)",
                                         attempted=0, R=R)
                continue
        n = int(attempted.get(setting, 0))
        settings[setting] = dict(state="COMPLETE" if n >= R else "PENDING", attempted=n, R=R)
    need = len(SUBJECTS) * R_RECOVERY
    recovery = {k: dict(state="COMPLETE" if int(rec_counts.get(k, 0)) >= need else "PENDING", rows=int(rec_counts.get(k, 0)), need=need)
                for k in recovery_settings()}
    pend = [k for k, v in settings.items() if v["state"] == "PENDING"] + [f"rec {k}" for k, v in recovery.items() if v["state"] == "PENDING"]
    return dict(complete=not pend, pending=pend, settings=settings, recovery=recovery)


# ----------------------------------------------------------------------------------------------
# evaluation (§7.3 gates, §7.5 flags, §7.6 rise)
# ----------------------------------------------------------------------------------------------
def evaluate() -> dict:
    a = load_s4a()
    stage = "validation"
    out = dict(s4a=dict(epsilon=a["epsilon"], c0=a["c0"], lam=a["lambda"]))
    outcomes, deltas, ub_fields, calls = {}, {}, [], {}
    for setting, (R, fam, inherited) in MANIFEST.items():
        outs, means, lmes = [], [], []
        attempted = 0
        for r in range(R):
            s = load_set(stage, setting, r)
            if s is None:
                continue
            attempted += 1
            sc = set_scores(s)
            prim = X.set_primary(sc)
            outs.append(prim)
            means.append(set_mean_delta(s, "B3", "G3"))
            if setting == "E1":
                iv = X.roster_interval({k: v["B3"] - v["G3"] for k, v in sc.items() if np.isfinite(v["B3"] - v["G3"])},
                                       [k for k, v in sc.items() if np.isfinite(v["B3"] - v["G3"])])
                if a["epsilon"] is None or iv.sign in (X.UNAVAILABLE, X.NONFINITE):
                    ub_fields.append(X.UNAVAILABLE)
                else:
                    ub_fields.append("BOUNDED" if iv.hi < a["epsilon"] else "NOT BOUNDED")
            if inherited and all("inherited_lme" in row for row in s["rows"]):
                summ = S.inherited_group_summary([np.asarray(row["inherited_lme"]) for row in s["rows"]])
                lmes.append(bool(summ["call"]))
        if attempted:
            outcomes[setting] = outs
            deltas[setting] = dict(attempted=attempted, R=R, primaries={k: outs.count(k) for k in (X.POSITIVE, X.NEGATIVE, X.UNRESOLVED, X.UNAVAILABLE)},
                                   set_mean_delta3=[v for v in means if v is not None],
                                   reference=X.procedure_reference(means).as_dict())
            if lmes:
                calls[setting] = lmes
    out["settings"] = deltas
    out["gate_b"] = X.gate_b({k: v for k, v in outcomes.items() if k in GRADED})
    out["gate_c"] = X.gate_c(outcomes.get("T1", []))
    out["gate_e"] = X.gate_e(ub_fields) if "E1" in outcomes else dict(passed=False, status="E1 absent")
    out["completion_v2"] = X.completion_v2(outcomes)
    out["T2"] = dict(primaries={k: outcomes.get("T2", []).count(k) for k in (X.POSITIVE, X.NEGATIVE, X.UNRESOLVED, X.UNAVAILABLE)})
    out["T3"] = dict(primaries={k: outcomes.get("T3", []).count(k) for k in (X.POSITIVE, X.NEGATIVE, X.UNRESOLVED, X.UNAVAILABLE)})
    if "W1" in calls:
        out["rise"] = {k: X.rise(calls["W1"], calls[k]) for k in ("W3", "W4") if k in calls}
        out["inherited_calls"] = {k: dict(calls=int(sum(v)), sets=len(v)) for k, v in calls.items()}
    # recovery battery
    stats = {}
    rec_counts = {}
    for fam in ("G", "B"):
        point, false_jitter, false_detect, coverage = {}, {}, {}, {}
        r5 = dict(detect=[], cover=[])
        for key in recovery_settings():
            rows = []
            for c in SUBJECTS:
                for i in range(R_RECOVERY):
                    pth = os.path.join(S4_DIR, "rec", key.replace("|", "_"), f"S{c}_r{i}.json")
                    if os.path.exists(pth):
                        with open(pth) as f:
                            rows.append(json.load(f))
            rec_counts[key] = len(rows)
            if not rows:
                continue
            if key in ("O1", "O2"):
                skey = key
                true_s = 0.0
            else:
                s_tau, s_g = key.split("|")
                skey = (float(s_tau), "fitted" if s_g == "fitted" else float(s_g))
                true_s = float(s_tau)
            fj, fd, cov = [], [], []
            per_cfg = {}
            for row in rows:
                fr = row["families"][fam]
                s_hat = fr.get("s_tau_hat")
                prof = fr.get("profile")
                avail = s_hat is not None
                fj.append((not avail) or (s_hat > X.DETECT_MS))
                lb_exceeds = bool(prof and prof["status"] == "AVAILABLE" and prof["lo"] > X.DETECT_MS)
                fd.append(lb_exceeds)
                cov.append(bool(prof and prof["status"] == "AVAILABLE" and prof["lo"] <= true_s <= prof["hi"]))
                per_cfg.setdefault(row["config"], []).append((s_hat, prof))
            if skey in ((0.0, 0.0), (0.0, "fitted"), (0.0, 1.0), "O1", "O2"):
                false_jitter[skey] = fj
                false_detect[skey] = fd
            if skey in ((40.0, "fitted"), (80.0, "fitted")):
                coverage[skey] = cov
                pt = {}
                for c, lst in per_cfg.items():
                    hats = np.array([h for h, _ in lst if h is not None], dtype=float)
                    n_un = sum(1 for h, pr in lst if h is None or pr is None or pr["status"] != "AVAILABLE")
                    pt[c] = dict(median_rel_bias=float(np.median(hats - true_s) / true_s) if hats.size else np.inf,
                                 rmse=float(np.sqrt(np.mean((hats - true_s) ** 2))) if hats.size else np.inf,
                                 completion_ok=bool(n_un <= 0.2 * len(lst)))
                point[skey] = pt
            if skey == (20.0, "fitted"):
                r5["detect"] = [((not (pr and pr["status"] == "AVAILABLE")) or pr["lo"] > X.DETECT_MS) for _, pr in
                                [(fr.get("s_tau_hat"), fr.get("profile")) for fr in (row["families"][fam] for row in rows)]]
                r5["cover"] = [bool(pr and pr["status"] == "AVAILABLE" and pr["lo"] <= 20.0 <= pr["hi"]) for pr in
                               (row["families"][fam].get("profile") for row in rows)]
        stats[fam] = dict(point=point, false_jitter=false_jitter, false_detect=false_detect, coverage=coverage, r5=r5)
    out["recovery"] = {}
    for fam in ("G", "B"):
        try:
            out["recovery"][fam] = X.recovery_flags(stats, fam)
        except KeyError as e:
            out["recovery"][fam] = dict(flag="INCOMPLETE", missing=str(e))
    # manifest completeness BEFORE any licence (Codex finding 11): gates and flags computed on an incomplete manifest
    # are PROVISIONAL and license nothing; an unfinished required setting is PENDING, never silently absent
    man = manifest_status(a, {k: v["attempted"] for k, v in deltas.items()}, rec_counts, deferred_settings())
    out["manifest"] = man
    final = bool(man["complete"])
    for g in ("gate_b", "gate_c", "gate_e", "completion_v2"):
        out[g]["final"] = final
    for fam in ("G", "B"):
        out["recovery"][fam]["provisional"] = not final
    lam_e1 = (a.get("lambda", {}).get("E1") or {}).get("status") == "CERTIFIED"
    out["licence_inputs"] = dict(
        manifest_complete=final,
        gates_bc_met=bool(final and out["gate_b"]["passed"] and out["gate_c"]["passed"]),
        v2_sim_met=bool(final and out["completion_v2"]["passed"]),
        gate_e_met=bool(final and out["gate_e"]["passed"]),
        epsilon=a["epsilon"], epsilon_available=a["epsilon"] is not None, lambda_e1_certified=bool(lam_e1),
        recovery_G=(out["recovery"]["G"].get("flag") if final else "INCOMPLETE"),
        recovery_B=(out["recovery"]["B"].get("flag") if final else "INCOMPLETE"),
        note=("the manifest is complete: these inputs may feed decide.decide" if final else
              "PROVISIONAL: the manifest is incomplete (" + ", ".join(man["pending"]) + "); no licence may be read"))
    out["utc"] = _time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime())
    _write(os.path.join(S4_DIR, "summary.json"), out)
    with open(os.path.join(S4_DIR, "summary.md"), "w") as f:
        f.write(summary_markdown(out))
    return out


def summary_markdown(out: dict) -> str:
    man = out.get("manifest", {})
    L = ["# S4 — gates and flags (DESIGN rev 7 §7.3–§7.6)", "",
         ("MANIFEST COMPLETE — the gates and flags below are final." if man.get("complete") else
          "MANIFEST PENDING — every gate and flag below is PROVISIONAL and licenses nothing; pending: " + ", ".join(man.get("pending", []))),
         "settings: " + ", ".join(f"{k} {v['state']} {v['attempted']}/{v['R']}" for k, v in man.get("settings", {}).items()),
         "recovery: " + ", ".join(f"{k} {v['rows']}/{v['need']}" for k, v in man.get("recovery", {}).items() if v["state"] != "COMPLETE") or "recovery: all 14 settings complete",
         "",
         f"S4a: ε {out['s4a']['epsilon']}; c₀ {out['s4a']['c0']}; λ {json.dumps(out['s4a']['lam'], default=str)[:400]}", "",
         "| setting | attempted/R | POSITIVE | NEGATIVE | UNRESOLVED | UNAVAILABLE | reference Δ₃ (mean [lo, hi]) |", "|---|---|---|---|---|---|---|"]
    for k, v in out["settings"].items():
        p = v["primaries"]; ref = v["reference"]
        L.append(f"| {k} | {v['attempted']}/{v['R']} | {p['POSITIVE']} | {p['NEGATIVE']} | {p['UNRESOLVED']} | {p['UNAVAILABLE']} | "
                 f"{ref['mean']:+.5f} [{ref['lo']:+.5f}, {ref['hi']:+.5f}] {ref['sign']} |" if np.isfinite(ref["mean"]) else
                 f"| {k} | {v['attempted']}/{v['R']} | {p['POSITIVE']} | {p['NEGATIVE']} | {p['UNRESOLVED']} | {p['UNAVAILABLE']} | UNAVAILABLE |")
    L += ["", f"gate (b) {out['gate_b']['passed']}: " + ", ".join(f"{k} {v['bad']}/{v['attempted']}" for k, v in out['gate_b']['settings'].items()),
          f"gate (c) T1 {out['gate_c']}", f"gate (e) E1 {out['gate_e']}", f"V2 {out['completion_v2']['passed']}",
          f"T2 {out['T2']}, T3 {out['T3']}"]
    if "rise" in out:
        L.append(f"rise {out['rise']}; inherited calls {out.get('inherited_calls')}")
    L.append(f"recovery flags: {json.dumps({k: v.get('flag') for k, v in out['recovery'].items()})}")
    for fam, v in out["recovery"].items():
        if "rules" in v:
            for rn, rv in v["rules"].items():
                L.append(f"  {fam} {rn}: {json.dumps(rv, default=str)[:300]}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bases")
    a4 = sub.add_parser("s4a"); a4.add_argument("--workers", type=int, default=12)
    a4.add_argument("--shard", default=None, help="i/K: this host's hash shard of every S4a batch (K hosts share the result prefix)")
    a4.add_argument("--wait-h", type=float, default=0.0, help="how long a shard waits for the others at each barrier")
    q = sub.add_parser("s4b-queue"); q.add_argument("--kind", default="all", choices=["cv", "rec", "all"])
    b4 = sub.add_parser("s4b"); b4.add_argument("--workers", type=int, default=12); b4.add_argument("--shard", default=None)
    b4.add_argument("--kind", default="all", choices=["cv", "rec", "all"])
    b4.add_argument("--defer", default=None, help="T2 or T2,T3: invoke the §8 time-priority amendment (recorded before the batch)")
    b4.add_argument("--defer-reason", default="time-priority amendment, DESIGN rev 7 §8 (owner's submission window)")
    sub.add_parser("evaluate")
    sm = sub.add_parser("smoke"); sm.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    if a.cmd == "bases":
        b = load_bases()
        print(f"[s4] cached {len(b)} bases with W53 -> {bases_path()}")
    elif a.cmd == "s4a":
        s4a(a.workers, a.shard, a.wait_h * 3600.0)
    elif a.cmd == "s4b-queue":
        tasks = s4b_tasks(a.kind)
        todo = pending(tasks)
        print(f"[s4] S4b {a.kind}: {len(tasks)} tasks, {len(todo)} pending; deferred {deferred_settings() or 'none'}")
    elif a.cmd == "s4b":
        s4b(a.workers, a.shard, a.kind, a.defer.split(",") if a.defer else None, a.defer_reason)
    elif a.cmd == "evaluate":
        out = evaluate()
        print(summary_markdown(out))
    elif a.cmd == "smoke":
        # one task of each kind on development-stage seeds into results/s4_smoke (never the S4 folders)
        global S4_DIR
        S4_DIR = os.path.join(HERE, "results", "s4_smoke")
        bases = load_bases()
        t0 = _time.time()
        tasks = [dict(kind="cv", stage="development", setting=s, r=0, m=0, base=set_members("development", s, 0)[0],
                      models=(EPS_MODELS if s == "EPS" else DECISION_MODELS), inherited=(s in ("W3", "O5")),
                      lam={"E1": 0.6, "T3": 0.8}, path=cv_path("development", s, 0, 0))
                 for s in ("EPS", "W3", "O5", "T2", "E1", "LAM@0.5")]
        tasks += [dict(kind="c0", family="G", config=10, i=0, path=os.path.join(S4_DIR, "c0", "G", "S10_d0.json"))]
        tasks += [dict(kind="rec", setting="40|fitted", config=10, i=0, path=os.path.join(S4_DIR, "rec", "40_fitted", "S10_r0.json")),
                  dict(kind="rec", setting="O1", config=13, i=0, path=os.path.join(S4_DIR, "rec", "O1", "S13_r0.json"))]
        run_queue(pending(tasks), a.workers, bases, c0={"G": 3.84, "B": 3.84}, label="smoke")
        for t in tasks:
            with open(t["path"]) as f:
                r = json.load(f)
            if t["kind"] == "cv":
                print(f"  {t['setting']:8s} scores {r['scores']} {r['seconds']:.0f} s inherited {'yes' if 'inherited_lme' in r else 'no'}")
            elif t["kind"] == "c0":
                print(f"  c0 G S10: q0 {r['q0']} {r['seconds']:.0f} s")
            else:
                g = r["families"]["G"]; b = r["families"]["B"]
                print(f"  rec {t['setting']}: G s_tau {g['s_tau_hat']} profile {None if g['profile'] is None else (g['profile']['status'], g['profile']['lo'], g['profile']['hi'])}; "
                      f"B s_tau {b['s_tau_hat']} profile {None if b['profile'] is None else (b['profile']['status'], b['profile']['lo'], b['profile']['hi'])}; {r['seconds']:.0f} s")
        print(f"[s4] smoke done in {_time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
