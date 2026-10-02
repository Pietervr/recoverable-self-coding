"""Photograph arm, desk gate: the per-photo manifest of framework §8.2 for the 32 development roles (P = 1 so far:
the THINGSplus primary view; the Stage B second view is added when found and cleared).

TERMS (framework §8.2 as decided by R052, handoffs 41b67d26 and a89ddc24 - option A): BOTH field sets per image.
  release   the THINGSplus release fields: zip, notice and LICENSE hashes, OSF ids, the download date, the file and
            its hash, the misattribution caveat, and "creator / original URL: not supplied by the release";
  check     "found by the per-image check, <date>" (provenance_checks.json): source URL, creator, published date, the
            licence line read and its basis, status. The check GATES CAPTURE as well as publication: an image enters
            any capture only when its check is 'eligible' (CC0 or documented PD at source; Pixabay: published before
            2019-01-09). The collective grant alone admits nothing. Unchecked reads "pending (before row 21)".
Fields that exist only at capture time (dose nonce, trial positions, delivered tensor per trial) are marked as
assigned at capture; the clean-canvas pixel hashes and geometry are computed here, pixels only, no model.

    .venv-image/bin/python stimuli/photo/manifest.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dose  # noqa: E402
from dose_report import processor  # noqa: E402

THINGS = Path.home() / "things-plus"
IMAGES = THINGS / "cc0" / "object_images_CC0"
RELEASE = {
    "zip": {"name": "images_THINGSplus-CC0.zip", "osf": "jum2f", "bytes": 1177368548,
            "sha256": "ed86912f6848ac5cf8b405a727f875295cc081cdd64271e80ae4d607b7d447e3"},
    "notice": {"osf": "ahg2k", "sha256": "bdda43a819803658fb0e3611cdfa571a2b2dc2f3a3429617a4cf1169ace1e69e",
               "quote": "We provide the THINGS+ public domain images for any purpose without restriction under "
                        "copyright or database law ... At the time of downloading, all images had a public domain/CC0 "
                        "license"},
    "license": {"osf": "52wrx", "sha256": "de570769b5545d7b9a7f9165b9da691370fa680330a8b2bf73cd9368ba1dbc97",
                "quote": "The THINGSplus images ... have a CC0 license"},
    "downloaded": "2026-10-01",
    "misattribution_caveat": "the notice reports rights status at collection and acknowledges possible "
                             "misattribution, with a take-down route",
    "creator": "not supplied by the release", "original_url": "not supplied by the release",
    "per_image_provenance_in_release": "none (zip of square-cropped derivatives, EXIF stripped)",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    pool = json.loads((HERE / "dev_pool.json").read_text())
    checks = {c["concept"]: c for c in json.loads((HERE / "provenance_checks.json").read_text())["checks"]}
    proc = processor()
    code = {n: sha((HERE / n).read_bytes()) for n in ("dose.py", "dose_report.py", "pool.py", "image_adapter.py",
                                                       "manifest.py")}
    import image_adapter
    import mlx_vlm
    identity = {"code_sha256": code, "template_sha256": image_adapter.template_sha256(),
                "processor": {"class": type(proc).__name__, "mlx_vlm": mlx_vlm.__version__,
                              "config": "snapshot c000ac2c preprocessor_config.json"},
                "pillow": Image.__version__, "numpy": np.__version__,
                "dev_pool_sha256": sha((HERE / "dev_pool.json").read_bytes()),
                "provenance_checks_sha256": sha((HERE / "provenance_checks.json").read_bytes())}
    records = []
    for r in pool["roles"]:
        path = IMAGES / r["thingsplus_image"]
        raw = path.read_bytes()
        canvas, geom = dose.load_canvas(path)
        S = dose.signal(dose.luma(canvas))
        rgb8, clip = dose.quantise(dose.mix(S, np.zeros_like(S), 1.0))
        png = dose.to_png(rgb8)
        out = proc(images=[Image.open(io.BytesIO(png)).convert("RGB")], return_tensors="np")
        c = checks.get(r["concept"])
        if c is None:
            check = {"status": "pending (before row 21)"}
            publish = "not admitted: per-image check pending"
        else:
            check = {"label": f"found by the per-image check, {c['checked']}",
                     **{k: c[k] for k in ("status", "checked", "source_url", "creator", "published", "licence_shown",
                                          "licence_basis", "tineye_results", "notes")},
                     "stock_matches": c.get("stock_matches"),          # null = unrecorded, never zero
                     "stock_comparison": c.get("stock_comparison")}    # the dated comparison (framework 8.2)
            for k in ("creator", "published"):                          # a missing field keeps its actual basis
                if c.get(k) in (None, "", "-"):
                    check[k] = f"not shown at the source checked ({c['source_url']}), {c['checked']}"
            basis = c.get("licence_basis") or ""
            at_source = ("CC0 at source" if basis.startswith("CC0") else
                         f"public domain at source ({basis})" if basis.lower().startswith("public domain") else basis)
            publish = {"eligible": f"publishable with the source record ({at_source})",
                       "not_found": "by reference only (filename and hash), never redistributed",
                       "ineligible": "not publishable; replaced"}[c["status"]]
        records.append({
            "concept": r["concept"], "synset": r["synset"], "wnid": r["wnid"], "family": r["family"],
            "e1_token_id": r["e1_token_id"], "role": r["role"], "stage_a_primary_view": r["stage_a_primary_view"],
            "replaces": r.get("replaces"),
            "photo_id": f"thingsplus:{r['thingsplus_image']}", "source_group_id": f"thingsplus-primary:{r['concept']}",
            "view": "THINGSplus primary view (view 1); Stage B second view: search pending",
            "release_basis": "THINGSplus release fields (see 'release'); admission is by the per-image check",
            "release_file": r["thingsplus_image"], "original_bytes": len(raw), "original_sha256": sha(raw),
            "per_image_check": check,
            "permission": {"capture_and_transformation": "yes" if c and c["status"] == "eligible" else
                           "no: not admitted until the per-image check is eligible",
                           "publication_and_redistribution": publish},
            "operations": geom, "clean_canvas": {"png_sha256": sha(png), "clip": clip,
                                                 "processed_tensor_sha256": sha(np.ascontiguousarray(
                                                     np.asarray(out["pixel_values"], dtype=np.float32)).tobytes()),
                                                 "grid_thw": np.asarray(out["image_grid_thw"]).tolist()[0]},
            "capture_time_fields": "dose nonce, mask draws, trial positions and delivered tensors are assigned and "
                                   "hashed per trial at capture (row 20/21 schedules), not here",
            "image_and_sense_audit": "pending: the grayscale normalised clean stimulus, by the AI image reader once "
                                     "qualified against THINGSplus norms, the owner deciding referrals (framework "
                                     "8.2, owner 2 Oct 2026)",
            "recognizability_at_source": r["recognizability"], "raters_most_common_label": r["most_common_label"],
        })
    manifest = {"note": __doc__.split("\n\n")[0], "release": RELEASE, "execution_identity": identity,
                "n_records": len(records),
                "check_status_counts": {s: sum(1 for x in records if x["per_image_check"]["status"] == s)
                                        for s in ("eligible", "not_found", "ineligible", "pending (before row 21)")},
                "records": records}
    (HERE / "manifest_dev.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(manifest["check_status_counts"]), len(records), "records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
