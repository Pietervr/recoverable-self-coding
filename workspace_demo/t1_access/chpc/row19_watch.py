"""Ledger row 19: read the qualification slice LIVE from the Mac (owner, 2 Oct: "evaluate as the results come in";
Codex 523249d G; e44f804 R4/R5: no false green, expected jobs from the ledger, fresh per-poll snapshots, checkpoint-
derived progress and failures, PBS observation failures named, stop acknowledgments bound to the current request).

Every poll pulls a FRESH snapshot into its own staging directory (never merged into an older copy), then rotates it
into `results/row19_slice/live/` and keeps the previous snapshot under `archive/`. A failed or partial pull is an
ALARM, never a green. The expected evidence is derived from the campaign ledger (every reservation, its job id and its
state) - not from whatever files happen to exist: a live job must publish its task binding within the start-up
allowance, then its first accepted record within the original-fit allowance; accepted, failed and non-finite records
are counted from strict checkpoint records (checksum, identity, seed, B, draw, schema) that the manifest and the
task binding define, not from timing rows; timing rows are cross-checked against them. --qstat asks the login node for
every bound job's state; a failed observation or an absent id is named and alarmed (unknown is not green). Nothing
scientific is displayed or interpreted: a status file's result/interval and the records' stats are loaded and dropped.

    python chpc/row19_watch.py --manifest chpc/row19_slice_manifest.json [--expect-original-s S] [--expect-fit-s LO HI]
                               [--startup-allowance-s 900] [--stall-h 4] [--qstat] [--no-pull]
Exit 1 on any alarm (R052 then submits nothing further until it is diagnosed); 0 only on fresh evidence with no alarm.
Poll cadence: every 2 hours while any reservation is live.
"""
import argparse, glob, json, os, shutil, subprocess, sys, time, hashlib, math

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = "chpc-scp"
LOGIN = "lengau"
LIVE_DIR = os.path.join(HERE, "results", "row19_slice", "live")
ARCHIVE_DIR = os.path.join(HERE, "results", "row19_slice", "archive")
NEVER_SHOWN = ("result", "interval", "stats")
LIVE_STATES = ("reserved", "bound", "live")


def sh(cmd, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 255, "", str(e)


def record_sha(rec):
    return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != "sha"}, sort_keys=True, default=float).encode()).hexdigest()


def fresh_snapshot(campaign, roots):
    """Pull the campaign and every root into a new staging directory; rotate it in only when every pull succeeded."""
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage = os.path.join(os.path.dirname(LIVE_DIR), f"stage_{stamp}")
    os.makedirs(stage, exist_ok=True)
    problems = []
    for name, remote in [("campaign", campaign)] + [(os.path.basename(r.rstrip("/")), r) for r in roots]:
        local = os.path.join(stage, name)
        os.makedirs(local, exist_ok=True)
        rc, out, err = sh(["scp", "-q", "-r", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{remote}/.", local])
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True)
        return False, problems
    if os.path.exists(LIVE_DIR):
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        shutil.move(LIVE_DIR, os.path.join(ARCHIVE_DIR, f"live_{stamp}"))
        old = sorted(glob.glob(os.path.join(ARCHIVE_DIR, "live_*")))
        for p in old[:-3]:
            shutil.rmtree(p, ignore_errors=True)
    shutil.move(stage, LIVE_DIR)
    return True, []


def qstat_states(job_ids):
    """{job_id: state} from one `qstat -x` on the login node; 'gone' for an id the scheduler no longer lists; None on failure."""
    if not job_ids:
        return {}
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", LOGIN, "qstat -xf " + " ".join(job_ids) + " 2>&1"])
    if rc != 0 and not out:
        return None
    states = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("Job Id:"):
            cur = line.split(":", 1)[1].strip()
        elif cur and line.strip().startswith("job_state ="):
            states[cur] = line.split("=", 1)[1].strip()
    return {j: states.get(j, "gone") for j in job_ids}


def task_contract(manifest, binding):
    """Expected draws and bands for a task binding; None with a reason when the binding is not this manifest's."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    from row19_control_compare import expected_contract
    try:
        return expected_contract(manifest, binding), ""
    except Exception as e:
        return None, str(e)


def checkpoint_metadata(path, ex):
    """Accepted indices, failed indices, finite-fit metadata and problems from STRICT records; statistics dropped."""
    acc, failed, fits, problems = set(), set(), {}, []
    if not os.path.exists(path):
        return acc, failed, fits, problems, False
    lines = open(path).read().split("\n")
    tail = bool(lines and lines[-1].strip())
    body = [l for l in lines if l.strip()]
    for i, line in enumerate(body):
        try:
            d = json.loads(line)
        except Exception:
            if tail and i == len(body) - 1:
                continue
            problems.append(f"line {i+1}: not JSON"); continue
        if not isinstance(d, dict) or record_sha(d) != d.get("sha"):
            problems.append(f"line {i+1}: checksum rejected"); continue
        if d.get("ident") != ex["ident"] or d.get("seed") != ex["seed"] or d.get("n_rep") != ex["n_rep"]:
            problems.append(f"line {i+1}: identity/seed/B rejected"); continue
        r = d.get("rep")
        if not isinstance(r, int) or isinstance(r, bool) or not (0 <= r < ex["n_rep"]) or d.get("chosen") != ex["draws"][r]:
            problems.append(f"line {i+1}: index or draw rejected"); continue
        if not isinstance(d.get("failed"), bool) or not isinstance(d.get("stats"), dict) or sorted(d["stats"]) != sorted(ex["predictors"]):
            problems.append(f"line {i+1}: schema rejected"); continue
        fs = d.get("fit_seconds")
        if isinstance(fs, bool) or not isinstance(fs, (int, float)) or not math.isfinite(fs) or fs < 0:
            problems.append(f"line {i+1}: fit_seconds rejected"); continue
        if r in acc:
            problems.append(f"line {i+1}: index {r} twice"); continue
        acc.add(r); fits[r] = float(fs)
        if d["failed"]:
            failed.add(r)
    return acc, failed, fits, problems, tail


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "row19_slice_manifest.json"))
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--qstat", action="store_true", help="also ask the login node for every bound job's queue state")
    ap.add_argument("--expect-original-s", type=float, default=None, help="expected original-fit seconds (the addendum)")
    ap.add_argument("--expect-fit-s", nargs=2, type=float, default=None)
    ap.add_argument("--startup-allowance-s", type=float, default=900.0, help="from runner start to the task binding")
    ap.add_argument("--stall-h", type=float, default=4.0)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest))
    campaign = man["storage"]["campaign"]
    now = time.time()
    alarms, notes = [], []
    if a.expect_fit_s is not None:
        lo, hi = a.expect_fit_s
        if not (math.isfinite(lo) and math.isfinite(hi) and lo >= 0 and hi > lo):
            print("--expect-fit-s must be finite and ordered"); return 1
    if a.expect_original_s is not None and not (math.isfinite(a.expect_original_s) and a.expect_original_s > 0):
        print("--expect-original-s must be finite and positive"); return 1
    # 1. the ledger: which roots and jobs to expect (a first local read decides the roots to pull; the pull refreshes it)
    led_local = os.path.join(LIVE_DIR, "campaign", "budget.json")
    roots = set()
    if os.path.exists(led_local):
        try:
            roots = {e["root"] for e in json.load(open(led_local))["entries"].values()}
        except Exception:
            pass
    roots |= {man["storage"]["root"]}
    fresh = False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(campaign, sorted(roots))
        if not fresh:
            alarms += probs
        else:
            try:
                more = {e["root"] for e in json.load(open(led_local))["entries"].values()} - roots
            except Exception:
                more = set()
            if more:
                fresh, probs = fresh_snapshot(campaign, sorted(roots | more))
                if not fresh:
                    alarms += probs
    print(f"ROW 19 CAMPAIGN, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  evidence: "
          f"{'FRESH snapshot' if fresh else 'LOCAL CACHE (not fresh evidence)' if a.no_pull else 'PULL FAILED - stale'}")
    if not os.path.exists(led_local):
        alarms.append("campaign ledger absent in the snapshot")
        led = dict(cap_core_h=None, entries={})
    else:
        led = json.load(open(led_local))
    entries = sorted(led["entries"].values(), key=lambda e: e.get("created", 0))
    spent = sum(float(e.get("settled_core_h", 0.0)) for e in entries if e.get("state") == "settled")
    live = sum(float(e.get("reserved_core_h", 0.0)) for e in entries if e.get("state") in LIVE_STATES)
    cap = led.get("cap_core_h")
    print(f"  ledger: cap {cap}  spent {spent:.1f}  live reserved {live:.1f}  entries {len(entries)}")
    if cap and spent + live > float(cap) + 1e-9:
        alarms.append("ledger: spent + live reserved exceeds the cap")
    # 2. PBS observation of every bound or live job
    bound = [e for e in entries if e.get("job_id") and e.get("state") in ("bound", "live")]
    qs = None
    if a.qstat and bound:
        qs = qstat_states([e["job_id"] for e in bound])
        if qs is None:
            alarms.append("PBS observation failed (qstat unreachable): job states unknown")
    stops = {}
    for p in glob.glob(os.path.join(LIVE_DIR, "campaign", "STOP*")):
        try:
            stops[os.path.basename(p)] = json.load(open(p))
        except Exception:
            stops[os.path.basename(p)] = dict(id="unreadable")
    if stops:
        notes.append("stop request(s): " + ", ".join(f"{k} id {v.get('id')}" for k, v in stops.items()))
    # 3. every expected job and dataset
    for e in entries:
        if e.get("state") not in LIVE_STATES:
            continue
        root = e["root"]; rep = e.get("rep"); lr = os.path.join(LIVE_DIR, os.path.basename(root.rstrip("/")))
        q = (qs or {}).get(e.get("job_id")) if qs is not None else ("-" if not a.qstat else "unknown")
        started = e.get("runner_started"); ended = e.get("runner_exit")
        phase = "settled" if e["state"] == "settled" else "ended" if ended is not None else "running" if started else "queued/not started"
        print(f"\n  {e['kind']:<6} rep {rep} attempt {e['attempt']} {e['state']:<8} job {e.get('job_id')} PBS {q}  {phase}  "
              f"{e['reserved_core_h']:.0f} core-h reserved, runner exit {ended}")
        if e["state"] == "live" and ended == 4:
            alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: HELD (exit 4) - diagnose before any resubmission")
        if a.qstat and e.get("job_id") and q in ("gone", "F", "E") and ended is None:
            alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: PBS says {q} but the runner never ended - killed or crashed; keep the reservation")
        if a.qstat and e.get("job_id") and q == "unknown":
            alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: PBS state unknown")
        if e["kind"] == "stage0" or rep is None:
            continue
        tp = os.path.join(lr, f"task_{rep}.json")
        if not os.path.exists(tp):
            if started and ended is None and now - started > a.startup_allowance_s:
                alarms.append(f"{e['kind']} rep {rep}: live for {(now-started)/60:.0f} min without a task binding (allowance {a.startup_allowance_s/60:.0f} min)")
            elif started and ended is not None:
                alarms.append(f"{e['kind']} rep {rep}: the runner ended (exit {ended}) without a task binding")
            else:
                print(f"    no task binding yet ({phase})")
            continue
        task = json.load(open(tp)); b = task["binding"]
        ex, why = task_contract(a.manifest, b)
        if ex is None:
            alarms.append(f"rep {rep}: task binding is not this manifest's ({why})"); continue
        ck = os.path.join(lr, "ckpt", os.path.basename(b["ckpt"]))
        acc, failed, fits, problems, tail = checkpoint_metadata(ck, ex)
        target = ex["n_rep"] if b.get("until") is None else int(b["until"])
        rows = [json.loads(l) for l in open(os.path.join(lr, f"timing_{rep}.jsonl")).read().splitlines() if l.strip()] if os.path.exists(os.path.join(lr, f"timing_{rep}.jsonl")) else []
        sp = os.path.join(lr, f"status_{rep}.json")
        st = {}
        if os.path.exists(sp):
            st = json.load(open(sp))
            for k in NEVER_SHOWN:
                st.pop(k, None)
        running = e["state"] == "live" and ended is None
        fvals = sorted(v for r, v in fits.items() if r not in failed)
        rate_h = None
        if len(rows) >= 2 and rows[-1]["t"] > rows[0]["t"]:
            rate_h = (len(rows) - 1) / (rows[-1]["t"] - rows[0]["t"]) * 3600
        left = max(0, target - len(acc))
        print(f"    dataset rep {rep}: accepted {len(acc)}/{target} from strict checkpoint records, failed {len(failed)}, timing rows {len(rows)}, "
              f"watermark {task.get('expected_accepted')}, status phase {st.get('phase', 'none yet')}")
        if st:
            print(f"      last job {st.get('job')}: exit {st.get('exit')} new {st.get('n_new')} resumed {st.get('n_resumed')} tail-repaired "
                  f"{st.get('n_tail_repaired')} damaged {st.get('n_damaged')} partial={st.get('partial')} target_complete={st.get('target_complete')} "
                  f"stop={st.get('stopped_by_request')} mem_breach={st.get('memory_breach')} original {st.get('original_seconds', 0):.0f} s "
                  f"cached={st.get('original_cached')} util {st.get('utilisation', 0):.2f} maxrss {st.get('maxrss_bytes', 0)/2**30:.2f} GiB")
        if fvals:
            print(f"      fit s: n {len(fvals)} min {fvals[0]:.0f} median {fvals[len(fvals)//2]:.0f} max {fvals[-1]:.0f}"
                  + (f"  rate {rate_h:.2f}/h -> {left/rate_h:.1f} h chain time left" if rate_h else ""))
        if problems:
            alarms.append(f"rep {rep}: checkpoint records rejected: {problems[:3]}")
        if len(acc) < int(task.get("expected_accepted", 0)):
            alarms.append(f"rep {rep}: checkpoint holds {len(acc)} accepted but the watermark says {task['expected_accepted']}")
        if failed:
            alarms.append(f"rep {rep}: failed resample(s) in the checkpoint {sorted(failed)[:10]}")
        if len(rows) < len(acc) - 1:
            notes.append(f"rep {rep}: {len(acc) - len(rows)} accepted record(s) have no timing row (committed before the timing write)")
        if a.expect_fit_s and fvals:
            out = [f for f in fvals if f < a.expect_fit_s[0] or f > a.expect_fit_s[1]]
            if out:
                alarms.append(f"rep {rep}: {len(out)} fit(s) outside the expected range, e.g. {[round(x) for x in out[:5]]}")
        if st.get("memory_breach") or st.get("stop_reason", {}).get("memory"):
            alarms.append(f"rep {rep}: memory stop")
        if running:
            last_t = rows[-1]["t"] if rows else None
            if not acc:
                allow = ((a.expect_original_s or 0) + 2 * (a.expect_fit_s[1] if a.expect_fit_s else 0)) or a.stall_h * 3600
                if now - started > allow:
                    alarms.append(f"rep {rep}: no accepted record {((now-started)/3600):.1f} h after the job started (allowance {allow/3600:.1f} h)")
            elif last_t and now - last_t > a.stall_h * 3600:
                alarms.append(f"rep {rep}: no new record for {((now-last_t)/3600):.1f} h while running")
        # live logs: the terminal witness and HELD lines
        for lp in sorted(glob.glob(os.path.join(lr, f"live_rep{rep}.log")) + glob.glob(os.path.join(lr, "live_ctl_*.log"))):
            txt = open(lp, errors="replace").read().splitlines()
            if any(l.startswith("HELD:") for l in txt[-5:]):
                alarms.append(f"{os.path.basename(lp)}: HELD - " + next(l for l in reversed(txt) if l.startswith("HELD:"))[:120])
            if ended is not None and not any(l.startswith("exit ") for l in txt[-3:]):
                alarms.append(f"{os.path.basename(lp)}: the runner ended but the live log has no terminal 'exit' line (logger failure or truncated stream)")
            if txt:
                print(f"      {os.path.basename(lp)}: {txt[-1][:140]}")
        # the current stop request and its acknowledgment
        cur = stops.get(f"STOP_rep{rep}") or stops.get("STOP")
        if cur:
            ackp = os.path.join(lr, f"STOP_ACK_rep{rep}.json")
            ack = json.load(open(ackp)) if os.path.exists(ackp) else None
            if ack and ack.get("request_id") == cur.get("id"):
                print(f"      stop {cur.get('id')} acknowledged at boundary '{ack.get('boundary')}' by job {ack.get('job')}")
            elif running:
                last_t = rows[-1]["t"] if rows else None
                allow = (a.expect_fit_s[1] if a.expect_fit_s else a.stall_h * 3600)
                boundary_passed = last_t is not None and last_t > float(cur.get("requested", 0))
                if boundary_passed or now - float(cur.get("requested", 0)) > allow:
                    alarms.append(f"rep {rep}: stop {cur.get('id')} not acknowledged past a record boundary (old ack {ack.get('request_id') if ack else None})")
    for n in notes:
        print("\n  note:", n)
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms IN THE LOCAL CACHE (not fresh evidence)"))
    for x in alarms:
        print("   -", x)
    return 1 if alarms else 0


if __name__ == "__main__":
    sys.exit(main())
