"""devcheck_v7.py on synthetic blocks only (no EEG, no generated recording): the replay contract on logged folds (round
trip, tampering of starts, bounds, fit records and fold outputs), an unavailable fold, a non-finite held-out density that
is still rescored under C2, the first-in-order selection with ties and the retry path, the clamp, the unit categories and
every development gate, including the zero-count conventions and an incomplete set.

Run: ../../.venv/bin/python test_devcheck_v7.py
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import devcheck_v7 as DC
import likelihood as LK
from test_likelihood import synth_block

TAGS = (1, 0, 0, 0, 20)


def logged_fold(train, test, tags=TAGS):
    DC.install()
    DC._reset()
    LK.fold_scores(train, test, tags=tags, models=LK.PRIMARY)
    fr, fits = DC._STATE["folds"][tags], dict(DC._STATE["fits"])
    DC._reset()
    return fr, fits


def shifted_test(rng, n=110, law="graded", offset=0.35):
    """A test block whose doses reach above the training range (extrapolation) and below it."""
    b = synth_block(rng, n, law)
    logc = np.where(b.catch, np.nan, b.logc + np.where(np.arange(n) % 2 == 0, offset, -offset))
    return LK.Block(b.y, logc, b.catch, b.right)


def raises(fn):
    try:
        fn()
    except DC.ReplayMismatch:
        return True
    return False


def check_roundtrip_and_tamper():
    rng = np.random.default_rng(11)
    fr, fits = logged_fold(synth_block(rng, 110, "graded"), shifted_test(rng))
    rec = DC.replay_fold(TAGS, fr, fits, "roundtrip")
    assert all(rec["models"][m]["category"] == "fit" for m in LK.PRIMARY)
    assert (rec["label"] == "above").any() and (rec["label"] == "below").any()
    assert np.array_equal(rec["models"]["null"]["ll_c2"], rec["models"]["null"]["ll_baseline"])
    ext = (rec["label"] == "above") | (rec["label"] == "below")
    changed = not np.array_equal(rec["models"]["graded"]["ll_c2"][ext], rec["models"]["graded"]["ll_baseline"][ext])

    def tamper(edit):
        fr2, fits2 = copy.deepcopy(fr), copy.deepcopy(fits)
        edit(fr2, fits2)
        return raises(lambda: DC.replay_fold(TAGS, fr2, fits2, "tamper"))
    key = (TAGS, "graded")
    best, _ = DC.select_start(fits[key]["starts"])
    cases = dict(
        start_loglik=lambda f, s: s[key]["starts"]["loglik"].__setitem__(best, s[key]["starts"]["loglik"][best] + 1e-9),
        start_x0=lambda f, s: s[key]["starts"]["x0"].__setitem__((0, 0), s[key]["starts"]["x0"][0, 0] + 1e-12),
        bounds=lambda f, s: s[key]["bounds"].__setitem__((0, 0), s[key]["bounds"][0, 0] - 1.0),
        kept_theta=lambda f, s: s[key]["theta"].__setitem__(0, s[key]["theta"][0] + 1e-12),
        heldout=lambda f, s: f["output"]["graded"].__setitem__("heldout", f["output"]["graded"]["heldout"] + 1e-9),
        missing_fit=lambda f, s: s.pop((TAGS, "twostate")),
        n_at_best=lambda f, s: s[key].__setitem__("n_at_best", s[key]["n_at_best"] + 1),
        test_y=lambda f, s: f["test"]["y"].__setitem__(0, f["test"]["y"][0] + 1e-9))
    failed = [name for name, edit in cases.items() if not tamper(edit)]
    assert not failed, failed
    return changed


def check_unavailable_fold():
    rng = np.random.default_rng(12)
    train = synth_block(rng, 110, "graded", n_catch=1)                     # below MIN_CATCH: the fold is unavailable
    fr, fits = logged_fold(train, synth_block(rng, 110, "graded"))
    assert not fits
    rec = DC.replay_fold(TAGS, fr, fits, "unavailable")
    assert rec["fold_reason"].startswith("fewer than") and all(rec["models"][m]["category"] == "no fit" for m in LK.PRIMARY)
    fake = {(TAGS, "graded"): dict()}
    assert raises(lambda: DC.replay_fold(TAGS, fr, fake, "unavailable+fit"))
    units = DC.fold_units("k", DC.GROUPS[2], 1, 0, 0, 20, rec)
    assert [u["category"] for u in units] == ["no fit", "no fit"]


def check_nonfinite_heldout_rescored():
    rng = np.random.default_rng(13)
    test = synth_block(rng, 110, "graded")
    y = test.y.copy()
    y[5] = 1e200                                                           # finite input, non-finite density for every model
    fr, fits = logged_fold(synth_block(rng, 110, "graded"), LK.Block(y, test.logc, test.catch, test.right))
    rec = DC.replay_fold(TAGS, fr, fits, "nonfinite")
    for m in LK.PRIMARY:
        r = rec["models"][m]
        assert r["category"] == "fit" and not r["finite_baseline"] and "ll_c2" in r and not r["finite_c2"]
        assert fr["output"][m]["reason"] == "non-finite held-out density"
    assert [u["category"] for u in DC.fold_units("k", DC.GROUPS[2], 1, 0, 0, 20, rec)] == ["reference failure"] * 2

    # constructed: null finite, graded non-finite at baseline but finite under C2 (repaired), two-state newly non-finite
    n = 4
    label = np.array(["within", "above", "catch", "within"], dtype=object)
    fin = np.zeros(n)
    bad = np.array([0.0, -np.inf, 0.0, 0.0])
    rec2 = dict(n_test=n, fold_reason=None, label=label, models=dict(
        null=dict(category="fit", ll_baseline=fin, ll_c2=fin, finite_baseline=True, finite_c2=True),
        graded=dict(category="fit", ll_baseline=bad, ll_c2=fin - 0.5, finite_baseline=False, finite_c2=True),
        twostate=dict(category="fit", ll_baseline=fin, ll_c2=bad, finite_baseline=True, finite_c2=False)))
    ug, ut = DC.fold_units("k", DC.GROUPS[2], 1, 0, 0, 20, rec2)
    assert ug["baseline_severe"] and ug["baseline_unavailable"] and not ug["c2_severe"] and not ug["c2_unavailable"]
    assert ut["c2_severe"] and ut["c2_unavailable"] and not ut["baseline_unavailable"]
    t = DC.tallies([ug, ut])
    gid = DC.group_id(DC.GROUPS[2])
    assert t[(gid, "graded", "newly_unavailable")] == 0 and t[(gid, "twostate", "newly_unavailable")] == 1
    assert t[(gid, "graded", "transition_SN")] == 1 and t[(gid, "twostate", "transition_NS")] == 1


def check_selection_and_retry():
    st = dict(loglik=np.array([-5.0, -3.0, -3.0, -2.0, -2.0]), converged=np.array([True, True, True, False, True]))
    best, n_at = DC.select_start(st)
    assert best == 4 and n_at == 1                                          # -2.0 converged only at index 4
    st["converged"][4] = False
    assert DC.select_start(st) == (1, 2)                                   # first in order among the exact tie at -3.0
    st["converged"][:] = False
    assert DC.select_start(st) == (None, 0)

    rng = np.random.default_rng(14)
    fr, fits = logged_fold(synth_block(rng, 110, "graded"), synth_block(rng, 110, "graded"))
    train = LK.Block(**fr["train"])
    sc = LK.scaling(train)
    dtr = LK.design(train, sc)
    b = LK.bounds("graded", sc)
    p0 = LK.interior(LK.moment_start("graded", dtr, sc), b)
    rng1 = np.random.default_rng(np.random.SeedSequence([LK.SEED, *TAGS, LK.MODEL_INDEX["graded"]]))
    rng2 = np.random.default_rng(np.random.SeedSequence([LK.SEED, *TAGS, LK.MODEL_INDEX["graded"], 1]))
    x0 = np.stack([p0] + [LK.jitter(p0, b, rng1, LK.JITTER_SD) for _ in range(LK.N_JITTER)]
                  + [LK.jitter(p0, b, rng2, LK.RETRY_JITTER_SD) for _ in range(LK.RETRY_STARTS)])
    n = x0.shape[0]
    no_conv = dict(available=False, reason="no converged start", n_starts=n, n_converged=0, retry=True, n_at_best=None, theta=None,
                   loglik=None, bounds=b, starts=dict(x0=x0, theta=x0.copy(), loglik=np.full(n, -np.inf),
                                                      converged=np.zeros(n, dtype=bool)))
    xp = dtr["x"][~dtr["c"]]
    assert DC.replay_fit("graded", no_conv, sc, dtr, TAGS, float(xp.min()), float(xp.max()), "retry") is None
    wrong = copy.deepcopy(no_conv)
    wrong["retry"] = False
    assert raises(lambda: DC.replay_fit("graded", wrong, sc, dtr, TAGS, float(xp.min()), float(xp.max()), "retry flag"))
    short = copy.deepcopy(no_conv)
    short["starts"] = {k: v[:8] for k, v in short["starts"].items()}
    short["n_starts"] = 8
    assert raises(lambda: DC.replay_fit("graded", short, sc, dtr, TAGS, float(xp.min()), float(xp.max()), "no retries"))


def check_clamp():
    d = dict(x=np.array([-3.0, 0.0, 0.5, 4.0]), c=np.array([False, True, False, False]), y=np.zeros(4), h=np.zeros(4))
    c = DC.clamp(d, -1.0, 1.0)
    assert np.array_equal(c["x"], [-1.0, 0.0, 0.5, 1.0]) and c["y"] is d["y"]
    assert np.array_equal(DC.clamp(dict(d, x=np.array([-1.0, 0.0, 0.5, 1.0])), -1.0, 1.0)["x"], [-1.0, 0.0, 0.5, 1.0])


def scored(g, fam, bsev=False, csev=False, bun=False, cun=False):
    return dict(group=DC.group_id(g), family=fam, category="scored", baseline_severe=bsev, c2_severe=csev,
                baseline_unavailable=bun, c2_unavailable=cun)


def check_gates():
    def world(x1=("two-state", "two-state"), graded="inconclusive/mixed", B=4, C=2, ts_increase=False, newly=False, empty=False):
        dec = {(DC.group_id(g), c): dict(outcome="inconclusive/mixed") for g in DC.GROUPS for c in DC.CONFIGS}
        for g, o in zip(DC.X1_GROUPS, x1):
            dec[(DC.group_id(g), "c2")] = dict(outcome=o)
        for g in DC.GRADED_GROUPS:
            dec[(DC.group_id(g), "c2")] = dict(outcome=graded)
        units = []
        for g in DC.GROUPS:
            units.append(scored(g, "twostate", bsev=False, csev=ts_increase and g == DC.GROUPS[0]))
        for i, g in enumerate(DC.GRADED_GROUPS):
            if empty:
                units.append(dict(group=DC.group_id(g), family="graded", category="no fit"))
                continue
            units.append(scored(g, "graded"))
        g0 = DC.GRADED_GROUPS[0]
        if not empty:
            units += [scored(g0, "graded", bsev=True, csev=False) for _ in range(B)]
            for u in units[-C:] if C else []:
                u["c2_severe"] = True
        if newly:
            units.append(scored(DC.GROUPS[1], "twostate", cun=True))
        return dec, units
    ok = DC.gates(*world(), n_present=204, n_expected=204)
    assert ok["decided"] and ok["lock_c2"] and ok["graded_severe_B"] == 4 and ok["graded_severe_C"] == 2, ok
    assert not DC.gates(*world(B=4, C=3), n_present=204, n_expected=204)["gates"]["graded_severe_halved"]
    assert not DC.gates(*world(B=1, C=1), n_present=204, n_expected=204)["gates"]["graded_severe_halved"]
    zero = DC.gates(*world(B=0, C=0), n_present=204, n_expected=204)
    assert zero["gates"]["graded_severe_halved"] and zero["lock_c2"]
    assert not DC.gates(*world(empty=True, B=0, C=0), n_present=204, n_expected=204)["gates"]["graded_severe_halved"]
    assert not DC.gates(*world(ts_increase=True), n_present=204, n_expected=204)["gates"]["no_twostate_severe_increase"]
    nu = DC.gates(*world(newly=True), n_present=204, n_expected=204)
    assert not nu["gates"]["no_newly_unavailable"] and not nu["lock_c2"]
    assert not DC.gates(*world(x1=("two-state", "inconclusive/mixed")), n_present=204, n_expected=204)["lock_c2"]
    assert not DC.gates(*world(graded="two-state"), n_present=204, n_expected=204)["lock_c2"]
    inc = DC.gates(*world(), n_present=203, n_expected=204)
    assert not inc["decided"] and not inc["lock_c2"]
    graded_up = world(B=0, C=0)
    graded_up[1].append(scored(DC.GRADED_GROUPS[1], "graded", bsev=False, csev=True))
    g = DC.gates(*graded_up, n_present=204, n_expected=204)["gates"]
    assert not g["no_graded_severe_increase"] and not g["graded_severe_halved"]


def main():
    changed = check_roundtrip_and_tamper()
    print(f"replay round trip exact on a logged fold with extrapolated doses (C2 changed graded there: {changed}); 8 tamperings "
          "caught (start loglik, start x0, bounds, kept theta, held-out, missing fit, n_at_best, test y)")
    check_unavailable_fold()
    print("unavailable fold: categories 'no fit', a fit record where none may exist is refused")
    check_nonfinite_heldout_rescored()
    print("non-finite held-out density: rescored under C2, reference failure when null is non-finite; repaired and "
          "newly unavailable transitions counted")
    check_selection_and_retry()
    print("selection: first converged maximum in order with ties; retry path replayed; wrong retry flag and missing retries refused")
    check_clamp()
    print("clamp: training identity, catch rows untouched, outside doses clipped")
    check_gates()
    print("gates: halving with zero-count conventions and a non-empty set, tail guards, newly unavailable, X1 and graded "
          "outcomes, incomplete set")
    print("test_devcheck_v7: ALL OK")


if __name__ == "__main__":
    main()
