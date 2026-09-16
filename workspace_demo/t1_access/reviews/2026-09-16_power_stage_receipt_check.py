"""Verify one saved-reply delivery and complete native Read receipts; no model code."""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
from pathlib import Path

USER_ROOT = Path('/Users/pietervanrooyen')
RSC = USER_ROOT / 'Recoverable-Self-Coding'
UNIMOG = USER_ROOT / 'Unimog-Projects'
RECEIVER = '9c0d76b5-e296-4739-bb14-ed95dfe64a09'
TRANSCRIPT = USER_ROOT / '.claude/projects/-Users-pietervanrooyen-Unimog-Projects' / (RECEIVER + '.jsonl')
CHAT = USER_ROOT / '.local/share/xs/chat.jsonl'
RECORD = 'workspace_demo/t1_access/reviews/2026-09-16_power_stage_codex_record.md'
REPLY = 'prompts/2026-09-16_codex_r052_power_stage_reply.txt'
OUTPUT = Path(__file__).with_name('2026-09-16_power_stage_receipt.json')


def json_rows(path):
    for number, line in enumerate(path.open(), 1):
        try:
            yield number, json.loads(line)
        except json.JSONDecodeError:
            # A concurrently appended final line may be incomplete.
            continue


def text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(x.get('text', '') for x in content if isinstance(x, dict))
    return ''


def verify():
    paths = [(RSC, RECORD, 'fe34a17'), (UNIMOG, REPLY, 'de2cb38d')]
    expected = {}
    report = {'receiver_uuid': RECEIVER, 'native_transcript': str(TRANSCRIPT), 'files': {}}
    for repo, relative, commit in paths:
        path = repo / relative
        data = path.read_bytes()
        committed = subprocess.check_output(['git', '-C', str(repo), 'show', commit + ':' + relative])
        assert data == committed, str(path) + ': working bytes differ from reviewed commit'
        expected[str(path)] = data.decode().splitlines()
        report['files'][str(path)] = {'commit': commit, 'bytes': len(data), 'lines': len(data.decode().splitlines()),
                                    'sha256': hashlib.sha256(data).hexdigest(), 'committed_bytes_unchanged': True,
                                    'reads': [], 'received_lines': {}, 'complete_unchanged': False}
    reply = (UNIMOG / REPLY).read_text()
    deliveries = [{'chat_line': n, **r} for n, r in json_rows(CHAT)
                  if r.get('from') == 'codex:01a0abca' and r.get('to') == 'claude:Entropy SI'
                  and r.get('text', '').rstrip('\n') == reply.rstrip('\n')]
    assert len(deliveries) == 1, f'Expected one exact saved-reply delivery, got {len(deliveries)}'
    delivery = deliveries[0]
    report['delivery'] = {k: delivery.get(k) for k in ('chat_line', 'ts', 'from', 'to', 'delivered')}
    report['delivery']['exact_saved_text_except_terminal_newline'] = True
    report['delivery']['matching_count'] = len(deliveries)
    calls = {}
    for n, row in json_rows(TRANSCRIPT):
        stamp = row.get('timestamp')
        if not stamp or datetime.datetime.fromisoformat(stamp.replace('Z', '+00:00')) < datetime.datetime.fromisoformat(delivery['ts']):
            continue
        blocks = row.get('message', {}).get('content', [])
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'tool_use' and block.get('name') == 'Read':
                args = block.get('input', {})
                path = str(Path(args.get('file_path', '')).expanduser())
                if path in expected:
                    calls[block['id']] = {'path': path, 'tool_use_id': block['id'], 'call_native_line': n,
                                         'call_timestamp': row.get('timestamp'), 'input': args}
            if block.get('type') == 'tool_result' and block.get('tool_use_id') in calls:
                call = calls[block['tool_use_id']]
                entry = report['files'][call['path']]
                assert not block.get('is_error'), 'Native Read failed'
                content = text_content(block.get('content'))
                numbered = {}
                for text_line in content.splitlines():
                    match = re.match(r'^[ \t]*(\d+)(?:→|\t)(.*)$', text_line)
                    if match:
                        numbered[int(match[1])] = match[2]
                entry['received_lines'].update(numbered)
                entry['reads'].append({**call, 'result_native_line': n, 'result_timestamp': row.get('timestamp'),
                                       'numbered_lines': len(numbered),
                                       'numbered_range': [min(numbered), max(numbered)] if numbered else None,
                                       'tool_result_sha256': hashlib.sha256(content.encode()).hexdigest()})
    for path, entry in report['files'].items():
        lines = entry.pop('received_lines')
        target = expected[path]
        terminal = len(target) + 1
        entry['native_terminal_empty_line'] = terminal in lines and lines[terminal] == '' and Path(path).read_bytes().endswith(b'\n')
        if entry['native_terminal_empty_line']:
            del lines[terminal]
        indices = set(range(1, len(target) + 1))
        entry['complete_unchanged'] = set(lines) == indices and all(lines[n] == target[n - 1] for n in indices)
        entry['received_unique_line_count'] = len(lines)
        entry['comparison'] = 'Every numbered native Read line equals the committed file line; Read framing excluded.'
    report['complete'] = all(x['complete_unchanged'] for x in report['files'].values())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    result = verify()
    if args.save:
        assert result['complete'], 'Cannot save closure before both complete native receipts exist'
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
