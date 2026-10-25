"""Chunk paired check: build run records from results/checks/chunkpair/{0,64}/m*.json (pulled from S3) and judge
chunk 64 (candidate) against chunk 0 (reference) with s2.repair_compare (the repair job's PASS rule)."""
import glob, json, os, subprocess, sys
import numpy as np
SP = "/private/tmp/claude-501/-Users-pietervanrooyen-Unimog-Projects/ef8d8958-4777-4d1b-9c40-5dcfa7082e8d/scratchpad"
JD = f"{SP}/jchunk/sergent_port/jitter"
sys.path.insert(0, JD)
os.environ.setdefault("NPROC", "1")
import s2
X = s2.X

dst = f"{SP}/cpair/rows"
subprocess.run(["aws", "--profile", "xtenure-read", "--region", "us-west-2", "s3", "sync",
                "s3://xtenure-cself-pvr-usw2/results/t1_access/jitter_s4/results/checks/chunkpair", dst, "--quiet"], check=True)

def run(chunk):
    rows = []
    for p in glob.glob(f"{dst}/{chunk}/m*.json"):
        with open(p) as f:
            rows.append(json.load(f))
    rows.sort(key=lambda r: r["m"])
    d3 = {f"m{r['m']}": r["scores"]["B3"] - r["scores"]["G3"] for r in rows}
    vals = list(d3.values())
    iv = X.t_interval(vals) if len(vals) == 20 and all(np.isfinite(vals)) else None
    half = 0.5 * (iv.hi - iv.lo) if iv is not None else float("nan")
    return dict(label=f"chunk{chunk}", quad=None, rule=None, code_hash=rows[0]["code"] if rows else None,
                data_ids=[r.get("data_id") for r in rows], delta3=d3, participants=rows, half_width=half,
                numerical_failures=[f"m{r['m']}:{k}" for r in rows for k in r.get("numerical_failures", [])],
                primary=X.set_primary({f"m{r['m']}": r["scores"] for r in rows}) if len(rows) == 20 else None,
                n=len(rows), walls=[r["wall"] for r in rows])

y, x = run("0"), run("64")
print(f"chunk0 {y['n']}/20, chunk64 {x['n']}/20")
if x["n"] < 20 or y["n"] < 20:
    sys.exit(0)
c = s2.repair_compare(x, y)
out = {k: v for k, v in c.items() if k not in ("moved",)}
out["walls"] = dict(chunk0=y["walls"], chunk64=x["walls"])
with open(f"{SP}/cpair/compare.json", "w") as f:
    json.dump(out, f, indent=1, default=str)
print(f"PASS {c['passed']}  max |dDelta3| {c['max_abs_diff']:.3e} ({c['worst_participant']}) vs T {c['tolerance']:.3e}; "
      f"over T {c['over_tolerance']}; flips {sum(len(v) for v in c['selection_flips'].values())}; numerical failures {c['numerical_failures']}; "
      f"nesting {len(c['nesting_failures']['candidate'])}/{len(c['nesting_failures']['reference'])}; same data {c['same_data']}; "
      f"primary {c['primary']}; half-widths {y['half_width']:.3e} / {x['half_width']:.3e}")
print("diffs: " + ", ".join(f"{k} {v:+.1e}" for k, v in c["diffs"].items() if v is not None))
print(f"mean wall chunk0 {np.mean(y['walls']):.0f} s, chunk64 {np.mean(x['walls']):.0f} s")
