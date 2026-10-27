from pathlib import Path
import json
from scipy.stats import t, binom
r=json.loads((Path(__file__).parent/'reproduced.json').read_text())
print('SHA256',r['input_sha256'])
print('fields',r['fields'])
print('resampling',r['resampling'])
for s in r['settings']:
    print(s['setting'], 'theta/mcse',s['reference'],s['reference_mcse'],
          'G',s['selected_G'],'X',s['selected_X'],
          'sd/exactSE',s['point_sd']/s['median_exact_unbiased_stratified_se'],
          'basic/F1/normal',s['basic'],s['basic_F1'],s['normal_exact_stratified'],
          'cov_share',s['covariance_cross_term']/s['replicate_variance'],
          'dom_hit/miss',s['dominance_median_hits'],s['dominance_median_misses'],
          'rounding',s['point_vs_delta_mean_max_error'])
print('t7',t.ppf(.975,7),'t7/normal',t.ppf(.975,7)/1.96,
      'stop',[(p,binom.cdf(48,60,p)) for p in (.75,.8,.85,.9,.95)])
