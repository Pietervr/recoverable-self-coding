"""AI image-reader qualification, revision 4: the mechanical SCORER (orchestrator side; the reader never sees it).
Framework §8.2 reader rule; Codex RSC cf3e49e and 7048bb8; R052 handoffs 7f25830e repairs 1, 2, 4, 7 and 742146ad
groups 1 and 6; RSC 5a8d7ac closures 1 and 6. Standard library only.

    python3 stimuli/photo/ai_reader_score.py <raw_responses.jsonl>

ADMISSION OF THE RAW FILE (groups 1 and 6), before any score: the file is tracked and clean in git and its bytes equal
the committed blob (its sha256 and the commit are carried into the output and every referral); the journal passes the
complete validator (ai_reader_journal.validate: schema, statuses, ordering, attempts, counters, caps, unique attempt
ids, delivery order, first-answer ordering, bounded and unedited answers, a COMPLETE receipt); the package recomputed
now (key, set, this scorer and every other bound file, the binary and runtime) equals the package digest in every
journal record and the package the go approved (stage_a_guard.require_go, row aireader), and the journal's receipts
equal that package's instruction pin and the frozen delivery. In SCIENTIFIC mode the key, the set and the package are
ALWAYS the approved objects loaded and recomputed here: a caller-supplied key, set or package is refused (only the
labelled synthetic mode accepts injected objects). A synthetic-fixture journal is refused unless
`allow_synthetic=True`, and then the output is labelled as not a qualification result.

PRIMARY SCORE. Codes, in this precedence (format before matching - a multi-line, over-length or malformed answer is
an error even when its normalised text would equal an alias):
  ERR_ISOLATION       the reader used a tool, file or web access, or its event evidence was malformed or incomplete
  ERR_OVERLENGTH      the answer exceeded 2,000 characters, or the worker's output crossed its cap
  ERR_INTERRUPTED     the attempt was dispatched and a crash lost its outcome (recovery's conservative rule)
  ERR_NO_RESPONSE     no answer was obtained within the job's attempt limits
  ERR_EXPLANATORY     more than one line, more than five words, or sentence punctuation inside the answer
  ERR_MALFORMED       control characters, or characters other than letters, digits, spaces and apostrophes
  ERR_EMPTY           nothing left after normalisation
  ERR_UNCLEAR         exactly 'unclear' (the permitted abstention - an error, never excluded)
  ERR_MULTIPLE        more than one name ('x or y', 'x, y', 'x/y', 'x and y', 'x; y', 'x & y')
  OK_MATCH            the WHOLE normalised answer equals one of the item's frozen admissible aliases
  ERR_NONMATCH        a well-formed name that is not an admissible alias
No admissible alias trips a format check (tested over the key: at most three words, letters, digits, spaces and
apostrophes, no 'and'/'or'). Broad 'close' credit (an alias as a whole-word run inside the answer) is a DESCRIPTIVE
column only and never enters a gate.

COMPLETENESS. Exactly one retained outcome for each of the 600 declared requests (the validator's COMPLETE receipt).

ADMISSION (R052's rule in §8.2, fixed before any answer). Whole-answer admissible naming accuracy on the EASY items
(human recognizability >= 0.8) on the GRAYSCALE canvas as delivered; admitted iff the one-sided exact (Clopper-Pearson)
95 % lower bound is >= 0.90: with 63 easy items, 61 of 63 or better (`required_successes`). Nothing else gates.
DESCRIPTIVE (no claim): colour accuracy, the paired colour/gray table with discordant counts, full-panel and
per-stratum rows with denominators (an empty stratum reports n = 0 and accuracy null), Q1 beside the human mean.

REFERRAL RECORDS. Every grayscale item not answered correctly: opaque item and view, intended concept, THINGS sense
and synset, human proportion and rating count, the delivered image digest and the attempt id from the executed
request's receipt, the prompt hash and reader identity, the unedited raw answer with its length and sha256, the
question order, the frozen code, the raw file's sha256 and commit, the package digest and the key, set and scorer
hashes, and empty fields for the owner's dated evidence, decision and disposition. An owner decision never adds an
alias and never changes the qualification score.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_journal as J  # noqa: E402
from ai_reader_key import KEY, normalise  # noqa: E402

SET = HERE / "ai_reader_qual_set.json"
LOWER_BOUND, CONF = 0.90, 0.95
STATUS_CODES = {"isolation_violation": "ERR_ISOLATION", "overflow": "ERR_OVERLENGTH",
                "interrupted": "ERR_INTERRUPTED", "no_response": "ERR_NO_RESPONSE"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def binom_tail_ge(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))


def cp_lower(k: int, n: int, conf: float = CONF) -> float:
    """One-sided exact lower bound: the p at which P(X >= k | n, p) = 1 - conf (0 when k = 0)."""
    if n == 0 or k == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if binom_tail_ge(k, n, mid) < 1 - conf:
            lo = mid
        else:
            hi = mid
    return lo


def required_successes(n: int) -> int | None:
    for k in range(n + 1):
        if cp_lower(k, n) >= LOWER_BOUND:
            return k
    return None


def classify(raw: str | None, aliases: list[str], status: str = "ok", overlength: bool = False) -> tuple[str, bool]:
    """(reason code, descriptive close). 'OK_MATCH' is the only correct outcome."""
    if status in STATUS_CODES:
        return STATUS_CODES[status], False
    if overlength:
        return "ERR_OVERLENGTH", False
    if status != "ok" or raw is None:
        return "ERR_NO_RESPONSE", False
    n = normalise(raw)
    close = any(re.search(r"(^| )" + re.escape(a) + r"( |$)", n) for a in aliases) if n else False
    if re.search(r"[\r\n  ]", raw.strip()):
        return "ERR_EXPLANATORY", close
    if any((ord(ch) < 32 and ch != "\t") or 127 <= ord(ch) < 160 for ch in raw.strip()):
        return "ERR_MALFORMED", close
    if not n:
        return "ERR_EMPTY", False
    if n == "unclear":
        return "ERR_UNCLEAR", False
    if re.search(r"\b(or|and)\b|[,/;&]", n):
        return "ERR_MULTIPLE", close
    if len(n.split()) > 5 or re.search(r"[.!?:]", n):
        return "ERR_EXPLANATORY", close
    if not re.fullmatch(r"[a-z0-9' ]+", n):
        return "ERR_MALFORMED", close
    if n in aliases:
        return "OK_MATCH", True
    return "ERR_NONMATCH", close


def committed(raw_path: Path) -> dict:
    """The raw file must be tracked, clean and byte-equal to the committed blob."""
    p = raw_path.resolve()
    top = subprocess.run(["git", "-C", str(p.parent), "rev-parse", "--show-toplevel"], capture_output=True,
                         text=True)
    if top.returncode != 0:
        raise SystemExit("refused: the raw file is not in a git repository")
    rel = str(p.relative_to(Path(top.stdout.strip()).resolve()))
    ls = subprocess.run(["git", "-C", top.stdout.strip(), "ls-files", "--error-unmatch", rel], capture_output=True)
    dirty = subprocess.run(["git", "-C", top.stdout.strip(), "status", "--porcelain", "--", rel], capture_output=True,
                           text=True).stdout.strip()
    if ls.returncode != 0 or dirty:
        raise SystemExit("refused: commit the raw responses before scoring (raw answers are locked first)")
    blob = subprocess.run(["git", "-C", top.stdout.strip(), "show", f"HEAD:{rel}"], capture_output=True).stdout
    data = p.read_bytes()
    if sha(blob) != sha(data):
        raise SystemExit("refused: the raw file differs from its committed blob")
    commit = subprocess.run(["git", "-C", top.stdout.strip(), "log", "-1", "--format=%H", "--", rel],
                            capture_output=True, text=True).stdout.strip()
    return {"raw_sha256": sha(data), "raw_commit": commit, "bytes": data}


def admit(raw_path: Path, sset: dict, *, package: dict | None, allow_synthetic: bool, go: Path | None,
          delivery: dict | None = None) -> dict:
    """Groups 1 and 6: committed raw, complete validation, approved package."""
    if not allow_synthetic and package is not None:
        raise SystemExit("refused: scientific scoring recomputes the package; a caller-supplied package is refused")
    if allow_synthetic:
        data = raw_path.read_bytes()
        info = {"raw_sha256": sha(data), "raw_commit": None, "bytes": data}
    else:
        info = committed(raw_path)
    recs, tail = J.read(raw_path)
    if tail:
        raise SystemExit("refused: the raw file ends in an incomplete line")
    digest = recs[0].get("package_digest") if recs else None
    if not allow_synthetic:
        import ai_reader_exec as X
        import stage_a_guard
        pkg = X.package()
        if digest != pkg["package_digest"]:
            raise SystemExit("refused: the journal's package digest is not the package recomputed now")
        stage_a_guard.NEGATIVE_REVIEWS = stage_a_guard.NEGATIVE_REVIEWS | X.NEGATIVE
        stage_a_guard.require_go(go or X.GO, pkg, row="aireader", stage="qualification",
                                 verify_at_commit=X.package_at_commit)
    if allow_synthetic:
        v = J.validate(recs, sset, digest, raw_bytes=info["bytes"], require_complete=True, mode="synthetic-fixture",
                       delivery=delivery, instructions_sha256=(delivery or {}).get("instructions_sha256"))
    else:
        import ai_reader_exec as X
        deliv = json.loads(X.DELIVERY.read_text())
        v = J.validate(recs, sset, digest, raw_bytes=info["bytes"], require_complete=True, mode="scientific",
                       delivery=deliv, instructions_sha256=pkg["instructions_sha256"], limits=X.LIMITS)
    begins = {r["attempt_id"]: r for r in recs if r["t"] == "begin"}
    return {**info, "validation": v, "records": recs, "begins": begins, "package_digest": digest}


def rate(rows: list[bool]) -> dict:
    return {"n": len(rows), "correct": sum(rows), "accuracy": (sum(rows) / len(rows)) if rows else None}


def score(raw_path: Path, *, allow_synthetic: bool = False, package: dict | None = None, go: Path | None = None,
          sset: dict | None = None, key: dict | None = None, delivery: dict | None = None) -> dict:
    if not allow_synthetic and (sset is not None or key is not None or package is not None or delivery is not None):
        raise SystemExit("refused: scientific scoring uses only the approved key, set, delivery and package; "
                         "injected objects are accepted in labelled synthetic mode only")
    sset = sset or json.loads(SET.read_text())
    key_bytes = KEY.read_bytes()
    key = key or json.loads(key_bytes)
    if not allow_synthetic and sha(key_bytes) != sset.get("key_sha256"):
        raise SystemExit("refused: the key's sha256 differs from the set's key_sha256")
    a = admit(raw_path, sset, package=package, allow_synthetic=allow_synthetic, go=go, delivery=delivery)
    ident = {"raw_sha256": a["raw_sha256"], "raw_commit": a["raw_commit"], "package_digest": a["package_digest"],
             "key_sha256": sha(key_bytes), "set_sha256": sha(SET.read_bytes()),
             "scorer_sha256": sha(Path(__file__).read_bytes())}
    final = {}
    for r in a["records"]:
        if (r["t"] == "end" and r["retained"]) or r["t"] == "final":
            final[r["request"]] = r
    reqs = {r["request"]: r for r in sset["requests"]}
    rows = {}
    for rq, rec in final.items():
        item, view = reqs[rq]["item"], reqs[rq]["view"]
        k = key["items"][item]
        status = rec["outcome"]
        code, close = classify(rec.get("answer"), k["aliases"], status, bool(rec.get("overlength")))
        b = a["begins"].get(rec.get("attempt_id"), {})
        rows[rq] = {"item": item, "view": view, "code": code, "correct": code == "OK_MATCH",
                    "close_descriptive": close, "raw": rec.get("answer"), "answer_len": rec.get("answer_len"),
                    "answer_sha256": rec.get("answer_sha256"), "attempt_id": rec.get("attempt_id"),
                    "delivered_sha256": (b.get("receipt") or {}).get("image_sha256"),
                    "stratum": k["stratum"], "easy": k["easy"]}
    by_item = {}
    for v in rows.values():
        by_item.setdefault(v["item"], {})[v["view"]] = v
    items = sorted(by_item)

    def view_rows(view, pred=lambda i: True):
        return [by_item[i][view]["correct"] for i in items if pred(i)]
    easy = lambda i: key["items"][i]["easy"]
    g_easy = view_rows("gray", easy)
    k_req = required_successes(len(g_easy))
    lb = cp_lower(sum(g_easy), len(g_easy))
    paired = {}
    for name, pred in (("all", lambda i: True), ("easy", easy)):
        both = sum(1 for i in items if pred(i) and by_item[i]["colour"]["correct"] and by_item[i]["gray"]["correct"])
        c_only = sum(1 for i in items if pred(i) and by_item[i]["colour"]["correct"] and not by_item[i]["gray"]["correct"])
        g_only = sum(1 for i in items if pred(i) and not by_item[i]["colour"]["correct"] and by_item[i]["gray"]["correct"])
        neither = sum(1 for i in items if pred(i)) - both - c_only - g_only
        paired[name] = {"both": both, "colour_only": c_only, "gray_only": g_only, "neither": neither,
                        "discordant": c_only + g_only}
    human_mean = sum(key["items"][i]["human"]["recognizability"] for i in items) / len(items)
    codes = {}
    for v in rows.values():
        codes.setdefault(v["view"], {}).setdefault(v["code"], 0)
        codes[v["view"]][v["code"]] += 1
    referrals = []
    for i in items:
        g = by_item[i]["gray"]
        if not g["correct"]:
            k = key["items"][i]
            referrals.append({"item": i, "view": "gray", "concept": k["concept"], "sense": k["sense"],
                              "synset": k["synset"], "human_recognizability": k["human"]["recognizability"],
                              "human_n_ratings": k["human"]["n_ratings"], "attempt_id": g["attempt_id"],
                              "delivered_image_sha256": g["delivered_sha256"],
                              "prompt_sha256": sset["prompt_sha256"], "model": sset["reader"],
                              "raw_answer": g["raw"], "answer_len": g["answer_len"], "answer_sha256": g["answer_sha256"],
                              "question_order": ["free_name"], "score": g["code"], "reason": g["code"], **ident,
                              "owner_evidence": None, "owner_decision": None, "owner_date": None, "disposition": None})
    out = {"identity": ident, "mode": a["validation"]["mode"],
           "admission": {"rule": f"gray easy whole-answer accuracy, one-sided exact {int(CONF * 100)}% lower bound "
                                 f">= {LOWER_BOUND}", "easy_n": len(g_easy), "easy_correct": sum(g_easy),
                         "required_successes": k_req, "lower_bound": lb, "admitted": lb >= LOWER_BOUND},
           "descriptive": {
               "colour_easy": rate(view_rows("colour", easy)), "gray_easy": rate(g_easy),
               "colour_all": rate(view_rows("colour")), "gray_all": rate(view_rows("gray")),
               "by_stratum": {view: {s: rate(view_rows(view, lambda i, s=s: key["items"][i]["stratum"] == s))
                                     for s in (0, 1, 2)} for view in ("colour", "gray")},
               "paired": paired,
               "close_descriptive": {view: rate([by_item[i][view]["close_descriptive"] for i in items])
                                     for view in ("colour", "gray")},
               "Q1_colour_accuracy_beside_human_mean": [rate(view_rows("colour"))["accuracy"], human_mean],
               "Q1_note": "descriptive only: a menu-choice human norm is not a free-naming measure"},
           "reason_codes": codes, "attempts": a["validation"]["attempts"],
           "outcomes": a["validation"]["outcomes"], "referrals": referrals, "referral_count": len(referrals)}
    if out["mode"] != "scientific":
        out = {"WARNING": "SYNTHETIC FIXTURE - NOT A QUALIFICATION RESULT", **out}
        out["admission"]["admitted"] = None
        out["admission"]["synthetic_would_admit"] = lb >= LOWER_BOUND
    return out


if __name__ == "__main__":
    print(json.dumps(score(Path(sys.argv[1])), indent=1))
