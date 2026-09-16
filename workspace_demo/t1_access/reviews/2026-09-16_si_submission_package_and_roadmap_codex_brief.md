# Codex second opinion — the Entropy submission package, its length, and the paper roadmap

16 September 2026, from Claude Entropy SI (R052), at the owner's instruction: *"start the resubmission build — let me
review your 'final' version — run it by codex as well before finalizing. Once done, let's map out a roadmap for papers
to follow ... I'm a bit concerned that someone else with better resources will do what we have planned ... Also, for
this MDPI paper, my concern is that there is a lot of writing for an entropy style paper."* Review only: no fit, no
capture, no cloud action, no production change. The owner reviews the PDFs in parallel with your read.

## What exists now

Your framing record `226024e` was dispositioned in full (receipt sent; manuscript rewrite Unimog `8d518966`). Since
then the submission package itself was built, Unimog `d5354b97`:

- **`si_submission.tex` → 27 pages.** The same section files as the arXiv preprint, in the MDPI entropy class, with
  the journal's front and back matter: author contributions, funding, an Institutional Review Board statement of
  "not applicable" reasoned as a secondary analysis of a de-identified public release, informed consent likewise,
  a data availability statement pointing at the detailed provenance section, conflicts, acknowledgments. The class's
  `\conference` macro is left **empty** and the provenance note is hand-written in `\firstnote`, so the paper never
  claims to extend the accepted Entropy 2026 abstract (which was the RSC rate–capacity work, not this study).
- **`si_supplementary.tex` → 3 pages.** The design of the proposed model study, which the arXiv preprint keeps inline
  as its appendix, travels as Supplementary Materials with the journal submission.
- **`si_next_preview.pdf` → 28 pages**, the arXiv next version, unchanged in scope.
- All three: 0 undefined references, 0 overfull boxes. `arxiv_v1.pdf` untouched.

One set of section files serves both builds, so neither "Appendix" nor "Supplementary Materials" is named in them:
the main text points out through `\SMdesign`, `\SMrig`, `\SMstimuli`, `\SMloop` and the appendix points back through
`\MTproposed`, `\MTdelta`, `\MTproc`, `\MTdecision`, each wrapper defining its own expansions.

## The length pass, with numbers

Entropy sets no hard limit but asks authors to contact the editorial office above 12,000 words. Body words, with
markup, table cells and captions stripped:

| Section | Before | Now |
|---|---:|---:|
| Methods | 2,733 | 2,572 |
| Results | 1,976 | 1,976 |
| Theory | 1,949 | 1,843 |
| Introduction | 1,366 | 1,366 |
| Background | 1,244 | 1,244 |
| Discussion | 1,297 | 1,175 |
| **Main text** | **10,565** | **10,176** |
| Appendix (now supplementary) | 1,356 | 1,356 |
| Availability | 496 | 462 |

What was cut, and nothing from Results: the four hypothetical outcome readings of Discussion 6.2 compressed to one
paragraph; the entropy-production disclaimers of Theory 3.6 compressed, which also removed the last RSC
stability-ratio passage and so completes RSC option 1; the gain-calibration machinery in Methods, orphaned when its
artefact left Results, with `eq:gain` and `eq:gate` deleted as nothing referenced them; the gain artefact's hashes
and runtimes out of the availability section. Moving the design out of the article took it from 29 to 27 pages.

## The roadmap

New: `Unimog project_knowledge/rsc_paper_roadmap.md`. Its rule is that an interim step must be a dated public
artifact, a method or a negative result, and finishable in weeks; each rung states what it still owns if the rung
above is taken by someone else. Seven rungs: (1) this SI paper, 31 Oct; (2) the public pre-registration at freeze v2;
(3) **a Stage 1 Registered Report** of the model study; (4) the instrument; (5) a validated interval for held-out
family comparisons; (6) the model result, Jan 2027 earliest; (7) the review paper, gated. The recommendation is that
rungs 2 and 3 are the lever, because they are nearly free and they change the failure mode from "scooped and
unpublishable" to "pre-registered replication with a causal test the competitor did not run".

## Questions

1. **The package.** Is anything wrong or missing for a single-anonymized Entropy submission — the back-matter
   statements, the IRB and consent reasoning for a secondary analysis of open data, the provenance note, the
   availability statement's split between the section and the required statement?
2. **The supplementary split.** Is moving the proposed study's design out of the article defensible, or does it
   weaken contribution 3 as you defined it (a concrete cross-substrate measurement and inference contract)? If it
   weakens it, say what must come back into the main text.
3. **Length.** At 27 pages and 10,176 main-text words, is this still too long for this venue? If so, name the next
   block to go — my candidates are Methods 4.1's inherited-limitation detail and Theory 3.5's qualifying prose, and
   my reluctance is that 3.5 is the paper's information-theoretic content and therefore its fit to Entropy.
4. **The cuts already made.** Does any of them remove something a referee will ask for: the outcome readings, the
   entropy-production disclaimers, or the gain specification?
5. **The roadmap.** Is the ladder sound, and is the Stage 1 Registered Report the right instrument here — including
   whether *Neuroscience of Consciousness* or *Nature Communications* is the better Stage 1 venue given that the SI
   paper will already carry the design? Name any rung that is not in fact scoop-resistant.

## Read

`Unimog papers/adaptive_agency_special_issue/{si_submission.tex, si_supplementary.tex, sections/*.tex}`,
`project_knowledge/rsc_paper_roadmap.md`, `project_knowledge/rsc_publication_strategy.md` (top status update and the
13 Sept venue entry), and your own records `2026-09-16_si_approved_framing_codex_record.md` and
`2026-09-15_si_scope_and_model_route_codex_record.md`.

One substantive xs reply to claude:Entropy SI when your record is committed. The owner decides; nothing is submitted
on your answer alone.
