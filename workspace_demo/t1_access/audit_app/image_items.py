"""Image items for the photograph-arm image and sense audit (framework §8.2; R052 handoff d0db04cb).

Readers judge the ACTUAL stimulus: the grayscale, normalised clean canvas the model sees (dose pipeline, a = 1),
written byte for byte as public/img/<opaque id>.png. Its sha256 must equal manifest_dev.json's clean_canvas.png_sha256,
and the script asserts it. Each item carries the THINGS sense the concept is qualified under. The four questions, in this order on the page (images.html):
  ph     is it a photograph?                                                  y | n
  name   the main thing in one word, typed (w), or "I can't tell"             y (w = the word) | n
  sense  does it show <name> in the sense "<THINGS definition>"?              y | n | ?
         - hidden until 'name' is answered, so the naming is not primed by the concept's word
  dist   (second-view items only) a different photograph from the primary,
         not a crop or flip of it?                                            y | n
The model under test never sees these answers' inputs nor filters them.

    ../.venv-image/bin/python image_items.py --set stagea     # the Stage A eight (the pilot)
    ../.venv-image/bin/python image_items.py --set all        # all 32 primary views
Then push.py picks image_items.json up as part I.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHOTO = HERE.parent / "stimuli" / "photo"
sys.path.insert(0, str(PHOTO))
import dose  # noqa: E402

THINGS = Path.home() / "things-plus"


def definitions() -> dict:
    with open(THINGS / "_concepts-metadata_things.tsv", newline="", encoding="utf-8") as f:
        return {r["uniqueID"]: r["Definition (from WordNet, Google, or Wikipedia)"].strip()
                for r in csv.DictReader(f, delimiter="\t")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["stagea", "all"], required=True)
    a = ap.parse_args()
    pool = json.loads((PHOTO / "dev_pool.json").read_text())
    manifest = {r["concept"]: r for r in json.loads((PHOTO / "manifest_dev.json").read_text())["records"]}
    defs = definitions()
    roles = [r for r in pool["roles"] if a.set == "all" or r["stage_a_primary_view"]]
    out_dir = HERE / "public" / "img"
    out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for r in sorted(roles, key=lambda r: (r["family"], r["concept"])):
        assert manifest[r["concept"]]["per_image_check"]["status"] == "eligible", r["concept"]
        canvas, _ = dose.load_canvas(THINGS / "cc0" / "object_images_CC0" / r["thingsplus_image"])
        S = dose.signal(dose.luma(canvas))
        rgb8, _ = dose.quantise(dose.mix(S, S * 0.0, 1.0))
        png = dose.to_png(rgb8)
        h = hashlib.sha256(png).hexdigest()
        assert h == manifest[r["concept"]]["clean_canvas"]["png_sha256"], f"{r['concept']}: not the manifest's canvas"
        # Opaque id and file name (repair 18, Codex f9d2ef3): neither the URL nor the item id names the concept.
        op = hashlib.sha256(f"audit-img|{r['concept']}|v1".encode()).hexdigest()[:12]
        (out_dir / f"{op}.png").write_bytes(png)
        items.append({"id": f"i-{op}", "kind": "image",
                      "body": {"key": op, "concept": r["concept"], "family": r["family"],
                               "definition": defs[r["concept"]], "img": f"/img/{op}.png",
                               "png_sha256": h, "view": "primary", "second": None}})
    (HERE / "image_items.json").write_text(json.dumps({"set": a.set, "items": items}, indent=1) + "\n")
    print(len(items), "image items:", ", ".join(i["body"]["concept"] for i in items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
