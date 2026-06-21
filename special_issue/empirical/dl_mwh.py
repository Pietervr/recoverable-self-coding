import os
import urllib.request

SNAP = "2026-05"
BASE = f"https://dumps.wikimedia.org/other/mediawiki_history/{SNAP}"
OUT = "/tmp/mwh"
os.makedirs(OUT, exist_ok=True)
CAP = 48_000_000  # bytes; keep the probe light

# spread of small/medium language editions (codes); big ones get skipped by CAP
WIKIS = ["gotwiki", "iuwiki", "nvwiki", "cowiki", "lawiki", "fywiki", "scowiki",
         "anwiki", "barwiki", "gdwiki", "gvwiki", "kwwiki", "tlwiki", "nnwiki",
         "afwiki", "iswiki", "scnwiki", "liwiki", "vecwiki", "wawiki"]


def size_of(url):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return int(r.headers.get("Content-Length", 0))
    except Exception as e:
        return -1


for w in WIKIS:
    dest = f"{OUT}/{w}.tsv.bz2"
    url = f"{BASE}/{w}/{SNAP}.{w}.all-time.tsv.bz2"
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"have   {w} ({os.path.getsize(dest)} b)")
        continue
    sz = size_of(url)
    if sz < 0:
        print(f"skip   {w} (no all-time file / split wiki)")
        continue
    if sz > CAP:
        print(f"skip   {w} ({sz} b > cap)")
        continue
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"DL     {w} ({os.path.getsize(dest)} b)")
    except Exception as e:
        print(f"FAIL   {w}: {e}")

print("--- downloaded ---")
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
