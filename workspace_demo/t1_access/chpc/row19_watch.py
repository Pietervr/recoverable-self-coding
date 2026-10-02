"""Ledger row 19: read the qualification slice LIVE from the Mac (owner, 2 Oct: "evaluate as the results come in";
Codex 523249d, launch condition G: no false green, a first-record timeout, HELD and transfer alarms, progress from
validated checkpoint state, an acknowledged stop boundary).

What it reads, over the sanctioned transfer node: the campaign ledger (every reservation and its PBS binding), each
root's task bindings, status files, timing lines, checkpoint files and live logs; optionally the PBS queue state of
every bound job (--qstat, one ssh to the login node). What it prints: per bound job and dataset, the queue state,
the phase, resamples ACCEPTED (counted from the checkpoint's validated records, never from timing rows alone), the
rate, the projected chain time left, the original fit, utilisation, peak memory, and the ledger totals. What it never
prints or interprets: a status file's `result` and `interval` entries and the records' statistics (they are loaded
by json and dropped; see NEVER_SHOWN).

ALARMS (exit 1; the operator, R052, submits nothing further until each is diagnosed): a failed or partial pull; a
bound job whose files are missing or stale; no accepted record within the first-record allowance after a job
started (original fit + 2 resamples at the declared expectation); no new record for --stall-h hours while a job is
running; a HELD exit or a HELD line in a live log; a rejected or conflicting checkpoint record; a failed resample;
a fit outside --expect-fit-s LO HI (must be finite and ordered); a memory stop; the ledger absent or over its cap;
a stop request without its acknowledgment past the next record boundary.

    python chpc/row19_watch.py --manifest chpc/row19_slice_manifest.json [--expect-original-s S] [--expect-fit-s LO HI]
                               [--stall-h 4] [--qstat] [--no-pull]
Poll cadence: every 2 hours while any reservation is live (the operator runs it; it is read-only on Lustre).
"""
import argparse, glob, json, os, subprocess, sys, time, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = "chpc-scp"
LOGIN = "lengau"
NEVER_SHOWN = ("result", "interval", "stats")
LIVE_STATES = ("reserved", "bound", "live")


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def pull_tree(remote, local):
    """scp -r of one remote directory; returns (ok, message)."""
    os.makedirs(local, exist_ok=True)
    rc, out, err = sh(["scp", "-q", "-r", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{remote}/.", local])
    return rc == 0, err.strip()[:200]


def record_sha(rec):
    return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != "sha"}, sort_keys=True, default=float).encode()).hexdigest()


def checkpoint_progress(path, ident, n_rep):
    """Accepted indices (checksum, identity and B verified) and problems; statistics are never retained."""
    acc, problems = set(), []
    if not os.path.exists(path):
        return acc, problems, False
    tail = False
    with open(path) as fh:
        lines = fh.read().split("\n")
    if lines and lines[-1].strip():
        tail = True
    for i, line in enumerate(l for l in lines if l.strip()):
        try:
            d = json.loads(line)
        except Exception:
            if tail and i == len([l for l in lines if l.strip()]) - 1:
                continue
            problems.append(f"line {i+1}: not JSON"); continue
        if record_sha(d) != d.get("sha") or d.get("ident") != ident or int(d.get("n_rep", -1)) != int(n_rep):
            problems.append(f"line {i+1}: checksum/identity/B rejected"); continue
        if d["rep"] in acc:
            problems.append(f"line {i+1}: index {d['rep']} twice"); continue
        acc.add(int(d["rep"]))
    return acc, problems, tail


def qstat_states(job_ids):
    if not job_ids:
        return {}
    rc, out, _ = sh(["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", LOGIN, "qstat -x " + " ".join(job_ids) + " 2>&1"])
    st = {}
    for line in out.splitlines():
        parts = line.split()
        if parts and parts[0] in job_ids or (parts and any(parts[0].startswith(j.split('.')[0]) for j in job_ids)):
            key = next((j for j in job_ids if parts[0].startswith(j.split('.')[0])), parts[0])
            st[key] = parts[-2] if len(parts) >= 2 else "?"
    return st


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "row19_slice_manifest.json"))
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--qstat", action="store_true", help="also ask the login node for every bound job's queue state")
    ap.add_argument("--expect-original-s", type=float, default=None, help="expected original-fit seconds (from stage 0)")
    ap.add_argument("--expect-fit-s", nargs=2, type=float, default=None)
    ap.add_argument("--stall-h", type=float, default=4.0)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest))
    campaign = man["storage"]["campaign"]
    local = os.path.join(HERE, "results", "row19_slice", "live")
    now = time.time()
    alarms, notes = [], []
    if a.expect_fit_s is not None:
        lo, hi = a.expect_fit_s
        if not (lo >= 0 and hi > lo and all(x == x and x != float("inf") for x in (lo, hi))):
            print("--expect-fit-s must be finite and ordered"); return 1
    # 1. the campaign ledger, fresh
    cl = os.path.join(local, "campaign")
    if not a.no_pull:
        ok, msg = pull_tree(campaign, cl)
        if not ok:
            alarms.append(f"pull of the campaign ledger failed: {msg}")
    led_path = os.path.join(cl, "budget.json")
    if not os.path.exists(led_path):
        alarms.append("campaign ledger absent (no reservation has ever been made, or the pull failed)")
        led = dict(cap_core_h=None, entries={})
    else:
        led = json.load(open(led_path))
    entries = sorted(led["entries"].values(), key=lambda e: e["created"])
    spent = sum(float(e.get("settled_core_h", 0.0)) for e in entries if e.get("state") == "settled")
    live = sum(float(e.get("reserved_core_h", 0.0)) for e in entries if e.get("state") in LIVE_STATES)
    cap = led.get("cap_core_h")
    print(f"ROW 19 CAMPAIGN, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}")
    print(f"  ledger: cap {cap}  spent {spent:.1f}  live reserved {live:.1f}  entries {len(entries)}  (file {'fresh' if not a.no_pull else 'LOCAL CACHE'})")
    if cap and spent + live > float(cap) + 1e-9:
        alarms.append("ledger: spent + live reserved exceeds the cap")
    stops = [f for f in glob.glob(os.path.join(cl, "STOP*"))]
    if stops:
        notes.append("stop request(s) present: " + ", ".join(os.path.basename(s) for s in stops))
    # 2. every root with a live or bound reservation
    roots = sorted({e["root"] for e in entries if e.get("state") in LIVE_STATES or e.get("state") == "settled"})
    qs = qstat_states([e["job_id"] for e in entries if e.get("job_id") and e.get("state") in ("bound", "live")]) if a.qstat else {}
    for root in roots:
        lr = os.path.join(local, os.path.basename(root.rstrip("/")))
        if not a.no_pull:
            ok, msg = pull_tree(root, lr)
            if not ok:
                alarms.append(f"pull of {root} failed or partial: {msg}")
        print(f"\n  root {root}")
        root_entries = [e for e in entries if e.get("root") == root]
        for e in root_entries:
            q = qs.get(e.get("job_id"), "-") if qs else "-"
            age_h = (now - e.get("runner_started", e.get("created", now))) / 3600
            print(f"    {e['kind']:<6} rep {e.get('rep')} attempt {e['attempt']} {e['state']:<8} job {e.get('job_id')} queue {q}  "
                  f"{e['reserved_core_h']:.0f} core-h reserved, runner exit {e.get('runner_exit')}")
            if e.get("state") == "live" and e.get("runner_exit") == 4:
                alarms.append(f"{e['kind']} rep {e.get('rep')} job {e.get('job_id')}: HELD (exit 4) - diagnose before any resubmission")
            if e.get("state") == "live" and e.get("runner_exit") is None and age_h > 0 and q in ("F", "E", "gone"):
                alarms.append(f"{e['kind']} rep {e.get('rep')} job {e.get('job_id')}: job finished in PBS without a runner end - killed or crashed; keep its reservation")
        for tp in sorted(glob.glob(os.path.join(lr, "task_*.json"))):
            task = json.load(open(tp)); b = task["binding"]; rep = b["rep"]
            ck = os.path.join(lr, "ckpt", os.path.basename(b["ckpt"]))
            acc, problems, tail = checkpoint_progress(ck, b["ident"], b["n_rep"])
            target = b["n_rep"] if b.get("until") is None else int(b["until"])
            rows = [json.loads(l) for l in open(os.path.join(lr, f"timing_{rep}.jsonl")).read().splitlines() if l.strip()] if os.path.exists(os.path.join(lr, f"timing_{rep}.jsonl")) else []
            sp = os.path.join(lr, f"status_{rep}.json")
            st = {}
            if os.path.exists(sp):
                st = json.load(open(sp))
                for k in NEVER_SHOWN:
                    st.pop(k, None)
            live_e = [e for e in root_entries if e.get("rep") == rep and e.get("state") == "live" and e.get("runner_exit") is None]
            running = bool(live_e)
            fits = [float(r["fit_seconds"]) for r in rows if not r.get("failed")]
            rate_h = None
            if len(rows) >= 2 and rows[-1]["t"] > rows[0]["t"]:
                rate_h = (len(rows) - 1) / (rows[-1]["t"] - rows[0]["t"]) * 3600
            left = max(0, target - len(acc))
            print(f"    dataset rep {rep}: accepted {len(acc)}/{target} (checkpoint-validated), timing rows {len(rows)}, "
                  f"phase {st.get('phase', 'running' if running else 'no status yet')}, running={running}")
            if st:
                print(f"      last job {st.get('job')}: exit {st.get('exit')} new {st.get('n_new')} resumed {st.get('n_resumed')} "
                      f"tail-repaired {st.get('n_tail_repaired')} damaged {st.get('n_damaged')} partial={st.get('partial')} "
                      f"target_complete={st.get('target_complete')} stop={st.get('stopped_by_request')} "
                      f"original {st.get('original_seconds', 0):.0f} s cached={st.get('original_cached')} "
                      f"util {st.get('utilisation', 0):.2f} maxrss {st.get('maxrss_bytes', 0)/2**30:.2f} GiB")
            if fits:
                fs = sorted(fits)
                print(f"      fit s: n {len(fs)} min {fs[0]:.0f} median {fs[len(fs)//2]:.0f} max {fs[-1]:.0f}"
                      + (f"  rate {rate_h:.2f}/h -> {left/rate_h:.1f} h chain time left" if rate_h else ""))
            if problems:
                alarms.append(f"rep {rep}: checkpoint records rejected: {problems[:3]}")
            if len(acc) < int(task.get("expected_accepted", 0)):
                alarms.append(f"rep {rep}: checkpoint holds {len(acc)} accepted but {task['expected_accepted']} were committed")
            if any(r.get("failed") for r in rows):
                alarms.append(f"rep {rep}: failed resample(s) {[r['rep'] for r in rows if r.get('failed')][:10]}")
            if a.expect_fit_s and fits:
                out = [f for f in fits if f < a.expect_fit_s[0] or f > a.expect_fit_s[1]]
                if out:
                    alarms.append(f"rep {rep}: {len(out)} fit(s) outside the expected range, e.g. {[round(x) for x in out[:5]]}")
            if st.get("stop_reason", {}).get("memory"):
                alarms.append(f"rep {rep}: memory stop")
            if running:
                started = live_e[0].get("runner_started", now)
                last_t = rows[-1]["t"] if rows else None
                if not rows:
                    allow = (a.expect_original_s or 0) + 2 * (a.expect_fit_s[1] if a.expect_fit_s else 0) if (a.expect_original_s or a.expect_fit_s) else a.stall_h * 3600
                    if now - started > allow:
                        alarms.append(f"rep {rep}: no accepted record {((now-started)/3600):.1f} h after the job started (allowance {allow/3600:.1f} h)")
                elif now - last_t > a.stall_h * 3600:
                    alarms.append(f"rep {rep}: no new record for {((now-last_t)/3600):.1f} h while running")
            for lp in glob.glob(os.path.join(lr, f"live_rep{rep}.log")) + glob.glob(os.path.join(lr, "live_ctl_*.log")):
                txt = open(lp, errors="replace").read().splitlines()
                if any(l.startswith("HELD:") for l in txt[-5:]):
                    alarms.append(f"{os.path.basename(lp)}: HELD - " + next(l for l in reversed(txt) if l.startswith("HELD:"))[:120])
                if txt:
                    print(f"      {os.path.basename(lp)}: {txt[-1][:140]}")
            ack = os.path.join(lr, f"STOP_ACK_rep{rep}.json")
            if stops and running and not os.path.exists(ack) and rows and now - rows[-1]["t"] > (a.expect_fit_s[1] if a.expect_fit_s else a.stall_h * 3600):
                alarms.append(f"rep {rep}: stop requested but not acknowledged past a record boundary")
    for n in notes:
        print("\n  note:", n)
    print("\n  ALARMS:" if alarms else "\n  no alarms (fresh evidence)" if not a.no_pull else "\n  no alarms IN THE LOCAL CACHE (not fresh evidence)")
    for x in alarms:
        print("   -", x)
    return 1 if alarms else 0


if __name__ == "__main__":
    sys.exit(main())
