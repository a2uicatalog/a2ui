// Renders the four landing-film poster stills (frame at 2.5 s) to public/brand/film-poster-<aspect>-<theme>.webp.
// Usage: node scripts/film_posters.mjs <url of a built index.html> ; needs puppeteer-core (PUPPETEER_CORE env = path to its ESM entry) and chromium.
const puppeteer = await import(process.env.PUPPETEER_CORE || 'puppeteer-core');
const url = process.argv[2], T = 2.5;
const b = await (puppeteer.default || puppeteer).launch({ executablePath: process.env.CHROMIUM || '/usr/bin/chromium', headless: 'new', args: ['--no-sandbox', '--disable-gpu'] });
for (const aspect of ['wide', 'tall']) for (const theme of ['light', 'dark']) {
  const p = await b.newPage(); await p.setViewport(aspect === 'wide' ? { width: 1280, height: 780 } : { width: 390, height: 844, deviceScaleFactor: 2 });
  await p.goto(url, { waitUntil: 'load' });
  await p.evaluate(th => document.documentElement.setAttribute('data-theme', th), theme);
  await new Promise(r => setTimeout(r, 1500));
  const box = await p.evaluate(t => {
    document.querySelectorAll('.film-ui,.film-cue').forEach(e => e.style.display = 'none');
    const m = [...document.querySelectorAll('.film-hero .mf')].find(x => x.offsetParent), r = m.querySelector('.mt-root'), f = window.__a2uiMotion[r.id.slice(3)];
    f.pause(); f.seek(t); const bb = m.getBoundingClientRect(); return [bb.x, bb.y, bb.width, bb.height];
  }, T);
  await new Promise(r => setTimeout(r, 600));
  await p.screenshot({ path: `public/brand/film-poster-${aspect}-${theme}.webp`, type: 'webp', quality: 78, clip: { x: box[0], y: Math.max(0, box[1]), width: box[2], height: box[3] } });
  await p.close();
}
await b.close();
