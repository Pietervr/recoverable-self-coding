# Job (a) re-scored under revision 12's shared matching rule: RE-ANALYSIS, NOT ADMISSION

R084, 3 October 2026, for the owner's information only (R052 handoff `ff264083`, item G). Job (a) of 2 October stays
**NOT ADMITTED** under its frozen whole-answer rule (`2026-10-02_ai_reader_job_a.md`); nothing here is re-scored for
admission. Job (a) answered revision 11's prompt ("one short noun or noun phrase"), not revision 12's ("one or two
words"), so these numbers do not predict job (b).

Script and full output: `2026-10-03_ai_reader_job_a_rescore_rev12/` (`rescore.py`, `rescore.json`). Outside
scientific mode: it reads job (a)'s journal (sha256 `b8c8bf4f…`, RSC `0baec65`) and the frozen key directly and calls
the revision-12 scorer's `classify_detail`; it admits nothing and touches no go. Revision 11's counts are reproduced
first (49 / 177 / 184).

| | revision 11 (frozen) | revision 12 rule (re-analysis) |
|---|---|---|
| gray easy | 49 of 63 | **61 of 63** (one-sided exact 95 % lower bound 0.9034) |
| colour easy | 49 of 63 | 62 of 63 |
| gray, all strata | 177 of 300 | 231 of 300 (strata 0 / 1 / 2: 55 / 82 / 94) |
| colour, all strata | 184 of 300 | 254 of 300 (69 / 88 / 97) |

Gray codes: OK_WHOLE 177, OK_CONTAINS 51, OK_HYPONYM 3, ERR_NONMATCH 68, ERR_MALFORMED 1 - 69 gray referrals.

**The brief expected 60 easy gray; the rule as written gives 61.** "Air conditioning unit" (air_conditioner) passes by
(ii): "air conditioning" is an admitted form of the key (a THINGS-listed WordNet synonym), so it occurs in the answer
as a whole-word phrase. The 12 easy gray recoveries: air conditioner, album, bandage, car door, generator, hole, paint
("Paint dishes"), pillow, scale, thread, toilet paper (all contains) and shoe ("Sneakers", hyponym). The two easy gray
referrals: pearl ("Seashell") and christmas card ("Holiday greeting card": head "greeting card", a hypernym).

**The S1 guard.** An answer equal to another released THINGS concept's canonical name or inflection does not pass
(fixture D: "an answer equal to another released concept's alias still fails S1"). On job (a) it refused 42 answers
across both views, none easy - among them "Alpaca" (llama) and "Belt buckle" (buckle), which (iii) and (ii) would
otherwise have credited, and "Stretcher" (gurney), "Drums" (bongo). Without the guard the counts would be gray 233,
colour 257; the easy counts are the same either way.

Other passes worth the owner's eye (all non-easy): "Hard hat" (helmet) and "Stack of logs" (wood) by hyponym; modifier
answers by (ii) such as "Toy train" (toy), "Mascara brush" (mascara), "Wafer biscuit" (wafer), "Pinball machine"
(pinball) - the disclosed residual. The full lists are in `rescore.json` (`recovered`, `s1_guarded`,
`gray_referrals`).
