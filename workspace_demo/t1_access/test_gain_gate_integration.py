"""Mocked integration checks for the gain gate: the wrapper keeps the gate fields; the monitor holds power."""
import io, json, os, sys, contextlib, tempfile
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import numpy as np
import pandas as pd
import simulate as S
import spotcheck as C
import analyze as A
CFG = A.Config()

# 1. _one_gain preserves everything calibrate_gain returns
def fake_calibrate(name, target, kwargs, seed=0, cfg=None, D=4):
    return dict(scale=0.5, gain=target * 1.02, gain_check=target * 0.95, gain_check_se=0.05 * target,
                check_best="M2K", check_converged=True, calib_converged=True, trace=[{"scale": 0.5}], note="")
S.calibrate_gain = fake_calibrate
entries = S.calibrate_all_gains(seed=1, cfg=CFG, n_jobs=1, D=4)["entries"]
assert len(entries) == 12 and all(e["calib_converged"] and e["check_converged"] for e in entries)
assert S.validate_gain_entries(entries) == []
def fake_calibrate_unconv(name, target, kwargs, seed=0, cfg=None, D=4):
    r = fake_calibrate(name, target, kwargs); r["check_converged"] = False; return r
S.calibrate_gain = fake_calibrate_unconv
try:
    S.calibrate_all_gains(seed=1, cfg=CFG, n_jobs=1, D=4); raise SystemExit("unconverged check was accepted")
except RuntimeError as e:
    assert "check draw" in str(e)
print("wrapper keeps the gate fields and calibrate_all_gains refuses an unconverged check: OK")

# 2. the monitor holds power statistics unless the gain file passes
row = dict(generator="M3H", family="X", grid="{}", rep=0, D=4, n_layers=1, code_hash="abcdefabcdef", failed=0,
           convergence=1.0, inner_convergence=1.0, selection_decision="mixture", selection_ws_point=0.01,
           selection_ws_lo=0.005, selection_ws_hi=0.015, selection_ws_se=0.002, fit_seconds=1.0)
df = pd.DataFrame([row, dict(row, rep=1)])
found = {"power_D4": (df, [])}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    C.report(found, brief=True, gain_ok={})
assert "HELD" in buf.getvalue() and "mixture rate" not in buf.getvalue(), buf.getvalue()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    C.report(found, brief=True, gain_ok={4: False})
assert "HELD" in buf.getvalue()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    C.report(found, brief=True, gain_ok={4: True})
assert "mixture rate" in buf.getvalue() and "HELD" not in buf.getvalue(), buf.getvalue()
# check_gain_file on a failing file returns problems (so gain_ok is False)
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "gain_calibration_D4.json")
    bad = [dict(generator=n, kwargs={}, target=t, D=4, scale=0.5, gain=t, gain_check=t, gain_check_se=0.5 * t,
                calib_converged=True, check_converged=True, note="") for n in S.M.FAMILY_X for t in S.GAINS]
    json.dump(dict(entries=bad), open(p, "w"))
    with contextlib.redirect_stdout(io.StringIO()):
        problems = C.check_gain_file(p)
    assert problems and all("SE" in x for x in problems)
print("monitor holds power until the gain file passes: OK")
