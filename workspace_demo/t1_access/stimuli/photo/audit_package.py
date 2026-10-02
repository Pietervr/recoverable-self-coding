"""Before-audit binding of the audit scorer's CODE (Codex RSC 1bf9890 A8). The frozen audit alias map is pinned by its
bytes (audit_alias_map.load_frozen, the sha256 in IMAGE_AUDIT_FREEZE.md); the code that classifies and normalises an
answer against it - ai_reader_score.py (classify, the format checks), ai_reader_key.py (normalise) and
audit_alias_map.py (score) - is bound here. This is a later audit-package condition, not a Stage A gate: the audit
package records `identity()` when it is reviewed, and every audit score goes through `score(..., pins=<that record>)`,
which refuses unless the live map bytes AND the three source files hash to the pinned values. Nothing here changes the
frozen map, its construction record or the qualification scorer.

    .venv-image/bin/python stimuli/photo/audit_package.py      # prints identity() for the audit package
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CODE = ["ai_reader_score.py", "ai_reader_key.py", "audit_alias_map.py"]


def identity() -> dict:
    """The map's pinned sha256 (verified against its bytes) and the sha256 of each scorer source file."""
    import audit_alias_map as M
    M.load_frozen()                                   # refuses unless the map bytes equal the freeze's pin
    return {"audit_alias_map_json_sha256": M.pinned_sha(),
            **{f"{n}_sha256": hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in CODE}}


def require(pins: dict) -> dict:
    now = identity()
    if not isinstance(pins, dict) or pins != now:
        diff = sorted(k for k in set(now) | set(pins if isinstance(pins, dict) else {})
                      if (pins or {}).get(k) != now.get(k))
        raise SystemExit(f"refused: the audit scorer's live identity differs from the audit package's pins: {diff}")
    return now


def score(concept: str, answer: str | None, status: str = "ok", overlength: bool = False, *, pins: dict) -> dict:
    """audit_alias_map.score, only under the audit package's pinned map AND scorer-code identity."""
    import audit_alias_map as M
    ident = require(pins)
    return {**M.score(concept, answer, status, overlength), "scorer_identity": ident}


if __name__ == "__main__":
    print(json.dumps(identity(), indent=1))
