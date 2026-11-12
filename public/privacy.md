---
title: Privacy — A2UI Atomic Catalog
description: What the A2UI Atomic Catalog stores, what it does not, and what the MCP server logs.
canonical: https://a2uicatalog.ai/privacy/
generated_by: gen_page_twins.py
---

# A2UI Atomic Catalog — Privacy

## Developer & Agent Documentation

## The short version

There are no accounts, no sign-up, no advertising and no third-party analytics or tracking scripts on this site. Browsing the catalogue requires giving nothing.

## The MCP server

The MCP endpoint at `a2uicatalog.ai/mcp` is unauthenticated and stores nothing about who calls it. Rate limits are enforced against a **SHA-256 hash of the client IP** with a counter — never the IP itself, and never any payload content. Those counters expire automatically (7 days for preview limits, 24 hours for render limits).

## Rendering

Surface content passed to `preview_url` or `render_surface` is rendered and returned; it is not retained for analytics. Payloads sent to `publish_url` are stored deliberately, because that tool exists to mint a shareable link — those entries carry a TTL and can be removed at any time with `unpublish_url`.

## Logs

The edge keeps standard operational request logs (path, status, timing) as any web host does. Application logs record the tool name and duration of a call, not its content.

## Third parties

The site is served by Cloudflare, whose own processing is covered by their privacy terms. Atoms that fetch live data do so only through declared sources listed in the catalogue's data-source registry — network access is not open-ended.

## Contact

Questions about any of this: see the [contact page](https://a2uicatalog.ai/contact/).
