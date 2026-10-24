#!/usr/bin/env python3
"""jitter/decide.py — the decision rules of DESIGN_jitter.md rev 6 §6, §7.3–§7.6 as pure functions on tables of
scores, set outcomes and profile objectives. No fitting here. Stage S1 (provisional; FROZEN by commit at S3 with
the branch tests in tests/test_decide.py).

Contents
  sign partition          t_interval, sign (POSITIVE / NEGATIVE / UNRESOLVED; a bound exactly 0 is UNRESOLVED)
  rosters                 primary (B3 and G3 available), R6 (all six of G0 G2 G3 B0 B2 B3), own rosters (≥ 16)
  decision fields (§6)    decide(): PRIMARY SIGN, ATTENUATION D / D_scale / D_τ / D_τ − D_scale on R6, UPPER BOUND,
                          BRIDGE (iii)/(iv), ATTRIBUTION contrasts, licences V2/V3, the attenuation premise
  profiles (§7.5)         hull_search(): grid, reference rule, c₀ at zero, χ²₁(0.95) elsewhere, one bisection per
                          side, conservative outer hull, the UNAVAILABLE rules; q0_statistic, critical_value
  calibration (§7.4)      procedure_reference, epsilon, lambda_path (pilots, exact hits, bracket, certification,
                          one secant correction, precision failure, search failure)
  gates and flags         gate_b/gate_c/gate_e/completion_v2 (§7.3), recovery_flags R1–R5 (§7.5),
                          jitter_detected, rise (§7.6 Newcombe), clopper_pearson bounds, claims (§9)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import norm, t as t_dist

CHI2_95 = 3.841458820694124
MIN_ROSTER = 16
N_PARTICIPANTS = 20
PROFILE_GRID_MS = (0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0, 80.0, 100.0, 120.0, 150.0)
DETECT_MS = 20.0
REF_TOL = 1e-9
SIX = ("G0", "G2", "G3", "B0", "B2", "B3")

POSITIVE, NEGATIVE, UNRESOLVED, UNAVAILABLE, NONFINITE = "POSITIVE", "NEGATIVE", "UNRESOLVED", "UNAVAILABLE", "NONFINITE"


# ----------------------------------------------------------------------------------------------
# sign partition
# ----------------------------------------------------------------------------------------------
@dataclass
class Interval:
    mean: float
    lo: float
    hi: float
    n: int
    sign: str
    level: float = 0.95

    def as_dict(self):
        return dict(mean=self.mean, lo=self.lo, hi=self.hi, n=self.n, sign=self.sign, level=self.level)


def sign_of(lo: float, hi: float) -> str:
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return NONFINITE
    if lo > 0.0:
        return POSITIVE
    if hi < 0.0:
        return NEGATIVE
    return UNRESOLVED


def t_interval(x, level: float = 0.95, min_n: int = 2) -> Interval:
    """Mean with the two-sided t-interval (n − 1 df); participant (or set) as the unit."""
    x = np.asarray([v for v in x if v is not None], dtype=np.float64)
    n = int(x.size)
    if n < min_n:
        return Interval(np.nan, np.nan, np.nan, n, UNAVAILABLE, level)
    if not np.all(np.isfinite(x)):
        return Interval(np.nan, np.nan, np.nan, n, NONFINITE, level)
    m = float(x.mean())
    if n == 1:
        return Interval(m, np.nan, np.nan, n, UNAVAILABLE, level)
    h = float(t_dist.ppf(0.5 + level / 2.0, n - 1) * x.std(ddof=1) / np.sqrt(n))
    return Interval(m, m - h, m + h, n, sign_of(m - h, m + h), level)


def roster_interval(values: dict, roster, level: float = 0.95, min_roster: int = MIN_ROSTER) -> Interval:
    """Paired participant means over `roster`; UNAVAILABLE below the roster minimum."""
    xs = [values[p] for p in roster]
    if len(xs) < min_roster:
        return Interval(np.nan, np.nan, np.nan, len(xs), UNAVAILABLE, level)
    return t_interval(xs, level)


# ----------------------------------------------------------------------------------------------
# rosters and the §6 fields
# ----------------------------------------------------------------------------------------------
def available(scores: dict, p, models) -> bool:
    return all(m in scores[p] and scores[p][m] is not None and np.isfinite(scores[p][m]) for m in models)


def roster(scores: dict, models) -> list:
    return [p for p in scores if available(scores, p, models)]


def contrast(scores: dict, p, a: str, b: str) -> float:
    return float(scores[p][a] - scores[p][b])


@dataclass
class Decision:
    primary: Interval
    primary_roster: list
    licence_primary: bool
    licence_reasons: list
    R6: list
    delta0_R6: Interval
    delta2_R6: Interval
    delta3_R6: Interval
    D: Interval
    D_scale: Interval
    D_tau: Interval
    D_tau_minus_D_scale: Interval
    upper_bound: str
    epsilon: float | None
    bridge_iii: Interval
    bridge_iv: Interval
    attribution: dict
    premise: bool
    fields: dict = field(default_factory=dict)

    def as_dict(self):
        d = dict(primary=self.primary.as_dict(), primary_roster=list(self.primary_roster),
                 licence_primary=self.licence_primary, licence_reasons=self.licence_reasons, R6=list(self.R6),
                 delta0_R6=self.delta0_R6.as_dict(), delta2_R6=self.delta2_R6.as_dict(),
                 delta3_R6=self.delta3_R6.as_dict(), D=self.D.as_dict(), D_scale=self.D_scale.as_dict(),
                 D_tau=self.D_tau.as_dict(), D_tau_minus_D_scale=self.D_tau_minus_D_scale.as_dict(),
                 upper_bound=self.upper_bound, epsilon=self.epsilon, bridge_iii=self.bridge_iii.as_dict(),
                 bridge_iv=self.bridge_iv.as_dict(), attribution={k: v.as_dict() for k, v in self.attribution.items()},
                 premise=self.premise)
        d.update(self.fields)
        return d


def decide(scores: dict, epsilon: float | None = None, epsilon_available: bool = False,
           lambda_e1_certified: bool = False, gate_e_met: bool = False, gates_bc_met: bool = False,
           v2_sim_met: bool = False, n_participants: int = N_PARTICIPANTS) -> Decision:
    """ALL §6 fields from per-participant held-out scores {p: {model: nat/trial or nan}} on the primary span.
    No field ends the evaluation of another. Licence inputs come from S4b (gates) and S4a (ε, λ_E1)."""
    prim_roster = roster(scores, ("G3", "B3"))
    primary = roster_interval({p: contrast(scores, p, "B3", "G3") for p in prim_roster}, prim_roster)
    reasons = []
    if not gates_bc_met:
        reasons.append("V1a: gates (b)/(c) not met in S4b")
    if not v2_sim_met:
        reasons.append("V2: simulation completion not met")
    if len(prim_roster) < MIN_ROSTER:
        reasons.append(f"V2: {len(prim_roster)} of {n_participants} participants with CONVERGED B3 and G3 (< 16)")
    if primary.sign == NONFINITE:
        reasons.append("V3: non-finite primary interval")
    licence = len(reasons) == 0
    R6 = roster(scores, SIX)
    d0 = {p: contrast(scores, p, "B0", "G0") for p in R6}
    d2 = {p: contrast(scores, p, "B2", "G2") for p in R6}
    d3 = {p: contrast(scores, p, "B3", "G3") for p in R6}
    delta0_R6, delta2_R6, delta3_R6 = (roster_interval(x, R6) for x in (d0, d2, d3))
    D = roster_interval({p: d0[p] - d3[p] for p in R6}, R6)
    D_scale = roster_interval({p: d0[p] - d2[p] for p in R6}, R6)
    D_tau = roster_interval({p: d2[p] - d3[p] for p in R6}, R6)
    D_diff = roster_interval({p: (d2[p] - d3[p]) - (d0[p] - d2[p]) for p in R6}, R6)
    if not (epsilon_available and lambda_e1_certified and gate_e_met) or epsilon is None \
            or primary.sign in (UNAVAILABLE, NONFINITE):
        ub = UNAVAILABLE
    else:
        ub = "BOUNDED" if primary.hi < epsilon else "NOT BOUNDED"
    r0 = roster(scores, ("G0", "B0"))
    bridge_iii = roster_interval({p: contrast(scores, p, "B0", "G0") for p in r0}, r0)
    bridge_iv = delta0_R6
    attribution = {}
    for a, b in (("G3", "G2"), ("B3", "B2"), ("G2", "G0"), ("B2", "B0"), ("G3", "G0"), ("B3", "B0")):
        r = roster(scores, (a, b))
        attribution[f"{a}-{b}"] = roster_interval({p: contrast(scores, p, a, b) for p in r}, r)
    premise = bridge_iv.sign == POSITIVE and D.sign == POSITIVE
    return Decision(primary, prim_roster, licence, reasons, R6, delta0_R6, delta2_R6, delta3_R6, D, D_scale, D_tau,
                    D_diff, ub, epsilon, bridge_iii, bridge_iv, attribution, premise)


def set_primary(set_scores: dict, min_available: int = MIN_ROSTER) -> str:
    """Set-level primary of one synthetic replicate set (20 participants): UNAVAILABLE if fewer than 16 have
    both B3 and G3 (§7.7), else the sign of the Δ₃ interval."""
    r = roster(set_scores, ("G3", "B3"))
    if len(r) < min_available:
        return UNAVAILABLE
    return roster_interval({p: contrast(set_scores, p, "B3", "G3") for p in r}, r).sign


# ----------------------------------------------------------------------------------------------
# profiles (§7.5)
# ----------------------------------------------------------------------------------------------
@dataclass
class Profile:
    status: str                      # AVAILABLE | UNAVAILABLE
    reason: str
    lo: float
    hi: float
    accepted: list
    rejected: list
    q: dict                          # s -> q(s) against the final reference
    ell: dict                        # s -> constrained objective (None = UNAVAILABLE)
    ref: float
    flagged_unrestricted: bool
    disconnected: bool
    n_constrained: int
    midpoints: list
    records: dict = field(default_factory=dict)

    @property
    def lower_bound_exceeds(self) -> bool:
        return self.status == "AVAILABLE" and self.lo > DETECT_MS

    def covers(self, s_true: float) -> bool:
        return self.status == "AVAILABLE" and self.lo <= s_true <= self.hi

    def as_dict(self):
        return dict(status=self.status, reason=self.reason, lo=self.lo, hi=self.hi, accepted=self.accepted,
                    rejected=self.rejected, q={str(k): v for k, v in self.q.items()},
                    ell={str(k): v for k, v in self.ell.items()}, ref=self.ref,
                    flagged_unrestricted=self.flagged_unrestricted, disconnected=self.disconnected,
                    n_constrained=self.n_constrained, midpoints=self.midpoints)


def _accept(s: float, q: float, c0: float, chi: float) -> bool:
    return q <= (c0 if s == 0.0 else chi)


def hull_search(evaluate, ell_hat: float, c0: float | None, grid=PROFILE_GRID_MS, chi: float = CHI2_95) -> Profile:
    """The §7.5 profile confidence set for s_τ. `evaluate(s) -> (ℓ_prof(s) or None, record)`; ℓ̂ = the selected
    unrestricted objective. Reference rule: any constrained optimum above ℓ̂ (by more than REF_TOL relative)
    replaces it and every q is recomputed; if that changes the acceptance of an endpoint of an already refined
    bracket, the profile is UNAVAILABLE. Accepted: q(0) ≤ c₀, q(s>0) ≤ χ²₁(0.95). Interval = conservative outer
    hull of the accepted set, each side refined by one bisection (rejected midpoint → the rejected endpoint moves
    to it; accepted → it stays); 0/150 at accepted domain endpoints. At most 15 constrained fits."""
    grid = [float(s) for s in grid]
    ell, records, midpoints = {}, {}, []
    unavailable = c0 is None
    reason = "c0 UNAVAILABLE" if unavailable else ""
    ref = float(ell_hat)
    flagged = False
    n_fits = 0

    def ev(s):
        nonlocal n_fits
        v, rec = evaluate(s)
        n_fits += 1
        ell[s] = None if v is None else float(v)
        records[s] = rec
        return ell[s]

    def q_of(s):
        return 2.0 * (ref - ell[s])

    def acceptance():
        return {s: _accept(s, q_of(s), c0, chi) for s in grid if ell.get(s) is not None}

    if unavailable:
        return Profile("UNAVAILABLE", reason, np.nan, np.nan, [], [], {}, {}, ref, False, False, 0, [], {})
    for s in grid:
        if ev(s) is None:
            return Profile("UNAVAILABLE", f"constrained fit UNAVAILABLE at {s:g} ms", np.nan, np.nan, [], [],
                           {}, dict(ell), ref, False, False, n_fits, [], records)
    top = max(ell.values())
    if top > ref + REF_TOL * max(1.0, abs(ref)):
        ref, flagged = top, True
    acc = acceptance()
    accepted = [s for s in grid if acc[s]]
    if not accepted:
        return Profile("UNAVAILABLE", "empty accepted set", np.nan, np.nan, [], list(grid),
                       {s: q_of(s) for s in grid}, dict(ell), ref, flagged, False, n_fits, [], records)
    refined = []     # (rejected endpoint, accepted endpoint) brackets already refined

    def apply_reference(v):
        """Reference increase from a midpoint value; returns False if an already refined bracket is invalidated."""
        nonlocal ref, flagged, acc
        if v > ref + REF_TOL * max(1.0, abs(ref)):
            before = dict(acc)
            ref, flagged = v, True
            acc = acceptance()
            for s_rej, s_acc in refined:
                if before[s_rej] != acc[s_rej] or before[s_acc] != acc[s_acc]:
                    return False
        return True

    def side(lower: bool):
        """One bisection on one side; returns (bound, ok)."""
        accepted_now = [s for s in grid if acc[s]]
        if not accepted_now:
            return np.nan, False
        if lower:
            s_acc = min(accepted_now)
            if s_acc == grid[0]:
                return grid[0], True
            s_rej = max(s for s in grid if s < s_acc and not acc[s])
        else:
            s_acc = max(accepted_now)
            if s_acc == grid[-1]:
                return grid[-1], True
            s_rej = min(s for s in grid if s > s_acc and not acc[s])
        m = 0.5 * (s_rej + s_acc)
        midpoints.append(m)
        refined.append((s_rej, s_acc))
        v = ev(m)
        if v is None:
            return np.nan, False
        if not apply_reference(v):
            return np.nan, False
        if not acc[s_acc] or acc[s_rej]:
            return np.nan, False          # the bracket itself changed under the new reference
        return (m if not _accept(m, q_of(m), c0, chi) else s_rej), True

    lo, ok = side(True)
    if not ok:
        return Profile("UNAVAILABLE", "lower bisection: unavailable midpoint or reference increase invalidated a "
                       "refined bracket", np.nan, np.nan, [], [], {s: q_of(s) for s in ell if ell[s] is not None},
                       dict(ell), ref, flagged, False, n_fits, midpoints, records)
    hi, ok = side(False)
    if not ok:
        return Profile("UNAVAILABLE", "upper bisection: unavailable midpoint or reference increase invalidated a "
                       "refined bracket", np.nan, np.nan, [], [], {s: q_of(s) for s in ell if ell[s] is not None},
                       dict(ell), ref, flagged, False, n_fits, midpoints, records)
    accepted = [s for s in grid if acc[s]]
    rejected = [s for s in grid if not acc[s]]
    idx = [grid.index(s) for s in accepted]
    disconnected = bool(max(idx) - min(idx) + 1 != len(idx))
    return Profile("AVAILABLE", "", float(lo), float(hi), accepted, rejected,
                   {s: q_of(s) for s in ell if ell[s] is not None}, dict(ell), ref, flagged, disconnected,
                   n_fits, midpoints, records)


def q0_statistic(ell_reduced: float | None, ell_positive: float | None) -> float | None:
    """c₀ calibration statistic q(0) = 2[max(ℓ_reduced, ℓ_positive) − ℓ_reduced] ≥ 0; None if either fit is
    UNAVAILABLE."""
    if ell_reduced is None or ell_positive is None or not (np.isfinite(ell_reduced) and np.isfinite(ell_positive)):
        return None
    return float(2.0 * max(ell_positive - ell_reduced, 0.0))


def critical_value(q0_values, n_total: int, max_unavailable: float = 0.05, level: float = 0.95):
    """c₀ = type-7 95th percentile of the AVAILABLE q(0); UNAVAILABLE if more than 5% of the batch is."""
    vals = [v for v in q0_values if v is not None and np.isfinite(v)]
    n_un = n_total - len(vals)
    if n_total <= 0 or n_un > max_unavailable * n_total:
        return None, dict(n_available=len(vals), n_unavailable=n_un, status="UNAVAILABLE")
    return float(np.percentile(vals, 100.0 * level)), dict(n_available=len(vals), n_unavailable=n_un,
                                                             status="AVAILABLE")


# ----------------------------------------------------------------------------------------------
# calibration (§7.4)
# ----------------------------------------------------------------------------------------------
def procedure_reference(set_means, level: float = 0.95, max_unavailable: float = 0.10) -> Interval:
    """Mean over AVAILABLE replicate sets with its nominal t-interval; UNAVAILABLE if more than 10% of the sets
    are (a set with fewer than 16 usable participants is UNAVAILABLE and counted)."""
    n = len(set_means)
    avail = [v for v in set_means if v is not None and np.isfinite(v)]
    if n == 0 or (n - len(avail)) > max_unavailable * n:
        return Interval(np.nan, np.nan, np.nan, len(avail), UNAVAILABLE, level)
    return t_interval(avail, level)


def epsilon(benchmark: Interval):
    """ε = benchmark/3 from the Δ₀ reference under the fitted B0 generators; UNAVAILABLE if the MC lower bound
    ≤ 0 or the reference is UNAVAILABLE."""
    if benchmark.sign in (UNAVAILABLE, NONFINITE) or not (benchmark.lo > 0.0):
        return None
    return float(benchmark.mean / 3.0)


@dataclass
class LambdaRecord:
    status: str                  # CERTIFIED | UNCERTIFIED | SEARCH FAILURE
    mode: str                    # hit | bracket | none
    lam: float | None
    certified: Interval | None
    attempts: list
    reason: str
    bracket: tuple | None = None

    def as_dict(self):
        return dict(status=self.status, mode=self.mode, lam=self.lam,
                    certified=None if self.certified is None else self.certified.as_dict(),
                    attempts=self.attempts, reason=self.reason, bracket=self.bracket)


def select_lambda(pilots: list, target: float):
    """Pilot selection. `pilots` = [(λ, Interval or None)] on the declared grid. An UNAVAILABLE pilot leaves the
    grid. Exact hits (target inside the MC interval): the largest λ among them (declared tie-break). Otherwise the
    adjacent remaining pair straddling the target, the pair with the larger λ among several. Fewer than two
    remaining pilots or no bracket → SEARCH FAILURE."""
    rem = [(lam, iv) for lam, iv in pilots if iv is not None and iv.sign not in (UNAVAILABLE, NONFINITE)]
    hits = [(lam, iv) for lam, iv in rem if iv.lo <= target <= iv.hi]
    if hits:
        lam, iv = max(hits, key=lambda x: x[0])
        return dict(mode="hit", lam=lam, bracket=None, ref=iv)
    if len(rem) < 2:
        return dict(mode="none", lam=None, bracket=None, ref=None, reason="fewer than two remaining pilots")
    rem = sorted(rem, key=lambda x: x[0])
    pairs = []
    for (l1, i1), (l2, i2) in zip(rem[:-1], rem[1:]):
        if (i1.mean - target) * (i2.mean - target) < 0:
            pairs.append(((l1, i1.mean), (l2, i2.mean)))
    if not pairs:
        return dict(mode="none", lam=None, bracket=None, ref=None, reason="no bracket")
    (l1, r1), (l2, r2) = max(pairs, key=lambda pr: pr[1][0])
    lam = l1 + (target - r1) * (l2 - l1) / (r2 - r1)
    return dict(mode="bracket", lam=float(lam), bracket=((l1, r1), (l2, r2)), ref=None)


def certify_check(iv: Interval | None, target: float, eps: float, tol_frac: float = 0.15) -> str:
    """CERTIFIED if the certified MC interval lies within target ± 0.15 ε; UNAVAILABLE reference → UNCERTIFIED
    (no correction); interval containing the target but too wide → PRECISION FAILURE (no correction);
    otherwise MISS (eligible for the one secant correction)."""
    if iv is None or iv.sign in (UNAVAILABLE, NONFINITE):
        return "UNAVAILABLE"
    lo_t, hi_t = target - tol_frac * eps, target + tol_frac * eps
    if iv.lo >= lo_t and iv.hi <= hi_t:
        return "CERTIFIED"
    if iv.lo <= target <= iv.hi:
        return "PRECISION FAILURE"
    return "MISS"


def lambda_path(pilots: list, target: float, eps: float, certify) -> LambdaRecord:
    """The declared λ search: `certify(λ) -> Interval or None` runs the fresh certification batch at R_ref = 50
    (97.5% per-attempt intervals supplied by the caller). At most one secant correction, only for a bracket
    selection that MISSES; a direct hit has no bracket and fails without correction."""
    sel = select_lambda(pilots, target)
    attempts = []
    if sel["mode"] == "none":
        return LambdaRecord("SEARCH FAILURE", "none", None, None, attempts, sel.get("reason", ""))
    lam = sel["lam"]
    if not (0.0 < lam <= 1.0):
        return LambdaRecord("SEARCH FAILURE", sel["mode"], lam, None, attempts, "proposed λ outside (0, 1]")
    iv = certify(lam)
    st = certify_check(iv, target, eps)
    attempts.append(dict(lam=lam, status=st, interval=None if iv is None else iv.as_dict()))
    if st == "CERTIFIED":
        return LambdaRecord("CERTIFIED", sel["mode"], lam, iv, attempts, "", sel["bracket"])
    if st in ("UNAVAILABLE", "PRECISION FAILURE") or sel["mode"] == "hit":
        return LambdaRecord("UNCERTIFIED", sel["mode"], lam, iv, attempts, f"first certification {st}; no correction",
                            sel["bracket"])
    # one secant correction from (λ_cert, r_cert) and the bracket endpoint on the other side of the target
    (l1, r1), (l2, r2) = sel["bracket"]
    r_cert = iv.mean
    others = [(l1, r1), (l2, r2)]
    opposite = [o for o in others if (o[1] - target) * (r_cert - target) < 0]
    if opposite:
        l_o, r_o = opposite[0]
    else:
        l_o, r_o = min(others, key=lambda o: abs(o[1] - target))
    if r_o == r_cert:
        return LambdaRecord("SEARCH FAILURE", "bracket", lam, iv, attempts, "secant slope zero", sel["bracket"])
    lam2 = lam + (target - r_cert) * (l_o - lam) / (r_o - r_cert)
    if not (0.0 < lam2 <= 1.0):
        return LambdaRecord("SEARCH FAILURE", "bracket", lam2, iv, attempts, "corrected λ outside (0, 1]",
                            sel["bracket"])
    iv2 = certify(lam2)
    st2 = certify_check(iv2, target, eps)
    attempts.append(dict(lam=lam2, status=st2, interval=None if iv2 is None else iv2.as_dict()))
    if st2 == "CERTIFIED":
        return LambdaRecord("CERTIFIED", "bracket", lam2, iv2, attempts, "after one secant correction", sel["bracket"])
    return LambdaRecord("UNCERTIFIED", "bracket", lam2, iv2, attempts, f"re-certification {st2}", sel["bracket"])


# ----------------------------------------------------------------------------------------------
# gates (§7.3), recovery flags (§7.5), detection, rise (§7.6)
# ----------------------------------------------------------------------------------------------
def clopper_pearson(k: int, n: int, level: float = 0.95):
    """Exact one-sided bounds: (lower, upper) each at `level`."""
    if n <= 0:
        return np.nan, np.nan
    lower = 0.0 if k == 0 else float(beta_dist.ppf(1.0 - level, k, n - k + 1))
    upper = 1.0 if k == n else float(beta_dist.ppf(level, k + 1, n - k))
    return lower, upper


def gate_b(outcomes: dict, R: int = 100, max_bad: int = 1) -> dict:
    """(b) false POSITIVE under every graded setting: ≤ 1 of R attempted sets, UNAVAILABLE counted as POSITIVE."""
    per = {}
    ok = True
    for setting, outs in outcomes.items():
        bad = sum(1 for o in outs if o in (POSITIVE, UNAVAILABLE))
        attempted = len(outs)
        passed = attempted == R and bad <= max_bad
        per[setting] = dict(bad=bad, attempted=attempted, upper=clopper_pearson(bad, attempted)[1], passed=passed)
        ok = ok and passed
    return dict(passed=ok, settings=per)


def gate_c(outcomes_T1, R: int = 50, min_pos: int = 45) -> dict:
    """(c) power at T1: ≥ 45 of 50 sets POSITIVE, UNAVAILABLE counted as non-detection."""
    pos = sum(1 for o in outcomes_T1 if o == POSITIVE)
    attempted = len(outcomes_T1)
    return dict(passed=(attempted == R and pos >= min_pos), positive=pos, attempted=attempted,
                lower=clopper_pearson(pos, attempted)[0])


def gate_e(upper_bound_fields, R: int = 100, max_bounded: int = 4) -> dict:
    """(e) upper-bound error at E1: BOUNDED in ≤ 4 of 100 sets, UNAVAILABLE counted as BOUNDED."""
    b = sum(1 for o in upper_bound_fields if o in ("BOUNDED", UNAVAILABLE))
    attempted = len(upper_bound_fields)
    return dict(passed=(attempted == R and b <= max_bounded), bounded=b, attempted=attempted,
                upper=clopper_pearson(b, attempted)[1])


def completion_v2(outcomes: dict, max_frac: float = 0.10) -> dict:
    """V2: UNAVAILABLE set-level primaries ≤ 10% at every ATTEMPTED setting (uninstantiated settings absent)."""
    per, ok = {}, True
    for setting, outs in outcomes.items():
        n_un = sum(1 for o in outs if o == UNAVAILABLE)
        passed = len(outs) > 0 and n_un <= max_frac * len(outs)
        per[setting] = dict(unavailable=n_un, attempted=len(outs), passed=passed)
        ok = ok and passed
    return dict(passed=ok, settings=per)


def pooled_rate(flags) -> dict:
    """Pooled rate over attempted replicates with exact one-sided 95% bounds (§7.5 convention)."""
    k = int(sum(bool(f) for f in flags))
    n = len(flags)
    lo, hi = clopper_pearson(k, n)
    return dict(k=k, n=n, rate=(k / n if n else np.nan), lower=lo, upper=hi)


def recovery_flags(stats: dict, family: str) -> dict:
    """R1–R5 of §7.5 for one family from the S4b recovery battery.
    stats[family] = dict(
      point={(s_tau, 'fitted'): {config: dict(median_rel_bias, rmse, completion_ok)}},   # per configuration
      false_jitter={setting: [bool ŝ_τ > 20 per attempted replicate (UNAVAILABLE = True)]},
      false_detect={setting: [bool hull lower bound > 20 (UNAVAILABLE = True? no: UNAVAILABLE = non-detection
                     for R3? R3 counts 'fraction whose hull lower bound > 20' over the same replicates; an
                     UNAVAILABLE profile cannot exceed 20 → False)]},
      coverage={(s_tau, 'fitted'): [bool covers (UNAVAILABLE = False)]},
      r5=dict(detect=[bool lower bound > 20 (UNAVAILABLE = True)], cover=[bool covers 20 (UNAVAILABLE = False)]))
    Returns dict(flag = ADEQUATE | ADEQUATE-ZERO-ONLY | NOT ADEQUATE, rules = per-rule detail)."""
    S = stats[family]
    rules = {}
    # R1: the SAME ≥ 15 of 20 configurations pass at 40 and 80 ms with fitted s_g
    def passing(setting):
        return {c for c, d in S["point"][setting].items()
                if abs(d["median_rel_bias"]) <= 0.25 and d["rmse"] <= 0.5 * setting[0] and d["completion_ok"]}
    same = passing((40.0, "fitted")) & passing((80.0, "fitted"))
    rules["R1"] = dict(passed=len(same) >= 15, n_same=len(same), configs=sorted(same))
    # R2: false jitter ŝ_τ > 20 over all zero-jitter replicates
    fj = [f for setting in ((0.0, 0.0), (0.0, "fitted"), (0.0, 1.0), "O1", "O2") for f in S["false_jitter"][setting]]
    r2 = pooled_rate(fj)
    rules["R2"] = dict(passed=(r2["rate"] <= 0.10 and r2["upper"] <= 0.15), **r2)
    fd = [f for setting in ((0.0, 0.0), (0.0, "fitted"), (0.0, 1.0), "O1", "O2") for f in S["false_detect"][setting]]
    r3 = pooled_rate(fd)
    rules["R3"] = dict(passed=(r3["rate"] <= 0.05 and r3["upper"] <= 0.10), **r3)
    cov = {}
    ok4 = True
    for setting in ((40.0, "fitted"), (80.0, "fitted")):
        c = pooled_rate(S["coverage"][setting])
        c["passed"] = c["rate"] >= 0.90 and c["lower"] >= 0.87
        cov[str(setting)] = c
        ok4 = ok4 and c["passed"]
    rules["R4"] = dict(passed=ok4, settings=cov)
    d5 = pooled_rate(S["r5"]["detect"])
    c5 = pooled_rate(S["r5"]["cover"])
    rules["R5"] = dict(passed=(d5["rate"] <= 0.10 and d5["upper"] <= 0.15 and c5["rate"] >= 0.90 and c5["lower"] >= 0.87),
                       detect=d5, cover=c5)
    core = all(rules[r]["passed"] for r in ("R1", "R2", "R3", "R4"))
    if core and rules["R5"]["passed"]:
        flag = "ADEQUATE"
    elif core:
        flag = "ADEQUATE-ZERO-ONLY"
    else:
        flag = "NOT ADEQUATE"
    return dict(flag=flag, rules=rules)


def jitter_detected(profiles: dict, group_contrast: Interval, min_participants: int = 10) -> dict:
    """JITTER DETECTED (real data, per family): hull lower bound > 20 ms in ≥ 10 of 20 participants (UNAVAILABLE =
    non-detection) AND the group G3 − G2 (or B3 − B2) interval POSITIVE."""
    det = {p: bool(pr is not None and pr.lower_bound_exceeds) for p, pr in profiles.items()}
    n = sum(det.values())
    return dict(detected=(n >= min_participants and group_contrast.sign == POSITIVE), n_exceeding=n,
                group_sign=group_contrast.sign, per_participant=det)


def zero_only_participants(profiles: dict) -> list:
    """Under ADEQUATE-ZERO-ONLY: participants for whom the tested zero-jitter explanations may be called rejected
    = those whose real hull lower bound exceeds 20 ms (the R3-validated event). A hull merely excluding zero
    (lower bound in (0, 20]) licenses nothing."""
    return [p for p, pr in profiles.items() if pr is not None and pr.lower_bound_exceeds]


def newcombe(k1: int, n1: int, k2: int, n2: int, level: float = 0.95):
    """Newcombe (1998) method 10: Wilson-score hybrid interval for p1 − p2 of two INDEPENDENT proportions."""
    z = norm.ppf(0.5 + level / 2.0)

    def wilson(k, n):
        p = k / n
        den = 1.0 + z * z / n
        c = p + z * z / (2 * n)
        h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        return (c - h) / den, (c + h) / den

    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    lo = d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return float(d), float(lo), float(hi)


def rise(calls_W1, calls_W3) -> dict:
    """RISE in the inherited pipeline's call rate from W1 to W3 (or W4): Newcombe lower bound > 0."""
    d, lo, hi = newcombe(int(sum(calls_W3)), len(calls_W3), int(sum(calls_W1)), len(calls_W1))
    return dict(rise=lo > 0.0, diff=d, lo=lo, hi=hi)


# ----------------------------------------------------------------------------------------------
# §9 wording keys
# ----------------------------------------------------------------------------------------------
def claims(dec: Decision, recovery_G: str, detected_G: bool, rise_W3: bool, rise_W4: bool) -> dict:
    """Which §9 statements the fields license (keys only; the text lives in the paper)."""
    c = {}
    lic = dec.licence_primary
    c["primary_positive"] = lic and dec.primary.sign == POSITIVE
    c["primary_negative"] = lic and dec.primary.sign == NEGATIVE
    c["attenuation_premise"] = lic and dec.premise
    residual = dec.delta3_R6.sign
    c["not_robust"] = c["attenuation_premise"] and (residual in (NEGATIVE, UNRESOLVED) or dec.upper_bound == "BOUNDED")
    c["framing_result"] = c["primary_negative"] and dec.bridge_iii.sign != POSITIVE
    full = recovery_G == "ADEQUATE"
    c["latency_part"] = c["attenuation_premise"] and dec.D_tau.sign == POSITIVE and full and detected_G and rise_W3
    c["latency_most"] = c["latency_part"] and dec.D_tau_minus_D_scale.sign == POSITIVE
    c["scale_part"] = c["attenuation_premise"] and dec.D_scale.sign == POSITIVE and rise_W4
    c["latency_reduced_delta2_only"] = lic and dec.D_tau.sign == POSITIVE and not c["attenuation_premise"]
    c["unresolved_no_bound"] = lic and dec.primary.sign == UNRESOLVED and dec.upper_bound != "BOUNDED"
    c["not_licensed"] = not lic
    return c
