import json
import calendar
import bisect
import statistics
from collections import defaultdict
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FLOOD = [("public-apis", "public-apis"),
         ("EddieHubCommunity", "BioDrop"),
         ("MunGell", "awesome-for-beginners")]


def dt(iso):
    return datetime.strptime(iso[:19], '%Y-%m-%dT%H:%M:%S') if iso else None


def ym(iso):
    return iso[:7] if iso else None


fig, axes = plt.subplots(len(FLOOD), 1, figsize=(11, 3.1 * len(FLOOD)))
summary = []
for ax, (o, n) in zip(axes, FLOOD):
    repo = f"{o}/{n}"
    prs = json.load(open(f'/tmp/gh/{o}__{n}.json'))
    M = defaultdict(lambda: dict(op=0, mg=0, cu=0, cl=0, res=[]))
    cre, clo = [], []
    for p in prs:
        c, m, cl, merged = p['createdAt'], p.get('mergedAt'), p.get('closedAt'), p.get('merged')
        if ym(c):
            M[ym(c)]['op'] += 1
        clm = ym(cl) or ym(m)
        if clm:
            M[clm]['cl'] += 1
            M[clm]['mg' if merged else 'cu'] += 1
            res = dt(cl) or dt(m)
            if res and dt(c):
                M[clm]['res'].append((res - dt(c)).total_seconds() / 86400)
        if dt(c):
            cre.append(dt(c))
        if (dt(cl) or dt(m)):
            clo.append(dt(cl) or dt(m))
    cre.sort(); clo.sort()
    months = sorted(M)
    xs, opened, backlog, isoct = [], [], [], []
    for mo in months:
        y, mn = int(mo[:4]), int(mo[5:7])
        me = datetime(y, mn, calendar.monthrange(y, mn)[1], 23, 59, 59)
        bl = bisect.bisect_right(cre, me) - bisect.bisect_right(clo, me)
        xs.append(datetime(y, mn, 15)); opened.append(M[mo]['op'])
        backlog.append(max(0, bl)); isoct.append(mn == 10)
    xs = np.array(xs); op = np.array(opened); io = np.array(isoct)
    ax.plot(xs, opened, color='C0', lw=1.1, label='PRs opened / mo')
    ax.scatter(xs[io], op[io], color='red', s=34, zorder=5, label='October (Hacktoberfest)')
    ax2 = ax.twinx()
    ax2.plot(xs, backlog, color='C2', lw=1.4, alpha=0.85)
    ax.set_title(repo, fontsize=11)
    ax.set_ylabel('PRs opened / mo'); ax2.set_ylabel('open backlog', color='C2')
    ax.legend(loc='upper left', fontsize=7)
    bl_arr = np.array(backlog)
    summary.append((repo,
                    np.median(op[io]) if io.any() else 0,
                    np.median(op[~io]),
                    np.median(bl_arr[io]) if io.any() else 0,
                    np.median(bl_arr[~io])))
fig.suptitle('Overload episodes: Hacktoberfest PR floods vs the queue', y=1.0)
fig.tight_layout()
fig.savefig('/tmp/gh_episode.png', dpi=110, bbox_inches='tight')

print("repo                          medOct_open  medNonOct_open  arr_x   medOct_backlog  medNonOct_backlog  bl_x")
for repo, mo, mn, mob, mnb in summary:
    print(f"{repo:28s}  {mo:9.0f}  {mn:13.0f}  {mo/max(1,mn):4.1f}x  {mob:13.0f}  {mnb:16.0f}  {mob/max(1,mnb):4.1f}x")
print("saved /tmp/gh_episode.png")
