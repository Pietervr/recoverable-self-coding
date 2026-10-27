# Bounded-comparison qualification: Codex review of the production code and the design-freeze draft (round 4)

27 October 2026, R052. Owner go for steps 1-2 ("yes, do 1 and 2"). A Claude job agent built the S1 procedure and the S3
catalogue of your `reviews/2026-10-27_method_repair_codex_record.md` as production code and wrote the design-freeze DRAFT:
RSC `049c325` (code + tests, config hash 890f65ccba39), `77789e1` (Mac smoke run, 30/30 settings, mean 505 CPU-s per
point), `98aa7ed` (`bounded/DESIGN_bounded_v1.md`, not adopted, + one pointer row in PREREGISTRATION section 15). The
build brief: `/Users/pietervanrooyen/Unimog-Projects/prompts/2026-10-27_r052_bounded_qualification_build.txt`.
`models.py`, `analyze.py`, `simulate.py` are unchanged (verified: empty diff over the three commits).

Review, as the gate before the owner adopts the design and before any Lengau compute:
1. Does `bounded/` implement S1 exactly (M3S likelihood and start; 8 cold + 64 keyed M2S starts; 3 stratified outer folds;
   no inner selection; equal-weight joint-density ensembles; d_c, clipping at 0.03, fixed family weights; unavailable
   rule) and `calibrate.py` the S1 interval/critical-value construction with the stated error allocations? Find bugs.
2. Generators and catalogue against S3: the 30 settings, parameters, seed namespaces, attempt counts. The agent's
   declared choices are in DESIGN section 13 - judge each (esp. 2 non-converged-after-recovery is not unavailable,
   6 the M3S starting scale borrowed from M3H, 7 the values S3 left open, 8 lambda null in the catalogue).
3. The omega=2 M3S quadrature error 1.545e-6 nat/concept against a 1e-6 target, driven by the frozen TRAP_POINTS=96:
   acceptable for qualification (relative to the 0.03 cap and the decision scale), or must a new snapshot raise it?
4. Determinism and provenance: config hash coverage, deterministic row digest, seed rule, unavailable recording.
5. The design draft: complete and consistent with S1/S3 and with the paper text (methods.tex sec:m-amend last paragraph,
   results.tex sec:r-bounded)? List what must change before the owner can adopt it, and what the development reserve
   (benchmark, boundary lambda search, gain re-certification) still needs from code.
6. The smoke results: anything alarming (e.g. G14 at placeholder lambda=0.5 gave T=+0.0022, G13 +0.00005)?

No live actions, no edits outside `reviews/2026-10-27_bounded_build_codex_record.md` and scratch under
`bounded/dev/codex/`; you may run the tests (quick tier; slow tier only if under ~30 min CPU). Do not commit.
Record: blocking findings first (file:line, exact fix), then non-blocking, then a verdict line: ADOPTABLE AFTER FIXES /
NOT ADOPTABLE.
