"""Image audit, step 4: the mechanical SCORER of one audit round (orchestrator side; the reader never sees it).
Framework §8.2, audit_app/IMAGE_AUDIT_FREEZE.md ("Aggregation"), AI_AUDIT_JOB.md; R052 rulings 1a-1f (handoff 08f09009).
Standard library plus WordNet 3.0 (the shared matching rule), so it runs under .venv-build:

    .venv-build/bin/python stimuli/photo/ai_audit_score.py score <k>   # writes ai_audit_score_r<k>.json
    .venv-build/bin/python stimuli/photo/ai_audit_score.py verify <k>  # re-admits, re-scores, compares to the commit

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
  candidate not passed -> RETAINED and REFERRED to the owner; succession is automatic - the next candidate is
                          audited in the next round (the freeze's amendment of 4 October); `resolve` keeps the
                          earliest-ranked candidate passed by the reader or the owner, a later mechanical selection
                          it outranks recorded as superseded.
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
        chained = fixture["chain"].admit(k, for_run=False) if fixture.get("chain") else None
        import ai_reader_exec as E
        clock = E.admit_clock(fixture["job"] / "clock.json", data, recs[-1])   # the real finished-closure admission
        return {**info, "validation": v, "clock": clock, "records": recs, "package_digest": digest, "sset": sset,
                "chained": chained}
    lim, chained = A.configure(k, chain=A.scientific_chain(verify=verify_result), for_run=False)
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
    set_info = check_set_in_image_venv(k, chained)
    sset = json.loads(S.set_path(k).read_text())
    deliv = json.loads(A.delivery_path(k).read_text())
    A.check_delivery(sset, deliv, pkg["instructions_sha256"])
    v = J.validate(recs, sset, digest, raw_bytes=info["bytes"], require_complete=True, mode="scientific",
                   delivery=deliv, instructions_sha256=pkg["instructions_sha256"], limits=lim)
    clock = E.admit_clock(A.job_dir(k) / "clock.json", info["bytes"], recs[-1])
    return {**info, "validation": v, "clock": clock, "records": recs, "package_digest": digest, "sset": sset,
            "chained": chained}


OWNER_DECISIONS = ("pass", "fail_replace", "fail_hold")


def resolve(scores: dict, decisions: dict) -> dict:
    """Revision 2 (Codex 1b17d64 finding 3; R052's ruling): the final disposition per concept from the authenticated
    round scores (`scores[j]`) and the owner's dated decisions (`decisions["items"][item] = {"decision": pass |
    fail_replace | fail_hold, "date", "by", "evidence"}`). Reader outcomes are never changed: a reader fail the owner
    passes is reported as OWNER-PASSED, never as a reader pass. Primary: kept if the reader passed it or the owner
    passed it; otherwise the owner's replace/hold stands (pending without a decision). Second view: the EARLIEST-RANKED
    candidate passed by the reader or by the owner is kept - the declared order wins - and a later candidate the reader
    selected mechanically is recorded as SUPERSEDED; the per-image check of framework 8.2 applies to the kept
    candidate only. A failed candidate without an owner decision is pending, never kept."""
    dec = (decisions or {}).get("items", {})
    for item, d in dec.items():
        if d.get("decision") not in OWNER_DECISIONS or not d.get("date") or not d.get("by"):
            raise SystemExit(f"refused: owner decision for {item} is not a dated pass / fail_replace / fail_hold")
    concepts = {}
    for j in sorted(scores):
        for item, it in scores[j]["items"].items():
            c = concepts.setdefault(it["concept"], {"primary": None, "candidates": {}})
            if it["kind"] == "primary":
                c["primary"] = {"item": item, "reader": "pass" if it["passed_by_reader"] else "fail", "round": j}
            else:
                c["candidates"][it["rank"]] = {"item": item, "rank": it["rank"], "round": j,
                                               "reader": "pass" if it["passed_by_reader"] else "fail"}
    out = {}
    for concept, c in sorted(concepts.items()):
        p = c["primary"]
        pd = dec.get(p["item"], {}).get("decision") if p else None
        primary = {**(p or {}), "owner": pd,
                   "status": "kept" if p and (p["reader"] == "pass" or pd == "pass") else
                             (pd or "pending_owner")}
        kept, superseded, pending = None, [], []
        for rank in sorted(c["candidates"]):
            x = c["candidates"][rank]
            od = dec.get(x["item"], {}).get("decision")
            passed = x["reader"] == "pass" or od == "pass"
            entry = {**x, "owner": od, "decided_by": "reader" if x["reader"] == "pass" else ("owner" if od else None)}
            if passed and kept is None:
                kept = entry
            elif passed:
                superseded.append({**entry, "superseded_by": kept["item"]})
            elif od is None:
                pending.append(entry)
        out[concept] = {"primary": primary, "second_view_kept": kept, "superseded": superseded,
                        "failed_candidates_pending_owner": pending,
                        "per_image_check": kept["item"] if kept else None}
    return out


IMAGE_PY = HERE.parents[1] / ".venv-image" / "bin" / "python"


def check_set_in_image_venv(k: int, chained: dict) -> dict:
    """Round k's set, key and delivery are tracked, clean and byte-equal to their commits, and the set and key equal
    their derivation from the AUTHENTICATED chain - derived by the bound set builder under the image venv (the canvas
    pipeline's pinned numpy and Pillow), which this .venv-build process does not have."""
    import subprocess
    import tempfile
    for p in (S.set_path(k), S.key_path(k), A.delivery_path(k)):
        committed(p)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        json.dump({"round": k, "priors": chained["priors"], "evidence": chained["evidence"]}, t)
    try:
        got = subprocess.run([str(IMAGE_PY), str(HERE / "ai_audit_set.py"), "derive-hashes", str(k), t.name],
                             capture_output=True, text=True, timeout=A.VERIFY_TIMEOUT_S)
    finally:
        Path(t.name).unlink(missing_ok=True)
    if got.returncode != 0:
        raise SystemExit(f"refused: round {k}'s set derivation failed: {got.stderr.strip()[-600:]}")
    d = json.loads(got.stdout.strip().splitlines()[-1])
    if (d.get("round"), d.get("set_sha256"), d.get("key_sha256")) != (k, sha(S.set_path(k).read_bytes()),
                                                                       sha(S.key_path(k).read_bytes())):
        raise SystemExit(f"refused: round {k}'s set or key differs from its derivation from the admitted chain")
    return d


def serialise(out: dict) -> bytes:
    return (json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()


def verify_result(k: int, *, allow_synthetic: bool = False, fixture: dict | None = None, name_score=None,
                  score_file: Path | None = None) -> dict:
    """Revision 2 (Codex 1b17d64 finding 2): round k re-admitted (committed raw, complete validation, package, go,
    its own predecessor chain, set derivation, delivery, the finished CURRENT clock) and re-scored; the result must
    equal the committed score file byte for byte. Returns the authenticated identity and the CURRENT charges."""
    from ai_reader_score import committed as _committed
    if not allow_synthetic and (fixture is not None or name_score is not None or score_file is not None):
        raise SystemExit("refused: scientific verification takes no injected objects")
    out, a = _score(k, allow_synthetic=allow_synthetic, fixture=fixture, name_score=name_score)
    b = serialise(out)
    got = _committed(score_file or S.score_path(k))
    if got["bytes"] != b:
        raise SystemExit(f"refused: round {k}'s committed score file is not what its admitted evidence scores to")
    return {"round": k, "score_sha256": sha(b), "raw_sha256": a["raw_sha256"],
            "attempts": a["validation"]["attempts"], "seconds": float(a["clock"]["seconds_total"])}


def score(k: int, **kw) -> dict:
    return _score(k, **kw)[0]


def _score(k: int, *, allow_synthetic: bool = False, fixture: dict | None = None, name_score=None):
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
        rec = {"item": item, "view": "primary" if meta["kind"] == "primary" else "second",
               "concept": meta["concept"], "family": meta["family"], "role": meta["role"],
               "sense": meta["definition"], "synset": meta["synset"],
               "human_recognizability": (meta.get("human") or {}).get("recognizability"),
               "human_n_ratings": (meta.get("human") or {}).get("n_ratings"),
               "human_n_correct": (meta.get("human") or {}).get("n_correct"),
               "png_sha256": meta["png_sha256"], "source_sha256": meta.get("source_sha256"),
               "commons_original_sha1": meta.get("commons_original_sha1"),
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
    chained = a.get("chained")
    prior = S.prior_outcomes(chained) if (k > 1 and chained) else {}
    history = {}                                       # every earlier failed candidate, per concept (finding 3 / limits)
    for j in sorted((chained or {}).get("priors", {})):
        for x in chained["priors"][j]["candidates_failed_listed_for_owner"]:
            history.setdefault(x["concept"], []).append({"round": j, **{k2: x[k2] for k2 in
                                                         ("item", "candidate", "reasons", "answers")}})
    n_ranks = dict(fixture.get("available_ranks", {})) if allow_synthetic else {}
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
        elif any(r not in audited for r in n_ranks.get(c, [])):
            sv = {"status": "next", "candidate": None, "audited_ranks": audited}
        else:
            sv = {"status": "exhausted", "candidate": None, "audited_ranks": audited}
            referrals.append({"concept": c, "referral_reason": "no candidate accepted: the concept holds Stage B "
                                                               "unless the owner passes a failed candidate",
                              "candidates_failed": history.get(c, []) + [
                                  {"round": k, **{k2: x[k2] for k2 in ("item", "candidate", "reasons", "answers")}}
                                  for x in candidates_failed if x["concept"] == c], **ident,
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
                       "note": "seconds are not recorded here: the chain charges each round's CURRENT admitted clock"},
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
    return out, a


if __name__ == "__main__":
    cmd, k = sys.argv[1], int(sys.argv[2])
    if cmd == "score":                                 # writes ai_audit_score_r<k>.json (then commit it)
        res = score(k)
        S.score_path(k).write_bytes(serialise(res))
        print(json.dumps(res["counts"], indent=1))
    elif cmd == "verify":                              # the chain's authentication of a committed round
        print(json.dumps(verify_result(k)))
    else:
        raise SystemExit("usage: ai_audit_score.py score|verify <k>")
