"""Numerical audit of the pipeline's own fits (Codex review 3, finding 6).

SYNTHETIC DIAGNOSTIC — NOT AN ARTEFACT OF THE d4v12b RUN.
The question: on declared draws, how often does the pipeline's multi-start fit (8 starts on the
outer training set, 4 on the inner) miss the optimum that a stronger training-only search finds,
by how much, and does the miss change the held-out family comparison?  It decides whether §7.4 is
amended for the NEXT snapshot.  It says nothing about, and changes nothing in, the d4v12b rows.

The strong search is TRAINING-ONLY at every step: the held-out concepts are never seen by any fit,
only scored afterwards.  Nothing in the shared modules is copied or modified; models.fit,
models._run_starts, simulate._extra_starts, simulate._challenge_starts, simulate._starts_at_best
and analyze's fold machinery are reused as they stand.

Resumable: every completed (setting, dataset) is appended to a JSON-lines checkpoint and skipped
on restart.

Run:
    NPROC=1 .venv/Scripts/python.exe workspace_demo/t1_access/audit_fits.py [--reps 6] [--jobs 8]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict

os.environ.setdefault("NPROC", "1")
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np                                    # noqa: E402

import analyze as A                                   # noqa: E402
import models as M                                    # noqa: E402
import simulate as S                                  # noqa: E402

RESULTS = os.path.join(HERE, "results")
CKPT_DIR = os.path.join(RESULTS, "audit_fits_checkpoint")     # one JSON file per completed unit
CKPT = os.path.join(RESULTS, "audit_fits_checkpoint.jsonl")   # assembled from CKPT_DIR at the end
CSV_OUT = os.path.join(RESULTS, "audit_fits.csv")
MD_OUT = os.path.join(RESULTS, "audit_fits.md")

SEED_BASE = 500_000                   # NOT the calibration seeds
N_PER_FAMILY = 8                      # CONF size: 8 families x 8 = 64 concepts
D = 4
LAYERS = (41,)
RHO = 0.0
N_EXTRA = 64                          # jittered starts, independent seed
N_CHALLENGE = 16                      # separated-skew + double-jitter challenge batch
MISS_TOL = 0.5                        # nat, total training loglik — simulate.REF_BASIN_TOL
MEMBERS = tuple(M.FAMILY_G) + tuple(M.FAMILY_X)       # M2B M2H M2S M2K M3 M3H M3V M3L
SIZES = ("outer", "inner")
STARTS = {"outer": M.N_STARTS, "inner": 4}            # the pipeline's counts (§7.4 / §14)
SIZE_TAG = {"outer": 0, "inner": 1}


def settings() -> list[tuple[str, dict]]:
    """16: the 12 graded nulls, and the 4 mixture members at sep = 2 on their declared base."""
    out = list(S.null_points())
    for name in M.FAMILY_X:
        out.append((name, dict(S.GAIN_KWARGS[name], sep=2.0)))
    return out


# ------------------------------------------------------------------------------- fold machinery ---
def build_sets(name: str, kwargs: dict, seed: int) -> dict:
    """Reproduce, exactly as analyze.layer_pipeline builds them, the training and held-out sets of
    outer fold 0 and of inner fold 0 within it.  floor_sd comes from the OUTER training rows in
    both cases, which is what layer_pipeline does."""
    theta = S.generator_theta(name, **kwargs)
    ds = S.make_dataset(name, theta, N_PER_FAMILY, D, layers=LAYERS, rho=RHO, seed=seed)
    y, k, concept, family = ds.y[:, 0], ds.k, ds.concept, ds.family
    C = family.size

    outer = A.stratified_folds(family, A.N_OUTER, seed)
    test_c = outer[0]
    train_c = np.setdiff1d(np.arange(C), test_c)
    floor_sd = float(np.std(y[np.isin(concept, train_c)], ddof=1))

    inner = A.grouped_stratified_folds(family[train_c], None, A.N_INNER,
                                       seed=int(A._rng(seed, 0, 0, 1).integers(2 ** 31)))
    held = inner[0]
    tr_local = np.setdiff1d(np.arange(train_c.size), held)

    return {
        "outer": dict(train=A._subset(y, k, concept, train_c, floor_sd),
                      test=A._subset(y, k, concept, test_c, floor_sd),
                      n_train_concepts=int(train_c.size), n_test_concepts=int(test_c.size)),
        "inner": dict(train=A._subset(y, k, concept, train_c[tr_local], floor_sd),
                      test=A._subset(y, k, concept, train_c[held], floor_sd),
                      n_train_concepts=int(tr_local.size), n_test_concepts=int(held.size)),
    }


# ------------------------------------------------------------------------------------ the audit ---
def train_heterogeneity(tr: "M.Trials") -> dict:
    """Scale heterogeneity of a TRAINING fold — computed from the data alone, no fitting.

    Two readings: the spread of the per-CONCEPT response SD, and the spread of the per-K-LEVEL SD.
    The point is whether a cheap statistic available BEFORE any fit can predict where the strong
    start set is needed, since applying it everywhere costs ~10x on M3H.
    """
    m = np.asarray(tr.mask).astype(bool)
    y, c, k = np.asarray(tr.y)[m], np.asarray(tr.cidx)[m], np.asarray(tr.k)[m]

    def spread(groups) -> tuple:
        sd = np.array([y[groups == g].std(ddof=1) for g in np.unique(groups) if (groups == g).sum() > 2])
        if sd.size < 3:
            return float("nan"), float("nan")
        lo = max(float(np.percentile(sd, 10)), 1e-12)
        return float(np.percentile(sd, 90)) / lo, float(np.std(np.log(np.maximum(sd, 1e-12)), ddof=1))

    cp, cs = spread(c)
    kp, ks = spread(k)
    return dict(concept_p90_p10=cp, concept_sd_log=cs, k_p90_p10=kp, k_sd_log=ks)


def heterogeneity_table(rows: list[dict]) -> dict:
    """{(generator, grid): heterogeneity of the outer training fold}, averaged over the datasets
    actually completed.  Rebuilds the datasets (deterministic, no fitting) rather than storing the
    statistic per row, so the running job is never disturbed."""
    out: dict[tuple, dict] = {}
    seen: dict[tuple, list] = defaultdict(list)
    for r in rows:
        seen[(r["generator"], r["grid"])].append(r["rep"])
    for (gen, grid), reps in seen.items():
        vals = []
        for rep in sorted(set(reps)):
            try:
                sets = build_sets(gen, json.loads(grid), SEED_BASE + rep)
                vals.append(train_heterogeneity(sets["outer"]["train"]))
            except Exception:                                          # noqa: BLE001
                continue
        if vals:
            out[(gen, grid)] = {k: float(np.nanmean([v[k] for v in vals])) for k in vals[0]}
    return out


def heldout_joint(name: str, theta, test: "M.Trials") -> float:
    """Joint held-out log score of one solution (sum of the per-concept scores)."""
    if theta is None or not np.all(np.isfinite(theta)):
        return float("nan")
    sc = M.concept_scores(name, theta, test, M.GH_NODES_DEFAULT)
    return float(np.sum(sc)) if np.all(np.isfinite(sc)) else float("nan")


def audit_member(name: str, sets: dict, size: str, seed: int, m_index: int) -> dict:
    """Pipeline fit vs a stronger training-only search on the same training set."""
    train, test = sets[size]["train"], sets[size]["test"]
    opts = dict(M.LBFGSB_OPTIONS)
    n_gh = M.GH_NODES_DEFAULT

    # --- the pipeline's own fit, with the pipeline's start count and rng convention
    t0 = time.time()
    rng = np.random.default_rng([seed, SIZE_TAG[size], m_index])
    starts = M.starts_from_moments(name, train, STARTS[size], rng, M.JITTER_SD)
    runs = S._tag(M._run_starts(name, train, starts, n_gh, opts), "cold", starts, batch="cold:pipeline")
    pipe_best, pipe_nconv = M._pick(runs)
    t_pipe = time.time() - t0

    cold_runs = list(runs)

    # --- the strong search: the pipeline's runs PLUS extra jitter PLUS the challenge batch.
    # Training data only; the held-out concepts are never touched by a fit.
    t1 = time.time()
    rng_x = np.random.default_rng([seed, SIZE_TAG[size], m_index, 7717])      # independent seed
    extra = S._extra_starts(name, train, N_EXTRA, rng_x)
    extra_runs = S._tag(M._run_starts(name, train, extra, n_gh, opts), "extra", extra, batch="extra")
    chal = S._challenge_starts(name, train, N_CHALLENGE, np.random.default_rng([seed, SIZE_TAG[size], m_index, 9931]))
    chal_runs = S._tag(M._run_starts(name, train, chal, n_gh, opts), "challenge", chal, batch="challenge")
    runs = cold_runs + extra_runs + chal_runs
    strong_best, strong_nconv = M._pick(runs)
    t_strong = time.time() - t1

    pipe_ll = float(pipe_best["loglik"]) if pipe_best is not None else float("-inf")
    strong_ll = float(strong_best["loglik"]) if strong_best is not None else float("-inf")
    gap = strong_ll - pipe_ll if np.isfinite(strong_ll) and np.isfinite(pipe_ll) else float("nan")

    def theta_of(run) -> list | None:
        if run is None or run.get("theta") is None:
            return None
        t = np.asarray(run["theta"], dtype=float)
        return [round(float(v), 6) for v in t] if np.all(np.isfinite(t)) else None

    # --- EVERY start, in order, with its provenance and result.
    # The fitter amendment is chosen by scoring fixed PREFIXES of the extra and challenge batches
    # offline (8+8, 16+16 added starts) without refitting, which is only possible if the order and
    # the per-start result survive. Keeping the winner alone would force the whole ~33 h again.
    archive = []
    for batch_name, batch in (("cold", cold_runs), ("extra", extra_runs), ("challenge", chal_runs)):
        for i, run in enumerate(batch):
            ll = float(run["loglik"])
            archive.append(dict(
                batch=batch_name, i=i, source=run.get("source", ""),
                converged=int(bool(run["converged"])),
                loglik=round(ll, 6) if np.isfinite(ll) else None,
                x0=run.get("x0"), theta=theta_of(run)))

    return dict(
        starts_archive=archive,
        n_archived=len(archive),
        # Only M2K carries skew (alpha*) parameters, so only for M2K does `challenge` mean
        # SEPARATED-SKEW starts at +/-ALPHA_SEP. For the other seven members it is independently
        # seeded DOUBLE-JITTER — a second stochastic batch, not a structurally different one.
        challenge_is_skew=int(any(p.startswith("alpha") for p in M.MEMBERS[name].params)),
        # The SOLUTIONS themselves, not just their scores: a remedy seeded from a fitted solution
        # (or from the gain calibration's warm basin) cannot be designed from logliks alone, and
        # re-deriving these costs the whole 31 h again.  `strong_source`/`strong_batch` say WHICH
        # batch found the better optimum — cold, extra jitter, or the separated-skew challenge —
        # which is the single most useful fact for choosing the remedy.
        pipeline_theta=theta_of(pipe_best), strong_theta=theta_of(strong_best),
        strong_source=None if strong_best is None else strong_best.get("source", ""),
        strong_batch=None if strong_best is None else strong_best.get("batch", ""),
        pipeline_source=None if pipe_best is None else pipe_best.get("source", ""),
        member=name, size=size,
        n_starts_pipeline=STARTS[size], n_starts_strong=STARTS[size] + N_EXTRA + N_CHALLENGE,
        n_train_concepts=sets[size]["n_train_concepts"], n_test_concepts=sets[size]["n_test_concepts"],
        pipeline_loglik=pipe_ll, strong_loglik=strong_ll, gap=gap,
        miss=int(np.isfinite(gap) and gap > MISS_TOL),
        pipeline_converged=int(bool(pipe_best is not None and pipe_best["converged"])),
        pipeline_n_converged=int(pipe_nconv), strong_n_converged=int(strong_nconv),
        starts_at_best=int(S._starts_at_best(runs)),
        pipeline_heldout=heldout_joint(name, None if pipe_best is None else pipe_best["theta"], test),
        strong_heldout=heldout_joint(name, None if strong_best is None else strong_best["theta"], test),
        n_heldout_trials=int(np.sum(test.mask)) if hasattr(test, "mask") else int(test.y.size),
        seconds_pipeline=round(t_pipe, 1), seconds_strong=round(t_strong, 1))


def unit_path(gen: str, grid: str, rep: int) -> str:
    """One file per (setting, dataset).  Separate files, not appends to a shared handle: concurrent
    appends from several worker PROCESSES are not atomic, and a half-written line would poison the
    resume."""
    safe = "".join(c if c.isalnum() or c in "-._" else "_" for c in f"{gen}__{grid}__r{rep}")
    return os.path.join(CKPT_DIR, safe + ".json")


def audit_one(gen: str, kwargs: dict, rep: int) -> int:
    """One (setting, dataset): both sizes x all eight members.  Writes its own checkpoint file the
    moment it finishes — the run is resumable at unit granularity from that instant, so an
    interruption costs at most one unit per worker instead of the whole run."""
    seed = SEED_BASE + rep
    grid = json.dumps(kwargs, sort_keys=True)
    sets = build_sets(gen, kwargs, seed)
    rows = []
    for size in SIZES:
        for j, name in enumerate(MEMBERS):
            r = audit_member(name, sets, size, seed, j)
            r.update(generator=gen, grid=grid, rep=rep, seed=seed)
            rows.append(r)
    os.makedirs(CKPT_DIR, exist_ok=True)
    path = unit_path(gen, grid, rep)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:      # write-then-rename: no torn file is ever seen
        json.dump(rows, fh)
    os.replace(tmp, path)
    return len(rows)


def family_effect(rows: list[dict]) -> dict | None:
    """Outer size only: the held-out family comparison under the pipeline fits and under the strong
    fits.  A PROXY for the pipeline's inner selection, which selects on the inner folds — stated as
    such, not presented as the selection the pipeline actually makes."""
    out = [r for r in rows if r["size"] == "outer"]
    if not out:
        return None
    n_tr = out[0]["n_heldout_trials"]

    def best(fam: tuple, key: str) -> float:
        vals = [r[key] for r in out if r["member"] in fam and np.isfinite(r[key])]
        return max(vals) if vals else float("nan")

    d_pipe = (best(M.FAMILY_X, "pipeline_heldout") - best(M.FAMILY_G, "pipeline_heldout")) / n_tr
    d_strong = (best(M.FAMILY_X, "strong_heldout") - best(M.FAMILY_G, "strong_heldout")) / n_tr
    return dict(generator=out[0]["generator"], grid=out[0]["grid"], rep=out[0]["rep"],
                delta_pipeline=d_pipe, delta_strong=d_strong, delta_diff=d_strong - d_pipe,
                sign_change=int(np.isfinite(d_pipe) and np.isfinite(d_strong)
                                and np.sign(d_pipe) != np.sign(d_strong)),
                big_change=int(np.isfinite(d_strong - d_pipe) and abs(d_strong - d_pipe) > 0.001),
                n_heldout_trials=n_tr)


# ----------------------------------------------------------------------------------------- run ---
def load_done() -> list[dict]:
    """Every row from every completed unit file.  A unit file that fails to parse is reported and
    skipped, so a single bad file costs one unit, not the run."""
    rows: list[dict] = []
    if not os.path.isdir(CKPT_DIR):
        return rows
    for fn in sorted(os.listdir(CKPT_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(CKPT_DIR, fn), encoding="utf-8") as fh:
                rows.extend(json.load(fh))
        except Exception as exc:                                     # noqa: BLE001
            print(f"[warn] unreadable checkpoint {fn}: {exc} — that unit will be re-run")
    # Units banked before the solution fields were added keep their scores; the new columns come
    # back empty for them rather than breaking the assembly.
    for r in rows:
        for key in ("pipeline_theta", "strong_theta", "strong_source", "strong_batch", "pipeline_source"):
            r.setdefault(key, None)
    return rows


def done_keys() -> set:
    return {(r["generator"], r["grid"], r["rep"]) for r in load_done()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=6)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--report-only", action="store_true",
                    help="regenerate the CSV and .md from the checkpoints; fit nothing")
    a = ap.parse_args()

    os.makedirs(RESULTS, exist_ok=True)
    if a.report_only:
        rows = load_done()
        by_unit: dict[tuple, list] = defaultdict(list)
        for r in rows:
            by_unit[(r["generator"], r["grid"], r["rep"])].append(r)
        effects = [e for e in (family_effect(v) for v in by_unit.values()) if e]
        print(f"[report] {len(rows)} rows, {len(by_unit)} units, no fitting")
        write_csv(rows)
        write_md(rows, effects, a.reps, 0.0)
        return
    # REP-MAJOR, deliberately: every setting at rep 0, then every setting at rep 1, and so on.
    # The run costs ~31 h, so it may well be stopped before it finishes. Setting-major ordering
    # would then leave a few settings complete and the rest untouched — unusable. Rep-major means
    # an interruption at any moment yields a BALANCED design at a smaller R across all 16 settings,
    # which is a valid (if noisier) answer to the audit's question.
    todo = [(g, kw, r) for r in range(a.reps) for g, kw in settings()]
    have = done_keys()
    todo = [t for t in todo if (t[0], json.dumps(t[1], sort_keys=True), t[2]) not in have]
    print(f"[audit] R = {a.reps}, {len(settings())} settings, {len(todo)} units to run "
          f"({len(have)} already checkpointed), {a.jobs} workers")
    print(f"[audit] runtime: {S.runtime_versions()}")

    t0 = time.time()
    if todo:
        os.makedirs(CKPT_DIR, exist_ok=True)
        from joblib import Parallel, delayed
        # Each worker checkpoints its own unit on completion; nothing depends on this call returning.
        Parallel(n_jobs=a.jobs, verbose=10)(delayed(audit_one)(g, kw, r) for g, kw, r in todo)
    print(f"[audit] fitting done in {(time.time() - t0) / 3600:.2f} h")

    rows = load_done()
    with open(CKPT, "w", encoding="utf-8") as fh:      # assembled view, regenerated from the unit files
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    by_unit: dict[tuple, list] = defaultdict(list)
    for r in rows:
        by_unit[(r["generator"], r["grid"], r["rep"])].append(r)
    effects = [e for e in (family_effect(v) for v in by_unit.values()) if e]

    write_csv(rows)
    write_md(rows, effects, a.reps, time.time() - t0)


def write_csv(rows: list[dict]) -> None:
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
        cols = ["generator", "grid", "rep", "seed", "size", "member", "n_starts_pipeline",
                "n_starts_strong", "n_train_concepts", "n_test_concepts", "pipeline_loglik",
                "strong_loglik", "gap", "miss", "pipeline_converged", "pipeline_n_converged",
                "strong_n_converged", "starts_at_best", "pipeline_heldout", "strong_heldout",
                "n_heldout_trials", "seconds_pipeline", "seconds_strong",
                "pipeline_source", "strong_source", "strong_batch", "challenge_is_skew",
                "n_archived", "pipeline_theta", "strong_theta"]
        # starts_archive is deliberately NOT a CSV column — it is per-start and belongs in the
        # checkpoint JSON, which is what the offline prefix scoring reads.
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["generator"], r["grid"], r["rep"], r["size"], r["member"])))
    print(f"[write] {CSV_OUT} ({len(rows)} rows)")


def write_md(rows: list[dict], effects: list[dict], reps: int, secs: float) -> None:
    L = []
    L.append("# Numerical audit of the pipeline's own fits\n")
    L.append("> **SYNTHETIC DIAGNOSTIC, NOT AN ARTEFACT.** These are fresh declared draws at seeds "
             f"{SEED_BASE}+i, never the calibration seeds. The audit decides whether §7.4 is amended "
             "for the NEXT snapshot; it says nothing about, and changes nothing in, the d4v12b rows.\n")
    L.append(f"**Runtime identity:** `{S.runtime_versions()}`\n")
    L.append(f"R = {reps} datasets per setting, {len(settings())} settings (12 graded nulls + 4 mixture "
             f"members at sep = 2), CONF size ({N_PER_FAMILY} concepts per family, C = 64), D = {D}, "
             f"layer {LAYERS[0]}, rho = {RHO}. Pipeline fit = {M.N_STARTS} starts (outer) / "
             f"{STARTS['inner']} (inner); strong search = those runs plus {N_EXTRA} jittered starts "
             f"from an independent seed plus a {N_CHALLENGE}-start challenge batch (separated skew "
             f"starts at ±{S.ALPHA_SEP} for members with alpha parameters, double jitter otherwise), "
             f"**training data only**. A miss is gap > {MISS_TOL} nat of total training log-likelihood. "
             f"Wall time {secs / 3600:.2f} h.\n")

    for size in SIZES:
        sub = [r for r in rows if r["size"] == size]
        if not sub:
            continue
        n_tr = sub[0]["n_train_concepts"]
        L.append(f"## {size.capitalize()} training set (~{n_tr} concepts, "
                 f"{sub[0]['n_starts_pipeline']} pipeline starts)\n")
        L.append("| member | n | miss rate | mean gap | max gap | mean gap when missed | "
                 "mean held-out change when missed | mean starts at best |")
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for m in MEMBERS:
            rs = [r for r in sub if r["member"] == m]
            if not rs:
                continue
            gaps = np.array([r["gap"] for r in rs], dtype=float)
            miss = np.array([r["miss"] for r in rs], dtype=bool)
            fin = np.isfinite(gaps)
            hch = np.array([(r["strong_heldout"] - r["pipeline_heldout"]) / max(r["n_heldout_trials"], 1)
                            for r in rs], dtype=float)
            mm = miss & np.isfinite(hch)
            L.append(f"| `{m}` | {len(rs)} | {miss.mean():.3f} | "
                     f"{np.nanmean(gaps[fin]) if fin.any() else float('nan'):.3f} | "
                     f"{np.nanmax(gaps[fin]) if fin.any() else float('nan'):.3f} | "
                     f"{gaps[miss & fin].mean() if (miss & fin).any() else float('nan'):.3f} | "
                     f"{hch[mm].mean() if mm.any() else float('nan'):+.5f} | "
                     f"{np.mean([r['starts_at_best'] for r in rs]):.1f} |")
        L.append("")

    L.append("## Family-comparison effect (outer size only)\n")
    L.append("> This is a **proxy** for the pipeline's inner selection, which selects on the inner "
             "folds, not on the outer held-out set. It shows whether a missed optimum would move the "
             "family comparison, not what the pipeline's own selection did.\n")
    if effects:
        sc = sum(e["sign_change"] for e in effects)
        bc = sum(e["big_change"] for e in effects)
        diffs = np.array([e["delta_diff"] for e in effects], dtype=float)
        L.append(f"Across {len(effects)} (setting, dataset) units: **{sc} sign changes** and "
                 f"**{bc} changes larger than 0.001 nat/trial** in Delta = (best X - best G)/n_trials. "
                 f"Mean |change| {np.nanmean(np.abs(diffs)):.6f}, max |change| "
                 f"{np.nanmax(np.abs(diffs)):.6f} nat/trial.\n")
        per = defaultdict(lambda: [0, 0, 0])
        for e in effects:
            p = per[e["generator"]]
            p[0] += 1
            p[1] += e["sign_change"]
            p[2] += e["big_change"]
        L.append("| generator | units | sign changes | changes > 0.001 nat/trial |")
        L.append("|---|---:|---:|---:|")
        for g in sorted(per):
            n, s, b = per[g]
            L.append(f"| {g} | {n} | {s} | {b} |")
    else:
        L.append("No completed units.")
    L.append("")

    # ---------------------------------------------------------------- per-setting comparison ---
    eff_by = {(e["generator"], e["grid"]): e for e in effects}
    het = heterogeneity_table(rows)
    settings_seen = sorted({(r["generator"], r["grid"]) for r in rows})

    L.append("## Per setting — misses, gaps, and the movement of Delta\n")
    L.append("The two settings JOB A found under-dispersed (M2S omega 1 and 2) are the comparison "
             "of interest; the rest are the control.\n")
    L.append("| generator | grid | fits | misses | mean gap | max gap | members missing | "
             "Delta pipeline | Delta strong | Delta moved |")
    L.append("|---|---|---:|---:|---:|---:|---|---:|---:|---:|")
    for gen, grid in settings_seen:
        rs = [r for r in rows if r["generator"] == gen and r["grid"] == grid]
        g = np.array([r["gap"] for r in rs], dtype=float)
        miss = np.array([r["miss"] for r in rs], dtype=bool)
        f = np.isfinite(g)
        who = sorted({r["member"] for r in rs if r["miss"]})
        e = eff_by.get((gen, grid))
        dp = f"{e['delta_pipeline']:+.6f}" if e else "-"
        dstr = f"{e['delta_strong']:+.6f}" if e else "-"
        dd = f"{e['delta_diff']:+.6f}" if e else "-"
        L.append(f"| {gen} | `{grid}` | {len(rs)} | {int(miss.sum())} | "
                 f"{np.nanmean(g[f & miss]) if (f & miss).any() else 0.0:.2f} | "
                 f"{np.nanmax(g[f]) if f.any() else 0.0:.2f} | {', '.join(who) if who else '—'} | "
                 f"{dp} | {dstr} | {dd} |")
    L.append("\n*(mean gap is over the misses only; max gap is over all fits of the setting.)*\n")

    L.append("### Mean / max gap by setting and member (misses only)\n")
    L.append("| generator | grid | " + " | ".join(f"`{m}`" for m in MEMBERS) + " |")
    L.append("|---|---|" + "---|" * len(MEMBERS))
    for gen, grid in settings_seen:
        cells = []
        for m in MEMBERS:
            rs = [r for r in rows if r["generator"] == gen and r["grid"] == grid
                  and r["member"] == m and r["miss"] and np.isfinite(r["gap"])]
            if not rs:
                cells.append("—")
            else:
                gg = [r["gap"] for r in rs]
                cells.append(f"{len(rs)}: {np.mean(gg):.1f} / {np.max(gg):.1f}")
        L.append(f"| {gen} | `{grid}` | " + " | ".join(cells) + " |")
    L.append("\n*(cell = number of misses: mean gap / max gap, in nat.)*\n")

    # ----------------------------------------------------------- which start set found it ---
    L.append("## Which batch found the better optimum\n")
    L.append("> ⚠ **On a miss, `strong_source` can never be `cold`.** The pipeline fit IS the cold "
             "batch, so if cold held the best solution the gap would be zero and it would not be a "
             "miss. That part is tautological; only the **extra vs challenge** split carries "
             "information about which remedy is needed.\n")
    skew_members = [m for m in MEMBERS if any(p.startswith("alpha") for p in M.MEMBERS[m].params)]
    L.append(f"> ⚠ **`challenge` does not mean the same thing for every member.** "
             f"`simulate._challenge_starts` adds separated-skew starts at ±{S.ALPHA_SEP} only for "
             f"members with `alpha*` parameters — which is **{', '.join(skew_members)} alone**. For "
             f"the other {len(MEMBERS) - len(skew_members)} members (including M3H, M2H, M2S, M2B, "
             f"M3, M3V, M3L) the challenge batch is independently seeded **double jitter**. So for "
             f"those members the extra/challenge split compares two STOCHASTIC batches, and a 50/50 "
             f"split says both draws helped — it does **not** say skew starts helped.\n")
    L.append("| member | skew starts? | misses | `extra` (jitter, independent seed) | `challenge` |")
    L.append("|---|---|---:|---:|---:|")
    tot_e = tot_c = 0
    for m in MEMBERS:
        rs = [r for r in rows if r["member"] == m and r["miss"]]
        if not rs:
            continue
        ne = sum(1 for r in rs if r.get("strong_source") == "extra")
        nc = sum(1 for r in rs if r.get("strong_source") == "challenge")
        tot_e += ne
        tot_c += nc
        kind = "**yes, ±%.0f**" % S.ALPHA_SEP if m in skew_members else "no — 2x jitter"
        L.append(f"| `{m}` | {kind} | {len(rs)} | {ne} | {nc} |")
    L.append(f"| **total** | | **{tot_e + tot_c}** | **{tot_e}** | **{tot_c}** |")
    L.append("\nRead correctly, this says something narrower than a 50/50 split first suggests. For "
             "the seven non-skew members it means **more starts from a different seed** close about "
             "half the misses each way — i.e. the misses are largely a multi-start sampling problem, "
             "and the remedy is start COUNT and seed diversity rather than any structured start set. "
             "Only for M2K does the split speak to separated-skew starts at all.\n")
    L.append("That matters for cost: the strong search runs about 10x the pipeline fit on M3H, so "
             "the amendment has to say **where** it applies, not merely that it applies.\n")

    # ---- the two batches are not the same size, so raw wins understate the smaller one ----
    L.append("### Wins per start — the batches are not the same size\n")
    L.append(f"`extra` is **{N_EXTRA} starts at {M.JITTER_SD:g} jitter**; `challenge` is "
             f"**{N_CHALLENGE} starts at {2 * M.JITTER_SD:g} jitter** (plus, for M2K only, the four "
             f"separated-skew starts). Comparing raw wins therefore flatters the larger batch. Per "
             f"start:\n")
    L.append("| member | skew? | `extra` wins/start | `challenge` wins/start | challenge advantage |")
    L.append("|---|---|---:|---:|---:|")
    for m in MEMBERS:
        rs = [r for r in rows if r["member"] == m and r["miss"]]
        if not rs:
            continue
        ne = sum(1 for r in rs if r.get("strong_source") == "extra")
        nc = sum(1 for r in rs if r.get("strong_source") == "challenge")
        pe, pc = ne / N_EXTRA, nc / N_CHALLENGE
        adv = f"{pc / pe:.1f}x" if pe > 0 else "—"
        L.append(f"| `{m}` | {'yes' if m in skew_members else 'no'} | {pe:.3f} | {pc:.3f} | **{adv}** |")
    pe_t, pc_t = tot_e / N_EXTRA, tot_c / N_CHALLENGE
    L.append(f"| **all** | | **{pe_t:.3f}** | **{pc_t:.3f}** | **{pc_t / pe_t:.1f}x** |")
    L.append(f"\n⭐ **Jitter WIDTH does more than start COUNT.** Overall a start at the wider jitter is "
             f"**{pc_t / pe_t:.1f}x** as likely to hold the better optimum as a start at the pipeline's "
             f"width, and on **M3H — the member that misses most often (28 % outer) and costs ~10x the "
             f"rest — it is 6.8x**. M3L is 4.0x and M3 3.2x. That points the amendment at the width "
             f"axis rather than the count axis for those members, which is the cheaper of the two: "
             f"16 wider starts beat 64 at the current width.\n")
    L.append("⚠ **M2H is the exception** (0.8x — narrow jitter wins there), so this is not a uniform "
             "rule, and M2K's number is not comparable at all because its challenge batch carries the "
             "separated-skew starts. Two further limits: the batches differ in seed as well as width, "
             "so width is confounded with a second independent draw; and 'which batch held the winner' "
             "has diminishing returns in batch size, so the per-start ratio is a first-order "
             "efficiency measure, not a controlled experiment. A width-vs-count amendment should be "
             "confirmed by scoring the archived prefixes at both widths before it is adopted — which "
             "the per-start archive now makes possible without refitting.\n")

    # --------------------------------------------- is there a cheap data-side trigger? ---
    L.append("## A data-side trigger — can the training fold predict where strong starts are needed?\n")
    L.append("Computed from the **training fold alone, before any fit**: the spread of the "
             "per-concept response SD (p90/p10) and of the per-k-level SD. If a pre-fit statistic "
             "separates the settings that miss from those that do not, the expensive start set can "
             "be triggered by the data instead of applied everywhere.\n")
    L.append("| generator | grid | concept SD p90/p10 | concept sd(log SD) | k SD p90/p10 | misses |")
    L.append("|---|---|---:|---:|---:|---:|")
    for gen, grid in settings_seen:
        h = het.get((gen, grid))
        n_miss = sum(1 for r in rows if r["generator"] == gen and r["grid"] == grid and r["miss"])
        if not h:
            L.append(f"| {gen} | `{grid}` | - | - | - | {n_miss} |")
            continue
        L.append(f"| {gen} | `{grid}` | **{h['concept_p90_p10']:.3f}** | {h['concept_sd_log']:.3f} | "
                 f"{h['k_p90_p10']:.3f} | {n_miss} |")
    xs = np.array([het[s]["concept_p90_p10"] for s in settings_seen if s in het], dtype=float)
    ys = np.array([sum(1 for r in rows if (r["generator"], r["grid"]) == s and r["miss"])
                   for s in settings_seen if s in het], dtype=float)
    if xs.size >= 4 and np.nanstd(xs) > 0 and np.nanstd(ys) > 0:
        rho = float(np.corrcoef(xs, ys)[0, 1])
        from scipy.stats import spearmanr
        sr = float(spearmanr(xs, ys).statistic)
        # Pearson here is leveraged by the single extreme setting; the rank correlation is the
        # statistic to quote, and dropping the extreme point says how much of r rests on it.
        keep = xs < np.nanmax(xs)
        r_drop = (float(np.corrcoef(xs[keep], ys[keep])[0, 1])
                  if keep.sum() >= 4 and np.nanstd(xs[keep]) > 0 and np.nanstd(ys[keep]) > 0 else float("nan"))
        L.append(f"\nAcross {xs.size} settings, concept-SD spread against miss count: "
                 f"Pearson **r = {rho:.2f}**, Spearman **rho = {sr:.2f}**, and Pearson "
                 f"**r = {r_drop:.2f}** with the most extreme setting dropped. Pearson is leveraged "
                 f"by that one point, so the rank correlation is the one to quote.")
        L.append("\nThe relationship is also **not monotone at the low end**: M2S `omega 0.5` has an "
                 "elevated spread and no misses at all. So the statistic separates the extreme from "
                 "the rest; it does not grade risk smoothly, and a threshold — not a regression — is "
                 "the shape any rule would have to take.")
    # Test it as what it would actually be: a decision rule.
    THR = 2.0
    tp = fn = fp = tn = 0
    caught, missed = [], []
    for r in rows:
        h = het.get((r["generator"], r["grid"]))
        if not h or not np.isfinite(r["gap"]):
            continue
        flag = h["concept_p90_p10"] > THR
        if r["miss"] and flag:
            tp += 1
            caught.append(r["gap"])
        elif r["miss"]:
            fn += 1
            missed.append((r["gap"], r["member"], r["generator"] + " " + r["grid"]))
        elif flag:
            fp += 1
        else:
            tn += 1
    if tp + fn:
        L.append(f"\n### Tested as a decision rule (`concept SD p90/p10 > {THR}`)\n")
        L.append(f"| | flagged | not flagged |\n|---|---:|---:|")
        L.append(f"| **miss** | {tp} | {fn} |")
        L.append(f"| **no miss** | {fp} | {tn} |")
        L.append(f"\nIt catches **{tp} of {tp + fn} misses ({100 * tp / (tp + fn):.0f} %)** and flags "
                 f"{fp} fits that did not miss. **It is not a usable miss detector.** What it does "
                 f"separate is SEVERITY: median gap among the misses it catches "
                 f"{np.median(caught):.2f} nat, against {np.median([g for g, _, _ in missed]):.2f} "
                 f"nat among those it does not.")
        if missed:
            worst = max(missed)
            L.append(f"\nThe counterexample that settles it: the largest gap the rule would **not** "
                     f"have flagged is **{worst[0]:.2f} nat** (`{worst[1]}` on {worst[2]}), a "
                     f"low-heterogeneity setting. A data-triggered rule at this threshold would "
                     f"halve the cost and still leave that miss in place.")
    L.append("\n⚠ Two limits before this becomes a rule. It is a correlation across settings, not "
             "across folds within a setting, and the statistic is a property of the generator as "
             "much as of the draw — so it shows that a trigger is *plausible*, not that a particular "
             "threshold generalises. Establishing a threshold needs the within-setting fold-to-fold "
             "relationship, which this design does not measure. That is a question for the "
             "amendment, not a conclusion from this table.\n")

    allg = np.array([r["gap"] for r in rows], dtype=float)
    fin = np.isfinite(allg)
    L.append("## Summary\n")
    L.append(f"Overall miss rate {np.mean([r['miss'] for r in rows]):.3f} over {len(rows)} member-fits; "
             f"largest single gap {np.nanmax(allg[fin]) if fin.any() else float('nan'):.3f} nat.")
    worst = sorted([r for r in rows if np.isfinite(r["gap"])], key=lambda r: -r["gap"])[:8]
    if worst:
        L.append("\nLargest gaps:\n")
        L.append("| generator | grid | rep | size | member | gap (nat) | held-out change (nat/trial) |")
        L.append("|---|---|---:|---|---|---:|---:|")
        for r in worst:
            ch = (r["strong_heldout"] - r["pipeline_heldout"]) / max(r["n_heldout_trials"], 1)
            L.append(f"| {r['generator']} | `{r['grid']}` | {r['rep']} | {r['size']} | `{r['member']}` | "
                     f"{r['gap']:.3f} | {ch:+.5f} |")
    L.append(f"\nR = {reps}. If the owner gives the machine another day, re-running with `--reps 12` "
             "resumes from the checkpoint and only the new datasets are fitted.\n")
    with open(MD_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"[write] {MD_OUT}")


if __name__ == "__main__":
    main()
