"""Read the McRae et al. (2005) feature production norms.

Source (not redistributed with this repo):
  McRae, K., Cree, G. S., Seidenberg, M. S., & McNorgan, C. (2005). Semantic feature production
  norms for a large set of living and nonliving things. Behavior Research Methods, 37(4), 547-559.
  Archive: McRae-BRM-2005.zip from the Psychonomic Society web archive via Springer,
  483,471 bytes, sha256 eb36b4c88f85141a226879ef2fdddc8075b9d35705fd27344c3a414eb56430a3.
  Data file: McRae-BRM-InPress/CONCS_FEATS_concstats_brm.txt, 7,259 rows over 541 concepts,
  listing every feature given by at least 5 of 30 participants.

WHY THIS SOURCE AND NOT BUCHANAN: a McRae feature is a RELATIONAL STATEMENT, not a word -
`has_a_trunk`, `lives_in_Africa`, `used_in_circuses`, `has_a_wooden_handle`, `a_mammal`. The
relation is what a clause asserts, so rendering is de-underscoring plus agreement rather than
authoring a predicate, and the per-clause citation is real. Buchanan's `feature` column holds
single content words stripped out of free-text prose, where the relation is gone.

Columns used: Concept, Feature, BR_Label (the brain-region feature type: visual-form_and_surface,
function, encyclopaedic, taxonomic, visual-colour, visual-motion, tactile, sound, taste, smell),
Prod_Freq (how many of 30 participants produced it), CV_No_Tax (the authors' own cue validity,
P(concept | feature) over the non-taxonomic norms).

Interface matches norms_parse.Norms so family_pool.py can take either source.

    .venv-build/bin/python mcrae_parse.py
"""

from __future__ import annotations

import collections
import hashlib
import os
from pathlib import Path

DEFAULT_DIR = Path(os.environ.get("MCRAE_DIR", Path.home() / "word-norms-mcrae/McRae-BRM-InPress"))
DATA = "CONCS_FEATS_concstats_brm.txt"
EXPECTED_ZIP_SHA256 = "eb36b4c88f85141a226879ef2fdddc8075b9d35705fd27344c3a414eb56430a3"


class McRae:
    """Concept -> features, feature -> concepts, production frequency and the authors' cue validity."""

    name = "mcrae"

    def __init__(self, directory: Path = DEFAULT_DIR):
        self.path = directory / DATA
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()
        lines = self.path.read_text(encoding="utf8", errors="replace").splitlines()
        header = lines[0].split("\t")
        col = {n: i for i, n in enumerate(header)}
        features: dict[str, set[str]] = collections.defaultdict(set)
        self.frequency: dict[tuple[str, str], int] = {}
        self.cue_validity: dict[tuple[str, str], float] = {}
        self.relation: dict[str, str] = {}
        self.n_rows = 0
        for line in lines[1:]:
            if not line.strip():
                continue
            f = line.split("\t")
            concept, feature = f[col["Concept"]].strip(), f[col["Feature"]].strip()
            if not concept or not feature:
                continue
            self.n_rows += 1
            features[concept].add(feature)
            try:
                self.frequency[(concept, feature)] = int(f[col["Prod_Freq"]])
            except (ValueError, IndexError):
                pass
            try:
                self.cue_validity[(concept, feature)] = float(f[col["CV_No_Tax"]])
            except (ValueError, IndexError):
                pass
            self.relation[feature] = f[col["BR_Label"]].strip()
        self.all_cues = dict(features)
        # concepts are single words by construction in this set; keep the same guard as Buchanan
        self.features = {c: fs for c, fs in features.items() if c.isalpha()}
        self.pos = {c: "noun" for c in self.features}      # all 541 are concrete nouns by design
        self.sharing: collections.Counter = collections.Counter()
        for fs in self.features.values():
            self.sharing.update(fs)

    def nouns(self) -> list[str]:
        return sorted(self.features)

    def with_features(self, minimum: int, cues=None) -> list[str]:
        pool = self.features if cues is None else {c: self.features[c] for c in cues}
        return sorted(c for c, fs in pool.items() if len(fs) >= minimum)


def main() -> None:
    m = McRae()
    print(f"{m.path}\n  sha256 {m.sha256}")
    print(f"  {m.n_rows} rows, {len(m.all_cues)} concepts, {len(m.features)} single-word concepts")
    print(f"  distinct feature statements: {len(m.sharing)}")
    print(f"  concepts with >= 12 features: {len(m.with_features(12))}")
    print(f"  concepts with >= 16 features: {len(m.with_features(16))}")
    counts = sorted(len(v) for v in m.features.values())
    print(f"  features per concept: min {counts[0]}, median {counts[len(counts)//2]}, max {counts[-1]}")
    rel = collections.Counter(m.relation.values())
    print("  relation types: " + ", ".join(f"{k} {v}" for k, v in rel.most_common()))


if __name__ == "__main__":
    main()
