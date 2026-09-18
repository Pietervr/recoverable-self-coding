// POST /api/mark  {t, s, id, m, via} — save one answer for this visitor session; last write wins per
// (link, session, item). An empty mark ({} or null) deletes the row, so un-clicking really un-marks.
// A request without a session comes from a page loaded before sessions existed: it is refused with a
// "please reload" message, so its answers never land in a bucket shared by everyone on the link.

import { J, ID_RE, SID_RE, RELOAD, UPSERT, reader, checkMark } from '../_lib.js';

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return J({ error: 'bad json' }, 400); }
  const token = String(b.t || '');
  const sid = String(b.s || '');
  const id = String(b.id || '');
  const r = await reader(env, token);
  if (!r) return J({ error: 'not found' }, 404);
  if (!SID_RE.test(sid)) return J({ error: RELOAD }, 400);
  if (!ID_RE.test(id) || !r.ids.has(id)) return J({ error: 'unknown item' }, 400);

  const v = checkMark(id, b.m);
  if (v.error) return J({ error: v.error }, 400);
  if (v.empty) {
    await env.DB.prepare('DELETE FROM answers WHERE token = ?1 AND sid = ?2 AND id = ?3')
      .bind(token, sid, id).run();
    return J({ ok: true, cleared: true });
  }
  const via = b.via === 'card' ? 'card' : 'row';
  await env.DB.prepare(UPSERT)
    .bind(token, sid, id, JSON.stringify(v.m), via, new Date().toISOString()).run();
  return J({ ok: true });
}
