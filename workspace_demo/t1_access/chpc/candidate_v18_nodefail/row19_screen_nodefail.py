"""Ledger row 19 screen: the NODE-FAILURE disposition (controls v18 CANDIDATE, NOT adopted; chpc/candidate_v18_nodefail/DESIGN_v18.md).

CASE (R052, 20 Oct 2026). Refit job 54, PBS 7551259.sched01, ended state F with Exit_status 265 (256 + SIGKILL) after 17:21:10 of
a 48 h request, exec_host cnode0240/0*24; `pbsnodes cnode0240` reported state down, comment "node down: communication closed",
last_state_change_time equal to the job's mtime to the second. Slots 19 and 20 had finished (status exit 0, records); slots
0-18 and 21-23 have no status; PBS never staged out the .out/.err (they died with the node's spool). The job is SETTLED
(416.47 core-h). Neither existing disposition fits: closed-no-record (REVISION 8) needs NO status and a retrieved PBS output;
the crashed-worker slot disposition (REVISION 14) needs scheduler and runner exit 4 and a fatal-signal line per missing slot.

THE RULE (node_failure_evidence; ONE implementation, called by the status view to report and by the admission to recompute;
the receipt's copy is never taken on its word). A terminal refit job is DISPOSITIONED (node-failure) only when ALL hold:
  (1) the scheduler observation is state F with an integer exit in KILL_EXITS (265 only: PBS's SIGKILL of the job when its
      execution host is lost; 271 = SIGTERM, the walltime-kill signature of job 3, and every other code are excluded);
  (2) the ledger entry is SETTLED with its settlement certificate (finite charge, note >= 8 chars, non-negative time), the
      note's `Exit_status <n>` equals that exit, NO runner end (runner_exit, runner_ended, runner_wall_s all absent: job-end
      never ran) and a finite `runner_started` (job-start ran, so this is not an admission failure); its token, PBS id and plan
      are the plan's;
  (3) the node evidence file <toolchain>/jobs/row19_screen_refit_<n>.nodefail.json - written once by the reviewed capture
      script chpc/row19_nodefail_capture.py (the OWNER runs it on the Lengau login node) - is a strict, small, hashed document
      (evidence_doc_problem): exact keys, no raw scheduler text, the capture script's SHA-256 equal to the latest controls
      version's pin of that script, its job / PBS id / exit / state the ledger's and the observation's, exactly ONE execution
      host, that host's pbsnodes state containing "down", its last_state_change_time within NODE_TOL_S of the job's mtime, the
      capture after both, every printed time recomputing to its recorded epoch under the recorded UTC offset, the walltime used
      below the request less the deadline reserve (not a walltime kill), the request equal to the plan's, stime <= the ledger's
      runner_started <= mtime, the settlement not before mtime, and no PBS .out/.err present at capture;
  (4) every planned slot EITHER has a COMPLETED status (readable, this job and slot, exit 0 not boolean, nothing left, its new +
      resumed exactly the plan's indices, rep the plan's, host = the down node, ended no later than mtime + NODE_TOL_S) whose
      coordinates are valid verified records with valid timing (a NEW coordinate's timing naming this job and slot), OR has NO
      status at all; no other status is scoped to the PBS id; a status of any other kind (exit 75 / 4 / anything else, left
      work, wrong assignment, unreadable) refuses the class;
  (5) a no-status slot's coordinates carry no unit timing naming the job, no temporary/non-canonical file, and no record or
      timing except a LATER bound job's verified planned completion (the R1 rule); its worker log, when present, has no
      "worker job <id> slot <s>: exit" line; EVERY timing file naming the PBS id is a surviving worker's planned coordinate in
      its slot at its canonical path (the V15-1 rule).
Then the summary carries `node_disposition`; ONLY the scheduler-exit alarm, the missing-runner-end alarm and the no-status slots'
missing-status alarms are not raised; every survivor is reconciled exactly as an ordinary worker; the no-status slots'
coordinates are accounted `uncompleted` with origin "node-failure" and return to the planner. The cause is infrastructure:
nothing here is a crashed-worker slot disposition, so crash_history (the two-crash rule) never counts these coordinates. The
charge stays; nothing is credited; a node-dispositioned job never qualifies a pilot."""
import calendar, hashlib, json, math, os, re, time

SCHEMA = "row19-screen-nodefail-1"
NODE_KIND = "node-failure"
KILL_EXITS = (265,)                         # 256 + 9 (SIGKILL). 271 (256 + SIGTERM) is the walltime kill and stays excluded.
NODE_TOL_S = 120                            # |pbsnodes last_state_change_time - job mtime|, and the clock slack elsewhere
CAPTURE_REL = "chpc/row19_nodefail_capture.py"
MAX_BYTES = 4096
MAX_STR = 160
PBS_TIME_FMT = "%a %b %d %H:%M:%S %Y"        # PBS Pro's printed times (qstat -xf stime/mtime, pbsnodes last_state_change_time)

TOP_KEYS = ("schema", "role", "job", "job_id", "captured_at", "captured_by", "capture_sha256", "utc_offset_s", "qstat", "node",
            "pbs_output_present", "source_sha256")
QSTAT_KEYS = ("job_state", "Exit_status", "exec_host", "stime", "stime_epoch", "mtime", "mtime_epoch", "resources_used_walltime",
              "resources_used_walltime_s", "resources_used_mem_kb", "Resource_List_walltime", "Resource_List_walltime_s")
NODE_KEYS = ("name", "state", "comment", "last_state_change_time", "last_state_change_epoch")
POUT_KEYS = ("out", "err")
SRC_KEYS = ("qstat_xf", "pbsnodes")
HOST_PART = re.compile(r"^([A-Za-z0-9._-]+)/[0-9]+(?:\*[0-9]+)?$")
EXIT_RE = re.compile(r"Exit_status (-?\d+)\b")


def evidence_name(role, n):
    return f"row19_screen_{role}_{int(n)}.nodefail.json"


def evidence_path(man, role, n):
    return os.path.join(man["shard"]["toolchain"], "jobs", evidence_name(role, n))


def capture_pin():
    """The latest controls version's pin of the capture script, or None (v17 pins none: the class then never applies)."""
    try:
        import row19_screen_admit as SA
        h = SA.controls()["versions"][-1]["files"].get(CAPTURE_REL)
        return h if SA._hex64(h) else None
    except Exception:
        return None


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _hex64(x):
    return isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x)


def hms_s(v):
    """'17:21:10' -> 62470 (hours may exceed 24); anything else raises ValueError."""
    m = re.fullmatch(r"([0-9]+):([0-5][0-9]):([0-5][0-9])", v if isinstance(v, str) else "")
    if not m:
        raise ValueError(f"not a [h]h:mm:ss duration: {v!r}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def pbs_epoch(s, utc_offset_s):
    """A PBS-printed time -> epoch seconds: an integer epoch as printed, or the ctime form read in the capture host's local time
    (UTC offset recorded by the capture). Raises ValueError otherwise."""
    if not isinstance(s, str):
        raise ValueError("not a string")
    t = s.strip()
    if re.fullmatch(r"[0-9]{9,11}", t):
        return int(t)
    return calendar.timegm(time.strptime(t, PBS_TIME_FMT)) - int(utc_offset_s)


def exec_nodes(exec_host):
    """['cnode0240'] from 'cnode0240/0*24'; ValueError for anything that is not '+'-joined host/index[*n] parts."""
    parts = (exec_host or "").split("+") if isinstance(exec_host, str) else []
    out = []
    for p in parts:
        m = HOST_PART.match(p)
        if not m:
            raise ValueError(f"exec_host part {p!r} is not host/index[*ncpus]")
        if m.group(1) not in out:
            out.append(m.group(1))
    if not out:
        raise ValueError("no exec_host")
    return out


def _no_constant(c):
    raise ValueError(f"non-finite constant {c}")


def _strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            for s in _strings(v):
                yield s


def evidence_doc_problem(b, role, n, jid, pin):
    """(doc, '') when the evidence bytes are a strict node-failure capture of job n / PBS id jid by the pinned capture script,
    internally consistent; (None, reason) otherwise. Raw scheduler output is refused: exact key sets, every string at most
    MAX_STR characters on one line with no 'key = value' or 'Job Id:' text, and the whole file at most MAX_BYTES."""
    if not isinstance(b, (bytes, bytearray)) or len(b) > MAX_BYTES:
        return None, f"the evidence is not a file of at most {MAX_BYTES} bytes (a raw scheduler capture is never evidence)"
    try:
        doc = json.loads(b.decode("utf-8"), parse_constant=_no_constant)
    except Exception as e:
        return None, f"the evidence is not strict JSON ({type(e).__name__})"
    if not isinstance(doc, dict) or tuple(sorted(doc)) != tuple(sorted(TOP_KEYS)):
        return None, "the evidence does not have exactly the declared top-level keys"
    for k, keys in (("qstat", QSTAT_KEYS), ("node", NODE_KEYS), ("pbs_output_present", POUT_KEYS), ("source_sha256", SRC_KEYS)):
        if not isinstance(doc[k], dict) or tuple(sorted(doc[k])) != tuple(sorted(keys)):
            return None, f"the evidence's {k} does not have exactly the declared keys"
    for s in _strings(doc):
        if len(s) > MAX_STR or "\n" in s or "\r" in s or " = " in s or "Job Id:" in s:
            return None, "the evidence carries raw scheduler text (a multi-line, long or 'key = value' string); only extracted fields are evidence"
    if doc["schema"] != SCHEMA or doc["role"] != role or not _int(doc["job"]) or doc["job"] != int(n) or doc["job_id"] != jid:
        return None, f"the evidence is not schema {SCHEMA} of {role} job {n} ({jid})"
    if doc["captured_by"] != os.path.basename(CAPTURE_REL) or not _hex64(pin) or doc["capture_sha256"] != pin:
        return None, "the evidence was not written by the pinned capture script (capture_sha256 is not the latest controls version's pin)"
    if not (_num(doc["captured_at"]) and doc["captured_at"] > 0) or not _int(doc["utc_offset_s"]) or abs(doc["utc_offset_s"]) > 14 * 3600:
        return None, "the evidence's capture time or UTC offset is not valid"
    q, nd = doc["qstat"], doc["node"]
    for k in ("stime_epoch", "mtime_epoch", "resources_used_walltime_s", "resources_used_mem_kb", "Resource_List_walltime_s", "Exit_status"):
        if not _int(q[k]):
            return None, f"the evidence's qstat {k} is not an integer"
    if not _int(nd["last_state_change_epoch"]):
        return None, "the evidence's last_state_change_epoch is not an integer"
    if not all(_hex64(doc["source_sha256"][k]) for k in SRC_KEYS) or any(not isinstance(doc["pbs_output_present"][k], bool) for k in POUT_KEYS):
        return None, "the evidence's source digests or PBS-output flags are malformed"
    try:
        off = doc["utc_offset_s"]
        if (pbs_epoch(q["stime"], off) != q["stime_epoch"] or pbs_epoch(q["mtime"], off) != q["mtime_epoch"]
                or pbs_epoch(nd["last_state_change_time"], off) != nd["last_state_change_epoch"]):
            return None, "a printed time does not recompute to its recorded epoch under the recorded UTC offset"
        if hms_s(q["resources_used_walltime"]) != q["resources_used_walltime_s"] or hms_s(q["Resource_List_walltime"]) != q["Resource_List_walltime_s"]:
            return None, "a printed walltime does not recompute to its recorded seconds"
        nodes = exec_nodes(q["exec_host"])
    except (ValueError, OverflowError) as e:
        return None, f"the evidence's printed fields do not parse ({e})"
    if len(nodes) != 1 or nodes[0] != nd["name"]:
        return None, f"the job ran on {nodes}, not exactly the one captured node {nd['name']!r}"
    return doc, ""


def node_failure_evidence(man, role, n, e, plan, jid, obs, ev_bytes, units, entries, root=None, slot_map=None, pin=None, reserve_s=None):
    """(disposition, '') when job n is a node-failure job on THIS evidence (module docstring, conditions 1-5); (None, reason)
    otherwise. `obs` is the scheduler observation (state, exit); `e` the ledger entry; `entries` every ledger entry (producer
    numbering for later completions); `pin` the capture script's pinned SHA-256; `reserve_s` the job's deadline reserve."""
    import row19_screen_admit as SA
    n = int(n)
    if role != "refit":
        return None, "only refit jobs carry node-failure dispositions"
    ex = (obs or {}).get("exit")
    if (obs or {}).get("state") != "F" or not _int(ex) or ex not in KILL_EXITS:
        return None, f"the scheduler observation is not state F with an exit in the node-failure kill set {list(KILL_EXITS)}"
    if e.get("state") != "settled" or not (_num(e.get("settled_core_h")) and e["settled_core_h"] >= 0) \
            or not (_num(e.get("settled_at")) and e["settled_at"] >= 0) or not (isinstance(e.get("settle_note"), str) and len(e["settle_note"].strip()) >= 8):
        return None, "the ledger entry is not SETTLED with settlement evidence (charge, note, non-negative time)"
    m = EXIT_RE.search(e["settle_note"])
    if not m or int(m.group(1)) != ex:
        return None, f"the settlement note's Exit_status is not the observed {ex}"
    if any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s")):
        return None, "the ledger records a runner end (job-end ran: not a node lost before the job's end)"
    if not (_num(e.get("runner_started")) and e["runner_started"] > 0):
        return None, "the ledger records no runner start (job-start never ran: an admission failure is not excluded)"
    if not jid or e.get("job_id") != jid or not e.get("token") or plan.get("token") != e.get("token") or plan.get("job") != n:
        return None, "the plan is not this entry's token, job and PBS id"
    doc, why = evidence_doc_problem(ev_bytes, role, n, jid, pin)
    if why:
        return None, why
    q, nd = doc["qstat"], doc["node"]
    tol = NODE_TOL_S
    if q["job_state"] != "F" or q["Exit_status"] != ex:
        return None, f"the captured scheduler record is state {q['job_state']} exit {q['Exit_status']}, not F {ex}"
    if "down" not in [t.strip() for t in str(nd["state"]).split(",")]:
        return None, f"the captured node {nd['name']} is in state {nd['state']!r}, not down"
    delta = nd["last_state_change_epoch"] - q["mtime_epoch"]
    if abs(delta) > tol:
        return None, f"the node's last state change is {delta:+d} s from the job's end (tolerance {tol} s): not the node loss that ended the job"
    if doc["captured_at"] + tol < max(q["mtime_epoch"], nd["last_state_change_epoch"]):
        return None, "the capture is older than the job's end or the node's state change"
    if doc["pbs_output_present"]["out"] or doc["pbs_output_present"]["err"]:
        return None, "the job's PBS output or error file existed at capture: PBS staged the job out, use the output-based dispositions"
    if not (_num(plan.get("walltime_s")) and abs(q["Resource_List_walltime_s"] - plan["walltime_s"]) <= 1.0):
        return None, f"the captured walltime request {q['Resource_List_walltime_s']} s is not the plan's {plan.get('walltime_s')} s"
    rsv = reserve_s if _num(reserve_s) else ((plan.get("envelope") or {}).get("deadline_reserve_s") or (man.get("pbs") or {}).get("deadline_reserve_s"))
    if not _num(rsv) or q["resources_used_walltime_s"] >= q["Resource_List_walltime_s"] - float(rsv):
        return None, "the walltime used reached the request less the deadline reserve (a walltime kill is not a node failure)"
    if not (q["stime_epoch"] - tol <= e["runner_started"] <= q["mtime_epoch"] + tol) or q["resources_used_walltime_s"] > q["mtime_epoch"] - q["stime_epoch"] + tol:
        return None, "the captured start/end times are inconsistent with the ledger's runner start or the walltime used"
    if e["settled_at"] + tol < q["mtime_epoch"]:
        return None, "the settlement precedes the captured job end"
    node = nd["name"]
    root = root or man["storage"]["root"]; slots = plan.get("slots") or []
    slot_map = slot_map or (lambda m_: SA._plan_slot_of(man, m_))
    ident = ((man.get("datasets") or {}).get("identities") or {})
    present, missing, completed = {}, [], []
    for sl in slots:
        s = int(sl["slot"]); want = [int(i) for i in sl["indices"]]
        p = os.path.join(root, "status", f"job{jid}.slot{s}.json")
        if not os.path.exists(p):
            missing.append(sl); continue
        try:
            st = SA._strict_load(p)
        except Exception:
            return None, f"slot {s}: its worker status is unreadable"
        if not isinstance(st, dict) or st.get("job") != jid or st.get("slot") != s or not _int(st.get("exit")) or st["exit"] != 0:
            return None, f"slot {s}: its status is not this job's slot with exit 0 (a partial, HELD or failed worker is not a node-failure survivor)"
        if st.get("left") != [] or st.get("rep") != int(sl["rep"]) or st.get("indices") != want \
                or not isinstance(st.get("new"), list) or not isinstance(st.get("resumed"), list) or sorted(st["new"] + st["resumed"]) != sorted(want):
            return None, f"slot {s}: its status is not a completed assignment (nothing left, new + resumed = the plan's indices)"
        if st.get("host") != node:
            return None, f"slot {s}: its status names host {st.get('host')!r}, not the down node {node}"
        if not (_num(st.get("ended")) and st["ended"] <= q["mtime_epoch"] + tol):
            return None, f"slot {s}: its status ended after the job's captured end"
        for i in want:
            k = f"{int(sl['rep'])}/{i}"; u = units.get(k) or {}; t = u.get("timing") or {}
            if not ((u.get("record") or {}).get("ok") and t.get("ok") is True):
                return None, f"slot {s}: completed coordinate {k} has no valid verified record with valid timing"
            if i in st["new"] and (t.get("job") != jid or t.get("slot") != s):
                return None, f"slot {s}: new coordinate {k}'s timing names {t.get('job')} slot {t.get('slot')}"
            completed.append(k)
        present[s] = st
    want_scoped = sorted(f"job{jid}.slot{s}.json" for s in present)
    if sorted(SA.status_scoped(root, jid)) != want_scoped:
        return None, f"status evidence scoped to {jid} is not exactly the completed workers' statuses"
    gone = {f"{int(sl['rep'])}/{int(i)}": int(sl["slot"]) for sl in missing for i in sl["indices"]}
    named = sorted(k for k, u in units.items() if ((u or {}).get("timing") or {}).get("job") == jid and k in gone)
    if named:
        return None, f"unit(s) {named[:3]} at a no-status slot's coordinates carry timing naming {jid}"
    for sl in missing:
        lp = os.path.join(root, "logs", f"job{jid}.slot{int(sl['slot'])}.log")
        if os.path.exists(lp):
            try:
                txt = open(lp, "rb").read().decode("utf-8", errors="replace")
            except OSError:
                return None, f"slot {sl['slot']}: its worker log is unreadable"
            if any(l.startswith(f"worker job {jid} slot {int(sl['slot'])}: exit ") for l in txt.splitlines()):
                return None, f"slot {sl['slot']}: its worker log reports an exit but no status exists (not a worker lost with its node)"
    surv = {f"{int(sl['rep'])}/{int(i)}": int(sl["slot"]) for sl in slots if int(sl["slot"]) in present for i in sl["indices"]}
    for rel in SA.timing_scan(root, jid):                               # the V15-1 rule: every same-job timing is a survivor's
        mt = SA.TIMING_REL.match(rel)
        if not mt:
            return None, f"timing evidence of unknown attribution ({rel})"
        try:
            t = SA._strict_load(os.path.join(root, rel))
        except Exception:
            return None, f"timing evidence of unknown attribution ({rel})"
        if not isinstance(t, dict) or t.get("job") != jid or not all(_int(t.get(f)) for f in ("rep", "index", "slot")):
            return None, f"timing {rel} names {jid} without integer rep, index and slot"
        if rel != f"timing/rep{t['rep']}/t_{t['index']:03d}.json":
            return None, f"timing {rel} is not at its canonical path (it names {t['rep']}/{t['index']})"
        if surv.get(f"{t['rep']}/{t['index']}") != t["slot"]:
            return None, f"timing {rel} names {jid} slot {t['slot']}, not a completed worker's planned coordinate and slot"
    num_of = {x.get("job_id"): int(x["rep"]) for x in entries if x.get("kind") == SA.ROLES[role] and x.get("job_id")}
    plans = {}

    def pso(m_):
        if m_ not in plans:
            plans[m_] = slot_map(m_)
        return plans[m_]
    for k in sorted(gone):
        files, odd = SA.coordinate_files(man, root, role, k)
        if odd:
            return None, f"coordinate {k}: temporary or non-canonical output files {[os.path.basename(p) for p in odd][:3]}"
        if files or (units.get(k) or {}).get("record") is not None:
            why = SA.later_completion(man, root, role, units, k, n, num_of, pso)
            if why:
                return None, f"coordinate {k} holds output that is not a later bound job's planned completion ({why})"
    pp = os.path.join(root, "plans", f"job_{n}.json")
    return dict(kind=NODE_KIND, job_id=jid, scheduler_state="F", scheduler_exit=ex, runner_exit=None,
                settled_core_h=e["settled_core_h"], settle_note=e["settle_note"], settled_at=e["settled_at"], token=e["token"],
                plan_sha256=SA.sha_file(pp), evidence_file=evidence_name(role, n), evidence_sha256=hashlib.sha256(ev_bytes).hexdigest(),
                node=node, node_state=nd["state"], node_comment=nd["comment"], node_change_epoch=nd["last_state_change_epoch"],
                job_mtime_epoch=q["mtime_epoch"], node_change_minus_mtime_s=delta, walltime_used_s=q["resources_used_walltime_s"],
                completed_slots=sorted(present), no_status_slots=sorted(int(sl["slot"]) for sl in missing),
                completed=sorted(completed), uncompleted=sorted(gone), counts_as_crash=False,
                note="the execution node was lost (pbsnodes down at the job's end): charged, no completion or credit for the no-status "
                     "slots, whose coordinates return to the planner and never count toward the crash rule; completed slots keep their "
                     "records; the job never qualifies"), ""
