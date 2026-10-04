"""Image audit, step 3: the bounded audit JOB executor - the admitted reader route of revision 17, REUSED, not
re-implemented (R052 ruling 1a, handoff 08f09009). The job brief is AI_AUDIT_JOB.md.

REUSE. This module imports the reviewed qualification executor (ai_reader_exec.py, unchanged, bound by its own 25-field
package) and runs its `Job` - the owned CLI, the deny-by-default allowlist, the per-attempt prompt-input receipt, the
exec-invocation receipt in every preflight, the gate, the watchdog, the journal with its recovery and holds, the clock
and its closure, the STOPPED receipt on every stop - with exactly three differences, each stated and fixtured:
  1. CONFIGURATION. `configure(k)` admits round k's predecessor CHAIN (revision 2, below) and then rebinds the executor
     module's eight path/limit names (SET, DELIVERY, IMAGES, JOB, RAW, GO, ATTEMPTS, LIMITS) to round k's audit files,
     directories and chain-derived limits, in THIS process only; every Job method reads them at call time. The attempts root is /tmp/ra (the qualification's is /tmp/rq: a sweep never touches the
     other job's directories).
  2. ADMISSION. `AuditJob._admit` binds the go as row "aiaudit", stage "audit" against the AUDIT package (below), checks
     the pinned CLI version, re-derives round k's set and key from committed inputs (ai_audit_set.check) and checks the
     round's delivery (the reader's instruction pin, one image per request equal to the item file, the prompt
     rendered) - all inside the reviewed ADMIT_TIMEOUT_S deadline.
  3. THE PROMPT PER REQUEST. The qualification sent one prompt; the audit sends the request's own frozen prompt
     (`AuditJob.attempt` sets it before the reviewed `attempt`, which renders and compares the receipt for exactly
     that prompt - user text hash and prompt_rendered - before anything is sent).
Nothing else changes: one fresh, stateless, image-only request per question, never carrying a prior answer; a retry
only when no answer came back; an answer is final however wrong; the smoke rule on the first request; the holds.

LIMITS (AI_READER_JOB.md: "up to 400 reader turns, a separate job with its own frozen state and caps"). The whole
audit, all rounds: <= 400 attempts and <= 6 h. Round k: planned = its requests; max attempts = min(ceil(1.1 x
planned), 400 - attempts charged in rounds < k); clock = 6 h - seconds charged in rounds < k; 3 tries per request,
120 s per attempt, raw journal <= 20 MiB. Revision 2 (Codex 1b17d64): the round is an integer 1..8 at every entry point,
and the attempts and seconds of earlier rounds come from the authenticated CHAIN (`Chain`): each predecessor's committed
raw journal and committed score file, re-admitted and re-scored by the bound scorer (`ai_audit_score.py verify j`
under .venv-build) to the committed bytes, its charges the re-admitted journal's attempts and CURRENT clock's seconds.
A round refuses when its planned requests exceed the attempts left or the envelope is exhausted.

    .venv-image/bin/python stimuli/photo/ai_audit_exec.py delivery 1   # renders round 1's inputs locally (no request)
    .venv-image/bin/python stimuli/photo/ai_audit_exec.py plan 1       # identity and boundary checks, no request
    .venv-image/bin/python stimuli/photo/ai_audit_exec.py package      # prints the audit package
    .venv-image/bin/python stimuli/photo/ai_audit_exec.py run 1        # only with AIAUDIT_GO.json bound
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_audit_set as S  # noqa: E402
import ai_reader_journal as J  # noqa: E402
import ai_reader_exec as E  # noqa: E402
import ai_reader_runtime as R  # noqa: E402
import stage_a_guard  # noqa: E402

GO = HERE / "AIAUDIT_GO.json"
ATTEMPTS = Path(tempfile.gettempdir()) / "ra"
CAPTURES = HERE.parents[1] / "captures"
TOTAL = {"max_attempts": 400, "job_clock_s": 6 * 3600}
PER_ROUND = {"max_tries_per_request": 3, "attempt_timeout_s": 120, "answer_chars": R.ANSWER_KEEP,
             "raw_bytes": 20 * 1024 * 1024}
ROW, STAGE = "aiaudit", "audit"
NEGATIVE: set[str] = set()
# The audit package: every file the audit's behaviour or its scoring depends on, by path relative to this directory.
BOUND_FILES = [
    # the audit's own code, brief, inputs and round-1 objects
    "ai_audit_exec.py", "ai_audit_set.py", "ai_audit_score.py", "ai_audit_sources.py", "AI_AUDIT_JOB.md",
    "second_view_candidates.json", "ai_audit_sources.json", "manifest_dev.json", "dev_pool.json", "dose.py",
    "ai_audit_set_r1.json", "ai_audit_key_r1.json", "ai_audit_delivery_r1.json",
    # the frozen audit freeze, map and scorer identity (audit_package.py pins)
    "../../audit_app/IMAGE_AUDIT_FREEZE.md", "audit_alias_map.json", "audit_alias_map.py", "audit_package.py",
    # the admitted reader route, reused unchanged
    "ai_reader_exec.py", "ai_reader_runtime.py", "ai_reader_journal.py", "ai_reader_score.py", "ai_reader_key.py",
    "ai_reader_qual_set.json", "ai_reader_delivery.json",
    "stage_a_guard.py", "enforce.py", "memprobe.py", "stage_a_watchdog.py",
]


def sha(b: bytes) -> str:
    return E.sha(b)


def _field(name: str) -> str:
    return Path(name).name.replace(".", "_") + "_sha256"


def delivery_path(k: int) -> Path:
    return HERE / f"ai_audit_delivery_r{k}.json"


def raw_path(k: int) -> Path:
    return HERE / f"ai_audit_raw_r{k}.jsonl"


def job_dir(k: int) -> Path:
    return CAPTURES / f"ai_audit_job_r{k}"


def package(read=None, codex: Path = R.CODEX) -> dict:
    """Every bound file's sha256, the binary and runtime fields (as the reader's package), the round-1 template and the
    reader's instruction pin; `package_digest` over all of it. `read(name)` returns a bound file's bytes (the working
    tree by default; the reviewed commit's blobs in `package_at_commit`)."""
    read = read or (lambda n: (HERE / n).read_bytes())
    p = {_field(n): sha(read(n)) for n in BOUND_FILES}
    qual = json.loads(read("ai_reader_qual_set.json"))
    deliv = json.loads(read("ai_reader_delivery.json"))
    p["things_definitions_sha256"] = sha(S.DEFS.read_bytes())
    p["things_images_metadata_sha256"] = sha(S.IMAGES_TSV.read_bytes())
    p["codex_realpath"] = str(Path(codex).resolve())
    p["codex_sha256"] = E.sha_file(codex)
    p["codex_package_json_sha256"] = E.sha_file(Path(codex).resolve().parents[1] / "codex-package.json")
    p["codex_tree_sha256"] = R.tree_sha(Path(codex).resolve().parents[1])
    p["cli_version"] = subprocess.run([str(codex), "--version"], capture_output=True, text=True,
                                      env={"PATH": "/usr/bin:/bin"}, timeout=30).stdout.strip()
    p["sandbox_exec_sha256"] = E.sha_file(R.SANDBOX_EXEC)
    p["command_template_sha256"] = R.template_sha(qual["reader"], "<per-request frozen prompt>")
    p["instructions_sha256"] = deliv["instructions_sha256"]
    p["package_digest"] = sha(json.dumps(p, sort_keys=True).encode())
    return p


def package_at_commit(commit: str, repo: Path = stage_a_guard.RSC) -> dict:
    rel = HERE.relative_to(repo)

    def read(n: str) -> bytes:
        path = (rel / n).as_posix()
        parts = []
        for part in path.split("/"):                   # resolve '..' inside the repository path
            if part == "..":
                parts.pop()
            elif part not in ("", "."):
                parts.append(part)
        got = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{'/'.join(parts)}"], capture_output=True)
        if got.returncode != 0:
            raise SystemExit(f"refused: {n} is not in the reviewed commit {commit}")
        return got.stdout
    return package(read)


MAX_ROUNDS = 8                                         # a list holds at most 8 candidates: at most 8 rounds
BUILD_PY = HERE.parents[1] / ".venv-build" / "bin" / "python"
VERIFY_TIMEOUT_S = 900.0


def require_round(k) -> int:
    """Revision 2 (Codex 1b17d64 finding 1): a round is a plain int in 1..MAX_ROUNDS - no bool, zero or negative -
    checked by every entry point (AuditJob, configure, the chain, the set builder) before anything is charged or sent."""
    if type(k) is not int or not 1 <= k <= MAX_ROUNDS:
        raise SystemExit(f"refused: round {k!r} is not an integer in 1..{MAX_ROUNDS}")
    return k


def _count(v, what: str) -> int:
    if type(v) is not int or v < 0:
        raise SystemExit(f"refused: {what} {v!r} is not a non-negative integer")
    return v


def _secs(v, what: str) -> float:
    if type(v) not in (int, float) or not math.isfinite(v) or v < 0:
        raise SystemExit(f"refused: {what} {v!r} is not a finite non-negative number of seconds")
    return float(v)


def subprocess_verify(j: int) -> dict:
    """The executor's predecessor authentication: the bound scorer, under .venv-build (WordNet), re-admits round j's
    committed raw journal (complete validation, package, go, set derivation, delivery, the finished CURRENT clock) and
    its own predecessors, re-scores it, and compares the result byte for byte with the committed score file."""
    got = subprocess.run([str(BUILD_PY), str(HERE / "ai_audit_score.py"), "verify", str(j)], capture_output=True,
                         text=True, timeout=VERIFY_TIMEOUT_S)
    if got.returncode != 0:
        raise SystemExit(f"refused: round {j} is not an authenticated predecessor: {got.stderr.strip()[-600:]}")
    try:
        return json.loads(got.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise SystemExit(f"refused: round {j}'s verification printed no result")


class Chain:
    """Revision 2 (Codex 1b17d64 findings 1-2): round k is admitted only on a contiguous chain 1..k-1 of authenticated
    predecessors. For each j: the raw journal AND the score file are tracked, clean and byte-equal to their committed
    blobs; `verify(j)` re-admits and re-scores round j from that evidence and must reproduce the committed score bytes;
    the charges are the RE-ADMITTED journal's attempts and the RE-ADMITTED current clock's seconds (strict finite
    non-negative types), never a field of the score file; the score's mode must be this chain's mode (a synthetic
    predecessor never enters a scientific chain); a STOPPED, missing or inconsistent predecessor refuses. For a run
    (`for_run`) also: round k has not ended (a receipt in its journal refuses before any accounting, so an ended round
    is never re-opened and its clock never re-charged), round k has no score file, and no job directory exists for a
    round outside 1..k. The aggregate envelope - 400 attempts and 6 h over all rounds - is computed from these charges."""

    def __init__(self, *, verify, committed, raw_path, score_path, job_root: Path, mode: str = "scientific"):
        self.verify, self.committed, self.mode = verify, committed, mode
        self.raw_path, self.score_path, self.job_root = raw_path, score_path, Path(job_root)

    def admit(self, k, *, for_run: bool = True) -> dict:
        k = require_round(k)
        if for_run:
            rp = self.raw_path(k)
            if rp.exists():
                recs, _ = J.read(rp, cap=PER_ROUND["raw_bytes"])
                if recs and recs[-1].get("t") == "receipt":
                    raise SystemExit(f"refused: round {k} ended ({recs[-1].get('outcome')}); nothing runs after a "
                                     f"receipt and its clock is not re-opened")
            if self.score_path(k).exists():
                raise SystemExit(f"refused: round {k} already has a score file")
            for d in sorted(self.job_root.glob("ai_audit_job_r*")):
                n = d.name[len("ai_audit_job_r"):]
                if not n.isdigit() or not 1 <= int(n) <= k:
                    raise SystemExit(f"refused: a job directory for a round outside 1..{k} exists ({d.name})")
        priors, att, secs, evidence = {}, 0, 0.0, {}
        for j in range(1, k):
            raw_info = self.committed(self.raw_path(j))
            sc_info = self.committed(self.score_path(j))
            v = self.verify(j)
            if not isinstance(v, dict) or v.get("round") != j:
                raise SystemExit(f"refused: round {j}'s verification is not for round {j}")
            if v.get("score_sha256") != sc_info["raw_sha256"] or v.get("raw_sha256") != raw_info["raw_sha256"]:
                raise SystemExit(f"refused: round {j}'s committed score or journal is not the one re-derived now")
            a, s = _count(v.get("attempts"), f"round {j} attempts"), _secs(v.get("seconds"), f"round {j} seconds")
            sc = json.loads(sc_info["bytes"])
            if sc.get("mode") != self.mode or (self.mode == "scientific" and "WARNING" in sc):
                raise SystemExit(f"refused: round {j}'s score is not a {self.mode} result")
            ident = sc.get("identity") or {}
            if ident.get("round") != j or ident.get("raw_sha256") != raw_info["raw_sha256"] or \
                    (sc.get("charged") or {}).get("attempts") != a:
                raise SystemExit(f"refused: round {j}'s score does not name its admitted journal and attempts")
            priors[j], att, secs = sc, att + a, secs + s
            evidence[j] = {"raw_sha256": raw_info["raw_sha256"], "raw_commit": raw_info["raw_commit"],
                           "score_sha256": sc_info["raw_sha256"], "score_commit": sc_info["raw_commit"],
                           "attempts": a, "seconds": s}
        left_att, left_s = TOTAL["max_attempts"] - att, TOTAL["job_clock_s"] - secs
        if for_run and (left_att <= 0 or left_s <= E.FINAL_S + E.MIN_ATTEMPT_S):
            raise SystemExit(f"refused: the audit envelope is exhausted ({att} of {TOTAL['max_attempts']} attempts, "
                             f"{secs:.0f} of {TOTAL['job_clock_s']} s charged in rounds < {k})")
        return {"round": k, "priors": priors, "attempts": att, "seconds": secs, "left_attempts": left_att,
                "left_seconds": left_s, "evidence": evidence}


def scientific_chain(verify=None) -> Chain:
    from ai_reader_score import committed
    return Chain(verify=verify or subprocess_verify, committed=committed, raw_path=raw_path,
                 score_path=S.score_path, job_root=CAPTURES)


def limits(chained: dict, n_requests: int) -> dict:
    k, left_att, left_s = chained["round"], chained["left_attempts"], chained["left_seconds"]
    if n_requests <= 0 or n_requests > left_att:
        raise SystemExit(f"refused: round {k} plans {n_requests} requests with {left_att} of "
                         f"{TOTAL['max_attempts']} audit attempts left")
    if left_s <= E.FINAL_S + E.MIN_ATTEMPT_S:
        raise SystemExit(f"refused: round {k} has {left_s:.0f} s of the audit's six hours left")
    return {"planned": n_requests, "max_attempts": min(math.ceil(1.1 * n_requests), left_att),
            "job_clock_s": left_s, **PER_ROUND}


def configure(k, *, chain: Chain | None = None, fixture: dict | None = None, for_run: bool = True):
    """Admit round k's chain, then rebind the reviewed executor's module configuration to it (this process only). In
    fixture mode the fixture's paths stand and only the limits are bound - from the SAME chain admission."""
    k = require_round(k)
    if fixture is not None and chain is None:
        raise SystemExit("refused: a fixture run needs its own chain")
    chained = (chain or scientific_chain()).admit(k, for_run=for_run)
    if fixture is not None:
        n = len(fixture["sset"]["requests"])
    else:
        n = len(json.loads(S.set_path(k).read_text())["requests"])
    lim = limits(chained, n)
    if fixture is None:
        E.SET, E.DELIVERY, E.IMAGES = S.set_path(k), delivery_path(k), S.ITEMS
        E.JOB, E.RAW, E.GO, E.ATTEMPTS = job_dir(k), raw_path(k), GO, ATTEMPTS
    E.LIMITS = lim
    return lim, chained


def check_delivery(sset: dict, deliv: dict, pin: str) -> None:
    """A round's delivery: the reader's instruction pin, one entry per request with the item file's image digest (a
    re-encoding is recorded, never accepted silently) and a rendered prompt."""
    if deliv.get("instructions_sha256") != pin:
        raise SystemExit("refused: the round's delivery instructions differ from the reader's frozen pin")
    if sorted(deliv["requests"]) != sorted(r["request"] for r in sset["requests"]):
        raise SystemExit("refused: the delivery does not cover exactly the round's requests")
    for r in sset["requests"]:
        d = deliv["requests"][r["request"]]
        if d["file_sha256"] != r["sha256"] or (d["image_sha256"] != r["sha256"] and not d["reencoded"]) \
                or not d["prompt_rendered"] or d["prompt_sha256"] != sha(r["prompt"].encode()):
            raise SystemExit(f"refused: delivery entry {r['request']} does not match its request")


class AuditJob(E.Job):
    """The reviewed Job with the audit's admission. The chain is admitted BEFORE any accounting (`run`: a refused
    round opens no clock and writes nothing) and AGAIN inside the reviewed admission deadline (`_admit`), which must
    find the same predecessors and charges; the limits are re-bound from that second admission."""

    def __init__(self, k, fixture: dict | None = None, chain: Chain | None = None):
        self.round = require_round(k)
        self.chain = chain
        if fixture is not None and chain is None:
            raise SystemExit("refused: a fixture run needs its own chain")
        super().__init__(fixture)

    def run(self) -> dict:
        self.lim, self.chained = configure(self.round, chain=self.chain, fixture=self.fx)
        return super().run()

    def _readmit(self) -> dict:
        lim, again = configure(self.round, chain=self.chain, fixture=self.fx)
        if (again["attempts"], again["evidence"].keys()) != (self.chained["attempts"],
                                                             self.chained["evidence"].keys()) or \
                any(again["evidence"][j]["score_sha256"] != self.chained["evidence"][j]["score_sha256"]
                    for j in again["evidence"]) or again["seconds"] + 1e-6 < self.chained["seconds"]:
            raise SystemExit("refused: the predecessor chain changed between the pre-clock and the admission check")
        self.chained = again
        return again

    def _admit(self) -> None:
        if self.fx:
            with E.Deadline(E.ADMIT_TIMEOUT_S, "audit chain admission (fixture)"):
                self._readmit()
            return super()._admit()
        with E.Deadline(E.ADMIT_TIMEOUT_S, "audit package, chain and go admission"):
            chained = self._readmit()
            self.sset = json.loads(E.SET.read_text())
            self.deliv = json.loads(E.DELIVERY.read_text())
            self.pkg = package()
            stage_a_guard.NEGATIVE_REVIEWS = stage_a_guard.NEGATIVE_REVIEWS | NEGATIVE
            stage_a_guard.require_go(GO, self.pkg, row=ROW, stage=STAGE, verify_at_commit=package_at_commit)
            S.check(self.round, chained["priors"])
            check_delivery(self.sset, self.deliv, self.pkg["instructions_sha256"])
        if self.pkg["cli_version"] != self.sset["reader"]["cli_version"]:
            raise SystemExit("refused: the installed codex CLI is not the pinned version")
        self.digest = self.pkg["package_digest"]
        self.reqs = {r["request"]: r for r in self.sset["requests"]}
        self.order = self.sset["delivery_order"]

    def attempt(self, r: dict, timeout: float) -> dict:
        self.sset["prompt"] = r["prompt"]              # the request's own frozen prompt (difference 3)
        return super().attempt(r, timeout)


def delivery(k: int) -> dict:
    """Render every request of round k locally (no request): image digest, user text hash, prompt rendered."""
    configure(k)                                       # the chain is admitted first (a later round needs its predecessors)
    sset = json.loads(S.set_path(k).read_text())
    codex = [str(R.CODEX)]
    out, instr = {}, set()
    for r in sset["requests"]:
        data = (S.ITEMS / r["file"]).read_bytes()
        if sha(data) != r["sha256"]:
            raise SystemExit(f"refused: item {r['file']} differs from the set")
        with tempfile.TemporaryDirectory(dir=E.ensure_root()) as td:
            adir = Path(td) / "a"
            img = R.prepare(adir, data, r["file"])
            rc = R.prompt_input(codex, sset["reader"], adir, img, r["prompt"])
        if len(rc["images"]) != 1:
            raise SystemExit(f"refused: {r['request']}: {len(rc['images'])} images rendered")
        im = rc["images"][0]
        instr.add(rc["instructions_sha256"])
        out[r["request"]] = {"image_sha256": im["sha256"], "bytes": im["bytes"], "detail": im["detail"],
                             "mime": im["mime"], "file_sha256": r["sha256"], "reencoded": im["sha256"] != r["sha256"],
                             "user_text_sha256": rc["user_text_sha256"], "prompt_rendered": rc["prompt_rendered"],
                             "prompt_sha256": sha(r["prompt"].encode())}
    if len(instr) != 1:
        raise SystemExit(f"refused: the model-visible instructions differ between requests: {instr}")
    ih = instr.pop()
    pin = json.loads((HERE / "ai_reader_delivery.json").read_text())["instructions_sha256"]
    d = {"note": "Local renderings of each audit request's model-visible input by `codex debug prompt-input` with the "
                 "reader's flags, allowlist sandbox, environment and the request's prompt after '--' (no request was "
                 "sent).", "round": k, "cli_version": sset["reader"]["cli_version"], "instructions_sha256": ih,
         "instructions_equal_reader_pin": ih == pin,
         "reencoded": sum(v["reencoded"] for v in out.values()), "requests": out}
    check_delivery(sset, d, pin)
    delivery_path(k).write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    return {k2: v for k2, v in d.items() if k2 != "requests"}


def plan(k: int) -> dict:
    lim, chained = configure(k)
    S.check(k, chained["priors"])
    sset = json.loads(S.set_path(k).read_text())
    check_delivery(sset, json.loads(delivery_path(k).read_text()),
                   json.loads((HERE / "ai_reader_delivery.json").read_text())["instructions_sha256"])
    codex = [str(R.CODEX)]
    with tempfile.TemporaryDirectory(dir=E.ensure_root()) as td:
        adir = Path(td) / "a"
        img = R.prepare(adir, E._synthetic_png(), "x.png")
        pre = E.preflight(codex, sset, adir, img)
    return {"dry_run": True, "round": k, "requests": len(sset["requests"]), "limits": lim, "preflight": pre,
            "package": package()}


def run(k: int) -> dict:
    return AuditJob(k).run()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "package":
        print(json.dumps(package(), indent=1))
    else:
        k = int(sys.argv[2])
        print(json.dumps({"delivery": delivery, "plan": plan, "run": run}[cmd](k), indent=1, default=str))
