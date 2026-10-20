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
The base is ONLY the live controls/adoption at exactly v17 (no archive branch yet: the v17_before_v18 archive and promote_v18
are migration work for after Codex rules on this design; DESIGN_v18.md s.7)."""
import copy, hashlib, json, os, sys

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


def reviewed(h):
    return ("pending Codex review of controls v18, the NODE-FAILURE disposition (chpc/candidate_v18_nodefail/DESIGN_v18.md; R052 "
            "20 Oct: refit job 54 7551259.sched01 F/265 with exec node cnode0240 down at its end): v18 = adopted v17 (9ea4e727) with "
            f"chpc/row19_screen_admit.py ({h['chpc/row19_screen_admit.py'][:8]}) and chpc/row19_screen_status.py "
            f"({h['chpc/row19_screen_status.py'][:8]}) = v17 + REVISION 18, NEW chpc/row19_screen_nodefail.py "
            f"({h['chpc/row19_screen_nodefail.py'][:8]}, the one shared rule) and NEW chpc/row19_nodefail_capture.py "
            f"({h['chpc/row19_nodefail_capture.py'][:8]}, the owner's Lengau capture; evidence must carry this SHA-256). Every other "
            "pin, the e2 partition 48cea639, sub_envelopes, qualification_S, programme and deployment unchanged. A node-dispositioned "
            "job never qualifies and never counts toward the crash rule. NOT adopted.")


def build():
    for rel, h in (ADOPTED_CTL, ADOPTED_ADOPTION):
        if sha(rel) != h:
            raise SystemExit(f"REFUSED: {rel} is not the adopted v17 bytes {h[:8]} (the only base this builder accepts)")
    adopted = open(os.path.join(T1, ADOPTED_CTL[0]), "rb").read()
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
    ctl_b, pm_b = build()
    targets = ((os.path.join(CAND, "row19_screen_controls.json"), ctl_b), (os.path.join(CAND, "v18_promotion_map.json"), pm_b))
    if sys.argv[1:] == ["--check"]:
        bad = [p for p, b in targets if not os.path.isfile(p) or open(p, "rb").read() != b]
        print("CHECK " + ("OK: the candidate controls and promotion map are the deterministic build from the live v17 base" if not bad else f"FAILED: {bad}"))
        return 3 if bad else 0
    for p, b in targets:
        tmp = p + f".tmp.{os.getpid()}"
        open(tmp, "wb").write(b); os.replace(tmp, p)
    print("controls v18", hashlib.sha256(ctl_b).hexdigest(), "promotion map", hashlib.sha256(pm_b).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
