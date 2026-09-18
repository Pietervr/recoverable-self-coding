// POST /api/bulk  {t, s, marks: [{id, m}], via} — the "the other ... are fine" button: up to 60 answers
// for one visitor session in one D1 batch, each validated exactly as /api/mark validates it. All or nothing.

import { J, ID_RE, SID_RE, RELOAD, UPSERT, reader, checkMark } from '../_lib.js';

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return J({ error: 'bad json' }, 400); }
  const token = String(b.t || '');
  const sid = String(b.s || '');
  const r = await reader(env, token);
  if (!r) return J({ error: 'not found' }, 404);
  if (!SID_RE.test(sid)) return J({ error: RELOAD }, 400);
  const list = Array.isArray(b.marks) ? b.marks : [];
  if (list.length === 0 || list.length > 60) return J({ error: 'bad batch size' }, 400);

  const via = b.via === 'row' ? 'row' : 'card';
  const ts = new Date().toISOString();
  const stmts = [];
  for (const x of list) {
    const id = String(x.id || '');
    if (!ID_RE.test(id) || !r.ids.has(id)) return J({ error: 'unknown item', id }, 400);
    const v = checkMark(id, x.m);
    if (v.error || v.empty) return J({ error: v.error || 'empty mark in batch', id }, 400);
    stmts.push(env.DB.prepare(UPSERT).bind(token, sid, id, JSON.stringify(v.m), via, ts));
  }
  await env.DB.batch(stmts);
  return J({ ok: true, n: stmts.length });
}
