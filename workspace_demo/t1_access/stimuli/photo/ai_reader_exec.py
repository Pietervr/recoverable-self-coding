"""AI image-reader qualification, revision 2: the bounded READER JOB executor (R052 handoff 7f25830e repairs 5, 6, 8;
the job brief is AI_READER_JOB.md). It is the orchestrator's half: it holds the key and the scorer out of the reader's
reach and sends the reader one image per fresh request.

    .venv-image/bin/python stimuli/photo/ai_reader_exec.py plan     # dry run: identity, isolation set-up, no call
    .venv-image/bin/python stimuli/photo/ai_reader_exec.py run      # only with AIREADER_GO.json bound (below)

ISOLATION, per request (repair 6): a new empty directory holding only the request's image under its opaque name;
`codex exec --ephemeral --skip-git-repo-check --ignore-user-config --ignore-rules -s read-only -C <that dir>` with a
PRIVATE CODEX_HOME that holds only a link to the auth file (no AGENTS.md, memories, history, config or plugins), the
pinned model and effort, tool features disabled, `--json` events and `-o` the last message. The prompt is the frozen
PROMPT; nothing else is sent. Colour and grayscale requests of one item are separate sessions in the frozen order
(never adjacent). The JSONL event stream is checked: any event that is not the session, turn, reasoning or agent
message bookkeeping (a command, file, patch, MCP, web or other tool event) marks the response ERR_ISOLATION - kept,
scored as an error, never retried. The delivered bytes are re-hashed against the set before every call.

LIMITS (repair 8): 600 planned responses; at most 3 tries per request and 660 attempts in all, retries ONLY when no
answer was received (process error, timeout, empty last message) - an answer, however wrong, is final; 120 s per
attempt; 6 h of wall clock for the job; 2,000 characters kept per answer (longer is kept truncated and is an
explanatory error by construction); the job's raw output under 20 MB. The later audit has its own allowance, not this
one (AI_READER_JOB.md).

DURABILITY: an exclusive lock; state (attempt counters per request and in total, seconds, status) written atomically
before and after every attempt; every attempt appended to raw_responses.jsonl and fsynced before the next starts. A
restart skips requests that already have a retained answer (idempotent), counts an attempt that was open at a crash
as a failed try, and continues within the same limits. Raw answers are COMMITTED to git before scoring; the scorer
refuses an uncommitted file.

GO: `run` refuses unless AIREADER_GO.json names a favourable Codex review (commit, record path, the record's sha256 at
that commit) and the owner's dated words, and binds the sha256 of ai_reader_qual_set.json, ai_reader_qual_key.json,
this file, ai_reader_score.py, ai_reader_key.py, ai_reader_frame.py, ai_reader_qual.py and AI_READER_JOB.md, plus the
CLI version string. Revision 1's negative review (RSC cf3e49e) can never serve.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from enforce import write_json_atomic  # noqa: E402
from stage_a_guard import TaskLock, require_go  # noqa: E402
import stage_a_guard  # noqa: E402

SET = HERE / "ai_reader_qual_set.json"
IMAGES = HERE.parents[1] / "captures" / "ai_reader_qual"
JOB = HERE.parents[1] / "captures" / "ai_reader_job"
RAW = HERE / "ai_reader_raw_responses.jsonl"          # committed before scoring
GO = HERE / "AIREADER_GO.json"
LIMITS = {"planned": 600, "max_tries_per_request": 3, "max_attempts": 660, "attempt_timeout_s": 120,
          "job_clock_s": 6 * 3600, "answer_chars": 2000, "raw_bytes": 20 * 1024 * 1024}
DISABLE = ["apps", "browser_use", "browser_use_external", "computer_use", "code_mode_host", "shell_tool",
           "unified_exec", "js_repl", "view_image", "image_generation", "tool_search", "web_search_request",
           "web_search_cached", "multi_agent", "memories", "plugins", "hooks", "goals"]
BOOKKEEPING = {"thread.started", "turn.started", "turn.completed", "turn.failed", "item.started", "item.completed",
               "error"}
ALLOWED_ITEM_TYPES = {"agent_message", "reasoning"}
BOUND_FILES = ["ai_reader_qual_set.json", "ai_reader_qual_key.json", "ai_reader_exec.py", "ai_reader_score.py",
               "ai_reader_key.py", "ai_reader_frame.py", "ai_reader_qual.py", "AI_READER_JOB.md"]
NEGATIVE = {"cf3e49e"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def package() -> dict:
    p = {f"{n}_sha256": sha((HERE / n).read_bytes()) for n in BOUND_FILES}
    p["cli_version"] = subprocess.run(["codex", "--version"], capture_output=True, text=True).stdout.strip()
    return p


def command(sset: dict, workdir: Path, image: Path, last: Path) -> list[str]:
    r = sset["reader"]
    cmd = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
           "-s", "read-only", "-C", str(workdir), "-m", r["model"], "-c", f'model_reasoning_effort="{r["reasoning_effort"]}"',
           "--json", "-o", str(last), "-i", str(image)]
    for f in DISABLE:
        cmd += ["--disable", f]
    return cmd + [sset["prompt"]]


def isolation_ok(events: list[dict]) -> tuple[bool, list[str]]:
    bad = []
    for e in events:
        t = e.get("type", "")
        if t not in BOOKKEEPING:
            bad.append(t)
        item = e.get("item") or {}
        if item and item.get("type") not in ALLOWED_ITEM_TYPES:
            bad.append(f"item:{item.get('type')}")
    return not bad, bad


def private_home(root: Path) -> Path:
    home = root / "codex_home"
    home.mkdir(parents=True, exist_ok=True)
    link = home / "auth.json"
    if not link.exists():
        link.symlink_to(Path.home() / ".codex" / "auth.json")   # a link; the credential is never read or copied
    extra = sorted(p.name for p in home.iterdir() if p.name != "auth.json")
    return home, extra


def run(dry: bool = True, *, call=None) -> dict:
    sset = json.loads(SET.read_text())
    if sset["reader"]["cli_version"] not in subprocess.run(["codex", "--version"], capture_output=True,
                                                           text=True).stdout:
        raise SystemExit("refused: the installed codex CLI is not the pinned version")
    reqs = {r["request"]: r for r in sset["requests"]}
    if sorted(sset["delivery_order"]) != sorted(reqs) or len(reqs) != LIMITS["planned"]:
        raise SystemExit("refused: the delivery order does not cover the 600 declared requests")
    for r in reqs.values():
        if sha((IMAGES / r["file"]).read_bytes()) != r["sha256"]:
            raise SystemExit(f"refused: image {r['file']} differs from the set")
    if dry:
        with tempfile.TemporaryDirectory() as td:
            home, extra = private_home(Path(td))
            first = reqs[sset["delivery_order"][0]]
            cmd = command(sset, Path(td) / "w", Path(td) / "w" / first["file"], Path(td) / "last.txt")
        listed = subprocess.run(["codex", "features", "list"], capture_output=True, text=True).stdout.split()
        unknown = [f for f in DISABLE if f not in listed]
        if unknown:
            raise SystemExit(f"refused: features to disable are unknown to this CLI: {unknown}")
        return {"dry_run": True, "requests": len(reqs), "images_verified": len(reqs), "limits": LIMITS,
                "first_command": cmd, "private_home_extra_files": extra, "package": package()}
    stage_a_guard.NEGATIVE_REVIEWS = stage_a_guard.NEGATIVE_REVIEWS | NEGATIVE
    require_go(GO, package(), row="aireader", stage="qualification")   # the attested review (guard v3)
    JOB.mkdir(parents=True, exist_ok=True)
    lock = TaskLock(JOB)
    state_path = JOB / "state.json"
    st = json.loads(state_path.read_text()) if state_path.exists() else {
        "attempts": 0, "seconds": 0.0, "tries": {}, "retained": [], "open": None, "started_wall": time.time()}
    if st["open"]:                                     # crashed mid-attempt: a failed try, already counted
        o = reqs[st["open"]]
        _append({"request": o["request"], "item": o["item"], "view": o["view"], "retained": False,
                 "status": "provider_failure", "reason": "interrupted by a crash (recovered at restart)"})
        st["open"] = None
    t0 = time.monotonic()
    base = st["seconds"]
    try:
        for rq in sset["delivery_order"]:
            if rq in st["retained"]:
                continue
            r = reqs[rq]
            while True:
                if st["attempts"] >= LIMITS["max_attempts"] or base + time.monotonic() - t0 >= LIMITS["job_clock_s"]:
                    raise SystemExit("stop: attempt or clock limit reached; the job holds")
                if RAW.exists() and RAW.stat().st_size >= LIMITS["raw_bytes"]:
                    raise SystemExit("stop: raw output limit reached")
                if st["tries"].get(rq, 0) >= LIMITS["max_tries_per_request"]:
                    rec = {"request": rq, "item": r["item"], "view": r["view"], "retained": True, "status": "no_response",
                           "answer": None, "tries": st["tries"][rq]}
                    _append(rec)
                    st["retained"].append(rq)
                    break
                st["attempts"] += 1
                st["tries"][rq] = st["tries"].get(rq, 0) + 1
                st["open"] = rq
                st["seconds"] = base + time.monotonic() - t0
                write_json_atomic(state_path, st)
                rec = (call or _call)(sset, r)
                rec.update(request=rq, item=r["item"], view=r["view"], attempt=st["tries"][rq])
                st["open"] = None
                if rec["status"] == "provider_failure":
                    rec["retained"] = False
                    _append(rec)
                    write_json_atomic(state_path, st)
                    continue
                rec["retained"] = True
                _append(rec)
                st["retained"].append(rq)
                st["seconds"] = base + time.monotonic() - t0
                write_json_atomic(state_path, st)
                break
        return {"retained": len(st["retained"]), "attempts": st["attempts"], "seconds": st["seconds"]}
    finally:
        st["seconds"] = base + time.monotonic() - t0
        write_json_atomic(state_path, st)
        lock.release()


def _append(rec: dict) -> None:
    with open(RAW, "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _call(sset: dict, r: dict) -> dict:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        work = td / "w"
        work.mkdir()
        img = work / r["file"]
        shutil.copyfile(IMAGES / r["file"], img)
        if sha(img.read_bytes()) != r["sha256"]:
            raise SystemExit(f"refused: delivered bytes of {r['file']} differ from the set")
        home, extra = private_home(td)
        if extra:
            raise SystemExit(f"refused: the private CODEX_HOME holds more than the auth link: {extra}")
        last = td / "last.txt"
        env = {**os.environ, "CODEX_HOME": str(home)}
        t = time.monotonic()
        try:
            p = subprocess.run(command(sset, work, img, last), capture_output=True, text=True, env=env,
                               timeout=LIMITS["attempt_timeout_s"])
        except subprocess.TimeoutExpired:
            return {"status": "provider_failure", "reason": "timeout", "seconds": time.monotonic() - t}
        events = [json.loads(l) for l in p.stdout.splitlines() if l.strip().startswith("{")]
        answer = last.read_text()[:LIMITS["answer_chars"]] if last.exists() else ""
        rec = {"seconds": time.monotonic() - t, "returncode": p.returncode, "events_sha256": sha(p.stdout.encode()),
               "event_types": sorted({e.get("type", "") for e in events}), "delivered_sha256": r["sha256"]}
        if p.returncode != 0 or not answer.strip():
            return {**rec, "status": "provider_failure", "reason": (p.stderr or "")[-500:]}
        ok, bad = isolation_ok(events)
        return {**rec, "status": "ok" if ok else "isolation_violation", "answer": answer, "isolation_events": bad}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    print(json.dumps(run(dry=(cmd != "run")), indent=1, default=str))
