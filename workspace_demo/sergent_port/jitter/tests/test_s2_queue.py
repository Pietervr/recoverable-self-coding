"""Plumbing test of jitter/s2.run_decision's cross-set queue (24 Oct 2026): every pending set's participant-datasets go
through ONE Parallel call, each task writes its own file first (resume unit), the per-set records are assembled with
the same fields as before (members, primary, delta3, participants, archive npz), finished sets are skipped, and a
half-finished set resumes from its task files. decision_task is replaced by a fast fake; no fit runs.
Run: ../../t1_access/.venv/bin/python tests/test_s2_queue.py"""
import json
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import s2  # noqa: E402

CALLS = []


def _fake_task(setting, r, m, base_subject, bases, span_name="primary", quad=None):
    CALLS.append((setting, r, m))
    g3, b3 = -15.0 + 0.001 * m, -15.0 + 0.001 * m - 0.002       # every participant: B3 below G3 -> NEGATIVE set
    return dict(setting=setting, r=r, m=m, base=base_subject, data_id=f"fake{r}_{m}", n_trials=900, n_scored=850,
                scores={"G3": g3, "B3": b3}, fold_sums={"G3": [g3] * 5, "B3": [b3] * 5}, folds=[], seconds=1.5,
                code_hash="fake", quad={}, _xs={"f0_G3_theta": np.zeros(3, dtype=np.float32)})


def _redirect():
    tmp = tempfile.mkdtemp()
    s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR = tmp, os.path.join(tmp, "decision"), os.path.join(tmp, "archive")
    return tmp


def test_queue_assembles_sets_skips_finished_and_resumes():
    old = (s2.decision_task, s2.PARALLEL_BACKEND, s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR)
    s2.decision_task = _fake_task
    s2.PARALLEL_BACKEND = "threading"
    tmp = _redirect()
    try:
        CALLS.clear()
        s2.run_decision("W2", 3, 4, sets=[0, 1, 2])
        assert len(CALLS) == 60 and len({(r, m) for _, r, m in CALLS}) == 60       # 3 sets × 20, each once, one queue
        for r in range(3):
            p = os.path.join(s2.DEC_DIR, "W2", f"set_{r}.json")
            assert os.path.exists(p)
            with open(p) as f:
                rec = json.load(f)
            assert rec["primary"] == "NEGATIVE" and len(rec["participants"]) == 20 and len(rec["delta3"]) == 20
            assert rec["members"] == s2.set_members("W2", r) and rec["wall_s"] == 30.0 and "queue_wall_s" in rec
            assert [row["m"] for row in rec["participants"]] == list(range(20))
            with np.load(os.path.join(s2.ARC_DIR, "W2", f"set_{r}.npz")) as z:
                assert len(z.files) == 20
        assert not os.path.exists(os.path.join(s2.DEC_DIR, "W2", "tasks")) or not os.listdir(os.path.join(s2.DEC_DIR, "W2", "tasks"))
        # finished sets are skipped; a half-finished set resumes from its task files
        CALLS.clear()
        for m in range(7):
            jp, npz = s2.task_paths("W2", 3, m)
            s2.decision_task_to_file("W2", 3, m, 10, {}, "primary", jp, npz)
        CALLS.clear()
        s2.run_decision("W2", 4, 4)
        assert sorted(CALLS) == [("W2", 3, m) for m in range(7, 20)]                 # sets 0-2 skipped, set 3 resumed
        with open(os.path.join(s2.DEC_DIR, "W2", "set_3.json")) as f:
            assert len(json.load(f)["participants"]) == 20
    finally:
        s2.decision_task, s2.PARALLEL_BACKEND, s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR = old


def _fake_run(label, quad, g_nodes=17, delta_shift=None, nan_m=None, failures=(), nest_break=None, code="h1"):
    """A repair-run record with twenty participants, five folds, the four candidates and the two selected models."""
    parts = []
    for m in range(20):
        g3 = -15.0 + 0.001 * m
        b3 = g3 - 0.002 + (delta_shift or {}).get(m, 0.0)
        if nan_m is not None and m == nan_m:
            b3 = float("nan")
        folds = []
        for fold in range(5):
            fits = {}
            for g, b in (("G2", "B2"), ("G3+", "B3+")):
                lg = -10000.0 - fold
                lb = lg + 0.5
                if nest_break == (m, fold, b):
                    lb = lg - 1.0
                fits[g] = dict(status="AVAILABLE", loglik=lg, quad=dict(n_tau_nodes=quad.get("n_tau_nodes", 31), n_g_nodes=g_nodes, adaptive_g=True))
                fits[b] = dict(status="AVAILABLE", loglik=lb, quad=dict(n_tau_nodes=quad.get("n_tau_nodes", 31), n_g_nodes=g_nodes, adaptive_g=True))
            fits["G3"] = dict(status="AVAILABLE", selection="POSITIVE")
            fits["B3"] = dict(status="AVAILABLE", selection="POSITIVE" if m % 2 else "REDUCED")
            folds.append(dict(fold=fold, fits=fits))
        parts.append(dict(m=m, scores=dict(G3=g3, B3=b3), folds=folds, numerical_failures=[], polish=dict(calls=0, accepted=0, seconds=0.0),
                          fit_seconds=100.0, seconds=120.0, data_id=f"d{m}", quad_rule=dict(per_model={})))
    d3 = {f"m{p['m']}": p["scores"]["B3"] - p["scores"]["G3"] for p in parts}
    vals = list(d3.values())
    half = 0.5 * 1.2e-3 if all(np.isfinite(v) for v in vals) else float("nan")
    return dict(setting="W2", r=0, label=label, quad=quad, rule=dict(rule="17", refit_sg=0.6, refit_nodes=33), code_hash=code,
                data_ids=[p["data_id"] for p in parts], delta3=d3, half_width=half, primary="NEGATIVE",
                numerical_failures=list(failures), participants=parts, n_available=int(sum(np.isfinite(v) for v in vals)),
                polish=dict(calls=0, accepted=0, seconds=0.0, r_extra_work=0.0), cost=dict(fit_seconds=2000.0, task_seconds=2400.0),
                interval=dict(mean=-0.002, lo=-0.0026, hi=-0.0014), workers=12, utc="x", quad_rule=dict(per_model={}))


def test_repair_compare_needs_the_whole_roster_and_no_failures():
    """The repaired node checks (25 Oct 2026, Codex finding 14): identical runs PASS with every participant compared; a
    participant unavailable in either run is a FAILED check (never a shrunken roster); a numerical failure or a nesting
    failure in either run fails it; a Δ₃ difference at or above T = min(8.83e-5, one tenth of the reference half-width)
    fails it and is named; selection flips are listed per fold; the summary names the LATENCY RULE outcome."""
    A = _fake_run("A", dict(n_tau_nodes=31, n_g_nodes=17))
    B = _fake_run("B", dict(n_tau_nodes=61, n_g_nodes=17))
    c = s2.repair_compare(A, B)
    assert c["passed"] and c["n_compared"] == 20 and c["max_abs_diff"] == 0.0 and c["same_code"] and c["same_data"]
    assert abs(c["tolerance"] - min(s2.REPAIR_T_ABS, 0.1 * B["half_width"])) < 1e-15 and c["selection_flips"] == {}
    c = s2.repair_compare(A, _fake_run("B", dict(n_tau_nodes=61), nan_m=3))
    assert not c["passed"] and c["unavailable"] == ["m3"] and c["n_compared"] == 19 and c["diffs"]["m3"] is None
    c = s2.repair_compare(_fake_run("A", dict(n_tau_nodes=31), failures=["m1:f0_B3+"]), B)
    assert not c["passed"] and c["numerical_failures"] == ["m1:f0_B3+"]
    c = s2.repair_compare(A, _fake_run("B", dict(n_tau_nodes=61), failures=["m2:f1_G3+"]))
    assert not c["passed"] and c["numerical_failures"] == ["ref:m2:f1_G3+"]
    c = s2.repair_compare(_fake_run("A", dict(n_tau_nodes=31), nest_break=(4, 2, "B2")), B)
    assert not c["passed"] and len(c["nesting_failures"]["candidate"]) == 1 and c["nesting_failures"]["candidate"][0]["m"] == 4
    c = s2.repair_compare(_fake_run("A", dict(n_tau_nodes=31), delta_shift={5: 1e-4}), B)
    assert not c["passed"] and c["over_tolerance"] == ["m5"] and abs(c["max_abs_diff"] - 1e-4) < 1e-12 and c["worst_participant"] == "m5"
    assert c["moved"]["m5"]["family"] == "B3" and abs(c["moved"]["m5"]["B3"] - 1e-4) < 1e-12
    c = s2.repair_compare(_fake_run("A", dict(n_tau_nodes=31), delta_shift={5: 5e-5}), B)
    assert c["passed"] and c["over_tolerance"] == []
    # a nesting deficit at MIXED scale quadrature is not a failure (not comparable), at the same quadrature it is
    rows = s2._nesting_rows(_fake_run("D", dict(n_tau_nodes=31), nest_break=(0, 0, "B3+")))
    assert sum(r["failure"] for r in rows) == 1
    mixed = _fake_run("D", dict(n_tau_nodes=31), nest_break=(0, 0, "B3+"))
    mixed["participants"][0]["folds"][0]["fits"]["G3+"]["quad"]["n_g_nodes"] = 33
    assert sum(r["failure"] for r in s2._nesting_rows(mixed)) == 0
    # the summary over whatever runs exist, in a scratch checks directory
    old = s2.CHECK_DIR
    tmp = tempfile.mkdtemp()
    s2.CHECK_DIR = tmp
    try:
        for run in (A, B, _fake_run("C", dict(n_tau_nodes=31, n_g_nodes=33), g_nodes=33)):
            with open(s2.repair_paths("W2", 0, run["label"])[0], "w") as f:
                json.dump(run, f)
        s = s2.repair_summary("W2", 0)
        assert set(s["comparisons"]) == {"A_vs_B", "A_vs_C"} and s["one_code_hash"] and s["latency_rule"].startswith("RETAIN 31")
        assert s["cost"]["C_over_A_task_seconds"] == 1.0 and os.path.exists(os.path.join(tmp, "repair_W2_set0_summary.md"))
        md = s2.repair_summary_markdown(s)
        assert "| A_vs_B | PASS |" in md and "LATENCY RULE outcome: RETAIN 31" in md
        with open(s2.repair_paths("W2", 0, "B")[0], "w") as f:
            json.dump(_fake_run("B", dict(n_tau_nodes=61), delta_shift={7: 2e-4}), f)
        s = s2.repair_summary("W2", 0)
        assert not s["comparisons"]["A_vs_B"]["passed"] and s["latency_rule"].startswith("ADOPT 61") and "owed" in s["latency_rule"]
    finally:
        s2.CHECK_DIR = old


if __name__ == "__main__":
    import inspect
    import traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception:  # noqa
                fails += 1
                print("FAIL", name)
                traceback.print_exc(limit=3)
    print("FAILED" if fails else "ALL OK", fails)
    sys.exit(1 if fails else 0)
