-- audit.raconteur-road.com — D1 raconteur-audit
-- items:   every clause and property question, pushed from the committed audit sheets by push.py.
-- readers: one row per human reader; items = JSON array of the item ids they were dealt (assignment.json).
-- marks:   written by the app; PK (token, id) = one mark per reader per item, last write wins.
--          m = JSON: a clause {t: y|n|?, nm: y|n, d: y|n, c}; a property question {ok: y|n, un: y|n, c}.
--          via = 'row' (clicked on the item) or 'card' (the "rest are fine" button).

CREATE TABLE IF NOT EXISTS items (
  id    TEXT PRIMARY KEY,
  kind  TEXT NOT NULL,             -- 'clue' | 'prop'
  body  TEXT NOT NULL              -- JSON, see push.py
);

CREATE TABLE IF NOT EXISTS readers (
  token    TEXT PRIMARY KEY,
  slot     TEXT NOT NULL UNIQUE,
  name     TEXT NOT NULL,
  items    TEXT NOT NULL,          -- JSON array of item ids in display order
  disabled INTEGER NOT NULL DEFAULT 0,
  updated  TEXT
);

-- marks: the first design's table, one set of marks per LINK. Kept read-only as history: the links were
-- forwarded to several people (owner, 18 Sept), so one link is not one reader. Its rows were copied into
-- answers under sid 'legacy' on the day.
CREATE TABLE IF NOT EXISTS marks (
  token TEXT NOT NULL,
  id    TEXT NOT NULL,
  m     TEXT NOT NULL,
  via   TEXT NOT NULL DEFAULT 'row',
  ts    TEXT NOT NULL,
  PRIMARY KEY (token, id)
);

-- answers: one row per (link, visitor session, item). A session id is made in the visitor's browser on
-- first load and kept there (and in their personal resume link), so everyone who opens a shared link
-- keeps their own answers. No name or other personal detail is stored.
CREATE TABLE IF NOT EXISTS answers (
  token TEXT NOT NULL,
  sid   TEXT NOT NULL,
  id    TEXT NOT NULL,
  m     TEXT NOT NULL,
  via   TEXT NOT NULL DEFAULT 'row',
  ts    TEXT NOT NULL,
  PRIMARY KEY (token, sid, id)
);
CREATE INDEX IF NOT EXISTS answers_by_item ON answers (token, id);
