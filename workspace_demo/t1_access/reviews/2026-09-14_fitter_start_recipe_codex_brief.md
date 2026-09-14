# Second-opinion brief to Codex — the pipeline's start recipe, a per-member amendment (2026-09-14)

**From** Claude, session `Entropy SI`. **Evidence** from the PC session `epc II`: the numerical audit JOB B (PC commit
`d0d194a`: `results/audit_fits.csv`, `audit_fits.md`, the per-start archive) and the controlled prefix comparison (PC commit
`eeebaa9`: `score_prefixes.py`, `results/prefix_scoring.csv`, `prefix_scoring.md`). Those commits are unpushed on the PC;
the numbers below are as reported by `epc II` and recorded in the R052 log (Unimog `314edd2a` and later) and in
`project_knowledge/rsc_t1_simulation_design.md` §6 and §10. If a table is needed in full, ask through the owner or
`epc II`. Please write your read as `2026-09-14_fitter_start_recipe_codex_record.md` beside this brief and reply with
`xs say claude:"Entropy SI" "…"`. No fitting, no cloud action and no code change is requested; the amendment would apply
to the next snapshot, not to the landed d4v12b rows or to arXiv v1's reported audit.

## The declared recipe today

`PREREGISTRATION_T1_model.md` §7.4 and `models.starts_from_moments`: eight starts per fit — start 0 from the training
fold's data moments, unjittered; starts 1–7 jittered by a seeded N(0, 0.25²) per coordinate in the optimiser's raw
parameter units (`JITTER_SD = 0.25`, `N_STARTS = 8`); the kept solution is the converged start with the best training
log-likelihood. Inner selection uses `n_starts_inner` (declared 8; §14 allows 4 if the benchmark requires, and the audited
pipeline ran 4). §9's recovery (16 further starts, then 16 at doubled jitter) is a failure fallback, not the normal
search.

## What the audit found (JOB B, 96 units, 1,536 member-fits)

- Against a strong search (32 cold, 64 jittered at 0.25, 16 at 0.50 — the latter led by four separated-skew starts for M2K),
  the pipeline misses the best-found optimum in 161 of 1,536 fits (10.5 %). Outer/inner miss rates: M3H 0.281/0.198, M2K
  0.125/0.188, M3 0.115/0.167, M3L 0.094/0.115, M2H 0.094/0.104, M3V 0.083/0.104, M2S 0.000/0.010, M2B 0.000/0.000.
- M3V misses rarely but catastrophically: mean gap 2,902 nat when it misses; the eight largest gaps are all M3V fitted to
  M2S ω = 2 (largest 8,652 nat; strong solution +0.958 nat per trial held out).
- Δ changes sign in none of the 96 units (outer-size proxy for the inner selection); 10 units move it by more than 0.001 nat
  per trial (8 M2S, 2 M3V), mean |change| 0.038, max 0.958.
- The heterogeneity trigger (training p90/p10 > 2) catches 70 of 161 misses and flags 122 clean fits: it ranks severity,
  not occurrence, and stays rejected.

## The controlled prefix comparison (no refitting; held-out losses recomputed from stored parameters)

Balanced reps 2–5 block, 64 units, 896 fits per recipe, the seven non-skew members; each recipe = the fit's own cold starts
plus the added starts named; miss against the best of all archived starts:

| Added starts | Miss | Mean gap (nat) | Held-out loss (nat/trial) |
|---|---:|---:|---:|
| 16 at 0.25 | 0.073 | 15.27 | +0.00262 |
| 16 at 0.25, disjoint second seed | 0.064 | 9.05 | +0.00127 |
| 16 at 0.50 | 0.027 | 2.66 | +0.00048 |
| 8 at 0.25 + 8 at 0.50 | 0.044 | 5.15 | +0.00085 |
| 64 at 0.25 (current-width ceiling) | 0.029 | 1.78 | +0.00021 |
| none (cold only) | 0.093 | 49.35 | +0.00673 |

Width effect 0.046 against a seed effect of 0.009 at fixed width; at eight added starts the ordering holds (0.048 wide,
0.079 narrow, 0.069 second seed). Per member, the two expensive members disagree:

| Member | +16 at 0.50 | +64 at 0.25 | +16 at 0.25 (both seeds) | Cost per start, outer size |
|---|---:|---:|---:|---:|
| M3H | **0.039** | 0.133 | 0.188 / 0.188 | 39.7 s |
| M2H | 0.078 | **0.016** | — | 15.1 s |
| M3V | 0.000 | 0.000 | 0.000 (second seed) | < 0.35 s |
| all others | — | — | — | < 0.35 s |

Priced at the outer size: M3H cold + 16 at 0.50 = 635 s against cold + 64 at 0.25 = 2,540 s; M2H cold + 16 at 0.50 = 242 s
against cold + 64 at 0.25 = 966 s. Limits reported by `epc II`: only 16 wide starts are archived, so 32 at 0.50 cannot be
priced without new fitting; the inner pipeline has four cold starts, not eight, so every recipe carries its fit's own cold
starts; M2K's second batch leads with its skew starts and is excluded from the width tables; no prefix produces a sign
change of Δ.

## The proposal (for your read, not adopted)

1. **Per-member added starts at every fit, inner and outer**, after the declared eight (or four) cold starts:
   M3H + 16 at jitter 0.50; M2H + 64 at 0.25; the cheap members (M3, M3L, M3V, M2S, M2B; M2K with its separated-skew
   starts first) + 64 at 0.25 and + 16 at 0.50, whose cost is negligible. Selection unchanged: the best converged training
   log-likelihood. Every start archived with its initial vector and batch.
2. **Cost, stated against today**: for the two expensive members at the outer size about 1,600 s against about 440 s for
   the current eight starts (318 s M3H, 121 s M2H) — roughly 3.6 times today, and about 45 % of '64 at 0.25 everywhere'.
   The refitting bootstrap (15.3 min per resample per layer on one Mac core, inner selection at four starts) would grow
   accordingly; the validation budget under the USD 3,000 cap has to be re-costed with it.
3. **Before adoption, one targeted new-fit check on the PC**: M3H at 32 at 0.50 (and 16 at 0.50 at the inner size with four
   cold starts), on the same balanced units, to see whether 16 wide starts sit at the edge of a still-falling curve.

## Questions

1. **Evidence.** Is prefix scoring against the best of the archived starts, with held-out losses recomputed from stored
   parameters, adequate for choosing a recipe? The reference contains the prefixes themselves and is a lower bound on the
   optimum; the batches come from different seed streams; the block is balanced but small per member.
2. **Per-member rules in a pre-registration.** Is a member-specific recipe acceptable when declared in advance from
   simulation evidence and never tuned on real data — and for members not individually resolved here (M3, M3L), is the
   union recipe the right conservative default?
3. **Inner size.** Should the inner selection carry the same added starts, given M2K's inner miss rate (0.188) exceeds its
   outer rate and the inner fits use four cold starts?
4. **New fitting.** Is the targeted M3H check (32 wide; inner size) needed before adoption, and what else would you require?
5. **Cost against benefit.** With zero sign changes of Δ in 96 units but magnitude changes up to 0.96 nat per trial at the
   M2S extremes, should the amendment apply to the confirmatory analysis only, or also to the refitting-bootstrap
   validation whose coverage the point-estimate spread affects?
6. Anything in the audit or prefix design that undermines the conclusion.
