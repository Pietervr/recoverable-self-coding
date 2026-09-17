"""Blinded read of a sensitivity run: record the reading before the generator labels are revealed.

The verdicts themselves cannot be biased — analyze_dataset is a pure function of one dataset and its
seed, with no cross-dataset state — so this protocol does not protect the assay. It protects the
WRITE-UP. Knowing that a weak row is the alternative you hoped would work invites charitable prose,
emphasis on the settings that look good, and a denominator chosen after the fact. This makes that
impossible to do unnoticed, because the reading is committed before the key is opened.

    blind        summarise a run into opaque settings and seal the key
    reveal       print the mapping, after the reading is committed

    .venv/bin/python blind_read.py blind  --run sens600
    .venv/bin/python blind_read.py reveal --run sens600

Protocol, and the git history is the evidence for each step:
  1. `blind` writes blinded_counts.csv (opaque ids A..L, all four outcome counts, attempted denominators)
     and unblinding_key.json, prints the key's SHA-256, and does NOT print the mapping.
  2. Commit blinded_counts.csv AND the key file together. The key is committed sealed so that its
     content is fixed and timestamped before any reading exists; the point is not secrecy from the
     repository but that it cannot be altered afterwards.
  3. Write the reading from blinded_counts.csv alone and commit it. This is the step the blinding
     protects.
  4. `reveal` joins the key back. Any difference between the committed reading and the final write-up
     is visible in the history.

Opaque labels come from a hash of the setting name with a fixed salt, not from a seed chosen after
seeing the data, so the assignment could not have been searched for a flattering arrangement.

LIMIT, stated because it is real: this is partial blinding. The design is known — four generators at
three declared gains — so a monotone pattern across three rows of one generator may suggest which gain
is which. It removes the ability to write to a known label; it does not make the table unreadable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os

SALT = "t1-blind-read-2026"
OUTCOMES = ("mixture", "graded", "inconclusive", "unavailable")


def _label(setting: str) -> str:
    """A..Z from a salted hash of the setting, so the assignment is fixed before any data is seen."""
    h = hashlib.sha256(f"{SALT}:{setting}".encode()).hexdigest()
    return chr(ord("A") + int(h[:8], 16) % 26)


def _rows(path: str) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def blind(run_dir: str) -> None:
    src = os.path.join(run_dir, "power_D4.csv")
    if not os.path.exists(src):
        raise SystemExit(f"no power rows at {src}")
    rows = _rows(src)

    by: dict[str, dict] = {}
    for r in rows:
        # key on the declared target gain when the row carries it: the three gains of one generator are
        # distinct settings, and relying on their `scale` kwargs differing would silently merge them if
        # the extras were ever dropped (caught on synthetic rows before the real run existed)
        tg = (r.get("target_gain") or "").strip()
        setting = f"{r['generator']}|{tg}" if tg else f"{r['generator']}|{r['grid']}"
        b = by.setdefault(setting, {o: 0 for o in OUTCOMES} | {"attempted": 0})
        b["attempted"] += 1
        d = (r.get("selection_decision") or "").strip().lower()
        b[d if d in OUTCOMES else "unavailable"] += 1

    # a stable opaque id per setting; collisions get a numeric suffix, deterministically
    used: dict[str, int] = {}
    ids = {}
    for setting in sorted(by):
        base = _label(setting)
        used[base] = used.get(base, 0) + 1
        ids[setting] = base if used[base] == 1 else f"{base}{used[base]}"

    out_counts = os.path.join(run_dir, "blinded_counts.csv")
    with open(out_counts, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["setting_id", "attempted", *OUTCOMES, "detection_rate"])
        for setting in sorted(by, key=lambda s: ids[s]):
            b = by[setting]
            rate = b["mixture"] / b["attempted"] if b["attempted"] else float("nan")
            w.writerow([ids[setting], b["attempted"], *[b[o] for o in OUTCOMES], f"{rate:.4f}"])

    key_path = os.path.join(run_dir, "unblinding_key.json")
    with open(key_path, "w") as fh:
        json.dump({"salt": SALT, "map": {ids[s]: s for s in sorted(by)}}, fh, indent=1, sort_keys=True)
    digest = hashlib.sha256(open(key_path, "rb").read()).hexdigest()

    print(f"wrote {out_counts} ({len(by)} settings) and {key_path}")
    print(f"key SHA-256 {digest}")
    print("\nCommit both files, then write the reading from blinded_counts.csv alone and commit that")
    print("BEFORE running `reveal`. The mapping is deliberately not printed here.")


def reveal(run_dir: str) -> None:
    key_path = os.path.join(run_dir, "unblinding_key.json")
    key = json.load(open(key_path))
    digest = hashlib.sha256(open(key_path, "rb").read()).hexdigest()
    counts = {r["setting_id"]: r for r in _rows(os.path.join(run_dir, "blinded_counts.csv"))}
    print(f"key SHA-256 {digest}")
    print(f"\n{'id':<5}{'generator / grid':<34}{'attempted':>10}{'mixture':>9}{'detection':>11}")
    for sid in sorted(key["map"]):
        setting = key["map"][sid].replace("|", "  ")
        c = counts.get(sid, {})
        print(f"{sid:<5}{setting:<34}{c.get('attempted',''):>10}{c.get('mixture',''):>9}{c.get('detection_rate',''):>11}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["blind", "reveal"])
    ap.add_argument("--run", required=True, help="run name under sim_results/")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    run_dir = os.path.join(here, "sim_results", a.run)
    {"blind": blind, "reveal": reveal}[a.cmd](run_dir)


if __name__ == "__main__":
    main()
