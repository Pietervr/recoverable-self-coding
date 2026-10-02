"""Synthetic fixture for the AI-reader mechanism tests: a small labelled-synthetic set (N_ITEMS items x 2 views), tiny
generated images, a delivery receipt, a key and a fake-codex plan. No model, no development or qualification image.

As a script (the hard-kill driver): airq_fixture.py <root>   -> runs the executor once in fixture mode and prints
the result; AIRQ_CRASH=<point>:<n> in its environment makes it os._exit(77) at that point.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PHOTO = TESTS.parent
sys.path.insert(0, str(PHOTO))
import ai_reader_exec as X  # noqa: E402
import ai_reader_runtime as R  # noqa: E402

N_ITEMS = 3
READER = {"model": "gpt-6.1-sol", "reasoning_effort": "medium", "cli_version": "codex-cli 0.159.3"}
PROMPT = "fixture prompt"
DIGEST = "f" * 64


def png(v: int) -> bytes:
    raw = b"".join(b"\x00" + bytes([v]) * 8 for _ in range(8))

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 0, 0, 0, 0)) + \
        ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")


def build(root: Path, plan: dict | None = None, n_items: int = N_ITEMS) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    (root / "images").mkdir(exist_ok=True)
    (root / "attempts").mkdir(exist_ok=True)
    requests, items = [], {}
    for i in range(n_items):
        item = f"it{i}"
        items[item] = {"concept": f"thing{i}", "sense": "a synthetic thing", "synset": "", "aliases": ["thing"],
                       "human": {"recognizability": 0.9, "n_ratings": 10}, "stratum": i % 3, "easy": True}
        for j, view in enumerate(("colour", "gray")):
            rq = f"rq{i}{view[0]}"
            data = png(16 * i + j + 1)
            (root / "images" / f"{rq}.png").write_bytes(data)
            requests.append({"request": rq, "item": item, "view": view, "file": f"{rq}.png",
                             "sha256": hashlib.sha256(data).hexdigest()})
    order = [r["request"] for r in requests if r["view"] == "colour"] + \
            [r["request"] for r in requests if r["view"] == "gray"]
    sset = {"requests": requests, "delivery_order": order, "reader": READER, "prompt": PROMPT,
            "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest()}
    codex = [sys.executable, str(TESTS / "fake_codex.py")]
    per, instr = {}, set()
    for i, r in enumerate(requests):                   # rendered like the real delivery receipt, per request
        adir = root / "probe" / f"r{i}" / "a"
        img = R.prepare(adir, (root / "images" / r["file"]).read_bytes(), r["file"])
        rc = R.prompt_input(codex, READER, adir, img, PROMPT, sandbox=False)
        instr.add(rc["instructions_sha256"])
        per[r["request"]] = {"image_sha256": rc["images"][0]["sha256"], "user_text_sha256": rc["user_text_sha256"],
                             "bytes": rc["images"][0]["bytes"], "detail": rc["images"][0]["detail"]}
    import shutil
    shutil.rmtree(root / "probe", ignore_errors=True)
    delivery = {"instructions_sha256": instr.pop(), "requests": per}
    (root / "fake_plan.json").write_text(json.dumps(plan or {}))
    fx = {"codex": codex, "images": root / "images", "job": root / "job", "raw": root / "raw.jsonl",
          "attempts": root / "attempts", "sset": sset, "delivery": delivery, "package": {"package_digest": DIGEST}}
    (root / "fixture.json").write_text(json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in fx.items()}))
    return {"fixture": fx, "key": {"items": items}, "sset": sset}


def load(root: Path) -> dict:
    d = json.loads((root / "fixture.json").read_text())
    for k in ("images", "job", "raw", "attempts"):
        d[k] = Path(d[k])
    return d


def dispatches(root: Path) -> list[dict]:
    p = root / "dispatch_log.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


if __name__ == "__main__":
    import os
    import time
    import ai_reader_journal as J
    if os.environ.get("AIRQ_FINAL_WRITE_S"):               # revision-6 timing fixtures (R3)
        X.FINAL_WRITE_S = float(os.environ["AIRQ_FINAL_WRITE_S"])
    if os.environ.get("AIRQ_SETUP_S"):
        X.SETUP_S = float(os.environ["AIRQ_SETUP_S"])
    slow_r, slow_c = float(os.environ.get("AIRQ_SLOW_RECEIPT", 0)), float(os.environ.get("AIRQ_SLOW_CLOSE", 0))
    slow_a = float(os.environ.get("AIRQ_SLOW_ACCOUNTING", 0))
    if slow_r:
        _append = J.append

        def append(path, rec, cap=None):
            if rec.get("t") == "receipt":
                time.sleep(slow_r)
            return _append(path, rec, cap)
        J.append = append
    if slow_c:
        _wa = X.write_atomic

        def wa(path, data, **kw):
            if b'"open_session": null' in data:
                time.sleep(slow_c)
            return _wa(path, data, **kw)
        X.write_atomic = wa
    close_fail, marker_fail = os.environ.get("AIRQ_CLOSE_FAIL"), os.environ.get("AIRQ_MARKER_FAIL")
    if close_fail:                                         # revision-7 post-rename failure fixtures (reader A)
        _wa2 = X.write_atomic

        def wa2(path, data, **kw):
            _wa2(path, data, **kw)                         # the rename (and fsyncs) happened ...
            if b'"open_session": null' in data:
                if close_fail == "stall":
                    time.sleep(10 ** 6)
                raise OSError("fixture: directory fsync failed after the rename")
        X.write_atomic = wa2
    if marker_fail:                                        # revision 8 (reader A): the marker's write and commit
        _wm = X.write_marker

        def wm(path, data, commit=None):
            if marker_fail == "error":
                raise OSError("fixture: the marker's write failed")

            def c2(fn, undo=None):
                def f():
                    if marker_fail == "stall_before_rename":
                        time.sleep(10 ** 6)
                    if marker_fail == "late_release":      # revision 9: released AFTER the deadline fired and the
                        dl = commit.__self__               # revocation's first unlink found no marker
                        while not dl.fired:
                            time.sleep(0.005)
                        time.sleep(0.05)
                    fn()                                   # the rename
                    if marker_fail == "stall_after_rename":   # visible, but the call does not return
                        time.sleep(10 ** 6)
                return commit(f, undo=undo) if commit else f()
            return _wm(path, data, c2)
        X.write_marker = wm
    if os.environ.get("AIRQ_TOMBSTONE_BLOCK"):             # revision 9 (reader A): the tombstone writer blocks
        _wj = X.write_json_atomic

        def wj(path, obj, **kw):
            if Path(path).name == X.CLOSE_TOMBSTONE:
                time.sleep(10 ** 6)
            return _wj(path, obj, **kw)
        X.write_json_atomic = wj
    if os.environ.get("AIRQ_PENDING_STALL"):               # revision 9 (reader B1): the pending write's temporary is
        _wj2 = X.write_json_atomic                         # written and fsynced, then the rename never comes

        def wj2(path, obj, **kw):
            if Path(path).name.startswith("clock.starting."):
                tmp = Path(path).with_name(Path(path).name + ".tmp")
                with open(tmp, "w") as fh:
                    fh.write(json.dumps(obj))
                    fh.flush()
                    os.fsync(fh.fileno())
                time.sleep(10 ** 6)
            return _wj2(path, obj, **kw)
        X.write_json_atomic = wj2
    if os.environ.get("AIRQ_BLOCK_FIRST_PERSIST"):         # revision 9 (reader B2): the clock's first persist blocks
        _wa3 = X.write_atomic

        def wa3(path, data, **kw):
            if Path(path).name == "clock.json":
                time.sleep(10 ** 6)
            return _wa3(path, data, **kw)
        X.write_atomic = wa3
    if os.environ.get("AIRQ_LOCK_STALL"):                  # revision 10: alive before the lock, pending published
        X.TaskLock = lambda d: time.sleep(10 ** 6)
    if os.environ.get("AIRQ_JOB_CLOCK_S"):                 # revision 8 (reader B): a cap near the used time
        X.LIMITS["job_clock_s"] = float(os.environ["AIRQ_JOB_CLOCK_S"])
    if os.environ.get("AIRQ_SLOW_CLOCK_READ"):             # revision 8 (reader B): the old clock's read is slow
        _rt, slow_cr = Path.read_text, float(os.environ["AIRQ_SLOW_CLOCK_READ"])
        done = {"n": 0}

        def rt(self, *a, **k):
            if self.name == "clock.json" and not done["n"]:
                done["n"] = 1
                time.sleep(slow_cr)
            return _rt(self, *a, **k)
        Path.read_text = rt
    if slow_a:
        _ca = X.check_accounting
        X.check_accounting = lambda *a: (time.sleep(slow_a), _ca(*a))[1]
    print(json.dumps(X.run(fixture=load(Path(sys.argv[1]))), default=str))
