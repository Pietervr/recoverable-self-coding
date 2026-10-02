"""AI image-reader qualification, revision 3: the bounded READER JOB executor (the job brief is AI_READER_JOB.md; Codex
RSC 7048bb8 groups 1, 3, 4 and 5; R052 handoff 742146ad). It is the orchestrator's half: it holds the key and the
scorer out of the reader's reach and sends the reader one image per fresh request.

    .venv-image/bin/python stimuli/photo/ai_reader_exec.py plan       # identity and boundary checks, no request
    .venv-image/bin/python stimuli/photo/ai_reader_exec.py delivery   # renders all 600 inputs locally, writes
                                                                      # ai_reader_delivery.json (no request)
    .venv-image/bin/python stimuli/photo/ai_reader_exec.py run        # only with AIREADER_GO.json bound (below)

APPROVAL AND IDENTITY (group 1). `package()` hashes every bound file - the set, key, this file, the scorer, the
runtime, the journal, the key/frame/set builders, the job brief, the design, the delivery receipt, and the imported
stage_a_guard.py and enforce.py - plus the actual executable (codex realpath and sha256, its version string,
sandbox-exec's sha256), the command template (argv with placeholders, sandbox profile, environment keys) and the
model-visible instructions hash; `package_digest` is the sha256 of all of it. `run` refuses unless
`stage_a_guard.require_go(GO, package(), row="aireader", stage="qualification")` passes: the go names a review record
at a full commit with its sha256; that record holds exactly one STAGE-ATTESTATION v1 block whose row, stage and
verdict are aireader / qualification / favourable and whose package equals the go's package and the package
recomputed now, and the package re-derived from the reviewed commit's own blobs (`package_at_commit`) equals it too;
dates in order; the negative records (cf3e49e, 7048bb8 among them) never serve. The digest is in
every journal record and in the receipt; a journal written under another digest is refused (mixed resumed state).

THE JOURNAL (group 3) is the raw file and the only attempt state (ai_reader_journal.py): begin (fsynced) -> worker
started -> dispatched (fsynced) -> 'GO' written to the worker -> wait -> end (fsynced). A crash before 'dispatched' is
durable sends nothing (the gate exits on EOF); a crash after it leaves begin+dispatched without end, which the next
start records as INTERRUPTED - retained, a final error, never re-asked - after killing the surviving worker group. An
answer that reached the journal is never asked again. An incomplete last line is quarantined with its hash.

THE CLOCK AND LIMITS (group 5). The session clock starts when `run` is entered, before hashing, recovery and the
journal scan, and is written durably (clock.json) every second while a worker runs and after every record; a session
that dies is charged its last durable live time plus TAIL_S at the next start. Before every attempt: the request's
3-try limit first (a third non-retained attempt -> final no_response, before the aggregate cap is consulted), then the
660-attempt cap, then the clock - the attempt gets min(120 s, remaining - FINAL_S) and is not started when that is
under MIN_ATTEMPT_S - then the raw cap (an attempt's three records must fit under 20 MiB less RAW_FINAL_BYTES). The
worker runs in its own process group; at its deadline, or when its stdout, stderr or attempt directory crosses its
cap, the group gets SIGTERM, TERM_GRACE_S, SIGKILL and is reaped; the outcome is recorded (timeout = provider failure,
overflow = retained ERR_OVERLENGTH). Every stop writes a bounded STOPPED receipt inside the reserve; all 600 final
writes COMPLETE. Nothing is reset, extended or substituted. The lock (stage_a_guard.TaskLock, an fcntl lock) lives
exactly as long as this process.

THE SMOKE RULE (framework 8.2): the first ordinary frozen request is the technical smoke after the go - attempt 1 of
660, charged, retained and scored whatever it says. Before dispatch every attempt, the smoke included, must show the
pinned model-visible instructions and the request's frozen delivered image digest in its prompt-input receipt (a
mismatch holds before anything is sent). After attempt 1 the job holds (STOPPED) on a structural failure, on
malformed or incomplete event evidence, or on an answer saying no image arrived; and after request 1 if it ended with
no answer in three attempts. Nothing is changed on its answer.

FIXTURE MODE. `run(fixture=...)` replaces the binary, the directories and the sandbox for the mechanism tests; its
records are marked mode 'synthetic-fixture', the go is not consulted, and the scorer refuses that mode unless asked
explicitly, labelling the output as not a qualification result.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_journal as J  # noqa: E402
import ai_reader_runtime as R  # noqa: E402
import stage_a_guard  # noqa: E402
from enforce import write_json_atomic  # noqa: E402
from stage_a_guard import TaskLock  # noqa: E402

SET = HERE / "ai_reader_qual_set.json"
DELIVERY = HERE / "ai_reader_delivery.json"
IMAGES = HERE.parents[1] / "captures" / "ai_reader_qual"
JOB = HERE.parents[1] / "captures" / "ai_reader_job"
RAW = HERE / "ai_reader_raw_responses.jsonl"          # the journal; committed before scoring
GO = HERE / "AIREADER_GO.json"
ATTEMPTS = Path(tempfile.gettempdir()) / "rq"         # outside the home, so the sandbox lets the reader read it
LIMITS = {"planned": 600, "max_tries_per_request": 3, "max_attempts": 660, "attempt_timeout_s": 120,
          "job_clock_s": 6 * 3600, "answer_chars": R.ANSWER_KEEP, "raw_bytes": 20 * 1024 * 1024}
FINAL_S, MIN_ATTEMPT_S, TAIL_S, TERM_GRACE_S, BEAT_S = 120.0, 30.0, 30.0, 3.0, 1.0
RAW_FINAL_BYTES, TEMP_CAP = 256 * 1024, 16 * 1024 * 1024
BOUND_FILES = ["ai_reader_qual_set.json", "ai_reader_qual_key.json", "ai_reader_delivery.json", "ai_reader_exec.py",
               "ai_reader_score.py", "ai_reader_runtime.py", "ai_reader_journal.py", "ai_reader_key.py",
               "ai_reader_frame.py", "ai_reader_qual.py", "AI_READER_JOB.md", "AI_READER_DESIGN.md",
               "stage_a_guard.py", "enforce.py"]
NEGATIVE = {"cf3e49e", "7048bb8"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


def package(root: Path = HERE, codex: Path = R.CODEX) -> dict:
    sset = json.loads((root / "ai_reader_qual_set.json").read_text())
    deliv = json.loads((root / "ai_reader_delivery.json").read_text())
    p = {f"{n}_sha256": sha_file(root / n) for n in BOUND_FILES}
    p["codex_realpath"] = str(Path(codex).resolve())
    p["codex_sha256"] = sha_file(codex)
    p["cli_version"] = subprocess.run([str(codex), "--version"], capture_output=True, text=True,
                                      env={"PATH": "/usr/bin:/bin"}, timeout=30).stdout.strip()
    p["sandbox_exec_sha256"] = sha_file(R.SANDBOX_EXEC)
    p["command_template_sha256"] = R.template_sha(sset["reader"], sset["prompt"])
    p["instructions_sha256"] = deliv["instructions_sha256"]
    p["package_digest"] = sha(json.dumps(p, sort_keys=True).encode())
    return p


def package_at_commit(commit: str, repo: Path = stage_a_guard.RSC) -> dict:
    """The package re-derived from the reviewed commit's own blobs (the bound files) with the runtime fields measured
    now; require_go refuses unless it equals the package recomputed from the working tree."""
    rel = HERE.relative_to(repo)
    with tempfile.TemporaryDirectory() as td:
        for n in BOUND_FILES:
            got = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel / n}"], capture_output=True)
            if got.returncode != 0:
                raise SystemExit(f"refused: {n} is not in the reviewed commit {commit}")
            (Path(td) / n).write_bytes(got.stdout)
        return package(Path(td))


class Clock:
    """The job's wall clock across sessions (group 5)."""

    def __init__(self, path: Path, t0: float, cap: float):
        self.path, self.t0, self.cap = path, t0, cap
        rec = json.loads(path.read_text()) if path.exists() else {"sessions": [], "seconds_total": 0.0,
                                                                   "open_session": None}
        if rec["open_session"]:
            s = rec["open_session"]
            charged = float(s["live_s"]) + TAIL_S
            rec["seconds_total"] += charged
            rec["sessions"].append({**s, "closed": "crashed", "charged_s": charged})
        self.rec, self.base = rec, rec["seconds_total"]
        rec["open_session"] = {"session": uuid.uuid4().hex[:12], "pid": os.getpid(), "opened_wall": time.time(),
                               "live_s": 0.0}
        self.last = 0.0
        self.persist()

    def elapsed(self) -> float:
        return self.base + time.monotonic() - self.t0

    def remaining(self) -> float:
        return self.cap - self.elapsed()

    def persist(self) -> None:
        self.rec["open_session"]["live_s"] = time.monotonic() - self.t0
        self.rec["seconds_total_live"] = self.elapsed()
        write_json_atomic(self.path, self.rec)
        self.last = time.monotonic()

    def beat(self) -> None:
        if time.monotonic() - self.last >= BEAT_S:
            self.persist()

    def close(self, outcome: str) -> None:
        s = dict(self.rec["open_session"], live_s=time.monotonic() - self.t0, closed=outcome)
        self.rec["sessions"].append(s)
        self.rec["seconds_total"] = self.elapsed()
        self.rec["open_session"] = None
        write_json_atomic(self.path, self.rec)


def kill_group(proc: subprocess.Popen) -> dict:
    t = time.monotonic()
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=TERM_GRACE_S)
        how = "SIGTERM"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        how = "SIGKILL"
    try:                                                  # the rest of the group, if the leader left first
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    return {"how": how, "kill_to_reap_s": round(time.monotonic() - t, 3)}


def kill_orphan(pid: int, adir: str) -> bool:
    """At recovery: kill a surviving worker group of a crashed session, if it is ours (its command names adir)."""
    cmd = subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True).stdout
    if adir not in cmd:
        return False
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return False
    for _ in range(100):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    raise SystemExit(f"refused: worker {pid} of a crashed session survives SIGKILL; the job holds")


def read_capped(p: Path, cap: int) -> tuple[bytes, bool]:
    if not p.exists():
        return b"", False
    with open(p, "rb") as fh:
        b = fh.read(cap + 1)
    return b[:cap], len(b) > cap


def dir_bytes(d: Path) -> int:
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file() and not f.is_symlink())


def plan() -> dict:
    sset = json.loads(SET.read_text())
    reqs = {r["request"]: r for r in sset["requests"]}
    if sorted(sset["delivery_order"]) != sorted(reqs) or len(reqs) != LIMITS["planned"]:
        raise SystemExit("refused: the delivery order does not cover the 600 declared requests")
    for r in reqs.values():
        if sha_file(IMAGES / r["file"]) != r["sha256"]:
            raise SystemExit(f"refused: image {r['file']} differs from the set")
    codex = [str(R.CODEX)]
    with tempfile.TemporaryDirectory(dir=ensure_root()) as td:
        adir = Path(td) / "a"
        img = R.prepare(adir, (IMAGES / reqs[sset["delivery_order"][0]]["file"]).read_bytes(), "x.png")
        feats = R.effective_features(codex, sset["reader"], adir)
        route = R.auth_route(codex, adir)
        extra = sorted(p.name for p in (adir / "codex_home").iterdir() if p.name != "auth.json")
        argv = R.exec_argv(codex, sset["reader"], adir, img, sset["prompt"])
    return {"dry_run": True, "requests": len(reqs), "images_verified": len(reqs), "limits": LIMITS,
            "effective_features": feats, "auth_route": route, "codex_home_after_local_commands": extra,
            "command_template": argv, "package": package()}


def ensure_root() -> Path:
    ATTEMPTS.mkdir(parents=True, exist_ok=True)
    return ATTEMPTS


def delivery() -> dict:
    """Render every request's model-visible input locally (no request) and freeze the delivered image digests."""
    sset = json.loads(SET.read_text())
    codex = [str(R.CODEX)]
    out, instr = {}, set()
    for r in sset["requests"]:
        data = (IMAGES / r["file"]).read_bytes()
        if sha(data) != r["sha256"]:
            raise SystemExit(f"refused: image {r['file']} differs from the set")
        with tempfile.TemporaryDirectory(dir=ensure_root()) as td:
            adir = Path(td) / "a"
            img = R.prepare(adir, data, r["file"])
            rc = R.prompt_input(codex, sset["reader"], adir, img, sset["prompt"])
        if len(rc["images"]) != 1:
            raise SystemExit(f"refused: {len(rc['images'])} images rendered for {r['request']}")
        im = rc["images"][0]
        instr.add((rc["instructions_sha256"], tuple(rc["instruction_kinds"])))
        out[r["request"]] = {"image_sha256": im["sha256"], "bytes": im["bytes"], "detail": im["detail"],
                             "mime": im["mime"], "file_sha256": r["sha256"], "reencoded": im["sha256"] != r["sha256"],
                             "user_text_sha256": rc["user_text_sha256"]}
    if len(instr) != 1:
        raise SystemExit(f"refused: the model-visible instructions differ between requests: {instr}")
    (ih, kinds), = instr
    with tempfile.TemporaryDirectory(dir=ensure_root()) as td:
        adir = Path(td) / "a"
        R.prepare(adir, b"", "x.png")
        feats = R.effective_features(codex, sset["reader"], adir)
        route = R.auth_route(codex, adir)
    d = {"note": "Local renderings of each request's model-visible input by `codex debug prompt-input` with the job's "
                 "flags, sandbox and environment (no request was sent). The reader receives the delivered bytes.",
         "rendered": time.strftime("%Y-%m-%d"), "cli_version": json.loads(SET.read_text())["reader"]["cli_version"],
         "instructions_sha256": ih, "instruction_kinds": list(kinds), "effective_features": feats,
         "auth_route": route, "reencoded": sum(v["reencoded"] for v in out.values()), "requests": out}
    DELIVERY.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    return {k: v for k, v in d.items() if k != "requests"}


class Stop(Exception):
    pass


class Job:
    def __init__(self, fixture: dict | None):
        self.t0 = time.monotonic()
        self.fx = fixture
        self.mode = "synthetic-fixture" if fixture else "scientific"
        self.sset = fixture["sset"] if fixture else json.loads(SET.read_text())
        self.deliv = fixture["delivery"] if fixture else json.loads(DELIVERY.read_text())
        self.reqs = {r["request"]: r for r in self.sset["requests"]}
        if fixture:
            self.codex, self.sandbox = fixture["codex"], False
            self.images, self.job, self.raw = fixture["images"], fixture["job"], fixture["raw"]
            self.pkg = fixture.get("package") or {"package_digest": "f" * 64}
            self.root = fixture["attempts"]
        else:
            self.codex, self.sandbox = [str(R.CODEX)], True
            self.images, self.job, self.raw, self.root = IMAGES, JOB, RAW, ensure_root()
            self.pkg = package()
            stage_a_guard.NEGATIVE_REVIEWS = stage_a_guard.NEGATIVE_REVIEWS | NEGATIVE
            stage_a_guard.require_go(GO, self.pkg, row="aireader", stage="qualification",
                                     verify_at_commit=package_at_commit)
            if self.pkg["cli_version"] != self.sset["reader"]["cli_version"]:
                raise SystemExit("refused: the installed codex CLI is not the pinned version")
        self.digest = self.pkg["package_digest"]
        self.proc = None

    def crash(self, point: str, n) -> None:
        if self.fx and os.environ.get("AIRQ_CRASH") == f"{point}:{n}":
            os._exit(77)

    def rec(self, t: str, **kw) -> dict:
        r = {"t": t, "seq": self.st["seq"] + 1, "package_digest": self.digest, "mode": self.mode, **kw}
        J.append(self.raw, r, cap=LIMITS["raw_bytes"])
        J.apply(self.st, r)
        self.clock.persist()
        return r

    def stop(self, outcome: str, reason: str, smoke=None) -> dict:
        data = self.raw.read_bytes() if self.raw.exists() else b""
        r = self.rec("receipt", outcome=outcome, reason=reason, counts=J.counts(self.st), journal_sha256=sha(data),
                     seconds_total=self.clock.elapsed(), limits=LIMITS, smoke=smoke)
        return r

    def run(self) -> dict:
        self.job.mkdir(parents=True, exist_ok=True)
        lock = TaskLock(self.job)
        try:
            self.clock = Clock(self.job / "clock.json", self.t0, LIMITS["job_clock_s"])
            tail = J.repair_tail(self.raw, self.job / "quarantine")
            recs, _ = J.read(self.raw)
            for r in recs:
                if r.get("package_digest") != self.digest or r.get("mode") != self.mode:
                    raise SystemExit("refused: the journal was written under another package or mode "
                                     "(mixed resumed state)")
            self.st = J.reconstruct(recs)
            if self.st["receipt"]:
                raise SystemExit(f"refused: the job ended ({self.st['receipt']['outcome']}); nothing runs after a "
                                 f"receipt")
            if tail:
                self.rec("tail_repair", **tail)
            if self.st["open"]:
                self.recover()
            self.rec("open", session=self.clock.rec["open_session"]["session"], wall=time.time())
            result = self.loop()
            self.clock.close(result["outcome"])
            return result
        except BaseException:
            if self.proc is not None and self.proc.poll() is None:
                kill_group(self.proc)                      # no worker outlives an orchestrator that is still alive
            raise
        finally:
            lock.release()

    def recover(self) -> None:
        o, d = self.st["open"], self.st["open_dispatched"]
        adir = Path(o["adir"])
        killed = kill_orphan(d["pid"], o["adir"]) if d else False
        ev = {}
        if adir.exists():
            for name, cap in (("stdout", R.EVENTS_KEEP), ("stderr", R.STDERR_KEEP), ("last.txt", R.ANSWER_KEEP)):
                b, _ = read_capped(adir / name, 1 << 20)
                ev[name] = R.bounded(b, cap)
        finding = "dispatched_no_end" if d else "not_dispatched"
        if not self.st["open_recovered"]:              # a crash during an earlier recovery already recorded it
            self.rec("recovered", attempt_id=o["attempt_id"], finding=finding, killed=killed, evidence=ev,
                     rule="dispatched without end: interrupted, retained as a final error, never re-asked; "
                          "never dispatched: charged, retry permitted")
            self.crash("recovery", o["attempt_no"])
        self.rec("end", attempt_id=o["attempt_id"], request=o["request"],
                 outcome="interrupted" if d else "not_dispatched", retained=bool(d), seconds=0.0, answer=None)
        if adir.exists():
            shutil.rmtree(adir, ignore_errors=True)

    def loop(self) -> dict:
        order = self.sset["delivery_order"]
        smoke = None
        for idx, rq in enumerate(order):
            if rq in self.st["final"]:
                continue
            r = self.reqs[rq]
            while True:
                tries = self.st["tries"].get(rq, 0)
                if tries >= LIMITS["max_tries_per_request"]:
                    self.crash("final", self.st["attempts"])
                    self.rec("final", request=rq, outcome="no_response", tries=tries)
                    if idx == 0:
                        return self.stop("STOPPED", "smoke: the first request had no answer in three attempts; "
                                                    "the route is held", smoke)
                    break
                if self.st["attempts"] >= LIMITS["max_attempts"]:
                    return self.stop("STOPPED", f"attempt cap {LIMITS['max_attempts']} reached", smoke)
                budget = self.clock.remaining() - FINAL_S
                if budget < MIN_ATTEMPT_S:
                    return self.stop("STOPPED", f"job clock: {budget:.0f} s left after the final reserve", smoke)
                size = self.raw.stat().st_size if self.raw.exists() else 0
                if size + 3 * J.MAX_RECORD > LIMITS["raw_bytes"] - RAW_FINAL_BYTES:
                    return self.stop("STOPPED", f"raw output {size} bytes: the next attempt might not fit", smoke)
                try:
                    end = self.attempt(r, min(float(LIMITS["attempt_timeout_s"]), budget))
                except Stop as exc:
                    return self.stop("STOPPED", str(exc), smoke)
                if self.st["attempts"] == 1:
                    smoke = self.smoke(end)
                    if not smoke["pass"]:
                        return self.stop("STOPPED", "smoke: " + smoke["why"], smoke)
                if end["outcome"] == "structural_failure":
                    return self.stop("STOPPED", "structural failure: " + end["stderr"].get("text", "")[-300:], smoke)
                if end["retained"]:
                    break
        return self.stop("COMPLETE", "all 600 requests final", smoke)

    def smoke(self, end: dict) -> dict:
        s = {"attempt": 1, "request": end["request"], "outcome": end["outcome"], "receipt_checked": True}
        if end["outcome"] == "structural_failure":
            return {**s, "pass": False, "why": "structural failure on the first request"}
        if end["outcome"] == "isolation_violation":
            return {**s, "pass": False, "why": "isolation or event evidence failure on the first request: "
                                               + "; ".join(end["isolation_events"])[:300]}
        if end["outcome"] == "ok" and R.no_image_answer(end.get("answer")):
            return {**s, "pass": False, "why": "the first answer says no image arrived"}
        return {**s, "pass": True, "why": ""}

    def attempt(self, r: dict, timeout: float) -> dict:
        n, rq = self.st["attempts"] + 1, r["request"]
        tr = self.st["tries"].get(rq, 0) + 1
        data = (self.images / r["file"]).read_bytes()
        if sha(data) != r["sha256"]:
            raise Stop(f"image {r['file']} differs from the set (nothing sent)")
        adir = Path(tempfile.mkdtemp(dir=self.root)) / "a"
        img = R.prepare(adir, data, r["file"])
        rc = R.prompt_input(self.codex, self.sset["reader"], adir, img, self.sset["prompt"], self.sandbox)
        want = self.deliv["requests"][rq]
        if rc["instructions_sha256"] != self.deliv["instructions_sha256"] or len(rc["images"]) != 1 or \
                rc["images"][0]["sha256"] != want["image_sha256"]:
            raise Stop(f"prompt-input receipt for {rq} differs from the frozen delivery (nothing sent)")
        receipt = {"instructions_sha256": rc["instructions_sha256"], "image_sha256": rc["images"][0]["sha256"],
                   "image_bytes": rc["images"][0]["bytes"], "detail": rc["images"][0]["detail"],
                   "user_text_sha256": rc["user_text_sha256"]}
        self.crash("before_begin", n)
        aid = f"{n:03d}.{rq}.{tr}"
        self.rec("begin", **{"attempt_id": aid, "attempt_no": n, "request": rq, "try": tr, "item": r["item"],
                             "view": r["view"], "timeout_s": timeout, "receipt": receipt, "adir": str(adir),
                             "wall": time.time()})
        self.crash("after_begin", n)
        argv = R.gated(R.boxed(adir, R.exec_argv(self.codex, self.sset["reader"], adir, img, self.sset["prompt"]),
                               self.sandbox))
        with open(adir / "stdout", "wb") as so, open(adir / "stderr", "wb") as se:
            self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=so, stderr=se, env=R.env(adir),
                                         cwd=adir / "w", start_new_session=True)
        t = time.monotonic()
        self.rec("dispatched", attempt_id=aid, pid=self.proc.pid, wall=time.time())
        self.crash("after_dispatch", n)
        self.proc.stdin.write(b"GO\n")
        self.proc.stdin.close()
        self.crash("after_go", n)
        deadline, timed_out, overflow, kill = t + timeout, False, None, None
        while self.proc.poll() is None:
            if time.monotonic() >= deadline:
                timed_out, kill = True, kill_group(self.proc)
                break
            so_n, se_n = (adir / "stdout").stat().st_size, (adir / "stderr").stat().st_size
            if so_n > R.STDOUT_CAP or se_n > R.STDERR_CAP or dir_bytes(adir) > TEMP_CAP + len(data):
                overflow, kill = f"stdout {so_n}, stderr {se_n} bytes", kill_group(self.proc)
                break
            self.clock.beat()
            time.sleep(0.05)
        seconds = time.monotonic() - t
        rcode = self.proc.returncode
        self.proc = None
        self.crash("after_response", n)
        out, o1 = read_capped(adir / "stdout", R.STDOUT_CAP)
        err, o2 = read_capped(adir / "stderr", R.STDERR_CAP)
        last_b, o3 = read_capped(adir / "last.txt", 1 << 20)
        over = bool(overflow) or o1 or o2 or o3
        last = last_b.decode("utf-8", "replace") if (adir / "last.txt").exists() else None
        c = R.classify(out, err, last, rcode, timed_out=timed_out, overflow=over)
        end = self.rec("end", attempt_id=aid, request=rq, seconds=seconds, kill=kill, overflow_detail=overflow,
                       **{k: v for k, v in c.items()})
        self.crash("after_end", n)
        self.clock.persist()
        self.crash("after_state", n)
        shutil.rmtree(adir.parent, ignore_errors=True)
        return end


def run(*, fixture: dict | None = None) -> dict:
    return Job(fixture).run()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    out = {"plan": plan, "delivery": delivery, "run": run}[cmd]()
    print(json.dumps(out, indent=1, default=str))
