"""The qualification cutover (Codex cf07869 D-2): the ONLY way to set qualification.permitted in ec2_release_state.json.

    python3 aws_ec2/qual_permit.py --record <reviewed qualification-permission record, path relative to aws_ec2/> [--wait-s 600]
    python3 aws_ec2/qual_permit.py --epoch2 --record <reviewed E2Q1 permission record>              # REVISION 2 (candidate)
    python3 aws_ec2/qual_permit.py --epoch2 --e2q2 --record <reviewed E2Q2 permission record>        # REVISION 2 (candidate)

  1. take runs/.bench_inflight.lock EXCLUSIVELY (bench_launch.inflight): this waits until every in-flight benchmark
     admission/recovery command - including one still waiting or staging before its first journal entry - has ended, and
     no new one can start meanwhile (a drain, not an inference from ledger intents); give up after --wait-s and change nothing
  2. write runs/BENCH_FENCE.json once (never overwritten): from now on every benchmark command refuses at entry AND
     immediately before every RunInstances issue/retry/recovery re-issue (bench_launch.cutover_problem)
  3. set qualification.permitted with the record's path and sha256 - only when row 23 is declared (backed) and the owner
     accepted the ceilings; prod_authority.release_state() also requires the fence before qualification is ok.
The running row-23 attempt-5 reaper is not a benchmark command (it never issues RunInstances) and is not affected; Q1/Q2
admission separately refuses while any benchmark attempt is live (prod_authority.exclusion_problem).
Exit 0 permitted (or already permitted with this record), 3 refused (nothing changed after step 1 fails).

REVISION 2 - CANDIDATE, not adopted (EC2 provider epoch 2 QUALIFICATION, chpc/candidate_e2q/DESIGN_e2q.md). With --epoch2
the same drain and fence precede writing the `qualification_e2` block {permitted, record_path, record_sha256} that
prod_authority REVISION 7 reads (absent = not permitted); the epoch-1 block is never touched. The epoch-2 allowance needs no
owner-ceiling acceptance here: its bounds (2 qualification instances, 4 extra production batches, USD 300) are code
constants enforced by prod_authority.epoch2_problem (owner, 17 Oct). --e2q2 writes `qualification_e2.e2q2` only when the
epoch-2 qualification is already permitted: the conditional retry needs its OWN reviewed record naming E2Q1's
external-cause end (spot interruption before the memory gate, or capacity) - never a retry by outcome (QUALIFICATION_E2.md
s.2). The record is a reviewed file; this tool pins its bytes, it does not judge its content."""
import argparse, fcntl, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prod_authority as PA                                  # first: resolves t1_access and the data directory aws_ec2/
import bench_launch as L


def _drain_and_fence(record_rel, wait_s, log):
    """Steps 1-2. Returns the open lock handle (caller releases) or None when refused."""
    os.makedirs(os.path.dirname(L.inflight_path()), exist_ok=True)
    fh = open(L.inflight_path(), "a+"); t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); break
        except BlockingIOError:
            if time.time() - t0 >= wait_s:
                fh.close(); log(f"REFUSED: benchmark commands still in flight after {wait_s} s - nothing changed"); return None
            time.sleep(1)
    fp = L.fence_path()
    if not os.path.exists(fp):
        fd = os.open(fp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        with os.fdopen(fd, "w") as f:
            json.dump(dict(schema="t1-bench-fence-1", at=time.time(), record=record_rel,
                           note="qualification cutover: benchmark admissions/recoveries frozen (Codex cf07869 D-2)"), f, indent=1)
            f.flush(); os.fsync(f.fileno())
    log(f"fence set: {fp}")
    return fh


def _write_state(r):
    tmp = PA.RELEASE_STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(r, f, indent=1); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, PA.RELEASE_STATE)


def permit(record_rel, wait_s=600, log=print, epoch2=False, e2q2=False):
    rp = os.path.join(L.HERE, record_rel)
    if not os.path.exists(rp):
        log(f"REFUSED: the qualification-permission record {record_rel} does not exist"); return 3
    rel = PA.release_state()
    if not rel["row23"]["ok"]:
        log("REFUSED: row 23 is not declared successful with a backed report"); return 3
    if not epoch2 and not rel["qualification"].get("owner_accepted_ceilings"):
        log("REFUSED: the owner has not accepted the qualification ceilings"); return 3
    if e2q2 and not (epoch2 and rel["qualification_e2"]["ok"]):
        log("REFUSED: E2Q2 is permitted only with --epoch2 and after the epoch-2 qualification itself is permitted"); return 3
    fh = _drain_and_fence(record_rel, wait_s, log)
    if fh is None:
        return 3
    try:
        r = json.load(open(PA.RELEASE_STATE))
        if not epoch2:
            r["qualification"].update(permitted=True, record_path=record_rel, record_sha256=L.sha256(rp))
            what = "qualification"
        elif not e2q2:
            q2 = r.get("qualification_e2") if isinstance(r.get("qualification_e2"), dict) else {}
            q2.update(permitted=True, record_path=record_rel, record_sha256=L.sha256(rp),
                      rule="epoch-2 qualification (QUALIFICATION_E2.md): E2Q1 one instance; bounds in prod_authority.epoch2_problem")
            r["qualification_e2"] = q2; what = "qualification_e2"
        else:
            r["qualification_e2"]["e2q2"] = dict(permitted=True, record_path=record_rel, record_sha256=L.sha256(rp),
                                                 rule="the one conditional identical retry after an external-cause end of E2Q1")
            what = "qualification_e2.e2q2"
        _write_state(r)
        log(f"{what} permitted in ec2_release_state.json")
        return 0
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--record", required=True); ap.add_argument("--wait-s", type=float, default=600)
    ap.add_argument("--epoch2", action="store_true"); ap.add_argument("--e2q2", action="store_true")
    a = ap.parse_args()
    return permit(a.record, a.wait_s, epoch2=a.epoch2, e2q2=a.e2q2)


if __name__ == "__main__":
    sys.exit(main())
