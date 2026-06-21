#!/usr/bin/env python3
"""Numerically verify the effective-capacity derivation against the simulation:
  (1) theta_star measured from the sojourn tail == mu(1-CR) for M/M/1;
  (2) SR = (1-Pc)/Pc == e^{-theta* Dt}/(1-e^{-theta* Dt})  [Eq. srtheta], across the whole CR range;
  (3) SR*(1-CR) -> (c_a^2+c_s^2)/(2 mu Dt) at the boundary, for several GI/G/1 processes.
"""
import numpy as np
rng = np.random.default_rng(3)
mu, Dt = 1.0, 4.0


def lindley_sojourn(inter, serv):
    n = len(serv); d = np.empty(n); d[0] = 0.0; d[1:] = serv[:-1] - inter[1:]
    P = np.cumsum(d); wait = P - np.minimum.accumulate(P)
    return wait + serv


def gamma(n, mean, cv2):
    return np.full(n, mean) if cv2 <= 1e-9 else rng.gamma(1.0 / cv2, mean * cv2, n)


def run(rho, ca2, cs2, n=400000):
    soj = lindley_sojourn(gamma(n, 1.0 / (rho * mu), ca2), gamma(n, 1.0 / mu, cs2))[2000:]
    Pc = float((soj <= Dt).mean())
    SR = (1 - Pc) / Pc
    theta_meas = -np.log(max(1 - Pc, 1e-12)) / Dt          # from P(T>Dt)=e^{-theta Dt}
    SR_from_theta = np.exp(-theta_meas * Dt) / (1 - np.exp(-theta_meas * Dt))
    return Pc, SR, theta_meas, SR_from_theta


print("(1)+(2) M/M/1 (c_a^2=c_s^2=1): theta* predicted = 1-CR ; SR vs SR_from_theta")
print(" CR    Pc     SR       theta_meas  theta_pred=1-CR   SR_from_theta")
for rho in [0.3, 0.5, 0.7, 0.85, 0.95]:
    Pc, SR, th, srth = run(rho, 1.0, 1.0)
    print(f"{rho:4.2f}  {Pc:5.3f}  {SR:7.3f}   {th:8.4f}    {1-rho:8.4f}        {srth:7.3f}")

print("\n(3) boundary prefactor SR*(1-CR) -> (c_a^2+c_s^2)/(2*Dt) = (c_a^2+c_s^2)/8, at CR=0.97")
for name, ca2, cs2 in [("M/M/1", 1, 1), ("M/D/1", 1, 0), ("D/M/1", 0, 1), ("bursty M/G/1", 1, 4)]:
    Pc, SR, th, _ = run(0.97, ca2, cs2)
    print(f"  {name:14s} SR*(1-CR)={SR*(1-0.97):6.3f}   predicted {(ca2+cs2)/(2*Dt):6.3f}")
