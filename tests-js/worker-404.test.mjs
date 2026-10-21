// Agent-friendly 404: src/worker.js must answer an unmatched path with a
// Markdown 404 (still status 404) when the client prefers text/markdown, and
// leave every other response exactly as the assets runtime produced it.
// src/worker.js has no package.json "type":"module" beside it, so load a
// temp .mjs copy (works on Node 20 and 22).
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

const HTML_404 = '<!DOCTYPE html><title>Page not found</title>';
const env = {
  ASSETS: {
    async fetch(req) {
      const p = new URL(req.url).pathname;
      if (p === '/') return new Response('<h1>home</h1>', { status: 200, headers: { 'Content-Type': 'text/html' } });
      if (p === '/llms.txt') return new Response('llms', { status: 200, headers: { 'Content-Type': 'text/plain' } });
      return new Response(HTML_404, { status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
    },
  },
};
const get = (p, accept) => worker.fetch(new Request('https://a2uicatalog.ai' + p, accept ? { headers: { Accept: accept } } : {}), env);

test('markdown Accept on a missing path -> 404 + text/markdown body with recovery links', async () => {
  const res = await get('/some-path-that-does-not-exist', 'text/markdown');
  assert.equal(res.status, 404);
  assert.equal(res.headers.get('Content-Type'), 'text/markdown; charset=utf-8');
  assert.match(res.headers.get('Vary') || '', /Accept/i);
  const body = await res.text();
  assert.ok(body.length >= 20);
  assert.match(body, /not found/i);
  for (const l of ['https://a2uicatalog.ai/llms.txt', 'https://a2uicatalog.ai/agents.md',
                   'https://a2uicatalog.ai/docs/', 'https://a2uicatalog.ai/sitemap.xml']) {
    assert.ok(body.includes(l), 'missing ' + l);
  }
});

test('q-values: markdown preferred over html when ranked higher', async () => {
  const res = await get('/nope', 'text/html;q=0.5, text/markdown');
  assert.equal(res.status, 404);
  assert.match(res.headers.get('Content-Type'), /^text\/markdown/);
});

test('browser Accept on a missing path -> HTML 404 unchanged', async () => {
  const res = await get('/nope', 'text/html,application/xhtml+xml,*/*;q=0.8');
  assert.equal(res.status, 404);
  assert.match(res.headers.get('Content-Type'), /^text\/html/);
  assert.equal(await res.text(), HTML_404);
});

test('no Accept header -> HTML 404', async () => {
  const res = await get('/nope');
  assert.equal(res.status, 404);
  assert.match(res.headers.get('Content-Type'), /^text\/html/);
});

test('existing asset with markdown Accept is passed through untouched', async () => {
  const res = await get('/llms.txt', 'text/markdown');
  assert.equal(res.status, 200);
  assert.equal(res.headers.get('Content-Type'), 'text/plain');
});
