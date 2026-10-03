"""Prepare the AI reader's FRESH state for job (c) (reader revision 13; R052 handoff 09226a88): move job (b)'s journal
and clock files into a dated archive under reviews/, listed with their sha256, so the executor starts with no raw
journal and no clock. Job (b) stays closed by its STOPPED receipt, unscored and never re-used, beside job (c).

The job-(b) variant of archive_job_a.py, with its own constants. Not part of either package (bound to neither
identity). Prepared on 3 October; run only on the owner's go for job (c), after Codex's favourable record:

    .venv-image/bin/python stimuli/photo/archive_job_b.py            # dry run: lists what would move
    .venv-image/bin/python stimuli/photo/archive_job_b.py --apply    # moves (git mv for the tracked journal)

It refuses if the archive exists, if the journal is not job (b)'s - file sha256 734ea772… (committed at RSC e543984),
its last record the STOPPED receipt naming journal sha256 316014d6… - if the closure marker is absent, or if any
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
DEST = T1 / "reviews" / "2026-10-03_ai_reader_job_b_archive"
FILE_SHA = "734ea772254dcc3d5d0627b078b405d1e4643a6df5415f0e19f1ebadacf65d55"
RECEIPT_JOURNAL_SHA = "316014d63845b1386fe3929ccc1c56d2efd088c58057027444f52afcecf3df82"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(apply: bool) -> int:
    if DEST.exists():
        raise SystemExit(f"refused: {DEST} exists")
    if subprocess.run(["pgrep", "-f", "ai_reader_exec.py run"], capture_output=True).returncode == 0:
        raise SystemExit("refused: a reader job is running")
    if sha(RAW) != FILE_SHA:
        raise SystemExit("refused: the journal is not job (b)'s")
    last = json.loads(RAW.read_bytes().splitlines()[-1])
    if last.get("t") != "receipt" or last.get("outcome") != "STOPPED" or \
            last.get("journal_sha256") != RECEIPT_JOURNAL_SHA:
        raise SystemExit("refused: the journal's last record is not job (b)'s STOPPED receipt")
    if not (JOB / "clock.closed.json").exists():
        raise SystemExit("refused: job (b)'s closure marker is absent")
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
    (DEST / "manifest.json").write_text(json.dumps({"archived_from": manifest, "job": "job (b), 3 October 2026: "
                                                    "STOPPED after 219 of 600 requests (218 ok, 1 capacity refusal "
                                                    "classified isolation), 219 attempts, 1,754.1 s live; the pinned "
                                                    "codex 0.159.3 removed by a cask upgrade; never scored, never "
                                                    "re-used; revision-12 package 3e2bcdcc…"},
                                                   indent=1, sort_keys=True) + "\n")
    print(f"moved {len(moves)} files to {DEST}; commit them with explicit paths")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv[1:]))
