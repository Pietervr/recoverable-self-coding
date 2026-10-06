"""Operating characteristics of row 22's predeclared target rules (chpc/row22_target.py), by simulation of the summary alone:
how often a CLEAN bank (normal values, n = 408, SD 0.36) is ruled UNRESOLVED by each check, and how often banks with heavier
tails or one extreme dataset are. No fit; seconds on one core. Run: python reviews/2026-10-06_row22_target_rule_operating_characteristics.py"""
import os, sys, importlib.util
import numpy as np
T1 = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("row22_target", os.path.join(T1, "chpc", "row22_target.py"))
TG = importlib.util.module_from_spec(spec); spec.loader.exec_module(TG)
R = TG.rules({"target": {}})
N, SD, SIMS = 408, 0.36, 2000
reps = list(range(N))
rng = np.random.default_rng(20261006)
cases = {
    "normal": lambda: rng.normal(-0.9, SD, N),
    "t(5) scaled to SD 0.36": lambda: -0.9 + SD * rng.standard_t(5, N) / np.sqrt(5 / 3),
    "t(3) scaled to SD 0.36": lambda: -0.9 + SD * rng.standard_t(3, N) / np.sqrt(3.0),
    "normal + one dataset at -55": lambda: np.r_[rng.normal(-0.9, SD, N - 1), -55.0],
    "normal + one dataset at -2650": lambda: np.r_[rng.normal(-0.9, SD, N - 1), -2650.0],
}
print(f"n = {N}, {SIMS} simulated banks per case; rules {R}")
for name, draw in cases.items():
    fails = {"tail": 0, "precision": 0, "stability": 0, "unusable": 0, "any": 0}
    for _ in range(SIMS):
        s = TG.summarise(list(draw()), reps, R, N)
        rs = " ".join(s.get("reasons", []))
        for k in ("tail", "precision", "stability"):
            fails[k] += k in rs
        fails["unusable"] += "unusable" in rs
        fails["any"] += s["status"] != "RESOLVED"
    print(f"  {name:32s} " + "  ".join(f"{k} {v / SIMS:.3f}" for k, v in fails.items()))
