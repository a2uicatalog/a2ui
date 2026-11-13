# Animated Border

Card or section with a rotating conic gradient border. Child blocks or content inside.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| blocks | array of child atoms inside |
| content | markdown string (if no blocks) |
| from | gradient start colour (default |
| to | gradient end colour (default |
| via | gradient mid colour (default |
| speed | rotation speed in seconds (default 3) |
| padding | inner padding (default 20px) |
| radius | border radius (default 12px) |

## Example payload

```json
{
  "type": "animated_border",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ],
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/animated_border/
Full field contract: https://a2uicatalog.ai/spec.json
