"""Row 19 screen on EC2, production: derive the EC2 operational manifest for one partition epoch from the production screen
manifest 43b75f94, changing ONLY operational fields (Codex f3dd3d7 contract 3). The scientific projection (setting,
datasets, seeds, identities, cfg incl. B = 200, code and environment pins, anchors) is copied unchanged; the canonical
Lengau task bindings are never touched (the EC2 instance binds its own local root).

    python3 make_prod_manifest.py --epoch 1 --expect-s <measured> --out prod/manifest_e1.json

--expect-s is the reviewed first-dispatch expectation, taken from row 23's MEASURED paired walls (not assumed); the
instance lifetime is then expect + 900 s setup + 3,000 s upload/cleanup reserve."""
import argparse, hashlib, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.join(HERE, "..", "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
import prod_authority as PA


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epoch", type=int, required=True); ap.add_argument("--expect-s", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert hashlib.sha256(open(PROD, "rb").read()).hexdigest() == PROD_SHA
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists: an epoch's operational manifest is immutable")
    m = json.load(open(PROD))
    m["storage"] = {"root": f"/mnt/prod/root", "campaign": f"/mnt/prod/campaign"}
    m["pbs"]["cores"] = PA.WORKERS_PER_INSTANCE
    m["shard"]["expect_layer_s"] = int(a.expect_s)
    m["shard"]["expect_note"] = f"EC2 production epoch {a.epoch}: first-dispatch expectation from row 23's measured paired walls"
    m["ec2_production"] = {"epoch": a.epoch, "derived_from_sha256": PROD_SHA, "profile": "B_full",
                           "changed": ["storage.root", "storage.campaign", "pbs.cores", "shard.expect_layer_s", "shard.expect_note", "ec2_production"],
                           "lifetime_s": int(a.expect_s) + 900 + 3000}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(m, open(a.out, "w"), indent=1, sort_keys=True)
    print(a.out, hashlib.sha256(open(a.out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
