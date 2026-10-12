"""E1 input: the token count of every candidate cue's answer-context form, under the frozen Qwen3.6 tokenizer.

E1 (unchanged in §3.1) requires the answer-context form ' x' to be ONE token: the single-token answer is what
makes the final-position logit contrast, the linear token readout and the H3 token-direction interventions
read a whole concept rather than a prefix. clean_eligibility.py applies E1 from this file, and also reports an
upper bound with E1 relaxed to at most TWO tokens, which is information for the 15 October decision only.

Runs in the upstream venv (transformers + the tokenizer snapshot); WordNet and the norms run in .venv-build, so
the two steps exchange this JSON, which holds cue words and token counts only - no norm data.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/token_counts.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
TOKENIZER_SHA256 = "87a7830d63fcf43bf241c3c5242e96e62dd3fdc29224ca26fed8ea333db72de4"


def cue_words() -> list[str]:
    """Every alphabetic concept label in McRae, Feats, Hovhannisyan and CSLB, read straight from the files."""
    import csv
    words = set()
    mcrae = Path.home() / "word-norms-mcrae/McRae-BRM-InPress/CONCS_FEATS_concstats_brm.txt"
    for line in mcrae.read_text(encoding="utf8", errors="replace").splitlines()[1:]:
        c = line.split("\t", 1)[0].strip()
        if c.isalpha():
            words.add(c)
    for name in ("MBCDI_concsFeats_2022-07-14.csv", "remainingUKCDI_concsFeats.csv"):
        with open(Path.home() / "word-norms-feats" / name, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                c = (r.get("Concept") or "").strip()
                if c.isalpha():
                    words.add(c)
    with open(Path.home() / "word-norms-hovhannisyan" / "featurematrix.csv", encoding="utf-8-sig", newline="") as fh:
        for r in csv.reader(fh):
            c = r[0].strip()
            if c.isalpha() and c != "concept":
                words.add(c)
    cslb = Path.home() / "word-norms-cslb" / "norms.dat"           # CSLB (12 Oct 2026): concept labels only
    if cslb.exists():
        for line in cslb.read_text(encoding="utf-8").splitlines()[1:]:
            c = line.split("\t")[2].strip()
            if c.isalpha():
                words.add(c)
    return sorted(words)


def main() -> int:
    from transformers import AutoTokenizer

    sha = hashlib.sha256((SNAPSHOT / "tokenizer.json").read_bytes()).hexdigest()
    if sha != TOKENIZER_SHA256:
        raise SystemExit(f"tokenizer.json sha256 {sha} does not match the pinned {TOKENIZER_SHA256}")
    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    ids = {w: tok.encode(" " + w, add_special_tokens=False) for w in cue_words()}
    counts = {w: len(v) for w, v in ids.items()}
    out = {"tokenizer_snapshot": SNAPSHOT.name, "tokenizer_json_sha256": sha,
           "form": "' x' (leading space, lower case as written in the norms)", "counts": counts,
           "ids": ids}
    (HERE / "token_counts.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    hist: dict[int, int] = {}
    for n in counts.values():
        hist[n] = hist.get(n, 0) + 1
    print(f"{len(counts)} alphabetic cues; token-count histogram {dict(sorted(hist.items()))}")
    print(f"-> {HERE / 'token_counts.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
