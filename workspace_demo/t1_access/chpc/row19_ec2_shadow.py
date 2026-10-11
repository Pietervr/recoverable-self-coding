"""Row 19 screen, EC2 qualification part S: admit ONE of the two isolated Lengau shadow jobs (Codex RSC 3dc0daf, the shortest
bounded route; aws_ec2/QUALIFICATION_PLAN.md). Lengau login node, t1py, controller tree.

    t1py chpc/row19_ec2_shadow.py --manifest chpc/row19_screen_manifest.json --s-manifest chpc/row19_qual_S_manifest.json --job 1 [--dry-run]

S recomputes Q1's 48 block coordinates (index 199 = job 1 "S1", index 198 = job 2 "S2", reps 3..26) with the UNCHANGED
row19_shard.py worker under an isolated operational manifest (row19_ec2_state.derive_isolated_S: only storage and the
2,304 core-h reservation cap differ from 43b75f94), into an isolated root and campaign - never the screen root, never the
canonical denominator. The existing CampaignLedger kind `shard` records it (job number = ledger rep, one reservation per job;
a retry needs a raised S cap, i.e. an owner decision). Admission refuses unless ALL hold:
  controls   the controls are the ADOPTED bytes and every controller (this file included) is the latest version's; the latest
             version declares `qualification_S` (root, campaign, plan sha256, isolated manifest sha256) and the programme
             block lists the S campaign (may_be_absent only while its root holds no plan);
  release    aws_ec2/ec2_release_state.json: row 23 declared successful and qualification permitted, each claim backed by the
             pinned file (the same rule the Mac launcher applies);
  inputs     the isolated manifest is the exact derivation and the declared bytes; the plan is the declared fixed plan's job;
             the manifest is present with those bytes in the clone the job runs from;
  STOP       no STOP in the S root or the screen root, no screen ec2/HOLD;
  funding    under the programme admission lock: the programme allocation (100,000) AND the combined refit+S sub-envelope
             (60,000) hold every committed reservation plus this job's full 24 x 48 h = 1,152 core-h.
Then the immutable plan root/plans/job_<n>.json, the reservation, the PBS script (the screen's own refit script with S job
and file names) and qsub; the token is bound to the PBS id. Settlement, statuses, STOP and job-end are the worker's own."""
import os, sys, json, time, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import row19_ec2_state as ES

PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
S_PLAN = os.path.join(T1, "aws_ec2", "qual_S_plan.json")
RELEASE = os.path.join(T1, "aws_ec2", "ec2_release_state.json")
CORES, WALL_S = 24, 48 * 3600
SA = None                                               # row19_screen_admit (tests inject the candidate module)


def _sa():
    global SA
    if SA is None:
        import row19_screen_admit as _m
        SA = _m
    return SA


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def release_problem(path=RELEASE):
    """'' when row 23 is declared successful and qualification permitted, each backed by its pinned file."""
    try:
        r = json.load(open(path))
    except Exception as e:
        return f"the release state is unreadable ({type(e).__name__})"
    base = os.path.dirname(path)
    def backed(d, pk, hk):
        p = d.get(pk); return bool(p) and os.path.exists(os.path.join(base, p)) and sha(os.path.join(base, p)) == d.get(hk)
    r23, q = r.get("row23") or {}, r.get("qualification") or {}
    if not (r23.get("declared_success") and backed(r23, "report_path", "report_sha256")):
        return "row 23 is not declared successful with its pinned report"
    if not (q.get("permitted") and q.get("owner_accepted_ceilings") and backed(q, "record_path", "record_sha256")):
        return "the qualification is not permitted with its pinned review record"
    return ""


def s_job(n, plan_path=S_PLAN):
    d = json.load(open(plan_path))
    j = [x for x in d["jobs"] if x.get("job") == n]
    if len(j) != 1:
        raise ValueError(f"the S plan declares no job {n}")
    j = j[0]
    if (j["cores"], j["walltime_h"], j["reserved_core_h"]) != (CORES, 48, 1152):
        raise ValueError(f"S job {n} is not 24 cores x 48 h = 1,152 core-h")
    return dict(job=n, label=j["label"], role="qual_S", s_plan_sha256=sha(plan_path),
                slots=[dict(slot=s["slot"], rep=s["rep"], indices=list(s["indices"])) for s in j["slots"]])


def decl_problem(ctl, sman_path, prod):
    """'' when the latest controls version declares S exactly as this admission would run it."""
    q = ctl["versions"][-1].get("qualification_S")
    if not isinstance(q, dict):
        return "the latest controls version declares no qualification_S"
    sman = json.load(open(sman_path))
    why = ES.isolated_S_problem(sman, prod, PROD_SHA)
    if why:
        return why
    if (q.get("root"), q.get("campaign")) != (sman["storage"]["root"], sman["storage"]["campaign"]):
        return "the isolated manifest's root/campaign are not the declared ones"
    if q.get("manifest_sha256") != sha(sman_path) or q.get("plan_sha256") != sha(S_PLAN):
        return "the isolated manifest or the fixed S plan is not the declared bytes"
    camps = {(c["path"] if isinstance(c, dict) else c): c for c in ctl["programme"]["campaigns"]}
    c = camps.get(q["campaign"])
    if not (isinstance(c, dict) and c.get("may_be_absent") and c.get("root") == q["root"]):
        return "the programme block does not list the S campaign (may_be_absent, root = the S root)"
    if not any(q["campaign"] in e["campaigns"] and abs(e["cap_core_h"] - 60000.0) < 1e-9 for e in ctl["versions"][-1].get("sub_envelopes") or []):
        return "no combined refit+S sub-envelope of 60,000 core-h is declared"
    return ""


def pbs_script(sman, plan, token, toolchain, clone, manifest_rel):
    s = _sa().refit_pbs_script(sman, plan, token, WALL_S, sman["pbs"]["queue"], toolchain, clone, manifest_rel)
    n = plan["job"]
    s = s.replace(f"#PBS -N t1_screen_{n}", f"#PBS -N t1_qualS_{n}").replace(f"row19_screen_refit_{n}.", f"row19_qualS_{n}.")
    return s.replace(f"screen refit job {n}", f"EC2 qualification S job {n} ({plan['label']})")


def admit(a):
    SAm = _sa()
    prod = json.load(open(a.manifest))
    if sha(a.manifest) != PROD_SHA:
        return "the screen manifest is not 43b75f94"
    why = SAm.controls_problem()
    if why:
        return why
    ctl = SAm.controls()
    why = decl_problem(ctl, a.s_manifest, prod) or release_problem()
    if why:
        return why
    sman = json.load(open(a.s_manifest)); root, camp = sman["storage"]["root"], sman["storage"]["campaign"]
    toolchain, clone = prod["shard"]["toolchain"], prod["shard"]["clone"]
    manifest_rel = os.path.relpath(os.path.abspath(a.s_manifest), T1)
    cm = os.path.join(clone, "workspace_demo", "t1_access", manifest_rel)
    if not os.path.exists(cm) or sha(cm) != sha(a.s_manifest):
        return f"the isolated manifest is not in the job clone with these bytes ({cm})"
    for p in (os.path.join(root, "STOP"), os.path.join(prod["storage"]["root"], "STOP"), ES.paths(prod["storage"]["root"])["hold"]):
        if os.path.exists(p):
            return f"STOP/HOLD in force ({p})"
    plan = s_job(a.job)
    pp = os.path.join(root, "plans", f"job_{a.job}.json")
    if os.path.exists(pp):
        return f"{pp} exists: S job {a.job} was admitted before (a retry needs a raised S cap - an owner decision)"
    import programme_gate as PG
    from row19_ledger import CampaignLedger
    funding = PG.programme_funding(prod)
    proposal = CORES * WALL_S / 3600.0
    with PG.programme_lock(funding):
        why = PG.funding_problem(funding, proposal) or SAm.sub_envelope_problem(camp, proposal, ctl)
        if why:
            return why
        script0 = pbs_script(sman, plan, "TOKEN", toolchain, clone, manifest_rel)
        if a.dry_run:
            print(f"DRY RUN: S job {a.job} ({plan['label']}) would be admitted: {len(plan['slots'])} slots, {proposal:.0f} core-h")
            print(script0); return ""
        os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(toolchain, "jobs"), exist_ok=True)
        L = CampaignLedger(camp, ES.S_RESERVED_CORE_H)
        token, t = L.reserve("shard", a.job, CORES, WALL_S, root, f"row19_ec2_shadow S job {a.job} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
        pdoc = dict(plan, queue=sman["pbs"]["queue"], walltime_s=WALL_S, token=token, created=time.time())
        tmp = pp + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(pdoc, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
        os.link(tmp, pp); os.unlink(tmp)
        sp = os.path.join(toolchain, "jobs", f"row19_qualS_{a.job}.pbs")
        open(sp, "w").write(pbs_script(sman, plan, token, toolchain, clone, manifest_rel))
        r = subprocess.run(["qsub", sp], capture_output=True, text=True)
        with open(os.path.join(toolchain, "programme_admissions.jsonl"), "a") as fh:
            fh.write(json.dumps(dict(at=time.time(), cmd=f"row19_ec2_shadow --job {a.job}", proposal_core_h=proposal, rc=r.returncode)) + "\n")
        if r.returncode != 0:
            return f"qsub failed ({r.stderr.strip()[:200]}); reservation {token} stays reserved and unbound"
        L.bind(token, r.stdout.strip())
        print(f"S job {a.job} ({plan['label']}): reserved {token} ({proposal:.0f} core-h; S spent {t['spent']:.0f}, live {t['live']:.0f} of {t['cap']:.0f}), submitted {r.stdout.strip()}")
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--s-manifest", required=True)
    ap.add_argument("--job", type=int, choices=(1, 2), required=True); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    why = admit(a)
    if why:
        print(f"REFUSED: {why}"); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
