"""Ledger row 19, the RESIZED screen: the first-80 PREFIX release consumer (CANDIDATE, not adopted).

Design: `reviews/2026-10-17_row19_resize_codex.md` ss.1, 2, 5 and 6 item 3; PREREGISTRATION_T1_model.md s.10.1, "Amendment of
17 October 2026"; chpc/ROW19_SCREEN_DECLARATIONS.md, "Owner adoption of the resized screen". Repaired per Codex's review
`reviews/2026-10-17_v16_p80_codex_review.md` B1-B4 and its re-review `reviews/2026-10-17_e2_p80r_codex_review.md` B-R1, B-R2. The adopted B = 200 consumer (`chpc/row19_screen_release.py`) is NOT
changed and stays the only consumer of the declared 100 x B = 200 screen; this module is a separate consumer with its own
adoption schema, its own review literal and its own pins, so neither consumer can release under the other's adoption.

WHAT IS SCREENED. For each of the 60 designated datasets S = {r in 3..102 : (r - 3) mod 5 in {0, 1, 2}} the interval is the
2.5 % / 97.5 % percentile interval (np.percentile, default linear interpolation, exactly the expression of
analyze.refit_bootstrap) over the FIRST 80 records (indices 0..79) of that dataset's UNCHANGED B = 200 producer stream. The
producer's B stays 200: every record is validated against the dataset's original B = 200 task (its manifest-declared parent
identity, which hashes B = 200 and the folds; its seed; n_rep = 200; its own index; the row of the B = 200 draw matrix it must
have drawn; its checksum) and nothing is relabelled, re-drawn or re-identified. B = 80 is the procedure screened, not an
approximation of B = 200 (design s.1).

THE SEAL (all before any statistic is computed; any failure REFUSES and computes nothing):
  0. B-R1: the adoption is read ONCE (`adoption_snapshot`: with check_git git-tracked, unmodified and the bytes read equal to
     HEAD's blob), parsed once, and that one snapshot is what items 1-3 and the terminal authority judge. The inherited seal's
     reads of the adoption path are served from the snapshot (the adopted module is not edited; its `open` is redirected for
     the call only and restored), and the release refuses if the inherited seal did not read it. The release review record is
     likewise one snapshot (hash and literal from the same bytes).
  1. The adopted consumer's whole seal, unchanged (`row19_screen_release.seal_problems`: target bytes, RESOLVED status, bank
     binding and record set recomputed, both seed domains, controller lineage, consumer pins, manifests), run with THIS
     consumer's adoption schema (`row19-p80-adoption-1`) and THIS consumer's pin list (the adopted list plus this module).
  2. The adoption's `prefix_contract` equals this module's CONTRACT exactly, and the screen manifest is that contract's
     producer (interval refit, n_boot_refit 200, refit_min_usable 1.0, every designated ID declared with an identity).
  3. A separate git-tracked, unmodified release review record carries
     `ADOPT row19-p80-release consumer=<sha256 of this file> target=<target sha256> contract=<contract sha256> verdict=FAVOURABLE`.
COLLECTION (validation only, no statistic): per designated dataset, the original (lossless cache, read back) and the records
at indices 0..79. An unacceptable record or cache HOLDS (wrong parent, seed, B, draw, index or checksum - it is never
skipped). Out-of-prefix records (80..199) are not read: they stay history and earn no credit.
TERMINALITY (one look): a decision is emitted only when ALL 60 datasets are terminal - complete (original valid and 80 valid
records), original failed (recorded reason), or every missing prefix coordinate of a valid original covered by a TERMINAL
CERTIFICATE (B1). The fully complete case needs no certificate. An absent original has no certificate route: NOT TERMINAL.
  The certificate (schema row19-p80-terminal-cert-1) is immutable and review-bound: its bytes are read ONCE (hashed and parsed
  from that one snapshot) and must be git-tracked and equal to HEAD's blob; a SEPARATE tracked review record (also one
  snapshot) must carry `ADOPT row19-p80-terminal certificate=<its sha256> screen=<screen manifest sha256> contract=<contract
  sha256> target=<target sha256> controls=<controls sha256> verdict=FAVOURABLE`. Its identity fields (campaign, root, both
  manifests, contract, target, controller = admit / controls / controls version / designated declaration) must equal this
  release's, and the controller files must be pinned by the adoption at their present bytes. Its evidence is then verified
  against the controller's own representation (the v16 controller API, refused when absent): every certified coordinate's
  attempts must equal EXACTLY the crashed-worker slot dispositions the certificate's bound gate receipts carry. B-R2: every
  bound receipt AND the newest gate receipt (read once, bytes frozen and reported) must be a zero-alarm production refit receipt
  of the controller's schema with a finite time, bound to this campaign's identity (screen manifest, root, campaign, code,
  wrapper) with every job binding equal to the ledger's PBS id / token and the plan bytes; the newest must bind every ledger job,
  and be either a certified receipt (the reviewed state) or a validated successor of the newest certified one (later in path
  and time, every certified job binding and crash disposition retained), and must agree on the certified coordinates' attempts; they must reach the crash rule's same-envelope maximum in the envelope the next ordinary job uses
  (`crash_excluded`), every attempt's job must be SETTLED in the ledger with its settlement fields bound in the certificate,
  and either (rescue-failed) the bound declaration's rescue route is enabled and exactly one settled rescue-route plan held the
  coordinate after its crashes, or (allowance-exhausted) no rescue plan held it, every rescue job is settled and the finite
  allowance left is below one full reservation. Finally no outstanding ownership: every plan holding the coordinate belongs to
  a settled ledger entry (a live entry or a plan without an entry refuses), it lies in Lengau's scope (an unclaimed
  EC2-designated coordinate waits for the EC2 epoch), and no EC2 register attempt names it. A certificate naming a coordinate
  that holds a valid record, or one of a dataset whose original is absent or failed, HOLDS (never relabel a record as missing).
AGGREGATION (only after seal + terminality; analyze.run_dataset raises throughout, so nothing can be fitted): per dataset and
predictor, the 80 statistics; usable only when ALL 80 scored (refit_min_usable = 1.0 over the 80; never the first 80
successes, never a substitute index); the cluster companion interval from the cached original's fixed scores
(analyze.band_bootstrap, exactly as analyze.analyze_dataset computes it - independent of B).
OVERLAP (B4): K_max / K_min over the frozen T by an exact sorted-endpoint sweep - every closed point (both ends of T, every
endpoint inside T) and every OPEN segment between consecutive points, counted symbolically (no midpoint is formed, so adjacent
floats and large finite values are exact); inclusive ties.
DECISION - refit only (the screened procedure), n_attempted = 60: STOP FOR FUTILITY iff the one-sided 98.5 % Clopper-Pearson
upper bound at (K_max, n_usable) < 0.90 AND the all-60 bound at (K_max + M, 60) < 0.90, M = 60 - n_usable; otherwise "not
ruled out at this look"; never PASS. Reported uncertainty (B2) is ONLY the valid sandwich L_CP(K_min, n) .. U_CP(K_max, n)
(one-sided 98.5 % each; a two-sided 97 % interval conditional on theta_g lying in T, under the binomial assumptions; the bank's
nominal 1 % is separate) and the attempted-set corners L_CP(K_min, 60) and U_CP(K_max + M, 60). The opposite corners
L_CP(K_max, n) and U_CP(K_min, n) carry no coverage guarantee and are not computed. The CLUSTER interval (B3) is a COMPANION
REPORT only - its intervals, paired availability, containment of T and the same descriptive sandwich, labelled as carrying no
allocated error - with no STOP/decision. The bank's point mean is never substituted for T.

    t1py chpc/release_p80/row19_screen_release_p80.py --screen chpc/row19_screen_manifest.json \\
        --originals chpc/row19_screen_orig_manifest.json --target <frozen target> --adoption reviews/<p80 adoption>.json \\
        [--terminal reviews/<terminal certificate>.json --terminal-review reviews/<its review>.md] [--out <result.json>]
"""
import os, io, sys, json, glob, math, bisect, hashlib, argparse, builtins, contextlib, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.abspath(os.path.join(HERE, ".."))
T1 = os.path.abspath(os.path.join(CHPC, ".."))
for p in (T1, CHPC):
    if p not in sys.path:
        sys.path.insert(0, p)

import row19_screen_release as R                    # the adopted consumer: its seal and helpers are reused unchanged

ADOPTION_SCHEMA = "row19-p80-adoption-1"
TERMINAL_SCHEMA = "row19-p80-terminal-cert-1"
RESULT_SCHEMA = "row19-p80-result-2"
SELF_REL = "chpc/release_p80/row19_screen_release_p80.py"
CONSUMER_FILES = tuple(R.CONSUMER_FILES) + (SELF_REL,)
PRIMARY = R.PRIMARY

PARENT_B = 200
PREFIX = 80
REFIT_MIN_USABLE = 1.0
CP_CONF = 0.985
TWO_SIDED_CONF = 0.97                                # 1 - 2 x (1 - CP_CONF)
FLOOR = 0.90
DESIGNATED = tuple(r for r in range(3, 103) if (r - 3) % 5 in (0, 1, 2))
N_DESIGNATED = 60
assert len(DESIGNATED) == N_DESIGNATED and 83 in DESIGNATED
assert abs((1.0 - 2.0 * (1.0 - CP_CONF)) - TWO_SIDED_CONF) < 1e-12

# The controller whose plans / ledger / receipts represent the campaign's attempts (B1). Paths are relative to T1; at release
# every one must be pinned by the adoption's consumer_pins at its present bytes, and the module in use must be the admit file.
CONTROLLER_FILES = dict(admit="chpc/row19_screen_admit.py", controls="chpc/row19_screen_controls.json",
                        designated="chpc/row19_screen_designated.json")
CONTROLLER_API = ("crash_history", "crash_excluded", "lengau_scope", "designated_coordinates", "env_key", "resolve_envelope",
                  "envelope_core_h", "DESIGNATED", "WATCH_SCHEMA", "CRASH_KIND")
RESCUE_ROUTE = "rescue"                              # a rescue-lane plan carries "route": "rescue"
BRANCHES = ("rescue-failed", "allowance-exhausted")
SETTLEMENT_FIELDS = ("job_id", "reserved_core_h", "settled_core_h", "settled_at", "settle_note")

SANDWICH_NOTE = ("valid sandwich: for a fixed theta_g in T, P(L_CP(K_min, n) > c) <= 1.5 % and P(U_CP(K_max, n) < c) <= 1.5 %, "
                 "a two-sided 97 % interval for the coverage c conditional on theta_g lying in T, under the binomial assumptions; "
                 "the bank's nominal 1 % target error is separate (combined nominal error up to 4 %). The opposite corners "
                 "L_CP(K_max, n) and U_CP(K_min, n) carry no coverage guarantee and are not reported")
ENVELOPE_NOTE = ("attempted-set envelope: all M unavailable counted as covering for the upper corner U_CP(K_max + M, 60) and as "
                 "not covering for the lower corner L_CP(K_min, 60); unavailability stays an operational result")
COMPANION_NOTE = ("COMPANION REPORT ONLY: no campaign-authoritative STOP/PASS and no allocated error (the adopted 1.5 % screen "
                  "component is for selection/ws refit coverage); its sandwich is the same CP arithmetic, descriptive. A second "
                  "formal test would need its own adopted scope and error allocation before release")

CONTRACT = dict(schema="row19-p80-contract-2", parent_B=PARENT_B, prefix=PREFIX, prefix_indices="0..79",
                designated_rule="r in 3..102, (r - 3) mod 5 in {0, 1, 2}", designated=list(DESIGNATED), n_attempted=N_DESIGNATED,
                refit_min_usable=REFIT_MIN_USABLE, percentile="numpy.percentile default linear, 2.5 and 97.5",
                cp_one_sided_conf=CP_CONF, floor=FLOOR, attempted_set_guard="cp_upper(Kmax + M, 60) < floor also required",
                looks=1, primary="/".join(PRIMARY), decided="refit only",
                overlap="exact sorted-endpoint sweep: closed points and symbolic open segments, inclusive ties, no midpoint",
                uncertainty="L_CP(Kmin, n) .. U_CP(Kmax, n), one-sided 98.5 % each, two-sided 97 % conditional on theta_g in T; "
                            "attempted set L_CP(Kmin, 60) and U_CP(Kmax + M, 60); no opposite corners",
                cluster="companion report only: intervals, paired availability, containment, descriptive sandwich; no decision",
                terminal="complete, original failed, or every missing prefix coordinate of a valid original certified by a "
                         "review-bound " + TERMINAL_SCHEMA + " certificate (ADOPT row19-p80-terminal); absent original not terminal")


def contract_sha():
    return hashlib.sha256(json.dumps(CONTRACT, sort_keys=True).encode()).hexdigest()


def release_literal(target_sha):
    return (f"ADOPT row19-p80-release consumer={R.sha_file(os.path.join(T1, SELF_REL))} target={target_sha} "
            f"contract={contract_sha()} verdict=FAVOURABLE")


def terminal_literal(cert_sha, screen_sha, target_sha, controls_sha):
    return (f"ADOPT row19-p80-terminal certificate={cert_sha} screen={screen_sha} contract={contract_sha()} target={target_sha} "
            f"controls={controls_sha} verdict=FAVOURABLE")


# ------------------------------------------------------------------------------------------------------------------------
# exact binomial bounds, the overlap sweep, the report and the decision (pure; no data)
# ------------------------------------------------------------------------------------------------------------------------
def cp_upper(k, n, conf=CP_CONF):
    """One-sided exact (Clopper-Pearson) upper confidence bound for a binomial proportion at k of n."""
    from scipy.stats import beta
    if not (isinstance(k, int) and isinstance(n, int) and 0 <= k <= n and n > 0):
        raise ValueError(f"cp_upper needs integers 0 <= k <= n, n > 0 (got {k}, {n})")
    return 1.0 if k >= n else float(beta.ppf(conf, k + 1, n - k))


def cp_lower(k, n, conf=CP_CONF):
    """One-sided exact (Clopper-Pearson) lower confidence bound for a binomial proportion at k of n."""
    from scipy.stats import beta
    if not (isinstance(k, int) and isinstance(n, int) and 0 <= k <= n and n > 0):
        raise ValueError(f"cp_lower needs integers 0 <= k <= n, n > 0 (got {k}, {n})")
    return 0.0 if k <= 0 else float(beta.ppf(1.0 - conf, k, n - k + 1))


def _real(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def overlap_counts(intervals, lo, hi):
    """[(kind, where, count)] over T = [lo, hi]: the number of closed intervals [a, b] containing theta, for every closed
    POINT (both ends of T and every endpoint inside T) and every OPEN SEGMENT between consecutive points. The count is constant
    on each open segment because no endpoint lies strictly inside it, so a segment is handled symbolically: no midpoint is
    formed (a midpoint can round onto an endpoint between adjacent floats, or overflow for large finite values). Only order
    comparisons are made. With A, B the sorted left and right endpoints:
        point v:          #{a <= v <= b} = #{a <= v} - #{b < v}
        segment (v, w):   #{a <= v, b >= w} = #{a <= v} - #{b <= v}   (no endpoint in (v, w): b < w <=> b <= v; b <= v => a <= v)
    Inclusive ties: an interval touching v at either end contains v."""
    if not (_real(lo) and _real(hi) and lo <= hi):
        raise ValueError(f"T must be finite and ordered (got {lo!r}, {hi!r})")
    iv = []
    for x in intervals:
        a, b = x
        if not (_real(a) and _real(b) and a <= b):
            raise ValueError(f"an interval must be finite and ordered (got {x!r})")
        iv.append((a, b))
    A = sorted(a for a, _ in iv); B = sorted(b for _, b in iv)
    pts = sorted({lo, hi} | {x for a, b in iv for x in (a, b) if lo <= x <= hi})
    out = []
    for k, v in enumerate(pts):
        out.append(("point", (v,), bisect.bisect_right(A, v) - bisect.bisect_left(B, v)))
        if k + 1 < len(pts):
            out.append(("segment", (v, pts[k + 1]), bisect.bisect_right(A, v) - bisect.bisect_right(B, v)))
    return out


def k_max(intervals, lo, hi):
    """The largest number of intervals containing any theta in T (inclusive), from the exact sweep."""
    return max(c for _, _, c in overlap_counts(intervals, lo, hi))


def k_min(intervals, lo, hi):
    """The smallest number of intervals containing any theta in T (inclusive), from the exact sweep (open segments included)."""
    return min(c for _, _, c in overlap_counts(intervals, lo, hi))


def describe(intervals, lo, hi, n_attempted=N_DESIGNATED):
    """The descriptive report of one method's usable intervals: counts, the empirical range, the VALID CP sandwich and the
    attempted-set corners. No decision."""
    n = len(intervals); M = int(n_attempted) - n
    if M < 0:
        raise ValueError("more usable intervals than attempted datasets")
    base = dict(n_attempted=int(n_attempted), n_usable=n, M_unavailable=M, cp_one_sided_conf=CP_CONF)
    if n == 0:
        return dict(base, k_max=None, k_min=None)
    kx, kn = k_max(intervals, lo, hi), k_min(intervals, lo, hi)
    na = int(n_attempted)
    return dict(base, k_max=kx, k_min=kn, coverage_range=[kn / n, kx / n],
                sandwich=dict(lower_at_k_min=cp_lower(kn, n), upper_at_k_max=cp_upper(kx, n), one_sided_conf_each=CP_CONF,
                              two_sided_conf=TWO_SIDED_CONF, conditional_on="theta_g in T", note=SANDWICH_NOTE),
                attempted_envelope=dict(range=[kn / na, (kx + M) / na], lower_at_k_min=cp_lower(kn, na),
                                        upper_at_k_max_plus_M=cp_upper(kx + M, na), note=ENVELOPE_NOTE))


def decide(intervals, lo, hi, n_attempted=N_DESIGNATED, all_terminal=False):
    """The one terminal look of the REFIT method (the only formal decision). `intervals` are the usable intervals of the
    n_attempted designated datasets."""
    if not all_terminal:
        return dict(decision="REFUSED: not every designated dataset is terminal; no decision at this point")
    d = describe(intervals, lo, hi, n_attempted)
    d["floor"] = FLOOR
    if d["n_usable"] == 0:
        return dict(d, decision="unresolved: no usable interval")
    up = d["sandwich"]["upper_at_k_max"]; up_all = d["attempted_envelope"]["upper_at_k_max_plus_M"]
    stop = up < FLOOR and up_all < FLOOR
    return dict(d, upper=up, upper_all_attempted=up_all, complete_case_fails=up < FLOOR, attempted_set_fails=up_all < FLOOR,
                decision="STOP FOR FUTILITY" if stop else "not ruled out at this look")


def containment(iv, lo, hi):
    """'contains T' / 'meets T' (overlaps it, not all of it) / 'misses T' for one closed interval."""
    a, b = iv
    if a <= lo and hi <= b:
        return "contains T"
    return "meets T" if (a <= hi and b >= lo) else "misses T"


def cluster_companion(per, lo, hi, n_attempted=N_DESIGNATED):
    """B3: the cluster interval as a companion report only - its descriptive report, paired availability with refit and the
    containment cross table on the datasets where both are usable. Carries NO decision."""
    clus = [tuple(v["cluster"]) for v in per.values() if v["cluster_usable"]]
    rep = describe(clus, lo, hi, n_attempted)
    r_ok = {r for r, v in per.items() if v["refit_usable"]}; c_ok = {r for r, v in per.items() if v["cluster_usable"]}
    kinds = ("contains T", "meets T", "misses T")
    cross = {k: {j: 0 for j in kinds} for k in kinds}
    for r in sorted(r_ok & c_ok):
        cross[containment(tuple(per[r]["refit"]), lo, hi)][containment(tuple(per[r]["cluster"]), lo, hi)] += 1
    return dict(rep, role=COMPANION_NOTE,
                paired=dict(both=len(r_ok & c_ok), refit_only=len(r_ok - c_ok), cluster_only=len(c_ok - r_ok),
                            neither=len(set(per) - r_ok - c_ok)),
                containment=dict(rows="refit", columns="cluster", datasets="both usable", table=cross,
                                 cluster_alone={k: sum(1 for r in c_ok if containment(tuple(per[r]["cluster"]), lo, hi) == k) for k in kinds}))


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
def _as_p80_consumer(adoption_rel=None, adoption_bytes=None):
    """Run the adopted seal with this consumer's adoption schema and pin list; restored in every case.

    B-R1: with `adoption_bytes` (the ONE snapshot of the adoption), every open() the adopted seal makes of the adoption path is
    served from those bytes, so the inherited seal judges exactly the snapshot that the prefix/review checks and the terminal
    authority then use. The adopted module is pinned and adopted, so it is not edited; its file reads are redirected for the
    duration of the call only (the module-level `open` name is removed again in `finally`). Yields a one-element counter of the
    snapshot reads the inherited seal made (it must be at least 1, or the redirection did not take effect)."""
    keep = (R.ADOPTION_SCHEMA, R.CONSUMER_FILES)
    had_open = "open" in vars(R)
    keep_open = vars(R).get("open")
    used = [0]
    R.ADOPTION_SCHEMA, R.CONSUMER_FILES = ADOPTION_SCHEMA, CONSUMER_FILES
    if adoption_bytes is not None:
        ad_real = os.path.realpath(os.path.join(R.T1, adoption_rel))

        def _snapshot_open(file, mode="r", *a, **k):
            if isinstance(file, (str, bytes, os.PathLike)) and os.path.realpath(file) == ad_real:
                if any(c in mode for c in "wax+"):
                    raise PermissionError("the adoption snapshot is read-only")
                used[0] += 1
                return io.BytesIO(adoption_bytes) if "b" in mode else io.StringIO(adoption_bytes.decode())
            return builtins.open(file, mode, *a, **k)
        R.open = _snapshot_open
    try:
        yield used
    finally:
        R.ADOPTION_SCHEMA, R.CONSUMER_FILES = keep
        if had_open:
            R.open = keep_open
        elif "open" in vars(R):
            del R.open


def adoption_snapshot(adoption_rel, check_git=True):
    """(bytes, sha256, parsed adoption, problem) from ONE read of the adoption (B-R1). With check_git the file must be
    git-tracked, unmodified and the bytes read must be HEAD's blob. Every later adoption use parses nothing else."""
    b, sha, w = snapshot(adoption_rel, check_git)
    if w:
        return None, sha, None, f"the adoption document: {w}"
    try:
        ad = json.loads(b.decode())
        assert isinstance(ad, dict)
    except Exception as e:
        return None, sha, None, f"the adoption document is unreadable ({type(e).__name__})"
    return b, sha, ad, ""


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


def seal_problems(screen_path, orig_path, target, adoption_rel, check_git=True, adoption=None):
    """Every reason the prefix release may not compute. `adoption` = (bytes, parsed) from adoption_snapshot: the ONE adoption
    snapshot judged by the inherited seal AND by the prefix/review checks here, and afterwards used by the terminal authority
    (B-R1). Without it, the snapshot is taken here."""
    if adoption is None:
        ab, _s, ad, w = adoption_snapshot(adoption_rel, check_git)
        if w:
            return [w]
    else:
        ab, ad = adoption
    with _as_p80_consumer(adoption_rel, ab) as used:
        why = R.seal_problems(screen_path, orig_path, None, adoption_rel, check_git=check_git, target=target)
    if used[0] < 1:
        why.append("the inherited seal did not judge the adoption snapshot (B-R1): refused")
    if ad.get("prefix_contract") != CONTRACT:
        why.append("the adoption's prefix_contract is not this consumer's contract")
    if ad.get("prefix_contract_sha256") != contract_sha():
        why.append("the adoption does not name this contract's SHA-256")
    rr = ad.get("release_review_record") or {}
    rrb, rrs, w = snapshot(rr.get("path", "") or "_none_", check_git) if isinstance(rr.get("path", ""), str) else (None, None, "no path")
    if w or rrs != rr.get("sha256"):
        why.append("the prefix release review record is not tracked and unmodified with the adopted SHA-256")
    elif release_literal(target[0]) not in [l.strip() for l in rrb.decode(errors="replace").splitlines()]:
        why.append("the prefix release review record does not carry its ADOPT row19-p80-release line for this consumer, target and contract")
    try:
        why += contract_problems(json.load(open(screen_path)))
    except Exception as e:
        why.append(f"the screen manifest is unreadable ({e})")
    return why


# ------------------------------------------------------------------------------------------------------------------------
# B1: the terminal certificate (authority; validation only, no statistic)
# ------------------------------------------------------------------------------------------------------------------------
def _git_head_bytes(rel):
    try:
        r = subprocess.run(["git", "show", f"HEAD:./{rel}"], cwd=T1, capture_output=True)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def snapshot(rel, check_git=True):
    """(bytes, sha256, problem) from ONE read of T1/rel; every later use parses these bytes. With check_git the file must be
    git-tracked and unmodified AND the bytes read must be HEAD's blob (so a change between the read and the check is caught)."""
    full = os.path.join(T1, rel)
    try:
        b = open(full, "rb").read()
    except OSError as e:
        return None, None, f"{rel} is absent or unreadable ({type(e).__name__})"
    sha = hashlib.sha256(b).hexdigest()
    if check_git and not (R.tracked_unmodified(rel) and _git_head_bytes(rel) == b):
        return None, sha, f"{rel} is not git-tracked and unmodified (the bytes read are not HEAD's)"
    return b, sha, ""


def _read_once(path):
    """(parsed JSON, sha256) from one read of an operational file (ledger, plan, receipt, register); raises on failure."""
    b = open(path, "rb").read()
    return json.loads(b.decode()), hashlib.sha256(b).hexdigest()


def controller():
    """The pinned controller module (chpc/row19_screen_admit.py). The release verifies it is the adoption-pinned admit file and
    that it carries the v16 terminal representation (CONTROLLER_API)."""
    import row19_screen_admit as C
    return C


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _plan_coords(plan):
    return {(int(s["rep"]), int(i)) for s in plan["slots"] for i in s["indices"]}


RECEIPT_BOUND_KEYS = ("manifest_sha256", "root", "campaign", "code", "wrapper_sha256")    # the controller's BOUND_KEYS


def _receipt_rel(rel):
    return (isinstance(rel, str) and os.path.dirname(rel) == "gate" and os.path.basename(rel).startswith("watch_refit_")
            and rel.endswith(".json") and ".." not in rel)


def receipt_identity(screen, adoption):
    """The `bound` identity a gate receipt of THIS campaign must carry (B-R2): the adopted screen manifest, its root and
    campaign, its pinned code and wrapper."""
    return dict(manifest_sha256=(adoption.get("manifests") or {}).get("screen"), root=screen["storage"]["root"],
                campaign=screen["storage"]["campaign"], code=dict((screen.get("code") or {}).get("files") or {}),
                wrapper_sha256=(screen.get("environment") or {}).get("wrapper_sha256"))


def receipt_problems(doc, C, ident, by_job, plan_sha, every_job=False):
    """Every reason one gate receipt is not valid evidence of this campaign (B-R2; applied to every certified receipt and to
    the newest one): a dict of the controller's WATCH_SCHEMA, role refit, production, an empty alarm list, a finite time; its
    `bound` identity equals this campaign's (manifest, root, campaign, code, wrapper); every job it binds is a ledger job with
    the ledger's PBS id and token and the plan bytes read here; the jobs it summarises are exactly the jobs it binds; an anchor
    digest. With every_job (the newest receipt) it must bind every ledger job: current evidence covers the current ledger."""
    if not isinstance(doc, dict):
        return ["not a receipt object"]
    why = []
    if doc.get("schema") != C.WATCH_SCHEMA:
        why.append(f"schema {str(doc.get('schema'))[:40]!r} is not the controller's {C.WATCH_SCHEMA}")
    if doc.get("role") != "refit":
        why.append(f"role {str(doc.get('role'))[:20]!r} is not refit")
    if doc.get("production") is not True:
        why.append("not a production receipt")
    if not (isinstance(doc.get("alarms"), list) and doc["alarms"] == []):
        why.append(f"alarms {str(doc.get('alarms'))[:80]} (a zero-alarm receipt is required)")
    if not _real(doc.get("time")):
        why.append("no finite time")
    b = doc.get("bound")
    if not isinstance(b, dict):
        return why + ["no `bound` identity: foreign or unbound evidence"]
    for k in RECEIPT_BOUND_KEYS:
        if b.get(k) != ident.get(k):
            why.append(f"its bound {k} is not this campaign's: foreign evidence")
    bj = b.get("jobs")
    if not isinstance(bj, dict):
        return why + ["no job bindings"]
    for n, v in sorted(bj.items(), key=lambda kv: str(kv[0])):
        try:
            k = int(n); assert str(k) == n
        except Exception:
            why.append(f"job binding {n!r} is malformed"); continue
        le = by_job.get(k)
        if le is None:
            why.append(f"it binds job {n}, which has no ledger entry: foreign or invented evidence"); continue
        if v != dict(job_id=le.get("job_id"), token=le.get("token"), plan_sha256=plan_sha.get(k)):
            why.append(f"its binding of job {n} is not the ledger's PBS id / token and the plan bytes")
    if not isinstance(doc.get("jobs"), dict) or set(doc["jobs"]) != set(bj):
        why.append("the jobs it summarises are not exactly the jobs it binds")
    if every_job and set(bj) != {str(n) for n in by_job}:
        why.append(f"it does not summarise every ledger job (missing {sorted(set(map(str, by_job)) - set(bj))[:5]}, "
                   f"extra {sorted(set(bj) - set(map(str, by_job)))[:5]}): stale or foreign current evidence")
    if not (isinstance(b.get("anchors_sha256"), str) and len(b["anchors_sha256"]) == 64):
        why.append("no anchor verdict digest is bound")
    return why


def successor_problems(bound, nrel, ndoc):
    """B-R2: the newest receipt is a validated SUCCESSOR of the certified ones only when it comes after every certified
    receipt (path order and a strictly later time) and RETAINS their evidence: every job binding of the newest certified
    receipt unchanged, and every crash disposition (slot_disposition) any certified receipt carries unchanged. Both sides
    have already passed receipt_problems, so their campaign identity is equal."""
    why = []
    last_rel, _s, last = bound[-1]
    if not nrel > last_rel:
        why.append(f"it does not follow the newest certified receipt {last_rel} in path order")
    if not ndoc["time"] > max(d["time"] for _, _, d in bound):
        why.append("its time is not later than every certified receipt's")
    nb = ndoc["bound"]["jobs"]
    for n, v in last["bound"]["jobs"].items():
        if nb.get(n) != v:
            why.append(f"it does not retain the certified binding of job {n}")
    for rel, _s, d in bound:
        for n, sj in d["jobs"].items():
            if isinstance(sj, dict) and "slot_disposition" in sj and (ndoc["jobs"].get(n) or {}).get("slot_disposition") != sj["slot_disposition"]:
                why.append(f"it does not retain the crash disposition of job {n} that {rel} certifies")
    return why


def terminal_authority(cert_rel, review_rel, screen_path, screen, adoption, target_sha, C, check_git=True):
    """({(rep, index): certified entry}, problems, certificate sha256). No certificate -> ({}, [], None): the fully complete
    case needs none. Any problem refuses the certificate as a whole (nothing it names becomes terminal)."""
    if cert_rel is None:
        return {}, (["a terminal review record was given without a certificate"] if review_rel else []), None, None
    if not review_rel:
        return None, ["a terminal certificate needs its separate tracked review record (--terminal-review)"], None, None
    cb, csha, w = snapshot(cert_rel, check_git)
    if w:
        return None, [f"terminal certificate: {w}"], csha, None
    rb, _rsha, w = snapshot(review_rel, check_git)
    if w:
        return None, [f"terminal review record: {w}"], csha, None
    try:
        cert = json.loads(cb.decode())
    except Exception as e:
        return None, [f"the terminal certificate is unreadable ({type(e).__name__})"], csha, None
    if not isinstance(cert, dict) or cert.get("schema") != TERMINAL_SCHEMA:
        return None, [f"the terminal certificate is not a {TERMINAL_SCHEMA} document (a free-form declaration is no authority)"], csha, None
    miss = [n for n in CONTROLLER_API if not hasattr(C, n)]
    if miss:
        return None, [f"the controller in use has no terminal representation ({miss[:3]}...): only the reviewed v16+ controller "
                      "can supply attempt/crash/ownership evidence"], csha, None

    # ---- identity: campaign / manifests / contract / target / controller, and the review literal over the exact bytes
    why = []
    pins = adoption.get("consumer_pins") or {}
    files = {}
    for k, rel in CONTROLLER_FILES.items():
        b, s, w = snapshot(rel, check_git)
        if w:
            why.append(f"controller {k}: {w}"); continue
        if pins.get(rel) != s:
            why.append(f"the adoption does not pin the controller's {rel} at its present bytes")
        files[k] = (b, s)
    if why:
        return None, why, csha, None
    if os.path.realpath(getattr(C, "__file__", "") or "") != os.path.realpath(os.path.join(T1, CONTROLLER_FILES["admit"])):
        return None, ["the controller module in use is not the adoption-pinned admit file"], csha, None
    try:
        controls = json.loads(files["controls"][0].decode()); last = controls["versions"][-1]
        desig = json.loads(files["designated"][0].decode())
    except Exception as e:
        return None, [f"the controller's controls or designated declaration is unreadable ({type(e).__name__})"], csha, None
    if (last.get("files") or {}).get(C.DESIGNATED) != files["designated"][1]:
        why.append("the controls' latest version does not pin the designated declaration's present bytes")
    if [int(r) for r in desig.get("reps") or []] != list(DESIGNATED) or desig.get("indices") != dict(start=0, stop=PREFIX):
        why.append("the controller's designated declaration is not this contract's S x 0..79")
    man_sha = (adoption.get("manifests") or {})
    want = dict(schema=TERMINAL_SCHEMA, campaign=screen["storage"]["campaign"], root=screen["storage"]["root"],
                screen_manifest_sha256=man_sha.get("screen"), originals_manifest_sha256=man_sha.get("originals"),
                contract_sha256=contract_sha(), target_sha256=target_sha,
                controller=dict(admit_sha256=files["admit"][1], controls_sha256=files["controls"][1],
                                controls_version=last.get("version"), designated_sha256=files["designated"][1]))
    for k, v in want.items():
        if cert.get(k) != v:
            why.append(f"the certificate's {k} is not this release's ({str(cert.get(k))[:40]!r}): a foreign or stale certificate")
    lit = terminal_literal(csha, man_sha.get("screen"), target_sha, files["controls"][1])
    if lit not in [l.strip() for l in rb.decode(errors="replace").splitlines()]:
        why.append("the terminal review record does not carry ADOPT row19-p80-terminal for this exact certificate, screen, "
                   "contract, target and controls (an unreviewed or changed certificate)")
    if why:
        return None, why, csha, None

    # ---- the controller's representation of the attempts: ledger, plans, receipts, EC2 register (each file read once)
    root, camp = screen["storage"]["root"], screen["storage"]["campaign"]
    try:
        led, _ = _read_once(os.path.join(camp, "budget.json"))
        entries = [e for e in (led.get("entries") or {}).values() if isinstance(e, dict) and e.get("kind") == "shard"]
    except Exception as e:
        return None, [f"the campaign ledger is unreadable ({type(e).__name__}): attempts and ownership are unknown"], csha, None
    by_job = {}
    for e in entries:
        n = e.get("rep")
        if not _int(n) or n in by_job:
            why.append(f"ledger job number {n!r} is malformed or duplicated: ownership ambiguous"); continue
        by_job[n] = e
    plans, plan_sha = {}, {}
    for pp in sorted(glob.glob(os.path.join(root, "plans", "job_*.json"))):
        name = os.path.basename(pp)[4:-5]
        try:
            n = int(name); assert name == str(n)
            d, psha = _read_once(pp)
            assert isinstance(d.get("slots"), list) and d["slots"]
            assert all(isinstance(s, dict) and _int(s.get("rep")) and isinstance(s.get("indices"), list) and s["indices"]
                       and all(_int(i) for i in s["indices"]) for s in d["slots"])
        except Exception:
            why.append(f"plan {os.path.basename(pp)} is malformed or unreadable: its claims are unknown (ownership ambiguous)"); continue
        plans[n] = d; plan_sha[n] = psha
    for n in by_job:
        if n not in plans:
            why.append(f"ledger job {n} has no plan: its claims are unknown (ownership ambiguous)")
    claims = {}
    for n, d in plans.items():
        for c in _plan_coords(d):
            claims.setdefault(c, set()).add(n)
    receipts = cert.get("receipts")
    if not (isinstance(receipts, list) and receipts):
        why.append("the certificate binds no gate receipt")
        receipts = []
    ident = receipt_identity(screen, adoption)
    rdocs, bound = [], []                                                   # bound: [(rel, sha256, doc)] in path order
    for x in receipts:
        rel = (x or {}).get("path") if isinstance(x, dict) else None
        if not _receipt_rel(rel):
            why.append(f"a bound receipt path {rel!r} is not a gate/watch_refit_*.json receipt"); continue
        try:
            doc, s = _read_once(os.path.join(root, rel))
        except Exception as e:
            why.append(f"the bound receipt {rel} is unreadable ({type(e).__name__})"); continue
        if s != x.get("sha256"):
            why.append(f"the bound receipt {rel} is not the certified bytes"); continue
        w = receipt_problems(doc, C, ident, by_job, plan_sha)
        if w:
            why += [f"the bound receipt {rel}: {v}" for v in w]; continue
        rdocs.append(doc); bound.append((rel, s, doc))
    bound.sort(key=lambda t: t[0])
    # B-R2: the NEWEST receipt is current evidence; it is read once (bytes frozen and hashed) and must itself be a valid,
    # zero-alarm production refit receipt of this campaign that summarises every ledger job, AND be either a certified receipt
    # (the reviewed state) or a validated successor of the newest certified one - never trusted for one parsed sublist alone.
    newest = sorted(glob.glob(os.path.join(root, "gate", "watch_refit_*.json")))
    newest_doc, current = None, None
    if newest:
        nrel = os.path.join("gate", os.path.basename(newest[-1]))
        try:
            newest_doc, nsha = _read_once(newest[-1])
        except Exception as e:
            newest_doc = None; why.append(f"the newest gate receipt is unreadable ({type(e).__name__})")
        if newest_doc is not None:
            w = receipt_problems(newest_doc, C, ident, by_job, plan_sha, every_job=True)
            if w:
                why += [f"the newest gate receipt {nrel}: {v}" for v in w]
            elif bound:
                rel_ok = {r: s for r, s, _ in bound}
                if nrel in rel_ok:
                    if rel_ok[nrel] != nsha:
                        why.append(f"the newest gate receipt {nrel} is a certified path with other bytes than the certified ones")
                    else:
                        current = dict(path=nrel, sha256=nsha, relation="certified (the reviewed state)")
                else:
                    w = successor_problems(bound, nrel, newest_doc)
                    if w:
                        why += [f"the newest gate receipt {nrel} is not a validated successor of the certified receipts: {v}" for v in w]
                    else:
                        current = dict(path=nrel, sha256=nsha, relation=f"validated successor of {bound[-1][0]}")
    if newest_doc is None and not why:
        why.append("no gate receipt exists")
    reg_named = set()
    rp = os.path.join(root, "ec2", "register.json")
    if os.path.exists(rp):
        try:
            reg, _ = _read_once(rp)
            for a in (reg.get("attempts") or {}).values():
                for k in (a.get("coordinates") or {}):
                    reg_named.add(tuple(int(v) for v in k.split("/")))
        except Exception as e:
            why.append(f"the EC2 register is unreadable ({type(e).__name__}): EC2 ownership unknown")
    if why:
        return None, why, csha, None

    def env_of(n):
        try:
            return C.resolve_envelope(screen, screen_path, "refit", int(n))[0]
        except Exception:
            return None

    def history_of(docs):
        seen, bad = {}, []
        for doc in docs:
            for c, atts in C.crash_history(doc, env_of).items():
                for a in atts:
                    k = (c, a["job"])
                    if k in seen and seen[k] != a:
                        bad.append(k)
                    seen[k] = a
        h = {}
        for (c, _n), a in sorted(seen.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            h.setdefault(c, []).append(a)
        return h, bad

    history, bad = history_of(rdocs)
    if bad:
        return None, [f"the bound receipts disagree on attempts {bad[:3]}"], csha, None
    newest_hist, _ = history_of([newest_doc])
    nxt = (max(by_job) + 1) if by_job else 1
    env_next = env_of(nxt)
    if env_next is None:
        return None, [f"the envelope of the next ordinary job ({nxt}) is not resolvable: the crash rule cannot be evaluated"], csha, None
    excluded = C.crash_excluded(history, env_next)
    rs = desig.get("rescue") or {}
    rescue_on = rs.get("enabled") is True and rs.get("resources") is not None
    rescue_jobs = sorted(n for n, d in plans.items() if d.get("route") == RESCUE_ROUTE)
    if rescue_jobs and not rescue_on:
        why.append(f"rescue-route plans {rescue_jobs[:3]} exist under a declaration whose rescue route is disabled")
    scope = C.lengau_scope(desig, set(claims))
    D = C.designated_coordinates(desig)

    # ---- every certified coordinate
    certified, needed, exhausted_used = {}, set(), False
    missing = cert.get("missing")
    if not (isinstance(missing, list) and missing):
        why.append("the certificate certifies no coordinate")
        missing = []
    for e in missing:
        rep, idx = (e or {}).get("rep"), (e or {}).get("index")
        if not (_int(rep) and rep in DESIGNATED and _int(idx) and 0 <= idx < PREFIX):
            why.append(f"a certificate entry names {rep!r}/{idx!r}: not a designated prefix coordinate (an absent original is not certifiable)"); continue
        c, tag = (rep, idx), f"certificate {rep}/{idx}"
        if c in certified:
            why.append(f"{tag}: certified twice"); continue
        if c not in D:
            why.append(f"{tag}: not in the controller's designated set"); continue
        if c not in scope:
            why.append(f"{tag}: outside Lengau's scope (an unclaimed EC2-designated coordinate waits for the EC2 epoch): ownership outstanding")
        if c in reg_named:
            why.append(f"{tag}: named by an EC2 register attempt: ownership ambiguous")
        for n in sorted(claims.get(c, ())):
            le = by_job.get(n)
            if le is None:
                why.append(f"{tag}: plan job_{n} has no ledger entry: ownership ambiguous")
            elif le.get("state") != "settled":
                why.append(f"{tag}: job {n} ({le.get('state')}) still owns it: live or planned")
        h = history.get(c, [])
        if e.get("crashes") != h:
            why.append(f"{tag}: its attempts are not exactly the crashed-worker dispositions its bound receipts carry (invented or missing attempts)")
        if newest_hist.get(c, []) != h:
            why.append(f"{tag}: the newest gate receipt carries other attempts than the certificate's receipts")
        if c not in excluded:
            why.append(f"{tag}: below {getattr(C, 'DESIGN_MAX_CRASHES', 2)} same-envelope fatal crashes in the envelope the next "
                       "ordinary job uses: the ordinary planner may still attempt it (no crash branch)")
        for a in h:
            le = by_job.get(a.get("job"))
            if le is None or le.get("job_id") != a.get("job_id"):
                why.append(f"{tag}: crash attempt of job {a.get('job')} has no ledger entry with its PBS id")
            needed.add(a.get("job"))
        resc = sorted(n for n in rescue_jobs if c in _plan_coords(plans[n]))
        br = e.get("branch")
        if br == "rescue-failed":
            r = e.get("rescue") or {}
            if not rescue_on:
                why.append(f"{tag}: the bound declaration's rescue route is disabled: no rescue outcome can exist")
            elif resc != [r.get("job")]:
                why.append(f"{tag}: the certified rescue job {r.get('job')!r} is not the one rescue-route plan holding it ({resc})")
            elif h and r["job"] <= max(a["job"] for a in h):
                why.append(f"{tag}: the rescue attempt does not follow its crashes")
            elif (by_job.get(r["job"]) or {}).get("job_id") != r.get("job_id"):
                why.append(f"{tag}: the rescue job has no ledger entry with its PBS id")
            else:
                needed.add(r["job"])
        elif br == "allowance-exhausted":
            exhausted_used = True
            if resc:
                why.append(f"{tag}: rescue-route plan(s) {resc} held it: its branch is rescue-failed, not allowance-exhausted")
            if "rescue" in e:
                why.append(f"{tag}: an allowance-exhausted entry names a rescue attempt")
        else:
            why.append(f"{tag}: branch {br!r} is not one of {BRANCHES}")
        certified[c] = dict(branch=br, crash_jobs=[a.get("job") for a in h], rescue_job=(e.get("rescue") or {}).get("job"))

    # ---- settlement receipts of every attempt, bound exactly
    want_settle = {}
    for n in sorted(x for x in needed if _int(x)):
        le = by_job.get(n) or {}
        if le.get("state") != "settled":
            why.append(f"job {n} is not settled: its attempt is not terminal")
        want_settle[str(n)] = {k: le.get(k) for k in SETTLEMENT_FIELDS}
    if cert.get("settlements") != want_settle:
        why.append("the certificate's settlement receipts are not exactly the ledger's settled entries of its attempts")

    # ---- the finite global rescue allowance (allowance-exhausted only). Codex re-review choice 3: this is a RESERVATION QUOTA
    # (declared allowance minus the ledger reservations of every rescue job), not charged-hour exhaustion. The "full
    # reservation" is priced in the next ORDINARY envelope, which is valid only if the future adopted rescue amendment's request
    # reserves exactly that; otherwise that amendment must price the rescue envelope here (and re-review this consumer). The
    # branch stays unreachable under the v16 declaration (rescue disabled: a hold, not exhaustion).
    if exhausted_used:
        A_ = rs.get("allowance_core_h")
        jobs_ = {str(n): (by_job.get(n) or {}).get("reserved_core_h") for n in rescue_jobs}
        if not (_real(A_) and A_ > 0):
            why.append("the bound declaration declares no finite rescue allowance")
        elif not all(_real(v) and v >= 0 for v in jobs_.values()):
            why.append("a rescue job has no finite reservation: the allowance cannot be established")
        else:
            live = [n for n in rescue_jobs if (by_job.get(n) or {}).get("state") != "settled"]
            full = C.envelope_core_h(env_next); left = A_ - sum(jobs_.values())
            if cert.get("rescue_allowance") != dict(allowance_core_h=A_, rescue_jobs=jobs_, full_reservation_core_h=full):
                why.append("the certificate's rescue-allowance evidence is not the declaration's allowance and the ledger's rescue jobs")
            if live:
                why.append(f"rescue job(s) {live[:3]} are not settled: the allowance is not exhausted")
            if left >= full:
                why.append(f"the rescue allowance is not exhausted: {left:.1f} core-h remain, at least one full reservation ({full:.1f})")
    elif cert.get("rescue_allowance") is not None:
        why.append("the certificate carries rescue-allowance evidence but certifies no allowance-exhausted coordinate")
    return (None if why else certified), why, csha, (None if why else current)


# ------------------------------------------------------------------------------------------------------------------------
# collection and terminality (validation only; no statistic)
# ------------------------------------------------------------------------------------------------------------------------
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


def terminality(items, certified):
    """(per-dataset terminal state, non-terminal list, conflicts). `certified` = {(rep, index): entry} from a verified
    terminal certificate ({} without one). No statistic is read."""
    state, open_, conflict = {}, [], []
    for (r, i) in sorted(certified):
        it = items.get(r)
        if it is None:
            continue
        if it["original"] is None or bool(it["original"]["run"]["failed"]):
            conflict.append(f"rep {r}: index {i} certified, but the dataset's original is absent or failed (not certifiable)")
        elif i not in it["missing"]:
            conflict.append(f"rep {r}: index {i} certified missing but holds a valid record (never relabelled)")
    for r in DESIGNATED:
        it = items[r]
        if it["original"] is None:
            open_.append(f"rep {r}: no original (an absent original has no certificate route)")
            continue
        if bool(it["original"]["run"]["failed"]):
            state[r] = dict(terminal="original failed", reason=str(it["original"]["run"].get("failed_reason", "")))
            continue
        uncert = [i for i in it["missing"] if (r, i) not in certified]
        if uncert:
            open_.append(f"rep {r}: designated indices {uncert[:8]}{'...' if len(uncert) > 8 else ''} missing ({len(uncert)})")
        elif it["missing"]:
            state[r] = dict(terminal="certified missing", indices=list(it["missing"]),
                            branches={str(i): certified[(r, i)]["branch"] for i in it["missing"]})
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
                row["reason"] = f"{st['terminal']}: {st.get('reason') or st.get('branches')}"
            out[r] = row
    finally:
        A.run_dataset = keep
    return out


def release(screen_path, orig_path, target_path, adoption_rel, terminal_rel=None, terminal_review_rel=None, check_git=True,
            controller_module=None):
    if not os.path.exists(target_path):
        return dict(status="REFUSED", reasons=["the target file is absent"])
    target = R.load_target(target_path)                                       # ONE read: these bytes decide
    ab, asha, ad, w = adoption_snapshot(adoption_rel, check_git)              # ONE read of the adoption (B-R1)
    if w:
        return dict(status="REFUSED", reasons=[w])
    why = seal_problems(screen_path, orig_path, target, adoption_rel, check_git=check_git, adoption=(ab, ad))
    if why:
        return dict(status="REFUSED", reasons=why)
    screen = json.load(open(screen_path)); origm = json.load(open(orig_path))
    C = controller_module if controller_module is not None else (controller() if terminal_rel is not None else None)
    certified, twhy, csha, current = terminal_authority(terminal_rel, terminal_review_rel, screen_path, screen, ad, target[0], C,
                                                        check_git=check_git)
    if twhy:
        return dict(status="HELD", reasons=twhy)
    why, items = collect(screen, origm)
    if why:
        return dict(status="HELD", reasons=why[:50], n_reasons=len(why))
    state, open_, conflict = terminality(items, certified)
    if conflict:
        return dict(status="HELD", reasons=conflict)
    if open_:
        return dict(status="NOT TERMINAL", reasons=open_, n_terminal=len(state), n_designated=N_DESIGNATED,
                    note="one terminal look: no interval, count or decision is computed before every designated dataset is terminal")
    per = _aggregate(items, state)
    tsha, tg = target; t = tg["targets"]["/".join(PRIMARY)]; lo, hi = float(t["lo"]), float(t["hi"])
    refit = [tuple(v["refit"]) for v in per.values() if v["refit_usable"]]
    return dict(schema=RESULT_SCHEMA, status="RELEASED", contract=CONTRACT, contract_sha256=contract_sha(),
                target=dict(lo=lo, hi=hi, sha256=tsha), adoption_sha256=asha, terminal_certificate_sha256=csha,
                terminal_current_receipt=current,
                terminal_certified={f"{r}/{i}": v for (r, i), v in sorted((certified or {}).items())}, n_attempted=N_DESIGNATED,
                failed_originals={str(r): v["terminal"]["reason"] for r, v in per.items() if v["terminal"]["terminal"] == "original failed"},
                unavailable={str(r): v["reason"] for r, v in per.items() if v["status"] != "usable"},
                refit=decide(refit, lo, hi, N_DESIGNATED, all_terminal=True),
                cluster_companion=cluster_companion(per, lo, hi, N_DESIGNATED),
                per_dataset={str(r): v for r, v in per.items()})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True); ap.add_argument("--originals", required=True)
    ap.add_argument("--target", required=True); ap.add_argument("--adoption", required=True)
    ap.add_argument("--terminal", default=None); ap.add_argument("--terminal-review", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.out and os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists; a release is written once"); return 2
    res = release(a.screen, a.originals, a.target, a.adoption, terminal_rel=a.terminal, terminal_review_rel=a.terminal_review)
    if res["status"] != "RELEASED":
        print(f"{res['status']}:"); [print("  -", w) for w in res["reasons"]]; return 2
    if a.out:
        with open(a.out, "x") as fh:
            json.dump(res, fh, indent=1)
    cc = res["cluster_companion"]
    print(f"RELEASED: refit {res['refit']['decision']} (n {res['refit']['n_usable']}, Kmax {res['refit']['k_max']}, M {res['refit']['M_unavailable']}); "
          f"cluster companion (no decision): n {cc['n_usable']}, Kmax {cc['k_max']}; paired {cc['paired']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
