#!/usr/bin/env python3
"""The synthetic development battery — PREREG_secondary_melcon.md §9, DRAFT v5 (Codex, continuation review 4, §4–§5).
No EEG is read. Development checks of the implementation, not calibrated family-error control.

Stage A (continuous preprocessing and QC on artificial raw recordings): test_preprocess.py, test_causal.py.
Stage B (likelihood, decoder/recording isolation, inclusion, decision function): test_likelihood.py, test_recording.py,
test_inclusion.py, test_group.py.
Stage C (this file): the complete pipeline of §2 and §4–§8 on synthetic epochs (synthetic.py).

Templates: the nocue recordings that pass §2 at the events-table level (34: sub-35 nocue is not on OpenNeuro and sub-36
nocue is excluded, README D14). Cells: 5 generators × 2 decoder strengths ('weak', 'strong') × 2 drift conditions (none;
0.3 SD per block) × 3 replicates = 60 replicates × 34 recordings = 2,040 synthetic recordings. A recording's seed tags are
(1, generator index, strength index, drift index, replicate, subject).

Strength, defined per generator (v5; v4's common targets AUC 0.6 and 0.8 are withdrawn — Codex showed the population
limit of X1 is 0.744 and of X2 0.648 on the calibration templates, so 0.8 was unattainable). The calibration statistic is
the median over recordings of the recording's mean held-out AUC over the two halves and the ten main-interval windows.
Its population ceiling for a generator, POPULATION LIMIT, is the same statistic computed exactly from the latent ranking
AUC of each present trial (synthetic.present_latent_auc) on the first N_CAL templates without drift — behaviour only, no
epochs, no outcome. The target is 0.5 + HEADROOM[strength] × (limit − 0.5): 'weak' 50 %, 'strong' 90 % of the generator's
own discriminability headroom. The amplitude is read from a calibration draw (tags (2, generator, strength, 0, subject))
of the first N_CAL templates without drift on CAL_GRID, interpolated linearly to the target; accepted if a fresh check draw
(tags (2, generator, strength, 1, subject)) lands within CAL_TOL of the target, otherwise REFINE_FACTORS around it are added
once and the check repeated. The full search history (grid, refinement points, both checks) is saved. A calibration that
misses twice is NOT USABLE: its cells run as diagnostics, identified as such in every result and verdict, and can neither
pass, fail nor drive a protocol revision. Equal presence AUC across generators is not equal mixture identifiability; the
conditional readout separation is reported beside it.

Result provenance: a configuration identity (battery version, digests of every pipeline module, every module SPEC, the
strength definition, the calibration constants and the events-table digest) names the result namespace
results/battery/<version>-<identity digest>/. Every recording result carries its manifest (identity, generator, strength,
drift, replicate, subject, seed tags, amplitude, calibration digest and acceptance, template digest); an existing result
whose manifest differs, or that cannot be read, is refused — results are never silently reused across revisions, and a
revision writes a new namespace beside the retained old one.

Pass criteria, evaluated on the main interval with group.decide, only on COMPLETE cells (every replicate with every
recording present): 'incomplete' otherwise; 'diagnostic: calibration not usable' for an unusable calibration;
  - G1, G2, G3, every strength × drift cell: at least 2 of the 3 replicates end in a substantive outcome (two-state,
    graded, inconclusive/mixed) and at most 1 ends 'two-state'. Technical failure, insufficient sensitivity and
    insufficient availability are not substantive: they count against the first requirement and never pass a cell.
  - X1 'strong', both drift conditions: 'two-state' in at least 2 of 3 replicates.
  - X1 'weak' and X2: 'reported' (outcome counts and diagnostics; X2 is the weak-separation stress condition).
Diagnostics per replicate: the median fitted minimum gap e^delta0 / sigma and full gap
(e^delta0 + e^delta1 lg(k_h (x - x0))) / sigma at the held-out present doses, the median absolute occupancy error, the
conditional readout separation of the generating high and low present trials (X generators) and the readout-latent
correlation. A failure leads to a registered revision of the protocol and a re-run; every result and revision is retained.

CLI:  --benchmark | --calibrate [--n-jobs N] | --run [--n-jobs N] [--generators G1,X1] | --summarize | --limits
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd
from scipy.special import expit

import decoder as DEC
import group as G
import inclusion as INC
import likelihood as LK
import recording as RC
import synthetic as SY

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results", "battery")
BATTERY_VERSION = "v5"
STRENGTHS = ("weak", "strong")
HEADROOM = {"weak": 0.5, "strong": 0.9}
DRIFTS = (False, True)
N_REP = 3
N_CAL = 8
CAL_GRID = (0.0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.2, 3.2, 4.6, 6.4)
REFINE_FACTORS = (0.75, 0.875, 1.0, 1.125, 1.25)
CAL_TOL = 0.03
CODE_FILES = ("synthetic.py", "battery.py", "decoder.py", "likelihood.py", "recording.py", "group.py", "inclusion.py")
SUBSTANTIVE = ("two-state", "graded", "inconclusive/mixed")


# ----------------------------------------------------------------------------------------------------------- identity
def _sha_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def config_identity() -> dict:
    return dict(battery_version=BATTERY_VERSION, code={f: _sha_file(os.path.join(HERE, f)) for f in CODE_FILES},
                synthetic=SY.SPEC, decoder=DEC.SPEC, likelihood=LK.SPEC, group=G.SPEC, inclusion=INC.SPEC,
                strengths=STRENGTHS, headroom=HEADROOM, drifts=DRIFTS, n_rep=N_REP, n_cal=N_CAL, cal_grid=CAL_GRID,
                refine_factors=REFINE_FACTORS, cal_tol=CAL_TOL, events_table=_sha_file(SY.TRIALS_CSV))


def run_directory(identity: dict | None = None) -> str:
    identity = identity or config_identity()
    d = os.path.join(OUT_DIR, f"{BATTERY_VERSION}-{digest(identity)[:12]}")
    os.makedirs(os.path.join(d, "recordings"), exist_ok=True)
    path = os.path.join(d, "manifest.json")
    if os.path.exists(path):
        with open(path) as fh:
            if json.load(fh) != json.loads(json.dumps(identity, default=str)):
                raise RuntimeError(f"{path}: namespace manifest differs from the running configuration")
    else:
        with open(path, "w") as fh:
            json.dump(identity, fh, indent=2, default=str)
    return d


def template_digest(subject: int) -> str:
    return hashlib.sha256(SY.template(subject, "nocue").to_csv(index=False).encode()).hexdigest()


# ---------------------------------------------------------------------------------------------------------- templates
def templates() -> list:
    """Nocue recordings passing §2 at the events-table level, in subject order."""
    df = pd.read_csv(SY.TRIALS_CSV)
    out = []
    for s, t in df[df.task == "nocue"].groupby("subject"):
        if s == 36:                                                    # README D14: sorted, unrandomised trial order
            continue
        t = t[~(t.present & ~(t.contrast > 0))]
        pres, catch = t[t.present], t[t["catch"]]
        if len(pres) < INC.MIN_PRESENT or len(catch) < INC.MIN_CATCH:
            continue
        ok = True
        for b, tb in t.groupby("block"):
            if tb["catch"].sum() < LK.MIN_CATCH or min((tb.present & (tb.side == side)).sum() for side in ("left", "right")) < LK.MIN_SIDE:
                ok = False
        for half in DEC.HALVES:
            if t[t.block.isin(half)]["catch"].sum() < DEC.MIN_CATCH_HALF:
                ok = False
        if ok:
            out.append(int(s))
    return out


# ------------------------------------------------------------------------------------------------- strength and limits
def population_calibration_auc(generator: str, subjects: list) -> float:
    """The calibration statistic's population ceiling: per template the mean over the two halves of the mean latent
    ranking AUC of the half's present trials against catch, then the median over templates (no drift)."""
    per = []
    for s in subjects:
        t = SY.template(s, "nocue")
        pres = ~t["catch"].to_numpy(bool)
        lc = np.log(t["contrast"].to_numpy(float)[pres])
        x = (lc - lc.mean()) / lc.std(ddof=1)
        auc = SY.present_latent_auc(generator, expit(SY.DOSE_SLOPE * x), t["side"].to_numpy()[pres] == "right")
        blk = t["block"].to_numpy()[pres]
        per.append(float(np.mean([auc[np.isin(blk, h)].mean() for h in DEC.HALVES])))
    return float(np.median(per))


def strength_target(generator: str, strength: str, subjects: list) -> tuple:
    limit = population_calibration_auc(generator, subjects)
    return limit, 0.5 + HEADROOM[strength] * (limit - 0.5)


def calibration_statistic(recs: list) -> float:
    vals = []
    for rec in recs:
        dec = DEC.split_half(rec)
        if dec["status"] != "ok":
            continue
        vals.append(float(np.nanmean([d["auc"][DEC.MAIN] for d in dec["halves"].values()])))
    return float(np.median(vals)) if vals else np.nan


def _draw(generator, amplitude, draw, strength_i, subjects):
    gi = SY.GENERATORS.index(generator)
    return [SY.generate(SY.template(s, "nocue"), generator, amplitude, False, tags=(2, gi, strength_i, draw, s)) for s in subjects]


def _interpolate(table: dict, target: float) -> float:
    a = np.array(sorted(table))
    v = np.array([table[x] for x in a])
    above = np.where(v >= target)[0]
    if above.size == 0:
        return float(a[-1])
    j = int(above[0])
    if j == 0:
        return float(a[0])
    return float(a[j - 1] + (target - v[j - 1]) * (a[j] - a[j - 1]) / (v[j] - v[j - 1]))


def calibrate(generator: str, strength: str, subjects: list, log=print) -> dict:
    si = STRENGTHS.index(strength)
    limit, target = strength_target(generator, strength, subjects)
    grid = {float(a): calibration_statistic(_draw(generator, float(a), 0, si, subjects)) for a in CAL_GRID}
    log(f"{generator} {strength}: population limit {limit:.4f}, target {target:.4f}; grid "
        f"{json.dumps({str(a): round(v, 3) for a, v in grid.items()})}")
    first_amp = _interpolate(grid, target)
    first_check = calibration_statistic(_draw(generator, first_amp, 1, si, subjects))
    refinement = {}
    amp, check = first_amp, first_check
    if not abs(first_check - target) <= CAL_TOL:
        for a in np.round(first_amp * np.array(REFINE_FACTORS), 4):
            if float(a) not in grid and float(a) not in refinement:
                refinement[float(a)] = calibration_statistic(_draw(generator, float(a), 0, si, subjects))
        amp = _interpolate({**grid, **refinement}, target)
        check = calibration_statistic(_draw(generator, amp, 1, si, subjects))
    accepted = bool(abs(check - target) <= CAL_TOL)
    entry = dict(generator=generator, strength=strength, headroom=HEADROOM[strength], population_limit=limit, target=target,
                 tolerance=CAL_TOL, subjects=[int(s) for s in subjects],
                 grid={str(k): v for k, v in sorted(grid.items())},
                 first=dict(amplitude=first_amp, check=first_check), refined=bool(not abs(first_check - target) <= CAL_TOL),
                 refinement={str(k): v for k, v in sorted(refinement.items())},
                 amplitude=amp, check=check, accepted=accepted,
                 grid_reaches_target=bool(max([*grid.values(), *refinement.values()]) >= target))
    log(f"  -> amplitude {amp:.4f}, check {check:.4f}, accepted {accepted}")
    return entry


# ----------------------------------------------------------------------------------------------------------- recordings
def summary(res: dict) -> dict:
    """What the group rule and the diagnostics need from one recording result (no epochs, no per-start records)."""
    keep = {k: res[k] for k in ("status", "subject", "task")}
    if "section2" in res:
        keep["section2"] = res["section2"]
    if res["status"] != "ok":
        return keep
    min_gap, full_gap, occ_err, read_sep, read_corr = [], [], [], [], []
    halves = sorted(res["decoder"]["halves"])
    names = LK.PARAMS["twostate"]
    ix = {n: names.index(n) for n in names}
    for (hi, fi, w), s in res["folds"].items():
        if w in DEC.MAIN and s["twostate"]["available"]:
            th, sc = s["twostate"]["theta"], s["twostate"]["scaling"]
            sigma = np.exp(th[ix["log_sigma"]])
            g0, g1 = np.exp(th[ix["delta0"]]), np.exp(th[ix["delta1"]])
            min_gap.append(float(g0 / sigma))
            B = halves[hi]
            tr = res["decoder"]["halves"][B]["trials"]
            b_te = B[1] if fi == 0 else B[0]
            t = tr[(tr.block == b_te) & ~tr["catch"]]
            x = (np.log(t["contrast"].to_numpy(float)) - sc["m"]) / sc["s"]
            full_gap.append(float(np.median((g0 + g1 * expit(np.exp(th[ix["log_k_h"]]) * (x - th[ix["x0"]]))) / sigma)))
            if "occupancy_true" in t:
                A = expit(np.exp(th[ix["log_k_a"]]) * (x - th[ix["x0"]]))
                occ_err.append(float(np.median(np.abs(A - t["occupancy_true"].to_numpy(float)))))
    for B in halves:
        d = res["decoder"]["halves"][B]
        tr, W = d["trials"], d["W"]
        pres = ~tr["catch"].to_numpy(bool)
        for w in DEC.MAIN:
            y = W[:, w]
            if not np.all(np.isfinite(y[pres])):
                continue
            if "high_true" in tr and SY.GENERATORS and tr["high_true"].to_numpy(bool)[pres].any():
                hi_m = tr["high_true"].to_numpy(bool) & pres
                lo_m = ~tr["high_true"].to_numpy(bool) & pres
                if hi_m.sum() >= 2 and lo_m.sum() >= 2:
                    pooled = np.sqrt((np.var(y[hi_m], ddof=1) + np.var(y[lo_m], ddof=1)) / 2)
                    if pooled > 0:
                        read_sep.append(float((y[hi_m].mean() - y[lo_m].mean()) / pooled))
            if "z_true" in tr and np.std(y[pres]) > 0:
                read_corr.append(float(np.corrcoef(y[pres], tr["z_true"].to_numpy(float)[pres])[0, 1]))

    def med(v):
        return float(np.median(v)) if v else np.nan
    keep.update(windows=res["windows"], models=res["models"], evidence=res["evidence"], available=res["available"],
                delta=res["delta"], n_trials=res["n_trials"], auc=res["auc"],
                twostate_min_gap_median=med(min_gap), twostate_full_gap_median=med(full_gap),
                occupancy_abs_error_median=med(occ_err), readout_component_separation_median=med(read_sep),
                readout_latent_corr_median=med(read_corr))
    return keep


def main_positions(res_windows) -> list:
    return [res_windows.index(w) for w in DEC.MAIN]


def recording_manifest(identity_digest: str, generator: str, strength_i: int, drift_i: int, rep: int, subject: int,
                       cal_entry: dict) -> dict:
    return dict(config=identity_digest, generator=generator, strength=STRENGTHS[strength_i], drift=bool(DRIFTS[drift_i]),
                replicate=int(rep), subject=int(subject),
                tags=[1, SY.GENERATORS.index(generator), int(strength_i), int(drift_i), int(rep), int(subject)],
                amplitude=float(cal_entry["amplitude"]), calibration=digest(cal_entry),
                calibration_accepted=bool(cal_entry["accepted"]), template=template_digest(subject))


def load(path):
    return np.load(path, allow_pickle=True)[0]


def load_verified(path: str, manifest: dict) -> dict:
    try:
        res = load(path)
    except Exception as e:
        raise RuntimeError(f"{path}: existing result cannot be read ({type(e).__name__}); results are never overwritten") from e
    if not isinstance(res, dict) or res.get("manifest") != manifest:
        raise RuntimeError(f"{path}: existing result has a different identity; revisions use a new namespace")
    return res


def run_recording(manifest: dict, path: str) -> str:
    if os.path.exists(path):
        load_verified(path, manifest)
        return path
    rec = SY.generate(SY.template(manifest["subject"], "nocue"), manifest["generator"], manifest["amplitude"],
                      manifest["drift"], tags=tuple(manifest["tags"]))
    res = summary(RC.recording_scores(rec, manifest["subject"], "nocue"))
    res["manifest"] = manifest
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        np.save(fh, np.array([res], dtype=object), allow_pickle=True)
    os.replace(tmp, path)
    return path


def cell_path(run_dir, generator, strength_i, drift_i, rep, subject):
    return os.path.join(run_dir, "recordings", f"{generator}_{STRENGTHS[strength_i]}_d{drift_i}_r{rep}_sub-{subject:02d}.npy")


# ------------------------------------------------------------------------------------------------------------- verdicts
def cell_verdicts(outcomes: dict, calibration_usable: dict | None = None, expected=None, n_rep: int = N_REP) -> dict:
    """outcomes {(generator, strength, drift_i): [outcome or None per replicate]} -> the §9 verdicts. A missing or
    incomplete replicate (None) makes the cell 'incomplete'; an unusable calibration makes it a diagnostic."""
    keys = list(expected) if expected is not None else list(outcomes)
    out = {}
    for key in keys:
        g, strength, _ = key
        reps = list(outcomes.get(key, []))
        if len(reps) < n_rep or any(o is None for o in reps):
            out[key] = "incomplete"
        elif calibration_usable is not None and not calibration_usable.get((g, strength), False):
            out[key] = "diagnostic: calibration not usable"
        elif g in ("G1", "G2", "G3"):
            ok = sum(o in SUBSTANTIVE for o in reps) >= 2 and sum(o == "two-state" for o in reps) <= 1
            out[key] = "pass" if ok else "fail"
        elif g == "X1" and strength == "strong":
            out[key] = "pass" if sum(o == "two-state" for o in reps) >= 2 else "fail"
        else:
            out[key] = "reported"
    return out


def load_calibration(run_dir: str) -> dict:
    path = os.path.join(run_dir, "calibration.json")
    entries = json.load(open(path)) if os.path.exists(path) else []
    return {(e["generator"], e["strength"]): e for e in entries}


def save_calibration(run_dir: str, entry: dict) -> None:
    """Add one calibration entry under an exclusive lock, re-reading the file first, so that several --calibrate
    processes (one per generator set) never overwrite each other's entries; an existing entry is never replaced."""
    import fcntl
    path = os.path.join(run_dir, "calibration.json")
    with open(path + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        entries = load_calibration(run_dir)
        key = (entry["generator"], entry["strength"])
        if key in entries:
            raise RuntimeError(f"calibration for {key} already exists in {run_dir}; results are never replaced")
        entries[key] = entry
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(list(entries.values()), fh, indent=2)
        os.replace(tmp, path)


# ----------------------------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--limits", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--generators", default=",".join(SY.GENERATORS))
    ap.add_argument("--n-jobs", type=int, default=1)
    a = ap.parse_args()
    subjects = templates()
    gens = a.generators.split(",")
    identity = config_identity()
    ident = digest(identity)
    run_dir = run_directory(identity)
    if a.limits:
        rows = []
        for g in gens:
            for st in STRENGTHS:
                limit, target = strength_target(g, st, subjects[:N_CAL])
                rows.append(dict(generator=g, strength=st, limit_first_eight=limit, target=target,
                                 limit_all=population_calibration_auc(g, subjects)))
        print(pd.DataFrame(rows).to_string())
        pd.DataFrame(rows).to_csv(os.path.join(run_dir, "limits.csv"), index=False)
    if a.benchmark:
        t0 = time.time()
        rec = SY.generate(SY.template(subjects[0], "nocue"), "X1", 1.0, False, tags=(3, 0))
        t1 = time.time()
        res = RC.recording_scores(rec, subjects[0], "nocue")
        t2 = time.time()
        per = t2 - t0
        n_rec = len(SY.GENERATORS) * len(STRENGTHS) * len(DRIFTS) * N_REP * len(subjects)
        n_cal_max = len(SY.GENERATORS) * len(STRENGTHS) * (len(CAL_GRID) + 2 + len(REFINE_FACTORS)) * N_CAL
        info = dict(templates=len(subjects), status=res["status"], generate_s=t1 - t0, pipeline_s=t2 - t1,
                    recordings_stage_c=n_rec, projected_stage_c_core_hours=n_rec * per / 3600,
                    calibration_decoder_runs_max=n_cal_max, projected_calibration_core_hours_max=n_cal_max * (t1 - t0 + 11.0) / 3600,
                    note="one worker on a machine shared with the refit probe; decoder-only runs assumed at 11 s; planning "
                         "evidence, not a measured end-to-end run")
        print(json.dumps(info, indent=2))
        with open(os.path.join(OUT_DIR, "benchmark.json"), "w") as fh:
            json.dump(info, fh, indent=2)
    if a.calibrate:
        for g in gens:
            for st in STRENGTHS:
                if (g, st) in load_calibration(run_dir):
                    continue
                save_calibration(run_dir, calibrate(g, st, subjects[:N_CAL]))
    if a.run:
        cal = load_calibration(run_dir)
        missing = [(g, st) for g in gens for st in STRENGTHS if (g, st) not in cal]
        if missing:
            raise SystemExit(f"calibrate first: {missing}")
        jobs = [(recording_manifest(ident, g, si, di, r, s, cal[(g, STRENGTHS[si])]), cell_path(run_dir, g, si, di, r, s))
                for g in gens for si in range(len(STRENGTHS)) for di in range(len(DRIFTS)) for r in range(N_REP)
                for s in subjects]
        if a.n_jobs > 1:
            from joblib import Parallel, delayed
            Parallel(n_jobs=a.n_jobs)(delayed(run_recording)(*j) for j in jobs)
        else:
            for j in jobs:
                run_recording(*j)
    if a.summarize:
        cal = load_calibration(run_dir)
        outcomes, rows, expected = {}, [], []
        for g in gens:
            for si, st in enumerate(STRENGTHS):
                for di in range(len(DRIFTS)):
                    key = (g, st, di)
                    expected.append(key)
                    entry = cal.get((g, st))
                    for r in range(N_REP):
                        base = dict(generator=g, strength=st, drift=DRIFTS[di], replicate=r,
                                    calibration_target=entry["target"] if entry else np.nan,
                                    calibration_check=entry["check"] if entry else np.nan,
                                    calibration_usable=bool(entry and entry["accepted"]))
                        paths = [cell_path(run_dir, g, si, di, r, s) for s in subjects]
                        n_missing = sum(not os.path.exists(p) for p in paths)
                        if entry is None or n_missing:
                            outcomes.setdefault(key, []).append(None)
                            rows.append(dict(base, outcome="incomplete", n_missing=n_missing))
                            continue
                        res = [load_verified(cell_path(run_dir, g, si, di, r, s), recording_manifest(ident, g, si, di, r, s, entry))
                               for s in subjects]
                        ok = [x for x in res if x["status"] == "ok"]
                        pos = main_positions(ok[0]["windows"]) if ok else []
                        n_pass = sum(not x["status"].startswith("excluded") for x in res)
                        d = G.decide(res, pos, n_pass)
                        outcomes.setdefault(key, []).append(d["outcome"])

                        def med(k):
                            return float(np.nanmedian([x.get(k, np.nan) for x in ok])) if ok else np.nan
                        rows.append(dict(base, outcome=d["outcome"], n_missing=0, n_windows_eligible=d.get("n_windows_eligible"),
                                         median_auc_main=float(np.nanmedian(d.get("median_auc", [np.nan]))),
                                         twostate_min_gap=med("twostate_min_gap_median"),
                                         twostate_full_gap=med("twostate_full_gap_median"),
                                         occupancy_abs_error=med("occupancy_abs_error_median"),
                                         readout_component_separation=med("readout_component_separation_median"),
                                         readout_latent_corr=med("readout_latent_corr_median")))
        usable = {k: bool(e["accepted"]) for k, e in cal.items()}
        verdicts = cell_verdicts(outcomes, usable, expected)
        pd.DataFrame(rows).to_csv(os.path.join(run_dir, "replicates.csv"), index=False)
        with open(os.path.join(run_dir, "verdicts.json"), "w") as fh:
            json.dump({f"{g}|{st}|{DRIFTS[di]}": dict(outcomes=outcomes.get((g, st, di), []), verdict=v)
                       for (g, st, di), v in verdicts.items()}, fh, indent=2)
        print(pd.DataFrame(rows).to_string())
        print(json.dumps({f"{k}": v for k, v in verdicts.items()}, indent=1))


if __name__ == "__main__":
    main()
