"""The production paths execute the frozen S4 rule (25 Oct 2026, Codex S3 re-review findings 6, 7, 8, 11): every fit that
the decision batch (s4.cv_task), the c0 batch (s4.c0_task), the recovery battery with its profiles (s4.rec_task) and S5
(s5.cv_task, s5.full_task) request is built on 61 latency nodes, 17 adaptive scale nodes and the "17then33" rule, every
constrained profile fit has FOUR starts, O1/O2 recovery draws ONE dataset shared by both families, and a fit with a standing
numerical failure never reaches a task record or a score as a clean AVAILABLE. The fitter's em_fit is replaced by a fast
recorder that returns a plausible AVAILABLE fit at its first start (no optimisation runs); everything around it — the
cross-family procedure, selection, the two-pass rule, the final guard, profile search, held-out scoring — is the real code.
Synthetic participants from the stored generators only; never real data. About a minute.
Run: ../../t1_access/.venv/bin/python tests/test_production.py"""
import json
import os
import sys
import tempfile

os.environ.setdefault("NPROC", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402

import fit as F  # noqa: E402
import models as M  # noqa: E402
import s4  # noqa: E402
import s5  # noqa: E402

SEEN = []


def _loglik(sp) -> float:
    """Stub log-likelihoods that respect the nesting (B above G) and favour the positive candidate (so POSITIVE selections
    and the profile paths are exercised); constrained profile points sit below the unrestricted fit."""
    v = -10000.0 + (1.0 if sp.family == "B" else 0.0) + (0.5 if sp.tau_free else 0.0) + (0.1 if sp.scale_free else 0.0)
    if not sp.tau_free and sp.tau_fixed_ms > 0:
        v -= 0.2 + 0.01 * sp.tau_fixed_ms
    return v


def _stub_em_fit(sp, ds, starts=None, info=None, options=None, em=True, max_iter=F.EM_MAX_ITER, tol=F.EM_TOL, warm=None):
    SEEN.append(dict(name=sp.name, n_tau=sp.n_tau_nodes, n_g=sp.n_g_nodes, adaptive=sp.adaptive_g, rule=M.QUAD_G_RULE,
                     n_starts=len(starts) if starts else 0, constrained=bool(not sp.tau_free and sp.tau_fixed_ms > 0),
                     ident=ds.ident))
    theta = np.asarray(starts[0][1] if starts else warm[0][1], dtype=np.float64)
    lb, ub = sp.bounds()
    theta = np.clip(theta, lb, ub)
    ll = _loglik(sp)
    archive = [F.StartResult(lab, "CONVERGED", np.clip(np.asarray(x, dtype=np.float64), lb, ub), -ll, 0.0, 10, 11, 0.0, [])
               for lab, x in (starts or [])]
    return F.FitResult(sp.name, ds.ident, "AVAILABLE", theta, ll, archive, 4, 0.0, M.code_hash(), [], [], [],
                       wh=ds.wh, quad=F._quad_of(sp))


class _Stubbed:
    def __enter__(self):
        self.orig = F.em_fit
        F.em_fit = _stub_em_fit
        SEEN.clear()
        return self

    def __exit__(self, *a):
        F.em_fit = self.orig


def _assert_frozen(rows):
    assert rows, "no fit was requested"
    for r in rows:
        assert (r["n_tau"], r["n_g"], r["adaptive"], r["rule"]) == (61, 17, True, "17then33"), r


def test_every_production_path_uses_61_nodes_the_17then33_rule_and_four_profile_starts():
    assert (M.N_TAU_NODES, M.N_G_NODES, M.QUAD_G_RULE, M.QUAD_G_REFIT_SG, F.PROFILE_STARTS) == (61, 17, "17then33", 0.6, 4)
    assert M.spec("G3+").n_tau_nodes == 61 and M.ModelSpec("G", True, 0.0, True, "primary").n_tau_nodes == 61
    assert M.tau_nodes_ms().size == 61 and M.basis("primary").Bmat.shape[0] == 61
    assert F.profile_evaluator.__defaults__[1] == 4 and F.constrained_starts.__defaults__[0] == 4
    bases = s4.load_bases()
    tmp = tempfile.mkdtemp()
    c0 = {"G": 3.84, "B": 3.84}
    with _Stubbed():
        base = s4.set_members("development", "W2", 0)[0]
        rec = s4.cv_task("development", "W2", 0, 0, base, bases, s4.DECISION_MODELS, False, None, os.path.join(tmp, "cv.json"))
        _assert_frozen(SEEN)
        assert {r["name"] for r in SEEN} >= {"G2", "G3+", "B2", "B3+"}
        assert rec["run_fingerprint"] == s4.run_fingerprint() and np.isfinite(rec["scores"]["G3"])
        assert rec["numerical_failures"] == [] and rec["nesting_failures"] == []
        SEEN.clear()
        rec = s4.c0_task("G", 10, 0, bases, os.path.join(tmp, "c0.json"))
        _assert_frozen(SEEN)
        assert rec["reduced"]["quad"]["n_tau_nodes"] == 61 and rec["positive"]["status"] == "AVAILABLE"
        SEEN.clear()
        rec = s4.rec_task("40|fitted", 10, 0, bases, c0, os.path.join(tmp, "rec.json"))
        _assert_frozen(SEEN)
        prof = [r for r in SEEN if r["constrained"]]
        assert prof and all(r["n_starts"] == F.PROFILE_STARTS == 4 for r in prof), prof[:3]
        for fam in ("G", "B"):
            pts = rec["families"][fam]["profile_points"]
            assert rec["families"][fam]["profile"] is not None and rec["families"][fam]["profile_starts"] == 4
            assert all(v["n_starts"] == 4 for k, v in pts.items() if float(k) > 0) and pts["0"]["status"] == "AVAILABLE"
        SEEN.clear()
        p = s4.make_synthetic("development", "W2", 0, 1, s4.set_members("development", "W2", 0)[1], bases)
        rec = s5.full_task(p, c0, os.path.join(tmp, "s5full.json"))
        _assert_frozen(SEEN)
        assert [r for r in SEEN if r["constrained"]] and all(r["n_starts"] == 4 for r in SEEN if r["constrained"])
        assert rec["families"]["G"]["profile_starts"] == 4 and rec["run_fingerprint"] == s4.run_fingerprint()
        SEEN.clear()
        rec = s5.cv_task(p, os.path.join(tmp, "s5cv.json"))
        _assert_frozen(SEEN)
        assert np.isfinite(rec["scores"]["B3"]) and rec["numerical_failures"] == []


def test_o1_o2_recovery_shares_one_dataset_and_one_fit_across_families():
    """Codex S3 re-review finding 11: at O1 and O2 each (config, i) draws ONE dataset (a seed that does not name the family),
    the eight models are fitted once on it, and both families' profiles read that common dataset and cache; a W recovery
    setting keeps its per-family generation as declared."""
    bases = s4.load_bases()
    tmp = tempfile.mkdtemp()
    c0 = {"G": 3.84, "B": 3.84}
    with _Stubbed():
        for key in ("O1", "O2"):
            SEEN.clear()
            rec = s4.rec_task(key, 13, 0, bases, c0, os.path.join(tmp, f"{key}.json"))
            fam = rec["families"]
            assert fam["G"]["data_id"] == fam["B"]["data_id"] and fam["G"]["shared_dataset"] and fam["B"]["shared_dataset"]
            unrestricted = [r for r in SEEN if not r["constrained"] and r["name"] in ("G2", "G3+", "B2", "B3+")]
            idents = {r["ident"].split("/")[0] for r in unrestricted}
            assert len(idents) == 1, idents                                       # one dataset for every fit
            # each candidate's multi-start fit runs once (chains — re-seeds, nests — carry no starts of their own)
            assert all(sum(1 for r in SEEN if r["name"] == n and r["n_starts"] > 0) == 1 for n in ("G2", "G3+", "B2", "B3+"))
            assert fam["G"]["profile"] is not None and fam["B"]["profile"] is not None
        rec = s4.rec_task("40|fitted", 13, 0, bases, c0, os.path.join(tmp, "W.json"))
        assert rec["families"]["G"]["data_id"] != rec["families"]["B"]["data_id"]
        assert not rec["families"]["G"]["shared_dataset"]


def test_a_flagged_available_fit_never_reaches_a_record_as_clean():
    """Codex S3 re-review finding 7 at the task/aggregation boundary: fit_all_models is made to hand back an AVAILABLE B3
    carrying numerical_failure=True (bypassing the fitter's own exit); s4.cv_task's boundary guard still records it
    UNAVAILABLE with the flag, scores B3 as NaN for that participant (so set_primary's availability count sees it like any
    UNAVAILABLE fit) and lists the failure in the task record."""
    bases = s4.load_bases()
    tmp = tempfile.mkdtemp()
    orig = F.fit_all_models

    def flagged(ds, cache=None, span_name=None, models=F.FULL_MODELS, quad=None, extra_warm=None):
        with _Stubbed():
            res = orig(ds, cache, span_name, models, quad, extra_warm)
        res["B3"].numerical_failure = True                                     # AVAILABLE and flagged, as in the review
        return res

    try:
        F.fit_all_models = flagged
        base = s4.set_members("development", "W2", 0)[0]
        rec = s4.cv_task("development", "W2", 0, 0, base, bases, s4.DECISION_MODELS, False, None, os.path.join(tmp, "cv.json"))
    finally:
        F.fit_all_models = orig
    with open(os.path.join(tmp, "cv.json")) as f:
        disk = json.load(f)
    for row in (rec, disk):
        assert not np.isfinite(row["scores"]["B3"]) and np.isfinite(row["scores"]["G3"])
        assert all(fold["fits"]["B3"]["status"] == "UNAVAILABLE" and fold["fits"]["B3"]["numerical_failure"]
                   and fold["fits"]["B3"]["unavailable_reason"] == "numerical_failure" for fold in row["folds"])
        assert row["numerical_failures"] == [f"f{f}_B3" for f in range(5)]


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
                traceback.print_exc(limit=5)
    print("FAILED" if fails else "ALL OK", fails)
    sys.exit(1 if fails else 0)
