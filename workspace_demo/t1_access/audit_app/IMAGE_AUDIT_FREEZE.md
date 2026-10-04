# Image and sense audit: frozen before any answer (repair 18)

R084, 2 October 2026. This answers Codex's record RSC `f9d2ef3` (answer 6.3) and R052's repair 18, under framework
§8.2's reader rule as revised by R052 (Unimog `16eb683f`, owner's decision of 2 October 2026). Revision 12 of the
reader package (3 October 2026, R052 handoff `ff264083`, the owner's decision of 3 October) changes the free-name
question and the matching rule below - one rule shared with the qualification scorer - and nothing else here.

**Exposure (updated 4 October 2026; the rules below are unchanged).** No audit answer exists: no reader has seen any
audit item and the page is not deployed. The AI reader has seen the 300 qualification images (outside the development
pool) in the qualification jobs: the first job of 2 October (STOPPED after 175 requests, never scored), job (a)
(600 requests, NOT ADMITTED under the revision-11 rule), job (b) (STOPPED at 219, never scored) and job (c) under
revision 17 (600 of 600; ADMITTED WITH 3 OWNER-ADJUDICATED ITEMS, `reviews/2026-10-04_ai_reader_job_c_owner_adjudication.md`).
The audit runs as its own bounded job: `stimuli/photo/AI_AUDIT_JOB.md` (the reader route reused, rounds, limits,
dispositions); nothing in this freeze is changed by it.

**Not a row-20 gate.** The audit is required for all 32 roles and their second views before row 21. The Stage A
eight go first, as the audit's own pilot.

## Panel

- **Reader: one AI reader, Codex (GPT-family vision).** Codex is from a different developer than the model under
  test. It reads the stimuli only after it passes the qualification of §8.2: on the grayscale canvas, naming under
  the shared matching rule on 61 of the 63 easy THINGSplus images or better (one-sided exact 95 % lower bound >= 0.90). The qualification is a separate package
  (`stimuli/photo/ai_reader_qual.py`, with its executor and bounded job brief), reviewed by Codex before its first
  call.
- **The owner decides referrals.** The owner does not read every item.
- **No other reader.** If the reader fails qualification, the audit holds. An owner-only audit, or a different
  reader, would be a separate explicit decision and is not an automatic fallback.

## Delivery and isolation

- The reader never uses this web page. The reader executor sends each image as a fresh, stateless, image-only
  request.
- Each item has an opaque id. `image_items.py` names files and items by `sha256("audit-img|<concept>|v1")[:12]`, so
  neither the URL nor the id names the concept.
- The PNG is byte-identical to `manifest_dev.json`'s clean canvas, and the script asserts it.
- **Every photograph is named blind first, on its own** (Codex RSC 69539bb §4.6): a second view gets its own free-name request, alone, exactly like a primary view. Only after both photographs' names are locked is the pair shown side by side, and only for the distinct-view question.

## Instructions and question order

Each question is a separate turn. Each answer is locked before the next question shows anything new.

1. **Free name, first.** "Look at this picture. What is the main object in it? Answer with the most common name for the object, in one or two words, or with the single word 'unclear' if you cannot tell. Reply with the name only."
   - the qualification's prompt, word for word (revision 12). Nothing about the concept, sense, family or any label
   list is visible at this point.
2. **Photograph.** "Is this a photograph?" (yes / no / unsure)
3. **Sense.** Only after 1 and 2 are locked: "Does it show a <name> in this sense: '<THINGS definition>'?"
   (yes / no / unsure)
4. **Distinct view** (second-view items only; the pair shown only after both photos' blind names are locked): "Is
   the second picture a different photograph from the first, not a crop or flip of it?" (yes / no / unsure)

The page `public/images.html` keeps the same order for the owner's referral view: the name is saved before the sense
question appears.

## Attempts

- Exactly one retained response per item and question.
- A failed request (provider error or timeout) may be retried. Every attempt is counted against the bounded job's
  allowance, and a retry never follows a received answer.
- Duplicate or unknown ids are rejected.
- Raw answers are committed before scoring.

## Aggregation (mechanical, by the separate orchestrator)

An item **passes on the AI reader alone** when all of these hold:

- the free name names the intended concept under the ONE matching rule the qualification scorer also uses
  (`ai_reader_key.names_concept`, revision 12): after normalisation (and with its tokens singularised under the key's
  inflection policy) it (i) equals an admitted form, or (ii) contains an admitted form as a whole-word phrase, or
  (iii) has a head lemma (the longest whole-word suffix WordNet 3.0 knows as a noun) that is a strict, transitive
  WordNet hyponym of the concept's recorded synset; an answer equal to one of the concept's excluded forms, or to the
  canonical name or an inflection of another released THINGS concept, does not name it. (ii) has no head-noun guard:
  the concept as a modifier of another object passes, and for this audit's question - does the stimulus evoke the
  concept - such an answer is evidence that it does (disclosed). The rule label (whole / contains / hyponym) is
  recorded per item. The admitted and excluded forms are those of `stimuli/photo/audit_alias_map.json` - the audit's own frozen map for the 32 instrument concepts (the qualification
  key excludes every pool concept and cannot score them), built under the qualification key's specificity rule S1-S4
  (dress is pruned from clothes, lid from hat), with three documented same-referent equivalences (taxi/cab,
  hamburger/burger, pig/hog), one documented exclusion the rule does not reach (denim from jeans: it also names the
  fabric), and ordinary validated inflections (taxis beside taxies). The map records its construction identities
  (THINGS tables and norm description, WordNet 3.0, dev_pool.json, ai_reader_key.py and its builder), and the audit
  scorer (`audit_alias_map.score`, format checked before matching, then the shared rule; it needs the pinned WordNet
  and runs under `.venv-build`) refuses unless the map hashes to
  audit_alias_map.json sha256: `a3f6ab51dbf0dda1148a26bfdc8b671adf91d1edc712fe58ef9ddcffc0397c80`;
- photograph = yes;
- sense = yes;
- for a second view, distinct = yes.

Any other outcome is a **referral to the owner**: 'unclear', a name the shared rule does not credit, a no or unsure
answer, or an input or provenance problem. Each referral record carries:

- the opaque item and view;
- the intended concept and sense;
- the THINGSplus human proportion and rating count;
- the hashes;
- the unedited raw answers and the question order;
- the frozen score;
- the reason code;
- the owner's dated evidence and decision;
- the disposition.

The owner's decision is **pass** or **fail (replace by the seeded rule, or hold)**. It never adds an alias
retrospectively and never adds a reader. It never turns a reader error into a pass of the qualification. Declared
before any revision-12 answer: a qualification referral the owner adjudicates as naming the intended object - the
picture and the raw answer recorded before the decision - is not a reader error; an admission that rests on such
adjudications is reported as "admitted with N owner-adjudicated items", never as a mechanical admission.

Items passed by the AI reader and items adjudicated by the owner are reported separately. Every answer is retained.

## Pilot set

The Stage A eight are `crow`, `horse`, `clothes`, `jacket`, `chili`, `hamburger`, `taxi` and `wagon`. `clothes`
replaced `mask` on 2 October: `mask` has a live stock listing that credits another author, which makes it
ineligible under the §8.2 stock-listing rule (`stimuli/photo/provenance_checks.json`).
