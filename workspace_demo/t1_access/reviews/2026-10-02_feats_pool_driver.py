#!/usr/bin/env python3
"""Feasibility only (R052, 1 Oct 2026): McRae 2005 pooled with the NEW concepts of Feats (Borovsky, Peters, Cox &
McRae 2023, OSF 7d8et; McRae's schema), measured through R084's family_pool.py under SOURCE=feats so that every
output is a new file. Rule: a concept in both sets keeps McRae's feature set; Feats contributes concepts McRae
lacks; the same single-word (isalpha) guard as McRae. Nothing in stimuli/ is edited.

    .venv-build/bin/python feats_pool_driver.py        (then pool_e1.py with SOURCE=feats in the jlens venv)
"""
import collections
import csv
import hashlib
import os
import sys
from pathlib import Path

os.environ["SOURCE"] = "feats"
NB = Path("/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/stimuli/norms_bank")
sys.path.insert(0, str(NB))
FEATS_DIR = Path.home() / "word-norms-feats"
FILES = ["MBCDI_concsFeats_2022-07-14.csv", "remainingUKCDI_concsFeats.csv"]


class Pooled:
    name = "feats"

    def __init__(self):
        from mcrae_parse import McRae
        m = McRae()
        self.mcrae = m
        self.path = FEATS_DIR / FILES[0]
        h = hashlib.sha256()
        feats: dict[str, set[str]] = collections.defaultdict(set)
        self.frequency = dict(m.frequency)
        self.cue_validity = dict(m.cue_validity)
        self.relation = dict(m.relation)
        rows = 0
        for f in FILES:
            p = FEATS_DIR / f
            h.update(p.read_bytes())
            for r in csv.DictReader(open(p, encoding="utf-8-sig")):
                c, ft = r["Concept"].strip(), r["Feature"].strip()
                if not c or not ft:
                    continue
                rows += 1
                feats[c].add(ft)
                try:
                    self.frequency.setdefault((c, ft), int(float(r["Prod_Freq"])))
                except (ValueError, KeyError):
                    pass
                try:
                    self.cue_validity.setdefault((c, ft), float(r["CV_No_Tax"]))
                except (ValueError, KeyError):
                    pass
                self.relation.setdefault(ft, r.get("BR_Label", "").strip())
        self.sha256 = h.hexdigest()
        self.n_rows = m.n_rows + rows
        new = {c: fs for c, fs in feats.items() if c not in m.all_cues}
        self.all_cues = dict(m.all_cues)
        self.all_cues.update(new)
        self.features = dict(m.features)
        self.features.update({c: fs for c, fs in new.items() if c.isalpha()})
        self.feats_new_single = sorted(c for c in new if c.isalpha())
        self.pos = {c: "noun" for c in self.features}
        self.sharing = collections.Counter()
        for fs in self.features.values():
            self.sharing.update(fs)

    def nouns(self):
        return sorted(self.features)

    def with_features(self, minimum, cues=None):
        pool = self.features if cues is None else {c: self.features[c] for c in cues}
        return sorted(c for c, fs in pool.items() if len(fs) >= minimum)


import family_pool as fp  # noqa: E402

pooled = Pooled()
fp.load_source = lambda: pooled
print(f"McRae single-word concepts {len(pooled.mcrae.features)}; Feats new single-word concepts {len(pooled.feats_new_single)}; "
      f"pooled {len(pooled.features)}; at >= {fp.MIN_FEATURES} features {len(pooled.with_features(fp.MIN_FEATURES))}")
rc = fp.main()
print("family_pool done, rc", rc)
