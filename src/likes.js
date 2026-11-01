// src/likes.js — the atom like counter (I160).
//
//   GET  /api/likes          -> {"<type>": n, ...}, cacheable for a minute
//   POST /api/likes/<type>   body {"delta": 1 | -1} -> {"type": "<type>", "count": n}
//
// Storage is ONE KV key (LIKES_KEY) holding {type: count}. Nothing else is stored or logged with a like: no IP address,
// no account, no cookie, no timestamp. KV is eventually consistent and read-modify-write, so two likes landing in the
// same instant can lose one; counts are a signal for ranking, not a ledger. An edge rate limit (Cloudflare dashboard,
// per client) is configured outside this file; this code stores nothing per client.
//
// Only a published atom type is accepted: a type is published when its page /atoms/<type>/ exists as an asset, the
// same set the /atoms/ hub lists.

export const LIKES_KEY = 'likes';
const TYPE_RE = /^[a-z][a-z0-9_]{0,63}$/;
const MAX_BODY = 64;

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'X-API-Version': '1', ...extra },
  });
}

async function readCounts(kv) {
  try {
    const raw = await kv.get(LIKES_KEY);
    const v = raw ? JSON.parse(raw) : {};
    return v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  } catch {
    return {};
  }
}

async function isPublished(env, url, type) {
  if (!TYPE_RE.test(type)) return false;
  const res = await env.ASSETS.fetch(new Request(new URL(`/atoms/${type}/`, url).href, { method: 'GET' }));
  const ok = res.status === 200;
  if (res.body) await res.body.cancel();
  return ok;
}

export async function handleLikes(request, env, url) {
  const kv = env.LIKES;
  if (!kv) return json({ error: 'likes are not configured' }, 503, { 'Cache-Control': 'no-store' });
  const path = url.pathname.replace(/\/+$/, '');

  if (path === '/api/likes') {
    if (request.method !== 'GET' && request.method !== 'HEAD') return json({ error: 'method not allowed' }, 405, { Allow: 'GET, HEAD' });
    return json(await readCounts(kv), 200, { 'Cache-Control': 'public, max-age=60' });
  }

  const type = decodeURIComponent(path.slice('/api/likes/'.length));
  if (request.method !== 'POST') return json({ error: 'method not allowed' }, 405, { Allow: 'POST' });
  if (!(request.headers.get('Content-Type') || '').toLowerCase().startsWith('application/json')) {
    return json({ error: 'Content-Type must be application/json' }, 415, { 'Cache-Control': 'no-store' });
  }
  const text = await request.text();
  if (text.length > MAX_BODY) return json({ error: 'body too large' }, 413, { 'Cache-Control': 'no-store' });
  let body;
  try { body = JSON.parse(text); } catch { return json({ error: 'body must be JSON' }, 400, { 'Cache-Control': 'no-store' }); }
  const delta = body && typeof body === 'object' ? body.delta : undefined;
  if (delta !== 1 && delta !== -1) return json({ error: 'delta must be 1 or -1' }, 400, { 'Cache-Control': 'no-store' });
  if (!(await isPublished(env, url, type))) return json({ error: 'unknown atom type' }, 404, { 'Cache-Control': 'no-store' });

  const counts = await readCounts(kv);
  const next = Math.max(0, (Number.isInteger(counts[type]) ? counts[type] : 0) + delta);
  if (next === 0) delete counts[type]; else counts[type] = next;
  await kv.put(LIKES_KEY, JSON.stringify(counts));
  return json({ type, count: next }, 200, { 'Cache-Control': 'no-store' });
}
