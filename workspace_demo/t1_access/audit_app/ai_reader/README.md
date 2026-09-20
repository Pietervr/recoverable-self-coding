# Independent AI reading of the T1 stimulus bank

Date: 2026-09-20. Status: **Complete**.

Reader: OpenAI `gpt-6-astra`, native session model identifier; reasoning effort `max`, Codex CLI `0.155.0`. The native metadata exposes no more specific model snapshot/version, so none is inferred. Session `01a0c0c1-45aa-7b90-b0e1-70ea45e01c7d`, exact topic name `GPT: R052 Entropy paper`.

Authority: `../../stimuli/audit/CHECKLIST.md` (both sections), `../../PREREGISTRATION_T1_model.md` sections 3 and 11 and the 18 September reader amendments; task brief `Unimog-Projects/prompts/2026-09-20_codex_r084_clue_bank_read.txt` (SHA256 `9784704909fa95a5ca6554888494f198fd333a4ba14c3047efba534a21ffd57d`). This is an independent reader's judgment, with author resolution deferred. All resolution cells are empty.

## Progress

Row numbers below are one-based data rows, excluding the header. Clause identities are `concept:index`; property identities are `id`. Each saved mark was assigned to an explicit identity after reading its clause or question. No marks are generated for unread rows.

| Sheet | Completed data rows | Read / total | Last identity |
|---|---|---|---|
| Clauses | 1–1536 | 1536 / 1536 | materials/wood:11 |
| Property items | 1–100 | 100 / 100 | P100 |

Clause counts among rows read: truth `n` = 8; truth `?` = 73; names `y` = 12; unexpected decisive `y` = 121; distinct flagged rows = **211**. A flagged row has any of those four outcomes; overlapping flags count once. The other **1,325** rows pass this reader's clause criteria. All **216** designated decisive rows retain an empty `R2_decisive`; none is assigned a decisiveness judgment.

Property counts among rows read: both answers correct `n` = 3; unambiguous `n` = 8; distinct failed rows = **8**; passed = **92**. A property item fails if either answer judgment is `n`.

The read was saved after each of sixteen 96-clause batches and two 50-property batches. All rows are now complete; there are no unread rows.

| Family | Read | Truth n | Truth ? | Names y | Unexpected decisive y | Distinct flagged |
|---|---:|---:|---:|---:|---:|---:|
| Animals | 192 | 1 | 10 | 1 | 12 | 24 |
| Countries | 192 | 0 | 3 | 9 | 17 | 27 |
| Tools | 192 | 4 | 13 | 1 | 9 | 27 |
| Foods | 192 | 0 | 8 | 0 | 13 | 20 |
| Transport | 192 | 1 | 7 | 0 | 12 | 20 |
| Instruments | 192 | 1 | 22 | 0 | 14 | 37 |
| Body parts | 192 | 0 | 2 | 0 | 28 | 30 |
| Materials | 192 | 1 | 8 | 1 | 16 | 26 |

## Judgments and unresolved items

Truth `?` records uncertainty or dependence on species, variety or sense; the specific reason is in `R2_comment`. Truth `n` means the stated clause is false or misleading in the intended ordinary sense. Generic descriptions are read as ordinary generic claims, not universal quantification over every exceptional specimen. The decisive judgment asks whether this clause alone supplies a recognizable identification, without the other eleven clauses or the bank's candidate list. Mere compatibility or a weak association is insufficient. Names include literal longer-word occurrences and the intended family's name, including disguised forms, as directed by the brief.

All flagged and uncertain judgments await author resolution after the independent readings. No human answers, `audit_app/results/`, pull output, audit website or D1 database have been read. The drafter's notes were read as cautions, not answers. The source sheets and concept senses/accepted variants supply the only bank material used; no stimulus was rewritten and no capture or simulation was run.

Patterns for the author:

- **Unspecified subtypes.** Many uncertain clauses describe one familiar subtype: honeybees, long-endurance submarines, consumer/arranger keyboards, tin whistles, or particular alloys and manufacturing processes. `concepts.json` fixes family, word and accepted forms but does not explicitly settle these narrower senses. Instruments have 22 uncertain clauses, including seven for `instruments/keyboard` and seven for `instruments/whistle`.
- **Name leakage.** `animals/ant:8` contains `ant` inside “antennae.” Nine country clauses use “state/states” as a country synonym. `tools/whisk:6` uses “utensils”; `materials/paper:8` names tissue and card. The latter semantic judgments, like all flags, are left for resolution. A supplemental literal scan of every accepted variant and literal family term found only the already-marked antennae occurrence; it did not assign judgments.
- **Unexpected identification cues.** 121 unmarked clauses supplied a recognizable identification to this reader. This is a reader judgment, not a measured single-clause naming rate. Body parts account for 28 of these; familiar injuries, actions and locations often identify the part on their own.
- **Overstated mechanisms or quantifiers.** Examples include a queen “ruling” an ant colony, chips or loud sounds on every blow, screws always needing masonry anchors, amplification itself sustaining guitar strings, and glazing bricks to save weight. Comments explain the eight truth-`n` judgments.
- **Facts I could not independently settle.** `animals/fox:7` names three predators; `materials/cement:0` compares particle size with flour. I left both `?` rather than adopting the drafter's factual assurance. Other `?` rows identify the particular sense, variety or qualification that remains open.

All eight failed property items remain unresolved:

| Item | Both correct | Unambiguous | Reason |
|---|---|---|---|
| P005 | n | n | “Can be burned as fuel” does not categorically exclude animal remains. |
| P027 | y | n | “Connected to the foot” needs to distinguish anatomical connection from attached leather footwear. |
| P037 | n | n | Human flesh physically can be cooked and eaten; customary food use is a narrower question. |
| P083 | y | n | Underwater travel needs a normal-role or self-propulsion qualification to exclude a transported object. |
| P084 | y | n | Crew membership depends on whether the submarine is crewed. |
| P086 | y | n | The size contrast assumes an ordinary crewed submarine, excluding small uncrewed/model types. |
| P087 | n | n | Referee use switches from the clause set's musical/tin-whistle sense to a signaling whistle. |
| P096 | y | n | The pedal answer assumes a pedal bicycle, excluding common children's balance bicycles. |

P087 is also a cross-item sense issue: the whistle clauses describe a finger-holed musical tube, while this property asks about a referee's whistle. This reading does not select or rewrite the intended sense. For properties marked `y/n`, the supplied labels fit the ordinary intended reading, but the wording also admits a reasonable competing reading or type. Every flagged row has an explanatory `R2_comment`.

## Preservation and provenance

The CSV copies preserve all source rows, order, headers, UTF-8 BOM, and every non-R2 cell. Source R1/R2 and resolution columns were verified empty before work. Each checkpoint validates non-R2 equality and empty R1/resolution cells, then atomically replaces each output file. These checks validate preservation, not the substantive judgments.

Source SHA256:

- `clue_audit_2026-09-15.csv`: `be394ae9911e0dcb001669ec464c6fd609c730f879482f02e7fe2cc2bec7ed5d`
- `property_audit_2026-09-15.csv`: `a474025e969bf3b62ad122dacf58730984f2cdb99d2765394ab7b922c18cfd3e`
- `concepts.json`: `3738fe24032b1cd14000d2c7f22bd128ca4c969295f900d7901a7e680ef268e3`

Both source sheets matched their committed bytes at the start and end of the read. Final validation checked all 1,536 clause rows and 100 property rows, exact column order, every non-R2 cell, complete legal R2 values, and the 216 required empty decisiveness cells. The source sheets, `concepts.json` and unrelated work were left unchanged. No human-reader agreement or author resolution is inferred from an R2 pass.

R084 retains ownership of the stimulus bank and eventual freeze; R052 retains manuscript and protocol decisions. This reader owns only these two R2 copies and this record.
