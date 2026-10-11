"""Common STOP for EC2 work (Codex f3dd3d7 contract 5; repaired for Codex RSC 0483db4 V10-8). Mac only.

    python3 prod_stop.py --run prod-e1 --reason "<why>"            # this run: no new dispatch; its instances stop starting work
    python3 prod_stop.py --all --reason "<why>"                    # GLOBAL STOP (runs/STOP + S3 code/t1_access/aws_bench/STOP)
    python3 prod_stop.py --run prod-e1 --reason "<why>" --terminate # also terminate the run's live instances now

Sources a launch or a recovery refuses on (prod_launch.stop_problem): the run's and the global local STOP, the run's and
the global S3 STOP, the Lengau screen root STOP and ec2/HOLD in the pulled snapshot. PROPAGATION of the Lengau common STOP:
the v11 candidate status tool (chpc/candidate_v10r2/row19_screen_status.py, every whole-role receipt) calls `propagate` for every
run the authority inventory shows live whenever the pulled root carries STOP; a failure is a receipt alarm, so no
admission anywhere proceeds on it. The producer of that signal is the Lengau root STOP itself (an operator or a held
admission writes it); nothing else on Lengau needs to change.

Instance semantics (prod_userdata.sh): STOP is checked before job-start and again immediately before any worker starts (a
STOP then means no fit starts at all; the instance uploads its setup evidence and powers off); after that a poller checks
every 60 s with 20 s-bounded calls and touches the instance root STOP, which each worker checks before its (single) index:
a fit already running FINISHES and its record is kept as evidence; none starts. Canonical publication of anything produced
under a STOP waits: the Lengau ingestion refuses while the root STOP or ec2/HOLD exists. --terminate ends the instances at
once (in-flight fits are lost and stay charged; the reaper reconciles them). Lifting STOP is a deliberate manual step:
delete the local file(s) and the S3 object(s)."""
import argparse, json, os, sys, time
import bench_launch as L

HERE = os.path.dirname(os.path.abspath(__file__))


def _write(local, key, doc):
    open(local, "w").write(doc + "\n")
    L.aws("s3", "cp", local, key, "--only-show-errors", timeout=30)        # raises on failure: the caller must know


def propagate(runs, reason, terminate=False):
    """Write STOP (local + S3) for each run; returns the runs written. Raises L.AwsError when S3 cannot be written."""
    doc = json.dumps(dict(reason=reason, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), terminate=terminate))
    out = []
    for run in runs:
        _write(os.path.join(L.run_dir(run), "STOP"), f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run}/STOP", doc)
        out.append(run)
        if terminate:
            for i in L.find_instances(**{"tag:run": run}):
                if i["State"]["Name"] not in ("terminated", "shutting-down"):
                    print(f"terminate {i['InstanceId']}: {'requested' if L.emergency_terminate(i['InstanceId']) else 'FAILED - retry by hand'}")
    return out


def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run"); g.add_argument("--all", action="store_true")
    ap.add_argument("--reason", required=True); ap.add_argument("--terminate", action="store_true")
    a = ap.parse_args()
    if a.all:
        doc = json.dumps(dict(scope="global", reason=a.reason, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
        _write(os.path.join(HERE, "runs", "STOP"), f"s3://{L.BUCKET}/code/t1_access/aws_bench/STOP", doc)
        print("GLOBAL STOP written (local + S3)"); return 0
    print(f"STOP written for {propagate([a.run], a.reason, a.terminate)}: {a.reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
