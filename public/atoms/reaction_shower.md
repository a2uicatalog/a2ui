# Reaction Shower

Emoji reaction buttons — tapping rains the emoji down the screen, with optional Sheet-backed totals

## Surfaces

google-apps-script-web, mcp-apps, android

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
| reactions | array of emoji strings (optional, default 🔥💡🤯👏) |
| write_url | string (optional, GAS doGet URL to record reactions) |
| sheet_url | string (optional, Google Sheet CSV for live counts) |
| poll | number (optional, poll interval ms) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "reaction_shower"
}
```

Live page: https://a2uicatalog.ai/atoms/reaction_shower/
Full field contract: https://a2uicatalog.ai/spec.json
