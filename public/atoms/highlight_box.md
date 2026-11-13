# Highlight Box

A visually rich highlighted box with gradient, solid, or outline style. Richer than callout — no severity system, pure design focus.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| text | string (optional, markdown — renderer degrades to empty; provide title and/or text) |
| icon | string (optional, emoji) |
| accent | string (optional, hex, default "#4f46e5") |
| style | string (optional, "gradient"|"solid"|"outline", default "gradient") |

## Example payload

```json
{
  "type": "highlight_box"
}
```

Live page: https://a2uicatalog.ai/atoms/highlight_box/
Full field contract: https://a2uicatalog.ai/spec.json
