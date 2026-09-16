import ast
import hashlib
import json
import math
from pathlib import Path
import types

base = Path('/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access')
path = base / 'sim_results/gain_local_9b277df/gain_calibration_D4.json'
data = json.loads(path.read_text())
source = (base / 'simulate.py').read_text()
tree = ast.parse(source)
selected = {'gain_gate','validate_gain_entries','power_points','accepted_gain_artefact','file_digest'}
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in selected]
context = dict(np=types.SimpleNamespace(nan=math.nan, isfinite=math.isfinite), M=types.SimpleNamespace(FAMILY_X=('M3','M3H','M3V','M3L')), GAINS=(.003,.01,.03), REF_MIN_STARTS_AT_BEST=2, GATE_REL_SE=.2, GATE_REL_AGREE=.25, CHECK_N_PER_FAMILY=64, json=json, os=__import__('os'), hashlib=hashlib)
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(base/'simulate.py'), 'exec'), context)
entries = data['entries']
print('FILE', path, 'bytes',path.stat().st_size,'sha256',hashlib.sha256(path.read_bytes()).hexdigest())
print('TOP', json.dumps({k:v for k,v in data.items() if k!='entries'}, indent=2))
keys = ['generator','target','D','kwargs','scale','gain','gain_check','gain_check_se','calib_converged','check_converged','calib_ref_reproduced','check_ref_reproduced','calib_seed','calib_n_per_family','check_seed','check_n_per_family','note','revalidated','calib_starts_at_best','check_starts_at_best']
for entry in entries:
    print('ENTRY',json.dumps({**{k:entry.get(k) for k in keys}, 'gate_reason':context['gain_gate'](entry,float(entry['target']))},sort_keys=True))
print('VALIDATE_ALL',context['validate_gain_entries'](entries))
for target in (None,[.01]):
    points, extras=context['power_points'](str(path),targets=target)
    print('POWER_POINTS',json.dumps({'targets':target,'count':len(points),'points':points}))
print('ACCEPTED_OWN_HASH', context['accepted_gain_artefact'](str(path),None,4,data.get('code_hash')))
print('SOURCE_AST_FUNCTIONS', sorted(selected))
print('NO fitting, response simulation or revalidation computation was executed.')
