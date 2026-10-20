"""migration_v18 step 5 (Mac, read only): the newest refit watch receipt published at or after --since is a v18 receipt that
keeps epoch 2 bound and carries the reviewed job-54 node disposition (the migration_v17 receipt_check_v17.py, re-pointed). Used
by receipts_v18.sh; also usable alone.

    python3 chpc/migration_v18/receipt_check_v18.py --since <epoch seconds> [--receipts chpc/results/row19_screen/receipts]

Refuses (exit 3) unless the newest chpc/results/row19_screen/receipts/watch_refit_<stamp>.json with time >= --since:
  - is schema/role refit, fresh, production, with an explicitly EMPTY alarm list and the designated view;
  - names a retained verifier document (bound.verify_file) whose bytes match bound.verify_file_sha256 and whose generation is
    version 18 = latest 18, a clean lineage verdict, and the v18 controls 452b82df;
  - binds EC2 state (ec2.bound) with EXACTLY activation_e1.json and activation_e2.json, no HOLD, no STOP and no EC2 problems
    (epoch 2 stays active through v18);
  - carries refit job 54 as a node-failure disposition (jobs.54.node_disposition, kind node-failure, counts_as_crash false)
    whose evidence is the retained capture 730ea262, bound as bound.node_evidence.54 with that sha256, and no other job with a
    node disposition.
It certifies what the receipt says; the admission recomputes the disposition itself, and the receipt's own freshness and the
admission's 2,700 s window stay the controllers' rules."""
import argparse, glob, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
V18_CONTROLS = "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b"
NODE_EV = ("row19_screen_refit_54.nodefail.json", "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")


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
        if not (g.get("version") == 18 and g.get("latest") == 18 and g.get("controls_problem") == "" and g.get("controls_sha256") == V18_CONTROLS):
            why.append("the verifier generation is not v18 (version %r latest %r controls %r lineage %r)" % (
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
    jobs = r.get("jobs") if isinstance(r.get("jobs"), dict) else {}
    nd = (jobs.get("54") or {}).get("node_disposition") if isinstance(jobs.get("54"), dict) else None
    if not isinstance(nd, dict) or nd.get("kind") != "node-failure" or nd.get("counts_as_crash") is not False \
            or nd.get("evidence_file") != NODE_EV[0] or nd.get("evidence_sha256") != NODE_EV[1]:
        why.append("refit job 54 is not a node-failure disposition on the retained evidence %s %s" % (NODE_EV[0], NODE_EV[1][:8]))
    ne = (b.get("node_evidence") or {}) if isinstance(b.get("node_evidence"), dict) else {}
    if sorted(ne) != ["54"] or (ne.get("54") or {}).get("sha256") != NODE_EV[1] or (ne.get("54") or {}).get("file") != NODE_EV[0]:
        why.append("bound.node_evidence is not exactly job 54's retained evidence (%s)" % sorted(ne))
    others = sorted(n for n, s in jobs.items() if n != "54" and isinstance(s, dict) and "node_disposition" in s)
    if others:
        why.append("other jobs carry node dispositions %s (each needs its own reviewed evidence)" % others[:5])
    return p, why


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, required=True)
    ap.add_argument("--receipts", default=os.path.join(T1, "chpc", "results", "row19_screen", "receipts"))
    a = ap.parse_args(argv)
    p, why = problems(os.path.abspath(a.receipts), a.since)
    if why:
        print("RECEIPT REFUSED%s:" % ((" (" + os.path.basename(p) + ")") if p else "")); [print("  -", w) for w in why]; return 3
    print("RECEIPT OK: %s - fresh production, zero alarms, generation 18 (controls 452b82df), designated view, EC2 binding with "
          "activation_e1 and activation_e2, refit job 54 node-dispositioned on the retained evidence 730ea262" % os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
