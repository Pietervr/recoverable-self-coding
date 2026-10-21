"""Controls v19 CANDIDATE (NOT adopted): the operational-loss disposition. Builds chpc/candidate_v19_oploss/row19_screen_controls.json
and v19_promotion_map.json from the ADOPTED v18 bytes and the candidate sources in this folder, deterministically. Nothing outside
this folder is written; nothing is promoted. Design: DESIGN_v19.md.

    python3 chpc/candidate_v19_oploss/build_v19.py            (from workspace_demo/t1_access; --check: rebuild in memory and compare)

v19 = adopted v18 (controls 452b82df, adoption 3e1fe9a1) with ONE appended version-19 entry, a copy of version 18 except:
  version 19, commit (candidate text), reviewed (owner-approved operational change text), and files:
    chpc/row19_screen_admit.py    -> this folder's admission (v18 e2260765 + REVISION 19)
    chpc/row19_screen_status.py   -> this folder's status view (v18 4710544a + REVISION 19)
Every other pin (incl. the v18 node-failure rule and capture script), the partition (e2 48cea639), sub_envelopes,
qualification_S, programme, deployment and versions 1-18 unchanged.

The base-first pattern of build_v18 REVISION 2. The builder FIRST resolves and authenticates an immutable v18 BASE
(resolve_base) and builds the expected v19 from that base, never from whatever the live controls hold:
  live     the live controls are exactly v18 452b82df AND the live adoption record exactly 3e1fe9a1 (before promotion, and
           during a promotion interrupted before its controls-last copy);
  archive  otherwise only the COMPLETELY VERIFIED Mac archive chpc/results/archive/row19_screen_v18_before_v19/ (exactly the
           ARCHIVE inventory below + SHA256SUMS + COMPLETE, every digest verifying, the fixed members at their v18 digests) -
           after, and through, the promotion's controls-last copy.
Anything else refuses. The archive inventory and its verification live here (promote_v19.py and chpc/migration_v19/mac_archive.py
read them), so the builder and the promoter authenticate one base the same way."""
import copy, hashlib, json, os, re, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)

ADOPTED_CTL = ("chpc/row19_screen_controls.json", "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b")
ADOPTED_ADOPTION = ("chpc/row19_screen_controls_adoption.json", "3e1fe9a1ddd10a6ed160f5f1f9fc3f4f4de707efa3e90259104e7e5670ae1616")
# (promoted path, source path, v18 bytes)
MAP = [
    ("chpc/row19_screen_status.py", "chpc/candidate_v19_oploss/row19_screen_status.py", "4710544a3861b688b0f2c89e67a8ba56cf65261a8900d4147658fee576f58232"),
    ("chpc/row19_screen_admit.py", "chpc/candidate_v19_oploss/row19_screen_admit.py", "e22607650058ae2cbb8f19fe3e225d886bd2cc733adf02bb93dbc01d65f719af"),
]


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


# the immutable v18 base and the Mac archive that carries it through and after the promotion
ARCH = "chpc/results/archive/row19_screen_v18_before_v19"
ARCH_SCHEMA = "row19-screen-mac-archive-v18-before-v19-1"
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "530df9a208eb1578282ef564708447fd3b32c5fa1366f388f51059ebcfd70839")
PILOT_REC = ("reviews/2026-10-20_pilot_v18_operator_record.md", "67f2b4383a1b25d7e6921f0c8252514a6fe797e37419af3ddfbb8116753fae87")
NODE_EVIDENCE = ("chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json",
                 "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")
# 8 members: the v18 bytes of the two replaced controllers (admission, status view), the v18 controls and adoption record, the
# adopted v18 pilot qualification 530df9a2 and its operator pilot record, the committed budget phases, and the retained captured
# node document of refit job 54 (still the evidence of its node-failure disposition under v19).
ARCHIVE = {os.path.basename(dst): (dst, prev) for dst, _src, prev in MAP}
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
        return [f"the Mac archive {ARCH}/ does not exist (migration_v19 archive step)"]
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
    """(base, problems): the authenticated immutable v18 base - {"source": "live"|"archive", "controls": bytes, "adoption":
    bytes} - resolved BEFORE any candidate or build check. Live only while the live controls AND adoption are exactly v18;
    otherwise only the completely verified archive. Never the live controls of any other version."""
    lc, la = _bytes_or_none(ADOPTED_CTL[0]), _bytes_or_none(ADOPTED_ADOPTION[0])
    dig = lambda b: hashlib.sha256(b).hexdigest() if b is not None else None
    if dig(lc) == ADOPTED_CTL[1] and dig(la) == ADOPTED_ADOPTION[1]:
        return dict(source="live", controls=lc, adoption=la), []
    why = archive_problems()
    if why:
        return None, [f"no authenticated v18 base: the live controls/adoption are not exactly v18 ({(dig(lc) or 'absent')[:8]}/"
                      f"{(dig(la) or 'absent')[:8]}, want {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}) and the v18 archive does not "
                      f"verify: {why[:3]}"]
    ac = open(os.path.join(T1, ARCH, "row19_screen_controls.json"), "rb").read()
    aa = open(os.path.join(T1, ARCH, "row19_screen_controls_adoption.json"), "rb").read()
    if dig(ac) != ADOPTED_CTL[1] or dig(aa) != ADOPTED_ADOPTION[1]:          # already fixed members; checked again where used
        return None, ["the archived controls/adoption are not v18 452b82df/3e1fe9a1"]
    return dict(source="archive", controls=ac, adoption=aa), []


def input_problems(base=None):
    """The base FIRST (resolve_base), then every map source exists as a regular file."""
    if base is None:
        base, why = resolve_base()
        if why:
            return why
    why = []
    if hashlib.sha256(base["controls"]).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        why.append(f"the {base.get('source')} base is not v18 {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}")
    for _dst, src, _prev in MAP:
        p = os.path.join(T1, src)
        if os.path.islink(p) or not os.path.isfile(p):
            why.append(f"{src} is missing or not a regular file")
    return why


def reviewed(h):
    return ("owner-approved operational change, R052 lean T1 plan item 2 (20 Oct 2026; no Codex review of operational changes): controls "
            "v19, the OPERATIONAL-LOSS disposition (chpc/candidate_v19_oploss/DESIGN_v19.md): v19 = adopted v18 (452b82df) with "
            f"chpc/row19_screen_admit.py ({h['chpc/row19_screen_admit.py'][:8]}) and chpc/row19_screen_status.py "
            f"({h['chpc/row19_screen_status.py'][:8]}) = v18 + REVISION 19. Every other pin, the e2 partition 48cea639, sub_envelopes, "
            "qualification_S, programme and deployment unchanged. An operational-loss job never qualifies and never counts toward the "
            "crash rule. Adopted by an operator record carrying the ADOPT literal.")


def build(base=None):
    """(controls bytes, promotion-map bytes) built from the authenticated v18 base (resolve_base when not given)."""
    if base is None:
        base, why = resolve_base()
        if why:
            raise SystemExit("REFUSED: " + "; ".join(why))
    adopted = base["controls"]
    if hashlib.sha256(adopted).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        raise SystemExit(f"REFUSED: the base is not the adopted v18 bytes {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]} (the only base this builder accepts)")
    ctl = json.loads(adopted)
    if json.dumps(ctl, indent=1).encode() != adopted:
        raise SystemExit("REFUSED: the adopted controls are not json.dumps(indent=1) bytes; versions 1-18 would change")
    v18 = ctl["versions"][-1]
    if v18.get("version") != 18:
        raise SystemExit("REFUSED: the adopted latest entry is not version 18")
    for dst, _src, prev in MAP:
        if v18["files"].get(dst) != prev:
            raise SystemExit(f"REFUSED: v18 pins {dst} as {v18['files'].get(dst)}, not {prev}")
    h = {dst: sha(src) for dst, src, _p in MAP}
    v19 = copy.deepcopy(v18)
    v19["version"] = 19
    v19["commit"] = "candidate: see the commit that adds this entry"
    v19["reviewed"] = reviewed(h)
    files = dict(v18["files"])
    for dst, _src, _p in MAP:
        files[dst] = h[dst]                   # existing keys keep their position
    v19["files"] = files
    out = copy.deepcopy(ctl); out["versions"].append(v19)
    ctl_bytes = json.dumps(out, indent=1).encode()
    rows = [dict(promoted=dst, source=src, sha256=h[dst], previous_sha256=prev, group="pin") for dst, src, prev in MAP]
    rows.append(dict(promoted=ADOPTED_CTL[0], source="chpc/candidate_v19_oploss/row19_screen_controls.json",
                     sha256=hashlib.sha256(ctl_bytes).hexdigest(), previous_sha256=ADOPTED_CTL[1], group="ctl"))
    pm = dict(schema="row19-controls-promotion-map-1", version=19, base=dict(controls_sha256=ADOPTED_CTL[1], adoption_sha256=ADOPTED_ADOPTION[1]),
              rule="each row: copy `source` (exactly `sha256`) to `promoted`; the path must hold `previous_sha256` or already the new "
                   "bytes. Order: the status view, the admission, then the controls LAST, then the version-19 adoption record. "
                   "Unchanged v18 pins are not listed.",
              unchanged_v18_pins=sorted(f for f in v18["files"] if f not in {m[0] for m in MAP}), rows=rows)
    return ctl_bytes, (json.dumps(pm, indent=1) + "\n").encode()


def main():
    base, why = resolve_base()
    if why:
        print("REFUSED: " + "; ".join(why)); return 3
    ctl_b, pm_b = build(base)
    targets = ((os.path.join(CAND, "row19_screen_controls.json"), ctl_b), (os.path.join(CAND, "v19_promotion_map.json"), pm_b))
    if sys.argv[1:] == ["--check"]:
        bad = [p for p, b in targets if not os.path.isfile(p) or open(p, "rb").read() != b]
        print("CHECK " + (f"OK: the candidate controls and promotion map are the deterministic build from the authenticated {base['source']} v18 base"
                          if not bad else f"FAILED: {bad}"))
        return 3 if bad else 0
    if base["source"] != "live":
        print("REFUSED: candidate files are (re)written only from the live v18 base; use --check after the promotion"); return 3
    for p, b in targets:
        tmp = p + f".tmp.{os.getpid()}"
        open(tmp, "wb").write(b); os.replace(tmp, p)
    print("controls v19", hashlib.sha256(ctl_b).hexdigest(), "promotion map", hashlib.sha256(pm_b).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
