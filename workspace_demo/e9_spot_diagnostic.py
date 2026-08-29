"""E9 post-hoc coordinate diagnostic (labeled as such): the spot rig
hard-coded lambda = rho_nom / 25.2 s (the calibration amendment E7 got
was not propagated), so each spot's TRUE utilization is rho_nom *
s_measured / 25.2. Re-score each verdict against the committed map
(runs/e9_cusp_map.json) at the TRUE coordinates.

Run: python3 e9_spot_diagnostic.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
S_PLAN = 25.2
SPOTS = {
    "S1_up_td33": ("up", 0.65, 33, 0.8, "IGNITED"),
    "S2_up_td132": ("up", 0.65, 132, 0.8, "CALM"),
    "S3_down_quench02": ("measure", 0.55, 66, 0.2, "EXIT"),
    "S4_down_a08": ("measure", 0.55, 66, 0.8, "PINNED"),
}
MAP = json.loads((HERE / "runs" / "e9_cusp_map.json").read_text())

svc = defaultdict(list)
for line in (HERE / "runs" / "e9_spots.jsonl").read_text().splitlines():
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    if r.get("exp") == "e9" and "service_s" in r:
        svc[(r["spot"], r["phase"])].append(r["service_s"])

print(f"{'spot':20s} {'n':>4s} {'s_mean':>7s} {'rho_nom':>8s} "
      f"{'rho_true':>8s} {'boundary':>22s} {'verdict':>8s} {'on-map?':>8s}")
for spot, (phase, rho_nom, td, alpha, pred) in SPOTS.items():
    ss = svc.get((spot, phase), [])
    if not ss:
        print(f"{spot:20s}  (no records)")
        continue
    s_mean = sum(ss) / len(ss)
    rho_true = rho_nom * s_mean / S_PLAN
    key = f"td{td}_a{alpha}"
    m = MAP[key]
    if phase == "up":
        bound = m["l_up"]
        bname = f"l_up({key})={bound}"
        onmap = ("IGNITED" if rho_true >= bound else "CALM")
    else:
        bound = m["l_down"]
        bname = f"l_down({key})={bound}"
        onmap = ("PINNED" if bound is None or rho_true >= bound else "EXIT")
    print(f"{spot:20s} {len(ss):4d} {s_mean:7.1f} {rho_nom:8.2f} "
          f"{rho_true:8.2f} {bname:>22s} {pred:>8s} {onmap:>8s}")
