"""Explicit arithmetic for proposed sample sizes and budget gates; no remote work."""
from pathlib import Path
import json
from scipy.stats import beta,binom
OUT=Path(__file__).resolve().parent
Jnull=16;Jalt=14;J=Jnull+Jalt;Rcal=500;Rval=1000;Rnull=400
tests=J+Jnull+6
d=.04/tests
def lower(k,n):return 0. if k==0 else float(beta.ppf(d,k,n-k+1))
def upper(k,n):return 1. if k==n else float(beta.ppf(1-d,k+1,n-k))
cov_min=next(k for k in range(Rval+1) if lower(k,Rval)>=.90)
cov_null_min=next(k for k in range(Rnull+1) if lower(k,Rnull)>=.90)
power_min=next(k for k in range(Rval+1) if lower(k,Rval)>=.80)
size_max=max(k for k in range(Rnull+1) if upper(k,Rnull)<=.064)
cost_per=2.2;points=J*Rcal+Jnull*Rnull+Jalt*Rval
out=dict(null_settings=Jnull,alternative_settings=Jalt,calibration_per_setting=Rcal,null_validation_per_setting=Rnull,alternative_validation_per_setting=Rval,
         total_points=points,validation_bounds=tests,one_sided_bound_alpha=d,
         alternative_coverage_successes_min=cov_min,null_coverage_successes_min=cov_null_min,
         power_successes_min=power_min,false_or_unavailable_max=size_max,
         max_lengau_coreh_per_point=cost_per,base_coreh=points*cost_per,
         development_and_benchmark_reserve_coreh=6000,total_coreh=points*cost_per*1.2+6000,
         reserve_split_coreh={'boundary':2700,'gain_recertification':2000,'benchmark_and_fitter_checks':1000,'contingency':300},
         boundary_development_max_points=7*8+8*20+1000,boundary_development_cost_at_ceiling=(7*8+8*20+1000)*cost_per,
         csc_available_user_brief=7600,heal_available_user_brief=100000,combined_available=107600,
         original_one_refit_coreh=23.6,original_same_points_coreh=points*23.6,
         current_screen_full_cost=60*80*23.6,
         bootstrap_200_per_point_coreh=points*200*23.6,
         single_layer_to_35_layer_base_coreh=points*cost_per*35,
         mean_bound_log_factor=float(__import__('numpy').log(4/(.005/J))))
j=max(j for j in range(1,Rcal//2+1) if binom.cdf(j-1,Rcal,.5)<=(.005/J)/2)
out['median_reference_ranks']=[j,Rcal-j+1]
for p in (.98,.95):
    delta=.005/(2*J)
    k=next(k for k in range(1,Rcal+1) if binom.cdf(k-1,Rcal,p)>=1-delta)
    out[f'upper_tolerance_rank_p{p}']=k
(OUT/'repair_costs.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
