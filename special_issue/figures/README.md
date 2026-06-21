# SI figures — computational engine + empirical pipeline

Figure-generation for the Entropy SI ("Entropy, Annealing, and the Continuity of
Agency in Human–AI Systems"). Plan + findings: `project_knowledge/rsc_publication_strategy.md`
(§ "SI paper plan", "Empirical-data probe and the reframe").

Run with the project venv:
`/Users/pietervanrooyen/Unimog-Projects/photography/papers/ai_dissipative/presentation/.venv/bin/python <script>`

## Computational engine (the simulation legs)

- **`rsc_engine.py`** → `si_universality.pdf` — **teeth B + the Kingman-universality check.**
  Generalizes the proceedings M/M/1 demo to GI/G/1 (Gamma arrival/service with matched
  mean, varied c²; c²=0 = deterministic). Shows (a) SR diverges as (1−CR)⁻¹ for *every*
  process — universal exponent; (b) SR·(1−CR) → (c_a²+c_s²)/(2Dt), the Kingman prefactor
  (matches for low-variance processes; bursty ones are pre-asymptotic at CR≤0.96); (c) the
  accuracy/recoverability decoupling is robust across all processes.
- Proceedings baseline: `../../adaptive_agency_proceedings/figures/rsc_simulation.py`.
- **`rsc_estimators.py`** → `si_estimators.pdf` — **teeth C.** SR̂ = N_uncert/N_cert from a
  window of n commitments (CR̂ = SR̂/(1+SR̂)): (a) consistent, rel-SE ~1/√n; (b) estimation
  is hardest near the boundary (rel-SE at n=2000 climbs ~0.17 → ~5 as CR→0.95 — certified
  events become rare); (c) early-warning detection ROC for "flag CR≥0.85" — AUC 0.90
  (n=200) → 0.97 (n=1000) → 1.00 (n=5000). Invertibility-MI estimation is harder (needs a
  joint observable); noted as future work in the text, not in this figure.
- **`rsc_instrument.py`** → `si_instrument.pdf` — **uses the effective-capacity machinery (not just cites it) and operationalizes the invertibility condition.** (a) decay exponent estimated from counts θ̂⋆=−ln(P_unc)/Δt matches μ(1−CR); (b) the closed-form SR(θ⋆) at the *theoretical* exponent tracks the simulated SR across the whole CR range (Eq. exact, not asymptotic); (c) the invertibility MI I(δE;Z) collapses from 0.46 bit → 0 as CR→1, in lockstep with recoverability — Eq. 3 made a measured quantity. Answers the round-2 review (cite→compute) + resolves concern 7. Manuscript Sec.6.
- **`rsc_coupled.py`** → `si_coupled.pdf` — **the decoupling is derived, not assumed**
  (answers the referee objection that the baseline draws accuracy independently of load).
  Accuracy and recoverability are made different functionals of the *same* single-server
  sojourn: recoverability = resolution within the deadline Δt (hard threshold); accuracy =
  saturating in the active deliberation before the deadline, bounded below by a fast-heuristic
  floor a_floor>½. (a) As CR→1 recoverability collapses while accuracy (now load-dependent, it
  falls) degrades only to a_floor (0.94→0.05 vs 0.88→0.72 at a_floor=0.65). (b) the decoupling
  gap equals the fast-heuristic quality. Vanishes as τ0→Δt or a_floor→½ (stated boundary
  conditions). Fig 4 in the manuscript.

## Empirical figures (paper-ready)

Read from the pinned snapshots (paths overridable via env: `GH_DATA`, `MWH_DATA`; defaults
`/tmp/gh`, `/tmp/mwh`). Re-pull the raw data with the `empirical/` fetchers first.

- **`fig_github.py`** → `si_github.pdf` — GitHub PR review queues. (a) public-apis: the open-PR
  backlog blows up to ~1400 and median open-PR age to ~400 d (the in-the-wild **boundary
  crossing**, leg 3). (b) within-repo queue *age* couples to queue *size* only past the boundary
  — median Spearman **+0.87** in the three repos that crossed (public-apis, next.js, MunGell)
  vs **+0.14** in well-triaged repos (flask, cli) that hold age decoupled from size while
  sub-critical (machinery, leg 1).
- **`fig_wikipedia.py`** → `si_wikipedia.pdf` — Wikipedia recovery (leg 1, second substrate).
  (a) within-wiki, recovery **coverage** (revert fraction) falls as editing load rises, median
  Spearman **−0.70**. (b) negative in **all 9 wikis** (−0.42 to −0.88) — robust, not a
  single-community artifact. **Honest null:** revert *latency* showed no consistent load
  relationship (median +0.15, signs split across wikis) — reported in stdout, not plotted, not
  claimed.

## Empirical pipeline — `empirical/` (the two real substrates)

Probe prototypes (write to `/tmp`; the paper figures above supersede their plots). **Raw data is
NOT committed** (large) — re-pull from the pinned snapshots below.

**GitHub** (PR lifecycles via authenticated `gh` GraphQL; pull pinned **2026-06-17**):
- `gh_fetch.py` (flask, cli, vercel/next.js), `gh_fetch_floods.py` (public-apis,
  MunGell/awesome-for-beginners, EddieHubCommunity/BioDrop).
- `analyze_gh.py` — queueing machinery (utilization → backlog → latency), within-repo.
- `analyze_blowup.py` — backlog blow-up → queue-age divergence (the in-the-wild crossing;
  public-apis +0.87, MunGell +0.78, next.js +0.89).
- `analyze_episode.py` — Hacktoberfest October arrival floods vs the queue.

**Wikipedia** (`mediawiki_history` dumps, snapshot **2026-05**; editions got, iu, nv, co,
gd, gv, kw, li, wa):
- `dl_mwh.py` — downloader (size-gated). `analyze_mwh2.py` — within-wiki recovery-coverage
  vs load (revert fraction falls with load in all 9; median Spearman −0.70), ns0 + bots
  removed. Columns pinned: entity=col2, type=col3, ts=col4, editor=col9, namespace=col33,
  bot-flag=col15, reverted=row[−6], seconds-to-revert=row[−5].

## The three-leg empirical case (see strategy doc)

1. **Machinery + in-regime slopes** — healthy GitHub repos + Wikipedia.
2. **The (1−CR)⁻¹ divergence** — Kingman (analytic) + `rsc_engine.py`.
3. **In-the-wild crossing** — GitHub backlog blow-ups (`analyze_blowup.py`).
