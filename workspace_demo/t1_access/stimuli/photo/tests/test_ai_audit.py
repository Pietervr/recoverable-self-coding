"""Image-audit mechanism tests (AI_AUDIT_JOB.md, revision 2): the reviewed reader Job driven by the audit subclass on a
labelled synthetic set with the fake CLI - no network, no model, no development image is sent anywhere.

Revision 2 (Codex 1b17d64): the chain fixtures run the REAL admission path up to the send boundary - AuditJob(k).run()
admits the chain (committed bytes in a real temporary git repository, re-scoring by `ai_audit_score.verify_result`,
the real `admit_clock` on the predecessor's own closed clock) before the clock opens and again inside admission; a
refusal is asserted to dispatch nothing, open no clock and create no job directory.

    .venv-image/bin/python -m unittest stimuli/photo/tests/test_ai_audit.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PHOTO = TESTS.parent
sys.path.insert(0, str(PHOTO))
sys.path.insert(0, str(TESTS))
import ai_audit_exec as A  # noqa: E402
import ai_audit_score as SC  # noqa: E402
import ai_audit_set as S  # noqa: E402
import ai_reader_exec as E  # noqa: E402
import ai_reader_journal as J  # noqa: E402
import ai_reader_runtime as R  # noqa: E402
from airq_fixture import READER, png  # noqa: E402

PROMPTS = {"name": "name it", "photograph": "photo?", "sense": 'sense of "{c}"?', "distinct": "distinct?"}
CONCEPTS = (("crow", True), ("pig", False))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(root: Path, *args) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def build(root: Path, plan: dict, *, k: int = 1, rank: int = 1, wrong_prompt_for: str | None = None,
          primaries: bool = True, only: tuple = ("crow", "pig")) -> dict:
    """Round k of a two-concept synthetic audit (crow: a Stage A primary; pig: not): primaries (round 1 only) and each
    concept's rank-`rank` candidate with its pair. Item ids carry the round so rounds never share ids."""
    rd = root / f"r{k}"
    for d in ("images", "attempts"):
        (rd / d).mkdir(parents=True, exist_ok=True)
    (root / "jobs").mkdir(exist_ok=True)
    key, requests = {"items": {}}, []
    for n, (concept, stage_a) in enumerate(CONCEPTS):
        if concept not in only:
            continue
        pid, cid, prid = f"p{n}", f"c{n}k{k}", f"x{n}k{k}"
        common = {"concept": concept, "family": "animals", "role": "DEV-CAL", "synset": "s", "definition": "d"}
        key["items"][pid] = {**common, "kind": "primary", "stage_a_primary_view": stage_a, "png_sha256": "0" * 64,
                             "human": {"recognizability": 0.9, "n_ratings": 12, "n_correct": 11}}
        key["items"][cid] = {**common, "kind": "candidate", "rank": rank, "title": "t", "page_url": "u",
                             "licence_statement": "CC0", "source_sha256": "0" * 64, "commons_original_sha1": "0",
                             "png_sha256": "0" * 64, "pair": prid}
        key["items"][prid] = {"concept": concept, "kind": "pair", "primary": pid, "candidate": cid,
                              "png_sha256": "0" * 64}
        rows = [(cid, "second", ("name", "photograph", "sense"), 20 + n + 10 * k), (prid, "pair", ("distinct",),
                                                                                   30 + n + 10 * k)]
        if primaries:
            rows.insert(0, (pid, "primary", ("name", "photograph", "sense"), 10 + n))
        else:
            del key["items"][pid]
        for item, view, qs, v in rows:
            data = png(v)
            (rd / "images" / f"{item}.png").write_bytes(data)
            for q in qs:
                requests.append({"request": f"{item}{q[0]}", "item": item, "view": view, "question": q,
                                 "file": f"{item}.png", "sha256": sha(data), "bytes": len(data),
                                 "prompt": PROMPTS[q].format(c=concept)})
    order = [r["request"] for q in S.QUESTION_ORDER for r in requests if r["question"] == q]
    sset = {"requests": requests, "delivery_order": order, "reader": READER, "prompt": PROMPTS["name"]}
    codex = [sys.executable, str(TESTS / "fake_codex.py")]
    per, instr = {}, set()
    for i, r in enumerate(requests):
        adir = rd / "probe" / f"r{i}" / "a"
        img = R.prepare(adir, (rd / "images" / r["file"]).read_bytes(), r["file"])
        prompt = "a different prompt" if r["request"] == wrong_prompt_for else r["prompt"]
        rc = R.prompt_input(codex, READER, adir, img, prompt, sandbox=False)
        instr.add(rc["instructions_sha256"])
        im = rc["images"][0]
        per[r["request"]] = {"image_sha256": im["sha256"], "user_text_sha256": rc["user_text_sha256"],
                             "bytes": im["bytes"], "detail": im["detail"], "file_sha256": r["sha256"],
                             "reencoded": im["sha256"] != r["sha256"], "prompt_rendered": True,
                             "prompt_sha256": sha(r["prompt"].encode())}
    shutil.rmtree(rd / "probe", ignore_errors=True)
    (rd / "fake_plan.json").write_text(json.dumps(plan))
    return {"sset": sset, "delivery": {"instructions_sha256": instr.pop(), "requests": per}, "key": key}


def fx_for(root: Path, k: int, b: dict) -> dict:
    rd = root / f"r{k}"
    return {"codex": [sys.executable, str(TESTS / "fake_codex.py")], "images": rd / "images",
            "job": root / "jobs" / f"ai_audit_job_r{k}", "raw": rd / "raw.jsonl", "attempts": rd / "attempts",
            "sset": b["sset"], "delivery": b["delivery"], "package": {"package_digest": "f" * 64}}


def fake_name(concept, answer, status, overlength):
    code = "OK_WHOLE" if status == "ok" and (answer or "").strip().lower() == concept else "ERR_NONMATCH"
    return {"code": code, "pass_name": code == "OK_WHOLE", "rule": "whole" if code == "OK_WHOLE" else None}


class World:
    """A synthetic audit world under `root` (a git repository): builds, chains, scores and commits rounds."""

    def __init__(self, root: Path, builds: dict):
        self.root, self.builds = root, builds

    def score_file(self, j: int) -> Path:
        return self.root / f"r{j}" / "score.json"

    def score_fx(self, j: int) -> dict:
        b = self.builds[j]
        return {"raw": self.root / f"r{j}" / "raw.jsonl", "sset": b["sset"], "delivery": b["delivery"],
                "key": b["key"], "job": self.root / "jobs" / f"ai_audit_job_r{j}", "chain": self.chain(),
                "available_ranks": {"crow": [1, 2], "pig": [1, 2]}}

    def verify(self, j: int) -> dict:
        return SC.verify_result(j, allow_synthetic=True, fixture=self.score_fx(j), name_score=fake_name,
                                score_file=self.score_file(j))

    def chain(self, mode: str = "synthetic-fixture") -> A.Chain:
        from ai_reader_score import committed
        return A.Chain(verify=self.verify, committed=committed, raw_path=lambda j: self.root / f"r{j}" / "raw.jsonl",
                       score_path=self.score_file, job_root=self.root / "jobs", mode=mode)

    def run(self, k: int) -> dict:
        return A.AuditJob(k, fx_for(self.root, k, self.builds[k]), chain=self.chain()).run()

    def score_and_commit(self, j: int) -> dict:
        out = SC.score(j, allow_synthetic=True, fixture=self.score_fx(j), name_score=fake_name)
        self.score_file(j).write_bytes(SC.serialise(out))
        git(self.root, "add", f"r{j}/raw.jsonl", f"r{j}/score.json")
        git(self.root, "commit", "-q", "-m", f"round {j}")
        return out


def dispatched(rd: Path) -> list[str]:
    log = rd / "dispatch_log.jsonl"
    return [json.loads(x)["request"] for x in log.read_text().splitlines()] if log.exists() else []


PLAN1 = {"p0": ["ok:crow", "ok:Yes", "ok:yes."], "p1": ["ok:pig", "ok:yes", "ok:yes"],
         "c0k1": ["ok:crow", "ok:yes", "ok:YES"], "x0k1": ["ok:yes"],
         "c1k1": ["ok:pig", "ok:no", "ok:yes"], "x1k1": ["ok:yes"]}          # pig's rank-1 candidate fails
PLAN2 = {"c1k2": ["ok:pig", "ok:yes", "ok:yes"], "x1k2": ["ok:yes"]}


class ChainBase(unittest.TestCase):
    TEMPLATE: Path | None = None
    BUILDS: dict = {}

    @classmethod
    def setUpClass(cls):
        cls._lim, cls._total = dict(E.LIMITS), dict(A.TOTAL)
        cls.TEMPLATE = Path(tempfile.mkdtemp())
        git(cls.TEMPLATE, "init", "-q")
        git(cls.TEMPLATE, "config", "user.email", "t@t")
        git(cls.TEMPLATE, "config", "user.name", "t")
        b1 = build(cls.TEMPLATE, PLAN1, k=1)
        w = World(cls.TEMPLATE, {1: b1})
        res = w.run(1)
        assert res["outcome"] == "COMPLETE", res
        cls.SCORE1 = w.score_and_commit(1)
        cls.BUILDS = {1: b1}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEMPLATE, ignore_errors=True)

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "w"
        shutil.copytree(self.TEMPLATE, self.root, symlinks=True)
        b2 = build(self.root, PLAN2, k=2, rank=2, primaries=False, only=("pig",))
        self.w = World(self.root, {**self.BUILDS, 2: b2})

    def tearDown(self):
        E.LIMITS.clear()
        E.LIMITS.update(self._lim)
        A.TOTAL.clear()
        A.TOTAL.update(self._total)
        shutil.rmtree(self.root.parent, ignore_errors=True)

    def assert_refused_unsent(self, k: int, why: str):
        with self.assertRaises(SystemExit) as cm:
            self.w.run(k)
        self.assertIn(why, str(cm.exception.code))
        self.assertEqual(dispatched(self.root / f"r{k}"), [])
        self.assertFalse((self.root / "jobs" / f"ai_audit_job_r{k}").exists(), "a refused round opened no clock")


class Round1(ChainBase):
    def test_round1_outcomes_and_dispositions(self):
        out = self.SCORE1
        self.assertEqual(out["second_views"]["crow"]["status"], "selected")
        self.assertEqual(out["second_views"]["pig"]["status"], "next")
        self.assertEqual([r["item"] for r in out["candidates_failed_listed_for_owner"]], ["c1k1"])
        self.assertEqual(out["charged"]["attempts"], 14)
        self.assertNotIn("seconds", out["charged"])
        self.assertIn("first use on unseen candidate images", out["reader_scope"])

    def test_per_request_prompt_receipts(self):
        recs, _ = J.read(self.root / "r1" / "raw.jsonl")
        begins = [r for r in recs if r["t"] == "begin"]
        self.assertEqual(len(begins), 14)
        for r in begins:
            self.assertEqual(r["receipt"]["user_text_sha256"],
                             self.BUILDS[1]["delivery"]["requests"][r["request"]]["user_text_sha256"])
        self.assertGreater(len({r["receipt"]["user_text_sha256"] for r in begins}), 4)

    def test_verify_reproduces_the_committed_score(self):
        v = self.w.verify(1)
        self.assertEqual((v["round"], v["attempts"]), (1, 14))
        self.assertGreater(v["seconds"], 0.0)

    def test_ended_round_is_not_reopened(self):
        clock = (self.root / "jobs" / "ai_audit_job_r1" / "clock.json").read_bytes()
        with self.assertRaises(SystemExit) as cm:
            self.w.run(1)
        self.assertIn("nothing runs after a receipt", str(cm.exception.code))
        self.assertEqual((self.root / "jobs" / "ai_audit_job_r1" / "clock.json").read_bytes(), clock)


class RoundNumbers(ChainBase):
    def test_nonpositive_and_invalid_rounds_never_reach_a_dispatch(self):
        for k in (0, -1, -3, True, 9, 1.0, "1"):
            with self.subTest(k=k):
                with self.assertRaises(SystemExit):
                    A.AuditJob(k, fx_for(self.root, 2, self.w.builds[2]), chain=self.w.chain()).run()
                with self.assertRaises(SystemExit):
                    self.w.chain().admit(k)
                with self.assertRaises(SystemExit):
                    A.configure(k, chain=self.w.chain(), fixture=fx_for(self.root, 2, self.w.builds[2]))
                with self.assertRaises(SystemExit):
                    S.derive(k)
        self.assertEqual(dispatched(self.root / "r2"), [])
        self.assertEqual(sorted(p.name for p in (self.root / "jobs").iterdir()), ["ai_audit_job_r1"])


class LaterRounds(ChainBase):
    def test_honest_round2_runs_with_the_carried_envelope(self):
        res = self.w.run(2)
        self.assertEqual(res["outcome"], "COMPLETE")
        self.assertEqual(E.LIMITS["max_attempts"], 5)               # ceil(1.1 x 4) with 400 - 14 attempts left
        self.assertLess(E.LIMITS["job_clock_s"], A.TOTAL["job_clock_s"])
        self.assertEqual(sorted(set(dispatched(self.root / "r2"))), ["c1k2", "x1k2"])

    def _edit_score(self, fn):
        p = self.w.score_file(1)
        d = json.loads(p.read_text())
        fn(d)
        p.write_bytes(SC.serialise(d))
        git(self.root, "commit", "-q", "-am", "edited")

    def test_changed_charges_refuse(self):
        self._edit_score(lambda d: d["charged"].__setitem__("attempts", 0))
        self.assert_refused_unsent(2, "not what its admitted evidence scores to")

    def test_changed_outcomes_refuse(self):
        self._edit_score(lambda d: d["second_views"]["pig"].__setitem__("status", "selected"))
        self.assert_refused_unsent(2, "not what its admitted evidence scores to")

    def test_uncommitted_score_refuses(self):
        p = self.w.score_file(1)
        p.write_text(p.read_text().replace('"next"', '"selected"'))
        self.assert_refused_unsent(2, "commit")

    def test_synthetic_predecessor_never_enters_a_scientific_chain(self):
        with self.assertRaises(SystemExit) as cm:
            self.w.chain(mode="scientific").admit(2)
        self.assertIn("not a scientific result", str(cm.exception.code))

    def test_changed_prior_clock_refuses(self):
        cp = self.root / "jobs" / "ai_audit_job_r1" / "clock.json"
        c = json.loads(cp.read_text())
        c["seconds_total"] = float(c["seconds_total"]) + 100.0
        cp.write_text(json.dumps(c))
        self.assert_refused_unsent(2, "no closure marker for this journal and clock")

    def test_stopped_predecessor_holds(self):
        recs, _ = J.read(self.root / "r1" / "raw.jsonl")
        last = recs[-1]
        self.assertEqual(last["outcome"], "COMPLETE")
        raw = self.root / "r1" / "raw.jsonl"
        raw.write_text(raw.read_text().replace('"outcome": "COMPLETE"', '"outcome": "STOPPED"'))
        git(self.root, "commit", "-q", "-am", "stopped")
        self.assert_refused_unsent(2, "the job did not complete")

    def test_cumulative_attempt_exhaustion(self):
        A.TOTAL["max_attempts"] = 17                                 # 14 charged: 3 left for 4 planned requests
        self.assert_refused_unsent(2, "audit attempts left")
        A.TOTAL["max_attempts"] = 14                                 # nothing left at all
        self.assert_refused_unsent(2, "envelope is exhausted")

    def test_cumulative_time_exhaustion(self):
        A.TOTAL["job_clock_s"] = self.w.verify(1)["seconds"] + 10.0
        self.assert_refused_unsent(2, "envelope is exhausted")

    def test_stray_job_directory_refuses(self):
        (self.root / "jobs" / "ai_audit_job_r5").mkdir()
        self.assert_refused_unsent(2, "outside 1..2")

    def test_round3_needs_round2(self):
        b3 = build(self.root, PLAN2, k=3, rank=3, primaries=False, only=("pig",))
        self.w.builds[3] = b3
        self.assert_refused_unsent(3, "commit the raw responses before scoring")


class WrongPrompt(unittest.TestCase):
    def test_wrong_frozen_prompt_sends_nothing_for_that_request(self):
        root = Path(tempfile.mkdtemp())
        lim = dict(E.LIMITS)
        try:
            git(root, "init", "-q")
            b = build(root, PLAN1, k=1, wrong_prompt_for="p0p")
            res = World(root, {1: b}).run(1)
            self.assertEqual(res["outcome"], "STOPPED")
            self.assertIn("prompt-input receipt for p0p differs", res["reason"])
            self.assertEqual(dispatched(root / "r1").count("p0"), 1)   # the name went; the photograph was never sent
        finally:
            E.LIMITS.clear()
            E.LIMITS.update(lim)
            shutil.rmtree(root, ignore_errors=True)


class Pure(unittest.TestCase):
    def test_yes_no(self):
        self.assertEqual(SC.yes_no(" Yes. ", "ok", False), "YES")
        self.assertEqual(SC.yes_no("unsure", "ok", False), "UNSURE")
        self.assertEqual(SC.yes_no("yes, it is", "ok", False), "ERR_MALFORMED")
        self.assertEqual(SC.yes_no("yes", "ok", True), "ERR_OVERLENGTH")
        self.assertEqual(SC.yes_no(None, "interrupted", False), "ERR_INTERRUPTED")
        self.assertEqual(SC.yes_no(None, "no_response", False), "ERR_NO_RESPONSE")

    def test_scientific_scoring_refuses_injection(self):
        with self.assertRaises(SystemExit):
            SC.admit(1, allow_synthetic=False, fixture={"raw": Path("/nonexistent")})
        with self.assertRaises(SystemExit):
            SC.verify_result(1, fixture={"raw": Path("/nonexistent")})

    def test_strict_charge_types(self):
        for bad in (-1, 1.5, True, None, "3"):
            with self.assertRaises(SystemExit):
                A._count(bad, "x")
        for bad in (-0.1, float("nan"), float("inf"), True, None, "1"):
            with self.assertRaises(SystemExit):
                A._secs(bad, "x")
        self.assertEqual(A._secs(3, "x"), 3.0)

    def test_check_delivery(self):
        sset = {"requests": [{"request": "a", "sha256": "1" * 64, "prompt": "p"}]}
        good = {"instructions_sha256": "i", "requests": {"a": {"file_sha256": "1" * 64, "image_sha256": "1" * 64,
                                                                "reencoded": False, "prompt_rendered": True,
                                                                "prompt_sha256": sha(b"p")}}}
        A.check_delivery(sset, good, "i")
        for bad in ({**good, "instructions_sha256": "j"},
                    {**good, "requests": {"a": {**good["requests"]["a"], "prompt_sha256": sha(b"q")}}},
                    {**good, "requests": {"a": {**good["requests"]["a"], "image_sha256": "2" * 64}}},
                    {**good, "requests": {"a": {**good["requests"]["a"], "prompt_rendered": False}}},
                    {**good, "requests": {}}):
            with self.assertRaises(SystemExit):
                A.check_delivery(sset, bad, "i")


def _items(*rows):
    return {"items": {i: {"concept": c, "kind": kind, "rank": rank, "passed_by_reader": ok}
                      for i, c, kind, rank, ok in rows}}


class Resolve(unittest.TestCase):
    D = {"date": "2026-10-05", "by": "owner", "evidence": "picture and raw answers"}

    def test_owner_pass_of_an_earlier_candidate_supersedes_the_mechanical_selection(self):
        scores = {1: _items(("p", "pig", "primary", None, True), ("c1", "pig", "candidate", 1, False)),
                  2: _items(("c2", "pig", "candidate", 2, True))}
        r = SC.resolve(scores, {"items": {"c1": {"decision": "pass", **self.D}}})["pig"]
        self.assertEqual(r["second_view_kept"]["item"], "c1")
        self.assertEqual(r["second_view_kept"]["reader"], "fail")      # never relabelled a reader pass
        self.assertEqual(r["second_view_kept"]["decided_by"], "owner")
        self.assertEqual([(x["item"], x["superseded_by"]) for x in r["superseded"]], [("c2", "c1")])
        self.assertEqual(r["per_image_check"], "c1")

    def test_without_a_decision_the_mechanical_selection_stands_and_failures_are_pending(self):
        scores = {1: _items(("p", "pig", "primary", None, False), ("c1", "pig", "candidate", 1, False)),
                  2: _items(("c2", "pig", "candidate", 2, True))}
        r = SC.resolve(scores, {})["pig"]
        self.assertEqual(r["second_view_kept"]["item"], "c2")
        self.assertEqual([x["item"] for x in r["failed_candidates_pending_owner"]], ["c1"])
        self.assertEqual(r["primary"]["status"], "pending_owner")

    def test_owner_fail_keeps_nothing_and_decisions_must_be_dated(self):
        scores = {1: _items(("p", "pig", "primary", None, False), ("c1", "pig", "candidate", 1, False))}
        r = SC.resolve(scores, {"items": {"c1": {"decision": "fail_hold", **self.D},
                                          "p": {"decision": "fail_replace", **self.D}}})["pig"]
        self.assertIsNone(r["second_view_kept"])
        self.assertEqual(r["primary"]["status"], "fail_replace")
        with self.assertRaises(SystemExit):
            SC.resolve(scores, {"items": {"c1": {"decision": "pass"}}})
        with self.assertRaises(SystemExit):
            SC.resolve(scores, {"items": {"c1": {"decision": "maybe", **self.D}}})


if __name__ == "__main__":
    unittest.main()
