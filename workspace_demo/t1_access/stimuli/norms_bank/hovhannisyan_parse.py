"""Hovhannisyan et al. (2021): a third relational feature source, read with its gaps labelled.

Source (not redistributed with this repo): Hovhannisyan, M., et al. (2021), the Object Memory project - human
feature production for 995 PHOTOGRAPHED objects by 566 native American-English MTurk respondents, at least 20
respondents per concept (mean 30.5). Author files from github.com/ElectricDinoLab/ObjectMemory, tree
9cac6649dfd9ad5dca97dca2c265df4cf7c58c9f, OSF fxgzj; held at ~/word-norms-hovhannisyan/. The article is CC BY 4.0;
the GitHub tree carries no LICENSE and the OSF node reports none, so the data's own reuse terms are an open
metadata gap (Codex, RSC d6bdbc4) - recorded, not resolved here.

What is read:
  featurematrix.csv          concept x feature, integer production counts; features are relational statements
                             (is_made_of_metal, has_a_handle, is_a_bird);
  conceptFeatureLabelList.xlsx, sheet 'fullList'   the authors' relation label per (concept, feature), in McRae's
                             scheme (taxonomic, encyclopedic, visual-form_and_surface ...), so rule T uses the
                             SOURCE'S OWN label, as it does for McRae and Feats - no frame proxy is needed.

THREE GAPS, LABELLED AND NEVER IMPUTED:
  - NO PER-CONCEPT DENOMINATOR. Inclusion is an ABSOLUTE cutoff of >= CUTOFF productions (declared 3, with 5 as
    the sensitivity), not the one-sixth prevalence McRae (5/30) and Feats (16.66 %) use; num_parts is None.
  - NO CV. Features carry cv_published=None; within a Hovhannisyan concept they would be ranked by raw production
    count, labelled as such.
  - PHOTO-CONDITIONED. Features were elicited on a photograph, not a name, so a feature may describe the pictured
    exemplar (is_green for one photographed object) rather than the concept. Carried in every provenance record.

    .venv-build/bin/python hovhannisyan_parse.py
"""

from __future__ import annotations

import collections
import csv
import hashlib
import html
import os
import re
import zipfile
from pathlib import Path

HOV_DIR = Path(os.environ.get("HOV_DIR", Path.home() / "word-norms-hovhannisyan"))
VERSION = "Hovhannisyan et al. 2021, ElectricDinoLab/ObjectMemory tree 9cac664"
CAVEAT = "photo-conditioned: elicited on a photograph of one exemplar, not on the concept name"
PINNED = {
    "featurematrix.csv": "152eb2cc1729514781f4087d7fd6bbf2f34ff05089af02636f1e11df57b80e33",
    "conceptFeatureLabelList.xlsx": "570aa322dd7af158f5d893a3c9f7ed47000a753607c63fbd81dd6bd53eb3dc3b",
    "pics.csv": "ce2688a42010e928d64f662cc6136a8a01f15e82a36b575d219179c2f1269d2a",
}
DEFAULT_CUTOFF = 3


def _labels(path: Path) -> dict[tuple[str, str], str]:
    """The authors' relation label per (concept, feature), majority over the per-production rows of 'fullList'."""
    z = zipfile.ZipFile(path)
    wb = z.read("xl/workbook.xml").decode()
    names = re.findall(r'<sheet [^>]*name="([^"]+)"', wb)
    sheet = f"xl/worksheets/sheet{names.index('fullList') + 1}.xml"
    shared = [html.unescape(re.sub(r"<[^>]+>", "", m))
              for m in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode("utf8"), re.S)]
    votes: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for row in re.findall(r"<row[^>]*>(.*?)</row>", z.read(sheet).decode("utf8"), re.S)[1:]:
        vals = []
        for attrs, inner in re.findall(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", row, re.S):
            v = re.search(r"<v>(.*?)</v>", inner or "")
            t = re.search(r't="([a-z]+)"', attrs)
            vals.append("" if not v else (shared[int(v.group(1))] if t and t.group(1) == "s" else v.group(1)))
        if len(vals) >= 3 and vals[0] and vals[1]:
            votes[(vals[0], vals[1])][vals[2]] += 1
    return {k: c.most_common(1)[0][0] for k, c in votes.items()}


def read(cutoff: int = DEFAULT_CUTOFF) -> tuple[dict[str, list[dict]], dict[str, str]]:
    """Per concept label (as written in the matrix), the feature rows at >= cutoff productions, with provenance."""
    digests = {}
    for name, pinned in PINNED.items():
        d = hashlib.sha256((HOV_DIR / name).read_bytes()).hexdigest()
        if d != pinned:
            raise SystemExit(f"{name}: sha256 {d} does not match the pinned {pinned}")
        digests[name] = d
    labels = _labels(HOV_DIR / "conceptFeatureLabelList.xlsx")
    rows: dict[str, list[dict]] = {}
    with open(HOV_DIR / "featurematrix.csv", encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        feats = header[3:]
        for rec in r:
            concept = rec[0].strip()
            key = concept.replace(" ", "_")
            out = []
            for f, v in zip(feats, rec[3:]):
                try:
                    n = int(float(v)) if v else 0
                except ValueError:
                    n = 0
                if n >= cutoff:
                    out.append({"source": "Hovhannisyan", "version": f"{VERSION}, featurematrix.csv, cutoff >= {cutoff}",
                                "concept": concept, "feature": f, "relation": labels.get((key, f), ""),
                                "prod_freq": float(n), "num_parts": None, "cv_published": None,
                                "cv_column_present": False, "caveat": CAVEAT,
                                "category_by_source": rec[1].strip()})
            rows[concept] = out
    return rows, digests


def main() -> None:
    for cutoff in (3, 5):
        rows, _ = read(cutoff)
        n = [len(v) for v in rows.values()]
        unlabelled = sum(1 for v in rows.values() for x in v if not x["relation"])
        print(f">= {cutoff}: {len(rows)} concepts; features per concept median {sorted(n)[len(n)//2]}, "
              f"{sum(1 for x in n if x >= 12)} at >= 12, {sum(1 for x in n if x >= 10)} at >= 10; "
              f"{unlabelled} retained features with no authors' label")


if __name__ == "__main__":
    main()
