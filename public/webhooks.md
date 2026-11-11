---
title: Webhooks & Event Delivery — A2UI Atomic Catalog
description: A2UI Atomic Catalog webhooks and event delivery documentation: SSE streaming, JSON-RPC notifications, and Chat webhooks.
canonical: https://a2uicatalog.ai/webhooks/
generated_by: gen_page_twins.py
---

# A2UI Atomic Catalog — Webhooks & Event Delivery

## Developer & Agent Documentation

Event delivery, webhook integration, and streaming documentation for the A2UI Atomic Catalog.

## Event Delivery Architecture

A2UI uses modern streaming and push transports designed for AI agents and chat surfaces:

- **MCP Streamable HTTP / JSON-RPC** — live streaming tool invocations over `/mcp`
- **Server-Sent Events (SSE)** — live incremental streaming on `/ask` (pass `Accept: text/event-stream`)
- **Google Chat Webhooks** — server-side rendering of cardsV2 messages directly posted to incoming webhook URLs

## Developer Resources

- [API Documentation](https://a2uicatalog.ai/docs/) — endpoint schemas and transport contracts
- [OpenAPI 3.1 Specification](https://a2uicatalog.ai/openapi.json) — machine-readable spec
- [MCP Server Endpoint](https://a2uicatalog.ai/mcp) — live streamable JSON-RPC 2.0 interface
- [Developers Guide](https://a2uicatalog.ai/developers/) — deployment and integration guides
