"""Counterexamples for review only: fixed fixtures and mocked fits, no simulation or optimization."""
import sys
from types import SimpleNamespace
import numpy as np

sys.path.insert(0, '/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access')
import simulate as S
import analyze as A
import models as M

levels = np.array([0., 1., 2., 3., 4., 6., 8.])
fixed = SimpleNamespace(y=np.tile(np.linspace(-1,1,7),8)[:,None], k=np.tile(levels,8),
                        concept=np.repeat(np.arange(8),7), n_concepts=8)
S.make_dataset = lambda *args, **kwargs: fixed
original_scores = M.concept_scores
M.concept_scores = lambda name, theta, data, n_gh: np.zeros(data.n_concepts)
batches=[]
def fake_fit(name, data, n_gh, n_starts, rng, **kwargs):
    starts=M.starts_from_moments(name,data,n_starts,rng)
    batches.append(starts)
    runs=[dict(theta=np.zeros(8), loglik=10. if i==0 else 0., converged=True) for i in range(n_starts)]
    return M.FitResult(name,np.zeros(8),10.,True,n_starts,n_starts,runs=runs)
M.fit=fake_fit
r=S.expected_gain('M3L',np.zeros(8),seed=2026,graded=('M2K',))
assert len(batches)==2 and np.array_equal(batches[0][0],batches[1][0])
assert r['starts_at_best']['M2K']==2 and r['ref_reproduced']
print('Duplicate unjittered moment start accepted as two reference reproductions:',
      {'batch_sizes':[len(b) for b in batches], 'distinct_successful_initial_vectors':1,
       'reported_starts_at_best':r['starts_at_best'], 'ref_reproduced':r['ref_reproduced']})

C=64
ds=A.Dataset(np.zeros((C,1)),np.zeros(C),np.arange(C),np.repeat(np.arange(8),8),np.array([41]))
def fake_run(sub, cfg, seed, outer_folds=None, n_jobs=1):
    delta=np.ones((1,C)); delta[0,0]=np.nan
    return {'delta':{'selection':delta},'failed':False,'fit_seconds':0.}
A.run_dataset=fake_run
r=A.refit_bootstrap(ds,A.Config(),seed=1,n_rep=4)
assert r['usable'] and r['n_failed']==0 and r['ws']['lo']==1.
print('Partial nonfinite score without upstream failure flag silently averaged:',
      {'usable':r['usable'], 'n_failed':r['n_failed'], 'interval':r['ws']})

for R in (100,400,1000):
    print('Monte Carlo binomial SE', {'R':R,'at_coverage_0.90':(.9*.1/R)**.5,
                                    'at_coverage_0.95':(.95*.05/R)**.5})
print('Hypothetical miss probabilities, not estimated hit rates:',
      {'p_1_in_8_N32':(7/8)**32, 'p_1_in_16_N32':(15/16)**32})
