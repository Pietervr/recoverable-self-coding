#!/usr/bin/env python3
"""jitter/bench.py — the measured-throughput benchmark of DESIGN_jitter.md rev 6 §8 ("Before launch: benchmark one
participant's full §4 set, a profile (both start rules), a generator fit, a c₀ pair and the inherited pipeline
including BMS … steady-state value + gradient to convergence from all starts; completed-dataset throughput at
N-way concurrency; compile time separately; cost the frozen manifest from measured rates").

Stage discipline (§0): real data enter only through the §7.1 GENERATOR fits (S1). Every cross-validated batch,
full-data fit, profile and c₀ pair below runs on SYNTHETIC participants generated from the real participant's
generator configurations (W2 = fitted G3, T1 = fitted B3, the c₀ pair from G3 at (0, fitted)), so no real-data
cross-validated fit or real profile exists before S5. Reported: timings, convergence statistics and the generator
parameter summary (permitted at S1); synthetic held-out scores are kept only as a self-check.

    ../../t1_access/.venv/bin/python bench.py --subject 10 --workers 12
Outputs results/bench/bench_<UTC>.json and .md.
"""
from __future__ import annotations

import os

os.environ.setdefault("NPROC", "1")

import argparse  # noqa: E402
import datetime as _dt  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
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

CANDIDATES = M.MODEL_NAMES                 # G0 G1+ G2 G3+ B0 B1+ B2 B3+
DECISION_MIX = ("G2", "B2", "G3+", "B3+")  # the §7.3 decision batch (80 starts per participant-dataset)
EPS_MIX = ("G0", "B0")

# DESIGN §8 manifest, in starts (2-start profiles, no contingency) — kept verbatim so the costing is traceable
MANIFEST = dict(
    S2_decision=120_000, S2_profile_constrained=10_400, S2_misc=20_000,
    real_cv=6_400, real_generator=400, real_full=640, real_profile_constrained=1_200, real_sensitivities=25_600,
    S4a_epsilon=40_000, S4a_pilots=160_000, S4a_certification=160_000, S4a_recertification=160_000, S4a_c0=8_000,
    S4b_decision=1_840_000, S4b_recovery=416_000, S4b_profile_constrained=780_000,
    S4b_inherited_nm_runs=15_105_000, S4b_bms_calls=50_350,
)


def _machine():
    info = dict(platform=platform.platform(), python=platform.python_version(), cpu_count=os.cpu_count())
    try:
        out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string", "hw.perflevel0.physicalcpu",
                              "hw.perflevel1.physicalcpu", "hw.memsize"], capture_output=True, text=True, timeout=5)
        parts = out.stdout.split("\n")
        info.update(cpu=parts[0], p_cores=int(parts[1]), e_cores=int(parts[2]), mem_gb=round(int(parts[3]) / 2 ** 30))
    except Exception:  # noqa
        pass
    import jax
    info.update(jax=jax.__version__, numpy=np.__version__, code_hash=M.code_hash())
    return info


def _start_stats(results: list) -> dict:
    """Per-start timing/convergence statistics over a list of FitResults."""
    secs, nit, nfev, conv, retries, early, attempts = [], [], [], 0, 0, 0, 0
    for r in results:
        for s in r.starts:
            secs.append(s.seconds); nit.append(s.nit); nfev.append(s.nfev)
            conv += s.status == "CONVERGED"; retries += s.retries; early += s.early; attempts += len(s.attempts)
    n = len(secs)
    return dict(n_starts=n, seconds_mean=float(np.mean(secs)) if n else None, seconds_median=float(np.median(secs)) if n else None,
                seconds_max=float(np.max(secs)) if n else None, nit_mean=float(np.mean(nit)) if n else None,
                nfev_mean=float(np.mean(nfev)) if n else None, converged=conv, retries=retries, early=early,
                attempts=attempts, unavailable=sum(1 for r in results if not r.available))


def timed_fit(sp, ds, info=None):
    t0 = _time.time()
    r = F.fit_model(sp, ds, info=info)
    return r, _time.time() - t0


def compile_times(ds) -> dict:
    out = {}
    for name in CANDIDATES:
        sp = M.spec(name)
        M.functions.cache_clear()
        obj = M.Objective(sp, ds)
        th = F.start_vectors(sp, F.start_info(sp, ds))[0][1]
        t0 = _time.time(); obj(th); c1 = _time.time() - t0
        t0 = _time.time(); obj(th); c2 = _time.time() - t0
        t0 = _time.time(); obj.trial_loglik(th); c3 = _time.time() - t0
        t0 = _time.time(); obj.trial_loglik(th); c4 = _time.time() - t0
        out[name] = dict(value_grad_compile_s=c1, value_grad_call_ms=1000 * c2, per_trial_compile_s=c3,
                         per_trial_call_ms=1000 * c4, n_params=sp.n_params)
    return out


def cv_batch_sequential(p: D.Participant, span_name="primary") -> dict:
    """5 folds × 8 candidates × 4 starts, timed per spec; selected models built; synthetic held-out scores."""
    sp_ = D.span(span_name)
    per_spec = {n: [] for n in CANDIDATES}
    selected_flags = {n: [] for n in M.SELECTED_NAMES}
    fold_sums = {n: [] for n in F.FULL_MODELS}
    t0 = _time.time()
    for fold in range(5):
        train, test, _, _ = D.fold_datasets(p, sp_, fold)
        cache = F.FitCache()
        res = F.fit_all_models(train, cache, span_name)
        for n in CANDIDATES:
            per_spec[n].append(res[n])
        for n in M.SELECTED_NAMES:
            selected_flags[n].append(dict(selection=res[n].selection, flags=res[n].flags))
        for m in F.FULL_MODELS:
            r = res[m]
            if r.available:
                ll = F.score_heldout(F.selected_spec(m, r, span_name), r, test)
                fold_sums[m].append(float(np.sum(ll)))
            else:
                fold_sums[m].append(float("nan"))
    wall = _time.time() - t0
    stats = {n: _start_stats(per_spec[n]) for n in CANDIDATES}
    n_starts = sum(s["n_starts"] for s in stats.values())
    return dict(wall_s=wall, n_starts=n_starts, starts_per_s=n_starts / wall, per_spec=stats,
                selected=selected_flags, fold_sums=fold_sums, n_scored=D.n_scored(p))


def full_data_fits(p: D.Participant, span_name="primary"):
    ds = D.full_dataset(p, D.span(span_name))
    cache = F.FitCache()
    t0 = _time.time()
    res = F.fit_all_models(ds, cache, span_name)
    wall = _time.time() - t0
    stats = {n: _start_stats([res[n]]) for n in CANDIDATES}
    return ds, cache, res, dict(wall_s=wall, per_spec=stats, n_starts=sum(s["n_starts"] for s in stats.values()),
                               selected={n: dict(selection=res[n].selection, flags=res[n].flags) for n in M.SELECTED_NAMES})


def profile_timing(family, ds, cache, res, span_name="primary", n_starts=2) -> dict:
    unres = res[family + "3"]
    if not unres.available:
        return dict(status="UNAVAILABLE (unrestricted fit)")
    ev, log = F.profile_evaluator(family, ds, unres, span_name, cache, n_starts=n_starts)
    t0 = _time.time()
    pr = X.hull_search(ev, unres.loglik, c0=X.CHI2_95)      # c0 PROVISIONAL (χ²₁ 0.95); the real c0 comes from S4a
    wall = _time.time() - t0
    fits = [r for s, r in log.items() if s > 0.0]
    st = _start_stats(fits)
    d = pr.as_dict(); d.pop("ell", None); d.pop("q", None)
    return dict(wall_s=wall, n_constrained_fits=len(fits), start_stats=st, profile=d, c0_provisional=X.CHI2_95,
                unrestricted=dict(selection=unres.selection, loglik=unres.loglik,
                                  s_tau_ms=M.unpack(F.selected_spec(family + "3", unres, span_name), unres.theta).s_tau_ms))


def c0_pair(cfg_g3, base: D.Participant, seed: int, span_name="primary") -> dict:
    """One zero-jitter dataset from the G3 generator at (0, fitted) → G2 and G3+ on primary full data → q(0)."""
    cfg0 = S.with_nuisance(cfg_g3, 0.0, cfg_g3.s_g)
    syn = S.generate(cfg0, base.levels, base.blocks, seed, "W").participant(901)
    ds = D.full_dataset(syn, D.span(span_name))
    t0 = _time.time()
    red, _ = timed_fit(M.spec("G2", span_name), ds)
    pos, _ = timed_fit(M.spec("G3+", span_name), ds)
    wall = _time.time() - t0
    q0 = X.q0_statistic(red.loglik if red.available else None, pos.loglik if pos.available else None)
    return dict(wall_s=wall, start_stats=_start_stats([red, pos]), q0=q0,
                reduced=dict(status=red.status, loglik=red.loglik), positive=dict(status=pos.status, loglik=pos.loglik))


def inherited_timing(syn: D.Participant, nsamp=1_000_000) -> dict:
    t0 = _time.time()
    lme = S.inherited_fits(syn.W53, syn.levels, syn.blocks)
    t_fit = _time.time() - t0
    from bms import spm_bms
    rng = np.random.default_rng(0)
    L = np.stack([lme + rng.normal(0, 0.5, size=lme.shape) for _ in range(20)])
    t0 = _time.time()
    for w in range(53):
        spm_bms(L[:, w, :], nsamp=nsamp, rng=rng)
    t_bms = _time.time() - t0
    return dict(nm_runs=795, nm_wall_s=t_fit, nm_s_per_run=t_fit / 795, bms_calls=53, bms_wall_s=t_bms,
                bms_s_per_call=t_bms / 53, nsamp=nsamp)


def _parallel_task(payload, fold, name, span_name):
    """One (fold, candidate) fit in a worker process."""
    os.environ.setdefault("NPROC", "1")
    import data as Dw, fit as Fw, models as Mw
    p = Dw.Participant(**payload)
    train, _, _, _ = Dw.fold_datasets(p, Dw.span(span_name), fold)
    t0 = _time.time()
    r = Fw.fit_model(Mw.spec(name, span_name), train)
    return dict(fold=fold, name=name, seconds=_time.time() - t0, n_starts=len(r.starts),
                converged=sum(s.status == "CONVERGED" for s in r.starts), status=r.status)


def parallel_throughput(p: D.Participant, workers: int, span_name="primary") -> dict:
    from joblib import Parallel, delayed
    payload = dict(subject=p.subject, session=p.session, tag=p.tag, W53=p.W53, fpreds=None, time_ms=p.time_ms,
                   levels=p.levels, blocks=p.blocks, data_id=p.data_id)
    tasks = [(fold, name) for fold in range(5) for name in CANDIDATES]
    t0 = _time.time()
    out = Parallel(n_jobs=workers, backend="loky")(delayed(_parallel_task)(payload, f, n, span_name) for f, n in tasks)
    wall = _time.time() - t0
    n_starts = sum(o["n_starts"] for o in out)
    return dict(workers=workers, wall_s=wall, n_tasks=len(tasks), n_starts=n_starts, starts_per_s=n_starts / wall,
                worker_seconds_sum=sum(o["seconds"] for o in out),
                converged=sum(o["converged"] for o in out), unavailable=sum(o["status"] != "AVAILABLE" for o in out))


def cost_projection(cv, full, prof2, prof4, gen_stats, c0, inh, par) -> dict:
    """Core-hours of the §8 manifest from measured per-start seconds, by category, on this machine."""
    def mean_secs(stats, names):
        return float(np.mean([stats[n]["seconds_mean"] for n in names]))
    t_dec = mean_secs(cv["per_spec"], DECISION_MIX)
    t_cv_all = mean_secs(cv["per_spec"], CANDIDATES)
    t_eps = mean_secs(cv["per_spec"], EPS_MIX)
    t_rec = mean_secs(full["per_spec"], CANDIDATES)
    t_c0 = mean_secs(full["per_spec"], DECISION_MIX)
    t_prof2 = prof2["start_stats"]["seconds_mean"]
    t_prof4 = prof4["start_stats"]["seconds_mean"] if prof4 and "start_stats" in prof4 else t_prof2
    t_gen = gen_stats["seconds_mean"]
    t_nm, t_bms = inh["nm_s_per_run"], inh["bms_s_per_call"]
    m = MANIFEST
    sec = dict(
        S2=m["S2_decision"] * t_dec + m["S2_profile_constrained"] * t_prof4 + m["S2_misc"] * t_rec,
        real=m["real_cv"] * t_cv_all + m["real_generator"] * t_gen + m["real_full"] * t_rec
             + m["real_profile_constrained"] * t_prof2 + m["real_sensitivities"] * t_cv_all,
        S4a=m["S4a_epsilon"] * t_eps + (m["S4a_pilots"] + m["S4a_certification"]) * t_dec + m["S4a_c0"] * t_c0,
        S4a_recertification_contingency=m["S4a_recertification"] * t_dec,
        S4b_fits=m["S4b_decision"] * t_dec + m["S4b_recovery"] * t_rec + m["S4b_profile_constrained"] * t_prof2,
        S4b_profiles_4start_extra=m["S4b_profile_constrained"] * (2 * t_prof4 - t_prof2),
        S4b_inherited=m["S4b_inherited_nm_runs"] * t_nm + m["S4b_bms_calls"] * t_bms,
    )
    ch = {k: v / 3600.0 for k, v in sec.items()}
    base = ch["S4a"] + ch["S4b_fits"] + ch["S4b_inherited"]
    worst = base + ch["S4a_recertification_contingency"] + ch["S4b_profiles_4start_extra"]
    eff = par["starts_per_s"] / (par["workers"] * cv["starts_per_s"]) if par else None
    return dict(per_start_seconds=dict(decision_mix=t_dec, cv_all_models=t_cv_all, epsilon_mix=t_eps,
                                       recovery_full_data=t_rec, c0_pair=t_c0, profile_2start=t_prof2,
                                       profile_4start=t_prof4, generator=t_gen, inherited_nm_run=t_nm, bms_call=t_bms),
                core_hours=ch, S4_core_hours_base=base, S4_core_hours_worst=worst,
                S2_core_hours=ch["S2"], real_core_hours=ch["real"],
                parallel_efficiency=eff,
                mac_wall_days=None if not par else dict(
                    S4_base=base / (par["workers"] * eff) / 24.0, S4_worst=worst / (par["workers"] * eff) / 24.0,
                    S2=ch["S2"] / (par["workers"] * eff) / 24.0, real=ch["real"] / (par["workers"] * eff) / 24.0),
                design_assumption_s_per_start=30.0, design_core_hours_quoted="29,000-36,800")


def to_markdown(R: dict) -> str:
    L = []
    mi = R["machine"]
    L.append(f"# Jitter study benchmark — {R['utc']} — S{R['subject']} ({mi.get('cpu', mi['platform'])}, "
             f"{mi.get('p_cores', '?')}P+{mi.get('e_cores', '?')}E cores, jax {mi['jax']}, code {mi['code_hash']})")
    L.append("")
    L.append("Real data enter only through the §7.1 generator fits; every timed batch below runs on synthetic "
             "participants from those generators (W2 = fitted G3, T1 = fitted B3). c₀ in the profiles is the provisional "
             "χ²₁(0.95); the real c₀ comes from S4a.")
    L.append("")
    g = R["generator"]
    L.append(f"## Generator fits (real S{R['subject']}, whole epoch, {g['n_starts']} starts, {g['wall_s']:.1f} s wall)")
    L.append("")
    L.append("| model | selection | s_tau ms | s_g | a(1..5) | A(1..5) | strength | converged |")
    L.append("|---|---|---|---|---|---|---|---|")
    for name in ("G3", "B3", "B0"):
        s = g["summary"][name]
        if s.get("status") != "AVAILABLE":
            L.append(f"| {name} | UNAVAILABLE | | | | | | |")
            continue
        A = ", ".join(f"{v:.2f}" for v in s.get("A", [])) if "A" in s else "—"
        L.append(f"| {name} | {s['selection']} | {s['s_tau_ms']:.1f} | {s['s_g']:.2f} | "
                 f"{', '.join(f'{v:.2f}' for v in s['a'])} | {A} | {g['strength'][name]:.3f} | {s['n_converged']}/4 |")
    L.append("")
    L.append("## Per-start timing (sequential, one process, one XLA thread)")
    L.append("")
    L.append("| batch | spec | starts | mean s | median s | max s | nit | converged | retries | unavailable |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for batch, key in (("CV train (W2)", "cv_sequential"), ("full data (W2)", "full_W2"), ("full data (T1)", "full_T1")):
        for n in CANDIDATES:
            s = R[key]["per_spec"][n]
            L.append(f"| {batch} | {n} | {s['n_starts']} | {s['seconds_mean']:.3f} | {s['seconds_median']:.3f} | "
                     f"{s['seconds_max']:.3f} | {s['nit_mean']:.0f} | {s['converged']}/{s['n_starts']} | {s['retries']} | {s['unavailable']} |")
    for fam in ("G", "B"):
        for k, lab in (("profile2", "2 starts"), ("profile4", "4 starts")):
            pr = R[k][fam]
            if "start_stats" in pr:
                s = pr["start_stats"]
                L.append(f"| profile {fam} ({lab}) | {fam}3@s | {s['n_starts']} | {s['seconds_mean']:.3f} | {s['seconds_median']:.3f} | "
                         f"{s['seconds_max']:.3f} | {s['nit_mean']:.0f} | {s['converged']}/{s['n_starts']} | {s['retries']} | {s['unavailable']} |")
    s = R["c0_pair"]["start_stats"]
    L.append(f"| c0 pair (G2 + G3+) | — | {s['n_starts']} | {s['seconds_mean']:.3f} | {s['seconds_median']:.3f} | {s['seconds_max']:.3f} | "
             f"{s['nit_mean']:.0f} | {s['converged']}/{s['n_starts']} | {s['retries']} | {s['unavailable']} |")
    s = R["generator"]["start_stats"]
    L.append(f"| generator (whole epoch) | — | {s['n_starts']} | {s['seconds_mean']:.3f} | {s['seconds_median']:.3f} | {s['seconds_max']:.3f} | "
             f"{s['nit_mean']:.0f} | {s['converged']}/{s['n_starts']} | {s['retries']} | {s['unavailable']} |")
    L.append("")
    cv = R["cv_sequential"]
    L.append(f"CV batch: {cv['n_starts']} starts in {cv['wall_s']:.1f} s = {cv['starts_per_s']:.2f} starts/s sequential. "
             f"Compile (first call) per model: " + ", ".join(f"{n} {c['value_grad_compile_s']:.2f} s" for n, c in R["compile"].items()) + ".")
    inh = R["inherited"]
    L.append(f"Inherited pipeline: 795 Nelder–Mead runs in {inh['nm_wall_s']:.1f} s ({inh['nm_s_per_run']*1000:.1f} ms/run); "
             f"spm_BMS {inh['bms_s_per_call']:.2f} s/call at {inh['nsamp']:,} draws.")
    for fam in ("G", "B"):
        pr = R["profile2"][fam]
        if "profile" in pr:
            P = pr["profile"]
            L.append(f"Profile {fam} (W2 synthetic, 2 starts): {P['status']} [{P['lo']}, {P['hi']}] ms, {pr['n_constrained_fits']} "
                     f"constrained fits in {pr['wall_s']:.1f} s; unrestricted s_tau {pr['unrestricted']['s_tau_ms']:.1f} ms ({pr['unrestricted']['selection']}).")
    L.append(f"c0 pair q(0) on one (0, fitted) dataset: {R['c0_pair']['q0']}.")
    L.append("")
    par = R.get("parallel")
    if par:
        L.append(f"## Concurrency: {par['workers']} workers, {par['n_tasks']} fits / {par['n_starts']} starts in {par['wall_s']:.1f} s "
                 f"= {par['starts_per_s']:.2f} starts/s (efficiency {R['cost']['parallel_efficiency']:.2f} of {par['workers']}× sequential)")
        L.append("")
    c = R["cost"]
    L.append("## Cost of the §8 manifest from measured rates (this machine)")
    L.append("")
    L.append("| category | measured s/start | core-hours |")
    L.append("|---|---|---|")
    ps = c["per_start_seconds"]
    L.append(f"| S4a (ε, pilots, certification, c0) | dec {ps['decision_mix']:.3f}, ε {ps['epsilon_mix']:.3f}, c0 {ps['c0_pair']:.3f} | {c['core_hours']['S4a']:.1f} |")
    L.append(f"| S4a re-certification contingency | {ps['decision_mix']:.3f} | {c['core_hours']['S4a_recertification_contingency']:.1f} |")
    L.append(f"| S4b fits (decision, recovery, 2-start profiles) | dec {ps['decision_mix']:.3f}, rec {ps['recovery_full_data']:.3f}, prof {ps['profile_2start']:.3f} | {c['core_hours']['S4b_fits']:.1f} |")
    L.append(f"| S4b 4-start profiles extra | {ps['profile_4start']:.3f} | {c['core_hours']['S4b_profiles_4start_extra']:.1f} |")
    L.append(f"| S4b inherited pipeline (15.1 M NM runs + 50,350 BMS) | {ps['inherited_nm_run']*1000:.1f} ms/run, {ps['bms_call']:.2f} s/call | {c['core_hours']['S4b_inherited']:.1f} |")
    L.append(f"| **S4 total** | | **{c['S4_core_hours_base']:.0f} base, {c['S4_core_hours_worst']:.0f} worst** |")
    L.append(f"| S2 development | | {c['S2_core_hours']:.1f} |")
    L.append(f"| real data (CV, generators, full, profiles, sensitivities) | | {c['real_core_hours']:.1f} |")
    L.append("")
    L.append(f"Design assumption was {c['design_assumption_s_per_start']:.0f} s/start → {c['design_core_hours_quoted']} core-h for S4.")
    if c["mac_wall_days"]:
        w = c["mac_wall_days"]
        L.append(f"Wall time on this machine at the measured {par['workers']}-way throughput: S4 base {w['S4_base']*24:.1f} h "
                 f"({w['S4_worst']*24:.1f} h worst), S2 {w['S2']*24:.1f} h, real data {w['real']*24:.1f} h.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", type=int, default=10)
    ap.add_argument("--session", default="active")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--skip-parallel", action="store_true")
    ap.add_argument("--write-generators", action="store_true",
                    help="replace the stored results/generators/S<subject>_* files with this run's generator fits")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "bench"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    gen_dir = os.path.join(HERE, "results", "generators")
    os.makedirs(gen_dir, exist_ok=True)
    utc = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    R = dict(utc=utc, subject=a.subject, session=a.session, machine=_machine(), manifest=MANIFEST)
    T0 = _time.time()

    print(f"[bench] S{a.subject}: generator fits (real data, whole epoch)", flush=True)
    p = D.load_participant(a.subject, a.session)
    t0 = _time.time()
    gens = F.generator_fits(p, F.FitCache(em=False))          # §7.1: Ledoit-Wolf Σ, never the EM Σ (S2 finding D5)
    g_wall = _time.time() - t0
    fits = gens["fits"]
    summary = {n: F.summarize_fit(F.selected_spec(n, fits[n], "whole"), fits[n]) if fits[n].available
               else dict(status="UNAVAILABLE") for n in ("G3", "B3", "B0")}
    for n in ("G3", "B3", "B0"):
        path = os.path.join(gen_dir, f"S{a.subject}_{a.session}_{n}.npz")
        if gens[n] is not None and (a.write_generators or not os.path.exists(path)):
            # the stored generator configurations are the S1 record that every S2/S4 batch draws from; a benchmark
            # never replaces them unless told to (24 Oct 2026 the benchmark silently overwrote S10's with a
            # degenerate fit while the development chain was about to draw from it)
            gens[n].to_npz(path)
    cand_fits = [fits[n] for n in ("G2", "G3+", "B2", "B3+", "B0")]
    R["generator"] = dict(wall_s=g_wall, n_starts=sum(len(r.starts) for r in cand_fits), start_stats=_start_stats(cand_fits),
                          summary=summary, strength={n: (gens[n].strength if gens[n] else None) for n in ("G3", "B3", "B0")},
                          level_counts=p.level_counts().tolist(), n_trials=p.n, data_id=p.data_id)
    print(f"[bench]   {R['generator']['n_starts']} starts in {g_wall:.1f} s; " +
          "; ".join(f"{n}: s_tau {summary[n].get('s_tau_ms', float('nan')):.1f} s_g {summary[n].get('s_g', float('nan')):.2f}"
                    for n in ("G3", "B3")), flush=True)
    if gens["G3"] is None or gens["B3"] is None:
        raise SystemExit("generator fit UNAVAILABLE; benchmark stops (non-numerical failure)")

    print("[bench] synthetic participants W2 (fitted G3) and T1 (fitted B3)", flush=True)
    seed_w2 = S.seed_for("development", "bench-W2", 0, 0)
    seed_t1 = S.seed_for("development", "bench-T1", 0, 0)
    W2 = S.generate(gens["G3"], p.levels, p.blocks, seed_w2, "W").participant(900)
    T1 = S.generate(gens["B3"], p.levels, p.blocks, seed_t1, "W").participant(902)
    R["synthetic"] = dict(W2=dict(seed=seed_w2, n=W2.n, data_id=W2.data_id), T1=dict(seed=seed_t1, n=T1.n, data_id=T1.data_id))

    train0, _, _, _ = D.fold_datasets(W2, D.span("primary"), 0)
    R["compile"] = compile_times(train0)
    print("[bench] compile: " + ", ".join(f"{n} {c['value_grad_compile_s']:.2f}s" for n, c in R["compile"].items()), flush=True)

    print("[bench] CV batch on W2: 5 folds x 8 candidates x 4 starts, sequential", flush=True)
    R["cv_sequential"] = cv_batch_sequential(W2)
    cv = R["cv_sequential"]
    print(f"[bench]   {cv['n_starts']} starts in {cv['wall_s']:.1f} s ({cv['starts_per_s']:.2f} starts/s); " +
          ", ".join(f"{n} {s['seconds_mean']:.2f}s" for n, s in cv["per_spec"].items()), flush=True)

    print("[bench] full-data fits W2 and T1 (8 candidates each)", flush=True)
    dsW, cacheW, resW, R["full_W2"] = full_data_fits(W2)
    dsT, cacheT, resT, R["full_T1"] = full_data_fits(T1)
    print(f"[bench]   W2 {R['full_W2']['wall_s']:.1f} s, T1 {R['full_T1']['wall_s']:.1f} s", flush=True)

    print("[bench] profiles on W2: G and B, 2 starts then 4 starts", flush=True)
    R["profile2"] = {fam: profile_timing(fam, dsW, cacheW, resW, n_starts=2) for fam in ("G", "B")}
    R["profile4"] = {fam: profile_timing(fam, dsW, cacheW, resW, n_starts=4) for fam in ("G", "B")}
    for fam in ("G", "B"):
        pr = R["profile2"][fam]
        if "profile" in pr:
            print(f"[bench]   {fam}: {pr['profile']['status']} [{pr['profile']['lo']}, {pr['profile']['hi']}] in {pr['wall_s']:.1f} s "
                  f"({pr['n_constrained_fits']} fits); 4-start {R['profile4'][fam].get('wall_s', float('nan')):.1f} s", flush=True)

    print("[bench] c0 pair", flush=True)
    R["c0_pair"] = c0_pair(gens["G3"], p, S.seed_for("development", "bench-c0", 0, 0))
    print(f"[bench]   q0 = {R['c0_pair']['q0']} in {R['c0_pair']['wall_s']:.1f} s", flush=True)

    print("[bench] inherited pipeline on W2 (795 NM runs) + 53 BMS calls", flush=True)
    R["inherited"] = inherited_timing(W2)
    print(f"[bench]   NM {R['inherited']['nm_wall_s']:.1f} s, BMS {R['inherited']['bms_wall_s']:.1f} s", flush=True)

    R["parallel"] = None
    if not a.skip_parallel:
        print(f"[bench] parallel throughput: {a.workers} workers over 40 (fold, candidate) fits on W2", flush=True)
        R["parallel"] = parallel_throughput(W2, a.workers)
        print(f"[bench]   {R['parallel']['n_starts']} starts in {R['parallel']['wall_s']:.1f} s = {R['parallel']['starts_per_s']:.2f} starts/s", flush=True)

    R["cost"] = cost_projection(cv, R["full_W2"], R["profile2"]["G"], R["profile4"]["G"], R["generator"]["start_stats"],
                                R["c0_pair"], R["inherited"], R["parallel"])
    R["total_wall_s"] = _time.time() - T0
    base = os.path.join(a.out, f"bench_{utc}")
    with open(base + ".json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: float(o) if isinstance(o, (np.floating,)) else str(o))
    md = to_markdown(R)
    with open(base + ".md", "w") as f:
        f.write(md)
    print(md)
    print(f"[bench] written {base}.json/.md in {R['total_wall_s']/60:.1f} min")


if __name__ == "__main__":
    main()
