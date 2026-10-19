"""The qualification cutover (Codex cf07869 D-2): the ONLY way to set qualification.permitted in ec2_release_state.json.

    python3 aws_ec2/qual_permit.py --record <reviewed qualification-permission record, path relative to aws_ec2/> [--wait-s 600]

  1. take runs/.bench_inflight.lock EXCLUSIVELY (bench_launch.inflight): this waits until every in-flight benchmark
     admission/recovery command - including one still waiting or staging before its first journal entry - has ended, and
     no new one can start meanwhile (a drain, not an inference from ledger intents); give up after --wait-s and change nothing
  2. write runs/BENCH_FENCE.json once (never overwritten): from now on every benchmark command refuses at entry AND
     immediately before every RunInstances issue/retry/recovery re-issue (bench_launch.cutover_problem)
  3. set qualification.permitted with the record's path and sha256 - only when row 23 is declared (backed) and the owner
     accepted the ceilings; prod_authority.release_state() also requires the fence before qualification is ok.
The running row-23 attempt-5 reaper is not a benchmark command (it never issues RunInstances) and is not affected; Q1/Q2
admission separately refuses while any benchmark attempt is live (prod_authority.exclusion_problem).
Exit 0 permitted (or already permitted with this record), 3 refused (nothing changed after step 1 fails)."""
import argparse, fcntl, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bench_launch as L
import prod_authority as PA


def permit(record_rel, wait_s=600, log=print):
    rp = os.path.join(L.HERE, record_rel)
    if not os.path.exists(rp):
        log(f"REFUSED: the qualification-permission record {record_rel} does not exist"); return 3
    rel = PA.release_state()
    if not rel["row23"]["ok"]:
        log("REFUSED: row 23 is not declared successful with a backed report"); return 3
    if not rel["qualification"].get("owner_accepted_ceilings"):
        log("REFUSED: the owner has not accepted the qualification ceilings"); return 3
    os.makedirs(os.path.dirname(L.inflight_path()), exist_ok=True)
    fh = open(L.inflight_path(), "a+"); t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); break
        except BlockingIOError:
            if time.time() - t0 >= wait_s:
                fh.close(); log(f"REFUSED: benchmark commands still in flight after {wait_s} s - nothing changed"); return 3
            time.sleep(1)
    try:
        fp = L.fence_path()
        if not os.path.exists(fp):
            fd = os.open(fp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
            with os.fdopen(fd, "w") as f:
                json.dump(dict(schema="t1-bench-fence-1", at=time.time(), record=record_rel,
                               note="qualification cutover: benchmark admissions/recoveries frozen (Codex cf07869 D-2)"), f, indent=1)
                f.flush(); os.fsync(f.fileno())
        log(f"fence set: {fp}")
        r = json.load(open(PA.RELEASE_STATE)); q = r["qualification"]
        q.update(permitted=True, record_path=record_rel, record_sha256=L.sha256(rp))
        tmp = PA.RELEASE_STATE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(r, f, indent=1); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, PA.RELEASE_STATE)
        log("qualification permitted in ec2_release_state.json")
        return 0
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--record", required=True); ap.add_argument("--wait-s", type=float, default=600)
    a = ap.parse_args()
    return permit(a.record, a.wait_s)


if __name__ == "__main__":
    sys.exit(main())
