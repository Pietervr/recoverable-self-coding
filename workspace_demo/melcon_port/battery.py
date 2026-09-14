#!/usr/bin/env python3
"""The synthetic development battery — PREREG_secondary_melcon.md §9, DRAFT v6 (Codex, v5 calibration revision record,
14 Sept 2026, with the review-5 numerical and identity items). No EEG is read. Development checks of the implementation,
not calibrated family-error control.

Stage A (continuous preprocessing and QC on artificial raw recordings): test_preprocess.py, test_causal.py.
Stage B (likelihood, decoder/recording isolation, inclusion, decision function): test_likelihood.py, test_recording.py,
test_inclusion.py, test_group.py.
Stage C (this file): the complete pipeline of §2 and §4–§8 on synthetic epochs (synthetic.py).

Templates: the nocue recordings that pass §2 at the events-table level (34: sub-35 nocue is not on OpenNeuro and sub-36
nocue is excluded, README D14). Cells: 5 generators × 2 decoder strengths ('weak', 'strong') × 2 drift conditions (none;
0.3 SD per block) × 3 replicates = 60 replicates × 34 recordings = 2,040 synthetic recordings.

Calibration statistic: for one draw of all 34 templates without drift, each recording's mean held-out presence AUC over
its two halves and the ten main-interval windows, then the median over recordings. A statistic is COMPLETE only when all
34 recordings decode and all 680 main-window AUCs (34 × 2 × 10) are finite and in [0, 1]; otherwise it is recorded as
incomplete with its failures, its value is NaN, and it enters no reach, bracket or acceptance.

Strength (v6). The reach R_g is the mean of two independently seeded complete statistics at REACH_AMPLITUDE 6.4 (seed
phase 'reach', draws 0 and 1), saved with both values, their per-template AUCs and their disagreement, and frozen in
reach.json before either strength is searched. It is an empirical finite-amplitude reference, not a ceiling or a noise
estimate; R_g must be finite and above 0.5, otherwise the generator's calibrations are not usable. The target is
T = 0.5 + Q[strength] (R_g − 0.5): 'weak' 0.5, 'strong' 0.8. The latent-ranking reference (synthetic.present_latent_auc)
on the same 34 templates is reported beside it and never used as a target.

Search. The calibration grid CAL_GRID (0.2 … 3.2 and 6.4) on one calibration draw per generator and strength (phase
'calibration', common random numbers across amplitudes). Interior bracket: in ascending amplitude over the points in
[0.2, 6.4), the first adjacent pair with s(lo) < T <= s(hi), every statistic up to hi complete; the amplitude is the
linear interpolation between them. There is no usable bracket if s(0.2) >= T, if T is not reached below 6.4, or if a
statistic at or before the crossing is incomplete; the whole curve is saved and non-monotone steps are flagged, and a
later crossing is never chosen. With a bracket, a fresh check draw (phase 'check') at the amplitude is accepted within
CAL_TOL. Otherwise the one refinement: points round(a × f, 4) for f in REFINE_FACTORS, clipped to [0.2, 6.4], a point
equal to an existing one reusing it, drawn with the calibration seed; the bracket is re-read on the union by the same rule,
and its amplitude receives a NEW terminal check draw (phase 'terminal'), which alone decides; the search then stops. No
usable bracket, or a terminal check that is incomplete or outside the tolerance, makes the calibration NOT USABLE: never
retargeted or retried; its stage C cells are diagnostics (run only when an amplitude exists) and can neither pass, fail
nor drive a revision. At most 8 + 5 + 2 statistics per cell.

Seeds by phase (SEED_PHASES; v5's calibration phase 2 is retired): stage C (1, generator, strength, drift, replicate,
subject); benchmark (3, 0); reach (4, generator, draw, subject); calibration (5, generator, strength, subject); check (6,
generator, strength, subject); terminal check (7, generator, strength, subject).

±0.03 is a declared development tolerance, not a confidence interval or a demonstrated precision. The weak and strong
targets differ by 0.3 (R_g − 0.5); when that is at most 2 × CAL_TOL the acceptance bands overlap and the two strengths are
UNRESOLVED at this tolerance, and a strong check at or below the weak check is a REVERSAL. strength_resolution() reports
both; neither counts as demonstrating two distinct strengths.

Provenance. The configuration identity — battery version and result schema; the SHA-256 of every covered module as
imported and of the imported BMS port; every module SPEC; the strength, grid, refinement, tolerance, statistic and seed
constants; the effective template list with each template's digest; the events-table digest; the Python and library
versions, thread variables and effective thread pools — names results/battery/v6-<digest>/. verify_runtime() re-derives
it in the executing process (before every calibration statistic and every recording, in joblib workers too) and refuses a
mismatch or a module changed on disk since import. Reach and calibration entries carry a SHA-256 of their content, checked
on every load. A recording result is written with a sidecar holding the payload SHA-256, the manifest digest and the
schema; reuse requires all three, the manifest itself and the result schema, else it is refused. v5
(results/battery/v5-7fcb46729408/) is retained unchanged as the historical computation.

Pass criteria, evaluated on the main interval with group.decide, only on COMPLETE cells (every replicate with every
recording present): 'incomplete' otherwise; 'diagnostic: calibration not usable' for an unusable calibration;
  - G1, G2, G3, every strength × drift cell: at least 2 of the 3 replicates end in a substantive outcome (two-state,
    graded, inconclusive/mixed) and at most 1 ends 'two-state'. Technical failure, insufficient sensitivity and
    insufficient availability are not substantive: they count against the first requirement and never pass a cell.
  - X1 'strong', both drift conditions: 'two-state' in at least 2 of 3 replicates.
  - X1 'weak' and X2: 'reported' (outcome counts and diagnostics; X2 is the weak-separation stress condition).
Diagnostics per replicate: the median fitted minimum gap e^delta0 / sigma and full gap
(e^delta0 + e^delta1 lg(k_h (x - x0))) / sigma at the held-out present doses, the median absolute occupancy error, the
unadjusted high/low readout contrast (X generators: generating high against low present trials, pooled over a half's two
blocks, not conditioned on dose, hemifield or block; descriptive) and the readout-latent correlation. A failure leads to a
registered revision of the protocol and a re-run; every result and revision is retained.

CLI:  --limits | --benchmark | --reach | --calibrate [--n-jobs N] | --calibration-report | --run [--n-jobs N]
      [--generators G1,X1] | --summarize        (as a script, numerical thread variables are pinned to 1 before numpy loads)
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
if __name__ == "__main__":
    for _v in THREAD_VARS:
        os.environ[_v] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.special import expit  # noqa: E402

import decoder as DEC  # noqa: E402
import group as G  # noqa: E402
import inclusion as INC  # noqa: E402
import likelihood as LK  # noqa: E402
import recording as RC  # noqa: E402
import synthetic as SY  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results", "battery")
BMS_PATH = os.path.normpath(os.path.join(HERE, "..", "sergent_port", "bms.py"))
BATTERY_VERSION = "v6"
RESULT_SCHEMA = "melcon-battery-result-v6"
STRENGTHS = ("weak", "strong")
Q = {"weak": 0.5, "strong": 0.8}
DRIFTS = (False, True)
N_REP = 3
REACH_AMPLITUDE = 6.4
REACH_DRAWS = (0, 1)
AMP_RANGE = (0.2, 6.4)
CAL_GRID = (0.2, 0.4, 0.7, 1.0, 1.5, 2.2, 3.2, 6.4)
REFINE_FACTORS = (0.75, 0.875, 1.0, 1.125, 1.25)
REFINE_DECIMALS = 4
CAL_TOL = 0.03
SEED_PHASES = {"stage_c": 1, "benchmark": 3, "reach": 4, "calibration": 5, "check": 6, "terminal": 7}
CAL_STAT_SPEC = dict(cohort="all templates, no drift", per_recording="mean held-out AUC over 2 halves x 10 main windows",
                     aggregate="median over recordings",
                     complete="every recording decodes; every main-window AUC finite and in [0, 1]")
CODE_FILES = ("synthetic.py", "battery.py", "decoder.py", "likelihood.py", "recording.py", "group.py", "inclusion.py")
SUBSTANTIVE = ("two-state", "graded", "inconclusive/mixed")
SUMMARY_KEYS = ("windows", "models", "evidence", "available", "delta", "n_trials", "auc", "twostate_min_gap_median",
                "twostate_full_gap_median", "occupancy_abs_error_median", "readout_highlow_contrast_unadjusted_median",
                "readout_latent_corr_median")


# ----------------------------------------------------------------------------------------------------------- identity
def _sha_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


LOADED_CODE = {f: _sha_file(os.path.join(HERE, f)) for f in CODE_FILES}     # read at import, re-verified before use
LOADED_BMS = _sha_file(BMS_PATH)


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _jsonable(obj):
    return json.loads(json.dumps(obj, default=str))


def runtime() -> dict:
    import joblib
    import scipy
    import sklearn
    from threadpoolctl import threadpool_info
    return dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__,
                pandas=pd.__version__, joblib=joblib.__version__, bms_sha256=LOADED_BMS,
                thread_env={v: os.environ.get(v) for v in THREAD_VARS},
                threadpools=sorted([d["user_api"], d["internal_api"], int(d["num_threads"])] for d in threadpool_info()))


_TEMPLATE_DIGESTS: dict = {}


def template_digest(subject: int) -> str:
    return hashlib.sha256(SY.template(subject, "nocue").to_csv(index=False).encode()).hexdigest()


def template_digests(subjects: list) -> dict:
    key = (_sha_file(SY.TRIALS_CSV), tuple(subjects))
    if key not in _TEMPLATE_DIGESTS:
        _TEMPLATE_DIGESTS[key] = {str(s): template_digest(s) for s in subjects}
    return _TEMPLATE_DIGESTS[key]


def config_identity() -> dict:
    subjects = templates()
    return dict(battery_version=BATTERY_VERSION, result_schema=RESULT_SCHEMA, code=dict(LOADED_CODE),
                synthetic=SY.SPEC, decoder=DEC.SPEC, likelihood=LK.SPEC, group=G.SPEC, inclusion=INC.SPEC,
                strengths=STRENGTHS, q=Q, drifts=DRIFTS, n_rep=N_REP, reach_amplitude=REACH_AMPLITUDE,
                reach_draws=REACH_DRAWS, amplitude_range=AMP_RANGE, cal_grid=CAL_GRID, refine_factors=REFINE_FACTORS,
                refine_decimals=REFINE_DECIMALS, cal_tol=CAL_TOL, seed_phases=SEED_PHASES, calibration_statistic=CAL_STAT_SPEC,
                templates=subjects, template_digests=template_digests(subjects), events_table=_sha_file(SY.TRIALS_CSV),
                runtime=runtime())


def namespace_path(identity: dict) -> str:
    return os.path.join(OUT_DIR, f"{BATTERY_VERSION}-{digest(identity)[:12]}")


def run_directory(identity: dict | None = None) -> str:
    identity = identity or config_identity()
    d = namespace_path(identity)
    os.makedirs(os.path.join(d, "recordings"), exist_ok=True)
    path = os.path.join(d, "manifest.json")
    if os.path.exists(path):
        with open(path) as fh:
            if json.load(fh) != _jsonable(identity):
                raise RuntimeError(f"{path}: namespace manifest differs from the running configuration")
    else:
        with open(path, "w") as fh:
            json.dump(identity, fh, indent=2, default=str)
    return d


def verify_runtime(run_dir: str) -> str:
    """Re-derive the identity in THIS process and compare it with the namespace manifest; refuse a covered module or the
    BMS port changed on disk since import. Returns the identity digest."""
    changed = [f for f in CODE_FILES if _sha_file(os.path.join(HERE, f)) != LOADED_CODE[f]]
    if _sha_file(BMS_PATH) != LOADED_BMS:
        changed.append(BMS_PATH)
    if changed:
        raise RuntimeError(f"changed on disk since this process imported them: {changed}")
    identity = _jsonable(config_identity())
    path = os.path.join(run_dir, "manifest.json")
    try:
        with open(path) as fh:
            saved = json.load(fh)
    except Exception as e:
        raise RuntimeError(f"{path}: namespace manifest cannot be read") from e
    if saved != identity:
        diff = sorted(k for k in set(saved) | set(identity) if saved.get(k) != identity.get(k))
        raise RuntimeError(f"{path}: this process's configuration differs from the namespace in {diff}")
    return digest(identity)


# ---------------------------------------------------------------------------------------------------------- templates
def templates() -> list:
    """Nocue recordings passing §2 at the events-table level, in subject order."""
    df = SY.events_table()
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


def seed_tags(phase: str, generator: str, index: int, subject: int) -> tuple:
    """Calibration-side seed tags; index = the reach draw, or the strength index for calibration/check/terminal."""
    return (SEED_PHASES[phase], SY.GENERATORS.index(generator), int(index), int(subject))


# ------------------------------------------------------------------------------------------ latent-ranking reference
def latent_ranking_reference(generator: str, subjects: list) -> float:
    """Per template the mean over the two halves of the mean latent ranking AUC of the half's present trials against
    catch, then the median over templates (no drift). For X1 and X2 also the optimal population ROC; for G3 (unequal
    present and catch variances) and in general only the reference strength of the declared linear readout."""
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


def target_for(reach_value: float, strength: str) -> float:
    return 0.5 + Q[strength] * (reach_value - 0.5)


# ------------------------------------------------------------------------------------------------ calibration statistic
def _peak_rss_mb() -> float:
    import resource
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3


def recording_aucs(rec: dict) -> dict:
    """One synthetic recording's held-out AUCs in the ten main windows of both halves (2 × 10), or its failure."""
    t0 = time.time()
    try:
        dec = DEC.split_half(rec)
    except Exception as e:                                                # recorded as a failure, never dropped
        return dict(status=f"technical failure: {type(e).__name__}: {e}", auc=None, decoder_s=time.time() - t0)
    if dec["status"] != "ok":
        return dict(status=dec["status"], auc=None, decoder_s=time.time() - t0)
    halves = sorted(dec["halves"])
    return dict(status="ok", halves=[list(B) for B in halves], decoder_s=time.time() - t0,
                auc=[[float(dec["halves"][B]["auc"][w]) for w in DEC.MAIN] for B in halves])


def _cell_recording(generator: str, amplitude: float, tags: tuple, subject: int, run_dir: str | None = None) -> dict:
    if run_dir is not None:
        verify_runtime(run_dir)
    t0 = time.time()
    rec = SY.generate(SY.template(subject, "nocue"), generator, amplitude, False, tags=tags)
    gen_s = time.time() - t0
    out = recording_aucs(rec)
    out.update(subject=int(subject), tags=[int(t) for t in tags], generate_s=gen_s, worker_peak_rss_mb=_peak_rss_mb())
    return out


def calibration_statistic(rows: list, subjects: list) -> dict:
    """Median over recordings of the recording's mean main-window AUC — COMPLETE only with exactly one decoded row per
    expected subject and every one of its 2 × 10 AUCs finite and in [0, 1]; otherwise value NaN and the failures listed."""
    shape = (len(DEC.HALVES), len(DEC.MAIN))
    n_auc = len(subjects) * shape[0] * shape[1]
    failures, per, aucs, n_finite = [], [], {}, 0
    seen = [int(r["subject"]) for r in rows]
    extra = sorted({s for s in seen if s not in subjects} | {s for s in seen if seen.count(s) > 1})
    if extra:
        failures.append([extra, "unexpected or duplicated recordings"])
    by = {int(r["subject"]): r for r in rows}
    for s in subjects:
        r = by.get(int(s))
        if r is None:
            failures.append([int(s), "missing"])
            continue
        if r["status"] != "ok" or r.get("auc") is None:
            failures.append([int(s), r["status"]])
            continue
        a = np.asarray(r["auc"], dtype=float)
        aucs[str(s)] = a.tolist()
        good = np.isfinite(a) & (a >= 0.0) & (a <= 1.0)
        n_finite += int(good.sum()) if a.shape == shape else 0
        if a.shape != shape or not good.all():
            failures.append([int(s), f"{int(good.sum())} of {shape[0] * shape[1]} main-window AUCs finite in [0, 1]"])
            continue
        per.append(float(a.mean()))
    complete = not failures
    return dict(value=float(np.median(per)) if complete else float("nan"), complete=bool(complete),
                n_recordings_expected=len(subjects), n_recordings_decoded=len(per), n_auc_expected=n_auc,
                n_auc_finite=n_finite, per_template={k: float(np.mean(v)) for k, v in aucs.items()}, auc=aucs,
                failures=failures)


def draw_statistic(generator: str, amplitude: float, phase: str, index: int, subjects: list, n_jobs: int = 1,
                   run_dir: str | None = None, log=print) -> dict:
    """Generate and decode one draw of the templates at an amplitude in a seed phase; the complete statistic record."""
    tags = [seed_tags(phase, generator, index, s) for s in subjects]
    t0 = time.time()
    if n_jobs > 1:
        from joblib import Parallel, delayed
        worker = importlib.import_module("battery")._cell_recording        # by reference: workers import and verify
        rows = Parallel(n_jobs=n_jobs)(delayed(worker)(generator, float(amplitude), tg, s, run_dir) for tg, s in zip(tags, subjects))
    else:
        rows = [_cell_recording(generator, float(amplitude), tg, s, run_dir) for tg, s in zip(tags, subjects)]
    rec = calibration_statistic(rows, subjects)
    rec.update(generator=generator, phase=phase, index=int(index), amplitude=float(amplitude), tags_pattern=list(tags[0][:3]),
               seconds=dict(generate=float(sum(r.get("generate_s", 0.0) for r in rows)),
                            decoder=float(sum(r.get("decoder_s", 0.0) for r in rows)), wall=time.time() - t0),
               n_jobs=int(n_jobs), peak_rss_mb=float(max([_peak_rss_mb()] + [r.get("worker_peak_rss_mb", 0.0) for r in rows])))
    log(f"  statistic {generator} {phase}[{index}] amplitude {amplitude:.4f}: {rec['value']:.4f} complete {rec['complete']} "
        f"({rec['n_auc_finite']}/{rec['n_auc_expected']} AUCs); generate {rec['seconds']['generate']:.1f} s, decoder "
        f"{rec['seconds']['decoder']:.1f} s, wall {rec['seconds']['wall']:.1f} s, peak RSS {rec['peak_rss_mb']:.0f} MB")
    return rec


# ---------------------------------------------------------------------------------------------------- reach and search
def reach(generator: str, subjects: list, n_jobs: int = 1, run_dir: str | None = None, log=print) -> dict:
    draws = [draw_statistic(generator, REACH_AMPLITUDE, "reach", d, subjects, n_jobs, run_dir, log) for d in REACH_DRAWS]
    vals = [d["value"] for d in draws]
    complete = all(d["complete"] for d in draws)
    value = float(np.mean(vals)) if complete else float("nan")
    usable = bool(complete and np.isfinite(value) and value > 0.5)
    reason = None if usable else ("a reach draw is incomplete" if not complete else f"reach {value:.6f} gives no headroom above 0.5")
    entry = dict(generator=generator, amplitude=REACH_AMPLITUDE, subjects=[int(s) for s in subjects], draws=draws, values=vals,
                 disagreement=float(abs(vals[1] - vals[0])) if complete else float("nan"), reach=value, usable=usable,
                 unusable_reason=reason, latent_ranking_reference=latent_ranking_reference(generator, subjects),
                 targets={st: (target_for(value, st) if usable else None) for st in STRENGTHS})
    log(f"reach {generator}: {value:.4f} (draws {', '.join(f'{v:.4f}' for v in vals)}), usable {usable}; latent-ranking "
        f"reference {entry['latent_ranking_reference']:.4f}")
    return entry


def find_bracket(curve: dict, target: float) -> dict:
    """The interior bracket rule on {amplitude: statistic value (NaN if incomplete)} — see the module docstring."""
    amps = sorted(a for a in curve if AMP_RANGE[0] <= a < AMP_RANGE[1])
    if not amps:
        return dict(usable=False, reason="no amplitude in [0.2, 6.4)")
    vals = [curve[a] for a in amps]
    if not np.isfinite(vals[0]):
        return dict(usable=False, reason=f"statistic at the lowest amplitude {amps[0]} is incomplete")
    if vals[0] >= target:
        return dict(usable=False, reason=f"statistic at the lowest amplitude {amps[0]} already meets the target")
    for j in range(1, len(amps)):
        if not np.isfinite(vals[j]):
            return dict(usable=False, reason=f"statistic at amplitude {amps[j]} is incomplete before any crossing")
        if vals[j] >= target:
            lo, hi, s_lo, s_hi = amps[j - 1], amps[j], vals[j - 1], vals[j]
            return dict(usable=True, lo=lo, hi=hi, s_lo=s_lo, s_hi=s_hi,
                        amplitude=float(lo + (target - s_lo) * (hi - lo) / (s_hi - s_lo)))
    return dict(usable=False, reason="target not reached below the top amplitude 6.4")


def nonmonotone_steps(curve: dict) -> list:
    pts = [(a, curve[a]) for a in sorted(curve) if np.isfinite(curve[a])]
    return [[a0, a1, v0, v1] for (a0, v0), (a1, v1) in zip(pts, pts[1:]) if v1 < v0]


def refinement_points(amplitude: float) -> list:
    return sorted({float(np.clip(round(amplitude * f, REFINE_DECIMALS), *AMP_RANGE)) for f in REFINE_FACTORS})


def _within(stat: dict, target: float) -> bool:
    return bool(stat["complete"] and abs(stat["value"] - target) <= CAL_TOL)


def calibrate(generator: str, strength: str, reach_entry: dict, subjects: list, n_jobs: int = 1, run_dir: str | None = None,
              log=print) -> dict:
    si = STRENGTHS.index(strength)
    entry = dict(generator=generator, strength=strength, q=Q[strength], tolerance=CAL_TOL, subjects=[int(s) for s in subjects],
                 reach=reach_entry["reach"], reach_sha256=reach_entry["sha256"],
                 latent_ranking_reference=reach_entry["latent_ranking_reference"], target=None, grid=[], curve={},
                 first_bracket=None, nonmonotone=[], first_check=None, refinement=None, terminal_check=None, amplitude=None,
                 check=None, accepted=False, unusable_reason=None, statistics_drawn=0)

    def done(**kw):
        entry.update(kw)
        log(f"{generator} {strength}: target {entry['target']}, -> amplitude {entry['amplitude']}, check {entry['check']}, "
            f"accepted {entry['accepted']}" + (f" ({entry['unusable_reason']})" if entry["unusable_reason"] else ""))
        return entry

    if not reach_entry["usable"]:
        return done(unusable_reason=f"reach not usable: {reach_entry['unusable_reason']}")
    target = target_for(reach_entry["reach"], strength)
    entry["target"] = target
    stats = {}
    for a in CAL_GRID:
        stats[float(a)] = draw_statistic(generator, float(a), "calibration", si, subjects, n_jobs, run_dir, log)
    entry["grid"] = [stats[a] for a in sorted(stats)]
    curve = {a: s["value"] for a, s in stats.items()}
    entry.update(curve={str(a): v for a, v in sorted(curve.items())}, nonmonotone=nonmonotone_steps(curve),
                 statistics_drawn=len(stats))
    br = find_bracket(curve, target)
    entry["first_bracket"] = br
    if not br["usable"]:
        return done(unusable_reason=f"no usable bracket: {br['reason']}")
    chk = draw_statistic(generator, br["amplitude"], "check", si, subjects, n_jobs, run_dir, log)
    entry["statistics_drawn"] += 1
    entry["first_check"] = dict(amplitude=br["amplitude"], within_tolerance=_within(chk, target), statistic=chk)
    if _within(chk, target):
        return done(amplitude=br["amplitude"], check=chk["value"], accepted=True)
    reason = "first check incomplete" if not chk["complete"] else f"first check {chk['value']:.6f} outside +-{CAL_TOL} of the target"
    pts = refinement_points(br["amplitude"])
    new = {}
    for p in pts:
        if p not in stats:
            new[p] = draw_statistic(generator, p, "calibration", si, subjects, n_jobs, run_dir, log)
    entry["statistics_drawn"] += len(new)
    union = {**curve, **{p: s["value"] for p, s in new.items()}}
    br2 = find_bracket(union, target)
    entry["refinement"] = dict(reason=reason, points=pts, reused=[p for p in pts if p in stats],
                               statistics=[new[p] for p in sorted(new)], curve={str(a): v for a, v in sorted(union.items())},
                               nonmonotone=nonmonotone_steps(union), bracket=br2)
    if not br2["usable"]:
        return done(unusable_reason=f"no usable bracket after the refinement: {br2['reason']}")
    term = draw_statistic(generator, br2["amplitude"], "terminal", si, subjects, n_jobs, run_dir, log)
    entry["statistics_drawn"] += 1
    ok = _within(term, target)
    entry["terminal_check"] = dict(amplitude=br2["amplitude"], within_tolerance=ok, statistic=term)
    return done(amplitude=br2["amplitude"], check=term["value"], accepted=ok,
                unusable_reason=None if ok else ("terminal check incomplete" if not term["complete"]
                                                 else f"terminal check {term['value']:.6f} outside +-{CAL_TOL} of the target"))


def strength_resolution(reach_store: dict, cal_store: dict) -> dict:
    """Per generator: the target gap 0.3 (R - 0.5) against the two tolerance bands, the achieved checks, reversal."""
    out = {}
    for g in SY.GENERATORS:
        r = reach_store.get(g)
        if r is None or not r["usable"]:
            out[g] = dict(status="reach missing" if r is None else f"reach not usable: {r['unusable_reason']}")
            continue
        tw, ts = target_for(r["reach"], "weak"), target_for(r["reach"], "strong")
        w, s = cal_store.get((g, "weak")), cal_store.get((g, "strong"))

        def chk(e):
            return float(e["check"]) if e is not None and e.get("check") is not None else float("nan")
        cw, cs = chk(w), chk(s)
        both = bool(w is not None and s is not None and w["accepted"] and s["accepted"])
        overlap = bool(ts - tw <= 2 * CAL_TOL)
        diff = cs - cw
        reversal = bool(np.isfinite(diff) and diff <= 0)
        out[g] = dict(reach=r["reach"], target_weak=tw, target_strong=ts, target_gap=ts - tw, bands_overlap=overlap,
                      check_weak=cw, check_strong=cs, achieved_difference=diff, reversal=reversal, both_accepted=both,
                      resolved=bool(both and not overlap and not reversal))
    return out


# ------------------------------------------------------------------------------------------- sealed append-only stores
def seal(entry: dict) -> dict:
    body = {k: v for k, v in _jsonable(entry).items() if k != "sha256"}
    return dict(body, sha256=digest(body))


def _store_key(name: str, e: dict):
    return e["generator"] if name == "reach" else (e["generator"], e["strength"])


def load_store(run_dir: str, name: str) -> dict:
    """reach.json or calibration.json in a namespace; every entry's content SHA-256 is checked, a damaged file refused."""
    path = os.path.join(run_dir, f"{name}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            entries = json.load(fh)
    except Exception as e:
        raise RuntimeError(f"{path}: cannot be read") from e
    out = {}
    for e in entries:
        body = {k: v for k, v in e.items() if k != "sha256"}
        if e.get("sha256") != digest(body):
            raise RuntimeError(f"{path}: entry {e.get('generator')}/{e.get('strength', '')} is damaged (content SHA-256 mismatch)")
        out[_store_key(name, e)] = e
    return out


def load_calibration(run_dir: str) -> dict:
    return load_store(run_dir, "calibration")


def save_store(run_dir: str, name: str, entry: dict) -> dict:
    """Add one sealed entry under an exclusive lock, re-reading the file first, so that separate processes never
    overwrite each other; an existing entry is never replaced."""
    import fcntl
    path = os.path.join(run_dir, f"{name}.json")
    sealed = seal(entry)
    with open(path + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        entries = load_store(run_dir, name)
        key = _store_key(name, sealed)
        if key in entries:
            raise RuntimeError(f"{name} entry {key} already exists in {run_dir}; entries are never replaced")
        entries[key] = sealed
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(list(entries.values()), fh, indent=1)
        os.replace(tmp, path)
    return sealed


# ----------------------------------------------------------------------------------------------------------- recordings
def summary(res: dict) -> dict:
    """What the group rule and the diagnostics need from one recording result (no epochs, no per-start records)."""
    keep = {k: res[k] for k in ("status", "subject", "task")}
    if "section2" in res:
        keep["section2"] = res["section2"]
    if res["status"] != "ok":
        return keep
    min_gap, full_gap, occ_err, read_contrast, read_corr = [], [], [], [], []
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
            if "high_true" in tr and tr["high_true"].to_numpy(bool)[pres].any():
                hi_m = tr["high_true"].to_numpy(bool) & pres
                lo_m = ~tr["high_true"].to_numpy(bool) & pres
                if hi_m.sum() >= 2 and lo_m.sum() >= 2:
                    pooled = np.sqrt((np.var(y[hi_m], ddof=1) + np.var(y[lo_m], ddof=1)) / 2)
                    if pooled > 0:
                        read_contrast.append(float((y[hi_m].mean() - y[lo_m].mean()) / pooled))
            if "z_true" in tr and np.std(y[pres]) > 0:
                read_corr.append(float(np.corrcoef(y[pres], tr["z_true"].to_numpy(float)[pres])[0, 1]))

    def med(v):
        return float(np.median(v)) if v else np.nan
    keep.update(windows=res["windows"], models=res["models"], evidence=res["evidence"], available=res["available"],
                delta=res["delta"], n_trials=res["n_trials"], auc=res["auc"],
                twostate_min_gap_median=med(min_gap), twostate_full_gap_median=med(full_gap),
                occupancy_abs_error_median=med(occ_err), readout_highlow_contrast_unadjusted_median=med(read_contrast),
                readout_latent_corr_median=med(read_corr))
    return keep


def check_schema(res: dict) -> None:
    """A stored recording result must be a summary() with its manifest: every key, and array shapes for 'ok'."""
    if not isinstance(res, dict) or not {"status", "subject", "task", "manifest"} <= set(res):
        raise RuntimeError("result schema: status, subject, task or manifest missing")
    if res["status"] != "ok":
        return
    missing = [k for k in SUMMARY_KEYS if k not in res]
    if missing:
        raise RuntimeError(f"result schema: keys missing {missing}")
    nW, nM = len(res["windows"]), len(res["models"])
    shapes = dict(evidence=(nW, nM), available=(nW, nM), delta=(nW,), n_trials=(nW,), auc=(nW, 2))
    bad = [k for k, sh in shapes.items() if np.shape(res[k]) != sh]
    if nW != len(RC.WINDOWS) or bad:
        raise RuntimeError(f"result schema: {nW} windows, shapes wrong for {bad}")


def main_positions(res_windows) -> list:
    return [res_windows.index(w) for w in DEC.MAIN]


def recording_manifest(identity_digest: str, generator: str, strength_i: int, drift_i: int, rep: int, subject: int,
                       cal_entry: dict) -> dict:
    return dict(config=identity_digest, generator=generator, strength=STRENGTHS[strength_i], drift=bool(DRIFTS[drift_i]),
                replicate=int(rep), subject=int(subject),
                tags=[SEED_PHASES["stage_c"], SY.GENERATORS.index(generator), int(strength_i), int(drift_i), int(rep), int(subject)],
                amplitude=float(cal_entry["amplitude"]), calibration=cal_entry["sha256"],
                calibration_accepted=bool(cal_entry["accepted"]), template=template_digest(subject))


def write_result(path: str, res: dict) -> None:
    buf = io.BytesIO()
    np.save(buf, np.array([res], dtype=object), allow_pickle=True)
    data = buf.getvalue()
    side = dict(sha256=hashlib.sha256(data).hexdigest(), manifest=digest(res["manifest"]), schema=RESULT_SCHEMA)
    for p, payload in ((path, data), (path + ".sha256", json.dumps(side).encode())):
        with open(p + ".tmp", "wb") as fh:
            fh.write(payload)
        os.replace(p + ".tmp", p)


def load_verified(path: str, manifest: dict) -> dict:
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        with open(path + ".sha256") as fh:
            side = json.load(fh)
    except Exception as e:
        raise RuntimeError(f"{path}: existing result or its checksum sidecar cannot be read ({type(e).__name__}); "
                           "results are never overwritten") from e
    if hashlib.sha256(data).hexdigest() != side.get("sha256"):
        raise RuntimeError(f"{path}: payload SHA-256 differs from its sidecar (damaged result)")
    if side.get("manifest") != digest(manifest) or side.get("schema") != RESULT_SCHEMA:
        raise RuntimeError(f"{path}: sidecar names another identity or schema; revisions use a new namespace")
    try:
        res = np.load(io.BytesIO(data), allow_pickle=True)[0]
    except Exception as e:
        raise RuntimeError(f"{path}: payload cannot be decoded ({type(e).__name__})") from e
    if not isinstance(res, dict) or res.get("manifest") != manifest:
        raise RuntimeError(f"{path}: existing result has a different identity; revisions use a new namespace")
    check_schema(res)
    return res


def run_recording(manifest: dict, path: str) -> str:
    if os.path.exists(path) or os.path.exists(path + ".sha256"):
        load_verified(path, manifest)
        return path
    run_dir = os.path.dirname(os.path.dirname(path))
    if verify_runtime(run_dir) != manifest["config"]:
        raise RuntimeError(f"{path}: manifest names another configuration than this namespace")
    rec = SY.generate(SY.template(manifest["subject"], "nocue"), manifest["generator"], manifest["amplitude"],
                      manifest["drift"], tags=tuple(manifest["tags"]))
    res = summary(RC.recording_scores(rec, manifest["subject"], "nocue"))
    res["manifest"] = manifest
    check_schema(res)
    write_result(path, res)
    return path


def cell_path(run_dir, generator, strength_i, drift_i, rep, subject):
    return os.path.join(run_dir, "recordings", f"{generator}_{STRENGTHS[strength_i]}_d{drift_i}_r{rep}_sub-{subject:02d}.npy")


# ------------------------------------------------------------------------------------------------------------- verdicts
def cell_verdicts(outcomes: dict, calibration_usable: dict | None = None, expected=None, n_rep: int = N_REP) -> dict:
    """outcomes {(generator, strength, drift_i): [outcome or None per replicate]} -> the §9 verdicts. A calibrated but
    unusable cell is a diagnostic (and says so if it is also incomplete, e.g. not run for want of an amplitude); a
    missing or incomplete replicate (None) otherwise makes the cell 'incomplete'."""
    keys = list(expected) if expected is not None else list(outcomes)
    out = {}
    for key in keys:
        g, strength, _ = key
        reps = list(outcomes.get(key, []))
        incomplete = len(reps) < n_rep or any(o is None for o in reps)
        if calibration_usable is not None and (g, strength) in calibration_usable and not calibration_usable[(g, strength)]:
            out[key] = "diagnostic: calibration not usable" + ("; incomplete" if incomplete else "")
        elif incomplete:
            out[key] = "incomplete"
        elif g in ("G1", "G2", "G3"):
            ok = sum(o in SUBSTANTIVE for o in reps) >= 2 and sum(o == "two-state" for o in reps) <= 1
            out[key] = "pass" if ok else "fail"
        elif g == "X1" and strength == "strong":
            out[key] = "pass" if sum(o == "two-state" for o in reps) >= 2 else "fail"
        else:
            out[key] = "reported"
    return out


# ----------------------------------------------------------------------------------------------------------------- main
def calibration_table(reach_store: dict, cal: dict) -> pd.DataFrame:
    rows = []
    for g in SY.GENERATORS:
        r = reach_store.get(g)
        for st in STRENGTHS:
            e = cal.get((g, st))
            rows.append(dict(generator=g, strength=st, reach=r["reach"] if r else np.nan,
                             reach_disagreement=r["disagreement"] if r else np.nan,
                             latent_ranking_reference=r["latent_ranking_reference"] if r else np.nan,
                             target=e["target"] if e else np.nan, amplitude=e["amplitude"] if e else None,
                             check=e["check"] if e else None, accepted=e["accepted"] if e else None,
                             refined=bool(e and e["refinement"]), statistics_drawn=e["statistics_drawn"] if e else 0,
                             nonmonotone=len(e["nonmonotone"]) if e else 0,
                             unusable_reason=e["unusable_reason"] if e else "not calibrated"))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("--benchmark", "--limits", "--reach", "--calibrate", "--calibration-report", "--run", "--summarize"):
        ap.add_argument(flag, action="store_true")
    ap.add_argument("--generators", default=",".join(SY.GENERATORS))
    ap.add_argument("--n-jobs", type=int, default=1)
    a = ap.parse_args()
    subjects = templates()
    gens = a.generators.split(",")
    identity = config_identity()
    ident = digest(identity)
    run_dir = run_directory(identity)
    print(f"namespace {run_dir}", flush=True)
    log = lambda s: print(s, flush=True)                                # noqa: E731
    if a.limits:
        rows = [dict(generator=g, latent_ranking_reference_all=latent_ranking_reference(g, subjects),
                     latent_ranking_reference_first_eight=latent_ranking_reference(g, subjects[:8])) for g in gens]
        print(pd.DataFrame(rows).to_string())
        pd.DataFrame(rows).to_csv(os.path.join(run_dir, "limits.csv"), index=False)
    if a.benchmark:
        t0 = time.time()
        rec = SY.generate(SY.template(subjects[0], "nocue"), "X1", 1.0, False, tags=(SEED_PHASES["benchmark"], 0))
        t1 = time.time()
        recording_aucs(rec)
        t2 = time.time()
        res = RC.recording_scores(rec, subjects[0], "nocue")
        t3 = time.time()
        n_stat = len(subjects)
        info = dict(templates=len(subjects), status=res["status"], generate_s=t1 - t0, decoder_only_s=t2 - t1,
                    pipeline_s=t3 - t2, recordings_stage_c=2040, projected_stage_c_core_hours=2040 * (t1 - t0 + t3 - t2) / 3600,
                    calibration_calls=dict(reach=len(SY.GENERATORS) * len(REACH_DRAWS) * n_stat,
                                           cells_min=len(SY.GENERATORS) * len(STRENGTHS) * (len(CAL_GRID) + 1) * n_stat,
                                           cells_max=len(SY.GENERATORS) * len(STRENGTHS) * (len(CAL_GRID) + len(REFINE_FACTORS) + 2) * n_stat),
                    note="one worker on a machine shared with the refit probe; planning evidence, not a measured calibration")
        info["projected_calibration_core_hours"] = [(info["calibration_calls"]["reach"] + info["calibration_calls"][k]) *
                                                    (t2 - t0) / 3600 for k in ("cells_min", "cells_max")]
        print(json.dumps(info, indent=2))
        with open(os.path.join(run_dir, "benchmark.json"), "w") as fh:
            json.dump(info, fh, indent=2)
    if a.reach or a.calibrate:
        for g in gens:
            if g not in load_store(run_dir, "reach"):
                save_store(run_dir, "reach", reach(g, subjects, a.n_jobs, run_dir, log))
    if a.calibrate:
        for g in gens:
            r = load_store(run_dir, "reach")[g]                         # frozen before either strength is searched
            for st in STRENGTHS:
                if (g, st) in load_calibration(run_dir):
                    continue
                save_store(run_dir, "calibration", calibrate(g, st, r, subjects, a.n_jobs, run_dir, log))
    if a.calibration_report or a.calibrate or a.summarize:
        reach_store, cal = load_store(run_dir, "reach"), load_calibration(run_dir)
        print(calibration_table(reach_store, cal).to_string())
        res_ = strength_resolution(reach_store, cal)
        print(json.dumps(res_, indent=1))
        with open(os.path.join(run_dir, "strengths.json"), "w") as fh:
            json.dump(res_, fh, indent=2)
    if a.run:
        cal = load_calibration(run_dir)
        missing = [(g, st) for g in gens for st in STRENGTHS if (g, st) not in cal]
        if missing:
            raise SystemExit(f"calibrate first: {missing}")
        skipped = [(g, st) for g in gens for st in STRENGTHS if cal[(g, st)]["amplitude"] is None]
        if skipped:
            print(f"not run (calibration not usable, no amplitude; diagnostic): {skipped}", flush=True)
        jobs = [(recording_manifest(ident, g, si, di, r, s, cal[(g, STRENGTHS[si])]), cell_path(run_dir, g, si, di, r, s))
                for g in gens for si in range(len(STRENGTHS)) if (g, STRENGTHS[si]) not in skipped
                for di in range(len(DRIFTS)) for r in range(N_REP) for s in subjects]
        if a.n_jobs > 1:
            from joblib import Parallel, delayed
            worker = importlib.import_module("battery").run_recording
            Parallel(n_jobs=a.n_jobs)(delayed(worker)(*j) for j in jobs)
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
                        if entry is None or entry["amplitude"] is None or n_missing:
                            outcomes.setdefault(key, []).append(None)
                            rows.append(dict(base, outcome="incomplete" if entry and entry["amplitude"] is not None else "not run",
                                             n_missing=n_missing))
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
                                         readout_highlow_contrast_unadjusted=med("readout_highlow_contrast_unadjusted_median"),
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
