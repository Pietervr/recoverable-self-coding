"""Development probe: R3 correctness as argmax over a closed answer set, by dose, per suffix.

probe_answer_form.py and probe_answer_suffix.py (15 Sept) found that no suffix tried puts the
concept at the open-vocabulary argmax: the model emits formatting first ("\\n\\n" or ":"), even
with all eight clauses about the concept. This probe measures, on development concepts only (no
bank concept, no bank token in the answer set), whether a closed-set reading would behave as §5
needs: correct = the concept's lower-case leading-space id has the highest logit among the
answer set's ids. Dose k in {0, 1, 2, 4, 8}: k clauses of the target, the other slots one clause
each from other development concepts (a competition packet, not the §3 background channel).

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/probe_answer_closed_set.py
"""

from __future__ import annotations

import json
import random
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture import LOGS, Server, load_tokenizer  # noqa: E402
from probe_answer_form import CARRIERS, DEV  # noqa: E402
from stimuli.packet import INSTRUCTION_A, build_ids, packet_text  # noqa: E402

SUFFIXES = ["\nAnswer:", "\nAnswer (one word):", "\nIn one word, the answer is"]
LEVELS = [0, 1, 2, 4, 8]
# Answer-set fillers: common nouns in no bank family and not in any bank candidate list.
FILLERS = ("table sofa desk shelf pillow blanket towel soap bottle jar plate bowl spoon key coin ring "
           "watch wallet bag box basket window roof wall fence garden tree flower grass leaf river "
           "mountain beach cloud rain snow moon star book map letter phone radio camera computer "
           "television ball kite doll bridge tower castle church school hospital library").split()


def main() -> int:
    server = Server()
    info = server.info()
    tok = load_tokenizer(info)
    bank = json.loads((HERE / "stimuli" / "concepts.json").read_text())
    bank_words = {f.lower() for c in bank["concepts"] for f in c["surface_forms"]}
    answer_words = [w for w in list(DEV) + FILLERS if w not in bank_words]
    answer_ids = {}
    for w in answer_words:
        enc = tok.encode(" " + w, add_special_tokens=False)
        if len(enc) == 1:
            answer_ids[w] = enc[0]
    missing = [w for w in DEV if w not in answer_ids]
    if missing:
        raise SystemExit(f"development concepts not single-token: {missing}")
    rng = random.Random(20260915)
    rows = []
    concepts = list(DEV)
    for suffix in SUFFIXES:
        for concept in concepts:
            others = [c for c in concepts if c != concept]
            for ci, carrier in enumerate(CARRIERS):
                order = rng.sample(range(8), 8)
                fill = rng.sample(others, 8)
                for k in LEVELS:
                    slots = [DEV[concept][order[j]] if j < k else DEV[fill[j]][order[j]] for j in range(8)]
                    b = build_ids(tok, packet_text(INSTRUCTION_A, carrier[0], slots, carrier[1]), suffix)
                    r = server.capture({"input_ids": b["ids"], "readout_positions": [b["readout_position"]],
                                        "capture_layers": [63], "request_token_ids": sorted(answer_ids.values()),
                                        "top_k": 5})
                    logit = {x["id"]: x["logit"] for x in r["requested"]}
                    tid = answer_ids[concept]
                    best_other = max((v, w) for w, i in answer_ids.items() if w != concept for v in [logit[i]])
                    closed_best = max(answer_ids, key=lambda w: logit[answer_ids[w]])
                    rows.append({"suffix": suffix, "concept": concept, "carrier": ci, "k": k,
                                 "closed_correct": closed_best == concept, "closed_best": closed_best,
                                 "closed_margin": logit[tid] - best_other[0],
                                 "open_correct": r["top_ids"][0] == tid,
                                 "target_logprob": logit[tid] - r["logsumexp"]})
    summary = {}
    for suffix in SUFFIXES:
        for k in LEVELS:
            rs = [r for r in rows if r["suffix"] == suffix and r["k"] == k]
            s = {"n": len(rs), "closed_correct": sum(r["closed_correct"] for r in rs),
                 "open_correct": sum(r["open_correct"] for r in rs),
                 "median_margin": round(statistics.median(r["closed_margin"] for r in rs), 3),
                 "median_logprob": round(statistics.median(r["target_logprob"] for r in rs), 3)}
            summary[f"{suffix!r} k={k}"] = s
            print(f"{suffix!r:<32} k={k}: closed-set correct {s['closed_correct']:>2}/{s['n']} | "
                  f"open argmax {s['open_correct']:>2}/{s['n']} | margin {s['median_margin']:>7} | "
                  f"lp {s['median_logprob']:>7}")
    LOGS.mkdir(exist_ok=True)
    out = LOGS / f"answer_closed_set_probe_{time.strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps({"summary": summary, "answer_set": answer_ids, "rows": rows, "server": info},
                              indent=1))
    print(f"answer set: {len(answer_ids)} ids; written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
