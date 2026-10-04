"""Image-audit mechanism tests (AI_AUDIT_JOB.md): the reviewed reader Job driven by the audit subclass on a labelled
synthetic set with the fake CLI - no network, no model, no development image is sent anywhere.

    .venv-image/bin/python -m unittest stimuli/photo/tests/test_ai_audit.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
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


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build(root: Path, plan: dict, *, wrong_prompt_for: str | None = None) -> dict:
    """Two concepts (crow: a Stage A primary; pig: not), each a primary and one candidate, plus the pairs."""
    root.mkdir(parents=True, exist_ok=True)
    for d in ("images", "attempts"):
        (root / d).mkdir(exist_ok=True)
    key, requests = {"items": {}}, []
    names = []
    for n, (concept, stage_a) in enumerate((("crow", True), ("pig", False))):
        pid, cid, prid = f"p{n}", f"c{n}", f"x{n}"
        key["items"][pid] = {"concept": concept, "kind": "primary", "family": "animals", "role": "DEV-CAL",
                             "stage_a_primary_view": stage_a, "synset": "s", "definition": "d", "png_sha256": "0" * 64}
        key["items"][cid] = {"concept": concept, "kind": "candidate", "rank": 1, "title": "t", "page_url": "u",
                             "licence_statement": "CC0", "family": "animals", "role": "DEV-CAL", "synset": "s",
                             "definition": "d", "original_sha256": "0" * 64, "png_sha256": "0" * 64, "pair": prid}
        key["items"][prid] = {"concept": concept, "kind": "pair", "primary": pid, "candidate": cid,
                              "png_sha256": "0" * 64}
        for item, view, qs, v in ((pid, "primary", ("name", "photograph", "sense"), 10 + n),
                                  (cid, "second", ("name", "photograph", "sense"), 20 + n),
                                  (prid, "pair", ("distinct",), 30 + n)):
            data = png(v)
            (root / "images" / f"{item}.png").write_bytes(data)
            for q in qs:
                requests.append({"request": f"{item}{q[0]}", "item": item, "view": view, "question": q,
                                 "file": f"{item}.png", "sha256": sha(data), "bytes": len(data),
                                 "prompt": PROMPTS[q].format(c=concept)})
        names.append(concept)
    order = [r["request"] for q in S.QUESTION_ORDER for r in requests if r["question"] == q]
    sset = {"requests": requests, "delivery_order": order, "reader": READER, "prompt": PROMPTS["name"]}
    codex = [sys.executable, str(TESTS / "fake_codex.py")]
    per, instr = {}, set()
    for i, r in enumerate(requests):
        adir = root / "probe" / f"r{i}" / "a"
        img = R.prepare(adir, (root / "images" / r["file"]).read_bytes(), r["file"])
        prompt = "a different prompt" if r["request"] == wrong_prompt_for else r["prompt"]
        rc = R.prompt_input(codex, READER, adir, img, prompt, sandbox=False)
        instr.add(rc["instructions_sha256"])
        im = rc["images"][0]
        per[r["request"]] = {"image_sha256": im["sha256"], "user_text_sha256": rc["user_text_sha256"],
                             "bytes": im["bytes"], "detail": im["detail"], "file_sha256": r["sha256"],
                             "reencoded": im["sha256"] != r["sha256"], "prompt_rendered": True,
                             "prompt_sha256": sha(r["prompt"].encode())}
    shutil.rmtree(root / "probe", ignore_errors=True)
    delivery = {"instructions_sha256": instr.pop(), "requests": per}
    (root / "fake_plan.json").write_text(json.dumps(plan))
    fx = {"codex": codex, "images": root / "images", "job": root / "job", "raw": root / "raw.jsonl",
          "attempts": root / "attempts", "sset": sset, "delivery": delivery, "package": {"package_digest": "f" * 64}}
    return {"fixture": fx, "key": key, "sset": sset, "delivery": delivery}


def fixture_limits(n: int) -> dict:
    return {"planned": n, "max_attempts": n + 2, "job_clock_s": 600.0, **A.PER_ROUND}


def fake_name(concept, answer, status, overlength):
    code = "OK_WHOLE" if status == "ok" and (answer or "").strip().lower() == concept else "ERR_NONMATCH"
    return {"code": code, "pass_name": code == "OK_WHOLE", "rule": "whole" if code == "OK_WHOLE" else None}


class AuditJobFixture(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        self._lim = E.LIMITS

    def tearDown(self):
        E.LIMITS = self._lim
        shutil.rmtree(self.td, ignore_errors=True)

    def plan_all_pass(self) -> dict:
        p = {}
        for n, c in enumerate(("crow", "pig")):
            p[f"p{n}"] = [f"ok:{c}", "ok:Yes", "ok:yes."]
            p[f"c{n}"] = [f"ok:{c}", "ok:yes", "ok:YES"]
            p[f"x{n}"] = ["ok:yes"]
        return p

    def run_job(self, b: dict) -> dict:
        E.LIMITS = fixture_limits(len(b["sset"]["requests"]))
        return A.AuditJob(1, b["fixture"]).run()

    def test_per_request_prompts_complete(self):
        b = build(self.td, self.plan_all_pass())
        res = self.run_job(b)
        self.assertEqual(res["outcome"], "COMPLETE")
        recs, _ = J.read(b["fixture"]["raw"])
        begins = [r for r in recs if r["t"] == "begin"]
        self.assertEqual(len(begins), 14)
        # each attempt's live receipt carried its OWN request's frozen user text (prompts differ by question)
        for r in begins:
            self.assertEqual(r["receipt"]["user_text_sha256"], b["delivery"]["requests"][r["request"]]["user_text_sha256"])
        self.assertGreater(len({r["receipt"]["user_text_sha256"] for r in begins}), 4)
        # names before every other question
        qs = {x["request"]: x["question"] for x in b["sset"]["requests"]}
        order = [qs[r["request"]] for r in begins]
        self.assertEqual(order[:4], ["name"] * 4)
        self.assertNotIn("name", order[4:])

    def test_wrong_frozen_prompt_sends_nothing(self):
        b = build(self.td, self.plan_all_pass(), wrong_prompt_for="p0p")
        res = self.run_job(b)
        self.assertEqual(res["outcome"], "STOPPED")
        self.assertIn("prompt-input receipt for p0p differs", res["reason"])
        log = self.td / "dispatch_log.jsonl"
        sent = [json.loads(x)["request"] for x in log.read_text().splitlines()] if log.exists() else []
        self.assertEqual(sent.count("p0"), 1)          # only the name request went; the photograph was never sent

    def test_score_dispositions(self):
        p = self.plan_all_pass()
        p["p0"] = ["ok:bird", "ok:yes", "ok:yes"]      # crow primary: wrong name -> referral with Stage A consequence
        p["c1"] = ["ok:pig", "ok:no", "ok:yes"]        # pig candidate: not a photograph -> next candidate
        b = build(self.td, p)
        self.assertEqual(self.run_job(b)["outcome"], "COMPLETE")
        out = SC.score(1, allow_synthetic=True, name_score=fake_name,
                       fixture={"raw": b["fixture"]["raw"], "sset": b["sset"], "delivery": b["delivery"],
                                "key": b["key"]})
        self.assertTrue(out["WARNING"].startswith("SYNTHETIC"))
        ref = [r for r in out["referrals"] if r.get("item") == "p0"]
        self.assertEqual(len(ref), 1)
        self.assertIn("accepted Stage A bundle", ref[0]["stage_a_consequence"])
        self.assertEqual(ref[0]["answers"]["name"]["raw"], "bird")
        self.assertEqual(out["second_views"]["crow"]["status"], "selected")
        self.assertEqual(out["second_views"]["pig"]["status"], "next")
        self.assertEqual([r["item"] for r in out["candidates_failed_listed_for_owner"]], ["c1"])
        self.assertEqual(out["charged"]["attempts"], 14)
        self.assertIn("first use on unseen candidate images", out["reader_scope"])

    def test_score_refuses_injection_in_scientific_mode(self):
        with self.assertRaises(SystemExit):
            SC.admit(1, allow_synthetic=False, fixture={"raw": self.td / "x"})


class Pure(unittest.TestCase):
    def test_yes_no(self):
        self.assertEqual(SC.yes_no(" Yes. ", "ok", False), "YES")
        self.assertEqual(SC.yes_no("unsure", "ok", False), "UNSURE")
        self.assertEqual(SC.yes_no("yes, it is", "ok", False), "ERR_MALFORMED")
        self.assertEqual(SC.yes_no("yes", "ok", True), "ERR_OVERLENGTH")
        self.assertEqual(SC.yes_no(None, "interrupted", False), "ERR_INTERRUPTED")
        self.assertEqual(SC.yes_no(None, "no_response", False), "ERR_NO_RESPONSE")

    def test_limits_carry_prior_rounds(self):
        td = Path(tempfile.mkdtemp())
        orig = S.score_path
        try:
            S.score_path = lambda j: td / f"s{j}.json"
            (td / "s1.json").write_text(json.dumps({"charged": {"attempts": 240, "seconds": 3600.0}}))
            (td / "s2.json").write_text(json.dumps({"charged": {"attempts": 100, "seconds": 1800.0}}))
            lim = A.limits(3, 40)
            self.assertEqual(lim["max_attempts"], 44)
            self.assertAlmostEqual(lim["job_clock_s"], 6 * 3600 - 5400.0)
            self.assertEqual(A.limits(3, 60)["max_attempts"], 60)        # 400 - 340 caps the 10 % allowance
            with self.assertRaises(SystemExit):
                A.limits(3, 61)                                           # more requests than attempts left
        finally:
            S.score_path = orig
            shutil.rmtree(td, ignore_errors=True)

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


if __name__ == "__main__":
    unittest.main()
