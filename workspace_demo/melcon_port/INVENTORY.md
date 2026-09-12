# ds006171 (Melcón et al. 2024) — inventory from the events tables

Generated 2026-09-12 by `inventory.py` from `../brain_data/melcon2024/ds006171` — **events.tsv / participants.tsv only; no EEG was read for this file.** Per-trial rows: `results/trials_all.csv`; per-file rows (every column below and more): `results/inventory_by_file.csv`. Code scheme and the photodiode rule: `common.py` docstring and README D1–D3.

## 1. What is on the server and on disk

* Subjects sub-01 … sub-36; tasks nocue / noninformative / informative; **104 of 108 subject × task recordings exist** (BDF + sidecars). Missing on OpenNeuro: sub-01 informative, sub-02 noninformative, sub-35 nocue, sub-36 noninformative.
* Events tables on disk: 104; BDF files on disk at generation time: 104 (the download runs separately; see README).
* `participants.tsv` has **55 rows with ids `sub-001` … `sub-590`** (sex, age, handedness, `session1`, `late_ses1`, `session2`, `late_ses2`) that do not match the 36 EEG subject ids `sub-01` … `sub-36`, and the paper describes 36 *graduate students, 21.0 ± 6.2 years, 27 female, 30 right-handed*, whereas this table has ages 27–70 (mean 38.3), 24 F / 31 M, 6 left-handed, and two-session columns that the paradigm does not have. **I can't determine the mapping**, and the table is very likely from another study of the same laboratory; per-subject age and sex are therefore not available. What would settle it: the authors (dataset contact via OpenNeuro) or a corrected `participants.tsv` in a later dataset version.
* All 104 `events.json`, `eeg.json` and `channels.tsv` sidecars are byte-identical across files; `electrodes.tsv` is identical across subjects (a template montage, not digitised positions). The BDF headers disagree with the sidecars in two ways (`results/bdf_headers.csv`, from `verify_download.py`): nine recordings have 272 channels (sub-02 nocue/informative, sub-04 and sub-05 all tasks, sub-11 informative; README D12) and four were recorded at 2048 Hz (sub-35 informative/noninformative, sub-36 informative/nocue; README D13) — `eeg.json` says 128 + 4 + 1 channels and 1024 Hz for all.

## 2. Per task

### nocue  (35 subjects)

| sub | trials | present | catch | contrast min / median / max | contrast CV | seen rate | seen by contrast quintile 1→5 | seen on catch | objective n / acc | left / right | vert / horiz | 128s total / used / breaks | pd delay ms med (min–max) | seen missing | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | 400 | 360 | 40 | 0.0132 / 0.0278 / 0.0413 | 0.22 | 0.52 | 0.49 0.51 0.50 0.56 0.56 | 0.00 | 48 / 0.65 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 38 (38–56) | 0 |  |
| 02 | 400 | 360 | 40 | 0.0247 / 0.0455 / 0.0795 | 0.26 | 0.38 | 0.39 0.36 0.42 0.40 0.31 | 0.00 | 49 / 0.63 | 180 / 180 | 180 / 180 | 406 / 400 / 6 | 39 (30–80) | 0 |  |
| 03 | 398 | 358 | 40 | 0.0196 / 0.0280 / 0.0411 | 0.14 | 0.52 | 0.38 0.54 0.51 0.51 0.67 | 0.10 | 56 / 0.59 | 178 / 180 | 180 / 178 | 402 / 398 / 4 | 39 (30–57) | 0 | 398 trials |
| 04 | 400 | 360 | 40 | 0.0262 / 0.0460 / 0.0615 | 0.14 | 0.42 | 0.35 0.35 0.47 0.44 0.47 | 0.03 | 47 / 0.64 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 38 (30–60) | 0 |  |
| 05 | 400 | 360 | 40 | 0.0165 / 0.0247 / 0.0313 | 0.11 | 0.47 | 0.29 0.43 0.51 0.49 0.65 | 0.12 | 56 / 0.77 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 38 (30–55) | 0 |  |
| 06 | 400 | 360 | 40 | 0.0160 / 0.0250 / 0.0324 | 0.09 | 0.49 | 0.24 0.46 0.50 0.47 0.78 | 0.03 | 50 / 0.70 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–63) | 0 |  |
| 07 | 400 | 360 | 40 | 0.0229 / 0.0448 / 0.0661 | 0.20 | 0.45 | 0.33 0.50 0.33 0.57 0.50 | 0.00 | 56 / 0.66 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–60) | 0 |  |
| 08 | 400 | 360 | 40 | 0.0235 / 0.0354 / 0.0484 | 0.15 | 0.50 | 0.44 0.47 0.58 0.44 0.58 | 0.03 | 48 / 0.67 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–71) | 1 |  |
| 09 | 400 | 360 | 40 | 0.0254 / 0.0337 / 0.0504 | 0.18 | 0.51 | 0.42 0.54 0.53 0.47 0.58 | 0.15 | 50 / 0.78 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–55) | 0 |  |
| 10 | 400 | 360 | 40 | 0.0226 / 0.0356 / 0.0482 | 0.17 | 0.45 | 0.42 0.39 0.50 0.40 0.54 | 0.23 | 54 / 0.59 | 180 / 180 | 180 / 180 | 401 / 400 / 1 | 40 (30–73) | 0 |  |
| 11 | 400 | 360 | 40 | 0.0174 / 0.0265 / 0.0364 | 0.14 | 0.49 | 0.43 0.43 0.46 0.53 0.62 | 0.03 | 49 / 0.73 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–71) | 0 |  |
| 12 | 400 | 360 | 40 | 0.0203 / 0.0269 / 0.0360 | 0.12 | 0.50 | 0.39 0.46 0.46 0.58 0.61 | 0.10 | 54 / 0.61 | 180 / 180 | 180 / 180 | 401 / 400 / 1 | 40 (40–73) | 0 |  |
| 13 | 400 | 360 | 40 | 0.0222 / 0.0343 / 0.0414 | 0.12 | 0.47 | 0.33 0.43 0.43 0.46 0.68 | 0.10 | 81 / 0.77 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–40) | 1 | 27 obj from column; 2 obj column≠trigger |
| 14 | 400 | 360 | 40 | 0.0261 / 0.0382 / 0.0487 | 0.13 | 0.49 | 0.43 0.41 0.50 0.51 0.60 | 0.05 | 53 / 0.83 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–60) | 1 |  |
| 15 | 400 | 360 | 40 | 0.0218 / 0.0273 / 0.0348 | 0.09 | 0.50 | 0.29 0.34 0.54 0.62 0.68 | 0.03 | 47 / 0.68 | 180 / 180 | 180 / 180 | 407 / 400 / 7 | 39 (30–56) | 1 |  |
| 16 | 400 | 360 | 40 | 0.0236 / 0.0449 / 0.0815 | 0.31 | 0.36 | 0.31 0.36 0.43 0.35 0.35 | 0.03 | 51 / 0.71 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–56) | 1 |  |
| 17 | 400 | 360 | 40 | 0.0189 / 0.0295 / 0.0415 | 0.17 | 0.45 | 0.33 0.51 0.42 0.47 0.50 | 0.05 | 54 / 0.59 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–56) | 0 |  |
| 18 | 400 | 360 | 40 | 0.0420 / 0.0647 / 0.0795 | 0.14 | 0.44 | 0.32 0.33 0.40 0.61 0.52 | 0.05 | 45 / 0.56 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–63) | 1 |  |
| 19 | 397 | 358 | 39 | 0.0160 / 0.0224 / 0.0301 | 0.11 | 0.51 | 0.32 0.46 0.57 0.52 0.65 | 0.15 | 42 / 0.74 | 178 / 180 | 179 / 179 | 401 / 397 / 4 | 39 (30–56) | 0 | 397 trials |
| 20 | 400 | 360 | 40 | 0.0218 / 0.0319 / 0.0399 | 0.13 | 0.46 | 0.38 0.42 0.47 0.47 0.57 | 0.10 | 54 / 0.56 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–63) | 1 |  |
| 21 | 400 | 360 | 40 | 0.0199 / 0.0329 / 0.0431 | 0.13 | 0.53 | 0.43 0.43 0.50 0.64 0.64 | 0.23 | 53 / 0.58 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–57) | 0 |  |
| 22 | 400 | 360 | 40 | 0.0113 / 0.0242 / 0.0361 | 0.25 | 0.52 | 0.47 0.51 0.60 0.47 0.53 | 0.03 | 55 / 0.82 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–57) | 0 |  |
| 23 | 400 | 360 | 40 | 0.0258 / 0.0337 / 0.0468 | 0.14 | 0.46 | 0.38 0.46 0.53 0.47 0.49 | 0.05 | 55 / 0.62 | 180 / 180 | 180 / 180 | 407 / 400 / 7 | 39 (30–57) | 0 |  |
| 24 | 400 | 360 | 40 | 0.0167 / 0.0231 / 0.0287 | 0.10 | 0.51 | 0.38 0.32 0.54 0.64 0.65 | 0.03 | 101 / 0.91 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–62) | 1 | 47 obj from column; 1 obj column≠trigger |
| 25 | 400 | 360 | 40 | 0.0344 / 0.0494 / 0.0809 | 0.23 | 0.44 | 0.39 0.42 0.44 0.43 0.51 | 0.05 | 58 / 0.67 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–56) | 0 |  |
| 26 | 400 | 360 | 40 | 0.0272 / 0.0549 / 0.0771 | 0.27 | 0.39 | 0.43 0.39 0.31 0.33 0.49 | 0.00 | 48 / 0.67 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–56) | 0 |  |
| 27 | 400 | 360 | 40 | 0.0163 / 0.0226 / 0.0275 | 0.10 | 0.50 | 0.36 0.38 0.47 0.57 0.71 | 0.17 | 47 / 0.60 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–60) | 0 |  |
| 28 | 400 | 360 | 40 | 0.0138 / 0.0262 / 0.0352 | 0.16 | 0.52 | 0.39 0.54 0.50 0.53 0.65 | 0.05 | 44 / 0.84 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (38–57) | 0 |  |
| 29 | 400 | 360 | 40 | 0.0140 / 0.0207 / 0.0291 | 0.13 | 0.49 | 0.31 0.42 0.49 0.58 0.68 | 0.05 | 50 / 0.72 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (38–51) | 2 |  |
| 30 | 400 | 360 | 40 | 0.0195 / 0.0333 / 0.0542 | 0.24 | 0.45 | 0.43 0.42 0.51 0.43 0.44 | 0.03 | 51 / 0.71 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (39–56) | 0 |  |
| 31 | 400 | 360 | 40 | 0.0188 / 0.0267 / 0.0388 | 0.12 | 0.46 | 0.35 0.49 0.43 0.51 0.54 | 0.23 | 57 / 0.58 | 180 / 180 | 180 / 180 | 404 / 400 / 4 | 39 (30–56) | 0 |  |
| 32 | 400 | 360 | 40 | 0.0238 / 0.0409 / 0.0602 | 0.22 | 0.46 | 0.42 0.35 0.46 0.49 0.57 | 0.03 | 57 / 0.58 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–60) | 0 |  |
| 33 | 400 | 360 | 40 | 0.0224 / 0.0295 / 0.0381 | 0.10 | 0.51 | 0.25 0.47 0.51 0.58 0.72 | 0.05 | 55 / 0.65 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–56) | 0 |  |
| 34 | 400 | 360 | 40 | 0.0224 / 0.0296 / 0.0393 | 0.11 | 0.48 | 0.33 0.44 0.46 0.56 0.61 | 0.03 | 51 / 0.69 | 180 / 180 | 180 / 180 | 405 / 400 / 5 | 39 (30–60) | 0 | stray code 40 |
| 36 | 400 | 360 | 40 | 0.0191 / 0.0258 / 0.0351 | 0.13 | 0.50 | 0.24 0.50 0.56 0.60 0.61 | 0.03 | 54 / 0.80 | 180 / 180 | 180 / 180 | 404 / 400 / 4 | 39 (30–60) | 0 |  |

**nocue totals:** 13995 trials, 12596 present, 1399 catch; seen rate 0.474 on present (subject range 0.36–0.53), 0.068 on catch (false alarms; range 0.00–0.23); contrast median 0.0302 (subject medians 0.0207–0.0647); within-subject contrast CV 0.14 (range 0.09–0.31); seen rate by contrast quintile (mean of subjects) 0.37 / 0.44 / 0.48 / 0.51 / 0.58; objective questions 1880 (53.7 per subject), accuracy 0.688; trials without a seen/unseen response 10; photodiode delay median 39 ms (file medians 38–40); subjective RT median 0.93 s (10th percentile 0.74 s).

### noninformative  (34 subjects)

| sub | trials | present | catch | contrast min / median / max | contrast CV | seen rate | seen by contrast quintile 1→5 | seen on catch | objective n / acc | left / right | vert / horiz | 128s total / used / breaks | pd delay ms med (min–max) | seen missing | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | 400 | 360 | 40 | 0.0154 / 0.0247 / 0.0380 | 0.18 | 0.51 | 0.56 0.51 0.49 0.54 0.47 | 0.03 | 50 / 0.70 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 38 (30–60) | 0 |  |
| 03 | 400 | 360 | 40 | 0.0155 / 0.0336 / 0.0425 | 0.21 | 0.47 | 0.44 0.41 0.42 0.57 0.51 | 0.07 | 79 / 0.33 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–68) | 1 | 39 obj from column; 3 obj column≠trigger |
| 04 | 400 | 360 | 40 | 0.0311 / 0.0452 / 0.0547 | 0.10 | 0.46 | 0.44 0.35 0.50 0.51 0.49 | 0.07 | 49 / 0.71 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 | stray code 41 |
| 05 | 400 | 360 | 40 | 0.0181 / 0.0249 / 0.0362 | 0.11 | 0.50 | 0.51 0.39 0.61 0.46 0.54 | 0.15 | 57 / 0.70 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 06 | 400 | 360 | 40 | 0.0175 / 0.0275 / 0.0362 | 0.14 | 0.47 | 0.56 0.36 0.50 0.39 0.54 | 0.00 | 57 / 0.72 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–65) | 0 |  |
| 07 | 400 | 360 | 40 | 0.0296 / 0.0374 / 0.0522 | 0.13 | 0.48 | 0.43 0.38 0.58 0.49 0.51 | 0.07 | 52 / 0.79 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 08 | 400 | 360 | 40 | 0.0187 / 0.0297 / 0.0401 | 0.17 | 0.46 | 0.43 0.47 0.44 0.54 0.40 | 0.00 | 61 / 0.67 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–66) | 0 |  |
| 09 | 400 | 360 | 40 | 0.0170 / 0.0391 / 0.0510 | 0.16 | 0.47 | 0.46 0.49 0.40 0.49 0.50 | 0.05 | 62 / 0.77 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 10 | 400 | 360 | 40 | 0.0259 / 0.0396 / 0.0565 | 0.18 | 0.45 | 0.53 0.44 0.47 0.39 0.42 | 0.15 | 51 / 0.57 | 180 / 180 | 180 / 180 | 801 / 800 / 1 | 40 (30–66) | 0 |  |
| 11 | 400 | 360 | 40 | 0.0179 / 0.0270 / 0.0336 | 0.10 | 0.49 | 0.47 0.44 0.53 0.56 0.44 | 0.07 | 53 / 0.74 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–65) | 2 |  |
| 12 | 400 | 360 | 40 | 0.0201 / 0.0306 / 0.0377 | 0.10 | 0.49 | 0.40 0.47 0.53 0.51 0.53 | 0.03 | 57 / 0.79 | 180 / 180 | 180 / 180 | 801 / 800 / 1 | 40 (39–83) | 0 | stray code 255 |
| 13 | 400 | 360 | 40 | 0.0331 / 0.0480 / 0.0563 | 0.11 | 0.47 | 0.53 0.42 0.40 0.51 0.49 | 0.05 | 61 / 0.59 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 14 | 400 | 360 | 40 | 0.0163 / 0.0285 / 0.0466 | 0.26 | 0.41 | 0.39 0.38 0.39 0.38 0.54 | 0.03 | 55 / 0.71 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–64) | 0 |  |
| 15 | 400 | 360 | 40 | 0.0143 / 0.0251 / 0.0347 | 0.15 | 0.48 | 0.43 0.45 0.56 0.53 0.46 | 0.00 | 72 / 0.72 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–57) | 2 |  |
| 16 | 400 | 360 | 40 | 0.0299 / 0.0397 / 0.0481 | 0.12 | 0.46 | 0.45 0.51 0.42 0.48 0.46 | 0.03 | 56 / 0.79 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–65) | 4 | stray code 33 |
| 17 | 400 | 360 | 40 | 0.0166 / 0.0347 / 0.0483 | 0.19 | 0.42 | 0.36 0.44 0.42 0.46 0.43 | 0.00 | 51 / 0.65 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 18 | 400 | 360 | 40 | 0.0249 / 0.0439 / 0.0649 | 0.19 | 0.46 | 0.44 0.40 0.53 0.46 0.46 | 0.23 | 57 / 0.72 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–68) | 0 |  |
| 19 | 400 | 360 | 40 | 0.0152 / 0.0253 / 0.0400 | 0.19 | 0.54 | 0.44 0.54 0.62 0.57 0.50 | 0.05 | 54 / 0.61 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–64) | 0 |  |
| 20 | 400 | 360 | 40 | 0.0133 / 0.0272 / 0.0393 | 0.19 | 0.45 | 0.43 0.47 0.43 0.47 0.44 | 0.42 | 54 / 0.65 | 180 / 180 | 180 / 180 | 803 / 799 / 4 | 39 (30–64) | 0 |  |
| 21 | 398 | 358 | 40 | 0.0200 / 0.0317 / 0.0429 | 0.16 | 0.48 | 0.54 0.44 0.42 0.46 0.56 | 0.23 | 64 / 0.56 | 178 / 180 | 180 / 178 | 800 / 796 / 4 | 39 (30–60) | 0 | 398 trials |
| 22 | 400 | 360 | 40 | 0.0194 / 0.0284 / 0.0356 | 0.13 | 0.51 | 0.49 0.54 0.49 0.47 0.58 | 0.00 | 42 / 0.67 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–65) | 0 |  |
| 23 | 400 | 360 | 40 | 0.0256 / 0.0339 / 0.0444 | 0.12 | 0.47 | 0.47 0.46 0.50 0.39 0.51 | 0.00 | 55 / 0.67 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–72) | 0 |  |
| 24 | 400 | 360 | 40 | 0.0179 / 0.0254 / 0.0318 | 0.10 | 0.50 | 0.44 0.53 0.50 0.50 0.54 | 0.10 | 54 / 0.74 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–61) | 0 |  |
| 25 | 400 | 360 | 40 | 0.0342 / 0.0569 / 0.0938 | 0.23 | 0.37 | 0.44 0.35 0.40 0.31 0.35 | 0.05 | 56 / 0.59 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–57) | 0 |  |
| 26 | 400 | 360 | 40 | 0.0383 / 0.0534 / 0.0814 | 0.21 | 0.42 | 0.46 0.43 0.44 0.31 0.49 | 0.00 | 63 / 0.75 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–65) | 0 |  |
| 27 | 400 | 360 | 40 | 0.0121 / 0.0247 / 0.0309 | 0.12 | 0.46 | 0.38 0.42 0.43 0.67 0.43 | 0.12 | 54 / 0.70 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 28 | 400 | 360 | 40 | 0.0167 / 0.0249 / 0.0343 | 0.16 | 0.54 | 0.49 0.53 0.53 0.56 0.58 | 0.00 | 56 / 0.80 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–67) | 0 |  |
| 29 | 400 | 360 | 40 | 0.0160 / 0.0229 / 0.0325 | 0.11 | 0.50 | 0.53 0.60 0.42 0.44 0.53 | 0.07 | 59 / 0.71 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 30 | 400 | 360 | 40 | 0.0198 / 0.0296 / 0.0394 | 0.13 | 0.49 | 0.56 0.47 0.50 0.38 0.57 | 0.00 | 53 / 0.66 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 31 | 400 | 360 | 40 | 0.0172 / 0.0263 / 0.0356 | 0.11 | 0.51 | 0.53 0.47 0.51 0.54 0.50 | 0.05 | 57 / 0.61 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 40 (30–60) | 0 |  |
| 32 | 395 | 355 | 40 | 0.0266 / 0.0471 / 0.0563 | 0.14 | 0.46 | 0.32 0.44 0.46 0.52 0.55 | 0.12 | 56 / 0.66 | 178 / 177 | 178 / 177 | 794 / 790 / 4 | 39 (30–60) | 0 | 395 trials |
| 33 | 400 | 360 | 40 | 0.0196 / 0.0264 / 0.0328 | 0.10 | 0.47 | 0.42 0.54 0.33 0.58 0.50 | 0.00 | 68 / 0.75 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 34 | 400 | 360 | 40 | 0.0230 / 0.0294 / 0.0385 | 0.10 | 0.51 | 0.49 0.51 0.50 0.54 0.50 | 0.20 | 63 / 0.78 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 40 (30–73) | 0 |  |
| 35 | 400 | 360 | 40 | 0.0124 / 0.0346 / 0.0472 | 0.24 | 0.45 | 0.36 0.56 0.51 0.38 0.46 | 0.05 | 64 / 0.77 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 2 | 12 obj from column |

**noninformative totals:** 13593 trials, 12233 present, 1360 catch; seen rate 0.474 on present (subject range 0.37–0.54), 0.074 on catch (false alarms; range 0.00–0.42); contrast median 0.0303 (subject medians 0.0229–0.0569); within-subject contrast CV 0.14 (range 0.10–0.26); seen rate by contrast quintile (mean of subjects) 0.46 / 0.46 / 0.48 / 0.48 / 0.49; objective questions 1952 (57.4 per subject), accuracy 0.684; trials without a seen/unseen response 11; photodiode delay median 39 ms (file medians 38–40); cue→Gabor SOA 0.680–1.087 s; subjective RT median 0.94 s (10th percentile 0.74 s).

Validity classes (code digit 0 vs 1, assignment unknown — README D2): seen rate 0.474 vs 0.473 (paired across subjects: 15 of 34 have digit-0 > digit-1), median contrast 0.0332 vs 0.0332.

### informative  (35 subjects)

| sub | trials | present | catch | contrast min / median / max | contrast CV | seen rate | seen by contrast quintile 1→5 | seen on catch | objective n / acc | left / right | vert / horiz | 128s total / used / breaks | pd delay ms med (min–max) | seen missing | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 02 | 400 | 360 | 40 | 0.0334 / 0.0802 / 0.0967 | 0.18 | 0.36 | 0.21 0.32 0.33 0.42 0.54 | 0.00 | 48 / 0.79 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 40 (40–60) | 0 |  |
| 03 | 400 | 360 | 40 | 0.0093 / 0.0183 / 0.0269 | 0.15 | 0.49 | 0.36 0.32 0.51 0.64 0.64 | 0.12 | 54 / 0.59 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–63) | 0 |  |
| 04 | 400 | 360 | 40 | 0.0118 / 0.0192 / 0.0289 | 0.17 | 0.53 | 0.29 0.49 0.51 0.58 0.76 | 0.00 | 52 / 0.67 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 38 (30–60) | 1 |  |
| 05 | 400 | 360 | 40 | 0.0169 / 0.0283 / 0.0417 | 0.18 | 0.51 | 0.38 0.50 0.53 0.54 0.60 | 0.33 | 52 / 0.56 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 06 | 400 | 360 | 40 | 0.0218 / 0.0288 / 0.0373 | 0.11 | 0.53 | 0.36 0.50 0.51 0.64 0.62 | 0.03 | 55 / 0.76 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–62) | 0 |  |
| 07 | 400 | 360 | 40 | 0.0231 / 0.0329 / 0.0493 | 0.17 | 0.47 | 0.38 0.43 0.56 0.42 0.55 | 0.05 | 47 / 0.62 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 2 |  |
| 08 | 400 | 360 | 40 | 0.0064 / 0.0209 / 0.0350 | 0.25 | 0.49 | 0.28 0.51 0.46 0.56 0.62 | 0.03 | 50 / 0.72 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 09 | 400 | 360 | 40 | 0.0223 / 0.0354 / 0.0496 | 0.17 | 0.46 | 0.36 0.36 0.50 0.58 0.51 | 0.07 | 52 / 0.81 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 10 | 400 | 360 | 40 | 0.0227 / 0.0348 / 0.0517 | 0.15 | 0.55 | 0.40 0.56 0.57 0.61 0.62 | 0.03 | 51 / 0.65 | 180 / 180 | 180 / 180 | 801 / 800 / 1 | 40 (39–72) | 1 |  |
| 11 | 400 | 360 | 40 | -0.0135 / 0.0256 / 0.0370 | 0.53 | 0.45 | 0.24 0.32 0.42 0.70 0.57 | 0.15 | 52 / 0.69 | 180 / 180 | 180 / 180 | 806 / 800 / 6 | 39 (30–60) | 1 |  |
| 12 | 400 | 360 | 40 | 0.0112 / 0.0197 / 0.0330 | 0.18 | 0.51 | 0.40 0.36 0.47 0.64 0.68 | 0.07 | 44 / 0.68 | 180 / 180 | 180 / 180 | 801 / 800 / 1 | 40 (40–65) | 0 |  |
| 13 | 398 | 358 | 40 | 0.0285 / 0.0395 / 0.0511 | 0.11 | 0.48 | 0.36 0.42 0.51 0.46 0.64 | 0.03 | 48 / 0.62 | 178 / 180 | 179 / 179 | 800 / 796 / 4 | 39 (30–60) | 0 | 398 trials |
| 14 | 400 | 360 | 40 | 0.0103 / 0.0206 / 0.0375 | 0.19 | 0.52 | 0.38 0.38 0.53 0.60 0.71 | 0.10 | 50 / 0.68 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–62) | 0 |  |
| 15 | 400 | 360 | 40 | 0.0089 / 0.0133 / 0.0201 | 0.14 | 0.52 | 0.11 0.40 0.61 0.67 0.81 | 0.00 | 44 / 0.73 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 16 | 400 | 360 | 40 | 0.0244 / 0.0355 / 0.0544 | 0.13 | 0.44 | 0.29 0.51 0.49 0.38 0.56 | 0.07 | 43 / 0.70 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–63) | 0 |  |
| 17 | 400 | 360 | 40 | 0.0163 / 0.0268 / 0.0342 | 0.10 | 0.48 | 0.29 0.42 0.47 0.56 0.65 | 0.03 | 48 / 0.69 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 18 | 400 | 360 | 40 | 0.0325 / 0.0513 / 0.0618 | 0.13 | 0.46 | 0.33 0.46 0.53 0.46 0.53 | 0.07 | 47 / 0.68 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–63) | 0 |  |
| 19 | 400 | 360 | 40 | 0.0084 / 0.0154 / 0.0350 | 0.29 | 0.54 | 0.33 0.47 0.51 0.71 0.69 | 0.07 | 57 / 0.65 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 20 | 400 | 360 | 40 | 0.0197 / 0.0304 / 0.0384 | 0.12 | 0.51 | 0.47 0.44 0.50 0.54 0.58 | 0.15 | 47 / 0.53 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–64) | 0 |  |
| 21 | 399 | 359 | 40 | 0.0224 / 0.0316 / 0.0405 | 0.11 | 0.47 | 0.25 0.42 0.54 0.54 0.60 | 0.33 | 45 / 0.62 | 179 / 180 | 179 / 180 | 802 / 798 / 4 | 39 (30–73) | 0 | 399 trials |
| 22 | 400 | 360 | 40 | 0.0227 / 0.0319 / 0.0404 | 0.10 | 0.49 | 0.40 0.42 0.51 0.51 0.60 | 0.07 | 50 / 0.72 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–63) | 0 |  |
| 23 | 399 | 359 | 40 | 0.0229 / 0.0296 / 0.0512 | 0.19 | 0.55 | 0.38 0.53 0.62 0.58 0.62 | 0.07 | 52 / 0.63 | 180 / 179 | 179 / 180 | 801 / 797 / 4 | 39 (30–60) | 0 | 399 trials |
| 24 | 400 | 360 | 40 | 0.0134 / 0.0212 / 0.0270 | 0.13 | 0.48 | 0.26 0.40 0.49 0.62 0.64 | 0.05 | 46 / 0.72 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–62) | 0 |  |
| 25 | 400 | 360 | 40 | 0.0276 / 0.0498 / 0.0652 | 0.16 | 0.42 | 0.31 0.49 0.42 0.43 0.46 | 0.05 | 49 / 0.61 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–57) | 0 |  |
| 26 | 399 | 360 | 39 | 0.0215 / 0.0312 / 0.0417 | 0.13 | 0.48 | 0.39 0.42 0.46 0.51 0.61 | 0.03 | 43 / 0.72 | 180 / 180 | 180 / 180 | 802 / 798 / 4 | 39 (30–60) | 4 | 399 trials |
| 27 | 400 | 360 | 40 | 0.0151 / 0.0220 / 0.0295 | 0.11 | 0.48 | 0.20 0.41 0.48 0.61 0.67 | 0.15 | 47 / 0.68 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 53 |  |
| 28 | 400 | 360 | 40 | 0.0082 / 0.0144 / 0.0268 | 0.23 | 0.53 | 0.21 0.54 0.64 0.57 0.69 | 0.00 | 43 / 0.63 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 29 | 400 | 360 | 40 | 0.0163 / 0.0225 / 0.0371 | 0.14 | 0.55 | 0.47 0.47 0.44 0.67 0.71 | 0.15 | 50 / 0.78 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–56) | 0 |  |
| 30 | 400 | 360 | 40 | 0.0128 / 0.0243 / 0.0357 | 0.18 | 0.55 | 0.44 0.49 0.49 0.58 0.74 | 0.05 | 48 / 0.73 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 31 | 400 | 360 | 40 | 0.0117 / 0.0170 / 0.0315 | 0.18 | 0.54 | 0.25 0.42 0.54 0.72 0.75 | 0.15 | 44 / 0.80 | 180 / 180 | 180 / 180 | 804 / 800 / 4 | 40 (30–60) | 0 |  |
| 32 | 400 | 360 | 40 | 0.0148 / 0.0372 / 0.0472 | 0.16 | 0.47 | 0.34 0.40 0.46 0.57 0.59 | 0.17 | 43 / 0.70 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 40 (30–60) | 19 |  |
| 33 | 400 | 360 | 40 | 0.0190 / 0.0256 / 0.0347 | 0.11 | 0.50 | 0.31 0.35 0.62 0.53 0.71 | 0.05 | 42 / 0.76 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 34 | 400 | 360 | 40 | 0.0214 / 0.0313 / 0.0416 | 0.10 | 0.51 | 0.38 0.44 0.42 0.58 0.71 | 0.07 | 47 / 0.64 | 180 / 180 | 180 / 180 | 805 / 800 / 5 | 39 (30–60) | 0 |  |
| 35 | 398 | 358 | 40 | 0.0165 / 0.0351 / 0.0495 | 0.20 | 0.43 | 0.29 0.35 0.46 0.54 0.50 | 0.10 | 48 / 0.67 | 179 / 179 | 180 / 178 | 800 / 795 / 5 | 39 (30–63) | 0 | 398 trials |
| 36 | 400 | 360 | 40 | 0.0199 / 0.0269 / 0.0344 | 0.10 | 0.51 | 0.35 0.50 0.47 0.57 0.65 | 0.05 | 58 / 0.67 | 180 / 180 | 180 / 180 | 804 / 800 / 4 | 39 (30–60) | 0 |  |

**informative totals:** 13993 trials, 12594 present, 1399 catch; seen rate 0.493 on present (subject range 0.36–0.55), 0.084 on catch (false alarms; range 0.00–0.33); contrast median 0.0275 (subject medians 0.0133–0.0802); within-subject contrast CV 0.15 (range 0.10–0.53); seen rate by contrast quintile (mean of subjects) 0.33 / 0.43 / 0.50 / 0.57 / 0.63; objective questions 1696 (48.5 per subject), accuracy 0.682; trials without a seen/unseen response 81; photodiode delay median 39 ms (file medians 38–40); cue→Gabor SOA 0.680–1.505 s; subjective RT median 0.93 s (10th percentile 0.74 s).

## 3. Totals and cross-checks

* **41581 trials** in 104 recordings (37423 Gabor-present, 4158 catch); 41479 with a seen/unseen response, 5528 with an orientation response.
* Seen rate on present trials: nocue 0.474, noninformative 0.474, informative 0.493; false-alarm rate on catch trials 0.075 overall.
* Objective accuracy on present trials with an orientation response: 0.685 overall (seen 0.866, n = 2660; unseen 0.517, n = 2864).
* Behaviour source: the `subjective_r` column agrees with the 124/125 triggers wherever both exist (0 conflicts in 36286 trials); it is empty on 5193 stimulus rows in 21 recordings that do have the triggers, so `seen` is taken from the triggers (0 trials fall back to the column). `objective_r` vs the 121/122 triggers: 6 conflicts, 125 trials with a column value but no trigger (column used), 639 with a trigger but an empty column.
* Photodiode: every cue / Gabor / catch trigger in every file is immediately followed by a 128 (0 exceptions in 0 files, see notes); the remaining 128s are the start and break screens (489 in total, 0–7 per recording). Delay trigger→photodiode: Gabor/catch median 39 ms, range 30–83 ms; cue median 53 ms, range 40–151 ms (n = 27583). The correction shifts every epoch by the measured delay of its own trial; the 1024 Hz onsets in `events.tsv` reproduce the BDF Status channel exactly (checked in `load.py --verify`).
* Blocks: the paradigm has 4 blocks of 100 trials with a break screen between them, and the break screen fires an unpaired 128. In 97 recordings exactly three such interior 128s are present and define the blocks (block sizes 100;100;100;100, 95;100;100;100, 97;100;100;100, 98;100;100;100, 99;100;100;100); in the other 7 (sub-02 nocue (4 interior break 128s), sub-10 nocue (0 interior break 128s), sub-10 noninformative (0 interior break 128s), sub-10 informative (0 interior break 128s), sub-12 nocue (0 interior break 128s), sub-12 noninformative (0 interior break 128s), sub-12 informative (0 interior break 128s)) the blocks are ceil(trial_number / 100) (`block_source`).
* Trigger codes, all files: nocue/informative 11 12 21 22 31 32 (+ 1 2 cues in informative), noninformative 1 2 98 99 101–104 111–114; responses 121 122 124 125; photodiode 128. Stray single codes: sub-04 noninformative 41, sub-12 noninformative 255, sub-16 noninformative 33, sub-34 nocue 40 (one event each, ignored).

## 4. Does the contrast column behave as the staircase output of its own trial?

Per task, on present trials with a response (behaviour only): the per-subject correlation of contrast with the seen/unseen response, the same correlation with the contrast of neighbouring trials (a misaligned column would peak at a non-zero lag), and the staircase rule (the paper: contrast goes down after a run of seen responses and up after a run of unseen ones).

| task | corr(contrast, seen) per subject: median (min–max), n > 0 | mean corr at lag −2 / −1 / 0 / +1 / +2 | mean Δcontrast after an unseen / a seen trial |
|---|---|---|---|
| nocue | 0.141 (-0.052–0.312), 34 of 35 | 0.077 / 0.077 / 0.145 / 0.013 / 0.012 | +0.00054 / -0.00055 |
| noninformative | 0.031 (-0.072–0.129), 27 of 34 | 0.034 / 0.032 / 0.031 / 0.026 / 0.019 | +0.00006 / -0.00003 |
| informative | 0.217 (0.071–0.454), 35 of 35 | 0.102 / 0.106 / 0.213 / 0.047 / 0.025 | +0.00068 / -0.00067 |

In the **nocue** and **informative** tasks the column behaves as expected: the correlation peaks at lag 0, is positive in 34/35 and 35/35 subjects, and the staircase moves the contrast down after seen and up after unseen trials by ≈ 0.0005 per trial. In the **noninformative** task it does not: the lag-0 correlation is 0.031 (no lag is better), only 27 of 34 subjects are positive, and the contrast changes by only +0.00006 / -0.00003 after unseen / seen trials — a tenth of the other tasks. Split by the undocumented validity digit: digit 0 r = 0.059 (22/34 positive; seen by contrast quintile [0.447, 0.439, 0.475, 0.483, 0.526]), digit 1 r = 0.003 (17/34; [0.466, 0.488, 0.47, 0.483, 0.46]). Reading: the column in this task most likely records the staircase of the *cued* hemifield while the Gabor appeared in the other hemifield on the invalid half of the trials (which would make digit 0 the valid class), but even the digit-0 relation is a third of the other tasks' — **I can't determine the cause from the files**; the authors' presentation script would. **Consequence: the noninformative task has no usable trial-by-trial intensity covariate.**

## 5. What limits the planned analysis (PREREG_secondary_melcon.md)

1. **Catch trials are few: 40 per recording** (20 per side), of which some are 'seen' (false alarms, mean 0.08). A decoder trained on catch vs Gabor has at most 40 negative examples per subject × task — Sergent had ≈ 150 no-sound trials per session. Pooling the three tasks of a subject gives ≤ 120 catch trials, at the cost of mixing cue conditions.
2. **Contrast is a staircase output, not a designed level set**: within a recording it spans a factor of ≈ 2.1 (median max/min; range 1.6–5.4) with CV ≈ 0.14, and 56 recordings have CV < 0.15. The staircase concentrates trials near threshold — good for the mixture question, poor for anchoring a 'high-intensity' state: the top quintile is only modestly above the median (seen rate in quintile 5 ≈ 0.57 vs quintile 1 ≈ 0.38, nocue and informative; flat in noninformative, §4). 36 present trials carry a **negative** contrast (sub-11 informative; min -0.0135) — the staircase ran below zero; what was displayed on those trials cannot be determined from the files, and they are to be excluded.
2b. **The noninformative task's contrast column is not a usable intensity covariate** (§4): it neither predicts the seen/unseen response nor follows the staircase rule in that task. That task can enter a report-conditioned (seen vs unseen) analysis only.
3. **Missing recordings:** sub-01 informative, sub-02 noninformative, sub-35 nocue, sub-36 noninformative — so 32 subjects have all three tasks, 4 have two.
4. **Missing responses:** 102 trials without a seen/unseen response (sub-03 noninformative 1, sub-04 informative 1, sub-07 informative 2, sub-08 nocue 1, sub-10 informative 1, sub-11 noninformative 2, sub-11 informative 1, sub-13 nocue 1, sub-14 nocue 1, sub-15 nocue 1, sub-15 noninformative 2, sub-16 nocue 1, sub-16 noninformative 4, sub-18 nocue 1, sub-20 nocue 1, sub-24 nocue 1, sub-26 informative 4, sub-27 informative 53, sub-29 nocue 2, sub-32 informative 19, sub-35 noninformative 2).
5. **The subjective question appears 250–350 ms after Gabor offset** (paper) — i.e. 300–400 ms after Gabor onset — and is not marked by a trigger. Responses follow at a median 0.93 s after Gabor onset (10th percentile 0.74 s). Any window later than ≈ 300 ms contains the (jittered) question display and response preparation; Sergent's bifurcation interval (250–700 ms) is not cleanly available.
6. **No per-subject demographics** (participants.tsv mismatch, §1) and **no per-Gabor hemifield in the noninformative task** (README D2).
7. **The paper's own exclusions** (5–6 subjects per task for > 45 % ocular-artefact trials, 1 for persistent contrast differences, 1–2 for data loss) are not encoded in the dataset; the pre-registration must define its own artefact rule.
