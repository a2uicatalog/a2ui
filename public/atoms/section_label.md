# Section Label

Uppercase section marker with a short glowing accent line — use between content sections on dark pages to create visual rhythm.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| text | string. Label text (uppercased automatically). |
| colour | string (optional). Accent colour. Default |
| margin | string (optional). Vertical margin. Default 24px 0 12px. |

## Example payload

```json
{
  "type": "section_label",
  "text": "New"
}
```

Live page: https://a2uicatalog.ai/atoms/section_label/
Full field contract: https://a2uicatalog.ai/spec.json
