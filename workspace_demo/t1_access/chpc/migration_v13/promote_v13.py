"""Migration v9 -> v13, step 3 (Mac): promote the exact reviewed v13 controller bytes into chpc/ and write the adoption record
(Codex RSC 64034c5: direct v9 -> v13; the actually adopted v9 - not the never-adopted v12 - is the archived predecessor).

    python3 chpc/migration_v13/promote_v13.py [--dry-run]          (from workspace_demo/t1_access)

Checks first (refuses on any): candidate controls = d933862e, its latest entry is version 13 pinning partition e1 8d1de408;
the review record = 99f059ff and holds the literal ADOPT line; every file the v13 entry pins equals its pin (admit/status from
candidate_v10r4/, which must equal the pins); the current chpc/ controls/adoption are the adopted v9 bytes (45f840bc / 42b99b4d).
Then (not with --dry-run): an immutable Mac archive chpc/results/archive/row19_screen_v9_before_v13/ (v9 controls, adoption,
admit, status, verify, and the Mac copy of qualified_refit_job1.json 3820ac0e) with SHA256SUMS, read-only; copy the v13
controls/admit/status into chpc/; write chpc/row19_screen_controls_adoption.json for version 13. Refuses if the archive exists.
Commit the result with explicit paths; deploy with deploy_v13.sh."""
import argparse, hashlib, json, os, shutil, sys

T1 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAND = "chpc/candidate_v10r4/"
V13 = "d933862e7031acad1c5a864ffec0c9e4b295c4101a88e2e4a1691deef12636da"
PART = ("chpc/row19_partition_e1.json", "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608")
REC = ("reviews/2026-10-11_partition_e1_v13_codex_record.md", "99f059ffb5cbf97d114e9462b8d60e4e9fb132c4318b1717795e56d0dd4479e5", "64034c5")
LINE = f"ADOPT row19-screen-controls sha256={V13} version=13"
V9 = {"chpc/row19_screen_controls.json": "45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07",
      "chpc/row19_screen_controls_adoption.json": "42b99b4d4ceda4bf"}            # adoption: prefix check (as deployed on Lengau)
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "3820ac0e0c28a9cf484f02be3a9c377891aa81595413978d74e7de1eddee4678")
ARCH = "chpc/results/archive/row19_screen_v9_before_v13/"


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def problems():
    why = []
    if sha(CAND + "row19_screen_controls.json") != V13:
        why.append("candidate controls are not d933862e")
    c = json.load(open(os.path.join(T1, CAND, "row19_screen_controls.json"))); v = c["versions"][-1]
    if v.get("version") != 13 or (v.get("partition") or {}).get("sha256") != PART[1] or (v.get("partition") or {}).get("path") != PART[0]:
        why.append("the latest candidate entry is not version 13 pinning partition e1")
    if sha(PART[0]) != PART[1]:
        why.append("the partition file is not 8d1de408")
    if sha(REC[0]) != REC[1] or LINE not in [l.strip() for l in open(os.path.join(T1, REC[0])).read().splitlines()]:
        why.append("the review record is not 99f059ff with the literal ADOPT line")
    for f, h in sorted(v["files"].items()):
        src = CAND + os.path.basename(f) if f in ("chpc/row19_screen_admit.py", "chpc/row19_screen_status.py") else f
        if not os.path.exists(os.path.join(T1, src)) or sha(src) != h:
            why.append(f"{src} is not the v13 pin for {f}")
    if sha("chpc/row19_screen_controls.json") != V9["chpc/row19_screen_controls.json"] and sha("chpc/row19_screen_controls.json") != V13:
        why.append("chpc/row19_screen_controls.json is neither adopted v9 nor v13")
    return why, v


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    why, v = problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    if sha("chpc/row19_screen_controls.json") == V13:
        print("already promoted (chpc controls are d933862e); nothing to do"); return 0
    if os.path.exists(os.path.join(T1, ARCH)):
        print(f"REFUSED: {ARCH} exists"); return 3
    if not sha("chpc/row19_screen_controls_adoption.json").startswith(V9["chpc/row19_screen_controls_adoption.json"]):
        print("REFUSED: the current adoption record is not the adopted v9 record 42b99b4d"); return 3
    if sha(QUAL[0]) != QUAL[1]:
        print("REFUSED: the Mac copy of qualified_refit_job1.json is not 3820ac0e"); return 3
    plan = [f"archive -> {ARCH}: v9 controls/adoption/admit/status/verify + {os.path.basename(QUAL[0])}",
            f"copy {CAND}row19_screen_controls.json, row19_screen_admit.py, row19_screen_status.py -> chpc/",
            "write chpc/row19_screen_controls_adoption.json (version 13, review 64034c5)"]
    if a.dry_run:
        print("DRY RUN - checks pass; would:"); [print("  -", p) for p in plan]
        print("  pinned files:", len(v["files"])); return 0
    A = os.path.join(T1, ARCH); os.makedirs(A)
    for rel in ("chpc/row19_screen_controls.json", "chpc/row19_screen_controls_adoption.json", "chpc/row19_screen_admit.py",
                "chpc/row19_screen_status.py", "chpc/row19_screen_verify.py", QUAL[0]):
        shutil.copy2(os.path.join(T1, rel), A)
    with open(os.path.join(A, "SHA256SUMS"), "w") as fh:
        for f in sorted(os.listdir(A)):
            if f != "SHA256SUMS":
                fh.write(f"{hashlib.sha256(open(os.path.join(A, f), 'rb').read()).hexdigest()}  {f}\n")
    for f in os.listdir(A):
        os.chmod(os.path.join(A, f), 0o444)
    prev_ad = sha("chpc/row19_screen_controls_adoption.json")
    for f in ("row19_screen_controls.json", "row19_screen_admit.py", "row19_screen_status.py"):
        shutil.copyfile(os.path.join(T1, CAND, f), os.path.join(T1, "chpc", f))
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": "chpc/row19_screen_controls.json", "controls_sha256": V13,
          "version": 13, "controls_commit": "fa2c325",
          "review_record": {"path": REC[0], "sha256": REC[1], "commit": REC[2], "adopt_line": LINE},
          "by": "R052 Entropy SI (Claude)",
          "previous": {"version": 9, "controls_sha256": V9["chpc/row19_screen_controls.json"], "adoption_sha256": prev_ad,
                       "archived": "Lengau archive_screen/v9_before_v13, Mac " + ARCH},
          "scope": "direct v9 -> v13 (Codex 64034c5): controllers + the epoch-1 partition 8d1de408 pinned; grants no job and no EC2 "
                   "permission; canonical activation under the plan lock, fresh whole-role v13 receipts and an adopted review of the "
                   "REGENERATED refit pilot qualification (new hash, max job 100, no new fit) precede any further gated refit admission"}
    open(os.path.join(T1, "chpc", "row19_screen_controls_adoption.json"), "w").write(json.dumps(ad, indent=1) + "\n")
    print("promoted: controls", sha("chpc/row19_screen_controls.json")[:16], "adoption", sha("chpc/row19_screen_controls_adoption.json")[:16],
          "archive SHA256SUMS", hashlib.sha256(open(os.path.join(A, "SHA256SUMS"), "rb").read()).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
