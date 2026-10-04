"""Stage A revision 16: the row-20 OS-bridge supplement (Codex b0db0f9; STAGE_A_SUPPLEMENT_CRITERIA.md) on the fake
instrument - no model is imported, loaded or run, and no forward. A complete fake Stage A run is made in a temporary
tree and given the accepted-bundle files (controller record, admitted final, acceptance); the supplement runs beside
it in its own tree. SupplementController fixtures use the real controller, watchdog and guardian with synthetic
workers (fake_worker.py sgates / ok / sreceipt).

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_stage_a_supplement.py' -v
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fake_stage_a as F  # noqa: E402
import enforce  # noqa: E402
import stage_a  # noqa: E402
import stage_a_controller as C  # noqa: E402

PY = sys.executable
BUILD = stage_a.SUPP_ENVIRONMENT["build"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fake_identity() -> dict:
    """A full identity body (the real revision-15 file's fields, so the compatibility record is complete) under a
    fake identity_sha256."""
    ident = json.loads(stage_a.IDENTITY.read_text())
    ident["identity_sha256"] = "e" * 64
    return ident


def accept_stage_a(a: Path) -> None:
    """The accepted-bundle files a real Stage A tree has after its PASS and Codex's acceptance."""
    (a / "controller.json").write_text(json.dumps({"seconds_total": 2338.113973380568, "carry_s": 1808.73}))
    fin = json.dumps({"outcome": "PASS", "session": "stagea"}).encode()
    (a / "STAGE_A_FINAL.json").write_bytes(fin)
    (a / "STAGE_A_FINAL.ADMITTED.json").write_text(json.dumps({"final_sha256": sha(fin), "session": "stagea"}))
    (a / "report").mkdir(exist_ok=True)
    (a / "report/ACCEPTANCE.json").write_text(json.dumps({"record": "fixture"}))


_TEMPLATE: dict = {}


def stage_a_template() -> Path:
    """One complete fake Stage A run (194/193/1/194) with its accepted-bundle files, copied into each test."""
    if "a" not in _TEMPLATE:
        d = Path(tempfile.mkdtemp()) / "photo_stage_a"
        enforce.STORAGE.update(roots=None)
        stage_a.run_instrumented(F.make_ctx(d))
        stage_a.run_native(F.make_ctx(d))
        accept_stage_a(d)
        enforce.STORAGE.update(roots=None)
        _TEMPLATE["a"] = d
    return _TEMPLATE["a"]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.a, self.s = root / "photo_stage_a", root / "photo_stage_a_supplement"
        os.environ.pop("STAGE_A_GATES", None)
        os.environ.pop("STAGE_A_SESSION", None)
        enforce.STORAGE.update(roots=None)
        shutil.copytree(stage_a_template(), self.a)
        self.ident = fake_identity()
        self.ident_path = root / "supp_identity.json"
        self.ident_path.write_text(json.dumps(self.ident))
        self.plan_path = root / "supp_plan.json"
        self.plan_path.write_text(json.dumps(stage_a.make_supplement_plan(self.ctx())))
        self.a_bytes = enforce.dir_bytes([self.a])

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("STAGE_A_GATES", None)
        enforce.STORAGE.update(roots=None)

    def ctx(self, faults: dict | None = None, native_scale: float = 1.0, **kw) -> stage_a.Ctx:
        c = F.make_ctx(self.s, faults or {})
        s = self.s

        def native_factory():
            from transformers import AutoTokenizer
            from image_adapter import SNAPSHOT
            tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))

            def forward(vmodel, seq, pv, layers, positions):
                rec = json.loads((s / f"passes/{stage_a.SUPP_INST}.json").read_text())
                res = stage_a.bf16_to_f32(np.load(s / f"passes/{stage_a.SUPP_INST}.residuals.npy")) * native_scale
                logits = np.zeros(F.VOCAB, dtype=np.float32)
                for q in rec["requested"]:
                    logits[q["id"]] = q["logit"]
                x = F._PLAN["inputs"][0]
                return {"residuals": res, "logits": logits, "decoder_calls": {"min": 1, "max": 1, "layers": 64},
                        "effective_positions_sha256": x["expected"]["positions_sha256"],
                        "inputs_embeds_sha256": rec["image"]["merge"]["merged_sha256"],
                        "inputs_embeds_dtype": "mlx.core.bfloat16"}
            return None, F.FakeProcessor(), tok, forward
        c.native_factory = native_factory
        c.identity_path = self.ident_path
        c.compute_identity = lambda: self.ident
        c.supp_plan_path = self.plan_path
        c.stage_a_out = self.a
        c.os_build_fn = lambda: BUILD
        for k, v in kw.items():
            setattr(c, k, v)
        return c

    def gates(self, **kw) -> dict:
        self.assertEqual(stage_a.run_supplement_gates(self.ctx(**kw)), 0)
        g = json.loads((self.s / "SUPPLEMENT_GATES.json").read_text())
        os.environ["STAGE_A_GATES"] = json.dumps(g)
        return g

    def state(self) -> dict:
        return json.loads((self.s / "stage_a_state.json").read_text())

    def stage_a_unchanged(self) -> None:
        self.assertEqual(enforce.dir_bytes([self.a]), self.a_bytes)
        stage_a.check_stage_a_frozen(self.ctx(), json.loads(self.plan_path.read_text()))

    def finalise(self) -> dict:
        """What SupplementController._finalise writes on a PASS: the final record naming the receipt, then its marker."""
        rp = self.s / C.SUPPLEMENT_NAMES["receipt"]
        rc = json.loads(rp.read_text())
        fin = json.dumps({"outcome": "PASS" if rc["outcome"] == "PASS" else "STOPPED", "session": rc["session"],
                          "receipt_sha256": sha(rp.read_bytes())}).encode()
        (self.s / C.SUPPLEMENT_NAMES["final"]).write_bytes(fin)
        (self.s / C.SUPPLEMENT_NAMES["admitted"]).write_text(json.dumps({"final_sha256": sha(fin),
                                                                         "session": rc["session"]}))
        return json.loads(fin)

    def verify(self, ident: dict | None = None, build: str = BUILD) -> dict:
        return stage_a.supplement_receipt_ok(ident or self.ident, out=self.s, supp_plan_path=self.plan_path,
                                             stage_a_out=self.a, build=build)


class Plan(Base):
    def test_input_00_fixed_and_row20_accounting(self):
        p = json.loads(self.plan_path.read_text())
        self.assertEqual(p["input"], F._PLAN["inputs"][0])                      # the original input 00, every hash
        self.assertEqual(p["input_sha256"], sha(json.dumps(F._PLAN["inputs"][0], sort_keys=True).encode()))
        self.assertEqual([a["id"] for a in p["attempts"]], ["00-plain-os2701", "00-native-os2701"])
        e = p["envelope"]
        self.assertEqual((e["starts_before"], e["starts_after"], e["cap_attempts"], e["in_hand_after"]),
                         (194, 196, 200, 4))
        self.assertEqual(e["seconds_carry"], 2338.113973380568)
        self.assertEqual(e["storage_carry_bytes"], self.a_bytes)
        self.assertEqual(p["reference"]["outputs"],
                         json.loads((self.a / "stage_a_state.json").read_text())["completed"]["00-plain"]["outputs"])
        self.assertEqual(p["budget_sha256"], stage_a.budget_sha256(e))

    def test_tampered_plan_refused(self):
        for mutate in (lambda p: p["input"].update(png_sha256="0" * 64),
                       lambda p: p["attempts"].append({"id": "00-extra"}),
                       lambda p: p["envelope"].update(starts_after=195),
                       lambda p: p["stage_a"]["counters_row20"].update(started=190),
                       lambda p: p["environment"].update(build="26A999")):
            p = json.loads(self.plan_path.read_text())
            mutate(p)
            bad = self.plan_path.parent / "bad_plan.json"
            bad.write_text(json.dumps(p))
            with self.assertRaises(SystemExit):
                stage_a.load_supplement(self.ctx(supp_plan_path=bad))

    def test_stage_a_tree_must_stay_frozen(self):
        before = (self.a / "controller.json").read_bytes()
        (self.a / "controller.json").write_text(json.dumps({"seconds_total": 1.0}))
        with self.assertRaisesRegex(SystemExit, "Stage A tree changed"):
            stage_a.run_supplement_gates(self.ctx())
        (self.a / "controller.json").write_bytes(before)
        (self.a / "extra.bin").write_bytes(b"x")                                   # any new byte in the tree
        with self.assertRaisesRegex(SystemExit, "tree_bytes"):
            stage_a.run_supplement_gates(self.ctx())
        (self.a / "extra.bin").unlink()
        (self.a / "STAGE_A_FINAL.ADMITTED.json").unlink()                          # an unadmitted Stage A final
        with self.assertRaisesRegex(SystemExit, "lacks STAGE_A_FINAL.ADMITTED.json"):
            stage_a.run_supplement_gates(self.ctx())
        self.assertFalse(self.s.exists() and (self.s / "SUPPLEMENT_GATES.json").exists())


class Gates(Base):
    def test_declared_environment_build_not_just_version(self):
        with self.assertRaisesRegex(SystemExit, "not the declared"):
            stage_a.run_supplement_gates(self.ctx(os_build_fn=lambda: "26A999"))
        other = {**self.ident, "macos": "27.0"}
        with self.assertRaisesRegex(SystemExit, "not the declared"):
            stage_a.run_supplement_gates(self.ctx(compute_identity=lambda: other,
                                                  identity_path=self._write(other)))
        self.assertFalse((self.s / "SUPPLEMENT_GATES.json").exists())

    def _write(self, ident: dict) -> Path:
        p = self.ident_path.parent / "other_identity.json"
        p.write_text(json.dumps(ident))
        return p

    def test_go_is_stage_a_supplement_and_binds_the_package(self):
        seen = {}

        def fake_require_go(go_path, pkg, *, row, stage, verify_at_commit, repo=None):
            seen.update(row=row, stage=stage, keys=sorted(pkg), at=verify_at_commit)
            raise SystemExit("refused: ROW20S_GO.json absent - no owner go bound to a favourable review")
        import stage_a_guard as G
        real = G.require_go
        G.require_go = fake_require_go
        try:
            with self.assertRaisesRegex(SystemExit, "ROW20S_GO.json absent"):
                stage_a.run_supplement_gates(self.ctx(check_go=None))
        finally:
            G.require_go = real
        self.assertEqual((seen["row"], seen["stage"]), ("20", "A-supplement"))
        self.assertEqual(seen["keys"], ["budget_sha256", "manifest_sha256", "plan_sha256",
                                        "supplement_criteria_sha256", "supplement_identity_sha256",
                                        "supplement_plan_sha256"])
        self.assertIs(seen["at"], stage_a.supplement_package_at_commit)

    def test_interrupted_try_stops_the_supplement(self):
        self.gates()
        budget, *_ = stage_a.supplement_open(self.ctx(), "supplement_instrumented")
        cm = budget.attempt(stage_a.SUPP_INST, "supplement_instrumented", passes=1)
        cm.__enter__()                                                            # a crash mid-forward
        self.assertIsNotNone(self.state()["open_attempt"])
        with self.assertRaisesRegex(SystemExit, "interrupted supplement try"):
            stage_a.run_supplement_gates(self.ctx())
        self.assertTrue((self.s / C.SUPPLEMENT_TERMINAL).exists())               # no recovery path, no retry
        c = self.state()["counters"]["row20"]
        self.assertEqual((c["started"], c["failed"]), (195, 2))                  # the start stays charged
        with self.assertRaisesRegex(SystemExit, "stopped terminally"):
            stage_a.run_supplement_instrumented(self.ctx())
        self.stage_a_unchanged()


class Run(Base):
    def test_pass_both_comparisons_receipt_and_row21_verifier(self):
        g = self.gates()
        r1 = stage_a.run_supplement_instrumented(self.ctx())
        r2 = stage_a.run_supplement_native(self.ctx())
        self.assertTrue(r1["comparison_a"] and r2["comparison_b"])
        c = self.state()["counters"]["row20"]
        self.assertEqual((c["started"], c["completed"], c["failed"], c["passes"]), (196, 195, 1, 196))
        self.assertEqual(enforce.check_ledger(self.state(), witness_dir=self.s), [])
        ca = json.loads((self.s / "supplement/comparison_a.json").read_text())
        cb = json.loads((self.s / "supplement/comparison_b.json").read_text())
        self.assertEqual((ca["reference"], ca["candidate"]), ("00-plain", "00-plain-os2701"))
        self.assertEqual((cb["reference"], cb["candidate"]), ("00-plain-os2701", "00-native-os2701"))
        self.assertTrue(ca["pass"] and cb["pass"] and ca["diagnostic"]["residuals_bitwise_equal"])
        rc = stage_a.run_supplement_receipt(self.ctx())
        self.assertEqual(rc["outcome"], "PASS", rc["reasons"])
        receipt = json.loads((self.s / C.SUPPLEMENT_NAMES["receipt"]).read_text())
        self.assertEqual(set(receipt), C.SUPPLEMENT_RECEIPT_KEYS)
        self.assertEqual((receipt["package"], receipt["identity"]), (g["package"], g["identity"]))
        for rel, h in receipt["outputs"].items():
            self.assertEqual(sha((self.s / rel).read_bytes()), h)
        self.assertEqual(receipt["compatibility"]["build"], BUILD)
        self.stage_a_unchanged()                                                  # nothing written to Stage A
        self.assertFalse((self.a / "TERMINAL.json").exists())
        # row 21's verifier
        self.assertIn("no admitted supplement final record", self.verify()["why"][0])   # before the final: hold
        self.finalise()
        v = self.verify()
        self.assertTrue(v["ok"], v["why"])
        self.assertIn("build", str(self.verify(build="26A999")["why"]))          # same version, other build
        moved = {**self.ident, "package_file_maps_sha256": "0" * 64}              # same macOS string, other runtime
        self.assertIn("package_file_maps_sha256", str(self.verify(moved)["why"]))
        proc = copy.deepcopy(self.ident)
        proc["local_code_sha256"]["image_adapter.py"] = "0" * 64                 # processor code changed
        self.assertIn("processor_code_sha256", str(self.verify(proc)["why"]))
        incomplete = {k: v for k, v in self.ident.items() if k != "lens"}
        self.assertFalse(self.verify(incomplete)["ok"])
        cp = self.s / "supplement/comparison_b.json"                              # a changed retained receipt
        keep = cp.read_bytes()
        cp.write_bytes(keep.replace(b'"pass": true', b'"pass": false'))
        self.assertFalse(self.verify()["ok"])
        cp.write_bytes(keep)
        (self.s / C.SUPPLEMENT_NAMES["admitted"]).unlink()                        # absent / unadmitted
        v = self.verify()
        self.assertFalse(v["ok"])
        self.assertIn("no admitted supplement final record", v["why"][0])

    def test_comparison_a_failure_stops_and_retains_its_receipt(self):
        self.gates()
        with self.assertRaisesRegex(stage_a.StopCheck, r"comparison \(a\)"):
            stage_a.run_supplement_instrumented(self.ctx({"differ": [0, "plain-like"]}))
        ca = json.loads((self.s / "supplement/comparison_a.json").read_text())
        self.assertFalse(ca["pass"])                                              # retained, failing
        self.assertTrue((self.s / C.SUPPLEMENT_TERMINAL).exists())
        c = self.state()["counters"]["row20"]
        self.assertEqual((c["started"], c["completed"]), (195, 194))             # preserved, not reset
        for run in (stage_a.run_supplement_instrumented, stage_a.run_supplement_native):
            with self.assertRaisesRegex(SystemExit, "stopped terminally"):      # no retry, no other input
                run(self.ctx())
        self.assertEqual(stage_a.run_supplement_receipt(self.ctx())["outcome"], "STOPPED")
        self.assertFalse((self.a / "TERMINAL.json").exists())                    # Stage A's gate untouched
        self.stage_a_unchanged()

    def test_comparison_b_failure_stops(self):
        self.gates()
        stage_a.run_supplement_instrumented(self.ctx())
        with self.assertRaisesRegex(stage_a.StopCheck, r"comparison \(b\)"):
            stage_a.run_supplement_native(self.ctx(native_scale=1.5))
        self.assertFalse(json.loads((self.s / "supplement/comparison_b.json").read_text())["pass"])
        c = self.state()["counters"]["row20"]
        self.assertEqual(c["started"], 196)
        r = stage_a.run_supplement_receipt(self.ctx())
        self.assertEqual(r["outcome"], "STOPPED")
        self.assertIn("comparison (b) absent or not passing", r["reasons"])

    def test_failed_forward_is_charged_and_stops(self):
        self.gates()
        ctx = self.ctx()
        inst_factory = ctx.instrument_factory

        def broken():
            inst = inst_factory()
            inst.capture = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fixture: forward failed"))
            return inst
        ctx.instrument_factory = broken
        with self.assertRaisesRegex(RuntimeError, "forward failed"):
            stage_a.run_supplement_instrumented(ctx)
        c = self.state()["counters"]["row20"]
        self.assertEqual((c["started"], c["failed"], c["passes"]), (195, 2, 195))   # the start is charged
        self.assertTrue((self.s / C.SUPPLEMENT_TERMINAL).exists())

    def test_native_refused_before_the_instrumented_phase(self):
        self.gates()
        with self.assertRaisesRegex(SystemExit, "supplement instrumented phase has not completed"):
            stage_a.run_supplement_native(self.ctx())
        self.assertNotIn(stage_a.SUPP_NAT, self.state()["attempts"])

    def test_a_started_endpoint_is_never_resumed(self):
        """Revision 2 (Codex 478196f P1): a committed endpoint is never reloaded or continued by a later run, and native
        is never dispatched on an instrumented commit from another session."""
        self.gates()
        stage_a.run_supplement_instrumented(self.ctx())
        (self.s / "SUPPLEMENT_INSTRUMENTED_DONE.json").unlink()                   # died after commit, before DONE
        calls = []
        ctx = self.ctx()
        f = ctx.instrument_factory
        ctx.instrument_factory = lambda: (lambda i: (setattr(i, "capture", lambda *a, **k: calls.append(1)), i)[1])(f())
        with self.assertRaisesRegex(stage_a.StopCheck, "never resumes after a start"):
            stage_a.run_supplement_instrumented(ctx)
        self.assertEqual(calls, [])
        self.assertTrue((self.s / C.SUPPLEMENT_TERMINAL).exists())
        self.assertEqual(self.state()["counters"]["row20"]["started"], 195)      # preserved

    def test_native_needs_the_instrumented_commit_of_its_own_session(self):
        self.gates()
        stage_a.run_supplement_instrumented(self.ctx())
        os.environ["STAGE_A_SESSION"] = "another"
        try:
            with self.assertRaisesRegex(stage_a.StopCheck, "committed in another session"):
                stage_a.run_supplement_native(self.ctx())
        finally:
            os.environ.pop("STAGE_A_SESSION", None)
        self.assertNotIn(stage_a.SUPP_NAT, self.state()["attempts"])

    def test_corrupt_reference_holds(self):
        self.gates()
        victim = self.a / "passes/00-plain.residuals.npy"
        b = bytearray(victim.read_bytes())
        b[-1] ^= 0xFF
        victim.write_bytes(bytes(b))
        with self.assertRaisesRegex(stage_a.StopCheck, "00-plain.*fails its checksum - hold for diagnosis"):
            stage_a.run_supplement_instrumented(self.ctx())                       # same size: the checksum catches it
        self.assertEqual(self.state()["attempts"], {})                            # before any start
        self.assertTrue((self.s / C.SUPPLEMENT_TERMINAL).exists())


# ---- SupplementController with synthetic workers ---------------------------------------------------------------
OK = {"supplement_gates": "sgates:ok", "supplement_instrumented": "sok:supplement_instrumented:00-plain-os2701",
      "supplement_native": "sok:supplement_native:00-native-os2701", "supplement_receipt": "sreceipt:ok"}
NOSTART = {"supplement_instrumented": "ok:supplement_instrumented", "supplement_native": "ok:supplement_native"}
SOK = {"supplement_instrumented": "sok:supplement_instrumented:00-plain-os2701",
       "supplement_native": "sok:supplement_native:00-native-os2701"}
CARRY = 2338.113973380568
STAGE_A_BYTES = 396783863


def sctl(out: Path, modes: dict, **kw) -> C.SupplementController:
    m = {**OK, **modes}
    return C.SupplementController(out, carry_seconds=CARRY,
                                  worker_cmd=lambda ph: [PY, str(HERE / "fake_worker.py"), str(out), m[ph]],
                                  storage_cap=enforce.CAPS["row20"]["bytes"] - STAGE_A_BYTES,
                                  system_reader=lambda: {"swap": 0, "pressure": 1}, **kw)


class Controller(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp()) / "photo_stage_a_supplement"

    def tearDown(self):
        shutil.rmtree(self.out.parent, ignore_errors=True)

    def test_pass_under_its_own_names(self):
        final = sctl(self.out, {}).run()
        self.assertEqual(final["outcome"], "PASS", final)
        r = json.loads((self.out / "controller.json").read_text())
        self.assertEqual([w["phase"] for w in r["workers"]],
                         ["supplement_gates", "supplement_instrumented", "supplement_native", "supplement_receipt"])
        self.assertEqual(C.final_admitted(self.out, C.SUPPLEMENT_NAMES), final)
        self.assertIsNone(C.final_admitted(self.out))                            # no Stage A final in this tree
        for name in ("STAGE_A_FINAL.json", "GATES.json", "TERMINAL.json", "report"):
            self.assertFalse((self.out / name).exists(), name)
        self.assertGreater(final["seconds_total"], CARRY)                        # row 20's clock continues
        self.assertEqual(final["carry_s"], CARRY)
        self.assertEqual(final["storage_carry_bytes"], STAGE_A_BYTES)
        self.assertEqual(final["row20_storage_final"], final["storage_final"] + STAGE_A_BYTES)
        self.assertTrue(all(final["caps_ok_on_final_figures"].values()))

    def test_work_failure_writes_the_supplement_terminal_and_the_receipt_still_runs(self):
        final = sctl(self.out, {"supplement_instrumented": "exit:1"}).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue((self.out / C.SUPPLEMENT_TERMINAL).exists())
        self.assertFalse((self.out / "TERMINAL.json").exists())
        r = json.loads((self.out / "controller.json").read_text())
        self.assertEqual([w["phase"] for w in r["workers"]][-1], "supplement_receipt")
        self.assertNotIn("supplement_native", [w["phase"] for w in r["workers"]])
        again = sctl(self.out, {}).run()                                          # revision 3: refused, no worker
        self.assertEqual(again["outcome"], "REFUSED")
        self.assertEqual([w for w in json.loads((self.out / "controller.json").read_text())["workers"]
                          if w["session"] == again["session"]], [])

    def test_receipt_failure_modes_prevent_pass(self):
        for mode in ("sreceipt:stopped", "sreceipt:extra_key", "sreceipt:bad_hash", "exit:1"):
            out = Path(tempfile.mkdtemp()) / "s"
            try:
                final = sctl(out, {"supplement_receipt": mode}).run()
                self.assertEqual(final["outcome"], "STOPPED", mode)
                self.assertIsNone(C.final_admitted(out, C.SUPPLEMENT_NAMES)
                                  if final["outcome"] == "PASS" else None)
            finally:
                shutil.rmtree(out.parent, ignore_errors=True)

    def test_supersedes_only_its_own_names(self):
        """With no start evidence, a stray unadmitted supplement final and receipt move aside; a foreign Stage A name
        in the tree is never moved."""
        self.out.mkdir(parents=True)
        (self.out / C.SUPPLEMENT_NAMES["final"]).write_text(json.dumps({"outcome": "STOPPED", "session": "x"}))
        (self.out / "supplement").mkdir()
        (self.out / C.SUPPLEMENT_NAMES["receipt"]).write_text("{}")
        (self.out / "STAGE_A_FINAL.json").write_text("{}")
        (self.out / "controller.json").write_text(json.dumps(
            {"carry_s": CARRY, "seconds_total": CARRY, "sessions": [], "open_session": None, "stops": [],
             "workers": [], "reconciled": [], "swap_baseline": 0,
             "peaks": {"task_lifetime_sum": 0, "phase_aggregates": {}, "storage_bytes": 0, "max_iteration_s": {}}}))
        second = sctl(self.out, {}).run()
        self.assertEqual(second["outcome"], "PASS", second)
        sup = sorted(p.name for p in (self.out / "superseded").iterdir())
        self.assertTrue(any(n.startswith("SUPPLEMENT_FINAL.") for n in sup))
        self.assertTrue(any(n.startswith("SUPPLEMENT_RECEIPT.") for n in sup))
        self.assertFalse(any(n.startswith("STAGE_A_FINAL") for n in sup))
        self.assertTrue((self.out / "STAGE_A_FINAL.json").exists())

    def test_a_pass_is_never_superseded_or_regenerated(self):
        final = sctl(self.out, SOK).run()
        self.assertEqual(final["outcome"], "PASS", final)
        before = (self.out / C.SUPPLEMENT_NAMES["final"]).read_bytes()
        with self.assertRaisesRegex(SystemExit, "already PASSED"):
            sctl(self.out, SOK).run()
        self.assertEqual((self.out / C.SUPPLEMENT_NAMES["final"]).read_bytes(), before)
        self.assertEqual(C.final_admitted(self.out, C.SUPPLEMENT_NAMES), final)

    def test_gates_refusal_and_hold(self):
        f = sctl(self.out, {"supplement_gates": "sgates:refuse"}).run()
        self.assertEqual(f["outcome"], "REFUSED")
        out2 = Path(tempfile.mkdtemp()) / "s"
        try:
            h = sctl(out2, {"supplement_gates": "sgates:hold"}).run()
            self.assertEqual(h["outcome"], "HELD")
            self.assertFalse((out2 / C.SUPPLEMENT_TERMINAL).exists())
        finally:
            shutil.rmtree(out2.parent, ignore_errors=True)

    def test_time_exhausted_spawns_no_work(self):
        c = sctl(self.out, {}, row_cap_s=CARRY + 10.0)
        final = c.run()
        self.assertNotEqual(final["outcome"], "PASS")
        r = json.loads((self.out / "controller.json").read_text())
        self.assertNotIn("supplement_instrumented", [w["phase"] for w in r["workers"]])



class FailOncePeak:
    """memprobe with exit_peak unavailable once, for the first worker that exits after SUPPLEMENT_NATIVE_DONE.json."""

    def __init__(self, out: Path):
        import memprobe
        self.m, self.out, self.fired = memprobe, out, False

    def exit_peak(self, pid):
        if not self.fired and (self.out / "SUPPLEMENT_NATIVE_DONE.json").exists():
            self.fired = True
            raise self.m.Unavailable("fixture: the native exit peak cannot be read")
        return self.m.exit_peak(pid)

    def __getattr__(self, k):
        return getattr(self.m, k)


DRIVER = ("import sys; sys.path.insert(0, {photo!r}); sys.path.insert(0, {tests!r})\n"
          "from pathlib import Path\nimport test_stage_a_supplement as T\n"
          "T.sctl(Path({out!r}), {modes!r}).run()\n")


class Restart(unittest.TestCase):
    """Revision 2 (Codex 478196f P1), no forward: after any start, a STOPPED, held, crashed or interrupted session is
    terminal; a restart dispatches no endpoint, preserves charges, results and the missing-measurement evidence, and
    never regenerates a PASS - even when the first terminal write did not land."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp()) / "photo_stage_a_supplement"

    def tearDown(self):
        shutil.rmtree(self.out.parent, ignore_errors=True)

    def ledger(self) -> dict:
        return json.loads((self.out / "stage_a_state.json").read_text())

    def phases(self, session: str) -> list:
        r = json.loads((self.out / "controller.json").read_text())
        return [w["phase"] for w in r["workers"] if w["session"] == session]

    def restart_stays_stopped(self, started: int, **kw) -> dict:
        """Revision 3: the restart REFUSES before supersede, gates, any worker, receipt or final; results, counters and
        the earlier final/receipt bytes unchanged; the earlier clock carried and this session charged."""
        r0 = json.loads((self.out / "controller.json").read_text())
        keep = {n: (self.out / n).read_bytes() for n in (C.SUPPLEMENT_NAMES["final"], C.SUPPLEMENT_NAMES["receipt"],
                                                           "stage_a_state.json") if (self.out / n).exists()}
        again = sctl(self.out, {**SOK}, **kw).run()
        self.assertEqual(again["outcome"], "REFUSED", again)
        self.assertIn("prior supplement start without an admitted PASS", again["reason"])
        self.assertEqual(self.phases(again["session"]), [])                               # no worker at all
        self.assertEqual({n: (self.out / n).read_bytes() for n in keep}, keep)            # nothing regenerated
        fin = C.final_admitted(self.out, C.SUPPLEMENT_NAMES)
        self.assertTrue(fin is None or fin["outcome"] != "PASS")                          # never a PASS
        self.assertEqual(self.ledger()["counters"]["row20"]["started"], started)
        r1 = json.loads((self.out / "controller.json").read_text())
        self.assertGreater(r1["seconds_total"], r0["seconds_total"])                       # carried and charged
        self.assertEqual(r1["sessions"][-1]["closed"], "refused")
        return again

    def test_receipt_exit_then_restart(self):
        final = sctl(self.out, {**SOK, "supplement_receipt": "exit:1"}).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue((self.out / C.SUPPLEMENT_TERMINAL).exists())                      # terminal at once
        self.restart_stays_stopped(196)

    def test_non_pass_receipt_then_restart(self):
        final = sctl(self.out, {**SOK, "supplement_receipt": "sreceipt:stopped"}).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.restart_stays_stopped(196)

    def test_missing_native_exit_peak_then_restart_even_without_the_terminal(self):
        final = sctl(self.out, SOK, probe=FailOncePeak(self.out)).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue(any("supplement_native" in m for m in final["missing_measurements"]))
        (self.out / C.SUPPLEMENT_TERMINAL).unlink()                                         # the first write "lost"
        self.restart_stays_stopped(196)
        self.assertTrue((self.out / C.SUPPLEMENT_TERMINAL).exists())                      # recorded again

    def test_hold_after_the_instrumented_commit_then_restart(self):
        old = C.GROUP_GONE_S
        C.GROUP_GONE_S = 3.0
        try:
            held = sctl(self.out, {**SOK, "supplement_native": "block"},
                        watchdog_cmd=[PY, str(HERE / "fixture_watchdogs.py"), "retire_early"]).run()
        finally:
            C.GROUP_GONE_S = old
        self.assertEqual(held["outcome"], "HELD", held)
        self.assertTrue((self.out / C.SUPPLEMENT_TERMINAL).exists())                      # a post-start hold stops
        self.assertEqual(self.ledger()["counters"]["row20"]["started"], 195)
        self.restart_stays_stopped(195)

    def test_controller_crash_after_the_instrumented_commit_then_restart(self):
        import signal
        import subprocess
        modes = {**OK, **SOK, "supplement_native": "family"}
        p = subprocess.Popen([PY, "-c", DRIVER.format(photo=str(HERE.parent), tests=str(HERE), out=str(self.out),
                                                      modes=modes)])
        for _ in range(600):
            if (self.out / "grandchild.pid").exists():
                break
            time.sleep(0.05)
        time.sleep(0.3)
        p.send_signal(signal.SIGKILL)
        p.wait()
        self.assertFalse((self.out / C.SUPPLEMENT_TERMINAL).exists())                     # no chance to write it
        gp = int((self.out / "grandchild.pid").read_text())
        for _ in range(200):
            import memprobe
            if memprobe.proc_info(gp) is None:
                break
            time.sleep(0.05)
        self.restart_stays_stopped(195)
        crashed = [x for x in json.loads((self.out / "controller.json").read_text())["sessions"]
                   if x.get("closed") == "crashed"]
        self.assertEqual(len(crashed), 1)                                                 # the dead session charged



class FailingTerminal:
    """Revision 3: make supplement_set_terminal fail BEFORE its rename (nothing lands on disk)."""

    def __enter__(self):
        self.real = C.supplement_set_terminal
        C.supplement_set_terminal = lambda out, phase, reason: (_ for _ in ()).throw(OSError("fixture: pre-rename"))
        return self

    def __exit__(self, *a):
        C.supplement_set_terminal = self.real


class Rev3Adversarial(unittest.TestCase):
    """Revision 3 (Codex 1abb851 P1): every way found to bring a second session to an endpoint, a receipt or a final
    after a start - each refused before any worker, with the terminal write failing where that matters."""

    setUp, tearDown, ledger, phases = Restart.setUp, Restart.tearDown, Restart.ledger, Restart.phases
    restart_stays_stopped = Restart.restart_stays_stopped

    def first_session_completed_endpoints_no_final(self) -> None:
        """Both endpoints and their DONE records committed, then the controller SIGKILLed during the receipt - no
        final, no terminal (the earlier session crashed)."""
        import signal
        import subprocess
        modes = {**OK, **SOK, "supplement_receipt": "block"}
        p = subprocess.Popen([PY, "-c", DRIVER.format(photo=str(HERE.parent), tests=str(HERE), out=str(self.out),
                                                      modes=modes)])
        for _ in range(600):
            r = json.loads((self.out / "controller.json").read_text()) if (self.out / "controller.json").exists() \
                else {}
            if any(w.get("phase") == "supplement_receipt" and w.get("released") for w in r.get("workers", [])):
                break
            time.sleep(0.05)
        time.sleep(0.5)
        p.send_signal(signal.SIGKILL)
        p.wait()
        time.sleep(1.5)                                       # the watchdog ends the orphaned receipt worker
        self.assertFalse((self.out / C.SUPPLEMENT_TERMINAL).exists())
        self.assertTrue((self.out / "SUPPLEMENT_NATIVE_DONE.json").exists())

    def test_crash_with_completed_endpoints_and_a_failing_terminal_write(self):
        self.first_session_completed_endpoints_no_final()
        with FailingTerminal():
            again = self.restart_stays_stopped(196)
        self.assertIn("could not be written", again["reason"])
        self.assertFalse((self.out / C.SUPPLEMENT_TERMINAL).exists())                     # still refused without it

    def test_receipt_failure_then_lost_terminal_and_a_failing_rewrite(self):
        sctl(self.out, {**SOK, "supplement_receipt": "exit:1"}).run()
        (self.out / C.SUPPLEMENT_TERMINAL).unlink()
        with FailingTerminal():
            self.restart_stays_stopped(196)

    def test_ledger_deleted_done_records_remain(self):
        self.first_session_completed_endpoints_no_final()
        (self.out / "stage_a_state.json").unlink()
        with FailingTerminal():
            again = sctl(self.out, SOK).run()
        self.assertEqual(again["outcome"], "REFUSED")
        self.assertIn("SUPPLEMENT_NATIVE_DONE.json", again["reason"])

    def test_ledger_and_done_records_deleted_controller_record_remains(self):
        self.first_session_completed_endpoints_no_final()
        for n in ("stage_a_state.json", "SUPPLEMENT_INSTRUMENTED_DONE.json", "SUPPLEMENT_NATIVE_DONE.json"):
            (self.out / n).unlink()
        with FailingTerminal():
            again = sctl(self.out, SOK).run()
        self.assertEqual(again["outcome"], "REFUSED")
        self.assertIn("a durable endpoint worker record", again["reason"])
        self.assertEqual(self.phases(again["session"]), [])

    def test_unreadable_ledger(self):
        self.first_session_completed_endpoints_no_final()
        (self.out / "stage_a_state.json").write_text("{not json")
        with FailingTerminal():
            again = sctl(self.out, SOK).run()
        self.assertEqual(again["outcome"], "REFUSED")
        self.assertIn("unreadable ledger", again["reason"])

    def test_final_without_its_marker_or_with_an_abort(self):
        final = sctl(self.out, SOK).run()
        self.assertEqual(final["outcome"], "PASS")
        (self.out / C.SUPPLEMENT_NAMES["admitted"]).unlink()                                # a crash before the marker
        with FailingTerminal():
            self.restart_stays_stopped(196)
        out2 = Path(tempfile.mkdtemp()) / "s"
        try:
            self.out = out2
            sctl(out2, SOK).run()
            (out2 / C.SUPPLEMENT_NAMES["aborted"]).write_text(json.dumps(
                {"session": json.loads((out2 / C.SUPPLEMENT_NAMES["final"]).read_text())["session"]}))
            with FailingTerminal():
                self.restart_stays_stopped(196)                                           # an aborted PASS is no PASS
        finally:
            shutil.rmtree(out2.parent, ignore_errors=True)

    def test_without_gates_no_worker_is_spawned(self):
        sctl(self.out, {**SOK, "supplement_receipt": "exit:1"}).run()
        with self.assertRaisesRegex(SystemExit, "prior supplement start"):
            sctl(self.out, SOK, gates=False).run()
        r = json.loads((self.out / "controller.json").read_text())
        self.assertFalse(any(w["phase"] in ("supplement_instrumented", "supplement_native", "supplement_receipt")
                             for w in r["workers"][-1:] if w.get("session") not in
                             {x.get("session") for x in r["sessions"]}))                    # nothing new spawned
        self.assertEqual(self.ledger()["counters"]["row20"]["started"], 196)

    def test_a_pass_needs_both_endpoints_from_this_session(self):
        c = sctl(self.out, SOK)
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "stage_a_state.json").write_text(json.dumps({"completed": {
            "00-plain-os2701": {"session": "earlier"}, "00-native-os2701": {"session": c.session}}}))
        self.assertFalse(c._endpoints_this_session())
        (self.out / "stage_a_state.json").write_text(json.dumps({"completed": {
            "00-plain-os2701": {"session": c.session}, "00-native-os2701": {"session": c.session}}}))
        self.assertTrue(c._endpoints_this_session())



def _sleeper() -> "subprocess.Popen":
    import subprocess
    return subprocess.Popen([PY, "-c", "import time; time.sleep(600)"], start_new_session=True)


class Rev4ReleaseEvidence(unittest.TestCase):
    """Revision 4 (Codex 410b580 P2), no forward: the base _phase persists an endpoint record with released=False BEFORE
    it sends GO and marks it released only after; a crash in between leaves an ambiguous record. Any durable endpoint
    record is start evidence; the pre-persist boundary (no record) is not."""

    setUp, tearDown, ledger, phases = Restart.setUp, Restart.tearDown, Restart.ledger, Restart.phases

    def crashed_at_the_release_boundary(self, leader_alive: bool) -> dict:
        """A dead controller's open session whose last durable record is an endpoint worker with released=False and
        a valid leader/watchdog identity - GO possibly delivered, no ledger attempt, DONE, pass, comparison or terminal."""
        import memprobe
        self.out.mkdir(parents=True)
        worker, wd = _sleeper(), _sleeper()
        time.sleep(0.2)
        self.procs = [worker, wd]
        li, wi = memprobe.proc_info(worker.pid), memprobe.proc_info(wd.pid)
        if not leader_alive:
            worker.kill()
            worker.wait()
        rec = {"carry_s": CARRY, "seconds_total": CARRY + 30.0, "stops": [], "reconciled": [], "swap_baseline": 0,
               "sessions": [], "peaks": {"task_lifetime_sum": 0, "phase_aggregates": {}, "storage_bytes": 0,
                                         "max_iteration_s": {}},
               "workers": [{"phase": "supplement_gates", "session": "dead", "released": True, "reaped": True,
                            "returncode": 0, "exit_peak": 1 << 20, "members": {}, "member_max": {}},
                           {"phase": "supplement_instrumented", "session": "dead", "released": False, "members": {},
                            "member_max": {}, "leader": li, "watchdog": wi, "spawned_total_s": 20.0}],
               "open_session": {"session": "dead", "pid": 1, "live_s": 25.0, "opened_wall": time.time() - 30,
                                "beat_wall": time.time() - 2}}
        (self.out / "controller.json").write_text(json.dumps(rec))
        return rec

    def tearDown_procs(self):
        for p in getattr(self, "procs", []):
            if p.poll() is None:
                p.kill()
                p.wait()

    def assert_refused_and_reconciled(self, started_before):
        try:
            again = sctl(self.out, SOK).run()
        finally:
            self.tearDown_procs()
        self.assertEqual(again["outcome"], "REFUSED", again)
        self.assertIn("a durable endpoint worker record", again["reason"])
        self.assertEqual(self.phases(again["session"]), [])                               # no worker of any phase
        r = json.loads((self.out / "controller.json").read_text())
        crashed = [x for x in r["sessions"] if x.get("closed") == "crashed"]
        self.assertEqual(len(crashed), 1)                                                 # the dead session charged
        self.assertGreater(r["seconds_total"], started_before)
        self.assertEqual(r["sessions"][-1]["closed"], "refused")
        self.assertFalse((self.out / "stage_a_state.json").exists())                      # nothing started anew
        for name in (C.SUPPLEMENT_NAMES["final"], C.SUPPLEMENT_NAMES["receipt"]):
            self.assertFalse((self.out / name).exists())                                  # nothing generated
        return again

    def test_crash_after_go_before_the_released_snapshot_live_worker(self):
        rec = self.crashed_at_the_release_boundary(leader_alive=True)
        self.assert_refused_and_reconciled(rec["seconds_total"])
        import memprobe
        self.assertIsNone(memprobe.proc_info(self.procs[0].pid))                          # reconciled (killed)

    def test_crash_after_go_before_the_released_snapshot_dead_worker(self):
        rec = self.crashed_at_the_release_boundary(leader_alive=False)
        self.assert_refused_and_reconciled(rec["seconds_total"])

    def test_the_boundary_before_the_endpoint_record_is_not_a_start(self):
        """Control: a dead session whose last durable record is the GATES worker (no endpoint record persisted, so no
        GO can have been sent) - the restart is not refused and runs to PASS."""
        self.out.mkdir(parents=True)
        rec = {"carry_s": CARRY, "seconds_total": CARRY + 10.0, "stops": [], "reconciled": [], "swap_baseline": 0,
               "sessions": [], "peaks": {"task_lifetime_sum": 0, "phase_aggregates": {}, "storage_bytes": 0,
                                         "max_iteration_s": {}},
               "workers": [{"phase": "supplement_gates", "session": "dead", "released": True, "reaped": True,
                            "returncode": 0, "exit_peak": 1 << 20, "members": {}, "member_max": {}}],
               "open_session": {"session": "dead", "pid": 1, "live_s": 8.0, "opened_wall": time.time() - 10,
                                "beat_wall": time.time() - 2}}
        (self.out / "controller.json").write_text(json.dumps(rec))
        final = sctl(self.out, SOK).run()
        self.assertEqual(final["outcome"], "PASS", final)

    def test_an_unreleased_endpoint_record_needs_its_exit_peak(self):
        c = sctl(self.out, SOK)
        c.rec = {"workers": [{"phase": "supplement_native", "session": "x", "released": False}],
                 "peaks": {"controller_final": 1, "guardian_final": 1}}
        self.assertTrue(any("supplement_native" in m for m in c._missing_measurements()))

    def isolated_history(self, make) -> dict:
        self.out.mkdir(parents=True)
        (self.out / "controller.json").write_text(json.dumps(
            {"carry_s": CARRY, "seconds_total": CARRY, "sessions": [], "open_session": None, "stops": [],
             "workers": [], "reconciled": [], "swap_baseline": 0,
             "peaks": {"task_lifetime_sum": 0, "phase_aggregates": {}, "storage_bytes": 0, "max_iteration_s": {}}}))
        make()
        with FailingTerminal():
            again = sctl(self.out, SOK).run()
        self.assertEqual(again["outcome"], "REFUSED", again)
        self.assertEqual(self.phases(again["session"]), [])
        self.assertFalse((self.out / C.SUPPLEMENT_NAMES["final"]).exists())
        return again

    def test_pass_output_only(self):
        def make():
            (self.out / "passes").mkdir()
            (self.out / "passes" / "00-plain-os2701.json").write_text("{}")
        self.assertIn("pass outputs", self.isolated_history(make)["reason"])

    def test_comparison_receipt_only(self):
        def make():
            (self.out / "supplement").mkdir()
            (self.out / "supplement" / "comparison_a.json").write_text("{}")
        self.assertIn("comparison receipts", self.isolated_history(make)["reason"])

    def test_terminal_record_only(self):
        def make():
            C.supplement_set_terminal(self.out, "controller", "fixture")
        self.assertIn(C.SUPPLEMENT_TERMINAL, self.isolated_history(make)["reason"])


if __name__ == "__main__":
    unittest.main()
