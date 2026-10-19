"""migration_v17 step 7 (Mac, read only): the newest refit watch receipt published at or after --since is a v17 receipt that
binds the epoch-2 activation. Used by ec2_cycle_v17.sh post-activation; also usable alone.

    python3 chpc/migration_v17/receipt_check_v17.py --since <epoch seconds> [--receipts chpc/results/row19_screen/receipts]

Refuses (exit 3) unless the newest chpc/results/row19_screen/receipts/watch_refit_<stamp>.json with time >= --since:
  - is schema/role refit, fresh, production, with an explicitly EMPTY alarm list and the designated view;
  - names a retained verifier document (bound.verify_file) whose bytes match bound.verify_file_sha256 and whose generation is
    version 17 = latest 17, a clean lineage verdict, and the adopted controls 9ea4e727;
  - binds EC2 state (ec2.bound) with BOTH activation_e1.json and activation_e2.json, no HOLD, no STOP and no EC2 problems.
It certifies what the receipt says; the receipt's own freshness and the admission's 2,700 s window stay the controllers' rules."""
import argparse, glob, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
V17_CONTROLS = "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0"


def problems(rdir, since):
    cands = []
    for p in sorted(glob.glob(os.path.join(rdir, "watch_refit_*.json"))):
        try:
            r = json.load(open(p))
        except Exception:
            continue
        if isinstance(r, dict) and isinstance(r.get("time"), (int, float)) and r["time"] >= since:
            cands.append((r["time"], p, r))
    if not cands:
        return None, ["no refit watch receipt published at or after %s in %s" % (since, os.path.relpath(rdir, T1))]
    _, p, r = max(cands)
    why = []
    if r.get("role") != "refit" or not r.get("schema"):
        why.append("not a refit watch receipt")
    if r.get("fresh") is not True or r.get("production") is not True:
        why.append("not fresh production evidence (fresh %r, production %r)" % (r.get("fresh"), r.get("production")))
    if r.get("alarms") != []:
        why.append("alarms %s" % (r.get("alarms") if isinstance(r.get("alarms"), list) else "missing"))
    if not isinstance(r.get("designated"), dict):
        why.append("no designated view")
    b = r.get("bound") or {}
    vf = b.get("verify_file")
    vp = os.path.join(rdir, vf) if isinstance(vf, str) and "/" not in vf else None
    if not vp or not os.path.isfile(vp):
        why.append("the receipt names no retained verifier document")
    else:
        if hashlib.sha256(open(vp, "rb").read()).hexdigest() != b.get("verify_file_sha256"):
            why.append("the verifier document %s is not the bytes the receipt binds" % vf)
        g = (json.load(open(vp)) or {}).get("generation") or {}
        if not (g.get("version") == 17 and g.get("latest") == 17 and g.get("controls_problem") == "" and g.get("controls_sha256") == V17_CONTROLS):
            why.append("the verifier generation is not v17 (version %r latest %r controls %r lineage %r)" % (
                g.get("version"), g.get("latest"), str(g.get("controls_sha256"))[:12], g.get("controls_problem")))
    e = r.get("ec2") or {}
    eb = e.get("bound") if isinstance(e, dict) else None
    if not isinstance(eb, dict):
        why.append("no EC2 binding")
    else:
        acts = eb.get("activations") or {}
        if sorted(acts) != ["activation_e1.json", "activation_e2.json"]:
            why.append("the EC2 binding names activations %s, not exactly e1 and e2" % sorted(acts))
        if eb.get("hold") or eb.get("stop"):
            why.append("an EC2 HOLD or STOP is bound")
    if isinstance(e, dict) and e.get("problems"):
        why.append("EC2 problems %s" % e["problems"][:3])
    return p, why


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, required=True)
    ap.add_argument("--receipts", default=os.path.join(T1, "chpc", "results", "row19_screen", "receipts"))
    a = ap.parse_args(argv)
    p, why = problems(os.path.abspath(a.receipts), a.since)
    if why:
        print("RECEIPT REFUSED%s:" % ((" (" + os.path.basename(p) + ")") if p else "")); [print("  -", w) for w in why]; return 3
    print("RECEIPT OK: %s - fresh production, zero alarms, generation 17 (controls 9ea4e727), designated view, EC2 binding with "
          "activation_e1 and activation_e2" % os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
