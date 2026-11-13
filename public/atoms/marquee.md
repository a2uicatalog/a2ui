# Marquee

Infinite horizontal scrolling ticker. Items can be text strings, logos (image_url), or icon+label chips.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| items | array of {text?, label?, icon?, image_url?, url?} |
| title | optional label above the marquee strip |
| speed | seconds for one full cycle (default 30) |
| gap | px spacing between items (default 48) |
| direction | normal (left scroll, default) or right |
| separator | optional separator character between items |
| pause_on_hover | pause animation on hover (default true) |
| bg | background colour (default var(--surface)) |
| rounded | rounded corners (default true) |

## Example payload

```json
{
  "type": "marquee",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/marquee/
Full field contract: https://a2uicatalog.ai/spec.json
