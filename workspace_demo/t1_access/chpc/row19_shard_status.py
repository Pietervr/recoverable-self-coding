"""Row 19 sharded route: the live view from the Mac (R052), failing closed (Codex RSC 395e49d).

ONE fresh snapshot per poll - the shard root, the shard campaign ledger, the PBS job files, AND the sequential slice's
roots and ledger, pulled together; any failed pull is an alarm and nothing stale is called fresh. From it:
  RECORDS   every record file validated against the frozen task rebuilt from the manifest and the task binding
            (row19_control_compare.expected_contract, with the pinned-runtime identity oracle where this host cannot
            rebuild the identity; validate_record), and bound to the index in its file name;
  TIMING    one timing file per accepted record, matching its rep, index and identity, with finite measurements; a
            record without one is INCOMPLETE MEASUREMENT (an alarm: no unqualified distribution, no stage-2 costing);
  MEMORY    every worker peak against the per-worker stop; each job's scheduler-accounted peak against its request;
  JOBS      each ledger shard entry reconciled with its plan, its workers' statuses, the ledger's runner exit and the
            scheduler's state: a terminal job with a missing, malformed, foreign or undeclared worker exit, a runner
            exit other than 0 or 75, a failed admission, or no runner end is an alarm; a missing status is normal only
            while the job is queued or running; a job that started without its task bindings is an alarm;
  PARITY    shard records against the sequential chain's VALIDATED records for the same identity and index (C1, mains),
            compared on the canonical scientific payload with float BITS (float.hex), so +0.0 and -0.0 differ; zero
            overlap is reported as PENDING; any difference is an alarm;
  BUDGET    both campaign ledgers (settled and live) against the programme's allocation.
  SLOTS     (revision 3, Codex RSC 13a2fea) each worker's terminal status against its plan slot EXACTLY: the assigned list
            equal to the plan's, new / resumed / left a partition of it, exit 0 with nothing left and exit 75 with
            something left, every `new` index an accepted record whose timing names this job and slot, no `left` index
            carrying this job's timing; and every accepted record's timing traced to a ledger job whose plan assigns
            that index to that slot and whose status lists it as new. A deadline exit 75 is reported slot by slot.
`--publish-receipt` retains the view as a receipt and copies it to <root>/gate/watch_receipt.json (the submitter's gate
reads it). `--qualify 1` writes the pilot's qualification when - on fresh evidence with zero alarms - job 1 has ended
in the scheduler (state F, exit 0 or 75) with every planned worker ended 0 or 75, each dataset in its plan has an
accepted record from it, the scheduler-accounted memory is under the request with headroom, and production parity is
OBSERVED (not pending) and equal for all datasets.
RECEIPTS ARE BOUND (revision 3): each carries `bound` = the manifest's SHA-256, the root, the campaign, the manifest's
code pins and wrapper hash, the task identities and the manifest hash in each binding, and per shard job its PBS id,
reservation token and plan-file SHA-256 - what the submitter's gate recomputes on the cluster and compares. A receipt
is `production` only from a fresh pull with the scheduler asked and the upload enabled; --no-pull, --pbs-file and
--no-upload produce receipts marked non-production, which the gate refuses and which are never uploaded as a
qualification. A qualification is EVIDENCE for the reviewer, not authority to submit: the gate also requires the
operator's record of the reviewer's verdict (row19_shard_submit.py --adopt-review).

    python chpc/row19_shard_status.py --manifest chpc/row19_shard_manifest.json [--publish-receipt] [--qualify 1]
Exit 1 on any alarm or when the evidence is not fresh; 0 only on fresh evidence with none."""
import os, sys, json, glob, math, time, shutil, hashlib, argparse, subprocess, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
os.environ.setdefault("NPROC", "1")
from row19_control_compare import expected_contract, validate_record
import row19_identity_oracle as O

HOST = "chpc-scp"
LIVE_DIR = os.path.join(HERE, "results", "row19_shard", "live")
RECEIPTS = os.path.join(HERE, "results", "row19_shard", "receipts")
SCI = ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep")
OK_EXITS = (0, 75)
TERMINAL = ("F", "E", "X", "gone")
WATCH_SCHEMA = "row19-shard-watch-3"
QUAL_SCHEMA = "row19-shard-qualification-3"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ints(v):
    return isinstance(v, list) and all(isinstance(i, int) and not isinstance(i, bool) for i in v)


def slot_problems(s, slot, job, k, acc_all, timing_all, idents):
    """Why a worker's terminal status (exit 0 or 75) is not its plan slot's exact assignment with a consistent account."""
    out = []
    rep = int(slot["rep"]); assigned = [int(i) for i in slot["indices"]]
    if s.get("job") != job or s.get("slot") != k:
        out.append(f"the status names job {s.get('job')} slot {s.get('slot')}")
    if s.get("rep") != rep:
        out.append(f"the status's rep {s.get('rep')} is not the plan's {rep}"); return out
    L = {}
    for name in ("indices", "new", "resumed", "left"):
        if not _ints(s.get(name)):
            out.append(f"the status's `{name}` is not a list of integers"); return out
        L[name] = s[name]
    if L["indices"] != assigned:
        out.append(f"the status's assigned indices {L['indices']} are not the plan's exact list {assigned}")
    parts = L["new"] + L["resumed"] + L["left"]
    if len(parts) != len(set(parts)) or sorted(parts) != sorted(L["indices"]):
        out.append(f"new {L['new']} / resumed {L['resumed']} / left {L['left']} is not a partition of its indices {L['indices']}")
    if s.get("exit") == 0 and L["left"]:
        out.append(f"exit 0 with indices left {L['left']}")
    if s.get("exit") == 75 and not L["left"]:
        out.append("exit 75 with nothing left")
    if rep in idents and s.get("ident") != idents[rep]:
        out.append("the status's identity is not the task binding's")
    acc, tm = acc_all.get(rep, {}), timing_all.get(rep, {})
    for i in L["new"]:
        t = tm.get(i)
        if i not in acc:
            out.append(f"index {i} is reported new but has no accepted record")
        elif t is None or t.get("job") != job or t.get("slot") != k:
            out.append(f"index {i} is reported new but its timing names job {t.get('job') if t else None} slot {t.get('slot') if t else None}")
    for i in L["resumed"]:
        t = tm.get(i)
        if i not in acc:
            out.append(f"index {i} is reported resumed but has no accepted record")
        elif t is not None and t.get("job") == job:
            out.append(f"index {i} is reported resumed but its timing names this job")
    for i in L["left"]:
        t = tm.get(i)
        if i in acc and t is not None and t.get("job") == job:
            out.append(f"index {i} is reported left but an accepted record with this job's timing exists")
    return out


def sh(cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def canon(v):
    """The canonical form compared for parity: floats by their bits (float.hex), ints and bools as themselves."""
    if isinstance(v, bool) or v is None or isinstance(v, (int, str)):
        return v
    if isinstance(v, float):
        return "f:" + v.hex()
    if isinstance(v, (list, tuple)):
        return [canon(x) for x in v]
    if isinstance(v, dict):
        return {k: canon(v[k]) for k in sorted(v)}
    return repr(v)


def payload(rec):
    return json.dumps({k: canon(rec.get(k)) for k in SCI}, sort_keys=True)


def fresh_snapshot(man):
    """Pull everything this view reads into a new staging directory; rotate it in only when EVERY pull succeeded."""
    sh_ = man["shard"]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage = os.path.join(os.path.dirname(LIVE_DIR), f"stage_{stamp}")
    pulls = [("campaign", man["storage"]["campaign"]), ("root", man["storage"]["root"]), ("jobs", os.path.join(sh_["toolchain"], "jobs")),
             ("seq_campaign", sh_["sequential_campaign"])] + [(os.path.join("seq", os.path.basename(r.rstrip("/"))), r) for r in sh_["sequential_roots"]]
    problems = []
    for name, remote in pulls:
        local = os.path.join(stage, name); os.makedirs(local, exist_ok=True)
        rc, out, err = sh(["scp", "-q", "-r", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{remote}/.", local])
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True); return False, problems
    shutil.rmtree(LIVE_DIR, ignore_errors=True); shutil.move(stage, LIVE_DIR)
    return True, []


def pbs_observe(job_ids):
    """{job_id: {state, exit, mem_kb, walltime}} from one `qstat -xf`; a job the scheduler no longer lists is 'gone'."""
    if not job_ids:
        return {}, ""
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", "lengau", "qstat -xf " + " ".join(job_ids) + " 2>&1"])
    if rc not in (0, 35, 153) and not out:
        return None, f"qstat unreachable (rc {rc}): {err.strip()[:120]}"
    obs, cur = {j: {"state": "gone"} for j in job_ids}, None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Job Id:"):
            cur = s.split(":", 1)[1].strip(); obs.setdefault(cur, {})["state"] = obs.get(cur, {}).get("state", "gone")
        elif cur and " = " in s:
            k, v = s.split(" = ", 1)
            if k == "job_state":
                obs[cur]["state"] = v
            elif k == "Exit_status":
                obs[cur]["exit"] = int(v)
            elif k == "resources_used.mem":
                obs[cur]["mem_kb"] = int(v.rstrip("kb")) if v.endswith("kb") else None
            elif k == "resources_used.walltime":
                obs[cur]["walltime"] = v
    return obs, ""


def seq_records(ident, ex, B):
    """{index: [(root, record)]} of VALIDATED sequential records carrying this identity, plus the problems found."""
    out, bad = {}, 0
    for ck in glob.glob(os.path.join(LIVE_DIR, "seq", "*", "ckpt", f"refit_{ident[:24]}.jsonl")):
        where = os.path.basename(os.path.dirname(os.path.dirname(ck)))
        for line in open(ck).read().splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except Exception:
                bad += 1; continue
            if validate_record(d, ex, B):
                bad += 1; continue
            out.setdefault(d["rep"], []).append((where, d))
    return out, bad


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def ledger_totals(path):
    if not os.path.exists(path):
        return None
    led = json.load(open(path))
    settled = sum(float(e.get("settled_core_h", 0) or 0) for e in led["entries"].values() if e.get("state") == "settled")
    live = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
    return dict(cap=led.get("cap_core_h"), settled=settled, live=live, entries=led["entries"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "row19_shard_manifest.json"))
    ap.add_argument("--no-pull", action="store_true", help="read the local cache (never fresh evidence)")
    ap.add_argument("--pbs-file", default=None, help="tests: a JSON {job_id: {state, exit, mem_kb}} instead of asking the scheduler")
    ap.add_argument("--publish-receipt", action="store_true")
    ap.add_argument("--qualify", type=int, default=None, help="write the pilot's qualification for this job number when it holds")
    ap.add_argument("--no-upload", action="store_true", help="tests: do not copy receipts to the cluster")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); B = int(man["cfg"]["n_boot_refit"]); shd = man["shard"]
    reps = [int(r) for r in man["datasets"]["reps"]]
    manifest_sha = sha_file(a.manifest)
    alarms, notes, fresh = [], [], False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(man); alarms += probs
    root = os.path.join(LIVE_DIR, "root")
    now = time.time()
    print(f"ROW 19 SHARDED ROUTE, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  evidence: "
          f"{'FRESH snapshot' if fresh else 'LOCAL CACHE (not fresh evidence)' if a.no_pull else 'PULL FAILED - stale'}")
    led = ledger_totals(os.path.join(LIVE_DIR, "campaign", "budget.json"))
    seq_led = ledger_totals(os.path.join(LIVE_DIR, "seq_campaign", "budget.json"))
    entries = []
    if led is None:
        alarms.append("shard campaign ledger absent in the snapshot")
    else:
        entries = sorted((e for e in led["entries"].values() if e.get("kind") == "shard"), key=lambda e: e["rep"])
    if seq_led is None:
        alarms.append("the sequential slice's ledger is absent in the snapshot")
    if led and seq_led:
        alloc = float(shd.get("allocation_core_h", 100000))
        print(f"  budget: shard ledger cap {led['cap']} settled {led['settled']:.1f} live {led['live']:.1f}; slice ledger settled {seq_led['settled']:.1f} "
              f"live {seq_led['live']:.1f}; both campaigns {led['settled'] + led['live'] + seq_led['settled'] + seq_led['live']:.1f} of the {alloc:.0f} core-hour "
              f"allocation (other rows' use is in ledger rows 6 and 18)")
    # the scheduler's view of every shard job
    ids = [e["job_id"] for e in entries if e.get("job_id")]
    if a.pbs_file:
        pbs = json.load(open(a.pbs_file))
    elif a.no_pull:
        pbs = {}
    else:
        pbs, why = pbs_observe(ids)
        if pbs is None:
            alarms.append(f"PBS observation failed: {why}"); pbs = {}
    started = [e for e in entries if e.get("runner_started") or pbs.get(e.get("job_id"), {}).get("state") in ("R",) + TERMINAL]
    # records, timing, memory, parity - per dataset
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    oracle = O.load(root) if (fresh or a.no_pull) and os.path.exists(os.path.join(root, O.ORACLE_NAME)) else None
    summary, accepted_by_job = {}, {}
    acc_all, timing_all, idents, binding_sha = {}, {}, {}, {}
    for rep in reps:
        tp = os.path.join(root, f"task_{rep}.json")
        files = sorted(glob.glob(os.path.join(root, "records", f"rep{rep}", "rec_*.json")))
        if not os.path.exists(tp):
            if files or any(rep in {int(s["rep"]) for s in _plan(root, e).get("slots", [])} for e in started):
                alarms.append(f"rep {rep}: no task binding although a job that names it has started or {len(files)} record file(s) exist")
            else:
                print(f"  rep {rep}: no task binding yet (no job has started)")
            continue
        try:
            b = json.load(open(tp))["binding"]
            ex = expected_contract(a.manifest, b, oracle=oracle)
        except Exception as e:
            alarms.append(f"rep {rep}: the task binding is not this manifest's ({e})"); continue
        idents[rep] = b.get("ident"); binding_sha[rep] = b.get("manifest_sha")
        if b.get("manifest_sha") != manifest_sha:
            alarms.append(f"rep {rep}: the task binding names manifest {str(b.get('manifest_sha'))[:12]}, this view reads {manifest_sha[:12]}")
        acc, failed, bad, no_timing = {}, [], [], []
        acc_all[rep], timing_all[rep] = acc, {}
        walls, peaks = [], []
        for p in files:
            name = os.path.basename(p)
            try:
                d = json.load(open(p))
            except Exception:
                bad.append((name, "not JSON")); continue
            why = validate_record(d, ex, B)
            if why or f"rec_{d.get('rep', -1):03d}.json" != name:
                bad.append((name, why or "the record's index is not the file name's")); continue
            acc[d["rep"]] = d
            if d["failed"]:
                failed.append(d["rep"])
            tf = os.path.join(root, "timing", f"rep{rep}", f"t_{d['rep']:03d}.json")
            try:
                t = json.load(open(tf))
                if not (t.get("rep") == rep and t.get("index") == d["rep"] and t.get("ident") == d["ident"] and _finite(t.get("wall_s"))
                        and _finite(t.get("fit_seconds")) and _finite(t.get("maxrss"))):
                    raise ValueError("fields")
                walls.append(t["wall_s"]); peaks.append(t["maxrss"]); timing_all[rep][d["rep"]] = t
                accepted_by_job.setdefault(t.get("job"), {}).setdefault(rep, []).append(d["rep"])
            except Exception:
                no_timing.append(d["rep"])
        seq, seq_bad = seq_records(b["ident"], ex, B)
        both = sorted(set(acc) & set(seq)); diff = []
        for i in both:
            for where, s in seq[i]:
                if payload(acc[i]) != payload(s):
                    diff.append((i, where))
        equal = len(both) - len({i for i, _ in diff})
        parity = "PENDING (no index computed by both)" if not both else f"{len(both)} index(es) in both, {equal} bit-equal on the scientific payload"
        print(f"  rep {rep}: identity {b['ident'][:16]} basis {ex['basis']}; accepted {len(acc)}/{B}, failed {len(failed)}, rejected {len(bad)}, missing {B - len(acc)}; "
              f"sequential records validated {sum(len(v) for v in seq.values())}")
        if walls:
            ws = sorted(walls)
            print(f"    per-resample wall (packed): n {len(ws)}, median {statistics.median(ws)/3600:.2f} h, min {ws[0]/3600:.2f} h, max {ws[-1]/3600:.2f} h; "
                  f"peak worker memory {max(peaks)/2**30:.2f} GiB; records without a valid timing file: {len(no_timing)}")
        print(f"    production parity: {parity}" + (f"; DIFFERENT at {diff[:6]}" if diff else ""))
        summary[rep] = dict(accepted=len(acc), failed=len(failed), rejected=len(bad), no_timing=len(no_timing), overlap=len(both), equal=equal,
                            basis=ex["basis"], median_wall_s=(statistics.median(walls) if walls else None), peak_rss=(max(peaks) if peaks else None))
        if bad:
            alarms.append(f"rep {rep}: {len(bad)} record file(s) rejected, e.g. {bad[:3]}")
        if failed:
            alarms.append(f"rep {rep}: {len(failed)} FAILED resample(s): {failed[:10]}")
        if no_timing:
            alarms.append(f"rep {rep}: INCOMPLETE MEASUREMENT - {len(no_timing)} accepted record(s) without a valid timing file: {no_timing[:10]}")
        if seq_bad:
            alarms.append(f"rep {rep}: {seq_bad} sequential checkpoint line(s) for this identity failed validation (not used for parity)")
        if diff:
            alarms.append(f"rep {rep}: shard records differ from the sequential chain at {diff[:10]}")
        if mem_stop and peaks and max(peaks) > mem_stop:
            alarms.append(f"rep {rep}: a worker peak of {max(peaks)/2**30:.2f} GiB exceeds the {mem_stop/2**30:.2f} GiB per-worker stop")
    # jobs - plan, statuses, runner exit, scheduler state
    jobs, by_job = {}, {}
    for e in entries:
        n, job = int(e["rep"]), e.get("job_id")
        plan = _plan(root, e)
        if not plan:
            alarms.append(f"job {n} ({job}): its plan file is missing from the root"); continue
        o = pbs.get(job, {}) if job else {}
        state = o.get("state", "unknown" if not a.no_pull else "-")
        terminal = state in TERMINAL or e.get("runner_ended") is not None
        slots = {int(s["slot"]): s for s in plan["slots"]}
        sts, unread = {}, []
        for p in glob.glob(os.path.join(root, "status", f"job{job}.slot*.json")) if job else []:
            try:
                s = json.load(open(p)); sts[int(s["slot"])] = s
            except Exception:
                unread.append(os.path.basename(p))
        codes = [sts[k].get("exit") for k in sorted(sts)]
        out_p = os.path.join(LIVE_DIR, "jobs", f"row19_shard_{n}.out")
        out_txt = open(out_p, errors="replace").read() if os.path.exists(out_p) else ""
        mem = o.get("mem_kb")
        print(f"  job {n} {job} ledger {e.get('state')} PBS {state}: workers ended {len(sts)}/{len(slots)}, exits {dict((c, codes.count(c)) for c in set(codes))}, "
              f"runner exit {e.get('runner_exit')}" + (f", PBS peak memory {mem/2**20:.1f} GiB of {man['pbs']['mem_gb']} GiB requested" if mem else ""))
        for name in unread:
            alarms.append(f"job {n}: status file {name} is unreadable")
        table = []
        for k, s in sorted(sts.items()):
            if k not in slots:
                alarms.append(f"job {n}: a status exists for slot {k}, which the plan does not have"); continue
            if s.get("exit") not in OK_EXITS:
                alarms.append(f"job {n} slot {k}: worker exit {s.get('exit')} ({str(s.get('reason'))[:140]})")
            else:
                alarms += [f"job {n} slot {k}: {w}" for w in slot_problems(s, slots[k], job, k, acc_all, timing_all, idents)]
            lst = {name: (s.get(name) if _ints(s.get(name)) else None) for name in ("new", "resumed", "left")}
            table.append(dict(slot=k, rep=s.get("rep"), assigned=[int(i) for i in slots[k]["indices"]], new=lst["new"], resumed=lst["resumed"],
                              left=lst["left"], exit=s.get("exit"), reason=str(s.get("reason") or "")[:160], wall_s=s.get("wall_s"), maxrss=s.get("maxrss")))
        if job:
            by_job[job] = (n, slots, sts)
        undone = [(r["slot"], r["rep"], r["left"]) for r in table if r["exit"] == 75]
        if table:
            print(f"    slots: new {sum(len(r['new'] or []) for r in table)}, resumed {sum(len(r['resumed'] or []) for r in table)}, "
                  f"left {sum(len(r['left'] or []) for r in table)} index(es)" + (f"; exit 75 (slot, rep, left): {undone}" if undone else ""))
        if "ADMISSION FAILED" in out_txt:
            alarms.append(f"job {n}: the PBS script reports a FAILED ADMISSION (see jobs/row19_shard_{n}.out)")
        if e.get("runner_exit") is not None and e.get("runner_exit") not in OK_EXITS:
            alarms.append(f"job {n}: runner exit {e.get('runner_exit')}")
        if terminal:
            missing = sorted(set(slots) - set(sts))
            if missing:
                alarms.append(f"job {n}: ended (PBS {state}) with no terminal status for slot(s) {missing[:12]}")
            if e.get("runner_ended") is None:
                alarms.append(f"job {n}: the scheduler shows it ended (PBS {state}) but the runner never recorded its end - killed or vanished; keep the reservation")
            if o.get("exit") not in (None,) + OK_EXITS:
                alarms.append(f"job {n}: PBS Exit_status {o.get('exit')}")
        elif state == "unknown":
            alarms.append(f"job {n} ({job}): PBS state unknown")
        if mem and mem / 2 ** 20 > 0.9 * float(man["pbs"]["mem_gb"]):
            alarms.append(f"job {n}: scheduler-accounted memory {mem/2**20:.1f} GiB is above 90% of the {man['pbs']['mem_gb']} GiB request")
        pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[n] = dict(job_id=job, state=state, terminal=terminal, slots=len(slots), ended=len(sts), exits=codes, runner_exit=e.get("runner_exit"),
                       mem_kb=mem, reps=sorted({int(s["rep"]) for s in plan["slots"]}), pbs_exit=o.get("exit"), token=e.get("token"),
                       plan_sha256=(sha_file(pp) if os.path.exists(pp) else None), slot_table=table)
    # every accepted record's timing traced to the job, slot and plan that produced it
    for rep in sorted(timing_all):
        for i, t in sorted(timing_all[rep].items()):
            pj = by_job.get(t.get("job"))
            if pj is None:
                alarms.append(f"rep {rep} index {i}: its timing names job {t.get('job')}, which is not a shard job in the ledger with a plan"); continue
            n_, slots_, sts_ = pj
            sl = slots_.get(t.get("slot"))
            if sl is None or int(sl["rep"]) != rep or i not in [int(x) for x in sl["indices"]]:
                alarms.append(f"rep {rep} index {i}: its timing names job {n_} slot {t.get('slot')}, whose plan does not assign it"); continue
            s_ = sts_.get(t.get("slot"))
            if s_ is not None and (not _ints(s_.get("new")) or i not in s_["new"]):
                alarms.append(f"rep {rep} index {i}: its timing names job {n_} slot {t.get('slot')}, whose status does not list it as new")
    production = bool(fresh) and not a.no_pull and not a.pbs_file and not a.no_upload
    bound = dict(manifest_sha256=manifest_sha, root=man["storage"]["root"], campaign=man["storage"]["campaign"], code=dict(man["code"]["files"]),
                 wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"),
                 identities={str(r): idents.get(r) for r in reps}, binding_manifest_sha={str(r): binding_sha.get(r) for r in reps},
                 jobs={str(n): dict(job_id=j["job_id"], token=j["token"], plan_sha256=j["plan_sha256"]) for n, j in sorted(jobs.items())})
    ok = not alarms and fresh
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms IN THE LOCAL CACHE (not fresh evidence)"))
    for x in alarms:
        print("   -", x)
    receipt = dict(schema=WATCH_SCHEMA, time=now, fresh=bool(fresh), production=production, alarms=alarms, reps=summary, jobs=jobs,
                   manifest=os.path.basename(a.manifest), bound=bound,
                   ledger=(dict(cap=led["cap"], settled=led["settled"], live=led["live"]) if led else None))
    if a.publish_receipt or a.qualify is not None:
        os.makedirs(RECEIPTS, exist_ok=True)
        rp = os.path.join(RECEIPTS, f"watch_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json")
        json.dump(receipt, open(rp, "w"), indent=1, allow_nan=False)
        if production:
            rc, out, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", rp, f"{HOST}:{man['storage']['root']}/gate/watch_receipt.json"])
            print(f"  receipt {os.path.basename(rp)} " + ("copied to the root's gate" if rc == 0 else f"NOT copied (rc {rc}: {err.strip()[:100]})"))
        else:
            print(f"  receipt {os.path.basename(rp)} retained locally (NOT production evidence: no fresh pull, a scheduler fixture, or upload disabled)")
    if a.qualify is not None:
        n = int(a.qualify); why = []
        j = jobs.get(n)
        if not fresh and not a.no_upload:
            why.append("the evidence is not a fresh snapshot")
        if alarms:
            why.append(f"{len(alarms)} alarm(s)")
        if not j:
            why.append(f"job {n} is not in the ledger")
        else:
            if not j["terminal"] or j["runner_exit"] not in OK_EXITS or j["ended"] != j["slots"] or any(c not in OK_EXITS for c in j["exits"]):
                why.append(f"job {n} is not terminal with every planned worker ended 0 or 75 (ended {j['ended']}/{j['slots']}, runner exit {j['runner_exit']})")
            if j["state"] != "F" or j["pbs_exit"] not in OK_EXITS:
                why.append(f"the scheduler does not show job {n} finished with exit 0 or 75 (state {j['state']}, Exit_status {j['pbs_exit']})")
            if not j["job_id"] or not j["token"] or not j["plan_sha256"]:
                why.append(f"job {n} has no PBS id, reservation token or plan hash to bind the qualification to")
            if not j["mem_kb"]:
                why.append("the scheduler-accounted peak memory of the job is not observed")
            for rep in j["reps"]:
                if not accepted_by_job.get(j["job_id"], {}).get(rep):
                    why.append(f"job {n} produced no accepted record for rep {rep}")
        for rep in reps:
            s = summary.get(rep)
            if not s or s["overlap"] < 1 or s["equal"] != s["overlap"]:
                why.append(f"rep {rep}: production parity is not observed and equal (overlap {s['overlap'] if s else 0})")
            if idents.get(rep) is None or binding_sha.get(rep) != manifest_sha:
                why.append(f"rep {rep}: no task binding of this manifest to bind the qualification to")
        if why:
            print(f"\n  NOT QUALIFIED (job {n}):"); [print("   -", w) for w in why]
            return 1
        qp = os.path.join(RECEIPTS, f"qualified_job{n}.json")
        json.dump(dict(schema=QUAL_SCHEMA, qualified_job=n, by="R052", time=now, production=production, bound=bound, receipt=receipt),
                  open(qp, "w"), indent=1, allow_nan=False)
        if not production:
            print(f"\n  QUALIFIED: job {n} on NON-PRODUCTION evidence (receipt {os.path.basename(qp)}, kept locally; the gate refuses it)")
        elif not a.no_upload:
            rc, out, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", qp, f"{HOST}:{man['storage']['root']}/gate/qualified_job{n}.json"])
            if rc != 0:
                print(f"  qualification written locally but NOT copied (rc {rc}: {err.strip()[:100]})"); return 1
        if production:
            print(f"\n  QUALIFIED: job {n} (receipt {os.path.basename(qp)}) - evidence for the reviewer; the gate also needs the adopted review")
    return 0 if ok or (a.no_pull and not alarms) else 1


def _plan(root, e):
    p = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
    try:
        return json.load(open(p))
    except Exception:
        return {}


if __name__ == "__main__":
    sys.exit(main())
