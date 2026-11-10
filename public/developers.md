---
title: Developer Portal — A2UI Atomic Catalog
description: A2UI Atomic Catalog Developer Portal: integrate 573 typed atoms over MCP or REST. No API key, no signup. OpenAPI spec, live server descriptor, rate limits.
canonical: https://a2uicatalog.ai/developers/
generated_by: gen_page_twins.py
---

# A2UI Atomic Catalog — Developer Portal

## Developer & Agent Documentation

Everything here is free, unauthenticated, and machine-readable — this developer portal is a human index into the same documents an agent reads.

## 1. Connect the MCP server

The primary integration surface. No API key, no signup.

```
POST https://a2uicatalog.ai/mcp
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

`GET` the same URL with `Accept: application/json` for a live server descriptor — every tool, transport, and the current rate limits, generated from the running server so it cannot go stale:

```
curl -H "Accept: application/json" https://a2uicatalog.ai/mcp
```

## 2. Or use the REST surfaces directly

 ``
| GET /spec.json | Full atom vocabulary — 573 atoms, every field contract |
|---|---| ``
| GET /catalogue/index.json | Compact catalog selection menu | ``
| GET /catalogue/atoms-json-schema.json | Strict per-atom JSON Schema for constrained decoding | ``
| POST /api/compose | Natural language → atom blocks |

## 3. Reference & Developer Resources

- [OpenAPI Spec (OpenAPI 3.1)](https://a2uicatalog.ai/openapi.json) — every endpoint, request/response schemas, examples
- [API Docs](https://a2uicatalog.ai/docs/) — REST endpoints, error models, and rate limits
- [API Reference & Docs](https://a2uicatalog.ai/api-docs/) — complete endpoint and parameter directory
- [SDKs & Client Libraries](https://a2uicatalog.ai/sdks/) — npm CLI/MCP package, Python A2A tools, and SDK generators
- [Auth Docs](https://a2uicatalog.ai/auth/) — authentication overview, rate limits, and enterprise OAuth
- [Webhooks Docs](https://a2uicatalog.ai/webhooks/) — SSE streaming, event delivery, and chat integrations
- [API Versioning Policy](https://a2uicatalog.ai/versioning/) — X-API-Version headers, deprecation timelines, and compatibility
- [Pricing & Limits](https://a2uicatalog.ai/pricing/) — free tier allowances and self-hosting runbooks
- [agents.md](https://a2uicatalog.ai/agents.md) — agent-facing guide, served as `text/markdown`
- [llms.txt](https://a2uicatalog.ai/llms.txt) — short overview + entry points
- [Auth & rate limits](https://a2uicatalog.ai/.well-known/agent-auth.md) — the real per-tool numbers
- [Authentication guide](https://a2uicatalog.ai/auth.md) — why you probably need no credential, and the optional OAuth path if your platform requires one
- [SDK Documentation](https://a2uicatalog.ai/sdk.md) — guide to client libraries and packages
- [Versioning & deprecation policy](https://a2uicatalog.ai/versioning.md) — what changes without notice, and the CI gate that fails a deploy if a response shape changes undeclared
- [MCP discovery manifest](https://a2uicatalog.ai/.well-known/mcp.json)

## 4. Own your renderer

The shared demo renderer is rate limited by design. Deploy your own Apps Script renderer in four commands — no cost beyond a Google account — and every subsequent call targets it instead:

```
git clone https://github.com/a2uicatalog/a2ui
cd a2ui/apps-script-surface/gas-wired-renderer
clasp login && clasp create --type webapp && clasp push && clasp deploy
```

## 5. Auth

None required for normal use. See [auth & rate limits](https://a2uicatalog.ai/.well-known/agent-auth.md) for the optional OAuth/Basic-Auth paths used by platforms that require attributed access (e.g. Gemini Enterprise's BYO-MCP model).

## Source

MIT licensed. Full source, issues and pull requests: [github.com/a2uicatalog/a2ui](https://github.com/a2uicatalog/a2ui).
