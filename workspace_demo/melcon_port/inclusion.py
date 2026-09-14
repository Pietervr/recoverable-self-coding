#!/usr/bin/env python3
"""The label-free recording inclusion of PREREG_secondary_melcon.md §2 — DRAFT v5 (Codex, continuation review 4, §6).

One entry point, run before any decoding, for preprocessed epochs (preprocess.preprocess_raw, preprocess.read_cache) and
synthetic ones (synthetic.generate) alike.

Trial exclusions first, under the requested retention variant, in this order (a trial carries its first reason): no epoch;
not retained by the artefact rule of §3; a present trial with a non-positive or missing recorded contrast; and, as
sensitivities, an edge trial (drop_edge) and a trial without a seen/unseen response (exclude_no_response).

Then the recording rules on the remaining trials, every failing rule recorded (not only the first): the preprocessor's
exclusion (more than 12 bad channels in a block); fewer than MIN_PRESENT present or MIN_CATCH catch trials; any block of
1-4 with fewer than LK.MIN_CATCH catch trials or fewer than LK.MIN_SIDE present trials in either hemifield; any decoder
half with fewer than DEC.MIN_CATCH_HALF catch trials; trials outside blocks 1-4. A recording failing any rule is
'excluded' — never a technical failure and never an unavailable fold — and the recordings that pass are §8's
n_pass_section2. Nothing but presence, hemifield, block, contrast, the epoch/retention flags and (for the no-response
sensitivity) the report flag is read; no EEG sample.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import decoder as DEC
import likelihood as LK

MIN_PRESENT = 250
MIN_CATCH = 25
BLOCKS = (1, 2, 3, 4)
TRIAL_RULES = ("no epoch", "artefact rule", "non-positive contrast", "edge trial (sensitivity)",
               "no seen/unseen response (sensitivity)")

SPEC = dict(min_present=MIN_PRESENT, min_catch=MIN_CATCH, blocks=BLOCKS, min_catch_block=LK.MIN_CATCH,
            min_present_side_block=LK.MIN_SIDE, min_catch_half=DEC.MIN_CATCH_HALF, halves=DEC.HALVES, trial_rules=TRIAL_RULES)


def trial_exclusions(trials: pd.DataFrame, drop_edge: bool = False, exclude_no_response: bool = False) -> np.ndarray:
    """Per trial its first exclusion reason ('' for a kept trial), as an object array in the row order of `trials`."""
    n = len(trials)
    present = trials["present"].to_numpy(bool)
    contrast = pd.to_numeric(trials["contrast"], errors="coerce").to_numpy(float)
    rules = [(TRIAL_RULES[0], ~trials["has_epoch"].to_numpy(bool)),
             (TRIAL_RULES[1], ~trials["retained"].to_numpy(bool)),
             (TRIAL_RULES[2], present & ~(contrast > 0))]
    if drop_edge:
        rules.append((TRIAL_RULES[3], trials["edge_trial"].to_numpy(bool)))
    if exclude_no_response:
        if "seen" not in trials:
            raise ValueError("the no-response sensitivity needs the trials' 'seen' column")
        rules.append((TRIAL_RULES[4], ~np.isfinite(pd.to_numeric(trials["seen"], errors="coerce").to_numpy(float))))
    reason = np.full(n, "", dtype=object)
    for name, mask in rules:
        reason[(reason == "") & mask] = name
    return reason


def section2(rec: dict, drop_edge: bool = False, exclude_no_response: bool = False) -> dict:
    """{'passed', 'reasons' (every failing recording rule), 'keep' (bool per trial row), 'trial_reason', 'counts'}."""
    trials = rec["trials"]
    why = trial_exclusions(trials, drop_edge, exclude_no_response)
    keep = why == ""
    kept = trials[keep]
    reasons = []
    if bool(rec.get("excluded", False)):
        reasons.append(f"preprocessing: {rec.get('exclude_reason') or 'excluded'}")
    pres = kept["present"].to_numpy(bool)
    catch = kept["catch"].to_numpy(bool)
    side = kept["side"].to_numpy()
    blk = kept["block"].to_numpy()
    n_pres, n_catch = int(pres.sum()), int(catch.sum())
    if n_pres < MIN_PRESENT:
        reasons.append(f"fewer than {MIN_PRESENT} present trials ({n_pres})")
    if n_catch < MIN_CATCH:
        reasons.append(f"fewer than {MIN_CATCH} catch trials ({n_catch})")
    blocks = {}
    for b in BLOCKS:
        m = blk == b
        c = int((catch & m).sum())
        left, right = int((pres & m & (side == "left")).sum()), int((pres & m & (side == "right")).sum())
        blocks[b] = dict(catch=c, present_left=left, present_right=right)
        if c < LK.MIN_CATCH:
            reasons.append(f"block {b}: fewer than {LK.MIN_CATCH} catch trials ({c})")
        if min(left, right) < LK.MIN_SIDE:
            reasons.append(f"block {b}: fewer than {LK.MIN_SIDE} present trials in a hemifield ({left} left, {right} right)")
    halves = {}
    for h in DEC.HALVES:
        c = int((catch & np.isin(blk, h)).sum())
        halves[f"{h[0]}-{h[1]}"] = c
        if c < DEC.MIN_CATCH_HALF:
            reasons.append(f"decoder half {h}: fewer than {DEC.MIN_CATCH_HALF} catch trials ({c})")
    outside = sorted({int(b) for b in blk} - set(BLOCKS))
    if outside:
        reasons.append(f"trials outside blocks 1-4: {outside}")
    excluded_trials = {r: int((why == r).sum()) for r in TRIAL_RULES if (why == r).any()}
    return dict(passed=not reasons, reasons=reasons, keep=keep, trial_reason=why,
                counts=dict(present=n_pres, catch=n_catch, blocks=blocks, halves=halves, excluded_trials=excluded_trials))


def apply(rec: dict, gate: dict) -> dict:
    """A shallow copy of the recording whose trials keep only the included rows as retained (the reason is kept)."""
    out = dict(rec)
    tr = rec["trials"].copy()
    tr["retained"] = gate["keep"]
    tr["section2_exclusion"] = gate["trial_reason"]
    out["trials"] = tr
    return out


def report(gate: dict) -> dict:
    return dict(passed=gate["passed"], reasons=list(gate["reasons"]), counts=gate["counts"])
