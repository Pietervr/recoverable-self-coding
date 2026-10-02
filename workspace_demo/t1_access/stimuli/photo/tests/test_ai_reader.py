"""AI-reader qualification revision 3: scorer, key, frame, identity, validator, boundary and executor fixtures - no
model is called and no qualification image is shown to anything. The hard-kill fixtures are test_ai_reader_crash.py.

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_ai_reader*.py' -v
    .venv-build/bin/python -m unittest stimuli/photo/tests/test_ai_reader.py -k KeyFunctions -v   # needs WordNet
"""

from __future__ import annotations

import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PHOTO = TESTS.parent
sys.path.insert(0, str(PHOTO))
sys.path.insert(0, str(TESTS))
import ai_reader_exec as X  # noqa: E402
import ai_reader_frame as F  # noqa: E402
import ai_reader_journal as J  # noqa: E402
import ai_reader_runtime as R  # noqa: E402
import ai_reader_score as S  # noqa: E402
import airq_fixture as A  # noqa: E402
import stage_a_guard as G  # noqa: E402
from ai_reader_key import normalise  # noqa: E402

SET = json.loads(S.SET.read_text())
KEY = json.loads(S.KEY.read_text())
try:
    import nltk  # noqa: F401
    from nltk.corpus import wordnet as _wn
    _wn.get_version()
    HAVE_WN = True
except Exception:
    HAVE_WN = False


def tmp() -> Path:
    return Path(tempfile.mkdtemp(dir=X.ensure_root()))


class Scoring(unittest.TestCase):
    def test_normalise(self):
        self.assertEqual(normalise("  The Road-Sweeper. "), "road sweeper")
        self.assertEqual(normalise("“Knife”"), "knife")
        self.assertEqual(normalise("an\tapple"), "apple")

    def test_codes_and_format_precedence(self):
        al = ["road sweeper", "road sweepers", "roadsweeper"]
        self.assertEqual(S.classify("Road sweepers", al)[0], "OK_MATCH")
        self.assertEqual(S.classify("road", al)[0], "ERR_NONMATCH")
        self.assertEqual(S.classify("unclear", al)[0], "ERR_UNCLEAR")
        self.assertEqual(S.classify("", al)[0], "ERR_EMPTY")
        self.assertEqual(S.classify("truck or road sweeper", al)[0], "ERR_MULTIPLE")
        self.assertEqual(S.classify("it is probably a big road sweeper", al)[0], "ERR_EXPLANATORY")
        self.assertEqual(S.classify("r0@d", al)[0], "ERR_MALFORMED")
        self.assertEqual(S.classify("big road sweeper", al), ("ERR_NONMATCH", True))
        self.assertEqual(S.classify(None, al, "no_response")[0], "ERR_NO_RESPONSE")
        self.assertEqual(S.classify("road sweeper", al, "isolation_violation")[0], "ERR_ISOLATION")
        self.assertEqual(S.classify(None, al, "interrupted")[0], "ERR_INTERRUPTED")
        self.assertEqual(S.classify("road sweeper", al, "overflow")[0], "ERR_OVERLENGTH")
        # format precedes matching: these normalise to an alias but are errors
        self.assertEqual(S.classify("road\nsweeper", al)[0], "ERR_EXPLANATORY")
        self.assertEqual(S.classify("road sweeper\n\nIt has brushes.", al)[0], "ERR_EXPLANATORY")
        self.assertEqual(S.classify("road\x07sweeper", al)[0], "ERR_MALFORMED")
        self.assertEqual(S.classify("road sweeper", al, "ok", overlength=True)[0], "ERR_OVERLENGTH")

    def test_no_alias_trips_a_format_check(self):
        for v in KEY["items"].values():
            for a in v["aliases"]:
                self.assertEqual(S.classify(a, v["aliases"])[0], "OK_MATCH", a)

    def test_gate_arithmetic(self):
        self.assertAlmostEqual(S.cp_lower(59, 61), 0.900365, places=5)
        self.assertAlmostEqual(S.cp_lower(61, 63), 0.903420, places=5)
        self.assertAlmostEqual(S.cp_lower(60, 63), 0.881501, places=5)
        self.assertEqual(S.required_successes(SET["easy_items"]), 61)
        self.assertEqual(S.cp_lower(0, 0), 0.0)


class KeyIntegrity(unittest.TestCase):
    """Group 2, on the frozen key (no WordNet needed)."""

    def items(self, concept):
        return next(v for v in KEY["items"].values() if v["concept"] == concept)

    def test_counts_frozen(self):
        self.assertEqual(len(KEY["items"]), 300)
        self.assertEqual(sum(v["easy"] for v in KEY["items"].values()), 63)
        self.assertEqual(KEY["frame_size"], 1659)
        self.assertEqual(KEY["stratum_frame_sizes"], {"0": 520, "1": 585, "2": 554})
        r = [v["human"]["n_ratings"] for v in KEY["items"].values()]
        self.assertEqual((min(r), max(r)), (8, 22))

    def test_plural_only_artefacts_gone(self):
        al = {a for v in KEY["items"].values() for a in v["aliases"]}
        for bad in ("drawerses", "shortses", "boxerses", "underdrawerses", "boxershortses", "boxer shortses",
                    "scissorses", "pair of scissorses", "knive", "leave", "specy", "gravys", "benchs"):
            self.assertNotIn(bad, al)
        self.assertIn("pairs of scissors", self.items("scissors")["aliases"])
        self.assertIn("pair of scissors", self.items("scissors")["aliases"])

    def test_specificity_collisions_pruned(self):
        for concept, alias in (("workbench", "bench"), ("roulette_wheel", "wheel"), ("headphones", "phone"),
                               ("porcupine", "hedgehog"), ("boxer_shorts", "shorts"), ("palette", "pallet"),
                               ("parachute", "chute"), ("firecracker", "cracker"), ("mud", "clay"),
                               ("boxer_shorts", "drawers"), ("lighter", "light"), ("sword", "brand")):
            it = self.items(concept)
            self.assertNotIn(alias, it["aliases"], (concept, alias))
            self.assertIn(alias, [e["alias"] for e in it["excluded_aliases"]])
        self.assertIn("bun", self.items("roll")["aliases"])                 # the frozen equivalence

    def test_no_shared_string_but_the_equivalence(self):
        self.assertEqual(KEY["specificity_audit"]["shared_admitted_strings"], ["bun", "buns"])

    def test_no_synset_items_record_source_and_rationale(self):
        ns = [v for v in KEY["items"].values() if not v["synset"]]
        self.assertEqual(len(ns), 10)
        for v in ns:
            self.assertTrue(v["sense_rationale"])
            self.assertTrue(all(v["alias_sources"].get(a.split(" ")[0]) is not None or a in v["alias_sources"]
                                or any(a in f for f in v["validated_plurals"].values()) for a in v["aliases"]))

    def test_residue_alias_gone(self):
        al = self.items("spider_web")["aliases"]
        self.assertFalse([a for a in al if '"' in a or "]" in a])
        self.assertIn("spider's web", al)

    def test_plural_only_heuristic_audited(self):
        # every -s head among the 300 items' candidates, classified by the suffix rule and frozen after review
        self.assertEqual(KEY["inflection_audit"]["plural_only_heads"],
                         ["beans", "boots", "boxers", "boxershorts", "chopsticks", "drawers", "headphones", "latrans",
                          "overalls", "scissors", "shorts", "suspenders", "underdrawers"])
        self.assertEqual(len(KEY["inflection_audit"]["singular_s_heads"]), 19)

    def test_source_pins_in_key(self):
        self.assertEqual(KEY["source_pins"]["things"], F.SOURCE_PINS)
        self.assertEqual(KEY["source_pins"]["wordnet"]["version"], "3.0")

    def test_docstring_counts(self):
        doc = (PHOTO / "ai_reader_key.py").read_text()
        self.assertNotIn("37 concepts", doc)
        self.assertIn("29 before the specificity rule, 33 after it", doc)
        self.assertEqual(sum(v["multiword_only"] for v in KEY["items"].values()), 33)


@unittest.skipUnless(HAVE_WN, "needs WordNet (run under .venv-build)")
class KeyFunctions(unittest.TestCase):
    def test_inflections(self):
        import ai_reader_key as K
        self.assertEqual(K.inflections("knife"), ["knives"])               # irregular, WordNet noun.exc
        self.assertEqual(K.inflections("box"), ["boxes"])                  # regular
        self.assertEqual(K.inflections("road sweeper"), ["road sweepers"])
        self.assertEqual(K.inflections("pair of scissors"), ["pairs of scissors"])   # head, never the complement
        for po in ("scissors", "shorts", "drawers", "boxers", "headphones"):
            self.assertEqual(K.inflections(po), [], po)                   # plural-only: no generated plural
        self.assertEqual(K.inflections("glass"), ["glasses"])              # singular -ss keeps its plural

    def test_synonym_residue(self):
        import ai_reader_key as K
        self.assertEqual(K.synonyms('spider_web, u"spider\'s_web"]'), ["spider web", "spider's web"])

    def test_specificity_rules(self):
        import ai_reader_key as K
        c = {"Word": "workbench", "WordNet ID": "n04600486", "WordNet Synonyms": "workbench, work bench, bench"}
        released = {"bench": {"bench"}, "benches": {"bench"}}
        out = K.aliases_for("workbench", c, released, {})
        self.assertNotIn("bench", out["aliases"])
        self.assertTrue(any(r.startswith("S1") for r in out["excluded_aliases"][0]["rules"]))
        self.assertIn("work bench", out["aliases"])                        # a space variant of the canonical name

    def test_rebuild_reproduces_the_key(self):
        import ai_reader_key as K
        before = K.KEY.read_bytes()
        K.main()
        self.assertEqual(K.KEY.read_bytes(), before)


class FrameInvariant(unittest.TestCase):
    """Group 2 mutation fixtures: asserted, never used to exclude or redraw."""

    @classmethod
    def setUpClass(cls):
        cls.concepts, cls.imgs = F.read_tables()
        cls.rows, _ = F.frame()

    def test_real_frame_passes(self):
        self.assertEqual(F.check_frame_invariant(self.rows, self.concepts, self.imgs), 1659)

    def row(self, uid):
        im = self.imgs[f"{uid}.jpg"]
        return {"concept": uid, "c": self.concepts[uid], "im": im, "rec": float(im["recognizability"]),
                "close": float(im["recognizability_close"]), "n_ratings": int(float(im["recognizability_N-ratings"])),
                "n_correct": int(float(im["recognizability_N-correct"]))}

    def test_known_release_mismatch_refused(self):
        x = self.row("camera1")                                            # the image row of camera1.jpg says camera_lens
        with self.assertRaises(SystemExit):
            F.check_frame_invariant([x], self.concepts, self.imgs)

    def test_equal_ratio_swap_refused(self):
        by = {}
        for x in self.rows:
            by.setdefault((x["n_correct"], x["n_ratings"]), []).append(x)
        a, b = next(v for v in by.values() if len(v) >= 2)[:2]           # same N_correct/N_ratings: A1 cannot see it
        imgs = dict(self.imgs)
        ia, ib = dict(a["im"]), dict(b["im"])
        ia["image"], ib["image"] = b["im"]["image"], a["im"]["image"]     # rows interchanged, filenames kept
        imgs[ia["image"]], imgs[ib["image"]] = ia, ib
        xa = {**b, "im": ia, "concept": b["concept"], "c": b["c"]}
        with self.assertRaises(SystemExit):
            F.check_frame_invariant([xa], self.concepts, imgs)

    def test_counts_and_proportions(self):
        x = self.row(self.rows[0]["concept"])
        for field, val in (("recognizability_N-correct", "99"), ("recognizability_N-ratings", "0"),
                           ("recognizability", "1.2"), ("recognizability_close", "nan"),
                           ("recognizability_N-ratings", "10.5")):
            im = {**x["im"], field: val}
            imgs = {**self.imgs, im["image"]: im}
            with self.assertRaises(SystemExit, msg=field):
                F.check_frame_invariant([{**x, "im": im}], self.concepts, imgs)

    def test_duplicate_row_refused(self):
        x = self.row(self.rows[0]["concept"])
        with self.assertRaises(SystemExit):
            F.check_frame_invariant([x, x], self.concepts, self.imgs)

    def test_source_pin_mismatch_refused(self):
        d = tmp()
        for n in F.SOURCE_PINS:
            shutil.copyfile(F.THINGS / n, d / n)
        with open(d / "image-level_description.txt", "a") as fh:
            fh.write(" ")
        with self.assertRaises(SystemExit):
            F.check_sources(d)


def git(repo: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


class Approval(unittest.TestCase):
    """Group 1: the attested go, the package, the bound imports, mixed state."""

    PKG = {"a_sha256": "1" * 64, "package_digest": "2" * 64}

    def go(self, att_over=None, pkg=None):
        today = time.strftime("%Y-%m-%d")
        repo = tmp()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        (repo / "package.txt").write_text("the reviewed package")
        git(repo, "add", "package.txt")
        git(repo, "commit", "-q", "-m", "package")
        att = {"row": "aireader", "stage": "qualification", "verdict": "favourable", "reviewer": "r", "date": today,
               "reviewed_commit": git(repo, "rev-parse", "HEAD"), "package": dict(self.PKG)}
        att.update(att_over or {})
        rec = repo / "review.md"
        rec.write_text("# review\n" + G.ATTEST_OPEN + "\n" + json.dumps(att) + "\n" + G.ATTEST_CLOSE + "\n")
        git(repo, "add", "review.md")
        git(repo, "commit", "-q", "-m", "review")
        go = repo / "GO.json"
        go.write_text(json.dumps({"review": {"commit": git(repo, "rev-parse", "HEAD"), "path": "review.md",
                                             "record_sha256": J.sha(rec.read_bytes())},
                                  "owner_go": {"by": "owner", "date": today, "words": "go"},
                                  "package": pkg or dict(self.PKG)}))
        return go, repo

    def check(self, go, repo, pkg=None):
        return G.require_go(go, pkg or dict(self.PKG), row="aireader", stage="qualification", repo=repo)

    def test_positive_control(self):
        go, repo = self.go()
        self.assertEqual(self.check(go, repo)["attestation"]["row"], "aireader")

    def test_unrelated_approval_refused(self):
        go, repo = self.go({"row": "20", "stage": "A"})
        with self.assertRaises(SystemExit) as cm:
            self.check(go, repo)
        self.assertIn("not aireader/qualification/favourable", str(cm.exception))

    def test_modified_package_refused(self):
        go, repo = self.go()
        with self.assertRaises(SystemExit):
            self.check(go, repo, {**self.PKG, "a_sha256": "9" * 64})        # e.g. the key or a dependency changed

    def test_negative_record_refused(self):
        go, repo = self.go()
        d = json.loads(go.read_text())
        d["review"]["commit"] = "7048bb8" + "0" * 33
        go.write_text(json.dumps(d))
        old = G.NEGATIVE_REVIEWS
        G.NEGATIVE_REVIEWS = old | X.NEGATIVE
        try:
            with self.assertRaises(SystemExit):
                self.check(go, repo)
        finally:
            G.NEGATIVE_REVIEWS = old

    def test_bound_files_include_imports(self):
        for n in ("stage_a_guard.py", "enforce.py", "ai_reader_runtime.py", "ai_reader_journal.py",
                  "ai_reader_delivery.json", "AI_READER_DESIGN.md"):
            self.assertIn(n, X.BOUND_FILES)

    @unittest.skipUnless(X.DELIVERY.exists() and R.CODEX.exists(), "needs the delivery receipt and the codex binary")
    def test_modified_dependency_moves_the_package(self):
        d = tmp()
        for n in X.BOUND_FILES:
            shutil.copyfile(PHOTO / n, d / n)
        p1 = X.package(d)
        with open(d / "enforce.py", "a") as fh:
            fh.write("\n# changed\n")
        p2 = X.package(d)
        self.assertNotEqual(p1["enforce.py_sha256"], p2["enforce.py_sha256"])
        self.assertNotEqual(p1["package_digest"], p2["package_digest"])
        self.assertEqual(p1["codex_realpath"], str(R.CODEX.resolve()))

    @unittest.skipUnless(X.DELIVERY.exists() and R.CODEX.exists(), "needs the delivery receipt and the codex binary")
    def test_reviewed_commit_rederivation(self):
        with self.assertRaises(SystemExit):                # revision 2's commit lacks the revision-3 files
            X.package_at_commit("a59fc2d0000000000000000000000000000000000"[:7])
        head = git(G.RSC, "rev-parse", "HEAD")
        dirty = subprocess.run(["git", "-C", str(G.RSC), "status", "--porcelain", "--", *[str(PHOTO / n)
                                for n in X.BOUND_FILES]], capture_output=True, text=True).stdout.strip()
        if not dirty:                                      # positive control once the package is committed
            self.assertEqual(X.package_at_commit(head), X.package())

    def test_mixed_resumed_state_refused(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        raw = b["fixture"]["raw"]
        lines = raw.read_bytes().splitlines(keepends=True)
        raw.write_bytes(b"".join(lines[:-1]))                              # drop the receipt so a resume is possible
        fx = {**b["fixture"], "package": {"package_digest": "e" * 64}}
        with self.assertRaises(SystemExit) as cm:
            X.run(fixture=fx)
        self.assertIn("mixed resumed state", str(cm.exception))

    def test_nothing_runs_after_a_receipt(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        with self.assertRaises(SystemExit):
            X.run(fixture=b["fixture"])


class ScorerAdmission(unittest.TestCase):
    """Groups 1 and 6 at the scorer: committed raw, synthetic refusal, changed key."""

    def test_synthetic_refused_without_flag(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        with self.assertRaises(SystemExit):
            S.score(b["fixture"]["raw"], sset=b["sset"], key=b["key"])
        out = S.score(b["fixture"]["raw"], allow_synthetic=True, sset=b["sset"], key=b["key"])
        self.assertEqual(out["WARNING"], "SYNTHETIC FIXTURE - NOT A QUALIFICATION RESULT")
        self.assertIsNone(out["admission"]["admitted"])

    def test_untracked_and_tracked_dirty_refused(self):
        repo = tmp()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        raw = repo / "raw.jsonl"
        raw.write_text('{"t": "open"}\n')
        with self.assertRaises(SystemExit):
            S.committed(raw)                                               # untracked
        git(repo, "add", "raw.jsonl")
        git(repo, "commit", "-q", "-m", "raw")
        self.assertEqual(S.committed(raw)["raw_commit"], git(repo, "rev-parse", "HEAD"))
        raw.write_text('{"t": "open"}\n{"t": "edited"}\n')
        with self.assertRaises(SystemExit):
            S.committed(raw)                                               # tracked but dirty

    def test_changed_key_refused(self):
        sset = {**SET, "key_sha256": "0" * 64}
        with self.assertRaises(SystemExit) as cm:
            S.score(Path("/nonexistent"), sset=sset)
        self.assertIn("key's sha256", str(cm.exception))

    def test_referrals_carry_identity(self):
        root = tmp()
        b = A.build(root, {"rq0g": ["ok:wrong"]})
        X.run(fixture=b["fixture"])
        out = S.score(b["fixture"]["raw"], allow_synthetic=True, sset=b["sset"], key=b["key"])
        ref = out["referrals"][0]
        for k in ("raw_sha256", "package_digest", "key_sha256", "set_sha256", "scorer_sha256", "attempt_id",
                  "delivered_image_sha256", "answer_sha256", "answer_len"):
            self.assertIsNotNone(ref[k], k)
        self.assertEqual(ref["raw_answer"], "wrong")
        self.assertIsNone(ref["owner_decision"])


class Validator(unittest.TestCase):
    """Group 6: complete raw-evidence validation, mutation by mutation."""

    @classmethod
    def setUpClass(cls):
        cls.root = tmp()
        cls.b = A.build(cls.root, {"rq1c": ["fail", "ok:thing"], "rq2g": ["long"]})
        X.run(fixture=cls.b["fixture"])
        cls.recs, _ = J.read(cls.b["fixture"]["raw"])

    def ok(self, recs):
        return J.validate(recs, self.b["sset"], A.DIGEST, mode="synthetic-fixture")

    def bad(self, recs, msg=None):
        with self.assertRaises(SystemExit) as cm:
            self.ok(recs)
        if msg:
            self.assertIn(msg, str(cm.exception))

    def test_valid_journal_passes(self):
        v = J.validate(self.recs, self.b["sset"], A.DIGEST, raw_bytes=self.b["fixture"]["raw"].read_bytes(),
                       mode="synthetic-fixture")
        self.assertEqual(v["final"], 6)

    def idx(self, pred):
        return next(i for i, r in enumerate(self.recs) if pred(r))

    def mutate(self, i, **kw):
        recs = copy.deepcopy(self.recs)
        recs[i].update(kw)
        return recs

    def test_mutations(self):
        e_ok = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "ok")
        e_pf = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "provider_failure")
        b1 = self.idx(lambda r: r["t"] == "begin")
        b2 = self.idx(lambda r: r["t"] == "begin" and r["attempt_no"] == 2)
        self.bad(self.mutate(e_ok, retained="yes"), "retained")
        self.bad(self.mutate(e_ok, retained=False), "retained")
        self.bad(self.mutate(e_pf, answer="thing"), "answer on a provider_failure")
        self.bad(self.mutate(e_ok, answer=None), "ok outcome without an answer")
        self.bad(self.mutate(e_ok, answer="thinG"), "edited")
        self.bad(self.mutate(e_ok, overlength=True), "overlength")
        self.bad(self.mutate(e_ok, outcome="maybe"), "unknown outcome")
        self.bad(self.mutate(b2, attempt_id=self.recs[b1]["attempt_id"]), "repeated")
        self.bad(self.mutate(b2, attempt_no=5), "attempt_no")
        self.bad(self.mutate(b1, request=self.b["sset"]["delivery_order"][1],
                             item="it1", view="colour"), "delivery order")
        self.bad(self.mutate(b1, package_digest="e" * 64), "mixed or foreign")
        self.bad(self.mutate(b1, mode="scientific"), "modes")
        self.bad(self.mutate(e_ok, events={"length": 99999, "sha256": "x", "text": "y" * 99999}), "bounded")
        recs = copy.deepcopy(self.recs)
        recs[-1]["counts"]["attempts"] += 1
        self.bad(recs, "receipt counters")
        recs = copy.deepcopy(self.recs)
        del recs[e_ok]
        self.bad(recs)                                                     # seq gap
        self.bad(self.recs[:-1], "did not complete")                       # no receipt: incomplete

    def test_no_response_needs_three_failures(self):
        root = tmp()
        b = A.build(root, {"rq1c": ["fail"]})
        X.run(fixture=b["fixture"])
        recs, _ = J.read(b["fixture"]["raw"])
        self.assertEqual(J.validate(recs, b["sset"], A.DIGEST, mode="synthetic-fixture")["outcomes"]["no_response"], 1)
        fi = next(i for i, r in enumerate(recs) if r["t"] == "final")
        recs2 = copy.deepcopy(recs)
        pf = [i for i, r in enumerate(recs2) if r["t"] == "end" and r["outcome"] == "provider_failure"]
        recs2[pf[0]]["outcome"], recs2[pf[0]]["retained"] = "ok", True
        recs2[pf[0]]["answer"], recs2[pf[0]]["answer_len"] = "thing", 5
        recs2[pf[0]]["answer_sha256"], recs2[pf[0]]["overlength"] = J.sha(b"thing"), False
        with self.assertRaises(SystemExit):
            J.validate(recs2, b["sset"], A.DIGEST, mode="synthetic-fixture")
        self.assertGreater(fi, 0)


class Boundary(unittest.TestCase):
    """Group 4: parser and classification (synthetic bytes), and the real binary without any request."""

    EV = [{"type": "thread.started"}, {"type": "turn.started"},
          {"type": "item.completed", "item": {"type": "agent_message", "text": "knife"}}, {"type": "turn.completed"}]

    def b(self, evs):
        return ("\n".join(json.dumps(e) for e in evs) + "\n").encode()

    def test_fail_closed(self):
        c = R.classify(b"", b"", None, 1, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "provider_failure")                # nothing received: retry allowed
        c = R.classify(b"", b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")             # an answer without event evidence
        c = R.classify(b"not json\n" + self.b(self.EV), b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")
        tool = [self.EV[0], {"type": "item.completed", "item": {"type": "command_execution"}}]
        c = R.classify(self.b(tool), b"boom", None, 1, timed_out=False, overflow=False)
        self.assertEqual((c["outcome"], c["retained"]), ("isolation_violation", True))   # before retry eligibility
        c = R.classify(self.b(self.EV), b"", "knife", 1, timed_out=False, overflow=False)
        self.assertEqual((c["outcome"], c["answer"]), ("ok", "knife"))   # answer locked despite exit 1
        c = R.classify(self.b(self.EV[:3]), b"", None, None, timed_out=True, overflow=False)
        self.assertEqual((c["outcome"], c["answer"]), ("isolation_violation", "knife"))  # received, incomplete
        c = R.classify(b"", b"Error loading config: x", None, 1, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "structural_failure")
        self.assertTrue(R.isolation_problems([{"type": "web_search.begin"}]))

    def test_no_silent_truncation(self):
        long = "knife " * 500
        c = R.classify(self.b(self.EV), b"", long, 0, timed_out=False, overflow=False)
        self.assertTrue(c["overlength"])
        self.assertEqual(c["answer_len"], len(long))
        self.assertEqual(c["answer_sha256"], J.sha(long.encode()))
        self.assertEqual(len(c["answer"]), R.ANSWER_KEEP)

    def test_pinned_env(self):
        e = R.env(Path("/x"))
        self.assertEqual(sorted(e), ["CODEX_HOME", "HOME", "LANG", "PATH", "TMPDIR"])
        self.assertEqual(e["PATH"], "/usr/bin:/bin")

    @unittest.skipUnless(R.CODEX.exists(), "needs the codex binary")
    def test_profile_denies_repo_and_allows_codex(self):
        adir = tmp() / "a"
        R.prepare(adir, A.png(7), "x.png")
        rc, out, err = R.run_local(["/bin/cat"], adir, [str(S.KEY)])
        self.assertNotEqual(rc, 0)
        self.assertIn(b"Operation not permitted", err)
        rc, out, err = R.run_local(["/bin/ls"], adir, [str(Path.home())])
        self.assertNotEqual(rc, 0)
        rc, out, err = R.run_local([str(R.CODEX)], adir, ["--version"])
        self.assertEqual((rc, out.strip()), (0, b"codex-cli 0.159.3"))

    @unittest.skipUnless(R.CODEX.exists(), "needs the codex binary")
    def test_effective_features_and_receipt(self):
        adir = tmp() / "a"
        img = R.prepare(adir, A.png(9), "x.png")
        f = R.effective_features([str(R.CODEX)], SET["reader"], adir)
        self.assertEqual(f["disabled_effective_false"], len(R.DISABLE) - len(R.UNDISABLEABLE))
        self.assertEqual(f["cannot_be_disabled"], {"unified_exec": "true"})       # measured; contained, disclosed
        rc = R.prompt_input([str(R.CODEX)], SET["reader"], adir, img, SET["prompt"])
        self.assertEqual(rc["images"][0]["sha256"], J.sha(A.png(9)))
        self.assertEqual(rc["instruction_kinds"], ["multi_agent.mode_instructions", "multi_agent.role_instructions"])
        self.assertEqual(R.auth_route([str(R.CODEX)], adir), "Logged in using ChatGPT")


class Executor(unittest.TestCase):
    """Groups 3-5 in fixture mode (in-process; hard kills are in test_ai_reader_crash.py)."""

    def run_fx(self, plan, **over):
        root = tmp()
        b = A.build(root, plan)
        saved = {k: getattr(X, k) for k in over}
        lim = dict(X.LIMITS)
        try:
            for k, v in over.items():
                if k == "LIMITS":
                    X.LIMITS.update(v)
                else:
                    setattr(X, k, v)
            out = X.run(fixture=b["fixture"])
        finally:
            X.LIMITS.clear()
            X.LIMITS.update(lim)
            for k, v in saved.items():
                if k != "LIMITS":
                    setattr(X, k, v)
        recs, _ = J.read(b["fixture"]["raw"])
        return out, recs, root, b

    def ends(self, recs):
        return [r for r in recs if r["t"] == "end"]

    def test_retry_only_without_answer(self):
        out, recs, root, b = self.run_fx({"rq1c": ["fail", "fail", "ok:thing"], "rq2c": ["ok_exit1:thing"],
                                          "rq0g": ["tool_exit1"]})
        self.assertEqual(out["outcome"], "COMPLETE")
        calls = [d["request"] for d in A.dispatches(root)]
        self.assertEqual(calls.count("rq1c"), 3)
        self.assertEqual(calls.count("rq2c"), 1)                          # an answer with exit 1 is final
        self.assertEqual(calls.count("rq0g"), 1)                          # a tool event with exit 1 is final
        J.validate(recs, b["sset"], A.DIGEST, mode="synthetic-fixture")

    def test_three_failures_then_no_response(self):
        out, recs, root, b = self.run_fx({"rq1c": ["fail"]})
        self.assertEqual(out["outcome"], "COMPLETE")
        self.assertEqual([r["request"] for r in recs if r["t"] == "final"], ["rq1c"])

    def test_smoke_holds_on_structural_and_no_image(self):
        out, recs, root, b = self.run_fx({"rq0c": ["structural"]})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("structural", out["reason"])
        self.assertEqual(len(A.dispatches(root)), 1)
        out, recs, root, b = self.run_fx({"rq0c": ["noimage"]})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertEqual(self.ends(recs)[0]["answer"], "There is no image attached.")   # retained and scorable
        out, recs, root, b = self.run_fx({"rq0c": ["fail"]})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("first request had no answer", out["reason"])

    def test_attempt_cap_writes_final_then_stops(self):
        out, recs, root, b = self.run_fx({"rq1c": ["fail"]}, LIMITS={"max_attempts": 4})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("attempt cap", out["reason"])
        self.assertEqual([r["request"] for r in recs if r["t"] == "final"], ["rq1c"])   # before the cap check
        J.validate(recs, b["sset"], A.DIGEST, require_complete=False, mode="synthetic-fixture")

    def test_clock_stops_inside_reserve(self):
        out, recs, root, b = self.run_fx({}, LIMITS={"job_clock_s": X.FINAL_S + X.MIN_ATTEMPT_S - 1})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("job clock", out["reason"])
        self.assertFalse([r for r in recs if r["t"] == "begin"])

    def test_timeout_kills_and_reaps_the_group(self):
        out, recs, root, b = self.run_fx({"rq1c": ["block", "ok:thing"]},
                                         LIMITS={"attempt_timeout_s": 2})
        e = next(r for r in self.ends(recs) if r["request"] == "rq1c")
        self.assertEqual((e["outcome"], e["kill"]["how"]), ("provider_failure", "SIGKILL"))
        self.assertLess(e["kill"]["kill_to_reap_s"], X.TERM_GRACE_S + 1.5)
        self.assertLess(e["seconds"], 2 + X.TERM_GRACE_S + 2)
        pid = next(d["pid"] for d in A.dispatches(root) if d["behaviour"] == "block")
        with self.assertRaises(ProcessLookupError):
            __import__("os").kill(pid, 0)

    def test_overflow_is_retained_overlength(self):
        out, recs, root, b = self.run_fx({"rq1c": ["flood"]})
        e = next(r for r in self.ends(recs) if r["request"] == "rq1c")
        self.assertEqual((e["outcome"], e["retained"]), ("overflow", True))
        self.assertLessEqual(len(json.dumps(e)), J.MAX_RECORD)

    def test_raw_cap_stops(self):
        out, recs, root, b = self.run_fx({}, LIMITS={"raw_bytes": 3 * J.MAX_RECORD + X.RAW_FINAL_BYTES + 2000})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("raw output", out["reason"])

    def test_receipt_mismatch_holds_before_sending(self):
        root = tmp()
        b = A.build(root, {})
        b["fixture"]["delivery"]["requests"]["rq0c"]["image_sha256"] = "0" * 64
        out = X.run(fixture=b["fixture"])
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("nothing sent", out["reason"])
        self.assertEqual(A.dispatches(root), [])


if __name__ == "__main__":
    unittest.main()
