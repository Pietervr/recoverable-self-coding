#!/usr/bin/env python3
"""Download the PhysioNet/CinC Challenge 2019 training data (CC-BY 4.0).

40,336 hourly-resolution ICU records (training_setA: 20,336 from BIDMC;
training_setB: 20,000 from Emory), one pipe-separated .psv per patient, served
as individual files at physionet.org/files/challenge-2019/1.0.0/training/.
No bulk zip exists on the current mirror, so this fetches the directory
listings and downloads concurrently. Idempotent: existing non-empty files are
skipped, so it can be re-run to fill gaps.

Usage: python3 fetch_cinc2019.py [--workers 12] [--dest data/cinc2019]
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://physionet.org/files/challenge-2019/1.0.0/training"
SETS = ["training_setA", "training_setB"]
UA = {"User-Agent": "rsc-cself-fetch/1.0 (research; CC-BY dataset)"}


def listing(set_name: str) -> list[str]:
    url = f"{BASE}/{set_name}/"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    files = sorted(set(re.findall(r'href="(p\d+\.psv)"', html)))
    if not files:
        raise SystemExit(f"no .psv entries found in listing {url}")
    return files


def fetch_one(set_name: str, fname: str, dest: Path) -> str:
    out = dest / set_name / fname
    if out.exists() and out.stat().st_size > 0:
        return "skip"
    url = f"{BASE}/{set_name}/{fname}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            if not data:
                raise OSError("empty body")
            out.write_bytes(data)
            return "ok"
        except Exception:
            if attempt == 3:
                return f"FAIL {set_name}/{fname}"
            time.sleep(1.5 * (attempt + 1))
    return f"FAIL {set_name}/{fname}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dest", default=str(Path(__file__).parent / "data" / "cinc2019"))
    a = ap.parse_args()
    dest = Path(a.dest)

    jobs: list[tuple[str, str]] = []
    for s in SETS:
        (dest / s).mkdir(parents=True, exist_ok=True)
        files = listing(s)
        print(f"[fetch] {s}: {len(files)} files listed", flush=True)
        jobs += [(s, f) for f in files]

    done = fails = skips = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(fetch_one, s, f, dest) for s, f in jobs]
        for fut in as_completed(futs):
            r = fut.result()
            done += 1
            if r == "skip":
                skips += 1
            elif r.startswith("FAIL"):
                fails += 1
                print(f"[fetch] {r}", flush=True)
            if done % 2000 == 0:
                rate = done / max(time.time() - t0, 1)
                print(f"[fetch] {done}/{len(jobs)} ({rate:.0f}/s, "
                      f"{skips} skipped, {fails} failed)", flush=True)

    print(f"[fetch] DONE: {done} processed, {skips} skipped, {fails} failed "
          f"in {(time.time()-t0)/60:.1f} min", flush=True)
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
