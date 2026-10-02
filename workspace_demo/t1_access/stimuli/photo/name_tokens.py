"""E1 input for the photograph arm: the answer-form token ids of every THINGS concept name.

E1 is unchanged from the text arm: the answer-context form ' x' (leading space, lower case) is ONE token under the
frozen Qwen3.6 tokenizer (snapshot c000ac2c, tokenizer.json sha256 87a7830d...). The photograph arm answers after
the same suffix, so the same convention applies. Runs in the upstream venv; pool.py reads the JSON.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/photo/name_tokens.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
TOKENIZER_SHA256 = "87a7830d63fcf43bf241c3c5242e96e62dd3fdc29224ca26fed8ea333db72de4"
CONCEPTS = Path.home() / "things-plus/_concepts-metadata_things.tsv"


def main() -> None:
    from transformers import AutoTokenizer
    sha = hashlib.sha256((SNAPSHOT / "tokenizer.json").read_bytes()).hexdigest()
    assert sha == TOKENIZER_SHA256, sha
    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    words = sorted({r["Word"].strip().lower() for r in csv.DictReader(open(CONCEPTS, encoding="utf-8",
                                                                         errors="replace"), delimiter="\t")})
    ids = {w: tok.encode(" " + w, add_special_tokens=False) for w in words}
    (HERE / "name_tokens.json").write_text(json.dumps({"tokenizer_json_sha256": sha, "form": "' x'",
                                                       "ids": ids}, indent=1, sort_keys=True) + "\n")
    print(f"{len(ids)} names; single-token {sum(len(v) == 1 for v in ids.values())}")


if __name__ == "__main__":
    main()
