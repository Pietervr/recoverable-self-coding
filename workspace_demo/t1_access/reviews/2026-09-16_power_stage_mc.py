"""Exact binomial arithmetic and source pins for the bounded power review.

Standard library only. No simulated responses, numerical pipeline imports,
fits, gain recalibration, job operations, or saved-row reanalysis.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess


def cdf(k, n, p):
    return math.fsum(math.comb(n, j) * p**j * (1-p)**(n-j)
                     for j in range(k+1))


def tail(k, n, p):
    return math.fsum(math.comb(n, j) * p**j * (1-p)**(n-j)
                     for j in range(k, n+1))


def lower(k, n, alpha):
    if k == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo+hi)/2
        if tail(k, n, mid) < alpha:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


def upper(k, n, alpha):
    if k == n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo+hi)/2
        if cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


base = Path(__file__).resolve().parents[1]
rsc = base.parents[1]
unimog = Path('/Users/pietervanrooyen/Unimog-Projects')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def pin(repo, rel):
    raw = (repo/rel).read_bytes()
    return {'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw), 'lines': len(raw.splitlines()),
            'last_commit': git(repo, 'log', '-1', '--format=%H', '--', rel),
            'tracked_change': git(repo, 'status', '--porcelain', '--', rel)}


rsc_paths = ['workspace_demo/t1_access/' + p for p in (
    'simulate.py', 'analyze.py', 'models.py', 'probe_refit.py',
    'PREREGISTRATION_T1_model.md',
    'sim_results/gain_local_9b277df/gain_calibration_D4.json',
    'reviews/2026-09-16_power_stage_codex_brief.md',
    'reviews/2026-09-16_power_stage_gate_check.py',
    'reviews/2026-09-16_power_stage_gate_check.output.txt')]
unimog_paths = ['papers/adaptive_agency_special_issue/sections/' + p + '.tex'
                 for p in ('introduction', 'methods', 'results', 'discussion', 'transfer')]
unimog_paths += ['project_knowledge/rsc_publication_strategy.md',
                  'project_knowledge/rsc_t1_simulation_design.md']
examples = []
for n, k in [(25,20), (50,0), (50,35), (50,40), (50,45), (50,46), (50,47), (50,50)]:
    p = k/n
    examples.append({'n': n, 'detections': k, 'rate': p,
                     'mcse': math.sqrt(p*(1-p)/n),
                     'cp_two_sided_95': [lower(k,n,.025),upper(k,n,.025)],
                     'cp_lower_one_sided_95': lower(k,n,.05),
                     'cp_lower_bonferroni_four_one_sided_95': lower(k,n,.05/4)})
nist = [lower(4,20,.05), upper(4,20,.05)]
assert abs(nist[0] - .071354) < 1e-6 and abs(nist[1] - .401029) < 1e-6
assert abs(upper(0,50,.05) - (1-.05**(1/50))) < 1e-13
out = {
    'purpose': 'Planning arithmetic; examples are hypothetical, not measured power.',
    'time_utc': datetime.now(timezone.utc).isoformat(),
    'rsc_head': git(rsc, 'rev-parse', 'HEAD'),
    'unimog_head': git(unimog, 'rev-parse', 'HEAD'),
    'examples': examples,
    'mcse_at_p08': {str(n): math.sqrt(.8*.2/n) for n in (25,50,100,200,1000)},
    'normal_95_halfwidth_005_at_p08_n': math.ceil(1.959963984540054**2*.8*.2/.05**2),
    'minimum_k_of_50_for_lower_above_08': {
        'individual_one_sided_95': next(k for k in range(51) if lower(k,50,.05) > .8),
        'bonferroni_four_one_sided_95': next(k for k in range(51) if lower(k,50,.05/4) > .8)},
    'pool_example_rates': [.4,1,1,1],
    'pool_example_equal_weight_mean': .85,
    'nist_90_interval_4_of_20_check': nist,
    'gain_chronology': [git(rsc, 'show', '-s', '--format=%H %aI %s', c)
                        for c in ('4677e41','3ca9304')],
    'rsc_sources': [pin(rsc,p) for p in rsc_paths],
    'unimog_sources': [pin(unimog,p) for p in unimog_paths],
    'calculation_source': 'https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm',
    'no_scientific_run': True}
print(json.dumps(out, indent=2))
