"""Fixture watchdogs (revision 11, the 2 October run). Usage: fixture_watchdogs.py <variant> <watchdog json>.
  teardown      the real watchdog, except that proc_info stops answering for the worker leader once it has committed
                its phase record (its pid in <out>/teardown.pid) - while the leader is still alive and its NOTE_EXIT
                not yet posted, exactly as a large worker's teardown did on 2 October. The kqueue stays real.
  retire_early  in phase mode: report ARMED, then exit 0 after 1 s (a watchdog gone before the leader's exit);
                guardian mode runs the real watchdog.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import memprobe  # noqa: E402
import stage_a_watchdog as W  # noqa: E402

variant, arg = sys.argv[1], sys.argv[2]
a = json.loads(arg)
sys.argv = [sys.argv[0], arg]

if variant == "retire_early" and a.get("mode") != "guardian":
    import time
    sys.stdout.write("ARMED\n")
    sys.stdout.flush()
    time.sleep(1.0)                                 # past the controller's identity check of its watchdog
    sys.exit(0)

if variant == "teardown" and a.get("mode") != "guardian":
    out = Path(a["record"]).parent
    _same, _tasks = memprobe.same_process, memprobe.task_processes

    def tearing() -> int | None:
        try:
            return int((out / "teardown.pid").read_text())
        except (OSError, ValueError):
            return None

    def same_process(ident):
        return False if ident.get("pid") == tearing() else _same(ident)

    def task_processes(roots, pgids):
        t = tearing()
        return {p: i for p, i in _tasks(roots, pgids).items() if p != t}

    memprobe.same_process, memprobe.task_processes = same_process, task_processes

sys.exit(W.main())
