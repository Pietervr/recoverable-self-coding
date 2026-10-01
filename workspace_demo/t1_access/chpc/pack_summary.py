#!/usr/bin/env python3
"""Summarise the packed benchmark (row 18 stage 1b): per member, the fit time across the N concurrent copies.

    pack_summary.py <dir with copy_*.log>

Each log is one bench.py --D 4 run. Prints min / median / max fit seconds per member, the count of copies
that converged 8/8, and the number of logs that failed to produce a table.
"""
import glob
import re
import statistics
import sys
from collections import defaultdict

ROW = re.compile(r"^(M\w+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)/(\d+)\s+(\d+)\s+([\d.]+)\s*$")


def main(d):
    fit = defaultdict(list)
    conv = defaultdict(int)
    logs = sorted(glob.glob(f"{d}/copy_*.log"))
    bad = []
    for path in logs:
        rows = 0
        for line in open(path):
            m = ROW.match(line)
            if m:
                rows += 1
                name, _c, fit_s, _per, nc, ns, _nfev, _score = m.groups()
                fit[name].append(float(fit_s))
                conv[name] += int(nc == ns)
        if rows == 0:
            bad.append(path)
    print(f"{len(logs)} logs, {len(bad)} without a table")
    for p in bad:
        print("  failed:", p)
    print(f"{'member':6s} {'n':>3s} {'min s':>8s} {'median':>8s} {'max s':>8s} {'conv 8/8':>9s}")
    for name in ["M0", "M2B", "M2H", "M2S", "M2K", "M3", "M3H", "M3V", "M3L"]:
        v = fit.get(name)
        if not v:
            continue
        print(f"{name:6s} {len(v):3d} {min(v):8.2f} {statistics.median(v):8.2f} {max(v):8.2f} {conv[name]:9d}")


if __name__ == "__main__":
    main(sys.argv[1])
