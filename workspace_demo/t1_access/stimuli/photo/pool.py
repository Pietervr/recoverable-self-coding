"""Photograph arm, desk gate ask 1: the qualified THINGSplus development pool and the 32 development roles.

Framework §8.1-8.2 (rsc_t1_two_channel_framework.md, draft 3), R052 handoff 2e94e85e. Nothing here touches the model
under test: every criterion is a source, name or taxonomy rule, decided independently of any target-model output.

SOURCE. THINGS concept metadata (Hebart et al. 2019; metadata CC BY) and the THINGSplus images and their human
image norms (Stoinski, Perkuhn & Hebart 2024): one image per concept, public domain / CC0 at collection, with the
THINGSplus notice's caveat that rights may have been misattributed. Held at ~/things-plus/, outside the repo.

QUALIFICATION, per THINGS concept, in this order (the first failure is recorded as the exclusion reason):
  Q1  single meaning in THINGS: 'Number of word meanings in list' == 1 (bat-the-animal and bat-the-club share a
      name, so neither has an unambiguous canonical answer);
  Q2  the name is one alphabetic word;
  Q3  SOURCE-GROUNDED SENSE: THINGS' own WordNet ID resolves to a WordNet 3.0 noun synset;
  Q4  FAMILY: that synset lies in exactly one family subtree - animals (animal.n.01), foods (food.n.01, food.n.02),
      vehicles (vehicle.n.01, the canonical family identifier), clothing (clothing.n.01);
  Q5  DOMINANT SENSE: the name's first WordNet noun synset IS that synset, so the canonical answer's dominant
      meaning is the pictured concept;
  Q6  E2: no noun sense of the name lies in another family's subtree;
  Q7  E1: ' name' is one token (name_tokens.json, frozen tokenizer);
  Q8  THINGSplus image present in the release;
  Q9  VISIBLY UNAMBIGUOUS AT SOURCE: on the THINGSplus image itself, human raters' most common label is the correct
      one (THINGS recognizability task). This is source evidence about the colour original; it is NOT the image
      audit, which §8.2 requires on the actual grayscale normalised stimulus by the owner or a qualified reader.

ROLES. Within each family the qualified concepts are put in an ORDER by a seed derived from SEED; the first eight
are the family's development concepts, then a second derived seed splits them 4 DEV-CAL / 4 DEV-PILOT, and a third
picks the two DEV-CAL concepts per family whose primary views feed Stage A. If the image audit later rejects a
concept, its slot is filled by the next qualified concept in the same family's seeded order, in the same role - a
declared rule, so no replacement is chosen by hand. All 32 are excluded from any later formal CAL, PILOT or CONF.

PROVENANCE. provenance_checks.json holds the per-image source checks of R052's terms reading (framework §8.2 (ii)).
A role concept whose check is 'ineligible' is replaced AFTER the roles are drawn (so no other role moves) by the next
concept in its family's seeded order past the first eight that is unused and not itself ineligible, taking the
rejections in the order their checks were recorded (so a replacement once made never moves); it inherits the
role and the Stage A flag. The replacement must carry a check of its own (eligible or not_found), or the run stops
and asks for that check first. Every replacement is logged with its reason in dev_pool.json 'replacements'; the
replaced concept stays excluded from formal CAL, PILOT and CONF.

    .venv-build/bin/python stimuli/photo/pool.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

from nltk.corpus import wordnet as wn

HERE = Path(__file__).resolve().parent
THINGS = Path.home() / "things-plus"
SEED = 20261003
FAMILIES = {"animals": ["animal.n.01"], "foods": ["food.n.01", "food.n.02"],
            "vehicles": ["vehicle.n.01"], "clothing": ["clothing.n.01"]}
PER_FAMILY, CAL, PILOT, STAGE_A = 8, 4, 4, 2


def derived(*parts) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in (SEED, *parts)).encode()).hexdigest()[:16], 16)


def subtree(roots: list[str]) -> set:
    out = set()
    for r in roots:
        s = wn.synset(r)
        out.add(s)
        out |= set(s.closure(lambda x: x.hyponyms() + x.instance_hyponyms()))
    return out


def main() -> int:
    trees = {f: subtree(r) for f, r in FAMILIES.items()}
    tokens = json.loads((HERE / "name_tokens.json").read_text())["ids"]
    concepts = list(csv.DictReader(open(THINGS / "_concepts-metadata_things.tsv", encoding="utf-8",
                                        errors="replace"), delimiter="\t"))
    images = {r["image"]: r for r in csv.DictReader(open(THINGS / "_images-metadata_things.tsv", encoding="utf-8",
                                                          errors="replace"), delimiter="\t") if "/" not in r["image"]}
    digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (THINGS / "_concepts-metadata_things.tsv", THINGS / "_images-metadata_things.tsv")}

    qualified = {f: [] for f in FAMILIES}
    excluded: list[dict] = []
    for r in concepts:
        word, uid = r["Word"].strip().lower(), r["uniqueID"].strip()
        rec = {"concept": uid, "name": word, "wnid": r["WordNet ID"].strip()}

        def out(reason: str) -> None:
            excluded.append({**rec, "rule": reason.split(":")[0], "reason": reason})

        if r["Number of word meanings in list"].strip() != "1":
            out("Q1: the name has several meanings in THINGS"); continue
        if not word.isalpha():
            out("Q2: not one alphabetic word"); continue
        try:
            syn = wn.synset_from_pos_and_offset("n", int(rec["wnid"].lstrip("n")))
        except Exception:
            syn = None
        if syn is None:
            out("Q3: THINGS WordNet ID does not resolve to a WordNet 3.0 noun synset"); continue
        rec["synset"] = syn.name()
        home = [f for f in FAMILIES if syn in trees[f]]
        if len(home) != 1:
            out("Q4: not in exactly one family" + (f" ({home})" if home else "")); continue
        fam = home[0]
        rec["family"] = fam
        senses = wn.synsets(word, pos="n")
        if not senses or senses[0] != syn:
            out(f"Q5: dominant sense is {senses[0].name() if senses else 'none'}, not THINGS' {syn.name()}"); continue
        clash = [g for g in FAMILIES if g != fam and set(senses) & trees[g]]
        if clash:
            out(f"Q6: E2 - a noun sense also lies in {clash}"); continue
        ids = tokens.get(word)
        if not ids or len(ids) != 1:
            out(f"Q7: E1 - ' {word}' is {len(ids) if ids else '?'} tokens"); continue
        rec["e1_token_id"] = ids[0]
        img = images.get(f"{uid}.jpg")
        if img is None:
            out("Q8: no THINGSplus image in the release"); continue
        rec["thingsplus_image"] = img["image"]
        rec["recognizability"] = float(img["recognizability"] or 0)
        rec["most_common_label"] = img["recognizability_most-common-label"]
        if img["recognizability_most-common-label"].strip() != img["display_label"].strip():
            out(f"Q9: raters' most common label '{img['recognizability_most-common-label']}' is not "
                f"'{img['display_label']}'"); continue
        qualified[fam].append(rec)

    roles, order = [], {}
    for fam, recs in qualified.items():
        pool = sorted(recs, key=lambda x: x["concept"])
        random.Random(derived(fam, "order")).shuffle(pool)
        order[fam] = [x["concept"] for x in pool]
        dev = pool[:PER_FAMILY]
        split = list(dev)
        random.Random(derived(fam, "roles")).shuffle(split)
        cal, pilot = split[:CAL], split[CAL:CAL + PILOT]
        stage_a = sorted(cal, key=lambda x: x["concept"])
        random.Random(derived(fam, "stage_a")).shuffle(stage_a)
        stage_a_ids = {x["concept"] for x in stage_a[:STAGE_A]}
        for x in cal:
            roles.append({**x, "role": "DEV-CAL", "stage_a_primary_view": x["concept"] in stage_a_ids})
        for x in pilot:
            roles.append({**x, "role": "DEV-PILOT", "stage_a_primary_view": False})

    checks_path = HERE / "provenance_checks.json"
    checks = {c["concept"]: c for c in json.loads(checks_path.read_text())["checks"]} if checks_path.exists() else {}
    replacements = []
    used = {x["concept"] for x in roles}
    check_order = list(checks)                        # the order the checks were recorded
    pending = sorted((i for i, x in enumerate(roles)
                      if checks.get(x["concept"], {}).get("status") == "ineligible"),
                     key=lambda i: check_order.index(roles[i]["concept"]))
    for i in pending:                                 # earliest-recorded rejection first: a replacement once made
        x, c = roles[i], checks[roles[i]["concept"]]  # never moves when a later check rejects another concept
        by_name = {r["concept"]: r for r in qualified[x["family"]]}
        skipped = []
        for cand in order[x["family"]][PER_FAMILY:]:
            if cand in used:
                continue
            cc = checks.get(cand)
            if cc is None:
                raise SystemExit(f"replacement for {x['concept']}: next in order is {cand}, which has no provenance "
                                 "check yet - check it first")
            if cc["status"] == "ineligible":
                skipped.append({"concept": cand, "reason": cc["licence_basis"]})
                continue
            roles[i] = {**by_name[cand], "role": x["role"], "stage_a_primary_view": x["stage_a_primary_view"],
                        "replaces": x["concept"]}
            used.add(cand)
            replacements.append({"family": x["family"], "role": x["role"],
                                 "stage_a_primary_view": x["stage_a_primary_view"], "out": x["concept"],
                                 "reason": c["licence_basis"], "skipped": skipped, "in": cand,
                                 "in_check": {k: cc[k] for k in ("source_url", "published", "licence_basis")}})
            break
        else:
            raise SystemExit(f"no eligible replacement left for {x['concept']} in {x['family']}")

    counts = {f: len(v) for f, v in qualified.items()}
    out = {"seed": SEED, "families": FAMILIES, "per_family": PER_FAMILY, "source_digests": digests,
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "qualified_counts": counts, "qualified": qualified, "seeded_order": order,
           "roles": sorted(roles, key=lambda x: (x["family"], x["role"], x["concept"])),
           "provenance_checks_sha256": hashlib.sha256(checks_path.read_bytes()).hexdigest() if checks else None,
           "replacements": replacements,
           "excluded_from_formal_CAL_PILOT_CONF": sorted({x["concept"] for x in roles}
                                                         | {r["out"] for r in replacements}),
           "exclusions": excluded,
           "exclusion_counts": {k: sum(e["rule"] == k for e in excluded) for k in
                                ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9")}}
    (HERE / "dev_pool.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print("qualified per family:", counts, "(need >= 8 each)")
    print("exclusions by rule:", out["exclusion_counts"])
    for fam in FAMILIES:
        r = [x for x in out["roles"] if x["family"] == fam]
        print(f"  {fam:<9} CAL {[x['concept'] + ('*' if x['stage_a_primary_view'] else '') for x in r if x['role'] == 'DEV-CAL']}"
              f"  PILOT {[x['concept'] for x in r if x['role'] == 'DEV-PILOT']}")
    print("  (* = Stage A primary view)")
    return 0 if all(v >= PER_FAMILY for v in counts.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
