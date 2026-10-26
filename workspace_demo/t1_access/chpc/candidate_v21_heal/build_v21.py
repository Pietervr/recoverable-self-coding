"""Controls v21 CANDIDATE (NOT adopted): the FUNDING ROUTE - CSCI1913 first, then HEAL1922, per admission, side by side (owner
ruling 26 Oct 2026, R052). Builds chpc/candidate_v21_heal/row19_screen_controls.json and v21_promotion_map.json from the ADOPTED
v20 bytes and the candidate sources in this folder, deterministically. Nothing outside this folder is written; nothing is
promoted. Design: DESIGN_v21.md.

    python3 chpc/candidate_v21_heal/build_v21.py          (from workspace_demo/t1_access; --check: rebuild in memory and compare)

v21 = adopted v20 (controls 4e64982b, adoption 1ef162de) with ONE appended version-21 entry, a copy of version 20 except:
  version 21, commit (candidate text), reviewed (owner-ruling operational change text), files:
    chpc/programme_gate.py        -> this folder's gate (v20 10a53402 + REVISION 5: the funding route, per-programme accounting)
    chpc/row19_screen_admit.py    -> this folder's admission (v20 7c49bf86 + REVISION 21: route per job, `programme` on the entry,
                                     the plan and `#PBS -P`)
  sub_envelopes: refit+S cap_core_h 81,000 -> 181,000 (= 81,000 + HEAL1922's 100,000; the per-programme allocations bind), and
  ONE new key, funding_route (FUNDING_ROUTE below).
Every other pin, the partition (e3 ca87fb1d), qualification_S, the top-level programme block (the CSCI1913 allocation of the
manifest), deployment and versions 1-20 unchanged.

The base-first pattern of build_v20: the builder FIRST resolves and authenticates an immutable v20 BASE (resolve_base) and builds
the expected v21 from it:
  live     the live controls are exactly v20 4e64982b AND the live adoption record exactly 1ef162de;
  archive  otherwise only the COMPLETELY VERIFIED Mac archive chpc/results/archive/row19_screen_v20_before_v21/.
Anything else refuses."""
import copy, hashlib, json, os, re, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)

ADOPTED_CTL = ("chpc/row19_screen_controls.json", "4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c")
ADOPTED_ADOPTION = ("chpc/row19_screen_controls_adoption.json", "1ef162deb000bdc8a423d2c74d606c5db481a92fa2484d8cef75944687232894")
CREL = "chpc/candidate_v21_heal/"
# (promoted path, source path, v20 bytes)
MAP = [
    ("chpc/programme_gate.py", CREL + "programme_gate.py", "10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0"),
    ("chpc/row19_screen_admit.py", CREL + "row19_screen_admit.py", "7c49bf86c6809941bc982393fb4ae095f7186e0c47665c426c27350a841b08af"),
]
DATA = []
MAC = []
V20_PARTITION = {"path": "chpc/row19_partition_e3.json", "sha256": "ca87fb1da163df10e720e5778542d2bcc5c78f30fc08b6a1cc61d671773f0e6a"}
V20_SUBENV_CAP = 81000.0
V21_SUBENV_CAP = 181000.0
V21_SUBENV_RULE = ("the screen refit campaign and the isolated S campaign share ONE envelope (settled + every live reservation, "
                   "of EITHER programme); each admission of either checks it under the programme lock. Version 16 declared 81,000 "
                   "core-h; version 21 (owner ruling 26 Oct 2026: once CSCI1913 is spent the refit goes to HEAL1922) declares "
                   "181,000 = 81,000 + HEAL1922's 100,000, so the envelope never binds before the per-programme allocations of "
                   "funding_route do; the refit campaign ledger's own cap (81,000 until the v21 migration's two-phase "
                   "--raise-cap 181000) is checked as well, so the smaller binds")
FUNDING_ROUTE = [
    {"programme": "CSCI1913", "allocation_core_h": 100000.0, "other_settled_core_h": 6.0,
     "note": "the screen manifest's programme (the CHPC allocation of the project, 100,000 CPU-h); its allocation and other use "
             "must equal the funding block the manifest and the top-level programme block resolve (programme_gate route_of). "
             "Every ledger entry without a `programme` field is charged here by definition"},
    {"programme": "HEAL1922", "allocation_core_h": 100000.0, "other_settled_core_h": 0.01,
     "note": "Gert van Zyl's CHPC programme (the owner is a member), 100,000 CPU-h to 5 April 2027; owner 17 Oct 2026 'yes, we can "
             "charge this to those hours' and 26 Oct 2026 'once we are out of our own limit we go to HEAL1922'. Other use 0.01 "
             "core-h declared for the route check of 26 Oct 2026 (test-queue job 7587231.sched01, 1 core, walltime 00:00:01; the "
             "held serial check 7587238.sched01 never ran). The expiry (5 April 2027) is not enforced by the gate"},
]


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


ARCH = "chpc/results/archive/row19_screen_v20_before_v21"
ARCH_SCHEMA = "row19-screen-mac-archive-v20-before-v21-1"
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "2e99d6159623b787568d538493f44f2ef5fc97ec0b340ae9e3c48672cca00959")
PILOT_REC = ("reviews/2026-10-26_pilot_v20_max200_operator_record.md", "34c2b22b62fd018fc92114a669e1807bc7ba39c63a85dcdc1223fcbbdef99a51")
NODE_EVIDENCE = ("chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json",
                 "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")
# 8 members: the v20 bytes of the two replaced controllers (programme gate, admission), the v20 controls and adoption record, the
# adopted v20 pilot qualification 2e99d615 and its ACTIVE operator pilot record (max_job 200), the committed budget phases, and
# the retained captured node document of refit job 54.
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
        return [f"the Mac archive {ARCH}/ does not exist (migration_v21 archive step)"]
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
    """(base, problems): the authenticated immutable v20 base - live only while the live controls AND adoption are exactly v20;
    otherwise only the completely verified archive."""
    lc, la = _bytes_or_none(ADOPTED_CTL[0]), _bytes_or_none(ADOPTED_ADOPTION[0])
    dig = lambda b: hashlib.sha256(b).hexdigest() if b is not None else None
    if dig(lc) == ADOPTED_CTL[1] and dig(la) == ADOPTED_ADOPTION[1]:
        return dict(source="live", controls=lc, adoption=la), []
    why = archive_problems()
    if why:
        return None, [f"no authenticated v20 base: the live controls/adoption are not exactly v20 ({(dig(lc) or 'absent')[:8]}/"
                      f"{(dig(la) or 'absent')[:8]}, want {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}) and the v20 archive does not "
                      f"verify: {why[:3]}"]
    ac = open(os.path.join(T1, ARCH, "row19_screen_controls.json"), "rb").read()
    aa = open(os.path.join(T1, ARCH, "row19_screen_controls_adoption.json"), "rb").read()
    if dig(ac) != ADOPTED_CTL[1] or dig(aa) != ADOPTED_ADOPTION[1]:
        return None, ["the archived controls/adoption are not v20 4e64982b/1ef162de"]
    return dict(source="archive", controls=ac, adoption=aa), []


def input_problems(base=None):
    if base is None:
        base, why = resolve_base()
        if why:
            return why
    why = []
    if hashlib.sha256(base["controls"]).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        why.append(f"the {base.get('source')} base is not v20 {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}")
    for _dst, src, _prev in MAP + DATA + MAC:
        p = os.path.join(T1, src)
        if os.path.islink(p) or not os.path.isfile(p):
            why.append(f"{src} is missing or not a regular file")
    return why


def reviewed(h):
    return ("owner ruling 26 Oct 2026 (R052 chat: 'once we are out of our own limit we go to HEAL1922'; 'make sure that we can run "
            "jobs on HEAL1922 while we are running our own so that there is no holdup when we switch over'; 17 Oct 2026 'yes, we can "
            "charge this to those hours'): controls v21, the FUNDING ROUTE (chpc/candidate_v21_heal/DESIGN_v21.md): v21 = adopted v20 "
            f"(4e64982b) with chpc/programme_gate.py ({h['chpc/programme_gate.py'][:8]}, REVISION 5: the ordered funding route and "
            f"per-programme accounting; an entry without `programme` is CSCI1913 by definition) and chpc/row19_screen_admit.py "
            f"({h['chpc/row19_screen_admit.py'][:8]}, REVISION 21: each job goes to the first programme that fits; the code is written "
            "into the ledger entry, the plan and #PBS -P), funding_route CSCI1913 100,000 then HEAL1922 100,000, and the refit+S "
            "sub-envelope 81,000 -> 181,000 (the per-programme allocations bind; the ledger cap follows by the two-phase --raise-cap "
            "181000). No change to fit code, estimand, seeds, folds, pass conditions, the crash rule, the rescue route, the envelope, "
            "the partition (e3), qualification_S, the top-level programme block or deployment; every other pin unchanged. No science "
            "byte moves: adopted by an operator record carrying the ADOPT literal (owner rule 20 Oct 2026).")


def build(base=None):
    """(controls bytes, promotion-map bytes) built from the authenticated v20 base."""
    if base is None:
        base, why = resolve_base()
        if why:
            raise SystemExit("REFUSED: " + "; ".join(why))
    adopted = base["controls"]
    if hashlib.sha256(adopted).hexdigest() != ADOPTED_CTL[1] or hashlib.sha256(base["adoption"]).hexdigest() != ADOPTED_ADOPTION[1]:
        raise SystemExit(f"REFUSED: the base is not the adopted v20 bytes {ADOPTED_CTL[1][:8]}/{ADOPTED_ADOPTION[1][:8]}")
    ctl = json.loads(adopted)
    if json.dumps(ctl, indent=1).encode() != adopted:
        raise SystemExit("REFUSED: the adopted controls are not json.dumps(indent=1) bytes; versions 1-20 would change")
    v20 = ctl["versions"][-1]
    if v20.get("version") != 20:
        raise SystemExit("REFUSED: the adopted latest entry is not version 20")
    for dst, _src, prev in MAP:
        if v20["files"].get(dst) != prev:
            raise SystemExit(f"REFUSED: v20 pins {dst} as {v20['files'].get(dst)}, not {prev}")
    if v20.get("partition") != V20_PARTITION:
        raise SystemExit(f"REFUSED: v20 does not pin the e3 partition {V20_PARTITION['sha256'][:8]}")
    envs = v20.get("sub_envelopes") or []
    if len(envs) != 1 or envs[0].get("name") != "refit+S" or envs[0].get("cap_core_h") != V20_SUBENV_CAP:
        raise SystemExit("REFUSED: v20 does not declare exactly the refit+S sub-envelope at 81,000")
    if "funding_route" in v20:
        raise SystemExit("REFUSED: v20 already declares a funding route")
    h = {dst: sha(src) for dst, src, _p in MAP}
    v21 = copy.deepcopy(v20)
    v21["version"] = 21
    v21["commit"] = "candidate: see the commit that adds this entry"
    v21["reviewed"] = reviewed(h)
    files = dict(v20["files"])
    for dst, _src, _p in MAP:
        files[dst] = h[dst]                   # existing keys keep their position
    v21["files"] = files
    env = copy.deepcopy(envs[0]); env["cap_core_h"] = V21_SUBENV_CAP; env["rule"] = V21_SUBENV_RULE
    v21["sub_envelopes"] = [env]
    v21["funding_route"] = copy.deepcopy(FUNDING_ROUTE)
    out = copy.deepcopy(ctl); out["versions"].append(v21)
    ctl_bytes = json.dumps(out, indent=1).encode()
    rows = [dict(promoted=dst, source=src, sha256=h[dst], previous_sha256=prev, group="pin") for dst, src, prev in MAP]
    rows.append(dict(promoted=ADOPTED_CTL[0], source=CREL + "row19_screen_controls.json",
                     sha256=hashlib.sha256(ctl_bytes).hexdigest(), previous_sha256=ADOPTED_CTL[1], group="ctl"))
    pm = dict(schema="row19-controls-promotion-map-1", version=21, base=dict(controls_sha256=ADOPTED_CTL[1], adoption_sha256=ADOPTED_ADOPTION[1]),
              rule="each row: copy `source` (exactly `sha256`) to `promoted`; the path must hold `previous_sha256` or already the new "
                   "bytes. Order: the programme gate, the admission, then the controls LAST, then the version-21 adoption record. "
                   "Unchanged v20 pins are not listed.",
              unchanged_v20_pins=sorted(f for f in v20["files"] if f not in {m[0] for m in MAP}), rows=rows)
    return ctl_bytes, (json.dumps(pm, indent=1) + "\n").encode()


def main():
    base, why = resolve_base()
    if why:
        print("REFUSED: " + "; ".join(why)); return 3
    ctl_b, pm_b = build(base)
    targets = ((os.path.join(CAND, "row19_screen_controls.json"), ctl_b), (os.path.join(CAND, "v21_promotion_map.json"), pm_b))
    if sys.argv[1:] == ["--check"]:
        bad = [p for p, b in targets if not os.path.isfile(p) or open(p, "rb").read() != b]
        print("CHECK " + (f"OK: the candidate controls and promotion map are the deterministic build from the authenticated {base['source']} v20 base"
                          if not bad else f"FAILED: {bad}"))
        return 3 if bad else 0
    if base["source"] != "live":
        print("REFUSED: candidate files are (re)written only from the live v20 base; use --check after the promotion"); return 3
    for p, b in targets:
        tmp = p + f".tmp.{os.getpid()}"
        open(tmp, "wb").write(b); os.replace(tmp, p)
    print("controls v21", hashlib.sha256(ctl_b).hexdigest(), "promotion map", hashlib.sha256(pm_b).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
