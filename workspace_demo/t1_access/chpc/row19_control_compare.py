"""Ledger row 19, the recovery control: compare the completed scientific outputs of the normal subchain (C1) with the
interrupted-then-resumed subchain (C3) on the same dataset identity - resample index, drawn concepts, every predictor's
band statistics, failed flags - field by field; timing fields and per-record checksums are excluded (they differ by
construction). Prints the comparison and exits 0 on exact agreement, 1 otherwise.

    python chpc/row19_control_compare.py <C1 checkpoint.jsonl> <C3 checkpoint.jsonl> [--status <C1 status> <C3 status>]
"""
import json, sys, argparse

SCIENTIFIC = ("rep", "chosen", "stats", "failed", "failed_reason", "ident", "seed", "n_rep")
EXCLUDED = ("fit_seconds", "sha")


def load(path):
    recs = {}
    for line in open(path):
        if not line.strip():
            continue
        d = json.loads(line)
        assert d["rep"] not in recs, f"{path}: resample {d['rep']} recorded twice"
        recs[d["rep"]] = d
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("c1"); ap.add_argument("c3")
    ap.add_argument("--status", nargs=2, default=None)
    a = ap.parse_args(argv)
    c1, c3 = load(a.c1), load(a.c3)
    ok = True
    print(f"C1 {len(c1)} resamples, C3 {len(c3)} resamples")
    if sorted(c1) != sorted(c3):
        print(f"  resample index sets differ: C1 {sorted(c1)} C3 {sorted(c3)}"); ok = False
    for r in sorted(set(c1) & set(c3)):
        for k in SCIENTIFIC:
            if c1[r].get(k) != c3[r].get(k):
                print(f"  resample {r}: {k} differs"); ok = False
        extra = (set(c1[r]) | set(c3[r])) - set(SCIENTIFIC) - set(EXCLUDED)
        if extra:
            print(f"  resample {r}: unexpected fields {sorted(extra)}"); ok = False
    if a.status:
        s1, s3 = json.load(open(a.status[0])), json.load(open(a.status[1]))
        for k in ("ident", "code_hash", "policy", "n_rep", "segment"):
            if s1.get(k) != s3.get(k):
                print(f"  status: {k} differs ({s1.get(k)} vs {s3.get(k)})"); ok = False
        if s3.get("n_resumed", 0) < 1:
            print("  status: C3 resumed nothing - the interruption did not happen before the segment completed"); ok = False
        if s3.get("n_damaged", 0) or s1.get("n_damaged", 0):
            print("  status: damaged records were recomputed somewhere"); ok = False
        print(f"  C1: new {s1.get('n_new')} resumed {s1.get('n_resumed')} | C3: new {s3.get('n_new')} resumed {s3.get('n_resumed')} tail-repaired {s3.get('n_tail_repaired')}")
        print(f"  original run: C1 {s1.get('original_seconds', 0):.1f} s computed; C3 cached={s3.get('original_cached')}")
    print("VERDICT:", "AGREE - every completed scientific output of the resumed chain equals the uninterrupted chain's" if ok
          else "DIFFER - the resumed chain is not the uninterrupted chain; hold for diagnosis")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
