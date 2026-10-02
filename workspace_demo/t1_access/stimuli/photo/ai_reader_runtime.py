"""AI image-reader qualification, revision 4: THE REQUEST BOUNDARY (Codex RSC 5a8d7ac closure 4; framework 8.2's isolation
evidence list and smoke rule). Standard library only. Nothing here sends a request by itself: `exec_argv` builds the one
command that does, and only `ai_reader_exec.run` starts it, after the go.

THE INPUT BOUNDARY IS AN ALLOWLIST (`profile`), enforced by macOS sandbox-exec on the reader process and every
descendant: (deny default), then only
  - process-exec of the pinned codex binary itself (no shell, no helper, no other program: unified_exec, which this CLI
    keeps on under every switch, has nothing it may launch - measured: /bin/sh, /bin/zsh and /bin/bash cannot even be
    stat'ed, and code-mode-host cannot be spawned);
  - file reads of: the attempt directory (the image under its opaque name, the private CODEX_HOME with the auth link,
    tmp, its own outputs), the auth file, the codex binary and its package manifest, and the system runtime (/System,
    /usr/lib, /usr/share, the dyld cache, the timezone database, /private/etc/ssl, localtime, a few /dev nodes, the
    directory "/" itself); file metadata only of those and of the attempt directory's ancestors;
  - file writes only inside the attempt directory and to the auth file (a token refresh);
  - network outbound (the request), sysctl reads, and eight named Mach services (TLS trust, Security, network
    configuration, DNS, directory lookups, notifications, logging) - no pasteboard, no file-serving service.
Everything else is denied wherever it resides: the key, the set, the scorer, the repositories, the human norms, other
attempt directories (sibling copies under /tmp), the orchestrator's temporary files, the home directory. Measured with
the real binary and no request (tests `Boundary`): --version, features list, debug prompt-input and login status run
under it; reading the key, a sibling attempt's file, /private/tmp and the home is denied; /bin/sh cannot be executed.

WHAT THE READER PROCESS GETS, per attempt: the pinned codex binary under that profile; a pinned five-variable
environment (`env`); a private CODEX_HOME holding only a symlink to the auth file (so --ignore-user-config and
--ignore-rules have nothing to ignore: measured "loaded rules from 0 files"); `--ephemeral --skip-git-repo-check
--ignore-user-config --ignore-rules -s read-only`, the CONFIG overrides (model, effort, read-only sandbox mode, web
search disabled, and the switches that drop the permissions, environment, collaboration-mode, apps and skills
instructions) and every tool-capable feature in DISABLE turned off - 32 requested, `features list` under the same flags
showing 31 false and unified_exec true (UNDISABLEABLE, measured); one working directory holding only the image; the
frozen PROMPT after a `--` separator; stdin /dev/null.

THE PROMPT SEPARATOR (revision 4, measured). `-i` takes several values: in revision 3's order (`-i <image> <prompt>`)
the CLI read the prompt as a second image path - debug prompt-input rendered "Codex could not read the local image at
`<prompt>`" and no prompt text, and exec read stdin for its prompt. `-i <image> -- <prompt>` renders the prompt.

RECEIPTS (no credential is read or recorded):
  - `prompt_input`: `codex debug prompt-input` with the same flags, profile, environment and separator renders the
    model-visible input locally: the non-user instructions (attempt directory written <W>) must hash to the package's
    pin, the embedded image to the request's frozen delivered digest, the normalised user text to the request's frozen
    hash.
  - `invocation_receipt`: the EXACT exec invocation, run once with the synthetic image under the same profile with ALL
    network denied by the kernel (nothing can leave), logs at the instant it would sample: its submitted user input
    (the image path and the prompt text, nothing else) and its effective configuration (model, effort, approval
    Never, sandbox ReadOnly without network, and every feature flag). Required: the user input is exactly [image,
    prompt]; every feature `features list` reports agrees with exec's own flag; model, effort and policies as pinned.
    What it cannot show without a request - the serialised request body (instructions and tool schema as sent) - is
    recorded as unobserved; the per-attempt prompt-input receipt covers the instructions as the CLI renders them.
  - `effective_features`, `auth_route` (`codex login status`, redacted): re-measured fresh in the scientific run.

PARSER AND CLASSIFICATION (fail closed; `parse_events`, `lifecycle`, `classify`):
  1. any event or item outside the bookkeeping set (a command, file, patch, MCP, web, plan, agent or other tool
     event) -> ISOLATION, retained, final - BEFORE any retry eligibility, whatever the exit status. An item of type
     'error' is a CLI notice only when its text is one of the frozen NOTICES (the code-mode-disabled notice, the
     transport fallback); any other is ISOLATION;
  2. stdout, stderr or the attempt directory over its cap -> OVERFLOW, retained, final (ERR_OVERLENGTH);
  3. any stdout line that is not a JSON object with a string type -> ISOLATION (malformed evidence);
  4. an answer received is LOCKED whatever the exit status. It is retained 'ok' only when the lifecycle is complete
     and ordered - thread.started once and first, turn.started once after it, each item id started at most once and
     completed exactly once, exactly one completed agent message, turn.completed once and last, no turn.failed, every
     bookkeeping payload well formed - and the event stream's message EQUALS the -o file's text; otherwise retained
     ISOLATION (evidence incomplete or contradictory);
  5. no answer and no agent message: STRUCTURAL when stderr matches a frozen configuration/authentication/image/sandbox
     pattern (the job holds), else PROVIDER_FAILURE (the only retryable outcome).
  An answer longer than ANSWER_KEEP characters is never cut silently (excerpt, original length and sha256, overlength).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

HOME = Path.home()
CODEX = Path("/opt/homebrew/Caskroom/codex/0.159.3/bin/codex")
CODEX_PACKAGE = CODEX.parents[1] / "codex-package.json"
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
AUTH = HOME / ".codex" / "auth.json"
DISABLE = ["apps", "browser_use", "browser_use_external", "browser_use_full_cdp_access", "computer_use",
           "code_mode_host", "shell_tool", "unified_exec", "unified_exec_tty", "shell_snapshot", "js_repl",
           "view_image", "image_generation", "tool_search", "tool_suggest", "multi_agent", "memories", "plugins",
           "plugin_sharing", "remote_plugin", "hooks", "goals", "sleep_tool", "skill_search",
           "skill_mcp_dependency_install", "tool_call_mcp_elicitation", "realtime_conversation", "in_app_browser",
           "in_app_local_automation", "worktrees", "workspace_dependencies", "write_stdin_approval"]
# Measured 2 October 2026 (`codex features list`, no request): unified_exec stays effectively true under
# --disable unified_exec, -c features.unified_exec=false and every other switch tried. The deprecated
# web_search_cached / web_search_request disables (revision 3) made exec emit two deprecation 'error' items; web search
# is disabled by configuration instead (`web_search="disabled"`), and both features read false.
UNDISABLEABLE = ["unified_exec"]
CONFIG = ['model_reasoning_effort="{effort}"', 'sandbox_mode="read-only"', 'web_search="disabled"',
          "include_permissions_instructions=false", "include_environment_context=false",
          "include_collaboration_mode_instructions=false", "include_apps_instructions=false",
          "skills.include_instructions=false", "skills.bundled.enabled=false"]
BOOKKEEPING = {"thread.started", "turn.started", "turn.completed", "turn.failed", "item.started", "item.updated",
               "item.completed", "error"}
ALLOWED_ITEM_TYPES = {"agent_message", "reasoning"}
NOTICES = ("Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable "
           "`features.code_mode_host` and install `codex-code-mode-host`.",)
NOTICE_PREFIXES = ("Falling back from WebSockets to HTTPS transport.",)
MACH = ["com.apple.trustd.agent", "com.apple.SecurityServer", "com.apple.SystemConfiguration.configd",
        "com.apple.dnssd.service", "com.apple.system.opendirectoryd.libinfo", "com.apple.system.notification_center",
        "com.apple.logd", "com.apple.diagnosticd"]
SYSTEM_READ = ['(subpath "/System")', '(subpath "/usr/lib")', '(subpath "/usr/share")',
               '(subpath "/private/var/db/timezone")', '(subpath "/private/var/db/dyld")', '(subpath "/private/etc/ssl")',
               '(literal "/private/etc/localtime")', '(literal "/dev/null")', '(literal "/dev/urandom")',
               '(literal "/dev/random")', '(literal "/dev/dtracehelper")', '(literal "/dev/autofs_nowait")',
               '(literal "/")']
ANSWER_KEEP = 2000                     # characters kept verbatim; longer = excerpt + length + sha256, ERR_OVERLENGTH
EVENTS_KEEP, STDERR_KEEP = 32768, 4096  # bytes of raw evidence retained per attempt; events beyond EVENTS_KEEP
                                       # cannot be retained completely and the attempt is OVERFLOW (ERR_OVERLENGTH)
STDOUT_CAP, STDERR_CAP = 1 << 20, 256 << 10   # bytes captured per attempt before the worker is killed (OVERFLOW)
LOCAL_CAP = 4 << 20                    # bytes captured from a local receipt command (features, prompt-input, ...)
STRUCTURAL = re.compile(r"(?i)(error loading config|unknown (feature|variant|field)|invalid value|unsupported image|"
                        r"invalid[_ ]image|image (could not|cannot) be|could not read the local image|not logged in|"
                        r"login required|unauthori[sz]ed|\b401\b|\b403\b|model[_ ]not[_ ]found|"
                        r"does not exist or you do not have access|sandbox-exec: |operation not permitted|"
                        r"no prompt provided)")
NO_IMAGE = re.compile(r"(?i)(no (image|picture|photo)|can(no|')t see (an|the|any) (image|picture)|"
                      r"(image|picture) (is|was) not (attached|provided|visible)|did ?n[o']t (attach|include|provide))")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _ancestors(p: Path) -> list[str]:
    out, q = [], p
    while q != q.parent:
        q = q.parent
        out.append(str(q))
    return out


def profile(adir: Path, home: Path = HOME, codex: Path = CODEX, network: bool = True) -> str:
    """The allowlist (see the module docstring). Paths are resolved: the sandbox matches /private/var, not /var."""
    a = str(Path(adir).resolve())
    auth = f"{home}/.codex/auth.json"
    reads = [f'(subpath "{a}")', f'(literal "{codex}")', f'(literal "{codex.parents[1]}/codex-package.json")',
             f'(literal "{auth}")'] + SYSTEM_READ
    meta = reads + [f'(literal "{p}")' for p in sorted(set(_ancestors(Path(a)) + _ancestors(codex) +
                                                             [str(home), f"{home}/.codex", "/var", "/tmp", "/etc"]))]
    return ("(version 1)\n(deny default)\n"
            f'(allow process-exec (literal "{codex}"))\n(allow process-fork)\n(allow signal (target self))\n'
            "(allow sysctl-read)\n(allow ipc-posix-shm)\n(allow system-socket)\n"
            + ("(allow network-outbound)\n" if network else "(deny network*)\n")
            + "(allow mach-lookup " + " ".join(f'(global-name "{m}")' for m in MACH) + ")\n"
            f"(allow file-read* {' '.join(reads)})\n"
            f"(allow file-read-metadata {' '.join(meta)})\n"
            f'(allow file-write* (subpath "{a}") (literal "{auth}") (literal "/dev/null") (literal "/dev/dtracehelper"))\n'
            '(allow file-ioctl (literal "/dev/dtracehelper"))\n')


def env(adir: Path) -> dict:
    return {"PATH": "/usr/bin:/bin", "HOME": str(adir), "CODEX_HOME": str(adir / "codex_home"),
            "TMPDIR": str(adir / "tmp"), "LANG": "en_US.UTF-8"}


def prepare(adir: Path, image_bytes: bytes, name: str) -> Path:
    """The attempt directory: codex_home (auth link only), tmp, w/<name> (the image), the sandbox profile."""
    (adir / "codex_home").mkdir(parents=True)
    (adir / "tmp").mkdir()
    (adir / "w").mkdir()
    (adir / "codex_home" / "auth.json").symlink_to(AUTH)
    (adir / "profile.sb").write_text(profile(adir))
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


def boxed(adir: Path, argv: list[str], sandbox: bool = True, prof: str = "profile.sb") -> list[str]:
    return ([str(SANDBOX_EXEC), "-f", str(adir / prof)] if sandbox else []) + argv


def exec_argv(codex: list[str], reader: dict, adir: Path, img: Path, prompt: str) -> list[str]:
    return codex + ["exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
                    "-s", "read-only", "-C", str(adir / "w"), *flags(reader), "--json",
                    "-o", str(adir / "last.txt"), "-i", str(img), "--", prompt]


def template_sha(reader: dict, prompt: str) -> str:
    """The exact command, with the attempt-specific paths as placeholders, the sandbox profile and the gate."""
    a = Path("/ADIR")
    argv = exec_argv(["<codex>"], reader, a, a / "w" / "<image>", prompt)
    return sha(json.dumps({"argv": argv, "profile": profile(Path("/ADIR"), Path("/HOME"), Path("/CODEX/bin/codex")),
                           "env": sorted(env(a)), "gate": gated(["<argv>"])}).encode())


def gated(argv: list[str]) -> list[str]:
    """The worker waits for 'GO' on stdin before it execs the reader (stdin then /dev/null): an orchestrator that dies
    before the dispatch record is durable closes the pipe, and nothing is sent (exit 97)."""
    return ["/bin/sh", "-c", 'IFS= read -r go || exit 97; [ "$go" = GO ] || exit 97; exec "$@" </dev/null', "airq",
            *argv]


def run_local(codex: list[str], adir: Path, args: list[str], sandbox: bool = True, timeout: float = 60,
              cap: int = LOCAL_CAP, extra_env: dict | None = None, prof: str = "profile.sb") -> tuple:
    """A local receipt command under the attempt's profile, its output captured to files with a size cap (the
    process group is killed past the cap or the timeout)."""
    so, se = adir / f".local_{os.getpid()}_out", adir / f".local_{os.getpid()}_err"
    with open(so, "wb") as fo, open(se, "wb") as fe:
        p = subprocess.Popen(boxed(adir, codex + args, sandbox, prof), stdout=fo, stderr=fe,
                             env={**env(adir), **(extra_env or {})}, cwd=adir / "w", stdin=subprocess.DEVNULL,
                             start_new_session=True)
        t = time.monotonic()
        while p.poll() is None:
            if time.monotonic() - t > timeout or so.stat().st_size > cap or se.stat().st_size > cap:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                p.wait()
                break
            time.sleep(0.02)
    out, err = so.read_bytes()[:cap], se.read_bytes()[:cap]
    so.unlink()
    se.unlink()
    return p.returncode, out, err


def prompt_input(codex: list[str], reader: dict, adir: Path, img: Path, prompt: str, sandbox: bool = True) -> dict:
    rc, out, err = run_local(codex, adir, ["debug", "prompt-input", *flags(reader), "-i", str(img), "--", prompt],
                             sandbox)
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
                user_text.append(c.get("text", "").replace(w, "<W>").replace(str(Path(w).resolve()), "<W>"))
            else:
                model_visible.append({"role": m.get("role"), "kinds": kinds, "text": c.get("text", "").replace(w, "<W>")})
    return {"instructions_sha256": sha(json.dumps(model_visible, sort_keys=True).encode()),
            "instruction_kinds": sorted({k for x in model_visible for k in (x["kinds"] or [])}),
            "user_text_sha256": sha(json.dumps(user_text).encode()), "user_text": user_text,
            "prompt_rendered": bool(user_text) and user_text[-1] == prompt,
            "images": images, "rendered_bytes": len(out)}


def features_state(codex: list[str], reader: dict, adir: Path, sandbox: bool = True) -> dict:
    rc, out, err = run_local(codex, adir, ["features", "list", *flags(reader)], sandbox)
    if rc != 0:
        raise SystemExit(f"refused: features list failed ({rc})")
    state = {}
    for line in out.decode().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            state[parts[0]] = parts[-1]
    return {"state": state, "listed_sha256": sha(out)}


def effective_features(codex: list[str], reader: dict, adir: Path, sandbox: bool = True) -> dict:
    fs = features_state(codex, reader, adir, sandbox)
    state = fs["state"]
    bad = {f: state.get(f) for f in DISABLE if state.get(f) != "false" and f not in UNDISABLEABLE}
    if bad:
        raise SystemExit(f"refused: features not effectively off under the pinned flags: {bad}")
    off = [f for f in DISABLE if state.get(f) == "false"]
    return {"listed_sha256": fs["listed_sha256"], "requested_disabled": len(DISABLE),
            "disabled_effective_false": len(off), "web_search": {k: state.get(k) for k in
                                                                 ("web_search_cached", "web_search_request")},
            "cannot_be_disabled": {f: state.get(f) for f in UNDISABLEABLE}}


def auth_route(codex: list[str], adir: Path, sandbox: bool = True) -> str:
    rc, out, err = run_local(codex, adir, ["login", "status"], sandbox)
    line = (out + err).decode().strip().splitlines()
    text = line[0] if line else ""
    return re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+|sk-[\w-]+", "<redacted>", text)


# exec's sampling-time tag map has no 'feature.multi_agent' entry; it carries the CLI feature's two variants, which
# must both read false (measured: features list multi_agent false; exec multi_agent_mode false, multi_agent_v2 false).
EXEC_TAG_ALIASES = {"multi_agent": ["multi_agent_mode", "multi_agent_v2"]}
_SUBMISSION = re.compile(r"TurnInput \{ request: TurnInputRequest \{ input: UserInput \{ content: \[(.*?)\], client_id")
_FEEDBACK = re.compile(r'feedback_tags: model="([^"]*)" approval_policy=(\S+) sandbox_policy=(.*?) effort=(\S+) '
                       r'auth_mode=\S+ tags_json=(\{[^{}]*\})')


def invocation_receipt(codex: list[str], reader: dict, adir: Path, img: Path, prompt: str,
                       wait_s: float = 20.0) -> dict:
    """The EXACT exec invocation under the attempt profile with ALL network denied (nothing can leave): its logged
    submitted input and its effective configuration at the sampling instant, compared with `features list` under the
    same flags. Only the parsed fields are kept (the log carries account identifiers; it is discarded)."""
    (adir / "nonet.sb").write_text(profile(adir, network=False))
    argv = exec_argv(codex, reader, adir, img, prompt)
    rust_log = "warn,codex_core::session::handlers=debug,feedback_tags=info"
    so, se = adir / ".inv_out", adir / ".inv_err"
    with open(so, "wb") as fo, open(se, "wb") as fe:
        p = subprocess.Popen(boxed(adir, argv, True, "nonet.sb"), stdout=fo, stderr=fe,
                             env={**env(adir), "RUST_LOG": rust_log}, cwd=adir / "w", stdin=subprocess.DEVNULL,
                             start_new_session=True)
        t, sub, fb = time.monotonic(), None, None
        while time.monotonic() - t < wait_s and p.poll() is None:
            txt = se.read_bytes()[:LOCAL_CAP].decode("utf-8", "replace")
            sub, fb = _SUBMISSION.search(txt), _FEEDBACK.search(txt)
            if sub and fb:
                break
            time.sleep(0.1)
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait()
    txt = se.read_bytes()[:LOCAL_CAP].decode("utf-8", "replace")
    so.unlink()
    se.unlink()
    sub, fb = _SUBMISSION.search(txt), _FEEDBACK.search(txt)
    if not (sub and fb):
        raise SystemExit("refused: the exec invocation receipt could not be read (no submission or sampling log)")
    content = sub.group(1)
    rimg = str(Path(img).resolve()) if str(Path(img).resolve()) in content else str(img)
    want_items = f'LocalImage {{ path: "{rimg}", detail: None }}, Text {{ text: {json.dumps(prompt)}, ' \
                 f'text_elements: [] }}'
    tags = json.loads(fb.group(5))
    exec_features = {k[len("feature."):]: v for k, v in tags.items() if k.startswith("feature.")}
    listed = features_state(codex, reader, adir)["state"]
    disagree = sorted(f for f, v in listed.items() if f in exec_features and exec_features[f] != v)
    missing = sorted(f for f in DISABLE if f not in exec_features and not
                     (f in EXEC_TAG_ALIASES and all(exec_features.get(g) == "false" for g in EXEC_TAG_ALIASES[f])))
    out = {"user_input_exact": content == want_items, "model": fb.group(1), "approval_policy": fb.group(2),
           "sandbox_policy": fb.group(3).strip(), "effort": fb.group(4),
           "features_compared": len(set(listed) & set(exec_features)), "features_disagreeing": disagree,
           "disabled_missing_from_exec": missing,
           "exec_disabled_false": sum(exec_features.get(f) == "false" or
                                      (f not in exec_features and f in EXEC_TAG_ALIASES) for f in DISABLE),
           "aliases_used": {f: {g: exec_features.get(g) for g in EXEC_TAG_ALIASES[f]} for f in EXEC_TAG_ALIASES
                            if f not in exec_features},
           "exec_unified_exec": exec_features.get("unified_exec"),
           "tags_sha256": sha(json.dumps(tags, sort_keys=True).encode()),
           "unobserved": "the serialised request body (instructions and tool schema as sent) - not observable "
                         "without a request; the prompt-input receipt covers the instructions as rendered"}
    ok = (out["user_input_exact"] and out["model"] == reader["model"] and out["approval_policy"] == "Never" and
          out["sandbox_policy"] == "ReadOnly { network_access: false }" and
          out["effort"] == f"Some({reader['reasoning_effort'].capitalize()})" and not disagree and not missing)
    out["equivalent"] = ok
    return out


def bounded(b: bytes, keep: int) -> dict:
    """Retained evidence: the complete text when it fits (exact = it decodes losslessly, so its length and sha256
    can be checked against it), else head and tail with the original length and sha256."""
    d = {"length": len(b), "sha256": sha(b)}
    if len(b) <= keep:
        d["text"] = b.decode("utf-8", "replace")
        d["exact"] = d["text"].encode("utf-8") == b
    else:
        d["head"] = b[:keep // 2].decode("utf-8", "replace")
        d["tail"] = b[-keep // 2:].decode("utf-8", "replace")
        d["exact"] = False
    return d


def retained_text(d: dict) -> str:
    return d["text"] if "text" in d else d["head"] + "\n" + d["tail"]


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


def is_notice(item: dict) -> bool:
    m = item.get("message")
    return item.get("type") == "error" and isinstance(m, str) and (m in NOTICES or m.startswith(NOTICE_PREFIXES))


def isolation_problems(events: list[dict]) -> list[str]:
    bad = []
    for e in events:
        t = e["type"]
        if t not in BOOKKEEPING:
            bad.append(t)
        item = e.get("item")
        if item is not None:
            if not isinstance(item, dict):
                bad.append(f"item:{type(item).__name__}")
            elif item.get("type") not in ALLOWED_ITEM_TYPES and not is_notice(item):
                bad.append(f"item:{item.get('type')}")
    return bad


def event_answer(events: list[dict]) -> str | None:
    msgs = [e["item"].get("text") for e in events if e["type"] == "item.completed"
            and isinstance(e.get("item"), dict) and e["item"].get("type") == "agent_message"]
    msgs = [m for m in msgs if isinstance(m, str)]
    return msgs[-1] if msgs else None


def lifecycle(events: list[dict]) -> list[str]:
    """Problems with the ordered, unique lifecycle; [] when complete (see the module docstring, rule 4)."""
    p = []
    types = [e["type"] for e in events]
    if not types or types[0] != "thread.started" or types.count("thread.started") != 1:
        p.append("thread.started not once and first")
    if types.count("turn.started") != 1 or "thread.started" not in types or \
            types.index("turn.started") < types.index("thread.started"):
        p.append("turn.started not once after thread.started")
    if types.count("turn.completed") != 1 or not types or types[-1] != "turn.completed":
        p.append("turn.completed not once and last")
    if "turn.failed" in types:
        p.append("turn.failed present")
    if not isinstance(events[0].get("thread_id") if events else None, str):
        p.append("thread.started without a thread_id")
    started, completed = {}, {}
    ts = types.index("turn.started") if "turn.started" in types else len(types)
    for i, e in enumerate(events):
        it = e.get("item")
        if e["type"].startswith("item."):
            if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not isinstance(it.get("type"), str):
                p.append(f"event {i + 1}: malformed item")
                continue
            if i < ts and not is_notice(it):
                p.append(f"event {i + 1}: item before turn.started")
            if e["type"] == "item.started":
                if it["id"] in started or it["id"] in completed:
                    p.append(f"item {it['id']} started twice or after completion")
                started[it["id"]] = i
            elif e["type"] == "item.updated":
                if it["id"] in completed:
                    p.append(f"item {it['id']} updated after completion")
            elif e["type"] == "item.completed":
                if it["id"] in completed:
                    p.append(f"item {it['id']} completed twice")
                completed[it["id"]] = i
                if it["type"] == "agent_message" and not isinstance(it.get("text"), str):
                    p.append(f"item {it['id']}: agent message without text")
    if [i for i in started if i not in completed]:
        p.append("an item started and never completed")
    n_msgs = sum(1 for e in events if e["type"] == "item.completed" and isinstance(e.get("item"), dict)
                 and e["item"].get("type") == "agent_message")
    if n_msgs != 1:
        p.append(f"{n_msgs} completed agent messages, not exactly one")
    tc = [e for e in events if e["type"] == "turn.completed"]
    if tc and not isinstance(tc[-1].get("usage"), dict):
        p.append("turn.completed without usage")
    return p


def lifecycle_complete(events: list[dict]) -> bool:
    return not lifecycle(events)


def classify(stdout: bytes, stderr: bytes, last_message: str | None, returncode: int | None, *, timed_out: bool,
             overflow: bool) -> dict:
    """The outcome of one attempt from its retained evidence (see the module docstring for the order)."""
    events, problems = parse_events(stdout)
    ev = {"events": bounded(stdout, EVENTS_KEEP), "stderr": bounded(stderr, STDERR_KEEP), "returncode": returncode,
          "timed_out": timed_out, "event_types": sorted({e["type"] for e in events}),
          "notices": sorted({e["item"]["message"][:120] for e in events if isinstance(e.get("item"), dict)
                             and is_notice(e["item"])}),
          "usage": next((e.get("usage") for e in reversed(events) if e["type"] == "turn.completed"), None)}
    ea = event_answer(events)
    file_answer = last_message if last_message is not None else None
    answer = ea if ea is not None else (file_answer if file_answer is not None and file_answer.strip() else None)
    ev["file_answer_sha256"] = sha(file_answer.encode()) if file_answer is not None else None
    bad = isolation_problems(events)
    if bad:
        return {**ev, "outcome": "isolation_violation", "retained": True, "isolation_events": bad,
                **bounded_answer(answer)}
    if overflow or len(stdout) > EVENTS_KEEP:     # a cap cut the stream, or the events cannot be retained completely
        return {**ev, "outcome": "overflow", "retained": True, "isolation_events": [], **bounded_answer(answer)}
    if problems:
        return {**ev, "outcome": "isolation_violation", "retained": True, "isolation_events": problems,
                **bounded_answer(answer)}
    if answer is not None:
        why = lifecycle(events)
        if ea is not None and file_answer is not None and file_answer != ea:
            why.append("the event stream's message differs from the -o answer")
        if ea is not None and file_answer is None:
            why.append("an event answer without the -o answer file")
        if ea is None:
            why.append("an -o answer without an agent message in the event stream")
        return {**ev, "outcome": "ok" if not why else "isolation_violation", "retained": True,
                "isolation_events": [] if not why else ["evidence incomplete or contradictory: " + "; ".join(why)],
                **bounded_answer(answer)}
    if STRUCTURAL.search(retained_text(ev["stderr"])):
        return {**ev, "outcome": "structural_failure", "retained": False, "isolation_events": [],
                **bounded_answer(None)}
    return {**ev, "outcome": "provider_failure", "retained": False, "isolation_events": [], **bounded_answer(None)}


def no_image_answer(answer: str | None) -> bool:
    return bool(answer) and bool(NO_IMAGE.search(answer))
