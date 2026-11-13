# Spotlight Card

A content card where a radial gradient spotlight follows the cursor. Child blocks or content field.

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
| blocks | array of child atoms inside the card |
| content | markdown string (if no blocks) |
| accent | spotlight tint colour (default var(--a2ui-accent)) |

## Example payload

```json
{
  "type": "spotlight_card",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ],
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/spotlight_card/
Full field contract: https://a2uicatalog.ai/spec.json
