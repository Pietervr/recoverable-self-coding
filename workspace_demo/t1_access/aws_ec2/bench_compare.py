"""Ledger row 23 (revision 2): validate and compare one benchmark attempt against Lengau. Runs on the Lengau login node
under t1py from the controller tree (rsc_screen_ctl/workspace_demo/t1_access), where the frozen task is computed with
the pinned libraries the screen verifier uses:

    $T/t1py bench_compare.py --tree $T/rsc_screen_ctl/workspace_demo/t1_access --ec2 <attempt dir> --lengau-root $T/row19_screen --row6-ref $T/jobs --out report.json

Prints counts and deviations only - never a statistic's value or a decision (sens600 and the screen stay sealed).
EVERY record (EC2 and Lengau) first passes row19_shard.read_record against the frozen task (identity, seed, B, index,
draw, complete payload, own checksum); payload equality is the verifier's canonical float.hex form
(row19_screen_verify.payload over SCI). Exactly reps 3..38 at index 0 per arm: a missing, extra, invalid, unbound or
unattributed coordinate makes the panel INVALID. Failed fits are counted apart from usable parity. Timings are paired by
coordinate, identity and producer and must be positive and finite. Exit 0 only for a complete, valid panel (whatever the
parity outcome); exit 3 otherwise, with the reasons."""
import argparse, csv, glob, hashlib, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# --tree <t1_access> selects the code tree (on Lengau: rsc_screen_ctl's); it must be read before the imports below
T1 = os.path.abspath(sys.argv[sys.argv.index("--tree") + 1]) if "--tree" in sys.argv else os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [T1, os.path.join(T1, "chpc")]
import row19_shard as SH
import row19_screen_verify as V

REPS = list(range(3, 39))
PROD = os.path.join(T1, "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
NUM = ("selection_ws_point", "selection_ws_lo", "selection_ws_hi", "selection_ws_se")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def numeric_leaves(x, path=""):
    if isinstance(x, dict):
        for k in sorted(x):
            yield from numeric_leaves(x[k], f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from numeric_leaves(v, f"{path}[{i}]")
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield path, float(x)


def read_rows(files):
    rows, dup = {}, []
    for f in files:
        for r in csv.DictReader(open(f)):
            k = int(r["rep"])
            if k in rows:
                dup.append(k)
            rows[k] = r
    return rows, dup


def stage1(ec2, ref_dir, problems):
    ref, dup = read_rows(sorted(glob.glob(os.path.join(ref_dir, "row6_lengau_rows_rep*.csv"))))
    if dup or sorted(ref) != [0, 20, 40]:
        problems.append(f"stage 1: Lengau reference reps {sorted(ref)} duplicates {dup}")
        return {}
    out = {}
    for arm in ("A", "B"):
        rows, dup = read_rows(sorted(glob.glob(os.path.join(ec2, f"row6_{arm}", "row6_rows_rep*.csv"))))
        if dup or sorted(rows) != [0, 20, 40]:
            problems.append(f"stage 1 arm {arm}: reps {sorted(rows)} duplicates {dup} (need exactly 0, 20, 40)")
            continue
        worst = {q: 0.0 for q in NUM}; exact = 0; dec = True; failed_same = True
        for rp in (0, 20, 40):
            r, m = rows[rp], ref[rp]
            if r["code_hash"] != m["code_hash"] or r["code_hash"] != "625798e9e7f4":
                problems.append(f"stage 1 arm {arm} rep {rp}: code hash"); continue
            failed_same &= (r["failed"] == m["failed"])
            for q in NUM:
                a, b = float(r[q]), float(m[q])
                if not (math.isfinite(a) and math.isfinite(b)):
                    problems.append(f"stage 1 arm {arm} rep {rp} {q}: non-finite"); continue
                exact += (a.hex() == b.hex()); worst[q] = max(worst[q], abs(a - b))
            dec &= (r["selection_decision"] == m["selection_decision"])
        out[arm] = dict(exact_quantities=f"{exact}/12", decisions_identical=dec, failed_flags_identical=failed_same,
                        max_abs_delta={q: worst[q] for q in NUM})
    return out


def stage2(ec2, lengau_root, problems):
    man = json.load(open(PROD))
    tasks = {rep: SH.task(man, rep) for rep in REPS}
    out = {}
    for arm in ("A", "B"):
        mpath = os.path.join(ec2, "env", f"manifest_{arm}.json")
        msha = sha(mpath) if os.path.exists(mpath) else None
        root = os.path.join(ec2, f"root_{arm}")
        found = sorted(int(os.path.basename(d)[3:]) for d in glob.glob(os.path.join(root, "records", "rep*")))
        extra = [r for r in found if r not in REPS]
        if extra:
            problems.append(f"stage 2 arm {arm}: records for undeclared reps {extra}")
        n_exact = n_usable = n_failed_both = n_failed_mismatch = 0; worst = 0.0; walls = []; ratios = []; bad = []
        for rep in REPS:
            t = tasks[rep]
            try:
                e = SH.read_record(SH.record_path(root, rep, 0), t, 0)
                l = SH.read_record(SH.record_path(lengau_root, rep, 0), t, 0)
            except ValueError as ex:
                bad.append(f"rep {rep}: {ex}"); continue
            if e is None or l is None:
                bad.append(f"rep {rep}: {'EC2' if e is None else 'Lengau'} record missing"); continue
            if sorted(glob.glob(os.path.join(root, "records", f"rep{rep}", "rec_*.json"))) != [SH.record_path(root, rep, 0)]:
                bad.append(f"rep {rep}: extra or aliased EC2 record files")
            tp = os.path.join(root, f"task_{rep}.json")
            try:
                b = json.load(open(tp))["binding"]
                if b.get("manifest_sha") != msha or b.get("ident") != t["ident"] or b.get("rep") != rep:
                    bad.append(f"rep {rep}: binding does not name this arm's manifest/identity")
            except Exception as ex:
                bad.append(f"rep {rep}: binding unreadable ({ex})")
            te_p, tl_p = SH.timing_path(root, rep, 0), SH.timing_path(lengau_root, rep, 0)
            try:
                te, tl = json.load(open(te_p)), json.load(open(tl_p))
            except Exception as ex:
                bad.append(f"rep {rep}: timing unreadable ({ex})"); continue
            why = V.timing_ok(te, rep=rep, index=0, ident=t["ident"], job=f"ec2{arm}", slot=rep - 3) or V.timing_ok(tl, rep=rep, index=0, ident=t["ident"])
            if why:
                bad.append(f"rep {rep}: timing {why}"); continue
            if e["failed"] or l["failed"]:
                if e["failed"] and l["failed"]:
                    n_failed_both += 1
                else:
                    n_failed_mismatch += 1
                continue
            n_usable += 1
            if V.payload(e) == V.payload(l):
                n_exact += 1
            else:
                le, ll = dict(numeric_leaves(e["stats"])), dict(numeric_leaves(l["stats"]))
                if le.keys() != ll.keys():
                    bad.append(f"rep {rep}: statistic layout differs"); continue
                worst = max([worst] + [abs(le[k] - ll[k]) for k in le if math.isfinite(le[k]) and math.isfinite(ll[k])])
            we, wl = float(te["wall_s"]), float(tl["wall_s"])
            if we > 0 and wl > 0:
                walls.append(we); ratios.append(wl / we)
            else:
                bad.append(f"rep {rep}: non-positive wall")
        problems.extend(f"stage 2 arm {arm}: {x}" for x in bad)
        out[arm] = dict(declared=len(REPS), valid_pairs=n_usable + n_failed_both + n_failed_mismatch, usable_both=n_usable,
                        payload_exact=n_exact, failed_both=n_failed_both, failed_one_side=n_failed_mismatch,
                        max_abs_delta_nonexact=worst, invalid=len(bad),
                        ec2_wall_h=(dict(median=statistics.median(walls) / 3600, min=min(walls) / 3600, max=max(walls) / 3600) if walls else None),
                        lengau_over_ec2=(dict(median=statistics.median(ratios), min=min(ratios), max=max(ratios)) if ratios else None))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ec2", required=True); ap.add_argument("--lengau-root", required=True)
    ap.add_argument("--row6-ref", required=True); ap.add_argument("--out", required=True); ap.add_argument("--tree", default=None)
    a = ap.parse_args()
    problems = []
    if sha(PROD) != PROD_SHA:
        sys.exit("the production screen manifest here is not 43b75f94")
    env = os.path.join(a.ec2, "env")
    att = {}
    for arm in ("A", "B"):
        try:
            att[arm] = json.load(open(os.path.join(env, f"attest_{arm}.json")))
            if att[arm].get("problems"):
                problems.append(f"attestation {arm}: {att[arm]['problems']}")
        except Exception as ex:
            problems.append(f"attestation {arm} missing ({ex})")
    if os.path.exists(os.path.join(env, "FAILED")):
        problems.append("instance reported FAILED: " + open(os.path.join(env, "FAILED")).read().strip())
    try:
        oc = json.load(open(os.path.join(env, "outcomes.json")))["outcomes"]
        nonzero = {k: v for k, v in oc.items() if v != 0}
        if len(oc) != 78:
            problems.append(f"outcomes for {len(oc)} of 78 declared processes")
        if nonzero:
            problems.append(f"{len(nonzero)} process(es) not exit 0: {nonzero}")
    except Exception as ex:
        oc = None; problems.append(f"outcomes.json missing ({ex})")
    occ = []
    try:
        occ = [l.split() for l in open(os.path.join(env, "occupancy.txt"))]
    except Exception:
        problems.append("occupancy.txt missing")
    running = [int(x[1]) for x in occ if len(x) >= 2]
    report = dict(profile_B=(att.get("B") or {}).get("profile"), stage1=stage1(a.ec2, a.row6_ref, problems),
                  stage2=stage2(a.ec2, a.lengau_root, problems),
                  occupancy=(dict(samples=len(running), max=max(running), mean=sum(running) / len(running), min=min(running)) if running else None),
                  problems=problems, valid=not problems)
    json.dump(report, open(a.out, "w"), indent=1)
    print(json.dumps({k: report[k] for k in ("profile_B", "stage1", "stage2", "occupancy", "valid")}, indent=1))
    for p in problems:
        print("INVALID:", p)
    return 0 if not problems else 3


if __name__ == "__main__":
    sys.exit(main())
