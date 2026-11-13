#!/usr/bin/env node
// Browser half of tests/test_mermaid_llm_render.py: opens each rendered film in one headless Chromium (one page at a time), runs the
// probe (seek to the last frame, measure each node label against its box) and, when asked, saves a screenshot.
// usage: node tests/mermaid_llm_shoot.mjs <jobs.json>   -> prints {name: [{label, over}]}; exit 3 when puppeteer-core is missing
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const spec = JSON.parse(readFileSync(process.argv[2], 'utf8'));
let puppeteer = null;
for (const where of [process.env.A2UI_PUPPETEER, 'puppeteer-core',
  '/mnt/hdd2/work/a2ui-private-dev/pm/dev/presentation-styles/shot/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js']) {
  if (!where) continue;
  try { puppeteer = (await import(where)).default; break; } catch (e) { /* next */ }
}
if (!puppeteer) { console.log('puppeteer-core is not available'); process.exit(3); }

const browser = await puppeteer.launch({ executablePath: spec.chromium, headless: 'new',
  args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const out = {};
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 960, height: 600, deviceScaleFactor: 1 });
  for (const j of spec.jobs) {
    await page.goto(pathToFileURL(j.page).href, { waitUntil: 'load' });
    out[j.name] = await page.evaluate(spec.probe);
    if (j.shot) await (await page.$('.f')).screenshot({ path: j.shot });
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify(out));
