"""group.py on constructed recording results (no fits, no EEG): runs on the physical window grid, the total decision
function in its declared order — including Codex's counterexample (35 recordings pass §2, no hard failure, AUC 0.8,
every model unavailable in every window: previously 'inconclusive', now 'insufficient availability') — an isolated
opposing window, both families running, a null run, a run broken by an ineligible window, the technical-failure and
sensitivity gates with missing AUC, the common cohort, and the bootstrap's missing-window, finite-fraction and paired rules.

Run: ../../.venv/bin/python test_group.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import group as G

NW = 10
NSAMP = 20_000


def result(subject, favour=None, auc=0.8, unavailable=(), status="ok", task="nocue"):
    """favour: {window: model index given +8 nat in every recording}; the graded and two-state models exactly tied
    elsewhere (random near-ties are not ties for BMS: 35 recordings of 0.2 nat noise can give a decisive pxp by chance)."""
    ev = np.zeros((NW, 3))
    ev[:, 1] += 3.0                                      # graded ahead of null by default
    ev[:, 2] += 3.0
    for w, m in (favour or {}).items():
        ev[w, m] += 8.0
    av = np.ones((NW, 3), dtype=bool)
    for w in unavailable:
        av[w] = False
    ev = np.where(av, ev, np.nan)
    return dict(status=status, subject=subject, task=task, windows=list(range(20, 20 + NW)), models=["null", "graded", "twostate"],
                evidence=ev, available=av, delta=np.where(av[:, 1] & av[:, 2], ev[:, 2] - ev[:, 1], np.nan) / 100.0,
                auc=np.full((NW, 2), auc))


def decide(results, n_pass=None):
    return G.decide(results, list(range(NW)), n_pass_section2=len(results) if n_pass is None else n_pass, nsamp=NSAMP)


def main():
    assert G.runs([1, 1, 0, 1, 1, 1]) and not G.runs([1, 1, 0, 1, 1]) and not G.runs([])
    outcomes = {}

    rs = [result(s, unavailable=range(NW)) for s in range(35)]
    outcomes["no eligible window, 35 pass, AUC 0.8"] = decide(rs)["outcome"]
    assert outcomes["no eligible window, 35 pass, AUC 0.8"] == "insufficient availability"

    rs = [result(s, favour={2: 2, 3: 2, 4: 2, 7: 1}) for s in range(35)]
    d = decide(rs)
    outcomes["two-state run + isolated graded window"] = d["outcome"]
    assert d["outcome"] == "two-state" and d["runs"]["twostate"] and not d["runs"]["graded"], d["runs"]
    assert len(d["common_cohort"]) == 35 and d["common_cohort_runs"]["twostate"]

    rs = [result(s, favour={1: 2, 2: 2, 3: 2, 6: 1, 7: 1, 8: 1}) for s in range(35)]
    outcomes["both families run"] = decide(rs)["outcome"]
    assert outcomes["both families run"] == "inconclusive/mixed"

    rs = [result(s, favour={4: 0, 5: 0, 6: 0}) for s in range(35)]
    d = decide(rs)
    outcomes["null run only"] = d["outcome"]
    assert d["outcome"] == "inconclusive/mixed" and d["runs"]["null"]

    rs = [result(s, favour={2: 2, 3: 2, 5: 2, 6: 2}, unavailable=(4,) if s < 20 else ()) for s in range(35)]
    d = decide(rs)
    outcomes["two-state windows around an ineligible window"] = d["outcome"]
    assert not d["windows"][4]["eligible"] and d["n_windows_eligible"] == 9
    assert d["outcome"] == "inconclusive/mixed", "a run must not bridge an ineligible window"

    rs = [result(s, favour={2: 2, 3: 2, 4: 2}, unavailable=(0, 1, 8) if s < 20 else ()) for s in range(35)]
    outcomes["7 of 10 windows eligible"] = decide(rs)["outcome"]
    assert outcomes["7 of 10 windows eligible"] == "insufficient availability"

    rs = [result(s, favour={2: 2, 3: 2, 4: 2}) for s in range(27)] + \
         [dict(status="technical failure: X", subject=100 + s, task="nocue") for s in range(9)]
    outcomes["9 technical failures of 36"] = decide(rs)["outcome"]
    assert outcomes["9 technical failures of 36"] == "two-state"          # 9 <= 36/4
    rs = rs + [dict(status="technical failure: X", subject=200, task="nocue")]
    outcomes["10 technical failures of 37"] = decide(rs)["outcome"]
    assert outcomes["10 technical failures of 37"] == "technical failure"  # 10 > 37/4

    outcomes["19 pass §2"] = decide([result(s) for s in range(19)])["outcome"]
    assert outcomes["19 pass §2"] == "technical failure"

    rs = [result(s, favour={2: 2, 3: 2, 4: 2}, auc=0.52) for s in range(35)]
    outcomes["AUC 0.52 everywhere"] = decide(rs)["outcome"]
    assert outcomes["AUC 0.52 everywhere"] == "insufficient sensitivity"
    rs = [result(s, favour={2: 2, 3: 2, 4: 2}, auc=np.nan) for s in range(35)]
    outcomes["AUC missing everywhere"] = decide(rs)["outcome"]
    assert outcomes["AUC missing everywhere"] == "insufficient sensitivity"
    rs = [result(s, favour={2: 2, 3: 2, 4: 2}, auc=(0.8 if s < 19 else np.nan)) for s in range(35)]
    outcomes["AUC finite in 19 recordings"] = decide(rs)["outcome"]
    assert outcomes["AUC finite in 19 recordings"] == "insufficient sensitivity"

    for k, v in outcomes.items():
        print(f"  {k:48s} -> {v}")

    # bootstrap
    v = np.full((30, 3), 0.01)
    b = G.bootstrap_mean(v)
    assert all(abs(x["point"] - 0.01) < 1e-12 and abs(x["lo"] - 0.01) < 1e-12 and abs(x["hi"] - 0.01) < 1e-12 for x in b)
    v = np.random.default_rng(0).normal(0.02, 0.01, (30, 3))
    v[:22, 1] = np.nan                                     # 8 participants with a finite value: below MIN_BOOT_N
    v[:5, 2] = np.nan
    b = G.bootstrap_mean(v)
    assert np.isfinite(b[0]["lo"]) and b[0]["lo"] < 0.02 < b[0]["hi"]
    assert np.isnan(b[1]["point"]) and np.isnan(b[1]["lo"])
    assert b[2]["n"] == 25 and np.isfinite(b[2]["lo"])
    res = {"nocue": [dict(status="ok", subject=s, delta=np.full(NW, 0.01)) for s in range(1, 31)],
           "informative": [dict(status="ok", subject=s, delta=np.full(NW, 0.03)) for s in range(2, 32)]}
    bt = G.bootstrap_tasks(res, [0, 1])
    assert bt["participants"] == list(range(1, 32))
    diff = bt["informative_minus_nocue"][0]
    assert diff["n"] == 29 and abs(diff["point"] - 0.02) < 1e-12
    med = G.bootstrap_median(np.random.default_rng(1).uniform(0.5, 0.9, (30, 2)), seed=G.BOOT_SEED + 1)
    assert all(m["lo"] <= m["point"] <= m["hi"] for m in med)
    print("bootstrap: constant data give a degenerate interval; windows with fewer than 10 finite values are missing; "
          "the paired difference uses the 29 participants with both tasks; median intervals bracket their points")
    print("test_group: ALL OK")


if __name__ == "__main__":
    main()
