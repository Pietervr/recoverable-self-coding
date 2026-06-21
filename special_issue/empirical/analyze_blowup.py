import json
import calendar
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPOS = [("public-apis", "public-apis"), ("MunGell", "awesome-for-beginners"), ("vercel", "next.js")]


def dt(iso):
    return datetime.strptime(iso[:19], '%Y-%m-%dT%H:%M:%S') if iso else None


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b)); a, b = a[ok], b[ok]
    if len(a) < 4:
        return float('nan')
    return float(np.corrcoef(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))[0, 1])


fig, axes = plt.subplots(len(REPOS), 1, figsize=(11, 3.3 * len(REPOS)))
for ax, (o, n) in zip(axes, REPOS):
    repo = f"{o}/{n}"
    prs = json.load(open(f'/tmp/gh/{o}__{n}.json'))
    items = []
    for p in prs:
        c = dt(p['createdAt']); cl = dt(p.get('closedAt')) or dt(p.get('mergedAt'))
        if c:
            items.append((c, cl))
    c0 = min(c for c, _ in items)
    months = []
    y, mn = c0.year, c0.month
    end = datetime(2026, 6, 1)
    while datetime(y, mn, 1) <= end:
        months.append((y, mn))
        mn += 1
        if mn > 12:
            mn = 1; y += 1
    xs, L, age = [], [], []
    for (yy, mm) in months:
        me = datetime(yy, mm, calendar.monthrange(yy, mm)[1], 23, 59, 59)
        openages = [(me - c).days for c, cl in items if c <= me and (cl is None or cl > me)]
        xs.append(datetime(yy, mm, 15))
        L.append(len(openages))
        age.append(np.median(openages) if openages else 0)
    xs = np.array(xs)
    ax.plot(xs, L, color='C2', lw=1.5, label='open-PR backlog L')
    ax.set_ylabel('open backlog L', color='C2')
    ax2 = ax.twinx()
    ax2.plot(xs, age, color='C3', lw=1.5, label='median age of open PRs (days)')
    ax2.set_ylabel('median open-PR age (days)', color='C3')
    ax.set_title(f"{repo}   —   Spearman(L, queue-age) = {spearman(L, age):+.2f}", fontsize=11)
    print(f"{repo:30s} backlog {L[0]:4d}->{L[-1]:5d}   median open-age {age[0]:.0f}->{age[-1]:.0f} days   "
          f"Spearman(L,age)={spearman(L, age):+.2f}")
fig.suptitle('Backlog blow-up in the wild: the queue stagnates as it grows (CR>1)', y=1.0)
fig.tight_layout()
fig.savefig('/tmp/gh_blowup.png', dpi=110, bbox_inches='tight')
print("saved /tmp/gh_blowup.png")
