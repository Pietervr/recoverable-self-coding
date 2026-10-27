from pathlib import Path
OUT=Path(__file__).resolve().parent
s=(OUT/'repair_quadrature.py').read_text()
for old,new in [('repair_local.json','repair_primary_local.json'),("len(data['datasets'])==3","len(data['datasets'])==2"),('stratified_folds(family,5,seed)','stratified_folds(family,3,seed)'),('repair_quadrature.json','repair_primary_quadrature.json')]:
    assert s.count(old)==1,(old,s.count(old))
    s=s.replace(old,new)
(OUT/'repair_primary_quadrature.py').write_text(s)
