#!/usr/bin/env python3
"""Independent exact checks for Proposition 1; no random draws or simulations.

Only two function definitions are extracted from rsc_simulation.py. Importing
that module would execute its full simulation campaign, which is not needed.
Run with the paper's NumPy environment, or /usr/local/bin/python3 on the Mac.
"""

import ast
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

import numpy as np


def positive_h2_gap(rho, scv):
    """Positive quadratic root for 1-sigma, independently of bisection."""
    a = 2 * rho - 1
    b = 2 * rho * (1 - rho) / (scv + 1)
    # Use the rationalized expression where direct subtraction cancels.
    root = (a * a + 4 * b).sqrt()
    return 2 * b / (root + a) if a >= 0 else (root - a) / 2


def main():
    source = Path(__file__).resolve().parents[1] / 'figures/rsc_simulation.py'
    parsed = ast.parse(source.read_text())
    names = {'gim1_root', 'exact_sr'}
    selected = [node for node in parsed.body
                if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in selected} == names
    definitions = ast.Module(body=selected, type_ignores=[])
    namespace = {'np': np, 'mu': 1.0}
    exec(compile(definitions, str(source), 'exec'), namespace)

    with localcontext() as ctx:
        ctx.prec = 70
        D = Decimal
        loads = np.linspace(0.30, 0.965, 28)
        max_sigma_error = 0.0
        max_sr_relative_error = 0.0
        for load in loads:
            rho = D(str(load))
            gap = positive_h2_gap(rho, D(4))
            sigma = namespace['gim1_root'](float(load))
            sr = namespace['exact_sr'](float(load), 'H2M1')
            max_sigma_error = max(max_sigma_error, abs(sigma - float(1 - gap)))
            exact_mean = float(rho / gap)
            max_sr_relative_error = max(max_sr_relative_error,
                                       abs(sr / exact_mean - 1))
        assert max_sigma_error < 5e-13
        assert max_sr_relative_error < 5e-11
        print(f'H2/M/1, all 28 existing loads: max root difference '
              f'{max_sigma_error:.3g}; max relative SR difference '
              f'{max_sr_relative_error:.3g}')
        for index in (8, 20, 26, 27):
            rho = D(str(loads[index]))
            gap = positive_h2_gap(rho, D(4))
            print(f'  CR={rho:.12f}, sigma={1-gap:.9f}, SR={rho/gap:.9f}')
        for rho in (D('0.99'), D('0.999'), D('0.9999')):
            gap = positive_h2_gap(rho, D(4))
            print(f'  H2 exact (1-CR) SR at CR={rho}: '
                  f'{(1-rho)*rho/gap:.12f} (limit 2.5)')

        # Equal first two arrival moments do not determine the GI/M/1 root.
        # Exp(mean 2) versus A=1/2 with probability 16/25, A=14/3 otherwise.
        a1, a2, p = D(1)/2, D(14)/3, D(16)/25
        mean_a = p*a1 + (1-p)*a2
        second_a = p*a1*a1 + (1-p)*a2*a2
        assert abs(mean_a - 2) < D('1e-65')
        assert abs(second_a - 8) < D('1e-65')
        def f(z):
            return p*(-(1-z)*a1).exp() + (1-p)*(-(1-z)*a2).exp() - z
        low, high = D(0), D('0.999')
        assert f(low) > 0 and f(high) < 0
        for _ in range(230):
            middle = (low + high) / 2
            if f(middle) > 0:
                low = middle
            else:
                high = middle
        sigma = (low + high) / 2
        assert abs(f(sigma)) < D('1e-65')
        print('Equal moments, mu=1, E[A]=2, Var(A)=4:')
        print('  exponential arrivals: sigma=0.5, SR=1')
        print(f'  two-point arrivals: sigma={sigma:.12f}, '
              f'SR={D("0.5")/(1-sigma):.12f}')

    # A separate lattice queue has an elementary birth-death invariant law.
    # A=1; S=0 with probability 3/4, S=2 with probability 1/4.
    # W has geometric ratio 1/3, as follows from adjacent-state balance.
    F = Fraction
    p_up, p_down = F(1, 4), F(3, 4)
    ratio = p_up / p_down
    mean_w = ratio / (1-ratio)
    idle_positive = (1-ratio) * p_down
    idle_variance = idle_positive * (1-idle_positive)
    rho, ca2, cs2 = F(1, 2), F(0), F(3)
    mean_from_counts = mean_w + F(1, 2)  # lambda=1
    mean_from_identity = rho + (ca2 + rho*rho*cs2-idle_variance)/(2*(1-rho))
    assert mean_from_counts == mean_from_identity == 1
    assert idle_positive == F(1, 2)
    assert 1-ratio == F(2, 3) != idle_positive
    print('Lattice/zero-service check: SR=1 from the geometric wait and '
          'from the identity; P(I>0)=1/2 but P(W=0)=2/3.')
    # D/D/1 has W=0 at every subcritical load and occupies service for rho
    # of each deterministic arrival interval. The equilibrium mean is rho.
    for rho in (F(1, 4), F(1, 2), F(99, 100)):
        assert rho + (0 + rho*rho*0 - 0)/(2*(1-rho)) == rho
    print('D/D/1 check: random-phase time occupancy is CR; no divergence.')


if __name__ == '__main__':
    main()
