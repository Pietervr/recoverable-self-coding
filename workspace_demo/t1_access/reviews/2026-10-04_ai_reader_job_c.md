# AI-reader qualification, job (c) of 4 October 2026: COMPLETE, 600 of 600 ok - mechanically NOT admitted (60 of 63 easy gray; 61 required; one owner adjudication would decide)

R084, 4 October 2026. The go: the owner's standing reader go of 3 October, bound by R052 in
`stimuli/photo/AIREADER_GO.json` (RSC `82180df`) to Codex's favourable revision-17 record RSC `410b580`
(`reviews/2026-10-04_reader_rev17_codex_record.md`, sha256 `a647f024...`) and the 25-field package (digest
`4517553a0615436d8a0c384849c43a206fd9e428729d1d91ef6a0d68bf4b3e35`, RSC `977655f`).

## Before the run

- Job (b) archived: `archive_job_b.py --apply` (RSC `4c473c3`; journal `734ea772...` and its closed clock in
  `2026-10-03_ai_reader_job_b_archive/`); job (b) stays STOPPED, unscored, never re-used. Fresh state: no journal, no clock.
- Checks (02:0x UTC): `ai_reader_exec.package()` on the live tree equals the bound package; the owned CLI tree hash
  `ced09ec2...` live = bound; `stage_a_guard.require_go(...)` against `package_at_commit` accepts the go (favourable,
  reviewed commit `977655f`); `codex login status` (owned binary): "Logged in using ChatGPT"; limits as declared (600
  planned, 3 tries per request, 660 attempts, 120 s per attempt, 21,600 s job clock, 2,000 answer characters, 20 MiB raw);
  photo directory clean; no local model job on the Mac; memory 97 % free; network reachable.
- Launch: `.venv-image/bin/python stimuli/photo/ai_reader_exec.py run` under `caffeinate -i`, fully detached
  (vehicle/engineering/xentry_vm/detach.py pattern), outputs kept in `2026-10-04_ai_reader_job_c/`.

## The job

- Started 2026-10-04T02:09:04Z; runner exit 0 at 03:17:36Z with the receipt **COMPLETE, "all 600 requests final"**.
- Smoke passed (`001.b2df6c4dfae2.1`).
- 600 requests final in **600 attempts** (of 660): **600 ok**; no provider failure, no retry, no isolation, no overflow,
  no capacity refusal, no structural failure, no hold.
- Clock: one session, closed COMPLETE, 4,111.4 s live; receipt seconds_total 4,171.3 s (incl. the 60 s close allowance)
  of 21,600 s; closure marker present, naming the journal (`clock.closed.json`).
- Journal: `stimuli/photo/ai_reader_raw_responses.jsonl`, sha256 `0260f350abfd97b662f18a040d00255dab9a3399285637becf97ec7c25cd00e5`,
  receipt journal_sha256 `1a25a610...` (committed RSC `c8db934`).

## The score (`ai_reader_score.py`, scientific mode, frozen rule) - `2026-10-04_ai_reader_job_c/score.json`

| | n | correct | accuracy |
|---|---|---|---|
| **gray easy (the gate)** | 63 | **60** | 0.952 |
| colour easy | 63 | 61 | 0.968 |
| gray all | 300 | 224 | 0.747 |
| colour all | 300 | 246 | 0.820 |

Gate: one-sided exact (Clopper-Pearson) 95 % lower bound >= 0.90, i.e. at least **61 of 63** easy gray. 60 of 63 gives a
lower bound of 0.8815: **not admitted mechanically**. `adjudications_needed: 1`.

The three easy gray referrals (raw answers as returned; the pictures are the delivered gray views, identified by
`delivered_image_sha256` in the score file):

| item | intended concept | human recognizability | reader's answer | code |
|---|---|---|---|---|
| `3996843626` | paint | 0.933 | "Paintbrushes" | ERR_NONMATCH |
| `9f5d8717bd` | pearl | 0.917 | "Oyster" | ERR_NONMATCH |
| `f7d4961b2f` | christmas_card | 0.818 | "Greeting card" | ERR_NONMATCH |

By the rule declared before any revision-12 answer (`AI_READER_JOB.md`, order of operations 7): an easy gray referral
the OWNER adjudicates as naming the intended object - the picture and the raw answer recorded before the decision - is
not a reader error, and an admission resting on it is reported as "admitted with N owner-adjudicated items". One such
adjudication would reach 61 of 63. That decision is the owner's; nothing here adjudicates. Without it the audit holds.

Descriptive (no criterion): by stratum gray 0.51 / 0.84 / 0.89, colour 0.63 / 0.87 / 0.96; paired all 219 both, 27
colour only, 5 gray only, 49 neither; easy 60 both, 1 colour only, 0 gray only, 2 neither. 76 referrals in all (every
non-match on either view), listed in the score file for the owner.

## Scope carried (Codex `410b580`)

- Job (c) is the THIRD pass over this already exposed 600-request panel (job (a) all 600; job (b) 219): evidence for the
  prospective rule, never a blind calibration. Job (a) remains not admitted; job (b) stopped and unscored.
- Partial stdout text may remain retained evidence on a final error, never an admitted answer (no final error occurred
  in this run).
- The capacity detector covers VISIBLE retained capacity text only (no capacity event occurred in this run).
- Matching/adjudication limits and the scientific gates carry; this record is the mechanical result, not an admission.
