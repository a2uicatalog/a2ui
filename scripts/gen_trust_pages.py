#!/usr/bin/env python3
"""gen_trust_pages.py — About / Contact / Privacy, plus /agents.md.

Answers three findings from the 2026-07-31 agent-readiness audit:
  * "Trust anchor pages 0/2 — No trust anchor pages found with sufficient
    content (About, Contact, Privacy)"
  * "Agent discovery file 0/2 — Probed /.well-known/agent-skills, /agents.md,
    /skills.sh"
  * "Markdown URL fallback / markdown agent docs" — /agents.md is served as
    real text/markdown, so a cold-arriving agent has one canonical markdown
    URL describing the site.

Counts come from public/spec.json, never a literal, for the same reason
gen_openapi.py does it: these pages state how big the catalogue is, and a
hand-written number is wrong the moment an atom is added.

Run:  python3 scripts/gen_trust_pages.py     # after gen_public_catalog.py
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")
BASE = "https://a2uicatalog.ai"
LINKEDIN = "https://www.linkedin.com/in/curtiskrygier"
REPO = "https://github.com/a2uicatalog/a2ui"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — A2UI Atomic Catalog</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/{slug}/">
<meta property="og:type" content="website">
<meta property="og:title" content="{title} — A2UI Atomic Catalog">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{base}/{slug}/">
<meta property="og:image" content="{base}/brand/og-card.png">
<script type="application/ld+json">
{jsonld}
</script>
<style>
:root{{color-scheme:light dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f8fb;color:#1f2330;padding:48px 20px;
 font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.wrap{{max-width:720px;margin:0 auto;background:#fff;border-radius:14px;padding:40px 44px;
 box-shadow:0 1px 3px rgba(16,24,40,.06),0 12px 32px rgba(16,24,40,.07)}}
h1{{margin:0 0 6px;font-size:1.9rem;letter-spacing:-.02em}}
h2{{font-size:1.15rem;margin:2rem 0 .5rem}}
.k{{color:#6b7280;font-size:.78rem;letter-spacing:.09em;text-transform:uppercase;
 font-weight:600;margin:0 0 26px}}
a{{color:#00205B}} code{{background:#f1f3f8;padding:2px 6px;border-radius:5px;font-size:.9em}}
nav.top{{max-width:720px;margin:0 auto 14px;font-size:.85rem}}
nav.top a{{text-decoration:none;margin-right:14px}}
footer{{max-width:720px;margin:22px auto 0;font-size:.78rem;color:#6b7280}}
@media(prefers-color-scheme:dark){{
 body{{background:#0e1116;color:#e6e9ef}} .wrap{{background:#161a22;box-shadow:none}}
 a{{color:#8ab4ff}} code{{background:#1e2430}}}}
</style>
</head>
<body>
<nav class="top"><a href="/">← A2UI Atomic Catalog</a><a href="/developers/">Developers</a><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a></nav>
<div class="wrap">
<h1>{title}</h1>
<h2 class="k">A2UI Atomic Catalog</h2>
{body}
</div>
<footer>Independent, unofficial catalog — not affiliated with, endorsed by, or sponsored by Google or Anthropic.
A2UI is Google's protocol; MCP is Anthropic's. Maintained by <a href="{li}">Curtis Krygier</a>. MIT License.</footer>
</body>
</html>
"""


def _n():
    with open(os.path.join(PUBLIC, "spec.json"), encoding="utf-8") as f:
        return json.load(f).get("atomCount", 0)


def pages(n):
    return {
        "developers": dict(
            title="Developers",
            desc=(f"Integrate with the A2UI Atomic Catalog: {n} typed atoms over MCP or REST. "
                  "No API key, no signup. OpenAPI spec, live server descriptor, rate limits."),
            jsonld=json.dumps({
                "@context": "https://schema.org", "@type": "WebPage",
                "url": f"{BASE}/developers/", "name": "Developers — A2UI Atomic Catalog",
                "publisher": {"@id": f"{BASE}/#org"},
            }, indent=2),
            body=f"""
<p>Everything here is free, unauthenticated, and machine-readable — this page is a human
index into the same documents an agent reads.</p>

<h2>1. Connect the MCP server</h2>
<p>The primary integration surface. No API key, no signup.</p>
<pre style="background:#0e1116;color:#c7d1e0;padding:14px 16px;border-radius:8px;overflow-x:auto;"><code>POST https://a2uicatalog.ai/mcp
Content-Type: application/json

{{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}}</code></pre>
<p><code>GET</code> the same URL with <code>Accept: application/json</code> for a live server
descriptor — every tool, transport, and the current rate limits, generated from the running
server so it cannot go stale:</p>
<pre style="background:#0e1116;color:#c7d1e0;padding:14px 16px;border-radius:8px;overflow-x:auto;"><code>curl -H "Accept: application/json" https://a2uicatalog.ai/mcp</code></pre>

<h2>2. Or use the REST surfaces directly</h2>
<table style="width:100%;border-collapse:collapse;margin:1rem 0;font-size:.92rem;">
<tr><td style="padding:6px 10px 6px 0;"><code>GET /spec.json</code></td><td>Full atom vocabulary — {n} atoms, every field contract</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /catalogue/index.json</code></td><td>Compact catalog selection menu</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /catalogue/atoms-json-schema.json</code></td><td>Strict per-atom JSON Schema for constrained decoding</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>POST /api/compose</code></td><td>Natural language → atom blocks</td></tr>
</table>

<h2>3. Reference</h2>
<ul>
<li><a href="/openapi.json">OpenAPI 3.1 specification</a> — every endpoint, request/response schemas, examples</li>
<li><a href="/docs/">API Documentation</a> — REST endpoints, error models, and rate limits</li>
<li><a href="/agents.md">agents.md</a> — agent-facing guide, served as <code>text/markdown</code></li>
<li><a href="/llms.txt">llms.txt</a> — short overview + entry points</li>
<li><a href="/.well-known/agent-auth.md">Auth &amp; rate limits</a> — the real per-tool numbers</li>
<li><a href="/auth.md">Authentication guide</a> — why you probably need no credential, and the optional OAuth path if your platform requires one</li>
<li><a href="/versioning.md">Versioning &amp; deprecation policy</a> — what changes without notice, and the CI gate that fails a deploy if a response shape changes undeclared</li>
<li><a href="/.well-known/mcp.json">MCP discovery manifest</a></li>
</ul>

<h2>4. Own your renderer</h2>
<p>The shared demo renderer is rate limited by design. Deploy your own Apps Script renderer in
four commands — no cost beyond a Google account — and every subsequent call targets it instead:</p>
<pre style="background:#0e1116;color:#c7d1e0;padding:14px 16px;border-radius:8px;overflow-x:auto;"><code>git clone {REPO}
cd a2ui/apps-script-surface/gas-schema-renderer
clasp login && clasp create --type webapp && clasp push && clasp deploy</code></pre>

<h2>5. Auth</h2>
<p>None required for normal use. See <a href="/.well-known/agent-auth.md">auth &amp; rate
limits</a> for the optional OAuth/Basic-Auth paths used by platforms that require attributed
access (e.g. Gemini Enterprise's BYO-MCP model).</p>

<h2>Source</h2>
<p>MIT licensed. Full source, issues and pull requests: <a href="{REPO}">{REPO.replace('https://','')}</a>.</p>"""),
        "docs": dict(
            title="API Documentation",
            desc=(f"A2UI Atomic Catalog API documentation: endpoints, OpenAPI 3.1 specification, "
                  f"JSON schemas, MCP servers, and REST routes for AI agents."),
            jsonld=json.dumps({
                "@context": "https://schema.org", "@type": "APIReference",
                "url": f"{BASE}/docs/", "name": "API Documentation — A2UI Atomic Catalog",
                "publisher": {"@id": f"{BASE}/#org"},
            }, indent=2),
            body=f"""
<p>Developer and API documentation for the A2UI Atomic Catalog. All developer resources are free,
unauthenticated, and machine-readable.</p>

<h2>REST Endpoints</h2>
<table style="width:100%;border-collapse:collapse;margin:1rem 0;font-size:.92rem;">
<tr><td style="padding:6px 10px 6px 0;"><code>POST /api/render</code></td><td>Render atom payload to standalone HTML page (50 req/day)</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>POST /api/compose</code></td><td>Natural language prompt → typed atom blocks (20 req/day)</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /ask?q=...</code></td><td>Natural-language search over the atom catalog (60 req/day)</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /api/data/{{source}}</code></td><td>Declared data source proxy (data-sources.yaml)</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /spec.json</code></td><td>Full atom vocabulary ({n} atoms) with all field contracts</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /catalogue/atoms-json-schema.json</code></td><td>Strict JSON Schema for constrained agent decoding</td></tr>
<tr><td style="padding:6px 10px 6px 0;"><code>GET /catalogue/index.json</code></td><td>Compact catalog selection menu</td></tr>
</table>

<h2>MCP Servers</h2>
<ul>
<li><strong>Product MCP Server</strong>: <code>https://a2uicatalog.ai/mcp</code> — tools for composing, rendering, and publishing UI atoms.</li>
<li><strong>Documentation MCP Server</strong>: <code>https://a2uicatalog.ai/mcp-docs</code> — tools (<code>search_docs</code>, <code>list_docs</code>) for querying documentation.</li>
</ul>

<h2>Specifications &amp; Developer Resources</h2>
<ul>
<li><a href="/openapi.json">OpenAPI 3.1 Specification</a> — complete machine-readable OpenAPI spec</li>
<li><a href="/developers/">Developers Guide</a> — integration walkthrough and deployment guide</li>
<li><a href="/llms.txt">llms.txt</a> and <a href="/docs/llms.txt">docs/llms.txt</a> — LLM-friendly context documents</li>
<li><a href="/agents.md">agents.md</a> — agent guide with tool contracts and invocation examples</li>
<li><a href="/auth.md">Authentication Guide</a> — auth requirements and OAuth metadata</li>
<li><a href="/.well-known/agent-auth.md">Auth &amp; Rate Limits</a> — real rate limits per tool and endpoint</li>
<li><a href="/pricing.md">Pricing &amp; Limits</a> — free tier terms and self-hosting runbooks</li>
<li><a href="/versioning.md">Versioning Policy</a> — API versioning (X-API-Version) and deprecation rules</li>
<li><a href="/.well-known/api-catalog">RFC 9727 API Catalog</a> — linkset of all API surfaces</li>
<li><a href="/.well-known/ai-catalog.json">ARD Discovery Catalog</a> — AI Resource Discovery index</li>
</ul>"""),
        "api-docs": dict(
            title="API Docs & Reference",
            desc=(f"A2UI Atomic Catalog API docs and reference: OpenAPI 3.1 spec, endpoints, "
                  f"MCP servers, and integration guides."),
            jsonld=json.dumps({
                "@context": "https://schema.org", "@type": "APIReference",
                "url": f"{BASE}/api-docs/", "name": "API Docs & Reference — A2UI Atomic Catalog",
                "publisher": {"@id": f"{BASE}/#org"},
            }, indent=2),
            body=f"""
<p>Predictable entry point for developer resources and API reference documents.</p>
<p>Primary integration surface: <a href="/mcp">the MCP server at /mcp</a> — no API key, no
signup, <code>POST</code> JSON-RPC 2.0 directly.</p>
<ul>
<li><a href="/docs/">API Documentation</a> — complete endpoint and protocol reference</li>
<li><a href="/openapi.json">OpenAPI 3.1 Specification</a> — raw JSON OpenAPI contract</li>
<li><a href="/developers/">Developers Guide</a> — human integration guide</li>
<li><a href="/llms.txt">llms.txt</a> — LLM overview and quick links</li>
<li><a href="/spec.json">spec.json</a> — {n} atom definitions and field contracts</li>
<li><a href="/auth.md">Authentication Guide</a> and <a href="/.well-known/agent-auth.md">Rate Limits</a></li>
</ul>"""),
        "about": dict(
            title="About",
            desc=("What the A2UI Atomic Catalog is, who maintains it, and why a typed UI "
                  "vocabulary beats asking a model to write HTML."),
            jsonld=json.dumps({
                "@context": "https://schema.org", "@type": "AboutPage",
                "url": f"{BASE}/about/", "name": "About the A2UI Atomic Catalog",
                "publisher": {"@id": f"{BASE}/#org"},
            }, indent=2),
            body=f"""
<p>The A2UI Atomic Catalog is an open-source, typed UI vocabulary — <strong>{n} atoms</strong> —
that AI agents use to produce real rendered interfaces instead of generating HTML. An agent
names a component (<code>stat_card</code>, <code>gauge_sla</code>, <code>stepper</code>) and
passes data; a renderer that already knows that component draws it.</p>

<h2>Why a vocabulary instead of generated markup</h2>
<p>A model writing HTML has to be correct every time, and its failure mode is markup that is
subtly wrong in ways nobody notices. A model naming a component from a fixed set can only fail
by naming something that does not exist — which fails immediately, at the schema boundary.
Constraining the output makes the system more reliable, not less capable.</p>

<h2>One payload, many surfaces</h2>
<p>The same payload renders on the web, Google Meet stages, Apps Script web apps, Google Chat
cards, and MCP Apps hosts such as claude.ai. Per-surface support is declared per atom, so an
atom that cannot work somewhere says so rather than degrading silently.</p>

<h2>Independence</h2>
<p>This is an independent, unofficial project. It is not affiliated with, endorsed by, or
sponsored by Google or Anthropic. A2UI is Google's protocol (official spec at
<a href="https://a2ui.org">a2ui.org</a>); MCP is Anthropic's. The catalogue is MIT licensed and
the full source is on <a href="{REPO}">GitHub</a>.</p>

<h2>Who maintains it</h2>
<p>Built and maintained by <a href="{LINKEDIN}">Curtis Krygier</a>. Design notes and build
write-ups are published on the <a href="/blog/">blog</a>.</p>

<h2>Start here</h2>
<ul>
<li><a href="/">Browse the catalogue</a> — search and preview every atom live</li>
<li><a href="/openapi.json">OpenAPI specification</a> — the full API surface</li>
<li><a href="/llms.txt">llms.txt</a> — the agent-facing overview</li>
<li><a href="/surfaces/mcp-apps">MCP Apps playground</a> — render atoms in a sandboxed MCP host</li>
</ul>"""),
        "contact": dict(
            title="Contact",
            desc="How to reach the maintainer of the A2UI Atomic Catalog, report an issue, or contribute.",
            jsonld=json.dumps({
                "@context": "https://schema.org", "@type": "ContactPage",
                "url": f"{BASE}/contact/", "name": "Contact",
                "publisher": {"@id": f"{BASE}/#org"},
            }, indent=2),
            body=f"""
<h2>Issues and contributions</h2>
<p>The fastest route for anything technical is the repository:
<a href="{REPO}/issues">{REPO.replace('https://','')}/issues</a>.
Bug reports, atom proposals and pull requests are all welcome there.</p>

<h2>Maintainer</h2>
<p>The catalogue is built and maintained by <a href="{LINKEDIN}">Curtis Krygier</a>.
LinkedIn is the most reliable way to get a direct reply.</p>

<h2>Integration questions</h2>
<p>If you are wiring an agent to the MCP server, the answers are usually already written down:
the <a href="/openapi.json">OpenAPI spec</a> describes every endpoint, and
<code>GET /mcp</code> with <code>Accept: application/json</code> returns a live server
descriptor listing every tool and its current rate limits. No API key or signup is required.</p>

<h2>Security</h2>
<p>If you believe you have found a security issue, please report it privately through the
GitHub repository's security advisory form rather than a public issue.</p>"""),
        "privacy": dict(
            title="Privacy",
            desc="What the A2UI Atomic Catalog stores, what it does not, and what the MCP server logs.",
            jsonld=json.dumps({
                "@context": "https://schema.org", "@type": "WebPage",
                "url": f"{BASE}/privacy/", "name": "Privacy",
                "publisher": {"@id": f"{BASE}/#org"},
            }, indent=2),
            body="""
<h2>The short version</h2>
<p>There are no accounts, no sign-up, no advertising and no third-party analytics or tracking
scripts on this site. Browsing the catalogue requires giving nothing.</p>

<h2>The MCP server</h2>
<p>The MCP endpoint at <code>a2uicatalog.ai/mcp</code> is unauthenticated and stores nothing
about who calls it. Rate limits are enforced against a <strong>SHA-256 hash of the client IP</strong>
with a counter — never the IP itself, and never any payload content. Those counters expire
automatically (7 days for preview limits, 24 hours for render limits).</p>

<h2>Rendering</h2>
<p>Surface content passed to <code>preview_url</code> or <code>render_surface</code> is rendered
and returned; it is not retained for analytics. Payloads sent to <code>publish_url</code> are
stored deliberately, because that tool exists to mint a shareable link — those entries carry a
TTL and can be removed at any time with <code>unpublish_url</code>.</p>

<h2>Logs</h2>
<p>The edge keeps standard operational request logs (path, status, timing) as any web host does.
Application logs record the tool name and duration of a call, not its content.</p>

<h2>Third parties</h2>
<p>The site is served by Cloudflare, whose own processing is covered by their privacy terms.
Atoms that fetch live data do so only through declared sources listed in the catalogue's
data-source registry — network access is not open-ended.</p>

<h2>Contact</h2>
<p>Questions about any of this: see the <a href="/contact/">contact page</a>.</p>"""),
    }


AGENTS_MD = """---
title: A2UI Atomic Catalog — agent guide
description: {n} typed UI atoms an AI agent composes into real rendered interfaces instead of generating HTML.
canonical: https://a2uicatalog.ai/agents.md
---

# A2UI Atomic Catalog — agent guide

> {n} typed UI atoms an AI agent composes into real rendered interfaces — web, Google Meet,
> Apps Script, Google Chat and MCP Apps — instead of generating HTML.

## Connect

MCP server (no auth, no signup):

    https://a2uicatalog.ai/mcp

`GET` it with `Accept: application/json` for a machine-readable descriptor listing every tool,
its rate limits and documentation links. `POST` speaks JSON-RPC 2.0 (MCP Streamable HTTP).

Documentation MCP server (no auth, separate identity — `a2uicatalog-docs`):

    https://a2uicatalog.ai/mcp-docs

`search_docs(query)` answers questions FROM this product's own docs (auth, versioning,
pricing, API surface, runbook catalog). Use the server above to take actions; use this one
to answer doc questions.

CLI / local MCP server (npm, no account needed):

    npx -p @a2uicatalog/mcp a2ui render page.json

Renders a payload to HTML with no MCP client at all. The same package also runs as a local
MCP server (`a2uicatalog-mcp` bin) for Claude Desktop/Cursor, and deploys a `training.md` to
your own Google Apps Script web app via `build_app`. https://www.npmjs.com/package/@a2uicatalog/mcp

## When to use this

Use it when you need to SHOW something rather than describe it: a chart, a status board, a
step-by-step procedure, a comparison table, a dashboard, a decision tree.

Do NOT use it for plain prose answers, for fetching data (it renders data; it only reaches
declared sources), or on hosts that cannot display HTML.

## How to use it correctly

1. `list_catalogs` — pick the catalog slice for the need. Do not load the whole vocabulary.
2. `get_catalog` — read the real field contracts. Never guess a field name.
3. Render:
   - `render_surface` on MCP Apps-capable hosts (renders inline in the conversation)
   - `preview_url` elsewhere (returns a shareable link)
   - `make_surface_url` to render against the caller's OWN deployed renderer, unlimited

## Machine-readable entry points

| Document | URL |
|---|---|
| Developer guide & API docs | https://a2uicatalog.ai/developers/ |
| CLI / local MCP server (npm) | https://www.npmjs.com/package/@a2uicatalog/mcp |
| OpenAPI specification | https://a2uicatalog.ai/openapi.json |
| Full atom vocabulary | https://a2uicatalog.ai/spec.json |
| Strict per-atom JSON Schema | https://a2uicatalog.ai/catalogue/atoms-json-schema.json |
| Catalog selection menu | https://a2uicatalog.ai/catalogue/index.json |
| ARD discovery document | https://a2uicatalog.ai/.well-known/ai-catalog.json |
| Auth & rate limits | https://a2uicatalog.ai/.well-known/agent-auth.md |
| Authentication guide | https://a2uicatalog.ai/auth.md |
| Pricing & limits | https://a2uicatalog.ai/pricing.md |
| Versioning policy | https://a2uicatalog.ai/versioning.md |
| Agent overview | https://a2uicatalog.ai/llms.txt |

## Terms

Free and MIT licensed. No API key or signup. Rate limits are per-tool and published in the
descriptor. Independent, unofficial project — not affiliated with, endorsed by or sponsored by
Google or Anthropic. A2UI is Google's protocol; MCP is Anthropic's.

Source: https://github.com/a2uicatalog/a2ui
Maintained by Curtis Krygier — https://www.linkedin.com/in/curtiskrygier
"""


DEVELOPERS_LLMS_TXT = """# A2UI Atomic Catalog — Developers

> Scoped context for integration questions only. For the full site overview, see
> https://a2uicatalog.ai/llms.txt instead.

## Connect

- MCP server: https://a2uicatalog.ai/mcp — no API key, no signup. `POST` speaks JSON-RPC 2.0
  (Streamable HTTP). `GET` with `Accept: application/json` returns a live server descriptor
  (every tool, current rate limits).
- Documentation MCP server: https://a2uicatalog.ai/mcp-docs — a separate identity
  (`a2uicatalog-docs`) exposing `search_docs(query)`/`list_docs()` over this product's own
  docs, distinct from the product server above.
- REST: `GET /spec.json` (full atom vocabulary), `GET /catalogue/atoms-json-schema.json`
  (strict per-atom JSON Schema for constrained decoding), `POST /api/compose` (natural
  language to atom blocks).
- CLI (npm, no account): `npx -p @a2uicatalog/mcp a2ui render page.json` — same package also
  runs as a local MCP server for Claude Desktop/Cursor. https://www.npmjs.com/package/@a2uicatalog/mcp

## Reference

- OpenAPI 3.1 specification: https://a2uicatalog.ai/openapi.json
- Auth & rate limits (the real per-tool numbers): https://a2uicatalog.ai/.well-known/agent-auth.md
- Self-host your own renderer (4 commands, no cost beyond a Google account):
  https://a2uicatalog.ai/developers/

## Terms

Free, MIT licensed, no signup. Source: https://github.com/a2uicatalog/a2ui
"""


SURFACES_LLMS_TXT = """# A2UI Atomic Catalog — Surfaces

> Scoped context: which rendering surfaces exist and how they differ. For the full
> site overview see https://a2uicatalog.ai/llms.txt; for integration mechanics see
> https://a2uicatalog.ai/developers/llms.txt.

## The surfaces

One payload, several renderers. Per-surface support is declared PER ATOM in
`spec.json` (`surfaces.works_on`) — an atom that cannot render somewhere says so
rather than degrading silently. Always check that field before composing for a
specific surface.

- `web` — the reference renderer; the widest support.
- `mcp-apps` — renders inline inside MCP Apps hosts (e.g. claude.ai) via `render_surface`.
- `google-meet-stage` — Meet add-on stage.
- `google-apps-script-web` — self-hosted Apps Script web app; deploy your own for
  unmetered rendering.
- `google-apps-script-side-panel` — Apps Script side panel.
- `google-chat` — Chat cards; visuals arrive as server-rendered images (Chat's own
  widget set cannot express custom charts or layout).
- `email` / `pdf` — static print channels; no scripting, no interactivity.

## Choosing one

Ask what the host can actually display. MCP Apps hosts render inline. Everything
else takes a link (`preview_url`, or `make_surface_url` against your own renderer).
Static channels (`email`, `pdf`) need the image/print path, not interactive atoms.

## Reference

- Per-atom surface support: https://a2uicatalog.ai/spec.json
- Live playground: https://a2uicatalog.ai/surfaces/mcp-apps
"""


def main():
    n = _n()
    for slug, p in pages(n).items():
        d = os.path.join(PUBLIC, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(PAGE.format(slug=slug, base=BASE, li=LINKEDIN, **p))
        print(f"wrote public/{slug}/index.html")

    with open(os.path.join(PUBLIC, "agents.md"), "w", encoding="utf-8") as f:
        f.write(AGENTS_MD.format(n=n))
    print("wrote public/agents.md")

    # A markdown twin of the homepage — a cold-arriving agent that only knows
    # to try the .md suffix gets a real, canonical summary instead of a 404.
    # Deliberately NOT the same content as agents.md: this is a description
    # of the SITE (what it is, top links); agents.md is a HOW-TO for the MCP
    # server. Different questions, kept separate rather than aliased.
    index_md = f"""---
title: A2UI Atomic Catalog
description: {n} typed UI atoms an AI agent composes into real rendered interfaces instead of generating HTML.
canonical: {BASE}/
---

# A2UI Atomic Catalog

{n} typed UI atoms an AI agent composes into real rendered interfaces — web, Google Meet,
Apps Script, Google Chat and MCP Apps — instead of generating HTML.

## Start here

- [Browse the catalog]({BASE}/) — search and preview every atom live
- [Developers]({BASE}/developers/) — MCP + REST integration guide
- [OpenAPI specification]({BASE}/openapi.json)
- [agents.md]({BASE}/agents.md) — agent-facing how-to
- [MCP Apps playground]({BASE}/surfaces/mcp-apps)

## What this is

An independent, unofficial, open-source project (MIT licensed). Not affiliated with, endorsed
by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is Anthropic's.

Source: {REPO}
Maintained by Curtis Krygier — {LINKEDIN}
"""
    with open(os.path.join(PUBLIC, "index.md"), "w", encoding="utf-8") as f:
        f.write(index_md)
    print("wrote public/index.md")

    # Modular llms.txt (2026-07-31): a section-scoped context file so an
    # agent working an integration question fetches ~700 bytes instead of
    # the whole-site llms.txt. Real subset of agents.md/developers content,
    # not a duplicate — see DEVELOPERS_LLMS_TXT's header note pointing back
    # to the full-site doc.
    dev_dir = os.path.join(PUBLIC, "developers")
    os.makedirs(dev_dir, exist_ok=True)
    with open(os.path.join(dev_dir, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(DEVELOPERS_LLMS_TXT)
    print("wrote public/developers/llms.txt")

    # Second scoped section: "which surface do I target?" is a genuinely
    # different question from "how do I integrate?", and the answer is long
    # enough that folding it into the developers file would bury both.
    surf_dir = os.path.join(PUBLIC, "surfaces")
    os.makedirs(surf_dir, exist_ok=True)
    with open(os.path.join(surf_dir, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(SURFACES_LLMS_TXT)
    print("wrote public/surfaces/llms.txt")


if __name__ == "__main__":
    main()
