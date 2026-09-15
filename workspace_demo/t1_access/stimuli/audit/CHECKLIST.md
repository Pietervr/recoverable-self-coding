# Clue audit checklist (T1 stimulus bank, PREREGISTRATION_T1_model.md §3)

Each reader works alone and fills only their own columns (R1_* or R2_*). One row is one clause. The clause describes
the concept in the "concept" column as its implied subject; in the experiment it appears as a line "- <clause>".

For every clause mark:
- **true**: `y` if the clause is true of the concept as an ordinary reader understands the word (the sense in
  `concepts.json`), `n` if false or misleading, `?` if you cannot tell. The "drafter_note" column flags facts the
  drafter was unsure of: check those with particular care.
- **names**: `y` if the clause names the concept, an inflection or an accepted variant, or names its family (e.g.
  "animal", "country", "instrument"), in any disguise the checker could miss (a translation, a synonym, a pun).
- **decisive**: `y` if the clause alone would let a knowledgeable reader name the concept. At most two clauses per
  concept may be decisive; they are marked in the "marked_decisive" column. Mark `y` on any OTHER clause you find
  decisive.
- **comment**: optional; propose a rewrite if you mark n, y or y above.

A clause passes when both readers mark true = y, names = n, and (unless marked_decisive) decisive = n. Disagreements
are resolved by the two readers together; the resolution is recorded in the "resolution" column. The audited bank
is then frozen as stimuli/clues.json with the readers' names and the date.

# Property item audit (H3 secondary task, PREREGISTRATION_T1_model.md §11)

Each row is one yes/no question asked after a description of the concept. In the experiment the model's preference for
" Yes" over " No" is scored, and the target's representation is swapped for its foil's, so the two answers must be
opposite. For every item mark:
- **both_answers_correct**: `y` if "answer_for_concept" is correct for the concept AND "answer_for_foil" is correct for
  the foil, `n` otherwise.
- **unambiguous**: `y` if an ordinary educated adult would give both answers at once without dispute (no dependence on
  species, variety, word sense, era or culture), `n` otherwise.
- **comment**: optional; propose a better question if you mark n.
An item passes when both readers mark y and y; disagreements are resolved together and recorded in "resolution".
