"""Ledger row 19, the recovery control (Codex 523249d E/F; e44f804 R3; 6d8a597 R3): compare the normal subchain (C1) with
the interrupted-then-resumed subchain (C3) on the declared fixed target 0..target-1 under the unchanged B identity, and
say SEPARATELY whether (1) the scientific outputs agree and (2) the control is technically QUALIFIED as a recovery
control. Every supplied file is validated on its own first against the FROZEN task: the dataset is rebuilt from the
manifest and the task binding, so each record's drawn concepts must equal the draw this identity makes for its index,
each record's checksum is recomputed, its statistics must hold every predictor and band as finite numbers unless the
record is marked failed with a string reason, its identity, seed and B must be the task's, and the index set must be
exactly the target. The status files must be TERMINAL and successful (phase final, exit 75 - the ordinary end of a
partial-B control - no memory breach, no held state), bound to the task (identity, code hash, policy, seed, B, target)
with typed roles, and their job ids must be the C1 and C3 jobs bound in the campaign ledger; C1 fresh and C3 resumed.
The interruption record must be typed, name the C2 job bound in the ledger, request exactly the walltime that C2's
reservation carries, and show a real walltime kill with at least one and fewer than `target` accepted records before
it, equal to what C3 resumed. Any FAILED resample in either chain is non-qualification, whatever the parity.

    python chpc/row19_control_compare.py --manifest M --task <task_0.json> --c1 <ckpt> --c3 <ckpt>
           --status-c1 <status> --status-c3 <status> --interruption <c2_interruption.json> --ledger <budget.json> [--target 20]

Exit 0: parity AND qualified; 1: parity differs; 2: parity holds but not qualified (or validation failed); 3: both.
Prints no statistic (the records' stats are compared, never shown).
"""
import os
os.environ.setdefault("NPROC", "1")
import json, sys, argparse, hashlib, math

SCIENTIFIC = ("rep", "chosen", "stats", "failed", "failed_reason", "ident", "seed", "n_rep")
CANONICAL_SOURCES = ("analyze.py", "models.py", "simulate.py")       # the sources the producer registers as loaded
EXCLUDED = ("fit_seconds", "sha")
CONTROL_EXIT = 75          # a partial-B control ends with "resume" (its target is complete, B is not)


def record_sha(rec):
    return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != "sha"}, sort_keys=True, default=float).encode()).hexdigest()


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def expected_contract(manifest_path, task_binding, oracle=None):
    """Rebuild the dataset of the frozen task (no fit) and return the expected draws per index and the band names.
    `oracle`: the root's pulled identity_oracle.json (a dict from row19_identity_oracle.load) - consulted ONLY when this
    host's rebuilt identity differs from the binding's; the returned `basis` is 'local' or 'oracle' with its detail."""
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
    snap = task_binding.get("numerical")
    if not isinstance(snap, dict):
        raise ValueError("the task binding carries no producer numerical snapshot")
    want = man["environment"]
    rt = snap.get("runtime", {})
    for k in ("python", "jax", "numpy", "scipy"):
        if str(rt.get(k)) != str(want.get(k)):
            raise ValueError(f"the producer's snapshot runtime {k} {rt.get(k)!r} is not the manifest's pinned {want.get(k)!r}")
    pins = man["code"]["files"]
    files = snap.get("files")
    if not isinstance(files, dict) or sorted(files) != sorted(CANONICAL_SOURCES):
        raise ValueError(f"the producer's snapshot does not name exactly the canonical sources {CANONICAL_SOURCES}")
    for name in CANONICAL_SOURCES:
        pin = pins.get(name)
        if not (isinstance(pin, str) and len(pin) == 64):
            raise ValueError(f"the manifest does not pin {name}, so the producer's snapshot cannot be verified")
        if str(files[name]) != pin[:16]:
            raise ValueError(f"the producer's loaded {name} digest {files[name]!r} is not the manifest's pin {pin[:16]!r}")
    for k in ("python", "jax", "numpy", "scipy"):
        if k not in rt:
            raise ValueError(f"the producer's snapshot runtime lacks {k}")
    local_models = A.numerical_snapshot().get("models", {})
    if snap.get("models") != json.loads(json.dumps(local_models, default=str)):
        raise ValueError("the producer's snapshot model settings differ from the pinned models.py's")
    ident = A.dataset_identity(ds, cfg, seed, n_rep, folds, numerical=snap)
    if n_rep != int(task_binding["n_rep"]):
        raise ValueError("the task binding's identity or B is not the manifest's for this rep")
    idx = A.stratified_resample(ds.family, n_rep, np.random.default_rng(seed))
    basis, basis_detail = "local", "identity reproduced by this host's reconstruction"
    if ident != task_binding["ident"]:
        # The producer-runtime identity oracle (chpc/row19_identity_oracle.py; Codex RSC 9d8f706): only when the local
        # rebuild differs, and only an entry bound to this manifest's bytes and this binding, generated under the pinned
        # runtime with the binding's snapshot, whose recomputed identity equals the binding's and whose structural digests
        # (everything but the response bytes, the folds, the full draw matrix) equal this host's reconstruction.
        if oracle is None:
            raise ValueError("the task binding's identity or B is not the manifest's for this rep")
        import row19_identity_oracle as O
        local_digests, _ = O.structural_digests(ds, folds, idx)
        ok, detail = O.verify_entry(oracle, manifest_path, task_binding, local_digests)
        if not ok:
            raise ValueError("the task binding's identity or B is not the manifest's for this rep, and the oracle cannot supply the "
                             "fallback: " + "; ".join(detail))
        ident, basis, basis_detail = task_binding["ident"], "oracle", detail
    masks = {b: m for b, m in A.band_masks(ds.layers, cfg.bands).items() if m.any()}
    bands = list(masks) + (["ws_minus_early"] if "ws" in masks and "early" in masks else [])
    return dict(ident=ident, seed=seed, n_rep=n_rep, draws={i: [int(x) for x in idx[i]] for i in range(n_rep)}, bands=bands,
                predictors=list(A.PREDICTORS), code_hash=S.config_hash(cfg, int(st["D"]), st["layers"], seed, float(st["rho"])),
                policy=cfg.start_policy, rep=rep, basis=basis, basis_detail=basis_detail)


def validate_record(d, ex, target):
    """The complete per-record contract against the frozen task; a reason string, or '' when the record is accepted."""
    if not isinstance(d, dict) or any(k not in d for k in SCIENTIFIC + ("sha", "fit_seconds")):
        return "missing fields"
    if record_sha(d) != d["sha"]:
        return "checksum mismatch"
    if d["ident"] != ex["ident"] or d["n_rep"] != ex["n_rep"] or d["seed"] != ex["seed"]:
        return "identity, seed or B differs from the frozen task"
    if not _is_int(d["rep"]) or not (0 <= d["rep"] < target):
        return f"index {d['rep']!r} outside the target 0..{target-1}"
    if d["chosen"] != ex["draws"][d["rep"]]:
        return f"drawn concepts differ from the identity's draw for index {d['rep']}"
    if not isinstance(d["failed"], bool) or not isinstance(d["failed_reason"], str):
        return "failed/failed_reason malformed"
    if not (_is_num(d["fit_seconds"]) and math.isfinite(d["fit_seconds"]) and d["fit_seconds"] >= 0):
        return "fit_seconds not finite and non-negative"
    s = d["stats"]
    if not isinstance(s, dict) or sorted(s) != sorted(ex["predictors"]):
        return "stats do not hold exactly the predictors"
    for p, bs in s.items():
        if not isinstance(bs, dict) or sorted(bs) != sorted(ex["bands"]):
            return f"stats[{p}] does not hold exactly the bands"
        for b, v in bs.items():
            if not _is_num(v) or (not d["failed"] and not math.isfinite(v)):
                return f"stats[{p}][{b}] is missing, non-numeric, or non-finite on a record not marked failed"
    return ""


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
            why = validate_record(d, ex, target)
            if why:
                problems.append(f"{path}:{lineno}: {why}"); continue
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
    ap.add_argument("--ledger", required=True, help="the campaign ledger budget.json (binds the C1, C2 and C3 jobs)")
    ap.add_argument("--target", type=int, default=20)
    ap.add_argument("--oracle", default=None, help="the C1 root's pulled identity_oracle.json (row19_identity_oracle.py); consulted only "
                                                   "when this host's rebuilt identity differs from the task binding's")
    a = ap.parse_args(argv)
    qual, diffs = [], []
    task_doc = json.load(open(a.task)); task = task_doc["binding"]; task_sha = task.get("manifest_sha")
    if task.get("until") is None or int(task["until"]) != a.target:
        qual.append(f"task binding's target {task.get('until')} is not --target {a.target}")
    oracle = None
    if a.oracle:
        import row19_identity_oracle as O
        oracle = O.load(a.oracle)
        if oracle is None:
            print(f"the oracle {a.oracle} is absent: local reconstruction only")
    try:
        ex = expected_contract(a.manifest, task, oracle=oracle)
    except Exception as e:
        print(f"the frozen task cannot be rebuilt from the manifest: {e}")
        print("  PARITY: not comparable\n  QUALIFIED AS A RECOVERY CONTROL: NO")
        return 3
    print(f"identity basis: {ex['basis']} - {ex['basis_detail']}")
    try:
        led = json.load(open(a.ledger))
        entries = {k: [e for e in led["entries"].values() if e.get("kind") == k and e.get("rep") == int(task["rep"])] for k in ("c1", "c2", "c3")}
    except Exception as e:
        print(f"ledger unreadable: {e}"); led, entries = None, {"c1": [], "c2": [], "c3": []}
    c1, p1 = load_validated(a.c1, ex, a.target)
    c3, p3 = load_validated(a.c3, ex, a.target)
    qual += p1 + p3
    if os.path.realpath(a.c1) == os.path.realpath(a.c3):
        qual.append("the same checkpoint file was supplied for both roles")
    s1, s3 = json.load(open(a.status_c1)), json.load(open(a.status_c3))
    for name, s_, role, fresh in (("C1", s1, "c1", True), ("C3", s3, "c3", False)):
        if s_.get("kind") != role:
            qual.append(f"status {name}: role is {s_.get('kind')!r}, not {role!r}")
        if s_.get("phase") != "final":
            qual.append(f"status {name}: not a terminal status (phase {s_.get('phase')!r})")
        if s_.get("exit") != CONTROL_EXIT:
            qual.append(f"status {name}: exit {s_.get('exit')!r} is not the control's successful end ({CONTROL_EXIT})")
        if s_.get("memory_breach") is not False:
            qual.append(f"status {name}: memory breach recorded or not stated")
        if s_.get("ident") != ex["ident"] or s_.get("code_hash") != ex["code_hash"] or s_.get("policy") != ex["policy"] \
                or s_.get("seed") != ex["seed"] or s_.get("n_rep") != ex["n_rep"]:
            qual.append(f"status {name}: identity/code hash/policy/seed/B are not the frozen task's")
        if s_.get("until") != a.target:
            qual.append(f"status {name}: not bound to the target {a.target}")
        if s_.get("n_damaged", 0):
            qual.append(f"status {name}: damaged records were recomputed")
        if s_.get("target_complete") is not True:
            qual.append(f"status {name}: did not report the target complete")
        bound = [e for e in entries[role] if e.get("job_id")]
        mine = [e for e in bound if e["job_id"] == s_.get("job")]
        if not (isinstance(s_.get("job"), str) and s_.get("job") and mine):
            qual.append(f"status {name}: job {s_.get('job')!r} is not a {role} job bound in the campaign ledger")
        else:
            e = mine[0]
            if s_.get("reservation") != e.get("token"):
                qual.append(f"status {name}: reservation {s_.get('reservation')!r} is not the ledger entry's token {e.get('token')}")
            if os.path.basename(str(s_.get("checkpoint", ""))) != os.path.basename(str(task["ckpt"])):
                qual.append(f"status {name}: checkpoint {os.path.basename(str(s_.get('checkpoint', '')))!r} is not the task's")
            root_b = os.path.basename(str(e.get("root", "")).rstrip("/"))
            ck_root = os.path.basename(os.path.dirname(os.path.dirname(str(s_.get("checkpoint", "")))))
            if root_b != ck_root:
                qual.append(f"status {name}: its checkpoint lies under {ck_root!r}, not the ledger entry's root {root_b!r} (roots compared by basename: pulled paths differ from remote ones)")
            opened = os.path.realpath(a.c1 if role == "c1" else a.c3)                 # the file actually opened for this role
            if os.path.basename(opened) != os.path.basename(str(task["ckpt"])) or os.path.basename(os.path.dirname(opened)) != "ckpt" \
                    or os.path.basename(os.path.dirname(os.path.dirname(opened))) != root_b:
                qual.append(f"--{role}: the opened file {opened!r} is not <{root_b}>/ckpt/{os.path.basename(str(task['ckpt']))} - the evidence this role's status and ledger entry name")
            if s_.get("manifest_sha") != task_sha:
                qual.append(f"status {name}: manifest sha is not the task binding's")
            if role == "c3":
                c2e = [x for x in entries["c2"] if x.get("job_id")]
                if len(c2e) == 1 and os.path.basename(str(c2e[0].get("root", "")).rstrip("/")) != root_b:
                    qual.append(f"status C3: its reservation's root {root_b!r} is not C2's root {os.path.basename(str(c2e[0].get('root', '')).rstrip('/'))!r}")
        if fresh and not (s_.get("n_resumed") == 0 and s_.get("original_cached") is False):
            qual.append("status C1: not a fresh run (something resumed or the original came from a cache)")
        if not fresh and not (_is_int(s_.get("n_resumed")) and s_.get("n_resumed") >= 1 and s_.get("original_cached") is True):
            qual.append("status C3: not a resumed run (nothing resumed, or the original was recomputed)")
    try:
        it = json.load(open(a.interruption))
        c2 = [e for e in entries["c2"] if e.get("job_id")]
        if len(c2) != 1:
            qual.append("ledger: no single bound C2 reservation for this rep")
        else:
            if it.get("job_id") != c2[0]["job_id"]:
                qual.append(f"interruption: job id {it.get('job_id')!r} is not the C2 job bound in the ledger ({c2[0]['job_id']})")
            wr = it.get("walltime_requested_s")
            if not (_is_num(wr) and math.isfinite(wr) and abs(wr - float(c2[0]["walltime_s"])) <= 1.0):
                qual.append(f"interruption: requested walltime {wr!r} is not C2's reserved walltime {c2[0]['walltime_s']}")
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
        qual.append(f"interruption record unreadable: {e}")
    # any failed procedure is non-qualification, independent of parity
    n_failed = sum(1 for r in c1.values() if r["failed"]) + sum(1 for r in c3.values() if r["failed"])
    if n_failed:
        qual.append(f"{n_failed} FAILED resample record(s) across the chains: a failed procedure qualifies nothing, whatever the parity")
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
    print(f"ROW 19 RECOVERY CONTROL, target 0..{a.target-1}, B = {ex['n_rep']}, identity {ex['ident'][:16]}")
    print(f"  C1 {len(c1)} validated record(s), C3 {len(c3)}; validation problems {len(p1) + len(p3)}")
    for x in (p1 + p3)[:20]:
        print("   -", x)
    for x in diffs[:20]:
        print("   -", x)
    print(f"  PARITY: {'AGREE - every scientific field of the resumed chain equals the normal chain on the target' if parity_ok else 'DIFFER or not comparable'}")
    print(f"  QUALIFIED AS A RECOVERY CONTROL: {'YES' if not qual else 'NO'}")
    for x in qual[:24]:
        print("   -", x)
    return (0 if parity_ok else 1) + (0 if not qual else 2)


if __name__ == "__main__":
    sys.exit(main())
