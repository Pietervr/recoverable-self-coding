#!/usr/bin/env python3
"""Verify the local copy of ds006171 against the S3 manifest saved at download time
(results/s3_manifest_2026-09-12.txt = `aws s3 ls --recursive s3://openneuro.org/ds006171/ --no-sign-request`).

Per subject: files expected / present / size-matched; lists every missing or size-mismatched file and
any stray partial download (*.bdf.<tmp>). Writes results/download_verification.csv.
Run:  python verify_download.py
"""
from __future__ import annotations

import glob
import os
import re

import pandas as pd

from common import DATA_ROOT, RESULTS_DIR

MANIFEST = os.path.join(RESULTS_DIR, "s3_manifest_2026-09-12.txt")


def main():
    rows = []
    with open(MANIFEST) as f:
        for line in f:
            m = re.match(r"\s*(\S+)\s+(\S+)\s+(\d+)\s+ds006171/(.+)$", line.rstrip("\n"))
            if m:
                rows.append(dict(key=m.group(4), size=int(m.group(3))))
    man = pd.DataFrame(rows)
    man["subject"] = man.key.str.extract(r"^(sub-\d+)/")[0].fillna("(root)")
    man["local"] = [os.path.join(DATA_ROOT, k) for k in man.key]
    man["present"] = [os.path.isfile(p) for p in man.local]
    man["local_size"] = [os.path.getsize(p) if ok else -1 for p, ok in zip(man.local, man.present)]
    man["size_ok"] = man.present & (man.local_size == man["size"])
    per = man.groupby("subject").agg(n_expected=("key", "size"), n_present=("present", "sum"), n_size_ok=("size_ok", "sum"),
                                     bytes_expected=("size", "sum"), bytes_present=("local_size", lambda s: int(s[s > 0].sum()))).reset_index()
    per.to_csv(os.path.join(RESULTS_DIR, "download_verification.csv"), index=False)
    pd.set_option("display.width", 200, "display.max_rows", 100)
    print(per.to_string(index=False))
    bad = man[~man.size_ok]
    print(f"\nfiles expected {len(man)}, present {int(man.present.sum())}, size-matched {int(man.size_ok.sum())}; "
          f"bytes expected {int(man['size'].sum()):,}, present and matched {int(man.loc[man.size_ok, 'size'].sum()):,}")
    if len(bad):
        print("MISSING or SIZE-MISMATCHED:")
        for _, r in bad.iterrows():
            print(f"  {r.key}: expected {r['size']}, local {'absent' if not r.present else r.local_size}")
    stray = glob.glob(os.path.join(DATA_ROOT, "sub-*", "eeg", "*.bdf.*"))
    print(f"stray partial downloads: {len(stray)}" + ("".join("\n  " + s for s in stray) if stray else ""))
    extra = set(os.path.relpath(p, DATA_ROOT) for p in glob.glob(os.path.join(DATA_ROOT, "**", "*"), recursive=True) if os.path.isfile(p)) - set(man.key) - set(os.path.relpath(s, DATA_ROOT) for s in stray)
    extra = {e for e in extra if not e.startswith(".datalad") and e != ".gitattributes"}
    print(f"local files not in the manifest: {len(extra)}" + ("".join("\n  " + e for e in sorted(extra)) if extra else ""))
    # BDF headers: channel count, duration, and the file size the header implies (integrity beyond byte count)
    hdr = []
    for p in sorted(glob.glob(os.path.join(DATA_ROOT, "sub-*", "eeg", "*_eeg.bdf"))):
        with open(p, "rb") as fh:
            h = fh.read(256)
        nrec, rdur, nch = int(h[236:244]), float(h[244:252]), int(h[252:256])
        # samples per record are in the per-channel header block (BDF/EDF layout: all labels, then all
        # transducers, ... then all samples-per-record fields, 8 chars each)
        with open(p, "rb") as fh:
            fh.seek(256)
            chh = fh.read(256 * nch)
        off = (16 + 80 + 8 + 8 + 8 + 8 + 8 + 80) * nch  # label, transducer, unit, phys min/max, dig min/max, prefiltering
        spr = [int(chh[off + 8 * i: off + 8 * (i + 1)]) for i in range(nch)]
        implied = 256 * (nch + 1) + nrec * sum(spr) * 3
        m = re.search(r"(sub-\d+)_task-(\w+)_eeg", os.path.basename(p))
        hdr.append(dict(subject=m.group(1), task=m.group(2), n_channels=nch, n_records=nrec, duration_s=nrec * rdur,
                        samples_per_record=spr[0], size=os.path.getsize(p), size_implied_by_header=implied,
                        size_ok=os.path.getsize(p) == implied))
    hd = pd.DataFrame(hdr)
    hd.to_csv(os.path.join(RESULTS_DIR, "bdf_headers.csv"), index=False)
    print(f"\nBDF headers: {len(hd)} files; channel counts {hd.n_channels.value_counts().to_dict()}; "
          f"size == header-implied size in {int(hd.size_ok.sum())} of {len(hd)}; duration {hd.duration_s.min():.0f}–{hd.duration_s.max():.0f} s")
    if (~hd.size_ok).any():
        print("size mismatch vs header:\n", hd[~hd.size_ok].to_string(index=False))
    print("272-channel recordings:", ", ".join(f"{r.subject} {r.task}" for _, r in hd[hd.n_channels != 144].iterrows()))


if __name__ == "__main__":
    main()
