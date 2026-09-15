"""A1, step 1: the concept list and its roles (PREREGISTRATION_T1_model.md §3), by string rules and one seed.

Declared before any bank concept is read by the model:
- CANDIDATES: per family, common English nouns written in advance;
- COLLISIONS: candidates excluded because the word also names a member of another bank family
  (the family stratification would be ambiguous), with that family.

Eligibility uses string and token rules only, never model performance (§3):
- E1: the answer-context form is a single token: ' x' in lower case, or capitalised for
  countries. Convention from probe_answer_form.py (15 Sept, development concepts from no bank
  family): after the answer suffix the lower-case leading-space form outranks the capitalised
  one in 17 of 20 packets;
- E2: the word is not in COLLISIONS.

Selection per family: the eligible list is shuffled by a seed derived from SEED and the family,
and its first 16 are kept. Roles use a second derived seed: 4 BACKGROUND, 2 CAL, 2 PILOT, 8 CONF.
A family with fewer than 16 eligible words stops the build.

Output: concepts.json with each concept's family, role, frozen token id and enumerated
variants (' x', ' X', 'x', 'X', plural and irregular or demonym forms, each with its ids and
single-token status). The prompt scan uses the surface forms. Every exclusion is listed with
its rule.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/stimuli/build_concepts.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
SEED = 20260915
FAMILIES = ["animals", "countries", "tools", "foods", "vehicles", "instruments", "body parts", "materials"]
ROLE_COUNTS = [("BACKGROUND", 4), ("CAL", 2), ("PILOT", 2), ("CONF", 8)]
PER_FAMILY = 16

CANDIDATES = {
    "animals": "dog cat horse cow sheep pig goat rabbit mouse lion tiger bear wolf fox deer elephant monkey "
               "camel whale dolphin shark eagle owl snake frog bee ant spider duck chicken".split(),
    "countries": "France Japan Brazil Canada India Mexico Germany Australia Peru Norway Sweden Iran Argentina "
                 "Nigeria Thailand Egypt Italy Spain Russia Israel Pakistan Indonesia Iraq Syria Ukraine "
                 "Afghanistan Colombia Venezuela Ethiopia Denmark Finland Netherlands Belgium Austria Hungary "
                 "Kenya Greece Poland Portugal Vietnam Ireland Cuba Iceland Morocco Switzerland Mongolia Nepal "
                 "Jamaica China Turkey Chile".split(),
    "tools": "hammer saw drill axe knife needle brush wrench shovel rake scissors ladder ruler funnel clamp "
             "hoe vise magnet flashlight pencil screw bolt sponge bucket mop whisk nail".split(),
    "foods": "bread cheese rice pizza apple banana soup egg butter honey chocolate pasta sushi potato tomato "
             "lemon cake sandwich burger salad steak bacon mango grape strawberry orange".split(),
    "vehicles": "car bus truck train bicycle boat ship taxi van motorcycle rocket tram ferry airplane "
                "helicopter tractor submarine scooter canoe yacht ambulance sled wagon jet kayak raft cart "
                "subway plane".split(),
    "instruments": "piano guitar drum violin flute trumpet accordion bell whistle sax keyboard synth viola "
                   "tabla piccolo recorder triangle organ bass horn pipes".split(),
    "body parts": "heart liver lung brain knee nose ear eye tooth finger toe shoulder skull thumb lip chin "
                  "hip neck skin kidney stomach elbow tongue spine ankle wrist rib".split(),
    "materials": "steel glass wood copper cotton leather rubber concrete silk wool plastic iron gold silver "
                 "clay marble granite paper aluminum brick nylon bronze stone cement velvet".split(),
}

COLLISIONS = {
    "duck": "foods", "chicken": "foods", "Turkey": "animals", "China": "materials", "Chile": "foods",
    "nail": "body parts", "plane": "tools", "organ": "body parts", "bass": "animals", "horn": "body parts",
    "pipes": "tools", "rib": "foods",
}

IRREGULAR = {
    "mouse": ["mice"], "wolf": ["wolves"], "sheep": [], "deer": [], "knife": ["knives"], "tooth": ["teeth"],
    "foot": ["feet"], "loaf": ["loaves"], "potato": ["potatoes"], "tomato": ["tomatoes"], "mango": ["mangoes"],
    "sandwich": ["sandwiches"], "brush": ["brushes"], "bus": ["buses", "busses"], "scissors": ["scissor"],
    "sushi": [], "rice": [], "bacon": [], "honey": [], "butter": [], "cotton": [], "wool": [], "silk": [],
    "steel": [], "glass": ["glasses"], "wood": ["woods", "wooden"], "copper": [], "leather": [],
    "rubber": [], "concrete": [], "plastic": ["plastics"], "iron": ["irons"], "gold": ["golden"],
    "silver": [], "clay": [], "marble": ["marbles"], "granite": [], "paper": ["papers"], "aluminum": ["aluminium"],
    "nylon": [], "bronze": [], "stone": ["stones"], "cement": [], "velvet": [], "cheese": ["cheeses"],
    "peach": ["peaches"], "fox": ["foxes"], "whisk": ["whisks"], "wrench": ["wrenches"], "axe": ["axes", "ax"],
    "vise": ["vises", "vice"], "sax": ["saxophone", "saxes"], "synth": ["synthesizer", "synths"],
    "ferry": ["ferries"], "strawberry": ["strawberries"], "knee": ["knees"], "kidney": ["kidneys"],
    "stomach": ["stomachs"], "skull": ["skulls"], "spine": ["spines", "spinal"], "chocolate": ["chocolates"],
    "piccolo": ["piccolos"], "tabla": ["tablas"], "yacht": ["yachts"], "subway": ["subways"],
}
DEMONYMS = {
    "France": ["French"], "Japan": ["Japanese"], "Brazil": ["Brazilian"], "Canada": ["Canadian"],
    "India": ["Indian"], "Mexico": ["Mexican"], "Germany": ["German"], "Australia": ["Australian"],
    "Peru": ["Peruvian"], "Norway": ["Norwegian"], "Sweden": ["Swedish", "Swede"], "Iran": ["Iranian", "Persian"],
    "Argentina": ["Argentine", "Argentinian"], "Nigeria": ["Nigerian"], "Thailand": ["Thai"], "Egypt": ["Egyptian"],
    "Italy": ["Italian"], "Spain": ["Spanish", "Spaniard"], "Russia": ["Russian"], "Israel": ["Israeli"],
    "Pakistan": ["Pakistani"], "Indonesia": ["Indonesian"], "Iraq": ["Iraqi"], "Syria": ["Syrian"],
    "Ukraine": ["Ukrainian"], "Afghanistan": ["Afghan"], "Colombia": ["Colombian"], "Venezuela": ["Venezuelan"],
    "Ethiopia": ["Ethiopian"], "Denmark": ["Danish", "Dane"], "Finland": ["Finnish", "Finn"],
    "Netherlands": ["Dutch"], "Belgium": ["Belgian"], "Austria": ["Austrian"], "Hungary": ["Hungarian"],
    "Kenya": ["Kenyan"], "Greece": ["Greek"], "Poland": ["Polish", "Pole"], "Portugal": ["Portuguese"],
    "Vietnam": ["Vietnamese"], "Ireland": ["Irish"], "Cuba": ["Cuban"], "Iceland": ["Icelandic", "Icelander"],
    "Morocco": ["Moroccan"], "Switzerland": ["Swiss"], "Mongolia": ["Mongolian"], "Nepal": ["Nepali", "Nepalese"],
    "Jamaica": ["Jamaican"],
}


def derived_seed(*parts: object) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in (SEED, *parts)).encode()).hexdigest()[:16], 16)


def surface_forms(family: str, word: str) -> list[str]:
    """Words the prompt scan treats as the concept (matched case-insensitively on word boundaries)."""
    forms = {word}
    if family == "countries":
        forms.update(DEMONYMS.get(word, []))
    elif word in IRREGULAR:
        forms.update(IRREGULAR[word])
    else:
        forms.add(word + "s")
    return sorted(forms, key=str.lower)


def main() -> int:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))

    def ids(text: str) -> list[int]:
        return list(tok.encode(text, add_special_tokens=False))

    concepts, excluded, eligible_counts = [], [], {}
    for family in FAMILIES:
        eligible = []
        for word in CANDIDATES[family]:
            form = " " + word
            if word in COLLISIONS:
                excluded.append({"family": family, "word": word, "rule": "E2",
                                 "detail": f"also names a member of {COLLISIONS[word]}"})
                continue
            if len(ids(form)) != 1:
                excluded.append({"family": family, "word": word, "rule": "E1",
                                 "detail": f"{form!r} is {len(ids(form))} tokens"})
                continue
            eligible.append(word)
        eligible_counts[family] = len(eligible)
        if len(eligible) < PER_FAMILY:
            print(f"STOP: {family} has {len(eligible)} eligible words, needs {PER_FAMILY}")
            return 1
        pool = sorted(eligible)
        random.Random(derived_seed(family, "select")).shuffle(pool)
        chosen = pool[:PER_FAMILY]
        random.Random(derived_seed(family, "roles")).shuffle(chosen)
        roles = [r for r, n in ROLE_COUNTS for _ in range(n)]
        for word, role in zip(chosen, roles):
            variants = {}
            for v in (" " + word.lower(), " " + word.capitalize(), word.lower(), word.capitalize()):
                variants[v] = ids(v)
            for f in surface_forms(family, word):
                if f != word:
                    variants[" " + f] = ids(" " + f)
            concepts.append({
                "id": f"{family}/{word}", "family": family, "word": word, "role": role,
                "token_id": ids(" " + word)[0], "token_str": " " + word,
                "variants": {k: {"ids": v, "single_token": len(v) == 1} for k, v in variants.items()},
                "surface_forms": surface_forms(family, word),
            })

    tokenizer_sha = hashlib.sha256((SNAPSHOT / "tokenizer.json").read_bytes()).hexdigest()
    out = {
        "build": {"step": "concepts", "seed": SEED, "per_family": PER_FAMILY, "roles": dict(ROLE_COUNTS),
                  "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "tokenizer_json_sha256": tokenizer_sha, "snapshot": SNAPSHOT.name,
                  "rules": {"E1": "answer-context form ' x' (countries capitalised) is one token",
                            "E2": "not a word that also names a member of another bank family"}},
        "families": FAMILIES,
        "eligible_counts": eligible_counts,
        "concepts": concepts,
        "excluded": excluded,
    }
    (HERE / "concepts.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for family in FAMILIES:
        row = [c for c in concepts if c["family"] == family]
        print(f"{family:>12} ({eligible_counts[family]} eligible): " +
              "  ".join(f"{r}:" + ",".join(c["word"] for c in row if c["role"] == r) for r, _ in ROLE_COUNTS))
    ids_all = [c["token_id"] for c in concepts]
    assert len(set(ids_all)) == len(ids_all), "duplicate token ids across concepts"
    print(f"{len(concepts)} concepts, {len(excluded)} exclusions -> {HERE / 'concepts.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
