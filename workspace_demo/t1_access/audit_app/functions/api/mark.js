// POST /api/mark  {t, id, m, via} — save one mark; last write wins per (reader, item).
// An empty mark ({} or null) deletes the row, so un-clicking really un-marks.

import { J, ID_RE, reader, checkMark } from '../_lib.js';

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return J({ error: 'bad json' }, 400); }
  const token = String(b.t || '');
  const id = String(b.id || '');
  const r = await reader(env, token);
  if (!r) return J({ error: 'not found' }, 404);
  if (!ID_RE.test(id) || !r.ids.has(id)) return J({ error: 'unknown item' }, 400);

  const v = checkMark(id, b.m);
  if (v.error) return J({ error: v.error }, 400);
  if (v.empty) {
    await env.DB.prepare('DELETE FROM marks WHERE token = ?1 AND id = ?2').bind(token, id).run();
    return J({ ok: true, cleared: true });
  }
  const via = b.via === 'card' ? 'card' : 'row';
  await env.DB.prepare(
    `INSERT INTO marks (token, id, m, via, ts) VALUES (?1, ?2, ?3, ?4, ?5)
     ON CONFLICT (token, id) DO UPDATE SET m = ?3, via = ?4, ts = ?5`
  ).bind(token, id, JSON.stringify(v.m), via, new Date().toISOString()).run();
  return J({ ok: true });
}
