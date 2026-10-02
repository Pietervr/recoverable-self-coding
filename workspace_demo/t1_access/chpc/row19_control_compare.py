"""Ledger row 19, the recovery control (Codex 523249d, launch conditions E and F): compare the normal subchain (C1)
with the interrupted-then-resumed subchain (C3) on the declared fixed target 0..target-1 under the unchanged B
identity, and say SEPARATELY whether (1) the scientific outputs agree and (2) the control is technically QUALIFIED
as a recovery control. Every supplied file is validated on its own first: each record's checksum is recomputed, its
schema and failure semantics checked, its identity bound to the task binding, and the index set required to be
exactly the target; the status files must show C1 fresh (nothing resumed, original computed) and C3 resumed
(records resumed, original from its cache); the interruption record must show a real PBS kill of C2 with at least
one and fewer than `target` accepted records before it.

    python chpc/row19_control_compare.py --c1 <ckpt.jsonl> --c3 <ckpt.jsonl> --task <task_0.json>
           --status-c1 <status_0.json> --status-c3 <status_0.json> --interruption <c2_interruption.json> [--target 20]

Exit 0: parity AND qualified; 1: parity differs; 2: parity holds but the control is not qualified (or validation
failed); 3: both. Prints no statistic (the records' stats are compared, never shown).
"""
import json, sys, argparse, hashlib, math, os

SCIENTIFIC = ("rep", "chosen", "stats", "failed", "failed_reason", "ident", "seed", "n_rep")
EXCLUDED = ("fit_seconds", "sha")


def record_sha(rec):
    return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != "sha"}, sort_keys=True, default=float).encode()).hexdigest()


def _finite_tree(o):
    if isinstance(o, dict):
        return all(_finite_tree(v) for v in o.values())
    if isinstance(o, list):
        return all(_finite_tree(v) for v in o)
    if isinstance(o, float):
        return math.isfinite(o)
    return isinstance(o, (int, str, bool)) or o is None


def load_validated(path, ident, n_rep, target):
    """Records keyed by index, plus the problems found; nothing scientific is returned beyond the records themselves."""
    problems, recs = [], {}
    if not os.path.exists(path):
        return recs, [f"{path}: missing"]
    with open(path) as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except Exception:
                problems.append(f"{path}:{lineno}: not JSON"); continue
            if not isinstance(d, dict) or any(k not in d for k in SCIENTIFIC + ("sha",)):
                problems.append(f"{path}:{lineno}: missing fields"); continue
            if record_sha(d) != d["sha"]:
                problems.append(f"{path}:{lineno}: checksum mismatch"); continue
            if d["ident"] != ident or int(d["n_rep"]) != int(n_rep):
                problems.append(f"{path}:{lineno}: identity or B differs from the task binding"); continue
            if not isinstance(d["rep"], int) or not (0 <= d["rep"] < target):
                problems.append(f"{path}:{lineno}: index {d['rep']} outside the target 0..{target-1}"); continue
            if not (isinstance(d["chosen"], list) and all(isinstance(c, int) for c in d["chosen"]) and d["chosen"]):
                problems.append(f"{path}:{lineno}: chosen is not a list of ints"); continue
            if not isinstance(d["failed"], bool) or not isinstance(d["stats"], dict) or not d["stats"]:
                problems.append(f"{path}:{lineno}: failed/stats malformed"); continue
            if not d["failed"] and not _finite_tree(d["stats"]):
                problems.append(f"{path}:{lineno}: non-finite statistic on a record not marked failed"); continue
            if d["rep"] in recs:
                problems.append(f"{path}:{lineno}: index {d['rep']} recorded twice"); continue
            recs[d["rep"]] = d
    want = set(range(target))
    if set(recs) != want:
        problems.append(f"{path}: index set is not exactly 0..{target-1} (missing {sorted(want - set(recs))[:10]}, extra {sorted(set(recs) - want)[:10]})")
    return recs, problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--c1", required=True); ap.add_argument("--c3", required=True)
    ap.add_argument("--task", required=True, help="the task binding (task_<rep>.json) the control is bound to")
    ap.add_argument("--status-c1", required=True); ap.add_argument("--status-c3", required=True)
    ap.add_argument("--interruption", required=True, help="C2's interruption record (PBS accounting + records before the kill)")
    ap.add_argument("--target", type=int, default=20)
    a = ap.parse_args(argv)
    task = json.load(open(a.task))["binding"]
    ident, n_rep = task["ident"], int(task["n_rep"])
    if task.get("until") is not None and int(task["until"]) != a.target:
        print(f"task binding's target {task.get('until')} differs from --target {a.target}")
    c1, p1 = load_validated(a.c1, ident, n_rep, a.target)
    c3, p3 = load_validated(a.c3, ident, n_rep, a.target)
    qual = []  # qualification problems
    qual += p1 + p3
    s1, s3 = json.load(open(a.status_c1)), json.load(open(a.status_c3))
    for k in ("ident", "code_hash", "policy", "n_rep"):
        if s1.get(k) != s3.get(k) or s1.get(k) != (ident if k == "ident" else s1.get(k)):
            qual.append(f"status: {k} differs or is not the task's")
    if int(s1.get("until", -1)) != a.target or int(s3.get("until", -1)) != a.target:
        qual.append("status: a control run was not bound to the target")
    if s1.get("n_resumed", -1) != 0 or s1.get("original_cached") is not False:
        qual.append("status C1: not a fresh run (something resumed or the original came from a cache)")
    if int(s3.get("n_resumed", 0)) < 1 or s3.get("original_cached") is not True:
        qual.append("status C3: not a resumed run (nothing resumed, or the original was recomputed)")
    if s3.get("n_damaged", 0) or s1.get("n_damaged", 0):
        qual.append("status: damaged records were recomputed somewhere")
    if not (s1.get("target_complete") and s3.get("target_complete")):
        qual.append("status: a control run did not report the target complete")
    try:
        it = json.load(open(a.interruption))
        n_before = int(it["accepted_records_before"])
        if not (1 <= n_before < a.target):
            qual.append(f"interruption: {n_before} accepted record(s) before the kill is not within 1..{a.target-1}")
        if not it.get("pbs_killed"):
            qual.append("interruption: C2 was not killed by PBS (cooperative end or normal completion is non-qualification)")
        if float(it.get("walltime_used_s", 0)) + 1e-9 < float(it.get("walltime_requested_s", 1e18)):
            qual.append("interruption: scheduler-accounted walltime used is below the requested walltime (not a walltime kill)")
        if it.get("job_id") in (None, "") or it.get("exit_status") in (None, ""):
            qual.append("interruption: job id or PBS exit status missing")
        if int(s3.get("n_resumed", 0)) != n_before:
            qual.append(f"interruption: C3 resumed {s3.get('n_resumed')} record(s) but C2 had committed {n_before}")
    except Exception as e:
        qual.append(f"interruption record unreadable: {e}")
    parity_ok = not p1 and not p3
    diffs = []
    if parity_ok:
        for r in range(a.target):
            for k in SCIENTIFIC:
                if c1[r].get(k) != c3[r].get(k):
                    diffs.append(f"index {r}: {k} differs")
            extra = (set(c1[r]) | set(c3[r])) - set(SCIENTIFIC) - set(EXCLUDED)
            if extra:
                diffs.append(f"index {r}: unexpected fields {sorted(extra)}")
        parity_ok = not diffs
    both_failed = parity_ok and any(c1[r]["failed"] for r in c1)
    print(f"ROW 19 RECOVERY CONTROL, target 0..{a.target-1}, B = {n_rep}, identity {ident[:16]}")
    print(f"  C1 {len(c1)} validated record(s), C3 {len(c3)}; validation problems {len(p1) + len(p3)}")
    for x in (p1 + p3)[:20]:
        print("   -", x)
    for x in diffs[:20]:
        print("   -", x)
    print(f"  PARITY: {'AGREE - every scientific field of the resumed chain equals the normal chain on the target' if parity_ok else 'DIFFER or not comparable'}"
          + ("  (NOTE: failed resamples agree as failed; parity of failures is not evidence of a working procedure)" if both_failed else ""))
    print(f"  QUALIFIED AS A RECOVERY CONTROL: {'YES' if not qual else 'NO'}")
    for x in qual[:20]:
        print("   -", x)
    return (0 if parity_ok else 1) + (0 if not qual else 2)


if __name__ == "__main__":
    sys.exit(main())
