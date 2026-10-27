import os,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(OUT/'mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
d=json.loads((OUT/'repair_local.json').read_text())['datasets']
p=json.loads((OUT/'repair_primary_local.json').read_text())['datasets']
assert len(p)==2 and all(x['complete'] for x in p)
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,rows,title in [(axes[0],d,'Initial: five folds, eight cold starts'),(axes[1],p,'Selected: three folds, expanded M2S starts')]:
    x=list(range(len(rows)))
    ax.plot(x,[r['old']['bounded_point_cap03'] for r in rows],'o-',label='Without M3S')
    ax.plot(x,[r['with_m3s']['bounded_point_cap03'] for r in rows],'o-',label='With M3S')
    ax.axhline(0,color='black',lw=.8)
    ax.set(xticks=x,xticklabels=[r['generator'] for r in rows],ylim=(-.032,.032),ylabel='Bounded concept-average contrast',title=title)
    ax.legend(fontsize=8)
fig.suptitle('Local development: one dataset per setting; point signs are not interval decisions')
fig.savefig(OUT/'repair_local.png',dpi=170)
