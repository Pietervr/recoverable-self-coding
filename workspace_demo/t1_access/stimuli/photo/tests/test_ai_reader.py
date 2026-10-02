"""AI-reader qualification revision 2: scorer, completeness, gate and executor tests - no model is called.

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_ai_reader.py' -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PHOTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHOTO))
import ai_reader_exec as X  # noqa: E402
import ai_reader_score as S  # noqa: E402
from ai_reader_key import normalise  # noqa: E402

SET = json.loads(S.SET.read_text())
KEY = json.loads(S.KEY.read_text())


def fake_answer(r: dict, wrong: set) -> str:
    k = KEY["items"][r["item"]]
    return "unclear" if r["request"] in wrong else k["aliases"][0].title() + "."


class Scoring(unittest.TestCase):
    def test_normalise(self):
        self.assertEqual(normalise("  The Road-Sweeper. "), "road sweeper")
        self.assertEqual(normalise("“Knife”"), "knife")
        self.assertEqual(normalise("an\tapple"), "apple")

    def test_codes(self):
        al = ["road sweeper", "road sweepers", "roadsweeper"]
        self.assertEqual(S.classify("Road sweepers", al)[0], "OK_MATCH")
        self.assertEqual(S.classify("road", al)[0], "ERR_NONMATCH")          # no partial credit
        self.assertEqual(S.classify("unclear", al)[0], "ERR_UNCLEAR")
        self.assertEqual(S.classify("", al)[0], "ERR_EMPTY")
        self.assertEqual(S.classify("truck or road sweeper", al)[0], "ERR_MULTIPLE")
        self.assertEqual(S.classify("it is probably a big road sweeper", al)[0], "ERR_EXPLANATORY")
        self.assertEqual(S.classify("r0@d", al)[0], "ERR_MALFORMED")
        self.assertEqual(S.classify("big road sweeper", al), ("ERR_NONMATCH", True))   # close is descriptive only
        self.assertEqual(S.classify(None, al, "no_response")[0], "ERR_NO_RESPONSE")
        self.assertEqual(S.classify("road sweeper", al, "isolation_violation")[0], "ERR_ISOLATION")

    def test_key_has_no_stemming_artefacts(self):
        al = {a for v in KEY["items"].values() for a in v["aliases"]}
        for bad in ("knive", "leave", "specy", "gravys", "benchs"):
            self.assertNotIn(bad, al)

    def test_gate_arithmetic(self):
        self.assertAlmostEqual(S.cp_lower(59, 61), 0.900365, places=5)       # Codex's table
        self.assertEqual(S.required_successes(61), 59)
        self.assertEqual(S.required_successes(SET["easy_items"]), 61)         # 63 easy items after the frame repair
        self.assertEqual(S.cp_lower(0, 0), 0.0)


class Completeness(unittest.TestCase):
    def write(self, recs) -> Path:
        p = Path(tempfile.mkdtemp()) / "raw.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
        return p

    def full(self, wrong=frozenset()):
        return [{"request": r["request"], "item": r["item"], "view": r["view"], "retained": True, "status": "ok",
                 "answer": fake_answer(r, wrong)} for r in SET["requests"]]

    def test_perfect_and_admitted(self):
        out = S.score(self.write(self.full()), require_committed=False)
        self.assertTrue(out["admission"]["admitted"])
        self.assertEqual(out["descriptive"]["gray_all"]["correct"], 300)
        self.assertEqual(out["referral_count"], 0)

    def test_three_easy_gray_errors_fail(self):
        easy_gray = [r["request"] for r in SET["requests"] if r["view"] == "gray" and KEY["items"][r["item"]]["easy"]]
        out = S.score(self.write(self.full(set(easy_gray[:3]))), require_committed=False)
        self.assertEqual(out["admission"]["easy_correct"], SET["easy_items"] - 3)
        self.assertFalse(out["admission"]["admitted"])
        self.assertEqual(out["referral_count"], 3)
        self.assertEqual(out["referrals"][0]["reason"], "ERR_UNCLEAR")
        self.assertIsNone(out["referrals"][0]["owner_decision"])

    def test_colour_alone_cannot_pass(self):
        recs = [r for r in self.full() if r["view"] == "colour"]
        with self.assertRaises(SystemExit):
            S.score(self.write(recs), require_committed=False)

    def test_duplicates_unknown_and_mismatch_refused(self):
        recs = self.full()
        for bad in (recs + [recs[0]], recs + [{**recs[0], "request": "zzzz"}],
                    [{**recs[0], "view": "gray" if recs[0]["view"] == "colour" else "colour"}] + recs[1:]):
            with self.assertRaises(SystemExit):
                S.score(self.write(bad), require_committed=False)

    def test_provider_failures_listed_not_scored(self):
        recs = self.full()
        recs.insert(0, {**recs[0], "retained": False, "status": "provider_failure", "answer": None})
        out = S.score(self.write(recs), require_committed=False)
        self.assertEqual(out["provider_failures"], 1)

    def test_uncommitted_refused(self):
        with self.assertRaises(SystemExit):
            S.score(self.write(self.full()))


class Executor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.saved = (X.RAW, X.JOB, X.require_go)
        X.RAW, X.JOB = self.tmp / "raw.jsonl", self.tmp / "job"
        X.require_go = lambda *a, **k: {}

    def tearDown(self):
        X.RAW, X.JOB, X.require_go = self.saved

    def test_isolation_check(self):
        ok = [{"type": "thread.started"}, {"type": "item.completed", "item": {"type": "agent_message"}}]
        self.assertTrue(X.isolation_ok(ok)[0])
        self.assertFalse(X.isolation_ok(ok + [{"type": "item.completed", "item": {"type": "command_execution"}}])[0])
        self.assertFalse(X.isolation_ok(ok + [{"type": "web_search.begin"}])[0])

    def test_run_retries_only_failures_and_recovers(self):
        calls = {"n": 0}

        def call(sset, r):
            calls["n"] += 1
            if calls["n"] == 5:
                raise KeyboardInterrupt                    # a crash mid-attempt
            if r["request"] == SET["delivery_order"][1]:
                return {"status": "provider_failure", "reason": "test"}
            return {"status": "ok", "answer": fake_answer(r, set())}
        with self.assertRaises(KeyboardInterrupt):
            X.run(dry=False, call=call)
        st = json.loads((X.JOB / "state.json").read_text())
        self.assertIsNotNone(st["open"])
        out = X.run(dry=False, call=call)                  # restart: idempotent, same limits
        self.assertEqual(out["retained"], 600)
        recs = [json.loads(l) for l in X.RAW.read_text().splitlines()]
        no_resp = [r for r in recs if r["retained"] and r["status"] == "no_response"]
        self.assertEqual(len(no_resp), 1)                  # three provider failures, then ERR_NO_RESPONSE
        self.assertEqual(sum(1 for r in recs if r["retained"]), 600)
        self.assertLessEqual(out["attempts"], X.LIMITS["max_attempts"])
        sc = S.score(X.RAW, require_committed=False)
        self.assertEqual(sc["reason_codes"]["gray"].get("ERR_NO_RESPONSE", 0) +
                         sc["reason_codes"]["colour"].get("ERR_NO_RESPONSE", 0), 1)


if __name__ == "__main__":
    unittest.main()
