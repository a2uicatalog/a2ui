# Publishing an ARD Catalog with 467 Atoms

**Status:** Live  
**Date:** 2026-06-28  
**Tags:** ARD, agentic-resource-discovery, A2UI, cloudflare, open-source

---

## What ARD Is

On June 17, 2026, Google published the Agentic Resource Discovery (ARD) specification, co-signed by Microsoft, Hugging Face, Nvidia, Salesforce, and others. The premise is simple: AI agents operating across the open web have no standard way to discover what capabilities exist, which to use, or whether they're safe to connect to.

ARD's answer is a static `ai-catalog.json` file at `/.well-known/ai-catalog.json` on your domain. Registries crawl it. Agents query registries. Your capabilities surface in agent tool selection automatically — no SDK, no handshake, no prior arrangement.

---

## The A2UI Head Start

[A2UI](https://a2ui.org) (Agent-to-User Interface) is an open protocol — created by Google, Apache 2.0 licensed — for agent-driven interfaces. Agents send declarative component descriptions; clients render them using native widgets. No code execution, no UI injection risk. Flat streaming JSON, LLM-friendly by design.

I've been building [a2uicatalog.ai](https://a2uicatalog.ai) as a community implementation of that protocol, focused on Google Workspace surfaces: GAS, Meet stage, Chat, and web. The catalog covers 467 components — I call them atoms — each typed, surface-scoped, and field-described in a single `schema.yaml`.

That schema already contained everything ARD needs per entry: `type`, `description`, `surfaces.works_on`, and `compact_description`.

The ARD transform was almost mechanical.

A single script reads `atoms/schema.yaml` and generates the full catalog at build time:

```bash
python3 scripts/generate_ard_catalog.py
# ✓ 468 entries (467 atoms + 1 renderer) → public/.well-known/ai-catalog.json
```

Each atom maps directly:

```json
{
  "identifier": "urn:air:a2uicatalog.ai:atom:stat_card",
  "displayName": "Stat Card",
  "type": "application/vnd.a2ui.atom+json",
  "url": "https://a2uicatalog.ai/atoms/stat_card",
  "capabilities": ["web", "meet-stage", "google-apps-script-web", "googlechat"],
  "representativeQueries": [
    "show an animated stat card with label and trend",
    "render a stat card"
  ]
}
```

---

## The Journey

**Org and domain.** The repo moved to [github.com/a2uicatalog/a2ui](https://github.com/a2uicatalog/a2ui). `a2uicatalog` was already squatted when ARD dropped. `a2uicatalog.ai` was registered the same day. GitHub redirected old URLs automatically — nothing broke.

**Cloudflare Pages.** Build command: `pip install pyyaml && python3 scripts/generate_ard_catalog.py`. Output: `public/`. Every push to `main` regenerates the catalog. Total build time: ~9 seconds. The well-known file requires one `_headers` entry:

```
/.well-known/ai-catalog.json
  Content-Type: application/json; charset=utf-8
  Access-Control-Allow-Origin: *
```

`Access-Control-Allow-Origin: *` is mandatory — the ARD spec requires it for crawler access.

**Atom pages.** A second script generates a reference page for every atom at `public/atoms/{type}/index.html` — fields table, example payload, surface badges, live renderer link, and the exact ARD entry for that atom. The documentation, the catalog, and the canonical URL are the same artifact.

**Payload quality.** The example payloads are auto-generated from schema field names. After shipping atom pages, a diagnostic pass found 79 atoms producing empty required list fields and 56 field names falling through to a title-case fallback. Both fixed: `_infer_list` now handles 60+ field name patterns (`nodes`, `options`, `cohorts`, `skills`, `risks`, `criteria`…), `_infer_string` handles 50+ (`message`, `question`, `price`, `method`, `version`, `front`, `back`…). Zero empty lists. Zero meaningful generic fallbacks.

---

## Directory vs Discovery

I've argued elsewhere that for enterprise deployments, the A2UI protocol makes ARD-style discovery unnecessary. The entire capability surface — atoms, surface declarations, connector schemas — is compiled into the agent's context before any prompt is processed. The agent doesn't discover what it can render. It already knows. Build-time resolution beats runtime crawling in zero-trust environments: faster, auditable, and architecturally correct (capability existence is itself sensitive in a zero-trust model).

That argument stands for enterprise. But A2UI is also a community protocol — and for an open protocol serving unknown participants across GAS, Meet, web, and Chat, discovery does two distinct jobs:

**For humans** — the catalog is a browsable directory. A developer building a Meet add-on wants to find the right atom for their use case: filter by surface, scan example payloads, click "Try it live." Discovery here is navigation. `a2uicatalog.ai` is the index that makes that possible.

**For agents** — the ARD manifest is declarative. An agent that encounters A2UI for the first time doesn't need a compiled vocab injected into its context. It queries a registry, finds `a2uicatalog.ai`, and gets 467 typed, surface-scoped, query-matched entries it can reason over immediately. No prior arrangement needed.

The distinction: enterprise agents operate inside a known, pre-compiled vocabulary. Open-web agents operate in an unknown landscape — discovery is their vocabulary bootstrap.

ARD is the right primitive for an open protocol precisely because participants are unknown in advance. Publishing `a2uicatalog.ai` as an ARD node isn't a concession to the discovery model — it's recognition that the same protocol serves two different agent populations, and each needs the format that fits their context.

---

## Status

- [x] ARD catalog live: `https://a2uicatalog.ai/.well-known/ai-catalog.json`
- [x] 467 atom pages: `https://a2uicatalog.ai/atoms/{type}`
- [x] Example payload quality: 0 empty lists, 0 generic fallbacks
- [ ] Submit to ARD registry (open for publishers Q3 2026)
- [ ] Explore private ARD registry pattern for enterprise A2UI deployments

---

*Catalog at [github.com/a2uicatalog/a2ui](https://github.com/a2uicatalog/a2ui). Built with [Claude Code](https://claude.ai/code).*
