# audit_app — the T1 stimulus audit, as a click-through page (audit.raconteur-road.com)

The clue bank (1,536 clauses) and the 100 H3 property questions must be checked by two readers before any
of them is captured (`PREREGISTRATION_T1_model.md` §3, amended 18 Sept 2026). Every item is read twice and
independently:

- **once by one of four human readers**, each dealt a quarter by `assign.py` (seed 20260918, 4 concepts of
  every family = 32 concepts and 384 clauses, plus 25 questions; a concept's 12 clauses stay together), on
  this page, filling the sheets' **R1** columns;
- **once by the AI reader** (Codex, a different developer than the Claude agents that drafted the clauses),
  on the whole bank, filling the **R2** columns offline.

An item passes only when both readers pass it; the author decides every other case, with both readers'
marks recorded beside the resolution. `stimuli/audit/CHECKLIST.md` is the checklist; the page asks the
same three questions in plain words (true / names it / gives it away on its own) plus the two for a
property question (both answers right / beyond dispute).

The page opens with a short account of why the check is done, for readers who know nothing of the study.

## Pieces

| File | What it does |
|---|---|
| `assign.py` → `assignment.json` | the seeded four-way split, from the committed sheets alone |
| `push.py` | loads items and readers into D1; `--links` prints the four invite links; `--name A=Anna` sets a display name |
| `pull.py` | progress per reader, and `results/*_R1_<date>.csv` (the sheets with R1 filled, plus reader, via, time) |
| `functions/api/{state,mark,bulk}.js` | read a reader's part; save one mark; save a card's "the other … are fine" |
| `public/index.html` | the page (vanilla, one file); `/r/<token>` is a reader's link |
| `test_api.py` | 33-check executable spec, **local rig only** (it writes and then removes marks) |
| `check_live.py` | read-only check of a deployed site: every link loads its dealt items in order; a bad token is refused |
| `amend_prereg_2026-09-18.py` | the §3/§15 draft amendment that introduced this design |

`readers.local.json` holds the tokens and is gitignored: the token in a link is the reader's identity,
and this repository is on GitHub. `results/` is gitignored until the audit closes, because it carries the
readers' names; the paper names them only with their consent (the page says so).

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

Marks: one row per (reader, item), last write wins; an empty mark deletes the row. A clause mark is
`{t: y|n|?, nm: y|n, d: y|n, c}`; a question mark `{ok: y|n, un: y|n, c}`; `via` records whether it was
clicked on the item or given by the card's "the other … are fine" button.
