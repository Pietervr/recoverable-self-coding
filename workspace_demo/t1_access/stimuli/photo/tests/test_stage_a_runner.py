"""Stage A revision 4: runner, validator, recovery, attestation and identity tests on a fake instrument - no model
is imported, loaded or run. Controller mechanism fixtures are in test_controller.py.

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import shutil
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
GATES = {"passed": True, "session": "test", "identity": "f" * 64, "package": {"criteria_sha256": "a" * 64}}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def state(out: Path) -> dict:
    return json.loads((out / "stage_a_state.json").read_text())


def full_run(out: Path) -> None:
    stage_a.run_instrumented(F.make_ctx(out))
    stage_a.run_native(F.make_ctx(out))


def gates_env(on: bool = True):
    if on:
        os.environ["STAGE_A_GATES"] = json.dumps(GATES)
    else:
        os.environ.pop("STAGE_A_GATES", None)


class StageA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "photo_stage_a"
        gates_env(False)
        enforce.STORAGE.update(roots=None)

    def tearDown(self):
        self.tmp.cleanup()
        gates_env(False)
        enforce.STORAGE.update(roots=None)

    def test_full_pass_validator(self):
        full_run(self.out)
        c = state(self.out)["counters"]["row20"]
        self.assertEqual((c["started"], c["completed"], c["failed"], c["passes"]), (194, 193, 1, 194))
        gates_env()
        r = stage_a.run_report(F.make_ctx(self.out))
        rep = json.loads((self.out / "report/stage_a_report.json").read_text())
        self.assertTrue(r["validator_pass"], rep["validator"]["failures"][:3])
        self.assertEqual((rep["unique_planned_ids"], rep["actual_tries"]), (178, 178))
        self.assertFalse(rep["stage_b_admission"]["admitted"])               # a report never admits B
        rc = json.loads((self.out / "report/REPORT_RECEIPT.json").read_text())
        for rel, h in rc["outputs"].items():                                 # the receipt binds every output
            self.assertEqual(sha((self.out / rel).read_bytes()), h)
        self.assertEqual(rc["session"], "test")

    def test_diagnostic_report_confers_nothing(self):
        full_run(self.out)
        r = stage_a.run_report(F.make_ctx(self.out))                         # no gates record for this session
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
        gates_env()
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
        with self.assertRaises(stage_a.Hold) as e:                           # a hold, not an integrity failure
            stage_a.run_instrumented(F.make_ctx(self.out))
        self.assertIn("interrupted tries without a recovery file", str(e.exception))
        self.assertFalse((self.out / "TERMINAL.json").exists())
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

    def test_gates_reconcile_then_hold(self):
        """Restart before interruption reconciliation: the GATES worker converts the open attempt durably, then
        holds for authority (exit 4, GATES.json hold) - no TERMINAL record."""
        p = subprocess.run([PY, str(HERE / "fake_stage_a.py"), str(self.out), json.dumps({"exit_at_call": 5,
                            "session": "s1"})], capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, 9)
        self.assertIsNotNone(state(self.out)["open_attempt"])
        rc = stage_a.run_gates(F.make_ctx(self.out))
        self.assertEqual(rc, 4)
        g = json.loads((self.out / "GATES.json").read_text())
        self.assertTrue(g["hold"] and not g["passed"])
        st = state(self.out)
        self.assertIsNone(st["open_attempt"])
        self.assertEqual(len(st["interrupted"]), 1)
        self.assertFalse((self.out / "TERMINAL.json").exists())

    def test_stopped_report_with_unauthorised_interrupted_attempt(self):
        """A resource-killed open attempt: the report describes it and grants or consumes nothing."""
        p = subprocess.run([PY, str(HERE / "fake_stage_a.py"), str(self.out), json.dumps({"exit_at_call": 7,
                            "session": "s1"})], capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, 9)
        G.set_terminal(self.out, "controller", "fixture: resource stop")
        before = (self.out / "stage_a_state.json").read_bytes()
        gates_env()
        r = stage_a.run_report(F.make_ctx(self.out))
        self.assertFalse(r["validator_pass"])
        self.assertEqual((self.out / "stage_a_state.json").read_bytes(), before)    # nothing converted or consumed
        rep = json.loads((self.out / "report/stage_a_report.json").read_text())
        self.assertIsNotNone(rep["unreconciled_open_attempt"])
        self.assertTrue((self.out / "report/REPORT_RECEIPT.json").exists())

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
    """Committed outputs tampered CONSISTENTLY (hashes in the ledger updated) so each check is reached on its own."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name) / "base"
        full_run(cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def copy(self) -> Path:
        d = Path(tempfile.mkdtemp()) / "o"
        shutil.copytree(self.base, d)
        return d

    def codes(self, out: Path) -> set:
        st = json.loads((out / "stage_a_state.json").read_text())
        return {f["code"] for f in R.validate(out, PLAN, st, identity="f" * 64)["failures"]}

    def rewrite(self, out: Path, aid: str, record=None, array=None):
        st = json.loads((out / "stage_a_state.json").read_text())
        outs = st["completed"][aid]["outputs"]
        npy = f"passes/{aid}.residuals.npy"
        if array is not None:
            np.save(out / npy, array, allow_pickle=False)
            outs[npy] = sha((out / npy).read_bytes())
        if record is not None or array is not None:
            r = record if record is not None else self.rec(out, aid)
            r["arrays"] = {npy: outs[npy]}
            (out / f"passes/{aid}.json").write_text(json.dumps(r))
            outs[f"passes/{aid}.json"] = sha((out / f"passes/{aid}.json").read_bytes())
        (out / "stage_a_state.json").write_text(json.dumps(st))
        for name in ("INSTRUMENTED_DONE.json", "NATIVE_DONE.json"):        # phase records follow the ledger
            d = json.loads((out / name).read_text())
            if aid in d["attempts"]:
                d["attempts"][aid] = outs
                (out / name).write_text(json.dumps(d))
        return st

    def rec(self, out, aid):
        return json.loads((out / f"passes/{aid}.json").read_text())

    def mutate(self, aid: str, fn) -> set:
        out = self.copy()
        r = self.rec(out, aid)
        fn(r)
        self.rewrite(out, aid, record=r)
        return self.codes(out)

    def test_clean_base_passes(self):
        self.assertEqual(self.codes(self.copy()), set())

    def test_hash_tamper(self):
        out = self.copy()
        p = out / "passes/03-native.residuals.npy"
        b = bytearray(p.read_bytes()); b[-1] ^= 1; p.write_bytes(bytes(b))
        self.assertIn("OUTPUT_HASH", self.codes(out))

    def test_record_identity_fields(self):
        self.assertIn("RECORD_ID", self.mutate("02-empty", lambda r: r.update(case="plain")))
        self.assertIn("RECORD_ID", self.mutate("02-empty", lambda r: r.update(kind="diagnostic_mechanics")))

    def test_schema_extra_and_missing_keys(self):
        self.assertIn("RECORD_SCHEMA", self.mutate("04-plain", lambda r: r.update(extra=1)))
        self.assertIn("RECORD_SCHEMA", self.mutate("04-plain", lambda r: r.pop("input_ids_sha256")))
        self.assertIn("RECORD_SCHEMA", self.mutate("04-native", lambda r: r.pop("decoder_calls")))
        self.assertIn("IMAGE_SCHEMA", self.mutate("04-plain", lambda r: r["image"].pop("rope_calls")))

    def test_plain_input_ids_and_token_count(self):
        self.assertIn("INPUT_IDS", self.mutate("05-plain", lambda r: r.update(input_ids_sha256="0" * 64)))
        self.assertIn("TOKEN_COUNT", self.mutate("05-plain", lambda r: r.update(n_tokens=r["n_tokens"] + 1)))

    def test_capture_and_dispatch_metadata(self):
        self.assertIn("READOUT", self.mutate("05-plain", lambda r: r.update(readout_positions=[1, 2, 3])))
        self.assertIn("CAPTURE_LAYERS", self.mutate("05-plain", lambda r: r.update(capture_layers=[0])))
        self.assertIn("TOP_K", self.mutate("05-plain", lambda r: r.update(top_ids=[0], top_logits=[0.0])))
        self.assertIn("LOGITS_META", self.mutate("05-plain", lambda r: r["final_logits"].update(sha256="0" * 64)))
        self.assertIn("RESIDUAL_META", self.mutate("05-plain", lambda r: r["residuals_meta"].update(dtype="float16")))
        self.assertIn("EDITS", self.mutate("05-zero_swap", lambda r: r["edit_log"][0].update(mode="steer")))
        self.assertIn("EDITS", self.mutate("05-zero_swap", lambda r: r["edit_log"][0].update(alpha=1.0)))
        self.assertIn("EDITS", self.mutate("05-plain", lambda r: r.update(edits_installed=True)))

    def test_image_rotary_merge_and_features(self):
        self.assertIn("ROTARY", self.mutate("06-plain", lambda r: r["image"].update(rope_calls=[[0, 5]] * 32)))
        self.assertIn("MERGE", self.mutate("06-plain", lambda r: r["image"]["merge"].update(n_image_rows=143)))
        self.assertIn("TOKENS", self.mutate("06-plain", lambda r: r["image"].update(features_shape=[144, 8])))
        self.assertIn("FEATURE_DTYPE", self.mutate("06-plain", lambda r: r["image"].update(features_dtype="x")))
        c = self.mutate("06-repeat", lambda r: r["image"]["merge"].update(merged_sha256="1" * 64))
        self.assertIn("MERGE_ACROSS_CASES", c)

    def test_boundary_bytes_decoded(self):
        def nan_boundary(r):
            b = np.frombuffer(base64.b64decode(r["image"]["boundary_mean_fp32_b64"]), dtype=np.float32).copy()
            b[0] = np.nan
            r["image"]["boundary_mean_fp32_b64"] = base64.b64encode(b.tobytes()).decode()
            r["image"]["boundary_mean_sha256"] = sha(b.tobytes())               # consistent hash, flag still true
        self.assertIn("BOUNDARY_FINITE", self.mutate("07-plain", nan_boundary))
        self.assertIn("BOUNDARY_HASH", self.mutate("07-plain", lambda r: r["image"].update(
            boundary_mean_sha256="0" * 64)))
        self.assertIn("BOUNDARY_BYTES", self.mutate("07-plain", lambda r: r["image"].update(
            boundary_mean_fp32_b64=base64.b64encode(b"\0" * 8).decode())))

    def test_native_embedding_digest_from_archive(self):
        c = self.mutate("08-native", lambda r: r.update(inputs_embeds_sha256="2" * 64))   # boolean left true
        self.assertIn("EMBEDDINGS", c)
        self.assertIn("EMBEDDINGS_FLAG", c)
        self.assertIn("EMBEDDINGS_FLAG", self.mutate("08-native", lambda r: r.update(
            inputs_embeds_equal_instrumented_merge=False)))
        self.assertIn("DECODER_CALLS", self.mutate("08-native", lambda r: r.update(
            decoder_calls={"min": 1, "max": 2, "layers": 64})))

    def test_nonfinite_native(self):
        out = self.copy()
        a = np.load(out / "passes/04-native.residuals.npy"); a[0, 0, 0] = np.nan
        r = self.rec(out, "04-native"); r["residuals_sha256"] = sha(np.ascontiguousarray(a).tobytes())
        self.rewrite(out, "04-native", record=r, array=a)
        self.assertIn("NONFINITE", self.codes(out))

    def test_parity_summary_unbound(self):
        out = self.copy()
        rows = json.loads((out / "native_parity.json").read_text())
        (out / "native_parity.json").write_text(json.dumps([rows[0]] * 20))   # twenty duplicate passing rows
        self.assertIn("PARITY_SUMMARY_MISMATCH", self.codes(out))

    def test_failing_numbers_marked_pass(self):
        self.assertIn("PARITY", self.mutate("06-native", lambda r: r.update(
            requested_logits=[v + 1.0 for v in r["requested_logits"]])))

    def test_phase_record_mismatch_and_identity(self):
        out = self.copy()
        d = json.loads((out / "NATIVE_DONE.json").read_text()); d["attempts"].pop("00-native")
        (out / "NATIVE_DONE.json").write_text(json.dumps(d))
        self.assertIn("PHASE_RECORD_MISMATCH", self.codes(out))
        out = self.copy()
        d = json.loads((out / "INSTRUMENTED_DONE.json").read_text()); d["identity"] = "e" * 64
        (out / "INSTRUMENTED_DONE.json").write_text(json.dumps(d))
        self.assertIn("PHASE_RECORD_IDENTITY", self.codes(out))

    def test_suffix_leak_and_encoder_insensitive(self):
        out = self.copy()
        r = self.rec(out, "01-suffix_isolation"); r["residuals_sha256"] = "0" * 64
        self.rewrite(out, "01-suffix_isolation", record=r)
        r6 = self.rec(out, "06-plain"); r1 = self.rec(out, "01-plain")
        r6["image"]["features_sha256"] = r1["image"]["features_sha256"]
        self.rewrite(out, "06-plain", record=r6)
        c = self.codes(out)
        self.assertTrue({"SUFFIX_ISOLATION", "ENCODER_SENSITIVITY"} <= c, c)

    def test_ledger_consistency(self):
        out = self.copy()
        st = json.loads((out / "stage_a_state.json").read_text())
        st["counters"]["row20"]["completed"] -= 1
        (out / "stage_a_state.json").write_text(json.dumps(st))
        self.assertIn("LEDGER_COUNTERS", self.codes(out))
        out = self.copy()
        st = json.loads((out / "stage_a_state.json").read_text())
        st["completed"]["99-extra"] = st["completed"]["00-plain"]
        (out / "stage_a_state.json").write_text(json.dumps(st))
        self.assertIn("LEDGER_UNKNOWN_ID", self.codes(out))
        out = self.copy()
        st = json.loads((out / "stage_a_state.json").read_text())
        st["identities"]["row20"] = "e" * 64
        (out / "stage_a_state.json").write_text(json.dumps(st))
        self.assertIn("LEDGER_IDENTITY", self.codes(out))
        out = self.copy()
        st = json.loads((out / "stage_a_state.json").read_text())
        st["caps"]["row20"]["attempts"] = 400
        (out / "stage_a_state.json").write_text(json.dumps(st))
        self.assertIn("LEDGER_CAPS", self.codes(out))

    def test_output_membership(self):
        out = self.copy()
        (out / "passes" / "stray.npy").write_bytes(b"x")
        self.assertIn("OUTPUT_MEMBERSHIP", self.codes(out))


class Units(unittest.TestCase):
    def tearDown(self):
        enforce.STORAGE.update(roots=None)

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

    def test_every_writer_reserves(self):
        """Work writes stop at the operational limit; finalisation writes may use the reserve but not pass the cap."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "x").write_bytes(b"0" * 4000)
            enforce.configure_storage([root], cap=10000, operational=6000)
            with self.assertRaises(enforce.StorageStop):
                enforce.write_atomic(root / "work.bin", b"0" * 1000)                 # 4000 + 3000 > 6000
            enforce.write_json_atomic(root / "state.json", {"a": "0" * 500}, final=True)   # into the reserve
            with self.assertRaises(enforce.StorageStop):
                enforce.write_atomic(root / "final.bin", b"0" * 3000, final=True)    # past the cap
            with self.assertRaises(enforce.StorageStop):
                G.set_terminal(root, "x", "y" * 4000)                                 # the terminal writer too
            enforce.write_atomic(Path(tempfile.mkdtemp()) / "elsewhere", b"0" * 99999)  # outside the task: free

    def test_identity_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            enforce.Budget(Path(d) / "s.json", "row20", "one", [Path(d)], "t")
            with self.assertRaises(enforce.StopRun):
                enforce.Budget(Path(d) / "s.json", "row20", "two", [Path(d)], "t")

    def test_consumed_map_bound_and_origins(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "pkgroot" / "watchedpkg"
            root.mkdir(parents=True)
            (root / "__init__.py").write_text("X = 1\n")
            maps = Path(d) / "maps.json"
            maps.write_text(json.dumps({"watchedpkg": {"root": str(root), "files": {"__init__.py": G.sha_file(
                root / "__init__.py")}}}))
            good = G.sha_file(maps)
            other = Path(d) / "elsewhere" / "watchedpkg"
            other.mkdir(parents=True)
            (other / "__init__.py").write_text("X = 2\n")
            for where, expect_ok in ((root, True), (other, False)):
                sys.modules.pop("watchedpkg", None)
                mod = types.ModuleType("watchedpkg"); mod.__file__ = str(where / "__init__.py")
                sys.modules["watchedpkg"] = mod
                if expect_ok:
                    G.check_imported_origins(maps, good)
                else:
                    with self.assertRaises(SystemExit):
                        G.check_imported_origins(maps, good)
            mod.__file__ = str(root / "__init__.py")
            m = json.loads(maps.read_text())                                  # a consumed map rewritten to admit
            m["watchedpkg"]["root"] = str(other)                              # the shadowing copy
            m["watchedpkg"]["files"]["__init__.py"] = G.sha_file(other / "__init__.py")
            maps.write_text(json.dumps(m))
            mod.__file__ = str(other / "__init__.py")
            with self.assertRaises(SystemExit) as cm:
                G.check_imported_origins(maps, good)
            self.assertIn("not the admitted map", str(cm.exception))
            (root / "__init__.py").write_text("X = 3\n")                    # a changed file at the right origin
            maps.write_text(json.dumps({"watchedpkg": {"root": str(root), "files": {"__init__.py": "0" * 64}}}))
            mod.__file__ = str(root / "__init__.py")
            with self.assertRaises(SystemExit):
                G.check_imported_origins(maps, G.sha_file(maps))
            sys.modules.pop("watchedpkg", None)

    def test_positions_receipt_absent_failing_stale(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            plan = d / "plan.json"
            plan.write_text("{}")
            ctx = stage_a.Ctx(plan_path=plan, receipt_path=d / "r.json")
            with self.assertRaisesRegex(SystemExit, "absent"):
                stage_a.check_receipt(ctx)
            (d / "r.json").write_text(json.dumps({"all_equal": False, "plan_sha256": G.sha_file(plan)}))
            with self.assertRaisesRegex(SystemExit, "does not show"):
                stage_a.check_receipt(ctx)
            (d / "r.json").write_text(json.dumps({"all_equal": True, "plan_sha256": "0" * 64}))
            with self.assertRaisesRegex(SystemExit, "stale"):
                stage_a.check_receipt(ctx)
            (d / "r.json").write_text(json.dumps({"all_equal": True, "plan_sha256": G.sha_file(plan)}))
            stage_a.check_receipt(ctx)

    def test_code_changed_between_phases(self):
        ident = json.loads(stage_a.IDENTITY.read_text())
        ctx = stage_a.Ctx()
        now = {**ident, "local_code_sha256": {n: G.sha_file(stage_a.HERE / n) for n in G.LOCAL_CODE},
               "packet_py_sha256": G.sha_file(stage_a.T1 / "stimuli" / "packet.py"),
               "plan_sha256": G.sha_file(ctx.plan_path), "manifest_sha256": G.sha_file(ctx.manifest_path),
               "positions_receipt_sha256": G.sha_file(ctx.receipt_path)}
        stage_a.recheck_identity(ctx, now)                                    # unchanged: passes
        for k in ("stage_a_report.py", "enforce.py"):
            bad = copy.deepcopy(now)
            bad["local_code_sha256"][k] = "0" * 64                            # as if the file changed since
            with self.assertRaises(stage_a.StopCheck):
                stage_a.recheck_identity(ctx, bad)
        with self.assertRaises(stage_a.StopCheck):
            stage_a.recheck_identity(ctx, {**now, "positions_receipt_sha256": "0" * 64})

    def test_worker_identity_must_equal_frozen_and_gates(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "o"
            ctx = F.make_ctx(out)
            ctx.compute_identity = lambda: {"identity_sha256": "e" * 64}
            with self.assertRaisesRegex(SystemExit, "differs from the frozen"):
                stage_a.worker_identity(ctx, "instrumented")
            ctx = F.make_ctx(out)
            ctx.verify_controller = True
            os.environ["STAGE_A_GATES"] = json.dumps({**GATES, "identity": "e" * 64})
            try:
                with self.assertRaisesRegex(SystemExit, "gates admitted"):
                    stage_a.worker_identity(ctx, "report")
            finally:
                gates_env(False)

    def test_interpretation_status(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / "report").mkdir()
            self.assertEqual(R.interpretation_status(out)["problems"], ["absent"])
            for f in ("rel_l2_by_layer.svg", "logit_max_abs.svg"):
                (out / "report" / f).write_text(f"<svg>{f}</svg>")
            h = {f: G.sha_file(out / "report" / f) for f in ("rel_l2_by_layer.svg", "logit_max_abs.svg")}
            good = "Author: A. Author\nDate: 2026-10-03\n" + "".join(f"{f} sha256: {v}\n" for f, v in h.items())
            (out / "report" / "INTERPRETATION.md").write_text(good)
            self.assertTrue(R.interpretation_status(out)["valid"])
            (out / "report" / "INTERPRETATION.md").write_text(good.replace("Author: A. Author\n", ""))
            self.assertIn("no author", R.interpretation_status(out)["problems"])
            (out / "report" / "INTERPRETATION.md").write_text(good.replace(h["logit_max_abs.svg"], "0" * 64))
            self.assertFalse(R.interpretation_status(out)["valid"])


HEX = {k: c * 64 for k, c in (("criteria_sha256", "a"), ("identity_sha256", "b"), ("plan_sha256", "c"),
                               ("manifest_sha256", "d"), ("budget_sha256", "e"))}


class GoAttestation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q"); self.git("config", "user.email", "t@t"); self.git("config", "user.name", "t")
        (self.repo / "pkg.txt").write_text("package v1\n")
        self.git("add", "pkg.txt"); self.git("commit", "-q", "-m", "package")
        self.pkg_commit = self.head()
        self.pkg = dict(HEX)
        self.path = Path(self.tmp.name) / "ROW20_GO.json"
        self.today = self.out("show", "-s", "--format=%cs", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *a):
        subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True)

    def out(self, *a):
        return subprocess.run(["git", "-C", str(self.repo), *a], capture_output=True, text=True).stdout.strip()

    def head(self):
        return self.out("rev-parse", "HEAD")

    def review(self, att, extra: str = "", raw: str | None = None) -> dict:
        body = "# review\n\nVerdict: favourable.\n" + extra
        if raw is not None:
            body += raw
        elif att is not None:
            body += f"\n{G.ATTEST_OPEN}\n{json.dumps(att)}\n{G.ATTEST_CLOSE}\n"
        (self.repo / "rev.md").write_text(body)
        self.git("add", "rev.md"); self.git("commit", "-q", "--allow-empty", "-m", "review")
        return {"commit": self.head(), "path": "rev.md", "record_sha256": G.sha_bytes(body.encode())}

    def att(self, **kw):
        a = {"row": "20", "stage": "A", "verdict": "favourable", "reviewer": "codex", "date": self.today,
             "reviewed_commit": self.pkg_commit, "package": dict(self.pkg)}
        a.update(kw)
        return a

    def go(self, review, package=None, date="2099-01-01", **og):
        self.path.write_text(json.dumps({"review": review, "owner_go": {"by": "owner", "date": date, "words": "go",
                                                                        **og},
                                         "package": package or dict(self.pkg)}))

    def check(self, at=None, pkg=None):
        return G.require_go(self.path, pkg or self.pkg, repo=self.repo,
                            verify_at_commit=at or (lambda c: dict(self.pkg)))

    def refused(self, msg=None, **kw):
        with self.assertRaises(SystemExit) as cm:
            self.check(**kw)
        if msg:
            self.assertIn(msg, str(cm.exception))

    def test_good(self):
        self.go(self.review(self.att()))
        self.assertEqual(self.check()["attestation"]["row"], "20")

    def test_reviewed_commit_rederivation_is_mandatory(self):
        self.go(self.review(self.att()))
        with self.assertRaises(SystemExit):
            G.require_go(self.path, self.pkg, repo=self.repo, verify_at_commit=None)

    def test_attestation_refusals(self):
        cases = {
            "unrelated package attested": self.att(package={**self.pkg, "plan_sha256": "f" * 64}),
            "wrong row": self.att(row="21"),
            "not favourable": self.att(verdict="not on board"),
            "extra field": {**self.att(), "x": 1},
            "extra null package key": self.att(package={**self.pkg, "extra_sha256": None}),
            "short digest": self.att(package={**self.pkg, "plan_sha256": "c" * 63}),
            "uppercase digest": self.att(package={**self.pkg, "plan_sha256": "C" * 64}),
            "truthy non-string reviewer": self.att(reviewer=1),
            "boolean reviewer": self.att(reviewer=True),
            "empty reviewer": self.att(reviewer="  "),
            "date with time": self.att(date=self.today + "T23:59"),
            "impossible date": self.att(date="2026-02-30"),
            "short reviewed commit": self.att(reviewed_commit=self.pkg_commit[:7]),
            "non-hex reviewed commit": self.att(reviewed_commit="g" * 40),
            "unknown reviewed commit": self.att(reviewed_commit="1" * 40),
            "row as integer": self.att(row=20),
        }
        for name, a in cases.items():
            with self.subTest(name):
                self.go(self.review(a))
                self.refused()

    def test_extra_null_key_in_both_attestation_and_go(self):
        p2 = {**self.pkg, "extra_sha256": None}
        self.go(self.review(self.att(package=p2)), package=p2)
        self.refused("fields")

    def test_reviewed_commit_must_be_a_commit_object(self):
        tree = self.out("rev-parse", "HEAD^{tree}")
        self.go(self.review(self.att(reviewed_commit=tree)))
        self.refused("not a commit object")

    def test_block_structure(self):
        a = json.dumps(self.att())
        for name, raw in (("no closing delimiter", f"\n{G.ATTEST_OPEN}\n{a}\n"),
                          ("closing delimiter not on its own line", f"\n{G.ATTEST_OPEN}\n{a} -->\n"),
                          ("marker not at line start", f"\nsee {G.ATTEST_OPEN}\n{a}\n{G.ATTEST_CLOSE}\n"),
                          ("text after the closing delimiter", f"\n{G.ATTEST_OPEN}\n{a}\n{G.ATTEST_CLOSE} x\n"),
                          ("duplicate key", f"\n{G.ATTEST_OPEN}\n" + a[:-1] + ', "row": "20"}' +
                           f"\n{G.ATTEST_CLOSE}\n")):
            with self.subTest(name):
                self.go(self.review(None, raw=raw))
                self.refused()
        with self.subTest("two blocks"):
            self.go(self.review(self.att(), extra=f"\n{G.ATTEST_OPEN}\n{a}\n{G.ATTEST_CLOSE}\n"))
            self.refused("blocks")
        with self.subTest("no block"):
            self.go(self.review(None))
            self.refused("0 attestation blocks")

    def test_go_file_refusals(self):
        rv = self.review(self.att())
        for name, mk in (("go package differs", lambda: self.go(rv, package={**self.pkg, "identity_sha256": "1" * 64})),
                         ("owner go before review", lambda: self.go(rv, date="2000-01-01")),
                         ("owner date truncation", lambda: self.go(rv, date="2099-01-01T00:00")),
                         ("owner by not a string", lambda: self.go(rv, by=1)),
                         ("record hash mismatch", lambda: self.go({**rv, "record_sha256": "0" * 64})),
                         ("short review commit", lambda: self.go({**rv, "commit": rv["commit"][:12]})),
                         ("absolute record path", lambda: self.go({**rv, "path": "/etc/passwd"})),
                         ("extra review key", lambda: self.go({**rv, "x": None}))):
            with self.subTest(name):
                mk()
                self.refused()

    def test_package_changes(self):
        self.go(self.review(self.att()))
        with self.subTest("package changed since review"):
            self.refused(pkg={**self.pkg, "criteria_sha256": "9" * 64})
        with self.subTest("package at reviewed commit differs"):
            self.refused(at=lambda c: {**self.pkg, "plan_sha256": "8" * 64})
        with self.subTest("re-derivation with a null field"):
            self.refused(at=lambda c: {**self.pkg, "plan_sha256": None})

    def test_review_must_descend_from_reviewed_commit(self):
        self.git("checkout", "-q", "--orphan", "side")
        (self.repo / "other.txt").write_text("x")
        self.git("add", "other.txt"); self.git("commit", "-q", "-m", "unrelated root")
        self.go(self.review(self.att()))
        self.refused("does not descend")

    def test_negative_record_supplement(self):
        self.go(self.review(self.att()))
        d = json.loads(self.path.read_text())
        old = G.NEGATIVE_REVIEWS
        G.NEGATIVE_REVIEWS = old | {d["review"]["commit"][:7]}
        try:
            self.refused("negative record")
        finally:
            G.NEGATIVE_REVIEWS = old


class ReviewedPackageBuilder(unittest.TestCase):
    """stage_a.package_at_commit on a real git repository laid out like RSC (not a callback)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "rsc"
        self.photo = "workspace_demo/t1_access/stimuli/photo"
        pd = self.repo / self.photo
        pd.mkdir(parents=True)
        (self.repo / "workspace_demo/t1_access/stimuli/packet.py").write_text("# packet\n")
        for n in ("STAGE_A_CRITERIA.md", "stage_a_plan.json", "manifest_dev.json", "stage_a_positions_receipt.json",
                  "stage_a_identity_files.json") + tuple(G.LOCAL_CODE):
            shutil.copyfile(stage_a.HERE / n, pd / n)
        self.write_identity()
        self.git("init", "-q"); self.git("config", "user.email", "t@t"); self.git("config", "user.name", "t")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True, text=True).stdout

    def write_identity(self, **over):
        pd = self.repo / self.photo
        ident = {"local_code_sha256": {n: G.sha_file(pd / n) for n in G.LOCAL_CODE},
                 "packet_py_sha256": G.sha_file(self.repo / "workspace_demo/t1_access/stimuli/packet.py"),
                 "package_file_maps_sha256": G.sha_file(pd / "stage_a_identity_files.json"),
                 "plan_sha256": G.sha_file(pd / "stage_a_plan.json"),
                 "manifest_sha256": G.sha_file(pd / "manifest_dev.json"),
                 "positions_receipt_sha256": G.sha_file(pd / "stage_a_positions_receipt.json"), "row": "20"}
        ident.update(over)
        ident["identity_sha256"] = G.sha_bytes(json.dumps(ident, sort_keys=True).encode())
        (pd / "stage_a_identity.json").write_text(json.dumps(ident, indent=1, sort_keys=True) + "\n")

    def commit(self) -> str:
        self.git("add", "-A"); self.git("commit", "-q", "-m", "package")
        return self.git("rev-parse", "HEAD").strip()

    def build(self, c):
        return stage_a.package_at_commit(c, repo=self.repo, photo=self.photo)

    def test_positive(self):
        c = self.commit()
        p = self.build(c)
        self.assertEqual(p["plan_sha256"], G.sha_file(self.repo / self.photo / "stage_a_plan.json"))

    def test_identity_not_describing_its_blobs_refused(self):
        for k, v in (("package_file_maps_sha256", "0" * 64), ("positions_receipt_sha256", "1" * 64),
                     ("packet_py_sha256", "2" * 64), ("plan_sha256", "3" * 64)):
            with self.subTest(k):
                self.write_identity(**{k: v})
                with self.assertRaises(SystemExit):
                    self.build(self.commit())

    def test_local_code_mismatch_refused(self):
        pd = self.repo / self.photo
        self.write_identity()
        (pd / "enforce.py").write_text("# changed after the identity was taken\n")
        with self.assertRaisesRegex(SystemExit, "local_code_sha256"):
            self.build(self.commit())

    def test_identity_self_hash_refused(self):
        pd = self.repo / self.photo
        d = json.loads((pd / "stage_a_identity.json").read_text())
        d["row"] = "21"                                                         # hash no longer matches its body
        (pd / "stage_a_identity.json").write_text(json.dumps(d))
        with self.assertRaisesRegex(SystemExit, "own identity_sha256"):
            self.build(self.commit())


if __name__ == "__main__":
    unittest.main()
