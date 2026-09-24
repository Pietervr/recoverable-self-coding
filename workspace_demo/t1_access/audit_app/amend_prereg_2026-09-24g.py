"""Draft amendment of 24 Sept 2026 to PREREGISTRATION_T1_model.md §3 and §3.1: the bank moves to McRae
(with CSLB pooled) and to THREE families.

Owner's decision, 24 Sept, on R084's measurement (SOURCES_MCRAE_CSLB.md, RSC aec969e): go with three
families. Buchanan is dropped as a primary source because its feature column carries no relation; McRae
carries the relation explicitly and ships the authors' own cue validity, but neither McRae nor CSLB norms
people, buildings or materials at the depth eight families need.

Prospective. No bank is built and nothing is frozen; §3.1 states the construction that runs once the CSLB
access question is settled.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

EDITS = [
    ("at most 127 single-token concepts in 8 families — animals, body parts, buildings, clothing, foods, "
     "materials, occupations, vehicles — 16 per family except buildings at 15, and a family that cannot "
     "fill its count may run to 13 with the shortfall taken from BACKGROUND (§3.1); the realised count is "
     "fixed by the seeded acceptance loop and recorded at the freeze",
     "single-token concepts in **3 families — animals, foods, vehicles** (§3.1). The confirmation set stays "
     "at 64 concepts, so §10's power numbers are unchanged; what changes is the stratification, from eight "
     "levels to three. Per-family role counts are no longer equal and are allocated by seed in proportion "
     "to each family's eligible pool, subject to CONF totalling 64, CAL 16 and PILOT 16; the realised "
     "allocation is fixed by the seeded acceptance loop and recorded at the freeze"),

    ("4 → **BACKGROUND** (never a target, foil or competitor), 2 → CAL, 2 → PILOT, 8 → CONF; buildings "
     "takes 3 → BACKGROUND, so the bank is 127. The shortfall is taken from BACKGROUND and nowhere else "
     "because CAL, PILOT and CONF are fixed by the pairing (8, 8 and 32 pairs), and an odd count in any of "
     "them cannot be paired at all; BACKGROUND concepts are never a target, foil or competitor, so three of "
     "them instead of four costs a little variety in the filler and nothing in the inference.",
     "**BACKGROUND** (never a target, foil or competitor), CAL, PILOT and CONF, with CONF, CAL and PILOT "
     "totalling 64, 16 and 16 across the three families and BACKGROUND taking every remaining eligible "
     "concept, at least one per family. The totals are what the pairing fixes (32, 8 and 8 pairs, each "
     "member the foil of the other), and they are met across families rather than within one: with counts "
     "$a \\ge b \\ge c$ over three families, every concept can be paired outside its own family whenever "
     "$a \\le b + c$, which the allocation rule must satisfy and record."),

    ("**Background list.** Per (concept, carrier, draw): eight background clauses, exactly one from a\n"
     "BACKGROUND concept of each family (the target's own family included), drawn by seed; identical for\n"
     "the target packet and its paired foil packet.",
     "**Background list.** Per (concept, carrier, draw): eight background clauses drawn by seed from "
     "BACKGROUND concepts, balanced across the three families in a declared 3–3–2 pattern whose family "
     "order rotates by seed, the target's own family included; identical for the target packet and its "
     "paired foil packet. One clause per family no longer fills eight slots at three families, so the rule "
     "states the balance explicitly instead; what it preserves is unchanged — background composition is "
     "fixed by seed, balanced across families, and identical between a target packet and its foil."),
]
for old, new in EDITS:
    assert t.count(old) == 1, f"no unique match: {old[:60]!r}"
    t = t.replace(old, new)

BLOCK = """

**The source is McRae, with CSLB pooled (24 Sept 2026).** Buchanan is dropped as a primary source: its
`feature` column carries no relation, so every predicate would be authored and the citation decorative, and
that finding stands in the record as the reason. McRae et al. (2005) carries the relation explicitly, one
relation type per entry — *elephant* `has_a_trunk` (production frequency 23, shared by 1, cue validity
1.000), *truck* `used_for_cargo`, *cow* `beh_-_produces_milk` — so `has_a_trunk` renders to "has a trunk"
and what remains is agreement and padding to the 8–14 token window, not the invention of a predicate. It
also ships **`CV_No_Tax`, the authors' own cue validity per feature**, which replaces the proxy this section
previously tried to compute: cue validity is cited, not derived. File
`McRae-BRM-InPress/CONCS_FEATS_concstats_brm.txt` from `McRae-BRM-2005.zip`, SHA-256
`eb36b4c88f85141a226879ef2fdddc8075b9d35705fd27344c3a414eb56430a3`, 541 concepts, 2,432 feature statements,
every feature given by at least 5 of 30 participants. CSLB (Devereux et al. 2014, 638 concepts) states the
same kind of relational label and its appendix carries a McRae label column, so the two pool on a separator
and a label reconciliation. The norms are held outside the repository and never redistributed; McRae's terms
are non-commercial with a citation stipulation, which citing per clause satisfies and which is why they
cannot sit inside the CC BY 4.0 data release.

**Three families, and why not more.** Animals, foods and vehicles are the only families McRae and CSLB can
fill. Both are concrete-**object** norm sets: neither norms people at all, and clothing, body parts,
materials and buildings fall short. Three is also the floor, since a competitor must come from a third
family. **The design does not stand on McRae alone.** McRae's own eligible counts across these three
families are animals 29, foods 14, vehicles 15 — 58 against the 96 that CONF, CAL and PILOT require before
any background — so CSLB's concepts are load-bearing, and CSLB's data is available only on request. Until
that access is settled the pooled figures (animals 52, foods 40, vehicles 27) are an upper bound, because
CSLB's concepts are counted without the ≥ 12 feature filter. **Vehicles is the binding family**, and if its
realised eligible count falls below what the allocation needs, the three-family design fails and the
question returns to whether this bank can be built from published norms at all.

**Merging is by subsumption, not by stem.** The derivational-merge and brand-name rules above were written
for Buchanan's single-word features and move no McRae count. McRae's duplication is subsumption — one
feature's words a subset of another's: `has_legs` and `has_4_legs`; `has_wheels`, `has_4_wheels`,
`has_>_4_wheels` and `has_18_wheels`; `beh_-_eats` and `beh_-_eats_peanuts`. 70 such pairs across 77
eligible concepts. Two features merge when one's word set contains the other's, the more specific
representing the pair, and the stem and brand rules are retained only for whatever they still catch. McRae's
taxonomic features (`an_animal`, `a_mammal`, `a_vehicle`) are family words by construction and rule F
removes them, which is consistent: `CV_No_Tax` is blank for exactly those rows."""

ANCHOR = "\n\n**The source is under question (24 Sept 2026).**"
assert t.count(ANCHOR) == 1
i = t.index(ANCHOR)
j = t.index("\n\n**Recorded fragility.**", i)
t = t[:i] + BLOCK + t[j:]

ROW = (
    "| 2026-09-24 | Draft amendment, §3 and §3.1: the source becomes McRae (CSLB pooled) and the bank becomes "
    "**three families** — animals, foods, vehicles. CONF stays 64 so §10 is unchanged; stratification drops "
    "from eight levels to three; per-family role counts become unequal and seeded in proportion to each "
    "family's eligible pool; the background list becomes a declared 3–3–2 balance rotating by seed, since "
    "one clause per family no longer fills eight slots; merging becomes subsumption over the feature's word "
    "set | McRae carries the relation and ships the authors' own cue validity (`CV_No_Tax`), so the clause "
    "is rendered from a cited statement rather than authored from a cited topic word. But McRae and CSLB "
    "are concrete-object norms: neither norms people, and only animals, foods and vehicles can be filled. "
    "McRae alone gives 58 eligible across those three against the 96 CONF, CAL and PILOT need, so CSLB is "
    "load-bearing and its data is gated; vehicles is the binding family |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3/§3.1 moved to McRae and three families; §15 row appended")
