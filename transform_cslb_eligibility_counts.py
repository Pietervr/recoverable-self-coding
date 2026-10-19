"""Counts-only public transformation of the concept-bank eligibility summary (R052, Codex release-gate ruling 1).

The producer, workspace_demo/t1_access/stimuli/norms_bank/cslb_eligibility.py at recoverable-self-coding commit
2f77020c0a22ade2f25c4aaa61e36cc88eb6fa18, writes cslb_eligibility.json. Beside the counts, that file lists the eligible
concept (cue) names of every family under results.<source>.<threshold|tier>.concepts. The study snapshot is released
under CC BY 4.0 and excludes CSLB-derived material, so the original file is NOT archived. This script builds a
TRANSFORMED summary, cslb_eligibility_counts.json, from an explicit allowlist:

  kept     aggregate counts per family and their totals; the feasibility/allocation values (integers, booleans and
           the two fixed reason strings of clean_eligibility.feasible_allocation); the per-source bookkeeping counts;
           the design statement and the CSLB licence notice exactly as written by the producer; the 26 September
           baseline counts; the SHA-256 digests of the norm files, tokenizer and scripts the producer read.
  omitted  every concept/cue list (results.*.*.concepts) and any field not named in the allowlist. The per-concept
           feature record (cslb_eligibility_detail.json) was never committed and is not read here.

Every value is type-checked; an unexpected key, type or string fails the transformation instead of passing through.
The script prints only key paths and counts, never a name. The output cannot be recomputed from the snapshot: the
producer reads the CSLB and McRae norm files and token_counts.json, which are not redistributed.

  python3 transform_cslb_eligibility_counts.py --out <path>      reads the original from the local RSC clone

validate(obj) is imported by prepare_public_source_v2.py, which re-checks the archived file before every commit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

RSC = Path('/Users/pietervanrooyen/Recoverable-Self-Coding')
COMMIT = '2f77020c0a22ade2f25c4aaa61e36cc88eb6fa18'
SOURCE_PATH = 'workspace_demo/t1_access/stimuli/norms_bank/cslb_eligibility.json'
OUT_NAME = 'cslb_eligibility_counts.json'
FAMILIES = ['animals', 'foods', 'vehicles']
SPLITS = ['BACKGROUND', 'CAL', 'CONF', 'PILOT']
SOURCES = ['mcrae', 'mcrae+cslb_pf5', 'mcrae+cslb_pf3', 'mcrae+cslb_pf2', 'mcrae+cslb_pf5_merged']
RESULT_KEYS = [f'>={t}|{tier}' for t in (10, 12) for tier in ('raw', 'protocol')]
REASONS = {'a family cannot reserve a background and appear in all three splits',
           'no joint integer allocation satisfies the half bounds and capacities'}
DIGEST_FILES = {'CONCS_FEATS_concstats_brm.txt', 'CSLB_Property_Norms_V1.1.zip', 'norms.dat'}
BOOKKEEPING = {'pf_min': int, 'merged': bool, 'cslb_labels': int, 'overlap': int, 'exact_new': int,
               'exact_new_single_word': int, 'features_added_to_overlap': int}
ALLOCATION_SCALARS = {'available': int, 'needed': int, 'deficit': int, 'feasible': bool, 'reason': str}
# Fixed text written by the producer (cslb_eligibility.py at 2f77020c); copied only if it is exactly this.
DESIGN = ('three families (animals, foods, vehicles); needed CONF 64 + CAL 12 + PILOT 12 + one BACKGROUND '
          'per family = 91 (owner, 13 Oct 2026); usable-feature minimum 10 (12 also reported); single-token E1')
LICENCE = ('CSLB Norms: Copyright (c) and database right 2012-15 Centre for Speech, Language and the '
           'Brain (CSLB), Department of Psychology, University of Cambridge. All rights reserved. '
           'Devereux, Tyler, Geertzen & Randall (2014), BRM 46(4) 1119-1127, doi:10.3758/s13428-013-0420-4. '
           'CSLB, the original collectors and the funders bear no responsibility for this analysis.')
HEX64 = re.compile(r'[0-9a-f]{64}')
OMITTED = ['results.<source>.<threshold|tier>.concepts: the eligible concept (cue) names of each family',
           'any other field not in the allowlist (none present in the original at 2f77020c)']
RECOMPUTATION = ('Not recomputable from this snapshot: cslb_eligibility.py reads the CSLB Property Norms V1.1, the '
                 'McRae et al. (2005) norms and token_counts.json, none of which is redistributed. The digests above '
                 'identify the norm files the run read, so a separately obtained copy can be checked against them.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _check(cond, where):
    if not cond:
        raise ValueError(f'allowlist violation at {where}')


def allocation(a, where):
    out = {}
    for key, value in a.items():
        if key in ALLOCATION_SCALARS:
            kind = ALLOCATION_SCALARS[key]
            _check(_int(value) if kind is int else isinstance(value, kind), f'{where}.{key}')
            if key == 'reason':
                _check(value in REASONS, f'{where}.reason')
            out[key] = value
        elif key in ('witness', 'proportional'):
            _check(isinstance(value, dict), f'{where}.{key}')
            block = {}
            for k, v in value.items():
                if k == 'ok':
                    _check(isinstance(v, bool), f'{where}.{key}.ok')
                else:
                    _check(k in SPLITS and isinstance(v, list) and len(v) == 3 and all(_int(e) for e in v),
                           f'{where}.{key}.{k}')
                block[k] = v
            out[key] = block
        else:
            raise ValueError(f'allowlist violation at {where}.{key}: unknown field')
    return out


def transform(original):
    """Return the counts-only summary. Raises on any field outside the allowlist."""
    keep_top = {'design', 'baseline_2026_09_26', 'tokenizer_json_sha256', 'script_sha256', 'usable_sha256',
                'clean_eligibility_sha256', 'licence_note', 'sources', 'results'}
    _check(set(original) == keep_top, 'top-level keys')
    _check(original['design'] == DESIGN, 'design')
    _check(original['licence_note'] == LICENCE, 'licence_note')
    for k in ('tokenizer_json_sha256', 'script_sha256', 'usable_sha256', 'clean_eligibility_sha256'):
        _check(isinstance(original[k], str) and HEX64.fullmatch(original[k]), k)
    base = original['baseline_2026_09_26']
    _check(set(base) == {'rsc', 'mcrae_raw_ge12', 'pooled_upper_bound_no_feature_filter'}, 'baseline keys')
    _check(re.fullmatch(r'[0-9a-f]{7,40}', base['rsc']) is not None, 'baseline.rsc')
    for k in ('mcrae_raw_ge12', 'pooled_upper_bound_no_feature_filter'):
        _check(isinstance(base[k], list) and len(base[k]) == 4 and all(_int(e) for e in base[k]), f'baseline.{k}')
    _check(list(original['sources']) == SOURCES and list(original['results']) == SOURCES, 'source names')
    sources = {}
    for name, s in original['sources'].items():
        _check(set(s) == {'digests', 'bookkeeping'}, f'sources.{name}')
        _check(set(s['digests']) <= DIGEST_FILES and all(isinstance(v, str) and HEX64.fullmatch(v)
                                                          for v in s['digests'].values()), f'sources.{name}.digests')
        for k, v in s['bookkeeping'].items():
            _check(k in BOOKKEEPING and (_int(v) if BOOKKEEPING[k] is int else isinstance(v, bool)),
                   f'sources.{name}.bookkeeping.{k}')
        sources[name] = dict(digests=dict(s['digests']), bookkeeping=dict(s['bookkeeping']))
    results, omitted_lists = {}, 0
    for name, block in original['results'].items():
        _check(list(block) == RESULT_KEYS, f'results.{name} keys')
        results[name] = {}
        for key, r in block.items():
            where = f'results.{name}.{key}'
            _check(set(r) == {'counts', 'total', 'concepts', 'allocation'}, where)
            _check(list(r['counts']) == FAMILIES and all(_int(v) for v in r['counts'].values()), f'{where}.counts')
            _check(_int(r['total']) and r['total'] == sum(r['counts'].values()), f'{where}.total')
            # The omitted lists must agree with the kept counts; only their lengths are read.
            _check(list(r['concepts']) == FAMILIES and all(len(r['concepts'][f]) == r['counts'][f] for f in FAMILIES),
                   f'{where}.concepts lengths')
            omitted_lists += len(r['concepts'])
            results[name][key] = dict(counts=dict(r['counts']), total=r['total'],
                                      allocation=allocation(r['allocation'], f'{where}.allocation'))
    kept = {k: original[k] for k in ('design', 'baseline_2026_09_26', 'tokenizer_json_sha256', 'script_sha256',
                                     'usable_sha256', 'clean_eligibility_sha256', 'licence_note')}
    return dict(kept, sources=sources, results=results), omitted_lists


def build(original_bytes, script_bytes):
    original = json.loads(original_bytes)
    body, omitted_lists = transform(original)
    out = {
        'transformed_summary': OUT_NAME,
        'note': ('Counts-only public transformation of cslb_eligibility.json, which is not archived because it lists '
                 'eligible concept names. Every number below is copied unchanged from that file.'),
        'transformation': dict(script='transform_cslb_eligibility_counts.py', script_sha256=sha(script_bytes),
                               rule='explicit allowlist of aggregate counts, allocation values, fixed labels and digests',
                               omitted=OMITTED, concept_lists_omitted=omitted_lists),
        'source': dict(repository='recoverable-self-coding', commit=COMMIT, path=SOURCE_PATH,
                       sha256=sha(original_bytes), bytes=len(original_bytes), archived=False),
        'recomputation': RECOMPUTATION,
        **body,
    }
    validate(out)
    return (json.dumps(out, indent=1, ensure_ascii=False) + '\n').encode()


def validate(obj):
    """Check a transformed summary: allowlisted keys only, no list of strings anywhere, no 'concepts' key."""
    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                _check(k != 'concepts', f'{path}.concepts present')
                walk(v, f'{path}.{k}')
        elif isinstance(x, list):
            _check(path.endswith('.omitted') or all(_int(e) for e in x), f'{path}: non-integer list')
    walk(obj, '')
    _check(obj.get('transformed_summary') == OUT_NAME and obj['source']['archived'] is False, 'header')
    body = {k: obj[k] for k in ('design', 'baseline_2026_09_26', 'tokenizer_json_sha256', 'script_sha256',
                                'usable_sha256', 'clean_eligibility_sha256', 'licence_note', 'sources', 'results')}
    for name, block in body['results'].items():
        for key, r in block.items():
            _check(set(r) == {'counts', 'total', 'allocation'}, f'results.{name}.{key}')
            allocation(r['allocation'], f'results.{name}.{key}.allocation')
    _check(obj['design'] == DESIGN and obj['licence_note'] == LICENCE, 'fixed labels')
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    a = p.parse_args()
    original = subprocess.check_output(['git', '-C', str(RSC), 'show', f'{COMMIT}:{SOURCE_PATH}'])
    data = build(original, Path(__file__).read_bytes())
    Path(a.out).write_bytes(data)
    obj = json.loads(data)
    print(f'{OUT_NAME}: {len(data)} bytes, sha256 {sha(data)}; concept lists omitted: '
          f'{obj["transformation"]["concept_lists_omitted"]}; sources {len(obj["sources"])}; '
          f'result blocks {sum(len(b) for b in obj["results"].values())}')


if __name__ == '__main__':
    main()
