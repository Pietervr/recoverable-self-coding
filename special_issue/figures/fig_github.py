#!/usr/bin/env python3
"""SI empirical figure — GitHub: the in-the-wild boundary crossing (leg 3) and
the queue machinery (leg 1). PR-lifecycle JSON from GH_DATA (default /tmp/gh;
re-pull via figures/empirical/gh_fetch*.py, snapshot 2026-06-17). -> si_github.pdf
"""
import json
import os
import calendar
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = os.environ.get("GH_DATA", "/tmp/gh")
plt.rcParams.update({"font.size": 10, "axes.titlesize": 10, "legend.fontsize": 7})


def dt(iso):
    return datetime.strptime(iso[:19], '%Y-%m-%dT%H:%M:%S') if iso else None


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b)); a, b = a[ok], b[ok]
    return float(np.corrcoef(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))[0, 1]) if len(a) >= 4 else float('nan')


def monthly(prs):
    items = [(dt(p['createdAt']), dt(p.get('closedAt')) or dt(p.get('mergedAt'))) for p in prs]
    items = [(c, cl) for c, cl in items if c]
    c0 = min(c for c, _ in items)
    y, mn, end = c0.year, c0.month, datetime(2026, 6, 1)
    xs, L, age = [], [], []
    while datetime(y, mn, 1) <= end:
        me = datetime(y, mn, calendar.monthrange(y, mn)[1], 23, 59, 59)
        oa = [(me - c).days for c, cl in items if c <= me and (cl is None or cl > me)]
        xs.append(datetime(y, mn, 15)); L.append(len(oa)); age.append(np.median(oa) if oa else 0)
        mn += 1
        if mn > 12:
            mn = 1; y += 1
    return np.array(xs), np.array(L, float), np.array(age, float)


repos = {}
for fn in sorted(os.listdir(DATA)):
    if fn.endswith('.json'):
        repos[fn[:-5].replace('__', '/')] = monthly(json.load(open(os.path.join(DATA, fn))))

fig, ax = plt.subplots(1, 2, figsize=(11.2, 4.3))
xs, L, age = repos['public-apis/public-apis']
ax[0].plot(xs, L, color="#2E7D32", lw=1.7)
ax[0].set_ylabel(r"open-PR backlog $L$", color="#2E7D32"); ax[0].tick_params(axis='y', colors="#2E7D32")
a2 = ax[0].twinx(); a2.plot(xs, age, color="#C00000", lw=1.7)
a2.set_ylabel("median open-PR age (days)", color="#C00000"); a2.tick_params(axis='y', colors="#C00000")
ax[0].set_title("(a) public-apis: the queue blows up and stagnates (CR>1)")

# the three repos that crossed the boundary (analyze_blowup.py) vs the rest
CROSSERS = {'public-apis/public-apis', 'vercel/next.js', 'MunGell/awesome-for-beginners'}
cross_c = {'public-apis/public-apis': '#C00000', 'vercel/next.js': '#E8702A', 'MunGell/awesome-for-beginners': '#B5179E'}
calm_c = {'pallets/flask': '#1f77b4', 'cli/cli': '#2E7D32', 'EddieHubCommunity/BioDrop': '#7f9bb3'}
cross_rho, calm_rho = [], []
for repo, (xs, L, age) in sorted(repos.items()):
    m = (L > 0) & (age > 0)
    crossed = repo in CROSSERS
    ax[1].scatter(L[m], age[m], s=13, alpha=0.55,
                  color=(cross_c if crossed else calm_c)[repo],
                  marker=('o' if crossed else '^'), label=repo.split('/')[-1])
    rho_w = spearman(L[m], age[m])
    (cross_rho if crossed else calm_rho).append(rho_w)
    print(f"  within-repo Spearman(L, age)  {repo:35s} {rho_w:+.2f}  final-month L={L[-1]:.0f}")
ax[1].set_xscale('log'); ax[1].set_yscale('log')
ax[1].set_xlabel(r"open-PR backlog $L$"); ax[1].set_ylabel("median open-PR age (days)")
ax[1].set_title("(b) age couples to size only past the boundary")
ax[1].text(0.04, 0.96, f"crossed (●): median Spearman {np.median(cross_rho):+.2f}\n"
                       f"triaged (▲): median Spearman {np.median(calm_rho):+.2f}",
           transform=ax[1].transAxes, va='top', fontsize=8,
           bbox=dict(boxstyle='round', fc='white', ec='0.7', alpha=0.9))
ax[1].legend(ncol=2, loc='lower right')
fig.suptitle("GitHub: PR review queues — machinery in-regime and the boundary crossing in the wild", y=1.0)
fig.tight_layout()
fig.savefig("si_github.pdf", bbox_inches="tight")
print(f"wrote si_github.pdf; crossed median {np.median(cross_rho):+.2f}, triaged median {np.median(calm_rho):+.2f}")
