"""Width vs count, settled offline from the per-start archive. NO REFITTING.

The fit audit found that a start at 0.50 jitter is ~3.2x as likely to hold the better optimum as a
start at the pipeline's 0.25 (6.8x on M3H).  That comparison was uncontrolled: the two batches differ
in SIZE (64 vs 16) and in SEED STREAM as well as in width.  This scores fixed prefixes of the
archived starts at EQUAL count, so width is compared against count on the same footing, and adds a
disjoint second prefix at the SAME width so the seed effect can be read beside the width effect.

Every number here comes from log-likelihoods already recorded in the audit's per-start archive.
Nothing is refit.  Held-out scores ARE recomputed — that is evaluation of an already-fitted theta
via models.concept_scores, not fitting — because a prefix that misses a large TRAINING optimum but
lands on the same held-out score is not a practical failure, and the training gap alone cannot say
which happened.

Two corrections to the brief's wording, both applied:
  - "the 8 cold starts" is only true at the outer size; the inner pipeline uses 4.  All cold starts
    of the fit are used, whatever their number, and the count is reported.
  - For M2K the challenge batch LEADS with the four separated-skew starts, so a k = 8 challenge
    prefix is 4 skew + 4 jittered, not 8 jittered.  M2K is reported separately throughout and is
    excluded from the pooled width comparison.

Run:
    NPROC=1 .venv/Scripts/python.exe workspace_demo/t1_access/score_prefixes.py
"""
from __future__ import annotations

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

import models as M                                    # noqa: E402
import simulate as S                                  # noqa: E402
import audit_fits as AF                               # noqa: E402

RESULTS = AF.RESULTS
CSV_OUT = os.path.join(RESULTS, "prefix_scoring.csv")
MD_OUT = os.path.join(RESULTS, "prefix_scoring.md")
BALANCED_REPS = (2, 3, 4, 5)            # the block where every setting carries the archive
MISS_TOL = AF.MISS_TOL


def prefixes(arch: list) -> dict:
    """{label: [start entries]} — every recipe scored, all of them including ALL cold starts."""
    cold = [x for x in arch if x["batch"] == "cold"]
    ex = [x for x in arch if x["batch"] == "extra"]
    ch = [x for x in arch if x["batch"] == "challenge"]
    ex = sorted(ex, key=lambda x: x["i"])
    ch = sorted(ch, key=lambda x: x["i"])
    out = {"cold only": cold}
    for k in (8, 16, 32, 64):
        if len(ex) >= k:
            out[f"+{k} @0.25"] = cold + ex[:k]
    for k in (8, 16):
        if len(ch) >= k:
            out[f"+{k} @0.50"] = cold + ch[:k]
        if len(ex) >= k // 2 and len(ch) >= k // 2:
            out[f"+{k} mixed"] = cold + ex[:k // 2] + ch[:k // 2]
        # the seed control: a DISJOINT second prefix at the SAME width as +k @0.25
        if len(ex) >= 16 + k:
            out[f"+{k} @0.25 (seed B)"] = cold + ex[16:16 + k]
    return out


def best_of(entries: list) -> tuple:
    """(loglik, theta) of the best CONVERGED start in the set, matching models._pick's preference
    for converged runs and its fallback to any finite run."""
    conv = [x for x in entries if x["converged"] and x["loglik"] is not None]
    pool = conv if conv else [x for x in entries if x["loglik"] is not None]
    if not pool:
        return float("-inf"), None
    b = max(pool, key=lambda x: x["loglik"])
    return float(b["loglik"]), b.get("theta")


def score_unit(path: str) -> list[dict]:
    rows = json.load(open(path, encoding="utf-8"))
    if not rows or not rows[0].get("starts_archive"):
        return []
    gen, grid, rep = rows[0]["generator"], rows[0]["grid"], rows[0]["rep"]
    sets = AF.build_sets(gen, json.loads(grid), rows[0]["seed"])
    out = []
    for r in rows:
        arch = r["starts_archive"]
        ref_ll, ref_theta = best_of(arch)
        pres = prefixes(arch)
        test = sets[r["size"]]["test"]
        n_tr = max(int(r["n_heldout_trials"]), 1)
        # score each DISTINCT theta once (many prefixes land on the same solution)
        cache: dict[tuple, float] = {}

        def heldout(theta) -> float:
            if theta is None:
                return float("nan")
            key = tuple(theta)
            if key not in cache:
                cache[key] = AF.heldout_joint(r["member"], np.asarray(theta, dtype=float), test)
            return cache[key]

        ref_h = heldout(ref_theta)
        for label, entries in pres.items():
            ll, th = best_of(entries)
            gap = ref_ll - ll if np.isfinite(ll) and np.isfinite(ref_ll) else float("nan")
            h = heldout(th)
            out.append(dict(
                generator=gen, grid=grid, rep=rep, size=r["size"], member=r["member"],
                recipe=label, n_cold=sum(1 for x in entries if x["batch"] == "cold"),
                n_starts=len(entries), ref_loglik=ref_ll, prefix_loglik=ll, gap=gap,
                miss=int(np.isfinite(gap) and gap > MISS_TOL),
                heldout=h, ref_heldout=ref_h,
                heldout_change=(ref_h - h) / n_tr if np.isfinite(h) and np.isfinite(ref_h) else float("nan"),
                n_heldout_trials=n_tr,
                seconds_strong=r["seconds_strong"], seconds_pipeline=r["seconds_pipeline"],
                n_archived=r["n_archived"]))
    return out


def main() -> None:
    import glob
    t0 = time.time()
    files = sorted(glob.glob(os.path.join(AF.CKPT_DIR, "*.json")))
    print(f"[prefix] {len(files)} checkpoint files; runtime {S.runtime_versions()}")
    from joblib import Parallel, delayed
    batches = Parallel(n_jobs=max(1, (os.cpu_count() or 2) - 1), verbose=5)(
        delayed(score_unit)(f) for f in files)
    rows = [r for b in batches for r in b]
    print(f"[prefix] {len(rows)} scored rows in {(time.time() - t0) / 60:.1f} min")
    if not rows:
        raise SystemExit("no archived units found")
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {CSV_OUT} ({len(rows)} rows)")
    write_md(rows, time.time() - t0)


def block(rows: list[dict], reps) -> list[dict]:
    return [r for r in rows if r["rep"] in reps]


def table(L: list, rows: list[dict], members, title: str) -> None:
    recipes = ["cold only", "+8 @0.25", "+8 @0.25 (seed B)", "+8 @0.50", "+8 mixed",
               "+16 @0.25", "+16 @0.25 (seed B)", "+16 @0.50", "+16 mixed", "+32 @0.25", "+64 @0.25"]
    L.append(f"\n### {title}\n")
    L.append("| recipe | starts added | n | miss rate | mean gap | max gap | "
             "mean held-out loss (nat/trial) | max held-out loss |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for rec in recipes:
        rs = [r for r in rows if r["recipe"] == rec and r["member"] in members]
        if not rs:
            continue
        g = np.array([r["gap"] for r in rs], dtype=float)
        hc = np.array([r["heldout_change"] for r in rs], dtype=float)
        fin, hfin = np.isfinite(g), np.isfinite(hc)
        added = rs[0]["n_starts"] - rs[0]["n_cold"]
        L.append(f"| `{rec}` | {added} | {len(rs)} | {np.mean([r['miss'] for r in rs]):.3f} | "
                 f"{np.nanmean(g[fin]) if fin.any() else 0:.2f} | "
                 f"{np.nanmax(g[fin]) if fin.any() else 0:.2f} | "
                 f"{np.nanmean(hc[hfin]) if hfin.any() else float('nan'):+.5f} | "
                 f"{np.nanmax(hc[hfin]) if hfin.any() else float('nan'):+.5f} |")


def write_md(rows: list[dict], secs: float) -> None:
    skew = [m for m in AF.MEMBERS if any(p.startswith("alpha") for p in M.MEMBERS[m].params)]
    nonskew = [m for m in AF.MEMBERS if m not in skew]
    bal = block(rows, BALANCED_REPS)
    other = block(rows, (1,))

    L = []
    L.append("# Width vs count — fixed prefixes of the archived starts, no refitting\n")
    L.append(f"**Runtime identity:** `{S.runtime_versions()}`\n")
    L.append("> Every log-likelihood here was recorded during the fit audit; nothing is refit. "
             "Held-out scores are recomputed from already-fitted parameter vectors via "
             "`models.concept_scores` — evaluation, not fitting — because a prefix that misses a "
             "large TRAINING optimum but lands on the same held-out score is not a practical "
             "failure, and the training gap alone cannot tell the two apart.\n")
    L.append(f"Reference for every row: the best converged training log-likelihood over ALL "
             f"{rows[0]['n_archived']} archived starts of that member-fit. A *miss* is a prefix "
             f"falling more than {MISS_TOL} nat short of it — the audit's own definition. "
             f"Analysis time {secs / 60:.1f} min.\n")
    L.append(f"**Balanced block: reps {BALANCED_REPS} — {len({(r['generator'], r['grid'], r['rep']) for r in bal})} "
             f"units, all 16 settings.** Rep 1's {len({(r['generator'], r['grid'], r['rep']) for r in other})} "
             f"stragglers are reported separately and pooled into nothing.\n")
    L.append(f"⚠ `+k @0.50` is the wider batch; `+k @0.25 (seed B)` is a DISJOINT second prefix at "
             f"the SAME width as `+k @0.25`, drawn from the same stream — it measures how much of any "
             f"difference is simply a second draw rather than the width.\n")
    L.append(f"⚠ **M2K is excluded from the pooled tables** and shown on its own: its challenge batch "
             f"leads with four separated-skew starts at ±{S.ALPHA_SEP}, so `+8 @0.50` is 4 skew + 4 "
             f"jittered for M2K and is not a width comparison at all.\n")
    L.append("⚠ Cold-start count differs by size — 8 at the outer training set, 4 at the inner. "
             "Every recipe includes all cold starts of its fit; the `starts added` column counts "
             "only what the recipe adds.\n")

    table(L, bal, nonskew, "All seven non-skew members, balanced block")
    for m in nonskew:
        sub = [r for r in bal if r["member"] == m]
        if sub and any(r["miss"] for r in sub):
            table(L, sub, [m], f"`{m}`")
    table(L, bal, skew, "`M2K` — NOT a width comparison (skew starts lead its challenge batch)")
    if other:
        table(L, other, nonskew, "Rep 1 stragglers (6 units), reported separately")

    # ---- the headline comparison, stated as a ratio at equal count
    L.append("\n## The controlled comparison\n")
    for k in (8, 16):
        rs_a = [r for r in bal if r["recipe"] == f"+{k} @0.25" and r["member"] in nonskew]
        rs_b = [r for r in bal if r["recipe"] == f"+{k} @0.50" and r["member"] in nonskew]
        rs_s = [r for r in bal if r["recipe"] == f"+{k} @0.25 (seed B)" and r["member"] in nonskew]
        rs_m = [r for r in bal if r["recipe"] == f"+{k} mixed" and r["member"] in nonskew]
        if not (rs_a and rs_b):
            continue
        ma, mb = np.mean([r["miss"] for r in rs_a]), np.mean([r["miss"] for r in rs_b])
        ms = np.mean([r["miss"] for r in rs_s]) if rs_s else float("nan")
        mm = np.mean([r["miss"] for r in rs_m]) if rs_m else float("nan")
        L.append(f"**At {k} added starts** (non-skew members, balanced block): "
                 f"miss rate **{ma:.3f} at 0.25**, **{mb:.3f} at 0.50**, "
                 f"**{ms:.3f} at 0.25 from a disjoint second draw**, **{mm:.3f} mixed**. "
                 f"Width effect {ma - mb:+.3f}; seed effect at fixed width {ma - ms:+.3f}.")
    L.append("\nIf the width effect is large against the seed effect, width is doing the work; if "
             "they are comparable, the audit's 3.2x was a seed artefact. The tables above answer it "
             "per member as well as in pool.\n")

    # ---- per-member cost, so a recipe can be priced
    L.append("## Cost per start, per member\n")
    L.append("From the audit's own timings: the strong search ran "
             f"{AF.N_EXTRA + AF.N_CHALLENGE} added starts per member-fit.\n")
    L.append("| member | size | s/start | cost of +16 | cost of +64 | ratio |")
    L.append("|---|---|---:|---:|---:|---:|")
    for m in AF.MEMBERS:
        for size in AF.SIZES:
            rs = [r for r in rows if r["member"] == m and r["size"] == size and r["recipe"] == "cold only"]
            if not rs:
                continue
            per = float(np.mean([r["seconds_strong"] for r in rs])) / (AF.N_EXTRA + AF.N_CHALLENGE)
            L.append(f"| `{m}` | {size} | {per:.2f} | {per * 16:.0f} s | {per * 64:.0f} s | "
                     f"{per * 64 / max(per * 16, 1e-9):.0f}x |")
    L.append("\nA recipe of **cold + 16 at 0.50** costs a quarter of **cold + 64 at 0.25** on every "
             "member, so if it also matches or beats it on miss rate the choice is settled on both "
             "axes at once.\n")
    with open(MD_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"[write] {MD_OUT}")


if __name__ == "__main__":
    main()
