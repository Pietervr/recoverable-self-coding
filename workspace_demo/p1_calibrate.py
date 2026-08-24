"""P1 — instrument calibration.

1. Lens gate (n=1000).
2. Filter the probe-swap battery to single-token intermediates.
3. Baseline pass (no load): per item, slice -> certification record;
   generate -> graded answer. Summaries: certification rate, accuracy,
   cert-vs-correct contingency.
4. Optional causal spot-check (--validate N): for N certified items, a
   single-layer swap intermediate->swap_to at the item's best layer; count
   answer flips to swap_answer. (Single-layer is weaker than the paper's
   band-wide swap: treat the flip rate as a lower bound.)

Run:  python3 p1_calibrate.py [--port 8765] [--top-k 10] [--validate 10]
Logs: runs/p1_calibrate.jsonl (+ summary JSON printed and saved)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness.battery import filter_single_token, graded, load_probe_swap
from harness.certify import band_layers, certified
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--validate", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "p1_calibrate.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    lens = c.require_n1000()
    print("lens ok:", {k: lens[k] for k in lens if k in ("n_prompts", "d_model", "path")})

    items = load_probe_swap()
    kept, dropped = filter_single_token(c, items)
    print(f"battery: {len(kept)} usable / {len(items)}; dropped: {dropped}")

    log = RunLog(args.out)
    done = log.done_keys("phase", "item")

    band: list[int] | None = None
    n_cert = n_corr = n_both = n_run = 0
    for it in kept:
        if ("baseline", it["name"]) in done:
            continue
        sl = c.slice(it["prompt"], top_n=args.top_k)
        if band is None:
            band = band_layers(sl["layers"])
            print(f"workspace band (fallback frac): {band[0]}..{band[-1]} of {sl['layers'][-1]}")
        cert = certified(sl, [it["intermediate"]], band, args.top_k)
        text = c.generate(it["prompt"], max_tokens=8)
        ok = graded(it, text)
        n_run += 1
        n_cert += cert["certified"]
        n_corr += ok
        n_both += cert["certified"] and ok
        log.write(
            {
                "phase": "baseline",
                "item": it["name"],
                "certified": cert["certified"],
                "best_rank": cert["best_rank"],
                "best_layer": cert["best_layer"],
                "n_hits": cert["n_hits"],
                "correct": ok,
                "text": text[:60],
            }
        )
        print(
            f"  {it['name']:>28}  cert={int(cert['certified'])} "
            f"rank={cert['best_rank']} correct={int(ok)}  {text[:32]!r}"
        )

    recs = [r for r in log.records() if r.get("phase") == "baseline"]
    N = len(recs)
    if N:
        cert_rate = sum(r["certified"] for r in recs) / N
        acc = sum(r["correct"] for r in recs) / N
        both = sum(r["certified"] and r["correct"] for r in recs) / N
        summary = {
            "n": N,
            "cert_rate": round(cert_rate, 3),
            "accuracy": round(acc, 3),
            "cert_and_correct": round(both, 3),
            "band": [band[0], band[-1]] if band else None,
            "top_k": args.top_k,
        }
        print("BASELINE SUMMARY:", json.dumps(summary))
        (HERE / "runs" / "p1_summary.json").write_text(json.dumps(summary, indent=1))

    if args.validate:
        vdone = log.done_keys("phase", "item")
        cand = [
            r["item"] for r in recs if r["certified"] and r["correct"]
        ][: args.validate]
        by_name = {it["name"]: it for it in kept}
        flips = tried = 0
        for name in cand:
            if ("validate", name) in vdone:
                continue
            it = by_name[name]
            base = [r for r in recs if r["item"] == name][-1]
            layer = base.get("best_layer")
            if layer is None:
                continue
            r = c.intervene(
                it["prompt"], layer=layer, mode="swap",
                token=it["intermediate"], target=it["swap_to"],
                alpha=2.0, max_tokens=8,
            )
            # /api/intervene returns {baseline:{text}, intervened:{text}, ...}
            text = r.get("intervened", {}).get("text", "")
            base_text = r.get("baseline", {}).get("text", "")
            flip = it["swap_answer"].strip().lower() in text[:48].strip().lower()
            tried += 1
            flips += flip
            log.write({"phase": "validate", "item": name, "layer": layer,
                       "flip": flip, "text": text[:60], "base_text": base_text[:60]})
            print(f"  swap {it['intermediate']}->{it['swap_to']} @L{layer}: "
                  f"flip={int(flip)}  base={base_text[:24]!r} int={text[:24]!r}")
        if tried:
            print(f"VALIDATION: {flips}/{tried} single-layer swaps flipped the answer")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
