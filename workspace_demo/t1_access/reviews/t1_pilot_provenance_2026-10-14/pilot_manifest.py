"""Provenance manifest of the 16 Sept 2026 development pilot (SI Section 6.5 / S6), read-only.

The pilot's captures (captures/pilot_cal, captures/pilot_pilot; about 1.7 GB each of residual-stream arrays) are kept
out of git by captures/.gitignore. This script copies each capture run's header (model id, per-file model SHA-256s,
lens SHA-256, runtime, capture-code hashes) beside itself and records the size and SHA-256 of every capture file, so
the tracked outputs (decoders/pilot_cal/, validation/pilot_pilot/) are tied to the exact inputs that produced them.

Run: python3 pilot_manifest.py   (writes run_header_<split>.json and pilot_manifest.json beside it)
"""
import hashlib
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.normpath(os.path.join(HERE, "..", ".."))
CAPTURES = ("pilot_cal", "pilot_pilot")
OUTPUTS = ("decoders/pilot_cal/decode_cal.json", "decoders/pilot_cal/decoders.npz",
           "validation/pilot_pilot/report.json", "validation/pilot_pilot/scores.npz",
           "validation/pilot_pilot/assay_layer41.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main():
    out = {"captures": {}, "outputs": {}}
    for split in CAPTURES:
        d = os.path.join(T1, "captures", split)
        shutil.copyfile(os.path.join(d, "run_header.json"), os.path.join(HERE, f"run_header_{split}.json"))
        hdr = json.load(open(os.path.join(d, "run_header.json")))
        ident = hdr["provenance"]["server"]["identity"]
        out["captures"][split] = {
            "model_id": ident["model_id"],
            "model_safetensors_sha256": {k: v for k, v in ident["model_files_sha256"].items() if k.endswith(".safetensors")},
            "lens_sha256": ident["lens_sha256"],
            "n_layers": ident["n_layers"], "d_model": ident["d_model"],
            "selection": hdr["identity"]["selection"],
            "files": {f: {"bytes": os.path.getsize(os.path.join(d, f)), "sha256": sha256(os.path.join(d, f))}
                      for f in sorted(os.listdir(d)) if not f.startswith(".")},
        }
    for rel in OUTPUTS:
        p = os.path.join(T1, rel)
        out["outputs"][rel] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
    with open(os.path.join(HERE, "pilot_manifest.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for split, c in out["captures"].items():
        print(split, c["model_id"], "lens", c["lens_sha256"][:16], c["selection"], len(c["files"]), "files")
    print("outputs:", ", ".join(f"{k} {v['sha256'][:12]}" for k, v in out["outputs"].items()))


if __name__ == "__main__":
    main()
