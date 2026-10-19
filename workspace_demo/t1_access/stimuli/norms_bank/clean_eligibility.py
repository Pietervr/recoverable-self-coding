"""Cleaned eligibility for the adopted three-family design: McRae alone and McRae + Feats, at >= 12 and >= 10.

The chain, per candidate cue, in this order:
  F1/F2   noun with a WordNet noun sense; its own WordNet base form;
  F4      dominant sense: the FIRST noun synset lies in one adopted family's subtree (animals, foods, vehicles);
  E2      no noun sense in another adopted family's subtree (all senses: the prompt scan cannot tell them apart);
  E1      the answer-context form ' x' is ONE token (token_counts.json, frozen Qwen3.6 tokenizer);
  F3      >= THRESHOLD USABLE features (usable.py), not raw features - Codex's finding 3;
then cues sharing a dominant synset collapse to one concept AFTER E1 and F3, so a synset counts if any of its cues
qualifies. Three tiers are reported: raw (the old ceiling), minimal (Codex's screen, to check against his
figures) and protocol (every usable-feature rule §3.1 states).

Two further readings:
  E1<=2   the same chain with E1 relaxed to at most two tokens: an UPPER BOUND for the 15 October decision, not a
          proposal. Its cost is stated in the report: a two-token answer has no single answer-position logit.
  allocation  for each count triple, whether CONF 64 / CAL 12 / PILOT 12 plus one BACKGROUND per family can be
          allocated jointly in integers: all three families present in every split, each <= half of the split
          (so cross-family reciprocal pairs and a third-family competitor exist), role totals disjoint, and the
          background reserve taken FIRST. It reports a reserve-aware largest-remainder witness, or the deficit.

    .venv-build/bin/python stimuli/norms_bank/clean_eligibility.py
"""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

from nltk.corpus import wordnet as wn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import family_pool as fp  # noqa: E402
from feats_parse import Source  # noqa: E402
from usable import COMMON_CAPITALS, Canon, proper_words, usable, words  # noqa: E402

FAMILIES = ["animals", "foods", "vehicles"]
# Owner's decision, 13 October 2026 (R052 handoff f9aac0a7): CONF stays 64; CAL 12 and PILOT 12 (were 16 each);
# one BACKGROUND per family (3); need 91. The usable-feature minimum is 10 (was 12); 12 is still reported.
SPLITS = [("CONF", 64), ("CAL", 12), ("PILOT", 12)]
THRESHOLDS = [10, 12]
TIERS = ["raw", "minimal", "protocol"]
E1_LIMITS = {"E1": 1, "E1<=2": 2}


def candidates(src: Source, trees: dict, tokens: dict, max_tokens: int) -> dict[str, dict]:
    """Every cue passing F1, F2, F4 (dominant sense), E2 and E1 - before any feature count."""
    out = {}
    for c in src.nouns():
        senses = wn.synsets(c, pos="n")
        if not senses or (wn.morphy(c, "n") or c) != c:
            continue
        home = [f for f in FAMILIES if senses[0] in trees[f]]
        if len(home) != 1:
            continue
        fam = home[0]
        if any(set(senses) & trees[g] for g in FAMILIES if g != fam):
            continue
        n = tokens.get(c)
        if n is None or n > max_tokens:
            continue
        out[c] = {"family": fam, "synset": senses[0].name(), "tokens": n}
    return out


def collapse(qualifying: dict[str, dict]) -> dict[str, list[str]]:
    """Distinct dominant synsets per family; the representative is the cue with most usable features, then name."""
    best: dict[str, tuple] = {}
    for c, info in qualifying.items():
        key = (info["family"], info["synset"])
        cand = (-info["usable"], c)
        if key not in best or cand < best[key]:
            best[key] = cand
    fams: dict[str, list[str]] = {f: [] for f in FAMILIES}
    for (fam, _), (_, c) in best.items():
        fams[fam].append(c)
    return {f: sorted(v) for f, v in fams.items()}


def feasible_allocation(n: dict[str, int]) -> dict:
    """Joint integer allocation, background reserved first. Exhaustive over CONF and CAL; PILOT checked in closed form."""
    cap = {f: n[f] - 1 for f in FAMILIES}                 # one BACKGROUND per family, reserved first
    need = sum(k for _, k in SPLITS) + len(FAMILIES)
    out = {"available": sum(n.values()), "needed": need, "deficit": max(0, need - sum(n.values()))}
    if any(cap[f] < 3 for f in FAMILIES):
        out.update(feasible=False, reason="a family cannot reserve a background and appear in all three splits")
        return out

    def triples(total):
        half = total // 2
        for a in range(1, half + 1):
            for b in range(1, half + 1):
                c = total - a - b
                if 1 <= c <= half:
                    yield (a, b, c)

    (_, n_conf), (_, n_cal), (_, n_pilot) = SPLITS
    for conf in triples(n_conf):
        if any(conf[i] > cap[f] for i, f in enumerate(FAMILIES)):
            continue
        for cal in triples(n_cal):
            rem = [cap[f] - conf[i] - cal[i] for i, f in enumerate(FAMILIES)]
            if min(rem) < 1:
                continue
            hi = [min(n_pilot // 2, r) for r in rem]
            if sum(hi) < n_pilot:
                continue
            pilot, left = [1, 1, 1], n_pilot - 3
            for i in range(3):
                add = min(hi[i] - 1, left)
                pilot[i] += add
                left -= add
            if left == 0:
                out.update(feasible=True, witness={"CONF": list(conf), "CAL": list(cal), "PILOT": pilot,
                                                   "BACKGROUND": [n[f] - conf[i] - cal[i] - pilot[i]
                                                                  for i, f in enumerate(FAMILIES)]})
                out["proportional"] = proportional(n)
                return out
    out.update(feasible=False, reason="no joint integer allocation satisfies the half bounds and capacities")
    return out


def proportional(n: dict[str, int]) -> dict:
    """Reserve-aware largest remainder: backgrounds first, then each split in proportion to remaining capacity."""
    cap = {f: n[f] - 1 for f in FAMILIES}
    alloc = {}
    for split, total in SPLITS:
        half = total // 2
        weight = sum(cap.values())
        raw = {f: total * cap[f] / weight for f in FAMILIES}
        take = {f: max(1, min(half, cap[f], int(raw[f]))) for f in FAMILIES}
        for f in sorted(FAMILIES, key=lambda f: -(raw[f] - int(raw[f]))):
            while sum(take.values()) < total and take[f] < min(half, cap[f]):
                take[f] += 1
                break
        while sum(take.values()) < total:
            grow = [f for f in FAMILIES if take[f] < min(half, cap[f])]
            if not grow:
                return {"ok": False, "failed_at": split}
            take[max(grow, key=lambda f: cap[f] - take[f])] += 1
        while sum(take.values()) > total:
            take[max(FAMILIES, key=lambda f: take[f])] -= 1
        alloc[split] = [take[f] for f in FAMILIES]
        for f in FAMILIES:
            cap[f] -= take[f]
    alloc["BACKGROUND"] = [cap[f] + 1 for f in FAMILIES]
    return {"ok": True, **alloc}


def main() -> int:
    trees = {f: fp.subtree(f) for f in FAMILIES}
    tok = json.loads((HERE / "token_counts.json").read_text())
    tokens = tok["counts"]
    sources = {"mcrae": Source("mcrae"), "pooled": Source("pooled")}
    vocab = {w for s in sources.values() for fs in s.features.values() for f in fs for w in words(f)}
    canon = Canon({w for w in vocab if w.isalpha()})

    results, detail, ablation = {}, {}, {}
    for sname, src in sources.items():
        for e1name, lim in E1_LIMITS.items():
            cands = candidates(src, trees, tokens, lim)
            bank_names = set(cands)
            per_cue = {c: {t: usable(c, src.features[c], src.provenance, bank_names, canon, t) for t in TIERS}
                       for c in cands}
            for thr in THRESHOLDS:
                for tier in TIERS:
                    q = {c: {**cands[c], "usable": per_cue[c][tier]["count"]} for c in cands
                         if per_cue[c][tier]["count"] >= thr}
                    fams = collapse(q)
                    counts = {f: len(v) for f, v in fams.items()}
                    key = f"{sname}|{e1name}|>={thr}|{tier}"
                    results[key] = {"counts": counts, "total": sum(counts.values()), "concepts": fams,
                                    "allocation": feasible_allocation(counts)}
            if e1name == "E1":
                # What each protocol rule costs: the protocol count with that ONE rule switched off.
                for thr in THRESHOLDS:
                    row = {}
                    for drop in ("none", "T", "N", "X", "P", "D"):
                        skip = frozenset() if drop == "none" else frozenset({drop})
                        q = {}
                        for c in cands:
                            u = usable(c, src.features[c], src.provenance, bank_names, canon, "protocol", skip)
                            if u["count"] >= thr:
                                q[c] = {**cands[c], "usable": u["count"]}
                        fams = collapse(q)
                        row[drop] = {f: len(v) for f, v in fams.items()}
                    ablation[f"{sname}|E1|>={thr}"] = row
                detail[sname] = {c: {"family": cands[c]["family"], "synset": cands[c]["synset"],
                                     "raw": per_cue[c]["raw"]["count"], "minimal": per_cue[c]["minimal"]["count"],
                                     "protocol": per_cue[c]["protocol"]["count"],
                                     "removed": {k: v for k, v in per_cue[c]["protocol"]["log"].items() if v},
                                     "merged": per_cue[c]["protocol"]["merged"]}
                                 for c in sorted(cands)}

    caps = sorted({f for s in sources.values() for fs in s.features.values() for f in fs if any(ch.isupper() for ch in f)})
    out = {
        "design": "three families (animals, foods, vehicles); needed CONF 64 + CAL 12 + PILOT 12 + one BACKGROUND per "
                  "family = 91 (owner, 13 Oct 2026; was CAL 16 + PILOT 16 = 99)",
        "sources": {k: {"digests": v.digests, "composite_sha256": v.sha256, "bookkeeping": v.bookkeeping}
                    for k, v in sources.items()},
        "tokenizer_json_sha256": tok["tokenizer_json_sha256"],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "usable_sha256": hashlib.sha256((HERE / "usable.py").read_bytes()).hexdigest(),
        "common_capitals_not_removed": sorted(COMMON_CAPITALS),
        "capitalised_labels": {f: ("proper/brand: " + ",".join(proper_words(f))) if proper_words(f) else "kept (common)"
                               for f in caps},
        "results": results,
        "ablation_protocol_without_one_rule": ablation,
    }
    # Feature labels are the norms' content: the per-concept record (what each rule removed or merged) and the
    # capitalised-label verdicts go to a gitignored file, so nothing of the databases is committed. The committed
    # JSON holds counts, cue words, allocations and digests only.
    private = {"capitalised_labels": out.pop("capitalised_labels"), "per_concept_E1": detail}
    (HERE / "clean_eligibility_detail.json").write_text(
        json.dumps(private, indent=1, ensure_ascii=False, default=list) + "\n")
    (HERE / "clean_eligibility.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=list) + "\n")

    print(f"{'source':<7} {'E1':<6} {'thr':>4} {'tier':<9} {'animals':>8} {'foods':>6} {'vehicles':>9} {'total':>6}  allocation")
    for key, r in results.items():
        s, e, t, tier = key.split("|")
        c = r["counts"]
        a = r["allocation"]
        verdict = "feasible" if a.get("feasible") else f"NO (deficit {a['deficit']})" if a["deficit"] else "NO (half bound)"
        print(f"{s:<7} {e:<6} {t:>4} {tier:<9} {c['animals']:>8} {c['foods']:>6} {c['vehicles']:>9} {r['total']:>6}  {verdict}")
    # The cost of E1<=2 that can be counted: two-token answers whose FIRST token is shared with another selected
    # answer cannot be told apart by an answer-position (first-token) logit at all.
    ids = tok["ids"]
    for key in ("pooled|E1<=2|>=12|protocol", "pooled|E1<=2|>=10|protocol"):
        names = [c for v in results[key]["concepts"].values() for c in v]
        multi = [c for c in names if len(ids[c]) > 1]
        firsts: dict[int, list[str]] = {}
        for c in names:
            firsts.setdefault(ids[c][0], []).append(c)
        shared = sorted(c for c in names if len(firsts[ids[c][0]]) > 1)
        results[key]["two_token"] = {"answers": len(names), "multi_token": len(multi),
                                     "first_token_shared": shared,
                                     "groups": {str(k): v for k, v in firsts.items() if len(v) > 1}}
        print(f"{key}: {len(names)} answers, {len(multi)} of them two tokens; {len(shared)} share a first token "
              f"with another answer: {sorted(v for v in firsts.values() if len(v) > 1)}")
    (HERE / "clean_eligibility.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=list) + "\n")

    print("\nprotocol count with ONE rule switched off (single-token E1): what each rule costs")
    print(f"{'config':<18} " + "  ".join(f"{d:>9}" for d in ("all", "-T", "-N", "-X", "-P", "-D")))
    for key, row in ablation.items():
        cells = [sum(row[d].values()) for d in ("none", "T", "N", "X", "P", "D")]
        print(f"{key:<18} " + "  ".join(f"{c:>9}" for c in cells))
    print("   T taxonomic rows  N own name  X other bank-concept names  P proper nouns/brands  D stem/derivation merge")
    print(f"\n-> {HERE / 'clean_eligibility.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
