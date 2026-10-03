"""Stage A revision 7: runner, validator, recovery, attestation and identity tests on a fake instrument - no model
is imported, loaded or run. Controller mechanism fixtures are in test_controller.py. Revision 5 adds Codex RSC
1bf9890's A1 call-site fixtures (gates and report consume their own map and recheck before committing), the A6 ledger
counterexample and coherent zero/negative states, full instrumented admission before any native work (a CONSISTENT
non-plain input_ids change), resumed-record admission, rank/top-k/logit-dtype predicates and the A8 source pins.

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
        self.assertEqual(enforce.check_ledger(st), [])                 # an honest, authorised history is legal

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

    def test_consistent_nonplain_change_refused_before_native(self):
        """A6: a non-plain record's input_ids_sha256 changed with every hash (record, ledger, phase record) updated
        consistently - the full instrumented validator refuses BEFORE the native model is even constructed."""
        stage_a.run_instrumented(F.make_ctx(self.out))
        aid = "05-zero_steer"
        st = state(self.out)
        r = json.loads((self.out / f"passes/{aid}.json").read_text())
        r["input_ids_sha256"] = "0" * 64
        (self.out / f"passes/{aid}.json").write_text(json.dumps(r))
        st["completed"][aid]["outputs"][f"passes/{aid}.json"] = sha((self.out / f"passes/{aid}.json").read_bytes())
        (self.out / "stage_a_state.json").write_text(json.dumps(st))
        d = json.loads((self.out / "INSTRUMENTED_DONE.json").read_text())
        d["attempts"][aid] = st["completed"][aid]["outputs"]
        (self.out / "INSTRUMENTED_DONE.json").write_text(json.dumps(d))
        ctx = F.make_ctx(self.out)
        built = []
        nf = ctx.native_factory
        ctx.native_factory = lambda: built.append(1) or nf()
        with self.assertRaisesRegex(stage_a.StopCheck, "pre-native admission failed.*INPUT_IDS"):
            stage_a.run_native(ctx)
        self.assertEqual(built, [])                                          # no native model, no forward

    def test_resumed_record_admitted_by_the_full_predicates(self):
        """A6: a committed record reloaded on resumption passes the instrumented predicates before use."""
        p = subprocess.run([PY, str(HERE / "fake_stage_a.py"), str(self.out), json.dumps({"exit_at_call": 30,
                            "session": "s1"})], capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, 9, p.stderr[-1500:])
        st = state(self.out)
        crashed = st["open_attempt"]["id"]
        aid = "02-plain"
        r = json.loads((self.out / f"passes/{aid}.json").read_text())
        r["requested"][0]["rank"] = True                                     # a bool rank, hashes kept consistent
        (self.out / f"passes/{aid}.json").write_text(json.dumps(r))
        st["completed"][aid]["outputs"][f"passes/{aid}.json"] = sha((self.out / f"passes/{aid}.json").read_bytes())
        (self.out / "stage_a_state.json").write_text(json.dumps(st))
        (self.out / f"RECOVERY_{crashed}__s1__1.json").write_text(json.dumps(
            {"attempt_id": crashed, "session": "s1", "try": 1, "owner": "test", "date": "2026-10-02",
             "reason": "test crash"}))
        with self.assertRaisesRegex(stage_a.StopCheck, "resumed record fails admission.*RANKS"):
            stage_a.run_instrumented(F.make_ctx(self.out))

    def test_gates_consume_their_map_and_recheck(self):
        """A1: the gates check their own bound map and recheck the identity before GATES.json is committed."""
        os.environ.pop("STAGE_A_SESSION", None)
        ctx = F.make_ctx(self.out)
        calls = []
        ctx.origins_check = lambda: calls.append("origins") or (_ for _ in ()).throw(SystemExit("refused: origins"))
        with self.assertRaisesRegex(SystemExit, "origins"):
            stage_a.run_gates(ctx)
        self.assertEqual(calls, ["origins"])
        self.assertFalse((self.out / "GATES.json").exists())
        real = stage_a.recheck_identity
        stage_a.recheck_identity = lambda c, i: (_ for _ in ()).throw(stage_a.StopCheck("identity changed (fixture)"))
        try:
            with self.assertRaisesRegex(stage_a.StopCheck, "identity changed"):
                stage_a.run_gates(F.make_ctx(self.out))
        finally:
            stage_a.recheck_identity = real
        self.assertFalse((self.out / "GATES.json").exists())

    def test_report_consumes_its_map_and_rechecks_before_the_receipt(self):
        full_run(self.out)
        gates_env()
        ctx = F.make_ctx(self.out)
        calls = []
        ctx.origins_check = lambda: calls.append("origins")
        real = stage_a.recheck_identity
        stage_a.recheck_identity = lambda c, i: (_ for _ in ()).throw(stage_a.StopCheck("identity changed (fixture)"))
        try:
            with self.assertRaisesRegex(stage_a.StopCheck, "identity changed"):
                stage_a.run_report(ctx)
        finally:
            stage_a.recheck_identity = real
        self.assertEqual(calls, ["origins"])
        self.assertTrue((self.out / "report/stage_a_report.json").exists())
        self.assertFalse((self.out / "report/REPORT_RECEIPT.json").exists())    # no receipt without the recheck
        for f in ("rel_l2_by_layer.svg", "logit_max_abs.svg"):
            self.assertTrue((self.out / "report" / f).exists())

    def test_source_records_pinned(self):
        """A8: admission requires the current dev pool and provenance records identical to the plan's pins."""
        with tempfile.TemporaryDirectory() as d:
            plan = json.loads(stage_a.PLAN.read_text())
            plan["provenance_checks_sha256"] = "0" * 64
            pp = Path(d) / "plan.json"
            pp.write_text(json.dumps(plan))
            with self.assertRaisesRegex(SystemExit, "provenance_checks.json differs"):
                stage_a.load_frozen(stage_a.Ctx(plan_path=pp))

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

    def ledger_codes(self, st: dict) -> set:
        out = self.copy()
        (out / "stage_a_state.json").write_text(json.dumps(st))
        return self.codes(out)

    def test_codex_ledger_counterexample(self):
        """A6, Codex's static counterexample: all tries 0, passes per try 1, row20 started 16, passes 16, completed
        193, failed -177, row 21 zero, aggregate = row 20 - the old equations held; the legal domains refuse it."""
        st = json.loads((self.base / "stage_a_state.json").read_text())
        for a in st["attempts"].values():
            a["tries"], a["passes"] = 0, 1
        st["counters"]["row20"] = {"started": 16, "passes": 16, "completed": 193, "failed": -177}
        st["counters"]["row21"] = {"started": 0, "passes": 0, "completed": 0, "failed": 0}
        st["counters"]["aggregate"] = dict(st["counters"]["row20"])
        self.assertIn("LEDGER_DOMAIN", self.ledger_codes(st))
        self.assertTrue(enforce.check_ledger(st))

    def with_recovery(self, st: dict, out: Path, aid: str = "05-plain", tries: int = 2, **auth_over) -> dict:
        """A legal authorised history for one attempt: tries raised, counters raised, the owner's recovery file retained
        in out and its consumed entry recorded (the authority possibly altered by auth_over)."""
        st = copy.deepcopy(st)
        st["attempts"][aid]["tries"] = tries
        for k in ("row20", "aggregate"):
            for x in ("started", "passes", "failed"):
                st["counters"][k][x] += tries - 1
        st["recoveries_consumed"] = []
        for t in range(1, tries):
            body = {"attempt_id": aid, "session": f"s{t}", "try": t, "owner": "o", "date": "2026-10-02",
                    "reason": "test crash"}
            raw = json.dumps(body).encode()
            (out / f"RECOVERY_{aid}__s{t}__{t}.json").write_bytes(raw)
            auth = {**body, "file_sha256": sha(raw), **auth_over}
            st["recoveries_consumed"].append({"attempt_id": aid, "session": f"s{t}", "try": t, "authority": auth,
                                              "consumed_by": f"s{t + 1}"})
        return st

    def both_admissions(self, out: Path, st: dict) -> tuple:
        (out / "stage_a_state.json").write_text(json.dumps(st))
        fin = {f["code"] for f in R.validate(out, PLAN, st, identity="f" * 64)["failures"]}
        pre = {f["code"] for f in R.validate(out, PLAN, st, identity="f" * 64, phases=("instrumented",))["failures"]}
        return fin, pre

    def test_codex_unauthorised_extra_try(self):
        """Stage A 4 (b569f8a): one completed attempt's tries 1 -> 2 with NO consumed recovery and counters raised by one
        (195 of 200, every counter legal) - refused in final and pre-native admission."""
        out = self.copy()
        st = json.loads((out / "stage_a_state.json").read_text())
        st["attempts"]["05-plain"]["tries"] = 2
        for k in ("row20", "aggregate"):
            for x in ("started", "passes", "failed"):
                st["counters"][k][x] += 1
        self.assertTrue(any("not exactly tries [1]" in p for p in enforce.check_ledger(st)))
        fin, pre = self.both_admissions(out, st)
        self.assertIn("LEDGER_DOMAIN", fin)
        self.assertIn("LEDGER_DOMAIN", pre)

    def test_authority_domains_and_witness(self):
        """Stage A D (c036c00): an authorised history is legal only with the intake's domains AND its retained owner
        file; authority-only mutations (bool / float try, an impossible date, a non-hex digest) and a well-typed
        authority that differs from the witness file are refused - in final and pre-native admission."""
        out = self.copy()
        base = json.loads((out / "stage_a_state.json").read_text())
        good = self.with_recovery(base, out)
        self.assertEqual(enforce.check_ledger(good, witness_dir=out), [])
        fin, pre = self.both_admissions(out, good)
        self.assertNotIn("LEDGER_DOMAIN", fin | pre)
        muts = {"authority try true": {"try": True}, "authority try 1.0": {"try": 1.0},
                "date not a date": {"date": "not-a-date"}, "impossible date": {"date": "2026-02-30"},
                "digest x*64": {"file_sha256": "x" * 64}, "owner differs from the witness": {"owner": "someone"},
                "digest of another file": {"file_sha256": "a" * 64}}
        for name, over in muts.items():
            with self.subTest(name):
                o = self.copy()
                st = self.with_recovery(base, o, **over)
                self.assertTrue(enforce.check_ledger(st, witness_dir=o), name)
                fin, pre = self.both_admissions(o, st)
                self.assertIn("LEDGER_DOMAIN", fin)
                self.assertIn("LEDGER_DOMAIN", pre)
        o = self.copy()                                                  # the witness file removed
        st = self.with_recovery(base, o)
        (o / "RECOVERY_05-plain__s1__1.json").unlink()
        self.assertTrue(any("not retained" in p for p in enforce.check_ledger(st, witness_dir=o)))

    def test_exact_consumed_and_outstanding_sets(self):
        """Stage A D: legal counters and unchanged outputs, but the recovery sets are not exact."""
        out = self.copy()
        base = json.loads((out / "stage_a_state.json").read_text())
        st = self.with_recovery(base, out, tries=2)
        clean = copy.deepcopy(base)                                       # a clean tries=1 attempt with a consumed try 1
        clean["recoveries_consumed"] = [dict(st["recoveries_consumed"][0], attempt_id="06-plain",
                                             authority={**st["recoveries_consumed"][0]["authority"],
                                                        "attempt_id": "06-plain"})]
        overlap = copy.deepcopy(st)
        overlap["attempts"]["05-plain"]["status"] = "interrupted"
        del overlap["completed"]["05-plain"]
        overlap["interrupted"] = [{"id": "05-plain", "session": "s2", "try": 2}, {"id": "05-plain", "session": "s1",
                                                                                 "try": 1}]
        dup = copy.deepcopy(overlap)
        dup["interrupted"] = [{"id": "05-plain", "session": "s2", "try": 2}, {"id": "05-plain", "session": "s2",
                                                                             "try": 2}]
        for name, bad, msg in (("consumed try on a clean attempt", clean, "are not exactly tries []"),
                               ("outstanding and consumed overlap", overlap, "both outstanding and consumed"),
                               ("duplicate outstanding", dup, "exactly one outstanding entry")):
            with self.subTest(name):
                probs = enforce.check_ledger(bad, witness_dir=out)
                self.assertTrue(any(msg in x for x in probs), (name, probs[:4]))

    def test_coherent_zero_negative_and_typed_states(self):
        base = json.loads((self.base / "stage_a_state.json").read_text())
        self.assertEqual(enforce.check_ledger(base), [])
        muts = {
            "negative failed, consistent sums": lambda st: [st["counters"][k].update(
                failed=st["counters"][k]["failed"] - 2, completed=st["counters"][k]["completed"] + 2)
                for k in ("row20", "aggregate")],
            "bool counter": lambda st: st["counters"]["row20"].update(passes=True),
            "float counter": lambda st: st["counters"]["row20"].update(started=194.0),
            "zero tries on one attempt": lambda st: st["attempts"]["00-plain"].update(tries=0),
            "two passes per try": lambda st: st["attempts"]["00-plain"].update(passes=2),
            "completed > started": lambda st: [st["counters"][k].update(completed=st["counters"][k]["started"] + 1)
                                               for k in ("row20", "aggregate")],
            "unknown status": lambda st: st["attempts"]["00-plain"].update(status="maybe"),
            "open attempt without its entry": lambda st: st.update(open_attempt={
                "id": "00-plain", "kind": "mandatory", "row": "row20", "passes": 1, "session": "x", "try": 1}),
            "interrupted entry without status": lambda st: st["interrupted"].append(
                {"id": "00-plain", "session": "x", "try": 1}),
            "aggregate not the sum": lambda st: st["counters"]["aggregate"].update(
                started=st["counters"]["aggregate"]["started"] + 1),
        }
        for name, fn in muts.items():
            with self.subTest(name):
                st = copy.deepcopy(base)
                fn(st)
                self.assertTrue(enforce.check_ledger(st), name)
                self.assertIn("LEDGER_DOMAIN", self.ledger_codes(st))

    def test_ranks_top_k_and_logit_dtype(self):
        self.assertIn("RANKS", self.mutate("05-plain", lambda r: r["requested"][0].update(rank=True)))
        self.assertIn("RANKS", self.mutate("05-plain", lambda r: r["requested"][0].update(rank=-1)))
        self.assertIn("RANKS", self.mutate("05-plain", lambda r: r["requested"][0].update(rank=10 ** 9)))
        def swap(r):                                                          # two ranks exchanged: order violated
            q = sorted(r["requested"], key=lambda q: (-q["logit"], q["id"]))
            q[0]["rank"], q[-1]["rank"] = q[-1]["rank"], q[0]["rank"]
        self.assertIn("RANKS", self.mutate("05-plain", swap))
        self.assertIn("TOP_K", self.mutate("05-plain", lambda r: r["top_ids"].__setitem__(0, -1)))
        self.assertIn("TOP_K", self.mutate("05-plain", lambda r: r["top_ids"].__setitem__(1, r["top_ids"][0])))
        self.assertIn("TOP_K", self.mutate("05-plain", lambda r: r["top_ids"].__setitem__(0, True)))
        self.assertIn("TOP_K", self.mutate("05-plain", lambda r: r["top_logits"].__setitem__(
            0, r["top_logits"][1] - 1.0)))                                     # increasing: not the descending top-k
        self.assertIn("LOGITS_META", self.mutate("05-plain", lambda r: r["final_logits"].update(dtype="x")))
        self.assertIn("LOGITS_META", self.mutate("05-plain", lambda r: r["final_logits"].update(dtype="float32")))

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



REAL_RUN = HERE.parents[2] / "captures" / "photo_stage_a"       # the 2 October run (machine-local, gitignored)


@unittest.skipUnless((REAL_RUN / "INSTRUMENTED_DONE.json").exists(), "needs the 2 October run's records")
class Rev12Transition(unittest.TestCase):
    """Revision 12 (Codex 5eb51a8 A1): the reviewed compatibility transition, PRODUCED on the REAL revision-10
    producer records of 2 October (158 instrumented attempts bound to e146ec63, a terminal record) copied - never
    edited - and resumed under the current package with NO forward: worker_open's transition and the full pre-native
    admission (every record re-read and re-verified, the instrumented validator)."""

    def setUp(self):
        st = json.loads((REAL_RUN / "stage_a_state.json").read_text())
        if st["identities"]["row20"] != stage_a.PREDECESSOR_ID:
            self.skipTest("the 2 October ledger was moved by the 3 October resume's transition (IDENTITY_TRANSITION"
                          ".json); the chained transition is PRODUCED by Rev13Transition")
        self.out = Path(tempfile.mkdtemp()) / "o"
        shutil.copytree(REAL_RUN, self.out, ignore=shutil.ignore_patterns("LOCK"))
        self.ctx = stage_a.Ctx(out=self.out, verify_controller=False)
        self.state0 = json.loads((self.out / "stage_a_state.json").read_text())
        self.done0 = (self.out / "INSTRUMENTED_DONE.json").read_bytes()

    def tearDown(self):
        shutil.rmtree(self.out.parent, ignore_errors=True)

    def release(self):
        tb = (self.out / "TERMINAL.json").read_bytes()
        (self.out / "TERMINAL_RELEASE.json").write_text(json.dumps(
            {"terminal_sha256": hashlib.sha256(tb).hexdigest(), "owner": "the owner", "date": "2026-10-02",
             "words": "release; resume with every counter carried", "reason": "fixture"}))

    def test_resume_admits_the_predecessor_phase_with_counters_carried(self):
        self.assertEqual(self.state0["identities"]["row20"], stage_a.PREDECESSOR_ID)
        self.release()
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")
        cur = json.loads(self.ctx.identity_path.read_text())["identity_sha256"]
        self.assertEqual(budget.identity, cur)
        self.assertNotEqual(cur, stage_a.PREDECESSOR_ID)
        self.assertEqual(budget.state["counters"], self.state0["counters"])          # carried, none reset
        self.assertEqual(budget.state["completed"], self.state0["completed"])        # not relabelled or recomputed
        t = stage_a.transition_record(self.out)
        self.assertEqual((t["from"], t["to"]), (stage_a.PREDECESSOR_ID, cur))
        self.assertEqual(t["counters"], self.state0["counters"])
        self.assertEqual(t["completed_attempts"], sorted(self.state0["completed"]))
        self.assertIn("stage_a_controller.py", t["local_code_differs"])
        self.assertEqual((self.out / "INSTRUMENTED_DONE.json").read_bytes(), self.done0)   # still the producer's
        plains = stage_a.admit_native(self.ctx, plan, budget)                       # every pre-native predicate
        self.assertEqual(len(plains), len(plan["inputs"]))

    def test_no_release_no_transition(self):
        with self.assertRaisesRegex(SystemExit, "terminal|release"):
            stage_a.worker_open(self.ctx, "native")
        self.assertIsNone(stage_a.transition_record(self.out))
        self.assertEqual(json.loads((self.out / "stage_a_state.json").read_text())["identities"]["row20"],
                         stage_a.PREDECESSOR_ID)

    def test_changed_frozen_inputs_refuse(self):
        self.release()
        cur = json.loads(self.ctx.identity_path.read_text())
        with self.assertRaisesRegex(SystemExit, "frozen inputs differ"):
            stage_a.identity_transition(self.ctx, {**cur, "plan_sha256": "0" * 64})
        self.assertIsNone(stage_a.transition_record(self.out))

    def test_relabelled_phase_record_refuses(self):
        self.release()
        d = json.loads(self.done0)
        d["identity"] = "f" * 64
        (self.out / "INSTRUMENTED_DONE.json").write_text(json.dumps(d))
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")
        with self.assertRaises(stage_a.StopCheck):
            stage_a.admit_native(self.ctx, plan, budget)

    def test_undeclared_predecessor_refuses(self):
        self.release()
        st = dict(self.state0)
        st["identities"] = {"row20": "a" * 64}
        (self.out / "stage_a_state.json").write_text(json.dumps(st))
        with self.assertRaises(enforce.StopRun):
            stage_a.worker_open(self.ctx, "native")
        self.assertIsNone(stage_a.transition_record(self.out))



def _u16(x: np.ndarray) -> np.ndarray:
    return (np.asarray(x, dtype=np.float32).view(np.uint32) >> 16).astype(np.uint16)


class Rev13Parity(unittest.TestCase):
    """Revision 13 (R052 handoff 8508993b, A-B): the native logit criterion per requested logit, |d| <= max(0.10, one
    bfloat16 step at the larger magnitude); rel L2 <= 0.01 and identical argmax unchanged. One implementation,
    stage_a.compare, decides both the native worker's StopCheck and the final validator's PARITY row. No forward."""

    def row(self, li, ln, nat_scale=1.0):
        inst = np.ones((stage_a.N_LAYERS, 3), dtype=np.float32)
        return stage_a.compare(_u16(inst), inst * nat_scale, np.asarray(li, dtype=np.float64),
                               np.asarray(ln, dtype=np.float64))

    def test_bf16_step(self):
        for m, step in ((16.5, 0.125), (16.0, 0.125), (15.999, 0.0625), (32.0, 0.25), (3.0, 0.015625),
                        (0.3, 2.0 ** -9), (0.0, 0.0), (-16.5, 0.125)):
            self.assertEqual(stage_a.bf16_step(m), step, m)
        self.assertEqual(stage_a.logit_tolerance(15.999), 0.10)
        self.assertEqual(stage_a.logit_tolerance(16.0), 0.125)
        self.assertEqual(stage_a.logit_tolerance(0.0), 0.10)

    def test_cases(self):
        top = [20.0]                                       # a top logit that keeps the argmax on index 0
        cases = [("one step at 16.5 passes (15-native)", [16.5], [16.375], True),
                 ("two steps at 16.5 fail", [16.5], [16.25], False),
                 ("0.11 at 12.0 fails (unchanged below 16)", [12.0], [12.11], False),
                 ("0.0625 at 3.0 passes (unchanged)", [3.0], [3.0625], True),
                 ("0.13 at 16.0 fails (just over one step)", [16.0], [16.13], False),
                 ("m = 16 exactly, 0.125 passes", [16.0], [15.875], True),
                 ("m just below 16: 0.10 applies, 0.12 fails", [15.99], [15.87], False),
                 ("0.10 exactly below 16 passes", [8.0], [8.1], True)]
        for name, li, ln, ok in cases:
            with self.subTest(name):
                r = self.row(top + li, [top[0] + 0.0] + ln)
                self.assertEqual(r["pass"], ok)
                self.assertEqual(r["logit_within_tolerance"], ok)
                if not ok:
                    msg = stage_a.parity_failure("x-native", r)
                    self.assertIn("magnitude", msg)
                    self.assertIn("tolerance", msg)

    def test_argmax_and_rel_l2_still_fail(self):
        r = self.row([5.0, 1.0], [5.0, 1.0], nat_scale=1.02)                          # rel L2 0.02 > 0.01
        self.assertTrue(r["logit_within_tolerance"])
        self.assertFalse(r["pass"])
        r = self.row([5.0, 4.99], [4.99, 5.0])                                       # within tolerance, argmax swaps
        self.assertTrue(r["logit_within_tolerance"])
        self.assertFalse(r["argmax_equal"])
        self.assertFalse(r["pass"])

    def test_report_labels_the_floor(self):
        """Revision 14 (Codex c4bbcb5 R2 item 4): the SVG's 0.10 guide is the floor, not the bound for every logit."""
        src = Path(R.__file__).read_text()
        self.assertNotIn("(tolerance 0.10)", src)
        self.assertIn('"floor 0.10; at |logit| >= 16 the bound is one bf16 step)"', src)
        self.assertIn("0.10 is the floor, not the bound for every logit", src)

    def test_one_implementation(self):
        src_a = Path(stage_a.__file__).read_text()
        src_r = Path(R.__file__).read_text()
        self.assertIn("**compare(pres, nres, li, ln)", src_a)
        self.assertIn("raise StopCheck(parity_failure(aid, row))", src_a)
        self.assertIn("row = A.compare(", src_r)
        self.assertIn('v.need(row["pass"], "PARITY"', src_r)
        self.assertNotIn('TOL["logit"] and', src_a)                                 # no second, absolute-only test


RESUME_RUN = HERE.parents[2] / "reviews" / "2026-10-03_stage_a_resume_run"


@unittest.skipUnless((REAL_RUN / "IDENTITY_TRANSITION.json").exists() and (REAL_RUN / "passes" / "15-native.json")
                     .exists(), "needs the 3 October resume's records")
class Rev13Transition(unittest.TestCase):
    """Revision 13 (D): the chained reviewed transition, PRODUCED on the REAL records of the 3 October resume (158
    instrumented attempts bound to revision 10 / e146ec63 through the first transition, 16 native records committed
    under revision 12 / c0fb2ea0, the native StopCheck in TERMINAL.json) copied - never edited - and resumed under the
    current package with NO forward."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp()) / "o"
        # the copy starts with NO release (the live directory may hold the owner's; each test writes the release it
        # needs); the 2 October one, if kept beside the live record, is copied under its own name
        shutil.copytree(REAL_RUN, self.out, ignore=shutil.ignore_patterns("LOCK", "TERMINAL_RELEASE.json"))
        self.ctx = stage_a.Ctx(out=self.out, verify_controller=False)
        self.state0 = json.loads((self.out / "stage_a_state.json").read_text())
        self.done0 = (self.out / "INSTRUMENTED_DONE.json").read_bytes()
        self.t1 = (self.out / "IDENTITY_TRANSITION.json").read_bytes()

    def tearDown(self):
        shutil.rmtree(self.out.parent, ignore_errors=True)

    def release(self, terminal_bytes=None):
        tb = terminal_bytes if terminal_bytes is not None else (self.out / "TERMINAL.json").read_bytes()
        (self.out / "TERMINAL_RELEASE.json").write_text(json.dumps(
            {"terminal_sha256": hashlib.sha256(tb).hexdigest(), "owner": "the owner", "date": "2026-10-03",
             "words": "release; resume with every counter carried", "reason": "fixture"}))

    def test_the_real_records_are_the_3_october_state(self):
        self.assertEqual(self.state0["identities"]["row20"], stage_a.PREDECESSOR_12_ID)
        t = json.loads(self.t1)
        self.assertEqual((t["from"], t["to"]), (stage_a.PREDECESSOR_ID, stage_a.PREDECESSOR_12_ID))
        self.assertEqual(json.loads(self.done0)["identity"], stage_a.PREDECESSOR_ID)
        self.assertEqual(self.state0["counters"]["row20"], {"completed": 189, "failed": 1, "passes": 190,
                                                           "started": 190})
        self.assertIn("15-native", (self.out / "TERMINAL.json").read_text())

    def test_resume_admits_both_predecessors_with_counters_carried(self):
        self.release()
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")
        cur = json.loads(self.ctx.identity_path.read_text())["identity_sha256"]
        self.assertNotIn(cur, stage_a.PREDECESSORS)
        self.assertEqual(budget.identity, cur)
        self.assertEqual(budget.state["counters"], self.state0["counters"])          # carried, none reset
        self.assertEqual(budget.state["completed"], self.state0["completed"])        # not relabelled or recomputed
        self.assertEqual((self.out / "IDENTITY_TRANSITION.json").read_bytes(), self.t1)   # the first stays as written
        t2 = json.loads((self.out / "IDENTITY_TRANSITION.2.json").read_text())
        self.assertEqual((t2["from"], t2["to"]), (stage_a.PREDECESSOR_12_ID, cur))
        self.assertEqual(t2["predecessor"]["package"], "Stage A revision 12, RSC 620f768")
        self.assertEqual(t2["counters"], self.state0["counters"])
        self.assertIn("15-native", t2["completed_attempts"])
        self.assertIn("stage_a.py", t2["local_code_differs"])
        self.assertEqual([r["to"] for r in stage_a.transition_records(self.out)], [stage_a.PREDECESSOR_12_ID, cur])
        self.assertEqual((self.out / "INSTRUMENTED_DONE.json").read_bytes(), self.done0)   # still the producer's
        self.assertTrue(stage_a.admitted_phase_identity(self.out, stage_a.PREDECESSOR_ID, cur))    # two links
        self.assertTrue(stage_a.admitted_phase_identity(self.out, stage_a.PREDECESSOR_12_ID, cur))  # one link
        self.assertFalse(stage_a.admitted_phase_identity(self.out, "f" * 64, cur))
        plains = stage_a.admit_native(self.ctx, plan, budget)                       # every pre-native predicate
        self.assertEqual(len(plains), len(plan["inputs"]))
        # the 16 committed native records re-evaluated under the revision-13 rule (no forward): all pass,
        # 15-native at exactly one bf16 step
        rows = {}
        for i in range(16):
            aid = f"{i:02d}-native"
            rec, arrays = stage_a.load_outputs(self.out, aid, budget.completed(aid))
            prec, pres = plains[i]
            rows[aid] = stage_a.compare(pres, arrays["residuals"],
                                        np.array([q["logit"] for q in prec["requested"]], dtype=np.float64),
                                        np.asarray(rec["requested_logits"], dtype=np.float64))
        self.assertTrue(all(r["pass"] for r in rows.values()), [a for a, r in rows.items() if not r["pass"]])
        r15 = rows["15-native"]
        self.assertEqual((r15["logit_max_abs"], r15["logit_max_abs_magnitude"], r15["logit_max_abs_tolerance"],
                          r15["logit_max_abs_bf16_steps"]), (0.125, 16.5, 0.125, 1.0))
        self.assertTrue(all(r["rel_l2_max"] == 0.0 and r["argmax_equal"] for r in rows.values()))
        # under revision 12's absolute rule exactly 15-native would fail
        self.assertEqual([a for a, r in rows.items() if r["logit_max_abs"] > 0.10], ["15-native"])

    def test_no_release_no_transition(self):
        with self.assertRaisesRegex(SystemExit, "terminal|release"):
            stage_a.worker_open(self.ctx, "native")
        self.assertFalse((self.out / "IDENTITY_TRANSITION.2.json").exists())
        self.assertEqual(json.loads((self.out / "stage_a_state.json").read_text())["identities"]["row20"],
                         stage_a.PREDECESSOR_12_ID)

    def test_the_2_october_release_does_not_release_the_3_october_record(self):
        old = self.out / "TERMINAL_RELEASE.2026-10-02.json"
        if old.exists():
            shutil.copyfile(old, self.out / "TERMINAL_RELEASE.json")
        else:                                                                       # reconstructed: the old bytes
            self.release(terminal_bytes=b"the 2 October terminal record")
        self.assertIsNone(G.terminal_release(self.out))                            # stale: names the old bytes
        with self.assertRaisesRegex(SystemExit, "terminal|release"):
            stage_a.worker_open(self.ctx, "native")

    def test_changed_frozen_inputs_refuse(self):
        self.release()
        cur = json.loads(self.ctx.identity_path.read_text())
        with self.assertRaisesRegex(SystemExit, "frozen inputs differ"):
            stage_a.identity_transition(self.ctx, {**cur, "manifest_sha256": "0" * 64})
        self.assertFalse((self.out / "IDENTITY_TRANSITION.2.json").exists())

    def test_broken_chain_admits_nothing(self):
        self.release()
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")
        (self.out / "IDENTITY_TRANSITION.json").unlink()                           # the first link gone
        self.assertFalse(stage_a.admitted_phase_identity(self.out, stage_a.PREDECESSOR_ID, budget.identity))
        with self.assertRaises(stage_a.StopCheck):
            stage_a.admit_native(self.ctx, plan, budget)

    def test_relabelled_phase_record_refuses(self):
        self.release()
        d = json.loads(self.done0)
        d["identity"] = stage_a.PREDECESSOR_12_ID                                   # relabelled to the later producer
        (self.out / "INSTRUMENTED_DONE.json").write_text(json.dumps(d))
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")
        self.assertTrue(stage_a.admitted_phase_identity(self.out, d["identity"], budget.identity))
        d["identity"] = "f" * 64
        (self.out / "INSTRUMENTED_DONE.json").write_text(json.dumps(d))
        with self.assertRaises(stage_a.StopCheck):
            stage_a.admit_native(self.ctx, plan, budget)

    def test_ledger_not_where_the_chain_ends_refuses(self):
        self.release()
        t = json.loads(self.t1)
        t["to"] = "b" * 64
        (self.out / "IDENTITY_TRANSITION.json").write_text(json.dumps(t))
        with self.assertRaisesRegex(SystemExit, "recorded transitions end"):
            stage_a.worker_open(self.ctx, "native")

    def test_undeclared_predecessor_refuses(self):
        self.release()
        st = dict(self.state0)
        st["identities"] = {"row20": "a" * 64}
        (self.out / "stage_a_state.json").write_text(json.dumps(st))
        with self.assertRaises(enforce.StopRun):
            stage_a.worker_open(self.ctx, "native")
        self.assertFalse((self.out / "IDENTITY_TRANSITION.2.json").exists())

    def test_retained_resume_records_match_the_live_ones(self):
        """The retained copy in reviews/ is the evidence the brief cites: its TERMINAL and transition equal the
        live records this class copies."""
        if not RESUME_RUN.exists():
            self.skipTest("no retained resume record")
        for n in ("TERMINAL.json", "IDENTITY_TRANSITION.json"):
            self.assertEqual((RESUME_RUN / n).read_bytes(), (REAL_RUN / n).read_bytes(), n)



@unittest.skipUnless((REAL_RUN / "IDENTITY_TRANSITION.json").exists() and (REAL_RUN / "passes" / "15-native.json")
                     .exists(), "needs the 3 October resume's records")
class Rev14PreparedLink(unittest.TestCase):
    """Revision 14 (Codex c4bbcb5 R1): the prepared-link write boundary. A fault between write (1), the durable second
    link, and write (2), the ledger slot, is injected on a COPY of the real 3 October records (no forward); the next
    start reconciles the exact prepared tail idempotently - only the slot commit."""

    setUp, tearDown, release = Rev13Transition.setUp, Rev13Transition.tearDown, Rev13Transition.release

    def prepare(self):
        """Produce the post-link / pre-slot state by failing write (2) once."""
        self.release()
        real = enforce.write_json_atomic

        def failing(path, obj, *a, **k):
            if Path(path).name == "stage_a_state.json":
                raise OSError("injected: the ledger slot write fails after the link is durable")
            return real(path, obj, *a, **k)
        enforce.write_json_atomic = failing
        try:
            with self.assertRaisesRegex(OSError, "injected"):
                stage_a.worker_open(self.ctx, "native")
        finally:
            enforce.write_json_atomic = real
        self.assertTrue((self.out / "IDENTITY_TRANSITION.2.json").exists())
        self.assertEqual(json.loads((self.out / "stage_a_state.json").read_text())["identities"]["row20"],
                         stage_a.PREDECESSOR_12_ID)
        return (self.out / "IDENTITY_TRANSITION.2.json").read_bytes()

    def snapshot(self):
        return {p.name: p.read_bytes() for p in sorted(self.out.iterdir()) if p.is_file()}

    def test_fault_between_the_writes_then_retry_reconciles(self):
        link2 = self.prepare()
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")                  # the retry
        cur = json.loads(self.ctx.identity_path.read_text())["identity_sha256"]
        self.assertEqual(budget.identity, cur)
        self.assertFalse((self.out / "IDENTITY_TRANSITION.3.json").exists())       # no third link
        self.assertEqual((self.out / "IDENTITY_TRANSITION.2.json").read_bytes(), link2)
        self.assertEqual((self.out / "IDENTITY_TRANSITION.json").read_bytes(), self.t1)
        self.assertEqual((self.out / "INSTRUMENTED_DONE.json").read_bytes(), self.done0)
        self.assertEqual(budget.state["counters"], self.state0["counters"])
        self.assertEqual(budget.state["completed"], self.state0["completed"])
        self.assertEqual(len(stage_a.admit_native(self.ctx, plan, budget)), len(plan["inputs"]))

    def test_repeat_of_the_reconciled_state_writes_nothing(self):
        self.prepare()
        stage_a.identity_transition(self.ctx, json.loads(self.ctx.identity_path.read_text()))
        before = self.snapshot()
        stage_a.identity_transition(self.ctx, json.loads(self.ctx.identity_path.read_text()))
        self.assertEqual(self.snapshot(), before)

    def test_prepared_tail_under_an_invalidated_release_refuses_then_a_new_release_reconciles(self):
        self.prepare()
        tb = (self.out / "TERMINAL.json").read_bytes()
        (self.out / "TERMINAL.json").write_bytes(tb.replace(b'"later": [', b'"later": [{"phase": "native", "pid": 1, '
                                                            b'"reason": "a later failure", "wall": "x"}, ', 1))
        with self.assertRaisesRegex(SystemExit, "terminal"):                       # the terminal gate first
            stage_a.worker_open(self.ctx, "native")
        with self.assertRaisesRegex(SystemExit, "terminal release"):               # and the reconciliation itself
            stage_a.identity_transition(self.ctx, json.loads(self.ctx.identity_path.read_text()))
        self.assertEqual(json.loads((self.out / "stage_a_state.json").read_text())["identities"]["row20"],
                         stage_a.PREDECESSOR_12_ID)
        self.release()                                                             # the owner's NEW release
        stage_a.worker_open(self.ctx, "native")
        self.assertFalse((self.out / "IDENTITY_TRANSITION.3.json").exists())

    def test_prepared_tail_whose_endpoints_differ_refuses(self):
        self.prepare()
        for k, v in (("to", "b" * 64), ("from", "c" * 64)):
            with self.subTest(k):
                t = json.loads((self.out / "IDENTITY_TRANSITION.2.json").read_text())
                good = dict(t)
                t[k] = v
                (self.out / "IDENTITY_TRANSITION.2.json").write_text(json.dumps(t))
                with self.assertRaisesRegex(SystemExit, "recorded transitions end"):
                    stage_a.worker_open(self.ctx, "native")
                (self.out / "IDENTITY_TRANSITION.2.json").write_text(json.dumps(good))

    def test_prepared_tail_whose_counters_or_ids_differ_refuses(self):
        self.prepare()
        good = json.loads((self.out / "IDENTITY_TRANSITION.2.json").read_text())
        for k, v in (("counters", {**good["counters"], "row20": {**good["counters"]["row20"], "started": 1}}),
                     ("completed_attempts", good["completed_attempts"][:-1]),
                     ("frozen_identical", good["frozen_identical"][:-1])):
            with self.subTest(k):
                (self.out / "IDENTITY_TRANSITION.2.json").write_text(json.dumps({**good, k: v}))
                with self.assertRaisesRegex(SystemExit, "prepared transition record does not match"):
                    stage_a.worker_open(self.ctx, "native")
                self.assertEqual(json.loads((self.out / "stage_a_state.json").read_text())["identities"]["row20"],
                                 stage_a.PREDECESSOR_12_ID)



@unittest.skipUnless((REAL_RUN / "IDENTITY_TRANSITION.json").exists() and (REAL_RUN / "passes" / "15-native.json")
                     .exists(), "needs the 3 October resume's records")
class Rev15Environment(unittest.TestCase):
    """Revision 15 (R052 handoff 6dc8029e): macOS 27.0 -> 27.0.1 as the ONE declared environment difference of the
    revision-12 -> current link, on a COPY of the real 3 October records (no forward). The current identity is the
    one regenerated on this machine (27.0.1)."""

    setUp, tearDown, release = Rev13Transition.setUp, Rev13Transition.tearDown, Rev13Transition.release
    prepare = Rev14PreparedLink.prepare

    def cur(self):
        return json.loads(self.ctx.identity_path.read_text())

    def test_the_declared_pair_is_admitted_and_recorded(self):
        self.assertEqual(stage_a.PREDECESSOR_12["identity_body"]["macos"], "27.0")
        self.assertEqual(self.cur()["macos"], "27.0.1")
        self.assertNotIn("macos", stage_a.FROZEN_KEYS)
        self.release()
        budget, plan, _ = stage_a.worker_open(self.ctx, "native")
        t2 = json.loads((self.out / "IDENTITY_TRANSITION.2.json").read_text())
        self.assertEqual([(d["field"], d["from"], d["to"]) for d in t2["environment_differences"]],
                         [("macos", "27.0", "27.0.1")])
        self.assertEqual(t2["environment_differences"][0]["to_build"], stage_a.os_build())
        self.assertNotIn("macos", t2["frozen_identical"])
        self.assertEqual((self.out / "IDENTITY_TRANSITION.json").read_bytes(), self.t1)    # link 1 untouched
        self.assertEqual(budget.state["counters"], self.state0["counters"])
        self.assertEqual(len(stage_a.admit_native(self.ctx, plan, budget)), len(plan["inputs"]))
        # per-record provenance: 00-15 native and the instrumented records on 27.0; later records on 27.0.1
        for aid, want in (("00-native", "27.0"), ("15-native", "27.0"), ("03-plain", "27.0"), ("16-native", "27.0.1"),
                          ("19-native", "27.0.1")):
            self.assertEqual(stage_a.attempt_environment(self.out, aid, "27.0.1"), want, aid)

    def test_another_current_os_refuses(self):
        self.release()
        with self.assertRaisesRegex(SystemExit, "environment field macos"):
            stage_a.identity_transition(self.ctx, {**self.cur(), "macos": "27.1"})
        self.assertFalse((self.out / "IDENTITY_TRANSITION.2.json").exists())

    def test_a_predecessor_os_other_than_the_declared_one_refuses(self):
        self.release()
        saved = stage_a.PREDECESSOR_12["environment_differences"]
        stage_a.PREDECESSOR_12["environment_differences"] = {"macos": ["26.9", "27.0.1"]}
        try:
            with self.assertRaisesRegex(SystemExit, "environment field macos"):
                stage_a.identity_transition(self.ctx, self.cur())
        finally:
            stage_a.PREDECESSOR_12["environment_differences"] = saved
        self.assertFalse((self.out / "IDENTITY_TRANSITION.2.json").exists())

    def test_another_frozen_field_changed_with_it_refuses(self):
        self.release()
        with self.assertRaisesRegex(SystemExit, "frozen inputs differ"):
            stage_a.identity_transition(self.ctx, {**self.cur(), "machine": "x86_64"})
        self.assertFalse((self.out / "IDENTITY_TRANSITION.2.json").exists())

    def test_the_revision_10_predecessor_declares_no_difference(self):
        self.assertEqual(stage_a.PREDECESSOR.get("environment_differences", {}), {})
        with self.assertRaisesRegex(SystemExit, "environment field macos"):
            stage_a.environment_differences(stage_a.PREDECESSOR, stage_a.PREDECESSOR["identity_body"], self.cur())

    def test_a_prepared_tail_for_another_os_pair_refuses(self):
        self.prepare()
        t = json.loads((self.out / "IDENTITY_TRANSITION.2.json").read_text())
        t["environment_differences"] = [{**t["environment_differences"][0], "to": "27.1"}]
        (self.out / "IDENTITY_TRANSITION.2.json").write_text(json.dumps(t))
        with self.assertRaisesRegex(SystemExit, "prepared transition record does not match"):
            stage_a.worker_open(self.ctx, "native")
        self.assertEqual(json.loads((self.out / "stage_a_state.json").read_text())["identities"]["row20"],
                         stage_a.PREDECESSOR_12_ID)

    def test_report_states_the_mixed_provenance(self):
        """Source-string scope (as revision 14's label test): the report's provenance note and OS column exist."""
        src = Path(R.__file__).read_text()
        self.assertIn("Environment provenance (revision 15)", src)
        self.assertIn("| native macOS |", src)
        self.assertIn("AMBIGUOUS (OS or path)", src)
        self.assertIn("A.attempt_environment(out, r['id'], cur_os)", src)


if __name__ == "__main__":
    unittest.main()
