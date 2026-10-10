"""Common STOP for EC2 production (Codex f3dd3d7 contract 5).

    python3 prod_stop.py --epoch 1 --reason "<why>"              # no new dispatch; running instances stop starting work
    python3 prod_stop.py --epoch 1 --reason "<why>" --terminate  # also terminate every running instance of the epoch now

Semantics: the STOP is written locally (runs/prod-e<epoch>/STOP) and to S3; prod_launch refuses while either exists or the
Lengau screen root carries STOP. Each running instance polls S3 every 300 s and touches its own root STOP, which the
unchanged worker checks before each index - with one index per worker, a fit already running FINISHES (its record is
ingested normally) and no new fit starts. --terminate ends the instances at once (their in-flight fits are lost and stay
charged; the reaper reconciles them). Removing STOP is a deliberate manual step: delete both files."""
import argparse, json, os, sys, time
import bench_launch as L, prod_authority as PA


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epoch", type=int, required=True); ap.add_argument("--reason", required=True)
    ap.add_argument("--terminate", action="store_true")
    a = ap.parse_args(); run = PA.run_name(a.epoch)
    doc = json.dumps(dict(epoch=a.epoch, reason=a.reason, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), terminate=a.terminate))
    p = os.path.join(L.run_dir(run), "STOP"); open(p, "w").write(doc + "\n")
    L.aws("s3", "cp", p, f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run}/STOP", "--only-show-errors")
    live = [i for i in L.find_instances(**{"tag:run": run}) if i["State"]["Name"] not in ("terminated", "shutting-down")]
    print(f"STOP written (local + S3) for {run}: {a.reason}; running instances {[i['InstanceId'] for i in live]}")
    if a.terminate and live:
        for i in live:
            ok = L.emergency_terminate(i["InstanceId"])
            print(f"terminate {i['InstanceId']}: {'requested' if ok else 'FAILED - retry by hand'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
