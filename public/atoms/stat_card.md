# Stat Card

Glowing neon stat card — large value with label and optional delta

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| value | string |
| label | string |
| delta | string (optional) |
| is_up | bool (optional) |
| accent | string (optional) |

## Example payload

```json
{
  "type": "stat_card",
  "value": "1,234",
  "label": "Stat Card"
}
```

Live page: https://a2uicatalog.ai/atoms/stat_card/
Full field contract: https://a2uicatalog.ai/spec.json
