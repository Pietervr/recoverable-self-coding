"""Review-only exact binomial arithmetic; no data, fitting or simulation imports.

All boundary decisions use integer binomial probabilities for rational p/alpha.
Floating point is used only to display probabilities. This is not a T1 runner.
"""

import argparse
from fractions import Fraction
import json
from math import comb, sqrt
from pathlib import Path


COVERAGE = Fraction(9, 10)
FPR = Fraction(8, 125)
PASS_ALPHA = Fraction(1, 50)  # 0.02 at each of the two possible final looks
FAIL_ALPHA = Fraction(1, 2400)  # 0.04 / (12 settings * 2 endpoints * 4 looks)


def tails(n, p):
    """Return inclusive CDF/SF integer numerators and their common denominator."""
    a, b = p.numerator, p.denominator
    assert n >= 1 and 0 < a < b
    denominator = b ** n
    mass = (b - a) ** n
    cdf = []
    cumulative = 0
    for k in range(n + 1):
        cumulative += mass
        cdf.append(cumulative)
        if k < n:
            numerator = mass * (n - k) * a
            divisor = (k + 1) * (b - a)
            assert numerator % divisor == 0
            mass = numerator // divisor
    assert cdf[-1] == denominator
    sf = [denominator] + [denominator - cdf[k - 1] for k in range(1, n + 1)]
    assert all(cdf[k] < cdf[k + 1] for k in range(n))
    assert all(sf[k] > sf[k + 1] for k in range(n))
    return cdf, sf, denominator


def boundary(n, p, alpha, direction):
    cdf, sf, denominator = tails(n, p)
    values = cdf if direction == 'le' else sf
    qualifying = [k for k, value in enumerate(values)
                  if value * alpha.denominator <= denominator * alpha.numerator]
    if not qualifying:
        return None
    k = max(qualifying) if direction == 'le' else min(qualifying)
    adjacent = k + 1 if direction == 'le' else k - 1
    assert 0 <= adjacent <= n
    assert values[adjacent] * alpha.denominator > denominator * alpha.numerator
    return dict(count=k, direction=direction,
                tail_probability=float(Fraction(values[k], denominator)),
                adjacent_count=adjacent,
                adjacent_tail_probability=float(Fraction(values[adjacent], denominator)))


def probability(n, p, k, direction):
    cdf, sf, denominator = tails(n, p)
    values = cdf if direction == 'le' else sf
    return float(Fraction(values[k], denominator))


def row(n):
    return dict(n=n,
                coverage_fail=boundary(n, COVERAGE, FAIL_ALPHA, 'le'),
                fpr_fail=boundary(n, FPR, FAIL_ALPHA, 'ge'),
                coverage_pass=boundary(n, COVERAGE, PASS_ALPHA, 'ge'),
                fpr_pass=boundary(n, FPR, PASS_ALPHA, 'le'))


def checks():
    # Independent direct-combination calculation and symmetry, plus cutoff checks.
    for n in (1, 2, 7, 20):
        for p in (COVERAGE, FPR, Fraction(1, 2)):
            cdf, sf, denominator = tails(n, p)
            direct = [comb(n, k) * p.numerator ** k *
                      (p.denominator - p.numerator) ** (n - k)
                      for k in range(n + 1)]
            assert [cdf[k] - (cdf[k - 1] if k else 0)
                    for k in range(n + 1)] == direct
            reflected_cdf, _, reflected_denominator = tails(n, 1 - p)
            assert denominator == reflected_denominator
            assert sf == list(reversed(reflected_cdf))
    assert 2 * PASS_ALPHA == Fraction(1, 25)
    assert 12 * 2 * 4 * FAIL_ALPHA == Fraction(1, 25)


def report(extra_n):
    checks()
    rows = [row(n) for n in sorted(set((100, 200, 400, 1000) + tuple(extra_n)))]
    power = []
    for n in (400, 1000):
        cutoff = boundary(n, COVERAGE, PASS_ALPHA, 'ge')['count']
        fpr_cutoff = boundary(n, FPR, PASS_ALPHA, 'le')['count']
        power.append(dict(n=n, coverage_pass_count=cutoff,
                          fpr_pass_count=fpr_cutoff,
                          fpr_pass_probability_at_true_005=probability(n, Fraction(1, 20), fpr_cutoff, 'le'),
                          known_target_pass_probability={str(p): probability(n, p, cutoff, 'ge')
                              for p in (Fraction(90, 100), Fraction(91, 100),
                                        Fraction(92, 100), Fraction(94, 100), Fraction(95, 100))}))
    bootstrap = [dict(B=b, expected_draws_below_true_025_quantile=0.025 * b,
                      probability_scale_mcse=sqrt(0.025 * 0.975 / b),
                      probability_no_draw_below_true_025_quantile=float(Fraction(39, 40) ** b))
                 for b in (50, 100, 200)]
    return dict(scope='Deterministic review arithmetic only; proposed rules, not an adopted protocol.',
                thresholds=dict(coverage=str(COVERAGE), fpr=str(FPR)),
                error_budgets=dict(pass_alpha_per_final_look=str(PASS_ALPHA),
                                  fail_alpha_per_endpoint_setting_look=str(FAIL_ALPHA),
                                  reference_simultaneous_error='1/100',
                                  settings=12, endpoints=2,
                                  failure_looks=[100, 200, 400, 1000], pass_looks=[400, 1000]),
                interpretation='Pass columns are eligible only at the 400/1000 final looks. '
                               'Coverage uses containment for pass and intersection for failure. '
                               'With unavailable intervals its binomial n is the usable count; '
                               'FPR n is all attempted datasets. No pass with fewer than 400 usable intervals.',
                boundaries=rows, fixed_look_power_known_target=power,
                bootstrap_quantile_arithmetic=bootstrap,
                chpc_break_even=dict(cluster_hours=19800,
                    maximum_chpc_hours_per_historical_mac_equivalent=100000 / 19800,
                    policy_A_historical_loaded_pc_ratio=56647.375 / 5766.015625,
                    two_null_refit_hours=41000,
                    maximum_chpc_ratio_two_null_refit=100000 / 41000),
                checks='Exact mass sums, integer recurrence divisibility, monotone tails, '
                       'direct-combination agreement, symmetry, error budgets and adjacent cutoffs passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--n', type=int, action='append', default=[],
                        help='Additional usable denominator; does not add an authorized look.')
    args = parser.parse_args()
    result = json.dumps(report(args.n), indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')
