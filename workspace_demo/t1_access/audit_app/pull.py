"""Pull the human readers' answers from D1: coverage per part, every answer, and the sheets' R1 columns.

    python3 pull.py --remote            # production
    python3 pull.py --local             # the local test rig

The links were forwarded to several people (owner, 18 Sept 2026), so a part can have many anonymous
readers: each visitor's browser holds a private session id, and an item may be read by nobody, one person
or several. Written to results/ (gitignored until the audit closes):

- `answers_<date>.csv`: every answer, one row per (item, session), with part, via and time;
- `<sheet>_R1_<date>.csv`: the committed sheet row for row, R1 filled by combining that item's human reads
  strictly: true = n if anyone said n, else ? if anyone said ?, else y; names / decisive / wrong / arguable
  = y if anyone said so; comments joined; plus R1_reads (sessions that answered it) and R1_via.
  For a clause marked decisive in advance, R1_decisive stays blank: the reader was not asked it.

The 'legacy-shared-link' session holds the answers saved before sessions existed (13 on part A, 18 Sept
22:05-22:11 UTC); they may be one person or several on the same link.
"""
import argparse
import csv
import json
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

import assign

HERE = Path(__file__).resolve().parent


def query(where, sql):
    out = subprocess.run(["wrangler", "d1", "execute", "raconteur-audit", where, "--json", "--command", sql],
                         cwd=HERE, check=True, capture_output=True, text=True).stdout
    return json.loads(out)[0]["results"]


def combine_clue(ms):
    ts = [m["t"] for m in ms]
    return {"R1_true": "n" if "n" in ts else "?" if "?" in ts else "y",
            "R1_names": "y" if any(m["nm"] == "y" for m in ms) else "n",
            "R1_decisive": "y" if any(m["d"] == "y" for m in ms) else "n"}


def combine_prop(ms):
    return {"R1_both_answers_correct": "n" if any(m["ok"] == "n" for m in ms) else "y",
            "R1_unambiguous": "n" if any(m["un"] == "n" for m in ms) else "y"}


def flagged(m):
    return (m.get("t", "y") != "y" or m.get("nm") == "y" or m.get("d") == "y"
            or m.get("ok", "y") != "y" or m.get("un", "y") != "y")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--local", action="store_true")
    g.add_argument("--remote", action="store_true")
    a = ap.parse_args()
    where = "--remote" if a.remote else "--local"

    parts = {r["token"]: r for r in query(where, "SELECT token, slot, items FROM readers")}
    rows = query(where, "SELECT token, sid, id, m, via, ts FROM answers ORDER BY ts")
    by_item = defaultdict(list)
    for x in rows:
        x["m"] = json.loads(x["m"])
        x["slot"] = parts[x["token"]]["slot"]
        by_item[x["id"]].append(x)

    print("part  sessions  answers  flagged  items read/dealt  unread  last answer")
    for tok, p in sorted(parts.items(), key=lambda kv: kv[1]["slot"]):
        ids = json.loads(p["items"])
        mine = [x for x in rows if x["token"] == tok]
        read = sum(1 for i in ids if by_item.get(i))
        print(f"  {p['slot']}   {len({x['sid'] for x in mine}):>6}  {len(mine):>7}  "
              f"{sum(flagged(x['m']) for x in mine):>7}  {read:>6}/{len(ids):<6}  {len(ids) - read:>6}  "
              f"{mine[-1]['ts'] if mine else '-'}")

    res = HERE / "results"
    res.mkdir(exist_ok=True)
    stamp = date.today().isoformat()
    with open(res / f"answers_{stamp}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "part", "session", "answer", "via", "ts"])
        for x in rows:
            w.writerow([x["id"], x["slot"], x["sid"], json.dumps(x["m"], ensure_ascii=False), x["via"], x["ts"]])

    for sheet, idf, kind in [(assign.CLUES, assign.clue_id, "clue"), (assign.PROPS, assign.prop_id, "prop")]:
        src = assign.read(sheet)
        cols = list(src[0].keys()) + ["R1_reads", "R1_via"]
        out = res / f"{sheet.stem}_R1_{stamp}.csv"
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in src:
                r = dict(r)
                hits = by_item.get(idf(r), [])
                r["R1_reads"] = len(hits)
                if hits:
                    ms = [h["m"] for h in hits]
                    r.update(combine_clue(ms) if kind == "clue" else combine_prop(ms))
                    if kind == "clue" and r["marked_decisive"].strip().lower() == "yes":
                        r["R1_decisive"] = ""
                    r["R1_comment"] = " | ".join(m["c"] for m in ms if m.get("c"))
                    r["R1_via"] = ",".join(sorted({h["via"] for h in hits}))
                w.writerow(r)
        print("wrote", out.relative_to(HERE))
    print("wrote", (res / f"answers_{stamp}.csv").relative_to(HERE))


if __name__ == "__main__":
    main()
