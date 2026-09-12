"""Shared constants, paths and the events-table reader for the Melcón et al. 2024 port.

Melcón M., Stern E., Kessel D., Arana L., Poch C., Campo P., Capilla A. (2024) "Perception of
near-threshold visual stimuli is influenced by prestimulus alpha-band amplitude but not by alpha
phase", Psychophysiology 61:e14525, doi:10.1111/psyp.14525. Data: OpenNeuro ds006171 (CC0),
doi:10.18112/openneuro.ds006171.v1.0.0 — 36 subjects (sub-01 … sub-36), three tasks (nocue,
noninformative, informative), BioSemi ActiveTwo 128 + 4 EOG at 1024 Hz, one BDF per subject × task.

Everything in this file is derived from the BIDS sidecars (events.tsv / events.json / channels.tsv)
and from the behavioural events only. No EEG is read here (see load.py) and none is decoded
anywhere in melcon_port (README, "hard limit").

Trigger-code scheme, as established from the events tables (README D2, INVENTORY.md §3):
  nocue / informative: 11 12 21 22 = Gabor (hemifield digit 1 left / 2 right, orientation digit
    1 vertical / 2 horizontal); 31 32 = catch trial (no Gabor) after a left / right cue; 1 2 = cue
    left / right (informative only, 200 ms); 124 125 = seen / unseen; 121 122 = reported vertical /
    horizontal; 128 = photodiode.
  noninformative (NOT documented in events.json): 1 2 = cue left / right; 101 102 111 112 = Gabor
    after a LEFT cue, 103 104 113 114 = Gabor after a RIGHT cue (last digit odd = vertical, even =
    horizontal; middle digit 0 vs 1 = the two cue-validity classes, whose assignment to valid /
    invalid cannot be determined from the files); 98 99 = catch after a left / right cue.
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.normpath(os.path.join(HERE, "..", "brain_data", "melcon2024", "ds006171"))
# derived outputs (epoch caches) live beside the data, which is gitignored (workspace_demo/brain_data/)
DERIVED_DIR = os.path.normpath(os.path.join(HERE, "..", "brain_data", "melcon2024", "derived"))
RESULTS_DIR = os.path.join(HERE, "results")
FIG_DIR = os.path.join(HERE, "figures")

TASKS = ("nocue", "noninformative", "informative")
SUBJECTS = list(range(1, 37))
FS_RAW = 1024.0        # per eeg.json; four BDFs (sub-35 ×2, sub-36 ×2) are actually 2048 Hz — load.py reads the header (README D13)
N_EEG = 128            # scalp channels (BioSemi A1..D32 = channels.tsv rows 1..128, 10-20 names)
EOG_NAMES = ("VEOG1", "VEOG2", "HEOG1", "HEOG2")   # channels.tsv names of BDF EXG1..EXG4
TRIALS_PER_TASK = 400
TRIALS_PER_BLOCK = 100  # self-paced breaks every 100 trials (paper); the break screen fires a 128

CUE_CODES = {1: "left", 2: "right"}
PHOTODIODE = 128
RESP_SUBJECTIVE = {124: 1, 125: 0}     # seen = 1, unseen = 0 (events.json)
RESP_OBJECTIVE = {121: 1, 122: 2}      # reported vertical = 1, horizontal = 2 (events.json)
BLOCK_BREAK_TRIALS = (0, 100, 200, 300, 400)  # trial_number of the break-screen 128s

# Gabor / catch codes -> (present, hemifield-or-cue-side, orientation, validity_digit)
#   hemifield: for nocue/informative the Gabor's hemifield (catch: the "virtual" side of events.json);
#              for noninformative the CUE side (the Gabor's own hemifield is not recoverable, D2).
#   validity_digit: None (nocue), "valid" (informative, 100 %), 0 / 1 (noninformative, undetermined).
STIM_CODES = {
    11: (True, "left", "vertical", None), 12: (True, "left", "horizontal", None),
    21: (True, "right", "vertical", None), 22: (True, "right", "horizontal", None),
    31: (False, "left", None, None), 32: (False, "right", None, None),
    101: (True, "left", "vertical", 0), 102: (True, "left", "horizontal", 0),
    103: (True, "right", "vertical", 0), 104: (True, "right", "horizontal", 0),
    111: (True, "left", "vertical", 1), 112: (True, "left", "horizontal", 1),
    113: (True, "right", "vertical", 1), 114: (True, "right", "horizontal", 1),
    98: (False, "left", None, None), 99: (False, "right", None, None),
}
TASK_STIM_CODES = {
    "nocue": (11, 12, 21, 22, 31, 32),
    "informative": (11, 12, 21, 22, 31, 32),
    "noninformative": (101, 102, 103, 104, 111, 112, 113, 114, 98, 99),
}
PD_MAX_DELAY_S = 0.20   # a 128 later than this after its trigger is not accepted as its photodiode


def sub_id(subject: int) -> str:
    return f"sub-{subject:02d}"


def bids_path(subject: int, task: str, suffix: str) -> str:
    """suffix: 'eeg.bdf', 'events.tsv', 'channels.tsv', 'eeg.json', 'events.json'."""
    s = sub_id(subject)
    return os.path.join(DATA_ROOT, s, "eeg", f"{s}_task-{task}_{suffix}")


def available(kind: str = "events") -> list[tuple[int, str]]:
    """(subject, task) pairs for which the events table ('events') or the BDF ('bdf') is on disk."""
    suffix = {"events": "events.tsv", "bdf": "eeg.bdf"}[kind]
    out = []
    for f in sorted(glob.glob(os.path.join(DATA_ROOT, "sub-*", "eeg", f"*_task-*_{suffix}"))):
        m = re.search(r"sub-(\d+)_task-(\w+)_", os.path.basename(f))
        out.append((int(m.group(1)), m.group(2)))
    return sorted(out, key=lambda st: (st[0], TASKS.index(st[1])))


def read_events(subject: int, task: str) -> pd.DataFrame:
    """The raw events.tsv with numeric dtypes. The 'sample' column is a broken character encoding of
    the sample index (README D3) and is dropped; 'onset' (seconds, 1024 Hz) is the time base."""
    df = pd.read_csv(bids_path(subject, task, "events.tsv"), sep="\t", dtype={"sample": str})
    for c in ("onset", "duration", "trial_type", "value", "trial_number", "gabor_contrast", "subjective_r", "objective_r"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.drop(columns=["sample"]).reset_index(drop=True)


def read_channels(subject: int, task: str) -> pd.DataFrame:
    return pd.read_csv(bids_path(subject, task, "channels.tsv"), sep="\t")


def read_participants() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_ROOT, "participants.tsv"), sep="\t")


def trial_table(subject: int, task: str) -> pd.DataFrame:
    """One row per trial (Gabor or catch), built from the events table only.

    Photodiode correction (README D1): every cue / Gabor / catch trigger is immediately followed by
    a 128 (verified over all 104 files); the trigger's onset is replaced by that 128's onset
    (`onset_pd`) and the delay is kept (`pd_delay`). If no 128 follows within PD_MAX_DELAY_S the
    trigger's own onset plus the file's median delay is used and `pd_corrected` is False. All other
    128s (the break screens at trial_number 0/100/200/300/400) and all response triggers are used
    only for behaviour.

    Behaviour: `seen` comes from the first 124/125 trigger of the trial (events.json's
    `subjective_r` column is empty in 16 files but never contradicts the triggers); `objective`
    from the first 121/122 trigger, else from the `objective_r` column (`objective_source`).
    """
    df = read_events(subject, task)
    tt = df.trial_type.values
    on = df.onset.values
    tn = df.trial_number.values
    n = len(df)
    codes = TASK_STIM_CODES[task]
    is_trigger = np.isin(tt, list(codes) + list(CUE_CODES))
    # the 128 immediately after each trigger
    nxt_is_pd = np.r_[tt[1:] == PHOTODIODE, False]
    nxt_on = np.r_[on[1:], np.nan]
    delay = np.where(is_trigger & nxt_is_pd, nxt_on - on, np.nan)
    ok = is_trigger & nxt_is_pd & (delay >= 0) & (delay <= PD_MAX_DELAY_S)
    med_delay = float(np.nanmedian(delay[ok & np.isin(tt, list(codes))])) if ok.any() else np.nan
    rows = []
    stim_idx = np.where(np.isin(tt, list(codes)))[0]
    # blocks: the break screens fire an UNPAIRED 128 (not immediately preceded by a cue/stim trigger);
    # a break 128 between two stimulus triggers starts a new block. Used when exactly three interior
    # breaks are found (4 blocks); otherwise ceil(trial_number / 100) with block_source = "trial_number".
    unpaired = np.where((tt == PHOTODIODE) & ~np.r_[False, ok[:-1]])[0]
    interior = [u for u in unpaired if stim_idx[0] < u < stim_idx[-1]]
    if len(interior) == 3:
        block_of = np.searchsorted(np.array(interior), stim_idx) + 1
        block_source = "break_128"
    else:
        block_of = None
        block_source = "trial_number"
    for k, i in enumerate(stim_idx):
        present, side, orient, vdig = STIM_CODES[int(tt[i])]
        t_no = int(tn[i]) if not np.isnan(tn[i]) else -1
        # cue: the last 1/2 before this trigger with the same trial number
        cue_i = None
        j = i - 1
        while j >= 0 and tn[j] == tn[i]:
            if tt[j] in CUE_CODES:
                cue_i = j
                break
            j -= 1
        # responses: rows after this trigger, before the next stimulus trigger, same trial number
        stop = stim_idx[k + 1] if k + 1 < len(stim_idx) else n
        seg = np.arange(i + 1, stop)
        seg = seg[tn[seg] == tn[i]]
        s_rows = [int(tt[j]) for j in seg if tt[j] in RESP_SUBJECTIVE]
        o_rows = [int(tt[j]) for j in seg if tt[j] in RESP_OBJECTIVE]
        s_on = [on[j] for j in seg if tt[j] in RESP_SUBJECTIVE]
        seen_col = df.subjective_r.iloc[i]
        obj_col = df.objective_r.iloc[i]
        seen = RESP_SUBJECTIVE[s_rows[0]] if s_rows else (int(seen_col) if not np.isnan(seen_col) else np.nan)
        seen_src = "trigger" if s_rows else ("column" if not np.isnan(seen_col) else "missing")
        if o_rows:
            objective, obj_src = RESP_OBJECTIVE[o_rows[0]], "trigger"
        elif not np.isnan(obj_col):
            objective, obj_src = int(obj_col), "column"
        else:
            objective, obj_src = np.nan, "none"
        onset_pd = nxt_on[i] if ok[i] else on[i] + med_delay
        cue_on_pd = np.nan
        if cue_i is not None:
            cue_on_pd = nxt_on[cue_i] if ok[cue_i] else on[cue_i] + med_delay
        rows.append(dict(
            subject=subject, task=task, trial=t_no,
            block=int(block_of[k]) if block_of is not None else (int(np.ceil(t_no / TRIALS_PER_BLOCK)) if t_no > 0 else 0),
            block_source=block_source,
            code=int(tt[i]), present=present, catch=not present,
            side=side, orientation=orient, validity_digit=vdig if task == "noninformative" else ("valid" if task == "informative" else None),
            cue_side=CUE_CODES[int(tt[cue_i])] if cue_i is not None else None,
            contrast=float(df.gabor_contrast.iloc[i]),
            seen=seen, seen_source=seen_src,
            objective=objective, objective_source=obj_src,
            objective_correct=(np.nan if (np.isnan(objective) or orient is None)
                               else float({1: "vertical", 2: "horizontal"}[int(objective)] == orient)),
            seen_col_conflict=bool(s_rows and not np.isnan(seen_col) and int(seen_col) != RESP_SUBJECTIVE[s_rows[0]]),
            obj_col_conflict=bool(o_rows and not np.isnan(obj_col) and int(obj_col) != RESP_OBJECTIVE[o_rows[0]]),
            n_subj_resp=len(s_rows), n_obj_resp=len(o_rows),
            seen_col=seen_col, objective_col=obj_col,
            onset_trigger=float(on[i]), onset_pd=float(onset_pd), pd_delay=float(delay[i]) if ok[i] else np.nan,
            pd_corrected=bool(ok[i]),
            cue_onset_pd=float(cue_on_pd), cue_soa=float(onset_pd - cue_on_pd) if cue_i is not None else np.nan,
            cue_pd_delay=float(delay[cue_i]) if (cue_i is not None and ok[cue_i]) else np.nan,
            rt_subjective=float(s_on[0] - onset_pd) if s_on else np.nan,
        ))
    out = pd.DataFrame(rows)
    out.attrs["median_pd_delay"] = med_delay
    out.attrs["n_pd_total"] = int((tt == PHOTODIODE).sum())
    out.attrs["n_pd_used"] = int(ok.sum())
    out.attrs["n_pd_break"] = int(len(unpaired))          # unpaired 128s = break / start screens
    out.attrs["n_pd_break_interior"] = int(len(interior))
    out.attrs["block_source"] = block_source
    out.attrs["stray_codes"] = sorted(set(np.unique(tt[~np.isnan(tt)]).astype(int).tolist())
                                      - set(codes) - set(CUE_CODES) - {PHOTODIODE} - set(RESP_SUBJECTIVE) - set(RESP_OBJECTIVE))
    return out


def parse_subjects(s: str) -> list[int]:
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out
