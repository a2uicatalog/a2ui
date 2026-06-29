/**
 * gas_entry_stub.js — worker entry point for gas-fakes web server.
 *
 * gas-fakes imports this file in each request worker thread.
 * We load all A2UI .gs renderer files here so doGet is available in globalThis.
 * File list is auto-discovered via gsfiles.mjs — no manual updates needed.
 */
import { readFileSync } from 'fs';
import { runInThisContext } from 'vm';
import { fileURLToPath } from 'url';
import path from 'path';
import { gasFiles } from './gsfiles.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

for (const f of gasFiles) {
  try {
    runInThisContext(readFileSync(path.join(__dirname, f), 'utf8'), { filename: f });
  } catch (e) { console.warn(`[a2ui stub] skipped ${f}: ${e.message}`); }
}

// Patch ScriptApp.getService — not implemented in gas-fakes
if (typeof globalThis.ScriptApp !== 'undefined' && !globalThis.ScriptApp.getService) {
  globalThis.ScriptApp.getService = () => ({ getUrl: () => 'http://localhost:3099/' });
}

runInThisContext(`
  function _errorPage(msg) {
    console.error('[renderer error]', msg);
    return HtmlService.createHtmlOutput(
      '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
      '<h2>Render error</h2><pre>' + String(msg) + '</pre></body>'
    ).setTitle('Render error');
  }
`);

export {};
