"""Photograph arm, rows 20 and 21: the WORKER-SIDE ledger - attempts, the completion transaction, recovery and
storage reservations. Revision 3 (Codex RSC 69539bb closure groups 2-4): time, memory, swap, pressure, the deadline,
termination and reaping moved to the independent controller process (`stage_a_controller.py`), which a worker
cannot outlive or block; this module no longer runs a thread or reads memory.

STATE: one file per task (`stage_a_state.json`), written atomically (temp file, fsync, os.replace, directory fsync)
before and after every attempt. Counters are cumulative and never reset: attempts started / completed / failed and
the model passes they declare, per row and in aggregate (row 20 <= 200, row 21 <= 1,856, aggregate <= 2,056).
`carry_in` adds already-spent attempts when the file is created (row 20: the 16 engineering attempts). Seconds are
the controller's (`controller.json`), not this module's.

ATTEMPTS: `attempt(id, kind, passes)` counts the attempt durably BEFORE the forward and yields an `Attempt`; the
caller writes, re-reads, checksums and validates its outputs and then calls `commit({path: sha256})`. Only a
committed attempt is complete. An exception, or leaving without commit, records a failed attempt. An attempt open at a
crash is recorded at the next open as INTERRUPTED with the session and try that held it; it is never re-run unless
the controller passes an authorisation naming that attempt, session and try, which `authorise_recovery` consumes
durably (a second use, or a use for a later crash of the same id, is refused). A committed attempt is reloaded and
re-verified by the caller, never replayed; an id already attempted otherwise is never retried.

STORAGE: `reserve(n)` must pass before a write of n bytes: everything under the task directories plus 3 n (the bytes
and the temp/rename overlap) must stay under the row's operational storage limit, which the caller sets to the cap
minus the declared finalisation reserve (state, terminal, completion, parity and report writes). `final_size()` is
checked at phase end against the full cap.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

GiB = 1 << 30
MiB = 1 << 20
CAPS = {"row20": {"attempts": 200, "seconds": 4 * 3600, "bytes": 1 * GiB},
        "row21": {"attempts": 1856, "seconds": 4 * 3600, "bytes": 8 * GiB},
        "aggregate": {"attempts": 2056, "seconds": 8 * 3600, "bytes": 9 * GiB}}
MEMORY_CAP = 48 * GiB


class StopRun(RuntimeError):
    """A declared stop condition. The caller archives and stops; it never retries past one."""


def write_atomic(path: Path, data: bytes) -> None:
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def write_json_atomic(path: Path, obj) -> None:
    write_atomic(path, json.dumps(obj, indent=1, sort_keys=True).encode())


def dir_bytes(paths) -> int:
    seen, total = set(), 0
    for d in paths:
        d = Path(d)
        items = [d] if d.is_file() else (d.rglob("*") if d.exists() else [])
        for f in items:
            if f.is_file() and f.resolve() not in seen:
                seen.add(f.resolve())
                total += f.stat().st_size
    return total


def _zero() -> dict:
    return {"started": 0, "completed": 0, "failed": 0, "passes": 0}


class Attempt:
    def __init__(self, attempt_id: str):
        self.id, self.outputs = attempt_id, None

    def commit(self, outputs: dict[str, str]) -> None:
        """Mark complete: call only after every output is written durably, checksummed and validated."""
        if self.outputs is not None:
            raise RuntimeError(f"{self.id} committed twice")
        self.outputs = dict(outputs)


class Budget:
    """The worker's persisted attempt ledger for one row, checked against that row's and the aggregate caps."""

    def __init__(self, state_path: Path, row: str, identity: str, task_paths: list[Path], session: str, *,
                 carry_in: dict | None = None, storage_limit: int | None = None, caps: dict | None = None):
        if row not in ("row20", "row21"):
            raise ValueError(row)
        self.path, self.row, self.identity, self.session = Path(state_path), row, identity, session
        self.task_paths = [Path(p) for p in task_paths]
        self.caps = caps or CAPS
        self.storage_limit = storage_limit if storage_limit is not None else self.caps[row]["bytes"]
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state["identities"].get(row) not in (None, identity):
                raise StopRun(f"identity mismatch for {row}: state has {self.state['identities'][row]}, "
                              f"this execution is {identity}")
            a = self.state.get("open_attempt")
            if a:                                       # died mid-attempt: stays started, now failed and interrupted
                for key in (a["row"], "aggregate"):
                    self.state["counters"][key]["failed"] += 1
                self.state["attempts"][a["id"]]["status"] = "interrupted"
                self.state["interrupted"].append({"id": a["id"], "session": a["session"], "try": a["try"]})
                self.state["open_attempt"] = None
        else:
            self.state = {"identities": {}, "counters": {"row20": _zero(), "row21": _zero(), "aggregate": _zero()},
                          "completed": {}, "attempts": {}, "interrupted": [], "recoveries_consumed": [],
                          "open_attempt": None, "caps": self.caps, "carry_in": {}, "log": []}
            if carry_in:
                for key in (row, "aggregate"):
                    for k in ("started", "completed", "failed", "passes"):
                        self.state["counters"][key][k] += int(carry_in.get(k, 0))
                self.state["carry_in"][row] = carry_in
        self.state["identities"][row] = identity
        self.persist()

    def persist(self) -> None:
        write_json_atomic(self.path, self.state)

    def used_bytes(self) -> int:
        return dir_bytes(self.task_paths)

    def reserve(self, nbytes: int) -> None:
        used = self.used_bytes()
        if used + 3 * int(nbytes) > min(self.storage_limit, self.caps["aggregate"]["bytes"]):
            raise StopRun(f"reserving {nbytes} bytes would exceed the operational storage limit "
                          f"{self.storage_limit} ({used} used)")

    def final_size(self) -> int:
        used = self.used_bytes()
        for key in (self.row, "aggregate"):
            if used > self.caps[key]["bytes"]:
                raise StopRun(f"{key}: final durable size {used} over the cap")
        return used

    def completed(self, attempt_id: str) -> dict | None:
        rec = self.state["completed"].get(attempt_id)
        return dict(rec["outputs"]) if rec else None

    def authorise_recovery(self, auth: dict) -> None:
        """auth names attempt_id, session and try of ONE interrupted try; consumed durably, never reusable."""
        key = {k: auth.get(k) for k in ("attempt_id", "session", "try")}
        match = [i for i in self.state["interrupted"]
                 if (i["id"], i["session"], i["try"]) == (key["attempt_id"], key["session"], key["try"])]
        if not match:
            raise StopRun(f"recovery {key} names no outstanding interrupted try")
        if key in [{k: c.get(k) for k in ("attempt_id", "session", "try")} for c in self.state["recoveries_consumed"]]:
            raise StopRun(f"recovery {key} was already consumed")
        self.state["interrupted"].remove(match[0])
        self.state["recoveries_consumed"].append({**key, "authority": auth, "consumed_by": self.session})
        self.state["attempts"][key["attempt_id"]]["status"] = "interrupted, recovery consumed"
        self.persist()

    @contextmanager
    def attempt(self, attempt_id: str, kind: str, passes: int = 1):
        if attempt_id in self.state["completed"]:
            raise StopRun(f"{attempt_id} already completed: reload its outputs, never replay it")
        prior = self.state["attempts"].get(attempt_id)
        if prior and prior["status"] != "interrupted, recovery consumed":
            raise StopRun(f"{attempt_id} already attempted ({prior['status']}): no retry")
        c = self.state["counters"]
        for key in (self.row, "aggregate"):
            if c[key]["passes"] + passes > self.caps[key]["attempts"]:
                raise StopRun(f"{key}: attempt cap {self.caps[key]['attempts']} would be exceeded")
        tries = (prior or {}).get("tries", 0) + 1
        self.state["open_attempt"] = {"id": attempt_id, "kind": kind, "row": self.row, "passes": passes,
                                      "session": self.session, "try": tries}
        self.state["attempts"][attempt_id] = {"kind": kind, "passes": passes, "status": "open", "tries": tries}
        for key in (self.row, "aggregate"):
            c[key]["started"] += 1
            c[key]["passes"] += passes
        self.persist()                                  # durable BEFORE the forward
        att = Attempt(attempt_id)
        try:
            yield att
        except BaseException as exc:
            self._close(att, kind, passes, f"failed: {exc!r}"[:500])
            raise
        if att.outputs is None:
            self._close(att, kind, passes, "failed: left without commit")
            raise StopRun(f"{attempt_id}: attempt left without a validated commit")
        self._close(att, kind, passes, "completed")

    def _close(self, att: Attempt, kind: str, passes: int, status: str) -> None:
        ok = status == "completed"
        for key in (self.row, "aggregate"):
            self.state["counters"][key]["completed" if ok else "failed"] += 1
        if ok:
            self.state["completed"][att.id] = {"kind": kind, "outputs": att.outputs, "session": self.session}
        self.state["attempts"][att.id]["status"] = status
        self.state["open_attempt"] = None
        self.state["log"].append({"id": att.id, "kind": kind, "passes": passes, "status": status,
                                  "session": self.session})
        self.persist()
