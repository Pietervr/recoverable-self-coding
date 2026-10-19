"""Controls v17 CANDIDATE (NOT adopted): build chpc/candidate_v17/row19_screen_controls.json and v17_promotion_map.json from the
ADOPTED v16 bytes and the reviewed candidate bytes, deterministically, and refuse unless every input is exactly the expected
file. Design: chpc/candidate_v17/DESIGN_v17.md. Nothing outside chpc/candidate_v17/ is written; nothing is promoted.

    python3 chpc/candidate_v17/build_v17.py            (from workspace_demo/t1_access; --check: rebuild in memory and compare)

v17 = adopted v16 (controls 01976b6a, adoption 523fe18a, Codex RSC f6896e1) with:
  - the partition pin: chpc/row19_partition_e1.json (8d1de408) -> chpc/row19_partition_e2.json (48cea639, the FINAL epoch-2
    declaration in chpc/e2_final/; e1 stays pinned by versions 13-16, unchanged, and is the e2 file's named predecessor);
  - the helpers: chpc/row19_partition.py, chpc/row19_ec2_ingest.py (candidate_e2, REVISION 6/7), chpc/row19_ec2_qualify.py,
    chpc/row19_ec2_state.py (candidate_e2q, REVISION 5 / REVISION 4); NEW chpc/row19_ec2_e2rules.py (candidate_e2) and
    chpc/row19_ec2_e2qual.py (candidate_e2q);
  - chpc/row19_screen_admit.py: the adopted v16 admission with candidate_e2/admit_v17_partition_line.diff applied (one print
    line) - chpc/candidate_v17/row19_screen_admit.py;
  - every other pin, sub_envelopes and qualification_S byte-equal to v16; versions 1-16 byte-identical to the adopted file."""
import copy, hashlib, json, os, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)

ADOPTED_CTL = ("chpc/row19_screen_controls.json", "01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220")
ADOPTED_ADOPTION = ("chpc/row19_screen_controls_adoption.json", "523fe18adad603af23425cdd4cb41039b4a287254e36aa55ba34d933b0081411")
ADMIT_DIFF = ("chpc/candidate_e2/admit_v17_partition_line.diff", "0fc23704b26269c18718f4f8d86430676ee2e90cef1c927f9ee59da31aa25067")
E1 = ("chpc/row19_partition_e1.json", "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608")

# (promoted path, source path, expected sha256 of the source = the v17 bytes, group)
#   pin      pinned in the v17 `files` (lineage: present at these bytes in every controller tree)
#   part     the v17 `partition` reference
#   data     deployed tracked data, bound transitively (the partition binds the snapshot; the qualifier/release bind the rest)
#   mac      Mac-only EC2 authority code (aws_ec2/), promoted with v17 (DESIGN_e2 s.6 step 5), not a controls pin
#   ctl      the controls file itself (promoted LAST)
MAP = [
    ("chpc/row19_screen_admit.py", "chpc/candidate_v17/row19_screen_admit.py", "c3960464db74a282f20da030008fb759a0fad4e1d4d3c7133c98f3b821d6b9ed", "pin"),
    ("chpc/row19_partition.py", "chpc/candidate_e2/row19_partition.py", "eabf50c34be2bad3f92e07370966bcc94162cf12cbcefb326cc07a72d49ac0d8", "pin"),
    ("chpc/row19_ec2_ingest.py", "chpc/candidate_e2/row19_ec2_ingest.py", "6ac144c616d330c83fcd5e665bdc48a9396d962e4aacba03c4775e26950ce108", "pin"),
    ("chpc/row19_ec2_qualify.py", "chpc/candidate_e2q/row19_ec2_qualify.py", "73f912b8ba2f4112462f279644da61d69ea40d31e905765839ad7420b3fe29c8", "pin"),
    ("chpc/row19_ec2_state.py", "chpc/candidate_e2q/row19_ec2_state.py", "7bdedafc7c90ec065217d9a7bbf53b88e1bf31e0c094dc34df730b4028bd038e", "pin"),
    ("chpc/row19_ec2_e2rules.py", "chpc/candidate_e2/row19_ec2_e2rules.py", "a9ea1f61daa577b642739ae781cb179e9a2089d42d3c23fff277d7d4849a3bcc", "pin"),
    ("chpc/row19_ec2_e2qual.py", "chpc/candidate_e2q/row19_ec2_e2qual.py", "b3f29816f80974c6f21d215b435c12d6d68d41927e89cd03f45ca614896e8ac8", "pin"),
    ("chpc/row19_partition_e2.json", "chpc/e2_final/row19_partition_e2.json", "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6", "part"),
    ("chpc/claims_snapshot_e2.json", "chpc/e2_final/claims_snapshot_e2.json", "31cc268ff3247858fc73ac17a3a387b43e17a829d9cdea505958890a97eecb6f", "data"),
    ("aws_ec2/e2_funding.json", "chpc/e2_final/e2_funding.json", "d6f414e8107f25e5de43d6b33764106c6c92dd64440ff33fddf4873416ce4815", "data"),
    ("aws_ec2/prod/manifest_production_e2.json", "chpc/e2_final/manifest_production_e2.json", "e126050536a8459cb1432cf78321e82147c67f5406441fff131a1f543f9f82f9", "data"),
    ("aws_ec2/prod/manifest_e2q1_e2.json", "chpc/e2_final/manifest_e2q1_e2.json", "3ea8cafd736871de715062ca398f36ff98f93f27d1d82bd977c3b72b0f1cfb8b", "data"),
    ("aws_ec2/prod/manifest_e2q2_e2.json", "chpc/e2_final/manifest_e2q2_e2.json", "4af4a64d83c749394c7159814359da716b2a9f9a694cd23fe46157aecd7b0cec", "data"),
    ("aws_ec2/prod/panel_e2q_e2.json", "chpc/e2_final/panel_e2q_e2.json", "f04a5e43634e13bfceaf173e303ebf780f4280de044b6bd97ee9e2c3f711c7a2", "data"),
    ("aws_ec2/prod_authority.py", "chpc/candidate_e2q/aws_ec2/prod_authority.py", "eee1bcd439f11abe3bc11fcaa905257c02157e4b4a95f506a3b2792fcebd5e65", "mac"),
    ("aws_ec2/prod_launch.py", "chpc/candidate_e2q/aws_ec2/prod_launch.py", "6bca470910489376d37529fb37772d4a2758d4c71758c990bd17108c6ff6c784", "mac"),
    ("aws_ec2/make_prod_manifest.py", "chpc/candidate_e2q/aws_ec2/make_prod_manifest.py", "d8412c32f5663350a5029309dffd6183aaf0a0a76afb089f85f8e8208ac01f07", "mac"),
    ("aws_ec2/qual_permit.py", "chpc/candidate_e2q/aws_ec2/qual_permit.py", "51653d26c69552ea449c10747672786a77dac67e4ffe183f7ff6b7382433a8ad", "mac"),
    ("aws_ec2/make_e2_funding.py", "chpc/candidate_e2/aws_ec2/make_e2_funding.py", "85e1b69cb6c993dfa9a37252f30c91a2afdc10932d389b331d5136a51f743554", "mac"),
]
# the bytes each promoted path holds TODAY (adopted v16 tree / live Mac files); None = the path is new
PREVIOUS = {
    "chpc/row19_screen_admit.py": "1b02f336f174147db975142f62e3dae947deb14f673345cc99120074deb747a0",
    "chpc/row19_partition.py": "ed6aa177a2c144d277be137212822ae405694dc342bded9bcaf6a50a4d9dd75f",
    "chpc/row19_ec2_ingest.py": "b697dc366d8fbb06619fa01cbdd5a51460a1c0e2f2bbb3d85d1a1c1a48788639",
    "chpc/row19_ec2_qualify.py": "1fc6b61fca18e4823988ec895266083895cbafcc5f9b6a10a6606e7dcd052ad6",
    "chpc/row19_ec2_state.py": "bda200dc1fa01753083b2150e2605bad6aa63cc1ed5d4f56b17858681500cf27",
    "chpc/row19_ec2_e2rules.py": None, "chpc/row19_ec2_e2qual.py": None, "chpc/row19_partition_e2.json": None,
    "chpc/claims_snapshot_e2.json": None, "aws_ec2/e2_funding.json": None, "aws_ec2/prod/manifest_production_e2.json": None,
    "aws_ec2/prod/manifest_e2q1_e2.json": None, "aws_ec2/prod/manifest_e2q2_e2.json": None, "aws_ec2/prod/panel_e2q_e2.json": None,
    "aws_ec2/prod_authority.py": "b8ca02b86bd42ebcdea15c823d0503f81c9a91978dfd3e0e4673028bdd8f5585",
    "aws_ec2/prod_launch.py": "21b7cf5768dced4f831f367b40a250b80a1ed900fe301165c4c312f15ae0f7f3",
    "aws_ec2/make_prod_manifest.py": "8da7991138a5b5cbf76396dd46c9fadcd9e582acfedfbcbace98ffdc4c5ce11c",
    "aws_ec2/qual_permit.py": "c503e795f7ed7bfa393980073df062b41f4eea78a0e9b5039c4aa1314fd56c22",
    "aws_ec2/make_e2_funding.py": None,
}
DEPLOY_GROUPS = ("pin", "part", "data")          # what travels to the Lengau controller clone as tracked files (+ controls, adoption)

REVIEWED = ("pending Codex review of controls v17, the EC2 provider epoch-2 adoption (chpc/candidate_v17/DESIGN_v17.md; DESIGN_e2.md "
            "s.5-s.6 steps 5-7; DESIGN_e2q.md s.4-s.5 choice 1): v17 = adopted v16 (01976b6a, Codex RSC f6896e1) with the partition pin "
            "moved from chpc/row19_partition_e1.json (8d1de408, still pinned by versions 13-16 and named as the e2 predecessor) to the "
            "FINAL epoch-2 declaration chpc/row19_partition_e2.json (48cea639, owned 3,274, from the locked 19 Oct snapshot 31cc268f); "
            "the epoch-2 helpers chpc/row19_partition.py (eabf50c3), chpc/row19_ec2_ingest.py (6ac144c6), chpc/row19_ec2_e2rules.py "
            "(a9ea1f61, NEW) from candidate_e2 and chpc/row19_ec2_state.py (7bdedafc, E2Q contracts), chpc/row19_ec2_qualify.py "
            "(73f912b8, the candidate_e2 REVISION 4 qualifier + the `e2` command), chpc/row19_ec2_e2qual.py (b3f29816, NEW) from "
            "candidate_e2q; chpc/row19_screen_admit.py = v16 with the one schema-2 print line (candidate_e2/admit_v17_partition_line.diff). "
            "Every other pin, sub_envelopes (refit+S 81,000), qualification_S, programme and deployment unchanged. From adoption until "
            "the canonical epoch-2 activation, Lengau refit admission HOLDS (activation_problem_v10). Grants no EC2 qualification or "
            "production: epoch-2 production needs the E2Q1 qualification, a schema-3 RELEASE certificate, a FAVOURABLE actual-result "
            "review and release-adopt. NOT adopted.")


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def input_problems():
    why = []
    for rel, h in (ADOPTED_CTL, ADOPTED_ADOPTION, ADMIT_DIFF, E1):
        if sha(rel) != h:
            why.append(f"{rel} is not {h[:8]}")
    for dst, src, h, _g in MAP:
        if not os.path.isfile(os.path.join(T1, src)) or sha(src) != h:
            why.append(f"{src} is not the reviewed/expected {h[:8]}")
    return why


def build():
    """(controls bytes, promotion-map bytes)."""
    adopted = open(os.path.join(T1, ADOPTED_CTL[0]), "rb").read()
    ctl = json.loads(adopted)
    if (json.dumps(ctl, indent=1)).encode() != adopted:
        raise SystemExit("the adopted controls are not json.dumps(indent=1) bytes: the serialisation would change versions 1-16")
    v16 = ctl["versions"][-1]
    if v16.get("version") != 16 or v16.get("partition") != {"path": E1[0], "sha256": E1[1]}:
        raise SystemExit("the adopted latest entry is not version 16 pinning e1")
    v17 = copy.deepcopy(v16)
    v17["version"] = 17
    v17["commit"] = "candidate: see the commit that adds this entry"
    v17["reviewed"] = REVIEWED
    files = dict(v16["files"])
    for dst, src, h, g in MAP:
        if g == "pin":
            files[dst] = h                       # existing keys keep their position; the two new helpers append in MAP order
    v17["files"] = files
    part = [m for m in MAP if m[3] == "part"][0]
    v17["partition"] = {"path": part[0], "sha256": part[2]}
    out = copy.deepcopy(ctl)
    out["versions"].append(v17)
    ctl_bytes = json.dumps(out, indent=1).encode()
    ctl_sha = hashlib.sha256(ctl_bytes).hexdigest()
    rows = [dict(promoted=dst, source=src, sha256=h, previous_sha256=PREVIOUS[dst], group=g, pinned_by_v17=(g == "pin"),
                 partition_ref=(g == "part"), deploy_lengau=(g in DEPLOY_GROUPS)) for dst, src, h, g in MAP]
    rows.append(dict(promoted=ADOPTED_CTL[0], source="chpc/candidate_v17/row19_screen_controls.json", sha256=ctl_sha,
                     previous_sha256=ADOPTED_CTL[1], group="ctl", pinned_by_v17=False, partition_ref=False, deploy_lengau=True))
    pm = dict(schema="row19-controls-promotion-map-1", version=17, base=dict(controls_sha256=ADOPTED_CTL[1], adoption_sha256=ADOPTED_ADOPTION[1]),
              rule="each row: copy `source` (exactly `sha256`) to `promoted`; the path must hold `previous_sha256` (or be absent when null) or "
                   "already the new bytes. Order: data and partition, Mac code, helpers, admission, then the controls LAST, then the "
                   "version-17 adoption record (promote_v17.py). Unchanged v16 pins are not listed (they stay as they are).",
              unchanged_v16_pins=sorted(f for f in v16["files"] if f not in {m[0] for m in MAP}),
              kept_for_provenance=[dict(path=E1[0], sha256=E1[1], why="pinned by versions 13-16 (unchanged) and named as the e2 predecessor; "
                                        "never deleted or relabelled; its activation proof root/ec2/activation_e1.json stays on the root")],
              rows=rows)
    return ctl_bytes, (json.dumps(pm, indent=1) + "\n").encode()


def main():
    why = input_problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    ctl_b, pm_b = build()
    targets = ((os.path.join(CAND, "row19_screen_controls.json"), ctl_b), (os.path.join(CAND, "v17_promotion_map.json"), pm_b))
    if sys.argv[1:] == ["--check"]:
        bad = [p for p, b in targets if not os.path.isfile(p) or open(p, "rb").read() != b]
        print("CHECK " + ("OK: the candidate controls and promotion map are the deterministic build" if not bad else f"FAILED: {bad}"))
        return 3 if bad else 0
    for p, b in targets:
        tmp = p + f".tmp.{os.getpid()}"
        open(tmp, "wb").write(b); os.replace(tmp, p)
    print("controls v17", hashlib.sha256(ctl_b).hexdigest(), "promotion map", hashlib.sha256(pm_b).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
