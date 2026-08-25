"""E4 mode forensics — what does repair junk actually do to the model?

Trisects the collapse mechanism with three same-size windows:
  clean    : plain "Fact: X is <correct>." lines
  fmt      : repair-format lines carrying CORRECT answers
  poison   : repair-format lines carrying WRONG answers (swap_answer)
Measures exo two-hop accuracy (max_tokens=8, mirroring E4) under each, and
prints a few LONG generations (max_tokens=40) under `poison` so the failure
text itself is inspectable (think-block contagion vs asserted wrong facts).

  fmt ~ clean, poison low  -> falsity is the poison (epistemic corruption)
  fmt low too              -> the repair FORMAT degrades (mode contagion)

Run:  python3 e4_forensics.py     Logs: runs/e4_forensics.json
"""

from __future__ import annotations

import json
from pathlib import Path

from harness.battery import filter_single_token, graded, load_probe_swap
from harness.client import JLensClient

HERE = Path(__file__).parent
WINDOW_CHARS = 11000
N_PROBE = 20


def clause_of(item: dict) -> str:
    p = item["prompt"].strip()
    body = p[5:].strip() if p.lower().startswith("fact:") else p
    return body[0].lower() + body[1:]


def build_window(items, mode: str) -> str:
    out = ""
    i = 0
    while len(out) < WINDOW_CHARS:
        it = items[i % len(items)]
        i += 1
        if mode == "clean":
            out += it["prompt"].rstrip() + " " + it["answer"] + ".\n"
        else:
            ans = it["answer"] if mode == "fmt" else it["swap_answer"]
            cl = clause_of(it)
            if cl.endswith(" is"):
                cl = cl[:-3]
            out += (f"Fact check: it was recorded that {cl} is {ans}. "
                    f"That may be wrong. In fact, {cl} is {ans}.\n")
    return out[-WINDOW_CHARS:]


def real_main() -> int:
    c = JLensClient()
    c.require_n1000()
    items, _ = filter_single_token(c, load_probe_swap())
    win_items = items[:50]
    probe_items = items[50:50 + N_PROBE]
    if len(probe_items) < N_PROBE:
        probe_items = items[-N_PROBE:]

    results = {}
    for mode in ("clean", "fmt", "poison"):
        win = build_window(win_items, mode)
        ok = 0
        for it in probe_items:
            text = c.generate(win + "\n" + it["prompt"].rstrip(), max_tokens=8)
            ok += graded(it, text)
        acc = ok / len(probe_items)
        results[mode] = {"accuracy": round(acc, 3), "n": len(probe_items)}
        print(f"window={mode:>6}: exo accuracy {acc:.2f} ({ok}/{len(probe_items)})")

    print("\nLONG generations under the poison window (inspect the text):")
    win = build_window(win_items, "poison")
    longs = []
    for it in probe_items[:5]:
        text = c.generate(win + "\n" + it["prompt"].rstrip(), max_tokens=40)
        longs.append({"item": it["name"], "text": text[:200]})
        print(f"  {it['name']}: {text[:120]!r}")
    results["long_poison_samples"] = longs
    (HERE / "runs" / "e4_forensics.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(real_main())
