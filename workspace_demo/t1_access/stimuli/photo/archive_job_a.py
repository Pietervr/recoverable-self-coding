"""Prepare the AI reader's FRESH state for job (b) (revision 12; R052 handoff ff264083 "THEN"): move job (a)'s journal
and clock files into a dated archive under reviews/, listed with their sha256, so the executor starts with no raw
journal and no clock (it refuses mixed old-package state, and a receipt is terminal for its journal). Job (a) stays
closed and retained beside job (b): its verdict (NOT ADMITTED under its frozen rule) is unchanged.

The job-(a) variant of archive_first_reader_job.py, with its own constants. Not part of either package (bound to
neither identity). Prepared on 3 October; run only on the owner's go for job (b), after Codex's favourable record:

    .venv-image/bin/python stimuli/photo/archive_job_a.py            # dry run: lists what would move
    .venv-image/bin/python stimuli/photo/archive_job_a.py --apply    # moves (git mv for the tracked journal)

It refuses if the archive exists, if the journal is not job (a)'s - file sha256 b8c8bf4f… (committed at RSC 0baec65),
its last record the COMPLETE receipt naming journal sha256 e61357d6… - if the closure marker is absent, or if any
reader process is running. It commits nothing.
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
DEST = T1 / "reviews" / "2026-10-02_ai_reader_job_a_archive"
FILE_SHA = "b8c8bf4f991f6ebd5e90f049999d1d7c7a9df566701380807522277a3fc1ee44"
RECEIPT_JOURNAL_SHA = "e61357d6f3738c6354288614e917a9fe58e4481f2e1a8bee98884b0dba3210be"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(apply: bool) -> int:
    if DEST.exists():
        raise SystemExit(f"refused: {DEST} exists")
    if subprocess.run(["pgrep", "-f", "ai_reader_exec.py run"], capture_output=True).returncode == 0:
        raise SystemExit("refused: a reader job is running")
    if sha(RAW) != FILE_SHA:
        raise SystemExit("refused: the journal is not job (a)'s")
    last = json.loads(RAW.read_bytes().splitlines()[-1])
    if last.get("t") != "receipt" or last.get("outcome") != "COMPLETE" or \
            last.get("journal_sha256") != RECEIPT_JOURNAL_SHA:
        raise SystemExit("refused: the journal's last record is not job (a)'s COMPLETE receipt")
    if not (JOB / "clock.closed.json").exists():
        raise SystemExit("refused: job (a)'s closure marker is absent")
    moves = [RAW] + sorted(p for p in JOB.iterdir() if p.is_file() and p.name != "LOCK")
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
    (DEST / "manifest.json").write_text(json.dumps({"archived_from": manifest, "job": "job (a), 2 October 2026 "
                                                    "(UTC 3 October): COMPLETE 600 of 600, 600 of 660 attempts, "
                                                    "4,000.8 s; scored NOT ADMITTED (49 of 63 easy gray) under the "
                                                    "revision-11 package 6be7d4c8…"},
                                                   indent=1, sort_keys=True) + "\n")
    print(f"moved {len(moves)} files to {DEST}; commit them with explicit paths")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv[1:]))
