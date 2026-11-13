# Badge Group

Group of coloured status badges with optional pulse animation — green/cyan/blue/yellow/red/purple/grey

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
| title | string (optional) |
| badges | [{'text': 'string', 'color': 'green|cyan|blue|yellow|red|purple|grey', 'pulse': 'bool (optional)'}] |

## Example payload

```json
{
  "type": "badge_group"
}
```

Live page: https://a2uicatalog.ai/atoms/badge_group/
Full field contract: https://a2uicatalog.ai/spec.json
