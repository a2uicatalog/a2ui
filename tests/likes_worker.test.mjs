// node --test tests/likes_worker.test.mjs : the atom like counter (src/likes.js), I160.
import test from 'node:test';
import assert from 'node:assert/strict';
import { handleLikes, LIKES_KEY } from '../src/likes.js';

const PUBLISHED = new Set(['treemap', 'kpi_card']);
function env({ withKv = true } = {}) {
  const store = new Map();
  return {
    store,
    LIKES: withKv ? { get: async k => store.get(k) ?? null, put: async (k, v) => { store.set(k, v); } } : undefined,
    ASSETS: { fetch: async req => {
      const m = new URL(req.url).pathname.match(/^\/atoms\/([^/]+)\/$/);
      return new Response('page', { status: m && PUBLISHED.has(m[1]) ? 200 : 404 });
    } },
  };
}
const call = (e, method, path, body, headers = { 'Content-Type': 'application/json' }) => {
  const url = new URL('https://a2uicatalog.ai' + path);
  return handleLikes(new Request(url, { method, headers: body === undefined ? {} : headers, body }), e, url);
};
const post = (e, type, delta) => call(e, 'POST', `/api/likes/${type}`, JSON.stringify({ delta }));

test('like and un-like change the count, and GET shows it', async () => {
  const e = env();
  assert.deepEqual(await (await call(e, 'GET', '/api/likes')).json(), {});
  assert.deepEqual(await (await post(e, 'treemap', 1)).json(), { type: 'treemap', count: 1 });
  assert.deepEqual(await (await post(e, 'treemap', 1)).json(), { type: 'treemap', count: 2 });
  assert.deepEqual(await (await post(e, 'treemap', -1)).json(), { type: 'treemap', count: 1 });
  const res = await call(e, 'GET', '/api/likes');
  assert.equal(res.headers.get('Cache-Control'), 'public, max-age=60');
  assert.deepEqual(await res.json(), { treemap: 1 });
});

test('the count never goes below zero and a zero count is not stored', async () => {
  const e = env();
  assert.deepEqual(await (await post(e, 'treemap', -1)).json(), { type: 'treemap', count: 0 });
  assert.equal(e.store.get(LIKES_KEY) ?? '{}', '{}');
});

test('unknown or malformed atom types are rejected and nothing is stored', async () => {
  const e = env();
  for (const t of ['nope', '..%2Fetc', 'Treemap', 'a'.repeat(80), '']) {
    const res = await post(e, t, 1);
    assert.ok([404, 400, 405].includes(res.status), `${t} -> ${res.status}`);
  }
  assert.equal(e.store.size, 0);
});

test('only +1 and -1 are accepted', async () => {
  const e = env();
  for (const d of [0, 2, -2, '1', null, 1.5, true]) assert.equal((await post(e, 'treemap', d)).status, 400, String(d));
  assert.equal((await call(e, 'POST', '/api/likes/treemap', '{not json')).status, 400);
  assert.equal((await call(e, 'POST', '/api/likes/treemap', '{"delta":1}', { 'Content-Type': 'text/plain' })).status, 415);
  assert.equal((await call(e, 'POST', '/api/likes/treemap', JSON.stringify({ delta: 1, pad: 'x'.repeat(100) }))).status, 413);
  assert.equal(e.store.size, 0);
});

test('storage holds only type -> count, nothing about the visitor', async () => {
  const e = env();
  const headers = { 'Content-Type': 'application/json', 'CF-Connecting-IP': '203.0.113.9', Cookie: 'a=b', 'User-Agent': 'x' };
  await call(e, 'POST', '/api/likes/kpi_card', '{"delta":1}', headers);
  assert.deepEqual([...e.store.keys()], [LIKES_KEY]);
  assert.deepEqual(JSON.parse(e.store.get(LIKES_KEY)), { kpi_card: 1 });
  assert.ok(!e.store.get(LIKES_KEY).includes('203.0.113.9'));
});

test('wrong methods and a missing KV binding fail cleanly', async () => {
  const e = env();
  assert.equal((await call(e, 'DELETE', '/api/likes/treemap')).status, 405);
  assert.equal((await call(e, 'POST', '/api/likes', '{"delta":1}')).status, 405);
  assert.equal((await call(e, 'GET', '/api/likes/treemap')).status, 405);
  assert.equal((await call(env({ withKv: false }), 'GET', '/api/likes')).status, 503);
});
