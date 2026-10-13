"""Ten clauses per concept (owner, 13 October 2026; R052 handoff 1970a4cc): the selection rule and the declared counts.

    python3 -m unittest test_select_features.py        (the build venv, for norms_parse's imports)
"""

import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "stimuli" / "norms_bank"))
import select_features as S  # noqa: E402


def norms(n: int) -> SimpleNamespace:
    """One concept 'x' with n features f00..; feature fNN is shared by NN+1 concepts (so f00 is the rarest)."""
    feats = {f"f{i:02d}" for i in range(n)}
    return SimpleNamespace(features={"x": feats}, sharing={f: int(f[1:]) + 1 for f in feats})


class Selection(unittest.TestCase):
    def test_exactly_ten_from_a_concept_with_more(self):
        for n in (10, 11, 14, 25):
            sel = S.select(norms(n), "x")
            self.assertEqual(len(sel), 10, n)
            self.assertEqual(len({f for f, _ in sel}), 10)

    def test_two_rarest_first_then_evenly_spaced(self):
        sel = S.select(norms(20), "x")
        self.assertEqual([f for f, _ in sel[:2]], ["f00", "f01"])
        rest = [int(f[1:]) for f, _ in sel[2:]]
        self.assertEqual(rest[0], 2)
        self.assertEqual(rest[-1], 19)                       # spans rare to common
        self.assertEqual(rest, sorted(rest))

    def test_deterministic(self):
        self.assertEqual(S.select(norms(17), "x"), S.select(norms(17), "x"))

    def test_fewer_than_ten_cannot_supply(self):
        self.assertIsNone(S.select(norms(9), "x"))

    def test_reselection_needs_spare_features(self):
        self.assertIsNone(S.select(norms(10), "x", skip=1))  # exactly ten: no freedom to re-select
        self.assertEqual(len(S.select(norms(11), "x", skip=1)), 10)

    def test_declared_counts_agree(self):
        self.assertEqual(S.CLAUSES, 10)
        stim = HERE / "stimuli"
        self.assertRegex((stim / "build_bank.py").read_text(), r"(?m)^N_CLUES = 10\b")
        m = re.search(r"(?m)^TOKENS_MIN, TOKENS_MAX, PER_CONCEPT = 8, 14, (\d+)", (stim / "check_clues.py").read_text())
        self.assertEqual(m.group(1), "10")


if __name__ == "__main__":
    unittest.main()
