"""Ledger row 23 (revision 3): supervision, fallback termination and terminal accounting for ONE launched attempt.
bench_launch.py starts it detached under caffeinate and refuses to leave an instance without its heartbeat; it can also
be (re)started by hand after a crash:

    python3 bench_reaper.py --run b2 --attempt 1

Every poll writes runs/<run>/reaper_attempt<n>.heartbeat. Describe/Terminate errors and timeouts are caught, logged with
backoff and retried; an empty or unattributable Describe is NOT a terminal observation (the attempt stays funded).
From launch + lifetime + 900 s it calls TerminateInstances (idempotent, project=t1 only) on every poll until it observes
the instance itself in shutting-down or terminated. That observation ends COMPUTE billing (upper bound: the poll time).
Ancillary resources are accounted separately: the attempt's tagged EBS volumes are polled until none remains (deleted
on termination; an 'available' leftover is deleted, project=t1 only), and their end time closes the ancillary hours.
Only then does it write state 'reconciled' under the run lock. It never launches anything."""
import argparse, datetime, json, os, sys, time
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
            if not found:
                log("describe returned no attributable instance: unresolved, reservation held")
            else:
                state = found[0]["State"]["Name"]
                if state in ("shutting-down", "terminated"):
                    compute_end = now; reason = found[0].get("StateTransitionReason", ""); break
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
                vols_end = now; break
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
    with L.run_lock(a.run, blocking=True):
        led = L.load(a.run)
        for x in led["attempts"]:
            if x["attempt"] == a.attempt:
                x["state"] = "reconciled"
                x["terminal"] = dict(observed_state=state, reason=reason, compute_end=compute_end, compute_s=compute_end - t0,
                                     ancillary_end=vols_end, ancillary_s=vols_end - t0, leftover_volumes=sorted(set(leftovers)),
                                     terminate_calls=terminate_calls, errors=errors)
                x["charged_usd"] = round(L.charged(x), 2)
                done = x
        L.save(a.run, led)
    log(f"attempt {a.attempt} reconciled: compute {done['terminal']['compute_s']/3600:.2f} h, ancillary {done['terminal']['ancillary_s']/3600:.2f} h, "
        f"charged USD {done['charged_usd']:.2f}; row 23 total USD {sum(L.charged(x) for x in led['attempts']):.2f} of {L.CEILING:.2f}")


if __name__ == "__main__":
    main()
