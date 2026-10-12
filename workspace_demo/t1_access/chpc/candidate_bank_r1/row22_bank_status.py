"""Ledger row 22: the bank's live view, watch receipt and pilot qualification (Mac). Codex RSC 97fc278 conditions 3-4: fresh
coherent snapshots and successful scheduler observations; every planned rep and slot reconciled with disjoint new / resumed /
left lists, exact status, record and timing provenance, finite non-negative measurements, scheduler state, exit and
accounting; any HELD or missing worker, invalid or foreign record, missing or invalid timing, memory breach, failed admission
or absent accounting is an ALARM that holds progression.

EVIDENCE, every call:
  1. the producer-runtime verdict: `t1py chpc/row22_bank_verify.py` run in the bank clone on the login node; its stdout (one
     JSON document) is kept and its SHA-256 bound into the receipt. Records are validated THERE, against the production task
     identities; the Mac never recomputes an identity.
  2. a fresh pull of the bank root and campaign into a new staging directory, rotated in only when EVERY pull succeeded.
  3. one `qstat -xf` of every bank job id in the ledger that is NOT settled: the call must RETURN 0 (a non-zero return is a
     failed observation whatever its stdout - the defect Codex found in the shard parser) and must describe every id.
     REVISION (R052 11 Oct, PBS history expiry): a SETTLED entry is not asked of the scheduler - PBS drops finished jobs
     from its history after a few days and `qstat -xf` then fails "Unknown Job Id" for the whole call. Its observation is
     the settlement's own (`settle_note`, written by xf_settle from `qstat -xf` at settlement): state F and the exit and
     walltime the note records, with source "ledger-settlement" and the note's SHA-256 in the receipt. A settled entry
     whose note carries no `Exit_status <n>` is a failed observation (alarm). An unsettled job qstat cannot describe stays
     a failed observation (fail-closed). A ledger-sourced observation never qualifies a job (--qualify needs the scheduler).
     MEMORY of a settled job (Codex RSC 5bab1a9 (a), c38779c, 5183208: the aggregate >90 % alarm survives settlement).
     Evidence is read from (i) one separate `qstat -xf` of the settled ids, whose only tolerated failure is "Unknown Job Id"
     of those ids, and (ii) EVERY fresh production bank receipt, alarmed or not, that recorded the same PBS id at state F
     with the same exit (receipts record mem_kb and memory_evidence). The checked mem_kb is the LARGEST of the qstat value
     and the recorded values, checked against 90 % as before; a receipt's scheduler-memory alarm for that job is kept as an
     ALARM (memory_breach) whatever else holds. Only with no value does a breach or, failing that, the newest alarm-free
     direct-qstat receipt become the evidence - the latter a LIMITED historical attestation (`prior-clean-receipt-check`,
     file + SHA-256): the old check was conditional (no kb value -> no check), so it is neither a measured value nor proof
     of memory <= 90 %. No evidence at all is an ALARM; absence is never a memory pass.
RECONCILIATION per bank job (plan file, ledger entry, scheduler, statuses, verify verdict):
  - a terminal job (scheduler F/E/X/gone) must have a status for EVERY planned slot; a status's reps equal its plan slot's;
    new, resumed and left are disjoint and their union is the slot's reps; exit 0 iff left is empty, 75 with left non-empty,
    anything else (4 HELD, missing) is an alarm;
  - every new or resumed rep has a VALID record (verify) and a valid timing file; a new rep's timing names this job and slot;
  - worker maxrss below the per-worker stop; scheduler memory below 90 % of the request; a terminal job's scheduler exit 0
    or 75 and its runner end recorded in the ledger;
  - a running job: records published so far must be valid with timings; nothing else is required yet.
  - a record or timing for a rep no plan assigns is an alarm (foreign evidence).
RECEIPT (--publish-receipt): schema row22-bank-watch-1, fresh/production flags, alarms, bound = manifest SHA-256, root, campaign,
code pins, wrapper, bank binding SHA-256, the verify document's SHA-256, and every bank job (PBS id, token, plan SHA-256).
REVISION B1 CANDIDATE (R052 12 Oct, bank job 11 7531003 wall-killed at 36 h; NOT adopted): CLOSED-NO-RECORD DISPOSITION.
The fresh observation also retrieves the PBS output (<toolchain>/jobs/row22_bank_<n>.out) of every bank job whose ledger entry
is settled with no runner end, into jobs/ of the snapshot, each result (rc, ok, SHA-256) in jobs/_fetch.json; a failed retrieval
proves nothing and leaves the alarms. row22_bank_dispo.closed_no_record (ONE implementation, also used by the admission)
decides on THIS snapshot and the verify document. Only when it holds are that job's bad-scheduler-exit, missing-runner-end and
missing-worker-status alarms suppressed (memory alarms and every other check stand); the summary keeps the actual exit, zero
ended/new/resumed/left, carries `disposition` and `partition` (uncompleted = the plan's reps, origin "plan"); the receipt binds
the output in `bound.job_outputs`. Otherwise the reason is kept as `disposition_held` and the alarms stand. A dispositioned
job never qualifies.
QUALIFICATION (--qualify 1): only on fresh production evidence with zero alarms, job 1 terminal with scheduler exit 0, every
planned slot exit 0, every planned rep a valid record with timing, runner end in the ledger; written locally and copied to
<root>/gate/qualified_bank_job1.json. It is EVIDENCE for the reviewer; the submitter also needs the adopted review.

    python chpc/row22_bank_status.py --manifest chpc/row22_bank_manifest.json [--publish-receipt] [--qualify 1]
Exit 1 on any alarm or when the evidence is not fresh."""
import os, sys, json, glob, math, time, shutil, hashlib, argparse, subprocess, shlex, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import row22_bank_dispo as DP
HOST, LOGIN = "chpc-scp", "lengau"
LIVE_DIR = os.path.join(HERE, "results", "row22_bank", "live")
RECEIPTS = os.path.join(HERE, "results", "row22_bank", "receipts")
WATCH_SCHEMA = "row22-bank-watch-1"
QUAL_SCHEMA = "row22-bank-qualification-1"
TERMINAL = ("F", "E", "X", "gone")


def sh(cmd, timeout=600):
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


def verify_remote(man, manifest_rel):
    clone = man["bank"]["clone"]; tc = man["bank"]["toolchain"]
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN,
                       f"cd {clone}/workspace_demo/t1_access && {tc}/t1py chpc/row22_bank_verify.py --manifest {manifest_rel}"], timeout=1800)
    if rc != 0:
        return None, None, f"producer-runtime verify failed (rc {rc}): {err.strip()[-200:]}"
    line = [l for l in out.splitlines() if l.startswith("{")]
    if len(line) != 1:
        return None, None, "producer-runtime verify printed no single JSON document"
    try:
        doc = json.loads(line[0])
    except Exception as e:
        return None, None, f"producer-runtime verify output is not JSON ({e})"
    if doc.get("schema") != "row22-bank-verify-1":
        return None, None, "producer-runtime verify has another schema"
    return doc, sha_bytes(line[0].encode()), ""


def fresh_snapshot(man):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage = os.path.join(os.path.dirname(LIVE_DIR), f"stage_{stamp}")
    problems = []
    for name, remote in (("campaign", man["storage"]["campaign"]), ("root", man["storage"]["root"])):
        local = os.path.join(stage, name); os.makedirs(local, exist_ok=True)
        rc, err = pull_tree(remote, local, timeout=900)
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True); return False, problems
    fetch_job_outputs(man, stage)
    shutil.rmtree(LIVE_DIR, ignore_errors=True); os.makedirs(os.path.dirname(LIVE_DIR), exist_ok=True); shutil.move(stage, LIVE_DIR)
    return True, []


def fetch_job_outputs(man, stage):
    """REVISION B1: the PBS output of every bank job that could be closed-no-record (its staged ledger entry settled, no runner
    end), pulled into <stage>/jobs; each result (rc, ok, SHA-256) in jobs/_fetch.json. A failed retrieval is recorded, never
    fatal: it only means that job cannot be dispositioned in this observation."""
    jd = os.path.join(stage, "jobs"); os.makedirs(jd, exist_ok=True); res = {}
    try:
        led = json.load(open(os.path.join(stage, "campaign", "budget.json")))
    except Exception:
        led = {"entries": {}}
    for e in (led.get("entries") or {}).values():
        if e.get("kind") != "bank" or e.get("state") != "settled" or any(e.get(f) is not None for f in DP.RUNNER_END):
            continue
        n = int(e["rep"]); name = f"row22_bank_{n}.out"; local = os.path.join(jd, name)
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{man['bank']['toolchain']}/jobs/{name}", local])
        ok = rc == 0 and os.path.isfile(local)
        if not ok and os.path.exists(local):
            os.remove(local)
        res[str(n)] = dict(file=name, rc=rc, ok=ok, sha256=(sha_file(local) if ok else None), err=str(err).strip()[:160])
    json.dump(res, open(os.path.join(jd, "_fetch.json"), "w"), indent=1)
    return res


def fetched_output(live, n):
    """(name, bytes) of bank job n's PBS output as this observation retrieved and recorded it unchanged; bytes None otherwise."""
    name = f"row22_bank_{int(n)}.out"; p = os.path.join(live, "jobs", name)
    try:
        f = json.load(open(os.path.join(live, "jobs", "_fetch.json"))).get(str(int(n))) or {}
    except Exception:
        f = {}
    if not f.get("ok") or f.get("file") != name or not os.path.isfile(p):
        return name, None
    b = open(p, "rb").read()
    return name, (b if sha_bytes(b) == f.get("sha256") else None)


def settled_observation(e):
    """The observation a SETTLED ledger entry carries (its settlement's qstat -xf, in settle_note), or None."""
    note = e.get("settle_note")
    m = re.search(r"Exit_status (-?\d+)\b", note) if isinstance(note, str) else None
    if not m or e.get("state") != "settled":
        return None
    w = re.search(r"resources_used\.walltime (\d+:\d\d:\d\d)\b", note)
    return dict(state="F", exit=int(m.group(1)), walltime=(w.group(1) if w else None), source="ledger-settlement",
                settle_note_sha256=sha_bytes(note.encode()), settled_at=e.get("settled_at"))


def settled_memory_qstat(ids, pbs_file=None):
    """{job_id: mem_kb} the scheduler still reports for SETTLED ids; only "Unknown Job Id <settled id>" failures are tolerated."""
    if pbs_file:
        q = json.load(open(pbs_file))
        return {j: q[j]["mem_kb"] for j in ids if j in q and finite_nonneg((q[j] or {}).get("mem_kb"))}
    if not ids:
        return {}
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN, "qstat -xf " + " ".join(ids)], timeout=300)
    errs = [x.strip() for x in str(err or "").splitlines() if x.strip()]
    if rc != 0 and not (errs and all(re.fullmatch(r"qstat: Unknown Job Id (\S+)", x) and x.split()[-1] in ids for x in errs)):
        return {}
    mem, cur, st = {}, None, {}
    for line in out.splitlines():
        t = line.strip()
        if t.startswith("Job Id:"):
            cur = t.split(":", 1)[1].strip()
        elif cur in ids and " = " in t:
            k, v = t.split(" = ", 1)
            if k == "resources_used.mem" and v.endswith("kb"):
                mem[cur] = int(v[:-2])
            elif k == "job_state":
                st[cur] = v
    return {j: m for j, m in mem.items() if st.get(j) == "F"}


def prior_bank_memory(j, exit_, receipts_dir=None):
    """Codex RSC c38779c: what EVERY fresh, production bank receipt (alarmed or not) recorded about PBS id j at state F with
    exit_ -> (worst, breach, clean): worst = (largest recorded mem_kb, evidence) or None; breach = evidence of the newest
    receipt carrying a scheduler-memory alarm for that job, or None; clean = evidence of the newest alarm-free receipt that
    observed it from qstat (the limited historical attestation), or None. Breach evidence is consulted before any fallback."""
    worst = breach = clean = None
    for p in sorted(glob.glob(os.path.join(receipts_dir or RECEIPTS, "bank_watch_*.json")), reverse=True):
        try:
            r = json.load(open(p))
        except Exception:
            continue
        if r.get("schema") != WATCH_SCHEMA or r.get("fresh") is not True or r.get("production") is not True \
                or not isinstance(r.get("alarms"), list):
            continue
        for k, sj in (r.get("jobs") or {}).items():
            if not (isinstance(sj, dict) and sj.get("job_id") == j and sj.get("state") == "F" and sj.get("exit") == exit_
                    and not isinstance(sj.get("exit"), bool)):
                continue
            ev = dict(file=os.path.basename(p), sha256=sha_file(p))
            if finite_nonneg(sj.get("mem_kb")) and (worst is None or sj["mem_kb"] > worst[0]):
                worst = (sj["mem_kb"], dict(ev, kind="prior-receipt-value"))
            if breach is None and any(isinstance(a, str) and a.startswith(f"bank job {k}: scheduler memory") for a in r["alarms"]):
                breach = dict(ev, kind="prior-memory-alarm")
            if clean is None and r["alarms"] == [] and sj.get("observation", "qstat") == "qstat":
                clean = dict(ev, kind="prior-clean-receipt-check")
    return worst, breach, clean


def pbs_observe(job_ids, pbs_file=None, settled=None, receipts_dir=None):
    """({job_id: {state, exit, mem_kb, walltime, source}}, problem). A non-zero return of qstat is a FAILED observation.
    `settled` = {job_id: ledger entry} of the SETTLED entries: observed from their settlement, never asked of qstat."""
    settled = settled or {}
    obs = {}
    for j in job_ids:
        if j in settled:
            o = settled_observation(settled[j])
            if o is None:
                return None, f"settled job {j}: its settlement note carries no Exit_status (no observation)"
            obs[j] = o
    sq = settled_memory_qstat([j for j in job_ids if j in settled], pbs_file)
    for j in [j for j in job_ids if j in settled]:
        worst, breach, clean = prior_bank_memory(j, obs[j]["exit"], receipts_dir)
        vals = ([(sq[j], dict(kind="qstat"))] if j in sq else []) + ([worst] if worst else [])
        if vals:                                                            # the largest known value is the one checked
            m, ev = max(vals, key=lambda x: x[0])
            obs[j].update(mem_kb=m, memory_evidence=ev)
        else:
            obs[j].update(mem_kb=None, memory_evidence=breach or clean)
        obs[j]["memory_breach"] = breach
    ask = [j for j in job_ids if j not in settled]
    if pbs_file:
        q = json.load(open(pbs_file))
        obs.update({j: dict(v, source="qstat") for j, v in q.items() if j not in settled})
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
            cur = s.split(":", 1)[1].strip(); obs[cur] = {"state": None, "source": "qstat"}
        elif cur and " = " in s:
            k, v = s.split(" = ", 1)
            if k == "job_state":
                obs[cur]["state"] = v
            elif k == "Exit_status":
                obs[cur]["exit"] = int(v)
            elif k == "resources_used.mem":
                obs[cur]["mem_kb"] = int(v[:-2]) if v.endswith("kb") else None
            elif k == "resources_used.walltime":
                obs[cur]["walltime"] = v
    missing = [j for j in ask if j not in obs or not obs[j].get("state")]
    if missing:
        return None, f"qstat returned 0 but did not describe {missing}"
    return obs, ""


def reconcile(man, verify, obs, ledger, live=None):
    """(alarms, notes, per-job summaries, the bound job map, the bound PBS outputs of dispositioned jobs)."""
    alarms, notes, summary, jobs, outputs = [], [], {}, {}, {}
    live = live or LIVE_DIR
    root = live + "/root"
    entries = list(ledger["entries"].values())
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    mem_req_kb = float(man["pbs"]["mem_gb"]) * 1024 ** 2
    vreps = verify.get("reps", {})
    planned = {}
    for e in sorted((e for e in ledger["entries"].values() if e.get("kind") == "bank"), key=lambda e: int(e["rep"])):
        n = int(e["rep"]); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[str(n)] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
        if not os.path.exists(pp):
            alarms.append(f"bank job {n}: no plan file"); continue
        plan = json.load(open(pp)); j = e.get("job_id")
        o = (obs or {}).get(j, {}) if j else {}
        state = o.get("state"); terminal = state in TERMINAL
        s_sum = dict(job_id=j, state=state, exit=o.get("exit"), slots=len(plan["slots"]), ended=0, exits={}, new=0, resumed=0, left=0,
                     observation=o.get("source"), settle_note_sha256=o.get("settle_note_sha256"), mem_kb=o.get("mem_kb"),
                     memory_evidence=o.get("memory_evidence"))
        dispo = None
        if terminal and j and (o.get("exit") not in (0, 75) or e.get("runner_exit") is None):      # REVISION B1
            oname, ob = fetched_output(live, n)
            dispo, dwhy = DP.closed_no_record(root, n, e, plan, jobs[str(n)]["plan_sha256"], o, entries, oname, ob, vreps)
            if dispo:
                s_sum["disposition"] = dispo
                s_sum["partition"] = dict(new=[], resumed=[], left=[], uncompleted=dispo["uncompleted"], uncompleted_origin="plan")
                outputs[str(n)] = dict(file=dispo["output_file"], sha256=dispo["output_sha256"])
            else:
                s_sum["disposition_held"] = dwhy
        if o.get("memory_breach"):
            alarms.append(f"bank job {n} ({j}): receipt {o['memory_breach']['file']} recorded a scheduler-memory alarm for this terminal job")
        if o.get("source") == "ledger-settlement" and not o.get("memory_evidence"):
            alarms.append(f"bank job {n} ({j}): settled, but no scheduler memory evidence (qstat, a recorded value or a clean receipt's check)")
        if not j:
            alarms.append(f"bank job {n}: reserved but not bound to a PBS id")
        if j and o.get("mem_kb") is not None and o["mem_kb"] > 0.9 * mem_req_kb:
            alarms.append(f"bank job {n}: scheduler memory {o['mem_kb']/1024**2:.1f} GiB above 90 % of the request")
        if terminal and o.get("exit") not in (0, 75) and not dispo:
            alarms.append(f"bank job {n} ({j}): scheduler state {state}, exit {o.get('exit')}")
        if terminal and e.get("runner_exit") is None and not dispo:
            alarms.append(f"bank job {n} ({j}): terminal in the scheduler but no runner end in the ledger")
        for sl in plan["slots"]:
            reps = [int(r) for r in sl["reps"]]
            for r in reps:
                planned[r] = (n, int(sl["slot"]))
            stp = os.path.join(root, "status", f"job{j}.slot{sl['slot']}.json")
            st = None
            if os.path.exists(stp):
                try:
                    st = json.load(open(stp))
                except Exception:
                    alarms.append(f"bank job {n} slot {sl['slot']}: status unreadable")
            if st is None:
                if terminal and not dispo:
                    alarms.append(f"bank job {n} slot {sl['slot']}: no worker status after the job ended (killed, segfault or import failure: read its log)")
                continue
            s_sum["ended"] += 1; s_sum["exits"][str(st.get("exit"))] = s_sum["exits"].get(str(st.get("exit")), 0) + 1
            new, res, left = st.get("new", []), st.get("resumed", []), st.get("left", [])
            if st.get("reps") != reps:
                alarms.append(f"bank job {n} slot {sl['slot']}: status reps {st.get('reps')} are not the plan's {reps}")
            if set(new) & set(res) or set(new) & set(left) or set(res) & set(left) or sorted(new + res + left) != sorted(reps):
                alarms.append(f"bank job {n} slot {sl['slot']}: new/resumed/left are not a partition of {reps}")
            ex = st.get("exit")
            if ex == 0 and left:
                alarms.append(f"bank job {n} slot {sl['slot']}: exit 0 with reps left {left}")
            elif ex == 75 and not left:
                alarms.append(f"bank job {n} slot {sl['slot']}: exit 75 with nothing left")
            elif ex not in (0, 75):
                alarms.append(f"bank job {n} slot {sl['slot']}: worker exit {ex} ({str(st.get('reason'))[:120]})")
            if mem_stop and finite_nonneg(st.get("maxrss")) and st["maxrss"] > mem_stop:
                alarms.append(f"bank job {n} slot {sl['slot']}: worker maxrss {st['maxrss']/2**30:.2f} GiB above the stop")
            for k in ("wall_s", "cpu_s", "maxrss"):
                if not finite_nonneg(st.get(k)):
                    alarms.append(f"bank job {n} slot {sl['slot']}: status {k} is not finite and non-negative")
            s_sum["new"] += len(new); s_sum["resumed"] += len(res); s_sum["left"] += len(left)
            for r in new + res:
                v = vreps.get(str(r))
                if not v or not v.get("record") or not v["record"].get("ok"):
                    alarms.append(f"bank rep {r}: no valid record in the producer runtime ({(v or {}).get('record')})"); continue
                if not v.get("timing") or not v["timing"].get("ok"):
                    alarms.append(f"bank rep {r}: no valid timing ({(v or {}).get('timing')})"); continue
                if r in new and (v["timing"].get("job") != j or v["timing"].get("slot") != int(sl["slot"])):
                    alarms.append(f"bank rep {r}: timing names job {v['timing'].get('job')} slot {v['timing'].get('slot')}, not {j} slot {sl['slot']}")
        summary[str(n)] = s_sum
    for r, v in vreps.items():
        if int(r) not in planned:
            alarms.append(f"bank rep {r}: a record or timing that no plan assigns (foreign evidence)")
        elif v.get("record") and not v["record"].get("ok"):
            alarms.append(f"bank rep {r}: invalid record ({v['record'].get('reason')})")
        elif v.get("record") and v["record"].get("ok") and not (v.get("timing") or {}).get("ok"):
            alarms.append(f"bank rep {r}: record without a valid timing")
    return alarms, notes, summary, jobs, outputs


def ledger_line(path, label):
    if not os.path.exists(path):
        return f"{label}: ledger not in this snapshot"
    led = json.load(open(path))
    settled = sum(float(e.get("settled_core_h", 0) or 0) for e in led["entries"].values() if e.get("state") == "settled")
    live = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
    return f"{label}: cap {led.get('cap_core_h')} settled {settled:.1f} live {live:.1f}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "row22_bank_manifest.json"))
    ap.add_argument("--no-pull", action="store_true", help="tests: read the local cache (never fresh evidence)")
    ap.add_argument("--verify-file", default=None, help="tests: a verify document instead of the producer runtime")
    ap.add_argument("--pbs-file", default=None, help="tests: {job_id: {state, exit, mem_kb}} instead of the scheduler")
    ap.add_argument("--publish-receipt", action="store_true")
    ap.add_argument("--qualify", type=int, default=None)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); now = time.time()
    manifest_rel = "chpc/" + os.path.basename(a.manifest)
    alarms = []
    fresh = False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(man); alarms += probs
    if a.verify_file:
        verify = json.load(open(a.verify_file)); vsha = sha_file(a.verify_file); vprob = ""
    else:
        verify, vsha, vprob = verify_remote(man, manifest_rel)
    if vprob:
        alarms.append(vprob); verify = verify or {"reps": {}}
    led_p = os.path.join(LIVE_DIR, "campaign", "budget.json")
    ledger = json.load(open(led_p)) if os.path.exists(led_p) else {"entries": {}}
    if not os.path.exists(led_p):
        alarms.append("the bank ledger is not in the snapshot")
    ids = [e["job_id"] for e in ledger["entries"].values() if e.get("kind") == "bank" and e.get("job_id")]
    settled = {e["job_id"]: e for e in ledger["entries"].values() if e.get("kind") == "bank" and e.get("job_id") and e.get("state") == "settled"}
    obs, oprob = pbs_observe(ids, a.pbs_file, settled)
    if oprob:
        alarms.append(oprob)
    if verify.get("seed_problem"):
        alarms.append(f"seed gate: {verify['seed_problem']}")
    if verify.get("environment_bad") or verify.get("code_bad"):
        alarms.append(f"producer runtime: environment {verify.get('environment_bad')} code {verify.get('code_bad')}")
    if verify.get("binding_equal") is False:
        alarms.append("the bank binding is not what the producer runtime recomputes")
    if verify.get("manifest_sha256") and verify["manifest_sha256"] != sha_file(a.manifest):
        alarms.append("the producer runtime's manifest is not this manifest")
    al, notes, summary, jobs, outputs = reconcile(man, verify, obs, ledger)
    alarms += al
    production = fresh and not a.no_pull and not a.verify_file and not a.pbs_file
    print(f"ROW 22 BANK, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  evidence: "
          f"{'FRESH snapshot' if fresh else 'NOT FRESH'}{'' if production else ' (not production)'}")
    print("  " + ledger_line(led_p, "bank ledger"))
    nrec = sum(1 for v in verify.get("reps", {}).values() if (v.get("record") or {}).get("ok"))
    print(f"  valid records {nrec}/{len(man['datasets']['reps'])} (producer runtime); verify {str(vsha)[:12]}")
    for n, s in summary.items():
        print(f"  bank job {n} {s['job_id']} PBS {s['state']} exit {s['exit']}: workers ended {s['ended']}/{s['slots']} exits {s['exits']}, "
              f"new {s['new']} resumed {s['resumed']} left {s['left']}")
        if s.get("disposition"):
            d = s["disposition"]
            print(f"    DISPOSITIONED closed-no-record: exit {d['scheduler_exit']}, charged {d['settled_core_h']:.2f} core-h, "
                  f"{len(d['uncompleted'])} reps uncompleted (origin plan), output {d['output_sha256'][:12]}")
        elif s.get("disposition_held"):
            print(f"    not dispositioned: {s['disposition_held']}")
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms, but NOT fresh evidence"))
    for x in alarms:
        print("   -", x)
    bp = os.path.join(LIVE_DIR, "root", "bank_binding.json")
    bound = dict(manifest_sha256=sha_file(a.manifest), root=man["storage"]["root"], campaign=man["storage"]["campaign"],
                 code=dict(man["code"]["files"]), wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"),
                 bank_binding_sha256=sha_file(bp) if os.path.exists(bp) else None, verify_sha256=vsha, jobs=jobs,
                 job_outputs=outputs)
    receipt = dict(schema=WATCH_SCHEMA, time=now, fresh=fresh, production=production, alarms=alarms, bound=bound, jobs=summary)
    os.makedirs(RECEIPTS, exist_ok=True)
    if a.verify_file is None and verify.get("reps") is not None:
        open(os.path.join(RECEIPTS, f"verify_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json"), "w").write(json.dumps(verify, sort_keys=True))
    rc_out = 1 if (alarms or not fresh) else 0
    if a.publish_receipt or a.qualify is not None:
        rp = os.path.join(RECEIPTS, f"bank_watch_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json")
        json.dump(receipt, open(rp, "w"), indent=1, allow_nan=False)
        if production:
            rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", rp, f"{HOST}:{man['storage']['root']}/gate/{os.path.basename(rp)}"])
            print(f"  receipt {os.path.basename(rp)} " + ("copied to the root's gate" if rc == 0 else f"NOT copied (rc {rc}: {err.strip()[:80]})"))
    if a.qualify is not None:
        n = str(int(a.qualify)); why = []
        if not production:
            why.append("the evidence is not fresh production evidence")
        if alarms:
            why.append(f"{len(alarms)} alarm(s)")
        s = summary.get(n)
        if not s:
            why.append(f"no bank job {n} in the ledger")
        else:
            if s["state"] not in TERMINAL or s["exit"] != 0:
                why.append(f"job {n} is not terminal with scheduler exit 0 (state {s['state']}, exit {s['exit']})")
            if s.get("observation") != "qstat":
                why.append(f"job {n} is observed from its settlement, not the scheduler (a qualification needs qstat)")
            if s["ended"] != s["slots"] or s["exits"] != {"0": s["slots"]}:
                why.append(f"job {n}: not every planned worker ended with exit 0 ({s['exits']}, {s['ended']}/{s['slots']})")
            if s["left"]:
                why.append(f"job {n}: {s['left']} planned rep(s) left")
            if s.get("disposition") is not None:
                why.append(f"job {n} is dispositioned (closed-no-record); a dispositioned job never qualifies")
        jn = jobs.get(n)
        if not jn or None in jn.values():
            why.append(f"job {n} has no PBS id, token or plan hash to bind")
        if why:
            print(f"\n  NOT QUALIFIED (bank job {n}):"); [print("   -", w) for w in why]
            return 1
        qp = os.path.join(RECEIPTS, f"qualified_bank_job{n}.json")
        json.dump(dict(schema=QUAL_SCHEMA, qualified_job=int(n), by="R052", time=now, production=production, bound=bound, receipt=receipt),
                  open(qp, "w"), indent=1, allow_nan=False)
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", qp, f"{HOST}:{man['storage']['root']}/gate/qualified_bank_job{n}.json"])
        print(f"\n  QUALIFIED: bank job {n} ({sha_file(qp)[:16]}) " + ("copied to the root's gate" if rc == 0 else f"NOT copied (rc {rc})")
              + " - evidence for the reviewer; the submitter also needs the adopted review")
        return 0 if rc == 0 else 1
    return rc_out


if __name__ == "__main__":
    sys.exit(main())
