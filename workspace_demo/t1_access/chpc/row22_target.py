"""Ledger row 22: the omega = 1 reference TARGET SET from the bank's records, and the evaluator that refuses an incompatible
reference. Row 19's stage-2 rule: T is a declared 99 % reference confidence set, mean +- t(0.995, n - 1) x MCSE, under
predeclared normal-approximation, tail and stability checks; the screen's futility decision is a containment argument over
EVERY point of T; where no justified T exists the setting is UNRESOLVED; the external evaluator is frozen and reviewed
before the screen's coverage is read and never uses the screen's own mean.

THE PREDECLARED RULES (values from the manifest's `target` block; nothing here is tuned on the bank's numbers):
  usable        a record that is not failed and whose statistic is finite; unusable ones are counted, never imputed
  completeness  every declared bank rep has a valid record (otherwise the set is INCOMPLETE and nothing is frozen)
  failures      unusable fraction <= max_unusable_fraction (0.01)                                  else UNRESOLVED
  tail          the full mean lies inside the TRIMMED sample's own 99 % interval (trim_fraction 0.005 from EACH end, 1 % in
                all): the extreme 1 % may not move the mean by more than the target's own uncertainty     else UNRESOLVED
                (a single extreme dataset - omega = 2's -2,650 - widens T until any trimmed mean sits inside it, so the
                comparison is made against the trimmed sample's interval, not T)
  precision     T's half-width is at most max_halfwidth (0.10 nat per trial, about a fifth of the refit interval's
                half-width at omega = 1): a wider T cannot adjudicate the containment rule                   else UNRESOLVED
  stability     the even-rep and odd-rep half means differ by at most stability_z (3) combined SEs  else UNRESOLVED
  report        skewness, excess kurtosis, the largest |z|, min and max - reported, not gates
For the primary predictor and band (selection, ws) and, as reported secondary targets, every other predictor and band.

FREEZE. `--freeze OUT` writes the target document once (never overwritten): schema, the bank binding's SHA-256, the manifest's
SHA-256, the SHA-256 over the sorted record checksums, the rules applied, every target, its status. Its own SHA-256 is what
the review names and what the screen's coverage step must be given.

EVALUATOR HELPER. `compatible(target_doc, bank_binding, bank_binding_sha, screen, bank_manifest_path, screen_manifest_path)`
returns reasons a frozen target may NOT score a screen: a status other than RESOLVED; a setting, cfg (B excluded: the original
fit does not depend on it), start policy, code pin of analyze.py / models.py / simulate.py or numerical snapshot that differs
from the screen's; a bank binding that is not the one the target document names; and the seed domains, both DERIVED from the
admitted manifests (never a caller's list) and required disjoint. It is not the whole consumer: the reviewed target digest,
the numerical body, review authority and the endpoint/coverage seal belong to the separately reviewed consumer.

    t1py chpc/row22_target.py --manifest chpc/row22_bank_manifest.json [--freeze <root>/gate/target_omega1.json]
"""
import os, sys, json, math, glob, time, hashlib, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from scipy import stats as SS

TARGET_SCHEMA = "row22-target-1"
STATUSES = ("RESOLVED", "UNRESOLVED", "INCOMPLETE")


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(open(p, "rb").read())


def rules(man):
    t = man.get("target", {})
    return dict(level=float(t.get("level", 0.99)), max_unusable_fraction=float(t.get("max_unusable_fraction", 0.01)),
                max_halfwidth=float(t.get("max_halfwidth", 0.10)),
                trim_fraction=float(t.get("trim_fraction", 0.005)), stability_z=float(t.get("stability_z", 3.0)),
                primary=dict(predictor=t.get("primary_predictor", "selection"), band=t.get("primary_band", "ws")))


def summarise(values, reps, R, n_declared):
    """One target from a list of (rep, value-or-None) for the usable/unusable split. Pure arithmetic on the given values."""
    usable = [(r, v) for r, v in zip(reps, values) if v is not None and math.isfinite(v)]
    n_att, n = len(values), len(usable)
    out = dict(n_declared=int(n_declared), n_attempted=n_att, n_usable=n, n_unusable=n_att - n)
    if n_att < n_declared:
        return dict(out, status="INCOMPLETE", reasons=[f"{n_att} of {n_declared} declared datasets have a valid record"])
    if n < 3:
        return dict(out, status="UNRESOLVED", reasons=["fewer than 3 usable datasets"])
    x = np.array([v for _, v in usable], dtype=float)
    mean, sd = float(x.mean()), float(x.std(ddof=1)); mcse = sd / math.sqrt(n)
    tq = float(SS.t.ppf(0.5 + R["level"] / 2.0, n - 1))
    lo, hi = mean - tq * mcse, mean + tq * mcse
    k = int(math.floor(R["trim_fraction"] * n))
    xs = np.sort(x); core = xs[k:n - k]
    trimmed = float(core.mean()) if core.size else float("nan")
    if core.size >= 2:
        tq_c = float(SS.t.ppf(0.5 + R["level"] / 2.0, core.size - 1)); hw_c = tq_c * float(core.std(ddof=1)) / math.sqrt(core.size)
    else:
        hw_c = float("nan")
    ev = np.array([v for r, v in usable if r % 2 == 0]); od = np.array([v for r, v in usable if r % 2 == 1])
    if ev.size >= 2 and od.size >= 2:
        se = math.sqrt(ev.var(ddof=1) / ev.size + od.var(ddof=1) / od.size)
        split = dict(even_mean=float(ev.mean()), odd_mean=float(od.mean()), diff=float(ev.mean() - od.mean()), se=se,
                     z=float(abs(ev.mean() - od.mean()) / se) if se > 0 else (0.0 if ev.mean() == od.mean() else float("inf")))
    else:
        split = dict(z=float("inf"), note="a half has fewer than 2 usable datasets")
    z = (x - mean) / sd if sd > 0 else np.zeros_like(x)
    report = dict(skewness=float(SS.skew(x)), excess_kurtosis=float(SS.kurtosis(x)), max_abs_z=float(np.max(np.abs(z))),
                  min=float(xs[0]), max=float(xs[-1]), median=float(np.median(x)))
    reasons = []
    if (n_att - n) / n_att > R["max_unusable_fraction"]:
        reasons.append(f"unusable fraction {(n_att - n) / n_att:.4f} above {R['max_unusable_fraction']}")
    if not (abs(mean - trimmed) <= hw_c):
        reasons.append(f"the mean {mean:.6g} lies outside the {2 * R['trim_fraction']:.1%}-trimmed sample's interval {trimmed:.6g} +- {hw_c:.6g} (tail)")
    if not ((hi - lo) / 2.0 <= R["max_halfwidth"]):
        reasons.append(f"T's half-width {(hi - lo) / 2.0:.4g} is above {R['max_halfwidth']} (precision)")
    if not (split["z"] <= R["stability_z"]):
        reasons.append(f"the even/odd halves differ by {split['z']:.2f} combined SEs (stability, limit {R['stability_z']})")
    return dict(out, status="UNRESOLVED" if reasons else "RESOLVED", reasons=reasons, mean=mean, sd=sd, mcse=mcse, t=tq,
                lo=lo, hi=hi, trimmed_mean=trimmed, trimmed_halfwidth=hw_c, trimmed_k_each_end=k, split=split, report=report)


def load_records(man, validate=True):
    """{rep: record} of every VALID bank record; raises ValueError on any invalid file (nothing is frozen over bad evidence)."""
    import row22_bank as B
    root = man["storage"]["root"]; reps = [int(r) for r in man["datasets"]["reps"]]
    out = {}
    for r in reps:
        p = B.record_path(root, r)
        if not os.path.exists(p):
            continue
        if validate:
            d = B.read_record(p, B.SH.task(man, r), r)
        else:
            d = json.load(open(p))
        out[r] = d
    extra = [p for p in glob.glob(os.path.join(root, "records", "b*.json")) if os.path.basename(p) not in {f"b{r:03d}.json" for r in reps}]
    if extra:
        raise ValueError(f"{len(extra)} record file(s) for undeclared bank reps, e.g. {extra[0]}")
    return out


def targets(man, recs):
    R = rules(man); reps_decl = [int(r) for r in man["datasets"]["reps"]]
    import analyze as A
    rs = sorted(recs)
    preds = list(A.PREDICTORS)
    bands = sorted({b for d in recs.values() for p in preds for b in d["stats"].get(p, {})}) or [R["primary"]["band"]]
    out = {}
    for p in preds:
        for b in bands:
            vals = [None if recs[r]["failed"] else recs[r]["stats"][p].get(b) for r in rs]
            vals = [None if (v is None or not isinstance(v, (int, float))) else float(v) for v in vals]
            out[f"{p}/{b}"] = summarise(vals, rs, R, len(reps_decl))
    return R, out


def freeze(man, manifest_path, out_path):
    if os.path.exists(out_path):
        return f"REFUSED: {out_path} exists; a frozen target is never overwritten"
    recs = load_records(man)
    R, tg = targets(man, recs)
    root = man["storage"]["root"]
    bp = os.path.join(root, "bank_binding.json")
    key = f"{R['primary']['predictor']}/{R['primary']['band']}"
    doc = dict(schema=TARGET_SCHEMA, time=time.time(), manifest_sha256=sha_file(manifest_path),
               bank_binding_sha256=sha_file(bp) if os.path.exists(bp) else None,
               records_sha256=sha_bytes(json.dumps(sorted(d["sha"] for d in recs.values())).encode()),
               rules=R, primary=key, status=tg[key]["status"], targets=tg)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = out_path + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, allow_nan=True); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, out_path); os.remove(tmp)
    return f"frozen: {out_path} ({sha_file(out_path)[:16]}), primary {key} {doc['status']}"


CFG_KEYS = ("start_policy", "interval", "n_starts", "n_starts_inner", "refit_min_usable", "n_outer", "n_inner")
CODE_FILES = ("analyze.py", "models.py", "simulate.py")


def _screen_seed_domain_problem(screen_man):
    """The reviewed screen seed-domain checker (row19_screen_admit.seed_domain_problem: complete, unique, declared, disjoint
    from the reconstructed historical/development/bank exclusion contract and from the named bank's recomputed seeds)."""
    import row19_screen_admit as SA
    return SA.seed_domain_problem(screen_man)


def compatible(target_doc, bank_binding, bank_binding_sha, screen, bank_manifest_path, screen_manifest_path,
               seed_domain_check=_screen_seed_domain_problem):
    """The reasons a frozen target may NOT score a screen ('[]' = no reason found here). `screen`: dict(setting, cfg, code
    (file pins), numerical (the screen binding's snapshot), manifest_sha256 (the screen binding's manifest)).

    SEED DOMAINS (Codex 97fc278 / 6d8c30a): both are DERIVED here from the immutable admitted manifests - never taken from the
    caller. Bank: the manifest the target was frozen from and the binding names, its seeds recomputed (row22_bank.seed_problems:
    unique, no excluded seed, the declared resolved_seeds_sha256), complete (one per declared rep), equal to the binding's
    seeds_sha256. Screen: the manifest the screen binding names, naming THIS bank manifest, passing the reviewed screen
    seed-domain checker, its seeds recomputed and non-empty. Overlap refuses. A caller-supplied `seeds` / `bank_seeds` list is
    only compared: any difference from the derived domain refuses as foreign. Missing manifests refuse.
    NOT covered here (they belong to the separately reviewed consumer): the expected reviewed target-file digest, the complete
    finite ordered numerical body, review authority, and the endpoint/decision/coverage seal."""
    import row22_bank as R22
    why = []
    if target_doc.get("schema") != TARGET_SCHEMA:
        why.append("not a row-22 target document")
    if target_doc.get("status") != "RESOLVED":
        why.append(f"the primary target is {target_doc.get('status')}, not RESOLVED")
    if target_doc.get("bank_binding_sha256") != bank_binding_sha:
        why.append("the target names another bank binding")
    if bank_binding.get("setting") != screen.get("setting"):
        why.append("the setting differs")
    bc, sc = bank_binding.get("cfg", {}), screen.get("cfg", {})
    diff = [k for k in CFG_KEYS if bc.get(k) != sc.get(k)]
    if diff:
        why.append(f"the cfg differs on {diff}")
    cd = [f for f in CODE_FILES if bank_binding.get("code", {}).get(f) != screen.get("code", {}).get(f)]
    if cd:
        why.append(f"the code pins differ on {cd}")
    if bank_binding.get("numerical") != screen.get("numerical"):
        why.append("the numerical snapshot differs")
    # bank seed domain
    bseeds = None
    if not (bank_manifest_path and os.path.exists(bank_manifest_path)):
        why.append("the bank manifest is missing")
    else:
        bsha = sha_file(bank_manifest_path); bman = json.load(open(bank_manifest_path))
        if target_doc.get("manifest_sha256") != bsha:
            why.append("the target was frozen from another bank manifest")
        if bank_binding.get("manifest_sha") != bsha:
            why.append("the bank binding names another bank manifest")
        bp = R22.seed_problems(bman)
        if bp:
            why.append(f"the bank seed domain does not recompute: {bp}")
        else:
            bseeds = R22.resolved_seeds(bman)
            if not bseeds or len(bseeds) != len(R22.bank_reps(bman)):
                why.append("the bank seed domain is empty or incomplete"); bseeds = None
            elif R22.seeds_sha256(bseeds) != bank_binding.get("seeds_sha256") or bank_binding.get("n") != len(bseeds):
                why.append("the bank seed domain is not the one the bank binding records"); bseeds = None
    # screen seed domain
    sseeds = None
    if not (screen_manifest_path and os.path.exists(screen_manifest_path)):
        why.append("the screen manifest is missing")
    else:
        ssha = sha_file(screen_manifest_path); sman = json.load(open(screen_manifest_path))
        if screen.get("manifest_sha256") != ssha:
            why.append("the screen binding names another screen manifest (or none)")
        if bank_manifest_path and os.path.exists(bank_manifest_path) and (sman.get("datasets") or {}).get("bank_manifest_sha256") != sha_file(bank_manifest_path):
            why.append("the screen manifest names another bank manifest")
        sp = seed_domain_check(sman)
        if sp:
            why.append(f"the screen seed domain fails its reviewed check: {sp}")
        else:
            st = sman["setting"]; kw = dict(st["grid"])
            import simulate as S
            sseeds = {int(r): int(S.dataset_seed(st["generator"], kw, int(r), int(st["D"]), int(sman["datasets"]["seed_base"])))
                      for r in sman["datasets"]["reps"]}
            if not sseeds:
                why.append("the screen seed domain is empty"); sseeds = None
    if bseeds is not None and sseeds is not None:
        hit = set(bseeds.values()) & set(sseeds.values())
        if hit:
            why.append(f"{len(hit)} bank seed(s) are screen seeds")
    for key, dom, label in (("bank_seeds", bseeds, "bank"), ("seeds", sseeds, "screen")):
        if screen.get(key) is not None and (dom is None or sorted(int(x) for x in screen[key]) != sorted(dom.values())):
            why.append(f"the supplied {label} seed list is not the derived {label} domain (foreign list)")
    return why


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--freeze", default=None, help="write the frozen target document here (once)")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest))
    if a.freeze:
        out = freeze(man, a.manifest, a.freeze); print(out); return 0 if out.startswith("frozen") else 2
    recs = load_records(man)
    R, tg = targets(man, recs)
    key = f"{R['primary']['predictor']}/{R['primary']['band']}"
    t = tg[key]
    print(f"bank: {len(recs)} valid records of {len(man['datasets']['reps'])}; primary {key}: {t['status']}"
          + (f", n {t['n_usable']}, T [{t['lo']:.5f}, {t['hi']:.5f}]" if "lo" in t else "") + (f"; {t['reasons']}" if t.get("reasons") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
