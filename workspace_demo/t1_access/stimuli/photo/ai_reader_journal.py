"""AI image-reader qualification, revision 3: the ATTEMPT JOURNAL and the COMPLETE RAW-EVIDENCE VALIDATOR (Codex RSC
7048bb8 groups 3 and 6). Standard library only.

THE JOURNAL IS THE RAW FILE (`ai_reader_raw_responses.jsonl`) AND THE ONLY STATE. Every record is one JSON line,
appended, flushed and fsynced (the directory too when the file is created) before the next step; nothing else holds
attempt state, so there is no state file to disagree with it. Each record carries `t` (type), `seq` (1, 2, 3 ...),
`package_digest` (the approved package) and `mode` ('scientific' or 'synthetic-fixture').

    open        a session started (after recovery)
    begin       an attempt is charged: attempt_id (unique), attempt_no (1..660), request, try (1..3), item, view,
                timeout_s, and the prompt-input receipt (instructions hash, delivered image digest)
    dispatched  the worker exists (pid); only after this durable line is 'GO' written to it
    end         the attempt's outcome from its retained evidence (ai_reader_runtime.classify): ok, isolation_violation,
                overflow and interrupted are RETAINED and final; provider_failure, not_dispatched and
                structural_failure are not
    final       a request with three non-retained attempts is retained as no_response (no attempt is charged)
    recovered   at a restart, for an attempt with begin and no end: 'not_dispatched' (no dispatched line - the
                gate never received GO, nothing was sent) is followed by end not_dispatched (charged, retry allowed);
                'dispatched_no_end' (the request may have been answered and the answer lost) is followed by end
                interrupted - RETAINED as a final error, never re-asked (the conservative rule: no retry can select
                among answers). Any surviving worker process group is killed first.
    tail_repair an incomplete last line (a write cut by a crash) moved to a quarantine file with its length and hash
    receipt     COMPLETE (all 600 requests final) or STOPPED (a limit, a structural failure, the smoke rule), with
                the exact counters and the sha256 of every journal byte before it; nothing is appended after it

RECOVERY reconstructs everything from the journal (`reconstruct`) without a call: no answer that reached the journal
is ever asked again, and an answer that did not reach it is handled by the conservative rule above.

VALIDATION (`validate`), before any scoring: every line a JSON object; seq contiguous; one package digest and one
mode throughout; the per-type schema and types; attempt ids unique; attempt_no contiguous and <= 660; tries
contiguous and <= 3 per request; no begin while another attempt is open, after the request is final, or out of the
frozen delivery order; dispatched/end/recovered refer to the open attempt; retained exactly for the retained
outcomes; an answer only where one was received, unedited and bounded (<= 2,000 characters, length and sha256
consistent, `overlength` exactly when longer); bounded evidence; a no-response final only after exactly three
non-retained attempts; nothing after a structural failure but the STOPPED receipt; a last-line receipt whose
counters equal the recount; COMPLETE only with all 600 requests final.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

TYPES = {"open", "begin", "dispatched", "end", "final", "recovered", "tail_repair", "receipt"}
RETAINED = {"ok", "isolation_violation", "overflow", "interrupted"}
NOT_RETAINED = {"provider_failure", "not_dispatched", "structural_failure"}
MODES = {"scientific", "synthetic-fixture"}
MAX_RECORD = 48 * 1024
ANSWER_KEEP, MAX_TRIES, MAX_ATTEMPTS = 2000, 3, 660
COMMON = {"t": str, "seq": int, "package_digest": str, "mode": str}
SCHEMA = {
    "open": {"session": str, "wall": float},
    "begin": {"attempt_id": str, "attempt_no": int, "request": str, "try": int, "item": str, "view": str,
              "timeout_s": float, "receipt": dict, "adir": str, "wall": float},
    "dispatched": {"attempt_id": str, "pid": int, "wall": float},
    "end": {"attempt_id": str, "request": str, "outcome": str, "retained": bool, "seconds": float},
    "final": {"request": str, "outcome": str, "tries": int},
    "recovered": {"attempt_id": str, "finding": str, "killed": bool},
    "tail_repair": {"bytes": int, "sha256": str, "quarantine": str},
    "receipt": {"outcome": str, "reason": str, "counts": dict, "journal_sha256": str, "seconds_total": float},
}


class RawCap(RuntimeError):
    """An append would cross the raw-output cap."""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def append(path: Path, rec: dict, cap: int | None = None) -> None:
    line = (json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n").encode()
    if len(line) > MAX_RECORD:
        raise SystemExit(f"refused: a {rec.get('t')} record of {len(line)} bytes exceeds the {MAX_RECORD} bound")
    size = path.stat().st_size if path.exists() else 0
    if cap is not None and size + len(line) > cap:
        raise RawCap(f"raw output {size} + {len(line)} bytes would cross {cap}")
    new = not path.exists()
    with open(path, "ab") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    if new:
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


def read(path: Path) -> tuple[list[dict], bytes]:
    """(records, incomplete tail bytes). A complete line that is not a JSON object is a refusal."""
    if not path.exists():
        return [], b""
    data = path.read_bytes()
    cut = data.rfind(b"\n") + 1
    recs = []
    for i, line in enumerate(data[:cut].splitlines()):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            raise SystemExit(f"refused: journal line {i + 1} is not JSON")
        if not isinstance(r, dict):
            raise SystemExit(f"refused: journal line {i + 1} is not an object")
        recs.append(r)
    return recs, data[cut:]


def repair_tail(path: Path, quarantine_dir: Path) -> dict | None:
    recs, tail = read(path)
    if not tail:
        return None
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    q = quarantine_dir / f"tail_{len(recs) + 1:06d}_{sha(tail)[:12]}.bin"
    q.write_bytes(tail)
    with open(path, "r+b") as fh:
        fh.truncate(path.stat().st_size - len(tail))
        fh.flush()
        os.fsync(fh.fileno())
    return {"bytes": len(tail), "sha256": sha(tail), "quarantine": q.name}


def fresh() -> dict:
    return {"attempts": 0, "tries": {}, "final": {}, "open": None, "open_dispatched": None, "open_recovered": None,
            "seq": 0, "receipt": None, "outcomes": {}, "structural": False}


def apply(st: dict, r: dict) -> dict:
    st["seq"] = r["seq"]
    t = r["t"]
    if t == "begin":
        st["attempts"] += 1
        st["tries"][r["request"]] = st["tries"].get(r["request"], 0) + 1
        st["open"], st["open_dispatched"], st["open_recovered"] = r, None, None
    elif t == "dispatched":
        st["open_dispatched"] = r
    elif t == "recovered":
        st["open_recovered"] = r
    elif t == "end":
        st["outcomes"][r["outcome"]] = st["outcomes"].get(r["outcome"], 0) + 1
        if r["retained"]:
            st["final"][r["request"]] = r
        if r["outcome"] == "structural_failure":
            st["structural"] = True
        st["open"], st["open_dispatched"], st["open_recovered"] = None, None, None
    elif t == "final":
        st["final"][r["request"]] = r
        st["outcomes"]["no_response"] = st["outcomes"].get("no_response", 0) + 1
    elif t == "receipt":
        st["receipt"] = r
    return st


def reconstruct(recs: list[dict]) -> dict:
    st = fresh()
    for r in recs:
        apply(st, r)
    return st


def counts(st: dict) -> dict:
    return {"attempts": st["attempts"], "requests_final": len(st["final"]),
            "outcomes": dict(sorted(st["outcomes"].items()))}


def _bounded_ok(d, keep: int) -> bool:
    if not isinstance(d, dict) or not isinstance(d.get("length"), int) or not isinstance(d.get("sha256"), str):
        return False
    if "text" in d:
        return d["length"] <= keep and len(d["text"].encode("utf-8", "replace")) <= keep * 4
    return d["length"] > keep and isinstance(d.get("head"), str) and isinstance(d.get("tail"), str) and \
        len(d["head"]) <= keep and len(d["tail"]) <= keep


def _fail(i: int, why: str):
    raise SystemExit(f"refused: raw evidence invalid at record {i + 1}: {why}")


def validate(recs: list[dict], sset: dict, package_digest: str, *, raw_bytes: bytes | None = None,
             require_complete: bool = True, mode: str | None = None) -> dict:
    from ai_reader_runtime import EVENTS_KEEP, STDERR_KEEP
    reqs = {r["request"]: r for r in sset["requests"]}
    order = list(sset["delivery_order"])
    if not recs:
        raise SystemExit("refused: the raw file is empty")
    modes = {r.get("mode") for r in recs}
    if len(modes) != 1 or not modes <= MODES or (mode is not None and modes != {mode}):
        raise SystemExit(f"refused: raw modes {sorted(map(str, modes))}, expected one of {sorted(MODES)}"
                         + (f" = {mode}" if mode else ""))
    ids, st = set(), {"attempts": 0, "tries": {}, "final": set(), "open": None, "disp": False, "recovered": None,
                      "structural": False, "outcomes": {}, "prov_by_req": {}}
    for i, r in enumerate(recs):
        for k, ty in COMMON.items():
            if not isinstance(r.get(k), ty):
                _fail(i, f"field {k} missing or not {ty.__name__}")
        t = r["t"]
        if t not in TYPES:
            _fail(i, f"unknown type {t!r}")
        if r["seq"] != i + 1:
            _fail(i, f"seq {r['seq']} where {i + 1} was due")
        if r["package_digest"] != package_digest:
            _fail(i, "package digest differs from the approved package (mixed or foreign state)")
        for k, ty in SCHEMA[t].items():
            v = r.get(k)
            if ty is float:
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    _fail(i, f"{t}.{k} not a number")
            elif not isinstance(v, ty) or (ty is int and isinstance(v, bool)):
                _fail(i, f"{t}.{k} missing or not {ty.__name__}")
        if i == 0 and t != "open":
            _fail(i, "the journal does not start with an open record")
        if st["structural"] and t != "receipt":
            _fail(i, "a record after a structural failure other than the STOPPED receipt")
        if t == "receipt" and i != len(recs) - 1:
            _fail(i, "a receipt that is not the last record")
        if t == "open":
            if st["open"] is not None:
                _fail(i, "a session opened while an attempt was open")
        elif t == "begin":
            a = r
            if st["open"] is not None:
                _fail(i, "begin while another attempt is open")
            if a["attempt_id"] in ids:
                _fail(i, f"attempt id {a['attempt_id']} repeated")
            ids.add(a["attempt_id"])
            if a["request"] not in reqs or (a["item"], a["view"]) != (reqs[a["request"]]["item"],
                                                                       reqs[a["request"]]["view"]):
                _fail(i, f"unknown request or item/view mismatch {a['request']}")
            if a["request"] in st["final"]:
                _fail(i, f"begin for {a['request']}, already final")
            due = next((q for q in order if q not in st["final"]), None)
            if a["request"] != due:
                _fail(i, f"begin for {a['request']} out of the delivery order (due {due})")
            st["attempts"] += 1
            if a["attempt_no"] != st["attempts"] or a["attempt_no"] > MAX_ATTEMPTS:
                _fail(i, f"attempt_no {a['attempt_no']} where {st['attempts']} was due (cap {MAX_ATTEMPTS})")
            st["tries"][a["request"]] = st["tries"].get(a["request"], 0) + 1
            if a["try"] != st["tries"][a["request"]] or a["try"] > MAX_TRIES:
                _fail(i, f"try {a['try']} for {a['request']} where {st['tries'][a['request']]} was due")
            rc = a["receipt"]
            if not isinstance(rc.get("instructions_sha256"), str) or not isinstance(rc.get("image_sha256"), str):
                _fail(i, "begin without the prompt-input receipt")
            st["open"], st["disp"], st["recovered"] = a, False, None
        elif t == "dispatched":
            if st["open"] is None or r["attempt_id"] != st["open"]["attempt_id"] or st["disp"]:
                _fail(i, "dispatched without its open attempt, or twice")
            st["disp"] = True
        elif t == "recovered":
            if st["open"] is None or r["attempt_id"] != st["open"]["attempt_id"] or st["recovered"]:
                _fail(i, "recovered without its open attempt, or twice")
            want = "dispatched_no_end" if st["disp"] else "not_dispatched"
            if r["finding"] != want:
                _fail(i, f"recovery finding {r['finding']} where {want} follows from the journal")
            st["recovered"] = r["finding"]
        elif t == "end":
            a = st["open"]
            if a is None or r["attempt_id"] != a["attempt_id"] or r["request"] != a["request"]:
                _fail(i, "end without its open attempt")
            o = r["outcome"]
            if o not in RETAINED | NOT_RETAINED:
                _fail(i, f"unknown outcome {o!r}")
            if r["retained"] is not (o in RETAINED):
                _fail(i, f"outcome {o} with retained={r['retained']}")
            if (o == "interrupted") != (st["recovered"] == "dispatched_no_end"):
                _fail(i, "interrupted exactly when recovery found a dispatched attempt without an end")
            if (o == "not_dispatched") != (st["recovered"] == "not_dispatched"):
                _fail(i, "not_dispatched exactly when recovery found an attempt that was never dispatched")
            if o not in ("interrupted", "not_dispatched") and not st["disp"]:
                _fail(i, f"outcome {o} for an attempt that was never dispatched")
            ans = r.get("answer")
            if o in ("ok", "isolation_violation", "overflow"):
                if ans is not None:
                    if not isinstance(ans, str) or not isinstance(r.get("answer_len"), int) or \
                            not isinstance(r.get("answer_sha256"), str) or not isinstance(r.get("overlength"), bool):
                        _fail(i, "answer fields malformed")
                    if r["overlength"] != (r["answer_len"] > ANSWER_KEEP) or len(ans) > ANSWER_KEEP:
                        _fail(i, "answer length, excerpt and overlength flag disagree")
                    if not r["overlength"] and (len(ans) != r["answer_len"] or sha(ans.encode()) != r["answer_sha256"]):
                        _fail(i, "answer differs from its recorded length or sha256 (edited)")
                elif o == "ok":
                    _fail(i, "an ok outcome without an answer")
                for k, keep in (("events", EVENTS_KEEP), ("stderr", STDERR_KEEP)):
                    if not _bounded_ok(r.get(k), keep):
                        _fail(i, f"{k} evidence missing or not bounded")
            elif ans is not None:
                _fail(i, f"an answer on a {o} outcome")
            st["outcomes"][o] = st["outcomes"].get(o, 0) + 1
            if r["retained"]:
                st["final"].add(r["request"])
            else:
                st["prov_by_req"][r["request"]] = st["prov_by_req"].get(r["request"], 0) + 1
            if o == "structural_failure":
                st["structural"] = True
            st["open"] = None
        elif t == "final":
            q = r["request"]
            due = next((x for x in order if x not in st["final"]), None)
            if st["open"] is not None or q != due or r["outcome"] != "no_response" or r["tries"] != MAX_TRIES or \
                    st["tries"].get(q) != MAX_TRIES or st["prov_by_req"].get(q) != MAX_TRIES:
                _fail(i, f"no-response final for {q} without exactly {MAX_TRIES} non-retained attempts")
            st["final"].add(q)
            st["outcomes"]["no_response"] = st["outcomes"].get("no_response", 0) + 1
        elif t == "receipt":
            if st["open"] is not None:
                _fail(i, "receipt while an attempt is open")
            want = {"attempts": st["attempts"], "requests_final": len(st["final"]),
                    "outcomes": dict(sorted(st["outcomes"].items()))}
            if r["counts"] != want:
                _fail(i, f"receipt counters {r['counts']} differ from the recount {want}")
            if r["outcome"] not in ("COMPLETE", "STOPPED"):
                _fail(i, f"receipt outcome {r['outcome']!r}")
            if r["outcome"] == "COMPLETE" and len(st["final"]) != len(reqs):
                _fail(i, "COMPLETE with requests not final")
            if st["structural"] and r["outcome"] != "STOPPED":
                _fail(i, "a structural failure not followed by STOPPED")
            if raw_bytes is not None:
                before = raw_bytes[:raw_bytes.rstrip(b"\n").rfind(b"\n") + 1]
                if sha(before) != r["journal_sha256"]:
                    _fail(i, "receipt journal hash differs from the bytes before it")
    last = recs[-1]
    if require_complete and (last["t"] != "receipt" or last["outcome"] != "COMPLETE"):
        raise SystemExit("refused: the job did not complete (no COMPLETE receipt); an incomplete job cannot qualify")
    return {"records": len(recs), "attempts": st["attempts"], "final": len(st["final"]),
            "outcomes": st["outcomes"], "mode": modes.pop(), "receipt": last if last["t"] == "receipt" else None}
