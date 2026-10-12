"""Cutover v14 -> v15, step 1 (Mac): promote the exact reviewed v15 controls + status + admission into chpc/ and write the adoption
record. Lineage (Codex RSC f1bede4, record reviews/2026-10-12_v15_r14_alias_repair_codex_record.md, literal ADOPT for controls
828d3b69 version 15): v15 = adopted v14 95d9bdfe with ONLY chpc/row19_screen_status.py and chpc/row19_screen_admit.py changed
(REVISION 14, crashed-worker slot disposition). No v9 replay: the v9 archive, epoch-1 activation, bench finish and pilot fit are
NOT repeated.

    python3 chpc/migration_v15/promote_v15.py [--dry-run]          (from workspace_demo/t1_access)

Refuses unless: candidate_v15 controls = 828d3b69 with latest entry version 15 pinning partition e1 8d1de408; versions 1-14
are byte-identical to the adopted controls; the record is c5167063 and holds the literal ADOPT line; every file the v15 entry
pins equals its pin (status and admission from candidate_v15/) and every other pin equals v14's; the current chpc/ controls/
adoption/status/admission are the ADOPTED v14 bytes (95d9bdfe / 1b292213 / 05d952bd / a5fac9a9). Then (not with --dry-run): an
immutable Mac archive chpc/results/archive/row19_screen_v14_before_v15/ (v14 controls, adoption, status, admission and the Mac
copy of qualified_refit_job1.json) with SHA256SUMS, read-only; copy the v15 controls, status and admission into chpc/; write
chpc/row19_screen_controls_adoption.json for version 15. Refuses if the archive exists. Commit with explicit paths; deploy
with deploy_v15.sh."""
import argparse, hashlib, json, os, shutil, sys

T1 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAND = "chpc/candidate_v15/"
V15 = "828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5"
CHANGED = ("chpc/row19_screen_status.py", "chpc/row19_screen_admit.py")
PART = ("chpc/row19_partition_e1.json", "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608")
REC = ("reviews/2026-10-12_v15_r14_alias_repair_codex_record.md", "c5167063220722457277f8c963ccfa3011423e2146aed8a0260b30c216c9db47", "f1bede4")
LINE = f"ADOPT row19-screen-controls sha256={V15} version=15"
V14 = {"chpc/row19_screen_controls.json": "95d9bdfe4e4883b3e04d458a606c34d8504584b65e41344185beb8980df65630",
       "chpc/row19_screen_controls_adoption.json": "1b292213feae553c1749d85a41cd31a3664e162c71028d00aa9c6e94f155af12",
       "chpc/row19_screen_status.py": "05d952bd67b73a71c3ddea2919b38e5abb1696af03f77a78a1d55f7be80a680b",
       "chpc/row19_screen_admit.py": "a5fac9a96e2073e9c89ca52ced9667692e4d65e838d93feb60b63fa5015fbeca"}
QUAL = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
ARCH = "chpc/results/archive/row19_screen_v14_before_v15/"


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def problems():
    why = []
    if sha(CAND + "row19_screen_controls.json") != V15:
        why.append("candidate controls are not 828d3b69")
    c = json.load(open(os.path.join(T1, CAND, "row19_screen_controls.json"))); v = c["versions"][-1]
    if c["versions"][:-1] != json.load(open(os.path.join(T1, "chpc/row19_screen_controls.json")))["versions"] and sha("chpc/row19_screen_controls.json") != V15:
        why.append("candidate versions 1-14 are not the adopted controls' versions")
    if v.get("version") != 15 or (v.get("partition") or {}).get("sha256") != PART[1] or (v.get("partition") or {}).get("path") != PART[0]:
        why.append("the latest candidate entry is not version 15 pinning partition e1")
    if sha(PART[0]) != PART[1]:
        why.append("the partition file is not 8d1de408")
    if sha(REC[0]) != REC[1] or LINE not in [l.strip() for l in open(os.path.join(T1, REC[0])).read().splitlines()]:
        why.append("the review record is not c5167063 with the literal ADOPT line")
    prev = c["versions"][-2]
    for f, h in sorted(v["files"].items()):
        src = CAND + os.path.basename(f) if f in CHANGED else f
        if not os.path.exists(os.path.join(T1, src)) or sha(src) != h:
            why.append(f"{src} is not the v15 pin for {f}")
        if f not in CHANGED and prev["files"].get(f) != h:
            why.append(f"{f} differs from v14 (this cutover changes only status and admission)")
    if sorted(v["files"]) != sorted(prev["files"]):
        why.append("the v15 entry pins another file set than v14")
    return why, v


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    why, v = problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    if sha("chpc/row19_screen_controls.json") == V15:
        print("already promoted (chpc controls are 828d3b69); nothing to do"); return 0
    bad = [f for f, h in V14.items() if sha(f) != h]
    if bad:
        print("REFUSED: not the adopted v14 bytes:", ", ".join(bad)); return 3
    if os.path.exists(os.path.join(T1, ARCH)):
        print(f"REFUSED: {ARCH} exists"); return 3
    plan = [f"archive -> {ARCH}: v14 controls/adoption/status/admission + {os.path.basename(QUAL)} ({sha(QUAL)[:8]})",
            f"copy {CAND}row19_screen_controls.json, row19_screen_status.py, row19_screen_admit.py -> chpc/",
            "write chpc/row19_screen_controls_adoption.json (version 15, review f1bede4)"]
    if a.dry_run:
        print("DRY RUN - checks pass; would:"); [print("  -", p) for p in plan]
        print("  pinned files:", len(v["files"])); return 0
    A = os.path.join(T1, ARCH); os.makedirs(A)
    for rel in list(V14) + [QUAL]:
        shutil.copy2(os.path.join(T1, rel), A)
    with open(os.path.join(A, "SHA256SUMS"), "w") as fh:
        for f in sorted(os.listdir(A)):
            if f != "SHA256SUMS":
                fh.write(f"{hashlib.sha256(open(os.path.join(A, f), 'rb').read()).hexdigest()}  {f}\n")
    for f in os.listdir(A):
        os.chmod(os.path.join(A, f), 0o444)
    for f in ("row19_screen_controls.json", "row19_screen_status.py", "row19_screen_admit.py"):
        shutil.copyfile(os.path.join(T1, CAND, f), os.path.join(T1, "chpc", f))
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": "chpc/row19_screen_controls.json", "controls_sha256": V15,
          "version": 15, "controls_commit": "b6ea998",
          "review_record": {"path": REC[0], "sha256": REC[1], "commit": REC[2], "adopt_line": LINE},
          "by": "R052 Entropy SI (Claude)",
          "previous": {"version": 14, "controls_sha256": V14["chpc/row19_screen_controls.json"],
                       "adoption_sha256": V14["chpc/row19_screen_controls_adoption.json"],
                       "archived": "Lengau archive_screen/v14_before_v15, Mac " + ARCH},
          "scope": "status + admission v14 -> v15 (Codex f1bede4; REVISION 14: crashed-worker slot disposition - a settled refit job "
                   "whose only defect is planned workers killed by their own fatal signal; its crashed coordinates return to the "
                   "planner uncompleted, nothing credited, the job never qualifies): every other controller byte, the epoch-1 "
                   "partition 8d1de408 and the activation unchanged; "
                   "grants no job and no EC2 permission; fresh whole-role receipts and an adopted review of the REGENERATED refit "
                   "pilot qualification (new hash, max job 100, no new fit) precede any further gated refit admission"}
    open(os.path.join(T1, "chpc", "row19_screen_controls_adoption.json"), "w").write(json.dumps(ad, indent=1) + "\n")
    print("promoted: controls", sha("chpc/row19_screen_controls.json")[:16], "status", sha("chpc/row19_screen_status.py")[:16],
          "adoption", sha("chpc/row19_screen_controls_adoption.json")[:16],
          "archive SHA256SUMS", hashlib.sha256(open(os.path.join(A, "SHA256SUMS"), "rb").read()).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
