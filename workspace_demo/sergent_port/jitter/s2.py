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


def decision_task(setting: str, r: int, m: int, base_subject: int, bases: dict, span_name: str = "primary") -> dict:
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    p = make_synthetic(setting, r, m, base_subject, bases)
    sp_ = D.span(span_name)
    cache = F.FitCache()
    sums = {"G3": [], "B3": []}
    folds = []
    xs = {}
    for fold in range(5):
        train, test, _, _ = D.fold_datasets(p, sp_, fold)
        res = F.fit_all_models(train, cache, span_name, ("G3", "B3"))
        row = dict(fold=fold, n_train=train.n, n_test=test.n, shrinkage=train.wh.shrinkage, fits={})
        for name in DECISION_SPECS:
            fr = res[name]
            row["fits"][name] = dict(status=fr.status, loglik=fr.loglik, n_converged=fr.n_converged,
                                     bounds_hit=fr.bounds_hit, clipped=fr.clipped, notes=fr.notes,
                                     starts=_start_rows(fr), seconds=fr.seconds)
            for i, s in enumerate(fr.starts):
                xs[f"f{fold}_{name}_s{i}"] = np.asarray(s.x, dtype=np.float32)
        for sel in ("G3", "B3"):
            fr = res[sel]
            row["fits"][sel] = dict(status=fr.status, loglik=fr.loglik, selection=fr.selection, flags=fr.flags,
                                    candidates=fr.candidates)
            if fr.available:
                sp = F.selected_spec(sel, fr, span_name)
                ll = M.Objective(sp, train).trial_loglik(fr.theta, test)
                sums[sel].append(float(np.sum(ll)))
                xs[f"f{fold}_{sel}_theta"] = np.asarray(fr.theta, dtype=np.float32)
            else:
                sums[sel].append(float("nan"))
        folds.append(row)
    n = D.n_scored(p)
    scores = {k: (float(np.nansum(v) / n) if not np.any(np.isnan(v)) else float("nan")) for k, v in sums.items()}
    return dict(setting=setting, r=r, m=m, base=base_subject, data_id=p.data_id, n_trials=p.n, n_scored=n,
                scores=scores, fold_sums=sums, folds=folds, seconds=_time.time() - t0, code_hash=M.code_hash(),
                _xs=xs)


def run_decision(setting: str, R: int, workers: int, sets=None, span_name: str = "primary"):
    from joblib import Parallel, delayed
    bases = load_bases()
    out_dir = os.path.join(DEC_DIR, setting)
    arc_dir = os.path.join(ARC_DIR, setting)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(arc_dir, exist_ok=True)
    sets = list(range(R)) if sets is None else sets
    for r in sets:
        path = os.path.join(out_dir, f"set_{r}.json")
        if os.path.exists(path):
            print(f"[s2] {setting} set {r}: exists, skipped", flush=True)
            continue
        members = set_members(setting, r)
        t0 = _time.time()
        rows = Parallel(n_jobs=workers, backend="loky")(
            delayed(decision_task)(setting, r, m, s, bases, span_name) for m, s in enumerate(members))
        xs = {}
        for row in rows:
            for k, v in row.pop("_xs").items():
                xs[f"m{row['m']}_{k}"] = v
        np.savez_compressed(os.path.join(arc_dir, f"set_{r}.npz"), **xs)
        set_scores = {f"m{row['m']}": row["scores"] for row in rows}
        primary = X.set_primary(set_scores)
        rec = dict(setting=setting, r=r, members=members, primary=primary,
                   delta3={k: (v["B3"] - v["G3"]) for k, v in set_scores.items()},
                   participants=rows, wall_s=_time.time() - t0, workers=workers, code_hash=M.code_hash())
        with open(path, "w") as f:
            json.dump(rec, f)
        avail = sum(1 for v in set_scores.values() if np.isfinite(v["B3"] - v["G3"]))
        print(f"[s2] {setting} set {r}: primary {primary}, {avail}/20 available, {rec['wall_s']:.0f} s", flush=True)


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


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bases")
    d = sub.add_parser("decision")
    d.add_argument("--setting", required=True, choices=list(SETTINGS))
    d.add_argument("--R", type=int, default=25)
    d.add_argument("--workers", type=int, default=12)
    d.add_argument("--sets", default=None, help="e.g. 0-4")
    sub.add_parser("summary")
    a = ap.parse_args()
    if a.cmd == "bases":
        b = cache_bases()
        print(f"[s2] cached {len(b)} bases")
    elif a.cmd == "decision":
        sets = None
        if a.sets:
            lo, hi = a.sets.split("-")
            sets = list(range(int(lo), int(hi) + 1))
        run_decision(a.setting, a.R, a.workers, sets)
        print(summary_markdown(summarize()))
    elif a.cmd == "summary":
        print(summary_markdown(summarize()))


if __name__ == "__main__":
    main()
