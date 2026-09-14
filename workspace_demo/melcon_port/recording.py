#!/usr/bin/env python3
"""One recording's model comparison — PREREG_secondary_melcon.md §4, §6–§7, DRAFT v4. Input: preprocessed epochs
(preprocess.py) or synthetic ones (synthetic.py). Nothing here is run on ds006171 EEG before the freeze.

Inside each held-out half B = {b1, b2} the likelihood runs a two-fold block cross-validation on the projections of
the one decoder fitted on the other half: train on b1 and score b2, and train on b2 and score b1. Across the two halves
every block is scored once: the recording's four folds. Per window and model, the model is AVAILABLE when it is
available on all four folds; its evidence is the mean over the four held-out blocks of the block's summed held-out
log-likelihood, and the held-out log-score difference per trial is Delta = (sum ll_twostate - sum ll_graded) / n over
the four blocks' trials. Seeds: likelihood.fit tags (subject, task index, half index, fold index, window).

Status: 'ok'; 'excluded: …' for a label-free inclusion rule of §2 (a decoder half short of catch trials); 'technical
failure: …' for an exception anywhere in the decoder or the fits (§8 counts those separately).
"""
from __future__ import annotations

import traceback

import numpy as np

import decoder as DEC
import likelihood as LK

TASK_INDEX = {"nocue": 0, "informative": 1, "noninformative": 2}
WINDOWS = tuple(DEC.EARLY + DEC.MAIN)


def recording_scores(rec: dict, subject: int, task: str, windows=WINDOWS, models=LK.PRIMARY, variant: str = "all_present",
                     drop_edge: bool = False, causal: bool = False) -> dict:
    try:
        dec = DEC.split_half(rec, variant=variant, drop_edge=drop_edge, causal=causal)
        if dec["status"] != "ok":
            return dict(status=dec["status"], subject=subject, task=task)
        nW, nM = len(windows), len(models)
        held = np.zeros((nW, nM))
        avail = np.ones((nW, nM), dtype=bool)
        n_trials = np.zeros(nW, dtype=int)
        reasons = [[set() for _ in models] for _ in windows]
        auc = np.full((nW, 2), np.nan)
        folds = {}
        for hi, (B, d) in enumerate(sorted(dec["halves"].items())):
            tr, W = d["trials"], d["W"]
            catch = tr["catch"].to_numpy(bool)
            right = (tr["side"].to_numpy() == "right") & ~catch
            logc = np.log(np.where(catch, 1.0, tr["contrast"].to_numpy(float)))
            logc = np.where(catch, np.nan, logc)
            blk = tr["block"].to_numpy()
            for wi, w in enumerate(windows):
                auc[wi, hi] = d["auc"][w]
                for fi, (b_tr, b_te) in enumerate(((B[0], B[1]), (B[1], B[0]))):
                    mtr, mte = blk == b_tr, blk == b_te
                    train = LK.Block(W[mtr, w], logc[mtr], catch[mtr], right[mtr])
                    test = LK.Block(W[mte, w], logc[mte], catch[mte], right[mte])
                    s = LK.fold_scores(train, test, tags=(subject, TASK_INDEX[task], hi, fi, w), models=models)
                    folds[(hi, fi, w)] = s
                    n_trials[wi] += int(mte.sum())
                    for mi, m in enumerate(models):
                        if s[m]["available"]:
                            held[wi, mi] += s[m]["heldout"]
                        else:
                            avail[wi, mi] = False
                            reasons[wi][mi].add(s[m]["reason"])
        evidence = np.where(avail, held / 4.0, np.nan)
        mi2, mi3 = models.index("graded"), models.index("twostate")
        delta = np.where(avail[:, mi2] & avail[:, mi3], (held[:, mi3] - held[:, mi2]) / np.maximum(n_trials, 1), np.nan)
        return dict(status="ok", subject=subject, task=task, windows=list(windows), models=list(models), evidence=evidence,
                    available=avail, delta=delta, n_trials=n_trials, auc=auc,
                    reasons=[[sorted(r) for r in row] for row in reasons], folds=folds, decoder=dec)
    except Exception as e:                                        # §8: counted as a technical failure, never dropped
        return dict(status=f"technical failure: {type(e).__name__}: {e}", subject=subject, task=task,
                    traceback=traceback.format_exc())
