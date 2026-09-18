// GET /api/state?t=<token> — the reader's whole task in one response: who they are, the items they
// were dealt (in display order, with their text) and every mark they have saved so far.
// Unknown or disabled token -> 404; no clause text leaves the server without a valid token.

import { J, reader } from '../_lib.js';

export async function onRequestGet({ request, env }) {
  const token = new URL(request.url).searchParams.get('t') || '';
  const r = await reader(env, token);
  if (!r) return J({ error: 'not found' }, 404);

  const { results: rows } = await env.DB.prepare('SELECT id, kind, body FROM items').all();
  const byId = new Map(rows.map((x) => [x.id, x]));
  const items = [];
  for (const id of r.order) {
    const x = byId.get(id);
    if (x) items.push({ id, kind: x.kind, ...JSON.parse(x.body) });
  }

  const { results } = await env.DB.prepare('SELECT id, m, via FROM marks WHERE token = ?1')
    .bind(token).all();
  const marks = {};
  for (const x of results) marks[x.id] = { m: JSON.parse(x.m), via: x.via };

  return J({ name: r.name, slot: r.slot, items, marks });
}
