"""Ledger row 23 (revision 3): supervision, fallback termination and terminal accounting for ONE launched attempt.
bench_launch.py starts it detached under caffeinate and refuses to leave an instance without its heartbeat; it can also
be (re)started by hand after a crash:

    python3 bench_reaper.py --run b2 --attempt 1

Every poll writes runs/<run>/reaper_attempt<n>.heartbeat. Describe/Terminate errors and timeouts are caught, logged with
backoff and retried; an empty or unattributable Describe is NOT a terminal observation (the attempt stays funded).
From launch + lifetime + 900 s (the launcher also budgets a further 1,800 s reserve for polling, API retries
and cleanup) it calls TerminateInstances (idempotent, project=t1 only) on every poll until it observes
the instance itself in shutting-down or terminated. That observation ends COMPUTE billing (upper bound: the poll time).
Ancillary resources are accounted separately: the attempt's tagged EBS volumes are polled until none remains (deleted
on termination; an 'available' leftover is deleted, project=t1 only), and their end time closes the ancillary hours.
Only then does it write state 'reconciled' under the run lock. It never launches anything.

REVISION 4 (Codex RSC 299f4b7 R2-1): for a production or qualification run (prod-*, qual-*) the reconciliation is written
under the global authority lock as well (taken first, the launcher's order) and a new inventory generation is sealed at
once, so the reconciled view is installable; a benchmark run is unchanged."""
import argparse, contextlib, datetime, json, os, sys, time
import bench_launch as L


def epoch(iso):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def log(msg):
    print(f"{time.strftime('%FT%TZ', time.gmtime())} {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--attempt", type=int, required=True)
    ap.add_argument("--poll-s", type=int, default=60)
    a = ap.parse_args()
    att = next((x for x in L.load(a.run)["attempts"] if x["attempt"] == a.attempt), None)
    if att is None or att.get("state") != "launched":
        sys.exit(f"attempt {a.attempt} is {None if att is None else att.get('state')}, not launched")
    iid, t0 = att["instance"], epoch(att["launch_time"])
    stop_at = t0 + att["lifetime_s"] + L.GRACE_S
    hb = os.path.join(L.run_dir(a.run), f"reaper_attempt{a.attempt}.heartbeat")
    errors, terminate_calls, compute_end, state = [], 0, None, "unknown"
    log(f"supervising {iid}: launch {att['launch_time']}, fallback terminate from {time.strftime('%FT%TZ', time.gmtime(stop_at))}")
    while compute_end is None:
        now = time.time()
        try:
            found = [i for i in L.find_instances(**{"instance-id": iid}) if i.get("InstanceId") == iid]
            t_resp = time.time()                       # stamped AFTER the response: an upper bound on the state's onset
            if not found:
                log("describe returned no attributable instance: unresolved, reservation held")
            else:
                state = found[0]["State"]["Name"]
                if state in ("shutting-down", "terminated"):
                    compute_end = t_resp; reason = found[0].get("StateTransitionReason", ""); break
        except Exception as e:
            errors.append(dict(at=now, op="describe", error=str(e)[:300])); log(f"describe error: {e}")
        if now >= stop_at:
            try:
                L.aws("ec2", "terminate-instances", "--instance-ids", iid); terminate_calls += 1
                log(f"lifetime exceeded: TerminateInstances {iid} (call {terminate_calls})")
            except Exception as e:
                errors.append(dict(at=now, op="terminate", error=str(e)[:300])); log(f"terminate error: {e}")
        open(hb, "w").write(json.dumps(dict(at=now, state=state, errors=len(errors), terminate_calls=terminate_calls)))
        time.sleep(a.poll_s if not errors or now - errors[-1]["at"] > 300 else min(300, a.poll_s * 2))
    log(f"{iid} observed {state} at {time.strftime('%FT%TZ', time.gmtime(compute_end))} ({reason})")
    vols_end, leftovers = None, []
    while vols_end is None:
        now = time.time()
        try:
            out = json.loads(L.aws("ec2", "describe-volumes", "--filters", f"Name=tag:run,Values={a.run}",
                                   f"Name=tag:attempt,Values={a.attempt}", "--output", "json").stdout)
            vols = [(v["VolumeId"], v["State"]) for v in out["Volumes"]]
            if not vols:
                vols_end = time.time(); break          # after the response that shows no volume left
            for vid, st in vols:
                if st == "available":
                    leftovers.append(vid)
                    try:
                        L.aws("ec2", "delete-volume", "--volume-id", vid); log(f"deleted leftover volume {vid}")
                    except Exception as e:
                        errors.append(dict(at=now, op="delete-volume", error=str(e)[:300])); log(f"delete-volume error: {e}")
        except Exception as e:
            errors.append(dict(at=now, op="describe-volumes", error=str(e)[:300])); log(f"describe-volumes error: {e}")
        open(hb, "w").write(json.dumps(dict(at=now, state=state, volumes="waiting", errors=len(errors))))
        time.sleep(a.poll_s)
    paid = a.run.startswith(("prod-", "qual-"))
    with (authority(a.run) if paid else contextlib.nullcontext()), L.run_lock(a.run, blocking=True):
        led = L.load(a.run)
        for x in led["attempts"]:
            if x["attempt"] == a.attempt:
                x["state"] = "reconciled"
                x["terminal"] = dict(observed_state=state, reason=reason, compute_end=compute_end, compute_s=compute_end - t0,
                                     ancillary_end=vols_end, ancillary_s=vols_end - t0, leftover_volumes=sorted(set(leftovers)),
                                     terminate_calls=terminate_calls, errors=errors)
                x["charged_usd"] = round(report_charge(x), 2)
                done = x
        L.save(a.run, led)
        if paid:
            import prod_authority as PA
            log(f"inventory sealed: {PA.write_inventory()}")
    total = sum(report_charge(x) for x in led["attempts"])
    tail = (f"row 23 total USD {total:.2f} of {L.CEILING:.2f}" if not any("anc_h" in x for x in led["attempts"])
            else f"run {a.run} total USD {total:.2f} (production/qualification rates; the global authority recomputes every envelope)")
    log(f"attempt {a.attempt} reconciled: compute {done['terminal']['compute_s']/3600:.2f} h, ancillary {done['terminal']['ancillary_s']/3600:.2f} h, "
        f"charged USD {done['charged_usd']:.2f}; {tail}")


@contextlib.contextmanager
def authority(run):
    """The global authority lock for a production/qualification reconciliation (waits; logs while waiting)."""
    import prod_authority as PA
    while True:
        cm = PA.authority_lock(wait_s=600)
        try:
            cm.__enter__(); break
        except BlockingIOError:
            log(f"{run}: waiting for the authority lock to record the reconciliation")
    try:
        yield
    finally:
        cm.__exit__(None, None, None)


def report_charge(x):
    """The charge REPORTED for one attempt (Codex 3dc0daf R1-7): a production/qualification attempt (it records its own
    ancillary rate `anc_h` and fixed `s3_fixed`) at those rates and its own cap; a benchmark attempt by the reviewed row-23
    rule. Reporting only - prod_authority recomputes every envelope independently."""
    if "anc_h" not in x:
        return L.charged(x)
    if x.get("state") == "rejected":
        return 0.0
    if x.get("state") == "reconciled":
        t = x["terminal"]
        return (t["compute_s"] / 3600) * x["max_price"] + (t["ancillary_s"] / 3600) * x["anc_h"] + x["s3_fixed"]
    return ((x["lifetime_s"] + L.GRACE_S + L.RESERVE_S) / 3600) * (x["max_price"] + x["anc_h"]) + x["s3_fixed"]


if __name__ == "__main__":
    main()
