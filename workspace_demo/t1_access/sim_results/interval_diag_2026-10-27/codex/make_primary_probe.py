"""Exact checked transformations of the initial scratch prototype for the selected design."""
from pathlib import Path
OUT=Path(__file__).resolve().parent
s=(OUT/'repair_local.py').read_text()
changes={
"ROOT=Path(__file__).resolve().parents[3]":"ROOT=Path(__file__).resolve().parents[3]",
"OUT=Path(__file__).resolve().parent":"OUT=Path(__file__).resolve().parent\ninitial_cpu=json.loads((OUT/'repair_local.json').read_text())['cpu_seconds']\npaired_cpu=sum(json.loads(p.read_text())['cpu_seconds'] for p in OUT.glob('repair_starts_setting[0-3].json'))\nfit_budget_cpu=7200-initial_cpu-paired_cpu-450",
"repair_local_plan.json":"repair_primary_plan.json",
"repair_local.json').write_text":"repair_primary_local.json').write_text",
"[('M2H',{'tau':.5},271001),('M2S',{'omega':1.},271002),('M3S',{'omega':1.,'sep':2.},271003)]":"[('M2H',{'tau':.5},271004),('M3S',{'omega':1.,'sep':2.},271005)]",
"time.process_time()-begin_cpu>6500":"time.process_time()-begin_cpu>fit_budget_cpu-120",
"A.stratified_folds(family,5,seed)":"A.stratified_folds(family,3,seed)",
"time.process_time()-begin_cpu>6960":"time.process_time()-begin_cpu>fit_budget_cpu-120",
"fit=M.fit(m,tr,n_starts=8,rng=np.random.default_rng([seed,f,j]))":"fit=M.fit(m,tr,n_starts=8,rng=np.random.default_rng([seed,f,j]), policy_key=(M.SIZE_OUTER,f,(seed,41)) if m=='M2S' else None, policy={'M2S':((64,.25),)} if m=='M2S' else None)",
"res={'plan'":"res={'budget_cpu_seconds':fit_budget_cpu,'initial_cpu_seconds':initial_cpu,'completed_paired_cpu_seconds':paired_cpu,'plan'"
}
for old,new in changes.items():
    assert s.count(old)==1,(old,s.count(old))
    s=s.replace(old,new)
(OUT/'repair_primary_local.py').write_text(s)
print('Wrote selected-design probe')
