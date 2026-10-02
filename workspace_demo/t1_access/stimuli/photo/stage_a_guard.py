"""Photograph arm, Stage A (ledger row 20) and the AI-reader qualification: the guards consulted before anything is
loaded or sent - revision 4 (Codex RSC 081f17b closure group 1; RSC 5a8d7ac closure 1).

Framework §8.4 (b), (c), (j), (n).

TaskLock       an exclusive fcntl.flock on <out>/LOCK, held for the life of the process. A second process - another
               phase, or the same phase twice - is refused at once. Atomic file replacement is not a lock; this is.
Terminal gate  <out>/TERMINAL.json, written durably (a finalisation-class reserved write) at the FIRST integrity,
               parity, identity, resource or unexpected failure in any phase, and consulted at the start of every work
               phase before any load. Once it exists no work phase runs again: no retry of a failed gate. Later
               failures are appended, the first stays first. An explicitly authorised crash recovery is different: an
               attempt interrupted by a crash (not by a check) may be re-attempted only if
               <out>/RECOVERY_<attempt>__<session>__<try>.json (an exact schema) names it with the owner's dated
               authorisation; its absence is an authorisation HOLD, not a terminal failure.
Go binding     `require_go`, shared by row 20 (row "20", stage "A") and the AI reader (row "aireader", stage
               "qualification"), under a STRICT schema: the go file holds exactly review {commit, path,
               record_sha256}, owner_go {by, date, words} and package; the review record is read from git at that
               commit and hashed; it holds exactly ONE closed attestation block (marker at a line start, JSON with no
               duplicate key, the closing delimiter on its own line) with exactly row, stage, verdict, reviewer, date,
               reviewed_commit and package; strings are non-empty strings (never a number or bool), digests 64
               lowercase hex, commit ids 40 lowercase hex resolving to COMMIT objects, dates exact YYYY-MM-DD calendar
               dates (nothing truncated); the package key set is EXACTLY the recomputed package's, so an extra key,
               null or not, refuses; attestation package = go package = package recomputed now = package re-derived
               from the reviewed commit (`verify_at_commit`, mandatory); the review record's commit descends from the
               reviewed commit; reviewed commit <= attestation date <= review commit <= owner go. The absence of a
               positive, exactly matching attestation is the general rejection; the negative-record list (Codex's
               not-favourable records) is a supplement. A refusal is a hold (nothing ran).
Identity       `execution_identity()` hashes everything either phase loads or runs, without loading a model: the
               snapshot's config, tokenizer, processor and template files and every safetensors shard; the lens; this
               directory's runner, controller, watchdog, report and enforcement code and stimuli/packet.py; the whole
               jlens_qwen source tree, its upstream HEAD, tracked diff and sitecustomize shim; the package trees
               (sources and binaries) of mlx, mlx_lm, mlx_vlm, transformers, tokenizers, safetensors, numpy, Pillow,
               huggingface_hub and pydantic with their versions; the Python version; the declared precision and
               dispatch; the full frozen plan and manifest; the positions receipt. Hashed afresh every time (no cache).
               Every worker - gates, instrumented, native and report - recomputes it, and the per-file import map it
               writes is the map it consumes: `check_imported_origins` refuses unless that map's bytes hash to the
               identity's package_file_maps_sha256.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import re
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
NEGATIVE_REVIEWS = {"f9d2ef3", "69539bb", "081f17b", "cf3e49e", "7048bb8", "5a8d7ac"}   # Codex negative records: row 20, AI reader
LOCAL_CODE = ["stage_a.py", "stage_a_guard.py", "stage_a_report.py", "stage_a_controller.py", "stage_a_watchdog.py",
              "memprobe.py", "enforce.py", "image_adapter.py", "dose.py", "dose_report.py"]
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
    write_json_atomic(p, t, final=True)


def recovery_files(out: Path) -> list[dict]:
    """RECOVERY_<attempt>__<session>__<try>.json files: each names exactly one interrupted try (closure group 2), under
    an exact schema - attempt_id, session and owner non-empty strings, try a positive integer (not a bool), date an
    exact YYYY-MM-DD, reason a non-empty string, no other field."""
    found = []
    for p in sorted(out.glob("RECOVERY_*.json")):
        a = _keys(strict_json(p.read_text(), p.name), RECOVERY_KEYS, p.name)
        for k in ("attempt_id", "session", "owner", "reason"):
            _str(a[k], f"{p.name}.{k}")
        if not isinstance(a["try"], int) or isinstance(a["try"], bool) or a["try"] < 1:
            _refuse(f"{p.name}.try must be a positive integer")
        iso_date(a["date"], f"{p.name}.date")
        want = f"RECOVERY_{a['attempt_id']}__{a['session']}__{a['try']}.json"
        if p.name != want:
            _refuse(f"{p.name} must be named {want}")
        found.append({**a, "file_sha256": sha_bytes(p.read_bytes())})
    return found


# ---- the execution identity (fresh hashes every time; no cache - closure group 1) ------------------------------
def _git(*args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(UPSTREAM), *args], capture_output=True, timeout=60)
    if p.returncode != 0:
        raise SystemExit(f"refused: identity command git {' '.join(args)} failed ({p.returncode}): fail closed")
    return p.stdout


def package_roots() -> dict[str, Path]:
    import importlib
    roots = {}
    for name in PACKAGES:
        mod = importlib.import_module(name)
        roots[name] = Path(mod.__file__).parent if getattr(mod, "__file__", None) else Path(list(mod.__path__)[0])
    roots["jlens_qwen"] = UPSTREAM / "jlens_qwen"
    return roots


def file_map(root: Path, suffixes=TREE_SUFFIXES) -> dict[str, str]:
    return {str(p.relative_to(root)): sha_file(p) for p in sorted(Path(root).rglob("*"))
            if p.is_file() and p.suffix in suffixes and "__pycache__" not in p.parts}


def execution_identity(plan_path: Path, manifest_path: Path, receipt_path: Path, files_path: Path | None = None) -> dict:
    """Everything either phase loads or runs, hashed afresh without loading a model. The per-file maps of every
    watched package tree are written to files_path (when given) and their hash enters the identity, so the actual
    imported origins can be checked against them at run time (`check_imported_origins`)."""
    import importlib.metadata as md
    snap = {p.name: sha_file(p) for p in sorted(SNAPSHOT.iterdir())
            if p.is_file() and p.name not in ("README.md", ".gitattributes")}
    roots = package_roots()
    maps = {name: {"root": str(r), "files": file_map(r, (".py",) if name == "jlens_qwen" else TREE_SUFFIXES)}
            for name, r in roots.items()}
    versions = {}
    for name in PACKAGES + ["mlx-metal"]:
        dist = {"PIL": "pillow"}.get(name, name.replace("_", "-"))
        try:
            versions[name] = md.version(dist)
        except md.PackageNotFoundError:
            versions[name] = None
    maps_json = json.dumps(maps, sort_keys=True).encode()
    if files_path is not None:
        Path(files_path).write_bytes(maps_json)
    if not Path(receipt_path).exists():
        raise SystemExit("refused: the positions receipt is absent (stage_a.py plan writes it only on success)")
    ident = {
        "row": "20", "stage": "A",
        "snapshot": {"id": SNAPSHOT.name, "files_sha256": snap},
        "lens": {"name": LENS.name, "sha256": sha_file(LENS)},
        "local_code_sha256": {n: sha_file(HERE / n) for n in LOCAL_CODE},
        "packet_py_sha256": sha_file(T1 / "stimuli" / "packet.py"),
        "jlens": {"head": _git("rev-parse", "HEAD").decode().strip(),
                  "tracked_diff_sha256": sha_bytes(_git("diff", "HEAD")),
                  "sitecustomize_sha256": sha_file(UPSTREAM / "sitecustomize.py")},
        "package_versions": versions, "package_file_maps_sha256": sha_bytes(maps_json),
        "python": sys.version.split()[0], "machine": platform.machine(), "macos": platform.mac_ver()[0],
        "dispatch": DISPATCH,
        "plan_sha256": sha_file(plan_path), "manifest_sha256": sha_file(manifest_path),
        "positions_receipt_sha256": sha_file(receipt_path),
    }
    ident["identity_sha256"] = sha_bytes(json.dumps(ident, sort_keys=True).encode())
    return ident


def check_imported_origins(files_path: Path, maps_sha256: str) -> dict:
    """The map CONSUMED here must be byte-identical to the admitted one (its sha256 = the identity's
    package_file_maps_sha256) before it is trusted; then every loaded module of a watched package must come from inside
    its hashed root with an unchanged file hash - a watched package imported from anywhere else (a shadowing copy,
    another venv) is refused."""
    raw = Path(files_path).read_bytes()
    if sha_bytes(raw) != maps_sha256:
        raise SystemExit(f"refused: the consumed import map {Path(files_path).name} is not the admitted map "
                         f"({sha_bytes(raw)[:12]} != {str(maps_sha256)[:12]})")
    maps = json.loads(raw)
    checked, bad = 0, []
    for name, mod in list(sys.modules.items()):
        top = name.split(".")[0]
        if top not in maps:
            continue
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        root = Path(maps[top]["root"])
        try:
            rel = str(Path(f).resolve().relative_to(root.resolve()))
        except ValueError:
            bad.append(f"{name}: loaded from {f}, outside {root}")
            continue
        want = maps[top]["files"].get(rel)
        if want is None or sha_file(Path(f)) != want:
            bad.append(f"{name}: {rel} not in the identity or changed")
        checked += 1
    if bad:
        raise SystemExit(f"refused: imported origins differ from the identity: {bad[:5]}")
    return {"modules_checked": checked, "map_sha256": maps_sha256}


# ---- the go: a machine-readable attestation inside the review record (strict schema, revision 4) -----------------
# Shared by row 20 (row "20", stage "A") and the AI reader (row "aireader", stage "qualification"). The absence of a
# POSITIVE, exactly matching attestation is the general rejection: every check below must pass, and anything not
# recognised refuses. The negative-record list is a supplement only.
ATTEST_OPEN, ATTEST_CLOSE = "<!-- STAGE-ATTESTATION v1", "-->"
ATTEST_KEYS = {"row", "stage", "verdict", "reviewer", "date", "reviewed_commit", "package"}
GO_KEYS = {"review", "owner_go", "package"}
REVIEW_KEYS = {"commit", "path", "record_sha256"}
OWNER_KEYS = {"by", "date", "words"}
RECOVERY_KEYS = {"attempt_id", "session", "try", "owner", "date", "reason"}
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _refuse(msg: str):
    raise SystemExit(f"refused: {msg}")


def _no_dupes(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            _refuse(f"duplicate JSON key {k!r}")
        d[k] = v
    return d


def strict_json(text: str, what: str):
    try:
        return json.loads(text, object_pairs_hook=_no_dupes)
    except json.JSONDecodeError as exc:
        _refuse(f"{what} is not JSON ({exc})")


def _str(v, what: str) -> str:
    if not isinstance(v, str) or not v.strip():
        _refuse(f"{what} must be a non-empty string, got {type(v).__name__} {v!r:.60}")
    return v


def _hex(v, n: int, what: str) -> str:
    if not isinstance(v, str) or not (_HEX40 if n == 40 else _HEX64).fullmatch(v):
        _refuse(f"{what} must be {n} lowercase hexadecimal characters, got {v!r:.80}")
    return v


def iso_date(v, what: str) -> str:
    """Exactly YYYY-MM-DD and a real calendar date; nothing is truncated."""
    if not isinstance(v, str) or not _DATE.fullmatch(v):
        _refuse(f"{what} {v!r:.40} is not an exact YYYY-MM-DD date")
    try:
        time.strptime(v, "%Y-%m-%d")
    except ValueError:
        _refuse(f"{what} {v!r} is not a calendar date")
    return v


def _keys(d, want: set, what: str) -> dict:
    if not isinstance(d, dict) or set(d) != want:
        got = sorted(d) if isinstance(d, dict) else type(d).__name__
        _refuse(f"{what} fields {got} are not exactly {sorted(want)}")
    return d


def is_digest_key(k: str) -> bool:
    return k.endswith("_sha256") or k == "package_digest"


def check_package_schema(pkg, keys: set, what: str) -> dict:
    """Exact key set; digests 64 lowercase hex; every other field a non-empty string (no null, number or bool)."""
    _keys(pkg, keys, what)
    for k, v in pkg.items():
        if is_digest_key(k):
            _hex(v, 64, f"{what}.{k}")
        else:
            _str(v, f"{what}.{k}")
    return pkg


def resolve_commit(repo: Path, commit: str, what: str) -> str:
    """A full 40-hex id that names a commit object in this repository (not a tree, blob or tag)."""
    _hex(commit, 40, what)
    t = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", commit], capture_output=True, text=True)
    if t.returncode != 0 or t.stdout.strip() != "commit":
        _refuse(f"{what} {commit} is not a commit object in {repo}")
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
                       capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.strip() != commit:
        _refuse(f"{what} {commit} does not resolve to itself")
    return commit


def commit_day(repo: Path, commit: str) -> str:
    c = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%cs", commit], capture_output=True, text=True)
    if c.returncode != 0:
        _refuse(f"cannot read the date of {commit}")
    return iso_date(c.stdout.strip(), f"commit date of {commit}")


def parse_attestation(text: str) -> dict:
    """Exactly one block: the opening marker at the start of a line, then a newline, a JSON object (duplicate keys
    refused), and the closing delimiter on its own line. Anything else between the markers refuses."""
    n = text.count(ATTEST_OPEN)
    if n != 1:
        _refuse(f"the review record holds {n} attestation blocks, not exactly one")
    i = text.index(ATTEST_OPEN)
    if i and text[i - 1] != "\n":
        _refuse("the attestation marker does not start a line")
    rest = text[i + len(ATTEST_OPEN):]
    if not rest.startswith("\n"):
        _refuse("the attestation marker is not followed by a newline")
    j = rest.find("\n" + ATTEST_CLOSE)
    if j < 0:
        _refuse("the attestation block has no closing delimiter on its own line")
    after = rest[j + 1 + len(ATTEST_CLOSE):]
    if after and not after.startswith("\n"):
        _refuse("the closing delimiter is not on its own line")
    att = strict_json(rest[1:j], "the attestation")
    return _keys(att, ATTEST_KEYS, "attestation")


def require_go(go_path: Path, package: dict[str, str], *, row: str = "20", stage: str = "A", repo: Path = RSC,
               verify_at_commit) -> dict:
    """The go names the review record (full commit, path, sha256) and the owner's dated words; the record carries
    exactly one closed attestation; attestation package = go package = package recomputed now = package re-derived
    from the reviewed commit (`verify_at_commit`, mandatory), each under the exact schema; both commits resolve to
    commit objects, the review record's commit descends from the reviewed commit, and the dates are ordered:
    reviewed commit <= attestation <= review record commit <= owner go."""
    if verify_at_commit is None:
        _refuse("no reviewed-commit re-derivation was supplied")
    keys = set(package)
    check_package_schema(package, keys, "the package recomputed now")
    if not go_path.exists():
        _refuse(f"{go_path.name} absent - no owner go bound to a favourable review")
    go = _keys(strict_json(go_path.read_text(), go_path.name), GO_KEYS, go_path.name)
    rv = _keys(go["review"], REVIEW_KEYS, "go.review")
    og = _keys(go["owner_go"], OWNER_KEYS, "go.owner_go")
    check_package_schema(go["package"], keys, "go.package")
    commit = resolve_commit(repo, rv["commit"], "go.review.commit")
    rec = _str(rv["path"], "go.review.path")
    if rec.startswith("/") or ".." in Path(rec).parts:
        _refuse(f"go.review.path {rec!r} must be a relative path inside the repository")
    _hex(rv["record_sha256"], 64, "go.review.record_sha256")
    if any(commit.startswith(n) for n in NEGATIVE_REVIEWS):
        _refuse(f"review commit {commit} is a negative record")
    got = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rec}"], capture_output=True)
    if got.returncode != 0:
        _refuse(f"{rec} not found at commit {commit}")
    if sha_bytes(got.stdout) != rv["record_sha256"]:
        _refuse("the review record's sha256 at that commit differs from the go file's")
    try:
        text = got.stdout.decode("utf-8")
    except UnicodeDecodeError:
        _refuse("the review record is not UTF-8")
    att = parse_attestation(text)
    for k, want in (("row", row), ("stage", stage), ("verdict", "favourable")):
        if not isinstance(att[k], str) or att[k] != want:
            _refuse(f"attestation is {att['row']!r}/{att['stage']!r}/{att['verdict']!r}, not {row}/{stage}/favourable")
    _str(att["reviewer"], "attestation.reviewer")
    reviewed = resolve_commit(repo, att["reviewed_commit"], "attestation.reviewed_commit")
    if any(reviewed.startswith(n) for n in NEGATIVE_REVIEWS):
        _refuse(f"reviewed commit {reviewed} is a negative record")
    check_package_schema(att["package"], keys, "attestation.package")
    for k in sorted(keys):
        a, g, n = att["package"][k], go["package"][k], package[k]
        if not (a == g == n):
            _refuse(f"{k}: attested {a!r}, go {g!r}, now {n!r}")
    then = verify_at_commit(reviewed)
    check_package_schema(then, keys, "the package re-derived at the reviewed commit")
    if then != package:
        diff = sorted(k for k in keys if then[k] != package[k])
        _refuse(f"the package at the reviewed commit differs from the package now: {diff}")
    anc = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", reviewed, commit], capture_output=True)
    if anc.returncode != 0:
        _refuse(f"the review record's commit {commit} does not descend from the reviewed commit {reviewed}")
    _str(og["by"], "owner_go.by")
    _str(og["words"], "owner_go.words")
    a_day, o_day = iso_date(att["date"], "attestation.date"), iso_date(og["date"], "owner_go.date")
    c_day, r_day = commit_day(repo, reviewed), commit_day(repo, commit)
    if not (c_day <= a_day <= r_day <= o_day):
        _refuse(f"dates out of order (reviewed commit {c_day}, attestation {a_day}, review record commit {r_day}, "
                f"owner go {o_day})")
    return {"go": go, "attestation": att}
