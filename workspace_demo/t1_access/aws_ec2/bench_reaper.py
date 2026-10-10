"""Ledger row 23 (revision 2): the Mac-side terminal proof and fallback stop for one benchmark attempt. Run it beside
every attempt (in the background) from the moment bench_launch.py returns.

    python3 bench_reaper.py --run b2

Polls the attempt's instance every 60 s. At launch + lifetime + 600 s, if the instance is not shutting-down or
terminated, it calls TerminateInstances (allowed only on project=t1 instances). It records the first time it OBSERVES
shutting-down or terminated as the end of billing (an upper bound) and writes the terminal accounting into
runs/<run>/attempts.json (state 'reconciled', billed seconds, charged USD at MaxPrice + ancillaries), which the launcher
uses for the cumulative USD 28 ceiling. It never launches anything."""
import argparse, datetime, json, sys, time
import bench_launch as L


def epoch(iso):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--poll-s", type=int, default=60)
    a = ap.parse_args()
    led = L.load(a.run)
    att = next((x for x in reversed(led["attempts"]) if x.get("state") == "launched"), None)
    if att is None:
        sys.exit("no launched, unreconciled attempt")
    iid, t0 = att["instance"], epoch(att["launch_time"])
    stop_at = t0 + att["lifetime_s"] + L.GRACE_S
    terminated_by_reaper = False
    while True:
        found = L.find_instances(**{"instance-id": iid})
        state = found[0]["State"]["Name"] if found else "terminated"
        now = time.time()
        if state in ("shutting-down", "terminated"):
            break
        if now >= stop_at and not terminated_by_reaper:
            L.aws("ec2", "terminate-instances", "--instance-ids", iid)
            terminated_by_reaper = True
            print(f"{time.strftime('%FT%TZ', time.gmtime())} lifetime exceeded: TerminateInstances {iid}", flush=True)
        time.sleep(a.poll_s)
    billed = now - t0
    reason = found[0].get("StateTransitionReason", "") if found else ""
    led = L.load(a.run)
    for x in led["attempts"]:
        if x["attempt"] == att["attempt"]:
            x["state"] = "reconciled"
            x["terminal"] = dict(observed_state=state, observed_at=now, billed_s=billed, reason=reason,
                                 terminated_by_reaper=terminated_by_reaper, charged_usd=round(L.worst_usd(billed), 2))
    L.save(a.run, led)
    print(f"attempt {att['attempt']} {iid}: {state} observed {time.strftime('%FT%TZ', time.gmtime(now))}, billed <= {billed/3600:.2f} h, "
          f"charged USD {L.worst_usd(billed):.2f}; row 23 total USD {sum(L.charged(x) for x in led['attempts']):.2f} of {L.CEILING:.2f}")


if __name__ == "__main__":
    main()
