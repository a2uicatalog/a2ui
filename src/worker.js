// src/worker.js — content negotiation for the HOMEPAGE ONLY.
//
// Everything on a2uicatalog.ai is a static asset served by the Workers assets
// runtime. This Worker exists solely so the homepage can answer two questions
// it could not answer as a flat file:
//
//   GET /?mode=agent                  -> structured JSON summary, not marketing HTML
//   GET /  Accept: text/markdown      -> the markdown twin, with a correct Vary header
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

    // ── Accept: text/markdown — serve the markdown twin ──────────────────────
    // Deliberately conservative: markdown is served ONLY when the client asked
    // for it AND did not ask for HTML. Every browser sends
    // "text/html,application/xhtml+xml,...,*/*", so this can never flip a real
    // browser onto the markdown branch — a naive substring test on */* would.
    const accept = request.headers.get('Accept') || '';
    const wantsMarkdown = accept.includes('text/markdown') && !accept.includes('text/html');
    if (wantsMarkdown) {
      const res = await serveAsset(env, request, MARKDOWN_TWIN, {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'X-API-Version': '1',
        // REQUIRED, not decorative: without it a CDN can serve whichever
        // variant landed in cache first to the other kind of client — the
        // exact cache-poisoning failure acceptmarkdown.com warns about.
        'Vary': 'Accept',
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
