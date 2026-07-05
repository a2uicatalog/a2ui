---
title: How the A2UI Renderer Works: JSON In, HTML Out
slug: a2ui-renderer-how-it-works
date: 2026-06-28
firestore_id: XegERk2C8pY3SRgZXFiy
status: published
---

*Summary: The A2UI renderer is a visual translator — it takes a declarative JSON payload and produces surface-appropriate HTML. Here's how the dispatch works, why the same schema renders on three surfaces, and what it means when an AI agent generates UI.*

You pick a component from [a2uicatalog.ai](https://a2uicatalog.ai). You write a JSON payload. A rendered page appears — styled, interactive, surface-appropriate. No HTML written. No CSS authored.

This is what the renderer does. It's a translator: JSON in, HTML out. This post explains how that translation works, and what it means for the way you build Workspace tools.

## The translation in one diagram

*[embedded image]*The same JSON payload dispatches through a renderer to produce HTML for any supported surface.

## Schema is the what. Renderer is the how.

The [A2UI schema](https://a2uicatalog.ai) defines 485 component types. Each type has a name and a set of fields. `stat_card` has `value`, `label`, `delta`, `is_up`. That's the vocabulary — the *what*.

The renderer is the implementation — the *how*. For every type in the catalog, there's a function that takes a block and returns HTML:

```
// The entire renderer contract — one function per type
_RENDERERS['stat_card'] = function(b) {
  return '<div class="stat-card">'
    + '<div class="value">' + b.value + '</div>'
    + '<div class="label">' + b.label + '</div>'
    + (b.delta ? '<div class="delta">' + b.delta + '</div>' : '')
    + '</div>';
};
```

The dispatcher routes by type:

```
function renderAtoms(blocks) {
  return blocks.map(function(block) {
    var fn = _RENDERERS[block.type];
    return fn ? fn(block) : '';
  }).join('');
}
```

That's the entire engine. Every component in the catalog — from a simple `body` block to a full interactive globe — is one entry in `_RENDERERS`.

## Same payload, different surface

The schema doesn't change between surfaces. A `stat_card` payload is identical whether it's rendering on Apps Script web, a Meet stage sidebar, or a web article. What changes is the renderer — each surface has its own implementation of `_RENDERERS['stat_card']` tuned for that environment.

This is the payoff of the declarative approach: swap the renderer file, keep the payload, get a different surface. The JSON is the contract; the renderer is the adapter.

| Surface | Renderer | Output |
|---|---|---|
| Apps Script Web | `atoms_*.gs` (V8 GAS) | HtmlOutput via HtmlService |
| Meet Stage | `atoms_*.gs` (Meet API) | Card UI via CardService |
| Web Article | `renderer.py` (Python) | HTML fragment in blog post |
| Google Chat | `atoms_chat.gs` | Card JSON for Chat API |
| PDF | `atoms_pdf.gs` | Styled HTML → print |

## The extreme case: globe_3d

To see what the renderer abstraction actually buys you, look at `globe_3d`. Seven optional fields. Full interactive 3-D globe — wireframe or earth mode, draggable with inertia, dot pins at lat/lon coordinates, great-circle arcs between points.

```
{
  "type": "globe_3d",
  "theme": "earth",
  "size": 400,
  "dots": [
    {"lat": 48.8, "lon": 2.3, "label": "Paris"},
    {"lat": 40.7, "lon": -74,  "label": "NYC"},
    {"lat": 35.7, "lon": 139.7,"label": "Tokyo"}
  ],
  "arcs": [
    {"from": [48.8, 2.3],  "to": [40.7, -74]},
    {"from": [40.7, -74],  "to": [35.7, 139.7]}
  ]
}
```

*[embedded image]*globe_3d — earth theme, city pins, great-circle arcs. Pure canvas. Zero external dependencies. Draggable with inertia.

That payload produces a self-contained canvas animation — ~160 lines of GAS renderer code, no external libraries, CSP-safe. The developer writes 12 lines of JSON. The renderer handles the rest.

## What this means for AI agents

An AI agent that understands the A2UI schema can generate UI without knowing HTML. It produces a payload — typed blocks with named fields — and the renderer turns that into a page. The agent never sees CSS. It never writes a ``.

This is the premise behind the [ARD manifest](https://a2uicatalog.ai/.well-known/ai-catalog.json) at `a2uicatalog.ai`. An agent can query 485 typed components, pick the right one for the job, generate the payload, and hand it to a renderer. Structured output → structured UI.

- **Browse the catalog** [a2uicatalog.ai](https://a2uicatalog.ai) — every component with fields, surfaces, degradation notes
- **ARD manifest** [ai-catalog.json](https://a2uicatalog.ai/.well-known/ai-catalog.json) — machine-readable, agent-queryable
- **GitHub** [a2uicatalog/a2ui](https://github.com/a2uicatalog/a2ui) — renderers, schema, MIT licensed
- **Protocol** [a2ui.org](https://a2ui.org) — the A2UI standard from Google
## Deploy your own renderer

The renderer is fully open source — [github.com/a2uicatalog/a2ui](https://github.com/a2uicatalog/a2ui). Deploy your own instance in four commands. You own the URL, you own the deployment, no dependency on the catalog's demo endpoint.

```
git clone https://github.com/a2uicatalog/a2ui
cd apps-script-surface/gas-schema-renderer
clasp login
clasp create --type webapp --title "My A2UI Renderer"
clasp push
clasp deploy
# → https://script.google.com/macros/s/YOUR_ID/exec
```

From that point you own a renderer. Call it with any payload from the catalog. Push updates when new atoms ship. Customise CSS, add internal atoms, restrict to your surfaces. It's your instance.

The catalog's "Try it live" button runs a shared demo of the same renderer — same code, same atoms, different URL. For anything beyond exploration, deploy your own.

