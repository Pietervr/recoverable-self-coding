"""A synthetic stand-in for the codex binary in the AI-reader mechanism fixtures (no model, no network, no image is
looked at). The fixture root (three levels above HOME, i.e. <root>/attempts/<tmp>/a) holds fake_plan.json:
{"<request>": ["<behaviour>", ...]} - the n-th call for a request takes the n-th behaviour (the last repeats) - and
each exec call appends {request, behaviour, pid} to dispatch_log.jsonl there.

Behaviours: ok:<answer> | ok_exit1:<answer> | slow_ok:<seconds>:<answer> | arg0churn:<seconds>:<answer> | fail | structural | tool | tool_exit1 |
malformed | no_events:<answer> | long | multiline | noimage | block (ignores SIGTERM) | flood (> 1 MiB stdout) |
quickflood (> 1 MiB stdout, then exit at once) | orphanchild:<answer> (a child ignoring SIGTERM outlives the answer) |
escape:<answer> (a child leaves the group and persists) | notice:<answer> (the frozen code-mode notice first) | unknown_error:<answer> | two_messages | mismatch (-o differs) |
completed_not_last | item_without_id | promptfail (debug prompt-input fails) - FAKE_PROMPT_FAIL=1 in the environment
of the fixture also makes prompt-input fail.
"""

import base64
import json
import os
import signal
import sys
import time
from pathlib import Path

args = sys.argv[1:]
FEATURES = ["apps", "browser_use", "browser_use_external", "browser_use_full_cdp_access", "computer_use",
            "code_mode_host", "shell_tool", "unified_exec", "unified_exec_tty", "shell_snapshot", "js_repl",
            "view_image", "image_generation", "tool_search", "tool_suggest", "web_search_request", "web_search_cached",
            "multi_agent", "memories", "plugins", "plugin_sharing", "remote_plugin", "hooks", "goals", "sleep_tool",
            "skill_search", "skill_mcp_dependency_install", "tool_call_mcp_elicitation", "realtime_conversation",
            "in_app_browser", "in_app_local_automation", "worktrees", "workspace_dependencies", "write_stdin_approval",
            "in_app_updates", "daemon_auto_start", "unified_exec_zsh_fork"]     # reader revision 13's three disables


def opt(name):
    return args[args.index(name) + 1] if name in args else None


if args[:1] == ["--version"]:
    print("codex-cli 0.159.3")
    sys.exit(0)
if args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT", file=sys.stderr)
    sys.exit(0)
if args[:2] == ["features", "list"]:
    for f in FEATURES:
        print(f"{f:40} stable             false")
    sys.exit(0)
if args[:2] == ["debug", "prompt-input"]:
    img = Path(opt("-i"))
    if (Path(os.environ["HOME"]).parents[2] / "PROMPT_FAIL").exists():
        print("prompt-input failed (fixture)", file=sys.stderr)
        sys.exit(2)
    b64 = base64.b64encode(img.read_bytes()).decode()
    meta = {"internal_chat_message_metadata_passthrough": {"content_item_kinds": ["multi_agent.role_instructions"]}}
    out = [{"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "<fake role>"}], **meta},
           {"type": "message", "role": "user", "content": [
               {"type": "input_text", "text": f'<image name=[Image #1] path="{img}">'},
               {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"},
               {"type": "input_text", "text": "</image>"}, {"type": "input_text", "text": args[-1]}]}]
    print(json.dumps(out))
    sys.exit(0)
assert args[0] == "exec", args
root = Path(os.environ["HOME"]).parents[2]
img = Path(opt("-i"))
request = img.stem
plan = json.loads((root / "fake_plan.json").read_text())
log = root / "dispatch_log.jsonl"
n = sum(1 for line in log.read_text().splitlines() if json.loads(line)["request"] == request) if log.exists() else 0
seq = plan.get(request, ["ok:thing"])
b = seq[min(n, len(seq) - 1)]
with open(log, "a") as fh:
    fh.write(json.dumps({"request": request, "behaviour": b, "pid": os.getpid()}) + "\n")
    fh.flush()
    os.fsync(fh.fileno())
last = Path(opt("-o"))


def ev(t, **kw):
    print(json.dumps({"type": t, **kw}), flush=True)


NOTICE = ("Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable "
          "`features.code_mode_host` and install `codex-code-mode-host`.")


def answer(text, code=0, tool=False, pre=None, file_text=None, extra=None, last_event=True):
    ev("thread.started", thread_id="t")
    for x in pre or []:
        ev("item.completed", item=x)
    ev("turn.started")
    ev("item.completed", item={"id": "r", "type": "reasoning", "text": "..."})
    if tool:
        ev("item.completed", item={"id": "c", "type": "command_execution", "command": "cat key"})
    ev("item.completed", item={"id": "m", "type": "agent_message", "text": text})
    for x in extra or []:
        ev(x["type"], **{k: v for k, v in x.items() if k != "type"})
    last.write_text(text if file_text is None else file_text)
    if last_event:
        ev("turn.completed", usage={"input_tokens": 900, "output_tokens": 3})
    else:
        ev("turn.completed", usage={"input_tokens": 900, "output_tokens": 3})
        ev("item.completed", item={"id": "late", "type": "reasoning", "text": "late"})
    sys.exit(code)


kind, _, rest = b.partition(":")
if kind == "ok":
    answer(rest)
if kind == "ok_exit1":
    answer(rest, 1)
if kind == "slow_ok":
    secs, _, text = rest.partition(":")
    time.sleep(float(secs))
    answer(text)
if kind == "arg0churn":                      # revision 11: like the real CLI, create and remove its own arg0 helper
    secs, _, text = rest.partition(":")      # entries in CODEX_HOME for <secs>, as fast as it can, then answer
    import shutil
    home = Path(os.environ["CODEX_HOME"]) / "tmp" / "arg0"
    end, n = time.monotonic() + float(secs), 0
    while time.monotonic() < end:
        d = home / f"codex-arg0{n:06d}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "applypatch").write_bytes(b"x" * 4096)
        os.symlink(d / "applypatch", d / "apply_patch")
        shutil.rmtree(d)
        n += 1
    answer(text)
if kind == "fail":
    ev("thread.started", thread_id="t")
    print("stream disconnected before completion: 503", file=sys.stderr)
    sys.exit(1)
if kind == "structural":
    print("Error loading config: invalid value for model", file=sys.stderr)
    sys.exit(1)
if kind == "tool":
    answer("thing", tool=True)
if kind == "tool_exit1":
    ev("thread.started", thread_id="t")
    ev("item.completed", item={"id": "c", "type": "command_execution", "command": "cat key"})
    sys.exit(1)
if kind == "malformed":
    print("this is not json", flush=True)
    answer("thing")
if kind == "no_events":
    last.write_text(rest)
    sys.exit(0)
if kind == "long":
    answer("thing " * 600)
if kind == "multiline":
    answer("thing\nIt is a thing")
if kind == "noimage":
    answer("There is no image attached.")
if kind == "block":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(600)
if kind == "quickflood":
    ev("thread.started", thread_id="t")
    sys.stdout.write("x" * (2 << 20))
    sys.stdout.flush()
    sys.exit(0)
if kind == "orphanchild":
    import subprocess
    c = subprocess.Popen([sys.executable, "-c", "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                                                "time.sleep(600)"])
    with open(root / "orphan.pid", "w") as fh:
        fh.write(str(c.pid))
    time.sleep(1.5)                                # sampled as a member before the leader answers and exits
    answer(rest)
if kind == "escape":                               # a child that leaves the group, recorded, then the leader answers
    import subprocess
    c = subprocess.Popen([sys.executable, "-c", "import os, time; time.sleep(0.3); os.setsid(); time.sleep(600)"])
    with open(root / "escaped.pid", "w") as fh:
        fh.write(str(c.pid))
    time.sleep(1.6)                                # sampled as a member (by parent chain) before the answer
    answer(rest)
if kind == "notice":
    answer(rest, pre=[{"id": "n0", "type": "error", "message": NOTICE}])
if kind == "unknown_error":
    answer(rest, pre=[{"id": "n0", "type": "error", "message": "something else went wrong"}])
if kind == "two_messages":
    answer("thing", extra=[{"type": "item.completed", "item": {"id": "m2", "type": "agent_message", "text": "other"}}])
if kind == "mismatch":
    answer("thing", file_text="something else")
if kind == "completed_not_last":
    answer("thing", last_event=False)
if kind == "item_without_id":
    ev("thread.started", thread_id="t")
    ev("turn.started")
    ev("item.completed", item={"type": "agent_message", "text": "thing"})
    last.write_text("thing")
    ev("turn.completed", usage={"input_tokens": 1, "output_tokens": 1})
    sys.exit(0)
if kind == "flood":
    ev("thread.started", thread_id="t")
    sys.stdout.write("x" * (2 << 20))
    sys.stdout.flush()
    time.sleep(600)
sys.exit(3)
