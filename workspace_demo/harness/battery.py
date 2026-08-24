"""Task battery: the shipped probe-swap two-hop set plus the E1 load ramp.

probe-swap.json (Anthropic, Apache-2.0): 90 items, each
  {name, category, prompt, intermediate, answer, swap_to, swap_answer}
where `prompt` ends just before the answer and `intermediate` is the unspoken
bridge entity. Grading: greedy continuation contains `answer` (exact-match
family — no LLM judge, per design doc §5).

Load ramp (E1): prepend a directed-modulation instruction holding K unrelated
single-token nouns in mind (the paper's §3.2 mechanism) before the two-hop
question. K is the load dial; the held words also give the occupancy probe.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

PROBE_SWAP = Path(
    "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/upstream/"
    "jacobian-lens/data/experiments/probe-swap.json"
)

# Concrete, common, likely-single-token nouns; unrelated to the probe-swap
# domains as far as possible. Filtered against the live tokenizer at runtime.
LOAD_POOL = [
    "anchor", "bottle", "candle", "drum", "engine", "fork", "guitar",
    "hammer", "island", "jacket", "kettle", "ladder", "mirror", "needle",
    "orange", "pillow", "queen", "rocket", "saddle", "tunnel", "umbrella",
    "violin", "wallet", "yogurt", "zebra", "basket", "curtain", "donkey",
    "eagle", "feather", "garden", "helmet", "iron", "jungle", "kitchen",
    "lantern", "magnet", "nest", "ocean", "pencil", "quilt", "ribbon",
    "shovel", "ticket", "urn", "valley", "window", "yarn", "zipper",
    "bridge", "castle", "desert", "elbow", "flag", "glove", "harbor",
    "ink", "jewel", "knife", "lemon", "meadow", "napkin", "onion", "pearl",
    "arrow", "button", "cactus", "dolphin", "ember", "fountain", "goose",
    "hinge", "igloo", "jar", "kite", "lobster", "mustard", "nut", "oven",
    "parrot", "quartz", "raft", "sponge", "trumpet", "unicorn", "vase",
    "whale", "xylophone", "yacht", "zinc", "badge", "cloak", "dice",
    "envelope", "fern", "grape",
]


def load_probe_swap(path: Path = PROBE_SWAP) -> list[dict]:
    return json.loads(path.read_text())["items"]


def filter_single_token(client, items: list[dict]) -> tuple[list[dict], list[str]]:
    """Keep items whose intermediate is a single tokenizer piece in at least
    one surface form (' Word' or 'Word'). Returns (kept, dropped_names)."""
    kept, dropped = [], []
    for it in items:
        w = it["intermediate"]
        forms = (f" {w}", w, f" {w.lower()}", w.lower())
        if any(client.n_pieces(f) == 1 for f in forms):
            kept.append(it)
        else:
            dropped.append(it["name"])
    return kept, dropped


def held_words(client, k: int, seed: int) -> list[str]:
    """Deterministic sample of k single-token load words."""
    rng = random.Random(seed)
    pool = LOAD_POOL[:]
    rng.shuffle(pool)
    out: list[str] = []
    for w in pool:
        if len(out) >= k:
            break
        if client.n_pieces(f" {w}") == 1:
            out.append(w)
    return out


def ramped_prompt(item: dict, words: list[str]) -> str:
    """E1 prompt: hold-K-words instruction + the two-hop question."""
    if not words:
        return item["prompt"]
    return (
        "Hold the following words carefully in mind while you answer, "
        "you will be asked about them later: "
        + ", ".join(words)
        + ".\n\n"
        + item["prompt"]
    )


def graded(item: dict, text: str) -> bool:
    """Greedy continuation contains the expected answer (case-insensitive,
    first 48 chars — the answer should lead)."""
    return item["answer"].strip().lower() in text[:48].strip().lower()
