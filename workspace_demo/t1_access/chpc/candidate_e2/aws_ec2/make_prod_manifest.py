"""Row 19 screen on EC2: derive the EC2 operational manifest for one partition epoch and instance contract from the
production screen manifest 43b75f94, changing ONLY operational fields (Codex f3dd3d7 contract 3; V10-1: the derivation is
row19_ec2_state.derive_operational, which the launcher and the Lengau ingestion re-run and compare byte for byte). The
scientific projection (setting, datasets, seeds, identities, cfg incl. B = 200, code and environment pins, anchors) is
copied unchanged; the canonical Lengau task bindings are never touched (the EC2 instance binds its own local root).

    python3 make_prod_manifest.py --epoch 1 --contract Q1 --expect-s 75300 --out prod/manifest_q1_e1.json
    python3 make_prod_manifest.py --epoch 2 --contract production --expect-s 75300 --out prod/manifest_production_e2.json

--expect-s is the reviewed first-dispatch expectation, taken from row 23's MEASURED paired walls (not assumed); the
instance lifetime is then expect + 900 s setup + 3,000 s upload/cleanup reserve. Q1 and Q2 are declared at a 22 h lifetime
(expect 75,300 s), which the launcher enforces.

REVISION 2 - CANDIDATE, not adopted (EC2 provider epoch 2; Codex design reviews/2026-10-17_row19_resize_codex.md s.3). The
epoch-2 production manifest is the funded geometry and nothing else: contract `production` (c7a.24xlarge, 76 workers = 72
work + 4 sentinels, spot cap 1.20) at the 22 h lifetime the design's funding formula uses (46 x [22.75 x (1.20 + 0.014) +
0.30]); any other expectation for epoch >= 2 is refused, because the per-batch worst case and the funding declaration
(make_e2_funding.py) are computed at that lifetime. Q1 ran 21.28 h at the 76-worker packing (qual-Q1 attempt 4), inside it."""
import argparse, hashlib, json, os, sys
SRC = os.path.dirname(os.path.abspath(__file__))
T1 = SRC
while os.path.basename(T1) != "t1_access":
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{SRC} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
sys.path.insert(0, os.path.join(T1, "chpc"))
import row19_ec2_state as ES
PROD = os.path.join(T1, "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
E2_EXPECT_S = 75300                                    # 79,200 s lifetime - 900 s setup - 3,000 s upload reserve
E2_GEOMETRY = dict(itype="c7a.24xlarge", workers=76, max_price=1.20, roles={"work": None, "sentinel": 4})


def epoch2_problem(epoch, contract, expect_s):
    """'' unless an epoch >= 2 production manifest departs from the funded geometry and lifetime."""
    if int(epoch) < 2:
        return ""
    if contract != "production":
        return f"epoch {epoch}: only the production contract is declared here (epoch-2 qualification contracts are not built)"
    c = ES.CONTRACTS["production"]
    if {k: c[k] for k in E2_GEOMETRY} != E2_GEOMETRY:
        return f"the production contract {c} is not the funded 76-worker geometry {E2_GEOMETRY}"
    if int(expect_s) != E2_EXPECT_S:
        return f"epoch {epoch}: expect {expect_s} s is not the funded 22 h lifetime's {E2_EXPECT_S} s"
    return ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epoch", type=int, required=True); ap.add_argument("--expect-s", type=int, required=True)
    ap.add_argument("--contract", choices=sorted(ES.CONTRACTS), required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert hashlib.sha256(open(PROD, "rb").read()).hexdigest() == PROD_SHA
    why = epoch2_problem(a.epoch, a.contract, a.expect_s)
    if why:
        raise SystemExit(f"REFUSED: {why}")
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists: an epoch's operational manifest is immutable")
    m = ES.derive_operational(json.load(open(PROD)), PROD_SHA, a.epoch, a.expect_s, a.contract)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(m, open(a.out, "w"), indent=1, sort_keys=True)
    print(a.out, hashlib.sha256(open(a.out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
