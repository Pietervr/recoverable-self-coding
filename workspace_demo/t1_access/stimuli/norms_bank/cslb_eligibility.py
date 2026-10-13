"""Three-family eligibility on McRae + CSLB with the REAL CSLB features (12 October 2026; R052 handoff 10df48d8).

The 26 September count (RSC 2646bf1) pooled McRae with a CSLB-only UPPER BOUND: CSLB's feature file was gated, so its
concepts went through the family rules but not the >= 12 feature filter. The norms arrived on 12 October 2026 (Barry
Devereux, CSLB Property Norms V1.1, held in ~/word-norms-cslb/, never in a repository), so the filter now runs.

SAME CHAIN AS clean_eligibility.py (its functions are imported, unchanged): F1/F2 noun and own base form; F4 dominant
sense in one adopted family (animals, foods, vehicles); E2 no noun sense in another adopted family; E1 the answer form
' x' is one token (token_counts.json, now including CSLB's single-word labels); F3 >= 12 features at the RAW tier (the
26 September measure) and at the PROTOCOL tier (§3.1's usable features: T taxonomic rows, F family words, N own name,
X other bank-concept names, P proper nouns, M merge by subsumption over Porter2-stem / WordNet-derivation classes);
cues sharing a dominant synset collapse after E1 and F3; the joint CONF 64 / CAL 12 / PILOT 12 + one BACKGROUND per
family allocation is checked.

THE POOL. McRae concepts keep McRae's features. A CSLB concept whose label is not a McRae label is a NEW concept with
its CSLB features (the pooling convention of feats_parse.Source: "exact-new concepts only"). CSLB's `taxonomic`
feature type is rule T's relation. CSLB's labels use spaces; they are tokenised like McRae's underscore labels.
Sense-tagged labels (bat_(animal)) are not single words and drop out, as McRae's do.

THE PF CUTOFF (declared, not tuned): CSLB publishes every concept-feature pair with production frequency > 1 (readme);
McRae kept a feature only when at least 5 of its 30 participants produced it. CSLB's own similarity files use pf >= 5.
PRIMARY: pf >= 5 (comparable to McRae). Sensitivity: pf >= 3 and pf >= 2 (every published pair).

A SECOND READING, not the convention: `merged` also adds CSLB's features to the overlapping McRae concepts, under the
same merge rules. McRae and CSLB phrase one property differently (has_4_legs / has four legs), and the stem/derivation
merge does not equate '4' with 'four', so this reading can double-count across sources: an UPPER reading, reported for
R052, not a proposal.

LICENCE (cslb_norms_licence.pdf): no redistribution in any form without CSLB's written consent. The committed JSON holds
counts, cue words (CSLB's concept list is published in its paper's appendix), allocations and digests only; the
per-concept feature record goes to cslb_eligibility_detail.json, which is git-ignored.

    .venv-build/bin/python stimuli/norms_bank/cslb_eligibility.py
"""

from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clean_eligibility as CE  # noqa: E402
import family_pool as fp  # noqa: E402
from feats_parse import Source  # noqa: E402
from usable import Canon, usable, words  # noqa: E402

CSLB_DIR = Path.home() / "word-norms-cslb"
NORMS = CSLB_DIR / "norms.dat"
ZIP_SHA256 = "473eb656398695f9f9f5c8b8a675d4ca3cbdb09391a5946d0a0d4a82038d6e2b"
NORMS_PREFIX = "d81d5120"                      # the brief's pin of norms.dat (prefix)
PF_LEVELS = [5, 3, 2]
THRESHOLDS = [10, 12]                          # owner, 13 Oct 2026: the minimum is 10
TIERS = ["raw", "protocol"]


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_cslb(pf_min: int) -> dict[str, list[dict]]:
    rows = collections.defaultdict(list)
    lines = NORMS.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t")
    if head[:5] != ["domain", "feature type", "concept", "feature", "pf"]:
        raise SystemExit(f"unexpected norms.dat header {head}")
    for line in lines[1:]:
        dom, ftype, concept, feature, pf = line.split("\t")[:5]
        if int(pf) < pf_min:
            continue
        label = "_".join(feature.split())
        rows[concept].append({"source": "CSLB", "version": "1.1", "concept": concept, "feature": label,
                              "relation": "taxonomic" if ftype == "taxonomic" else ftype,
                              "prod_freq": float(pf), "feature_type": ftype, "domain": dom})
    return dict(rows)


class McRaeCSLB(Source):
    """McRae > CSLB: exact-new CSLB concepts with their CSLB features (merged=True also unions CSLB features into the
    overlapping McRae concepts - the upper reading)."""

    def __init__(self, pf_min: int, merged: bool = False):
        super().__init__("mcrae")
        if sha_file(CSLB_DIR / "CSLB_Property_Norms_V1.1.zip") != ZIP_SHA256 or \
                not sha_file(NORMS).startswith(NORMS_PREFIX):
            raise SystemExit("CSLB files differ from the pinned zip / norms.dat")
        cslb = read_cslb(pf_min)
        labels = set(cslb)
        overlap = sorted(labels & set(self.all_cues))
        new = sorted(labels - set(self.all_cues))
        new_single = [c for c in new if c.isalpha()]
        for c in new:
            self.all_cues[c] = {r["feature"] for r in cslb[c]}
            for r in cslb[c]:
                self.provenance[(c, r["feature"])] = r
        for c in new_single:
            self.features[c] = {r["feature"] for r in cslb[c]}
        added = 0
        if merged:
            for c in overlap:
                if c in self.features:
                    for r in cslb[c]:
                        if (c, r["feature"]) not in self.provenance:
                            self.provenance[(c, r["feature"])] = r
                            self.features[c].add(r["feature"])
                            added += 1
        self.digests = {**self.digests, "CSLB_Property_Norms_V1.1.zip": ZIP_SHA256, "norms.dat": sha_file(NORMS)}
        self.sha256 = hashlib.sha256("|".join(f"{k}:{v}" for k, v in sorted(self.digests.items())).encode()).hexdigest()
        self.pos = {c: "noun" for c in self.features}
        self.sharing = collections.Counter()
        for fs in self.features.values():
            self.sharing.update(fs)
        self.bookkeeping = {"pf_min": pf_min, "merged": merged, "cslb_labels": len(labels), "overlap": len(overlap),
                            "exact_new": len(new), "exact_new_single_word": len(new_single),
                            "features_added_to_overlap": added}
        self.cslb_new_single = new_single


def count(src, trees, tokens, canon) -> dict:
    cands = CE.candidates(src, trees, tokens, 1)
    bank = set(cands)
    per = {c: {t: usable(c, src.features[c], src.provenance, bank, canon, t) for t in TIERS} for c in cands}
    res = {}
    for thr in THRESHOLDS:
        for tier in TIERS:
            q = {c: {**cands[c], "usable": per[c][tier]["count"]} for c in cands if per[c][tier]["count"] >= thr}
            fams = CE.collapse(q)
            counts = {f: len(v) for f, v in fams.items()}
            res[f">={thr}|{tier}"] = {"counts": counts, "total": sum(counts.values()), "concepts": fams,
                                      "allocation": CE.feasible_allocation(counts)}
    detail = {c: {"family": cands[c]["family"], "source": src.provenance[(c, next(iter(src.features[c])))]["source"],
                  "raw": per[c]["raw"]["count"], "protocol": per[c]["protocol"]["count"],
                  "removed": {k: v for k, v in per[c]["protocol"]["log"].items() if v}} for c in sorted(cands)}
    return {"results": res, "detail": detail}


def main() -> int:
    trees = {f: fp.subtree(f) for f in CE.FAMILIES}
    tok = json.loads((HERE / "token_counts.json").read_text())
    sources = {"mcrae": Source("mcrae")}
    for pf in PF_LEVELS:
        sources[f"mcrae+cslb_pf{pf}"] = McRaeCSLB(pf)
    sources["mcrae+cslb_pf5_merged"] = McRaeCSLB(5, merged=True)
    vocab = {w for s in sources.values() for fs in s.features.values() for f in fs for w in words(f)}
    canon = Canon({w for w in vocab if w.isalpha()})
    out = {"design": "three families (animals, foods, vehicles); needed CONF 64 + CAL 12 + PILOT 12 + one BACKGROUND "
                     "per family = 91 (owner, 13 Oct 2026); usable-feature minimum 10 (12 also reported); single-token E1",
           "baseline_2026_09_26": {"rsc": "2646bf1", "mcrae_raw_ge12": [33, 15, 17, 65],
                                   "pooled_upper_bound_no_feature_filter": [57, 42, 29, 128]},
           "tokenizer_json_sha256": tok["tokenizer_json_sha256"],
           "script_sha256": sha_file(Path(__file__)),
           "usable_sha256": sha_file(HERE / "usable.py"), "clean_eligibility_sha256": sha_file(HERE / "clean_eligibility.py"),
           "licence_note": "CSLB Norms: Copyright (c) and database right 2012-15 Centre for Speech, Language and the "
                           "Brain (CSLB), Department of Psychology, University of Cambridge. All rights reserved. "
                           "Devereux, Tyler, Geertzen & Randall (2014), BRM 46(4) 1119-1127, doi:10.3758/s13428-013-0420-4. "
                           "CSLB, the original collectors and the funders bear no responsibility for this analysis.",
           "sources": {}, "results": {}}
    private = {}
    for name, src in sources.items():
        r = count(src, trees, tok["counts"], canon)
        out["sources"][name] = {"digests": src.digests, "bookkeeping": src.bookkeeping}
        out["results"][name] = r["results"]
        private[name] = r["detail"]
    (HERE / "cslb_eligibility_detail.json").write_text(json.dumps(private, indent=1, ensure_ascii=False) + "\n")
    (HERE / "cslb_eligibility.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=list) + "\n")
    print(f"{'source':<24} {'thr':>4} {'tier':<9} {'animals':>8} {'foods':>6} {'vehicles':>9} {'total':>6}  allocation (need 91)")
    for name, rs in out["results"].items():
        for key, r in rs.items():
            thr, tier = key.split("|")
            c, a = r["counts"], r["allocation"]
            verdict = "feasible" if a.get("feasible") else (f"NO (deficit {a['deficit']})" if a["deficit"]
                                                            else "NO (half bound)")
            print(f"{name:<24} {thr:>4} {tier:<9} {c['animals']:>8} {c['foods']:>6} {c['vehicles']:>9} {r['total']:>6}  {verdict}")
    for name, s in out["sources"].items():
        if s["bookkeeping"]:
            print(f"  {name}: {s['bookkeeping']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
