"""Final numerical/provenance checks, including exact finite-calibration arithmetic."""
from pathlib import Path
import json,hashlib,re
import numpy as np
from scipy.stats import binom,beta
from repair_procedure import calibrate,apply,median_bracket
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
c=json.loads((OUT/'repair_costs.json').read_text())
e=json.loads((OUT/'repair_evidence.json').read_text())
f=json.loads((OUT/'repair_finish.json').read_text())
J=c['null_settings']+c['alternative_settings'];R=c['calibration_per_setting'];j=c['median_reference_ranks'][0]
median_fail=2*binom.cdf(j-1,R,.5);tail_fail=.98**R
assert median_fail<=.005/J and tail_fail<=.005/(2*J)
assert c['total_points']==J*R+c['null_settings']*c['null_validation_per_setting']+c['alternative_settings']*c['alternative_validation_per_setting']
assert c['total_coreh']<=c['combined_available']
assert e['artifact']['target']=='median' and e['artifact']['cap']==.03
assert len(e['nulls'])==12 and len(e['alternatives'])==12
assert min(r['point_reference_inclusion'] for r in e['nulls'])>=.90
assert min(r['entire_reference_bracket_inclusion'] for r in e['nulls'])>=.90
assert sum(r['mixture_calls'] for r in e['nulls'])==0
middle=[e['alternatives'][i]['positive_calls'] for i in (1,4,7,10)]
assert sum(middle)==199
assert all(d['complete'] for d in f['datasets']) and sum(d['n_fits'] for d in f['datasets'])==135
assert f['model_sources_unchanged_since_local_import'] and f['as_run_source_reconstructed_matches']
assert f['quadrature']['max_absolute_joint_logq_error']<1e-3
pp=f['selected_primary']
assert hashlib.sha256((OUT/'repair_primary_local.py').read_bytes()).hexdigest()==pp['prototype_sha256']
assert len(pp['datasets'])==2 and all(d['complete'] for d in pp['datasets'])
assert sum(d['n_fits'] for d in pp['datasets'])==54 and sum(d['n_converged'] for d in pp['datasets'])==54
assert all(n==72 for d in pp['datasets'] for n in d['M2S_start_counts'])
assert pp['datasets'][0]['new_bounded']<0 and pp['datasets'][1]['new_bounded']>0
assert pp['datasets'][1]['old_bounded']<0
assert f['selected_primary_quadrature']['max_absolute_joint_logq_error']<1e-3
assert f['combined_cpu_with_interruption_and_check_allowance']<=7200
assert f['paired_starts']['max_training_gain']>.5 and not f['paired_starts']['development_accept_cold']
assert sum(c['reserve_split_coreh'].values())==6000
assert c['boundary_development_cost_at_ceiling']<=c['reserve_split_coreh']['boundary']
rejected=False
try:calibrate({'bad':np.array([0.,np.nan])},{'bad'})
except ValueError:rejected=True
assert rejected and apply(float('nan'),e['artifact'])['status']=='unavailable'
record=ROOT/'reviews/2026-10-27_method_repair_codex_record.md'
text=record.read_text();heads=re.findall(r'^## S([1-6])\.',text,re.M)
assert heads==list('123456')
assert not re.findall(r'\b[A-Z_]*TO_BE_FILLED[A-Z_]*\b',text)
out={'median_reference_failure_per_setting':float(median_fail),'tail_tolerance_failure_per_tail':float(tail_fail),
     'actual_union_bound_calibration_failure':float(J*median_fail+2*J*tail_fail),
     'declared_joint_calibration_validation_failure_budget':.01+.04,
     'min_null_development_point_reference_inclusion':min(r['point_reference_inclusion'] for r in e['nulls']),
     'min_null_development_entire_bracket_inclusion':min(r['entire_reference_bracket_inclusion'] for r in e['nulls']),
     'middle_gain_positive_count':sum(middle),'checks_passed':True,
     'selected_primary_local_summary':pp,
     'combined_cpu_with_interruption_and_check_allowance':f['combined_cpu_with_interruption_and_check_allowance'],
     'unresolved_record_placeholders':re.findall(r'\b[A-Z_]*TO_BE_FILLED[A-Z_]*\b',text),
     'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (record,OUT/'repair_procedure.py',OUT/'repair_evidence.py',OUT/'repair_costs.py')}}
if 'paired_starts' in f:out['paired_start_status']=f['paired_starts']
(OUT/'repair_verify.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
