"""Ledger row 19 stage 2: the screen's live view, watch receipt and pilot qualification, per role (Mac). Codex RSC 9202e8b item 5.

EVIDENCE every call: (1) the producer-runtime verdict, `t1py chpc/row19_screen_verify.py --role R` in the screen clone, its stdout
SHA-256 bound; (2) a fresh pull of the role's root and campaign (rotated in only when every pull succeeded); (3) one `qstat -xf`
that must RETURN 0 and describe every job of the role.
RAW ONLY (item 4): nothing here reads a statistic, builds an interval, endpoint, decision or coverage. Records are reported as
valid/invalid with their checksums; the scientific payload never enters this view.
RECONCILIATION per job of the role: a terminal job (F/E/X/gone) has a status for every planned slot; the status's assignment
equals the plan slot's (refit: rep and indices; orig: reps); new / resumed / left partition it; exit 0 iff nothing is left,
75 only with work left, anything else an alarm; every new or resumed unit has a valid record and a valid timing, and a new
unit's timing names this job and slot; worker memory under the stop; scheduler memory under 90 % of the request; a terminal
job's scheduler exit 0 or 75 and its runner end in the ledger; records no plan assigns are foreign (an alarm). Refit task
bindings: every binding must equal what the producer runtime recomputes and name the declared identity. ANCHORS: every
required overlap present, compared and equal on all three anchors; any invalid anchor record or difference is an alarm.
RECEIPT (--publish-receipt): schema row19-screen-watch-1, role, fresh, production, alarms, bound = manifest SHA-256, root,
campaign, code pins, wrapper, every job of the role (PBS id, token, plan SHA-256), every task binding's SHA-256, the anchor
verdict's SHA-256 and the verify document's SHA-256; copied to <root>/gate/watch_<role>_<stamp>.json.
QUALIFICATION (--qualify 1): fresh production evidence, zero alarms, job 1 terminal with scheduler exit 0 or 75, every planned
slot ended 0 with every planned unit a valid record with timing, the three anchors equal; refit: job 1's reps all bound.
REVISION 11 (R052 11 Oct, PBS history expiry): (3) asks `qstat -xf` only of the role's jobs whose ledger entry is NOT settled.
PBS drops finished jobs from its history after a few days and then fails the whole call with "Unknown Job Id" (rc 153), which
held every receipt. A SETTLED entry is observed from its settlement instead (`settle_note`, written by xf_settle from
`qstat -xf` at settlement): state F with the note's Exit_status, carried together with the scheduler facts the settlement
does not hold (scheduler memory, walltime request) from the NEWEST local receipt of this role that is fresh, production and
alarm-free and observed the SAME PBS id from qstat at state F with the SAME exit. The job summary records `observation`
"ledger-settlement", the note's SHA-256 and that receipt (`prior_receipt`: file, SHA-256). A settled note without
`Exit_status <n>` is a failed observation; a settled job no such receipt observed carries no memory and keeps the
no-finite-memory alarm (fail-closed); an unsettled job qstat cannot describe stays a failed observation. The receipt and
qualification formats, and the admission's checks of them, are unchanged.
REVISION 12 (R052 11 Oct, settled before any clean receipt saw it): a refit job settled before a fresh, production,
alarm-free receipt observed it at F carried no memory, and its no-finite-memory alarm then held EVERY later receipt (which
in turn can never become the clean source REVISION 11 needs) - refit job 10 7530233, settled 18:30Z 11 Oct. The settled ids
now also get ONE tolerant `qstat -xf` (the bank status's reviewed pattern, Codex RSC 5183208 (a''): only "Unknown Job Id <a
settled id>" failures are tolerated, any other failure gives no values); a settled job the scheduler still reports at state F
contributes its live `resources_used.mem` and `Resource_List.walltime`. The scheduler memory checked is the LARGEST of the live
value and the REVISION 11 carried value; `memory_evidence` in the job summary names the source(s) ("qstat", the prior
receipt). Neither source -> no memory and the alarm stays (fail-closed). Expiry still never fails the observation; the state
and exit stay the settlement's; unsettled ids are unchanged. The receipt and qualification formats and the admission's checks
are unchanged apart from the added `memory_evidence` field of a ledger-settlement job summary.
REVISION 13 (Codex RSC 7523370 (a), 12 Oct: a newly observed same-job breach could vanish after PBS expiry, because the
REVISION 11 selector read only alarm-free receipts with a direct-qstat observation and fell back to an older, lower, clean
one). The bank status's reviewed rule (Codex c38779c / 5183208) now applies to settled refit jobs, with one restriction that
keeps carry non-recursive: (i) EVERY fresh production receipt of the role, alarmed or not, that recorded the same PBS id at
state F with the same exit is consulted; (ii) only DIRECTLY observed memory is consumed - a summary observed from qstat
(`observation` absent or "qstat") contributes its `mem_kb`, and a ledger-settlement summary contributes only the new field
`qstat_mem_kb`, written by this status solely from its own live tolerant query of the settled id (with `qstat_walltime_req_s`);
a ledger-settlement summary's `mem_kb` (possibly itself carried) is never re-carried; (iii) the checked memory is the LARGEST
of the live value and every directly observed recorded value, and the walltime request comes from the same direct source;
(iv) a receipt whose alarms carry "<role> job <n>: scheduler memory above 90 %" for that job is kept as `memory_breach`
(file, SHA-256) and alarms in every later receipt while that original receipt is retained, whatever lower clean value exists;
other alarms of that receipt are not carried. A settled job first observed by REVISION 13 is therefore durable: its receipt
holds `qstat_mem_kb`, which later receipts consume after PBS expiry even though the summary is labelled ledger-settlement.
No direct value at all -> no memory and the no-finite-memory alarm stays (fail-closed; no clean-check fallback for refit).
`prior_receipt` names the receipt whose value was checked. Qualification and admission are unchanged.
REVISION 7 (Codex RSC 8865474 C2): each job summary also carries `partition`, the sorted new / resumed / left coordinate lists
read from that job's own worker statuses, so the admission reconciles a job's historical outcome, not today's aggregate.

    python chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit [--publish-receipt] [--qualify 1]
Exit 1 on any alarm or when the evidence is not fresh.

REVISION 2 (Codex RSC a1ce224): qualification needs scheduler state F exactly (not E, X or gone), scheduler exit and the
ledger's runner exit both 0 or 75, finite scheduler memory and finite worker memory for every slot; a refit worker's status
must name its task's declared identity; a status file for a job or slot no plan assigns is an alarm; every rep of a STARTED
job (scheduler R or terminal) must have a task binding, checked against the plans rather than the files present; the full
verifier document is saved beside every receipt and copied to the gate; the anchor verdict itself is embedded in the receipt
and the qualification (not only its digest); the job summary carries timings, peaks and failures.

REVISION 3 (Codex RSC ee99ee1, R2 and R3): EVERY job, not only job 1: a terminal job must be scheduler state F with scheduler
and runner exits 0/75 and finite observed scheduler memory; a runner exit outside 0/75 is an alarm whatever the state; every
ended worker needs finite memory and wall time. The status directory is checked against the WHOLE planned job/slot universe
(a status of an unplanned job is an alarm). The producer verifier runs from the CONTROLLER clone named in the lineage
(chpc/row19_screen_controls.json `deployment`), and its document must report the latest controller generation with a clean
lineage check; the producer's binding digests must equal the local snapshot's (one coherent observation); the full verifier
document is saved, copied to the gate and only a SUCCESSFUL copy lets the evidence count as production; the receipt and the
qualification name the verifier file and its SHA-256, and the qualification binds job 1's own tasks only.

REVISION 8 CANDIDATE (Codex R052 record reviews/2026-10-09_refit_wall_kill_codex_record.md, verdicts 1 and 2; NOT adopted):
the fresh observation also retrieves the role/job PBS output (<toolchain>/jobs/row19_screen_<role>_<n>.out, written by the PBS
request row19_screen_admit.py fills) of every job whose ledger entry is settled without a runner end; each retrieval's result is
kept beside the snapshot (jobs/_fetch.json) - a failed, missing or unreadable retrieval proves nothing and leaves the job's alarms
in place. A terminal job is DISPOSITIONED (closed-no-record), reported and not alarmed, only when ALL hold: the scheduler
observation succeeded with state F and an observed integer exit; the ledger entry is SETTLED with settlement evidence (finite
charge, technical note, settlement time) and carries no runner-end field; its plan is the entry's token and job; no status file
is scoped to its PBS id (by name, any slot, planned or unplanned, or by parsed `job`) and no status is unreadable with no job named;
no verifier unit and no timing file anywhere names it, and no timing file is unreadable or temporary; every file at a planned
coordinate is a valid record whose timing names a LATER bound job that planned it in that slot; and the retrieved PBS output names
the PBS id and carries no ADMISSION FAILED. Only then are its bad-scheduler-exit, missing-runner-end and missing-worker-status
alarms suppressed; the summary keeps the actual exit, zero ended/new/resumed/left and absent worker measurements, carries
`disposition` (with the output's SHA-256) and accounts the plan's coordinates as `uncompleted` with origin "plan"; the receipt
binds the output (`bound.job_outputs`). A dispositioned job never qualifies. Every summary also carries the plan's walltime and
the scheduler's observed walltime request (Resource_List.walltime); a difference between them is an alarm. An unreadable status
file is an alarm (it used to stop the view).
REPAIRS of Codex 5cb9a02: the disposition carries the observed settlement certificate (settle_note, settled_at, token, job_id,
plan_sha256 beside the charge) for the admission to compare exactly (R2); a later completion at a disposed coordinate also needs
its current canonical record and timing to be the verified evidence (R1, row19_screen_admit.current_artifacts_problem).

REVISION 14 CANDIDATE (R052 12 Oct, refit job 13 7531397 slot 16 SIGSEGV; NOT adopted): a CRASHED-WORKER SLOT DISPOSITION.
The fresh observation also retrieves the PBS output AND error stream (<toolchain>/jobs/row19_screen_<role>_<n>.out/.err) of every
refit job whose ledger entry is settled with runner exit 4 (HELD); results in jobs/_fetch.json under "<n>" and "<n>.err" (a
failed retrieval proves nothing and leaves the alarms). row19_screen_admit.crashed_slot_evidence (ONE implementation, recomputed
by the admission) decides, from the snapshot's ledger, root, verifier units and those bytes, whether the job's only defect is
planned workers killed by their own fatal signal before any status (conditions in the admission's REVISION 14 note). If so the
summary carries `slot_disposition` (the evidence, both files' SHA-256, the crashed slots with the signal and the exact error
line), the crashed coordinates are accounted `uncompleted` with origin "crashed-slot", the receipt binds both files
(`bound.slot_outputs`) and retains copies beside it, and ONLY the scheduler-exit-4, runner-exit-4 and those slots'
missing-status alarms are not raised; every other check of the job and of its surviving slots is unchanged. Otherwise the
reason is kept as `slot_disposition_held` and the alarms stand. A slot-dispositioned job never qualifies.

REVISION 16 CANDIDATE (controls version 16, the resized screen; NOT adopted): the refit view also reports the DESIGNATED set
(designated_report -> row19_screen_admit.designated_view, the same code the admission dry run prints): S x 0..79 progress, Lengau's
plannable count, the EC2-designated unclaimed coordinates waiting for the provider-epoch package, history outside the set (kept,
counted, never planned), the crash history from this receipt's own slot dispositions and the RESCUE-PENDING list (two
same-envelope crashes; the rescue route declared and disabled). The receipt carries it as `designated` (informational: the
admission recomputes everything itself). Its only alarm is a declaration the lineage does not pin or that does not recompute from
the manifest. Every other check, alarm, receipt field and the qualification are unchanged.

REVISION 18 CANDIDATE (controls version 18; R052 20 Oct, refit job 54 7551259.sched01 lost with node cnode0240; NOT adopted;
chpc/candidate_v18_nodefail/DESIGN_v18.md): a NODE-FAILURE DISPOSITION. The fresh observation also retrieves the node evidence
file <toolchain>/jobs/row19_screen_refit_<n>.nodefail.json (written once by the owner with chpc/row19_nodefail_capture.py) of
every refit job whose ledger entry is settled without a runner end and whose settlement note's Exit_status is in the kill set;
the result is in jobs/_fetch.json under "<n>.nodefail" (a failed retrieval proves nothing and leaves the alarms).
row19_screen_nodefail.node_failure_evidence (ONE implementation, recomputed by the admission) decides from the snapshot's
ledger, root, verifier units and those bytes. If it holds, the summary carries `node_disposition`, the no-status slots'
coordinates are accounted `uncompleted` with origin "node-failure", the receipt binds the evidence (`bound.node_evidence`) and
retains a copy beside it, and ONLY the scheduler-exit, missing-runner-end and those slots' missing-status alarms are not raised;
every completed slot is reconciled as an ordinary worker. Otherwise the reason is kept as `node_disposition_held`. The receipt
prints "DISPOSITIONED (node-failure)". A node-dispositioned job never qualifies, and it is never a crash (the two-crash rule
reads slot dispositions only).

REVISION 19 CANDIDATE (controls version 19; R052 lean T1 plan item 2, owner-approved 20 Oct 2026; NOT adopted;
chpc/candidate_v19_oploss/DESIGN_v19.md): an OPERATIONAL-LOSS DISPOSITION, the general fallback. A terminal refit job that none
of closed-no-record, crashed-slot and node-failure disposition holds is examined by row19_screen_admit.operational_loss_evidence
(ONE implementation, recomputed by the admission; no evidence file). If it holds, the summary carries `operational_loss`; the
no-status coordinates (less salvaged records of this job, which count as new) are `uncompleted` with origin "operational-loss";
and the job's OPERATIONAL alarms - the scheduler-exit, missing-runner-end and runner-exit alarms, the missing-status and
worker-exit alarms of its slots, and the no-finite-scheduler-memory alarm - are not raised but kept as informational lines
(summary `informational`, the receipt's top-level `informational` when any, printed as INFORMATIONAL). Every other alarm stands
(integrity: verifier code/environment, anchors, records, timings, statuses, identities, bindings, foreign evidence; and the
walltime-request and scheduler-memory-above-90 % alarms). An UNSETTLED terminal job is never dispositioned: its alarms stand
until the operator settles it. An operational-loss job never qualifies and is never a crash."""
import os, sys, json, glob, math, time, shutil, hashlib, argparse, subprocess, shlex, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
HOST, LOGIN = "chpc-scp", "lengau"
MANIFEST_PATH = None                                                   # set by main (REVISION 10: the partition check needs it)
BASE = os.path.join(HERE, "results", "row19_screen")
LIVE_DIR = os.path.join(BASE, "live")
RECEIPTS = os.path.join(BASE, "receipts")
WATCH_SCHEMA = "row19-screen-watch-1"
QUAL_SCHEMA = "row19-screen-qualification-1"
TERMINAL = ("F", "E", "X", "gone")
KIND = {"refit": "shard", "orig": "orig"}


def sh(cmd, timeout=900):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 255, "", str(e)

# The remote half of pull_tree: explicit phases, each reported on stderr; stdout carries ONLY the tar stream.
_PULL_REMOTE = r"""
cd -- "$1" || { echo "PHASE cd FAILED" >&2; exit 90; }
L=$(mktemp) || { echo "PHASE mktemp FAILED" >&2; exit 91; }
trap 'rm -f "$L"' EXIT
find . -type f > "$L" || { echo "PHASE find FAILED" >&2; exit 92; }
LC_ALL=C sort "$L" >&2 || { echo "PHASE sort FAILED" >&2; exit 93; }
echo "LISTING-END $(wc -l < "$L")" >&2
tar -cf - .
rc=$?
echo "TAR-RC $rc" >&2
exit $rc
"""
# Temporary files of the publishers that write into these trees: row19_ledger.write_atomic (<path>.tmp) and the
# link-publishers row19_shard.publish / row19_screen_orig (<path>.tmp.<pid>). Only these may vanish during a pull.
_TMP_NAME = re.compile(r"\.tmp(\.\d+)?$")


def pull_tree(remote, local, timeout=900):
    """REVISION 9: copy a remote directory tree in ONE ssh stream instead of scp -r's per-file round trips (~1.1 s per
    file over the tunnel on 10 Oct 2026: the 938-file refit root overran the 900 s pull). Same source, destination and
    one bounded deadline. The remote runs explicit phases (cd, a complete file listing written to a remote temp file,
    the sorted listing on stderr closed by 'LISTING-END <n>', then GNU tar, closed by 'TAR-RC <rc>'). Stderr goes to a
    task-owned local temp file, so a listing of any size cannot block the stream (no pipe-capacity deadlock). Accepted
    only when: the local extractor exits 0; every phase marker is present; LISTING-END equals the number of listed
    names; TAR-RC is 0, or 1 = GNU tar's 'file changed as we read it' (recorded); ssh's own exit equals TAR-RC; and every
    listed file exists locally except the publishers' temporary names (<path>.tmp, <path>.tmp.<pid>). On any failure or
    the deadline both children are terminated, then killed, and reaped before returning. Returns (0, note) or
    (255, reason); the caller keeps the old live snapshot on 255."""
    import tempfile
    t_end = time.time() + timeout
    errf = tempfile.TemporaryFile()
    cmd = "bash -c " + shlex.quote(_PULL_REMOTE) + " pull " + shlex.quote(remote)
    src = dst = None

    def reap(*ps):
        for p in ps:
            if p is not None and p.poll() is None:
                p.terminate()
        for p in ps:
            if p is None:
                continue
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
                try:
                    p.wait(timeout=10)
                except Exception:
                    pass

    try:
        src = subprocess.Popen(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", HOST, cmd],
                               stdout=subprocess.PIPE, stderr=errf)
        dst = subprocess.Popen(["tar", "-xf", "-", "-C", local], stdin=src.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        src.stdout.close()
        _, derr = dst.communicate(timeout=max(1.0, t_end - time.time()))
        src.wait(timeout=max(1.0, t_end - time.time()))
    except Exception as e:
        reap(src, dst)
        return 255, f"tar stream: {type(e).__name__}: {str(e)[:120]}"
    errf.seek(0); serr = errf.read().decode(errors="replace"); errf.close()
    lines = serr.splitlines()
    if dst.returncode != 0:
        return 255, f"local tar rc {dst.returncode}: {derr.decode(errors='replace').strip()[:160]}"
    phase = [l for l in lines if l.startswith("PHASE ")]
    if phase:
        return 255, f"remote {phase[0]} (ssh rc {src.returncode})"
    ends = [l for l in lines if l.startswith("LISTING-END ")]
    tars = [l for l in lines if l.startswith("TAR-RC ")]
    if len(ends) != 1 or len(tars) != 1:
        return 255, f"remote phases incomplete (LISTING-END x{len(ends)}, TAR-RC x{len(tars)}, ssh rc {src.returncode})"
    listed = [l[2:] for l in lines if l.startswith("./")]
    try:
        n_end, tar_rc = int(ends[0].split()[1]), int(tars[0].split()[1])
    except ValueError:
        return 255, "remote phase markers unparsable"
    if n_end != len(listed):
        return 255, f"listing incomplete: LISTING-END {n_end} vs {len(listed)} names received"
    if tar_rc not in (0, 1) or src.returncode != tar_rc:
        return 255, f"remote tar rc {tar_rc}, ssh rc {src.returncode}"
    missing = [p for p in listed if not _TMP_NAME.search(p) and not os.path.isfile(os.path.join(local, p))]
    if missing:
        return 255, f"{len(missing)} listed file(s) not extracted, e.g. {missing[:3]}"
    return 0, ("" if tar_rc == 0 else "GNU tar exit 1: a file changed while it was read (live tree)")



def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(open(p, "rb").read())


def finite_nonneg(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def controls():
    import programme_gate as _PG                                            # REVISION 4 (C3): the deployment is read only when adopted
    why = _PG.controls_authority_problem()
    if why:
        raise RuntimeError(f"the controls file cannot be trusted: {why}")
    return json.load(open(os.path.join(HERE, "row19_screen_controls.json")))


def verify_remote(man, role, manifest_rel):
    clone, tc = controls()["deployment"]["controller_clone"], man["shard"]["toolchain"]
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN,
                       f"cd {clone}/workspace_demo/t1_access && {tc}/t1py chpc/row19_screen_verify.py --manifest {manifest_rel} --role {role}"], timeout=3600)
    if rc != 0:
        return None, None, f"producer-runtime verify failed (rc {rc}): {err.strip()[-200:]}"
    lines = [l for l in out.splitlines() if l.startswith("{")]
    if len(lines) != 1:
        return None, None, "producer-runtime verify printed no single JSON document"
    doc = json.loads(lines[0])
    if doc.get("schema") != "row19-screen-verify-1" or doc.get("role") != role:
        return None, None, "producer-runtime verify has another schema or role"
    import row19_screen_admit as _SA                                       # REVISION 4 (C2): exact digests, explicit clean lineage
    why = _SA.controls_problem() or _SA.generation_problem(doc.get("generation"))
    if why:
        return None, None, f"the producer verifier: {why}"
    return doc, sha_bytes(lines[0].encode()), ""


def fresh_snapshot(man, role):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    live = os.path.join(LIVE_DIR, role); stage = os.path.join(BASE, f"stage_{role}_{stamp}")
    problems = []
    for name, remote in (("campaign", man["storage"]["campaign"]), ("root", man["storage"]["root"])):
        local = os.path.join(stage, name); os.makedirs(local, exist_ok=True)
        rc, err = pull_tree(remote, local, timeout=900)
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True); return False, problems
    fetch_job_outputs(man, role, stage)
    shutil.rmtree(live, ignore_errors=True); os.makedirs(LIVE_DIR, exist_ok=True); shutil.move(stage, live)
    return True, []


def fetch_job_outputs(man, role, stage):
    """REVISION 8: the PBS output of every job that could be closed-no-record (its staged ledger entry settled, no runner end),
    pulled into <stage>/jobs; each result (rc, ok, SHA-256) in jobs/_fetch.json. A failed retrieval is recorded, never fatal: it
    only means that job cannot be dispositioned in this observation."""
    jd = os.path.join(stage, "jobs"); os.makedirs(jd, exist_ok=True); res = {}
    try:
        led = json.load(open(os.path.join(stage, "campaign", "budget.json")))
    except Exception:
        led = {"entries": {}}
    for e in (led.get("entries") or {}).values():
        if e.get("kind") != KIND[role] or e.get("state") != "settled":
            continue
        no_end = not any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s"))
        held = role == "refit" and e.get("runner_exit") == 4 and not isinstance(e.get("runner_exit"), bool)   # REVISION 14
        if not (no_end or held):
            continue
        n = int(e["rep"])
        nf = ()                                                               # REVISION 18: the node evidence of a possible node failure
        if role == "refit" and no_end:
            import row19_screen_nodefail as _NF
            m = _NF.EXIT_RE.search(e.get("settle_note") or "") if isinstance(e.get("settle_note"), str) else None
            if m and int(m.group(1)) in _NF.KILL_EXITS:
                nf = ((f"{n}.nodefail", _NF.evidence_name(role, n)),)
        for key, name in ((str(n), f"row19_screen_{role}_{n}.out"),) + (((f"{n}.err", f"row19_screen_{role}_{n}.err"),) if held else ()) + nf:
            local = os.path.join(jd, name)
            rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{man['shard']['toolchain']}/jobs/{name}", local])
            ok = rc == 0 and os.path.isfile(local)
            if not ok and os.path.exists(local):
                os.remove(local)
            res[key] = dict(file=name, rc=rc, ok=ok, sha256=(sha_file(local) if ok else None), err=str(err).strip()[:160])
    json.dump(res, open(os.path.join(jd, "_fetch.json"), "w"), indent=1)
    return res


def prior_scheduler_memory(role, j, exit_, receipts_dir=None):
    """REVISION 13 (Codex RSC 7523370 (a); the bank's c38779c rule): what EVERY fresh production receipt of this role, alarmed or
    not, DIRECTLY observed about PBS id j at state F with exit `exit_` -> (worst, breach). worst = (largest directly observed
    mem_kb, its walltime request, evidence {kind, file, sha256}) or None: a qstat-observed summary's mem_kb, or a
    ledger-settlement summary's qstat_mem_kb (never its possibly carried mem_kb). breach = evidence of the newest receipt whose
    alarms record a scheduler-memory breach for that job, or None."""
    worst = breach = None
    for p in sorted(glob.glob(os.path.join(receipts_dir or RECEIPTS, f"watch_{role}_*.json")), reverse=True):
        try:
            r = json.load(open(p))
        except Exception:
            continue
        if r.get("schema") != WATCH_SCHEMA or r.get("role") != role or r.get("fresh") is not True or r.get("production") is not True \
                or not isinstance(r.get("alarms"), list):
            continue
        for k, sj in (r.get("jobs") or {}).items():
            if not (isinstance(sj, dict) and sj.get("job_id") == j and sj.get("state") == "F" and sj.get("exit") == exit_
                    and not isinstance(sj.get("exit"), bool)):
                continue
            ev = dict(file=os.path.basename(p), sha256=sha_file(p))
            if sj.get("observation", "qstat") == "qstat":
                direct = (sj.get("mem_kb"), sj.get("requested_walltime_s"), "prior-receipt-qstat")
            elif sj.get("observation") == "ledger-settlement":
                direct = (sj.get("qstat_mem_kb"), sj.get("qstat_walltime_req_s"), "prior-receipt-settled-qstat")
            else:
                direct = (None, None, None)
            if finite_nonneg(direct[0]) and (worst is None or direct[0] > worst[0]):
                worst = (direct[0], direct[1], dict(ev, kind=direct[2]))
            if breach is None and any(isinstance(a, str) and a.startswith(f"{role} job {k}: scheduler memory above 90 %") for a in r["alarms"]):
                breach = dict(ev, kind="prior-memory-alarm")
    return worst, breach


def settled_scheduler_qstat(ids, pbs_file=None):
    """REVISION 12: {job_id: {mem_kb, walltime_req_s}} the scheduler still reports at state F for SETTLED ids; only
    "Unknown Job Id <settled id>" failures are tolerated (bank status settled_memory_qstat, Codex RSC 5183208)."""
    if pbs_file:
        q = json.load(open(pbs_file))
        return {j: dict(mem_kb=q[j]["mem_kb"], walltime_req_s=q[j].get("walltime_req_s")) for j in ids
                if j in q and (q[j] or {}).get("state") == "F" and finite_nonneg((q[j] or {}).get("mem_kb"))}
    if not ids:
        return {}
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN, "qstat -xf " + " ".join(ids)], timeout=300)
    errs = [x.strip() for x in str(err or "").splitlines() if x.strip()]
    if rc != 0 and not (errs and all(re.fullmatch(r"qstat: Unknown Job Id (\S+)", x) and x.split()[-1] in ids for x in errs)):
        return {}
    got, cur = {}, None
    for line in out.splitlines():
        t = line.strip()
        if t.startswith("Job Id:"):
            cur = t.split(":", 1)[1].strip(); got.setdefault(cur, {})
        elif cur in ids and " = " in t:
            k, v = t.split(" = ", 1)
            if k == "resources_used.mem" and v.endswith("kb"):
                got[cur]["mem_kb"] = int(v[:-2])
            elif k == "Resource_List.walltime":
                got[cur]["walltime_req_s"] = hms_s(v)
            elif k == "job_state":
                got[cur]["state"] = v
    return {j: dict(mem_kb=g["mem_kb"], walltime_req_s=g.get("walltime_req_s")) for j, g in got.items()
            if j in ids and g.get("state") == "F" and finite_nonneg(g.get("mem_kb"))}


def settled_observation(role, e, receipts_dir=None):
    """REVISION 11: the observation of a SETTLED ledger entry (its settlement's qstat -xf, in settle_note), or None."""
    note = e.get("settle_note")
    m = re.search(r"Exit_status (-?\d+)\b", note) if isinstance(note, str) else None
    if not m or e.get("state") != "settled":
        return None
    return dict(state="F", exit=int(m.group(1)), source="ledger-settlement", settle_note_sha256=sha_bytes(note.encode()))


def pbs_observe(job_ids, pbs_file=None, settled=None, role=None, receipts_dir=None):
    """REVISION 11: `settled` = {job_id: ledger entry} of the SETTLED entries, observed from their settlement, never asked of qstat."""
    settled = settled or {}
    obs = {}
    for j in job_ids:
        if j in settled:
            o = settled_observation(role, settled[j], receipts_dir)
            if o is None:
                return None, f"settled job {j}: its settlement note carries no Exit_status (no observation)"
            obs[j] = o
    live = settled_scheduler_qstat([j for j in job_ids if j in settled], pbs_file)      # REVISION 12
    for j in [j for j in job_ids if j in settled]:                      # REVISION 13: largest DIRECT value; breaches kept
        o = obs[j]
        worst, breach = prior_scheduler_memory(role, j, o["exit"], receipts_dir)
        vals = ([(live[j]["mem_kb"], live[j].get("walltime_req_s"), dict(kind="qstat"))] if j in live else []) + ([worst] if worst else [])
        if j in live:
            o.update(qstat_mem_kb=live[j]["mem_kb"], qstat_walltime_req_s=live[j].get("walltime_req_s"))
        if vals:
            m, w, ev = max(vals, key=lambda x: x[0])
            o["mem_kb"] = m
            o["walltime_req_s"] = w if w is not None else next((x[1] for x in vals if x[1] is not None), None)
            if ev["kind"] != "qstat":
                o["prior_receipt"] = dict(file=ev["file"], sha256=ev["sha256"])
        o["memory_evidence"] = [v[2] for v in vals]
        o["memory_breach"] = breach
    ask = [j for j in job_ids if j not in settled]
    if pbs_file:
        q = json.load(open(pbs_file))
        obs.update({j: v for j, v in q.items() if j not in settled})
        return obs, ""
    if not ask:
        return obs, ""
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN, "qstat -xf " + " ".join(ask)], timeout=300)
    if rc != 0:
        return None, f"qstat failed (rc {rc}): {(err or out).strip()[:160]}"
    cur = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Job Id:"):
            cur = s.split(":", 1)[1].strip(); obs[cur] = {"state": None}
        elif cur and " = " in s:
            k, v = s.split(" = ", 1)
            if k == "job_state":
                obs[cur]["state"] = v
            elif k == "Exit_status":
                obs[cur]["exit"] = int(v)
            elif k == "resources_used.mem":
                obs[cur]["mem_kb"] = int(v[:-2]) if v.endswith("kb") else None
            elif k == "Resource_List.walltime":
                obs[cur]["walltime_req_s"] = hms_s(v)
    missing = [j for j in ask if j not in obs or not obs[j].get("state")]
    if missing:
        return None, f"qstat returned 0 but did not describe {missing}"
    return obs, ""


def hms_s(v):
    try:
        h, m, x = (int(p) for p in v.strip().split(":"))
        return float(h * 3600 + m * 60 + x)
    except Exception:
        return None


def _slot_map(root, m):
    p = os.path.join(root, "plans", f"job_{m}.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for sl in json.load(open(p)).get("slots", []):
        keys = [f"{int(sl['rep'])}/{int(i)}" for i in sl["indices"]] if "rep" in sl else [str(int(r)) for r in sl["reps"]]
        for k in keys:
            out[k] = int(sl["slot"])
    return out


def closed_no_record(man, role, n, e, plan, j, o, units, ledger, live):
    """REVISION 8: (disposition, '') when job n is a closed, settled, no-record job on THIS observation; (None, reason) otherwise."""
    import row19_screen_admit as _SA
    root = os.path.join(live, "root")
    if o.get("state") != "F" or not isinstance(o.get("exit"), int) or isinstance(o.get("exit"), bool):
        return None, "the scheduler observation is not state F with an observed exit"
    if e.get("state") != "settled" or not finite_nonneg(e.get("settled_core_h")) or not finite_nonneg(e.get("settled_at")) \
            or not (isinstance(e.get("settle_note"), str) and len(e["settle_note"].strip()) >= 8):
        return None, "the ledger entry is not SETTLED with settlement evidence (charge, note, time)"
    if any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s")):
        return None, "the ledger records a runner end"
    if not j or not e.get("token") or plan.get("token") != e.get("token") or plan.get("job") != n:
        return None, "the plan is not this entry's token and job"
    sc = _SA.status_scoped(root, j)
    if sc:
        return None, f"status evidence scoped to {j}: {sc[:3]}"
    named = sorted(k for k, v in units.items() if ((v or {}).get("timing") or {}).get("job") == j)
    if named:
        return None, f"unit(s) {named[:3]} carry timing naming {j}"
    ts = _SA.timing_scan(root, j)
    if ts:
        return None, f"timing evidence naming {j} or of unknown attribution: {ts[:3]}"
    num_of = {x.get("job_id"): int(x["rep"]) for x in ledger["entries"].values() if x.get("kind") == KIND[role] and x.get("job_id")}
    maps = {}

    def pso(m):
        if m not in maps:
            maps[m] = _slot_map(root, m)
        return maps[m]
    keys = sorted(_slot_map(root, n))
    for k in keys:
        files, odd = _SA.coordinate_files(man, root, role, k)
        if odd:
            return None, f"coordinate {k}: temporary or non-canonical output files {[os.path.basename(p) for p in odd][:3]}"
        if files or (units.get(k) or {}).get("record") is not None:
            why = _SA.later_completion(man, root, role, units, k, n, num_of, pso)
            if why:
                return None, f"coordinate {k} holds output that is not a later bound job's planned completion ({why})"
    name = f"row19_screen_{role}_{n}.out"; p = os.path.join(live, "jobs", name)
    try:
        f = json.load(open(os.path.join(live, "jobs", "_fetch.json"))).get(str(n)) or {}
    except Exception:
        f = {}
    if not f.get("ok") or f.get("file") != name or not os.path.isfile(p):
        return None, "its PBS output was not retrieved in this observation (absence of an admission failure is not proven)"
    try:
        b = open(p, "rb").read()
    except OSError:
        return None, "its retrieved PBS output is unreadable"
    if sha_bytes(b) != f.get("sha256"):
        return None, "its retrieved PBS output changed after retrieval"
    txt = b.decode("utf-8", errors="replace")
    if "ADMISSION FAILED" in txt:
        return None, "its PBS output reports ADMISSION FAILED"
    if f"job {j}" not in txt:
        return None, f"its PBS output does not name {j}"
    pp = os.path.join(root, "plans", f"job_{n}.json")
    return dict(kind=_SA.DISPO_KIND, scheduler_state="F", scheduler_exit=o["exit"], settled_core_h=e["settled_core_h"],
                settle_note=e["settle_note"], settled_at=e["settled_at"], token=e["token"], job_id=j, plan_sha256=sha_file(pp),
                output_file=name, output_sha256=sha_bytes(b), status_files=0, attributed_units=0, uncompleted=len(keys),
                note="a charged failed attempt: no completion, no restart or recovery credit; its coordinates return to the planner"), ""


def fetched(live, key, name):
    """REVISION 14: (bytes, '') of a PBS file this observation retrieved and recorded unchanged, or (None, reason)."""
    try:
        f = json.load(open(os.path.join(live, "jobs", "_fetch.json"))).get(key) or {}
    except Exception:
        f = {}
    p = os.path.join(live, "jobs", name)
    if not f.get("ok") or f.get("file") != name or not os.path.isfile(p):
        return None, f"{name} was not retrieved in this observation"
    b = open(p, "rb").read()
    if sha_bytes(b) != f.get("sha256"):
        return None, f"{name} changed after retrieval"
    return b, ""


def crashed_slots(man, role, n, e, plan, j, o, units, ledger, live):
    """REVISION 14: (slot disposition, '') or (None, reason), from row19_screen_admit.crashed_slot_evidence on THIS snapshot."""
    import row19_screen_admit as _SA
    ob, why = fetched(live, str(n), f"row19_screen_{role}_{n}.out")
    eb, why2 = fetched(live, f"{n}.err", f"row19_screen_{role}_{n}.err")
    if why or why2:
        return None, why or why2
    root = os.path.join(live, "root")
    return _SA.crashed_slot_evidence(man, role, n, e, plan, j, o, ob, eb, units, list(ledger["entries"].values()),
                                     root=root, slot_map=lambda m: _slot_map(root, m))


def node_failure(man, role, n, e, plan, j, o, units, ledger, live):
    """REVISION 18: (node disposition, '') or (None, reason), from row19_screen_nodefail.node_failure_evidence on THIS snapshot."""
    import row19_screen_nodefail as _NF
    if role != "refit":
        return None, "only refit jobs carry node-failure dispositions"
    if o.get("state") != "F" or o.get("exit") not in _NF.KILL_EXITS or isinstance(o.get("exit"), bool):
        return None, f"the scheduler observation is not state F with an exit in the node-failure kill set {list(_NF.KILL_EXITS)}"
    vb, why = fetched(live, f"{n}.nodefail", _NF.evidence_name(role, n))
    if why:
        return None, why
    root = os.path.join(live, "root")
    return _NF.node_failure_evidence(man, role, n, e, plan, j, o, vb, units, list(ledger["entries"].values()),
                                     root=root, slot_map=lambda m: _slot_map(root, m), pin=_NF.capture_pin())


def operational_loss(man, role, n, e, plan, j, o, units, ledger, live):
    """REVISION 19: (operational-loss disposition, '') or (None, reason), from row19_screen_admit.operational_loss_evidence on
    THIS snapshot (no evidence file)."""
    import row19_screen_admit as _SA
    root = os.path.join(live, "root")
    return _SA.operational_loss_evidence(man, role, n, e, plan, j, o, units, list(ledger["entries"].values()),
                                         root=root, slot_map=lambda m: _slot_map(root, m))


def anchor_alarms(verify):
    an = verify.get("anchors") or {}
    if an.get("problem"):
        return [f"anchors: {an['problem']}"]
    al = []
    reps = an.get("reps") or {}
    if sorted(reps) != ["0", "1", "2"]:
        al.append(f"anchors: the verdict covers {sorted(reps)}, not all three development anchors")
    for r, e in reps.items():
        if e.get("problem"):
            al.append(f"anchor {r}: {e['problem']}")
        if e.get("missing"):
            al.append(f"anchor {r}: required overlap {e['missing']} not present in both the shard root and the sequential chain")
        if e.get("invalid"):
            al.append(f"anchor {r}: {len(e['invalid'])} invalid record(s), e.g. {e['invalid'][0]}")
        if e.get("differ"):
            al.append(f"anchor {r}: payload DIFFERS at {e['differ']}")
        if e.get("conflict"):
            al.append(f"anchor {r}: conflicting duplicate sequential records at {e['conflict']}")
        if 0 not in (e.get("equal") or []):
            al.append(f"anchor {r}: index 0 is not observed equal")
        if not e.get("equal"):
            al.append(f"anchor {r}: no overlap observed equal")
    return al


def ec2_reconcile(man, role, units, root, assigned, alarms, now=None):
    """REVISION 10 r1 (Codex RSC 0483db4 V10-2/V10-4/V10-5/V10-8): EC2 production attempts are a second producer kind.
    Two sources, both on the root: the Mac claim authority's sealed inventory of EVERY attempt of every run
    (root/ec2/authority/inventory.json: intent, launched, ambiguous, rejected, reconciled; pending, ingested, dispositioned -
    failed and no-record attempts included) and the ingestion register (root/ec2/register.json). Alarms: an invalid or
    unsealed inventory; a stale one while any attempt is still live or owning; a register attempt the inventory does not
    carry with the same global sequence; an EC2-owned coordinate also in a Lengau plan; a coordinate claimed twice; an
    unknown register state; EC2 evidence while no partition is in force or outside it; for every published coordinate of an
    'ingested' attempt, a canonical record/timing/status whose bytes are not the register's or whose content is not a
    completed terminal status of exactly this attempt and slot. The receipt's `ec2` carries `bound` (ES.bound of the root,
    which every admission recomputes), the per-attempt states and USD (never mixed with core-hours). A Lengau root STOP while
    EC2 attempts are live is propagated to every live EC2 run (aws_ec2/prod_stop.propagate); a failure to do so alarms."""
    import row19_ec2_state as ES
    now = time.time() if now is None else now
    out = dict(bound=ES.bound(root), attempts={}, usd=dict(charged=0.0), problems=[])
    P = ES.paths(root)
    inv = None
    if os.path.exists(P["inventory"]):
        try:
            inv = json.load(open(P["inventory"]))
        except Exception as e:
            alarms.append(f"the EC2 authority inventory is unreadable ({e})")
        if inv is not None:
            why = ES.inventory_problem(inv, now, max_age=float("inf"))
            if why:
                alarms.append(f"EC2 authority inventory: {why}"); inv = None
    live_runs = set()
    if inv is not None:
        stale = now - inv["at"] > ES.INVENTORY_MAX_AGE_S
        for key, a in sorted(inv["attempts"].items()):
            live = a["state"] in ("intent", "launched", "ambiguous") or ES.owns(a)
            if live:
                live_runs.add(a["run"])
            if live and stale:
                alarms.append(f"EC2 attempt {key} is live/owning but the authority inventory is {now - inv['at']:.0f} s old")
            out["attempts"][key] = dict(state=a["state"], ingestion=a["ingestion"], cls=a["class"], sequence=a["sequence"],
                                        coordinates=len(a.get("coordinates", [])), charged_usd=a["charged_usd"])
            out["usd"]["charged"] += a["charged_usd"]
        for k in inv["owners"]:
            if k in assigned:
                alarms.append(f"EC2-owned coordinate {k} ({inv['owners'][k][0]}) is also in a Lengau plan")
        out["usd"].update(inventory_generation=inv["generation"], inventory_at=inv["at"])
    acts = [f for f in os.listdir(P["dir"]) if f.startswith("activation_e")] if os.path.isdir(P["dir"]) else []
    reg = None
    if os.path.exists(P["register"]):
        try:
            reg = json.load(open(P["register"]))
            if reg.get("schema") != ES.REGISTER_SCHEMA:
                alarms.append(f"the EC2 register schema {reg.get('schema')!r} is not {ES.REGISTER_SCHEMA}"); reg = None
        except Exception as e:
            alarms.append(f"the EC2 register is unreadable ({e})")
    part = None
    import row19_screen_admit as _SA
    try:
        pinned = bool(_SA.controls()["versions"][-1].get("partition"))
    except Exception:
        pinned = False
    if reg is not None or inv is not None or acts:
        try:
            part = _SA.partition(man, MANIFEST_PATH)
        except Exception as e:
            alarms.append(f"EC2 evidence present but the provider partition cannot be trusted ({e})")
        if part is None and reg is not None:
            alarms.append("EC2 evidence present but no provider partition is in force")
    # REVISION 11 (Codex 3dc0daf R1-2): an inventory is REQUIRED whenever a partition is pinned or any EC2 register or
    # activation exists; its absence (or an invalid one) alarms - only the genuinely empty null-partition root is clean
    if inv is None and (pinned or reg is not None or acts) and not any("authority inventory" in x for x in alarms):
        alarms.append("EC2 partition/register/activation present but no valid authority inventory is installed on the root")
    if os.path.exists(P["stop"]) and live_runs:
        try:
            sys.path.insert(0, os.path.join(HERE, "..", "aws_ec2"))
            import prod_stop as _PS
            done = _PS.propagate(sorted(live_runs), "Lengau screen root STOP seen by the status receipt")
            out["stop_propagated"] = done
        except Exception as e:
            alarms.append(f"the Lengau STOP could not be propagated to live EC2 runs {sorted(live_runs)} ({type(e).__name__}: {e})")
    if reg is None:
        return out
    import row19_partition as _RP
    try:                                                  # REVISION 11 (R1-1): each entry against ITS OWN epoch's block
        hist = _RP.historical_partitions(_SA.controls(), man, ES.sha_file(MANIFEST_PATH))
    except Exception as e:
        hist = {}; alarms.append(f"the historical provider partitions cannot be loaded ({type(e).__name__}: {e})")
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    idents = man["shard"]["identities"]
    owner = {}
    for aid, e in sorted((reg.get("attempts") or {}).items()):
        st = e.get("state"); coords = e.get("coordinates") or {}
        ia = (inv or {}).get("attempts", {}).get(e.get("key")) if inv is not None else None
        if inv is not None and (ia is None or ia.get("sequence") != e.get("sequence") or ia.get("attempt_id") != aid):
            alarms.append(f"EC2 attempt {aid}: not in the authority inventory with the register's key and sequence")
        out["attempts"].setdefault(e.get("key") or aid, {}).update(register_state=st, ingested_coordinates=len(coords),
                                                                    failed=sum(1 for c in coords.values() if c.get("failed")))
        if st == "dispositioned":                        # fenced at installation (R1-2): no coordinate may be published
            if coords:
                alarms.append(f"EC2 attempt {aid}: dispositioned but carries published coordinates")
            continue
        if st not in ("ingesting", "ingested"):
            alarms.append(f"EC2 attempt {aid}: unknown register state {st!r}"); continue
        epart = hist.get(e.get("partition_sha256"))
        if epart is None:
            alarms.append(f"EC2 attempt {aid}: its partition {str(e.get('partition_sha256'))[:12]} is not one any controls version pins")
        for key, ce in coords.items():
            if key in owner:
                alarms.append(f"EC2 unit {key}: claimed by attempts {owner[key]} and {aid}"); continue
            owner[key] = aid; assigned.add(key)
            r, i = (int(x) for x in key.split("/"))
            if epart is not None and not _RP.blocked(epart, r, i):
                alarms.append(f"EC2 unit {key} ({aid}): outside the block of its own partition epoch {epart['epoch']}")
            if st != "ingested" or ce.get("preexisting"):
                continue
            v = units.get(key) or {}
            if not (v.get("record") or {}).get("ok"):
                alarms.append(f"EC2 unit {key} ({aid}): no valid record"); continue
            if not (v.get("timing") or {}).get("ok"):
                alarms.append(f"EC2 unit {key} ({aid}): no valid timing"); continue
            if v["timing"].get("job") != aid or v["timing"].get("slot") != ce.get("slot"):
                alarms.append(f"EC2 unit {key}: timing names {v['timing'].get('job')} slot {v['timing'].get('slot')}, not {aid} slot {ce.get('slot')}")
            for what, fp, h in (("record", os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"), ce.get("record_sha256")),
                                ("timing", os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json"), ce.get("timing_sha256"))):
                if not os.path.exists(fp) or ES.sha_file(fp) != h:
                    alarms.append(f"EC2 unit {key} ({aid}): canonical {what} is not the register's bytes")
            sp = os.path.join(root, "ec2", "status", f"{aid}.slot{ce.get('slot')}.json")
            if not os.path.exists(sp):
                alarms.append(f"EC2 unit {key} ({aid}): no worker status copied"); continue
            if ES.sha_file(sp) != ce.get("status_sha256"):
                alarms.append(f"EC2 unit {key} ({aid}): copied status is not the register's bytes"); continue
            try:
                why = ES.status_problem(json.load(open(sp)), aid, ce.get("slot"), r, i, idents.get(str(r)), mem_stop)
            except Exception as ex:
                why = f"status unreadable ({ex})"
            if why:
                alarms.append(f"EC2 unit {key} ({aid}): {why}")
    return out


def reconcile(man, role, verify, obs, ledger, live):
    alarms, summary, jobs = [], {}, {}
    root = os.path.join(live, "root")
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    mem_req_kb = float(man["pbs"]["mem_gb"]) * 1024 ** 2
    units = verify.get("units", {}); assigned = set(); expected_status = set()
    for e in sorted((e for e in ledger["entries"].values() if e.get("kind") == KIND[role]), key=lambda e: int(e["rep"])):
        n = int(e["rep"]); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[str(n)] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
        if not os.path.exists(pp):
            alarms.append(f"{role} job {n}: no plan file"); continue
        plan = json.load(open(pp)); j = e.get("job_id")
        o = (obs or {}).get(j, {}) if j else {}
        state = o.get("state"); terminal = state in TERMINAL
        s_sum = dict(job_id=j, state=state, exit=o.get("exit"), runner_exit=e.get("runner_exit"), mem_kb=o.get("mem_kb"),
                     slots=len(plan["slots"]), ended=0, exits={}, new=0, resumed=0, left=0, max_worker_maxrss=None, max_wall_s=None,
                     failed_units=[], partition=dict(new=[], resumed=[], left=[]),
                     plan_walltime_s=plan.get("walltime_s"), requested_walltime_s=o.get("walltime_req_s"))
        if o.get("source") == "ledger-settlement":                          # REVISION 11: the observation's provenance
            s_sum.update(observation=o["source"], settle_note_sha256=o["settle_note_sha256"], prior_receipt=o.get("prior_receipt"),
                         memory_evidence=o.get("memory_evidence"), qstat_mem_kb=o.get("qstat_mem_kb"),
                         qstat_walltime_req_s=o.get("qstat_walltime_req_s"), memory_breach=o.get("memory_breach"))
            if o.get("memory_breach"):                                  # REVISION 13: a recorded breach is never displaced
                alarms.append(f"{role} job {n} ({j}): receipt {o['memory_breach']['file']} recorded a scheduler-memory alarm for this terminal job")
        dispo, dwhy = None, ""
        if e.get("runner_exit") is None and terminal:                       # every terminal job without a runner exit is examined
            dispo, dwhy = closed_no_record(man, role, n, e, plan, j, o, units, ledger, live)
        if dispo:
            s_sum["disposition"] = dispo
        elif dwhy:
            s_sum["disposition_held"] = dwhy
        sdispo, crashed = None, set()                                       # REVISION 14: crashed-worker slot disposition
        if role == "refit" and terminal and e.get("runner_exit") == 4 and not isinstance(e.get("runner_exit"), bool):
            sdispo, swhy = crashed_slots(man, role, n, e, plan, j, o, units, ledger, live)
            if sdispo:
                s_sum["slot_disposition"] = sdispo; crashed = {d["slot"] for d in sdispo["slots"]}
            else:
                s_sum["slot_disposition_held"] = swhy
        ndispo, nodeless = None, set()                                      # REVISION 18: node-failure disposition
        if role == "refit" and terminal and not dispo and e.get("runner_exit") is None:
            ndispo, nwhy = node_failure(man, role, n, e, plan, j, o, units, ledger, live)
            if ndispo:
                s_sum["node_disposition"] = ndispo; nodeless = set(ndispo["no_status_slots"])
            else:
                s_sum["node_disposition_held"] = nwhy
        odispo, ostat, info = None, set(), []                               # REVISION 19: operational-loss disposition (fallback)
        unclean = state != "F" or o.get("exit") not in (0, 75) or e.get("runner_exit") not in (0, 75) or isinstance(o.get("exit"), bool)
        if role == "refit" and terminal and unclean and not dispo and not sdispo and not ndispo:
            odispo, owhy = operational_loss(man, role, n, e, plan, j, o, units, ledger, live)
            if odispo:
                s_sum["operational_loss"] = odispo; ostat = set(odispo["no_status_slots"])
            else:
                s_sum["operational_loss_held"] = owhy

        def alarm(msg, operational=False):                                  # REVISION 19: an operational alarm of an
            (info if operational and odispo else alarms).append(msg)       # operational-loss job is an informational line
        if finite_nonneg(o.get("walltime_req_s")) and finite_nonneg(plan.get("walltime_s")) and abs(o["walltime_req_s"] - plan["walltime_s"]) > 1.0:
            alarms.append(f"{role} job {n} ({j}): the scheduler's walltime request {o['walltime_req_s']:.0f} s is not the plan's {plan['walltime_s']:.0f} s")
        started = state == "R" or terminal
        expected_status.update(f"job{j}.slot{sl['slot']}.json" for sl in plan["slots"])
        if not j:
            alarms.append(f"{role} job {n}: reserved but not bound to a PBS id")
        if o.get("mem_kb") is not None and o["mem_kb"] > 0.9 * mem_req_kb:
            alarms.append(f"{role} job {n}: scheduler memory above 90 % of the request")
        if terminal and not dispo and not sdispo and not ndispo and (state != "F" or o.get("exit") not in (0, 75)):
            alarm(f"{role} job {n} ({j}): terminal as state {state}, scheduler exit {o.get('exit')} (F with 0/75 required)", True)
        if terminal and not dispo and not ndispo and e.get("runner_exit") is None:
            alarm(f"{role} job {n} ({j}): terminal but no runner end in the ledger", True)
        if e.get("runner_exit") not in (None, 0, 75) and not sdispo:
            alarm(f"{role} job {n} ({j}): runner exit {e.get('runner_exit')}", True)
        if terminal and not finite_nonneg(o.get("mem_kb")):
            alarm(f"{role} job {n} ({j}): no finite observed scheduler memory", True)
        for sl in plan["slots"]:
            want = ([f"{int(sl['rep'])}/{int(i)}" for i in sl["indices"]] if role == "refit" else [str(int(r)) for r in sl["reps"]])
            assigned.update(want)
            stp = os.path.join(root, "status", f"job{j}.slot{sl['slot']}.json")
            try:
                st = json.load(open(stp)) if os.path.exists(stp) else None
            except Exception:
                alarms.append(f"{role} job {n} slot {sl['slot']}: the worker status is unreadable"); continue
            if st is None:
                if terminal and not dispo and int(sl["slot"]) not in crashed and int(sl["slot"]) not in nodeless:
                    alarm(f"{role} job {n} slot {sl['slot']}: no worker status after the job ended (read its log)", int(sl["slot"]) in ostat)
                continue
            s_sum["ended"] += 1; s_sum["exits"][str(st.get("exit"))] = s_sum["exits"].get(str(st.get("exit")), 0) + 1
            if st.get("job") != j or st.get("slot") != int(sl["slot"]):
                alarms.append(f"{role} job {n} slot {sl['slot']}: the status names job {st.get('job')} slot {st.get('slot')}")
            if finite_nonneg(st.get("maxrss")):
                s_sum["max_worker_maxrss"] = max(s_sum["max_worker_maxrss"] or 0, st["maxrss"])
            else:
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker memory is not finite")
            if finite_nonneg(st.get("wall_s")):
                s_sum["max_wall_s"] = max(s_sum["max_wall_s"] or 0, st["wall_s"])
            else:
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker wall time is not finite")
            if role == "refit":
                if st.get("rep") != int(sl["rep"]) or st.get("indices") != [int(i) for i in sl["indices"]]:
                    alarms.append(f"{role} job {n} slot {sl['slot']}: status assignment is not the plan's")
                if st.get("ident") != man["datasets"]["identities"].get(str(int(sl["rep"]))):
                    alarms.append(f"{role} job {n} slot {sl['slot']}: the status names another identity than the declared one")
                key = lambda i: f"{int(sl['rep'])}/{int(i)}"
            else:
                if st.get("reps") != [int(r) for r in sl["reps"]]:
                    alarms.append(f"{role} job {n} slot {sl['slot']}: status assignment is not the plan's")
                key = lambda r: str(int(r))
            new, res, left = [key(x) for x in st.get("new", [])], [key(x) for x in st.get("resumed", [])], [key(x) for x in st.get("left", [])]
            if set(new) & set(res) or set(new) & set(left) or set(res) & set(left) or sorted(new + res + left) != sorted(want):
                alarms.append(f"{role} job {n} slot {sl['slot']}: new/resumed/left are not a partition of its assignment")
            ex = st.get("exit")
            if ex == 0 and left:
                alarms.append(f"{role} job {n} slot {sl['slot']}: exit 0 with work left")
            elif ex == 75 and not left:
                alarms.append(f"{role} job {n} slot {sl['slot']}: exit 75 with nothing left")
            elif ex not in (0, 75):
                alarm(f"{role} job {n} slot {sl['slot']}: worker exit {ex} ({str(st.get('reason'))[:120]})", True)
            if mem_stop and finite_nonneg(st.get("maxrss")) and st["maxrss"] > mem_stop:
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker memory above the stop")
            s_sum["new"] += len(new); s_sum["resumed"] += len(res); s_sum["left"] += len(left)
            s_sum["partition"]["new"] += new; s_sum["partition"]["resumed"] += res; s_sum["partition"]["left"] += left
            s_sum["failed_units"] += [u for u in new + res if ((units.get(u) or {}).get("record") or {}).get("failed")]
            for u in new + res:
                v = units.get(u) or {}
                if not (v.get("record") or {}).get("ok"):
                    alarms.append(f"{role} unit {u}: no valid record in the producer runtime"); continue
                if not (v.get("timing") or {}).get("ok"):
                    alarms.append(f"{role} unit {u}: no valid timing"); continue
                if u in new and (v["timing"].get("job") != j or v["timing"].get("slot") != int(sl["slot"])):
                    alarms.append(f"{role} unit {u}: timing names another job or slot")
        if role == "refit" and started:
            bound_reps = set((verify.get("bindings") or {}).keys())
            missing = sorted({int(sl["rep"]) for sl in plan["slots"]} - {int(k) for k in bound_reps if k.isdigit()})
            if missing:
                alarms.append(f"{role} job {n}: started, but reps {missing[:5]} have no task binding")
        s_sum["partition"] = {x: sorted(v) for x, v in s_sum["partition"].items()}
        if dispo:
            s_sum["partition"].update(uncompleted=sorted(_slot_map(root, n)), uncompleted_origin="plan")
        elif sdispo:
            s_sum["partition"].update(uncompleted=list(sdispo["uncompleted"]), uncompleted_origin="crashed-slot")
        elif ndispo:                                                        # REVISION 18
            s_sum["partition"].update(uncompleted=list(ndispo["uncompleted"]), uncompleted_origin="node-failure")
        elif odispo:                                                        # REVISION 19: salvaged records count as this job's new
            s_sum["new"] += len(odispo["salvaged"]); s_sum["partition"]["new"] = sorted(s_sum["partition"]["new"] + list(odispo["salvaged"]))
            s_sum["partition"].update(uncompleted=list(odispo["uncompleted"]), uncompleted_origin="operational-loss")
        if info:
            s_sum["informational"] = info
        summary[str(n)] = s_sum
    ec2 = ec2_reconcile(man, role, units, root, assigned, alarms) if role == "refit" else {}
    for sp in glob.glob(os.path.join(root, "status", "*")):
        if os.path.basename(sp) not in expected_status:
            alarms.append(f"{role}: status {os.path.basename(sp)!r} that no planned job and slot assigns")
    for u, v in units.items():
        if u not in assigned:
            alarms.append(f"{role} unit {u}: evidence no plan assigns (foreign)")
        elif not (v.get("record") or {}).get("ok") and v.get("record") is not None:
            alarms.append(f"{role} unit {u}: invalid record ({(v.get('record') or {}).get('reason')})")
    for r, b in (verify.get("bindings") or {}).items():
        if not b.get("ok") or not b.get("declared_ident_equal"):
            alarms.append(f"task binding of rep {r}: {b.get('reason') or 'not the declared identity'}")
    return alarms, summary, jobs, ec2


def designated_report(man, verify, ledger, live, summary, manifest_path):
    """REVISION 16 CANDIDATE: (view, problem) - the raw designated-set view of THIS snapshot (row19_screen_admit.designated_view,
    the ONE implementation the admission dry run prints): progress over S x 0..79, Lengau's plannable count, the EC2-designated
    unclaimed coordinates that wait for the provider-epoch package, the crash history from THIS receipt's slot dispositions and
    the rescue-pending list. Informational: it changes no alarm except a declaration the lineage does not pin or that does not
    recompute (that would hold every admission too)."""
    import row19_screen_admit as _SA, row19_partition as _RP
    doc, why = _SA.designated(man, manifest_path)
    if why:
        return None, why
    root = os.path.join(live, "root")
    done = set()
    for u, v in (verify.get("units") or {}).items():
        if (v.get("record") or {}).get("ok"):
            r, i = u.split("/"); done.add((int(r), int(i)))
    flight, claimed, probs = set(), set(), []
    for e in ledger["entries"].values():
        if e.get("kind") != "shard":
            continue
        pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
        if e.get("state") in _SA.LIVE and e.get("runner_exit") is None and os.path.exists(pp):
            flight |= _RP.plan_claims(pp, probs)
    for pp in glob.glob(os.path.join(root, "plans", "job_*.json")):
        claimed |= _RP.plan_claims(pp, probs)
    if probs:
        return None, f"the snapshot's plans are not establishable: {probs[:3]}"
    used = [int(e["rep"]) for e in ledger["entries"].values() if e.get("kind") == "shard"]
    env_of = lambda m: _SA.resolve_envelope(man, manifest_path, "refit", m)[0]
    history = _SA.crash_history(dict(jobs=summary), env_of)
    part = None
    try:
        part = _SA.partition(man, manifest_path)
    except Exception as e:
        return None, f"the provider partition cannot be trusted: {e}"
    return _SA.designated_view(doc, done, flight, claimed, history, env_of((max(used) + 1) if used else 1), part), ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--role", required=True, choices=("refit", "orig"))
    ap.add_argument("--no-pull", action="store_true"); ap.add_argument("--verify-file", default=None); ap.add_argument("--pbs-file", default=None)
    ap.add_argument("--publish-receipt", action="store_true"); ap.add_argument("--qualify", type=int, default=None)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); role = a.role; now = time.time()
    if man.get("role") != role:
        print(f"{a.manifest} is not the {role} manifest"); return 2
    live = os.path.join(LIVE_DIR, role); alarms = []; fresh = False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(man, role); alarms += probs
    if a.verify_file:
        verify = json.load(open(a.verify_file)); vsha = sha_file(a.verify_file); vprob = ""
    else:
        verify, vsha, vprob = verify_remote(man, role, "chpc/" + os.path.basename(a.manifest))
    if vprob:
        alarms.append(vprob); verify = verify or {}
    if verify.get("environment_bad") or verify.get("code_bad"):
        alarms.append(f"producer runtime: environment {verify.get('environment_bad')} code {verify.get('code_bad')}")
    if verify.get("manifest_sha256") and verify["manifest_sha256"] != sha_file(a.manifest):
        alarms.append("the producer runtime's manifest is not this manifest")
    alarms += anchor_alarms(verify)
    led_p = os.path.join(live, "campaign", "budget.json")
    ledger = json.load(open(led_p)) if os.path.exists(led_p) else {"entries": {}}
    ids = [e["job_id"] for e in ledger["entries"].values() if e.get("kind") == KIND[role] and e.get("job_id")]
    settled = {e["job_id"]: e for e in ledger["entries"].values() if e.get("kind") == KIND[role] and e.get("job_id") and e.get("state") == "settled"}
    obs, oprob = pbs_observe(ids, a.pbs_file, settled, role)
    if oprob:
        alarms.append(oprob)
    global MANIFEST_PATH
    MANIFEST_PATH = a.manifest
    al, summary, jobs, ec2 = reconcile(man, role, verify, obs, ledger, live)
    alarms += al
    desig = None
    if role == "refit":                                                     # REVISION 16: the designated view (raw, informational)
        desig, dwhy = designated_report(man, verify, ledger, live, summary, a.manifest)
        if dwhy:
            alarms.append(f"designated set: {dwhy}")
    production = fresh and not (a.no_pull or a.verify_file or a.pbs_file)
    nvalid = sum(1 for v in (verify.get("units") or {}).values() if (v.get("record") or {}).get("ok"))
    print(f"ROW 19 SCREEN ({role}), live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  evidence: "
          f"{'FRESH snapshot' if fresh else 'NOT FRESH'}{'' if production else ' (not production)'}; valid units {nvalid}; verify {str(vsha)[:12]}")
    for n, s in summary.items():
        print(f"  {role} job {n} {s['job_id']} PBS {s['state']} exit {s['exit']}: workers ended {s['ended']}/{s['slots']} exits {s['exits']}, "
              f"new {s['new']} resumed {s['resumed']} left {s['left']}")
        if s.get("disposition"):
            d = s["disposition"]
            print(f"    DISPOSITIONED (closed-no-record): scheduler exit {d['scheduler_exit']} kept, no worker status, no record; settled "
                  f"{d['settled_core_h']:.2f} core-h charged; {d['uncompleted']} planned coordinate(s) uncompleted (plan-derived); "
                  f"PBS output {d['output_file']} {d['output_sha256'][:12]}")
        elif s.get("disposition_held"):
            print(f"    not dispositioned: {s['disposition_held']}")
        if s.get("slot_disposition"):
            d = s["slot_disposition"]
            for c in d["slots"]:
                print(f"    SLOT-DISPOSITIONED (crashed worker): slot {c['slot']} rep {c['rep']} indices {c['indices']} - {c['signal']}; "
                      f"no status, no record; coordinates uncompleted (crashed-slot)")
            print(f"    PBS output {d['output_sha256'][:12]} error {d['error_sha256'][:12]}; settled {d['settled_core_h']:.2f} core-h charged")
        elif s.get("slot_disposition_held"):
            print(f"    not slot-dispositioned: {s['slot_disposition_held']}")
        if s.get("node_disposition"):                                       # REVISION 18
            d = s["node_disposition"]
            print(f"    DISPOSITIONED (node-failure): scheduler exit {d['scheduler_exit']} kept, no runner end; node {d['node']} {d['node_state']} "
                  f"({d['node_comment']}) changed {d['node_change_minus_mtime_s']:+d} s from the job's end; completed slots {d['completed_slots']} "
                  f"kept ({len(d['completed'])} record(s)); {len(d['uncompleted'])} coordinate(s) of no-status slots uncompleted (node-failure, "
                  f"returned to the planner, not a crash); settled {d['settled_core_h']:.2f} core-h charged; evidence {d['evidence_file']} "
                  f"{d['evidence_sha256'][:12]}")
        elif s.get("node_disposition_held"):
            print(f"    not node-dispositioned: {s['node_disposition_held']}")
        if s.get("operational_loss"):                                       # REVISION 19
            d = s["operational_loss"]
            print(f"    DISPOSITIONED (operational-loss): scheduler exit {d['scheduler_exit']} runner exit {d['runner_exit']} kept; completed slots "
                  f"{len(d['completed_slots'])}, crashed {[c['slot'] for c in d['crashed_slots']]}, no status {d['no_status_slots']}; salvaged "
                  f"{len(d['salvaged'])} record(s); {len(d['uncompleted'])} coordinate(s) uncompleted (operational-loss, returned to the planner, "
                  f"not a crash); settled {d['settled_core_h']:.2f} core-h charged")
            for x in s.get("informational") or []:
                print(f"      informational: {x}")
        elif s.get("operational_loss_held"):
            print(f"    not operational-loss: {s['operational_loss_held']}")
    if desig:
        print(f"  DESIGNATED S x 0..79 ({str(desig['declaration_sha256'])[:12]}): {desig['designated']} coordinates, done {desig['done']}, in flight "
              f"{desig['in_flight']}, Lengau plannable {desig['lengau_plannable']}, EC2-designated unclaimed (wait for the EC2 epoch package) "
              f"{desig['ec2_waiting_unclaimed']}; history outside the set kept: done {desig['outside_set_history']['done']}, in flight "
              f"{desig['outside_set_history']['in_flight']}")
        for x in desig["rescue_pending"]:
            print(f"    RESCUE-PENDING {x['coordinate']}: {x['crashes']} same-envelope crash(es), jobs {x['jobs']} - no further ordinary attempt; rescue route disabled"
                  + ("; an earlier attempt is still running (untouched)" if x["attempt_running"] else ""))
        if desig["crash_excluded_outside_set"]:
            print(f"    crash-excluded outside the set (never planned anyway): {desig['crash_excluded_outside_set']}")
    for r, e in sorted(((verify.get("anchors") or {}).get("reps") or {}).items()):
        print(f"  anchor {r}: required {e.get('required')} compared {len(e.get('compared', []))} equal {len(e.get('equal', []))}")
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms, but NOT fresh evidence"))
    for x in alarms:
        print("   -", x)
    bindings = {os.path.basename(p)[5:-5]: sha_file(p) for p in sorted(glob.glob(os.path.join(live, "root", "task_*.json")))}
    produced = {k: (v or {}).get("sha256") for k, v in (verify.get("bindings") or {}).items()}
    if role == "refit" and produced != bindings:
        alarms.append("the producer's task-binding digests are not the local snapshot's (not one coherent observation; recollect)")
    bound = dict(manifest_sha256=sha_file(a.manifest), root=man["storage"]["root"], campaign=man["storage"]["campaign"],
                 code=dict(man["code"]["files"]), wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"), jobs=jobs,
                 bindings=bindings, anchors_sha256=sha_bytes(json.dumps(verify.get("anchors"), sort_keys=True).encode()), verify_sha256=vsha,
                 job_outputs={k: dict(file=v["disposition"]["output_file"], sha256=v["disposition"]["output_sha256"])
                              for k, v in summary.items() if v.get("disposition")},
                 slot_outputs={k: dict(out=dict(file=v["slot_disposition"]["output_file"], sha256=v["slot_disposition"]["output_sha256"]),
                                       err=dict(file=v["slot_disposition"]["error_file"], sha256=v["slot_disposition"]["error_sha256"]))
                               for k, v in summary.items() if v.get("slot_disposition")},
                 node_evidence={k: dict(file=v["node_disposition"]["evidence_file"], sha256=v["node_disposition"]["evidence_sha256"])
                                for k, v in summary.items() if v.get("node_disposition")})
    receipt = dict(schema=WATCH_SCHEMA, role=role, time=now, fresh=fresh, production=production, alarms=alarms, bound=bound, jobs=summary,
                   anchors=verify.get("anchors"), plan_slots={k: v["slots"] for k, v in summary.items()}, ec2=ec2)
    if desig is not None:
        receipt["designated"] = desig                                       # REVISION 16: informational; no consumer gates on it
    info_all = [x for k, v in sorted(summary.items(), key=lambda kv: int(kv[0])) for x in (v.get("informational") or [])]
    if info_all:
        receipt["informational"] = info_all                                 # REVISION 19: never alarms; no consumer gates on it
    os.makedirs(RECEIPTS, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
    vp = os.path.join(RECEIPTS, f"verify_{role}_{stamp}.json")
    json.dump(verify, open(vp, "w"), sort_keys=True)
    vsha_saved = sha_file(vp)
    for k, ob in bound["job_outputs"].items():                               # REVISION 8: retain the bound PBS output beside the receipt
        shutil.copy(os.path.join(live, "jobs", ob["file"]), os.path.join(RECEIPTS, f"{ob['file']}.{stamp}"))
    for k, so in bound["slot_outputs"].items():                              # REVISION 14: retain both bound files
        for ob in so.values():
            shutil.copy(os.path.join(live, "jobs", ob["file"]), os.path.join(RECEIPTS, f"{ob['file']}.{stamp}"))
    for k, ob in bound["node_evidence"].items():                             # REVISION 18: retain the bound node evidence
        shutil.copy(os.path.join(live, "jobs", ob["file"]), os.path.join(RECEIPTS, f"{ob['file']}.{stamp}"))
    if production:
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", vp, f"{HOST}:{man['storage']['root']}/gate/{os.path.basename(vp)}"])
        if rc != 0:
            alarms.append(f"the full verifier document could not be retained in the gate (rc {rc}); this is not production evidence")
            production = False; receipt.update(production=False, alarms=alarms)
    bound["verify_file"] = os.path.basename(vp); bound["verify_file_sha256"] = vsha_saved
    if a.publish_receipt or a.qualify is not None:
        rp = os.path.join(RECEIPTS, f"watch_{role}_{stamp}.json")
        json.dump(receipt, open(rp, "w"), indent=1, allow_nan=False)
        if production:
            rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", rp, f"{HOST}:{man['storage']['root']}/gate/{os.path.basename(rp)}"])
            print(f"  receipt {os.path.basename(rp)} " + ("copied to the gate" if rc == 0 else f"NOT copied (rc {rc})"))
    if a.qualify is not None:
        n = str(int(a.qualify)); why = []
        if not production:
            why.append("the evidence is not fresh production evidence")
        if alarms:
            why.append(f"{len(alarms)} alarm(s)")
        s = summary.get(n)
        if not s:
            why.append(f"no {role} job {n} in the ledger")
        else:
            if s["state"] != "F" or s["exit"] not in (0, 75) or s.get("runner_exit") not in (0, 75):
                why.append(f"job {n} is not state F with scheduler and runner exits 0 or 75")
            if not (finite_nonneg(s.get("mem_kb")) and finite_nonneg(s.get("max_worker_maxrss"))):
                why.append(f"job {n}: observed scheduler and worker memory are not finite")
            if s.get("disposition") is not None:
                why.append(f"job {n} is dispositioned (closed-no-record); a dispositioned job never qualifies")
            if s.get("slot_disposition") is not None:
                why.append(f"job {n} is slot-dispositioned (crashed worker); it never qualifies")
            if s.get("node_disposition") is not None:                       # REVISION 18
                why.append(f"job {n} is dispositioned (node-failure); a node-dispositioned job never qualifies")
            if s.get("operational_loss") is not None:                       # REVISION 19
                why.append(f"job {n} is dispositioned (operational-loss); it never qualifies")
            if s["ended"] != s["slots"] or s["exits"] != {"0": s["slots"]} or s["left"]:
                why.append(f"job {n}: not every planned worker completed its assignment ({s['exits']}, left {s['left']})")
        jn = jobs.get(n)
        if not jn or None in jn.values():
            why.append(f"job {n} has no PBS id, token or plan hash to bind")
        if role == "refit" and s:
            plan = json.load(open(os.path.join(live, "root", "plans", f"job_{n}.json")))
            unbound = [sl["rep"] for sl in plan["slots"] if str(sl["rep"]) not in bindings]
            if unbound:
                why.append(f"job {n}'s reps {unbound[:5]} have no task binding")
        if why:
            print(f"\n  NOT QUALIFIED ({role} job {n}):"); [print("   -", w) for w in why]; return 1
        qp = os.path.join(RECEIPTS, f"qualified_{role}_job{n}.json")
        p1 = json.load(open(os.path.join(live, "root", "plans", f"job_{n}.json")))
        reps1 = {str(sl["rep"]) for sl in p1["slots"]} if role == "refit" else set()
        qbound = dict(bound, jobs={n: jobs[n]}, bindings={k: v for k, v in bindings.items() if k in reps1})
        json.dump(dict(schema=QUAL_SCHEMA, role=role, qualified_job=int(n), by="R052", time=now, production=True, bound=qbound, receipt=receipt,
                       anchors=verify.get("anchors"), verify_file=os.path.basename(vp)),
                  open(qp, "w"), indent=1, allow_nan=False)
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", qp, f"{HOST}:{man['storage']['root']}/gate/qualified_{role}_job{n}.json"])
        print(f"\n  QUALIFIED: {role} job {n} ({sha_file(qp)[:16]}) " + ("copied to the gate" if rc == 0 else f"NOT copied (rc {rc})"))
        return 0 if rc == 0 else 1
    return 1 if (alarms or not fresh) else 0


if __name__ == "__main__":
    sys.exit(main())
