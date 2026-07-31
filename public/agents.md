# A2UI Atomic Catalog — agent guide

> 474 typed UI atoms an AI agent composes into real rendered interfaces — web, Google Meet,
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
