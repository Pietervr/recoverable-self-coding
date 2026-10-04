"""Image audit, step 4: the mechanical SCORER of one audit round (orchestrator side; the reader never sees it).
Framework §8.2, audit_app/IMAGE_AUDIT_FREEZE.md ("Aggregation"), AI_AUDIT_JOB.md; R052 rulings 1a-1f (handoff 08f09009).
Standard library plus WordNet 3.0 (the shared matching rule), so it runs under .venv-build:

    .venv-build/bin/python stimuli/photo/ai_audit_score.py <k>        # writes ai_audit_score_r<k>.json

ADMISSION OF THE ROUND'S JOURNAL, before any score - the reader scorer's chain, reused: the raw file is tracked, clean
and byte-equal to its committed blob (ai_reader_score.committed); the journal passes the complete validator
(ai_reader_journal.validate, a COMPLETE receipt) under round k's limits; the audit package recomputed now equals the
digest in every record and the package the go approved (row "aiaudit", stage "audit"); the round's set and key equal
their derivation (ai_audit_set.check); the clock's FINISHED closure is admitted (ai_reader_exec.admit_clock).
A synthetic-fixture journal is refused unless `allow_synthetic=True`, and the output is then labelled as such.

AGGREGATION (the freeze, unchanged). Each request's retained outcome is scored:
  name        audit_package.score under the pinned map and scorer code - the ONE matching rule shared with the
              qualification (whole / contains / hyponym; the S1 guard; format before matching); pass = an OK code
  photograph, sense, distinct
              the answer, trimmed, lower-cased and with one trailing full stop removed, must be exactly yes, no or
              unsure; anything else is MALFORMED; a non-answer outcome keeps its status code; pass = yes
A PRIMARY passes on the reader alone iff name, photograph and sense pass. A CANDIDATE passes iff name, photograph and
sense pass and its pair's distinct answer is yes.

DISPOSITIONS.
  primary not passed   -> a REFERRAL to the owner (pass, or fail: replace by the seeded rule, or hold). For a DEV-CAL
                          Stage A primary the referral says explicitly that a replacement would change an input of the
                          accepted Stage A bundle and needs the owner's decision with its stated consequence (ruling 1f).
  candidate passed     -> the concept's SECOND VIEW (the first passing candidate in rank order), subject to its
                          per-image check before any capture (ruling 1e).
  candidate not passed -> the next candidate is audited in the next round (second_views.py's declared rule); the
                          failed candidate's full record is kept and listed for the owner, who may still pass it.
  no candidate left    -> a REFERRAL: the concept has no accepted second view and holds Stage B (framework §8.2).
Every referral carries the freeze's fields: opaque item and view, intended concept and sense, the THINGSplus human
proportion and rating count (primaries; none exists for a Commons candidate), the hashes, the unedited raw answers in
question order, the frozen scores and reason codes, the round's raw sha256 and commit, the package digest, and empty
fields for the owner's dated evidence, decision and disposition. AI-passed and owner-adjudicated items are reported
separately; an owner decision never adds an alias.

CARRIED SCOPE (ruling 1; Codex 410b580; job (c) record 0f3af76): the reader is ADMITTED WITH 3 OWNER-ADJUDICATED ITEMS
on the third pass over an exposed qualification panel - evidence for the prospective rule, not a blind calibration;
this audit is its first use on unseen candidate images; partial stdout text is never an answer; the capacity detector
covers visible retained capacity text only. A reader pass is a bounded claim about this stimulus and these questions,
not human equivalence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_audit_exec as A  # noqa: E402
import ai_audit_set as S  # noqa: E402
import ai_reader_journal as J  # noqa: E402
from ai_reader_score import STATUS_CODES, committed, sha  # noqa: E402

YES_NO = ("yes", "no", "unsure")
SCOPE = ("Reader ADMITTED WITH 3 OWNER-ADJUDICATED ITEMS (job (c), RSC 0f3af76; the owner's adjudication record "
         "reviews/2026-10-04_ai_reader_job_c_owner_adjudication.md), on the third pass over an exposed qualification "
         "panel: evidence for the prospective rule, not a blind calibration. This audit is the reader's first use on "
         "unseen candidate images. Partial stdout text is never an answer; the capacity detector covers visible "
         "retained capacity text only (Codex 410b580). A reader pass is a bounded claim about this stimulus and "
         "question, not human equivalence.")
STAGE_A_CONSEQUENCE = ("This primary is the source of Stage A inputs (row 20, accepted with qualifications, Codex "
                       "b0db0f9; OS bridge 92409ba). Replacing it would change an input of the accepted Stage A bundle: "
                       "no replacement without the owner's decision and its stated consequence for that bundle.")


def yes_no(answer: str | None, status: str, overlength: bool) -> str:
    if status in STATUS_CODES:
        return STATUS_CODES[status]
    if overlength:
        return "ERR_OVERLENGTH"
    if status != "ok" or answer is None:
        return "ERR_NO_RESPONSE"
    a = answer.strip().lower()
    if a.endswith("."):
        a = a[:-1]
    return a.upper() if a in YES_NO else "ERR_MALFORMED"


def admit(k: int, *, allow_synthetic: bool = False, fixture: dict | None = None) -> dict:
    if fixture is not None and not allow_synthetic:
        raise SystemExit("refused: injected fixture objects are accepted in labelled synthetic mode only")
    if allow_synthetic:
        raw, sset, deliv = fixture["raw"], fixture["sset"], fixture["delivery"]
        data = raw.read_bytes()
        info = {"raw_sha256": sha(data), "raw_commit": None, "bytes": data}
        recs, tail = J.read(raw, cap=A.PER_ROUND["raw_bytes"])
        if tail:
            raise SystemExit("refused: the raw file ends in an incomplete line")
        digest = recs[0].get("package_digest") if recs else None
        v = J.validate(recs, sset, digest, raw_bytes=data, require_complete=True, mode="synthetic-fixture",
                       delivery=deliv, instructions_sha256=deliv.get("instructions_sha256"))
        return {**info, "validation": v, "clock": None, "records": recs, "package_digest": digest, "sset": sset}
    lim = A.configure(k)
    import ai_reader_exec as E
    import stage_a_guard
    info = committed(A.raw_path(k))
    recs, tail = J.read(A.raw_path(k), cap=lim["raw_bytes"])
    if tail:
        raise SystemExit("refused: the raw file ends in an incomplete line")
    pkg = A.package()
    digest = recs[0].get("package_digest") if recs else None
    if digest != pkg["package_digest"]:
        raise SystemExit("refused: the journal's package digest is not the audit package recomputed now")
    stage_a_guard.require_go(A.GO, pkg, row=A.ROW, stage=A.STAGE, verify_at_commit=A.package_at_commit)
    S.check(k)
    sset = json.loads(S.set_path(k).read_text())
    deliv = json.loads(A.delivery_path(k).read_text())
    A.check_delivery(sset, deliv, pkg["instructions_sha256"])
    v = J.validate(recs, sset, digest, raw_bytes=info["bytes"], require_complete=True, mode="scientific",
                   delivery=deliv, instructions_sha256=pkg["instructions_sha256"], limits=lim)
    clock = E.admit_clock(A.job_dir(k) / "clock.json", info["bytes"], recs[-1])
    return {**info, "validation": v, "clock": clock, "records": recs, "package_digest": digest, "sset": sset}


def score(k: int, *, allow_synthetic: bool = False, fixture: dict | None = None, name_score=None) -> dict:
    """`name_score(concept, answer, status, overlength)` is injected only in synthetic mode (no WordNet in the
    fixtures); scientific mode always uses audit_package.score under the package's pins."""
    a = admit(k, allow_synthetic=allow_synthetic, fixture=fixture)
    sset = a["sset"]
    key = fixture["key"] if allow_synthetic else json.loads(S.key_path(k).read_text())
    if allow_synthetic:
        nscore = name_score
    else:
        if name_score is not None:
            raise SystemExit("refused: scientific scoring uses only audit_package.score")
        import audit_package
        pins = audit_package.identity()

        def nscore(concept, answer, status, overlength):
            return audit_package.score(concept, answer, status, overlength, pins=pins)
    pool = {r["concept"]: r for r in json.loads((HERE / "dev_pool.json").read_text())["roles"]}
    reqs = {r["request"]: r for r in sset["requests"]}
    final = {}
    for r in a["records"]:
        if (r["t"] == "end" and r["retained"]) or r["t"] == "final":
            final[r["request"]] = r
    begins = {r["attempt_id"]: r for r in a["records"] if r["t"] == "begin"}
    ans = {}                                          # item -> question -> scored answer
    for rq, rec in final.items():
        q, item = reqs[rq]["question"], reqs[rq]["item"]
        status, over = rec["outcome"], bool(rec.get("overlength"))
        concept = key["items"][item]["concept"]
        if q == "name":
            s = nscore(concept, rec.get("answer"), status, over)
            code, ok, rule = s["code"], s["pass_name"], s["rule"]
        else:
            code = yes_no(rec.get("answer"), status, over)
            ok, rule = code == "YES", None
        b = begins.get(rec.get("attempt_id"), {})
        ans.setdefault(item, {})[q] = {
            "request": rq, "code": code, "pass": ok, "rule": rule, "raw": rec.get("answer"),
            "answer_len": rec.get("answer_len"), "answer_sha256": rec.get("answer_sha256"),
            "attempt_id": rec.get("attempt_id"), "delivered_sha256": (b.get("receipt") or {}).get("image_sha256"),
            "prompt_sha256": sha(reqs[rq]["prompt"].encode())}
    ident = {"round": k, "raw_sha256": a["raw_sha256"], "raw_commit": a["raw_commit"],
             "package_digest": a["package_digest"], "set_sha256": sha(json.dumps(sset, sort_keys=True).encode())
             if allow_synthetic else sha(S.set_path(k).read_bytes()),
             "key_sha256": sha(json.dumps(key, sort_keys=True).encode()) if allow_synthetic
             else sha(S.key_path(k).read_bytes()), "scorer_sha256": sha(Path(__file__).read_bytes())}
    items, referrals, second, candidates_failed = {}, [], {}, []
    for item, meta in sorted(key["items"].items()):
        if meta["kind"] == "pair":
            continue
        got = ans.get(item, {})
        qs = ("name", "photograph", "sense") + (("distinct",) if meta["kind"] == "candidate" else ())
        rows = {q: (got.get(q) if q != "distinct" else ans.get(meta["pair"], {}).get("distinct")) for q in qs}
        passed = all(rows[q] is not None and rows[q]["pass"] for q in qs)
        reasons = [f"{q}:{rows[q]['code'] if rows[q] else 'MISSING'}" for q in qs if not (rows[q] and rows[q]["pass"])]
        items[item] = {"concept": meta["concept"], "kind": meta["kind"], "rank": meta.get("rank"),
                       "passed_by_reader": passed, "reasons": reasons, "answers": rows}
        role = pool[meta["concept"]]
        rec = {"item": item, "view": "primary" if meta["kind"] == "primary" else "second",
               "concept": meta["concept"], "family": meta["family"], "role": meta["role"],
               "sense": meta["definition"], "synset": meta["synset"],
               "human_recognizability": role["recognizability"] if meta["kind"] == "primary" else None,
               "human_n_ratings": None if meta["kind"] != "primary" else "see THINGSplus norms (release table)",
               "png_sha256": meta["png_sha256"], "original_sha256": meta.get("original_sha256"),
               "candidate": {k2: meta.get(k2) for k2 in ("rank", "title", "page_url", "licence_statement")}
               if meta["kind"] == "candidate" else None,
               "question_order": list(qs), "answers": rows, "reasons": reasons, **ident,
               "reader_scope": SCOPE,
               "owner_evidence": None, "owner_decision": None, "owner_date": None, "disposition": None}
        if meta["kind"] == "primary" and not passed:
            if meta["stage_a_primary_view"]:
                rec["stage_a_consequence"] = STAGE_A_CONSEQUENCE
            rec["referral_reason"] = "primary not passed by the reader"
            referrals.append(rec)
        if meta["kind"] == "candidate" and not passed:
            candidates_failed.append(rec)
    # second views: per concept, this round's candidate outcome joined with earlier rounds' committed outcomes
    prior = S.prior_outcomes(k) if (k > 1 and not allow_synthetic) else {}
    n_ranks = {}
    if not allow_synthetic:
        cands = json.loads(S.SRC.CANDS.read_text())
        pins = json.loads(S.SRC.PINS.read_text())
        for concept, v in cands["concepts"].items():
            n_ranks[concept] = [rank for rank, c in enumerate(v["candidates"], 1)
                                if pins["items"][S.SRC.cand_id(concept, c["title"])].get("sha256")]
    for item, it in items.items():
        if it["kind"] != "candidate":
            continue
        c = it["concept"]
        audited = sorted(prior.get(c, {}).get("ranks", set()) | {it["rank"]})
        if it["passed_by_reader"]:
            sv = {"status": "selected", "candidate": item, "rank": it["rank"], "audited_ranks": audited}
        elif allow_synthetic or any(r not in audited for r in n_ranks.get(c, [])):
            sv = {"status": "next", "candidate": None, "audited_ranks": audited}
        else:
            sv = {"status": "exhausted", "candidate": None, "audited_ranks": audited}
            referrals.append({"concept": c, "referral_reason": "no candidate accepted: the concept holds Stage B "
                                                               "unless the owner passes a failed candidate",
                              "candidates_failed": [x for x in candidates_failed if x["concept"] == c], **ident,
                              "owner_evidence": None, "owner_decision": None, "owner_date": None,
                              "disposition": None})
        second[c] = sv
    if k == 1:                                         # a concept whose list had no available candidate at all
        for item, meta in key["items"].items():
            c = meta["concept"]
            if meta["kind"] == "primary" and c not in second:
                second[c] = {"status": "exhausted", "candidate": None, "audited_ranks": []}
                referrals.append({"concept": c, "referral_reason": "no candidate with a pinned source: the concept "
                                                                   "holds Stage B unless the owner decides otherwise",
                                  "candidates_failed": [], **ident, "owner_evidence": None, "owner_decision": None,
                                  "owner_date": None, "disposition": None})
    out = {"identity": ident, "mode": a["validation"]["mode"], "reader_scope": SCOPE,
           "charged": {"attempts": a["validation"]["attempts"],
                       "seconds": (a["clock"] or {}).get("seconds_total", 0.0) if a["clock"] else 0.0},
           "outcomes": a["validation"]["outcomes"], "items": items, "second_views": second,
           "candidates_failed_listed_for_owner": candidates_failed, "referrals": referrals,
           "referral_count": len(referrals),
           "counts": {"primaries_passed": sum(1 for i in items.values() if i["kind"] == "primary" and
                                              i["passed_by_reader"]),
                      "primaries": sum(1 for i in items.values() if i["kind"] == "primary"),
                      "second_views_selected": sum(1 for s in second.values() if s["status"] == "selected"),
                      "concepts_next_round": sorted(c for c, s in second.items() if s["status"] == "next"),
                      "concepts_exhausted": sorted(c for c, s in second.items() if s["status"] == "exhausted")}}
    if out["mode"] != "scientific":
        out = {"WARNING": "SYNTHETIC FIXTURE - NOT AN AUDIT RESULT", **out}
    return out


if __name__ == "__main__":
    k = int(sys.argv[1])
    res = score(k)
    S.score_path(k).write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False, default=list) + "\n")
    print(json.dumps(res["counts"], indent=1))
