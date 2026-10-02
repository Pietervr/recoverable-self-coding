"""Photograph arm, Stage A (ledger row 20): the guards the runner consults before anything is loaded.

Framework §8.4 (b), (c), (j), (n); R052 brief 2026-10-02 repairs 5, 6, 7, 11.

TaskLock       an exclusive fcntl.flock on <out>/LOCK, held for the life of the process. A second process - another
               phase, or the same phase twice - is refused at once. Atomic file replacement is not a lock; this is.
Terminal gate  <out>/TERMINAL.json, written durably at the FIRST integrity, parity, identity, resource or unexpected
               failure in any phase, and consulted at the start of every phase before any load. Once it exists no
               phase runs again: no retry of a failed gate. Later failures are appended, the first stays first.
               An explicitly authorised crash recovery is different: an attempt interrupted by a crash (not by a
               check) may be re-attempted only if <out>/RECOVERY_<attempt id>.json names it with the owner's dated
               authorisation; a crash that leaves no interrupted attempt needs nothing (the session clock charged it).
Go binding     ROW20_GO.json must carry: the favourable review (RSC commit, record path, the record's sha256 at that
               commit, verdict exactly "favourable", reviewer), the owner's dated go (date, words), and the sha256 of
               the exact package - STAGE_A_CRITERIA.md, stage_a_identity.json, stage_a_plan.json, manifest_dev.json and
               the budget envelope. Each is recomputed and compared; the review record is read from git at the named
               commit and hashed; RSC f9d2ef3 (the negative record) can never serve. A mismatch refuses before any
               model import or load. Refusal here is a hold, not a terminal failure (nothing ran).
Identity       `execution_identity()` hashes everything either phase loads or runs, without loading a model: the
               snapshot's config, tokenizer, processor and template files and every safetensors shard; the lens; this
               directory's runner code and stimuli/packet.py; the whole jlens_qwen source tree, its upstream HEAD,
               tracked diff and sitecustomize shim; the package trees (sources and binaries) of mlx, mlx_lm, mlx_vlm,
               transformers, tokenizers, safetensors, numpy, Pillow, huggingface_hub and pydantic with their versions;
               the Python version; the declared precision and dispatch; the full frozen plan and manifest. Large files
               are hashed once and cached by (path, size, mtime_ns). The record is written to stage_a_identity.json;
               both phases recompute it and refuse a different value. The in-process `_run` never builds the HTTP
               startup manifest, so nothing relies on that manifest's attestation.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
T1 = HERE.parents[1]
RSC = T1.parents[1]
UPSTREAM = T1.parent / "upstream" / "jlens-qwen36"
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
LENS = UPSTREAM / "data" / "lens" / "qwen36_27b_neuronpedia_n1000.npz"
NEGATIVE_REVIEWS = {"f9d2ef3"}                     # Codex's NOT ON BOARD record for the first package
LOCAL_CODE = ["stage_a.py", "stage_a_guard.py", "stage_a_report.py", "enforce.py", "image_adapter.py", "dose.py",
              "dose_report.py"]
PACKAGES = ["mlx", "mlx_lm", "mlx_vlm", "transformers", "tokenizers", "safetensors", "numpy", "PIL",
            "huggingface_hub", "pydantic"]
TREE_SUFFIXES = (".py", ".so", ".dylib", ".metallib", ".json", ".jinja")
# Declared precision and dispatch (checked at run time against what the loaded objects report).
DISPATCH = {"hidden_dtype": "bfloat16", "weights": "4-bit affine (snapshot quantization config)",
            "instrumented": {"jlens patch_gdn applied": True, "GDN inference kernel per pass": True,
                             "custom GDN VJP": "recorded (training-only path, unused in a prefill)",
                             "capture": "jlens_qwen.capture_endpoint._run, one StreamSession.extend per pass"},
            "native": {"jlens_qwen imported": False, "capture_layer_ids": None,
                       "prefill": "mlx-vlm get_input_embeddings + language_model(ids, inputs_embeds, fresh cache)"},
            "vision": "mlx-vlm qwen3_5 vision tower in its weight dtype; features cast to the hidden dtype at merge"}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(path: Path, cache: dict | None = None) -> str:
    p = Path(path).resolve()
    st = p.stat()
    key = f"{p}|{st.st_size}|{st.st_mtime_ns}"
    if cache is not None and key in cache:
        return cache[key]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    if cache is not None:
        cache[key] = h.hexdigest()
    return h.hexdigest()


def tree_digest(root: Path, cache: dict, suffixes=TREE_SUFFIXES) -> dict:
    h, n = hashlib.sha256(), 0
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and p.suffix in suffixes and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(root)).encode() + b"\0" + sha_file(p, cache).encode() + b"\n")
            n += 1
    return {"sha256": h.hexdigest(), "files": n}


# ---- the lock --------------------------------------------------------------------------------------------------
class TaskLock:
    def __init__(self, out: Path):
        out.mkdir(parents=True, exist_ok=True)
        self.path = out / "LOCK"
        self.fh = open(self.path, "a+")
        try:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.fh.close()
            raise SystemExit(f"refused: another Stage A process holds {self.path}")
        self.fh.seek(0)
        self.fh.truncate()
        self.fh.write(json.dumps({"pid": os.getpid(), "since": time.time()}))
        self.fh.flush()

    def release(self) -> None:
        if not self.fh.closed:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            self.fh.close()


# ---- the terminal gate -----------------------------------------------------------------------------------------
def terminal_path(out: Path) -> Path:
    return out / "TERMINAL.json"


def check_terminal(out: Path) -> None:
    p = terminal_path(out)
    if p.exists():
        t = json.loads(p.read_text())
        raise SystemExit(f"refused: Stage A stopped terminally ({t['first']['phase']}: {t['first']['reason']}); "
                         f"no phase runs again and no failed gate is retried")


def set_terminal(out: Path, phase: str, reason: str) -> None:
    from enforce import write_json_atomic
    p = terminal_path(out)
    entry = {"phase": phase, "reason": str(reason)[:4000], "wall": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "pid": os.getpid()}
    if p.exists():
        t = json.loads(p.read_text())
        t.setdefault("later", []).append(entry)
    else:
        t = {"first": entry}
    write_json_atomic(p, t)


def recovery_authority(out: Path, attempt_id: str) -> dict | None:
    p = out / f"RECOVERY_{attempt_id}.json"
    if not p.exists():
        return None
    a = json.loads(p.read_text())
    if a.get("attempt_id") != attempt_id or not a.get("owner") or not a.get("date") or not a.get("reason"):
        raise SystemExit(f"refused: {p.name} must name attempt_id, owner, date and reason")
    return a


# ---- the execution identity ------------------------------------------------------------------------------------
def execution_identity(plan_path: Path, manifest_path: Path, cache_path: Path) -> dict:
    """Everything either phase loads or runs, hashed without loading a model."""
    import importlib
    import importlib.metadata as md
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    snap = {p.name: sha_file(p, cache) for p in sorted(SNAPSHOT.iterdir())
            if p.is_file() and p.name not in ("README.md", ".gitattributes")}
    pkgs = {}
    for name in PACKAGES:
        mod = importlib.import_module(name)
        root = Path(mod.__file__).parent if getattr(mod, "__file__", None) else Path(list(mod.__path__)[0])
        dist = {"PIL": "pillow", "mlx": "mlx"}.get(name, name.replace("_", "-"))
        try:
            ver = md.version(dist)
        except md.PackageNotFoundError:
            ver = getattr(mod, "__version__", None)
        pkgs[name] = {"version": ver, "tree": tree_digest(root, cache)}
    try:
        pkgs["mlx-metal"] = {"version": md.version("mlx-metal")}
    except md.PackageNotFoundError:
        pass
    git = lambda *a: subprocess.run(["git", "-C", str(UPSTREAM), *a], capture_output=True, timeout=60).stdout
    ident = {
        "row": "20", "stage": "A",
        "snapshot": {"id": SNAPSHOT.name, "files_sha256": snap},
        "lens": {"name": LENS.name, "sha256": sha_file(LENS, cache)},
        "local_code_sha256": {n: sha_file(HERE / n, cache) for n in LOCAL_CODE},
        "packet_py_sha256": sha_file(T1 / "stimuli" / "packet.py", cache),
        "jlens": {"tree": tree_digest(UPSTREAM / "jlens_qwen", cache, (".py",)),
                  "head": git("rev-parse", "HEAD").decode().strip(),
                  "tracked_diff_sha256": sha_bytes(git("diff", "HEAD")),
                  "sitecustomize_sha256": sha_file(UPSTREAM / "sitecustomize.py", cache)},
        "packages": pkgs,
        "python": sys.version.split()[0], "machine": platform.machine(), "macos": platform.mac_ver()[0],
        "dispatch": DISPATCH,
        "plan_sha256": sha_file(plan_path), "manifest_sha256": sha_file(manifest_path),
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=0, sort_keys=True))
    ident["identity_sha256"] = sha_bytes(json.dumps(ident, sort_keys=True).encode())
    return ident


# ---- the go ----------------------------------------------------------------------------------------------------
def require_go(go_path: Path, package: dict[str, str], *, repo: Path = RSC) -> dict:
    """package: {criteria_sha256, identity_sha256, plan_sha256, manifest_sha256, budget_sha256} as computed now."""
    if not go_path.exists():
        raise SystemExit(f"refused: {go_path.name} absent - row 20 has no owner go bound to a favourable review")
    go = json.loads(go_path.read_text())
    rv, og, bound = go.get("codex_row_review") or {}, go.get("owner_go") or {}, go.get("package") or {}
    if not isinstance(rv, dict) or rv.get("verdict") != "favourable":
        raise SystemExit("refused: codex_row_review.verdict is not exactly 'favourable'")
    commit, rec = str(rv.get("commit", "")), str(rv.get("record_path", ""))
    if len(commit) < 7 or any(commit.startswith(n) or n.startswith(commit) for n in NEGATIVE_REVIEWS):
        raise SystemExit(f"refused: review commit {commit!r} is absent or is the negative record")
    got = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rec}"], capture_output=True)
    if got.returncode != 0:
        raise SystemExit(f"refused: {rec} not found at commit {commit}")
    if sha_bytes(got.stdout) != rv.get("record_sha256"):
        raise SystemExit("refused: the review record's sha256 at that commit differs from the go file's")
    if b"not on board" in got.stdout.lower():
        raise SystemExit("refused: the named review record says NOT ON BOARD")
    if not og.get("date") or not og.get("words") or not og.get("by"):
        raise SystemExit("refused: owner_go needs by, date and the owner's words")
    try:
        go_day = time.strptime(og["date"][:10], "%Y-%m-%d")
    except ValueError:
        raise SystemExit("refused: owner_go.date is not an ISO date")
    review_day = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%cs", commit],
                                capture_output=True, text=True).stdout.strip()
    if review_day and time.strftime("%Y-%m-%d", go_day) < review_day:
        raise SystemExit("refused: the owner's go predates the review it is bound to")
    for k, v in package.items():
        if bound.get(k) != v:
            raise SystemExit(f"refused: the go binds {k}={bound.get(k)!r}, the package now has {v!r}")
    extra = set(bound) - set(package)
    if extra:
        raise SystemExit(f"refused: the go binds unknown fields {sorted(extra)}")
    return go
