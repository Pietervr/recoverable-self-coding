#!/usr/bin/env python3
"""jitter/generators.py — the S1 GENERATOR fits of DESIGN_jitter.md rev 6 §7.1 for all participants: G3, B3 and
B0 on full data, whole-epoch span and support, μ0 and the 53 × 53 Ledoit–Wolf Σ from all catch trials. Writes
results/generators/S{n}_{session}_{G3,B3,B0}.npz (GeneratorConfig) and results/generators/summary_{session}.{csv,md}
with the parameter values (inspection of generator parameters is permitted at S1; no cross-validated contrast is
computed on real data here).

    ../../t1_access/.venv/bin/python generators.py --subjects 1-20 --workers 10
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
import fit as F  # noqa: E402
import models as M  # noqa: E402

GEN_DIR = os.path.join(HERE, "results", "generators")


def parse_subjects(s: str) -> list:
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def fit_one(subject: int, session: str) -> dict:
    os.environ.setdefault("NPROC", "1")
    t0 = _time.time()
    p = D.load_participant(subject, session)
    out = F.generator_fits(p, F.FitCache())
    row = dict(subject=subject, session=session, n_trials=p.n, level_counts=p.level_counts().tolist(),
               data_id=p.data_id, seconds=_time.time() - t0, code_hash=M.code_hash())
    for name in ("G3", "B3", "B0"):
        cfg = out[name]
        r = out["fits"][name]
        if cfg is None:
            row[name] = dict(status="UNAVAILABLE", flags=r.flags)
            continue
        cfg.to_npz(os.path.join(GEN_DIR, f"S{subject}_{session}_{name}.npz"))
        sp = F.selected_spec(name, r, "whole")
        s = F.summarize_fit(sp, r)
        s.update(strength=cfg.strength, starts_converged=r.n_converged, candidates=r.candidates)
        row[name] = s
    return row


def write_summary(rows: list, session: str):
    rows = sorted(rows, key=lambda r: r["subject"])
    with open(os.path.join(GEN_DIR, f"summary_{session}.json"), "w") as f:
        json.dump(rows, f, indent=1)
    L = [f"# S1 generator fits — {session} session — {len(rows)} participants (code {rows[0]['code_hash']})", "",
         "Whole-epoch full-data fits (§7.1). s_tau in ms (parent SD), realised SD beside it; a(1..5) in decoder units "
         "(span mean at zero shift); strength = a(5) × mean T̃ over the primary windows. 'sel' = REDUCED/POSITIVE of "
         "the zero-boundary construction; flags per §5.", "",
         "| S | n | G3 sel | G3 s_tau (real.) | G3 s_g | G3 a(5) | G3 str | B3 sel | B3 s_tau (real.) | B3 s_g | "
         "B3 a(5) | B3 A(1..5) | B3 str | B0 a(5) | B0 A(1..5) | conv G3/B3/B0 | flags | s |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        g, b, b0 = r["G3"], r["B3"], r["B0"]

        def st(x, key, fmt="{:.2f}"):
            return fmt.format(x[key]) if x.get("status") == "AVAILABLE" else "—"

        def A(x):
            return ", ".join(f"{v:.2f}" for v in x["A"]) if x.get("status") == "AVAILABLE" else "—"

        def tau(x):
            if x.get("status") != "AVAILABLE":
                return "—"
            return f"{x['s_tau_ms']:.1f} ({x.get('realised_sd_ms', 0.0):.1f})" if x["s_tau_ms"] > 0 else "0"
        flags = "; ".join(f"{k}:{','.join(x.get('flags', []))}" for k, x in (("G3", g), ("B3", b), ("B0", b0)) if x.get("flags"))
        L.append(f"| {r['subject']} | {r['n_trials']} | {g.get('selection', '—')} | {tau(g)} | {st(g, 's_g')} | "
                 f"{st(g, 'a', '{}') if False else (f'{g[chr(97)][-1]:.2f}' if g.get('status') == 'AVAILABLE' else '—')} | "
                 f"{st(g, 'strength', '{:.3f}')} | {b.get('selection', '—')} | {tau(b)} | {st(b, 's_g')} | "
                 f"{(f'{b[chr(97)][-1]:.2f}' if b.get('status') == 'AVAILABLE' else '—')} | {A(b)} | {st(b, 'strength', '{:.3f}')} | "
                 f"{(f'{b0[chr(97)][-1]:.2f}' if b0.get('status') == 'AVAILABLE' else '—')} | {A(b0)} | "
                 f"{g.get('starts_converged', 0)}/{b.get('starts_converged', 0)}/{b0.get('starts_converged', 0)} | {flags} | {r['seconds']:.0f} |")
    L.append("")
    av = [r for r in rows if r["G3"].get("status") == "AVAILABLE"]
    if av:
        taus = np.array([r["G3"]["s_tau_ms"] for r in av])
        sgs = np.array([r["G3"]["s_g"] for r in av])
        L.append(f"G3 across participants: s_tau median {np.median(taus):.1f} ms (min {taus.min():.1f}, max {taus.max():.1f}), "
                 f"{int(np.sum(taus == 0))} REDUCED; s_g median {np.median(sgs):.2f}.")
    av = [r for r in rows if r["B3"].get("status") == "AVAILABLE"]
    if av:
        taus = np.array([r["B3"]["s_tau_ms"] for r in av])
        L.append(f"B3 across participants: s_tau median {np.median(taus):.1f} ms (min {taus.min():.1f}, max {taus.max():.1f}), "
                 f"{int(np.sum(taus == 0))} REDUCED.")
    with open(os.path.join(GEN_DIR, f"summary_{session}.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", default="1-20")
    ap.add_argument("--session", default="active")
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    os.makedirs(GEN_DIR, exist_ok=True)
    subs = parse_subjects(a.subjects)
    t0 = _time.time()
    if a.workers > 1:
        from joblib import Parallel, delayed
        rows = Parallel(n_jobs=a.workers, backend="loky")(delayed(fit_one)(s, a.session) for s in subs)
    else:
        rows = [fit_one(s, a.session) for s in subs]
    print(write_summary(rows, a.session))
    print(f"[generators] {len(rows)} participants in {(_time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
