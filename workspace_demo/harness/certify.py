"""The certification classifier.

RSC operationalization (design doc §3): a commitment is *workspace-certified*
iff its determinants appear in the J-lens readout (top-k, workspace band) at
some prompt position BEFORE the action token. /api/slice reads the prompt
span only, so every hit here is pre-action by construction.

Band: prefer the measured band from upstream data/bands/<lens>.json
(scripts/measure_bands.py output); fallback = the paper-shaped fraction of
the lens's source layers (~L38-L92 of 100 => 0.35-0.92).
"""

from __future__ import annotations

import json
from pathlib import Path


def band_layers(
    layers: list[int],
    bands_json: str | Path | None = None,
    lo_frac: float = 0.35,
    hi_frac: float = 0.92,
) -> list[int]:
    """Workspace-band subset of the readout layers."""
    if bands_json:
        p = Path(bands_json)
        if p.exists():
            d = json.loads(p.read_text())
            # accept a few plausible schema shapes from measure_bands.py
            for key in ("workspace", "bands", "band"):
                b = d.get(key)
                if isinstance(b, dict) and "start" in b and "end" in b:
                    return [l for l in layers if b["start"] <= l <= b["end"]]
                if isinstance(b, list):
                    for seg in b:
                        if isinstance(seg, dict) and seg.get("name", "").lower().startswith("work"):
                            return [l for l in layers if seg["start"] <= l <= seg["end"]]
    n = max(layers) or 1
    return [l for l in layers if lo_frac * n <= l <= hi_frac * n]


def _norm(s: str) -> str:
    return s.strip().lower()


def hits(
    slice_resp: dict,
    targets: list[str],
    band: list[int],
    top_k: int = 10,
) -> list[tuple[int, int, int, str]]:
    """All (layer, pos, rank, matched_target) where a target token appears in
    the top_k readout within the band. Matching: stripped, case-folded
    equality against decoded token strings."""
    tset = {_norm(t) for t in targets}
    cells = slice_resp["cells"]
    out: list[tuple[int, int, int, str]] = []
    for layer in band:
        cell = cells.get(str(layer)) or cells.get(layer)
        if cell is None:
            continue
        for pos, top in enumerate(cell["top_tokens"]):
            for rank, tok in enumerate(top[:top_k]):
                m = _norm(tok)
                if m in tset:
                    out.append((int(layer), pos, rank + 1, m))
    return out


def certified(
    slice_resp: dict,
    determinants: list[str],
    band: list[int],
    top_k: int = 10,
) -> dict:
    """Classify one commitment. Returns the record, not just the bit, so runs
    keep the evidence."""
    h = hits(slice_resp, determinants, band, top_k)
    best = min(h, key=lambda x: x[2]) if h else None
    return {
        "certified": bool(h),
        "n_hits": len(h),
        "best_rank": best[2] if best else None,
        "best_layer": best[0] if best else None,
        "best_pos": best[1] if best else None,
    }


def occupancy_of(
    slice_resp: dict,
    words: list[str],
    band: list[int],
    top_k: int = 10,
) -> int:
    """How many of `words` are present anywhere in the band top-k readout —
    the E1 occupancy proxy for held-in-mind load words."""
    present = set()
    tset = {_norm(w): w for w in words}
    cells = slice_resp["cells"]
    for layer in band:
        cell = cells.get(str(layer)) or cells.get(layer)
        if cell is None:
            continue
        for top in cell["top_tokens"]:
            for tok in top[:top_k]:
                m = _norm(tok)
                if m in tset:
                    present.add(m)
    return len(present)
