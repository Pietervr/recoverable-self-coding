"""Branch tests of jitter/decide.py (DESIGN rev 6 §6 'Branch tests committed at S3 cover at least …', §7.4, §7.5).
Run: ../../t1_access/.venv/bin/python tests/test_decide.py   (or -m pytest tests/test_decide.py -q)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402

import decide as X  # noqa: E402

P = X.POSITIVE; N = X.NEGATIVE; U = X.UNRESOLVED; UA = X.UNAVAILABLE


def _scores(n=20, seed=0, **shift):
    """Per-participant scores for the eight models: base −15 nat/trial plus small model offsets and noise;
    `shift` moves one model's offset for every participant (e.g. B3=0.01)."""
    rng = np.random.default_rng(seed)
    base = dict(G0=0.0, G2=0.0, G3=0.0, B0=0.0, B2=0.0, B3=0.0, G1=0.0, B1=0.0)
    base.update(shift)
    out = {}
    for p in range(n):
        noise = rng.normal(0, 0.002)
        out[f"S{p+1}"] = {m: -15.0 + noise + base[m] + rng.normal(0, 1e-4) for m in base}
    return out


# ---- sign partition -----------------------------------------------------------------------------
def test_sign_partition_and_exact_zero_bounds():
    assert X.sign_of(0.1, 0.5) == P and X.sign_of(-0.5, -0.1) == N and X.sign_of(-0.1, 0.1) == U
    assert X.sign_of(0.0, 0.5) == U and X.sign_of(-0.5, 0.0) == U        # a bound exactly 0 is UNRESOLVED
    assert X.sign_of(np.nan, 0.5) == X.NONFINITE
    iv = X.t_interval([1.0, 1.1, 0.9, 1.0])
    assert iv.sign == P and iv.n == 4 and iv.lo < 1.0 < iv.hi
    assert X.t_interval([1.0]).sign == UA
    assert X.t_interval([1.0, np.nan]).sign == X.NONFINITE


def test_roster_of_15_is_unavailable():
    s = _scores(n=15, B3=0.01)
    d = X.decide(s)
    assert d.primary.sign == UA and not d.licence_primary
    assert any("< 16" in r for r in d.licence_reasons)
    assert d.D.sign == UA and d.bridge_iv.sign == UA
    s = _scores(n=16, B3=0.01, gates=None) if False else _scores(n=16, B3=0.01)
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    assert d.primary.sign == P and d.licence_primary


# ---- §6 fields ----------------------------------------------------------------------------------
def test_primary_positive_with_full_licence_and_fields():
    s = _scores(B0=0.02, B2=0.012, B3=0.006)       # D = 0.014, D_scale = 0.008, D_tau = 0.006
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True, epsilon=0.003, epsilon_available=True,
                 lambda_e1_certified=True, gate_e_met=True)
    assert d.licence_primary and d.primary.sign == P
    assert d.D.sign == P and d.D_scale.sign == P and d.D_tau.sign == P and d.D_tau_minus_D_scale.sign == N
    assert d.bridge_iv.sign == P and d.premise
    assert d.upper_bound == "NOT BOUNDED"
    assert abs((d.D.mean) - (d.D_scale.mean + d.D_tau.mean)) < 1e-12       # D = D_scale + D_tau exactly on R6
    assert d.attribution["B3-B2"].sign == N and d.attribution["G3-G2"].sign == U


def test_failed_recovery_with_valid_prediction():
    s = _scores(B3=0.01)
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    c = X.claims(d, recovery_G="NOT ADEQUATE", detected_G=False, rise_W3=True, rise_W4=True)
    assert c["primary_positive"] and not c["latency_part"] and not c["not_licensed"]


def test_B0_G0_missing_with_B3_G3_available():
    s = _scores(B3=0.01)
    for p in list(s)[:6]:
        s[p]["B0"] = float("nan")
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    assert d.primary.sign == P and d.licence_primary                 # primary on its own roster
    assert len(d.R6) == 14 and d.D.sign == UA and d.bridge_iv.sign == UA and not d.premise
    assert d.bridge_iii.sign == UA and d.attribution["B3-B2"].sign == P


def test_epsilon_unavailable_and_lambda_not_certified_leave_primary_unaffected():
    s = _scores(B3=0.001)
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True, epsilon=None, epsilon_available=False)
    assert d.upper_bound == UA and d.licence_primary
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True, epsilon=0.01, epsilon_available=True,
                 lambda_e1_certified=False, gate_e_met=True)
    assert d.upper_bound == UA and d.licence_primary
    assert X.epsilon(X.Interval(0.03, 0.01, 0.05, 50, P)) == 0.01
    assert X.epsilon(X.Interval(0.03, -0.01, 0.07, 50, U)) is None
    assert X.epsilon(X.Interval(np.nan, np.nan, np.nan, 3, UA)) is None


def test_positive_but_sub_epsilon_advantage_is_positive_and_bounded():
    s = _scores(B3=0.001)
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True, epsilon=0.01, epsilon_available=True,
                 lambda_e1_certified=True, gate_e_met=True)
    assert d.primary.sign == P and d.upper_bound == "BOUNDED"          # both reported, neither ends the other


def test_nonfinite_fits_fail_V3():
    s = _scores(B3=0.01)
    s["S3"]["G3"] = float("inf")
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    # inf is not 'available' -> dropped from the roster; a finite-but-non-finite interval is NONFINITE
    assert "S3" not in d.primary_roster
    s = _scores(B3=0.01)
    vals = {p: 1.0 for p in s}
    vals["S1"] = np.inf
    iv = X.t_interval([np.inf, 1.0, 1.0])
    assert iv.sign == X.NONFINITE


def test_rev3_counterexample_no_latency_attribution():
    """D POSITIVE, G3 − G2 and B3 − B2 POSITIVE, D_tau NEGATIVE → no latency attribution."""
    s = _scores(B0=0.020, B2=0.004, B3=0.008, G2=0.001, G3=0.003)
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    assert d.D.sign == P and d.attribution["G3-G2"].sign == P and d.attribution["B3-B2"].sign == P
    assert d.D_tau.sign == N
    c = X.claims(d, "ADEQUATE", True, True, True)
    assert not c["latency_part"] and not c["latency_most"]


def test_rev4_counterexample_no_most_of_the_attenuation():
    """D_tau POSITIVE, D_tau − D_scale POSITIVE, D NEGATIVE → no attenuation premise; only the Δ₂ wording."""
    s = _scores(B0=0.000, B2=0.010, B3=0.004)      # D = -0.004, D_scale = -0.010, D_tau = +0.006
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    assert d.D_tau.sign == P and d.D_tau_minus_D_scale.sign == P and d.D.sign == N and not d.premise
    c = X.claims(d, "ADEQUATE", True, True, True)
    assert not c["latency_most"] and not c["latency_part"] and c["latency_reduced_delta2_only"]


def test_rev5_counterexample_bridge_positive_but_delta0_on_R6_not():
    """BRIDGE (iii) POSITIVE on 20 while Δ₀ on R6 (16) is negative → premise fails."""
    s = _scores()
    ps = list(s)
    for p in ps[:16]:
        s[p]["B0"] = s[p]["G0"] - 0.0001
        s[p]["B2"] = s[p]["G2"] - 0.0003
        s[p]["B3"] = s[p]["G3"] - 0.0011
    for p in ps[16:]:
        s[p]["B0"] = s[p]["G0"] + 0.1
        s[p]["B3"] = float("nan")      # missing later fits
    d = X.decide(s, gates_bc_met=True, v2_sim_met=True)
    assert len(d.R6) == 16 and d.bridge_iii.sign == P and d.bridge_iv.sign == N
    assert d.D.sign == P and d.D_tau.sign == P and d.D_tau_minus_D_scale.sign == P and not d.premise


# ---- set-level primary and gates -----------------------------------------------------------------
def test_set_primary_and_gates():
    s = _scores(B3=0.01)
    assert X.set_primary(s) == P
    for p in list(s)[:5]:
        s[p]["B3"] = float("nan")
    assert X.set_primary(s) == UA                                     # 15 usable < 16
    outs = {"W1": [U] * 99 + [P], "O1": [U] * 100}
    assert X.gate_b(outs)["passed"]
    outs["O1"][0] = UA                                                # UNAVAILABLE counts as POSITIVE
    outs["O1"][1] = UA
    assert not X.gate_b(outs)["passed"]
    assert X.gate_b({"W1": [U] * 99})["passed"] is False               # incomplete setting
    assert X.gate_c([P] * 45 + [U] * 5)["passed"] and not X.gate_c([P] * 44 + [UA] * 6)["passed"]
    assert X.gate_e(["NOT BOUNDED"] * 96 + ["BOUNDED"] * 4)["passed"]
    assert not X.gate_e(["NOT BOUNDED"] * 95 + ["BOUNDED"] * 4 + [UA])["passed"]
    v2 = X.completion_v2({"W1": [U] * 90 + [UA] * 10, "T1": [P] * 50})
    assert v2["passed"]
    assert not X.completion_v2({"W1": [U] * 89 + [UA] * 11})["passed"]  # over the UNAVAILABLE limit
    lo, hi = X.clopper_pearson(1, 100)
    assert abs(hi - 0.0466) < 5e-4
    lo, hi = X.clopper_pearson(45, 50)
    assert abs(lo - 0.801) < 2e-3


# ---- profiles (§7.5) -----------------------------------------------------------------------------
def _ev_from(fn):
    def evaluate(s):
        v = fn(s)
        return (None if v is None else float(v)), dict(s=s)
    return evaluate


def test_hull_simple_interval_and_bisection():
    # ell_prof(s) = -(s - 40)^2 / 400 : q = (s-40)^2/200; accepted where q <= 3.841 -> |s-40| <= 27.7
    pr = X.hull_search(_ev_from(lambda s: -(s - 40.0) ** 2 / 400.0), 0.0, c0=3.841)
    assert pr.status == "AVAILABLE" and pr.accepted == [15.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    # lower bracket (10, 15): midpoint 12.5 has q = 3.78 accepted -> lower bound stays at the rejected 10
    assert pr.lo == 10.0
    # upper bracket (60, 80): midpoint 70 has q = 4.5 rejected -> upper bound moves to 70
    assert pr.hi == 70.0 and pr.midpoints == [12.5, 70.0] and pr.n_constrained == 15
    assert not pr.disconnected and not pr.flagged_unrestricted and pr.covers(40.0) and not pr.lower_bound_exceeds


def test_hull_accepted_zero_and_150_endpoints():
    pr = X.hull_search(_ev_from(lambda s: -(s / 1000.0) ** 2), 0.0, c0=3.841)  # everything accepted
    assert pr.lo == 0.0 and pr.hi == 150.0 and pr.n_constrained == 13 and pr.midpoints == []
    pr = X.hull_search(_ev_from(lambda s: -(s - 150.0) ** 2 / 400.0), 0.0, c0=3.841)
    # q = (s-150)^2/200: only 150 accepted (120: q = 4.5); bracket (120, 150), midpoint 135 has q = 1.125 ->
    # accepted -> the rejected endpoint stays: lo = 120, hi = 150 (accepted domain endpoint)
    assert pr.hi == 150.0 and pr.lo == 120.0 and pr.accepted == [150.0] and pr.midpoints == [135.0]


def test_hull_zero_uses_c0_and_lower_bound_exceeds_20():
    # q(0) = 13.6 > c0 = 5 -> zero rejected; profile peaked at 70: q = (s-70)^2/360, accepted 40..100;
    # lower bracket (30, 40), midpoint 35 has q = 3.40 accepted -> lo = 30 > 20
    pr = X.hull_search(_ev_from(lambda s: -(s - 70.0) ** 2 / 720.0), 0.0, c0=5.0)
    assert 0.0 not in pr.accepted and pr.lo == 30.0 and pr.lower_bound_exceeds
    # same profile but c0 huge -> zero accepted and kept even though the accepted set is disconnected
    pr2 = X.hull_search(_ev_from(lambda s: -(s - 70.0) ** 2 / 720.0), 0.0, c0=1e9)
    assert pr2.lo == 0.0 and pr2.disconnected and 0.0 in pr2.accepted and not pr2.lower_bound_exceeds
    # a lower bound of exactly 20 ms does not exceed 20 (profile peaked at 60: bracket (20, 30), midpoint 25 accepted)
    pr3 = X.hull_search(_ev_from(lambda s: -(s - 60.0) ** 2 / 720.0), 0.0, c0=5.0)
    assert pr3.lo == 20.0 and not pr3.lower_bound_exceeds


def test_hull_empty_set_and_unavailable_fits():
    pr = X.hull_search(_ev_from(lambda s: -100.0), 0.0, c0=3.841)
    assert pr.status == "UNAVAILABLE" and pr.reason == "empty accepted set"
    pr = X.hull_search(_ev_from(lambda s: None if s == 40.0 else -(s - 40) ** 2 / 400.0), 0.0, c0=3.841)
    assert pr.status == "UNAVAILABLE" and "40" in pr.reason
    pr = X.hull_search(_ev_from(lambda s: None if s == 12.5 else -(s - 40) ** 2 / 400.0), 0.0, c0=3.841)
    assert pr.status == "UNAVAILABLE" and "lower bisection" in pr.reason       # unavailable midpoint
    assert X.hull_search(_ev_from(lambda s: 0.0), 0.0, c0=None).status == "UNAVAILABLE"


def test_hull_reference_rule_recomputes_all_q():
    # grid optimum above ell_hat: ell_prof(40) = 1 > ell_hat = 0 -> reference 1, every q recomputed
    pr = X.hull_search(_ev_from(lambda s: 1.0 - (s - 40.0) ** 2 / 400.0), 0.0, c0=3.841)
    assert pr.flagged_unrestricted and abs(pr.ref - 1.0) < 1e-12
    assert abs(pr.q[0.0] - 2.0 * (1.0 - (1.0 - 4.0))) < 1e-12 and abs(pr.q[40.0]) < 1e-12   # q(0) = 8


def test_hull_review_counterexample_midpoint_raises_reference_invalidating_refined_bracket():
    """Codex rev 5 §4: ell_hat = 0, ell(20) = −2.5, ell(30) = −1, ell(40) = 0; the midpoint 25 attains ell = 1,
    so 30 goes from q = 2 (accepted) to q = 4 (rejected): the refined bracket is obsolete → UNAVAILABLE."""
    table = {20.0: -2.5, 30.0: -1.0, 40.0: 0.0, 25.0: 1.0}

    def f(s):
        if s in table:
            return table[s]
        return -50.0                                       # everything else firmly rejected
    pr = X.hull_search(_ev_from(f), 0.0, c0=3.841)
    assert pr.status == "UNAVAILABLE" and "reference increase" in pr.reason and pr.flagged_unrestricted


def test_hull_midpoint_reference_increase_without_invalidation_is_kept():
    """A midpoint slightly above ell_hat that flips no refined endpoint: profile stays AVAILABLE, flagged."""
    def f(s):
        return 0.001 if s == 12.5 else -(s - 40.0) ** 2 / 400.0     # the midpoint beats ell_hat = 0 by 0.001
    pr = X.hull_search(_ev_from(f), 0.0, c0=3.841)
    assert pr.status == "AVAILABLE" and pr.flagged_unrestricted and abs(pr.ref - 0.001) < 1e-12
    assert pr.lo == 10.0 and pr.accepted == [15.0, 20.0, 30.0, 40.0, 50.0, 60.0]   # no acceptance flipped


def test_off_grid_truth_coverage_is_meaningful():
    pr = X.hull_search(_ev_from(lambda s: -(s - 33.0) ** 2 / 400.0), 0.0, c0=3.841)
    assert pr.covers(33.0) and pr.lo <= 33.0 <= pr.hi


def test_q0_statistic_and_critical_value():
    assert X.q0_statistic(-10.0, -9.0) == 2.0 and X.q0_statistic(-10.0, -11.0) == 0.0   # never negative
    assert X.q0_statistic(None, -9.0) is None
    vals = list(np.linspace(0, 10, 500))
    c0, info = X.critical_value(vals, 500)
    assert abs(c0 - np.percentile(vals, 95)) < 1e-12 and info["status"] == "AVAILABLE"
    c0, info = X.critical_value(vals[:470] + [None] * 30, 500)
    assert c0 is None and info["status"] == "UNAVAILABLE"            # > 5% unavailable


# ---- calibration (§7.4) ---------------------------------------------------------------------------
def _iv(m, h, n=20):
    return X.Interval(m, m - h, m + h, n, X.sign_of(m - h, m + h))


def test_procedure_reference_unavailable_rule():
    assert X.procedure_reference([0.01] * 45 + [None] * 5).sign != UA
    assert X.procedure_reference([0.01] * 44 + [None] * 6).sign == UA


def test_lambda_successful_initial_targeting_by_bracket():
    pil = [(1.0, _iv(0.040, 0.004)), (0.75, _iv(0.030, 0.004)), (0.5, _iv(0.020, 0.004)),
           (0.35, _iv(0.012, 0.004)), (0.25, _iv(0.008, 0.004))]
    target, eps = 0.025, 0.02
    rec = X.lambda_path(pil, target, eps, certify=lambda lam: _iv(0.02 + 0.04 * (lam - 0.5), 0.001, 50))
    assert rec.status == "CERTIFIED" and rec.mode == "bracket" and abs(rec.lam - 0.625) < 1e-12
    assert len(rec.attempts) == 1


def test_lambda_exact_hit_selects_largest_and_fails_without_correction():
    pil = [(1.0, _iv(0.030, 0.006)), (0.75, _iv(0.027, 0.006)), (0.5, _iv(0.020, 0.004))]
    rec = X.lambda_path(pil, 0.025, 0.02, certify=lambda lam: _iv(0.05, 0.001, 50))   # certification misses
    assert rec.mode == "hit" and rec.lam == 1.0 and rec.status == "UNCERTIFIED" and len(rec.attempts) == 1


def test_lambda_failed_then_corrected_targeting():
    pil = [(1.0, _iv(0.040, 0.004)), (0.5, _iv(0.020, 0.004))]
    target, eps = 0.030, 0.02
    truth = lambda lam: 0.02 + 0.05 * (lam - 0.5) ** 1.5 * 4   # nonlinear: the first interpolation misses
    rec = X.lambda_path(pil, target, eps, certify=lambda lam: _iv(truth(lam), 0.0005, 50))
    assert rec.mode == "bracket" and len(rec.attempts) == 2
    assert rec.attempts[0]["status"] == "MISS"
    assert rec.status in ("CERTIFIED", "UNCERTIFIED")


def test_lambda_precision_failure_unavailable_and_search_failure():
    pil = [(1.0, _iv(0.040, 0.004)), (0.5, _iv(0.020, 0.004))]
    rec = X.lambda_path(pil, 0.030, 0.02, certify=lambda lam: _iv(0.030, 0.01, 50))       # too wide
    assert rec.status == "UNCERTIFIED" and rec.attempts[0]["status"] == "PRECISION FAILURE"
    rec = X.lambda_path(pil, 0.030, 0.02, certify=lambda lam: None)                       # unavailable reference
    assert rec.status == "UNCERTIFIED" and rec.attempts[0]["status"] == "UNAVAILABLE"
    rec = X.lambda_path([(1.0, _iv(0.010, 0.001)), (0.5, _iv(0.005, 0.001))], 0.030, 0.02, certify=lambda lam: None)
    assert rec.status == "SEARCH FAILURE" and rec.reason == "no bracket"
    rec = X.lambda_path([(1.0, None), (0.5, _iv(0.005, 0.001))], 0.030, 0.02, certify=lambda lam: None)
    assert rec.status == "SEARCH FAILURE"


# ---- recovery flags, detection, rise ---------------------------------------------------------------
def _stats(r5_ok=True, r3_ok=True):
    cfgs = [f"c{i}" for i in range(20)]
    good = {c: dict(median_rel_bias=0.1, rmse=10.0, completion_ok=True) for c in cfgs}
    zero = {s: [False] * 125 for s in ((0.0, 0.0), (0.0, "fitted"), (0.0, 1.0), "O1", "O2")}
    fd = {s: [False] * 125 for s in zero}
    if not r3_ok:
        fd["O1"] = [True] * 60 + [False] * 65          # 60 of 625 pooled = 9.6% > 5%
    cov = {(40.0, "fitted"): [True] * 490 + [False] * 10, (80.0, "fitted"): [True] * 495 + [False] * 5}
    r5 = dict(detect=[False] * 500 if r5_ok else [True] * 100 + [False] * 400, cover=[True] * 480 + [False] * 20)
    return {"G": dict(point={(40.0, "fitted"): good, (80.0, "fitted"): good}, false_jitter=zero, false_detect=fd,
                      coverage=cov, r5=r5)}


def test_recovery_flags_three_outcomes():
    assert X.recovery_flags(_stats(), "G")["flag"] == "ADEQUATE"
    assert X.recovery_flags(_stats(r5_ok=False), "G")["flag"] == "ADEQUATE-ZERO-ONLY"
    assert X.recovery_flags(_stats(r3_ok=False), "G")["flag"] == "NOT ADEQUATE"


def test_recovery_r2_r3_judged_per_zero_jitter_setting():
    """Codex S3 review finding 8 (dilution counterexample): O1 alone at 40% false jitter and 20% false detection
    with four clean settings must FAIL R2 and R3 - the rates are judged within each setting, never pooled across them
    (pooled they would read 8% and 4%, both under the thresholds)."""
    st = _stats()
    S = st["G"]
    for s in S["false_jitter"]:
        S["false_jitter"][s] = [False] * 500
        S["false_detect"][s] = [False] * 500
    S["false_jitter"]["O1"] = [True] * 200 + [False] * 300
    S["false_detect"]["O1"] = [True] * 100 + [False] * 400
    out = X.recovery_flags(st, "G")
    assert out["flag"] == "NOT ADEQUATE"
    assert not out["rules"]["R2"]["passed"] and not out["rules"]["R3"]["passed"]
    assert out["rules"]["R2"]["settings"]["O1"]["rate"] == 0.4 and not out["rules"]["R2"]["settings"]["O1"]["passed"]
    assert out["rules"]["R3"]["settings"]["O1"]["rate"] == 0.2 and not out["rules"]["R3"]["settings"]["O1"]["passed"]
    assert all(v["passed"] for k, v in out["rules"]["R2"]["settings"].items() if k != "O1")
    assert len(out["rules"]["R2"]["settings"]) == 5 and len(out["rules"]["R3"]["settings"]) == 5


def test_zero_only_rejection_event_is_lower_bound_above_20():
    """A hull [2.5, 15] excludes zero but licenses nothing; only lower bound > 20 (the R3 event) counts."""
    hull_small = X.Profile("AVAILABLE", "", 2.5, 15.0, [5.0, 10.0, 15.0], [], {}, {}, 0.0, False, False, 15, [])
    hull_big = X.Profile("AVAILABLE", "", 25.0, 80.0, [30.0, 40.0], [], {}, {}, 0.0, False, False, 15, [])
    hull_un = X.Profile("UNAVAILABLE", "x", np.nan, np.nan, [], [], {}, {}, 0.0, False, False, 15, [])
    profiles = {"S1": hull_small, "S2": hull_big, "S3": hull_un, "S4": None}
    assert X.zero_only_participants(profiles) == ["S2"]
    det = X.jitter_detected(profiles, _iv(0.01, 0.001))
    assert det["n_exceeding"] == 1 and not det["detected"]
    many = {f"S{i}": hull_big for i in range(10)}
    assert X.jitter_detected(many, _iv(0.01, 0.001))["detected"]
    assert not X.jitter_detected(many, _iv(0.01, 0.02))["detected"]       # group contrast not POSITIVE


def test_rise_newcombe():
    r = X.rise([False] * 95 + [True] * 5, [False] * 60 + [True] * 40)
    assert r["rise"] and r["lo"] > 0
    r = X.rise([False] * 95 + [True] * 5, [False] * 93 + [True] * 7)
    assert not r["rise"]
    d, lo, hi = X.newcombe(56, 70, 48, 80)         # Newcombe 1998 example (a): 0.20, [0.0524, 0.3339]
    assert abs(d - 0.2) < 1e-9 and abs(lo - 0.0524) < 1e-3 and abs(hi - 0.3339) < 1e-3


if __name__ == "__main__":
    import inspect, traceback
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
