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
`--publish-receipt` retains the view as a receipt and copies it to <root>/gate/watch_receipt.json (the submitter's gate
reads it). `--qualify 1` writes the pilot's qualification when - on fresh evidence with zero alarms - job 1 is terminal
with every planned worker ended 0 or 75, each dataset in its plan has an accepted record from it, the scheduler-accounted
memory is under the request with headroom, and production parity is OBSERVED (not pending) and equal for all datasets.

    python chpc/row19_shard_status.py --manifest chpc/row19_shard_manifest.json [--publish-receipt] [--qualify 1]
Exit 1 on any alarm or when the evidence is not fresh; 0 only on fresh evidence with none."""
import os, sys, json, glob, math, time, shutil, argparse, subprocess, statistics

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
        acc, failed, bad, no_timing = {}, [], [], []
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
                walls.append(t["wall_s"]); peaks.append(t["maxrss"])
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
    jobs = {}
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
        for k, s in sts.items():
            if k not in slots:
                alarms.append(f"job {n}: a status exists for slot {k}, which the plan does not have")
            elif s.get("exit") not in OK_EXITS:
                alarms.append(f"job {n} slot {k}: worker exit {s.get('exit')} ({str(s.get('reason'))[:140]})")
            elif s.get("rep") != int(slots[k]["rep"]) or not set(s.get("indices") or []) <= set(int(i) for i in slots[k]["indices"]):
                alarms.append(f"job {n} slot {k}: the status's rep or indices are not the plan's")
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
        jobs[n] = dict(job_id=job, state=state, terminal=terminal, slots=len(slots), ended=len(sts), exits=codes, runner_exit=e.get("runner_exit"),
                       mem_kb=mem, reps=sorted({int(s["rep"]) for s in plan["slots"]}))
    ok = not alarms and fresh
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms IN THE LOCAL CACHE (not fresh evidence)"))
    for x in alarms:
        print("   -", x)
    receipt = dict(time=now, fresh=bool(fresh), alarms=alarms, reps=summary, jobs=jobs, manifest=os.path.basename(a.manifest),
                   ledger=(dict(cap=led["cap"], settled=led["settled"], live=led["live"]) if led else None))
    if a.publish_receipt or a.qualify is not None:
        os.makedirs(RECEIPTS, exist_ok=True)
        rp = os.path.join(RECEIPTS, f"watch_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json")
        json.dump(receipt, open(rp, "w"), indent=1)
        if fresh and not a.no_upload:
            rc, out, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", rp, f"{HOST}:{man['storage']['root']}/gate/watch_receipt.json"])
            print(f"  receipt {os.path.basename(rp)} " + ("copied to the root's gate" if rc == 0 else f"NOT copied (rc {rc}: {err.strip()[:100]})"))
        else:
            print(f"  receipt {os.path.basename(rp)} retained locally (not fresh evidence or upload disabled)")
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
            if not j["mem_kb"]:
                why.append("the scheduler-accounted peak memory of the job is not observed")
            for rep in j["reps"]:
                if not accepted_by_job.get(j["job_id"], {}).get(rep):
                    why.append(f"job {n} produced no accepted record for rep {rep}")
        for rep in reps:
            s = summary.get(rep)
            if not s or s["overlap"] < 1 or s["equal"] != s["overlap"]:
                why.append(f"rep {rep}: production parity is not observed and equal (overlap {s['overlap'] if s else 0})")
        if why:
            print(f"\n  NOT QUALIFIED (job {n}):"); [print("   -", w) for w in why]
            return 1
        qp = os.path.join(RECEIPTS, f"qualified_job{n}.json")
        json.dump(dict(qualified_job=n, by="R052", time=now, receipt=receipt), open(qp, "w"), indent=1)
        if not a.no_upload:
            rc, out, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", qp, f"{HOST}:{man['storage']['root']}/gate/qualified_job{n}.json"])
            if rc != 0:
                print(f"  qualification written locally but NOT copied (rc {rc}: {err.strip()[:100]})"); return 1
        print(f"\n  QUALIFIED: job {n} (receipt {os.path.basename(qp)})")
    return 0 if ok or (a.no_pull and not alarms) else 1


def _plan(root, e):
    p = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
    try:
        return json.load(open(p))
    except Exception:
        return {}


if __name__ == "__main__":
    sys.exit(main())
