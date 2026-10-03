"""Prepare the AI reader's FRESH state for its next job (the owner's alternative (a)): move the closed 2 October job's
journal and clock files into a dated archive under reviews/, listed with their sha256, so the executor starts with no
raw journal and no clock (it refuses mixed old-package state, and a receipt is terminal for its journal).

Not part of either package (bound to neither identity). Prepared on 2 October; run only on the owner's go for job (a):

    .venv-image/bin/python stimuli/photo/archive_first_reader_job.py            # dry run: lists what would move
    .venv-image/bin/python stimuli/photo/archive_first_reader_job.py --apply    # moves (git mv for the tracked journal)

It refuses if the archive exists, if the journal's last record is not the 2 October STOPPED receipt (journal sha256
289ecc6b… at its receipt, committed at RSC f021c53), or if any reader process is running. It commits nothing.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T1 = HERE.parents[1]
RSC = T1.parents[1]
RAW = HERE / "ai_reader_raw_responses.jsonl"
JOB = T1 / "captures" / "ai_reader_job"
DEST = T1 / "reviews" / "2026-10-02_ai_reader_first_job_archive"
RECEIPT_JOURNAL_SHA = "289ecc6bc1bdd359702be6c45dd4294f8f48abd9958e46a97b829477fb098b2d"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(apply: bool) -> int:
    if DEST.exists():
        raise SystemExit(f"refused: {DEST} exists")
    if subprocess.run(["pgrep", "-f", "ai_reader_exec.py run"], capture_output=True).returncode == 0:
        raise SystemExit("refused: a reader job is running")
    recs = [json.loads(x) for x in RAW.read_bytes().splitlines()]
    last = recs[-1]
    if last.get("t") != "receipt" or last.get("outcome") != "STOPPED" or last.get("journal_sha256") != RECEIPT_JOURNAL_SHA:
        raise SystemExit("refused: the journal is not the closed 2 October job")
    moves = [RAW] + sorted(p for p in JOB.iterdir() if p.is_file() and p.name != "LOCK") if JOB.exists() else [RAW]
    manifest = {str(p.relative_to(T1)): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in moves}
    print(json.dumps(manifest, indent=1))
    if not apply:
        print("dry run: nothing moved")
        return 0
    DEST.mkdir(parents=True)
    for p in moves:
        if p == RAW:
            subprocess.run(["git", "-C", str(RSC), "mv", str(p), str(DEST / p.name)], check=True)
        else:
            shutil.move(str(p), str(DEST / p.name))
    (DEST / "manifest.json").write_text(json.dumps({"archived_from": manifest, "job": "2 October 2026, STOPPED after "
                                                    "175 attempts; never scored; spend 175 of 660 attempts, 1,097.4 s"},
                                                   indent=1, sort_keys=True) + "\n")
    print(f"moved {len(moves)} files to {DEST}; commit them with explicit paths")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv[1:]))
