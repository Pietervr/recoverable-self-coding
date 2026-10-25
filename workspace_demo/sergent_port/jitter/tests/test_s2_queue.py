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


def test_sharded_block_is_disjoint_complete_and_assembles():
    """The R = 25 development blocks on K hosts (25 Oct 2026, Codex findings 3/9): `--shard i/K` runs exactly the
    participant-datasets with shard_of(setting, r, m, K) == i, so the K shards are disjoint and cover the block once; the
    settings share one queue; an explicit --out-dir carries the run record (written at first start; a host whose contract
    differs refuses); a sharded host keeps its task files and assembles only the sets it holds whole; `assemble --all`
    then builds every complete set and reports the incomplete ones. decision_task is a fast fake; no fit runs."""
    import fit as F
    old = (s2.decision_task, s2.PARALLEL_BACKEND, s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR)
    s2.decision_task = _fake_task
    s2.PARALLEL_BACKEND = "threading"
    tmp = _redirect()
    out_dir = os.path.join(tmp, "decision_final")
    try:
        K = 3
        seen = []
        for i in range(K):
            CALLS.clear()
            s2.run_decision("W2,T1", 2, 4, out_dir=out_dir, shard=f"{i}/{K}")
            assert all(s2.shard_of(st, r, m, K) == i for st, r, m in CALLS)
            seen += list(CALLS)
        assert len(seen) == len(set(seen)) == 2 * 2 * 20                       # disjoint and complete: 2 settings × 2 sets × 20
        rc = os.path.join(out_dir, F.RUN_CONFIG_NAME)
        assert os.path.exists(rc)
        for st in ("W2", "T1"):
            assert len(os.listdir(os.path.join(out_dir, st, "tasks"))) == 40     # every task file kept
        # the archive goes to results/s2/archive/<basename(out_dir)>/<setting> (out of git)
        assert os.path.isdir(os.path.join(s2.ARC_DIR, "decision_final", "W2", "tasks"))
        os.remove(s2.task_paths("T1", 1, 7, out_dir)[0])                         # one lost task: set 1 of T1 incomplete
        for st in ("W2", "T1"):
            for r in range(2):
                p = os.path.join(out_dir, st, f"set_{r}.json")
                if os.path.exists(p):
                    os.remove(p)
        rep = s2.assemble_all("W2,T1", 2, out_dir)
        assert rep["W2"]["assembled"] == [0, 1] and rep["T1"]["assembled"] == [0] and rep["T1"]["incomplete"] == {1: [7]}
        with open(os.path.join(out_dir, "W2", "set_0.json")) as f:
            rec = json.load(f)
        assert rec["primary"] == "NEGATIVE" and len(rec["participants"]) == 20 and rec["interval"]["n"] == 20
        assert rec["numerical_failures"] == [] and rec["nesting_failures"] == [] and "run_fingerprints" in rec
        # a host with another numerical contract refuses to join the block
        with open(rc) as f:
            rec_cfg = json.load(f)
        rec_cfg["trial_chunk"] = 0 if rec_cfg["trial_chunk"] else 64
        rec_cfg["fingerprint"] = F.config_fingerprint(rec_cfg)
        with open(rc, "w") as f:
            json.dump(rec_cfg, f)
        try:
            s2.run_decision("W2", 2, 4, out_dir=out_dir, shard="0/3")
            assert False, "a mismatched host must refuse"
        except SystemExit as e:
            assert "trial_chunk" in str(e) and "refused" in str(e)
    finally:
        s2.decision_task, s2.PARALLEL_BACKEND, s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR = old


def _vary(extra=None):
    """Participant spread for the set-level tests: Δ₃ varies over m (half-width about 2.0e-4, so T_set about 2.0e-5)."""
    d = {m: 3e-4 * ((m % 5) - 2) for m in range(20)}
    for k, v in (extra or {}).items():
        d[k] = d.get(k, 0.0) + v
    return d


def test_set_compare_is_codex_finding_3_exactly():
    """The amended set-level criterion (Codex S3 re-review finding 3): identical complete rosters, finite results, no
    unresolved numerical failure, no material matched-quadrature nesting failure, the same primary sign, and
    max(|Δμ|, |ΔL|, |ΔU|) < T_set = min(8.8322454e-5, 0.1·min(h_x, h_y)). A participant shift that leaves the group
    interval within T_set PASSES (participant differences are diagnostics); a uniform shift of the mean beyond T_set
    FAILS; a missing participant, a failure, a nesting failure (in either run) or a sign change each FAIL."""
    A = _fake_run("F", dict(n_tau_nodes=61, n_g_nodes=17), delta_shift=_vary())
    B = _fake_run("G", dict(n_tau_nodes=121, n_g_nodes=17), delta_shift=_vary())
    c = s2.set_compare(A, B)
    assert c["passed"] and all(c["criteria"].values()) and c["values"]["d_max"] == 0.0
    h = 0.5 * (c["values"]["hi"][0] - c["values"]["lo"][0])
    assert abs(c["T_set"] - min(s2.REPAIR_T_ABS, 0.1 * h)) < 1e-18
    # one participant moved by 2e-5 (the interval moves by ~1e-6 + its width effect) — the group interval stays inside T_set
    c = s2.set_compare(_fake_run("F", dict(n_tau_nodes=61), delta_shift=_vary({5: 2e-5})), B)
    assert c["passed"] and c["participant_max_abs_diff_diagnostic"] > 1e-5
    # every participant shifted: the mean moves by more than T_set
    c = s2.set_compare(_fake_run("F", dict(n_tau_nodes=61), delta_shift=_vary({m: 1.5 * s2.REPAIR_T_ABS for m in range(20)})), B)
    assert not c["passed"] and not c["criteria"]["group_inequality"] and c["criteria"]["identical_complete_rosters"]
    c = s2.set_compare(A, _fake_run("G", dict(n_tau_nodes=121), nan_m=4, delta_shift=_vary()))
    assert not c["passed"] and not c["criteria"]["identical_complete_rosters"]
    c = s2.set_compare(_fake_run("F", dict(n_tau_nodes=61), failures=["m1:f0_B3+"], delta_shift=_vary()), B)
    assert not c["passed"] and not c["criteria"]["no_unresolved_numerical_failure"] and c["criteria"]["group_inequality"]
    c = s2.set_compare(A, _fake_run("G", dict(n_tau_nodes=121), nest_break=(3, 1, "B3+"), delta_shift=_vary()))
    assert not c["passed"] and not c["criteria"]["no_material_nesting_failure"] and c["nesting_failures"]["reference"][0]["m"] == 3
    other = _fake_run("G", dict(n_tau_nodes=121), delta_shift=_vary())
    other["primary"] = "UNRESOLVED"
    c = s2.set_compare(A, other)
    assert not c["passed"] and not c["criteria"]["same_primary_sign"]
    # a recorded final-guard failure counts as a nesting failure too
    rec = _fake_run("F", dict(n_tau_nodes=61), delta_shift=_vary())
    rec["participants"][2]["folds"][0]["fits"]["B3"]["nesting"] = dict(vs="G3", deficit=-0.3, failure=True)
    assert len(s2.material_nesting(rec)) == 1 and not s2.set_compare(rec, B)["passed"]


def test_final_summary_needs_both_pairs_and_the_crosseval():
    old = s2.CHECK_DIR
    s2.CHECK_DIR = tempfile.mkdtemp()
    try:
        for lab, q in (("F", dict(n_tau_nodes=61, n_g_nodes=17)), ("G", dict(n_tau_nodes=121, n_g_nodes=17))):
            with open(s2.repair_paths("W2", 0, lab)[0], "w") as f:
                json.dump(_fake_run(lab, q, delta_shift=_vary()), f)
        s = s2.final_summary("W2", 0)
        assert not s["passed"] and set(s["missing"]) == {"F_vs_H", "crosseval"} and s["verdict"].startswith("INCOMPLETE")
        with open(s2.repair_paths("W2", 0, "H")[0], "w") as f:
            json.dump(_fake_run("H", dict(n_tau_nodes=61, n_g_nodes=33), g_nodes=33, delta_shift=_vary()), f)
        xe = dict(passed=True, reproduction=dict(max_abs_vs_archived=0.0, passed=True),
                  grids={g: dict(T_set=6e-5, max_abs_change=1e-6, over=[], passed=True, complete=True) for g in ("G", "H")})
        with open(os.path.join(s2.CHECK_DIR, "repair_W2_set0_crosseval.json"), "w") as f:
            json.dump(xe, f)
        s = s2.final_summary("W2", 0)
        assert s["passed"] and s["verdict"].startswith("PASS") and os.path.exists(os.path.join(s2.CHECK_DIR, "repair_W2_set0_final_summary.md"))
        assert "| F_vs_G | PASS |" in s2.final_summary_markdown(s)
        xe["grids"]["H"].update(passed=False, over=["m3"])
        xe["passed"] = False
        with open(os.path.join(s2.CHECK_DIR, "repair_W2_set0_crosseval.json"), "w") as f:
            json.dump(xe, f)
        assert s2.final_summary("W2", 0)["verdict"].startswith("FAIL")
    finally:
        s2.CHECK_DIR = old


def test_crosseval_reproduces_an_archived_run_at_fixed_parameters():
    """The fixed-endpoint cross-evaluation on a real archived run (W2 set 0, run B: 61/17, archived with float64 θ and Σ):
    re-evaluated at its own recorded grid, every participant's Δ₃ equals the archived one to < 1e-9 (the reproduction
    check that makes the grid changes meaningful), and both grids are evaluated for all twenty participants. Skipped when
    the archive is not on this machine. About 15 s at 8 workers."""
    jp, npz = s2.repair_paths("W2", 0, "B")
    if not (os.path.exists(jp) and os.path.exists(npz)):
        print("     (skipped: no archived run B)")
        return
    out = os.path.join(tempfile.mkdtemp(), "xe.json")
    xe = s2.crosseval("W2", 0, "B", 8, out_path=out)
    assert xe["reproduction"]["passed"] and xe["reproduction"]["n"] == 20 and xe["reproduction"]["max_abs_vs_archived"] < 1e-9
    assert all(v["n_evaluated"] == 20 and v["complete"] for v in xe["grids"].values())
    assert set(xe["grids"]) == {"G", "H"} and os.path.exists(out)


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
