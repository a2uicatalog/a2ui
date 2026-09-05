---
title: A2UI Atomic Catalog — agent guide
description: 500 typed UI atoms an AI agent composes into real rendered interfaces instead of generating HTML.
canonical: https://a2uicatalog.ai/agents.md
---

# A2UI Atomic Catalog — agent guide

> 500 typed UI atoms an AI agent composes into real rendered interfaces — web, Google Meet,
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
your own Google Apps Script web app via `build_app`. https://registry.npmjs.org/@a2uicatalog/mcp

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
| CLI / local MCP server (npm) | https://registry.npmjs.org/@a2uicatalog/mcp |
| Agent Skills index | https://a2uicatalog.ai/.well-known/agent-skills/index.json |
| OpenAPI specification | https://a2uicatalog.ai/openapi.json |
| Full atom vocabulary | https://a2uicatalog.ai/spec.json |
| Strict per-atom JSON Schema | https://a2uicatalog.ai/catalogue/atoms-json-schema.json |
| Catalog selection menu | https://a2uicatalog.ai/catalogue/index.json |
| ARD discovery document | https://a2uicatalog.ai/.well-known/ard.json |
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
