#!/usr/bin/env python3
"""Read-only Q4 source/archive lineage. No scientific imports, EEG, fits or BMS.

Only this review's adjacent JSON is written. The completed numerical audit in
stage_c_checks.py is intentionally not imported or repeated.
"""
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

RSC = Path(__file__).resolve().parents[3]
UNIMOG = RSC.parent / "Unimog-Projects"
PRODUCER = "e341319f5c6e0ce27fdeeb83ca6124009b7e0996"
ARCHIVE = UNIMOG / "papers/adaptive_agency_special_issue/release/local/arxiv-submitted-v1/arxiv_v1_source_candidate.zip"
EXPECTED_ARCHIVE = "af47b85b2a9fd24222dfb73ba6781feb287d702169fa4463ebf3ec9d313f4818"


def git(*args):
    return subprocess.check_output(["git", "-C", str(RSC), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    tracked = git("ls-tree", "-r", "--name-only", PRODUCER,
                  "workspace_demo/sergent_port").decode().splitlines()
    rows = {}
    for rel in tracked:
        if Path(rel).suffix not in {".py", ".md"}:
            continue
        archived = git("show", f"{PRODUCER}:{rel}")
        current = (RSC / rel).read_bytes()
        rows[rel] = {"sha256": sha(current), "producer_sha256": sha(archived),
                     "bytes": len(current), "identical": current == archived}
    assert rows and all(row["identical"] for row in rows.values())
    tracked_diff = git("diff", "--name-status", PRODUCER, "--",
                       "workspace_demo/sergent_port").decode()
    assert not tracked_diff, tracked_diff
    audit = json.loads(Path(__file__).with_name(
        "2026-09-15_melcon_v6_stage_c_checks.json").read_text())
    bms_rel = "workspace_demo/sergent_port/bms.py"
    assert rows[bms_rel]["sha256"] == audit["source_sha256"][bms_rel]
    archive_sha = sha(ARCHIVE.read_bytes())
    assert archive_sha == EXPECTED_ARCHIVE
    with zipfile.ZipFile(ARCHIVE, "r") as archive:
        members = {info.filename: {"sha256": sha(archive.read(info.filename)),
                                  "bytes": info.file_size}
                   for info in archive.infolist()}
    assert len(members) == 14
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": sha(Path(__file__).read_bytes()),
        "rsc_head": git("rev-parse", "HEAD").decode().strip(),
        "human_producer": PRODUCER,
        "sergent_source_and_docs": rows,
        "tracked_sergent_diff_from_producer": tracked_diff,
        "shared_bms_matches_completed_stage_c_audit": True,
        "archive_path": str(ARCHIVE), "archive_sha256": archive_sha,
        "archive_members": members,
        "scope": "Source and archive bytes only; no imports of analysis code, EEG, fits, BMS, or scientific recomputation."
    }
    target = Path(__file__).with_suffix(".json")
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"evidence": str(target), "source_files": len(rows),
                      "all_sources_identical_to_producer": True,
                      "shared_bms_sha256": rows[bms_rel]["sha256"],
                      "archive_sha256": archive_sha,
                      "archive_members": len(members)}, indent=2))


if __name__ == "__main__":
    main()
