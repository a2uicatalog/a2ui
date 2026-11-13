# Key Takeaways

Displays a highlighted summary box containing critical bullet points from an article.

## Surfaces

web, google-apps-script-web, mcp-apps, claude-code, android

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
| points | array. Core sentences highlighting the key learnings. |

## Example payload

```json
{
  "type": "key_takeaways",
  "points": [
    "First key point",
    "Second key point",
    "Third key point"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/key_takeaways/
Full field contract: https://a2uicatalog.ai/spec.json
