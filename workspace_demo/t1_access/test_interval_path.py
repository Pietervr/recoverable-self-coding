"""The §8.2 interval method is a declared Config choice carried through the runner (Codex, 12 Sept 2026, finding 3):
with interval="refit" analyze_dataset's intervals come from the refitting bootstrap (the point estimates unchanged,
the cluster interval kept beside), an unusable refit interval is an assay failure, the row carries the method and its
counts, and the code/config hash separates the two methods. run_dataset is mocked; nothing is fitted."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
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
FAIL_REPS = set()

def fake_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    folds = A.stratified_folds(sub.family, cfg.n_outer, seed) if outer_folds is None else outer_folds
    r = np.random.default_rng(seed)
    Cs, L = sub.n_concepts, sub.n_layers
    base = 0.02 + 0.005 * r.normal()                       # per-replicate shift: the refit interval is not degenerate
    delta = {p: base * (1 if p == "selection" else 2) + 0.001 * r.normal(size=(L, Cs)) for p in A.PREDICTORS}
    failed = (seed - 1 - 5) in FAIL_REPS and sub.group is not None
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
FAIL_REPS.add(2)
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
print("interval path: cluster unchanged; refit intervals from the refitting bootstrap with the point kept and the cluster CI beside; "
      "a failed resample -> assay failure under the every-replicate policy; row + hash carry the method OK")
