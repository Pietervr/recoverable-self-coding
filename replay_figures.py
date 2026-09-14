"""Render the archived article figures in a temporary directory, without fits.

The original figure scripts are unchanged. The human script's machine-specific
input path is replaced in memory with this archive's input directory.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='entropy-figure-replay-') as temp:
        figures = Path(temp) / 'figures'
        shutil.copytree(root / 'paper/figures', figures)
        for name in ['fig_human_bms.py', 'fig_t1_calibration.py']:
            path = figures / name
            code = path.read_text()
            if name == 'fig_human_bms.py':
                old = 'os.path.expanduser("~/Recoverable-Self-Coding/workspace_demo/sergent_port/figures")'
                assert code.count(old) == 1
                code = code.replace(old, repr(str(root / 'workspace_demo/sergent_port/figures')))
            exec(compile(code, str(path), 'exec'), {'__file__': str(path), '__name__': '__main__'})
        for name in ['human_bms_data.csv', 't1_calibration_D4_summary.csv']:
            assert (figures / name).read_bytes() == (root / 'paper/figures' / name).read_bytes(), name
        for name in ['human_bms.pdf', 't1_calibration_D4.pdf']:
            shutil.copy2(figures / name, args.out / name)
            print(name, hashlib.sha256((args.out / name).read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
