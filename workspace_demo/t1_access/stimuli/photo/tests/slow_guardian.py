"""Fixture (revision 9, Stage A A1): the real watchdog, whose guardian publishes its post-kill record only after
SLOW_GUARDIAN_S seconds - the receipt-publication window between the controller's death and its durable record."""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stage_a_watchdog as W  # noqa: E402

_write = W.write_record


def write_record(path, rec):
    if rec.get("state") == "killed":
        time.sleep(float(os.environ.get("SLOW_GUARDIAN_S", "8")))
    _write(path, rec)


W.write_record = write_record

if __name__ == "__main__":
    sys.exit(W.main())
