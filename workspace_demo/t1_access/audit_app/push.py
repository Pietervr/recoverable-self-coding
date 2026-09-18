"""Load the audit items and the readers into D1 (audit.raconteur-road.com), and print the invite links.

    python3 push.py --local                  # local rig (wrangler pages dev), for testing
    python3 push.py --remote                 # production
    python3 push.py --remote --name A=Anna   # set a reader's display name (repeatable), then push
    python3 push.py --links                  # print the four links, push nothing

Tokens are created once per slot and kept in readers.local.json (gitignored): the token in the link
IS the part's identity (several people may share it; each visitor gets a private session in the
page), so never commit it. Re-pushing replaces items and part rows but never touches saved answers. Item text comes from the committed audit sheets through assign.py's ids.
"""
import argparse
import csv
import json
import secrets
import subprocess
from pathlib import Path

import assign

HERE = Path(__file__).resolve().parent
READERS = HERE / "readers.local.json"
BASE = "https://audit.raconteur-road.com/r/"


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def load_readers(names):
    data = json.loads(READERS.read_text()) if READERS.exists() else {}
    for s in assign.SLOTS:
        data.setdefault(s, {"token": secrets.token_urlsafe(18), "name": f"Reader {s}"})
    for s, n in names.items():
        data[s]["name"] = n
    READERS.write_text(json.dumps(data, indent=1) + "\n")
    READERS.chmod(0o600)
    return data


def item_rows():
    out = []
    for r in assign.read(assign.CLUES):
        fam, word = r["concept"].split("/", 1)
        body = {"key": r["concept"], "family": fam, "concept": word, "index": int(r["index"]),
                "clause": r["clause"], "allowed": r["marked_decisive"].strip().lower() == "yes",
                "note": r["drafter_note"].strip()}
        out.append((assign.clue_id(r), "clue", body))
    for r in assign.read(assign.PROPS):
        body = {"pid": r["id"], "concept": r["concept"].split("/", 1)[1], "foil": r["foil"].split("/", 1)[1],
                "question": r["question"], "a_concept": r["answer_for_concept"], "a_foil": r["answer_for_foil"],
                "note": r["drafter_note"].strip()}
        out.append((assign.prop_id(r), "prop", body))
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--local", action="store_true")
    g.add_argument("--remote", action="store_true")
    g.add_argument("--links", action="store_true")
    ap.add_argument("--name", action="append", default=[], help="SLOT=Display name")
    a = ap.parse_args()

    names = dict(x.split("=", 1) for x in a.name)
    assert set(names) <= set(assign.SLOTS), names
    readers = load_readers(names)
    if a.links:
        for s in assign.SLOTS:
            print(f"{s}  {readers[s]['name']:<20} {BASE}{readers[s]['token']}")
        return

    plan = json.loads((HERE / "assignment.json").read_text())
    rows = item_rows()
    known = {i for i, _, _ in rows}
    # The first design kept one set of marks per link; the links were then forwarded to several people, so
    # those marks are copied (once, idempotently) into answers under one 'legacy' session per link.
    stmts = [(HERE / "schema.sql").read_text(),
             "INSERT OR IGNORE INTO answers (token, sid, id, m, via, ts) "
             "SELECT token, 'legacy-shared-link', id, m, via, ts FROM marks;",
             "DELETE FROM items;"]
    for i, kind, body in rows:
        stmts.append(f"INSERT INTO items (id, kind, body) VALUES ({q(i)}, {q(kind)}, {q(json.dumps(body, ensure_ascii=False))});")
    for s in assign.SLOTS:
        ids = plan["slots"][s]["items"]
        assert set(ids) <= known, f"slot {s} has ids not in the sheets"
        stmts.append(
            "INSERT INTO readers (token, slot, name, items, disabled, updated) VALUES "
            f"({q(readers[s]['token'])}, {q(s)}, {q(readers[s]['name'])}, {q(json.dumps(ids))}, 0, datetime('now')) "
            "ON CONFLICT (token) DO UPDATE SET slot = excluded.slot, name = excluded.name, items = excluded.items, "
            "updated = excluded.updated;")
    build = HERE / "build"
    build.mkdir(exist_ok=True)
    sql = build / "seed.sql"
    sql.write_text("\n".join(stmts) + "\n")
    where = "--remote" if a.remote else "--local"
    subprocess.run(["wrangler", "d1", "execute", "raconteur-audit", where, "--file", str(sql), "--yes"],
                   cwd=HERE, check=True)
    print(f"pushed {len(rows)} items and {len(assign.SLOTS)} readers ({where})")


if __name__ == "__main__":
    main()
