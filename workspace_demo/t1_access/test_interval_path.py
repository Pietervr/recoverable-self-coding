"""The §8.2 interval method is a declared Config choice carried through the runner (Codex, 12 Sept 2026, finding 3):
with interval="refit" analyze_dataset's intervals come from the refitting bootstrap (the point estimates unchanged,
the cluster interval kept beside), an unusable refit interval is an assay failure, the row carries the method and its
counts, and the code/config hash separates the two methods. run_dataset is mocked; nothing is fitted."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import json
import numpy as np
import analyze as A
import simulate as S

C, per = 64, 6 * 7 * 4
layers = np.array([10, 41, 60])
fam = np.repeat(np.arange(8), 8)
rng = np.random.default_rng(0)
ds = A.Dataset(y=rng.normal(size=(C * per, layers.size)), k=np.tile(np.repeat(np.arange(7.0), 4 * 6), C),
               concept=np.repeat(np.arange(C), per), family=fam, layers=layers)
MEMBERS = ("M2B", "M2H", "M2S", "M2K", "M3", "M3H", "M3V", "M3L")
FAIL_SEEDS = set()            # refit resamples whose run_dataset seed (analysis seed + 1 + rep) is here fail

def fake_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    folds = A.stratified_folds(sub.family, cfg.n_outer, seed) if outer_folds is None else outer_folds
    r = np.random.default_rng(seed)
    Cs, L = sub.n_concepts, sub.n_layers
    base = 0.02 + 0.005 * r.normal()                       # per-replicate shift: the refit interval is not degenerate
    delta = {p: base * (1 if p == "selection" else 2) + 0.001 * r.normal(size=(L, Cs)) for p in A.PREDICTORS}
    failed = seed in FAIL_SEEDS and sub.group is not None
    return dict(layers=sub.layers, folds=folds, members=MEMBERS, delta=delta, logq=np.zeros((L, len(MEMBERS), Cs)),
                n_c=np.bincount(sub.concept, minlength=Cs).astype(float),
                selected=[[("M2B", "M3")] * len(folds)] * L, converged=np.ones((L, len(folds), len(MEMBERS)), bool),
                inner_conv=np.ones((L, len(folds), len(MEMBERS))), inner_nonfinite=np.zeros((L, len(folds), len(MEMBERS)), bool),
                recovery=np.zeros((L, len(folds), len(MEMBERS)), np.int8), failed=failed,
                failed_reason="fold 0: every member of a family unscorable in inner selection" if failed else "",
                params={m: np.zeros((L, len(folds), 2)) for m in MEMBERS}, fit_seconds=2.0)
A.run_dataset = fake_run_dataset

# 1. cluster (the default): as before — no refit call, interval fields say cluster
c1 = A.analyze_dataset(ds, A.Config(), seed=5)
assert c1["interval"]["method"] == "cluster" and "cluster" not in c1["predictors"]["selection"]
assert c1["predictors"]["selection"]["decision"] == "mixture"

# 2. refit: the intervals come from the refitting bootstrap, the point is unchanged, the cluster CI is kept beside
cfg = A.Config(interval="refit", n_boot_refit=8)
c2 = A.analyze_dataset(ds, cfg, seed=5)
sel1, sel2 = c1["predictors"]["selection"], c2["predictors"]["selection"]
assert c2["interval"]["method"] == "refit" and c2["interval"]["n_used"] == 8 and c2["interval"]["usable"]
assert sel2["ws"]["point"] == sel1["ws"]["point"] and sel2["cluster"]["ws"] == sel1["ws"]
assert (sel2["ws"]["lo"], sel2["ws"]["hi"]) != (sel1["ws"]["lo"], sel1["ws"]["hi"])
assert sel2["usable"] and sel2["decision"] in ("mixture", "graded", "inconclusive")
assert "ws_minus_early" in sel2 and np.isfinite(sel2["ws_minus_early"]["lo"])
assert len(c2["interval"]["replicates"]) == 8 and c2["interval"]["policy"] == "every replicate scored"
row = S._row("M3", {}, 0, 4, layers.tolist(), c2, 1.0)
assert row["interval_method"] == "refit" and row["interval_n_used"] == 8 and row["interval_usable"] == 1
assert row["selection_ws_lo"] == sel2["ws"]["lo"]
assert S.config_hash(A.Config(), 4, (41,), 2026) != S.config_hash(cfg, 4, (41,), 2026)

# 3. one failed resample under the every-replicate policy: the refit interval is unusable -> assay failure, not inconclusive
FAIL_SEEDS.add(5 + 1 + 2)                  # resample 2 of the analysis at seed 5
c3 = A.analyze_dataset(ds, cfg, seed=5)
sel3 = c3["predictors"]["selection"]
assert not c3["interval"]["usable"] and c3["interval"]["n_failed"] == 1 and np.isnan(sel3["ws"]["lo"])
assert sel3["decision"] == "assay failure" and sel3["ws"]["point"] == sel1["ws"]["point"]
assert S._row("M3", {}, 0, 4, layers.tolist(), c3, 1.0)["interval_usable"] == 0
# ... unless the policy is relaxed by an explicit amendment
c4 = A.analyze_dataset(ds, A.Config(interval="refit", n_boot_refit=8, refit_min_usable=0.8), seed=5)
assert c4["interval"]["usable"] and c4["predictors"]["selection"]["decision"] != "assay failure"
try:
    A.analyze_dataset(ds, A.Config(interval="bogus"), seed=5); raise SystemExit("unknown interval accepted")
except ValueError:
    pass

# 4. nothing is lost at the row boundary (review 3, finding 5): every band and ws - early per predictor, the companion
#    cluster interval, each predictor's interval availability, the seed / policy / folds / failure reasons / replicate
#    statistics of the bootstrap, and the three separate flags
row2, row3 = S._row("M3", {}, 0, 4, layers.tolist(), c2, 1.0), S._row("M3", {}, 1, 4, layers.tolist(), c3, 1.0)
for p in A.PREDICTORS:
    for band in ("ws", "early", "late", "ws_minus_early"):
        assert np.isfinite(row2[f"{p}_{band}_lo"]) and row2[f"{p}_{band}_point"] == c2["predictors"][p][band]["point"]
    assert row2[f"{p}_cluster_ws_lo"] == c1["predictors"][p]["ws"]["lo"] and row2[f"{p}_interval_usable"] == 1 and row2[f"{p}_interval_n_used"] == 8
assert row2["interval_seed"] == 5 and row2["interval_policy"] == "every replicate scored" and row2["primary_available"] == 1
assert len(json.loads(row2["interval_replicates"])) == 8 and len(json.loads(row2["interval_outer_folds"])) == A.N_OUTER
assert row3["failed"] == 0 and row3["primary_available"] == 0 and row3["selection_interval_usable"] == 0 and np.isnan(row3["selection_ws_lo"])
assert json.loads(row3["interval_failed_reasons"]) and row3["interval_n_failed"] == 1

# 5. the bookkeeping (review 3, finding 3): a valid original point with an unusable interval keeps its point in the
#    target's mean, leaves the coverage denominator, and is an assay failure — never a "usable" success
import pandas as pd, tempfile, os
FAIL_SEEDS.clear()
rows = [S._row("M3", {}, r, 4, layers.tolist(), A.analyze_dataset(ds, cfg, seed=100 + r), 1.0) for r in range(4)]
FAIL_SEEDS.add(104 + 1 + 2)                # resample 2 of the analysis at seed 104
rows.append(S._row("M3", {}, 4, 4, layers.tolist(), A.analyze_dataset(ds, cfg, seed=104), 1.0))
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "power.csv")
    pd.DataFrame(rows).to_csv(p, index=False)
    s = S.summarize(p).iloc[0]
assert s["n"] == 5 and s["n_points"] == 5 and s["n_usable"] == 4 and s["n_interval_missing"] == 1 and s["failure"] == 0.2
assert abs(s["mean_point"] - np.mean([r["selection_ws_point"] for r in rows])) < 1e-12        # every valid point estimates theta_g
assert np.isfinite(s["coverage"]) and 0.0 <= s["coverage"] <= 1.0, s["coverage"]
assert abs(s["mean_se"] - np.mean([r["selection_ws_se"] for r in rows[:4]])) < 1e-9      # over the four usable intervals only
# 6. dataset seeds (review 4, finding 1): the two M3H recovery points that collided under the v1.2 weighted tag now
#    differ; every point with at most one grid value keeps its v1.2 seed (the d4v12b null rows depend on it)
def old_seed(name, kw, rep, D, seed):
    tag = sum((i + 1) * int(round(1000 * float(v))) for i, v in enumerate(kw.get(x, 0.0) for x in ("tau", "omega", "sep", "pi0", "alpha", "scale")))
    return int(np.random.default_rng([seed, S.M.ALL_MEMBERS.index(name), tag % (2**31 - 1), rep, D]).integers(2**31))
p1, p2 = dict(tau=0.5, sep=1.0), dict(tau=2.0, sep=0.5)
assert old_seed("M3H", p1, 0, 4, 2026) == old_seed("M3H", p2, 0, 4, 2026)                     # the collision was real
assert S.dataset_seed("M3H", p1, 0, 4, 2026) != S.dataset_seed("M3H", p2, 0, 4, 2026)
for name, kw in (("M2B", {}), ("M2H", dict(tau=0.5)), ("M2S", dict(omega=2.0)), ("M2K", dict(alpha=1.0)), ("M3", dict(sep=2.0))):
    assert S.dataset_seed(name, kw, 7, 4, 2026) == old_seed(name, kw, 7, 4, 2026)
# 7. the row carries the companion cluster interval of EVERY band and the bootstrap's identity (review 4, finding 4)
assert all(np.isfinite(row2[f"selection_cluster_{b}_{k}"]) for b in ("ws", "early", "late", "ws_minus_early") for k in ("lo", "hi", "se"))
assert len(row2["interval_ident"]) == 64 and row2["interval_n_damaged"] == 0
# 8. the row is self-describing: its Config settings travel as a readable column beside the hash and the runtime
row_s = S._row("M3", {}, 0, 4, layers.tolist(), c2, 1.0, cfg=A.Config(n_starts_inner=4, interval="refit", n_boot_refit=8))
st = json.loads(row_s["settings"])
assert st["n_starts_inner"] == 4 and st["interval"] == "refit" and st["n_boot_refit"] == 8 and st["layers"] == layers.tolist()
assert row_s["runtime"].startswith("python ") and row2["settings"] == ""      # no cfg given -> empty, never a guess
print("dataset seeds: colliding recovery points separated, null-point seeds unchanged; row carries every companion interval + identity OK")
print("interval path: cluster unchanged; refit intervals from the refitting bootstrap with the point kept and the cluster CI beside; "
      "a failed resample -> assay failure under the every-replicate policy; row carries every band, H2, cluster CI, flags, seeds, folds, "
      "replicates; summarize keeps valid points in the target and drops unusable intervals from the coverage denominator OK")
