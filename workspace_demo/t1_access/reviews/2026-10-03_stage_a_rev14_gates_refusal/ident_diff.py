"""Read-only: recompute Stage A's execution identity now and list the fields that differ from the frozen one."""
import json
import sys
import tempfile
from pathlib import Path

PHOTO = Path.home() / "Recoverable-Self-Coding/workspace_demo/t1_access/stimuli/photo"
sys.path.insert(0, str(PHOTO))
sys.path.insert(0, str(PHOTO.parents[1]))
import stage_a  # noqa: E402
from stage_a_guard import execution_identity  # noqa: E402

frozen = json.loads(stage_a.IDENTITY.read_text())
with tempfile.TemporaryDirectory() as td:
    now = execution_identity(stage_a.PLAN, stage_a.MANIFEST, stage_a.RECEIPT, Path(td) / "files.json")
    files_now = json.loads((Path(td) / "files.json").read_text())
print("frozen", frozen["identity_sha256"], "now", now["identity_sha256"])


def walk(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(a.get(k), b.get(k), f"{path}.{k}" if path else k)
    elif a != b:
        print(f"  {path}: frozen={a!r} now={b!r}")


walk({k: v for k, v in frozen.items() if k != "identity_sha256"}, {k: v for k, v in now.items() if k != "identity_sha256"})
fz = json.loads(stage_a.IDENTITY_FILES.read_text()) if stage_a.IDENTITY_FILES.exists() else None
if fz is not None:
    for pkg in sorted(set(fz) | set(files_now)):
        a, b = (fz.get(pkg) or {}).get("files", {}), (files_now.get(pkg) or {}).get("files", {})
        d = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        if d or (fz.get(pkg) or {}).get("root") != (files_now.get(pkg) or {}).get("root"):
            print(f"  file map {pkg}: root {(fz.get(pkg) or {}).get('root')} -> {(files_now.get(pkg) or {}).get('root')}; "
                  f"{len(d)} files differ, e.g. {d[:8]}")
