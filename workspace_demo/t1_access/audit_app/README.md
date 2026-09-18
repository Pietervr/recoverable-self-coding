# audit_app — the T1 stimulus audit, as a click-through page (audit.raconteur-road.com)

The clue bank (1,536 clauses) and the 100 H3 property questions must be checked by two readers before any
of them is captured (`PREREGISTRATION_T1_model.md` §3, amended 18 Sept 2026). Every item is read twice and
independently:

- **by one or more anonymous human readers** on this page, filling the sheets' **R1** columns. The bank is
  dealt into four parts by `assign.py` (seed 20260918, 4 concepts of every family = 32 concepts and 384
  clauses, plus 25 questions; a concept's 12 clauses stay together), one link per part. The owner forwarded
  the links for onward sharing, so a link is a part, not a person: each visitor's browser makes a private,
  anonymous session id (kept in the browser and in a personal resume link, `?s=`), answers are stored per
  session, and each visitor sees the part's least-read cards first;
- **once by the AI reader** (Codex, a different developer than the Claude agents that drafted the clauses),
  on the whole bank, filling the **R2** columns offline.

An item passes only when it has at least one human read and the AI reader and every human reader pass it;
the author decides every other case, with all answers recorded beside the resolution. No names are stored. `stimuli/audit/CHECKLIST.md` is the checklist; the page asks the
same three questions in plain words (true / names it / gives it away on its own) plus the two for a
property question (both answers right / beyond dispute).

The page opens with a short account of why the check is done, for readers who know nothing of the study.

## Pieces

| File | What it does |
|---|---|
| `assign.py` → `assignment.json` | the seeded four-way split, from the committed sheets alone |
| `push.py` | loads items and parts into D1 (and copies first-version marks into `answers`); `--links` prints the four links |
| `pull.py` | sessions, answers and unread items per part; `results/answers_<date>.csv` and the sheets with R1 combined strictly |
| `functions/api/{state,mark,bulk}.js` | one session's view of a part (least-read cards first); save one answer; save a card's "the other … are fine" |
| `public/index.html` | the page (vanilla, one file); `/r/<token>` is a reader's link |
| `test_api.py` | 40-check executable spec, **local rig only** (sessions kept apart, reload on stale pages, least-read first; cleans up) |
| `check_live.py` | read-only check of a deployed site: every part's link loads exactly its items; a bad token is refused |
| `amend_prereg_2026-09-18.py`, `…b.py` | the §3/§15 draft amendments: the split and the AI reader; then anonymous, open readers |

`readers.local.json` holds the four part tokens and is gitignored (this repository is on GitHub). `results/`
is gitignored until the audit closes.

## Run it

```sh
python3 assign.py                       # only if the sheets change; the split is fixed before anyone reads
python3 push.py --local                 # local rig
wrangler --cwd . pages dev --port 8797 --ip 127.0.0.1
python3 test_api.py                     # 33 checks, cleans up after itself
python3 push.py --remote                # production D1 (items and readers; marks are never touched)
wrangler --cwd . pages deploy --branch main --commit-dirty=true
python3 check_live.py                   # read-only
python3 push.py --links                 # the four links to send
python3 pull.py --remote                # progress, and the R1 sheets
```

Hosting: Cloudflare Pages project `raconteur-road-audit` with D1 `raconteur-audit`, custom domain
`audit.raconteur-road.com` (dashboard ▸ Workers & Pages ▸ raconteur-road-audit ▸ Custom domains; the CNAME was
added by Cloudflare). The public raconteur-road.com site is not touched. `compatibility_date` is 2026-07-07
because the local runtime of wrangler 4.106 supports nothing later.

Answers: one row per (part, session, item) in `answers`, last write wins; an empty mark deletes the row. A
clause answer is `{t: y|n|?, nm: y|n, d: y|n, c}`; a question answer `{ok: y|n, un: y|n, c}`; `via` records
whether it was clicked on the item or given by the card's "the other … are fine" button. A page loaded before
sessions existed is told to reload rather than saving. The first version's table `marks` (one set per link)
is kept as history; its 13 answers (part A, 18 Sept 22:05-22:11 UTC) live on in `answers` under the session
`legacy-shared-link`, which is also the restore link for whoever made them.
