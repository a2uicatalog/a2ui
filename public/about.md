---
title: About — A2UI Atomic Catalog
description: What the A2UI Atomic Catalog is, who maintains it, and why a typed UI vocabulary beats asking a model to write HTML.
canonical: https://a2uicatalog.ai/about/
generated_by: gen_page_twins.py
---

# A2UI Atomic Catalog — About

## Developer & Agent Documentation

The A2UI Atomic Catalog is an open-source, typed UI vocabulary — **573 atoms** — that AI agents use to produce real rendered interfaces instead of generating HTML. An agent names a component (`stat_card`, `gauge_sla`, `stepper`) and passes data; a renderer that already knows that component draws it. New to the protocol itself? Start with [What is A2UI?](https://a2uicatalog.ai/what-is-a2ui/)

## Why a vocabulary instead of generated markup

A model writing HTML has to be correct every time, and its failure mode is markup that is subtly wrong in ways nobody notices. A model naming a component from a fixed set can only fail by naming something that does not exist — which fails immediately, at the schema boundary. Constraining the output makes the system more reliable, not less capable.

## One payload, many surfaces

The same payload renders on the web, Google Meet stages, Apps Script web apps, Google Chat cards, and MCP Apps hosts such as claude.ai. Per-surface support is declared per atom, so an atom that cannot work somewhere says so rather than degrading silently.

## Independence

This is an independent, unofficial project. It is not affiliated with, endorsed by, or sponsored by Google or Anthropic. A2UI is Google's protocol (official spec at [a2ui.org](https://a2ui.org)); MCP is Anthropic's. The catalogue is MIT licensed and the full source is on [GitHub](https://github.com/a2uicatalog/a2ui).

## Who maintains it

Built and maintained by [Curtis Krygier](https://www.linkedin.com/in/curtiskrygier). Design notes and build write-ups are published on the [blog](https://a2uicatalog.ai/blog/).

## Start here

- [Browse the catalogue](https://a2uicatalog.ai/) — search and preview every atom live
- [OpenAPI specification](https://a2uicatalog.ai/openapi.json) — the full API surface
- [llms.txt](https://a2uicatalog.ai/llms.txt) — the agent-facing overview
- [MCP Apps playground](https://a2uicatalog.ai/surfaces/mcp-apps) — render atoms in a sandboxed MCP host
- [Claude Code surface](https://a2uicatalog.ai/surfaces/claude-code) — render atoms natively in Claude Code panes
