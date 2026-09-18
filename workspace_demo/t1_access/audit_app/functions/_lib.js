// Shared by the audit API. Files starting with "_" are not routes in Pages Functions.

export const J = (o, status = 200) =>
  new Response(JSON.stringify(o), {
    status,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  });

export const TOKEN_RE = /^[A-Za-z0-9_-]{16,64}$/;
export const SID_RE = /^[A-Za-z0-9_-]{16,40}$/;
export const ID_RE = /^[cp]-[a-z0-9][a-z0-9-]{0,80}$/;

// Sent to a page loaded before the per-visitor sessions existed: its saves must not land in a shared bucket.
export const RELOAD = 'this page was updated: please reload it';

// The part behind a link token, with its item ids as a Set; null if unknown or disabled.
export async function reader(env, token) {
  if (!TOKEN_RE.test(token)) return null;
  const r = await env.DB.prepare(
    'SELECT slot, name, items FROM readers WHERE token = ?1 AND disabled = 0'
  ).bind(token).first();
  if (!r) return null;
  const order = JSON.parse(r.items);
  return { slot: r.slot, name: r.name, order, ids: new Set(order) };
}

const YN = new Set(['y', 'n']);
const YNQ = new Set(['y', 'n', '?']);

// Validate one mark for item `id`. Returns {empty: true} for "unmark", {m} for a valid mark, or {error}.
// A clause needs all three answers (true, names, decisive); a property question needs both (ok, un).
export function checkMark(id, m) {
  if (m === null || m === undefined || (typeof m === 'object' && Object.keys(m).length === 0)) {
    return { empty: true };
  }
  if (typeof m !== 'object') return { error: 'bad mark' };
  const c = String(m.c || '').slice(0, 1000);
  if (id.startsWith('c-')) {
    if (!YNQ.has(m.t) || !YN.has(m.nm) || !YN.has(m.d)) return { error: 'incomplete clause mark' };
    return { m: { t: m.t, nm: m.nm, d: m.d, c } };
  }
  if (!YN.has(m.ok) || !YN.has(m.un)) return { error: 'incomplete question mark' };
  return { m: { ok: m.ok, un: m.un, c } };
}

export const UPSERT = `INSERT INTO answers (token, sid, id, m, via, ts) VALUES (?1, ?2, ?3, ?4, ?5, ?6)
  ON CONFLICT (token, sid, id) DO UPDATE SET m = ?4, via = ?5, ts = ?6`;
