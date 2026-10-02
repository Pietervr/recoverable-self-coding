"""AI-reader qualification revision 4: scorer, key, frame, identity, validator, boundary and executor fixtures - no
model is called and no qualification image is shown to anything. The real codex binary is used only for its local
subcommands (--version, features list, debug prompt-input, login status) and for the exec-invocation receipt with all
network denied by the kernel sandbox and a synthetic 8x8 image. The hard-kill fixtures are test_ai_reader_crash.py.

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_ai_reader*.py' -v
    .venv-build/bin/python -m unittest stimuli/photo/tests/test_ai_reader.py -k KeyFunctions -v   # needs WordNet
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import signal
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
import memprobe  # noqa: E402
import stage_a_guard as G  # noqa: E402
from ai_reader_key import KEY as KEY_PATH, normalise  # noqa: E402

SET = json.loads(S.SET.read_text())
KEY = json.loads(KEY_PATH.read_text())
try:
    import nltk  # noqa: F401
    from nltk.corpus import wordnet as _wn
    _wn.get_version()
    HAVE_WN = True
except Exception:
    HAVE_WN = False
HAVE_CODEX = R.CODEX.exists()


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
    """Closure 2 on the frozen key (no WordNet needed)."""

    def items(self, concept):
        return next(v for v in KEY["items"].values() if v["concept"] == concept)

    def test_counts_frozen(self):
        self.assertEqual(len(KEY["items"]), 300)
        self.assertEqual(sum(v["easy"] for v in KEY["items"].values()), 63)
        self.assertEqual(KEY["frame_size"], 1659)
        self.assertEqual(KEY["stratum_frame_sizes"], {"0": 520, "1": 585, "2": 554})
        r = [v["human"]["n_ratings"] for v in KEY["items"].values()]
        self.assertEqual((min(r), max(r)), (8, 22))
        a = KEY["specificity_audit"]
        self.assertEqual((a["excluded_bases"], a["excluded_forms"], a["targets_affected"], a["easy_targets_affected"]),
                         (64, 126, 52, 14))
        self.assertEqual(a["by_rule"], {"S1": 23, "S2": 4, "S3": 5, "S4": 60})

    def test_plural_only_artefacts_gone(self):
        al = {a for v in KEY["items"].values() for a in v["aliases"]}
        for bad in ("drawerses", "shortses", "boxerses", "underdrawerses", "boxershortses", "boxer shortses",
                    "scissorses", "pair of scissorses", "knive", "leave", "specy", "gravys", "benchs"):
            self.assertNotIn(bad, al)
        self.assertIn("pairs of scissors", self.items("scissors")["aliases"])

    def test_specificity_collisions_pruned(self):
        for concept, alias in (("workbench", "bench"), ("roulette_wheel", "wheel"), ("headphones", "phone"),
                               ("porcupine", "hedgehog"), ("boxer_shorts", "shorts"), ("palette", "pallet"),
                               ("parachute", "chute"), ("firecracker", "cracker"), ("mud", "clay"),
                               ("boxer_shorts", "drawers"), ("lighter", "light"), ("sword", "brand")):
            it = self.items(concept)
            self.assertNotIn(alias, it["aliases"], (concept, alias))
            self.assertIn(alias, [e["alias"] for e in it["excluded_aliases"]])
        self.assertIn("bun", self.items("roll")["aliases"])

    def test_full_forms_prospectively_excluded_with_their_base(self):
        """A generated inflection inherits its base's decision: no excluded base admits any of its forms."""
        for v in KEY["items"].values():
            excl = {e["alias"] for e in v["excluded_aliases"]}
            self.assertFalse(excl & set(v["aliases"]), v["concept"])
            bases = {e["base"] for e in v["excluded_aliases"]}
            for e in v["excluded_aliases"]:
                self.assertIn(e["base"], bases)
                self.assertEqual(e["rules"], next(x["rules"] for x in v["excluded_aliases"] if x["alias"] == e["base"]))

    def test_no_shared_string_but_the_equivalence(self):
        self.assertEqual(KEY["specificity_audit"]["shared_admitted_strings"], ["bun", "buns"])

    def test_no_synset_items_record_source_and_rationale(self):
        ns = [v for v in KEY["items"].values() if not v["synset"]]
        self.assertEqual(len(ns), 10)
        syn_bases = [a for v in ns for a, src in v["alias_sources"].items() if "WordNet Synonyms" in src
                     and src == ["WordNet Synonyms"]]
        self.assertEqual((len(syn_bases), len({v["concept"] for v in ns for a, src in v["alias_sources"].items()
                                                if src == ["WordNet Synonyms"]})), (5, 3))
        for v in ns:
            self.assertTrue(v["sense_rationale"])

    def test_wording_matches_the_predicates(self):
        doc = (PHOTO / "ai_reader_key.py").read_text()
        self.assertIn("FIRST-LISTED WordNet noun sense differs from the recorded target synset", doc)
        self.assertNotIn("Word and id fields alone", doc)
        self.assertIn("BOUNDED TO THIS CANDIDATE", doc)
        self.assertIn("first-listed WordNet noun sense differs", KEY["specificity_rule"])
        self.assertIn("latrans", KEY["inflection_audit"]["note"])
        self.assertIn("not a general grammatical validator", KEY["inflection_audit"]["note"])

    def test_plural_only_heuristic_audited(self):
        self.assertEqual(KEY["inflection_audit"]["plural_only_heads"],
                         ["beans", "boots", "boxers", "boxershorts", "chopsticks", "drawers", "headphones", "latrans",
                          "overalls", "scissors", "shorts", "suspenders", "underdrawers"])
        self.assertEqual(len(KEY["inflection_audit"]["singular_s_heads"]), 19)

    def test_source_pins_in_key(self):
        self.assertEqual(KEY["source_pins"]["things"], F.SOURCE_PINS)
        self.assertEqual(KEY["source_pins"]["wordnet"]["version"], "3.0")

    def test_docstring_counts(self):
        doc = (PHOTO / "ai_reader_key.py").read_text()
        self.assertIn("29 before the specificity rule, 33 after it", doc)
        self.assertEqual(sum(v["multiword_only"] for v in KEY["items"].values()), 33)


@unittest.skipUnless(HAVE_WN, "needs WordNet (run under .venv-build)")
class KeyFunctions(unittest.TestCase):
    def test_inflections(self):
        import ai_reader_key as K
        self.assertEqual(K.inflections("knife"), ["knives"])
        self.assertEqual(K.inflections("box"), ["boxes"])
        self.assertEqual(K.inflections("road sweeper"), ["road sweepers"])
        self.assertEqual(K.inflections("pair of scissors"), ["pairs of scissors"])
        for po in ("scissors", "shorts", "drawers", "boxers", "headphones"):
            self.assertEqual(K.inflections(po), [], po)
        self.assertEqual(K.inflections("glass"), ["glasses"])

    def test_synonym_residue(self):
        import ai_reader_key as K
        self.assertEqual(K.synonyms('spider_web, u"spider\'s_web"]'), ["spider web", "spider's web"])

    def test_specificity_rules(self):
        import ai_reader_key as K
        c = {"Word": "workbench", "WordNet ID": "n04600486", "WordNet Synonyms": "workbench, work bench, bench"}
        out = K.aliases_for("workbench", c, {"bench": {"bench"}, "benches": {"bench"}}, {})
        self.assertNotIn("bench", out["aliases"])
        self.assertIn("work bench", out["aliases"])

    def test_full_form_s1_prospectively(self):
        """Every ADMITTED full form (inflections included) against every released concept's canonical names and
        inflections: the only hits are the declared roll/bun equivalence and hook2's own canonical Word."""
        import ai_reader_key as K
        concepts, _ = F.read_tables()
        released = K.released_names(concepts)
        hits = sorted((v["concept"], a) for v in KEY["items"].values() for a in v["aliases"]
                      if released.get(a, set()) - {v["concept"]})
        self.assertEqual(hits, [("hook2", "hook"), ("hook2", "hooks"), ("roll", "bun"), ("roll", "buns")])

    def test_rebuild_reproduces_the_key(self):
        import ai_reader_key as K
        before = K.KEY.read_bytes()
        K.main()
        self.assertEqual(K.KEY.read_bytes(), before)


class FrameInvariant(unittest.TestCase):
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
        with self.assertRaises(SystemExit):
            F.check_frame_invariant([self.row("camera1")], self.concepts, self.imgs)

    def test_equal_ratio_swap_refused(self):
        by = {}
        for x in self.rows:
            by.setdefault((x["n_correct"], x["n_ratings"]), []).append(x)
        a, b = next(v for v in by.values() if len(v) >= 2)[:2]
        imgs = dict(self.imgs)
        ia, ib = dict(a["im"]), dict(b["im"])
        ia["image"], ib["image"] = b["im"]["image"], a["im"]["image"]
        imgs[ia["image"]], imgs[ib["image"]] = ia, ib
        with self.assertRaises(SystemExit):
            F.check_frame_invariant([{**b, "im": ia}], self.concepts, imgs)

    def test_retained_close_and_ratio_mutations(self):
        x = self.row(self.rows[0]["concept"])
        with self.assertRaisesRegex(SystemExit, "retained norm"):
            F.check_frame_invariant([{**x, "close": x["close"] + 0.01}], self.concepts, self.imgs)
        im = {**x["im"], "recognizability": str(x["rec"] + 0.05)}
        imgs = {**self.imgs, im["image"]: im}
        with self.assertRaises(SystemExit):
            F.check_frame_invariant([{**x, "im": im, "rec": x["rec"] + 0.05}], self.concepts, imgs)

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
    """Closure 1: the shared strict guard with row aireader, the package, the bound imports, mixed state."""

    PKG = {"a_sha256": "1" * 64, "codex_realpath": "/x/codex", "package_digest": "2" * 64}

    def go(self, att_over=None, pkg=None):
        repo = tmp()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        (repo / "package.txt").write_text("the reviewed package")
        git(repo, "add", "package.txt")
        git(repo, "commit", "-q", "-m", "package")
        today = git(repo, "show", "-s", "--format=%cs", "HEAD")
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
                                  "owner_go": {"by": "owner", "date": "2099-01-01", "words": "go"},
                                  "package": pkg or dict(self.PKG)}))
        return go, repo

    def check(self, go, repo, pkg=None, at=None):
        return G.require_go(go, pkg or dict(self.PKG), row="aireader", stage="qualification", repo=repo,
                            verify_at_commit=at or (lambda c: dict(self.PKG)))

    def test_positive_control(self):
        go, repo = self.go()
        self.assertEqual(self.check(go, repo)["attestation"]["row"], "aireader")

    def test_unrelated_approval_refused(self):
        go, repo = self.go({"row": "20", "stage": "A"})
        with self.assertRaises(SystemExit) as cm:
            self.check(go, repo)
        self.assertIn("not aireader/qualification/favourable", str(cm.exception))

    def test_strict_schema_on_the_reader_package(self):
        for name, over in (("extra null key", {"package": {**self.PKG, "x_sha256": None}}),
                           ("short digest", {"package": {**self.PKG, "a_sha256": "1" * 63}}),
                           ("numeric path", {"package": {**self.PKG, "codex_realpath": 1}}),
                           ("truthy reviewer", {"reviewer": True}), ("date truncation", {"date": "2026-10-02x"})):
            with self.subTest(name):
                go, repo = self.go(over)
                with self.assertRaises(SystemExit):
                    self.check(go, repo)

    def test_modified_package_refused(self):
        go, repo = self.go()
        with self.assertRaises(SystemExit):
            self.check(go, repo, {**self.PKG, "a_sha256": "9" * 64})

    def test_negative_record_refused(self):
        go, repo = self.go()
        d = json.loads(go.read_text())
        old = G.NEGATIVE_REVIEWS
        G.NEGATIVE_REVIEWS = old | {d["review"]["commit"][:7]}
        try:
            with self.assertRaises(SystemExit):
                self.check(go, repo)
        finally:
            G.NEGATIVE_REVIEWS = old
        self.assertTrue({"cf3e49e", "7048bb8", "5a8d7ac"} <= G.NEGATIVE_REVIEWS | X.NEGATIVE)

    def test_bound_files_include_imports(self):
        for n in ("stage_a_guard.py", "enforce.py", "memprobe.py", "stage_a_watchdog.py", "ai_reader_runtime.py",
                  "ai_reader_journal.py", "ai_reader_delivery.json", "AI_READER_DESIGN.md"):
            self.assertIn(n, X.BOUND_FILES)

    @unittest.skipUnless(X.DELIVERY.exists() and HAVE_CODEX, "needs the delivery receipt and the codex binary")
    def test_modified_dependency_moves_the_package(self):
        d = tmp()
        for n in X.BOUND_FILES:
            shutil.copyfile(PHOTO / n, d / n)
        p1 = X.package(d)
        with open(d / "memprobe.py", "a") as fh:
            fh.write("\n# changed\n")
        p2 = X.package(d)
        self.assertNotEqual(p1["memprobe.py_sha256"], p2["memprobe.py_sha256"])
        self.assertNotEqual(p1["package_digest"], p2["package_digest"])
        G.check_package_schema(p1, set(p1), "package")                      # the real package passes the schema

    @unittest.skipUnless(X.DELIVERY.exists() and HAVE_CODEX, "needs the delivery receipt and the codex binary")
    def test_reviewed_commit_rederivation(self):
        with self.assertRaises(SystemExit):
            X.package_at_commit("a59fc2d")
        head = git(G.RSC, "rev-parse", "HEAD")
        dirty = subprocess.run(["git", "-C", str(G.RSC), "status", "--porcelain", "--", *[str(PHOTO / n)
                                for n in X.BOUND_FILES]], capture_output=True, text=True).stdout.strip()
        if not dirty:
            self.assertEqual(X.package_at_commit(head), X.package())

    def test_mixed_resumed_state_refused(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        raw = b["fixture"]["raw"]
        lines = raw.read_bytes().splitlines(keepends=True)
        raw.write_bytes(b"".join(lines[:-1]))
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
    def test_synthetic_refused_without_flag_and_labelled(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        with self.assertRaises(SystemExit):
            S.score(b["fixture"]["raw"])                                     # scientific mode on a fixture journal
        out = S.score(b["fixture"]["raw"], allow_synthetic=True, sset=b["sset"], key=b["key"],
                      delivery=b["fixture"]["delivery"])
        self.assertEqual(out["WARNING"], "SYNTHETIC FIXTURE - NOT A QUALIFICATION RESULT")
        self.assertIsNone(out["admission"]["admitted"])

    def test_scientific_mode_refuses_injected_objects(self):
        changed_alias = copy.deepcopy(KEY)
        it = next(iter(changed_alias["items"].values()))
        it["aliases"] = it["aliases"] + ["anything"]
        changed_easy = copy.deepcopy(KEY)
        for v in changed_easy["items"].values():
            v["easy"] = True
        for name, kw in (("changed alias", {"key": changed_alias}), ("changed easy set", {"key": changed_easy}),
                         ("changed set", {"sset": {**SET, "easy_items": 300}}),
                         ("caller package", {"package": {"package_digest": "0" * 64}}),
                         ("caller delivery", {"delivery": {"instructions_sha256": "0" * 64, "requests": {}}})):
            with self.subTest(name):
                with self.assertRaises(SystemExit) as cm:
                    S.score(Path("/nonexistent"), **kw)
                self.assertIn("injected objects", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            S.admit(Path("/nonexistent"), SET, package={"package_digest": "0" * 64}, allow_synthetic=False, go=None)
        self.assertIn("caller-supplied package", str(cm.exception))

    def test_untracked_and_tracked_dirty_refused(self):
        repo = tmp()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        raw = repo / "raw.jsonl"
        raw.write_text('{"t": "open"}\n')
        with self.assertRaises(SystemExit):
            S.committed(raw)
        git(repo, "add", "raw.jsonl")
        git(repo, "commit", "-q", "-m", "raw")
        self.assertEqual(S.committed(raw)["raw_commit"], git(repo, "rev-parse", "HEAD"))
        raw.write_text('{"t": "open"}\n{"t": "edited"}\n')
        with self.assertRaises(SystemExit):
            S.committed(raw)

    def test_referrals_carry_identity(self):
        root = tmp()
        b = A.build(root, {"rq0g": ["ok:wrong"]})
        X.run(fixture=b["fixture"])
        out = S.score(b["fixture"]["raw"], allow_synthetic=True, sset=b["sset"], key=b["key"],
                      delivery=b["fixture"]["delivery"])
        ref = out["referrals"][0]
        for k in ("raw_sha256", "package_digest", "key_sha256", "set_sha256", "scorer_sha256", "attempt_id",
                  "delivered_image_sha256", "answer_sha256", "answer_len"):
            self.assertIsNotNone(ref[k], k)
        self.assertEqual(ref["raw_answer"], "wrong")


def vkw(b):
    return {"mode": "synthetic-fixture", "delivery": b["fixture"]["delivery"],
            "instructions_sha256": b["fixture"]["delivery"]["instructions_sha256"], "limits": X.LIMITS}


class Validator(unittest.TestCase):
    """Closure 6: complete raw-evidence validation, mutation by mutation."""

    @classmethod
    def setUpClass(cls):
        cls.root = tmp()
        cls.b = A.build(cls.root, {"rq1c": ["fail", "ok:thing"], "rq2g": ["long"]})
        X.run(fixture=cls.b["fixture"])
        cls.recs, _ = J.read(cls.b["fixture"]["raw"])

    def ok(self, recs, **kw):
        return J.validate(recs, self.b["sset"], A.DIGEST, **{**vkw(self.b), **kw})

    def bad(self, recs, msg=None):
        with self.assertRaises(SystemExit) as cm:
            self.ok(recs)
        if msg:
            self.assertIn(msg, str(cm.exception))

    def test_valid_journal_passes(self):
        v = self.ok(self.recs, raw_bytes=self.b["fixture"]["raw"].read_bytes())
        self.assertEqual((v["final"], v["smoke"]["state"]), (6, "passed"))

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
        self.bad(self.mutate(b1, package_digest="e" * 64), "mixed or foreign")
        self.bad(self.mutate(b1, mode="scientific"), "modes")
        recs = copy.deepcopy(self.recs)
        recs[-1]["counts"]["attempts"] += 1
        self.bad(recs, "receipt counters")
        with self.assertRaises(SystemExit):
            J.validate(self.recs[:-1], self.b["sset"], A.DIGEST, **vkw(self.b))      # no receipt: incomplete

    def test_receipt_pins(self):
        b1 = self.idx(lambda r: r["t"] == "begin")
        for k in ("instructions_sha256", "image_sha256", "user_text_sha256"):
            with self.subTest(k):
                recs = copy.deepcopy(self.recs)
                recs[b1]["receipt"][k] = "0" * 64
                self.bad(recs)
        recs = copy.deepcopy(self.recs)
        recs[b1]["receipt"]["extra"] = "x"
        self.bad(recs, "exact prompt-input receipt")

    def test_evidence_required_and_consistent(self):
        e_pf = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "provider_failure")
        e_ok = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "ok")
        recs = copy.deepcopy(self.recs)
        del recs[e_pf]["events"]
        self.bad(recs, "events evidence")                                    # missing failure evidence
        recs = copy.deepcopy(self.recs)
        recs[e_ok]["events"]["length"] += 1
        self.bad(recs, "events evidence")                                    # length/hash against its bytes
        recs = copy.deepcopy(self.recs)
        recs[e_ok]["events"]["sha256"] = "x" * 64
        self.bad(recs, "events evidence")                                    # digest syntax

    def test_contradictory_evidence(self):
        e_ok = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "ok")
        recs = copy.deepcopy(self.recs)
        ev = recs[e_ok]["events"]["text"].replace('"agent_message"', '"command_execution"', 1)
        recs[e_ok]["events"] = R.bounded(ev.encode(), R.EVENTS_KEEP)
        self.bad(recs, "isolation")                                          # ok, but the events show a command
        recs = copy.deepcopy(self.recs)
        recs[e_ok]["file_answer_sha256"] = "0" * 64
        self.bad(recs, "disagree")                                           # -o answer differs
        recs = copy.deepcopy(self.recs)
        e_pf = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "provider_failure")
        recs[e_pf]["outcome"] = "structural_failure"
        recs = recs[:e_pf + 1] + [dict(recs[-1], seq=e_pf + 2)]
        self.bad(recs)                                                       # structural without the pattern

    def test_nonfinite_and_out_of_range(self):
        e_ok = self.idx(lambda r: r["t"] == "end" and r["outcome"] == "ok")
        b1 = self.idx(lambda r: r["t"] == "begin")
        self.bad(self.mutate(e_ok, seconds=float("nan")), "finite")
        self.bad(self.mutate(e_ok, seconds=-1.0), "seconds")
        self.bad(self.mutate(e_ok, seconds=10_000.0), "seconds")
        self.bad(self.mutate(b1, timeout_s=500.0), "timeout_s")
        recs = copy.deepcopy(self.recs)
        recs[-1]["limits"] = {**recs[-1]["limits"], "max_attempts": 999}
        self.bad(recs, "limits")
        recs = copy.deepcopy(self.recs)
        recs[-1]["seconds_total"] = float("inf")
        self.bad(recs, "finite")

    def test_illegal_resumed_transitions(self):
        root = tmp()
        b = A.build(root, {"rq0c": ["noimage"]})
        X.run(fixture=b["fixture"])
        recs, _ = J.read(b["fixture"]["raw"])
        self.assertEqual(recs[-1]["smoke"]["state"], "held")
        body = recs[:-1]
        e = body[-1]                                                         # forge a later request after the hold
        forged = {**next(r for r in body if r["t"] == "begin"), "seq": len(body) + 1, "attempt_no": 2,
                  "attempt_id": "002.x", "request": b["sset"]["delivery_order"][1],
                  "item": next(q["item"] for q in b["sset"]["requests"] if q["request"] ==
                               b["sset"]["delivery_order"][1]),
                  "view": next(q["view"] for q in b["sset"]["requests"] if q["request"] ==
                               b["sset"]["delivery_order"][1]), "try": 1}
        self.assertEqual(e["t"], "end")
        with self.assertRaises(SystemExit) as cm:
            J.validate(body + [forged], b["sset"], A.DIGEST, require_complete=False, **vkw(b))
        self.assertIn("hold", str(cm.exception))

    def test_no_response_needs_three_failures(self):
        root = tmp()
        b = A.build(root, {"rq1c": ["fail"]})
        X.run(fixture=b["fixture"])
        recs, _ = J.read(b["fixture"]["raw"])
        self.assertEqual(J.validate(recs, b["sset"], A.DIGEST, **vkw(b))["outcomes"]["no_response"], 1)


EV = [{"type": "thread.started", "thread_id": "t"}, {"type": "turn.started"},
      {"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": "knife"}},
      {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}]


def evb(evs):
    return ("\n".join(json.dumps(e) for e in evs) + "\n").encode()


class Boundary(unittest.TestCase):
    """Closure 4: parser, lifecycle and classification on synthetic bytes; the real binary without any request."""

    def test_fail_closed(self):
        c = R.classify(b"", b"", None, 1, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "provider_failure")
        c = R.classify(b"", b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")                  # an -o answer without events
        c = R.classify(b"not json\n" + evb(EV), b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")
        tool = [EV[0], {"type": "item.completed", "item": {"id": "c", "type": "command_execution"}}]
        c = R.classify(evb(tool), b"boom", None, 1, timed_out=False, overflow=False)
        self.assertEqual((c["outcome"], c["retained"]), ("isolation_violation", True))
        c = R.classify(evb(EV), b"", "knife", 1, timed_out=False, overflow=False)
        self.assertEqual((c["outcome"], c["answer"]), ("ok", "knife"))
        c = R.classify(evb(EV[:3]), b"", None, None, timed_out=True, overflow=False)
        self.assertEqual((c["outcome"], c["answer"]), ("isolation_violation", "knife"))
        c = R.classify(b"", b"Error loading config: x", None, 1, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "structural_failure")
        c = R.classify(b"", b"Codex could not read the local image at `x`", None, 1, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "structural_failure")

    def test_lifecycle_mutations(self):
        msg2 = {"type": "item.completed", "item": {"id": "m2", "type": "agent_message", "text": "fork"}}
        cases = {
            "completed not last": EV + [{"type": "item.completed", "item": {"id": "r", "type": "reasoning"}}],
            "two terminal events": EV + [EV[-1]],
            "two agent messages": EV[:3] + [msg2] + EV[3:],
            "turn.started twice": EV[:2] + [EV[1]] + EV[2:],
            "thread.started not first": [EV[1], EV[0]] + EV[2:],
            "item without id": EV[:2] + [{"type": "item.completed", "item": {"type": "agent_message", "text": "k"}}] +
                               EV[3:],
            "item completed twice": EV[:3] + [EV[2]] + EV[3:],
            "turn.failed": EV[:3] + [{"type": "turn.failed", "error": {}}] + EV[3:],
            "usage missing": EV[:3] + [{"type": "turn.completed"}],
        }
        for name, evs in cases.items():
            with self.subTest(name):
                c = R.classify(evb(evs), b"", "knife", 0, timed_out=False, overflow=False)
                self.assertEqual(c["outcome"], "isolation_violation", name)

    def test_event_and_file_answers_must_agree(self):
        c = R.classify(evb(EV), b"", "spoon", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")
        self.assertIn("differs from the -o answer", c["isolation_events"][0])
        c = R.classify(evb(EV), b"", None, 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")                  # no -o file

    def test_notices(self):
        notice = {"type": "item.completed", "item": {"id": "n", "type": "error", "message": R.NOTICES[0]}}
        c = R.classify(evb([EV[0], notice] + EV[1:]), b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "ok")
        other = {"type": "item.completed", "item": {"id": "n", "type": "error", "message": "unknown"}}
        c = R.classify(evb([EV[0], other] + EV[1:]), b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "isolation_violation")

    def test_events_beyond_retention_are_overflow(self):
        pad = [{"type": "item.updated", "item": {"id": "r", "type": "reasoning", "text": "x" * 4000}}] * 10
        evs = EV[:2] + [{"type": "item.started", "item": {"id": "r", "type": "reasoning"}}] + pad + \
            [{"type": "item.completed", "item": {"id": "r", "type": "reasoning"}}] + EV[2:]
        c = R.classify(evb(evs), b"", "knife", 0, timed_out=False, overflow=False)
        self.assertEqual(c["outcome"], "overflow")

    def test_no_silent_truncation(self):
        long = "knife " * 500
        evs = EV[:2] + [{"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": long}}] + EV[3:]
        c = R.classify(evb(evs), b"", long, 0, timed_out=False, overflow=False)
        self.assertTrue(c["overlength"])
        self.assertEqual((c["answer_len"], len(c["answer"])), (len(long), R.ANSWER_KEEP))

    def test_pinned_env_and_gate(self):
        e = R.env(Path("/x"))
        self.assertEqual(sorted(e), ["CODEX_HOME", "HOME", "LANG", "PATH", "TMPDIR"])
        self.assertIn('exec "$@" </dev/null', R.gated(["x"])[2])
        argv = R.exec_argv(["codex"], SET["reader"], Path("/a"), Path("/a/w/x.png"), "P")
        self.assertEqual(argv[-4:], ["-i", "/a/w/x.png", "--", "P"])               # the prompt after the separator

    @unittest.skipUnless(HAVE_CODEX, "needs the codex binary")
    def test_allowlist_real_binary(self):
        """The production profile: codex's local subcommands run; reads outside the allowlist and any other program
        are denied. Probe-only addition: /bin/cat and /bin/ls may be executed (their reads are judged by the same
        rules)."""
        root = tmp()
        adir = root / "a"
        R.prepare(adir, A.png(7), "x.png")
        sib = root.parent / (root.name + "_sibling")
        sib.mkdir()
        (sib / "answer.txt").write_text("the paired answer")
        probe = R.profile(adir) + '(allow process-exec (literal "/bin/cat") (literal "/bin/ls"))\n' \
                                  '(allow file-read* (literal "/bin/cat") (literal "/bin/ls"))\n'
        (adir / "probe.sb").write_text(probe)
        for target in (str(KEY_PATH), str(sib / "answer.txt"), str(Path.home() / ".zshrc")):
            rc, out, err = R.run_local(["/bin/cat"], adir, [target], prof="probe.sb")
            self.assertNotEqual(rc, 0, target)
            self.assertIn(b"Operation not permitted", err, target)
        for target in ("/private/tmp", str(Path.home()), str(root.parent)):
            rc, out, err = R.run_local(["/bin/ls"], adir, [target], prof="probe.sb")
            self.assertNotEqual(rc, 0, target)
        rc, out, err = R.run_local(["/bin/cat"], adir, [str(adir / "w" / "x.png")], prof="probe.sb")
        self.assertEqual((rc, out), (0, A.png(7)))                           # its own image is readable
        rc, out, err = R.run_local(["/bin/sh"], adir, ["-c", "echo hi"])     # production profile: no other program
        self.assertNotEqual(rc, 0)
        rc, out, err = R.run_local([str(R.CODEX)], adir, ["--version"])
        self.assertEqual((rc, out.strip()), (0, b"codex-cli 0.159.3"))
        self.assertEqual(R.auth_route([str(R.CODEX)], adir), "Logged in using ChatGPT")

    @unittest.skipUnless(HAVE_CODEX, "needs the codex binary")
    def test_effective_features_and_receipts(self):
        adir = tmp() / "a"
        img = R.prepare(adir, A.png(9), "x.png")
        f = R.effective_features([str(R.CODEX)], SET["reader"], adir)
        self.assertEqual((f["requested_disabled"], f["disabled_effective_false"]), (32, 31))
        self.assertEqual(f["cannot_be_disabled"], {"unified_exec": "true"})
        rc = R.prompt_input([str(R.CODEX)], SET["reader"], adir, img, SET["prompt"])
        self.assertEqual(rc["images"][0]["sha256"], J.sha(A.png(9)))
        self.assertTrue(rc["prompt_rendered"])
        self.assertEqual(rc["instructions_sha256"], json.loads(X.DELIVERY.read_text())["instructions_sha256"])

    @unittest.skipUnless(HAVE_CODEX, "needs the codex binary")
    def test_prompt_separator_regression(self):
        """Measured: without '--' the CLI reads the prompt as a second image path and renders no prompt."""
        adir = tmp() / "a"
        img = R.prepare(adir, A.png(9), "x.png")
        rc, out, err = R.run_local([str(R.CODEX)], adir, ["debug", "prompt-input", *R.flags(SET["reader"]), "-i",
                                                          str(img), SET["prompt"]])
        self.assertEqual(rc, 0)
        self.assertIn(b"could not read the local image", out)
        self.assertNotIn(json.dumps(SET["prompt"])[1:-1].encode(), out.replace(b"could not read", b""))

    @unittest.skipUnless(HAVE_CODEX, "needs the codex binary")
    def test_exec_invocation_receipt(self):
        """The exact exec invocation, network denied by the kernel, synthetic image: its submitted input and its
        sampling-time configuration equal what the receipts show."""
        adir = tmp() / "a"
        img = R.prepare(adir, A.png(9), "x.png")
        r = R.invocation_receipt([str(R.CODEX)], SET["reader"], adir, img, SET["prompt"])
        self.assertTrue(r["equivalent"], r)
        self.assertTrue(r["user_input_exact"])
        self.assertEqual((r["sandbox_policy"], r["approval_policy"]), ("ReadOnly { network_access: false }", "Never"))
        self.assertEqual(r["features_disagreeing"], [])
        self.assertGreaterEqual(r["features_compared"], 100)


class AuditMap(unittest.TestCase):
    """Before-audit condition (Codex RSC 081f17b group 7): the audit map under the uniform specificity rule, its
    construction identities, and the audit scorer bound to the hash pinned in the audit freeze."""

    def test_rule_applied_and_inflections(self):
        import audit_alias_map as M
        m = M.load_frozen()
        c = m["concepts"]
        self.assertNotIn("dress", c["clothes"]["aliases"])
        self.assertNotIn("lid", c["hat"]["aliases"])
        self.assertNotIn("denim", c["jeans"]["aliases"])
        self.assertTrue({"taxis", "taxies", "cab"} <= set(c["taxi"]["aliases"]))
        self.assertEqual(m["shared_admitted_strings"], [])
        self.assertEqual(set(m["construction"]), {"things_sources_sha256", "wordnet", "dev_pool_sha256",
                                                  "ai_reader_key_py_sha256", "audit_alias_map_py_sha256"})
        self.assertEqual(m["construction"]["ai_reader_key_py_sha256"], J.sha((PHOTO / "ai_reader_key.py").read_bytes()))
        self.assertEqual(m["construction"]["audit_alias_map_py_sha256"],
                         J.sha((PHOTO / "audit_alias_map.py").read_bytes()))

    def test_scorer_bound_to_the_pinned_map(self):
        import audit_alias_map as M
        self.assertEqual(M.score("taxi", "Taxis")["code"], "OK_MATCH")
        self.assertEqual(M.score("jeans", "denim")["code"], "ERR_NONMATCH")
        self.assertEqual(M.score("hat", "a hat\nwith a brim")["code"], "ERR_EXPLANATORY")
        d = tmp()
        shutil.copyfile(M.MAP, d / "map.json")
        with open(d / "map.json", "a") as fh:
            fh.write(" ")
        old = M.MAP
        M.MAP = d / "map.json"
        try:
            with self.assertRaisesRegex(SystemExit, "differs from the frozen map"):
                M.score("taxi", "taxi")
        finally:
            M.MAP = old

    def test_freeze_states_the_current_rule(self):
        t = (PHOTO.parents[1] / "audit_app" / "IMAGE_AUDIT_FREEZE.md").read_text()
        self.assertIn("61 of the 63", t)
        self.assertNotIn("59 of the 61", t)


class Executor(unittest.TestCase):
    """Closures 3-5 in fixture mode (in-process; hard kills are in test_ai_reader_crash.py)."""

    def run_fx(self, plan, setup=None, **over):
        root = tmp()
        b = A.build(root, plan)
        if setup:
            setup(root, b)
        saved = {k: getattr(X, k) for k in over if k != "LIMITS"}
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
        self.assertEqual((calls.count("rq1c"), calls.count("rq2c"), calls.count("rq0g")), (3, 1, 1))
        J.validate(recs, b["sset"], A.DIGEST, **vkw(b))

    def test_smoke_holds(self):
        for plan, want in (({"rq0c": ["structural"]}, "structural"), ({"rq0c": ["noimage"]}, "no image"),
                           ({"rq0c": ["fail"]}, "no answer in three"),
                           ({"rq0c": ["fail", "noimage"]}, "no image"),                 # try 2, not attempt 1
                           ({"rq0c": ["tool"]}, "isolation"), ({"rq0c": ["quickflood"]}, "overflow")):
            with self.subTest(str(plan)):
                out, recs, root, b = self.run_fx(plan)
                self.assertEqual(out["outcome"], "STOPPED")
                self.assertIn(want, out["reason"])
                self.assertEqual({d["request"] for d in A.dispatches(root)}, {"rq0c"})   # nothing after the hold
                self.assertEqual(out["smoke"]["state"], "held")

    def test_structural_later_holds(self):
        out, recs, root, b = self.run_fx({"rq1c": ["structural"]})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("structural", out["reason"])
        self.assertNotIn("rq2c", [d["request"] for d in A.dispatches(root)])

    def test_notice_is_bookkeeping_unknown_error_is_isolation(self):
        out, recs, root, b = self.run_fx({"rq1c": ["notice:thing"], "rq2c": ["unknown_error:thing"]})
        e = {r["request"]: r["outcome"] for r in self.ends(recs)}
        self.assertEqual((e["rq1c"], e["rq2c"]), ("ok", "isolation_violation"))

    def test_attempt_cap_writes_final_then_stops(self):
        out, recs, root, b = self.run_fx({"rq1c": ["fail"]}, LIMITS={"max_attempts": 4})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("attempt cap", out["reason"])
        self.assertEqual([r["request"] for r in recs if r["t"] == "final"], ["rq1c"])
        J.validate(recs, b["sset"], A.DIGEST, require_complete=False, **{**vkw(b), "limits": None})

    def test_clock_stops_inside_reserve(self):
        out, recs, root, b = self.run_fx({}, LIMITS={"job_clock_s": X.FINAL_S + X.MIN_ATTEMPT_S - 1})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("job clock", out["reason"])
        self.assertFalse([r for r in recs if r["t"] == "begin"])

    def test_timeout_kills_and_reaps_the_group(self):
        out, recs, root, b = self.run_fx({"rq1c": ["block", "ok:thing"]}, LIMITS={"attempt_timeout_s": 2})
        e = next(r for r in self.ends(recs) if r["request"] == "rq1c")
        self.assertEqual((e["outcome"], e["kill"]["how"]), ("provider_failure", "SIGKILL"))
        self.assertLess(e["kill"]["kill_to_reap_s"], X.TERM_GRACE_S + 1.5)
        pid = next(d["pid"] for d in A.dispatches(root) if d["behaviour"] == "block")
        self.assertIsNone(memprobe.proc_info(pid))

    def test_leader_exit_leaves_no_child(self):
        out, recs, root, b = self.run_fx({"rq1c": ["orphanchild:thing"]})
        child = int((root / "orphan.pid").read_text())
        self.assertIsNone(memprobe.proc_info(child), "a child outlived its leader's ordinary exit")
        self.assertEqual(out["outcome"], "COMPLETE")

    def test_overflow_retained_including_quick_exit(self):
        out, recs, root, b = self.run_fx({"rq1c": ["flood"], "rq2c": ["quickflood"]})
        for rq in ("rq1c", "rq2c"):
            e = next(r for r in self.ends(recs) if r["request"] == rq)
            self.assertEqual((e["outcome"], e["retained"]), ("overflow", True), rq)
            self.assertLessEqual(len(json.dumps(e)), J.MAX_RECORD)

    def test_raw_cap_stops(self):
        out, recs, root, b = self.run_fx({}, LIMITS={"raw_bytes": 3 * J.MAX_RECORD + X.RAW_FINAL_BYTES + 2000})
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("raw output", out["reason"])

    def test_receipt_mismatch_holds_before_sending(self):
        for field in ("image_sha256", "user_text_sha256"):
            with self.subTest(field):
                def setup(root, b, f=field):
                    b["fixture"]["delivery"]["requests"]["rq0c"][f] = "0" * 64
                out, recs, root, b = self.run_fx({}, setup=setup)
                self.assertEqual(out["outcome"], "STOPPED")
                self.assertIn("nothing sent", out["reason"])
                self.assertEqual(A.dispatches(root), [])
                self.assertEqual(list((root / "attempts").iterdir()), [])     # no directory left behind

    def test_failed_receipt_setup_stops_with_a_receipt(self):
        def setup(root, b):
            (root / "PROMPT_FAIL").write_text("1")
        out, recs, root, b = self.run_fx({}, setup=setup)
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn("prompt-input receipt failed", out["reason"])
        self.assertEqual(recs[-1]["t"], "receipt")
        self.assertEqual(list((root / "attempts").iterdir()), [])

    def test_stop_during_open_attempt_reconciles_first(self):
        real = J.append
        state = {"n": 0}

        def flaky(path, rec, cap=None):
            if rec.get("t") == "dispatched" and state["n"] == 0:
                state["n"] += 1
                raise J.RawCap("fixture: raw cap at the dispatch record")
            return real(path, rec, cap)
        J.append = flaky
        try:
            out, recs, root, b = self.run_fx({"rq0c": ["slow_ok:2:thing"]})
        finally:
            J.append = real
        self.assertEqual(out["outcome"], "STOPPED")
        types = [r["t"] for r in recs]
        self.assertEqual(types[-3:], ["recovered", "end", "receipt"])          # reconciled before the receipt
        self.assertEqual(recs[-2]["outcome"], "not_dispatched")
        J.validate(recs, b["sset"], A.DIGEST, **{**vkw(b), "limits": X.LIMITS}, require_complete=False)

    def test_lost_and_inconsistent_accounting_refused(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        raw = b["fixture"]["raw"]
        raw.write_bytes(b"".join(raw.read_bytes().splitlines(keepends=True)[:-1]))
        clock = b["fixture"]["job"] / "clock.json"
        c = json.loads(clock.read_text())
        clock.unlink()
        with self.assertRaisesRegex(SystemExit, "accumulated time is lost"):
            X.run(fixture=b["fixture"])
        clock.write_text(json.dumps({**c, "seconds_total": 0.0, "open_session": None}))
        recs, _ = J.read(raw)
        body = [dict(r, seconds=500.0) if r["t"] == "end" else r for r in recs]
        raw.write_bytes(b"".join((json.dumps(r, sort_keys=True) + "\n").encode() for r in body))
        with self.assertRaisesRegex(SystemExit, "inconsistent accounting"):
            X.run(fixture=b["fixture"])

    def test_clock_beats_without_the_main_thread(self):
        d = tmp()
        c = X.Clock(d / "clock.json", time.monotonic(), 100.0)
        time.sleep(2.5)                                                       # the main thread does nothing
        live = json.loads((d / "clock.json").read_text())["open_session"]["live_s"]
        c.close("test")
        self.assertGreaterEqual(live, 1.5)

    def test_pending_quarantine_recorded(self):
        root = tmp()
        b = A.build(root, {})
        q = b["fixture"]["job"] / "quarantine"
        q.mkdir(parents=True)
        (q / "tail_000009_abcdefabcdef.bin").write_bytes(b'{"t": "end", "seq')   # truncated, record never written
        X.run(fixture=b["fixture"])
        recs, _ = J.read(b["fixture"]["raw"])
        self.assertEqual([r["quarantine"] for r in recs if r["t"] == "tail_repair"], ["tail_000009_abcdefabcdef.bin"])

    def test_resumed_journal_validated_before_dispatch(self):
        root = tmp()
        b = A.build(root, {})
        X.run(fixture=b["fixture"])
        raw = b["fixture"]["raw"]
        recs, _ = J.read(raw)
        body = recs[:-1]
        i = next(k for k, r in enumerate(body) if r["t"] == "end" and r["outcome"] == "ok")
        body[i]["answer"] = "edited"
        raw.write_bytes(b"".join((json.dumps(r, sort_keys=True) + "\n").encode() for r in body))
        n = len(A.dispatches(root))
        with self.assertRaisesRegex(SystemExit, "edited"):
            X.run(fixture=b["fixture"])
        self.assertEqual(len(A.dispatches(root)), n)                          # nothing dispatched


if __name__ == "__main__":
    unittest.main()
