"""Pull the human readers' marks from D1 into the audit sheets' R1 columns, and report progress.

    python3 pull.py --remote            # progress per reader, and results/*_R1.csv written
    python3 pull.py --local             # the same against the local test rig

The output copies the committed sheets row for row and fills R1_* from whichever human reader was
dealt that row (assignment.json), adding R1_reader, R1_via ('row' = clicked on the item, 'card' = the
"the other ... are fine" button) and R1_ts. For a clause marked decisive in advance, R1_decisive is left
blank: the reader was not asked it (CHECKLIST.md). The AI reader's R2_* columns are filled separately.
results/ is gitignored until the audit is closed, because it carries the readers' names.
"""
import argparse
import csv
import json
import subprocess
from datetime import date
from pathlib import Path

import assign

HERE = Path(__file__).resolve().parent


def query(where, sql):
    out = subprocess.run(["wrangler", "d1", "execute", "raconteur-audit", where, "--json", "--command", sql],
                         cwd=HERE, check=True, capture_output=True, text=True).stdout
    return json.loads(out)[0]["results"]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--local", action="store_true")
    g.add_argument("--remote", action="store_true")
    a = ap.parse_args()
    where = "--remote" if a.remote else "--local"

    readers = {r["slot"]: r for r in query(where, "SELECT slot, name, token, items FROM readers")}
    rows = query(where, "SELECT r.slot AS slot, m.id AS id, m.m AS m, m.via AS via, m.ts AS ts "
                        "FROM marks m JOIN readers r ON r.token = m.token")
    got = {}
    for x in rows:
        got[x["id"]] = (x["slot"], json.loads(x["m"]), x["via"], x["ts"])

    for s in sorted(readers):
        ids = json.loads(readers[s]["items"])
        mine = [i for i in ids if i in got and got[i][0] == s]
        flagged = 0
        for i in mine:
            m = got[i][1]
            flagged += (m.get("t", "y") != "y" or m.get("nm") == "y" or m.get("d") == "y"
                        or m.get("ok", "y") != "y" or m.get("un", "y") != "y")
        last = max((got[i][3] for i in mine), default="-")
        print(f"{s}  {readers[s]['name']:<20} {len(mine):>3}/{len(ids)} done, {flagged} flagged, last {last}")

    res = HERE / "results"
    res.mkdir(exist_ok=True)
    stamp = date.today().isoformat()
    for sheet, idf, kind in [(assign.CLUES, assign.clue_id, "clue"), (assign.PROPS, assign.prop_id, "prop")]:
        src = assign.read(sheet)
        cols = list(src[0].keys()) + ["R1_reader", "R1_via", "R1_ts"]
        out = res / f"{sheet.stem}_R1_{stamp}.csv"
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in src:
                r = dict(r)
                hit = got.get(idf(r))
                if hit:
                    s, m, via, ts = hit
                    r["R1_reader"] = f"{s}: {readers[s]['name']}"
                    r["R1_via"], r["R1_ts"] = via, ts
                    if kind == "clue":
                        r["R1_true"], r["R1_names"], r["R1_comment"] = m["t"], m["nm"], m["c"]
                        r["R1_decisive"] = "" if r["marked_decisive"].strip().lower() == "yes" else m["d"]
                    else:
                        r["R1_both_answers_correct"], r["R1_unambiguous"], r["R1_comment"] = m["ok"], m["un"], m["c"]
                w.writerow(r)
        print("wrote", out.relative_to(HERE))


if __name__ == "__main__":
    main()
