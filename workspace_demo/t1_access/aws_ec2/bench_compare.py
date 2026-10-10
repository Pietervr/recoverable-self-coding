"""Ledger row 23: compare the EC2 benchmark against Lengau (Mac side). Prints deviations and counts only - never a
statistic's value or a decision - so sens600 stays blinded and no screen quantity is read.

    python3 bench_compare.py --ec2 <downloaded results/t1_access/aws_bench/<run>> --lengau <dir with rep<R>/rec_000.json + t_000.json>

Stage 1 (row 6 panel): per arm, max |delta| per quantity against Lengau's rows (chpc/results/row6_lengau_rows_rep*.csv),
exact-equality count and decision agreement. Stage 2 (screen refit, index 0 of reps 3..38): per arm, identity agreement,
exact float-bit agreement of the canonical payload (stats, failed, failed_reason, chosen, ident, seed, n_rep; fit_seconds
and sha differ by construction since the record carries its own fit time), max |delta| over every statistic, and the wall
time per refit against the same coordinates' Lengau timing (the speed ratio the costing uses)."""
import argparse, csv, glob, json, math, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
NUM = ("selection_ws_point", "selection_ws_lo", "selection_ws_hi", "selection_ws_se")
PAYLOAD = ("ident", "seed", "n_rep", "rep", "failed", "failed_reason", "chosen")


def leaves(x, path=""):
    if isinstance(x, dict):
        for k in sorted(x):
            yield from leaves(x[k], f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, x


def stage1(ec2):
    ref = {}
    for f in glob.glob(os.path.join(T1, "chpc/results/row6_lengau_rows_rep*.csv")):
        for r in csv.DictReader(open(f)):
            ref[int(r["rep"])] = r
    for arm in ("A", "B"):
        rows = {}
        for f in glob.glob(os.path.join(ec2, f"row6_{arm}", "row6_rows_rep*.csv")):
            for r in csv.DictReader(open(f)):
                rows[int(r["rep"])] = r
        if not rows:
            print(f"stage 1 arm {arm}: no rows yet"); continue
        worst = {q: 0.0 for q in NUM}; exact = 0; total = 0; dec = True
        for rp, r in sorted(rows.items()):
            m = ref[rp]
            assert r["code_hash"] == m["code_hash"], f"rep {rp}: code hash differs"
            for q in NUM:
                d = abs(float(r[q]) - float(m[q])); worst[q] = max(worst[q], d); total += 1; exact += (r[q] == m[q])
            dec &= (r["selection_decision"] == m["selection_decision"])
        print(f"stage 1 arm {arm}: {len(rows)}/3 datasets; exact {exact}/{total} quantities; decisions identical {dec}; "
              + ", ".join(f"{q[10:]} {worst[q]:.3e}" for q in NUM))


def stage2(ec2, lengau):
    for arm, root in (("A", "root_A"), ("B", "root_B")):
        recs = sorted(glob.glob(os.path.join(ec2, root, "records", "rep*", "rec_000.json")))
        if not recs:
            print(f"stage 2 arm {arm}: no records yet"); continue
        n = exact = ident_ok = 0; worst = 0.0; nonfinite = 0; ratios = []; walls = []
        for p in recs:
            rep = os.path.basename(os.path.dirname(p))
            ref_p = os.path.join(lengau, rep, "rec_000.json")
            if not os.path.exists(ref_p):
                print(f"  {rep}: no Lengau reference"); continue
            e, l = json.load(open(p)), json.load(open(ref_p))
            n += 1; ident_ok += (e["ident"] == l["ident"])
            same = all(e.get(k) == l.get(k) for k in PAYLOAD) and e["stats"] == l["stats"]
            exact += same
            le, ll = dict(leaves(e["stats"])), dict(leaves(l["stats"]))
            assert le.keys() == ll.keys(), f"{rep}: statistic layout differs"
            for k in le:
                a, b = le[k], ll[k]
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
                    if math.isfinite(a) and math.isfinite(b):
                        worst = max(worst, abs(a - b))
                    elif not (a == b or (math.isnan(a) and math.isnan(b))):
                        nonfinite += 1
            te = os.path.join(ec2, root, "timing", rep, "t_000.json"); tl = os.path.join(lengau, rep, "t_000.json")
            if os.path.exists(te) and os.path.exists(tl):
                we, wl = json.load(open(te))["wall_s"], json.load(open(tl))["wall_s"]
                walls.append(we / 3600); ratios.append(wl / we)
        print(f"stage 2 arm {arm}: {n} records vs Lengau; identities equal {ident_ok}/{n}; payload float-bit exact {exact}/{n}; "
              f"max |delta| over statistics {worst:.3e}; non-finite mismatches {nonfinite}")
        if walls:
            print(f"  wall per refit on EC2: median {statistics.median(walls):.2f} h (range {min(walls):.2f}-{max(walls):.2f}); "
                  f"Lengau/EC2 speed ratio median {statistics.median(ratios):.2f} (range {min(ratios):.2f}-{max(ratios):.2f})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--ec2", required=True); ap.add_argument("--lengau", required=True)
    a = ap.parse_args()
    stage1(a.ec2); stage2(a.ec2, a.lengau)
