"""Controls v18 CANDIDATE (NOT adopted): the node-failure disposition. Builds chpc/candidate_v18_nodefail/row19_screen_controls.json
and v18_promotion_map.json from the ADOPTED v17 bytes and the candidate sources in this folder, deterministically. Nothing outside
this folder is written; nothing is promoted. Design: DESIGN_v18.md.

    python3 chpc/candidate_v18_nodefail/build_v18.py            (from workspace_demo/t1_access; --check: rebuild in memory and compare)

v18 = adopted v17 (controls 9ea4e727, adoption 61ca680e) with ONE appended version-18 entry, a copy of version 17 except:
  version 18, commit (candidate text), reviewed (pending text), and files:
    chpc/row19_screen_admit.py    -> this folder's admission (v17 c3960464 + REVISION 18)
    chpc/row19_screen_status.py   -> this folder's status view (v17 a9f9180b + REVISION 18)
    chpc/row19_screen_nodefail.py -> NEW: the shared node-failure rule
    chpc/row19_nodefail_capture.py-> NEW: the owner's Lengau capture script (its SHA-256 is what evidence must carry)
Every other pin, the partition (e2 48cea639), sub_envelopes, qualification_S, programme, deployment and versions 1-17 unchanged.

REVISION 2 (the base-first pattern of build_v17 REVISION 2, for chpc/migration_v18; Codex review
reviews/2026-10-20_v18_nodefail_codex_review.md "Controls binding and migration ruling"). The builder FIRST resolves and
authenticates an immutable v17 BASE (resolve_base) and builds the expected v18 from that base, never from whatever the live
controls hold:
  live     the live controls are exactly v17 9ea4e727 AND the live adoption record exactly 61ca680e (before promotion, and
           during a promotion interrupted before its controls-last copy);
  archive  otherwise only the COMPLETELY VERIFIED Mac archive chpc/results/archive/row19_screen_v17_before_v18/ (exactly the
           ARCHIVE inventory below + SHA256SUMS + COMPLETE, every digest verifying, the fixed members at their v17 digests) -
           after, and through, the promotion's controls-last copy.
Anything else refuses. The built bytes are unchanged by this revision (the same deterministic controls and map from the same
v17 bytes); only where the base may come from is new. The archive inventory and its verification live here (promote_v18.py
and chpc/migration_v18/mac_archive.py read them), so the builder and the promoter authenticate one base the same way."""
import copy, hashlib, json, os, re, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)

ADOPTED_CTL = ("chpc/row19_screen_controls.json", "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0")
ADOPTED_ADOPTION = ("chpc/row19_screen_controls_adoption.json", "61ca680e932fcb6d32a972c3198b5bd9c029da3955e15dd7acb2e07db125699b")
# (promoted path, source path, v17 bytes or None when new)
MAP = [
    ("chpc/row19_screen_nodefail.py", "chpc/candidate_v18_nodefail/row19_screen_nodefail.py", None),
    ("chpc/row19_nodefail_capture.py", "chpc/candidate_v18_nodefail/row19_nodefail_capture.py", None),
    ("chpc/row19_screen_status.py", "chpc/candidate_v18_nodefail/row19_screen_status.py", "a9f9180b73438221788d745567603fd267befca8fbc60528e3e7de47421ff64a"),
    ("chpc/row19_screen_admit.py", "chpc/candidate_v18_nodefail/row19_screen_admit.py", "c3960464db74a282f20da030008fb759a0fad4e1d4d3c7133c98f3b821d6b9ed"),
]


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


# REVISION 2: the immutable v17 base and the Mac archive that carries it through and after the promotion
ARCH = "chpc/results/archive/row19_screen_v17_before_v18"
ARCH_SCHEMA = "row19-screen-mac-archive-v17-before-v18-1"
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "8fdbf48e998e39a8c0b12900d75e3dfaf4ab64396ade08a17a5cab549c0b5faa")
PILOT_REC = ("reviews/2026-10-20_pilot_v17_codex_review.md", "75bb50101afa7eebc07e47915afbed32dec92ebf1e68235fe742bf9e5ff0035d")
NODE_EVIDENCE = ("chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json",
                 "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")
# 8 members: the v17 bytes of the two replaced controllers (admission, status view), the v17 controls and adoption record, the
# adopted v17 pilot qualification 8fdbf48e and its Codex pilot record, the committed budget phases, and the RETAINED captured
# node document of refit job 54 (Codex ruling: "retain this captured node document"). The two NEW files have no v17 bytes.
ARCHIVE = {os.path.basename(dst): (dst, prev) for dst, _src, prev in MAP if prev is not None}
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
        return [f"the Mac archive {ARCH}/ does not exist (migration_v18 archive step)"]
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
    """(base, problems): the authenticated immutable v17 base - {"source": "live"|"archive", "controls": bytes, "adoption":
    bytes} - resolved BEFORE any candidate or build check. Live only while the live controls AND adoption are exactly v17;
    otherwise only the completely verified archive. Never the live controls of any other version."""
    lc, la = _bytes_or_none(ADOPTED_CTL[0]), _bytes_or_none(ADOPTED_ADOPTION[0])
    dig = lambda b: hashlib.sha256(b).hexdigest() if b is not None else None
    if dig(lc) == ADOPTED_CTL[1] and dig(la) == ADOPTED_ADOPTION[1]:
        return dict(source="live", controls=lc, adoption=la), []
    why = archive_problems()
    if why:
        return None, [f"no authenticated v17 base: the live controls/adoption are not exactly v17 ({(dig(lc) or 'absent')[:8]}/"
                      f"{(dig(la) or 'absent')[:8]}, want {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}) and the v17 archive does not "
                      f"verify: {why[:3]}"]
    ac = open(os.path.join(T1, ARCH, "row19_screen_controls.json"), "rb").read()
    aa = open(os.path.join(T1, ARCH, "row19_screen_controls_adoption.json"), "rb").read()
    if dig(ac) != ADOPTED_CTL[1] or dig(aa) != ADOPTED_ADOPTION[1]:          # already fixed members; checked again where used
        return None, ["the archived controls/adoption are not v17 9ea4e727/61ca680e"]
    return dict(source="archive", controls=ac, adoption=aa), []


def input_problems(base=None):
    """The base FIRST (resolve_base), then every map source exists as a regular file."""
    if base is None:
        base, why = resolve_base()
        if why:
            return why
    why = []
    if hashlib.sha256(base["controls"]).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        why.append(f"the {base.get('source')} base is not v17 {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}")
    for _dst, src, _prev in MAP:
        p = os.path.join(T1, src)
        if os.path.islink(p) or not os.path.isfile(p):
            why.append(f"{src} is missing or not a regular file")
    return why


def reviewed(h):
    return ("pending Codex review of controls v18, the NODE-FAILURE disposition (chpc/candidate_v18_nodefail/DESIGN_v18.md; R052 "
            "20 Oct: refit job 54 7551259.sched01 F/265 with exec node cnode0240 down at its end): v18 = adopted v17 (9ea4e727) with "
            f"chpc/row19_screen_admit.py ({h['chpc/row19_screen_admit.py'][:8]}) and chpc/row19_screen_status.py "
            f"({h['chpc/row19_screen_status.py'][:8]}) = v17 + REVISION 18, NEW chpc/row19_screen_nodefail.py "
            f"({h['chpc/row19_screen_nodefail.py'][:8]}, the one shared rule) and NEW chpc/row19_nodefail_capture.py "
            f"({h['chpc/row19_nodefail_capture.py'][:8]}, the owner's Lengau capture; evidence must carry this SHA-256). Every other "
            "pin, the e2 partition 48cea639, sub_envelopes, qualification_S, programme and deployment unchanged. A node-dispositioned "
            "job never qualifies and never counts toward the crash rule. NOT adopted.")


def build(base=None):
    """(controls bytes, promotion-map bytes) built from the authenticated v17 base (resolve_base when not given)."""
    if base is None:
        base, why = resolve_base()
        if why:
            raise SystemExit("REFUSED: " + "; ".join(why))
    adopted = base["controls"]
    if hashlib.sha256(adopted).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        raise SystemExit(f"REFUSED: the base is not the adopted v17 bytes {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]} (the only base this builder accepts)")
    ctl = json.loads(adopted)
    if json.dumps(ctl, indent=1).encode() != adopted:
        raise SystemExit("REFUSED: the adopted controls are not json.dumps(indent=1) bytes; versions 1-17 would change")
    v17 = ctl["versions"][-1]
    if v17.get("version") != 17:
        raise SystemExit("REFUSED: the adopted latest entry is not version 17")
    for dst, _src, prev in MAP:
        if v17["files"].get(dst) != prev:
            raise SystemExit(f"REFUSED: v17 pins {dst} as {v17['files'].get(dst)}, not {prev}")
    h = {dst: sha(src) for dst, src, _p in MAP}
    v18 = copy.deepcopy(v17)
    v18["version"] = 18
    v18["commit"] = "candidate: see the commit that adds this entry"
    v18["reviewed"] = reviewed(h)
    files = dict(v17["files"])
    for dst, _src, _p in MAP:
        files[dst] = h[dst]                   # existing keys keep their position; the two new files append in MAP order
    v18["files"] = files
    out = copy.deepcopy(ctl); out["versions"].append(v18)
    ctl_bytes = json.dumps(out, indent=1).encode()
    rows = [dict(promoted=dst, source=src, sha256=h[dst], previous_sha256=prev, group="pin") for dst, src, prev in MAP]
    rows.append(dict(promoted=ADOPTED_CTL[0], source="chpc/candidate_v18_nodefail/row19_screen_controls.json",
                     sha256=hashlib.sha256(ctl_bytes).hexdigest(), previous_sha256=ADOPTED_CTL[1], group="ctl"))
    pm = dict(schema="row19-controls-promotion-map-1", version=18, base=dict(controls_sha256=ADOPTED_CTL[1], adoption_sha256=ADOPTED_ADOPTION[1]),
              rule="each row: copy `source` (exactly `sha256`) to `promoted`; the path must hold `previous_sha256` (or be absent when null) "
                   "or already the new bytes. Order: the two new files, the status view, the admission, then the controls LAST, then the "
                   "version-18 adoption record. Unchanged v17 pins are not listed.",
              unchanged_v17_pins=sorted(f for f in v17["files"] if f not in {m[0] for m in MAP}), rows=rows)
    return ctl_bytes, (json.dumps(pm, indent=1) + "\n").encode()


def main():
    base, why = resolve_base()
    if why:
        print("REFUSED: " + "; ".join(why)); return 3
    ctl_b, pm_b = build(base)
    targets = ((os.path.join(CAND, "row19_screen_controls.json"), ctl_b), (os.path.join(CAND, "v18_promotion_map.json"), pm_b))
    if sys.argv[1:] == ["--check"]:
        bad = [p for p, b in targets if not os.path.isfile(p) or open(p, "rb").read() != b]
        print("CHECK " + (f"OK: the candidate controls and promotion map are the deterministic build from the authenticated {base['source']} v17 base"
                          if not bad else f"FAILED: {bad}"))
        return 3 if bad else 0
    if base["source"] != "live":
        print("REFUSED: candidate files are (re)written only from the live v17 base; use --check after the promotion"); return 3
    for p, b in targets:
        tmp = p + f".tmp.{os.getpid()}"
        open(tmp, "wb").write(b); os.replace(tmp, p)
    print("controls v18", hashlib.sha256(ctl_b).hexdigest(), "promotion map", hashlib.sha256(pm_b).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
