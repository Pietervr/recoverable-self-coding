"""Structural checks of a built bank (build_bank.py outputs) against §3, independent of the builder's code paths.

  V1 pairs: every split concept in exactly one pair; members from different families
  V2 competitors: same split, family neither the concept's nor its foil's
  V3 nesting: within (concept, carrier, draw, condition) the target slots at level k are a subset of those at k+1,
     every non-target slot keeps the same clause, k = 0 has no target clause, k = 8 has eight distinct ones
  V4 background: at k = 0 the eight clauses come from BACKGROUND concepts, one per family
  V5 C1 equals the draw-0 primary packet at the same k with each target clause replaced by the foil's clause of
     the same index; C2 keeps the target slots and fills every other slot from the competitor
  V6 conditions: noreport rows have the same slots, readout and marker positions as their active twin
  V7 counts per split, set and condition as §3 declares (D = 4 for CAL and PILOT, 8 for CONF)
  V8 CAL single: clue i in exactly one slot, the other seven from BACKGROUND concepts

    python3 workspace_demo/t1_access/stimuli/verify_bank.py <build dir>
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEVELS = [0, 1, 2, 3, 4, 6, 8]


def main(build: Path) -> int:
    bank = json.loads((HERE / "concepts.json").read_text())
    role = {c["id"]: c["role"] for c in bank["concepts"]}
    fam = {c["id"]: c["family"] for c in bank["concepts"]}
    pairs = json.loads((build / "pairs.json").read_text())
    comps = json.loads((build / "competitors.json").read_text())
    rows = list(csv.DictReader(open(build / "manifest.csv")))
    fails: list[str] = []

    def check(ok: bool, msg: str) -> None:
        if not ok:
            fails.append(msg)

    foil = {}
    for split, ps in pairs.items():
        members = [m for p in ps for m in p]
        check(sorted(members) == sorted(c for c, r in role.items() if r == split), f"V1 {split} membership")
        for a, b in ps:
            check(fam[a] != fam[b], f"V1 same-family pair {a} {b}")
            foil[a], foil[b] = b, a
    for c, comp in comps.items():
        check(role[comp] == role[c] and fam[comp] not in (fam[c], fam[foil[c]]), f"V2 {c} -> {comp}")

    def refs(row):
        return [tuple(s.rsplit("#", 1)) for s in row["slots"].split(";")]

    groups = defaultdict(dict)
    by_key = {}
    for r in rows:
        by_key[(r["split"], r["set"], r["condition"], r["concept"], r["carrier"], r["draw"], r["k"], r["clue"])] = r
        if r["set"] == "primary":
            groups[(r["concept"], r["carrier"], r["draw"], r["condition"])][int(r["k"])] = refs(r)
    for (c, ci, d, cond), lv in groups.items():
        check(sorted(lv) == LEVELS, f"V3 levels {c} {ci} {d} {cond}")
        tslots = {k: {j for j, (cc, _) in enumerate(s) if cc == c} for k, s in lv.items()}
        check(len(tslots[0]) == 0 and len(tslots[8]) == 8 and len(set(lv[8])) == 8, f"V3 endpoints {c} {ci} {d}")
        for k0, k1 in zip(LEVELS, LEVELS[1:]):
            check(tslots[k0] <= tslots[k1] and len(tslots[k1]) == k1, f"V3 nesting {c} {ci} {d} k{k0}->k{k1}")
            for j in range(8):
                if j not in tslots[k1]:
                    check(lv[k0][j] == lv[k1][j], f"V3 background moved {c} {ci} {d} slot {j}")
        bgc = [cc for cc, _ in lv[0]]
        check(all(role[x] == "BACKGROUND" for x in bgc) and sorted(fam[x] for x in bgc) == sorted(set(fam.values())),
              f"V4 background {c} {ci} {d}")

    counts = defaultdict(int)
    for r in rows:
        counts[(r["split"], r["set"], r["condition"])] += 1
        c = r["concept"]
        if r["set"] in ("C1", "C2"):
            prim = refs(by_key[(r["split"], "primary", r["condition"], c, r["carrier"], "0", r["k"], "")])
            got = refs(r)
            for j, (pc, pi) in enumerate(prim):
                if pc == c:
                    want = (foil[c], pi) if r["set"] == "C1" else (c, pi)
                    check(got[j] == want, f"V5 {r['trial_id']} slot {j}")
                elif r["set"] == "C1":
                    check(got[j] == (pc, pi), f"V5 C1 background {r['trial_id']} slot {j}")
                else:
                    check(got[j][0] == comps[c], f"V5 C2 competitor {r['trial_id']} slot {j}")
        if r["set"] == "single":
            got = refs(r)
            check(sum(1 for cc, i in got if cc == c and i == r["clue"]) == 1
                  and all(role[cc] == "BACKGROUND" for cc, _ in got if cc != c), f"V8 {r['trial_id']}")
        n_dec = int(r["n_decisive_inserted"])
        inserted = int(r["k"]) if r["set"] in ("primary", "C1", "C2") else 1
        check(0 <= n_dec <= min(2, inserted) and (r["set"] == "C2" or int(r["n_decisive_competitor"]) == 0),
              f"V9 decisive covariate {r['trial_id']}")
        if r["condition"] == "noreport":
            a = by_key[(r["split"], r["set"], "active", c, r["carrier"], r["draw"], r["k"], r["clue"])]
            check(a["slots"] == r["slots"] and a["readout_position"] == r["readout_position"]
                  and a["marker_positions"] == r["marker_positions"], f"V6 {r['trial_id']}")

    want = {("CAL", "primary"): 2688, ("PILOT", "primary"): 2688, ("CONF", "primary"): 21504,
            ("CONF", "C1"): 1152, ("CONF", "C2"): 1152}
    for (split, kind), n in want.items():
        for cond in ("active", "noreport"):
            check(counts[(split, kind, cond)] == n, f"V7 {split} {kind} {cond}: {counts[(split, kind, cond)]} != {n}")
    check(counts[("CAL", "single", "active")] == 1152, "V7 CAL single")
    for f in fails[:40]:
        print("FAIL", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} problems over {len(rows)} rows, {len(groups)} level groups")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
