"""A synthetic worker for the controller fixtures (no model, no development input). Usage: fake_worker.py <out> <mode>
  ok:<phase>   write <PHASE>_DONE.json (report: report/stage_a_report.json, validator_pass true) and exit 0;
               first checks it cannot take the task lock (the controller must hold it) and records that
  block        ignore SIGTERM and sleep in C (time.sleep) - only SIGKILL ends it
  mlxblock     ignore SIGTERM and loop 4096 x 4096 MLX matmuls on the GPU
  family       spawn a grandchild that sleeps, then block (the process group must die together)
  alloc:<gib>  touch <gib> GiB of host memory and hold it
  exit:<code>  exit with that code
  norecord     exit 0 without writing the phase record
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

out, mode = Path(sys.argv[1]), sys.argv[2]
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
                            "gates_ok": os.environ.get("STAGE_A_GATES_OK"),
                            "t": time.time()}) + "\n")
    if ph == "report":
        (out / "report").mkdir(exist_ok=True)
        (out / "report" / "stage_a_report.json").write_text(json.dumps(
            {"validator_pass": not (out / "TERMINAL.json").exists()}))
    else:
        (out / f"{ph.upper()}_DONE.json").write_text("{}")
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
if mode.startswith("alloc:"):
    import numpy as np
    a = np.ones(int(float(mode.split(":")[1]) * (1 << 30)) // 8)
    a += 1
    time.sleep(600)
if mode.startswith("exit:"):
    sys.exit(int(mode.split(":")[1]))
if mode == "norecord":
    sys.exit(0)
