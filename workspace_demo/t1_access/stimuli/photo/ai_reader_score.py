"""AI image-reader qualification, revision 2: the mechanical SCORER (orchestrator side; the reader never sees it).
Framework §8.2 reader rule (R052, 2 Oct); Codex RSC cf3e49e; R052 handoff 7f25830e repairs 1, 2, 4 and 7.
Standard library only.

    python3 stimuli/photo/ai_reader_score.py <raw_responses.jsonl>      # refuses unless the raw file is committed

PRIMARY SCORE. An answer is correct only when its WHOLE normalised text equals one of the item's frozen admissible
aliases (`ai_reader_key.normalise`, `ai_reader_qual_key.json`). Every other outcome is an ERROR and stays in the
denominator, with a reason code, in this order:
  ERR_NO_RESPONSE     no answer was obtained within the job's attempt limits (provider failures only)
  ERR_ISOLATION       the reader used a tool, file or web access in that request (the executor's event check)
  ERR_EMPTY           nothing left after normalisation
  ERR_UNCLEAR         the answer is exactly 'unclear' (the permitted abstention - an error, never excluded)
  ERR_MULTIPLE        more than one name ('x or y', 'x, y', 'x/y', 'x and y', 'x; y')
  ERR_EXPLANATORY     more than five words, or sentence punctuation inside the answer
  ERR_MALFORMED       characters other than letters, digits, spaces and apostrophes
  ERR_NONMATCH        a well-formed name that is not an admissible alias
Broad 'close' credit (an alias appearing as a whole-word run inside the answer) is reported as a DESCRIPTIVE column
only and never enters a gate.

COMPLETENESS (repair 4). The raw file must hold exactly one RETAINED response for each of the 600 declared
(item, view) requests - no more, no fewer; a duplicate retained response, an unknown request id or view, or a
request's item/view disagreeing with the set is a refusal, not a warning. Provider-failure attempts are listed and
counted but never scored.

ADMISSION (R052's rule in §8.2, fixed before any answer). Whole-answer admissible naming accuracy on the EASY items
(human recognizability >= 0.8) on the GRAYSCALE canvas as delivered; the reader is admitted iff the one-sided exact
(Clopper-Pearson) 95 % lower bound on that proportion is >= 0.90. With 63 easy items after the frame repair
(revision 1 had 61) that is 61 of 63 or better (`required_successes`). Nothing else gates.
DESCRIPTIVE (no claim): colour accuracy on the same items as the human-reference diagnostic, the paired colour/gray
table with discordant counts, full-panel and per-stratum rows with their denominators (an empty stratum reports n = 0
and accuracy null, never NaN), and Q1 - reader colour accuracy beside the human mean recognizability - with no
equivalence reading.

REFERRAL RECORDS (repair 7). Every grayscale item not answered correctly becomes a record with: opaque item and
view, intended concept and THINGS sense, human proportion and rating count, image hash, prompt hash, model identity,
the unedited raw answer and the question order, the frozen score and reason code, and empty fields for the owner's
dated evidence, decision and disposition. AI-passed and owner-adjudicated items are reported separately; an owner
decision never adds an alias and never changes the qualification score.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ai_reader_key import KEY, normalise  # noqa: E402

SET = HERE / "ai_reader_qual_set.json"
LOWER_BOUND, CONF = 0.90, 0.95


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


def classify(raw: str | None, aliases: list[str], status: str = "ok") -> tuple[str, bool]:
    """(reason code, descriptive close). 'OK_MATCH' is the only correct outcome."""
    if status == "isolation_violation":
        return "ERR_ISOLATION", False
    if status != "ok" or raw is None:
        return "ERR_NO_RESPONSE", False
    n = normalise(raw)
    close = any(re.search(r"(^| )" + re.escape(a) + r"( |$)", n) for a in aliases) if n else False
    if n in aliases:
        return "OK_MATCH", True
    if not n:
        return "ERR_EMPTY", False
    if n == "unclear":
        return "ERR_UNCLEAR", False
    if re.search(r"\b(or|and)\b|[,/;&]", n):
        return "ERR_MULTIPLE", close
    if len(n.split()) > 5 or re.search(r"[.!?:]", n) or "\n" in raw.strip():
        return "ERR_EXPLANATORY", close
    if not re.fullmatch(r"[a-z0-9' ]+", n):
        return "ERR_MALFORMED", close
    return "ERR_NONMATCH", close


def retained(raw_path: Path, sset: dict) -> dict:
    """{request_id: record} with exactly one retained response per declared request, or a refusal."""
    want = {r["request"]: r for r in sset["requests"]}
    got, failures = {}, []
    for line in raw_path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        rq = rec.get("request")
        if rq not in want:
            raise SystemExit(f"refused: unknown request id {rq!r}")
        if (rec.get("item"), rec.get("view")) != (want[rq]["item"], want[rq]["view"]):
            raise SystemExit(f"refused: request {rq} names item/view {rec.get('item')}/{rec.get('view')}")
        if rec.get("retained"):
            if rq in got:
                raise SystemExit(f"refused: duplicate retained response for {rq}")
            got[rq] = rec
        else:
            failures.append(rec)
    missing = sorted(set(want) - set(got))
    if missing:
        raise SystemExit(f"refused: {len(missing)} of {len(want)} requests have no retained response "
                         f"(first: {missing[:3]}); no verdict on an incomplete file")
    return {"retained": got, "failures": failures}


def rate(rows: list[bool]) -> dict:
    return {"n": len(rows), "correct": sum(rows), "accuracy": (sum(rows) / len(rows)) if rows else None}


def score(raw_path: Path, *, require_committed: bool = True) -> dict:
    if require_committed:
        rel = str(raw_path.resolve())
        ls = subprocess.run(["git", "-C", str(HERE), "ls-files", "--error-unmatch", rel], capture_output=True)
        dirty = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "--", rel], capture_output=True,
                               text=True).stdout.strip()
        if ls.returncode != 0 or dirty:
            raise SystemExit("refused: commit the raw responses before scoring (raw answers are locked first)")
    sset = json.loads(SET.read_text())
    key = json.loads(KEY.read_text())
    r = retained(raw_path, sset)
    rows = {}
    for rq, rec in r["retained"].items():
        k = key["items"][rec["item"]]
        code, close = classify(rec.get("answer"), k["aliases"], rec.get("status", "ok"))
        rows[rq] = {"item": rec["item"], "view": rec["view"], "code": code, "correct": code == "OK_MATCH",
                    "close_descriptive": close, "raw": rec.get("answer"), "stratum": k["stratum"], "easy": k["easy"]}
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
                              "human_n_ratings": k["human"]["n_ratings"],
                              "image_sha256": next(r["sha256"] for r in sset["requests"]
                                                   if r["item"] == i and r["view"] == "gray"),
                              "prompt_sha256": sset["prompt_sha256"], "model": sset["reader"],
                              "raw_answer": g["raw"], "question_order": ["free_name"], "score": g["code"],
                              "reason": g["code"], "owner_evidence": None, "owner_decision": None,
                              "owner_date": None, "disposition": None})
    out = {"admission": {"rule": f"gray easy whole-answer accuracy, one-sided exact {int(CONF * 100)}% lower bound "
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
           "reason_codes": codes, "provider_failures": len(r["failures"]),
           "referrals": referrals, "referral_count": len(referrals)}
    return out


if __name__ == "__main__":
    print(json.dumps(score(Path(sys.argv[1])), indent=1))
