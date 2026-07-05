#!/usr/bin/env node
// Deterministic test of the progress-persistence server logic
// (a2uiLoadProgress/a2uiSaveProgress/_progressKey_) with mocked GAS globals.
// Proves identity isolation, anonymous clientId fallback, per-slug scoping.
// Wired into pytest via tests/test_progress_persistence.py.
import { readFileSync } from 'fs';

// Extract the progress functions + a stub identity from Code.gs
const src = readFileSync(new URL('../apps-script-surface/gas-wired-renderer/Code.gs', import.meta.url), 'utf8');
function grab(name) {
  const i = src.indexOf('function ' + name);
  // brace-match
  let depth = 0, started = false, out = '';
  for (let j = i; j < src.length; j++) {
    const c = src[j]; out += c;
    if (c === '{') { depth++; started = true; }
    else if (c === '}') { depth--; if (started && depth === 0) break; }
  }
  return out;
}

// In-memory mocks
const store = {};
globalThis.PropertiesService = { getScriptProperties: () => ({
  getProperty: k => (k in store ? store[k] : null),
  setProperty: (k, v) => { store[k] = v; },
}) };
let MOCK_EMAIL = 'curtis@krygier.fr';
globalThis._resolveIdentity = () => ({ email: MOCK_EMAIL });

(0, eval)(grab('_progressKey_') + '\n' + grab('a2uiLoadProgress') + '\n' + grab('a2uiSaveProgress'));

let fails = 0;
function ok(cond, msg) { console.log((cond ? '✅' : '❌') + ' ' + msg); if (!cond) fails++; }

// 1. save + load round-trips for a signed-in user
globalThis.a2uiSaveProgress('clasp-deployment', 'ignored-client', 's_1', true);
globalThis.a2uiSaveProgress('clasp-deployment', 'ignored-client', 's_3', true);
let r = globalThis.a2uiLoadProgress('clasp-deployment', 'ignored-client');
ok(r.ok && r.data.s_1 === true && r.data.s_3 === true && r.data.s_2 === undefined, 'signed-in: saved states load back, unset absent');
ok(r.data._u === undefined, 'internal _u timestamp stripped from load');

// 2. identity isolation — different email sees nothing
MOCK_EMAIL = 'someone@else.com';
r = globalThis.a2uiLoadProgress('clasp-deployment', 'ignored-client');
ok(r.ok && Object.keys(r.data).length === 0, 'different identity: isolated, no leakage');

// 3. anonymous falls back to clientId, and two clients are isolated
MOCK_EMAIL = '';
globalThis.a2uiSaveProgress('clasp-deployment', 'clientA', 's_1', true);
r = globalThis.a2uiLoadProgress('clasp-deployment', 'clientA');
ok(r.data.s_1 === true, 'anonymous clientA persists via clientId');
r = globalThis.a2uiLoadProgress('clasp-deployment', 'clientB');
ok(Object.keys(r.data).length === 0, 'anonymous clientB isolated from clientA');

// 4. slug isolation
globalThis.a2uiSaveProgress('other-app', 'clientA', 's_1', true);
MOCK_EMAIL = 'curtis@krygier.fr';
r = globalThis.a2uiLoadProgress('other-app', 'x');
ok(Object.keys(r.data).length === 0, 'per-slug isolation (curtis has nothing on other-app)');

// 5. no-slug guard
r = globalThis.a2uiLoadProgress('', 'x');
ok(r.ok && Object.keys(r.data).length === 0, 'empty slug: safe no-op');

process.exit(fails);
