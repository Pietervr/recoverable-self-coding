"""Ledger row 19 screen: capture the NODE evidence of a refit job lost with its execution node (controls v18 CANDIDATE, NOT
adopted; promoted to chpc/row19_nodefail_capture.py and pinned by version 18; chpc/candidate_v18_nodefail/DESIGN_v18.md s.4).

THE OWNER runs this on the Lengau login node, in the controller clone, through t1py (CHPC Accounts Policy v2.8 s.2.2(6): no AI
agent operates on Lengau). It is read-only towards PBS, the ledger and the root, and writes ONE small file:

    cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access
    /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_nodefail_capture.py --manifest chpc/row19_screen_manifest.json --role refit --job 54 --dry-run
    /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_nodefail_capture.py --manifest chpc/row19_screen_manifest.json --role refit --job 54

It reads the job's ledger entry (PBS id; refuses when a runner end is recorded), runs `qstat -xf <id>` and `pbsnodes <node>`
ONCE each, extracts only the fields the disposition needs (state, Exit_status, exec_host, stime, mtime, walltimes, memory; the
node's state, comment, last_state_change_time), records the SHA-256 of each raw output but NEVER the output itself, records
whether the job's PBS .out/.err exist, checks the document with the same strict validator the status view and the admission use
(row19_screen_nodefail.evidence_doc_problem), and writes <toolchain>/jobs/row19_screen_refit_<n>.nodefail.json with an exclusive
create (never overwritten). It decides nothing: the status view and the admission recompute the disposition from this file and
the root. It REFUSES, writing nothing, when the PBS history no longer holds the job ("Unknown Job Id": capture is only possible
within PBS's few-day history), when the job is not state F with an integer Exit_status, when it ran on more than one node, when
the node is no longer reported down (once the node is returned to service its last_state_change_time no longer dates the loss),
when the printed times use different UTC offsets, or when an evidence file already exists. Exit 0 written (or dry run), 3 refused."""
import argparse, hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import row19_screen_nodefail as NF

ROLES = {"refit": "shard"}


def run(cmd):
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 255, "", str(e)


def parse_kv(text, header_ok):
    """{key: value} of PBS 'key = value' lines (tab continuation lines appended) after the first header line header_ok accepts."""
    got, cur, on = {}, None, False
    for line in text.splitlines():
        if not on:
            on = header_ok(line.strip()); continue
        if line.startswith("\t") and cur is not None:
            got[cur] += line.strip(); continue
        s = line.strip()
        if " = " in s:
            cur, v = s.split(" = ", 1); got[cur] = v
        elif s and not line.startswith(" "):
            break                                                          # the next record
    return got


def local_epoch(s):
    """(epoch, utc offset) of a PBS-printed time in this host's local time (or an integer epoch as printed: offset None)."""
    t = s.strip()
    if re.fullmatch(r"[0-9]{9,11}", t):
        return int(t), None
    ep = int(time.mktime(time.strptime(t, NF.PBS_TIME_FMT)))
    return ep, time.localtime(ep).tm_gmtoff


def refuse(why):
    print(f"REFUSED (nothing written): {why}")
    return 3


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--role", required=True, choices=sorted(ROLES))
    ap.add_argument("--job", type=int, required=True); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); n = int(a.job)
    if man.get("role") != a.role:
        return refuse(f"{a.manifest} is not the {a.role} manifest")
    led = json.load(open(os.path.join(man["storage"]["campaign"], "budget.json")))
    hits = [e for e in led["entries"].values() if e.get("kind") == ROLES[a.role] and e.get("rep") == n]
    if len(hits) != 1 or not hits[0].get("job_id"):
        return refuse(f"{len(hits)} ledger entries for {a.role} job {n}, or no PBS id bound")
    e = hits[0]; jid = e["job_id"]
    if any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s")):
        return refuse(f"job {n} has a runner end in the ledger: job-end ran, it is not a node lost before the job's end")
    out_p = NF.evidence_path(man, a.role, n)
    if os.path.exists(out_p):
        return refuse(f"{out_p} already exists (evidence is written once; never overwritten)")
    rc, qx, qerr = run(["qstat", "-xf", jid])
    if rc != 0:
        return refuse(f"qstat -xf {jid} failed (rc {rc}): {qerr.strip()[:160]}")
    q = parse_kv(qx, lambda s: s == f"Job Id: {jid}")
    try:
        state, ex, eh = q["job_state"], int(q["Exit_status"]), q["exec_host"]
        nodes = NF.exec_nodes(eh)
        used, req = q["resources_used.walltime"], q["Resource_List.walltime"]
        mem = q["resources_used.mem"]
        mem_kb = int(mem[:-2]) if mem.endswith("kb") else None
        st_ep, st_off = local_epoch(q["stime"]); mt_ep, mt_off = local_epoch(q["mtime"])
    except (KeyError, ValueError) as x:
        return refuse(f"the scheduler record lacks or garbles a needed field ({type(x).__name__}: {x})")
    if state != "F":
        return refuse(f"{jid} is in state {state}, not F")
    if len(nodes) != 1 or mem_kb is None:
        return refuse(f"{jid} ran on {nodes} (exactly one node required) or reports no memory in kb")
    rc, px, perr = run(["pbsnodes", nodes[0]])
    if rc != 0:
        return refuse(f"pbsnodes {nodes[0]} failed (rc {rc}): {perr.strip()[:160]}")
    p = parse_kv(px, lambda s: s == nodes[0])
    try:
        ns, lsct = p["state"], p["last_state_change_time"]
        ls_ep, ls_off = local_epoch(lsct)
    except (KeyError, ValueError) as x:
        return refuse(f"pbsnodes {nodes[0]} lacks or garbles state / last_state_change_time ({type(x).__name__}: {x})")
    if "down" not in [t.strip() for t in ns.split(",")]:
        return refuse(f"node {nodes[0]} is in state {ns!r}, not down: its last state change no longer dates the loss")
    offs = {o for o in (st_off, mt_off, ls_off) if o is not None}
    if len(offs) > 1:
        return refuse(f"the printed times use different UTC offsets {sorted(offs)}")
    off = offs.pop() if offs else time.localtime().tm_gmtoff
    tc_jobs = os.path.join(man["shard"]["toolchain"], "jobs")
    doc = dict(schema=NF.SCHEMA, role=a.role, job=n, job_id=jid, captured_at=round(time.time(), 3), captured_by=os.path.basename(NF.CAPTURE_REL),
               capture_sha256=hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(), utc_offset_s=int(off),
               qstat=dict(job_state=state, Exit_status=ex, exec_host=eh, stime=q["stime"], stime_epoch=st_ep, mtime=q["mtime"], mtime_epoch=mt_ep,
                          resources_used_walltime=used, resources_used_walltime_s=NF.hms_s(used), resources_used_mem_kb=mem_kb,
                          Resource_List_walltime=req, Resource_List_walltime_s=NF.hms_s(req)),
               node=dict(name=nodes[0], state=ns, comment=p.get("comment", ""), last_state_change_time=lsct, last_state_change_epoch=ls_ep),
               pbs_output_present=dict(out=os.path.exists(os.path.join(tc_jobs, f"row19_screen_{a.role}_{n}.out")),
                                       err=os.path.exists(os.path.join(tc_jobs, f"row19_screen_{a.role}_{n}.err"))),
               source_sha256=dict(qstat_xf=hashlib.sha256(qx.encode()).hexdigest(), pbsnodes=hashlib.sha256(px.encode()).hexdigest()))
    b = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode()
    _, why = NF.evidence_doc_problem(b, a.role, n, jid, doc["capture_sha256"])
    if why:
        return refuse(f"the capture does not pass the strict evidence check: {why}")
    print(b.decode(), end="")
    print(f"node {nodes[0]} {ns} ({doc['node']['comment']}), last change {ls_ep - mt_ep:+d} s from the job's mtime; exit {ex}; "
          f"PBS .out/.err present: {doc['pbs_output_present']}")
    if a.dry_run:
        print("DRY RUN: nothing written"); return 0
    fd = os.open(out_p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as fh:
        fh.write(b); fh.flush(); os.fsync(fh.fileno())
    print(f"written {out_p} sha256 {hashlib.sha256(b).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
