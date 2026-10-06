"""Ledger row 19 stage 2: the SEALED RELEASE of the screen - the only path that may compute a refit percentile interval, a
cluster interval, a decision or a coverage for a screen dataset (Codex RSC 9202e8b items 3, 4 and 6).

THE SEAL. `release()` checks EVERYTHING below before it touches any aggregation helper; the aggregation helpers are imported
and called only inside `_aggregate`, after `seal_problems()` returned nothing. Any failure refuses with the reasons and
computes nothing:
  1. ADOPTION AUTHORITY: the adoption document (schema row19-target-adoption-1) is a git-tracked, unmodified file of this
     clone; it names the frozen target's SHA-256, the bank manifest's and binding's SHA-256, the screen and originals
     manifests' SHA-256, the reviewed consumer's pins, and a review record that is itself git-tracked and unmodified with its
     SHA-256. The row-22 first-pilot verdict is not such an authority (the adoption names the numerical-target review).
  2. THE TARGET BYTES AND BODY: the target file's SHA-256 is the adopted one; schema row22-target-1; primary selection/ws;
     status RESOLVED; finite ordered bounds; n_attempted equal to the bank's declared count; rules equal the bank manifest's.
  3. THE BANK: its manifest's bytes are the adopted ones; its binding file equals what THIS runtime recomputes
     (row22_bank.binding) and its SHA-256 is the target's and the adoption's; the complete validated bank record set
     (row22_target.load_records) has the target's record digest, and recomputing the target from it gives the frozen
     primary's numbers exactly. A caller-supplied hash is never trusted.
  4. THE CONSUMER: every pinned file of this release (this module, the canonical science, the runner and producer modules,
     the target and bank modules) has the adopted SHA-256.
  5. THE DOMAINS: the screen and originals manifests' bytes are the adopted ones and declare the same datasets, identities,
     cfg and pins; the screen seed domain recomputed, complete, unique, disjoint from its exclusions and from the bank's 408
     seeds recomputed from the bank manifest (row19_screen_admit.seed_domain_problem); the identity map complete.
  6. COMPLETENESS: every one of the 100 screen datasets has a valid lossless original (read back against its task) and every
     resample index 0..199 a valid record attributable to its task; a missing, invalid or conflicting item HOLDS. Nothing can
     be fitted here: during aggregation `analyze.run_dataset` is replaced by a function that raises.
THE COMPUTATION (only after the seal): per dataset, the 200 records written in index order into a fresh checkpoint file
(the on-file record text, unchanged) and restored by `analyze.refit_bootstrap(..., strict_restore=True)` with no new resample
allowed; `analyze.analyze_dataset(run=<the cached original>, interval_result=<that chain>)`; the selection predictor's ws
refit interval and its companion cluster interval. Per method: usable n (an unusable interval or a failed original is
counted, never imputed), K_max = the largest number of usable intervals containing any theta in T, evaluated at every
endpoint inside T, both ends of T and a point inside every segment between them (inclusive ties); the one-sided 97.5 %
exact (Clopper-Pearson) upper bound at (K_max, n); STOP FOR FUTILITY iff that bound is below 0.90 (at n = 100: K_max <= 83),
otherwise "not ruled out at this look" - never a pass. Paired availability (refit-only, cluster-only, both, neither) is
reported. ONE look; no subset, no early look, no replacement dataset.

    t1py chpc/row19_screen_release.py --screen chpc/row19_screen_manifest.json --originals chpc/row19_screen_orig_manifest.json \\
                                      --target <frozen target> --adoption reviews/<adoption>.json [--out <result.json>]
"""
import os, sys, json, math, glob, hashlib, argparse, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

ADOPTION_SCHEMA = "row19-target-adoption-1"
RESULT_SCHEMA = "row19-screen-result-1"
CONSUMER_FILES = ("chpc/row19_screen_release.py", "analyze.py", "models.py", "simulate.py", "chpc/row19_slice.py", "chpc/row19_shard.py",
                  "chpc/row19_screen_orig.py", "chpc/row19_screen_admit.py", "chpc/row22_target.py", "chpc/row22_bank.py")
PRIMARY = ("selection", "ws")


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tracked_unmodified(rel):
    try:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=T1, capture_output=True, text=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=T1, capture_output=True, text=True)
        return a.returncode == 0 and b.returncode == 0
    except Exception:
        return False


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def seal_problems(screen_path, orig_path, target_path, adoption_rel, check_git=True):
    """Every reason the release may not compute. Imports only identity/validation helpers, never an aggregation."""
    why = []
    ad_full = os.path.join(T1, adoption_rel)
    if not os.path.exists(ad_full):
        return ["no adoption document"]
    if check_git and not tracked_unmodified(adoption_rel):
        why.append("the adoption document is not git-tracked and unmodified in this clone")
    try:
        ad = json.load(open(ad_full))
    except Exception as e:
        return [f"the adoption document is unreadable ({e})"]
    if ad.get("schema") != ADOPTION_SCHEMA:
        why.append("the adoption document has another schema")
    rv = ad.get("review_record") or {}
    rv_full = os.path.join(T1, rv.get("path", "") or "_none_")
    if not os.path.exists(rv_full) or sha_file(rv_full) != rv.get("sha256") or (check_git and not tracked_unmodified(rv.get("path", ""))):
        why.append("the numerical-target review record is not tracked and unmodified with the adopted SHA-256")
    if not os.path.exists(target_path) or sha_file(target_path) != ad.get("target_sha256"):
        return why + ["the target file is absent or not the adopted bytes"]
    tg = json.load(open(target_path))
    if tg.get("schema") != "row22-target-1":
        why.append("the target is not a row-22 target document")
    if tg.get("primary") != "/".join(PRIMARY):
        why.append("the target's primary is not selection/ws")
    if tg.get("status") != "RESOLVED":
        why.append(f"the target is {tg.get('status')}, not RESOLVED")
    t = (tg.get("targets") or {}).get("/".join(PRIMARY)) or {}
    if not (_finite(t.get("lo")) and _finite(t.get("hi")) and t["lo"] <= t["hi"]):
        why.append("the target's bounds are not finite and ordered")
    for k, v in (("screen", screen_path), ("originals", orig_path)):
        if sha_file(v) != (ad.get("manifests") or {}).get(k):
            why.append(f"the {k} manifest is not the adopted bytes")
    screen = json.load(open(screen_path)); origm = json.load(open(orig_path))
    for k in ("setting", "datasets", "cfg", "code", "environment"):
        if screen.get(k) != origm.get(k):
            why.append(f"the screen and originals manifests differ on {k}")
    bank_rel = screen["datasets"]["bank_manifest"]; bank_path = os.path.join(T1, bank_rel)
    if not os.path.exists(bank_path) or sha_file(bank_path) != ad.get("bank_manifest_sha256") or sha_file(bank_path) != screen["datasets"]["bank_manifest_sha256"]:
        return why + ["the bank manifest is not the adopted bytes"]
    bank = json.load(open(bank_path))
    import row22_bank as B, row22_target as TG
    if tg.get("manifest_sha256") != sha_file(bank_path):
        why.append("the target was not computed under the adopted bank manifest")
    if TG.rules(bank) != tg.get("rules"):
        why.append("the target's rules are not the bank manifest's")
    bb_path = os.path.join(bank["storage"]["root"], "bank_binding.json")
    if not os.path.exists(bb_path):
        why.append("the bank binding is absent")
    else:
        bsha = sha_file(bb_path)
        if not (bsha == tg.get("bank_binding_sha256") == ad.get("bank_binding_sha256")):
            why.append("the bank binding's SHA-256 is not the target's and the adoption's")
        if B.binding_problem(bank["storage"]["root"], B.binding(bank, sha_file(bank_path)), create=False):
            why.append("the bank binding is not what this runtime recomputes from the bank manifest")
    if not why:
        try:
            recs = TG.load_records(bank)
        except ValueError as e:
            return why + [f"the bank record set does not validate: {e}"]
        if len(recs) != len(bank["datasets"]["reps"]):
            why.append(f"the bank holds {len(recs)} valid records of {len(bank['datasets']['reps'])}")
        if TG.sha_bytes(json.dumps(sorted(d["sha"] for d in recs.values())).encode()) != tg.get("records_sha256"):
            why.append("the bank record set is not the one the target was computed from")
        R, again = TG.targets(bank, recs)
        mine = again.get("/".join(PRIMARY)) or {}
        if any(mine.get(k) != t.get(k) for k in ("mean", "sd", "mcse", "lo", "hi", "n_usable", "status")):
            why.append("recomputing the target from the bank records does not reproduce the frozen primary")
        if int(t.get("n_attempted", -1)) != len(bank["datasets"]["reps"]):
            why.append("the target's attempted count is not the bank's declared count")
    pins = ad.get("consumer_pins") or {}
    bad = [f for f in CONSUMER_FILES if sha_file(os.path.join(T1, f)) != pins.get(f)]
    if bad:
        why.append(f"the consumer's pins differ on {bad}")
    import row19_screen_admit as SA
    sd = SA.seed_domain_problem(screen)
    if sd:
        why.append(f"seed domain: {sd}")
    return why


def completeness_problems(screen, origm):
    """Every screen dataset's original and all B records, validated; nothing missing, nothing conflicting."""
    import row19_shard as SH, row19_screen_orig as O
    why, items = [], {}
    B = int(screen["cfg"]["n_boot_refit"])
    for r in [int(x) for x in screen["datasets"]["reps"]]:
        try:
            t = O.task_checked(screen, r)
        except ValueError as e:
            why.append(str(e)); continue
        try:
            got, _ = O.read_cache(origm["storage"]["root"], t)
        except ValueError as e:
            why.append(str(e)); continue
        if got is None:
            why.append(f"rep {r}: no original"); continue
        recs = []
        for i in range(B):
            p = SH.record_path(screen["storage"]["root"], r, i)
            try:
                d = SH.read_record(p, t, i)
            except ValueError as e:
                why.append(str(e)); d = None
            if d is None:
                if os.path.exists(p) is False:
                    why.append(f"rep {r}: resample {i} missing")
                break
            recs.append((i, open(p).read().strip()))
        if len(recs) == B:
            items[r] = (t, got, recs)
    extra = [p for p in glob.glob(os.path.join(screen["storage"]["root"], "records", "rep*")) if not os.path.basename(p)[3:].isdigit()
             or int(os.path.basename(p)[3:]) not in [int(x) for x in screen["datasets"]["reps"]]]
    if extra:
        why.append(f"records of undeclared datasets: {extra[:3]}")
    return why, items


def k_max(intervals, lo, hi):
    """The largest number of intervals [a, b] containing any theta in [lo, hi], inclusive, over every endpoint inside T, both
    ends of T and one point inside every segment between consecutive candidate points."""
    pts = sorted({lo, hi} | {x for a, b in intervals for x in (a, b) if lo <= x <= hi})
    cand = list(pts) + [(pts[k] + pts[k + 1]) / 2.0 for k in range(len(pts) - 1)]
    return max((sum(1 for a, b in intervals if a <= th <= b) for th in cand), default=0)


def cp_upper(k, n, conf=0.975):
    from scipy.stats import beta
    return 1.0 if k >= n else float(beta.ppf(conf, k + 1, n - k))


def decide(intervals, n_attempted, lo, hi):
    n = len(intervals)
    if n == 0:
        return dict(n_usable=0, k_max=0, upper=None, decision="unresolved: no usable interval")
    k = k_max(intervals, lo, hi); up = cp_upper(k, n)
    stop = (k <= 83) if n == 100 else (up < 0.90)
    return dict(n_usable=n, n_attempted=n_attempted, k_max=k, upper=up,
                decision="STOP FOR FUTILITY" if stop else "not ruled out at this look")


def _aggregate(items, screen):
    """ONLY after the seal. No fit can be bought: run_dataset raises for the whole call."""
    import analyze as A
    keep = A.run_dataset

    def forbidden(*a, **k):
        raise RuntimeError("the sealed release may not fit anything")
    A.run_dataset = forbidden
    out = {}
    try:
        cfg_B = int(screen["cfg"]["n_boot_refit"])
        for r, (t, got, recs) in sorted(items.items()):
            with tempfile.TemporaryDirectory() as td:
                ck = os.path.join(td, "chain.jsonl")
                open(ck, "w").write("\n".join(line for _, line in recs) + "\n")
                rb = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], n_rep=cfg_B, outer_folds=t["folds"], min_usable=t["cfg"].refit_min_usable,
                                       checkpoint_path=ck, strict_restore=True)
            if rb.get("n_new", 0) != 0 or rb.get("partial") or int(rb.get("n_done", -1)) != cfg_B:
                raise RuntimeError(f"rep {r}: the chain did not restore completely without new work")
            res = A.analyze_dataset(t["ds"], t["cfg"], t["seed"], outer_folds=t["folds"], run=got["run"], interval_result=rb)
            p = res["predictors"][PRIMARY[0]]
            refit = p.get(PRIMARY[1], {}); clus = (p.get("cluster") or {}).get(PRIMARY[1], {})
            out[r] = dict(failed=bool(res["failed"]), refit_usable=bool(p.get("usable")) and not res["failed"],
                          refit=[refit.get("lo"), refit.get("hi")], cluster=[clus.get("lo"), clus.get("hi")], point=refit.get("point"))
    finally:
        A.run_dataset = keep
    return out


def release(screen_path, orig_path, target_path, adoption_rel, check_git=True):
    why = seal_problems(screen_path, orig_path, target_path, adoption_rel, check_git=check_git)
    if why:
        return dict(status="REFUSED", reasons=why)
    screen = json.load(open(screen_path)); origm = json.load(open(orig_path))
    why, items = completeness_problems(screen, origm)
    if why:
        return dict(status="HELD", reasons=why[:50], n_reasons=len(why))
    per = _aggregate(items, screen)
    tg = json.load(open(target_path)); t = tg["targets"]["/".join(PRIMARY)]; lo, hi = float(t["lo"]), float(t["hi"])
    N = int(screen["datasets"]["n_attempted"])
    fin = lambda v: v is not None and all(_finite(x) for x in v)
    refit = [tuple(v["refit"]) for v in per.values() if v["refit_usable"] and fin(v["refit"])]
    clus = [tuple(v["cluster"]) for v in per.values() if not v["failed"] and fin(v["cluster"])]
    r_ok = {r for r, v in per.items() if v["refit_usable"] and fin(v["refit"])}; c_ok = {r for r, v in per.items() if not v["failed"] and fin(v["cluster"])}
    allr = set(per)
    return dict(schema=RESULT_SCHEMA, status="RELEASED", target=dict(lo=lo, hi=hi, sha256=sha_file(target_path)), n_attempted=N,
                failed_originals=sorted(r for r, v in per.items() if v["failed"]),
                refit=decide(refit, N, lo, hi), cluster=decide(clus, N, lo, hi),
                paired=dict(both=len(r_ok & c_ok), refit_only=len(r_ok - c_ok), cluster_only=len(c_ok - r_ok), neither=len(allr - r_ok - c_ok)),
                per_dataset={str(r): v for r, v in per.items()})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True); ap.add_argument("--originals", required=True)
    ap.add_argument("--target", required=True); ap.add_argument("--adoption", required=True); ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = release(a.screen, a.originals, a.target, a.adoption)
    if res["status"] != "RELEASED":
        print(f"{res['status']}:"); [print("  -", w) for w in res["reasons"]]; return 2
    if a.out:
        if os.path.exists(a.out):
            print(f"REFUSED: {a.out} exists; a release is written once"); return 2
        json.dump(res, open(a.out, "w"), indent=1)
    print(f"RELEASED: refit {res['refit']}; cluster {res['cluster']}; paired {res['paired']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
