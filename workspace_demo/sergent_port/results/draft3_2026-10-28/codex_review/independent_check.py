"""Saved-table review only. All writes are confined to this script's directory.

Run from the repository root: .venv/bin/python -B <path>/independent_check.py
Does not import or execute any of the three reviewed analysis scripts.
"""
from pathlib import Path
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd
import scipy
from scipy.integrate import quad
from scipy.special import gammainc, gammaln, logsumexp, psi
from scipy.stats import t as t_dist

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RES = ROOT / "workspace_demo/sergent_port/results"
DRAFT = HERE.parent
SIM = ROOT / "workspace_demo/t1_access/sim_results"
OLD = ROOT / "workspace_demo/t1_access/reviews/t1_sampling_unit_2026-09-16"
sys.dont_write_bytecode = True
sys.path.insert(0, str(RES.parent))
from bms import spm_bms, dirichlet_exceedance

LOG = []


def say(s):
    print(s, flush=True)
    LOG.append(s)


def save(df, name):
    df.to_csv(HERE / name, index=False, float_format="%.12g")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protected = [
    SIM / "draft3_reanalyses_2026-10-28/d6_rms_claimed_se.py",
    SIM / "draft3_reanalyses_2026-10-28/d6_rms_claimed_se.txt",
    SIM / "draft3_reanalyses_2026-10-28/d6_rms_claimed_se.csv",
    DRAFT / "d12_fold_sum_bms.py", DRAFT / "d12_fold_sum_bms.txt",
    DRAFT / "d12_fold_sum_bms_active.csv", DRAFT / "d12_fold_sum_bms_passive.csv",
    DRAFT / "d1_paired_active_passive.py", DRAFT / "d1_paired_active_passive.txt",
    DRAFT / "d1_paired_active_passive.csv",
]
inputs = protected + [SIM / "d4v12b/calibration_D4.csv", OLD / "sampling_unit.csv",
                     RES.parent / "bms.py", RES.parent / "fit_models.py",
                     RES.parent / "README.md", RES.parent / "RESULTS_sergent.md",
                     RES.parent / "figures/fig_b_pxp_published_vs_port_active.csv"]
for tag in ["active", "passive", "passive_max6"]:
    inputs += [RES / f"fits_{tag}.csv", RES / f"llh_{tag}.csv"]
for tag in ["active", "passive"]:
    inputs += [RES / f"bms_{tag}.csv", RES / f"bms_two_model_{tag}.csv"]
before = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
(HERE / "input_sha256.json").write_text(json.dumps(before, indent=2) + "\n")
say(f"ENV Python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}, scipy {scipy.__version__}")

# D6: NumPy recomputation, finite/uniqueness checks, and tail influence.
say("D6 independent recomputation")
cal = pd.read_csv(SIM / "d4v12b/calibration_D4.csv")
cal["csv_line"] = np.arange(len(cal)) + 2
assert len(cal) == 12000
assert not cal.duplicated(["generator", "grid", "rep"]).any()
assert (cal.failed == 0).all()
assert np.isfinite(cal[["selection_ws_point", "selection_ws_se"]]).all().all()
assert (cal.selection_ws_se > 0).all()
assert before[str((SIM / "d4v12b/calibration_D4.csv").relative_to(ROOT))] == "7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb"
old = pd.read_csv(OLD / "sampling_unit.csv")
given = pd.read_csv(SIM / "draft3_reanalyses_2026-10-28/d6_rms_claimed_se.csv")
d6rows = []
for _, ref in given.iterrows():
    g = cal[(cal.generator == ref.generator) & (cal.grid == ref.grid)].copy()
    assert len(g) == 1000 and g.rep.nunique() == 1000
    x, se = g.selection_ws_point.to_numpy(), g.selection_ws_se.to_numpy()
    v, q = se**2, (x - x.mean())**2
    ix = np.argsort(v)[::-1]
    n = len(x)
    sd, rms = x.std(ddof=1), np.sqrt(v.mean())
    median, mean = np.median(se), se.mean()
    d = dict(setting=ref.setting, n=n, sd_rep=sd, median_se=median, mean_se=mean,
             rms_se=rms, ratio_median=sd/median, ratio_mean=sd/mean, ratio_rms=sd/rms,
             top1pct_share_of_mean_square=v[ix[:10]].sum()/v.sum(),
             largest_share_ms=v.max()/v.sum(), largest_share_centered_point_ss=q.max()/q.sum(),
             top10_se_rows_share_centered_point_ss=q[ix[:10]].sum()/q.sum(),
             effective_ms_contributors=v.sum()**2 / (v**2).sum(),
             rms_mcse_delta=np.sqrt(v.var(ddof=1)/n)/(2*rms),
             point_min=x.min(), point_max=x.max(),
             sd_without_top10_se=x[np.argsort(v)[:-10]].std(ddof=1),
             rms_without_top10_se=np.sqrt(v[np.argsort(v)[:-10]].mean()))
    # Delete-one diagnostics retain the paired estimate and SE from each dataset.
    sd_delete = np.sqrt(np.maximum(0, (q.sum() - n/(n-1)*q)/(n-2)))
    rms_delete = np.sqrt((v.sum()-v)/(n-1))
    d.update(delete_one_ratio_min=(sd_delete/rms_delete).min(),
             delete_one_ratio_max=(sd_delete/rms_delete).max())
    oldr = old[(old.generator == ref.generator) & (old.grid == ref.grid)].iloc[0]
    assert abs(d["ratio_median"] - oldr.ratio_median) < 1e-10
    for col in ["sd_rep", "median_se", "mean_se", "rms_se", "ratio_median", "ratio_mean", "ratio_rms", "top1pct_share_of_mean_square"]:
        assert np.isclose(d[col], ref[col], rtol=1e-10, atol=1e-12), (ref.setting, col)
    d6rows.append(d)
    say(f"  {ref.setting}: n={n}, SD={sd:.10g}, median={median:.10g}, mean={mean:.10g}, RMS={rms:.10g}, SD/median={sd/median:.8f}, SD/RMS={sd/rms:.8f}, top10_MS={d['top1pct_share_of_mean_square']:.8f}")
    if ref.generator == "M2S" and json.loads(ref.grid)["omega"] >= 1:
        say(f"    tail: max_MS_share={d['largest_share_ms']:.8f}, max_point_SS_share={d['largest_share_centered_point_ss']:.8f}, top10_SE_rows_point_SS_share={d['top10_se_rows_share_centered_point_ss']:.8f}, effective_MS_contributors={d['effective_ms_contributors']:.5f}, RMS_MCSE_delta={d['rms_mcse_delta']:.8g}")
        say(f"    influence only (not replacement estimates): drop_top10_SE SD={d['sd_without_top10_se']:.8g}, RMS={d['rms_without_top10_se']:.8g}; delete_one_SD/RMS_range=[{d['delete_one_ratio_min']:.8g},{d['delete_one_ratio_max']:.8g}]; point_range=[{x.min():.8g},{x.max():.8g}]")
        top = g.iloc[ix[:3]]
        say("    largest SE rows: " + "; ".join(f"calibration_D4.csv:{int(r.csv_line)} rep={int(r.rep)} point={r.selection_ws_point:.10g} SE={r.selection_ws_se:.10g}" for _, r in top.iterrows()))
save(pd.DataFrame(d6rows), "d6_independent.csv")
say("D6 PASS: all 12 RMS/median tables match; 12000 finite successful unique rows, 1000/setting")


# Independent deterministic variational posterior and free energies.
def independent_vb(scores):
    L = np.asarray(scores)
    n, k = L.shape
    a = np.ones(k)
    for it in range(10000):
        logits = L + psi(a) - psi(a.sum())
        g = np.exp(logits - logsumexp(logits, axis=1, keepdims=True))
        anew = 1 + g.sum(axis=0)
        if np.linalg.norm(anew - a) <= 1e-3:
            a = anew
            break
        a = anew
    else:
        raise AssertionError("VB not converged")
    e = psi(a) - psi(a.sum())
    f1 = gammaln(k) + (g * (L + e)).sum()
    f1 += np.sum(gammaln(a)) - gammaln(a.sum()) - np.dot(a-1, e)
    f1 -= np.sum(g * np.log(g + np.finfo(float).eps))
    f0 = (logsumexp(L, axis=1) - np.log(k)).sum()
    bor = 1/(1+np.exp(f1-f0))
    return a, bor


def xp_quad(a, target=2):
    # Independent gamma representation of a Dirichlet; normalisation preserves winner.
    def integrand(x):
        if x <= 0:
            return 0.0
        return np.exp((a[target]-1)*np.log(x)-x-gammaln(a[target])) * np.prod([gammainc(a[j], x) for j in range(len(a)) if j != target])
    return quad(integrand, 0, np.inf, epsabs=1e-11, epsrel=1e-11)


say("D12 construction, same-seed ties, independent VB, exact gamma-integral xp")
M = ["model0", "model2B", "model3"]
tables, fit_tables, exactrows, mctargets, fullrows = {}, {}, [], [], []
for tag in ["active", "passive", "passive_max6"]:
    fits = pd.read_csv(RES / f"fits_{tag}.csv")
    llh = pd.read_csv(RES / f"llh_{tag}.csv")
    fit_tables[tag], tables[tag] = fits, llh
    assert len(fits) == 15900 and len(llh) == 1060
    assert not fits.duplicated(["subject", "window", "model", "fold"]).any()
    assert not llh.duplicated(["subject", "window"]).any()
    assert np.isfinite(fits.test_llh).all()
    assert fits.groupby(["subject", "window", "model"]).fold.apply(lambda x: set(x) == set(range(5))).all()
    assert fits.groupby(["subject", "window", "fold"]).n_test.nunique().eq(1).all()
    assert fits.n_test.gt(0).all()
    assert fits.groupby(["subject", "model", "fold"]).n_test.nunique().eq(1).all()
    assert llh.groupby("subject").size().eq(53).all()
    assert llh.subject.nunique() == 20
    fmean = fits.pivot(index=["subject", "window", "fold"], columns="model", values="test_llh").groupby(["subject", "window"]).mean()
    fsum = fits.pivot(index=["subject", "window", "fold"], columns="model", values="test_llh").groupby(["subject", "window"]).sum()
    li = llh.set_index(["subject", "window"]).sort_index()[M]
    tie = np.abs(fmean[M]-li).max().max()
    say(f"  {tag}: fits={len(fits)}, score_rows={len(llh)}, complete_unique_5_folds=True, finite=True, n_test_equal_across_models=True; mean_vs_llh_max={tie:.9g}, sum_vs_5_saved_mean_max={np.abs(fsum[M]-5*li).max().max():.9g}")
    if tag == "passive_max6":
        continue
    given12 = pd.read_csv(DRAFT / f"d12_fold_sum_bms_{tag}.csv").set_index("window")
    given3 = pd.read_csv(RES / f"bms_{tag}.csv").set_index("window")
    given2 = pd.read_csv(RES / f"bms_two_model_{tag}.csv").set_index("window")
    rngs = {scale: np.random.default_rng(0) for scale in ["mean", "sum"]}
    errs = dict(draft_pxp=0., draft_bor=0., bms3_pxp=0., bms3_bor=0., bms2_pxp=0., bms2_bor=0., independent_alpha=0., independent_bor=0.)
    for w in sorted(llh.window.unique()):
        tm = int(llh.loc[llh.window == w, "t_ms"].iloc[0])
        dm, ds = li.xs(w, level="window").to_numpy(), fsum[M].xs(w, level="window").to_numpy()
        for scale, scores in [("mean", dm), ("sum", ds)]:
            port = spm_bms(scores, rng=rngs[scale])
            a, bor = independent_vb(scores)
            errs["independent_alpha"] = max(errs["independent_alpha"], np.max(np.abs(a-port["alpha"])))
            errs["independent_bor"] = max(errs["independent_bor"], abs(bor-port["bor"]))
            ex, error = xp_quad(a)
            px = (1-bor)*ex + bor/3
            exactrows.append(dict(session=tag, t_ms=tm, scale=scale, xp=ex, pxp=px, bor=bor, quad_error=error, **{f"alpha{i}":v for i,v in enumerate(a)}))
            two = spm_bms(scores[:, 1:])
            errs["draft_pxp"] = max(errs["draft_pxp"], abs(port["pxp"][2]-given12.loc[w, f"pxp3_{scale}"]), abs(two["pxp"][1]-given12.loc[w, f"two_pxp3_{scale}"]))
            errs["draft_bor"] = max(errs["draft_bor"], abs(port["bor"]-given12.loc[w, f"bor3_{scale}"]), abs(two["bor"]-given12.loc[w, f"two_bor_{scale}"]))
            if scale == "mean":
                errs["bms3_pxp"] = max(errs["bms3_pxp"], abs(port["pxp"][2]-given3.loc[w,"pxp_model3"]))
                errs["bms3_bor"] = max(errs["bms3_bor"], abs(port["bor"]-given3.loc[w,"bor"]))
                errs["bms2_pxp"] = max(errs["bms2_pxp"], abs(two["pxp"][1]-given2.loc[w,"pxp_model3"]))
                errs["bms2_bor"] = max(errs["bms2_bor"], abs(two["bor"]-given2.loc[w,"bor"]))
            fullrows.append(dict(session=tag, window=w, t_ms=tm, scale=scale, pxp=port["pxp"][2], xp=port["xp"][2], bor=port["bor"], two_pxp=two["pxp"][1], two_bor=two["bor"]))
            if tag == "active" and tm in [315,345,375,405]:
                mctargets.append((tm, scale, a, bor, ex, px))
            if tag == "active" and tm in [315,345,375,405,435,465,495]:
                # Isolate score rounding from the factor-five sensitivity.
                alt_scores = fmean[M].xs(w, level="window").to_numpy() if scale == "mean" else 5*dm
                aa, bb = independent_vb(alt_scores)
                xx, _ = xp_quad(aa)
                pp = (1-bb)*xx+bb/3
                say(f"  active {tm} {scale}: exact_xp={ex:.9f}, exact_pxp={px:.9f}, BOR={bor:.9g}, rounding_variant_pxp={pp:.9f}, delta={pp-px:+.9g}")
    assert max(errs[k] for k in ["draft_pxp", "draft_bor", "bms3_pxp", "bms3_bor", "bms2_pxp", "bms2_bor"]) < 5.1e-7, errs
    assert errs["independent_alpha"] < 1e-8 and errs["independent_bor"] < 1e-8
    say(f"  {tag} max absolute ties: " + ", ".join(f"{k}={v:.9g}" for k,v in errs.items()))

exactdf = pd.DataFrame(exactrows)
save(exactdf, "d12_exact.csv")
save(pd.DataFrame(fullrows), "d12_same_seed.csv")
for tag in ["active", "passive"]:
    for scale in ["mean", "sum"]:
        e = exactdf[(exactdf.session == tag) & (exactdf.scale == scale)].sort_values("t_ms")
        ts, mask = e.t_ms.to_numpy(), e.pxp.to_numpy() > .95
        hits = ts[mask].tolist()
        runs = [int(ts[i]) for i in range(len(ts)-2) if mask[i:i+3].all()]
        say(f"  exact {tag} {scale}: >.95={hits}, first={hits[0] if hits else None}, first_run3={runs[0] if runs else None}")
overlay = pd.read_csv(RES.parent / "figures/fig_b_pxp_published_vs_port_active.csv")
for col in ["published_pxp_model3", "port_pxp_model3"]:
    say(f"  saved_overlay {col} first>.95={int(overlay.loc[overlay[col]>.95, 't_ms'].iloc[0])}")

say("D12 Monte Carlo check: seeds 0..9, 1000000 independent gamma draws per seed/cell")
mcrows = []
for tm, scale, a, bor, ex, px in mctargets:
    xpse = np.sqrt(ex*(1-ex)/1_000_000)
    pxse = (1-bor)*xpse
    draws = []
    for seed in range(10):
        xx = dirichlet_exceedance(a, nsamp=1_000_000, rng=np.random.default_rng(seed))[2]
        pp = (1-bor)*xx+bor/3
        draws.append(pp)
        mcrows.append(dict(t_ms=tm, scale=scale, seed=seed, xp=xx, pxp=pp, exact_xp=ex, exact_pxp=px, bor=bor, xp_mcse=xpse, pxp_mcse=pxse))
    say(f"  {tm} {scale}: exact_pxp={px:.9f}, xp_MCSE={xpse:.9g}, pxp_MCSE={pxse:.9g}, seed_mean={np.mean(draws):.9f}, seed_SD={np.std(draws,ddof=1):.9g}, seed_min={min(draws):.9f}, seed_max={max(draws):.9f}, threshold_distance_MCSE={abs(px-.95)/pxse:.2f}")
save(pd.DataFrame(mcrows), "d12_mc_seeds.csv")

# D1: aggregate trial-weighted fold differences directly, and compare to saved llh.
say("D1 independent participant pairing and normalization")
advantages = {}
for tag in ["active", "passive", "passive_max6"]:
    f, l = fit_tables[tag], tables[tag]
    idx = ["subject", "window", "fold"]
    p = f.pivot(index=idx, columns="model", values="test_llh")
    n = f[f.model == "model3"].set_index(idx).n_test
    numer = (p.model3 - p.model2B).groupby(["subject", "window"]).sum()
    denom = n.groupby(["subject", "window"]).sum()
    direct = numer / denom
    li = l.set_index(["subject", "window"]).sort_index()
    adv_fold = li.model3 - li.model2B
    pertrial = adv_fold / (denom/5)
    # The numerator uses separately rounded saved llh, hence a small precision difference.
    advantages[tag] = pd.DataFrame(dict(adv_trial=pertrial, direct_trial=direct, adv_fold=adv_fold, n_mean=denom/5, n_total=denom, t_ms=li.t_ms))
    assert direct.index.equals(pertrial.index)
    ns = denom.groupby("subject").first()
    say(f"  {tag}: total_scored_trials_per_subject_min={ns.min()}, max={ns.max()}, mean_per_fold={ns.mean()/5:.8g}, max_pertrial_saved_llh_minus_direct={abs(pertrial-direct).max():.9g}; all 20x53 participant windows and matching model denominators verified")
given1 = pd.read_csv(DRAFT / "d1_paired_active_passive.csv").set_index(["passive", "window", "unit"])
d1rows, participantrows = [], []
for tag in ["passive", "passive_max6"]:
    aa = advantages["active"].reset_index().set_index(["subject", "t_ms"])
    pp = advantages[tag].reset_index().set_index(["subject", "t_ms"])
    assert aa.index.equals(pp.index)
    for lab, windows in [("315", [315]), ("435", [435]), ("465", [465]), ("495", [495]), ("435-495 mean", [435,465,495])]:
        a = aa.loc[aa.index.get_level_values("t_ms").isin(windows)].groupby("subject").mean()
        p = pp.loc[pp.index.get_level_values("t_ms").isin(windows)].groupby("subject").mean()
        assert len(a) == len(p) == 20
        for unit in ["fold", "trial"]:
            d = a[f"adv_{unit}"]-p[f"adv_{unit}"]
            sd, mn = d.std(ddof=1), d.mean()
            tt = mn/(sd/np.sqrt(20))
            pv = 2*t_dist.sf(abs(tt), df=19)
            row = dict(passive=tag, window=lab, unit=unit, n=20, mean_active=a[f"adv_{unit}"].mean(), mean_passive=p[f"adv_{unit}"].mean(), mean_diff=mn, sd_diff=sd, t=tt, p=pv, n_active_gt_passive=int((d>0).sum()), n_active_pos=int((a[f"adv_{unit}"]>0).sum()), n_passive_pos=int((p[f"adv_{unit}"]>0).sum()))
            ref = given1.loc[(tag, lab, unit)]
            for k,v in row.items():
                if k not in ["passive", "window", "unit"]:
                    assert np.isclose(v, ref[k], rtol=6e-6, atol=5e-9), (row,k,ref[k])
            d1rows.append(row)
        if lab in ["315", "435-495 mean"]:
            d = a.adv_trial - p.adv_trial
            dd = a.direct_trial - p.direct_trial
            direct_t = dd.mean()/(dd.std(ddof=1)/np.sqrt(20))
            say(f"  active-minus-{tag} {lab}: per_trial_mean={d.mean():.10g}, SD={d.std(ddof=1):.10g}, t19={d.mean()/(d.std(ddof=1)/np.sqrt(20)):.9g}, count_positive={int((d>0).sum())}; direct_from_fits_mean={dd.mean():.10g}, t19={direct_t:.9g}, count_positive={int((dd>0).sum())}")
            for subject in a.index:
                participantrows.append(dict(passive=tag, window=lab, subject=subject, active=a.loc[subject,"adv_trial"], passive_adv=p.loc[subject,"adv_trial"], difference=d.loc[subject], direct_difference=dd.loc[subject]))
save(pd.DataFrame(d1rows), "d1_independent.csv")
save(pd.DataFrame(participantrows), "d1_participants.csv")
say("D1 PASS: all 20 saved summary rows reproduced; no missing subject/window, pseudoreplication, or model-dependent n_test")

after = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
assert after == before, "An input changed during review"
say(f"READ_ONLY_PASS: all {len(inputs)} explicit inputs unchanged by SHA256, including all 3 reviewed scripts and 7 outputs")
(HERE / "independent_check.txt").write_text("\n".join(LOG) + "\n")
