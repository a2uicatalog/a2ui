import '/home/curtis/gas-fakes/main.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import vm from 'vm';

const __dirname = dirname(fileURLToPath(import.meta.url));

const gasFiles = [
  'atom.gs',
  'atoms_ai.gs',
  'atoms_airspace.gs',
  'atoms_animate.gs',
  'atoms_brevet.gs',
  'atoms_canvas.gs',
  'atoms_certs.gs',
  'atoms_charts.gs',
  'atoms_dark.gs',
  'atoms_data.gs',
  'atoms_demo.gs',
  'atoms_effects.gs',
  'atoms_globe.gs',
  'atoms_icons.gs',
  'atoms_lms2.gs',
  'atoms_lms.gs',
  'atoms_nav.gs',
  'atoms_news.gs',
  'atoms_typography.gs',
  'atoms_workspace.gs',
  'Code.js',
];

for (const f of gasFiles) {
  try {
    const code = readFileSync(join(__dirname, f), 'utf8');
    vm.runInThisContext(code, { filename: f });
  } catch(e) { console.warn(`[local_serve] skipped ${f}: ${e.message}`); }
}

// Redefine _errorPage without ScriptApp.getService (not implemented in gas-fakes)
// Also logs the real error so we can see what's actually failing
vm.runInThisContext(`
  function _errorPage(msg) {
    console.error('[renderer error]', msg);
    return HtmlService.createHtmlOutput(
      '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
      '<h2>Render error</h2><pre>' + msg + '</pre>' +
      '</body>'
    ).setTitle('Render error');
  }
`);

const _doGet = globalThis.doGet;
export const doGet = (...args) => _doGet(...args);
