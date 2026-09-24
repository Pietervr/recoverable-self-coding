"""Read the Buchanan et al. (2019) extended feature-production norms without pandas or openpyxl.

Source (not redistributed with this repo; see FEASIBILITY.md "Licence"):
  Buchanan, E. M., Valentine, K. D., & Maxwell, N. P. (2019). English semantic feature production
  norms: an extended database of 4436 concepts. Behavior Research Methods, 51(4), 1849-1863.
  Data mirror: github.com/doomlab/Word-Norms-2, file "4 analysis/final words 2017.xlsx"
  (7,173,768 bytes, sha256 6e1fc087986d5657684e190c2c04bd5a2c40f1d39b78eebb0ead8bb5e2225337).

An .xlsx is a zip of XML, so the file is read with zipfile + re: xl/sharedStrings.xml holds every
string, xl/worksheets/sheet1.xml the cells. 69,284 data rows, 4,436 distinct cues, which is the
published count. 25 of those cues are sense-disambiguated with an underscore (bat_animal,
bat_baseball); they are not single words and are dropped here, leaving 4,411.

The feature identity used throughout is the raw `feature` string, not `translated`: `translated`
collapses production variants and leaves only 878 cues with >= 12 features against 2,585 on
`feature`. Which column defines a feature for the DECISIVENESS statistic is a step-2 question and
is not settled here.

    python3 norms_parse.py            # prints the summary counts, no dependencies
"""

from __future__ import annotations

import collections
import hashlib
import html
import os
import re
import zipfile
from pathlib import Path

DEFAULT_XLSX = Path(os.environ.get("WORD_NORMS_XLSX", Path.home() / "word-norms-2/final_words_2017.xlsx"))
EXPECTED_SHA256 = "6e1fc087986d5657684e190c2c04bd5a2c40f1d39b78eebb0ead8bb5e2225337"

_CELL = re.compile(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", re.S)
_REF = re.compile(r'r="([A-Z]+)\d+"')
_TYPE = re.compile(r't="([a-z]+)"')
_VAL = re.compile(r"<v>(.*?)</v>", re.S)
_SI = re.compile(r"<si>(.*?)</si>", re.S)
_ROW = re.compile(r"<row[^>]*>(.*?)</row>", re.S)
_TAG = re.compile(r"<[^>]+>")


def read_rows(xlsx: Path = DEFAULT_XLSX) -> list[dict[str, str]]:
    """Every data row as {column name: value}, in file order."""
    with zipfile.ZipFile(xlsx) as z:
        shared = [html.unescape(_TAG.sub("", m)) for m in _SI.findall(z.read("xl/sharedStrings.xml").decode("utf8"))]
        raw_rows = _ROW.findall(z.read("xl/worksheets/sheet1.xml").decode("utf8"))

    def cells(row: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for attrs, inner in _CELL.findall(row):
            ref = _REF.search(attrs).group(1)
            typed = _TYPE.search(attrs)
            val = _VAL.search(inner or "")
            if val is None:
                out[ref] = ""
            elif typed is not None and typed.group(1) == "s":
                out[ref] = shared[int(val.group(1))]
            else:
                out[ref] = html.unescape(val.group(1))
        return out

    header = cells(raw_rows[0])
    names = {ref: header[ref] for ref in header}
    return [{names[ref]: v for ref, v in cells(r).items() if ref in names} for r in raw_rows[1:]]


class Norms:
    """Cue -> features, feature -> cues, and the per-cue part of speech."""

    def __init__(self, xlsx: Path = DEFAULT_XLSX):
        self.xlsx = xlsx
        self.sha256 = hashlib.sha256(xlsx.read_bytes()).hexdigest()
        rows = read_rows(xlsx)
        self.n_rows = len(rows)
        features: dict[str, set[str]] = collections.defaultdict(set)
        pos: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        freq: dict[tuple[str, str], int] = {}
        for r in rows:
            cue = r.get("cue", "").strip()
            feat = r.get("feature", "").strip()
            if not cue or not feat:
                continue
            features[cue].add(feat)
            pos[cue][r.get("pos_cue", "")] += 1
            try:
                freq[(cue, feat)] = max(freq.get((cue, feat), 0), int(float(r.get("frequency_feature") or 0)))
            except ValueError:
                pass
        self.all_cues = dict(features)
        self.features = {c: fs for c, fs in features.items() if c.isalpha()}  # drops the 25 sense-tagged cues
        self.pos = {c: pos[c].most_common(1)[0][0] for c in self.features}
        self.frequency = freq
        self.sharing: collections.Counter = collections.Counter()
        for fs in self.features.values():
            self.sharing.update(fs)

    def nouns(self) -> list[str]:
        return sorted(c for c in self.features if self.pos[c] == "noun")

    def with_features(self, minimum: int, cues=None) -> list[str]:
        pool = self.features if cues is None else {c: self.features[c] for c in cues}
        return sorted(c for c, fs in pool.items() if len(fs) >= minimum)


def main() -> None:
    n = Norms()
    ok = "matches" if n.sha256 == EXPECTED_SHA256 else "DOES NOT MATCH"
    print(f"{n.xlsx}\n  sha256 {n.sha256} ({ok} the recorded file)")
    print(f"  {n.n_rows} data rows, {len(n.all_cues)} distinct cues, {len(n.features)} single-word cues")
    print(f"  single-word cues with >= 12 features: {len(n.with_features(12))}")
    print(f"  single-word cues with >= 16 features: {len(n.with_features(16))}")
    print(f"  of the single-word cues, {len(n.nouns())} carry pos_cue = noun")


if __name__ == "__main__":
    main()
