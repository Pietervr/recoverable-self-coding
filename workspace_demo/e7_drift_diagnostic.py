"""E7 post-hoc drift diagnostic (labeled as such — the pre-registered
statistics stand; this attributes, not replaces).

Question: is seed 2's control-arm tau_qvar = +0.834 explained by
measured service drift (host load rising through the arm -> true
utilization rising -> queue variance rising), the known nuisance the
calibration can only remove at arm START?

For every (seed, arm): mean service and implied true utilization
(mean service x the seed's calibrated lambda) in the first vs last
third of the arm's served tasks.

Run: python3 e7_drift_diagnostic.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
RHO_DESIGN = 0.45

recs = defaultdict(list)
cal = {}
for line in (HERE / "runs" / "e7_precursors.jsonl").read_text().splitlines():
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    if r.get("exp") != "e7":
        continue
    if r.get("calibration"):
        cal[r["seed"]] = r["s_med"]
    elif r.get("arm") in ("feedback", "control") and "service_s" in r:
        recs[(r["seed"], r["arm"])].append(r["service_s"])

print(f"{'seed/arm':16s} {'n':>4s} {'s_first3rd':>10s} {'s_last3rd':>10s} "
      f"{'rho_first':>9s} {'rho_last':>9s}")
for (seed, arm), ss in sorted(recs.items()):
    n = len(ss)
    third = max(1, n // 3)
    s_a = sum(ss[:third]) / third
    s_b = sum(ss[-third:]) / third
    lam = RHO_DESIGN / cal[seed]
    print(f"s{seed} {arm:12s} {n:4d} {s_a:10.1f} {s_b:10.1f} "
          f"{s_a * lam:9.2f} {s_b * lam:9.2f}")
