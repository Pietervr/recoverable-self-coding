"""Cutover v13 -> v14, step 1 (Mac): promote the exact reviewed v14 controls + status into chpc/ and write the adoption record.
Status-only lineage (Codex RSC 1de6dc0, record reviews/2026-10-12_v14_status_r13_codex_record.md, literal ADOPT for controls
95d9bdfe version 14): v14 = adopted v13 840840f5 with ONLY chpc/row19_screen_status.py changed (REVISION 13). No v9 replay:
the v9 archive, epoch-1 activation, bench finish and pilot fit are NOT repeated.

    python3 chpc/migration_v14/promote_v14.py [--dry-run]          (from workspace_demo/t1_access)

Refuses unless: candidate_v14 controls = 95d9bdfe with latest entry version 14 pinning partition e1 8d1de408; the record is
4618b933 and holds the literal ADOPT line; every file the v14 entry pins equals its pin (status from candidate_v14/); the
current chpc/ controls/adoption/status are the ADOPTED v13 bytes (840840f5 / 150b7f6f / eeacc7e3). Then (not with --dry-run):
an immutable Mac archive chpc/results/archive/row19_screen_v13_before_v14/ (v13 controls, adoption, status and the Mac copy
of qualified_refit_job1.json, which step 8b later regenerates under its fixed name) with SHA256SUMS, read-only; copy the v14
controls and status into chpc/; write chpc/row19_screen_controls_adoption.json for version 14. Refuses if the archive exists.
Commit with explicit paths; deploy with deploy_v14.sh."""
import argparse, hashlib, json, os, shutil, sys

T1 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAND = "chpc/candidate_v14/"
V14 = "95d9bdfe4e4883b3e04d458a606c34d8504584b65e41344185beb8980df65630"
PART = ("chpc/row19_partition_e1.json", "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608")
REC = ("reviews/2026-10-12_v14_status_r13_codex_record.md", "4618b933904f35d1049e2d64e0b7db5e777e0ef458deb54fe6f506bdcc6285a5", "1de6dc0")
LINE = f"ADOPT row19-screen-controls sha256={V14} version=14"
V13 = {"chpc/row19_screen_controls.json": "840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c",
       "chpc/row19_screen_controls_adoption.json": "150b7f6ff47aa49b5850541655d835ce6d59183dcf02116664505ed3fea98bdf",
       "chpc/row19_screen_status.py": "eeacc7e36a833b653d7410e597189b3a154ec76b84225eaf736b8366cad9c9d9"}
QUAL = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
ARCH = "chpc/results/archive/row19_screen_v13_before_v14/"


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def problems():
    why = []
    if sha(CAND + "row19_screen_controls.json") != V14:
        why.append("candidate controls are not 95d9bdfe")
    c = json.load(open(os.path.join(T1, CAND, "row19_screen_controls.json"))); v = c["versions"][-1]
    if v.get("version") != 14 or (v.get("partition") or {}).get("sha256") != PART[1] or (v.get("partition") or {}).get("path") != PART[0]:
        why.append("the latest candidate entry is not version 14 pinning partition e1")
    if sha(PART[0]) != PART[1]:
        why.append("the partition file is not 8d1de408")
    if sha(REC[0]) != REC[1] or LINE not in [l.strip() for l in open(os.path.join(T1, REC[0])).read().splitlines()]:
        why.append("the review record is not 4618b933 with the literal ADOPT line")
    prev = c["versions"][-2]
    for f, h in sorted(v["files"].items()):
        src = CAND + os.path.basename(f) if f == "chpc/row19_screen_status.py" else f
        if not os.path.exists(os.path.join(T1, src)) or sha(src) != h:
            why.append(f"{src} is not the v14 pin for {f}")
        if f != "chpc/row19_screen_status.py" and prev["files"].get(f) != h:
            why.append(f"{f} differs from v13 (this cutover is status-only)")
    return why, v


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    why, v = problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    if sha("chpc/row19_screen_controls.json") == V14:
        print("already promoted (chpc controls are 95d9bdfe); nothing to do"); return 0
    bad = [f for f, h in V13.items() if sha(f) != h]
    if bad:
        print("REFUSED: not the adopted v13 bytes:", ", ".join(bad)); return 3
    if os.path.exists(os.path.join(T1, ARCH)):
        print(f"REFUSED: {ARCH} exists"); return 3
    plan = [f"archive -> {ARCH}: v13 controls/adoption/status + {os.path.basename(QUAL)} ({sha(QUAL)[:8]})",
            f"copy {CAND}row19_screen_controls.json, row19_screen_status.py -> chpc/",
            "write chpc/row19_screen_controls_adoption.json (version 14, review 1de6dc0)"]
    if a.dry_run:
        print("DRY RUN - checks pass; would:"); [print("  -", p) for p in plan]
        print("  pinned files:", len(v["files"])); return 0
    A = os.path.join(T1, ARCH); os.makedirs(A)
    for rel in list(V13) + [QUAL]:
        shutil.copy2(os.path.join(T1, rel), A)
    with open(os.path.join(A, "SHA256SUMS"), "w") as fh:
        for f in sorted(os.listdir(A)):
            if f != "SHA256SUMS":
                fh.write(f"{hashlib.sha256(open(os.path.join(A, f), 'rb').read()).hexdigest()}  {f}\n")
    for f in os.listdir(A):
        os.chmod(os.path.join(A, f), 0o444)
    for f in ("row19_screen_controls.json", "row19_screen_status.py"):
        shutil.copyfile(os.path.join(T1, CAND, f), os.path.join(T1, "chpc", f))
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": "chpc/row19_screen_controls.json", "controls_sha256": V14,
          "version": 14, "controls_commit": "70cbfd5",
          "review_record": {"path": REC[0], "sha256": REC[1], "commit": REC[2], "adopt_line": LINE},
          "by": "R052 Entropy SI (Claude)",
          "previous": {"version": 13, "controls_sha256": V13["chpc/row19_screen_controls.json"],
                       "adoption_sha256": V13["chpc/row19_screen_controls_adoption.json"],
                       "archived": "Lengau archive_screen/v13_before_v14, Mac " + ARCH},
          "scope": "status-only v13 -> v14 (Codex 1de6dc0; REVISION 13: settled refit memory keeps the largest direct value and "
                   "recorded breaches): every other controller byte, the epoch-1 partition 8d1de408 and the activation unchanged; "
                   "grants no job and no EC2 permission; fresh whole-role receipts and an adopted review of the REGENERATED refit "
                   "pilot qualification (new hash, max job 100, no new fit) precede any further gated refit admission"}
    open(os.path.join(T1, "chpc", "row19_screen_controls_adoption.json"), "w").write(json.dumps(ad, indent=1) + "\n")
    print("promoted: controls", sha("chpc/row19_screen_controls.json")[:16], "status", sha("chpc/row19_screen_status.py")[:16],
          "adoption", sha("chpc/row19_screen_controls_adoption.json")[:16],
          "archive SHA256SUMS", hashlib.sha256(open(os.path.join(A, "SHA256SUMS"), "rb").read()).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
