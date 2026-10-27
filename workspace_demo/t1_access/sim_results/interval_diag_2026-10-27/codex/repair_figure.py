"""Use the Mac system Python's matplotlib, not the fitting venv."""
import os
from pathlib import Path
OUT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(OUT/'mpl-cache')
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
d=json.loads((OUT/'repair_summary.json').read_text())['figure_data']
e=json.loads((OUT/'repair_evidence.json').read_text())
d['null_assessment_inclusion']=[r['point_reference_inclusion'] for r in e['nulls']]
d['sensitivity_positive_fraction']=[r['positive_calls']/r['n'] for r in e['alternatives']]
fig,ax=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for key,label in [('original_inclusion','Original: original mean target'),('F1_inclusion','Strata correction: original target'),('null_assessment_inclusion','Bounded ensemble: median target')]:
    ax[0].plot(range(12),d[key],'o-',label=label)
ax[0].axhline(.9,color='black',ls='--',lw=.8)
ax[0].set(xticks=range(12),xticklabels=d['null_names'],ylim=(0,1.04),ylabel='Reference inclusion',title='Graded development rows')
ax[0].legend(fontsize=7,loc='lower left')
ax[1].bar(range(12),d['sensitivity_positive_fraction'])
ax[1].set(ylim=(0,1.04),xticks=range(12),xticklabels=d['alternative_names'],ylabel='Positive bounded intervals',title='Sensitivity development rows; 50 per cell')
ax[1].axhline(.8,color='black',ls='--',lw=.8)
fig.suptitle('Post hoc development screens; no fresh-seed validation')
fig.savefig(OUT/'repair_development.png',dpi=170)
