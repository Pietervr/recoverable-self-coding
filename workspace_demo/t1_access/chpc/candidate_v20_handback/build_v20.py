"""Controls v20 CANDIDATE (NOT adopted): the EC2 CLOSE - the epoch-2 block handed back to Lengau (route A, owner decision 23 Oct
2026, R052). Builds chpc/candidate_v20_handback/row19_screen_controls.json and v20_promotion_map.json from the ADOPTED v19 bytes
and the candidate sources in this folder, deterministically. Nothing outside this folder is written; nothing is promoted.
Design: DESIGN_v20.md.

    python3 chpc/candidate_v20_handback/build_v20.py          (from workspace_demo/t1_access; --check: rebuild in memory and compare)

v20 = adopted v19 (controls 111c3107, adoption 2b9f3c78) with ONE appended version-20 entry, a copy of version 19 except:
  version 20, commit (candidate text), reviewed (owner-approved operational change text), files:
    chpc/row19_partition.py       -> this folder's partition module (v19 eabf50c3 + REVISION 7: schema 3, the closing epoch)
    chpc/row19_screen_admit.py    -> this folder's admission (v19 27e066c7 + REVISION 20: lengau_scope gains the hand-back)
  and partition -> {chpc/row19_partition_e3.json, this folder's e3 declaration} (the closing epoch; e2 48cea639 stays on disk
  as its bound predecessor and in versions 17-19).
Every other pin (the status view, the EC2 state, E2Q module, ingestion, qualifier, root, shadow, node-failure rule and capture
script, verifier, release consumer, resources, designated declaration, programme gate, qual_S plan/manifest), sub_envelopes
(refit+S 81,000), qualification_S, programme (so the CSCI1913 allocation 100,000 of the manifest), deployment and versions 1-19
unchanged.
DATA (not a controls pin: a NEW path promoted beside the pins, the build_v17 `data` group): chpc/row19_partition_e3.json (pinned
through the version entry's `partition`, as e1 and e2 were).
MAC (not a controls pin: a REPLACED Mac tool, its v19 bytes archived): aws_ec2/prod_authority.py (REVISION 10, the terminal
close in the EC2 claim and budget authority).

The base-first pattern of build_v18 REVISION 2 / build_v19. The builder FIRST resolves and authenticates an immutable v19 BASE
(resolve_base) and builds the expected v20 from that base, never from whatever the live controls hold:
  live     the live controls are exactly v19 111c3107 AND the live adoption record exactly 2b9f3c78 (before promotion, and
           during a promotion interrupted before its controls-last copy);
  archive  otherwise only the COMPLETELY VERIFIED Mac archive chpc/results/archive/row19_screen_v19_before_v20/ (exactly the
           ARCHIVE inventory below + SHA256SUMS + COMPLETE, every digest verifying, the fixed members at their v19 digests) -
           after, and through, the promotion's controls-last copy.
Anything else refuses. The archive inventory and its verification live here (promote_v20.py reads them), so the builder and the
promoter authenticate one base the same way."""
import copy, hashlib, json, os, re, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)

ADOPTED_CTL = ("chpc/row19_screen_controls.json", "111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5")
ADOPTED_ADOPTION = ("chpc/row19_screen_controls_adoption.json", "2b9f3c783e1f7ce53cbdafa4a84e66315874512d7afcde6b03783c343ba2939c")
CREL = "chpc/candidate_v20_handback/"
# (promoted path, source path, v19 bytes)
MAP = [
    ("chpc/row19_partition.py", CREL + "row19_partition.py", "eabf50c34be2bad3f92e07370966bcc94162cf12cbcefb326cc07a72d49ac0d8"),
    ("chpc/row19_screen_admit.py", CREL + "row19_screen_admit.py", "27e066c72ed43919a92083fcf3f035cbee232c2137c2e97832f0e41b1113f9df"),
]
# (promoted path, source path, None): NEW data paths promoted beside the pins (build_v17 `data`); the e3 declaration is pinned
# through the version entry's `partition`, never in `files`
PARTITION_REL = "chpc/row19_partition_e3.json"
V19_PARTITION = {"path": "chpc/row19_partition_e2.json", "sha256": "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6"}
DATA = [
    (PARTITION_REL, CREL + "row19_partition_e3.json", None),
]
# (promoted path, source path, v19 bytes): REPLACED Mac tools, not pinned by the controls; their v19 bytes are archived
MAC = [
    ("aws_ec2/prod_authority.py", CREL + "aws_ec2/prod_authority.py", "ba726a197ab2da5d89a1b8d9615890ab9e49ddf1614191d7fb2a5fc446142ac6"),
]


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


# the immutable v19 base and the Mac archive that carries it through and after the promotion
ARCH = "chpc/results/archive/row19_screen_v19_before_v20"
ARCH_SCHEMA = "row19-screen-mac-archive-v19-before-v20-1"
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "e123d6e5d136dfda31ac5f61dd18a2cce31ecc8dea9f1ad27be73d427cc50b02")
PILOT_REC = ("reviews/2026-10-22_pilot_v19_operator_record.md", "26aa4f8dc52be9d7f67fc493bd6002ae4d3b29ca73b77ce9c30082336ff4bde6")
NODE_EVIDENCE = ("chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json",
                 "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")
# 9 members: the v19 bytes of the two replaced controllers (partition module, admission) and of the replaced Mac authority, the
# v19 controls and adoption record, the adopted v19 pilot qualification e123d6e5 and its operator pilot record, the committed
# budget phases, and the retained captured node document of refit job 54 (still the evidence of its node-failure disposition).
# The DATA row is a new path with no v19 bytes, so nothing of it is archived (e2, its predecessor, stays in place, unchanged).
ARCHIVE = {os.path.basename(dst): (dst, prev) for dst, _src, prev in MAP + MAC}
ARCHIVE.update({"row19_screen_controls.json": ADOPTED_CTL, "row19_screen_controls_adoption.json": ADOPTED_ADOPTION,
                "qualified_refit_job1.json": QUAL, "row19_screen_budget.json": ("chpc/row19_screen_budget.json", None),
                os.path.basename(PILOT_REC[0]): PILOT_REC, "row19_screen_refit_54.nodefail.json": NODE_EVIDENCE})


def _bytes_or_none(rel):
    p = os.path.join(T1, rel)
    return open(p, "rb").read() if os.path.isfile(p) and not os.path.islink(p) else None


def archive_problems():
    """[] when the Mac archive holds EXACTLY the ARCHIVE inventory + SHA256SUMS + COMPLETE and every digest verifies."""
    d = os.path.join(T1, ARCH)
    if not os.path.isdir(d) or os.path.islink(d):
        return [f"the Mac archive {ARCH}/ does not exist (migration_v20 archive step)"]
    why = []
    names = sorted(os.listdir(d))
    if names != sorted(list(ARCHIVE) + ["SHA256SUMS", "COMPLETE"]):
        return [f"the archive holds {names}, not exactly its inventory + SHA256SUMS + COMPLETE"]
    sums = {}
    for line in open(os.path.join(d, "SHA256SUMS")).read().splitlines():
        m = re.match(r"^([0-9a-f]{64})  ([A-Za-z0-9._-]+)$", line)
        if not m or m.group(2) in sums:
            return ["the archive's SHA256SUMS has a malformed or duplicate line"]
        sums[m.group(2)] = m.group(1)
    if sorted(sums) != sorted(ARCHIVE):
        why.append("the archive's SHA256SUMS does not list exactly its inventory")
    for n, (_src, fixed) in ARCHIVE.items():
        p = os.path.join(d, n)
        if os.path.islink(p) or not os.path.isfile(p):
            why.append(f"archive member {n} is not a regular file"); continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if sums.get(n) != h or (fixed is not None and h != fixed):
            why.append(f"archive member {n} does not verify ({h[:8]})")
    try:
        comp = json.load(open(os.path.join(d, "COMPLETE")))
        if comp.get("schema") != ARCH_SCHEMA or comp.get("sha256sums") != hashlib.sha256(open(os.path.join(d, "SHA256SUMS"), "rb").read()).hexdigest():
            why.append("the archive's COMPLETE certificate does not name its SHA256SUMS")
    except Exception as e:
        why.append(f"the archive's COMPLETE is unreadable ({type(e).__name__})")
    return why


def resolve_base():
    """(base, problems): the authenticated immutable v19 base - {"source": "live"|"archive", "controls": bytes, "adoption":
    bytes} - resolved BEFORE any candidate or build check. Live only while the live controls AND adoption are exactly v19;
    otherwise only the completely verified archive. Never the live controls of any other version."""
    lc, la = _bytes_or_none(ADOPTED_CTL[0]), _bytes_or_none(ADOPTED_ADOPTION[0])
    dig = lambda b: hashlib.sha256(b).hexdigest() if b is not None else None
    if dig(lc) == ADOPTED_CTL[1] and dig(la) == ADOPTED_ADOPTION[1]:
        return dict(source="live", controls=lc, adoption=la), []
    why = archive_problems()
    if why:
        return None, [f"no authenticated v19 base: the live controls/adoption are not exactly v19 ({(dig(lc) or 'absent')[:8]}/"
                      f"{(dig(la) or 'absent')[:8]}, want {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}) and the v19 archive does not "
                      f"verify: {why[:3]}"]
    ac = open(os.path.join(T1, ARCH, "row19_screen_controls.json"), "rb").read()
    aa = open(os.path.join(T1, ARCH, "row19_screen_controls_adoption.json"), "rb").read()
    if dig(ac) != ADOPTED_CTL[1] or dig(aa) != ADOPTED_ADOPTION[1]:          # already fixed members; checked again where used
        return None, ["the archived controls/adoption are not v19 111c3107/2b9f3c78"]
    return dict(source="archive", controls=ac, adoption=aa), []


def input_problems(base=None):
    """The base FIRST (resolve_base), then every map source exists as a regular file."""
    if base is None:
        base, why = resolve_base()
        if why:
            return why
    why = []
    if hashlib.sha256(base["controls"]).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        why.append(f"the {base.get('source')} base is not v19 {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}")
    for _dst, src, _prev in MAP + DATA + MAC:
        p = os.path.join(T1, src)
        if os.path.islink(p) or not os.path.isfile(p):
            why.append(f"{src} is missing or not a regular file")
    return why


def reviewed(h, psha):
    return ("owner decision 23 Oct 2026 (R052, route A: EC2 is finished for row 19; the EC2-designated epoch-2 block goes back to "
            "Lengau): controls v20, the EC2 CLOSE (chpc/candidate_v20_handback/DESIGN_v20.md): v20 = adopted v19 (111c3107) with "
            f"chpc/row19_partition.py ({h['chpc/row19_partition.py'][:8]}, REVISION 7: schema 3, the terminal closing epoch) and "
            f"chpc/row19_screen_admit.py ({h['chpc/row19_screen_admit.py'][:8]}, REVISION 20: Lengau's scope gains the hand-back, the "
            f"replicate-complete order unchanged), pinning the closing epoch e3 {PARTITION_REL} ({psha[:8]}: EC2 owns nothing; every "
            "coordinate e2 48cea639 owned and EC2 never completed is handed back). No change to fit code, estimand, seeds, folds, "
            "pass conditions, the crash rule, the rescue route, the envelope, sub_envelopes (refit+S 81,000), the ledger cap, "
            "qualification_S, programme (the CSCI1913 allocation) or deployment; every other pin unchanged. Lengau refit admission "
            "holds from this version's adoption until the e3 activation. Adopted by an operator record carrying the ADOPT literal.")


def build(base=None):
    """(controls bytes, promotion-map bytes) built from the authenticated v19 base (resolve_base when not given)."""
    if base is None:
        base, why = resolve_base()
        if why:
            raise SystemExit("REFUSED: " + "; ".join(why))
    adopted = base["controls"]
    if hashlib.sha256(adopted).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        raise SystemExit(f"REFUSED: the base is not the adopted v19 bytes {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]} (the only base this builder accepts)")
    ctl = json.loads(adopted)
    if json.dumps(ctl, indent=1).encode() != adopted:
        raise SystemExit("REFUSED: the adopted controls are not json.dumps(indent=1) bytes; versions 1-19 would change")
    v19 = ctl["versions"][-1]
    if v19.get("version") != 19:
        raise SystemExit("REFUSED: the adopted latest entry is not version 19")
    for dst, _src, prev in MAP:
        if v19["files"].get(dst) != prev:
            raise SystemExit(f"REFUSED: v19 pins {dst} as {v19['files'].get(dst)}, not {prev}")
    if v19.get("partition") != V19_PARTITION:
        raise SystemExit(f"REFUSED: v19 does not pin the e2 partition {V19_PARTITION['sha256'][:8]}")
    h = {dst: sha(src) for dst, src, _p in MAP}
    psha = sha(DATA[0][1])
    v20 = copy.deepcopy(v19)
    v20["version"] = 20
    v20["commit"] = "candidate: see the commit that adds this entry"
    v20["reviewed"] = reviewed(h, psha)
    files = dict(v19["files"])
    for dst, _src, _p in MAP:
        files[dst] = h[dst]                   # existing keys keep their position
    v20["files"] = files
    v20["partition"] = {"path": PARTITION_REL, "sha256": psha}
    out = copy.deepcopy(ctl); out["versions"].append(v20)
    ctl_bytes = json.dumps(out, indent=1).encode()
    rows = [dict(promoted=dst, source=src, sha256=h[dst], previous_sha256=prev, group="pin") for dst, src, prev in MAP]
    rows += [dict(promoted=dst, source=src, sha256=sha(src), previous_sha256=None, group="data") for dst, src, _p in DATA]
    rows += [dict(promoted=dst, source=src, sha256=sha(src), previous_sha256=prev, group="mac") for dst, src, prev in MAC]
    rows.append(dict(promoted=ADOPTED_CTL[0], source=CREL + "row19_screen_controls.json",
                     sha256=hashlib.sha256(ctl_bytes).hexdigest(), previous_sha256=ADOPTED_CTL[1], group="ctl"))
    pm = dict(schema="row19-controls-promotion-map-1", version=20, base=dict(controls_sha256=ADOPTED_CTL[1], adoption_sha256=ADOPTED_ADOPTION[1]),
              rule="each row: copy `source` (exactly `sha256`) to `promoted`; the path must hold `previous_sha256` (null: a NEW path, "
                   "absent before) or already the new bytes. Order: the partition module, the admission, the e3 closing declaration "
                   "(data: pinned by the version entry's `partition`, not in `files`), the Mac authority (mac: not pinned by the "
                   "controls), then the controls LAST, then the version-20 adoption record. Unchanged v19 pins are not listed.",
              unchanged_v19_pins=sorted(f for f in v19["files"] if f not in {m[0] for m in MAP}), rows=rows)
    return ctl_bytes, (json.dumps(pm, indent=1) + "\n").encode()


def main():
    base, why = resolve_base()
    if why:
        print("REFUSED: " + "; ".join(why)); return 3
    ctl_b, pm_b = build(base)
    targets = ((os.path.join(CAND, "row19_screen_controls.json"), ctl_b), (os.path.join(CAND, "v20_promotion_map.json"), pm_b))
    if sys.argv[1:] == ["--check"]:
        bad = [p for p, b in targets if not os.path.isfile(p) or open(p, "rb").read() != b]
        print("CHECK " + (f"OK: the candidate controls and promotion map are the deterministic build from the authenticated {base['source']} v19 base"
                          if not bad else f"FAILED: {bad}"))
        return 3 if bad else 0
    if base["source"] != "live":
        print("REFUSED: candidate files are (re)written only from the live v19 base; use --check after the promotion"); return 3
    for p, b in targets:
        tmp = p + f".tmp.{os.getpid()}"
        open(tmp, "wb").write(b); os.replace(tmp, p)
    print("controls v20", hashlib.sha256(ctl_b).hexdigest(), "promotion map", hashlib.sha256(pm_b).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
