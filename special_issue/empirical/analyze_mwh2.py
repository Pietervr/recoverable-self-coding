import bz2
import os
import statistics
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DIR = '/tmp/mwh'
files = sorted(f for f in os.listdir(DIR) if f.endswith('.tsv.bz2'))


def quarter(ts):
    y, m = ts[:4], ts[5:7]
    if not (y.isdigit() and m.isdigit() and 1 <= int(m) <= 12):
        return None
    return f"{y}Q{(int(m)-1)//3+1}"


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b))
    a, b = a[ok], b[ok]
    if len(a) < 4:
        return float('nan')
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


cells = []
filt_counts = {}
for fn in files:
    wiki = fn.split('.')[0]
    win = {}
    kept = 0
    with bz2.open(os.path.join(DIR, fn), 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            r = line.rstrip('\n').split('\t')
            if len(r) < 78 or r[2] != 'revision' or r[3] != 'create':
                continue
            if r[33] != '0' or r[15] != '':   # ns0 + non-bot
                continue
            q = quarter(r[4])
            if not q:
                continue
            kept += 1
            ed, reverted, secs, anon = r[9], r[-6] == 'true', r[-5], (r[6] == '')
            d = win.setdefault(q, {'e': 0, 'eds': set(), 'rev': 0, 'secs': [], 'anon': 0})
            d['e'] += 1
            if ed:
                d['eds'].add(ed)
            if anon:
                d['anon'] += 1
            if reverted:
                d['rev'] += 1
                if secs.isdigit():
                    d['secs'].append(int(secs))
    filt_counts[wiki] = kept
    for q, d in win.items():
        ne = len(d['eds'])
        if d['e'] >= 100 and d['rev'] >= 20 and ne >= 5:
            cells.append(dict(wiki=wiki, q=q, edits=d['e'], eds=ne, rev=d['rev'],
                              med_secs=statistics.median(d['secs']) if d['secs'] else float('nan'),
                              revfrac=d['rev'] / d['e'],
                              epepd=d['e'] / (ne * 91.0),
                              anonfrac=d['anon'] / d['e']))

print("ns0+non-bot edits kept per wiki:", {w: filt_counts[w] for w in sorted(filt_counts)})
print(f"qualifying (wiki,quarter) cells: {len(cells)}\n")

byw = defaultdict(list)
for c in cells:
    byw[c['wiki']].append(c)

print("WITHIN-WIKI Spearman (load = edits/editor/day):")
lat_s, cov_s = [], []
for w, cs in sorted(byw.items()):
    if len(cs) < 5:
        print(f"  {w:9s} n={len(cs):3d}  (too few windows)")
        continue
    load = [c['epepd'] for c in cs]
    sl = spearman(load, [c['med_secs'] for c in cs])
    sc = spearman(load, [c['revfrac'] for c in cs])
    sa = spearman(load, [c['anonfrac'] for c in cs])
    lat_s.append(sl); cov_s.append(sc)
    print(f"  {w:9s} n={len(cs):3d}  load~latency {sl:+.2f}   load~revfrac {sc:+.2f}   load~anonfrac {sa:+.2f}")
print(f"\nmedian within-wiki:  load~latency {np.nanmedian(lat_s):+.2f}   load~revfrac {np.nanmedian(cov_s):+.2f}")

# pooled plot colored by wiki
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
cmap = plt.get_cmap('tab10')
for i, (w, cs) in enumerate(sorted(byw.items())):
    if len(cs) < 5:
        continue
    load = np.array([c['epepd'] for c in cs])
    ax[0].scatter(load, np.array([c['med_secs'] for c in cs]) / 3600, s=16, alpha=0.6, color=cmap(i % 10), label=w)
    ax[1].scatter(load, np.array([c['revfrac'] for c in cs]) * 100, s=16, alpha=0.6, color=cmap(i % 10))
for a in ax:
    a.set_xscale('log'); a.set_xlabel('load: edits / editor / day  (CR →)')
ax[0].set_yscale('log'); ax[0].set_ylabel('median time-to-revert (hrs)')
ax[0].set_title('Recovery latency vs load (within-wiki, ns0, no bots)')
ax[1].set_ylabel('revert fraction (%)')
ax[1].set_title('Revert fraction vs load')
ax[0].legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig('/tmp/mwh_probe2.png', dpi=110, bbox_inches='tight')
print("saved /tmp/mwh_probe2.png")
