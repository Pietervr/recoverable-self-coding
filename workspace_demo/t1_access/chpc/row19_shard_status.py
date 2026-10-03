"""Row 19 sharded route: the live view from the Mac (R052). Pulls the shard root and its campaign ledger fresh (a failed
pull is an alarm, never a green), validates EVERY record file against the frozen task rebuilt from the manifest and the
task binding (`row19_control_compare.expected_contract`, with the pinned-runtime identity oracle where this host cannot
rebuild the identity; `validate_record`), and reports per dataset: accepted, failed, invalid, missing; the per-resample
wall and fit time distribution and peak memory from the timing rows; each job's workers and exits; and the PARITY of
shard records against the sequential chain's records for the same identity and index wherever both exist (the slice's
C1 and main checkpoints from the watch's last pull): the scientific fields must be bitwise equal.

    python chpc/row19_shard_status.py --manifest chpc/row19_shard_manifest.json [--no-pull] [--qstat]
Exit 1 on any alarm; 0 only on fresh evidence with none."""
import os, sys, json, glob, time, shutil, argparse, subprocess, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
os.environ.setdefault("NPROC", "1")
from row19_control_compare import expected_contract, validate_record
import row19_identity_oracle as O

HOST = "chpc-scp"
LIVE_DIR = os.path.join(HERE, "results", "row19_shard", "live")
SLICE_LIVE = os.path.join(HERE, "results", "row19_slice", "live")
SCI = ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep")


def sh(cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def fresh_snapshot(campaign, root):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage = os.path.join(os.path.dirname(LIVE_DIR), f"stage_{stamp}")
    problems = []
    for name, remote in (("campaign", campaign), ("root", root)):
        local = os.path.join(stage, name); os.makedirs(local, exist_ok=True)
        rc, out, err = sh(["scp", "-q", "-r", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{remote}/.", local])
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True); return False, problems
    shutil.rmtree(LIVE_DIR, ignore_errors=True); shutil.move(stage, LIVE_DIR)
    return True, []


def sequential_records(ident):
    """{index: record} from the slice's pulled sequential checkpoints carrying this identity (C1 and the mains)."""
    out = {}
    for ck in glob.glob(os.path.join(SLICE_LIVE, "*", "ckpt", f"refit_{ident[:24]}.jsonl")):
        for line in open(ck).read().splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("ident") == ident and isinstance(d.get("rep"), int):
                out.setdefault(d["rep"], []).append((os.path.basename(os.path.dirname(os.path.dirname(ck))), d))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "row19_shard_manifest.json"))
    ap.add_argument("--no-pull", action="store_true"); ap.add_argument("--qstat", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); B = int(man["cfg"]["n_boot_refit"])
    alarms, fresh = [], False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(man["storage"]["campaign"], man["storage"]["root"]); alarms += probs
    root = os.path.join(LIVE_DIR, "root")
    print(f"ROW 19 SHARDED ROUTE, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}  evidence: "
          f"{'FRESH snapshot' if fresh else 'LOCAL CACHE (not fresh evidence)' if a.no_pull else 'PULL FAILED - stale'}")
    led_p = os.path.join(LIVE_DIR, "campaign", "budget.json")
    entries = []
    if os.path.exists(led_p):
        led = json.load(open(led_p)); entries = sorted((e for e in led["entries"].values() if e.get("kind") == "shard"), key=lambda e: e["rep"])
        spent = sum(float(e.get("settled_core_h", 0) or 0) for e in led["entries"].values())
        live = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
        print(f"  ledger: cap {led.get('cap_core_h')}  settled {spent:.1f}  live reserved {live:.1f}  shard jobs {len(entries)}")
    else:
        alarms.append("campaign ledger absent in the snapshot")
    states = {}
    if a.qstat and entries:
        ids = [e["job_id"] for e in entries if e.get("job_id")]
        rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", "lengau", "qstat -x " + " ".join(ids) + " 2>&1 | tail -n +3"])
        if rc == 0:
            for line in out.splitlines():
                p = line.split()
                if len(p) >= 5:
                    states[p[0]] = p[-2]
        else:
            alarms.append("PBS observation failed (qstat unreachable)")
    oracle = O.load(root) if (fresh or a.no_pull) and os.path.exists(os.path.join(root, O.ORACLE_NAME)) else None
    for rep in [int(r) for r in man["datasets"]["reps"]]:
        tp = os.path.join(root, f"task_{rep}.json")
        if not os.path.exists(tp):
            print(f"  rep {rep}: no task binding yet"); continue
        b = json.load(open(tp))["binding"]
        try:
            ex = expected_contract(a.manifest, b, oracle=oracle)
        except Exception as e:
            alarms.append(f"rep {rep}: the task binding is not this manifest's ({e})"); continue
        acc, failed, bad = {}, [], []
        for p in sorted(glob.glob(os.path.join(root, "records", f"rep{rep}", "rec_*.json"))):
            try:
                d = json.load(open(p))
            except Exception:
                bad.append((os.path.basename(p), "not JSON")); continue
            why = validate_record(d, ex, B)
            if why or f"rec_{d.get('rep', -1):03d}.json" != os.path.basename(p):
                bad.append((os.path.basename(p), why or "index does not match the file name")); continue
            acc[d["rep"]] = d
            if d["failed"]:
                failed.append(d["rep"])
        rows = []
        for tfile in glob.glob(os.path.join(root, "timing", f"rep{rep}.job*.jsonl")):
            rows += [json.loads(l) for l in open(tfile).read().splitlines() if l.strip()]
        walls = sorted(r["wall_s"] for r in rows if isinstance(r.get("wall_s"), (int, float)))
        rss = max((r.get("maxrss", 0) for r in rows), default=0)
        seq = sequential_records(b["ident"])
        both = sorted(set(acc) & set(seq)); diff = []
        for i in both:
            for where, s in seq[i]:
                if any(acc[i][k] != s[k] for k in SCI):
                    diff.append((i, where))
        print(f"  rep {rep}: identity {b['ident'][:16]} basis {ex['basis']}; accepted {len(acc)}/{B}, failed {len(failed)}, invalid {len(bad)}, missing {B - len(acc)}")
        if walls:
            print(f"    per-resample wall: n {len(walls)}, median {statistics.median(walls)/3600:.2f} h, min {walls[0]/3600:.2f} h, max {walls[-1]/3600:.2f} h; "
                  f"peak worker memory {rss/2**30:.2f} GiB")
        print(f"    parity with the sequential chain: {len(both)} index(es) in both, {len(both) - len({i for i, _ in diff})} bitwise equal"
              + (f", DIFFERENT at {diff[:6]}" if diff else ""))
        if bad:
            alarms.append(f"rep {rep}: {len(bad)} record file(s) rejected, e.g. {bad[:3]}")
        if failed:
            alarms.append(f"rep {rep}: {len(failed)} FAILED resample(s): {failed[:10]}")
        if diff:
            alarms.append(f"rep {rep}: shard records differ from the sequential chain at {diff[:10]}")
    for e in entries:
        n = int(e["rep"]); job = e.get("job_id")
        sts = [json.load(open(p)) for p in glob.glob(os.path.join(root, "status", f"job{job}.slot*.json"))] if job else []
        codes = [s.get("exit") for s in sts]
        print(f"  job {n} {job} {e.get('state')} PBS {states.get(job, states.get((job or '').split('.')[0], '-'))}: workers ended {len(sts)}, "
              f"exits {dict((c, codes.count(c)) for c in set(codes))}, runner exit {e.get('runner_exit')}")
        for s in sts:
            if s.get("exit") == 4:
                alarms.append(f"job {n} slot {s.get('slot')}: HELD ({str(s.get('reason'))[:120]})")
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms IN THE LOCAL CACHE (not fresh evidence)"))
    for x in alarms:
        print("   -", x)
    return 1 if alarms or not (fresh or a.no_pull) else 0


if __name__ == "__main__":
    sys.exit(main())
