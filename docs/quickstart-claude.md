# Quickstart: A2UI Catalog in Claude (5 minutes)

Connect the live MCP server, render your first atom, deploy your own renderer. No signup, no API key — the catalog never sees your data; renders happen against your own Apps Script deployment (or the shared demo, rate-limited).

## 1. Add the connector

**Claude Desktop** — Settings → Connectors → Add custom connector:

```
Name: A2UI Catalog
URL:  https://a2uicatalog.ai/mcp
```

**claude.ai** (web) — Settings → Connectors → Add connector, same URL. No auth fields — the server is open by design (nothing to protect; render output belongs to the caller, not us).

Claude should confirm the connection and list tools: `list_catalogs`, `get_catalog`, `render_surface`, `make_surface_url`, `preview_url`, `emit_deployment`, and a few more.

## 2. Ask for something real

Try, verbatim:

> Using the A2UI catalog, show me the atoms available for a stat dashboard, then render a `stat_card` with value "1,234", label "Daily users", delta "+12%".

What happens under the hood:
1. `list_catalogs` — Claude picks the right catalog slice for the request (473 atoms across 14 catalogs; it doesn't need the whole vocabulary in context for one card).
2. `get_catalog` — fetches that slice's real field contracts. Claude never guesses a field name.
3. `render_surface` (on MCP Apps hosts) or `preview_url` (elsewhere) — the rendered result comes back as a live view or a link, not raw HTML in the transcript.

If you're on an MCP Apps-capable host (claude.ai web is), the card renders **inline, in the conversation** — that's the whole pitch: the model names an atom, it never writes HTML.

## 3. Push it further

> Now render a `sankey_flow` showing traffic from three sources into two destinations, dark theme.

> Build me a small dashboard: a `stat_card`, a `progress_bar`, and a `chartjs_bar` — pick reasonable data.

Claude composes from the vocabulary each time. If something looks wrong, ask it to check `get_catalog` again — the fields are real, not memorized.

## 4. Own your renderer (recommended before real use)

`preview_url`/`render_surface` run against the catalog's own shared demo Apps Script instance — fine for exploring, rate-limited (10 renders/week per client) by design, and not something to build on. Deploying your own takes four commands and costs nothing beyond a Google account:

```bash
git clone https://github.com/a2uicatalog/a2ui
cd a2ui/apps-script-surface/gas-schema-renderer
clasp login
clasp create --type webapp --title "My A2UI Renderer"
clasp push
clasp deploy
```

Tell Claude the deployment URL — "use `https://script.google.com/macros/s/YOUR_ID/exec` as my renderer" — and every subsequent `make_surface_url` call targets it instead of the shared demo. You now own the URL, the deployment, and everything rendered through it.

## What just happened, structurally

Claude never generated HTML, CSS, or a component library. It picked names from a fixed, typed vocabulary (`atoms/schema.yaml` — [browse it live](https://a2uicatalog.ai/)) and handed them to a renderer that already knows how to draw each one, on whichever of 8 surfaces you're targeting. That's the whole idea — see [the main README](../README.md#the-idea) for the token-efficiency argument and [`spec.json`](https://a2uicatalog.ai/spec.json) for the machine-readable catalog Claude is actually reading from.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Connector won't add | URL must be exactly `https://a2uicatalog.ai/mcp`, no trailing content |
| Tools listed but calls fail | Rare — check [a2uicatalog.ai](https://a2uicatalog.ai) itself loads; the MCP server and site share infrastructure |
| Render looks unstyled/broken | You're on a host without MCP Apps view support — ask for `preview_url` instead of `render_surface`, which returns a link you open directly |
| "Demo limit reached" | You've used your 10 renders this week on the shared instance — deploy your own (step 4) |
