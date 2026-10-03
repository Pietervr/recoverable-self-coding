"""AI image-reader qualification, revision 5: the ATTEMPT JOURNAL and the COMPLETE RAW-EVIDENCE VALIDATOR (Codex RSC
1bf9890 R1, R2, R4 and R6; revision 4 answered RSC 5a8d7ac closures 3, 5 and 6). Standard library plus memprobe's
identity schema.

THE JOURNAL IS THE RAW FILE (`ai_reader_raw_responses.jsonl`) AND THE ONLY STATE. Every record is one JSON line,
appended, flushed and fsynced (the directory too when the file is created) before the next step. Each record carries
`t` (type), `seq` (1, 2, 3 ...), `package_digest` and `mode` ('scientific' or 'synthetic-fixture').

    open        a session started (after recovery), with its fresh preflight: effective features, auth route and the
                exec-invocation receipt (no credential)
    begin       an attempt is charged: attempt_id, attempt_no (1..660), request, try (1..3), item, view, timeout_s and
                the prompt-input receipt (instructions, delivered image and normalised user-text digests)
    dispatched  the worker exists, with its identity (pid, process group, start time) and its watchdog's; only after
                this durable line is 'GO' written to it
    end         the outcome from the retained evidence (ai_reader_runtime.classify): ok, isolation_violation, overflow and
                interrupted are RETAINED and final; provider_failure, not_dispatched and structural_failure are not
    final       a request with three non-retained attempts is retained as no_response
    recovered   at a restart, for an attempt with begin and no end: 'not_dispatched' (charged, retry allowed) or
                'dispatched_no_end' (followed by end interrupted - RETAINED as a final error, never re-asked); the
                surviving worker group killed by verified identity first; captured evidence is labelled a prefix
    tail_repair an incomplete last line, moved durably to a quarantine file (file and directory fsynced) BEFORE the
                journal is truncated; a quarantine file without its record is recorded at the next start (idempotent)
    receipt     COMPLETE or STOPPED, with the exact counters, the smoke status, the limits, the clock and the sha256 of
                every journal byte before it; nothing is appended after it

HOLDS FROM DURABLE RECORDS (`holds`, `smoke_status`): before EVERY dispatch the executor derives, from the journal
alone, whether the job must stop: a structural failure anywhere; and the SMOKE over every attempt of the first ordinary
request - held on a structural failure, an isolation or evidence failure, an overflow, an INTERRUPTED (uncertain)
outcome or an answer saying no image arrived, and after a no-response final; passed only on a retained ok answer;
pending while only provider failures or never-dispatched attempts exist. A recovered uncertain smoke never passes.

VALIDATION (`validate`), run on the INCOMPLETE journal before every resumed dispatch and on the complete journal
before scoring: the file within the raw cap and every line within MAX_RECORD BEFORE parsing; every line an object; seq
contiguous; one digest and mode; EXACT per-type key sets (end in its three variants: recovery, not-sent, classified) and
types; strict worker and watchdog identities (pid = pgid = the leader, start 'sec.usec', never bool); the receipt's
image size and detail equal to the frozen delivery; finite,
in-range numbers (timeouts in (0, 120], durations within the timeout plus grace, walls positive); attempt ids
unique; attempt_no contiguous <= 660; tries contiguous <= 3; no begin while another attempt is open, after the
request is final, out of the frozen order, or after a hold; every begin's receipt equal to the package's instruction
pin and the request's frozen delivered image and user-text digests; dispatched/end/recovered on the open attempt;
retained exactly for the retained outcomes; evidence REQUIRED for every dispatched outcome, its length and sha256
equal to its retained bytes when complete, digest syntax checked; the OUTCOME RE-DERIVED from the retained evidence
(isolation events, the ordered lifecycle, the event answer equal to the -o answer and to the recorded answer, the
structural pattern on the retained stderr) - every COMPLETE retained stream is parsed with the classifier's own
decoding whether or not it decoded losslessly; head-and-tail evidence admits only a retained final error; a
provider/structural label with a received agent message or a non-blank -o file refuses; answers unedited and bounded;
no-response finals only after exactly three non-retained attempts; after a structural failure only tail repairs and the
STOPPED receipt; one tail_repair per quarantine file; the receipt's counters, smoke status, limits, clock (finite,
non-negative; COMPLETE only within job_clock_s) and journal hash; COMPLETE only with all requests final and the smoke
passed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path

TYPES = {"open", "begin", "dispatched", "end", "final", "recovered", "tail_repair", "receipt"}
RETAINED = {"ok", "isolation_violation", "overflow", "interrupted"}
NOT_RETAINED = {"provider_failure", "not_dispatched", "structural_failure"}
MODES = {"scientific", "synthetic-fixture"}
MAX_RECORD = 64 * 1024
ANSWER_KEEP, MAX_TRIES, MAX_ATTEMPTS, MAX_TIMEOUT_S, GRACE_MARGIN_S = 2000, 3, 660, 120.0, 30.0
HEX64 = re.compile(r"[0-9a-f]{64}")
COMMON = {"t": str, "seq": int, "package_digest": str, "mode": str}
# Exact key sets per record type (revision 5, R6): the COMMON keys plus exactly these; `end` has three variants.
EXACT = {
    "open": {"session", "wall", "preflight"},
    "begin": {"attempt_id", "attempt_no", "request", "try", "item", "view", "timeout_s", "receipt", "adir", "wall"},
    "dispatched": {"attempt_id", "pid", "worker", "watchdog", "wall"},
    "final": {"request", "outcome", "tries"},
    "recovered": {"attempt_id", "finding", "killed", "evidence", "note", "rule"},
    "tail_repair": {"bytes", "sha256", "quarantine"},
    "receipt": {"outcome", "reason", "counts", "journal_sha256", "raw_bytes_before", "seconds_total", "limits",
                "smoke"},
}
CLASSIFY_KEYS = {"events", "stderr", "returncode", "timed_out", "event_types", "notices", "usage",
                 "file_answer_sha256", "file_answer", "outcome", "retained", "isolation_events", "answer",
                 "answer_len", "answer_sha256", "overlength"}
END_KEYS = {"recovery": {"attempt_id", "request", "outcome", "retained", "seconds", "answer"},
            "not_sent": {"attempt_id", "request", "outcome", "retained", "seconds", "answer", "cause"},
            "classified": {"attempt_id", "request", "seconds", "kill", "overflow_detail", "group_clean"} | CLASSIFY_KEYS}
SCHEMA = {
    "open": {"session": str, "wall": float, "preflight": dict},
    "begin": {"attempt_id": str, "attempt_no": int, "request": str, "try": int, "item": str, "view": str,
              "timeout_s": float, "receipt": dict, "adir": str, "wall": float},
    "dispatched": {"attempt_id": str, "pid": int, "worker": dict, "watchdog": dict, "wall": float},
    "end": {"attempt_id": str, "request": str, "outcome": str, "retained": bool, "seconds": float},
    "final": {"request": str, "outcome": str, "tries": int},
    "recovered": {"attempt_id": str, "finding": str, "killed": list, "evidence": dict},
    "tail_repair": {"bytes": int, "sha256": str, "quarantine": str},
    "receipt": {"outcome": str, "reason": str, "counts": dict, "journal_sha256": str, "seconds_total": float,
                "limits": dict, "smoke": dict, "raw_bytes_before": int},
}
RECEIPT_KEYS = {"instructions_sha256", "image_sha256", "image_bytes", "detail", "user_text_sha256"}


class RawCap(RuntimeError):
    """An append would cross the raw-output cap."""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _fsync_dir(d: Path) -> None:
    dfd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


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
        _fsync_dir(path.parent)


def read(path: Path, cap: int | None = None) -> tuple[list[dict], bytes]:
    """(records, incomplete tail bytes). A file over `cap`, a complete line longer than MAX_RECORD, or a complete line
    that is not a JSON object is a refusal (R6: bounds enforced before parsing)."""
    if not path.exists():
        return [], b""
    if cap is not None and path.stat().st_size > cap:
        raise SystemExit(f"refused: the journal holds {path.stat().st_size} bytes, over its {cap}-byte cap")
    data = path.read_bytes()
    cut = data.rfind(b"\n") + 1
    recs = []
    for i, line in enumerate(data[:cut].splitlines(keepends=True)):
        if len(line) > MAX_RECORD:
            raise SystemExit(f"refused: journal line {i + 1} holds {len(line)} bytes, over the {MAX_RECORD} bound")
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            raise SystemExit(f"refused: journal line {i + 1} is not JSON")
        if not isinstance(r, dict):
            raise SystemExit(f"refused: journal line {i + 1} is not an object")
        recs.append(r)
    return recs, data[cut:]


def repair_tail(path: Path, quarantine_dir: Path) -> dict | None:
    """Quarantine an incomplete last line DURABLY (file and directory fsynced) before truncating the journal; the
    caller appends the tail_repair record. Idempotent with `pending_quarantine`: a crash after the truncation leaves
    the quarantine file, which the next start records."""
    recs, tail = read(path)
    if not tail:
        return None
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    q = quarantine_dir / f"tail_{len(recs) + 1:06d}_{sha(tail)[:12]}.bin"
    with open(q, "wb") as fh:
        fh.write(tail)
        fh.flush()
        os.fsync(fh.fileno())
    _fsync_dir(quarantine_dir)
    with open(path, "r+b") as fh:
        fh.truncate(path.stat().st_size - len(tail))
        fh.flush()
        os.fsync(fh.fileno())
    return {"bytes": len(tail), "sha256": sha(tail), "quarantine": q.name}


def pending_quarantine(quarantine_dir: Path, recs: list[dict]) -> list[dict]:
    """Quarantine files with no tail_repair record (a crash between truncation and the record)."""
    if not quarantine_dir.exists():
        return []
    done = {r.get("quarantine") for r in recs if r.get("t") == "tail_repair"}
    out = []
    for q in sorted(quarantine_dir.glob("tail_*.bin")):
        if q.name not in done:
            b = q.read_bytes()
            out.append({"bytes": len(b), "sha256": sha(b), "quarantine": q.name})
    return out


def fresh() -> dict:
    return {"attempts": 0, "tries": {}, "final": {}, "open": None, "open_dispatched": None, "open_recovered": None,
            "seq": 0, "receipt": None, "outcomes": {}, "structural": False, "capacity_unproven": False, "ends": {}}


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
        st["ends"].setdefault(r["request"], []).append(r)
        if r["retained"]:
            st["final"][r["request"]] = r
        if r["outcome"] == "structural_failure":
            st["structural"] = True
        if _unproven_mark(r):                          # revision 15: the capacity end whose -o blankness is unproven
            st["capacity_unproven"] = True
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


def smoke_status(st: dict, first_request: str) -> dict:
    """The smoke over every attempt of the first ordinary request, from durable records only."""
    from ai_reader_runtime import no_image_answer
    for e in st["ends"].get(first_request, []):
        o = e["outcome"]
        if o == "structural_failure":
            return {"state": "held", "why": "structural failure on the first request"}
        if o in ("isolation_violation", "overflow"):
            return {"state": "held", "why": f"{o} on the first request: isolation or event evidence failed"}
        if o == "interrupted":
            return {"state": "held", "why": "the first request's outcome was lost in a crash: an uncertain smoke "
                                            "never passes"}
        if o == "ok":
            if no_image_answer(e.get("answer")):
                return {"state": "held", "why": "the first answer says no image arrived"}
            return {"state": "passed", "why": "", "attempt_id": e["attempt_id"]}
    f = st["final"].get(first_request)
    if f is not None and f.get("t") == "final":
        return {"state": "held", "why": "the first request had no answer in three attempts; the route is held"}
    return {"state": "pending", "why": ""}


def holds(st: dict, first_request: str) -> str | None:
    """A reason the job must stop before any further dispatch, derived from durable records; None to proceed."""
    if st["structural"]:
        return "structural failure: the job holds"
    if st.get("capacity_unproven"):
        return "capacity refusal with incomplete -o evidence (blank -o file over 2,048 UTF-8 bytes): the job holds"
    s = smoke_status(st, first_request)
    if s["state"] == "held":
        return "smoke: " + s["why"]
    return None


def _num(v, lo: float, hi: float) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and lo <= v <= hi


def _bounded_ok(d, keep: int) -> bool:
    if not isinstance(d, dict) or not isinstance(d.get("length"), int) or isinstance(d.get("length"), bool) or \
            d["length"] < 0 or not isinstance(d.get("sha256"), str) or not HEX64.fullmatch(d["sha256"]) or \
            not isinstance(d.get("exact"), bool):
        return False
    if "text" in d:
        if set(d) != {"length", "sha256", "text", "exact"} or not isinstance(d["text"], str) or d["length"] > keep:
            return False
        if d["exact"]:
            b = d["text"].encode("utf-8")
            return len(b) == d["length"] and sha(b) == d["sha256"]
        return len(d["text"].encode("utf-8", "replace")) <= keep * 4
    return set(d) == {"length", "sha256", "head", "tail", "exact"} and d["length"] > keep and \
        isinstance(d["head"], str) and isinstance(d["tail"], str) and len(d["head"]) <= keep and len(d["tail"]) <= keep


def _unproven_mark(r: dict) -> bool:
    from ai_reader_runtime import CAPACITY_UNPROVEN
    return r.get("t") == "end" and CAPACITY_UNPROVEN in (r.get("isolation_events") or [])


def _fail(i: int, why: str):
    raise SystemExit(f"refused: raw evidence invalid at record {i + 1}: {why}")


def _rederive(i: int, r: dict) -> None:
    """The end's outcome re-derived from its retained evidence (closure 6; revision 5, R1). Every COMPLETE retained
    stream is parsed whether or not it decoded losslessly: the retained text IS the classifier's own decoding (UTF-8
    with replacement), so parsing it reproduces the events the classifier saw. A stream retained only as head and
    tail cannot be re-derived: such an end is admitted only as a retained final error (isolation or overflow) - never
    as ok, and never as a retryable label."""
    from ai_reader_runtime import (STRUCTURAL, capacity_refusal, event_answer, isolation_problems, lifecycle,
                                   parse_events, retained_text)
    o = r["outcome"]
    ev = r["events"]
    complete = "text" in ev
    if complete and not ev["exact"] and "\ufffd" not in ev["text"]:
        _fail(i, "events marked inexact without a replacement character (representation inconsistent)")
    if not complete and o not in ("isolation_violation", "overflow"):
        _fail(i, f"{o} on events that cannot be re-derived (head and tail only): only a retained final error may")
    if o == "ok" and not (complete and ev["exact"]):
        _fail(i, "an ok outcome without its complete, exact event stream")
    if o == "ok":                                      # the retained -o evidence bound to the answer (revision 6, R2)
        from ai_reader_runtime import ANSWER_KEEP as _AK, FILE_ANSWER_KEEP as _FK
        ans, fa = r.get("answer"), r.get("file_answer")
        if not isinstance(fa, dict) or fa.get("sha256") != r.get("file_answer_sha256") or \
                fa.get("sha256") != r.get("answer_sha256"):
            _fail(i, "an ok outcome whose retained -o evidence is absent or not the answer's digest")
        ev_ = r["events"]
        if "text" in ev_:                              # the complete event answer binds the representation (rev 7, D)
            from ai_reader_runtime import event_answer as _ea, parse_events as _pe
            full = _ea(_pe(ev_["text"].encode("utf-8"))[0])
            if isinstance(full, str) and ((r.get("overlength") and (ans != full[:_AK] or
                                                                   r.get("answer_len") != len(full))) or
                                          (not r.get("overlength") and (ans != full or r.get("answer_len") != len(full)))):
                _fail(i, "an ok outcome whose answer excerpt or length is not the complete event answer's")
        if "text" in fa:
            if not fa["exact"] or (not r.get("overlength") and fa["text"] != ans) or \
                    len(fa["text"].encode("utf-8")) != fa["length"]:
                _fail(i, "an ok outcome whose retained -o text is not exactly the recorded answer")
        elif not (fa["length"] > _FK and isinstance(ans, str) and
                  (r.get("overlength") or len(ans.encode("utf-8")) == fa["length"])):
            _fail(i, "an ok outcome whose retained -o excerpt does not match the answer's declared length")
    fa = r.get("file_answer")
    if o in ("provider_failure", "structural_failure"):
        if fa is not None and not ("text" in fa and fa["exact"] and fa["text"].strip() == "" and
                                   r.get("file_answer_sha256") == fa["sha256"]):
            _fail(i, f"{o} although the -o answer file holds text (a received answer cannot be retried)")
        if fa is None and r.get("file_answer_sha256") is not None:
            _fail(i, f"{o} with an -o answer digest but no retained -o evidence")
    if complete:
        events, problems = parse_events(ev["text"].encode("utf-8"))
        iso = isolation_problems(events)
        # revision 13, repaired in 14 (R2): the declared capacity shape excuses its bare markers for a provider OR a
        # structural failure; which one is decided below by the retained stderr (structural wins), never waived
        declared_capacity = o in ("provider_failure", "structural_failure") and not problems and \
            capacity_refusal(events)
        if (iso or problems) and o not in ("isolation_violation", "overflow") and not declared_capacity:
            _fail(i, f"outcome {o} where the retained events show isolation or malformed lines")
        ea = event_answer(events)
        if sorted({e["type"] for e in events}) != r.get("event_types"):
            _fail(i, "recorded event types differ from the retained events")
        if o == "ok":
            if lifecycle(events):
                _fail(i, "an ok outcome whose retained events do not show the complete ordered lifecycle")
            if ea is None or sha(ea.encode()) != r.get("answer_sha256") or r.get("file_answer_sha256") != \
                    r.get("answer_sha256"):
                _fail(i, "an ok outcome whose event answer, -o answer and recorded answer disagree")
        if o in ("provider_failure", "structural_failure") and (ea is not None or any(
                isinstance(e.get("item"), dict) and e["item"].get("type") == "agent_message" for e in events)):
            _fail(i, f"{o} although the retained events carry an agent message")
        # revision 15 (Codex RSC 431f072): the capacity shape whose -o blankness cannot be re-derived (no answer, the -o
        # file present but not retained complete, exact and blank) is EXACTLY the marked end - a retained final
        # isolation whose recorded isolation events are the stream's own plus the marker; both directions are checked
        from ai_reader_runtime import CAPACITY_UNPROVEN, FILE_ANSWER_KEEP, file_blank_proven
        unproven = not problems and capacity_refusal(events) and isinstance(fa, dict) and \
            not file_blank_proven(fa) and r.get("answer") is None
        if unproven != (CAPACITY_UNPROVEN in (r.get("isolation_events") or [])):
            _fail(i, "the incomplete-capacity-evidence marker disagrees with the retained events and -o evidence")
        if unproven and not (o == "isolation_violation" and r.get("retained") is True and
                             r.get("isolation_events") == iso + [CAPACITY_UNPROVEN] and
                             fa.get("sha256") == r.get("file_answer_sha256") and fa["length"] > FILE_ANSWER_KEEP and
                             "text" not in fa and fa["head"].strip() == "" and fa["tail"].strip() == ""):
            _fail(i, "a capacity end with unproven -o blankness that is not the declared final isolation and hold")
    elif _unproven_mark(r):
        _fail(i, "the incomplete-capacity-evidence marker on events that cannot be re-derived")
    if o in ("provider_failure", "structural_failure"):
        hit = bool(STRUCTURAL.search(retained_text(r["stderr"])))
        if hit != (o == "structural_failure"):
            _fail(i, f"{o} disagrees with the structural pattern on the retained stderr")


def validate(recs: list[dict], sset: dict, package_digest: str, *, raw_bytes: bytes | None = None,
             require_complete: bool = True, mode: str | None = None, delivery: dict | None = None,
             instructions_sha256: str | None = None, limits: dict | None = None) -> dict:
    from ai_reader_runtime import EVENTS_KEEP, STDERR_KEEP
    reqs = {r["request"]: r for r in sset["requests"]}
    order = list(sset["delivery_order"])
    if not recs:
        raise SystemExit("refused: the raw file is empty")
    if raw_bytes is not None:
        cap = (limits or {}).get("raw_bytes")
        if cap is not None and len(raw_bytes) > cap:
            _fail(len(recs) - 1, f"the raw file holds {len(raw_bytes)} bytes, over its {cap}-byte cap")
        for k, line in enumerate(raw_bytes.splitlines(keepends=True)):
            if len(line) > MAX_RECORD:
                _fail(k, f"a line of {len(line)} bytes, over the {MAX_RECORD} bound")
    modes = {r.get("mode") for r in recs}
    if len(modes) != 1 or not modes <= MODES or (mode is not None and modes != {mode}):
        raise SystemExit(f"refused: raw modes {sorted(map(str, modes))}, expected one of {sorted(MODES)}"
                         + (f" = {mode}" if mode else ""))
    ids, st = set(), {"attempts": 0, "tries": {}, "final": set(), "open": None, "disp": False, "recovered": None,
                      "structural": False, "capacity_unproven": False, "outcomes": {}, "prov_by_req": {}}
    js = fresh()
    quarantines = set()
    timeout_cap = float((limits or {}).get("attempt_timeout_s", MAX_TIMEOUT_S))
    for i, r in enumerate(recs):
        for k, ty in COMMON.items():
            if not isinstance(r.get(k), ty) or (ty is int and isinstance(r.get(k), bool)):
                _fail(i, f"field {k} missing or not {ty.__name__}")
        t = r["t"]
        if t not in TYPES:
            _fail(i, f"unknown type {t!r}")
        if r["seq"] != i + 1:
            _fail(i, f"seq {r['seq']} where {i + 1} was due")
        if r["package_digest"] != package_digest:
            _fail(i, "package digest differs from the approved package (mixed or foreign state)")
        if t == "end":
            variant = ("classified" if set(r) & (CLASSIFY_KEYS - {"outcome", "retained", "answer"}) else
                       "not_sent" if "cause" in r else "recovery")
            keys = END_KEYS[variant]
        else:
            keys = EXACT[t]
        if set(r) != set(COMMON) | keys:
            _fail(i, f"{t} fields {sorted(set(r) ^ (set(COMMON) | keys))} differ from its exact schema")
        for k, ty in SCHEMA[t].items():
            v = r.get(k)
            if ty is float:
                if not _num(v, -1e300, 1e300):
                    _fail(i, f"{t}.{k} not a finite number")
            elif not isinstance(v, ty) or (ty is int and isinstance(v, bool)):
                _fail(i, f"{t}.{k} missing or not {ty.__name__}")
        if "wall" in SCHEMA[t] and not r["wall"] > 0:
            _fail(i, f"{t}.wall not positive")
        if i == 0 and t != "open":
            _fail(i, "the journal does not start with an open record")
        if st["structural"] and t not in ("receipt", "tail_repair"):
            _fail(i, "a record after a structural failure other than a tail repair or the STOPPED receipt")
        if st["capacity_unproven"] and t not in ("receipt", "tail_repair"):          # revision 15: the same hold
            _fail(i, "a record after an unproven capacity end other than a tail repair or the STOPPED receipt")
        if t == "receipt" and i != len(recs) - 1:
            _fail(i, "a receipt that is not the last record")
        if t == "open":
            if st["open"] is not None:
                _fail(i, "a session opened while an attempt was open")
        elif t == "begin":
            a = r
            if st["open"] is not None:
                _fail(i, "begin while another attempt is open")
            h = holds(js, order[0])
            if h:
                _fail(i, f"begin after a durable hold ({h})")
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
            if a["request"] != order[0] and smoke_status(js, order[0])["state"] != "passed":
                _fail(i, "a later request begun before the smoke passed")
            st["attempts"] += 1
            if a["attempt_no"] != st["attempts"] or a["attempt_no"] > MAX_ATTEMPTS:
                _fail(i, f"attempt_no {a['attempt_no']} where {st['attempts']} was due (cap {MAX_ATTEMPTS})")
            st["tries"][a["request"]] = st["tries"].get(a["request"], 0) + 1
            if a["try"] != st["tries"][a["request"]] or a["try"] > MAX_TRIES:
                _fail(i, f"try {a['try']} for {a['request']} where {st['tries'][a['request']]} was due")
            if not _num(a["timeout_s"], 1e-9, timeout_cap):
                _fail(i, f"timeout_s {a['timeout_s']} outside (0, {timeout_cap}]")
            rc = a["receipt"]
            if set(rc) != RECEIPT_KEYS or not all(isinstance(rc[k], str) and HEX64.fullmatch(rc[k]) for k in
                                                  ("instructions_sha256", "image_sha256", "user_text_sha256")):
                _fail(i, "begin without the exact prompt-input receipt")
            if not (isinstance(rc["image_bytes"], int) and not isinstance(rc["image_bytes"], bool) and
                    rc["image_bytes"] > 0 and isinstance(rc["detail"], str)):
                _fail(i, "receipt image_bytes/detail malformed")
            if instructions_sha256 is not None and rc["instructions_sha256"] != instructions_sha256:
                _fail(i, "receipt instructions differ from the package's instruction pin")
            if delivery is not None:
                want = delivery["requests"].get(a["request"], {})
                if rc["image_sha256"] != want.get("image_sha256") or \
                        rc["user_text_sha256"] != want.get("user_text_sha256") or \
                        rc["image_bytes"] != want.get("bytes") or rc["detail"] != want.get("detail"):
                    _fail(i, "receipt image, size, detail or user text differs from the request's frozen delivery")
            st["open"], st["disp"], st["recovered"] = a, False, None
        elif t == "dispatched":
            if st["open"] is None or r["attempt_id"] != st["open"]["attempt_id"] or st["disp"]:
                _fail(i, "dispatched without its open attempt, or twice")
            from memprobe import valid_ident
            w_, wd_ = r["worker"], r["watchdog"]
            if not valid_ident(w_) or not valid_ident(wd_) or w_["pid"] != r["pid"] or w_["pgid"] != w_["pid"] or \
                    isinstance(r["pid"], bool) or wd_["pid"] == w_["pid"]:
                _fail(i, "dispatched without strict worker and watchdog identities (pid = pgid = leader)")
            st["disp"] = True
        elif t == "recovered":
            if st["open"] is None or r["attempt_id"] != st["open"]["attempt_id"] or st["recovered"]:
                _fail(i, "recovered without its open attempt, or twice")
            want = "dispatched_no_end" if st["disp"] else "not_dispatched"
            if r["finding"] != want:
                _fail(i, f"recovery finding {r['finding']} where {want} follows from the journal")
            from memprobe import valid_ident
            if not all(valid_ident(k) for k in r["killed"]) or not set(r["evidence"]) <= {"stdout", "stderr",
                                                                                          "last.txt"} or \
                    not isinstance(r["note"], str) or not isinstance(r["rule"], str):
                _fail(i, "recovered record: killed identities, evidence names or text fields malformed")
            for name, e in r["evidence"].items():
                if not (isinstance(e, dict) and e.get("captured_prefix") is True and
                        _bounded_ok({k: v for k, v in e.items() if k not in ("captured_prefix", "source_truncated")},
                                    1 << 20)):
                    _fail(i, f"recovery evidence {name} not a labelled, bounded captured prefix")
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
            if (o == "not_dispatched") != (st["recovered"] == "not_dispatched" or r.get("cause") == "not_sent"):
                _fail(i, "not_dispatched only when recovery found it or the gate was closed unsent")
            if o not in ("interrupted", "not_dispatched") and not st["disp"]:
                _fail(i, f"outcome {o} for an attempt that was never dispatched")
            if not _num(r["seconds"], 0.0, a["timeout_s"] + GRACE_MARGIN_S):
                _fail(i, f"seconds {r['seconds']} outside [0, timeout + {GRACE_MARGIN_S}]")
            ans = r.get("answer")
            if o in ("interrupted", "not_dispatched"):
                if ans is not None:
                    _fail(i, f"an answer on a {o} outcome")
            else:
                for k, keep in (("events", EVENTS_KEEP), ("stderr", STDERR_KEEP)):
                    if not _bounded_ok(r.get(k), keep):
                        _fail(i, f"{k} evidence missing or not bounded and consistent")
                if not isinstance(r.get("timed_out"), bool) or not (r.get("returncode") is None or
                                                                    isinstance(r.get("returncode"), int)):
                    _fail(i, "returncode/timed_out evidence malformed")
                if o in ("ok", "isolation_violation", "overflow"):
                    if ans is not None:
                        if not isinstance(ans, str) or not isinstance(r.get("answer_len"), int) or \
                                not isinstance(r.get("answer_sha256"), str) or not HEX64.fullmatch(r["answer_sha256"]) \
                                or not isinstance(r.get("overlength"), bool):
                            _fail(i, "answer fields malformed")
                        if r["overlength"] != (r["answer_len"] > ANSWER_KEEP) or len(ans) > ANSWER_KEEP:
                            _fail(i, "answer length, excerpt and overlength flag disagree")
                        if not r["overlength"] and (len(ans) != r["answer_len"] or
                                                    sha(ans.encode()) != r["answer_sha256"]):
                            _fail(i, "answer differs from its recorded length or sha256 (edited)")
                    elif o == "ok":
                        _fail(i, "an ok outcome without an answer")
                elif ans is not None:
                    _fail(i, f"an answer on a {o} outcome")
                from ai_reader_runtime import FILE_ANSWER_KEEP, usage_ok
                k_ = r["kill"]
                strs = lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v)   # noqa: E731
                if not (k_ is None or (isinstance(k_, dict) and set(k_) == {"how", "kill_to_reap_s"} and
                                       k_["how"] in ("SIGTERM", "SIGKILL") and _num(k_["kill_to_reap_s"], 0.0, 1e6))) \
                        or not (r["overflow_detail"] is None or isinstance(r["overflow_detail"], str)) or \
                        r["group_clean"] is not True or not strs(r["event_types"]) or not strs(r["notices"]) or \
                        not strs(r["isolation_events"]) or not (r["usage"] is None or isinstance(r["usage"], dict)) \
                        or (o == "ok" and not usage_ok(r["usage"])) or \
                        not (r["file_answer"] is None or _bounded_ok(r["file_answer"], FILE_ANSWER_KEEP)) or \
                        not (r["file_answer_sha256"] is None or (isinstance(r["file_answer_sha256"], str) and
                                                                 HEX64.fullmatch(r["file_answer_sha256"]))):
                    _fail(i, "end bookkeeping fields (kill, overflow, cleanup, event types, notices, usage, -o "
                             "evidence) malformed")
                _rederive(i, r)
            st["outcomes"][o] = st["outcomes"].get(o, 0) + 1
            if r["retained"]:
                st["final"].add(r["request"])
            else:
                st["prov_by_req"][r["request"]] = st["prov_by_req"].get(r["request"], 0) + 1
            if o == "structural_failure":
                st["structural"] = True
            if _unproven_mark(r):
                st["capacity_unproven"] = True
            st["open"] = None
        elif t == "final":
            q = r["request"]
            due = next((x for x in order if x not in st["final"]), None)
            if st["open"] is not None or q != due or r["outcome"] != "no_response" or r["tries"] != MAX_TRIES or \
                    st["tries"].get(q) != MAX_TRIES or st["prov_by_req"].get(q) != MAX_TRIES:
                _fail(i, f"no-response final for {q} without exactly {MAX_TRIES} non-retained attempts")
            st["final"].add(q)
            st["outcomes"]["no_response"] = st["outcomes"].get("no_response", 0) + 1
        elif t == "tail_repair":
            if not HEX64.fullmatch(r["sha256"]) or r["bytes"] <= 0:
                _fail(i, "tail_repair malformed")
            if r["quarantine"] in quarantines:
                _fail(i, f"tail_repair {r['quarantine']} recorded twice (one quarantine, one record)")
            quarantines.add(r["quarantine"])
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
            if st["capacity_unproven"] and r["outcome"] != "STOPPED":
                _fail(i, "an unproven capacity end not followed by STOPPED")
            sm = smoke_status(js, order[0])
            if r["smoke"].get("state") != sm["state"]:
                _fail(i, f"receipt smoke {r['smoke'].get('state')} where the journal shows {sm['state']}")
            if r["outcome"] == "COMPLETE" and sm["state"] != "passed":
                _fail(i, "COMPLETE without a passed smoke")
            if limits is not None and r["limits"] != limits:
                _fail(i, "receipt limits differ from the frozen limits")
            cap_s = float((limits or {}).get("job_clock_s", 6 * 3600))
            if not _num(r["seconds_total"], 0.0, 1e12):
                _fail(i, "receipt clock not finite or negative")
            if r["outcome"] == "COMPLETE" and r["seconds_total"] > cap_s:
                _fail(i, f"COMPLETE with {r['seconds_total']:.0f} s on the clock, over the {cap_s:.0f} s cap")
            if r["raw_bytes_before"] < 0 or (limits is not None and r["raw_bytes_before"] > limits["raw_bytes"]):
                _fail(i, "receipt raw size outside the cap")
            if raw_bytes is not None:
                before = raw_bytes[:raw_bytes.rstrip(b"\n").rfind(b"\n") + 1]
                if sha(before) != r["journal_sha256"] or len(before) != r["raw_bytes_before"]:
                    _fail(i, "receipt journal hash or size differs from the bytes before it")
        apply(js, r)
    last = recs[-1]
    if require_complete and (last["t"] != "receipt" or last["outcome"] != "COMPLETE"):
        raise SystemExit("refused: the job did not complete (no COMPLETE receipt); an incomplete job cannot qualify")
    return {"records": len(recs), "attempts": st["attempts"], "final": len(st["final"]),
            "outcomes": st["outcomes"], "mode": modes.pop(), "receipt": last if last["t"] == "receipt" else None,
            "smoke": smoke_status(js, order[0])}
