---
title: API Docs, OpenAPI Spec & MCP Server — A2UI Atomic Catalog
description: A2UI Atomic Catalog API docs: the MCP server, REST endpoints, OpenAPI 3.1 specification, JSON schemas and SDKs for AI agents. Free, no API key.
canonical: https://a2uicatalog.ai/docs/
generated_by: gen_page_twins.py
---

# A2UI Atomic Catalog — API Docs, OpenAPI Spec & MCP Server

## Developer & Agent Documentation

Developer and API documentation for the A2UI Atomic Catalog. All developer resources are free, unauthenticated, and machine-readable.

Primary integration surface: [the MCP server at https://a2uicatalog.ai/mcp](https://a2uicatalog.ai/mcp) — no API key, no signup, `POST` JSON-RPC 2.0 directly. Documentation questions: [the docs MCP server at /mcp-docs](https://a2uicatalog.ai/mcp-docs). Contract: [OpenAPI 3.1 specification](https://a2uicatalog.ai/openapi.json). Packages: [SDKs & client libraries](https://a2uicatalog.ai/sdks/). Guide: [developer portal](https://a2uicatalog.ai/developers/).

## REST Endpoints

 ``
| POST /api/render | Render atom payload to standalone HTML page (50 req/day) |
|---|---| ``
| POST /api/compose | Natural language prompt → typed atom blocks (20 req/day) | ``
| GET /ask?q=... | Natural-language search over the atom catalog (60 req/day) | ``
| GET /api/data/{source} | Declared data source proxy (data-sources.yaml) | ``
| GET /spec.json | Full atom vocabulary (573 atoms) with all field contracts | ``
| GET /catalogue/atoms-json-schema.json | Strict JSON Schema for constrained agent decoding | ``
| GET /catalogue/index.json | Compact catalog selection menu |

## MCP Servers

- **Product MCP Server**: `https://a2uicatalog.ai/mcp` — tools for composing, rendering, and publishing UI atoms.
- **Documentation MCP Server**: `https://a2uicatalog.ai/mcp-docs` — tools (`search_docs`, `list_docs`) for querying documentation.

## Specifications & Developer Resources

- [OpenAPI 3.1 Specification](https://a2uicatalog.ai/openapi.json) — complete machine-readable OpenAPI spec
- [Developers Guide](https://a2uicatalog.ai/developers/) — integration walkthrough and deployment guide
- [SDKs & Client Libraries](https://a2uicatalog.ai/sdks/) — npm CLI/MCP package, Python A2A tools, and SDK generators
- [llms.txt](https://a2uicatalog.ai/llms.txt) and [docs/llms.txt](https://a2uicatalog.ai/docs/llms.txt) — LLM-friendly context documents
- [agents.md](https://a2uicatalog.ai/agents.md) — agent guide with tool contracts and invocation examples
- [Authentication Guide](https://a2uicatalog.ai/auth.md) — auth requirements and OAuth metadata
- [SDK Documentation](https://a2uicatalog.ai/sdk.md) — SDKs and client packages
- [Auth & Rate Limits](https://a2uicatalog.ai/.well-known/agent-auth.md) — real rate limits per tool and endpoint
- [Pricing & Limits](https://a2uicatalog.ai/pricing.md) — free tier terms and self-hosting runbooks
- [Versioning Policy](https://a2uicatalog.ai/versioning.md) — API versioning (X-API-Version) and deprecation rules
- [RFC 9727 API Catalog](https://a2uicatalog.ai/.well-known/api-catalog) — linkset of all API surfaces
- [ARD Discovery Catalog](https://a2uicatalog.ai/.well-known/ard.json) — AI Resource Discovery index
