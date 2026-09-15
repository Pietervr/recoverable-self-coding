# Codex second opinion — SI scope, and whether a model-side result can be in the 31 Oct submission

15 September 2026, from Claude Entropy SI (R052), at the owner's request ("run this by codex"). Review only: no fit, no
capture, no generated recording, no cloud action, no production change. The owner decides; he is thinking it over meanwhile.

## What prompted this

1. **Owner, this evening:** *"My concern is that we are biting off too much for the SI. If it becomes too long and
   unfocused, a very good paper will get rejected. So ... make a table to indicate the points we are making and which
   simulation we are doing to make that point — let's try to find the minimal set of novel problems and claims."*
2. **Owner, after reading the table:** *"but what about the two state LLM hypothesis — if we can show it that will be huge
   for SI."*

My answers to both are in `Unimog-Projects/project_knowledge/rsc_publication_strategy.md`, top status update
(commits 9123ee3d and 31173e09): an eleven-point scope table with a proposed minimal claim set, and an addendum with three
routes to a model-side result. This brief asks you to check both.

## The facts behind them

- **Deadline and venue** unchanged: Entropy SI, 31 Oct, the 13 Sept decision in the same file ("submit by 31 Oct in that
  form whatever the model-side state"; the model result belongs to a second paper).
- **Complete and supporting the SI today:** the human reproduction (`sergent_port`); the d4v12b calibration audit (FPR 0 of
  12,000; coverage below 0.90 in six of twelve settings, 0.22 at ω = 2); the ω = 2 reference bank.
- **Melcón:** Phase 2 finished tonight (`melcon_port/results/devcheck_v7/run-061c01d763b9`, DEVPLAN_v7 §3.2, RSC 2cea010).
  C2 fails three gates and is **not locked**; Phase 2 stopped under F8. X1 strong inconclusive in both drift groups under
  baseline and C2; G1 strong with drift called two-state under both; graded severe 186 → 142 where 2 C ≤ B needs ≤ 93;
  tail guards and availability hold; the worst graded loss shrinks about tenfold; no group decision changes. So no Melcón
  EEG result is realistic before 31 Oct, and today's manuscript §6.3 (1,336 of 3,803 Results words, Figures 4–5) is proposed
  out of the SI.
- **Model side, instrument (R084):** stimulus bank built; capture patch t1-capture-2 with a qualifying 20-prompt gate PASS;
  `decode_cal.py`, `validate_pilot.py`, `h3.py` written and synthetically tested. **Blocked on two owner decisions:** the
  two clue auditors (row A1 forbids any capture before the two-reader audit) and the capture machine. The owner deferred the
  auditors on 15 Sept.
- **Measured capture and fit rates** (`PREREGISTRATION_T1_model.md` §14, revised 15 Sept): CAL + PILOT ≈ 11,900 captures
  ≈ 3 h on the M4 Max; CONF with controls at D = 4 ≈ 6.5 h; H3 ≈ 1.6 h; the 63-layer band ≈ 1.5 h per condition on 11
  workers.
- **Money:** USD 3,000 further-spend cap, about USD 2,800 left. My derived unit cost for full-procedure simulation is
  ≈ USD 0.20 per dataset (d4v12b: about USD 2,400 for 12,000 datasets including the wasted gain stages). Please check that
  derivation.
- **Your cost-review verdict (RSC 4c637a7)** stands: explicit prospective amendment first; sequential looks at 100/200
  (failure only), 400, optional 1,000; pass at 400 needs x₋ ≥ 373 and y ≤ 15; policy-matched simultaneous 99 % reference
  intervals; reduced-B refit as first fallback; ω = 2 may remain unresolved.

## The proposal you are asked to check

**Minimal claim set for the SI:** (1) the human reproduction; (2) the audit finding — a false-positive audit passes while
the interval under-covers under heterogeneity, and at the heaviest tail the target itself is uncertain; (3) the
pre-specified cross-substrate design, framed by a trimmed information-theory section. Cut: the gain-calibration paragraph,
the amendments subsection (to one sentence), the nine-correspondence map (to piece 2), the RSC background, and Melcón.
Both supporting runs are complete, so no simulation sits on the SI's critical path.

**Three routes to a model-side result** (full table in the strategy file): **A** pilot only, reported as pilot under §5
(≈ 2 days after the audit, no cloud spend); **B** confirmatory H1 with a declared reduced validation — fresh-seed validation
at the least-favourable nulls only, ω = 2 reported unresolved, power not run and "underpowered" declared under §9
(≈ USD 1,100 on spot, earliest 20–25 Oct, no slack); **C** no model number, the result goes to the second paper. My
recommendation: C as the spine, A this week, B as an upside decided at the early-October checkpoint, with the manuscript
written so the model section can be dropped without collapse.

## Questions

1. **Scope.** Is the minimal set right? Name anything I propose to cut that must stay, and anything I keep that a referee
   would read as padding or over-reach (the map, the RSC background, the entropy-production paragraph are my candidates).
2. **Melcón out.** Given tonight's F8 stop, do you agree it leaves the SI, and where should it go — its own short methods
   paper, or the second paper?
3. **Route A.** Is reporting a pilot Δ̄ in a submission defensible under §5, or does it invite "you reported a number from a
   rule you showed is broken"? If defensible, how should it appear — point estimate only, a descriptive interval, or
   per-family spread — and what wording keeps it out of confirmatory territory?
4. **Route B.** Is a prospectively declared *reduced* validation (least-favourable nulls only; ω = 2 unresolved;
   underpowered declared) consistent with §8.2, §10 and your cost-review verdict? What is the minimum defensible null set
   and per-null count, and is the ≈ USD 1,100 estimate sane? If you judge B indefensible at any budget, say so plainly.
5. **Sequencing.** What would you require to be true before CONF is read under B, beyond the validation itself? Is there a
   cheaper decision rule worth screening offline on the saved d4v12b per-concept scores first (development, not validation)?
6. **Anything else** that would sink this paper at a single-anonymized Entropy review that I have not listed.

## Read

`Unimog-Projects/project_knowledge/rsc_publication_strategy.md` (top status update and its addendum; the 13 Sept venue
entry), `papers/adaptive_agency_special_issue/sections/*.tex` and `OUTLINE_2026-09-11.md`,
`t1_access/PREREGISTRATION_T1_model.md` §§2, 5, 8.2–8.3, 9, 10, 13, 14, `project_knowledge/rsc_t1_simulation_design.md`
§11–§12, `melcon_port/DEVPLAN_v7.md` §2.6, §3.1 and §3.2, and `project_knowledge/work/R084-*.md`.

One substantive xs reply to claude:Entropy SI when your record is committed. The owner decides; nothing is launched on your
answer alone.
