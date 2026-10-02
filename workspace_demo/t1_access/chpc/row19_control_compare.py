"""Ledger row 19, the recovery control (Codex 523249d E/F; e44f804 R3): compare the normal subchain (C1) with the
interrupted-then-resumed subchain (C3) on the declared fixed target 0..target-1 under the unchanged B identity, and say
SEPARATELY whether (1) the scientific outputs agree and (2) the control is technically QUALIFIED as a recovery
control. Every supplied file is validated on its own first against the FROZEN task: the dataset is rebuilt from the
manifest and the task binding, so each record's drawn concepts must equal the draw this identity makes for its index,
each record's checksum is recomputed, its statistics must hold every predictor and band as finite numbers unless the
record is marked failed with a string reason, its identity, seed and B must be the task's, and the index set must be
exactly the target. The status files must show C1 fresh and C3 resumed, both bound to the task (identity, code hash,
policy, seed, B, target) with typed roles; the interruption record must be typed, name the C2 job bound in the
campaign ledger, and show a real walltime kill with at least one and fewer than `target` accepted records before it,
equal to what C3 resumed. A parity of identically FAILED resamples is reported as parity but is NOT a qualification.

    python chpc/row19_control_compare.py --manifest M --task <task_0.json> --c1 <ckpt> --c3 <ckpt>
           --status-c1 <status> --status-c3 <status> --interruption <c2_interruption.json> --ledger <budget.json> [--target 20]

Exit 0: parity AND qualified; 1: parity differs; 2: parity holds but not qualified (or validation failed); 3: both.
Prints no statistic (the records' stats are compared, never shown).
"""
import os
os.environ.setdefault("NPROC", "1")
import json, sys, argparse, hashlib, math

SCIENTIFIC = ("rep", "chosen", "stats", "failed", "failed_reason", "ident", "seed", "n_rep")
EXCLUDED = ("fit_seconds", "sha")


def record_sha(rec):
    return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != "sha"}, sort_keys=True, default=float).encode()).hexdigest()


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def expected_contract(manifest_path, task_binding):
    """Rebuild the dataset of the frozen task (no fit) and return the expected draws per index and the band names."""
    import numpy as np
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
    import analyze as A, simulate as S
    man = json.load(open(manifest_path))
    st, c = man["setting"], man["cfg"]
    cfg = A.Config(start_policy=c["start_policy"], interval=c["interval"], n_boot_refit=int(c["n_boot_refit"]),
                   n_starts=int(c["n_starts"]), n_starts_inner=int(c["n_starts_inner"]), refit_min_usable=float(c["refit_min_usable"]),
                   n_outer=int(c["n_outer"]), n_inner=int(c["n_inner"]))
    kw = dict(st["grid"]); theta = S.generator_theta(st["generator"], **kw)
    rep = int(task_binding["rep"]); seed = int(task_binding["ds_seed"])
    if S.dataset_seed(st["generator"], kw, rep, int(st["D"]), int(man["datasets"]["seed_base"])) != seed:
        raise ValueError("the task binding's seed is not the manifest's resolved seed for its rep")
    ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]), layers=np.array(st["layers"]),
                        rho=float(st["rho"]), seed=seed)
    ds.meta.update(generator=st["generator"], theta=[float(x) for x in theta], D=int(st["D"]), rho=float(st["rho"]), seed=seed)
    folds = A.stratified_folds(ds.family, cfg.n_outer, seed)
    n_rep = int(cfg.n_boot_refit)
    ident = A.dataset_identity(ds, cfg, seed, n_rep, folds)
    if ident != task_binding["ident"] or n_rep != int(task_binding["n_rep"]):
        raise ValueError("the task binding's identity or B is not the manifest's for this rep")
    idx = A.stratified_resample(ds.family, n_rep, np.random.default_rng(seed))
    masks = {b: m for b, m in A.band_masks(ds.layers, cfg.bands).items() if m.any()}
    bands = list(masks) + (["ws_minus_early"] if "ws" in masks and "early" in masks else [])
    return dict(ident=ident, seed=seed, n_rep=n_rep, draws={i: [int(x) for x in idx[i]] for i in range(n_rep)}, bands=bands,
                predictors=list(A.PREDICTORS), code_hash=S.config_hash(cfg, int(st["D"]), st["layers"], seed, float(st["rho"])),
                policy=cfg.start_policy)


def load_validated(path, ex, target):
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
            if not isinstance(d, dict) or any(k not in d for k in SCIENTIFIC + ("sha", "fit_seconds")):
                problems.append(f"{path}:{lineno}: missing fields"); continue
            if record_sha(d) != d["sha"]:
                problems.append(f"{path}:{lineno}: checksum mismatch"); continue
            if d["ident"] != ex["ident"] or d["n_rep"] != ex["n_rep"] or d["seed"] != ex["seed"]:
                problems.append(f"{path}:{lineno}: identity, seed or B differs from the frozen task"); continue
            if not _is_int(d["rep"]) or not (0 <= d["rep"] < target):
                problems.append(f"{path}:{lineno}: index {d['rep']!r} outside the target 0..{target-1}"); continue
            if d["chosen"] != ex["draws"][d["rep"]]:
                problems.append(f"{path}:{lineno}: drawn concepts differ from the identity's draw for index {d['rep']}"); continue
            if not isinstance(d["failed"], bool) or not isinstance(d["failed_reason"], str):
                problems.append(f"{path}:{lineno}: failed/failed_reason malformed"); continue
            if not (_is_num(d["fit_seconds"]) and math.isfinite(d["fit_seconds"]) and d["fit_seconds"] >= 0):
                problems.append(f"{path}:{lineno}: fit_seconds not finite and non-negative"); continue
            s = d["stats"]
            if not isinstance(s, dict) or sorted(s) != sorted(ex["predictors"]):
                problems.append(f"{path}:{lineno}: stats do not hold exactly the predictors"); continue
            bad = False
            for p, bs in s.items():
                if not isinstance(bs, dict) or sorted(bs) != sorted(ex["bands"]):
                    bad = True; break
                for b, v in bs.items():
                    if not _is_num(v) or (not d["failed"] and not math.isfinite(v)):
                        bad = True; break
                if bad:
                    break
            if bad:
                problems.append(f"{path}:{lineno}: a statistic is missing, non-numeric, or non-finite on a record not marked failed"); continue
            if d["rep"] in recs:
                problems.append(f"{path}:{lineno}: index {d['rep']} recorded twice"); continue
            recs[d["rep"]] = d
    want = set(range(target))
    if set(recs) != want:
        problems.append(f"{path}: index set is not exactly 0..{target-1} (missing {sorted(want - set(recs))[:10]}, extra {sorted(set(recs) - want)[:10]})")
    return recs, problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--task", required=True, help="the task binding (task_<rep>.json) the control is bound to")
    ap.add_argument("--c1", required=True); ap.add_argument("--c3", required=True)
    ap.add_argument("--status-c1", required=True); ap.add_argument("--status-c3", required=True)
    ap.add_argument("--interruption", required=True, help="C2's interruption record (PBS accounting + records before the kill)")
    ap.add_argument("--ledger", required=True, help="the campaign ledger budget.json (binds the C2 job id)")
    ap.add_argument("--target", type=int, default=20)
    a = ap.parse_args(argv)
    qual, diffs = [], []
    task = json.load(open(a.task))["binding"]
    if task.get("until") is None or int(task["until"]) != a.target:
        qual.append(f"task binding's target {task.get('until')} is not --target {a.target}")
    try:
        ex = expected_contract(a.manifest, task)
    except Exception as e:
        print(f"the frozen task cannot be rebuilt from the manifest: {e}")
        print("  PARITY: not comparable\n  QUALIFIED AS A RECOVERY CONTROL: NO")
        return 3
    c1, p1 = load_validated(a.c1, ex, a.target)
    c3, p3 = load_validated(a.c3, ex, a.target)
    qual += p1 + p3
    s1, s3 = json.load(open(a.status_c1)), json.load(open(a.status_c3))
    for name, s_, role, fresh in (("C1", s1, "c1", True), ("C3", s3, "c3", False)):
        if s_.get("kind") != role:
            qual.append(f"status {name}: role is {s_.get('kind')!r}, not {role!r}")
        if s_.get("ident") != ex["ident"] or s_.get("code_hash") != ex["code_hash"] or s_.get("policy") != ex["policy"] \
                or s_.get("seed") != ex["seed"] or s_.get("n_rep") != ex["n_rep"]:
            qual.append(f"status {name}: identity/code hash/policy/seed/B are not the frozen task's")
        if s_.get("until") != a.target:
            qual.append(f"status {name}: not bound to the target {a.target}")
        if not isinstance(s_.get("job"), str) or not s_.get("job"):
            qual.append(f"status {name}: no job id")
        if s_.get("n_damaged", 0):
            qual.append(f"status {name}: damaged records were recomputed")
        if s_.get("target_complete") is not True:
            qual.append(f"status {name}: did not report the target complete")
        if fresh and not (s_.get("n_resumed") == 0 and s_.get("original_cached") is False):
            qual.append("status C1: not a fresh run (something resumed or the original came from a cache)")
        if not fresh and not (_is_int(s_.get("n_resumed")) and s_.get("n_resumed") >= 1 and s_.get("original_cached") is True):
            qual.append("status C3: not a resumed run (nothing resumed, or the original was recomputed)")
    try:
        it = json.load(open(a.interruption))
        led = json.load(open(a.ledger))
        c2 = [e for e in led["entries"].values() if e.get("kind") == "c2" and e.get("rep") == int(task["rep"])]
        if len(c2) != 1 or not c2[0].get("job_id"):
            qual.append("ledger: no single bound C2 reservation for this rep")
        elif it.get("job_id") != c2[0]["job_id"]:
            qual.append(f"interruption: job id {it.get('job_id')!r} is not the C2 job bound in the ledger ({c2[0]['job_id']})")
        if it.get("pbs_killed") is not True:
            qual.append("interruption: pbs_killed is not exactly true (cooperative end or normal completion is non-qualification)")
        if not _is_int(it.get("exit_status")) or it.get("exit_status") == 0:
            qual.append("interruption: PBS exit status is not a non-zero integer")
        wr, wu = it.get("walltime_requested_s"), it.get("walltime_used_s")
        if not (_is_num(wr) and _is_num(wu) and math.isfinite(wr) and math.isfinite(wu) and wr > 0 and wu >= wr):
            qual.append("interruption: walltime used/requested are not finite with used >= requested (not a walltime kill)")
        nb = it.get("accepted_records_before")
        if not _is_int(nb) or not (1 <= nb < a.target):
            qual.append(f"interruption: accepted records before the kill {nb!r} is not an integer within 1..{a.target-1}")
        elif s3.get("n_resumed") != nb:
            qual.append(f"interruption: C3 resumed {s3.get('n_resumed')} record(s) but C2 had committed {nb}")
        if it.get("original_cache_reused") is not True:
            qual.append("interruption: the original cache was not recorded as reused by C3")
        if "tail_fragment_present" not in it or not isinstance(it["tail_fragment_present"], bool):
            qual.append("interruption: whether a lost in-flight record/tail fragment was present is not recorded as a bool")
    except Exception as e:
        qual.append(f"interruption or ledger unreadable: {e}")
    parity_ok = not p1 and not p3
    if parity_ok:
        for r in range(a.target):
            for k in SCIENTIFIC:
                if c1[r].get(k) != c3[r].get(k):
                    diffs.append(f"index {r}: {k} differs")
            extra = (set(c1[r]) | set(c3[r])) - set(SCIENTIFIC) - set(EXCLUDED)
            if extra:
                diffs.append(f"index {r}: unexpected fields {sorted(extra)}")
        parity_ok = not diffs
    any_failed = parity_ok and any(c1[r]["failed"] for r in c1)
    if any_failed:
        qual.append(f"{sum(c1[r]['failed'] for r in c1)} resample(s) FAILED in both chains: parity of failures is not a working procedure")
    print(f"ROW 19 RECOVERY CONTROL, target 0..{a.target-1}, B = {ex['n_rep']}, identity {ex['ident'][:16]}")
    print(f"  C1 {len(c1)} validated record(s), C3 {len(c3)}; validation problems {len(p1) + len(p3)}")
    for x in (p1 + p3)[:20]:
        print("   -", x)
    for x in diffs[:20]:
        print("   -", x)
    print(f"  PARITY: {'AGREE - every scientific field of the resumed chain equals the normal chain on the target' if parity_ok else 'DIFFER or not comparable'}")
    print(f"  QUALIFIED AS A RECOVERY CONTROL: {'YES' if not qual else 'NO'}")
    for x in qual[:20]:
        print("   -", x)
    return (0 if parity_ok else 1) + (0 if not qual else 2)


if __name__ == "__main__":
    sys.exit(main())
