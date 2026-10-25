# S4 — gates and flags (DESIGN rev 7 §7.3–§7.6)

MANIFEST COMPLETE — the gates and flags below are final.
settings: W1 COMPLETE 100/100, W2 COMPLETE 100/100, W3 COMPLETE 100/100, W4 COMPLETE 100/100, O1 COMPLETE 100/100, O2 COMPLETE 100/100, O3 COMPLETE 100/100, O4 COMPLETE 100/100, O5 COMPLETE 100/100, T1 COMPLETE 50/50, T2 COMPLETE 50/50, T3 ABSENT 0/50, E1 COMPLETE 100/100
recovery: 

S4a: ε 0.011402454358678912; c₀ {'G': 6.651796161290416, 'B': 8.13516601307564}; λ {"E1": {"target": 0.01425306794834864, "status": "CERTIFIED", "mode": "hit", "lam": 1.0, "certified": {"mean": 0.01407064224689195, "lo": 0.012864875473635932, "hi": 0.01527640902014797, "n": 50, "sign": "POSITIVE", "level": 0.975}, "attempts": [{"lam": 1.0, "status": "CERTIFIED", "interval": {"mean": 0.01407064224689195, "lo": 0.012864875473635932, "hi": 0.01527640902014797, "n": 50, "sign": "POS

| setting | attempted/R | POSITIVE | NEGATIVE | UNRESOLVED | UNAVAILABLE | reference Δ₃ (mean [lo, hi]) |
|---|---|---|---|---|---|---|
| W1 | 100/100 | 0 | 83 | 17 | 0 | -0.00107 [-0.00114, -0.00100] NEGATIVE |
| W2 | 100/100 | 0 | 77 | 23 | 0 | -0.00117 [-0.00125, -0.00108] NEGATIVE |
| W3 | 100/100 | 0 | 76 | 24 | 0 | -0.00110 [-0.00118, -0.00101] NEGATIVE |
| W4 | 100/100 | 0 | 77 | 19 | 4 | -0.00111 [-0.00120, -0.00101] NEGATIVE |
| O1 | 100/100 | 0 | 82 | 18 | 0 | -0.00114 [-0.00123, -0.00105] NEGATIVE |
| O2 | 100/100 | 0 | 83 | 17 | 0 | -0.00110 [-0.00119, -0.00101] NEGATIVE |
| O3 | 100/100 | 0 | 73 | 27 | 0 | -0.00117 [-0.00127, -0.00106] NEGATIVE |
| O4 | 100/100 | 0 | 77 | 23 | 0 | -0.00124 [-0.00134, -0.00113] NEGATIVE |
| O5 | 100/100 | 12 | 0 | 88 | 0 | +0.00252 [+0.00203, +0.00301] POSITIVE |
| T1 | 50/50 | 49 | 0 | 1 | 0 | +0.01394 [+0.01261, +0.01527] POSITIVE |
| T2 | 50/50 | 0 | 0 | 0 | 50 | UNAVAILABLE |
| E1 | 100/100 | 99 | 0 | 1 | 0 | +0.01374 [+0.01299, +0.01448] POSITIVE |

gate (b) False: W1 0/100, W2 0/100, W3 0/100, W4 4/100, O1 0/100, O2 0/100, O3 0/100, O4 0/100, O5 12/100
gate (c) T1 {'passed': True, 'positive': 49, 'attempted': 50, 'lower': 0.9086018692803026, 'final': True}
gate (e) E1 {'passed': True, 'bounded': 0, 'attempted': 100, 'upper': 0.029513049607039925, 'final': True}
V2 False
T2 {'primaries': {'POSITIVE': 0, 'NEGATIVE': 0, 'UNRESOLVED': 0, 'UNAVAILABLE': 50}}, T3 {'primaries': {'POSITIVE': 0, 'NEGATIVE': 0, 'UNRESOLVED': 0, 'UNAVAILABLE': 0}}
rise {'W3': {'rise': False, 'diff': -0.01, 'lo': -0.054486196178705315, 'hi': 0.0278984707397118}, 'W4': {'rise': False, 'diff': -0.01, 'lo': -0.054486196178705315, 'hi': 0.0278984707397118}}; inherited calls {'W1': {'calls': 1, 'sets': 100}, 'W2': {'calls': 0, 'sets': 100}, 'W3': {'calls': 0, 'sets': 100}, 'W4': {'calls': 0, 'sets': 100}, 'O1': {'calls': 0, 'sets': 100}, 'O2': {'calls': 0, 'sets': 100}, 'O3': {'calls': 0, 'sets': 100}, 'O4': {'calls': 0, 'sets': 100}, 'O5': {'calls': 39, 'sets': 100}, 'T1': {'calls': 7, 'sets': 50}}
recovery flags: {"G": "NOT ADEQUATE", "B": "NOT ADEQUATE"}
  G R1: {"passed": false, "n_same": 13, "configs": [1, 5, 6, 7, 9, 10, 11, 12, 13, 14, 16, 17, 19]}
  G R2: {"passed": false, "settings": {"(0.0, 0.0)": {"k": 6, "n": 500, "rate": 0.012, "lower": 0.005238564057380191, "upper": 0.023546585483971323, "passed": true}, "(0.0, 'fitted')": {"k": 5, "n": 500, "rate": 0.01, "lower": 0.003948329589176697, "upper": 0.020910322942267072, "passed": true}, "(0.0, 1.0)
  G R3: {"passed": false, "settings": {"(0.0, 0.0)": {"k": 0, "n": 500, "rate": 0.0, "lower": 0.0, "upper": 0.005973551516349557, "passed": true}, "(0.0, 'fitted')": {"k": 0, "n": 500, "rate": 0.0, "lower": 0.0, "upper": 0.005973551516349557, "passed": true}, "(0.0, 1.0)": {"k": 0, "n": 500, "rate": 0.0, "l
  G R4: {"passed": false, "settings": {"(40.0, 'fitted')": {"k": 424, "n": 500, "rate": 0.848, "lower": 0.8190634640541874, "upper": 0.8738279241744018, "passed": false}, "(80.0, 'fitted')": {"k": 401, "n": 500, "rate": 0.802, "lower": 0.7703850313772271, "upper": 0.8309292042360374, "passed": false}}}
  G R5: {"passed": false, "detect": {"k": 14, "n": 500, "rate": 0.028, "lower": 0.017005477465531944, "upper": 0.04342734347331628}, "cover": {"k": 442, "n": 500, "rate": 0.884, "lower": 0.8577325859992218, "upper": 0.9068187182746217}}
  B R1: {"passed": false, "n_same": 11, "configs": [1, 7, 8, 9, 10, 11, 12, 14, 15, 17, 19]}
  B R2: {"passed": false, "settings": {"(0.0, 0.0)": {"k": 2, "n": 500, "rate": 0.004, "lower": 0.0007111818447311464, "upper": 0.012537605409672668, "passed": true}, "(0.0, 'fitted')": {"k": 3, "n": 500, "rate": 0.006, "lower": 0.0016373209819238429, "upper": 0.015433734876752685, "passed": true}, "(0.0, 1
  B R3: {"passed": false, "settings": {"(0.0, 0.0)": {"k": 0, "n": 500, "rate": 0.0, "lower": 0.0, "upper": 0.005973551516349557, "passed": true}, "(0.0, 'fitted')": {"k": 0, "n": 500, "rate": 0.0, "lower": 0.0, "upper": 0.005973551516349557, "passed": true}, "(0.0, 1.0)": {"k": 0, "n": 500, "rate": 0.0, "l
  B R4: {"passed": false, "settings": {"(40.0, 'fitted')": {"k": 396, "n": 500, "rate": 0.792, "lower": 0.7598896792142451, "upper": 0.8215154027283029, "passed": false}, "(80.0, 'fitted')": {"k": 363, "n": 500, "rate": 0.726, "lower": 0.6912471861969456, "upper": 0.7587516204812705, "passed": false}}}
  B R5: {"passed": false, "detect": {"k": 10, "n": 500, "rate": 0.02, "lower": 0.010889901301799896, "upper": 0.03368827233114448}, "cover": {"k": 432, "n": 500, "rate": 0.864, "lower": 0.8361766579655499, "upper": 0.8885649418472384}}
