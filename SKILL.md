---
name: a2ui-atomic-catalog
description: Renders real interactive UI — charts, gauges, steppers, dashboards, decision trees — for AI agents instead of generating raw HTML. Use this skill when a user needs to SEE something rather than read a description of it, and the host (Claude, another MCP client, a Gemini Enterprise agent) can display rendered visuals or open a link. Do not use for plain prose answers, for data retrieval (this renders data, it does not fetch it beyond a few declared sources), or on hosts that cannot display HTML.
---

# A2UI Atomic Catalog

474 typed UI atoms an AI agent composes into real rendered interfaces — web, Google Meet,
Apps Script, Google Chat and MCP Apps — instead of writing HTML by hand. The agent names a
component from a fixed vocabulary; a renderer that already knows that component draws it.

## Connect

MCP server, no auth, no signup, no API key:

```
https://a2uicatalog.ai/mcp
```

`POST` speaks JSON-RPC 2.0 (MCP Streamable HTTP). `GET` with `Accept: application/json`
returns a machine-readable descriptor listing every tool, current rate limits, and
documentation links.

## How to use it

1. **`list_catalogs`** — pick the catalog slice the task actually needs. Do not load the
   whole 474-atom vocabulary into context for a one-chart request.
2. **`get_catalog`** — read the real field contracts for that slice. Never guess a field
   name; a hallucinated field is a validation error, not a broken render.
3. **Render**, by host capability:
   - `render_surface` — MCP Apps-capable hosts (Claude.ai and others): renders inline in
     the conversation, no URL.
   - `preview_url` — any other host: returns a shareable link (rate-limited demo renderer).
   - `make_surface_url` — render against the caller's own deployed renderer instead of the
     shared demo one; no rate limit.

## When this is the wrong tool

- The answer is better as prose than a visual.
- The host cannot display HTML or open a link.
- The task needs live data this catalog doesn't already declare a source for — this skill
  renders data, it does not fetch arbitrary data.

## Reference

| Document | URL |
|---|---|
| OpenAPI specification | https://a2uicatalog.ai/openapi.json |
| Full atom vocabulary | https://a2uicatalog.ai/spec.json |
| Strict per-atom JSON Schema | https://a2uicatalog.ai/catalogue/atoms-json-schema.json |
| Agent overview | https://a2uicatalog.ai/llms.txt |
| A2A agent card | https://a2uicatalog.ai/.well-known/agent-card.json |

Free, MIT licensed, no signup. Independent, unofficial project — not affiliated with,
endorsed by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is
Anthropic's. Source: https://github.com/a2uicatalog/a2ui
