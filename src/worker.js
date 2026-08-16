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
// SCOPE IS THE WHOLE POINT. wrangler.toml sets:
//     run_worker_first = ["/"]
// so this code runs for the bare homepage and nothing else. The 474 atom pages,
// their .md twins, /.well-known/*, openapi.json and every other asset keep the
// direct-from-assets path with no Worker in front of them — no added latency,
// no new failure mode on the rest of the site. Requests that reach here for any
// other reason (an unmatched path falling through) are handed straight to
// env.ASSETS, which reproduces the pre-Worker behaviour exactly, 404s included.
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Only ever act on the bare homepage. Anything else is passed through
    // untouched, so this Worker can never change another page's behaviour.
    if (url.pathname !== '/') return env.ASSETS.fetch(request);

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
