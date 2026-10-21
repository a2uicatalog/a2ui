// src/worker.js — content negotiation for the HOMEPAGE ONLY.
//
// Everything on a2uicatalog.ai is a static asset served by the Workers assets
// runtime. This Worker exists solely so the homepage can answer questions it
// could not answer as a flat file:
//
//   GET /?mode=agent                  -> structured JSON summary, not marketing HTML
//   GET /  Accept: text/markdown      -> the markdown twin, with a correct Vary header
//   GET /  UA: a known AI crawler     -> the markdown twin, even if it sent Accept: text/html
//
// SCOPE: wrangler.toml sets run_worker_first = true (2026-10-21) so a MISS on
// any path can be answered as a Markdown 404 for Accept: text/markdown clients
// (see withMarkdown404). Every hit other than the homepage negotiation below is
// handed straight to env.ASSETS and comes back exactly as the assets runtime
// served it; HTML 404s keep their 404 status and body.
//
// Both special cases are served BY FETCHING A REAL ASSET rather than by
// generating a body here. agent-view.json is built by scripts/gen_openapi.py
// from spec.json, so its atom count cannot drift the way a string literal in
// this file would. Same reason index.md is read rather than re-written.

const AGENT_VIEW = '/agent-view.json';
const MARKDOWN_TWIN = '/index.md';

// Known AI-crawler User-Agent substrings (case-insensitive). These bots
// commonly send Accept: text/html regardless of what they can actually use,
// so Accept-header negotiation alone never triggers for them — an
// agent-readiness finding, 2026-08-16: "no probed bot User-Agent ... receives
// markdown when requesting HTML." Matched separately from the Accept-header
// path below, which stays exactly as strict as it was for everyone else.
const BOT_USER_AGENTS = [
  'gptbot', 'claudebot', 'chatgpt-user', 'perplexitybot',
  'google-extended', 'applebot-extended', 'ora-agent', 'deepseekbot',
];

function isKnownBot(userAgent) {
  const ua = (userAgent || '').toLowerCase();
  return BOT_USER_AGENTS.some((b) => ua.includes(b));
}

/** Serve a static asset's BODY under a different URL, with our own headers. */
async function serveAsset(env, request, path, headers) {
  const res = await env.ASSETS.fetch(new URL(path, request.url));
  if (!res.ok) return null;                       // asset missing -> caller falls back
  return new Response(res.body, { status: 200, headers });
}

// ── Agent-friendly 404 ──────────────────────────────────────────────────────
// Every non-homepage path reaches this Worker (wrangler.toml run_worker_first)
// only so that a MISS can be answered in Markdown for a client that prefers it.
// Hits are returned exactly as the assets runtime produced them.

/** True when text/markdown outranks text/html in the Accept header (q-values honoured). */
function prefersMarkdown(accept) {
  let md = -1, html = -1;
  for (const part of (accept || '').split(',')) {
    const [type, ...params] = part.trim().toLowerCase().split(';');
    const qp = params.map((x) => x.trim()).find((x) => x.startsWith('q='));
    const q = qp ? parseFloat(qp.slice(2)) : 1;
    if (Number.isNaN(q)) continue;
    if (type === 'text/markdown') md = Math.max(md, q);
    else if (type === 'text/html') html = Math.max(html, q);
  }
  return md > 0 && md > html;
}

const NOT_FOUND_MD = `# 404 - Page not found

The page you requested does not exist on a2uicatalog.ai.

Start from one of these machine-readable entry points:

- [llms.txt](https://a2uicatalog.ai/llms.txt) - site summary and index for agents
- [agents.md](https://a2uicatalog.ai/agents.md) - how agents should use this site and its API
- [Documentation](https://a2uicatalog.ai/docs/) - API and developer docs
- [sitemap.xml](https://a2uicatalog.ai/sitemap.xml) - every published page
`;

// With not_found_handling = "none" the Worker only runs for "/" and for paths no asset matches, so a miss arrives here
// as a bare 404: answer it in Markdown when the client prefers that, else with the site's HTML 404 page (status kept).
async function withMarkdown404(request, env) {
  const res = await env.ASSETS.fetch(request);
  if (res.status !== 404) return res;
  if (!prefersMarkdown(request.headers.get('Accept'))) {
    const page = await env.ASSETS.fetch(new Request(new URL('/404.html', request.url)));
    if (!page.ok) return res;
    return new Response(request.method === 'HEAD' ? null : page.body, {
      status: 404,
      headers: { 'Content-Type': 'text/html; charset=utf-8', 'Vary': 'Accept', 'Cache-Control': 'public, max-age=60' },
    });
  }
  return new Response(request.method === 'HEAD' ? null : NOT_FOUND_MD, {
    status: 404,
    headers: {
      'Content-Type': 'text/markdown; charset=utf-8',
      'Vary': 'Accept',
      'Cache-Control': 'public, max-age=60',
      'X-API-Version': '1',
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Only ever act on the bare homepage. Anything else is passed through
    // untouched, so this Worker can never change another page's behaviour.
    if (url.pathname !== '/') return withMarkdown404(request, env);

    // ── ?mode=agent — structured view instead of the marketing page ──────────
    if (url.searchParams.get('mode') === 'agent') {
      const res = await serveAsset(env, request, AGENT_VIEW, {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'X-API-Version': '1',
        // The response differs by query string, not by header, so Vary is not
        // required here — but caches key on the full URL including ?mode=agent,
        // so this is already correct without it.
        'Cache-Control': 'public, max-age=300',
      });
      if (res) return res;
      // agent-view.json missing (shouldn't happen — it's generated) -> fall
      // through to the normal homepage rather than erroring.
    }

    // ── Accept: text/markdown, OR a known bot UA — serve the markdown twin ───
    // Accept-header negotiation is deliberately conservative: markdown is
    // served ONLY when the client asked for it AND did not ask for HTML.
    // Every browser sends "text/html,application/xhtml+xml,...,*/*", so this
    // can never flip a real browser onto the markdown branch — a naive
    // substring test on */* would. The bot-UA path is separate and looser ON
    // PURPOSE: these crawlers commonly send Accept: text/html regardless of
    // what they can actually use, so they'd never hit the branch above.
    const accept = request.headers.get('Accept') || '';
    const wantsMarkdown = accept.includes('text/markdown') && !accept.includes('text/html');
    const isBot = isKnownBot(request.headers.get('User-Agent'));
    if (wantsMarkdown || isBot) {
      const res = await serveAsset(env, request, MARKDOWN_TWIN, {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'X-API-Version': '1',
        // REQUIRED, not decorative: without it a CDN can serve whichever
        // variant landed in cache first to the other kind of client — the
        // exact cache-poisoning failure acceptmarkdown.com warns about.
        // Varying on User-Agent too, not just Accept, since the bot-UA path
        // above means the SAME Accept header can now get two different
        // bodies depending on who's asking.
        'Vary': 'Accept, User-Agent',
        'Cache-Control': 'public, max-age=300',
      });
      if (res) return res;
    }

    // ── Default: the homepage exactly as before ─────────────────────────────
    // Vary: Accept on the HTML branch too, so the two variants are cached
    // separately rather than one masking the other.
    const res = await env.ASSETS.fetch(request);
    const headers = new Headers(res.headers);
    headers.append('Vary', 'Accept');
    return new Response(res.body, { status: res.status, headers });
  },
};
