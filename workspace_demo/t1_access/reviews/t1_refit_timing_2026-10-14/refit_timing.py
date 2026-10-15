"""Measured Lengau time per refitting resample, sequential against packed (read-only; no fits).

The SI's Methods 5.4.1 states the cost of one refitting resample (steps 1-5 of Procedure 1 on one resampled
dataset, M2S omega = 1, D = 4, one layer, amended start policy) on Lengau, the CHPC cluster (Intel Xeon E5-2690 v3,
2.6 GHz). Two measured sources, both pulled from Lengau and committed beside this script's input paths:

  sequential  chpc/results/row19_shard/live/seq/row19_slice/timing_{0,1,2}.jsonl - one resample at a time on one
              core of a node (jobs 7516928 and 7521637), three datasets, six resamples each;
  packed      chpc/results/row19_shard/live/root/timing/rep{0,1,2}/t_*.json - 24 single-core workers on one
              `serial` node, one resample each (qualification job 7517913 and its successors).

fit_seconds is the worker's own clock around the resample; one core per worker, so hours = core-hours.
Run: python3 refit_timing.py   (writes refit_timing.output.txt beside it)
"""
import glob
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.normpath(os.path.join(HERE, "..", "..", "chpc", "results", "row19_shard", "live"))


def summary(name, hours):
    q = statistics.quantiles(hours, n=4)
    return (f"{name:<11} n={len(hours):>3}  median {statistics.median(hours):5.1f} h  quartiles {q[0]:5.1f}-{q[2]:5.1f} h  "
            f"range {min(hours):5.1f}-{max(hours):5.1f} h")


def main():
    seq = []
    for p in sorted(glob.glob(os.path.join(LIVE, "seq", "row19_slice", "timing_*.jsonl"))):
        for line in open(p):
            r = json.loads(line)
            if not r["failed"]:
                seq.append((os.path.basename(p), r["rep"], r["job"], r["fit_seconds"] / 3600))
    packed = []
    for p in sorted(glob.glob(os.path.join(LIVE, "root", "timing", "rep*", "t_*.json"))):
        r = json.load(open(p))
        if not r["failed"]:
            packed.append((r["rep"], r["index"], r["job"], r["host"], r["fit_seconds"] / 3600))
    out = ["Lengau core-hours per refitting resample (M2S omega = 1, D = 4, one layer)", ""]
    out.append(summary("sequential", [h for *_, h in seq]))
    out.append(summary("packed", [h for *_, h in packed]))
    out += ["", "sequential records (file, resample, job, hours):"]
    out += [f"  {f} {k:>2} {j} {h:6.2f}" for f, k, j, h in seq]
    jobs = sorted({j for _, _, j, _, _ in packed})
    out += ["", f"packed records: {len(packed)} from jobs {', '.join(jobs)}"]
    for j in jobs:
        hs = [h for _, _, jj, _, h in packed if jj == j]
        out.append("  " + summary(j, hs))
    text = "\n".join(out)
    print(text)
    open(os.path.join(HERE, "refit_timing.output.txt"), "w").write(text + "\n")


if __name__ == "__main__":
    main()
