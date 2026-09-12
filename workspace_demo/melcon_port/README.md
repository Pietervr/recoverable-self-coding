# Melcón et al. 2024 (OpenNeuro ds006171) — the second, visual, human dataset: download and loader

Companion of `../sergent_port/` for the Entropy special-issue paper (access at threshold, brain vs
language model). This folder holds the **data provenance, the events-table inventory, the loader and a
DRAFT pre-registration** for a secondary analysis on a visual near-threshold detection dataset with a
trial-by-trial intensity covariate (Gabor contrast) and a seen/unseen report on every trial.

**Hard limit (owner, 2026-09-12): no EEG of this dataset has been decoded, averaged, contrasted or
plotted.** `load.py` reads BDF files into epochs and counts them; `inventory.py` reads only the
behavioural events tables; nothing here trains a classifier or computes a condition mean. The secondary
analysis is to be pre-registered (`PREREG_secondary_melcon.md`, DRAFT) and the owner wants the first
results of the running model-side simulation before any neural analysis is opened.

## Source and citation

Melcón M., Stern E., Kessel D., Arana L., Poch C., Campo P., Capilla A. (2024). *Perception of
near-threshold visual stimuli is influenced by prestimulus alpha-band amplitude but not by alpha
phase.* Psychophysiology 61:e14525, doi:10.1111/psyp.14525. Dataset: Melcón, Stern, Arana & Capilla,
"EEG data during three near-threshold visual detection tasks: a no-cue task, a noninformative cue task
(50% validity), and an informative cue task (100% validity)", OpenNeuro **ds006171 v1.0.0**
(2025-04-24), CC0, doi:10.18112/openneuro.ds006171.v1.0.0. BioSemi ActiveTwo, 128 scalp + 4 EOG
(+ 8 unused EXG/GSR/Erg/Resp/Plet/Temp) at 1024 Hz, one BDF per subject × task, BIDS 1.8.0.

## Download (2026-09-12)

```sh
aws s3 sync s3://openneuro.org/ds006171 workspace_demo/brain_data/melcon2024/ds006171 --no-sign-request
```

Public bucket, no credentials. **561 objects, 72,833,079,341 bytes (72.8 GB; 67.8 GiB)**, of which the
104 BDF files are 72,823,531,520 bytes (444 MB – 1.45 GB each; nocue ≈ 0.45 GB, cue tasks ≈ 0.65 GB
because of the cue period) and the 457 sidecars 9.5 MB. The brief's estimate of ≈ 50 GB was low. The
sync was run as three subject partitions in parallel (`--exclude "*" --include "sub-0*" …`, 24
concurrent requests) at ≈ 10 MB/s, then a final full `aws s3 sync` pass; the listing taken before the
download is `results/s3_manifest_2026-09-12.txt` and `verify_download.py` checks every local file's
size against it (`results/download_verification.csv`, per-subject counts and bytes). **Download
status at the time of this README: see the bottom of this file.**

**Where the data live (owner, 2026-09-12).** The dataset stays on the Mac in
`workspace_demo/brain_data/melcon2024/` while the analysis runs and is moved to the SSD when the
analysis is done — the same drill as `brain_data/sergent2021/`. `workspace_demo/brain_data/` is in the
repo's `.gitignore`; data are never committed. Derived epoch caches, if written (`load.py --cache`),
go to `brain_data/melcon2024/derived/` beside the data.

## What is in the dataset (from the events tables — `INVENTORY.md` has every number)

* 36 subjects `sub-01 … sub-36`, **104 of 108 recordings** on the server: missing sub-01 informative,
  sub-02 noninformative, sub-35 nocue, sub-36 noninformative.
* Per recording 400 trials in 4 blocks of 100 (self-paced breaks): 360 Gabor-present (90 per
  hemifield × orientation), 40 catch; seen/unseen on every trial (124/125), orientation question on
  ≈ 15 % (121/122); the Gabor contrast is the online staircase's output for that trial.
* 41,581 trials; seen rate on present trials 0.47 / 0.47 / 0.49 (nocue / noninformative /
  informative), false alarms on catch 0.075; objective accuracy 0.69 (0.87 seen, 0.52 unseen).
* Timing (paper): fixation 800–1200 ms (nocue) or cue 200 ms + 500–800 ms; Gabor 50 ms at 5° below
  and 5° left/right of fixation; **subjective question 250–350 ms after Gabor offset** (no trigger);
  response median 0.93 s after Gabor onset.
* `participants.tsv` does not belong to these 36 subjects (55 rows, other ids, other ages) — no
  demographics (D8).

## Files

| file | what it does |
|---|---|
| `common.py` | paths, the trigger-code tables, `read_events`, `trial_table` (per-trial table with the photodiode correction and the behaviour from the response triggers) |
| `inventory.py` | events-only inventory → `INVENTORY.md`, `results/trials_all.csv` (41,581 rows), `results/inventory_by_file.csv` |
| `load.py` | one subject × task → epochs `X (n_trials, 128, n_times)` + trial table in the shape `sergent_port/decode.py` consumes; `--verify` compares epoch counts with the events tables and the Status channel with events.tsv (`results/load_verification.csv`); `--cache` writes npz |
| `verify_download.py` | local files vs the S3 manifest → `results/download_verification.csv` |
| `PREREG_secondary_melcon.md` | DRAFT pre-registration for the owner's review |
| `results/s3_manifest_2026-09-12.txt` | the bucket listing at download time |

## Environment

The repo-root venv used by `sergent_port` (`../../.venv`): Python 3.14.6, mne 1.13.0, numpy 2.5.3,
scipy 1.18.1, pandas 3.0.5, scikit-learn 1.9.1 (macOS, Apple silicon). `load.py` needs ≈ 1.7 GB RAM
per cue-task file (144 channels × 1.45 M samples as float64) and takes ≈ 6 s per recording; the
`workspace_demo/t1_access/.venv` (JAX) is not used here. `aws` CLI 2 for the download.

## How to run

```sh
cd workspace_demo/melcon_port
../../.venv/bin/python inventory.py                       # events only, seconds
../../.venv/bin/python load.py --subjects 1-3 --verify    # reads BDFs, counts epochs, no decoding
../../.venv/bin/python verify_download.py                 # after the sync
```

## D-list — every deviation from, and choice beyond, the sergent_port pipeline

**D1 — the photodiode rule.** `events.json`: *"128: Photodiode to correct screen delays: replace each
128 with the next trigger code (delayed) and then forget about the rest of the triggers."* In every one
of the 104 files each cue / Gabor / catch trigger is followed, as the very next event, by a 128 at
30–83 ms (Gabor: median 39 ms; cue: median 53 ms, one outlier of 151 ms), the break screens fire a
128 at trial 0/100/200/300/400, and nothing else does. The rule is therefore read as: *the 128 is the
delayed, true onset of the trigger immediately before it* — every epoch is locked to its own trial's
128, the software trigger's onset is discarded, the response triggers are used for behaviour only and
the break-screen 128s are dropped. `trial_table` keeps the measured delay per trial (`pd_delay`) and a
flag; no trial in the dataset lacked its 128, so the fallback (trigger onset + file median delay) is
never exercised. The literal reading "the *next* trigger code" cannot be right — the next code after
a 128 is the response.

**D2 — the trigger-code scheme.** `events.json` documents only 11/12/21/22/31/32 (Gabor hemifield ×
orientation, catch after a left/right cue), 124/125, 121/122 and 128. The **noninformative** task
uses codes it does not document: 1/2 (cue, 200 ms), 101–104 / 111–114 (Gabor, 45 each), 98/99 (catch,
20 each). From the events alone (`INVENTORY.md` §3): cue 1 always precedes 11/12/31 in the
informative task, so **cue 1 = left, cue 2 = right**; in the noninformative task 101/102/111/112 follow
a left cue and 103/104/113/114 a right cue; the objective responses make the **odd last digit
vertical** (accuracy 0.65–0.72 under that mapping, below chance under the reverse); the middle digit
(0/1) separates the two cue-validity classes, but **which digit is "valid" cannot be determined from
the files** (both have 180 trials; seen rate 0.474 vs 0.473; only the weak contrast–seen relation of
digit 0, INVENTORY §4, hints that it is the valid class). The Gabor's own hemifield on a noninformative
trial is therefore unknown; `side` holds the cue side for that task. Settling it needs the authors'
presentation script.

**D3 — time base.** The `sample` column of events.tsv is a broken character encoding of the sample
index (a single code-point character equal to the sample number, unreadable beyond U+FFFF and mangled
elsewhere: 75 of 1,253 rows decodable in sub-01 nocue) and is dropped. `onset` (seconds) is used, but
it carries only six significant figures — 10 ms resolution past 100 s — so `load.py` snaps each
photodiode onset to the nearest 128 of the BDF Status channel (≤ 5 samples away; the Status channel
reproduces events.tsv event-for-event, `load.py --verify`).

**D4 — reference and filters** (sergent_port used the authors' preprocessed FieldTrip data; here the
raw BDF is processed, mirroring `SoundConsciousEEG_PreProcessing.m`): common average reference over
the 128 scalp channels (Sergent: `refchannel 'all'`; BioSemi records against CMS/DRL and must be
re-referenced); high-pass 0.4 Hz (Sergent: `hpfreq .4`, MNE's default FIR instead of FieldTrip's
Butterworth); 50 Hz notch (Sergent: `dftfilter`); no low-pass beyond the acquisition filter (Sergent:
none). The 4 EOG channels are kept out of the feature set (Sergent: 63 scalp channels).

**D5 — epoch window and baseline.** −0.5 … +1.0 s around the photodiode-corrected Gabor/catch onset,
baseline −0.5 … 0 s (Sergent: −0.5 … +2.0 s, baseline −0.5 … 0). The Melcón trial is over by ≈ 1 s
(question at +0.30 … 0.40 s, response median +0.93 s); the cue tasks' cue is at −0.7 … −1.0 s, so a
longer pre-stimulus window would run into it.

**D6 — sampling rate.** Decimation by 2 to 512 Hz (the paper's own analysis rate; Sergent's data were
500 Hz) without an extra anti-alias filter: the BioSemi on-line 5th-order sinc low-pass sits at
fs/5 = 204.8 Hz (header: 208 Hz), below the new Nyquist of 256 Hz. Window lengths of 16 samples at
512 Hz are 31.25 ms (Sergent: 16 samples at 500 Hz = 32 ms).

**D7 — no artefact handling in the loader.** No ICA, no channel repair, no trial rejection here; the
authors' visual rejection + ICA + interpolation (307 ± 35 / 290 ± 38 / 256 ± 47 trials retained per
task, 5–6 subjects excluded per task) are not part of the dataset. A fixed automatic rule is proposed
in the pre-registration (§3) and is the owner's call.

**D8 — participants.tsv.** 55 rows with ids `sub-001 … sub-590`, ages 27–70, two-session columns:
not the 36 subjects of this dataset (the paper: 36 graduate students, 21.0 ± 6.2 years). No mapping
exists in the files; no demographics are used.

**D9 — blocks and cross-validation.** 4 blocks of 100 trials per recording (Sergent: 20 blocks of
≈ 48), derived from the break-screen 128s where exactly three interior ones exist (97 recordings) and
from ceil(trial_number / 100) in the other 7 (sub-02 nocue has a spurious extra 128; sub-10 and sub-12
have no break 128s at all) — `block_source` in the trial table. The likelihood cross-validation by
block is therefore 4-fold (pre-registration §5).

**D10 — the contrast column of the noninformative task** neither predicts the seen/unseen response
(per-subject r median 0.03 vs 0.14 / 0.22 in the other tasks, no lag better) nor follows the
staircase rule (`INVENTORY.md` §4). It is not used as an intensity covariate; the cause cannot be
determined from the files.

**D11 — negative contrasts.** 36 present trials of sub-11 informative have a negative recorded
contrast (min −0.0135): the staircase ran below zero. What was displayed is unknown; the trials are to
be excluded.

**D12 — 272-channel BDF files.** Nine recordings were saved in BioSemi's 256-channel configuration
(272 channels: A1…H32 plus the same 16 extras) while `channels.tsv` lists 144 for every file:
sub-02 nocue + informative, sub-04 and sub-05 all three tasks, sub-11 informative
(`results/bdf_headers.csv`; the other large files, sub-32/35/36, are 144-channel recordings that
simply ran longer, up to 2,340 s). In sub-02 the E–H groups are exactly zero and A–D carry the EEG
(SD 60–130 µV; corr(A1, E1) = 0), i.e. the same 128-electrode cap on the larger amplifier. `load.py`
maps channels by BioSemi name (A1…D32 → the 128 rows of channels.tsv, the extras by name) and drops
E–H; `load.py --verify` records the header channel count per recording.

**D13 — 2048 Hz recordings.** Four BDF files were recorded at 2048 Hz — sub-35 informative and
noninformative, sub-36 informative and nocue (`results/bdf_headers.csv`, samples per record) —
although the identical `eeg.json` sidecars say 1024 Hz for every file and `events.tsv` onsets are in
seconds throughout. `load.py` takes the rate from the BDF header, decimates by round(sfreq / 512) (4
for these, 2 otherwise) so every recording comes out at 512 Hz with 769 samples per epoch, and
expresses its snap and matching tolerances in milliseconds (8 ms and 6 ms) rather than samples.

## Download and verification status (2026-09-12, 18:45 UTC)

**Complete.** `verify_download.py`: 561 of 561 objects present, every one byte-matched to the
manifest (72,833,079,341 bytes; 69 GiB on disk), no stray partial files, a final
`aws s3 sync --dryrun` against the bucket lists nothing; all 104 BDF headers are consistent with
their file sizes (`results/bdf_headers.csv`: 95 files with 144 channels, 9 with 272 — D12; 100 at
1024 Hz, 4 at 2048 Hz — D13; durations 1,004–2,340 s). The download ran 16:09–18:27 UTC: the
parallel `aws s3 sync` partitions were twice stopped by the harness for low system memory (other
applications' pressure, not the CLI's ~0.3 GB), so the last 36 files came through a per-file
`aws s3 cp` loop; every file was checked by size at the end of its own copy.

**Loader (`load.py --verify`, all 104 recordings, no decoding; `results/load_verification.csv`):**
every recording yields `X (n, 128, 769)` at 512 Hz; **41,578 of 41,581 trials become epochs — the
epoch count equals the events-table trial count in 101 recordings**, and in the other three (sub-03
nocue, sub-20 noninformative, sub-23 informative) trial 1 is lost because the recording starts 0.2–
0.46 s before the first Gabor, inside the −0.5 s baseline. The BDF Status channel reproduces
`events.tsv`: every tsv row has its Status event within 6 ms with the same code except two single
rows (the stray tsv codes 41 in sub-04 noninformative and 33 in sub-16 noninformative); 26 recordings
carry 1–2 extra Status triggers the tsv omits (29 in all; single stray codes such as 84, 16, 20, 64),
none of them a cue/Gabor/catch trigger except one 101 and one 125; every trial's photodiode 128 was
found in the Status channel (0 unsnapped; ≤ 10 samples from the rounded tsv onset). `inventory.py`
ran on all 104 events tables (`INVENTORY.md`).

**Storage (owner's rule, 2026-09-12):** the dataset stays on the Mac in
`workspace_demo/brain_data/melcon2024/` while the analysis runs and is moved to the SSD when the
analysis is done — the same drill as `brain_data/sergent2021/`. Nothing under `brain_data/` is
committed.

**Hard limit kept:** no EEG of ds006171 was decoded, averaged by condition, contrasted or plotted.
The neural analysis opens when the Entropy session says so, after the pre-registration is frozen.
