"""E10 attempt-4 service profile: quartiles of service_s per arm in
task-index thirds — was the capped phase actually served at the
uncached ~5.3 s anchor, or did the prefix cache keep it fast?

Run: python3 e10_service_profile.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

by_arm = defaultdict(list)
for line in (HERE / "runs" / "e10_llama.jsonl").read_text().splitlines():
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    if r.get("exp") == "e10" and "service_s" in r:
        by_arm[r["arm"]].append(r["service_s"])


def q(xs, f):
    return sorted(xs)[int(f * (len(xs) - 1))]


for arm, ss in by_arm.items():
    n = len(ss)
    t = n // 3
    for name, seg in (("first", ss[:t]), ("mid", ss[t:2 * t]),
                      ("last", ss[2 * t:])):
        print(f"{arm:9s} {name:6s} n={len(seg):3d} "
              f"q25={q(seg, .25):5.2f} med={q(seg, .5):5.2f} "
              f"q75={q(seg, .75):5.2f} q95={q(seg, .95):5.2f}")
