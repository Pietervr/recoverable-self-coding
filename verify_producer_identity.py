"""Verify historical settings hashes by imports only; never run scientific jobs."""
import dataclasses
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    if len(sys.argv) > 1:
        label, expected = sys.argv[1:]
        folder = ROOT / 'producers' / label / 'workspace_demo/t1_access'
        sys.path.insert(0, str(folder))
        import analyze as A
        import simulate as S
        cfg = A.Config(n_starts_inner=4)
        actual = S.config_hash(cfg, 4, [41], 2026)
        assert actual == expected, (label, actual, expected)
        print(json.dumps(dict(label=label, expected=expected, actual=actual,
                              config=dataclasses.asdict(cfg), D=4, layers=[41], seed=2026)))
        return
    result = []
    for label, expected in [('calibration_52267ec', 'b29215469af9'), ('gain_9b277df', 'd77c3ecc161e')]:
        out = subprocess.check_output([sys.executable, str(Path(__file__).resolve()), label, expected], timeout=30)
        result.append(json.loads(out))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
