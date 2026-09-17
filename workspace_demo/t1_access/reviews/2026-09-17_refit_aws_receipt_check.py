"""Verify the single row 17 notification and complete native file receipts.

Reads local evidence only. Does not import model code, send messages, or inspect
simulation outputs. --save writes the receipt beside this script after all checks.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/Users/pietervanrooyen')
RSC = ROOT / 'Recoverable-Self-Coding'
UNIMOG = ROOT / 'Unimog-Projects'
RECEIVER = 'ced0f2b1-fb5f-48d8-b54c-3a1e91f50686'
TRANSCRIPT = ROOT / '.claude/projects/-Users-pietervanrooyen-Unimog-Projects' / (RECEIVER + '.jsonl')
CHAT = ROOT / '.local/share/xs/chat.jsonl'
RECORD = 'workspace_demo/t1_access/reviews/2026-09-17_refit_aws_codex_record.md'
REPLY = 'prompts/2026-09-17_codex_r052_refit_aws_reply.txt'
OUTPUT = Path(__file__).with_name('2026-09-17_refit_aws_receipt.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_rows(path):
    lines = path.read_bytes().splitlines(keepends=True)
    for number, line in enumerate(lines, 1):
        try:
            yield number, json.loads(line)
        except json.JSONDecodeError:
            # Only an incomplete concurrent final append may be ignored.
            if number != len(lines) or line.endswith(b'\n'):
                raise


def timestamp(value):
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))


def verify():
    report = {'receiver_uuid': RECEIVER, 'native_transcript': str(TRANSCRIPT), 'files': {}}
    specifications = [
        (RSC, RECORD, '052f156', '2f1211a4be4adf0fac56eeef707f3957cfcfffef1f14f198d60c8f7f322ade42', 12463, 191,
         [('toolu_015cQeLtNGbUmfrV4z1jB3AR', 1, 95,
           "sed -n '1,95p' ~/Recoverable-Self-Coding/" + RECORD + ' | fold -w 175'),
          ('toolu_01MRk71hWkezEfd4hvWFq7uq', 96, 191,
           "sed -n '96,191p' ~/Recoverable-Self-Coding/" + RECORD + ' | fold -w 175')]),
        (UNIMOG, REPLY, 'c3ae4939', '48bf569fcefe4810315e41b9b0c66a064302d6506810c06dfb7afb98b6cba082', 4373, 16,
         [('toolu_01AwknNTs1kc9pobNYyuL12D', 1, 16, 'cat ' + str(UNIMOG / REPLY) + ' 2>&1')]),
    ]
    deliveries = [(n, row) for n, row in json_rows(CHAT)
                  if row.get('from') == 'codex:01a0adb6'
                  and row.get('to') == 'claude:R052 Entropy paper'
                  and row.get('text', '').startswith('Row 17 review complete:')
                  and RECORD in row.get('text', '') and REPLY in row.get('text', '')]
    assert len(deliveries) == 1, 'Expected exactly one matching notification'
    chat_line, delivery = deliveries[0]
    assert delivery['ts'] == '2026-09-17T12:45:36-07:00'
    assert delivery['delivered'] == 'inbox' and delivery['project'] == str(UNIMOG)
    report['notification'] = {'chat_line': chat_line, 'matching_count': len(deliveries),
                              **{k: delivery[k] for k in ('ts', 'from', 'to', 'delivered')},
                              'text_sha256': sha(delivery['text'].encode()),
                              'kind': 'Read-file notification; the complete reply was read separately.'}

    wanted = {item[0] for spec in specifications for item in spec[-1]}
    calls, results, notifications, disposition = {}, {}, [], []
    for number, row in json_rows(TRANSCRIPT):
        stamp = row.get('timestamp')
        if not stamp or timestamp(stamp) < timestamp(delivery['ts']):
            continue
        message = row.get('message') or {}
        content = message.get('content', [])
        blocks = [{'type': 'text', 'text': content}] if isinstance(content, str) else content
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if block.get('type') == 'tool_use' and block.get('id') in wanted:
                assert block['id'] not in calls
                calls[block['id']] = (number, stamp, block)
            elif block.get('type') == 'tool_result' and block.get('tool_use_id') in wanted:
                assert block['tool_use_id'] not in results
                results[block['tool_use_id']] = (number, stamp, block)
            elif block.get('type') == 'text':
                text = block.get('text', '')
                if message.get('role') == 'user' and '<event>12:45:36 codex:01a0adb6 → claude:R052 Entropy paper: Row 17 review complete:' in text:
                    notifications.append({'native_line': number, 'timestamp': stamp, 'text_sha256': sha(text.encode()),
                                          'notification_is_truncated': '...(truncated)' in text})
                if message.get('role') == 'assistant':
                    for marker in ("Codex's record is correct throughout", 'let the Mac finish, spend nothing here'):
                        if marker in text:
                            disposition.append({'native_line': number, 'timestamp': stamp, 'marker': marker,
                                                'text_sha256': sha(text.encode())})
    assert len(notifications) == 1, 'Expected one native monitor notification'
    assert set(calls) == set(results) == wanted, 'Missing native call or result'
    report['notification']['native_receipts'] = notifications

    for repo, relative, commit, digest, size, line_count, reads in specifications:
        path = repo / relative
        data = path.read_bytes()
        assert (sha(data), len(data), len(data.splitlines())) == (digest, size, line_count)
        committed = subprocess.check_output(['git', '-C', str(repo), 'show', commit + ':' + relative])
        head = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + relative])
        assert data == committed == head, str(path) + ': committed payload changed'
        source_lines = data.splitlines(keepends=True)
        chunks, receipts, next_line = [], [], 1
        for tool_id, first, last, command in reads:
            call_line, call_stamp, call = calls[tool_id]
            result_line, result_stamp, result = results[tool_id]
            assert call['name'] == 'Bash' and call['input']['command'] == command
            assert not result.get('is_error') and result_line > call_line
            assert first == next_line and last <= len(source_lines), 'Gap or overlap in receipt ranges'
            content = result['content']
            assert isinstance(content, str)
            expected = b''.join(source_lines[first - 1:last])
            assert expected.endswith(b'\n')
            actual = content.encode()
            assert actual == expected[:-1], 'Native payload differs from source beyond one terminal newline'
            # No unfolding or interior whitespace normalization: all bytes match.
            chunks.append(actual + b'\n')
            next_line = last + 1
            receipts.append({'tool_use_id': tool_id, 'call_native_line': call_line, 'call_timestamp': call_stamp,
                             'command': command, 'result_native_line': result_line, 'result_timestamp': result_stamp,
                             'source_line_range': [first, last], 'tool_result_bytes': len(actual),
                             'tool_result_sha256': sha(actual), 'complete_chunk_match': True})
        reconstructed = b''.join(chunks)
        assert next_line == line_count + 1 and reconstructed == data
        report['files'][str(path)] = {'commit': commit, 'bytes': size, 'lines': line_count, 'sha256': digest,
                                     'committed_and_head_bytes_unchanged': True, 'reads': receipts,
                                     'received_unique_line_count': line_count, 'reconstructed_sha256': sha(reconstructed),
                                     'comparison': 'Exact bytes; restore only the one terminal newline omitted by each Bash result.',
                                     'complete_unchanged': True}
    assert len(disposition) == 2, 'Expected acceptance and subsequent no-revision disposition'
    report['claude_disposition'] = {'native_evidence': disposition, 'ledger_commit': '0b7c1e53',
                                    'work_item_commit': 'a2fea7d2',
                                    'meaning': 'Claude accepts the review, holds row 17, and proposes no revision; let the Mac finish.',
                                    'scope': 'Receipt and disposition only; no new scientific recheck or timing validation.'}
    report['earlier_single_payload_check'] = 'Found reply only; the record arrived in two consecutive Bash results. That earlier limitation is retained.'
    report['complete'] = True
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    result = verify()
    if args.save:
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
