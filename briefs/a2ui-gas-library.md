# A2UI Apps Script Library — Concept Brief

**Status:** Parked — return when catalog is stable  
**Inspiration:** Martin Hawksey's [GAS Gemini library](https://github.com/mhawksey/GeminiApp) — simple, widely adopted, zero setup

---

## The Problem

Using A2UI today requires a developer to:

1. Understand the atom schema vocabulary (467 types)
2. Hand-build a JSON payload
3. Know the renderer URL
4. Encode as gzip+base64
5. Deploy or share the result

That's 5 steps before you see anything. The library collapses this to one.

---

## The Vision

A published Apps Script library (Library Key: `A2UI`) that any GAS developer can add in one click and use immediately:

```javascript
function createDashboard() {
  const page = A2UI.page("Team Dashboard")
    .add({ type: "stat_card", value: "1,234", label: "Weekly users", trend: "up" })
    .add({ type: "metric_row", metrics: [
      { label: "Revenue", value: "$42K", trend: "up" },
      { label: "Churn",   value: "2.1%", trend: "down" },
    ]})
    .add({ type: "progress_bar", value: 75, label: "Q2 target" });

  return page.render(); // returns HtmlOutput — drop into doGet()
}
```

Or one-shot:

```javascript
const url = A2UI.url([
  { type: "dark_hero", heading: "Hello World", badge: "Live" }
]);
// → https://a2uicatalog.ai/r?p=<encoded>  (or public renderer URL)
```

---

## Why Now

The A2UI Atomic Catalog changes the equation:

- **`a2uicatalog.ai/atoms/stat_card`** — every atom has a reference page with fields, example payload, and a live "Try it" render
- **`a2uicatalog.ai/surfaces/google-apps-script-web`** — curated list of atoms that work in GAS
- The catalog makes the library discoverable and self-documenting — a developer can browse atoms, click "Try it live", see what renders, then copy the JSON payload directly into their script

Without the catalog the library is abstract. With it, the atom vocabulary is tangible before you write a line of code.

---

## What the Library Does

| Method | Description |
|---|---|
| `A2UI.page(title, theme?)` | Create a new page builder |
| `page.add(block)` | Append an atom block |
| `page.render()` | Return `HtmlOutput` for `doGet()` |
| `page.url()` | Return shareable renderer URL |
| `A2UI.url(blocks, title?)` | One-shot URL from a blocks array |
| `A2UI.html(blocks, title?)` | One-shot `HtmlOutput` |
| `A2UI.validate(block)` | Check a block against the schema |
| `A2UI.catalog()` | Return the full atom catalog as JSON |

---

## Implementation Path

### Phase 1 — Thin wrapper (no schema bundled)
- Library wraps the public renderer URL
- Encodes payload as gzip+base64 (same as `make_url.py`)
- Returns `HtmlService.createHtmlOutputFromFile()` or redirect
- Publish as GAS library with a key

### Phase 2 — Schema-aware
- Bundle atom schema (compact version) into the library
- `A2UI.validate(block)` checks required fields, warns on unknown types
- `A2UI.atoms()` returns list of available types with descriptions
- Autocomplete-friendly via JSDoc annotations

### Phase 3 — Catalog-connected
- Library fetches from `a2uicatalog.ai/.well-known/ai-catalog.json` at runtime
- Always up to date as new atoms are added
- `A2UI.atom("stat_card")` returns the full ARD entry for that type

---

## Developer Experience Goal

```
1. Add library (one click in GAS editor)
2. Browse a2uicatalog.ai to find atoms
3. Click "Try it live" to preview
4. Copy example payload from atom page
5. Paste into A2UI.page().add({...}).render()
6. Deploy
```

Total time from zero to live web app: **under 5 minutes**.

---

## Positioning

- **Hawksey Gemini lib** — wraps a Google API, zero setup, widely shared
- **A2UI library** — wraps a UI renderer, zero setup, atoms are browsable at `a2uicatalog.ai`
- Target audience: GAS developers who build internal tools, dashboards, reports — today they hand-craft `HtmlService` templates

The catalog and the library are a flywheel: catalog drives discovery → library drives adoption → adoption drives catalog contributions.

---

## Open Questions

- **Renderer URL**: should the library point to the public GAS renderer or a dedicated lightweight endpoint?
- **Versioning**: how to handle schema changes without breaking existing library users?
- **Auth**: public renderer requires Google sign-in — library users are already signed in via GAS, so this may be a non-issue
- **Naming**: `A2UI` as the library identifier? Or something friendlier like `Atomic`?

---

*Catalog reference: `https://a2uicatalog.ai`  
GitHub: `https://github.com/a2uicatalog/a2ui`*
