import json
import os
import calendar
from collections import defaultdict
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

GH = '/tmp/gh'
files = sorted(f for f in os.listdir(GH) if f.endswith('.json'))


def dt(iso):
    return datetime.strptime(iso[:19], '%Y-%m-%dT%H:%M:%S') if iso else None


def ym(iso):
    return iso[:7] if iso else None


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b))
    a, b = a[ok], b[ok]
    if len(a) < 4:
        return float('nan')
    return float(np.corrcoef(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))[0, 1])


import statistics
cells = []
byrepo = defaultdict(list)
for fn in files:
    repo = fn[:-5].replace('__', '/')
    prs = json.load(open(os.path.join(GH, fn)))
    months = defaultdict(lambda: dict(opened=0, closed=0, merged=0, lat=[]))
    cre, clo = [], []
    for p in prs:
        c, m, cl = p['createdAt'], p.get('mergedAt'), p.get('closedAt')
        if ym(c):
            months[ym(c)]['opened'] += 1
        clm = ym(cl) or ym(m)
        if clm:
            months[clm]['closed'] += 1
        if p.get('merged') and m:
            d = months[ym(m)]
            d['merged'] += 1
            lat = (dt(m) - dt(c)).total_seconds() / 86400.0   # sojourn, days
            d['lat'].append(lat)
        if dt(c):
            cre.append(dt(c))
        if (dt(cl) or dt(m)):
            clo.append(dt(cl) or dt(m))
    cre.sort(); clo.sort()
    for mo in sorted(months.keys()):
        y, mn = int(mo[:4]), int(mo[5:7])
        me = datetime(y, mn, calendar.monthrange(y, mn)[1], 23, 59, 59)
        backlog = sum(1 for x in cre if x <= me) - sum(1 for x in clo if x <= me)
        d = months[mo]
        if d['merged'] >= 15 and d['closed'] >= 10 and d['lat']:
            cell = dict(repo=repo, mo=mo, merged=d['merged'], backlog=max(0, backlog),
                        cr=d['opened'] / max(1, d['closed']),       # utilization rho
                        med_lat=statistics.median(d['lat']))         # sojourn (days)
            cells.append(cell)
            byrepo[repo].append(cell)

print(f"repos: {list(byrepo)} | total (repo,month) cells: {len(cells)}\n")
print("WITHIN-REPO Spearman (the queueing law):")
for repo, cs in sorted(byrepo.items()):
    bl = [c['backlog'] for c in cs]; lat = [c['med_lat'] for c in cs]; cr = [c['cr'] for c in cs]
    print(f"  {repo:16s} n={len(cs):3d}  CR~latency {spearman(cr, lat):+.2f}   "
          f"backlog~latency {spearman(bl, lat):+.2f}   CR~backlog {spearman(cr, bl):+.2f}")

fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
cmap = plt.get_cmap('tab10')
for i, (repo, cs) in enumerate(sorted(byrepo.items())):
    ax[0].scatter([c['cr'] for c in cs], [c['med_lat'] for c in cs], s=18, alpha=0.6, color=cmap(i % 10), label=repo)
    ax[1].scatter([c['backlog'] for c in cs], [c['med_lat'] for c in cs], s=18, alpha=0.6, color=cmap(i % 10))
ax[0].set_xlabel('utilization  rho = opened/closed  (CR →)')
ax[0].set_ylabel('median PR merge latency (days)')
ax[0].set_yscale('log'); ax[0].set_title('Sojourn vs utilization (W ~ 1/(1-rho)?)')
ax[0].legend(fontsize=8)
ax[1].set_xlabel('open-PR backlog L')
ax[1].set_ylabel('median PR merge latency (days)')
ax[1].set_yscale('log'); ax[1].set_title('Sojourn vs backlog (Little: W ~ L)')
fig.tight_layout()
fig.savefig('/tmp/gh_probe.png', dpi=110, bbox_inches='tight')
print("\nsaved /tmp/gh_probe.png")
