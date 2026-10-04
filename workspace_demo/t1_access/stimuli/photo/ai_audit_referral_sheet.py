"""Image audit: the owner's referral sheets (no model, no reader). For every referral in the committed round scores -
failed primaries and failed candidates - the image EXACTLY as delivered (the item file, sha256-checked against its
request) with the reader's raw answers in question order, recorded before any owner decision (AI_AUDIT_JOB.md;
IMAGE_AUDIT_FREEZE.md "Referrals and candidate succession"). Writes PNG contact sheets and a markdown index.

    .venv-image/bin/python stimuli/photo/ai_audit_referral_sheet.py <out_dir> <k1> [<k2> ...]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_audit_set as S  # noqa: E402

TILE, CAP, COLS = 384, 118, 4


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rows(ks: list[int]) -> list[dict]:
    out = []
    for k in ks:
        sc = json.loads(S.score_path(k).read_text())
        sset = json.loads(S.set_path(k).read_text())
        files = {}
        for r in sset["requests"]:
            files.setdefault(r["item"], (r["file"], r["sha256"]))
        for item, it in sorted(sc["items"].items(), key=lambda x: (x[1]["kind"], x[1]["concept"])):
            if it["passed_by_reader"]:
                continue
            f, h = files[item]
            data = (S.ITEMS / f).read_bytes()
            if sha(data) != h:
                raise SystemExit(f"refused: {f} differs from its request")
            a = it["answers"]
            out.append({"round": k, "item": item, "kind": it["kind"], "concept": it["concept"], "rank": it["rank"],
                        "file": f, "sha256": h, "reasons": it["reasons"],
                        "answers": {q: (a[q] or {}).get("raw") for q in a},
                        "rules": {q: (a[q] or {}).get("rule") for q in a if (a[q] or {}).get("rule")}})
    return out


def sheet(rs: list[dict], path: Path, title: str) -> None:
    n = len(rs)
    h = (n + COLS - 1) // COLS
    img = Image.new("RGB", (COLS * TILE, 40 + h * (TILE + CAP)), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
        big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    except OSError:
        font = big = ImageFont.load_default()
    d.text((10, 8), title, fill="black", font=big)
    for i, r in enumerate(rs):
        x, y = (i % COLS) * TILE, 40 + (i // COLS) * (TILE + CAP)
        img.paste(Image.open(S.ITEMS / r["file"]).convert("RGB"), (x, y))
        a = r["answers"]
        lines = [f"{i + 1}. {r['concept'].upper()} - {r['kind']}" + (f" rank {r['rank']}" if r["rank"] else "")
                 + f" (round {r['round']})",
                 f"name: {a.get('name')!r}" + (f"  [{r['rules'].get('name')}]" if r["rules"].get("name") else ""),
                 f"photo: {a.get('photograph')}   sense: {a.get('sense')}" +
                 (f"   distinct: {a.get('distinct')}" if "distinct" in a else ""),
                 "failed: " + ", ".join(r["reasons"])]
        for j, line in enumerate(lines):
            d.text((x + 6, y + TILE + 6 + j * 26), line[:52], fill="black", font=font)
    img.save(path)


def main(out: Path, ks: list[int]) -> int:
    out.mkdir(parents=True, exist_ok=True)
    rs = rows(ks)
    prim = [r for r in rs if r["kind"] == "primary"]
    cand = [r for r in rs if r["kind"] == "candidate"]
    sheet(prim, out / "primaries.png", f"Failed PRIMARY views ({len(prim)}): pass, or fail (replace / hold)")
    for i in range(0, len(cand), 16):
        sheet(cand[i:i + 16], out / f"candidates_{i // 16 + 1}.png",
              f"Failed second-view CANDIDATES {i + 1}-{min(i + 16, len(cand))} of {len(cand)} (left: the image the "
              f"reader saw; distinct = the side-by-side pair)")
    (out / "referrals.json").write_text(json.dumps(rs, indent=1, ensure_ascii=False) + "\n")
    print(len(prim), "primaries,", len(cand), "candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), [int(x) for x in sys.argv[2:]]))
