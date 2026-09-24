"""Step 1b: apply E1 to the WordNet pools and report the eligible count per family.

E1 is the existing rule in stimuli/build_concepts.py: the answer-context form is a single token
under the frozen Qwen3.6 tokenizer - ' x' in lower case, capitalised for countries. It is applied
here rather than in family_pool.py because it needs transformers and the tokenizer snapshot, which
live in the upstream venv, while WordNet lives in .venv-build. Neither goes into t1_access/.venv,
which is version-pinned for parity.

Input : pool_wordnet.json (written by family_pool.py)
Output: pool_eligible.json + the per-family table that the feasibility report quotes.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python stimuli/norms_bank/pool_e1.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
PER_FAMILY = 16
_SRC = os.environ.get("SOURCE", "buchanan")
_MIN = os.environ.get("MIN_FEATURES", "12")
SUFFIX = ("" if _SRC == "buchanan" else f"_{_SRC}") + ("" if _MIN == "12" else f"_min{_MIN}")
VARIANTS = ("any_sense", "sense1")


def main() -> int:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    pool = json.loads((HERE / f"pool_wordnet{SUFFIX}.json").read_text())

    def ids(text: str) -> list[int]:
        return list(tok.encode(text, add_special_tokens=False))

    def answer_form(family: str, word: str) -> str:
        return " " + (word.capitalize() if family == "countries" else word)

    out = {
        "source": pool["source"], "wordnet_version": pool["wordnet_version"],
        "min_features": pool["min_features"], "per_family": PER_FAMILY, "roots": pool["roots"],
        "tokenizer": {"snapshot": SNAPSHOT.name,
                      "tokenizer_json_sha256": hashlib.sha256((SNAPSHOT / "tokenizer.json").read_bytes()).hexdigest()},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scenarios": {},
    }

    for scenario, families in pool["scenarios"].items():
        rows: dict = {}
        for family, by_variant in families.items():
            rows[family] = {}
            for variant in (*VARIANTS, "ceiling"):
                keep, dropped = [], []
                for word in by_variant[variant]["words"]:
                    form = answer_form(family, word)
                    n = len(ids(form))
                    if n == 1:
                        keep.append(word)
                    else:
                        dropped.append({"word": word, "form": form, "tokens": n})
                # A dominant-sense concept is a SYNSET, not a word: 'ax' and 'axe' are one.
                # Collapsing happens here, after E1, so a concept survives if ANY of its cues
                # passes E1 - collapsing first would discard a passing cue behind a failing one.
                key = by_variant[variant].get("synset_key") or {}
                if variant == "sense1" and key:
                    chosen: dict[str, str] = {}
                    for w in keep:
                        chosen.setdefault(key[w], w)
                    concepts = sorted(chosen.values())
                    merged = {k: v for k, v in chosen.items() if sum(1 for w in keep if key[w] == k) > 1}
                else:
                    concepts, merged = keep, {}
                rows[family][variant] = {
                    "after_E2": by_variant[variant]["after_E2"],
                    "after_E1": len(concepts),
                    "after_E1_words": len(keep),
                    "superordinate_in_pool": [w for w in by_variant[variant].get("superordinate_in_pool", []) if w in concepts],
                    "words": concepts,
                    "merged_synsets": merged,
                    "excluded_E1": [] if variant == "ceiling" else dropped,
                }
        out["scenarios"][scenario] = rows

    (HERE / f"pool_eligible{SUFFIX}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    print(f"tokenizer snapshot {SNAPSHOT.name}   needs {PER_FAMILY} per family")
    print("ceiling = every single-word WordNet noun in the subtree passing E2+E1, normed or not\n")
    for scenario, families in out["scenarios"].items():
        print(f"-- scenario {scenario} --        any_sense            sense1          no-norms ceiling")
        for family, by_variant in families.items():
            a, s, c = by_variant["any_sense"], by_variant["sense1"], by_variant["ceiling"]
            flags = []
            if a["after_E1"] < PER_FAMILY:
                flags.append("any_sense BELOW 16")
            if s["after_E1"] < PER_FAMILY:
                flags.append("sense1 below 16")
            mark = ("   << " + "; ".join(flags)) if flags else ""
            print(f"{family:>12}: E2 {a['after_E2']:>4} -> E1 {a['after_E1']:>4}"
                  f"   |  E2 {s['after_E2']:>4} -> E1 {s['after_E1']:>4}"
                  f"   |  ceiling {c['after_E1']:>4}{mark}")
        print()
    print(f"-> {HERE / f'pool_eligible{SUFFIX}.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
