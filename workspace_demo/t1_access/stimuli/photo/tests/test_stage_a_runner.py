"""Stage A revision 3: runner, validator, recovery, attestation and identity tests on a fake instrument - no model
is imported, loaded or run. Controller mechanism fixtures are in test_controller.py.

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fake_stage_a as F  # noqa: E402
import enforce  # noqa: E402
import stage_a  # noqa: E402
import stage_a_guard as G  # noqa: E402
import stage_a_report as R  # noqa: E402

PY = sys.executable
PLAN = json.loads(stage_a.PLAN.read_text())
N_INST = sum(a["phase"] == "instrumented" for a in PLAN["attempts"])


def state(out: Path) -> dict:
    return json.loads((out / "stage_a_state.json").read_text())


def full_run(out: Path) -> None:
    stage_a.run_instrumented(F.make_ctx(out))
    stage_a.run_native(F.make_ctx(out))


class StageA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "photo_stage_a"
        os.environ.pop("STAGE_A_GATES_OK", None)

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("STAGE_A_GATES_OK", None)

    def test_full_pass_validator(self):
        full_run(self.out)
        c = state(self.out)["counters"]["row20"]
        self.assertEqual((c["started"], c["completed"], c["failed"], c["passes"]), (194, 193, 1, 194))
        os.environ["STAGE_A_GATES_OK"] = "1"
        r = stage_a.run_report(F.make_ctx(self.out))
        self.assertTrue(r["validator_pass"], json.loads((self.out / "report/stage_a_report.json").read_text())
                        ["validator"]["failures"][:3])
        rep = json.loads((self.out / "report/stage_a_report.json").read_text())
        self.assertEqual((rep["unique_planned_ids"], rep["actual_tries"]), (178, 178))
        self.assertFalse(rep["stage_b_admission"]["admitted"])               # a report never admits B

    def test_diagnostic_report_confers_nothing(self):
        full_run(self.out)
        r = stage_a.run_report(F.make_ctx(self.out))                         # STAGE_A_GATES_OK unset
        self.assertFalse(r["validator_pass"])

    def test_bitwise_failure_is_terminal_in_both_phases(self):
        with self.assertRaises(stage_a.StopCheck):
            stage_a.run_instrumented(F.make_ctx(self.out, {"differ": [3, "zero_swap"]}))
        t = json.loads((self.out / "TERMINAL.json").read_text())
        self.assertIn("bitwise parity failure", t["first"]["reason"])
        for run in (stage_a.run_instrumented, stage_a.run_native):
            with self.assertRaises(SystemExit) as e:
                run(F.make_ctx(self.out))
            self.assertIn("stopped terminally", str(e.exception))
        os.environ["STAGE_A_GATES_OK"] = "1"
        self.assertFalse(stage_a.run_report(F.make_ctx(self.out))["validator_pass"])

    def test_native_parity_failure_is_terminal(self):
        stage_a.run_instrumented(F.make_ctx(self.out))
        with self.assertRaises(stage_a.StopCheck):
            stage_a.run_native(F.make_ctx(self.out, {"native_off": 5}))

    def test_native_refused_before_instrumented(self):
        with self.assertRaises(SystemExit):
            stage_a.run_native(F.make_ctx(self.out))

    def test_crash_recovery_is_per_try_and_consumed(self):
        p = subprocess.run([PY, str(HERE / "fake_stage_a.py"), str(self.out), json.dumps({"exit_at_call": 40,
                            "session": "s1"})], capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, 9, p.stderr[-1500:])
        crashed = state(self.out)["open_attempt"]["id"]
        with self.assertRaises(SystemExit) as e:                             # holds without a recovery file
            stage_a.run_instrumented(F.make_ctx(self.out))
        self.assertIn("interrupted tries without a recovery file", str(e.exception))
        good = {"attempt_id": crashed, "session": "s1", "try": 1, "owner": "test", "date": "2026-10-02",
                "reason": "test crash"}
        (self.out / f"RECOVERY_{crashed}__s1__1.json").write_text(json.dumps(good))
        p = subprocess.run([PY, str(HERE / "fake_stage_a.py"), str(self.out), json.dumps({"exit_at_call": 1,
                            "session": "s2"})], capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, 9, p.stderr[-1500:])                  # the SAME id crashes again
        st = state(self.out)
        self.assertEqual(len(st["recoveries_consumed"]), 1)
        with self.assertRaises(SystemExit):                                 # the old file cannot serve again
            stage_a.run_instrumented(F.make_ctx(self.out))
        (self.out / f"RECOVERY_{crashed}__s2__2.json").write_text(json.dumps({**good, "session": "s2", "try": 2}))
        stage_a.run_instrumented(F.make_ctx(self.out))
        st = state(self.out)
        self.assertEqual(st["counters"]["row20"]["started"], 16 + N_INST + 2)    # both crashed tries counted
        self.assertEqual(st["attempts"][crashed]["tries"], 3)

    def test_corrupt_committed_output_holds(self):
        stage_a.run_instrumented(F.make_ctx(self.out))
        victim = self.out / "passes" / "07-zero_ablate.residuals.npy"
        b = bytearray(victim.read_bytes())
        b[-1] ^= 0xFF
        victim.write_bytes(bytes(b))
        with self.assertRaises(stage_a.StopCheck) as e:
            stage_a.run_native(F.make_ctx(self.out))
        self.assertIn("hold for diagnosis", str(e.exception))


class ValidatorMutations(unittest.TestCase):
    """Committed outputs tampered CONSISTENTLY (hashes in the state updated) so each check is reached on its own."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name) / "base"
        full_run(cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def copy(self) -> Path:
        import shutil
        d = Path(tempfile.mkdtemp()) / "o"
        shutil.copytree(self.base, d)
        return d

    def codes(self, out: Path) -> set:
        st = json.loads((out / "stage_a_state.json").read_text())
        return {f["code"] for f in R.validate(out, PLAN, st)["failures"]}

    def rewrite(self, out: Path, aid: str, record=None, array=None):
        st = json.loads((out / "stage_a_state.json").read_text())
        outs = st["completed"][aid]["outputs"]
        for rel in list(outs):
            p = out / rel
            if rel.endswith(".npy") and array is not None:
                np.save(p, array, allow_pickle=False)
            if rel.endswith(".json") and record is not None:
                p.write_text(json.dumps(record))
            outs[rel] = enforce.write_json_atomic.__globals__["json"] and __import__("hashlib").sha256(
                p.read_bytes()).hexdigest()
        (out / "stage_a_state.json").write_text(json.dumps(st))
        return st

    def rec(self, out, aid):
        return json.loads((out / f"passes/{aid}.json").read_text())

    def test_clean_base_passes(self):
        self.assertEqual(self.codes(self.copy()), set())

    def test_hash_tamper(self):
        out = self.copy()
        p = out / "passes/03-native.residuals.npy"
        b = bytearray(p.read_bytes()); b[-1] ^= 1; p.write_bytes(bytes(b))
        self.assertIn("OUTPUT_HASH", self.codes(out))

    def test_wrong_case_in_record(self):
        out = self.copy()
        r = self.rec(out, "02-empty"); r["case"] = "plain"
        self.rewrite(out, "02-empty", record=r)
        self.assertIn("RECORD_ID", self.codes(out))

    def test_nonfinite_native(self):
        out = self.copy()
        a = np.load(out / "passes/04-native.residuals.npy"); a[0, 0, 0] = np.nan
        r = self.rec(out, "04-native"); r["residuals_sha256"] = __import__("hashlib").sha256(
            np.ascontiguousarray(a).tobytes()).hexdigest()
        self.rewrite(out, "04-native", record=r, array=a)
        c = self.codes(out)
        self.assertIn("NONFINITE", c)

    def test_parity_summary_unbound(self):
        out = self.copy()
        rows = json.loads((out / "native_parity.json").read_text())
        (out / "native_parity.json").write_text(json.dumps([rows[0]] * 20))   # twenty duplicate passing rows
        self.assertIn("PARITY_SUMMARY_MISMATCH", self.codes(out))

    def test_failing_numbers_marked_pass(self):
        out = self.copy()
        r = self.rec(out, "06-native"); r["requested_logits"] = [v + 1.0 for v in r["requested_logits"]]
        self.rewrite(out, "06-native", record=r)
        self.assertIn("PARITY", self.codes(out))                              # recomputed, not read

    def test_phase_record_mismatch(self):
        out = self.copy()
        d = json.loads((out / "NATIVE_DONE.json").read_text()); d["attempts"].pop("00-native")
        (out / "NATIVE_DONE.json").write_text(json.dumps(d))
        self.assertIn("PHASE_RECORD_MISMATCH", self.codes(out))

    def test_suffix_leak_and_encoder_insensitive(self):
        out = self.copy()
        r = self.rec(out, "01-suffix_isolation"); r["residuals_sha256"] = "0" * 64
        self.rewrite(out, "01-suffix_isolation", record=r)
        r6 = self.rec(out, "06-plain"); r1 = self.rec(out, "01-plain")
        r6["image"]["features_sha256"] = r1["image"]["features_sha256"]
        self.rewrite(out, "06-plain", record=r6)
        c = self.codes(out)
        self.assertTrue({"SUFFIX_ISOLATION", "ENCODER_SENSITIVITY"} <= c, c)

    def test_embedding_difference_fails(self):
        out = self.copy()
        r = self.rec(out, "08-native"); r["inputs_embeds_equal_instrumented_merge"] = False
        self.rewrite(out, "08-native", record=r)
        self.assertIn("EMBEDDINGS", self.codes(out))


class Units(unittest.TestCase):
    def test_cases(self):
        self.assertIsNone(stage_a.edits_for(F.FakeCE(), "repeat", {}, {"marker_positions": [1, 2, 3]}, None))
        with self.assertRaises(ValueError):
            stage_a.edits_for(F.FakeCE(), "rescue", {}, {"marker_positions": [1, 2, 3]}, None)

    def test_attempt_without_commit_fails_and_is_never_retried(self):
        with tempfile.TemporaryDirectory() as d:
            b = enforce.Budget(Path(d) / "s.json", "row20", "id", [Path(d)], "t")
            for _ in range(2):
                with self.assertRaises(enforce.StopRun):
                    with b.attempt("a", "test"):
                        pass
            c = json.loads((Path(d) / "s.json").read_text())["counters"]["row20"]
            self.assertEqual((c["started"], c["failed"]), (1, 1))

    def test_storage_reserve_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "x").write_bytes(b"0" * 1000)
            b = enforce.Budget(Path(d) / "s.json", "row20", "id", [Path(d)], "t", storage_limit=2000)
            with self.assertRaises(enforce.StopRun):
                b.reserve(500)

    def test_identity_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            enforce.Budget(Path(d) / "s.json", "row20", "one", [Path(d)], "t")
            with self.assertRaises(enforce.StopRun):
                enforce.Budget(Path(d) / "s.json", "row20", "two", [Path(d)], "t")

    def test_imported_origin_and_changed_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "pkgroot" / "watchedpkg"
            root.mkdir(parents=True)
            (root / "__init__.py").write_text("X = 1\n")
            maps = Path(d) / "maps.json"
            maps.write_text(json.dumps({"watchedpkg": {"root": str(root), "files": {"__init__.py": G.sha_file(
                root / "__init__.py")}}}))
            other = Path(d) / "elsewhere" / "watchedpkg"
            other.mkdir(parents=True)
            (other / "__init__.py").write_text("X = 2\n")
            for where, expect_ok in ((root, True), (other, False)):
                sys.modules.pop("watchedpkg", None)
                mod = types.ModuleType("watchedpkg"); mod.__file__ = str(where / "__init__.py")
                sys.modules["watchedpkg"] = mod
                if expect_ok:
                    G.check_imported_origins(maps)
                else:
                    with self.assertRaises(SystemExit):
                        G.check_imported_origins(maps)
            (root / "__init__.py").write_text("X = 3\n")                    # a changed file at the right origin
            mod.__file__ = str(root / "__init__.py")
            with self.assertRaises(SystemExit):
                G.check_imported_origins(maps)
            sys.modules.pop("watchedpkg", None)


class GoAttestation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q"); self.git("config", "user.email", "t@t"); self.git("config", "user.name", "t")
        (self.repo / "pkg.txt").write_text("package v1\n")
        self.git("add", "pkg.txt"); self.git("commit", "-q", "-m", "package")
        self.pkg_commit = self.head()
        self.pkg = {"criteria_sha256": "a", "identity_sha256": "b", "plan_sha256": "c", "manifest_sha256": "d",
                    "budget_sha256": "e"}
        self.path = Path(self.tmp.name) / "ROW20_GO.json"

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *a):
        subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True)

    def head(self):
        return subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip()

    def review(self, att: dict | None, extra: str = "") -> dict:
        body = "# review\n\nVerdict: favourable.\n" + extra
        if att is not None:
            body += f"\n{G.ATTEST_OPEN}\n{json.dumps(att)}\n{G.ATTEST_CLOSE}\n"
        (self.repo / "rev.md").write_text(body)
        self.git("add", "rev.md"); self.git("commit", "-q", "--allow-empty", "-m", "review")
        return {"commit": self.head(), "path": "rev.md", "record_sha256": G.sha_bytes(body.encode())}

    def att(self, **kw):
        a = {"row": "20", "stage": "A", "verdict": "favourable", "reviewer": "codex", "date": "2026-10-02",
             "reviewed_commit": self.pkg_commit, "package": dict(self.pkg)}
        a.update(kw)
        return a

    def go(self, review, package=None, date="2099-01-01"):
        self.path.write_text(json.dumps({"review": review, "owner_go": {"by": "owner", "date": date, "words": "go"},
                                         "package": package or dict(self.pkg)}))

    def check(self, **kw):
        return G.require_go(self.path, self.pkg, repo=self.repo, **kw)

    def test_good(self):
        self.go(self.review(self.att()))
        self.check(verify_at_commit=lambda c: dict(self.pkg))

    def test_refusals(self):
        cases = {
            "no attestation": (self.att, None),
            "unrelated package attested": (lambda: self.att(package={**self.pkg, "plan_sha256": "zz"}), "att"),
            "wrong row": (lambda: self.att(row="21"), "att"),
            "not favourable": (lambda: self.att(verdict="not on board"), "att"),
            "extra field": (lambda: {**self.att(), "x": 1}, "att"),
        }
        for name, (mk, kind) in cases.items():
            with self.subTest(name):
                self.go(self.review(mk() if kind else None))
                with self.assertRaises(SystemExit):
                    self.check()
        with self.subTest("two blocks"):
            a = self.att()
            self.go(self.review(a, extra=f"\n{G.ATTEST_OPEN}\n{json.dumps(a)}\n{G.ATTEST_CLOSE}\n"))
            with self.assertRaises(SystemExit):
                self.check()
        with self.subTest("go package differs"):
            self.go(self.review(self.att()), package={**self.pkg, "identity_sha256": "x"})
            with self.assertRaises(SystemExit):
                self.check()
        with self.subTest("package changed since review"):
            self.go(self.review(self.att()))
            with self.assertRaises(SystemExit):
                G.require_go(self.path, {**self.pkg, "criteria_sha256": "new"}, repo=self.repo)
        with self.subTest("package at reviewed commit differs"):
            self.go(self.review(self.att()))
            with self.assertRaises(SystemExit):
                self.check(verify_at_commit=lambda c: {**self.pkg, "plan_sha256": "old"})
        with self.subTest("owner go before review"):
            self.go(self.review(self.att()), date="2000-01-01")
            with self.assertRaises(SystemExit):
                self.check()
        with self.subTest("record hash mismatch"):
            rv = self.review(self.att()); rv["record_sha256"] = "0" * 64
            self.go(rv)
            with self.assertRaises(SystemExit):
                self.check()


if __name__ == "__main__":
    unittest.main()
