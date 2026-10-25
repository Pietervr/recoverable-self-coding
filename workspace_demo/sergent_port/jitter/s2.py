#!/usr/bin/env python3
"""jitter/s2.py — stage S2 of DESIGN_jitter.md rev 6: development on DEVELOPMENT seeds (W2, T1, O1 at R = 25),
the start-basin report and the development reading of the decision batch. Nothing here feeds a gate or flag
(§0: only S4b batches do); numerical repairs found here are declared in the code and reviewed at S3.

    s2.py bases                         cache the base participants' levels/blocks (results/generators/bases.json)
    s2.py decision --setting W2 --R 25  the §7.3 decision batch (G2, B2, G3+, B3+ = 80 starts per participant-dataset,
                                        5 block folds, held-out score) on R replicate sets of 20 synthetic participants
                                        drawn with replacement from the 20 generator configurations (§7.2)
    s2.py summary                       set-level primaries, UNAVAILABLE and convergence statistics, selection rates,
                                        start basins, timing -> results/s2/decision/summary.{json,md}

Per set: results/s2/decision/<setting>/set_<r>.json (scores, statuses, selections, start statuses and objectives);
the start end points (every start's x) go to results/s2/archive/<setting>/set_<r>.npz (kept out of git).
Seeds: seed_for('development', setting, r, member) for the data, seed_for('development', setting, r, 0, 'set') for
the base draw; development seeds never recur in S4a/S4b (§7.7).
"""
from __future__ import annotations

import os

os.environ.setdefault("NPROC", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time as _time  # noqa: E402

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data as D  # noqa: E402
import decide as X  # noqa: E402
import fit as F  # noqa: E402
import models as M  # noqa: E402
import simulate as S  # noqa: E402

GEN_DIR = os.path.join(HERE, "results", "generators")
S2_DIR = os.path.join(HERE, "results", "s2")
DEC_DIR = os.path.join(S2_DIR, "decision")
ARC_DIR = os.path.join(S2_DIR, "archive")
SETTINGS = {"W2": ("G3", "W"), "T1": ("B3", "W"), "O1": ("G3", "O1")}
DECISION_SPECS = ("G2", "G3+", "B2", "B3+")
SUBJECTS = list(range(1, 21))


# ----------------------------------------------------------------------------------------------
# bases and sets
# ----------------------------------------------------------------------------------------------
def bases_path(session="active"):
    return os.path.join(GEN_DIR, f"bases_{session}.json")


def cache_bases(session="active"):
    out = {}
    for s in SUBJECTS:
        p = D.load_participant(s, session)
        out[str(s)] = dict(levels=p.levels.tolist(), blocks=p.blocks.tolist(), n=p.n, data_id=p.data_id)
    with open(bases_path(session), "w") as f:
        json.dump(out, f)
    return out


def load_bases(session="active"):
    if not os.path.exists(bases_path(session)):
        return cache_bases(session)
    with open(bases_path(session)) as f:
        return json.load(f)


def load_config(subject: int, model: str, session="active") -> F.GeneratorConfig:
    return F.GeneratorConfig.from_npz(os.path.join(GEN_DIR, f"S{subject}_{session}_{model}.npz"))


def set_members(setting: str, r: int, stage: str = "development") -> list:
    """The 20 base subjects of replicate set r (drawn with replacement, seeded)."""
    rng = np.random.default_rng(S.seed_for(stage, setting, r, 0, "set"))
    return [int(s) for s in rng.choice(SUBJECTS, size=20, replace=True)]


def make_synthetic(setting: str, r: int, m: int, base_subject: int, bases: dict, stage: str = "development",
                   session: str = "active") -> D.Participant:
    model, mode = SETTINGS[setting]
    cfg = load_config(base_subject, model, session)
    if setting == "O1":
        cfg = S.with_nuisance(cfg, 0.0, cfg.s_g)          # zero latency jitter, s_g at the fitted G3 value
    b = bases[str(base_subject)]
    seed = S.seed_for(stage, setting, r, m)
    syn = S.generate(cfg, np.asarray(b["levels"]), np.asarray(b["blocks"]), seed, mode)
    p = syn.participant(subject=1000 * r + m)
    p.tag = f"{setting}-r{r}-m{m}-S{base_subject}"
    return p


# ----------------------------------------------------------------------------------------------
# the decision batch on one participant-dataset
# ----------------------------------------------------------------------------------------------
def _start_rows(r: F.FitResult):
    return [dict(label=s.label, status=s.status, f=s.f, pg=s.pg, nit=s.nit, nfev=s.nfev, retries=s.retries,
                 early=s.early, seconds=s.seconds) for s in r.starts]


def decision_task(setting: str, r: int, m: int, base_subject: int, bases: dict, span_name: str = "primary",
                  quad: dict | None = None, g_rule: tuple | None = None, archive: bool = False,
                  extra_warm: dict | None = None) -> dict:
    """`g_rule` = (models.QUAD_G_RULE, models.QUAD_G_REFIT_SG) to apply in THIS process (a loky worker imports models
    afresh, so the two-pass check passes the rule explicitly as well as through the environment); None = as imported.
    `archive` (the repaired node checks, 25 Oct 2026) adds every candidate's and selected fit's θ (float64) to the row
    and θ/Σ (float64) to the start archive, so that a check's endpoints can be re-evaluated or transported exactly.
    `extra_warm` = {(fold, candidate name): [(label, θ, Σ)]} further warm EM chains for the candidates, started under
    the given Σ with the fold's training-catch μ0 (the 121-node recheck warm-started from the 61-node endpoints).
    Every candidate row carries `numerical_failure` and the `polish` record; the row lists its failures."""
    os.environ.setdefault("NPROC", "1")
    if g_rule is not None:
        M.QUAD_G_RULE, M.QUAD_G_REFIT_SG = str(g_rule[0]), float(g_rule[1])
    t0 = _time.time()
    p = make_synthetic(setting, r, m, base_subject, bases)
    sp_ = D.span(span_name)
    cache = F.FitCache()
    sums = {"G3": [], "B3": []}
    folds = []
    xs = {}
    fits_seen = []
    failures = []
    polish = dict(calls=0, accepted=0, seconds=0.0)
    fit_seconds = 0.0
    for fold in range(5):
        train, test, _, _ = D.fold_datasets(p, sp_, fold)
        warm = None
        if extra_warm:
            warm = {}
            for name in DECISION_SPECS:
                chains = extra_warm.get((fold, name)) or extra_warm.get(f"f{fold}_{name}") or []
                if chains:
                    warm[name] = [(lab, np.asarray(th, dtype=np.float64),
                                   D.whitening_from_sigma(train.wh.mu0, np.asarray(Sg, dtype=np.float64), 0.0, train.wh.n_catch))
                                  for lab, th, Sg in chains]
        res = F.fit_all_models(train, cache, span_name, ("G3", "B3"), quad, extra_warm=warm or None)
        row = dict(fold=fold, n_train=train.n, n_test=test.n, shrinkage=train.wh.shrinkage, fits={})
        for name in DECISION_SPECS:
            fr = res[name]
            fits_seen.append(fr)
            sp_n = F.selected_spec(name, fr, span_name, quad)
            row["fits"][name] = dict(status=fr.status, loglik=fr.loglik, n_converged=fr.n_converged,
                                     bounds_hit=fr.bounds_hit, clipped=fr.clipped, notes=fr.notes,
                                     starts=_start_rows(fr), seconds=fr.seconds, quad=fr.quad,
                                     numerical_failure=bool(fr.numerical_failure), polish=dict(fr.polish),
                                     em_iterations=fr.em_iterations, em_trace=fr.em_trace,
                                     s_g=(float(M.unpack(sp_n, fr.theta).s_g) if (fr.available and sp_n.scale_free) else None),
                                     s_tau_ms=(float(M.unpack(sp_n, fr.theta).s_tau_ms) if fr.available else None))
            if fr.numerical_failure:
                failures.append(f"f{fold}_{name}")
            for k in ("calls", "accepted", "seconds"):
                polish[k] += (fr.polish or {}).get(k, 0)
            fit_seconds += fr.seconds
            for i, s in enumerate(fr.starts):
                xs[f"f{fold}_{name}_s{i}"] = np.asarray(s.x, dtype=np.float32)
            if archive and fr.available:
                row["fits"][name]["theta"] = [float(v) for v in fr.theta]
                xs[f"f{fold}_{name}_theta64"] = np.asarray(fr.theta, dtype=np.float64)
                if fr.wh is not None:
                    xs[f"f{fold}_{name}_sigma64"] = np.asarray(fr.wh.Sigma, dtype=np.float64)
        for sel in ("G3", "B3"):
            fr = res[sel]
            fits_seen.append(fr)
            row["fits"][sel] = dict(status=fr.status, loglik=fr.loglik, selection=fr.selection, flags=fr.flags,
                                    candidates=fr.candidates, quad=fr.quad, numerical_failure=bool(fr.numerical_failure))
            if fr.available:
                sp = F.selected_spec(sel, fr, span_name, quad)
                ll = F.score_heldout(sp, fr, test)
                sums[sel].append(float(np.sum(ll)))
                xs[f"f{fold}_{sel}_theta"] = np.asarray(fr.theta, dtype=np.float32)
                if fr.wh is not None:
                    xs[f"f{fold}_{sel}_sigma"] = np.asarray(fr.wh.Sigma, dtype=np.float32)
                row["fits"][sel].update(em_iterations=fr.em_iterations, em_trace=fr.em_trace)
                if archive:
                    row["fits"][sel]["theta"] = [float(v) for v in fr.theta]
                    xs[f"f{fold}_{sel}_theta64"] = np.asarray(fr.theta, dtype=np.float64)
                    if fr.wh is not None:
                        xs[f"f{fold}_{sel}_sigma64"] = np.asarray(fr.wh.Sigma, dtype=np.float64)
            else:
                sums[sel].append(float("nan"))
        folds.append(row)
    n = D.n_scored(p)
    scores = {k: (float(np.nansum(v) / n) if not np.any(np.isnan(v)) else float("nan")) for k, v in sums.items()}
    return dict(setting=setting, r=r, m=m, base=base_subject, data_id=p.data_id, n_trials=p.n, n_scored=n,
                scores=scores, fold_sums=sums, folds=folds, seconds=_time.time() - t0, code_hash=M.code_hash(),
                quad=quad or {}, quad_rule=F.quad_rule_record(fits_seen), numerical_failures=failures,
                polish=polish, fit_seconds=fit_seconds, _xs=xs)


PARALLEL_BACKEND = "loky"          # tests switch to "threading" so that a monkeypatched task is seen by the workers


def task_paths(setting: str, r: int, m: int) -> tuple:
    """(json, npz) of one participant-dataset's own result files: the resume unit of the decision batch on an
    interruptible host. The json lives under decision/<setting>/tasks (synced), the start archive under
    archive/<setting>/tasks (not synced, not needed for any reading)."""
    return (os.path.join(DEC_DIR, setting, "tasks", f"set_{r}_m{m}.json"),
            os.path.join(ARC_DIR, setting, "tasks", f"set_{r}_m{m}.npz"))


def decision_task_to_file(setting: str, r: int, m: int, base_subject: int, bases: dict, span_name: str,
                          json_path: str, npz_path: str) -> str:
    if os.path.exists(json_path):
        return json_path
    row = decision_task(setting, r, m, base_subject, bases, span_name)
    xs = row.pop("_xs")
    os.makedirs(os.path.dirname(npz_path), exist_ok=True)
    np.savez_compressed(npz_path, **xs)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    tmp = json_path + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(row, f)
    os.replace(tmp, json_path)
    return json_path


def run_decision(setting: str, R: int, workers: int, sets=None, span_name: str = "primary"):
    """Every pending set's participant-datasets in ONE queue (R × 20 tasks), so that a 96-core host is full from the
    first minute — the set-by-set form (one Parallel call per set of 20) kept 76 of 96 cores idle on the AWS closure
    of 24 Oct 2026. Each task writes its own file first (the resume unit); the per-set records (set_<r>.json and the
    archive npz, unchanged in form) are assembled from them after the queue and the task files are removed.
    `wall_s` of a set is now the SUM of its tasks' seconds; `queue_wall_s` is the queue's wall."""
    from joblib import Parallel, delayed
    bases = load_bases()
    out_dir = os.path.join(DEC_DIR, setting)
    arc_dir = os.path.join(ARC_DIR, setting)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(arc_dir, exist_ok=True)
    sets = list(range(R)) if sets is None else sets
    todo = []
    for r in sets:
        if os.path.exists(os.path.join(out_dir, f"set_{r}.json")):
            print(f"[s2] {setting} set {r}: exists, skipped", flush=True)
        else:
            todo.append(r)
    # a second host on the same setting works the list from its far end (sets reversed by the CLI) and the members of
    # each set in reverse too, so the two hosts meet in the middle with the least duplicated work
    rev = len(todo) > 1 and todo[0] > todo[-1]
    jobs = [(r, m, s) + task_paths(setting, r, m) for r in todo
            for m, s in (reversed(list(enumerate(set_members(setting, r)))) if rev else enumerate(set_members(setting, r)))]
    pending_jobs = [j for j in jobs if not os.path.exists(j[3])]
    t0 = _time.time()
    print(f"[s2] {setting}: {len(todo)} sets, {len(pending_jobs)} of {len(jobs)} participant-datasets pending, "
          f"{workers} workers, start {_time.strftime('%H:%M:%SZ', _time.gmtime())}", flush=True)
    if pending_jobs:
        Parallel(n_jobs=workers, backend=PARALLEL_BACKEND)(
            delayed(decision_task_to_file)(setting, r, m, s, bases, span_name, jp, npz) for r, m, s, jp, npz in pending_jobs)
    wall = _time.time() - t0
    print(f"[s2] {setting}: queue done in {wall:.0f} s", flush=True)
    for r in todo:
        assemble_set(setting, r, workers, wall, remove_task_files=True)


def assemble_set(setting: str, r: int, workers: int = 0, queue_wall_s: float = 0.0, remove_task_files: bool = True) -> dict:
    """The per-set record (set_<r>.json + archive npz, the pre-queue form) from the 20 task files of set r. Another host
    may assemble a set it did not compute (the checks instance assembles W2 set 0 for the node check as soon as the W2
    host's first round has landed on S3; it keeps the task files)."""
    out_dir = os.path.join(DEC_DIR, setting)
    arc_dir = os.path.join(ARC_DIR, setting)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(arc_dir, exist_ok=True)
    members = set_members(setting, r)
    rows, xs, used = [], {}, []
    for m in range(len(members)):
        jp, npz = task_paths(setting, r, m)
        with open(jp) as f:
            rows.append(json.load(f))
        used.append(jp)
        if os.path.exists(npz):                       # the archive is not synced: tolerate a lost npz after a resume
            with np.load(npz) as z:
                for k in z.files:
                    xs[f"m{m}_{k}"] = z[k]
            used.append(npz)
    np.savez_compressed(os.path.join(arc_dir, f"set_{r}.npz"), **xs)
    set_scores = {f"m{row['m']}": row["scores"] for row in rows}
    primary = X.set_primary(set_scores)
    failures = [f"m{row['m']}:{k}" for row in rows for k in row.get("numerical_failures", [])]
    rec = dict(setting=setting, r=r, members=members, primary=primary,
               delta3={k: (v["B3"] - v["G3"]) for k, v in set_scores.items()},
               participants=rows, wall_s=float(sum(row["seconds"] for row in rows)), queue_wall_s=queue_wall_s,
               workers=workers, code_hash=M.code_hash(),
               numerical_failure=bool(failures), numerical_failures=failures)
    path = os.path.join(out_dir, f"set_{r}.json")
    tmp = path + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(rec, f)
    os.replace(tmp, path)
    if remove_task_files:
        for p in used:
            os.remove(p)
    avail = sum(1 for v in set_scores.values() if np.isfinite(v["B3"] - v["G3"]))
    print(f"[s2] {setting} set {r}: primary {primary}, {avail}/20 available, {rec['wall_s']:.0f} task-s "
          f"(mean {rec['wall_s'] / len(rows):.0f} s per participant-dataset)", flush=True)
    return rec


# ----------------------------------------------------------------------------------------------
# summary
# ----------------------------------------------------------------------------------------------
def _load_sets(setting: str) -> list:
    d = os.path.join(DEC_DIR, setting)
    if not os.path.isdir(d):
        return []
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.startswith("set_") and fn.endswith(".json"):
            with open(os.path.join(d, fn)) as f:
                out.append(json.load(f))
    return out


def summarize() -> dict:
    out = {}
    for setting in SETTINGS:
        sets = _load_sets(setting)
        if not sets:
            continue
        prim = [s["primary"] for s in sets]
        deltas = [v for s in sets for v in s["delta3"].values() if v is not None and np.isfinite(v)]
        per_spec = {n: dict(starts=0, converged=0, retries=0, early=0, unavailable=0, fits=0, seconds=0.0,
                            best_not_first=0, improved_by_later_start=0, nit=0.0, max_gap_nat=0.0) for n in DECISION_SPECS}
        sel_rate = {"G3": dict(REDUCED=0, POSITIVE=0, flags={}), "B3": dict(REDUCED=0, POSITIVE=0, flags={})}
        set_wall, task_secs, n_part, n_unavail_part = [], [], 0, 0
        for s in sets:
            set_wall.append(s["wall_s"])
            for part in s["participants"]:
                n_part += 1
                task_secs.append(part["seconds"])
                if not (np.isfinite(part["scores"]["G3"]) and np.isfinite(part["scores"]["B3"])):
                    n_unavail_part += 1
                for fold in part["folds"]:
                    for n in DECISION_SPECS:
                        fr = fold["fits"][n]
                        ps = per_spec[n]
                        ps["fits"] += 1
                        ps["seconds"] += fr["seconds"]
                        ps["unavailable"] += fr["status"] != "AVAILABLE"
                        conv = [st for st in fr["starts"] if st["status"] == "CONVERGED"]
                        for st in fr["starts"]:
                            ps["starts"] += 1
                            ps["converged"] += st["status"] == "CONVERGED"
                            ps["retries"] += st["retries"]
                            ps["early"] += st["early"]
                            ps["nit"] += st["nit"]
                        if conv:
                            best = min(conv, key=lambda st: st["f"])
                            first = fr["starts"][0]
                            if best is not first and best["label"] != first["label"]:
                                ps["best_not_first"] += 1
                            # did any start beyond the first improve on the first start's objective (if converged)?
                            if first["status"] == "CONVERGED":
                                gap = first["f"] - best["f"]
                                if gap > 1e-6 * max(1.0, abs(best["f"])):
                                    ps["improved_by_later_start"] += 1
                                ps["max_gap_nat"] = max(ps["max_gap_nat"], gap)
                    for sel in ("G3", "B3"):
                        fr = fold["fits"][sel]
                        if fr["status"] == "AVAILABLE":
                            sel_rate[sel][fr["selection"]] += 1
                        for fl in fr.get("flags", []):
                            sel_rate[sel]["flags"][fl] = sel_rate[sel]["flags"].get(fl, 0) + 1
        for n, ps in per_spec.items():
            ps["seconds_per_start"] = ps["seconds"] / max(ps["starts"], 1)
            ps["nit_mean"] = ps["nit"] / max(ps["starts"], 1)
            ps["converged_frac"] = ps["converged"] / max(ps["starts"], 1)
        out[setting] = dict(
            R=len(sets), primaries={k: prim.count(k) for k in (X.POSITIVE, X.NEGATIVE, X.UNRESOLVED, X.UNAVAILABLE)},
            delta3_mean=float(np.mean(deltas)) if deltas else None, delta3_sd=float(np.std(deltas, ddof=1)) if len(deltas) > 1 else None,
            set_means=[float(np.nanmean(list(s["delta3"].values()))) for s in sets],
            participants=n_part, participants_unavailable=n_unavail_part,
            per_spec=per_spec, selection=sel_rate, set_wall_s_mean=float(np.mean(set_wall)),
            task_seconds_mean=float(np.mean(task_secs)), starts_total=sum(ps["starts"] for ps in per_spec.values()))
    os.makedirs(DEC_DIR, exist_ok=True)
    with open(os.path.join(DEC_DIR, "summary.json"), "w") as f:
        json.dump(out, f, indent=1)
    md = summary_markdown(out)
    with open(os.path.join(DEC_DIR, "summary.md"), "w") as f:
        f.write(md)
    return out


def summary_markdown(out: dict) -> str:
    L = ["# S2 decision batches on development seeds — reading, not a gate", "",
         "Set-level primary = sign of the Δ₃ = S_B3 − S_G3 t-interval over the set's available participants "
         "(UNAVAILABLE if fewer than 16). W2/O1 are graded generators (a POSITIVE set is a false call), T1 the "
         "two-state generator (a POSITIVE set is a detection). Start basins: 'best≠first' = the selected optimum came "
         "from a start other than the first; 'improved' = a later start beat a CONVERGED first start by > 1e-6 relative.", ""]
    L.append("| setting | R | POSITIVE | NEGATIVE | UNRESOLVED | UNAVAILABLE | Δ₃ mean (sd) per participant | set-mean Δ₃ range | participants unavailable | s per participant-dataset |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for st, o in out.items():
        pr = o["primaries"]
        sm = o["set_means"]
        L.append(f"| {st} | {o['R']} | {pr['POSITIVE']} | {pr['NEGATIVE']} | {pr['UNRESOLVED']} | {pr['UNAVAILABLE']} | "
                 f"{o['delta3_mean']:+.5f} ({o['delta3_sd']:.5f}) | [{min(sm):+.5f}, {max(sm):+.5f}] | "
                 f"{o['participants_unavailable']}/{o['participants']} | {o['task_seconds_mean']:.1f} |")
    L.append("")
    L.append("| setting | spec | starts | s/start | nit | converged | retries | early | fits UNAVAILABLE | best≠first | improved | max gap nat |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for st, o in out.items():
        for n, ps in o["per_spec"].items():
            L.append(f"| {st} | {n} | {ps['starts']} | {ps['seconds_per_start']:.3f} | {ps['nit_mean']:.0f} | "
                     f"{ps['converged_frac']:.3f} | {ps['retries']} | {ps['early']} | {ps['unavailable']}/{ps['fits']} | "
                     f"{ps['best_not_first']}/{ps['fits']} | {ps['improved_by_later_start']}/{ps['fits']} | {ps['max_gap_nat']:.3f} |")
    L.append("")
    for st, o in out.items():
        for sel in ("G3", "B3"):
            s = o["selection"][sel]
            L.append(f"{st} {sel}: REDUCED {s['REDUCED']}, POSITIVE {s['POSITIVE']}, flags {s['flags']}.")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------------
# §4 checks: node counts (refits), Jacobian ranks, small-spread behaviour
# ----------------------------------------------------------------------------------------------
CHECK_DIR = os.path.join(S2_DIR, "checks")


def node_check(setting: str, r: int, quad: dict, label: str, workers: int) -> dict:
    """Refit replicate set r of `setting` under `quad` and compare every participant's Δ₃ with the archived
    (default-rule) Δ₃: pass if max |ΔΔ₃| < one tenth of the set's Δ₃ interval half-width (§4)."""
    from joblib import Parallel, delayed
    with open(os.path.join(DEC_DIR, setting, f"set_{r}.json")) as f:
        ref = json.load(f)
    bases = load_bases()
    members = ref["members"]
    t0 = _time.time()
    rows = Parallel(n_jobs=workers, backend="loky")(
        delayed(decision_task)(setting, r, m, s, bases, "primary", quad) for m, s in enumerate(members))
    d_ref = {f"m{m}": ref["delta3"][f"m{m}"] for m in range(20)}
    d_new = {f"m{row['m']}": row["scores"]["B3"] - row["scores"]["G3"] for row in rows}
    both = [k for k in d_ref if np.isfinite(d_ref[k]) and np.isfinite(d_new[k])]
    vals = np.array([d_ref[k] for k in both])
    iv = X.t_interval(vals)
    half = 0.5 * (iv.hi - iv.lo) if np.isfinite(iv.hi) else float("nan")
    diffs = {k: d_new[k] - d_ref[k] for k in both}
    worst = max(abs(v) for v in diffs.values()) if diffs else float("nan")
    out = dict(setting=setting, r=r, label=label, quad=quad, n_compared=len(both), half_width=half,
               tolerance=0.1 * half, max_abs_change=worst, passed=bool(worst < 0.1 * half), changes=diffs,
               delta3_ref=d_ref, delta3_new=d_new, primary_ref=ref["primary"],
               primary_new=X.set_primary({f"m{row['m']}": row["scores"] for row in rows}),
               seconds=_time.time() - t0,
               mean_seconds_per_dataset=float(np.mean([row["seconds"] for row in rows])))
    os.makedirs(CHECK_DIR, exist_ok=True)
    with open(os.path.join(CHECK_DIR, f"nodes_{label}_{setting}_set{r}.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"[s2 checks] {label} {setting} set {r}: max |ΔΔ₃| {worst:.2e} vs tolerance {0.1 * half:.2e} -> "
          f"{'PASS' if out['passed'] else 'FAIL'}; primary {ref['primary']} -> {out['primary_new']}; {out['seconds']:.0f} s", flush=True)
    return out


AWS_CHECK_DIR = os.path.join(S2_DIR + "_aws", "checks")      # the closure fleet's check files, pulled from S3


def twopass_check(setting: str, r: int, workers: int, refit_sg: float = M.QUAD_G_REFIT_SG, ref_path: str | None = None,
                  label: str | None = None) -> dict:
    """The two-pass scale quadrature (models.QUAD_G_RULE "17then33" at threshold `refit_sg`; DESIGN §4, declared 25 Oct
    2026 for the Codex S3 re-review) against the blanket 33-node reference of the §4 node check: replicate set r of
    `setting` is refitted under the two-pass rule and every participant's Δ₃ = S_B3 − S_G3 is compared with `delta3_new`
    of the reference file (nodes_g33_<setting>_set<r>.json from the checks host, pulled to results/s2_aws/checks/). PASS
    if max |Δ₃(two-pass) − Δ₃(33)| < the tolerance recorded there (one tenth of the set's Δ₃ interval half-width).
    Also recorded: the refit counts per model and the fraction of the eligible candidate fits refitted, the fitted s_g
    of every candidate, the task seconds against the archived 17-node seconds of the same set on this machine, the
    within-run multiplier (all fit seconds / their 17-node seconds, independent of the machine's load), and the set
    primaries under 17, 33 and the two-pass rule. The rule reaches the loky workers explicitly (decision_task's
    `g_rule`) and through the environment (JITTER_QUAD_G_RULE / JITTER_QUAD_G_REFIT_SG, read by models.py at import)."""
    from joblib import Parallel, delayed
    ref_path = os.path.join(AWS_CHECK_DIR, f"nodes_g33_{setting}_set{r}.json") if ref_path is None else ref_path
    with open(ref_path) as f:
        ref = json.load(f)
    with open(os.path.join(DEC_DIR, setting, f"set_{r}.json")) as f:
        arch = json.load(f)
    rule = ("17then33", float(refit_sg))
    os.environ["JITTER_QUAD_G_RULE"], os.environ["JITTER_QUAD_G_REFIT_SG"] = rule[0], f"{rule[1]:g}"
    M.QUAD_G_RULE, M.QUAD_G_REFIT_SG = rule
    label = (f"sg{refit_sg:g}" if label is None else label)
    bases = load_bases()
    members = arch["members"]
    t0 = _time.time()
    rows = Parallel(n_jobs=workers, backend="loky")(
        delayed(decision_task)(setting, r, m, s, bases, "primary", None, rule) for m, s in enumerate(members))
    rows = sorted(rows, key=lambda row: row["m"])
    d17 = {f"m{m}": arch["delta3"][f"m{m}"] for m in range(len(members))}
    d33 = {f"m{m}": ref["delta3_new"][f"m{m}"] for m in range(len(members))}
    d_tp = {f"m{row['m']}": row["scores"]["B3"] - row["scores"]["G3"] for row in rows}
    both = [k for k in d33 if np.isfinite(d33[k]) and np.isfinite(d_tp[k])]
    diffs = {k: d_tp[k] - d33[k] for k in both}
    worst = max(abs(v) for v in diffs.values()) if diffs else float("nan")
    tol = float(ref["tolerance"])
    # refits: per model over the 20 × 5 candidate fits, and the within-run cost split of every fit
    per_model, s_g, refit_rows = {}, {}, {}
    secs_all = secs_17 = 0.0
    for row in rows:
        k = f"m{row['m']}"
        s_g[k], refit_rows[k] = {}, {}
        for fold in row["folds"]:
            for name in DECISION_SPECS:
                fr = fold["fits"][name]
                c = per_model.setdefault(name, dict(fits=0, refitted=0))
                c["fits"] += 1
                q = fr.get("quad") or {}
                refit = q.get("refit_from") is not None
                c["refitted"] += int(refit)
                s_g[k][f"f{fold['fold']}_{name}"] = fr.get("s_g")
                if refit:
                    refit_rows[k][f"f{fold['fold']}_{name}"] = dict(s_g=q.get("refit_s_g"), loglik_before=q.get("loglik_before"),
                                                                   loglik=fr["loglik"], seconds_before=q.get("seconds_before"),
                                                                   seconds=fr["seconds"])
                secs_all += fr["seconds"]
                secs_17 += q.get("seconds_before", fr["seconds"]) if refit else fr["seconds"]
    eligible = sum(c["fits"] for c in per_model.values())
    refitted = sum(c["refitted"] for c in per_model.values())
    task_tp = float(sum(row["seconds"] for row in rows))
    task_17 = float(sum(p["seconds"] for p in arch["participants"]))
    out = dict(setting=setting, r=r, label=label, rule=dict(rule=rule[0], refit_sg=rule[1], refit_nodes=M.QUAD_G_REFIT_NODES),
               reference=os.path.relpath(ref_path, HERE), reference_label=ref.get("label"), tolerance=tol,
               half_width=ref.get("half_width"), n_compared=len(both), max_abs_diff_vs_33=worst, passed=bool(worst < tol),
               diffs_vs_33=diffs, diffs_vs_17={k: d_tp[k] - d17[k] for k in both},
               delta3_twopass=d_tp, delta3_33=d33, delta3_17=d17,
               primary_17=arch["primary"], primary_33=ref.get("primary_new"),
               primary_twopass=X.set_primary({f"m{row['m']}": row["scores"] for row in rows}),
               refits=dict(per_model=per_model, eligible_fits=eligible, refitted_fits=refitted,
                           fraction=(refitted / eligible if eligible else None),
                           participants_with_refit=sorted(k for k, v in refit_rows.items() if v), detail=refit_rows),
               fitted_s_g=s_g,
               cost=dict(fit_seconds_all=secs_all, fit_seconds_17_within_run=secs_17,
                         within_run_multiplier=(secs_all / secs_17 if secs_17 else None),
                         task_seconds_twopass=task_tp, task_seconds_17_archived=task_17,
                         task_multiplier_vs_archive=(task_tp / task_17 if task_17 else None),
                         workers_twopass=workers, workers_17=arch.get("workers"),
                         mean_task_seconds_twopass=task_tp / len(rows), mean_task_seconds_17=task_17 / len(arch["participants"]),
                         note="both on the Mac; the archived 17-node set ran alone at 12 workers, the two-pass run at "
                              f"{workers} workers beside another job's battery — the within-run multiplier is the load-free figure"),
               seconds=_time.time() - t0, code_hash=M.code_hash(), code_hash_17=arch.get("code_hash"),
               utc=_time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime()), participants=rows)
    for row in out["participants"]:
        row.pop("_xs", None)
    os.makedirs(CHECK_DIR, exist_ok=True)
    path = os.path.join(CHECK_DIR, f"twopass_g_{setting}_set{r}.json" if abs(refit_sg - 0.6) < 1e-12
                        else f"twopass_g_{label}_{setting}_set{r}.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    per_txt = ", ".join(f"{n} {c['refitted']}/{c['fits']}" for n, c in per_model.items())
    print(f"[s2 checks] two-pass {rule} {setting} set {r}: max |Δ₃(two-pass) − Δ₃(33)| {worst:.2e} vs tolerance {tol:.2e} -> "
          f"{'PASS' if out['passed'] else 'FAIL'}; refitted {refitted}/{eligible} candidate fits ({per_txt}); "
          f"within-run multiplier {out['cost']['within_run_multiplier']:.3f}; task seconds {task_tp:.0f} vs archived 17-node {task_17:.0f}; "
          f"primary 17 {arch['primary']} / 33 {ref.get('primary_new')} / two-pass {out['primary_twopass']}; {out['seconds']:.0f} s -> {path}", flush=True)
    return out


# ----------------------------------------------------------------------------------------------
# the repaired same-data, same-code node checks (25 Oct 2026; Codex latency/quadrature review, findings 11, 13, 14)
# ----------------------------------------------------------------------------------------------
REPAIR_T_ABS = 8.8322454e-5      # the declared cap on the tolerance: one tenth of the AWS 31-node reference half-width
REPAIR_RUNS = {                   # label -> (quadrature override, scale rule (QUAD_G_RULE, QUAD_G_REFIT_SG), warm-start source)
    "A": (dict(n_tau_nodes=31, n_g_nodes=17), ("17", 0.6), None),          # the rule to retain if it passes
    "B": (dict(n_tau_nodes=61, n_g_nodes=17), ("17", 0.6), None),
    "C": (dict(n_tau_nodes=31, n_g_nodes=33), ("17", 0.6), None),
    "D": (dict(n_tau_nodes=31, n_g_nodes=17), ("17then33", 0.6), None),    # the final combined rule: 17 then 33 where s_g > 0.6
    "E": (dict(n_tau_nodes=121, n_g_nodes=17), ("17", 0.6), "B"),          # the fallback's recheck, warm-started from B
}
REPAIR_COMPARISONS = (("A", "B"), ("A", "C"), ("D", "C"), ("B", "E"))      # (candidate, reference)


def repair_paths(setting: str, r: int, label: str) -> tuple:
    stem = os.path.join(CHECK_DIR, f"repair_{setting}_set{r}_{label}")
    return stem + ".json", stem + ".npz"


def repair_status(setting: str, r: int, line: str):
    """One line per event to results/s2/checks/repair_<setting>_set<r>_status.txt (the parent reads it)."""
    os.makedirs(CHECK_DIR, exist_ok=True)
    with open(os.path.join(CHECK_DIR, f"repair_{setting}_set{r}_status.txt"), "a") as f:
        f.write(f"{_time.strftime('%Y-%m-%dT%H:%M:%SZ', _time.gmtime())} {line}\n")


def repair_verify_data(setting: str, r: int, ref: dict) -> list:
    """Regenerate every participant-dataset of set r from the stored generators and compare its data identity with the
    archived record's; returns the mismatches (empty = verified)."""
    bases = load_bases()
    out = []
    for m, s in enumerate(ref["members"]):
        p = make_synthetic(setting, r, m, s, bases)
        want = ref["participants"][m]["data_id"]
        if p.data_id != want or ref["participants"][m]["base"] != s:
            out.append(dict(m=m, base=s, regenerated=p.data_id, archived=want))
    return out


def _warm_from_run(setting: str, r: int, label: str) -> dict:
    """{m: {(fold, candidate): [(label, θ, Σ)]}} from an archived repair run: every AVAILABLE candidate's float64 θ and
    Σ (the run must have been made with archive=True)."""
    jp, npz = repair_paths(setting, r, label)
    with open(jp) as f:
        run = json.load(f)
    out = {}
    with np.load(npz) as z:
        for row in run["participants"]:
            m = row["m"]
            per = {}
            for fold in row["folds"]:
                for name in DECISION_SPECS:
                    kt, ks = f"m{m}_f{fold['fold']}_{name}_theta64", f"m{m}_f{fold['fold']}_{name}_sigma64"
                    if kt in z.files and ks in z.files:
                        per[(fold["fold"], name)] = [(f"warm{label}", z[kt], z[ks])]
            out[m] = per
    return out


def repair_run(setting: str, r: int, label: str, workers: int) -> dict:
    """One archived full-procedure run of set r under the quadrature and scale rule of REPAIR_RUNS[label], all twenty
    participant-datasets in one loky queue (Codex finding 13: no nested parallelism), after the data identities have been
    verified against the archived Mac record (results/s2/decision/<setting>/set_<r>.json; a mismatch stops the run).
    Archived per fold and candidate: θ, Σ, training log-likelihood, every start's status/objective/iterations, notes,
    the boundary selection and candidates, each family's held-out fold sums, task seconds, the polish record and the
    numerical-failure flags. Written to results/s2/checks/repair_<setting>_set<r>_<label>.{json,npz}."""
    from joblib import Parallel, delayed
    quad, rule, warm_src = REPAIR_RUNS[label]
    with open(os.path.join(DEC_DIR, setting, f"set_{r}.json")) as f:
        ref = json.load(f)
    mism = repair_verify_data(setting, r, ref)
    if mism:
        repair_status(setting, r, f"{label}: STOPPED before fitting, {len(mism)} data identities differ from the archived record: {mism}")
        raise SystemExit(f"[s2 repair] {label}: data identities differ from {setting} set {r}: {mism}")
    os.environ["JITTER_QUAD_G_RULE"], os.environ["JITTER_QUAD_G_REFIT_SG"] = rule[0], f"{rule[1]:g}"
    M.QUAD_G_RULE, M.QUAD_G_REFIT_SG = rule
    warm = _warm_from_run(setting, r, warm_src) if warm_src else {}
    bases = load_bases()
    members = ref["members"]
    repair_status(setting, r, f"{label}: START quad {quad} rule {rule} warm_from {warm_src} workers {workers} code {M.code_hash()} "
                              f"(20/20 data identities verified against the archived record)")
    t0 = _time.time()
    rows = Parallel(n_jobs=workers, backend="loky")(
        delayed(decision_task)(setting, r, m, s, bases, "primary", quad, rule, True, warm.get(m)) for m, s in enumerate(members))
    rows = sorted(rows, key=lambda row: row["m"])
    wall = _time.time() - t0
    xs = {f"m{row['m']}_{k}": v for row in rows for k, v in row.pop("_xs").items()}
    jp, npz = repair_paths(setting, r, label)
    os.makedirs(CHECK_DIR, exist_ok=True)
    np.savez_compressed(npz, **xs)
    d3 = {f"m{row['m']}": row["scores"]["B3"] - row["scores"]["G3"] for row in rows}
    vals = [v for v in d3.values()]
    complete = all(np.isfinite(v) for v in vals)
    iv = X.t_interval(vals) if complete else None
    half = 0.5 * (iv.hi - iv.lo) if (iv is not None and np.isfinite(iv.hi)) else float("nan")
    failures = [f"m{row['m']}:{k}" for row in rows for k in row["numerical_failures"]]
    pol = dict(calls=sum(row["polish"]["calls"] for row in rows), accepted=sum(row["polish"]["accepted"] for row in rows),
               seconds=float(sum(row["polish"]["seconds"] for row in rows)))
    fit_s = float(sum(row["fit_seconds"] for row in rows))
    task_s = float(sum(row["seconds"] for row in rows))
    out = dict(setting=setting, r=r, label=label, quad=quad, rule=dict(rule=rule[0], refit_sg=rule[1], refit_nodes=M.QUAD_G_REFIT_NODES),
               warm_from=warm_src, code_hash=M.code_hash(), workers=workers,
               utc=_time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime()), data_ids_verified=True,
               members=members, data_ids=[row["data_id"] for row in rows],
               delta3=d3, scores={f"m{row['m']}": row["scores"] for row in rows}, fold_sums={f"m{row['m']}": row["fold_sums"] for row in rows},
               n_available=int(sum(np.isfinite(v) for v in vals)), complete=complete,
               primary=X.set_primary({f"m{row['m']}": row["scores"] for row in rows}),
               interval=None if iv is None else dict(mean=iv.mean, lo=iv.lo, hi=iv.hi), half_width=half,
               numerical_failure=bool(failures), numerical_failures=failures,
               polish=dict(pol, r_extra_work=(pol["seconds"] / (fit_s - pol["seconds"]) if fit_s > pol["seconds"] > 0 else 0.0)),
               cost=dict(fit_seconds=fit_s, task_seconds=task_s, mean_task_seconds=task_s / len(rows), queue_wall_seconds=wall),
               quad_rule=dict(F.quad_rule_record([]), per_model=_merge_counts([row["quad_rule"]["per_model"] for row in rows])),
               participants=rows)
    tmp = jp + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(out, f)
    os.replace(tmp, jp)
    repair_status(setting, r, f"{label}: DONE {out['n_available']}/20 available, primary {out['primary']}, half-width "
                              f"{half:.3e}, numerical failures {len(failures)}, polish {pol['calls']} calls / {pol['accepted']} accepted "
                              f"({pol['seconds']:.0f} s, r {out['polish']['r_extra_work']:.4f}), task-s {task_s:.0f} (mean {task_s / 20:.0f}), "
                              f"wall {wall:.0f} s at {workers} workers -> {os.path.relpath(jp, HERE)}")
    print(f"[s2 repair] {label}: " + open(os.path.join(CHECK_DIR, f"repair_{setting}_set{r}_status.txt")).read().strip().splitlines()[-1], flush=True)
    return out


def _merge_counts(dicts: list) -> dict:
    out = {}
    for d in dicts:
        for name, c in d.items():
            o = out.setdefault(name, dict(fits=0, refitted=0))
            o["fits"] += c["fits"]
            o["refitted"] += c["refitted"]
    return out


def _nesting_rows(run: dict) -> list:
    """Per participant and fold the training deficits l(B) − l(G) of both candidate pairs, with the quadratures;
    a deficit beyond NEST_TOL_REL at the SAME scale quadrature is a nesting failure."""
    out = []
    for row in run["participants"]:
        for fold in row["folds"]:
            for g, b in (("G2", "B2"), ("G3+", "B3+")):
                fg, fb = fold["fits"][g], fold["fits"][b]
                if fg["status"] != "AVAILABLE" or fb["status"] != "AVAILABLE":
                    out.append(dict(m=row["m"], fold=fold["fold"], pair=f"{b}-{g}", deficit=None, same_quad=None,
                                    failure=True, note="candidate UNAVAILABLE"))
                    continue
                qg, qb = (fg.get("quad") or {}).get("n_g_nodes"), (fb.get("quad") or {}).get("n_g_nodes")
                same = qg == qb
                deficit = fb["loglik"] - fg["loglik"]
                fail = bool(same and deficit < -F.NEST_TOL_REL * max(1.0, abs(fg["loglik"])))
                out.append(dict(m=row["m"], fold=fold["fold"], pair=f"{b}-{g}", deficit=deficit, same_quad=same, failure=fail,
                                g_nodes=qg, b_nodes=qb))
    return out


def repair_compare(x: dict, y: dict) -> dict:
    """Candidate run x against reference run y on the full roster (every m0..m19; a participant unavailable in either run
    is a FAILED check, never a shrunken roster — Codex finding 14 on s2.py:395). Tolerance T = min(REPAIR_T_ABS, one tenth
    of the reference run's Δ₃ interval half-width); the candidate's own tenth-of-half-width is reported beside it. PASS =
    all twenty compared, max |Δ₃(x) − Δ₃(y)| < T, no numerical failure in either run, no nesting failure in either run.
    Reported per participant: the Δ₃ difference, which family moved (ΔS_G3, ΔS_B3), and every selection flip per fold."""
    roster = [f"m{m}" for m in range(20)]
    diffs, moved, flips, unavailable = {}, {}, {}, []
    px = {f"m{row['m']}": row for row in x["participants"]}
    py = {f"m{row['m']}": row for row in y["participants"]}
    for k in roster:
        dx, dy = x["delta3"].get(k, float("nan")), y["delta3"].get(k, float("nan"))
        if not (np.isfinite(dx) and np.isfinite(dy)):
            unavailable.append(k)
            diffs[k] = None
            continue
        diffs[k] = dx - dy
        moved[k] = dict(G3=px[k]["scores"]["G3"] - py[k]["scores"]["G3"], B3=px[k]["scores"]["B3"] - py[k]["scores"]["B3"],
                        family=("B3" if abs(px[k]["scores"]["B3"] - py[k]["scores"]["B3"]) >= abs(px[k]["scores"]["G3"] - py[k]["scores"]["G3"]) else "G3"))
        fl = []
        for fx, fy in zip(px[k]["folds"], py[k]["folds"]):
            for sel in ("G3", "B3"):
                sx, sy = fx["fits"][sel].get("selection"), fy["fits"][sel].get("selection")
                if sx != sy:
                    fl.append(dict(fold=fx["fold"], model=sel, candidate=sx, reference=sy))
        flips[k] = fl
    finite = [abs(v) for v in diffs.values() if v is not None]
    worst = max(finite) if finite else float("nan")
    worst_k = max((k for k in diffs if diffs[k] is not None), key=lambda k: abs(diffs[k]), default=None)
    half_y, half_x = y.get("half_width", float("nan")), x.get("half_width", float("nan"))
    T = min(REPAIR_T_ABS, 0.1 * half_y) if np.isfinite(half_y) else REPAIR_T_ABS
    T_both = min(T, 0.1 * half_x) if np.isfinite(half_x) else T
    nest_x = [n for n in _nesting_rows(x) if n["failure"]]
    nest_y = [n for n in _nesting_rows(y) if n["failure"]]
    nf = list(x["numerical_failures"]) + [f"ref:{v}" for v in y["numerical_failures"]]
    passed = bool(not unavailable and np.isfinite(worst) and worst < T and not nf and not nest_x and not nest_y)
    return dict(candidate=x["label"], reference=y["label"], quad_candidate=x["quad"], quad_reference=y["quad"],
                rule_candidate=x["rule"], rule_reference=y["rule"], code_hash=(x["code_hash"], y["code_hash"]),
                same_code=x["code_hash"] == y["code_hash"], same_data=x["data_ids"] == y["data_ids"],
                n_compared=20 - len(unavailable), unavailable=unavailable,
                tolerance=T, tolerance_abs_cap=REPAIR_T_ABS, tenth_half_width_reference=0.1 * half_y, tenth_half_width_candidate=0.1 * half_x,
                passed_at_min_of_both=bool(passed and (not np.isfinite(worst) or worst < T_both)),
                max_abs_diff=worst, worst_participant=worst_k, passed=passed,
                diffs=diffs, over_tolerance=sorted([k for k in diffs if diffs[k] is not None and abs(diffs[k]) >= T], key=lambda k: int(k[1:])),
                moved=moved, selection_flips={k: v for k, v in flips.items() if v},
                numerical_failures=nf, nesting_failures=dict(candidate=nest_x, reference=nest_y),
                primary=dict(candidate=x["primary"], reference=y["primary"]))


def repair_summary(setting: str = "W2", r: int = 0) -> dict:
    """The summary over the runs present: every comparison of REPAIR_COMPARISONS whose two runs exist, the measured r
    (polish seconds / original fit seconds) per run, the D cost against A and C, the LATENCY RULE outcome. Written to
    results/s2/checks/repair_<setting>_set<r>_summary.{json,md}."""
    runs = {}
    for label in REPAIR_RUNS:
        jp, _ = repair_paths(setting, r, label)
        if os.path.exists(jp):
            with open(jp) as f:
                runs[label] = json.load(f)
    comps = {f"{a}_vs_{b}": repair_compare(runs[a], runs[b]) for a, b in REPAIR_COMPARISONS if a in runs and b in runs}
    per_run = {k: dict(code_hash=v["code_hash"], quad=v["quad"], rule=v["rule"]["rule"], primary=v["primary"], n_available=v["n_available"],
                       half_width=v["half_width"], interval=v["interval"], numerical_failures=v["numerical_failures"],
                       polish=v["polish"], cost=v["cost"], workers=v["workers"], utc=v["utc"],
                       refits=v["quad_rule"]["per_model"], nesting_failures=len([n for n in _nesting_rows(v) if n["failure"]]))
               for k, v in runs.items()}
    cost = {}
    if "A" in runs and "D" in runs:
        cost["D_over_A_task_seconds"] = runs["D"]["cost"]["task_seconds"] / runs["A"]["cost"]["task_seconds"]
        cost["D_over_A_fit_seconds"] = runs["D"]["cost"]["fit_seconds"] / runs["A"]["cost"]["fit_seconds"]
    if "A" in runs and "C" in runs:
        cost["C_over_A_task_seconds"] = runs["C"]["cost"]["task_seconds"] / runs["A"]["cost"]["task_seconds"]
    if "A" in runs and "B" in runs:
        cost["B_over_A_task_seconds"] = runs["B"]["cost"]["task_seconds"] / runs["A"]["cost"]["task_seconds"]
    hashes = sorted({v["code_hash"] for v in runs.values()})
    latency = None
    if "A_vs_B" in comps:
        latency = ("RETAIN 31 nodes (A vs B passed; no 121 check owed)" if comps["A_vs_B"]["passed"]
                   else "ADOPT 61 (A vs B failed)" + (f"; B vs E {'PASSED' if comps['B_vs_E']['passed'] else 'FAILED'}" if "B_vs_E" in comps else "; the 61-vs-121 recheck (E) is owed"))
    out = dict(setting=setting, r=r, utc=_time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime()), runs=per_run, one_code_hash=len(hashes) == 1,
               code_hashes=hashes, comparisons=comps, cost=cost, latency_rule=latency,
               verdicts={k: dict(passed=c["passed"], max_abs_diff=c["max_abs_diff"], tolerance=c["tolerance"], worst=c["worst_participant"],
                                 over=c["over_tolerance"], unavailable=c["unavailable"], numerical_failures=len(c["numerical_failures"]),
                                 nesting_failures=len(c["nesting_failures"]["candidate"]) + len(c["nesting_failures"]["reference"]))
                         for k, c in comps.items()})
    os.makedirs(CHECK_DIR, exist_ok=True)
    stem = os.path.join(CHECK_DIR, f"repair_{setting}_set{r}_summary")
    with open(stem + ".json", "w") as f:
        json.dump(out, f, indent=1)
    with open(stem + ".md", "w") as f:
        f.write(repair_summary_markdown(out))
    return out


def repair_summary_markdown(s: dict) -> str:
    L = [f"# Repaired same-data, same-code node checks — {s['setting']} set {s['r']} ({s['utc']})", "",
         f"Code hash{'' if s['one_code_hash'] else 'es (NOT one)'}: {', '.join(s['code_hashes'])}. Tolerance T = min({REPAIR_T_ABS:.7e}, "
         "one tenth of the reference run's Δ₃ interval half-width); PASS needs all twenty participants available in both runs, "
         "max |Δ₃ difference| < T, no numerical failure and no nesting failure in either run.", ""]
    L.append("| run | τ nodes | g nodes | rule | available | primary | half-width | numerical failures | nesting failures | polish calls/accepted | r | task-s (mean) | wall s | workers |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, v in s["runs"].items():
        p, c = v["polish"], v["cost"]
        L.append(f"| {k} | {v['quad'].get('n_tau_nodes', 31)} | {v['quad'].get('n_g_nodes', 17)} | {v['rule']} | {v['n_available']}/20 | {v['primary']} | "
                 f"{v['half_width']:.3e} | {len(v['numerical_failures'])} | {v['nesting_failures']} | {p['calls']}/{p['accepted']} | {p['r_extra_work']:.4f} | "
                 f"{c['task_seconds']:.0f} ({c.get('mean_task_seconds', c['task_seconds'] / 20):.0f}) | {c.get('queue_wall_seconds', float('nan')):.0f} | {v['workers']} |")
    L.append("")
    L.append("| comparison | PASS | max abs diff | worst | T | over T | unavailable | numerical failures | nesting failures | selection flips |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for k, c in s["comparisons"].items():
        L.append(f"| {k} | {'PASS' if c['passed'] else 'FAIL'} | {c['max_abs_diff']:.3e} | {c['worst_participant']} | {c['tolerance']:.3e} | "
                 f"{', '.join(c['over_tolerance']) or '-'} | {', '.join(c['unavailable']) or '-'} | {len(c['numerical_failures'])} | "
                 f"{len(c['nesting_failures']['candidate']) + len(c['nesting_failures']['reference'])} | "
                 f"{sum(len(v) for v in c['selection_flips'].values())} |")
    L.append("")
    for k, c in s["comparisons"].items():
        L.append(f"## {k}: per participant (Δ₃ difference; ΔS_G3, ΔS_B3; family that moved; selection flips)")
        L.append("")
        L.append("| m | Δ₃ diff | ΔS_G3 | ΔS_B3 | moved | flips |")
        L.append("|---|---|---|---|---|---|")
        for m in range(20):
            key = f"m{m}"
            d = c["diffs"].get(key)
            if d is None:
                L.append(f"| {key} | UNAVAILABLE | | | | |")
                continue
            mv = c["moved"][key]
            fl = "; ".join(f"f{x['fold']} {x['model']} {x['reference']}->{x['candidate']}" for x in c["selection_flips"].get(key, [])) or "-"
            L.append(f"| {key} | {d:+.3e} | {mv['G3']:+.3e} | {mv['B3']:+.3e} | {mv['family']} | {fl} |")
        L.append("")
    if s["cost"]:
        L.append("Cost: " + ", ".join(f"{k} {v:.4f}" for k, v in s["cost"].items()) + ".")
        L.append("")
    L.append(f"LATENCY RULE outcome: {s['latency_rule']}.")
    return "\n".join(L) + "\n"


def rank_checks() -> dict:
    """Jacobian rank of the per-trial log-likelihood map at a generic point (local identifiability of the full
    parameter vector) for every model, and the rank of the stacked 31-node window basis (§4)."""
    import jax
    import jax.numpy as jnp
    out = {}
    for span_name in ("primary", "whole"):
        b = M.basis(span_name)
        stacked = b.Bmat.reshape(-1, b.n_basis)
        sv = np.linalg.svd(stacked, compute_uv=False)
        out[f"stacked_basis_{span_name}"] = dict(shape=list(stacked.shape), rank=int(np.sum(sv > 1e-10 * sv[0])),
                                                 n_basis=b.n_basis, min_sv_ratio=float(sv[-1] / sv[0]))
        b0 = b.Bmat[b.node0][:, b.visible]
        sv0 = np.linalg.svd(b0, compute_uv=False)
        out[f"zero_shift_visible_basis_{span_name}"] = dict(shape=list(b0.shape), rank=int(np.sum(sv0 > 1e-10 * sv0[0])))
    bases = load_bases()
    p = make_synthetic("W2", 0, 0, 10, bases)
    train, _, _, _ = D.fold_datasets(p, D.span("primary"), 0)
    rng = np.random.default_rng(0)
    for name in M.MODEL_NAMES:
        sp = M.spec(name)
        info = F.start_info(sp, train)
        th = F.start_vectors(sp, info)[0][1] + rng.normal(0, 0.05, size=sp.n_params)
        if sp.tau_free:
            th[sp.layout()["index"]["theta_tau"]] = 0.4          # a generic positive spread (40 ms)
        if sp.scale_free:
            th[sp.layout()["index"]["s_g"]] = 0.5
        obj = M.Objective(sp, train)
        U, k, Linv, logdet = obj.U[: obj.n_eff], obj.k[: obj.n_eff], obj.Linv, obj.logdet
        Jm = np.asarray(jax.jacfwd(lambda t: obj.per_trial(t, U, k, Linv, logdet))(jnp.asarray(th)))
        sv = np.linalg.svd(Jm, compute_uv=False)
        out[name] = dict(n_params=sp.n_params, jacobian_shape=list(Jm.shape),
                         rank=int(np.sum(sv > 1e-8 * sv[0])), sv_min_over_max=float(sv[-1] / sv[0]),
                         smallest_sv=[float(v) for v in sv[-4:]])
    os.makedirs(CHECK_DIR, exist_ok=True)
    with open(os.path.join(CHECK_DIR, "ranks.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


def small_spread_check() -> dict:
    """ℓ_prof(s) − ℓ_reduced at parent spreads {1, 2, 5, 8, 10} ms (and the node-0 weight) on a development
    participant: documents the flat region below the 2 ms floor and the node spacing (§4, §5)."""
    bases = load_bases()
    out = {}
    for setting, m, base in (("W2", 0, 10), ("T1", 0, 10)):
        p = make_synthetic(setting, 0, m, base, bases)
        ds = D.full_dataset(p, D.span("primary"))
        cache = F.FitCache()
        rows = {}
        for fam in ("G", "B"):
            res = F.fit_all_models(ds, cache, "primary", (fam + "3",))
            red = res[fam + "2"]
            sp_full = M.spec(fam + "3+")
            info = F.start_info(sp_full, ds)
            prof = {}
            for s in (1.0, 2.0, 5.0, 8.0, 10.0, 20.0):
                sp_c = sp_full.constrained(s)
                starts = F.constrained_starts(sp_full, sp_c, res[fam + "3"], F.selected_spec(fam + "3", res[fam + "3"], "primary"), info, 2)
                r = F.em_fit(sp_c, ds, starts=starts, info=info)
                w0 = float(M.truncnorm_node_weights(M.tau_nodes_ms(), s)[15])
                prof[str(s)] = dict(ell_minus_reduced=(r.loglik - red.loglik) if r.available else None,
                                    node0_weight=w0, status=r.status)
            rows[fam] = dict(reduced_loglik=red.loglik, unrestricted=dict(selection=res[fam + "3"].selection,
                             s_tau_ms=M.unpack(F.selected_spec(fam + "3", res[fam + "3"], "primary"), res[fam + "3"].theta).s_tau_ms,
                             loglik=res[fam + "3"].loglik), profile=prof)
        out[f"{setting}-m{m}-S{base}"] = rows
    os.makedirs(CHECK_DIR, exist_ok=True)
    with open(os.path.join(CHECK_DIR, "small_spread.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


# ----------------------------------------------------------------------------------------------
# start basins: the two development starts (§5)
# ----------------------------------------------------------------------------------------------
BASIN_DIR = os.path.join(S2_DIR, "basins")


def development_starts(sp: M.ModelSpec, info: F.StartInfo) -> list:
    """The near-collapsed two-state start (A → 1 at all levels: κ = 50, x0 = −5; B family only) and the broad
    template start (every coefficient at the gauge value, i.e. a flat T̃), with the first recipe's nuisance."""
    base = F.nuisance_recipes(sp)[0]
    out = []
    flat = F.StartInfo(np.zeros(sp.basis().n_basis), np.zeros(sp.basis().n_basis), info.a, info.logkappa, info.x0,
                       True, info.kappa_fallback)
    out.append(("broad-template", F.start_vectors(sp, flat, [base])[0][1]))
    if sp.family == "B":
        th = F.start_vectors(sp, info, [base])[0][1].copy()
        lay = sp.layout()["index"]
        th[lay["logkappa"]] = np.log(M.KAPPA_MAX)
        th[lay["x0"]] = -5.0
        out.append(("near-collapsed", th))
    return out


def basin_task(setting: str, r: int, m: int, base_subject: int, bases: dict) -> dict:
    """Start-basin check, corrected after the Codex S3 review (24 Oct 2026, finding 6): on fold 0 the REPAIRED
    procedure (the union start set, warm chains, re-seeds, EM) gives each candidate's final optimum; each development
    start (broad template; near-collapsed two-state) is then run as its own complete EM fit from that start alone, and
    a development start is MATERIAL when its final end point beats the procedure's final optimum by more than 1e-6
    relative. Final EM end points are compared with final EM end points. Also reports the B ⊇ G nesting of the
    procedure's training objectives."""
    os.environ.setdefault("NPROC", "1")
    p = make_synthetic(setting, r, m, base_subject, bases)
    train, _, _, _ = D.fold_datasets(p, D.span("primary"), 0)
    res = F.fit_all_models(train, F.FitCache(), "primary", ("G3", "B3"))
    out = dict(setting=setting, r=r, m=m, base=base_subject, data_id=p.data_id, code_hash=M.code_hash(), fits={})
    for name in DECISION_SPECS:
        sp = M.spec(name)
        proc = res[name]
        info = F.start_info(sp, train)
        dev = development_starts(sp, info)
        dev_fits = {}
        for label, theta in dev:
            rd = F.em_fit(sp, train, starts=[(label, theta)], info=info)
            dev_fits[label] = dict(status=rd.status, loglik=rd.loglik if rd.available else None, em=rd.em_iterations)
        best_dev = max((v["loglik"] for v in dev_fits.values() if v["loglik"] is not None), default=None)
        proc_ll = proc.loglik if proc.available else None
        improved = (best_dev is not None and proc_ll is not None and best_dev > proc_ll + 1e-6 * max(1.0, abs(proc_ll)))
        out["fits"][name] = dict(procedure_loglik=proc_ll, procedure_status=proc.status, procedure_starts=len(proc.starts),
                                 dev=dev_fits, best_dev=best_dev, dev_improved=bool(improved),
                                 gain_nat=(best_dev - proc_ll) if (best_dev is not None and proc_ll is not None) else None,
                                 selected_loglik=proc_ll)
    for g, b in (("G2", "B2"), ("G3+", "B3+")):
        lg, lb = out["fits"][g]["selected_loglik"], out["fits"][b]["selected_loglik"]
        out[f"nesting_{b}_minus_{g}"] = None if lg is None or lb is None else lb - lg
    return out


def run_basins(settings=("W2", "T1", "O1"), r: int = 0, workers: int = 12) -> dict:
    from joblib import Parallel, delayed
    bases = load_bases()
    os.makedirs(BASIN_DIR, exist_ok=True)
    summary = {}
    for setting in settings:
        members = set_members(setting, r)
        rows = Parallel(n_jobs=workers, backend="loky")(
            delayed(basin_task)(setting, r, m, s, bases) for m, s in enumerate(members))
        with open(os.path.join(BASIN_DIR, f"{setting}_set{r}.json"), "w") as f:
            json.dump(rows, f, indent=1)
        agg = {}
        for name in DECISION_SPECS:
            imp = [row["fits"][name] for row in rows if row["fits"][name]["dev_improved"]]
            agg[name] = dict(n=len(rows), dev_improved=len(imp),
                             max_gain_nat=max([x["gain_nat"] for x in imp], default=0.0))
        viol = {k: sum(1 for row in rows if row[k] is not None and row[k] < -1e-6) for k in ("nesting_B2_minus_G2", "nesting_B3+_minus_G3+")}
        worst = {k: min([row[k] for row in rows if row[k] is not None], default=0.0) for k in viol}
        summary[setting] = dict(per_spec=agg, nesting_violations=viol, worst_nesting_deficit_nat=worst)
        print(f"[s2 basins] {setting}: " + ", ".join(f"{n} dev-improved {a['dev_improved']}/{a['n']} (max {a['max_gain_nat']:.3f} nat)" for n, a in agg.items())
              + f"; nesting violations {viol}", flush=True)
    with open(os.path.join(BASIN_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary


# ----------------------------------------------------------------------------------------------
# profile-start validation (§5): 2 vs 4 constrained starts on 100 datasets per family from W2 and T1
# ----------------------------------------------------------------------------------------------
PROF_DIR = os.path.join(S2_DIR, "profile_validation")
PROFILE_REL_TOL, PROFILE_LR_TOL = 1e-6, 0.05


def profile_task(setting: str, r: int, m: int, base_subject: int, bases: dict, family: str) -> dict:
    """§5 profile-start validation, corrected after the Codex S3 review (24 Oct 2026, finding 9): the unrestricted
    reference is the REPAIRED cross-family fitter (both families fitted, so G's B-basin re-seed and B's G-twin chains
    apply), and at every grid point the TWO-start and the FOUR-start constrained procedures are run SEPARATELY, each as
    its own EM fit, and compared on their FINAL log-likelihoods. (The earlier form ran one four-start EM fit and read
    its first two initial-covariance start objectives as the two-start result, which is not the two-start procedure.)"""
    os.environ.setdefault("NPROC", "1")
    p = make_synthetic(setting, r, m, base_subject, bases)
    ds = D.full_dataset(p, D.span("primary"))
    cache = F.FitCache()
    res = F.fit_all_models(ds, cache, "primary", ("G3", "B3"))
    unres = res[family + "3"]
    out = dict(setting=setting, r=r, m=m, base=base_subject, family=family, data_id=p.data_id, code_hash=M.code_hash(),
               unrestricted=dict(status=unres.status, selection=unres.selection, loglik=unres.loglik), points={})
    if not unres.available:
        return out
    sp_full = M.spec(family + "3+")
    sp_u = F.selected_spec(family + "3", unres, "primary")
    info = F.start_info(sp_full, ds)
    ell_hat = unres.loglik
    for s in X.PROFILE_GRID_MS:
        if s == 0.0:
            red = res[family + "2"]
            out["points"]["0"] = dict(ell2=red.loglik, ell4=red.loglik, status2=red.status, status4=red.status, q2=None, q4=None)
            continue
        sp_c = sp_full.constrained(s)
        starts4 = F.constrained_starts(sp_full, sp_c, unres, sp_u, info, 4)
        r2 = F.em_fit(sp_c, ds, starts=starts4[:2], info=info)          # the declared two-start procedure, complete
        r4 = F.em_fit(sp_c, ds, starts=starts4, info=info)              # the four-start procedure, complete
        ell2 = r2.loglik if r2.available else None
        ell4 = r4.loglik if r4.available else None
        out["points"][str(s)] = dict(ell2=ell2, ell4=ell4, status2=r2.status, status4=r4.status,
                                     q2=None if ell2 is None else 2.0 * (ell_hat - ell2),
                                     q4=None if ell4 is None else 2.0 * (ell_hat - ell4),
                                     em2=r2.em_iterations, em4=r4.em_iterations,
                                     starts4={st.label: dict(status=st.status, f=st.f) for st in r4.starts})
    return out


def run_profile_validation(n_per_family: int = 100, workers: int = 12) -> dict:
    """100 development participant-datasets per family drawn alternately from the W2 and T1 sets (set r, member
    m in order), every grid point, agreement to 1e-6 relative in objective AND 0.05 on the LR scale."""
    from joblib import Parallel, delayed
    bases = load_bases()
    os.makedirs(PROF_DIR, exist_ok=True)
    summary = {}
    for family in ("G", "B"):
        tasks = []
        i = 0
        while len(tasks) < n_per_family:
            setting = ("W2", "T1")[i % 2]
            r, m = (i // 2) // 20, (i // 2) % 20
            tasks.append((setting, r, m, set_members(setting, r)[m]))
            i += 1
        rows = Parallel(n_jobs=workers, backend="loky")(
            delayed(profile_task)(setting, r, m, base, bases, family) for setting, r, m, base in tasks)
        with open(os.path.join(PROF_DIR, f"{family}.json"), "w") as f:
            json.dump(rows, f)
        n_points = n_fail_rel = n_fail_lr = n_unavail2 = n_unavail4 = n_unres_unavail = 0
        worst_rel = worst_lr = 0.0
        expected_points = len(rows) * (len(X.PROFILE_GRID_MS) - 1)
        for row in rows:
            if row["unrestricted"]["status"] != "AVAILABLE":
                n_unres_unavail += 1
            for s, pt in row["points"].items():
                if s == "0":
                    continue
                n_points += 1
                if pt["ell4"] is None:
                    n_unavail4 += 1
                    continue
                if pt["ell2"] is None:
                    n_unavail2 += 1
                    continue
                rel = abs(pt["ell2"] - pt["ell4"]) / max(1.0, abs(pt["ell4"]))
                lr = abs(pt["q2"] - pt["q4"])
                worst_rel, worst_lr = max(worst_rel, rel), max(worst_lr, lr)
                n_fail_rel += rel > PROFILE_REL_TOL
                n_fail_lr += lr > PROFILE_LR_TOL
        # the validation passes only when EVERY promised dataset and grid point was fitted and compared: an unavailable
        # unrestricted fit or four-start fit is a missing comparison, never a vacuous pass (Codex S3 review, finding 9)
        complete = (len(rows) == n_per_family and n_points == expected_points and n_unres_unavail == 0 and n_unavail4 == 0)
        summary[family] = dict(datasets=len(rows), datasets_promised=n_per_family, grid_points=n_points,
                               grid_points_promised=expected_points, unrestricted_unavailable=n_unres_unavail,
                               two_start_unavailable=n_unavail2, four_start_unavailable=n_unavail4,
                               fail_relative=n_fail_rel, fail_lr=n_fail_lr, worst_relative=worst_rel, worst_lr=worst_lr,
                               complete=complete, code_hash=M.code_hash(),
                               passed=bool(complete and n_fail_rel == 0 and n_fail_lr == 0 and n_unavail2 == 0))
        print(f"[s2 profiles] {family}: {n_points} grid points on {len(rows)} datasets; relative failures {n_fail_rel}, "
              f"LR failures {n_fail_lr}, 2-start unavailable {n_unavail2}; worst rel {worst_rel:.1e}, worst LR {worst_lr:.3f} -> "
              f"{'PASS' if summary[family]['passed'] else 'FAIL (profiles use 4 starts; re-cost §8)'}", flush=True)
    with open(os.path.join(PROF_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bases")
    d = sub.add_parser("decision")
    d.add_argument("--setting", required=True, choices=list(SETTINGS))
    d.add_argument("--R", type=int, default=25)
    d.add_argument("--workers", type=int, default=12)
    d.add_argument("--sets", default=None, help="e.g. 0-4")
    d.add_argument("--reverse", action="store_true", help="work the set list from its far end (a second host on the same setting)")
    sub.add_parser("summary")
    asm = sub.add_parser("assemble", help="set_<r>.json from the 20 task files of a set computed elsewhere (task files kept)")
    asm.add_argument("--setting", required=True, choices=list(SETTINGS))
    asm.add_argument("--set", type=int, required=True)
    c = sub.add_parser("checks")
    c.add_argument("--kind", required=True, choices=["nodes", "ranks", "smallspread", "twopass"])
    c.add_argument("--setting", default="W2", choices=list(SETTINGS))
    c.add_argument("--set", type=int, default=0)
    c.add_argument("--workers", type=int, default=12)
    c.add_argument("--sg", type=float, default=M.QUAD_G_REFIT_SG, help="twopass: the refit threshold on the fitted s_g (0.6 declared; 0.4 the declared retry)")
    c.add_argument("--ref", default=None, help="twopass: the blanket-33 reference json (default results/s2_aws/checks/nodes_g33_<setting>_set<set>.json)")
    bsn = sub.add_parser("basins")
    bsn.add_argument("--workers", type=int, default=12)
    pr = sub.add_parser("profiles")
    pr.add_argument("--n", type=int, default=100)
    pr.add_argument("--workers", type=int, default=12)
    rp = sub.add_parser("repair", help="the repaired same-data, same-code node checks (REPAIR_RUNS): one archived run, or the summary")
    rp.add_argument("--label", required=True, choices=list(REPAIR_RUNS) + ["summary"])
    rp.add_argument("--setting", default="W2", choices=list(SETTINGS))
    rp.add_argument("--set", type=int, default=0)
    rp.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    if a.cmd == "bases":
        b = cache_bases()
        print(f"[s2] cached {len(b)} bases")
    elif a.cmd == "decision":
        sets = list(range(a.R))
        if a.sets:
            lo, hi = a.sets.split("-")
            sets = list(range(int(lo), int(hi) + 1))
        if a.reverse:
            sets = sets[::-1]
        run_decision(a.setting, a.R, a.workers, sets)
        print(summary_markdown(summarize()))
    elif a.cmd == "summary":
        print(summary_markdown(summarize()))
    elif a.cmd == "assemble":
        assemble_set(a.setting, a.set, remove_task_files=False)
    elif a.cmd == "checks":
        if a.kind == "nodes":
            node_check(a.setting, a.set, dict(n_g_nodes=33), "g33", a.workers)
            node_check(a.setting, a.set, dict(n_tau_nodes=61), "tau61", a.workers)
            node_check(a.setting, a.set, dict(n_g_nodes=7, adaptive_g=False), "prior7", a.workers)
        elif a.kind == "twopass":
            twopass_check(a.setting, a.set, a.workers, a.sg, a.ref)
        elif a.kind == "ranks":
            print(json.dumps(rank_checks(), indent=1))
        else:
            print(json.dumps(small_spread_check(), indent=1))
    elif a.cmd == "basins":
        run_basins(workers=a.workers)
    elif a.cmd == "profiles":
        run_profile_validation(a.n, a.workers)
    elif a.cmd == "repair":
        if a.label == "summary":
            s = repair_summary(a.setting, a.set)
            print(repair_summary_markdown(s))
        else:
            repair_run(a.setting, a.set, a.label, a.workers)
            print(repair_summary_markdown(repair_summary(a.setting, a.set)))


if __name__ == "__main__":
    main()
