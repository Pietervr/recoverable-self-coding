"""The §10 gain gate on known entries: the smoke's M3V entry, a wide-SE entry, a disagreeing one, a duplicate set."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import simulate as S

ok = dict(generator="M3V", target=0.01, scale=0.6027, gain=0.00988, gain_check=0.00823, gain_check_se=0.00069,
          calib_converged=True, check_converged=True, note="")
assert S.gain_gate(ok, 0.01) == "", S.gain_gate(ok, 0.01)
wide = dict(ok, gain_check_se=0.0025)
assert "SE" in S.gain_gate(wide, 0.01)
off = dict(ok, gain_check=0.0070)
assert "disagrees" in S.gain_gate(off, 0.01)
unconv = dict(ok, check_converged=False)
assert "check draw" in S.gain_gate(unconv, 0.01)
entries = [dict(ok, generator=n, target=t, gain=t, gain_check=0.9 * t, gain_check_se=0.1 * t) for n in S.M.FAMILY_X for t in S.GAINS]
assert S.validate_gain_entries(entries) == []
dup = entries[:-1] + [dict(entries[0])]            # 12 entries, one pair twice, one missing
p = S.validate_gain_entries(dup)
assert p and "pairs present" in p[0], p
bad = entries[:-1] + [dict(entries[-1], gain_check_se=0.01)]
p = S.validate_gain_entries(bad)
assert len(p) == 1 and "SE" in p[0], p
print("gate tests OK:", S.gain_gate(ok, 0.01) == "", "| wide:", S.gain_gate(wide, 0.01), "| off:", S.gain_gate(off, 0.01))
