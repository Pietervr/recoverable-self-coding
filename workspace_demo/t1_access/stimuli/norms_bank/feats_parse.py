"""Feats (Borovsky, Peters, Cox & McRae 2023) and the McRae + Feats pooled source, with per-row provenance.

Source (not redistributed with this repo; CC BY 4.0, cited per clause):
  Borovsky, A., Peters, R. E., Cox, J. I., & McRae, K. (2023). Feats: A database of semantic features for
  early produced noun concepts. Behavior Research Methods 56 (2024), 3259-3279.
  DOI 10.3758/s13428-023-02242-x. OSF project 7d8et, held at ~/word-norms-feats/.
Feats is in McRae's own schema (Concept, Feature, BR_Label, Prod_Freq, Num_Parts, CV_No_Tax ...): features are
relational statements (`used_for_passengers`, `requires_pilots`), produced by adult respondents (33-126 per
newly normed concept) and retained at >= 16.66 % of respondents, McRae's 5 of 30. "LLaMA" in a file name is the
Language Learning and Meaning Acquisition lab, not a language model.

POOLING RULE (declared, R052/Codex 2 Oct 2026). Whole-set source priority on EXACT concept labels:
  - a concept label present in McRae keeps McRae's ENTIRE feature set; Feats adds nothing to it;
  - a Feats label absent from McRae contributes its Feats feature set (an "exact-new" concept);
  - McRae's alphabetic single-word guard applies to both, so `back_(body_part)` and `dining_room` drop out.
Parenthesised sense labels are NOT stripped: doing so would need a declared sense/collision rule and renewed E2.
Because every concept takes ALL its features from ONE source, a concept's features never mix two reference
universes - which is what makes source-specific CV usable as a within-concept heuristic (see CV POLICY).

PROVENANCE is kept per (concept, feature) from the row that supplied it: source and file version, the source's
own BR_Label relation, Prod_Freq, the respondent denominator, and the published CV_No_Tax. Nothing is copied from
one source's row onto another's (a feature-only relation map would give Feats' `has_cheese` McRae's label).
McRae's file has no Num_Parts column; its denominator is 30 per concept by the study's design (McRae et al.
2005), recorded as such.

CV POLICY. The authors' CV_No_Tax is reported as published and labelled with its source. It is not
source-invariant (airplane / has_wings: McRae CV .038 over a 529 denominator, Feats .141 over 141.5), so it is
never compared across sources and never recomputed under the authors' name. It is a selection heuristic within
one concept, and it gates nothing (§3.1: decisiveness comes from the naming test).
MISSING-CV POLICY. remainingUKCDI_concsFeats.csv has no CV_No_Tax column (e.g. `tea`). Such features carry
cv=None; a concept whose features lack published CV is ranked for selection by normalised production frequency
(30 x Prod_Freq / Num_Parts), labelled as such. No value is ever imputed; a missing CV is not read as low evidence.

    .venv-build/bin/python feats_parse.py          # prints the pinned bookkeeping and asserts it
"""

from __future__ import annotations

import collections
import csv
import hashlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mcrae_parse import McRae  # noqa: E402

FEATS_DIR = Path(os.environ.get("FEATS_DIR", Path.home() / "word-norms-feats"))
FEATS_VERSION = "Feats OSF 7d8et, release 2022-07-14"
FILES = {
    "MBCDI_concsFeats_2022-07-14.csv": "4b45b8910c5f42f7a6450aa33732a81bcbbcc0631d8c41df7b73d8c9d83d29ba",
    "remainingUKCDI_concsFeats.csv": "91aaef66e7e4cbfa975238c79f7ed7dcb0903b9dc4cdae37ae864f84a3302d34",
}
RELEASE_EVIDENCE = {   # checked as release evidence, not read for features
    "MBCDI_concs_2022-07-14.csv": "202311ec37050b4b7ccaff646cafcdac4acf134b75f5905bdfbdb8334b21eb09",
    "MCSM_LLAMA_feats_2022-07-14.csv": "f941ef90437407eb7de34085d27d69ebea8f9049508a335e752ac3894496935e",
}
MCRAE_SHA256 = "fe796831232b164635c258095749320665c18c40186778e8d8baf4b0c4cdba23"
MCRAE_DENOMINATOR = 30
MCRAE_VERSION = "McRae et al. 2005, McRae-BRM-2005.zip, CONCS_FEATS_concstats_brm.txt"

# Pinned bookkeeping (Codex record RSC 99277aa); the loader asserts these so a changed file cannot pass silently.
PINNED = {"feats_labels": 372, "uk_labels": 13, "overlap": 136, "overlap_identical": 103,
          "overlap_differing": 33, "exact_new": 236, "exact_new_single_word": 208}


def _float(x: str | None) -> float | None:
    try:
        return float(x) if x not in (None, "", "NA") else None
    except ValueError:
        return None


def read_feats() -> tuple[dict[str, list[dict]], dict[str, str]]:
    """Feats rows per concept label, each a provenance record; and the SHA-256 of every file read."""
    rows: dict[str, list[dict]] = collections.defaultdict(list)
    digests = {}
    for name, pinned in FILES.items():
        path = FEATS_DIR / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != pinned:
            raise SystemExit(f"{name}: sha256 {digest} does not match the pinned {pinned}")
        digests[name] = digest
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                concept, feature = (r.get("Concept") or "").strip(), (r.get("Feature") or "").strip()
                if not concept or not feature:
                    continue
                rows[concept].append({
                    "source": "Feats", "version": f"{FEATS_VERSION}, {name}", "concept": concept,
                    "feature": feature, "relation": (r.get("BR_Label") or "").strip(),
                    "prod_freq": _float(r.get("Prod_Freq")), "num_parts": _float(r.get("Num_Parts")),
                    "cv_published": _float(r.get("CV_No_Tax")) if "CV_No_Tax" in r else None,
                    "cv_column_present": "CV_No_Tax" in r,
                })
    for name, pinned in RELEASE_EVIDENCE.items():
        digests[name] = hashlib.sha256((FEATS_DIR / name).read_bytes()).hexdigest()
        if digests[name] != pinned:
            raise SystemExit(f"{name}: sha256 {digests[name]} does not match the pinned {pinned}")
    return dict(rows), digests


# Hovhannisyan's overlap with McRae + Feats on exact labels (Codex, RSC d6bdbc4), asserted below.
PINNED_HOV = {"hov_labels": 995, "overlap": 327, "exact_new": 668, "exact_new_single_word": 404}


class Source:
    """One source or a pool, with the McRae-compatible interface family_pool.py expects.

    mcrae    McRae alone
    pooled   McRae > Feats, exact-new Feats concepts only
    pooled3  McRae > Feats > Hovhannisyan (2021), exact-new Hovhannisyan concepts only, Hovhannisyan features at an
             absolute cutoff of >= hov_cutoff productions (hovhannisyan_parse.py states the gaps that implies)
    """

    def __init__(self, name: str, hov_cutoff: int = 3):
        if name not in ("mcrae", "pooled", "pooled3"):
            raise ValueError(name)
        self.name = name
        mc = McRae()
        if mc.sha256 != MCRAE_SHA256:
            raise SystemExit(f"McRae sha256 {mc.sha256} does not match the pinned {MCRAE_SHA256}")
        self.path = mc.path
        self.provenance: dict[tuple[str, str], dict] = {}
        for (c, f), freq in mc.frequency.items():
            self.provenance[(c, f)] = {
                "source": "McRae", "version": MCRAE_VERSION, "concept": c, "feature": f,
                "relation": mc.relation_of.get((c, f), ""), "prod_freq": float(freq),
                "num_parts": float(MCRAE_DENOMINATOR), "cv_published": mc.cue_validity.get((c, f)),
                "cv_column_present": True,
            }
        all_cues = dict(mc.all_cues)
        features = dict(mc.features)
        digests = {"CONCS_FEATS_concstats_brm.txt": mc.sha256}
        self.bookkeeping: dict = {}
        n_rows = mc.n_rows
        if name in ("pooled", "pooled3"):
            feats, fd = read_feats()
            digests.update(fd)
            labels = set(feats)
            overlap = sorted(labels & set(mc.all_cues))
            new = sorted(labels - set(mc.all_cues))
            same = [c for c in overlap if {r["feature"] for r in feats[c]} == set(mc.all_cues[c])]
            uk = {r["concept"] for rs in feats.values() for r in rs if "remainingUKCDI" in r["version"]}
            new_single = [c for c in new if c.isalpha()]
            self.bookkeeping = {"feats_labels": len(labels), "uk_labels": len(uk), "overlap": len(overlap),
                                "overlap_identical": len(same), "overlap_differing": len(overlap) - len(same),
                                "exact_new": len(new), "exact_new_single_word": len(new_single)}
            if self.bookkeeping != PINNED:
                raise SystemExit(f"Feats bookkeeping {self.bookkeeping} differs from the pinned {PINNED}")
            for c in new:
                all_cues[c] = {r["feature"] for r in feats[c]}
                n_rows += len(feats[c])
                for r in feats[c]:
                    self.provenance[(c, r["feature"])] = r
            for c in new_single:
                features[c] = {r["feature"] for r in feats[c]}
            self.exact_new_single = new_single
        if name == "pooled3":
            from hovhannisyan_parse import read as read_hov
            hov, hd = read_hov(hov_cutoff)
            digests.update(hd)
            hlabels = set(hov)
            h_overlap = sorted(hlabels & set(all_cues))
            h_new = sorted(hlabels - set(all_cues))
            h_single = [c for c in h_new if c.isalpha()]
            hb = {"hov_labels": len(hlabels), "overlap": len(h_overlap), "exact_new": len(h_new),
                  "exact_new_single_word": len(h_single)}
            if hb != PINNED_HOV:
                raise SystemExit(f"Hovhannisyan bookkeeping {hb} differs from the pinned {PINNED_HOV}")
            self.bookkeeping["hovhannisyan"] = {**hb, "cutoff": hov_cutoff}
            for c in h_new:
                all_cues[c] = {r["feature"] for r in hov[c]}
                n_rows += len(hov[c])
                for r in hov[c]:
                    self.provenance[(c, r["feature"])] = r
            for c in h_single:
                features[c] = {r["feature"] for r in hov[c]}
            self.hov_new_single = h_single
        self.digests = digests
        self.sha256 = hashlib.sha256("|".join(f"{k}:{v}" for k, v in sorted(digests.items())).encode()).hexdigest()
        self.n_rows = n_rows
        self.all_cues = all_cues
        self.features = features
        self.pos = {c: "noun" for c in features}
        self.sharing: collections.Counter = collections.Counter()
        for fs in features.values():
            self.sharing.update(fs)

    def source_of(self, concept: str) -> str:
        return self.provenance[(concept, next(iter(self.features[concept])))]["source"]

    def nouns(self) -> list[str]:
        return sorted(self.features)

    def with_features(self, minimum: int, cues=None) -> list[str]:
        pool = self.features if cues is None else {c: self.features[c] for c in cues}
        return sorted(c for c, fs in pool.items() if len(fs) >= minimum)


def main() -> None:
    for name in ("mcrae", "pooled"):
        s = Source(name)
        print(f"{name}: {len(s.features)} single-word concepts, {len(s.with_features(12))} at >= 12 raw features,"
              f" {len(s.with_features(10))} at >= 10; composite digest {s.sha256[:16]}...")
        for k, v in s.digests.items():
            print(f"    {k:<36} {v}")
        if s.bookkeeping:
            print(f"    bookkeeping (asserted against the pinned figures): {s.bookkeeping}")
    p = Source("pooled")
    no_cv = sorted(c for c in p.exact_new_single if all(p.provenance[(c, f)]["cv_published"] is None
                                                       for f in p.features[c]))
    print(f"exact-new single-word concepts with no published CV on any feature: {no_cv}")


if __name__ == "__main__":
    main()
