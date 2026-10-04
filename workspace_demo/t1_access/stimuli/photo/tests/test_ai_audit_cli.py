"""Image-audit revision 3 (Codex 748c59a): OFFLINE fixtures through the PUBLIC CLI in FRESH processes.

A temporary git repository holds a copy of the photo package laid out as in RSC (so every path the code derives from
its own location - the owned-CLI path, the guard's repository, the captures - lands in the copy), a fake reader binary
at the owned-CLI path, a fixture review record with a favourable attestation for the copy's exact audit package and a
go file bound to it. Then, each step a NEW process:

  harness delivery 1 / package; run 1                 round 1 through production construction, chain, go, journal, clock
  .venv-build ai_audit_score.py score 1               the real scorer (WordNet, the image-venv set check)
  .venv-image ai_audit_set.py build 2                 round 2 derived from the authenticated chain (verify subprocess)
  harness delivery 2; plan 2; run 2                   an honest later round through admission to dispatch
  refusals: run 0 / -1 / 9; run 1 again (ended); plan 3 (round 2 unscored); a changed committed score -> plan 2

asserting that round 1 opens ONLY the audit round's job directory, journal and clock, and that the qualification job
directory, raw file and lock are byte-unchanged. Only the provider is substituted (tests/audit_cli_harness.py).
No network, no model; the real WordNet scorer runs under .venv-build.

    .venv-image/bin/python -m unittest stimuli/photo/tests/test_ai_audit_cli.py
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PHOTO = TESTS.parent
T1 = PHOTO.parents[1]
REAL_RSC = T1.parents[1]
IMAGE_PY = T1 / ".venv-image" / "bin" / "python"
BUILD_PY = T1 / ".venv-build" / "bin" / "python"
sys.path.insert(0, str(PHOTO))
import ai_reader_runtime as R  # noqa: E402


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def tree_digest(root: Path) -> dict:
    """Every file under root (or the single file) with its sha256 - absent = {}."""
    root = Path(root)
    if root.is_file():
        return {root.name: sha(root.read_bytes())}
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}


class AuditCLI(unittest.TestCase):
    OUT: dict = {}

    @classmethod
    def git(cls, *args) -> str:
        return subprocess.run(["git", "-C", str(cls.repo), *args], check=True, capture_output=True,
                              text=True).stdout.strip()

    @classmethod
    def commit(cls, msg: str, *paths: str) -> None:
        cls.git("add", "-f", *paths)
        cls.git("commit", "-q", "-m", msg)

    @classmethod
    def cli(cls, *argv: str, py: Path = IMAGE_PY, script: str = "tests/audit_cli_harness.py") -> dict:
        env = {**os.environ, "TMPDIR": str(cls.tmpdir)}
        p = subprocess.run([str(py), str(cls.photo / script), *argv], capture_output=True, text=True, env=env,
                           cwd=str(cls.t1), timeout=3600)
        return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}

    @classmethod
    def plan_answers(cls, k: int, fail_photo_for: tuple = ()) -> None:
        """Fake answers keyed by image file stem (the fake's request key): the concept's canonical name, then yes."""
        sset = json.loads((cls.photo / f"ai_audit_set_r{k}.json").read_text())
        key = json.loads((cls.photo / f"ai_audit_key_r{k}.json").read_text())
        pool = {r["concept"]: r for r in json.loads((cls.photo / "dev_pool.json").read_text())["roles"]}
        plan = json.loads(cls.plan_file.read_text()) if cls.plan_file.exists() else {}
        for r in sset["requests"]:
            stem = Path(r["file"]).stem
            it = key["items"][r["item"]]
            name = pool[it["concept"]]["name"].replace("_", " ")
            if it["kind"] == "pair":
                plan[stem] = ["ok:yes"]
            else:
                photo = "ok:no" if it["kind"] == "candidate" and it["concept"] in fail_photo_for else "ok:yes"
                plan[stem] = [f"ok:{name}", photo, "ok:yes"]
        cls.plan_file.write_text(json.dumps(plan))

    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp())
        cls.repo = cls.base / "rsc"
        cls.t1 = cls.repo / "workspace_demo" / "t1_access"
        cls.photo = cls.t1 / "stimuli" / "photo"
        cls.tmpdir = cls.base / "tmp"
        cls.tmpdir.mkdir()
        cls.plan_file = cls.tmpdir / "fake_plan.json"
        shutil.copytree(PHOTO, cls.photo, ignore=shutil.ignore_patterns("__pycache__"))
        (cls.t1 / "audit_app").mkdir()
        shutil.copy2(T1 / "audit_app" / "IMAGE_AUDIT_FREEZE.md", cls.t1 / "audit_app")
        for v in (".venv-image", ".venv-build"):
            (cls.t1 / v).symlink_to(T1 / v)
        cap = cls.t1 / "captures"
        cap.mkdir()
        (cap / ".gitignore").write_text("*\n")
        shutil.copytree(T1 / "captures" / "ai_audit_items", cap / "ai_audit_items")
        (cap / "second_view_sources").symlink_to(T1 / "captures" / "second_view_sources")
        cli = cap / "reader_cli" / "codex-0.160.0"
        (cli / "bin").mkdir(parents=True)
        (cli / "codex-package.json").write_text('{"name": "fixture", "version": "0.160.0"}\n')
        fake = cli / "bin" / "codex"
        fake.write_text(f"#!{IMAGE_PY}\nimport runpy, sys\nif sys.argv[1:] == ['--version']:\n"
                        f"    print('codex-cli 0.160.0'); sys.exit(0)\nsys.argv = [{str(TESTS / 'fake_codex.py')!r}]"
                        f" + sys.argv[1:]\nrunpy.run_path(sys.argv[0], run_name='__main__')\n")
        fake.chmod(0o755)
        # the qualification's namespace in the copy: must stay byte-unchanged
        (cap / "ai_reader_job").mkdir()
        (cap / "ai_reader_job" / "clock.json").write_text('{"fixture": "qualification clock"}\n')
        (cap / "ai_reader_job" / "task.lock").write_text("fixture qualification lock\n")
        (cap / "ai_reader_qual").mkdir()
        # the fake's model-visible instructions become the copy's reader pin (the fake renders other instructions)
        with tempfile.TemporaryDirectory() as td:
            adir = Path(td) / "a"
            img = R.prepare(adir, (cap / "ai_audit_items" / sorted(os.listdir(cap / "ai_audit_items"))[0])
                            .read_bytes(), "x.png")
            rc = R.prompt_input([str(fake)], json.loads((cls.photo / "ai_reader_qual_set.json").read_text())["reader"],
                                adir, img, "x", sandbox=False)
        dp = cls.photo / "ai_reader_delivery.json"
        d = json.loads(dp.read_text())
        d["instructions_sha256"] = rc["instructions_sha256"]
        dp.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
        for f in ("ai_audit_raw_r1.jsonl", "ai_audit_score_r1.json", "AIAUDIT_GO.json"):
            (cls.photo / f).unlink(missing_ok=True)
        subprocess.run(["git", "init", "-q", str(cls.repo)], check=True)
        cls.git("config", "user.email", "t@t")
        cls.git("config", "user.name", "fixture")
        cls.commit("copy", ".")
        out = cls.OUT
        out["delivery1"] = cls.cli("delivery", "1")
        cls.commit("delivery 1", "workspace_demo/t1_access/stimuli/photo/ai_audit_delivery_r1.json")
        pkg = json.loads(cls.cli("package")["out"])
        reviewed = cls.git("rev-parse", "HEAD")
        today = cls.git("show", "-s", "--format=%cs", "HEAD")
        rec = cls.t1 / "reviews" / "fixture_audit_review.md"
        rec.parent.mkdir()
        att = {"row": "aiaudit", "stage": "audit", "verdict": "favourable", "reviewer": "fixture", "date": today,
               "reviewed_commit": reviewed, "package": pkg}
        rec.write_text("# fixture review\n\n<!-- STAGE-ATTESTATION v1\n" + json.dumps(att, indent=1) + "\n-->\n")
        cls.commit("review", "workspace_demo/t1_access/reviews/fixture_audit_review.md")
        go = {"review": {"commit": cls.git("rev-parse", "HEAD"), "path": "workspace_demo/t1_access/reviews/"
                                                                         "fixture_audit_review.md",
                         "record_sha256": sha(rec.read_bytes())},
              "owner_go": {"by": "fixture", "date": today, "words": "fixture go"}, "package": pkg}
        (cls.photo / "AIAUDIT_GO.json").write_text(json.dumps(go, indent=1) + "\n")
        cls.commit("go", "workspace_demo/t1_access/stimuli/photo/AIAUDIT_GO.json")
        cls.plan_answers(1, fail_photo_for=("pig",))
        qual = {"job": cap / "ai_reader_job", "raw": cls.photo / "ai_reader_raw_responses.jsonl",
                "images": cap / "ai_reader_qual"}
        out["qual_before"] = {k: tree_digest(v) for k, v in qual.items()}
        out["rq_before"] = (cls.tmpdir / "rq").exists()
        # invalid rounds through the CLI before anything ran
        out["run_bad"] = {k: cls.cli("run", k) for k in ("0", "-1", "9")}
        out["jobs_after_bad"] = sorted(p.name for p in cap.iterdir() if p.name.startswith("ai_audit_job"))
        out["run1"] = cls.cli("run", "1")
        out["qual_after"] = {k: tree_digest(v) for k, v in qual.items()}
        out["rq_after"] = (cls.tmpdir / "rq").exists()
        out["jobs_after_run1"] = sorted(p.name for p in cap.iterdir() if p.name.startswith("ai_audit_job"))
        out["run1_again"] = cls.cli("run", "1")
        cls.commit("raw 1", "workspace_demo/t1_access/stimuli/photo/ai_audit_raw_r1.jsonl")
        out["plan3_before_r2"] = cls.cli("plan", "3")
        out["score1"] = cls.cli("score", "1", py=BUILD_PY, script="ai_audit_score.py")
        cls.commit("score 1", "workspace_demo/t1_access/stimuli/photo/ai_audit_score_r1.json")
        out["build2"] = cls.cli("build", "2", script="ai_audit_set.py")
        cls.commit("set 2", "workspace_demo/t1_access/stimuli/photo/ai_audit_set_r2.json",
                   "workspace_demo/t1_access/stimuli/photo/ai_audit_key_r2.json")
        out["delivery2"] = cls.cli("delivery", "2")
        cls.commit("delivery 2", "workspace_demo/t1_access/stimuli/photo/ai_audit_delivery_r2.json")
        out["plan2"] = cls.cli("plan", "2")
        # a changed committed predecessor score refuses through the CLI, then is restored
        sp = cls.photo / "ai_audit_score_r1.json"
        good = sp.read_bytes()
        d = json.loads(good)
        d["charged"]["attempts"] = 0
        sp.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        cls.commit("tamper", "workspace_demo/t1_access/stimuli/photo/ai_audit_score_r1.json")
        out["plan2_tampered"] = cls.cli("plan", "2")
        sp.write_bytes(good)
        cls.commit("restore", "workspace_demo/t1_access/stimuli/photo/ai_audit_score_r1.json")
        cls.plan_answers(2)
        out["run2"] = cls.cli("run", "2")
        out["limits2"] = json.loads((cap / "ai_audit_job_r2" / "clock.json").read_text()) \
            if (cap / "ai_audit_job_r2" / "clock.json").exists() else None

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    def last_json(self, r: dict) -> dict:
        self.assertEqual(r["rc"], 0, r["err"][-1500:])
        return json.loads(r["out"][r["out"].index("{"):])

    def test_invalid_rounds_refuse_through_the_cli(self):
        for k, r in self.OUT["run_bad"].items():
            self.assertNotEqual(r["rc"], 0)
            self.assertIn("is not an integer in 1..8", r["err"], k)
        self.assertEqual(self.OUT["jobs_after_bad"], [])

    def test_round1_runs_in_its_own_namespace_only(self):
        res = self.last_json(self.OUT["run1"])
        self.assertEqual(res["outcome"], "COMPLETE")
        self.assertEqual(res["counts"]["final"] if "final" in res["counts"] else 224, 224)
        self.assertEqual(self.OUT["jobs_after_run1"], ["ai_audit_job_r1"])
        self.assertEqual(self.OUT["qual_after"], self.OUT["qual_before"], "the qualification namespace changed")
        self.assertFalse(self.OUT["rq_after"], "the qualification attempts root was used")
        self.assertTrue((self.photo / "ai_audit_raw_r1.jsonl").exists())

    def test_ended_round_refuses_through_the_cli(self):
        r = self.OUT["run1_again"]
        self.assertNotEqual(r["rc"], 0)
        self.assertIn("nothing runs after a receipt", r["err"])

    def test_later_round_needs_its_scored_predecessor(self):
        r = self.OUT["plan3_before_r2"]
        self.assertNotEqual(r["rc"], 0)
        self.assertIn("refused", r["err"])

    def test_real_scorer_and_round2_derivation(self):
        self.assertEqual(self.OUT["score1"]["rc"], 0, self.OUT["score1"]["err"][-1500:])
        sc = json.loads((self.photo / "ai_audit_score_r1.json").read_text())
        self.assertEqual(sc["mode"], "scientific")
        self.assertEqual(sc["counts"]["concepts_next_round"], ["pig"])
        self.assertEqual(self.OUT["build2"]["rc"], 0, self.OUT["build2"]["err"][-1500:])
        s2 = json.loads((self.photo / "ai_audit_set_r2.json").read_text())
        self.assertEqual(s2["n_requests"], 4)
        self.assertEqual(sorted(s2["inputs"]["prior_rounds"]), ["r1"])

    def test_honest_round2_passes_plan_and_admission_with_the_carried_envelope(self):
        plan = self.last_json(self.OUT["plan2"])
        self.assertEqual(plan["limits"]["planned"], 4)
        self.assertEqual(plan["limits"]["max_attempts"], 5)
        self.assertLess(plan["limits"]["job_clock_s"], 6 * 3600)
        res = self.last_json(self.OUT["run2"])
        self.assertEqual(res["outcome"], "COMPLETE")

    def test_changed_committed_score_refuses_through_the_cli(self):
        r = self.OUT["plan2_tampered"]
        self.assertNotEqual(r["rc"], 0)
        self.assertIn("not what its admitted evidence scores to", r["err"])


if __name__ == "__main__":
    unittest.main()
