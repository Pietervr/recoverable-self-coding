"""Regenerate serve_capture.patch from the working upstream clone, then prove it applies.

The upstream clone (workspace_demo/upstream/jlens-qwen36, gitignored) carries two local
patches in order: serve_tail_readout.patch, then serve_capture.patch (jlens_qwen/
capture_endpoint.py plus a hook at the end of serve.py). This script diffs the working
clone against pristine HEAD with the tail patch applied, writes serve_capture.patch, and
verifies on a fresh copy that tail + capture reproduce the working files byte for byte.

    python3 workspace_demo/patches/make_serve_capture_patch.py
"""

from __future__ import annotations

import difflib
import hashlib
import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PATCHES = Path(__file__).resolve().parent
UPSTREAM = PATCHES.parent / "upstream" / "jlens-qwen36"
TAIL = PATCHES / "serve_tail_readout.patch"
OUT = PATCHES / "serve_capture.patch"
FILES = ["jlens_qwen/serve.py", "jlens_qwen/capture_endpoint.py"]


def pristine_with_tail(dest: Path) -> None:
    arch = subprocess.run(["git", "-C", str(UPSTREAM), "archive", "HEAD", "jlens_qwen/serve.py"],
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(arch)) as t:
        t.extractall(dest, filter="data")
    subprocess.run(["git", "apply", str(TAIL)], cwd=dest, check=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        pristine_with_tail(base)
        chunks = []
        for rel in FILES:
            old_path = base / rel
            new_path = UPSTREAM / rel
            old = old_path.read_text().splitlines(keepends=True) if old_path.exists() else []
            new = new_path.read_text().splitlines(keepends=True)
            fromfile = f"a/{rel}" if old_path.exists() else "/dev/null"
            diff = list(difflib.unified_diff(old, new, fromfile, f"b/{rel}", n=3))
            if diff:
                header = f"diff --git a/{rel} b/{rel}\n" + ("" if old_path.exists() else "new file mode 100644\n")
                chunks.append(header + "".join(diff))
        OUT.write_text("".join(chunks))

    with tempfile.TemporaryDirectory() as tmp:
        check = Path(tmp)
        pristine_with_tail(check)
        subprocess.run(["git", "apply", "--check", str(OUT)], cwd=check, check=True)
        subprocess.run(["git", "apply", str(OUT)], cwd=check, check=True)
        for rel in FILES:
            a, b = (check / rel).read_bytes(), (UPSTREAM / rel).read_bytes()
            if a != b:
                print(f"FAIL: {rel} differs after applying tail + capture patches")
                return 1
            print(f"ok  {rel}  sha256 {hashlib.sha256(a).hexdigest()}")
    print(f"written {OUT} ({OUT.stat().st_size} bytes), sha256 {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
