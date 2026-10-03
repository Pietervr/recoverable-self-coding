"""A synthetic worker for the controller fixtures (no model, no development input). Usage: fake_worker.py <out> <mode>
  gates:ok | gates:hold | gates:refuse      the gates worker: GATES.json passed (exit 0), a hold (exit 4), a refusal
  sgates:<how>   revision 16: the supplement's gates worker, the same three outcomes in SUPPLEMENT_GATES.json
  sok:<phase>:<id>  supplement rev 2: start and commit <id> in a real supplement ledger (carry 194/193/1/194), then
                 write <PHASE>_DONE.json and exit 0
  sreceipt:<how> revision 16: the supplement's receipt worker: ok (outcome PASS unless SUPPLEMENT_TERMINAL.json exists),
                 stopped (outcome STOPPED), extra_key (one more field), bad_hash (a bound output's hash wrong)
  ok:<phase>     write <PHASE>_DONE.json and exit 0; first checks it cannot take the task lock (the controller must
                 hold it) and records that
  report:<how>   the report worker: ok (both figures, md, json, then the receipt last, exact schema); json_then_fail
                 (machine JSON written, then a failure before the receipt); bad_receipt (a receipt whose output hash is
                 wrong); other_session (a receipt naming another session); trimmed (figures and Markdown removed and
                 the receipt consistently trimmed to the machine JSON); extra_key (a receipt with one more field);
                 flag_mismatch (the receipt's validator flag differs from the machine report's); fail (exit 1 at once)
  block          ignore SIGTERM and sleep in C (time.sleep) - only SIGKILL ends it
  mlxblock       ignore SIGTERM and loop 4096 x 4096 MLX matmuls on the GPU
  family         spawn a grandchild that sleeps, then block (the process group must die together)
  orphanchild    spawn a child that ignores SIGTERM and sleeps, write the phase record, exit 0 (leader first)
  escape         spawn a child that leaves the process group (setsid) after 1 s, write the record, exit 0 after 2 s
  spike_exit     touch 1 GiB of host memory and exit at once (faster than a sample): the exit peak must be read
  fill:<bytes>   write <bytes> into the output tree, then block
  alloc:<gib>    touch <gib> GiB of host memory and hold it
  late_alloc:<s>:<gib>  idle <s>, then touch <gib> GiB and hold it (rev 12)
  exit:<code>    exit with that code
  norecord       exit 0 without writing the phase record
  linger:<phase>:<s>  write the phase record, then linger <s> before exit 0 (a slow teardown; rev 11)
"""

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

out, mode = Path(sys.argv[1]), sys.argv[2]
session = os.environ.get("STAGE_A_SESSION", "test")
gates = json.loads(os.environ.get("STAGE_A_GATES") or "{}")


def put(rel: str, b: bytes) -> str:
    p = out / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)
    return hashlib.sha256(b).hexdigest()


if mode.startswith("gates:"):
    how = mode.split(":")[1]
    if how == "refuse":
        sys.exit("refused: fixture refusal")
    rec = {"session": session, "package": {"criteria_sha256": "a" * 64}, "identity": "f" * 64,
           "passed": how == "ok", "hold": how == "hold", "hold_reason": "fixture hold" if how == "hold" else None}
    put("GATES.json", json.dumps(rec).encode())
    sys.exit(0 if how == "ok" else 4)
if mode.startswith("sgates:"):                 # revision 16: the supplement's gates (SUPPLEMENT_GATES.json)
    how = mode.split(":")[1]
    if how == "refuse":
        sys.exit("refused: fixture refusal")
    rec = {"session": session, "package": {"supplement_plan_sha256": "b" * 64}, "identity": "e" * 64,
           "passed": how == "ok", "hold": how == "hold", "hold_reason": "fixture hold" if how == "hold" else None}
    put("SUPPLEMENT_GATES.json", json.dumps(rec).encode())
    sys.exit(0 if how == "ok" else 4)
if mode.startswith("sok:"):                    # supplement rev 2: a real ledger start + commit, then the phase record
    _, ph, aid = mode.split(":")
    from enforce import Budget
    with open(out / "worker_log.jsonl", "a") as f:
        f.write(json.dumps({"phase": ph, "pid": os.getpid(), "t": time.time()}) + "\n")
    b = Budget(out / "stage_a_state.json", "row20", "e" * 64, [out], session,
               carry_in={"started": 194, "completed": 193, "failed": 1, "passes": 194})
    with b.attempt(aid, ph, passes=1) as att:
        att.commit({})
    (out / f"{ph.upper()}_DONE.json").write_text("{}")
    sys.exit(0)
if mode.startswith("sreceipt:"):               # revision 16: the supplement's receipt worker
    how = mode.split(":")[1]
    with open(out / "worker_log.jsonl", "a") as f:
        f.write(json.dumps({"phase": "supplement_receipt", "pid": os.getpid(), "t": time.time()}) + "\n")
    terminal = (out / "SUPPLEMENT_TERMINAL.json").exists()
    outputs = {"supplement/comparison_a.json": put("supplement/comparison_a.json", b'{"pass": true}')}
    if how == "bad_hash":
        outputs["supplement/comparison_a.json"] = "0" * 64
    rc = {"session": session, "package": gates.get("package"), "identity": gates.get("identity"),
          "date": time.strftime("%Y-%m-%d"), "outcome": "STOPPED" if (terminal or how == "stopped") else "PASS",
          "admissible": gates.get("passed") is True, "reasons": [], "input": {}, "attempts": {}, "comparisons": {},
          "counters": {}, "compatibility": {}, "outputs": outputs}
    if how == "extra_key":
        rc["note"] = "x"
    put("supplement/SUPPLEMENT_RECEIPT.json", json.dumps(rc).encode())
    sys.exit(0)
if mode.startswith("ok:"):
    from stage_a_guard import TaskLock
    try:
        TaskLock(out)
        held = False
    except SystemExit:
        held = True
    ph = mode.split(":")[1]
    with open(out / "worker_log.jsonl", "a") as f:
        f.write(json.dumps({"phase": ph, "pid": os.getpid(), "lock_held_by_controller": held,
                            "gates": gates.get("passed"), "t": time.time()}) + "\n")
    (out / f"{ph.upper()}_DONE.json").write_text("{}")
    sys.exit(0)
if mode.startswith("linger:"):                 # revision 11: complete and commit, then a slow teardown before exit
    _, ph, secs = mode.split(":")
    with open(out / "worker_log.jsonl", "a") as f:
        f.write(json.dumps({"phase": ph, "pid": os.getpid(), "t": time.time()}) + "\n")
    (out / f"{ph.upper()}_DONE.json").write_text("{}")
    (out / "teardown.pid").write_text(str(os.getpid()))   # the fixture watchdog's proc_info stops answering for it
    time.sleep(float(secs))
    sys.exit(0)
if mode.startswith("report:"):
    how = mode.split(":")[1]
    if how == "fail":
        sys.exit(1)
    with open(out / "worker_log.jsonl", "a") as f:
        f.write(json.dumps({"phase": "report", "pid": os.getpid(), "t": time.time()}) + "\n")
    outputs = {"report/rel_l2_by_layer.svg": put("report/rel_l2_by_layer.svg", b"<svg/>"),
               "report/logit_max_abs.svg": put("report/logit_max_abs.svg", b"<svg></svg>"),
               "report/STAGE_A_REPORT.md": put("report/STAGE_A_REPORT.md", b"# report\n")}
    from stage_a_guard import terminal_active          # revision 11: as the real report - an owner-released terminal
    rec = {"validator_pass": not terminal_active(out), "admissible": gates.get("passed") is True,
           "session": session}
    outputs["report/stage_a_report.json"] = put("report/stage_a_report.json", json.dumps(rec).encode())
    if how == "json_then_fail":
        sys.exit(1)
    if how == "bad_receipt":
        outputs["report/STAGE_A_REPORT.md"] = "0" * 64
    if how == "trimmed":
        for rel in ("report/rel_l2_by_layer.svg", "report/logit_max_abs.svg", "report/STAGE_A_REPORT.md"):
            (out / rel).unlink()
            outputs.pop(rel)
    rc = {"session": "another" if how == "other_session" else session, "package": gates.get("package"),
          "identity": gates.get("identity"), "date": time.strftime("%Y-%m-%d"), "outputs": outputs,
          "admissible": rec["admissible"], "validator_pass": rec["validator_pass"]}
    if how == "extra_key":
        rc["note"] = "x"
    if how == "flag_mismatch":
        rc["validator_pass"] = not rec["validator_pass"]
    put("report/REPORT_RECEIPT.json", json.dumps(rc).encode())
    sys.exit(0)
if mode in ("block", "family"):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if mode == "family":
        c = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
        (out / "grandchild.pid").write_text(str(c.pid))
    time.sleep(600)
if mode == "mlxblock":                       # busy in MLX/Metal work, SIGTERM ignored (synthetic arrays)
    import mlx.core as mx
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    a = mx.random.normal((4096, 4096))
    (out / "mlx_started").write_text("1")
    while True:
        a = (a @ a) / 4096.0
        mx.eval(a)
if mode == "orphanchild":
    c = subprocess.Popen([sys.executable, "-c", "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                                                "time.sleep(600)"])
    (out / "child.pid").write_text(str(c.pid))
    time.sleep(0.5)                          # long enough to be sampled as a member
    (out / "INSTRUMENTED_DONE.json").write_text("{}")
    os._exit(0)                              # the leader exits first; the child survives it
if mode == "escape":
    c = subprocess.Popen([sys.executable, "-c", "import os, time; time.sleep(1.0); os.setsid(); time.sleep(600)"])
    (out / "child.pid").write_text(str(c.pid))
    time.sleep(2.0)                          # sampled in the group first, then it leaves the group
    (out / "INSTRUMENTED_DONE.json").write_text("{}")
    os._exit(0)
if mode == "spike_exit":
    import numpy as np
    a = np.ones((1 << 30) // 8)
    a += 1
    (out / "INSTRUMENTED_DONE.json").write_text("{}")
    os._exit(0)
if mode.startswith("fill:"):
    put("passes/fill.bin", b"\0" * int(mode.split(":")[1]))
    time.sleep(600)
if mode.startswith("alloc:"):
    import numpy as np
    a = np.ones(int(float(mode.split(":")[1]) * (1 << 30)) // 8)
    a += 1
    time.sleep(600)
if mode.startswith("late_alloc:"):             # revision 12: idle <s>, then touch <gib> GiB and hold it
    import numpy as np
    _, delay, gib = mode.split(":")
    time.sleep(float(delay))
    a = np.ones(int(float(gib) * (1 << 30)) // 8)
    a += 1
    time.sleep(600)
if mode.startswith("exit:"):
    sys.exit(int(mode.split(":")[1]))
if mode == "norecord":
    sys.exit(0)
