"""Photograph arm, desk gate ask 1b: Stage B second-view CANDIDATES per development concept (framework §8.2).

A second view must be a genuine second photograph of the concept, individually released CC0 or documented public
domain; a crop or flip of the primary is not one. Wikimedia Commons is a platform, not a licence, so candidates are
taken only from files whose OWN structured data states the licence: copyright licence (P275) = CC0 (Q6938433), or
copyright status (P6216) = public domain (Q19652). Bitmap files only, shorter side >= 384 px (the canvas).

ORDER (declared, no model involved): Commons search relevance for the concept's name, CC0 results first, then PD;
up to N candidates kept per concept with title, file page and media URLs, licence short name, artist, credit, size,
and the date read. Commons search also returns artworks, drawings, scenes and look-alikes; it cannot certify "a
photograph of this concept, distinct from the primary view". The second view is therefore the FIRST candidate in
this order that the image and sense audit accepts as (a) a photograph, (b) of the concept in its THINGS sense, (c) a
different photograph from the THINGSplus primary (not the same shot, crop or flip). An audit rejection moves to the
next candidate; a concept with no accepted candidate holds Stage B (framework §8.2). Network: the Commons API only.

DECLARED EXCLUSION before the audit: a title naming an artwork medium or a museum (NOT_PHOTO below) is dropped as not a
photograph. Under the capture gate (framework §8.2, option A) an accepted second view still needs its own per-image
check before any capture: the Commons file page's licence suffices for an own-work upload; a file credited to another
site (Pixabay, Flickr, Unsplash, ...) is checked at that original, recorded in provenance_checks.json.

    python3 stimuli/photo/second_views.py
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://commons.wikimedia.org/w/api.php"
UA = "R084-T1-research/1.0 (Recoverable-Self-Coding; contact via repository owner)"
N = 8
NOT_PHOTO = re.compile(r"painting|drawing|illustration|engraving|lithograph|woodcut|etching|sketch|watercolou?r|"
                       r"\bprint\b|museum|\bMET\b|\bDP\d|rijksmuseum|plate \d|sculpture|statue|\bicon\b|"
                       r"\blogo\b|diagram|\bmap\b|stamp", re.I)
STATEMENTS = [("CC0", "haswbstatement:P275=Q6938433"), ("PD", "haswbstatement:P6216=Q19652")]


def query(term: str, statement: str) -> list[dict]:
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 20,
              "gsrsearch": f"{term} {statement} filetype:bitmap", "prop": "imageinfo",
              "iiprop": "url|size|extmetadata",
              "iiextmetadatafilter": "LicenseShortName|Artist|Credit|DateTimeOriginal|ImageDescription"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    for wait in (5, 15, 45, 90, None):                # back off on HTTP 429 (Commons rate limit)
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                d = json.load(f)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {})
        out.append({"title": p["title"], "page_url": ii.get("descriptionurl"), "media_url": ii.get("url"),
                    "width": ii.get("width"), "height": ii.get("height"),
                    "licence": em.get("LicenseShortName", {}).get("value"),
                    "artist": em.get("Artist", {}).get("value"), "credit": em.get("Credit", {}).get("value"),
                    "date_original": em.get("DateTimeOriginal", {}).get("value")})
    return out


def main() -> int:
    pool = json.loads((HERE / "dev_pool.json").read_text())
    result = {"note": __doc__.split("\n\n")[0], "read": time.strftime("%Y-%m-%d"), "per_concept_max": N,
              "statements": dict(STATEMENTS), "concepts": {}}
    for r in pool["roles"]:
        seen, cands = set(), []
        for basis, st in STATEMENTS:
            for c in query(r["concept"], st):
                if c["title"] in seen or min(c["width"] or 0, c["height"] or 0) < 384 or NOT_PHOTO.search(c["title"]):
                    continue
                seen.add(c["title"])
                credit = re.sub("<[^>]+>", "", c["credit"] or "").strip()
                cands.append({**c, "credit": credit[:300], "basis": basis,
                              "own_work": "own work" in credit.lower(),
                              "credited_elsewhere": re.findall(r"pixabay|flickr|unsplash|pexels|stocksnap", credit, re.I)})
            time.sleep(1.5)
        result["concepts"][r["concept"]] = {"family": r["family"], "role": r["role"],
                                            "n_candidates": len(cands[:N]), "candidates": cands[:N]}
        print(f"{r['concept']:<11} {len(cands[:N])} candidates  first: {cands[0]['title'] if cands else '-'}")
    (HERE / "second_view_candidates.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    short = [k for k, v in result["concepts"].items() if v["n_candidates"] == 0]
    print("concepts with no candidate:", short or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
