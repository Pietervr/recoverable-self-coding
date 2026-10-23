"""migration_v20 step 5 (Mac, read only): the newest refit watch receipt published at or after --since is a v20 receipt that
keeps epoch 2 bound and carries the reviewed job-54 node disposition (the migration_v19 receipt_check_v19.py, re-pointed). Used
by receipts_v20.sh; also usable alone.

    python3 chpc/migration_v20/receipt_check_v20.py --since <epoch seconds> --phase pre|post [--receipts chpc/results/row19_screen/receipts]

Refuses (exit 3) unless the newest chpc/results/row19_screen/receipts/watch_refit_<stamp>.json with time >= --since:
  - is schema/role refit, fresh, production, with an explicitly EMPTY alarm list and the designated view;
  - names a retained verifier document (bound.verify_file) whose bytes match bound.verify_file_sha256 and whose generation is
    version 20 = latest 20, a clean lineage verdict, and the v20 controls 4e64982b;
  - binds EC2 state (ec2.bound) with EXACTLY activation_e1.json and activation_e2.json (--phase pre: before the close) or
    EXACTLY activation_e1/e2/e3.json (--phase post), no HOLD, no STOP and no EC2 problems; post-close the designated view shows
    EC2-designated unclaimed 0 and adds up (designated = done + in flight + Lengau plannable + rescue-pending);
  - carries refit job 54 as a node-failure disposition (jobs.54.node_disposition, kind node-failure, counts_as_crash false)
    whose evidence is the retained capture 730ea262, bound as bound.node_evidence.54 with that sha256 (v20: other node or
    operational-loss dispositions are no longer refused here - the admission recomputes every disposition itself).
It certifies what the receipt says; the admission recomputes the disposition itself, and the receipt's own freshness and the
admission's 2,700 s window stay the controllers' rules."""
import argparse, glob, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
V20_CONTROLS = "4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c"
NODE_EV = ("row19_screen_refit_54.nodefail.json", "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")


def problems(rdir, since, phase="pre"):
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
        if not (g.get("version") == 20 and g.get("latest") == 20 and g.get("controls_problem") == "" and g.get("controls_sha256") == V20_CONTROLS):
            why.append("the verifier generation is not v20 (version %r latest %r controls %r lineage %r)" % (
                g.get("version"), g.get("latest"), str(g.get("controls_sha256"))[:12], g.get("controls_problem")))
    e = r.get("ec2") or {}
    eb = e.get("bound") if isinstance(e, dict) else None
    if not isinstance(eb, dict):
        why.append("no EC2 binding")
    else:
        acts = eb.get("activations") or {}
        want = ["activation_e1.json", "activation_e2.json"] + (["activation_e3.json"] if phase == "post" else [])
        if sorted(acts) != want:
            why.append("the EC2 binding names activations %s, not exactly %s" % (sorted(acts), want))
        if eb.get("hold") or eb.get("stop"):
            why.append("an EC2 HOLD or STOP is bound")
    if isinstance(e, dict) and e.get("problems"):
        why.append("EC2 problems %s" % e["problems"][:3])
    d = r.get("designated") if isinstance(r.get("designated"), dict) else {}
    if phase == "post" and d:
        pend = len(d.get("rescue_pending") or [])
        if d.get("ec2_waiting_unclaimed") != 0:
            why.append("post-close the designated view still shows %r EC2-designated unclaimed coordinates" % d.get("ec2_waiting_unclaimed"))
        if (d.get("done", 0) + d.get("in_flight", 0) + d.get("lengau_plannable", 0) + pend) != d.get("designated"):
            why.append("the designated view does not add up: %s" % {k: d.get(k) for k in ("designated", "done", "in_flight", "lengau_plannable")})
        print("post-close designated view: designated %s, done %s, in flight %s, Lengau plannable %s, EC2 waiting %s, rescue-pending %d" % (
            d.get("designated"), d.get("done"), d.get("in_flight"), d.get("lengau_plannable"), d.get("ec2_waiting_unclaimed"), pend))
    jobs = r.get("jobs") if isinstance(r.get("jobs"), dict) else {}
    nd = (jobs.get("54") or {}).get("node_disposition") if isinstance(jobs.get("54"), dict) else None
    if not isinstance(nd, dict) or nd.get("kind") != "node-failure" or nd.get("counts_as_crash") is not False \
            or nd.get("evidence_file") != NODE_EV[0] or nd.get("evidence_sha256") != NODE_EV[1]:
        why.append("refit job 54 is not a node-failure disposition on the retained evidence %s %s" % (NODE_EV[0], NODE_EV[1][:8]))
    ne = (b.get("node_evidence") or {}) if isinstance(b.get("node_evidence"), dict) else {}
    if (ne.get("54") or {}).get("sha256") != NODE_EV[1] or (ne.get("54") or {}).get("file") != NODE_EV[0]:
        why.append("bound.node_evidence does not bind job 54's retained evidence (%s)" % sorted(ne))
    return p, why


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, required=True)
    ap.add_argument("--phase", choices=("pre", "post"), required=True)
    ap.add_argument("--receipts", default=os.path.join(T1, "chpc", "results", "row19_screen", "receipts"))
    a = ap.parse_args(argv)
    p, why = problems(os.path.abspath(a.receipts), a.since, a.phase)
    if why:
        print("RECEIPT REFUSED%s:" % ((" (" + os.path.basename(p) + ")") if p else "")); [print("  -", w) for w in why]; return 3
    print("RECEIPT OK: %s - fresh production, zero alarms, generation 20 (controls 4e64982b), designated view, EC2 binding with "
          "activation_e1 and activation_e2%s, refit job 54 node-dispositioned on the retained evidence 730ea262" % (
              os.path.basename(p), " and activation_e3 (the close; EC2 waiting 0)" if a.phase == "post" else " (pre-close)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
