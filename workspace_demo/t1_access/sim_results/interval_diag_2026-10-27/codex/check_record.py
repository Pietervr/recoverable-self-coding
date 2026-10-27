"""Consistency checks on this review's independent calculations and deliverable."""
from pathlib import Path
import json, re

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
r=json.loads((HERE/'reproduced.json').read_text())
a=json.loads((HERE/'additional.json').read_text())
assert len(r['settings'])==12
expected=[.935,.918,.819,.926,.894,.917,.848,.780,.216,.915,.885,.928]
expected_f1=[.948,.936,.849,.938,.921,.934,.877,.806,.223,.934,.902,.938]
for s,inc,f1 in zip(r['settings'],expected,expected_f1):
    assert s['n']==s['valid_reps']==1000
    assert s['original']==inc and s['F1']==f1
    assert s['miss_reference_below']+s['miss_reference_above']==round(1000*(1-inc))
    assert .998<s['median_claimed_over_exact_boot_se']<1.002
assert sum(s['F1']<.9 for s in r['settings'])==4
assert r['settings'][7]['miss_reference_above']==4
assert a['independent_bank']['inclusions']=={'mean':.178,'drop1_mean':.282,'median':.754}
assert r['input_sha256']==(HERE.parent/'input_sha256.txt').read_text().split()[0]
record=ROOT/'reviews/2026-10-27_interval_diagnosis_codex_record.md'
text=record.read_text()
assert re.findall(r'^## Q([1-6]) ',text,re.M)==list('123456')
assert len(re.findall(r'^\*\*Verdict:',text,re.M))==6
assert not any(line.rstrip()!=line for line in text.splitlines())
assert not re.search(r'TODO|PENDING|PLACEHOLDER',text)
print('PASS: 12 setting reproductions, miss counts, variance ratios, independent bank, input hash, six question verdicts, and record formatting.')
