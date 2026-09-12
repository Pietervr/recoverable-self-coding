"""The §8.2 refitting bootstrap after the 12 Sept 2026 correction and the Codex re-check: copies of one original
concept share a fold at BOTH levels, the plain analysis's folds are unchanged, a failed resample is counted and never
averaged in, a partial score array is a failure too (no nanmean), every replicate must be scored by default, and the
three predictors plus ws − early come from the same refits. Pure checks on the fold maker, then refit_bootstrap with
run_dataset mocked (no fitting)."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import numpy as np
import analyze as A

# 1. no grouping / all-distinct grouping = stratified_folds exactly (same RNG draws)
fam = np.repeat(np.arange(8), 8)
plain = A.stratified_folds(fam, 4, seed=7)
assert all(np.array_equal(a, b) for a, b in zip(plain, A.grouped_stratified_folds(fam, None, 4, seed=7)))
assert all(np.array_equal(a, b) for a, b in zip(plain, A.grouped_stratified_folds(fam, np.arange(64), 4, seed=7)))

# 2. a resample with copies: every copy of a group in one fold, folds concept-disjoint and complete
rng = np.random.default_rng(3)
chosen = A.stratified_resample(fam, 1, rng)[0]            # (64,) original ids, with repeats, family-stratified
fam_b = fam[chosen]
folds = A.grouped_stratified_folds(fam_b, chosen, 4, seed=11)
assert sorted(np.concatenate(folds).tolist()) == list(range(64))
fold_of = np.empty(64, dtype=int)
for r, f in enumerate(folds):
    fold_of[f] = r
for g in np.unique(chosen):
    assert len(set(fold_of[chosen == g])) == 1, f"group {g} split across inner folds"
assert len(np.unique(chosen)) < 64 and max(np.bincount(chosen)) > 1        # the resample really has copies
try:
    A.grouped_stratified_folds(fam_b, chosen[:10], 4, seed=1); raise SystemExit("length mismatch accepted")
except ValueError:
    pass
print(f"fold maker: copies together in {len(np.unique(chosen))} groups over 64 concepts OK")

# 3. refit_bootstrap with run_dataset mocked: the sub-dataset carries group=chosen, every copy of a concept sits in
#    that concept's OUTER fold, failed and partially scored resamples are excluded, every replicate is required by
#    default, the three predictors and ws - early come from the same refits
C, L = 64, 3
layers = np.array([10, 41, 60])            # early, ws, late -> ws_minus_early exists
per = 6 * 7 * 4
ds = A.Dataset(y=rng.normal(size=(C * per, L)), k=np.tile(np.repeat(np.arange(7.0), 4 * 6), C),
               concept=np.repeat(np.arange(C), per), family=fam, layers=layers)
cfg = A.Config()
seen = []
FAILED, PARTIAL = (0, 3), (5,)
def fake_run_dataset(sub, cfg_, seed, outer_folds=None, n_jobs=1):
    assert sub.group is not None and sub.group.size == sub.n_concepts
    fold_of_sub = np.empty(sub.n_concepts, dtype=int)
    for r, f in enumerate(outer_folds):
        fold_of_sub[f] = r
    for g in np.unique(sub.group):
        assert len(set(fold_of_sub[sub.group == g])) == 1, "copies split across outer folds"
    assert sorted(np.concatenate(outer_folds).tolist()) == list(range(sub.n_concepts))
    seen.append(seed)
    rep = seed - 1 - 5
    failed = rep in FAILED
    delta = {p: np.full((sub.n_layers, sub.n_concepts), 0.01 * (1 + rep) * (1 if p == "selection" else 2)) for p in A.PREDICTORS}
    if failed:
        for p in delta:
            delta[p][:, :] = np.nan
            delta[p][0, 0] = -99.0
    if rep in PARTIAL:                       # NOT flagged failed, one held-out score missing: must not yield a number
        delta["selection"][1, 7] = np.nan
    return dict(delta=delta, failed=failed,
                failed_reason="fold 1: every member of a family unscorable in inner selection" if failed else "",
                fit_seconds=1.0)
A.run_dataset = fake_run_dataset
out = A.refit_bootstrap(ds, cfg, seed=5, n_rep=10, predictor="selection")
assert out["n_rep"] == 10 and out["n_failed"] == 3 and out["n_used"] == 7 and out["usable"] is False, (out["n_failed"], out["usable"])
assert np.isnan(out["ws"]["lo"]) and np.isnan(out["ws"]["hi"]) and len(out["failed_reasons"]) == 2
assert out["predictors"]["ensemble"]["n_used"] == 8          # the partial NaN was in selection only
assert out["policy"] == "every replicate scored" and len(out["replicates"]) == 10 and len(out["outer_folds"]) == cfg.n_outer
out = A.refit_bootstrap(ds, cfg, seed=5, n_rep=10, predictor="selection", min_usable=0.7)
assert out["usable"] and out["n_used"] == 7 and out["policy"].startswith("at least 70%")
used = sorted(0.01 * (1 + r) for r in range(10) if r not in FAILED + PARTIAL)
assert abs(out["ws"]["lo"] - np.percentile(used, 2.5)) < 1e-12 and abs(out["ws"]["hi"] - np.percentile(used, 97.5)) < 1e-12
assert -99.0 not in (out["ws"]["lo"], out["ws"]["hi"]) and out["fit_seconds"] == 10.0
assert abs(out["ws_minus_early"]["lo"]) < 1e-12 and "ws_minus_early" in out["predictors"]["historical"]["bands"]
ens = out["predictors"]["ensemble"]["bands"]["ws"]
assert abs(ens["lo"] - 2 * np.percentile(sorted(0.01 * (1 + r) for r in range(10) if r not in FAILED), 2.5)) < 1e-12
assert A.decide(float("nan"), float("nan")) == "unavailable"
print(f"refit_bootstrap: group carried, outer copies together, {out['n_failed']} failed/partial resamples excluded, "
      f"every-replicate policy by default, three predictors + ws-early from the same refits OK")

# 4. checkpointing (review 3, finding 5): every completed resample is appended as it finishes; a restart skips the
#    ones on file for this seed and n_rep and gives the same result; a foreign seed's lines are ignored
import json, os, tempfile
with tempfile.TemporaryDirectory() as d:
    ck = os.path.join(d, "refit.jsonl")
    seen.clear()
    a = A.refit_bootstrap(ds, cfg, seed=5, n_rep=10, predictor="selection", min_usable=0.7, checkpoint_path=ck)
    assert a["n_resumed"] == 0 and len(seen) == 10 and sum(1 for _ in open(ck)) == 10
    seen.clear()
    b = A.refit_bootstrap(ds, cfg, seed=5, n_rep=10, predictor="selection", min_usable=0.7, checkpoint_path=ck)
    assert b["n_resumed"] == 10 and len(seen) == 0 and b["ws"] == a["ws"] and b["n_failed"] == a["n_failed"]
    lines = open(ck).read().splitlines()
    with open(ck, "w") as fh:
        fh.write("\n".join(lines[:6] + [json.dumps(dict(json.loads(lines[7]), seed=99))]) + "\n")   # 6 kept, one foreign
    seen.clear()
    c = A.refit_bootstrap(ds, cfg, seed=5, n_rep=10, predictor="selection", min_usable=0.7, checkpoint_path=ck)
    assert c["n_resumed"] == 6 and len(seen) == 4 and c["ws"] == a["ws"] and sum(1 for _ in open(ck)) == 11
print("refit_bootstrap checkpointing: appended per resample, resumed by seed and n_rep, same interval OK")

# 5. checkpoint IDENTITY (review 4, finding 1): a checkpoint is reused only by the same data-and-procedure identity
with tempfile.TemporaryDirectory() as d:
    a = A.refit_bootstrap(ds, cfg, seed=5, n_rep=6, min_usable=0.5, checkpoint_dir=d)
    assert a["n_resumed"] == 0 and len(a["ident"]) == 64 and os.path.exists(a["checkpoint"]) and a["n_damaged"] == 0
    # (i) the five-layer stage: same seed, another response array -> another identity, nothing reused
    ds5 = A.Dataset(y=rng.normal(size=(C * per, 5)), k=ds.k, concept=ds.concept, family=fam, layers=np.array([25, 33, 41, 49, 57]))
    b = A.refit_bootstrap(ds5, cfg, seed=5, n_rep=6, min_usable=0.5, checkpoint_dir=d)
    assert b["ident"] != a["ident"] and b["n_resumed"] == 0 and b["checkpoint"] != a["checkpoint"]
    # (ii) two recovery points that share a seed: the data differ -> another identity
    ds_b = A.Dataset(y=ds.y + 1e-9, k=ds.k, concept=ds.concept, family=fam, layers=layers)
    c2 = A.refit_bootstrap(ds_b, cfg, seed=5, n_rep=6, min_usable=0.5, checkpoint_dir=d)
    assert c2["ident"] != a["ident"] and c2["n_resumed"] == 0
    # (iii) another Config or other folds -> another identity
    assert A.dataset_identity(ds, A.Config(n_boot_refit=7), 5, 6, a["outer_folds"]) != a["ident"]
    assert A.dataset_identity(ds, cfg, 5, 6, list(reversed(a["outer_folds"]))) != a["ident"]
    assert A.dataset_identity(ds, cfg, 5, 6, a["outer_folds"]) == a["ident"]
    # (iv) the same everything -> every resample reused, the same interval
    seen.clear()
    a2 = A.refit_bootstrap(ds, cfg, seed=5, n_rep=6, min_usable=0.5, checkpoint_dir=d)
    assert a2["n_resumed"] == 6 and len(seen) == 0 and a2["ws"] == a["ws"]
    # (v) a tampered resample and a truncated last line are damaged: counted, recomputed, never accepted
    with open(a["checkpoint"]) as fh:
        lines = fh.read().splitlines()
    bad = json.loads(lines[1]); bad["chosen"][0] = (bad["chosen"][0] + 1) % 64
    with open(a["checkpoint"], "w") as fh:
        fh.write("\n".join(lines[:1] + [json.dumps(bad)] + lines[2:5] + [lines[5][:40]]) + "\n")
    seen.clear()
    a3 = A.refit_bootstrap(ds, cfg, seed=5, n_rep=6, min_usable=0.5, checkpoint_dir=d)
    assert a3["n_damaged"] == 2 and a3["n_resumed"] == 4 and len(seen) == 2 and a3["ws"] == a["ws"]
print("checkpoint identity: five-layer stage, colliding-seed data, other config/folds never reuse; damaged records recomputed OK")
