/**
 * local_render.mjs — one-shot CLI renderer via gas-fakes.
 * Usage: node local_render.mjs <base64_payload> [--out file.html]
 */
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';
import vm from 'vm';
import { gasFiles } from './gsfiles.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

const stubPath = path.join(__dirname, 'gas_entry_stub.js');
globalThis.__gasFakesMainScriptPath = stubPath;
process.argv[1] = stubPath;

await import('@mcpher/gas-fakes/main.js');

for (const f of gasFiles) {
  try {
    const code = fs.readFileSync(path.join(__dirname, f), 'utf8');
    vm.runInThisContext(code, { filename: f });
  } catch (e) { console.warn(`[local_render] skipped ${f}: ${e.message}`); }
}

// Patch _errorPage — gas-fakes doesn't implement ScriptApp.getService
vm.runInThisContext(`
  function _errorPage(msg) {
    console.error('[renderer error]', msg);
    return HtmlService.createHtmlOutput(
      '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
      '<h2>Render error</h2><pre>' + String(msg) + '</pre></body>'
    ).setTitle('Render error');
  }
`);

// Parse args
const args = process.argv.slice(2);
let outFile = null;
let payload = null;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--out') { outFile = args[++i]; }
  else { payload = args[i]; }
}

if (!payload) {
  console.error('Usage: node local_render.mjs <base64_payload> [--out file.html]');
  process.exit(1);
}

// Call doGet with the payload parameter
const output = globalThis.doGet({ parameter: { p: payload } });

// .evaluate() if it's a template, then .getContent()
let html;
if (typeof output.evaluate === 'function') {
  html = output.evaluate().getContent();
} else if (typeof output.getContent === 'function') {
  html = output.getContent();
} else {
  html = String(output);
}

const dest = outFile || path.join(__dirname, 'render_output.html');
fs.writeFileSync(dest, html, 'utf8');
console.log(`Rendered ${html.length} bytes → ${dest}`);
process.exit(0);
