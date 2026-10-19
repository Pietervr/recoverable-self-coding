"""Row 19 screen on EC2: derive the EC2 operational manifest for one partition epoch and instance contract from the
production screen manifest 43b75f94, changing ONLY operational fields (Codex f3dd3d7 contract 3; V10-1: the derivation is
row19_ec2_state.derive_operational, which the launcher and the Lengau ingestion re-run and compare byte for byte). The
scientific projection (setting, datasets, seeds, identities, cfg incl. B = 200, code and environment pins, anchors) is
copied unchanged; the canonical Lengau task bindings are never touched (the EC2 instance binds its own local root).

    python3 make_prod_manifest.py --epoch 1 --contract Q1 --expect-s 75300 --out prod/manifest_q1_e1.json
    python3 make_prod_manifest.py --epoch 1 --contract production --expect-s <measured> --out prod/manifest_e1.json

--expect-s is the reviewed first-dispatch expectation, taken from row 23's MEASURED paired walls (not assumed); the
instance lifetime is then expect + 900 s setup + 3,000 s upload/cleanup reserve. Q1 and Q2 are declared at a 22 h lifetime
(expect 75,300 s), which the launcher enforces."""
import argparse, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "chpc"))
import row19_ec2_state as ES
PROD = os.path.join(HERE, "..", "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epoch", type=int, required=True); ap.add_argument("--expect-s", type=int, required=True)
    ap.add_argument("--contract", choices=sorted(ES.CONTRACTS), required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert hashlib.sha256(open(PROD, "rb").read()).hexdigest() == PROD_SHA
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists: an epoch's operational manifest is immutable")
    m = ES.derive_operational(json.load(open(PROD)), PROD_SHA, a.epoch, a.expect_s, a.contract)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(m, open(a.out, "w"), indent=1, sort_keys=True)
    print(a.out, hashlib.sha256(open(a.out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
