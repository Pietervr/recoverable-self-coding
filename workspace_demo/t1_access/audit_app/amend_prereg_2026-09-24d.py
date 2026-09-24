"""Draft amendment of 24 Sept 2026 to PREREGISTRATION_T1_model.md §3: the stimulus bank is rebuilt on
published human feature norms. Concepts and the facts their clauses state come from Buchanan et al.
(2019); family membership from WordNet; decisiveness from cue validity computed on those norms.

Owner's decision, 24 Sept: rebuild on a curated set, because a self-authored bank is the easiest thing
in the study to attack and a cited one is not.

Numbers are R084's measured step 1 result (stimuli/norms_bank/FEASIBILITY.md, RSC 62b6601) under the four
rules R052 decided. Nothing is selected, rendered or frozen by this amendment; it fixes the construction
that step 2 then runs.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

EDITS = [
    # 1. the family list and the concept count
    ("128 single-token concepts, 16 per family, 8 families (animals, countries,\n"
     "tools, foods, vehicles, instruments, body parts, materials)",
     "127 single-token concepts in 8 families — animals, body parts, buildings, clothing, foods, "
     "materials, occupations, vehicles — 16 per family except buildings at 15 (§3.1)"),

    # 2. the frozen id sentence still names countries, a family that no longer exists
    ("The frozen id is the lower-case leading-space form (' fox'), capitalised for countries (' Kenya'); "
     "case, space, plural and demonym variants are enumerated per concept in `concepts.json`.",
     "The frozen id is the lower-case leading-space form (' fox'); case, space and plural variants are "
     "enumerated per concept in `concepts.json`. No family now takes a capitalised id."),

    # 3. the role split, with the buildings shortfall taken out of BACKGROUND
    ("4 → **BACKGROUND** (never a target, foil or competitor), 2 → CAL, 2 → PILOT, 8 → CONF.",
     "4 → **BACKGROUND** (never a target, foil or competitor), 2 → CAL, 2 → PILOT, 8 → CONF; buildings "
     "takes 3 → BACKGROUND, so the bank is 127. The shortfall is taken from BACKGROUND and nowhere else "
     "because CAL, PILOT and CONF are fixed by the pairing (8, 8 and 32 pairs), and an odd count in any of "
     "them cannot be paired at all; BACKGROUND concepts are never a target, foil or competitor, so three of "
     "them instead of four costs a little variety in the filler and nothing in the inference."),

    # 4. the clause count and its source
    ("12 descriptive clauses per concept (all 128), 8–14 tokens each",
     "12 descriptive clauses per concept (all 127), each stating one published normed feature of that "
     "concept (§3.1), 8–14 tokens each"),
]
for old, new in EDITS:
    assert t.count(old) == 1, f"no unique match: {old[:70]!r}"
    t = t.replace(old, new)

BLOCK = """### 3.1 The bank is built from published feature norms (draft amendment, 24 Sept 2026)

The concepts, the facts their clauses state and the decisiveness of each clause come from a published
human-produced source rather than from the authors. The reason is plain: these clauses are the base of the
whole study and the easiest part of it to attack, and a bank whose every fact carries a citation cannot be
dismissed as ours. It also retires the audit problem instead of managing it — the two questions that an
audit exists to answer, *is this true of the concept* and *does it give the concept away*, are answered by
the source.

**The source.** Buchanan, Valentine and Maxwell (2019), *English semantic feature production norms: an
extended database of 4436 concepts*, Behavior Research Methods: 69,284 concept–feature rows over 4,436
cues, each feature carrying the number of participants who produced it. The file is
`4 analysis/final words 2017.xlsx` from `github.com/doomlab/Word-Norms-2`, 7,173,768 bytes, SHA-256
`6e1fc087986d5657684e190c2c04bd5a2c40f1d39b78eebb0ead8bb5e2225337`. **It is held outside this repository
and is never redistributed.** Each clause cites its source entry — cue, feature, production frequency and
sharing count — and that citation table, not the database, is what the release publishes. LLM-augmented
norm sets are excluded by construction: building stimuli from model output to test a model would reintroduce
the circularity the different-developer rule exists to prevent.

**Family membership is taxonomic, not ours.** A concept belongs to a family when **its first WordNet noun
synset** (WordNet 3.0, senses ordered by frequency) lies in that family's hyponym and instance-hyponym
closure, and cues sharing a dominant synset are one concept. The eight roots are `animal.n.01`,
`body_part.n.01`, `building.n.01`, `clothing.n.01`, `food.n.01` with `food.n.02`, `material.n.01`,
`worker.n.01` with `professional.n.01`, and `vehicle.n.01`. The dominant-sense rule is used rather than
any-sense because any-sense admits members no reader would accept — *bark* the sailing ship, *secretary* the
writing desk, *kettle* the kettledrum — and a bank that needs those explained away defeats the point of
sourcing it. E1 (the answer-context form is one token) and E2 (no noun sense in another family's subtree)
are unchanged and are applied after membership, with dominant-sense collapsing applied after E1 so that a
synset is lost only when every one of its cues fails E1.

**Feature identity is lemmatised.** Sharing counts are computed on the feature string lowercased, stripped,
and lemmatised as a noun, else as a verb (`nltk.stem.wordnet.WordNetLemmatizer`, nltk 3.10.3, WordNet 3.0).
Raw strings fragment the counts — *trunk* and *trunks* count as two — and because cue validity is
approximated by one over the number of cues sharing a feature, fragmentation makes every feature look rarer
than it is and therefore **overstates decisiveness**, which would strip the bank of exactly the ordinary
filler the dose design needs. Lemmatising costs 43 % of the eligible pool (distinct features 11,424 →
7,534; cues at ≥ 12 features 2,585 → 1,474) and is taken anyway. Buchanan's own `translated` column is not
used: it collapses on meaning, which is a judgement, and leaves only 878 cues at ≥ 12 features.

**Twelve features, and why the threshold cannot be lowered.** A concept is eligible only with ≥ 12
lemmatised features, because step 2 selects 12 features per concept, one per clause: the threshold is the
clause count restated, and a concept with eight features cannot supply twelve clauses. Measured eligible
counts, dominant-sense, at ≥ 12: foods 40, animals 36, body parts 25, vehicles 19, clothing 19,
occupations 18, materials 16, buildings 15.

**What the families are, and what they are not.** Families are a stratification and an E2 exclusion device,
not a hypothesis, so which eight they are carries no scientific weight and they were chosen by what the
norms can support. Tools and instruments are **not** in the bank and could not be: after E2 and E1 the
ceiling over the entire WordNet subtree — every single-token English noun in the family, normed or not — is
11 for each. E1 is what binds, not the source: it removes *chisel*, *pliers*, *hatchet*, *scalpel*,
*gavel*, *corkscrew*, *sledgehammer*, *clarinet*, *saxophone*, *trombone*, *tuba*. E1 is a decode rule —
the single-token answer form is what makes the answer-position logit readable — so it was not relaxed to
retain a family name. Countries is likewise absent: concrete-object norms do not cover it.

**Decisiveness is measured, not judged.** Each concept's 12 selected features are ranked by sharing count
ascending, the rarest first. The **two rarest are the concept's permitted decisive clauses** and are marked
as such, which satisfies §3's "at most two" by construction rather than by a reader's opinion. Every other
selected feature must be shared by at least $K$ cues, $K$ declared from the reported distribution of
sharing counts **before** step 2 selects and recorded here; it is not set now, because setting it without
the distribution would be the same guess this amendment exists to remove. The per-clause record carries the
cue, the feature, its production frequency and its sharing count, so any reader can recompute the
decisiveness of every clause in the bank.

**Recorded fragility.** Materials stands at exactly 16 with no margin, and adopting occupations is what put
it there (*clay* is also a person in WordNet, so E2 removes it). Materials is the family most exposed to
E2, already losing *alligator*, *beaver*, *cherry*, *fur*, *leopard*, *lime*, *mink*, *raccoon*, *salt*,
*sponge* and *wash* to animals, foods or clothing. Any later tightening of any rule must re-check materials
first, because it is the family with nothing to give.

"""

ANCHOR = "**Audit readers (draft amendment, 24 Sept 2026, second entry).**"
assert t.count(ANCHOR) == 1, "audit readers anchor did not match once"
t = t.replace(ANCHOR, BLOCK + ANCHOR)

ROW = (
    "| 2026-09-24 | Draft amendment, §3.1: the stimulus bank is rebuilt on published feature norms. Concepts "
    "and clause facts from Buchanan et al. 2019 (held outside the repo, cited per clause, never "
    "redistributed); family membership by dominant WordNet noun sense over eight declared roots; feature "
    "identity lemmatised; eligibility at ≥ 12 features because that is the clause count restated; "
    "decisiveness set by cue-validity rank with the two rarest permitted and $K$ deferred to the reported "
    "distribution. The families become animals, body parts, buildings, clothing, foods, materials, "
    "occupations and vehicles — 127 concepts, buildings at 15 with its shortfall taken from BACKGROUND | "
    "owner, 24 Sept: these clauses are the base of the whole study and the easiest part to discredit, and a "
    "curated source takes the sting out of a review. Tools, instruments and countries could not be built "
    "from any norm set: after E2 and E1 the whole-subtree ceiling is 11 for tools and 11 for instruments, "
    "so E1 binds rather than the source, and E1 is a decode rule that was not relaxed to keep a family "
    "name. The shortfall goes to BACKGROUND alone because CAL, PILOT and CONF are fixed by the pairing and "
    "an odd count cannot be paired |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3 amended for the norms bank; §3.1 inserted; §15 row appended")
