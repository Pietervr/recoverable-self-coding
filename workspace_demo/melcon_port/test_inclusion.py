"""inclusion.py and its place in recording.py (PREREG §2, DRAFT v5; Codex continuation review 4, §6), synthetic inputs only.

Codex's deterministic counterexamples reached the decoder with 240 present, 24 catch, two catch in block 1, a negative
present contrast and a preprocessor exclusion. Here, with the decoder and the fitter replaced by stubs that record what
they receive: the four failing recordings are 'excluded' before the decoder is called, with every failing rule named;
the negative-contrast present trial is excluded as a trial and never reaches the decoder; sensitivity-induced losses (edge
trials, no response) are applied before the floors; excluded recordings do not count toward §8's n_pass_section2.

Run: ../../.venv/bin/python test_inclusion.py   (seconds; no epochs are decoded)
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import decoder as DEC
import inclusion as INC
import likelihood as LK
import recording as RC
import synthetic as SY


def base_template():
    t = SY.template(1, "nocue")
    t["retained"] = True
    t["has_epoch"] = True
    t["edge_trial"] = False
    t["epoch_index"] = np.arange(len(t))
    return t


def cases():
    t = base_template()
    out = {}
    t240 = t.copy()
    for _, rows in t240[t240.present].groupby("block"):
        t240.loc[rows.index[60:], "retained"] = False
    out["240_present"] = dict(trials=t240)
    t24 = t.copy()
    for _, rows in t24[t24["catch"]].groupby("block"):
        t24.loc[rows.index[6:], "retained"] = False
    out["24_catch"] = dict(trials=t24)
    tb = t.copy()
    tb.loc[tb.index[(tb.block == 1) & tb["catch"]][2:], "retained"] = False
    out["2_catch_block1"] = dict(trials=tb)
    tn = t.copy()
    tn.loc[tn.index[tn.present][0], "contrast"] = -1.0
    out["negative_contrast_present"] = dict(trials=tn)
    out["preprocessor_excluded"] = dict(trials=t.copy(), excluded=True, exclude_reason="13 bad channels in block(s) [2]")
    return out


def run_with_stubs(rec, **kw):
    calls = []

    def decoder(r, **kwargs):
        rows = r["trials"][r["trials"].retained & r["trials"].has_epoch]
        calls.append(dict(n_present=int(rows.present.sum()), n_catch=int(rows["catch"].sum()),
                          n_nonpositive_present=int((rows.present & ~(rows.contrast > 0)).sum())))
        return dict(status="ok", halves={B: dict(trials=rows[rows.block.isin(B)].reset_index(drop=True),
                                                 W=np.zeros((int(rows.block.isin(B).sum()), 40)), auc=np.full(40, 0.7))
                                         for B in DEC.HALVES})

    def fits(train, test, tags=(), models=LK.PRIMARY):
        return {m: dict(available=True, heldout=-float(len(test)), reason="") for m in models}
    with patch.object(DEC, "split_half", side_effect=decoder), patch.object(LK, "fold_scores", side_effect=fits):
        res = RC.recording_scores(rec, 1, "nocue", windows=(25,), **kw)
    return res, calls


def main():
    results = {}
    for name, rec in cases().items():
        res, calls = run_with_stubs(rec)
        results[name] = res
        if name == "negative_contrast_present":
            assert res["status"] == "ok", res["status"]
            assert len(calls) == 1 and calls[0]["n_nonpositive_present"] == 0, calls
            assert res["section2"]["counts"]["excluded_trials"] == {"non-positive contrast": 1}
        else:
            assert res["status"].startswith("excluded"), (name, res["status"])
            assert not calls, f"{name}: the decoder must not run on an excluded recording"
        print(f"{name}: {res['status'][:110]}")
    assert "fewer than 250 present trials (240)" in results["240_present"]["status"]
    assert "fewer than 25 catch trials (24)" in results["24_catch"]["status"]
    assert "block 1: fewer than 3 catch trials (2)" in results["2_catch_block1"]["status"]
    assert results["preprocessor_excluded"]["status"].startswith("excluded: preprocessing: 13 bad channels")

    # several failing rules are all recorded
    t = base_template()
    t.loc[t.index[(t.block == 2) & t["catch"]][1:], "retained"] = False
    t.loc[t.index[(t.block == 2) & t.present & (t.side == "left")][5:], "retained"] = False
    g = INC.section2(dict(trials=t))
    assert not g["passed"] and len(g["reasons"]) == 2, g["reasons"]
    assert g["reasons"][0].startswith("block 2: fewer than 3 catch trials") and "present trials in a hemifield" in g["reasons"][1]
    print(f"several rules at once: {g['reasons']}")

    # sensitivity-induced losses are applied before the floors
    t = base_template()
    t.loc[t.index[(t.block == 3) & t["catch"]][:8], "edge_trial"] = True
    rec = dict(trials=t)
    assert run_with_stubs(rec)[0]["status"] == "ok"
    res_edge, calls = run_with_stubs(rec, drop_edge=True)
    assert res_edge["status"].startswith("excluded") and "block 3: fewer than 3 catch trials" in res_edge["status"] and not calls
    t = base_template()
    t["seen"] = 1.0
    t.loc[t.index[t.present & (t.block == 4) & (t.side == "right")][2:], "seen"] = np.nan
    rec = dict(trials=t)
    assert run_with_stubs(rec)[0]["status"] == "ok"
    res_nr, _ = run_with_stubs(rec, exclude_no_response=True)
    assert res_nr["status"].startswith("excluded") and "block 4: fewer than 20 present trials in a hemifield" in res_nr["status"]
    try:
        INC.section2(dict(trials=base_template()), exclude_no_response=True)
        raise AssertionError("the no-response sensitivity without a report column must refuse")
    except ValueError:
        pass
    print("sensitivities: edge-trial and no-response losses are applied before the floors and can exclude a recording")

    # §8's denominator counts only recordings that pass §2
    statuses = [r["status"] for r in results.values()]
    n_pass = sum(not s.startswith("excluded") for s in statuses)
    assert n_pass == 1
    # the synthetic generator's recordings pass unchanged
    syn = SY.generate(SY.template(1, "nocue"), "G1", 0.5, False, tags=(9, 9))
    g = INC.section2(syn)
    assert g["passed"] and g["keep"].all(), g["reasons"]
    print(f"n_pass_section2 over the five cases = {n_pass}; a synthetic recording passes with every trial kept")
    print("test_inclusion: ALL OK")


if __name__ == "__main__":
    main()
