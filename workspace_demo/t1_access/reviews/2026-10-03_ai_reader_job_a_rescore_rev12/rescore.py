"""RE-ANALYSIS, NOT ADMISSION. Job (a) of 2 October 2026 (journal committed at RSC 0baec65, scored NOT ADMITTED under
its frozen whole-answer rule, reviews/2026-10-02_ai_reader_job_a.md) re-scored under revision 12's shared matching rule
(ai_reader_key.names_concept) - for the owner's information only (R052 handoff ff264083, item G). Outside scientific
mode: it reads the journal's retained answers and the frozen key directly; it does not admit the journal against a
package (job (a) ran under the revision-11 package, its prompt and its rule), does not touch the go, and its numbers
never decide admission. Job (a)'s verdict stays NOT ADMITTED.

    .venv-build/bin/python reviews/2026-10-03_ai_reader_job_a_rescore_rev12/rescore.py \
        <job (a) journal> > reviews/2026-10-03_ai_reader_job_a_rescore_rev12/rescore.json

The journal is read from the path given (job (a)'s journal; at RSC 0baec65 it is
stimuli/photo/ai_reader_raw_responses.jsonl); its sha256 must equal job (a)'s.
"""
import hashlib
import json
import sys
from pathlib import Path

T1 = Path(__file__).resolve().parents[2]
PHOTO = T1 / "stimuli" / "photo"
sys.path.insert(0, str(PHOTO))
import ai_reader_journal as J  # noqa: E402
import ai_reader_key as K  # noqa: E402
import ai_reader_score as S  # noqa: E402

JOB_A_SHA = "b8c8bf4f"          # job (a)'s journal sha256 prefix (reviews/2026-10-02_ai_reader_job_a.md)


def main(raw: Path) -> int:
    data = raw.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if not digest.startswith(JOB_A_SHA):
        raise SystemExit(f"refused: {raw} is not job (a)'s journal ({digest[:12]})")
    recs, tail = J.read(raw)
    if tail:
        raise SystemExit("refused: incomplete last line")
    sset = json.loads(S.SET.read_text())
    key = json.loads(K.KEY.read_text())
    reqs = {r["request"]: r for r in sset["requests"]}
    final = {r["request"]: r for r in recs if (r["t"] == "end" and r.get("retained")) or r["t"] == "final"}
    if len(final) != 600:
        raise SystemExit(f"refused: {len(final)} final outcomes, not 600")
    rows = {}
    for rq, rec in final.items():
        item, view = reqs[rq]["item"], reqs[rq]["view"]
        k = key["items"][item]
        raw_answer = rec.get("answer")
        code, _, rule = S.classify_detail(raw_answer, k, rec["outcome"], bool(rec.get("overlength")), k["concept"])
        n = K.normalise(raw_answer or "")
        old = code != "ERR_MALFORMED" and S.correct(code) and n in k["aliases"]      # revision 11: whole as given
        rows[(item, view)] = {"item": item, "view": view, "concept": k["concept"], "easy": k["easy"],
                              "stratum": k["stratum"], "human": k["human"]["recognizability"], "raw": raw_answer,
                              "code": code, "rule": rule, "correct": S.correct(code), "rev11_correct": old}

    def count(view, pred=lambda r: True, field="correct"):
        sel = [r for (i, v), r in rows.items() if v == view and pred(r)]
        return {"n": len(sel), "correct": sum(r[field] for r in sel)}
    easy = lambda r: r["easy"]
    out = {"LABEL": "RE-ANALYSIS - NOT A QUALIFICATION RESULT, NEVER ADMISSION (job (a) stays NOT ADMITTED)",
           "journal_sha256": digest, "key_sha256": hashlib.sha256(K.KEY.read_bytes()).hexdigest(),
           "ai_reader_key_py_sha256": hashlib.sha256((PHOTO / "ai_reader_key.py").read_bytes()).hexdigest(),
           "ai_reader_score_py_sha256": hashlib.sha256((PHOTO / "ai_reader_score.py").read_bytes()).hexdigest(),
           "rev11_reproduced": {"gray_easy": count("gray", easy, "rev11_correct"),
                                "gray_all": count("gray", field="rev11_correct"),
                                "colour_all": count("colour", field="rev11_correct")},
           "rev12": {"gray_easy": count("gray", easy), "colour_easy": count("colour", easy),
                     "gray_all": count("gray"), "colour_all": count("colour"),
                     "gray_by_stratum": {s: count("gray", lambda r, s=s: r["stratum"] == s) for s in (0, 1, 2)},
                     "colour_by_stratum": {s: count("colour", lambda r, s=s: r["stratum"] == s) for s in (0, 1, 2)}},
           "rev12_codes": {v: {} for v in ("gray", "colour")},
           "s1_guarded": sorted(({k_: r[k_] for k_ in ("view", "concept", "easy", "raw", "rule")}
                                 for r in rows.values() if (r["rule"] or "").startswith("S1:")),
                                key=lambda r: (r["view"], r["concept"]))}
    ge = out["rev12"]["gray_easy"]
    out["rev12"]["gray_easy_lower_bound"] = S.cp_lower(ge["correct"], ge["n"])
    out["rev12"]["required_successes"] = S.required_successes(ge["n"])
    for r in rows.values():
        c = out["rev12_codes"][r["view"]]
        c[r["code"]] = c.get(r["code"], 0) + 1
    out["recovered"] = sorted(({k_: r[k_] for k_ in ("view", "concept", "easy", "human", "raw", "code",
                                                       "rule")}
                               for r in rows.values() if r["correct"] and not r["rev11_correct"]),
                              key=lambda r: (r["view"], not r["easy"], r["concept"]))
    out["gray_easy_referrals"] = sorted(({k_: r[k_] for k_ in ("item", "concept", "human", "raw", "code", "rule")}
                                         for r in rows.values() if r["view"] == "gray" and r["easy"]
                                         and not r["correct"]), key=lambda r: r["concept"])
    out["gray_referrals"] = sorted(({k_: r[k_] for k_ in ("item", "concept", "easy", "human", "raw", "code", "rule")}
                                    for r in rows.values() if r["view"] == "gray" and not r["correct"]),
                                   key=lambda r: (not r["easy"], -r["human"], r["concept"]))
    out["gray_referral_count"] = len(out["gray_referrals"])
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
