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
<nav class="top"><a href="/">← A2UI Atomic Catalog</a><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a></nav>
<div class="wrap">
<h1>{title}</h1>
<p class="k">A2UI Atomic Catalog</p>
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


AGENTS_MD = """# A2UI Atomic Catalog — agent guide

> {n} typed UI atoms an AI agent composes into real rendered interfaces — web, Google Meet,
> Apps Script, Google Chat and MCP Apps — instead of generating HTML.

## Connect

MCP server (no auth, no signup):

    https://a2uicatalog.ai/mcp

`GET` it with `Accept: application/json` for a machine-readable descriptor listing every tool,
its rate limits and documentation links. `POST` speaks JSON-RPC 2.0 (MCP Streamable HTTP).

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
| OpenAPI specification | https://a2uicatalog.ai/openapi.json |
| Full atom vocabulary | https://a2uicatalog.ai/spec.json |
| Strict per-atom JSON Schema | https://a2uicatalog.ai/catalogue/atoms-json-schema.json |
| Catalog selection menu | https://a2uicatalog.ai/catalogue/index.json |
| ARD discovery document | https://a2uicatalog.ai/.well-known/ai-catalog.json |
| Auth and rate limits | https://a2uicatalog.ai/.well-known/agent-auth.md |
| Agent overview | https://a2uicatalog.ai/llms.txt |

## Terms

Free and MIT licensed. No API key or signup. Rate limits are per-tool and published in the
descriptor. Independent, unofficial project — not affiliated with, endorsed by or sponsored by
Google or Anthropic. A2UI is Google's protocol; MCP is Anthropic's.

Source: https://github.com/a2uicatalog/a2ui
Maintained by Curtis Krygier — https://www.linkedin.com/in/curtiskrygier
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


if __name__ == "__main__":
    main()
