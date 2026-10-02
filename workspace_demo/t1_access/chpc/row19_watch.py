"""Ledger row 19: read the qualification slice LIVE from the Mac (owner, 2 Oct: "evaluate as the results come in";
Codex 523249d G; e44f804 R4/R5; 6d8a597 R4: the full record contract, a per-job progress baseline, attributed terminal
and logger evidence, the externally killed C2 exempt from a normal terminal line).

Every poll pulls a FRESH snapshot into its own staging directory (never merged into an older copy), then rotates it
into `results/row19_slice/live/` and keeps the previous snapshot under `archive/`. A failed or partial pull is an
ALARM, never a green. The expected evidence is derived from the campaign ledger (every reservation, its job id and its
state) - not from whatever files happen to exist: a live job must publish its task binding within the start-up
allowance, then its first accepted record within the original-fit allowance measured from THIS job's start (older
jobs' timing rows never anchor a running job's clock); accepted, failed and non-finite records are counted from
records that pass the comparator's complete contract (checksum, identity, seed, B, the identity's draw, every
predictor and band finite unless failed with a string reason, finite fit seconds); timing rows are cross-checked by
index against accepted records. Every ENDED entry must show its own attributed terminal evidence: its role's live log
present, a terminal line naming its job id, and a logger status of 0 - an absent log, an old attempt's line, a
missing or non-zero logger status are alarms; the externally killed C2 is exempt from the normal terminal line and
is judged by its interruption record instead. --qstat asks the login node for every bound job's state; a failed
observation or an absent id is named and alarmed (unknown is not green). Nothing scientific is displayed or
interpreted: a status file's result/interval and the records' stats are loaded and dropped.

    python chpc/row19_watch.py --manifest chpc/row19_slice_manifest.json [--expect-original-s S] [--expect-fit-s LO HI]
                               [--startup-allowance-s 900] [--stall-h 4] [--qstat] [--no-pull]
Exit 1 on any alarm (R052 then submits nothing further until it is diagnosed); 0 only on fresh evidence with no alarm.
Poll cadence: every 2 hours while any reservation is live.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from row19_control_compare import expected_contract, validate_record

HOST = "chpc-scp"
LOGIN = "lengau"
LIVE_DIR = os.path.join(HERE, "results", "row19_slice", "live")
ARCHIVE_DIR = os.path.join(HERE, "results", "row19_slice", "archive")
NEVER_SHOWN = ("result", "interval", "stats")
LIVE_STATES = ("reserved", "bound", "live")
TERMINAL = re.compile(r"^exit (?P<rc>\d+) tee (?P<tee>\d*) job (?P<job>\S+) end \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def sh(cmd, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 255, "", str(e)


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
    """{job_id: state} from one `qstat -xf` on the login node; 'gone' for an id the scheduler no longer lists; None on failure."""
    if not job_ids:
        return {}
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", LOGIN, "qstat -xf " + " ".join(job_ids) + " 2>&1"])
    if rc != 0 and not out:
        return None
    states, cur = {}, None
    for line in out.splitlines():
        if line.startswith("Job Id:"):
            cur = line.split(":", 1)[1].strip()
        elif cur and line.strip().startswith("job_state ="):
            states[cur] = line.split("=", 1)[1].strip()
    return {j: states.get(j, "gone") for j in job_ids}


def checkpoint_metadata(path, ex, target):
    """Accepted indices, failed indices, fit seconds and problems from records passing the COMPLETE contract; stats dropped."""
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
        why = validate_record(d, ex, target)
        if why:
            problems.append(f"line {i+1}: {why}"); continue
        r = d["rep"]
        if r in acc:
            problems.append(f"line {i+1}: index {r} twice"); continue
        acc.add(r); fits[r] = float(d["fit_seconds"])
        if d["failed"]:
            failed.add(r)
    return acc, failed, fits, problems, tail


def kill_receipt_ok(it, e):
    """(known_kill, problem): the typed, bound native kill evidence a C2 exemption needs - the entry's job id, pbs_killed exactly
    True, a non-bool non-zero integer exit, a finite positive requested walltime equal to the reservation's, a finite used
    walltime supporting a walltime kill."""
    if not isinstance(it, dict):
        return False, "not an object"
    if it.get("job_id") != e.get("job_id"):
        return False, "names another job"
    if it.get("pbs_killed") is not True:
        return False, "pbs_killed is not exactly true"
    x = it.get("exit_status")
    if isinstance(x, bool) or not isinstance(x, int) or x == 0:
        return False, "exit status is not a non-zero integer"
    wr, wu = it.get("walltime_requested_s"), it.get("walltime_used_s")
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    if not (num(wr) and wr > 0 and abs(wr - float(e.get("walltime_s", -1))) <= 1.0):
        return False, "requested walltime is not the reservation's"
    if not (num(wu) and wu >= wr):
        return False, "used walltime does not support a walltime kill"
    return True, None


def expected_log(lr, e):
    """The live log an entry must have written: main -> live_rep<N>.log; a control -> live_ctl_<kind>.log."""
    return os.path.join(lr, f"live_rep{e['rep']}.log" if e["kind"] == "main" else f"live_ctl_{e['kind']}.log")


def terminal_evidence(lp, job_id):
    """(found, rc, tee) for the terminal line attributed to THIS job id in a live log; found False when absent."""
    if not os.path.exists(lp):
        return False, None, None
    for line in reversed(open(lp, errors="replace").read().splitlines()):
        m = TERMINAL.match(line)
        if m and m.group("job") == job_id:
            return True, m.group("rc"), m.group("tee")
    return False, None, None


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
    contracts = {}
    for e in entries:
        if e.get("state") not in LIVE_STATES and not (e.get("state") == "settled" and not str(e.get("settle_note", "")).strip()):
            continue
        root = e["root"]; rep = e.get("rep"); lr = os.path.join(LIVE_DIR, os.path.basename(root.rstrip("/")))
        q = (qs or {}).get(e.get("job_id")) if qs is not None else ("-" if not a.qstat else "unknown")
        started = e.get("runner_started"); ended = e.get("runner_exit")
        killed_c2, kill_problem = False, None
        if e["kind"] == "c2" and e.get("job_id") and os.path.exists(os.path.join(lr, "c2_interruption.json")):
            killed_c2, kill_problem = kill_receipt_ok(json.load(open(os.path.join(lr, "c2_interruption.json"))), e)
            if kill_problem:
                alarms.append(f"c2 job {e.get('job_id')}: interruption record incomplete or contradictory ({kill_problem}); not treated as a known kill")
        phase = "settled" if e["state"] == "settled" else "killed by PBS (known)" if killed_c2 else "ended" if ended is not None else "running" if started else "queued/not started"
        print(f"\n  {e['kind']:<6} rep {rep} attempt {e['attempt']} {e['state']:<8} job {e.get('job_id')} PBS {q}  {phase}  "
              f"{e['reserved_core_h']:.0f} core-h reserved, runner exit {ended}")
        if e["state"] in ("live", "settled") and ended == 4:
            alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: HELD (exit 4) - diagnose before any resubmission")
        if a.qstat and e.get("job_id") and q in ("gone", "F", "E") and ended is None and e["kind"] != "c2":
            alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: PBS says {q} but the runner never ended - killed or crashed; keep the reservation")
        if a.qstat and e.get("job_id") and q == "unknown":
            alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: PBS state unknown")
        if e["kind"] == "stage0" or rep is None:
            continue
        # terminal and logger evidence, attributed to this job
        if ended is not None:
            lp = expected_log(lr, e)
            found, rc, tee = terminal_evidence(lp, e.get("job_id") or "")
            if not os.path.exists(lp):
                alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: ended but its live log {os.path.basename(lp)} is absent")
            elif not found:
                alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: ended but no terminal line names this job in {os.path.basename(lp)} (truncated stream or an old attempt's line)")
            else:
                if rc != str(ended):
                    alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: terminal line exit {rc} differs from the ledger's runner exit {ended}")
                if tee != "0":
                    alarms.append(f"{e['kind']} rep {rep} job {e.get('job_id')}: logger status {tee!r} (tee failed or unknown): the live log is not a complete observation")
        elif killed_c2:
            notes.append(f"c2 job {e.get('job_id')}: externally killed by design (interruption record present); judged by c2_interruption.json, "
                         f"not by a terminal line; its reservation stays charged until the operator settles it")
        tp = os.path.join(lr, f"task_{rep}.json")
        if not os.path.exists(tp):
            if killed_c2:
                print(f"    no task binding ({phase}; the interruption record is the evidence)"); continue
            if started and ended is None and now - started > a.startup_allowance_s:
                alarms.append(f"{e['kind']} rep {rep}: live for {(now-started)/60:.0f} min without a task binding (allowance {a.startup_allowance_s/60:.0f} min)")
            elif started and ended is not None:
                alarms.append(f"{e['kind']} rep {rep}: the runner ended (exit {ended}) without a task binding")
            else:
                print(f"    no task binding yet ({phase})")
            continue
        task = json.load(open(tp)); b = task["binding"]
        key = (root, rep)
        if key not in contracts:
            try:
                contracts[key] = (expected_contract(a.manifest, b), "")
            except Exception as ex_:
                contracts[key] = (None, str(ex_))
        ex, why = contracts[key]
        if ex is None:
            alarms.append(f"rep {rep}: task binding is not this manifest's ({why})"); continue
        target = ex["n_rep"] if b.get("until") is None else int(b["until"])
        ck = os.path.join(lr, "ckpt", os.path.basename(b["ckpt"]))
        acc, failed, fits, problems, tail = checkpoint_metadata(ck, ex, ex["n_rep"])
        rows_raw = [json.loads(l) for l in open(os.path.join(lr, f"timing_{rep}.jsonl")).read().splitlines() if l.strip()] if os.path.exists(os.path.join(lr, f"timing_{rep}.jsonl")) else []
        rows = [r for r in rows_raw if isinstance(r.get("t"), (int, float)) and not isinstance(r.get("t"), bool) and math.isfinite(r["t"])
                and isinstance(r.get("rep"), int) and isinstance(r.get("fit_seconds"), (int, float)) and math.isfinite(r["fit_seconds"])]
        if len(rows) != len(rows_raw):
            alarms.append(f"rep {rep}: {len(rows_raw) - len(rows)} timing row(s) with non-finite or mistyped fields (not used for health)")
        mine = [r for r in rows if r.get("job") == e.get("job_id")]
        sp = os.path.join(lr, f"status_{rep}.json")
        st = {}
        if os.path.exists(sp):
            st = json.load(open(sp))
            for k in NEVER_SHOWN:
                st.pop(k, None)
        running = e["state"] == "live" and ended is None and not killed_c2
        fvals = sorted(v for r, v in fits.items() if r not in failed)
        rate_h = None
        if len(mine) >= 2 and mine[-1]["t"] > mine[0]["t"]:
            rate_h = (len(mine) - 1) / (mine[-1]["t"] - mine[0]["t"]) * 3600
        left = max(0, target - len(acc))
        print(f"    dataset rep {rep}: accepted {len(acc)}/{target} from strict checkpoint records, failed {len(failed)}, timing rows {len(rows)} "
              f"({len(mine)} this job), watermark {task.get('expected_accepted')}, status phase {st.get('phase', 'none yet')}")
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
        foreign_rows = [r.get("rep") for r in rows if r.get("rep") not in acc]
        if foreign_rows:
            alarms.append(f"rep {rep}: timing rows name indices with no accepted record {foreign_rows[:5]}")
        if len(rows) < len(acc) - 1:
            notes.append(f"rep {rep}: {len(acc) - len(rows)} accepted record(s) have no timing row (committed before the timing write)")
        if a.expect_fit_s and fvals:
            out = [f for f in fvals if f < a.expect_fit_s[0] or f > a.expect_fit_s[1]]
            if out:
                alarms.append(f"rep {rep}: {len(out)} fit(s) outside the expected range, e.g. {[round(x) for x in out[:5]]}")
        if st.get("memory_breach") or st.get("stop_reason", {}).get("memory"):
            alarms.append(f"rep {rep}: memory stop")
        if running:
            # the progress baseline is THIS job's start, moved forward only by this job's own validated timing rows
            baseline = max([started] + [r["t"] for r in mine if r.get("rep") in acc])
            allow_first = ((a.expect_original_s or 0) + 2 * (a.expect_fit_s[1] if a.expect_fit_s else 0)) or a.stall_h * 3600
            if not mine and now - baseline > allow_first:
                alarms.append(f"rep {rep}: no record from this job {((now-baseline)/3600):.1f} h after it started "
                              f"({len(acc)} restored record(s) do not count; allowance {allow_first/3600:.1f} h)")
            elif mine and now - baseline > a.stall_h * 3600:
                alarms.append(f"rep {rep}: no new record for {((now-baseline)/3600):.1f} h while running")
        cur = stops.get(f"STOP_rep{rep}") or stops.get("STOP")
        if cur:
            ackp = os.path.join(lr, f"STOP_ACK_rep{rep}.json")
            ack = json.load(open(ackp)) if os.path.exists(ackp) else None
            if ack and ack.get("request_id") == cur.get("id"):
                print(f"      stop {cur.get('id')} acknowledged at boundary '{ack.get('boundary')}' by job {ack.get('job')}")
            elif running:
                last_t = mine[-1]["t"] if mine else None
                allow = (a.expect_fit_s[1] if a.expect_fit_s else a.stall_h * 3600)
                boundary_passed = last_t is not None and last_t > float(cur.get("requested", 0))
                if boundary_passed or now - float(cur.get("requested", 0)) > allow:
                    alarms.append(f"rep {rep}: stop {cur.get('id')} not acknowledged past a record boundary (old ack {ack.get('request_id') if ack else None})")
        for lp in sorted(glob.glob(os.path.join(lr, f"live_rep{rep}.log")) + glob.glob(os.path.join(lr, "live_ctl_*.log"))):
            txt = open(lp, errors="replace").read().splitlines()
            if any(l.startswith("HELD:") for l in txt[-5:]):
                alarms.append(f"{os.path.basename(lp)}: HELD - " + next(l for l in reversed(txt) if l.startswith("HELD:"))[:120])
            if txt:
                print(f"      {os.path.basename(lp)}: {txt[-1][:140]}")
    for n in notes:
        print("\n  note:", n)
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms IN THE LOCAL CACHE (not fresh evidence)"))
    for x in alarms:
        print("   -", x)
    return 1 if alarms else 0


if __name__ == "__main__":
    sys.exit(main())
