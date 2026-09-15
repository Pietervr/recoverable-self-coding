"""A6: instruction B of the no-target-report condition (PREREGISTRATION_T1_model.md §12).

Instruction A is fixed by §12. Instruction B asks for no report of what is described and must
tokenize to exactly as many tokens as A, so that every packet and marker position has the same
global index in both conditions. The candidates below are declared in order before counting;
the first that matches A's token count, and gives identical ids from the carrier line onward at
identical positions in a test packet, is kept. Every attempt is recorded in instructions.json.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/stimuli/build_instructions.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from stimuli.build_concepts import SNAPSHOT  # noqa: E402
from stimuli.packet import INSTRUCTION_A, build_ids, packet_text  # noqa: E402

CANDIDATES_B = [
    "Read the description below; afterwards, do not name what is described.",
    "Read the description below; afterwards, do not say what is described.",
    "Read the description below; you will not be asked what is described.",
    "Read the description below; there is no need to name what is described.",
]
TEST_SLOTS = ["has four legs and a flat seat for one person"] * 8


def main() -> int:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    n_a = len(tok.encode(INSTRUCTION_A, add_special_tokens=False))
    ref = build_ids(tok, packet_text(INSTRUCTION_A, "Here are some notes:", TEST_SLOTS, "That is all."), None)
    attempts, chosen = [], None
    for cand in CANDIDATES_B:
        n_b = len(tok.encode(cand, add_special_tokens=False))
        b = build_ids(tok, packet_text(cand, "Here are some notes:", TEST_SLOTS, "That is all."), None)
        aligned = (len(b["ids"]) == len(ref["ids"]) and b["ids"][n_a:] == ref["ids"][n_a:]
                   and b["marker_positions"] == ref["marker_positions"])
        attempts.append({"text": cand, "n_tokens": n_b, "positions_aligned": aligned})
        print(f"{n_b:>3} tokens, aligned={aligned}: {cand}")
        if chosen is None and n_b == n_a and aligned:
            chosen = cand
    if chosen is None:
        print(f"STOP: no candidate has {n_a} tokens with aligned positions; propose a wording to Entropy SI")
        return 1
    out = {"A": INSTRUCTION_A, "B": chosen, "n_tokens": n_a, "attempts": attempts,
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "tokenizer_json_sha256": hashlib.sha256((SNAPSHOT / "tokenizer.json").read_bytes()).hexdigest()}
    (HERE / "instructions.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"B = {chosen!r} ({n_a} tokens) -> {HERE / 'instructions.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
