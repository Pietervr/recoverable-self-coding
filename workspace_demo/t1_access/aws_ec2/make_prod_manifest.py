"""Row 19 screen on EC2: derive the EC2 operational manifest for one partition epoch and instance contract from the
production screen manifest 43b75f94, changing ONLY operational fields (Codex f3dd3d7 contract 3; V10-1: the derivation is
row19_ec2_state.derive_operational, which the launcher and the Lengau ingestion re-run and compare byte for byte). The
scientific projection (setting, datasets, seeds, identities, cfg incl. B = 200, code and environment pins, anchors) is
copied unchanged; the canonical Lengau task bindings are never touched (the EC2 instance binds its own local root).

    python3 make_prod_manifest.py --epoch 1 --contract Q1 --expect-s 75300 --out prod/manifest_q1_e1.json
    python3 make_prod_manifest.py --epoch 2 --contract production --expect-s 75300 --out prod/manifest_production_e2.json
    python3 make_prod_manifest.py --epoch 2 --contract E2Q1 --expect-s 75300 --out prod/manifest_e2q1_e2.json \
        --partition ../chpc/row19_partition_e2.json --snapshot ../chpc/claims_snapshot_e2.json --panel-out prod/panel_e2q_e2.json
    python3 make_prod_manifest.py --epoch 2 --contract E2Q2 --expect-s 75300 --out prod/manifest_e2q2_e2.json \
        --partition ../chpc/row19_partition_e2.json --snapshot ../chpc/claims_snapshot_e2.json --panel-out prod/panel_e2q_e2.json

--expect-s is the reviewed first-dispatch expectation, taken from row 23's MEASURED paired walls (not assumed); the
instance lifetime is then expect + 900 s setup + 3,000 s upload/cleanup reserve. Q1 and Q2 are declared at a 22 h lifetime
(expect 75,300 s), which the launcher enforces.

REVISION 2 - CANDIDATE, not adopted (EC2 provider epoch 2; Codex design reviews/2026-10-17_row19_resize_codex.md s.3). The
epoch-2 production manifest is the funded geometry and nothing else: contract `production` (c7a.24xlarge, 76 workers = 72
work + 4 sentinels, spot cap 1.20) at the 22 h lifetime the design's funding formula uses (46 x [22.75 x (1.20 + 0.014) +
0.30]); any other expectation for epoch >= 2 is refused, because the per-batch worst case and the funding declaration
(make_e2_funding.py) are computed at that lifetime. Q1 ran 21.28 h at the 76-worker packing (qual-Q1 attempt 4), inside it.

REVISION 3 - CANDIDATE, not adopted (EC2 provider epoch 2 QUALIFICATION, chpc/candidate_e2q/DESIGN_e2q.md;
chpc/candidate_e2/QUALIFICATION_E2.md s.2). The E2Q1 and conditional E2Q2 contracts (row19_ec2_state REVISION 4: the
production geometry with roles 52 work + 20 Lengau duplicates + 4 sentinels) are admitted for epoch 2 at the same funded
lifetime. Their operational manifests do not depend on the partition (derive_operational of 43b75f94 only), but the panel
does: an E2Q contract therefore REQUIRES --partition and --snapshot (the claims snapshot the partition binds by sha256), and
the maker also writes the declared fixed panel (row19_ec2_e2qual.derive_panel) to --panel-out, binding the partition and the
snapshot. An existing panel file is never overwritten: it must already be the identical derivation (the E2Q2 run of the
maker re-derives the same panel and checks it), otherwise the maker refuses. When the partition is regenerated (fresh
post-v16 snapshot), the panel MUST be regenerated with it; the two operational manifests need not be.

REVISION 4 (owner decision 21 Oct 2026, R052 "On-demand E2Q3"; chpc/candidate_v19_oploss/DESIGN_v19.md s.7). Contract E2Q3
(row19_ec2_state REVISION 5, controls v19) is admitted for epoch 2 at the same funded lifetime with the identical geometry and
roles, purchased ON-DEMAND at the worst-case rate 5.60 (E2Q3_GEOMETRY); its maker run re-derives and accepts the same declared
panel. Every other contract's check is unchanged. Before controls v19 is promoted the live row19_ec2_state has no E2Q3, so
--contract E2Q3 is not a choice (the manifest is built from the v19 candidate and promoted with it).

    python3 make_prod_manifest.py --epoch 2 --contract E2Q3 --expect-s 75300 --out prod/manifest_e2q3_e2.json \
        --partition ../chpc/row19_partition_e2.json --snapshot ../chpc/claims_snapshot_e2.json --panel-out prod/panel_e2q_e2.json"""
import argparse, hashlib, json, os, sys
SRC = os.path.dirname(os.path.abspath(__file__))
T1 = SRC
while os.path.basename(T1) != "t1_access":
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{SRC} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
CAND = os.path.dirname(SRC) if os.path.basename(os.path.dirname(SRC)).startswith("candidate_") else os.path.join(T1, "chpc")
_PATH = [os.path.join(T1, "chpc")] + ([os.path.join(T1, "chpc", "candidate_e2")] if CAND != os.path.join(T1, "chpc") else []) + [CAND]
for _p in _PATH:                                       # CAND last inserted = first searched (the E2Q state contracts)
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)
import row19_ec2_state as ES
import row19_ec2_e2qual as EQ
PROD = os.path.join(T1, "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
E2_EXPECT_S = 75300                                    # 79,200 s lifetime - 900 s setup - 3,000 s upload reserve
E2_GEOMETRY = dict(itype="c7a.24xlarge", workers=76, max_price=1.20, roles={"work": None, "sentinel": 4})
E2Q_GEOMETRY = dict(itype="c7a.24xlarge", workers=76, max_price=1.20, roles={"work": 52, "qual_lengau": 20, "sentinel": 4})
E2Q3_GEOMETRY = dict(E2Q_GEOMETRY, max_price=5.60, market="on-demand")     # REVISION 4: the same geometry on-demand


def epoch2_problem(epoch, contract, expect_s):
    """'' unless an epoch >= 2 manifest departs from the funded geometry and lifetime (production or an E2Q contract)."""
    if int(epoch) < 2:
        return ""
    if contract not in ("production",) + EQ.CONTRACTS:
        return f"epoch {epoch}: only the production and the E2Q qualification contracts ({', '.join(EQ.CONTRACTS)}) are declared"
    if contract in EQ.CONTRACTS and int(epoch) != EQ.EPOCH:
        return f"the E2Q contracts qualify epoch {EQ.EPOCH} only"
    c = ES.CONTRACTS[contract]
    want = E2_GEOMETRY if contract == "production" else E2Q3_GEOMETRY if contract == "E2Q3" else E2Q_GEOMETRY
    if {k: c.get(k) for k in want} != want or (contract != "E2Q3" and "market" in c):
        return f"the {contract} contract {c} is not the funded 76-worker geometry {want}"
    if int(expect_s) != E2_EXPECT_S:
        return f"epoch {epoch}: expect {expect_s} s is not the funded 22 h lifetime's {E2_EXPECT_S} s"
    return ""


def rel_to_t1(p):
    """A path recorded in the panel: relative to t1_access when inside it, else absolute (sandboxes, tests)."""
    ap = os.path.abspath(p); rp = os.path.relpath(ap, T1)
    return ap if rp.startswith("..") else rp


def build_panel(partition, snapshot, man, man_sha):
    """(panel bytes) derived from the partition file and its bound claims snapshot (row19_ec2_e2qual.derive_panel); the
    partition is validated structurally (row19_partition.load) first."""
    import row19_partition as RP
    part = RP.load(partition, man, man_sha)
    snap = json.load(open(snapshot))
    panel = EQ.derive_panel(part, RP.sha_file(partition), snap, RP.sha_file(snapshot), rel_to_t1(snapshot))
    return EQ.panel_bytes(panel)


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--epoch", type=int, required=True); ap.add_argument("--expect-s", type=int, required=True)
    ap.add_argument("--contract", choices=sorted(ES.CONTRACTS), required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--partition"); ap.add_argument("--snapshot"); ap.add_argument("--panel-out")
    ap.add_argument("--designated", default=None, help="override of the designated declaration path (before v16 promotion)")
    a = ap.parse_args(argv)
    assert hashlib.sha256(open(PROD, "rb").read()).hexdigest() == PROD_SHA
    why = epoch2_problem(a.epoch, a.contract, a.expect_s)
    if why:
        raise SystemExit(f"REFUSED: {why}")
    man = json.load(open(PROD))
    panel = None
    if a.contract in EQ.CONTRACTS:
        if not (a.partition and a.snapshot and a.panel_out):
            raise SystemExit("REFUSED: an E2Q contract needs --partition, --snapshot and --panel-out (the panel binds the partition)")
        if a.designated:
            import row19_partition as RP
            RP.DESIGNATED_PATH = os.path.abspath(a.designated)
        try:
            panel = build_panel(a.partition, a.snapshot, man, PROD_SHA)
        except ValueError as e:
            raise SystemExit(f"REFUSED: {e}")
        if os.path.exists(a.panel_out) and open(a.panel_out, "rb").read() != panel:
            raise SystemExit(f"REFUSED: {a.panel_out} exists with other bytes: a declared panel is immutable (regenerate it with its partition)")
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists: an epoch's operational manifest is immutable")
    m = ES.derive_operational(man, PROD_SHA, a.epoch, a.expect_s, a.contract)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(m, open(a.out, "w"), indent=1, sort_keys=True)
    print(a.out, hashlib.sha256(open(a.out, "rb").read()).hexdigest())
    if panel is not None and not os.path.exists(a.panel_out):
        os.makedirs(os.path.dirname(os.path.abspath(a.panel_out)), exist_ok=True)
        open(a.panel_out, "wb").write(panel)
    if panel is not None:
        print(a.panel_out, hashlib.sha256(panel).hexdigest())


if __name__ == "__main__":
    main()
