#!/usr/bin/env python3
"""jitter/s5.py — stage S5 of DESIGN_jitter.md rev 7 (§0, §6, §7.5, §9): the real-data cross-validated fits, the real
full-data fits with the s_τ profile hull of each family, and the final decision. Written 24 Oct 2026 (R052) on the
s4.py pattern; one small JSON per participant, skipped when it exists.

Stage discipline (§0): nothing here touches real data until results/s4/summary.json exists AND its manifest is
complete (`s4.py evaluate`; Codex S3 review finding 11). `smoke` runs the same code path on ONE synthetic development
participant into results/s5_smoke and never reads real data.

    s5.py cv --workers N      20 participants × primary span × 5 block folds × (G0, G2, G3, B0, B2, B3): Σ by maximum
                              likelihood inside each model, held-out log density under the model's own Σ, nat per
                              scored trial -> results/s5/cv/S<s>.json
    s5.py full --workers N    full-data fits of the eight models (§7.5: the real reported estimates) + the s_τ profile
                              hull of G3 and B3 with c₀ from results/s4/s4a.json -> results/s5/full/S<s>.json
    s5.py decide              decide.decide(...) with the S4 licence inputs, JITTER DETECTED per family, the §9 claim
                              keys and the paper's branch -> results/s5/decision.{json,md}
    s5.py all --workers N     cv, full, decide
    s5.py smoke --workers N   the three steps on one synthetic W2 development participant (results/s5_smoke)
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
sys.path.insert(0, os.path.dirname(HERE))
import data as D  # noqa: E402
import decide as X  # noqa: E402
import fit as F  # noqa: E402
import models as M  # noqa: E402
import s4  # noqa: E402

S5_DIR = os.path.join(HERE, "results", "s5")
CV_MODELS = ("G0", "G2", "G3", "B0", "B2", "B3")       # the six of §6 (R6 roster); G3/B3 carry their G2/B2, G3+/B3+ candidates
SUBJECTS = list(range(1, 21))


# ----------------------------------------------------------------------------------------------
# the S4 gate: nothing real before the manifest is complete
# ----------------------------------------------------------------------------------------------
def load_s4_summary() -> dict:
    p = os.path.join(s4.S4_DIR, "summary.json")
    if not os.path.exists(p):
        sys.exit("S5 refused: results/s4/summary.json is missing — the S4 gates are read first (DESIGN rev 7 §0)")
    with open(p) as f:
        summ = json.load(f)
    man = summ.get("manifest", {})
    if not man.get("complete"):
        sys.exit(f"S5 refused: the S4 manifest is incomplete ({man.get('pending')}); no licence may be read "
                 f"(DESIGN rev 7 §0; Codex S3 review finding 11)")
    if "licence_inputs" not in summ:
        sys.exit("S5 refused: results/s4/summary.json carries no licence_inputs (rerun s4.py evaluate)")
    return summ


def ensure_run_record(label: str) -> dict:
    """S5 fits under the S4 numerical contract (Codex S3 re-review finding 6: S4 and S5 fitting on the same host type with the
    same pins). results/s4/run_config.json must exist and this process's fingerprint — trial chunk, node counts, scale rule,
    profile starts, rescue rounds, software versions, machine, CPU model, fitter code hash, generator assets — must equal it;
    otherwise S5 refuses with every difference named. The S5 record is written beside the results (results/s5/run_config.json;
    a resumed S5 is checked against it too). The runner hash may differ from S4's (it is recorded, not required)."""
    s4_path = os.path.join(s4.S4_DIR, F.RUN_CONFIG_NAME)
    if not os.path.exists(s4_path):
        raise F.RunConfigMismatch(f"{label} refused: {s4_path} is missing — S5 runs only under the recorded S4 contract")
    with open(s4_path) as f:
        rec4 = json.load(f)
    s4.load_bases()
    cur = F.run_record(s4.GEN_DIR)
    if cur["fingerprint"] != rec4.get("fingerprint"):
        diffs = F.config_differences(rec4, cur) or [f"fingerprint: S4 {rec4.get('fingerprint')}, this process {cur['fingerprint']}"]
        raise F.RunConfigMismatch(f"{label} refused: this process does not match the S4 run record {s4_path} "
                                  f"(written {rec4.get('utc')} on {rec4.get('host')}):\n  - " + "\n  - ".join(diffs) +
                                  "\nRun S5 on the S4 host type with the S4 bundle and environment (e.g. export JITTER_TRIAL_CHUNK=64).")
    rec = F.ensure_run_record(S5_DIR, s4.GEN_DIR, label, check_runner=True)
    rec = dict(rec, s4_fingerprint=rec4.get("fingerprint"), s4_runner_hash=rec4.get("runner_hash"))
    print(f"[s5] run record matches S4 ({cur['fingerprint']}); runner hash {cur['runner_hash']} (S4 {rec4.get('runner_hash')})", flush=True)
    return rec


def _failures_from_json(fits_per_fold: list) -> dict:
    nf, rescued, nest = [], [], []
    for fold, fits in enumerate(fits_per_fold):
        for name, d in fits.items():
            if d.get("numerical_failure"):
                nf.append(f"f{fold}_{name}")
            if (d.get("rescue") or {}).get("resolved"):
                rescued.append(f"f{fold}_{name}")
            if (d.get("nesting") or {}).get("failure"):
                nest.append(f"f{fold}_{name}<{d['nesting'].get('vs')}")
    return dict(numerical_failures=nf, rescued=rescued, nesting_failures=nest)


def load_c0() -> dict:
    with open(os.path.join(s4.S4_DIR, "s4a.json")) as f:
        return json.load(f)["c0"]


# ----------------------------------------------------------------------------------------------
# tasks
# ----------------------------------------------------------------------------------------------
def cv_task(p: D.Participant, out_path: str) -> dict:
    """One participant's cross-validated scores (§5 score: held-out log density summed over the five folds, divided
    by the scored trials; §4 Σ by maximum likelihood inside each model)."""
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    res = F.cv_scores(p, "primary", F.FitCache(), CV_MODELS)
    rec = dict(participant=res.participant, subject=int(p.subject), session=p.session, tag=p.tag, span="primary",
               data_id=p.data_id, n_trials=int(p.n), n_scored=res.n_scored, scores=res.scores, fold_sums=res.fold_sums,
               fold_mean=res.fold_mean, available=res.available, fits=res.fits, seconds=_time.time() - t0,
               code_hash=M.code_hash(), run_fingerprint=s4.run_fingerprint(), **_failures_from_json(res.fits))
    s4._write(out_path, rec)
    return rec


def full_task(p: D.Participant, c0: dict, out_path: str) -> dict:
    """One participant's full-data fits of the eight models on the primary span and the s_τ profile hull of each
    family's full model (§7.5; raw estimates, never corrected by the simulation bias)."""
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    ds = D.full_dataset(p, D.span("primary"))
    cache = F.FitCache()
    res = F.finalized(F.fit_all_models(ds, cache, "primary", F.FULL_MODELS))
    fits = {name: s4._fit_summary(fr, F.selected_spec(name, fr, "primary") if F.usable(fr) else None) for name, fr in res.items()}
    fam = {}
    fails = [s4.failure_record(res)]
    for family in ("G", "B"):
        full = res[family + "3"]
        prof, points = None, None
        if F.usable(full) and c0.get(family) is not None:
            ev, plog = F.profile_evaluator(family, ds, full, "primary", cache, n_starts=F.PROFILE_STARTS)
            prof = X.hull_search(ev, full.loglik, c0[family]).as_dict()
            points = {f"{s_ms:g}": dict(status=v.status, loglik=(v.loglik if F.usable(v) else None),
                                        numerical_failure=bool(v.numerical_failure), unavailable_reason=v.unavailable_reason,
                                        rescued=bool((v.rescue or {}).get("resolved")), n_starts=len(v.starts), quad=v.quad)
                      for s_ms, v in plog.items()}
            fails.append(s4.failure_record({f"{s_ms:g}": v for s_ms, v in plog.items() if s_ms > 0.0}, f"prof{family}@"))
        fam[family] = dict(profile=prof, profile_points=points, profile_starts=F.PROFILE_STARTS,
                           s_tau_hat=fits[family + "3"].get("s_tau_ms"), s_g_hat=fits[family + "3"].get("s_g"),
                           selection=fits[family + "3"].get("selection"), bounds_hit=(full.bounds_hit if F.usable(full) else None))
    rec = dict(subject=int(p.subject), session=p.session, tag=p.tag, span="primary", data_id=p.data_id, n_trials=int(p.n),
               fits=fits, families=fam, c0=c0, seconds=_time.time() - t0, code_hash=M.code_hash(),
               run_fingerprint=s4.run_fingerprint(), **s4._merge_failures(fails))
    s4._write(out_path, rec)
    return rec


def _run(tasks: list, workers: int, label: str):
    from joblib import Parallel, delayed
    print(f"[s5] {label}: {len(tasks)} tasks on {workers} workers, start {_time.strftime('%H:%M:%SZ', _time.gmtime())}", flush=True)
    t0 = _time.time()
    if tasks:
        Parallel(n_jobs=min(workers, len(tasks)), backend="loky", verbose=0)(delayed(fn)(*args) for fn, args in tasks)
    print(f"[s5] {label}: done in {_time.time() - t0:.0f} s", flush=True)


def run_cv(out_dir: str, participants: list, workers: int):
    tasks = [(cv_task, (p, os.path.join(out_dir, "cv", f"S{p.subject}.json"))) for p in participants
             if not os.path.exists(os.path.join(out_dir, "cv", f"S{p.subject}.json"))]
    _run(tasks, workers, "S5 cv")


def run_full(out_dir: str, participants: list, c0: dict, workers: int):
    tasks = [(full_task, (p, c0, os.path.join(out_dir, "full", f"S{p.subject}.json"))) for p in participants
             if not os.path.exists(os.path.join(out_dir, "full", f"S{p.subject}.json"))]
    _run(tasks, workers, "S5 full + profiles")


# ----------------------------------------------------------------------------------------------
# the decision
# ----------------------------------------------------------------------------------------------
def _profile(d: dict | None):
    if d is None:
        return None
    return X.Profile(status=d["status"], reason=d["reason"], lo=d["lo"], hi=d["hi"], accepted=d["accepted"],
                     rejected=d["rejected"], q={float(k): v for k, v in d["q"].items()},
                     ell={float(k): v for k, v in d["ell"].items()}, ref=d["ref"],
                     flagged_unrestricted=d["flagged_unrestricted"], disconnected=d["disconnected"],
                     n_constrained=d["n_constrained"], midpoints=d["midpoints"])


def _iv(iv: dict) -> str:
    if not np.isfinite(iv.get("mean", np.nan)):
        return f"{iv['sign']} (n {iv['n']})"
    return f"{iv['mean']:+.5f} [{iv['lo']:+.5f}, {iv['hi']:+.5f}] n {iv['n']} {iv['sign']}"


def branch(cl: dict) -> str:
    """The paper's outcome paragraph (sections/jitter_discussion.tex BRANCH A/B/C) that the §9 keys license."""
    if cl["not_licensed"]:
        return "C: NOT LICENSED — descriptive summaries only; name the failed gate with its count"
    if cl["primary_positive"]:
        return "A: the advantage is retained" + ("" if cl.get("recovery_full_and_detected") else
                                                 " (recovery not ADEQUATE or jitter not detected in G: robustness to a latency term the data did not pin down)")
    parts = ["B: the advantage is not retained"]
    if cl["not_robust"]:
        parts.append("part of the inherited advantage is removed by representing trial variability (premise met)")
    if cl["latency_most"]:
        parts.append("latency carries most of that removal")
    elif cl["latency_part"]:
        parts.append("latency variation carries part of that removal")
    elif cl["latency_reduced_delta2_only"]:
        parts.append("adding latency after scale reduced the scale-only contrast (no attenuation premise)")
    if cl["scale_part"]:
        parts.append("scale variation carries part of the removal")
    if cl["framing_result"]:
        parts.append("framing result: the joint framing favours the graded family")
    if cl["unresolved_no_bound"]:
        parts.append("UNRESOLVED without a bound: not evidence of absence, not a survival")
    if len(parts) == 1:
        parts.append("removal attributed to trial variability of unidentified form")
    return "; ".join(parts)


def decide_stage(out_dir: str, summ: dict, subjects: list) -> dict:
    scores, cv = {}, {}
    for s in subjects:
        p = os.path.join(out_dir, "cv", f"S{s}.json")
        if os.path.exists(p):
            with open(p) as f:
                r = json.load(f)
            cv[f"S{s}"] = r
            scores[f"S{s}"] = {m: r["scores"].get(m, float("nan")) for m in CV_MODELS}
    li = summ["licence_inputs"]
    dec = X.decide(scores, epsilon=li["epsilon"], epsilon_available=bool(li["epsilon_available"]),
                   lambda_e1_certified=bool(li["lambda_e1_certified"]), gate_e_met=bool(li["gate_e_met"]),
                   gates_bc_met=bool(li["gates_bc_met"]), v2_sim_met=bool(li["v2_sim_met"]), n_participants=len(subjects))
    profiles, full = {"G": {}, "B": {}}, {}
    for s in subjects:
        p = os.path.join(out_dir, "full", f"S{s}.json")
        if os.path.exists(p):
            with open(p) as f:
                r = json.load(f)
            full[f"S{s}"] = r
            for fam in ("G", "B"):
                profiles[fam][f"S{s}"] = _profile(r["families"][fam]["profile"])
    detected = {fam: X.jitter_detected(profiles[fam], dec.attribution[f"{fam}3-{fam}2"]) for fam in ("G", "B")}
    recovery = {fam: li.get(f"recovery_{fam}", "INCOMPLETE") for fam in ("G", "B")}
    rise = summ.get("rise", {}) or {}
    rise_W3 = bool((rise.get("W3") or {}).get("rise", False))
    rise_W4 = bool((rise.get("W4") or {}).get("rise", False))
    cl = X.claims(dec, recovery["G"], detected["G"]["detected"], rise_W3, rise_W4)
    cl["recovery_full_and_detected"] = recovery["G"] == "ADEQUATE" and detected["G"]["detected"]
    zero_only = X.zero_only_participants(profiles["G"]) if recovery["G"] == "ADEQUATE-ZERO-ONLY" else []
    per = {}
    for k in sorted(set(scores) | set(full), key=lambda x: int(x[1:])):
        row = dict(scores=scores.get(k))
        if k in full:
            for fam in ("G", "B"):
                fr = full[k]["families"][fam]
                pr = fr["profile"]
                row[fam] = dict(s_tau_hat=fr["s_tau_hat"], s_g_hat=fr["s_g_hat"], selection=fr["selection"],
                                hull=None if pr is None else [pr["status"], pr["lo"], pr["hi"]])
            row["B3_occupancy"] = full[k]["fits"]["B3"].get("A")
        per[k] = row
    out = dict(decision=dec.as_dict(), claims=cl, branch=branch(cl), jitter_detected=detected, recovery_flags=recovery,
               rise=dict(W3=rise_W3, W4=rise_W4), zero_only_participants_G=zero_only, per_participant=per,
               n_cv=len(scores), n_full=len(full), s4_summary_utc=summ.get("utc"), s4_licence_inputs=li,
               code_hash=M.code_hash(), utc=_time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime()))
    s4._write(os.path.join(out_dir, "decision.json"), out)
    with open(os.path.join(out_dir, "decision.md"), "w") as f:
        f.write(decision_markdown(out))
    return out


def decision_markdown(out: dict) -> str:
    d = out["decision"]
    L = ["# S5 — the real-data decision (DESIGN rev 7 §6, §9)", "",
         f"code {out['code_hash']}, {out['utc']}; S4 summary {out['s4_summary_utc']}; {out['n_cv']} participants scored, {out['n_full']} with full fits", "",
         f"PRIMARY LICENCE: {'LICENSED' if d['licence_primary'] else 'NOT LICENSED: ' + '; '.join(d['licence_reasons'])}",
         f"primary Δ₃ = S_B3 − S_G3 (nat/trial): {_iv(d['primary'])}; roster {len(d['primary_roster'])}",
         f"R6 ({len(d['R6'])}): Δ₀ {_iv(d['delta0_R6'])}; Δ₂ {_iv(d['delta2_R6'])}; Δ₃ {_iv(d['delta3_R6'])}",
         f"D = Δ₀ − Δ₃ {_iv(d['D'])}; D_scale {_iv(d['D_scale'])}; D_τ {_iv(d['D_tau'])}; D_τ − D_scale {_iv(d['D_tau_minus_D_scale'])}",
         f"upper bound: {d['upper_bound']} (ε {d['epsilon']}); bridge (iii) {_iv(d['bridge_iii'])}; bridge (iv) {_iv(d['bridge_iv'])}; attenuation premise {d['premise']}",
         "attribution: " + "; ".join(f"{k} {_iv(v)}" for k, v in d["attribution"].items()),
         f"recovery flags: G {out['recovery_flags']['G']}, B {out['recovery_flags']['B']}; rise W3 {out['rise']['W3']}, W4 {out['rise']['W4']}",
         "jitter detected: " + "; ".join(f"{fam} {v['detected']} ({v['n_exceeding']} hulls above 20 ms, group {v['group_sign']})" for fam, v in out["jitter_detected"].items()),
         f"zero-only participants (G): {out['zero_only_participants_G']}",
         "claims licensed: " + ", ".join(k for k, v in out["claims"].items() if v) or "claims licensed: none",
         f"paper branch: {out['branch']}", "",
         "| participant | Δ₀ | Δ₂ | Δ₃ | G3 ŝ_τ (hull) sel | B3 ŝ_τ (hull) sel | B3 A(1..5) |", "|---|---|---|---|---|---|---|"]
    for k, row in out["per_participant"].items():
        sc = row.get("scores") or {}

        def dd(j):
            a, b = sc.get(f"B{j}", np.nan), sc.get(f"G{j}", np.nan)
            return f"{a - b:+.4f}" if np.isfinite(a) and np.isfinite(b) else "n/a"

        def fam(f):
            r = row.get(f)
            if not r:
                return "—"
            h = r["hull"]
            hs = "no profile" if h is None else f"{h[0]} [{h[1]}, {h[2]}]"
            return f"{r['s_tau_hat']} ({hs}) {r['selection']}"

        occ = row.get("B3_occupancy")
        L.append(f"| {k} | {dd(0)} | {dd(2)} | {dd(3)} | {fam('G')} | {fam('B')} | {occ if occ is None else [round(v, 2) for v in occ]} |")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("cv", "full", "all", "smoke"):
        sp = sub.add_parser(name)
        sp.add_argument("--workers", type=int, default=12)
    sub.add_parser("decide")
    a = ap.parse_args()
    if a.cmd == "smoke":
        out_dir = os.path.join(HERE, "results", "s5_smoke")
        bases = s4.load_bases()
        base = s4.set_members("development", "W2", 0)[0]
        p = s4.make_synthetic("development", "W2", 0, 0, base, bases)         # one synthetic graded participant, never real data
        t0 = _time.time()
        run_cv(out_dir, [p], a.workers)
        run_full(out_dir, [p], {"G": 3.84, "B": 3.84}, a.workers)
        fake = dict(utc="smoke", rise={}, licence_inputs=dict(epsilon=None, epsilon_available=False, lambda_e1_certified=False,
                                                              gate_e_met=False, gates_bc_met=False, v2_sim_met=False,
                                                              recovery_G="INCOMPLETE", recovery_B="INCOMPLETE"))
        out = decide_stage(out_dir, fake, [p.subject])
        print(decision_markdown(out))
        print(f"[s5] smoke done in {_time.time() - t0:.0f} s (the decision above is on ONE synthetic participant: roster 1, everything UNAVAILABLE by design)")
        return
    summ = load_s4_summary()
    participants = None
    if a.cmd in ("cv", "full", "all"):
        ensure_run_record(f"S5 {a.cmd}")
        participants = [D.load_participant(s) for s in SUBJECTS]
    if a.cmd in ("cv", "all"):
        run_cv(S5_DIR, participants, a.workers)
    if a.cmd in ("full", "all"):
        run_full(S5_DIR, participants, load_c0(), a.workers)
    if a.cmd in ("decide", "all"):
        out = decide_stage(S5_DIR, summ, SUBJECTS)
        print(decision_markdown(out))


if __name__ == "__main__":
    main()
