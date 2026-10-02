"""AI image-reader qualification, revision 3: THE REQUEST BOUNDARY (Codex RSC 7048bb8 group 4; framework 8.2's
isolation evidence list and smoke rule). Standard library only. Nothing here sends a request by itself: `exec_argv`
builds the one command that does, and only `ai_reader_exec.run` starts it, after the go.

WHAT THE READER PROCESS GETS, per attempt:
  - the pinned codex binary (`CODEX`, realpath and sha256 bound into the package) under macOS sandbox-exec with
    `PROFILE`: every file read under the user's home is denied except the auth file (so the key, the set, the
    repositories, the norms and ~/.codex's config, rules and instructions are unreadable to it - fixture
    `Boundary.test_profile_denies_repo_and_allows_codex`, real binary, no request);
  - a pinned minimal environment (`env`): PATH=/usr/bin:/bin, HOME, CODEX_HOME and TMPDIR inside the attempt directory
    (outside the home), LANG. Nothing is inherited from the orchestrator's environment;
  - a private CODEX_HOME holding only a symlink to the auth file; `--ephemeral --skip-git-repo-check
    --ignore-user-config --ignore-rules -s read-only`, the CONFIG overrides (model, effort, and the switches that drop
    the permissions, environment, collaboration-mode, apps and skills instructions from the model-visible input), and
    every tool-capable feature in DISABLE turned off; `codex features list` under the same flags must report each
    of them false (`effective_features`) - except unified_exec, which this CLI keeps on under every switch
    (UNDISABLEABLE, measured and recorded; contained by the sandbox, shell_tool off and the event check);
  - one empty working directory holding only the image under its opaque request name, and the frozen PROMPT.

RECEIPTS (no credential is read or recorded):
  - `prompt_input`: `codex debug prompt-input` with the identical flags, sandbox and environment renders the
    model-visible input locally. Its non-user part (with the attempt's directory written as <W>) is hashed and must
    equal the INSTRUCTIONS pin in the package; the embedded image bytes are decoded and hashed, and must equal the
    request's frozen delivered digest (`ai_reader_delivery.json`). Measured 2 October 2026: with these flags the
    model-visible developer content is the CLI's multi-agent role and mode text only (it survives every switch,
    including --disable multi_agent); a 64 px PNG is embedded byte-identically and a 2,400 px one is re-encoded, so
    the delivered digest is the CLI's, recorded per request. What the CLI actually transmits is its own claim;
    this is its local rendering of the same input.
  - `auth_route`: `codex login status` (its one line, e.g. 'Logged in using ChatGPT').
  - the event stream and stderr of every attempt, retained bounded (`bounded`), with original length and sha256.

PARSER AND CLASSIFICATION (fail closed; `parse_events`, `classify`):
  1. any event or item outside the bookkeeping set (a command, file, patch, MCP, web, plan, agent or other tool
     event) -> ISOLATION, retained, final - checked BEFORE any retry eligibility, whatever the exit status;
  2. stdout, stderr or the attempt directory over its cap -> OVERFLOW, retained, final (ERR_OVERLENGTH);
  3. any stdout line that is not a JSON object with a string type -> ISOLATION (malformed evidence), retained, final;
  4. an answer received - the -o file, or else the last completed agent message in the events - is LOCKED whatever
     the exit status: retained 'ok' when the lifecycle is complete (thread.started first, turn.started, a completed
     agent message, turn.completed last), else retained ISOLATION (evidence incomplete, cannot be verified);
  5. no answer and no agent message: STRUCTURAL when stderr matches a frozen configuration/authentication/image
     pattern (the job holds), else PROVIDER_FAILURE (the only retryable outcome).
  An answer longer than ANSWER_KEEP characters is never cut silently: the record keeps an excerpt, the original
  length and sha256 and `overlength: true`, and the scorer codes it ERR_OVERLENGTH.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

HOME = Path.home()
CODEX = Path("/opt/homebrew/Caskroom/codex/0.159.3/bin/codex")
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
AUTH = HOME / ".codex" / "auth.json"
DISABLE = ["apps", "browser_use", "browser_use_external", "browser_use_full_cdp_access", "computer_use",
           "code_mode_host", "shell_tool", "unified_exec", "unified_exec_tty", "shell_snapshot", "js_repl",
           "view_image", "image_generation", "tool_search", "tool_suggest", "web_search_request", "web_search_cached",
           "multi_agent", "memories", "plugins", "plugin_sharing", "remote_plugin", "hooks", "goals", "sleep_tool",
           "skill_search", "skill_mcp_dependency_install", "tool_call_mcp_elicitation", "realtime_conversation",
           "in_app_browser", "in_app_local_automation", "worktrees", "workspace_dependencies", "write_stdin_approval"]
# Measured 2 October 2026 (`codex features list`, no request): unified_exec stays effectively true under
# --disable unified_exec, -c features.unified_exec=false and every other switch tried; shell_tool and unified_exec_tty
# do turn off. It is passed as --disable anyway and recorded as the one feature that cannot be turned off; the boundary
# for it is the sandbox (the home unreadable), shell_tool off, and the event check (any command event = ISOLATION).
UNDISABLEABLE = ["unified_exec"]
CONFIG = ['model_reasoning_effort="{effort}"', "include_permissions_instructions=false",
          "include_environment_context=false", "include_collaboration_mode_instructions=false",
          "include_apps_instructions=false", "skills.include_instructions=false", "skills.bundled.enabled=false"]
BOOKKEEPING = {"thread.started", "turn.started", "turn.completed", "turn.failed", "item.started", "item.updated",
               "item.completed", "error"}
ALLOWED_ITEM_TYPES = {"agent_message", "reasoning"}
ANSWER_KEEP = 2000                     # characters kept verbatim; longer = excerpt + length + sha256, ERR_OVERLENGTH
EVENTS_KEEP, STDERR_KEEP = 16384, 4096  # bytes of raw evidence retained per attempt (head and tail beyond that)
STDOUT_CAP, STDERR_CAP = 1 << 20, 256 << 10   # bytes captured per attempt before the worker is killed (OVERFLOW)
STRUCTURAL = re.compile(r"(?i)(error loading config|unknown (feature|variant|field)|invalid value|unsupported image|"
                        r"invalid[_ ]image|image (could not|cannot) be|not logged in|login required|unauthori[sz]ed|"
                        r"\b401\b|\b403\b|model[_ ]not[_ ]found|does not exist or you do not have access|"
                        r"sandbox-exec: )")
NO_IMAGE = re.compile(r"(?i)(no (image|picture|photo)|can(no|')t see (an|the|any) (image|picture)|"
                      r"(image|picture) (is|was) not (attached|provided|visible)|did ?n[o']t (attach|include|provide))")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def profile(home: Path = HOME) -> str:
    return ("(version 1)\n(allow default)\n"
            f'(deny file-read* (subpath "{home}"))\n'
            f'(allow file-read* (literal "{home}/.codex/auth.json"))\n'
            f'(allow file-read-metadata (literal "{home}") (literal "{home}/.codex"))\n')


def env(adir: Path) -> dict:
    return {"PATH": "/usr/bin:/bin", "HOME": str(adir), "CODEX_HOME": str(adir / "codex_home"),
            "TMPDIR": str(adir / "tmp"), "LANG": "en_US.UTF-8"}


def prepare(adir: Path, image_bytes: bytes, name: str) -> Path:
    """The attempt directory: codex_home (auth link only), tmp, w/<name> (the image), the sandbox profile."""
    (adir / "codex_home").mkdir(parents=True)
    (adir / "tmp").mkdir()
    (adir / "w").mkdir()
    (adir / "codex_home" / "auth.json").symlink_to(AUTH)
    (adir / "profile.sb").write_text(profile())
    img = adir / "w" / name
    img.write_bytes(image_bytes)
    return img


def flags(reader: dict) -> list[str]:
    out = ["-c", f'model="{reader["model"]}"']
    for c in CONFIG:
        out += ["-c", c.format(effort=reader["reasoning_effort"])]
    for f in DISABLE:
        out += ["--disable", f]
    return out


def boxed(adir: Path, argv: list[str], sandbox: bool = True) -> list[str]:
    return ([str(SANDBOX_EXEC), "-f", str(adir / "profile.sb")] if sandbox else []) + argv


def exec_argv(codex: list[str], reader: dict, adir: Path, img: Path, prompt: str) -> list[str]:
    return codex + ["exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
                    "-s", "read-only", "-C", str(adir / "w"), *flags(reader), "--json",
                    "-o", str(adir / "last.txt"), "-i", str(img), prompt]


def template_sha(reader: dict, prompt: str) -> str:
    """The exact command, with the attempt-specific paths as placeholders, and the sandbox profile."""
    a = Path("/ADIR")
    argv = exec_argv(["<codex>"], reader, a, a / "w" / "<image>", prompt)
    return sha(json.dumps({"argv": argv, "profile": profile(Path("/HOME")), "env": sorted(env(a))}).encode())


def gated(argv: list[str]) -> list[str]:
    """The worker waits for 'GO' on stdin before it execs the reader: an orchestrator that dies before the dispatch
    record is durable closes the pipe, and nothing is sent (exit 97)."""
    return ["/bin/sh", "-c", 'IFS= read -r go || exit 97; [ "$go" = GO ] || exit 97; exec "$@"', "airq", *argv]


def run_local(codex: list[str], adir: Path, args: list[str], sandbox: bool = True, timeout: float = 60) -> tuple:
    p = subprocess.run(boxed(adir, codex + args, sandbox), capture_output=True, env=env(adir), cwd=adir / "w",
                       timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def prompt_input(codex: list[str], reader: dict, adir: Path, img: Path, prompt: str, sandbox: bool = True) -> dict:
    rc, out, err = run_local(codex, adir, ["debug", "prompt-input", *flags(reader), "-i", str(img), prompt], sandbox)
    if rc != 0:
        raise SystemExit(f"refused: prompt-input receipt failed ({rc}): {err[-300:]!r}")
    items = json.loads(out)
    w = str(adir / "w")
    model_visible, images, user_text = [], [], []
    for m in items:
        kinds = (m.get("internal_chat_message_metadata_passthrough") or {}).get("content_item_kinds")
        for c in m.get("content", []):
            if c.get("type") == "input_image":
                url = c.get("image_url", "")
                b = base64.b64decode(url.split(",", 1)[1]) if url.startswith("data:") else b""
                images.append({"sha256": sha(b), "bytes": len(b), "detail": c.get("detail"),
                               "mime": url[5:url.find(";")] if url.startswith("data:") else None})
            elif m.get("role") == "user":
                user_text.append(c.get("text", "").replace(w, "<W>"))
            else:
                model_visible.append({"role": m.get("role"), "kinds": kinds, "text": c.get("text", "").replace(w, "<W>")})
    return {"instructions_sha256": sha(json.dumps(model_visible, sort_keys=True).encode()),
            "instruction_kinds": sorted({k for x in model_visible for k in (x["kinds"] or [])}),
            "user_text_sha256": sha(json.dumps(user_text).encode()), "user_text": user_text,
            "images": images, "rendered_bytes": len(out)}


def effective_features(codex: list[str], reader: dict, adir: Path, sandbox: bool = True) -> dict:
    rc, out, err = run_local(codex, adir, ["features", "list", *flags(reader)], sandbox)
    if rc != 0:
        raise SystemExit(f"refused: features list failed ({rc})")
    state = {}
    for line in out.decode().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            state[parts[0]] = parts[-1]
    bad = {f: state.get(f) for f in DISABLE if state.get(f) != "false" and f not in UNDISABLEABLE}
    if bad:
        raise SystemExit(f"refused: features not effectively off under the pinned flags: {bad}")
    return {"listed_sha256": sha(out), "disabled_effective_false": sum(state.get(f) == "false" for f in DISABLE),
            "cannot_be_disabled": {f: state.get(f) for f in UNDISABLEABLE}}


def auth_route(codex: list[str], adir: Path, sandbox: bool = True) -> str:
    rc, out, err = run_local(codex, adir, ["login", "status"], sandbox)
    line = (out + err).decode().strip().splitlines()
    text = line[0] if line else ""
    return re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+|sk-[\w-]+", "<redacted>", text)


def bounded(b: bytes, keep: int) -> dict:
    d = {"length": len(b), "sha256": sha(b)}
    if len(b) <= keep:
        d["text"] = b.decode("utf-8", "replace")
    else:
        d["head"] = b[:keep // 2].decode("utf-8", "replace")
        d["tail"] = b[-keep // 2:].decode("utf-8", "replace")
    return d


def bounded_answer(text: str | None) -> dict:
    if text is None:
        return {"answer": None, "answer_len": None, "answer_sha256": None, "overlength": False}
    over = len(text) > ANSWER_KEEP
    return {"answer": text[:ANSWER_KEEP] if over else text, "answer_len": len(text),
            "answer_sha256": sha(text.encode()), "overlength": over}


def parse_events(stdout: bytes) -> tuple[list[dict], list[str]]:
    events, problems = [], []
    for i, line in enumerate(stdout.decode("utf-8", "replace").splitlines()):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"line {i + 1}: not JSON")
            continue
        if not isinstance(e, dict) or not isinstance(e.get("type"), str):
            problems.append(f"line {i + 1}: not an event object")
            continue
        events.append(e)
    return events, problems


def isolation_problems(events: list[dict]) -> list[str]:
    bad = []
    for e in events:
        t = e["type"]
        if t not in BOOKKEEPING:
            bad.append(t)
        item = e.get("item")
        if item is not None and (not isinstance(item, dict) or item.get("type") not in ALLOWED_ITEM_TYPES):
            bad.append(f"item:{item.get('type') if isinstance(item, dict) else type(item).__name__}")
    return bad


def event_answer(events: list[dict]) -> str | None:
    msgs = [e["item"].get("text") for e in events if e["type"] == "item.completed"
            and isinstance(e.get("item"), dict) and e["item"].get("type") == "agent_message"]
    msgs = [m for m in msgs if isinstance(m, str)]
    return msgs[-1] if msgs else None


def lifecycle_complete(events: list[dict]) -> bool:
    types = [e["type"] for e in events]
    return bool(types) and types[0] == "thread.started" and "turn.started" in types and types[-1] == "turn.completed" \
        and event_answer(events) is not None


def classify(stdout: bytes, stderr: bytes, last_message: str | None, returncode: int | None, *, timed_out: bool,
             overflow: bool) -> dict:
    """The outcome of one attempt from its retained evidence (see the module docstring for the order)."""
    events, problems = parse_events(stdout)
    ev = {"events": bounded(stdout, EVENTS_KEEP), "stderr": bounded(stderr, STDERR_KEEP), "returncode": returncode,
          "timed_out": timed_out, "event_types": sorted({e["type"] for e in events}),
          "usage": next((e.get("usage") for e in reversed(events) if e["type"] == "turn.completed"), None)}
    answer = last_message if (last_message is not None and last_message.strip()) else event_answer(events)
    bad = isolation_problems(events)
    if bad:
        return {**ev, "outcome": "isolation_violation", "retained": True, "isolation_events": bad,
                **bounded_answer(answer)}
    if overflow:                                  # our cap cut the stream: its last line is incomplete by construction
        return {**ev, "outcome": "overflow", "retained": True, "isolation_events": [], **bounded_answer(answer)}
    if problems:
        return {**ev, "outcome": "isolation_violation", "retained": True, "isolation_events": problems,
                **bounded_answer(answer)}
    if answer is not None and (answer.strip() or event_answer(events) is not None):   # an empty agent message is
        ok = lifecycle_complete(events)                                                 # an answer too (ERR_EMPTY)
        return {**ev, "outcome": "ok" if ok else "isolation_violation", "retained": True,
                "isolation_events": [] if ok else ["incomplete lifecycle: isolation cannot be verified"],
                **bounded_answer(answer)}
    if STRUCTURAL.search(stderr.decode("utf-8", "replace")):
        return {**ev, "outcome": "structural_failure", "retained": False, "isolation_events": [],
                **bounded_answer(None)}
    return {**ev, "outcome": "provider_failure", "retained": False, "isolation_events": [], **bounded_answer(None)}


def no_image_answer(answer: str | None) -> bool:
    return bool(answer) and bool(NO_IMAGE.search(answer))
