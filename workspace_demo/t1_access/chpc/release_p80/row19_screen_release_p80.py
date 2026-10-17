"""Ledger row 19, the RESIZED screen: the first-80 PREFIX release consumer (CANDIDATE, not adopted).

Design: `reviews/2026-10-17_row19_resize_codex.md` ss.1, 2, 5 and 6 item 3; PREREGISTRATION_T1_model.md s.10.1, "Amendment of
17 October 2026"; chpc/ROW19_SCREEN_DECLARATIONS.md, "Owner adoption of the resized screen". The adopted B = 200 consumer
(`chpc/row19_screen_release.py`) is NOT changed and stays the only consumer of the declared 100 x B = 200 screen; this module is
a separate consumer with its own adoption schema, its own review literal and its own pins, so neither consumer can release under
the other's adoption.

WHAT IS SCREENED. For each of the 60 designated datasets S = {r in 3..102 : (r - 3) mod 5 in {0, 1, 2}} the interval is the
2.5 % / 97.5 % percentile interval (np.percentile, default linear interpolation, exactly the expression of
analyze.refit_bootstrap) over the FIRST 80 records (indices 0..79) of that dataset's UNCHANGED B = 200 producer stream. The
producer's B stays 200: every record is validated against the dataset's original B = 200 task (its manifest-declared parent
identity, which hashes B = 200 and the folds; its seed; n_rep = 200; its own index; the row of the B = 200 draw matrix it must
have drawn; its checksum) and nothing is relabelled, re-drawn or re-identified. B = 80 is the procedure screened, not an
approximation of B = 200 (design s.1).

THE SEAL (all before any statistic is computed; any failure REFUSES and computes nothing):
  1. The adopted consumer's whole seal, unchanged (`row19_screen_release.seal_problems`: target bytes, RESOLVED status, bank
     binding and record set recomputed, both seed domains, controller lineage, consumer pins, manifests), run with THIS
     consumer's adoption schema (`row19-p80-adoption-1`) and THIS consumer's pin list (the adopted list plus this module).
  2. The adoption's `prefix_contract` equals this module's CONTRACT exactly (parent B 200, prefix 80, the 60 designated IDs
     and their rule, refit_min_usable 1.0, 98.5 % one-sided CP, floor 0.90, one terminal look), and the screen manifest is
     that contract's producer (interval refit, n_boot_refit 200, refit_min_usable 1.0, every designated ID declared with an
     identity).
  3. A separate git-tracked, unmodified release review record carries
     `ADOPT row19-p80-release consumer=<sha256 of this file> target=<target sha256> contract=<contract sha256> verdict=FAVOURABLE`.
COLLECTION (validation only, no statistic): per designated dataset, the original (lossless cache, read back) and the records
at indices 0..79. An unacceptable record or cache HOLDS (wrong parent, seed, B, draw, index or checksum - it is never
skipped). Out-of-prefix records (80..199) are not read: they stay history and earn no credit.
TERMINALITY (one look): a decision is emitted only when ALL 60 datasets are terminal - complete (original valid and 80 valid
records), original failed (recorded reason), or every missing coordinate declared RESCUE-EXHAUSTED in a git-tracked terminal
document (schema row19-p80-terminal-1) with a reason and attempt provenance. Otherwise NOT TERMINAL: the non-terminal
coordinates are listed and no interval, count or decision is computed. A declaration naming a coordinate that holds a valid
record, an undesignated dataset or an index outside 0..79 HOLDS (never relabel a record as missing).
AGGREGATION (only after seal + terminality; analyze.run_dataset raises throughout, so nothing can be fitted): per dataset and
predictor, the 80 statistics; usable only when ALL 80 scored (refit_min_usable = 1.0 over the 80; never the first 80
successes, never a substitute index); the cluster companion interval from the cached original's fixed scores
(analyze.band_bootstrap, exactly as analyze.analyze_dataset computes it - independent of B).
DECISION per method (refit = the screened procedure, cluster = its companion), n_attempted = 60: K_max / K_min over the frozen
T (every endpoint inside T, both ends of T, a point inside every segment; inclusive ties - the adopted consumer's k_max);
STOP FOR FUTILITY iff the one-sided 98.5 % Clopper-Pearson upper bound at (K_max, n_usable) < 0.90 AND the all-60 bound at
(K_max + M, 60) < 0.90, M = 60 - n_usable; otherwise "not ruled out at this look"; never PASS. Reported: [K_min/n, K_max/n],
the exact 98.5 % one-sided bounds each way at both, the attempted-set envelope [K_min/60, (K_max + M)/60] with its bounds,
failures, M and the paired partition. The bank's point mean is never substituted for T.

    t1py chpc/release_p80/row19_screen_release_p80.py --screen chpc/row19_screen_manifest.json \\
        --originals chpc/row19_screen_orig_manifest.json --target <frozen target> --adoption reviews/<p80 adoption>.json \\
        [--terminal reviews/<terminal declaration>.json] [--out <result.json>]
"""
import os, sys, json, math, hashlib, argparse, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.abspath(os.path.join(HERE, ".."))
T1 = os.path.abspath(os.path.join(CHPC, ".."))
for p in (T1, CHPC):
    if p not in sys.path:
        sys.path.insert(0, p)

import row19_screen_release as R                    # the adopted consumer: its seal, k_max and helpers are reused unchanged

ADOPTION_SCHEMA = "row19-p80-adoption-1"
TERMINAL_SCHEMA = "row19-p80-terminal-1"
RESULT_SCHEMA = "row19-p80-result-1"
SELF_REL = "chpc/release_p80/row19_screen_release_p80.py"
CONSUMER_FILES = tuple(R.CONSUMER_FILES) + (SELF_REL,)
PRIMARY = R.PRIMARY

PARENT_B = 200
PREFIX = 80
REFIT_MIN_USABLE = 1.0
CP_CONF = 0.985
FLOOR = 0.90
DESIGNATED = tuple(r for r in range(3, 103) if (r - 3) % 5 in (0, 1, 2))
N_DESIGNATED = 60
assert len(DESIGNATED) == N_DESIGNATED and 83 in DESIGNATED
CONTRACT = dict(schema="row19-p80-contract-1", parent_B=PARENT_B, prefix=PREFIX, prefix_indices="0..79",
                designated_rule="r in 3..102, (r - 3) mod 5 in {0, 1, 2}", designated=list(DESIGNATED), n_attempted=N_DESIGNATED,
                refit_min_usable=REFIT_MIN_USABLE, percentile="numpy.percentile default linear, 2.5 and 97.5",
                cp_one_sided_conf=CP_CONF, floor=FLOOR, attempted_set_guard="cp_upper(Kmax + M, 60) < floor also required",
                looks=1, primary="/".join(PRIMARY))


def contract_sha():
    return hashlib.sha256(json.dumps(CONTRACT, sort_keys=True).encode()).hexdigest()


def release_literal(target_sha):
    return (f"ADOPT row19-p80-release consumer={R.sha_file(os.path.join(T1, SELF_REL))} target={target_sha} "
            f"contract={contract_sha()} verdict=FAVOURABLE")


# ------------------------------------------------------------------------------------------------------------------------
# exact binomial bounds and the decision (pure; no data)
# ------------------------------------------------------------------------------------------------------------------------
def cp_upper(k, n, conf=CP_CONF):
    """One-sided exact (Clopper-Pearson) upper confidence bound for a binomial proportion at k of n."""
    from scipy.stats import beta
    if not (isinstance(k, int) and isinstance(n, int) and 0 <= k <= n and n > 0):
        raise ValueError(f"cp_upper needs integers 0 <= k <= n, n > 0 (got {k}, {n})")
    return 1.0 if k >= n else float(beta.ppf(conf, k + 1, n - k))


def cp_lower(k, n, conf=CP_CONF):
    from scipy.stats import beta
    if not (isinstance(k, int) and isinstance(n, int) and 0 <= k <= n and n > 0):
        raise ValueError(f"cp_lower needs integers 0 <= k <= n, n > 0 (got {k}, {n})")
    return 0.0 if k <= 0 else float(beta.ppf(1.0 - conf, k, n - k + 1))


def _candidates(intervals, lo, hi):
    """Exactly the adopted consumer's candidate set: every endpoint inside T, both ends of T, the midpoint of every segment."""
    pts = sorted({lo, hi} | {x for a, b in intervals for x in (a, b) if lo <= x <= hi})
    return list(pts) + [(pts[k] + pts[k + 1]) / 2.0 for k in range(len(pts) - 1)]


def k_max(intervals, lo, hi):
    return R.k_max(intervals, lo, hi)


def k_min(intervals, lo, hi):
    """The smallest number of intervals containing any theta in T (inclusive): the count is piecewise constant between
    candidate points, so the minimum over the same candidate set is exact."""
    return min((sum(1 for a, b in intervals if a <= th <= b) for th in _candidates(intervals, lo, hi)), default=0)


def decide(intervals, lo, hi, n_attempted=N_DESIGNATED, all_terminal=False):
    """The one terminal look. `intervals` are the usable intervals of the n_attempted designated datasets."""
    if not all_terminal:
        return dict(decision="REFUSED: not every designated dataset is terminal; no decision at this point")
    n = len(intervals); M = int(n_attempted) - n
    if M < 0:
        raise ValueError("more usable intervals than attempted datasets")
    base = dict(n_attempted=int(n_attempted), n_usable=n, M_unavailable=M, cp_one_sided_conf=CP_CONF, floor=FLOOR)
    if n == 0:
        return dict(base, k_max=None, k_min=None, decision="unresolved: no usable interval")
    kx, kn = k_max(intervals, lo, hi), k_min(intervals, lo, hi)
    up = cp_upper(kx, n); up_all = cp_upper(kx + M, int(n_attempted))
    stop = up < FLOOR and up_all < FLOOR
    return dict(base, k_max=kx, k_min=kn, coverage_range=[kn / n, kx / n],
                exact=dict(k_max=dict(lower=cp_lower(kx, n), upper=up), k_min=dict(lower=cp_lower(kn, n), upper=cp_upper(kn, n))),
                attempted_envelope=dict(range=[kn / n_attempted, (kx + M) / n_attempted],
                                        lower_at_k_min=cp_lower(kn, int(n_attempted)), upper_at_k_max_plus_M=up_all),
                upper=up, upper_all_attempted=up_all, complete_case_fails=up < FLOOR, attempted_set_fails=up_all < FLOOR,
                decision="STOP FOR FUTILITY" if stop else "not ruled out at this look")


# ------------------------------------------------------------------------------------------------------------------------
# the prefix interval (pure; the expression of analyze.refit_bootstrap over the designated records)
# ------------------------------------------------------------------------------------------------------------------------
def prefix_interval(records, n, bands, predictors=None, min_usable=REFIT_MIN_USABLE):
    """Per predictor: n_used / n_failed / usable / per-band lo, hi, se over the n designated records, exactly as
    analyze.refit_bootstrap computes them (a record is used for a predictor only when not failed and every band finite;
    usable only when at least min_usable x n are used). `records` must be exactly the n designated records."""
    import numpy as np, analyze as A
    predictors = A.PREDICTORS if predictors is None else predictors
    if len(records) != n or sorted(int(s["rep"]) for s in records) != list(range(n)):
        raise ValueError(f"a prefix interval needs exactly the records of indices 0..{n - 1}")
    reps = sorted(records, key=lambda s: s["rep"])
    out = {}
    for p in predictors:
        ok = [s for s in reps if not s["failed"] and all(np.isfinite(s["stats"][p][b]) for b in bands)]
        usable = bool(ok) and len(ok) >= min_usable * n
        pr = dict(n_used=len(ok), n_failed=int(n - len(ok)), usable=usable, bands={})
        for b in bands:
            if usable:
                v = np.array([s["stats"][p][b] for s in ok])
                pr["bands"][b] = dict(lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)), se=float(np.std(v, ddof=1)))
            else:
                pr["bands"][b] = dict(lo=float("nan"), hi=float("nan"), se=float("nan"))
        out[p] = pr
    return out


# ------------------------------------------------------------------------------------------------------------------------
# the seal
# ------------------------------------------------------------------------------------------------------------------------
@contextlib.contextmanager
def _as_p80_consumer():
    """Run the adopted seal with this consumer's adoption schema and pin list; restored in every case."""
    keep = (R.ADOPTION_SCHEMA, R.CONSUMER_FILES)
    R.ADOPTION_SCHEMA, R.CONSUMER_FILES = ADOPTION_SCHEMA, CONSUMER_FILES
    try:
        yield
    finally:
        R.ADOPTION_SCHEMA, R.CONSUMER_FILES = keep


def contract_problems(screen):
    """The screen manifest must be this contract's producer: B = 200 refit, min_usable 1.0, every designated ID declared."""
    why = []
    c = screen.get("cfg") or {}
    if c.get("interval") != "refit":
        why.append("the screen manifest's interval is not refit")
    if not (isinstance(c.get("n_boot_refit"), int) and not isinstance(c.get("n_boot_refit"), bool) and c["n_boot_refit"] == PARENT_B):
        why.append(f"the producer's B is {c.get('n_boot_refit')!r}, not the parent B {PARENT_B} (producer B stays 200)")
    if c.get("refit_min_usable") != REFIT_MIN_USABLE:
        why.append(f"the producer's refit_min_usable is {c.get('refit_min_usable')!r}, not 1.0")
    reps = [int(x) for x in (screen.get("datasets") or {}).get("reps", [])]
    missing = [r for r in DESIGNATED if r not in reps]
    if missing:
        why.append(f"designated datasets not declared by the screen manifest: {missing[:5]}")
    ids = (screen.get("datasets") or {}).get("identities") or {}
    noid = [r for r in DESIGNATED if not ids.get(str(r))]
    if noid:
        why.append(f"designated datasets without a declared parent identity: {noid[:5]}")
    return why


def seal_problems(screen_path, orig_path, target, adoption_rel, check_git=True):
    with _as_p80_consumer():
        why = R.seal_problems(screen_path, orig_path, None, adoption_rel, check_git=check_git, target=target)
    try:
        ad = json.load(open(os.path.join(T1, adoption_rel)))
    except Exception as e:
        return why + [f"the adoption document is unreadable ({e})"]
    if ad.get("prefix_contract") != CONTRACT:
        why.append("the adoption's prefix_contract is not this consumer's contract")
    if ad.get("prefix_contract_sha256") != contract_sha():
        why.append("the adoption does not name this contract's SHA-256")
    rr = ad.get("release_review_record") or {}
    rr_full = os.path.join(T1, rr.get("path", "") or "_none_")
    if not os.path.exists(rr_full) or R.sha_file(rr_full) != rr.get("sha256") or (check_git and not R.tracked_unmodified(rr.get("path", ""))):
        why.append("the prefix release review record is not tracked and unmodified with the adopted SHA-256")
    elif release_literal(target[0]) not in [l.strip() for l in open(rr_full).read().splitlines()]:
        why.append("the prefix release review record does not carry its ADOPT row19-p80-release line for this consumer, target and contract")
    try:
        why += contract_problems(json.load(open(screen_path)))
    except Exception as e:
        why.append(f"the screen manifest is unreadable ({e})")
    return why


# ------------------------------------------------------------------------------------------------------------------------
# collection and terminality (validation only; no statistic)
# ------------------------------------------------------------------------------------------------------------------------
def terminal_declarations(terminal_rel, check_git=True):
    """{(rep, index-or-'original'): entry} from the terminal document, or (None, problems)."""
    if terminal_rel is None:
        return {}, [], None
    full = os.path.join(T1, terminal_rel)
    if not os.path.exists(full):
        return None, ["the terminal declaration is absent"], None
    if check_git and not R.tracked_unmodified(terminal_rel):
        return None, ["the terminal declaration is not git-tracked and unmodified"], None
    sha = R.sha_file(full)
    try:
        doc = json.load(open(full))
    except Exception as e:
        return None, [f"the terminal declaration is unreadable ({e})"], sha
    why, out = [], {}
    if doc.get("schema") != TERMINAL_SCHEMA:
        why.append("the terminal declaration has another schema")
    for e in doc.get("rescue_exhausted") or []:
        rep, idx = e.get("rep"), e.get("index")
        if not (isinstance(rep, int) and not isinstance(rep, bool) and rep in DESIGNATED):
            why.append(f"a terminal entry names an undesignated dataset {rep!r}"); continue
        if not (idx == "original" or (isinstance(idx, int) and not isinstance(idx, bool) and 0 <= idx < PREFIX)):
            why.append(f"a terminal entry for rep {rep} names index {idx!r}, outside the prefix 0..{PREFIX - 1}"); continue
        if not (isinstance(e.get("reason"), str) and e["reason"].strip()):
            why.append(f"rep {rep} index {idx}: no recorded reason"); continue
        att = e.get("attempts")
        if not (isinstance(att, list) and att and all(isinstance(a, str) and a.strip() for a in att)):
            why.append(f"rep {rep} index {idx}: no attempt provenance"); continue
        if (rep, idx) in out:
            why.append(f"rep {rep} index {idx}: declared twice"); continue
        out[(rep, idx)] = dict(reason=e["reason"], attempts=list(att))
    return out, why, sha


def collect(screen, origm):
    """Per designated dataset: the validated original (or its absence) and the validated records 0..79. Problems HOLD."""
    import numpy as np, analyze as A, row19_shard as SH, row19_screen_orig as O
    why, items = [], {}
    for r in DESIGNATED:
        try:
            t = O.task_checked(screen, r)                           # the manifest-declared PARENT identity (hashes B = 200)
        except ValueError as e:
            why.append(str(e)); continue
        if int(t["n_rep"]) != PARENT_B or t["idx"].shape[0] != PARENT_B:
            why.append(f"rep {r}: the task's B is {t['n_rep']}, not the parent {PARENT_B}"); continue
        if A.dataset_identity(t["ds"], t["cfg"], t["seed"], PARENT_B, t["folds"]) != t["ident"]:
            why.append(f"rep {r}: the parent identity does not recompute at B = {PARENT_B}"); continue
        if not np.array_equal(A.stratified_resample(t["ds"].family, PARENT_B, np.random.default_rng(t["seed"])), t["idx"]):
            why.append(f"rep {r}: the draw matrix is not the B = {PARENT_B} stream of the dataset seed"); continue
        try:
            got, _ = O.read_cache(origm["storage"]["root"], t)
        except ValueError as e:
            why.append(str(e)); continue
        recs, missing, bad = [], [], False
        for i in range(PREFIX):
            p = SH.record_path(screen["storage"]["root"], r, i)
            try:
                d = SH.read_record(p, t, i)                        # parent ident, seed, n_rep 200, index, draw row, checksum
            except ValueError as e:
                why.append(f"rep {r}: {e}"); bad = True; continue
            if d is None:
                missing.append(i); continue
            if not (d["ident"] == t["ident"] and d["seed"] == t["seed"] and d["n_rep"] == PARENT_B and d["rep"] == i
                    and d["chosen"] == [int(c) for c in t["idx"][i]]):
                why.append(f"rep {r}: record {i} is not of the parent B = {PARENT_B} task"); bad = True; continue
            recs.append(d)
        if not bad:
            items[r] = dict(task=t, original=got, records=recs, missing=missing)
    return why, items


def terminality(items, decl):
    """(per-dataset terminal state, non-terminal list, conflicts). No statistic is read."""
    state, open_, conflict = {}, [], []
    for (r, i), _ in sorted(decl.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        it = items.get(r)
        if it is None:
            continue
        if i == "original" and it["original"] is not None:
            conflict.append(f"rep {r}: declared original rescue-exhausted but a valid original exists")
        if isinstance(i, int) and i not in it["missing"]:
            conflict.append(f"rep {r}: index {i} declared rescue-exhausted but holds a valid record (never relabelled)")
    for r in DESIGNATED:
        it = items[r]
        if it["original"] is None:
            if (r, "original") in decl:
                state[r] = dict(terminal="original rescue-exhausted", reason=decl[(r, "original")]["reason"])
            else:
                open_.append(f"rep {r}: no original")
            continue
        if bool(it["original"]["run"]["failed"]):
            state[r] = dict(terminal="original failed", reason=str(it["original"]["run"].get("failed_reason", "")))
            continue
        undeclared = [i for i in it["missing"] if (r, i) not in decl]
        if undeclared:
            open_.append(f"rep {r}: designated indices {undeclared[:8]}{'...' if len(undeclared) > 8 else ''} missing ({len(undeclared)})")
        elif it["missing"]:
            state[r] = dict(terminal="rescue-exhausted", indices=list(it["missing"]),
                            reasons={str(i): decl[(r, i)]["reason"] for i in it["missing"]})
        else:
            state[r] = dict(terminal="complete")
    return state, open_, conflict


# ------------------------------------------------------------------------------------------------------------------------
# aggregation (only after the seal and terminality)
# ------------------------------------------------------------------------------------------------------------------------
def _aggregate(items, state):
    import numpy as np, analyze as A
    keep = A.run_dataset

    def forbidden(*a, **k):
        raise RuntimeError("the sealed prefix release may not fit anything")
    A.run_dataset = forbidden
    out = {}
    try:
        for r in DESIGNATED:
            it, st = items[r], state[r]
            t = it["task"]
            row = dict(terminal=st, refit=[None, None], cluster=[None, None], point=None, refit_usable=False, cluster_usable=False,
                       original_failed=None, prefix_records=len(it["records"]), prefix_missing=list(it["missing"]),
                       raw_prefix=None, record_failed_reasons=[s["failed_reason"] for s in it["records"] if s["failed"]])
            if it["original"] is not None:
                run = it["original"]["run"]
                row["original_failed"] = bool(run["failed"])
                if not run["failed"]:
                    cb = A.band_bootstrap(run["delta"][PRIMARY[0]], run["layers"], t["ds"].family, t["cfg"].bands, t["cfg"].n_boot, t["seed"])
                    cw = cb.get(PRIMARY[1]) or {}
                    row["cluster"] = [cw.get("lo"), cw.get("hi")]; row["point"] = cw.get("point")
                    row["cluster_usable"] = R._finite(cw.get("lo")) and R._finite(cw.get("hi"))
            if len(it["records"]) == PREFIX:
                pi = prefix_interval(it["records"], PREFIX, t["bands"])
                row["raw_prefix"] = pi                                   # every predictor and band, also for a failed original
                p = pi[PRIMARY[0]]; w = p["bands"].get(PRIMARY[1]) or {}
                if st["terminal"] == "complete":
                    row["refit"] = [w.get("lo"), w.get("hi")]
                    row["refit_usable"] = bool(p["usable"]) and R._finite(w.get("lo")) and R._finite(w.get("hi"))
            if row["refit_usable"]:
                row["status"] = "usable"; row["reason"] = ""
            elif st["terminal"] == "complete":
                p = row["raw_prefix"][PRIMARY[0]]
                row["status"] = "unavailable"
                row["reason"] = (f"{p['n_used']} of {PREFIX} designated resamples scored for {PRIMARY[0]} "
                                 f"(refit_min_usable 1.0; record failures {row['record_failed_reasons'][:5]})")
            else:
                row["status"] = "unavailable"
                row["reason"] = f"{st['terminal']}: {st.get('reason') or st.get('reasons')}"
            out[r] = row
    finally:
        A.run_dataset = keep
    return out


def release(screen_path, orig_path, target_path, adoption_rel, terminal_rel=None, check_git=True):
    if not os.path.exists(target_path):
        return dict(status="REFUSED", reasons=["the target file is absent"])
    target = R.load_target(target_path)                                       # ONE read: these bytes decide
    why = seal_problems(screen_path, orig_path, target, adoption_rel, check_git=check_git)
    if why:
        return dict(status="REFUSED", reasons=why)
    screen = json.load(open(screen_path)); origm = json.load(open(orig_path))
    decl, dwhy, dsha = terminal_declarations(terminal_rel, check_git=check_git)
    if dwhy:
        return dict(status="HELD", reasons=dwhy)
    why, items = collect(screen, origm)
    if why:
        return dict(status="HELD", reasons=why[:50], n_reasons=len(why))
    state, open_, conflict = terminality(items, decl)
    if conflict:
        return dict(status="HELD", reasons=conflict)
    if open_:
        return dict(status="NOT TERMINAL", reasons=open_, n_terminal=len(state), n_designated=N_DESIGNATED,
                    note="one terminal look: no interval, count or decision is computed before every designated dataset is terminal")
    per = _aggregate(items, state)
    tsha, tg = target; t = tg["targets"]["/".join(PRIMARY)]; lo, hi = float(t["lo"]), float(t["hi"])
    refit = [tuple(v["refit"]) for v in per.values() if v["refit_usable"]]
    clus = [tuple(v["cluster"]) for v in per.values() if v["cluster_usable"]]
    r_ok = {r for r, v in per.items() if v["refit_usable"]}; c_ok = {r for r, v in per.items() if v["cluster_usable"]}
    allr = set(per)
    return dict(schema=RESULT_SCHEMA, status="RELEASED", contract=CONTRACT, contract_sha256=contract_sha(),
                target=dict(lo=lo, hi=hi, sha256=tsha), terminal_declaration_sha256=dsha, n_attempted=N_DESIGNATED,
                failed_originals={str(r): v["terminal"]["reason"] for r, v in per.items() if v["terminal"]["terminal"] == "original failed"},
                unavailable={str(r): v["reason"] for r, v in per.items() if v["status"] != "usable"},
                refit=decide(refit, lo, hi, N_DESIGNATED, all_terminal=True),
                cluster=decide(clus, lo, hi, N_DESIGNATED, all_terminal=True),
                paired=dict(both=len(r_ok & c_ok), refit_only=len(r_ok - c_ok), cluster_only=len(c_ok - r_ok), neither=len(allr - r_ok - c_ok)),
                per_dataset={str(r): v for r, v in per.items()})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True); ap.add_argument("--originals", required=True)
    ap.add_argument("--target", required=True); ap.add_argument("--adoption", required=True)
    ap.add_argument("--terminal", default=None); ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.out and os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists; a release is written once"); return 2
    res = release(a.screen, a.originals, a.target, a.adoption, terminal_rel=a.terminal)
    if res["status"] != "RELEASED":
        print(f"{res['status']}:"); [print("  -", w) for w in res["reasons"]]; return 2
    if a.out:
        with open(a.out, "x") as fh:
            json.dump(res, fh, indent=1)
    print(f"RELEASED: refit {res['refit']['decision']} (n {res['refit']['n_usable']}, Kmax {res['refit']['k_max']}, M {res['refit']['M_unavailable']}); "
          f"cluster {res['cluster']['decision']}; paired {res['paired']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
