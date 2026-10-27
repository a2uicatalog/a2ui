// One URL per page (SEO, 2026-10-27): src/worker.js turns plain http and the assets runtime's 307 trailing-slash
// redirect into 301s to the canonical https URL with the slash, and leaves every other response untouched.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const src = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'src', 'worker.js');
const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'worker-')), 'worker.mjs');
fs.copyFileSync(src, tmp);
const worker = (await import(pathToFileURL(tmp).href)).default;

const env = {
  ASSETS: {
    async fetch(req) {
      const u = new URL(req.url);
      if (u.pathname === '/atoms/tooltip') return new Response(null, { status: 307, headers: { Location: '/atoms/tooltip/' } });
      if (u.pathname === '/old') return new Response(null, { status: 307, headers: { Location: '/new/' } });
      if (u.pathname === '/atoms/tooltip/') return new Response('<h1>Tooltip</h1>', { status: 200, headers: { 'Content-Type': 'text/html' } });
      if (u.pathname === '/404.html') return new Response('nf', { status: 200, headers: { 'Content-Type': 'text/html' } });
      return new Response(null, { status: 404 });
    },
  },
};
const get = (u) => worker.fetch(new Request(u, { redirect: 'manual' }), env);

test('slash-less page -> 301 to the slash URL, query kept', async () => {
  const res = await get('https://a2uicatalog.ai/atoms/tooltip?x=1');
  assert.equal(res.status, 301);
  assert.equal(res.headers.get('Location'), 'https://a2uicatalog.ai/atoms/tooltip/?x=1');
});

test('http -> 301 to https, same path and query', async () => {
  const res = await get('http://a2uicatalog.ai/atoms/tooltip/?x=1');
  assert.equal(res.status, 301);
  assert.equal(res.headers.get('Location'), 'https://a2uicatalog.ai/atoms/tooltip/?x=1');
});

test('the canonical page itself is served unchanged', async () => {
  const res = await get('https://a2uicatalog.ai/atoms/tooltip/');
  assert.equal(res.status, 200);
  assert.equal(await res.text(), '<h1>Tooltip</h1>');
});

test('a redirect that is not the trailing-slash one is left as it is', async () => {
  const res = await get('https://a2uicatalog.ai/old');
  assert.equal(res.status, 307);
  assert.equal(res.headers.get('Location'), '/new/');
});

test('a miss is still a 404', async () => {
  assert.equal((await get('https://a2uicatalog.ai/nope')).status, 404);
});
