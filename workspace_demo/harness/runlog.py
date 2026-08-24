"""Append-only JSONL run logging with resume support."""

from __future__ import annotations

import json
import time
from pathlib import Path


class RunLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict) -> None:
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
        with self.path.open("a") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()

    def done_keys(self, *fields: str) -> set[tuple]:
        """Keys of already-logged records, for resume-by-skipping."""
        out: set[tuple] = set()
        if not self.path.exists():
            return out
        for line in self.path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if all(f in r for f in fields):
                out.add(tuple(r[f] for f in fields))
        return out

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text().splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
