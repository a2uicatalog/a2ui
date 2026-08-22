---
name: a2ui-mcp
description: Connect an AI agent or host to the A2UI Atomic Catalog's MCP server for live, tool-based UI composition and rendering — Claude, ChatGPT, Gemini Enterprise, or a custom MCP client. Use when integrating a NEW agent/host with A2UI over MCP, diagnosing a connection or auth problem, or deciding between the public and enterprise-auth endpoints. Not for picking atoms (a2ui-catalog) or composing/rendering a payload once connected (a2ui-compose).
license: MIT
metadata:
  author: a2uicatalog
  version: "1.0.0"
---

# Connecting to the A2UI MCP server

## The default: no credential at all

```
https://a2uicatalog.ai/mcp
```

Public, unauthenticated, no signup, no API key. `POST` speaks JSON-RPC 2.0 (MCP
Streamable HTTP): `initialize` → `tools/list` → `tools/call`. `GET` the same URL with
`Accept: application/json` for a machine-readable server descriptor (every tool, current
rate limits, docs links) instead of the human landing page.

```http
POST https://a2uicatalog.ai/mcp
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

If a scanner, spec, or setup wizard told you to look for `/auth.md`, this is the short
answer: just call the endpoint above. The rest of this skill is about the optional
authenticated path most integrations don't need.

## A separate documentation server

`https://a2uicatalog.ai/mcp-docs` is a DIFFERENT MCP identity (`a2uicatalog-docs`)
exposing `search_docs(query)` / `list_docs()` — it answers questions FROM this product's
own docs (auth, versioning, pricing, rate limits). The server above TAKES ACTIONS
(compose, render, publish); this one only answers doc questions. Don't confuse the two
when an agent needs to look something up rather than do something.

## Rendering inline: MCP Apps

Hosts that negotiate the `io.modelcontextprotocol/ui` extension in their `initialize`
request get inline rendering: `render_surface` returns a live, interactive view inside
the conversation via a `ui://` resource — no URL, no size ceiling, nothing stored. On a
host that doesn't support MCP Apps, the same tool call just returns the payload as text
instead of erroring, so it's always safe to call.

## When you actually need a credential

Enterprise platforms whose connector model can't call an unauthenticated service (e.g.
Gemini Enterprise's BYO-MCP data store, which requires OAuth 2.0) use a second, gated
endpoint: `https://a2uicatalog.ai/mcp-auth` — the SAME tools as `/mcp`, behind a real
credential. Three accepted mechanisms, in precedence order: `Authorization: Bearer
<token>` (OAuth 2.0 authorization-code flow), `X-Api-Key: <key>` (for connector
templates that offer an API-key field but no OAuth), `Authorization: Basic
<base64(user:pass)>`. An unauthenticated request to `/mcp-auth` returns `401` with a
`WWW-Authenticate` header carrying a `resource_metadata` pointer to the RFC 9728
protected-resource metadata document.

**There is no self-service registration** — this server doesn't implement RFC 7591
dynamic client registration. Registration is manual, one `client_id` per organization
(the client IS the tenant): contact the maintainer via https://a2uicatalog.ai/contact/
with your exact `redirect_uri` values. If you don't want to wait, use the public `/mcp`
endpoint instead — it's the same server, same tools.

## Machine-readable discovery documents

| Document | URL |
|---|---|
| Authentication guide (full detail) | https://a2uicatalog.ai/auth.md |
| Protected resource metadata (RFC 9728, `/mcp-auth` only) | https://a2uicatalog.ai/.well-known/oauth-protected-resource/mcp-auth |
| Authorization server metadata (RFC 8414) | https://a2uicatalog.ai/.well-known/oauth-authorization-server |
| Auth & rate limits (real per-tool numbers) | https://a2uicatalog.ai/.well-known/agent-auth.md |
| MCP server card | https://a2uicatalog.ai/.well-known/mcp/server-card.json |

Free, MIT licensed, no signup for the default path. Independent, unofficial project —
not affiliated with, endorsed by, or sponsored by Google or Anthropic. A2UI is Google's
protocol; MCP is Anthropic's. Source: https://github.com/a2uicatalog/a2ui
