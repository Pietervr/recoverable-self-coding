"""Small provenance/denominator checks; writes only beside this script."""
from pathlib import Path
import csv
import hashlib
import json
import re
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RES = ROOT / "workspace_demo/sergent_port/results"
out = []


def say(s):
    out.append(s)
    print(s)


exact = pd.read_csv(HERE / "d12_exact.csv")
say(f"D12 max absolute error estimate from gamma quadrature: {exact.quad_error.max():.12g}")
for tag in ["active", "passive", "passive_max6"]:
    f = pd.read_csv(RES / f"fits_{tag}.csv")
    n = f[f.model == "model3"]
    counts = n[n.window == 0].groupby("subject").n_test.sum()
    say(f"{tag} total scored counts S1..S20: {counts.tolist()}")
    say(f"{tag} n_test per fold min={n.n_test.min()} max={n.n_test.max()}")
p = pd.read_csv(RES / "llh_passive.csv").set_index(["subject", "window"]).sort_index()
m = pd.read_csv(RES / "llh_passive_max6.csv").set_index(["subject", "window"]).sort_index()
cols = ["model0", "model2B", "model3"]
say(f"passive vs max6 S1..10 all score maxabs={abs(p.loc[1:10,cols]-m.loc[1:10,cols]).max().max():.12g}")
manifest = json.loads((HERE / "input_sha256.json").read_text())
say(f"Read-only SHA256 manifest entries={len(manifest)}")
source = ROOT / "workspace_demo/t1_access/sim_results/d4v12b/calibration_D4.csv"
targets = {3894,8342,6138,10669,11710,8477}
with source.open(newline="") as fh:
    r = csv.DictReader(fh)
    for row_index, row in enumerate(r, start=2):
        assert row_index == r.line_num  # All computed CSV row references are physical lines.
        if r.line_num in targets:
            say(f"physical calibration_D4.csv:{r.line_num}: generator={row['generator']} grid={row['grid']} rep={row['rep']} point={row['selection_ws_point']} SE={row['selection_ws_se']}")
say("PASS: calibration row references match physical line numbers")
for name, expected in manifest.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
say("PASS: all 27 input SHA256 values still unchanged after writing RECORD.md")
aliases = {"R": RES, "D": HERE.parent, "C": HERE,
           "S": ROOT / "workspace_demo/t1_access/sim_results/draft3_reanalyses_2026-10-28",
           "U": ROOT / "workspace_demo/t1_access/reviews/t1_sampling_unit_2026-09-16",
           "P": RES.parent}
record = (HERE / "RECORD.md").read_text()
refs = re.findall(r"\b([RDCUSP])/([\w/.-]+):(\d+)(?:[–-](\d+))?", record)
for alias, name, first, last in refs:
    lines = (aliases[alias] / name).read_text().splitlines()
    assert 1 <= int(first) <= int(last or first) <= len(lines), (alias, name, first, last, len(lines))
say(f"PASS: all {len(refs)} explicit alias/file/line references in RECORD.md exist and are in range")
(HERE / "supplemental_checks.txt").write_text("\n".join(out)+"\n")
