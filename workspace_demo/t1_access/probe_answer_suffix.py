"""Development probe: does the answer suffix let the concept token win the argmax?

probe_answer_form.py (15 Sept) found that after the §12 suffix "Answer:" the top-1 token is
"\\n\\n" in 20 of 20 development packets that describe their concept with all eight clauses,
with the concept at rank 2-5. The argmax-correct rate of §6.3 would then sit near 0 at k = 8
and the §5 dose rule could not be met. This probe measures candidate suffixes on the same
development concepts (none from the eight bank families), as evidence for an amendment that
Entropy SI decides. Per suffix: how often the argmax is the concept in lower-case leading-space
form (the target-id convention) or in any case, its rank, its log-probability, and the top-1s.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/probe_answer_suffix.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture import LOGS, Server, load_tokenizer  # noqa: E402
from probe_answer_form import CARRIERS, DEV  # noqa: E402
from stimuli.packet import INSTRUCTION_A, SuffixError, build_ids, packet_text  # noqa: E402

SUFFIXES = [
    "\nAnswer:",
    "\nAnswer (one word):",
    "\nOne-word answer:",
    "\nIn one word, the answer is",
    "\nThe one-word answer is",
    "\nIn one word, this describes",
]
TOP_K = 200


def main() -> int:
    server = Server()
    info = server.info()
    tok = load_tokenizer(info)
    rows = []
    for suffix in SUFFIXES:
        for concept, clauses in DEV.items():
            lower = tok.encode(" " + concept, add_special_tokens=False)
            cap = tok.encode(" " + concept.capitalize(), add_special_tokens=False)
            target = lower[0] if len(lower) == 1 else None
            forms = {x[0] for x in (lower, cap) if len(x) == 1}
            for carrier in CARRIERS:
                prefix = packet_text(INSTRUCTION_A, carrier[0], clauses, carrier[1])
                try:
                    b = build_ids(tok, prefix, suffix)
                except SuffixError as e:
                    rows.append({"suffix": suffix, "concept": concept, "error": str(e)})
                    continue
                r = server.capture({"input_ids": b["ids"], "readout_positions": [b["readout_position"]],
                                    "capture_layers": [63], "request_token_ids": sorted(forms),
                                    "top_k": TOP_K})
                logit = {x["id"]: x["logit"] for x in r["requested"]}
                top = r["top_ids"]
                rows.append({
                    "suffix": suffix, "concept": concept, "carrier": carrier[0],
                    "argmax_is_target": top[0] == target,
                    "argmax_is_any_form": top[0] in forms,
                    "target_rank": top.index(target) + 1 if target in top else None,
                    "target_logprob": logit[target] - r["logsumexp"] if target is not None else None,
                    "top1": tok.decode([top[0]]),
                })
    summary = {}
    for suffix in SUFFIXES:
        rs = [r for r in rows if r["suffix"] == suffix and "error" not in r]
        summary[suffix] = {
            "n": len(rs),
            "errors": sum(1 for r in rows if r["suffix"] == suffix and "error" in r),
            "argmax_is_target": sum(r["argmax_is_target"] for r in rs),
            "argmax_is_any_form": sum(r["argmax_is_any_form"] for r in rs),
            "median_target_rank": statistics.median(r["target_rank"] or TOP_K + 1 for r in rs) if rs else None,
            "median_target_logprob": statistics.median(r["target_logprob"] for r in rs) if rs else None,
            "top1_counts": Counter(r["top1"] for r in rs).most_common(4),
        }
        s = summary[suffix]
        print(f"{suffix!r:<34} n={s['n']:>2} err={s['errors']} argmax=target {s['argmax_is_target']:>2} "
              f"any-form {s['argmax_is_any_form']:>2} | rank {s['median_target_rank']} | "
              f"lp {s['median_target_logprob']:.2f} | top1 {s['top1_counts']}")
    LOGS.mkdir(exist_ok=True)
    out = LOGS / f"answer_suffix_probe_{time.strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows, "server": info}, indent=1))
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
