// GET /api/state?t=<token>&s=<session> — one visitor's view of a part: the items of that part and the
// answers THIS session has saved. Cards come least-read first (fewest sessions that answered any of the
// card's items), ties broken per session, so people who do only part of it spread over the whole part.
// Unknown or disabled token -> 404; no clause text leaves the server without a valid token.

import { J, SID_RE, reader } from '../_lib.js';

// Deterministic per-session tie-break (FNV-1a over session + card key).
function h(s) {
  let x = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
  return x;
}

export async function onRequestGet({ request, env }) {
  const q = new URL(request.url).searchParams;
  const token = q.get('t') || '';
  const sid = q.get('s') || '';
  const r = await reader(env, token);
  if (!r) return J({ error: 'not found' }, 404);
  if (!SID_RE.test(sid)) return J({ error: 'bad session' }, 400);

  const { results: rows } = await env.DB.prepare('SELECT id, kind, body FROM items').all();
  const byId = new Map(rows.map((x) => [x.id, x]));

  // How many distinct sessions have answered anything on each card of this part.
  const { results: cov } = await env.DB.prepare(
    'SELECT id, sid FROM answers WHERE token = ?1'
  ).bind(token).all();
  const readersOf = new Map();
  const cardOf = (id, body) => (id.startsWith('c-') || id.startsWith('i-') ? body.key : 'questions');

  const groups = new Map();
  for (const id of r.order) {
    const x = byId.get(id);
    if (!x) continue;
    const body = JSON.parse(x.body);
    const key = cardOf(id, body);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ id, kind: x.kind, ...body });
  }
  const keyOfItem = new Map();
  for (const [key, list] of groups) for (const it of list) keyOfItem.set(it.id, key);
  for (const a of cov) {
    const key = keyOfItem.get(a.id);
    if (!key) continue;
    if (!readersOf.has(key)) readersOf.set(key, new Set());
    readersOf.get(key).add(a.sid);
  }

  const keys = [...groups.keys()].filter((k) => k !== 'questions');
  keys.sort((a, b) => {
    const ra = (readersOf.get(a) || new Set()).size, rb = (readersOf.get(b) || new Set()).size;
    return ra - rb || h(sid + a) - h(sid + b);
  });
  if (groups.has('questions')) keys.push('questions');
  const items = keys.flatMap((k) => groups.get(k));

  const { results } = await env.DB.prepare(
    'SELECT id, m, via FROM answers WHERE token = ?1 AND sid = ?2'
  ).bind(token, sid).all();
  const marks = {};
  for (const x of results) marks[x.id] = { m: JSON.parse(x.m), via: x.via };

  return J({ slot: r.slot, items, marks });
}
