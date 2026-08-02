# A2UI Atomic Catalog

**Real rendered UI in the conversation — charts, gauges, dashboards, study apps —
without the model writing a single line of HTML.**

The agent names a component from a fixed vocabulary of 474 typed atoms. A renderer
that already knows that component draws it. So a hallucinated atom is a *parse
error*, not a broken screen — the failure surfaces before anything reaches the user.

No signup, no API key, no configuration. Add the URL and start.

```
https://a2uicatalog.ai/mcp
```

## Try it

> Using the A2UI catalog, render a stat_card with value "1,234", label "Daily users", delta "+12%".

> Build me a full-screen revision app for the French Brevet — subject tabs for Maths,
> Français and Histoire-Géo, with flashcards and a timed drill in each.

> Show a live ATC radar for Toulouse with simulated traffic and the real LFBO weather.

The second one is a single tool call: `emit_runbook_surface` stamps your content
through a pre-authored composition, so the agent supplies content and makes zero
layout decisions. The third pulls live METAR through a declared data proxy.

## One payload, many surfaces

Every atom declares where it works, where it degrades, and where it genuinely
cannot go — and those declarations are **enforced**, not documentation:

| | |
|---|---|
| `works_on` | renders fully |
| `degraded_on` | renders with something lost — an animation frozen, an ordered list instead of a stepper |
| `incompatible_on` | cannot do what it is designed to do there, and says so instead of pretending |

A `quiz_set` you cannot answer is not a degraded quiz, it is not a quiz. The
catalogue refuses rather than shipping something that looks right and isn't.

Surfaces: **web · MCP Apps · Google Apps Script · Google Meet · Google Chat · PDF · email**

## Interactive UI, not screenshots

Implements **MCP Apps (SEP-1865)** — `ui://` resources over the standard `ui/*`
JSON-RPC bridge. Verified rendering full-screen in **both Claude and ChatGPT** from
an identical payload, which is the point: the vocabulary is the product, the host
is a detail.

## 15 tools

**Compose** — `list_catalogs`, `get_catalog`, `required_catalogs`, `distill_document`
**Render** — `render_surface`, `render_ping`, `preview_url`, `make_surface_url`, `build_multi_page_surface`
**Runbooks** — `emit_runbook_surface`, `emit_training_runbook` (pre-authored compositions; you supply content only)
**Ship** — `emit_deployment`, `publish_url`, `unpublish_url`
**Setup** — `identify_model` (capability-matched guidance; optional, never a precondition)

## Without MCP at all

The vocabulary stands alone. No client, no connector, no account:

```bash
curl -X POST https://a2uicatalog.ai/api/render \
  -H 'Content-Type: application/json' \
  -d '{"blocks":[{"type":"stat_card","value":"1,234","label":"Daily users"}]}'

npx -p @a2uicatalog/mcp a2ui render page.json --surface email
```

`OpenAPI` · `spec.json` · `llms.txt` · ARD catalog — all public, all unauthenticated.

## Free

No paid tier, because there is nothing to upgrade to. MIT licensed, renderers in the
public repo — anything you hit a limit on here, you can run yourself.
Full limits: https://a2uicatalog.ai/pricing.md

---

[Docs](https://a2uicatalog.ai/llms.txt) · [OpenAPI](https://a2uicatalog.ai/openapi.json) ·
[Source](https://github.com/a2uicatalog/a2ui) · MIT
