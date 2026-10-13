"""The released citation table: McRae rows by statement, CSLB rows by reference only (stimuli/norms_bank/citation.py;
owner, 13 October 2026). No CSLB data is needed except for the coverage check, which is skipped without a local copy.

    python3 -m unittest test_norms_citation.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "stimuli" / "norms_bank"))
import citation as C  # noqa: E402


class Citation(unittest.TestCase):
    IDS = {("hamster", "has_fur_hair"): [[9381, 18], [9383, 13]], ("crow", "is_black"): [[42, 25]]}

    def test_mcrae_row_unchanged(self):
        r = C.citation_row({"source": "McRae", "concept": "crow", "feature": "is_black", "prod_freq": 20.0,
                            "cv_published": 0.04})
        self.assertEqual(r, {"source": "McRae", "concept": "crow", "feature": "is_black", "prod_freq": 20.0,
                             "cue_validity": 0.04})

    def test_cslb_row_is_a_reference(self):
        r = C.citation_row({"source": "CSLB", "concept": "hamster", "feature": "has_fur_hair", "prod_freq": 13.0},
                           ids=self.IDS)
        self.assertEqual(r, {"source": "CSLB", "concept": "hamster", "cslb_entries": [[9381, 18], [9383, 13]]})
        self.assertNotIn("feature", r)
        out = C.release_rows([r])
        self.assertIn("Centre for Speech, Language and the Brain", out["cslb"]["credit"])
        self.assertIn("bear no responsibility", out["cslb"]["declaration"])

    def test_text_never_leaves_in_a_cslb_row(self):
        for bad in ({"source": "CSLB", "concept": "crow", "cslb_entries": [[42, 25]], "feature": "is_black"},
                    {"source": "CSLB", "concept": "crow", "cslb_entries": "is black"},
                    {"source": "CSLB", "concept": "crow", "cslb_entries": [["42", 25]]},
                    {"source": "CSLB", "concept": "crow", "cslb_entries": [[True, 25]]},
                    {"source": "CSLB", "concept": "crow", "cslb_entries": []}):
            with self.assertRaises(SystemExit):
                C.release_rows([bad])

    def test_unknown_entry_and_source_refuse(self):
        with self.assertRaises(SystemExit):
            C.citation_row({"source": "CSLB", "concept": "crow", "feature": "can_fly", "prod_freq": 9.0}, ids=self.IDS)
        with self.assertRaises(SystemExit):
            C.citation_row({"source": "Buchanan", "concept": "crow", "feature": "x", "prod_freq": 1.0})

    @unittest.skipUnless(C.CSLB_NORMS.exists(), "CSLB norms not held on this machine (never in the repository)")
    def test_every_cslb_pair_resolves(self):
        ids = C.cslb_entry_ids()
        rows = C.CSLB_NORMS.read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual(sum(len(v) for v in ids.values()), len(rows))
        for line in rows[:500]:
            f = line.split("\t")
            r = C.citation_row({"source": "CSLB", "concept": f[2], "feature": "_".join(f[3].split()),
                                "prod_freq": float(f[4])}, ids=ids)
            C.release_rows([r])


if __name__ == "__main__":
    unittest.main()
