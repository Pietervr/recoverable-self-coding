#!/usr/bin/env python3
"""SI empirical figure — Wikipedia: recovery coverage erodes under load
(leg 1, second substrate). Within each wiki, as editing load rises the fraction
of edits the community reverts (recovery coverage) falls -- recoverability
degrades while the system is still sub-critical. The signal is unanimous across
all 9 wikis. (Revert *latency* showed no consistent load relationship -- median
within-wiki Spearman +0.15, signs split -- so it is reported but not plotted.)

mediawiki_history dumps from MWH_DATA (default /tmp/mwh; re-pull via
figures/empirical/dl_mwh.py, snapshot 2026-05). Columns pinned in the README.
Filters: ns0 main-namespace article revisions, bot edits removed. A (wiki,
quarter) cell qualifies with >=100 edits, >=20 reverts, >=5 editors.
-> si_wikipedia.pdf
"""
import bz2
import os
import statistics
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = os.environ.get("MWH_DATA", "/tmp/mwh")
plt.rcParams.update({"font.size": 10, "axes.titlesize": 10, "legend.fontsize": 7})


def quarter(ts):
    y, m = ts[:4], ts[5:7]
    return f"{y}Q{(int(m) - 1) // 3 + 1}" if y.isdigit() and m.isdigit() and 1 <= int(m) <= 12 else None


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b)); a, b = a[ok], b[ok]
    return float(np.corrcoef(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))[0, 1]) if len(a) >= 4 else float('nan')


cells = []
for fn in sorted(f for f in os.listdir(DATA) if f.endswith('.tsv.bz2')):
    wiki = fn.split('.')[0]
    win = {}
    with bz2.open(os.path.join(DATA, fn), 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            r = line.rstrip('\n').split('\t')
            if len(r) < 78 or r[2] != 'revision' or r[3] != 'create':
                continue
            if r[33] != '0' or r[15] != '':                 # ns0 main-namespace, non-bot
                continue
            q = quarter(r[4])
            if not q:
                continue
            d = win.setdefault(q, {'e': 0, 'eds': set(), 'rev': 0, 'secs': []})
            d['e'] += 1
            if r[9]:
                d['eds'].add(r[9])
            if r[-6] == 'true':                              # identity-reverted
                d['rev'] += 1
                if r[-5].isdigit():
                    d['secs'].append(int(r[-5]))             # seconds-to-revert
    for q, d in win.items():
        ne = len(d['eds'])
        if d['e'] >= 100 and d['rev'] >= 20 and ne >= 5:
            cells.append(dict(wiki=wiki, load=d['e'] / (ne * 91.0),
                              revfrac=d['rev'] / d['e'],
                              med_hrs=(statistics.median(d['secs']) / 3600) if d['secs'] else float('nan')))

byw = defaultdict(list)
for c in cells:
    byw[c['wiki']].append(c)
byw = {w: cs for w, cs in byw.items() if len(cs) >= 5}

lat_s, cov_s = [], []
print("within-wiki Spearman (load = edits/editor/day):")
for w, cs in sorted(byw.items()):
    load = [c['load'] for c in cs]
    sl = spearman(load, [c['med_hrs'] for c in cs]); sc = spearman(load, [c['revfrac'] for c in cs])
    lat_s.append(sl); cov_s.append(sc)
    print(f"  {w:9s} n={len(cs):3d}  load~latency {sl:+.2f}   load~coverage {sc:+.2f}")
print(f"median within-wiki:  load~latency {np.nanmedian(lat_s):+.2f}   load~coverage {np.nanmedian(cov_s):+.2f}")

fig, ax = plt.subplots(1, 2, figsize=(11.2, 4.4))
cmap = plt.get_cmap('tab10')
for i, (w, cs) in enumerate(sorted(byw.items())):
    load = np.array([c['load'] for c in cs])
    ax[0].scatter(load, np.array([c['revfrac'] for c in cs]) * 100, s=16, alpha=0.6, color=cmap(i % 10), label=w)
ax[0].set_xscale('log'); ax[0].set_xlabel("editing load: edits / editor / day  (CR$\\rightarrow$)")
ax[0].set_ylabel("revert fraction = recovery coverage (%)")
ax[0].set_title(f"(a) coverage falls as load rises (within-wiki, median Spearman {np.nanmedian(cov_s):+.2f})")
ax[0].legend(ncol=2, loc='upper right')

order = sorted(byw, key=lambda w: spearman([c['load'] for c in byw[w]], [c['revfrac'] for c in byw[w]]))
vals = [spearman([c['load'] for c in byw[w]], [c['revfrac'] for c in byw[w]]) for w in order]
ax[1].barh(range(len(order)), vals, color="#C00000", alpha=0.85)
ax[1].set_yticks(range(len(order))); ax[1].set_yticklabels(order)
ax[1].axvline(np.nanmedian(cov_s), color='k', ls='--', lw=1, label=f"median {np.nanmedian(cov_s):+.2f}")
ax[1].set_xlabel("within-wiki Spearman(load, coverage)")
ax[1].set_title("(b) negative in all 9 wikis — robust, not a single-community artifact")
ax[1].legend(loc='lower left')
fig.suptitle("Wikipedia: recovery coverage erodes under load (ns0 articles, bots removed)", y=1.0)
fig.tight_layout()
fig.savefig("si_wikipedia.pdf", bbox_inches="tight")
print("wrote si_wikipedia.pdf")
