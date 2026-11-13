# Two Tone Card

Card with a solid colored header section (title, subtitle, icon) and a white body that renders atom blocks. Clean, elegant container for any content.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| title | string (required) |
| subtitle | string (optional) |
| icon | string (optional, emoji) |
| accent | string (optional, hex, default "#4f46e5") |
| header_theme | string (optional, "light"|"dark", default "light") |
| blocks | array (optional, atom blocks rendered in white body) |

## Example payload

```json
{
  "type": "two_tone_card",
  "title": "Two Tone Card"
}
```

Live page: https://a2uicatalog.ai/atoms/two_tone_card/
Full field contract: https://a2uicatalog.ai/spec.json
