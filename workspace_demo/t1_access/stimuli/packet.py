"""Packet text and token ids for T1 — the one place a prompt is assembled (§3, §4, §12).

Every capture, the build's token counts and the prompt scan use these functions,
so a packet is tokenized one way everywhere.

Layout (one line each; "\\n" joins):
    <instruction>
    <carrier open>
    - <slot 1>
    ...
    - <slot 8>
    <carrier close>
    <marker>
followed, in the active condition only, by the answer suffix "\\nAnswer:".

Token ids are built from raw text with the model tokenizer and no special tokens
(the Qwen3.6 tokenizer adds none; no chat template). The suffix rule of §4: the
suffix is tokenized separately and its ids appended, and the item is rejected
unless tokenizing the joined text gives exactly the prefix ids followed by the
suffix ids. The marker must be token-aligned at the end of the prefix; its token
positions are returned, the last of them being the readout position.
"""

from __future__ import annotations

MARKER = "[END]"
ANSWER_SUFFIX = "\nAnswer:"
SLOT_PREFIX = "- "
INSTRUCTION_A = "Read the description below; afterwards, name in one word what is described."


class SuffixError(ValueError):
    """Tokenizing prefix + suffix does not reproduce prefix ids + suffix ids."""


class MarkerError(ValueError):
    """The marker does not end the prefix on token boundaries."""


def packet_text(instruction: str, carrier_open: str, slots: list[str], carrier_close: str,
                marker: str = MARKER) -> str:
    """The prompt prefix (no answer suffix)."""
    if len(slots) != 8:
        raise ValueError(f"a packet has 8 slots, got {len(slots)}")
    parts = [instruction, carrier_open, *(SLOT_PREFIX + s for s in slots), carrier_close, marker]
    for p in parts:
        if "\n" in p:
            raise ValueError(f"a packet line may not contain a newline: {p!r}")
    return "\n".join(parts)


def encode(tok, text: str) -> list[int]:
    return list(tok.encode(text, add_special_tokens=False))


def build_ids(tok, prefix: str, suffix: str | None, marker: str = MARKER) -> dict:
    """Token ids for one trial.

    Returns {"ids", "marker_positions", "readout_position", "n_prefix", "n_suffix"}.
    Raises MarkerError or SuffixError; never truncates.
    """
    if not prefix.endswith(marker):
        raise MarkerError("the prefix does not end with the marker")
    enc = tok(prefix, add_special_tokens=False, return_offsets_mapping=True)
    ids = list(enc["input_ids"])
    offsets = [tuple(o) for o in enc["offset_mapping"]]
    start = len(prefix) - len(marker)
    marker_positions = [i for i, (a, b) in enumerate(offsets) if b > start]
    if (not marker_positions or marker_positions[-1] != len(ids) - 1
            or offsets[marker_positions[0]][0] != start):
        raise MarkerError(f"the marker is not token-aligned: offsets {offsets[-4:]}")
    if ids != encode(tok, prefix):
        raise MarkerError("offset tokenization differs from plain tokenization")
    out = {"ids": ids, "marker_positions": marker_positions,
           "readout_position": marker_positions[-1], "n_prefix": len(ids), "n_suffix": 0}
    if suffix is None:
        return out
    sfx = encode(tok, suffix)
    joined = encode(tok, prefix + suffix)
    if joined != ids + sfx:
        raise SuffixError(f"joined tokenization differs at the boundary: {joined[len(ids) - 2:len(ids) + len(sfx)]} "
                          f"vs {ids[-2:] + sfx}")
    out["ids"] = ids + sfx
    out["n_suffix"] = len(sfx)
    return out
